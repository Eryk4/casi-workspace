from __future__ import annotations

import json

from app.db import get_connection
from tests.http_server_support import HttpServerTestCase


class BillingNextStepEventsHttpTests(HttpServerTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.admin = self.services["auth_service"].list_users()[0]
        self.organization = self.services["organization_service"].create_organization(
            {"name": "Misja Next Step", "slug": "misja-next-step", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        self.second_organization = self.services["organization_service"].create_organization(
            {"name": "CASI Next Step", "slug": "casi-next-step", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        self.operator = self.services["auth_service"].create_user(
            {
                "login": "next-step-operator",
                "display_name": "Operator Next Step",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": self.organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=self.admin["user_id"],
            actor_user=self.admin,
        )
        self.payer = self.services["billing_service"].create_payer(
            {
                "display_name": "Rodzina Next Step",
                "contact_phone": "501600777",
                "payment_identifier": "501600777",
            },
            actor_user=self.operator,
            actor="Operator Next Step",
            organization_id=self.organization["organization_id"],
        )
        self.other_payer = self.services["billing_service"].create_payer(
            {
                "display_name": "Rodzina Obca",
                "contact_phone": "501600778",
                "payment_identifier": "501600778",
            },
            actor_user=self.admin,
            actor="admin",
            organization_id=self.second_organization["organization_id"],
        )
        self.bank_account = self.services["billing_service"].create_bank_account(
            {
                "account_name": "Rachunek next step",
                "bank_name": "Bank Next Step",
                "iban": "PL10111122223333444455556666",
                "currency": "PLN",
            },
            actor_user=self.operator,
            actor="Operator Next Step",
            organization_id=self.organization["organization_id"],
        )
        self.services["billing_service"].import_statement_csv(
            self.bank_account["billing_bank_account_id"],
            "\n".join(
                [
                    "Data ksiegowania;Kwota;Waluta;Opis;Kontrahent;Rachunek kontrahenta;Referencja",
                    "2026-11-12;228,00;PLN;Wplata next step;Rodzina Next Step;PL00111122223333444455556666;NEXT-001",
                ]
            ),
            source_file_name="next-step.csv",
            actor_user=self.operator,
            actor="Operator Next Step",
            organization_id=self.organization["organization_id"],
        )
        transactions = self.services["billing_service"].list_transactions(
            organization_id=self.organization["organization_id"],
            billing_bank_account_id=self.bank_account["billing_bank_account_id"],
        )
        self.transaction_id = int(transactions[0]["billing_transaction_id"])
        self.cookie = self._login_default_admin()

    def _next_step_count(self) -> int:
        with get_connection() as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM billing_next_step_events").fetchone()
        return int(row["count"])

    def _financial_state(self, organization_id: int) -> dict[str, object]:
        with get_connection() as connection:
            ledger_count = int(connection.execute("SELECT COUNT(*) AS count FROM billing_payer_ledger_entries").fetchone()["count"])
        return {
            "transactions": self.services["billing_service"].list_transactions(organization_id=organization_id),
            "charges": self.services["billing_service"].list_charges(organization_id=organization_id),
            "matches": self.services["billing_ledger_service"].list_payment_matches(organization_id=organization_id),
            "balances": self.services["billing_ledger_service"].list_balances(organization_id=organization_id),
            "ledger_entries": ledger_count,
        }

    def test_can_add_and_list_payer_and_payment_next_steps_without_financial_side_effects(self) -> None:
        organization_id = int(self.organization["organization_id"])
        financial_before = self._financial_state(organization_id)

        response, payload = self._request(
            "POST",
            f"/api/billing/next-step-events?organization_id={organization_id}",
            body=json.dumps(
                {
                    "target_type": "payer",
                    "target_id": self.payer["billing_payer_id"],
                    "related_issue_key": f"payer:{self.payer['billing_payer_id']}:debt",
                    "step_type": "call",
                    "event_action": "planned",
                    "title": " Zadzwonic w sprawie rozliczenia ",
                    "note_text": " Test live: reczny krok bez przypomnienia. ",
                    "planned_for": "2026-12-18",
                }
            ),
            headers={"Content-Type": "application/json", "Cookie": self.cookie},
        )
        self.assertEqual(response.status, 201, payload.decode("utf-8"))
        event = json.loads(payload)
        self.assertEqual(event["title"], "Zadzwonic w sprawie rozliczenia")
        self.assertEqual(event["note_text"], "Test live: reczny krok bez przypomnienia.")
        self.assertEqual(event["event_action"], "planned")
        self.assertEqual(event["step_type"], "call")
        self.assertEqual(event["planned_for"], "2026-12-18")
        self.assertEqual(int(event["organization_id"]), organization_id)

        response, payload = self._request(
            "POST",
            f"/api/billing/next-step-events?organization_id={organization_id}",
            body=json.dumps(
                {
                    "target_type": "payment",
                    "target_id": self.transaction_id,
                    "step_type": "check_payment",
                    "event_action": "planned",
                    "title": "Sprawdzic, czy wplata przyszla po piatku",
                }
            ),
            headers={"Content-Type": "application/json", "Cookie": self.cookie},
        )
        self.assertEqual(response.status, 201, payload.decode("utf-8"))
        self.assertEqual(json.loads(payload)["target_type"], "payment")

        response, payload = self._request(
            "GET",
            f"/api/billing/next-step-events?organization_id={organization_id}",
            headers={"Cookie": self.cookie},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        data = json.loads(payload)
        self.assertEqual(int(data["organization_id"]), organization_id)
        self.assertEqual(len(data["events"]), 2)

        response, payload = self._request(
            "GET",
            f"/api/billing/next-step-events?organization_id={organization_id}&target_type=payer&target_id={self.payer['billing_payer_id']}",
            headers={"Cookie": self.cookie},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        self.assertEqual(len(json.loads(payload)["events"]), 1)

        self.assertEqual(financial_before, self._financial_state(organization_id))

        logs = self.services["event_repository"].list_logs(organization_id=organization_id)
        next_step_logs = [item for item in logs if item["event_type"] == "billing_next_step_event_added"]
        self.assertTrue(next_step_logs)
        details_items = [
            json.loads(item.get("details") or "{}") if isinstance(item.get("details"), str) else (item.get("details") or {})
            for item in next_step_logs
        ]
        self.assertTrue(all("note_text" not in details for details in details_items))
        self.assertTrue(
            any(
                details.get("event_action") == "planned" and details.get("step_type") == "check_payment"
                for details in details_items
            )
        )

    def test_can_add_completed_and_snoozed_append_only_events(self) -> None:
        organization_id = int(self.organization["organization_id"])
        for action in ("completed", "snoozed"):
            response, payload = self._request(
                "POST",
                f"/api/billing/next-step-events?organization_id={organization_id}",
                body=json.dumps(
                    {
                        "target_type": "payer",
                        "target_id": self.payer["billing_payer_id"],
                        "step_type": "wait_for_response",
                        "event_action": action,
                        "title": f"Krok {action}",
                    }
                ),
                headers={"Content-Type": "application/json", "Cookie": self.cookie},
            )
            self.assertEqual(response.status, 201, payload.decode("utf-8"))
            self.assertEqual(json.loads(payload)["event_action"], action)
        self.assertEqual(self._next_step_count(), 2)

    def test_rejects_invalid_payloads_without_writing_event(self) -> None:
        organization_id = int(self.organization["organization_id"])
        before_count = self._next_step_count()
        base = {
            "target_type": "payer",
            "target_id": self.payer["billing_payer_id"],
            "step_type": "call",
            "event_action": "planned",
            "title": "Poprawny tytul",
        }
        invalid_payloads = (
            {**base, "target_type": "invoice"},
            {**base, "step_type": "settle_payment"},
            {**base, "event_action": "paid"},
            {**base, "title": "   "},
            {**base, "title": "x" * 201},
            {**base, "note_text": "x" * 1001},
            {**base, "planned_for": "jutro"},
            {**base, "role": "admin"},
        )
        for body in invalid_payloads:
            response, payload = self._request(
                "POST",
                f"/api/billing/next-step-events?organization_id={organization_id}",
                body=json.dumps(body),
                headers={"Content-Type": "application/json", "Cookie": self.cookie},
            )
            self.assertEqual(response.status, 400, payload.decode("utf-8"))
        self.assertEqual(before_count, self._next_step_count())

    def test_cross_org_get_and_post_are_blocked(self) -> None:
        organization_id = int(self.organization["organization_id"])
        wrong_organization_id = int(self.second_organization["organization_id"])
        before_count = self._next_step_count()

        response, payload = self._request(
            "POST",
            f"/api/billing/next-step-events?organization_id={organization_id}",
            body=json.dumps(
                {
                    "target_type": "payer",
                    "target_id": self.payer["billing_payer_id"],
                    "step_type": "call",
                    "event_action": "planned",
                    "title": "Widoczny tylko w Misji",
                }
            ),
            headers={"Content-Type": "application/json", "Cookie": self.cookie},
        )
        self.assertEqual(response.status, 201, payload.decode("utf-8"))

        response, payload = self._request(
            "POST",
            f"/api/billing/next-step-events?organization_id={wrong_organization_id}",
            body=json.dumps(
                {
                    "target_type": "payer",
                    "target_id": self.payer["billing_payer_id"],
                    "step_type": "call",
                    "event_action": "planned",
                    "title": "Nie powinna sie zapisac",
                }
            ),
            headers={"Content-Type": "application/json", "Cookie": self.cookie},
        )
        self.assertEqual(response.status, 404, payload.decode("utf-8"))

        response, payload = self._request(
            "POST",
            f"/api/billing/next-step-events?organization_id={wrong_organization_id}",
            body=json.dumps(
                {
                    "target_type": "payment",
                    "target_id": self.transaction_id,
                    "step_type": "check_payment",
                    "event_action": "planned",
                    "title": "Nie powinna sie zapisac",
                }
            ),
            headers={"Content-Type": "application/json", "Cookie": self.cookie},
        )
        self.assertEqual(response.status, 404, payload.decode("utf-8"))

        response, payload = self._request(
            "GET",
            f"/api/billing/next-step-events?organization_id={wrong_organization_id}",
            headers={"Cookie": self.cookie},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        self.assertEqual(json.loads(payload)["events"], [])
        self.assertEqual(before_count + 1, self._next_step_count())


if __name__ == "__main__":
    import unittest

    unittest.main()
