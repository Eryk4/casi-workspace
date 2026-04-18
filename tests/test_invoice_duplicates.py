from __future__ import annotations

from tests.invoice_test_methods import InvoiceMvpTests
from tests.invoice_test_support import InvoiceMvpTestCase


class InvoiceDuplicateTests(InvoiceMvpTestCase):
    test_seed_creates_expected_records = InvoiceMvpTests.test_seed_creates_expected_records
    test_certain_duplicate_is_detected_by_ksef = InvoiceMvpTests.test_certain_duplicate_is_detected_by_ksef
    test_suspected_duplicate_is_detected_by_number_and_nip = (
        InvoiceMvpTests.test_suspected_duplicate_is_detected_by_number_and_nip
    )
    test_new_contractor_stays_marked_as_new = InvoiceMvpTests.test_new_contractor_stays_marked_as_new
    test_rejecting_duplicate_clears_flag = InvoiceMvpTests.test_rejecting_duplicate_clears_flag
    test_manual_duplicate_actions_always_refresh_verification_description = (
        InvoiceMvpTests.test_manual_duplicate_actions_always_refresh_verification_description
    )
    test_repeated_test_import_shows_human_duplicate_message = (
        InvoiceMvpTests.test_repeated_test_import_shows_human_duplicate_message
    )
    test_email_invoice_goes_to_verification_when_ocr_cannot_read_key_fields = (
        InvoiceMvpTests.test_email_invoice_goes_to_verification_when_ocr_cannot_read_key_fields
    )
    test_batch_action_can_move_invoices_to_verification = (
        InvoiceMvpTests.test_batch_action_can_move_invoices_to_verification
    )
    test_batch_action_can_mark_invoice_as_correct = InvoiceMvpTests.test_batch_action_can_mark_invoice_as_correct


del InvoiceMvpTestCase
del InvoiceMvpTests
