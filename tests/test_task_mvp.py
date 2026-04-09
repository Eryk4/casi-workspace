from __future__ import annotations

import http.client
import json
import threading
import unittest

from app.api.http_server import create_server
from app.bootstrap import build_services
from app.db import reset_database


class TaskMvpTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.services = build_services()
        self.services["auth_service"].ensure_default_admin()
        self.admin = self.services["auth_service"].list_users()[0]
        self.organization = self.services["organization_service"].create_organization(
            {"name": "Klient Zadaniowy", "slug": "klient-zadaniowy", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
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

    def test_task_service_can_create_update_and_add_note(self) -> None:
        created = self.services["task_service"].create_task(
            {
                "title": "Przygotowac spotkanie z klientem",
                "task_type": "zadanie",
                "status": "nowe",
                "priority": "wysoki",
                "due_at": "2026-04-10T10:30",
                "remind_at": "2026-04-10T09:45",
                "assigned_user_id": self.operator["user_id"],
                "description": "Zebrac materialy i potwierdzic zakres rozmowy.",
            },
            actor_user=self.operator,
            actor="Olga",
            organization_id=self.organization["organization_id"],
        )
        self.assertEqual(created["title"], "Przygotowac spotkanie z klientem")
        self.assertEqual(created["assigned_user_name"], "Olga")
        self.assertEqual(created["remind_at"], "2026-04-10T09:45")
        self.assertEqual(created["reminder_state"], "zaplanowane")

        updated = self.services["task_service"].update_task(
            created["task_id"],
            {
                "status": "w_toku",
                "priority": "krytyczny",
                "due_at": "2026-04-11T09:15",
                "remind_at": "2026-04-11T08:15",
            },
            actor_user=self.operator,
            actor="Olga",
            organization_id=self.organization["organization_id"],
        )
        self.assertIsNotNone(updated)
        assert updated is not None
        self.assertEqual(updated["status"], "w_toku")
        self.assertEqual(updated["priority"], "krytyczny")
        self.assertEqual(updated["remind_at"], "2026-04-11T08:15")

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

        snapshot = self.services["dashboard_service"].get_snapshot(organization_id=self.organization["organization_id"])
        self.assertEqual(snapshot["cards"]["aktywne_przypomnienia"], 1)
        self.assertTrue(snapshot["active_reminders"])
        self.assertEqual(snapshot["active_reminders"][0]["title"], "Przypomniec o podpisaniu umowy")

    def test_reminder_cannot_be_later_than_due_time(self) -> None:
        with self.assertRaisesRegex(ValueError, "Godzina przypomnienia nie moze byc pozniejsza niz termin zadania."):
            self.services["task_service"].create_task(
                {
                    "title": "Bledne przypomnienie",
                    "task_type": "zadanie",
                    "status": "nowe",
                    "priority": "normalny",
                    "due_at": "2026-04-10T08:00",
                    "remind_at": "2026-04-10T09:00",
                },
                actor_user=self.operator,
                actor="Olga",
                organization_id=self.organization["organization_id"],
            )

    def test_http_task_endpoints_work_for_operator(self) -> None:
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
                        "due_at": "2026-04-10T08:00",
                        "remind_at": "2026-04-10T07:30",
                    }
                ),
                headers={"Content-Type": "application/json", "Cookie": cookie},
            )
            response = connection.getresponse()
            payload = response.read()
            self.assertEqual(response.status, 201)
            created = json.loads(payload.decode("utf-8"))
            task_id = created["task_id"]
            connection.close()

            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            connection.request("GET", f"/api/tasks/{task_id}", headers={"Cookie": cookie})
            response = connection.getresponse()
            payload = response.read()
            self.assertEqual(response.status, 200)
            detail = json.loads(payload.decode("utf-8"))
            self.assertEqual(detail["task"]["title"], "Zadzwonic do kontrahenta")
            self.assertEqual(detail["task"]["remind_at"], "2026-04-10T07:30")
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
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
