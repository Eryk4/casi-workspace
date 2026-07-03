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
  BOSS_ASSISTANT_AI_ACTIONS_ENABLED,
  BOSS_ASSISTANT_ENDPOINT,
  BOSS_ASSISTANT_ORGANIZATION_REQUIRED_DESCRIPTION,
  BOSS_ASSISTANT_ORGANIZATION_REQUIRED_TITLE,
  BOSS_ASSISTANT_READ_ONLY,
  buildBossAssistantKpis,
  buildBossAssistantRows,
  canUseBossAssistantOrganizationScope,
  getBossAssistantErrorState,
  hasBossAssistantData,
  isBossAssistantEmpty,
  readTaskFocusSnapshot,
  taskPriorityTone,
  taskStatusTone,
} = require("../src/modules/assistant-ceo/bossAssistantModel.ts");

function jsonResponse(status, payload) {
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: {
      get(name) {
        return name.toLowerCase() === "content-type" ? "application/json" : null;
      },
    },
    json: async () => payload,
    text: async () => JSON.stringify(payload),
  };
}

async function withMockedFetch(handler, callback) {
  const originalFetch = global.fetch;
  global.fetch = async (url, options = {}) => handler(String(url), options);

  try {
    await callback();
  } finally {
    global.fetch = originalFetch;
  }
}

function makeTask(overrides = {}) {
  return {
    task_id: 21,
    title: "Zatwierdzic priorytet wdrozenia",
    description: "Sprawa wymaga decyzji managera.",
    task_type: "zadanie",
    status: "oczekuje",
    priority: "wysoki",
    due_at: "2099-06-30T10:00",
    remind_at: "2099-06-30T08:30",
    visibility_scope: "organizacja",
    organization_name: "CASI",
    owner_user_name: "Karol Manager",
    assigned_user_name: "Ola Operator",
    calendar_name: "Operacje",
    reminder_state: "zaplanowane",
    linked_entity_count: 2,
    ...overrides,
  };
}

const snapshot = readTaskFocusSnapshot({
  generated_at: "2099-06-30T08:00",
  available_views: ["moj_dzien", "do_decyzji", "po_terminie", "czeka_na_kogos"],
  views: [
    {
      code: "moj_dzien",
      label: "Moj dzien",
      count: 2,
      items: [makeTask({ task_id: 21 })],
    },
    {
      code: "do_decyzji",
      label: "Do decyzji",
      count: 1,
      items: [makeTask({ task_id: 21 }), makeTask({ task_id: 22, title: "Wybrac budzet", priority: "krytyczny" })],
    },
    {
      code: "po_terminie",
      label: "Po terminie",
      count: 1,
      items: [makeTask({ task_id: 23, title: "Zalegle potwierdzenie", priority: "normalny" })],
    },
    {
      code: "czeka_na_kogos",
      label: "Czeka na kogos",
      count: 1,
      items: [makeTask({ task_id: 24, title: "Czeka na kontrahenta", status: "oczekuje", priority: "niski" })],
    },
  ],
});

assert.equal(snapshot.views.length, 4);
assert.equal(snapshot.views[0].items[0].task_id, 21);

const rows = buildBossAssistantRows(snapshot);
assert.equal(rows.length, 4);
assert.equal(rows[0].title, "Zatwierdzic priorytet wdrozenia");
assert.equal(rows[0].focusLabel, "Do decyzji");
assert.equal(rows[0].statusLabel, "Oczekuje");
assert.equal(rows[0].statusTone, "warning");
assert.equal(rows[0].priorityLabel, "Wysoki");
assert.equal(rows[0].priorityTone, "warning");
assert.equal(rows[0].dueLabel, "2099-06-30 08:30");
assert.equal(rows[0].ownerLabel, "Ola Operator");
assert.equal(rows[0].sourceLabel, "Zadanie");

const kpis = buildBossAssistantKpis(snapshot);
assert.deepEqual(kpis, {
  urgent: 2,
  overdue: 1,
  decisions: 1,
  blockers: 1,
  today: 2,
  totalVisible: 4,
});

assert.equal(taskStatusTone(makeTask({ status: "zakonczone" })), "ok");
assert.equal(taskStatusTone(makeTask({ status: "oczekuje" })), "warning");
assert.equal(taskStatusTone(makeTask({ reminder_state: "blad", status: "nowe" })), "danger");
assert.equal(taskPriorityTone(makeTask({ priority: "krytyczny" })), "danger");
assert.equal(taskPriorityTone(makeTask({ priority: "niski" })), "neutral");

assert.equal(hasBossAssistantData("ready", snapshot), true);
assert.equal(isBossAssistantEmpty("ready", { generated_at: "x", available_views: [], views: [] }), true);
assert.equal(hasBossAssistantData("loading", snapshot), false);

assert.equal(BOSS_ASSISTANT_ENDPOINT, "/tasks/focus");
assert.equal(BOSS_ASSISTANT_READ_ONLY, true);
assert.equal(BOSS_ASSISTANT_AI_ACTIONS_ENABLED, false);
assert.equal(BOSS_ASSISTANT_ORGANIZATION_REQUIRED_TITLE, "Wybierz organizacje, aby zobaczyc Asystenta Szefa");
assert.match(BOSS_ASSISTANT_ORGANIZATION_REQUIRED_DESCRIPTION, /organization_id/);
assert.equal(canUseBossAssistantOrganizationScope(null), false);
assert.equal(canUseBossAssistantOrganizationScope(undefined), false);
assert.equal(canUseBossAssistantOrganizationScope(""), false);
assert.equal(canUseBossAssistantOrganizationScope("42"), true);
assert.deepEqual(withActiveOrganizationQuery("42"), { organization_id: "42" });
assert.deepEqual(withActiveOrganizationQuery("42", { limit: 5 }), { limit: 5, organization_id: "42" });

assert.throws(() => readTaskFocusSnapshot([]), ApiContractError);
assert.throws(() => readTaskFocusSnapshot({ views: [{ code: "moj_dzien", items: [{ title: "Brak ID" }] }] }), ApiContractError);

assert.equal(getBossAssistantErrorState(new ApiError("Brak sesji", 401, {})).status, "unauthenticated");
assert.equal(getBossAssistantErrorState(new ApiError("Brak uprawnien", 403, {})).status, "forbidden");
assert.equal(getBossAssistantErrorState(new ApiError("Backend padl", 500, {})).status, "server-error");
assert.equal(getBossAssistantErrorState(new ApiContractError(BOSS_ASSISTANT_ENDPOINT, {})).title, "Niepoprawny format Asystenta Szefa");

withMockedFetch(
  async (url, options) => {
    assert.equal(url, "/api/tasks/focus?organization_id=42");
    assert.equal(options.method, "GET");
    assert.equal(options.credentials, "include");
    assert.equal(options.body, undefined);
    return jsonResponse(200, snapshot);
  },
  async () => {
    const scopedPayload = await api.taskFocus(withActiveOrganizationQuery("42"));
    const scopedSnapshot = readTaskFocusSnapshot(scopedPayload);

    assert.equal(hasBossAssistantData("ready", scopedSnapshot), true);
    assert.equal(BOSS_ASSISTANT_READ_ONLY, true);
    assert.equal(BOSS_ASSISTANT_AI_ACTIONS_ENABLED, false);
  },
).then(
  () => {
    console.log("Boss Assistant regression tests passed.");
  },
  (error) => {
    console.error(error);
    process.exitCode = 1;
  },
);
