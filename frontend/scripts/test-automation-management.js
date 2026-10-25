const assert = require("node:assert/strict");
const fs = require("node:fs");
const Module = require("node:module");
const path = require("node:path");
const ts = require("typescript");

require.extensions[".ts"] = function compileTypeScript(module, filename) {
  const output = ts.transpileModule(fs.readFileSync(filename, "utf8"), {
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

const { ApiContractError, ApiError } = require("../src/lib/api.ts");
const {
  automationActionLabel,
  automationConditionLabel,
  automationTriggerLabel,
  emptyAutomationRuleDraft,
  hasAutomationManage,
  isAutomationCatalogSupported,
  readAutomationCatalog,
  readAutomationRules,
  resetConditionsForTrigger,
  readAutomationValidationError,
  supportedManagementActions,
  validateAutomationRuleDraft,
} = require("../src/modules/automations/automationManagementModel.ts");

function catalogFixture() {
  return {
    version: 1,
    triggers: [
      { key: "invoice_status_changed", label_key: "automation.trigger.invoice_status_changed", condition_fields: [
        { key: "source", type: "string", operators: ["equals"], max_length: 120 },
        { key: "status_after", type: "string", operators: ["equals"], max_length: 120 },
      ] },
      { key: "work_item_created", label_key: "automation.trigger.work_item_created", condition_fields: [
        { key: "status_after", type: "string", operators: ["equals"], max_length: 120 },
      ] },
    ],
    actions: [
      { key: "create_inbox_item", label_key: "automation.action.create_inbox_item", fields: [
        { key: "title", type: "string", required: true, max_length: 200 },
        { key: "description", type: "string", required: false, max_length: 2000 },
      ] },
    ],
    constraints: { min_actions: 1, max_actions: 1, max_conditions: 3 },
  };
}

const catalog = readAutomationCatalog(catalogFixture());
assert.equal(catalog.version, 1);
assert.equal(isAutomationCatalogSupported(catalog), true);
assert.equal(automationTriggerLabel(catalog.triggers[0]), "Zmiana statusu faktury");
assert.equal(automationConditionLabel("status_after"), "Nowy status");
assert.equal(automationActionLabel(catalog.actions[0]), "Utwórz powiadomienie w CASI");
assert.equal(supportedManagementActions(catalog).length, 1);
assert.equal(hasAutomationManage(["automation.read", "automation.manage"]), true);
assert.equal(hasAutomationManage(["automation.read"]), false);
assert.deepEqual(
  {
    system_owner: hasAutomationManage(["automation.read", "automation.manage"]),
    organization_admin: hasAutomationManage(["automation.read", "automation.manage"]),
    coordinator: hasAutomationManage(["automation.read"]),
    operator: hasAutomationManage([]),
    guest: hasAutomationManage([]),
  },
  { system_owner: true, organization_admin: true, coordinator: false, operator: false, guest: false },
);

for (const malformed of [
  { ...catalogFixture(), version: 2 },
  { ...catalogFixture(), triggers: [{ key: "x" }] },
  { ...catalogFixture(), actions: [{ key: "x", label_key: "x", fields: [{ key: "x", required: true, max_length: 1 }] }] },
  { ...catalogFixture(), constraints: { min_actions: 2, max_actions: 1, max_conditions: 3 } },
]) {
  assert.throws(() => readAutomationCatalog(malformed), ApiContractError);
}

const unsupportedFieldType = readAutomationCatalog({
  ...catalogFixture(),
  triggers: [{
    ...catalogFixture().triggers[0],
    condition_fields: [{ key: "source", type: "number", operators: ["equals"], max_length: 120 }],
  }],
});
assert.equal(isAutomationCatalogSupported(unsupportedFieldType), false);

const withUnsupportedAction = readAutomationCatalog({
  ...catalogFixture(),
  actions: [...catalogFixture().actions, { key: "log", label_key: "automation.action.log", fields: [] }],
});
assert.deepEqual(supportedManagementActions(withUnsupportedAction).map((item) => item.key), ["create_inbox_item"]);

const rules = readAutomationRules([{ automation_rule_id: 9, rule_name: "Powiadomienie", rule_slug: "hidden", description: null, trigger_event_type: "work_item_created", is_active: false, last_run_at: null, execution_count: 0, created_at: "2026-01-01T00:00:00Z", updated_at: "2026-01-01T00:00:00Z" }]);
assert.deepEqual(rules[0], { id: 9, name: "Powiadomienie", description: null, triggerKey: "work_item_created", active: false, lastRunAt: null, executionCount: 0, updatedAt: "2026-01-01T00:00:00Z" });
assert.throws(() => readAutomationRules([{ ...rules[0], automation_rule_id: 9, rule_name: "x", trigger_event_type: "x", is_active: false, last_run_at: null, execution_count: 0, updated_at: null, conditions_json: {} }]), ApiContractError);

const validDraft = {
  ...emptyAutomationRuleDraft(),
  name: "Powiadom o zadaniu",
  description: "Opis",
  triggerKey: "work_item_created",
  conditions: [{ fieldKey: "status_after", operator: "equals", value: "nowe" }],
  actionKey: "create_inbox_item",
  actionValues: { title: "Nowe zadanie", description: "Sprawdź zadanie" },
};
const validation = validateAutomationRuleDraft(catalog, validDraft);
assert.deepEqual(validation.errors, {});
assert.deepEqual(validation.payload, {
  rule_name: "Powiadom o zadaniu",
  description: "Opis",
  trigger_event_type: "work_item_created",
  conditions_json: { status_after: "nowe" },
  actions_json: [{ type: "create_inbox_item", title: "Nowe zadanie", description: "Sprawdź zadanie" }],
  is_active: false,
});

const noCondition = validateAutomationRuleDraft(catalog, { ...validDraft, conditions: [] });
assert.deepEqual(noCondition.payload.conditions_json, {});
assert.equal(noCondition.payload.actions_json.length, 1);

const reset = resetConditionsForTrigger(validDraft, "invoice_status_changed");
assert.equal(reset.triggerKey, "invoice_status_changed");
assert.deepEqual(reset.conditions, []);

const invalidField = validateAutomationRuleDraft(catalog, { ...validDraft, conditions: [{ fieldKey: "source", operator: "equals", value: "TEST" }] });
assert.equal(invalidField.payload, null);
assert.ok(invalidField.errors["conditions_json.0"]);

const catalogWithoutInvoice = readAutomationCatalog({ ...catalogFixture(), triggers: catalogFixture().triggers.slice(1) });
assert.deepEqual(catalogWithoutInvoice.triggers.map((item) => item.key), ["work_item_created"]);
assert.deepEqual(
  readAutomationValidationError(new ApiError("invalid", 400, { field: "actions[0].title", error: "Tytuł jest wymagany." })),
  { field: "actions_json.title", message: "Tytuł jest wymagany." },
);

console.log("Automation management model tests passed.");
