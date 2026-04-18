from __future__ import annotations

from tests.http_server_support import HttpServerTestCase
from tests.http_server_test_methods import HttpServerTestMethods


class HttpServerTelegramTests(HttpServerTestCase):
    test_public_telegram_webhook_creates_invoice_and_stores_real_file = (
        HttpServerTestMethods.test_public_telegram_webhook_creates_invoice_and_stores_real_file
    )
    test_public_telegram_webhook_can_resolve_organization_by_chat_id = (
        HttpServerTestMethods.test_public_telegram_webhook_can_resolve_organization_by_chat_id
    )
    test_public_telegram_webhook_marks_invoice_for_verification_when_ocr_fails = (
        HttpServerTestMethods.test_public_telegram_webhook_marks_invoice_for_verification_when_ocr_fails
    )


del HttpServerTestCase
del HttpServerTestMethods
