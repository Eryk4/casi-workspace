from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.db import POSTGRES_SCHEMA, initialize_database


class InternalNotificationSchedulerMigrationTests(unittest.TestCase):
    def _initialize(self, path: Path) -> None:
        with patch("app.db.SQLITE_DB_PATH", path):
            initialize_database()

    @staticmethod
    def _hash(connection: sqlite3.Connection, table: str) -> str:
        rows = connection.execute(f"SELECT * FROM {table} ORDER BY rowid").fetchall()
        return hashlib.sha256(json.dumps([tuple(row) for row in rows], default=str).encode()).hexdigest()

    def test_empty_and_old_schema_bootstrap_are_idempotent_and_preserve_data(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "scheduler.sqlite3"
            self._initialize(path)
            connection = sqlite3.connect(path)
            connection.execute("DROP TABLE internal_notification_schedule_runs")
            connection.execute("DROP TABLE internal_notification_schedules")
            preserved = {
                table: self._hash(connection, table)
                for table in (
                    "billing_transactions",
                    "billing_charges",
                    "billing_payment_matches",
                    "billing_payer_ledger_entries",
                    "billing_next_step_events",
                    "internal_notifications",
                    "internal_notification_state_events",
                )
            }
            connection.commit()
            connection.close()

            self._initialize(path)
            self._initialize(path)
            connection = sqlite3.connect(path)
            connection.row_factory = sqlite3.Row
            try:
                tables = {row["name"] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                self.assertIn("internal_notification_schedules", tables)
                self.assertIn("internal_notification_schedule_runs", tables)
                self.assertEqual(
                    {table: self._hash(connection, table) for table in preserved},
                    preserved,
                )
                self.assertEqual(connection.execute("PRAGMA quick_check").fetchone()[0], "ok")
            finally:
                connection.close()

    def test_uniqueness_status_constraints_and_indexes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "constraints.sqlite3"
            self._initialize(path)
            connection = sqlite3.connect(path)
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute(
                "INSERT INTO organizations (name, slug, created_at, updated_at) VALUES ('Scheduler', 'scheduler', 'x', 'x')"
            )
            organization_id = connection.execute("SELECT last_insert_rowid()").fetchone()[0]
            connection.execute(
                """INSERT INTO users (login, organization_id, password_hash, password_salt, role, created_at, updated_at)
                   VALUES ('scheduler-user', ?, 'h', 's', 'administrator', 'x', 'x')""",
                (organization_id,),
            )
            user_id = connection.execute("SELECT last_insert_rowid()").fetchone()[0]
            schedule_values = (organization_id, user_id, "billing_next_step_attention", 1, "daily", "Europe/Warsaw", "08:00", "2026-07-29T06:00:00+00:00", user_id, user_id, "x", "x")
            schedule_sql = """INSERT INTO internal_notification_schedules
                (organization_id, recipient_user_id, source_type, enabled, cadence, timezone_name, local_time,
                 next_run_at_utc, created_by_user_id, updated_by_user_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
            connection.execute(schedule_sql, schedule_values)
            schedule_id = connection.execute("SELECT last_insert_rowid()").fetchone()[0]
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(schedule_sql, schedule_values)
            run_values = (schedule_id, organization_id, user_id, "billing_next_step_attention", "2026-07-29", "2026-07-29", "2026-07-29T06:00:00+00:00", "pending", "x")
            run_sql = """INSERT INTO internal_notification_schedule_runs
                (schedule_id, organization_id, recipient_user_id, source_type, scheduled_local_date, as_of_date,
                 scheduled_for_utc, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""
            connection.execute(run_sql, run_values)
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(run_sql, run_values)
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(run_sql, (*run_values[:7], "sent", run_values[-1]))
            schedule_indexes = {row[1]: row for row in connection.execute("PRAGMA index_list(internal_notification_schedules)")}
            run_indexes = {row[1]: row for row in connection.execute("PRAGMA index_list(internal_notification_schedule_runs)")}
            self.assertEqual(schedule_indexes["idx_internal_notification_schedules_scope"][2], 1)
            self.assertEqual(run_indexes["idx_internal_notification_schedule_runs_day"][2], 1)
            self.assertIn("idx_internal_notification_schedules_due", schedule_indexes)
            self.assertIn("idx_internal_notification_schedule_runs_claim", run_indexes)
            self.assertEqual(connection.execute("PRAGMA quick_check").fetchone()[0], "ok")
            connection.close()

    def test_postgres_schema_is_additive_and_static_portable(self) -> None:
        self.assertIn("CREATE TABLE IF NOT EXISTS internal_notification_schedules", POSTGRES_SCHEMA)
        self.assertIn("CREATE TABLE IF NOT EXISTS internal_notification_schedule_runs", POSTGRES_SCHEMA)
        self.assertIn("BIGSERIAL PRIMARY KEY", POSTGRES_SCHEMA)
        self.assertIn("idx_internal_notification_schedules_scope", POSTGRES_SCHEMA)
        self.assertIn("idx_internal_notification_schedule_runs_day", POSTGRES_SCHEMA)
        self.assertNotIn("ALTER TABLE internal_notifications", POSTGRES_SCHEMA)


if __name__ == "__main__":
    unittest.main()
