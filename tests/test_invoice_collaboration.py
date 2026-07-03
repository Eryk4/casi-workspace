from __future__ import annotations

from tests.invoice_test_methods import InvoiceMvpTests
from tests.invoice_test_support import InvoiceMvpTestCase


class InvoiceCollaborationTests(InvoiceMvpTestCase):
    test_invoice_can_be_assigned_to_active_user_in_same_organization = (
        InvoiceMvpTests.test_invoice_can_be_assigned_to_active_user_in_same_organization
    )
    test_invoice_assignment_rejects_user_from_other_organization = (
        InvoiceMvpTests.test_invoice_assignment_rejects_user_from_other_organization
    )
    test_invoice_comment_is_added_and_visible_in_detail = (
        InvoiceMvpTests.test_invoice_comment_is_added_and_visible_in_detail
    )
    test_invoice_comment_history_redacts_legacy_note_text_details = (
        InvoiceMvpTests.test_invoice_comment_history_redacts_legacy_note_text_details
    )
    test_verification_workspace_item_exposes_assignee_and_comment_count = (
        InvoiceMvpTests.test_verification_workspace_item_exposes_assignee_and_comment_count
    )
    test_invoice_workflow_can_be_prepared_handed_off_and_reopened = (
        InvoiceMvpTests.test_invoice_workflow_can_be_prepared_handed_off_and_reopened
    )
    test_invoice_handoff_requires_decision_role = (
        InvoiceMvpTests.test_invoice_handoff_requires_decision_role
    )
    test_invoice_list_can_filter_by_workflow_state = (
        InvoiceMvpTests.test_invoice_list_can_filter_by_workflow_state
    )


del InvoiceMvpTestCase
del InvoiceMvpTests
