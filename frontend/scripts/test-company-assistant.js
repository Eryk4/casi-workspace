const assert = require("node:assert/strict");
const fs = require("node:fs");
const Module = require("node:module");
const path = require("node:path");
const ts = require("typescript");

require.extensions[".ts"] = function compileTypeScript(module, filename) {
  const source = fs.readFileSync(filename, "utf8");
  const output = ts.transpileModule(source, {
    compilerOptions: {
      esModuleInterop: true,
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2022,
    },
    fileName: filename,
  });

  module._compile(output.outputText, filename);
};

const srcRoot = path.join(__dirname, "..", "src");
const originalResolveFilename = Module._resolveFilename;

Module._resolveFilename = function resolveAlias(request, parent, isMain, options) {
  if (request.startsWith("@/")) {
    const resolved = path.join(srcRoot, request.slice(2));
    const filePath = [".ts", ".tsx", ".js", ".jsx"].map((extension) => `${resolved}${extension}`).find((candidate) => fs.existsSync(candidate));

    return filePath ?? resolved;
  }

  return originalResolveFilename.call(this, request, parent, isMain, options);
};

const { ApiContractError, ApiError, api } = require("../src/lib/api.ts");
const { withActiveOrganizationQuery } = require("../src/context/organizationContextModel.ts");
const {
  COMPANY_ASSISTANT_AI_AGENT_ENABLED,
  COMPANY_ASSISTANT_ORGANIZATION_REQUIRED_DESCRIPTION,
  COMPANY_ASSISTANT_ORGANIZATION_REQUIRED_TITLE,
  COMPANY_ASSISTANT_READ_ONLY,
  buildCompanyAssistantAttentionRows,
  buildCompanyAssistantKnowledgeRows,
  buildCompanyAssistantKpis,
  canUseCompanyAssistantOrganizationScope,
  getCompanyAssistantErrorState,
  hasCompanyAssistantData,
  isCompanyAssistantEmpty,
  readCompanyAssistantSnapshot,
  sourceError,
  sourceMissing,
  sourceReady,
} = require("../src/modules/assistant-company/companyAssistantModel.ts");

function jsonResponse(status, payload) {
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: {
      get(name) {
        return name.toLowerCase() === "content-type" ? "application/json" : null;
      },
    },
    json: async () => payload,
    text: async () => JSON.stringify(payload),
  };
}

async function withMockedFetch(handler, callback) {
  const originalFetch = global.fetch;
  global.fetch = async (url, options = {}) => handler(String(url), options);

  try {
    await callback();
  } finally {
    global.fetch = originalFetch;
  }
}

function makeDashboard() {
  return {
    cards: {
      nowe_faktury: 3,
      do_weryfikacji: 2,
      podejrzenia_duplikatow: 1,
      pewne_duplikaty: 0,
      nowi_kontrahenci: 4,
      aktywne_przypomnienia: 1,
    },
    operational_alerts: [
      {
        severity: "warning",
        category: "knowledge",
        title: "Dokument wymaga decyzji",
        description: "Polityka firmowa czeka na akceptacje.",
      },
    ],
    active_reminders: [],
    knowledge_queue: [],
    recent_events: [],
  };
}

function makeDocuments() {
  return {
    documents: [
      {
        knowledge_document_id: 11,
        title: "Procedura obslugi klienta",
        file_name: "procedura.pdf",
        business_status: "obowiazujacy",
        business_status_label: "Obowiazujacy",
        workflow_status: "stable",
        workflow_status_label: "Stabilny",
        owner_user_label: "Ola CASI",
        updated_at: "2099-06-30T10:00",
        use_in_assistant: true,
      },
      {
        knowledge_document_id: 12,
        title: "Regulamin delegacji",
        business_status: "do_akceptacji",
        business_status_label: "Do akceptacji",
        workflow_status: "review_needed",
        workflow_status_label: "Wymaga przegladu",
        owner_user_label: "Karol Manager",
      },
    ],
  };
}

function makeWorkItems() {
  return [
    {
      work_item_id: 31,
      title: "Wyjasnic brakujace dane klienta",
      status: "w_toku",
      priority_level: "wysoki",
      assigned_user_name: "Ola CASI",
      sla_state_label: "Ryzyko SLA",
      is_closed: false,
    },
  ];
}

function makeInvoiceInbox() {
  return {
    summary: {
      total_open_count: 2,
      generated_at: "2099-06-30T08:00",
    },
    sections: {
      verification: {
        title: "Do weryfikacji",
        description: "Faktury czekaja na operatora.",
        count: 2,
        items: [
          {
            invoice_id: 99,
            invoice_number: "FV/99",
          },
        ],
      },
    },
  };
}

const snapshot = readCompanyAssistantSnapshot({
  dashboard: makeDashboard(),
  documents: makeDocuments(),
  workItems: makeWorkItems(),
  invoiceInbox: makeInvoiceInbox(),
  sourceStates: [sourceReady("dashboard"), sourceReady("documents"), sourceReady("workItems"), sourceReady("invoices")],
});

const kpis = buildCompanyAssistantKpis(snapshot);
assert.deepEqual(kpis, {
  knowledgeDocuments: 2,
  readyKnowledgeDocuments: 1,
  openWorkItems: 1,
  invoicesToReview: 2,
  decisionSignals: 4,
});

const knowledgeRows = buildCompanyAssistantKnowledgeRows(snapshot);
assert.equal(knowledgeRows.length, 2);
assert.equal(knowledgeRows[0].title, "Procedura obslugi klienta");
assert.equal(knowledgeRows[0].statusTone, "ok");

const attentionRows = buildCompanyAssistantAttentionRows(snapshot);
assert.equal(attentionRows.length, 3);
assert.equal(attentionRows[0].typeLabel, "Work item");
assert.equal(attentionRows[1].typeLabel, "Sygnal");
assert.equal(attentionRows[2].typeLabel, "Faktury");

assert.equal(hasCompanyAssistantData("ready", snapshot), true);
assert.equal(isCompanyAssistantEmpty("ready", snapshot), false);
assert.equal(
  isCompanyAssistantEmpty(
    "ready",
    readCompanyAssistantSnapshot({
      dashboard: { ...makeDashboard(), operational_alerts: [], cards: { ...makeDashboard().cards, do_weryfikacji: 0 } },
      documents: { documents: [] },
      workItems: [],
      invoiceInbox: { summary: { total_open_count: 0 }, sections: {} },
      sourceStates: [sourceReady("dashboard"), sourceReady("documents"), sourceReady("workItems"), sourceReady("invoices")],
    }),
  ),
  true,
);

const partialSnapshot = readCompanyAssistantSnapshot({
  documents: makeDocuments(),
  workItems: makeWorkItems(),
  sourceStates: [sourceMissing("dashboard"), sourceReady("documents"), sourceReady("workItems"), sourceError("invoices", new Error("Brak faktur"))],
});
assert.equal(partialSnapshot.dashboard, undefined);
assert.equal(partialSnapshot.invoiceInbox, undefined);
assert.equal(partialSnapshot.sourceStates.filter((source) => source.status === "error").length, 1);
assert.equal(buildCompanyAssistantKpis(partialSnapshot).knowledgeDocuments, 2);

assert.equal(COMPANY_ASSISTANT_ORGANIZATION_REQUIRED_TITLE, "Wybierz organizacje, aby zobaczyc Asystenta Firmowego");
assert.match(COMPANY_ASSISTANT_ORGANIZATION_REQUIRED_DESCRIPTION, /organization_id/);
assert.equal(canUseCompanyAssistantOrganizationScope(null), false);
assert.equal(canUseCompanyAssistantOrganizationScope(""), false);
assert.equal(canUseCompanyAssistantOrganizationScope("42"), true);
assert.deepEqual(withActiveOrganizationQuery("42"), { organization_id: "42" });
assert.equal(COMPANY_ASSISTANT_READ_ONLY, true);
assert.equal(COMPANY_ASSISTANT_AI_AGENT_ENABLED, false);

assert.throws(() => readCompanyAssistantSnapshot([]), ApiContractError);
assert.equal(getCompanyAssistantErrorState(new ApiError("Brak sesji", 401, {})).status, "unauthenticated");
assert.equal(getCompanyAssistantErrorState(new ApiError("Brak dostepu", 403, {})).status, "forbidden");
assert.equal(getCompanyAssistantErrorState(new ApiError("Backend padl", 500, {})).status, "server-error");
assert.equal(getCompanyAssistantErrorState(new ApiContractError("/assistant-company", {})).title, "Niepoprawny format Asystenta Firmowego");

const expectedRequests = new Map([
  ["/api/dashboard?organization_id=42", makeDashboard()],
  ["/api/knowledge/documents?organization_id=42", makeDocuments()],
  ["/api/work-items?limit=50&only_open=1&organization_id=42", makeWorkItems()],
  ["/api/invoices/verification-inbox?organization_id=42", makeInvoiceInbox()],
]);

withMockedFetch(
  async (url, options) => {
    assert.equal(options.method, "GET");
    assert.equal(options.credentials, "include");
    assert.equal(options.body, undefined);
    assert.equal(expectedRequests.has(url), true, `Unexpected URL ${url}`);
    return jsonResponse(200, expectedRequests.get(url));
  },
  async () => {
    const organizationQuery = withActiveOrganizationQuery("42");
    const [dashboard, documents, workItems, invoiceInbox] = await Promise.all([
      api.dashboard(organizationQuery),
      api.knowledgeDocuments(organizationQuery),
      api.workItems(withActiveOrganizationQuery("42", { limit: 50, only_open: 1 })),
      api.invoiceVerificationInbox(organizationQuery),
    ]);

    const scopedSnapshot = readCompanyAssistantSnapshot({
      dashboard,
      documents,
      workItems,
      invoiceInbox,
      sourceStates: [sourceReady("dashboard"), sourceReady("documents"), sourceReady("workItems"), sourceReady("invoices")],
    });

    assert.equal(buildCompanyAssistantKpis(scopedSnapshot).invoicesToReview, 2);
    assert.equal(COMPANY_ASSISTANT_READ_ONLY, true);
    assert.equal(COMPANY_ASSISTANT_AI_AGENT_ENABLED, false);
  },
).then(
  () => {
    console.log("Company Assistant regression tests passed.");
  },
  (error) => {
    console.error(error);
    process.exitCode = 1;
  },
);
