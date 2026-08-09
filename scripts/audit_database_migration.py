from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.data_migration_manifest import MANIFEST_BY_TABLE, MIGRATION_MANIFEST, TABLE_ORDER


DEFAULT_DB_PATH = ROOT / "app" / "db.py"
DEFAULT_MIGRATOR_PATH = ROOT / "migrate_sqlite_to_configured_db.py"
DEFAULT_JSON_REPORT = ROOT / "reports" / "database_migration_audit.json"
DEFAULT_MD_REPORT = ROOT / "reports" / "database_migration_audit.md"

TABLE_PATTERN = re.compile(
    r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+([A-Za-z_][A-Za-z0-9_]*)",
    re.IGNORECASE,
)
FOREIGN_KEY_PATTERN = re.compile(
    r"REFERENCES\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(",
    re.IGNORECASE,
)
SEVERITY_ORDER = {"info": 0, "warning": 1, "error": 2, "blocker": 3}


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
    return {
        name
        for name in TABLE_PATTERN.findall(sql)
        if not name.endswith("__migracja")
    }


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


def _source_without_schema_assignments(module_text: str) -> str:
    """Return module source with the two backend schema literals masked out."""
    tree = ast.parse(module_text)
    lines = module_text.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    masked = list(module_text)
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        names = {
            target.id
            for target in node.targets
            if isinstance(target, ast.Name)
        }
        if not names.intersection({"SQLITE_SCHEMA", "POSTGRES_SCHEMA"}):
            continue
        start = offsets[node.value.lineno - 1] + node.value.col_offset
        end = offsets[node.value.end_lineno - 1] + node.value.end_col_offset
        masked[start:end] = [" " if char not in "\r\n" else char for char in masked[start:end]]
    return "".join(masked)


def _collect_declared_schema(
    db_path: Path,
) -> tuple[set[str], set[str], dict[str, set[str]], dict[str, set[str]]]:
    db_text = _read_text(db_path)
    sqlite_schema = str(_literal_assignment(db_text, "SQLITE_SCHEMA"))
    postgres_schema = str(_literal_assignment(db_text, "POSTGRES_SCHEMA"))

    # CREATE TABLE statements in shared additive helpers apply to both engines.
    # Backend-specific helpers already contain two declarations, while a shared
    # helper such as casi_schema_metadata legitimately occurs once.
    supplemental_sql = _source_without_schema_assignments(db_text)
    supplemental_tables = _table_names_from_sql(supplemental_sql)
    sqlite_tables = _table_names_from_sql(sqlite_schema) | supplemental_tables
    postgres_tables = _table_names_from_sql(postgres_schema) | supplemental_tables
    sqlite_dependencies = _foreign_key_dependencies(sqlite_schema + "\n" + supplemental_sql)
    postgres_dependencies = _foreign_key_dependencies(postgres_schema + "\n" + supplemental_sql)
    return sqlite_tables, postgres_tables, sqlite_dependencies, postgres_dependencies


def _collect_migrator_tables(migrator_path: Path) -> list[str]:
    if migrator_path.resolve() == DEFAULT_MIGRATOR_PATH.resolve():
        return list(TABLE_ORDER)
    migrator_text = _read_text(migrator_path)
    table_order = _literal_assignment(migrator_text, "TABLE_ORDER")
    if not isinstance(table_order, tuple):
        raise ValueError("TABLE_ORDER w migratorze nie jest krotka")
    return [str(item) for item in table_order]


def _manifest_decision(table_name: str) -> dict[str, Any] | None:
    spec = MANIFEST_BY_TABLE.get(table_name)
    if spec is None:
        return None
    return {
        "table": table_name,
        "category": spec.category,
        "migrate": spec.migrate,
        "order": spec.order,
        "primary_key": list(spec.primary_key),
        "dependencies": list(spec.dependencies),
        "verification": spec.verification,
        "sequence_column": spec.sequence_column,
        "exclusion_reason": spec.exclusion_reason,
        "rebuild_procedure": spec.rebuild_procedure,
    }


def classify_missing_table(table_name: str) -> tuple[str, str]:
    decision = _manifest_decision(table_name)
    if decision and not decision["migrate"]:
        return "info", "classified_non_migrated_table"
    return "blocker", "persistent_or_unclassified_table_not_migrated"


def _migration_order_issues(
    migrator_tables: list[str],
    dependencies: dict[str, set[str]],
) -> list[Issue]:
    positions = {table_name: index for index, table_name in enumerate(migrator_tables)}
    issues: list[Issue] = []
    for table_name in migrator_tables:
        for dependency in sorted(dependencies.get(table_name, set())):
            dependency_position = positions.get(dependency)
            if dependency_position is None:
                continue
            if dependency_position > positions[table_name]:
                issues.append(
                    Issue(
                        code="unsafe_migration_order",
                        severity="blocker",
                        table=table_name,
                        message=f"Tabela {table_name} jest migrowana przed zaleznoscia {dependency}.",
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

    if db_path.exists():
        sqlite_tables, postgres_tables, sqlite_dependencies, postgres_dependencies = (
            _collect_declared_schema(db_path)
        )
    else:
        issues.append(Issue("db_schema_file_missing", "error", None, "Brak pliku schematu."))

    if migrator_path.exists():
        migrator_tables = _collect_migrator_tables(migrator_path)
    else:
        issues.append(Issue("migrator_file_missing", "error", None, "Brak pliku migratora."))

    schema_tables = sqlite_tables | postgres_tables
    manifest_tables = set(MANIFEST_BY_TABLE) if db_path.resolve() == DEFAULT_DB_PATH.resolve() else set()
    excluded_tables = {
        table for table, spec in MANIFEST_BY_TABLE.items() if not spec.migrate
    } if manifest_tables else set()
    migrated_set = set(migrator_tables)
    unclassified_tables = sorted(schema_tables - manifest_tables) if manifest_tables else []
    manifest_tables_missing_from_schema = sorted(manifest_tables - schema_tables)
    tables_missing_from_migrator = sorted(schema_tables - migrated_set - excluded_tables)
    classified_excluded_tables = sorted(schema_tables & excluded_tables)
    migrator_tables_missing_from_schema = sorted(migrated_set - schema_tables)

    for table_name in unclassified_tables:
        issues.append(
            Issue(
                "schema_table_missing_manifest_classification",
                "blocker",
                table_name,
                "Tabela schematu nie ma jawnej klasyfikacji w kanonicznym manifeście.",
            )
        )
    for table_name in manifest_tables_missing_from_schema:
        issues.append(
            Issue(
                "manifest_table_missing_from_schema",
                "blocker",
                table_name,
                "Tabela manifestu nie wystepuje w aktualnym schemacie.",
            )
        )
    for table_name in tables_missing_from_migrator:
        severity, code = classify_missing_table(table_name)
        issues.append(Issue(code, severity, table_name, "Tabela nie jest objeta migracja danych."))
    for table_name in migrator_tables_missing_from_schema:
        issues.append(
            Issue(
                "migrator_table_missing_from_schema",
                "error",
                table_name,
                "Migrator wskazuje tabele nieobecna w schemacie.",
            )
        )

    sqlite_only_tables = sorted(sqlite_tables - postgres_tables)
    postgres_only_tables = sorted(postgres_tables - sqlite_tables)
    for table_name in sqlite_only_tables:
        issues.append(Issue("sqlite_only_table", "blocker", table_name, "Tabela tylko SQLite."))
    for table_name in postgres_only_tables:
        issues.append(Issue("postgres_only_table", "blocker", table_name, "Tabela tylko PostgreSQL."))

    order_issues = _migration_order_issues(
        migrator_tables,
        sqlite_dependencies | postgres_dependencies,
    )
    issues.extend(order_issues)
    severity_counts = Counter(issue.severity for issue in issues)
    code_counts = Counter(issue.code for issue in issues)
    blocker_count = severity_counts.get("blocker", 0)
    decisions = [
        decision
        for table in sorted(manifest_tables)
        if (decision := _manifest_decision(table)) is not None
    ]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "audit_type": "sqlite_to_postgresql_manifest_coverage",
        "schema_sources": {
            "db_schema_file": str(db_path.relative_to(ROOT)) if db_path.is_relative_to(ROOT) else db_path.name,
            "migrator_file": str(migrator_path.relative_to(ROOT)) if migrator_path.is_relative_to(ROOT) else migrator_path.name,
        },
        "sqlite_tables": sorted(sqlite_tables),
        "postgresql_tables": sorted(postgres_tables),
        "manifest_tables": sorted(manifest_tables),
        "migrator_tables": migrator_tables,
        "classified_excluded_tables": classified_excluded_tables,
        "unclassified_tables": unclassified_tables,
        "manifest_tables_missing_from_schema": manifest_tables_missing_from_schema,
        "tables_missing_from_migrator": tables_missing_from_migrator,
        "migrator_tables_missing_from_schema": migrator_tables_missing_from_schema,
        "sqlite_only_tables": sqlite_only_tables,
        "postgresql_only_tables": postgres_only_tables,
        "migration_order_issues": [issue.to_dict() for issue in order_issues],
        "table_decisions": decisions,
        "remaining_table_decisions": [
            decision for decision in decisions if not decision["migrate"]
        ],
        "issue_count_by_severity": {
            severity: severity_counts.get(severity, 0) for severity in SEVERITY_ORDER
        },
        "issue_count_by_category": dict(sorted(code_counts.items())),
        "blocker_count": blocker_count,
        "database_migration_blocked": blocker_count > 0,
        "issues": [
            issue.to_dict()
            for issue in sorted(
                issues,
                key=lambda item: (-SEVERITY_ORDER[item.severity], item.code, item.table or ""),
            )
        ],
        "recommended_next_actions": (
            ["Usunac blockery manifestu przed testem PostgreSQL."]
            if blocker_count
            else ["Uruchomic kontrolowany test na pustym, jednorazowym PostgreSQL."]
        ),
    }


def write_json_report(report: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Database Migration Audit",
        "",
        "Read-only audit of canonical SQLite -> PostgreSQL migration coverage.",
        "",
        "## Podsumowanie",
        "",
        f"- Tabele SQLite: {len(report['sqlite_tables'])}",
        f"- Tabele PostgreSQL: {len(report['postgresql_tables'])}",
        f"- Tabele sklasyfikowane: {len(report['manifest_tables'])}",
        f"- Tabele migrowane: {len(report['migrator_tables'])}",
        f"- Tabele jawnie wykluczone: {len(report['classified_excluded_tables'])}",
        f"- Tabele niesklasyfikowane: {len(report['unclassified_tables'])}",
        f"- Blockery: {report['blocker_count']}",
        "",
        "## Czy migracja bazy jest zablokowana?",
        "",
        "**TAK.**" if report["database_migration_blocked"] else "**NIE.**",
        "",
        "## Tabele objete migracja",
        "",
        ", ".join(f"`{table}`" for table in report["migrator_tables"]) or "Brak.",
        "",
        "## Jawnie wykluczone",
        "",
    ]
    for decision in report["remaining_table_decisions"]:
        lines.append(
            f"- `{decision['table']}` — `{decision['category']}`. "
            f"{decision['exclusion_reason']} Odtworzenie: {decision['rebuild_procedure']}"
        )
    if not report["remaining_table_decisions"]:
        lines.append("Brak.")
    lines.extend(["", "## Problemy", ""])
    for issue in report["issues"]:
        lines.append(
            f"- `{issue['severity']}` `{issue['code']}` `{issue.get('table') or 'global'}` — {issue['message']}"
        )
    if not report["issues"]:
        lines.append("Brak.")
    lines.extend(
        [
            "",
            "## Prywatnosc",
            "",
            "Raport nie zawiera DSN, sekretow ani danych rekordow.",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown_report(report: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_markdown(report), encoding="utf-8")


def print_console_summary(report: dict[str, Any]) -> None:
    print("Database migration manifest audit")
    print(f"SQLite tables: {len(report['sqlite_tables'])}")
    print(f"PostgreSQL tables: {len(report['postgresql_tables'])}")
    print(f"Manifest tables: {len(report['manifest_tables'])}")
    print(f"Migrated tables: {len(report['migrator_tables'])}")
    print(f"Excluded tables: {len(report['classified_excluded_tables'])}")
    print(f"Unclassified tables: {len(report['unclassified_tables'])}")
    print(f"Blockers: {report['blocker_count']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only migration manifest audit.")
    parser.add_argument("--db-file", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--migrator", default=str(DEFAULT_MIGRATOR_PATH))
    parser.add_argument("--output-json", default=str(DEFAULT_JSON_REPORT))
    parser.add_argument("--output-md", default=str(DEFAULT_MD_REPORT))
    parser.add_argument("--fail-on-blockers", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    report = build_audit(
        db_path=Path(args.db_file).resolve(),
        migrator_path=Path(args.migrator).resolve(),
    )
    write_json_report(report, Path(args.output_json).resolve())
    write_markdown_report(report, Path(args.output_md).resolve())
    print_console_summary(report)
    if args.fail_on_blockers and report["blocker_count"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
