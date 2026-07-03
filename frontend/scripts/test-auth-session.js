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
    const filePath = [".ts", ".tsx", ".js", ".jsx"]
      .map((extension) => `${resolved}${extension}`)
      .find((candidate) => fs.existsSync(candidate));

    return filePath ?? resolved;
  }

  return originalResolveFilename.call(this, request, parent, isMain, options);
};

const {
  DEFAULT_LOGIN_REDIRECT,
  LOGIN_FORM_ACTION,
  LOGIN_FORM_METHOD,
  resolveLoginRedirect,
} = require("../src/modules/auth/authModel.ts");
const { shouldClearSessionAttentionForPath, shouldShowTopbarPrimaryAction } = require("../src/layouts/appShellModel.ts");

assert.equal(LOGIN_FORM_ACTION, "/login");
assert.equal(LOGIN_FORM_METHOD, "post");
assert.equal(DEFAULT_LOGIN_REDIRECT, "/pulpit");
assert.equal(resolveLoginRedirect("/crm"), "/crm");
assert.equal(resolveLoginRedirect("/faktury/13"), "/faktury/13");
assert.equal(resolveLoginRedirect(null), "/pulpit");
assert.equal(resolveLoginRedirect(undefined), "/pulpit");
assert.equal(resolveLoginRedirect("https://example.com"), "/pulpit");
assert.equal(resolveLoginRedirect("//evil.example.com"), "/pulpit");
assert.equal(shouldClearSessionAttentionForPath("/login"), true);
assert.equal(shouldClearSessionAttentionForPath("/login?next=/pulpit-dnia"), false);
assert.equal(shouldClearSessionAttentionForPath("/pulpit-dnia"), false);
assert.equal(shouldShowTopbarPrimaryAction({ id: "work-items" }, "/work-items"), true);
assert.equal(shouldShowTopbarPrimaryAction({ id: "work-items" }, "/work-items/41"), false);
assert.equal(shouldShowTopbarPrimaryAction({ id: "daily-brief" }, "/pulpit-dnia"), true);

console.log("Auth/session regression tests passed.");
