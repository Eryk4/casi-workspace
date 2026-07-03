from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from scripts import check_postgres_migration as check


class PostgresMigrationCheckTests(unittest.TestCase):
    def test_requires_dedicated_test_database_url(self):
        with self.assertRaises(check.SafetyError) as context:
            check.load_target_from_env({})

        self.assertIn(check.ENV_NAME, str(context.exception))
        self.assertIn("never falls back", str(context.exception))

    def test_does_not_fallback_to_database_url_or_invoice_database_url(self):
        env = {
            "DATABASE_URL": "postgresql://postgres:secret@localhost:5432/casi_migration_test",
            "INVOICE_DATABASE_URL": "postgresql://postgres:secret@localhost:5432/casi_migration_test",
        }

        with self.assertRaises(check.SafetyError):
            check.load_target_from_env(env)

    def test_rejects_managed_or_production_looking_hosts(self):
        env = {
            check.ENV_NAME: (
                "postgresql://postgres:secret@"
                "private-db-postgresql-nyc3-12345-do-user-1-0.b.db.ondigitalocean.com"
                ":25060/casi_migration_test"
            )
        }

        with self.assertRaises(check.SafetyError) as context:
            check.load_target_from_env(env)

        self.assertIn("managed", str(context.exception))
        self.assertNotIn("secret", str(context.exception))

    def test_rejects_database_name_without_test_marker(self):
        env = {check.ENV_NAME: "postgresql://postgres:secret@localhost:5432/casi_workspace"}

        with self.assertRaises(check.SafetyError) as context:
            check.load_target_from_env(env)

        self.assertIn("database name must contain", str(context.exception))
        self.assertNotIn("secret", str(context.exception))

    def test_accepts_local_test_database_url_and_redacts_password(self):
        raw_url = "postgresql://postgres:super-secret@localhost:5432/casi_migration_test"
        target = check.load_target_from_env({check.ENV_NAME: raw_url})

        self.assertEqual(target.database_name, "casi_migration_test")
        self.assertEqual(target.host, "localhost")
        self.assertNotIn("super-secret", target.redacted_label)
        self.assertIn("postgres:***@", target.redacted_label)

    def test_configure_target_environment_uses_only_dedicated_test_url(self):
        raw_url = "postgresql://postgres:secret@localhost:5432/casi_migration_test"
        target = check.load_target_from_env({check.ENV_NAME: raw_url})
        original = os.environ.copy()
        try:
            os.environ["DATABASE_URL"] = "postgresql://prod:secret@prod-db.example.com:5432/casi_prod"
            os.environ["INVOICE_DATABASE_URL"] = "postgresql://prod:secret@prod-db.example.com:5432/casi_prod"

            check.configure_target_environment(target)

            self.assertEqual(os.environ["INVOICE_DB_ENGINE"], "postgresql")
            self.assertEqual(os.environ["INVOICE_DATABASE_URL"], raw_url)
            self.assertEqual(os.environ["DATABASE_URL"], "")
        finally:
            os.environ.clear()
            os.environ.update(original)

    def test_creates_synthetic_sqlite_in_requested_temp_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            source_path = Path(tmp) / "synthetic.sqlite3"

            check.create_synthetic_sqlite(source_path)

            self.assertTrue(source_path.exists())
            connection = sqlite3.connect(source_path)
            try:
                organization_count = connection.execute("SELECT COUNT(*) FROM organizations").fetchone()[0]
                task_count = connection.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
                invoice_count = connection.execute("SELECT COUNT(*) FROM invoices").fetchone()[0]
            finally:
                connection.close()

        self.assertEqual(organization_count, 1)
        self.assertEqual(task_count, 1)
        self.assertEqual(invoice_count, 1)

    def test_script_does_not_reference_local_user_database_or_file_storage_migration(self):
        source = Path(check.__file__).read_text(encoding="utf-8")

        self.assertNotIn("SQLITE_DB_PATH", source)
        self.assertNotIn("data/magazyn", source)
        self.assertNotIn("plan_storage_migration", source)
        self.assertNotIn("check_s3_storage", source)
        self.assertNotIn("S3StorageService", source)
        self.assertNotIn("boto3", source)


if __name__ == "__main__":
    unittest.main()
