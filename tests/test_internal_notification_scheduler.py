from __future__ import annotations

import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from app.bootstrap import build_services
from app.db import get_connection, reset_database
from app.domain.internal_notification_schedule import occurrence_for_due_schedule, utc_iso


UTC = timezone.utc


class InternalNotificationSchedulerTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.services = build_services()
        self.admin = self.services["auth_service"].ensure_default_admin()
        assert self.admin is not None
        self.organization = self.services["organization_service"].create_organization(
            {"name": "Scheduler Org", "slug": "scheduler-org", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        self.organization_id = int(self.organization["organization_id"])
        self.scheduler = self.services["internal_notification_scheduler_service"]
        self.repository = self.services["internal_notification_schedule_repository"]
        self.notification_service = self.services["internal_notification_service"]
        self.billing = self.services["billing_service"]
        self.save_now = datetime(2026, 1, 15, 6, 0, tzinfo=UTC)
        self.run_now = datetime(2026, 1, 15, 7, 5, tzinfo=UTC)

    def _save(self, enabled: bool = True):
        return self.scheduler.save_settings(
            organization_id=self.organization_id,
            recipient_user_id=int(self.admin["user_id"]),
            actor_user=self.admin,
            actor="admin",
            enabled=enabled,
            local_time="08:00",
            timezone_name="Europe/Warsaw",
            now_utc=self.save_now,
        )

    def _add_due_step(self, title: str = "Scheduler due") -> None:
        self.billing.add_next_step_event(
            {
                "target_type": "work_queue_issue",
                "related_issue_key": f"scheduler::{title}",
                "step_type": "call",
                "event_action": "planned",
                "title": title,
                "planned_for": "2026-01-15",
            },
            actor_user=self.admin,
            actor="admin",
            organization_id=self.organization_id,
        )

    @staticmethod
    def _counts() -> dict[str, int]:
        tables = (
            "billing_transactions", "billing_charges", "billing_payment_matches",
            "billing_payer_ledger_entries", "billing_next_step_events",
            "internal_notifications", "internal_notification_state_events",
            "internal_notification_schedules", "internal_notification_schedule_runs", "event_logs",
        )
        with get_connection() as connection:
            return {table: int(connection.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"]) for table in tables}

    def test_disabled_is_skipped_and_due_run_uses_materializer_without_billing_writes(self) -> None:
        self._save(enabled=False)
        self._add_due_step()
        disabled_before = self._counts()
        disabled = self.scheduler.run_once(now_utc=self.run_now)
        self.assertEqual(disabled["checked_schedules"], 0)
        self.assertEqual(self._counts(), disabled_before)

        self._save(enabled=True)
        before = self._counts()
        first = self.scheduler.run_once(now_utc=self.run_now)
        second = self.scheduler.run_once(now_utc=self.run_now + timedelta(minutes=1))
        self.assertEqual(first["succeeded_runs"], 1)
        self.assertEqual(first["runs"][0]["created_count"], 1)
        self.assertEqual(second["claimed_runs"], 0)
        after = self._counts()
        for table in (
            "billing_transactions", "billing_charges", "billing_payment_matches",
            "billing_payer_ledger_entries", "billing_next_step_events", "internal_notification_state_events",
        ):
            self.assertEqual(after[table], before[table])
        self.assertEqual(after["internal_notifications"] - before["internal_notifications"], 1)
        self.assertEqual(after["internal_notification_schedule_runs"] - before["internal_notification_schedule_runs"], 1)

    def test_two_workers_claim_once_and_loser_skips(self) -> None:
        self._save()
        self._add_due_step("Concurrent")
        original = self.notification_service.materialize_billing_attention
        entered = threading.Event()
        release = threading.Event()
        calls = 0
        lock = threading.Lock()

        def controlled(**kwargs):
            nonlocal calls
            with lock:
                calls += 1
            entered.set()
            release.wait(timeout=3)
            return original(**kwargs)

        with patch.object(self.notification_service, "materialize_billing_attention", side_effect=controlled):
            with ThreadPoolExecutor(max_workers=2) as executor:
                first = executor.submit(self.scheduler.run_once, now_utc=self.run_now)
                entered.wait(timeout=3)
                second = executor.submit(self.scheduler.run_once, now_utc=self.run_now)
                release.set()
                reports = [first.result(), second.result()]
        self.assertEqual(calls, 1)
        self.assertEqual(sum(report["succeeded_runs"] for report in reports), 1)
        self.assertEqual(sum(report["claimed_runs"] for report in reports), 1)
        with get_connection() as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) AS count FROM internal_notification_schedule_runs").fetchone()["count"], 1)

    def test_active_lease_blocks_and_expired_lease_is_reclaimed(self) -> None:
        settings = self._save()
        schedule = self.repository.get_schedule_by_id(settings["internal_notification_schedule_id"])
        assert schedule is not None
        occurrence = occurrence_for_due_schedule(
            local_time="08:00", timezone_name="Europe/Warsaw", now_utc=self.run_now,
        )
        run, _ = self.repository.ensure_run({
            "schedule_id": settings["internal_notification_schedule_id"],
            "organization_id": self.organization_id,
            "recipient_user_id": int(self.admin["user_id"]),
            "source_type": "billing_next_step_attention",
            "scheduled_local_date": occurrence.scheduled_local_date,
            "as_of_date": occurrence.as_of_date,
            "scheduled_for_utc": occurrence.scheduled_for_utc,
            "created_at": utc_iso(self.run_now),
        })
        run_id = int(run["internal_notification_schedule_run_id"])
        first = self.repository.claim_run(
            run_id=run_id, lease_token="lease-one", now_utc=utc_iso(self.run_now),
            lease_expires_at_utc=utc_iso(self.run_now + timedelta(minutes=10)), max_attempts=3,
        )
        blocked = self.repository.claim_run(
            run_id=run_id, lease_token="lease-two", now_utc=utc_iso(self.run_now + timedelta(minutes=5)),
            lease_expires_at_utc=utc_iso(self.run_now + timedelta(minutes=15)), max_attempts=3,
        )
        reclaimed = self.repository.claim_run(
            run_id=run_id, lease_token="lease-three", now_utc=utc_iso(self.run_now + timedelta(minutes=11)),
            lease_expires_at_utc=utc_iso(self.run_now + timedelta(minutes=21)), max_attempts=3,
        )
        self.assertIsNotNone(first)
        self.assertIsNone(blocked)
        self.assertEqual(reclaimed["attempt_count"], 2)

    def test_retry_backoff_sanitizes_error_and_stops_after_three_attempts(self) -> None:
        self._save()
        secret = "sekret-super-token"
        with patch.object(self.notification_service, "materialize_billing_attention", side_effect=RuntimeError(secret)):
            first = self.scheduler.run_once(now_utc=self.run_now)
            blocked = self.scheduler.run_once(now_utc=self.run_now + timedelta(minutes=5))
            second = self.scheduler.run_once(now_utc=self.run_now + timedelta(minutes=15))
            third = self.scheduler.run_once(now_utc=self.run_now + timedelta(minutes=30))
            exhausted = self.scheduler.run_once(now_utc=self.run_now + timedelta(minutes=45))
        self.assertTrue(first["runs"][0]["will_retry"])
        self.assertEqual(blocked["claimed_runs"], 0)
        self.assertEqual(second["runs"][0]["attempt_count"], 2)
        self.assertFalse(third["runs"][0]["will_retry"])
        self.assertEqual(exhausted["claimed_runs"], 0)
        with get_connection() as connection:
            run = dict(connection.execute("SELECT * FROM internal_notification_schedule_runs").fetchone())
        self.assertEqual(run["attempt_count"], 3)
        self.assertEqual(run["status"], "failed")
        self.assertIsNone(run["next_attempt_at_utc"])
        self.assertNotIn(secret, run["error_summary"])
        self.assertEqual(run["error_code"], "materialization_failed")

    def test_disable_after_claim_allows_inflight_run_to_finish_without_next_run(self) -> None:
        self._save()
        self._add_due_step("Disable after claim")
        original = self.notification_service.materialize_billing_attention
        entered = threading.Event()
        release = threading.Event()

        def controlled(**kwargs):
            entered.set()
            release.wait(timeout=3)
            return original(**kwargs)

        with patch.object(self.notification_service, "materialize_billing_attention", side_effect=controlled):
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self.scheduler.run_once, now_utc=self.run_now)
                self.assertTrue(entered.wait(timeout=3))
                self.scheduler.save_settings(
                    organization_id=self.organization_id,
                    recipient_user_id=int(self.admin["user_id"]),
                    actor_user=self.admin,
                    actor="admin",
                    enabled=False,
                    local_time="08:00",
                    timezone_name="Europe/Warsaw",
                    now_utc=self.run_now,
                )
                release.set()
                report = future.result()
        self.assertEqual(report["succeeded_runs"], 1)
        stored = self.repository.get_schedule(
            organization_id=self.organization_id,
            recipient_user_id=int(self.admin["user_id"]),
            source_type="billing_next_step_attention",
        )
        self.assertEqual(stored["enabled"], 0)
        self.assertIsNone(stored["next_run_at_utc"])
        self.assertEqual(self.scheduler.run_once(now_utc=self.run_now + timedelta(days=1))["claimed_runs"], 0)

    def test_failure_of_one_recipient_does_not_block_another_schedule(self) -> None:
        second_user = self.services["auth_service"].create_user(
            {
                "login": "scheduler-second",
                "display_name": "Scheduler Second",
                "password": "Scheduler123!",
                "role": "organization_admin",
                "organization_id": self.organization_id,
                "is_active": 1,
            },
            actor_login="admin",
            actor_user_id=int(self.admin["user_id"]),
            actor_user=self.admin,
        )
        self._save()
        self.scheduler.save_settings(
            organization_id=self.organization_id,
            recipient_user_id=int(second_user["user_id"]),
            actor_user=second_user,
            actor="scheduler-second",
            enabled=True,
            local_time="08:00",
            timezone_name="Europe/Warsaw",
            now_utc=self.save_now,
        )
        self._add_due_step("Two recipients")
        original = self.notification_service.materialize_billing_attention

        def selective(**kwargs):
            if int(kwargs["recipient_user_id"]) == int(self.admin["user_id"]):
                raise RuntimeError("controlled failure")
            return original(**kwargs)

        with patch.object(self.notification_service, "materialize_billing_attention", side_effect=selective):
            report = self.scheduler.run_once(now_utc=self.run_now)
        self.assertEqual(report["checked_schedules"], 2)
        self.assertEqual(report["failed_runs"], 1)
        self.assertEqual(report["succeeded_runs"], 1)
        with get_connection() as connection:
            recipients = [int(row["recipient_user_id"]) for row in connection.execute("SELECT recipient_user_id FROM internal_notifications").fetchall()]
        self.assertEqual(recipients, [int(second_user["user_id"])])


if __name__ == "__main__":
    unittest.main()
