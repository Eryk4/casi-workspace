from __future__ import annotations

from tests.invoice_test_methods import InvoiceMvpTests
from tests.invoice_test_support import InvoiceMvpTestCase


class InvoiceOperationsTests(InvoiceMvpTestCase):
    test_invoice_preview_returns_lightweight_payload_and_preview_kind = (
        InvoiceMvpTests.test_invoice_preview_returns_lightweight_payload_and_preview_kind
    )
    test_invoice_workflow_payload_exposes_undo_for_latest_reversible_action = (
        InvoiceMvpTests.test_invoice_workflow_payload_exposes_undo_for_latest_reversible_action
    )
    test_invoice_workflow_undo_reverts_last_action_and_logs_event = (
        InvoiceMvpTests.test_invoice_workflow_undo_reverts_last_action_and_logs_event
    )
    test_invoice_workflow_undo_of_handoff_restores_ready_state = (
        InvoiceMvpTests.test_invoice_workflow_undo_of_handoff_restores_ready_state
    )
    test_document_intake_snapshot_exposes_linked_invoice_and_status_counts = (
        InvoiceMvpTests.test_document_intake_snapshot_exposes_linked_invoice_and_status_counts
    )
    test_exception_center_snapshot_groups_invoice_operational_exceptions = (
        InvoiceMvpTests.test_exception_center_snapshot_groups_invoice_operational_exceptions
    )
    test_handoff_batch_can_be_created_and_exported_with_invoice_history = (
        InvoiceMvpTests.test_handoff_batch_can_be_created_and_exported_with_invoice_history
    )
    test_invoice_can_be_closed_after_handoff_and_keeps_closed_metadata = (
        InvoiceMvpTests.test_invoice_can_be_closed_after_handoff_and_keeps_closed_metadata
    )


del InvoiceMvpTestCase
del InvoiceMvpTests
