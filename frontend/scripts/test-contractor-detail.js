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
  CONTRACTOR_DETAIL_CREATE_ENABLED,
  CONTRACTOR_DETAIL_DELETE_ENABLED,
  CONTRACTOR_DETAIL_EDIT_ENABLED,
  CONTRACTOR_DETAIL_ENDPOINT_PREFIX,
  CONTRACTOR_DETAIL_IMPORT_ENABLED,
  CONTRACTOR_DETAIL_ORGANIZATION_REQUIRED_DESCRIPTION,
  CONTRACTOR_DETAIL_ORGANIZATION_REQUIRED_TITLE,
  CONTRACTOR_DETAIL_PIPELINE_ENABLED,
  CONTRACTOR_DETAIL_READ_ONLY,
  CONTRACTOR_NOTE_ENDPOINT_SUFFIX,
  CONTRACTOR_NOTE_MAX_LENGTH,
  buildContractorDetailFacts,
  buildContractorDocumentRows,
  buildContractorInvoiceRows,
  buildContractorNoteRequest,
  buildContractorNoteRows,
  buildContractorRelationshipSummary,
  buildContractorTaskRows,
  buildContractorWorkItemRows,
  canRenderContractorDetail,
  canUseContractorDetailOrganizationScope,
  contractorNoteEndpoint,
  createContractorNoteSubmitter,
  enrichContractorDetailWithWorkItems,
  getContractorDetailErrorState,
  getContractorDetailTitle,
  getContractorNoteErrorState,
  getContractorTypeLabel,
  isContractorDetailEmpty,
  readContractorDetail,
  readContractorNote,
  safeContractorText,
} = require("../src/modules/crm/contractorDetailModel.ts");

function makeDetail(overrides = {}) {
  return {
    contractor: {
      contractor_id: 31,
      name: "Karta Kamdata",
      nip: "1234567890",
      email: "kontakt@example.test",
      phone: "500600700",
      is_new: 1,
      last_invoice_date: "2099-04-10",
      last_invoice_number: "FV/10/2099",
      invoice_count: 2,
      notes: "Klient obslugiwany w standardowym procesie.",
      organization_name: "CASI",
      organization_slug: "casi",
      created_at: "2099-04-01T08:00",
      updated_at: "2099-04-12T12:30",
    },
    invoices: [
      {
        invoice_id: 501,
        invoice_number: "FV/501/2099",
        status: "weryfikacja",
        gross_amount: 1234.5,
        currency: "PLN",
        issue_date: "2099-04-09",
      },
    ],
    linked_tasks: [
      {
        task_id: 9001,
        title: "Sprawdz umowe kontrahenta",
        status: "open",
        due_at: "2099-04-15T10:00",
      },
    ],
    notes: [
      {
        contractor_note_id: 701,
        contractor_id: 31,
        organization_id: 42,
        author_user_id: 7,
        author_user_name: "Operator CRM",
        note_text: "Pierwsza notatka CRM.",
        created_at: "2099-04-12T12:30",
      },
    ],
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

function collectStrings(value, output = []) {
  if (typeof value === "string") {
    output.push(value);
    return output;
  }

  if (Array.isArray(value)) {
    value.forEach((item) => collectStrings(item, output));
    return output;
  }

  if (value && typeof value === "object") {
    Object.values(value).forEach((item) => collectStrings(item, output));
  }

  return output;
}

const detail = readContractorDetail(makeDetail(), 31);
assert.equal(detail.contractor.contractor_id, 31);
assert.equal(detail.contractor.name, "Karta Kamdata");
assert.equal(detail.contractor.nip, "1234567890");
assert.equal(detail.contractor.email, "kontakt@example.test");
assert.equal(detail.invoices.length, 1);
assert.equal(detail.linkedTasks.length, 1);
assert.equal(detail.notes.length, 1);
assert.equal(detail.notes[0].noteText, "Pierwsza notatka CRM.");
assert.equal(detail.notes[0].authorLabel, "Operator CRM");
assert.equal(detail.notes[0].dateLabel, "2099-04-12 12:30");
assert.equal(detail.safeNotes, "Klient obslugiwany w standardowym procesie.");

const facts = buildContractorDetailFacts(detail);
assert.equal(facts.find((fact) => fact.label === "Status").value, "Nowy");
assert.equal(facts.find((fact) => fact.label === "NIP").value, "1234567890");
assert.equal(facts.find((fact) => fact.label === "Organizacja").value, "CASI");
assert.equal(facts.find((fact) => fact.label === "Faktury").value, "2");

const invoiceRows = buildContractorInvoiceRows(detail);
assert.equal(invoiceRows[0].numberLabel, "FV/501/2099");
assert.equal(invoiceRows[0].statusLabel, "weryfikacja");
assert.match(invoiceRows[0].amountLabel, /^1\s?234,50 PLN$|^1234,50 PLN$/);
assert.equal(invoiceRows[0].dateLabel, "2099-04-09");
assert.equal(invoiceRows[0].href, "/faktury/501");

const taskRows = buildContractorTaskRows(detail);
assert.equal(taskRows[0].titleLabel, "Sprawdz umowe kontrahenta");
assert.equal(taskRows[0].statusLabel, "open");
assert.equal(taskRows[0].dueLabel, "2099-04-15 10:00");
assert.equal(taskRows[0].href, "/asystent-szefa");

const enrichedDetail = enrichContractorDetailWithWorkItems(detail, [
  {
    work_item_id: 77,
    title: "Wyjasnic warunki platnosci",
    description: "Kontrahent czeka na doprecyzowanie rozliczenia.",
    status: "w_toku",
    priority_level: "wysoki",
    due_at: "2099-04-14T09:00",
    organization_name: "CASI",
    metadata: {
      contractor_id: 31,
      knowledge_document_ids: [88],
      document_title: "Umowa ramowa Kamdata",
      document_folder: "Umowy",
      document_context: "Dokument potrzebny do oceny warunkow platnosci.",
    },
  },
  {
    work_item_id: 78,
    title: "Sprawa innego kontrahenta",
    status: "w_toku",
    priority_level: "wysoki",
    metadata: {
      contractor_id: 999,
      knowledge_document_ids: [99],
      document_title: "Nie powinno byc widoczne",
    },
  },
]);
const workItemRows = buildContractorWorkItemRows(enrichedDetail);
assert.equal(workItemRows.length, 1);
assert.equal(workItemRows[0].titleLabel, "Wyjasnic warunki platnosci");
assert.equal(workItemRows[0].href, "/work-items/77");
assert.equal(workItemRows[0].priorityLabel, "Wysoki");
const documentRows = buildContractorDocumentRows(enrichedDetail);
assert.equal(documentRows.length, 1);
assert.equal(documentRows[0].titleLabel, "Umowa ramowa Kamdata");
assert.equal(documentRows[0].href, "/dokumenty/88");
assert.equal(documentRows[0].contextLabel, "Dokument potrzebny do oceny warunkow platnosci.");
const summary = buildContractorRelationshipSummary(enrichedDetail);
assert.equal(summary.activeWorkItemsLabel, "1 spraw");
assert.equal(summary.invoicesLabel, "1 faktur");
assert.equal(summary.notesLabel, "1 notatek");
assert.equal(summary.documentsLabel, "1 dokumentow");
assert.match(summary.riskLabel, /otwartych spraw/);

const noteRows = buildContractorNoteRows(detail);
assert.equal(noteRows[0].id, "701");
assert.equal(noteRows[0].contractorId, 31);
assert.equal(noteRows[0].organizationId, 42);
assert.equal(noteRows[0].authorUserId, 7);

const unsafeDetail = readContractorDetail(
  makeDetail({
    contractor: {
      ...makeDetail().contractor,
      name: "postgres://secret-token@example.test/db",
      email: "DATABASE_URL=postgres://token",
      phone: "C:\\Users\\erykl\\private\\phone.txt",
      notes: "password=super-secret",
    },
    invoices: [
      {
        invoice_id: 502,
        invoice_number: "data/magazyn/hidden.pdf",
        status: "secret_status",
        gross_amount: 10,
        currency: "PLN",
      },
    ],
    linked_tasks: [
      {
        task_id: 9002,
        title: "token do systemu",
        status: "open",
      },
    ],
    notes: [
      {
        contractor_note_id: 702,
        contractor_id: 31,
        organization_id: 42,
        author_user_name: "token debug",
        note_text: "C:\\Users\\erykl\\private\\note.txt",
        created_at: "2099-04-13T09:00",
      },
    ],
  }),
  31,
);
const unsafeStrings = collectStrings({
  unsafeDetail,
  facts: buildContractorDetailFacts(unsafeDetail),
  invoiceRows: buildContractorInvoiceRows(unsafeDetail),
  taskRows: buildContractorTaskRows(unsafeDetail),
  workItemRows: buildContractorWorkItemRows(unsafeDetail),
  documentRows: buildContractorDocumentRows(unsafeDetail),
  summary: buildContractorRelationshipSummary(unsafeDetail),
});
assert.equal(unsafeStrings.some((value) => /postgres:\/\//i.test(value)), false);
assert.equal(unsafeStrings.some((value) => /database_url/i.test(value)), false);
assert.equal(unsafeStrings.some((value) => /C:\\Users\\/i.test(value)), false);
assert.equal(unsafeStrings.some((value) => /data\/magazyn/i.test(value)), false);
assert.equal(unsafeStrings.some((value) => /password=/i.test(value)), false);
assert.equal(unsafeStrings.some((value) => /token/i.test(value)), false);

assert.equal(safeContractorText("C:\\Users\\erykl\\sekret.txt", "ukryte"), "ukryte");
assert.equal(safeContractorText("postgres://secret@example.test/db", "ukryte"), "ukryte");
assert.equal(safeContractorText("Normalna nazwa", "ukryte"), "Normalna nazwa");

assert.equal(contractorNoteEndpoint(31), `${CONTRACTOR_DETAIL_ENDPOINT_PREFIX}/31${CONTRACTOR_NOTE_ENDPOINT_SUFFIX}`);
assert.equal(CONTRACTOR_NOTE_ENDPOINT_SUFFIX, "/notes");
assert.equal(CONTRACTOR_NOTE_MAX_LENGTH, 2000);
assert.deepEqual(buildContractorNoteRequest("  Krotka notatka operatora  ", "42"), {
  ok: true,
  payload: {
    note_text: "Krotka notatka operatora",
  },
});
assert.equal(buildContractorNoteRequest("   ", "42").ok, false);
assert.equal(buildContractorNoteRequest("Notatka", null).ok, false);
assert.equal(buildContractorNoteRequest("x".repeat(CONTRACTOR_NOTE_MAX_LENGTH + 1), "42").ok, false);
assert.equal(readContractorNote({ contractor_note_id: 9, note_text: "Notatka" }).noteText, "Notatka");
assert.throws(() => readContractorNote([]), ApiContractError);

assert.equal(canUseContractorDetailOrganizationScope("3"), true);
assert.equal(canUseContractorDetailOrganizationScope(3), true);
assert.equal(canUseContractorDetailOrganizationScope(null), false);
assert.equal(canUseContractorDetailOrganizationScope(""), false);
assert.equal(canRenderContractorDetail("ready", detail), true);
assert.equal(canRenderContractorDetail("loading", detail), false);
assert.equal(isContractorDetailEmpty("ready", null), true);
assert.equal(getContractorDetailTitle(null, 9), "Kontrahent #9");
assert.equal(getContractorDetailTitle(detail, 31), "Karta Kamdata");
assert.equal(getContractorTypeLabel(detail.contractor), "Nowy kontrahent");

assert.equal(CONTRACTOR_DETAIL_ENDPOINT_PREFIX, "/contractors");
assert.equal(CONTRACTOR_DETAIL_READ_ONLY, true);
assert.equal(CONTRACTOR_DETAIL_CREATE_ENABLED, false);
assert.equal(CONTRACTOR_DETAIL_EDIT_ENABLED, false);
assert.equal(CONTRACTOR_DETAIL_DELETE_ENABLED, false);
assert.equal(CONTRACTOR_DETAIL_IMPORT_ENABLED, false);
assert.equal(CONTRACTOR_DETAIL_PIPELINE_ENABLED, false);
assert.equal(CONTRACTOR_DETAIL_ORGANIZATION_REQUIRED_TITLE, "Wybierz organizacje, aby zobaczyc kontrahenta");
assert.match(CONTRACTOR_DETAIL_ORGANIZATION_REQUIRED_DESCRIPTION, /topbarze/);

assert.throws(() => readContractorDetail([], 31), ApiContractError);
assert.throws(() => readContractorDetail({ contractor: { name: "Brak ID" } }, 31), ApiContractError);
assert.throws(() => readContractorDetail(makeDetail({ contractor: { ...makeDetail().contractor, contractor_id: 32 } }), 31), ApiContractError);

assert.equal(getContractorDetailErrorState(new ApiError("Brak sesji", 401, {})).status, "unauthenticated");
assert.equal(getContractorDetailErrorState(new ApiError("Brak uprawnien", 403, {})).status, "forbidden");
assert.equal(getContractorDetailErrorState(new ApiError("Brak", 404, {})).title, "Nie znaleziono kontrahenta");
assert.equal(getContractorDetailErrorState(new ApiError("Backend padl", 500, {})).status, "server-error");
assert.equal(getContractorDetailErrorState(new ApiContractError("/contractors/31", {})).title, "Niepoprawny format kontrahenta");
assert.equal(getContractorNoteErrorState(new ApiError("Brak sesji", 401, {})).status, "unauthenticated");
assert.equal(getContractorNoteErrorState(new ApiError("Brak uprawnien", 403, {})).status, "forbidden");
assert.equal(getContractorNoteErrorState(new ApiError("Nie ma", 404, {})).title, "Nie znaleziono kontrahenta");
assert.equal(getContractorNoteErrorState(new ApiError("Backend padl", 500, {})).status, "server-error");

async function main() {
  await withMockedFetch(
    async (url, options) => {
      assert.equal(url, `/api${CONTRACTOR_DETAIL_ENDPOINT_PREFIX}/31?organization_id=42`);
      assert.equal(options.method, "GET");
      assert.equal(options.body, undefined);
      return jsonResponse(200, makeDetail());
    },
    async () => {
      const payload = await api.contractorDetail(31, withActiveOrganizationQuery("42"));
      const nextDetail = readContractorDetail(payload, 31);
      assert.equal(nextDetail.contractor.contractor_id, 31);
      assert.equal(nextDetail.invoices.length, 1);
    },
  );

  await withMockedFetch(
    async (url, options) => {
      assert.equal(url, `/api${contractorNoteEndpoint(31)}?organization_id=42`);
      assert.equal(options.method, "POST");
      assert.deepEqual(JSON.parse(options.body), { note_text: "Notatka z UI" });
      return jsonResponse(201, {
        contractor_note_id: 901,
        contractor_id: 31,
        organization_id: 42,
        author_user_id: 1,
        note_text: "Notatka z UI",
        created_at: "2099-04-12T13:00",
      });
    },
    async () => {
      const payload = await api.addContractorNote(31, "Notatka z UI", "42");
      const note = readContractorNote(payload);
      assert.equal(note.noteText, "Notatka z UI");
      assert.equal(note.contractorId, 31);
      assert.equal(note.organizationId, 42);
    },
  );

  let refreshCount = 0;
  let submitCount = 0;
  let submittingState = false;
  const submitter = createContractorNoteSubmitter({
    refreshDetail: async () => {
      refreshCount += 1;
    },
    setSubmitting: (value) => {
      submittingState = value;
    },
    submitNote: async (payload) => {
      submitCount += 1;
      assert.deepEqual(payload, { note_text: "Notatka po backendu" });
    },
  });
  const submitResult = await submitter(buildContractorNoteRequest("Notatka po backendu", "42"));
  assert.equal(submitResult.status, "success");
  assert.equal(submitCount, 1);
  assert.equal(refreshCount, 1);
  assert.equal(submittingState, false);

  const blockedResult = await createContractorNoteSubmitter({
    refreshDetail: async () => {
      throw new Error("refresh should not run");
    },
    setSubmitting: () => {
      throw new Error("submitting should not change");
    },
    submitNote: async () => {
      throw new Error("submit should not run");
    },
  })(buildContractorNoteRequest(" ", "42"));
  assert.equal(blockedResult.status, "blocked");

  const failedSubmitter = createContractorNoteSubmitter({
    refreshDetail: async () => {
      throw new Error("refresh should not run after failed submit");
    },
    setSubmitting: () => {},
    submitNote: async () => {
      throw new ApiError("Backend rejected note", 400, {});
    },
  });
  const failedResult = await failedSubmitter(buildContractorNoteRequest("Nie zapisuj bez backendu", "42"));
  assert.equal(failedResult.status, "error");
  assert.equal(failedResult.errorState.title, "Blad API (400)");

  console.log("Contractor detail regression tests passed.");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
