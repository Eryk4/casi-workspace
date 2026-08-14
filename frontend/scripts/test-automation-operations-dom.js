const assert = require("node:assert/strict");
const fs = require("node:fs");
const Module = require("node:module");
const path = require("node:path");
const ts = require("typescript");
const { JSDOM } = require("jsdom");

for (const extension of [".ts", ".tsx"]) {
  require.extensions[extension] = function compileTypeScript(module, filename) {
    const output = ts.transpileModule(fs.readFileSync(filename, "utf8"), {
      compilerOptions: { esModuleInterop: true, jsx: ts.JsxEmit.ReactJSX, module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 }, fileName: filename,
    });
    module._compile(output.outputText, filename);
  };
}

const srcRoot = path.join(__dirname, "..", "src");
const originalResolveFilename = Module._resolveFilename;
Module._resolveFilename = function resolveAlias(request, parent, isMain, options) {
  if (request.startsWith("@/")) {
    const resolved = path.join(srcRoot, request.slice(2));
    return [".ts", ".tsx", ".js", ".jsx"].map((extension) => `${resolved}${extension}`).find(fs.existsSync) ?? resolved;
  }
  return originalResolveFilename.call(this, request, parent, isMain, options);
};

let organizationId = "42";
let failDashboard = false;
let detailNotFound = false;
let emptyAttention = false;
let dashboardCalls = 0;
const operation = {
  automation_key: "internal_notification_scheduler", automation_type: "scheduler", title: "Automatyczne sprawdzanie powiadomień", description: "Opis operacyjny",
  status: "enabled", enabled: true, health: "attention", health_reason_code: "last_run_failed", schedule_id: 1, run_id: 2,
  next_run_at: "2026-01-16T07:00:00+00:00", last_run_at: "2026-01-15T07:00:00+00:00", last_run_status: "failed", last_run_duration_ms: 1000,
  last_attempt_count: 2, last_candidates_count: 7, last_created_count: 3, last_existing_count: 4, recent_failure_count: 1,
  last_error_code: "materialization_failed", last_error_summary: "Bezpieczne podsumowanie błędu", settings_url: "/powiadomienia",
  details_url: "/automatyzacje/internal_notification_scheduler", runtime_status: "unknown", schedule: { cadence: "daily", timezone_name: "Europe/Warsaw", local_time: "08:00" }, updated_at: "2026-01-15T07:00:01+00:00",
};
const reminderOperation = {
  ...operation, automation_key: "task_reminders", automation_type: "task_reminders", title: "Przypomnienia zadań", description: "Kolejka przypomnień",
  health: "attention", health_reason_code: "failed_outbox_present", schedule_id: null, run_id: null, next_run_at: null,
  last_run_duration_ms: null, last_candidates_count: null, last_created_count: null, last_existing_count: null, schedule: null, settings_url: null,
  disabled_reason: null, last_activity_at: "2026-01-15T07:01:00+00:00", last_attempt_at: "2026-01-15T07:01:00+00:00", last_attempt_status: "dead_letter",
  pending_count: 1, processing_count: 0, failed_count: 1, sent_count: 2, cancelled_count: 0, last_heartbeat_at: "2026-01-15T07:00:00+00:00",
  details_url: "/automatyzacje/task_reminders", last_error_summary: "Bezpieczny błąd przypomnienia",
};
const knowledgeOperation = {
  ...operation, automation_key: "knowledge_processing", automation_type: "knowledge_processing", title: "Przetwarzanie bazy wiedzy", description: "Kolejka przetwarzania dokumentów",
  health: "attention", health_reason_code: "last_job_failed", schedule_id: null, run_id: 13, next_run_at: null,
  last_run_at: "2026-02-13T10:00:00+00:00", last_run_status: "failed", last_run_duration_ms: 2500,
  last_attempt_count: 1, last_candidates_count: null, last_created_count: null, last_existing_count: null, schedule: null, settings_url: null,
  last_activity_at: "2026-02-13T10:01:00+00:00", last_job_at: "2026-02-13T10:00:00+00:00", last_job_status: "failed",
  last_success_at: "2026-02-12T10:00:00+00:00", last_failure_at: "2026-02-13T10:00:00+00:00",
  pending_count: 1, processing_count: 1, succeeded_count: 4, failed_count: 1, watcher_count: 1,
  last_scan_at: "2026-02-13T10:01:00+00:00", last_scan_status: "ok", last_error_code: "knowledge_processing_failed",
  last_error_summary: "Błąd wykonania. Szczegóły techniczne zostały ukryte.", details_url: "/automatyzacje/knowledge_processing",
};
const emailImportOperation = {
  ...operation, automation_key: "email_import", automation_type: "email_import", title: "Import e-maili", description: "Bezpieczny monitoring importu",
  status: "not_configured", enabled: false,
  health: "attention", health_reason_code: "last_email_import_run_requires_attention", schedule_id: null, run_id: 21, next_run_at: null,
  last_run_at: "2026-03-11T10:00:00+00:00", last_run_status: "failed", last_run_duration_ms: 2000,
  last_attempt_count: null, last_candidates_count: 4, last_created_count: 2, last_existing_count: 1, schedule: null,
  settings_url: "/ustawienia", details_url: "/automatyzacje/email_import", last_activity_at: "2026-03-11T10:00:00+00:00",
  last_success_at: "2026-03-10T10:00:00+00:00", last_failure_at: "2026-03-11T10:00:00+00:00",
  checked_message_count: 7, matched_message_count: 5, matched_attachment_count: 4, imported_count: 2, duplicate_count: 1,
  failed_count: 1, total_imported_count: 8, total_duplicate_count: 3, total_failed_count: 1, runs_count: 4,
  configured_connections_count: 1, enabled_connections_count: 1, last_error_code: "email_import_completed_with_issues",
  last_error_summary: "Część dokumentów z importu e-mail wymaga uwagi.",
};
const ksefImportOperation = {
  ...operation, automation_key: "ksef_import", automation_type: "ksef_import", title: "Import KSeF", description: "Bezpieczny monitoring importu KSeF",
  status: "disabled", enabled: false, health: "disabled", health_reason_code: "ksef_import_disabled", schedule_id: null, run_id: 31, next_run_at: null,
  last_run_at: "2026-04-11T10:00:00+00:00", last_run_status: "failed", last_run_duration_ms: 2000,
  last_attempt_count: null, last_candidates_count: 7, last_created_count: 2, last_existing_count: 1, schedule: null,
  settings_url: "/ustawienia", details_url: "/automatyzacje/ksef_import", last_activity_at: "2026-04-11T10:00:00+00:00",
  last_success_at: "2026-04-10T10:00:00+00:00", last_failure_at: "2026-04-11T10:00:00+00:00",
  checked_document_count: 7, imported_count: 2, duplicate_count: 1, failed_count: 1,
  total_imported_count: 8, total_duplicate_count: 3, total_failed_count: 1, runs_count: 4,
  configured_connections_count: 1, enabled_connections_count: 1, last_error_code: "ksef_import_completed_with_issues",
  last_error_summary: "Część dokumentów z importu KSeF wymaga uwagi.",
};
const automationEngineOperation = {
  ...operation, automation_key: "automation_engine", automation_type: "automation_engine", title: "Reguły automatyzacji", description: "Bezpieczny monitoring reguł",
  health: "attention", health_reason_code: "last_execution_failed", schedule_id: null, run_id: 41, next_run_at: null,
  last_run_at: "2026-05-11T10:00:00+00:00", last_run_status: "failed", last_run_duration_ms: null,
  last_attempt_count: null, last_candidates_count: null, last_created_count: null, last_existing_count: null, schedule: null,
  settings_url: null, details_url: "/automatyzacje/automation_engine", last_activity_at: "2026-05-11T10:00:00+00:00",
  last_success_at: "2026-05-10T10:00:00+00:00", last_failure_at: "2026-05-11T10:00:00+00:00",
  enabled_rules_count: 2, disabled_rules_count: 1, total_rules_count: 3, executions_count: 7, succeeded_count: 6, failed_count: 1,
  last_error_code: "automation_execution_failed", last_error_summary: "Ostatnie wykonanie reguły automatyzacji zakończyło się błędem.",
};
const attentionItems = [
  { automation_key: "automation_engine", title: "Reguły automatyzacji", attention_category: "execution", reason_code: "last_execution_failed", occurred_at: "2026-05-11T10:00:00+00:00", summary: "Ostatnie wykonanie reguły automatyzacji zakończyło się błędem.", details_url: "/automatyzacje/automation_engine", settings_url: null },
  { automation_key: "task_reminders", title: "Przypomnienia zadań", attention_category: "backlog", reason_code: "failed_outbox_present", occurred_at: "2026-01-15T07:01:00+00:00", summary: "Co najmniej jedno przypomnienie wymaga sprawdzenia po nieudanej wysyłce.", details_url: "/automatyzacje/task_reminders", settings_url: null },
  { automation_key: "email_import", title: "Import e-maili", attention_category: "configuration", reason_code: "system_mailbox_not_configured", occurred_at: null, summary: "Brakuje konfiguracji systemowej skrzynki importu e-maili.", details_url: "/automatyzacje/email_import", settings_url: "/ustawienia" },
];
const api = {
  automationOperationsActivity: async () => ({ items: [], limit: 8 }),
  automationOperations: async (query) => {
    dashboardCalls += 1;
    if (failDashboard) throw new Error("Kontrolowany błąd centrum");
    if (String(query.organization_id) !== organizationId) throw new Error("Stary scope organizacji");
    return { summary: { active_count: 6, disabled_count: 0, attention_count: emptyAttention ? 0 : attentionItems.length, recent_failure_count: 6 }, attention_items: emptyAttention ? [] : attentionItems, items: [operation, reminderOperation, knowledgeOperation, emailImportOperation, ksefImportOperation, automationEngineOperation] };
  },
  automationOperationDetail: async (automationKey) => {
    if (detailNotFound) throw new ApiError("Nie znaleziono", 404, {});
    if (automationKey === "task_reminders") return { item: reminderOperation, history_limit: 20, history: [{ history_type: "reminder_attempt", attempt_id: 9, outbox_id: 8, channel: "telegram", attempt_no: 2, status: "dead_letter", attempted_at: "2026-01-15T07:01:00+00:00", error_code: "task_reminder_delivery_failed", error_summary: "Bezpieczny błąd przypomnienia" }], outbox: [{ task_reminder_outbox_id: 8, status: "failed", delivery_channel: "telegram", available_at: "2026-01-15T07:00:00+00:00", attempt_count: 2, created_at: "2026-01-15T07:00:00+00:00", updated_at: "2026-01-15T07:01:00+00:00" }] };
    if (automationKey === "knowledge_processing") return { item: knowledgeOperation, history_limit: 20, history: [{ history_type: "knowledge_job", job_id: 13, job_type: "replace", status: "failed", attempt_count: 1, max_attempts: 3, created_at: "2026-02-13T09:59:00+00:00", started_at: "2026-02-13T10:00:00+00:00", finished_at: "2026-02-13T10:00:02.500+00:00", duration_ms: 2500, error_code: "knowledge_processing_failed", error_summary: "Błąd wykonania. Szczegóły techniczne zostały ukryte." }], watchers: [{ watcher_id: 2, watch_mode: "polling", status: "ok", last_scan_started_at: "2026-02-13T10:00:00+00:00", last_scan_completed_at: "2026-02-13T10:01:00+00:00", error_code: null, error_summary: null }] };
    if (automationKey === "email_import") return { item: emailImportOperation, history_limit: 20, history: [{ history_type: "email_import_run", run_id: 21, trigger_mode: "automatic", result_status: "completed_with_issues", status: "failed", started_at: "2026-03-11T09:59:58+00:00", finished_at: "2026-03-11T10:00:00+00:00", duration_ms: 2000, checked_message_count: 7, matched_message_count: 5, matched_attachment_count: 4, imported_count: 2, duplicate_count: 1, failed_count: 1, error_code: "email_import_completed_with_issues", error_summary: "Część dokumentów z importu e-mail wymaga uwagi." }] };
    if (automationKey === "ksef_import") return { item: ksefImportOperation, history_limit: 20, history: [{ history_type: "ksef_import_run", run_id: 31, trigger_mode: "manual", result_status: "completed_with_issues", status: "failed", started_at: "2026-04-11T09:59:58+00:00", finished_at: "2026-04-11T10:00:00+00:00", duration_ms: 2000, checked_document_count: 7, imported_count: 2, duplicate_count: 1, failed_count: 1, error_code: "ksef_import_completed_with_issues", error_summary: "Część dokumentów z importu KSeF wymaga uwagi." }] };
    if (automationKey === "automation_engine") return { item: automationEngineOperation, history_limit: 20, history: [{ history_type: "automation_execution", execution_id: 41, rule_id: 12, status: "failed", executed_at: "2026-05-11T10:00:00+00:00", error_code: "automation_execution_failed", error_summary: "Wykonanie reguły automatyzacji zakończyło się błędem." }], rules: [{ rule_id: 12, title: "Reguła #12", enabled: true, execution_count: 7, created_at: "2026-05-01T10:00:00+00:00", updated_at: "2026-05-11T10:00:00+00:00" }] };
    return { item: operation, history_limit: 20, history: [{ run_id: 2, schedule_id: 1, scheduled_local_date: "2026-01-15", as_of_date: "2026-01-15", scheduled_for_utc: "2026-01-15T07:00:00+00:00", status: "failed", attempt_count: 2, candidates_count: 7, created_count: 3, existing_count: 4, error_code: "materialization_failed", error_summary: "Bezpieczne podsumowanie błędu", started_at: "2026-01-15T07:00:00+00:00", finished_at: "2026-01-15T07:00:01+00:00", duration_ms: 1000 }] };
  },
};
class ApiError extends Error { constructor(message, status, payload) { super(message); this.status = status; this.payload = payload; } }

const originalLoad = Module._load;
Module._load = function loadWithMocks(request, parent, isMain) {
  if (request === "next/link") return function Link({ children, href, ...props }) { const React = require("react"); return React.createElement("a", { ...props, href }, children); };
  if (request === "lucide-react") { const React = require("react"); const Icon = (props) => React.createElement("svg", props); return { ArrowLeft: Icon, RefreshCw: Icon, Workflow: Icon }; }
  if (request === "@/context/ActiveOrganizationContext" || request.endsWith(`${path.sep}context${path.sep}ActiveOrganizationContext.tsx`)) return { useActiveOrganization: () => ({ selectedOrganizationId: organizationId, status: "ready" }) };
  if (request === "@/lib/api" || request.endsWith(`${path.sep}lib${path.sep}api.ts`)) return { ApiError, api, withOrganizationQuery: (id, query = {}) => ({ ...query, organization_id: id }) };
  return originalLoad.call(this, request, parent, isMain);
};

const dom = new JSDOM('<!doctype html><html><body><div id="root"></div></body></html>', { url: "http://127.0.0.1:3000/automatyzacje" });
globalThis.window = dom.window; globalThis.document = dom.window.document; globalThis.navigator = dom.window.navigator; globalThis.HTMLElement = dom.window.HTMLElement; globalThis.Event = dom.window.Event; globalThis.IS_REACT_ACT_ENVIRONMENT = true;
const React = require("react"); const { act } = React; const { createRoot } = require("react-dom/client");
const { AutomationOperationsPage } = require("../src/modules/automations/AutomationOperationsPage.tsx");
const { AutomationOperationDetailPage } = require("../src/modules/automations/AutomationOperationDetailPage.tsx");
async function settle() { await act(async () => { await new Promise((resolve) => setTimeout(resolve, 0)); }); }
function button(container, label) { return [...container.querySelectorAll("button")].find((item) => item.textContent.includes(label)); }

async function run() {
  const container = document.getElementById("root"); const root = createRoot(container);
  await act(async () => root.render(React.createElement(AutomationOperationsPage))); await settle();
  assert.match(container.textContent, /Automatyzacje/); assert.match(container.textContent, /Przypomnienia zadań/); assert.match(container.textContent, /Bezpieczny błąd przypomnienia/);
  assert.match(container.textContent, /Przetwarzanie bazy wiedzy/);
  assert.match(container.textContent, /Import e-maili/);
  assert.match(container.textContent, /Import KSeF/);
  assert.match(container.textContent, /Reguły automatyzacji/);
  assert.equal(container.querySelectorAll(".automation-card").length, 6);
  assert.deepEqual([...container.querySelectorAll(".automation-summary > div")].map((item) => item.textContent), ["Aktywne4", "Nieskonfigurowane1", "Wyłączone1", "Wymagają uwagi5"]);
  assert.ok(!container.textContent.includes("Ostatnie błędy"));
  assert.match(container.textContent, /Wymaga uwagi/);
  assert.equal(container.querySelectorAll(".automation-attention__item").length, 3);
  assert.deepEqual([...container.querySelectorAll(".automation-attention__item h4")].map((node) => node.textContent), ["Reguły automatyzacji", "Przypomnienia zadań", "Import e-maili"]);
  assert.match(container.textContent, /Wykonanie/); assert.match(container.textContent, /Kolejka/); assert.match(container.textContent, /Konfiguracja/);
  assert.match(container.textContent, /Czas niedostępny/);
  assert.equal(container.querySelectorAll('.automation-attention a[href^="/automatyzacje/"]').length, 3);
  assert.equal(container.querySelectorAll('.automation-attention a[href="/ustawienia"]').length, 0);
  assert.ok(!container.textContent.match(/last_execution_failed|failed_outbox_present|system_mailbox_not_configured|Retry|Run now|Rozwiąż|severity/i));
  const attentionText = container.querySelector(".automation-attention").textContent.toLowerCase();
  for (const forbidden of ["private@", "message-id", "nip", "fv/", "xml", "upo", "document.txt", "c:\\users", "payload=", "token=", "secret", "traceback"]) {
    assert.ok(!attentionText.includes(forbidden), `Sekcja attention ujawnia zakazany tekst: ${forbidden}`);
  }
  assert.equal(container.querySelector('a[href="/automatyzacje/internal_notification_scheduler"]').textContent, "Zobacz szczegóły");
  assert.equal(container.querySelector('a[href="/powiadomienia"]').textContent, "Przejdź do powiadomień");
  assert.equal(container.querySelector('a[href="/work-items"]').textContent, "Przejdź do zadań");
  assert.equal(container.querySelector('a[href="/dokumenty"]').textContent, "Przejdź do dokumentów");
  assert.equal(container.querySelectorAll('a[href="/ustawienia"]').length, 0);
  assert.equal(container.querySelectorAll('.automation-card a[href^="/automatyzacje/"]').length, 6);
  assert.ok(!container.textContent.includes("Runtime"));
  assert.ok(!container.textContent.includes("Nieznany"));
  assert.match(container.textContent, /sygnałów rozliczeniowych/);
  assert.match(container.textContent, /danych działań/);
  assert.ok(!container.textContent.match(/billing attention|payload/i));
  assert.ok(button(container, "Odśwież")); assert.ok(!container.textContent.includes("Uruchom teraz"));
  await act(async () => button(container, "Wymagają uwagi").dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true })));
  assert.equal(container.querySelectorAll(".automation-card").length, 5);
  assert.equal(container.querySelectorAll(".automation-attention__item").length, 3);
  await act(async () => button(container, "Nieskonfigurowane").dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true })));
  assert.deepEqual([...container.querySelectorAll(".automation-card h3")].map((node) => node.textContent), ["Import e-maili"]);
  assert.equal(container.querySelectorAll(".automation-attention__item").length, 3);
  await act(async () => button(container, "Wyłączone").dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true })));
  assert.deepEqual([...container.querySelectorAll(".automation-card h3")].map((node) => node.textContent), ["Import KSeF"]);
  assert.equal(container.querySelectorAll(".automation-attention__item").length, 3);
  emptyAttention = true; await act(async () => button(container, "Odśwież").dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true }))); await settle();
  assert.match(container.textContent, /Brak sygnałów wymagających uwagi/);
  assert.ok(container.querySelector(".automation-attention--empty"));
  emptyAttention = false;
  failDashboard = true; await act(async () => button(container, "Odśwież").dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true }))); await settle();
  assert.match(container.textContent, /Kontrolowany błąd centrum/); assert.ok(button(container, "Spróbuj ponownie"));
  failDashboard = false; organizationId = "43"; await act(async () => root.render(React.createElement(AutomationOperationsPage))); assert.ok(!container.textContent.includes("Opis operacyjny")); await settle();
  await act(async () => button(container, "Wszystkie").dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true })));
  assert.match(container.textContent, /sygnałów rozliczeniowych/);
  assert.ok(dashboardCalls >= 3);

  const cssSource = fs.readFileSync(path.join(__dirname, "..", "src", "app", "globals.css"), "utf8");
  assert.match(cssSource, /\.automation-attention__content[\s\S]*overflow-wrap:\s*anywhere/);
  assert.match(cssSource, /\.automation-attention--empty[\s\S]*padding-block:\s*0\.7rem/);
  assert.match(cssSource, /@media\s*\(max-width:\s*1100px\)[\s\S]*\.automation-attention__item[\s\S]*flex-direction:\s*column/);
  assert.ok(!/\.automation-(?:summary|grid|card|detail-card|operations__header)[^}]*var\(--(?:text-muted|surface|border)\)/s.test(cssSource));
  for (const token of ["--color-muted", "--color-surface", "--color-border"]) assert.match(cssSource, new RegExp(`${token}:`));
  assert.match(cssSource, /@media\s*\(max-width:\s*1440px\)[\s\S]*\.app-topbar[\s\S]*grid-template-columns:\s*1fr/);
  assert.match(cssSource, /@media\s*\(max-width:\s*820px\)[\s\S]*\.app-shell[\s\S]*grid-template-columns:\s*1fr/);

  await act(async () => root.render(React.createElement(AutomationOperationDetailPage, { automationKey: "internal_notification_scheduler" }))); await settle();
  assert.match(container.textContent, /Historia ostatnich uruchomień/); assert.match(container.textContent, /Monitoring procesu/); assert.match(container.textContent, /Brak monitoringu procesu/); assert.match(container.textContent, /Codziennie/); assert.equal(container.querySelectorAll("tbody tr").length, 1); assert.ok(!container.textContent.match(/\bonline\b|\boffline\b|runtime unknown/i));
  await act(async () => root.render(React.createElement(AutomationOperationDetailPage, { automationKey: "task_reminders" }))); await settle();
  assert.match(container.textContent, /Ostatnie próby/); assert.match(container.textContent, /Ostatnie wpisy kolejki/); assert.match(container.textContent, /Ostatni sygnał procesu/); assert.match(container.textContent, /Zakończone niepowodzeniem/); assert.match(container.textContent, /Nieudane/); assert.ok(!container.textContent.match(/\bonline\b|\boffline\b|Retry|Uruchom teraz|Wyślij ponownie/));
  await act(async () => root.render(React.createElement(AutomationOperationDetailPage, { automationKey: "knowledge_processing" }))); await settle();
  assert.match(container.textContent, /Ostatnie zadania przetwarzania/); assert.match(container.textContent, /Obserwowane foldery/); assert.match(container.textContent, /Brak monitoringu procesu/);
  assert.match(container.textContent, /Aktualizacja dokumentu/); assert.match(container.textContent, /Cykliczne skanowanie/); assert.ok(!container.textContent.match(/\breplace\b|\bpolling\b|\bqueued\b|\bprocessing\b|\bcompleted\b|\bfailed\b/));
  assert.ok(!container.textContent.match(/Retry|Reprocess|Uruchom teraz|Skanuj teraz|Run now|Scan now|C:\\Users|OCR text|treść dokumentu/i));
  await act(async () => root.render(React.createElement(AutomationOperationDetailPage, { automationKey: "email_import" }))); await settle();
  assert.match(container.textContent, /Import e-maili/); assert.match(container.textContent, /Automatyczny/); assert.match(container.textContent, /Zakończony z uwagami/);
  assert.match(container.textContent, /Brak monitoringu procesu/); assert.equal(container.querySelectorAll('a[href="/ustawienia"]').length, 0);
  for (const forbidden of ["email_import", "subject", "sender@", "recipient@", "message_id", "attachment", "token", "Importuj teraz", "Uruchom teraz"]) {
    assert.ok(!container.textContent.toLowerCase().includes(forbidden.toLowerCase()), `UI ujawnia zakazany tekst: ${forbidden}`);
  }
  await act(async () => root.render(React.createElement(AutomationOperationDetailPage, { automationKey: "ksef_import" }))); await settle();
  assert.match(container.textContent, /Import KSeF/); assert.match(container.textContent, /Ręczny/); assert.match(container.textContent, /Zakończony z uwagami/);
  assert.match(container.textContent, /Brak monitoringu procesu/); assert.equal(container.querySelectorAll('a[href="/ustawienia"]').length, 0);
  for (const forbidden of ["ksef_import", "nip", "numer faktury", "987.65", "xml", "upo", "ksef-id", "token", "certyfikat", "Importuj teraz", "Uruchom teraz", "Ponów"]) {
    assert.ok(!container.textContent.toLowerCase().includes(forbidden.toLowerCase()), `UI ujawnia zakazany tekst KSeF: ${forbidden}`);
  }
  await act(async () => root.render(React.createElement(AutomationOperationDetailPage, { automationKey: "automation_engine" }))); await settle();
  assert.match(container.textContent, /Reguły automatyzacji/); assert.match(container.textContent, /Reguła #12/); assert.match(container.textContent, /Ostatnie wykonania/);
  assert.match(container.textContent, /Brak monitoringu procesu/); assert.equal(container.querySelectorAll(".automation-card__links a").length, 0);
  for (const forbidden of ["automation_engine", "trigger", "actions_json", "input_json", "result_json", "traceback", "token", "Uruchom teraz", "Ponów", "Edytuj", "Usuń"]) {
    assert.ok(!container.textContent.toLowerCase().includes(forbidden.toLowerCase()), `UI ujawnia zakazany tekst silnika: ${forbidden}`);
  }
  detailNotFound = true; await act(async () => root.render(React.createElement(AutomationOperationDetailPage, { automationKey: "unknown" }))); await settle(); assert.match(container.textContent, /Nie znaleziono automatyzacji/);
  await act(async () => root.unmount());
  console.log("Automation operations DOM tests passed.");
}
run().catch((error) => { console.error(error); process.exit(1); });
