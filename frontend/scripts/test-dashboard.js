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

const { ApiContractError, ApiError, AUTH_REQUIRED_EVENT, api, apiRequest, readDashboardSnapshot } = require("../src/lib/api.ts");
const { withActiveOrganizationQuery } = require("../src/context/organizationContextModel.ts");
const {
  DASHBOARD_ENDPOINT,
  DASHBOARD_MUTATION_METHODS,
  DASHBOARD_ORGANIZATION_REQUIRED_DESCRIPTION,
  DASHBOARD_ORGANIZATION_REQUIRED_TITLE,
  buildSignals,
  canUseDashboardOrganizationScope,
  canRenderDashboardData,
  getDashboardErrorState,
  hasDashboardData,
  isDashboardReadOnly,
} = require("../src/modules/dashboard/dashboardModel.ts");

function makeSnapshot(cards) {
  return {
    cards,
    operational_alerts: [
      {
        severity: "warning",
        category: "invoices",
        title: "Faktury czekaja na weryfikacje",
        description: "4 faktury wymagaja decyzji.",
      },
    ],
    active_reminders: [],
    knowledge_queue: [],
    recent_events: [],
  };
}

const zeroSnapshot = makeSnapshot({
  nowe_faktury: 0,
  do_weryfikacji: 0,
  podejrzenia_duplikatow: 0,
  pewne_duplikaty: 0,
  nowi_kontrahenci: 0,
  aktywne_przypomnienia: 0,
});

const liveSnapshot = makeSnapshot({
  nowe_faktury: 3,
  do_weryfikacji: 4,
  podejrzenia_duplikatow: 1,
  pewne_duplikaty: 1,
  nowi_kontrahenci: 8,
  aktywne_przypomnienia: 0,
});

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

async function main() {

assert.equal(getDashboardErrorState(new ApiError("Brak sesji", 401, {})).status, "unauthenticated");
assert.equal(canRenderDashboardData("unauthenticated", null), false);

assert.equal(canRenderDashboardData("ready", liveSnapshot), true);
assert.equal(buildSignals(liveSnapshot, "invoices").length, 1);
assert.equal(buildSignals(liveSnapshot, "tasks").length, 0);

assert.throws(
  () => readDashboardSnapshot({ cards: {}, operational_alerts: [], active_reminders: [] }),
  ApiContractError,
);
assert.equal(
  getDashboardErrorState(new ApiContractError("/dashboard", {})).title,
  "Niepoprawny format danych pulpitu",
);

assert.equal(hasDashboardData(zeroSnapshot), true);
assert.equal(canRenderDashboardData("ready", zeroSnapshot), true);

assert.equal(isDashboardReadOnly(), true);
assert.deepEqual(DASHBOARD_MUTATION_METHODS, []);
assert.equal(DASHBOARD_ORGANIZATION_REQUIRED_TITLE, "Wybierz organizacje, aby zobaczyc pulpit");
assert.match(DASHBOARD_ORGANIZATION_REQUIRED_DESCRIPTION, /organization_id/);
assert.equal(canUseDashboardOrganizationScope(null), false);
assert.equal(canUseDashboardOrganizationScope(""), false);
assert.equal(canUseDashboardOrganizationScope("   "), false);
assert.equal(canUseDashboardOrganizationScope("42"), true);
assert.equal(canUseDashboardOrganizationScope(42), true);
assert.deepEqual(withActiveOrganizationQuery("42"), { organization_id: "42" });

await withMockedFetch(
  async (url, options) => {
    assert.equal(url, `/api${DASHBOARD_ENDPOINT}`);
    assert.equal(options.method, "GET");
    assert.equal(options.body, undefined);
    return jsonResponse(200, liveSnapshot);
  },
  async () => {
    const snapshot = await api.dashboard();
    assert.equal(canRenderDashboardData("ready", snapshot), true);
  },
);

await withMockedFetch(
  async (url, options) => {
    assert.equal(url, `/api${DASHBOARD_ENDPOINT}?organization_id=42`);
    assert.equal(options.method, "GET");
    assert.equal(options.body, undefined);
    return jsonResponse(200, liveSnapshot);
  },
  async () => {
    const snapshot = await api.dashboard(withActiveOrganizationQuery("42"));
    assert.equal(canRenderDashboardData("ready", snapshot), true);
    assert.equal(buildSignals(snapshot, "all").length, 1);
  },
);

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
      await assert.rejects(() => apiRequest(DASHBOARD_ENDPOINT), ApiError);
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

console.log("Dashboard regression tests passed.");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
