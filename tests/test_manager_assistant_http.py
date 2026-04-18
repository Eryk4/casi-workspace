from __future__ import annotations

import http.client
import json
import shutil
import threading
import unittest

from app.api.http_server import create_server
from app.bootstrap import build_services
from app.config import KNOWLEDGE_DIR
from app.db import reset_database
from app.demo_seed import seed_demo_data
from app.domain.constants import MANAGER_ASSISTANT_MODULE


class ManagerAssistantHttpTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        shutil.rmtree(KNOWLEDGE_DIR, ignore_errors=True)
        KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
        self.services = build_services()
        self.auth_service = self.services["auth_service"]
        self.organization_service = self.services["organization_service"]
        self.task_service = self.services["task_service"]
        self.admin = self.auth_service.ensure_default_admin()
        seed_demo_data(
            self.services["invoice_service"],
            self.services["invoice_repository"],
            task_service=self.task_service,
            auth_service=self.auth_service,
            billing_service=self.services["billing_service"],
            knowledge_service=self.services["knowledge_service"],
            calendar_service=self.services["calendar_service"],
        )
        self.server = create_server("127.0.0.1", 0, self.services)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def _request(self, method: str, path: str, body: str | None = None, headers: dict[str, str] | None = None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        payload = response.read()
        connection.close()
        return response, payload

    def _login(self, login: str, password: str) -> str:
        response, payload = self._request(
            "POST",
            "/api/session/login",
            body=json.dumps({"login": login, "password": password}),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        cookie = response.getheader("Set-Cookie")
        self.assertTrue(cookie)
        return str(cookie)

    def test_disabled_module_blocks_task_workspace_and_hides_dashboard_task_data(self) -> None:
        assert self.admin is not None
        organization = self.organization_service.create_organization(
            {
                "name": "Klient Bez Asystenta",
                "slug": "klient-bez-asystenta",
                "is_active": 1,
            },
            actor_user=self.admin,
            actor_login="admin",
        )
        org_admin = self.auth_service.create_user(
            {
                "login": "bez-asystenta-admin",
                "display_name": "Bez Asystenta Admin",
                "password": "1234",
                "role": "organization_admin",
                "organization_id": organization["organization_id"],
                "is_active": 1,
            },
            actor_login="admin",
            actor_user_id=self.admin["user_id"],
            actor_user=self.admin,
        )
        self.task_service.create_task(
            {
                "title": "Ukryte przypomnienie",
                "task_type": "przypomnienie",
                "status": "nowe",
                "priority": "normalny",
                "due_at": "2026-04-13T09:00",
                "remind_at": "2026-04-12T09:00",
            },
            actor_user=org_admin,
            actor=org_admin["login"],
            organization_id=int(organization["organization_id"]),
        )

        cookie = self._login("bez-asystenta-admin", "1234")

        response, payload = self._request("GET", "/api/session/current", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200)
        current_user = json.loads(payload.decode("utf-8"))
        self.assertEqual(current_user["organization_modules"], [])

        response, payload = self._request("GET", "/api/tasks", headers={"Cookie": cookie})
        self.assertEqual(response.status, 403)
        self.assertIn("Asystent Szefa", payload.decode("utf-8"))

        response, payload = self._request("GET", "/api/user-calendars", headers={"Cookie": cookie})
        self.assertEqual(response.status, 403)
        self.assertIn("Asystent Szefa", payload.decode("utf-8"))

        response, payload = self._request("GET", "/api/dashboard", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200)
        snapshot = json.loads(payload.decode("utf-8"))
        self.assertEqual(snapshot["cards"]["aktywne_przypomnienia"], 0)
        self.assertEqual(snapshot["active_reminders"], [])
        self.assertTrue(all(not item["event_type"].startswith("task_") for item in snapshot["recent_events"]))

    def test_enabled_module_allows_admin_and_worker_workspace(self) -> None:
        cookie = self._login("casi_admin", "Casi1234")

        response, payload = self._request("GET", "/api/session/current", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200)
        current_user = json.loads(payload.decode("utf-8"))
        self.assertEqual(current_user["organization_modules"], [MANAGER_ASSISTANT_MODULE])

        response, payload = self._request("GET", "/api/tasks", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        tasks = json.loads(payload.decode("utf-8"))
        self.assertTrue(isinstance(tasks, list))

        worker_cookie = self._login("casi_ola", "Casi1234")
        response, payload = self._request("GET", "/api/tasks", headers={"Cookie": worker_cookie})
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        worker_tasks = json.loads(payload.decode("utf-8"))
        self.assertTrue(isinstance(worker_tasks, list))

        response, payload = self._request("GET", "/api/user-calendars", headers={"Cookie": worker_cookie})
        self.assertEqual(response.status, 200, payload.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
