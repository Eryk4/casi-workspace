from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Any, Iterable

from app.config import DATABASE_URL, SQLITE_DB_PATH, ensure_directories, uses_postgresql

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:  # pragma: no cover - zależne od środowiska uruchomieniowego
    psycopg = None
    dict_row = None

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:  # pragma: no cover - zależne od środowiska uruchomieniowego
    psycopg2 = None
    RealDictCursor = None


SQLITE_SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS organizations (
    organization_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    slug TEXT NOT NULL UNIQUE,
    telegram_chat_id TEXT,
    telegram_chat_name TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS contractors (
    contractor_id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER,
    name TEXT NOT NULL,
    nip TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    is_new INTEGER NOT NULL DEFAULT 1,
    last_invoice_date TEXT,
    last_invoice_number TEXT,
    invoice_count INTEGER NOT NULL DEFAULT 0,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_contractors_org_nip ON contractors(organization_id, nip);

CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    login TEXT NOT NULL UNIQUE,
    display_name TEXT,
    telegram_user_id TEXT UNIQUE,
    organization_id INTEGER,
    password_hash TEXT NOT NULL,
    password_salt TEXT NOT NULL,
    role TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    last_login_at TEXT,
    created_by_user_id INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (created_by_user_id) REFERENCES users(user_id),
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
);

CREATE INDEX IF NOT EXISTS idx_users_login ON users(login);
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_telegram_user_id ON users(telegram_user_id);
CREATE INDEX IF NOT EXISTS idx_users_organization_id ON users(organization_id);

CREATE TABLE IF NOT EXISTS user_sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    ip_address TEXT,
    user_agent TEXT,
    created_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);

CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER,
    incoming_date TEXT NOT NULL,
    source TEXT NOT NULL,
    file_name TEXT NOT NULL,
    document_type TEXT,
    invoice_number TEXT,
    ksef_number TEXT,
    issuer_nip TEXT,
    issuer_name TEXT,
    issue_date TEXT,
    sale_date TEXT,
    gross_amount REAL,
    currency TEXT NOT NULL DEFAULT 'PLN',
    status TEXT NOT NULL,
    duplicate_type TEXT NOT NULL DEFAULT 'brak',
    flag_reason TEXT,
    contractor_id INTEGER,
    file_link TEXT,
    file_storage_key TEXT,
    ocr_link TEXT,
    ocr_storage_key TEXT,
    storage_backend TEXT,
    source_external_id TEXT,
    source_sender_name TEXT,
    source_sender_id TEXT,
    source_metadata TEXT,
    invoice_hash TEXT NOT NULL UNIQUE,
    ocr_raw_text TEXT,
    ocr_confidence REAL,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (contractor_id) REFERENCES contractors(contractor_id),
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
);

CREATE INDEX IF NOT EXISTS idx_invoices_ksef_number ON invoices(ksef_number);
CREATE INDEX IF NOT EXISTS idx_invoices_number_nip ON invoices(invoice_number, issuer_nip);
CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status);
CREATE INDEX IF NOT EXISTS idx_invoices_source ON invoices(source);
CREATE INDEX IF NOT EXISTS idx_invoices_organization_id ON invoices(organization_id);

CREATE TABLE IF NOT EXISTS tasks (
    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL,
    task_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL,
    priority TEXT NOT NULL,
    due_at TEXT,
    remind_at TEXT,
    assigned_user_id INTEGER,
    created_by_user_id INTEGER NOT NULL,
    completed_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    FOREIGN KEY (assigned_user_id) REFERENCES users(user_id),
    FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_tasks_organization_id ON tasks(organization_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_due_at ON tasks(due_at);
CREATE INDEX IF NOT EXISTS idx_tasks_remind_at ON tasks(remind_at);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_user_id ON tasks(assigned_user_id);

CREATE TABLE IF NOT EXISTS task_notes (
    task_note_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    organization_id INTEGER NOT NULL,
    note_text TEXT NOT NULL,
    created_by_user_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_task_notes_task_id ON task_notes(task_id);

CREATE TABLE IF NOT EXISTS task_history (
    task_history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    organization_id INTEGER NOT NULL,
    action_type TEXT NOT NULL,
    actor TEXT NOT NULL,
    message TEXT NOT NULL,
    details TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
);

CREATE INDEX IF NOT EXISTS idx_task_history_task_id ON task_history(task_id);

CREATE TABLE IF NOT EXISTS invoice_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER NOT NULL,
    related_invoice_id INTEGER NOT NULL,
    relation_type TEXT NOT NULL,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
    FOREIGN KEY (related_invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_invoice_relations_invoice_id ON invoice_relations(invoice_id);

CREATE TABLE IF NOT EXISTS event_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER,
    event_time TEXT NOT NULL,
    event_type TEXT NOT NULL,
    invoice_id INTEGER,
    source TEXT,
    status_before TEXT,
    status_after TEXT,
    decision_reason TEXT,
    actor TEXT NOT NULL,
    details TEXT,
    FOREIGN KEY (invoice_id) REFERENCES invoices(id),
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
);

CREATE INDEX IF NOT EXISTS idx_event_logs_invoice_id ON event_logs(invoice_id);
CREATE INDEX IF NOT EXISTS idx_event_logs_event_time ON event_logs(event_time DESC);
CREATE INDEX IF NOT EXISTS idx_event_logs_organization_id ON event_logs(organization_id);
"""

POSTGRES_SCHEMA = """
CREATE TABLE IF NOT EXISTS organizations (
    organization_id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    slug TEXT NOT NULL UNIQUE,
    telegram_chat_id TEXT,
    telegram_chat_name TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS contractors (
    contractor_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT,
    name TEXT NOT NULL,
    nip TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    is_new INTEGER NOT NULL DEFAULT 1,
    last_invoice_date TEXT,
    last_invoice_number TEXT,
    invoice_count INTEGER NOT NULL DEFAULT 0,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT fk_contractors_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_contractors_org_nip ON contractors(organization_id, nip);

CREATE TABLE IF NOT EXISTS users (
    user_id BIGSERIAL PRIMARY KEY,
    login TEXT NOT NULL UNIQUE,
    display_name TEXT,
    telegram_user_id TEXT UNIQUE,
    organization_id BIGINT,
    password_hash TEXT NOT NULL,
    password_salt TEXT NOT NULL,
    role TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    last_login_at TEXT,
    created_by_user_id BIGINT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT fk_users_creator
        FOREIGN KEY (created_by_user_id) REFERENCES users(user_id),
    CONSTRAINT fk_users_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
);

CREATE INDEX IF NOT EXISTS idx_users_login ON users(login);
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_telegram_user_id ON users(telegram_user_id);
CREATE INDEX IF NOT EXISTS idx_users_organization_id ON users(organization_id);

CREATE TABLE IF NOT EXISTS user_sessions (
    session_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    ip_address TEXT,
    user_agent TEXT,
    created_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    CONSTRAINT fk_user_sessions_user
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);

CREATE TABLE IF NOT EXISTS invoices (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT,
    incoming_date TEXT NOT NULL,
    source TEXT NOT NULL,
    file_name TEXT NOT NULL,
    document_type TEXT,
    invoice_number TEXT,
    ksef_number TEXT,
    issuer_nip TEXT,
    issuer_name TEXT,
    issue_date TEXT,
    sale_date TEXT,
    gross_amount DOUBLE PRECISION,
    currency TEXT NOT NULL DEFAULT 'PLN',
    status TEXT NOT NULL,
    duplicate_type TEXT NOT NULL DEFAULT 'brak',
    flag_reason TEXT,
    contractor_id BIGINT,
    file_link TEXT,
    file_storage_key TEXT,
    ocr_link TEXT,
    ocr_storage_key TEXT,
    storage_backend TEXT,
    source_external_id TEXT,
    source_sender_name TEXT,
    source_sender_id TEXT,
    source_metadata TEXT,
    invoice_hash TEXT NOT NULL UNIQUE,
    ocr_raw_text TEXT,
    ocr_confidence DOUBLE PRECISION,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT fk_invoices_contractor
        FOREIGN KEY (contractor_id) REFERENCES contractors(contractor_id),
    CONSTRAINT fk_invoices_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
);

CREATE INDEX IF NOT EXISTS idx_invoices_ksef_number ON invoices(ksef_number);
CREATE INDEX IF NOT EXISTS idx_invoices_number_nip ON invoices(invoice_number, issuer_nip);
CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status);
CREATE INDEX IF NOT EXISTS idx_invoices_source ON invoices(source);
CREATE INDEX IF NOT EXISTS idx_invoices_organization_id ON invoices(organization_id);

CREATE TABLE IF NOT EXISTS tasks (
    task_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    task_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL,
    priority TEXT NOT NULL,
    due_at TEXT,
    remind_at TEXT,
    assigned_user_id BIGINT,
    created_by_user_id BIGINT NOT NULL,
    completed_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT fk_tasks_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    CONSTRAINT fk_tasks_assigned_user
        FOREIGN KEY (assigned_user_id) REFERENCES users(user_id),
    CONSTRAINT fk_tasks_created_by_user
        FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_tasks_organization_id ON tasks(organization_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_due_at ON tasks(due_at);
CREATE INDEX IF NOT EXISTS idx_tasks_remind_at ON tasks(remind_at);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_user_id ON tasks(assigned_user_id);

CREATE TABLE IF NOT EXISTS task_notes (
    task_note_id BIGSERIAL PRIMARY KEY,
    task_id BIGINT NOT NULL,
    organization_id BIGINT NOT NULL,
    note_text TEXT NOT NULL,
    created_by_user_id BIGINT NOT NULL,
    created_at TEXT NOT NULL,
    CONSTRAINT fk_task_notes_task
        FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
    CONSTRAINT fk_task_notes_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    CONSTRAINT fk_task_notes_created_by_user
        FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_task_notes_task_id ON task_notes(task_id);

CREATE TABLE IF NOT EXISTS task_history (
    task_history_id BIGSERIAL PRIMARY KEY,
    task_id BIGINT NOT NULL,
    organization_id BIGINT NOT NULL,
    action_type TEXT NOT NULL,
    actor TEXT NOT NULL,
    message TEXT NOT NULL,
    details TEXT,
    created_at TEXT NOT NULL,
    CONSTRAINT fk_task_history_task
        FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
    CONSTRAINT fk_task_history_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
);

CREATE INDEX IF NOT EXISTS idx_task_history_task_id ON task_history(task_id);

CREATE TABLE IF NOT EXISTS invoice_relations (
    id BIGSERIAL PRIMARY KEY,
    invoice_id BIGINT NOT NULL,
    related_invoice_id BIGINT NOT NULL,
    relation_type TEXT NOT NULL,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL,
    CONSTRAINT fk_relations_invoice
        FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
    CONSTRAINT fk_relations_related_invoice
        FOREIGN KEY (related_invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_invoice_relations_invoice_id ON invoice_relations(invoice_id);

CREATE TABLE IF NOT EXISTS event_logs (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT,
    event_time TEXT NOT NULL,
    event_type TEXT NOT NULL,
    invoice_id BIGINT,
    source TEXT,
    status_before TEXT,
    status_after TEXT,
    decision_reason TEXT,
    actor TEXT NOT NULL,
    details TEXT,
    CONSTRAINT fk_event_logs_invoice
        FOREIGN KEY (invoice_id) REFERENCES invoices(id),
    CONSTRAINT fk_event_logs_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
);

CREATE INDEX IF NOT EXISTS idx_event_logs_invoice_id ON event_logs(invoice_id);
CREATE INDEX IF NOT EXISTS idx_event_logs_event_time ON event_logs(event_time DESC);
CREATE INDEX IF NOT EXISTS idx_event_logs_organization_id ON event_logs(organization_id);
"""

SQLITE_RESET_SCRIPT = """
PRAGMA foreign_keys = OFF;
DROP TABLE IF EXISTS invoice_relations;
DROP TABLE IF EXISTS task_history;
DROP TABLE IF EXISTS task_notes;
DROP TABLE IF EXISTS tasks;
DROP TABLE IF EXISTS event_logs;
DROP TABLE IF EXISTS user_sessions;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS invoices;
DROP TABLE IF EXISTS contractors;
DROP TABLE IF EXISTS organizations;
PRAGMA foreign_keys = ON;
"""

POSTGRES_RESET_SCRIPT = """
DROP TABLE IF EXISTS invoice_relations CASCADE;
DROP TABLE IF EXISTS task_history CASCADE;
DROP TABLE IF EXISTS task_notes CASCADE;
DROP TABLE IF EXISTS tasks CASCADE;
DROP TABLE IF EXISTS event_logs CASCADE;
DROP TABLE IF EXISTS user_sessions CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS invoices CASCADE;
DROP TABLE IF EXISTS contractors CASCADE;
DROP TABLE IF EXISTS organizations CASCADE;
"""

ADDITIVE_COLUMNS = {
    "organizations": {
        "telegram_chat_id": "TEXT",
        "telegram_chat_name": "TEXT",
    },
    "contractors": {
        "organization_id": "INTEGER",
    },
    "users": {
        "organization_id": "INTEGER",
        "telegram_user_id": "TEXT",
    },
    "invoices": {
        "organization_id": "INTEGER",
        "document_type": "TEXT",
        "file_storage_key": "TEXT",
        "ocr_storage_key": "TEXT",
        "storage_backend": "TEXT",
        "source_external_id": "TEXT",
        "source_sender_name": "TEXT",
        "source_sender_id": "TEXT",
        "source_metadata": "TEXT",
    },
    "event_logs": {
        "organization_id": "INTEGER",
    },
    "tasks": {
        "remind_at": "TEXT",
    },
}

ADDITIVE_INDEXES = (
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_organizations_telegram_chat_id ON organizations(telegram_chat_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_telegram_user_id ON users(telegram_user_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_contractors_org_nip ON contractors(organization_id, nip)",
    "CREATE INDEX IF NOT EXISTS idx_users_organization_id ON users(organization_id)",
    "CREATE INDEX IF NOT EXISTS idx_invoices_organization_id ON invoices(organization_id)",
    "CREATE INDEX IF NOT EXISTS idx_event_logs_organization_id ON event_logs(organization_id)",
    "CREATE INDEX IF NOT EXISTS idx_tasks_remind_at ON tasks(remind_at)",
)


def _split_sql_script(script: str) -> list[str]:
    return [statement.strip() for statement in script.split(";") if statement.strip()]


class DatabaseConnection:
    def __init__(self, raw_connection: Any, backend: str, driver_name: str) -> None:
        self.raw_connection = raw_connection
        self.backend = backend
        self.driver_name = driver_name

    def execute(self, query: str, params: Iterable[Any] | None = None):
        normalized_params = list(params or [])
        translated_query = self._translate_query(query)
        if self.backend == "sqlite":
            return self.raw_connection.execute(translated_query, normalized_params)
        if self.driver_name == "psycopg":
            return self.raw_connection.execute(translated_query, normalized_params)
        cursor = self.raw_connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute(translated_query, normalized_params)
        return cursor

    def commit(self) -> None:
        self.raw_connection.commit()

    def rollback(self) -> None:
        self.raw_connection.rollback()

    def close(self) -> None:
        self.raw_connection.close()

    def _translate_query(self, query: str) -> str:
        if self.backend == "sqlite":
            return query
        return query.replace("?", "%s")


def _open_sqlite_connection() -> DatabaseConnection:
    connection = sqlite3.connect(SQLITE_DB_PATH)
    connection.row_factory = sqlite3.Row
    return DatabaseConnection(connection, backend="sqlite", driver_name="sqlite")


def _open_postgres_connection() -> DatabaseConnection:
    if not DATABASE_URL:
        raise RuntimeError("Brakuje zmiennej INVOICE_DATABASE_URL dla PostgreSQL.")
    if psycopg is not None:
        connection = psycopg.connect(DATABASE_URL, row_factory=dict_row)
        return DatabaseConnection(connection, backend="postgresql", driver_name="psycopg")
    if psycopg2 is not None:
        connection = psycopg2.connect(DATABASE_URL)
        return DatabaseConnection(connection, backend="postgresql", driver_name="psycopg2")
    raise RuntimeError(
        "Brakuje sterownika PostgreSQL. Zainstaluj 'psycopg[binary]' albo 'psycopg2-binary'."
    )


def _open_connection() -> DatabaseConnection:
    ensure_directories()
    return _open_postgres_connection() if uses_postgresql() else _open_sqlite_connection()


def _run_schema_script(connection: DatabaseConnection, script: str) -> None:
    if connection.backend == "sqlite":
        connection.raw_connection.executescript(script)
        return
    for statement in _split_sql_script(script):
        connection.execute(statement)


def _list_table_columns(connection: DatabaseConnection, table_name: str) -> set[str]:
    if connection.backend == "sqlite":
        rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
        return {row["name"] for row in rows}

    rows = connection.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = ?
        """,
        (table_name,),
    ).fetchall()
    return {row["column_name"] for row in rows}


def _ensure_additive_columns(connection: DatabaseConnection) -> None:
    for table_name, columns in ADDITIVE_COLUMNS.items():
        existing = _list_table_columns(connection, table_name)
        for column_name, column_type in columns.items():
            if column_name in existing:
                continue
            connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")


def _ensure_additive_indexes(connection: DatabaseConnection) -> None:
    for statement in ADDITIVE_INDEXES:
        connection.execute(statement)


def _sqlite_table_sql(connection: DatabaseConnection, table_name: str) -> str:
    row = connection.execute(
        """
        SELECT sql
        FROM sqlite_master
        WHERE type = 'table'
          AND name = ?
        """,
        (table_name,),
    ).fetchone()
    return str(row["sql"] or "") if row else ""


def _ensure_sqlite_multi_org_contractors(connection: DatabaseConnection) -> None:
    if connection.backend != "sqlite":
        return

    contractors_sql = _sqlite_table_sql(connection, "contractors").upper()
    if "NIP TEXT NOT NULL UNIQUE" not in contractors_sql:
        return

    connection.raw_connection.executescript(
        """
        PRAGMA foreign_keys = OFF;

        CREATE TABLE contractors__migracja (
            contractor_id INTEGER PRIMARY KEY AUTOINCREMENT,
            organization_id INTEGER,
            name TEXT NOT NULL,
            nip TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            is_new INTEGER NOT NULL DEFAULT 1,
            last_invoice_date TEXT,
            last_invoice_number TEXT,
            invoice_count INTEGER NOT NULL DEFAULT 0,
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
        );

        INSERT INTO contractors__migracja (
            contractor_id, organization_id, name, nip, email, phone, is_new, last_invoice_date,
            last_invoice_number, invoice_count, notes, created_at, updated_at
        )
        SELECT
            contractor_id, organization_id, name, nip, email, phone, is_new, last_invoice_date,
            last_invoice_number, invoice_count, notes, created_at, updated_at
        FROM contractors;

        DROP TABLE contractors;
        ALTER TABLE contractors__migracja RENAME TO contractors;
        CREATE UNIQUE INDEX IF NOT EXISTS idx_contractors_org_nip ON contractors(organization_id, nip);

        PRAGMA foreign_keys = ON;
        """
    )


def initialize_database() -> None:
    connection = _open_connection()
    try:
        _run_schema_script(connection, POSTGRES_SCHEMA if uses_postgresql() else SQLITE_SCHEMA)
        _ensure_additive_columns(connection)
        _ensure_sqlite_multi_org_contractors(connection)
        _ensure_additive_indexes(connection)
        connection.commit()
    finally:
        connection.close()


def reset_database() -> None:
    connection = _open_connection()
    try:
        _run_schema_script(connection, POSTGRES_RESET_SCRIPT if uses_postgresql() else SQLITE_RESET_SCRIPT)
        connection.commit()
    finally:
        connection.close()
    initialize_database()


@contextmanager
def get_connection():
    connection = _open_connection()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def execute_insert_returning_id(
    connection: DatabaseConnection,
    query: str,
    params: Iterable[Any],
    id_column: str,
) -> int:
    if connection.backend == "sqlite":
        cursor = connection.execute(query, params)
        return int(cursor.lastrowid)
    cursor = connection.execute(f"{query.rstrip().rstrip(';')} RETURNING {id_column}", params)
    row = cursor.fetchone()
    return int(row[id_column])
