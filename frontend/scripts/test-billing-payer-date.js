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
    const filePath = [".ts", ".tsx", ".js", ".jsx"]
      .map((candidateExtension) => `${resolved}${candidateExtension}`)
      .find((candidate) => fs.existsSync(candidate));

    return filePath ?? resolved;
  }

  return originalResolveFilename.call(this, request, parent, isMain, options);
};

const billingModel = require("../src/modules/billing/billingModel.ts");
const originalLoad = Module._load;
const payerId = 14;
let submittedPayload = null;
let submittedOrganizationId = null;

const api = {
  addBillingNextStepEvent: async (payload, organizationId) => {
    submittedPayload = payload;
    submittedOrganizationId = organizationId;
    return {};
  },
  billingCharges: async () => [],
  billingContactEvents: async () => ({ organization_id: 42, events: [] }),
  billingNextStepEvents: async () => ({ organization_id: 42, events: [] }),
  billingPayerNotes: async () => [],
  billingPayers: async () => [],
  billingStudents: async () => [],
  contractors: async () => [],
  invoices: async () => [],
  ledgerBalances: async () => [],
  workItems: async () => [],
};

const payerDetail = {
  balanceExplanationRows: [],
  balanceLabel: "0,00 zl",
  balanceMeaningLabel: "Rozliczony",
  chargedLabel: "0,00 zl",
  chargeRows: [],
  contactEventRows: [],
  contactLabel: "Brak danych",
  contextItems: [],
  invoiceRows: [],
  lastPaymentLabel: "Brak wplat",
  noteRows: [],
  paidLabel: "0,00 zl",
  payerTypeLabel: "Osoba",
  paymentIdentifierLabel: "Platnik 14",
  paymentRows: [],
  peopleRows: [],
  serviceRows: [],
  statusLabel: "Rozliczony",
  statusTone: "ok",
  title: "Platnik testowy",
  workItemRows: [],
};

Module._load = function loadWithComponentDependencies(request, parent, isMain) {
  if (request === "next/link") {
    return function Link({ children, href, ...props }) {
      const React = require("react");
      return React.createElement("a", { ...props, href }, children);
    };
  }
  if (request === "lucide-react") {
    const React = require("react");
    const Icon = (props) => React.createElement("svg", props);
    return {
      ArrowLeft: Icon,
      CreditCard: Icon,
      FileText: Icon,
      ListChecks: Icon,
      MessageSquareText: Icon,
      RefreshCw: Icon,
      UsersRound: Icon,
      WalletCards: Icon,
    };
  }
  if (
    request === "@/context/ActiveOrganizationContext" ||
    request.endsWith(`${path.sep}context${path.sep}ActiveOrganizationContext.tsx`)
  ) {
    return {
      useActiveOrganization: () => ({
        selectedOrganization: { name: "Organizacja testowa" },
        selectedOrganizationId: "42",
        status: "ready",
      }),
    };
  }
  if (request === "@/lib/api" || request.endsWith(`${path.sep}lib${path.sep}api.ts`)) {
    return { api };
  }
  if (request === "./billingModel" && parent?.filename.endsWith("BillingPayerDetailPage.tsx")) {
    return {
      ...billingModel,
      buildBillingPayerDetailView: () => payerDetail,
      readBillingBalances: () => [],
      readBillingCharges: () => [],
      readBillingContactEvents: () => ({ organization_id: 42, events: [] }),
      readBillingInvoices: () => [],
      readBillingNextStepEvents: () => ({ organization_id: 42, events: [] }),
      readBillingPayerNotes: () => [],
      readBillingPayers: () => [],
      readBillingStudents: () => [],
    };
  }

  return originalLoad.call(this, request, parent, isMain);
};

const dom = new JSDOM("<!doctype html><html><body><div id=\"root\"></div></body></html>", {
  url: `http://127.0.0.1:3000/rozliczenia/platnicy/${payerId}`,
});

globalThis.window = dom.window;
globalThis.document = dom.window.document;
globalThis.navigator = dom.window.navigator;
globalThis.HTMLElement = dom.window.HTMLElement;
globalThis.HTMLInputElement = dom.window.HTMLInputElement;
globalThis.Event = dom.window.Event;
globalThis.IS_REACT_ACT_ENVIRONMENT = true;

const React = require("react");
const { act } = React;
const { createRoot } = require("react-dom/client");
const { BillingPayerDetailPage } = require("../src/modules/billing/BillingPayerDetailPage.tsx");

function setInputValue(input, value) {
  const valueSetter = Object.getOwnPropertyDescriptor(dom.window.HTMLInputElement.prototype, "value").set;
  valueSetter.call(input, value);
  input.dispatchEvent(new dom.window.Event("input", { bubbles: true }));
}

async function run() {
  const container = document.getElementById("root");
  const root = createRoot(container);

  await act(async () => {
    root.render(React.createElement(BillingPayerDetailPage, { payerId }));
  });

  const dateInput = container.querySelector("#billing-payer-next-step-date");
  const titleInput = container.querySelector("#billing-payer-next-step-title");
  assert.ok(dateInput, "Formularz nastepnego kroku platnika powinien zawierac input type=date");
  assert.equal(dateInput.type, "date");
  assert.ok(titleInput, "Formularz nastepnego kroku platnika powinien zawierac pole tytulu");
  const form = dateInput.closest("form");
  assert.ok(form, "Formularz nastepnego kroku platnika powinien byc wyrenderowany");

  await act(async () => {
    setInputValue(titleInput, "Zadzwonic w sprawie rozliczenia");
  });
  await act(async () => {
    setInputValue(dateInput, "2026-12-18");
  });
  assert.equal(dateInput.value, "2026-12-18");

  await act(async () => {
    form.dispatchEvent(new dom.window.Event("submit", { bubbles: true, cancelable: true }));
  });

  assert.deepEqual(submittedPayload, {
    target_type: "payer",
    target_id: payerId,
    step_type: "call",
    event_action: "planned",
    title: "Zadzwonic w sprawie rozliczenia",
    planned_for: "2026-12-18",
  });
  assert.equal(submittedOrganizationId, "42");

  await act(async () => {
    root.unmount();
  });
  dom.window.close();
  console.log("BillingPayerDetailPage planned_for DOM regression test passed.");
}

run().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
