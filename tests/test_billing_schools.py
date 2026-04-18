from __future__ import annotations

import http.client
import json
import threading
import unittest

from app.api.http_server import create_server
from app.bootstrap import build_services
from app.db import reset_database


class BillingSchoolServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.services = build_services()
        self.services["auth_service"].ensure_default_admin()
        self.admin = self.services["auth_service"].list_users()[0]
        self.organization = self.services["organization_service"].create_organization(
            {"name": "Szkoly Klienta", "slug": "szkoly-klienta", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        self.operator = self.services["auth_service"].create_user(
            {
                "login": "ola",
                "display_name": "Ola",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": self.organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=self.admin["user_id"],
            actor_user=self.admin,
        )

    def test_can_create_school_and_prevent_duplicates(self) -> None:
        school = self.services["billing_service"].create_school(
            {
                "full_name": "Szkola Podstawowa nr 4 w Bielsku Podlaskim",
                "short_name": "sp4 bp",
                "city": "Bielsk Podlaski",
                "notes": "Glowna placowka dla wtorku",
                "is_active": 1,
            },
            actor_user=self.operator,
            actor="Ola",
            organization_id=self.organization["organization_id"],
        )

        self.assertEqual(school["short_name"], "SP4 BP")
        self.assertEqual(school["full_name"], "Szkola Podstawowa nr 4 w Bielsku Podlaskim")

        schools = self.services["billing_service"].list_schools(
            organization_id=self.organization["organization_id"]
        )
        self.assertEqual(len(schools), 1)
        self.assertEqual(schools[0]["city"], "Bielsk Podlaski")

        with self.assertRaisesRegex(ValueError, "Ta szkola jest juz dodana"):
            self.services["billing_service"].create_school(
                {
                    "full_name": "szkola podstawowa nr 4 w bielsku podlaskim",
                    "short_name": "SP4 BIS",
                },
                actor_user=self.operator,
                actor="Ola",
                organization_id=self.organization["organization_id"],
            )

        with self.assertRaisesRegex(ValueError, "Ten skrot szkoly jest juz uzywany"):
            self.services["billing_service"].create_school(
                {
                    "full_name": "Szkola Podstawowa nr 5 w Bielsku Podlaskim",
                    "short_name": "sp4 bp",
                },
                actor_user=self.operator,
                actor="Ola",
                organization_id=self.organization["organization_id"],
            )

        logs = self.services["event_repository"].list_logs(organization_id=self.organization["organization_id"])
        self.assertTrue(any(item["event_type"] == "billing_school_created" for item in logs))


class BillingSchoolHttpTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.services = build_services()
        self.services["auth_service"].ensure_default_admin()
        self.admin = self.services["auth_service"].list_users()[0]
        self.organization = self.services["organization_service"].create_organization(
            {"name": "HTTP Szkoly", "slug": "http-szkoly", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        self.services["auth_service"].create_user(
            {
                "login": "ewa",
                "display_name": "Ewa",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": self.organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=self.admin["user_id"],
            actor_user=self.admin,
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

    def test_operator_can_create_and_list_billing_schools_via_api(self) -> None:
        headers = {"Content-Type": "application/json"}
        response, payload = self._request(
            "POST",
            "/api/session/login",
            body=json.dumps({"login": "ewa", "password": "1234"}),
            headers=headers,
        )
        self.assertEqual(response.status, 200)
        cookie = response.getheader("Set-Cookie")
        self.assertTrue(cookie)

        response, payload = self._request(
            "POST",
            "/api/billing/schools",
            body=json.dumps(
                {
                    "full_name": "Szkola Podstawowa nr 3 w Hajnowsce",
                    "short_name": "SP3 H",
                    "city": "Hajnowka",
                    "is_active": 1,
                }
            ),
            headers={"Cookie": cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 201)
        created = json.loads(payload.decode("utf-8"))
        self.assertEqual(created["short_name"], "SP3 H")

        response, payload = self._request("GET", "/api/billing/schools", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200)
        schools = json.loads(payload.decode("utf-8"))
        self.assertEqual(len(schools), 1)
        self.assertEqual(schools[0]["full_name"], "Szkola Podstawowa nr 3 w Hajnowsce")


if __name__ == "__main__":
    unittest.main()
