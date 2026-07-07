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
const { findNavigationItem, navigationItems } = require("../src/config/navigation.ts");
const { withActiveOrganizationQuery } = require("../src/context/organizationContextModel.ts");
const {
  BILLING_BALANCES_ENDPOINT,
  BILLING_CANONICAL_ROUTE,
  BILLING_FORBIDDEN_WRITE_ACTIONS,
  BILLING_LEGACY_ROUTE,
  BILLING_ORGANIZATION_REQUIRED_DESCRIPTION,
  BILLING_ORGANIZATION_REQUIRED_TITLE,
  BILLING_PAYER_DETAIL_ORGANIZATION_REQUIRED_DESCRIPTION,
  BILLING_PAYER_DETAIL_ORGANIZATION_REQUIRED_TITLE,
  BILLING_PAYER_DETAIL_ROUTE,
  BILLING_CHARGES_ENDPOINT,
  BILLING_PAYERS_ENDPOINT,
  BILLING_PAYMENT_MATCHES_ENDPOINT,
  BILLING_PAYMENTS_ROUTE,
  BILLING_PERIODS_ROUTE,
  BILLING_READ_ONLY,
  BILLING_STUDENTS_ENDPOINT,
  BILLING_TRANSACTIONS_ENDPOINT,
  billingBalanceTone,
  billingPayerDetailPath,
  billingScreenHasForbiddenTechnicalText,
  buildBillingAttentionItems,
  buildBillingBalanceRows,
  buildBillingBalanceExplanationRows,
  buildBillingCompanyClientRows,
  buildBillingContractorRows,
  buildBillingFamilyFoundationRows,
  buildBillingInvoiceRows,
  buildBillingKpis,
  buildBillingMoneySummary,
  buildBillingPayerDetailView,
  buildBillingPaymentsAllocationView,
  buildBillingPeriodView,
  buildBillingRecentPaymentRows,
  buildBillingRelatedWorkItemRows,
  buildBillingServiceEnrollmentRows,
  canUseBillingOrganizationScope,
  formatMoney,
  getBillingErrorState,
  hasBillingCenterData,
  hasBillingData,
  isBillingCenterEmpty,
  isBillingEmpty,
  readBillingBalances,
  readBillingCharges,
  readBillingInvoices,
  readBillingPaymentMatches,
  readBillingPayers,
  readBillingStudents,
  readBillingTransactions,
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

function makePayer(overrides = {}) {
  return {
    billing_payer_id: 14,
    display_name: "Rodzina Kowalskich",
    contact_phone: "500600700",
    payment_identifier: "500600700",
    email: "rodzina@example.test",
    has_large_family_card: 1,
    notes: "Rodzinne konto rozliczeniowe.",
    is_active: 1,
    billing_total_charges: 520,
    billing_total_matches: 300,
    billing_balance_due: 220,
    billing_last_payment_at: "2099-05-03",
    billing_last_payment_amount: 300,
    billing_last_payment_currency: "PLN",
    billing_last_payment_title: "Czesne maj",
    billing_matched_payment_count: 2,
    ...overrides,
  };
}

function makeStudent(overrides = {}) {
  return {
    billing_student_id: 21,
    organization_id: 42,
    billing_payer_id: 14,
    full_name: "Lena Kowalska",
    lesson_day: "wtorek",
    family_billing_order: 1,
    group_name: "Robotyka 8-10",
    is_active: 1,
    payer_label: "Rodzina Kowalskich",
    payer_display_name: "Rodzina Kowalskich",
    payer_contact_phone: "500600700",
    school_short_name: "SP 1",
    model_name: "Robotyka junior",
    family_balance_due: 220,
    ...overrides,
  };
}

function makeCharge(overrides = {}) {
  return {
    billing_charge_id: 31,
    billing_payer_id: 14,
    billing_student_id: 21,
    period_label: "Marzec 2026",
    due_date: "2026-03-10",
    base_amount: 228,
    intro_free_discount_amount: 0,
    sibling_discount_amount: 0,
    large_family_discount_amount: 0,
    total_amount: 228,
    status: "open",
    model_name: "Robotyka junior",
    student_full_name: "Lena Kowalska",
    payer_display_name: "Rodzina Kowalskich",
    ...overrides,
  };
}

function makePaymentMatch(overrides = {}) {
  return {
    billing_payment_match_id: 51,
    billing_transaction_id: 61,
    billing_payer_id: 14,
    billing_charge_id: 31,
    matched_amount: 228,
    matched_at: "2026-03-08T10:00:00",
    payer_display_name: "Rodzina Kowalskich",
    transaction_booking_date: "2026-03-08",
    transaction_amount: 228,
    transaction_title: "Czesne marzec",
    charge_total_amount: 228,
    ...overrides,
  };
}

function makeTransaction(overrides = {}) {
  return {
    billing_transaction_id: 61,
    organization_id: 1,
    booking_date: "2026-03-08",
    value_date: "2026-03-08",
    amount: 228,
    currency: "PLN",
    direction: "inflow",
    counterparty_name: "Rodzina Kowalskich",
    title: "Czesne marzec",
    reference: "TRX-61",
    matched_status: "matched",
    ...overrides,
  };
}

function makeInvoice(overrides = {}) {
  return {
    invoice_id: 18,
    invoice_number: "FV/CASI/18",
    contractor_id: 14,
    contractor_name: "Rodzina Kowalskich",
    status: "weryfikacja",
    workflow_state: "w_pracy",
    duplicate_type: "podejrzenie",
    gross_amount: 520,
    currency: "PLN",
    incoming_date: "2099-05-04",
    flag_reason: "Brakuje opisu kosztu.",
    ...overrides,
  };
}

function makeContractor(overrides = {}) {
  return {
    contractor_id: 14,
    name: "Rodzina Kowalskich",
    email: "rodzina@example.test",
    phone: "500600700",
    invoice_count: 3,
    is_new: false,
    organization_name: "CASI",
    ...overrides,
  };
}

function makeWorkItem(overrides = {}) {
  return {
    work_item_id: 44,
    title: "Wyjaśnić płatność Rodzina Kowalskich do faktury FV/CASI/18",
    description: "Sprawa może blokować rozliczenie faktury.",
    status: "w_toku",
    priority_level: "wysoki",
    priority_score: 81,
    is_closed: false,
    is_due_overdue: false,
    is_sla_overdue: true,
    metadata: { invoice_id: 18, contractor_id: 14 },
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
const payers = readBillingPayers([makePayer()]);
assert.equal(payers.length, 1);
assert.equal(payers[0].billing_payer_id, 14);
assert.equal(payers[0].is_active, true);
assert.equal(payers[0].billing_balance_due, 220);

const students = readBillingStudents([
  makeStudent({ billing_student_id: 21, full_name: "Lena Kowalska", family_billing_order: 1 }),
  makeStudent({ billing_student_id: 22, full_name: "Maja Kowalska", family_billing_order: 2 }),
]);
assert.equal(students.length, 2);
assert.equal(students[0].billing_payer_id, 14);
assert.equal(students[1].family_billing_order, 2);

const charges = readBillingCharges([
  makeCharge({ billing_charge_id: 31, billing_student_id: 21, total_amount: 228, student_full_name: "Lena Kowalska" }),
  makeCharge({ billing_charge_id: 32, billing_student_id: 22, total_amount: 228, student_full_name: "Maja Kowalska" }),
]);
assert.equal(charges.length, 2);
assert.equal(charges[0].billing_payer_id, 14);
assert.equal(charges[1].total_amount, 228);
const paymentMatches = readBillingPaymentMatches([
  makePaymentMatch({ billing_payment_match_id: 51, billing_charge_id: 31, matched_amount: 228 }),
  makePaymentMatch({ billing_payment_match_id: 52, billing_charge_id: 32, matched_amount: 171 }),
]);
assert.equal(paymentMatches.length, 2);
assert.equal(paymentMatches[0].billing_charge_id, 31);
assert.equal(paymentMatches[1].matched_amount, 171);
const transactions = readBillingTransactions([
  makeTransaction({ billing_transaction_id: 61, amount: 228 }),
  makeTransaction({ billing_transaction_id: 62, amount: 171, title: "Czesne Maja marzec" }),
]);
assert.equal(transactions.length, 2);
assert.equal(transactions[0].billing_transaction_id, 61);
assert.equal(transactions[1].amount, 171);

const rows = buildBillingBalanceRows(balances);
assert.equal(rows[0].payerLabel, "Rodzina Kowalskich");
assert.equal(rows[0].contactLabel, "500600700");
assert.equal(rows[0].statusLabel, "Do zapłaty");
assert.equal(rows[0].statusTone, "warning");
assert.equal(rows[0].totalChargesLabel, "520,00 PLN");
assert.equal(rows[0].totalMatchesLabel, "300,00 PLN");
assert.equal(rows[0].balanceDueLabel, "220,00 PLN");
assert.equal(rows[0].lastPaymentLabel, "2099-05-03 · 300,00 PLN");
assert.equal(rows[0].matchedPaymentCountLabel, "2");
const familyFoundationRows = buildBillingFamilyFoundationRows(payers, students, balances);
assert.equal(familyFoundationRows.length, 1);
assert.equal(familyFoundationRows[0].href, "/rozliczenia/platnicy/14");
assert.equal(familyFoundationRows[0].familyLabel, "Rodzina Kowalskich");
assert.equal(familyFoundationRows[0].payerLabel, "Rodzina Kowalskich");
assert.equal(familyFoundationRows[0].studentSummaryLabel, "2 uczniów");
assert.match(familyFoundationRows[0].studentsLabel, /Lena Kowalska/);
assert.match(familyFoundationRows[0].studentsLabel, /Maja Kowalska/);
assert.equal(familyFoundationRows[0].siblingLabel, "Rodzeństwo: 2 uczniów");
assert.equal(familyFoundationRows[0].balanceLabel, "220,00 PLN");
assert.doesNotMatch(familyFoundationRows[0].contextLabel, /endpoint|payload|debug|demo/i);
assert.deepEqual(buildBillingFamilyFoundationRows([], [], []), []);

const balanceExplanationRows = buildBillingBalanceExplanationRows(balances, payers, students, charges);
assert.equal(balanceExplanationRows.length, 1);
assert.equal(balanceExplanationRows[0].payerLabel, "Rodzina Kowalskich");
assert.equal(balanceExplanationRows[0].familyTypeLabel, "Rodzina z rodzeństwem: 2 uczniów");
assert.equal(balanceExplanationRows[0].chargedLabel, "520,00 PLN");
assert.equal(balanceExplanationRows[0].paidLabel, "300,00 PLN");
assert.equal(balanceExplanationRows[0].balanceMeaningLabel, "Do dopłaty pozostaje 220,00 PLN");
assert.match(balanceExplanationRows[0].topItemsLabel, /Lena Kowalska/);
assert.match(balanceExplanationRows[0].topItemsLabel, /Marzec 2026/);
assert.doesNotMatch(balanceExplanationRows[0].explanationLabel, /endpoint|payload|debug|demo/i);

const overpaymentExplanationRows = buildBillingBalanceExplanationRows(
  readBillingBalances([makeBalance({ billing_payer_id: 15, display_name: "Rodzina Nadpłata", total_charges: 100, total_matches: 157, balance_due: -57 })]),
  readBillingPayers([makePayer({ billing_payer_id: 15, display_name: "Rodzina Nadpłata" })]),
  readBillingStudents([makeStudent({ billing_student_id: 23, billing_payer_id: 15, full_name: "Tomek Nadpłata" })]),
  [],
);
assert.equal(overpaymentExplanationRows[0].balanceMeaningLabel, "Nadpłata wynosi 57,00 PLN");
assert.match(overpaymentExplanationRows[0].topItemsLabel, /Brakuje szczegółowych naliczeń/);
assert.deepEqual(buildBillingBalanceExplanationRows([], [], [], []), []);

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

const snapshot = {
  balances: readBillingBalances([
    makeBalance({ billing_payer_id: 1, display_name: "Rodzina Kowalskich", balance_due: 220 }),
    makeBalance({ billing_payer_id: 2, display_name: "Misja Robotyka", balance_due: -40, total_charges: 100, total_matches: 140 }),
  ]),
  payers: readBillingPayers([
    makePayer({ billing_payer_id: 1, display_name: "Rodzina Kowalskich", billing_balance_due: 220 }),
  ]),
  students: readBillingStudents([
    makeStudent({ billing_student_id: 21, billing_payer_id: 1, full_name: "Lena Kowalska", family_billing_order: 1 }),
    makeStudent({ billing_student_id: 22, billing_payer_id: 1, full_name: "Maja Kowalska", family_billing_order: 2 }),
  ]),
  charges: readBillingCharges([
    makeCharge({ billing_charge_id: 31, billing_payer_id: 1, billing_student_id: 21, student_full_name: "Lena Kowalska", period_label: "Marzec 2026", total_amount: 228 }),
    makeCharge({ billing_charge_id: 32, billing_payer_id: 1, billing_student_id: 22, student_full_name: "Maja Kowalska", period_label: "Marzec 2026", total_amount: 228 }),
    makeCharge({ billing_charge_id: 33, billing_payer_id: 1, billing_student_id: 21, student_full_name: "Lena Kowalska", period_label: "Kwiecień 2026", total_amount: 228 }),
    makeCharge({ billing_charge_id: 34, billing_payer_id: 2, billing_student_id: null, student_full_name: null, payer_display_name: "Misja Robotyka", model_name: "Abonament CASI", period_label: "Marzec 2026", total_amount: 100 }),
  ]),
  paymentMatches: readBillingPaymentMatches([
    makePaymentMatch({ billing_payment_match_id: 51, billing_transaction_id: 61, billing_payer_id: 1, billing_charge_id: 31, matched_amount: 228 }),
    makePaymentMatch({ billing_payment_match_id: 52, billing_transaction_id: 62, billing_payer_id: 1, billing_charge_id: 32, matched_amount: 171 }),
    makePaymentMatch({ billing_payment_match_id: 53, billing_transaction_id: 63, billing_payer_id: 2, billing_charge_id: 34, matched_amount: 140 }),
    makePaymentMatch({ billing_payment_match_id: 54, billing_transaction_id: 64, billing_payer_id: 1, billing_charge_id: null, matched_amount: 999 }),
  ]),
  transactions: readBillingTransactions([
    makeTransaction({ billing_transaction_id: 61, amount: 228, title: "Czesne Lena marzec" }),
    makeTransaction({ billing_transaction_id: 62, amount: 171, title: "Czesne Maja marzec" }),
    makeTransaction({ billing_transaction_id: 63, amount: 140, counterparty_name: "Misja Robotyka", title: "Abonament CASI marzec" }),
    makeTransaction({ billing_transaction_id: 64, amount: 999, title: "Wpłata ogólna Rodzina Kowalskich", matched_status: "payer_only" }),
    makeTransaction({ billing_transaction_id: 65, amount: 77, title: "Przelew bez identyfikatora", matched_status: "unmatched" }),
  ]),
  invoices: readBillingInvoices([
    makeInvoice({ invoice_id: 18, contractor_id: 14, invoice_number: "FV/CASI/18", duplicate_type: "podejrzenie" }),
    makeInvoice({ invoice_id: 19, contractor_id: 8, invoice_number: "FV/MR/19", status: "zaakceptowana", duplicate_type: "brak", flag_reason: null }),
  ]),
  contractors: [
    makeContractor({ contractor_id: 14, name: "Rodzina Kowalskich", invoice_count: 3 }),
    makeContractor({ contractor_id: 8, name: "Misja Robotyka", email: null, phone: null, invoice_count: 2 }),
  ],
  workItems: [makeWorkItem(), makeWorkItem({ work_item_id: 45, title: "Sprawdzić umowę serwisową", priority_score: 10, metadata: {} })],
};

const attentionItems = buildBillingAttentionItems(snapshot);
assert.ok(attentionItems.length <= 6);
assert.ok(attentionItems.some((item) => item.category === "Rozliczenia" && item.href === "/rozliczenia/platnicy/1"));
assert.ok(attentionItems.some((item) => item.category === "Faktury" && item.href === "/faktury/18"));
assert.ok(attentionItems.some((item) => item.category === "Sprawy" && item.href === "/work-items/44"));

const moneySummary = buildBillingMoneySummary(snapshot.balances, attentionItems.length);
assert.equal(moneySummary.receivables, 220);
assert.equal(moneySummary.overpayments, 40);
assert.equal(moneySummary.netBalance, 180);
assert.equal(moneySummary.headline, "Są należności do kontroli");
assert.equal(moneySummary.activePayerCount, 2);

const invoiceRows = buildBillingInvoiceRows(snapshot.invoices);
assert.equal(invoiceRows[0].href, "/faktury/18");
assert.equal(invoiceRows[0].contractorLabel, "Rodzina Kowalskich");
assert.equal(invoiceRows[0].amountLabel, "520,00 PLN");
assert.equal(invoiceRows[0].reasonLabel, "Brakuje opisu kosztu.");

const contractorRows = buildBillingContractorRows(snapshot.contractors, snapshot.balances);
assert.equal(contractorRows[0].href, "/crm/14");
assert.equal(contractorRows[0].balanceLabel, "220,00 PLN");
assert.equal(contractorRows[1].contactLabel, "Brak kontaktu");

const companyClientRows = buildBillingCompanyClientRows(snapshot.contractors, snapshot.balances, snapshot.payers);
assert.equal(companyClientRows.length, 1);
assert.equal(companyClientRows[0].href, "/crm/8");
assert.equal(companyClientRows[0].companyLabel, "Misja Robotyka");
assert.match(companyClientRows[0].contextLabel, /Klient firmowy/);

const serviceEnrollmentRows = buildBillingServiceEnrollmentRows(snapshot);
assert.equal(serviceEnrollmentRows.some((row) => row.payerLabel === "Rodzina Kowalskich"), true);
const familyServiceRow = serviceEnrollmentRows.find((row) => row.payerLabel === "Rodzina Kowalskich");
assert.ok(familyServiceRow);
assert.equal(familyServiceRow.serviceLabel, "Robotyka junior");
assert.equal(familyServiceRow.serviceTypeLabel, "zajęcia cykliczne");
assert.match(familyServiceRow.personLabel, /Lena Kowalska/);
assert.match(familyServiceRow.personLabel, /Maja Kowalska/);
assert.equal(familyServiceRow.statusLabel, "Aktywny zapis");
assert.equal(familyServiceRow.chargeCountLabel, "3 naliczeń");
assert.match(familyServiceRow.sourceLabel, /Wywnioskowane z naliczeń/);
assert.doesNotMatch(familyServiceRow.contextLabel, /pełny model zapisów|endpoint|payload|debug|demo/i);
const companyServiceRow = serviceEnrollmentRows.find((row) => row.payerLabel === "Misja Robotyka" && /faktur/.test(row.sourceLabel));
assert.ok(companyServiceRow);
assert.equal(companyServiceRow.serviceTypeLabel, "usługa firmowa");
assert.equal(companyServiceRow.personLabel, "Klient firmowy bez uczniów");
assert.match(companyServiceRow.sourceLabel, /Wywnioskowane z faktur/);

const periodView = buildBillingPeriodView(snapshot, null);
assert.ok(periodView);
assert.equal(periodView.selectedPeriodLabel, "Marzec 2026");
assert.match(periodView.selectedPeriodHint, /wywnioskowany/i);
assert.match(periodView.selectedPeriodHint, /bezpiecznie powiązać z naliczeniami/i);
assert.equal(periodView.summary.chargedLabel, "556,00 PLN");
assert.equal(periodView.summary.paidLabel, "539,00 PLN");
assert.equal(periodView.summary.balanceLabel, "17,00 PLN");
assert.equal(periodView.summary.payerCountLabel, "2");
assert.equal(periodView.summary.personCountLabel, "2");
assert.equal(periodView.summary.serviceCountLabel, "2");
assert.equal(periodView.summary.dueCountLabel, "1");
assert.equal(periodView.summary.overpaidCountLabel, "1");
assert.equal(periodView.options.some((row) => row.label === "Kwiecień 2026"), true);
const periodFamilyRow = periodView.payerRows.find((row) => row.payerLabel === "Rodzina Kowalskich");
assert.ok(periodFamilyRow);
assert.equal(periodFamilyRow.href, "/rozliczenia/platnicy/1");
assert.match(periodFamilyRow.peopleLabel, /Lena Kowalska/);
assert.match(periodFamilyRow.peopleLabel, /Maja Kowalska/);
assert.equal(periodFamilyRow.statusLabel, "Do dopłaty");
assert.equal(periodFamilyRow.paidLabel, "399,00 PLN");
assert.equal(periodFamilyRow.balanceLabel, "57,00 PLN");
const periodCompanyRow = periodView.payerRows.find((row) => row.payerLabel === "Misja Robotyka");
assert.ok(periodCompanyRow);
assert.equal(periodCompanyRow.peopleLabel, "Klient firmowy bez uczniów");
assert.equal(periodCompanyRow.statusLabel, "Nadpłata");
assert.equal(periodCompanyRow.balanceLabel, "-40,00 PLN");
assert.equal(periodView.serviceRows.some((row) => row.serviceLabel === "Robotyka junior" && row.sourceLabel.includes("Wywnioskowane")), true);
assert.ok(periodView.attentionRows.some((row) => row.href === "/rozliczenia/platnicy/1" && /Do dopłaty/.test(row.reasonLabel)));
const periodContextText = periodView.contextItems.map((item) => item.value).join(" ");
assert.match(periodContextText, /Część wpłat może być widoczna przy płatniku/i);
assert.match(periodContextText, /pełne przypisywanie wpłat do okresów będzie osobnym etapem/i);
assert.doesNotMatch(periodContextText, /endpoint|payload|debug|demo/i);

const paymentsAllocationView = buildBillingPaymentsAllocationView(snapshot);
assert.equal(paymentsAllocationView.summary.totalVisibleAmountLabel, "1615,00 PLN");
assert.equal(paymentsAllocationView.summary.paymentCountLabel, "5");
assert.equal(paymentsAllocationView.summary.chargeAssignedCountLabel, "3");
assert.equal(paymentsAllocationView.summary.payerOnlyCountLabel, "1");
assert.equal(paymentsAllocationView.summary.unexplainedCountLabel, "1");
assert.equal(paymentsAllocationView.summary.chargeAssignedAmountLabel, "539,00 PLN");
assert.equal(paymentsAllocationView.summary.needsExplanationAmountLabel, "1076,00 PLN");
const paymentChargeRow = paymentsAllocationView.chargeAssignedRows.find((row) => row.payerLabel === "Rodzina Kowalskich");
assert.ok(paymentChargeRow);
assert.equal(paymentChargeRow.payerHref, "/rozliczenia/platnicy/1");
assert.equal(paymentChargeRow.periodHref, "/rozliczenia/okresy");
assert.match(paymentChargeRow.assignmentLabel, /Robotyka junior/);
assert.match(paymentChargeRow.contextLabel, /bezpiecznie pokazać w okresie/);
const payerOnlyPaymentRow = paymentsAllocationView.payerOnlyRows[0];
assert.ok(payerOnlyPaymentRow);
assert.equal(payerOnlyPaymentRow.periodLabel, "Nie przypisano do okresu");
assert.match(payerOnlyPaymentRow.contextLabel, /nie jest jeszcze przypisana do konkretnego naliczenia/i);
const unexplainedPaymentRow = paymentsAllocationView.unexplainedRows[0];
assert.ok(unexplainedPaymentRow);
assert.equal(unexplainedPaymentRow.payerLabel, "Nieustalony płatnik");
assert.equal(unexplainedPaymentRow.statusLabel, "Do wyjaśnienia");
const paymentsContextText = paymentsAllocationView.contextItems.map((item) => item.value).join(" ");
assert.match(paymentsContextText, /nie dodaje wpłat/i);
assert.match(paymentsContextText, /Wpłata trafia do okresu tylko wtedy/i);
assert.doesNotMatch(paymentsContextText, /endpoint|payload|debug|demo/i);

const relatedWorkItems = buildBillingRelatedWorkItemRows(snapshot.workItems, snapshot.invoices, snapshot.contractors);
assert.equal(relatedWorkItems[0].href, "/work-items/44");
assert.match(relatedWorkItems[0].reasonLabel, /rozliczenie faktury/);

const recentPayments = buildBillingRecentPaymentRows(snapshot.balances);
assert.equal(recentPayments[0].amountLabel, "300,00 PLN");
assert.equal(recentPayments[0].titleLabel, "Czesne maj");

const payerDetail = buildBillingPayerDetailView(snapshot, 1);
assert.ok(payerDetail);
assert.equal(payerDetail.title, "Rodzina Kowalskich");
assert.equal(payerDetail.payerTypeLabel, "Płatnik rodzinny · rodzeństwo (2 uczniów)");
assert.equal(payerDetail.balanceMeaningLabel, "Do dopłaty pozostaje 220,00 PLN");
assert.equal(payerDetail.peopleRows.length, 2);
assert.equal(payerDetail.peopleRows[0].personLabel, "Lena Kowalska");
assert.equal(payerDetail.serviceRows.length, 1);
assert.equal(payerDetail.serviceRows[0].serviceTypeLabel, "zajęcia cykliczne");
assert.match(payerDetail.serviceRows[0].peopleLabel, /Lena Kowalska/);
assert.match(payerDetail.serviceRows[0].peopleLabel, /Maja Kowalska/);
assert.equal(payerDetail.serviceRows[0].statusLabel, "Aktywny zapis");
assert.equal(payerDetail.serviceRows[0].chargeCountLabel, "3 naliczeń");
assert.match(payerDetail.serviceRows[0].sourceLabel, /Wywnioskowane z naliczeń/);
assert.equal(payerDetail.chargeRows.length, 3);
assert.equal(payerDetail.paymentRows[0].amountLabel, "300,00 PLN");
assert.equal(payerDetail.invoiceRows[0].href, "/faktury/18");
assert.equal(payerDetail.workItemRows[0].href, "/work-items/44");
assert.equal(buildBillingPayerDetailView(snapshot, 999), null);
assert.equal(billingPayerDetailPath(14), "/rozliczenia/platnicy/14");

assert.equal(formatMoney(1234.5).endsWith("PLN"), true);
assert.equal(hasBillingData("ready", balances), true);
assert.equal(isBillingEmpty("ready", []), true);
assert.equal(hasBillingCenterData("ready", snapshot), true);
assert.equal(isBillingCenterEmpty("ready", { balances: [], payers: [], students: [], charges: [], invoices: [], contractors: [], workItems: [] }), true);
assert.equal(hasBillingData("loading", balances), false);

assert.equal(BILLING_BALANCES_ENDPOINT, "/billing/ledger/balances");
assert.equal(BILLING_PAYMENT_MATCHES_ENDPOINT, "/billing/ledger/matches");
assert.equal(BILLING_PAYERS_ENDPOINT, "/billing/payers");
assert.equal(BILLING_STUDENTS_ENDPOINT, "/billing/students");
assert.equal(BILLING_CHARGES_ENDPOINT, "/billing/charges");
assert.equal(BILLING_TRANSACTIONS_ENDPOINT, "/billing/transactions");
assert.equal(BILLING_CANONICAL_ROUTE, "/rozliczenia");
assert.equal(BILLING_LEGACY_ROUTE, "/kasa");
assert.equal(BILLING_PAYER_DETAIL_ROUTE, "/rozliczenia/platnicy");
assert.equal(BILLING_PERIODS_ROUTE, "/rozliczenia/okresy");
assert.equal(BILLING_PAYMENTS_ROUTE, "/rozliczenia/wplaty");
assert.equal(BILLING_READ_ONLY, true);
assert.deepEqual(BILLING_FORBIDDEN_WRITE_ACTIONS, [
  "Dodaj płatność",
  "Edytuj płatność",
  "Usuń płatność",
  "Dodaj usługę",
  "Dodaj zapis",
  "Edytuj usługę",
  "Edytuj zapis",
  "Dodaj wpłatę",
  "Dopasuj wpłatę",
  "Zmień przypisanie",
  "Importuj wyciąg",
  "Wygeneruj naliczenia",
  "Zaksięguj",
  "Eksportuj",
]);
assert.equal(BILLING_ORGANIZATION_REQUIRED_TITLE, "Wybierz organizację, aby zobaczyć rozliczenia");
assert.doesNotMatch(BILLING_ORGANIZATION_REQUIRED_DESCRIPTION, /organization_id|endpoint|payload|debug/i);
assert.equal(BILLING_PAYER_DETAIL_ORGANIZATION_REQUIRED_TITLE, "Wybierz organizację, aby zobaczyć płatnika");
assert.doesNotMatch(BILLING_PAYER_DETAIL_ORGANIZATION_REQUIRED_DESCRIPTION, /organization_id|endpoint|payload|debug/i);
assert.equal(navigationItems.some((item) => item.path === "/kasa" || item.label === "Kasa"), false);
const billingNavigationItem = findNavigationItem("/rozliczenia");
assert.equal(billingNavigationItem.id, "billing");
assert.equal(billingNavigationItem.readinessLabel, "Produkt v1");
assert.equal(billingNavigationItem.actionLabel, "Tylko odczyt");
assert.doesNotMatch(billingNavigationItem.description, /endpoint|payload|debug|demo/i);
assert.equal(findNavigationItem("/kasa").id, "dashboard");
assert.match(fs.readFileSync(path.join(srcRoot, "app", "kasa", "page.tsx"), "utf8"), /redirect\("\/rozliczenia"\)/);
assert.match(fs.readFileSync(path.join(srcRoot, "..", "next.config.js"), "utf8"), /source: "\/kasa"[\s\S]*destination: "\/rozliczenia"/);
assert.equal(canUseBillingOrganizationScope(null), false);
assert.equal(canUseBillingOrganizationScope(""), false);
assert.equal(canUseBillingOrganizationScope("   "), false);
assert.equal(canUseBillingOrganizationScope("42"), true);
assert.equal(canUseBillingOrganizationScope(42), true);
assert.deepEqual(withActiveOrganizationQuery("42"), { organization_id: "42" });

const billingProductNote = fs.readFileSync(path.join(srcRoot, "..", "docs", "BILLING_CENTER_PRODUCT_NOTE.md"), "utf8");
assert.match(billingProductNote, /Docelowy zakres pełnego modułu rozliczeń/);
assert.match(billingProductNote, /uczniów/);
assert.match(billingProductNote, /rodzin/);
assert.match(billingProductNote, /płatników/);
assert.match(billingProductNote, /usługi i zapisy/);
assert.match(billingProductNote, /cenniki/);
assert.match(billingProductNote, /zniżki/);
assert.match(billingProductNote, /naliczenia/);
assert.match(billingProductNote, /import przelewów/);
assert.match(billingProductNote, /dopasowanie płatności/);
assert.match(billingProductNote, /przypomnienia/);
assert.match(billingProductNote, /raporty właściciela/);
assert.match(billingProductNote, /eksport księgowy/);
assert.match(billingProductNote, /Czego v1 jeszcze nie robi/);
assert.match(billingProductNote, /nie nalicza opłat uczniom/);
assert.match(billingProductNote, /pokazuje rodziny/);
assert.match(billingProductNote, /Usługi są widoczne przez naliczenia/);
assert.match(billingProductNote, /trybie read-only/);
assert.match(billingProductNote, /nie dopasowuje przelewów/);
assert.match(billingProductNote, /nie zastępuje księgowości/);
assert.match(billingProductNote, /nie wykonuje operacji finansowych/);

const screenStrings = [
  ...attentionItems.flatMap((item) => [item.title, item.reason, item.href]),
  ...familyFoundationRows.flatMap((row) => [row.familyLabel, row.payerLabel, row.studentsLabel, row.siblingLabel, row.contextLabel]),
  ...balanceExplanationRows.flatMap((row) => [row.payerLabel, row.familyTypeLabel, row.balanceMeaningLabel, row.topItemsLabel, row.explanationLabel]),
  ...companyClientRows.flatMap((row) => [row.companyLabel, row.contactLabel, row.contextLabel, row.href]),
  ...serviceEnrollmentRows.flatMap((row) => [
    row.serviceLabel,
    row.serviceTypeLabel,
    row.payerLabel,
    row.personLabel,
    row.periodLabel,
    row.statusLabel,
    row.sourceLabel,
    row.contextLabel,
  ]),
  ...invoiceRows.flatMap((row) => [row.invoiceLabel, row.contractorLabel, row.reasonLabel, row.href]),
  ...contractorRows.flatMap((row) => [row.contractorLabel, row.contactLabel, row.balanceLabel, row.href]),
  ...relatedWorkItems.flatMap((row) => [row.titleLabel, row.reasonLabel, row.href]),
  ...(periodView
    ? [
        periodView.selectedPeriodLabel,
        periodView.selectedPeriodHint,
        periodView.summary.sourceLabel,
        ...periodView.options.flatMap((row) => [row.label, row.hintLabel, row.statusLabel]),
        ...periodView.payerRows.flatMap((row) => [row.payerLabel, row.peopleLabel, row.servicesLabel, row.statusLabel, row.href]),
        ...periodView.serviceRows.flatMap((row) => [row.serviceLabel, row.serviceTypeLabel, row.sourceLabel]),
        ...periodView.attentionRows.flatMap((row) => [row.titleLabel, row.reasonLabel, row.href]),
        ...periodView.contextItems.flatMap((item) => [item.label, item.value]),
      ]
    : []),
  ...paymentsAllocationView.chargeAssignedRows.flatMap((row) => [
    row.dateLabel,
    row.amountLabel,
    row.payerLabel,
    row.descriptionLabel,
    row.assignmentLabel,
    row.periodLabel,
    row.statusLabel,
    row.contextLabel,
    row.payerHref,
    row.periodHref,
  ]),
  ...paymentsAllocationView.payerOnlyRows.flatMap((row) => [
    row.dateLabel,
    row.amountLabel,
    row.payerLabel,
    row.descriptionLabel,
    row.assignmentLabel,
    row.periodLabel,
    row.statusLabel,
    row.contextLabel,
    row.payerHref,
  ]),
  ...paymentsAllocationView.unexplainedRows.flatMap((row) => [
    row.dateLabel,
    row.amountLabel,
    row.payerLabel,
    row.descriptionLabel,
    row.assignmentLabel,
    row.periodLabel,
    row.statusLabel,
    row.contextLabel,
  ]),
  ...paymentsAllocationView.contextItems.flatMap((item) => [item.label, item.value]),
  ...(payerDetail
    ? [
        payerDetail.title,
        payerDetail.payerTypeLabel,
        payerDetail.balanceMeaningLabel,
        payerDetail.lastPaymentLabel,
        ...payerDetail.peopleRows.flatMap((row) => [row.personLabel, row.serviceLabel, row.contextLabel]),
        ...payerDetail.serviceRows.flatMap((row) => [row.serviceLabel, row.serviceTypeLabel, row.peopleLabel, row.statusLabel, row.sourceLabel, row.contextLabel]),
        ...payerDetail.chargeRows.flatMap((row) => [row.periodLabel, row.personLabel, row.serviceLabel]),
        ...payerDetail.paymentRows.flatMap((row) => [row.dateLabel, row.amountLabel, row.titleLabel, row.contextLabel]),
        ...payerDetail.invoiceRows.flatMap((row) => [row.invoiceLabel, row.contractorLabel, row.href]),
        ...payerDetail.workItemRows.flatMap((row) => [row.titleLabel, row.reasonLabel, row.href]),
        ...payerDetail.contextItems.flatMap((item) => [item.label, item.value]),
      ]
    : []),
];
assert.equal(billingScreenHasForbiddenTechnicalText(screenStrings), false);
assert.equal(billingScreenHasForbiddenTechnicalText(["storage_key", "data/magazyn", "C:\\Users\\x", "payload"]), true);

assert.throws(() => readBillingBalances({ balances: [] }), ApiContractError);
assert.throws(() => readBillingBalances([{ display_name: "Brak ID" }]), ApiContractError);
assert.throws(() => readBillingPayers({ payers: [] }), ApiContractError);
assert.throws(() => readBillingPayers([{ display_name: "Brak ID" }]), ApiContractError);
assert.throws(() => readBillingStudents({ students: [] }), ApiContractError);
assert.throws(() => readBillingStudents([{ full_name: "Brak płatnika" }]), ApiContractError);
assert.throws(() => readBillingCharges({ charges: [] }), ApiContractError);
assert.throws(() => readBillingCharges([{ period_label: "Brak płatnika" }]), ApiContractError);
assert.throws(() => readBillingTransactions({ transactions: [] }), ApiContractError);
assert.throws(() => readBillingTransactions([{ title: "Brak ID" }]), ApiContractError);
assert.throws(() => readBillingInvoices({ invoices: [] }), ApiContractError);

assert.equal(getBillingErrorState(new ApiError("Brak sesji", 401, {})).status, "unauthenticated");
assert.equal(getBillingErrorState(new ApiError("Brak uprawnien", 403, {})).status, "forbidden");
assert.equal(getBillingErrorState(new ApiError("Backend padl", 500, {})).status, "server-error");
assert.equal(getBillingErrorState(new ApiContractError(BILLING_BALANCES_ENDPOINT, {})).title, "Niepoprawny format rozliczeń");

async function main() {
  await withMockedFetch(
    async (url, options) => {
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

  const requestedUrls = [];
  await withMockedFetch(
    async (url, options) => {
      requestedUrls.push(url);
      assert.equal(options.method, "GET");
      if (url.startsWith(`/api${BILLING_BALANCES_ENDPOINT}`)) {
        return jsonResponse(200, [makeBalance()]);
      }
      if (url.startsWith(`/api${BILLING_PAYERS_ENDPOINT}`)) {
        return jsonResponse(200, [makePayer()]);
      }
      if (url.startsWith(`/api${BILLING_STUDENTS_ENDPOINT}`)) {
        return jsonResponse(200, [makeStudent()]);
      }
      if (url.startsWith(`/api${BILLING_CHARGES_ENDPOINT}`)) {
        return jsonResponse(200, [makeCharge()]);
      }
      if (url.startsWith(`/api${BILLING_PAYMENT_MATCHES_ENDPOINT}`)) {
        return jsonResponse(200, [makePaymentMatch()]);
      }
      if (url.startsWith(`/api${BILLING_TRANSACTIONS_ENDPOINT}`)) {
        return jsonResponse(200, [makeTransaction()]);
      }
      if (url.startsWith("/api/invoices")) {
        return jsonResponse(200, [makeInvoice()]);
      }
      if (url.startsWith("/api/contractors")) {
        return jsonResponse(200, [makeContractor()]);
      }
      if (url.startsWith("/api/work-items")) {
        return jsonResponse(200, [makeWorkItem()]);
      }
      throw new Error(`Unexpected URL: ${url}`);
    },
    async () => {
      const query = withActiveOrganizationQuery("42");
      const workItemsQuery = withActiveOrganizationQuery("42", { limit: 100, only_open: 1 });
      const [balancesPayload, payersPayload, studentsPayload, chargesPayload, matchesPayload, transactionsPayload, invoicesPayload, contractorsPayload, workItemsPayload] = await Promise.all([
        api.ledgerBalances(query),
        api.billingPayers(query),
        api.billingStudents(query),
        api.billingCharges(withActiveOrganizationQuery("42", { limit: 100 })),
        api.billingLedgerMatches(withActiveOrganizationQuery("42", { limit: 1000 })),
        api.billingTransactions(withActiveOrganizationQuery("42", { limit: 1000 })),
        api.invoices(query),
        api.contractors(query),
        api.workItems(workItemsQuery),
      ]);
      assert.equal(readBillingBalances(balancesPayload).length, 1);
      assert.equal(readBillingPayers(payersPayload).length, 1);
      assert.equal(readBillingStudents(studentsPayload).length, 1);
      assert.equal(readBillingCharges(chargesPayload).length, 1);
      assert.equal(readBillingPaymentMatches(matchesPayload).length, 1);
      assert.equal(readBillingTransactions(transactionsPayload).length, 1);
      assert.equal(readBillingInvoices(invoicesPayload).length, 1);
      assert.equal(Array.isArray(contractorsPayload), true);
      assert.equal(Array.isArray(workItemsPayload), true);
    },
  );

  assert.ok(requestedUrls.every((url) => url.includes("organization_id=42")));
  assert.ok(requestedUrls.some((url) => url.includes("/api/billing/charges") && url.includes("limit=100")));
  assert.ok(requestedUrls.some((url) => url.includes("/api/billing/ledger/matches") && url.includes("limit=1000")));
  assert.ok(requestedUrls.some((url) => url.includes("/api/billing/transactions") && url.includes("limit=1000")));
  assert.ok(requestedUrls.some((url) => url.includes("/api/work-items") && url.includes("only_open=1") && url.includes("limit=100")));

  console.log("Billing regression tests passed.");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
