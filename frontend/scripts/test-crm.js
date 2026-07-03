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
  CRM_CONTRACTORS_ENDPOINT,
  CRM_ORGANIZATION_REQUIRED_DESCRIPTION,
  CRM_ORGANIZATION_REQUIRED_TITLE,
  CRM_PIPELINE_ENABLED,
  CRM_READ_ONLY,
  buildContractorRows,
  buildCrmKpis,
  canUseCrmOrganizationScope,
  contractorStatusTone,
  getCrmErrorState,
  hasCrmData,
  isCrmEmpty,
  readContractors,
} = require("../src/modules/crm/crmModel.ts");

function makeContractor(overrides = {}) {
  return {
    contractor_id: 31,
    name: "Karta Kamdata",
    nip: "1234567890",
    email: "kontakt@example.test",
    phone: "500600700",
    is_new: 1,
    last_invoice_date: "2099-04-10",
    last_invoice_number: "FV/10/2099",
    invoice_count: 3,
    notes: "Kontrahent testowy",
    organization_name: "CASI",
    organization_slug: "casi",
    created_at: "2099-04-01T08:00",
    updated_at: "2099-04-12T12:30",
    ...overrides,
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

const contractors = readContractors([makeContractor()]);
assert.equal(contractors.length, 1);
assert.equal(contractors[0].contractor_id, 31);
assert.equal(contractors[0].is_new, true);
assert.equal(contractors[0].invoice_count, 3);

const rows = buildContractorRows(contractors);
assert.equal(rows[0].nameLabel, "Karta Kamdata");
assert.equal(rows[0].nipLabel, "1234567890");
assert.equal(rows[0].contactLabel, "kontakt@example.test");
assert.equal(rows[0].statusLabel, "Nowy");
assert.equal(rows[0].statusTone, "info");
assert.equal(rows[0].invoiceCountLabel, "3");
assert.equal(rows[0].lastInvoiceLabel, "FV/10/2099 · 2099-04-10");
assert.equal(rows[0].organizationLabel, "CASI");
assert.equal(rows[0].updatedLabel, "2099-04-12 12:30");

assert.equal(contractorStatusTone(makeContractor({ is_new: true, invoice_count: 0 })), "info");
assert.equal(contractorStatusTone(makeContractor({ is_new: false, invoice_count: 2 })), "ok");
assert.equal(contractorStatusTone(makeContractor({ is_new: false, invoice_count: 0 })), "neutral");

const kpis = buildCrmKpis(readContractors([
  makeContractor({ contractor_id: 1, is_new: 1, email: "a@example.test", phone: null, invoice_count: 1 }),
  makeContractor({ contractor_id: 2, is_new: 0, email: null, phone: null, invoice_count: 0 }),
  makeContractor({ contractor_id: 3, is_new: 0, email: null, phone: "111222333", invoice_count: 4 }),
]));
assert.deepEqual(kpis, {
  total: 3,
  newCount: 1,
  knownCount: 2,
  missingContactCount: 1,
  linkedToInvoicesCount: 2,
});

assert.equal(hasCrmData("ready", contractors), true);
assert.equal(isCrmEmpty("ready", []), true);
assert.equal(hasCrmData("loading", contractors), false);

assert.equal(CRM_CONTRACTORS_ENDPOINT, "/contractors");
assert.equal(CRM_READ_ONLY, true);
assert.equal(CRM_PIPELINE_ENABLED, false);
assert.equal(CRM_ORGANIZATION_REQUIRED_TITLE, "Wybierz organizacje, aby zobaczyc CRM");
assert.match(CRM_ORGANIZATION_REQUIRED_DESCRIPTION, /organization_id/);
assert.equal(canUseCrmOrganizationScope(null), false);
assert.equal(canUseCrmOrganizationScope(""), false);
assert.equal(canUseCrmOrganizationScope("   "), false);
assert.equal(canUseCrmOrganizationScope("42"), true);
assert.equal(canUseCrmOrganizationScope(42), true);
assert.deepEqual(withActiveOrganizationQuery("42", { only_new: 1 }), { only_new: 1, organization_id: "42" });

assert.throws(() => readContractors({ contractors: [] }), ApiContractError);
assert.throws(() => readContractors([{ name: "Brak ID" }]), ApiContractError);

assert.equal(getCrmErrorState(new ApiError("Brak sesji", 401, {})).status, "unauthenticated");
assert.equal(getCrmErrorState(new ApiError("Brak uprawnien", 403, {})).status, "forbidden");
assert.equal(getCrmErrorState(new ApiError("Backend padl", 500, {})).status, "server-error");
assert.equal(getCrmErrorState(new ApiContractError(CRM_CONTRACTORS_ENDPOINT, {})).title, "Niepoprawny format CRM");

async function main() {
  await withMockedFetch(
    async (url, options) => {
      assert.equal(url, `/api${CRM_CONTRACTORS_ENDPOINT}?organization_id=42`);
      assert.equal(options.method, "GET");
      assert.equal(options.body, undefined);
      return jsonResponse(200, [makeContractor()]);
    },
    async () => {
      const payload = await api.contractors(withActiveOrganizationQuery("42"));
      const nextContractors = readContractors(payload);
      assert.equal(nextContractors.length, 1);
      assert.equal(nextContractors[0].contractor_id, 31);
    },
  );

  await withMockedFetch(
    async (url, options) => {
      assert.equal(url, `/api${CRM_CONTRACTORS_ENDPOINT}?only_new=1&organization_id=42`);
      assert.equal(options.method, "GET");
      return jsonResponse(200, []);
    },
    async () => {
      const payload = await api.contractors(withActiveOrganizationQuery("42", { only_new: 1 }));
      const emptyContractors = readContractors(payload);
      assert.equal(isCrmEmpty("ready", emptyContractors), true);
      assert.equal(hasCrmData("ready", emptyContractors), false);
    },
  );

  console.log("CRM regression tests passed.");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
