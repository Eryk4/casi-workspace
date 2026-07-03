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
  REPORTS_ENDPOINT,
  REPORTS_ORGANIZATION_REQUIRED_DESCRIPTION,
  REPORTS_ORGANIZATION_REQUIRED_TITLE,
  REPORTS_READ_ONLY,
  REPORT_EXPORTS_ENABLED,
  REPORT_GENERATOR_ENABLED,
  buildReportModuleLinks,
  buildReportSignals,
  buildReportsKpis,
  canUseReportsOrganizationScope,
  formatMoney,
  getReportsErrorState,
  hasReportsData,
  isReportsEmpty,
  readReportsSnapshot,
} = require("../src/modules/reports/reportsModel.ts");

function makeDashboard() {
  return {
    cards: {
      nowe_faktury: 3,
      do_weryfikacji: 4,
      podejrzenia_duplikatow: 1,
      pewne_duplikaty: 2,
      nowi_kontrahenci: 5,
      aktywne_przypomnienia: 7,
    },
    operational_alerts: [],
    active_reminders: [],
    knowledge_queue: [],
    recent_events: [],
  };
}

function jsonResponse(status, payload) {
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: {
      get: () => "application/json",
    },
    json: async () => payload,
    text: async () => JSON.stringify(payload),
  };
}

async function withMockedFetch(fetchImplementation, callback) {
  const previousFetch = global.fetch;
  global.fetch = fetchImplementation;

  try {
    await callback();
  } finally {
    if (previousFetch) {
      global.fetch = previousFetch;
    } else {
      delete global.fetch;
    }
  }
}

const snapshot = readReportsSnapshot({
  dashboard: makeDashboard(),
  workItems: [
    { work_item_id: 1, status: "w_toku", priority_level: "krytyczny", is_closed: false, is_sla_overdue: true },
    { work_item_id: 2, status: "zamkniete", priority_level: "niski", is_closed: true },
  ],
  documents: {
    documents: [
      { knowledge_document_id: 10, processing_status: "processing", business_status: "roboczy", workflow_status: "processing" },
      { knowledge_document_id: 11, processing_status: "done", business_status: "obowiazujacy", workflow_status: "stable" },
    ],
  },
  billingBalances: [
    { billing_payer_id: 50, balance_due: 120.5 },
    { billing_payer_id: 51, balance_due: -20.5 },
  ],
  contractors: [
    { contractor_id: 70, is_new: 1, invoice_count: 3 },
    { contractor_id: 71, is_new: 0, invoice_count: 0 },
  ],
});

assert.equal(snapshot.workItems.length, 2);
assert.equal(snapshot.documents.length, 2);
assert.equal(snapshot.contractors[0].is_new, true);

const kpis = buildReportsKpis(snapshot);
assert.deepEqual(kpis, {
  invoicesToAttention: 7,
  openWorkItems: 1,
  documentsToAttention: 1,
  billingBalanceDue: 100,
  contractorsTotal: 2,
});

const signals = buildReportSignals(snapshot);
assert.equal(signals.length, 5);
assert.equal(signals[0].id, "invoices");
assert.equal(signals[0].statusTone, "warning");
assert.equal(signals[1].id, "work-items");
assert.equal(signals[1].statusTone, "danger");
assert.equal(signals[3].value, "100,00 PLN");

const modules = buildReportModuleLinks(snapshot);
assert.equal(modules.length, 4);
assert.equal(modules[0].href, "/pulpit");
assert.equal(modules[3].href, "/rozliczenia");

const partialSnapshot = readReportsSnapshot({
  dashboard: makeDashboard(),
  missingSources: ["billingBalances", "contractors"],
});
assert.equal(partialSnapshot.missingSources.length, 2);
assert.equal(buildReportsKpis(partialSnapshot).invoicesToAttention, 7);
assert.equal(buildReportsKpis(partialSnapshot).billingBalanceDue, 0);

const emptySnapshot = readReportsSnapshot({});
assert.equal(hasReportsData("ready", snapshot), true);
assert.equal(isReportsEmpty("ready", emptySnapshot), true);
assert.equal(hasReportsData("loading", snapshot), false);

assert.equal(formatMoney(1234.5), "1234,50 PLN");
assert.equal(REPORTS_ENDPOINT, "/reports/operational-summary");
assert.equal(REPORTS_READ_ONLY, true);
assert.equal(REPORT_EXPORTS_ENABLED, false);
assert.equal(REPORT_GENERATOR_ENABLED, false);
assert.equal(REPORTS_ORGANIZATION_REQUIRED_TITLE, "Wybierz organizacje, aby zobaczyc raporty");
assert.match(REPORTS_ORGANIZATION_REQUIRED_DESCRIPTION, /organization_id/);
assert.equal(canUseReportsOrganizationScope(null), false);
assert.equal(canUseReportsOrganizationScope(""), false);
assert.equal(canUseReportsOrganizationScope("   "), false);
assert.equal(canUseReportsOrganizationScope("42"), true);
assert.equal(canUseReportsOrganizationScope(42), true);
assert.deepEqual(withActiveOrganizationQuery("42", { limit: 100 }), { limit: 100, organization_id: "42" });

assert.throws(() => readReportsSnapshot([]), ApiContractError);
assert.throws(() => readReportsSnapshot({ workItems: [{ title: "Brak ID" }] }), ApiContractError);
assert.throws(() => readReportsSnapshot({ documents: [] }), ApiContractError);

assert.equal(getReportsErrorState(new ApiError("Brak sesji", 401, {})).status, "unauthenticated");
assert.equal(getReportsErrorState(new ApiError("Brak uprawnien", 403, {})).status, "forbidden");
assert.equal(getReportsErrorState(new ApiError("Backend padl", 500, {})).status, "server-error");
assert.equal(getReportsErrorState(new ApiContractError(REPORTS_ENDPOINT, {})).title, "Niepoprawny format raportow");

async function main() {
  const expectedCalls = [
    { url: "/api/dashboard?organization_id=42", payload: makeDashboard() },
    {
      url: "/api/work-items?limit=100&only_open=1&organization_id=42",
      payload: [{ work_item_id: 1, status: "w_toku", priority_level: "krytyczny", is_closed: false }],
    },
    {
      url: "/api/knowledge/documents?organization_id=42",
      payload: { documents: [{ knowledge_document_id: 10, processing_status: "processing" }] },
    },
    { url: "/api/billing/ledger/balances?organization_id=42", payload: [{ billing_payer_id: 50, balance_due: 120.5 }] },
    { url: "/api/contractors?organization_id=42", payload: [{ contractor_id: 70, is_new: 1, invoice_count: 3 }] },
  ];
  const seenUrls = [];

  await withMockedFetch(
    async (url, options) => {
      seenUrls.push(url);
      assert.equal(options.method, "GET");
      assert.equal(options.body, undefined);
      const match = expectedCalls.find((call) => call.url === url);
      assert.ok(match, `Unexpected reports source URL: ${url}`);
      return jsonResponse(200, match.payload);
    },
    async () => {
      const organizationQuery = withActiveOrganizationQuery("42");
      const [dashboard, workItems, documents, billingBalances, contractors] = await Promise.all([
        api.dashboard(organizationQuery),
        api.workItems(withActiveOrganizationQuery("42", { limit: 100, only_open: 1 })),
        api.knowledgeDocuments(organizationQuery),
        api.ledgerBalances(organizationQuery),
        api.contractors(organizationQuery),
      ]);
      const scopedSnapshot = readReportsSnapshot({
        dashboard,
        workItems,
        documents,
        billingBalances,
        contractors,
        missingSources: [],
      });
      assert.equal(buildReportsKpis(scopedSnapshot).invoicesToAttention, 7);
      assert.equal(buildReportsKpis(scopedSnapshot).openWorkItems, 1);
      assert.equal(buildReportsKpis(scopedSnapshot).billingBalanceDue, 120.5);
    },
  );

  assert.deepEqual(seenUrls.sort(), expectedCalls.map((call) => call.url).sort());

  const emptyScopedSnapshot = readReportsSnapshot({
    dashboard: undefined,
    workItems: [],
    documents: { documents: [] },
    billingBalances: [],
    contractors: [],
    missingSources: [],
  });
  assert.equal(isReportsEmpty("ready", emptyScopedSnapshot), true);

  console.log("Reports regression tests passed.");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
