from __future__ import annotations

import json

from tests.http_server_support import HttpServerTestCase


class BillingPayerNotesHttpTests(HttpServerTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.admin = self.services["auth_service"].list_users()[0]
        self.organization = self.services["organization_service"].create_organization(
            {"name": "Misja Testowa", "slug": "misja-testowa", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        self.second_organization = self.services["organization_service"].create_organization(
            {"name": "Druga Organizacja", "slug": "druga-organizacja", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        self.payer = self.services["billing_service"].create_payer(
            {
                "display_name": "Rodzina Notatkowa",
                "contact_phone": "500600701",
                "email": "notatki@example.com",
            },
            actor_user=self.admin,
            actor="admin",
            organization_id=self.organization["organization_id"],
        )
        self.other_payer = self.services["billing_service"].create_payer(
            {
                "display_name": "Rodzina Innej Organizacji",
                "contact_phone": "500600702",
                "email": "inna@example.com",
            },
            actor_user=self.admin,
            actor="admin",
            organization_id=self.second_organization["organization_id"],
        )
        self.cookie = self._login_default_admin()

    def test_can_add_and_list_billing_payer_note_without_financial_side_effects(self) -> None:
        organization_id = int(self.organization["organization_id"])
        payer_id = int(self.payer["billing_payer_id"])
        balances_before = self.services["billing_ledger_service"].list_balances(organization_id=organization_id)
        matches_before = self.services["billing_ledger_service"].list_payment_matches(organization_id=organization_id)
        charges_before = self.services["billing_service"].list_charges(organization_id=organization_id)
        transactions_before = self.services["billing_service"].list_transactions(organization_id=organization_id)

        response, payload = self._request(
            "POST",
            f"/api/billing/payers/{payer_id}/notes?organization_id={organization_id}",
            body=json.dumps({"note_text": " Rodzic zaplaci do piatku. "}),
            headers={"Content-Type": "application/json", "Cookie": self.cookie},
        )

        self.assertEqual(response.status, 201, payload.decode("utf-8"))
        note = json.loads(payload)
        self.assertEqual(note["note_text"], "Rodzic zaplaci do piatku.")
        self.assertEqual(int(note["organization_id"]), organization_id)
        self.assertEqual(int(note["billing_payer_id"]), payer_id)
        self.assertEqual(note["note_type"], "operator_note")
        self.assertTrue(note.get("author_user_id"))
        self.assertTrue(note.get("created_at"))

        response, payload = self._request(
            "GET",
            f"/api/billing/payers/{payer_id}/notes?organization_id={organization_id}",
            headers={"Cookie": self.cookie},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        notes = json.loads(payload)
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0]["note_text"], "Rodzic zaplaci do piatku.")

        self.assertEqual(
            balances_before,
            self.services["billing_ledger_service"].list_balances(organization_id=organization_id),
        )
        self.assertEqual(
            matches_before,
            self.services["billing_ledger_service"].list_payment_matches(organization_id=organization_id),
        )
        self.assertEqual(charges_before, self.services["billing_service"].list_charges(organization_id=organization_id))
        self.assertEqual(
            transactions_before,
            self.services["billing_service"].list_transactions(organization_id=organization_id),
        )

        logs = self.services["event_repository"].list_logs(organization_id=organization_id)
        note_events = [item for item in logs if item["event_type"] == "billing_payer_note_added"]
        self.assertTrue(note_events)
        raw_details = note_events[-1].get("details") or {}
        details = json.loads(raw_details) if isinstance(raw_details, str) else raw_details
        self.assertNotIn("note_text", details)
        self.assertEqual(details.get("note_length"), len("Rodzic zaplaci do piatku."))

    def test_rejects_invalid_billing_payer_note_payloads(self) -> None:
        organization_id = int(self.organization["organization_id"])
        payer_id = int(self.payer["billing_payer_id"])

        for body in (
            {"note_text": ""},
            {"note_text": "   "},
            {"note_text": "x" * 2001},
            {"note_text": "Poprawna tresc.", "role": "admin"},
        ):
            response, payload = self._request(
                "POST",
                f"/api/billing/payers/{payer_id}/notes?organization_id={organization_id}",
                body=json.dumps(body),
                headers={"Content-Type": "application/json", "Cookie": self.cookie},
            )
            self.assertEqual(response.status, 400, payload.decode("utf-8"))

        response, payload = self._request(
            "GET",
            f"/api/billing/payers/{payer_id}/notes?organization_id={organization_id}",
            headers={"Cookie": self.cookie},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        self.assertEqual(json.loads(payload), [])

    def test_cannot_add_note_to_payer_from_another_organization_scope(self) -> None:
        organization_id = int(self.organization["organization_id"])
        other_payer_id = int(self.other_payer["billing_payer_id"])

        response, payload = self._request(
            "POST",
            f"/api/billing/payers/{other_payer_id}/notes?organization_id={organization_id}",
            body=json.dumps({"note_text": "Nie powinna sie zapisac."}),
            headers={"Content-Type": "application/json", "Cookie": self.cookie},
        )

        self.assertEqual(response.status, 404, payload.decode("utf-8"))
        notes = self.services["billing_service"].list_payer_notes(
            other_payer_id,
            organization_id=int(self.second_organization["organization_id"]),
        )
        self.assertEqual(notes, [])
