from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def json_dumps(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)
