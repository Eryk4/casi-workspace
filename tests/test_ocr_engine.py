from __future__ import annotations

import unittest
from unittest.mock import patch

from app.integrations.ocr_engine import OCREngine


class OCREngineTests(unittest.TestCase):
    def test_extract_data_parses_invoice_fields_from_textual_content(self) -> None:
        engine = OCREngine()
        content = (
            "%PDF-1.4\n"
            "Numer faktury: FV/44/04/2026\n"
            "NIP wystawcy: 1234567890\n"
            "Data wystawienia: 09.04.2026\n"
            "Data sprzedaży: 10.04.2026\n"
            "Kwota brutto: 1 234,56 PLN\n"
            "Wystawca: Biuro Serwis Alfa Sp. z o.o.\n"
        ).encode("utf-8")

        result = engine.extract_data("faktura_telegram.pdf", content)

        self.assertIn("Numer faktury: FV/44/04/2026", result["ocr_raw_text"])
        self.assertEqual(result["invoice_number"], "FV/44/04/2026")
        self.assertEqual(result["issuer_nip"], "1234567890")
        self.assertEqual(result["issue_date"], "2026-04-09")
        self.assertEqual(result["sale_date"], "2026-04-10")
        self.assertEqual(result["gross_amount"], 1234.56)
        self.assertEqual(result["currency"], "PLN")
        self.assertEqual(result["issuer_name"], "Biuro Serwis Alfa Sp. z o.o")

    def test_extract_data_returns_fallback_text_when_no_local_ocr_is_available(self) -> None:
        engine = OCREngine()
        binary_content = b"\x00\x01\x02\x03\x04\x05"

        with patch.object(engine, "tesseract_cmd", ""):
            result = engine.extract_data("skan_faktury.jpg", binary_content)

        self.assertIn("Nie udało się odczytać treści dokumentu lokalnym OCR.", result["ocr_raw_text"])
        self.assertEqual(result["gross_amount"], None)
        self.assertEqual(result["invoice_number"], "")
        self.assertEqual(result["issuer_nip"], "")


if __name__ == "__main__":
    unittest.main()
