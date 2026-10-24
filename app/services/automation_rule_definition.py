from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Literal


CATALOG_VERSION = 1
MANAGEMENT_MIN_ACTIONS = 1
MANAGEMENT_MAX_ACTIONS = 1
MANAGEMENT_MAX_CONDITIONS = 3
RULE_NAME_MAX_LENGTH = 160
RULE_SLUG_MAX_LENGTH = 120
RULE_DESCRIPTION_MAX_LENGTH = 1000
CONDITION_VALUE_MAX_LENGTH = 120


class AutomationRuleValidationError(ValueError):
    def __init__(self, code: str, path: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.path = path
        self.safe_message = message

    def as_response(self) -> dict[str, str]:
        return {"error": self.safe_message, "code": self.code, "field": self.path}


@dataclass(frozen=True)
class ConditionDefinition:
    key: str
    value_type: Literal["string"]
    operator: Literal["equals", "contains"]
    event_field: str
    max_length: int


@dataclass(frozen=True)
class TriggerDefinition:
    key: str
    label_key: str
    management_condition_keys: tuple[str, ...]


@dataclass(frozen=True)
class ActionFieldDefinition:
    key: str
    value_type: Literal["string"]
    max_length: int
    enum_values: tuple[str, ...] = ()
    allow_empty: bool = False


@dataclass(frozen=True)
class ActionDefinition:
    key: str
    label_key: str
    executor: str
    execution_fields: tuple[ActionFieldDefinition, ...]
    management_fields: tuple[str, ...]
    management_required_fields: tuple[str, ...]
    management_visible: bool


@dataclass(frozen=True)
class ValidatedAutomationRuleDefinition:
    trigger_event_type: str
    conditions: dict[str, str]
    actions: list[dict[str, str]]


CONDITION_DEFINITIONS: dict[str, ConditionDefinition] = {
    "source": ConditionDefinition("source", "string", "equals", "source", CONDITION_VALUE_MAX_LENGTH),
    "status_before": ConditionDefinition(
        "status_before", "string", "equals", "status_before", CONDITION_VALUE_MAX_LENGTH
    ),
    "status_after": ConditionDefinition(
        "status_after", "string", "equals", "status_after", CONDITION_VALUE_MAX_LENGTH
    ),
    "decision_reason_contains": ConditionDefinition(
        "decision_reason_contains", "string", "contains", "decision_reason", 500
    ),
    "details_contains": ConditionDefinition("details_contains", "string", "contains", "details", 500),
}


TRIGGER_DEFINITIONS: dict[str, TriggerDefinition] = {
    "invoice_status_changed": TriggerDefinition(
        "invoice_status_changed",
        "automation.trigger.invoice_status_changed",
        ("source", "status_before", "status_after"),
    ),
    "work_item_created": TriggerDefinition(
        "work_item_created",
        "automation.trigger.work_item_created",
        ("status_after",),
    ),
    "work_item_updated": TriggerDefinition(
        "work_item_updated",
        "automation.trigger.work_item_updated",
        ("status_before", "status_after"),
    ),
}


_CREATE_INBOX_FIELDS = (
    ActionFieldDefinition("title", "string", 200),
    ActionFieldDefinition("description", "string", 2000, allow_empty=True),
    ActionFieldDefinition("priority", "string", 20, ("niski", "normalny", "wysoki", "pilny")),
    ActionFieldDefinition("requester_name", "string", 200, allow_empty=True),
    ActionFieldDefinition("requester_email", "string", 320, allow_empty=True),
    ActionFieldDefinition("source_reference", "string", 200, allow_empty=True),
)


ACTION_DEFINITIONS: dict[str, ActionDefinition] = {
    "create_inbox_item": ActionDefinition(
        "create_inbox_item",
        "automation.action.create_inbox_item",
        "create_inbox_item",
        _CREATE_INBOX_FIELDS,
        ("title", "description"),
        ("title",),
        True,
    ),
    "log": ActionDefinition(
        "log",
        "automation.action.log",
        "log",
        (ActionFieldDefinition("message", "string", 2000, allow_empty=True),),
        (),
        (),
        False,
    ),
}


_SAFE_TRIGGER_PATTERN = re.compile(r"^[A-Za-z0-9_.:-]+$")


def get_automation_rule_catalog() -> dict[str, Any]:
    triggers: list[dict[str, Any]] = []
    for trigger in TRIGGER_DEFINITIONS.values():
        condition_fields = []
        for condition_key in trigger.management_condition_keys:
            condition = CONDITION_DEFINITIONS[condition_key]
            condition_fields.append(
                {
                    "key": condition.key,
                    "type": condition.value_type,
                    "operators": [condition.operator],
                    "max_length": condition.max_length,
                }
            )
        triggers.append(
            {
                "key": trigger.key,
                "label_key": trigger.label_key,
                "condition_fields": condition_fields,
            }
        )

    actions: list[dict[str, Any]] = []
    for action in ACTION_DEFINITIONS.values():
        if not action.management_visible:
            continue
        fields_by_key = {field.key: field for field in action.execution_fields}
        fields: list[dict[str, Any]] = []
        for field_key in action.management_fields:
            field = fields_by_key[field_key]
            field_payload: dict[str, Any] = {
                "key": field.key,
                "type": field.value_type,
                "required": field.key in action.management_required_fields,
                "max_length": field.max_length,
            }
            if field.enum_values:
                field_payload["enum_values"] = list(field.enum_values)
            fields.append(field_payload)
        actions.append({"key": action.key, "label_key": action.label_key, "fields": fields})

    return {
        "version": CATALOG_VERSION,
        "triggers": triggers,
        "actions": actions,
        "constraints": {
            "min_actions": MANAGEMENT_MIN_ACTIONS,
            "max_actions": MANAGEMENT_MAX_ACTIONS,
            "max_conditions": MANAGEMENT_MAX_CONDITIONS,
        },
    }


def validate_management_rule_definition(
    trigger_event_type: Any,
    conditions: Any,
    actions: Any,
) -> ValidatedAutomationRuleDefinition:
    return _validate_rule_definition(trigger_event_type, conditions, actions, mode="management")


def validate_execution_rule_definition(
    trigger_event_type: Any,
    conditions: Any,
    actions: Any,
) -> ValidatedAutomationRuleDefinition:
    return _validate_rule_definition(trigger_event_type, conditions, actions, mode="execution")


def get_execution_action_definition(action_type: str) -> ActionDefinition:
    definition = ACTION_DEFINITIONS.get(action_type)
    if definition is None:
        raise AutomationRuleValidationError(
            "automation_rule.unknown_action",
            "actions[].type",
            "Typ akcji automatyzacji nie jest obsługiwany.",
        )
    return definition


def get_condition_definition(condition_key: str) -> ConditionDefinition:
    definition = CONDITION_DEFINITIONS.get(condition_key)
    if definition is None:
        raise AutomationRuleValidationError(
            "automation_rule.unknown_condition",
            f"conditions.{condition_key}",
            "Pole warunku automatyzacji nie jest obsługiwane.",
        )
    return definition


def validate_rule_metadata(payload: dict[str, Any], *, partial: bool) -> dict[str, str | None]:
    result: dict[str, str | None] = {}
    field_specs = {
        "rule_name": (True, RULE_NAME_MAX_LENGTH),
        "rule_slug": (True, RULE_SLUG_MAX_LENGTH),
        "description": (False, RULE_DESCRIPTION_MAX_LENGTH),
    }
    for key, (required, max_length) in field_specs.items():
        if key not in payload:
            if required and not partial and key == "rule_name":
                raise AutomationRuleValidationError(
                    "automation_rule.required",
                    key,
                    "Nazwa reguły jest wymagana.",
                )
            continue
        value = payload.get(key)
        if value is None and not required:
            result[key] = None
            continue
        result[key] = _validate_string(value, key, max_length=max_length, allow_empty=not required)
    return result


def validate_rule_payload_keys(payload: Any, *, partial: bool) -> None:
    if not isinstance(payload, dict):
        raise AutomationRuleValidationError(
            "automation_rule.invalid_payload",
            "$",
            "Dane reguły automatyzacji muszą być obiektem.",
        )
    allowed = {
        "rule_name",
        "rule_slug",
        "description",
        "trigger_event_type",
        "conditions_json",
        "actions_json",
        "actions",
        "is_active",
    }
    unknown = sorted(str(key) for key in payload if key not in allowed)
    if unknown:
        raise AutomationRuleValidationError(
            "automation_rule.unknown_field",
            unknown[0],
            "Dane reguły zawierają nieobsługiwane pole.",
        )
    if "actions" in payload and "actions_json" in payload:
        raise AutomationRuleValidationError(
            "automation_rule.conflicting_fields",
            "actions",
            "Podaj tylko jedno pole akcji.",
        )
    if not partial:
        for required_key in ("rule_name", "trigger_event_type"):
            if required_key not in payload:
                raise AutomationRuleValidationError(
                    "automation_rule.required",
                    required_key,
                    "Brakuje wymaganego pola reguły automatyzacji.",
                )


def normalize_active_flag(value: Any, *, path: str = "is_active") -> int:
    if value is True:
        return 1
    if value is False:
        return 0
    if isinstance(value, int) and not isinstance(value, bool) and value in {0, 1}:
        return value
    if isinstance(value, str) and value in {"0", "1", "false", "true"}:
        return 1 if value in {"1", "true"} else 0
    raise AutomationRuleValidationError(
        "automation_rule.invalid_type",
        path,
        "Pole aktywności musi mieć wartość logiczną.",
    )


def _validate_rule_definition(
    trigger_event_type: Any,
    conditions: Any,
    actions: Any,
    *,
    mode: Literal["management", "execution"],
) -> ValidatedAutomationRuleDefinition:
    trigger = _validate_string(trigger_event_type, "trigger_event_type", max_length=120)
    if not _SAFE_TRIGGER_PATTERN.fullmatch(trigger):
        raise AutomationRuleValidationError(
            "automation_rule.invalid_trigger",
            "trigger_event_type",
            "Typ zdarzenia wyzwalającego ma nieprawidłowy format.",
        )
    trigger_definition = TRIGGER_DEFINITIONS.get(trigger)
    if mode == "management" and trigger_definition is None:
        raise AutomationRuleValidationError(
            "automation_rule.unknown_trigger",
            "trigger_event_type",
            "Typ zdarzenia wyzwalającego nie jest dostępny w zarządzaniu automatyzacjami.",
        )

    parsed_conditions = _parse_json(conditions, "conditions")
    if not isinstance(parsed_conditions, dict):
        raise AutomationRuleValidationError(
            "automation_rule.invalid_conditions",
            "conditions",
            "Warunki automatyzacji muszą być obiektem.",
        )
    allowed_condition_keys = (
        set(trigger_definition.management_condition_keys)
        if mode == "management" and trigger_definition is not None
        else set(CONDITION_DEFINITIONS)
    )
    if mode == "management" and len(parsed_conditions) > MANAGEMENT_MAX_CONDITIONS:
        raise AutomationRuleValidationError(
            "automation_rule.too_many_conditions",
            "conditions",
            "Reguła zawiera zbyt wiele warunków.",
        )
    normalized_conditions: dict[str, str] = {}
    for raw_key, raw_value in parsed_conditions.items():
        if not isinstance(raw_key, str) or raw_key not in allowed_condition_keys:
            path_key = raw_key if isinstance(raw_key, str) else "?"
            raise AutomationRuleValidationError(
                "automation_rule.unknown_condition",
                f"conditions.{path_key}",
                "Pole warunku automatyzacji nie jest obsługiwane.",
            )
        definition = CONDITION_DEFINITIONS[raw_key]
        normalized_conditions[raw_key] = _validate_string(
            raw_value,
            f"conditions.{raw_key}",
            max_length=definition.max_length,
        )

    parsed_actions = _parse_json(actions, "actions")
    if not isinstance(parsed_actions, list):
        raise AutomationRuleValidationError(
            "automation_rule.invalid_actions",
            "actions",
            "Akcje automatyzacji muszą być tablicą.",
        )
    if mode == "management" and not MANAGEMENT_MIN_ACTIONS <= len(parsed_actions) <= MANAGEMENT_MAX_ACTIONS:
        raise AutomationRuleValidationError(
            "automation_rule.invalid_action_count",
            "actions",
            "Reguła zarządzana musi zawierać dokładnie jedną akcję.",
        )
    if mode == "execution" and not parsed_actions:
        raise AutomationRuleValidationError(
            "automation_rule.invalid_action_count",
            "actions",
            "Reguła automatyzacji musi zawierać co najmniej jedną akcję.",
        )

    normalized_actions: list[dict[str, str]] = []
    for index, raw_action in enumerate(parsed_actions):
        path = f"actions[{index}]"
        if not isinstance(raw_action, dict):
            raise AutomationRuleValidationError(
                "automation_rule.invalid_action",
                path,
                "Akcja automatyzacji musi być obiektem.",
            )
        action_type = _validate_string(raw_action.get("type"), f"{path}.type", max_length=80).lower()
        action_definition = ACTION_DEFINITIONS.get(action_type)
        if action_definition is None or (mode == "management" and not action_definition.management_visible):
            raise AutomationRuleValidationError(
                "automation_rule.unknown_action",
                f"{path}.type",
                "Typ akcji automatyzacji nie jest dostępny.",
            )
        all_fields = {field.key: field for field in action_definition.execution_fields}
        ordered_allowed_fields = (
            action_definition.management_fields
            if mode == "management"
            else tuple(field.key for field in action_definition.execution_fields)
        )
        allowed_fields = set(ordered_allowed_fields)
        unknown_fields = sorted(
            str(key) for key in raw_action if key != "type" and key not in allowed_fields
        )
        if unknown_fields:
            raise AutomationRuleValidationError(
                "automation_rule.unknown_action_field",
                f"{path}.{unknown_fields[0]}",
                "Akcja automatyzacji zawiera nieobsługiwane pole.",
            )
        if mode == "management":
            missing = [
                key
                for key in action_definition.management_required_fields
                if key not in raw_action
            ]
            if missing:
                raise AutomationRuleValidationError(
                    "automation_rule.required",
                    f"{path}.{missing[0]}",
                    "Brakuje wymaganego pola akcji automatyzacji.",
                )
        normalized_action = {"type": action_type}
        for field_key in ordered_allowed_fields:
            if field_key not in raw_action:
                continue
            field = all_fields[field_key]
            normalized = _validate_string(
                raw_action.get(field_key),
                f"{path}.{field_key}",
                max_length=field.max_length,
                allow_empty=field.allow_empty,
            )
            if field.enum_values and normalized not in field.enum_values:
                raise AutomationRuleValidationError(
                    "automation_rule.invalid_value",
                    f"{path}.{field_key}",
                    "Pole akcji automatyzacji ma niedozwoloną wartość.",
                )
            normalized_action[field_key] = normalized
        if mode == "management" and action_type == "create_inbox_item":
            normalized_action.setdefault("description", "")
        normalized_actions.append(normalized_action)

    return ValidatedAutomationRuleDefinition(trigger, normalized_conditions, normalized_actions)


def _parse_json(value: Any, path: str) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError as error:
            raise AutomationRuleValidationError(
                "automation_rule.invalid_json",
                path,
                "Konfiguracja automatyzacji zawiera nieprawidłowy JSON.",
            ) from error
    return value


def _validate_string(value: Any, path: str, *, max_length: int, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise AutomationRuleValidationError(
            "automation_rule.invalid_type",
            path,
            "Pole konfiguracji automatyzacji musi być tekstem.",
        )
    normalized = value.strip()
    if not normalized and not allow_empty:
        raise AutomationRuleValidationError(
            "automation_rule.required",
            path,
            "Pole konfiguracji automatyzacji nie może być puste.",
        )
    if len(normalized) > max_length:
        raise AutomationRuleValidationError(
            "automation_rule.too_long",
            path,
            "Pole konfiguracji automatyzacji przekracza dozwoloną długość.",
        )
    return normalized
