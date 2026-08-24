const assert = require("node:assert/strict");
const fs = require("node:fs");
const Module = require("node:module");
const path = require("node:path");
const ts = require("typescript");
const { JSDOM } = require("jsdom");

for (const extension of [".ts", ".tsx"]) {
  require.extensions[extension] = function compileTypeScript(module, filename) {
    const output = ts.transpileModule(fs.readFileSync(filename, "utf8"), { compilerOptions: { esModuleInterop: true, jsx: ts.JsxEmit.ReactJSX, module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 }, fileName: filename });
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
let organizationName = "CASI";
let capabilities = ["automation.read", "work_items.read", "billing.read"];
let failBilling = false;
let requestGate = null;
const calls = [];
async function waitForGate(query) { if (requestGate && String(query.organization_id) === requestGate.organizationId) await requestGate.promise; }
const api = {
  automationOperations: async (query) => { calls.push(["attention", query]); await waitForGate(query); return { summary: { active_count: 1, disabled_count: 0, attention_count: 1, recent_failure_count: 0 }, attention_items: [{ automation_key: "task_reminders", title: `Przypomnienia ${query.organization_id}`, attention_category: "backlog", reason_code: "pending", occurred_at: "2026-08-17T08:00:00+00:00", summary: "Jedno przypomnienie oczekuje.", details_url: "/automatyzacje/task_reminders", settings_url: null }], items: [] }; },
  todayTasks: async (query) => { calls.push(["tasks", query]); await waitForGate(query); return { counts: { overdue: 1, today: 1, upcoming: 0 }, items: [{ task_id: Number(query.organization_id), title: `Zadanie ${query.organization_id}`, due_at: "2026-08-17T09:00:00+00:00", bucket: "today", details_url: `/work-items/${query.organization_id}` }] }; },
  todayBilling: async (query) => { calls.push(["billing", query]); await waitForGate(query); if (failBilling) throw new Error("Kontrolowany błąd rozliczeń"); return { overdue_count: 0, due_today_count: 1, items: [{ billing_next_step_event_id: 9, title: `Kontakt ${query.organization_id}`, planned_for: "2026-08-17", bucket: "today", details_url: "/rozliczenia/platnicy/1" }] }; },
  automationOperationsActivity: async (query) => { calls.push(["activity", query]); await waitForGate(query); return { limit: 3, items: [{ activity_id: `run:${query.organization_id}`, automation_key: "task_reminders", title: "Przypomnienia zadań", activity_type: "delivery", status: "succeeded", occurred_at: "2026-08-17T08:30:00+00:00", summary: `Aktywność ${query.organization_id}.`, details_url: "/automatyzacje/task_reminders" }] }; },
};

const originalLoad = Module._load;
Module._load = function loadWithMocks(request, parent, isMain) {
  if (request === "next/link") return function Link({ children, href, ...props }) { const React = require("react"); return React.createElement("a", { ...props, href }, children); };
  if (request === "lucide-react") { const React = require("react"); const Icon = (props) => React.createElement("svg", props); return { CheckCircle2: Icon, Clock3: Icon, ListChecks: Icon, RefreshCw: Icon, TriangleAlert: Icon, Workflow: Icon }; }
  if (request === "@/context/ActiveOrganizationContext" || request.endsWith(`${path.sep}context${path.sep}ActiveOrganizationContext.tsx`)) return { useActiveOrganization: () => ({ capabilities, selectedOrganizationId: organizationId, selectedOrganization: { id: organizationId, name: organizationName }, status: "ready" }) };
  if (request === "@/lib/api" || request.endsWith(`${path.sep}lib${path.sep}api.ts`)) return { api };
  return originalLoad.call(this, request, parent, isMain);
};

const dom = new JSDOM('<!doctype html><html><body><div id="root"></div></body></html>', { url: "http://127.0.0.1:3000/pulpit-dnia" });
globalThis.window = dom.window; globalThis.document = dom.window.document; globalThis.navigator = dom.window.navigator; globalThis.HTMLElement = dom.window.HTMLElement; globalThis.Event = dom.window.Event; globalThis.IS_REACT_ACT_ENVIRONMENT = true;
const React = require("react"); const { act } = React; const { createRoot } = require("react-dom/client");
const { DailyBriefPage } = require("../src/modules/daily-brief/DailyBriefPage.tsx");
async function settle() { await act(async () => { await new Promise((resolve) => setTimeout(resolve, 0)); }); }
function button(container, label) { return [...container.querySelectorAll("button")].find((item) => item.textContent.includes(label)); }

async function render(root) { await act(async () => root.render(React.createElement(DailyBriefPage))); await settle(); }

async function run() {
  const container = document.getElementById("root"); const root = createRoot(container);
  await render(root);
  assert.match(container.textContent, /Dzisiaj w CASI/); assert.match(container.textContent, /CASI/);
  assert.deepEqual([...container.querySelectorAll(".today-section")].map((node) => [...node.classList].find((name) => name.startsWith("today-section--"))), ["today-section--attention", "today-section--tasks", "today-section--billing", "today-section--activity"]);
  assert.match(container.textContent, /Zadanie 42/); assert.match(container.textContent, /Kontakt 42/); assert.match(container.textContent, /Aktywność 42/);
  assert.deepEqual(calls.slice(0, 4).map(([name]) => name).sort(), ["activity", "attention", "billing", "tasks"]);
  assert.equal(calls.find(([name]) => name === "activity")[1].limit, 3);
  assert.ok(calls.slice(0, 4).every(([, query]) => query.organization_id === "42"));

  failBilling = true; await act(async () => button(container, "Odśwież").dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true }))); await settle();
  assert.match(container.textContent, /Nie udało się pobrać spraw rozliczeniowych/); assert.match(container.textContent, /Zadanie 42/); assert.match(container.textContent, /Aktywność 42/);
  failBilling = false; await act(async () => button(container, "Spróbuj ponownie").dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true }))); await settle();
  assert.ok(!container.textContent.includes("Nie udało się pobrać spraw rozliczeniowych"));

  organizationId = "43"; organizationName = "Misja Robotyka"; await render(root);
  assert.ok(!container.textContent.includes("Zadanie 42")); assert.match(container.textContent, /Zadanie 43/); assert.match(container.textContent, /Misja Robotyka/);

  capabilities = ["automation.read", "work_items.read"]; await render(root);
  assert.equal(container.querySelectorAll(".today-section").length, 3); assert.ok(!container.textContent.includes("Kontakt 43"));
  capabilities = ["work_items.read"]; await render(root);
  assert.equal(container.querySelectorAll(".today-section").length, 1); assert.match(container.textContent, /Twoje zadania/);
  const callsBeforeGuest = calls.length; capabilities = []; await render(root);
  assert.equal(container.querySelectorAll(".today-section").length, 0); assert.match(container.textContent, /Brak dodatkowych sekcji do wyświetlenia/); assert.equal(calls.length, callsBeforeGuest);

  capabilities = ["automation.read", "work_items.read", "billing.read"];
  let releaseGate; requestGate = { organizationId: "44", promise: new Promise((resolve) => { releaseGate = resolve; }) };
  organizationId = "44"; organizationName = "Stara organizacja"; await render(root);
  organizationId = "45"; organizationName = "Nowa organizacja"; await render(root);
  assert.match(container.textContent, /Zadanie 45/); assert.match(container.textContent, /Kontakt 45/); assert.match(container.textContent, /Aktywność 45/);
  releaseGate(); await settle(); requestGate = null;
  assert.ok(!container.textContent.includes("Zadanie 44")); assert.ok(!container.textContent.includes("Kontakt 44")); assert.ok(!container.textContent.includes("Aktywność 44"));

  const css = fs.readFileSync(path.join(__dirname, "..", "src", "app", "globals.css"), "utf8");
  assert.match(css, /@media \(max-width: 1024px\)[\s\S]*grid-template-areas: "attention" "tasks" "billing" "activity"/);
  assert.match(css, /@media \(max-width: 520px\)/);
  await act(async () => root.unmount());
  console.log("Today dashboard DOM tests passed.");
}
run().catch((error) => { console.error(error); process.exit(1); });
