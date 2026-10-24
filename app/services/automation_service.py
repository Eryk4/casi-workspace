from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Callable
from uuid import uuid4

from app.repositories.automation_repository import AutomationRepository
from app.repositories.event_repository import EventRepository
from app.services.automation_public_projection import (
    project_public_automation_execution,
    project_public_automation_rule,
)
from app.services.automation_rule_definition import (
    AutomationRuleValidationError,
    get_condition_definition,
    get_execution_action_definition,
    normalize_active_flag,
    validate_execution_rule_definition,
    validate_management_rule_definition,
    validate_rule_metadata,
    validate_rule_payload_keys,
)
from app.services.intake_service import IntakeService
from app.utils import json_dumps


AUTOMATION_RULE_LEASE_SECONDS = 60


class AutomationRuleBusyError(ValueError):
    code = "automation_rule_busy"
    safe_message = "Reguła automatyzacji jest obecnie przetwarzana."

    def __init__(self) -> None:
        super().__init__(self.safe_message)

    def as_response(self) -> dict[str, str]:
        return {"error": self.safe_message, "code": self.code}


class AutomationService:
    def __init__(
        self,
        automation_repository: AutomationRepository,
        event_repository: EventRepository,
        intake_service: IntakeService | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.automation_repository = automation_repository
        self.event_repository = event_repository
        self.intake_service = intake_service
        self._clock = clock or (lambda: datetime.now(timezone.utc))

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

    def list_public_rules(
        self,
        organization_id: int | None = None,
        *,
        include_inactive: bool = False,
    ) -> list[dict[str, Any]]:
        return [
            project_public_automation_rule(rule)
            for rule in self.list_rules(organization_id=organization_id, include_inactive=include_inactive)
        ]

    def list_public_executions(
        self,
        *,
        organization_id: int | None = None,
        automation_rule_id: int | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        return [
            project_public_automation_execution(execution)
            for execution in self.list_executions(
                organization_id=organization_id,
                automation_rule_id=automation_rule_id,
                limit=limit,
            )
        ]

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
        validate_rule_payload_keys(payload, partial=False)
        metadata = validate_rule_metadata(payload, partial=False)
        definition = validate_management_rule_definition(
            payload.get("trigger_event_type"),
            payload.get("conditions_json", {}),
            payload.get("actions_json") if "actions_json" in payload else payload.get("actions", []),
        )
        rule_name = self._normalize_required_text(metadata.get("rule_name"), "Nazwa reguły")
        rule_slug = self._normalize_slug(payload.get("rule_slug") or rule_name)
        validate_rule_metadata({"rule_slug": rule_slug}, partial=True)
        if self.automation_repository.get_by_slug(organization_id, rule_slug):
            raise ValueError("Reguła automatyzacji o tym identyfikatorze juz istnieje.")

        rule_id = self.automation_repository.create(
            {
                "organization_id": organization_id,
                "rule_slug": rule_slug,
                "rule_name": rule_name,
                "description": metadata.get("description"),
                "trigger_event_type": definition.trigger_event_type,
                "conditions_json": json_dumps(definition.conditions),
                "actions_json": json_dumps(definition.actions),
                "is_active": normalize_active_flag(payload.get("is_active", True)),
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
        return project_public_automation_rule(created)

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

        validate_rule_payload_keys(payload, partial=True)
        metadata = validate_rule_metadata(payload, partial=True)
        updates: dict[str, Any] = {}
        if "rule_name" in payload:
            updates["rule_name"] = self._normalize_required_text(metadata.get("rule_name"), "Nazwa reguły")
        if "rule_slug" in payload:
            updates["rule_slug"] = self._normalize_slug(metadata.get("rule_slug"))
        if "description" in payload:
            updates["description"] = metadata.get("description")

        config_fields = {"trigger_event_type", "conditions_json", "actions_json", "actions"}
        changes_config = bool(config_fields.intersection(payload))
        resulting_trigger = payload.get("trigger_event_type", current.get("trigger_event_type"))
        resulting_conditions = payload.get("conditions_json", current.get("conditions_json"))
        resulting_actions = (
            payload.get("actions_json")
            if "actions_json" in payload
            else payload.get("actions")
            if "actions" in payload
            else current.get("actions_json")
        )
        if changes_config:
            definition = validate_management_rule_definition(
                resulting_trigger,
                resulting_conditions,
                resulting_actions,
            )
            if "trigger_event_type" in payload:
                updates["trigger_event_type"] = definition.trigger_event_type
            if "conditions_json" in payload:
                updates["conditions_json"] = json_dumps(definition.conditions)
            if "actions_json" in payload or "actions" in payload:
                updates["actions_json"] = json_dumps(definition.actions)

        if "is_active" in payload:
            updates["is_active"] = normalize_active_flag(payload.get("is_active"))
            if not int(current.get("is_active") or 0) and updates["is_active"] and not changes_config:
                validate_execution_rule_definition(
                    current.get("trigger_event_type"),
                    current.get("conditions_json"),
                    current.get("actions_json"),
                )
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
            return project_public_automation_rule(refreshed)
        return project_public_automation_rule(current)

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
        return project_public_automation_rule(refreshed)

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
        claim_token = uuid4().hex
        claimed_at, lease_until = self._lease_window()
        acquired = self.automation_repository.acquire_rule_claim(
            automation_rule_id=rule_id,
            organization_id=organization_id,
            claim_token=claim_token,
            claimed_at=claimed_at,
            lease_until=lease_until,
        )
        if not acquired:
            if manual:
                raise AutomationRuleBusyError()
            return {"processed": False, "executions": 0, "errors": 0}

        try:
            try:
                definition = validate_execution_rule_definition(
                    rule.get("trigger_event_type"),
                    rule.get("conditions_json"),
                    rule.get("actions_json"),
                )
            except AutomationRuleValidationError:
                if manual:
                    raise
                return {"processed": False, "executions": 0, "errors": 1}

            last_cursor = int(rule.get("last_processed_event_log_id") or 0)
            events = self.event_repository.list_logs_after(last_cursor, organization_id=organization_id, limit=limit)
            if not events:
                if manual:
                    progress_at, renewed_until = self._lease_window()
                    if self.automation_repository.renew_rule_claim(
                        automation_rule_id=rule_id,
                        organization_id=organization_id,
                        claim_token=claim_token,
                        now=progress_at,
                        lease_until=renewed_until,
                    ):
                        self.automation_repository.update_rule_progress(
                            automation_rule_id=rule_id,
                            organization_id=organization_id,
                            claim_token=claim_token,
                            now=progress_at,
                            last_processed_event_log_id=last_cursor,
                            last_run_at=progress_at,
                            last_result="Brak nowych zdarzen do przetworzenia.",
                            execution_count_increment=0,
                        )
                return {"processed": False, "executions": 0, "errors": 0}

            matches = 0
            errors = 0
            latest_event_id = last_cursor
            lease_lost = False
            for event in events:
                checkpoint_at, renewed_until = self._lease_window()
                if not self.automation_repository.renew_rule_claim(
                    automation_rule_id=rule_id,
                    organization_id=organization_id,
                    claim_token=claim_token,
                    now=checkpoint_at,
                    lease_until=renewed_until,
                ):
                    lease_lost = True
                    break

                latest_event_id = max(latest_event_id, int(event.get("id") or 0))
                if str(event.get("event_type") or "") != str(rule.get("trigger_event_type") or ""):
                    continue
                if str(event.get("source") or "").strip().upper() == "AUTOMATION":
                    continue
                if not self._event_matches_conditions(event, definition.conditions):
                    continue

                execution_claim = self.automation_repository.try_claim_execution(
                    {
                        "automation_rule_id": rule_id,
                        "organization_id": organization_id,
                        "event_log_id": event.get("id"),
                        "trigger_event_type": definition.trigger_event_type,
                        "input_json": json_dumps(event),
                        "executed_at": checkpoint_at,
                    }
                )
                if not execution_claim["claimed"]:
                    continue
                execution_id = int(execution_claim["automation_execution_id"])

                try:
                    execution_result = self._execute_actions(
                        rule,
                        event,
                        definition.actions,
                        actor_user=actor_user,
                        actor=actor,
                    )
                except Exception as error:
                    completed = self.automation_repository.complete_execution(
                        execution_id,
                        execution_status="failed",
                        error_message=str(error),
                        executed_at=self._now_iso(),
                    )
                    if completed:
                        errors += 1
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
                    continue

                completed = self.automation_repository.complete_execution(
                    execution_id,
                    execution_status="success",
                    result_json=json_dumps(execution_result),
                    executed_at=self._now_iso(),
                )
                if not completed:
                    continue
                matches += 1
                self.event_repository.log(
                    event_type="automation_rule_executed",
                    invoice_id=None,
                    organization_id=organization_id,
                    source="AUTOMATION",
                    status_before=None,
                    status_after=None,
                    decision_reason=str(rule.get("rule_name") or ""),
                    actor=actor,
                    details={
                        "automation_rule_id": rule_id,
                        "trigger_event_id": event.get("id"),
                        "results": execution_result["results"],
                    },
                )

            if not lease_lost:
                progress_at, renewed_until = self._lease_window()
                renewed = self.automation_repository.renew_rule_claim(
                    automation_rule_id=rule_id,
                    organization_id=organization_id,
                    claim_token=claim_token,
                    now=progress_at,
                    lease_until=renewed_until,
                )
                if renewed:
                    self.automation_repository.update_rule_progress(
                        automation_rule_id=rule_id,
                        organization_id=organization_id,
                        claim_token=claim_token,
                        now=progress_at,
                        last_processed_event_log_id=latest_event_id,
                        last_run_at=progress_at,
                        last_result=f"Przetworzono {matches} zdarzen, bledow: {errors}.",
                        execution_count_increment=matches + errors,
                    )
            return {"processed": True, "executions": matches, "errors": errors}
        finally:
            self.automation_repository.release_rule_claim(
                automation_rule_id=rule_id,
                organization_id=organization_id,
                claim_token=claim_token,
            )

    def _execute_actions(
        self,
        rule: dict[str, Any],
        event: dict[str, Any],
        actions: list[dict[str, str]],
        *,
        actor_user: dict[str, Any] | None,
        actor: str,
    ) -> dict[str, Any]:
        results: list[dict[str, Any]] = []
        for action in actions:
            action_definition = get_execution_action_definition(action["type"])
            executor = getattr(self, f"_execute_{action_definition.executor}_action")
            results.append(
                executor(
                    action,
                    rule=rule,
                    event=event,
                    actor_user=actor_user,
                    actor=actor,
                )
            )

        return {"results": results}

    def _now_iso(self) -> str:
        current = self._clock()
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
        return current.astimezone(timezone.utc).replace(microsecond=0).isoformat()

    def _lease_window(self) -> tuple[str, str]:
        current = self._clock()
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
        current = current.astimezone(timezone.utc).replace(microsecond=0)
        return current.isoformat(), (current + timedelta(seconds=AUTOMATION_RULE_LEASE_SECONDS)).isoformat()

    def _event_matches_conditions(self, event: dict[str, Any], conditions: dict[str, str]) -> bool:
        for key, expected in conditions.items():
            definition = get_condition_definition(key)
            actual = str(event.get(definition.event_field) or "").strip().lower()
            normalized_expected = expected.strip().lower()
            if definition.operator == "equals" and actual != normalized_expected:
                return False
            if definition.operator == "contains" and normalized_expected not in actual:
                return False
        return True

    def _execute_create_inbox_item_action(
        self,
        action: dict[str, str],
        *,
        rule: dict[str, Any],
        event: dict[str, Any],
        actor_user: dict[str, Any] | None,
        actor: str,
    ) -> dict[str, Any]:
        if not self.intake_service:
            raise ValueError("Modul skrzynki spraw nie jest dostepny.")
        title = action["title"] if "title" in action else event.get("decision_reason") or str(event.get("event_type") or "")
        description = action["description"] if "description" in action else self._event_excerpt(event)
        created = self.intake_service.create_item(
            {
                "title": title,
                "description": description,
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
        return {"type": action["type"], "created_intake_item_id": created["intake_item_id"]}

    def _execute_log_action(
        self,
        action: dict[str, str],
        *,
        rule: dict[str, Any],
        event: dict[str, Any],
        actor_user: dict[str, Any] | None,
        actor: str,
    ) -> dict[str, Any]:
        del rule, event, actor_user, actor
        return {"type": action["type"], "message": action.get("message", "")}

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
