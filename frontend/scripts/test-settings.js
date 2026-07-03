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
const {
  SETTINGS_ADMIN_ACTIONS_ENABLED,
  SETTINGS_ENDPOINTS,
  SETTINGS_READ_ONLY,
  buildAccountRows,
  buildSafeEnvironmentRows,
  buildSettingsKpis,
  getSettingsErrorState,
  hasSettingsData,
  isSettingsEmpty,
  readSettingsSnapshot,
  sanitizeSettingValue,
} = require("../src/modules/settings/settingsModel.ts");

const session = {
  user_id: 7,
  login: "antoni@casi24.com",
  display_name: "Antoni CASI",
  role: "global_operator",
  organization_id: 3,
  organization_name: "CASI Test",
  organization_slug: "casi-test",
  is_global_admin: true,
  is_active: 1,
  capabilities: ["knowledge.read", "knowledge.manage", "knowledge.read"],
  organization_modules: ["manager_assistant", "documents"],
};

const snapshot = readSettingsSnapshot({
  session,
  meta: {
    storage_backend: "s3",
    db_engine: "sqlite",
    app_release_id: "local-dev",
    public_base_url: "http://127.0.0.1:8000",
    email_enabled: true,
    DATABASE_URL: "postgres://user:password@localhost/db",
    INVOICE_S3_SECRET_ACCESS_KEY: "very-secret",
    storage_root_path: "C:\\Users\\erykl\\OneDrive\\Dokumenty\\CASI Workspace\\data",
  },
  organizations: [
    {
      organization_id: 3,
      name: "CASI Test",
      slug: "casi-test",
      is_active: true,
      enabled_modules: ["manager_assistant", "documents", "billing"],
    },
  ],
  users: [
    {
      user_id: 7,
      login: "antoni@casi24.com",
      display_name: "Antoni CASI",
      role: "global_operator",
      organization_id: 3,
      capabilities: ["knowledge.read"],
      organization_modules: ["documents"],
      is_active: true,
    },
  ],
});

assert.equal(snapshot.currentUser.login, "antoni@casi24.com");
assert.equal(snapshot.currentUser.displayName, "Antoni CASI");
assert.equal(snapshot.currentUser.role, "global_operator");
assert.equal(snapshot.activeOrganization.name, "CASI Test");
assert.deepEqual(snapshot.activeModules, ["billing", "documents", "manager_assistant"]);
assert.deepEqual(snapshot.capabilities, ["knowledge.manage", "knowledge.read"]);
assert.equal(snapshot.environmentRows.find((row) => row.id === "storage_backend").value, "s3");
assert.equal(snapshot.environmentRows.find((row) => row.id === "email_enabled").value, "Tak");
assert.equal(snapshot.environmentRows.some((row) => row.id === "DATABASE_URL"), false);
assert.equal(snapshot.environmentRows.some((row) => row.id === "INVOICE_S3_SECRET_ACCESS_KEY"), false);
assert.equal(snapshot.environmentRows.some((row) => row.value.includes("C:\\Users")), false);

const kpis = buildSettingsKpis(snapshot);
assert.deepEqual(kpis, {
  readOnlyMode: "Read-only",
  organizations: 1,
  users: 1,
  activeModules: 3,
  capabilities: 2,
});

const accountRows = buildAccountRows(snapshot);
assert.equal(accountRows[0].value, "Antoni CASI (antoni@casi24.com)");
assert.equal(accountRows[1].hint, "operator globalny");
assert.equal(accountRows[3].value, "Tylko podglad");
assert.equal(SETTINGS_READ_ONLY, true);
assert.equal(SETTINGS_ADMIN_ACTIONS_ENABLED, false);
assert.equal(SETTINGS_ENDPOINTS.session, "/session/current");
assert.equal(SETTINGS_ENDPOINTS.meta, "/meta");
assert.equal(SETTINGS_ENDPOINTS.organizations, "/organizations");
assert.equal(SETTINGS_ENDPOINTS.users, "/users");

assert.equal(sanitizeSettingValue("DATABASE_URL", "postgres://user:password@localhost/db"), "Ukryte");
assert.equal(sanitizeSettingValue("INVOICE_S3_SECRET_ACCESS_KEY", "secret"), "Ukryte");
assert.equal(sanitizeSettingValue("storage_root_path", "C:\\Users\\erykl\\secret"), "Ukryte");
assert.equal(sanitizeSettingValue("storage_backend", "local"), "local");

const safeRows = buildSafeEnvironmentRows({
  storage_backend: "local",
  public_base_url: "http://127.0.0.1:8000",
  token: "secret-token",
});
assert.equal(safeRows.length, 2);
assert.equal(safeRows.some((row) => row.value.includes("secret-token")), false);

const partialSnapshot = readSettingsSnapshot({
  session,
  meta: { storage_backend: "local" },
  missingSources: ["organizations", "users"],
});
assert.equal(partialSnapshot.missingSources.length, 2);
assert.equal(partialSnapshot.activeOrganization.name, "CASI Test");
assert.equal(buildSettingsKpis(partialSnapshot).organizations, 1);
assert.equal(buildSettingsKpis(partialSnapshot).users, 1);

const emptySnapshot = readSettingsSnapshot({});
assert.equal(hasSettingsData("ready", snapshot), true);
assert.equal(isSettingsEmpty("ready", emptySnapshot), true);
assert.equal(hasSettingsData("loading", snapshot), false);

assert.throws(() => readSettingsSnapshot([]), ApiContractError);
assert.throws(() => readSettingsSnapshot({ session: { login: "bez-id" } }), ApiContractError);
assert.throws(() => readSettingsSnapshot({ organizations: [{ name: "Bez ID" }] }), ApiContractError);
assert.throws(() => readSettingsSnapshot({ users: [{ login: "bez-id" }] }), ApiContractError);
assert.throws(() => buildSafeEnvironmentRows([]), ApiContractError);

assert.equal(getSettingsErrorState(new ApiError("Brak sesji", 401, {})).status, "unauthenticated");
assert.equal(getSettingsErrorState(new ApiError("Brak dostepu", 403, {})).status, "forbidden");
assert.equal(getSettingsErrorState(new ApiError("Backend padl", 500, {})).status, "server-error");
assert.equal(getSettingsErrorState(new ApiContractError("/settings", {})).title, "Niepoprawny format ustawien");

console.log("Settings regression tests passed.");
