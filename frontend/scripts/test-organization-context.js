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
  ACTIVE_ORGANIZATION_STORAGE_KEY,
  buildFallbackOrganization,
  isAuthenticatedSession,
  mergeOrganizationOptions,
  readOrganizations,
  readSessionOrganizationSnapshot,
  resolveOrganizationContext,
  resolveInitialOrganizationId,
  withActiveOrganizationQuery,
} = require("../src/context/organizationContextModel.ts");

assert.equal(ACTIVE_ORGANIZATION_STORAGE_KEY, "casi.activeOrganizationId");

const flatSession = readSessionOrganizationSnapshot({
  organization_id: 1,
  organization_name: "CASI",
  is_global_admin: false,
});
assert.deepEqual(flatSession, {
  organizationId: "1",
  organizationName: "CASI",
  isGlobalAdmin: false,
});

const nestedSession = readSessionOrganizationSnapshot({
  user: {
    organization_id: "2",
    organization_name: "Misja Robotyka",
    is_global_admin: true,
  },
});
assert.equal(nestedSession.organizationId, "2");
assert.equal(nestedSession.isGlobalAdmin, true);
assert.equal(isAuthenticatedSession({ user_id: 1, login: "admin" }), true);
assert.equal(isAuthenticatedSession({ authenticated: false }), false);
assert.equal(isAuthenticatedSession(null), false);

const organizations = readOrganizations([
  { organization_id: 1, name: "CASI", slug: "casi", is_active: 1 },
  { organization_id: 2, name: "Misja Robotyka", is_active: true },
  { organization_id: 3, name: "Archiwum", is_active: 0 },
]);
assert.deepEqual(
  organizations.map((organization) => organization.id),
  ["1", "2"],
);
assert.equal(organizations[0].name, "CASI");

const envelopedOrganizations = readOrganizations({ value: [{ id: "9", organization_name: "Alfa" }] });
assert.equal(envelopedOrganizations[0].id, "9");
assert.equal(envelopedOrganizations[0].name, "Alfa");

assert.throws(() => readOrganizations({ items: [] }), ApiContractError);
assert.throws(() => readOrganizations([{ name: "Bez ID" }]), ApiContractError);

const fallback = buildFallbackOrganization(flatSession);
assert.deepEqual(fallback, {
  id: "1",
  name: "CASI",
  isActive: true,
});

assert.deepEqual(mergeOrganizationOptions([], fallback), [fallback]);
assert.deepEqual(mergeOrganizationOptions(organizations, fallback), organizations);

assert.equal(
  resolveInitialOrganizationId({
    organizations: [organizations[0]],
    sessionOrganizationId: null,
    storedOrganizationId: null,
    isGlobalAdmin: true,
  }),
  "1",
);
assert.equal(
  resolveInitialOrganizationId({
    organizations,
    sessionOrganizationId: "1",
    storedOrganizationId: null,
    isGlobalAdmin: false,
  }),
  "1",
);
assert.equal(
  resolveInitialOrganizationId({
    organizations,
    sessionOrganizationId: null,
    storedOrganizationId: "2",
    isGlobalAdmin: true,
  }),
  "2",
);
assert.equal(
  resolveInitialOrganizationId({
    organizations,
    sessionOrganizationId: null,
    storedOrganizationId: "404",
    isGlobalAdmin: true,
  }),
  null,
);
assert.equal(
  resolveInitialOrganizationId({
    organizations,
    sessionOrganizationId: null,
    storedOrganizationId: null,
    isGlobalAdmin: true,
  }),
  null,
);

const successfulContext = resolveOrganizationContext({
  sessionResult: {
    status: "fulfilled",
    value: {
      user_id: 1,
      login: "owner",
      organization_id: null,
      is_global_admin: true,
    },
  },
  organizationsResult: {
    status: "fulfilled",
    value: organizations,
  },
  storedOrganizationId: "2",
});
assert.equal(successfulContext.status, "ready");
assert.equal(successfulContext.selectedOrganizationId, "2");
assert.equal(successfulContext.error, null);
assert.equal(successfulContext.shouldClearStoredOrganization, false);

const singleOrganizationContext = resolveOrganizationContext({
  sessionResult: {
    status: "fulfilled",
    value: {
      user_id: 2,
      login: "operator",
      organization_id: "1",
      organization_name: "CASI",
      is_global_admin: false,
    },
  },
  organizationsResult: {
    status: "fulfilled",
    value: [organizations[0]],
  },
  storedOrganizationId: null,
});
assert.equal(singleOrganizationContext.status, "ready");
assert.equal(singleOrganizationContext.selectedOrganizationId, "1");

const staleStoredOrganizationContext = resolveOrganizationContext({
  sessionResult: {
    status: "fulfilled",
    value: {
      user_id: 3,
      login: "owner",
      organization_id: null,
      is_global_admin: true,
    },
  },
  organizationsResult: {
    status: "fulfilled",
    value: organizations,
  },
  storedOrganizationId: "404",
});
assert.equal(staleStoredOrganizationContext.status, "ready");
assert.equal(staleStoredOrganizationContext.selectedOrganizationId, null);
assert.equal(staleStoredOrganizationContext.shouldClearStoredOrganization, true);

const unauthenticatedContext = resolveOrganizationContext({
  sessionResult: {
    status: "rejected",
    reason: new ApiError("Brak sesji", 401, {}),
  },
  organizationsResult: {
    status: "rejected",
    reason: new ApiError("Brak sesji", 401, {}),
  },
  storedOrganizationId: "1",
});
assert.equal(unauthenticatedContext.status, "unauthenticated");
assert.equal(unauthenticatedContext.error.title, "Sesja wygasla");
assert.equal(unauthenticatedContext.shouldClearStoredOrganization, true);

const missingOrganizationsContext = resolveOrganizationContext({
  sessionResult: {
    status: "fulfilled",
    value: {
      user_id: 4,
      login: "global",
      organization_id: null,
      is_global_admin: true,
    },
  },
  organizationsResult: {
    status: "rejected",
    reason: new ApiError("Backend padl", 500, {}),
  },
  storedOrganizationId: null,
});
assert.equal(missingOrganizationsContext.status, "error");
assert.equal(missingOrganizationsContext.error.title, "Nie udalo sie pobrac organizacji");
assert.equal(missingOrganizationsContext.organizations.length, 0);

const fallbackOrganizationContext = resolveOrganizationContext({
  sessionResult: {
    status: "fulfilled",
    value: {
      user_id: 5,
      login: "operator",
      organization_id: "1",
      organization_name: "CASI",
      is_global_admin: false,
    },
  },
  organizationsResult: {
    status: "rejected",
    reason: new ApiError("Brak dostepu", 403, {}),
  },
  storedOrganizationId: null,
});
assert.equal(fallbackOrganizationContext.status, "ready");
assert.equal(fallbackOrganizationContext.organizations.length, 1);
assert.equal(fallbackOrganizationContext.selectedOrganizationId, "1");
assert.equal(fallbackOrganizationContext.error.title, "Nie udalo sie pobrac organizacji");

assert.deepEqual(withActiveOrganizationQuery("2", { limit: 100, only_open: 1 }), {
  limit: 100,
  only_open: 1,
  organization_id: "2",
});
assert.deepEqual(withActiveOrganizationQuery(null, { limit: 100 }), {
  limit: 100,
});

console.log("Organization context regression tests passed.");
