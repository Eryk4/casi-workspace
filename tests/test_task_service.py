from __future__ import annotations

from tests.task_test_methods import TaskMvpTests
from tests.task_test_support import TaskMvpTestCase


class TaskServiceTests(TaskMvpTestCase):
    _utworz_testowa_fakture = TaskMvpTests._utworz_testowa_fakture
    test_task_service_can_create_update_and_add_note = TaskMvpTests.test_task_service_can_create_update_and_add_note
    test_dashboard_snapshot_includes_due_reminders = TaskMvpTests.test_dashboard_snapshot_includes_due_reminders
    test_private_task_is_visible_only_for_owner = TaskMvpTests.test_private_task_is_visible_only_for_owner
    test_task_can_be_shared_with_selected_users = TaskMvpTests.test_task_can_be_shared_with_selected_users
    test_operator_can_share_task_and_note_with_other_users = (
        TaskMvpTests.test_operator_can_share_task_and_note_with_other_users
    )
    test_recurrence_scope_updates_open_series_tasks = TaskMvpTests.test_recurrence_scope_updates_open_series_tasks
    test_logs_hide_private_task_events_from_other_users = TaskMvpTests.test_logs_hide_private_task_events_from_other_users
    test_reminder_cannot_be_later_than_due_time = TaskMvpTests.test_reminder_cannot_be_later_than_due_time
    test_task_planner_snapshot_and_snooze_reminder = TaskMvpTests.test_task_planner_snapshot_and_snooze_reminder
    test_completed_recurring_task_creates_next_occurrence = (
        TaskMvpTests.test_completed_recurring_task_creates_next_occurrence
    )
    test_focus_snapshot_groups_tasks_for_daily_work = TaskMvpTests.test_focus_snapshot_groups_tasks_for_daily_work
    test_task_detail_includes_uploaded_attachment = TaskMvpTests.test_task_detail_includes_uploaded_attachment
    test_task_detail_includes_link_attachment = TaskMvpTests.test_task_detail_includes_link_attachment
    test_task_can_link_invoice_and_contractor = TaskMvpTests.test_task_can_link_invoice_and_contractor
    test_private_linked_task_is_visible_in_invoice_and_contractor_detail_only_for_owner = (
        TaskMvpTests.test_private_linked_task_is_visible_in_invoice_and_contractor_detail_only_for_owner
    )


del TaskMvpTestCase
del TaskMvpTests
