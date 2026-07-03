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

const { ApiContractError, ApiError, workItemDetailPath } = require("../src/lib/api.ts");
const {
  WORK_ITEM_DETAIL_ORGANIZATION_REQUIRED_DESCRIPTION,
  WORK_ITEM_DETAIL_ORGANIZATION_REQUIRED_TITLE,
  WORK_ITEM_DETAIL_READ_ONLY,
  WORK_ITEM_DETAIL_WRITE_ACTIONS,
  buildWorkItemDetailView,
  canUseWorkItemDetailOrganizationScope,
  getWorkItemDetailErrorState,
  hasUnsafeWorkItemDetailText,
  hasWorkItemDetailWriteActions,
  readWorkItemDetail,
  workItemDetailPath: viewWorkItemDetailPath,
} = require("../src/modules/work-items/workItemDetailModel.ts");

function makePayload(overrides = {}) {
  const { work_item: workItemOverrides = {}, ...payloadOverrides } = overrides;
  return {
    work_item: {
      work_item_id: 41,
      title: "Wyjaśnić rozbieżność na fakturze serwisowej",
      description: "Kontrahent pyta, czy korekta dotyczy ostatniej dostawy.",
      status: "w_toku",
      priority_level: "wysoki",
      priority_score: 80,
      source_type: "invoice",
      source_id: 9,
      assigned_user_id: 12,
      assigned_user_name: "Ania Operator",
      organization_name: "CASI",
      due_at: "2026-07-03T15:00:00",
      sla_stage: "warning",
      sla_state_label: "SLA dziś",
      is_closed: false,
      is_due_overdue: false,
      is_sla_overdue: false,
      created_at: "2026-07-03T08:00:00",
      updated_at: "2026-07-03T09:00:00",
      metadata: {
        invoice_id: 9,
        invoice_number: "FV/9/2026",
        contractor_id: 13,
        contractor_name: "Kowalski Transport",
        knowledge_document_ids: [7],
        document_title: "Umowa serwisowa",
        task_id: 501,
        task_title: "Sprawdzić aneks",
        storage_key: "data/magazyn/private",
      },
      ...workItemOverrides,
    },
    history: [
      {
        work_item_history_id: 1001,
        action_type: "work_item_created",
        message: "Sprawa została utworzona po sygnale z faktury.",
        actor_user_name: "System",
        created_at: "2026-07-03T08:00:00",
        details: { payload: "hidden" },
      },
    ],
    ...payloadOverrides,
  };
}

const detail = readWorkItemDetail(makePayload(), 41);
assert.equal(detail.workItem.work_item_id, 41);
assert.equal(detail.workItem.source_id, 9);
assert.equal(detail.history.length, 1);

const view = buildWorkItemDetailView(detail);
assert.equal(view.title, "Wyjaśnić rozbieżność na fakturze serwisowej");
assert.equal(view.row.statusLabel, "W toku");
assert.equal(view.row.priorityLabel, "Wysoki");
assert.match(view.attentionReason, /priorytet|SLA/i);
assert.ok(view.facts.some((fact) => fact.label === "Źródło" && fact.value === "Faktury"));
assert.equal(view.relatedInvoices[0].href, "/faktury/9");
assert.equal(view.relatedInvoices[0].title, "FV/9/2026");
assert.equal(view.relatedContractors[0].href, "/crm/13");
assert.equal(view.relatedContractors[0].title, "Kowalski Transport");
assert.equal(view.relatedDocuments[0].href, "/dokumenty/7");
assert.equal(view.relatedDocuments[0].title, "Umowa serwisowa");
assert.equal(view.relatedTasks[0].href, "/asystent-szefa");
assert.equal(view.history[0].title, "Utworzono sprawę");
assert.equal(hasUnsafeWorkItemDetailText(view), false);

const sourceOnlyView = buildWorkItemDetailView(
  readWorkItemDetail(
    makePayload({
      work_item: {
        source_type: "knowledge_document",
        source_id: 55,
        metadata: {},
      },
      history: [],
    }),
    41,
  ),
);
assert.equal(sourceOnlyView.relatedDocuments[0].href, "/dokumenty/55");
assert.equal(sourceOnlyView.relatedInvoices.length, 0);
assert.equal(sourceOnlyView.history.length, 0);

const noRelations = buildWorkItemDetailView(
  readWorkItemDetail(
    makePayload({
      work_item: {
        source_type: "manual",
        source_id: null,
        metadata: {},
      },
      history: [],
    }),
    41,
  ),
);
assert.equal(noRelations.relatedInvoices.length, 0);
assert.equal(noRelations.relatedContractors.length, 0);
assert.equal(noRelations.relatedDocuments.length, 0);
assert.equal(noRelations.relatedTasks.length, 0);

assert.equal(WORK_ITEM_DETAIL_READ_ONLY, true);
assert.equal(hasWorkItemDetailWriteActions(), false);
assert.deepEqual(WORK_ITEM_DETAIL_WRITE_ACTIONS, []);
assert.equal(WORK_ITEM_DETAIL_ORGANIZATION_REQUIRED_TITLE, "Wybierz organizację, aby zobaczyć kartę sprawy");
assert.match(WORK_ITEM_DETAIL_ORGANIZATION_REQUIRED_DESCRIPTION, /organizacji/i);
assert.equal(canUseWorkItemDetailOrganizationScope("1"), true);
assert.equal(canUseWorkItemDetailOrganizationScope(null), false);
assert.equal(workItemDetailPath(41), "/work-items/41");
assert.equal(viewWorkItemDetailPath(41), "/work-items/41");

const allLinks = [
  ...view.relatedInvoices,
  ...view.relatedContractors,
  ...view.relatedDocuments,
  ...view.relatedTasks,
].map((item) => item.href);
assert.ok(allLinks.every((href) => ["/faktury/", "/crm/", "/dokumenty/", "/asystent-szefa"].some((prefix) => href.startsWith(prefix))));

assert.throws(() => readWorkItemDetail({ work_item: { title: "Bez ID" } }), ApiContractError);
assert.equal(getWorkItemDetailErrorState(new ApiError("Brak sesji", 401, {})).status, "unauthenticated");
assert.equal(getWorkItemDetailErrorState(new ApiError("Brak dostępu", 403, {})).status, "forbidden");
assert.equal(getWorkItemDetailErrorState(new ApiError("Nie ma", 404, {})).title, "Nie znaleziono sprawy");
assert.equal(getWorkItemDetailErrorState(new ApiError("Backend", 500, {})).status, "server-error");

console.log("Work Item detail model tests passed.");
