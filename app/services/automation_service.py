from __future__ import annotations

import json
import re
from typing import Any
from uuid import uuid4

from app.repositories.automation_repository import AutomationRepository
from app.repositories.event_repository import EventRepository
from app.services.intake_service import IntakeService
from app.utils import json_dumps, now_iso


class AutomationService:
    def __init__(
        self,
        automation_repository: AutomationRepository,
        event_repository: EventRepository,
        intake_service: IntakeService | None = None,
    ) -> None:
        self.automation_repository = automation_repository
        self.event_repository = event_repository
        self.intake_service = intake_service

    def list_rules(self, organization_id: int | None = None, *, include_inactive: bool = False) -> list[dict[str, Any]]:
        return self.automation_repository.list_rules(organization_id=organization_id, include_inactive=include_inactive)

    def list_executions(
        self,
        *,
        organization_id: int | None = None,
        automation_rule_id: int | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        return self.automation_repository.list_executions(
            organization_id=organization_id,
            automation_rule_id=automation_rule_id,
            limit=limit,
        )

    def create_rule(
        self,
        payload: dict[str, Any],
        *,
        actor_user: dict[str, Any],
        actor: str,
        organization_id: int | None,
    ) -> dict[str, Any]:
        if organization_id is None:
            raise ValueError("Wybierz organizacje przed dodaniem automatyzacji.")
        rule_name = self._normalize_required_text(payload.get("rule_name"), "Nazwa reguły")
        rule_slug = self._normalize_slug(payload.get("rule_slug") or rule_name)
        if self.automation_repository.get_by_slug(organization_id, rule_slug):
            raise ValueError("Reguła automatyzacji o tym identyfikatorze juz istnieje.")

        trigger_event_type = self._normalize_required_text(payload.get("trigger_event_type"), "Zdarzenie wyzwalające")
        conditions_json = self._normalize_json_text(payload.get("conditions_json") or {})
        actions_json = self._normalize_actions(payload.get("actions_json") or payload.get("actions") or [])
        rule_id = self.automation_repository.create(
            {
                "organization_id": organization_id,
                "rule_slug": rule_slug,
                "rule_name": rule_name,
                "description": self._normalize_optional_text(payload.get("description")),
                "trigger_event_type": trigger_event_type,
                "conditions_json": conditions_json,
                "actions_json": actions_json,
                "is_active": 1 if payload.get("is_active", True) not in {False, 0, "0", "false"} else 0,
                "created_by_user_id": int(actor_user["user_id"]),
            }
        )
        created = self.automation_repository.get_by_id(rule_id, organization_id=organization_id)
        assert created is not None
        self.event_repository.log(
            event_type="automation_rule_created",
            invoice_id=None,
            organization_id=organization_id,
            source="AUTOMATION",
            status_before=None,
            status_after="aktywny" if created.get("is_active") else "nieaktywny",
            decision_reason=f"Dodano regułę {created['rule_name']}.",
            actor=actor,
            details={
                "automation_rule_id": rule_id,
                "rule_slug": created["rule_slug"],
                "trigger_event_type": created["trigger_event_type"],
                "created_by_user_id": actor_user.get("user_id"),
            },
        )
        return self._decorate_rule(created)

    def update_rule(
        self,
        automation_rule_id: int,
        payload: dict[str, Any],
        *,
        actor_user: dict[str, Any],
        actor: str,
        organization_id: int | None,
    ) -> dict[str, Any] | None:
        current = self.automation_repository.get_by_id(automation_rule_id, organization_id=organization_id)
        if not current:
            return None

        updates: dict[str, Any] = {}
        if "rule_name" in payload:
            updates["rule_name"] = self._normalize_required_text(payload.get("rule_name"), "Nazwa reguły")
        if "rule_slug" in payload:
            updates["rule_slug"] = self._normalize_slug(payload.get("rule_slug"))
        if "description" in payload:
            updates["description"] = self._normalize_optional_text(payload.get("description"))
        if "trigger_event_type" in payload:
            updates["trigger_event_type"] = self._normalize_required_text(payload.get("trigger_event_type"), "Zdarzenie wyzwalające")
        if "conditions_json" in payload:
            updates["conditions_json"] = self._normalize_json_text(payload.get("conditions_json") or {})
        if "actions_json" in payload or "actions" in payload:
            updates["actions_json"] = self._normalize_actions(payload.get("actions_json") or payload.get("actions") or [])
        if "is_active" in payload:
            updates["is_active"] = 1 if payload.get("is_active") not in {False, 0, "0", "false"} else 0
        if updates:
            self.automation_repository.update(automation_rule_id, updates)
            refreshed = self.automation_repository.get_by_id(automation_rule_id, organization_id=organization_id)
            assert refreshed is not None
            self.event_repository.log(
                event_type="automation_rule_updated",
                invoice_id=None,
                organization_id=organization_id,
                source="AUTOMATION",
                status_before="aktywny" if current.get("is_active") else "nieaktywny",
                status_after="aktywny" if refreshed.get("is_active") else "nieaktywny",
                decision_reason=f"Zmieniono regułę {refreshed['rule_name']}.",
                actor=actor,
                details={"automation_rule_id": automation_rule_id, "updated_fields": sorted(updates.keys())},
            )
            return self._decorate_rule(refreshed)
        return self._decorate_rule(current)

    def run_rule(
        self,
        automation_rule_id: int,
        *,
        actor_user: dict[str, Any],
        actor: str,
        organization_id: int | None,
    ) -> dict[str, Any] | None:
        rule = self.automation_repository.get_by_id(automation_rule_id, organization_id=organization_id)
        if not rule:
            return None
        return self._process_rule(rule, manual=True, actor_user=actor_user, actor=actor)

    def delete_rule(self, automation_rule_id: int, *, organization_id: int | None, actor: str) -> dict[str, Any] | None:
        rule = self.automation_repository.get_by_id(automation_rule_id, organization_id=organization_id)
        if not rule:
            return None
        self.automation_repository.update(
            automation_rule_id,
            {
                "is_active": 0,
                "last_result": "Wyłączono ręcznie w panelu.",
            },
        )
        refreshed = self.automation_repository.get_by_id(automation_rule_id, organization_id=organization_id)
        assert refreshed is not None
        self.event_repository.log(
            event_type="automation_rule_disabled",
            invoice_id=None,
            organization_id=int(refreshed["organization_id"]),
            source="AUTOMATION",
            status_before="aktywny" if rule.get("is_active") else "nieaktywny",
            status_after="nieaktywny",
            decision_reason=f"Wyłączono regułę {refreshed['rule_name']}.",
            actor=actor,
            details={"automation_rule_id": automation_rule_id},
        )
        return self._decorate_rule(refreshed)

    def process_pending_events(self, *, organization_id: int | None = None, limit: int = 200) -> dict[str, Any]:
        rules = self.automation_repository.list_rules(organization_id=organization_id)
        if not rules:
            return {"processed_rules": 0, "executions": 0, "errors": 0}

        processed_rules = 0
        executions = 0
        errors = 0
        for rule in rules:
            result = self._process_rule(rule, limit=limit)
            if result["processed"]:
                processed_rules += 1
            executions += int(result["executions"])
            errors += int(result["errors"])
        return {"processed_rules": processed_rules, "executions": executions, "errors": errors}

    def _process_rule(
        self,
        rule: dict[str, Any],
        *,
        manual: bool = False,
        actor_user: dict[str, Any] | None = None,
        actor: str = "automation",
        limit: int = 200,
    ) -> dict[str, Any]:
        rule_id = int(rule["automation_rule_id"])
        organization_id = int(rule["organization_id"])
        last_cursor = int(rule.get("last_processed_event_log_id") or 0)
        events = self.event_repository.list_logs_after(last_cursor, organization_id=organization_id, limit=limit)
        if not events:
            if manual:
                self.automation_repository.update(
                    rule_id,
                    {
                        "last_run_at": now_iso(),
                        "last_result": "Brak nowych zdarzen do przetworzenia.",
                    },
                )
            return {"processed": False, "executions": 0, "errors": 0}

        matches = 0
        errors = 0
        latest_event_id = last_cursor
        for event in events:
            latest_event_id = max(latest_event_id, int(event.get("id") or 0))
            if str(event.get("event_type") or "") != str(rule.get("trigger_event_type") or ""):
                continue
            if str(event.get("source") or "").strip().upper() == "AUTOMATION":
                continue
            if not self._event_matches_conditions(event, rule):
                continue

            try:
                execution_result = self._execute_actions(rule, event, actor_user=actor_user, actor=actor)
                matches += 1
                self.automation_repository.create_execution(
                    {
                        "automation_rule_id": rule_id,
                        "organization_id": organization_id,
                        "event_log_id": event.get("id"),
                        "trigger_event_type": str(rule.get("trigger_event_type") or ""),
                        "execution_status": "success",
                        "input_json": json_dumps(event),
                        "result_json": json_dumps(execution_result),
                    }
                )
            except Exception as error:
                errors += 1
                self.automation_repository.create_execution(
                    {
                        "automation_rule_id": rule_id,
                        "organization_id": organization_id,
                        "event_log_id": event.get("id"),
                        "trigger_event_type": str(rule.get("trigger_event_type") or ""),
                        "execution_status": "failed",
                        "input_json": json_dumps(event),
                        "error_message": str(error),
                    }
                )
                self.event_repository.log(
                    event_type="automation_rule_failed",
                    invoice_id=None,
                    organization_id=organization_id,
                    source="AUTOMATION",
                    status_before=None,
                    status_after=None,
                    decision_reason=str(error),
                    actor=actor,
                    details={"automation_rule_id": rule_id, "event_log_id": event.get("id")},
                )
        self.automation_repository.update(
            rule_id,
            {
                "last_processed_event_log_id": latest_event_id,
                "last_run_at": now_iso(),
                "last_result": f"Przetworzono {matches} zdarzen, bledow: {errors}.",
                "execution_count": int(rule.get("execution_count") or 0) + matches + errors,
            },
        )
        return {"processed": True, "executions": matches, "errors": errors}

    def _execute_actions(
        self,
        rule: dict[str, Any],
        event: dict[str, Any],
        *,
        actor_user: dict[str, Any] | None,
        actor: str,
    ) -> dict[str, Any]:
        actions_raw = rule.get("actions_json") or "[]"
        actions = json.loads(actions_raw) if isinstance(actions_raw, str) else actions_raw
        if not isinstance(actions, list):
            raise ValueError("Lista akcji musi byc tablica JSON.")

        results: list[dict[str, Any]] = []
        for action in actions:
            if not isinstance(action, dict):
                continue
            action_type = str(action.get("type") or "").strip().lower()
            if action_type == "create_inbox_item":
                if not self.intake_service:
                    raise ValueError("Modul skrzynki spraw nie jest dostepny.")
                created = self.intake_service.create_item(
                    {
                        "title": action.get("title") or event.get("decision_reason") or str(event.get("event_type") or ""),
                        "description": action.get("description") or self._event_excerpt(event),
                        "priority": action.get("priority") or "normalny",
                        "requester_name": action.get("requester_name"),
                        "requester_email": action.get("requester_email"),
                        "source_reference": action.get("source_reference") or str(event.get("id") or ""),
                        "metadata_json": {
                            "rule_id": rule.get("automation_rule_id"),
                            "rule_slug": rule.get("rule_slug"),
                            "trigger_event_id": event.get("id"),
                            "trigger_event_type": event.get("event_type"),
                        },
                        "source_kind": "automation",
                    },
                    actor_user=actor_user,
                    actor=actor,
                    organization_id=int(rule["organization_id"]),
                )
                results.append({"type": action_type, "created_intake_item_id": created["intake_item_id"]})
            elif action_type == "log":
                results.append({"type": action_type, "message": str(action.get("message") or "")})
            else:
                raise ValueError(f"Nieznany typ akcji automatyzacji: {action_type}")

        self.event_repository.log(
            event_type="automation_rule_executed",
            invoice_id=None,
            organization_id=int(rule["organization_id"]),
            source="AUTOMATION",
            status_before=None,
            status_after=None,
            decision_reason=str(rule.get("rule_name") or ""),
            actor=actor,
            details={
                "automation_rule_id": rule.get("automation_rule_id"),
                "trigger_event_id": event.get("id"),
                "results": results,
            },
        )
        return {"results": results}

    def _event_matches_conditions(self, event: dict[str, Any], rule: dict[str, Any]) -> bool:
        raw_conditions = rule.get("conditions_json") or "{}"
        conditions = json.loads(raw_conditions) if isinstance(raw_conditions, str) else raw_conditions
        if not isinstance(conditions, dict):
            return True

        source = conditions.get("source")
        if source and str(event.get("source") or "").strip().lower() != str(source).strip().lower():
            return False

        status_after = conditions.get("status_after")
        if status_after and str(event.get("status_after") or "").strip().lower() != str(status_after).strip().lower():
            return False

        status_before = conditions.get("status_before")
        if status_before and str(event.get("status_before") or "").strip().lower() != str(status_before).strip().lower():
            return False

        decision_contains = conditions.get("decision_reason_contains")
        if decision_contains and str(decision_contains).strip().lower() not in str(event.get("decision_reason") or "").lower():
            return False

        details_contains = conditions.get("details_contains")
        if details_contains and str(details_contains).strip().lower() not in str(event.get("details") or "").lower():
            return False

        return True

    def _decorate_rule(self, rule: dict[str, Any]) -> dict[str, Any]:
        result = dict(rule)
        for key in ("conditions_json", "actions_json"):
            raw = result.get(key)
            if isinstance(raw, str) and raw.strip():
                try:
                    result[key] = json.loads(raw)
                except json.JSONDecodeError:
                    result[key] = raw
        return result

    def _event_excerpt(self, event: dict[str, Any]) -> str:
        details = str(event.get("details") or "").strip()
        if not details:
            return str(event.get("decision_reason") or event.get("event_type") or "Zdarzenie automatyzacji")
        return details[:400]

    def _normalize_required_text(self, value: Any, field_label: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError(f"{field_label} jest wymagana.")
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized

    def _normalize_optional_text(self, value: Any) -> str | None:
        normalized = str(value or "").strip()
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized or None

    def _normalize_slug(self, value: Any) -> str:
        normalized = self._normalize_required_text(value, "Identyfikator")
        normalized = normalized.lower()
        normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
        normalized = re.sub(r"-+", "-", normalized).strip("-")
        if not normalized:
            raise ValueError("Identyfikator reguly jest nieprawidlowy.")
        return normalized

    def _normalize_json_text(self, value: Any) -> str:
        if isinstance(value, str):
            candidate = value.strip()
            if not candidate:
                return "{}"
            try:
                parsed = json.loads(candidate)
            except json.JSONDecodeError as error:
                raise ValueError("Nieprawidlowy format danych JSON.") from error
            return json_dumps(parsed)
        return json_dumps(value if value is not None else {})

    def _normalize_actions(self, value: Any) -> str:
        if isinstance(value, str):
            candidate = value.strip()
            if not candidate:
                return "[]"
            try:
                parsed = json.loads(candidate)
            except json.JSONDecodeError as error:
                raise ValueError("Nieprawidlowy format akcji automatyzacji.") from error
            if not isinstance(parsed, list):
                raise ValueError("Akcje automatyzacji musza byc tablica JSON.")
            return json_dumps(parsed)
        if not isinstance(value, list):
            raise ValueError("Akcje automatyzacji musza byc tablica JSON.")
        return json_dumps(value)
