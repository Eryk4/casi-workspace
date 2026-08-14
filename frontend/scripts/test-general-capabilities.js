const assert = require("node:assert/strict");
const fs = require("node:fs");
const Module = require("node:module");
const path = require("node:path");
const ts = require("typescript");

for (const extension of [".ts", ".tsx"]) {
  require.extensions[extension] = function compileTypeScript(module, filename) {
    const source = fs.readFileSync(filename, "utf8");
    const output = ts.transpileModule(source, {
      compilerOptions: {
        esModuleInterop: true,
        jsx: ts.JsxEmit.ReactJSX,
        module: ts.ModuleKind.CommonJS,
        target: ts.ScriptTarget.ES2022,
      },
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

const React = require("react");
const Icon = (props) => React.createElement("svg", props);
const originalLoad = Module._load;
Module._load = function loadWithMocks(request, parent, isMain) {
  if (request === "next/link") {
    return function Link({ children, href, ...props }) {
      return React.createElement("a", { ...props, href }, children);
    };
  }
  if (request === "lucide-react") {
    return new Proxy({}, { get: () => Icon });
  }
  return originalLoad.call(this, request, parent, isMain);
};

const { renderToStaticMarkup } = require("react-dom/server");
const {
  filterNavigationItemsByCapabilities,
  navigationItems,
} = require("../src/config/navigation.ts");
const { Sidebar } = require("../src/layouts/Sidebar.tsx");

const expectedByRole = {
  system_owner: ["Automatyzacje", "Rozliczenia", "Work Items"],
  organization_admin: ["Automatyzacje", "Rozliczenia", "Work Items"],
  coordinator: ["Automatyzacje", "Work Items"],
  operator: ["Work Items"],
  guest: [],
};
const capabilitiesByRole = {
  system_owner: ["work_items.read", "billing.read", "automation.read"],
  organization_admin: ["work_items.read", "billing.read", "automation.read"],
  coordinator: ["work_items.read", "automation.read"],
  operator: ["work_items.read"],
  guest: [],
};

for (const role of Object.keys(expectedByRole)) {
  const visible = filterNavigationItemsByCapabilities(navigationItems, capabilitiesByRole[role]);
  const protectedLabels = visible
    .filter((item) => item.requiredCapabilities?.length)
    .map((item) => item.label)
    .sort();
  assert.deepEqual(protectedLabels, expectedByRole[role].slice().sort(), role);

  const markup = renderToStaticMarkup(
    React.createElement(Sidebar, {
      activePath: "/pulpit",
      capabilities: capabilitiesByRole[role],
      collapsed: false,
      onToggleCollapsed: () => {},
    }),
  );
  for (const label of ["Automatyzacje", "Rozliczenia", "Work Items"]) {
    const expected = expectedByRole[role].includes(label);
    assert.equal(markup.includes(`>${label}<`), expected, `${role}: ${label}`);
  }
  assert.match(markup, />Pulpit</);
}

const synthetic = [
  { ...navigationItems[0], id: "synthetic", requiredCapabilities: ["one", "two"] },
];
assert.equal(filterNavigationItemsByCapabilities(synthetic, ["one"]).length, 0);
assert.equal(filterNavigationItemsByCapabilities(synthetic, ["one", "two"]).length, 1);

console.log("General capability navigation and Sidebar tests passed.");
