from __future__ import annotations

import sqlite3
import tempfile
import threading
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import app.db as db_module
from app.data_migration_manifest import EXCLUDED_TABLES, MIGRATED_TABLES, MIGRATION_MANIFEST
from app.repositories.automation_repository import AutomationRepository
from app.services.automation_public_projection import (
    project_public_automation_execution,
    project_public_automation_rule,
)
from app.services.automation_rule_definition import get_automation_rule_catalog
from app.services.automation_service import AutomationRuleBusyError, AutomationService
from app.utils import json_dumps


NOW = "2026-10-24T10:00:00+00:00"
LATER = "2026-10-24T10:01:00+00:00"
AFTER_EXPIRY = "2026-10-24T10:02:00+00:00"


def _initialize(path: Path) -> None:
    with patch("app.db.SQLITE_DB_PATH", path):
        db_module.initialize_database()


def _downgrade_automation_schema(path: Path) -> None:
    _initialize(path)
    connection = sqlite3.connect(path)
    connection.execute("DROP INDEX idx_automation_executions_rule_event_unique")
    connection.execute("ALTER TABLE automation_rules DROP COLUMN processing_claim_token")
    connection.execute("ALTER TABLE automation_rules DROP COLUMN processing_claimed_at")
    connection.execute("ALTER TABLE automation_rules DROP COLUMN processing_lease_until")
    connection.commit()
    connection.close()


def _insert_organization_and_rules(path: Path, *, rules: int = 2, organizations: int = 1) -> None:
    connection = sqlite3.connect(path)
    for organization_id in range(1, organizations + 1):
        connection.execute(
            "INSERT INTO organizations(organization_id,name,slug,created_at,updated_at) VALUES(?,?,?,?,?)",
            (organization_id, f"Org {organization_id}", f"org-{organization_id}", NOW, NOW),
        )
    for rule_id in range(1, rules + 1):
        organization_id = min(rule_id, organizations)
        connection.execute(
            """
            INSERT INTO automation_rules(
                automation_rule_id, organization_id, rule_slug, rule_name, trigger_event_type,
                conditions_json, actions_json, is_active, last_processed_event_log_id,
                execution_count, created_at, updated_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                rule_id,
                organization_id,
                f"rule-{rule_id}",
                f"Rule {rule_id}",
                "work_item_created",
                "{}",
                '[{"type":"create_inbox_item","title":"Synthetic"}]',
                1,
                0,
                0,
                NOW,
                NOW,
            ),
        )
    connection.commit()
    connection.close()


class AutomationIdempotencyMigrationTests(unittest.TestCase):
    def test_fresh_and_clean_upgrade_have_matching_claim_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fresh = root / "fresh.sqlite3"
            upgraded = root / "upgraded.sqlite3"
            _initialize(fresh)
            _downgrade_automation_schema(upgraded)
            _insert_organization_and_rules(upgraded, rules=1)
            connection = sqlite3.connect(upgraded)
            connection.execute(
                "UPDATE automation_rules SET is_active=0,last_processed_event_log_id=44,execution_count=7 WHERE automation_rule_id=1"
            )
            connection.commit()
            connection.close()
            _initialize(upgraded)

            expected_columns = {"processing_claim_token", "processing_claimed_at", "processing_lease_until"}
            for path in (fresh, upgraded):
                connection = sqlite3.connect(path)
                columns = {row[1] for row in connection.execute("PRAGMA table_info(automation_rules)")}
                indexes = {row[1] for row in connection.execute("PRAGMA index_list(automation_executions)")}
                sql = connection.execute(
                    "SELECT sql FROM sqlite_master WHERE type='index' AND name='idx_automation_executions_rule_event_unique'"
                ).fetchone()[0]
                self.assertTrue(expected_columns.issubset(columns))
                self.assertIn("idx_automation_executions_rule_event_unique", indexes)
                self.assertIn("WHERE event_log_id IS NOT NULL", sql)
                self.assertEqual(connection.execute("PRAGMA quick_check").fetchone()[0], "ok")
                self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
                connection.close()

            connection = sqlite3.connect(upgraded)
            row = connection.execute(
                """
                SELECT is_active,last_processed_event_log_id,execution_count,
                       processing_claim_token,processing_claimed_at,processing_lease_until
                FROM automation_rules WHERE automation_rule_id=1
                """
            ).fetchone()
            self.assertEqual(row, (0, 44, 7, None, None, None))
            connection.close()

    def test_duplicate_upgrade_fails_closed_without_cleanup_or_partial_index(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "duplicates.sqlite3"
            _downgrade_automation_schema(path)
            _insert_organization_and_rules(path, rules=1)
            connection = sqlite3.connect(path)
            for execution_id in (1, 2):
                connection.execute(
                    """
                    INSERT INTO automation_executions(
                        automation_execution_id,automation_rule_id,organization_id,event_log_id,
                        trigger_event_type,execution_status,executed_at
                    ) VALUES(?,?,?,?,?,?,?)
                    """,
                    (execution_id, 1, 1, 99, "work_item_created", "success", NOW),
                )
            connection.commit()
            connection.close()

            with self.assertRaisesRegex(RuntimeError, "Duplicate automation executions"):
                _initialize(path)

            connection = sqlite3.connect(path)
            self.assertEqual(
                connection.execute(
                    "SELECT COUNT(*) FROM automation_executions WHERE automation_rule_id=1 AND event_log_id=99"
                ).fetchone()[0],
                2,
            )
            self.assertIsNone(
                connection.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='index' AND name='idx_automation_executions_rule_event_unique'"
                ).fetchone()
            )
            columns = {row[1] for row in connection.execute("PRAGMA table_info(automation_rules)")}
            self.assertNotIn("processing_claim_token", columns)
            connection.close()

    def test_partial_unique_index_allows_null_and_legal_fan_out(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "legal.sqlite3"
            _downgrade_automation_schema(path)
            _insert_organization_and_rules(path, rules=2)
            connection = sqlite3.connect(path)
            rows = (
                (1, 1, 1, None),
                (2, 1, 1, None),
                (3, 1, 1, 10),
                (4, 1, 1, 11),
                (5, 2, 1, 10),
            )
            for execution_id, rule_id, organization_id, event_id in rows:
                connection.execute(
                    """
                    INSERT INTO automation_executions(
                        automation_execution_id,automation_rule_id,organization_id,event_log_id,
                        trigger_event_type,execution_status,executed_at
                    ) VALUES(?,?,?,?,?,?,?)
                    """,
                    (execution_id, rule_id, organization_id, event_id, "work_item_created", "success", NOW),
                )
            connection.commit()
            connection.close()
            _initialize(path)
            connection = sqlite3.connect(path)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM automation_executions").fetchone()[0], 5)
            self.assertEqual(connection.execute("PRAGMA quick_check").fetchone()[0], "ok")
            connection.close()

    def test_manifest_and_postgresql_schema_remain_provider_neutral(self) -> None:
        self.assertEqual((len(MIGRATION_MANIFEST), len(MIGRATED_TABLES), len(EXCLUDED_TABLES)), (78, 73, 5))
        self.assertIn("processing_claim_token TEXT", db_module.POSTGRES_SCHEMA)
        self.assertIn("processing_lease_until TEXT", db_module.POSTGRES_SCHEMA)
        self.assertIn("idx_automation_executions_rule_event_unique", db_module.POSTGRES_SCHEMA)
        self.assertIn("WHERE event_log_id IS NOT NULL", db_module.POSTGRES_SCHEMA)


class AutomationRepositoryClaimTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name) / "claims.sqlite3"
        self.path_patch = patch("app.db.SQLITE_DB_PATH", self.path)
        self.path_patch.start()
        db_module.initialize_database()
        _insert_organization_and_rules(self.path, rules=2, organizations=2)
        self.repository = AutomationRepository()

    def tearDown(self) -> None:
        self.path_patch.stop()
        self.temporary.cleanup()

    def _execution_payload(self, *, rule_id: int = 1, organization_id: int = 1, event_id: int = 10):
        return {
            "automation_rule_id": rule_id,
            "organization_id": organization_id,
            "event_log_id": event_id,
            "trigger_event_type": "work_item_created",
            "input_json": "{}",
            "executed_at": NOW,
        }

    def test_execution_claim_identity_completion_and_terminal_immutability(self) -> None:
        first = self.repository.try_claim_execution(self._execution_payload())
        duplicate = self.repository.try_claim_execution(self._execution_payload())
        different_event = self.repository.try_claim_execution(self._execution_payload(event_id=11))
        different_rule = self.repository.try_claim_execution(
            self._execution_payload(rule_id=2, organization_id=2, event_id=10)
        )
        self.assertTrue(first["claimed"])
        self.assertEqual(duplicate["reason"], "already_claimed")
        self.assertTrue(different_event["claimed"])
        self.assertTrue(different_rule["claimed"])
        execution_id = int(first["automation_execution_id"])
        self.assertTrue(
            self.repository.complete_execution(
                execution_id,
                execution_status="success",
                result_json='{"ok":true}',
                executed_at=LATER,
            )
        )
        before = self.repository.get_execution_by_id(execution_id)
        self.assertFalse(
            self.repository.complete_execution(
                execution_id,
                execution_status="failed",
                error_message="must-not-replace-terminal",
                executed_at=AFTER_EXPIRY,
            )
        )
        self.assertEqual(before, self.repository.get_execution_by_id(execution_id))
        with self.assertRaisesRegex(ValueError, "does not belong"):
            self.repository.try_claim_execution(self._execution_payload(organization_id=2, event_id=12))

    def test_rule_lease_owner_renew_release_expiry_and_stale_owner(self) -> None:
        self.assertTrue(
            self.repository.acquire_rule_claim(
                automation_rule_id=1,
                organization_id=1,
                claim_token="owner-a",
                claimed_at=NOW,
                lease_until=LATER,
            )
        )
        self.assertFalse(
            self.repository.acquire_rule_claim(
                automation_rule_id=1,
                organization_id=1,
                claim_token="owner-b",
                claimed_at=NOW,
                lease_until=LATER,
            )
        )
        self.assertFalse(
            self.repository.renew_rule_claim(
                automation_rule_id=1,
                organization_id=1,
                claim_token="wrong",
                now=NOW,
                lease_until=AFTER_EXPIRY,
            )
        )
        self.assertTrue(
            self.repository.renew_rule_claim(
                automation_rule_id=1,
                organization_id=1,
                claim_token="owner-a",
                now=NOW,
                lease_until=LATER,
            )
        )
        self.assertFalse(
            self.repository.release_rule_claim(
                automation_rule_id=1, organization_id=1, claim_token="wrong"
            )
        )
        self.assertTrue(
            self.repository.acquire_rule_claim(
                automation_rule_id=1,
                organization_id=1,
                claim_token="owner-b",
                claimed_at=AFTER_EXPIRY,
                lease_until="2026-10-24T10:03:00+00:00",
            )
        )
        self.assertFalse(
            self.repository.release_rule_claim(
                automation_rule_id=1, organization_id=1, claim_token="owner-a"
            )
        )
        self.assertTrue(
            self.repository.release_rule_claim(
                automation_rule_id=1, organization_id=1, claim_token="owner-b"
            )
        )
        self.assertTrue(
            self.repository.acquire_rule_claim(
                automation_rule_id=1,
                organization_id=1,
                claim_token="owner-c",
                claimed_at=AFTER_EXPIRY,
                lease_until="2026-10-24T10:04:00+00:00",
            )
        )

    def test_real_execution_claim_race_has_one_winner(self) -> None:
        barrier = threading.Barrier(2)
        results: list[dict[str, object]] = []
        errors: list[BaseException] = []

        def compete() -> None:
            try:
                barrier.wait(timeout=5)
                results.append(self.repository.try_claim_execution(self._execution_payload(event_id=500)))
            except BaseException as error:
                errors.append(error)

        threads = [threading.Thread(target=compete) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)
        self.assertFalse(errors)
        self.assertEqual(sum(1 for result in results if result["claimed"]), 1)
        connection = sqlite3.connect(self.path)
        self.assertEqual(
            connection.execute(
                "SELECT COUNT(*) FROM automation_executions WHERE automation_rule_id=1 AND event_log_id=500"
            ).fetchone()[0],
            1,
        )
        connection.close()

    def test_different_rules_and_organizations_have_independent_leases(self) -> None:
        self.assertTrue(
            self.repository.acquire_rule_claim(
                automation_rule_id=1,
                organization_id=1,
                claim_token="org-a-rule-a",
                claimed_at=NOW,
                lease_until=LATER,
            )
        )
        self.assertTrue(
            self.repository.acquire_rule_claim(
                automation_rule_id=2,
                organization_id=2,
                claim_token="org-b-rule-b",
                claimed_at=NOW,
                lease_until=LATER,
            )
        )
        self.assertFalse(
            self.repository.acquire_rule_claim(
                automation_rule_id=1,
                organization_id=2,
                claim_token="cross-org",
                claimed_at=NOW,
                lease_until=LATER,
            )
        )

    def test_transient_execution_and_lease_fields_are_not_public(self) -> None:
        rule = self.repository.get_by_id(1, organization_id=1)
        rule.update(
            {
                "processing_claim_token": "TOKEN_FAKE",
                "processing_claimed_at": NOW,
                "processing_lease_until": LATER,
            }
        )
        projected_rule = project_public_automation_rule(rule)
        self.assertFalse(set(projected_rule).intersection(
            {"processing_claim_token", "processing_claimed_at", "processing_lease_until"}
        ))
        claim = self.repository.try_claim_execution(self._execution_payload(event_id=700))
        execution = self.repository.get_execution_by_id(int(claim["automation_execution_id"]))
        projected_execution = project_public_automation_execution(execution)
        self.assertNotIn("input_json", projected_execution)
        self.assertNotIn("result_json", projected_execution)
        self.assertNotIn("error_message", projected_execution)
        self.assertEqual(self.repository.list_executions(organization_id=1), [])
        self.assertNotIn("claim", str(get_automation_rule_catalog()).lower())
        self.assertNotIn("token_fake", str(projected_rule).lower())


class _SyntheticEventRepository:
    def __init__(self, events: list[dict[str, object]]) -> None:
        self.events = events
        self.audit_events: list[dict[str, object]] = []

    def list_logs_after(self, cursor: int, *, organization_id: int, limit: int):
        return [
            dict(event)
            for event in self.events
            if int(event["id"]) > cursor and int(event["organization_id"]) == organization_id
        ][:limit]

    def log(self, **payload):
        self.audit_events.append(payload)
        return len(self.audit_events)


class _SyntheticIntakeService:
    def __init__(self, path: Path, *, fail: bool = False, entered=None, release=None) -> None:
        self.path = path
        self.fail = fail
        self.entered = entered
        self.release = release
        self.calls = 0
        self.claim_statuses: list[str] = []

    def create_item(self, payload, *, actor_user, actor, organization_id):
        self.calls += 1
        connection = sqlite3.connect(self.path)
        status = connection.execute(
            "SELECT execution_status FROM automation_executions WHERE automation_rule_id=? AND event_log_id=?",
            (int(payload["metadata_json"]["rule_id"]), int(payload["metadata_json"]["trigger_event_id"])),
        ).fetchone()
        connection.close()
        self.claim_statuses.append(status[0] if status else "missing")
        if self.entered is not None:
            self.entered.set()
        if self.release is not None:
            self.release.wait(timeout=10)
        if self.fail:
            raise RuntimeError("synthetic handler failure")
        return {"intake_item_id": self.calls}


class _SimulatedCrash(BaseException):
    pass


class AutomationServiceIdempotencyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name) / "service.sqlite3"
        self.path_patch = patch("app.db.SQLITE_DB_PATH", self.path)
        self.path_patch.start()
        db_module.initialize_database()
        connection = sqlite3.connect(self.path)
        connection.execute(
            "INSERT INTO organizations(organization_id,name,slug,created_at,updated_at) VALUES(1,'Org','org',?,?)",
            (NOW, NOW),
        )
        connection.commit()
        connection.close()
        self.repository = AutomationRepository()
        self.rule_id = self.repository.create(
            {
                "organization_id": 1,
                "rule_slug": "service-rule",
                "rule_name": "Service rule",
                "trigger_event_type": "work_item_created",
                "conditions_json": "{}",
                "actions_json": json_dumps(
                    [{"type": "create_inbox_item", "title": "Literal", "description": "Synthetic"}]
                ),
            }
        )
        self.events = [
            {
                "id": 100,
                "organization_id": 1,
                "event_type": "work_item_created",
                "source": "TEST",
                "status_after": "nowe",
                "decision_reason": "synthetic",
                "details": "SECRET_FAKE",
            }
        ]
        self.event_repository = _SyntheticEventRepository(self.events)

    def tearDown(self) -> None:
        self.path_patch.stop()
        self.temporary.cleanup()

    def _service(self, intake: _SyntheticIntakeService) -> AutomationService:
        return AutomationService(
            self.repository,
            self.event_repository,
            intake,
            clock=lambda: datetime(2026, 10, 24, 10, 0, tzinfo=timezone.utc),
        )

    def _reset_cursor(self) -> None:
        self.repository.update(self.rule_id, {"last_processed_event_log_id": 0})

    def _rows(self):
        connection = sqlite3.connect(self.path)
        rows = connection.execute(
            "SELECT * FROM automation_executions WHERE automation_rule_id=? ORDER BY automation_execution_id",
            (self.rule_id,),
        ).fetchall()
        connection.close()
        return rows

    def test_action_runs_only_after_claim_and_duplicate_sweep_is_noop(self) -> None:
        intake = _SyntheticIntakeService(self.path)
        service = self._service(intake)
        first = service.run_rule(
            self.rule_id, actor_user={"user_id": 1}, actor="synthetic", organization_id=1
        )
        self.assertEqual(first, {"processed": True, "executions": 1, "errors": 0})
        self.assertEqual(intake.claim_statuses, ["processing"])
        self._reset_cursor()
        second = service.run_rule(
            self.rule_id, actor_user={"user_id": 1}, actor="synthetic", organization_id=1
        )
        self.assertEqual(second, {"processed": True, "executions": 0, "errors": 0})
        self.assertEqual(intake.calls, 1)
        self.assertEqual(len(self._rows()), 1)
        rule = self.repository.get_by_id(self.rule_id, organization_id=1)
        self.assertEqual(int(rule["execution_count"]), 1)

    def test_handler_failure_is_terminal_and_never_retried(self) -> None:
        intake = _SyntheticIntakeService(self.path, fail=True)
        service = self._service(intake)
        result = service.run_rule(
            self.rule_id, actor_user={"user_id": 1}, actor="synthetic", organization_id=1
        )
        self.assertEqual(result, {"processed": True, "executions": 0, "errors": 1})
        self.assertEqual(self._rows()[0][5], "failed")
        self._reset_cursor()
        service.run_rule(self.rule_id, actor_user={"user_id": 1}, actor="synthetic", organization_id=1)
        self.assertEqual(intake.calls, 1)
        self.assertEqual(len(self._rows()), 1)

    def test_crash_before_action_and_after_action_are_fail_closed(self) -> None:
        rule = self.repository.get_by_id(self.rule_id, organization_id=1)
        claim = self.repository.try_claim_execution(
            {
                "automation_rule_id": self.rule_id,
                "organization_id": 1,
                "event_log_id": 100,
                "trigger_event_type": "work_item_created",
                "input_json": "{}",
                "executed_at": NOW,
            }
        )
        self.assertTrue(claim["claimed"])
        intake = _SyntheticIntakeService(self.path)
        self._service(intake)._process_rule(rule, manual=False)
        self.assertEqual(intake.calls, 0)
        self.assertEqual(self._rows()[0][5], "processing")

        connection = sqlite3.connect(self.path)
        connection.execute("DELETE FROM automation_executions")
        connection.execute("UPDATE automation_rules SET last_processed_event_log_id=0")
        connection.commit()
        connection.close()
        intake_after = _SyntheticIntakeService(self.path)
        service_after = self._service(intake_after)
        original_complete = self.repository.complete_execution
        with patch.object(self.repository, "complete_execution", side_effect=_SimulatedCrash()):
            with self.assertRaises(_SimulatedCrash):
                service_after.run_rule(
                    self.rule_id, actor_user={"user_id": 1}, actor="synthetic", organization_id=1
                )
        self.assertEqual(intake_after.calls, 1)
        self.assertEqual(self._rows()[0][5], "processing")
        self.repository.complete_execution = original_complete
        service_after.run_rule(
            self.rule_id, actor_user={"user_id": 1}, actor="synthetic", organization_id=1
        )
        self.assertEqual(intake_after.calls, 1)
        self.assertEqual(len(self._rows()), 1)

    def test_two_manual_runs_and_manual_processor_overlap_execute_once(self) -> None:
        entered = threading.Event()
        release = threading.Event()
        intake = _SyntheticIntakeService(self.path, entered=entered, release=release)
        service = self._service(intake)
        start = threading.Barrier(2)
        results: list[object] = []

        def manual_run() -> None:
            start.wait(timeout=5)
            try:
                results.append(
                    service.run_rule(
                        self.rule_id,
                        actor_user={"user_id": 1},
                        actor="synthetic",
                        organization_id=1,
                    )
                )
            except AutomationRuleBusyError as error:
                results.append(error.code)

        threads = [threading.Thread(target=manual_run) for _ in range(2)]
        for thread in threads:
            thread.start()
        self.assertTrue(entered.wait(timeout=10))
        release.set()
        for thread in threads:
            thread.join(timeout=10)
        self.assertEqual(intake.calls, 1)
        self.assertIn("automation_rule_busy", results)
        self.assertEqual(len(self._rows()), 1)

        self._reset_cursor()
        entered.clear()
        release.clear()
        connection = sqlite3.connect(self.path)
        connection.execute("DELETE FROM automation_executions")
        connection.commit()
        connection.close()
        manual_thread = threading.Thread(target=lambda: service.run_rule(
            self.rule_id, actor_user={"user_id": 1}, actor="synthetic", organization_id=1
        ))
        manual_thread.start()
        self.assertTrue(entered.wait(timeout=10))
        processor_result = service.process_pending_events(organization_id=1)
        release.set()
        manual_thread.join(timeout=10)
        self.assertEqual(processor_result, {"processed_rules": 0, "executions": 0, "errors": 0})
        self.assertEqual(intake.calls, 2)

    def test_lease_loss_stops_before_next_event(self) -> None:
        self.events.append(dict(self.events[0], id=101))
        intake = _SyntheticIntakeService(self.path)
        service = self._service(intake)
        original_renew = self.repository.renew_rule_claim
        calls = 0

        def controlled_renew(**kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                return False
            return original_renew(**kwargs)

        with patch.object(self.repository, "renew_rule_claim", side_effect=controlled_renew):
            result = service.run_rule(
                self.rule_id, actor_user={"user_id": 1}, actor="synthetic", organization_id=1
            )
        self.assertEqual(result, {"processed": True, "executions": 1, "errors": 0})
        self.assertEqual(intake.calls, 1)
        rule = self.repository.get_by_id(self.rule_id, organization_id=1)
        self.assertEqual(int(rule["last_processed_event_log_id"]), 0)


if __name__ == "__main__":
    unittest.main()
