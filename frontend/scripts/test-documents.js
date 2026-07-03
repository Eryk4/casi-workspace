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

const { ApiContractError, ApiError } = require("../src/lib/api.ts");
const { withActiveOrganizationQuery } = require("../src/context/organizationContextModel.ts");
const {
  DOCUMENTS_ENDPOINT,
  DOCUMENTS_ORGANIZATION_REQUIRED_DESCRIPTION,
  DOCUMENTS_ORGANIZATION_REQUIRED_TITLE,
  DOCUMENTS_READ_ONLY,
  buildDocumentsKpis,
  buildKnowledgeDocumentRows,
  canUseDocumentsOrganizationScope,
  documentStatusTone,
  documentWorkflowTone,
  getDocumentsErrorState,
  hasDocumentsData,
  isDocumentsEmpty,
  readKnowledgeDocuments,
} = require("../src/modules/documents/documentsModel.ts");

function makeDocument(overrides = {}) {
  return {
    knowledge_document_id: 7,
    title: "Procedura akceptacji faktur",
    file_name: "procedura-faktur.pdf",
    mime_type: "application/pdf",
    source_type: "manual",
    library_path: "Procedury/Faktury",
    library_path_label: "Procedury / Faktury",
    lifecycle_status: "active",
    duplicate_status: "none",
    processing_status: "done",
    processing_error: null,
    current_version_number: 2,
    official_version_number: 1,
    business_status: "do_sprawdzenia",
    business_status_label: "do sprawdzenia",
    workflow_status: "official_missing",
    workflow_status_label: "brak wersji obowiazujacej",
    owner_user_label: "Ania Operator",
    reviewer_user_label: "Renata Reviewer",
    approver_user_label: "Adam Approval",
    organization_name: "CASI",
    created_by_login: "admin",
    created_by_display_name: "Administrator",
    updated_at: "2099-04-10T11:20:00",
    use_in_assistant: true,
    is_downloadable: true,
    ...overrides,
  };
}

const documents = readKnowledgeDocuments({ documents: [makeDocument()] });
assert.equal(documents.length, 1);
assert.equal(documents[0].knowledge_document_id, 7);
assert.equal(documents[0].business_status, "do_sprawdzenia");

const rows = buildKnowledgeDocumentRows(documents);
assert.equal(rows[0].title, "Procedura akceptacji faktur");
assert.equal(rows[0].fileLabel, "procedura-faktur.pdf");
assert.equal(rows[0].statusLabel, "do sprawdzenia");
assert.equal(rows[0].statusTone, "warning");
assert.equal(rows[0].workflowLabel, "brak wersji obowiazujacej");
assert.equal(rows[0].workflowTone, "warning");
assert.equal(rows[0].sourceLabel, "Manual");
assert.equal(rows[0].ownerLabel, "Ania Operator");
assert.equal(rows[0].folderLabel, "Procedury / Faktury");
assert.equal(rows[0].updatedLabel, "2099-04-10 11:20");
assert.equal(rows[0].versionLabel, "v2 / oficj. 1");
assert.equal(rows[0].title.includes("C:\\Users\\"), false);
assert.equal(rows[0].folderLabel.includes("C:\\Users\\"), false);

const localPathDocumentRows = buildKnowledgeDocumentRows(
  readKnowledgeDocuments({
    documents: [
      makeDocument({
        file_name: "C:\\Users\\erykl\\tajne\\umowa.pdf",
        library_path: "C:\\Users\\erykl\\storage\\knowledge",
        library_path_label: "Umowy / Klienci",
      }),
    ],
  }),
);
assert.equal(localPathDocumentRows[0].folderLabel, "Umowy / Klienci");
assert.equal(localPathDocumentRows[0].title.includes("C:\\Users\\"), false);
assert.equal(localPathDocumentRows[0].folderLabel.includes("C:\\Users\\"), false);

assert.equal(documentStatusTone(makeDocument({ business_status: "obowiazujacy" })), "ok");
assert.equal(documentStatusTone(makeDocument({ processing_status: "processing" })), "info");
assert.equal(documentStatusTone(makeDocument({ processing_status: "error" })), "danger");
assert.equal(documentWorkflowTone(makeDocument({ workflow_status: "stable" })), "ok");
assert.equal(documentWorkflowTone(makeDocument({ workflow_status: "deleted" })), "danger");

const kpis = buildDocumentsKpis([
  makeDocument({ knowledge_document_id: 1, business_status: "obowiazujacy", workflow_status: "stable", processing_status: "done" }),
  makeDocument({ knowledge_document_id: 2, business_status: "do_akceptacji", workflow_status: "review_needed", processing_status: "done" }),
  makeDocument({ knowledge_document_id: 3, business_status: "roboczy", workflow_status: "processing", processing_status: "processing" }),
]);
assert.deepEqual(kpis, {
  total: 3,
  ready: 1,
  needsDecision: 1,
  processingOrErrors: 1,
});

assert.equal(hasDocumentsData("ready", documents), true);
assert.equal(isDocumentsEmpty("ready", []), true);
assert.equal(hasDocumentsData("loading", documents), false);

assert.equal(DOCUMENTS_ENDPOINT, "/knowledge/documents");
assert.equal(DOCUMENTS_READ_ONLY, true);
assert.equal(DOCUMENTS_ORGANIZATION_REQUIRED_TITLE, "Wybierz organizacje, aby zobaczyc dokumenty");
assert.ok(DOCUMENTS_ORGANIZATION_REQUIRED_DESCRIPTION.includes("organization_id"));
assert.equal(canUseDocumentsOrganizationScope("1"), true);
assert.equal(canUseDocumentsOrganizationScope(1), true);
assert.equal(canUseDocumentsOrganizationScope(null), false);
assert.equal(canUseDocumentsOrganizationScope(""), false);
assert.deepEqual(withActiveOrganizationQuery("3"), { organization_id: "3" });
assert.deepEqual(withActiveOrganizationQuery("3", { search: "umowa" }), { search: "umowa", organization_id: "3" });
assert.deepEqual(withActiveOrganizationQuery(null, { search: "umowa" }), { search: "umowa" });

assert.throws(() => readKnowledgeDocuments([]), ApiContractError);
assert.throws(() => readKnowledgeDocuments({ items: [] }), ApiContractError);
assert.throws(() => readKnowledgeDocuments({ documents: [{ title: "Brak ID" }] }), ApiContractError);

assert.equal(getDocumentsErrorState(new ApiError("Brak sesji", 401, {})).status, "unauthenticated");
assert.equal(getDocumentsErrorState(new ApiError("Brak uprawnien", 403, {})).status, "forbidden");
assert.equal(getDocumentsErrorState(new ApiError("Backend padl", 500, {})).status, "server-error");
assert.equal(getDocumentsErrorState(new ApiContractError(DOCUMENTS_ENDPOINT, {})).title, "Niepoprawny format dokumentow");

console.log("Documents regression tests passed.");
