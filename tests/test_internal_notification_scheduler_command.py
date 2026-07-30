from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.bootstrap import build_services
from app.db import initialize_database
from app.utils import now_iso


ROOT = Path(__file__).resolve().parents[1]
MODULE = "app.jobs.internal_notifications_scheduler"
RUNTIME_FLAG = "INTERNAL_NOTIFICATION_SCHEDULER_RUNTIME_ENABLED"


class InternalNotificationSchedulerCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.database = self.root / "runtime.sqlite3"
        self.storage = self.root / "magazyn"
        self.base_env = {
            **os.environ,
            "INVOICE_DB_ENGINE": "sqlite",
            "INVOICE_SQLITE_PATH": str(self.database),
            "INVOICE_STORAGE_ROOT": str(self.storage),
            "INVOICE_ENABLE_DEMO_SEED": "0",
            "PYTHONPATH": str(ROOT),
        }
        with patch("app.db.SQLITE_DB_PATH", self.database), patch("app.db.DB_ENGINE", "sqlite"):
            initialize_database()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _run(self, mode: str, *, enabled: str | None = "true") -> tuple[subprocess.CompletedProcess[str], dict]:
        environment = dict(self.base_env)
        if enabled is None:
            environment.pop(RUNTIME_FLAG, None)
        else:
            environment[RUNTIME_FLAG] = enabled
        result = subprocess.run(
            [sys.executable, "-m", MODULE, mode],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        raw = result.stdout.strip() or result.stderr.strip()
        return result, json.loads(raw)

    def _counts(self) -> dict[str, int]:
        connection = sqlite3.connect(self.database)
        try:
            return {
                table: int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
                for table in (
                    "internal_notification_schedule_runs",
                    "internal_notifications",
                    "event_logs",
                    "billing_next_step_events",
                    "billing_transactions",
                    "billing_charges",
                    "billing_payment_matches",
                    "billing_payer_ledger_entries",
                )
            }
        finally:
            connection.close()

    def test_disabled_processes_exit_zero_without_touching_database(self) -> None:
        before_hash = hashlib.sha256(self.database.read_bytes()).hexdigest()
        for mode in ("--check", "--once"):
            result, payload = self._run(mode, enabled=None)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(payload["status"], "disabled")
            self.assertEqual(payload["exit_code"], 0)
        self.assertEqual(hashlib.sha256(self.database.read_bytes()).hexdigest(), before_hash)

    def test_enabled_check_and_empty_once_have_sanitized_exit_contract(self) -> None:
        before = self._counts()
        check_result, check = self._run("--check")
        once_result, once = self._run("--once")
        self.assertEqual(check_result.returncode, 0, check_result.stderr)
        self.assertEqual(check["status"], "ok")
        self.assertEqual(check["database_connection"], "read_only_ok")
        self.assertEqual(check["timezone"], "Europe/Warsaw")
        self.assertEqual(once_result.returncode, 0, once_result.stderr)
        self.assertEqual(once["status"], "completed")
        self.assertEqual(once["due_schedules"], 0)
        self.assertEqual(once["exit_code"], 0)
        self.assertEqual(self._counts(), before)
        self.assertNotIn(str(self.database), check_result.stdout)
        self.assertNotIn(str(self.database), once_result.stdout)

    def test_initialization_failure_is_nonzero_and_sanitized(self) -> None:
        environment = {
            **self.base_env,
            RUNTIME_FLAG: "true",
            "INVOICE_SQLITE_PATH": str(self.root / "missing" / "database.sqlite3"),
        }
        result = subprocess.run(
            [sys.executable, "-m", MODULE, "--check"],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn('"status":"system_error"', result.stderr)
        self.assertNotIn(str(self.root), result.stderr)

    def test_due_schedule_is_materialized_once_and_kill_switch_blocks_new_claim(self) -> None:
        with patch("app.db.SQLITE_DB_PATH", self.database), patch("app.db.DB_ENGINE", "sqlite"):
            services = build_services()
            admin = services["auth_service"].ensure_default_admin()
            self.assertIsNotNone(admin)
            organization = services["organization_service"].create_organization(
                {"name": "Runtime Command Org", "slug": "runtime-command-org", "is_active": 1},
                actor_user=admin,
                actor_login="admin",
            )
            organization_id = int(organization["organization_id"])
            services["internal_notification_scheduler_service"].save_settings(
                organization_id=organization_id,
                recipient_user_id=int(admin["user_id"]),
                actor_user=admin,
                actor="runtime-test",
                enabled=True,
                local_time="08:00",
                timezone_name="Europe/Warsaw",
            )
            services["billing_service"].add_next_step_event(
                {
                    "target_type": "work_queue_issue",
                    "related_issue_key": "runtime-command-due",
                    "step_type": "call",
                    "event_action": "planned",
                    "title": "Runtime command due",
                    "planned_for": "2000-01-01",
                },
                actor_user=admin,
                actor="runtime-test",
                organization_id=organization_id,
            )
        connection = sqlite3.connect(self.database)
        connection.execute(
            "UPDATE internal_notification_schedules SET next_run_at_utc = '2000-01-01T00:00:00+00:00'"
        )
        connection.commit()
        connection.close()

        first_result, first = self._run("--once")
        second_result, second = self._run("--once")
        self.assertEqual(first_result.returncode, 0, first_result.stderr)
        self.assertEqual(first["claimed_runs"], 1)
        self.assertEqual(first["succeeded_runs"], 1)
        self.assertEqual(first["created_notifications"], 1)
        self.assertEqual(second_result.returncode, 0, second_result.stderr)
        self.assertEqual(second["claimed_runs"], 0)
        stable = self._counts()

        connection = sqlite3.connect(self.database)
        connection.execute(
            "UPDATE internal_notification_schedules SET next_run_at_utc = '2000-01-01T00:00:00+00:00'"
        )
        connection.commit()
        connection.close()
        disabled_result, disabled = self._run("--once", enabled="false")
        self.assertEqual(disabled_result.returncode, 0, disabled_result.stderr)
        self.assertEqual(disabled["status"], "disabled")
        self.assertEqual(self._counts(), stable)

    def test_failed_schedule_keeps_process_exit_zero(self) -> None:
        with patch("app.db.SQLITE_DB_PATH", self.database), patch("app.db.DB_ENGINE", "sqlite"):
            services = build_services()
            admin = services["auth_service"].ensure_default_admin()
            self.assertIsNotNone(admin)
            organization = services["organization_service"].create_organization(
                {"name": "Runtime Failed Org", "slug": "runtime-failed-org", "is_active": 1},
                actor_user=admin,
                actor_login="admin",
            )
            organization_id = int(organization["organization_id"])
            services["internal_notification_scheduler_service"].save_settings(
                organization_id=organization_id,
                recipient_user_id=int(admin["user_id"]),
                actor_user=admin,
                actor="runtime-test",
                enabled=True,
                local_time="08:00",
                timezone_name="Europe/Warsaw",
            )
            healthy = services["organization_service"].create_organization(
                {"name": "Runtime Healthy Org", "slug": "runtime-healthy-org", "is_active": 1},
                actor_user=admin,
                actor_login="admin",
            )
            healthy_id = int(healthy["organization_id"])
            services["internal_notification_scheduler_service"].save_settings(
                organization_id=healthy_id,
                recipient_user_id=int(admin["user_id"]),
                actor_user=admin,
                actor="runtime-test",
                enabled=True,
                local_time="08:00",
                timezone_name="Europe/Warsaw",
            )
            services["billing_service"].add_next_step_event(
                {
                    "target_type": "work_queue_issue",
                    "related_issue_key": "runtime-healthy-due",
                    "step_type": "call",
                    "event_action": "planned",
                    "title": "Runtime healthy due",
                    "planned_for": "2000-01-01",
                },
                actor_user=admin,
                actor="runtime-test",
                organization_id=healthy_id,
            )
        connection = sqlite3.connect(self.database)
        connection.execute(
            "UPDATE internal_notification_schedules SET next_run_at_utc = '2000-01-01T00:00:00+00:00'"
        )
        connection.execute("UPDATE organizations SET is_active = 0 WHERE organization_id = ?", (organization_id,))
        connection.commit()
        connection.close()
        result, payload = self._run("--once")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(payload["failed_runs"], 1)
        self.assertEqual(payload["succeeded_runs"], 1)
        self.assertEqual(payload["created_notifications"], 1)
        self.assertEqual(payload["exit_code"], 0)
        self.assertNotIn("Traceback", result.stdout + result.stderr)
        self.assertNotIn(str(self.database), result.stdout + result.stderr)

    def test_two_processes_create_one_logical_run_and_notification(self) -> None:
        with patch("app.db.SQLITE_DB_PATH", self.database), patch("app.db.DB_ENGINE", "sqlite"):
            services = build_services()
            admin = services["auth_service"].ensure_default_admin()
            self.assertIsNotNone(admin)
            organization = services["organization_service"].create_organization(
                {"name": "Runtime Parallel Org", "slug": "runtime-parallel-org", "is_active": 1},
                actor_user=admin,
                actor_login="admin",
            )
            organization_id = int(organization["organization_id"])
            services["internal_notification_scheduler_service"].save_settings(
                organization_id=organization_id,
                recipient_user_id=int(admin["user_id"]),
                actor_user=admin,
                actor="runtime-test",
                enabled=True,
                local_time="08:00",
                timezone_name="Europe/Warsaw",
            )
            services["billing_service"].add_next_step_event(
                {
                    "target_type": "work_queue_issue",
                    "related_issue_key": "runtime-parallel-due",
                    "step_type": "call",
                    "event_action": "planned",
                    "title": "Runtime parallel due",
                    "planned_for": "2000-01-01",
                },
                actor_user=admin,
                actor="runtime-test",
                organization_id=organization_id,
            )
        connection = sqlite3.connect(self.database)
        connection.execute(
            "UPDATE internal_notification_schedules SET next_run_at_utc = '2000-01-01T00:00:00+00:00'"
        )
        connection.commit()
        connection.close()
        environment = {**self.base_env, RUNTIME_FLAG: "true"}
        processes = [
            subprocess.Popen(
                [sys.executable, "-m", MODULE, "--once"],
                cwd=ROOT,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            for _ in range(2)
        ]
        results = [process.communicate(timeout=20) for process in processes]
        self.assertEqual([process.returncode for process in processes], [0, 0])
        reports = [json.loads(stdout.strip() or stderr.strip()) for stdout, stderr in results]
        self.assertEqual(sum(int(report["claimed_runs"]) for report in reports), 1)
        counts = self._counts()
        self.assertEqual(counts["internal_notification_schedule_runs"], 1)
        self.assertEqual(counts["internal_notifications"], 1)


if __name__ == "__main__":
    unittest.main()
