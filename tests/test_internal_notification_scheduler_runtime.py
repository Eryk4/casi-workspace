from __future__ import annotations

import contextlib
import hashlib
import io
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.jobs import internal_notifications_scheduler as runtime


ROOT = Path(__file__).resolve().parents[1]


class InternalNotificationSchedulerRuntimeTests(unittest.TestCase):
    def test_runtime_flag_is_fail_closed(self) -> None:
        disabled_values = (None, "", "false", "0", "no", "off", "unexpected")
        for value in disabled_values:
            environment = {} if value is None else {runtime.RUNTIME_ENABLED_ENV: value}
            with self.subTest(value=value):
                self.assertFalse(runtime.runtime_enabled(environment))
        for value in ("true", "TRUE", "1", "yes", "tak", "on"):
            with self.subTest(value=value):
                self.assertTrue(runtime.runtime_enabled({runtime.RUNTIME_ENABLED_ENV: value}))

    def test_disabled_modes_exit_zero_without_loading_runtime(self) -> None:
        for mode in ("--once", "--check"):
            with self.subTest(mode=mode), patch.dict(os.environ, {}, clear=True), patch.object(
                runtime, "_run_once", side_effect=AssertionError("runtime loaded")
            ), patch.object(runtime, "_run_check", side_effect=AssertionError("runtime loaded")):
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    exit_code = runtime.main([mode])
                payload = output.getvalue()
                self.assertEqual(exit_code, 0)
                self.assertIn('"status":"disabled"', payload)
                self.assertIn('"exit_code":0', payload)

    def test_enabled_runtime_requires_explicit_database_configuration(self) -> None:
        environment = {runtime.RUNTIME_ENABLED_ENV: "true"}
        error_output = io.StringIO()
        with patch.dict(os.environ, environment, clear=True), contextlib.redirect_stderr(error_output):
            exit_code = runtime.main(["--check"])
        self.assertEqual(exit_code, 1)
        self.assertIn('"status":"configuration_error"', error_output.getvalue())
        self.assertNotIn("DATABASE_URL", error_output.getvalue())

    def test_check_uses_read_only_sqlite_and_counts_due_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "runtime-check.sqlite3"
            connection = sqlite3.connect(path)
            connection.execute(
                """
                CREATE TABLE internal_notification_schedules (
                    internal_notification_schedule_id INTEGER PRIMARY KEY,
                    enabled INTEGER NOT NULL,
                    next_run_at_utc TEXT
                )
                """
            )
            connection.execute(
                "INSERT INTO internal_notification_schedules VALUES (1, 1, '2000-01-01T00:00:00+00:00')"
            )
            connection.execute(
                "INSERT INTO internal_notification_schedules VALUES (2, 1, '2999-01-01T00:00:00+00:00')"
            )
            connection.commit()
            connection.close()
            before_hash = hashlib.sha256(path.read_bytes()).hexdigest()
            environment = {
                runtime.RUNTIME_ENABLED_ENV: "true",
                "INVOICE_DB_ENGINE": "sqlite",
                "INVOICE_SQLITE_PATH": str(path),
                "INVOICE_ENABLE_DEMO_SEED": "0",
            }
            import app.db

            output = io.StringIO()
            with patch.dict(os.environ, environment, clear=True), patch.object(
                app.db, "DB_ENGINE", "sqlite"
            ), patch.object(app.db, "SQLITE_DB_PATH", path), contextlib.redirect_stdout(output):
                exit_code = runtime.main(["--check"])
            self.assertEqual(exit_code, 0)
            self.assertIn('"database_connection":"read_only_ok"', output.getvalue())
            self.assertIn('"timezone":"Europe/Warsaw"', output.getvalue())
            self.assertIn('"due_schedules":1', output.getvalue())
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), before_hash)

    def test_system_error_report_is_sanitized(self) -> None:
        environment = {
            runtime.RUNTIME_ENABLED_ENV: "true",
            "INVOICE_DB_ENGINE": "sqlite",
            "INVOICE_SQLITE_PATH": "unused.sqlite3",
        }
        error_output = io.StringIO()
        with patch.dict(os.environ, environment, clear=True), patch.object(
            runtime, "_run_check", side_effect=RuntimeError("postgresql://user:secret@example")
        ), contextlib.redirect_stderr(error_output):
            exit_code = runtime.main(["--check"])
        self.assertEqual(exit_code, 1)
        self.assertIn('"status":"system_error"', error_output.getvalue())
        self.assertNotIn("secret", error_output.getvalue())
        self.assertNotIn("postgresql://", error_output.getvalue())

    def test_import_and_backend_do_not_autostart_scheduler(self) -> None:
        result = subprocess.run(
            [sys.executable, "-c", "import app.jobs.internal_notifications_scheduler; print('import-ok')"],
            cwd=ROOT,
            env={**os.environ, runtime.RUNTIME_ENABLED_ENV: ""},
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "import-ok")
        for relative in ("run.py", "app/bootstrap.py"):
            content = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn("internal_notifications_scheduler", content)


if __name__ == "__main__":
    unittest.main()
