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

    def _overview_read_state(self) -> dict[str, int]:
        table_names = (
            "billing_transactions",
            "billing_charges",
            "billing_payment_matches",
            "billing_payer_ledger_entries",
            "billing_next_step_events",
            "event_logs",
        )
        with get_connection() as connection:
            return {
                table_name: int(connection.execute(f"SELECT COUNT(*) AS count FROM {table_name}").fetchone()["count"])
                for table_name in table_names
            }

    def test_active_overview_is_parent_linked_org_scoped_tolerant_and_read_only(self) -> None:
        organization_id = int(self.organization["organization_id"])
        other_organization_id = int(self.second_organization["organization_id"])

        def add(payload: dict[str, object], *, scoped_organization_id: int = organization_id) -> dict[str, object]:
            return self.services["billing_service"].add_next_step_event(
                payload,
                actor_user=self.admin,
                actor="admin",
                organization_id=scoped_organization_id,
            )

        payer_event = add(
            {
                "target_type": "payer",
                "target_id": self.payer["billing_payer_id"],
                "step_type": "call",
                "event_action": "planned",
                "title": "Aktywny platnik",
                "planned_for": "2026-12-18",
            }
        )
        payment_event = add(
            {
                "target_type": "payment",
                "target_id": self.transaction_id,
                "step_type": "check_payment",
                "event_action": "planned",
                "title": "Aktywna wplata",
            }
        )
        issue_event = add(
            {
                "target_type": "work_queue_issue",
                "related_issue_key": "overview:issue:1",
                "step_type": "clarify_payment",
                "event_action": "planned",
                "title": "Aktywna sprawa",
            }
        )
        summary_event = add(
            {
                "target_type": "billing_summary",
                "step_type": "review_notes",
                "event_action": "planned",
                "title": "Aktywne podsumowanie",
            }
        )
        duplicate_payload = {
            "target_type": "billing_summary",
            "step_type": "other",
            "event_action": "planned",
            "title": "Identyczny krok",
            "planned_for": "2026-12-22",
        }
        first_duplicate = add(duplicate_payload)
        second_duplicate = add(duplicate_payload)

        response, payload = self._request(
            "GET",
            f"/api/billing/next-step-events/active?organization_id={organization_id}",
            headers={"Cookie": self.cookie},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        duplicate_ids = {
            int(item["billing_next_step_event_id"])
            for item in json.loads(payload)["events"]
            if item["title"] == "Identyczny krok"
        }
        self.assertEqual(
            duplicate_ids,
            {
                int(first_duplicate["billing_next_step_event_id"]),
                int(second_duplicate["billing_next_step_event_id"]),
            },
        )

        add(
            {
                "parent_event_id": first_duplicate["billing_next_step_event_id"],
                "target_type": "billing_summary",
                "step_type": "other",
                "event_action": "completed",
                "title": "Identyczny krok",
                "planned_for": "2026-12-22",
            }
        )
        repository = self.services["billing_service"].billing_repository
        repository.add_next_step_event(
            {
                "organization_id": organization_id,
                "target_type": "billing_summary",
                "step_type": "other",
                "event_action": "completed",
                "title": "Historyczny completed bez rodzica",
                "created_by_user_id": self.admin["user_id"],
            }
        )
        missing_target_id = repository.add_next_step_event(
            {
                "organization_id": organization_id,
                "target_type": "payer",
                "target_id": 987654321,
                "step_type": "call",
                "event_action": "planned",
                "title": "Historyczny brakujacy platnik",
                "created_by_user_id": self.admin["user_id"],
            }
        )
        unknown_target_id = repository.add_next_step_event(
            {
                "organization_id": organization_id,
                "target_type": "future_target",
                "target_id": 123456789,
                "step_type": "other",
                "event_action": "planned",
                "title": "Historyczny nieznany cel",
                "created_by_user_id": self.admin["user_id"],
            }
        )
        foreign_event = add(
            {
                "target_type": "billing_summary",
                "step_type": "review_notes",
                "event_action": "planned",
                "title": "Krok innej organizacji",
            },
            scoped_organization_id=other_organization_id,
        )

        read_state_before = self._overview_read_state()
        response, payload = self._request(
            "GET",
            f"/api/billing/next-step-events/active?organization_id={organization_id}&limit=2000",
            headers={"Cookie": self.cookie},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        data = json.loads(payload)
        self.assertEqual(int(data["organization_id"]), organization_id)
        events = data["events"]
        ids = {int(item["billing_next_step_event_id"]) for item in events}
        self.assertIn(int(payer_event["billing_next_step_event_id"]), ids)
        self.assertIn(int(payment_event["billing_next_step_event_id"]), ids)
        self.assertIn(int(issue_event["billing_next_step_event_id"]), ids)
        self.assertIn(int(summary_event["billing_next_step_event_id"]), ids)
        self.assertNotIn(int(first_duplicate["billing_next_step_event_id"]), ids)
        self.assertIn(int(second_duplicate["billing_next_step_event_id"]), ids)
        self.assertIn(missing_target_id, ids)
        self.assertIn(unknown_target_id, ids)
        self.assertNotIn(int(foreign_event["billing_next_step_event_id"]), ids)
        self.assertEqual({item["event_action"] for item in events}, {"planned"})
        self.assertEqual(read_state_before, self._overview_read_state())

        response, payload = self._request(
            "GET",
            f"/api/billing/next-step-events/active?organization_id={other_organization_id}",
            headers={"Cookie": self.cookie},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        foreign_events = json.loads(payload)["events"]
        self.assertEqual(
            {int(item["billing_next_step_event_id"]) for item in foreign_events},
            {int(foreign_event["billing_next_step_event_id"])},
        )

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
        financial_before = self._financial_state(organization_id)
        response, payload = self._request(
            "POST",
            f"/api/billing/next-step-events?organization_id={organization_id}",
            body=json.dumps(
                {
                    "target_type": "payer",
                    "target_id": self.payer["billing_payer_id"],
                    "step_type": "wait_for_response",
                    "event_action": "planned",
                    "title": "Krok do zakonczenia",
                }
            ),
            headers={"Content-Type": "application/json", "Cookie": self.cookie},
        )
        self.assertEqual(response.status, 201, payload.decode("utf-8"))
        planned_event = json.loads(payload)

        response, payload = self._request(
            "POST",
            f"/api/billing/next-step-events?organization_id={organization_id}",
            body=json.dumps(
                {
                    "parent_event_id": planned_event["billing_next_step_event_id"],
                    "target_type": "payer",
                    "target_id": self.payer["billing_payer_id"],
                    "step_type": "wait_for_response",
                    "event_action": "completed",
                    "title": "Krok do zakonczenia",
                }
            ),
            headers={"Content-Type": "application/json", "Cookie": self.cookie},
        )
        self.assertEqual(response.status, 201, payload.decode("utf-8"))
        completed_event = json.loads(payload)
        self.assertEqual(completed_event["event_action"], "completed")
        self.assertEqual(
            int(completed_event["parent_event_id"]),
            int(planned_event["billing_next_step_event_id"]),
        )

        response, payload = self._request(
            "POST",
            f"/api/billing/next-step-events?organization_id={organization_id}",
            body=json.dumps(
                {
                    "target_type": "payer",
                    "target_id": self.payer["billing_payer_id"],
                    "step_type": "wait_for_response",
                    "event_action": "snoozed",
                    "title": "Historyczny krok snoozed",
                }
            ),
            headers={"Content-Type": "application/json", "Cookie": self.cookie},
        )
        self.assertEqual(response.status, 201, payload.decode("utf-8"))
        self.assertEqual(json.loads(payload)["event_action"], "snoozed")
        self.assertEqual(self._next_step_count(), 3)
        self.assertEqual(financial_before, self._financial_state(organization_id))

        logs = self.services["event_repository"].list_logs(organization_id=organization_id)
        completion_logs = [item for item in logs if item["event_type"] == "billing_next_step_event_added"]
        completion_details = [
            json.loads(item.get("details") or "{}") if isinstance(item.get("details"), str) else (item.get("details") or {})
            for item in completion_logs
        ]
        self.assertTrue(
            any(
                details.get("event_action") == "completed"
                and int(details.get("parent_event_id") or 0) == int(planned_event["billing_next_step_event_id"])
                and "note_text" not in details
                for details in completion_details
            )
        )

    def test_rejects_invalid_completed_parent_relationships_without_extra_writes(self) -> None:
        organization_id = int(self.organization["organization_id"])
        base = {
            "target_type": "payer",
            "target_id": self.payer["billing_payer_id"],
            "step_type": "call",
            "event_action": "planned",
            "title": "Jednoznaczny krok",
        }
        response, payload = self._request(
            "POST",
            f"/api/billing/next-step-events?organization_id={organization_id}",
            body=json.dumps(base),
            headers={"Content-Type": "application/json", "Cookie": self.cookie},
        )
        self.assertEqual(response.status, 201, payload.decode("utf-8"))
        planned_event_id = int(json.loads(payload)["billing_next_step_event_id"])

        completed = {**base, "event_action": "completed"}
        invalid_requests = (
            (completed, 400),
            ({**completed, "parent_event_id": 999999}, 404),
            (
                {
                    **completed,
                    "parent_event_id": planned_event_id,
                    "target_type": "payment",
                    "target_id": self.transaction_id,
                },
                400,
            ),
            ({**base, "parent_event_id": planned_event_id}, 400),
        )
        for body, expected_status in invalid_requests:
            response, payload = self._request(
                "POST",
                f"/api/billing/next-step-events?organization_id={organization_id}",
                body=json.dumps(body),
                headers={"Content-Type": "application/json", "Cookie": self.cookie},
            )
            self.assertEqual(response.status, expected_status, payload.decode("utf-8"))

        valid_completed = {**completed, "parent_event_id": planned_event_id}
        response, payload = self._request(
            "POST",
            f"/api/billing/next-step-events?organization_id={organization_id}",
            body=json.dumps(valid_completed),
            headers={"Content-Type": "application/json", "Cookie": self.cookie},
        )
        self.assertEqual(response.status, 201, payload.decode("utf-8"))
        completed_event_id = int(json.loads(payload)["billing_next_step_event_id"])

        for body in (
            valid_completed,
            {**completed, "parent_event_id": completed_event_id},
        ):
            response, payload = self._request(
                "POST",
                f"/api/billing/next-step-events?organization_id={organization_id}",
                body=json.dumps(body),
                headers={"Content-Type": "application/json", "Cookie": self.cookie},
            )
            self.assertEqual(response.status, 400, payload.decode("utf-8"))
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
        local_planned_event_id = int(json.loads(payload)["billing_next_step_event_id"])

        response, payload = self._request(
            "POST",
            f"/api/billing/next-step-events?organization_id={wrong_organization_id}",
            body=json.dumps(
                {
                    "parent_event_id": local_planned_event_id,
                    "target_type": "payer",
                    "target_id": self.other_payer["billing_payer_id"],
                    "step_type": "call",
                    "event_action": "completed",
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
