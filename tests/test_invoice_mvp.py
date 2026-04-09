from __future__ import annotations

import unittest

from app.bootstrap import build_services
from app.db import reset_database
from app.demo_seed import seed_demo_data


class InvoiceMvpTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.services = build_services()
        seed_demo_data(self.services["invoice_service"], self.services["invoice_repository"])

    def test_seed_creates_expected_records(self) -> None:
        invoices = self.services["invoice_service"].list_invoices({})
        contractors = self.services["invoice_service"].list_contractors()
        self.assertEqual(len(invoices), 5)
        self.assertEqual(len(contractors), 3)

    def test_certain_duplicate_is_detected_by_ksef(self) -> None:
        detail = self.services["invoice_service"].get_invoice_detail(2)
        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertEqual(detail["invoice"]["duplicate_type"], "pewny")
        self.assertEqual(detail["invoice"]["status"], "pewny_duplikat")
        self.assertIn("KSEF-2026-0001-PL", detail["invoice"]["flag_reason"])
        self.assertTrue(any(item["id"] == 1 for item in detail["similar_invoices"]))

    def test_suspected_duplicate_is_detected_by_number_and_nip(self) -> None:
        detail = self.services["invoice_service"].get_invoice_detail(4)
        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertEqual(detail["invoice"]["duplicate_type"], "podejrzenie")
        self.assertEqual(detail["invoice"]["status"], "podejrzenie_duplikatu")
        self.assertTrue(any(item["id"] == 3 for item in detail["similar_invoices"]))

    def test_new_contractor_stays_marked_as_new(self) -> None:
        detail = self.services["invoice_service"].get_invoice_detail(5)
        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertEqual(detail["contractor"]["nip"], "5556667778")
        self.assertEqual(detail["contractor"]["is_new"], 1)
        self.assertFalse(detail["contractor_known_before"])

    def test_rejecting_duplicate_clears_flag(self) -> None:
        self.services["invoice_service"].reject_duplicate(4, actor="test")
        detail = self.services["invoice_service"].get_invoice_detail(4)
        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertEqual(detail["invoice"]["duplicate_type"], "brak")
        self.assertEqual(detail["invoice"]["status"], "poprawna")
        self.assertEqual(detail["invoice"]["flag_reason"], "Faktura została oznaczona jako poprawna ręcznie.")

    def test_manual_duplicate_actions_always_refresh_verification_description(self) -> None:
        self.services["invoice_service"].reject_duplicate(4, actor="test")
        self.services["invoice_service"].confirm_duplicate(4, actor="test")
        detail = self.services["invoice_service"].get_invoice_detail(4)
        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertEqual(detail["invoice"]["status"], "pewny_duplikat")
        self.assertEqual(detail["invoice"]["duplicate_type"], "pewny")
        self.assertEqual(detail["invoice"]["flag_reason"], "Duplikat został potwierdzony ręcznie.")

        self.services["invoice_service"].reject_duplicate(4, actor="test")
        detail = self.services["invoice_service"].get_invoice_detail(4)
        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertEqual(detail["invoice"]["status"], "poprawna")
        self.assertEqual(detail["invoice"]["duplicate_type"], "brak")
        self.assertEqual(detail["invoice"]["flag_reason"], "Faktura została oznaczona jako poprawna ręcznie.")

    def test_repeated_test_import_shows_human_duplicate_message(self) -> None:
        self.services["invoice_service"].import_mock("EMAIL", actor="test")
        with self.assertRaisesRegex(
            ValueError,
            "Nie można dodać dokumentu, ponieważ identyczna faktura została już wcześniej zapisana.",
        ):
            self.services["invoice_service"].import_mock("EMAIL", actor="test")


if __name__ == "__main__":
    unittest.main()
