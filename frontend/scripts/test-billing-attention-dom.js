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
    return [".ts", ".tsx", ".js", ".jsx"].map((candidate) => `${resolved}${candidate}`).find(fs.existsSync) ?? resolved;
  }
  return originalResolveFilename.call(this, request, parent, isMain, options);
};

const React = require("react");
const { createRoot } = require("react-dom/client");
const actualApi = require("../src/lib/api.ts");
const originalLoad = Module._load;

let organizationContext = { selectedOrganizationId: "42", status: "ready" };
let attentionRequest = () => Promise.reject(new Error("Brak mocka attention"));
const apiMock = {
  billingNextStepAttention: (query) => attentionRequest(query),
};

Module._load = function loadWithMocks(request, parent, isMain) {
  if (request === "@/lib/api") {
    return { ...actualApi, api: apiMock };
  }
  if (request === "@/context/ActiveOrganizationContext") {
    return { useActiveOrganization: () => organizationContext };
  }
  if (request === "next/link") {
    return function Link({ children, href, ...props }) {
      return React.createElement("a", { href, ...props }, children);
    };
  }
  return originalLoad.call(this, request, parent, isMain);
};

const { BillingNextStepAttentionPanel } = require("../src/modules/dashboard/BillingNextStepAttentionPanel.tsx");

const dom = new JSDOM("<!doctype html><html><body><div id='root'></div></body></html>", { url: "http://localhost/pulpit" });
global.window = dom.window;
global.document = dom.window.document;
global.navigator = dom.window.navigator;
global.HTMLElement = dom.window.HTMLElement;
global.MouseEvent = dom.window.MouseEvent;
global.IS_REACT_ACT_ENVIRONMENT = true;

function candidate(id, date, reasonCode, overrides = {}) {
  return {
    billing_next_step_event_id: id,
    organization_id: Number(organizationContext.selectedOrganizationId),
    reason_code: reasonCode,
    planned_for: date,
    target_type: "payer",
    target_id: 7,
    related_issue_key: null,
    step_type: "call",
    title: `Krok ${id}`,
    target_label: "Płatnik #7",
    target_href: "/rozliczenia/platnicy/7",
    created_at: `2026-12-10T10:00:0${id}`,
    ...overrides,
  };
}

function payload(organizationId, candidates) {
  return {
    organization_id: Number(organizationId),
    as_of_date: "2026-12-18",
    overdue_count: candidates.filter((item) => item.reason_code === "overdue").length,
    due_today_count: candidates.filter((item) => item.reason_code === "due_today").length,
    attention_count: candidates.length,
    candidates,
  };
}

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}

async function flush() {
  await React.act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
}

async function main() {
  const container = document.getElementById("root");
  const root = createRoot(container);
  const firstRequest = deferred();
  attentionRequest = () => firstRequest.promise;

  await React.act(async () => {
    root.render(React.createElement(BillingNextStepAttentionPanel));
  });
  assert.match(container.textContent, /Ladowanie danych/);

  const firstCandidates = [
    candidate(1, "2026-12-14", "overdue"),
    candidate(2, "2026-12-15", "overdue", { title: "Identyczny krok" }),
    candidate(3, "2026-12-15", "overdue", { title: "Identyczny krok" }),
    candidate(4, "2026-12-16", "overdue", { target_label: "Cel historyczny", target_href: null }),
    candidate(5, "2026-12-17", "overdue"),
    candidate(6, "2026-12-18", "due_today"),
  ];
  await React.act(async () => {
    firstRequest.resolve(payload(42, firstCandidates));
    await firstRequest.promise;
  });

  assert.match(container.textContent, /Rozliczenia — wymagają uwagi/);
  assert.match(container.textContent, /Zaległe 5/);
  assert.match(container.textContent, /Dzisiaj 1/);
  assert.match(container.textContent, /Łącznie 6/);
  assert.equal(container.querySelectorAll("[data-attention-event-id]").length, 5);
  assert.equal(container.textContent.match(/Identyczny krok/g).length, 2);
  assert.match(container.textContent, /Cel historyczny — brak bezpiecznego linku/);
  assert.equal(container.querySelector('a[href="/rozliczenia/kroki"]').textContent, "Pokaż wszystkie");
  assert.equal(container.querySelector('a[href="/rozliczenia/platnicy/7"]') !== null, true);
  assert.doesNotMatch(container.textContent, /Oznacz jako wykonany|Odłóż|Usuń|Edytuj|wyślij automatycznie/i);

  organizationContext = { selectedOrganizationId: "84", status: "ready" };
  const secondRequest = deferred();
  attentionRequest = () => secondRequest.promise;
  await React.act(async () => {
    root.render(React.createElement(BillingNextStepAttentionPanel));
  });
  assert.doesNotMatch(container.textContent, /Identyczny krok/);
  assert.match(container.textContent, /Ladowanie danych/);
  await React.act(async () => {
    secondRequest.resolve(payload(84, []));
    await secondRequest.promise;
  });
  assert.match(container.textContent, /Na dziś nic nie wymaga uwagi/);
  assert.match(container.textContent, /Przyszłe kroki i kroki bez daty nie są tu pokazywane/);

  organizationContext = { selectedOrganizationId: "85", status: "ready" };
  let retryCount = 0;
  attentionRequest = async () => {
    retryCount += 1;
    if (retryCount === 1) {
      throw new actualApi.ApiError("Kontrolowany blad", 500, {});
    }
    return payload(85, [candidate(9, "2026-12-18", "due_today", { organization_id: 85 })]);
  };
  await React.act(async () => {
    root.render(React.createElement(BillingNextStepAttentionPanel));
  });
  await flush();
  assert.match(container.textContent, /Nie udalo sie pobrac krokow/);
  const retryButton = Array.from(container.querySelectorAll("button")).find((button) => button.textContent.includes("Spróbuj ponownie"));
  assert.ok(retryButton);
  await React.act(async () => {
    retryButton.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  });
  await flush();
  assert.equal(retryCount, 2);
  assert.match(container.textContent, /Krok 9/);
  assert.match(container.textContent, /2026-12-18/);

  await React.act(async () => root.unmount());
  console.log("Billing attention dashboard DOM tests passed.");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
