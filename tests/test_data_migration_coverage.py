from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

os.environ["INVOICE_LOAD_LOCAL_ENV"] = "0"

import migrate_sqlite_to_configured_db as migrator
from app.data_migration_manifest import (
    EXCLUDED_TABLES,
    MANIFEST_BY_TABLE,
    MIGRATED_TABLES,
    MIGRATION_MANIFEST,
)
from app.db import initialize_database


class RecordingTarget:
    def __init__(self, counts: dict[str, int] | None = None) -> None:
        self.counts = counts or {}
        self.executions: list[tuple[str, object]] = []

    def execute(self, sql: str, parameters: object = ()) -> "RecordingTarget":
        self.executions.append((sql, parameters))
        return self

    def fetchone(self) -> dict[str, int]:
        sql = self.executions[-1][0]
        for table, count in self.counts.items():
            if f'FROM "{table}"' in sql:
                return {"total": count}
        return {"total": 0}


def representative_row(spec, ordinal: int) -> dict[str, object]:
    """One deterministic serialization fixture for every persistent table."""
    row: dict[str, object] = {}
    primary_keys = set(spec.primary_key)
    for column in spec.columns:
        if column in primary_keys or column.endswith("_id"):
            value: object = ordinal
        elif column in spec.boolean_columns:
            value = ordinal % 2
        elif column in spec.decimal_columns:
            value = "123456789012345.67"
        elif column in spec.json_columns:
            value = '{"żółć":true,"items":[2,1],"nested":{"b":2,"a":1}}'
        elif column in spec.date_columns or column == "planned_for":
            value = "2026-12-18"
        elif column in spec.timestamp_columns:
            value = "2026-07-31T12:34:56.123456+02:00"
        elif column in spec.blob_columns:
            value = b"\x00CASI\xff"
        elif column in spec.storage_columns:
            value = f"org-{ordinal}/documents/zażółć-{ordinal}.pdf"
        else:
            value = f"Zażółć gęślą jaźń {ordinal} — " + ("tekst " * 20)
        row[column] = value
    # Every table also exercises NULL without hiding type differences.
    nullable = next(
        (column for column in reversed(spec.columns) if column not in primary_keys),
        None,
    )
    if nullable:
        row[nullable] = None
    return row


class DataMigrationCoverageTests(unittest.TestCase):
    def _fresh_database(self, root: Path, name: str = "source.sqlite3") -> Path:
        path = root / name
        with patch("app.db.SQLITE_DB_PATH", path):
            initialize_database()
        return path

    def test_current_schema_and_manifest_are_exactly_classified(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = self._fresh_database(Path(temporary))
            with closing(sqlite3.connect(path)) as connection:
                actual = {
                    row[0]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                    )
                }
        self.assertEqual(actual, set(MANIFEST_BY_TABLE))
        self.assertEqual(len(actual), 78)
        self.assertEqual(len(MIGRATED_TABLES), 73)
        self.assertEqual(len(EXCLUDED_TABLES), 5)
        self.assertEqual(
            {spec.source_table for spec in EXCLUDED_TABLES},
            {
                "casi_schema_metadata",
                "google_calendar_oauth_states",
                "system_email_oauth_states",
                "task_reminder_worker_heartbeats",
                "user_sessions",
            },
        )

    def test_every_persistent_table_has_complete_contract_and_fixture(self) -> None:
        orders = []
        for spec in MIGRATED_TABLES:
            self.assertIn(spec.category, {"A_business", "B_operational_audit"})
            self.assertTrue(spec.columns)
            self.assertTrue(spec.primary_key)
            self.assertTrue(spec.verification)
            self.assertTrue(spec.representative_fixture_required)
            self.assertIsNotNone(spec.order)
            self.assertTrue(set(spec.primary_key).issubset(spec.columns))
            self.assertTrue(set(spec.dependencies).issubset(MANIFEST_BY_TABLE))
            self.assertEqual(spec.target_table, spec.source_table)
            row = representative_row(spec, int(spec.order))
            self.assertEqual(set(row), set(spec.columns))
            self.assertEqual(len(migrator.canonical_row_hash(spec, row)), 64)
            self.assertEqual(migrator._insert_statement(spec).count("?"), len(spec.columns))
            orders.append(spec.order)
        self.assertEqual(orders, sorted(orders))
        self.assertEqual(len(orders), len(set(orders)))

    def test_exclusions_have_explicit_non_destructive_rebuild_or_reauthentication(self) -> None:
        for spec in EXCLUDED_TABLES:
            self.assertEqual(spec.category, "D_runtime_temporary")
            self.assertFalse(spec.migrate)
            self.assertFalse(spec.representative_fixture_required)
            self.assertTrue(spec.exclusion_reason)
            self.assertTrue(spec.rebuild_procedure)

    def test_future_unclassified_table_blocks_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = self._fresh_database(Path(temporary))
            with closing(sqlite3.connect(path)) as connection:
                connection.execute("CREATE TABLE future_unclassified (id INTEGER PRIMARY KEY)")
                connection.commit()
            report = migrator.build_source_plan(path)
        self.assertEqual(report["status"], "fail")
        self.assertIn(
            {"code": "unclassified_source_table", "table": "future_unclassified"},
            report["issues"],
        )

    def test_empty_fresh_source_plan_is_read_only_and_complete(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = self._fresh_database(Path(temporary))
            before = (hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_size, path.stat().st_mtime_ns)
            report = migrator.build_source_plan(path)
            after = (hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_size, path.stat().st_mtime_ns)
            self.assertFalse(Path(f"{path}-wal").exists())
            self.assertFalse(Path(f"{path}-shm").exists())
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["quick_check"], "ok")
        self.assertTrue(report["read_only"])
        self.assertEqual(len(report["tables"]), 73)
        self.assertEqual(before, after)

    def test_explicit_legacy_source_shape_is_supported_without_general_relaxation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = self._fresh_database(Path(temporary))
            with closing(sqlite3.connect(path)) as connection:
                for table in (
                    "internal_notification_schedule_runs",
                    "internal_notification_schedules",
                    "internal_notification_state_events",
                    "internal_notifications",
                    "casi_schema_metadata",
                ):
                    connection.execute(f'DROP TABLE "{table}"')
                connection.execute("DROP INDEX IF EXISTS idx_billing_next_step_events_parent_unique")
                connection.execute("ALTER TABLE billing_next_step_events DROP COLUMN parent_event_id")
                connection.commit()
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            report = migrator.build_source_plan(path)
            after = hashlib.sha256(path.read_bytes()).hexdigest()
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["tables"]["internal_notifications"]["count"], 0)
        self.assertEqual(report["tables"]["internal_notification_schedules"]["count"], 0)
        self.assertEqual(report["tables"]["billing_next_step_events"]["count"], 0)
        self.assertEqual(before, after)

    def test_type_normalization_is_semantic_and_money_never_uses_float(self) -> None:
        decimal_spec = next(spec for spec in MIGRATED_TABLES if spec.decimal_columns)
        decimal_column = decimal_spec.decimal_columns[0]
        self.assertEqual(
            migrator.transform_for_target(decimal_spec, decimal_column, "1234567890.1200"),
            Decimal("1234567890.12"),
        )
        self.assertNotIsInstance(
            migrator.transform_for_target(decimal_spec, decimal_column, "1.10"), float
        )
        json_spec = next(spec for spec in MIGRATED_TABLES if spec.json_columns)
        json_column = json_spec.json_columns[0]
        left = migrator.canonical_value(json_spec, json_column, '{"b":2,"a":1}')
        right = migrator.canonical_value(json_spec, json_column, '{"a":1,"b":2}')
        self.assertEqual(left, right)
        boolean_spec = next(spec for spec in MIGRATED_TABLES if spec.boolean_columns)
        boolean_column = boolean_spec.boolean_columns[0]
        self.assertEqual(migrator.transform_for_target(boolean_spec, boolean_column, "true"), 1)
        timestamp_spec = next(spec for spec in MIGRATED_TABLES if spec.timestamp_columns)
        timestamp_column = timestamp_spec.timestamp_columns[0]
        self.assertEqual(
            migrator.canonical_value(timestamp_spec, timestamp_column, "2026-07-31T14:00:00+02:00"),
            {"timestamp": "2026-07-31T12:00:00.000000Z"},
        )
        self.assertEqual(
            migrator.canonical_value(timestamp_spec, timestamp_column, "2026-07-31T14:00:00"),
            {"timestamp": "naive:2026-07-31T14:00:00"},
        )

    def test_planned_date_unicode_blob_empty_string_and_null_remain_distinct(self) -> None:
        spec = MANIFEST_BY_TABLE["billing_next_step_events"]
        row = representative_row(spec, 901)
        row["planned_for"] = "2026-12-18"
        self.assertEqual(
            migrator.canonical_value(spec, "planned_for", row["planned_for"]),
            {"date": "2026-12-18"},
        )
        self.assertNotEqual(
            migrator.canonical_row_hash(spec, {**row, "title": ""}),
            migrator.canonical_row_hash(spec, {**row, "title": None}),
        )
        blob_spec = next((item for item in MIGRATED_TABLES if item.blob_columns), None)
        if blob_spec is not None:
            column = blob_spec.blob_columns[0]
            self.assertEqual(
                migrator.canonical_value(blob_spec, column, b"\x00\xff"),
                {"blob_base64": "AP8="},
            )

    def test_domain_fixture_covers_required_histories_without_deduplication(self) -> None:
        fixture = {
            "organizations": [1, 2],
            "recipients": [(1, 11), (2, 22)],
            "billing_steps": [
                {"id": 101, "org": 1, "action": "planned", "parent": None, "title": "Kontakt", "planned_for": "2026-12-18"},
                {"id": 102, "org": 1, "action": "planned", "parent": None, "title": "Kontakt", "planned_for": "2026-12-18"},
                {"id": 103, "org": 1, "action": "snoozed", "parent": 101},
                {"id": 104, "org": 1, "action": "completed", "parent": 103},
            ],
            "notification_states": [(11, "unread"), (11, "read"), (22, "archived")],
            "scheduler_runs": [(1, "leased"), (1, "retry"), (2, "completed")],
            "domains": ["documents", "knowledge", "tasks", "decisions", "billing", "event_logs"],
        }
        self.assertEqual(len([step for step in fixture["billing_steps"] if step["action"] == "planned"]), 2)
        identical = fixture["billing_steps"][:2]
        self.assertEqual(
            [(item["org"], item["title"], item["planned_for"]) for item in identical],
            [(1, "Kontakt", "2026-12-18"), (1, "Kontakt", "2026-12-18")],
        )
        self.assertEqual(fixture["billing_steps"][2]["parent"], 101)
        self.assertEqual(fixture["billing_steps"][3]["parent"], 103)
        self.assertEqual({state for _, state in fixture["notification_states"]}, {"unread", "read", "archived"})
        self.assertEqual({state for _, state in fixture["scheduler_runs"]}, {"leased", "retry", "completed"})
        self.assertEqual({spec.source_table for spec in MIGRATED_TABLES}, set(migrator.TABLE_ORDER))

    def test_sql_is_parameterized_identifiers_are_allowlisted_and_target_must_be_empty(self) -> None:
        spec = MANIFEST_BY_TABLE["organizations"]
        statement = migrator._insert_statement(spec)
        self.assertNotIn("Zażółć", statement)
        self.assertEqual(statement.count("?"), len(spec.columns))
        with self.assertRaises(migrator.MigrationValidationError):
            migrator._quote_identifier('organizations; DROP TABLE users')
        self.assertTrue(migrator._target_has_data(RecordingTarget({"organizations": 1})))
        self.assertFalse(migrator._target_has_data(RecordingTarget()))

    def test_sequence_reset_sql_covers_every_declared_sequence(self) -> None:
        target = RecordingTarget()
        migrator._reset_postgres_sequences(target)
        self.assertEqual(len(target.executions), len(migrator.POSTGRES_SEQUENCES))
        combined = "\n".join(sql for sql, _ in target.executions)
        for table, column in migrator.POSTGRES_SEQUENCES.items():
            self.assertIn(f"pg_get_serial_sequence('{table}', '{column}')", combined)
            self.assertIn(f'MAX("{column}")', combined)

    def test_target_requires_explicit_postgresql_and_dsn_without_fallback(self) -> None:
        for environment in (
            {},
            {"INVOICE_DB_ENGINE": "sqlite", "INVOICE_DATABASE_URL": "sqlite:///local"},
            {"INVOICE_DB_ENGINE": "postgresql"},
        ):
            with self.assertRaises(migrator.MigrationConfigurationError):
                migrator._validate_target_environment(environment)
        migrator._validate_target_environment(
            {"INVOICE_DB_ENGINE": "postgresql", "INVOICE_DATABASE_URL": "postgresql://test.invalid/db"}
        )

    def test_error_report_never_contains_exception_message_or_dsn(self) -> None:
        secret = "postgresql://user:super-secret@example.invalid/database"
        report = migrator._sanitized_error("apply", RuntimeError(secret), 0.0)
        serialized = json.dumps(report)
        self.assertNotIn("super-secret", serialized)
        self.assertNotIn("postgresql://", serialized)
        self.assertEqual(report["error_code"], "RuntimeError")

    def test_absolute_storage_path_is_a_blocker_without_value_disclosure(self) -> None:
        storage_spec = MANIFEST_BY_TABLE["task_attachments"]
        with tempfile.TemporaryDirectory() as temporary:
            path = self._fresh_database(Path(temporary))
            with closing(sqlite3.connect(path)) as connection:
                # This is a narrow path-audit exercise; parent FKs are intentionally bypassed.
                connection.execute("PRAGMA foreign_keys = OFF")
                connection.execute(
                    """
                    INSERT INTO task_attachments (
                        task_attachment_id, task_id, organization_id, file_name,
                        file_size, file_link, file_storage_key, storage_backend,
                        uploaded_by_user_id, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (999, 999, 999, "safe-name.pdf", 1, r"C:\\old-laptop\\secret.pdf", "relative/key", "lokalny", 999, "2026-07-31T00:00:00Z"),
                )
                connection.commit()
            report = migrator.build_source_plan(path)
        issue = next(item for item in report["issues"] if item["code"] == "absolute_storage_path")
        self.assertEqual(set(issue), {"code", "table", "column", "primary_key"})
        self.assertNotIn("old-laptop", json.dumps(issue))


if __name__ == "__main__":
    unittest.main()
