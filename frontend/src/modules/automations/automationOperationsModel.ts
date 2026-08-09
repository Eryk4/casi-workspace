export type AutomationConfigurationStatus = "enabled" | "disabled" | "not_configured";
export type AutomationHealth = "healthy" | "attention" | "never_run" | "disabled";
export type AutomationOperationsFilter = "all" | "active" | "disabled" | "attention";
export type AutomationRunStatus = "pending" | "running" | "succeeded" | "failed";

export type AutomationOperation = {
  automationKey: string;
  automationType: string;
  title: string;
  description: string;
  status: AutomationConfigurationStatus;
  enabled: boolean;
  health: AutomationHealth;
  healthReasonCode: string;
  scheduleId: number | null;
  runId: number | null;
  nextRunAt: string | null;
  lastRunAt: string | null;
  lastRunStatus: AutomationRunStatus | null;
  lastRunDurationMs: number | null;
  lastAttemptCount: number | null;
  lastCandidatesCount: number | null;
  lastCreatedCount: number | null;
  lastExistingCount: number | null;
  recentFailureCount: number;
  lastErrorCode: string | null;
  lastErrorSummary: string | null;
  settingsUrl: string;
  detailsUrl: string;
  runtimeStatus: "unknown";
  schedule: {
    cadence: string;
    timezoneName: string;
    localTime: string;
  };
  updatedAt: string | null;
};

export type AutomationOperationsDashboard = {
  summary: {
    activeCount: number;
    disabledCount: number;
    attentionCount: number;
    recentFailureCount: number;
  };
  items: AutomationOperation[];
};

export type AutomationRun = {
  runId: number;
  scheduleId: number;
  scheduledLocalDate: string;
  asOfDate: string;
  scheduledForUtc: string;
  status: AutomationRunStatus;
  attemptCount: number;
  candidatesCount: number | null;
  createdCount: number | null;
  existingCount: number | null;
  errorCode: string | null;
  errorSummary: string | null;
  startedAt: string | null;
  finishedAt: string | null;
  durationMs: number | null;
};

export type AutomationOperationDetail = {
  item: AutomationOperation;
  history: AutomationRun[];
  historyLimit: number;
};

export const AUTOMATION_OPERATIONS_FILTERS: Array<{ id: AutomationOperationsFilter; label: string }> = [
  { id: "all", label: "Wszystkie" },
  { id: "active", label: "Aktywne" },
  { id: "disabled", label: "Wyłączone" },
  { id: "attention", label: "Wymagają uwagi" },
];

export const AUTOMATION_OPERATIONS_POLL_INTERVAL = null;

const CONFIGURATION_STATUSES = new Set<AutomationConfigurationStatus>(["enabled", "disabled", "not_configured"]);
const HEALTH_STATUSES = new Set<AutomationHealth>(["healthy", "attention", "never_run", "disabled"]);
const RUN_STATUSES = new Set<AutomationRunStatus>(["pending", "running", "succeeded", "failed"]);

function record(value: unknown, label: string): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error(`Nieprawidłowy kontrakt: ${label}.`);
  return value as Record<string, unknown>;
}

function text(value: unknown, label: string): string {
  if (typeof value !== "string" || !value.trim()) throw new Error(`Nieprawidłowy kontrakt: ${label}.`);
  return value.trim();
}

function optionalText(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function nonNegativeInteger(value: unknown, label: string, nullable = false): number | null {
  if (nullable && value === null) return null;
  if (!Number.isInteger(value) || Number(value) < 0) throw new Error(`Nieprawidłowy kontrakt: ${label}.`);
  return Number(value);
}

function safePath(value: unknown, label: string): string {
  const path = text(value, label);
  if (!path.startsWith("/") || path.startsWith("//")) throw new Error(`Nieprawidłowy bezpieczny link: ${label}.`);
  return path;
}

function readOperation(value: unknown): AutomationOperation {
  const item = record(value, "automation operation");
  const status = text(item.status, "status") as AutomationConfigurationStatus;
  const health = text(item.health, "health") as AutomationHealth;
  if (!CONFIGURATION_STATUSES.has(status) || !HEALTH_STATUSES.has(health)) throw new Error("Nieznany status automatyzacji.");
  if (typeof item.enabled !== "boolean") throw new Error("Nieprawidłowy kontrakt: enabled.");
  const lastRunStatus = optionalText(item.last_run_status) as AutomationRunStatus | null;
  if (lastRunStatus && !RUN_STATUSES.has(lastRunStatus)) throw new Error("Nieznany status runu.");
  const schedule = record(item.schedule, "schedule");
  if (item.runtime_status !== "unknown") throw new Error("Nieznany status runtime.");
  return {
    automationKey: text(item.automation_key, "automation_key"),
    automationType: text(item.automation_type, "automation_type"),
    title: text(item.title, "title"),
    description: text(item.description, "description"),
    status,
    enabled: item.enabled,
    health,
    healthReasonCode: text(item.health_reason_code, "health_reason_code"),
    scheduleId: nonNegativeInteger(item.schedule_id, "schedule_id", true),
    runId: nonNegativeInteger(item.run_id, "run_id", true),
    nextRunAt: optionalText(item.next_run_at),
    lastRunAt: optionalText(item.last_run_at),
    lastRunStatus,
    lastRunDurationMs: nonNegativeInteger(item.last_run_duration_ms, "last_run_duration_ms", true),
    lastAttemptCount: nonNegativeInteger(item.last_attempt_count, "last_attempt_count", true),
    lastCandidatesCount: nonNegativeInteger(item.last_candidates_count, "last_candidates_count", true),
    lastCreatedCount: nonNegativeInteger(item.last_created_count, "last_created_count", true),
    lastExistingCount: nonNegativeInteger(item.last_existing_count, "last_existing_count", true),
    recentFailureCount: nonNegativeInteger(item.recent_failure_count, "recent_failure_count") as number,
    lastErrorCode: optionalText(item.last_error_code),
    lastErrorSummary: optionalText(item.last_error_summary),
    settingsUrl: safePath(item.settings_url, "settings_url"),
    detailsUrl: safePath(item.details_url, "details_url"),
    runtimeStatus: "unknown",
    schedule: {
      cadence: text(schedule.cadence, "schedule.cadence"),
      timezoneName: text(schedule.timezone_name, "schedule.timezone_name"),
      localTime: text(schedule.local_time, "schedule.local_time"),
    },
    updatedAt: optionalText(item.updated_at),
  };
}

function readRun(value: unknown): AutomationRun {
  const run = record(value, "automation run");
  const status = text(run.status, "run.status") as AutomationRunStatus;
  if (!RUN_STATUSES.has(status)) throw new Error("Nieznany status historii runu.");
  return {
    runId: nonNegativeInteger(run.run_id, "run_id") as number,
    scheduleId: nonNegativeInteger(run.schedule_id, "schedule_id") as number,
    scheduledLocalDate: text(run.scheduled_local_date, "scheduled_local_date"),
    asOfDate: text(run.as_of_date, "as_of_date"),
    scheduledForUtc: text(run.scheduled_for_utc, "scheduled_for_utc"),
    status,
    attemptCount: nonNegativeInteger(run.attempt_count, "attempt_count") as number,
    candidatesCount: nonNegativeInteger(run.candidates_count, "candidates_count", true),
    createdCount: nonNegativeInteger(run.created_count, "created_count", true),
    existingCount: nonNegativeInteger(run.existing_count, "existing_count", true),
    errorCode: optionalText(run.error_code),
    errorSummary: optionalText(run.error_summary),
    startedAt: optionalText(run.started_at),
    finishedAt: optionalText(run.finished_at),
    durationMs: nonNegativeInteger(run.duration_ms, "duration_ms", true),
  };
}

export function readAutomationOperationsDashboard(payload: unknown): AutomationOperationsDashboard {
  const root = record(payload, "automation dashboard");
  const summary = record(root.summary, "summary");
  if (!Array.isArray(root.items)) throw new Error("Nieprawidłowy kontrakt: items.");
  return {
    summary: {
      activeCount: nonNegativeInteger(summary.active_count, "active_count") as number,
      disabledCount: nonNegativeInteger(summary.disabled_count, "disabled_count") as number,
      attentionCount: nonNegativeInteger(summary.attention_count, "attention_count") as number,
      recentFailureCount: nonNegativeInteger(summary.recent_failure_count, "recent_failure_count") as number,
    },
    items: root.items.map(readOperation),
  };
}

export function readAutomationOperationDetail(payload: unknown): AutomationOperationDetail {
  const root = record(payload, "automation detail");
  if (!Array.isArray(root.history)) throw new Error("Nieprawidłowy kontrakt: history.");
  return {
    item: readOperation(root.item),
    history: root.history.map(readRun),
    historyLimit: nonNegativeInteger(root.history_limit, "history_limit") as number,
  };
}

export function filterAutomationOperations(
  items: AutomationOperation[],
  filter: AutomationOperationsFilter,
): AutomationOperation[] {
  if (filter === "active") return items.filter((item) => item.status === "enabled");
  if (filter === "disabled") return items.filter((item) => item.status !== "enabled");
  if (filter === "attention") return items.filter((item) => item.health === "attention");
  return items;
}

export function automationHealthLabel(health: AutomationHealth): string {
  if (health === "healthy") return "Działa poprawnie";
  if (health === "attention") return "Wymaga uwagi";
  if (health === "never_run") return "Jeszcze nie uruchomiono";
  return "Wyłączona";
}

export function automationRunLabel(status: AutomationRunStatus | null): string {
  if (status === "succeeded") return "Sukces";
  if (status === "failed") return "Błąd";
  if (status === "running") return "W toku";
  if (status === "pending") return "Oczekuje";
  return "Brak uruchomień";
}
