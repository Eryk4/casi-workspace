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

const srcRoot = path.join(__dirname, "..", "src");
const originalResolveFilename = Module._resolveFilename;
Module._resolveFilename = function resolveAlias(request, parent, isMain, options) {
  if (request.startsWith("@/")) {
    const resolved = path.join(srcRoot, request.slice(2));
    return [".ts", ".tsx", ".js", ".jsx"].map((extension) => `${resolved}${extension}`).find(fs.existsSync) ?? resolved;
  }
  return originalResolveFilename.call(this, request, parent, isMain, options);
};

let organizationId = "1";
let capabilities = ["automation.read", "automation.manage"];
let listError = false;
let busyEnable = false;
let createValidationError = false;
let rulesCalls = 0;
let catalogCalls = 0;
let createCalls = [];
let updateCalls = [];
let routePushes = [];
let routeReplacements = [];
let rulesResponseQueue = [];
let rules = [
  { automation_rule_id: 1, rule_name: "Nowe faktury", rule_slug: "hidden-slug", description: "Powiadamia o zmianie statusu.", trigger_event_type: "invoice_status_changed", is_active: false, last_run_at: null, execution_count: 0, created_at: "2026-01-01T00:00:00Z", updated_at: "2026-01-01T00:00:00Z" },
  { automation_rule_id: 2, rule_name: "Nowe zadania", rule_slug: "hidden-task", description: null, trigger_event_type: "work_item_created", is_active: true, last_run_at: "2026-01-02T12:00:00Z", execution_count: 4, created_at: "2026-01-01T00:00:00Z", updated_at: "2026-01-02T12:00:00Z" },
];
const catalog = {
  version: 1,
  triggers: [
    { key: "invoice_status_changed", label_key: "automation.trigger.invoice_status_changed", condition_fields: [{ key: "source", type: "string", operators: ["equals"], max_length: 120 }, { key: "status_after", type: "string", operators: ["equals"], max_length: 120 }] },
    { key: "work_item_created", label_key: "automation.trigger.work_item_created", condition_fields: [{ key: "status_after", type: "string", operators: ["equals"], max_length: 120 }] },
  ],
  actions: [{ key: "create_inbox_item", label_key: "automation.action.create_inbox_item", fields: [{ key: "title", type: "string", required: true, max_length: 200 }, { key: "description", type: "string", required: false, max_length: 2000 }] }],
  constraints: { min_actions: 1, max_actions: 1, max_conditions: 3 },
};

class ApiError extends Error { constructor(message, status, payload) { super(message); this.status = status; this.payload = payload; } }
const api = {
  automationCatalog: async () => { catalogCalls += 1; return catalog; },
  automationRules: async () => { rulesCalls += 1; if (rulesResponseQueue.length) return rulesResponseQueue.shift(); if (listError) throw new Error("list failed"); return rules; },
  createAutomationRule: async (payload, orgId) => {
    createCalls.push({ payload, orgId });
    if (createValidationError) throw new ApiError("invalid", 400, { code: "automation_rule.required", field: "actions[0].title", error: "Tytuł jest wymagany." });
    return { automation_rule_id: 3 };
  },
  updateAutomationRule: async (id, payload, orgId) => {
    updateCalls.push({ id, payload, orgId });
    if (busyEnable && payload.is_active) throw new ApiError("busy", 409, { code: "automation_rule_busy", error: "busy" });
    rules = rules.map((rule) => rule.automation_rule_id === id ? { ...rule, is_active: payload.is_active } : rule);
    return rules.find((rule) => rule.automation_rule_id === id);
  },
};
const router = { push: (value) => routePushes.push(value), replace: (value) => routeReplacements.push(value) };

const originalLoad = Module._load;
Module._load = function loadWithMocks(request, parent, isMain) {
  if (request === "next/link") return function Link({ children, href, ...props }) { const React = require("react"); return React.createElement("a", { ...props, href }, children); };
  if (request === "next/navigation") return { useRouter: () => router };
  if (request === "lucide-react") { const React = require("react"); const Icon = (props) => React.createElement("svg", props); return { ArrowLeft: Icon, Plus: Icon, RefreshCw: Icon, Settings2: Icon, Trash2: Icon }; }
  if (request === "@/context/ActiveOrganizationContext" || request.endsWith(`${path.sep}context${path.sep}ActiveOrganizationContext.tsx`)) return { useActiveOrganization: () => ({ capabilities, selectedOrganizationId: organizationId, status: "ready" }) };
  if (request === "@/lib/api" || request.endsWith(`${path.sep}lib${path.sep}api.ts`)) return { ApiError, ApiContractError: class ApiContractError extends Error {}, api, withOrganizationQuery: (id, query = {}) => ({ ...query, organization_id: id }) };
  return originalLoad.call(this, request, parent, isMain);
};

const dom = new JSDOM('<!doctype html><html><body><div id="root"></div></body></html>', { url: "http://127.0.0.1:3000/automatyzacje/reguly" });
globalThis.window = dom.window; globalThis.document = dom.window.document; globalThis.navigator = dom.window.navigator; globalThis.HTMLElement = dom.window.HTMLElement; globalThis.Event = dom.window.Event; globalThis.IS_REACT_ACT_ENVIRONMENT = true;
const React = require("react"); const { act } = React; const { createRoot } = require("react-dom/client");
const { AutomationRulesPage } = require("../src/modules/automations/AutomationRulesPage.tsx");
const { AutomationRuleCreatePage } = require("../src/modules/automations/AutomationRuleCreatePage.tsx");

async function settle() { await act(async () => { await new Promise((resolve) => setTimeout(resolve, 0)); }); }
function button(container, label) { return [...container.querySelectorAll("button")].find((item) => item.textContent.includes(label)); }
async function click(node) { await act(async () => node.dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true }))); await settle(); }
async function rapidDoubleClick(node) {
  await act(async () => {
    node.dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true }));
    node.dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true }));
  });
  await settle();
}
async function change(node, value) {
  const setter = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(node), "value").set;
  await act(async () => { setter.call(node, value); node.dispatchEvent(new dom.window.Event("change", { bubbles: true })); });
}

async function run() {
  const container = document.getElementById("root"); const root = createRoot(container);

  await act(async () => root.render(React.createElement(AutomationRulesPage))); await settle();
  assert.match(container.textContent, /Reguły automatyzacji/);
  assert.match(container.textContent, /Automatyczne wykonywanie reguł nie jest jeszcze uruchomione/);
  assert.match(container.textContent, /Zmiana statusu faktury/);
  assert.match(container.textContent, /Utworzono zadanie/);
  assert.match(container.textContent, /Jeszcze nie uruchomiono/);
  assert.match(container.textContent, /Aktywna/);
  assert.match(container.textContent, /Wyłączona/);
  assert.equal(rulesCalls, 1); assert.equal(catalogCalls, 1);
  for (const forbidden of ["hidden-slug", "conditions_json", "actions_json", "cursor", "lease", "Uruchom teraz", "Edytuj", "Usuń", "Retry"]) assert.ok(!container.textContent.includes(forbidden));

  await click(button(container, "Włącz"));
  assert.match(container.textContent, /Wcześniejsze zdarzenia nie zostaną uruchomione ponownie/);
  await rapidDoubleClick(button(container, "Włącz regułę"));
  assert.deepEqual(updateCalls[0], { id: 1, payload: { is_active: true }, orgId: "1" });
  assert.equal(updateCalls.length, 1);
  assert.match(container.textContent, /Reguła została włączona/);

  await click(button(container, "Wyłącz"));
  assert.match(container.textContent, /jedno działanie już trwa, może się jeszcze zakończyć/);
  await rapidDoubleClick(button(container, "Wyłącz regułę"));
  assert.deepEqual(updateCalls[1], { id: 1, payload: { is_active: false }, orgId: "1" });
  assert.equal(updateCalls.length, 2);

  rules = rules.map((rule) => rule.automation_rule_id === 1 ? { ...rule, is_active: false } : rule);
  busyEnable = true;
  await click(button(container, "Włącz")); await click(button(container, "Włącz regułę"));
  assert.match(container.textContent, /Reguła jest obecnie przetwarzana/);
  assert.equal(updateCalls.length, 3);
  busyEnable = false;
  await click(button(container, "Anuluj"));

  const catalogCallsBeforeRetry = catalogCalls;
  listError = true; await click(button(container, "Odśwież"));
  assert.match(container.textContent, /Nie udało się pobrać reguł automatyzacji/);
  assert.ok(button(container, "Spróbuj ponownie"));
  listError = false;

  rules = []; await click(button(container, "Spróbuj ponownie"));
  assert.equal(catalogCalls, catalogCallsBeforeRetry);
  assert.match(container.textContent, /Nie masz jeszcze żadnych reguł/);
  assert.match(container.textContent, /Utwórz pierwszą regułę/);

  let resolveOrgA;
  let resolveOrgB;
  const orgAResponse = new Promise((resolve) => { resolveOrgA = resolve; });
  const orgBResponse = new Promise((resolve) => { resolveOrgB = resolve; });
  rulesResponseQueue = [orgAResponse, orgBResponse];
  organizationId = "10";
  await act(async () => root.render(React.createElement(AutomationRulesPage)));
  organizationId = "11";
  await act(async () => root.render(React.createElement(AutomationRulesPage)));
  resolveOrgB([]);
  await settle();
  assert.match(container.textContent, /Nie masz jeszcze żadnych reguł/);
  resolveOrgA([{ automation_rule_id: 77, rule_name: "Stara reguła Org A", description: null, trigger_event_type: "work_item_created", is_active: false, last_run_at: null, execution_count: 0, updated_at: null }]);
  await settle();
  assert.ok(!container.textContent.includes("Stara reguła Org A"));

  const fetchesBeforeDenied = rulesCalls + catalogCalls;
  capabilities = ["automation.read"]; await act(async () => root.render(React.createElement(AutomationRulesPage))); await settle();
  assert.match(container.textContent, /Brak dostępu/);
  assert.equal(rulesCalls + catalogCalls, fetchesBeforeDenied);
  assert.ok(routeReplacements.includes("/automatyzacje"));

  capabilities = ["automation.read", "automation.manage"]; organizationId = "1"; rules = []; rulesResponseQueue = [];
  await act(async () => root.render(React.createElement(AutomationRuleCreatePage))); await settle();
  assert.match(container.textContent, /Nowa reguła automatyzacji/);
  assert.deepEqual([...container.querySelectorAll(".automation-rule-steps li")].map((item) => item.textContent.replace(/^\d+/, "")), ["Nazwa", "Gdy", "Jeśli", "Zrób", "Podsumowanie"]);
  assert.ok(!container.textContent.includes("log"));
  assert.ok(!container.textContent.includes("Włącz od razu"));
  assert.ok(!container.textContent.includes("Zapisz i włącz"));

  await change(container.querySelector("#automation-rule-name"), "Powiadom o zadaniu");
  await change(container.querySelector("#automation-rule-description"), "Opis reguły");
  await change(container.querySelector("#automation-rule-trigger"), "work_item_created");
  await click(button(container, "Dodaj warunek"));
  await change(container.querySelector('[aria-label="Wartość warunku 1"]'), "nowe");
  await change(container.querySelector("#automation-action-title"), "Nowe zadanie");
  await change(container.querySelector("#automation-action-description"), "Sprawdź zadanie");
  assert.match(container.textContent, /Podsumowanie reguły/);
  assert.match(container.textContent, /Reguła zostanie zapisana jako wyłączona/);
  await rapidDoubleClick(button(container, "Zapisz regułę"));
  assert.equal(createCalls.length, 1);
  assert.equal(createCalls[0].payload.is_active, false);
  assert.equal(createCalls[0].payload.trigger_event_type, "work_item_created");
  assert.deepEqual(createCalls[0].payload.conditions_json, { status_after: "nowe" });
  assert.deepEqual(createCalls[0].payload.actions_json, [{ type: "create_inbox_item", title: "Nowe zadanie", description: "Sprawdź zadanie" }]);
  assert.equal(updateCalls.length, 3);
  assert.ok(routePushes.includes("/automatyzacje/reguly?created=1"));

  createValidationError = true; routePushes = [];
  await act(async () => root.render(React.createElement(AutomationRulesPage))); await settle();
  await act(async () => root.render(React.createElement(AutomationRuleCreatePage))); await settle();
  await change(container.querySelector("#automation-rule-name"), "Reguła z błędem");
  await change(container.querySelector("#automation-rule-trigger"), "work_item_created");
  await change(container.querySelector("#automation-action-title"), "Tytuł lokalny");
  await click(button(container, "Zapisz regułę"));
  assert.match(container.textContent, /Tytuł jest wymagany/);
  assert.equal(container.querySelector("#automation-rule-name").value, "Reguła z błędem");
  assert.equal(routePushes.length, 0);
  createValidationError = false;

  createCalls = []; routePushes = [];
  await act(async () => root.render(React.createElement(AutomationRuleCreatePage))); await settle();
  await change(container.querySelector("#automation-rule-name"), "Draft organizacji A");
  organizationId = "2"; await act(async () => root.render(React.createElement(AutomationRuleCreatePage))); await settle();
  assert.ok(routeReplacements.includes("/automatyzacje/reguly?organization_changed=1"));
  assert.equal(createCalls.length, 0);

  const css = fs.readFileSync(path.join(__dirname, "..", "src", "app", "globals.css"), "utf8");
  assert.match(css, /\.automation-rules-grid[\s\S]*grid-template-columns:\s*repeat\(2/);
  assert.match(css, /@media\s*\(max-width:\s*1024px\)[\s\S]*\.automation-rules-grid\s*\{\s*grid-template-columns:\s*1fr/);
  assert.match(css, /@media\s*\(max-width:\s*768px\)[\s\S]*\.automation-rule-steps\s*\{\s*grid-template-columns:\s*1fr/);
  assert.match(css, /@media\s*\(max-width:\s*420px\)[\s\S]*\.automation-management__header-actions/);
  assert.ok(!/setInterval|WebSocket|EventSource/.test(fs.readFileSync(path.join(__dirname, "..", "src", "modules", "automations", "AutomationRulesPage.tsx"), "utf8")));

  await act(async () => root.unmount());
  console.log("Automation management DOM tests passed.");
}

run().catch((error) => { console.error(error); process.exit(1); });
