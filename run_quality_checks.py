from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent

HTTP_MODULES = [
    "tests.test_http_server_system",
    "tests.test_http_server_integrations",
    "tests.test_http_server_invoices",
    "tests.test_http_server_access",
    "tests.test_http_server_telegram",
]

TASK_MODULES = [
    "tests.test_task_service",
    "tests.test_task_commands",
    "tests.test_task_http",
    "tests.test_task_reminder_service",
]

INVOICE_MODULES = [
    "tests.test_invoice_duplicates",
    "tests.test_invoice_review_and_ksef",
    "tests.test_invoice_collaboration",
    "tests.test_ocr_engine",
    "tests.test_source_trace",
]

CALENDAR_MODULES = [
    "tests.test_calendar_service",
    "tests.test_calendar_google",
    "tests.test_calendar_http",
]

SEARCH_MODULES = [
    "tests.test_search_access",
    "tests.test_search_descriptive",
]

EMAIL_MODULES = [
    "tests.test_email_ingestion",
    "tests.test_email_scheduler",
    "tests.test_configure_email_settings",
    "tests.test_check_email_google_oauth_readiness",
]

KNOWLEDGE_MODULES = [
    "tests.test_knowledge_base",
    "tests.test_manager_assistant_http",
    "tests.test_support_center_http",
    "tests.test_whiteboard_http",
]

BILLING_MODULES = [
    "tests.test_billing_models",
    "tests.test_billing_charges",
    "tests.test_billing_customers",
    "tests.test_billing_schools",
    "tests.test_billing_import",
]

CORE_MODULES = [
    "tests.test_test_environment",
    "tests.test_auth_service",
    "tests.test_storage_service",
    "tests.test_organizations",
    "tests.test_demo_seed",
]

HTTP_SMOKE_MODULES = [
    "tests.test_http_server_system",
    "tests.test_http_server_access",
    "tests.test_http_server_invoices",
]

LEGACY_STATIC_MODULES = [
    "tests.test_legacy_static_http",
]


def build_test_env(label: str, *, storage_backend: str | None = "local") -> dict[str, str]:
    env = os.environ.copy()
    env["INVOICE_DATABASE_URL"] = ""
    env["DATABASE_URL"] = ""
    env["INVOICE_DB_ENGINE"] = "sqlite"
    if storage_backend is not None:
        env["INVOICE_STORAGE_BACKEND"] = storage_backend
    env["INVOICE_MAX_ACTIVE_DEVICES_PER_ACCOUNT"] = "3"
    safe_label = "".join(char.lower() if char.isalnum() else "_" for char in label).strip("_") or "tests"
    runtime_root = ROOT / "data" / "test_runtime" / "quality" / safe_label
    runtime_root.mkdir(parents=True, exist_ok=True)
    env["INVOICE_SQLITE_PATH"] = str((runtime_root / "invoice_ops.sqlite3").resolve())
    return env


def run_step(label: str, command: list[str], *, storage_backend: str | None = "local") -> None:
    started_at = time.perf_counter()
    print(f"\n=== {label} ===", flush=True)
    print(" ".join(command), flush=True)
    completed = subprocess.run(command, cwd=ROOT, env=build_test_env(label, storage_backend=storage_backend))
    elapsed = time.perf_counter() - started_at
    print(f"=== {label} finished in {elapsed:.1f}s with exit code {completed.returncode} ===", flush=True)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def run_frontend_step(label: str, npm_script: str) -> None:
    frontend_dir = ROOT / "frontend"
    npm_command = shutil.which("npm.cmd") if os.name == "nt" else shutil.which("npm")
    if not npm_command:
        fallback = "npm.cmd" if os.name == "nt" else "npm"
        npm_command = fallback

    command = [npm_command, "run", npm_script]
    started_at = time.perf_counter()
    print(f"\n=== {label} ===", flush=True)
    print(" ".join(command), flush=True)
    completed = subprocess.run(command, cwd=frontend_dir, env=os.environ.copy())
    elapsed = time.perf_counter() - started_at
    print(f"=== {label} finished in {elapsed:.1f}s with exit code {completed.returncode} ===", flush=True)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def run_unittest_group(label: str, modules: list[str]) -> None:
    run_step(label, [sys.executable, "-u", "-m", "unittest", *modules, "-v"])


def run_syntax_checks() -> None:
    run_step("Python compile", [sys.executable, "-m", "compileall", "app", "tests", "scripts", "run.py"])
    run_step("Frontend syntax", ["node", "--check", "static/app.js"])


def profile_smoke() -> None:
    run_syntax_checks()
    run_unittest_group("Core smoke", CORE_MODULES)
    run_unittest_group("Invoice smoke", INVOICE_MODULES)
    run_unittest_group("HTTP smoke", HTTP_SMOKE_MODULES)
    run_unittest_group("Search smoke", SEARCH_MODULES)


def profile_legacy_static() -> None:
    run_syntax_checks()
    run_unittest_group("Legacy static compatibility", LEGACY_STATIC_MODULES)


def profile_frontend_smoke() -> None:
    run_frontend_step("Next frontend typecheck", "typecheck")
    run_frontend_step("Next frontend model tests", "test:models")
    run_frontend_step("Next frontend build", "build")


def profile_s3_integration() -> None:
    run_step(
        "S3 storage integration",
        [sys.executable, "scripts/check_s3_storage.py"],
        storage_backend=None,
    )


def profile_storage_migration_plan() -> None:
    run_step(
        "Storage migration plan tests",
        [sys.executable, "-u", "-m", "unittest", "tests.test_plan_storage_migration", "-v"],
    )
    storage_root = ROOT / "data" / "magazyn"
    if storage_root.exists():
        run_step(
            "Storage migration dry-run",
            [
                sys.executable,
                "scripts/plan_storage_migration.py",
                "--storage-root",
                str(storage_root),
            ],
        )
    else:
        print("\n=== Storage migration dry-run skipped: data/magazyn does not exist ===", flush=True)


def profile_database_migration_audit() -> None:
    run_step(
        "Database migration audit tests",
        [
            sys.executable,
            "-u",
            "-m",
            "unittest",
            "tests.test_database_migration_audit",
            "tests.test_sqlite_to_configured_db_migrator",
            "-v",
        ],
    )
    run_step(
        "Database migration audit",
        [sys.executable, "scripts/audit_database_migration.py"],
    )


def profile_postgres_migration_check() -> None:
    run_step(
        "PostgreSQL migration check",
        [sys.executable, "scripts/check_postgres_migration.py"],
        storage_backend=None,
    )


def profile_predeploy() -> None:
    run_syntax_checks()
    run_unittest_group("Core", CORE_MODULES)
    run_unittest_group("HTTP", HTTP_MODULES)
    run_unittest_group("Invoices", INVOICE_MODULES)
    run_unittest_group("Tasks", TASK_MODULES)
    run_unittest_group("Calendars", CALENDAR_MODULES)
    run_unittest_group("Search", SEARCH_MODULES)
    run_unittest_group("Email", EMAIL_MODULES)
    run_unittest_group("Knowledge", KNOWLEDGE_MODULES)
    run_unittest_group("Billing", BILLING_MODULES)


def profile_full() -> None:
    run_syntax_checks()
    run_step("Full discover", [sys.executable, "-u", "-m", "unittest", "discover", "-s", "tests", "-v"])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Uruchamia uporzadkowane profile testow i kontroli jakosci."
    )
    parser.add_argument(
        "--profile",
        choices=[
            "smoke",
            "predeploy",
            "full",
            "legacy-static",
            "frontend-smoke",
            "s3-integration",
            "storage-migration-plan",
            "database-migration-audit",
            "postgres-migration-check",
        ],
        default="smoke",
        help="Wybierz profil uruchomienia.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.profile == "smoke":
        profile_smoke()
    elif args.profile == "legacy-static":
        profile_legacy_static()
    elif args.profile == "frontend-smoke":
        profile_frontend_smoke()
    elif args.profile == "s3-integration":
        profile_s3_integration()
    elif args.profile == "storage-migration-plan":
        profile_storage_migration_plan()
    elif args.profile == "database-migration-audit":
        profile_database_migration_audit()
    elif args.profile == "postgres-migration-check":
        profile_postgres_migration_check()
    elif args.profile == "predeploy":
        profile_predeploy()
    else:
        profile_full()


if __name__ == "__main__":
    main()
