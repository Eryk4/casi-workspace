const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const ts = require("typescript");

require.extensions[".ts"] = function compileTypeScript(module, filename) {
  const source = fs.readFileSync(filename, "utf8");
  const output = ts.transpileModule(source, {
    compilerOptions: { esModuleInterop: true, module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
    fileName: filename,
  });
  module._compile(output.outputText, filename);
};

const {
  readInternalNotificationSchedule,
  readInternalNotificationScheduleRuns,
  INTERNAL_NOTIFICATION_POLL_INTERVAL,
} = require("../src/modules/notifications/internalNotificationsModel.ts");

assert.deepEqual(readInternalNotificationSchedule({
  exists: false,
  organization_id: 42,
  recipient_user_id: 7,
  enabled: false,
  cadence: "daily",
  timezone_name: "Europe/Warsaw",
  local_time: "08:00",
  next_run_at_utc: null,
}), {
  exists: false,
  organizationId: 42,
  recipientUserId: 7,
  enabled: false,
  cadence: "daily",
  timezoneName: "Europe/Warsaw",
  localTime: "08:00",
  nextRunAtUtc: null,
});

const runs = readInternalNotificationScheduleRuns({ items: [{
  internal_notification_schedule_run_id: 8,
  status: "failed",
  scheduled_local_date: "2026-07-29",
  as_of_date: "2026-07-29",
  scheduled_for_utc: "2026-07-29T06:00:00+00:00",
  attempt_count: 3,
  candidates_count: null,
  created_count: null,
  existing_count: null,
  error_code: "materialization_failed",
  error_summary: "Nie udalo sie zmaterializowac wewnetrznych powiadomien.",
  started_at: "2026-07-29T06:00:00+00:00",
  finished_at: "2026-07-29T06:00:01+00:00",
}] });
assert.equal(runs[0].attemptCount, 3);
assert.equal(runs[0].status, "failed");
assert.doesNotMatch(runs[0].errorSummary, /Traceback|token|secret/i);
assert.equal(INTERNAL_NOTIFICATION_POLL_INTERVAL, null);
assert.throws(() => readInternalNotificationSchedule({
  organization_id: 42, recipient_user_id: 7, enabled: true, cadence: "hourly", timezone_name: "Europe/Warsaw", local_time: "08:00",
}), /czestotliwosc/);

const pageSource = fs.readFileSync(path.join(__dirname, "..", "src", "modules", "notifications", "InternalNotificationsPage.tsx"), "utf8");
assert.doesNotMatch(pageSource, /setInterval/);
assert.doesNotMatch(pageSource, /email|telegram|sms|webhook/i);
assert.match(pageSource, /Zapisz ustawienia/);
assert.match(pageSource, /saveInternalNotificationSchedule/);
assert.match(pageSource, /Sprawdź nowe powiadomienia/);

console.log("Internal notification scheduler model tests passed.");
