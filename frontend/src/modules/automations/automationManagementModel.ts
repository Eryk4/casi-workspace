import { ApiContractError, ApiError } from "@/lib/api";

export const AUTOMATION_MANAGE_CAPABILITY = "automation.manage";

export type AutomationCatalogField = {
  key: string;
  type: string;
  maxLength: number;
  required?: boolean;
  operators?: string[];
};

export type AutomationCatalogTrigger = {
  key: string;
  labelKey: string;
  conditionFields: AutomationCatalogField[];
};

export type AutomationCatalogAction = {
  key: string;
  labelKey: string;
  fields: AutomationCatalogField[];
};

export type AutomationCatalog = {
  version: 1;
  triggers: AutomationCatalogTrigger[];
  actions: AutomationCatalogAction[];
  constraints: {
    minActions: number;
    maxActions: number;
    maxConditions: number;
  };
};

export type AutomationRuleSummary = {
  id: number;
  name: string;
  description: string | null;
  triggerKey: string;
  active: boolean;
  lastRunAt: string | null;
  executionCount: number;
  updatedAt: string | null;
};

export type AutomationConditionDraft = {
  fieldKey: string;
  operator: string;
  value: string;
};

export type AutomationRuleDraft = {
  name: string;
  description: string;
  triggerKey: string;
  conditions: AutomationConditionDraft[];
  actionKey: string;
  actionValues: Record<string, string>;
};

export type AutomationRuleCreatePayload = {
  rule_name: string;
  description?: string;
  trigger_event_type: string;
  conditions_json: Record<string, string>;
  actions_json: Array<Record<string, string>>;
  is_active: false;
};

export type AutomationRuleDraftValidation = {
  payload: AutomationRuleCreatePayload | null;
  errors: Record<string, string>;
};

const FORBIDDEN_RULE_FIELDS = new Set([
  "conditions_json",
  "actions_json",
  "last_processed_event_log_id",
  "processing_claim_token",
  "processing_claimed_at",
  "processing_lease_until",
]);

const TRIGGER_LABELS: Record<string, string> = {
  "automation.trigger.invoice_status_changed": "Zmiana statusu faktury",
  "automation.trigger.work_item_created": "Utworzono zadanie",
  "automation.trigger.work_item_updated": "Zmieniono zadanie",
};

const CONDITION_LABELS: Record<string, string> = {
  source: "Źródło",
  status_before: "Poprzedni status",
  status_after: "Nowy status",
};

const ACTION_LABELS: Record<string, string> = {
  "automation.action.create_inbox_item": "Utwórz powiadomienie w CASI",
};

const ACTION_FIELD_LABELS: Record<string, string> = {
  title: "Tytuł",
  description: "Treść",
};

const OPERATOR_LABELS: Record<string, string> = {
  equals: "jest równe",
};

function record(value: unknown): Record<string, unknown> | null {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

function nonEmptyString(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
}

function nullableString(value: unknown): string | null | undefined {
  if (value === null || value === undefined) return null;
  return typeof value === "string" ? value : undefined;
}

function positiveInteger(value: unknown): number | null {
  return typeof value === "number" && Number.isInteger(value) && value > 0 ? value : null;
}

function nonNegativeInteger(value: unknown): number | null {
  return typeof value === "number" && Number.isInteger(value) && value >= 0 ? value : null;
}

function parseField(value: unknown, endpoint: string, actionField = false): AutomationCatalogField {
  const source = record(value);
  const key = nonEmptyString(source?.key);
  const type = nonEmptyString(source?.type);
  const maxLength = positiveInteger(source?.max_length);
  if (!source || !key || !type || maxLength === null) {
    throw new ApiContractError(endpoint, value);
  }

  if (actionField) {
    if (typeof source.required !== "boolean") throw new ApiContractError(endpoint, value);
    return { key, type, maxLength, required: source.required };
  }

  if (!Array.isArray(source.operators) || source.operators.length === 0 || !source.operators.every(nonEmptyString)) {
    throw new ApiContractError(endpoint, value);
  }
  return { key, type, maxLength, operators: source.operators as string[] };
}

export function readAutomationCatalog(payload: unknown): AutomationCatalog {
  const endpoint = "/automations/catalog";
  const source = record(payload);
  const constraints = record(source?.constraints);
  if (
    !source ||
    source.version !== 1 ||
    !Array.isArray(source.triggers) ||
    !Array.isArray(source.actions) ||
    !constraints
  ) {
    throw new ApiContractError(endpoint, payload);
  }

  const minActions = nonNegativeInteger(constraints.min_actions);
  const maxActions = positiveInteger(constraints.max_actions);
  const maxConditions = nonNegativeInteger(constraints.max_conditions);
  if (minActions === null || maxActions === null || maxConditions === null || minActions > maxActions) {
    throw new ApiContractError(endpoint, payload);
  }

  const triggers = source.triggers.map((entry) => {
    const trigger = record(entry);
    const key = nonEmptyString(trigger?.key);
    const labelKey = nonEmptyString(trigger?.label_key);
    if (!trigger || !key || !labelKey || !Array.isArray(trigger.condition_fields)) {
      throw new ApiContractError(endpoint, entry);
    }
    return {
      key,
      labelKey,
      conditionFields: trigger.condition_fields.map((field) => parseField(field, endpoint)),
    };
  });

  const actions = source.actions.map((entry) => {
    const action = record(entry);
    const key = nonEmptyString(action?.key);
    const labelKey = nonEmptyString(action?.label_key);
    if (!action || !key || !labelKey || !Array.isArray(action.fields)) {
      throw new ApiContractError(endpoint, entry);
    }
    return {
      key,
      labelKey,
      fields: action.fields.map((field) => parseField(field, endpoint, true)),
    };
  });

  return {
    version: 1,
    triggers,
    actions,
    constraints: { minActions, maxActions, maxConditions },
  };
}

export function readAutomationRules(payload: unknown): AutomationRuleSummary[] {
  const endpoint = "/automation/rules";
  if (!Array.isArray(payload)) throw new ApiContractError(endpoint, payload);

  return payload.map((entry) => {
    const source = record(entry);
    if (!source || Object.keys(source).some((key) => FORBIDDEN_RULE_FIELDS.has(key))) {
      throw new ApiContractError(endpoint, entry);
    }
    const id = positiveInteger(source.automation_rule_id);
    const name = nonEmptyString(source.rule_name);
    const description = nullableString(source.description);
    const triggerKey = nonEmptyString(source.trigger_event_type);
    const lastRunAt = nullableString(source.last_run_at);
    const updatedAt = nullableString(source.updated_at);
    const executionCount = nonNegativeInteger(source.execution_count);
    if (
      id === null ||
      !name ||
      description === undefined ||
      !triggerKey ||
      typeof source.is_active !== "boolean" ||
      lastRunAt === undefined ||
      updatedAt === undefined ||
      executionCount === null
    ) {
      throw new ApiContractError(endpoint, entry);
    }
    return {
      id,
      name,
      description,
      triggerKey,
      active: source.is_active,
      lastRunAt,
      executionCount,
      updatedAt,
    };
  });
}

export function hasAutomationManage(capabilities: string[]): boolean {
  return capabilities.includes(AUTOMATION_MANAGE_CAPABILITY);
}

export function automationTriggerLabel(trigger: AutomationCatalogTrigger | undefined): string {
  return trigger ? (TRIGGER_LABELS[trigger.labelKey] ?? "Zdarzenie automatyzacji") : "Zdarzenie automatyzacji";
}

export function automationConditionLabel(key: string): string {
  return CONDITION_LABELS[key] ?? "Warunek";
}

export function automationActionLabel(action: AutomationCatalogAction | undefined): string {
  return action ? (ACTION_LABELS[action.labelKey] ?? "Działanie w CASI") : "Działanie w CASI";
}

export function automationActionFieldLabel(key: string): string {
  return ACTION_FIELD_LABELS[key] ?? "Wartość";
}

export function automationOperatorLabel(operator: string): string {
  return OPERATOR_LABELS[operator] ?? "operator";
}

export function supportedManagementActions(catalog: AutomationCatalog): AutomationCatalogAction[] {
  return catalog.actions.filter(
    (action) =>
      action.key === "create_inbox_item" &&
      action.fields.every((field) => ["title", "description"].includes(field.key) && field.type === "string"),
  );
}

export function isAutomationCatalogSupported(catalog: AutomationCatalog): boolean {
  return (
    catalog.constraints.minActions === 1 &&
    catalog.constraints.maxActions === 1 &&
    catalog.triggers.length > 0 &&
    catalog.triggers.every((trigger) =>
      trigger.conditionFields.every(
        (field) => field.type === "string" && (field.operators ?? []).every((operator) => operator === "equals"),
      ),
    ) &&
    supportedManagementActions(catalog).length > 0
  );
}

export function emptyAutomationRuleDraft(): AutomationRuleDraft {
  return {
    name: "",
    description: "",
    triggerKey: "",
    conditions: [],
    actionKey: "",
    actionValues: {},
  };
}

export function conditionFieldsForTrigger(
  catalog: AutomationCatalog,
  triggerKey: string,
): AutomationCatalogField[] {
  return catalog.triggers.find((trigger) => trigger.key === triggerKey)?.conditionFields ?? [];
}

export function resetConditionsForTrigger(draft: AutomationRuleDraft, triggerKey: string): AutomationRuleDraft {
  return { ...draft, triggerKey, conditions: [] };
}

export function validateAutomationRuleDraft(
  catalog: AutomationCatalog,
  draft: AutomationRuleDraft,
): AutomationRuleDraftValidation {
  const errors: Record<string, string> = {};
  const name = draft.name.trim();
  const description = draft.description.trim();
  if (!name) errors.rule_name = "Podaj nazwę reguły.";
  else if (name.length > 160) errors.rule_name = "Nazwa reguły może mieć maksymalnie 160 znaków.";
  if (description.length > 1000) errors.description = "Opis może mieć maksymalnie 1000 znaków.";

  const trigger = catalog.triggers.find((item) => item.key === draft.triggerKey);
  if (!trigger) errors.trigger_event_type = "Wybierz zdarzenie uruchamiające regułę.";
  if (draft.conditions.length > catalog.constraints.maxConditions) {
    errors.conditions_json = `Możesz dodać maksymalnie ${catalog.constraints.maxConditions} warunki.`;
  }

  const conditions: Record<string, string> = {};
  draft.conditions.forEach((condition, index) => {
    const field = trigger?.conditionFields.find((item) => item.key === condition.fieldKey);
    const path = `conditions_json.${index}`;
    if (!field || conditions[condition.fieldKey] !== undefined) {
      errors[path] = "Wybierz unikalne pole warunku dostępne dla tego zdarzenia.";
      return;
    }
    if (!(field.operators ?? []).includes(condition.operator)) {
      errors[path] = "Wybrany operator nie jest dostępny dla tego warunku.";
      return;
    }
    const value = condition.value.trim();
    if (!value) errors[path] = "Podaj wartość warunku.";
    else if (value.length > field.maxLength) errors[path] = `Wartość może mieć maksymalnie ${field.maxLength} znaków.`;
    else conditions[field.key] = value;
  });

  const action = supportedManagementActions(catalog).find((item) => item.key === draft.actionKey);
  if (!action) errors.actions_json = "Wybierz obsługiwane działanie.";
  const actionPayload: Record<string, string> = action ? { type: action.key } : {};
  action?.fields.forEach((field) => {
    const value = (draft.actionValues[field.key] ?? "").trim();
    if (field.required && !value) errors[`actions_json.${field.key}`] = `Pole „${automationActionFieldLabel(field.key)}” jest wymagane.`;
    else if (value.length > field.maxLength) errors[`actions_json.${field.key}`] = `Pole może mieć maksymalnie ${field.maxLength} znaków.`;
    else if (value) actionPayload[field.key] = value;
  });

  if (Object.keys(errors).length > 0 || !trigger || !action) return { payload: null, errors };
  return {
    payload: {
      rule_name: name,
      ...(description ? { description } : {}),
      trigger_event_type: trigger.key,
      conditions_json: conditions,
      actions_json: [actionPayload],
      is_active: false,
    },
    errors: {},
  };
}

export function readAutomationValidationError(error: unknown): { field: string | null; message: string } {
  if (error instanceof ApiError) {
    const payload = record(error.payload);
    const rawField = typeof payload?.field === "string" ? payload.field : null;
    const field = rawField?.startsWith("actions[0].")
      ? `actions_json.${rawField.slice("actions[0].".length)}`
      : rawField === "actions" || rawField === "actions[0].type"
        ? "actions_json"
        : rawField?.startsWith("conditions.") || rawField === "conditions"
          ? "conditions_json"
          : rawField;
    const message = typeof payload?.error === "string" && payload.error.trim()
      ? payload.error
      : "Nie udało się zapisać reguły automatyzacji.";
    return { field, message };
  }
  return { field: null, message: "Nie udało się zapisać reguły automatyzacji." };
}

export function automationBusyMessage(error: unknown): string | null {
  if (!(error instanceof ApiError) || error.status !== 409) return null;
  const payload = record(error.payload);
  return payload?.code === "automation_rule_busy"
    ? "Reguła jest obecnie przetwarzana. Spróbuj włączyć ją ponownie za chwilę."
    : null;
}
