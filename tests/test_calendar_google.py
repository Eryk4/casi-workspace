from __future__ import annotations

from tests.calendar_test_methods import CalendarMvpTests
from tests.calendar_test_support import CalendarMvpTestCase


class CalendarGoogleTests(CalendarMvpTestCase):
    test_google_connection_status_exposes_setup_diagnostics = (
        CalendarMvpTests.test_google_connection_status_exposes_setup_diagnostics
    )
    test_google_connection_requires_visibility_confirmation = (
        CalendarMvpTests.test_google_connection_requires_visibility_confirmation
    )
    test_user_google_connection_waits_for_admin_approval_before_sync = (
        CalendarMvpTests.test_user_google_connection_waits_for_admin_approval_before_sync
    )
    test_assigned_organization_calendar_uses_organization_admin_connection = (
        CalendarMvpTests.test_assigned_organization_calendar_uses_organization_admin_connection
    )
    test_google_sync_check_detects_difference_and_missing_event = (
        CalendarMvpTests.test_google_sync_check_detects_difference_and_missing_event
    )


del CalendarMvpTestCase
del CalendarMvpTests
