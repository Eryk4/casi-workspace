from __future__ import annotations

import os
import sys
from pathlib import Path


def _flag_enabled(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "tak", "yes"}


def _looks_like_test_run() -> bool:
    argv = [part.lower() for part in sys.argv]
    joined = " ".join(argv)
    return "unittest" in joined or any(part.endswith(".py") and "test" in Path(part).name.lower() for part in argv)


def _configure_test_isolation() -> None:
    if _flag_enabled("INVOICE_DISABLE_TEST_ISOLATION"):
        return
    if not _looks_like_test_run():
        return

    base_dir = Path(__file__).resolve().parent
    runtime_root = base_dir / "data" / "test_runtime" / f"pid_{os.getpid()}"
    runtime_root.mkdir(parents=True, exist_ok=True)

    sqlite_path = runtime_root / "invoice_ops.sqlite3"
    storage_root = runtime_root / "magazyn"

    os.environ.setdefault("INVOICE_SQLITE_PATH", str(sqlite_path))
    os.environ.setdefault("INVOICE_STORAGE_ROOT", str(storage_root))


_configure_test_isolation()
