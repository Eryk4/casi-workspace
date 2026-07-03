from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RUNTIME_ROOT = ROOT / "data" / "test_runtime" / f"pid_{os.getpid()}"
RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)

os.environ["INVOICE_DATABASE_URL"] = ""
os.environ["DATABASE_URL"] = ""
os.environ["INVOICE_DB_ENGINE"] = "sqlite"
os.environ.setdefault("INVOICE_SQLITE_PATH", str(RUNTIME_ROOT / "invoice_ops.sqlite3"))
os.environ.setdefault("INVOICE_STORAGE_ROOT", str(RUNTIME_ROOT / "magazyn"))
os.environ["INVOICE_STORAGE_BACKEND"] = "local"
os.environ["INVOICE_MAX_ACTIVE_DEVICES_PER_ACCOUNT"] = "3"
