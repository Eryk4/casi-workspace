from __future__ import annotations

from tests.task_test_methods import TaskMvpTests
from tests.task_test_support import TaskMvpTestCase


class TaskCommandTests(TaskMvpTestCase):
    test_natural_command_preview_extracts_calendar_and_reminder = (
        TaskMvpTests.test_natural_command_preview_extracts_calendar_and_reminder
    )
    test_natural_command_preview_extracts_recurrence = TaskMvpTests.test_natural_command_preview_extracts_recurrence
    test_natural_command_preview_handles_relative_weekday_and_clean_title = (
        TaskMvpTests.test_natural_command_preview_handles_relative_weekday_and_clean_title
    )
    test_natural_command_preview_parses_weeks_ahead_and_half_hour_reminder = (
        TaskMvpTests.test_natural_command_preview_parses_weeks_ahead_and_half_hour_reminder
    )
    test_natural_command_preview_handles_polish_diacritics = (
        TaskMvpTests.test_natural_command_preview_handles_polish_diacritics
    )
    test_natural_command_preview_uses_fallback_for_joined_clauses = (
        TaskMvpTests.test_natural_command_preview_uses_fallback_for_joined_clauses
    )


del TaskMvpTestCase
del TaskMvpTests
