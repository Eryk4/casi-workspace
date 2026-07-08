from __future__ import annotations

import json

from app.db import get_connection
from tests.http_server_support import HttpServerTestCase


class BillingWorkQueueEventsHttpTests(HttpServerTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.admin = self.services["auth_service"].list_users()[0]
        self.organization = self.services["organization_service"].create_organization(
            {"name": "Misja Work Queue", "slug": "misja-work-queue", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        self.second_organization = self.services["organization_service"].create_organization(
            {"name": "CASI Work Queue", "slug": "casi-work-queue", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        self.operator = self.services["auth_service"].create_user(
            {
                "login": "work-queue-operator",
                "display_name": "Operator Work Queue",
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
                "display_name": "Rodzina Work Queue",
                "contact_phone": "501600700",
                "payment_identifier": "501600700",
            },
            actor_user=self.operator,
            actor="Operator Work Queue",
            organization_id=self.organization["organization_id"],
        )
        self.bank_account = self.services["billing_service"].create_bank_account(
            {
                "account_name": "Rachunek work queue",
                "bank_name": "Bank Work Queue",
                "iban": "PL10111122223333444455556666",
                "currency": "PLN",
            },
            actor_user=self.operator,
            actor="Operator Work Queue",
            organization_id=self.organization["organization_id"],
        )
        self.services["billing_service"].import_statement_csv(
            self.bank_account["billing_bank_account_id"],
            "\n".join(
                [
                    "Data ksiegowania;Kwota;Waluta;Opis;Kontrahent;Rachunek kontrahenta;Referencja",
                    "2026-11-12;228,00;PLN;Wplata do sprawy;Rodzina Work Queue;PL00111122223333444455556666;WQ-001",
                ]
            ),
            source_file_name="work-queue.csv",
            actor_user=self.operator,
            actor="Operator Work Queue",
            organization_id=self.organization["organization_id"],
        )
        transactions = self.services["billing_service"].list_transactions(
            organization_id=self.organization["organization_id"],
            billing_bank_account_id=self.bank_account["billing_bank_account_id"],
        )
        self.transaction_id = int(transactions[0]["billing_transaction_id"])
        self.cookie = self._login_default_admin()

    def _work_queue_event_count(self) -> int:
        with get_connection() as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM billing_work_queue_events").fetchone()
        return int(row["count"])

    def _financial_state(self, organization_id: int) -> dict[str, object]:
        return {
            "transactions": self.services["billing_service"].list_transactions(organization_id=organization_id),
            "charges": self.services["billing_service"].list_charges(organization_id=organization_id),
            "matches": self.services["billing_ledger_service"].list_payment_matches(organization_id=organization_id),
            "balances": self.services["billing_ledger_service"].list_balances(organization_id=organization_id),
            "ledger_entries": self._ledger_entry_count(),
        }

    def _ledger_entry_count(self) -> int:
        with get_connection() as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM billing_payer_ledger_entries").fetchone()
        return int(row["count"])

    def test_can_add_handled_and_snoozed_events_without_financial_side_effects(self) -> None:
        organization_id = int(self.organization["organization_id"])
        financial_before = self._financial_state(organization_id)

        handled_response, handled_payload = self._request(
            "POST",
            f"/api/billing/work-queue/events?organization_id={organization_id}",
            body=json.dumps(
                {
                    "issue_key": f"payment:{self.transaction_id}:manual-review",
                    "issue_type": "Wpłata do wyjaśnienia",
                    "target_type": "payment",
                    "target_id": self.transaction_id,
                    "action": "handled",
                    "note_text": " Sprawdzone telefonicznie. ",
                }
            ),
            headers={"Content-Type": "application/json", "Cookie": self.cookie},
        )
        self.assertEqual(handled_response.status, 201, handled_payload.decode("utf-8"))
        handled = json.loads(handled_payload)
        self.assertEqual(handled["action"], "handled")
        self.assertEqual(handled["note_text"], "Sprawdzone telefonicznie.")
        self.assertEqual(int(handled["organization_id"]), organization_id)
        self.assertEqual(int(handled["target_id"]), self.transaction_id)
        self.assertTrue(handled.get("created_by_user_id"))

        snoozed_response, snoozed_payload = self._request(
            "POST",
            f"/api/billing/work-queue/events?organization_id={organization_id}",
            body=json.dumps(
                {
                    "issue_key": f"payer:{self.payer['billing_payer_id']}:debt",
                    "issue_type": "Czeka na wpłatę",
                    "target_type": "payer",
                    "target_id": self.payer["billing_payer_id"],
                    "action": "snoozed",
                }
            ),
            headers={"Content-Type": "application/json", "Cookie": self.cookie},
        )
        self.assertEqual(snoozed_response.status, 201, snoozed_payload.decode("utf-8"))
        self.assertEqual(json.loads(snoozed_payload)["action"], "snoozed")

        response, payload = self._request(
            "GET",
            f"/api/billing/work-queue/events?organization_id={organization_id}",
            headers={"Cookie": self.cookie},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        data = json.loads(payload)
        self.assertEqual(int(data["organization_id"]), organization_id)
        self.assertEqual(len(data["events"]), 2)
        self.assertEqual({item["action"] for item in data["events"]}, {"handled", "snoozed"})

        self.assertEqual(financial_before, self._financial_state(organization_id))

        logs = self.services["event_repository"].list_logs(organization_id=organization_id)
        work_queue_logs = [item for item in logs if item["event_type"] == "billing_work_queue_event_added"]
        self.assertTrue(work_queue_logs)
        raw_details = work_queue_logs[-1].get("details") or {}
        details = json.loads(raw_details) if isinstance(raw_details, str) else raw_details
        self.assertNotIn("note_text", details)
        self.assertIn(details.get("action"), {"handled", "snoozed"})

    def test_rejects_invalid_payloads_without_writing_event(self) -> None:
        organization_id = int(self.organization["organization_id"])
        before_count = self._work_queue_event_count()
        invalid_payloads = (
            {
                "issue_key": "bad-action",
                "issue_type": "Wpłata do wyjaśnienia",
                "target_type": "payment",
                "target_id": self.transaction_id,
                "action": "settled",
            },
            {
                "issue_key": "bad-target",
                "issue_type": "Wpłata do wyjaśnienia",
                "target_type": "invoice",
                "target_id": self.transaction_id,
                "action": "handled",
            },
            {
                "issue_key": "extra-field",
                "issue_type": "Wpłata do wyjaśnienia",
                "target_type": "payment",
                "target_id": self.transaction_id,
                "action": "handled",
                "role": "admin",
            },
            {
                "issue_key": "long-note",
                "issue_type": "Wpłata do wyjaśnienia",
                "target_type": "payment",
                "target_id": self.transaction_id,
                "action": "handled",
                "note_text": "x" * 1001,
            },
        )
        for body in invalid_payloads:
            response, payload = self._request(
                "POST",
                f"/api/billing/work-queue/events?organization_id={organization_id}",
                body=json.dumps(body),
                headers={"Content-Type": "application/json", "Cookie": self.cookie},
            )
            self.assertEqual(response.status, 400, payload.decode("utf-8"))

        self.assertEqual(before_count, self._work_queue_event_count())

    def test_cross_org_get_and_post_are_blocked_for_verifiable_targets(self) -> None:
        organization_id = int(self.organization["organization_id"])
        wrong_organization_id = int(self.second_organization["organization_id"])
        before_count = self._work_queue_event_count()

        response, payload = self._request(
            "POST",
            f"/api/billing/work-queue/events?organization_id={wrong_organization_id}",
            body=json.dumps(
                {
                    "issue_key": f"payment:{self.transaction_id}:cross-org",
                    "issue_type": "Wpłata do wyjaśnienia",
                    "target_type": "payment",
                    "target_id": self.transaction_id,
                    "action": "handled",
                    "note_text": "Nie powinna sie zapisac.",
                }
            ),
            headers={"Content-Type": "application/json", "Cookie": self.cookie},
        )
        self.assertEqual(response.status, 404, payload.decode("utf-8"))
        self.assertEqual(before_count, self._work_queue_event_count())

        response, payload = self._request(
            "GET",
            f"/api/billing/work-queue/events?organization_id={wrong_organization_id}",
            headers={"Cookie": self.cookie},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        self.assertEqual(json.loads(payload)["events"], [])


if __name__ == "__main__":
    import unittest

    unittest.main()
