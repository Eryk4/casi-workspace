from __future__ import annotations

from tests.search_test_methods import SearchServiceTests
from tests.search_test_support import SearchServiceTestCase


class SearchDescriptiveTests(SearchServiceTestCase):
    test_descriptive_invoice_search_matches_april_invoice = (
        SearchServiceTests.test_descriptive_invoice_search_matches_april_invoice
    )
    test_descriptive_knowledge_search_returns_authorized_document = (
        SearchServiceTests.test_descriptive_knowledge_search_returns_authorized_document
    )
    test_descriptive_billing_search_matches_account_and_reference = (
        SearchServiceTests.test_descriptive_billing_search_matches_account_and_reference
    )


del SearchServiceTestCase
del SearchServiceTests
