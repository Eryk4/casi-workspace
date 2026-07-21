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
  BILLING_CONTACT_ACTION_OPTIONS,
  BILLING_CONTACT_CHANNEL_OPTIONS,
  BILLING_CONTACT_DRAFT_TEMPLATES,
  BILLING_CONTACT_EVENT_HELP_TEXT,
  BILLING_CONTACT_EVENTS_ENDPOINT,
  BILLING_CONTACT_CENTER_ROUTE,
  BILLING_CONTACT_MESSAGE_MAX_LENGTH,
  BILLING_CONTACT_NO_SEND_HELP_TEXT,
  BILLING_CONTACT_NOTE_MAX_LENGTH,
  BILLING_NEXT_STEP_EVENTS_ENDPOINT,
  BILLING_NEXT_STEP_HELP_TEXT,
  BILLING_NEXT_STEP_NOTE_MAX_LENGTH,
  BILLING_NEXT_STEP_TITLE_MAX_LENGTH,
  BILLING_NEXT_STEP_TYPE_OPTIONS,
  BILLING_DEBTS_ROUTE,
  BILLING_FORBIDDEN_WRITE_ACTIONS,
  BILLING_LEGACY_ROUTE,
  BILLING_OPERATIONAL_REPORT_ROUTE,
  BILLING_ORGANIZATION_REQUIRED_DESCRIPTION,
  BILLING_ORGANIZATION_REQUIRED_TITLE,
  BILLING_PAYER_NOTE_CREATE_ENABLED,
  BILLING_PAYER_NOTE_ENDPOINT_SUFFIX,
  BILLING_PAYER_NOTE_HELP_TEXT,
  BILLING_PAYER_NOTE_MAX_LENGTH,
  BILLING_PAYER_DETAIL_ORGANIZATION_REQUIRED_DESCRIPTION,
  BILLING_PAYER_DETAIL_ORGANIZATION_REQUIRED_TITLE,
  BILLING_PAYER_DETAIL_ROUTE,
  BILLING_PAYMENT_DETAIL_ORGANIZATION_REQUIRED_DESCRIPTION,
  BILLING_PAYMENT_DETAIL_ORGANIZATION_REQUIRED_TITLE,
  BILLING_PAYMENT_REVIEW_STATUS_ENDPOINT_SUFFIX,
  BILLING_PAYMENT_REVIEW_STATUSES_ENDPOINT,
  BILLING_PAYMENT_REVIEW_STATUS_HELP_TEXT,
  BILLING_PAYMENT_REVIEW_STATUS_MAX_NOTE_LENGTH,
  BILLING_PAYMENT_REVIEW_STATUS_OPTIONS,
  BILLING_WORK_QUEUE_DECISION_HELP_TEXT,
  BILLING_WORK_QUEUE_DECISION_MAX_NOTE_LENGTH,
  BILLING_WORK_QUEUE_EVENTS_ENDPOINT,
  billingPaymentReviewStatusEndpoint,
  buildBillingContactEventRequest,
  buildBillingContactCenterView,
  buildBillingNextStepRequest,
  buildBillingNextStepRows,
  buildBillingPaymentReviewStatusRequest,
  buildBillingWorkQueueDecisionRequest,
  createBillingContactEventSubmitter,
  createBillingNextStepSubmitter,
  createBillingPaymentReviewStatusSubmitter,
  getBillingContactEventErrorState,
  getBillingPaymentReviewStatusErrorState,
  readBillingContactEvents,
  readBillingNextStepEvents,
  readBillingPaymentReviewStatus,
  BILLING_CHARGES_ENDPOINT,
  BILLING_PAYERS_ENDPOINT,
  BILLING_PAYMENT_MATCHES_ENDPOINT,
  BILLING_PAYMENTS_ROUTE,
  BILLING_PERIODS_ROUTE,
  BILLING_READ_ONLY,
  BILLING_STUDENTS_ENDPOINT,
  BILLING_TRANSACTIONS_ENDPOINT,
  BILLING_WORK_QUEUE_ROUTE,
  billingBalanceTone,
  billingPaymentDetailPath,
  billingPayerDetailPath,
  billingPayerNoteEndpoint,
  billingScreenHasForbiddenTechnicalText,
  buildBillingAttentionItems,
  buildBillingBalanceRows,
  buildBillingBalanceExplanationRows,
  buildBillingCompanyClientRows,
  buildBillingContractorRows,
  buildBillingDebtsOverpaymentsView,
  buildBillingFamilyFoundationRows,
  buildBillingInvoiceRows,
  buildBillingKpis,
  buildBillingMoneySummary,
  buildBillingPayerDetailView,
  buildBillingPayerNoteRequest,
  buildBillingPaymentDetailView,
  buildBillingPaymentsAllocationView,
  buildBillingOperationalReport,
  buildBillingPeriodView,
  buildBillingWorkQueueView,
  buildBillingRecentPaymentRows,
  buildBillingRelatedWorkItemRows,
  buildBillingServiceEnrollmentRows,
  canUseBillingOrganizationScope,
  createBillingPayerNoteSubmitter,
  formatMoney,
  getBillingErrorState,
  getBillingPayerNoteErrorState,
  hasBillingCenterData,
  hasBillingData,
  isBillingCenterEmpty,
  isBillingEmpty,
  readBillingBalances,
  readBillingCharges,
  readBillingInvoices,
  readBillingPayerNotes,
  readBillingPaymentMatches,
  readBillingPaymentReviewStatuses,
  readBillingWorkQueueEvents,
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
const payerNotes = readBillingPayerNotes([
  {
    billing_note_id: 701,
    organization_id: 1,
    billing_payer_id: 14,
    author_user_id: 2,
    author_user_name: "Operator",
    note_type: "operator_note",
    note_text: "Rodzic potwierdził wyjaśnienie salda.",
    created_at: "2099-05-08T10:00:00",
  },
  {
    billing_note_id: 702,
    organization_id: 1,
    billing_payer_id: 14,
    author_user_id: 2,
    author_user_name: "Operator",
    note_type: "operator_note",
    note_text: "C:\\Users\\secret\\ledger.txt",
    created_at: "2099-05-09T10:00:00",
  },
]);
assert.equal(payerNotes.length, 2);
assert.equal(payerNotes[0].note_text, "Rodzic potwierdził wyjaśnienie salda.");
assert.equal(payerNotes[1].note_text, "Ukryto techniczną lub wrażliwą treść notatki.");
const contactEventsPayload = {
  organization_id: 42,
  events: [
    {
      billing_contact_event_id: 901,
      organization_id: 42,
      billing_payer_id: 14,
      payer_display_name: "Rodzina Kowalskich",
      related_payment_id: 61,
      related_issue_key: "payment:61:payer-only",
      channel: "sms",
      contact_action: "draft_prepared",
      message_text: "Dzień dobry, prosimy o sprawdzenie rozliczenia.",
      note_text: "Treść przygotowana do samodzielnego wysłania.",
      created_by_user_id: 2,
      created_by_user_name: "Operator",
      created_at: "2099-05-10T10:00:00",
    },
    {
      billing_contact_event_id: 902,
      organization_id: 42,
      billing_payer_id: 14,
      payer_display_name: "Rodzina Kowalskich",
      channel: "phone",
      contact_action: "contact_logged",
      message_text: "C:\\Users\\secret\\message.txt",
      note_text: "Rozmowa telefoniczna bez zmiany salda.",
      created_by_user_id: 2,
      created_by_user_name: "Operator",
      created_at: "2099-05-11T10:00:00",
    },
    {
      billing_contact_event_id: 903,
      organization_id: 42,
      billing_payer_id: 14,
      payer_display_name: "Rodzina Kowalskich",
      channel: "email",
      contact_action: "promised_payment",
      message_text: null,
      note_text: "Płatnik deklaruje wpłatę do piątku.",
      created_by_user_id: 2,
      created_by_user_name: "Operator",
      created_at: "2099-05-12T10:00:00",
    },
    {
      billing_contact_event_id: 904,
      organization_id: 42,
      billing_payer_id: 15,
      payer_display_name: "Firma Sigma",
      channel: "phone",
      contact_action: "needs_followup",
      message_text: null,
      note_text: "Oddzwonić po potwierdzenie przelewu.",
      created_by_user_id: 2,
      created_by_user_name: "Operator",
      created_at: "2099-05-13T10:00:00",
    },
  ],
};
const contactEvents = readBillingContactEvents(contactEventsPayload);
assert.equal(contactEvents.organization_id, 42);
assert.equal(contactEvents.events.length, 4);
assert.equal(contactEvents.events[0].channel, "sms");
assert.equal(contactEvents.events[1].message_text, "Ukryto techniczną lub wrażliwą treść wiadomości.");
const contactCenterView = buildBillingContactCenterView(contactEvents.events);
assert.equal(contactCenterView.summary.totalCount, 4);
assert.equal(contactCenterView.summary.draftCount, 1);
assert.equal(contactCenterView.summary.promisedPaymentCount, 1);
assert.equal(contactCenterView.summary.needsFollowupCount, 1);
assert.ok(contactCenterView.draftRows.some((row) => row.actionLabel === "Przygotowano treść" && row.payerHref === "/rozliczenia/platnicy/14"));
assert.ok(contactCenterView.promisedPaymentRows.some((row) => /Deklaracja płatności/.test(row.actionLabel)));
assert.ok(contactCenterView.followupRows.some((row) => row.actionLabel === "Wymaga ponownego kontaktu"));
assert.ok(contactCenterView.attentionRows.some((row) => row.paymentHref === "/rozliczenia/wplaty/61"));
assert.ok(contactCenterView.attentionRows.every((row) => row.workQueueHref === "/rozliczenia/sprawy"));
assert.equal(buildBillingContactCenterView(contactEvents.events, { channel: "sms" }).filteredRows.length, 1);
assert.equal(buildBillingContactCenterView(contactEvents.events, { action: "promised_payment" }).filteredRows.length, 1);
assert.equal(buildBillingContactCenterView(contactEvents.events, { payerQuery: "Firma Sigma" }).filteredRows.length, 1);

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
  paymentReviewStatuses: [
    {
      billing_payment_review_event_id: 801,
      organization_id: 42,
      billing_transaction_id: 61,
      status: "checked",
      note_text: "Wpłata sprawdzona.",
      created_by_user_id: 1,
      created_by_user_name: "Operator",
      created_at: "2026-03-09T10:00:00",
    },
    {
      billing_payment_review_event_id: 802,
      organization_id: 42,
      billing_transaction_id: 62,
      status: "waiting_for_contact",
      note_text: "Czeka na kontakt z płatnikiem.",
      created_by_user_id: 1,
      created_by_user_name: "Operator",
      created_at: "2026-03-10T10:00:00",
    },
    {
      billing_payment_review_event_id: 803,
      organization_id: 42,
      billing_transaction_id: 64,
      status: "do_not_auto_match",
      note_text: "Nie ruszać bez decyzji.",
      created_by_user_id: 1,
      created_by_user_name: "Operator",
      created_at: "2026-03-11T10:00:00",
    },
    {
      billing_payment_review_event_id: 804,
      organization_id: 42,
      billing_transaction_id: 65,
      status: "needs_review",
      note_text: "Brak jasnego identyfikatora.",
      created_by_user_id: 1,
      created_by_user_name: "Operator",
      created_at: "2026-03-12T10:00:00",
    },
  ],
  payerNotes: readBillingPayerNotes([
    {
      billing_note_id: 701,
      organization_id: 1,
      billing_payer_id: 1,
      author_user_id: 2,
      author_user_name: "Operator",
      note_type: "operator_note",
      note_text: "Ustalono rozmowę o saldzie po zajęciach.",
      created_at: "2099-05-08T10:00:00",
    },
  ]),
  contactEvents: contactEvents.events.map((event) => ({ ...event, billing_payer_id: 1 })),
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
assert.equal(paymentChargeRow.paymentHref, "/rozliczenia/wplaty/61");
assert.equal(paymentChargeRow.payerHref, "/rozliczenia/platnicy/1");
assert.equal(paymentChargeRow.periodHref, "/rozliczenia/okresy");
assert.match(paymentChargeRow.assignmentLabel, /Robotyka junior/);
assert.match(paymentChargeRow.contextLabel, /bezpiecznie pokazać w okresie/);
const payerOnlyPaymentRow = paymentsAllocationView.payerOnlyRows[0];
assert.ok(payerOnlyPaymentRow);
assert.equal(payerOnlyPaymentRow.paymentHref, "/rozliczenia/wplaty/64");
assert.equal(payerOnlyPaymentRow.periodLabel, "Nie przypisano do okresu");
assert.match(payerOnlyPaymentRow.contextLabel, /nie jest jeszcze przypisana do konkretnego naliczenia/i);
const unexplainedPaymentRow = paymentsAllocationView.unexplainedRows[0];
assert.ok(unexplainedPaymentRow);
assert.equal(unexplainedPaymentRow.paymentHref, "/rozliczenia/wplaty/65");
assert.equal(unexplainedPaymentRow.payerLabel, "Nieustalony płatnik");
assert.equal(unexplainedPaymentRow.statusLabel, "Do wyjaśnienia");
const paymentsContextText = paymentsAllocationView.contextItems.map((item) => item.value).join(" ");
assert.match(paymentsContextText, /nie dodaje wpłat/i);
assert.match(paymentsContextText, /Wpłata trafia do okresu tylko wtedy/i);
assert.doesNotMatch(paymentsContextText, /endpoint|payload|debug|demo/i);

const debtsView = buildBillingDebtsOverpaymentsView(snapshot);
assert.equal(debtsView.summary.debtTotalLabel, "220,00 PLN");
assert.equal(debtsView.summary.debtPayerCount, 1);
assert.equal(debtsView.summary.overpaymentTotalLabel, "40,00 PLN");
assert.equal(debtsView.summary.overpaymentPayerCount, 1);
assert.equal(debtsView.summary.settledPayerCount, 0);
assert.equal(debtsView.summary.payerOnlyPaymentCount, 1);
assert.ok(debtsView.summary.explanationCount >= 2);
assert.match(debtsView.summary.limitationLabel, /widoczna tylko przy płatniku/i);
assert.equal(debtsView.debtRows[0].payerLabel, "Rodzina Kowalskich");
assert.equal(debtsView.debtRows[0].amountLabel, "220,00 PLN");
assert.equal(debtsView.debtRows[0].attentionStatusLabel, "Do sprawdzenia wpłat");
assert.equal(debtsView.debtRows[0].payerHref, "/rozliczenia/platnicy/1");
assert.equal(debtsView.debtRows[0].paymentsHref, "/rozliczenia/wplaty");
assert.equal(debtsView.debtRows[0].periodsHref, "/rozliczenia/okresy");
assert.match(debtsView.debtRows[0].peopleLabel, /Lena Kowalska/);
assert.match(debtsView.debtRows[0].chargesLabel, /Marzec 2026/);
assert.match(debtsView.debtRows[0].servicesLabel, /Robotyka junior/);
assert.match(debtsView.debtRows[0].latestNoteLabel, /Ustalono rozmowę/);
assert.equal(debtsView.overpaymentRows[0].payerLabel, "Misja Robotyka");
assert.equal(debtsView.overpaymentRows[0].amountLabel, "40,00 PLN");
assert.match(debtsView.overpaymentRows[0].statusLabel, /nie została automatycznie rozliczona ani przeniesiona/i);
assert.doesNotMatch(debtsView.overpaymentRows[0].statusLabel, /zwróć|przenieś/i);
assert.ok(debtsView.explanationRows.some((row) => row.problemLabel === "Wpłaty do sprawdzenia" && row.nextHref === "/rozliczenia/wplaty"));
assert.ok(debtsView.explanationRows.some((row) => row.problemLabel === "Nadpłata wymaga decyzji"));
assert.ok(debtsView.urgentRows.some((row) => row.payerHref === "/rozliczenia/platnicy/1"));
assert.match(debtsView.contextItems.map((item) => item.value).join(" "), /Nie wysyła przypomnień|nie zmienia sald/i);

const workQueueView = buildBillingWorkQueueView(snapshot);
assert.ok(workQueueView.firstRows.length <= 8);
assert.ok(workQueueView.firstRows.every((row) => ["Wysoki", "Średni", "Niski"].includes(row.priority)));
assert.ok(workQueueView.firstRows.some((row) => row.type === "Wpłata do wyjaśnienia" && row.paymentHref === "/rozliczenia/wplaty/65"));
assert.ok(workQueueView.firstRows.some((row) => row.type === "Nie ruszać automatycznie" && row.paymentHref === "/rozliczenia/wplaty/64"));
assert.ok(workQueueView.contactRows.some((row) => row.type === "Czeka na kontakt" && row.paymentHref === "/rozliczenia/wplaty/62"));
assert.ok(workQueueView.paymentRows.some((row) => row.type === "Wpłata do wyjaśnienia" && row.paymentHref === "/rozliczenia/wplaty/64"));
assert.ok(workQueueView.paymentRows.some((row) => row.type === "Wpłata do wyjaśnienia" && row.paymentHref === "/rozliczenia/wplaty/65"));
assert.ok(workQueueView.overpaymentRows.some((row) => row.type === "Nadpłata do decyzji" && row.payerHref === "/rozliczenia/platnicy/2"));
assert.ok(workQueueView.firstRows.some((row) => row.type === "Zaległość do sprawdzenia" && row.payerHref === "/rozliczenia/platnicy/1"));
assert.ok(workQueueView.checkedRows.some((row) => row.type === "Sprawdzone" && row.paymentHref === "/rozliczenia/wplaty/61"));
assert.equal(workQueueView.firstRows.some((row) => row.type === "Sprawdzone"), false);
assert.match(workQueueView.contextItems.map((item) => item.value).join(" "), /nie zmienia sald/i);
assert.match(workQueueView.contextItems.map((item) => item.value).join(" "), /nie wysyła przypomnień/i);
assert.doesNotMatch(workQueueView.contextItems.map((item) => item.value).join(" "), /endpoint|payload|debug|match id|ledger entry id|foreign key|mutation/i);
const issueToHandle = workQueueView.firstRows.find((row) => row.paymentHref === "/rozliczenia/wplaty/65");
const issueToSnooze = workQueueView.firstRows.find((row) => row.paymentHref === "/rozliczenia/wplaty/64");
assert.ok(issueToHandle);
assert.ok(issueToSnooze);
assert.match(issueToHandle.issueKey, /^payment:65:/);
assert.equal(issueToHandle.targetType, "payment");
assert.equal(issueToHandle.targetId, 65);
const actionedWorkQueueView = buildBillingWorkQueueView({
  ...snapshot,
  workQueueEvents: [
    {
      billing_work_queue_event_id: 901,
      organization_id: 42,
      issue_key: issueToHandle.issueKey,
      issue_type: issueToHandle.type,
      target_type: issueToHandle.targetType,
      target_id: issueToHandle.targetId,
      action: "handled",
      note_text: "Sprawdzone w pracy operacyjnej.",
      created_by_user_id: 1,
      created_by_user_name: "Operator",
      created_at: "2026-03-13T10:00:00",
    },
    {
      billing_work_queue_event_id: 902,
      organization_id: 42,
      issue_key: issueToSnooze.issueKey,
      issue_type: issueToSnooze.type,
      target_type: issueToSnooze.targetType,
      target_id: issueToSnooze.targetId,
      action: "snoozed",
      note_text: null,
      created_by_user_id: 1,
      created_by_user_name: "Operator",
      created_at: "2026-03-13T11:00:00",
    },
  ],
});
assert.equal(actionedWorkQueueView.firstRows.some((row) => row.issueKey === issueToHandle.issueKey), false);
assert.equal(actionedWorkQueueView.firstRows.some((row) => row.issueKey === issueToSnooze.issueKey), false);
assert.ok(actionedWorkQueueView.handledRows.some((row) => row.issueKey === issueToHandle.issueKey));
assert.ok(actionedWorkQueueView.snoozedRows.some((row) => row.issueKey === issueToSnooze.issueKey));

const operationalReport = buildBillingOperationalReport(snapshot, "Misja Robotyka");
assert.equal(operationalReport.summary.debtTotalLabel, "220,00 PLN");
assert.equal(operationalReport.summary.debtPayerCount, 1);
assert.equal(operationalReport.summary.overpaymentTotalLabel, "40,00 PLN");
assert.equal(operationalReport.summary.overpaymentPayerCount, 1);
assert.equal(operationalReport.summary.chargeAssignedPaymentCount, 3);
assert.equal(operationalReport.summary.payerOnlyPaymentCount, 1);
assert.equal(operationalReport.summary.unexplainedPaymentCount, 1);
assert.ok(operationalReport.summary.activeIssueCount >= 4);
assert.ok(operationalReport.summary.contactCount >= 4);
assert.ok(operationalReport.summary.contactActionRequiredCount >= 2);
assert.ok(operationalReport.summaryCards.some((card) => card.label === "Suma zaległości" && card.value === "220,00 PLN"));
assert.ok(operationalReport.summaryCards.some((card) => card.label === "Wpłaty do wyjaśnienia" && card.value === "2"));
assert.ok(operationalReport.importantRows.length >= 5);
assert.ok(operationalReport.importantRows.length <= 10);
assert.ok(operationalReport.importantRows.some((row) => row.typeLabel === "Zaległość" && row.href === "/rozliczenia/platnicy/1"));
assert.ok(operationalReport.importantRows.some((row) => row.typeLabel === "Wpłata do wyjaśnienia" && row.href === "/rozliczenia/wplaty/65"));
assert.ok(operationalReport.importantRows.some((row) => row.typeLabel === "Kontakt wymagający działania" && row.href === "/rozliczenia/kontakty"));
assert.equal(operationalReport.paymentRows.some((row) => row.paymentHref === "/rozliczenia/wplaty/64"), true);
assert.equal(operationalReport.paymentRows.some((row) => row.paymentHref === "/rozliczenia/wplaty/61"), true);
assert.match(operationalReport.reportText, /Raport rozliczeniowy — Misja Robotyka/);
assert.match(operationalReport.reportText, /1\. Podsumowanie/);
assert.match(operationalReport.reportText, /2\. Najważniejsze do sprawdzenia/);
assert.match(operationalReport.reportText, /3\. Ograniczenia/);
assert.match(operationalReport.reportText, /nie jest dokumentem księgowym/i);
assert.match(operationalReport.reportText, /CASI Workspace nie wysyła tego raportu/i);
assert.doesNotMatch(
  operationalReport.reportText,
  /Wyślij raport|Pobierz PDF|Pobierz XLSX|Wyślij e-mail|Wyślij SMS|Zaksięguj|Dopasuj|windykacja|\braw\b|endpoint|payload|debug|match id|ledger entry id|foreign key|mutation/i,
);
assert.ok(operationalReport.limitations.some((item) => /nie zmienia danych/i.test(item)));
assert.ok(operationalReport.limitations.some((item) => /nie tworzy z niego pliku/i.test(item)));

const chargeAssignedPaymentDetail = buildBillingPaymentDetailView(snapshot, 61);
assert.ok(chargeAssignedPaymentDetail);
assert.equal(chargeAssignedPaymentDetail.title, "Szczegół wpłaty");
assert.equal(chargeAssignedPaymentDetail.amountLabel, "228,00 PLN");
assert.equal(chargeAssignedPaymentDetail.dateLabel, "2026-03-08");
assert.equal(chargeAssignedPaymentDetail.payerLabel, "Rodzina Kowalskich");
assert.equal(chargeAssignedPaymentDetail.payerHref, "/rozliczenia/platnicy/1");
assert.equal(chargeAssignedPaymentDetail.statusLabel, "Przypisana do naliczenia");
assert.equal(chargeAssignedPaymentDetail.assignmentRows[0].periodLabel, "Marzec 2026");
assert.equal(chargeAssignedPaymentDetail.assignmentRows[0].periodHref, "/rozliczenia/okresy");
assert.equal(chargeAssignedPaymentDetail.assignmentRows[0].personLabel, "Lena Kowalska");
assert.equal(chargeAssignedPaymentDetail.chargeRows[0].serviceLabel, "Robotyka junior");
assert.match(chargeAssignedPaymentDetail.assignmentSummaryLabel, /powiązanie z konkretnym naliczeniem/i);

const payerOnlyPaymentDetail = buildBillingPaymentDetailView(snapshot, 64);
assert.ok(payerOnlyPaymentDetail);
assert.equal(payerOnlyPaymentDetail.statusLabel, "Przypisana tylko do płatnika");
assert.equal(payerOnlyPaymentDetail.payerHref, "/rozliczenia/platnicy/1");
assert.equal(payerOnlyPaymentDetail.assignmentRows[0].periodLabel, "Nie przypisano do okresu");
assert.equal(payerOnlyPaymentDetail.assignmentRows[0].serviceLabel, "Nie przypisano do usługi");
assert.equal(payerOnlyPaymentDetail.chargeRows.length, 0);
assert.match(payerOnlyPaymentDetail.assignmentSummaryLabel, /nie jest jeszcze przypisana do konkretnego naliczenia/i);

const unexplainedPaymentDetail = buildBillingPaymentDetailView(snapshot, 65);
assert.ok(unexplainedPaymentDetail);
assert.equal(unexplainedPaymentDetail.statusLabel, "Do wyjaśnienia");
assert.equal(unexplainedPaymentDetail.payerLabel, "Nieustalony płatnik");
assert.equal(unexplainedPaymentDetail.payerHref, undefined);
assert.equal(unexplainedPaymentDetail.assignmentRows[0].periodLabel, "Nie przypisano do okresu");
assert.equal(unexplainedPaymentDetail.chargeRows.length, 0);
assert.match(unexplainedPaymentDetail.assignmentSummaryLabel, /nie zgaduje płatnika ani okresu/i);
assert.equal(buildBillingPaymentDetailView(snapshot, 999), null);
assert.equal(billingPaymentDetailPath(61), "/rozliczenia/wplaty/61");
assert.match(chargeAssignedPaymentDetail.contextItems.map((item) => item.value).join(" "), /nie zmienia salda/i);
assert.doesNotMatch(chargeAssignedPaymentDetail.contextItems.map((item) => item.value).join(" "), /endpoint|payload|debug|demo/i);

const paymentReviewStatusPayload = {
  billing_transaction_id: 61,
  organization_id: 42,
  current: {
    billing_payment_review_event_id: 701,
    organization_id: 42,
    billing_transaction_id: 61,
    status: "needs_review",
    note_text: "Sprawdzic tytul wplaty.",
    created_by_user_id: 1,
    created_by_user_name: "Operator",
    created_at: "2026-03-09T10:00:00",
  },
  history: [
    {
      billing_payment_review_event_id: 701,
      organization_id: 42,
      billing_transaction_id: 61,
      status: "needs_review",
      note_text: "Sprawdzic tytul wplaty.",
      created_by_user_id: 1,
      created_by_user_name: "Operator",
      created_at: "2026-03-09T10:00:00",
    },
  ],
};
const paymentReviewStatus = readBillingPaymentReviewStatus(paymentReviewStatusPayload, 61);
assert.equal(paymentReviewStatus.current.status, "needs_review");
assert.equal(paymentReviewStatus.current.note_text, "Sprawdzic tytul wplaty.");
assert.equal(paymentReviewStatus.history.length, 1);
const paymentReviewStatusesPayload = {
  organization_id: 42,
  statuses: [
    paymentReviewStatusPayload.current,
    {
      billing_payment_review_event_id: 702,
      organization_id: 42,
      billing_transaction_id: 64,
      status: "do_not_auto_match",
      note_text: "Nie ruszać bez decyzji.",
      created_by_user_id: 1,
      created_by_user_name: "Operator",
      created_at: "2026-03-10T10:00:00",
    },
  ],
};
const paymentReviewStatuses = readBillingPaymentReviewStatuses(paymentReviewStatusesPayload);
assert.equal(paymentReviewStatuses.organization_id, 42);
assert.equal(paymentReviewStatuses.statuses.length, 2);
assert.equal(paymentReviewStatuses.statuses[1].status, "do_not_auto_match");
assert.equal(billingPaymentReviewStatusEndpoint(61), "/billing/payments/61/review-status");
assert.equal(BILLING_PAYMENT_REVIEW_STATUSES_ENDPOINT, "/billing/payment-review-statuses");
assert.equal(BILLING_PAYMENT_REVIEW_STATUS_ENDPOINT_SUFFIX, "/review-status");
assert.equal(BILLING_PAYMENT_REVIEW_STATUS_MAX_NOTE_LENGTH, 1000);
assert.deepEqual(
  BILLING_PAYMENT_REVIEW_STATUS_OPTIONS.map((item) => item.label),
  ["Do wyja\u015bnienia", "Sprawdzone", "Czeka na kontakt", "Czeka na wp\u0142at\u0119", "Nie rusza\u0107 automatycznie"],
);
assert.match(BILLING_PAYMENT_REVIEW_STATUS_HELP_TEXT, /nie zmienia salda/i);
assert.match(BILLING_PAYMENT_REVIEW_STATUS_HELP_TEXT, /przypisania wp/iu);
assert.doesNotMatch(BILLING_PAYMENT_REVIEW_STATUS_HELP_TEXT, /payload|\braw\b|endpoint|debug|match id|ledger entry id|foreign key|mutation/i);
assert.deepEqual(buildBillingPaymentReviewStatusRequest("needs_review", "  Sprawdzic tytul.  ", "42"), {
  ok: true,
  payload: { status: "needs_review", note_text: "Sprawdzic tytul." },
});
assert.deepEqual(buildBillingPaymentReviewStatusRequest("checked", "   ", "42"), {
  ok: true,
  payload: { status: "checked" },
});
assert.equal(buildBillingPaymentReviewStatusRequest("settled", "", "42").ok, false);
assert.equal(buildBillingPaymentReviewStatusRequest("needs_review", "x".repeat(1001), "42").ok, false);
assert.equal(buildBillingPaymentReviewStatusRequest("needs_review", "", null).ok, false);
assert.throws(() => readBillingPaymentReviewStatus({ history: [] }, 61), ApiContractError);
assert.throws(() => readBillingPaymentReviewStatus({ billing_transaction_id: 61, current: null }, 61), ApiContractError);
assert.throws(() => readBillingPaymentReviewStatuses({ organization_id: 42 }), ApiContractError);
const workQueueEventsPayload = {
  organization_id: 42,
  events: [
    {
      billing_work_queue_event_id: 901,
      organization_id: 42,
      issue_key: "payment:65:unexplained:wplata-do-wyjasnienia",
      issue_type: "Wpłata do wyjaśnienia",
      target_type: "payment",
      target_id: 65,
      action: "handled",
      note_text: "Sprawdzone.",
      created_by_user_id: 1,
      created_by_user_name: "Operator",
      created_at: "2026-03-13T10:00:00",
    },
  ],
};
const workQueueEvents = readBillingWorkQueueEvents(workQueueEventsPayload);
assert.equal(workQueueEvents.organization_id, 42);
assert.equal(workQueueEvents.events[0].action, "handled");
assert.equal(BILLING_WORK_QUEUE_EVENTS_ENDPOINT, "/billing/work-queue/events");
assert.equal(BILLING_WORK_QUEUE_DECISION_MAX_NOTE_LENGTH, 1000);
assert.match(BILLING_WORK_QUEUE_DECISION_HELP_TEXT, /nie zmienia salda/i);
assert.match(BILLING_WORK_QUEUE_DECISION_HELP_TEXT, /wpłat ani naliczeń/i);
assert.doesNotMatch(BILLING_WORK_QUEUE_DECISION_HELP_TEXT, /payload|\braw\b|endpoint|debug|match id|ledger entry id|foreign key|mutation/i);
assert.deepEqual(buildBillingWorkQueueDecisionRequest(issueToHandle, "handled", "  Sprawdzone.  ", "42"), {
  ok: true,
  payload: {
    issue_key: issueToHandle.issueKey,
    issue_type: issueToHandle.type,
    target_type: issueToHandle.targetType,
    target_id: issueToHandle.targetId,
    action: "handled",
    note_text: "Sprawdzone.",
  },
});
assert.deepEqual(buildBillingWorkQueueDecisionRequest(issueToSnooze, "snoozed", "   ", "42"), {
  ok: true,
  payload: {
    issue_key: issueToSnooze.issueKey,
    issue_type: issueToSnooze.type,
    target_type: issueToSnooze.targetType,
    target_id: issueToSnooze.targetId,
    action: "snoozed",
  },
});
assert.equal(buildBillingWorkQueueDecisionRequest(issueToHandle, "handled", "x".repeat(1001), "42").ok, false);
assert.equal(buildBillingWorkQueueDecisionRequest(issueToHandle, "handled", "", null).ok, false);
assert.throws(() => readBillingWorkQueueEvents({ organization_id: 42 }), ApiContractError);

const nextStepEventsPayload = {
  organization_id: 42,
  events: [
    {
      billing_next_step_event_id: 1001,
      organization_id: 42,
      target_type: "work_queue_issue",
      related_issue_key: issueToHandle.issueKey,
      step_type: "check_payment",
      event_action: "planned",
      title: "Sprawdzić, czy wpłata przyszła po piątku",
      note_text: "Test live: ręczny krok bez przypomnienia.",
      planned_for: "2099-05-12",
      created_by_user_id: 1,
      created_by_user_name: "Operator",
      created_at: "2099-05-10T10:00:00",
    },
    {
      billing_next_step_event_id: 1002,
      organization_id: 42,
      target_type: "payer",
      target_id: 14,
      step_type: "call",
      event_action: "completed",
      title: "Zadzwonić w sprawie rozliczenia",
      created_by_user_id: 1,
      created_by_user_name: "Operator",
      created_at: "2099-05-11T10:00:00",
    },
    {
      billing_next_step_event_id: 1003,
      organization_id: 42,
      target_type: "payment",
      target_id: 61,
      step_type: "clarify_payment",
      event_action: "snoozed",
      title: "Poczekać na opis wpłaty",
      note_text: "C:\\Users\\secret\\payment.txt",
      created_by_user_id: 1,
      created_by_user_name: "Operator",
      created_at: "2099-05-12T10:00:00",
    },
  ],
};
const nextStepEvents = readBillingNextStepEvents(nextStepEventsPayload);
assert.equal(nextStepEvents.organization_id, 42);
assert.equal(nextStepEvents.events.length, 3);
assert.equal(nextStepEvents.events[2].note_text, "Ukryto techniczną lub wrażliwą treść notatki.");
assert.equal(BILLING_NEXT_STEP_EVENTS_ENDPOINT, "/billing/next-step-events");
assert.equal(BILLING_NEXT_STEP_TITLE_MAX_LENGTH, 200);
assert.equal(BILLING_NEXT_STEP_NOTE_MAX_LENGTH, 1000);
assert.match(BILLING_NEXT_STEP_HELP_TEXT, /nie zmienia salda/i);
assert.match(BILLING_NEXT_STEP_HELP_TEXT, /Nie tworzy automatycznego przypomnienia/i);
assert.equal(BILLING_NEXT_STEP_TYPE_OPTIONS.some((option) => option.value === "check_payment" && option.label === "Sprawdzić wpłatę"), true);
const plannedNextStepRows = buildBillingNextStepRows(nextStepEvents.events, { action: "planned" });
assert.equal(plannedNextStepRows.length, 1);
assert.equal(plannedNextStepRows[0].title, "Sprawdzić, czy wpłata przyszła po piątku");
assert.equal(plannedNextStepRows[0].targetHref, "/rozliczenia/sprawy");
assert.equal(plannedNextStepRows[0].noteText, "Test live: ręczny krok bez przypomnienia.");
assert.equal(buildBillingNextStepRows(nextStepEvents.events, { action: "completed" }).length, 1);
assert.equal(buildBillingNextStepRows(nextStepEvents.events, { action: "snoozed" }).length, 1);
assert.equal(buildBillingNextStepRows(nextStepEvents.events, { targetType: "payer", targetId: 14 })[0].targetHref, "/rozliczenia/platnicy/14");
assert.deepEqual(buildBillingNextStepRequest({
  targetType: "work_queue_issue",
  relatedIssueKey: issueToHandle.issueKey,
  stepType: "check_payment",
  eventAction: "planned",
  title: "  Sprawdzić wpłatę  ",
  noteText: "  Bez automatyzacji.  ",
  plannedFor: "2099-05-12",
  organizationId: "42",
}), {
  ok: true,
  payload: {
    target_type: "work_queue_issue",
    related_issue_key: issueToHandle.issueKey,
    step_type: "check_payment",
    event_action: "planned",
    title: "Sprawdzić wpłatę",
    note_text: "Bez automatyzacji.",
    planned_for: "2099-05-12",
  },
});
assert.equal(buildBillingNextStepRequest({
  targetType: "payer",
  targetId: 14,
  stepType: "call",
  title: "Zadzwonić",
  noteText: "",
  organizationId: "42",
}).ok, true);
assert.equal(buildBillingNextStepRequest({
  targetType: "payer",
  stepType: "call",
  title: "Zadzwonić",
  noteText: "",
  organizationId: "42",
}).ok, false);
assert.equal(buildBillingNextStepRequest({
  targetType: "work_queue_issue",
  stepType: "check_payment",
  title: "Sprawdzić",
  noteText: "",
  organizationId: "42",
}).ok, false);
assert.equal(buildBillingNextStepRequest({
  targetType: "payer",
  targetId: 14,
  stepType: "call",
  title: " ",
  noteText: "",
  organizationId: "42",
}).ok, false);
assert.equal(buildBillingNextStepRequest({
  targetType: "payer",
  targetId: 14,
  stepType: "call",
  title: "x".repeat(BILLING_NEXT_STEP_TITLE_MAX_LENGTH + 1),
  noteText: "",
  organizationId: "42",
}).ok, false);
assert.equal(buildBillingNextStepRequest({
  targetType: "payer",
  targetId: 14,
  stepType: "call",
  title: "Zadzwonić",
  noteText: "x".repeat(BILLING_NEXT_STEP_NOTE_MAX_LENGTH + 1),
  organizationId: "42",
}).ok, false);
assert.equal(buildBillingNextStepRequest({
  targetType: "payer",
  targetId: 14,
  stepType: "call",
  title: "Zadzwonić",
  noteText: "",
  plannedFor: "jutro",
  organizationId: "42",
}).ok, false);
assert.equal(buildBillingNextStepRequest({
  targetType: "payer",
  targetId: 14,
  stepType: "call",
  title: "Zadzwonić",
  noteText: "",
  organizationId: null,
}).ok, false);
assert.throws(() => readBillingNextStepEvents({ organization_id: 42 }), ApiContractError);
assert.throws(() => readBillingNextStepEvents({ organization_id: 42, events: [{ title: "Brak ID" }] }), ApiContractError);

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
assert.equal(payerDetail.noteRows.length, 1);
assert.equal(payerDetail.noteRows[0].typeLabel, "Notatka operatora");
assert.equal(payerDetail.noteRows[0].noteText, "Ustalono rozmowę o saldzie po zajęciach.");
assert.equal(payerDetail.contactEventRows.length, 4);
assert.ok(payerDetail.contactEventRows.some((row) => row.actionLabel === "Zapisano kontakt" && row.channelLabel === "Telefon"));
assert.ok(payerDetail.contactEventRows.some((row) => row.messageText === "Ukryto techniczną lub wrażliwą treść wiadomości."));
assert.ok(payerDetail.contactEventRows.some((row) => row.actionLabel === "Przygotowano treść" && /wpłatą #61/.test(row.contextLabel)));
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
assert.equal(BILLING_DEBTS_ROUTE, "/rozliczenia/zaleglosci");
assert.equal(BILLING_WORK_QUEUE_ROUTE, "/rozliczenia/sprawy");
assert.equal(BILLING_CONTACT_CENTER_ROUTE, "/rozliczenia/kontakty");
assert.equal(BILLING_OPERATIONAL_REPORT_ROUTE, "/rozliczenia/raport");
assert.equal(BILLING_PAYMENT_DETAIL_ORGANIZATION_REQUIRED_TITLE, "Wybierz organizację, aby zobaczyć wpłatę");
assert.doesNotMatch(BILLING_PAYMENT_DETAIL_ORGANIZATION_REQUIRED_DESCRIPTION, /organization_id|endpoint|payload|debug/i);
assert.equal(BILLING_READ_ONLY, true);
assert.equal(BILLING_PAYER_NOTE_CREATE_ENABLED, true);
assert.equal(BILLING_PAYER_NOTE_MAX_LENGTH, 2000);
assert.equal(BILLING_PAYER_NOTE_ENDPOINT_SUFFIX, "/notes");
assert.equal(billingPayerNoteEndpoint(14), "/billing/payers/14/notes");
assert.match(BILLING_PAYER_NOTE_HELP_TEXT, /nie zmienia salda/i);
assert.match(BILLING_PAYER_NOTE_HELP_TEXT, /przypisań wpłat/i);
assert.doesNotMatch(BILLING_PAYER_NOTE_HELP_TEXT, /endpoint|payload|debug|demo/i);
assert.equal(BILLING_CONTACT_EVENTS_ENDPOINT, "/billing/contact-events");
assert.equal(BILLING_CONTACT_MESSAGE_MAX_LENGTH, 2000);
assert.equal(BILLING_CONTACT_NOTE_MAX_LENGTH, 1000);
assert.equal(BILLING_CONTACT_CHANNEL_OPTIONS.some((option) => option.value === "sms" && option.label === "SMS"), true);
assert.equal(BILLING_CONTACT_ACTION_OPTIONS.some((option) => option.value === "draft_prepared" && option.label === "Przygotowano treść"), true);
assert.equal(BILLING_CONTACT_DRAFT_TEMPLATES.length >= 3, true);
assert.match(BILLING_CONTACT_NO_SEND_HELP_TEXT, /nie wysyła tej wiadomości/i);
assert.match(BILLING_CONTACT_NO_SEND_HELP_TEXT, /samodzielnie/i);
assert.match(BILLING_CONTACT_EVENT_HELP_TEXT, /Nie zmienia salda/i);
assert.doesNotMatch(BILLING_CONTACT_EVENT_HELP_TEXT, /endpoint|payload|debug|demo|mutation/i);
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
assert.match(fs.readFileSync(path.join(srcRoot, "app", "rozliczenia", "zaleglosci", "page.tsx"), "utf8"), /BillingDebtsOverpaymentsPage/);
assert.match(fs.readFileSync(path.join(srcRoot, "app", "rozliczenia", "sprawy", "page.tsx"), "utf8"), /BillingWorkQueuePage/);
assert.match(fs.readFileSync(path.join(srcRoot, "app", "rozliczenia", "kontakty", "page.tsx"), "utf8"), /BillingContactCenterPage/);
assert.match(fs.readFileSync(path.join(srcRoot, "app", "rozliczenia", "raport", "page.tsx"), "utf8"), /BillingOperationalReportPage/);
const workQueuePageSource = fs.readFileSync(path.join(srcRoot, "modules", "billing", "BillingWorkQueuePage.tsx"), "utf8");
assert.match(workQueuePageSource, /Oznacz jako obsłużoną/);
assert.match(workQueuePageSource, /Odłóż/);
assert.match(workQueuePageSource, /Przygotuj kontakt/);
assert.match(workQueuePageSource, /Kontakty rozliczeniowe/);
assert.match(workQueuePageSource, /BILLING_OPERATIONAL_REPORT_ROUTE/);
assert.match(workQueuePageSource, /BILLING_WORK_QUEUE_DECISION_HELP_TEXT/);
assert.match(workQueuePageSource, /Dodaj następny krok/);
assert.match(workQueuePageSource, /Następne kroki/);
assert.match(workQueuePageSource, /Ostatnio wykonane kroki/);
assert.match(workQueuePageSource, /BILLING_NEXT_STEP_HELP_TEXT/);
assert.doesNotMatch(workQueuePageSource, /zaksięguj|rozlicz nadpłatę|dopasuj|wyślij przypomnienie|wyślij SMS|wyślij e-mail|dodaj do kalendarza/i);
const billingCenterReportLinkSource = fs.readFileSync(path.join(srcRoot, "modules", "billing", "BillingLedgerOverview.tsx"), "utf8");
const debtsReportLinkSource = fs.readFileSync(path.join(srcRoot, "modules", "billing", "BillingDebtsOverpaymentsPage.tsx"), "utf8");
const contactCenterReportLinkSource = fs.readFileSync(path.join(srcRoot, "modules", "billing", "BillingContactCenterPage.tsx"), "utf8");
const operationalReportPageSource = fs.readFileSync(path.join(srcRoot, "modules", "billing", "BillingOperationalReportPage.tsx"), "utf8");
assert.match(billingCenterReportLinkSource, /BILLING_OPERATIONAL_REPORT_ROUTE/);
assert.match(debtsReportLinkSource, /BILLING_OPERATIONAL_REPORT_ROUTE/);
assert.match(contactCenterReportLinkSource, /BILLING_OPERATIONAL_REPORT_ROUTE/);
assert.match(operationalReportPageSource, /Ten raport nie zmienia danych/);
assert.match(operationalReportPageSource, /CASI Workspace nie wysyła tego raportu/);
assert.match(operationalReportPageSource, /Raport do skopiowania/);
assert.doesNotMatch(
  operationalReportPageSource,
  /Wyślij raport|Pobierz PDF|Pobierz XLSX|Wyślij e-mail|Wyślij SMS|Zaksięguj|Dopasuj|windykacja|\braw\b|endpoint|techniczny payload|debug|match id|ledger entry id|foreign key|mutation/i,
);
const payerDetailPageSource = fs.readFileSync(path.join(srcRoot, "modules", "billing", "BillingPayerDetailPage.tsx"), "utf8");
assert.match(payerDetailPageSource, /Kontakt rozliczeniowy/);
assert.match(payerDetailPageSource, /Zapisz kontakt/);
assert.match(payerDetailPageSource, /Zobacz wszystkie kontakty rozliczeniowe/);
assert.match(payerDetailPageSource, /BILLING_CONTACT_NO_SEND_HELP_TEXT/);
assert.match(payerDetailPageSource, /Następny krok/);
assert.match(payerDetailPageSource, /Zapisz krok/);
assert.match(payerDetailPageSource, /BILLING_NEXT_STEP_HELP_TEXT/);
assert.doesNotMatch(payerDetailPageSource, /Wyślij SMS|Wyślij e-mail|Wyślij przypomnienie|Dodaj płatność|Dopasuj wpłatę|Dodaj do kalendarza/i);
const paymentDetailPageSource = fs.readFileSync(path.join(srcRoot, "modules", "billing", "BillingPaymentDetailPage.tsx"), "utf8");
assert.match(paymentDetailPageSource, /Następny krok/);
assert.match(paymentDetailPageSource, /BILLING_NEXT_STEP_HELP_TEXT/);
assert.doesNotMatch(paymentDetailPageSource, /Wyślij SMS|Wyślij e-mail|Wyślij przypomnienie|Dodaj płatność|Dopasuj wpłatę|Dodaj do kalendarza/i);
const contactCenterPageSource = fs.readFileSync(path.join(srcRoot, "modules", "billing", "BillingContactCenterPage.tsx"), "utf8");
assert.match(contactCenterPageSource, /Kontakty rozliczeniowe/);
assert.match(contactCenterPageSource, /Przygotowane treści/);
assert.match(contactCenterPageSource, /Deklaracja płatności nie oznacza dodania wpłaty/);
assert.match(contactCenterPageSource, /CASI Workspace nie wysłał tej wiadomości/);
assert.match(contactCenterPageSource, /BILLING_CONTACT_NO_SEND_HELP_TEXT/);
assert.doesNotMatch(contactCenterPageSource, /Wyślij SMS|Wyślij e-mail|Wyślij przypomnienie|Dodaj płatność|Dopasuj wpłatę|raw JSON|techniczny payload|endpoint|debug|match id|ledger entry id|foreign key|mutation/i);
const ledgerOverviewSource = fs.readFileSync(path.join(srcRoot, "modules", "billing", "BillingLedgerOverview.tsx"), "utf8");
assert.match(ledgerOverviewSource, /Zaległości i nadpłaty/);
assert.match(ledgerOverviewSource, /Sprawy rozliczeniowe/);
assert.match(ledgerOverviewSource, /Kontakty rozliczeniowe/);
assert.match(fs.readFileSync(path.join(srcRoot, "modules", "billing", "BillingDebtsOverpaymentsPage.tsx"), "utf8"), /Sprawy rozliczeniowe/);
assert.equal(canUseBillingOrganizationScope(null), false);
assert.equal(canUseBillingOrganizationScope(""), false);
assert.equal(canUseBillingOrganizationScope("   "), false);
assert.equal(canUseBillingOrganizationScope("42"), true);
assert.equal(canUseBillingOrganizationScope(42), true);
assert.deepEqual(withActiveOrganizationQuery("42"), { organization_id: "42" });
assert.deepEqual(buildBillingPayerNoteRequest("  Ustalono termin dopłaty.  ", "42"), {
  ok: true,
  payload: { note_text: "Ustalono termin dopłaty." },
});
assert.equal(buildBillingPayerNoteRequest("Ustalono termin dopłaty.", null).ok, false);
assert.equal(buildBillingPayerNoteRequest("   ", "42").ok, false);
assert.equal(buildBillingPayerNoteRequest("x".repeat(BILLING_PAYER_NOTE_MAX_LENGTH + 1), "42").ok, false);
assert.equal(getBillingPayerNoteErrorState(new ApiError("Nie zapisano", 500)).title, "Backend nie zapisał notatki");
assert.deepEqual(
  buildBillingContactEventRequest({
    payerId: 14,
    channel: "sms",
    contactAction: "draft_prepared",
    messageText: "  Prosimy o sprawdzenie rozliczenia.  ",
    noteText: "  Do wysłania ręcznie.  ",
    organizationId: "42",
    relatedPaymentId: 61,
    relatedIssueKey: " payment:61:payer-only ",
  }),
  {
    ok: true,
    payload: {
      payer_id: 14,
      related_payment_id: 61,
      related_issue_key: "payment:61:payer-only",
      channel: "sms",
      contact_action: "draft_prepared",
      message_text: "Prosimy o sprawdzenie rozliczenia.",
      note_text: "Do wysłania ręcznie.",
    },
  },
);
assert.equal(
  buildBillingContactEventRequest({
    payerId: 14,
    channel: "phone",
    contactAction: "contact_logged",
    messageText: "",
    noteText: "Rozmowa bez odpowiedzi.",
    organizationId: "42",
  }).ok,
  true,
);
assert.equal(
  buildBillingContactEventRequest({
    payerId: 14,
    channel: "sms",
    contactAction: "draft_prepared",
    messageText: "",
    noteText: "Brak wiadomości.",
    organizationId: "42",
  }).ok,
  false,
);
assert.equal(
  buildBillingContactEventRequest({
    payerId: 14,
    channel: "sms",
    contactAction: "draft_prepared",
    messageText: "x".repeat(BILLING_CONTACT_MESSAGE_MAX_LENGTH + 1),
    noteText: "",
    organizationId: "42",
  }).ok,
  false,
);
assert.equal(
  buildBillingContactEventRequest({
    payerId: 14,
    channel: "phone",
    contactAction: "contact_logged",
    messageText: "",
    noteText: "x".repeat(BILLING_CONTACT_NOTE_MAX_LENGTH + 1),
    organizationId: "42",
  }).ok,
  false,
);
assert.equal(
  buildBillingContactEventRequest({
    payerId: 14,
    channel: "phone",
    contactAction: "contact_logged",
    messageText: "",
    noteText: "Rozmowa.",
    organizationId: null,
  }).ok,
  false,
);
assert.equal(getBillingContactEventErrorState(new ApiError("Nie zapisano", 500)).title, "Backend nie zapisał kontaktu");

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
  debtsView.summary.limitationLabel,
  ...debtsView.urgentRows.flatMap((row) => [row.payerLabel, row.amountLabel, row.reasonLabel, row.nextStepLabel, row.payerHref, row.paymentsHref]),
  ...debtsView.debtRows.flatMap((row) => [
    row.payerLabel,
    row.payerHref,
    row.amountLabel,
    row.peopleLabel,
    row.chargesLabel,
    row.periodsLabel,
    row.servicesLabel,
    row.lastPaymentLabel,
    row.payerOnlyPaymentLabel,
    row.latestNoteLabel,
    row.attentionStatusLabel,
    row.reasonLabel,
    row.nextStepLabel,
    row.paymentsHref,
    row.periodsHref,
  ]),
  ...debtsView.overpaymentRows.flatMap((row) => [
    row.payerLabel,
    row.payerHref,
    row.amountLabel,
    row.peopleLabel,
    row.lastPaymentLabel,
    row.possibleSourceLabel,
    row.statusLabel,
    row.paymentsHref,
  ]),
  ...debtsView.explanationRows.flatMap((row) => [row.payerLabel, row.problemLabel, row.amountLabel, row.reasonLabel, row.nextHref]),
  ...debtsView.contextItems.flatMap((item) => [item.label, item.value]),
  ...workQueueView.firstRows.flatMap((row) => [row.type, row.priority, row.payerLabel, row.amountLabel, row.reason, row.nextStep, row.href, row.paymentHref, row.payerHref]),
  ...workQueueView.paymentRows.flatMap((row) => [row.type, row.priority, row.payerLabel, row.amountLabel, row.reason, row.nextStep, row.href, row.paymentHref, row.payerHref]),
  ...workQueueView.contactRows.flatMap((row) => [row.type, row.priority, row.payerLabel, row.amountLabel, row.reason, row.nextStep, row.href, row.paymentHref, row.payerHref]),
  ...workQueueView.overpaymentRows.flatMap((row) => [row.type, row.priority, row.payerLabel, row.amountLabel, row.reason, row.nextStep, row.href, row.paymentHref, row.payerHref]),
  ...workQueueView.checkedRows.flatMap((row) => [row.type, row.priority, row.payerLabel, row.amountLabel, row.reason, row.nextStep, row.href, row.paymentHref, row.payerHref]),
  ...workQueueView.contextItems.flatMap((item) => [item.label, item.value]),
  ...buildBillingNextStepRows(nextStepEvents.events).flatMap((row) => [
    row.title,
    row.stepTypeLabel,
    row.eventActionLabel,
    row.targetLabel,
    row.targetHref,
    row.dateLabel,
    row.noteText,
  ]),
  ...(chargeAssignedPaymentDetail
    ? [
        chargeAssignedPaymentDetail.title,
        chargeAssignedPaymentDetail.amountLabel,
        chargeAssignedPaymentDetail.dateLabel,
        chargeAssignedPaymentDetail.descriptionLabel,
        chargeAssignedPaymentDetail.payerLabel,
        chargeAssignedPaymentDetail.statusLabel,
        chargeAssignedPaymentDetail.assignmentSummaryLabel,
        ...chargeAssignedPaymentDetail.assignmentRows.flatMap((row) => [
          row.payerLabel,
          row.personLabel,
          row.serviceLabel,
          row.periodLabel,
          row.amountLabel,
          row.statusLabel,
          row.contextLabel,
          row.payerHref,
          row.periodHref,
        ]),
        ...chargeAssignedPaymentDetail.chargeRows.flatMap((row) => [row.periodLabel, row.personLabel, row.serviceLabel, row.amountLabel, row.statusLabel]),
        ...chargeAssignedPaymentDetail.contextItems.flatMap((item) => [item.label, item.value]),
      ]
    : []),
  ...(payerOnlyPaymentDetail
    ? [
        payerOnlyPaymentDetail.statusLabel,
        payerOnlyPaymentDetail.assignmentSummaryLabel,
        ...payerOnlyPaymentDetail.assignmentRows.flatMap((row) => [row.payerLabel, row.serviceLabel, row.periodLabel, row.contextLabel, row.payerHref]),
      ]
    : []),
  ...(unexplainedPaymentDetail
    ? [
        unexplainedPaymentDetail.statusLabel,
        unexplainedPaymentDetail.assignmentSummaryLabel,
        ...unexplainedPaymentDetail.assignmentRows.flatMap((row) => [row.payerLabel, row.serviceLabel, row.periodLabel, row.contextLabel]),
      ]
    : []),
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
        ...payerDetail.noteRows.flatMap((row) => [row.authorLabel, row.dateLabel, row.typeLabel, row.noteText]),
        ...payerDetail.contactEventRows.flatMap((row) => [
          row.channelLabel,
          row.actionLabel,
          row.authorLabel,
          row.dateLabel,
          row.messageText,
          row.noteText,
          row.contextLabel,
        ]),
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
assert.throws(() => readBillingPayerNotes({ notes: [] }), ApiContractError);
assert.throws(() => readBillingPayerNotes([{ note_text: "Brak ID" }]), ApiContractError);
assert.throws(() => readBillingContactEvents({ events: "bad" }), ApiContractError);
assert.throws(() => readBillingContactEvents({ organization_id: 42, events: [{ billing_contact_event_id: 1 }] }), ApiContractError);
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

  await withMockedFetch(
    async (url, options) => {
      assert.equal(url, "/api/billing/payers/14/notes?organization_id=42");
      assert.equal(options.method, "POST");
      assert.deepEqual(JSON.parse(options.body), { note_text: "Ustalono termin dopłaty." });
      return jsonResponse(201, payerNotes[0]);
    },
    async () => {
      const payload = await api.addBillingPayerNote(14, "Ustalono termin dopłaty.", "42");
      assert.equal(readBillingPayerNotes([payload])[0].note_text, "Rodzic potwierdził wyjaśnienie salda.");
    },
  );

  await withMockedFetch(
    async (url, options) => {
      assert.ok(url.startsWith("/api/billing/contact-events?"));
      assert.match(url, /organization_id=42/);
      assert.match(url, /payer_id=14/);
      assert.match(url, /limit=50/);
      assert.equal(options.method, "GET");
      assert.equal(options.body, undefined);
      return jsonResponse(200, contactEventsPayload);
    },
    async () => {
      const payload = await api.billingContactEvents(withActiveOrganizationQuery("42", { payer_id: 14, limit: 50 }));
      const events = readBillingContactEvents(payload);
      assert.equal(events.events.length, 4);
    },
  );

  await withMockedFetch(
    async (url, options) => {
      assert.equal(url, "/api/billing/contact-events?organization_id=42");
      assert.equal(options.method, "POST");
      assert.deepEqual(JSON.parse(options.body), {
        payer_id: 14,
        channel: "sms",
        contact_action: "draft_prepared",
        message_text: "Prosimy o sprawdzenie rozliczenia.",
        note_text: "Do wysłania ręcznie.",
      });
      return jsonResponse(201, contactEventsPayload.events[0]);
    },
    async () => {
      const payload = await api.addBillingContactEvent(
        {
          payer_id: 14,
          channel: "sms",
          contact_action: "draft_prepared",
          message_text: "Prosimy o sprawdzenie rozliczenia.",
          note_text: "Do wysłania ręcznie.",
        },
        "42",
      );
      assert.equal(readBillingContactEvents({ organization_id: 42, events: [payload] }).events[0].contact_action, "draft_prepared");
    },
  );

  await withMockedFetch(
    async (url, options) => {
      assert.ok(url.startsWith("/api/billing/next-step-events?"));
      assert.match(url, /organization_id=42/);
      assert.match(url, /target_type=payer/);
      assert.match(url, /target_id=14/);
      assert.equal(options.method, "GET");
      assert.equal(options.body, undefined);
      return jsonResponse(200, nextStepEventsPayload);
    },
    async () => {
      const payload = await api.billingNextStepEvents(withActiveOrganizationQuery("42", { target_type: "payer", target_id: 14, limit: 50 }));
      const events = readBillingNextStepEvents(payload);
      assert.equal(events.events.length, 3);
    },
  );

  await withMockedFetch(
    async (url, options) => {
      assert.equal(url, "/api/billing/next-step-events?organization_id=42");
      assert.equal(options.method, "POST");
      assert.deepEqual(JSON.parse(options.body), {
        target_type: "work_queue_issue",
        related_issue_key: issueToHandle.issueKey,
        step_type: "check_payment",
        event_action: "planned",
        title: "Sprawdzić wpłatę",
        note_text: "Bez automatyzacji.",
      });
      return jsonResponse(201, nextStepEventsPayload.events[0]);
    },
    async () => {
      const validation = buildBillingNextStepRequest({
        targetType: "work_queue_issue",
        relatedIssueKey: issueToHandle.issueKey,
        stepType: "check_payment",
        eventAction: "planned",
        title: "Sprawdzić wpłatę",
        noteText: "Bez automatyzacji.",
        organizationId: "42",
      });
      assert.equal(validation.ok, true);
      const payload = await api.addBillingNextStepEvent(validation.payload, "42");
      assert.equal(readBillingNextStepEvents({ organization_id: 42, events: [payload] }).events[0].event_action, "planned");
    },
  );

  await withMockedFetch(
    async (url, options) => {
      assert.equal(url, "/api/billing/payments/61/review-status?organization_id=42");
      assert.equal(options.method, "GET");
      assert.equal(options.body, undefined);
      return jsonResponse(200, paymentReviewStatusPayload);
    },
    async () => {
      const payload = await api.billingPaymentReviewStatus(61, withActiveOrganizationQuery("42"));
      const status = readBillingPaymentReviewStatus(payload, 61);
      assert.equal(status.current.status, "needs_review");
    },
  );

  await withMockedFetch(
    async (url, options) => {
      assert.ok(url.startsWith("/api/billing/payment-review-statuses?"));
      assert.match(url, /organization_id=42/);
      assert.match(url, /limit=1000/);
      assert.equal(options.method, "GET");
      assert.equal(options.body, undefined);
      return jsonResponse(200, paymentReviewStatusesPayload);
    },
    async () => {
      const payload = await api.billingPaymentReviewStatuses(withActiveOrganizationQuery("42", { limit: 1000 }));
      const statuses = readBillingPaymentReviewStatuses(payload);
      assert.equal(statuses.statuses.length, 2);
    },
  );

  await withMockedFetch(
    async (url, options) => {
      assert.ok(url.startsWith("/api/billing/work-queue/events?"));
      assert.match(url, /organization_id=42/);
      assert.match(url, /limit=1000/);
      assert.equal(options.method, "GET");
      assert.equal(options.body, undefined);
      return jsonResponse(200, workQueueEventsPayload);
    },
    async () => {
      const payload = await api.billingWorkQueueEvents(withActiveOrganizationQuery("42", { limit: 1000 }));
      const events = readBillingWorkQueueEvents(payload);
      assert.equal(events.events.length, 1);
    },
  );

  await withMockedFetch(
    async (url, options) => {
      assert.equal(url, "/api/billing/payments/61/review-status?organization_id=42");
      assert.equal(options.method, "POST");
      assert.deepEqual(JSON.parse(options.body), { status: "checked", note_text: "Zweryfikowano tytul." });
      return jsonResponse(201, { ...paymentReviewStatusPayload.current, status: "checked", note_text: "Zweryfikowano tytul." });
    },
    async () => {
      const payload = await api.updateBillingPaymentReviewStatus(61, { status: "checked", note_text: "Zweryfikowano tytul." }, "42");
      assert.equal(payload.status, "checked");
    },
  );

  await withMockedFetch(
    async (url, options) => {
      assert.equal(url, "/api/billing/work-queue/events?organization_id=42");
      assert.equal(options.method, "POST");
      assert.deepEqual(JSON.parse(options.body), {
        issue_key: issueToHandle.issueKey,
        issue_type: issueToHandle.type,
        target_type: issueToHandle.targetType,
        target_id: issueToHandle.targetId,
        action: "handled",
        note_text: "Sprawdzone.",
      });
      return jsonResponse(201, workQueueEventsPayload.events[0]);
    },
    async () => {
      const validation = buildBillingWorkQueueDecisionRequest(issueToHandle, "handled", "Sprawdzone.", "42");
      assert.equal(validation.ok, true);
      const payload = await api.addBillingWorkQueueEvent(validation.payload, "42");
      assert.equal(readBillingWorkQueueEvents({ organization_id: 42, events: [payload] }).events[0].action, "handled");
    },
  );

  let refreshCount = 0;
  let submittingStates = [];
  let submittedPayload = null;
  const submitter = createBillingPayerNoteSubmitter({
    refreshDetail: async () => {
      refreshCount += 1;
    },
    setSubmitting: (isSubmitting) => {
      submittingStates.push(isSubmitting);
    },
    submitNote: async (payload) => {
      submittedPayload = payload;
    },
  });
  const submitResult = await submitter(buildBillingPayerNoteRequest("  Ustalono termin dopłaty.  ", "42"));
  assert.equal(submitResult.status, "success");
  assert.deepEqual(submittedPayload, { note_text: "Ustalono termin dopłaty." });
  assert.equal(refreshCount, 1);
  assert.deepEqual(submittingStates, [true, false]);

  const failingSubmitter = createBillingPayerNoteSubmitter({
    refreshDetail: async () => {
      throw new Error("Refresh should not run after failed submit.");
    },
    setSubmitting: () => {},
    submitNote: async () => {
      throw new ApiError("Backend odmówił", 500);
    },
  });
  const failingResult = await failingSubmitter(buildBillingPayerNoteRequest("Treść", "42"));
  assert.equal(failingResult.status, "error");
  assert.equal(failingResult.errorState.title, "Backend nie zapisał notatki");

  refreshCount = 0;
  submittingStates = [];
  submittedPayload = null;
  const contactSubmitter = createBillingContactEventSubmitter({
    refreshDetail: async () => {
      refreshCount += 1;
    },
    setSubmitting: (isSubmitting) => {
      submittingStates.push(isSubmitting);
    },
    submitContact: async (payload) => {
      submittedPayload = payload;
    },
  });
  const contactSubmitResult = await contactSubmitter(
    buildBillingContactEventRequest({
      payerId: 14,
      channel: "sms",
      contactAction: "draft_prepared",
      messageText: "  Prosimy o sprawdzenie rozliczenia.  ",
      noteText: "",
      organizationId: "42",
    }),
  );
  assert.equal(contactSubmitResult.status, "success");
  assert.deepEqual(submittedPayload, {
    payer_id: 14,
    channel: "sms",
    contact_action: "draft_prepared",
    message_text: "Prosimy o sprawdzenie rozliczenia.",
  });
  assert.equal(refreshCount, 1);
  assert.deepEqual(submittingStates, [true, false]);

  const failingContactSubmitter = createBillingContactEventSubmitter({
    refreshDetail: async () => {
      throw new Error("Refresh should not run after failed contact submit.");
    },
    setSubmitting: () => {},
    submitContact: async () => {
      throw new ApiError("Backend odmówił", 500);
    },
  });
  const failingContactResult = await failingContactSubmitter(
    buildBillingContactEventRequest({
      payerId: 14,
      channel: "phone",
      contactAction: "contact_logged",
      messageText: "",
      noteText: "Rozmowa.",
      organizationId: "42",
    }),
  );
  assert.equal(failingContactResult.status, "error");
  assert.equal(failingContactResult.errorState.title, "Backend nie zapisał kontaktu");

  refreshCount = 0;
  submittingStates = [];
  submittedPayload = null;
  const nextStepSubmitter = createBillingNextStepSubmitter({
    refreshDetail: async () => {
      refreshCount += 1;
    },
    setSubmitting: (isSubmitting) => {
      submittingStates.push(isSubmitting);
    },
    submitNextStep: async (payload) => {
      submittedPayload = payload;
    },
  });
  const nextStepSubmitResult = await nextStepSubmitter(
    buildBillingNextStepRequest({
      targetType: "payer",
      targetId: 14,
      stepType: "call",
      eventAction: "planned",
      title: "  Zadzwonić w sprawie rozliczenia  ",
      noteText: "",
      organizationId: "42",
    }),
  );
  assert.equal(nextStepSubmitResult.status, "success");
  assert.deepEqual(submittedPayload, {
    target_type: "payer",
    target_id: 14,
    step_type: "call",
    event_action: "planned",
    title: "Zadzwonić w sprawie rozliczenia",
  });
  assert.equal(refreshCount, 1);
  assert.deepEqual(submittingStates, [true, false]);

  const failingNextStepSubmitter = createBillingNextStepSubmitter({
    refreshDetail: async () => {
      throw new Error("Refresh should not run after failed next step submit.");
    },
    setSubmitting: () => {},
    submitNextStep: async () => {
      throw new ApiError("Backend odmówił", 500);
    },
  });
  const failingNextStepResult = await failingNextStepSubmitter(
    buildBillingNextStepRequest({
      targetType: "payer",
      targetId: 14,
      stepType: "call",
      eventAction: "planned",
      title: "Zadzwonić",
      noteText: "",
      organizationId: "42",
    }),
  );
  assert.equal(failingNextStepResult.status, "error");
  assert.equal(failingNextStepResult.errorState.title, "Backend nie zapisał kroku");

  refreshCount = 0;
  submittingStates = [];
  submittedPayload = null;
  const reviewSubmitter = createBillingPaymentReviewStatusSubmitter({
    refreshStatus: async () => {
      refreshCount += 1;
    },
    setSubmitting: (isSubmitting) => {
      submittingStates.push(isSubmitting);
    },
    submitStatus: async (payload) => {
      submittedPayload = payload;
    },
  });
  const reviewSubmitResult = await reviewSubmitter(buildBillingPaymentReviewStatusRequest("needs_review", "  Sprawdzic tytul.  ", "42"));
  assert.equal(reviewSubmitResult.status, "success");
  assert.deepEqual(submittedPayload, { status: "needs_review", note_text: "Sprawdzic tytul." });
  assert.equal(refreshCount, 1);
  assert.deepEqual(submittingStates, [true, false]);

  const failingReviewSubmitter = createBillingPaymentReviewStatusSubmitter({
    refreshStatus: async () => {
      throw new Error("Refresh should not run after failed review status submit.");
    },
    setSubmitting: () => {},
    submitStatus: async () => {
      throw new ApiError("Backend odmówił", 500);
    },
  });
  const failingReviewResult = await failingReviewSubmitter(buildBillingPaymentReviewStatusRequest("checked", "", "42"));
  assert.equal(failingReviewResult.status, "error");
  assert.equal(failingReviewResult.errorState.title, "Backend nie zapisał statusu");

  const requestedUrls = [];
  await withMockedFetch(
    async (url, options) => {
      requestedUrls.push(url);
      assert.equal(options.method, "GET");
      if (url.startsWith(`/api${BILLING_BALANCES_ENDPOINT}`)) {
        return jsonResponse(200, [makeBalance()]);
      }
      if (url.startsWith(`/api${billingPayerNoteEndpoint(14)}`)) {
        return jsonResponse(200, [payerNotes[0]]);
      }
      if (url.startsWith(`/api${BILLING_CONTACT_EVENTS_ENDPOINT}`)) {
        return jsonResponse(200, contactEventsPayload);
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
      if (url.startsWith(`/api${BILLING_PAYMENT_REVIEW_STATUSES_ENDPOINT}`)) {
        return jsonResponse(200, paymentReviewStatusesPayload);
      }
      if (url.startsWith(`/api${BILLING_WORK_QUEUE_EVENTS_ENDPOINT}`)) {
        return jsonResponse(200, workQueueEventsPayload);
      }
      if (url.startsWith(`/api${BILLING_NEXT_STEP_EVENTS_ENDPOINT}`)) {
        return jsonResponse(200, nextStepEventsPayload);
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
      const [
        balancesPayload,
        payersPayload,
        studentsPayload,
        chargesPayload,
        notesPayload,
        contactEventsListPayload,
        matchesPayload,
        transactionsPayload,
        reviewStatusesPayload,
        workQueueEventsListPayload,
        nextStepEventsListPayload,
        invoicesPayload,
        contractorsPayload,
        workItemsPayload,
      ] = await Promise.all([
        api.ledgerBalances(query),
        api.billingPayers(query),
        api.billingStudents(query),
        api.billingCharges(withActiveOrganizationQuery("42", { limit: 100 })),
        api.billingPayerNotes(14, withActiveOrganizationQuery("42", { limit: 100 })),
        api.billingContactEvents(withActiveOrganizationQuery("42", { payer_id: 14, limit: 50 })),
        api.billingLedgerMatches(withActiveOrganizationQuery("42", { limit: 1000 })),
        api.billingTransactions(withActiveOrganizationQuery("42", { limit: 1000 })),
        api.billingPaymentReviewStatuses(withActiveOrganizationQuery("42", { limit: 1000 })),
        api.billingWorkQueueEvents(withActiveOrganizationQuery("42", { limit: 1000 })),
        api.billingNextStepEvents(withActiveOrganizationQuery("42", { limit: 1000 })),
        api.invoices(query),
        api.contractors(query),
        api.workItems(workItemsQuery),
      ]);
      assert.equal(readBillingBalances(balancesPayload).length, 1);
      assert.equal(readBillingPayers(payersPayload).length, 1);
      assert.equal(readBillingStudents(studentsPayload).length, 1);
      assert.equal(readBillingCharges(chargesPayload).length, 1);
      assert.equal(readBillingPayerNotes(notesPayload).length, 1);
      assert.equal(readBillingContactEvents(contactEventsListPayload).events.length, 4);
      assert.equal(readBillingPaymentMatches(matchesPayload).length, 1);
      assert.equal(readBillingTransactions(transactionsPayload).length, 1);
      assert.equal(readBillingPaymentReviewStatuses(reviewStatusesPayload).statuses.length, 2);
      assert.equal(readBillingWorkQueueEvents(workQueueEventsListPayload).events.length, 1);
      assert.equal(readBillingNextStepEvents(nextStepEventsListPayload).events.length, 3);
      assert.equal(readBillingInvoices(invoicesPayload).length, 1);
      assert.equal(Array.isArray(contractorsPayload), true);
      assert.equal(Array.isArray(workItemsPayload), true);
    },
  );

  assert.ok(requestedUrls.every((url) => url.includes("organization_id=42")));
  assert.ok(requestedUrls.some((url) => url.includes("/api/billing/charges") && url.includes("limit=100")));
  assert.ok(requestedUrls.some((url) => url.includes("/api/billing/payers/14/notes") && url.includes("limit=100")));
  assert.ok(requestedUrls.some((url) => url.includes("/api/billing/contact-events") && url.includes("payer_id=14") && url.includes("limit=50")));
  assert.ok(requestedUrls.some((url) => url.includes("/api/billing/ledger/matches") && url.includes("limit=1000")));
  assert.ok(requestedUrls.some((url) => url.includes("/api/billing/transactions") && url.includes("limit=1000")));
  assert.ok(requestedUrls.some((url) => url.includes("/api/billing/payment-review-statuses") && url.includes("limit=1000")));
  assert.ok(requestedUrls.some((url) => url.includes("/api/billing/work-queue/events") && url.includes("limit=1000")));
  assert.ok(requestedUrls.some((url) => url.includes("/api/billing/next-step-events") && url.includes("limit=1000")));
  assert.ok(requestedUrls.some((url) => url.includes("/api/work-items") && url.includes("only_open=1") && url.includes("limit=100")));

  console.log("Billing regression tests passed.");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
