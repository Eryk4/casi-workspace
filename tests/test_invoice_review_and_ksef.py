from __future__ import annotations

from tests.invoice_test_methods import InvoiceMvpTests
from tests.invoice_test_support import InvoiceMvpTestCase


class InvoiceReviewAndKsefTests(InvoiceMvpTestCase):
    test_invoice_detail_exposes_field_provenance_and_duplicate_center = (
        InvoiceMvpTests.test_invoice_detail_exposes_field_provenance_and_duplicate_center
    )
    test_verification_inbox_snapshot_groups_operational_invoice_queues = (
        InvoiceMvpTests.test_verification_inbox_snapshot_groups_operational_invoice_queues
    )
    test_verification_workspace_snapshot_exposes_sla_counts_and_compare_targets = (
        InvoiceMvpTests.test_verification_workspace_snapshot_exposes_sla_counts_and_compare_targets
    )
    test_compare_invoices_returns_field_level_rows_and_ksef_provenance = (
        InvoiceMvpTests.test_compare_invoices_returns_field_level_rows_and_ksef_provenance
    )
    test_ksef_becomes_authoritative_for_matching_lower_priority_invoice = (
        InvoiceMvpTests.test_ksef_becomes_authoritative_for_matching_lower_priority_invoice
    )
    test_operator_save_on_ksef_invoice_creates_correction_request_after_save = (
        InvoiceMvpTests.test_operator_save_on_ksef_invoice_creates_correction_request_after_save
    )
    test_approved_ksef_correction_keeps_original_value_and_applies_local_value = (
        InvoiceMvpTests.test_approved_ksef_correction_keeps_original_value_and_applies_local_value
    )
    test_active_delegate_can_approve_ksef_correction_for_organization = (
        InvoiceMvpTests.test_active_delegate_can_approve_ksef_correction_for_organization
    )


del InvoiceMvpTestCase
del InvoiceMvpTests
