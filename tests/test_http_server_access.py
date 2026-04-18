from __future__ import annotations

from tests.http_server_support import HttpServerTestCase
from tests.http_server_test_methods import HttpServerTestMethods


class HttpServerAccessTests(HttpServerTestCase):
    _create_manager_assistant_org_for_http = HttpServerTestMethods._create_manager_assistant_org_for_http

    test_dashboard_snapshot_shows_knowledge_alerts_for_document_queue = (
        HttpServerTestMethods.test_dashboard_snapshot_shows_knowledge_alerts_for_document_queue
    )
    test_dashboard_snapshot_exposes_knowledge_queue_with_decision_actions = (
        HttpServerTestMethods.test_dashboard_snapshot_exposes_knowledge_queue_with_decision_actions
    )
    test_org_user_sees_only_own_invoices_and_cannot_open_other_org_files = (
        HttpServerTestMethods.test_org_user_sees_only_own_invoices_and_cannot_open_other_org_files
    )
    test_org_user_sees_only_own_knowledge_base_and_cannot_open_other_org_knowledge_files = (
        HttpServerTestMethods.test_org_user_sees_only_own_knowledge_base_and_cannot_open_other_org_knowledge_files
    )
    test_knowledge_upload_permission_is_controlled_per_user = (
        HttpServerTestMethods.test_knowledge_upload_permission_is_controlled_per_user
    )
    test_knowledge_reprocess_requires_manage_capability = (
        HttpServerTestMethods.test_knowledge_reprocess_requires_manage_capability
    )
    test_knowledge_document_metadata_can_be_updated_and_is_searchable = (
        HttpServerTestMethods.test_knowledge_document_metadata_can_be_updated_and_is_searchable
    )
    test_knowledge_assignment_candidates_endpoint_returns_active_org_members = (
        HttpServerTestMethods.test_knowledge_assignment_candidates_endpoint_returns_active_org_members
    )
    test_knowledge_document_detail_exposes_audit_after_download = (
        HttpServerTestMethods.test_knowledge_document_detail_exposes_audit_after_download
    )
    test_knowledge_document_comment_and_official_version_endpoints_update_detail = (
        HttpServerTestMethods.test_knowledge_document_comment_and_official_version_endpoints_update_detail
    )
    test_knowledge_document_compare_endpoint_returns_diff = (
        HttpServerTestMethods.test_knowledge_document_compare_endpoint_returns_diff
    )
    test_knowledge_document_preview_file_endpoint_returns_inline_content = (
        HttpServerTestMethods.test_knowledge_document_preview_file_endpoint_returns_inline_content
    )
    test_knowledge_preview_file_requires_download_capability = (
        HttpServerTestMethods.test_knowledge_preview_file_requires_download_capability
    )
    test_knowledge_comment_endpoint_allows_reader_but_mark_official_requires_manage = (
        HttpServerTestMethods.test_knowledge_comment_endpoint_allows_reader_but_mark_official_requires_manage
    )
    test_knowledge_documents_endpoint_exposes_activity_feed_and_mark_seen = (
        HttpServerTestMethods.test_knowledge_documents_endpoint_exposes_activity_feed_and_mark_seen
    )
    test_knowledge_document_decision_endpoint_updates_workflow_and_requires_reason = (
        HttpServerTestMethods.test_knowledge_document_decision_endpoint_updates_workflow_and_requires_reason
    )
    test_knowledge_document_tasks_endpoint_creates_linked_task_and_audit = (
        HttpServerTestMethods.test_knowledge_document_tasks_endpoint_creates_linked_task_and_audit
    )
    test_knowledge_document_bulk_endpoint_updates_selected_records = (
        HttpServerTestMethods.test_knowledge_document_bulk_endpoint_updates_selected_records
    )
    test_knowledge_bulk_endpoint_requires_manage_capability = (
        HttpServerTestMethods.test_knowledge_bulk_endpoint_requires_manage_capability
    )
    test_organization_admin_can_edit_own_organization_but_cannot_create_new_one = (
        HttpServerTestMethods.test_organization_admin_can_edit_own_organization_but_cannot_create_new_one
    )
    test_search_endpoint_returns_modules_and_visible_records = (
        HttpServerTestMethods.test_search_endpoint_returns_modules_and_visible_records
    )


del HttpServerTestCase
del HttpServerTestMethods
