from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


RESET_CONFIRMATION_ENV = "CASI_ALLOW_LOCAL_SANDBOX_RESET"


class ResetGuardError(RuntimeError):
    pass


@dataclass(frozen=True)
class LocalSandboxResetPlan:
    db_engine: str
    sqlite_path: Path
    data_dir: Path
    backup_path: Path | None

    @property
    def detected_database(self) -> str:
        return f"SQLite: {self.sqlite_path}"


def _is_truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "tak", "yes", "on"}


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _format_blocked_reset_message(
    *,
    detected_database: str,
    reasons: list[str],
    sqlite_path: Path,
) -> str:
    reasons_text = "\n".join(f"- {reason}" for reason in reasons)
    return (
        "Reset/reseed zostal zablokowany przez guardrail bezpieczenstwa danych.\n"
        f"Wykryta baza: {detected_database}\n"
        "Powody blokady:\n"
        f"{reasons_text}\n"
        "Reset wolno uruchomic tylko dla lokalnego sandboxu SQLite pod katalogiem data/.\n"
        f"Aktywna sciezka SQLite: {sqlite_path}\n"
        f"Aby swiadomie zresetowac lokalny sandbox, ustaw {RESET_CONFIRMATION_ENV}=1 "
        "i upewnij sie, ze nie pracujesz na prawdziwych danych.\n"
        "Nie uzywaj tej flagi dla stagingu, produkcji, zdalnej bazy ani danych klienta."
    )


def validate_local_sandbox_reset_allowed(
    *,
    db_engine: str,
    sqlite_path: str | Path,
    data_dir: str | Path,
    database_url: str | None = None,
    invoice_database_url: str | None = None,
    allow_local_sandbox_reset: str | None = None,
) -> LocalSandboxResetPlan:
    normalized_engine = str(db_engine or "").strip().lower()
    resolved_sqlite_path = Path(sqlite_path).resolve()
    resolved_data_dir = Path(data_dir).resolve()
    raw_database_url = str(database_url or "").strip()
    raw_invoice_database_url = str(invoice_database_url or "").strip()
    detected_database = (
        f"{normalized_engine or 'unknown'} database"
        if normalized_engine not in {"sqlite", "sqlite3"}
        else f"SQLite: {resolved_sqlite_path}"
    )
    reasons: list[str] = []

    if normalized_engine not in {"sqlite", "sqlite3"}:
        reasons.append(f"silnik bazy nie jest SQLite: {normalized_engine or 'brak'}")
    if raw_database_url:
        reasons.append("aktywna jest zmienna DATABASE_URL")
    if raw_invoice_database_url:
        reasons.append("aktywna jest zmienna INVOICE_DATABASE_URL")
    if not _is_relative_to(resolved_sqlite_path, resolved_data_dir):
        reasons.append("sciezka SQLite nie znajduje sie pod lokalnym katalogiem data/")

    path_text = str(resolved_sqlite_path).lower()
    suspicious_fragments = ("production", "prod", "staging", "railway", "digitalocean", "postgres")
    suspicious = [fragment for fragment in suspicious_fragments if fragment in path_text]
    if suspicious:
        reasons.append(f"sciezka SQLite wyglada na nielokalna lub produkcyjna: {', '.join(suspicious)}")

    if not _is_truthy(allow_local_sandbox_reset):
        reasons.append(f"brak swiadomego potwierdzenia {RESET_CONFIRMATION_ENV}=1")

    if reasons:
        raise ResetGuardError(
            _format_blocked_reset_message(
                detected_database=detected_database,
                reasons=reasons,
                sqlite_path=resolved_sqlite_path,
            )
        )

    return LocalSandboxResetPlan(
        db_engine=normalized_engine,
        sqlite_path=resolved_sqlite_path,
        data_dir=resolved_data_dir,
        backup_path=None,
    )


def create_local_sqlite_backup(plan: LocalSandboxResetPlan) -> LocalSandboxResetPlan:
    if not plan.sqlite_path.exists():
        return plan
    if not plan.sqlite_path.is_file():
        raise ResetGuardError(
            "Reset/reseed zostal zablokowany: sciezka SQLite istnieje, ale nie jest plikiem. "
            f"Sciezka: {plan.sqlite_path}"
        )

    backup_dir = plan.data_dir / "backup" / "reset"
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"{plan.sqlite_path.stem}_{timestamp}{plan.sqlite_path.suffix}"
    try:
        shutil.copy2(plan.sqlite_path, backup_path)
    except OSError as error:
        raise ResetGuardError(
            "Reset/reseed zostal zablokowany, bo nie udalo sie wykonac backupu lokalnej bazy SQLite. "
            f"Zrodlo: {plan.sqlite_path}. Blad: {error}"
        ) from error
    return LocalSandboxResetPlan(
        db_engine=plan.db_engine,
        sqlite_path=plan.sqlite_path,
        data_dir=plan.data_dir,
        backup_path=backup_path,
    )


def prepare_local_sandbox_reset(
    *,
    db_engine: str,
    sqlite_path: str | Path,
    data_dir: str | Path,
    database_url: str | None = None,
    invoice_database_url: str | None = None,
    allow_local_sandbox_reset: str | None = None,
) -> LocalSandboxResetPlan:
    plan = validate_local_sandbox_reset_allowed(
        db_engine=db_engine,
        sqlite_path=sqlite_path,
        data_dir=data_dir,
        database_url=database_url,
        invoice_database_url=invoice_database_url,
        allow_local_sandbox_reset=allow_local_sandbox_reset,
    )
    return create_local_sqlite_backup(plan)


def prepare_local_sandbox_reset_from_environment(
    *,
    db_engine: str,
    sqlite_path: str | Path,
    data_dir: str | Path,
) -> LocalSandboxResetPlan:
    return prepare_local_sandbox_reset(
        db_engine=db_engine,
        sqlite_path=sqlite_path,
        data_dir=data_dir,
        database_url=os.getenv("DATABASE_URL", ""),
        invoice_database_url=os.getenv("INVOICE_DATABASE_URL", ""),
        allow_local_sandbox_reset=os.getenv(RESET_CONFIRMATION_ENV, ""),
    )

