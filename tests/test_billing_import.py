from __future__ import annotations

import unittest

from app.bootstrap import build_services
from app.db import reset_database


class BillingImportTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.services = build_services()
        self.services["auth_service"].ensure_default_admin()
        self.admin = self.services["auth_service"].list_users()[0]
        self.organization = self.services["organization_service"].create_organization(
            {"name": "Klient Rozliczeniowy", "slug": "klient-rozliczeniowy", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        self.operator = self.services["auth_service"].create_user(
            {
                "login": "zosia",
                "display_name": "Zosia",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": self.organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=self.admin["user_id"],
            actor_user=self.admin,
        )

    def test_can_create_bank_account_and_import_statement_csv(self) -> None:
        bank_account = self.services["billing_service"].create_bank_account(
            {
                "account_name": "Rachunek glowny",
                "bank_name": "Przykladowy Bank",
                "iban": "PL12 3456 7890 1111 2222 3333 4444",
                "currency": "PLN",
            },
            actor_user=self.operator,
            actor="Zosia",
            organization_id=self.organization["organization_id"],
        )
        self.assertEqual(bank_account["account_name"], "Rachunek glowny")
        self.assertEqual(bank_account["iban"], "PL12345678901111222233334444")

        import_result = self.services["billing_service"].import_statement_csv(
            bank_account["billing_bank_account_id"],
            "\n".join(
                [
                    "Data ksiegowania;Kwota;Waluta;Opis;Kontrahent;Rachunek kontrahenta;Referencja",
                    "2026-04-08;1500,00;PLN;Oplata za kwiecien;Jan Kowalski;PL00111122223333444455556666;FV/04/2026/01",
                    "2026-04-09;-49,99;PLN;Oplata bankowa;Bank;PL00999988887777666655554444;PROWIZJA",
                ]
            ),
            source_file_name="wyciag_kwiecien.csv",
            actor_user=self.operator,
            actor="Zosia",
            organization_id=self.organization["organization_id"],
        )
        statement_import = import_result["statement_import"]
        self.assertEqual(statement_import["status"], "zaimportowany")
        self.assertEqual(import_result["imported_transaction_count"], 2)
        self.assertEqual(import_result["skipped_transaction_count"], 0)

        transactions = self.services["billing_service"].list_transactions(
            organization_id=self.organization["organization_id"],
            billing_bank_account_id=bank_account["billing_bank_account_id"],
        )
        self.assertEqual(len(transactions), 2)
        self.assertEqual(transactions[0]["direction"], "obciazenie")
        self.assertEqual(transactions[1]["direction"], "uznanie")
        self.assertEqual(transactions[1]["title"], "Oplata za kwiecien")
        self.assertEqual(transactions[1]["matched_status"], "nieprzypisana")

        repeated_import = self.services["billing_service"].import_statement_csv(
            bank_account["billing_bank_account_id"],
            "\n".join(
                [
                    "Data ksiegowania;Kwota;Waluta;Opis;Kontrahent;Rachunek kontrahenta;Referencja",
                    "2026-04-08;1500,00;PLN;Oplata za kwiecien;Jan Kowalski;PL00111122223333444455556666;FV/04/2026/01",
                    "2026-04-09;-49,99;PLN;Oplata bankowa;Bank;PL00999988887777666655554444;PROWIZJA",
                ]
            ),
            source_file_name="wyciag_kwiecien_ponownie.csv",
            actor_user=self.operator,
            actor="Zosia",
            organization_id=self.organization["organization_id"],
        )
        self.assertEqual(repeated_import["imported_transaction_count"], 0)
        self.assertEqual(repeated_import["skipped_transaction_count"], 2)

        logs = self.services["event_repository"].list_logs(organization_id=self.organization["organization_id"])
        self.assertTrue(any(item["event_type"] == "billing_bank_account_created" for item in logs))
        self.assertTrue(any(item["event_type"] == "billing_statement_imported" for item in logs))

    def test_same_iban_can_exist_in_different_organizations(self) -> None:
        second_organization = self.services["organization_service"].create_organization(
            {"name": "Drugi Klient", "slug": "drugi-klient", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        second_operator = self.services["auth_service"].create_user(
            {
                "login": "marta",
                "display_name": "Marta",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": second_organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=self.admin["user_id"],
            actor_user=self.admin,
        )

        first_account = self.services["billing_service"].create_bank_account(
            {
                "account_name": "Rachunek A",
                "iban": "PL55111122223333444455556666",
                "currency": "PLN",
            },
            actor_user=self.operator,
            actor="Zosia",
            organization_id=self.organization["organization_id"],
        )
        second_account = self.services["billing_service"].create_bank_account(
            {
                "account_name": "Rachunek B",
                "iban": "PL55111122223333444455556666",
                "currency": "PLN",
            },
            actor_user=second_operator,
            actor="Marta",
            organization_id=second_organization["organization_id"],
        )

        self.assertNotEqual(first_account["organization_id"], second_account["organization_id"])
        self.assertEqual(first_account["iban"], second_account["iban"])

    def test_latest_family_payment_uses_really_latest_matched_amount(self) -> None:
        bank_account = self.services["billing_service"].create_bank_account(
            {
                "account_name": "Rachunek glowny",
                "iban": "PL55111122223333444455556666",
                "currency": "PLN",
            },
            actor_user=self.operator,
            actor="Zosia",
            organization_id=self.organization["organization_id"],
        )
        school = self.services["billing_service"].create_school(
            {
                "full_name": "Szkola Podstawowa nr 4",
                "short_name": "SP4",
            },
            actor_user=self.operator,
            actor="Zosia",
            organization_id=self.organization["organization_id"],
        )
        payer = self.services["billing_service"].create_payer(
            {
                "display_name": "Rodzina Testowa",
                "contact_phone": "500-600-700",
            },
            actor_user=self.operator,
            actor="Zosia",
            organization_id=self.organization["organization_id"],
        )
        model = self.services["billing_service"].create_model(
            {
                "name": "26/27 Wtorek",
                "school_year": "2026/2027",
                "lesson_day": "wtorek",
                "settlement_mode": "monthly",
                "monthly_rate_amount": 57,
                "semester_rate_amount": 54,
            },
            actor_user=self.operator,
            actor="Zosia",
            organization_id=self.organization["organization_id"],
        )
        self.services["billing_service"].create_student(
            {
                "full_name": "Lena Testowa",
                "billing_payer_id": payer["billing_payer_id"],
                "billing_school_id": school["billing_school_id"],
                "billing_model_id": model["billing_model_id"],
                "lesson_day": "wtorek",
            },
            actor_user=self.operator,
            actor="Zosia",
            organization_id=self.organization["organization_id"],
        )
        self.services["billing_service"].generate_charges_for_model(
            {
                "billing_model_id": model["billing_model_id"],
                "period_label": "Pazdziernik 2026",
                "due_date": "2026-10-10",
                "lesson_count": 4,
            },
            actor_user=self.operator,
            actor="Zosia",
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
            actor="Zosia",
            organization_id=self.organization["organization_id"],
        )

        self.services["billing_service"].import_statement_csv(
            bank_account["billing_bank_account_id"],
            "\n".join(
                [
                    "Data ksiegowania;Kwota;Waluta;Opis;Kontrahent;Rachunek kontrahenta;Referencja",
                    "2026-10-11;171,00;PLN;500600700 rata pazdziernik;Rodzic;PL00111122223333444455556666;RATA-01",
                    "2026-11-12;57,00;PLN;500600700 doplata listopad;Rodzic;PL00111122223333444455556666;RATA-02",
                ]
            ),
            source_file_name="rodzina_testowa.csv",
            actor_user=self.operator,
            actor="Zosia",
            organization_id=self.organization["organization_id"],
        )

        payers = self.services["billing_service"].list_payers(organization_id=self.organization["organization_id"])
        self.assertEqual(len(payers), 1)
        self.assertEqual(payers[0]["billing_last_payment_at"], "2026-11-12")
        self.assertEqual(payers[0]["billing_last_payment_amount"], 57.0)
        self.assertEqual(payers[0]["latest_payment_amount"], 57.0)

        students = self.services["billing_service"].list_students(organization_id=self.organization["organization_id"])
        self.assertEqual(len(students), 1)
        self.assertEqual(students[0]["family_last_payment_date"], "2026-11-12")
        self.assertEqual(students[0]["family_last_payment_amount"], 57.0)


if __name__ == "__main__":
    unittest.main()
