const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const ts = require("typescript");

for (const extension of [".ts", ".tsx"]) {
  require.extensions[extension] = function compileTypeScript(module, filename) {
    const output = ts.transpileModule(fs.readFileSync(filename, "utf8"), { compilerOptions: { esModuleInterop: true, jsx: ts.JsxEmit.ReactJSX, module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 }, fileName: filename });
    module._compile(output.outputText, filename);
  };
}

const { readTodayTasks, todayTaskBucketLabel } = require("../src/modules/daily-brief/todayTasksModel.ts");
const { readTodayBilling, todayBillingBucketLabel } = require("../src/modules/daily-brief/todayBillingModel.ts");
const { formatTodayHeadingDate, resolveTodaySections } = require("../src/modules/daily-brief/todayDashboardModel.ts");

const tasks = readTodayTasks({ counts: { overdue: 2, today: 1, upcoming: 4 }, items: [
  { task_id: 7, title: "Telefon do klienta", due_at: "2026-08-17T09:00:00+00:00", bucket: "today", details_url: "/work-items/7" },
] });
assert.deepEqual(tasks.counts, { overdue: 2, today: 1, upcoming: 4 });
assert.equal(tasks.items[0].taskId, 7);
assert.equal(todayTaskBucketLabel("overdue"), "Po terminie");
assert.throws(() => readTodayTasks({ counts: { overdue: 0, today: 0, upcoming: 0 }, items: Array(6).fill({ task_id: 1, title: "x", due_at: null, bucket: "today", details_url: "/work-items/1" }) }), /items/);
assert.throws(() => readTodayTasks({ counts: { overdue: 0, today: 0, upcoming: 0 }, items: [{ task_id: 1, title: "x", due_at: null, bucket: "today", details_url: "https://evil.example" }] }), /details_url/);
assert.throws(() => readTodayTasks({ counts: { overdue: 0, today: 0, upcoming: 0 }, items: [{ task_id: 0, title: "x", due_at: "not-a-date", bucket: "today", details_url: "/work-items/0" }] }), /due_at|task_id/);

const billing = readTodayBilling({ overdue_count: 1, due_today_count: 2, items: [
  { billing_next_step_event_id: 9, title: "Wyślij przypomnienie", planned_for: "2026-08-17", bucket: "overdue", details_url: "/rozliczenia/kroki" },
] });
assert.equal(billing.items[0].billingNextStepEventId, 9);
assert.equal(todayBillingBucketLabel("today"), "Dzisiaj");
assert.throws(() => readTodayBilling({ overdue_count: 0, due_today_count: 0, items: [{ billing_next_step_event_id: 1, title: "x", planned_for: "17.08.2026", bucket: "today", details_url: "/x" }] }), /planned_for/);
assert.throws(() => readTodayBilling({ overdue_count: 0, due_today_count: 0, items: [{ billing_next_step_event_id: 1, title: "x", planned_for: "2026-02-31", bucket: "today", details_url: "/x" }] }), /planned_for/);

assert.deepEqual(resolveTodaySections(["automation.read", "work_items.read", "billing.read"]), { attention: true, tasks: true, billing: true, activity: true });
assert.deepEqual(resolveTodaySections(["automation.read", "work_items.read"]), { attention: true, tasks: true, billing: false, activity: true });
assert.deepEqual(resolveTodaySections(["work_items.read"]), { attention: false, tasks: true, billing: false, activity: false });
assert.deepEqual(resolveTodaySections([]), { attention: false, tasks: false, billing: false, activity: false });
const roleMatrix = {
  system_owner: ["automation.read", "work_items.read", "billing.read"],
  organization_admin: ["automation.read", "work_items.read", "billing.read"],
  coordinator: ["automation.read", "work_items.read"],
  operator: ["work_items.read"],
  guest: [],
};
assert.deepEqual(Object.fromEntries(Object.entries(roleMatrix).map(([role, values]) => [role, Object.values(resolveTodaySections(values)).filter(Boolean).length])), { system_owner: 4, organization_admin: 4, coordinator: 3, operator: 1, guest: 0 });
assert.match(formatTodayHeadingDate(new Date(2026, 7, 17, 12)), /^Poniedziałek, 17 sierpnia$/);

const pageSource = fs.readFileSync(path.join(__dirname, "..", "src", "modules", "daily-brief", "DailyBriefPage.tsx"), "utf8");
for (const required of ["api.todayTasks", "api.todayBilling", "api.automationOperations", "api.automationOperationsActivity", "limit: 3"]) assert.ok(pageSource.includes(required));
for (const forbidden of ["api.dashboard(", "api.taskFocus", "api.workItems", "api.invoiceVerificationInbox", "api.ledgerBalances", "api.contractors", "api.knowledgeDocuments", "setInterval"]) assert.ok(!pageSource.includes(forbidden), `Pulpit Dzisiaj nie może używać: ${forbidden}`);
assert.ok(pageSource.indexOf("<AttentionSection") < pageSource.indexOf("<TasksSection"));
assert.ok(pageSource.indexOf("<TasksSection") < pageSource.indexOf("<BillingSection"));
assert.ok(pageSource.indexOf("<BillingSection") < pageSource.indexOf("<ActivitySection"));

const navigation = fs.readFileSync(path.join(__dirname, "..", "src", "config", "navigation.ts"), "utf8");
assert.ok(navigation.indexOf('id: "daily-brief"') < navigation.indexOf('id: "dashboard"'));
assert.match(navigation, /id: "daily-brief"[\s\S]*label: "Dzisiaj"/);
assert.match(fs.readFileSync(path.join(__dirname, "..", "src", "app", "page.tsx"), "utf8"), /redirect\("\/pulpit-dnia"\)/);

console.log("Today dashboard model tests passed.");
