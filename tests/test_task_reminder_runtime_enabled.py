from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


os.environ.setdefault("INVOICE_LOAD_LOCAL_ENV", "0")

from app.services.task_reminder_service import TaskReminderService
from app.workers.task_reminder_worker import TaskReminderDeliveryLoop, TaskReminderSchedulerLoop


ROOT = Path(__file__).resolve().parents[1]


def build_reminder_service(*, runtime_enabled: bool, telegram_configured: bool = True) -> TaskReminderService:
    telegram = Mock()
    telegram.can_send_messages.return_value = telegram_configured
    outbox = Mock()
    outbox.count_statuses.return_value = {
        "total": 0,
        "due": 0,
        "scheduled": 0,
        "processing": 0,
        "failed": 0,
        "sent": 0,
        "cancelled": 0,
    }
    outbox.list_worker_heartbeats.return_value = []
    return TaskReminderService(
        task_repository=Mock(),
        event_repository=Mock(),
        outbox_repository=outbox,
        organization_repository=Mock(),
        telegram_adapter=telegram,
        runtime_enabled=runtime_enabled,
    )


class TaskReminderRuntimeEnabledTests(unittest.TestCase):
    def test_runtime_flag_is_fail_closed_for_supported_values(self) -> None:
        expected = {
            None: "0",
            "": "0",
            "false": "0",
            "0": "0",
            "no": "0",
            "off": "0",
            "unexpected": "0",
            "true": "1",
            "1": "1",
            "yes": "1",
            "on": "1",
        }
        for raw_value, enabled in expected.items():
            with self.subTest(raw_value=raw_value):
                environment = {
                    key: os.environ[key]
                    for key in ("SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "TEMP", "TMP")
                    if key in os.environ
                }
                environment.update(
                    {
                        "INVOICE_LOAD_LOCAL_ENV": "0",
                        "INVOICE_DB_ENGINE": "sqlite",
                        "INVOICE_DATABASE_URL": "",
                        "DATABASE_URL": "",
                        "PYTHONPATH": str(ROOT),
                    }
                )
                if raw_value is not None:
                    environment["INVOICE_ENABLE_TELEGRAM_TASK_REMINDERS"] = raw_value
                result = subprocess.run(
                    [sys.executable, "-c", "from app.config import ENABLE_TELEGRAM_TASK_REMINDERS; print(int(ENABLE_TELEGRAM_TASK_REMINDERS))"],
                    cwd=ROOT,
                    env=environment,
                    capture_output=True,
                    text=True,
                    timeout=15,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), enabled)

    def test_enabled_requires_runtime_gate_and_telegram_configuration(self) -> None:
        disabled = build_reminder_service(runtime_enabled=False, telegram_configured=True)
        missing_telegram = build_reminder_service(runtime_enabled=True, telegram_configured=False)
        enabled = build_reminder_service(runtime_enabled=True, telegram_configured=True)

        self.assertFalse(disabled.is_enabled())
        self.assertEqual(disabled.integration_status()["status"], "disabled")
        self.assertEqual(disabled.integration_status()["disabled_reason"], "runtime_disabled")
        self.assertFalse(missing_telegram.is_enabled())
        self.assertEqual(missing_telegram.integration_status()["disabled_reason"], "telegram_not_configured")
        self.assertTrue(enabled.is_enabled())
        self.assertEqual(enabled.integration_status()["status"], "enabled")
        self.assertIsNone(enabled.integration_status()["disabled_reason"])
        self.assertEqual(enabled.integration_status()["runtime_status"], "unknown")

    def test_kill_switch_blocks_loops_enqueue_process_and_network(self) -> None:
        service = build_reminder_service(runtime_enabled=False, telegram_configured=True)

        self.assertFalse(TaskReminderSchedulerLoop(service, 15).start())
        self.assertFalse(TaskReminderDeliveryLoop(service, 5).start())
        self.assertEqual(
            service.enqueue_due_reminders(),
            {"evaluated": 0, "queued": 0, "deferred": 0, "failed": 0, "skipped": 0},
        )
        self.assertEqual(
            service.process_due_reminders(),
            {"processed": 0, "sent": 0, "failed": 0, "deferred": 0, "skipped": 0, "retrying": 0},
        )
        service.task_repository.list_due_reminders_for_dispatch.assert_not_called()
        service.outbox_repository.claim_due_deliveries.assert_not_called()
        service.outbox_repository.upsert_worker_heartbeat.assert_not_called()
        service.telegram_adapter.send_text_message.assert_not_called()

    def test_standalone_does_not_construct_reminder_loops_when_disabled(self) -> None:
        import run

        class FakeServer:
            def serve_forever(self) -> None:
                return None

            def server_close(self) -> None:
                return None

        reminder_service = build_reminder_service(runtime_enabled=False, telegram_configured=True)
        invoice_service = Mock()
        invoice_service.email_scheduler_status.return_value = {"enabled": False, "configured": False}
        services = {
            "auth_service": Mock(),
            "invoice_service": invoice_service,
            "task_reminder_service": reminder_service,
            "knowledge_service": Mock(),
        }
        with patch.object(sys, "argv", ["run.py", "--mode", "standalone"]), patch.object(
            run, "DATABASE_BOOTSTRAP_MODE", "off"
        ), patch.object(run, "ENABLE_DEMO_SEED", False), patch.object(
            run, "build_services", return_value=services
        ), patch.object(run, "create_server", return_value=FakeServer()), patch.object(
            run, "_print_environment_info"
        ), patch.object(run, "EmailImportSchedulerLoop") as email_loop, patch.object(
            run, "KnowledgePipelineLoop"
        ) as knowledge_loop, patch.object(run, "TaskReminderSchedulerLoop") as scheduler_loop, patch.object(
            run, "TaskReminderDeliveryLoop"
        ) as delivery_loop:
            email_loop.return_value.start.return_value = False
            knowledge_loop.return_value.start.return_value = False
            run.main()

        scheduler_loop.assert_not_called()
        delivery_loop.assert_not_called()
        reminder_service.outbox_repository.upsert_worker_heartbeat.assert_not_called()
        reminder_service.telegram_adapter.send_text_message.assert_not_called()

    def test_worker_mode_keeps_independent_loops_when_reminders_are_disabled(self) -> None:
        import run

        reminder_service = build_reminder_service(runtime_enabled=False, telegram_configured=True)
        invoice_service = Mock()
        invoice_service.email_scheduler_status.return_value = {"enabled": False, "configured": False}
        services = {
            "auth_service": Mock(),
            "invoice_service": invoice_service,
            "task_reminder_service": reminder_service,
            "knowledge_service": Mock(),
        }
        with patch.object(sys, "argv", ["run.py", "--mode", "worker"]), patch.object(
            run, "DATABASE_BOOTSTRAP_MODE", "off"
        ), patch.object(run, "ENABLE_DEMO_SEED", False), patch.object(
            run, "build_services", return_value=services
        ), patch.object(run, "_print_environment_info"), patch.object(
            run, "EmailImportSchedulerLoop"
        ) as email_loop, patch.object(run, "KnowledgePipelineLoop") as knowledge_loop, patch.object(
            run, "TaskReminderSchedulerLoop"
        ) as scheduler_loop, patch.object(run, "TaskReminderDeliveryLoop") as delivery_loop, patch.object(
            run.time, "sleep", side_effect=KeyboardInterrupt
        ):
            email_loop.return_value.start.return_value = False
            knowledge_loop.return_value.start.return_value = False
            run.main()

        scheduler_loop.assert_not_called()
        delivery_loop.assert_not_called()
        email_loop.assert_called_once()
        knowledge_loop.assert_called_once()
        email_loop.return_value.stop.assert_called_once()
        knowledge_loop.return_value.stop.assert_called_once()


if __name__ == "__main__":
    unittest.main()
