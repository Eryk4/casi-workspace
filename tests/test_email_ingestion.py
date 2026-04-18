from __future__ import annotations

import unittest
import imaplib
from email.message import EmailMessage
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from app.integrations.email_ingestion import EmailIngestionAdapter, EmailIngestionError


class FakeOCREngine:
    def extract_data(self, file_name: str, file_bytes: bytes | None = None) -> dict:
        return {
            "ocr_raw_text": "Numer faktury: FV/EMAIL/44/04/2026",
            "ocr_confidence": 0.93,
            "invoice_number": "FV/EMAIL/44/04/2026",
            "ksef_number": "",
            "issuer_nip": "1234567890",
            "issuer_name": "Email Dostawca Sp. z o.o.",
            "issue_date": "2026-04-11",
            "sale_date": "2026-04-11",
            "gross_amount": 120.50,
            "currency": "PLN",
        }


class FakeIMAPClient:
    def __init__(self, message_bytes_by_uid: dict[str, bytes]) -> None:
        self.message_bytes_by_uid = message_bytes_by_uid
        self.selected_folder = ""
        self.logged_out = False
        self.authenticate_calls: list[tuple[str, bytes]] = []

    def login(self, username: str, password: str) -> tuple[str, list[bytes]]:
        return ("OK", [b"logged-in"])

    def authenticate(self, mechanism: str, auth_callback) -> tuple[str, list[bytes]]:
        payload = auth_callback(None)
        self.authenticate_calls.append((mechanism, payload))
        return ("OK", [b"authenticated"])

    def select(self, folder: str, readonly: bool = False) -> tuple[str, list[bytes]]:
        self.selected_folder = folder
        return ("OK", [b"1"])

    def uid(self, command: str, *args):
        normalized = str(command or "").lower()
        if normalized == "search":
            ordered_ids = b" ".join(uid.encode("utf-8") for uid in self.message_bytes_by_uid.keys())
            return ("OK", [ordered_ids])
        if normalized == "fetch":
            uid = args[0]
            if isinstance(uid, bytes):
                uid = uid.decode("utf-8")
            payload = self.message_bytes_by_uid[str(uid)]
            return ("OK", [(b"RFC822", payload)])
        raise AssertionError(f"Nieoczekiwana komenda IMAP: {command}")

    def logout(self) -> tuple[str, list[bytes]]:
        self.logged_out = True
        return ("BYE", [b"logout"])


class EmailIngestionAdapterTests(unittest.TestCase):
    def _build_message_bytes(
        self,
        *,
        to_address: str,
        from_address: str,
        subject: str,
        message_id: str,
        attachment_name: str,
        attachment_bytes: bytes,
    ) -> bytes:
        message = EmailMessage()
        message["To"] = to_address
        message["From"] = from_address
        message["Subject"] = subject
        message["Date"] = "Fri, 11 Apr 2026 10:15:00 +0200"
        message["Message-ID"] = message_id
        message.set_content("W zalaczniku przesylamy fakture.")
        message.add_attachment(
            attachment_bytes,
            maintype="application",
            subtype="pdf",
            filename=attachment_name,
        )
        return message.as_bytes()

    def test_fetch_invoice_candidates_reads_matching_imap_message(self) -> None:
        raw_message = self._build_message_bytes(
            to_address="Faktury <faktury@klient-email.pl>",
            from_address="Dostawca <dokumenty@dostawca.pl>",
            subject="Faktura FV/EMAIL/44/04/2026",
            message_id="<mail-1@example.com>",
            attachment_name="fv_email_44.pdf",
            attachment_bytes=b"%PDF-1.4 test",
        )
        fake_client = FakeIMAPClient({"101": raw_message})
        adapter = EmailIngestionAdapter(
            FakeOCREngine(),
            host="imap.example.com",
            port=993,
            username="user@example.com",
            password="sekret",
            folder="INBOX",
            use_ssl=True,
            fetch_limit=10,
        )

        organization = {
            "email_inbox_address": "faktury@klient-email.pl",
            "email_allowed_sender": "dokumenty@dostawca.pl",
            "email_subject_keyword": "Faktura",
        }

        with patch("app.integrations.email_ingestion.imaplib.IMAP4_SSL", return_value=fake_client):
            result = adapter.fetch_invoice_candidates(organization)

        self.assertEqual(result["checked_message_count"], 1)
        self.assertEqual(result["matched_message_count"], 1)
        self.assertEqual(result["matched_attachment_count"], 1)
        self.assertEqual(result["routing_mode"], "central_mailbox")
        self.assertEqual(len(result["candidates"]), 1)
        candidate = result["candidates"][0]
        self.assertEqual(candidate["source"], "EMAIL")
        self.assertEqual(candidate["file_name"], "fv_email_44.pdf")
        self.assertEqual(candidate["document_type"], "pdf")
        self.assertEqual(candidate["invoice_number"], "FV/EMAIL/44/04/2026")
        self.assertEqual(candidate["source_sender_name"], "dokumenty@dostawca.pl")
        self.assertEqual(candidate["incoming_date"], "2026-04-11")
        self.assertEqual(candidate["document_bytes"], b"%PDF-1.4 test")
        self.assertTrue(candidate["source_external_id"].startswith("email-"))
        self.assertEqual(candidate["source_metadata"]["skrzynka"], "faktury@klient-email.pl")
        self.assertEqual(candidate["source_metadata"]["nadawca_email"], "dokumenty@dostawca.pl")

    def test_fetch_invoice_candidates_skips_message_with_wrong_sender(self) -> None:
        raw_message = self._build_message_bytes(
            to_address="Faktury <faktury@klient-email.pl>",
            from_address="Inny Dostawca <inny@dostawca.pl>",
            subject="Faktura FV/EMAIL/55/04/2026",
            message_id="<mail-2@example.com>",
            attachment_name="fv_email_55.pdf",
            attachment_bytes=b"%PDF-1.4 test",
        )
        fake_client = FakeIMAPClient({"102": raw_message})
        adapter = EmailIngestionAdapter(
            FakeOCREngine(),
            host="imap.example.com",
            port=993,
            username="user@example.com",
            password="sekret",
            use_ssl=True,
        )

        organization = {
            "email_inbox_address": "faktury@klient-email.pl",
            "email_allowed_sender": "dokumenty@dostawca.pl",
            "email_subject_keyword": "Faktura",
        }

        with patch("app.integrations.email_ingestion.imaplib.IMAP4_SSL", return_value=fake_client):
            result = adapter.fetch_invoice_candidates(organization)

        self.assertEqual(result["checked_message_count"], 1)
        self.assertEqual(result["matched_message_count"], 0)
        self.assertEqual(result["matched_attachment_count"], 0)
        self.assertEqual(result["candidates"], [])

    def test_fetch_invoice_candidates_requires_imap_configuration(self) -> None:
        adapter = EmailIngestionAdapter(FakeOCREngine(), host="", username="", password="")

        with self.assertRaisesRegex(EmailIngestionError, "skonfigurowana na poziomie systemu"):
            adapter.fetch_invoice_candidates({"email_inbox_address": "faktury@klient-email.pl"})

    def test_test_connection_returns_folder_and_message_count(self) -> None:
        raw_message = self._build_message_bytes(
            to_address="Faktury <faktury@klient-email.pl>",
            from_address="Dostawca <dokumenty@dostawca.pl>",
            subject="Faktura FV/EMAIL/44/04/2026",
            message_id="<mail-3@example.com>",
            attachment_name="fv_email_44.pdf",
            attachment_bytes=b"%PDF-1.4 test",
        )
        fake_client = FakeIMAPClient({"201": raw_message, "202": raw_message})
        adapter = EmailIngestionAdapter(
            FakeOCREngine(),
            host="imap.example.com",
            port=993,
            username="user@example.com",
            password="sekret",
            folder="INBOX",
            use_ssl=True,
            fetch_limit=10,
        )

        with patch("app.integrations.email_ingestion.imaplib.IMAP4_SSL", return_value=fake_client):
            result = adapter.test_connection(limit=1)

        self.assertTrue(result["connected"])
        self.assertEqual(result["folder"], "INBOX")
        self.assertEqual(result["message_count"], 2)
        self.assertEqual(result["preview_uids"], ["202"])
        self.assertEqual(result["username_masked"], "us***@example.com")

    def test_test_connection_returns_google_workspace_hint_for_auth_error(self) -> None:
        adapter = EmailIngestionAdapter(
            FakeOCREngine(),
            host="imap.gmail.com",
            port=993,
            username="user@example.com",
            password="sekret",
            use_ssl=True,
        )

        with patch(
            "app.integrations.email_ingestion.imaplib.IMAP4_SSL",
            side_effect=imaplib.IMAP4.error("Application-specific password required"),
        ):
            with self.assertRaisesRegex(EmailIngestionError, "hasla aplikacji Google"):
                adapter.test_connection()

    def test_test_connection_uses_google_oauth_and_masks_google_email(self) -> None:
        class FakeOAuthRepository:
            def get_google_connection(self):
                return {
                    "google_email": "centralna@casi24.com",
                    "access_token": "token-123",
                    "refresh_token": "refresh-123",
                    "token_expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
                    "scope": "https://mail.google.com/",
                }

            def upsert_google_connection(self, payload, created_by_user_id=None):
                return payload

        class FakeGoogleOAuthAdapter:
            def build_xoauth2_string(self, username: str, access_token: str) -> bytes:
                return f"{username}|{access_token}".encode("utf-8")

            def refresh_tokens(self, refresh_token: str):
                return {
                    "access_token": "refreshed-token",
                    "refresh_token": refresh_token,
                    "token_expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
                    "scope": "https://mail.google.com/",
                }

        raw_message = self._build_message_bytes(
            to_address="Faktury <faktury@klient-email.pl>",
            from_address="Dostawca <dokumenty@dostawca.pl>",
            subject="Faktura FV/EMAIL/66/04/2026",
            message_id="<mail-66@example.com>",
            attachment_name="fv_email_66.pdf",
            attachment_bytes=b"%PDF-1.4 test",
        )
        fake_client = FakeIMAPClient({"301": raw_message})
        adapter = EmailIngestionAdapter(
            FakeOCREngine(),
            host="imap.gmail.com",
            port=993,
            folder="INBOX",
            use_ssl=True,
            oauth_repository=FakeOAuthRepository(),
            google_oauth_adapter=FakeGoogleOAuthAdapter(),
        )

        status = adapter.integration_status()
        self.assertTrue(status["enabled"])
        self.assertEqual(status["mode"], "google_oauth")
        self.assertTrue(status["uses_google_oauth"])
        self.assertEqual(status["mailbox_address"], "centralna@casi24.com")

        with patch("app.integrations.email_ingestion.imaplib.IMAP4_SSL", return_value=fake_client):
            result = adapter.test_connection(limit=1)

        self.assertTrue(result["connected"])
        self.assertEqual(result["username_masked"], "ce***@casi24.com")
        self.assertEqual(fake_client.authenticate_calls[0][0], "XOAUTH2")
        self.assertEqual(fake_client.authenticate_calls[0][1], b"centralna@casi24.com|token-123")



if __name__ == "__main__":
    unittest.main()
