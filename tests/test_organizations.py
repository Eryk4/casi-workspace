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
        self.organization_repository = self.services["organization_repository"]
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
        domyslna_organizacja = self.organization_repository.ensure_default_organization()
        self.assertIn(f"/organizacje/{domyslna_organizacja['slug']}/", faktura_domyslna["file_link"])
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

    def test_organization_can_store_slack_configuration_as_active_provider(self) -> None:
        organizacja = self.organization_service.create_organization(
            {
                "name": "Klient Slack",
                "slug": "klient-slack",
                "communication_provider": "slack",
                "communication_config": {
                    "slack": {
                        "workspace_name": "Casi Ops",
                        "channel_id": "C0123456789",
                        "channel_name": "#klient-slack",
                    }
                },
                "is_active": 1,
            },
            actor_user=self.admin,
            actor_login="admin",
        )

        self.assertEqual(organizacja["communication_provider"], "slack")
        self.assertEqual(organizacja["communication_provider_label"], "Slack")
        self.assertEqual(organizacja["communication_target_summary"], "#klient-slack")
        self.assertEqual(organizacja["telegram_chat_id"], None)
        self.assertEqual(organizacja["communication_config"]["slack"]["workspace_name"], "Casi Ops")
        self.assertEqual(organizacja["communication_config"]["slack"]["channel_id"], "C0123456789")

    def test_switching_active_provider_keeps_saved_configs_but_clears_active_telegram_fields(self) -> None:
        organizacja = self.organization_service.create_organization(
            {
                "name": "Klient Multi",
                "slug": "klient-multi",
                "telegram_chat_id": "-1001234567891",
                "telegram_chat_name": "Klient Multi - dokumenty",
                "is_active": 1,
            },
            actor_user=self.admin,
            actor_login="admin",
        )

        updated = self.organization_service.update_organization(
            int(organizacja["organization_id"]),
            {
                "communication_provider": "slack",
                "communication_config": {
                    "slack": {
                        "workspace_name": "Casi Ops",
                        "channel_id": "C0999999999",
                        "channel_name": "#multi",
                    }
                },
            },
            actor_user=self.admin,
            actor_login="admin",
        )

        self.assertEqual(updated["communication_provider"], "slack")
        self.assertIsNone(updated["telegram_chat_id"])
        self.assertIsNone(updated["telegram_chat_name"])
        self.assertEqual(updated["communication_config"]["telegram"]["chat_id"], "-1001234567891")
        self.assertEqual(updated["communication_config"]["slack"]["channel_name"], "#multi")

    def test_whatsapp_number_must_use_supported_format(self) -> None:
        with self.assertRaises(OrganizationError):
            self.organization_service.create_organization(
                {
                    "name": "Klient WhatsApp",
                    "slug": "klient-whatsapp",
                    "communication_provider": "whatsapp",
                    "communication_config": {
                        "whatsapp": {
                            "phone_number": "abc-123",
                            "display_name": "Klient WA",
                        }
                    },
                    "is_active": 1,
                },
                actor_user=self.admin,
                actor_login="admin",
            )

    def test_active_slack_channel_must_be_unique_between_organizations(self) -> None:
        self.organization_service.create_organization(
            {
                "name": "Klient Slack 1",
                "slug": "klient-slack-1",
                "communication_provider": "slack",
                "communication_config": {
                    "slack": {
                        "workspace_name": "Casi Ops",
                        "channel_id": "C0999999999",
                        "channel_name": "#faktury-klient-1",
                    }
                },
                "is_active": 1,
            },
            actor_user=self.admin,
            actor_login="admin",
        )

        with self.assertRaises(OrganizationError):
            self.organization_service.create_organization(
                {
                    "name": "Klient Slack 2",
                    "slug": "klient-slack-2",
                    "communication_provider": "slack",
                    "communication_config": {
                        "slack": {
                            "workspace_name": "Casi Ops",
                            "channel_id": "C0999999999",
                            "channel_name": "#faktury-klient-2",
                        }
                    },
                    "is_active": 1,
                },
                actor_user=self.admin,
                actor_login="admin",
            )

    def test_email_settings_can_be_saved_for_organization(self) -> None:
        organizacja = self.organization_service.create_organization(
            {
                "name": "Klient Email",
                "slug": "klient-email",
                "email_inbox_address": "faktury@klient-email.pl",
                "email_allowed_sender": "dokumenty@dostawca.pl",
                "email_subject_keyword": "Faktura",
                "email_integration_enabled": 1,
                "is_active": 1,
            },
            actor_user=self.admin,
            actor_login="admin",
        )

        self.assertEqual(organizacja["email_inbox_address"], "faktury@klient-email.pl")
        self.assertEqual(organizacja["email_allowed_sender"], "dokumenty@dostawca.pl")
        self.assertEqual(organizacja["email_subject_keyword"], "Faktura")
        self.assertEqual(int(organizacja["email_integration_enabled"]), 1)

    def test_email_integration_requires_inbox_address(self) -> None:
        with self.assertRaises(OrganizationError):
            self.organization_service.create_organization(
                {
                    "name": "Klient Bez Skrzynki",
                    "slug": "klient-bez-skrzynki",
                    "email_integration_enabled": 1,
                    "is_active": 1,
                },
                actor_user=self.admin,
                actor_login="admin",
            )

    def test_organization_can_store_temporary_ksef_delegate(self) -> None:
        organizacja = self.organization_service.create_organization(
            {
                "name": "Klient KSeF",
                "slug": "klient-ksef",
                "is_active": 1,
            },
            actor_user=self.admin,
            actor_login="admin",
        )
        delegat = self.auth_service.create_user(
            {
                "login": "ksef-delegat",
                "display_name": "KSeF Delegat",
                "password": "1234",
                "role": "coordinator",
                "is_active": 1,
                "organization_id": organizacja["organization_id"],
            },
            actor_login="admin",
            actor_user_id=int(self.admin["user_id"]),
            actor_user=self.admin,
        )

        updated = self.organization_service.update_organization(
            int(organizacja["organization_id"]),
            {
                "ksef_correction_delegate_user_id": delegat["user_id"],
                "ksef_correction_delegate_expires_at": "2026-05-31T18:30",
            },
            actor_user=self.admin,
            actor_login="admin",
        )

        self.assertEqual(updated["ksef_correction_delegate_user_id"], delegat["user_id"])
        self.assertEqual(updated["ksef_correction_delegate_expires_at"], "2026-05-31T18:30")
        self.assertTrue(updated["ksef_correction_delegate_assigned_at"])
        self.assertIsNotNone(updated["ksef_correction_delegate_user"])
        self.assertEqual(updated["ksef_correction_delegate_user"]["user_id"], delegat["user_id"])
        self.assertEqual(updated["ksef_correction_delegate_user"]["login"], "ksef-delegat")
        self.assertEqual(updated["ksef_correction_delegate_user"]["role"], "coordinator")

    def test_organization_can_store_module_shortcuts_with_empty_default(self) -> None:
        organizacja = self.organization_service.create_organization(
            {
                "name": "Klient Skroty",
                "slug": "klient-skroty",
                "module_shortcuts": {
                    "tasks": "ctrl + 1",
                    "knowledge": "Alt+2",
                    "logs": "",
                },
                "is_active": 1,
            },
            actor_user=self.admin,
            actor_login="admin",
        )

        self.assertEqual(
            organizacja["module_shortcuts"],
            {
                "knowledge": "Alt+2",
                "tasks": "Ctrl+1",
            },
        )

        bez_skrotow = self.organization_service.create_organization(
            {
                "name": "Klient Bez Skrotow",
                "slug": "klient-bez-skrotow",
                "is_active": 1,
            },
            actor_user=self.admin,
            actor_login="admin",
        )
        self.assertEqual(bez_skrotow["module_shortcuts"], {})

    def test_organization_module_shortcuts_must_be_unique(self) -> None:
        organizacja = self.organization_service.create_organization(
            {
                "name": "Klient Konflikt",
                "slug": "klient-konflikt",
                "is_active": 1,
            },
            actor_user=self.admin,
            actor_login="admin",
        )

        with self.assertRaises(OrganizationError):
            self.organization_service.update_organization(
                int(organizacja["organization_id"]),
                {
                    "module_shortcuts": {
                        "tasks": "Ctrl+1",
                        "knowledge": "Ctrl+1",
                    }
                },
                actor_user=self.admin,
                actor_login="admin",
            )

    def test_shared_note_is_available_for_organization(self) -> None:
        organizacja = self.organization_service.create_organization(
            {
                "name": "Klient Notatka",
                "slug": "klient-notatka",
                "is_active": 1,
            },
            actor_user=self.admin,
            actor_login="admin",
        )
        pracownik = self.auth_service.create_user(
            {
                "login": "notatka-pracownik",
                "display_name": "Notatka Pracownik",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": organizacja["organization_id"],
            },
            actor_login="admin",
            actor_user_id=int(self.admin["user_id"]),
            actor_user=self.admin,
        )

        updated = self.organization_service.update_shared_note(
            actor_user=pracownik,
            actor_login=pracownik["login"],
            requested_organization_id=int(organizacja["organization_id"]),
            shared_note_text="Pilnujemy dzis korekt od dostawcy Alfa.",
        )

        self.assertEqual(updated["organization_id"], int(organizacja["organization_id"]))
        self.assertEqual(updated["shared_note_text"], "Pilnujemy dzis korekt od dostawcy Alfa.")
        self.assertEqual(updated["shared_note_updated_by_user_id"], int(pracownik["user_id"]))
        self.assertEqual(updated["shared_note_updated_by_name"], "Notatka Pracownik")

        fetched = self.organization_service.get_shared_note(
            actor_user=pracownik,
            requested_organization_id=int(organizacja["organization_id"]),
        )
        self.assertEqual(fetched["shared_note_text"], "Pilnujemy dzis korekt od dostawcy Alfa.")
        self.assertTrue(fetched["shared_note_updated_at"])


if __name__ == "__main__":
    unittest.main()
