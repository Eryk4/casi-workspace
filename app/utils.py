from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def now_local_datetime_value() -> str:
    return datetime.now().replace(second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M")


def future_local_datetime_value(hours: int = 24) -> str:
    return (datetime.now() + timedelta(hours=hours)).replace(second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M")


def json_dumps(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)
