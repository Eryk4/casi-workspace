from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from app.repositories.user_repository import UserRepository
from app.services.calendar_service import CalendarService


@dataclass
class _MatchedUser:
    user_id: int
    display_name: str
    login: str


@dataclass
class _MatchedCalendar:
    user_calendar_id: int
    display_name: str
    calendar_kind: str
    default_duration_minutes: int


class NaturalTaskCommandService:
    TITLE_REVIEW_THRESHOLD = 0.80

    WEEKDAY_MAP = {
        "poniedzialek": 0,
        "poniedziaĹ‚ek": 0,
        "wtorek": 1,
        "sroda": 2,
        "Ĺ›roda": 2,
        "czwartek": 3,
        "piatek": 4,
        "piÄ…tek": 4,
        "sobota": 5,
        "niedziela": 6,
    }

    def __init__(self, user_repository: UserRepository, calendar_service: CalendarService) -> None:
        self.user_repository = user_repository
        self.calendar_service = calendar_service

    def parse(
        self,
        command_text: str,
        *,
        actor_user: dict[str, Any],
        organization_id: int | None,
    ) -> dict[str, Any]:
        text = str(command_text or "").strip()
        if not text:
            raise ValueError("Wpisz tresc polecenia do analizy.")

        warnings: list[str] = []
        working_text = self._normalize_spaces(text)

        task_type = self._detect_task_type(text)
        visibility_scope = self._detect_visibility_scope(text)
        working_text = self._strip_known_prefixes(working_text)

        calendars = self.calendar_service.get_user_calendar_options(actor_user)
        matched_calendar, working_text = self._extract_calendar(working_text, calendars)
        if matched_calendar is None and "kalendarz" in working_text.lower():
            warnings.append("Nie rozpoznano docelowego kalendarza Google.")

        matched_user, working_text = self._extract_assignee(working_text, organization_id=organization_id)
        if matched_user is None and re.search(r"\bdla\s+\S+", working_text, flags=re.IGNORECASE):
            warnings.append("Nie rozpoznano osoby docelowej z tej organizacji.")

        due_at, remind_at, working_text, time_warnings = self._extract_datetime_and_reminder(
            working_text,
            task_type=task_type,
            calendar=matched_calendar,
        )
        warnings.extend(time_warnings)
        recurrence, working_text = self._extract_recurrence(working_text)

        title, fallback = self._build_title_with_fallback(text, working_text, task_type, due_at=due_at, remind_at=remind_at, warnings=warnings)
        if not title:
            raise ValueError("Nie udalo sie rozpoznac tytulu wpisu. Doprecyzuj tresc polecenia.")

        payload = {
            "title": title,
            "task_type": task_type,
            "status": "nowe",
            "priority": self._detect_priority(text),
            "visibility_scope": visibility_scope,
            "assigned_user_id": matched_user.user_id if matched_user else None,
            "visible_user_ids": [matched_user.user_id] if visibility_scope == "wybrane_osoby" and matched_user else [],
            "calendar_id": matched_calendar.user_calendar_id if matched_calendar else None,
            "due_at": due_at,
            "remind_at": remind_at,
            "calendar_duration_minutes": self._detect_duration_minutes(text, matched_calendar),
            "description": self._build_description(text, title),
            "recurrence_pattern": recurrence["pattern"],
            "recurrence_interval": recurrence["interval"],
            "recurrence_weekdays": recurrence["weekdays"],
        }

        if visibility_scope == "wybrane_osoby" and not matched_user:
            warnings.append("Dla widocznosci 'Wybrane osoby' wskaz konkretna osobe.")

        summary = {
            "task_type_label": self._task_type_label(task_type),
            "title": title,
            "priority_label": self._priority_label(payload["priority"]),
            "visibility_label": self._visibility_label(visibility_scope),
            "due_at": due_at,
            "remind_at": remind_at,
            "assigned_user_name": matched_user.display_name if matched_user else None,
            "calendar_name": matched_calendar.display_name if matched_calendar else None,
            "recurrence_label": recurrence["label"],
        }

        return {
            "original_text": text,
            "normalized_text": working_text,
            "payload": payload,
            "summary": summary,
            "warnings": warnings,
            "matched_user": (
                {
                    "user_id": matched_user.user_id,
                    "display_name": matched_user.display_name,
                    "login": matched_user.login,
                }
                if matched_user
                else None
            ),
            "matched_calendar": (
                {
                    "user_calendar_id": matched_calendar.user_calendar_id,
                    "display_name": matched_calendar.display_name,
                    "calendar_kind": matched_calendar.calendar_kind,
                    "default_duration_minutes": matched_calendar.default_duration_minutes,
                }
                if matched_calendar
                else None
            ),
            "confidence": fallback["confidence"],
            "fallback": fallback,
        }

    def _normalize_spaces(self, value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()

    def _normalize_for_matching(self, value: str) -> str:
        folded = str(value or "").replace("ł", "l").replace("Ł", "L")
        folded = unicodedata.normalize("NFKD", folded)
        folded = "".join(ch for ch in folded if not unicodedata.combining(ch))
        folded = folded.lower()
        folded = re.sub(r"[^a-z0-9: ]+", " ", folded)
        return self._normalize_spaces(folded)

    def _strip_known_prefixes(self, value: str) -> str:
        cleaned = value
        patterns = [
            r"^(?:dodaj|utworz|utwórz|zapisz|stworz|stwórz|zaplanuj)(?:\s+mi)?\s+",
            r"^(?:przypomnij(?:\s+mi)?(?:\s+prosz(?:e|ę))?(?:\s+mi)?|przypomnij(?:\s+prosz(?:e|ę))?(?:\s+mi)?)\s+",
            r"^(?:ustaw\s+przypomnienie|dodaj\s+przypomnienie)\s+",
        ]
        for pattern in patterns:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
        return cleaned.strip()

    def _detect_task_type(self, text: str) -> str:
        lowered = self._normalize_for_matching(text)
        if any(keyword in lowered for keyword in ("spotkanie", "wydarzenie", "wyjazd", "rozmowa", "spotkaj")):
            return "wydarzenie"
        if any(keyword in lowered for keyword in ("przypomnienie", "przypomnij", "pamietaj")):
            return "przypomnienie"
        if any(keyword in lowered for keyword in ("notatka", "zanotuj", "zapisz notatke")):
            return "notatka"
        return "zadanie"

    def _detect_priority(self, text: str) -> str:
        lowered = self._normalize_for_matching(text)
        if any(keyword in lowered for keyword in ("pilne", "krytyczne", "natychmiast", "bardzo wazne", "wysoki priorytet")):
            return "krytyczny"
        if any(keyword in lowered for keyword in ("wazne", "wazna", "wazny", "istotne")):
            return "wysoki"
        if any(keyword in lowered for keyword in ("niewazne", "niski priorytet", "mniej wazne")):
            return "niski"
        return "normalny"

    def _detect_visibility_scope(self, text: str) -> str:
        lowered = self._normalize_for_matching(text)
        if "dla calej organizacji" in lowered or "dla wszystkich" in lowered:
            return "organizacja"
        if "dla wybranych osob" in lowered:
            return "wybrane_osoby"
        return "prywatne"

    def _detect_duration_minutes(self, text: str, calendar: _MatchedCalendar | None) -> int:
        normalized = self._normalize_for_matching(text)
        match = re.search(r"\bna\s+(\d{1,3})\s*min\b", normalized)
        if match:
            return min(max(1, int(match.group(1))), 1440)
        if re.search(r"(?:na|potrwa(?:\s+to)?|trwa(?:\s+to)?|bedzie\s+trwalo?)\s+poltorej\s+godzin(?:y|e)?", normalized):
            return 90
        if re.search(r"(?:na|potrwa(?:\s+to)?|trwa(?:\s+to)?|bedzie\s+trwalo?)\s+1[,.]5\s+godzin(?:y|e)?", normalized):
            return 90
        hours_match = re.search(
            r"(?:na|potrwa(?:\s+to)?|trwa(?:\s+to)?|bedzie\s+trwalo?)\s+(\d{1,2})(?:[,.](\d))?\s+godzin(?:y|e)?",
            normalized,
        )
        if hours_match:
            hours = int(hours_match.group(1))
            fraction = hours_match.group(2)
            if fraction == "5":
                return min(max(1, hours * 60 + 30), 1440)
            return min(max(1, hours * 60), 1440)
        if calendar and int(calendar.default_duration_minutes or 0) > 0:
            return int(calendar.default_duration_minutes)
        return 60

    def _strip_task_noise(self, text: str) -> str:
        cleaned = text
        patterns = [
            r"\bprzypomnij(?:\s+mi)?\b",
            r"\bustaw\s+przypomnienie\b",
            r"\bdodaj\s+przypomnienie\b",
            r"\bza\s+tydzien(?:\s+(?:w|we)\s+\w+)?\b",
            r"\bza\s+tydzień(?:\s+(?:w|we)\s+\w+)?\b",
            r"\bza\s+\d+\s+tygodnie?\b",
            r"\bza\s+\d+\s+dni?\b",
            r"\bjutro\b",
            r"\bpojutrze\b",
            r"\bdzis(?:iaj)?\b",
            r"\bdziś(?:iaj)?\b",
            r"\bwczoraj\b",
            r"\b(?:w|we)\s+(?:przyszly|przyszła|przyszlym|najblizszy|najblizsza|najblizszym|przyszły|najbliższy|najbliższa|najbliższym)\s+\w+\b",
            r"\b(?:w|we)\s+(?:poniedzialek|wtorek|sroda|czwartek|piatek|sobota|niedziela)\b",
            r"\b\d{4}-\d{2}-\d{2}\b",
            r"\b\d{1,2}[./-]\d{1,2}(?:[./-]\d{2,4})?\b",
            r"\b\d{1,2}:\d{2}\b",
            r"\b(?:o|na)\s+\d{1,2}(?::\d{2})?\b",
            r"\b(?:rano|wieczorem|popoludniu|po południu)\b",
            r"\b(?:dzien|dzień|dnia|dni)\s+(?:wczesniej|wcześniej)\b",
            r"\b(?:godzina|godzine|godzinę|godziny|godzin)\s+(?:wczesniej|wcześniej)\b",
            r"\b\d{1,3}\s*min(?:ut(?:y|a|e)?|)\s+(?:wczesniej|wcześniej)\b",
            r"\b(?:p[oó]l|pół)\s+godziny\s+(?:wczesniej|wcześniej)\b",
            r"\bpotrwa(?:\s+to)?\s+p[óo][łl]torej\s+godzin(?:y|e)?\b",
            r"\bpotrwa(?:\s+to)?\s+1[,.]5\s+godzin(?:y|e)?\b",
            r"\bpotrwa(?:\s+to)?\s+\d{1,2}(?:[,.]\d)?\s+godzin(?:y|e)?\b",
            r"\bpotrwa\s+godzin(?:y|e)?\b",
            r"\btrwa\s+godzin(?:y|e)?\b",
            r"\bna\s+\d{1,3}\s*min\b",
            r"\bbedzie\b",
            r"\bbędzie\b",
            r"\bma\s+byc\b",
            r"\bma\s+być\b",
            r"\bsie\s+odbedzie\b",
            r"\bsię\s+odbędzie\b",
            r"\bodbedzie\s+sie\b",
            r"\bodbędzie\s+się\b",
            r"\bco\s+tydzien\b",
            r"\bco\s+tydzień\b",
            r"\bco\s+tydzien\b",
            r"\bco\s+miesiac\b",
            r"\bco\s+miesiąc\b",
            r"\bw\s+dni\s+robocze\b",
        ]
        for pattern in patterns:
            cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"[.,;:!?]+", " ", cleaned)
        cleaned = self._normalize_spaces(cleaned)
        filler_words = {
            "i",
            "oraz",
            "to",
            "bedzie",
            "będzie",
            "ma",
            "byc",
            "być",
            "sie",
            "się",
            "na",
            "o",
            "w",
            "we",
            "do",
            "przed",
            "po",
            "za",
        }

        tokens = [token for token in cleaned.split(" ") if token]
        while tokens and tokens[0].lower() in filler_words:
            tokens.pop(0)
        while tokens and tokens[-1].lower() in filler_words:
            tokens.pop()

        filtered_tokens: list[str] = []
        for index, token in enumerate(tokens):
            lowered = token.lower()
            if lowered in filler_words:
                prev_token = tokens[index - 1].lower() if index > 0 else ""
                next_token = tokens[index + 1].lower() if index + 1 < len(tokens) else ""
                if index == 0 or index == len(tokens) - 1 or prev_token in filler_words or next_token in filler_words:
                    continue
            filtered_tokens.append(token)

        cleaned = self._normalize_spaces(" ".join(filtered_tokens))
        cleaned = re.sub(r"^(?:i|oraz|to|bedzie|będzie|ma|ma\s+byc|ma\s+być)\s+", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+(?:i|oraz|to|bedzie|będzie|ma|ma\s+byc|ma\s+być)$", "", cleaned, flags=re.IGNORECASE)
        return self._normalize_spaces(cleaned)

    def _extract_assignee(self, text: str, *, organization_id: int | None) -> tuple[_MatchedUser | None, str]:
        if organization_id is None:
            return None, text
        users = [
            user
            for user in self.user_repository.list_users(organization_id=organization_id)
            if user.get("is_active")
        ]
        matches = list(re.finditer(r"\bdla\s+([A-Za-z0-9_.Ä…Ä‡Ä™Ĺ‚Ĺ„ĂłĹ›ĹşĹĽÄ„Ä†ÄĹĹĂ“ĹšĹąĹ»-]+)", text, flags=re.IGNORECASE))
        for match in matches:
            token = match.group(1)
            normalized_token = token.lower()
            for user in users:
                display_name = str(user.get("display_name") or "").strip()
                login = str(user.get("login") or "").strip()
                first_name = display_name.split(" ", 1)[0].lower() if display_name else ""
                if normalized_token in {login.lower(), display_name.lower(), first_name}:
                    cleaned = (text[: match.start()] + text[match.end() :]).strip(" ,")
                    return (
                        _MatchedUser(
                            user_id=int(user["user_id"]),
                            display_name=display_name or login,
                            login=login,
                        ),
                        self._normalize_spaces(cleaned),
                    )
        return None, text

    def _extract_calendar(
        self,
        text: str,
        calendars: list[dict[str, Any]],
    ) -> tuple[_MatchedCalendar | None, str]:
        match = re.search(
            r"\bw\s+kalendarzu\s+(.+?)(?=(?:\s*,\s*przypomnij\b|\s*,\s*dla\b|\s+przypomnij\b|\s+dla\b|$))",
            text,
            flags=re.IGNORECASE,
        )
        if not match:
            match = re.search(
                r"\bdo\s+kalendarza\s+(.+?)(?=(?:\s*,\s*przypomnij\b|\s*,\s*dla\b|\s+przypomnij\b|\s+dla\b|$))",
                text,
                flags=re.IGNORECASE,
            )
        if not match:
            return None, text

        raw_value = match.group(1).strip(" .")
        normalized_value = raw_value.lower()
        selected = None
        for calendar in calendars:
            display_name = str(calendar.get("display_name") or "").strip()
            kind_label = str(calendar.get("calendar_kind_label") or "").strip()
            kind = str(calendar.get("calendar_kind") or "").strip()
            haystack = " ".join([display_name.lower(), kind_label.lower(), kind.lower()]).strip()
            if normalized_value == display_name.lower() or normalized_value == kind.lower() or normalized_value == kind_label.lower():
                selected = calendar
                break
            if normalized_value in haystack or haystack in normalized_value:
                selected = calendar
                break

        cleaned = (text[: match.start()] + text[match.end() :]).strip(" ,")
        if not selected:
            return None, self._normalize_spaces(cleaned)
        return (
            _MatchedCalendar(
                user_calendar_id=int(selected["user_calendar_id"]),
                display_name=str(selected.get("display_name") or ""),
                calendar_kind=str(selected.get("calendar_kind") or "inne"),
                default_duration_minutes=int(selected.get("default_duration_minutes") or 60),
            ),
            self._normalize_spaces(cleaned),
        )

    def _extract_datetime_and_reminder(
        self,
        text: str,
        *,
        task_type: str,
        calendar: _MatchedCalendar | None,
    ) -> tuple[str | None, str | None, str, list[str]]:
        warnings: list[str] = []
        working_text = text
        base_date = self._extract_date(working_text)

        time_match = re.search(r"\bo\s+(\d{1,2})(?::(\d{2}))?\b", working_text, flags=re.IGNORECASE)
        if not time_match:
            time_match = re.search(r"\b(\d{1,2}):(\d{2})\b", working_text, flags=re.IGNORECASE)
        hour = None
        minute = None
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2) or 0)
            if hour > 23 or minute > 59:
                warnings.append("Rozpoznano nieprawidlowa godzine. Popraw ja w podgladzie.")
                hour = None
                minute = None
        elif task_type == "wydarzenie" and base_date["date"] is not None:
            if re.search(r"\brano\b", working_text, flags=re.IGNORECASE):
                hour, minute = 9, 0
            elif re.search(r"\bwieczorem\b", working_text, flags=re.IGNORECASE):
                hour, minute = 18, 0
            else:
                warnings.append("Nie rozpoznano godziny wpisu. Ustaw ja recznie w formularzu.")

        due_at = None
        remind_at = None
        if base_date["date"] is not None and hour is not None and minute is not None:
            due_dt = datetime.combine(base_date["date"], datetime.min.time()).replace(hour=hour, minute=minute)
            due_at = due_dt.strftime("%Y-%m-%dT%H:%M")
            remind_at = self._default_reminder(due_dt, task_type=task_type, calendar=calendar)
        elif base_date["date"] is not None and task_type == "przypomnienie":
            due_dt = datetime.combine(base_date["date"], datetime.min.time()).replace(hour=9, minute=0)
            due_at = due_dt.strftime("%Y-%m-%dT%H:%M")
            remind_at = due_at
            warnings.append("Dla przypomnienia ustawiono domyslnie godzine 09:00. W razie potrzeby popraw ja przed zapisem.")
        elif task_type == "przypomnienie" and hour is not None and minute is not None:
            due_dt = datetime.now().replace(second=0, microsecond=0, hour=hour, minute=minute)
            if due_dt < datetime.now():
                due_dt += timedelta(days=1)
            due_at = due_dt.strftime("%Y-%m-%dT%H:%M")
            remind_at = due_at
            warnings.append("Nie podano daty, wiec ustawiono najblizszy pasujacy termin.")

        if due_at:
            reminder_offset = timedelta(0)
            reminder_applied = False
            normalized_text = self._normalize_for_matching(text)

            reminder_match = re.search(r"\b(\d{1,3})\s*min(?:ut(?:y|a|e)?|)\s+wczesniej\b", normalized_text)
            if reminder_match:
                minutes = min(max(1, int(reminder_match.group(1))), 1440)
                reminder_offset += timedelta(minutes=minutes)
                reminder_applied = True
            elif re.search(r"\bpol\s+godziny\s+wczesniej\b", normalized_text):
                reminder_offset += timedelta(minutes=30)
                reminder_applied = True

            day_match = re.search(r"\b(\d{1,2}|jeden|jedna|jednego|jednej)\s+dni?\s+wczesniej\b", normalized_text)
            if day_match:
                token = day_match.group(1).lower()
                days = 1 if not token.isdigit() else max(1, int(token))
                reminder_offset += timedelta(days=days)
                reminder_applied = True
            elif re.search(r"\bdzien\s+wczesniej\b", normalized_text):
                reminder_offset += timedelta(days=1)
                reminder_applied = True

            hour_match = re.search(r"\b(?:(\d{1,2}|jeden|jedna|jednego|jednej)\s+)?godzin(?:a|e|y|ę)?\s+wczesniej\b", normalized_text)
            if hour_match:
                token = (hour_match.group(1) or "").lower()
                hours = 1 if not token.isdigit() else max(1, int(token))
                reminder_offset += timedelta(hours=hours)
                reminder_applied = True

            if reminder_applied:
                due_dt = datetime.strptime(due_at, "%Y-%m-%dT%H:%M")
                remind_at = (due_dt - reminder_offset).strftime("%Y-%m-%dT%H:%M")

        return due_at, remind_at, self._normalize_spaces(working_text), warnings
    def _extract_recurrence(self, text: str) -> tuple[dict[str, Any], str]:
        pattern = "brak"
        interval = 1
        weekdays: str | None = None

        normalized = self._normalize_for_matching(text)
        weekday_match = re.search(r"\b(?:w|we)\s+(poniedzialki|poniedzialek|wtorki|srody|czwartki|piatki|soboty|niedziele)\b", normalized)
        if weekday_match:
            token = (
                weekday_match.group(1)
                .lower()
                .replace("poniedzialki", "poniedzialek")
                .replace("srody", "sroda")
                .replace("piatki", "piatek")
                .replace("soboty", "sobota")
                .replace("niedziele", "niedziela")
            )
            if token in self.WEEKDAY_MAP:
                pattern = "co_tydzien"
                weekdays = str(self.WEEKDAY_MAP[token])

        recurring_patterns = [
            (r"\bw\s+dni\s+robocze\b", "dni_robocze"),
            (r"\bcodziennie\b", "codziennie"),
            (r"\bco\s+tydzien\b", "co_tydzien"),
            (r"\bco\s+miesiac\b", "co_miesiac"),
        ]
        for expression, detected_pattern in recurring_patterns:
            match = re.search(expression, normalized)
            if not match:
                continue
            pattern = detected_pattern
            if pattern == "dni_robocze":
                weekdays = "0,1,2,3,4"
            break

        return (
            {
                "pattern": pattern,
                "interval": interval,
                "weekdays": weekdays,
                "label": self._recurrence_label(pattern, interval, weekdays),
            },
            text,
        )

    def _extract_date(self, text: str) -> dict[str, Any]:
        lowered = self._normalize_for_matching(text)
        now = datetime.now()
        current_week_start = (now - timedelta(days=now.weekday())).date()

        week_match = re.search(r"\bza\s+tydzien(?:\s+(?:w|we))?\s+(poniedzialek|wtorek|sroda|czwartek|piatek|sobota|niedziela)\b", lowered)
        if week_match:
            raw_weekday = week_match.group(1).lower()
            target_weekday = self.WEEKDAY_MAP.get(raw_weekday)
            if target_weekday is not None:
                return {"date": current_week_start + timedelta(days=7 + target_weekday), "match": week_match}

        week_days_match = re.search(
            r"\bza\s+(\d+)\s+tygodnie?(?:\s+(?:w|we))?\s+(poniedzialek|wtorek|sroda|czwartek|piatek|sobota|niedziela)\b",
            lowered,
        )
        if week_days_match:
            weeks = max(1, int(week_days_match.group(1)))
            raw_weekday = week_days_match.group(2).lower()
            target_weekday = self.WEEKDAY_MAP.get(raw_weekday)
            if target_weekday is not None:
                return {"date": current_week_start + timedelta(days=(7 * weeks) + target_weekday), "match": week_days_match}

        relative_weeks_match = re.search(r"\bza\s+(\d+)\s+tygodnie?\b", lowered)
        if relative_weeks_match:
            weeks = max(1, int(relative_weeks_match.group(1)))
            return {"date": current_week_start + timedelta(days=7 * weeks), "match": relative_weeks_match}

        next_week_match = re.search(r"\bza\s+tydzien\b", lowered)
        if next_week_match:
            return {"date": (now + timedelta(days=7)).date(), "match": next_week_match}

        relative_days_match = re.search(r"\bza\s+(\d+)\s+dni?\b", lowered)
        if relative_days_match:
            days = max(1, int(relative_days_match.group(1)))
            return {"date": (now + timedelta(days=days)).date(), "match": relative_days_match}

        future_weekday_match = re.search(
            r"\b(?:w|we)\s+(?:przyszly|przyszla|przyszlym|najblizszy|najblizsza|najblizszym)\s+(poniedzialek|wtorek|sroda|czwartek|piatek|sobota|niedziela)\b",
            lowered,
        )
        if future_weekday_match:
            raw_weekday = future_weekday_match.group(1).lower()
            target_weekday = self.WEEKDAY_MAP.get(raw_weekday)
            if target_weekday is not None:
                delta = (target_weekday - now.weekday()) % 7
                if delta == 0:
                    delta = 7
                return {"date": (now + timedelta(days=delta)).date(), "match": future_weekday_match}

        if "pojutrze" in lowered:
            match = re.search(r"\bpojutrze\b", text, flags=re.IGNORECASE)
            return {"date": (now + timedelta(days=2)).date(), "match": match}
        if "jutro" in lowered:
            match = re.search(r"\bjutro\b", text, flags=re.IGNORECASE)
            return {"date": (now + timedelta(days=1)).date(), "match": match}
        if "dzis" in lowered:
            match = re.search(r"\bdzi[śs]?\b", text, flags=re.IGNORECASE)
            return {"date": now.date(), "match": match}

        weekday_match = re.search(
            r"\b(?:w|we)\s+(poniedzialek|wtorek|sroda|czwartek|piatek|sobota|niedziela)\b",
            lowered,
        )
        if weekday_match:
            raw_weekday = weekday_match.group(1).lower()
            target_weekday = self.WEEKDAY_MAP.get(raw_weekday)
            if target_weekday is not None:
                delta = (target_weekday - now.weekday()) % 7
                if delta == 0:
                    delta = 7
                return {"date": (now + timedelta(days=delta)).date(), "match": weekday_match}

        explicit_match = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", text)
        if explicit_match:
            year, month, day = map(int, explicit_match.groups())
            try:
                return {"date": datetime(year, month, day).date(), "match": explicit_match}
            except ValueError:
                return {"date": None, "match": explicit_match}

        named_month_match = re.search(
            r"\b(\d{1,2})\s+(stycznia|lutego|marca|kwietnia|maja|czerwca|lipca|sierpnia|wrzesnia|pa[źz]dziernika|listopada|grudnia)(?:\s+(\d{4}))?\b",
            lowered,
        )
        if named_month_match:
            month_names = {
                "stycznia": 1,
                "lutego": 2,
                "marca": 3,
                "kwietnia": 4,
                "maja": 5,
                "czerwca": 6,
                "lipca": 7,
                "sierpnia": 8,
                "wrzesnia": 9,
                "pazdziernika": 10,
                "października": 10,
                "listopada": 11,
                "grudnia": 12,
            }
            day = int(named_month_match.group(1))
            month = month_names.get(named_month_match.group(2).replace("ź", "z"), 0)
            year = int(named_month_match.group(3) or now.year)
            try:
                candidate = datetime(year, month, day).date()
                if named_month_match.group(3) is None and candidate < now.date():
                    candidate = datetime(year + 1, month, day).date()
                return {"date": candidate, "match": named_month_match}
            except ValueError:
                return {"date": None, "match": named_month_match}

        day_month_match = re.search(r"\b(\d{1,2})[./](\d{1,2})(?:[./](\d{2,4}))?\b", lowered)
        if day_month_match:
            day = int(day_month_match.group(1))
            month = int(day_month_match.group(2))
            year_token = day_month_match.group(3)
            year = now.year if year_token is None else int(year_token)
            if year_token is not None and year < 100:
                year += 2000
            try:
                candidate = datetime(year, month, day).date()
                if year_token is None and candidate < now.date():
                    candidate = datetime(year + 1, month, day).date()
                return {"date": candidate, "match": day_month_match}
            except ValueError:
                return {"date": None, "match": day_month_match}

        return {"date": None, "match": None}
    def _default_reminder(
        self,
        due_dt: datetime,
        *,
        task_type: str,
        calendar: _MatchedCalendar | None,
    ) -> str:
        if task_type == "przypomnienie":
            return due_dt.strftime("%Y-%m-%dT%H:%M")
        offset = timedelta(minutes=30 if task_type == "wydarzenie" or calendar else 15)
        return (due_dt - offset).strftime("%Y-%m-%dT%H:%M")

    def _build_title_with_fallback(
        self,
        original_text: str,
        working_text: str,
        task_type: str,
        *,
        due_at: str | None,
        remind_at: str | None,
        warnings: list[str],
    ) -> tuple[str, dict[str, Any]]:
        primary_title = self._build_title(working_text, task_type)
        fallback_title = self._fallback_title_candidate(original_text, working_text, task_type, primary_title)
        primary_score = self._score_title_candidate(primary_title)
        fallback_score = self._score_title_candidate(fallback_title)

        title = primary_title
        used_fallback = False
        reason: str | None = None
        if fallback_title and fallback_score > primary_score + 1.25:
            title = fallback_title
            used_fallback = True
            reason = "Zastosowano ostrożny fallback tytulu."
        elif fallback_title and self._title_needs_review(primary_title) and fallback_score >= primary_score - 3.5:
            title = fallback_title
            used_fallback = True
            reason = "Zastosowano bezpieczniejszy wariant tytulu z fallbacku."

        confidence = 1.0
        confidence -= min(len(warnings) * 0.08, 0.24)
        if due_at is None:
            confidence -= 0.18
        if remind_at is None:
            confidence -= 0.05
        if used_fallback:
            confidence -= 0.06
        if self._title_needs_review(title):
            confidence -= 0.14
        if len(self._normalize_for_matching(title).split()) <= 2:
            confidence -= 0.05
        confidence = max(0.0, min(1.0, confidence))
        review_threshold = self.TITLE_REVIEW_THRESHOLD

        fallback = {
            "used": used_fallback,
            "reason": reason,
            "needs_review": confidence < review_threshold,
            "confidence": round(confidence, 2),
            "threshold": review_threshold,
            "primary_title": primary_title,
            "fallback_title": fallback_title if fallback_title != primary_title else None,
        }
        if fallback["needs_review"] and not fallback["reason"]:
            fallback["reason"] = "Tak to zrozumialem, ale mozesz to dopracowac przed zapisem."
        return title, fallback

    def _build_title(self, text: str, task_type: str) -> str:
        cleaned = self._clean_title_candidate(text)
        if not cleaned:
            return ""
        if task_type == "wydarzenie" and not cleaned.lower().startswith("spotkanie"):
            if any(keyword in cleaned.lower() for keyword in ("rozmowa", "prezentacja", "warsztat", "wyjazd")):
                return cleaned[:1].upper() + cleaned[1:]
        return cleaned[:1].upper() + cleaned[1:]

    def _clean_title_candidate(self, value: str) -> str:
        cleaned = self._strip_task_noise(value)
        cleaned = self._normalize_spaces(re.sub(r"\s+", " ", cleaned).strip(" ,.-"))
        cleaned = re.sub(r"^(?:i|oraz|to|bedzie|będzie|ma|ma\s+byc|ma\s+być|o|na|w|we)\s+", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+(?:i|oraz|to|bedzie|będzie|ma|ma\s+byc|ma\s+być|o|na|w|we)$", "", cleaned, flags=re.IGNORECASE)
        return self._normalize_spaces(cleaned)

    def _title_needs_review(self, title: str) -> bool:
        normalized = self._normalize_for_matching(title)
        if not normalized:
            return True
        review_tokens = {
            "przypomnij",
            "przypomnienie",
            "potrwa",
            "trwa",
            "wczesniej",
            "wcześniej",
            "rano",
            "wieczorem",
            "jutro",
            "pojutrze",
            "dzis",
            "dzisiaj",
        }
        tokens = normalized.split()
        if any(token in review_tokens for token in tokens):
            return True
        return "i" in tokens and len(tokens) > 3

    def _score_title_candidate(self, candidate: str) -> float:
        normalized = self._normalize_for_matching(candidate)
        if not normalized:
            return -100.0
        tokens = normalized.split()
        noise_tokens = {
            "przypomnij",
            "przypomnienie",
            "potrwa",
            "trwa",
            "wczesniej",
            "wcześniej",
            "jutro",
            "pojutrze",
            "dzis",
            "dzisiaj",
            "rano",
            "wieczorem",
            "na",
            "o",
            "w",
            "we",
            "i",
            "oraz",
            "to",
            "bedzie",
            "będzie",
            "ma",
            "byc",
            "być",
            "za",
        }
        content_words = sum(1 for token in tokens if token not in noise_tokens and not token.isdigit())
        noise_words = sum(1 for token in tokens if token in noise_tokens)
        alpha_chars = sum(1 for char in candidate if char.isalpha())
        long_penalty = max(0, len(tokens) - 8) * 0.4
        conjunction_penalty = 2.5 if "i" in tokens and len(tokens) > 3 else 0.0
        leading_preposition_penalty = 1.0 if tokens and tokens[0] in {"o", "na", "w", "we", "do", "za"} else 0.0
        return (content_words * 3.0) + min(alpha_chars / 12.0, 8.0) - (noise_words * 2.25) - long_penalty - conjunction_penalty - leading_preposition_penalty

    def _fallback_title_candidate(self, original_text: str, working_text: str, task_type: str, primary_title: str) -> str:
        candidates = [primary_title, self._clean_title_candidate(working_text), self._clean_title_candidate(original_text)]
        split_candidates: list[str] = []
        leading_split_candidate: str = ""
        leading_split_score = -100.0
        splitters = [
            r"\s+(?:i|oraz|ale|bo)\s+",
            r"[,.;:]+",
            r"\s+-\s+",
        ]

        for seed in list(candidates):
            if not seed:
                continue
            for splitter in splitters:
                parts = [part.strip() for part in re.split(splitter, seed, maxsplit=1, flags=re.IGNORECASE) if part.strip()]
                candidates.extend(parts)
                if len(parts) > 1:
                    split_candidates.extend(parts)
                    if splitter == r"\s+(?:i|oraz|ale|bo)\s+":
                        leading_candidate = self._clean_title_candidate(parts[0])
                        if leading_candidate:
                            leading_score = self._score_title_candidate(leading_candidate)
                            if leading_score > leading_split_score:
                                leading_split_candidate = leading_candidate
                                leading_split_score = leading_score

        if task_type == "wydarzenie":
            candidates.append("Spotkanie " + primary_title if primary_title else "")

        best_candidate = primary_title
        best_score = self._score_title_candidate(primary_title)
        best_split_candidate = ""
        best_split_score = -100.0
        for candidate in candidates:
            cleaned = self._clean_title_candidate(candidate)
            if not cleaned:
                continue
            score = self._score_title_candidate(cleaned)
            if cleaned in split_candidates and score > best_split_score:
                best_split_candidate = cleaned
                best_split_score = score
            if score > best_score:
                best_candidate = cleaned
                best_score = score

        if self._title_needs_review(primary_title) and leading_split_candidate and leading_split_score >= best_score - 4.0:
            return leading_split_candidate
        if self._title_needs_review(primary_title) and best_split_candidate and best_split_score >= best_score - 3.5:
            return best_split_candidate
        return best_candidate

    def _build_description(self, original_text: str, title: str) -> str | None:
        normalized_original = self._normalize_spaces(original_text)
        if normalized_original.lower() == title.lower():
            return None
        return f"Utworzone z polecenia tekstowego: {normalized_original}"

    def _remove_span(self, text: str, span: tuple[int, int]) -> str:
        return self._normalize_spaces((text[: span[0]] + text[span[1] :]).strip(" ,"))

    def _task_type_label(self, task_type: str) -> str:
        return {
            "zadanie": "Zadanie",
            "wydarzenie": "Wydarzenie",
            "przypomnienie": "Przypomnienie",
            "notatka": "Notatka",
        }.get(task_type, task_type)

    def _priority_label(self, priority: str) -> str:
        return {
            "niski": "Niski",
            "normalny": "Normalny",
            "wysoki": "Wysoki",
            "krytyczny": "Krytyczny",
        }.get(priority, priority)

    def _visibility_label(self, visibility_scope: str) -> str:
        return {
            "prywatne": "Prywatne",
            "wybrane_osoby": "Wybrane osoby",
            "organizacja": "Cala organizacja",
        }.get(visibility_scope, visibility_scope)

    def _recurrence_label(self, pattern: str, interval: int, weekdays: str | None = None) -> str:
        if pattern == "codziennie":
            return "Codziennie" if interval == 1 else f"Co {interval} dni"
        if pattern == "co_tydzien":
            if weekdays and weekdays.isdigit():
                weekday_labels = {
                    "0": "Co tydzien w poniedzialki",
                    "1": "Co tydzien we wtorki",
                    "2": "Co tydzien w srody",
                    "3": "Co tydzien w czwartki",
                    "4": "Co tydzien w piatki",
                    "5": "Co tydzien w soboty",
                    "6": "Co tydzien w niedziele",
                }
                return weekday_labels.get(weekdays, "Co tydzien")
            return "Co tydzien" if interval == 1 else f"Co {interval} tygodnie"
        if pattern == "dni_robocze":
            return "W dni robocze"
        if pattern == "co_miesiac":
            return "Co miesiac" if interval == 1 else f"Co {interval} miesiace"
        return "Brak cyklicznosci"

