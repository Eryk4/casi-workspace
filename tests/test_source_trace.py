from __future__ import annotations

import unittest
from pathlib import Path

from app.bootstrap import build_services
from app.config import DOCUMENTS_DIR, OCR_DIR
from app.db import reset_database


class SourceTraceTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.services = build_services()
        self.services["auth_service"].ensure_default_admin()

    def test_telegram_import_stores_sender_trace_and_structured_paths(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        self.services["auth_service"].create_user(
            {
                "login": "Eryk",
                "display_name": "Eryk",
                "telegram_user_id": "582114092",
                "password": "9834",
                "role": "operator",
                "is_active": 1,
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
        )

        invoice = self.services["invoice_service"].import_mock("TELEGRAM")
        detail = self.services["invoice_service"].get_invoice_detail(invoice["id"])

        self.assertIsNotNone(detail)
        assert detail is not None

        self.assertEqual(detail["invoice"]["source"], "TELEGRAM")
        self.assertEqual(detail["invoice"]["document_type"], "zdjecie")
        self.assertEqual(detail["invoice"]["source_sender_name"], "eryklach95")
        self.assertEqual(detail["invoice"]["source_sender_id"], "582114092")
        self.assertEqual(detail["invoice"]["storage_backend"], "lokalny")
        self.assertTrue(detail["invoice"]["file_storage_key"].startswith("organizacje/organizacja-domyslna/TELEGRAM/"))
        self.assertTrue(detail["invoice"]["ocr_storage_key"].startswith("organizacje/organizacja-domyslna/TELEGRAM/"))
        self.assertTrue(
            detail["invoice"]["file_link"].startswith("/pliki/dokumenty/organizacje/organizacja-domyslna/TELEGRAM/2026-04-07/")
        )
        self.assertTrue(
            detail["invoice"]["ocr_link"].startswith("/pliki/ocr/organizacje/organizacja-domyslna/TELEGRAM/2026-04-07/")
        )

        source_trace = detail["source_trace"]
        self.assertEqual(source_trace["source_sender_name"], "eryklach95")
        self.assertEqual(source_trace["metadata"]["typ_wiadomosci"], "upload_zdjecia")
        self.assertIsNotNone(source_trace["linked_user"])
        self.assertEqual(source_trace["linked_user"]["login"], "Eryk")
        self.assertTrue(any(item["event_type"] == "invoice_created" and item["actor"] == "Eryk" for item in detail["history"]))

        file_relative = detail["invoice"]["file_link"].removeprefix("/pliki/dokumenty/")
        ocr_relative = detail["invoice"]["ocr_link"].removeprefix("/pliki/ocr/")
        self.assertEqual(file_relative, detail["invoice"]["file_storage_key"])
        self.assertEqual(ocr_relative, detail["invoice"]["ocr_storage_key"])
        self.assertTrue((DOCUMENTS_DIR / Path(file_relative)).exists())
        self.assertTrue((OCR_DIR / Path(ocr_relative)).exists())


if __name__ == "__main__":
    unittest.main()
