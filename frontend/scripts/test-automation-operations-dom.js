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
const api = {
  automationOperations: async (query) => {
    dashboardCalls += 1;
    if (failDashboard) throw new Error("Kontrolowany błąd centrum");
    if (String(query.organization_id) !== organizationId) throw new Error("Stary scope organizacji");
    return { summary: { active_count: 2, disabled_count: 0, attention_count: 2, recent_failure_count: 2 }, items: [operation, reminderOperation] };
  },
  automationOperationDetail: async (automationKey) => {
    if (detailNotFound) throw new ApiError("Nie znaleziono", 404, {});
    if (automationKey === "task_reminders") return { item: reminderOperation, history_limit: 20, history: [{ history_type: "reminder_attempt", attempt_id: 9, outbox_id: 8, channel: "telegram", attempt_no: 2, status: "dead_letter", attempted_at: "2026-01-15T07:01:00+00:00", error_code: "task_reminder_delivery_failed", error_summary: "Bezpieczny błąd przypomnienia" }], outbox: [{ task_reminder_outbox_id: 8, status: "failed", delivery_channel: "telegram", available_at: "2026-01-15T07:00:00+00:00", attempt_count: 2, created_at: "2026-01-15T07:00:00+00:00", updated_at: "2026-01-15T07:01:00+00:00" }] };
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
  assert.equal(container.querySelectorAll(".automation-card").length, 2);
  assert.equal(container.querySelector('a[href="/automatyzacje/internal_notification_scheduler"]').textContent, "Szczegóły");
  assert.equal(container.querySelector('a[href="/powiadomienia"]').textContent, "Ustawienia");
  assert.ok(button(container, "Odśwież")); assert.ok(!container.textContent.includes("Uruchom teraz"));
  await act(async () => button(container, "Wyłączone").dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true })));
  assert.match(container.textContent, /Żadna automatyzacja/);
  failDashboard = true; await act(async () => button(container, "Odśwież").dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true }))); await settle();
  assert.match(container.textContent, /Kontrolowany błąd centrum/); assert.ok(button(container, "Spróbuj ponownie"));
  failDashboard = false; organizationId = "43"; await act(async () => root.render(React.createElement(AutomationOperationsPage))); assert.ok(!container.textContent.includes("Opis operacyjny")); await settle();
  await act(async () => button(container, "Wszystkie").dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true })));
  assert.match(container.textContent, /Opis operacyjny/);
  assert.ok(dashboardCalls >= 3);

  await act(async () => root.render(React.createElement(AutomationOperationDetailPage, { automationKey: "internal_notification_scheduler" }))); await settle();
  assert.match(container.textContent, /Historia ostatnich uruchomień/); assert.match(container.textContent, /Nieznany — centrum nie monitoruje procesu workera/); assert.equal(container.querySelectorAll("tbody tr").length, 1); assert.ok(!container.textContent.includes("lease"));
  await act(async () => root.render(React.createElement(AutomationOperationDetailPage, { automationKey: "task_reminders" }))); await settle();
  assert.match(container.textContent, /Ostatnie próby/); assert.match(container.textContent, /Ostatnie wpisy kolejki/); assert.match(container.textContent, /bez oceny online\/offline/); assert.ok(!container.textContent.match(/Retry|Uruchom teraz|Wyślij ponownie/));
  detailNotFound = true; await act(async () => root.render(React.createElement(AutomationOperationDetailPage, { automationKey: "unknown" }))); await settle(); assert.match(container.textContent, /Nie znaleziono automatyzacji/);
  await act(async () => root.unmount());
  console.log("Automation operations DOM tests passed.");
}
run().catch((error) => { console.error(error); process.exit(1); });
