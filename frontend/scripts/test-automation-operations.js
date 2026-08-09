const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const ts = require("typescript");

require.extensions[".ts"] = function compileTypeScript(module, filename) {
  const output = ts.transpileModule(fs.readFileSync(filename, "utf8"), {
    compilerOptions: { esModuleInterop: true, module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
    fileName: filename,
  });
  module._compile(output.outputText, filename);
};

const model = require("../src/modules/automations/automationOperationsModel.ts");

function operation(overrides = {}) {
  return {
    automation_key: "internal_notification_scheduler",
    automation_type: "scheduler",
    title: "Automatyczne sprawdzanie powiadomień",
    description: "Opis",
    status: "enabled",
    enabled: true,
    health: "healthy",
    health_reason_code: "last_run_succeeded",
    schedule_id: 1,
    run_id: 2,
    next_run_at: "2026-01-16T07:00:00+00:00",
    last_run_at: "2026-01-15T07:00:00+00:00",
    last_run_status: "succeeded",
    last_run_duration_ms: 1000,
    last_attempt_count: 1,
    last_candidates_count: 4,
    last_created_count: 2,
    last_existing_count: 2,
    recent_failure_count: 0,
    last_error_code: null,
    last_error_summary: null,
    settings_url: "/powiadomienia",
    details_url: "/automatyzacje/internal_notification_scheduler",
    runtime_status: "unknown",
    schedule: { cadence: "daily", timezone_name: "Europe/Warsaw", local_time: "08:00" },
    updated_at: "2026-01-15T07:00:01+00:00",
    ...overrides,
  };
}

const parsed = model.readAutomationOperationsDashboard({
  summary: { active_count: 2, disabled_count: 2, attention_count: 1, recent_failure_count: 3 },
  items: [
    operation(),
    operation({ automation_key: "failed", status: "enabled", health: "attention" }),
    operation({ automation_key: "disabled", status: "disabled", enabled: false, health: "disabled" }),
    operation({ automation_key: "new", status: "not_configured", enabled: false, health: "disabled" }),
  ],
});
assert.equal(parsed.items.length, 4);
assert.equal(model.filterAutomationOperations(parsed.items, "active").length, 2);
assert.equal(model.filterAutomationOperations(parsed.items, "disabled").length, 2);
assert.deepEqual(model.filterAutomationOperations(parsed.items, "attention").map((item) => item.automationKey), ["failed"]);
assert.equal(model.AUTOMATION_OPERATIONS_POLL_INTERVAL, null);
assert.equal(model.automationHealthLabel("never_run"), "Jeszcze nie uruchomiono");

const detail = model.readAutomationOperationDetail({
  item: operation(),
  history_limit: 20,
  history: [{
    run_id: 2, schedule_id: 1, scheduled_local_date: "2026-01-15", as_of_date: "2026-01-15",
    scheduled_for_utc: "2026-01-15T07:00:00+00:00", status: "succeeded", attempt_count: 1,
    candidates_count: 4, created_count: 2, existing_count: 2, error_code: null, error_summary: null,
    started_at: "2026-01-15T07:00:00+00:00", finished_at: "2026-01-15T07:00:01+00:00", duration_ms: 1000,
  }],
});
assert.equal(detail.history[0].durationMs, 1000);
assert.throws(() => model.readAutomationOperationsDashboard({ summary: {}, items: [] }), /kontrakt/i);
assert.throws(() => model.readAutomationOperationsDashboard({ summary: { active_count: 0, disabled_count: 0, attention_count: 0, recent_failure_count: 0 }, items: [operation({ settings_url: "https://evil.test" })] }), /bezpieczny link/i);

const apiSource = fs.readFileSync(path.join(__dirname, "..", "src", "lib", "api.ts"), "utf8");
const pageSource = fs.readFileSync(path.join(__dirname, "..", "src", "modules", "automations", "AutomationOperationsPage.tsx"), "utf8");
const detailSource = fs.readFileSync(path.join(__dirname, "..", "src", "modules", "automations", "AutomationOperationDetailPage.tsx"), "utf8");
const navigationSource = fs.readFileSync(path.join(__dirname, "..", "src", "config", "navigation.ts"), "utf8");
assert.match(apiSource, /automationOperations:[\s\S]*apiRequest[\s\S]*\/automations\/operations/);
assert.doesNotMatch(pageSource + detailSource, /setInterval|Uruchom teraz|method:\s*["']POST["']/);
assert.match(pageSource, /setDashboard\(null\)/);
assert.match(detailSource, /Nieznany — centrum nie monitoruje procesu workera/);
assert.match(navigationSource, /id:\s*["']automations["'][\s\S]*label:\s*["']Automatyzacje["'][\s\S]*path:\s*["']\/automatyzacje["']/);
assert.doesNotMatch(JSON.stringify(parsed), /recipient_user_id|lease_token/);

console.log("Automation operations model tests passed.");
