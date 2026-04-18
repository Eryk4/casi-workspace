from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import json
import re
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def now_local_datetime_value() -> str:
    return datetime.now().replace(second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M")


def future_local_datetime_value(hours: int = 24) -> str:
    return (datetime.now() + timedelta(hours=hours)).replace(second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M")


def parse_datetime_flexible(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, date):
        parsed = datetime.combine(value, datetime.min.time())
    else:
        normalized = str(value).strip()
        if not normalized:
            return None
        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            try:
                parsed = datetime.combine(date.fromisoformat(normalized), datetime.min.time())
            except ValueError:
                return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def age_in_days(value: Any, *, reference: datetime | None = None) -> int | None:
    parsed = parse_datetime_flexible(value)
    if parsed is None:
        return None
    current = reference or datetime.now(timezone.utc)
    delta = current - parsed
    if delta.total_seconds() < 0:
        return 0
    return int(delta.total_seconds() // 86400)


def json_dumps(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def normalize_phone_identifier(value: Any) -> str | None:
    digits = re.sub(r"\D+", "", str(value or ""))
    if not digits:
        return None
    if digits.startswith("0048"):
        digits = digits[4:]
    elif digits.startswith("48") and len(digits) > 9:
        digits = digits[2:]
    if len(digits) < 9:
        return None
    return digits[-9:]


def extract_phone_identifiers(text: Any) -> list[str]:
    normalized_text = str(text or "")
    if not normalized_text.strip():
        return []

    matches = re.findall(r"(?:\+?48[\s-]*)?(?:\d[\s-]*){9,11}", normalized_text)
    identifiers: list[str] = []
    for match in matches:
        normalized = normalize_phone_identifier(match)
        if normalized and normalized not in identifiers:
            identifiers.append(normalized)
    return identifiers


def text_contains_phone_identifier(text: Any, phone_identifier: Any) -> bool:
    normalized_phone = normalize_phone_identifier(phone_identifier)
    if not normalized_phone:
        return False
    return normalized_phone in extract_phone_identifiers(text)
