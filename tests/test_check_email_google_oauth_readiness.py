from __future__ import annotations

import unittest

from check_email_google_oauth_readiness import evaluate_google_email_oauth_readiness


class CheckEmailGoogleOAuthReadinessTests(unittest.TestCase):
    def test_readiness_is_true_for_complete_https_configuration(self) -> None:
        result = evaluate_google_email_oauth_readiness(
            public_base_url="https://panel.example.com",
            client_id="client-id",
            client_secret="client-secret",
            connection={"google_email": "inbox@example.com"},
        )

        self.assertTrue(result["ready"])
        self.assertTrue(result["connected"])
        self.assertEqual([], result["missing"])

    def test_readiness_is_false_when_public_url_is_not_https(self) -> None:
        result = evaluate_google_email_oauth_readiness(
            public_base_url="http://panel.example.com",
            client_id="client-id",
            client_secret="client-secret",
            connection=None,
        )

        self.assertFalse(result["ready"])
        self.assertFalse(result["uses_https"])
        self.assertFalse(result["connected"])

    def test_readiness_reports_missing_values(self) -> None:
        result = evaluate_google_email_oauth_readiness(
            public_base_url="",
            client_id="",
            client_secret="",
            connection=None,
        )

        self.assertFalse(result["ready"])
        self.assertEqual(
            [
                "INVOICE_PUBLIC_BASE_URL",
                "INVOICE_EMAIL_GOOGLE_CLIENT_ID",
                "INVOICE_EMAIL_GOOGLE_CLIENT_SECRET",
            ],
            result["missing"],
        )


if __name__ == "__main__":
    unittest.main()
