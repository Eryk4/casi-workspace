from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import plan_storage_migration


class StorageMigrationPlanTests(unittest.TestCase):
    def test_scans_local_storage_structure_and_builds_report_keys(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            document = root / "dokumenty" / "organizacje" / "casi" / "faktura.pdf"
            document.parent.mkdir(parents=True)
            document.write_bytes(b"pdf")

            plan = plan_storage_migration.build_migration_plan(
                storage_root=root,
                s3_prefix="casi/dev-test",
                include_backups=False,
                max_large_file_mb=100,
            )

        self.assertEqual(plan.file_count, 1)
        item = plan.files[0]
        self.assertEqual(item.area, "dokumenty")
        self.assertEqual(item.storage_key, "dokumenty/organizacje/casi/faktura.pdf")
        self.assertEqual(item.s3_object_key, "casi/dev-test/dokumenty/organizacje/casi/faktura.pdf")
        self.assertEqual(item.status, "planned")
        self.assertEqual(item.warnings, [])
        self.assertEqual(item.issues, [])

    def test_default_report_prefix_is_used_when_prefix_is_empty(self) -> None:
        self.assertEqual(plan_storage_migration.normalize_s3_prefix(""), "casi/dev-test")
        self.assertEqual(
            plan_storage_migration.build_s3_object_key("", "dokumenty/a.pdf"),
            "casi/dev-test/dokumenty/a.pdf",
        )

    def test_detects_zero_size_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            empty_file = root / "ocr" / "empty.txt"
            empty_file.parent.mkdir(parents=True)
            empty_file.write_bytes(b"")

            plan = plan_storage_migration.build_migration_plan(
                storage_root=root,
                s3_prefix="casi/dev-test",
                include_backups=False,
                max_large_file_mb=100,
            )

        self.assertEqual(plan.files[0].status, "warning")
        self.assertIn("zero_size_file", plan.files[0].warnings)
        self.assertEqual(plan.issue_count_by_severity["warning"], 1)

    def test_detects_duplicate_sha256(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first = root / "dokumenty" / "a.txt"
            second = root / "wiedza" / "b.txt"
            first.parent.mkdir(parents=True)
            second.parent.mkdir(parents=True)
            first.write_bytes(b"same")
            second.write_bytes(b"same")

            plan = plan_storage_migration.build_migration_plan(
                storage_root=root,
                s3_prefix="casi/dev-test",
                include_backups=False,
                max_large_file_mb=100,
            )

        self.assertEqual(plan.file_count, 2)
        self.assertTrue(all("duplicate_sha256" in item.issues for item in plan.files))
        self.assertTrue(all("duplicate_sha256" not in item.warnings for item in plan.files))
        self.assertEqual(plan.issue_count_by_severity["info"], 2)
        self.assertEqual(plan.issue_count_by_severity["warning"], 0)

    def test_detects_storage_key_conflicts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first = root / "dokumenty" / "a.txt"
            second = root / "wiedza" / "b.txt"
            first.parent.mkdir(parents=True)
            second.parent.mkdir(parents=True)
            first.write_bytes(b"first")
            second.write_bytes(b"second")

            with patch(
                "scripts.plan_storage_migration.build_storage_key",
                side_effect=["dokumenty/same.txt", "DOKUMENTY/same.txt"],
            ):
                plan = plan_storage_migration.build_migration_plan(
                    storage_root=root,
                    s3_prefix="casi/dev-test",
                    include_backups=False,
                    max_large_file_mb=100,
                )

        self.assertEqual(plan.file_count, 2)
        self.assertTrue(all("storage_key_conflict" in item.warnings for item in plan.files))
        self.assertEqual(plan.blocker_count, 2)
        self.assertTrue(all(item.status == "blocker" for item in plan.files))

    def test_missing_storage_root_is_reported_without_crashing(self) -> None:
        missing_root = Path(tempfile.gettempdir()) / "casi-missing-storage-root-for-test"
        plan = plan_storage_migration.build_migration_plan(
            storage_root=missing_root,
            s3_prefix="casi/dev-test",
            include_backups=False,
            max_large_file_mb=100,
        )

        self.assertEqual(plan.file_count, 0)
        self.assertIn("storage_root_missing", plan.global_issues)
        self.assertEqual(plan.issue_count_by_severity["error"], 1)

    def test_unknown_area_and_temporary_file_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            temp_file = root / "inne" / "upload.part"
            temp_file.parent.mkdir(parents=True)
            temp_file.write_bytes(b"partial")

            plan = plan_storage_migration.build_migration_plan(
                storage_root=root,
                s3_prefix="casi/dev-test",
                include_backups=False,
                max_large_file_mb=100,
            )

        item = plan.files[0]
        self.assertEqual(item.area, "unknown_area")
        self.assertIn("unknown_area", item.warnings)
        self.assertIn("temporary_file", item.warnings)
        self.assertEqual(plan.issue_count_by_severity["warning"], 2)

    def test_backups_are_skipped_by_default_but_can_be_included(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            backup = root / "backup" / "dump.zip"
            backup.parent.mkdir(parents=True)
            backup.write_bytes(b"backup")

            skipped = plan_storage_migration.build_migration_plan(
                storage_root=root,
                s3_prefix="casi/dev-test",
                include_backups=False,
                max_large_file_mb=100,
            )
            included = plan_storage_migration.build_migration_plan(
                storage_root=root,
                s3_prefix="casi/dev-test",
                include_backups=True,
                max_large_file_mb=100,
            )

        self.assertEqual(skipped.files[0].status, "skipped_backup")
        self.assertIn("backup_skipped_by_default", skipped.files[0].issues)
        self.assertNotIn("backup_skipped_by_default", skipped.files[0].warnings)
        self.assertEqual(skipped.issue_count_by_severity["info"], 1)
        self.assertEqual(included.files[0].status, "planned")
        self.assertNotIn("backup_skipped_by_default", included.files[0].issues)

    def test_cli_writes_reports_without_s3_or_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "storage"
            root.mkdir()
            source = root / "tablica" / "image.png"
            source.parent.mkdir(parents=True)
            source.write_bytes(b"png")
            output_json = Path(temp_dir) / "plan.json"
            output_md = Path(temp_dir) / "plan.md"

            result = plan_storage_migration.main(
                [
                    "--storage-root",
                    str(root),
                    "--output-json",
                    str(output_json),
                    "--output-md",
                    str(output_md),
                ]
            )

            payload = json.loads(output_json.read_text(encoding="utf-8"))
            markdown = output_md.read_text(encoding="utf-8")
            json_exists = output_json.exists()
            md_exists = output_md.exists()

        self.assertEqual(result, 0)
        self.assertTrue(json_exists)
        self.assertTrue(md_exists)
        self.assertEqual(payload["s3_prefix"], "casi/dev-test")
        self.assertEqual(payload["blocker_count"], 0)
        self.assertEqual(payload["files"][0]["storage_key"], "tablica/image.png")
        self.assertEqual(payload["files"][0]["local_path"], "tablica/image.png")
        self.assertIn("recommended_next_actions", payload)
        self.assertIn("[redacted in markdown", markdown)
        self.assertNotIn(str(root), markdown)


if __name__ == "__main__":
    unittest.main()
