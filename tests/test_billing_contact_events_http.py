from __future__ import annotations

import json

from app.db import get_connection
from tests.http_server_support import HttpServerTestCase


class BillingContactEventsHttpTests(HttpServerTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.admin = self.services["auth_service"].list_users()[0]
        self.organization = self.services["organization_service"].create_organization(
            {"name": "Misja Kontakt", "slug": "misja-kontakt", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        self.second_organization = self.services["organization_service"].create_organization(
            {"name": "CASI Kontakt", "slug": "casi-kontakt", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        self.operator = self.services["auth_service"].create_user(
            {
                "login": "contact-operator",
                "display_name": "Operator Kontakt",
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
                "display_name": "Rodzina Kontaktowa",
                "contact_phone": "501600701",
                "email": "kontakt@example.com",
                "payment_identifier": "KONTAKT-001",
            },
            actor_user=self.operator,
            actor="Operator Kontakt",
            organization_id=self.organization["organization_id"],
        )
        self.other_payer = self.services["billing_service"].create_payer(
            {
                "display_name": "Rodzina Innej Organizacji",
                "contact_phone": "501600702",
                "email": "inna@example.com",
                "payment_identifier": "KONTAKT-002",
            },
            actor_user=self.admin,
            actor="admin",
            organization_id=self.second_organization["organization_id"],
        )
        self.bank_account = self.services["billing_service"].create_bank_account(
            {
                "account_name": "Rachunek kontakt",
                "bank_name": "Bank Kontakt",
                "iban": "PL10111122223333444455556666",
                "currency": "PLN",
            },
            actor_user=self.operator,
            actor="Operator Kontakt",
            organization_id=self.organization["organization_id"],
        )
        self.other_bank_account = self.services["billing_service"].create_bank_account(
            {
                "account_name": "Rachunek innej organizacji",
                "bank_name": "Bank Kontakt 2",
                "iban": "PL20222233334444555566667777",
                "currency": "PLN",
            },
            actor_user=self.admin,
            actor="admin",
            organization_id=self.second_organization["organization_id"],
        )
        self.services["billing_service"].import_statement_csv(
            self.bank_account["billing_bank_account_id"],
            "\n".join(
                [
                    "Data ksiegowania;Kwota;Waluta;Opis;Kontrahent;Rachunek kontrahenta;Referencja",
                    "2026-11-12;228,00;PLN;Wplata kontaktowa;Rodzina Kontaktowa;PL00111122223333444455556666;CONTACT-001",
                ]
            ),
            source_file_name="contact.csv",
            actor_user=self.operator,
            actor="Operator Kontakt",
            organization_id=self.organization["organization_id"],
        )
        self.services["billing_service"].import_statement_csv(
            self.other_bank_account["billing_bank_account_id"],
            "\n".join(
                [
                    "Data ksiegowania;Kwota;Waluta;Opis;Kontrahent;Rachunek kontrahenta;Referencja",
                    "2026-11-13;100,00;PLN;Wplata innej organizacji;Rodzina Innej Organizacji;PL00222233334444555566667777;CONTACT-002",
                ]
            ),
            source_file_name="other-contact.csv",
            actor_user=self.admin,
            actor="admin",
            organization_id=self.second_organization["organization_id"],
        )
        transactions = self.services["billing_service"].list_transactions(
            organization_id=self.organization["organization_id"],
            billing_bank_account_id=self.bank_account["billing_bank_account_id"],
        )
        other_transactions = self.services["billing_service"].list_transactions(
            organization_id=self.second_organization["organization_id"],
            billing_bank_account_id=self.other_bank_account["billing_bank_account_id"],
        )
        self.transaction_id = int(transactions[0]["billing_transaction_id"])
        self.other_transaction_id = int(other_transactions[0]["billing_transaction_id"])
        self.cookie = self._login_default_admin()

    def _contact_event_count(self) -> int:
        with get_connection() as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM billing_contact_events").fetchone()
        return int(row["count"])

    def _ledger_entry_count(self) -> int:
        with get_connection() as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM billing_payer_ledger_entries").fetchone()
        return int(row["count"])

    def _financial_state(self, organization_id: int) -> dict[str, object]:
        return {
            "transactions": self.services["billing_service"].list_transactions(organization_id=organization_id),
            "charges": self.services["billing_service"].list_charges(organization_id=organization_id),
            "matches": self.services["billing_ledger_service"].list_payment_matches(organization_id=organization_id),
            "balances": self.services["billing_ledger_service"].list_balances(organization_id=organization_id),
            "ledger_entries": self._ledger_entry_count(),
        }

    def test_can_add_and_list_contact_events_without_financial_side_effects(self) -> None:
        organization_id = int(self.organization["organization_id"])
        payer_id = int(self.payer["billing_payer_id"])
        financial_before = self._financial_state(organization_id)

        response, payload = self._request(
            "POST",
            f"/api/billing/contact-events?organization_id={organization_id}",
            body=json.dumps(
                {
                    "payer_id": payer_id,
                    "related_payment_id": self.transaction_id,
                    "related_issue_key": f"payment:{self.transaction_id}:payer-only",
                    "channel": "phone",
                    "contact_action": "no_answer",
                    "note_text": " Proba kontaktu bez odpowiedzi. ",
                }
            ),
            headers={"Content-Type": "application/json", "Cookie": self.cookie},
        )
        self.assertEqual(response.status, 201, payload.decode("utf-8"))
        event = json.loads(payload)
        self.assertEqual(int(event["organization_id"]), organization_id)
        self.assertEqual(int(event["billing_payer_id"]), payer_id)
        self.assertEqual(int(event["related_payment_id"]), self.transaction_id)
        self.assertEqual(event["related_issue_key"], f"payment:{self.transaction_id}:payer-only")
        self.assertEqual(event["channel"], "phone")
        self.assertEqual(event["contact_action"], "no_answer")
        self.assertEqual(event["note_text"], "Proba kontaktu bez odpowiedzi.")
        self.assertTrue(event.get("created_by_user_id"))
        self.assertTrue(event.get("created_at"))

        response, payload = self._request(
            "POST",
            f"/api/billing/contact-events?organization_id={organization_id}",
            body=json.dumps(
                {
                    "payer_id": payer_id,
                    "channel": "sms",
                    "contact_action": "draft_prepared",
                    "message_text": "Prosba o sprawdzenie ostatniej wplaty.",
                }
            ),
            headers={"Content-Type": "application/json", "Cookie": self.cookie},
        )
        self.assertEqual(response.status, 201, payload.decode("utf-8"))
        self.assertEqual(json.loads(payload)["message_text"], "Prosba o sprawdzenie ostatniej wplaty.")

        for query in (
            f"organization_id={organization_id}",
            f"organization_id={organization_id}&payer_id={payer_id}",
            f"organization_id={organization_id}&payment_id={self.transaction_id}",
            f"organization_id={organization_id}&issue_key=payment:{self.transaction_id}:payer-only",
        ):
            response, payload = self._request(
                "GET",
                f"/api/billing/contact-events?{query}",
                headers={"Cookie": self.cookie},
            )
            self.assertEqual(response.status, 200, payload.decode("utf-8"))
            data = json.loads(payload)
            self.assertEqual(int(data["organization_id"]), organization_id)
            self.assertTrue(data["events"])

        self.assertEqual(financial_before, self._financial_state(organization_id))

        logs = self.services["event_repository"].list_logs(organization_id=organization_id)
        contact_logs = [item for item in logs if item["event_type"] == "billing_contact_event_added"]
        self.assertTrue(contact_logs)
        parsed_details = []
        for log_item in contact_logs:
            raw_details = log_item.get("details") or {}
            parsed_details.append(json.loads(raw_details) if isinstance(raw_details, str) else raw_details)
        details = next(item for item in parsed_details if item.get("contact_action") == "draft_prepared")
        self.assertNotIn("message_text", details)
        self.assertNotIn("note_text", details)
        self.assertEqual(details.get("contact_action"), "draft_prepared")
        self.assertEqual(details.get("message_length"), len("Prosba o sprawdzenie ostatniej wplaty."))

    def test_rejects_invalid_payloads_without_writing_event(self) -> None:
        organization_id = int(self.organization["organization_id"])
        payer_id = int(self.payer["billing_payer_id"])
        before_count = self._contact_event_count()
        invalid_payloads = (
            {
                "payer_id": payer_id,
                "channel": "fax",
                "contact_action": "contact_logged",
                "note_text": "Niepoprawny kanal.",
            },
            {
                "payer_id": payer_id,
                "channel": "phone",
                "contact_action": "sent",
                "note_text": "Niepoprawny typ.",
            },
            {
                "payer_id": payer_id,
                "channel": "phone",
                "contact_action": "contact_logged",
                "note_text": "Nadmiarowe pole.",
                "role": "admin",
            },
            {
                "payer_id": payer_id,
                "channel": "sms",
                "contact_action": "draft_prepared",
                "note_text": "Brak tresci roboczej.",
            },
            {
                "payer_id": payer_id,
                "channel": "phone",
                "contact_action": "contact_logged",
                "note_text": "x" * 1001,
            },
            {
                "payer_id": payer_id,
                "channel": "email",
                "contact_action": "draft_prepared",
                "message_text": "x" * 2001,
            },
            {
                "payer_id": payer_id,
                "channel": "phone",
                "contact_action": "contact_logged",
                "message_text": " ",
                "note_text": " ",
            },
        )
        for body in invalid_payloads:
            response, payload = self._request(
                "POST",
                f"/api/billing/contact-events?organization_id={organization_id}",
                body=json.dumps(body),
                headers={"Content-Type": "application/json", "Cookie": self.cookie},
            )
            self.assertEqual(response.status, 400, payload.decode("utf-8"))

        self.assertEqual(before_count, self._contact_event_count())

    def test_cross_org_get_and_post_are_blocked(self) -> None:
        organization_id = int(self.organization["organization_id"])
        wrong_organization_id = int(self.second_organization["organization_id"])
        payer_id = int(self.payer["billing_payer_id"])
        other_payer_id = int(self.other_payer["billing_payer_id"])
        before_count = self._contact_event_count()

        response, payload = self._request(
            "POST",
            f"/api/billing/contact-events?organization_id={organization_id}",
            body=json.dumps(
                {
                    "payer_id": other_payer_id,
                    "channel": "phone",
                    "contact_action": "contact_logged",
                    "note_text": "Nie powinna sie zapisac.",
                }
            ),
            headers={"Content-Type": "application/json", "Cookie": self.cookie},
        )
        self.assertEqual(response.status, 404, payload.decode("utf-8"))

        response, payload = self._request(
            "POST",
            f"/api/billing/contact-events?organization_id={organization_id}",
            body=json.dumps(
                {
                    "payer_id": payer_id,
                    "related_payment_id": self.other_transaction_id,
                    "channel": "phone",
                    "contact_action": "contact_logged",
                    "note_text": "Nie powinna sie zapisac.",
                }
            ),
            headers={"Content-Type": "application/json", "Cookie": self.cookie},
        )
        self.assertEqual(response.status, 404, payload.decode("utf-8"))
        self.assertEqual(before_count, self._contact_event_count())

        response, payload = self._request(
            "POST",
            f"/api/billing/contact-events?organization_id={organization_id}",
            body=json.dumps(
                {
                    "payer_id": payer_id,
                    "channel": "phone",
                    "contact_action": "contact_logged",
                    "note_text": "Kontakt w poprawnej organizacji.",
                }
            ),
            headers={"Content-Type": "application/json", "Cookie": self.cookie},
        )
        self.assertEqual(response.status, 201, payload.decode("utf-8"))

        response, payload = self._request(
            "GET",
            f"/api/billing/contact-events?organization_id={wrong_organization_id}",
            headers={"Cookie": self.cookie},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        self.assertEqual(json.loads(payload)["events"], [])

        response, payload = self._request(
            "GET",
            f"/api/billing/contact-events?organization_id={organization_id}&payer_id={other_payer_id}",
            headers={"Cookie": self.cookie},
        )
        self.assertEqual(response.status, 404, payload.decode("utf-8"))


if __name__ == "__main__":
    import unittest

    unittest.main()
