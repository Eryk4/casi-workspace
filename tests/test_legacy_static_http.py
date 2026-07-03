from __future__ import annotations

from tests.http_server_support import HttpServerTestCase
from tests.http_server_test_methods import HttpServerTestMethods


class LegacyStaticHttpTests(HttpServerTestCase):
    test_root_is_public_and_serves_html = HttpServerTestMethods.test_root_is_public_and_serves_html


del HttpServerTestCase
del HttpServerTestMethods
