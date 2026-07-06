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

const { ApiContractError, ApiError, AUTH_REQUIRED_EVENT, api, readInvoiceVerificationInbox } = require("../src/lib/api.ts");
const { withActiveOrganizationQuery } = require("../src/context/organizationContextModel.ts");
const {
  invoiceApi,
  invoiceActionEndpoint,
  invoiceCommentEndpoint,
  invoiceDetailEndpoint,
  readInvoiceActionResult,
  readInvoiceComment,
  readInvoiceDetail,
} = require("../src/modules/invoices/api.ts");
const { buildInvoiceDecisionActions } = require("../src/modules/invoices/decisionModel.ts");
const {
  INVOICE_ACTION_DEFINITIONS,
  INVOICE_COMMENT_MAX_LENGTH,
  INVOICE_COMMENT_MUTATION_METHODS,
  INVOICE_DETAIL_MUTATION_METHODS,
  INVOICE_DETAIL_ORGANIZATION_REQUIRED_DESCRIPTION,
  INVOICE_DETAIL_ORGANIZATION_REQUIRED_TITLE,
  INVOICE_INBOX_ENDPOINT,
  INVOICE_INBOX_MUTATION_METHODS,
  INVOICES_ORGANIZATION_REQUIRED_DESCRIPTION,
  INVOICES_ORGANIZATION_REQUIRED_TITLE,
  buildInvoiceActionConfirmation,
  buildInvoiceActionRequest,
  buildInvoiceBusinessSignals,
  buildInvoiceCenterSummary,
  buildInvoiceCommentEvents,
  buildInvoiceCommentRequest,
  buildInvoiceContractorContext,
  buildInvoiceDocumentTraceItems,
  buildInvoiceDetailEvents,
  buildInvoiceDetailFacts,
  buildInvoiceHistoryEvents,
  buildInvoiceRelatedDocumentRows,
  buildInvoiceRelatedTaskRows,
  buildInvoiceRelatedWorkItemRows,
  canUseInvoicesOrganizationScope,
  canRenderInvoiceDetailData,
  createInvoiceActionSubmitter,
  createInvoiceCommentSubmitter,
  flattenInboxItems,
  formatInvoiceAmount,
  getInvoiceDetailHref,
  getInvoiceActionDefinition,
  getInvoiceActionErrorState,
  getInvoiceCommentErrorState,
  getInvoiceDetailErrorState,
  getInvoiceDetailTitle,
  getInboxSections,
  getInvoicesErrorState,
  hasInvoiceInboxData,
  isInvoiceDetailEmpty,
  isInvoiceDetailReadOnly,
  isInvoiceInboxEmpty,
  isInvoiceInboxReadOnly,
  isUnsafeTechnicalValue,
  readSafeDisplayString,
  requiresInvoiceActionConfirmation,
} = require("../src/modules/invoices/invoicesModel.ts");

function makeItem(overrides = {}) {
  return {
    invoice_id: 13,
    invoice_number: "FV/2026/04/13",
    issuer_name: "CASI Test Sp. z o.o.",
    source: "email",
    status: "Do weryfikacji",
    duplicate_type: "brak",
    gross_amount: 620.1,
    currency: "PLN",
    ...overrides,
  };
}

function makeInbox(items = [makeItem()]) {
  return {
    summary: {
      total_open_count: items.length,
      generated_at: "2026-04-30T09:00:00Z",
    },
    sections: {
      verification: {
        title: "Do weryfikacji",
        description: "Faktury wymagajace decyzji.",
        count: items.length,
        action_key: "status_verification",
        items,
      },
      duplicates: {
        title: "Duplikaty do decyzji",
        description: "Faktury z podejrzeniem duplikatu.",
        count: 0,
        action_key: "duplicate_review",
        items: [],
      },
    },
  };
}

function makeDetail(overrides = {}) {
  return {
    invoice: {
      id: 13,
      invoice_id: 13,
      invoice_number: "FV/2026/04/13",
      issuer_name: "CASI Test Sp. z o.o.",
      issuer_nip: "5250000000",
      gross_amount: 620.1,
      currency: "PLN",
      status: "weryfikacja",
      source: "email",
      workflow_state: "w_pracy",
      invoice_comment_count: 1,
      contractor_id: 14,
      contractor_email: "kontakt@casi.test",
      contractor_phone: "+48 500 100 200",
      contractor_is_new: false,
      contractor_notes: "Staly kontrahent wymagajacy doprecyzowania opisu kosztu.",
    },
    contractor: {
      contractor_id: 14,
      name: "CASI Test Sp. z o.o.",
      nip: "5250000000",
      email: "kontakt@casi.test",
      phone: "+48 500 100 200",
      is_new: false,
      notes: "Staly kontrahent.",
    },
    contractor_known_before: true,
    linked_tasks: [
      {
        task_id: 31,
        title: "Uzgodnic opis kosztu z wlascicielem",
        status: "w_toku",
        due_at: "2026-05-02",
      },
    ],
    document_intake_items: [
      {
        knowledge_document_id: 22,
        document_title: "Umowa serwisowa CASI",
        folder_name: "Umowy",
        status: "zaakceptowany",
      },
    ],
    comments: [
      {
        invoice_comment_id: 7,
        id: 7,
        created_by_user_name: "Operator",
        created_at: "2026-04-30",
        note_text: "Sprawdzono dane kontrahenta.",
      },
    ],
    history: [
      {
        id: 3,
        event_type: "Import",
        actor: "System",
        event_time: "2026-04-30",
        decision_reason: "Faktura trafila do inboxu.",
      },
      {
        id: 4,
        event_type: "invoice_comment_added",
        actor: "Operator",
        event_time: "2026-04-30",
        details: {
          note_text: "Pelna tresc komentarza nie powinna byc w historii.",
          invoice_comment_id: 7,
        },
      },
    ],
    document_trace: {
      file_name: "fv-13.pdf",
      storage_backend: "local",
      ocr_storage_key: "organizacje/casi/EMAIL/2026-04-30/fv-13_ocr.txt",
      ocr_confidence: 0.91,
    },
    source_trace: {
      source: "email",
      message_id: "msg-13",
    },
    workflow: {
      state_label: "W pracy",
    },
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

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((promiseResolve, promiseReject) => {
    resolve = promiseResolve;
    reject = promiseReject;
  });

  return { promise, reject, resolve };
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

async function main() {
const liveInbox = readInvoiceVerificationInbox(makeInbox());
assert.equal(flattenInboxItems(liveInbox).length, 1);
assert.equal(getInboxSections(liveInbox).length, 2);
assert.equal(hasInvoiceInboxData("ready", liveInbox), true);
assert.equal(isInvoiceInboxEmpty("ready", liveInbox), false);
assert.equal(formatInvoiceAmount(liveInbox.sections.verification.items[0]), "620,10 PLN");
assert.equal(getInvoiceDetailHref(liveInbox.sections.verification.items[0].invoice_id), "/faktury/13");
assert.equal(getInvoiceDetailHref(null), null);
assert.equal(getInvoiceDetailHref("   "), null);

const emptyInbox = readInvoiceVerificationInbox(makeInbox([]));
assert.equal(flattenInboxItems(emptyInbox).length, 0);
assert.equal(hasInvoiceInboxData("ready", emptyInbox), false);
assert.equal(isInvoiceInboxEmpty("ready", emptyInbox), true);

const invoiceDetail = readInvoiceDetail(makeDetail(), 13);
assert.equal(canRenderInvoiceDetailData("ready", invoiceDetail), true);
assert.equal(isInvoiceDetailEmpty("ready", invoiceDetail), false);
assert.equal(getInvoiceDetailTitle(invoiceDetail, 13), "FV/2026/04/13");
assert.equal(buildInvoiceDetailFacts(invoiceDetail.invoice).length, 8);
assert.equal(buildInvoiceDetailEvents(invoiceDetail).length, 3);
assert.equal(buildInvoiceHistoryEvents(invoiceDetail).length, 2);
assert.equal(buildInvoiceCommentEvents(invoiceDetail).length, 1);
assert.equal(buildInvoiceCommentEvents(invoiceDetail).find((item) => item.id === "comment-7").type, "Komentarz operatora");
assert.equal(buildInvoiceCommentEvents(invoiceDetail).find((item) => item.id === "comment-7").actor, "Operator");
assert.equal(
  buildInvoiceCommentEvents(invoiceDetail).find((item) => item.id === "comment-7").description,
  "Sprawdzono dane kontrahenta.",
);
assert.equal(
  buildInvoiceHistoryEvents(invoiceDetail).find((item) => item.id === "history-4").description,
  "Dodano komentarz operatora. Pełna treść jest w sekcji komentarzy.",
);
assert.equal(
  buildInvoiceHistoryEvents(invoiceDetail).some((item) => item.description.includes("Pelna tresc komentarza")),
  false,
);
const centerSummary = buildInvoiceCenterSummary(invoiceDetail);
assert.equal(centerSummary.amountLabel, "620,10 zł");
assert.equal(centerSummary.contractorLabel, "CASI Test Sp. z o.o.");
assert.equal(centerSummary.decisionLabel, "Wymaga spokojnej weryfikacji");
const contractorContext = buildInvoiceContractorContext(invoiceDetail);
assert.equal(contractorContext.href, "/crm/14");
assert.equal(contractorContext.contactLabel, "kontakt@casi.test · +48 500 100 200");
assert.equal(contractorContext.knownBeforeLabel, "Występował wcześniej w fakturach");
const relatedWorkItems = buildInvoiceRelatedWorkItemRows(invoiceDetail, [
  {
    work_item_id: 91,
    title: "Doprecyzowac opis faktury",
    status: "w_toku",
    priority_level: "wysoki",
    due_at: "2026-05-01",
    metadata: {
      invoice_id: 13,
      contractor_id: 14,
    },
  },
  {
    work_item_id: 92,
    title: "Inna sprawa",
    metadata: {
      invoice_id: 99,
    },
  },
]);
assert.equal(relatedWorkItems.length, 1);
assert.equal(relatedWorkItems[0].href, "/work-items/91");
assert.equal(buildInvoiceRelatedTaskRows(invoiceDetail)[0].href, "/asystent-szefa");
assert.equal(buildInvoiceRelatedDocumentRows(invoiceDetail)[0].href, "/dokumenty/22");
assert.equal(buildInvoiceBusinessSignals(invoiceDetail).some((signal) => signal.label === "Co teraz oznacza ta faktura"), true);
const traceItems = buildInvoiceDocumentTraceItems(invoiceDetail);
assert.equal(traceItems.find((item) => item.label === "OCR").value, "Ślad OCR dostępny");
assert.equal(traceItems.some((item) => String(item.value).includes("organizacje/casi")), false);
assert.equal(traceItems.some((item) => String(item.description).includes("storage")), false);
assert.equal(isUnsafeTechnicalValue("C:\\Users\\erykl\\plik.pdf"), true);
assert.equal(isUnsafeTechnicalValue("data/magazyn/faktura.pdf"), true);
assert.equal(readSafeDisplayString("C:\\Users\\erykl\\plik.pdf", "Ukryto sciezke"), "Ukryto sciezke");
assert.equal(canRenderInvoiceDetailData("unauthenticated", null), false);
assert.equal(isInvoiceDetailEmpty("ready", null), true);

assert.equal(Object.keys(INVOICE_ACTION_DEFINITIONS).length, 7);
assert.equal(getInvoiceActionDefinition("close").requiresReason, true);
assert.equal(getInvoiceActionDefinition("handoff").requiresHandoffTarget, true);
assert.equal(requiresInvoiceActionConfirmation("confirm-duplicate"), true);
assert.equal(requiresInvoiceActionConfirmation("reject-duplicate"), true);
assert.equal(requiresInvoiceActionConfirmation("close"), true);
assert.equal(requiresInvoiceActionConfirmation("undo-last"), true);
assert.equal(buildInvoiceActionConfirmation(invoiceDetail, "close").invoiceNumber, "FV/2026/04/13");
assert.equal(buildInvoiceActionConfirmation(invoiceDetail, "close").contractor, "CASI Test Sp. z o.o.");

const duplicateDecisionPreview = buildInvoiceDecisionActions(
  makeDetail({ invoice: { ...makeDetail().invoice, duplicate_type: "podejrzenie" } }),
);
assert.equal(duplicateDecisionPreview.find((item) => item.action === "confirm-duplicate").availability, "preview-ready");
assert.match(
  duplicateDecisionPreview.find((item) => item.action === "confirm-duplicate").reason,
  /Backend nadal musi ja potwierdzic/,
);
assert.equal(buildInvoiceDecisionActions(makeDetail()).find((item) => item.action === "handoff").availability, "blocked");
assert.deepEqual(buildInvoiceActionRequest("confirm-duplicate"), {
  ok: true,
  request: {
    action: "confirm-duplicate",
    payload: undefined,
  },
});
assert.deepEqual(buildInvoiceActionRequest("handoff", { handoffTarget: "Ksiegowosc", handoffNote: "Gotowe." }), {
  ok: true,
  request: {
    action: "handoff",
    payload: {
      handoff_target: "Ksiegowosc",
      handoff_note: "Gotowe.",
    },
  },
});
assert.equal(buildInvoiceActionRequest("close").ok, false);
assert.deepEqual(buildInvoiceActionRequest("close", { reason: "Rozliczona." }), {
  ok: true,
  request: {
    action: "close",
    payload: {
      reason: "Rozliczona.",
    },
  },
});
assert.deepEqual(buildInvoiceCommentRequest("  Krotka notatka operatora.  ", "42"), {
  ok: true,
  payload: {
    note_text: "Krotka notatka operatora.",
  },
});
assert.equal(buildInvoiceCommentRequest("   ", "42").ok, false);
assert.equal(buildInvoiceCommentRequest("Notatka", null).ok, false);
assert.equal(buildInvoiceCommentRequest("x".repeat(INVOICE_COMMENT_MAX_LENGTH + 1), "42").ok, false);

assert.equal(getInvoicesErrorState(new ApiError("Brak sesji", 401, {})).status, "unauthenticated");
assert.equal(getInvoicesErrorState(new ApiError("Brak uprawnien", 403, {})).status, "forbidden");
assert.equal(getInvoicesErrorState(new ApiError("Backend padl", 500, {})).status, "server-error");
assert.equal(getInvoiceDetailErrorState(new ApiError("Brak sesji", 401, {})).status, "unauthenticated");
assert.equal(getInvoiceDetailErrorState(new ApiError("Brak uprawnien", 403, {})).status, "forbidden");
assert.equal(getInvoiceDetailErrorState(new ApiError("Backend padl", 500, {})).status, "server-error");
assert.equal(getInvoiceActionErrorState(new ApiError("Brak sesji", 401, {})).status, "unauthenticated");
assert.equal(getInvoiceActionErrorState(new ApiError("Brak uprawnien", 403, {})).status, "forbidden");
assert.equal(getInvoiceActionErrorState(new ApiError("Backend padl", 500, {})).status, "server-error");
assert.equal(getInvoiceCommentErrorState(new ApiError("Brak sesji", 401, {})).status, "unauthenticated");
assert.equal(getInvoiceCommentErrorState(new ApiError("Brak uprawnien", 403, {})).status, "forbidden");
assert.equal(getInvoiceCommentErrorState(new ApiError("Backend padl", 500, {})).status, "server-error");

assert.throws(
  () => readInvoiceVerificationInbox({ summary: {}, sections: {} }),
  ApiContractError,
);
assert.equal(
  getInvoicesErrorState(new ApiContractError(INVOICE_INBOX_ENDPOINT, {})).title,
  "Niepoprawny format inboxu faktur",
);
assert.throws(() => readInvoiceDetail({ invoice: null }, 13), ApiContractError);
assert.equal(
  getInvoiceDetailErrorState(new ApiContractError(invoiceDetailEndpoint(13), {})).title,
  "Niepoprawny format szczegolow faktury",
);
assert.equal(readInvoiceActionResult(makeDetail().invoice, 13, "close").invoice_number, "FV/2026/04/13");
assert.throws(() => readInvoiceActionResult({ workflow_state: "zamknieta" }, 13, "close"), ApiContractError);
assert.equal(
  getInvoiceActionErrorState(new ApiContractError(invoiceActionEndpoint(13, "close"), {})).title,
  "Niepoprawny format odpowiedzi po akcji",
);
assert.equal(readInvoiceComment({ invoice_comment_id: 9, note_text: "Komentarz" }, 13).note_text, "Komentarz");
assert.throws(() => readInvoiceComment({ comment: "stary format" }, 13), ApiContractError);
assert.equal(
  getInvoiceCommentErrorState(new ApiContractError(invoiceCommentEndpoint(13), {})).title,
  "Niepoprawny format komentarza",
);

assert.equal(isInvoiceInboxReadOnly(), true);
assert.deepEqual(INVOICE_INBOX_MUTATION_METHODS, []);
assert.equal(isInvoiceDetailReadOnly(), true);
assert.deepEqual(INVOICE_DETAIL_MUTATION_METHODS, []);
assert.deepEqual(INVOICE_COMMENT_MUTATION_METHODS, ["POST"]);
assert.equal(INVOICES_ORGANIZATION_REQUIRED_TITLE, "Wybierz organizację, aby zobaczyć faktury");
assert.match(INVOICES_ORGANIZATION_REQUIRED_DESCRIPTION, /organizację/);
assert.equal(INVOICE_DETAIL_ORGANIZATION_REQUIRED_TITLE, "Wybierz organizację, aby zobaczyć fakturę");
assert.match(INVOICE_DETAIL_ORGANIZATION_REQUIRED_DESCRIPTION, /wybranej organizacji/);
assert.equal(canUseInvoicesOrganizationScope(null), false);
assert.equal(canUseInvoicesOrganizationScope(""), false);
assert.equal(canUseInvoicesOrganizationScope("   "), false);
assert.equal(canUseInvoicesOrganizationScope("42"), true);
assert.equal(canUseInvoicesOrganizationScope(42), true);
assert.deepEqual(withActiveOrganizationQuery("42", { limit: 6 }), { limit: 6, organization_id: "42" });

await withMockedFetch(
  async (url, options) => {
    assert.equal(url, `/api${INVOICE_INBOX_ENDPOINT}`);
    assert.equal(options.method, "GET");
    assert.equal(options.body, undefined);
    return jsonResponse(200, makeInbox());
  },
  async () => {
    const inbox = await api.invoiceVerificationInbox();
    assert.equal(flattenInboxItems(inbox).length, 1);
  },
);

await withMockedFetch(
  async (url, options) => {
    assert.equal(url, `/api${INVOICE_INBOX_ENDPOINT}?limit=10&organization_id=42`);
    assert.equal(options.method, "GET");
    assert.equal(options.body, undefined);
    return jsonResponse(200, makeInbox());
  },
  async () => {
    const inbox = await api.invoiceVerificationInbox(withActiveOrganizationQuery("42", { limit: 10 }));
    assert.equal(flattenInboxItems(inbox).length, 1);
  },
);

await withMockedFetch(
  async (url, options) => {
    assert.equal(url, `/api/invoices?search=CASI&organization_id=42`);
    assert.equal(options.method, "GET");
    assert.equal(options.body, undefined);
    return jsonResponse(200, [makeDetail().invoice]);
  },
  async () => {
    const invoices = await invoiceApi.list({ search: "CASI" }, withActiveOrganizationQuery("42"));
    assert.equal(invoices.length, 1);
  },
);

await withMockedFetch(
  async (url, options) => {
    assert.equal(url, `/api${invoiceDetailEndpoint(13)}`);
    assert.equal(options.method, "GET");
    assert.equal(options.body, undefined);
    return jsonResponse(200, makeDetail());
  },
  async () => {
    const detail = await invoiceApi.detail(13);
    assert.equal(canRenderInvoiceDetailData("ready", detail), true);
  },
);

await withMockedFetch(
  async (url, options) => {
    assert.equal(url, `/api${invoiceDetailEndpoint(13)}?organization_id=42`);
    assert.equal(options.method, "GET");
    assert.equal(options.body, undefined);
    return jsonResponse(200, makeDetail());
  },
  async () => {
    const detail = await invoiceApi.detail(13, withActiveOrganizationQuery("42"));
    assert.equal(canRenderInvoiceDetailData("ready", detail), true);
  },
);

await withMockedFetch(
  async (url, options) => {
    assert.equal(url, `/api${invoiceCommentEndpoint(13)}?organization_id=42`);
    assert.equal(options.method, "POST");
    assert.deepEqual(JSON.parse(options.body), {
      note_text: "Komentarz operatora",
    });
    return jsonResponse(201, {
      invoice_comment_id: 9,
      invoice_id: 13,
      organization_id: 42,
      note_text: "Komentarz operatora",
      created_by_user_name: "Operator",
      created_at: "2026-07-02T10:00:00Z",
    });
  },
  async () => {
    const comment = await invoiceApi.addComment(
      13,
      { note_text: "Komentarz operatora" },
      withActiveOrganizationQuery("42"),
    );
    assert.equal(comment.invoice_comment_id, 9);
    assert.equal(comment.note_text, "Komentarz operatora");
  },
);

await withMockedFetch(
  async (url, options) => {
    assert.equal(url, `/api${invoiceActionEndpoint(13, "confirm-duplicate")}`);
    assert.equal(options.method, "POST");
    assert.equal(options.body, undefined);
    return jsonResponse(200, makeDetail().invoice);
  },
  async () => {
    const result = await invoiceApi.submitAction(13, "confirm-duplicate");
    assert.equal(result.invoice_number, "FV/2026/04/13");
  },
);

await withMockedFetch(
  async (url, options) => {
    assert.equal(url, `/api${invoiceActionEndpoint(13, "handoff")}`);
    assert.equal(options.method, "POST");
    assert.deepEqual(JSON.parse(options.body), {
      handoff_target: "Ksiegowosc",
      handoff_note: "Gotowe do przekazania.",
    });
    return jsonResponse(200, makeDetail({ invoice: { ...makeDetail().invoice, workflow_state: "przekazana" } }).invoice);
  },
  async () => {
    const request = buildInvoiceActionRequest("handoff", {
      handoffTarget: "Ksiegowosc",
      handoffNote: "Gotowe do przekazania.",
    });
    assert.equal(request.ok, true);
    const result = await invoiceApi.submitAction(13, request.request.action, request.request.payload);
    assert.equal(result.workflow_state, "przekazana");
  },
);

const actionRequest = buildInvoiceActionRequest("close", { reason: "Rozliczona." });
assert.equal(actionRequest.ok, true);

const submitDeferred = deferred();
const submittingStates = [];
const submittedRequests = [];
let refreshCount = 0;
const guardedSubmitter = createInvoiceActionSubmitter({
  refreshDetail: async () => {
    refreshCount += 1;
  },
  setSubmittingAction: (action) => submittingStates.push(action),
  submitAction: async (request) => {
    submittedRequests.push(request);
    await submitDeferred.promise;
    return makeDetail().invoice;
  },
});

const firstSubmit = guardedSubmitter(actionRequest.request);
const secondSubmit = guardedSubmitter(actionRequest.request);
assert.equal((await secondSubmit).status, "ignored");
assert.equal(submittedRequests.length, 1);
assert.equal(submittingStates[0], "close");
submitDeferred.resolve();
assert.equal((await firstSubmit).status, "success");
assert.equal(refreshCount, 1);
assert.equal(submittingStates.at(-1), null);

let failedRefreshCount = 0;
const failedSubmitter = createInvoiceActionSubmitter({
  refreshDetail: async () => {
    failedRefreshCount += 1;
  },
  setSubmittingAction: () => undefined,
  submitAction: async () => {
    throw new ApiError("Backend padl", 500, {});
  },
});
const failedResult = await failedSubmitter(actionRequest.request);
assert.equal(failedResult.status, "error");
assert.equal(failedResult.errorState.status, "server-error");
assert.equal(failedRefreshCount, 0);

const commentValidation = buildInvoiceCommentRequest("Komentarz po weryfikacji.", "42");
assert.equal(commentValidation.ok, true);

const commentDeferred = deferred();
const commentSubmittingStates = [];
const submittedComments = [];
let commentRefreshCount = 0;
const guardedCommentSubmitter = createInvoiceCommentSubmitter({
  refreshDetail: async () => {
    commentRefreshCount += 1;
  },
  setSubmitting: (submitting) => commentSubmittingStates.push(submitting),
  submitComment: async (payload) => {
    submittedComments.push(payload);
    await commentDeferred.promise;
    return { invoice_comment_id: 10, note_text: payload.note_text };
  },
});

const firstCommentSubmit = guardedCommentSubmitter(commentValidation);
const secondCommentSubmit = guardedCommentSubmitter(commentValidation);
assert.equal((await secondCommentSubmit).status, "ignored");
assert.deepEqual(submittedComments, [{ note_text: "Komentarz po weryfikacji." }]);
assert.equal(commentSubmittingStates[0], true);
commentDeferred.resolve();
assert.equal((await firstCommentSubmit).status, "success");
assert.equal(commentRefreshCount, 1);
assert.equal(commentSubmittingStates.at(-1), false);

const blockedCommentResult = await createInvoiceCommentSubmitter({
  refreshDetail: async () => {
    throw new Error("Nie powinno odswiezac bez poprawnego komentarza.");
  },
  setSubmitting: () => undefined,
  submitComment: async () => {
    throw new Error("Nie powinno wysylac pustego komentarza.");
  },
})(buildInvoiceCommentRequest("  ", "42"));
assert.equal(blockedCommentResult.status, "blocked");

let failedCommentRefreshCount = 0;
const failedCommentSubmitter = createInvoiceCommentSubmitter({
  refreshDetail: async () => {
    failedCommentRefreshCount += 1;
  },
  setSubmitting: () => undefined,
  submitComment: async () => {
    throw new ApiError("Backend padl", 500, {});
  },
});
const failedCommentResult = await failedCommentSubmitter(commentValidation);
assert.equal(failedCommentResult.status, "error");
assert.equal(failedCommentResult.errorState.status, "server-error");
assert.equal(failedCommentRefreshCount, 0);

let authEventCount = 0;
const previousWindow = global.window;
const previousCustomEvent = global.CustomEvent;

global.window = {
  dispatchEvent(event) {
    if (event.type === AUTH_REQUIRED_EVENT) {
      authEventCount += 1;
    }
    return true;
  },
};
global.CustomEvent = class CustomEvent {
  constructor(type) {
    this.type = type;
  }
};

try {
  await withMockedFetch(
    async () => jsonResponse(401, { error: "Brak sesji" }),
    async () => {
      await assert.rejects(() => invoiceApi.submitAction(13, "close", { reason: "Rozliczona." }), ApiError);
    },
  );
} finally {
  if (previousWindow) {
    global.window = previousWindow;
  } else {
    delete global.window;
  }

  if (previousCustomEvent) {
    global.CustomEvent = previousCustomEvent;
  } else {
    delete global.CustomEvent;
  }
}

assert.equal(authEventCount, 1);

console.log("Invoices regression tests passed.");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
