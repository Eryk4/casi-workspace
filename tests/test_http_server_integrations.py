from __future__ import annotations

from tests.http_server_support import HttpServerTestCase
from tests.http_server_test_methods import HttpServerTestMethods


class HttpServerIntegrationTests(HttpServerTestCase):
    test_email_center_requires_session = HttpServerTestMethods.test_email_center_requires_session
    test_email_center_returns_snapshot_for_owner = HttpServerTestMethods.test_email_center_returns_snapshot_for_owner
    test_integration_center_returns_nested_snapshot_for_owner = (
        HttpServerTestMethods.test_integration_center_returns_nested_snapshot_for_owner
    )
    test_email_google_connect_endpoint_returns_authorization_url = (
        HttpServerTestMethods.test_email_google_connect_endpoint_returns_authorization_url
    )
    test_email_google_disconnect_endpoint_returns_status = (
        HttpServerTestMethods.test_email_google_disconnect_endpoint_returns_status
    )
    test_email_oauth_callback_returns_success_html = HttpServerTestMethods.test_email_oauth_callback_returns_success_html
    test_org_admin_can_check_email_and_second_check_returns_no_new_documents = (
        HttpServerTestMethods.test_org_admin_can_check_email_and_second_check_returns_no_new_documents
    )
    test_test_email_connection_endpoint_reports_success_before_enabling_integration = (
        HttpServerTestMethods.test_test_email_connection_endpoint_reports_success_before_enabling_integration
    )
    test_check_email_endpoint_returns_friendly_error_when_system_imap_is_missing = (
        HttpServerTestMethods.test_check_email_endpoint_returns_friendly_error_when_system_imap_is_missing
    )
    test_check_email_endpoint_rejects_disabled_integration = (
        HttpServerTestMethods.test_check_email_endpoint_rejects_disabled_integration
    )
    test_test_ksef_connection_endpoint_reports_success = (
        HttpServerTestMethods.test_test_ksef_connection_endpoint_reports_success
    )
    test_org_admin_can_check_ksef_and_second_check_returns_no_new_documents = (
        HttpServerTestMethods.test_org_admin_can_check_ksef_and_second_check_returns_no_new_documents
    )


del HttpServerTestCase
del HttpServerTestMethods
