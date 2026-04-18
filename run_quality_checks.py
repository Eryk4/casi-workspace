from __future__ import annotations

import argparse
import os
import subprocess
import sys
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
    "tests.test_auth_service",
    "tests.test_organizations",
    "tests.test_demo_seed",
]


def build_test_env(label: str) -> dict[str, str]:
    env = os.environ.copy()
    env["INVOICE_DATABASE_URL"] = ""
    env["DATABASE_URL"] = ""
    env["INVOICE_DB_ENGINE"] = "sqlite"
    safe_label = "".join(char.lower() if char.isalnum() else "_" for char in label).strip("_") or "tests"
    runtime_root = ROOT / "data" / "test_runtime" / "quality" / safe_label
    runtime_root.mkdir(parents=True, exist_ok=True)
    env["INVOICE_SQLITE_PATH"] = str((runtime_root / "invoice_ops.sqlite3").resolve())
    return env


def run_step(label: str, command: list[str]) -> None:
    print(f"\n=== {label} ===")
    print(" ".join(command))
    completed = subprocess.run(command, cwd=ROOT, env=build_test_env(label))
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def run_unittest_group(label: str, modules: list[str]) -> None:
    run_step(label, [sys.executable, "-u", "-m", "unittest", *modules, "-v"])


def run_syntax_checks() -> None:
    run_step("Python compile", [sys.executable, "-m", "compileall", "app", "tests", "run.py"])
    run_step("Frontend syntax", ["node", "--check", "static/app.js"])


def profile_smoke() -> None:
    run_syntax_checks()
    run_unittest_group("Core smoke", CORE_MODULES)
    run_unittest_group("Invoice smoke", INVOICE_MODULES)
    run_unittest_group(
        "HTTP smoke",
        [
            "tests.test_http_server_system",
            "tests.test_http_server_access",
            "tests.test_http_server_invoices",
        ],
    )
    run_unittest_group("Search smoke", SEARCH_MODULES)


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
        choices=["smoke", "predeploy", "full"],
        default="smoke",
        help="Wybierz profil uruchomienia.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.profile == "smoke":
        profile_smoke()
    elif args.profile == "predeploy":
        profile_predeploy()
    else:
        profile_full()


if __name__ == "__main__":
    main()
