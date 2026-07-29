from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.db import POSTGRES_SCHEMA, SQLITE_SCHEMA, initialize_database


class InternalNotificationsMigrationTests(unittest.TestCase):
    def _initialize_at(self, database_path: Path) -> None:
        with patch("app.db.SQLITE_DB_PATH", database_path):
            initialize_database()

    @staticmethod
    def _table_hash(connection: sqlite3.Connection, table_name: str) -> str:
        rows = connection.execute(f"SELECT * FROM {table_name} ORDER BY rowid").fetchall()
        payload = json.dumps([tuple(row) for row in rows], ensure_ascii=False, default=str)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def test_full_initialize_from_empty_is_idempotent_and_complete(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "empty.sqlite3"
            self._initialize_at(database_path)
            self._initialize_at(database_path)
            connection = sqlite3.connect(database_path)
            connection.row_factory = sqlite3.Row
            try:
                tables = {row["name"] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                self.assertIn("internal_notifications", tables)
                self.assertIn("internal_notification_state_events", tables)
                notification_indexes = {row["name"]: row for row in connection.execute("PRAGMA index_list(internal_notifications)")}
                state_indexes = {row["name"]: row for row in connection.execute("PRAGMA index_list(internal_notification_state_events)")}
                self.assertEqual(int(notification_indexes["idx_internal_notifications_dedupe_key"]["unique"]), 1)
                self.assertEqual(int(notification_indexes["idx_internal_notifications_source_unique"]["unique"]), 1)
                self.assertIn("idx_internal_notifications_recipient_created", notification_indexes)
                self.assertIn("idx_internal_notification_state_latest", state_indexes)
                self.assertEqual(connection.execute("PRAGMA quick_check").fetchone()[0], "ok")
            finally:
                connection.close()

    def test_old_schema_upgrade_preserves_existing_and_financial_tables(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "old.sqlite3"
            self._initialize_at(database_path)
            connection = sqlite3.connect(database_path)
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("DROP TABLE internal_notification_state_events")
            connection.execute("DROP TABLE internal_notifications")
            connection.execute(
                "INSERT INTO organizations (name, slug, is_active, created_at, updated_at) VALUES (?, ?, 1, ?, ?)",
                ("Historyczna", "historyczna", "2026-01-01", "2026-01-01"),
            )
            existing_org_id = int(connection.execute("SELECT MAX(organization_id) FROM organizations").fetchone()[0])
            financial_before = {
                table: self._table_hash(connection, table)
                for table in ("billing_transactions", "billing_charges", "billing_payment_matches", "billing_payer_ledger_entries")
            }
            connection.commit()
            connection.close()

            self._initialize_at(database_path)
            self._initialize_at(database_path)
            connection = sqlite3.connect(database_path)
            try:
                self.assertEqual(connection.execute("SELECT name FROM organizations WHERE organization_id = ?", (existing_org_id,)).fetchone()[0], "Historyczna")
                financial_after = {
                    table: self._table_hash(connection, table)
                    for table in financial_before
                }
                self.assertEqual(financial_after, financial_before)
                self.assertEqual(connection.execute("PRAGMA quick_check").fetchone()[0], "ok")
            finally:
                connection.close()

    def test_uniqueness_foreign_keys_and_postgres_schema_are_safe(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "constraints.sqlite3"
            self._initialize_at(database_path)
            connection = sqlite3.connect(database_path)
            connection.execute("PRAGMA foreign_keys = ON")
            try:
                connection.execute(
                    "INSERT INTO organizations (name, slug, created_at, updated_at) VALUES (?, ?, ?, ?)",
                    ("Constraints", "constraints", "2026-07-29", "2026-07-29"),
                )
                org_id = int(connection.execute("SELECT last_insert_rowid()").fetchone()[0])
                connection.execute(
                    """
                    INSERT INTO users (
                        login, organization_id, password_hash, password_salt, role, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    ("constraints-user", org_id, "hash", "salt", "administrator", "2026-07-29", "2026-07-29"),
                )
                user_id = int(connection.execute("SELECT last_insert_rowid()").fetchone()[0])
                values = (org_id, user_id, "billing_next_step_attention", 99, "overdue", "2026-07-29", "T", "billing_summary", "Podsumowanie", "dedupe", user_id, "2026-07-29T10:00:00+00:00")
                query = """
                    INSERT INTO internal_notifications (
                        organization_id, recipient_user_id, source_type, source_event_id, reason_code,
                        detected_on, title_snapshot, target_type, target_label_snapshot, dedupe_key,
                        created_by_user_id, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                connection.execute(query, values)
                with self.assertRaises(sqlite3.IntegrityError):
                    connection.execute(query, values)
                with self.assertRaises(sqlite3.IntegrityError):
                    connection.execute(query, (org_id, 999999, *values[2:]))
                connection.rollback()
            finally:
                connection.close()

        self.assertIn("CREATE TABLE IF NOT EXISTS internal_notifications", POSTGRES_SCHEMA)
        self.assertIn("CREATE TABLE IF NOT EXISTS internal_notification_state_events", POSTGRES_SCHEMA)
        self.assertIn("BIGSERIAL PRIMARY KEY", POSTGRES_SCHEMA)
        self.assertIn("idx_internal_notifications_source_unique", POSTGRES_SCHEMA)
        self.assertIn("ON DELETE RESTRICT", POSTGRES_SCHEMA)
        self.assertIn("idx_internal_notification_state_latest", SQLITE_SCHEMA)


if __name__ == "__main__":
    unittest.main()
