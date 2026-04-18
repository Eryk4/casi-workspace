from __future__ import annotations

import base64
import http.client
import json
import threading
import unittest
from datetime import datetime, timedelta

from app.api.http_server import create_server
from app.bootstrap import build_services
from app.db import reset_database
from app.domain.constants import MANAGER_ASSISTANT_MODULE


class TaskMvpTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.services = build_services()
        self.services["auth_service"].ensure_default_admin()
        self.admin = self.services["auth_service"].list_users()[0]
        self.organization = self.services["organization_service"].create_organization(
            {
                "name": "Klient Zadaniowy",
                "slug": "klient-zadaniowy",
                "is_active": 1,
                "enabled_modules": ["manager_assistant"],
            },
            actor_user=self.admin,
            actor_login="admin",
        )
        self.services["organization_repository"].replace_enabled_modules(
            int(self.organization["organization_id"]),
            [MANAGER_ASSISTANT_MODULE],
            enabled_by_user_id=int(self.admin["user_id"]),
        )
        self.operator = self.services["auth_service"].create_user(
            {
                "login": "olga",
                "display_name": "Olga",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": self.organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=self.admin["user_id"],
            actor_user=self.admin,
        )
        self.coordinator = self.services["auth_service"].create_user(
            {
                "login": "karol",
                "display_name": "Karol",
                "password": "1234",
                "role": "coordinator",
                "is_active": 1,
                "organization_id": self.organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=self.admin["user_id"],
            actor_user=self.admin,
        )
        self.second_operator = self.services["auth_service"].create_user(
            {
                "login": "ania",
                "display_name": "Ania",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": self.organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=self.admin["user_id"],
            actor_user=self.admin,
        )

    def _utworz_testowa_fakture(self, invoice_number: str = "FV/TEST/1") -> dict[str, object]:
        return self.services["invoice_service"].create_invoice(
            {
                "source": "MANUAL",
                "file_name": f"{invoice_number.replace('/', '_')}.pdf",
                "invoice_number": invoice_number,
                "issuer_name": "Firma Testowa",
                "issuer_nip": "1234567890",
                "gross_amount": 199.99,
                "currency": "PLN",
                "issue_date": "2099-04-10",
                "sale_date": "2099-04-10",
            },
            actor="Olga",
            organization_id=self.organization["organization_id"],
        )

    def test_task_service_can_create_update_and_add_note(self) -> None:
        created = self.services["task_service"].create_task(
            {
                "title": "Przygotowac spotkanie z klientem",
                "task_type": "zadanie",
                "status": "nowe",
                "priority": "wysoki",
                "due_at": "2099-04-10T10:30",
                "remind_at": "2099-04-10T09:45",
                "assigned_user_id": self.operator["user_id"],
                "description": "Zebrac materialy i potwierdzic zakres rozmowy.",
            },
            actor_user=self.operator,
            actor="Olga",
            organization_id=self.organization["organization_id"],
        )
        self.assertEqual(created["title"], "Przygotowac spotkanie z klientem")
        self.assertEqual(created["assigned_user_name"], "Olga")
        self.assertEqual(created["remind_at"], "2099-04-10T09:45")
        self.assertEqual(created["reminder_state"], "zaplanowane")
        self.assertEqual(created["reminder_target_label"], "Przypisana osoba nie ma ID Telegram: Olga")
        self.assertFalse(created["reminder_target_ready"])
        self.assertEqual(created["visibility_scope"], "prywatne")

        updated = self.services["task_service"].update_task(
            created["task_id"],
            {
                "status": "w_toku",
                "priority": "krytyczny",
                "due_at": "2099-04-11T09:15",
                "remind_at": "2099-04-11T08:15",
            },
            actor_user=self.operator,
            actor="Olga",
            organization_id=self.organization["organization_id"],
        )
        self.assertIsNotNone(updated)
        assert updated is not None
        self.assertEqual(updated["status"], "w_toku")
        self.assertEqual(updated["priority"], "krytyczny")
        self.assertEqual(updated["remind_at"], "2099-04-11T08:15")
        self.assertEqual(updated["visibility_scope"], "prywatne")

        detail = self.services["task_service"].add_task_note(
            created["task_id"],
            "Potwierdzono spotkanie na jutro rano.",
            actor_user=self.operator,
            actor="Olga",
            organization_id=self.organization["organization_id"],
        )
        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertEqual(detail["task"]["task_id"], created["task_id"])
        self.assertEqual(len(detail["notes"]), 1)
        self.assertEqual(detail["notes"][0]["created_by_user_name"], "Olga")
        self.assertGreaterEqual(len(detail["history"]), 3)
        self.assertTrue(any(item["action_type"] == "task_created" for item in detail["history"]))
        self.assertTrue(any(item["action_type"] == "task_note_added" for item in detail["history"]))

    def test_dashboard_snapshot_includes_due_reminders(self) -> None:
        self.services["task_service"].create_task(
            {
                "title": "Przypomniec o podpisaniu umowy",
                "task_type": "wydarzenie",
                "status": "nowe",
                "priority": "wysoki",
                "due_at": "2099-04-10T11:00",
                "remind_at": "2000-04-10T10:00",
                "assigned_user_id": self.operator["user_id"],
            },
            actor_user=self.operator,
            actor="Olga",
            organization_id=self.organization["organization_id"],
        )

        snapshot = self.services["dashboard_service"].get_snapshot(
            organization_id=self.organization["organization_id"],
            viewer_user_id=self.operator["user_id"],
        )
        self.assertEqual(snapshot["cards"]["aktywne_przypomnienia"], 1)
        self.assertTrue(snapshot["active_reminders"])
        self.assertEqual(snapshot["active_reminders"][0]["title"], "Przypomniec o podpisaniu umowy")

    def test_private_task_is_visible_only_for_owner(self) -> None:
        created = self.services["task_service"].create_task(
            {
                "title": "Prywatna lista spraw",
                "task_type": "zadanie",
                "status": "nowe",
                "priority": "normalny",
            },
            actor_user=self.operator,
            actor="Olga",
            organization_id=self.organization["organization_id"],
        )

        visible_for_owner = self.services["task_service"].list_tasks(
            organization_id=self.organization["organization_id"],
            viewer_user=self.operator,
        )
        invisible_for_other = self.services["task_service"].list_tasks(
            organization_id=self.organization["organization_id"],
            viewer_user=self.second_operator,
        )
        invisible_for_admin = self.services["task_service"].list_tasks(
            organization_id=self.organization["organization_id"],
            viewer_user=self.admin,
        )

        self.assertTrue(any(item["task_id"] == created["task_id"] for item in visible_for_owner))
        self.assertFalse(any(item["task_id"] == created["task_id"] for item in invisible_for_other))
        self.assertFalse(any(item["task_id"] == created["task_id"] for item in invisible_for_admin))

    def test_task_can_be_shared_with_selected_users(self) -> None:
        created = self.services["task_service"].create_task(
            {
                "title": "Uzgodnic plan wdrozenia",
                "task_type": "wydarzenie",
                "status": "nowe",
                "priority": "wysoki",
                "visibility_scope": "wybrane_osoby",
                "visible_user_ids": [self.second_operator["user_id"]],
            },
            actor_user=self.coordinator,
            actor="Karol",
            organization_id=self.organization["organization_id"],
        )

        detail_for_selected = self.services["task_service"].get_task_detail(
            created["task_id"],
            organization_id=self.organization["organization_id"],
            viewer_user=self.second_operator,
        )
        detail_for_admin = self.services["task_service"].get_task_detail(
            created["task_id"],
            organization_id=self.organization["organization_id"],
            viewer_user=self.admin,
        )

        self.assertIsNotNone(detail_for_selected)
        assert detail_for_selected is not None
        self.assertEqual(detail_for_selected["task"]["visibility_scope"], "wybrane_osoby")
        self.assertEqual(detail_for_selected["task"]["visible_user_ids"], [self.second_operator["user_id"]])
        self.assertIsNone(detail_for_admin)

    def test_operator_can_share_task_and_note_with_other_users(self) -> None:
        created = self.services["task_service"].create_task(
            {
                "title": "Wspolne zadanie operatora",
                "task_type": "zadanie",
                "status": "nowe",
                "priority": "normalny",
                "visibility_scope": "wybrane_osoby",
                "assigned_user_id": self.coordinator["user_id"],
                "visible_user_ids": [self.coordinator["user_id"]],
            },
            actor_user=self.operator,
            actor="Olga",
            organization_id=self.organization["organization_id"],
        )
        self.assertEqual(created["assigned_user_id"], self.coordinator["user_id"])
        self.assertEqual(created["visible_user_ids"], [self.coordinator["user_id"]])

        detail = self.services["task_service"].add_task_note(
            created["task_id"],
            "Notatka dla Karola od operatora.",
            actor_user=self.operator,
            actor="Olga",
            organization_id=self.organization["organization_id"],
        )
        self.assertEqual(detail["notes"][0]["note_text"], "Notatka dla Karola od operatora.")
        visible_for_coordinator = self.services["task_service"].get_task_detail(
            created["task_id"],
            organization_id=self.organization["organization_id"],
            viewer_user=self.coordinator,
        )
        self.assertIsNotNone(visible_for_coordinator)
        assert visible_for_coordinator is not None
        self.assertEqual(visible_for_coordinator["task"]["assigned_user_id"], self.coordinator["user_id"])
        self.assertEqual(visible_for_coordinator["notes"][0]["note_text"], "Notatka dla Karola od operatora.")

    def test_task_can_link_invoice_and_contractor(self) -> None:
        invoice = self._utworz_testowa_fakture("FV/LINK/1")

        created = self.services["task_service"].create_task(
            {
                "title": "Wyjasnic platnosc do faktury",
                "task_type": "zadanie",
                "status": "nowe",
                "priority": "wysoki",
                "linked_entities": [
                    {"entity_type": "invoice", "entity_id": invoice["id"]},
                    {"entity_type": "contractor", "entity_id": invoice["contractor_id"]},
                ],
            },
            actor_user=self.operator,
            actor="Olga",
            organization_id=self.organization["organization_id"],
        )

        self.assertEqual(created["linked_entity_count"], 2)
        self.assertEqual(created["linked_invoice_ids"], [invoice["id"]])
        self.assertEqual(created["linked_contractor_ids"], [invoice["contractor_id"]])

        detail = self.services["task_service"].get_task_detail(
            created["task_id"],
            organization_id=self.organization["organization_id"],
            viewer_user=self.operator,
        )
        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertEqual(len(detail["task"]["linked_entities"]), 2)
        self.assertTrue(any(item["entity_type"] == "invoice" for item in detail["task"]["linked_entities"]))
        self.assertTrue(any(item["entity_type"] == "contractor" for item in detail["task"]["linked_entities"]))

    def test_private_linked_task_is_visible_in_invoice_and_contractor_detail_only_for_owner(self) -> None:
        invoice = self._utworz_testowa_fakture("FV/LINK/2")
        created = self.services["task_service"].create_task(
            {
                "title": "Prywatna analiza faktury",
                "task_type": "zadanie",
                "status": "nowe",
                "priority": "normalny",
                "linked_entities": [
                    {"entity_type": "invoice", "entity_id": invoice["id"]},
                    {"entity_type": "contractor", "entity_id": invoice["contractor_id"]},
                ],
            },
            actor_user=self.operator,
            actor="Olga",
            organization_id=self.organization["organization_id"],
        )

        invoice_detail_owner = self.services["invoice_service"].get_invoice_detail(
            invoice["id"],
            organization_id=self.organization["organization_id"],
            viewer_user=self.operator,
        )
        invoice_detail_other = self.services["invoice_service"].get_invoice_detail(
            invoice["id"],
            organization_id=self.organization["organization_id"],
            viewer_user=self.second_operator,
        )
        contractor_detail_owner = self.services["invoice_service"].get_contractor_detail(
            invoice["contractor_id"],
            organization_id=self.organization["organization_id"],
            viewer_user=self.operator,
        )
        contractor_detail_other = self.services["invoice_service"].get_contractor_detail(
            invoice["contractor_id"],
            organization_id=self.organization["organization_id"],
            viewer_user=self.second_operator,
        )

        assert invoice_detail_owner is not None
        assert invoice_detail_other is not None
        assert contractor_detail_owner is not None
        assert contractor_detail_other is not None

        self.assertTrue(any(item["task_id"] == created["task_id"] for item in invoice_detail_owner["linked_tasks"]))
        self.assertFalse(any(item["task_id"] == created["task_id"] for item in invoice_detail_other["linked_tasks"]))
        self.assertTrue(any(item["task_id"] == created["task_id"] for item in contractor_detail_owner["linked_tasks"]))
        self.assertFalse(any(item["task_id"] == created["task_id"] for item in contractor_detail_other["linked_tasks"]))

    def test_recurrence_scope_updates_open_series_tasks(self) -> None:
        created = self.services["task_service"].create_task(
            {
                "title": "Cotygodniowy status",
                "task_type": "wydarzenie",
                "status": "nowe",
                "priority": "normalny",
                "due_at": "2099-04-10T10:00",
                "remind_at": "2099-04-10T09:00",
                "recurrence_pattern": "co_tydzien",
                "recurrence_interval": 1,
            },
            actor_user=self.operator,
            actor="Olga",
            organization_id=self.organization["organization_id"],
        )
        next_task_id = self.services["task_repository"].create(
            {
                "organization_id": self.organization["organization_id"],
                "task_type": "wydarzenie",
                "visibility_scope": "prywatne",
                "owner_user_id": self.operator["user_id"],
                "title": "Cotygodniowy status",
                "description": None,
                "status": "nowe",
                "priority": "normalny",
                "due_at": "2099-04-17T10:00",
                "remind_at": "2099-04-17T09:00",
                "recurrence_pattern": "co_tydzien",
                "recurrence_interval": 1,
                "recurrence_weekdays": "4",
                "recurrence_end_at": None,
                "recurrence_series_id": created["recurrence_series_id"],
                "recurrence_parent_task_id": created["task_id"],
                "assigned_user_id": None,
                "calendar_id": None,
                "calendar_duration_minutes": 60,
                "created_by_user_id": self.operator["user_id"],
                "completed_at": None,
            }
        )
        self.services["task_service"].update_task(
            created["task_id"],
            {
                "title": "Cotygodniowy status klienta",
                "priority": "wysoki",
                "recurrence_apply_scope": "cala_seria",
            },
            actor_user=self.operator,
            actor="Olga",
            organization_id=self.organization["organization_id"],
        )
        next_task = self.services["task_repository"].get_by_id(
            next_task_id,
            organization_id=self.organization["organization_id"],
            viewer_user_id=self.operator["user_id"],
        )
        self.assertIsNotNone(next_task)
        assert next_task is not None
        self.assertEqual(next_task["title"], "Cotygodniowy status klienta")
        self.assertEqual(next_task["priority"], "wysoki")

    def test_logs_hide_private_task_events_from_other_users(self) -> None:
        self.services["task_service"].create_task(
            {
                "title": "Prywatna notatka operacyjna",
                "task_type": "zadanie",
                "status": "nowe",
                "priority": "normalny",
            },
            actor_user=self.operator,
            actor="Olga",
            organization_id=self.organization["organization_id"],
        )

        owner_logs = self.services["invoice_service"].list_logs(
            organization_id=self.organization["organization_id"],
            viewer_user_id=self.operator["user_id"],
        )
        other_logs = self.services["invoice_service"].list_logs(
            organization_id=self.organization["organization_id"],
            viewer_user_id=self.second_operator["user_id"],
        )

        self.assertTrue(any(log["event_type"] == "task_created" for log in owner_logs))
        self.assertFalse(any(log["event_type"] == "task_created" for log in other_logs))

    def test_reminder_cannot_be_later_than_due_time(self) -> None:
        with self.assertRaisesRegex(ValueError, "Godzina przypomnienia nie moze byc pozniejsza niz termin zadania."):
            self.services["task_service"].create_task(
                {
                    "title": "Bledne przypomnienie",
                    "task_type": "zadanie",
                    "status": "nowe",
                    "priority": "normalny",
                    "due_at": "2099-04-10T08:00",
                    "remind_at": "2099-04-10T09:00",
                },
                actor_user=self.operator,
                actor="Olga",
                organization_id=self.organization["organization_id"],
            )

    def test_task_planner_snapshot_and_snooze_reminder(self) -> None:
        now_dt = datetime.now().replace(second=0, microsecond=0)
        overdue_due_at = (now_dt - timedelta(days=1, minutes=30)).strftime("%Y-%m-%dT%H:%M")
        overdue_remind_at = (now_dt - timedelta(days=1, hours=1)).strftime("%Y-%m-%dT%H:%M")
        overdue_task = self.services["task_service"].create_task(
            {
                "title": "Pilny kontakt jeszcze dzis",
                "task_type": "zadanie",
                "status": "nowe",
                "priority": "wysoki",
                "due_at": overdue_due_at,
                "remind_at": overdue_remind_at,
                "assigned_user_id": self.operator["user_id"],
            },
            actor_user=self.operator,
            actor="Olga",
            organization_id=self.organization["organization_id"],
        )

        planner = self.services["task_service"].get_planner_snapshot(
            organization_id=self.organization["organization_id"],
            viewer_user=self.operator,
        )
        overdue_items = [
            item
            for group in planner["buckets"]["zalegle"]["groups"]
            for item in group["items"]
        ]
        self.assertTrue(any(item["task_id"] == overdue_task["task_id"] for item in overdue_items))

        future_due_at = (now_dt + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M")
        future_remind_at = (now_dt + timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M")
        future_task = self.services["task_service"].create_task(
            {
                "title": "Przypomnienie do odlozenia",
                "task_type": "zadanie",
                "status": "nowe",
                "priority": "normalny",
                "due_at": future_due_at,
                "remind_at": future_remind_at,
                "assigned_user_id": self.operator["user_id"],
            },
            actor_user=self.operator,
            actor="Olga",
            organization_id=self.organization["organization_id"],
        )

        detail = self.services["task_service"].snooze_task_reminder(
            future_task["task_id"],
            {"mode": "10m"},
            actor_user=self.operator,
            actor="Olga",
            organization_id=self.organization["organization_id"],
        )

        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertEqual(detail["task"]["reminder_state"], "zaplanowane")
        self.assertIsNotNone(detail["task"]["remind_at"])
        snoozed_dt = datetime.strptime(detail["task"]["remind_at"], "%Y-%m-%dT%H:%M")
        self.assertGreaterEqual(snoozed_dt, now_dt + timedelta(minutes=9))
        self.assertTrue(any(item["action_type"] == "task_reminder_snoozed" for item in detail["history"]))

    def test_completed_recurring_task_creates_next_occurrence(self) -> None:
        created = self.services["task_service"].create_task(
            {
                "title": "Raport dzienny",
                "task_type": "zadanie",
                "status": "nowe",
                "priority": "normalny",
                "due_at": "2099-04-10T08:00",
                "remind_at": "2099-04-10T07:30",
                "recurrence_pattern": "codziennie",
                "recurrence_interval": 1,
                "assigned_user_id": self.operator["user_id"],
            },
            actor_user=self.operator,
            actor="Olga",
            organization_id=self.organization["organization_id"],
        )

        detail = self.services["task_service"].update_task(
            int(created["task_id"]),
            {"status": "zakonczone"},
            actor_user=self.operator,
            actor="Olga",
            organization_id=self.organization["organization_id"],
        )

        self.assertIsNotNone(detail)
        assert detail is not None
        tasks = self.services["task_service"].list_tasks(
            organization_id=self.organization["organization_id"],
            viewer_user=self.operator,
        )
        same_series = [item for item in tasks if item.get("recurrence_series_id") == created["recurrence_series_id"]]
        self.assertEqual(len(same_series), 2)
        successor = next(item for item in same_series if int(item["task_id"]) != int(created["task_id"]))
        self.assertEqual(successor["status"], "nowe")
        self.assertEqual(successor["due_at"], "2099-04-11T08:00")
        self.assertEqual(successor["remind_at"], "2099-04-11T07:30")
        self.assertEqual(successor["recurrence_parent_task_id"], created["task_id"])

    def test_focus_snapshot_groups_tasks_for_daily_work(self) -> None:
        now_dt = datetime.now().replace(second=0, microsecond=0)
        today_due = (now_dt + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M")
        overdue_due = (now_dt - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M")

        self.services["task_service"].create_task(
            {
                "title": "Moje dzisiejsze zadanie",
                "task_type": "zadanie",
                "status": "nowe",
                "priority": "normalny",
                "due_at": today_due,
                "assigned_user_id": self.operator["user_id"],
            },
            actor_user=self.operator,
            actor="Olga",
            organization_id=self.organization["organization_id"],
        )
        self.services["task_service"].create_task(
            {
                "title": "Decyzja dla zespolu",
                "task_type": "wydarzenie",
                "status": "oczekuje",
                "priority": "wysoki",
                "visibility_scope": "organizacja",
                "due_at": today_due,
            },
            actor_user=self.coordinator,
            actor="Karol",
            organization_id=self.organization["organization_id"],
        )
        self.services["task_service"].create_task(
            {
                "title": "Zalegle przypomnienie",
                "task_type": "przypomnienie",
                "status": "nowe",
                "priority": "normalny",
                "due_at": overdue_due,
                "assigned_user_id": self.operator["user_id"],
            },
            actor_user=self.operator,
            actor="Olga",
            organization_id=self.organization["organization_id"],
        )

        snapshot = self.services["task_service"].get_focus_snapshot(
            organization_id=self.organization["organization_id"],
            viewer_user=self.operator,
        )
        views = {item["code"]: item for item in snapshot["views"]}
        self.assertGreaterEqual(views["moj_dzien"]["count"], 1)
        self.assertGreaterEqual(views["przypisane_do_mnie"]["count"], 1)
        self.assertGreaterEqual(views["po_terminie"]["count"], 1)
        self.assertGreaterEqual(views["organizacyjne"]["count"], 1)
        self.assertGreaterEqual(views["prywatne"]["count"], 1)
        self.assertNotIn("do_decyzji", views)

        manager_snapshot = self.services["task_service"].get_focus_snapshot(
            organization_id=self.organization["organization_id"],
            viewer_user=self.coordinator,
        )
        manager_views = {item["code"]: item for item in manager_snapshot["views"]}
        self.assertGreaterEqual(manager_views["do_decyzji"]["count"], 1)
        self.assertNotIn("przypisane_do_mnie", manager_views)

    def test_task_detail_includes_uploaded_attachment(self) -> None:
        created = self.services["task_service"].create_task(
            {
                "title": "Plan wdrozenia z zalacznikiem",
                "task_type": "zadanie",
                "status": "nowe",
                "priority": "normalny",
                "assigned_user_id": self.operator["user_id"],
            },
            actor_user=self.operator,
            actor="Olga",
            organization_id=self.organization["organization_id"],
        )

        detail = self.services["task_service"].add_task_attachment(
            created["task_id"],
            {
                "file_name": "notatka.txt",
                "content_type": "text/plain",
                "content_base64": base64.b64encode(b"To jest testowy zalacznik.").decode("ascii"),
            },
            actor_user=self.operator,
            actor="Olga",
            organization_id=self.organization["organization_id"],
        )

        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertEqual(len(detail["attachments"]), 1)
        attachment = detail["attachments"][0]
        self.assertEqual(attachment["file_name"], "notatka.txt")
        self.assertEqual(attachment["uploaded_by_user_name"], "Olga")
        self.assertTrue(str(attachment["file_link"]).endswith(".txt"))

    def test_task_detail_includes_link_attachment(self) -> None:
        created = self.services["task_service"].create_task(
            {
                "title": "Plan wdrozenia z linkiem",
                "task_type": "zadanie",
                "status": "nowe",
                "priority": "normalny",
                "assigned_user_id": self.operator["user_id"],
            },
            actor_user=self.operator,
            actor="Olga",
            organization_id=self.organization["organization_id"],
        )

        detail = self.services["task_service"].add_task_attachment(
            created["task_id"],
            {
                "attachment_kind": "link",
                "attachment_url": "https://docs.example.com/plan-wdrozenia",
                "file_name": "plan-wdrozenia-link",
            },
            actor_user=self.operator,
            actor="Olga",
            organization_id=self.organization["organization_id"],
        )

        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertEqual(len(detail["attachments"]), 1)
        attachment = detail["attachments"][0]
        self.assertEqual(attachment["file_name"], "plan-wdrozenia-link")
        self.assertEqual(attachment["storage_backend"], "external_link")
        self.assertEqual(attachment["file_link"], "https://docs.example.com/plan-wdrozenia")
        self.assertEqual(attachment["mime_type"], "text/uri-list")
        self.assertEqual(attachment["uploaded_by_user_name"], "Olga")

    def test_natural_command_preview_extracts_calendar_and_reminder(self) -> None:
        calendar = self.services["calendar_service"].create_user_calendar(
            {
                "display_name": "Sluzbowy",
                "description": "Osobisty kalendarz sluzbowy operatora",
                "calendar_kind": "inne",
                "default_duration_minutes": 90,
                "is_active": 1,
            },
            actor_user=self.operator,
            actor="Olga",
            base_url="https://panel.example.com",
        )

        preview = self.services["natural_task_command_service"].parse(
            "Spotkanie z klientem jutro o 14 w kalendarzu Sluzbowy, przypomnij godzine wczesniej",
            actor_user=self.operator,
            organization_id=self.organization["organization_id"],
        )

        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        self.assertEqual(preview["payload"]["task_type"], "wydarzenie")
        self.assertEqual(preview["payload"]["calendar_id"], calendar["user_calendar_id"])
        self.assertEqual(preview["payload"]["calendar_duration_minutes"], 90)
        self.assertEqual(preview["payload"]["due_at"], f"{tomorrow}T14:00")
        self.assertEqual(preview["payload"]["remind_at"], f"{tomorrow}T13:00")
        self.assertEqual(preview["summary"]["calendar_name"], "Sluzbowy")
        self.assertFalse(preview["warnings"])

    def test_natural_command_preview_extracts_recurrence(self) -> None:
        preview = self.services["natural_task_command_service"].parse(
            "Przypomnienie o raportach w dni robocze jutro o 9",
            actor_user=self.operator,
            organization_id=self.organization["organization_id"],
        )

        self.assertEqual(preview["payload"]["task_type"], "przypomnienie")
        self.assertEqual(preview["payload"]["recurrence_pattern"], "dni_robocze")
        self.assertEqual(preview["payload"]["recurrence_weekdays"], "0,1,2,3,4")
        self.assertIn("dni robocze", preview["summary"]["recurrence_label"].lower())

    def test_natural_command_preview_handles_relative_weekday_and_clean_title(self) -> None:
        preview = self.services["natural_task_command_service"].parse(
            "Za tydzien we wtorek bedzie zebranie pracownikow i potrwa poltorej godziny. przypomnij mi dzien wczesniej i godzine wczesniej",
            actor_user=self.operator,
            organization_id=self.organization["organization_id"],
        )

        today = datetime.now().date()
        current_week_start = today - timedelta(days=today.weekday())
        expected_date = current_week_start + timedelta(days=8)
        expected_due = f"{expected_date.strftime('%Y-%m-%d')}T09:00"
        expected_remind = (datetime.strptime(expected_due, "%Y-%m-%dT%H:%M") - timedelta(days=1, hours=1)).strftime(
            "%Y-%m-%dT%H:%M"
        )

        self.assertEqual(preview["payload"]["task_type"], "przypomnienie")
        self.assertEqual(preview["payload"]["due_at"], expected_due)
        self.assertEqual(preview["payload"]["remind_at"], expected_remind)
        self.assertEqual(preview["summary"]["title"], "Zebranie pracownikow")
        self.assertNotIn("Nie podano daty", " ".join(preview["warnings"]))
        self.assertNotIn("przypomnij", preview["summary"]["title"].lower())

    def test_natural_command_preview_parses_weeks_ahead_and_half_hour_reminder(self) -> None:
        preview = self.services["natural_task_command_service"].parse(
            "Za 2 tygodnie w czwartek bedzie przeglad kwartalny i potrwa 1.5 godziny, przypomnij 30 minut wczesniej",
            actor_user=self.operator,
            organization_id=self.organization["organization_id"],
        )

        today = datetime.now().date()
        current_week_start = today - timedelta(days=today.weekday())
        expected_date = current_week_start + timedelta(days=17)
        expected_due = f"{expected_date.strftime('%Y-%m-%d')}T09:00"
        expected_remind = (datetime.strptime(expected_due, "%Y-%m-%dT%H:%M") - timedelta(minutes=30)).strftime(
            "%Y-%m-%dT%H:%M"
        )

        self.assertEqual(preview["payload"]["task_type"], "przypomnienie")
        self.assertEqual(preview["payload"]["due_at"], expected_due)
        self.assertEqual(preview["payload"]["remind_at"], expected_remind)
        self.assertEqual(preview["summary"]["title"], "Przeglad kwartalny")
        self.assertNotIn("Nie podano daty", " ".join(preview["warnings"]))

    def test_natural_command_preview_handles_polish_diacritics(self) -> None:
        preview = self.services["natural_task_command_service"].parse(
            "Za tydzień we wtorek będzie zebranie pracowników i potrwa półtorej godziny, przypomnij godzinę wcześniej",
            actor_user=self.operator,
            organization_id=self.organization["organization_id"],
        )

        today = datetime.now().date()
        current_week_start = today - timedelta(days=today.weekday())
        expected_date = current_week_start + timedelta(days=8)
        expected_due = f"{expected_date.strftime('%Y-%m-%d')}T09:00"
        expected_remind = (datetime.strptime(expected_due, "%Y-%m-%dT%H:%M") - timedelta(hours=1)).strftime(
            "%Y-%m-%dT%H:%M"
        )

        self.assertEqual(preview["payload"]["task_type"], "przypomnienie")
        self.assertEqual(preview["payload"]["due_at"], expected_due)
        self.assertEqual(preview["payload"]["remind_at"], expected_remind)
        self.assertEqual(preview["summary"]["title"], "Zebranie pracowników")

    def test_natural_command_preview_uses_fallback_for_joined_clauses(self) -> None:
        preview = self.services["natural_task_command_service"].parse(
            "Przypomnij mi o przegladzie kwartalnym i przygotowaniu materialow jutro rano",
            actor_user=self.operator,
            organization_id=self.organization["organization_id"],
        )

        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        self.assertEqual(preview["payload"]["task_type"], "przypomnienie")
        self.assertEqual(preview["summary"]["title"], "Przegladzie kwartalnym")
        self.assertEqual(preview["payload"]["due_at"], f"{tomorrow}T09:00")
        self.assertTrue(preview["fallback"]["used"])
        self.assertFalse(preview["fallback"]["needs_review"])
        self.assertEqual(preview["fallback"]["threshold"], 0.8)
        self.assertIn("fallback", preview)

    def test_http_task_endpoints_work_for_operator(self) -> None:
        calendar = self.services["calendar_service"].create_user_calendar(
            {
                "display_name": "Sluzbowy operatora",
                "description": "Osobisty kalendarz sluzbowy operatora",
                "calendar_kind": "inne",
                "default_duration_minutes": 75,
                "is_active": 1,
            },
            actor_user=self.operator,
            actor="Olga",
            base_url="https://panel.example.com",
        )
        server = create_server("127.0.0.1", 0, self.services)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            connection.request(
                "POST",
                "/api/session/login",
                body=json.dumps({"login": "olga", "password": "1234"}),
                headers={"Content-Type": "application/json"},
            )
            response = connection.getresponse()
            payload = response.read()
            self.assertEqual(response.status, 200)
            cookie = response.getheader("Set-Cookie")
            self.assertTrue(cookie)
            user = json.loads(payload.decode("utf-8"))
            self.assertEqual(user["login"], "olga")
            connection.close()

            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            connection.request(
                "POST",
                "/api/tasks",
                body=json.dumps(
                    {
                        "title": "Zadzwonic do kontrahenta",
                        "task_type": "przypomnienie",
                        "status": "nowe",
                        "priority": "normalny",
                        "due_at": "2099-04-10T08:00",
                        "remind_at": "2099-04-10T07:30",
                    }
                ),
                headers={"Content-Type": "application/json", "Cookie": cookie},
            )
            response = connection.getresponse()
            payload = response.read()
            self.assertEqual(response.status, 201)
            created = json.loads(payload.decode("utf-8"))
            task_id = created["task_id"]
            self.assertEqual(created["visibility_scope"], "prywatne")
            connection.close()

            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            connection.request("GET", "/api/tasks/planner", headers={"Cookie": cookie})
            response = connection.getresponse()
            payload = response.read()
            self.assertEqual(response.status, 200)
            planner = json.loads(payload.decode("utf-8"))
            self.assertIn("buckets", planner)
            self.assertIn("dzis", planner["buckets"])
            connection.close()

            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            connection.request("GET", "/api/tasks/focus", headers={"Cookie": cookie})
            response = connection.getresponse()
            payload = response.read()
            self.assertEqual(response.status, 200)
            focus = json.loads(payload.decode("utf-8"))
            self.assertIn("views", focus)
            self.assertTrue(any(item["code"] == "moj_dzien" for item in focus["views"]))
            connection.close()

            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            connection.request("GET", f"/api/tasks/{task_id}", headers={"Cookie": cookie})
            response = connection.getresponse()
            payload = response.read()
            self.assertEqual(response.status, 200)
            detail = json.loads(payload.decode("utf-8"))
            self.assertEqual(detail["task"]["title"], "Zadzwonic do kontrahenta")
            self.assertEqual(detail["task"]["remind_at"], "2099-04-10T07:30")
            connection.close()

            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            connection.request(
                "POST",
                f"/api/tasks/{task_id}/notes",
                body=json.dumps({"note_text": "Klient prosi o kontakt po 14:00."}),
                headers={"Content-Type": "application/json", "Cookie": cookie},
            )
            response = connection.getresponse()
            payload = response.read()
            self.assertEqual(response.status, 201)
            noted = json.loads(payload.decode("utf-8"))
            self.assertEqual(noted["task"]["task_id"], task_id)
            self.assertEqual(noted["notes"][0]["note_text"], "Klient prosi o kontakt po 14:00.")
            connection.close()

            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            connection.request(
                "POST",
                "/api/tasks/parse-natural",
                body=json.dumps(
                    {
                        "command_text": "Spotkanie z klientem jutro o 14 w kalendarzu Sluzbowy operatora, przypomnij godzine wczesniej"
                    }
                ),
                headers={"Content-Type": "application/json", "Cookie": cookie},
            )
            response = connection.getresponse()
            payload = response.read()
            self.assertEqual(response.status, 200)
            preview = json.loads(payload.decode("utf-8"))
            self.assertEqual(preview["payload"]["calendar_id"], calendar["user_calendar_id"])
            self.assertEqual(preview["payload"]["task_type"], "wydarzenie")
            connection.close()

            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            connection.request(
                "POST",
                f"/api/tasks/{task_id}/snooze-reminder",
                body=json.dumps({"mode": "10m"}),
                headers={"Content-Type": "application/json", "Cookie": cookie},
            )
            response = connection.getresponse()
            payload = response.read()
            self.assertEqual(response.status, 200)
            snoozed = json.loads(payload.decode("utf-8"))
            self.assertEqual(snoozed["task"]["reminder_state"], "zaplanowane")
            self.assertTrue(snoozed["task"]["remind_at"])
            connection.close()

            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            connection.request(
                "POST",
                f"/api/tasks/{task_id}/attachments",
                body=json.dumps(
                    {
                        "file_name": "brief.txt",
                        "content_type": "text/plain",
                        "content_base64": base64.b64encode(b"Brief dla testu HTTP").decode("ascii"),
                    }
                ),
                headers={"Content-Type": "application/json", "Cookie": cookie},
            )
            response = connection.getresponse()
            payload = response.read()
            self.assertEqual(response.status, 201)
            attached = json.loads(payload.decode("utf-8"))
            self.assertEqual(attached["attachments"][0]["file_name"], "brief.txt")
            connection.close()

            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            connection.request(
                "POST",
                "/api/session/login",
                body=json.dumps({"login": "ania", "password": "1234"}),
                headers={"Content-Type": "application/json"},
            )
            response = connection.getresponse()
            response.read()
            self.assertEqual(response.status, 200)
            second_cookie = response.getheader("Set-Cookie")
            self.assertTrue(second_cookie)
            connection.close()

            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            connection.request("GET", f"/api/tasks/{task_id}", headers={"Cookie": second_cookie})
            response = connection.getresponse()
            response.read()
            self.assertEqual(response.status, 404)
            connection.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_http_task_reminder_dispatch_endpoint_runs_background_sweep(self) -> None:
        self.services["auth_service"].update_user(
            self.operator["user_id"],
            {"telegram_user_id": "900123"},
            actor_login="admin",
            actor_user=self.admin,
        )
        reminder_service = self.services["task_reminder_service"]
        reminder_service.telegram_adapter.bot_token = "test-token"

        sent_messages: list[tuple[str, str]] = []

        def fake_send(chat_id: str, text: str) -> dict[str, object]:
            sent_messages.append((chat_id, text))
            return {"ok": True}

        reminder_service.telegram_adapter.send_text_message = fake_send  # type: ignore[method-assign]

        self.services["task_service"].create_task(
            {
                "title": "Automatyczne przypomnienie serwera",
                "task_type": "zadanie",
                "status": "nowe",
                "priority": "wysoki",
                "due_at": "2000-04-10T10:30",
                "remind_at": "2000-04-10T09:45",
                "assigned_user_id": self.operator["user_id"],
            },
            actor_user=self.operator,
            actor="Olga",
            organization_id=self.organization["organization_id"],
        )

        server = create_server("127.0.0.1", 0, self.services)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            connection.request(
                "POST",
                "/api/session/login",
                body=json.dumps({"login": "olga", "password": "1234"}),
                headers={"Content-Type": "application/json"},
            )
            response = connection.getresponse()
            response.read()
            self.assertEqual(response.status, 200)
            cookie = response.getheader("Set-Cookie")
            self.assertTrue(cookie)
            connection.close()

            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            connection.request("POST", "/api/tasks/reminders/dispatch", headers={"Cookie": cookie})
            response = connection.getresponse()
            payload = response.read()
            self.assertEqual(response.status, 200)
            result = json.loads(payload.decode("utf-8"))
            self.assertEqual(result["result"]["processed"], 1)
            self.assertEqual(result["result"]["sent"], 1)
            self.assertEqual(result["result"]["failed"], 0)
            self.assertEqual(result["result"]["deferred"], 0)
            self.assertTrue(sent_messages)
            self.assertEqual(sent_messages[0][0], "900123")
            connection.close()

            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            connection.request("GET", "/api/tasks/reminders/status", headers={"Cookie": cookie})
            response = connection.getresponse()
            payload = response.read()
            self.assertEqual(response.status, 200)
            status = json.loads(payload.decode("utf-8"))
            self.assertTrue(status["enabled"])
            self.assertEqual(status["delivery_channel"], "telegram")
            connection.close()

            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            connection.request("GET", "/api/tasks/reminders/outbox?status=sent&limit=5", headers={"Cookie": cookie})
            response = connection.getresponse()
            payload = response.read()
            self.assertEqual(response.status, 200)
            outbox = json.loads(payload.decode("utf-8"))
            self.assertTrue(any(item["status"] == "sent" for item in outbox))
            connection.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_http_task_workflow_covers_comments_checklist_templates_and_approvals(self) -> None:
        server = create_server("127.0.0.1", 0, self.services)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        def request(method: str, path: str, body: dict[str, object] | None = None, cookie: str | None = None):
            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            headers = {"Content-Type": "application/json"}
            if cookie:
                headers["Cookie"] = cookie
            connection.request(method, path, body=json.dumps(body) if body is not None else None, headers=headers)
            response = connection.getresponse()
            payload = response.read()
            connection.close()
            return response, payload

        try:
            response, payload = request("POST", "/api/session/login", {"login": "olga", "password": "1234"})
            self.assertEqual(response.status, 200, payload.decode("utf-8"))
            cookie = response.getheader("Set-Cookie")
            self.assertTrue(cookie)

            response, payload = request(
                "POST",
                "/api/tasks",
                {
                    "title": "Wpis do obiegu",
                    "task_type": "zadanie",
                    "status": "nowe",
                    "priority": "normalny",
                    "due_at": "2099-04-10T10:00",
                    "remind_at": "2099-04-10T09:00",
                },
                cookie,
            )
            self.assertEqual(response.status, 201, payload.decode("utf-8"))
            created_task = json.loads(payload.decode("utf-8"))
            task_id = created_task["task_id"]

            response, payload = request(
                "POST",
                f"/api/tasks/{task_id}/notes",
                {"note_text": "Karol, prosze o akceptacje. @Karol"},
                cookie,
            )
            self.assertEqual(response.status, 201, payload.decode("utf-8"))
            noted = json.loads(payload.decode("utf-8"))
            self.assertEqual(noted["notes"][0]["mentioned_user_names"], ["Karol"])
            note_id = noted["notes"][0]["task_note_id"]

            response, payload = request(
                "POST",
                f"/api/tasks/{task_id}/notes",
                {
                    "note_text": "Doprecyzowanie do komentarza nadrzednego.",
                    "parent_note_id": note_id,
                    "note_kind": "reply",
                },
                cookie,
            )
            self.assertEqual(response.status, 201, payload.decode("utf-8"))
            replied = json.loads(payload.decode("utf-8"))
            self.assertTrue(any(note["parent_note_id"] == note_id for note in replied["notes"]))

            response, payload = request(
                "POST",
                f"/api/tasks/{task_id}/checklist",
                {"item_text": "Zebrac dane do zatwierdzenia"},
                cookie,
            )
            self.assertEqual(response.status, 201, payload.decode("utf-8"))
            checklist_detail = json.loads(payload.decode("utf-8"))
            checklist_item_id = checklist_detail["checklist_items"][0]["task_checklist_item_id"]

            response, payload = request("PATCH", f"/api/tasks/{task_id}/checklist/{checklist_item_id}", {}, cookie)
            self.assertEqual(response.status, 200, payload.decode("utf-8"))
            toggled = json.loads(payload.decode("utf-8"))
            self.assertEqual(toggled["checklist_items"][0]["is_completed"], 1)

            response, payload = request(
                "POST",
                "/api/task-templates",
                {
                    "template_name": "Obieg akceptacji",
                    "template_description": "Powtarzalny wpis z checklista.",
                    "task_type": "zadanie",
                    "priority": "wysoki",
                    "visibility_scope": "prywatne",
                    "due_offset_minutes": 60,
                    "reminder_offset_minutes": 15,
                    "calendar_duration_minutes": 45,
                    "checklist_items": ["Sprawdzic dane", "Zatwierdzic decyzje"],
                },
                cookie,
            )
            self.assertEqual(response.status, 201, payload.decode("utf-8"))
            template = json.loads(payload.decode("utf-8"))
            template_id = template["task_template_id"]

            response, payload = request(
                "POST",
                f"/api/task-templates/{template_id}/apply?anchor_at=2099-04-10T08:00",
                {"title": "Wpis z szablonu"},
                cookie,
            )
            self.assertEqual(response.status, 201, payload.decode("utf-8"))
            applied = json.loads(payload.decode("utf-8"))
            self.assertEqual(applied["task"]["due_at"], "2099-04-10T09:00")
            self.assertEqual([item["item_text"] for item in applied["checklist_items"]], ["Sprawdzic dane", "Zatwierdzic decyzje"])

            response, payload = request(
                "POST",
                "/api/approvals",
                {
                    "entity_type": "task",
                    "entity_id": task_id,
                    "title": "Akceptacja wpisu",
                    "description": "Akceptacja operacyjna przed realizacja.",
                },
                cookie,
            )
            self.assertEqual(response.status, 201, payload.decode("utf-8"))
            approval = json.loads(payload.decode("utf-8"))
            approval_id = approval["approval_request_id"]

            response, payload = request(
                "POST",
                f"/api/approvals/{approval_id}/approve",
                {"reason": "Zatwierdzone operacyjnie."},
                cookie,
            )
            self.assertEqual(response.status, 200, payload.decode("utf-8"))
            approved = json.loads(payload.decode("utf-8"))
            self.assertEqual(approved["status"], "approved")

            response, payload = request("GET", f"/api/tasks/{task_id}", cookie=cookie)
            self.assertEqual(response.status, 200, payload.decode("utf-8"))
            detail = json.loads(payload.decode("utf-8"))
            self.assertEqual(detail["task"]["status"], "w_toku")
            self.assertTrue(any(item["approval_request_id"] == approval_id and item["status"] == "approved" for item in detail["approval_requests"]))
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
