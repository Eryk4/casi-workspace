from __future__ import annotations

import http.client
import json
import threading
import unittest

from app.api.http_server import create_server
from app.bootstrap import build_services
from app.db import reset_database


class BillingModelsServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.services = build_services()
        self.services["auth_service"].ensure_default_admin()
        self.admin = self.services["auth_service"].list_users()[0]
        self.organization = self.services["organization_service"].create_organization(
            {"name": "Modele Klienta", "slug": "modele-klienta", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        self.operator = self.services["auth_service"].create_user(
            {
                "login": "zosia-model",
                "display_name": "Zosia Model",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": self.organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=self.admin["user_id"],
            actor_user=self.admin,
        )
        self.school = self.services["billing_service"].create_school(
            {
                "full_name": "Szkola Podstawowa nr 4",
                "short_name": "SP4",
            },
            actor_user=self.operator,
            actor="Zosia Model",
            organization_id=self.organization["organization_id"],
        )
        self.payer = self.services["billing_service"].create_payer(
            {
                "display_name": "Rodzina Testowa",
                "contact_phone": "500600700",
            },
            actor_user=self.operator,
            actor="Zosia Model",
            organization_id=self.organization["organization_id"],
        )

    def test_can_create_model_and_assign_it_to_student(self) -> None:
        model = self.services["billing_service"].create_model(
            {
                "name": "26/27 Wtorek",
                "school_year": "2026/2027",
                "lesson_day": "wtorek",
                "settlement_mode": "monthly",
                "monthly_rate_amount": "57",
                "semester_rate_amount": "54",
                "sibling_discount_amount": "100",
                "large_family_discount_amount": "50",
                "intro_free_lessons_count": "1",
                "contract_required": "1",
            },
            actor_user=self.operator,
            actor="Zosia Model",
            organization_id=self.organization["organization_id"],
        )

        self.assertEqual(model["name"], "26/27 Wtorek")
        self.assertEqual(model["settlement_mode"], "monthly")

        student = self.services["billing_service"].create_student(
            {
                "full_name": "Ola Test",
                "billing_payer_id": self.payer["billing_payer_id"],
                "billing_school_id": self.school["billing_school_id"],
                "billing_model_id": model["billing_model_id"],
            },
            actor_user=self.operator,
            actor="Zosia Model",
            organization_id=self.organization["organization_id"],
        )

        self.assertEqual(student["model_name"], "26/27 Wtorek")
        self.assertEqual(student["lesson_day"], "wtorek")

        models = self.services["billing_service"].list_models(organization_id=self.organization["organization_id"])
        self.assertEqual(len(models), 1)

        logs = self.services["event_repository"].list_logs(organization_id=self.organization["organization_id"])
        self.assertTrue(any(item["event_type"] == "billing_model_created" for item in logs))


class BillingModelsHttpTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.services = build_services()
        self.services["auth_service"].ensure_default_admin()
        self.admin = self.services["auth_service"].list_users()[0]
        self.organization = self.services["organization_service"].create_organization(
            {"name": "HTTP Modele", "slug": "http-modele", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        self.services["auth_service"].create_user(
            {
                "login": "ola-model",
                "display_name": "Ola Model",
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

    def test_operator_can_create_and_list_models_via_api(self) -> None:
        headers = {"Content-Type": "application/json"}
        response, payload = self._request(
            "POST",
            "/api/session/login",
            body=json.dumps({"login": "ola-model", "password": "1234"}),
            headers=headers,
        )
        self.assertEqual(response.status, 200)
        cookie = response.getheader("Set-Cookie")
        self.assertTrue(cookie)

        response, payload = self._request(
            "POST",
            "/api/billing/models",
            body=json.dumps(
                {
                    "name": "26/27 Piatek",
                    "school_year": "2026/2027",
                    "lesson_day": "piatek",
                    "settlement_mode": "semester",
                    "monthly_rate_amount": 57,
                    "semester_rate_amount": 54,
                }
            ),
            headers={"Cookie": cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 201)
        model = json.loads(payload.decode("utf-8"))
        self.assertEqual(model["lesson_day"], "piatek")

        response, payload = self._request("GET", "/api/billing/models", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200)
        models = json.loads(payload.decode("utf-8"))
        self.assertEqual(len(models), 1)
        self.assertEqual(models[0]["name"], "26/27 Piatek")


if __name__ == "__main__":
    unittest.main()
