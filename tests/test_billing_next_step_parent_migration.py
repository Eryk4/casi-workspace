from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.db import (
    DatabaseConnection,
    POSTGRES_SCHEMA,
    SQLITE_SCHEMA,
    _ensure_billing_next_step_parent_schema,
    _run_schema_script,
    initialize_database,
)


class BillingNextStepParentMigrationTests(unittest.TestCase):
    def _connection(self) -> DatabaseConnection:
        raw_connection = sqlite3.connect(":memory:")
        raw_connection.row_factory = sqlite3.Row
        return DatabaseConnection(raw_connection, backend="sqlite", driver_name="sqlite")

    def _financial_snapshot(self, connection: sqlite3.Connection) -> dict[str, str]:
        snapshot: dict[str, str] = {}
        for table_name in (
            "billing_transactions",
            "billing_charges",
            "billing_payment_matches",
            "billing_payer_ledger_entries",
        ):
            rows = connection.execute(f"SELECT * FROM {table_name} ORDER BY rowid").fetchall()
            serialized = json.dumps([tuple(row) for row in rows], ensure_ascii=False, default=str)
            snapshot[table_name] = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        return snapshot

    def _initialize_at(self, database_path: Path) -> None:
        with patch("app.db.SQLITE_DB_PATH", database_path):
            initialize_database()

    def test_full_initialize_database_from_empty_database_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "empty.sqlite3"

            self._initialize_at(database_path)
            self._initialize_at(database_path)

            connection = sqlite3.connect(database_path)
            connection.row_factory = sqlite3.Row
            try:
                columns = {
                    row["name"]: row
                    for row in connection.execute("PRAGMA table_info(billing_next_step_events)")
                }
                indexes = {
                    row["name"]: row
                    for row in connection.execute("PRAGMA index_list(billing_next_step_events)")
                }
                self.assertIn("parent_event_id", columns)
                self.assertEqual(int(columns["parent_event_id"]["notnull"]), 0)
                self.assertIn("idx_billing_next_step_events_parent_unique", indexes)
                self.assertEqual(int(indexes["idx_billing_next_step_events_parent_unique"]["unique"]), 1)
                self.assertEqual(connection.execute("PRAGMA quick_check").fetchone()[0], "ok")
            finally:
                connection.close()

    def test_full_initialize_database_upgrades_realistic_old_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "legacy.sqlite3"
            legacy_schema = SQLITE_SCHEMA.replace("    parent_event_id INTEGER,\n", "", 1).replace(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_billing_next_step_events_parent_unique\n"
                "    ON billing_next_step_events(parent_event_id);\n",
                "",
                1,
            )
            raw_connection = sqlite3.connect(database_path)
            raw_connection.row_factory = sqlite3.Row
            connection = DatabaseConnection(raw_connection, backend="sqlite", driver_name="sqlite")
            try:
                _run_schema_script(connection, legacy_schema)
                connection.execute("PRAGMA foreign_keys = OFF")
                connection.execute(
                    """
                    INSERT INTO billing_next_step_events (
                        organization_id, target_type, target_id, related_issue_key,
                        step_type, event_action, title, note_text, planned_for,
                        created_by_user_id, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (1, "payer", 7, None, "call", "planned", "Istniejacy krok", None, "2026-12-18", 1, "2026-01-01T10:00:00"),
                )
                connection.execute(
                    """
                    INSERT INTO billing_next_step_events (
                        organization_id, target_type, target_id, related_issue_key,
                        step_type, event_action, title, note_text, planned_for,
                        created_by_user_id, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (1, "payer", 7, None, "call", "completed", "Historyczny completed", None, None, 1, "2026-01-02T10:00:00"),
                )
                connection.execute(
                    """
                    INSERT INTO billing_transactions (
                        organization_id, billing_bank_account_id, booking_date, amount,
                        direction, transaction_hash, created_at, updated_at
                    ) VALUES (1, 1, '2026-01-01', 100, 'incoming', 'migration-test', '2026-01-01', '2026-01-01')
                    """
                )
                connection.execute(
                    """
                    INSERT INTO billing_charges (
                        organization_id, billing_charge_batch_id, billing_model_id,
                        billing_student_id, billing_payer_id, school_year, period_label,
                        due_date, unit_rate_amount, base_amount, total_amount, created_at, updated_at
                    ) VALUES (1, 1, 1, 1, 1, '2025/2026', '2026-01', '2026-01-10', 100, 100, 100, '2026-01-01', '2026-01-01')
                    """
                )
                connection.execute(
                    """
                    INSERT INTO billing_payment_matches (
                        organization_id, billing_transaction_id, billing_payer_id,
                        matched_amount, matched_at
                    ) VALUES (1, 1, 1, 100, '2026-01-01')
                    """
                )
                connection.execute(
                    """
                    INSERT INTO billing_payer_ledger_entries (
                        organization_id, billing_payer_id, entry_kind,
                        amount_delta, balance_after, created_at
                    ) VALUES (1, 1, 'payment', -100, 0, '2026-01-01')
                    """
                )
                connection.commit()
            finally:
                connection.close()

            before_connection = sqlite3.connect(database_path)
            before_connection.row_factory = sqlite3.Row
            try:
                expected_events = [
                    tuple(row)
                    for row in before_connection.execute(
                        "SELECT * FROM billing_next_step_events ORDER BY billing_next_step_event_id"
                    )
                ]
                financial_before = self._financial_snapshot(before_connection)
            finally:
                before_connection.close()

            self._initialize_at(database_path)
            self._initialize_at(database_path)

            migrated_connection = sqlite3.connect(database_path)
            migrated_connection.row_factory = sqlite3.Row
            try:
                columns = {
                    row["name"]: row
                    for row in migrated_connection.execute("PRAGMA table_info(billing_next_step_events)")
                }
                indexes = {
                    row["name"]: row
                    for row in migrated_connection.execute("PRAGMA index_list(billing_next_step_events)")
                }
                migrated_events = [
                    tuple(row)[:-1]
                    for row in migrated_connection.execute(
                        "SELECT * FROM billing_next_step_events ORDER BY billing_next_step_event_id"
                    )
                ]
                self.assertIn("parent_event_id", columns)
                self.assertEqual(int(columns["parent_event_id"]["notnull"]), 0)
                self.assertIn("idx_billing_next_step_events_parent_unique", indexes)
                self.assertEqual(int(indexes["idx_billing_next_step_events_parent_unique"]["unique"]), 1)
                self.assertEqual(
                    [row["name"] for row in migrated_connection.execute(
                        "PRAGMA index_info(idx_billing_next_step_events_parent_unique)"
                    )],
                    ["parent_event_id"],
                )
                self.assertEqual(expected_events, migrated_events)
                self.assertEqual(
                    migrated_connection.execute(
                        "SELECT COUNT(*) FROM billing_next_step_events WHERE parent_event_id IS NULL"
                    ).fetchone()[0],
                    2,
                )
                self.assertEqual(financial_before, self._financial_snapshot(migrated_connection))
                self.assertEqual(
                    migrated_connection.execute("PRAGMA quick_check").fetchone()[0],
                    "ok",
                )

                first_parent = migrated_connection.execute(
                    "SELECT billing_next_step_event_id FROM billing_next_step_events WHERE event_action = 'planned'"
                ).fetchone()[0]
                second_parent = migrated_connection.execute(
                    """
                    INSERT INTO billing_next_step_events (
                        organization_id, target_type, target_id, step_type,
                        event_action, title, created_by_user_id, created_at
                    ) VALUES (1, 'payer', 7, 'call', 'planned', 'Drugi krok', 1, '2026-01-03')
                    """
                ).lastrowid
                migrated_connection.execute(
                    """
                    INSERT INTO billing_next_step_events (
                        parent_event_id, organization_id, target_type, target_id,
                        step_type, event_action, title, created_by_user_id, created_at
                    ) VALUES (?, 1, 'payer', 7, 'call', 'completed', 'Pierwszy done', 1, '2026-01-04')
                    """,
                    (first_parent,),
                )
                migrated_connection.execute(
                    """
                    INSERT INTO billing_next_step_events (
                        parent_event_id, organization_id, target_type, target_id,
                        step_type, event_action, title, created_by_user_id, created_at
                    ) VALUES (?, 1, 'payer', 7, 'call', 'completed', 'Drugi done', 1, '2026-01-05')
                    """,
                    (second_parent,),
                )
                with self.assertRaises(sqlite3.IntegrityError):
                    migrated_connection.execute(
                        """
                        INSERT INTO billing_next_step_events (
                            parent_event_id, organization_id, target_type, target_id,
                            step_type, event_action, title, created_by_user_id, created_at
                        ) VALUES (?, 1, 'payer', 7, 'call', 'completed', 'Duplikat', 1, '2026-01-06')
                        """,
                        (first_parent,),
                    )
            finally:
                migrated_connection.close()

    def test_fresh_schema_contains_nullable_parent_and_unique_index(self) -> None:
        connection = self._connection()
        try:
            _run_schema_script(connection, SQLITE_SCHEMA)
            _ensure_billing_next_step_parent_schema(connection)
            columns = {
                row["name"]: row
                for row in connection.execute("PRAGMA table_info(billing_next_step_events)").fetchall()
            }
            self.assertIn("parent_event_id", columns)
            self.assertEqual(int(columns["parent_event_id"]["notnull"]), 0)

            indexes = {
                row["name"]: row
                for row in connection.execute("PRAGMA index_list(billing_next_step_events)").fetchall()
            }
            self.assertIn("idx_billing_next_step_events_parent_unique", indexes)
            self.assertEqual(int(indexes["idx_billing_next_step_events_parent_unique"]["unique"]), 1)
            self.assertIn("parent_event_id BIGINT", POSTGRES_SCHEMA)
            self.assertNotIn("idx_billing_next_step_events_parent_unique", POSTGRES_SCHEMA)
        finally:
            connection.close()

    def test_old_schema_is_upgraded_additively_and_rejects_second_completion(self) -> None:
        connection = self._connection()
        try:
            connection.execute(
                """
                CREATE TABLE billing_next_step_events (
                    billing_next_step_event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_action TEXT NOT NULL
                )
                """
            )
            _ensure_billing_next_step_parent_schema(connection)
            _ensure_billing_next_step_parent_schema(connection)

            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(billing_next_step_events)").fetchall()
            }
            self.assertIn("parent_event_id", columns)

            first_parent = connection.execute(
                "INSERT INTO billing_next_step_events (event_action) VALUES ('planned')"
            ).lastrowid
            second_parent = connection.execute(
                "INSERT INTO billing_next_step_events (event_action) VALUES ('planned')"
            ).lastrowid
            connection.execute(
                "INSERT INTO billing_next_step_events (event_action, parent_event_id) VALUES ('completed', ?)",
                (first_parent,),
            )
            connection.execute(
                "INSERT INTO billing_next_step_events (event_action, parent_event_id) VALUES ('completed', ?)",
                (second_parent,),
            )
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(
                    "INSERT INTO billing_next_step_events (event_action, parent_event_id) VALUES ('completed', ?)",
                    (first_parent,),
                )
        finally:
            connection.close()


if __name__ == "__main__":
    unittest.main()
