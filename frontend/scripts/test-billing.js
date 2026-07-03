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
  BILLING_BALANCES_ENDPOINT,
  BILLING_ORGANIZATION_REQUIRED_DESCRIPTION,
  BILLING_ORGANIZATION_REQUIRED_TITLE,
  BILLING_READ_ONLY,
  buildBillingBalanceRows,
  buildBillingKpis,
  billingBalanceTone,
  canUseBillingOrganizationScope,
  formatMoney,
  getBillingErrorState,
  hasBillingData,
  isBillingEmpty,
  readBillingBalances,
} = require("../src/modules/billing/billingModel.ts");

function makeBalance(overrides = {}) {
  return {
    billing_payer_id: 14,
    display_name: "Rodzina Kowalskich",
    contact_phone: "500600700",
    payment_identifier: "500600700",
    email: "rodzina@example.test",
    is_active: 1,
    total_charges: 520,
    total_matches: 300,
    balance_due: 220,
    last_payment_at: "2099-05-03",
    last_payment_amount: 300,
    last_payment_currency: "PLN",
    last_payment_title: "Czesne maj",
    last_payment_reference: "REF-1",
    matched_payment_count: 2,
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

const balances = readBillingBalances([makeBalance()]);
assert.equal(balances.length, 1);
assert.equal(balances[0].billing_payer_id, 14);
assert.equal(balances[0].is_active, true);
assert.equal(balances[0].total_charges, 520);
assert.equal(balances[0].balance_due, 220);

const rows = buildBillingBalanceRows(balances);
assert.equal(rows[0].payerLabel, "Rodzina Kowalskich");
assert.equal(rows[0].contactLabel, "500600700");
assert.equal(rows[0].statusLabel, "Do zaplaty");
assert.equal(rows[0].statusTone, "warning");
assert.equal(rows[0].totalChargesLabel, "520,00 PLN");
assert.equal(rows[0].totalMatchesLabel, "300,00 PLN");
assert.equal(rows[0].balanceDueLabel, "220,00 PLN");
assert.equal(rows[0].lastPaymentLabel, "2099-05-03 · 300,00 PLN");
assert.equal(rows[0].matchedPaymentCountLabel, "2");

assert.equal(billingBalanceTone(makeBalance({ balance_due: 0 })), "ok");
assert.equal(billingBalanceTone(makeBalance({ balance_due: -50 })), "info");
assert.equal(readBillingBalances([makeBalance({ balance_due: 0, is_active: 0 })])[0].is_active, false);
assert.equal(billingBalanceTone(readBillingBalances([makeBalance({ balance_due: 0, is_active: 0 })])[0]), "neutral");

const kpis = buildBillingKpis(readBillingBalances([
  makeBalance({ billing_payer_id: 1, total_charges: 100, total_matches: 80, balance_due: 20 }),
  makeBalance({ billing_payer_id: 2, total_charges: 200, total_matches: 200, balance_due: 0 }),
  makeBalance({ billing_payer_id: 3, total_charges: 120.55, total_matches: 150.55, balance_due: -30, is_active: 0 }),
]));
assert.deepEqual(kpis, {
  payerCount: 3,
  activePayerCount: 2,
  totalCharges: 420.55,
  totalMatches: 430.55,
  totalBalanceDue: -10,
  overdueCount: 1,
  paidOrSettledCount: 2,
});

assert.equal(formatMoney(1234.5), "1234,50 PLN");
assert.equal(hasBillingData("ready", balances), true);
assert.equal(isBillingEmpty("ready", []), true);
assert.equal(hasBillingData("loading", balances), false);

assert.equal(BILLING_BALANCES_ENDPOINT, "/billing/ledger/balances");
assert.equal(BILLING_READ_ONLY, true);
assert.equal(BILLING_ORGANIZATION_REQUIRED_TITLE, "Wybierz organizacje, aby zobaczyc rozliczenia");
assert.match(BILLING_ORGANIZATION_REQUIRED_DESCRIPTION, /organization_id/);
assert.equal(canUseBillingOrganizationScope(null), false);
assert.equal(canUseBillingOrganizationScope(""), false);
assert.equal(canUseBillingOrganizationScope("   "), false);
assert.equal(canUseBillingOrganizationScope("42"), true);
assert.equal(canUseBillingOrganizationScope(42), true);
assert.deepEqual(withActiveOrganizationQuery("42"), { organization_id: "42" });

assert.throws(() => readBillingBalances({ balances: [] }), ApiContractError);
assert.throws(() => readBillingBalances([{ display_name: "Brak ID" }]), ApiContractError);

assert.equal(getBillingErrorState(new ApiError("Brak sesji", 401, {})).status, "unauthenticated");
assert.equal(getBillingErrorState(new ApiError("Brak uprawnien", 403, {})).status, "forbidden");
assert.equal(getBillingErrorState(new ApiError("Backend padl", 500, {})).status, "server-error");
assert.equal(getBillingErrorState(new ApiContractError(BILLING_BALANCES_ENDPOINT, {})).title, "Niepoprawny format rozliczen");

async function main() {
  await withMockedFetch(
    async (url, options) => {
      assert.equal(url, `/api${BILLING_BALANCES_ENDPOINT}?organization_id=42`);
      assert.equal(options.method, "GET");
      assert.equal(options.body, undefined);
      return jsonResponse(200, [makeBalance()]);
    },
    async () => {
      const payload = await api.ledgerBalances(withActiveOrganizationQuery("42"));
      const nextBalances = readBillingBalances(payload);
      assert.equal(nextBalances.length, 1);
      assert.equal(nextBalances[0].billing_payer_id, 14);
    },
  );

  await withMockedFetch(
    async (url, options) => {
      assert.equal(url, `/api${BILLING_BALANCES_ENDPOINT}?organization_id=42`);
      assert.equal(options.method, "GET");
      return jsonResponse(200, []);
    },
    async () => {
      const payload = await api.ledgerBalances(withActiveOrganizationQuery("42"));
      const emptyBalances = readBillingBalances(payload);
      assert.equal(isBillingEmpty("ready", emptyBalances), true);
      assert.equal(hasBillingData("ready", emptyBalances), false);
    },
  );

  console.log("Billing regression tests passed.");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
