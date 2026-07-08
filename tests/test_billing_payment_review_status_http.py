from __future__ import annotations

import json

from app.db import get_connection
from tests.http_server_support import HttpServerTestCase


class BillingPaymentReviewStatusHttpTests(HttpServerTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.admin = self.services["auth_service"].list_users()[0]
        self.organization = self.services["organization_service"].create_organization(
            {"name": "Misja Review", "slug": "misja-review", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        self.second_organization = self.services["organization_service"].create_organization(
            {"name": "CASI Review", "slug": "casi-review", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        self.operator = self.services["auth_service"].create_user(
            {
                "login": "review-operator",
                "display_name": "Operator Review",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": self.organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=self.admin["user_id"],
            actor_user=self.admin,
        )
        self.bank_account = self.services["billing_service"].create_bank_account(
            {
                "account_name": "Rachunek review",
                "bank_name": "Bank Review",
                "iban": "PL10111122223333444455556666",
                "currency": "PLN",
            },
            actor_user=self.operator,
            actor="Operator Review",
            organization_id=self.organization["organization_id"],
        )
        self.services["billing_service"].import_statement_csv(
            self.bank_account["billing_bank_account_id"],
            "\n".join(
                [
                    "Data ksiegowania;Kwota;Waluta;Opis;Kontrahent;Rachunek kontrahenta;Referencja",
                    "2026-11-12;228,00;PLN;Wplata do sprawdzenia;Rodzina Review;PL00111122223333444455556666;REVIEW-001",
                ]
            ),
            source_file_name="review.csv",
            actor_user=self.operator,
            actor="Operator Review",
            organization_id=self.organization["organization_id"],
        )
        transactions = self.services["billing_service"].list_transactions(
            organization_id=self.organization["organization_id"],
            billing_bank_account_id=self.bank_account["billing_bank_account_id"],
        )
        self.transaction_id = int(transactions[0]["billing_transaction_id"])
        self.cookie = self._login_default_admin()

    def _review_event_count(self) -> int:
        with get_connection() as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM billing_payment_review_events").fetchone()
        return int(row["count"])

    def _ledger_entry_count(self) -> int:
        with get_connection() as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM billing_payer_ledger_entries").fetchone()
        return int(row["count"])

    def test_can_add_and_get_payment_review_status_without_financial_side_effects(self) -> None:
        organization_id = int(self.organization["organization_id"])
        transactions_before = self.services["billing_service"].list_transactions(organization_id=organization_id)
        matches_before = self.services["billing_ledger_service"].list_payment_matches(organization_id=organization_id)
        charges_before = self.services["billing_service"].list_charges(organization_id=organization_id)
        balances_before = self.services["billing_ledger_service"].list_balances(organization_id=organization_id)
        ledger_entries_before = self._ledger_entry_count()

        response, payload = self._request(
            "POST",
            f"/api/billing/payments/{self.transaction_id}/review-status?organization_id={organization_id}",
            body=json.dumps({"status": "needs_review", "note_text": " Sprawdzic tytul wplaty. "}),
            headers={"Content-Type": "application/json", "Cookie": self.cookie},
        )

        self.assertEqual(response.status, 201, payload.decode("utf-8"))
        created = json.loads(payload)
        self.assertEqual(created["status"], "needs_review")
        self.assertEqual(created["note_text"], "Sprawdzic tytul wplaty.")
        self.assertEqual(int(created["organization_id"]), organization_id)
        self.assertEqual(int(created["billing_transaction_id"]), self.transaction_id)
        self.assertTrue(created.get("created_by_user_id"))
        self.assertTrue(created.get("created_at"))

        response, payload = self._request(
            "GET",
            f"/api/billing/payments/{self.transaction_id}/review-status?organization_id={organization_id}",
            headers={"Cookie": self.cookie},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        review_status = json.loads(payload)
        self.assertEqual(review_status["current"]["status"], "needs_review")
        self.assertEqual(review_status["current"]["note_text"], "Sprawdzic tytul wplaty.")
        self.assertEqual(len(review_status["history"]), 1)

        self.assertEqual(transactions_before, self.services["billing_service"].list_transactions(organization_id=organization_id))
        self.assertEqual(matches_before, self.services["billing_ledger_service"].list_payment_matches(organization_id=organization_id))
        self.assertEqual(charges_before, self.services["billing_service"].list_charges(organization_id=organization_id))
        self.assertEqual(balances_before, self.services["billing_ledger_service"].list_balances(organization_id=organization_id))
        self.assertEqual(ledger_entries_before, self._ledger_entry_count())

        logs = self.services["event_repository"].list_logs(organization_id=organization_id)
        review_events = [item for item in logs if item["event_type"] == "billing_payment_review_status_changed"]
        self.assertTrue(review_events)
        raw_details = review_events[-1].get("details") or {}
        details = json.loads(raw_details) if isinstance(raw_details, str) else raw_details
        self.assertNotIn("note_text", details)
        self.assertEqual(details.get("status"), "needs_review")
        self.assertEqual(details.get("note_length"), len("Sprawdzic tytul wplaty."))

    def test_rejects_invalid_payment_review_payloads_without_writing_event(self) -> None:
        organization_id = int(self.organization["organization_id"])
        before_count = self._review_event_count()

        invalid_payloads = (
            {"status": "settled"},
            {"status": "needs_review", "role": "admin"},
            {"status": "needs_review", "note_text": "x" * 1001},
        )
        for body in invalid_payloads:
            response, payload = self._request(
                "POST",
                f"/api/billing/payments/{self.transaction_id}/review-status?organization_id={organization_id}",
                body=json.dumps(body),
                headers={"Content-Type": "application/json", "Cookie": self.cookie},
            )
            self.assertEqual(response.status, 400, payload.decode("utf-8"))

        self.assertEqual(before_count, self._review_event_count())

    def test_cross_org_get_and_post_are_blocked(self) -> None:
        organization_id = int(self.organization["organization_id"])
        wrong_organization_id = int(self.second_organization["organization_id"])
        before_count = self._review_event_count()

        response, payload = self._request(
            "GET",
            f"/api/billing/payments/{self.transaction_id}/review-status?organization_id={wrong_organization_id}",
            headers={"Cookie": self.cookie},
        )
        self.assertEqual(response.status, 404, payload.decode("utf-8"))

        response, payload = self._request(
            "POST",
            f"/api/billing/payments/{self.transaction_id}/review-status?organization_id={wrong_organization_id}",
            body=json.dumps({"status": "checked", "note_text": "Nie powinna sie zapisac."}),
            headers={"Content-Type": "application/json", "Cookie": self.cookie},
        )
        self.assertEqual(response.status, 404, payload.decode("utf-8"))
        self.assertEqual(before_count, self._review_event_count())

        response, payload = self._request(
            "GET",
            f"/api/billing/payments/{self.transaction_id}/review-status?organization_id={organization_id}",
            headers={"Cookie": self.cookie},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        self.assertIsNone(json.loads(payload)["current"])

    def test_list_payment_review_statuses_is_organization_scoped_and_read_only(self) -> None:
        organization_id = int(self.organization["organization_id"])
        wrong_organization_id = int(self.second_organization["organization_id"])
        financial_counts_before = {
            "transactions": len(self.services["billing_service"].list_transactions(organization_id=organization_id)),
            "matches": len(self.services["billing_ledger_service"].list_payment_matches(organization_id=organization_id)),
            "charges": len(self.services["billing_service"].list_charges(organization_id=organization_id)),
            "ledger_entries": self._ledger_entry_count(),
        }

        response, payload = self._request(
            "POST",
            f"/api/billing/payments/{self.transaction_id}/review-status?organization_id={organization_id}",
            body=json.dumps({"status": "waiting_for_contact", "note_text": "Sprawdzic kontakt z platnikiem."}),
            headers={"Content-Type": "application/json", "Cookie": self.cookie},
        )
        self.assertEqual(response.status, 201, payload.decode("utf-8"))

        response, payload = self._request(
            "GET",
            f"/api/billing/payment-review-statuses?organization_id={organization_id}",
            headers={"Cookie": self.cookie},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        data = json.loads(payload)
        self.assertEqual(int(data["organization_id"]), organization_id)
        self.assertEqual(len(data["statuses"]), 1)
        self.assertEqual(data["statuses"][0]["status"], "waiting_for_contact")
        self.assertEqual(int(data["statuses"][0]["billing_transaction_id"]), self.transaction_id)

        response, payload = self._request(
            "GET",
            f"/api/billing/payment-review-statuses?organization_id={wrong_organization_id}",
            headers={"Cookie": self.cookie},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        wrong_data = json.loads(payload)
        self.assertEqual(int(wrong_data["organization_id"]), wrong_organization_id)
        self.assertEqual(wrong_data["statuses"], [])

        self.assertEqual(
            financial_counts_before,
            {
                "transactions": len(self.services["billing_service"].list_transactions(organization_id=organization_id)),
                "matches": len(self.services["billing_ledger_service"].list_payment_matches(organization_id=organization_id)),
                "charges": len(self.services["billing_service"].list_charges(organization_id=organization_id)),
                "ledger_entries": self._ledger_entry_count(),
            },
        )


if __name__ == "__main__":
    import unittest

    unittest.main()
