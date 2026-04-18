from __future__ import annotations

from tests.search_test_methods import SearchServiceTests
from tests.search_test_support import SearchServiceTestCase


class SearchAccessTests(SearchServiceTestCase):
    test_org_admin_search_returns_admin_module_and_record_groups = (
        SearchServiceTests.test_org_admin_search_returns_admin_module_and_record_groups
    )
    test_operator_search_respects_private_tasks_and_admin_boundaries = (
        SearchServiceTests.test_operator_search_respects_private_tasks_and_admin_boundaries
    )
    test_tasks_module_card_requires_enabled_org_module = (
        SearchServiceTests.test_tasks_module_card_requires_enabled_org_module
    )


del SearchServiceTestCase
del SearchServiceTests
