from __future__ import annotations

import unittest

from configure_email_settings import build_updated_env_text


def _email_settings_payload() -> dict[str, str]:
    return {
        "INVOICE_EMAIL_IMAP_HOST": "imap.gmail.com",
        "INVOICE_EMAIL_IMAP_PORT": "993",
        "INVOICE_EMAIL_IMAP_USERNAME": "test@example.com",
        "INVOICE_EMAIL_IMAP_PASSWORD": "secret",
        "INVOICE_EMAIL_IMAP_FOLDER": "INBOX",
        "INVOICE_EMAIL_IMAP_USE_SSL": "1",
        "INVOICE_EMAIL_FETCH_LIMIT": "100",
        "INVOICE_EMAIL_AUTOCHECK_ENABLED": "1",
        "INVOICE_EMAIL_AUTOCHECK_SECONDS": "300",
        "INVOICE_PUBLIC_BASE_URL": "https://panel.example.com",
        "INVOICE_EMAIL_GOOGLE_CLIENT_ID": "client-id",
        "INVOICE_EMAIL_GOOGLE_CLIENT_SECRET": "client-secret",
    }


class ConfigureEmailSettingsTests(unittest.TestCase):
    def test_build_updated_env_text_preserves_non_email_values(self) -> None:
        existing = """KEEP_ME=1
INVOICE_EMAIL_IMAP_HOST=old.example.com
INVOICE_PUBLIC_BASE_URL=http://old.example.com
# komentarz
OTHER_VALUE=abc
"""
        updated = build_updated_env_text(existing, _email_settings_payload())

        self.assertIn("KEEP_ME=1", updated)
        self.assertIn("OTHER_VALUE=abc", updated)
        self.assertIn("INVOICE_EMAIL_IMAP_HOST=imap.gmail.com", updated)
        self.assertIn("INVOICE_PUBLIC_BASE_URL=https://panel.example.com", updated)
        self.assertNotIn("INVOICE_EMAIL_IMAP_HOST=old.example.com", updated)
        self.assertNotIn("INVOICE_PUBLIC_BASE_URL=http://old.example.com", updated)

    def test_build_updated_env_text_adds_all_email_blocks_to_empty_file(self) -> None:
        updated = build_updated_env_text("", _email_settings_payload())

        self.assertTrue(updated.startswith("# Ustawienia e-mail / IMAP"))
        self.assertIn("INVOICE_EMAIL_IMAP_PASSWORD=secret", updated)
        self.assertIn("# Automat sprawdzania skrzynki", updated)
        self.assertIn("INVOICE_EMAIL_AUTOCHECK_ENABLED=1", updated)
        self.assertIn("INVOICE_EMAIL_AUTOCHECK_SECONDS=300", updated)
        self.assertIn("# Google Workspace OAuth dla centralnej skrzynki", updated)
        self.assertIn("INVOICE_PUBLIC_BASE_URL=https://panel.example.com", updated)
        self.assertIn("INVOICE_EMAIL_GOOGLE_CLIENT_ID=client-id", updated)
        self.assertIn("INVOICE_EMAIL_GOOGLE_CLIENT_SECRET=client-secret", updated)


if __name__ == "__main__":
    unittest.main()
