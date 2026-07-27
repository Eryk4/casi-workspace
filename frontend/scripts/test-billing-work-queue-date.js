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
const issueKey = "payment:61:payer-only:wplata-do-wyjasnienia";
let submittedPayload = null;
let submittedOrganizationId = null;
const submittedPayloads = [];
const nextStepEvents = [
  {
    billing_next_step_event_id: 7001,
    organization_id: 42,
    target_type: "work_queue_issue",
    related_issue_key: issueKey,
    step_type: "check_payment",
    event_action: "planned",
    title: "Sprawdzic istniejacy krok",
    note_text: "Kontekst testowy",
    planned_for: "2026-12-20",
    created_at: "2026-12-01T10:00:00",
  },
];

const api = {
  addBillingNextStepEvent: async (payload, organizationId) => {
    submittedPayload = payload;
    submittedOrganizationId = organizationId;
    submittedPayloads.push(payload);
    const event = {
      billing_next_step_event_id: 7001 + nextStepEvents.length,
      organization_id: Number(organizationId),
      created_at: `2026-12-${String(nextStepEvents.length + 1).padStart(2, "0")}T11:00:00`,
      ...payload,
    };
    nextStepEvents.push(event);
    return event;
  },
  billingCharges: async () => [],
  billingLedgerMatches: async () => [],
  billingNextStepEvents: async () => ({ organization_id: 42, events: nextStepEvents }),
  billingPayerNotes: async () => [],
  billingPayers: async () => [],
  billingPaymentReviewStatuses: async () => ({ organization_id: 42, statuses: [] }),
  billingStudents: async () => [],
  billingTransactions: async () => [],
  billingWorkQueueEvents: async () => ({ organization_id: 42, events: [] }),
  ledgerBalances: async () => [],
};

const issue = {
  amountLabel: "123,45 zl",
  href: "/rozliczenia/sprawy",
  id: issueKey,
  issueKey,
  nextStep: "Wyjasnic wplate",
  payerHref: "/rozliczenia/platnicy/14",
  payerLabel: "Platnik testowy",
  paymentHref: "/rozliczenia/wplaty/61",
  priority: "wysoki",
  reason: "Wplata wymaga wyjasnienia",
  tone: "warning",
  type: "Wplata do wyjasnienia",
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
    return { ArrowLeft: Icon, ListChecks: Icon, RefreshCw: Icon };
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
  if (request === "./billingModel" && parent?.filename.endsWith("BillingWorkQueuePage.tsx")) {
    return {
      ...billingModel,
      buildBillingWorkQueueView: () => ({
        checkedRows: [],
        contactRows: [],
        contextItems: [],
        firstRows: [issue],
        handledRows: [],
        overpaymentRows: [],
        paymentRows: [],
        snoozedRows: [],
        summary: {
          checkedCount: 0,
          contactCount: 0,
          debtCount: 0,
          handledCount: 0,
          highPriorityCount: 1,
          needsReviewCount: 1,
          overpaymentCount: 0,
          snoozedCount: 0,
        },
      }),
      readBillingBalances: () => [],
      readBillingCharges: () => [],
      readBillingNextStepEvents: (payload) => billingModel.readBillingNextStepEvents(payload),
      readBillingPayerNotes: () => [],
      readBillingPaymentMatches: () => [],
      readBillingPaymentReviewStatuses: () => ({ organization_id: 42, statuses: [] }),
      readBillingPayers: () => [],
      readBillingStudents: () => [],
      readBillingTransactions: () => [],
      readBillingWorkQueueEvents: () => ({ organization_id: 42, events: [] }),
    };
  }

  return originalLoad.call(this, request, parent, isMain);
};

const dom = new JSDOM("<!doctype html><html><body><div id=\"root\"></div></body></html>", {
  url: "http://127.0.0.1:3000/rozliczenia/sprawy",
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
const { BillingWorkQueuePage } = require("../src/modules/billing/BillingWorkQueuePage.tsx");

function setInputValue(input, value) {
  const valueSetter = Object.getOwnPropertyDescriptor(dom.window.HTMLInputElement.prototype, "value").set;
  valueSetter.call(input, value);
  input.dispatchEvent(new dom.window.Event("input", { bubbles: true }));
}

async function run() {
  const container = document.getElementById("root");
  const root = createRoot(container);

  await act(async () => {
    root.render(React.createElement(BillingWorkQueuePage));
  });

  const form = Array.from(container.querySelectorAll("form")).find((candidate) =>
    candidate.textContent.includes("Zapisz krok"),
  );
  assert.ok(form, "Formularz dodawania nastepnego kroku powinien byc wyrenderowany");

  const dateInput = form.querySelector('input[type="date"]');
  const titleInput = form.querySelector('input[placeholder^="Np. Sprawdzic"], input[placeholder^="Np. Sprawdzić"]');
  assert.ok(dateInput, "Formularz powinien zawierac input type=date");
  assert.ok(titleInput, "Formularz powinien zawierac pole tytulu");

  await act(async () => {
    setInputValue(titleInput, "Sprawdzic wplate po terminie");
  });
  await act(async () => {
    setInputValue(dateInput, "2026-12-18");
  });
  assert.equal(dateInput.value, "2026-12-18");

  await act(async () => {
    form.dispatchEvent(new dom.window.Event("submit", { bubbles: true, cancelable: true }));
  });

  assert.deepEqual(submittedPayload, {
    target_type: "work_queue_issue",
    related_issue_key: issueKey,
    step_type: "check_payment",
    event_action: "planned",
    title: "Sprawdzic wplate po terminie",
    planned_for: "2026-12-18",
  });
  assert.equal(submittedOrganizationId, "42");

  const plannedRow = Array.from(container.querySelectorAll(".module-readiness__item")).find((candidate) =>
    candidate.textContent.includes("Sprawdzic istniejacy krok"),
  );
  assert.ok(plannedRow, "Aktywny krok powinien byc wyrenderowany");
  const completeButton = Array.from(plannedRow.querySelectorAll("button")).find((button) =>
    button.textContent.includes("Oznacz jako wykonany"),
  );
  assert.ok(completeButton, "Aktywny krok powinien miec akcje completed");

  await act(async () => {
    completeButton.dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true }));
    completeButton.dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true }));
  });

  const completedPayloads = submittedPayloads.filter((payload) => payload.event_action === "completed");
  assert.equal(completedPayloads.length, 1, "Podwojne klikniecie nie powinno wyslac drugiego zadania");
  assert.deepEqual(completedPayloads[0], {
    target_type: "work_queue_issue",
    related_issue_key: issueKey,
    step_type: "check_payment",
    event_action: "completed",
    title: "Sprawdzic istniejacy krok",
    planned_for: "2026-12-20",
  });
  assert.match(container.textContent, /Wykonano/);
  assert.equal(
    Array.from(container.querySelectorAll("button")).some((button) =>
      button.closest(".module-readiness__item")?.textContent.includes("Sprawdzic istniejacy krok") &&
      button.textContent.includes("Oznacz jako wykonany"),
    ),
    false,
  );

  await act(async () => {
    root.unmount();
  });
  dom.window.close();
  console.log("BillingWorkQueuePage planned_for and completed DOM regression tests passed.");
}

run().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
