from __future__ import annotations

import json
import subprocess
import sys
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
        self.assertIn("email_import_runs", report["migrator_tables"])
        self.assertIn("google_calendar_oauth_states", report["classified_excluded_tables"])
        self.assertEqual(len(report["sqlite_tables"]), 78)
        self.assertEqual(len(report["manifest_tables"]), 78)
        self.assertEqual(len(report["migrator_tables"]), 73)
        self.assertEqual(report["unclassified_tables"], [])
        self.assertEqual(report["tables_missing_from_migrator"], [])
        self.assertEqual(report["blocker_count"], 0)

    def test_audit_script_runs_directly_from_repository_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(audit.__file__),
                    "--output-json",
                    str(output_root / "audit.json"),
                    "--output-md",
                    str(output_root / "audit.md"),
                    "--fail-on-blockers",
                ],
                cwd=audit.ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Unclassified tables: 0", completed.stdout)
        self.assertIn("Blockers: 0", completed.stdout)

    def test_remaining_table_decisions_classify_current_missing_tables(self):
        report = audit.build_audit()
        decisions = {item["table"]: item for item in report["remaining_table_decisions"]}

        self.assertEqual(set(decisions), set(report["classified_excluded_tables"]))
        self.assertEqual(decisions["google_calendar_oauth_states"]["category"], "D_runtime_temporary")
        self.assertEqual(decisions["task_reminder_worker_heartbeats"]["category"], "D_runtime_temporary")
        self.assertFalse(decisions["user_sessions"]["migrate"])
        self.assertTrue(decisions["google_calendar_oauth_states"]["rebuild_procedure"])

    def test_no_remaining_must_migrate_tables_after_core_packages(self):
        report = audit.build_audit()
        decisions = {item["table"]: item for item in report["remaining_table_decisions"]}

        self.assertEqual(report["blocker_count"], 0)
        self.assertEqual(
            set(decisions),
            {
                "casi_schema_metadata",
                "google_calendar_oauth_states",
                "system_email_oauth_states",
                "task_reminder_worker_heartbeats",
                "user_sessions",
            },
        )
        for table_name in (
            "casi_schema_metadata",
            "google_calendar_oauth_states",
            "system_email_oauth_states",
            "task_reminder_worker_heartbeats",
            "user_sessions",
        ):
            self.assertEqual(decisions[table_name]["category"], "D_runtime_temporary")
            self.assertFalse(decisions[table_name]["migrate"])

    def test_recommendations_allow_controlled_postgresql_test_when_no_blockers_remain(self):
        report = audit.build_audit()
        recommendations = "\n".join(report["recommended_next_actions"])

        self.assertEqual(report["blocker_count"], 0)
        self.assertIn("pustym, jednorazowym PostgreSQL", recommendations)

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
        self.assertEqual(issues[0]["severity"], "info")
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
        self.assertIn("Jawnie wykluczone", markdown)
        self.assertIn("remaining_table_decisions", loaded)

    def test_missing_files_are_errors_without_postgresql_requirement(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = audit.build_audit(db_path=root / "missing_db.py", migrator_path=root / "missing_migrator.py")

        self.assertEqual(report["issue_count_by_severity"]["error"], 2)
        self.assertEqual(report["blocker_count"], 0)


if __name__ == "__main__":
    unittest.main()
