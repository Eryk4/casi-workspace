from __future__ import annotations

import contextlib
import io
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


os.environ.setdefault("INVOICE_LOAD_LOCAL_ENV", "0")
os.environ.setdefault("INVOICE_DB_ENGINE", "sqlite")
os.environ.setdefault("INVOICE_DATABASE_URL", "")
os.environ.setdefault("DATABASE_URL", "")
os.environ.setdefault("INVOICE_STORAGE_BACKEND", "local")

from app.cli import database_migrate, staging_preflight
from app.db import (
    CURRENT_SCHEMA_VERSION,
    DatabaseConnection,
    apply_database_schema_to_connection,
)


ROOT = Path(__file__).resolve().parents[1]


class DatabaseMigrationCommandTests(unittest.TestCase):
    def test_check_and_apply_without_explicit_postgres_dsn_fail_safely(self) -> None:
        for mode in ("--check", "--apply"):
            with self.subTest(mode=mode), patch.dict(os.environ, {}, clear=True):
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    exit_code = database_migrate.main([mode])
                self.assertEqual(exit_code, 1)
                report = json.loads(output.getvalue())
                self.assertEqual(report["status"], "configuration_error")
                self.assertNotIn("DATABASE_URL", output.getvalue())

    def test_apply_rejects_sqlite_even_with_explicit_path(self) -> None:
        environment = {
            "INVOICE_DB_ENGINE": "sqlite",
            "INVOICE_SQLITE_PATH": str(ROOT / "data" / "never-used.sqlite3"),
        }
        with self.assertRaises(database_migrate.MigrationConfigurationError):
            database_migrate.validate_environment(environment)

    def test_schema_only_is_idempotent_without_admin_seed_or_storage_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            database_path = root / "schema.sqlite3"
            forbidden_storage = root / "storage-must-not-exist"
            raw = sqlite3.connect(database_path)
            raw.row_factory = sqlite3.Row
            connection = DatabaseConnection(raw, backend="sqlite", driver_name="sqlite")
            apply_database_schema_to_connection(connection)
            connection.commit()
            apply_database_schema_to_connection(connection)
            connection.commit()
            version = connection.execute(
                "SELECT schema_value FROM casi_schema_metadata WHERE schema_key = 'schema_version'"
            ).fetchone()["schema_value"]
            users = connection.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"]
            events = connection.execute("SELECT COUNT(*) AS count FROM event_logs").fetchone()["count"]
            quick_check = connection.execute("PRAGMA quick_check").fetchone()[0]
            connection.close()
            self.assertEqual(version, CURRENT_SCHEMA_VERSION)
            self.assertEqual(users, 0)
            self.assertEqual(events, 0)
            self.assertEqual(quick_check, "ok")
            self.assertFalse(forbidden_storage.exists())

    def test_system_failure_report_is_sanitized_and_nonzero(self) -> None:
        environment = {
            "INVOICE_DB_ENGINE": "postgresql",
            "INVOICE_DATABASE_URL": "postgresql://user:TOP_SECRET@example.invalid/db",
        }
        with patch.dict(os.environ, environment, clear=True), patch(
            "app.db.initialize_database", side_effect=RuntimeError("TOP_SECRET")
        ):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = database_migrate.main(["--apply"])
        self.assertEqual(exit_code, 1)
        self.assertNotIn("TOP_SECRET", output.getvalue())
        self.assertNotIn("postgresql://", output.getvalue())

    def test_cli_sets_local_env_loading_off_before_app_imports(self) -> None:
        source = (ROOT / "app" / "cli" / "database_migrate.py").read_text(encoding="utf-8")
        assignment = source.index('os.environ["INVOICE_LOAD_LOCAL_ENV"] = "0"')
        database_import = source.index("from app.db import")
        self.assertLess(assignment, database_import)

    def test_schema_marker_sql_is_portable_to_postgresql(self) -> None:
        source = (ROOT / "app" / "db.py").read_text(encoding="utf-8")
        marker_sql = source.split("def _ensure_schema_metadata", 1)[1].split(
            "def apply_database_schema_to_connection",
            1,
        )[0]
        self.assertIn("CREATE TABLE IF NOT EXISTS casi_schema_metadata", marker_sql)
        self.assertIn("ON CONFLICT(schema_key) DO UPDATE", marker_sql)
        self.assertNotIn("AUTOINCREMENT", marker_sql)
        self.assertNotIn("PRAGMA", marker_sql)


class BackendBootstrapModeTests(unittest.TestCase):
    class FakeServer:
        def serve_forever(self):
            return None

        def server_close(self):
            return None

    def _services(self):
        return {"auth_service": Mock(), "invoice_service": Mock()}

    def test_auto_preserves_schema_admin_and_local_directory_bootstrap(self) -> None:
        import run

        services = self._services()
        with patch.object(sys, "argv", ["run.py", "--mode", "web"]), patch.object(
            run, "DATABASE_BOOTSTRAP_MODE", "auto"
        ), patch.object(run, "ENABLE_DEMO_SEED", False), patch.object(
            run, "ensure_directories"
        ) as directories, patch.object(
            run, "initialize_database"
        ) as initialize, patch.object(
            run, "build_services", return_value=services
        ) as build_services, patch.object(
            run, "create_server", return_value=self.FakeServer()
        ):
            run.main()
        directories.assert_called_once_with()
        initialize.assert_called_once_with()
        build_services.assert_called_once_with(initialize_default_organization=True)
        services["auth_service"].ensure_default_admin.assert_called_once_with()

    def test_validate_is_read_only_and_does_not_create_admin_or_seed(self) -> None:
        import run

        services = self._services()
        with patch.object(sys, "argv", ["run.py", "--mode", "web"]), patch.object(
            run, "DATABASE_BOOTSTRAP_MODE", "validate"
        ), patch.object(run, "ENABLE_DEMO_SEED", False), patch.object(
            run, "ensure_directories"
        ) as directories, patch.object(
            run, "initialize_database"
        ) as initialize, patch.object(
            run, "validate_database_schema", return_value={"ready": True}
        ) as validate, patch.object(
            run, "seed_demo_data"
        ) as seed, patch.object(
            run, "build_services", return_value=services
        ) as build_services, patch.object(
            run, "create_server", return_value=self.FakeServer()
        ):
            run.main()
        validate.assert_called_once_with()
        directories.assert_not_called()
        initialize.assert_not_called()
        build_services.assert_called_once_with(initialize_default_organization=False)
        services["auth_service"].ensure_default_admin.assert_not_called()
        seed.assert_not_called()

    def test_validate_never_falls_back_to_schema_initialization(self) -> None:
        import run

        with patch.object(sys, "argv", ["run.py", "--mode", "web"]), patch.object(
            run, "DATABASE_BOOTSTRAP_MODE", "validate"
        ), patch.object(run, "ENABLE_DEMO_SEED", False), patch.object(
            run, "validate_database_schema", return_value={"ready": True}
        ), patch.object(
            run,
            "build_services",
            side_effect=RuntimeError('relation "organizations" does not exist'),
        ), patch.object(run, "initialize_database") as initialize:
            with self.assertRaisesRegex(RuntimeError, "organizations"):
                run.main()
        initialize.assert_not_called()

    def test_validate_missing_schema_stops_before_services(self) -> None:
        import run

        with patch.object(sys, "argv", ["run.py", "--mode", "web"]), patch.object(
            run, "DATABASE_BOOTSTRAP_MODE", "validate"
        ), patch.object(run, "validate_database_schema", side_effect=RuntimeError("schema missing")), patch.object(
            run, "build_services"
        ) as build_services:
            with self.assertRaisesRegex(RuntimeError, "schema missing"):
                run.main()
        build_services.assert_not_called()

    def test_web_mode_does_not_construct_background_loops(self) -> None:
        import run

        services = self._services()
        with patch.object(sys, "argv", ["run.py", "--mode", "web"]), patch.object(
            run, "DATABASE_BOOTSTRAP_MODE", "off"
        ), patch.object(run, "ENABLE_DEMO_SEED", False), patch.object(
            run, "build_services", return_value=services
        ), patch.object(
            run, "create_server", return_value=self.FakeServer()
        ), patch.object(run, "EmailImportSchedulerLoop") as email_loop, patch.object(
            run, "TaskReminderSchedulerLoop"
        ) as reminder_loop, patch.object(run, "TaskReminderDeliveryLoop") as delivery_loop:
            run.main()
        email_loop.assert_not_called()
        reminder_loop.assert_not_called()
        delivery_loop.assert_not_called()

    def test_postgres_without_dsn_has_no_sqlite_fallback(self) -> None:
        code = "import app.config"
        environment = {
            "INVOICE_LOAD_LOCAL_ENV": "0",
            "INVOICE_DB_ENGINE": "postgresql",
            "PYTHONPATH": str(ROOT),
        }
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PostgreSQL", result.stderr)


class StagingPreflightTests(unittest.TestCase):
    @staticmethod
    def safe_environment() -> dict[str, str]:
        return {
            "INVOICE_DB_ENGINE": "postgresql",
            "INVOICE_DATABASE_URL": "postgresql://REDACTED",
            "INVOICE_DATABASE_BOOTSTRAP_MODE": "validate",
            "INVOICE_REQUIRE_DURABLE_STORAGE": "true",
            "INVOICE_STORAGE_BACKEND": "s3",
            "INVOICE_S3_REQUIRE_TLS": "true",
            "INVOICE_S3_ENDPOINT_URL": "https://storage.invalid",
            "INVOICE_S3_BUCKET": "casi-staging",
            "INVOICE_S3_ACCESS_KEY_ID": "REDACTED_ACCESS",
            "INVOICE_S3_SECRET_ACCESS_KEY": "REDACTED_SECRET",
            "INVOICE_ENABLE_DEMO_SEED": "0",
            "CASI_ALLOW_LOCAL_SANDBOX_RESET": "0",
            "INTERNAL_NOTIFICATION_SCHEDULER_RUNTIME_ENABLED": "false",
        }

    def test_complete_configuration_passes_with_read_only_schema_probe(self) -> None:
        environment = self.safe_environment()
        report = staging_preflight.evaluate_environment(
            environment,
            database_probe=lambda: {"ready": True},
        )
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["exit_code"], 0)
        serialized = json.dumps(report)
        self.assertNotIn(environment["INVOICE_DATABASE_URL"], serialized)
        self.assertNotIn(environment["INVOICE_S3_SECRET_ACCESS_KEY"], serialized)

    def test_unsafe_staging_variants_fail_closed(self) -> None:
        variants = {
            "sqlite": {"INVOICE_DB_ENGINE": "sqlite"},
            "missing_dsn": {"INVOICE_DATABASE_URL": ""},
            "auto_bootstrap": {"INVOICE_DATABASE_BOOTSTRAP_MODE": "auto"},
            "seed": {"INVOICE_ENABLE_DEMO_SEED": "1"},
            "reset": {"CASI_ALLOW_LOCAL_SANDBOX_RESET": "1"},
            "local_storage": {"INVOICE_STORAGE_BACKEND": "local"},
            "no_durable": {"INVOICE_REQUIRE_DURABLE_STORAGE": "false"},
            "missing_s3": {"INVOICE_S3_BUCKET": ""},
            "insecure_s3": {"INVOICE_S3_ENDPOINT_URL": "http://storage.invalid"},
            "tls_not_required": {"INVOICE_S3_REQUIRE_TLS": "false"},
        }
        for name, override in variants.items():
            with self.subTest(name=name):
                environment = {**self.safe_environment(), **override}
                report = staging_preflight.evaluate_environment(
                    environment,
                    database_probe=lambda: {"ready": True},
                )
                self.assertEqual(report["status"], "fail")
                self.assertEqual(report["exit_code"], 1)

    def test_scheduler_runtime_is_reported_and_initial_staging_requires_false(self) -> None:
        environment = {
            **self.safe_environment(),
            "INTERNAL_NOTIFICATION_SCHEDULER_RUNTIME_ENABLED": "true",
        }
        report = staging_preflight.evaluate_environment(
            environment,
            database_probe=lambda: {"ready": True},
        )
        self.assertTrue(report["scheduler_runtime_enabled"])
        self.assertEqual(report["status"], "fail")


class RuntimePinTests(unittest.TestCase):
    def test_runtime_files_and_package_engines_match(self) -> None:
        self.assertEqual((ROOT / ".python-version").read_text(encoding="utf-8").strip(), "3.11.9")
        self.assertEqual((ROOT / ".nvmrc").read_text(encoding="utf-8").strip(), "24.18.0")
        package = json.loads((ROOT / "frontend" / "package.json").read_text(encoding="utf-8"))
        lock = json.loads((ROOT / "frontend" / "package-lock.json").read_text(encoding="utf-8"))
        expected = {"node": ">=24.18.0 <25", "npm": ">=11.16.0 <12"}
        self.assertEqual(package["engines"], expected)
        self.assertEqual(lock["packages"][""]["engines"], expected)


if __name__ == "__main__":
    unittest.main()
