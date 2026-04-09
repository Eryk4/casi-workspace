from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

from app.config import SQLITE_DB_PATH, STORAGE_ROOT, database_label, uses_postgresql
from app.db import get_connection, initialize_database, reset_database


TABLE_ORDER = (
    "organizations",
    "users",
    "contractors",
    "invoices",
    "invoice_relations",
    "event_logs",
    "user_sessions",
)

ORDER_COLUMNS = {
    "organizations": "organization_id",
    "users": "user_id",
    "contractors": "contractor_id",
    "invoices": "id",
    "invoice_relations": "id",
    "event_logs": "id",
    "user_sessions": "session_id",
}

POSTGRES_SEQUENCES = {
    "organizations": "organization_id",
    "users": "user_id",
    "contractors": "contractor_id",
    "invoices": "id",
    "invoice_relations": "id",
    "event_logs": "id",
    "user_sessions": "session_id",
}


def _sqlite_connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def _sqlite_table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _sqlite_table_columns(connection: sqlite3.Connection, table_name: str) -> list[str]:
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return [str(row["name"]) for row in rows]


def _target_has_data() -> bool:
    with get_connection() as connection:
        for table_name in ("organizations", "users", "contractors", "invoices", "event_logs"):
            row = connection.execute(f"SELECT COUNT(*) AS total FROM {table_name}").fetchone()
            if row and int(row["total"]) > 0:
                return True
    return False


def _copy_table(source: sqlite3.Connection, table_name: str) -> int:
    if not _sqlite_table_exists(source, table_name):
        return 0

    columns = _sqlite_table_columns(source, table_name)
    if not columns:
        return 0

    rows = source.execute(
        f"SELECT * FROM {table_name} ORDER BY {ORDER_COLUMNS[table_name]} ASC"
    ).fetchall()
    if not rows:
        return 0

    column_list = ", ".join(columns)
    placeholders = ", ".join("?" for _ in columns)

    with get_connection() as target:
        for row in rows:
            target.execute(
                f"INSERT INTO {table_name} ({column_list}) VALUES ({placeholders})",
                [row[column] for column in columns],
            )
    return len(rows)


def _reset_postgres_sequences() -> None:
    if not uses_postgresql():
        return

    with get_connection() as connection:
        for table_name, id_column in POSTGRES_SEQUENCES.items():
            connection.execute(
                f"""
                SELECT setval(
                    pg_get_serial_sequence('{table_name}', '{id_column}'),
                    COALESCE(MAX({id_column}), 1),
                    MAX({id_column}) IS NOT NULL
                )
                FROM {table_name}
                """
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Przenosi dane z pliku SQLite do obecnie skonfigurowanej bazy docelowej."
    )
    parser.add_argument(
        "--source-sqlite",
        default=str(SQLITE_DB_PATH),
        help="Ścieżka do źródłowej bazy SQLite.",
    )
    parser.add_argument(
        "--reset-target",
        action="store_true",
        help="Czyści docelową bazę przed migracją.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Pozwala uruchomić migrację także wtedy, gdy docelowa baza nie jest pusta.",
    )
    args = parser.parse_args()

    source_sqlite = Path(args.source_sqlite).resolve()
    if not source_sqlite.exists():
        raise SystemExit(f"Nie znaleziono źródłowej bazy SQLite: {source_sqlite}")

    if not uses_postgresql() and source_sqlite == SQLITE_DB_PATH.resolve():
        raise SystemExit(
            "Źródłowa SQLite i docelowa baza wskazują na ten sam plik. "
            "Skonfiguruj docelową bazę PostgreSQL albo podaj inną ścieżkę źródłową."
        )

    if args.reset_target:
        reset_database()
    else:
        initialize_database()

    if _target_has_data() and not args.force:
        raise SystemExit(
            "Docelowa baza nie jest pusta. Użyj --reset-target albo --force, jeśli chcesz kontynuować."
        )

    summary: dict[str, int] = {}
    with _sqlite_connect(source_sqlite) as source:
        for table_name in TABLE_ORDER:
            summary[table_name] = _copy_table(source, table_name)

    _reset_postgres_sequences()

    print(f"Migracja zakończona do bazy: {database_label()}")
    print(f"Źródłowa baza SQLite: {source_sqlite}")
    print("Przeniesione rekordy:")
    for table_name in TABLE_ORDER:
        print(f"- {table_name}: {summary.get(table_name, 0)}")
    print("")
    print("Pamiętaj też o skopiowaniu całego magazynu plików:")
    print(STORAGE_ROOT)


if __name__ == "__main__":
    main()
