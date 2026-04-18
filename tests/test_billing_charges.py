from __future__ import annotations

import http.client
import json
import threading
import unittest

from app.api.http_server import create_server
from app.bootstrap import build_services
from app.db import reset_database


class BillingChargesServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.services = build_services()
        self.services["auth_service"].ensure_default_admin()
        self.admin = self.services["auth_service"].list_users()[0]
        self.organization = self.services["organization_service"].create_organization(
            {"name": "Rozliczenia Test", "slug": "rozliczenia-test", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        self.operator = self.services["auth_service"].create_user(
            {
                "login": "zosia-charge",
                "display_name": "Zosia Charge",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": self.organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=self.admin["user_id"],
            actor_user=self.admin,
        )

    def _create_model(
        self,
        *,
        name: str,
        monthly_rate_amount: str,
        semester_rate_amount: str = "54",
        sibling_discount_amount: str = "100",
        large_family_discount_amount: str = "50",
        intro_free_lessons_count: str = "1",
    ) -> dict:
        return self.services["billing_service"].create_model(
            {
                "name": name,
                "school_year": "2026/2027",
                "lesson_day": "wtorek",
                "settlement_mode": "monthly",
                "monthly_rate_amount": monthly_rate_amount,
                "semester_rate_amount": semester_rate_amount,
                "sibling_discount_amount": sibling_discount_amount,
                "large_family_discount_amount": large_family_discount_amount,
                "intro_free_lessons_count": intro_free_lessons_count,
            },
            actor_user=self.operator,
            actor="Zosia Charge",
            organization_id=self.organization["organization_id"],
        )

    def _create_payer(self, *, phone: str, has_large_family_card: bool = False) -> dict:
        return self.services["billing_service"].create_payer(
            {
                "display_name": "Rodzina Testowa",
                "contact_phone": phone,
                "has_large_family_card": 1 if has_large_family_card else 0,
            },
            actor_user=self.operator,
            actor="Zosia Charge",
            organization_id=self.organization["organization_id"],
        )

    def _create_student(
        self,
        *,
        payer_id: int,
        model_id: int,
        full_name: str,
        family_billing_order: int,
    ) -> dict:
        return self.services["billing_service"].create_student(
            {
                "full_name": full_name,
                "billing_payer_id": payer_id,
                "billing_model_id": model_id,
                "family_billing_order": family_billing_order,
            },
            actor_user=self.operator,
            actor="Zosia Charge",
            organization_id=self.organization["organization_id"],
        )

    def test_generate_charges_applies_intro_sibling_and_large_family_card(self) -> None:
        model = self._create_model(name="26/27 Wtorek", monthly_rate_amount="57")
        payer = self._create_payer(phone="500600700", has_large_family_card=True)
        self._create_student(
            payer_id=payer["billing_payer_id"],
            model_id=model["billing_model_id"],
            full_name="Ala Pierwsza",
            family_billing_order=1,
        )
        self._create_student(
            payer_id=payer["billing_payer_id"],
            model_id=model["billing_model_id"],
            full_name="Beata Druga",
            family_billing_order=2,
        )

        result = self.services["billing_service"].generate_charges_for_model(
            {
                "billing_model_id": model["billing_model_id"],
                "period_label": "Pazdziernik 2026",
                "due_date": "2026-10-10",
                "lesson_count": 4,
            },
            actor_user=self.operator,
            actor="Zosia Charge",
            organization_id=self.organization["organization_id"],
        )

        self.assertEqual(result["charge_count"], 2)
        charges = {
            item["student_full_name"]: item
            for item in self.services["billing_service"].list_charges(
                organization_id=self.organization["organization_id"],
                billing_model_id=model["billing_model_id"],
                limit=10,
            )
        }

        first = charges["Ala Pierwsza"]
        self.assertEqual(first["base_amount"], 228.0)
        self.assertEqual(first["intro_free_discount_amount"], 57.0)
        self.assertEqual(first["sibling_discount_amount"], 0.0)
        self.assertEqual(first["large_family_discount_amount"], 50.0)
        self.assertEqual(first["total_amount"], 121.0)

        second = charges["Beata Druga"]
        self.assertEqual(second["base_amount"], 228.0)
        self.assertEqual(second["intro_free_discount_amount"], 57.0)
        self.assertEqual(second["sibling_discount_amount"], 100.0)
        self.assertEqual(second["large_family_discount_amount"], 0.0)
        self.assertEqual(second["total_amount"], 71.0)

        logs = self.services["event_repository"].list_logs(organization_id=self.organization["organization_id"])
        self.assertTrue(any(item["event_type"] == "billing_charge_batch_generated" for item in logs))

    def test_generate_charges_carries_sibling_discount_between_periods(self) -> None:
        model = self._create_model(
            name="26/27 Mala rata",
            monthly_rate_amount="25",
            sibling_discount_amount="100",
            large_family_discount_amount="0",
            intro_free_lessons_count="0",
        )
        payer = self._create_payer(phone="501600700", has_large_family_card=False)
        self._create_student(
            payer_id=payer["billing_payer_id"],
            model_id=model["billing_model_id"],
            full_name="Celina Pierwsza",
            family_billing_order=1,
        )
        self._create_student(
            payer_id=payer["billing_payer_id"],
            model_id=model["billing_model_id"],
            full_name="Dawid Drugi",
            family_billing_order=2,
        )

        self.services["billing_service"].generate_charges_for_model(
            {
                "billing_model_id": model["billing_model_id"],
                "period_label": "Wrzesien 2026",
                "due_date": "2026-09-10",
                "lesson_count": 2,
            },
            actor_user=self.operator,
            actor="Zosia Charge",
            organization_id=self.organization["organization_id"],
        )
        self.services["billing_service"].generate_charges_for_model(
            {
                "billing_model_id": model["billing_model_id"],
                "period_label": "Pazdziernik 2026",
                "due_date": "2026-10-10",
                "lesson_count": 1,
            },
            actor_user=self.operator,
            actor="Zosia Charge",
            organization_id=self.organization["organization_id"],
        )
        self.services["billing_service"].generate_charges_for_model(
            {
                "billing_model_id": model["billing_model_id"],
                "period_label": "Listopad 2026",
                "due_date": "2026-11-10",
                "lesson_count": 1,
            },
            actor_user=self.operator,
            actor="Zosia Charge",
            organization_id=self.organization["organization_id"],
        )

        charges = self.services["billing_service"].list_charges(
            organization_id=self.organization["organization_id"],
            billing_model_id=model["billing_model_id"],
            limit=20,
        )
        second_child = {
            item["period_label"]: item
            for item in charges
            if item["student_full_name"] == "Dawid Drugi"
        }

        self.assertEqual(second_child["Wrzesien 2026"]["sibling_discount_amount"], 50.0)
        self.assertEqual(second_child["Wrzesien 2026"]["total_amount"], 0.0)
        self.assertEqual(second_child["Pazdziernik 2026"]["sibling_discount_amount"], 25.0)
        self.assertEqual(second_child["Pazdziernik 2026"]["total_amount"], 0.0)
        self.assertEqual(second_child["Listopad 2026"]["sibling_discount_amount"], 25.0)
        self.assertEqual(second_child["Listopad 2026"]["total_amount"], 0.0)


class BillingChargesHttpTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.services = build_services()
        self.services["auth_service"].ensure_default_admin()
        self.admin = self.services["auth_service"].list_users()[0]
        self.organization = self.services["organization_service"].create_organization(
            {"name": "HTTP Rozliczenia", "slug": "http-rozliczenia", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        self.services["auth_service"].create_user(
            {
                "login": "ola-charge",
                "display_name": "Ola Charge",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": self.organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=self.admin["user_id"],
            actor_user=self.admin,
        )
        operator = self.services["auth_service"].list_users()[-1]
        self.model = self.services["billing_service"].create_model(
            {
                "name": "26/27 Piatek",
                "school_year": "2026/2027",
                "lesson_day": "piatek",
                "settlement_mode": "monthly",
                "monthly_rate_amount": 57,
                "semester_rate_amount": 54,
            },
            actor_user=operator,
            actor="Ola Charge",
            organization_id=self.organization["organization_id"],
        )
        payer = self.services["billing_service"].create_payer(
            {
                "display_name": "Rodzina HTTP",
                "contact_phone": "502600700",
                "has_large_family_card": 1,
            },
            actor_user=operator,
            actor="Ola Charge",
            organization_id=self.organization["organization_id"],
        )
        self.services["billing_service"].create_student(
            {
                "full_name": "Hania HTTP",
                "billing_payer_id": payer["billing_payer_id"],
                "billing_model_id": self.model["billing_model_id"],
                "family_billing_order": 1,
            },
            actor_user=operator,
            actor="Ola Charge",
            organization_id=self.organization["organization_id"],
        )
        self.services["billing_service"].create_student(
            {
                "full_name": "Igor HTTP",
                "billing_payer_id": payer["billing_payer_id"],
                "billing_model_id": self.model["billing_model_id"],
                "family_billing_order": 2,
            },
            actor_user=operator,
            actor="Ola Charge",
            organization_id=self.organization["organization_id"],
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

    def test_operator_can_generate_and_list_charges_via_api(self) -> None:
        headers = {"Content-Type": "application/json"}
        response, payload = self._request(
            "POST",
            "/api/session/login",
            body=json.dumps({"login": "ola-charge", "password": "1234"}),
            headers=headers,
        )
        self.assertEqual(response.status, 200)
        cookie = response.getheader("Set-Cookie")
        self.assertTrue(cookie)

        response, payload = self._request(
            "POST",
            "/api/billing/charges/generate",
            body=json.dumps(
                {
                    "billing_model_id": self.model["billing_model_id"],
                    "period_label": "Pazdziernik 2026",
                    "due_date": "2026-10-10",
                    "lesson_count": 4,
                }
            ),
            headers={"Cookie": cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 201)
        result = json.loads(payload.decode("utf-8"))
        self.assertEqual(result["charge_count"], 2)

        response, payload = self._request("GET", "/api/billing/charges", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200)
        charges = json.loads(payload.decode("utf-8"))
        self.assertEqual(len(charges), 2)
        self.assertTrue(any(item["student_full_name"] == "Hania HTTP" for item in charges))
        self.assertTrue(any(item["student_full_name"] == "Igor HTTP" for item in charges))


if __name__ == "__main__":
    unittest.main()
