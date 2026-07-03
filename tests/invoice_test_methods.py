from __future__ import annotations

import unittest

from app.bootstrap import build_services
from app.db import get_connection, reset_database
from app.demo_seed import seed_demo_data
from app.services.auth_service import PermissionError


class InvoiceMvpTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.services = build_services()
        self.auth_service = self.services["auth_service"]
        self.organization_repository = self.services["organization_repository"]
        self.organization_service = self.services["organization_service"]
        self.approval_service = self.services["approval_service"]
        self.auth_service.ensure_default_admin()
        self.admin = self.auth_service.list_users()[0]
        self.default_organization = self.organization_repository.ensure_default_organization()
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

    def test_contractor_note_is_additive_and_visible_in_detail(self) -> None:
        invoice_detail = self.services["invoice_service"].get_invoice_detail(
            1,
            organization_id=int(self.default_organization["organization_id"]),
        )
        self.assertIsNotNone(invoice_detail)
        assert invoice_detail is not None
        contractor_id = int(invoice_detail["invoice"]["contractor_id"])
        contractor_before = self.services["invoice_service"].get_contractor_detail(
            contractor_id,
            organization_id=int(self.default_organization["organization_id"]),
            viewer_user=self.admin,
        )
        self.assertIsNotNone(contractor_before)
        assert contractor_before is not None
        invoice_before = self.services["invoice_service"].get_invoice_detail(
            1,
            organization_id=int(self.default_organization["organization_id"]),
        )
        with get_connection() as connection:
            ledger_count_before = connection.execute("SELECT COUNT(*) AS count FROM billing_payer_ledger_entries").fetchone()[
                "count"
            ]

        note = self.services["invoice_service"].add_contractor_note(
            contractor_id,
            "Notatka CRM do kontrahenta.",
            actor_user=self.admin,
            organization_id=int(self.default_organization["organization_id"]),
        )

        self.assertEqual(note["note_text"], "Notatka CRM do kontrahenta.")
        self.assertEqual(int(note["contractor_id"]), contractor_id)
        self.assertEqual(int(note["organization_id"]), int(self.default_organization["organization_id"]))
        self.assertEqual(int(note["author_user_id"]), int(self.admin["user_id"]))
        contractor_after = self.services["invoice_service"].get_contractor_detail(
            contractor_id,
            organization_id=int(self.default_organization["organization_id"]),
            viewer_user=self.admin,
        )
        self.assertIsNotNone(contractor_after)
        assert contractor_after is not None
        self.assertTrue(any(item["note_text"] == "Notatka CRM do kontrahenta." for item in contractor_after["notes"]))
        self.assertEqual(contractor_before["contractor"], contractor_after["contractor"])

        invoice_after = self.services["invoice_service"].get_invoice_detail(
            1,
            organization_id=int(self.default_organization["organization_id"]),
        )
        assert invoice_before is not None
        assert invoice_after is not None
        self.assertEqual(invoice_before["invoice"], invoice_after["invoice"])
        with get_connection() as connection:
            ledger_count_after = connection.execute("SELECT COUNT(*) AS count FROM billing_payer_ledger_entries").fetchone()[
                "count"
            ]
        self.assertEqual(ledger_count_before, ledger_count_after)

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

    def test_email_invoice_goes_to_verification_when_ocr_cannot_read_key_fields(self) -> None:
        invoice = self.services["invoice_service"].create_invoice(
            {
                "incoming_date": "2026-05-15",
                "source": "EMAIL",
                "file_name": "skan_z_maila.jpg",
                "document_type": "zdjecie",
                "invoice_number": "",
                "issuer_nip": "",
                "issuer_name": "",
                "issue_date": "",
                "sale_date": "",
                "gross_amount": None,
                "currency": "PLN",
                "source_external_id": "email-ocr-empty-2026-05-15",
                "source_sender_name": "faktury@dostawca.pl",
                "ocr_raw_text": "Nie udało się odczytać treści dokumentu lokalnym OCR.",
            },
            actor="test",
        )

        self.assertEqual(invoice["status"], "weryfikacja")
        self.assertEqual(
            invoice["flag_reason"],
            "Dokument z e-maila wymaga weryfikacji, ponieważ OCR nie odczytał kluczowych pól faktury.",
        )


    def test_batch_action_can_move_invoices_to_verification(self) -> None:
        result = self.services["invoice_service"].apply_batch_action([1, 5], "mark-verification", actor="test")
        self.assertEqual(result["updated_count"], 2)
        detail_one = self.services["invoice_service"].get_invoice_detail(1)
        detail_five = self.services["invoice_service"].get_invoice_detail(5)
        assert detail_one is not None
        assert detail_five is not None
        self.assertEqual(detail_one["invoice"]["status"], "weryfikacja")
        self.assertEqual(detail_five["invoice"]["status"], "weryfikacja")

    def test_batch_action_can_mark_invoice_as_correct(self) -> None:
        result = self.services["invoice_service"].apply_batch_action([4], "mark-correct", actor="test")
        self.assertEqual(result["updated_count"], 1)
        detail = self.services["invoice_service"].get_invoice_detail(4)
        assert detail is not None
        self.assertEqual(detail["invoice"]["status"], "poprawna")
        self.assertEqual(detail["invoice"]["duplicate_type"], "brak")

    def test_invoice_detail_exposes_field_provenance_and_duplicate_center(self) -> None:
        ksef_invoice = self.services["invoice_service"].create_invoice(
            {
                "incoming_date": "2026-05-25",
                "source": "KSeF",
                "file_name": "ksef_detail_origin_25_05_2026.xml",
                "document_type": "xml",
                "invoice_number": "FV/PROV/25/05/2026",
                "ksef_number": "KSEF-2026-PROV-25",
                "issuer_nip": "9123456780",
                "issuer_name": "Zrodlo KSeF Detail Sp. z o.o.",
                "issue_date": "2026-05-25",
                "sale_date": "2026-05-25",
                "gross_amount": 410.25,
                "currency": "PLN",
                "status": "nowa",
                "source_external_id": "ksef-provenance-2026-05-25",
            },
            actor="test",
        )
        self.services["invoice_service"].create_invoice(
            {
                "incoming_date": "2026-05-26",
                "source": "EMAIL",
                "file_name": "email_detail_origin_26_05_2026.pdf",
                "document_type": "pdf",
                "invoice_number": "FV/PROV/25/05/2026",
                "issuer_nip": "9123456780",
                "issuer_name": "Zrodlo pomocnicze z e-maila",
                "issue_date": "2026-05-25",
                "sale_date": "2026-05-25",
                "gross_amount": 410.25,
                "currency": "PLN",
                "status": "weryfikacja",
                "source_external_id": "email-provenance-2026-05-26",
            },
            actor="test",
        )

        detail = self.services["invoice_service"].get_invoice_detail(int(ksef_invoice["id"]))
        self.assertIsNotNone(detail)
        assert detail is not None

        provenance = {item["field_name"]: item for item in detail["field_provenance"]}
        self.assertIn("invoice_number", provenance)
        self.assertIn("gross_amount", provenance)
        self.assertTrue(provenance["invoice_number"]["is_ksef_protected"])
        self.assertEqual(provenance["invoice_number"]["source_label"], "Potwierdzone z KSeF")

        duplicate_center = detail["duplicate_center"]
        self.assertGreaterEqual(duplicate_center["candidate_count"], 1)
        self.assertTrue(any(item["invoice_number"] == "FV/PROV/25/05/2026" for item in duplicate_center["candidates"]))

    def test_verification_inbox_snapshot_groups_operational_invoice_queues(self) -> None:
        snapshot = self.services["invoice_service"].verification_inbox_snapshot(limit=3)

        self.assertIn("summary", snapshot)
        self.assertIn("sections", snapshot)
        self.assertEqual(
            set(snapshot["sections"].keys()),
            {"verification", "duplicates", "ksef_corrections", "ocr_attention"},
        )
        self.assertGreaterEqual(snapshot["summary"]["total_open_count"], 1)
        self.assertGreaterEqual(snapshot["sections"]["duplicates"]["count"], 1)
        self.assertIsInstance(snapshot["sections"]["verification"]["items"], list)

    def test_verification_workspace_snapshot_exposes_sla_counts_and_compare_targets(self) -> None:
        operator = self.auth_service.create_user(
            {
                "login": "workspace-operator",
                "display_name": "Workspace Operator",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": int(self.default_organization["organization_id"]),
            },
            actor_login="admin",
            actor_user_id=int(self.admin["user_id"]),
            actor_user=self.admin,
        )

        verification_invoice = self.services["invoice_service"].create_invoice(
            {
                "incoming_date": "2026-04-09",
                "source": "EMAIL",
                "file_name": "ocr_workspace_attention.pdf",
                "document_type": "pdf",
                "invoice_number": "FV/OCR/09/04/2026",
                "issuer_nip": "9998887776",
                "issuer_name": "OCR Attention Sp. z o.o.",
                "issue_date": "2026-04-09",
                "sale_date": "2026-04-09",
                "gross_amount": 321.45,
                "currency": "PLN",
                "status": "weryfikacja",
                "flag_reason": "Dokument z e-maila wymaga weryfikacji, poniewaz OCR nie odczytal kluczowych pol faktury.",
                "source_external_id": "workspace-ocr-2026-04-09",
            },
            actor="test",
            organization_id=int(self.default_organization["organization_id"]),
        )

        duplicate_original = self.services["invoice_service"].create_invoice(
            {
                "incoming_date": "2026-04-08",
                "source": "EMAIL",
                "file_name": "duplicate_workspace_a.pdf",
                "document_type": "pdf",
                "invoice_number": "FV/DUP/08/04/2026",
                "issuer_nip": "1231231239",
                "issuer_name": "Duplicate Workspace A",
                "issue_date": "2026-04-08",
                "sale_date": "2026-04-08",
                "gross_amount": 210.0,
                "currency": "PLN",
                "status": "nowa",
                "source_external_id": "workspace-dup-a",
            },
            actor="test",
            organization_id=int(self.default_organization["organization_id"]),
        )
        duplicate_candidate = self.services["invoice_service"].create_invoice(
            {
                "incoming_date": "2026-04-08",
                "source": "EMAIL",
                "file_name": "duplicate_workspace_b.pdf",
                "document_type": "pdf",
                "invoice_number": "FV/DUP/08/04/2026",
                "issuer_nip": "1231231239",
                "issuer_name": "Duplicate Workspace B",
                "issue_date": "2026-04-08",
                "sale_date": "2026-04-08",
                "gross_amount": 210.0,
                "currency": "PLN",
                "status": "nowa",
                "source_external_id": "workspace-dup-b",
            },
            actor="test",
            organization_id=int(self.default_organization["organization_id"]),
        )

        ksef_invoice = self.services["invoice_service"].create_invoice(
            {
                "incoming_date": "2026-04-07",
                "source": "KSeF",
                "file_name": "workspace_ksef.xml",
                "document_type": "xml",
                "invoice_number": "FV/KSEF/WORKSPACE/07/04/2026",
                "ksef_number": "KSEF-WORKSPACE-07",
                "issuer_nip": "4564564561",
                "issuer_name": "Workspace KSeF Sp. z o.o.",
                "issue_date": "2026-04-07",
                "sale_date": "2026-04-07",
                "gross_amount": 410.0,
                "currency": "PLN",
                "status": "nowa",
                "source_external_id": "workspace-ksef-07",
            },
            actor="test",
            organization_id=int(self.default_organization["organization_id"]),
        )

        correction_result = self.services["invoice_service"].update_invoice(
            int(ksef_invoice["id"]),
            {"gross_amount": "455.00"},
            actor="Workspace Operator",
            organization_id=int(self.default_organization["organization_id"]),
            actor_user=operator,
        )
        self.assertIsNotNone(correction_result)
        assert correction_result is not None
        self.assertEqual(correction_result["ksef_correction"]["mode"], "request_created")

        with get_connection() as connection:
            connection.execute(
                "UPDATE invoices SET updated_at = ? WHERE id IN (?, ?, ?)",
                (
                    "2026-04-10T09:00:00+00:00",
                    int(verification_invoice["id"]),
                    int(duplicate_original["id"]),
                    int(duplicate_candidate["id"]),
                ),
            )
            connection.execute(
                "UPDATE invoice_ksef_field_overrides SET created_at = ? WHERE invoice_id = ? AND status = ?",
                ("2026-04-11T09:00:00+00:00", int(ksef_invoice["id"]), "pending"),
            )

        snapshot = self.services["invoice_service"].verification_workspace_snapshot(
            active_bucket="duplicates",
            limit_per_bucket=10,
            organization_id=int(self.default_organization["organization_id"]),
        )

        self.assertEqual(snapshot["summary"]["active_bucket"], "duplicates")
        self.assertEqual(
            snapshot["bucket_order"],
            ["verification", "duplicates", "ksef_corrections", "ocr_attention"],
        )
        self.assertGreaterEqual(snapshot["summary"]["total_open_count"], 3)
        self.assertGreaterEqual(snapshot["summary"]["total_sla_breached"], 1)
        self.assertGreaterEqual(snapshot["sections"]["verification"]["sla_breached_count"], 1)
        self.assertGreaterEqual(snapshot["sections"]["ksef_corrections"]["sla_breached_count"], 1)
        self.assertTrue(
            any(item["sla_breached"] for item in snapshot["sections"]["ocr_attention"]["items"])
        )
        self.assertTrue(
            any(
                item["compare_target_invoice_id"] == int(duplicate_original["id"])
                for item in snapshot["sections"]["duplicates"]["items"]
                if int(item["invoice_id"]) == int(duplicate_candidate["id"])
            )
        )

    def test_compare_invoices_returns_field_level_rows_and_ksef_provenance(self) -> None:
        left_invoice = self.services["invoice_service"].create_invoice(
            {
                "incoming_date": "2026-05-02",
                "source": "KSeF",
                "file_name": "compare_left.xml",
                "document_type": "xml",
                "invoice_number": "FV/COMP/02/05/2026",
                "ksef_number": "KSEF-COMPARE-02",
                "issuer_nip": "7778889991",
                "issuer_name": "Compare Left Sp. z o.o.",
                "issue_date": "2026-05-02",
                "sale_date": "2026-05-02",
                "gross_amount": 500.0,
                "currency": "PLN",
                "status": "nowa",
                "source_external_id": "compare-left-02",
            },
            actor="test",
            organization_id=int(self.default_organization["organization_id"]),
        )
        right_invoice = self.services["invoice_service"].create_invoice(
            {
                "incoming_date": "2026-05-03",
                "source": "EMAIL",
                "file_name": "compare_right.pdf",
                "document_type": "pdf",
                "invoice_number": "FV/COMP/02/05/2026",
                "issuer_nip": "7778889991",
                "issuer_name": "Compare Right Sp. z o.o.",
                "issue_date": "2026-05-03",
                "sale_date": "2026-05-02",
                "gross_amount": 545.0,
                "currency": "PLN",
                "status": "weryfikacja",
                "flag_reason": "Wymaga porownania.",
                "source_external_id": "compare-right-03",
            },
            actor="test",
            organization_id=int(self.default_organization["organization_id"]),
        )

        comparison = self.services["invoice_service"].compare_invoices(
            int(left_invoice["id"]),
            int(right_invoice["id"]),
            organization_id=int(self.default_organization["organization_id"]),
        )

        self.assertIsNotNone(comparison)
        assert comparison is not None
        self.assertEqual(comparison["left_invoice"]["id"], int(left_invoice["id"]))
        self.assertEqual(comparison["right_invoice"]["id"], int(right_invoice["id"]))
        self.assertTrue(comparison["summary"]["same_invoice_number_and_nip"])
        self.assertFalse(comparison["summary"]["same_ksef_number"])
        self.assertEqual(len(comparison["rows"]), 8)

        gross_amount_row = next(row for row in comparison["rows"] if row["field_name"] == "gross_amount")
        self.assertFalse(gross_amount_row["matches"])
        self.assertTrue(gross_amount_row["left_is_ksef_protected"])
        self.assertEqual(gross_amount_row["left_source_label"], "Potwierdzone z KSeF")

        invoice_number_row = next(row for row in comparison["rows"] if row["field_name"] == "invoice_number")
        self.assertTrue(invoice_number_row["matches"])

    def test_ksef_becomes_authoritative_for_matching_lower_priority_invoice(self) -> None:
        email_invoice = self.services["invoice_service"].create_invoice(
            {
                "incoming_date": "2026-05-11",
                "source": "EMAIL",
                "file_name": "email_faktura_auth.pdf",
                "document_type": "pdf",
                "invoice_number": "FV/AUTH/11/05/2026",
                "issuer_nip": "1112223334",
                "issuer_name": "Dostawca roboczy z maila",
                "issue_date": "2026-05-11",
                "sale_date": "2026-05-11",
                "gross_amount": 199.99,
                "currency": "PLN",
                "status": "weryfikacja",
                "flag_reason": "Mail wymaga potwierdzenia.",
                "source_external_id": "email-auth-2026-05-11",
                "source_sender_name": "faktury@dostawca.pl",
                "notes": "Notatka operatora z maila.",
            },
            actor="test",
        )

        merged_invoice = self.services["invoice_service"].create_invoice(
            {
                "incoming_date": "2026-05-12",
                "source": "KSeF",
                "file_name": "ksef_auth_11_05_2026.xml",
                "document_type": "xml",
                "invoice_number": "FV/AUTH/11/05/2026",
                "ksef_number": "KSEF-2026-AUTH-11",
                "issuer_nip": "1112223334",
                "issuer_name": "Dostawca KSeF Sp. z o.o.",
                "issue_date": "2026-05-11",
                "sale_date": "2026-05-11",
                "gross_amount": 245.90,
                "currency": "PLN",
                "source_external_id": "ksef-auth-2026-05-11",
                "notes": "Notatka z KSeF nie powinna nadpisac notatek operatora.",
            },
            actor="test",
        )

        self.assertEqual(merged_invoice["id"], email_invoice["id"])

        detail = self.services["invoice_service"].get_invoice_detail(email_invoice["id"])
        self.assertIsNotNone(detail)
        assert detail is not None

        invoice = detail["invoice"]
        self.assertEqual(invoice["source"], "EMAIL")
        self.assertEqual(invoice["authoritative_source"], "KSeF")
        self.assertEqual(invoice["ksef_number"], "KSEF-2026-AUTH-11")
        self.assertEqual(invoice["issuer_name"], "Dostawca KSeF Sp. z o.o.")
        self.assertEqual(invoice["gross_amount"], 245.90)
        self.assertEqual(invoice["status"], "nowa")
        self.assertEqual(invoice["duplicate_type"], "brak")
        self.assertIsNone(invoice["flag_reason"])
        self.assertEqual(invoice["notes"], "Notatka operatora z maila.")
        self.assertEqual(detail["source_trace"]["authoritative_source"], "KSeF")
        self.assertEqual(detail["source_trace"]["metadata"]["original_source"], "EMAIL")
        self.assertEqual(detail["source_trace"]["metadata"]["authoritative_ksef_number"], "KSEF-2026-AUTH-11")

        matching = self.services["invoice_service"].list_invoices(
            {"invoice_number": "FV/AUTH/11/05/2026", "nip": "1112223334"}
        )
        self.assertEqual(len(matching), 1)

        logs = self.services["event_repository"].list_by_invoice(
            invoice["id"],
            organization_id=invoice["organization_id"],
        )
        self.assertTrue(
            any(item["event_type"] == "ksef_authority_applied" and item["source"] == "KSeF" for item in logs)
        )

    def test_operator_save_on_ksef_invoice_creates_correction_request_after_save(self) -> None:
        operator = self.auth_service.create_user(
            {
                "login": "ksef-operator",
                "display_name": "KSeF Operator",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": int(self.default_organization["organization_id"]),
            },
            actor_login="admin",
            actor_user_id=int(self.admin["user_id"]),
            actor_user=self.admin,
        )
        invoice = self.services["invoice_service"].create_invoice(
            {
                "incoming_date": "2026-05-20",
                "source": "KSeF",
                "file_name": "ksef_protected_20_05_2026.xml",
                "document_type": "xml",
                "invoice_number": "FV/KSEF/20/05/2026",
                "ksef_number": "KSEF-2026-PROTECTED-20",
                "issuer_nip": "1231231231",
                "issuer_name": "KSeF Dostawca Sp. z o.o.",
                "issue_date": "2026-05-20",
                "sale_date": "2026-05-20",
                "gross_amount": 100.0,
                "currency": "PLN",
                "status": "nowa",
                "source_external_id": "ksef-protected-2026-05-20",
                "notes": "Oryginalna notatka.",
            },
            actor="system",
            organization_id=int(self.default_organization["organization_id"]),
        )

        result = self.services["invoice_service"].update_invoice(
            int(invoice["id"]),
            {"gross_amount": "150.00", "notes": "Nowa notatka operatora."},
            actor="KSeF Operator",
            organization_id=int(self.default_organization["organization_id"]),
            actor_user=operator,
        )

        self.assertIsNotNone(result)
        assert result is not None
        self.assertIsNotNone(result["ksef_correction"])
        self.assertEqual(result["ksef_correction"]["mode"], "request_created")
        self.assertEqual(result["invoice"]["gross_amount"], 100.0)
        self.assertEqual(result["invoice"]["notes"], "Nowa notatka operatora.")

        detail = self.services["invoice_service"].get_invoice_detail(
            int(invoice["id"]),
            organization_id=int(self.default_organization["organization_id"]),
            viewer_user=operator,
        )
        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertEqual(detail["invoice"]["gross_amount"], 100.0)
        self.assertEqual(detail["invoice"]["notes"], "Nowa notatka operatora.")
        self.assertEqual(detail["ksef_corrections"]["active_local_values"], {})
        self.assertEqual(len(detail["ksef_corrections"]["pending"]), 1)
        pending = detail["ksef_corrections"]["pending"][0]
        self.assertEqual(pending["field_name"], "gross_amount")
        self.assertEqual(pending["source_value"], "100.00")
        self.assertEqual(pending["local_value"], "150.00")
        self.assertEqual(len(detail["approval_requests"]), 1)
        self.assertEqual(detail["approval_requests"][0]["status"], "pending")
        self.assertFalse(detail["approval_requests"][0]["can_decide"])

    def test_approved_ksef_correction_keeps_original_value_and_applies_local_value(self) -> None:
        org_admin = self.auth_service.create_user(
            {
                "login": "ksef-admin",
                "display_name": "KSeF Admin",
                "password": "1234",
                "role": "organization_admin",
                "is_active": 1,
                "organization_id": int(self.default_organization["organization_id"]),
            },
            actor_login="admin",
            actor_user_id=int(self.admin["user_id"]),
            actor_user=self.admin,
        )
        operator = self.auth_service.create_user(
            {
                "login": "ksef-operator-2",
                "display_name": "KSeF Operator 2",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": int(self.default_organization["organization_id"]),
            },
            actor_login="admin",
            actor_user_id=int(self.admin["user_id"]),
            actor_user=self.admin,
        )
        invoice = self.services["invoice_service"].create_invoice(
            {
                "incoming_date": "2026-05-21",
                "source": "KSeF",
                "file_name": "ksef_protected_21_05_2026.xml",
                "document_type": "xml",
                "invoice_number": "FV/KSEF/21/05/2026",
                "ksef_number": "KSEF-2026-PROTECTED-21",
                "issuer_nip": "3213213210",
                "issuer_name": "KSeF Zrodlo Sp. z o.o.",
                "issue_date": "2026-05-21",
                "sale_date": "2026-05-21",
                "gross_amount": 100.0,
                "currency": "PLN",
                "status": "nowa",
                "source_external_id": "ksef-protected-2026-05-21",
            },
            actor="system",
            organization_id=int(self.default_organization["organization_id"]),
        )

        result = self.services["invoice_service"].update_invoice(
            int(invoice["id"]),
            {"gross_amount": "150.00"},
            actor="KSeF Operator 2",
            organization_id=int(self.default_organization["organization_id"]),
            actor_user=operator,
        )
        assert result is not None
        correction = result["ksef_correction"]
        self.assertIsNotNone(correction)
        assert correction is not None

        approved = self.approval_service.decide_request(
            int(correction["request_id"]),
            decision="approve",
            actor_user=org_admin,
            actor="KSeF Admin",
            reason="Akceptuje lokalna korekte.",
        )
        self.assertEqual(approved["status"], "approved")

        detail = self.services["invoice_service"].get_invoice_detail(
            int(invoice["id"]),
            organization_id=int(self.default_organization["organization_id"]),
            viewer_user=org_admin,
        )
        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertEqual(detail["invoice"]["gross_amount"], 150.0)
        self.assertEqual(detail["ksef_corrections"]["authoritative_values"]["gross_amount"], "100.00")
        self.assertEqual(detail["ksef_corrections"]["active_local_values"]["gross_amount"], 150.0)
        self.assertTrue(
            any(
                item["field_name"] == "gross_amount"
                and item["local_value"] == "150.00"
                and item["status"] == "approved"
                for item in detail["ksef_corrections"]["approved"]
            )
        )
        self.assertTrue(
            any(item["event_type"] == "ksef_correction_applied" for item in detail["history"])
        )

    def test_active_delegate_can_approve_ksef_correction_for_organization(self) -> None:
        operator = self.auth_service.create_user(
            {
                "login": "ksef-operator-3",
                "display_name": "KSeF Operator 3",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": int(self.default_organization["organization_id"]),
            },
            actor_login="admin",
            actor_user_id=int(self.admin["user_id"]),
            actor_user=self.admin,
        )
        delegate = self.auth_service.create_user(
            {
                "login": "ksef-delegate",
                "display_name": "KSeF Delegate",
                "password": "1234",
                "role": "coordinator",
                "is_active": 1,
                "organization_id": int(self.default_organization["organization_id"]),
            },
            actor_login="admin",
            actor_user_id=int(self.admin["user_id"]),
            actor_user=self.admin,
        )
        self.organization_service.update_organization(
            int(self.default_organization["organization_id"]),
            {
                "ksef_correction_delegate_user_id": delegate["user_id"],
                "ksef_correction_delegate_expires_at": "2026-12-31T23:59",
            },
            actor_user=self.admin,
            actor_login="admin",
        )
        invoice = self.services["invoice_service"].create_invoice(
            {
                "incoming_date": "2026-05-22",
                "source": "KSeF",
                "file_name": "ksef_protected_22_05_2026.xml",
                "document_type": "xml",
                "invoice_number": "FV/KSEF/22/05/2026",
                "ksef_number": "KSEF-2026-PROTECTED-22",
                "issuer_nip": "4564564564",
                "issuer_name": "KSeF Korekta Sp. z o.o.",
                "issue_date": "2026-05-22",
                "sale_date": "2026-05-22",
                "gross_amount": 210.0,
                "currency": "PLN",
                "status": "nowa",
                "source_external_id": "ksef-protected-2026-05-22",
            },
            actor="system",
            organization_id=int(self.default_organization["organization_id"]),
        )

        result = self.services["invoice_service"].update_invoice(
            int(invoice["id"]),
            {"gross_amount": "222.00"},
            actor="KSeF Operator 3",
            organization_id=int(self.default_organization["organization_id"]),
            actor_user=operator,
        )
        assert result is not None
        correction = result["ksef_correction"]
        self.assertIsNotNone(correction)
        assert correction is not None
        self.assertEqual(correction["requested_user_id"], delegate["user_id"])

        detail_before = self.services["invoice_service"].get_invoice_detail(
            int(invoice["id"]),
            organization_id=int(self.default_organization["organization_id"]),
            viewer_user=delegate,
        )
        self.assertIsNotNone(detail_before)
        assert detail_before is not None
        self.assertTrue(detail_before["approval_requests"][0]["can_decide"])

        approved = self.approval_service.decide_request(
            int(correction["request_id"]),
            decision="approve",
            actor_user=delegate,
            actor="KSeF Delegate",
            reason="Delegacja tymczasowa.",
        )
        self.assertEqual(approved["status"], "approved")

        detail_after = self.services["invoice_service"].get_invoice_detail(
            int(invoice["id"]),
            organization_id=int(self.default_organization["organization_id"]),
            viewer_user=delegate,
        )
        self.assertIsNotNone(detail_after)
        assert detail_after is not None
        self.assertEqual(detail_after["invoice"]["gross_amount"], 222.0)
        self.assertEqual(detail_after["ksef_corrections"]["authoritative_values"]["gross_amount"], "210.00")
        self.assertEqual(detail_after["ksef_corrections"]["active_local_values"]["gross_amount"], 222.0)

    def test_invoice_can_be_assigned_to_active_user_in_same_organization(self) -> None:
        coordinator = self.auth_service.create_user(
            {
                "login": "invoice-owner",
                "display_name": "Invoice Owner",
                "password": "1234",
                "role": "coordinator",
                "is_active": 1,
                "organization_id": int(self.default_organization["organization_id"]),
            },
            actor_login="admin",
            actor_user_id=int(self.admin["user_id"]),
            actor_user=self.admin,
        )

        result = self.services["invoice_service"].update_invoice(
            1,
            {"assigned_user_id": coordinator["user_id"]},
            actor="Admin",
            organization_id=int(self.default_organization["organization_id"]),
            actor_user=self.admin,
        )
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["invoice"]["assigned_user_id"], coordinator["user_id"])
        self.assertEqual(result["invoice"]["assigned_user_name"], "Invoice Owner")

        detail = self.services["invoice_service"].get_invoice_detail(1, organization_id=int(self.default_organization["organization_id"]))
        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertTrue(any(item["event_type"] == "invoice_assigned" for item in detail["history"]))

    def test_invoice_assignment_rejects_user_from_other_organization(self) -> None:
        other_org = self.organization_service.create_organization(
            {"name": "Other Org", "slug": "other-org", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        outsider = self.auth_service.create_user(
            {
                "login": "other-org-user",
                "display_name": "Other Org User",
                "password": "1234",
                "role": "coordinator",
                "is_active": 1,
                "organization_id": int(other_org["organization_id"]),
            },
            actor_login="admin",
            actor_user_id=int(self.admin["user_id"]),
            actor_user=self.admin,
        )

        with self.assertRaisesRegex(ValueError, "Nie mozna przypisac odpowiedzialnego z innej organizacji."):
            self.services["invoice_service"].update_invoice(
                1,
                {"assigned_user_id": outsider["user_id"]},
                actor="Admin",
                organization_id=int(self.default_organization["organization_id"]),
                actor_user=self.admin,
            )

    def test_invoice_comment_is_added_and_visible_in_detail(self) -> None:
        comment = self.services["invoice_service"].add_invoice_comment(
            1,
            "Sprawdzic zgodnosc numeru z dokumentem zrodlowym.",
            actor_user=self.admin,
            actor="Administrator",
            organization_id=int(self.default_organization["organization_id"]),
        )

        self.assertEqual(comment["created_by_user_name"], self.admin["display_name"])
        detail = self.services["invoice_service"].get_invoice_detail(1, organization_id=int(self.default_organization["organization_id"]))
        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertTrue(any("Sprawdzic zgodnosc numeru" in item["note_text"] for item in detail["comments"]))
        self.assertTrue(any(item["event_type"] == "invoice_comment_added" for item in detail["history"]))
        comment_events = [item for item in detail["history"] if item["event_type"] == "invoice_comment_added"]
        self.assertTrue(comment_events)
        self.assertFalse(any("note_text" in (item.get("details") or {}) for item in comment_events))
        self.assertTrue(any("note_length" in (item.get("details") or {}) for item in comment_events))

    def test_invoice_comment_history_redacts_legacy_note_text_details(self) -> None:
        self.services["event_repository"].log(
            event_type="invoice_comment_added",
            invoice_id=1,
            organization_id=int(self.default_organization["organization_id"]),
            source="MANUAL",
            status_before="nowa",
            status_after="nowa",
            decision_reason="Starszy event komentarza.",
            actor="legacy",
            details={
                "invoice_comment_id": 999,
                "note_text": "Starsza tresc komentarza nie moze wyciec w historii.",
            },
        )

        detail = self.services["invoice_service"].get_invoice_detail(
            1,
            organization_id=int(self.default_organization["organization_id"]),
        )
        self.assertIsNotNone(detail)
        assert detail is not None
        legacy_events = [
            item
            for item in detail["history"]
            if item["event_type"] == "invoice_comment_added"
            and (item.get("details") or {}).get("invoice_comment_id") == 999
        ]
        self.assertTrue(legacy_events)
        self.assertFalse(any("note_text" in (item.get("details") or {}) for item in legacy_events))
        self.assertTrue(any("note_length" in (item.get("details") or {}) for item in legacy_events))

    def test_verification_workspace_item_exposes_assignee_and_comment_count(self) -> None:
        coordinator = self.auth_service.create_user(
            {
                "login": "verification-owner",
                "display_name": "Verification Owner",
                "password": "1234",
                "role": "coordinator",
                "is_active": 1,
                "organization_id": int(self.default_organization["organization_id"]),
            },
            actor_login="admin",
            actor_user_id=int(self.admin["user_id"]),
            actor_user=self.admin,
        )
        self.services["invoice_service"].update_invoice(
            4,
            {"assigned_user_id": coordinator["user_id"]},
            actor="Admin",
            organization_id=int(self.default_organization["organization_id"]),
            actor_user=self.admin,
        )
        self.services["invoice_service"].add_invoice_comment(
            4,
            "To wyglada na duplikat i czeka na decyzje.",
            actor_user=self.admin,
            actor="Administrator",
            organization_id=int(self.default_organization["organization_id"]),
        )

        snapshot = self.services["invoice_service"].verification_workspace_snapshot(
            organization_id=int(self.default_organization["organization_id"]),
            active_bucket="duplicates",
            limit_per_bucket=10,
        )
        items = snapshot["sections"]["duplicates"]["items"]
        duplicate_item = next(item for item in items if int(item["invoice_id"]) == 4)
        self.assertEqual(duplicate_item["assigned_user_name"], "Verification Owner")
        self.assertEqual(int(duplicate_item["invoice_comment_count"]), 1)

    def test_invoice_workflow_can_be_prepared_handed_off_and_reopened(self) -> None:
        operator = self.auth_service.create_user(
            {
                "login": "workflow-operator",
                "display_name": "Workflow Operator",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": int(self.default_organization["organization_id"]),
            },
            actor_login="admin",
            actor_user_id=int(self.admin["user_id"]),
            actor_user=self.admin,
        )
        coordinator = self.auth_service.create_user(
            {
                "login": "workflow-coordinator",
                "display_name": "Workflow Coordinator",
                "password": "1234",
                "role": "coordinator",
                "is_active": 1,
                "organization_id": int(self.default_organization["organization_id"]),
            },
            actor_login="admin",
            actor_user_id=int(self.admin["user_id"]),
            actor_user=self.admin,
        )

        ready_invoice = self.services["invoice_service"].mark_invoice_ready_for_handoff(
            1,
            actor_user=operator,
            actor="Workflow Operator",
            organization_id=int(self.default_organization["organization_id"]),
            handoff_target="Ksiegowosc",
            handoff_note="Gotowe do przekazania po weryfikacji.",
        )
        assert ready_invoice is not None
        self.assertEqual(ready_invoice["workflow_state"], "gotowa_do_przekazania")
        self.assertEqual(ready_invoice["handoff_target"], "Ksiegowosc")

        handed_off_invoice = self.services["invoice_service"].handoff_invoice(
            1,
            actor_user=coordinator,
            actor="Workflow Coordinator",
            organization_id=int(self.default_organization["organization_id"]),
            handoff_target="Ksiegowosc",
            handoff_note="Przekazano do dalszej obslugi.",
        )
        assert handed_off_invoice is not None
        self.assertEqual(handed_off_invoice["workflow_state"], "przekazana")
        self.assertIsNotNone(handed_off_invoice["handed_off_at"])

        reopened_invoice = self.services["invoice_service"].reopen_invoice(
            1,
            actor_user=coordinator,
            actor="Workflow Coordinator",
            organization_id=int(self.default_organization["organization_id"]),
            reason="Wrocila uwaga z ksiegowosci.",
        )
        assert reopened_invoice is not None
        self.assertEqual(reopened_invoice["workflow_state"], "w_pracy")
        self.assertEqual(reopened_invoice["reopen_reason"], "Wrocila uwaga z ksiegowosci.")

        detail = self.services["invoice_service"].get_invoice_detail(
            1,
            organization_id=int(self.default_organization["organization_id"]),
            viewer_user=coordinator,
        )
        assert detail is not None
        self.assertEqual(detail["workflow"]["state"], "w_pracy")
        self.assertEqual(detail["workflow"]["state_label"], "W pracy")
        self.assertTrue(detail["workflow"]["can_handoff"])
        self.assertTrue(any(item["event_type"] == "invoice_handed_off" for item in detail["history"]))
        self.assertTrue(any(item["event_type"] == "invoice_reopened" for item in detail["history"]))

    def test_invoice_preview_returns_lightweight_payload_and_preview_kind(self) -> None:
        created = self.services["invoice_service"].create_invoice(
            {
                "incoming_date": "2026-06-02",
                "source": "EMAIL",
                "file_name": "preview_invoice.pdf",
                "document_type": "pdf",
                "invoice_number": "PREVIEW/06/2026",
                "issuer_nip": "1020304050",
                "issuer_name": "Preview Test Sp. z o.o.",
                "issue_date": "2026-06-02",
                "sale_date": "2026-06-02",
                "gross_amount": 123.45,
                "currency": "PLN",
                "status": "nowa",
                "source_external_id": "preview-endpoint-2026-06-02",
                "ocr_raw_text": "Preview OCR text invoice number PREVIEW/06/2026 with issuer Preview Test Sp. z o.o.",
            },
            actor="test",
            organization_id=int(self.default_organization["organization_id"]),
        )

        preview = self.services["invoice_service"].get_invoice_preview(
            int(created["id"]),
            organization_id=int(self.default_organization["organization_id"]),
            viewer_user=self.admin,
        )
        self.assertIsNotNone(preview)
        assert preview is not None
        self.assertEqual(int(preview["invoice"]["id"]), int(created["id"]))
        self.assertEqual(preview["document_trace"]["preview_kind"], "pdf")
        self.assertIn("Preview OCR text", preview["ocr_excerpt"])
        self.assertIsInstance(preview["field_provenance"], list)

    def test_invoice_workflow_payload_exposes_undo_for_latest_reversible_action(self) -> None:
        operator = self.auth_service.create_user(
            {
                "login": "workflow-undo-operator",
                "display_name": "Workflow Undo Operator",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": int(self.default_organization["organization_id"]),
            },
            actor_login="admin",
            actor_user_id=int(self.admin["user_id"]),
            actor_user=self.admin,
        )

        self.services["invoice_service"].mark_invoice_ready_for_handoff(
            1,
            actor_user=operator,
            actor="Workflow Undo Operator",
            organization_id=int(self.default_organization["organization_id"]),
            handoff_target="Ksiegowosc",
            handoff_note="Do cofniecia w tescie.",
        )

        detail = self.services["invoice_service"].get_invoice_detail(
            1,
            organization_id=int(self.default_organization["organization_id"]),
            viewer_user=operator,
        )
        assert detail is not None
        self.assertTrue(detail["workflow"]["undo"]["available"])
        self.assertEqual(detail["workflow"]["undo"]["event_type"], "invoice_ready_for_handoff")
        self.assertEqual(detail["workflow"]["undo"]["target_state"], "w_pracy")

    def test_invoice_workflow_undo_reverts_last_action_and_logs_event(self) -> None:
        operator = self.auth_service.create_user(
            {
                "login": "workflow-undo-revert",
                "display_name": "Workflow Undo Revert",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": int(self.default_organization["organization_id"]),
            },
            actor_login="admin",
            actor_user_id=int(self.admin["user_id"]),
            actor_user=self.admin,
        )

        self.services["invoice_service"].mark_invoice_ready_for_handoff(
            1,
            actor_user=operator,
            actor="Workflow Undo Revert",
            organization_id=int(self.default_organization["organization_id"]),
            handoff_target="Ksiegowosc",
            handoff_note="Do cofniecia w tescie.",
        )

        reverted = self.services["invoice_service"].undo_last_invoice_workflow_decision(
            1,
            actor_user=operator,
            actor="Workflow Undo Revert",
            organization_id=int(self.default_organization["organization_id"]),
        )
        self.assertEqual(reverted["workflow_state"], "w_pracy")
        self.assertIsNone(reverted["ready_for_handoff_at"])

        detail = self.services["invoice_service"].get_invoice_detail(
            1,
            organization_id=int(self.default_organization["organization_id"]),
            viewer_user=operator,
        )
        assert detail is not None
        self.assertEqual(detail["workflow"]["state"], "w_pracy")
        self.assertFalse(detail["workflow"]["undo"]["available"])
        self.assertTrue(any(item["event_type"] == "invoice_workflow_undone" for item in detail["history"]))

    def test_invoice_workflow_undo_of_handoff_restores_ready_state(self) -> None:
        operator = self.auth_service.create_user(
            {
                "login": "workflow-undo-handoff-operator",
                "display_name": "Workflow Undo Handoff Operator",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": int(self.default_organization["organization_id"]),
            },
            actor_login="admin",
            actor_user_id=int(self.admin["user_id"]),
            actor_user=self.admin,
        )
        coordinator = self.auth_service.create_user(
            {
                "login": "workflow-undo-handoff-coordinator",
                "display_name": "Workflow Undo Handoff Coordinator",
                "password": "1234",
                "role": "coordinator",
                "is_active": 1,
                "organization_id": int(self.default_organization["organization_id"]),
            },
            actor_login="admin",
            actor_user_id=int(self.admin["user_id"]),
            actor_user=self.admin,
        )

        self.services["invoice_service"].mark_invoice_ready_for_handoff(
            1,
            actor_user=operator,
            actor="Workflow Undo Handoff Operator",
            organization_id=int(self.default_organization["organization_id"]),
            handoff_target="Ksiegowosc",
            handoff_note="Etap gotowosci.",
        )
        self.services["invoice_service"].handoff_invoice(
            1,
            actor_user=coordinator,
            actor="Workflow Undo Handoff Coordinator",
            organization_id=int(self.default_organization["organization_id"]),
            handoff_target="Ksiegowosc",
            handoff_note="Etap przekazania.",
        )

        reverted = self.services["invoice_service"].undo_last_invoice_workflow_decision(
            1,
            actor_user=coordinator,
            actor="Workflow Undo Handoff Coordinator",
            organization_id=int(self.default_organization["organization_id"]),
        )
        self.assertEqual(reverted["workflow_state"], "gotowa_do_przekazania")
        self.assertIsNone(reverted["handed_off_at"])
        self.assertIsNotNone(reverted["ready_for_handoff_at"])

    def test_invoice_handoff_requires_decision_role(self) -> None:
        operator = self.auth_service.create_user(
            {
                "login": "workflow-no-decision",
                "display_name": "Workflow No Decision",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": int(self.default_organization["organization_id"]),
            },
            actor_login="admin",
            actor_user_id=int(self.admin["user_id"]),
            actor_user=self.admin,
        )

        with self.assertRaisesRegex(PermissionError, "nie moze przekazac faktury dalej"):
            self.services["invoice_service"].handoff_invoice(
                1,
                actor_user=operator,
                actor="Workflow Operator",
                organization_id=int(self.default_organization["organization_id"]),
                handoff_target="Ksiegowosc",
            )

    def test_invoice_list_can_filter_by_workflow_state(self) -> None:
        self.services["invoice_service"].mark_invoice_ready_for_handoff(
            1,
            actor_user=self.admin,
            actor="Administrator",
            organization_id=int(self.default_organization["organization_id"]),
            handoff_target="Ksiegowosc",
        )

        invoices = self.services["invoice_service"].list_invoices(
            {"workflow_state": "gotowa_do_przekazania"},
            organization_id=int(self.default_organization["organization_id"]),
        )
        self.assertTrue(invoices)
        self.assertTrue(all(item["workflow_state"] == "gotowa_do_przekazania" for item in invoices))
        self.assertTrue(any(int(item["id"]) == 1 for item in invoices))

    def test_document_intake_snapshot_exposes_linked_invoice_and_status_counts(self) -> None:
        created = self.services["invoice_service"].create_invoice(
            {
                "incoming_date": "2026-04-16",
                "source": "EMAIL",
                "file_name": "intake_snapshot_service.pdf",
                "document_type": "pdf",
                "invoice_number": "INTAKE/SVC/16/04/2026",
                "issuer_nip": "1002003004",
                "issuer_name": "Intake Service Sp. z o.o.",
                "issue_date": "2026-04-16",
                "sale_date": "2026-04-16",
                "gross_amount": 256.40,
                "currency": "PLN",
                "status": "nowa",
                "source_external_id": "intake-service-2026-04-16",
            },
            actor="test",
            organization_id=int(self.default_organization["organization_id"]),
        )

        snapshot = self.services["invoice_service"].document_intake_snapshot(
            organization_id=int(self.default_organization["organization_id"]),
            limit=30,
        )

        self.assertIn("summary", snapshot)
        self.assertIn("items", snapshot)
        self.assertGreaterEqual(int(snapshot["summary"]["count"]), 1)
        self.assertGreaterEqual(int(snapshot["summary"]["counts_by_status"]["nowe"]), 1)
        intake_item = next(
            item for item in snapshot["items"] if int(item.get("linked_invoice_id") or 0) == int(created["id"])
        )
        self.assertEqual(intake_item["linked_invoice"]["invoice_number"], "INTAKE/SVC/16/04/2026")
        self.assertEqual(intake_item["status"], "nowe")

    def test_exception_center_snapshot_groups_invoice_operational_exceptions(self) -> None:
        created = self.services["invoice_service"].create_invoice(
            {
                "incoming_date": "2026-04-16",
                "source": "EMAIL",
                "file_name": "exception_snapshot_service.jpg",
                "document_type": "zdjecie",
                "invoice_number": "EXC/SVC/16/04/2026",
                "issuer_nip": "2003004005",
                "issuer_name": "Exception Service Sp. z o.o.",
                "issue_date": "2026-04-16",
                "sale_date": "2026-04-16",
                "gross_amount": 71.00,
                "currency": "PLN",
                "status": "weryfikacja",
                "flag_reason": "Dokument z e-maila wymaga weryfikacji, poniewaz OCR nie odczytal kluczowych pol faktury.",
                "source_external_id": "exception-service-2026-04-16",
            },
            actor="test",
            organization_id=int(self.default_organization["organization_id"]),
        )
        self.services["invoice_service"].update_invoice(
            int(created["id"]),
            {"contractor_id": None},
            actor="test",
            organization_id=int(self.default_organization["organization_id"]),
            actor_user=self.admin,
        )

        snapshot = self.services["invoice_service"].exception_center_snapshot(
            organization_id=int(self.default_organization["organization_id"]),
            limit=30,
        )

        self.assertIn("summary", snapshot)
        self.assertIn("items", snapshot)
        self.assertGreaterEqual(int(snapshot["summary"]["count"]), 1)
        self.assertIn("missing_contractor", snapshot["summary"]["counts_by_code"])
        self.assertIn("weak_ocr", snapshot["summary"]["counts_by_code"])
        related_items = [
            item for item in snapshot["items"] if int(item.get("linked_invoice_id") or 0) == int(created["id"])
        ]
        self.assertTrue(any(item["source_reference"] == "missing_contractor" for item in related_items))
        self.assertTrue(any(item["source_reference"] == "weak_ocr" for item in related_items))

    def test_handoff_batch_can_be_created_and_exported_with_invoice_history(self) -> None:
        first_invoice = self.services["invoice_service"].create_invoice(
            {
                "incoming_date": "2026-04-16",
                "source": "EMAIL",
                "file_name": "handoff_service_1.pdf",
                "document_type": "pdf",
                "invoice_number": "HANDOFF/SVC/1/16/04/2026",
                "issuer_nip": "3004005006",
                "issuer_name": "Handoff Service One",
                "issue_date": "2026-04-16",
                "sale_date": "2026-04-16",
                "gross_amount": 111.00,
                "currency": "PLN",
                "status": "nowa",
                "source_external_id": "handoff-service-1-2026-04-16",
            },
            actor="test",
            organization_id=int(self.default_organization["organization_id"]),
        )
        second_invoice = self.services["invoice_service"].create_invoice(
            {
                "incoming_date": "2026-04-16",
                "source": "TELEGRAM",
                "file_name": "handoff_service_2.pdf",
                "document_type": "pdf",
                "invoice_number": "HANDOFF/SVC/2/16/04/2026",
                "issuer_nip": "3004005007",
                "issuer_name": "Handoff Service Two",
                "issue_date": "2026-04-16",
                "sale_date": "2026-04-16",
                "gross_amount": 222.00,
                "currency": "PLN",
                "status": "nowa",
                "source_external_id": "handoff-service-2-2026-04-16",
            },
            actor="test",
            organization_id=int(self.default_organization["organization_id"]),
        )

        batch_detail = self.services["invoice_service"].create_handoff_batch(
            [int(first_invoice["id"]), int(second_invoice["id"])],
            handoff_target="Biuro rachunkowe",
            note="Pakiet testowy do eksportu.",
            actor_user=self.admin,
            actor="Administrator",
            organization_id=int(self.default_organization["organization_id"]),
        )

        self.assertEqual(batch_detail["batch"]["handoff_target"], "Biuro rachunkowe")
        self.assertEqual(len(batch_detail["items"]), 2)
        self.assertTrue(all(item["current_workflow_state"] == "przekazana" for item in batch_detail["items"]))

        listed = self.services["invoice_service"].list_handoff_batches(
            organization_id=int(self.default_organization["organization_id"]),
            limit=10,
        )
        self.assertGreaterEqual(int(listed["summary"]["count"]), 1)
        self.assertTrue(
            any(
                int(item["invoice_handoff_batch_id"]) == int(batch_detail["batch"]["invoice_handoff_batch_id"])
                for item in listed["batches"]
            )
        )

        exported = self.services["invoice_service"].export_handoff_batch_csv(
            int(batch_detail["batch"]["invoice_handoff_batch_id"]),
            actor_user=self.admin,
            actor="Administrator",
            organization_id=int(self.default_organization["organization_id"]),
        )
        self.assertIn("BatchNumber;InvoiceId;InvoiceNumber", exported["csv_content"])
        self.assertIn("HANDOFF/SVC/1/16/04/2026", exported["csv_content"])
        self.assertEqual(exported["batch"]["status"], "wyeksportowana")

    def test_invoice_can_be_closed_after_handoff_and_keeps_closed_metadata(self) -> None:
        created = self.services["invoice_service"].create_invoice(
            {
                "incoming_date": "2026-04-16",
                "source": "EMAIL",
                "file_name": "close_service.pdf",
                "document_type": "pdf",
                "invoice_number": "CLOSE/SVC/16/04/2026",
                "issuer_nip": "4005006007",
                "issuer_name": "Close Service Sp. z o.o.",
                "issue_date": "2026-04-16",
                "sale_date": "2026-04-16",
                "gross_amount": 444.00,
                "currency": "PLN",
                "status": "nowa",
                "source_external_id": "close-service-2026-04-16",
            },
            actor="test",
            organization_id=int(self.default_organization["organization_id"]),
        )

        self.services["invoice_service"].handoff_invoice(
            int(created["id"]),
            actor_user=self.admin,
            actor="Administrator",
            organization_id=int(self.default_organization["organization_id"]),
            handoff_target="Ksiegowosc",
            handoff_note="Zamkniecie po przekazaniu.",
        )
        closed = self.services["invoice_service"].close_invoice(
            int(created["id"]),
            actor_user=self.admin,
            actor="Administrator",
            organization_id=int(self.default_organization["organization_id"]),
            reason="Dokument rozliczony i zamkniety.",
        )

        self.assertIsNotNone(closed)
        assert closed is not None
        self.assertEqual(closed["workflow_state"], "zamknieta")
        self.assertEqual(closed["closed_reason"], "Dokument rozliczony i zamkniety.")
        self.assertIsNotNone(closed["closed_at"])

        detail = self.services["invoice_service"].get_invoice_detail(
            int(created["id"]),
            organization_id=int(self.default_organization["organization_id"]),
            viewer_user=self.admin,
        )
        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertEqual(detail["workflow"]["state"], "zamknieta")
        self.assertEqual(detail["workflow"]["closed_reason"], "Dokument rozliczony i zamkniety.")
        self.assertEqual(detail["document_intake_items"][0]["status"], "zakonczone")
        self.assertTrue(any(item["event_type"] == "invoice_closed" for item in detail["history"]))


if __name__ == "__main__":
    unittest.main()
