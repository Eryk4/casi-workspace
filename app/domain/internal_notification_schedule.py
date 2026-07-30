from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


DEFAULT_TIMEZONE_NAME = "Europe/Warsaw"
DEFAULT_LOCAL_TIME = "08:00"
SCHEDULE_CADENCE_DAILY = "daily"
UTC = timezone.utc
_LOCAL_TIME_PATTERN = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")


@dataclass(frozen=True)
class ScheduledOccurrence:
    scheduled_local_date: str
    as_of_date: str
    scheduled_for_utc: str


def normalize_now_utc(value: datetime | None = None) -> datetime:
    current = value or datetime.now(UTC)
    if current.tzinfo is None:
        raise ValueError("now_utc musi zawierac informacje o strefie czasowej.")
    return current.astimezone(UTC)


def utc_iso(value: datetime) -> str:
    return normalize_now_utc(value).isoformat(timespec="seconds")


def validate_timezone_name(value: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise ValueError("Strefa czasowa jest wymagana.")
    try:
        ZoneInfo(normalized)
    except ZoneInfoNotFoundError:
        raise ValueError("Nieprawidlowa strefa czasowa IANA.") from None
    return normalized


def validate_local_time(value: str) -> str:
    normalized = str(value or "").strip()
    if not _LOCAL_TIME_PATTERN.fullmatch(normalized):
        raise ValueError("Godzina musi miec format HH:MM.")
    return normalized


def local_date_for(now_utc: datetime, timezone_name: str) -> date:
    zone = ZoneInfo(validate_timezone_name(timezone_name))
    return normalize_now_utc(now_utc).astimezone(zone).date()


def scheduled_local_datetime_utc(
    local_date: date,
    local_time: str,
    timezone_name: str,
) -> datetime:
    """Resolve a local wall-clock time deterministically.

    Ambiguous autumn times use the first occurrence. Non-existent spring times
    move forward to the first valid minute after the DST gap.
    """
    zone = ZoneInfo(validate_timezone_name(timezone_name))
    hour, minute = (int(part) for part in validate_local_time(local_time).split(":"))
    naive = datetime.combine(local_date, time(hour=hour, minute=minute))
    for offset_minutes in range(0, 181):
        candidate = naive + timedelta(minutes=offset_minutes)
        valid: list[datetime] = []
        for fold in (0, 1):
            aware = candidate.replace(tzinfo=zone, fold=fold)
            round_trip = aware.astimezone(UTC).astimezone(zone).replace(tzinfo=None)
            if round_trip == candidate:
                valid.append(aware.astimezone(UTC))
        if valid:
            return min(valid)
    raise ValueError("Nie mozna wyznaczyc poprawnego czasu uruchomienia w wybranej strefie.")


def calculate_next_run_at_utc(
    *,
    enabled: bool,
    local_time: str,
    timezone_name: str,
    now_utc: datetime,
    last_succeeded_local_date: str | None = None,
) -> str | None:
    if not enabled:
        return None
    zone = ZoneInfo(validate_timezone_name(timezone_name))
    normalized_time = validate_local_time(local_time)
    current = normalize_now_utc(now_utc)
    current_local = current.astimezone(zone)
    candidate_date = current_local.date()
    today_scheduled = scheduled_local_datetime_utc(candidate_date, normalized_time, timezone_name)
    if current >= today_scheduled or last_succeeded_local_date == candidate_date.isoformat():
        candidate_date += timedelta(days=1)
    return utc_iso(scheduled_local_datetime_utc(candidate_date, normalized_time, timezone_name))


def occurrence_for_due_schedule(
    *,
    local_time: str,
    timezone_name: str,
    now_utc: datetime,
) -> ScheduledOccurrence:
    current_date = local_date_for(now_utc, timezone_name)
    return ScheduledOccurrence(
        scheduled_local_date=current_date.isoformat(),
        as_of_date=current_date.isoformat(),
        scheduled_for_utc=utc_iso(scheduled_local_datetime_utc(current_date, local_time, timezone_name)),
    )


def next_run_after_local_date(
    *,
    completed_local_date: str,
    local_time: str,
    timezone_name: str,
) -> str:
    next_date = date.fromisoformat(completed_local_date) + timedelta(days=1)
    return utc_iso(scheduled_local_datetime_utc(next_date, local_time, timezone_name))
