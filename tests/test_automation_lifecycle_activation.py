from __future__ import annotations

import json
import sqlite3
import tempfile
import threading
import unittest
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import app.db as db_module
from app.repositories.automation_repository import (
    AUTOMATION_ACTIVATION_SERIALIZATION_ATTEMPTS,
    AutomationRepository,
)
from app.repositories.event_repository import EventRepository
from app.services.automation_service import AutomationRuleBusyError, AutomationService


NOW = datetime(2026, 10, 25, 10, 0, tzinfo=timezone.utc)
NOW_ISO = NOW.isoformat()
LEASE_UNTIL = "2026-10-25T10:05:00+00:00"
EXPIRED_LEASE = "2026-10-25T09:59:00+00:00"
ACTION = [{"type": "create_inbox_item", "title": "Synthetic", "description": "Synthetic"}]
ACTOR = {"user_id": 1}


class RecordingHandler:
    def __init__(self, *, fail_event_ids: set[int] | None = None, entered=None, release=None) -> None:
        self.calls: list[int] = []
        self.fail_event_ids = fail_event_ids or set()
        self.entered = entered
        self.release = release

    def __call__(self, rule, event, actions, *, actor_user, actor):
        event_id = int(event["id"])
        self.calls.append(event_id)
        if self.entered is not None and len(self.calls) == 1:
            self.entered.set()
        if self.release is not None and len(self.calls) == 1:
            self.release.wait(timeout=10)
        if event_id in self.fail_event_ids:
            raise RuntimeError("synthetic failure")
        return {"results": [{"event_id": event_id}]}


class AutomationLifecycleActivationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name) / "lifecycle.sqlite3"
        self.path_patch = patch("app.db.SQLITE_DB_PATH", self.path)
        self.path_patch.start()
        db_module.initialize_database()
        connection = sqlite3.connect(self.path)
        connection.executemany(
            "INSERT INTO organizations(organization_id,name,slug,created_at,updated_at) VALUES(?,?,?,?,?)",
            [
                (1, "Org A", "org-a", NOW_ISO, NOW_ISO),
                (2, "Org B", "org-b", NOW_ISO, NOW_ISO),
            ],
        )
        connection.execute(
            """
            INSERT INTO users(
                user_id,login,display_name,organization_id,password_hash,password_salt,role,is_active,created_at,updated_at
            ) VALUES(1,'owner','Owner',1,'x','x','system_owner',1,?,?)
            """,
            (NOW_ISO, NOW_ISO),
        )
        connection.commit()
        connection.close()
        self.repository = AutomationRepository()
        self.events = EventRepository()
        self.service = AutomationService(self.repository, self.events, clock=lambda: NOW)

    def tearDown(self) -> None:
        self.path_patch.stop()
        self.temporary.cleanup()

    def _payload(self, slug: str, *, active: bool | None = None) -> dict[str, object]:
        payload: dict[str, object] = {
            "rule_name": f"Rule {slug}",
            "rule_slug": slug,
            "trigger_event_type": "work_item_created",
            "conditions_json": {},
            "actions_json": ACTION,
        }
        if active is not None:
            payload["is_active"] = active
        return payload

    def _create(self, slug: str, *, active: bool | None = None, organization_id: int = 1) -> int:
        created = self.service.create_rule(
            self._payload(slug, active=active),
            actor_user=ACTOR,
            actor="synthetic",
            organization_id=organization_id,
        )
        return int(created["automation_rule_id"])

    def _event(self, *, organization_id: int = 1, label: str = "event") -> int:
        return self.events.log(
            event_type="work_item_created",
            invoice_id=None,
            organization_id=organization_id,
            source="TEST",
            status_before=None,
            status_after="nowe",
            decision_reason=label,
            actor="synthetic",
            details={"label": label},
        )

    def _events(self, count: int, *, organization_id: int = 1, label: str = "event") -> list[int]:
        return [self._event(organization_id=organization_id, label=f"{label}-{index}") for index in range(count)]

    def _rule(self, rule_id: int, *, organization_id: int = 1) -> dict[str, object]:
        rule = self.repository.get_by_id(rule_id, organization_id=organization_id)
        self.assertIsNotNone(rule)
        return rule

    def _execution_rows(self, rule_id: int) -> list[sqlite3.Row]:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT event_log_id, execution_status
            FROM automation_executions
            WHERE automation_rule_id=?
            ORDER BY automation_execution_id
            """,
            (rule_id,),
        ).fetchall()
        connection.close()
        return rows

    def _enable(self, rule_id: int, **fields: object) -> dict[str, object]:
        result = self.service.update_rule(
            rule_id,
            {**fields, "is_active": True},
            actor_user=ACTOR,
            actor="synthetic",
            organization_id=1,
        )
        self.assertIsNotNone(result)
        return result

    def _disable(self, rule_id: int) -> None:
        self.service.update_rule(
            rule_id,
            {"is_active": False},
            actor_user=ACTOR,
            actor="synthetic",
            organization_id=1,
        )

    def test_create_defaults_inactive_and_explicit_inactive_has_no_replay(self) -> None:
        self._events(4, label="history")
        default_id = self._create("default")
        explicit_id = self._create("explicit", active=False)
        self.assertEqual(int(self._rule(default_id)["is_active"]), 0)
        self.assertEqual(int(self._rule(explicit_id)["is_active"]), 0)
        handler = RecordingHandler()
        self.service._execute_actions = handler
        self.assertEqual(
            self.service.process_pending_events(organization_id=1),
            {"processed_rules": 0, "executions": 0, "errors": 0},
        )
        self.assertEqual(handler.calls, [])

    def test_explicit_active_create_is_atomic_and_starts_from_org_watermark(self) -> None:
        history = self._events(100, label="history")
        self._events(5, organization_id=2, label="other-org-high-id")
        rule_id = self._create("active", active=True)
        rule = self._rule(rule_id)
        self.assertEqual(int(rule["is_active"]), 1)
        self.assertEqual(int(rule["last_processed_event_log_id"]), history[-1])

        handler = RecordingHandler()
        self.service._execute_actions = handler
        self.service.process_pending_events(organization_id=1)
        self.assertEqual(handler.calls, [])
        post_activation = self._events(3, label="post-activation")
        self.service.process_pending_events(organization_id=1)
        self.assertEqual(handler.calls, post_activation)

    def test_first_enable_skips_all_existing_events_and_empty_org_uses_zero(self) -> None:
        self._events(100, label="before-create")
        rule_id = self._create("first-enable", active=False)
        self._events(5, label="before-enable")
        self._enable(rule_id)
        watermark = int(self._rule(rule_id)["last_processed_event_log_id"])
        post_enable = self._events(3, label="post-enable")
        handler = RecordingHandler()
        self.service._execute_actions = handler
        self.service.process_pending_events(organization_id=1)
        self.assertEqual(handler.calls, post_enable)
        self.assertTrue(all(event_id > watermark for event_id in handler.calls))

        empty_rule_id = self._create("empty-org", active=True, organization_id=2)
        self.assertEqual(int(self._rule(empty_rule_id, organization_id=2)["last_processed_event_log_id"]), 0)

    def test_disable_reenable_and_repeated_cycles_never_replay_disabled_backlog(self) -> None:
        rule_id = self._create("cycles", active=True)
        handler = RecordingHandler()
        self.service._execute_actions = handler
        initial = self._events(2, label="initial")
        self.service.process_pending_events(organization_id=1)
        self.assertEqual(handler.calls, initial)

        for cycle in range(2):
            self._disable(rule_id)
            self._events(20, label=f"disabled-{cycle}")
            self._enable(rule_id)
            expected = self._events(3, label=f"enabled-{cycle}")
            calls_before = len(handler.calls)
            self.service.process_pending_events(organization_id=1)
            self.assertEqual(handler.calls[calls_before:], expected)

    def test_metadata_and_active_to_active_patches_preserve_cursor(self) -> None:
        rule_id = self._create("patches", active=True)
        self._events(2, label="pending")
        before = int(self._rule(rule_id)["last_processed_event_log_id"])
        self.service.update_rule(
            rule_id,
            {"rule_name": "Renamed"},
            actor_user=ACTOR,
            actor="synthetic",
            organization_id=1,
        )
        self.assertEqual(int(self._rule(rule_id)["last_processed_event_log_id"]), before)
        self.service.update_rule(
            rule_id,
            {"conditions_json": {"status_after": "nowe"}, "is_active": True},
            actor_user=ACTOR,
            actor="synthetic",
            organization_id=1,
        )
        self.assertEqual(int(self._rule(rule_id)["last_processed_event_log_id"]), before)

    def test_activation_is_scoped_to_rule_and_organization_and_includes_automation_sources(self) -> None:
        rule_a = self._create("scope-a", active=False)
        rule_b = self._create("scope-b", active=False)
        foreign_rule = self._create("scope-foreign", active=False, organization_id=2)
        automation_event = self.events.log(
            event_type="automation_synthetic",
            invoice_id=None,
            organization_id=1,
            source="AUTOMATION",
            status_before=None,
            status_after=None,
            decision_reason="watermark source coverage",
            actor="synthetic",
            details={},
        )
        self._events(4, organization_id=2, label="foreign-high-id")
        before_b = dict(self._rule(rule_b))
        before_foreign = dict(self._rule(foreign_rule, organization_id=2))
        self._enable(rule_a)
        self.assertEqual(int(self._rule(rule_a)["last_processed_event_log_id"]), automation_event)
        self.assertEqual(self._rule(rule_b)["last_processed_event_log_id"], before_b["last_processed_event_log_id"])
        self.assertEqual(
            self._rule(foreign_rule, organization_id=2)["last_processed_event_log_id"],
            before_foreign["last_processed_event_log_id"],
        )

    def test_unmatched_event_advances_cursor_without_execution(self) -> None:
        rule_id = self._create("unmatched", active=True)
        event_id = self.events.log(
            event_type="invoice_created",
            invoice_id=None,
            organization_id=1,
            source="TEST",
            status_before=None,
            status_after="nowe",
            decision_reason="unmatched",
            actor="synthetic",
            details={},
        )
        handler = RecordingHandler()
        self.service._execute_actions = handler
        self.service.process_pending_events(organization_id=1)
        self.assertEqual(handler.calls, [])
        self.assertEqual(self._execution_rows(rule_id), [])
        self.assertGreaterEqual(int(self._rule(rule_id)["last_processed_event_log_id"]), event_id)

    def test_config_enable_is_atomic_and_active_lease_fails_without_partial_write(self) -> None:
        rule_id = self._create("atomic-enable", active=False)
        before = dict(self._rule(rule_id))
        self.assertTrue(
            self.repository.acquire_rule_claim(
                automation_rule_id=rule_id,
                organization_id=1,
                claim_token="old-owner",
                claimed_at=NOW_ISO,
                lease_until=LEASE_UNTIL,
            )
        )
        with self.assertRaises(AutomationRuleBusyError):
            self._enable(rule_id, rule_name="Must not persist", conditions_json={"status_after": "w_toku"})
        after_busy = self._rule(rule_id)
        for key in ("rule_name", "conditions_json", "is_active", "last_processed_event_log_id"):
            self.assertEqual(after_busy[key], before[key])
        self.assertEqual(after_busy["processing_claim_token"], "old-owner")

        self.assertTrue(
            self.repository.release_rule_claim(
                automation_rule_id=rule_id,
                organization_id=1,
                claim_token="old-owner",
            )
        )
        self._events(2, label="before-successful-enable")
        self._enable(rule_id, rule_name="Persisted", conditions_json={"status_after": "w_toku"})
        activated = self._rule(rule_id)
        self.assertEqual(activated["rule_name"], "Persisted")
        self.assertEqual(json.loads(str(activated["conditions_json"])), {"status_after": "w_toku"})
        self.assertEqual(int(activated["is_active"]), 1)

    def test_expired_lease_does_not_block_fresh_enable(self) -> None:
        rule_id = self._create("expired", active=False)
        self.assertTrue(
            self.repository.acquire_rule_claim(
                automation_rule_id=rule_id,
                organization_id=1,
                claim_token="expired-owner",
                claimed_at="2026-10-25T09:58:00+00:00",
                lease_until=EXPIRED_LEASE,
            )
        )
        expected_watermark = self._event(label="before-expired-enable")
        self._enable(rule_id)
        rule = self._rule(rule_id)
        self.assertEqual(int(rule["last_processed_event_log_id"]), expected_watermark)

    def test_disable_in_flight_finishes_current_event_and_stops_before_next_claim(self) -> None:
        rule_id = self._create("disable-flight", active=True)
        event_ids = self._events(2, label="in-flight")
        entered = threading.Event()
        release = threading.Event()
        handler = RecordingHandler(entered=entered, release=release)
        self.service._execute_actions = handler
        result: dict[str, object] = {}
        worker = threading.Thread(
            target=lambda: result.update(self.service.process_pending_events(organization_id=1))
        )
        worker.start()
        self.assertTrue(entered.wait(timeout=10))
        self._disable(rule_id)
        release.set()
        worker.join(timeout=10)
        self.assertFalse(worker.is_alive())
        self.assertEqual(handler.calls, [event_ids[0]])
        self.assertEqual([int(row["event_log_id"]) for row in self._execution_rows(rule_id)], [event_ids[0]])
        rule = self._rule(rule_id)
        self.assertEqual(int(rule["is_active"]), 0)
        self.assertGreaterEqual(int(rule["last_processed_event_log_id"]), event_ids[0])

    def test_reenable_is_busy_while_old_owner_holds_lease_then_succeeds_after_release(self) -> None:
        rule_id = self._create("busy-reenable", active=True)
        self._event(label="blocked")
        entered = threading.Event()
        release = threading.Event()
        handler = RecordingHandler(entered=entered, release=release)
        self.service._execute_actions = handler
        worker = threading.Thread(target=lambda: self.service.process_pending_events(organization_id=1))
        worker.start()
        self.assertTrue(entered.wait(timeout=10))
        self._disable(rule_id)
        with self.assertRaises(AutomationRuleBusyError):
            self._enable(rule_id)
        self.assertEqual(int(self._rule(rule_id)["is_active"]), 0)
        release.set()
        worker.join(timeout=10)
        self.assertFalse(worker.is_alive())
        self._enable(rule_id)
        self.assertEqual(int(self._rule(rule_id)["is_active"]), 1)

    def test_failed_consumes_event_duplicate_is_not_retried_and_next_event_runs(self) -> None:
        rule_id = self._create("failed", active=True)
        first = self._event(label="fails")
        second = self._event(label="succeeds")
        handler = RecordingHandler(fail_event_ids={first})
        self.service._execute_actions = handler
        result = self.service.process_pending_events(organization_id=1)
        self.assertEqual(result["errors"], 1)
        self.assertEqual(handler.calls, [first, second])
        self.assertEqual(
            [(int(row["event_log_id"]), row["execution_status"]) for row in self._execution_rows(rule_id)],
            [(first, "failed"), (second, "success")],
        )
        self.service.process_pending_events(organization_id=1)
        self.assertEqual(handler.calls, [first, second])
        self.assertGreaterEqual(int(self._rule(rule_id)["last_processed_event_log_id"]), second)

    def test_stuck_processing_is_not_retried_and_rule_continues(self) -> None:
        rule_id = self._create("stuck", active=True)
        stuck = self._event(label="stuck")
        following = self._event(label="following")
        claim = self.repository.try_claim_execution(
            {
                "automation_rule_id": rule_id,
                "organization_id": 1,
                "event_log_id": stuck,
                "trigger_event_type": "work_item_created",
                "input_json": "{}",
                "executed_at": NOW_ISO,
            }
        )
        self.assertTrue(claim["claimed"])
        handler = RecordingHandler()
        self.service._execute_actions = handler
        self.service.process_pending_events(organization_id=1)
        self.assertEqual(handler.calls, [following])
        self.assertEqual(
            [(int(row["event_log_id"]), row["execution_status"]) for row in self._execution_rows(rule_id)],
            [(stuck, "processing"), (following, "success")],
        )

    def test_sqlite_activation_boundary_serializes_concurrent_event_insert(self) -> None:
        self._event(label="before-boundary")
        rule_id = self._create("sqlite-race", active=False)
        selected = threading.Event()
        release = threading.Event()
        original = self.repository._organization_event_watermark
        selected_watermarks: list[int] = []

        def blocking_watermark(connection, *, organization_id):
            watermark = original(connection, organization_id=organization_id)
            selected_watermarks.append(watermark)
            selected.set()
            release.wait(timeout=10)
            return watermark

        activation_error: list[BaseException] = []
        insert_result: list[int] = []

        def activate() -> None:
            try:
                self._enable(rule_id)
            except BaseException as error:
                activation_error.append(error)

        def insert() -> None:
            insert_result.append(self._event(label="after-boundary"))

        with patch.object(self.repository, "_organization_event_watermark", side_effect=blocking_watermark):
            activation = threading.Thread(target=activate)
            activation.start()
            self.assertTrue(selected.wait(timeout=10))
            writer = threading.Thread(target=insert)
            writer.start()
            self.assertTrue(writer.is_alive())
            release.set()
            activation.join(timeout=10)
            writer.join(timeout=10)

        self.assertFalse(activation_error)
        self.assertEqual(int(self._rule(rule_id)["last_processed_event_log_id"]), selected_watermarks[0])
        self.assertGreater(insert_result[0], selected_watermarks[0])
        handler = RecordingHandler()
        self.service._execute_actions = handler
        self.service.process_pending_events(organization_id=1)
        self.assertEqual(handler.calls, insert_result)

    def test_postgresql_serializable_contract_and_bounded_retry(self) -> None:
        class FakeConnection:
            backend = "postgresql"

            def __init__(self) -> None:
                self.commits = 0
                self.statements: list[str] = []

            def commit(self) -> None:
                self.commits += 1

            def execute(self, statement, params=None):
                self.statements.append(" ".join(str(statement).split()))

        fake = FakeConnection()
        self.repository._begin_activation_transaction(fake)
        self.assertEqual(fake.commits, 1)
        self.assertEqual(fake.statements, ["SET TRANSACTION ISOLATION LEVEL SERIALIZABLE"])

        class SerializationFailure(RuntimeError):
            sqlstate = "40001"

        attempts = 0

        @contextmanager
        def fake_connection():
            class SQLiteTransaction:
                backend = "sqlite"

                def execute(self, statement, params=None):
                    return None

            yield SQLiteTransaction()

        def eventually_succeeds(connection):
            nonlocal attempts
            attempts += 1
            if attempts < AUTOMATION_ACTIVATION_SERIALIZATION_ATTEMPTS:
                raise SerializationFailure("synthetic serialization conflict")
            return "ok"

        with patch("app.repositories.automation_repository.get_connection", side_effect=fake_connection):
            self.assertEqual(self.repository._run_activation_transaction(eventually_succeeds), "ok")
        self.assertEqual(attempts, AUTOMATION_ACTIVATION_SERIALIZATION_ATTEMPTS)

        arbitrary_attempts = 0

        def arbitrary_failure(connection):
            nonlocal arbitrary_attempts
            arbitrary_attempts += 1
            raise RuntimeError("arbitrary database error")

        with patch("app.repositories.automation_repository.get_connection", side_effect=fake_connection):
            with self.assertRaisesRegex(RuntimeError, "arbitrary database error"):
                self.repository._run_activation_transaction(arbitrary_failure)
        self.assertEqual(arbitrary_attempts, 1)


if __name__ == "__main__":
    unittest.main()
