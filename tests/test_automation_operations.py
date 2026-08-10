from __future__ import annotations

import unittest
from unittest.mock import patch

from app.bootstrap import build_services
from app.db import get_connection, reset_database
from app.services.automation_operations_service import (
    AutomationOperationsRegistry,
    scheduler_health,
    task_reminder_health,
)


class AutomationOperationsTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.services = build_services()
        self.admin = self.services["auth_service"].ensure_default_admin()
        assert self.admin is not None
        self.organization = self.services["organization_service"].create_organization(
            {"name": "Automation Org", "slug": "automation-org", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        self.organization_id = int(self.organization["organization_id"])
        self.user = self.services["auth_service"].create_user(
            {
                "login": "automation-user",
                "display_name": "Automation User",
                "password": "Automation123!",
                "role": "organization_admin",
                "organization_id": self.organization_id,
                "is_active": 1,
            },
            actor_login="admin",
            actor_user_id=int(self.admin["user_id"]),
            actor_user=self.admin,
        )
        self.user_id = int(self.user["user_id"])
        self.operations = self.services["automation_operations_service"]
        self.scheduler = self.services["internal_notification_scheduler_service"]
        self.reminders = self.services["task_reminder_service"]

    def _reminder_item(self):
        return next(item for item in self._dashboard()["items"] if item["automation_key"] == "task_reminders")

    def _insert_reminder(self, *, status: str, outcome: str | None = None, error: str | None = None) -> int:
        task = self.services["task_service"].create_task(
            {"title": "Widoczne przypomnienie", "task_type": "zadanie", "status": "nowe", "priority": "normalny",
             "due_at": "2099-01-01T10:00", "remind_at": "2000-01-01T09:00", "assigned_user_id": self.user_id,
             "visibility_scope": "organizacja"},
            actor_user=self.user, actor="automation-user", organization_id=self.organization_id,
        )
        with get_connection() as connection:
            cursor = connection.execute(
                """INSERT INTO task_reminder_outbox (
                    organization_id, task_id, delivery_channel, delivery_key, delivery_anchor_at,
                    recipient_user_id, recipient_telegram_user_id, available_at, status, retryable,
                    attempt_count, last_attempt_at, last_error, sent_at, payload, created_at, updated_at
                ) VALUES (?, ?, 'telegram', ?, '2026-01-15T07:00', ?, 'fake-user', '2026-01-15T07:00', ?, 0, 1,
                    '2026-01-15T07:01', ?, ?, '{}', '2026-01-15T07:00', '2026-01-15T07:01')""",
                (self.organization_id, int(task["task_id"]), f"test-{task['task_id']}", self.user_id, status, error,
                 "2026-01-15T07:01" if status == "sent" else None),
            )
            outbox_id = int(cursor.lastrowid)
            if outcome:
                connection.execute(
                    """INSERT INTO task_reminder_outbox_attempts (
                        task_reminder_outbox_id, organization_id, task_id, delivery_channel, attempt_no,
                        outcome, attempted_at, worker_name, error_message, details, created_at
                    ) VALUES (?, ?, ?, 'telegram', 1, ?, '2026-01-15T07:01', 'mock-worker', ?, '{}', '2026-01-15T07:01')""",
                    (outbox_id, self.organization_id, int(task["task_id"]), outcome, error),
                )
        return outbox_id

    def _dashboard(self):
        return self.operations.dashboard(
            organization_id=self.organization_id,
            recipient_user_id=self.user_id,
            actor_user=self.user,
        )

    def _save(self, enabled: bool = True) -> dict:
        return self.scheduler.save_settings(
            organization_id=self.organization_id,
            recipient_user_id=self.user_id,
            actor_user=self.user,
            actor="automation-user",
            enabled=enabled,
            local_time="08:15",
            timezone_name="Europe/Warsaw",
        )

    def _run(self, schedule_id: int, *, day: int, status: str, error_summary: str | None = None) -> None:
        timestamp = f"2026-01-{day:02d}T07:00:00+00:00"
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO internal_notification_schedule_runs (
                    schedule_id, organization_id, recipient_user_id, source_type,
                    scheduled_local_date, as_of_date, scheduled_for_utc, status,
                    attempt_count, candidates_count, created_count, existing_count,
                    error_code, error_summary, started_at, finished_at, created_at
                ) VALUES (?, ?, ?, 'billing_next_step_attention', ?, ?, ?, ?, 2, 7, 3, 4, ?, ?, ?, ?, ?)
                """,
                (
                    schedule_id, self.organization_id, self.user_id,
                    f"2026-01-{day:02d}", f"2026-01-{day:02d}", timestamp, status,
                    "materialization_failed" if status == "failed" else None,
                    error_summary, timestamp, f"2026-01-{day:02d}T07:00:01+00:00", timestamp,
                ),
            )

    def test_health_states_and_dashboard_query_does_not_load_history(self) -> None:
        item = self._dashboard()["items"][0]
        self.assertEqual((item["status"], item["health"]), ("not_configured", "disabled"))

        settings = self._save(enabled=False)
        item = self._dashboard()["items"][0]
        self.assertEqual((item["status"], item["health"]), ("disabled", "disabled"))

        self._save(enabled=True)
        item = self._dashboard()["items"][0]
        self.assertEqual((item["status"], item["health"]), ("enabled", "never_run"))

        self._run(int(settings["internal_notification_schedule_id"]), day=15, status="succeeded")
        repository = self.services["internal_notification_schedule_repository"]
        with patch.object(repository, "list_runs_read_only", side_effect=AssertionError("N+1 history query")):
            dashboard = self._dashboard()
        item = dashboard["items"][0]
        self.assertEqual(item["health"], "healthy")
        self.assertIsNotNone(item["next_run_at"])
        self.assertEqual(item["last_run_duration_ms"], 1000)
        self.assertEqual((item["last_candidates_count"], item["last_created_count"], item["last_existing_count"]), (7, 3, 4))

    def test_failed_run_is_attention_and_error_is_sanitized(self) -> None:
        settings = self._save()
        secret = "Traceback password=secret-token DSN=postgres://private"
        self._run(int(settings["internal_notification_schedule_id"]), day=15, status="failed", error_summary=secret)
        item = self._dashboard()["items"][0]
        self.assertEqual(item["health"], "attention")
        self.assertEqual(item["recent_failure_count"], 1)
        self.assertNotIn("secret", item["last_error_summary"].lower())
        detail = self.operations.detail(
            "internal_notification_scheduler",
            organization_id=self.organization_id,
            recipient_user_id=self.user_id,
            actor_user=self.user,
            history_limit=1000,
        )
        self.assertEqual(detail["history_limit"], 50)
        self.assertEqual(len(detail["history"]), 1)
        self.assertNotIn("lease_token", detail["history"][0])
        self.assertNotIn("secret", detail["history"][0]["error_summary"].lower())

    def test_scope_isolation_and_read_paths_do_not_write(self) -> None:
        other = self.services["organization_service"].create_organization(
            {"name": "Other Org", "slug": "automation-other", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        with self.assertRaises((PermissionError, ValueError)):
            self.operations.dashboard(
                organization_id=int(other["organization_id"]),
                recipient_user_id=self.user_id,
                actor_user=self.user,
            )
        with get_connection() as connection:
            before = {
                table: [dict(row) for row in connection.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()]
                for table in (
                    "task_reminder_outbox", "task_reminder_outbox_attempts", "task_reminder_worker_heartbeats", "tasks",
                    "automation_rules", "automation_executions",
                    "internal_notification_schedules", "internal_notification_schedule_runs",
                    "internal_notifications", "internal_notification_state_events", "event_logs",
                    "billing_transactions", "billing_charges", "billing_payment_matches",
                    "billing_payer_ledger_entries", "billing_next_step_events",
                )
            }
        self._dashboard()
        with get_connection() as connection:
            after = {
                table: [dict(row) for row in connection.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()]
                for table in before
            }
        self.assertEqual(after, before)

    def test_recipient_scope_never_returns_another_users_schedule(self) -> None:
        other_user = self.services["auth_service"].create_user(
            {
                "login": "automation-other-user", "display_name": "Other User", "password": "Automation123!",
                "role": "organization_admin", "organization_id": self.organization_id, "is_active": 1,
            },
            actor_login="admin", actor_user_id=int(self.admin["user_id"]), actor_user=self.admin,
        )
        self.scheduler.save_settings(
            organization_id=self.organization_id, recipient_user_id=int(other_user["user_id"]), actor_user=other_user,
            actor="automation-other-user", enabled=True, local_time="13:45", timezone_name="Europe/Warsaw",
        )
        own = self._dashboard()["items"][0]
        self.assertEqual(own["status"], "not_configured")
        self.assertNotEqual(own["schedule"]["local_time"], "13:45")

    def test_registry_contract_is_extensible_and_keys_are_unique(self) -> None:
        class Adapter:
            automation_key = "future_adapter"
            scope = "organization"
            capabilities = frozenset({"summary"})

            def get_operation(self, **kwargs):
                return {}

            def get_history(self, **kwargs):
                return []

        adapter = Adapter()
        registry = AutomationOperationsRegistry((adapter,))
        self.assertIs(registry.get("future_adapter"), adapter)
        with self.assertRaises(ValueError):
            AutomationOperationsRegistry((adapter, adapter))
        with self.assertRaises(ValueError):
            AutomationOperationsRegistry.validate_operation({"automation_key": "incomplete"})

    def test_health_mapping_is_explicit(self) -> None:
        self.assertEqual(scheduler_health(schedule_exists=False, enabled=False, last_terminal_status=None), ("not_configured", "disabled", "schedule_not_configured"))
        self.assertEqual(scheduler_health(schedule_exists=True, enabled=True, last_terminal_status="succeeded")[1], "healthy")
        self.assertEqual(scheduler_health(schedule_exists=True, enabled=True, last_terminal_status="failed")[1], "attention")
        self.assertEqual(task_reminder_health(enabled=False, failed_count=0, latest_attempt_status=None)[1], "disabled")
        self.assertEqual(task_reminder_health(enabled=True, failed_count=0, latest_attempt_status=None)[1], "never_run")
        self.assertEqual(task_reminder_health(enabled=True, failed_count=0, latest_attempt_status="sent")[1], "healthy")
        self.assertEqual(task_reminder_health(enabled=True, failed_count=1, latest_attempt_status="sent")[1], "attention")

    def test_task_reminders_health_queue_history_and_sanitization(self) -> None:
        self.assertEqual((self._reminder_item()["status"], self._reminder_item()["health"]), ("disabled", "disabled"))
        self.reminders.runtime_enabled = True
        self.reminders.telegram_adapter.bot_token = "fake-token"
        self.assertEqual(self._reminder_item()["health"], "never_run")
        self._insert_reminder(status="sent", outcome="sent")
        item = self._reminder_item()
        self.assertEqual(item["health"], "healthy")
        self.assertEqual(item["sent_count"], 1)
        self._insert_reminder(status="failed", outcome="dead_letter", error="Traceback token=secret DSN=postgres://private")
        item = self._reminder_item()
        self.assertEqual(item["health"], "attention")
        self.assertEqual(item["failed_count"], 1)
        self.assertNotIn("secret", item["last_error_summary"].lower())
        detail = self.operations.detail("task_reminders", organization_id=self.organization_id,
            recipient_user_id=self.user_id, actor_user=self.user, history_limit=100)
        self.assertEqual(detail["history_limit"], 50)
        self.assertEqual(len(detail["history"]), 2)
        self.assertEqual(len(detail["outbox"]), 2)
        self.assertNotIn("payload", str(detail).lower())
        self.assertNotIn("secret", str(detail).lower())

    def test_task_reminders_respect_private_task_visibility(self) -> None:
        other = self.services["auth_service"].create_user(
            {"login": "private-reminder-user", "display_name": "Private User", "password": "Automation123!",
             "role": "organization_admin", "organization_id": self.organization_id, "is_active": 1},
            actor_login="admin", actor_user_id=int(self.admin["user_id"]), actor_user=self.admin,
        )
        task = self.services["task_service"].create_task(
            {"title": "Prywatne przypomnienie", "task_type": "zadanie", "status": "nowe", "priority": "normalny",
             "due_at": "2099-01-01T10:00", "remind_at": "2000-01-01T09:00", "visibility_scope": "prywatne"},
            actor_user=other, actor="Private User", organization_id=self.organization_id,
        )
        with get_connection() as connection:
            connection.execute(
                """INSERT INTO task_reminder_outbox (organization_id, task_id, delivery_channel, delivery_key,
                    delivery_anchor_at, recipient_user_id, recipient_telegram_user_id, available_at, status,
                    retryable, attempt_count, payload, created_at, updated_at)
                    VALUES (?, ?, 'telegram', ?, '2026-01-15T07:00', ?, 'fake', '2026-01-15T07:00',
                    'queued', 1, 0, '{}', '2026-01-15T07:00', '2026-01-15T07:00')""",
                (self.organization_id, int(task["task_id"]), f"private-{task['task_id']}", int(other["user_id"])),
            )
        self.reminders.runtime_enabled = True
        self.reminders.telegram_adapter.bot_token = "fake-token"
        self.assertEqual(self._reminder_item()["pending_count"], 0)
        other_dashboard = self.operations.dashboard(organization_id=self.organization_id,
            recipient_user_id=int(other["user_id"]), actor_user=other)
        other_item = next(item for item in other_dashboard["items"] if item["automation_key"] == "task_reminders")
        self.assertEqual(other_item["pending_count"], 1)


if __name__ == "__main__":
    unittest.main()
