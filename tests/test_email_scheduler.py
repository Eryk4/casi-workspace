from __future__ import annotations

import unittest
from unittest.mock import patch

from app.bootstrap import build_services
from app.db import reset_database


class EmailSchedulerTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.services = build_services()
        self.auth_service = self.services["auth_service"]
        self.invoice_service = self.services["invoice_service"]
        self.organization_service = self.services["organization_service"]
        self.organization_repository = self.services["organization_repository"]
        self.email_import_repository = self.services["email_import_repository"]
        self.auth_service.ensure_default_admin()
        self.admin = self.auth_service.list_users()[0]

    def _create_org(self, *, name: str, slug: str, inbox: str, enabled: int = 1) -> dict[str, object]:
        return self.organization_service.create_organization(
            {
                "name": name,
                "slug": slug,
                "email_inbox_address": inbox,
                "email_allowed_sender": "faktury@dostawca.pl",
                "email_subject_keyword": "Faktura",
                "email_integration_enabled": enabled,
                "is_active": 1,
            },
            actor_user=self.admin,
            actor_login="admin",
        )

    def test_automatic_cycle_imports_ready_organizations_and_marks_runs(self) -> None:
        imported_org = self._create_org(
            name="Klient Import",
            slug="klient-import",
            inbox="faktury+import@casi24.com",
        )
        empty_org = self._create_org(
            name="Klient Bez Nowych",
            slug="klient-bez-nowych",
            inbox="faktury+empty@casi24.com",
        )

        def fake_fetch(organization, *, trigger_mode="manual", limit=None):
            organization_id = int(organization["organization_id"])
            if organization_id == int(imported_org["organization_id"]):
                self.assertEqual(trigger_mode, "automatic")
                return {
                    "candidates": [
                        {
                            "incoming_date": "2026-04-13",
                            "source": "EMAIL",
                            "file_name": "auto_mail_faktura.pdf",
                            "document_type": "pdf",
                            "invoice_number": "FV/AUTO/13/04/2026",
                            "ksef_number": "",
                            "issuer_nip": "1234567890",
                            "issuer_name": "Automat Dostawca Sp. z o.o.",
                            "issue_date": "2026-04-13",
                            "sale_date": "2026-04-13",
                            "gross_amount": 321.55,
                            "currency": "PLN",
                            "source_external_id": "email-auto-13",
                            "source_sender_name": "faktury@dostawca.pl",
                            "source_metadata": {
                                "temat": "Faktura FV/AUTO/13/04/2026",
                                "skrzynka": organization["email_inbox_address"],
                                "tryb": "automatic-check-imap",
                                "message_id": "<auto-13@example.com>",
                                "imap_uid": "13",
                                "nadawca_email": "faktury@dostawca.pl",
                                "odbiorcy": [organization["email_inbox_address"]],
                                "dopasowany_odbiorca": organization["email_inbox_address"],
                                "zalacznik_typ": "application/pdf",
                                "zalacznik_index": 1,
                            },
                            "notes": "Import automatyczny z e-maila.",
                        }
                    ],
                    "checked_message_count": 1,
                    "matched_message_count": 1,
                    "matched_attachment_count": 1,
                    "routing_mode": "central_mailbox",
                }

            self.assertEqual(organization_id, int(empty_org["organization_id"]))
            return {
                "candidates": [],
                "checked_message_count": 2,
                "matched_message_count": 0,
                "matched_attachment_count": 0,
                "routing_mode": "central_mailbox",
            }

        with patch("app.services.invoice_service.EMAIL_AUTOCHECK_ENABLED", True), patch(
            "app.services.invoice_service.EMAIL_AUTOCHECK_SECONDS",
            300,
        ), patch.object(self.invoice_service.email_adapter, "is_configured", return_value=True), patch.object(
            self.invoice_service.email_adapter,
            "fetch_invoice_candidates",
            side_effect=fake_fetch,
        ):
            result = self.invoice_service.run_email_scheduler_cycle()

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["checked_organization_count"], 2)
        self.assertEqual(result["imported_invoice_count"], 1)
        self.assertEqual(result["organizations_with_imports"], 1)
        self.assertEqual(result["organizations_without_new_documents"], 1)
        self.assertEqual(result["organizations_with_errors"], 0)

        imported_runs = self.email_import_repository.list_runs_for_organization(int(imported_org["organization_id"]), limit=1)
        empty_runs = self.email_import_repository.list_runs_for_organization(int(empty_org["organization_id"]), limit=1)
        self.assertEqual(imported_runs[0]["trigger_mode"], "automatic")
        self.assertEqual(empty_runs[0]["trigger_mode"], "automatic")
        self.assertEqual(imported_runs[0]["imported_invoice_count"], 1)
        self.assertEqual(empty_runs[0]["status"], "no_new_documents")

        imported_updated = self.organization_repository.get_by_id(int(imported_org["organization_id"]))
        empty_updated = self.organization_repository.get_by_id(int(empty_org["organization_id"]))
        self.assertIsNotNone(imported_updated)
        self.assertIsNotNone(empty_updated)
        assert imported_updated is not None
        assert empty_updated is not None
        self.assertIn("Zaimportowano 1 nowych faktur z e-maila.", imported_updated["email_last_check_status"])
        self.assertEqual(empty_updated["email_last_check_status"], "Brak nowych dokumentow e-mail do importu.")

    def test_scheduler_status_reports_not_configured_when_imap_missing(self) -> None:
        with patch("app.services.invoice_service.EMAIL_AUTOCHECK_ENABLED", True), patch(
            "app.services.invoice_service.EMAIL_AUTOCHECK_SECONDS",
            300,
        ), patch.object(self.invoice_service.email_adapter, "is_configured", return_value=False):
            result = self.invoice_service.run_email_scheduler_cycle()

        self.assertEqual(result["status"], "not_configured")
        self.assertIn("konfiguracje IMAP", result["message"])


if __name__ == "__main__":
    unittest.main()
