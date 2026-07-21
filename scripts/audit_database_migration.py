from __future__ import annotations

import argparse
import ast
import json
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT / "app" / "db.py"
DEFAULT_MIGRATOR_PATH = ROOT / "migrate_sqlite_to_configured_db.py"
DEFAULT_JSON_REPORT = ROOT / "reports" / "database_migration_audit.json"
DEFAULT_MD_REPORT = ROOT / "reports" / "database_migration_audit.md"

TABLE_PATTERN = re.compile(r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+([A-Za-z_][A-Za-z0-9_]*)", re.IGNORECASE)
FOREIGN_KEY_PATTERN = re.compile(r"REFERENCES\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", re.IGNORECASE)

SEVERITY_ORDER = {"info": 0, "warning": 1, "error": 2, "blocker": 3}

# Tables whose data defines the operational product state. If these are omitted,
# a full SQLite -> PostgreSQL data migration is not complete.
CRITICAL_TABLES = {
    "organizations",
    "organization_memberships",
    "organization_modules",
    "users",
    "user_capabilities",
    "contractors",
    "contractor_notes",
    "invoices",
    "invoice_relations",
    "invoice_comments",
    "invoice_handoff_batches",
    "invoice_handoff_batch_items",
    "invoice_ksef_field_overrides",
    "tasks",
    "task_visibility_users",
    "task_links",
    "task_notes",
    "task_checklist_items",
    "task_templates",
    "task_attachments",
    "task_history",
    "approval_requests",
    "work_items",
    "work_item_history",
    "billing_schools",
    "billing_models",
    "billing_payers",
    "billing_students",
    "billing_charge_batches",
    "billing_charges",
    "billing_student_charge_state",
    "billing_payer_charge_state",
    "billing_bank_accounts",
    "billing_statement_imports",
    "billing_transactions",
    "billing_payment_review_events",
    "billing_work_queue_events",
    "billing_contact_events",
    "billing_next_step_events",
    "billing_payment_matches",
    "billing_payer_ledger_entries",
    "billing_notes",
    "knowledge_documents",
    "knowledge_document_versions",
    "knowledge_document_comments",
    "knowledge_folder_watchers",
    "organization_whiteboard_events",
    "intake_forms",
    "intake_items",
    "intake_item_comments",
    "intake_item_history",
    "entity_attachments",
    "automation_rules",
    "automation_executions",
    "saved_views",
    "system_settings",
    "user_calendars",
    "user_calendar_assignments",
    "user_google_calendar_connections",
    "system_email_google_connections",
    "event_logs",
}

# These tables can usually be rebuilt, expired, retried, or consciously skipped in a
# prototype, but the report still highlights them before a real migration.
REBUILDABLE_OR_OPERATIONAL_TABLES = {
    "user_sessions",
    "google_calendar_oauth_states",
    "system_email_oauth_states",
    "task_reminder_worker_heartbeats",
    "task_reminder_outbox",
    "task_reminder_outbox_attempts",
    "knowledge_processing_jobs",
    "email_import_runs",
    "email_import_items",
    "ksef_import_runs",
    "ksef_import_items",
    "user_module_inbox_state",
}

MIGRATION_DECISION_BY_TABLE = {
    "organization_whiteboard_events": {
        "classification": "must_migrate",
        "module": "whiteboard",
        "contains_customer_business_data": True,
        "contains_sensitive_data": False,
        "can_be_rebuilt": False,
        "prototype_blocker": False,
        "recommended_package": "whiteboard core",
        "note": "Chronologiczny dziennik zdarzen tablicy organizacji; utrata oznacza utrate historii pracy klienta.",
    },
    "saved_views": {
        "classification": "should_migrate",
        "module": "ui_state",
        "contains_customer_business_data": False,
        "contains_sensitive_data": False,
        "can_be_rebuilt": True,
        "prototype_blocker": False,
        "recommended_package": "ui/state core",
        "note": "Zapisane widoki i filtry uzytkownikow/organizacji; mozna odtworzyc recznie, ale warto zachowac dla UX.",
    },
    "email_import_runs": {
        "classification": "should_migrate",
        "module": "email_import",
        "contains_customer_business_data": True,
        "contains_sensitive_data": True,
        "can_be_rebuilt": False,
        "prototype_blocker": False,
        "recommended_package": "import audit history",
        "note": "Historia uruchomien importu e-mail; zawiera adresy skrzynek i szczegoly diagnostyczne.",
    },
    "email_import_items": {
        "classification": "should_migrate",
        "module": "email_import",
        "contains_customer_business_data": True,
        "contains_sensitive_data": True,
        "can_be_rebuilt": False,
        "prototype_blocker": False,
        "recommended_package": "import audit history",
        "note": "Pozycje importu e-mail; moga zawierac nadawcow, odbiorcow, tematy, identyfikatory wiadomosci i powiazanie z faktura.",
    },
    "ksef_import_runs": {
        "classification": "should_migrate",
        "module": "ksef_import",
        "contains_customer_business_data": True,
        "contains_sensitive_data": True,
        "can_be_rebuilt": False,
        "prototype_blocker": False,
        "recommended_package": "import audit history",
        "note": "Historia uruchomien importu KSeF; zawiera identyfikatory firmy/srodowiska i wynik importu.",
    },
    "ksef_import_items": {
        "classification": "should_migrate",
        "module": "ksef_import",
        "contains_customer_business_data": True,
        "contains_sensitive_data": True,
        "can_be_rebuilt": False,
        "prototype_blocker": False,
        "recommended_package": "import audit history",
        "note": "Pozycje importu KSeF; zawiera numery KSeF, numery faktur, NIP i powiazanie z faktura.",
    },
    "task_reminder_outbox": {
        "classification": "can_rebuild",
        "module": "task_reminders",
        "contains_customer_business_data": True,
        "contains_sensitive_data": True,
        "can_be_rebuilt": True,
        "prototype_blocker": False,
        "recommended_package": "task reminder operational state",
        "note": "Kolejka przypomnien z payloadem i Telegram ID; mozna odtworzyc z zadan albo pozwolic systemowi odbudowac kolejke.",
    },
    "task_reminder_outbox_attempts": {
        "classification": "can_skip_for_prototype",
        "module": "task_reminders",
        "contains_customer_business_data": False,
        "contains_sensitive_data": False,
        "can_be_rebuilt": False,
        "prototype_blocker": False,
        "recommended_package": "task reminder operational state",
        "note": "Historia prob wysylki przypomnien; przydatna diagnostycznie, ale nie blokuje pracy aplikacji.",
    },
    "task_reminder_worker_heartbeats": {
        "classification": "can_rebuild",
        "module": "task_reminders",
        "contains_customer_business_data": False,
        "contains_sensitive_data": False,
        "can_be_rebuilt": True,
        "prototype_blocker": False,
        "recommended_package": "none",
        "note": "Stan heartbeat workerow; naturalnie odtwarzany po starcie procesow.",
    },
    "google_calendar_oauth_states": {
        "classification": "can_rebuild",
        "module": "google_calendar_oauth",
        "contains_customer_business_data": False,
        "contains_sensitive_data": True,
        "can_be_rebuilt": True,
        "prototype_blocker": False,
        "recommended_package": "none",
        "note": "Krotkozyjace state tokens OAuth; powinny wygasnac i byc odtworzone przez nowy flow logowania.",
    },
    "system_email_oauth_states": {
        "classification": "can_rebuild",
        "module": "system_email_oauth",
        "contains_customer_business_data": False,
        "contains_sensitive_data": True,
        "can_be_rebuilt": True,
        "prototype_blocker": False,
        "recommended_package": "none",
        "note": "Krotkozyjace state tokens OAuth poczty systemowej; powinny wygasnac i byc odtworzone przez nowy flow.",
    },
    "user_module_inbox_state": {
        "classification": "can_rebuild",
        "module": "module_inbox",
        "contains_customer_business_data": False,
        "contains_sensitive_data": False,
        "can_be_rebuilt": True,
        "prototype_blocker": False,
        "recommended_package": "user state cleanup",
        "note": "Stan 'last seen' dla skrzynki modulow; po migracji moze zostac zresetowany kosztem ponownego pokazania powiadomien.",
    },
}


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _literal_assignment(module_text: str, name: str) -> Any:
    tree = ast.parse(module_text)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return ast.literal_eval(node.value)
    raise ValueError(f"Nie znaleziono stalej {name}")


def _table_names_from_sql(sql: str) -> set[str]:
    return {name for name in TABLE_PATTERN.findall(sql) if not name.endswith("__migracja")}


def _foreign_key_dependencies(sql: str) -> dict[str, set[str]]:
    dependencies: dict[str, set[str]] = {}
    matches = list(TABLE_PATTERN.finditer(sql))
    for index, match in enumerate(matches):
        table_name = match.group(1)
        if table_name.endswith("__migracja"):
            continue
        end = matches[index + 1].start() if index + 1 < len(matches) else len(sql)
        statement = sql[match.start() : end]
        references = {
            reference
            for reference in FOREIGN_KEY_PATTERN.findall(statement)
            if reference != table_name and not reference.endswith("__migracja")
        }
        dependencies.setdefault(table_name, set()).update(references)
    return dependencies


def _collect_declared_schema(db_path: Path) -> tuple[set[str], set[str], dict[str, set[str]], dict[str, set[str]]]:
    db_text = _read_text(db_path)
    sqlite_schema = str(_literal_assignment(db_text, "SQLITE_SCHEMA"))
    postgres_schema = str(_literal_assignment(db_text, "POSTGRES_SCHEMA"))

    # Helper schema functions in app/db.py define additional tables for both backends.
    # Tables created outside the base constants appear at least twice in this file
    # (SQLite branch and PostgreSQL branch), so they can be treated as common
    # initialized schema without erasing true SQLite/PostgreSQL-only differences.
    table_occurrences = Counter(TABLE_PATTERN.findall(db_text))
    supplemental_tables = {
        name
        for name, count in table_occurrences.items()
        if count >= 2 and not name.endswith("__migracja")
    }
    sqlite_tables = _table_names_from_sql(sqlite_schema) | supplemental_tables
    postgres_tables = _table_names_from_sql(postgres_schema) | supplemental_tables

    sqlite_dependencies = _foreign_key_dependencies(sqlite_schema + "\n" + db_text)
    postgres_dependencies = _foreign_key_dependencies(postgres_schema + "\n" + db_text)
    return sqlite_tables, postgres_tables, sqlite_dependencies, postgres_dependencies


def _collect_migrator_tables(migrator_path: Path) -> list[str]:
    migrator_text = _read_text(migrator_path)
    table_order = _literal_assignment(migrator_text, "TABLE_ORDER")
    if not isinstance(table_order, tuple):
        raise ValueError("TABLE_ORDER w migratorze nie jest krotka")
    return [str(item) for item in table_order]


def classify_missing_table(table_name: str) -> tuple[str, str]:
    if table_name in CRITICAL_TABLES:
        return "blocker", "critical_table_not_migrated"
    if table_name in REBUILDABLE_OR_OPERATIONAL_TABLES:
        return "warning", "operational_table_not_migrated"
    return "warning", "unclassified_table_not_migrated"


def _remaining_table_decisions(tables_missing_from_migrator: list[str], issues: list[Issue]) -> list[dict[str, Any]]:
    issue_by_table = {issue.table: issue for issue in issues if issue.table}
    decisions: list[dict[str, Any]] = []
    for table_name in tables_missing_from_migrator:
        issue = issue_by_table.get(table_name)
        decision = MIGRATION_DECISION_BY_TABLE.get(
            table_name,
            {
                "classification": "unknown_requires_review",
                "module": "unknown",
                "contains_customer_business_data": False,
                "contains_sensitive_data": False,
                "can_be_rebuilt": False,
                "prototype_blocker": True,
                "recommended_package": "manual review",
                "note": "Tabela wymaga recznej klasyfikacji przed prawdziwa migracja.",
            },
        )
        decisions.append(
            {
                "table": table_name,
                "audit_severity": issue.severity if issue else "info",
                "audit_code": issue.code if issue else "none",
                **decision,
            }
        )
    return decisions


@dataclass(frozen=True)
class Issue:
    code: str
    severity: str
    table: str | None
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity,
            "table": self.table,
            "message": self.message,
        }


def _migration_order_issues(migrator_tables: list[str], dependencies: dict[str, set[str]]) -> list[Issue]:
    positions = {table_name: index for index, table_name in enumerate(migrator_tables)}
    issues: list[Issue] = []
    for table_name in migrator_tables:
        table_position = positions[table_name]
        for dependency in sorted(dependencies.get(table_name, set())):
            dependency_position = positions.get(dependency)
            if dependency_position is None:
                continue
            if dependency_position > table_position:
                issues.append(
                    Issue(
                        code="unsafe_migration_order",
                        severity="blocker",
                        table=table_name,
                        message=(
                            f"Tabela {table_name} jest migrowana przed zaleznoscia {dependency}."
                        ),
                    )
                )
    return issues


def build_audit(
    *,
    db_path: Path = DEFAULT_DB_PATH,
    migrator_path: Path = DEFAULT_MIGRATOR_PATH,
) -> dict[str, Any]:
    issues: list[Issue] = []
    sqlite_tables: set[str] = set()
    postgres_tables: set[str] = set()
    sqlite_dependencies: dict[str, set[str]] = {}
    postgres_dependencies: dict[str, set[str]] = {}
    migrator_tables: list[str] = []

    if not db_path.exists():
        issues.append(
            Issue(
                code="db_schema_file_missing",
                severity="error",
                table=None,
                message=f"Nie znaleziono pliku schematu: {db_path.name}",
            )
        )
    else:
        sqlite_tables, postgres_tables, sqlite_dependencies, postgres_dependencies = _collect_declared_schema(db_path)

    if not migrator_path.exists():
        issues.append(
            Issue(
                code="migrator_file_missing",
                severity="error",
                table=None,
                message=f"Nie znaleziono migratora: {migrator_path.name}",
            )
        )
    else:
        migrator_tables = _collect_migrator_tables(migrator_path)

    sqlite_only_tables = sorted(sqlite_tables - postgres_tables)
    postgres_only_tables = sorted(postgres_tables - sqlite_tables)
    schema_tables = sqlite_tables | postgres_tables
    migrated_set = set(migrator_tables)
    tables_missing_from_migrator = sorted(schema_tables - migrated_set)
    migrator_tables_missing_from_schema = sorted(migrated_set - schema_tables)

    for table_name in tables_missing_from_migrator:
        severity, code = classify_missing_table(table_name)
        issues.append(
            Issue(
                code=code,
                severity=severity,
                table=table_name,
                message=f"Tabela {table_name} istnieje w schemacie aplikacji, ale nie ma jej w TABLE_ORDER migratora.",
            )
        )

    for table_name in migrator_tables_missing_from_schema:
        issues.append(
            Issue(
                code="migrator_table_missing_from_schema",
                severity="error",
                table=table_name,
                message=f"Migrator probuje przeniesc tabele {table_name}, ktorej nie znaleziono w schemacie.",
            )
        )

    if sqlite_only_tables:
        for table_name in sqlite_only_tables:
            issues.append(
                Issue(
                    code="sqlite_only_table",
                    severity="warning",
                    table=table_name,
                    message=f"Tabela {table_name} wystepuje tylko w deklaracjach SQLite.",
                )
            )
    if postgres_only_tables:
        for table_name in postgres_only_tables:
            issues.append(
                Issue(
                    code="postgres_only_table",
                    severity="warning",
                    table=table_name,
                    message=f"Tabela {table_name} wystepuje tylko w deklaracjach PostgreSQL.",
                )
            )

    order_issues = _migration_order_issues(migrator_tables, sqlite_dependencies | postgres_dependencies)
    issues.extend(order_issues)

    severity_counts = Counter(issue.severity for issue in issues)
    code_counts = Counter(issue.code for issue in issues)
    blocker_count = severity_counts.get("blocker", 0)

    recommended_next_actions = _recommended_next_actions(
        blocker_count=blocker_count,
        tables_missing_from_migrator=tables_missing_from_migrator,
        sqlite_only_tables=sqlite_only_tables,
        postgres_only_tables=postgres_only_tables,
    )
    remaining_table_decisions = _remaining_table_decisions(tables_missing_from_migrator, issues)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "audit_type": "sqlite_to_postgresql_migration_readiness",
        "schema_sources": {
            "db_schema_file": str(db_path.relative_to(ROOT)) if db_path.is_relative_to(ROOT) else db_path.name,
            "migrator_file": str(migrator_path.relative_to(ROOT)) if migrator_path.is_relative_to(ROOT) else migrator_path.name,
        },
        "sqlite_tables": sorted(sqlite_tables),
        "postgresql_tables": sorted(postgres_tables),
        "migrator_tables": migrator_tables,
        "tables_missing_from_migrator": tables_missing_from_migrator,
        "migrator_tables_missing_from_schema": migrator_tables_missing_from_schema,
        "sqlite_only_tables": sqlite_only_tables,
        "postgresql_only_tables": postgres_only_tables,
        "migration_order_issues": [issue.to_dict() for issue in order_issues],
        "issue_count_by_severity": {severity: severity_counts.get(severity, 0) for severity in SEVERITY_ORDER},
        "issue_count_by_category": dict(sorted(code_counts.items())),
        "blocker_count": blocker_count,
        "database_migration_blocked": blocker_count > 0,
        "remaining_table_decisions": remaining_table_decisions,
        "issues": [issue.to_dict() for issue in sorted(issues, key=lambda issue: (-SEVERITY_ORDER[issue.severity], issue.code, issue.table or ""))],
        "recommended_next_actions": recommended_next_actions,
    }


def _recommended_next_actions(
    *,
    blocker_count: int,
    tables_missing_from_migrator: list[str],
    sqlite_only_tables: list[str],
    postgres_only_tables: list[str],
) -> list[str]:
    actions: list[str] = []
    if blocker_count:
        actions.append(
            "Przed prawdziwa migracja danych rozszerzyc TABLE_ORDER migratora o krytyczne tabele albo swiadomie oznaczyc je jako pomijalne."
        )
    if tables_missing_from_migrator:
        if blocker_count:
            actions.append(
                "Podzielic pomijane tabele na: dane biznesowe do migracji, dane operacyjne do odtworzenia oraz stany tymczasowe do pominiecia."
            )
        else:
            actions.append(
                "Pozostale tabele nie blokuja pierwszego kontrolowanego testu PostgreSQL; przed produkcyjna migracja podjac decyzje, czy przenosic historie importow i odtwarzalne stany operacyjne."
            )
    if sqlite_only_tables or postgres_only_tables:
        actions.append(
            "Wyrownac deklaracje schematu SQLite i PostgreSQL przed testem z prawdziwym PostgreSQL."
        )
    if blocker_count:
        actions.append(
            "Nastepny bezpieczny krok: przygotowac rozszerzenie migratora w malych partiach tabel i dopiero potem uruchomic osobny test na tymczasowym PostgreSQL."
        )
    else:
        actions.append(
            "Nastepny bezpieczny krok: uruchomic pierwszy kontrolowany test migracji na tymczasowym PostgreSQL, bez produkcyjnego deploya i bez migracji plikow."
        )
    return actions


def write_json_report(report: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _format_issue_list(issues: list[dict[str, Any]], *, limit: int = 30) -> str:
    if not issues:
        return "Brak.\n"
    lines = []
    for issue in issues[:limit]:
        table = issue.get("table") or "global"
        lines.append(f"- `{issue['severity']}` `{issue['code']}` `{table}` - {issue['message']}")
    if len(issues) > limit:
        lines.append(f"- ... oraz {len(issues) - limit} kolejnych pozycji w raporcie JSON.")
    return "\n".join(lines) + "\n"


def render_markdown(report: dict[str, Any]) -> str:
    issues = list(report["issues"])
    blockers = [issue for issue in issues if issue["severity"] == "blocker"]
    warnings = [issue for issue in issues if issue["severity"] == "warning"]
    errors = [issue for issue in issues if issue["severity"] == "error"]
    info = [issue for issue in issues if issue["severity"] == "info"]
    blocked_text = "TAK" if report["database_migration_blocked"] else "NIE"
    lines = [
        "# Database Migration Audit",
        "",
        "Ten raport jest lokalnym audytem gotowosci migracji SQLite -> PostgreSQL. To nie jest migracja i nie laczy sie z PostgreSQL.",
        "",
        "## Podsumowanie",
        "",
        f"- Tabele SQLite: {len(report['sqlite_tables'])}",
        f"- Tabele PostgreSQL: {len(report['postgresql_tables'])}",
        f"- Tabele w migratorze: {len(report['migrator_tables'])}",
        f"- Tabele nieobjete migratorem: {len(report['tables_missing_from_migrator'])}",
        f"- Blockery: {report['blocker_count']}",
        "",
        "## Czy migracja bazy jest zablokowana?",
        "",
        f"**{blocked_text}.**",
        "",
    ]
    if report["database_migration_blocked"]:
        lines.append("Pelna migracja danych SQLite -> PostgreSQL jest zablokowana, bo migrator nie obejmuje krytycznych tabel aplikacji.")
    else:
        lines.append("Audyt nie wykryl blockerow dla migratora, ale nadal wymagany jest osobny test na prawdziwym PostgreSQL przed produkcja.")
    lines.extend([
        "",
        "## Tabele objete migratorem",
        "",
        ", ".join(f"`{table}`" for table in report["migrator_tables"]) or "Brak.",
        "",
        "## Tabele nieobjete migratorem",
        "",
        ", ".join(f"`{table}`" for table in report["tables_missing_from_migrator"]) or "Brak.",
        "",
        "## Decyzje dla pozostalych tabel",
        "",
    ])
    for decision in report.get("remaining_table_decisions", []):
        flags = []
        if decision.get("contains_customer_business_data"):
            flags.append("dane klienta")
        if decision.get("contains_sensitive_data"):
            flags.append("dane wrazliwe")
        if decision.get("can_be_rebuilt"):
            flags.append("mozna odtworzyc")
        flag_text = f" ({', '.join(flags)})" if flags else ""
        lines.append(
            f"- `{decision['table']}` - `{decision['classification']}` / `{decision['audit_severity']}`; "
            f"pakiet: `{decision['recommended_package']}`{flag_text}. {decision['note']}"
        )
    if not report.get("remaining_table_decisions"):
        lines.append("Brak.")
    lines.extend([
        "",
        "## Ocena ryzyka",
        "",
        f"- `blocker`: {report['issue_count_by_severity'].get('blocker', 0)}",
        f"- `error`: {report['issue_count_by_severity'].get('error', 0)}",
        f"- `warning`: {report['issue_count_by_severity'].get('warning', 0)}",
        f"- `info`: {report['issue_count_by_severity'].get('info', 0)}",
        "",
        "## Najwazniejsze problemy",
        "",
        _format_issue_list(blockers + errors + warnings, limit=40),
        "## Informacje",
        "",
        _format_issue_list(info, limit=20),
        "## Rekomendowany nastepny krok",
        "",
    ])
    lines.extend(f"- {action}" for action in report["recommended_next_actions"])
    lines.extend([
        "",
        "## Uwagi prywatnosci",
        "",
        "Raport nie wymaga sekretow, nie pokazuje zmiennych srodowiskowych i nie zapisuje prywatnych pelnych sciezek uzytkownika. Zrodla sa raportowane wzgledem repozytorium.",
        "",
    ])
    return "\n".join(lines)


def write_markdown_report(report: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_markdown(report), encoding="utf-8")


def print_console_summary(report: dict[str, Any]) -> None:
    print("Database migration audit")
    print(f"SQLite tables: {len(report['sqlite_tables'])}")
    print(f"PostgreSQL tables: {len(report['postgresql_tables'])}")
    print(f"Migrator tables: {len(report['migrator_tables'])}")
    print(f"Tables missing from migrator: {len(report['tables_missing_from_migrator'])}")
    print(f"Blockers: {report['blocker_count']}")
    print("Issue severity:")
    for severity in SEVERITY_ORDER:
        print(f"- {severity}: {report['issue_count_by_severity'].get(severity, 0)}")
    print("Recommended next actions:")
    for action in report["recommended_next_actions"]:
        print(f"- {action}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Lokalny audyt gotowosci migracji SQLite -> PostgreSQL.")
    parser.add_argument("--db-file", default=str(DEFAULT_DB_PATH), help="Sciezka do app/db.py.")
    parser.add_argument("--migrator", default=str(DEFAULT_MIGRATOR_PATH), help="Sciezka do migratora SQLite -> DB.")
    parser.add_argument("--output-json", default=str(DEFAULT_JSON_REPORT), help="Sciezka raportu JSON.")
    parser.add_argument("--output-md", default=str(DEFAULT_MD_REPORT), help="Sciezka raportu Markdown.")
    parser.add_argument("--fail-on-blockers", action="store_true", help="Zakoncz kodem 1, jesli wykryto blockery.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    report = build_audit(db_path=Path(args.db_file).resolve(), migrator_path=Path(args.migrator).resolve())
    write_json_report(report, Path(args.output_json).resolve())
    write_markdown_report(report, Path(args.output_md).resolve())
    print_console_summary(report)
    if args.fail_on_blockers and report["blocker_count"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

