const assert = require("node:assert/strict");
const fs = require("node:fs");
const Module = require("node:module");
const path = require("node:path");
const ts = require("typescript");
const { JSDOM } = require("jsdom");

for (const extension of [".ts", ".tsx"]) {
  require.extensions[extension] = function compileTypeScript(module, filename) {
    const source = fs.readFileSync(filename, "utf8");
    const output = ts.transpileModule(source, {
      compilerOptions: {
        esModuleInterop: true,
        jsx: ts.JsxEmit.ReactJSX,
        module: ts.ModuleKind.CommonJS,
        target: ts.ScriptTarget.ES2022,
      },
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

let currentOrganizationId = "42";
let shouldFail = false;
let initialRequestPending = true;
let resolveInitialRequest = null;
let nextEventId = 900;
const submittedPayloads = [];
const allEvents = [
  { billing_next_step_event_id: 101, organization_id: 42, target_type: "billing_summary", step_type: "other", event_action: "planned", title: "Dwa takie same", created_at: "2026-12-01T09:00:00" },
  { billing_next_step_event_id: 102, organization_id: 42, target_type: "billing_summary", step_type: "other", event_action: "planned", title: "Dwa takie same", created_at: "2026-12-01T09:00:00" },
  { billing_next_step_event_id: 103, organization_id: 42, target_type: "payer", target_id: 7, step_type: "call", event_action: "planned", title: "Zaległy telefon", planned_for: "2020-01-01", created_at: "2026-12-01T10:00:00" },
  { billing_next_step_event_id: 104, organization_id: 42, target_type: "payment", target_id: 8, step_type: "check_payment", event_action: "planned", title: "Przyszła wpłata", planned_for: "2099-01-01", created_at: "2026-12-01T10:00:00" },
  { billing_next_step_event_id: 105, organization_id: 42, target_type: "work_queue_issue", related_issue_key: "issue:1", step_type: "clarify_payment", event_action: "planned", title: "Sprawa bez daty", created_at: "2026-12-01T10:00:00" },
  { billing_next_step_event_id: 106, organization_id: 42, target_type: "future_target", step_type: "other", event_action: "planned", title: "Historyczny cel", created_at: "2026-12-01T10:00:00" },
  { billing_next_step_event_id: 201, organization_id: 43, target_type: "billing_summary", step_type: "review_notes", event_action: "planned", title: "Tylko druga organizacja", created_at: "2026-12-02T10:00:00" },
];

function activeEventsFor(organizationId) {
  const scoped = allEvents.filter((event) => Number(event.organization_id) === Number(organizationId));
  const completedIds = new Set(scoped.filter((event) => event.event_action === "completed" && event.parent_event_id).map((event) => Number(event.parent_event_id)));
  return scoped.filter((event) => event.event_action === "planned" && !completedIds.has(Number(event.billing_next_step_event_id)));
}

const api = {
  billingActiveNextStepEvents: async (query) => {
    if (shouldFail) {
      throw new Error("Kontrolowany błąd pobierania");
    }
    if (initialRequestPending) {
      initialRequestPending = false;
      return new Promise((resolve) => {
        resolveInitialRequest = () => resolve({ organization_id: Number(query.organization_id), events: activeEventsFor(query.organization_id) });
      });
    }
    return { organization_id: Number(query.organization_id), events: activeEventsFor(query.organization_id) };
  },
  addBillingNextStepEvent: async (payload, organizationId) => {
    submittedPayloads.push(payload);
    if (allEvents.some((event) => event.event_action === "completed" && Number(event.parent_event_id) === Number(payload.parent_event_id))) {
      throw new Error("Ten krok został już zakończony");
    }
    const event = {
      billing_next_step_event_id: nextEventId++,
      organization_id: Number(organizationId),
      created_at: "2026-12-18T12:00:00",
      ...payload,
    };
    allEvents.push(event);
    return event;
  },
};

require("../src/modules/billing/billingModel.ts");
const originalLoad = Module._load;
Module._load = function loadWithMocks(request, parent, isMain) {
  if (request === "next/link") {
    return function Link({ children, href, ...props }) {
      const React = require("react");
      return React.createElement("a", { ...props, href }, children);
    };
  }
  if (request === "lucide-react") {
    const React = require("react");
    const Icon = (props) => React.createElement("svg", props);
    return { ArrowLeft: Icon, CheckCircle2: Icon, ListChecks: Icon, RefreshCw: Icon };
  }
  if (request === "@/context/ActiveOrganizationContext" || request.endsWith(`${path.sep}context${path.sep}ActiveOrganizationContext.tsx`)) {
    return {
      useActiveOrganization: () => ({
        selectedOrganization: { id: currentOrganizationId, name: `Organizacja ${currentOrganizationId}`, isActive: true },
        selectedOrganizationId: currentOrganizationId,
        status: "ready",
      }),
    };
  }
  if (request === "@/lib/api" || request.endsWith(`${path.sep}lib${path.sep}api.ts`)) {
    return { api };
  }
  return originalLoad.call(this, request, parent, isMain);
};

const dom = new JSDOM("<!doctype html><html><body><div id=\"root\"></div></body></html>", {
  url: "http://127.0.0.1:3000/rozliczenia/kroki",
});
globalThis.window = dom.window;
globalThis.document = dom.window.document;
globalThis.navigator = dom.window.navigator;
globalThis.HTMLElement = dom.window.HTMLElement;
globalThis.Event = dom.window.Event;
globalThis.IS_REACT_ACT_ENVIRONMENT = true;

const React = require("react");
const { act } = React;
const { createRoot } = require("react-dom/client");
const { BillingNextStepsOverviewPage } = require("../src/modules/billing/BillingNextStepsOverviewPage.tsx");

function buttonByText(container, text) {
  return [...container.querySelectorAll("button")].find((button) => button.textContent.trim() === text);
}

async function settle() {
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
}

async function run() {
  const container = document.getElementById("root");
  const root = createRoot(container);

  await act(async () => {
    root.render(React.createElement(BillingNextStepsOverviewPage));
  });
  assert.match(container.textContent, /Ladowanie danych/);
  await act(async () => {
    resolveInitialRequest();
  });
  await settle();

  assert.match(container.textContent, /Następne kroki/);
  assert.equal(container.querySelectorAll("tbody tr").length, 6);
  assert.equal([...container.querySelectorAll("tbody tr")].filter((row) => row.textContent.includes("Dwa takie same")).length, 2);
  assert.equal(container.querySelector('a[href="/rozliczenia/platnicy/7"]').textContent, "Płatnik #7");
  assert.equal(container.querySelector('a[href="/rozliczenia/wplaty/8"]').textContent, "Wpłata #8");
  assert.equal(container.querySelector('a[href="/rozliczenia/sprawy"]').textContent, "Sprawa rozliczeniowa");
  assert.match(container.textContent, /Nieobsługiwany lub historyczny cel/);

  await act(async () => {
    buttonByText(container, "Zaległe (1)").dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true }));
  });
  assert.match(container.textContent, /Zaległy telefon/);
  assert.ok(!container.textContent.includes("Przyszła wpłata"));

  await act(async () => {
    buttonByText(container, "Dzisiaj (0)").dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true }));
  });
  assert.match(container.textContent, /Brak kroków dla wybranego filtra/);

  await act(async () => {
    buttonByText(container, "Wszystkie (6)").dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true }));
  });
  const firstComplete = container.querySelector('button[data-next-step-id="101"]');
  assert.ok(firstComplete);
  await act(async () => {
    firstComplete.dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true }));
    firstComplete.dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true }));
  });
  await settle();

  const completedPayloads = submittedPayloads.filter((payload) => payload.event_action === "completed");
  assert.equal(completedPayloads.length, 1);
  assert.deepEqual(completedPayloads[0], {
    parent_event_id: 101,
    target_type: "billing_summary",
    step_type: "other",
    event_action: "completed",
    title: "Dwa takie same",
  });
  assert.equal(container.querySelector('button[data-next-step-id="101"]'), null);
  assert.ok(container.querySelector('button[data-next-step-id="102"]'));
  assert.equal([...container.querySelectorAll("tbody tr")].filter((row) => row.textContent.includes("Dwa takie same")).length, 1);

  const actionLabels = [...container.querySelectorAll("button")].map((button) => button.textContent.trim());
  assert.ok(!actionLabels.includes("Odłóż"));
  assert.ok(!actionLabels.includes("Usuń"));
  assert.ok(!actionLabels.includes("Edytuj"));

  currentOrganizationId = "43";
  await act(async () => {
    root.render(React.createElement(BillingNextStepsOverviewPage));
  });
  assert.ok(!container.textContent.includes("Dwa takie same"));
  await settle();
  assert.match(container.textContent, /Tylko druga organizacja/);
  assert.ok(!container.textContent.includes("Zaległy telefon"));

  currentOrganizationId = "44";
  await act(async () => {
    root.render(React.createElement(BillingNextStepsOverviewPage));
  });
  await settle();
  assert.match(container.textContent, /Brak aktywnych kroków/);

  shouldFail = true;
  currentOrganizationId = "45";
  await act(async () => {
    root.render(React.createElement(BillingNextStepsOverviewPage));
  });
  await settle();
  assert.match(container.textContent, /Nie udało się wczytać następnych kroków/);
  assert.ok(buttonByText(container, "Spróbuj ponownie"));

  await act(async () => root.unmount());
  console.log("Billing next steps overview DOM tests passed.");
}

run().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
