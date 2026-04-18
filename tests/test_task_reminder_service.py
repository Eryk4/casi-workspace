from __future__ import annotations

import unittest

from app.bootstrap import build_services
from app.db import reset_database


class TaskReminderServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.services = build_services()
        self.services["auth_service"].ensure_default_admin()
        self.admin = self.services["auth_service"].list_users()[0]
        self.organization = self.services["organization_service"].create_organization(
            {"name": "Organizacja Przypomnien", "slug": "organizacja-przypomnien", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        self.owner = self.services["auth_service"].create_user(
            {
                "login": "ola_przypomnienia",
                "display_name": "Ola",
                "password": "1234",
                "role": "coordinator",
                "is_active": 1,
                "organization_id": self.organization["organization_id"],
                "telegram_user_id": "700001",
            },
            actor_login="admin",
            actor_user_id=self.admin["user_id"],
            actor_user=self.admin,
        )
        self.assignee = self.services["auth_service"].create_user(
            {
                "login": "marek_przypomnienia",
                "display_name": "Marek",
                "password": "1234",
                "role": "coordinator",
                "is_active": 1,
                "organization_id": self.organization["organization_id"],
                "telegram_user_id": "700002",
            },
            actor_login="admin",
            actor_user_id=self.admin["user_id"],
            actor_user=self.admin,
        )
        self.no_telegram_user = self.services["auth_service"].create_user(
            {
                "login": "bez_telegrama",
                "display_name": "Bez Telegrama",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": self.organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=self.admin["user_id"],
            actor_user=self.admin,
        )
        self.reminder_service = self.services["task_reminder_service"]
        self.reminder_service.telegram_adapter.bot_token = "test-token"

    def test_dispatch_due_reminder_sends_only_once(self) -> None:
        sent_messages: list[tuple[str, str]] = []

        def fake_send(chat_id: str, text: str) -> dict[str, object]:
            sent_messages.append((chat_id, text))
            return {"ok": True}

        self.reminder_service.telegram_adapter.send_text_message = fake_send  # type: ignore[method-assign]

        created = self.services["task_service"].create_task(
            {
                "title": "Przypomniec o spotkaniu",
                "task_type": "wydarzenie",
                "status": "nowe",
                "priority": "wysoki",
                "due_at": "2099-04-10T10:00",
                "remind_at": "2000-04-10T09:00",
                "visibility_scope": "wybrane_osoby",
                "visible_user_ids": [self.assignee["user_id"]],
                "assigned_user_id": self.assignee["user_id"],
            },
            actor_user=self.owner,
            actor="Ola",
            organization_id=self.organization["organization_id"],
        )

        first_dispatch = self.reminder_service.dispatch_due_reminders()
        second_dispatch = self.reminder_service.dispatch_due_reminders()
        detail = self.services["task_service"].get_task_detail(
            created["task_id"],
            organization_id=self.organization["organization_id"],
            viewer_user=self.owner,
        )

        self.assertEqual(first_dispatch["sent"], 1)
        self.assertEqual(first_dispatch["failed"], 0)
        self.assertEqual(second_dispatch["sent"], 0)
        self.assertEqual(len(sent_messages), 1)
        self.assertEqual(sent_messages[0][0], "700002")
        self.assertIn("Przypomnienie: Wydarzenie", sent_messages[0][1])
        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertEqual(detail["task"]["reminder_delivery_state"], "wyslane")
        self.assertTrue(detail["task"]["reminder_sent_at"])

    def test_dispatch_failed_reminder_waits_before_retry(self) -> None:
        self.services["auth_service"].update_user(
            self.owner["user_id"],
            {"telegram_reminders_enabled": 0},
            actor_login="admin",
            actor_user=self.admin,
        )
        created = self.services["task_service"].create_task(
            {
                "title": "Zadzwonic do klienta",
                "task_type": "przypomnienie",
                "status": "nowe",
                "priority": "normalny",
                "due_at": "2099-04-10T08:00",
                "remind_at": "2000-04-10T07:30",
                "visibility_scope": "wybrane_osoby",
                "visible_user_ids": [self.no_telegram_user["user_id"]],
                "assigned_user_id": self.no_telegram_user["user_id"],
            },
            actor_user=self.owner,
            actor="Ola",
            organization_id=self.organization["organization_id"],
        )

        first_dispatch = self.reminder_service.dispatch_due_reminders()
        second_dispatch = self.reminder_service.dispatch_due_reminders()
        detail = self.services["task_service"].get_task_detail(
            created["task_id"],
            organization_id=self.organization["organization_id"],
            viewer_user=self.owner,
        )

        self.assertEqual(first_dispatch["failed"], 1)
        self.assertEqual(second_dispatch["processed"], 0)
        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertEqual(detail["task"]["reminder_delivery_state"], "blad")
        self.assertIn("Brak odbiorcy przypomnienia Telegram", detail["task"]["reminder_last_error"])
        self.assertTrue(detail["task"]["reminder_last_attempt_at"])

    def test_dispatch_falls_back_to_owner_when_assignee_disabled_reminders(self) -> None:
        sent_messages: list[tuple[str, str]] = []

        def fake_send(chat_id: str, text: str) -> dict[str, object]:
            sent_messages.append((chat_id, text))
            return {"ok": True}

        self.reminder_service.telegram_adapter.send_text_message = fake_send  # type: ignore[method-assign]
        self.services["auth_service"].update_user(
            self.assignee["user_id"],
            {"telegram_reminders_enabled": 0},
            actor_login="admin",
            actor_user=self.admin,
        )

        created = self.services["task_service"].create_task(
            {
                "title": "Sprawdzic raport",
                "task_type": "zadanie",
                "status": "nowe",
                "priority": "normalny",
                "due_at": "2099-04-10T11:00",
                "remind_at": "2000-04-10T09:00",
                "visibility_scope": "wybrane_osoby",
                "visible_user_ids": [self.assignee["user_id"]],
                "assigned_user_id": self.assignee["user_id"],
            },
            actor_user=self.owner,
            actor="Ola",
            organization_id=self.organization["organization_id"],
        )

        dispatch = self.reminder_service.dispatch_due_reminders()
        detail = self.services["task_service"].get_task_detail(
            created["task_id"],
            organization_id=self.organization["organization_id"],
            viewer_user=self.owner,
        )

        self.assertEqual(dispatch["sent"], 1)
        self.assertEqual(sent_messages[0][0], "700001")
        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertEqual(detail["task"]["reminder_delivery_state"], "wyslane")

    def test_manual_send_reminder_marks_task_as_sent(self) -> None:
        sent_messages: list[tuple[str, str]] = []

        def fake_send(chat_id: str, text: str) -> dict[str, object]:
            sent_messages.append((chat_id, text))
            return {"ok": True}

        self.reminder_service.telegram_adapter.send_text_message = fake_send  # type: ignore[method-assign]

        created = self.services["task_service"].create_task(
            {
                "title": "Wyslac podsumowanie",
                "task_type": "wydarzenie",
                "status": "nowe",
                "priority": "wysoki",
                "due_at": "2099-04-10T13:00",
                "remind_at": "2099-04-10T10:00",
                "visibility_scope": "wybrane_osoby",
                "visible_user_ids": [self.assignee["user_id"]],
                "assigned_user_id": self.assignee["user_id"],
            },
            actor_user=self.owner,
            actor="Ola",
            organization_id=self.organization["organization_id"],
        )

        reminder_task = self.reminder_service.send_reminder_now(
            created["task_id"],
            organization_id=self.organization["organization_id"],
            viewer_user_id=self.owner["user_id"],
            actor="Ola",
        )
        detail = self.services["task_service"].get_task_detail(
            created["task_id"],
            organization_id=self.organization["organization_id"],
            viewer_user=self.owner,
        )

        self.assertIsNotNone(reminder_task)
        self.assertEqual(len(sent_messages), 1)
        self.assertEqual(sent_messages[0][0], "700002")
        self.assertIn("Reczne przypomnienie", sent_messages[0][1])
        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertEqual(detail["task"]["reminder_delivery_state"], "wyslane")
        self.assertTrue(detail["task"]["reminder_sent_at"])

    def test_enqueue_then_process_outbox_delivery(self) -> None:
        sent_messages: list[tuple[str, str]] = []

        def fake_send(chat_id: str, text: str) -> dict[str, object]:
            sent_messages.append((chat_id, text))
            return {"ok": True}

        self.reminder_service.telegram_adapter.send_text_message = fake_send  # type: ignore[method-assign]

        created = self.services["task_service"].create_task(
            {
                "title": "Obslugic kolejke",
                "task_type": "zadanie",
                "status": "nowe",
                "priority": "normalny",
                "due_at": "2099-04-10T13:00",
                "remind_at": "2000-04-10T10:00",
                "visibility_scope": "wybrane_osoby",
                "visible_user_ids": [self.assignee["user_id"]],
                "assigned_user_id": self.assignee["user_id"],
            },
            actor_user=self.owner,
            actor="Ola",
            organization_id=self.organization["organization_id"],
        )

        enqueue_result = self.reminder_service.enqueue_due_reminders()
        status_after_enqueue = self.reminder_service.integration_status()
        process_result = self.reminder_service.process_due_reminders()
        detail = self.services["task_service"].get_task_detail(
            created["task_id"],
            organization_id=self.organization["organization_id"],
            viewer_user=self.owner,
        )

        self.assertEqual(enqueue_result["queued"], 1)
        self.assertGreaterEqual(int(status_after_enqueue["queue"]["due"]), 1)
        self.assertEqual(process_result["processed"], 1)
        self.assertEqual(process_result["sent"], 1)
        self.assertEqual(len(sent_messages), 1)
        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertEqual(detail["task"]["reminder_delivery_state"], "wyslane")
        self.assertTrue(detail["task"]["reminder_sent_at"])

    def test_retry_outbox_delivery_requeues_failed_item(self) -> None:
        self.services["auth_service"].update_user(
            self.owner["user_id"],
            {"telegram_reminders_enabled": 0},
            actor_login="admin",
            actor_user=self.admin,
        )
        created = self.services["task_service"].create_task(
            {
                "title": "Ponowic wpis outboxa",
                "task_type": "przypomnienie",
                "status": "nowe",
                "priority": "normalny",
                "due_at": "2099-04-10T08:00",
                "remind_at": "2000-04-10T07:30",
                "visibility_scope": "wybrane_osoby",
                "visible_user_ids": [self.no_telegram_user["user_id"]],
                "assigned_user_id": self.no_telegram_user["user_id"],
            },
            actor_user=self.owner,
            actor="Ola",
            organization_id=self.organization["organization_id"],
        )

        dispatch = self.reminder_service.dispatch_due_reminders()
        failed_deliveries = self.reminder_service.list_outbox_deliveries(
            limit=5,
            organization_id=self.organization["organization_id"],
            viewer_user_id=self.owner["user_id"],
            status="failed",
        )
        self.assertGreaterEqual(dispatch["failed"], 1)
        self.assertTrue(failed_deliveries)

        requeued = self.reminder_service.retry_outbox_delivery(
            int(failed_deliveries[0]["task_reminder_outbox_id"]),
            organization_id=self.organization["organization_id"],
            viewer_user_id=self.owner["user_id"],
            actor="Ola",
        )
        queue = self.reminder_service.integration_status(organization_id=self.organization["organization_id"])["queue"]

        self.assertIsNotNone(requeued)
        assert requeued is not None
        self.assertEqual(requeued["status"], "queued")
        self.assertGreaterEqual(int(queue["due"]), 1)

    def test_integration_status_reports_telegram_channel(self) -> None:
        self.reminder_service.record_worker_heartbeat(
            worker_name="worker-1",
            worker_role="scheduler",
            state="ok",
            process_id=1234,
            summary={
                "processed": 4,
                "sent": 2,
                "failed": 1,
                "deferred": 1,
                "retrying": 0,
                "skipped": 0,
                "queue": {"total": 3, "due": 1, "failed": 1},
            },
        )
        status = self.reminder_service.integration_status()

        self.assertTrue(status["enabled"])
        self.assertEqual(status["mode"], "aktywny")
        self.assertEqual(status["delivery_channel"], "telegram")
        self.assertGreaterEqual(int(status["retry_minutes"]), 1)
        self.assertIn("queue", status)
        self.assertIn("processing_timeout_minutes", status)
        self.assertIn("max_attempts", status)
        self.assertTrue(any(worker["worker_name"] == "worker-1" for worker in status["workers"]))

    def test_non_telegram_organization_disables_telegram_dispatch(self) -> None:
        slack_org = self.services["organization_service"].create_organization(
            {
                "name": "Slack Reminder Org",
                "slug": "slack-reminder-org",
                "communication_provider": "slack",
                "communication_config": {
                    "slack": {
                        "workspace_name": "Casi Ops",
                        "channel_id": "C0111111111",
                        "channel_name": "#powiadomienia",
                    }
                },
                "is_active": 1,
            },
            actor_user=self.admin,
            actor_login="admin",
        )
        slack_owner = self.services["auth_service"].create_user(
            {
                "login": "slack_owner",
                "display_name": "Slack Owner",
                "password": "1234",
                "role": "coordinator",
                "is_active": 1,
                "organization_id": slack_org["organization_id"],
                "telegram_user_id": "712345",
            },
            actor_login="admin",
            actor_user_id=self.admin["user_id"],
            actor_user=self.admin,
        )
        slack_assignee = self.services["auth_service"].create_user(
            {
                "login": "slack_assignee",
                "display_name": "Slack Assignee",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": slack_org["organization_id"],
                "telegram_user_id": "712346",
            },
            actor_login="admin",
            actor_user_id=self.admin["user_id"],
            actor_user=self.admin,
        )
        created = self.services["task_service"].create_task(
            {
                "title": "Slack reminder",
                "task_type": "zadanie",
                "status": "nowe",
                "priority": "normalny",
                "due_at": "2099-04-10T13:00",
                "remind_at": "2000-04-10T10:00",
                "visibility_scope": "wybrane_osoby",
                "visible_user_ids": [slack_assignee["user_id"]],
                "assigned_user_id": slack_assignee["user_id"],
            },
            actor_user=slack_owner,
            actor="Slack Owner",
            organization_id=slack_org["organization_id"],
        )

        status = self.reminder_service.integration_status(organization_id=slack_org["organization_id"])
        dispatch = self.reminder_service.dispatch_due_reminders(organization_id=slack_org["organization_id"])

        self.assertFalse(status["enabled"])
        self.assertIsNone(status["delivery_channel"])
        self.assertEqual(dispatch["processed"], 0)
        self.assertEqual(dispatch["queued"], 0)
        with self.assertRaises(ValueError):
            self.reminder_service.send_reminder_now(
                created["task_id"],
                organization_id=slack_org["organization_id"],
                viewer_user_id=slack_owner["user_id"],
                actor="Slack Owner",
            )


if __name__ == "__main__":
    unittest.main()
