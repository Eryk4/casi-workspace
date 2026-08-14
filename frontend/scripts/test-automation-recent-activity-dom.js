const assert = require("node:assert/strict");
const fs = require("node:fs");
const Module = require("node:module");
const path = require("node:path");
const ts = require("typescript");
const { JSDOM } = require("jsdom");

for (const extension of [".ts", ".tsx"]) {
  require.extensions[extension] = function compileTypeScript(module, filename) {
    const output = ts.transpileModule(fs.readFileSync(filename, "utf8"), {
      compilerOptions: { esModuleInterop: true, jsx: ts.JsxEmit.ReactJSX, module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
      fileName: filename,
    });
    module._compile(output.outputText, filename);
  };
}

let organizationId = "42";
let dashboardCalls = 0;
let activityCalls = 0;
let failActivity = false;
let emptyActivity = false;
let pendingActivity = null;

const operation = {
  automation_key: "internal_notification_scheduler", automation_type: "scheduler", title: "Automatyczne sprawdzanie powiadomień",
  description: "Opis", status: "enabled", enabled: true, health: "healthy", health_reason_code: "last_run_succeeded",
  schedule_id: 1, run_id: 2, next_run_at: "2026-08-14T07:00:00+00:00", last_run_at: "2026-08-13T07:00:00+00:00",
  last_run_status: "succeeded", last_run_duration_ms: 1000, last_attempt_count: 1, last_candidates_count: 4,
  last_created_count: 2, last_existing_count: 2, recent_failure_count: 0, last_error_code: null, last_error_summary: null,
  settings_url: "/powiadomienia", details_url: "/automatyzacje/internal_notification_scheduler", runtime_status: "unknown",
  schedule: { cadence: "daily", timezone_name: "Europe/Warsaw", local_time: "08:00" }, updated_at: "2026-08-13T07:00:01+00:00",
};
const keys = ["internal_notification_scheduler", "task_reminders", "knowledge_processing", "email_import", "ksef_import", "automation_engine", "task_reminders", "knowledge_processing"];
const types = ["scheduled_check", "delivery", "processing", "import", "import", "execution", "delivery", "processing"];
const statuses = ["succeeded", "failed", "partial", "succeeded", "failed", "partial", "succeeded", "failed"];
function activityPayload(prefix = "Org A") {
  return { limit: 8, items: keys.map((key, index) => ({
    activity_id: `${key}:source:${index + 1}`, automation_key: key, title: `${prefix} — Adapter ${index + 1}`,
    activity_type: types[index], status: statuses[index], occurred_at: `2026-08-13T1${9 - index}:00:00+00:00`,
    summary: index === 0 ? "Utworzono powiadomienia wewnętrzne: 3." : `Bezpieczne podsumowanie ${index + 1}.`,
    details_url: `/automatyzacje/${key}`,
  })) };
}
const api = {
  automationOperations: async () => {
    dashboardCalls += 1;
    return { summary: { active_count: 1, disabled_count: 0, attention_count: 0, recent_failure_count: 0 }, attention_items: [], items: [operation] };
  },
  automationOperationsActivity: async (query) => {
    activityCalls += 1;
    if (pendingActivity && String(query.organization_id) === "42") return pendingActivity.promise;
    if (failActivity) throw new Error("private SQL payload token");
    if (emptyActivity) return { items: [], limit: 8 };
    return activityPayload(String(query.organization_id) === "43" ? "Org B" : "Org A");
  },
};

const originalLoad = Module._load;
Module._load = function loadWithMocks(request, parent, isMain) {
  if (request === "next/link") return function Link({ children, href, ...props }) { const React = require("react"); return React.createElement("a", { ...props, href }, children); };
  if (request === "lucide-react") { const React = require("react"); const Icon = (props) => React.createElement("svg", props); return { RefreshCw: Icon, Workflow: Icon }; }
  if (request === "@/context/ActiveOrganizationContext" || request.endsWith(`${path.sep}context${path.sep}ActiveOrganizationContext.tsx`)) return { useActiveOrganization: () => ({ selectedOrganizationId: organizationId, status: "ready" }) };
  if (request === "@/lib/api" || request.endsWith(`${path.sep}lib${path.sep}api.ts`)) return { api, withOrganizationQuery: (id, query = {}) => ({ ...query, organization_id: id }) };
  return originalLoad.call(this, request, parent, isMain);
};

const dom = new JSDOM('<!doctype html><html><body><div id="root"></div></body></html>', { url: "http://127.0.0.1:3000/automatyzacje" });
globalThis.window = dom.window; globalThis.document = dom.window.document; globalThis.navigator = dom.window.navigator;
globalThis.HTMLElement = dom.window.HTMLElement; globalThis.Event = dom.window.Event; globalThis.IS_REACT_ACT_ENVIRONMENT = true;
const React = require("react"); const { act } = React; const { createRoot } = require("react-dom/client");
const { AutomationOperationsPage } = require("../src/modules/automations/AutomationOperationsPage.tsx");
async function settle() { await act(async () => { await new Promise((resolve) => setTimeout(resolve, 0)); }); }
function button(container, label) { return [...container.querySelectorAll("button")].find((item) => item.textContent.includes(label)); }
function deferred() { let resolve; const promise = new Promise((next) => { resolve = next; }); return { promise, resolve }; }

async function run() {
  const container = document.getElementById("root"); const root = createRoot(container);
  pendingActivity = deferred();
  await act(async () => root.render(React.createElement(AutomationOperationsPage))); await settle();
  assert.match(container.textContent, /Ostatnia aktywność/);
  assert.match(container.textContent, /Ładowanie ostatniej aktywności/);
  assert.equal(container.querySelectorAll(".automation-card").length, 1, "Activity loading nie blokuje kart");
  await act(async () => pendingActivity.resolve(activityPayload())); pendingActivity = null; await settle();
  assert.equal(container.querySelectorAll(".automation-activity__item").length, 8);
  assert.deepEqual([...container.querySelectorAll(".automation-activity__item h4")].map((node) => node.textContent), activityPayload().items.map((item) => item.title));
  for (const label of ["Zakończono", "Nieudane", "Z problemami"]) assert.match(container.textContent, new RegExp(label));
  assert.equal(container.querySelectorAll('.automation-activity a[href^="/automatyzacje/"]').length, 8);
  assert.match(container.querySelector(".automation-activity").textContent, /Utworzono powiadomienia wewnętrzne: 3/);
  assert.ok(!container.querySelector(".automation-activity").textContent.match(/source:1|scheduled_check|activity_id|payload|token|private SQL/i));
  assert.equal(container.querySelectorAll(".automation-activity time").length, 8);

  await act(async () => button(container, "Wymagają uwagi").dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true })));
  assert.equal(container.querySelectorAll(".automation-card").length, 0);
  assert.equal(container.querySelectorAll(".automation-activity__item").length, 8, "Filtr kart nie zmienia Activity");

  const beforeDashboard = dashboardCalls; const beforeActivity = activityCalls;
  await act(async () => button(container, "Odśwież").dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true }))); await settle();
  assert.equal(dashboardCalls, beforeDashboard + 1); assert.equal(activityCalls, beforeActivity + 1);

  failActivity = true;
  await act(async () => button(container, "Odśwież").dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true }))); await settle();
  assert.match(container.textContent, /Nie udało się pobrać ostatniej aktywności/);
  assert.ok(!container.textContent.match(/private SQL payload token/));
  const retry = button(container, "Spróbuj ponownie"); const dashboardBeforeRetry = dashboardCalls;
  failActivity = false; await act(async () => retry.dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true }))); await settle();
  assert.equal(dashboardCalls, dashboardBeforeRetry, "Retry Activity nie pobiera dashboardu");
  assert.equal(container.querySelectorAll(".automation-activity__item").length, 8);

  emptyActivity = true;
  await act(async () => button(container, "Odśwież").dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true }))); await settle();
  assert.match(container.textContent, /Brak ostatniej aktywności/);
  emptyActivity = false;

  organizationId = "42"; pendingActivity = deferred();
  await act(async () => button(container, "Odśwież").dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true })));
  organizationId = "43";
  await act(async () => root.render(React.createElement(AutomationOperationsPage))); await settle();
  assert.match(container.textContent, /Org B — Adapter 1/); assert.ok(!container.textContent.includes("Org A — Adapter 1"));
  await act(async () => pendingActivity.resolve(activityPayload("Org A"))); pendingActivity = null; await settle();
  assert.match(container.textContent, /Org B — Adapter 1/); assert.ok(!container.textContent.includes("Org A — Adapter 1"));

  const css = fs.readFileSync(path.join(__dirname, "..", "src", "app", "globals.css"), "utf8");
  assert.match(css, /\.automation-activity__list[\s\S]*grid-template-columns:\s*minmax\(0,\s*1fr\)/);
  assert.match(css, /\.automation-activity__content[\s\S]*overflow-wrap:\s*anywhere/);
  assert.match(css, /@media\s*\(max-width:\s*1100px\)[\s\S]*\.automation-activity__item[\s\S]*flex-direction:\s*column/);
  assert.ok(!/setInterval|WebSocket|EventSource/.test(fs.readFileSync(path.join(__dirname, "..", "src", "modules", "automations", "AutomationOperationsPage.tsx"), "utf8")));

  await act(async () => root.unmount());
  console.log("Automation recent activity DOM tests passed.");
}

run().catch((error) => { console.error(error); process.exit(1); });
