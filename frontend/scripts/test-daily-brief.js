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

const {
  DAILY_BRIEF_ORGANIZATION_REQUIRED_DESCRIPTION,
  DAILY_BRIEF_ORGANIZATION_REQUIRED_TITLE,
  DAILY_BRIEF_READ_ONLY,
  DAILY_BRIEF_REFRESH_LABEL,
  DAILY_BRIEF_SECTION_LABELS,
  DAILY_BRIEF_WRITE_ACTIONS,
  buildDailyBrief,
  canUseDailyBriefOrganizationScope,
  hasDailyBriefWriteActions,
  hasUnsafeTechnicalText,
  isDailyBriefEmpty,
  sourceState,
} = require("../src/modules/daily-brief/dailyBriefModel.ts");

function makeSnapshot(overrides = {}) {
  return {
    dashboard: {
      cards: {
        nowe_faktury: 2,
        do_weryfikacji: 3,
        podejrzenia_duplikatow: 1,
        pewne_duplikaty: 0,
        nowi_kontrahenci: 1,
        aktywne_przypomnienia: 1,
      },
      operational_alerts: [
        {
          severity: "danger",
          category: "invoices",
          title: "Faktury po terminie",
          description: "Wymagaja decyzji dzisiaj.",
        },
      ],
      active_reminders: [
        {
          task_id: 70,
          title: "Sprawdz umowe",
          task_type: "review",
          priority: "niski",
          due_at: "2026-07-03T12:00:00",
        },
      ],
      knowledge_queue: [],
      recent_events: [],
    },
    taskFocus: {
      generated_at: "2026-07-03T09:00:00",
      available_views: ["do_decyzji"],
      views: [
        {
          code: "do_decyzji",
          label: "Do decyzji",
          count: 1,
          items: [
            {
              task_id: 501,
              title: "Decyzja o umowie",
              description: "Wymaga akceptacji managera",
              status: "open",
              priority: "wysoki",
              due_at: "2026-07-03T15:00:00",
              organization_name: "CASI",
              owner_user_name: "Eryk",
              linked_entity_count: 1,
            },
          ],
        },
      ],
    },
    workItems: [
      {
        work_item_id: 91,
        title: "SLA klienta",
        description: "Sprawa wymaga odpowiedzi",
        status: "w_toku",
        priority_level: "krytyczny",
        priority_score: 94,
        source_type: "support",
        assigned_user_name: "Operator",
        due_at: "2026-07-03T13:00:00",
        sla_stage: "escalated",
        sla_state_label: "SLA po terminie",
        is_closed: false,
        is_sla_overdue: true,
      },
    ],
    invoiceInbox: {
      summary: { total_open_count: 2, generated_at: "2026-07-03T09:00:00" },
      sections: {
        overdue: {
          title: "Faktury po terminie",
          description: "Wymagaja pilnej weryfikacji.",
          count: 1,
          items: [
            {
              invoice_id: 9,
              invoice_number: "FV/9/2026",
              issuer_name: "Karta Kamdta",
              gross_amount: 122.24,
              currency: "PLN",
              status: "preview-ready",
              flag_reason: "Termin weryfikacji minal.",
            },
          ],
        },
      },
    },
    billingBalances: [
      {
        billing_payer_id: 11,
        display_name: "Rodzic Alfa",
        contact_phone: "123",
        is_active: true,
        total_charges: 400,
        total_matches: 100,
        balance_due: 300,
        matched_payment_count: 1,
      },
    ],
    contractors: [
      {
        contractor_id: 13,
        name: "Nowy Kontrahent",
        is_new: true,
        invoice_count: 1,
        last_invoice_number: "FV/9/2026",
        last_invoice_date: "2026-07-02",
      },
    ],
    documents: [
      {
        knowledge_document_id: 7,
        title: "Umowa do sprawdzenia",
        file_name: "umowa.pdf",
        lifecycle_status: "active",
        processing_status: "ready",
        business_status: "do_sprawdzenia",
        business_status_label: "Do sprawdzenia",
        workflow_status: "review",
        workflow_status_label: "Review",
        library_path_label: "Umowy",
        current_version_number: 1,
        updated_at: "2026-07-03",
        storage_key: "data/magazyn/private" ,
      },
    ],
    sourceStates: [sourceState("dashboard", "ready"), sourceState("workItems", "ready")],
    ...overrides,
  };
}

const snapshot = makeSnapshot();
const { sections, kpis } = buildDailyBrief(snapshot);

assert.equal(DAILY_BRIEF_READ_ONLY, true);
assert.equal(hasDailyBriefWriteActions(), false);
assert.deepEqual(DAILY_BRIEF_WRITE_ACTIONS, []);
assert.equal(canUseDailyBriefOrganizationScope("1"), true);
assert.equal(canUseDailyBriefOrganizationScope(null), false);
assert.equal(DAILY_BRIEF_ORGANIZATION_REQUIRED_TITLE, "Wybierz organizację, aby zobaczyć Pulpit dnia");
assert.match(DAILY_BRIEF_ORGANIZATION_REQUIRED_DESCRIPTION, /organizację/i);
assert.equal(DAILY_BRIEF_REFRESH_LABEL, "Odśwież");
assert.deepEqual(DAILY_BRIEF_SECTION_LABELS, {
  top: "Najważniejsze dziś",
  urgent: "Sprawy pilne",
  invoicesFinance: "Faktury i finanse",
  contractors: "Kontrahenci",
  documents: "Dokumenty",
  later: "Można odłożyć",
});

assert.ok(sections.top.length > 0, "top section should contain prioritized signals");
assert.equal(sections.top[0].title, "Faktury po terminie");
assert.ok(sections.top.length <= 7, "top section should stay compact");
assert.ok(sections.top.filter((item) => item.category === "invoices").length <= 2, "invoice signals should not dominate top section");
assert.ok(new Set(sections.top.map((item) => item.category)).size >= 3, "top section should mix operational categories");
assert.ok(sections.urgent.some((item) => item.source === "Sprawy"), "urgent section should include operational matters");
assert.ok(sections.urgent.some((item) => item.href === "/work-items/91"), "urgent work item should link to the case card");
assert.ok(sections.invoicesFinance.some((item) => item.href === "/faktury/9"), "invoice item should link to invoice detail");
assert.ok(sections.contractors.some((item) => item.href === "/crm/13"), "contractor item should link to contractor detail");
assert.ok(sections.documents.some((item) => item.href === "/dokumenty/7"), "document item should link to document detail");
assert.ok(sections.later.some((item) => item.source === "Pulpit"), "later section should include non-critical reminders");
assert.ok(kpis.criticalCount >= 1);
assert.ok(kpis.urgentCount >= 1);
assert.ok(kpis.invoiceCount >= 1);

const invoiceHeavySnapshot = makeSnapshot({
  dashboard: {
    ...snapshot.dashboard,
    operational_alerts: [
      { severity: "danger", category: "invoices", title: "Duplikaty wymagaja decyzji", description: "Pierwszy sygnal fakturowy." },
      { severity: "danger", category: "invoices", title: "Faktury czekaja na weryfikacje", description: "Drugi sygnal fakturowy." },
      { severity: "warning", category: "invoices", title: "Wyjatki w obiegu faktur", description: "Trzeci sygnal fakturowy." },
    ],
  },
  invoiceInbox: {
    summary: { total_open_count: 8 },
    sections: {
      duplicates: {
        title: "Duplikaty do decyzji",
        description: "Podobne faktury wymagaja spojrzenia.",
        count: 5,
        items: [
          { invoice_id: 101, invoice_number: "FV/101", issuer_name: "A", duplicate_type: "suspected", gross_amount: 10, currency: "PLN" },
          { invoice_id: 102, invoice_number: "FV/102", issuer_name: "B", duplicate_type: "suspected", gross_amount: 20, currency: "PLN" },
          { invoice_id: 103, invoice_number: "FV/103", issuer_name: "C", duplicate_type: "suspected", gross_amount: 30, currency: "PLN" },
        ],
      },
    },
  },
});
const invoiceHeavyTop = buildDailyBrief(invoiceHeavySnapshot).sections.top;
assert.ok(invoiceHeavyTop.filter((item) => item.category === "invoices").length <= 2);
assert.ok(invoiceHeavyTop.some((item) => item.category === "tasks"));
assert.ok(invoiceHeavyTop.some((item) => item.category === "crm"));
assert.ok(invoiceHeavyTop.some((item) => item.category === "documents"));

const lowPrioritySnapshot = makeSnapshot({
  dashboard: { cards: snapshot.dashboard.cards, operational_alerts: [], active_reminders: [], knowledge_queue: [], recent_events: [] },
  taskFocus: { generated_at: "2026-07-03", available_views: [], views: [] },
  workItems: [
    {
      work_item_id: 777,
      title: "Spokojna sprawa bez terminu",
      description: "Mo?na do niej wr?ci? p??niej",
      status: "nowe",
      priority_level: "niski",
      source_type: "manual",
      assigned_user_name: "Operator",
      sla_stage: "normal",
      sla_state_label: "W normie SLA",
      is_closed: false,
    },
  ],
  contractors: [
    {
      contractor_id: 88,
      name: "Stabilny Kontrahent",
      email: "kontakt@example.test",
      is_new: false,
      invoice_count: 2,
      last_invoice_number: "FV/88",
      last_invoice_date: "2026-07-01",
    },
  ],
  documents: [
    {
      knowledge_document_id: 66,
      title: "Dokument do spokojnego przejrzenia",
      lifecycle_status: "active",
      processing_status: "ready",
      business_status: "gotowy",
      business_status_label: "Gotowy",
      workflow_status: "ready",
      workflow_status_label: "Gotowy",
      library_path_label: "Procedury",
      current_version_number: 1,
      official_version_number: 1,
      updated_at: "2026-07-01",
    },
  ],
  invoiceInbox: { summary: { total_open_count: 0 }, sections: {} },
  billingBalances: [],
});
const lowPriorityLater = buildDailyBrief(lowPrioritySnapshot).sections.later;
assert.ok(lowPriorityLater.some((item) => item.category === "tasks"), "low urgency work item should appear in later section");
assert.ok(lowPriorityLater.some((item) => item.href === "/work-items/777"), "low urgency work item should link to the case card");
assert.ok(lowPriorityLater.some((item) => item.category === "crm"), "stable contractor should appear in later section");
assert.ok(lowPriorityLater.some((item) => item.category === "documents"), "calm document should appear in later section");

const allItems = Object.values(sections).flat();
assert.equal(hasUnsafeTechnicalText(allItems), false, "daily brief must not leak technical storage paths");
assert.ok(allItems.every((item) => ["/pulpit", "/asystent-szefa", "/work-items", "/faktury", "/rozliczenia", "/crm", "/dokumenty"].some((pathPrefix) => item.href === pathPrefix || item.href.startsWith(`${pathPrefix}/`))));
assert.ok(sections.top.every((item) => item.title && item.description && item.source && item.href), "top items should have title, reason, category and link");
assert.equal(allItems.some((item) => item.source === "Work Items"), false, "visible item categories should avoid technical module names");

const emptySnapshot = makeSnapshot({
  dashboard: { cards: snapshot.dashboard.cards, operational_alerts: [], active_reminders: [], knowledge_queue: [], recent_events: [] },
  taskFocus: { generated_at: "2026-07-03", available_views: [], views: [] },
  workItems: [],
  invoiceInbox: { summary: { total_open_count: 0 }, sections: {} },
  billingBalances: [],
  contractors: [],
  documents: [],
});
assert.equal(isDailyBriefEmpty("ready", emptySnapshot), true);
assert.equal(isDailyBriefEmpty("loading", emptySnapshot), false);

console.log("Pulpit dnia model tests passed.");
