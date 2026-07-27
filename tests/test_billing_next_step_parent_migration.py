from __future__ import annotations

import sqlite3
import unittest

from app.db import (
    DatabaseConnection,
    POSTGRES_SCHEMA,
    SQLITE_SCHEMA,
    _ensure_billing_next_step_parent_schema,
    _run_schema_script,
)


class BillingNextStepParentMigrationTests(unittest.TestCase):
    def _connection(self) -> DatabaseConnection:
        raw_connection = sqlite3.connect(":memory:")
        raw_connection.row_factory = sqlite3.Row
        return DatabaseConnection(raw_connection, backend="sqlite", driver_name="sqlite")

    def test_fresh_schema_contains_nullable_parent_and_unique_index(self) -> None:
        connection = self._connection()
        try:
            _run_schema_script(connection, SQLITE_SCHEMA)
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
            self.assertIn("idx_billing_next_step_events_parent_unique", POSTGRES_SCHEMA)
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
