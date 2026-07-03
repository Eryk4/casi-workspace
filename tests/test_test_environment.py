from __future__ import annotations

import os
import unittest

from app import config


class TestEnvironmentIsolationTests(unittest.TestCase):
    def test_unittest_runtime_uses_deterministic_local_defaults(self) -> None:
        self.assertEqual(os.getenv("INVOICE_DB_ENGINE"), "sqlite")
        self.assertEqual(os.getenv("INVOICE_DATABASE_URL"), "")
        self.assertEqual(os.getenv("DATABASE_URL"), "")
        self.assertEqual(os.getenv("INVOICE_STORAGE_BACKEND"), "local")
        self.assertEqual(config.DB_ENGINE, "sqlite")
        self.assertEqual(config.STORAGE_BACKEND, "local")
        self.assertEqual(config.SESSION_MAX_ACTIVE_DEVICES_PER_ACCOUNT, 3)


if __name__ == "__main__":
    unittest.main()
