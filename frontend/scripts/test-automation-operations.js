const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const ts = require("typescript");

require.extensions[".ts"] = function compileTypeScript(module, filename) {
  const output = ts.transpileModule(fs.readFileSync(filename, "utf8"), {
    compilerOptions: { esModuleInterop: true, module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
    fileName: filename,
  });
  module._compile(output.outputText, filename);
};

const model = require("../src/modules/automations/automationOperationsModel.ts");

function operation(overrides = {}) {
  return {
    automation_key: "internal_notification_scheduler",
    automation_type: "scheduler",
    title: "Automatyczne sprawdzanie powiadomień",
    description: "Opis",
    status: "enabled",
    enabled: true,
    health: "healthy",
    health_reason_code: "last_run_succeeded",
    schedule_id: 1,
    run_id: 2,
    next_run_at: "2026-01-16T07:00:00+00:00",
    last_run_at: "2026-01-15T07:00:00+00:00",
    last_run_status: "succeeded",
    last_run_duration_ms: 1000,
    last_attempt_count: 1,
    last_candidates_count: 4,
    last_created_count: 2,
    last_existing_count: 2,
    recent_failure_count: 0,
    last_error_code: null,
    last_error_summary: null,
    settings_url: "/powiadomienia",
    details_url: "/automatyzacje/internal_notification_scheduler",
    runtime_status: "unknown",
    schedule: { cadence: "daily", timezone_name: "Europe/Warsaw", local_time: "08:00" },
    updated_at: "2026-01-15T07:00:01+00:00",
    ...overrides,
  };
}

const parsed = model.readAutomationOperationsDashboard({
  summary: { active_count: 2, disabled_count: 2, attention_count: 1, recent_failure_count: 3 },
  attention_items: [],
  items: [
    operation(),
    operation({ automation_key: "failed", status: "enabled", health: "attention" }),
    operation({ automation_key: "disabled", status: "disabled", enabled: false, health: "disabled" }),
    operation({ automation_key: "new", status: "not_configured", enabled: false, health: "disabled" }),
  ],
});
assert.equal(parsed.items.length, 4);
assert.deepEqual(model.buildAutomationOperationsPresentationSummary(parsed.items), {
  activeCount: 2, notConfiguredCount: 1, disabledCount: 1, attentionCount: 1,
});
assert.deepEqual(model.filterAutomationOperations(parsed.items, "not_configured").map((item) => item.automationKey), ["new"]);
assert.deepEqual(model.filterAutomationOperations(parsed.items, "disabled").map((item) => item.automationKey), ["disabled"]);
assert.deepEqual(model.filterAutomationOperations(parsed.items, "attention").map((item) => item.automationKey), ["failed"]);
assert.equal(model.AUTOMATION_OPERATIONS_POLL_INTERVAL, null);
assert.equal(model.automationHealthLabel("never_run"), "Jeszcze nie uruchomiono");

const reminders = operation({
  automation_key: "task_reminders", automation_type: "task_reminders", title: "Przypomnienia zadań",
  description: "Kolejka", status: "enabled", enabled: true, health: "attention", health_reason_code: "failed_outbox_present",
  schedule_id: null, run_id: null, next_run_at: null, last_run_at: "2026-01-15T07:01:00+00:00", last_run_status: "failed",
  last_run_duration_ms: null, last_attempt_count: 2, last_candidates_count: null, last_created_count: null, last_existing_count: null,
  disabled_reason: null, last_activity_at: "2026-01-15T07:01:00+00:00", last_attempt_at: "2026-01-15T07:01:00+00:00",
  last_attempt_status: "dead_letter", pending_count: 1, processing_count: 0, failed_count: 1, sent_count: 3, cancelled_count: 0,
  last_heartbeat_at: "2026-01-15T07:00:00+00:00", settings_url: null, details_url: "/automatyzacje/task_reminders", schedule: null,
  last_error_code: "task_reminder_delivery_failed", last_error_summary: "Bezpieczny błąd",
});
const multi = model.readAutomationOperationsDashboard({ summary: { active_count: 2, disabled_count: 0, attention_count: 1, recent_failure_count: 1 }, attention_items: [], items: [operation(), reminders] });
assert.equal(multi.items.length, 2);
assert.equal(multi.items[1].pendingCount, 1);
assert.equal(multi.items[1].settingsUrl, null);

const knowledge = operation({
  automation_key: "knowledge_processing", automation_type: "knowledge_processing", title: "Przetwarzanie bazy wiedzy",
  description: "Kolejka wiedzy", health: "attention", health_reason_code: "last_job_failed", schedule_id: null,
  run_id: 13, next_run_at: null, last_run_at: "2026-02-13T10:00:00+00:00", last_run_status: "failed",
  last_run_duration_ms: 2500, last_attempt_count: 1, last_candidates_count: null, last_created_count: null,
  last_existing_count: null, settings_url: null, details_url: "/automatyzacje/knowledge_processing", schedule: null,
  last_activity_at: "2026-02-13T10:01:00+00:00", last_job_at: "2026-02-13T10:00:00+00:00",
  last_job_status: "failed", last_success_at: "2026-02-12T10:00:00+00:00", last_failure_at: "2026-02-13T10:00:00+00:00",
  pending_count: 1, processing_count: 1, succeeded_count: 4, failed_count: 1, watcher_count: 1,
  last_scan_at: "2026-02-13T10:01:00+00:00", last_scan_status: "ok", last_error_code: "knowledge_processing_failed",
  last_error_summary: "Błąd wykonania. Szczegóły techniczne zostały ukryte.",
});
const emailImport = operation({
  automation_key: "email_import", automation_type: "email_import", title: "Import e-maili",
  description: "Bezpieczny monitoring importu", health: "attention", health_reason_code: "last_email_import_run_requires_attention",
  schedule_id: null, run_id: 21, next_run_at: null, last_run_at: "2026-03-11T10:00:00+00:00", last_run_status: "failed",
  last_run_duration_ms: 2000, last_attempt_count: null, last_candidates_count: 4, last_created_count: 2,
  last_existing_count: 1, settings_url: "/ustawienia", details_url: "/automatyzacje/email_import", schedule: null,
  last_activity_at: "2026-03-11T10:00:00+00:00", last_success_at: "2026-03-10T10:00:00+00:00",
  last_failure_at: "2026-03-11T10:00:00+00:00", checked_message_count: 7, matched_message_count: 5,
  matched_attachment_count: 4, imported_count: 2, duplicate_count: 1, failed_count: 1,
  total_imported_count: 8, total_duplicate_count: 3, total_failed_count: 1, runs_count: 4,
  configured_connections_count: 1, enabled_connections_count: 1, last_error_code: "email_import_completed_with_issues",
  last_error_summary: "Część dokumentów z importu e-mail wymaga uwagi.",
});
const ksefImport = operation({
  automation_key: "ksef_import", automation_type: "ksef_import", title: "Import KSeF",
  description: "Bezpieczny monitoring importu KSeF", health: "attention", health_reason_code: "last_ksef_import_run_requires_attention",
  schedule_id: null, run_id: 31, next_run_at: null, last_run_at: "2026-04-11T10:00:00+00:00", last_run_status: "failed",
  last_run_duration_ms: 2000, last_attempt_count: null, last_candidates_count: 7, last_created_count: 2,
  last_existing_count: 1, settings_url: "/ustawienia", details_url: "/automatyzacje/ksef_import", schedule: null,
  last_activity_at: "2026-04-11T10:00:00+00:00", last_success_at: "2026-04-10T10:00:00+00:00",
  last_failure_at: "2026-04-11T10:00:00+00:00", checked_document_count: 7,
  imported_count: 2, duplicate_count: 1, failed_count: 1, total_imported_count: 8, total_duplicate_count: 3,
  total_failed_count: 1, runs_count: 4, configured_connections_count: 1, enabled_connections_count: 1,
  last_error_code: "ksef_import_completed_with_issues", last_error_summary: "Część dokumentów z importu KSeF wymaga uwagi.",
});
const automationEngine = operation({
  automation_key: "automation_engine", automation_type: "automation_engine", title: "Reguły automatyzacji",
  description: "Bezpieczny monitoring reguł", health: "attention", health_reason_code: "last_execution_failed",
  schedule_id: null, run_id: 41, next_run_at: null, last_run_at: "2026-05-11T10:00:00+00:00", last_run_status: "failed",
  last_run_duration_ms: null, last_attempt_count: null, last_candidates_count: null, last_created_count: null,
  last_existing_count: null, settings_url: null, details_url: "/automatyzacje/automation_engine", schedule: null,
  last_activity_at: "2026-05-11T10:00:00+00:00", last_success_at: "2026-05-10T10:00:00+00:00",
  last_failure_at: "2026-05-11T10:00:00+00:00", enabled_rules_count: 2, disabled_rules_count: 1,
  total_rules_count: 3, executions_count: 7, succeeded_count: 6, failed_count: 1,
  last_error_code: "automation_execution_failed", last_error_summary: "Ostatnie wykonanie reguły automatyzacji zakończyło się błędem.",
});
const sixAdapters = model.readAutomationOperationsDashboard({
  summary: { active_count: 6, disabled_count: 0, attention_count: 5, recent_failure_count: 5 },
  attention_items: [
    { automation_key: "automation_engine", title: "Reguły automatyzacji", attention_category: "execution", reason_code: "last_execution_failed", occurred_at: "2026-05-11T10:00:00+00:00", summary: "Ostatnie wykonanie zakończyło się błędem.", details_url: "/automatyzacje/automation_engine", settings_url: null },
    { automation_key: "email_import", title: "Import e-maili", attention_category: "configuration", reason_code: "system_mailbox_not_configured", occurred_at: null, summary: "Brakuje konfiguracji systemowej.", details_url: "/automatyzacje/email_import", settings_url: "/ustawienia" },
  ],
  items: [operation(), reminders, knowledge, emailImport, ksefImport, automationEngine],
});
assert.deepEqual(sixAdapters.items.map((item) => item.automationKey), ["internal_notification_scheduler", "task_reminders", "knowledge_processing", "email_import", "ksef_import", "automation_engine"]);
assert.equal(sixAdapters.items[2].watcherCount, 1);
assert.equal(sixAdapters.items[2].succeededCount, 4);
assert.equal(sixAdapters.items[3].configuredConnectionsCount, 1);
assert.equal(sixAdapters.items[4].checkedDocumentCount, 7);
assert.equal(sixAdapters.items[5].enabledRulesCount, 2);
assert.equal(sixAdapters.items[5].executionsCount, 7);
assert.deepEqual(sixAdapters.attentionItems.map((item) => item.automationKey), ["automation_engine", "email_import"]);
assert.equal(sixAdapters.attentionItems[0].attentionCategory, "execution");
assert.equal(sixAdapters.attentionItems[1].occurredAt, null);
assert.equal(sixAdapters.attentionItems[1].settingsUrl, "/ustawienia");
assert.equal(model.automationAttentionCategoryLabel("configuration"), "Konfiguracja");
assert.equal(model.automationAttentionCategoryLabel("execution"), "Wykonanie");
assert.equal(model.automationAttentionCategoryLabel("backlog"), "Kolejka");
assert.equal(model.automationTypeLabel("automation_engine"), "Silnik reguł");
assert.equal(model.automationTypeLabel("email_import"), "Źródło operacyjne");
assert.equal(model.automationTypeLabel("ksef_import"), "Źródło operacyjne");
assert.equal(model.emailImportResultLabel("no_new_documents"), "Brak nowych wiadomości");
assert.equal(model.ksefImportResultLabel("no_new_documents"), "Brak nowych dokumentów");
const ksefStates = model.readAutomationOperationsDashboard({
  summary: { active_count: 3, disabled_count: 1, attention_count: 1, recent_failure_count: 1 },
  attention_items: [],
  items: [
    { ...ksefImport, automation_key: "ksef_disabled", status: "disabled", enabled: false, health: "disabled", health_reason_code: "ksef_import_disabled" },
    { ...ksefImport, automation_key: "ksef_never", health: "never_run", health_reason_code: "no_terminal_ksef_import_run", run_id: null, last_run_at: null, last_run_status: null },
    { ...ksefImport, automation_key: "ksef_healthy", health: "healthy", health_reason_code: "last_ksef_import_run_succeeded", last_run_status: "succeeded", last_error_code: null, last_error_summary: null },
    ksefImport,
  ],
});
assert.equal(model.filterAutomationOperations(ksefStates.items, "disabled").length, 1);
assert.equal(model.filterAutomationOperations(ksefStates.items, "attention").length, 1);
const knowledgeStates = model.readAutomationOperationsDashboard({
  summary: { active_count: 3, disabled_count: 1, attention_count: 1, recent_failure_count: 1 },
  attention_items: [],
  items: [
    knowledge,
    { ...knowledge, automation_key: "knowledge_never", health: "never_run", health_reason_code: "no_terminal_job" },
    { ...knowledge, automation_key: "knowledge_healthy", health: "healthy", health_reason_code: "last_job_completed" },
    { ...knowledge, automation_key: "knowledge_disabled", status: "disabled", enabled: false, health: "disabled", health_reason_code: "runtime_disabled" },
  ],
});
assert.equal(model.filterAutomationOperations(knowledgeStates.items, "disabled").length, 1);
assert.equal(model.filterAutomationOperations(knowledgeStates.items, "attention").length, 1);
assert.equal(model.automationTechnicalStatusLabel("dead_letter"), "Zakończone niepowodzeniem");
assert.equal(model.automationTechnicalStatusLabel("retry"), "Oczekuje na ponowienie");
assert.equal(model.automationTechnicalStatusLabel("unknown-provider-state"), "Inny stan techniczny");
assert.equal(model.automationKnowledgeJobTypeLabel("ingest"), "Dodanie dokumentu");
assert.equal(model.automationKnowledgeJobTypeLabel("replace"), "Aktualizacja dokumentu");
assert.equal(model.automationWatcherModeLabel("polling"), "Cykliczne skanowanie");
assert.equal(model.automationScheduleCadenceLabel("daily"), "Codziennie");
assert.deepEqual(model.automationNavigationLinks("task_reminders"), [{ href: "/work-items", label: "Przejdź do zadań" }]);
assert.deepEqual(model.automationNavigationLinks("knowledge_processing"), [{ href: "/dokumenty", label: "Przejdź do dokumentów" }]);
assert.deepEqual(model.automationNavigationLinks("email_import"), []);
assert.deepEqual(model.automationNavigationLinks("ksef_import"), []);
assert.deepEqual(model.automationNavigationLinks("automation_engine"), []);
assert.match(model.automationDescription(parsed.items[0]), /sygnałów rozliczeniowych/);
assert.doesNotMatch(model.automationDescription(parsed.items[0]), /billing attention/i);
assert.match(model.automationDescription(sixAdapters.items[5]), /danych działań/);
assert.doesNotMatch(model.automationDescription(sixAdapters.items[5]), /payload/i);

const detail = model.readAutomationOperationDetail({
  item: operation(),
  history_limit: 20,
  history: [{
    run_id: 2, schedule_id: 1, scheduled_local_date: "2026-01-15", as_of_date: "2026-01-15",
    scheduled_for_utc: "2026-01-15T07:00:00+00:00", status: "succeeded", attempt_count: 1,
    candidates_count: 4, created_count: 2, existing_count: 2, error_code: null, error_summary: null,
    started_at: "2026-01-15T07:00:00+00:00", finished_at: "2026-01-15T07:00:01+00:00", duration_ms: 1000,
  }],
});
assert.equal(detail.history[0].durationMs, 1000);
const reminderDetail = model.readAutomationOperationDetail({ item: reminders, history_limit: 20, history: [{
  history_type: "reminder_attempt", attempt_id: 9, outbox_id: 8, channel: "telegram", attempt_no: 2,
  status: "dead_letter", attempted_at: "2026-01-15T07:01:00+00:00", error_code: "task_reminder_delivery_failed", error_summary: "Bezpieczny błąd",
}], outbox: [{ task_reminder_outbox_id: 8, status: "failed", delivery_channel: "telegram", available_at: "2026-01-15T07:00:00+00:00", attempt_count: 2, created_at: "2026-01-15T07:00:00+00:00", updated_at: "2026-01-15T07:01:00+00:00" }] });
assert.equal(reminderDetail.history[0].historyType, "reminder_attempt");
assert.equal(reminderDetail.outbox[0].status, "failed");
const knowledgeDetail = model.readAutomationOperationDetail({ item: knowledge, history_limit: 20, history: [{
  history_type: "knowledge_job", job_id: 13, job_type: "replace", status: "failed", attempt_count: 1, max_attempts: 3,
  created_at: "2026-02-13T09:59:00+00:00", started_at: "2026-02-13T10:00:00+00:00",
  finished_at: "2026-02-13T10:00:02.500+00:00", duration_ms: 2500,
  error_code: "knowledge_processing_failed", error_summary: "Błąd wykonania. Szczegóły techniczne zostały ukryte.",
}], watchers: [{ watcher_id: 2, watch_mode: "polling", status: "ok", last_scan_started_at: "2026-02-13T10:00:00+00:00", last_scan_completed_at: "2026-02-13T10:01:00+00:00", error_code: null, error_summary: null }] });
assert.equal(knowledgeDetail.history[0].historyType, "knowledge_job");
assert.equal(knowledgeDetail.watchers[0].status, "ok");
const emailDetail = model.readAutomationOperationDetail({ item: emailImport, history_limit: 20, history: [{
  history_type: "email_import_run", run_id: 21, trigger_mode: "automatic", result_status: "completed_with_issues",
  status: "failed", started_at: "2026-03-11T09:59:58+00:00", finished_at: "2026-03-11T10:00:00+00:00",
  duration_ms: 2000, checked_message_count: 7, matched_message_count: 5, matched_attachment_count: 4,
  imported_count: 2, duplicate_count: 1, failed_count: 1, error_code: "email_import_completed_with_issues",
  error_summary: "Część dokumentów z importu e-mail wymaga uwagi.",
}] });
assert.equal(emailDetail.history[0].historyType, "email_import_run");
assert.equal(emailDetail.history[0].importedCount, 2);
const ksefDetail = model.readAutomationOperationDetail({ item: ksefImport, history_limit: 20, history: [{
  history_type: "ksef_import_run", run_id: 31, trigger_mode: "manual", result_status: "completed_with_issues",
  status: "failed", started_at: "2026-04-11T09:59:58+00:00", finished_at: "2026-04-11T10:00:00+00:00",
  duration_ms: 2000, checked_document_count: 7, imported_count: 2, duplicate_count: 1,
  failed_count: 1, error_code: "ksef_import_completed_with_issues", error_summary: "Część dokumentów z importu KSeF wymaga uwagi.",
}] });
assert.equal(ksefDetail.history[0].historyType, "ksef_import_run");
assert.equal(ksefDetail.history[0].checkedDocumentCount, 7);
const engineDetail = model.readAutomationOperationDetail({ item: automationEngine, history_limit: 20, history: [{
  history_type: "automation_execution", execution_id: 41, rule_id: 12, status: "failed",
  executed_at: "2026-05-11T10:00:00+00:00", error_code: "automation_execution_failed",
  error_summary: "Wykonanie reguły automatyzacji zakończyło się błędem.",
}], rules: [{ rule_id: 12, title: "Reguła #12", enabled: true, execution_count: 7, created_at: "2026-05-01T10:00:00+00:00", updated_at: "2026-05-11T10:00:00+00:00" }] });
assert.equal(engineDetail.history[0].historyType, "automation_execution");
assert.equal(engineDetail.rules[0].title, "Reguła #12");
assert.doesNotMatch(JSON.stringify(engineDetail), /trigger|actions_json|input_json|result_json|traceback|customer@|token/i);
assert.doesNotMatch(JSON.stringify(ksefDetail), /nip|invoice_number|amount|xml|upo|ksef_number|token|certificate/i);
assert.doesNotMatch(JSON.stringify(emailDetail), /subject|sender|recipient|message_id|attachment_name|credentials|token|body/i);
assert.doesNotMatch(JSON.stringify(knowledgeDetail), /source_storage_key|source_file_name|content_text|ocr|c:\\users/i);
assert.doesNotMatch(JSON.stringify(reminderDetail), /payload|secret|token/i);
assert.throws(() => model.readAutomationOperationsDashboard({ summary: {}, attention_items: [], items: [] }), /kontrakt/i);
assert.throws(() => model.readAutomationOperationsDashboard({ summary: { active_count: 0, disabled_count: 0, attention_count: 0, recent_failure_count: 0 }, attention_items: [], items: [operation({ settings_url: "https://evil.test" })] }), /bezpieczny link/i);
assert.throws(() => model.readAutomationOperationsDashboard({ summary: { active_count: 0, disabled_count: 0, attention_count: 1, recent_failure_count: 0 }, attention_items: [{ automation_key: "x", title: "X", attention_category: "critical", reason_code: "x", occurred_at: null, summary: "X", details_url: "/automatyzacje/x", settings_url: null }], items: [] }), /attention_category/i);
assert.throws(() => model.readAutomationOperationsDashboard({ summary: { active_count: 0, disabled_count: 0, attention_count: 1, recent_failure_count: 0 }, attention_items: [{ automation_key: "x", title: "X", attention_category: "execution", reason_code: "x", occurred_at: null, summary: "X", details_url: "https://evil.test", settings_url: null }], items: [] }), /bezpieczny link/i);

const apiSource = fs.readFileSync(path.join(__dirname, "..", "src", "lib", "api.ts"), "utf8");
const pageSource = fs.readFileSync(path.join(__dirname, "..", "src", "modules", "automations", "AutomationOperationsPage.tsx"), "utf8");
const detailSource = fs.readFileSync(path.join(__dirname, "..", "src", "modules", "automations", "AutomationOperationDetailPage.tsx"), "utf8");
const navigationSource = fs.readFileSync(path.join(__dirname, "..", "src", "config", "navigation.ts"), "utf8");
assert.match(apiSource, /automationOperations:[\s\S]*apiRequest[\s\S]*\/automations\/operations/);
assert.doesNotMatch(pageSource + detailSource, /setInterval|Uruchom teraz|Importuj teraz|Pobierz faktury|Ponów|Skanuj teraz|Reprocess|Run now|Scan now|method:\s*["']POST["']/);
assert.doesNotMatch(pageSource + detailSource, />\s*email_import\s*</);
assert.doesNotMatch(pageSource + detailSource, />\s*ksef_import\s*</);
assert.doesNotMatch(pageSource + detailSource, />\s*automation_engine\s*</);
assert.match(pageSource, /setDashboard\(null\)/);
assert.match(detailSource, /Monitoring procesu/);
assert.match(detailSource, /Brak monitoringu procesu/);
assert.doesNotMatch(pageSource, />Runtime</);
assert.match(navigationSource, /id:\s*["']automations["'][\s\S]*label:\s*["']Automatyzacje["'][\s\S]*path:\s*["']\/automatyzacje["']/);
assert.doesNotMatch(JSON.stringify(parsed), /recipient_user_id|lease_token/);

console.log("Automation operations model tests passed.");
