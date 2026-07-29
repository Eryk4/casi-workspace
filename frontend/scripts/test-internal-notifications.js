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
  emptyStateCopy,
  formatUnreadCount,
  INTERNAL_NOTIFICATION_BILLING_ACTIONS,
  INTERNAL_NOTIFICATION_FILTERS,
  INTERNAL_NOTIFICATION_POLL_INTERVAL,
  INTERNAL_NOTIFICATION_WRITE_ACTIONS,
  readInternalNotificationPage,
  readMaterializationResult,
  readUnreadCount,
  safeNotificationHref,
} = require("../src/modules/notifications/internalNotificationsModel.ts");

const rawNotification = (id, overrides = {}) => ({
  internal_notification_id: id,
  organization_id: 42,
  recipient_user_id: 7,
  source_event_id: 1000 + id,
  reason_code: "overdue",
  detected_on: "2026-07-29",
  planned_for: "2026-07-20",
  title_snapshot: `Powiadomienie ${id}`,
  target_label_snapshot: "Płatnik #1",
  internal_link_snapshot: "/rozliczenia/platnicy/1",
  created_at: "2026-07-29T10:00:00+00:00",
  state: "unread",
  is_unread: true,
  is_archived: false,
  ...overrides,
});

const page = readInternalNotificationPage({
  organization_id: 42,
  filter: "inbox",
  items: [rawNotification(1), rawNotification(2, { reason_code: "due_today", planned_for: null })],
  next_cursor: "cursor-2",
  has_more: true,
});
assert.equal(page.items.length, 2);
assert.equal(page.nextCursor, "cursor-2");
assert.equal(page.hasMore, true);
assert.equal(page.items[1].plannedFor, null);
assert.deepEqual(INTERNAL_NOTIFICATION_FILTERS.map((item) => item.id), ["inbox", "unread", "all", "archived"]);
assert.deepEqual(INTERNAL_NOTIFICATION_WRITE_ACTIONS, ["read", "unread", "archived"]);
assert.deepEqual(INTERNAL_NOTIFICATION_BILLING_ACTIONS, []);
assert.equal(INTERNAL_NOTIFICATION_POLL_INTERVAL, null);
assert.equal(formatUnreadCount(null), null);
assert.equal(formatUnreadCount(0), null);
assert.equal(formatUnreadCount(7), "7");
assert.equal(formatUnreadCount(100), "99+");
assert.equal(readUnreadCount({ unread_count: 0 }), 0);
assert.equal(safeNotificationHref("/rozliczenia/kroki"), "/rozliczenia/kroki");
assert.equal(safeNotificationHref("https://example.test"), null);
assert.equal(safeNotificationHref("//example.test/rozliczenia"), null);
assert.match(emptyStateCopy("archived").title, /Archiwum/);
assert.deepEqual(readMaterializationResult({
  as_of_date: "2026-07-29",
  candidates_count: 3,
  created_count: 2,
  existing_count: 1,
}), { asOfDate: "2026-07-29", candidatesCount: 3, createdCount: 2, existingCount: 1 });

assert.throws(() => readInternalNotificationPage({ ...page, organization_id: 43, items: [rawNotification(3)] }), /organizacji/);
assert.throws(() => readInternalNotificationPage({ organization_id: 42, filter: "future", items: [] }), /filtr/);
assert.throws(() => readInternalNotificationPage({ organization_id: 42, filter: "inbox", items: [rawNotification(4, { planned_for: "29-07-2026" })] }), /data/);

const srcRoot = path.join(__dirname, "..", "src");
const pageSource = fs.readFileSync(path.join(srcRoot, "modules", "notifications", "InternalNotificationsPage.tsx"), "utf8");
const countSource = fs.readFileSync(path.join(srcRoot, "context", "InternalNotificationCountContext.tsx"), "utf8");
assert.doesNotMatch(pageSource, /setInterval|setTimeout/);
assert.doesNotMatch(countSource, /setInterval|setTimeout/);
assert.match(pageSource, /Sprawdź nowe powiadomienia/);
assert.match(pageSource, /Samo otwarcie strony niczego nie zapisuje/);

console.log("Internal notifications model tests passed.");
