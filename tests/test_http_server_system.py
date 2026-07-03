from __future__ import annotations

from tests.http_server_support import HttpServerTestCase
from tests.http_server_test_methods import HttpServerTestMethods


class HttpServerSystemTests(HttpServerTestCase):
    test_root_does_not_serve_static_html_when_legacy_static_is_disabled = (
        HttpServerTestMethods.test_root_does_not_serve_static_html_when_legacy_static_is_disabled
    )
    test_spa_fallback_does_not_serve_static_html_when_legacy_static_is_disabled = (
        HttpServerTestMethods.test_spa_fallback_does_not_serve_static_html_when_legacy_static_is_disabled
    )
    test_meta_exposes_storage_backend = HttpServerTestMethods.test_meta_exposes_storage_backend
    test_meta_exposes_environment_flags = HttpServerTestMethods.test_meta_exposes_environment_flags
    test_dashboard_requires_session_but_login_works = HttpServerTestMethods.test_dashboard_requires_session_but_login_works
    test_session_current_exposes_workspace_state_and_device_context = (
        HttpServerTestMethods.test_session_current_exposes_workspace_state_and_device_context
    )
    test_session_login_blocks_fourth_active_device = (
        HttpServerTestMethods.test_session_login_blocks_fourth_active_device
    )
    test_same_organization_users_share_one_note = HttpServerTestMethods.test_same_organization_users_share_one_note
    test_personal_note_is_private_per_user = HttpServerTestMethods.test_personal_note_is_private_per_user
    test_user_reminder_preferences_reject_extra_payload_fields = (
        HttpServerTestMethods.test_user_reminder_preferences_reject_extra_payload_fields
    )
    test_dashboard_snapshot_contains_operational_alerts = (
        HttpServerTestMethods.test_dashboard_snapshot_contains_operational_alerts
    )
    test_contractor_note_endpoint_adds_note_and_detail_contains_it = (
        HttpServerTestMethods.test_contractor_note_endpoint_adds_note_and_detail_contains_it
    )
    test_contractor_note_endpoint_rejects_invalid_payloads = (
        HttpServerTestMethods.test_contractor_note_endpoint_rejects_invalid_payloads
    )
    test_contractor_note_endpoint_requires_session_and_organization_access = (
        HttpServerTestMethods.test_contractor_note_endpoint_requires_session_and_organization_access
    )
    test_test_import_endpoint_can_be_disabled = HttpServerTestMethods.test_test_import_endpoint_can_be_disabled


del HttpServerTestCase
del HttpServerTestMethods
