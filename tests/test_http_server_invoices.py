from __future__ import annotations

from tests.http_server_support import HttpServerTestCase
from tests.http_server_test_methods import HttpServerTestMethods


class HttpServerInvoiceTests(HttpServerTestCase):
    _create_manager_assistant_org_for_http = HttpServerTestMethods._create_manager_assistant_org_for_http
    test_invoice_batch_action_endpoint_updates_multiple_invoices = (
        HttpServerTestMethods.test_invoice_batch_action_endpoint_updates_multiple_invoices
    )
    test_invoice_verification_inbox_endpoint_returns_operational_sections = (
        HttpServerTestMethods.test_invoice_verification_inbox_endpoint_returns_operational_sections
    )
    test_invoice_verification_workspace_endpoint_returns_sections_and_sla_summary = (
        HttpServerTestMethods.test_invoice_verification_workspace_endpoint_returns_sections_and_sla_summary
    )
    test_invoice_compare_endpoint_returns_side_by_side_rows = (
        HttpServerTestMethods.test_invoice_compare_endpoint_returns_side_by_side_rows
    )
    test_invoice_detail_endpoint_returns_field_provenance_and_duplicate_center = (
        HttpServerTestMethods.test_invoice_detail_endpoint_returns_field_provenance_and_duplicate_center
    )
    test_invoice_approval_workflow_updates_invoice_and_exposes_request = (
        HttpServerTestMethods.test_invoice_approval_workflow_updates_invoice_and_exposes_request
    )
    test_organization_patch_can_store_ksef_delegate_fields = (
        HttpServerTestMethods.test_organization_patch_can_store_ksef_delegate_fields
    )
    test_operator_save_on_ksef_invoice_returns_request_and_delegate_can_approve_via_http = (
        HttpServerTestMethods.test_operator_save_on_ksef_invoice_returns_request_and_delegate_can_approve_via_http
    )
    test_only_decision_roles_can_confirm_duplicate = (
        HttpServerTestMethods.test_only_decision_roles_can_confirm_duplicate
    )
    test_invoice_assignable_users_endpoint_returns_users_in_scope = (
        HttpServerTestMethods.test_invoice_assignable_users_endpoint_returns_users_in_scope
    )
    test_invoice_patch_can_assign_user_and_detail_exposes_assignee = (
        HttpServerTestMethods.test_invoice_patch_can_assign_user_and_detail_exposes_assignee
    )
    test_invoice_list_can_filter_by_assigned_user = (
        HttpServerTestMethods.test_invoice_list_can_filter_by_assigned_user
    )
    test_invoice_comment_endpoint_adds_comment_and_detail_contains_it = (
        HttpServerTestMethods.test_invoice_comment_endpoint_adds_comment_and_detail_contains_it
    )
    test_invoice_comment_endpoint_requires_write_scope = (
        HttpServerTestMethods.test_invoice_comment_endpoint_requires_write_scope
    )
    test_invoice_comment_endpoint_rejects_extra_payload_fields = (
        HttpServerTestMethods.test_invoice_comment_endpoint_rejects_extra_payload_fields
    )
    test_invoice_preview_endpoint_returns_preview_payload = (
        HttpServerTestMethods.test_invoice_preview_endpoint_returns_preview_payload
    )
    test_dashboard_views_accept_invoice_module_key = (
        HttpServerTestMethods.test_dashboard_views_accept_invoice_module_key
    )
    test_invoice_list_can_filter_by_workflow_state = (
        HttpServerTestMethods.test_invoice_list_can_filter_by_workflow_state
    )
    test_invoice_mark_ready_action_updates_workflow = (
        HttpServerTestMethods.test_invoice_mark_ready_action_updates_workflow
    )
    test_invoice_undo_last_action_endpoint_reverts_workflow = (
        HttpServerTestMethods.test_invoice_undo_last_action_endpoint_reverts_workflow
    )
    test_invoice_handoff_action_requires_decision_role = (
        HttpServerTestMethods.test_invoice_handoff_action_requires_decision_role
    )
    test_invoice_handoff_and_reopen_actions_change_workflow = (
        HttpServerTestMethods.test_invoice_handoff_and_reopen_actions_change_workflow
    )
    test_invoice_document_intake_endpoint_returns_snapshot = (
        HttpServerTestMethods.test_invoice_document_intake_endpoint_returns_snapshot
    )
    test_invoice_exception_center_endpoint_returns_snapshot = (
        HttpServerTestMethods.test_invoice_exception_center_endpoint_returns_snapshot
    )
    test_invoice_handoff_batch_endpoints_create_detail_and_export = (
        HttpServerTestMethods.test_invoice_handoff_batch_endpoints_create_detail_and_export
    )
    test_invoice_close_action_updates_workflow = (
        HttpServerTestMethods.test_invoice_close_action_updates_workflow
    )
    test_invoice_and_contractor_details_hide_private_linked_tasks_for_other_user = (
        HttpServerTestMethods.test_invoice_and_contractor_details_hide_private_linked_tasks_for_other_user
    )
    test_task_detail_http_returns_linked_entities = (
        HttpServerTestMethods.test_task_detail_http_returns_linked_entities
    )


del HttpServerTestCase
del HttpServerTestMethods
