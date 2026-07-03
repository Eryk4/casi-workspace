from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.reset_guard import (
    RESET_CONFIRMATION_ENV,
    ResetGuardError,
    prepare_local_sandbox_reset,
    validate_local_sandbox_reset_allowed,
)


class ResetGuardTests(unittest.TestCase):
    def test_blocks_without_explicit_local_sandbox_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "data"
            sqlite_path = data_dir / "invoice_ops.sqlite3"
            with self.assertRaises(ResetGuardError) as context:
                validate_local_sandbox_reset_allowed(
                    db_engine="sqlite",
                    sqlite_path=sqlite_path,
                    data_dir=data_dir,
                    allow_local_sandbox_reset="",
                )

        message = str(context.exception)
        self.assertIn(RESET_CONFIRMATION_ENV, message)
        self.assertIn("Reset/reseed zostal zablokowany", message)

    def test_blocks_when_database_url_is_active(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "data"
            sqlite_path = data_dir / "invoice_ops.sqlite3"
            with self.assertRaises(ResetGuardError) as context:
                validate_local_sandbox_reset_allowed(
                    db_engine="sqlite",
                    sqlite_path=sqlite_path,
                    data_dir=data_dir,
                    database_url="postgresql://example",
                    allow_local_sandbox_reset="1",
                )

        self.assertIn("DATABASE_URL", str(context.exception))

    def test_blocks_when_invoice_database_url_is_active(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "data"
            sqlite_path = data_dir / "invoice_ops.sqlite3"
            with self.assertRaises(ResetGuardError) as context:
                validate_local_sandbox_reset_allowed(
                    db_engine="sqlite",
                    sqlite_path=sqlite_path,
                    data_dir=data_dir,
                    invoice_database_url="postgresql://example",
                    allow_local_sandbox_reset="1",
                )

        self.assertIn("INVOICE_DATABASE_URL", str(context.exception))

    def test_blocks_sqlite_path_outside_data_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(ResetGuardError) as context:
                validate_local_sandbox_reset_allowed(
                    db_engine="sqlite",
                    sqlite_path=root / "outside.sqlite3",
                    data_dir=root / "data",
                    allow_local_sandbox_reset="1",
                )

        self.assertIn("nie znajduje sie pod lokalnym katalogiem data", str(context.exception))

    def test_blocks_non_sqlite_engine_even_with_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "data"
            sqlite_path = data_dir / "invoice_ops.sqlite3"
            with self.assertRaises(ResetGuardError) as context:
                validate_local_sandbox_reset_allowed(
                    db_engine="postgresql",
                    sqlite_path=sqlite_path,
                    data_dir=data_dir,
                    allow_local_sandbox_reset="1",
                )

        self.assertIn("silnik bazy nie jest SQLite", str(context.exception))

    def test_allows_local_sqlite_under_data_with_explicit_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "data"
            sqlite_path = data_dir / "invoice_ops.sqlite3"
            plan = validate_local_sandbox_reset_allowed(
                db_engine="sqlite",
                sqlite_path=sqlite_path,
                data_dir=data_dir,
                allow_local_sandbox_reset="1",
            )

        self.assertEqual(plan.sqlite_path, sqlite_path.resolve())
        self.assertEqual(plan.data_dir, data_dir.resolve())
        self.assertIsNone(plan.backup_path)

    def test_creates_backup_before_allowed_reset_when_sqlite_file_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "data"
            data_dir.mkdir()
            sqlite_path = data_dir / "invoice_ops.sqlite3"
            sqlite_path.write_bytes(b"local sqlite bytes")

            plan = prepare_local_sandbox_reset(
                db_engine="sqlite",
                sqlite_path=sqlite_path,
                data_dir=data_dir,
                allow_local_sandbox_reset="1",
            )

            self.assertIsNotNone(plan.backup_path)
            assert plan.backup_path is not None
            self.assertTrue(plan.backup_path.exists())
            self.assertEqual(plan.backup_path.read_bytes(), b"local sqlite bytes")
            self.assertTrue(str(plan.backup_path).startswith(str((data_dir / "backup").resolve())))

    def test_missing_sqlite_file_does_not_require_backup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "data"
            sqlite_path = data_dir / "invoice_ops.sqlite3"
            plan = prepare_local_sandbox_reset(
                db_engine="sqlite",
                sqlite_path=sqlite_path,
                data_dir=data_dir,
                allow_local_sandbox_reset="1",
            )

        self.assertIsNone(plan.backup_path)


if __name__ == "__main__":
    unittest.main()
