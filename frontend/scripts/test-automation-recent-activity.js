const assert = require("node:assert/strict");
const fs = require("node:fs");
const ts = require("typescript");

require.extensions[".ts"] = function compileTypeScript(module, filename) {
  const output = ts.transpileModule(fs.readFileSync(filename, "utf8"), {
    compilerOptions: { esModuleInterop: true, module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
    fileName: filename,
  });
  module._compile(output.outputText, filename);
};

const model = require("../src/modules/automations/automationOperationsModel.ts");
const types = ["scheduled_check", "delivery", "processing", "import", "import", "execution", "delivery", "processing"];
const statuses = ["succeeded", "failed", "partial", "succeeded", "failed", "partial", "succeeded", "failed"];
const keys = ["internal_notification_scheduler", "task_reminders", "knowledge_processing", "email_import", "ksef_import", "automation_engine", "task_reminders", "knowledge_processing"];
const payload = {
  limit: 8,
  items: keys.map((automationKey, index) => ({
    activity_id: `${automationKey}:source:${index + 1}`,
    automation_key: automationKey,
    title: `Adapter ${index + 1}`,
    activity_type: types[index],
    status: statuses[index],
    occurred_at: `2026-08-13T1${9 - index}:00:00+00:00`,
    summary: `Bezpieczne podsumowanie ${index + 1}.`,
    details_url: `/automatyzacje/${automationKey}`,
  })),
};

const parsed = model.readAutomationActivity(payload);
assert.equal(parsed.limit, 8);
assert.equal(parsed.items.length, 8);
assert.deepEqual(parsed.items.map((item) => item.activityType), types);
assert.deepEqual(parsed.items.map((item) => item.status), statuses);
assert.equal(parsed.items[0].activityId, "internal_notification_scheduler:source:1");
assert.equal(parsed.items[0].occurredAt, "2026-08-13T19:00:00+00:00");
assert.equal(model.automationActivityStatusLabel("succeeded"), "Zakończono");
assert.equal(model.automationActivityStatusLabel("failed"), "Nieudane");
assert.equal(model.automationActivityStatusLabel("partial"), "Z problemami");
for (const item of parsed.items) assert.ok(!JSON.stringify(item).match(/payload|raw_error|source_id|metadata/i));

for (const malformed of [
  { items: [], limit: 0 },
  { items: [], limit: 21 },
  { items: [{ ...payload.items[0], status: "running" }], limit: 8 },
  { items: [{ ...payload.items[0], activity_type: "heartbeat" }], limit: 8 },
  { items: [{ ...payload.items[0], occurred_at: "2026-08-13 19:00:00" }], limit: 8 },
  { items: [{ ...payload.items[0], details_url: "https://example.test/private" }], limit: 8 },
]) assert.throws(() => model.readAutomationActivity(malformed), /kontrakt|ścieżka|bezpieczny link/i);

console.log("Automation recent activity model tests passed.");
