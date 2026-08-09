from __future__ import annotations

import unittest
from unittest.mock import patch

from app.bootstrap import build_services
from app.db import get_connection, reset_database
from app.services.automation_operations_service import (
    AutomationOperationsRegistry,
    scheduler_health,
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
                table: int(connection.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"])
                for table in (
                    "internal_notification_schedules", "internal_notification_schedule_runs",
                    "internal_notifications", "internal_notification_state_events", "event_logs",
                    "billing_transactions", "billing_charges", "billing_payment_matches",
                    "billing_payer_ledger_entries", "billing_next_step_events",
                )
            }
        self._dashboard()
        with get_connection() as connection:
            after = {
                table: int(connection.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"])
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


if __name__ == "__main__":
    unittest.main()
