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
  DOCUMENT_DETAIL_DELETE_ENABLED,
  DOCUMENT_DETAIL_EDIT_ENABLED,
  DOCUMENT_DETAIL_ENDPOINT_PREFIX,
  DOCUMENT_DETAIL_OCR_ENABLED,
  DOCUMENT_DETAIL_ORGANIZATION_REQUIRED_DESCRIPTION,
  DOCUMENT_DETAIL_ORGANIZATION_REQUIRED_TITLE,
  DOCUMENT_DETAIL_READ_ONLY,
  DOCUMENT_DETAIL_S3_ACTIONS_ENABLED,
  DOCUMENT_DETAIL_UPLOAD_ENABLED,
  buildDocumentAuditRows,
  buildDocumentDetailFacts,
  buildDocumentVersionRows,
  canRenderDocumentDetail,
  canUseDocumentDetailOrganizationScope,
  getDocumentDetailErrorState,
  getDocumentDetailTitle,
  isDocumentDetailEmpty,
  readKnowledgeDocumentDetail,
  safeDocumentFileLabel,
  safeDocumentText,
  safeStorageLabel,
} = require("../src/modules/documents/documentDetailModel.ts");

function makeDetail(overrides = {}) {
  return {
    knowledge_document_id: 7,
    title: "Procedura akceptacji faktur",
    file_name: "C:\\Users\\erykl\\OneDrive\\tajne\\procedura.pdf",
    mime_type: "application/pdf",
    source_type: "manual",
    library_path: "C:\\Users\\erykl\\storage\\knowledge",
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
    organization_name: "CASI",
    created_by_login: "admin",
    created_by_display_name: "Administrator",
    created_at: "2099-04-01T08:00:00",
    updated_at: "2099-04-10T11:20:00",
    use_in_assistant: true,
    is_downloadable: true,
    content_preview: "Bezpieczny skrot procedury bez lokalnych sciezek.",
    versions: [
      {
        knowledge_document_version_id: 71,
        version_number: 2,
        file_name: "C:\\Users\\erykl\\tajne\\procedura-v2.pdf",
        mime_type: "application/pdf",
        storage_key: "data/magazyn/knowledge/procedura-v2.pdf",
        processing_status: "done",
        created_at: "2099-04-10T10:00:00",
        created_by_display_name: "Ania Operator",
        is_official: true,
      },
    ],
    audit_summary: {
      download_count: 3,
      event_count: 4,
      last_download_at: "2099-04-11T09:00:00",
    },
    comment_summary: {
      comment_count: 2,
      annotation_count: 1,
      last_comment_at: "2099-04-11T10:00:00",
    },
    audit_events: [
      {
        audit_event_id: 701,
        event_type: "knowledge_document_viewed",
        action_label: "Podglad szczegolu",
        actor_label: "Administrator",
        event_time: "2099-04-11T10:10:00",
      },
    ],
    ...overrides,
  };
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

const detail = readKnowledgeDocumentDetail(makeDetail(), 7);
assert.equal(detail.knowledge_document_id, 7);
assert.equal(detail.title, "Procedura akceptacji faktur");
assert.equal(detail.file_name, "procedura.pdf");
assert.equal(detail.library_path, "-");
assert.equal(detail.library_path_label, "Procedury / Faktury");
assert.equal(detail.safe_content_preview, "Bezpieczny skrot procedury bez lokalnych sciezek.");
assert.equal(detail.versions.length, 1);
assert.equal(detail.comment_summary.comment_count, 2);
assert.equal(detail.audit_summary.download_count, 3);

const facts = buildDocumentDetailFacts(detail);
assert.equal(facts.find((fact) => fact.label === "Status").value, "do sprawdzenia");
assert.equal(facts.find((fact) => fact.label === "Workflow").value, "brak wersji obowiazujacej");
assert.equal(facts.find((fact) => fact.label === "Odpowiedzialny").value, "Ania Operator");

const versionRows = buildDocumentVersionRows(detail);
assert.equal(versionRows[0].versionLabel, "v2");
assert.equal(versionRows[0].fileLabel, "procedura-v2.pdf");
assert.equal(versionRows[0].storageLabel, "Storage key ukryty");
assert.equal(versionRows[0].officialLabel, "Oficjalna");

const auditRows = buildDocumentAuditRows(detail);
assert.equal(auditRows[0].actionLabel, "Podglad szczegolu");
assert.equal(auditRows[0].actorLabel, "Administrator");

const viewStrings = collectStrings({ detail, facts, versionRows, auditRows });
assert.equal(viewStrings.some((value) => value.includes("C:\\Users\\")), false);
assert.equal(viewStrings.some((value) => value.includes("data/magazyn")), false);
assert.equal(viewStrings.some((value) => value.includes("OneDrive")), false);

assert.equal(safeDocumentText("C:\\Users\\erykl\\tajne\\plik.pdf", "ukryte"), "ukryte");
assert.equal(safeDocumentFileLabel("C:\\Users\\erykl\\tajne\\plik.pdf"), "plik.pdf");
assert.equal(safeStorageLabel("knowledge/documents/7/v2.pdf"), "Storage key zapisany");
assert.equal(safeStorageLabel("data/magazyn/knowledge/plik.pdf"), "Storage key ukryty");

assert.equal(canUseDocumentDetailOrganizationScope("3"), true);
assert.equal(canUseDocumentDetailOrganizationScope(3), true);
assert.equal(canUseDocumentDetailOrganizationScope(null), false);
assert.equal(canUseDocumentDetailOrganizationScope(""), false);
assert.equal(canRenderDocumentDetail("ready", detail), true);
assert.equal(canRenderDocumentDetail("loading", detail), false);
assert.equal(isDocumentDetailEmpty("ready", null), true);
assert.equal(getDocumentDetailTitle(null, 9), "Dokument #9");
assert.equal(getDocumentDetailTitle(detail, 7), "Procedura akceptacji faktur");

assert.equal(DOCUMENT_DETAIL_ENDPOINT_PREFIX, "/knowledge/documents");
assert.equal(DOCUMENT_DETAIL_READ_ONLY, true);
assert.equal(DOCUMENT_DETAIL_UPLOAD_ENABLED, false);
assert.equal(DOCUMENT_DETAIL_EDIT_ENABLED, false);
assert.equal(DOCUMENT_DETAIL_DELETE_ENABLED, false);
assert.equal(DOCUMENT_DETAIL_OCR_ENABLED, false);
assert.equal(DOCUMENT_DETAIL_S3_ACTIONS_ENABLED, false);
assert.equal(DOCUMENT_DETAIL_ORGANIZATION_REQUIRED_TITLE, "Wybierz organizacje, aby zobaczyc dokument");
assert.ok(DOCUMENT_DETAIL_ORGANIZATION_REQUIRED_DESCRIPTION.includes("organization_id"));

assert.throws(() => readKnowledgeDocumentDetail([], 7), ApiContractError);
assert.throws(() => readKnowledgeDocumentDetail({ title: "Brak ID" }, 7), ApiContractError);
assert.throws(() => readKnowledgeDocumentDetail(makeDetail({ knowledge_document_id: 8 }), 7), ApiContractError);

assert.equal(getDocumentDetailErrorState(new ApiError("Brak sesji", 401, {})).status, "unauthenticated");
assert.equal(getDocumentDetailErrorState(new ApiError("Brak uprawnien", 403, {})).status, "forbidden");
assert.equal(getDocumentDetailErrorState(new ApiError("Brak", 404, {})).title, "Nie znaleziono dokumentu");
assert.equal(getDocumentDetailErrorState(new ApiError("Backend padl", 500, {})).status, "server-error");
assert.equal(getDocumentDetailErrorState(new ApiContractError("/knowledge/documents/7", {})).title, "Niepoprawny format dokumentu");

assert.deepEqual(withActiveOrganizationQuery("3"), { organization_id: "3" });

const originalFetch = global.fetch;
let requestedUrl = "";
global.fetch = async (url, options) => {
  requestedUrl = String(url);
  assert.equal(options.method, "GET");
  assert.equal(options.credentials, "include");
  return new Response(JSON.stringify(makeDetail()), {
    status: 200,
    headers: { "content-type": "application/json" },
  });
};

api.knowledgeDocumentDetail(7, withActiveOrganizationQuery("3"))
  .then((payload) => {
    assert.equal(requestedUrl, "/api/knowledge/documents/7?organization_id=3");
    assert.equal(payload.knowledge_document_id, 7);
    global.fetch = originalFetch;
    console.log("Document detail regression tests passed.");
  })
  .catch((error) => {
    global.fetch = originalFetch;
    throw error;
  });
