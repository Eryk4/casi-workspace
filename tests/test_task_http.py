from __future__ import annotations

from tests.task_test_methods import TaskMvpTests
from tests.task_test_support import TaskMvpTestCase


class TaskHttpTests(TaskMvpTestCase):
    test_http_task_endpoints_work_for_operator = TaskMvpTests.test_http_task_endpoints_work_for_operator
    test_http_task_reminder_dispatch_endpoint_runs_background_sweep = (
        TaskMvpTests.test_http_task_reminder_dispatch_endpoint_runs_background_sweep
    )
    test_http_task_workflow_covers_comments_checklist_templates_and_approvals = (
        TaskMvpTests.test_http_task_workflow_covers_comments_checklist_templates_and_approvals
    )


del TaskMvpTestCase
del TaskMvpTests
