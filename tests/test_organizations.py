from __future__ import annotations

import unittest

from app.bootstrap import build_services
from app.db import reset_database
from app.services.organization_service import OrganizationError


class OrganizationTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.services = build_services()
        self.auth_service = self.services["auth_service"]
        self.invoice_service = self.services["invoice_service"]
        self.organization_service = self.services["organization_service"]
        self.auth_service.ensure_default_admin()
        self.admin = self.auth_service.list_users()[0]

    def test_same_invoice_can_exist_in_two_organizations_without_cross_org_duplicate(self) -> None:
        druga_organizacja = self.organization_service.create_organization(
            {"name": "Klient Beta", "slug": "klient-beta", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )

        payload = {
            "incoming_date": "2026-04-08",
            "source": "EMAIL",
            "file_name": "faktura_wspolna.pdf",
            "document_type": "pdf",
            "invoice_number": "FV/100/04/2026",
            "issuer_nip": "1234567890",
            "issuer_name": "Biuro Serwis Sp. z o.o.",
            "issue_date": "2026-04-08",
            "sale_date": "2026-04-08",
            "gross_amount": 120.0,
            "currency": "PLN",
            "status": "nowa",
        }

        faktura_domyslna = self.invoice_service.create_invoice(dict(payload), actor="test")
        faktura_beta = self.invoice_service.create_invoice(
            dict(payload),
            actor="test",
            organization_id=int(druga_organizacja["organization_id"]),
        )

        self.assertNotEqual(faktura_domyslna["organization_id"], faktura_beta["organization_id"])
        self.assertEqual(faktura_domyslna["duplicate_type"], "brak")
        self.assertEqual(faktura_beta["duplicate_type"], "brak")
        self.assertIn("/organizacje/organizacja-domyslna/", faktura_domyslna["file_link"])
        self.assertIn("/organizacje/klient-beta/", faktura_beta["file_link"])

        kontrahenci_domyslni = self.invoice_service.list_contractors(organization_id=faktura_domyslna["organization_id"])
        kontrahenci_beta = self.invoice_service.list_contractors(organization_id=faktura_beta["organization_id"])
        self.assertEqual(len(kontrahenci_domyslni), 1)
        self.assertEqual(len(kontrahenci_beta), 1)
        self.assertNotEqual(
            kontrahenci_domyslni[0]["contractor_id"],
            kontrahenci_beta[0]["contractor_id"],
        )

    def test_invoices_from_inactive_organization_are_hidden_but_not_deleted(self) -> None:
        organizacja = self.organization_service.create_organization(
            {"name": "Klient Archiwalny", "slug": "klient-archiwalny", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )

        faktura = self.invoice_service.create_invoice(
            {
                "incoming_date": "2026-04-08",
                "source": "EMAIL",
                "file_name": "archiwalna.pdf",
                "document_type": "pdf",
                "invoice_number": "ARCH/1/04/2026",
                "issuer_nip": "4445556667",
                "issuer_name": "Archiwalny Dostawca",
                "issue_date": "2026-04-08",
                "sale_date": "2026-04-08",
                "gross_amount": 199.0,
                "currency": "PLN",
                "status": "nowa",
            },
            actor="test",
            organization_id=int(organizacja["organization_id"]),
        )

        self.organization_service.update_organization(
            int(organizacja["organization_id"]),
            {"is_active": 0},
            actor_user=self.admin,
            actor_login="admin",
        )

        self.assertEqual(self.services["invoice_repository"].count_all(), 0)
        self.assertEqual(
            self.services["invoice_repository"].count_all(organization_id=int(organizacja["organization_id"])),
            0,
        )
        self.assertEqual(
            self.invoice_service.list_invoices({}, organization_id=int(organizacja["organization_id"])),
            [],
        )
        self.assertIsNone(
            self.invoice_service.get_invoice_detail(
                int(faktura["id"]),
                organization_id=int(organizacja["organization_id"]),
            )
        )

    def test_organization_can_store_unique_telegram_channel_settings(self) -> None:
        organizacja = self.organization_service.create_organization(
            {
                "name": "Klient Telegram",
                "slug": "klient-telegram",
                "telegram_chat_id": "-1001234567890",
                "telegram_chat_name": "Klient Telegram - dokumenty",
                "is_active": 1,
            },
            actor_user=self.admin,
            actor_login="admin",
        )

        self.assertEqual(organizacja["telegram_chat_id"], "-1001234567890")
        self.assertEqual(organizacja["telegram_chat_name"], "Klient Telegram - dokumenty")

        with self.assertRaises(OrganizationError):
            self.organization_service.create_organization(
                {
                    "name": "Drugi klient Telegram",
                    "slug": "drugi-klient-telegram",
                    "telegram_chat_id": "-1001234567890",
                    "is_active": 1,
                },
                actor_user=self.admin,
                actor_login="admin",
            )


if __name__ == "__main__":
    unittest.main()
