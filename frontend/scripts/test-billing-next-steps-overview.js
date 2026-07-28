const assert = require("node:assert/strict");
const fs = require("node:fs");
const Module = require("node:module");
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

const srcRoot = path.join(__dirname, "..", "src");
const originalResolveFilename = Module._resolveFilename;
Module._resolveFilename = function resolveAlias(request, parent, isMain, options) {
  if (request.startsWith("@/")) {
    const resolved = path.join(srcRoot, request.slice(2));
    return [".ts", ".tsx", ".js", ".jsx"].map((extension) => `${resolved}${extension}`).find(fs.existsSync) ?? resolved;
  }
  return originalResolveFilename.call(this, request, parent, isMain, options);
};

const {
  BILLING_NEXT_STEPS_OVERVIEW_ROUTE,
  buildBillingNextStepsOverview,
  readBillingActiveNextStepEvents,
} = require("../src/modules/billing/billingModel.ts");

const base = {
  targetType: "billing_summary",
  stepType: "other",
  eventAction: "planned",
  title: "Identyczny krok",
};
const events = [
  { ...base, eventId: 10, plannedFor: "2026-12-17", createdAt: "2026-12-01T10:00:00" },
  { ...base, eventId: 11, plannedFor: "2026-12-18", createdAt: "2026-12-01T10:00:00" },
  { ...base, eventId: 12, plannedFor: "2026-12-20", createdAt: "2026-12-01T10:00:00" },
  { ...base, eventId: 13, plannedFor: "2026-12-25", createdAt: "2026-12-01T10:00:00" },
  { ...base, eventId: 14, plannedFor: "2026-12-26", createdAt: "2026-12-01T10:00:00" },
  { ...base, eventId: 15, createdAt: "2026-12-01T10:00:00" },
  { ...base, eventId: 16, plannedFor: "2026-12-20", createdAt: "2026-12-01T09:00:00" },
  { ...base, eventId: 17, plannedFor: "2026-12-20", createdAt: "2026-12-01T09:00:00" },
  { ...base, eventId: 18, plannedFor: "2026-12-20", createdAt: "2026-12-01T09:00:00" },
  { ...base, eventId: 19, eventAction: "completed", parentEventId: 17 },
  { ...base, eventId: 20, eventAction: "completed" },
  { ...base, eventId: 21, targetType: "payer", targetId: 7, title: "Płatnik" },
  { ...base, eventId: 22, targetType: "payment", targetId: 8, title: "Wpłata" },
  { ...base, eventId: 23, targetType: "work_queue_issue", relatedIssueKey: "issue:1", title: "Sprawa" },
  { ...base, eventId: 24, targetType: "future_target", targetId: 9, title: "Nieznany" },
];

const view = buildBillingNextStepsOverview(events, { today: "2026-12-18" });
assert.equal(view.counts.all, 12);
assert.equal(view.counts.overdue, 1);
assert.equal(view.counts.today, 1);
assert.equal(view.counts["next-7-days"], 4);
assert.equal(view.counts.later, 1);
assert.equal(view.counts["no-date"], 5);
assert.deepEqual(view.allRows.slice(0, 7).map((row) => row.eventId), [10, 11, 16, 18, 12, 13, 14]);
assert.ok(view.allRows.some((row) => row.eventId === 16));
assert.ok(view.allRows.some((row) => row.eventId === 18));
assert.ok(!view.allRows.some((row) => row.eventId === 17));
assert.equal(view.allRows.filter((row) => row.title === "Identyczny krok" && row.eventId !== 17).length, 8);

const payer = view.allRows.find((row) => row.eventId === 21);
const payment = view.allRows.find((row) => row.eventId === 22);
const issue = view.allRows.find((row) => row.eventId === 23);
const unknown = view.allRows.find((row) => row.eventId === 24);
assert.equal(payer.targetHref, "/rozliczenia/platnicy/7");
assert.equal(payment.targetHref, "/rozliczenia/wplaty/8");
assert.equal(issue.targetHref, "/rozliczenia/sprawy");
assert.equal(unknown.targetHref, undefined);
assert.equal(unknown.completionTargetType, undefined);
assert.match(unknown.targetLabel, /historyczny cel/);

const filtered = buildBillingNextStepsOverview(events, { filter: "today", today: "2026-12-18" });
assert.deepEqual(filtered.filteredRows.map((row) => row.eventId), [11]);

const parsed = readBillingActiveNextStepEvents({
  organization_id: 42,
  events: [{
    billing_next_step_event_id: 31,
    organization_id: 42,
    target_type: "future_target",
    target_id: 999,
    step_type: "other",
    event_action: "planned",
    title: "Historyczny cel",
  }],
});
assert.equal(parsed.events[0].targetType, "future_target");
assert.equal(BILLING_NEXT_STEPS_OVERVIEW_ROUTE, "/rozliczenia/kroki");

const billingNavigationSource = fs.readFileSync(path.join(srcRoot, "modules", "billing", "BillingLedgerOverview.tsx"), "utf8");
assert.match(billingNavigationSource, /Następne kroki/);
assert.match(billingNavigationSource, /BILLING_NEXT_STEPS_OVERVIEW_ROUTE/);

console.log("Billing next steps overview model tests passed.");
