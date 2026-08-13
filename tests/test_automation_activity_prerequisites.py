from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

from app import db as db_module
import migrate_sqlite_to_configured_db as data_migrator
from app.data_migration_manifest import MANIFEST_BY_TABLE
from app.db import ADDITIVE_INDEXES, initialize_database
from app.services.task_reminder_service import TaskReminderService
from app.utils import canonical_utc_timestamp


INDEXES = {
    "scheduler": "idx_internal_notification_schedule_runs_org_recipient_finished",
    "task_reminders": "idx_task_reminder_outbox_attempts_org_attempted",
    "knowledge": "idx_knowledge_processing_jobs_org_finished",
    "email": "idx_email_import_runs_org_finished",
    "ksef": "idx_ksef_import_runs_org_finished",
    "automation": "idx_automation_executions_org_executed",
}

QUERIES = {
    "scheduler": """
        SELECT internal_notification_schedule_run_id, status, finished_at,
               candidates_count, created_count, existing_count
        FROM internal_notification_schedule_runs
        WHERE organization_id = ? AND recipient_user_id = ? AND finished_at IS NOT NULL
          AND (status = 'failed' OR (status = 'succeeded' AND COALESCE(created_count, 0) > 0))
        ORDER BY finished_at DESC, internal_notification_schedule_run_id DESC LIMIT ?
    """,
    "task_reminders": """
        SELECT a.task_reminder_outbox_attempt_id, a.outcome, a.attempted_at
        FROM task_reminder_outbox_attempts a
        JOIN tasks t ON t.task_id = a.task_id
        WHERE a.organization_id = ?
          AND (t.owner_user_id = ? OR t.assigned_user_id = ? OR EXISTS (
              SELECT 1 FROM task_visibility_users tvu
              WHERE tvu.task_id = t.task_id AND tvu.user_id = ?
          ))
          AND a.outcome IN ('sent', 'failed', 'dead_letter')
          AND (a.attempted_at LIKE '%+00:00' OR a.attempted_at LIKE '%Z')
        ORDER BY a.attempted_at DESC, a.task_reminder_outbox_attempt_id DESC LIMIT ?
    """,
    "knowledge": """
        SELECT knowledge_processing_job_id, job_type, status, finished_at
        FROM knowledge_processing_jobs
        WHERE organization_id = ? AND status IN ('completed', 'failed') AND finished_at IS NOT NULL
        ORDER BY finished_at DESC, knowledge_processing_job_id DESC LIMIT ?
    """,
    "email": """
        SELECT email_import_run_id, trigger_mode, status, finished_at,
               imported_invoice_count, skipped_existing_count, skipped_error_count
        FROM email_import_runs
        WHERE organization_id = ? AND status IN ('completed', 'completed_with_issues', 'failed')
          AND finished_at IS NOT NULL
        ORDER BY finished_at DESC, email_import_run_id DESC LIMIT ?
    """,
    "ksef": """
        SELECT ksef_import_run_id, trigger_mode, status, finished_at,
               imported_invoice_count, skipped_existing_count, skipped_error_count
        FROM ksef_import_runs
        WHERE organization_id = ? AND status IN ('completed', 'completed_with_issues', 'failed')
          AND finished_at IS NOT NULL
        ORDER BY finished_at DESC, ksef_import_run_id DESC LIMIT ?
    """,
    "automation": """
        SELECT automation_execution_id, automation_rule_id, execution_status, executed_at
        FROM automation_executions
        WHERE organization_id = ? AND execution_status IN ('success', 'failed')
        ORDER BY executed_at DESC, automation_execution_id DESC LIMIT ?
    """,
}

PARAMS = {
    "scheduler": (1, 10, 3),
    "task_reminders": (1, 10, 10, 10, 3),
    "knowledge": (1, 3),
    "email": (1, 3),
    "ksef": (1, 3),
    "automation": (1, 3),
}


class AutomationActivityTimestampTests(unittest.TestCase):
    def test_canonical_contract_rejects_legacy_invalid_null_and_non_utc(self) -> None:
        self.assertEqual(canonical_utc_timestamp("2026-08-13T20:15:00+00:00"), "2026-08-13T20:15:00+00:00")
        self.assertEqual(canonical_utc_timestamp("2026-08-13T20:15:00Z"), "2026-08-13T20:15:00+00:00")
        self.assertIsNone(canonical_utc_timestamp("2026-08-13T20:15:00"))
        self.assertIsNone(canonical_utc_timestamp("2026-08-13T22:15:00+02:00"))
        self.assertIsNone(canonical_utc_timestamp("invalid"))
        self.assertIsNone(canonical_utc_timestamp(None))

    def test_warsaw_dst_transitions_remain_distinct_in_utc_storage(self) -> None:
        warsaw = ZoneInfo("Europe/Warsaw")
        spring_before = datetime(2026, 3, 29, 1, 30, tzinfo=warsaw).astimezone(timezone.utc).isoformat()
        spring_after = datetime(2026, 3, 29, 3, 30, tzinfo=warsaw).astimezone(timezone.utc).isoformat()
        self.assertNotEqual(canonical_utc_timestamp(spring_before), canonical_utc_timestamp(spring_after))

        fall_first = datetime(2026, 10, 25, 2, 30, tzinfo=warsaw, fold=0).astimezone(timezone.utc).isoformat()
        fall_second = datetime(2026, 10, 25, 2, 30, tzinfo=warsaw, fold=1).astimezone(timezone.utc).isoformat()
        self.assertNotEqual(fall_first, fall_second)
        self.assertNotEqual(canonical_utc_timestamp(fall_first), canonical_utc_timestamp(fall_second))
        self.assertIsNone(canonical_utc_timestamp("2026-10-25T02:30:00"))

    def test_migrator_preserves_aware_and_distinguishes_legacy_attempt_timestamps(self) -> None:
        spec = MANIFEST_BY_TABLE["task_reminder_outbox_attempts"]
        self.assertIn("attempted_at", spec.timestamp_columns)
        self.assertEqual(
            data_migrator.canonical_value(spec, "attempted_at", "2026-08-13T20:15:00+00:00"),
            {"timestamp": "2026-08-13T20:15:00.000000Z"},
        )
        self.assertEqual(
            data_migrator.canonical_value(spec, "attempted_at", "2026-08-13T20:15:00"),
            {"timestamp": "naive:2026-08-13T20:15:00"},
        )

    def test_attempt_writer_uses_utc_only_for_attempt_audit_record(self) -> None:
        task_repository = MagicMock()
        task_repository.get_by_id.return_value = None
        outbox_repository = MagicMock()
        service = TaskReminderService(
            task_repository=task_repository,
            event_repository=MagicMock(),
            outbox_repository=outbox_repository,
            organization_repository=MagicMock(),
            telegram_adapter=MagicMock(),
        )
        delivery = {
            "task_reminder_outbox_id": 7, "organization_id": 1, "task_id": 8,
            "delivery_channel": "telegram", "attempt_count": 1,
        }
        with patch("app.services.task_reminder_service.now_local_datetime_value", return_value="2026-10-25T02:30"), patch(
            "app.services.task_reminder_service.now_iso", return_value="2026-10-25T01:30:00+00:00"
        ):
            self.assertEqual(service._process_outbox_delivery(delivery, worker_name="test"), "skipped")
        self.assertEqual(outbox_repository.mark_cancelled.call_args.kwargs["cancelled_at"], "2026-10-25T02:30")
        self.assertEqual(outbox_repository.create_attempt.call_args.kwargs["attempted_at"], "2026-10-25T01:30:00+00:00")


class AutomationActivityQueryContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name) / "activity.sqlite3"
        with patch("app.db.SQLITE_DB_PATH", self.path):
            initialize_database()
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = OFF")
        self._seed()

    def tearDown(self) -> None:
        self.connection.close()
        self.temporary.cleanup()

    def _seed(self) -> None:
        c = self.connection
        for task_id, org, owner in ((1, 1, 10), (2, 1, 20), (3, 2, 10)):
            c.execute("""INSERT INTO tasks
                (task_id, organization_id, task_type, visibility_scope, owner_user_id, title, status, priority,
                 created_by_user_id, created_at, updated_at)
                VALUES (?, ?, 'zadanie', 'prywatne', ?, 'private', 'nowe', 'normalny', ?, 'x', 'x')""",
                (task_id, org, owner, owner))
        for row in (
            (1, 1, 10, "succeeded", 0, "2026-01-01T10:00:00+00:00"),
            (2, 1, 10, "succeeded", 2, "2026-01-01T11:00:00+00:00"),
            (3, 1, 10, "failed", 0, "2026-01-01T12:00:00+00:00"),
            (4, 1, 10, "running", 0, None),
            (5, 2, 10, "failed", 0, "2026-01-01T13:00:00+00:00"),
        ):
            c.execute("""INSERT INTO internal_notification_schedule_runs
                (internal_notification_schedule_run_id,schedule_id,organization_id,recipient_user_id,source_type,
                 scheduled_local_date,as_of_date,scheduled_for_utc,status,attempt_count,created_count,finished_at,created_at)
                VALUES (?,?,?,?,'billing_next_step_attention','2026-01-01','2026-01-01','2026-01-01T08:00:00+00:00',?,1,?,?,?)""",
                (row[0], row[0], row[1], row[2], row[3], row[4], row[5], row[5] or "x"))
        attempts = (
            (1, 1, 1, "sent", "2026-01-01T10:00:00"),
            (2, 1, 1, "retry", "2026-01-01T11:00:00+00:00"),
            (3, 1, 1, "sent", "2026-01-01T12:00:00+00:00"),
            (4, 1, 1, "dead_letter", "2026-01-01T12:00:00+00:00"),
            (5, 1, 2, "failed", "2026-01-01T13:00:00+00:00"),
            (6, 2, 3, "sent", "2026-01-01T14:00:00+00:00"),
        )
        for attempt_id, org, task_id, outcome, at in attempts:
            c.execute("""INSERT INTO task_reminder_outbox_attempts
                (task_reminder_outbox_attempt_id,task_reminder_outbox_id,organization_id,task_id,delivery_channel,
                 attempt_no,outcome,attempted_at,worker_name,created_at)
                VALUES (?,?,?,?,'telegram',1,? ,?,'test',?)""", (attempt_id, attempt_id, org, task_id, outcome, at, at))
        for table, id_column, statuses in (
            ("knowledge_processing_jobs", "knowledge_processing_job_id", ("completed", "failed", "pending")),
            ("email_import_runs", "email_import_run_id", ("completed", "completed_with_issues", "failed", "no_new_documents", "running")),
            ("ksef_import_runs", "ksef_import_run_id", ("completed", "completed_with_issues", "failed", "no_new_documents", "running")),
        ):
            for index, status in enumerate(statuses, 1):
                at = f"2026-01-02T0{index}:00:00+00:00"
                if table == "knowledge_processing_jobs":
                    c.execute(f"""INSERT INTO {table}
                        ({id_column},organization_id,job_type,status,source_storage_key,source_file_name,
                         source_content_hash,finished_at,created_at,updated_at)
                        VALUES (?,1,'ingest',?,'secret-key','secret.pdf','hash',?,?,?)""", (index, status, at, at, at))
                else:
                    c.execute(f"""INSERT INTO {table}
                        ({id_column},organization_id,trigger_mode,actor,started_at,finished_at,status,
                         imported_invoice_count,skipped_existing_count,skipped_error_count)
                        VALUES (?,1,'manual','private',?,?,?,1,2,3)""", (index, at, at, status))
            # Cross-tenant terminal row must never be visible.
            terminal = "completed" if table != "knowledge_processing_jobs" else "completed"
            if table == "knowledge_processing_jobs":
                c.execute(f"""INSERT INTO {table}
                    ({id_column},organization_id,job_type,status,source_storage_key,source_file_name,
                     source_content_hash,finished_at,created_at,updated_at)
                    VALUES (99,2,'ingest',?,'secret','secret','hash','2026-02-01T00:00:00+00:00','x','x')""", (terminal,))
            else:
                c.execute(f"""INSERT INTO {table}
                    ({id_column},organization_id,trigger_mode,actor,started_at,finished_at,status)
                    VALUES (99,2,'manual','private','x','2026-02-01T00:00:00+00:00',?)""", (terminal,))
        for execution_id, org, status, at in (
            (1,1,"success","2026-01-03T10:00:00+00:00"),
            (2,1,"failed","2026-01-03T10:00:00+00:00"),
            (3,2,"success","2026-02-03T10:00:00+00:00"),
        ):
            c.execute("""INSERT INTO automation_executions
                (automation_execution_id,automation_rule_id,organization_id,trigger_event_type,execution_status,executed_at)
                VALUES (?,1,?,'private-trigger',?,?)""", (execution_id, org, status, at))
        c.commit()

    def test_queries_are_scoped_terminal_bounded_safe_and_deterministic(self) -> None:
        before = self._table_hashes()
        results = {name: [dict(row) for row in self.connection.execute(QUERIES[name], PARAMS[name])] for name in QUERIES}
        self.assertEqual([row["internal_notification_schedule_run_id"] for row in results["scheduler"]], [3, 2])
        self.assertEqual([row["task_reminder_outbox_attempt_id"] for row in results["task_reminders"]], [4, 3])
        self.assertEqual([row["status"] for row in results["knowledge"]], ["failed", "completed"])
        self.assertEqual([row["status"] for row in results["email"]], ["failed", "completed_with_issues", "completed"])
        self.assertEqual([row["status"] for row in results["ksef"]], ["failed", "completed_with_issues", "completed"])
        self.assertEqual([row["automation_execution_id"] for row in results["automation"]], [2, 1])
        serialized = json.dumps(results).lower()
        for forbidden in ("secret.pdf", "secret-key", "private-trigger", "payload", "error_message"):
            self.assertNotIn(forbidden, serialized)
        legacy_attempt = self.connection.execute(
            "SELECT attempted_at FROM task_reminder_outbox_attempts WHERE task_reminder_outbox_attempt_id = 1"
        ).fetchone()[0]
        self.assertEqual(legacy_attempt, "2026-01-01T10:00:00")
        self.assertIsNone(canonical_utc_timestamp(legacy_attempt))
        self.assertEqual(before, self._table_hashes())

    def test_indexes_remove_temp_sort_from_each_exact_query_shape(self) -> None:
        for index_name in INDEXES.values():
            self.connection.execute(f'DROP INDEX "{index_name}"')
        before = {
            name: " | ".join(
                str(row[3]) for row in self.connection.execute("EXPLAIN QUERY PLAN " + QUERIES[name], PARAMS[name])
            )
            for name in QUERIES
        }
        for name, plan in before.items():
            self.assertIn("TEMP B-TREE FOR ORDER BY", plan, (name, plan))

        statements = "\n".join(ADDITIVE_INDEXES)
        for index_name in INDEXES.values():
            statement = next(
                item.strip()
                for item in statements.splitlines()
                if index_name in item
            )
            self.connection.execute(statement)
        after = {
            name: " | ".join(
                str(row[3]) for row in self.connection.execute("EXPLAIN QUERY PLAN " + QUERIES[name], PARAMS[name])
            )
            for name in QUERIES
        }
        for name, index_name in INDEXES.items():
            self.assertIn(index_name, after[name], (name, after[name]))
            self.assertNotIn("TEMP B-TREE FOR ORDER BY", after[name], (name, after[name]))

    def test_each_query_uses_required_ordering_index_without_temp_sort(self) -> None:
        for name, index_name in INDEXES.items():
            plan = " | ".join(str(row[3]) for row in self.connection.execute("EXPLAIN QUERY PLAN " + QUERIES[name], PARAMS[name]))
            self.assertIn(index_name, plan, (name, plan))
            self.assertNotIn("TEMP B-TREE FOR ORDER BY", plan, (name, plan))

    def _table_hashes(self) -> dict[str, str]:
        tables = [row[0] for row in self.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )]
        result = {}
        for table in tables:
            rows = [tuple(row) for row in self.connection.execute(f'SELECT * FROM "{table}" ORDER BY rowid')]
            result[table] = hashlib.sha256(json.dumps(rows, default=str).encode()).hexdigest()
        return result


class AutomationActivitySchemaTests(unittest.TestCase):
    def test_fresh_and_additive_upgrade_preserve_all_data(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "upgrade.sqlite3"
            with patch("app.db.SQLITE_DB_PATH", path):
                initialize_database()
            connection = sqlite3.connect(path)
            connection.execute("PRAGMA foreign_keys=OFF")
            connection.execute("""INSERT INTO task_reminder_outbox_attempts
                (task_reminder_outbox_attempt_id,task_reminder_outbox_id,organization_id,task_id,delivery_channel,
                 attempt_no,outcome,attempted_at,worker_name,created_at)
                VALUES (1,1,1,1,'telegram',1,'sent','2026-10-25T02:30:00','legacy','2026-10-25T02:30:00')""")
            for index_name in INDEXES.values():
                connection.execute(f'DROP INDEX "{index_name}"')
            connection.commit()
            before = self._snapshot(connection)
            connection.close()

            with patch("app.db.SQLITE_DB_PATH", path):
                initialize_database()
                initialize_database()
            connection = sqlite3.connect(path)
            try:
                self.assertEqual(before, self._snapshot(connection))
                tables = connection.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchone()[0]
                self.assertEqual(tables, 78)
                for table, index_name in self._index_tables().items():
                    occurrences = connection.execute(
                        "SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name=?", (index_name,)
                    ).fetchone()[0]
                    self.assertEqual(occurrences, 1, (table, index_name))
                self.assertEqual(connection.execute("SELECT attempted_at FROM task_reminder_outbox_attempts").fetchone()[0], "2026-10-25T02:30:00")
                self.assertEqual(connection.execute("PRAGMA quick_check").fetchone()[0], "ok")
            finally:
                connection.close()

    def test_indexes_are_additive_and_have_postgresql_portable_shape(self) -> None:
        statements = "\n".join(ADDITIVE_INDEXES)
        for index_name in INDEXES.values():
            self.assertIn(index_name, statements)
        self.assertNotIn("DROP ", statements.upper())
        self.assertNotIn("UPDATE ", statements.upper())
        self.assertNotIn("DELETE ", statements.upper())
        self.assertIn("idx_task_reminder_outbox_attempts_org_attempted", db_module.POSTGRES_SCHEMA)
        self.assertIn("idx_internal_notification_schedule_runs_org_recipient_finished", db_module.POSTGRES_SCHEMA)
        self.assertIn("idx_automation_executions_org_executed", db_module.POSTGRES_SCHEMA)

    @staticmethod
    def _index_tables() -> dict[str, str]:
        return {
            "internal_notification_schedule_runs": INDEXES["scheduler"],
            "task_reminder_outbox_attempts": INDEXES["task_reminders"],
            "knowledge_processing_jobs": INDEXES["knowledge"],
            "email_import_runs": INDEXES["email"],
            "ksef_import_runs": INDEXES["ksef"],
            "automation_executions": INDEXES["automation"],
        }

    @staticmethod
    def _snapshot(connection: sqlite3.Connection) -> dict[str, str]:
        result = {}
        tables = [row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )]
        for table in tables:
            rows = connection.execute(f'SELECT * FROM "{table}" ORDER BY rowid').fetchall()
            result[table] = hashlib.sha256(json.dumps(rows, default=str).encode()).hexdigest()
        return result


if __name__ == "__main__":
    unittest.main()
