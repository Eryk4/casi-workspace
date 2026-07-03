from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_REPORT_PREFIX = "casi/dev-test"
DEFAULT_OUTPUT_JSON = Path("reports/storage_migration_plan.json")
DEFAULT_OUTPUT_MD = Path("reports/storage_migration_plan.md")
DEFAULT_LARGE_FILE_MB = 100
TEMPORARY_SUFFIXES = {".tmp", ".part", ".lock"}
KNOWN_AREAS = {"dokumenty", "ocr", "wiedza", "tablica", "backup", "organizacje"}
ISSUE_SEVERITY = {
    "backup_skipped_by_default": "info",
    "duplicate_sha256": "info",
    "large_file": "warning",
    "temporary_file": "warning",
    "unknown_area": "warning",
    "zero_size_file": "warning",
    "cannot_hash_file": "error",
    "cannot_stat_file": "error",
    "file_scan_error": "error",
    "storage_root_is_not_directory": "error",
    "storage_root_missing": "error",
    "invalid_relative_path": "blocker",
    "path_contains_parent_reference": "blocker",
    "storage_key_conflict": "blocker",
}
SEVERITY_ORDER = {"info": 0, "warning": 1, "error": 2, "blocker": 3}
SEVERITY_LABELS = ("info", "warning", "error", "blocker")


@dataclass
class PlannedFile:
    local_path: str
    area: str
    storage_key: str
    s3_object_key: str
    size_bytes: int
    sha256: str | None
    status: str
    warnings: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)


@dataclass
class MigrationPlan:
    generated_at: str
    storage_root: str
    s3_prefix: str
    file_count: int
    total_size_bytes: int
    files: list[PlannedFile]
    global_issues: list[str]
    summary_by_area: dict[str, dict[str, int]]
    issue_count_by_category: dict[str, int]
    issue_count_by_severity: dict[str, int]
    blocker_count: int
    recommended_next_actions: list[str]
    dry_run: bool = True


def normalize_s3_prefix(raw_prefix: str | None) -> str:
    normalized = str(raw_prefix or "").strip().strip("/")
    return normalized or DEFAULT_REPORT_PREFIX


def build_s3_object_key(s3_prefix: str, storage_key: str) -> str:
    prefix = normalize_s3_prefix(s3_prefix)
    return f"{prefix}/{storage_key.lstrip('/')}"


def issue_severity(issue_code: str) -> str:
    return ISSUE_SEVERITY.get(issue_code.split(":", 1)[0], "warning")


def issue_payload(issue_code: str) -> dict[str, str]:
    return {
        "code": issue_code,
        "category": issue_code.split(":", 1)[0],
        "severity": issue_severity(issue_code),
    }


def highest_severity(issue_codes: list[str]) -> str | None:
    if not issue_codes:
        return None
    return max((issue_severity(code) for code in issue_codes), key=lambda item: SEVERITY_ORDER[item])


def warning_codes(issue_codes: list[str]) -> list[str]:
    return sorted(code for code in issue_codes if issue_severity(code) in {"warning", "error", "blocker"})


def detect_area(storage_key: str) -> str:
    first_part = storage_key.split("/", 1)[0] if storage_key else ""
    if first_part in KNOWN_AREAS:
        return first_part
    return "unknown_area"


def build_storage_key(storage_root: Path, file_path: Path) -> str:
    relative = file_path.resolve().relative_to(storage_root.resolve())
    return relative.as_posix()


def sha256_file(file_path: Path) -> str:
    digest = hashlib.sha256()
    with file_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def planned_file_for_path(
    storage_root: Path,
    file_path: Path,
    *,
    s3_prefix: str,
    include_backups: bool,
    max_large_file_mb: int,
) -> PlannedFile:
    issues: list[str] = []
    try:
        storage_key = build_storage_key(storage_root, file_path)
    except Exception:
        storage_key = file_path.name
        issues.append("invalid_relative_path")

    normalized_parts = Path(storage_key).parts
    if ".." in normalized_parts:
        issues.append("path_contains_parent_reference")

    area = detect_area(storage_key)
    if area == "unknown_area":
        issues.append("unknown_area")

    if area == "backup" and not include_backups:
        issues.append("backup_skipped_by_default")

    if file_path.suffix.lower() in TEMPORARY_SUFFIXES:
        issues.append("temporary_file")

    try:
        size_bytes = file_path.stat().st_size
    except OSError:
        size_bytes = 0
        issues.append("cannot_stat_file")

    if size_bytes == 0:
        issues.append("zero_size_file")

    max_large_file_bytes = max(1, int(max_large_file_mb)) * 1024 * 1024
    if size_bytes > max_large_file_bytes:
        issues.append("large_file")

    try:
        digest = sha256_file(file_path)
    except OSError:
        digest = None
        issues.append("cannot_hash_file")

    status = "planned"
    severity = highest_severity(issues)
    if area == "backup" and not include_backups:
        status = "skipped_backup"
    elif severity in {"warning", "error", "blocker"}:
        status = severity

    return PlannedFile(
        local_path=storage_key,
        area=area,
        storage_key=storage_key,
        s3_object_key=build_s3_object_key(s3_prefix, storage_key),
        size_bytes=size_bytes,
        sha256=digest,
        status=status,
        warnings=warning_codes(sorted(set(issues))),
        issues=sorted(set(issues)),
    )


def iter_local_files(storage_root: Path) -> list[Path]:
    return sorted(
        path
        for path in storage_root.rglob("*")
        if path.is_file()
    )


def add_duplicate_and_conflict_warnings(files: list[PlannedFile]) -> None:
    hashes: dict[str, list[PlannedFile]] = defaultdict(list)
    keys: dict[str, list[PlannedFile]] = defaultdict(list)

    for item in files:
        if item.sha256:
            hashes[item.sha256].append(item)
        keys[item.storage_key.lower()].append(item)

    for duplicates in hashes.values():
        if len(duplicates) <= 1:
            continue
        for item in duplicates:
            item.issues.append("duplicate_sha256")

    for conflicts in keys.values():
        if len(conflicts) <= 1:
            continue
        for item in conflicts:
            item.issues.append("storage_key_conflict")

    for item in files:
        item.issues = sorted(set(item.issues))
        item.warnings = warning_codes(item.issues)
        severity = highest_severity(item.issues)
        if item.status == "skipped_backup":
            continue
        if severity in {"warning", "error", "blocker"}:
            item.status = severity


def build_summary_by_area(files: list[PlannedFile]) -> dict[str, dict[str, int]]:
    summary: dict[str, dict[str, int]] = {}
    for item in files:
        bucket = summary.setdefault(
            item.area,
            {
                "file_count": 0,
                "planned_count": 0,
                "info_count": 0,
                "warning_count": 0,
                "error_count": 0,
                "blocker_count": 0,
                "skipped_count": 0,
                "total_size_bytes": 0,
            },
        )
        bucket["file_count"] += 1
        bucket["total_size_bytes"] += int(item.size_bytes)
        if item.status == "planned":
            bucket["planned_count"] += 1
        elif item.status == "skipped_backup":
            bucket["skipped_count"] += 1
        elif item.status == "blocker":
            bucket["blocker_count"] += 1
        elif item.status == "error":
            bucket["error_count"] += 1
        elif item.status == "warning":
            bucket["warning_count"] += 1
        if any(issue_severity(code) == "info" for code in item.issues):
            bucket["info_count"] += 1
    return dict(sorted(summary.items()))


def count_issues_by_category(files: list[PlannedFile], global_issues: list[str]) -> dict[str, int]:
    counter: dict[str, int] = defaultdict(int)
    for item in files:
        for issue in item.issues:
            counter[issue.split(":", 1)[0]] += 1
    for issue in global_issues:
        counter[issue.split(":", 1)[0]] += 1
    return dict(sorted(counter.items()))


def count_issues_by_severity(files: list[PlannedFile], global_issues: list[str]) -> dict[str, int]:
    counter = {severity: 0 for severity in SEVERITY_LABELS}
    for item in files:
        for issue in item.issues:
            counter[issue_severity(issue)] += 1
    for issue in global_issues:
        counter[issue_severity(issue)] += 1
    return counter


def recommended_actions(
    *,
    issue_count_by_category: dict[str, int],
    issue_count_by_severity: dict[str, int],
) -> list[str]:
    actions: list[str] = []
    if issue_count_by_severity.get("blocker", 0):
        actions.append("Resolve blocker-level storage key or path issues before any real migration.")
    if issue_count_by_severity.get("error", 0):
        actions.append("Review error-level filesystem issues and rerun the dry-run plan.")
    if issue_count_by_category.get("unknown_area", 0):
        actions.append("Classify unknown top-level storage folders before migration.")
    if issue_count_by_category.get("temporary_file", 0):
        actions.append("Review temporary files and decide whether they should be excluded.")
    if issue_count_by_category.get("large_file", 0):
        actions.append("Review large files for upload limits and expected migration time.")
    if issue_count_by_category.get("zero_size_file", 0):
        actions.append("Review zero-byte files and decide whether they are valid placeholders.")
    if issue_count_by_category.get("duplicate_sha256", 0):
        actions.append("Duplicates are informational; keep storage keys unique and migrate them unless business cleanup is desired.")
    if not actions:
        actions.append("No blocking issues were found. Next safe step is a private DigitalOcean Spaces smoke test with prefix casi/dev-test.")
    elif not issue_count_by_severity.get("blocker", 0):
        actions.append("No blockers were found. Next safe step is a private DigitalOcean Spaces smoke test with prefix casi/dev-test.")
    return actions


def build_migration_plan(
    *,
    storage_root: Path,
    s3_prefix: str,
    include_backups: bool,
    max_large_file_mb: int,
) -> MigrationPlan:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    normalized_root = storage_root.resolve()
    normalized_prefix = normalize_s3_prefix(s3_prefix)
    global_issues: list[str] = []

    if not normalized_root.exists():
        global_issues.append("storage_root_missing")
        issue_count_by_category = count_issues_by_category([], global_issues)
        issue_count_by_severity = count_issues_by_severity([], global_issues)
        return MigrationPlan(
            generated_at=generated_at,
            storage_root=str(normalized_root),
            s3_prefix=normalized_prefix,
            file_count=0,
            total_size_bytes=0,
            files=[],
            global_issues=global_issues,
            summary_by_area={},
            issue_count_by_category=issue_count_by_category,
            issue_count_by_severity=issue_count_by_severity,
            blocker_count=issue_count_by_severity["blocker"],
            recommended_next_actions=recommended_actions(
                issue_count_by_category=issue_count_by_category,
                issue_count_by_severity=issue_count_by_severity,
            ),
        )

    if not normalized_root.is_dir():
        global_issues.append("storage_root_is_not_directory")
        issue_count_by_category = count_issues_by_category([], global_issues)
        issue_count_by_severity = count_issues_by_severity([], global_issues)
        return MigrationPlan(
            generated_at=generated_at,
            storage_root=str(normalized_root),
            s3_prefix=normalized_prefix,
            file_count=0,
            total_size_bytes=0,
            files=[],
            global_issues=global_issues,
            summary_by_area={},
            issue_count_by_category=issue_count_by_category,
            issue_count_by_severity=issue_count_by_severity,
            blocker_count=issue_count_by_severity["blocker"],
            recommended_next_actions=recommended_actions(
                issue_count_by_category=issue_count_by_category,
                issue_count_by_severity=issue_count_by_severity,
            ),
        )

    planned_files: list[PlannedFile] = []
    for file_path in iter_local_files(normalized_root):
        try:
            planned_files.append(
                planned_file_for_path(
                    normalized_root,
                    file_path,
                    s3_prefix=normalized_prefix,
                    include_backups=include_backups,
                    max_large_file_mb=max_large_file_mb,
                )
            )
        except Exception as error:
            global_issues.append(f"file_scan_error:{file_path}:{type(error).__name__}")

    add_duplicate_and_conflict_warnings(planned_files)
    issue_count_by_category = count_issues_by_category(planned_files, global_issues)
    issue_count_by_severity = count_issues_by_severity(planned_files, global_issues)
    return MigrationPlan(
        generated_at=generated_at,
        storage_root=str(normalized_root),
        s3_prefix=normalized_prefix,
        file_count=len(planned_files),
        total_size_bytes=sum(item.size_bytes for item in planned_files),
        files=planned_files,
        global_issues=sorted(set(global_issues)),
        summary_by_area=build_summary_by_area(planned_files),
        issue_count_by_category=issue_count_by_category,
        issue_count_by_severity=issue_count_by_severity,
        blocker_count=issue_count_by_severity["blocker"],
        recommended_next_actions=recommended_actions(
            issue_count_by_category=issue_count_by_category,
            issue_count_by_severity=issue_count_by_severity,
        ),
    )


def plan_to_dict(plan: MigrationPlan) -> dict[str, Any]:
    return {
        "generated_at": plan.generated_at,
        "dry_run": plan.dry_run,
        "storage_root": plan.storage_root,
        "s3_prefix": plan.s3_prefix,
        "file_count": plan.file_count,
        "total_size_bytes": plan.total_size_bytes,
        "global_issues": plan.global_issues,
        "summary_by_area": plan.summary_by_area,
        "issue_count_by_category": plan.issue_count_by_category,
        "issue_count_by_severity": plan.issue_count_by_severity,
        "blocker_count": plan.blocker_count,
        "migration_blocked": plan.blocker_count > 0,
        "recommended_next_actions": plan.recommended_next_actions,
        "files": [
            {
                "local_path": item.local_path,
                "area": item.area,
                "storage_key": item.storage_key,
                "s3_object_key": item.s3_object_key,
                "size_bytes": item.size_bytes,
                "sha256": item.sha256,
                "status": item.status,
                "warnings": item.warnings,
                "issues": [issue_payload(code) for code in item.issues],
            }
            for item in plan.files
        ],
    }


def write_json_report(plan: MigrationPlan, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(plan_to_dict(plan), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_markdown_report(plan: MigrationPlan, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    info_file_count = sum(1 for item in plan.files if any(issue_severity(code) == "info" for code in item.issues))
    warning_count = sum(1 for item in plan.files if any(issue_severity(code) == "warning" for code in item.issues))
    error_count = sum(1 for item in plan.files if any(issue_severity(code) == "error" for code in item.issues))
    blocker_file_count = sum(1 for item in plan.files if any(issue_severity(code) == "blocker" for code in item.issues))
    skipped_count = sum(1 for item in plan.files if item.status == "skipped_backup")
    lines = [
        "# Storage Migration Plan",
        "",
        "This is a dry-run report. No files were uploaded, moved, deleted, or modified.",
        "",
        f"- Generated at: `{plan.generated_at}`",
        f"- Storage root: `[redacted in markdown; see JSON metadata]`",
        f"- Report S3 prefix: `{plan.s3_prefix}`",
        f"- Files scanned: `{plan.file_count}`",
        f"- Total size: `{plan.total_size_bytes}` bytes",
        f"- Files with info: `{info_file_count}`",
        f"- Files with warnings: `{warning_count}`",
        f"- Files with errors: `{error_count}`",
        f"- Files with blockers: `{blocker_file_count}`",
        f"- Skipped backups: `{skipped_count}`",
        "",
        "## Czy migracja jest zablokowana?",
        "",
        "Tak." if plan.blocker_count > 0 else "Nie. Raport nie wykryl blockerow migracji.",
        "",
        f"- Blocker count: `{plan.blocker_count}`",
        f"- Error issue count: `{plan.issue_count_by_severity.get('error', 0)}`",
        f"- Warning issue count: `{plan.issue_count_by_severity.get('warning', 0)}`",
        f"- Info issue count: `{plan.issue_count_by_severity.get('info', 0)}`",
        "",
        "## Recommended Next Actions",
        "",
    ]
    lines.extend(f"- {action}" for action in plan.recommended_next_actions)
    lines.extend([
        "",
        "## Global Issues",
        "",
    ])
    if plan.global_issues:
        lines.extend(f"- `{issue}` ({issue_severity(issue)})" for issue in plan.global_issues)
    else:
        lines.append("- none")

    lines.extend(["", "## Issue Summary", ""])
    if plan.issue_count_by_category:
        lines.append("| Category | Count | Severity |")
        lines.append("| --- | ---: | --- |")
        for category, count in plan.issue_count_by_category.items():
            lines.append(f"| `{category}` | {count} | `{issue_severity(category)}` |")
    else:
        lines.append("- none")

    lines.extend(["", "## Summary By Area", ""])
    if plan.summary_by_area:
        lines.append("| Area | Files | Planned | Info | Warnings | Errors | Blockers | Skipped | Bytes |")
        lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
        for area, summary in plan.summary_by_area.items():
            lines.append(
                "| {area} | {file_count} | {planned_count} | {info_count} | {warning_count} | {error_count} | {blocker_count} | {skipped_count} | {total_size_bytes} |".format(
                    area=area,
                    **summary,
                )
            )
    else:
        lines.append("No files found.")

    lines.extend(["", "## Najwazniejsze problemy", ""])
    risky = [item for item in plan.files if any(issue_severity(code) in {"warning", "error", "blocker"} for code in item.issues)][:25]
    if risky:
        for item in risky:
            risk_codes = [f"{code} ({issue_severity(code)})" for code in item.issues if issue_severity(code) != "info"]
            lines.append(f"- `{item.storage_key}`: {', '.join(risk_codes)}")
    else:
        lines.append("- none")

    lines.extend(["", "## Informacyjne ostrzezenia", ""])
    info_items = [item for item in plan.files if any(issue_severity(code) == "info" for code in item.issues)][:25]
    if info_items:
        for item in info_items:
            info_codes = [code for code in item.issues if issue_severity(code) == "info"]
            lines.append(f"- `{item.storage_key}`: {', '.join(info_codes)}")
    else:
        lines.append("- none")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def has_warnings(plan: MigrationPlan) -> bool:
    return bool(plan.global_issues or any(item.warnings for item in plan.files))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Builds a dry-run local storage migration plan. It never uploads files to S3."
    )
    parser.add_argument("--storage-root", default=None, help="Local storage root. Defaults to app STORAGE_ROOT.")
    parser.add_argument("--s3-prefix", default=None, help="Report-only S3 prefix. Defaults to env or casi/dev-test.")
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON), help="JSON report path.")
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD), help="Markdown report path.")
    parser.add_argument("--include-backups", action="store_true", help="Mark backup files as planned instead of skipped.")
    parser.add_argument("--fail-on-warnings", action="store_true", help="Exit with code 1 when warnings are found.")
    parser.add_argument("--max-large-file-mb", type=int, default=DEFAULT_LARGE_FILE_MB, help="Large file warning threshold.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.storage_root:
        storage_root = Path(args.storage_root)
    else:
        from app.config import STORAGE_ROOT

        storage_root = STORAGE_ROOT

    prefix = args.s3_prefix
    if prefix is None:
        prefix = os.getenv("INVOICE_S3_PREFIX", DEFAULT_REPORT_PREFIX)

    plan = build_migration_plan(
        storage_root=storage_root,
        s3_prefix=prefix,
        include_backups=args.include_backups,
        max_large_file_mb=args.max_large_file_mb,
    )
    write_json_report(plan, Path(args.output_json))
    write_markdown_report(plan, Path(args.output_md))

    print("[OK] Storage migration dry-run plan generated.")
    print(f"[INFO] JSON report: {Path(args.output_json).resolve()}")
    print(f"[INFO] Markdown report: {Path(args.output_md).resolve()}")
    print(f"[INFO] Files scanned: {plan.file_count}")
    print(f"[INFO] Warnings: {sum(1 for item in plan.files if item.warnings)}")
    print(f"[INFO] Blockers: {plan.blocker_count}")
    if plan.global_issues:
        print(f"[WARN] Global issues: {', '.join(plan.global_issues)}")

    if args.fail_on_warnings and has_warnings(plan):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
