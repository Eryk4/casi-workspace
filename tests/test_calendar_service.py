from __future__ import annotations

from tests.calendar_test_methods import CalendarMvpTests
from tests.calendar_test_support import CalendarMvpTestCase


class CalendarServiceTests(CalendarMvpTestCase):
    test_user_can_create_named_google_calendars_and_assign_task = (
        CalendarMvpTests.test_user_can_create_named_google_calendars_and_assign_task
    )
    test_operator_cannot_create_private_family_or_organization_calendar = (
        CalendarMvpTests.test_operator_cannot_create_private_family_or_organization_calendar
    )
    test_org_admin_can_create_private_and_family_calendar = (
        CalendarMvpTests.test_org_admin_can_create_private_and_family_calendar
    )
    test_user_can_store_own_reminder_preferences = CalendarMvpTests.test_user_can_store_own_reminder_preferences


del CalendarMvpTestCase
del CalendarMvpTests
