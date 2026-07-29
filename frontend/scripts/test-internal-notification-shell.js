const assert = require("node:assert/strict");
const fs = require("node:fs");
const Module = require("node:module");
const path = require("node:path");
const ts = require("typescript");

for (const extension of [".ts", ".tsx"]) {
  require.extensions[extension] = function compileTypeScript(module, filename) {
    const source = fs.readFileSync(filename, "utf8");
    const output = ts.transpileModule(source, {
      compilerOptions: { esModuleInterop: true, jsx: ts.JsxEmit.ReactJSX, module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
      fileName: filename,
    });
    module._compile(output.outputText, filename);
  };
}

const srcRoot = path.join(__dirname, "..", "src");
const originalResolveFilename = Module._resolveFilename;
Module._resolveFilename = function resolveAlias(request, parent, isMain, options) {
  if (request.startsWith("@/")) {
    const resolved = path.join(srcRoot, request.slice(2));
    return [".ts", ".tsx", ".js", ".jsx"].map((extension) => `${resolved}${extension}`).find(fs.existsSync) ?? resolved;
  }
  return originalResolveFilename.call(this, request, parent, isMain, options);
};

let unreadCount = 123;
const originalLoad = Module._load;
Module._load = function loadWithMocks(request, parent, isMain) {
  if (request === "next/link") {
    return function Link({ children, href, ...props }) {
      const React = require("react");
      return React.createElement("a", { ...props, href }, children);
    };
  }
  if (request === "lucide-react") {
    const React = require("react");
    const Icon = (props) => React.createElement("svg", props);
    return { Bell: Icon, CircleHelp: Icon, Plus: Icon, RefreshCw: Icon, Search: Icon };
  }
  if (request === "@/context/ActiveOrganizationContext" || request.endsWith(`${path.sep}context${path.sep}ActiveOrganizationContext.tsx`)) {
    return {
      useActiveOrganization: () => ({
        error: null,
        organizations: [{ id: "42", name: "CASI", isActive: true }],
        selectedOrganizationId: "42",
        selectOrganization: () => {},
        status: "ready",
      }),
    };
  }
  if (request === "@/context/InternalNotificationCountContext" || request.endsWith(`${path.sep}context${path.sep}InternalNotificationCountContext.tsx`)) {
    return { useInternalNotificationCount: () => ({ unreadCount }) };
  }
  return originalLoad.call(this, request, parent, isMain);
};

const React = require("react");
const { renderToStaticMarkup } = require("react-dom/server");
const { Topbar } = require("../src/layouts/Topbar.tsx");

const currentModule = {
  id: "notifications",
  label: "Powiadomienia",
  href: "/powiadomienia",
  icon: () => null,
  description: "Centrum",
  readiness: "live",
  readinessLabel: "Aktywne",
};
let markup = renderToStaticMarkup(React.createElement(Topbar, { currentModule, pathname: "/powiadomienia" }));
assert.match(markup, /href="\/powiadomienia"/);
assert.match(markup, />99\+<\/span>/);

unreadCount = 0;
markup = renderToStaticMarkup(React.createElement(Topbar, { currentModule, pathname: "/powiadomienia" }));
assert.doesNotMatch(markup, />99\+<\/span>/);

const navigationSource = fs.readFileSync(path.join(srcRoot, "config", "navigation.ts"), "utf8");
const appShellSource = fs.readFileSync(path.join(srcRoot, "layouts", "AppShell.tsx"), "utf8");
assert.match(navigationSource, /id: "notifications"/);
assert.match(navigationSource, /path: "\/powiadomienia"/);
assert.match(appShellSource, /InternalNotificationCountProvider/);
assert.match(appShellSource, /<InternalNotificationCountProvider>[\s\S]*<AppShellFrame/);

console.log("Internal notification AppShell tests passed.");
