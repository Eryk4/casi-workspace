const assert = require("node:assert/strict");
const fs = require("node:fs");
const Module = require("node:module");
const path = require("node:path");
const ts = require("typescript");

require.extensions[".ts"] = function compileTypeScript(module, filename) {
  const source = fs.readFileSync(filename, "utf8");
  const output = ts.transpileModule(source, {
    compilerOptions: { esModuleInterop: true, module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
    fileName: filename,
  });
  module._compile(output.outputText, filename);
};

const srcRoot = path.join(__dirname, "..", "src");
const originalResolveFilename = Module._resolveFilename;
Module._resolveFilename = function resolveAlias(request, parent, isMain, options) {
  if (request.startsWith("@/")) {
    const resolved = path.join(srcRoot, request.slice(2));
    return [".ts", ".tsx", ".js", ".jsx"].map((extension) => `${resolved}${extension}`).find(fs.existsSync) ?? resolved;
  }
  return originalResolveFilename.call(this, request, parent, isMain, options);
};

const { ApiContractError, ApiError, api } = require("../src/lib/api.ts");
const {
  BILLING_ATTENTION_MUTATION_METHODS,
  BILLING_ATTENTION_PREVIEW_LIMIT,
  BILLING_NEXT_STEP_ATTENTION_ENDPOINT,
  buildBillingAttentionView,
  getBillingAttentionErrorState,
  isBillingAttentionReadOnly,
  readBillingAttentionResponse,
} = require("../src/modules/dashboard/billingAttentionModel.ts");

function candidate(id, plannedFor, reasonCode, overrides = {}) {
  return {
    billing_next_step_event_id: id,
    organization_id: 42,
    reason_code: reasonCode,
    planned_for: plannedFor,
    target_type: "payer",
    target_id: 7,
    related_issue_key: null,
    step_type: "call",
    title: `Krok ${id}`,
    target_label: "Płatnik #7",
    target_href: "/rozliczenia/platnicy/7",
    created_at: `2026-12-10T10:00:0${id}`,
    ...overrides,
  };
}

const payload = {
  organization_id: 42,
  as_of_date: "2026-12-18",
  overdue_count: 6,
  due_today_count: 1,
  attention_count: 7,
  candidates: [
    candidate(7, "2026-12-18", "due_today"),
    candidate(4, "2026-12-17", "overdue", { title: "Identyczny krok" }),
    candidate(5, "2026-12-17", "overdue", { title: "Identyczny krok" }),
    candidate(6, "2026-12-16", "overdue", { target_label: "Cel historyczny", target_href: "https://evil.example" }),
    candidate(3, "2026-12-15", "overdue"),
    candidate(2, "2026-12-14", "overdue"),
    candidate(1, "2026-12-13", "overdue"),
  ],
};

const response = readBillingAttentionResponse(payload);
const view = buildBillingAttentionView(response);
assert.equal(BILLING_NEXT_STEP_ATTENTION_ENDPOINT, "/billing/next-step-attention");
assert.equal(BILLING_ATTENTION_PREVIEW_LIMIT, 5);
assert.equal(view.overdueCount, 6);
assert.equal(view.dueTodayCount, 1);
assert.equal(view.attentionCount, 7);
assert.equal(view.preview.length, 5);
assert.deepEqual(view.candidates.map((item) => item.eventId), [1, 2, 3, 6, 4, 5, 7]);
assert.equal(view.candidates.filter((item) => item.title === "Identyczny krok").length, 2);
assert.equal(view.candidates.find((item) => item.eventId === 6).targetHref, undefined);
assert.equal(view.candidates.at(-1).plannedFor, "2026-12-18");
assert.equal(isBillingAttentionReadOnly(), true);
assert.deepEqual(BILLING_ATTENTION_MUTATION_METHODS, []);

assert.throws(
  () => readBillingAttentionResponse({ ...payload, candidates: [...payload.candidates, candidate(8, "2026-12-19", "overdue")], overdue_count: 7, attention_count: 8 }),
  ApiContractError,
);
assert.throws(
  () => readBillingAttentionResponse({ ...payload, candidates: [{ ...payload.candidates[0], planned_for: null }] }),
  ApiContractError,
);
assert.equal(getBillingAttentionErrorState(new ApiError("Awaria", 500, {})).status, "server-error");
assert.equal(getBillingAttentionErrorState(new ApiContractError(BILLING_NEXT_STEP_ATTENTION_ENDPOINT, {})).title, "Niepoprawne dane attention");

(async () => {
  const previousFetch = global.fetch;
  global.fetch = async (url, options) => {
    assert.equal(url, "/api/billing/next-step-attention?organization_id=42");
    assert.equal(options.method, "GET");
    assert.equal(options.body, undefined);
    return {
      ok: true,
      status: 200,
      headers: { get: () => "application/json" },
      json: async () => payload,
      text: async () => JSON.stringify(payload),
    };
  };
  try {
    const apiPayload = await api.billingNextStepAttention({ organization_id: 42 });
    assert.equal(readBillingAttentionResponse(apiPayload).attentionCount, 7);
  } finally {
    if (previousFetch) {
      global.fetch = previousFetch;
    } else {
      delete global.fetch;
    }
  }
  console.log("Billing attention model tests passed.");
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
