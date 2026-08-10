export type AutomationConfigurationStatus = "enabled" | "disabled" | "not_configured";
export type AutomationHealth = "healthy" | "attention" | "never_run" | "disabled";
export type AutomationOperationsFilter = "all" | "active" | "disabled" | "attention";
export type AutomationRunStatus = "pending" | "running" | "succeeded" | "failed";
export type KnowledgeJobStatus = "pending" | "processing" | "completed" | "failed";
export type EmailImportResultStatus = "running" | "completed" | "completed_with_issues" | "no_new_documents" | "failed";
export type KSeFImportResultStatus = EmailImportResultStatus;

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
  settingsUrl: string | null;
  detailsUrl: string;
  runtimeStatus: "unknown";
  schedule: {
    cadence: string;
    timezoneName: string;
    localTime: string;
  } | null;
  disabledReason: string | null;
  lastActivityAt: string | null;
  lastAttemptAt: string | null;
  lastAttemptStatus: string | null;
  pendingCount: number;
  processingCount: number;
  failedCount: number;
  succeededCount: number;
  sentCount: number;
  cancelledCount: number;
  lastHeartbeatAt: string | null;
  lastJobAt: string | null;
  lastJobStatus: KnowledgeJobStatus | null;
  lastSuccessAt: string | null;
  lastFailureAt: string | null;
  watcherCount: number;
  lastScanAt: string | null;
  lastScanStatus: string | null;
  checkedMessageCount: number;
  checkedDocumentCount: number;
  matchedMessageCount: number;
  matchedAttachmentCount: number;
  importedCount: number;
  duplicateCount: number;
  totalImportedCount: number;
  totalDuplicateCount: number;
  totalFailedCount: number;
  runsCount: number;
  configuredConnectionsCount: number;
  enabledConnectionsCount: number;
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
  historyType: "scheduler_run";
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

export type ReminderAttempt = {
  historyType: "reminder_attempt";
  attemptId: number;
  outboxId: number;
  channel: string;
  attemptNo: number;
  status: string;
  attemptedAt: string;
  errorCode: string | null;
  errorSummary: string | null;
};

export type ReminderOutboxItem = {
  outboxId: number;
  status: string;
  channel: string;
  availableAt: string | null;
  attemptCount: number;
  createdAt: string;
  updatedAt: string;
};

export type KnowledgeJob = {
  historyType: "knowledge_job";
  jobId: number;
  jobType: string;
  status: KnowledgeJobStatus;
  attemptCount: number;
  maxAttempts: number;
  createdAt: string;
  startedAt: string | null;
  finishedAt: string | null;
  durationMs: number | null;
  errorCode: string | null;
  errorSummary: string | null;
};

export type KnowledgeWatcher = {
  watcherId: number;
  watchMode: string;
  status: string;
  lastScanStartedAt: string | null;
  lastScanCompletedAt: string | null;
  errorCode: string | null;
  errorSummary: string | null;
};

export type EmailImportRun = {
  historyType: "email_import_run";
  runId: number;
  triggerMode: "manual" | "automatic";
  resultStatus: EmailImportResultStatus;
  status: AutomationRunStatus;
  startedAt: string | null;
  finishedAt: string | null;
  durationMs: number | null;
  checkedMessageCount: number;
  matchedMessageCount: number;
  matchedAttachmentCount: number;
  importedCount: number;
  duplicateCount: number;
  failedCount: number;
  errorCode: string | null;
  errorSummary: string | null;
};

export type KSeFImportRun = {
  historyType: "ksef_import_run";
  runId: number;
  triggerMode: "manual" | "automatic";
  resultStatus: KSeFImportResultStatus;
  status: AutomationRunStatus;
  startedAt: string | null;
  finishedAt: string | null;
  durationMs: number | null;
  checkedDocumentCount: number;
  importedCount: number;
  duplicateCount: number;
  failedCount: number;
  errorCode: string | null;
  errorSummary: string | null;
};

export type AutomationOperationDetail = {
  item: AutomationOperation;
  history: Array<AutomationRun | ReminderAttempt | KnowledgeJob | EmailImportRun | KSeFImportRun>;
  outbox: ReminderOutboxItem[];
  watchers: KnowledgeWatcher[];
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
const KNOWLEDGE_JOB_STATUSES = new Set<KnowledgeJobStatus>(["pending", "processing", "completed", "failed"]);
const EMAIL_IMPORT_RESULT_STATUSES = new Set<EmailImportResultStatus>(["running", "completed", "completed_with_issues", "no_new_documents", "failed"]);

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
  const lastJobStatus = optionalText(item.last_job_status) as KnowledgeJobStatus | null;
  if (lastJobStatus && !KNOWLEDGE_JOB_STATUSES.has(lastJobStatus)) throw new Error("Nieznany status joba wiedzy.");
  const schedule = item.schedule === null || item.schedule === undefined ? null : record(item.schedule, "schedule");
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
    settingsUrl: item.settings_url === null ? null : safePath(item.settings_url, "settings_url"),
    detailsUrl: safePath(item.details_url, "details_url"),
    runtimeStatus: "unknown",
    schedule: schedule ? {
      cadence: text(schedule.cadence, "schedule.cadence"),
      timezoneName: text(schedule.timezone_name, "schedule.timezone_name"),
      localTime: text(schedule.local_time, "schedule.local_time"),
    } : null,
    disabledReason: optionalText(item.disabled_reason),
    lastActivityAt: optionalText(item.last_activity_at ?? item.last_run_at),
    lastAttemptAt: optionalText(item.last_attempt_at),
    lastAttemptStatus: optionalText(item.last_attempt_status),
    pendingCount: nonNegativeInteger(item.pending_count ?? 0, "pending_count") as number,
    processingCount: nonNegativeInteger(item.processing_count ?? 0, "processing_count") as number,
    failedCount: nonNegativeInteger(item.failed_count ?? 0, "failed_count") as number,
    succeededCount: nonNegativeInteger(item.succeeded_count ?? 0, "succeeded_count") as number,
    sentCount: nonNegativeInteger(item.sent_count ?? 0, "sent_count") as number,
    cancelledCount: nonNegativeInteger(item.cancelled_count ?? 0, "cancelled_count") as number,
    lastHeartbeatAt: optionalText(item.last_heartbeat_at),
    lastJobAt: optionalText(item.last_job_at),
    lastJobStatus,
    lastSuccessAt: optionalText(item.last_success_at),
    lastFailureAt: optionalText(item.last_failure_at),
    watcherCount: nonNegativeInteger(item.watcher_count ?? 0, "watcher_count") as number,
    lastScanAt: optionalText(item.last_scan_at),
    lastScanStatus: optionalText(item.last_scan_status),
    checkedMessageCount: nonNegativeInteger(item.checked_message_count ?? 0, "checked_message_count") as number,
    checkedDocumentCount: nonNegativeInteger(item.checked_document_count ?? 0, "checked_document_count") as number,
    matchedMessageCount: nonNegativeInteger(item.matched_message_count ?? 0, "matched_message_count") as number,
    matchedAttachmentCount: nonNegativeInteger(item.matched_attachment_count ?? 0, "matched_attachment_count") as number,
    importedCount: nonNegativeInteger(item.imported_count ?? 0, "imported_count") as number,
    duplicateCount: nonNegativeInteger(item.duplicate_count ?? 0, "duplicate_count") as number,
    totalImportedCount: nonNegativeInteger(item.total_imported_count ?? 0, "total_imported_count") as number,
    totalDuplicateCount: nonNegativeInteger(item.total_duplicate_count ?? 0, "total_duplicate_count") as number,
    totalFailedCount: nonNegativeInteger(item.total_failed_count ?? 0, "total_failed_count") as number,
    runsCount: nonNegativeInteger(item.runs_count ?? 0, "runs_count") as number,
    configuredConnectionsCount: nonNegativeInteger(item.configured_connections_count ?? 0, "configured_connections_count") as number,
    enabledConnectionsCount: nonNegativeInteger(item.enabled_connections_count ?? 0, "enabled_connections_count") as number,
    updatedAt: optionalText(item.updated_at),
  };
}

function readRun(value: unknown): AutomationRun {
  const run = record(value, "automation run");
  const status = text(run.status, "run.status") as AutomationRunStatus;
  if (!RUN_STATUSES.has(status)) throw new Error("Nieznany status historii runu.");
  return {
    historyType: "scheduler_run",
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

function readReminderAttempt(value: unknown): ReminderAttempt {
  const attempt = record(value, "reminder attempt");
  return {
    historyType: "reminder_attempt",
    attemptId: nonNegativeInteger(attempt.attempt_id, "attempt_id") as number,
    outboxId: nonNegativeInteger(attempt.outbox_id, "outbox_id") as number,
    channel: text(attempt.channel, "channel"),
    attemptNo: nonNegativeInteger(attempt.attempt_no, "attempt_no") as number,
    status: text(attempt.status, "status"),
    attemptedAt: text(attempt.attempted_at, "attempted_at"),
    errorCode: optionalText(attempt.error_code),
    errorSummary: optionalText(attempt.error_summary),
  };
}

function readKnowledgeJob(value: unknown): KnowledgeJob {
  const job = record(value, "knowledge job");
  const status = text(job.status, "knowledge job status") as KnowledgeJobStatus;
  if (!KNOWLEDGE_JOB_STATUSES.has(status)) throw new Error("Nieznany status joba wiedzy.");
  return {
    historyType: "knowledge_job",
    jobId: nonNegativeInteger(job.job_id, "job_id") as number,
    jobType: text(job.job_type, "job_type"),
    status,
    attemptCount: nonNegativeInteger(job.attempt_count, "attempt_count") as number,
    maxAttempts: nonNegativeInteger(job.max_attempts, "max_attempts") as number,
    createdAt: text(job.created_at, "created_at"),
    startedAt: optionalText(job.started_at),
    finishedAt: optionalText(job.finished_at),
    durationMs: nonNegativeInteger(job.duration_ms, "duration_ms", true),
    errorCode: optionalText(job.error_code),
    errorSummary: optionalText(job.error_summary),
  };
}

function readEmailImportRun(value: unknown): EmailImportRun {
  const run = record(value, "email import run");
  const resultStatus = text(run.result_status, "email import result status") as EmailImportResultStatus;
  const status = text(run.status, "email import status") as AutomationRunStatus;
  const triggerMode = text(run.trigger_mode, "email import trigger mode") as "manual" | "automatic";
  if (!EMAIL_IMPORT_RESULT_STATUSES.has(resultStatus) || !RUN_STATUSES.has(status)) throw new Error("Nieznany status importu e-mail.");
  if (triggerMode !== "manual" && triggerMode !== "automatic") throw new Error("Nieznany tryb importu e-mail.");
  return {
    historyType: "email_import_run",
    runId: nonNegativeInteger(run.run_id, "run_id") as number,
    triggerMode,
    resultStatus,
    status,
    startedAt: optionalText(run.started_at),
    finishedAt: optionalText(run.finished_at),
    durationMs: nonNegativeInteger(run.duration_ms, "duration_ms", true),
    checkedMessageCount: nonNegativeInteger(run.checked_message_count, "checked_message_count") as number,
    matchedMessageCount: nonNegativeInteger(run.matched_message_count, "matched_message_count") as number,
    matchedAttachmentCount: nonNegativeInteger(run.matched_attachment_count, "matched_attachment_count") as number,
    importedCount: nonNegativeInteger(run.imported_count, "imported_count") as number,
    duplicateCount: nonNegativeInteger(run.duplicate_count, "duplicate_count") as number,
    failedCount: nonNegativeInteger(run.failed_count, "failed_count") as number,
    errorCode: optionalText(run.error_code),
    errorSummary: optionalText(run.error_summary),
  };
}

function readKSeFImportRun(value: unknown): KSeFImportRun {
  const run = record(value, "KSeF import run");
  const resultStatus = text(run.result_status, "KSeF import result status") as KSeFImportResultStatus;
  const status = text(run.status, "KSeF import status") as AutomationRunStatus;
  const triggerMode = text(run.trigger_mode, "KSeF import trigger mode") as "manual" | "automatic";
  if (!EMAIL_IMPORT_RESULT_STATUSES.has(resultStatus) || !RUN_STATUSES.has(status)) throw new Error("Nieznany status importu KSeF.");
  if (triggerMode !== "manual" && triggerMode !== "automatic") throw new Error("Nieznany tryb importu KSeF.");
  return {
    historyType: "ksef_import_run",
    runId: nonNegativeInteger(run.run_id, "run_id") as number,
    triggerMode,
    resultStatus,
    status,
    startedAt: optionalText(run.started_at),
    finishedAt: optionalText(run.finished_at),
    durationMs: nonNegativeInteger(run.duration_ms, "duration_ms", true),
    checkedDocumentCount: nonNegativeInteger(run.checked_document_count, "checked_document_count") as number,
    importedCount: nonNegativeInteger(run.imported_count, "imported_count") as number,
    duplicateCount: nonNegativeInteger(run.duplicate_count, "duplicate_count") as number,
    failedCount: nonNegativeInteger(run.failed_count, "failed_count") as number,
    errorCode: optionalText(run.error_code),
    errorSummary: optionalText(run.error_summary),
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
    history: root.history.map((entry) => {
      const historyType = record(entry, "history").history_type;
      if (historyType === "reminder_attempt") return readReminderAttempt(entry);
      if (historyType === "knowledge_job") return readKnowledgeJob(entry);
      if (historyType === "email_import_run") return readEmailImportRun(entry);
      if (historyType === "ksef_import_run") return readKSeFImportRun(entry);
      return readRun(entry);
    }),
    outbox: Array.isArray(root.outbox) ? root.outbox.map((entry) => {
      const item = record(entry, "outbox");
      return {
        outboxId: nonNegativeInteger(item.task_reminder_outbox_id, "outbox_id") as number,
        status: text(item.status, "status"),
        channel: text(item.delivery_channel, "delivery_channel"),
        availableAt: optionalText(item.available_at),
        attemptCount: nonNegativeInteger(item.attempt_count, "attempt_count") as number,
        createdAt: text(item.created_at, "created_at"),
        updatedAt: text(item.updated_at, "updated_at"),
      };
    }) : [],
    watchers: Array.isArray(root.watchers) ? root.watchers.map((entry) => {
      const watcher = record(entry, "knowledge watcher");
      return {
        watcherId: nonNegativeInteger(watcher.watcher_id, "watcher_id") as number,
        watchMode: text(watcher.watch_mode, "watch_mode"),
        status: text(watcher.status, "watcher status"),
        lastScanStartedAt: optionalText(watcher.last_scan_started_at),
        lastScanCompletedAt: optionalText(watcher.last_scan_completed_at),
        errorCode: optionalText(watcher.error_code),
        errorSummary: optionalText(watcher.error_summary),
      };
    }) : [],
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

export function automationConfigurationLabel(status: AutomationConfigurationStatus): string {
  if (status === "enabled") return "Włączona";
  if (status === "disabled") return "Wyłączona";
  return "Nieskonfigurowana";
}

export function automationTypeLabel(automationType: string): string {
  if (automationType === "email_import" || automationType === "ksef_import") return "Źródło operacyjne";
  if (automationType === "task_reminders") return "Przypomnienia";
  if (automationType === "knowledge_processing") return "Przetwarzanie wiedzy";
  return "Harmonogram";
}

export function emailImportResultLabel(status: EmailImportResultStatus): string {
  if (status === "completed") return "Zakończony";
  if (status === "completed_with_issues") return "Zakończony z uwagami";
  if (status === "no_new_documents") return "Brak nowych wiadomości";
  if (status === "failed") return "Błąd";
  return "W toku";
}

export function emailImportTriggerLabel(mode: "manual" | "automatic"): string {
  return mode === "automatic" ? "Automatyczny" : "Ręczny";
}

export function ksefImportResultLabel(status: KSeFImportResultStatus): string {
  if (status === "no_new_documents") return "Brak nowych dokumentów";
  return emailImportResultLabel(status);
}
