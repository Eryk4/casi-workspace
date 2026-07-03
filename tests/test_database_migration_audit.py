from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import audit_database_migration as audit


class DatabaseMigrationAuditTests(unittest.TestCase):
    def write_file(self, directory: Path, name: str, content: str) -> Path:
        path = directory / name
        path.write_text(content, encoding="utf-8")
        return path

    def test_current_schema_and_migrator_are_detected_without_database_connection(self):
        report = audit.build_audit()

        self.assertIn("organizations", report["sqlite_tables"])
        self.assertIn("organizations", report["postgresql_tables"])
        self.assertIn("organizations", report["migrator_tables"])
        self.assertIn("users", report["migrator_tables"])
        self.assertIn("google_calendar_oauth_states", report["tables_missing_from_migrator"])
        self.assertIn("email_import_runs", report["tables_missing_from_migrator"])
        self.assertEqual(report["blocker_count"], 0)

    def test_remaining_table_decisions_classify_current_missing_tables(self):
        report = audit.build_audit()
        decisions = {item["table"]: item for item in report["remaining_table_decisions"]}

        self.assertEqual(set(decisions), set(report["tables_missing_from_migrator"]))
        self.assertEqual(decisions["google_calendar_oauth_states"]["classification"], "can_rebuild")
        self.assertEqual(decisions["task_reminder_worker_heartbeats"]["classification"], "can_rebuild")
        self.assertTrue(decisions["email_import_items"]["contains_sensitive_data"])
        self.assertTrue(decisions["ksef_import_items"]["contains_customer_business_data"])

    def test_no_remaining_must_migrate_tables_after_core_packages(self):
        report = audit.build_audit()
        decisions = {item["table"]: item for item in report["remaining_table_decisions"]}

        self.assertEqual(report["blocker_count"], 0)
        self.assertFalse(
            [item for item in decisions.values() if item["classification"] == "must_migrate"]
        )

        for table_name in (
            "email_import_runs",
            "email_import_items",
            "ksef_import_runs",
            "ksef_import_items",
        ):
            self.assertEqual(decisions[table_name]["classification"], "should_migrate")
            self.assertFalse(decisions[table_name]["prototype_blocker"])
            self.assertEqual(decisions[table_name]["audit_severity"], "warning")

        for table_name in (
            "google_calendar_oauth_states",
            "system_email_oauth_states",
            "task_reminder_outbox",
            "task_reminder_worker_heartbeats",
            "user_module_inbox_state",
        ):
            self.assertEqual(decisions[table_name]["classification"], "can_rebuild")
            self.assertTrue(decisions[table_name]["can_be_rebuilt"])
            self.assertEqual(decisions[table_name]["audit_severity"], "warning")

        self.assertEqual(
            decisions["task_reminder_outbox_attempts"]["classification"],
            "can_skip_for_prototype",
        )

    def test_recommendations_allow_controlled_postgresql_test_when_no_blockers_remain(self):
        report = audit.build_audit()
        recommendations = "\n".join(report["recommended_next_actions"])

        self.assertEqual(report["blocker_count"], 0)
        self.assertIn("pierwszy kontrolowany test migracji", recommendations)
        self.assertIn("Pozostale tabele nie blokuja", recommendations)
        self.assertNotIn("dopiero potem uruchomic", recommendations)

    def test_critical_missing_table_is_reported_as_blocker(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_file = self.write_file(
                root,
                "db.py",
                'SQLITE_SCHEMA = """\nCREATE TABLE IF NOT EXISTS organizations (organization_id INTEGER PRIMARY KEY);\nCREATE TABLE IF NOT EXISTS tasks (task_id INTEGER PRIMARY KEY, organization_id INTEGER, FOREIGN KEY (organization_id) REFERENCES organizations(organization_id));\n"""\n'
                'POSTGRES_SCHEMA = """\nCREATE TABLE IF NOT EXISTS organizations (organization_id SERIAL PRIMARY KEY);\nCREATE TABLE IF NOT EXISTS tasks (task_id SERIAL PRIMARY KEY, organization_id INTEGER, FOREIGN KEY (organization_id) REFERENCES organizations(organization_id));\n"""\n',
            )
            migrator = self.write_file(root, "migrate.py", 'TABLE_ORDER = ("organizations",)\n')

            report = audit.build_audit(db_path=db_file, migrator_path=migrator)

        self.assertIn("tasks", report["tables_missing_from_migrator"])
        task_issues = [issue for issue in report["issues"] if issue["table"] == "tasks"]
        self.assertEqual(task_issues[0]["severity"], "blocker")
        self.assertTrue(report["database_migration_blocked"])

    def test_rebuildable_missing_table_is_warning_not_blocker(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_file = self.write_file(
                root,
                "db.py",
                'SQLITE_SCHEMA = """\nCREATE TABLE IF NOT EXISTS organizations (organization_id INTEGER PRIMARY KEY);\nCREATE TABLE IF NOT EXISTS google_calendar_oauth_states (id INTEGER PRIMARY KEY);\n"""\n'
                'POSTGRES_SCHEMA = """\nCREATE TABLE IF NOT EXISTS organizations (organization_id SERIAL PRIMARY KEY);\nCREATE TABLE IF NOT EXISTS google_calendar_oauth_states (id SERIAL PRIMARY KEY);\n"""\n',
            )
            migrator = self.write_file(root, "migrate.py", 'TABLE_ORDER = ("organizations",)\n')

            report = audit.build_audit(db_path=db_file, migrator_path=migrator)

        issues = [issue for issue in report["issues"] if issue["table"] == "google_calendar_oauth_states"]
        self.assertEqual(issues[0]["severity"], "warning")
        self.assertEqual(report["blocker_count"], 0)

    def test_sqlite_and_postgresql_only_tables_are_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_file = self.write_file(
                root,
                "db.py",
                'SQLITE_SCHEMA = """\nCREATE TABLE IF NOT EXISTS organizations (organization_id INTEGER PRIMARY KEY);\nCREATE TABLE IF NOT EXISTS sqlite_only (id INTEGER PRIMARY KEY);\n"""\n'
                'POSTGRES_SCHEMA = """\nCREATE TABLE IF NOT EXISTS organizations (organization_id SERIAL PRIMARY KEY);\nCREATE TABLE IF NOT EXISTS postgres_only (id SERIAL PRIMARY KEY);\n"""\n',
            )
            migrator = self.write_file(root, "migrate.py", 'TABLE_ORDER = ("organizations",)\n')

            report = audit.build_audit(db_path=db_file, migrator_path=migrator)

        self.assertEqual(report["sqlite_only_tables"], ["sqlite_only"])
        self.assertEqual(report["postgresql_only_tables"], ["postgres_only"])
        self.assertIn("sqlite_only_table", report["issue_count_by_category"])
        self.assertIn("postgres_only_table", report["issue_count_by_category"])

    def test_unsafe_migration_order_is_blocker(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_file = self.write_file(
                root,
                "db.py",
                'SQLITE_SCHEMA = """\nCREATE TABLE IF NOT EXISTS parent_table (id INTEGER PRIMARY KEY);\nCREATE TABLE IF NOT EXISTS child_table (id INTEGER PRIMARY KEY, parent_id INTEGER, FOREIGN KEY (parent_id) REFERENCES parent_table(id));\n"""\n'
                'POSTGRES_SCHEMA = """\nCREATE TABLE IF NOT EXISTS parent_table (id SERIAL PRIMARY KEY);\nCREATE TABLE IF NOT EXISTS child_table (id SERIAL PRIMARY KEY, parent_id INTEGER, FOREIGN KEY (parent_id) REFERENCES parent_table(id));\n"""\n',
            )
            migrator = self.write_file(root, "migrate.py", 'TABLE_ORDER = ("child_table", "parent_table")\n')

            report = audit.build_audit(db_path=db_file, migrator_path=migrator)

        self.assertIn("unsafe_migration_order", report["issue_count_by_category"])
        order_issues = report["migration_order_issues"]
        self.assertEqual(order_issues[0]["severity"], "blocker")

    def test_reports_are_written_without_private_absolute_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = audit.build_audit()
            json_path = root / "database_migration_audit.json"
            md_path = root / "database_migration_audit.md"
            audit.write_json_report(report, json_path)
            audit.write_markdown_report(report, md_path)

            loaded = json.loads(json_path.read_text(encoding="utf-8"))
            markdown = md_path.read_text(encoding="utf-8")

        self.assertEqual(loaded["schema_sources"]["db_schema_file"], "app\\db.py" if "\\" in loaded["schema_sources"]["db_schema_file"] else "app/db.py")
        self.assertNotIn("C:\\Users", markdown)
        self.assertIn("Czy migracja bazy jest zablokowana?", markdown)
        self.assertIn("Decyzje dla pozostalych tabel", markdown)
        self.assertIn("remaining_table_decisions", loaded)

    def test_missing_files_are_errors_without_postgresql_requirement(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = audit.build_audit(db_path=root / "missing_db.py", migrator_path=root / "missing_migrator.py")

        self.assertEqual(report["issue_count_by_severity"]["error"], 2)
        self.assertEqual(report["blocker_count"], 0)


if __name__ == "__main__":
    unittest.main()
