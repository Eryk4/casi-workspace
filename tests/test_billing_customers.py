from __future__ import annotations

import http.client
import json
import threading
import unittest

from app.api.http_server import create_server
from app.bootstrap import build_services
from app.db import reset_database


class BillingCustomersServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.services = build_services()
        self.services["auth_service"].ensure_default_admin()
        self.admin = self.services["auth_service"].list_users()[0]
        self.organization = self.services["organization_service"].create_organization(
            {"name": "Rodziny Klienta", "slug": "rodziny-klienta", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        self.operator = self.services["auth_service"].create_user(
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
        self.school = self.services["billing_service"].create_school(
            {
                "full_name": "Szkola Podstawowa nr 4 w Bielsku Podlaskim",
                "short_name": "SP4 BP",
            },
            actor_user=self.operator,
            actor="Ania",
            organization_id=self.organization["organization_id"],
        )
        self.bank_account = self.services["billing_service"].create_bank_account(
            {
                "account_name": "Rachunek glowny",
                "iban": "PL55111122223333444455556666",
                "currency": "PLN",
            },
            actor_user=self.operator,
            actor="Ania",
            organization_id=self.organization["organization_id"],
        )

    def test_family_payment_is_visible_for_all_students_of_that_family(self) -> None:
        payer = self.services["billing_service"].create_payer(
            {
                "display_name": "Rodzina Kowalskich",
                "contact_phone": "+48 500-600-700",
                "email": "rodzina@example.com",
            },
            actor_user=self.operator,
            actor="Ania",
            organization_id=self.organization["organization_id"],
        )
        self.services["billing_service"].create_student(
            {
                "full_name": "Jan Kowalski",
                "billing_payer_id": payer["billing_payer_id"],
                "billing_school_id": self.school["billing_school_id"],
                "lesson_day": "wtorek",
                "group_name": "Robotyka 1",
            },
            actor_user=self.operator,
            actor="Ania",
            organization_id=self.organization["organization_id"],
        )
        self.services["billing_service"].create_student(
            {
                "full_name": "Anna Kowalska",
                "billing_payer_id": payer["billing_payer_id"],
                "billing_school_id": self.school["billing_school_id"],
                "lesson_day": "wtorek",
                "group_name": "Robotyka 1",
            },
            actor_user=self.operator,
            actor="Ania",
            organization_id=self.organization["organization_id"],
        )

        self.services["billing_service"].import_statement_csv(
            self.bank_account["billing_bank_account_id"],
            "\n".join(
                [
                    "Data ksiegowania;Kwota;Waluta;Opis;Kontrahent;Rachunek kontrahenta;Referencja",
                    "2026-04-09;342,00;PLN;500-600-700 Jan i Anna Kowalscy;Rodzic;PL00111122223333444455556666;RATA-01",
                ]
            ),
            source_file_name="rodzina.csv",
            actor_user=self.operator,
            actor="Ania",
            organization_id=self.organization["organization_id"],
        )

        payers = self.services["billing_service"].list_payers(organization_id=self.organization["organization_id"])
        self.assertEqual(len(payers), 1)
        self.assertEqual(payers[0]["latest_payment_date"], "2026-04-09")
        self.assertEqual(payers[0]["latest_payment_amount"], 342.0)
        self.assertEqual(payers[0]["payment_identifier"], "500600700")

        students = self.services["billing_service"].list_students(organization_id=self.organization["organization_id"])
        self.assertEqual(len(students), 2)
        for student in students:
            self.assertEqual(student["family_last_payment_date"], "2026-04-09")
            self.assertEqual(student["family_last_payment_amount"], 342.0)
            self.assertEqual(student["school_short_name"], "SP4 BP")
            self.assertEqual(student["payer_contact_phone"], "500600700")

    def test_creating_student_with_new_phone_auto_creates_family(self) -> None:
        created = self.services["billing_service"].create_student(
            {
                "full_name": "Maja Nowak",
                "payer_contact_phone": "+48 600-700-800",
                "payer_display_name": "Rodzina Nowakow",
                "payer_email": "nowak@example.com",
                "payer_has_large_family_card": True,
                "billing_school_id": self.school["billing_school_id"],
                "lesson_day": "poniedzialek",
            },
            actor_user=self.operator,
            actor="Ania",
            organization_id=self.organization["organization_id"],
        )

        payers = self.services["billing_service"].list_payers(organization_id=self.organization["organization_id"])
        self.assertEqual(len(payers), 1)
        payer = payers[0]
        self.assertEqual(created["billing_payer_id"], payer["billing_payer_id"])
        self.assertEqual(payer["display_name"], "Rodzina Nowakow")
        self.assertEqual(payer["contact_phone"], "600700800")
        self.assertTrue(bool(payer["has_large_family_card"]))

        students = self.services["billing_service"].list_students(organization_id=self.organization["organization_id"])
        self.assertEqual(len(students), 1)
        self.assertEqual(students[0]["payer_contact_phone"], "600700800")
        self.assertEqual(students[0]["payer_label"], "Rodzina Nowakow")

    def test_students_with_same_phone_reuse_same_family_automatically(self) -> None:
        first = self.services["billing_service"].create_student(
            {
                "full_name": "Lena Kruk",
                "payer_contact_phone": "500-600-700",
                "payer_display_name": "Rodzina Kruk",
                "billing_school_id": self.school["billing_school_id"],
                "lesson_day": "piatek",
            },
            actor_user=self.operator,
            actor="Ania",
            organization_id=self.organization["organization_id"],
        )
        second = self.services["billing_service"].create_student(
            {
                "full_name": "Maja Kruk",
                "payer_contact_phone": "+48 500 600 700",
                "billing_school_id": self.school["billing_school_id"],
                "lesson_day": "piatek",
            },
            actor_user=self.operator,
            actor="Ania",
            organization_id=self.organization["organization_id"],
        )

        self.assertEqual(first["billing_payer_id"], second["billing_payer_id"])
        payers = self.services["billing_service"].list_payers(organization_id=self.organization["organization_id"])
        self.assertEqual(len(payers), 1)
        self.assertEqual(payers[0]["contact_phone"], "500600700")
        self.assertEqual(payers[0]["display_name"], "Rodzina Kruk")


class BillingCustomersHttpTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.services = build_services()
        self.services["auth_service"].ensure_default_admin()
        self.admin = self.services["auth_service"].list_users()[0]
        self.organization = self.services["organization_service"].create_organization(
            {"name": "HTTP Rodziny", "slug": "http-rodziny", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        self.services["auth_service"].create_user(
            {
                "login": "basia",
                "display_name": "Basia",
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

    def test_operator_can_create_family_and_student_via_api(self) -> None:
        headers = {"Content-Type": "application/json"}
        response, payload = self._request(
            "POST",
            "/api/session/login",
            body=json.dumps({"login": "basia", "password": "1234"}),
            headers=headers,
        )
        self.assertEqual(response.status, 200)
        cookie = response.getheader("Set-Cookie")
        self.assertTrue(cookie)

        response, payload = self._request(
            "POST",
            "/api/billing/schools",
            body=json.dumps({"full_name": "Szkola Podstawowa nr 5", "short_name": "SP5"}),
            headers={"Cookie": cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 201)
        school = json.loads(payload.decode("utf-8"))

        response, payload = self._request(
            "POST",
            "/api/billing/payers",
            body=json.dumps({"display_name": "Rodzina Nowakow", "contact_phone": "600-700-800"}),
            headers={"Cookie": cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 201)
        payer = json.loads(payload.decode("utf-8"))
        self.assertEqual(payer["contact_phone"], "600700800")

        response, payload = self._request(
            "POST",
            "/api/billing/students",
            body=json.dumps(
                {
                    "full_name": "Maja Nowak",
                    "billing_payer_id": payer["billing_payer_id"],
                    "billing_school_id": school["billing_school_id"],
                    "lesson_day": "poniedzialek",
                }
            ),
            headers={"Cookie": cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 201)

        response, payload = self._request("GET", "/api/billing/students", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200)
        students = json.loads(payload.decode("utf-8"))
        self.assertEqual(len(students), 1)
        self.assertEqual(students[0]["full_name"], "Maja Nowak")
        self.assertEqual(students[0]["payer_contact_phone"], "600700800")

    def test_operator_can_create_student_and_family_via_student_endpoint_using_phone(self) -> None:
        headers = {"Content-Type": "application/json"}
        response, payload = self._request(
            "POST",
            "/api/session/login",
            body=json.dumps({"login": "basia", "password": "1234"}),
            headers=headers,
        )
        self.assertEqual(response.status, 200)
        cookie = response.getheader("Set-Cookie")
        self.assertTrue(cookie)

        response, payload = self._request(
            "POST",
            "/api/billing/schools",
            body=json.dumps({"full_name": "Szkola Podstawowa nr 7", "short_name": "SP7"}),
            headers={"Cookie": cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 201)
        school = json.loads(payload.decode("utf-8"))

        response, payload = self._request(
            "POST",
            "/api/billing/students",
            body=json.dumps(
                {
                    "full_name": "Igor Lis",
                    "payer_contact_phone": "+48 700-800-900",
                    "payer_display_name": "Rodzina Lis",
                    "payer_has_large_family_card": True,
                    "billing_school_id": school["billing_school_id"],
                    "lesson_day": "sroda",
                }
            ),
            headers={"Cookie": cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 201)
        created = json.loads(payload.decode("utf-8"))
        self.assertEqual(created["payer_contact_phone"], "700800900")

        response, payload = self._request("GET", "/api/billing/payers", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200)
        payers = json.loads(payload.decode("utf-8"))
        self.assertEqual(len(payers), 1)
        self.assertEqual(payers[0]["display_name"], "Rodzina Lis")
        self.assertEqual(payers[0]["contact_phone"], "700800900")
        self.assertTrue(bool(payers[0]["has_large_family_card"]))


if __name__ == "__main__":
    unittest.main()
