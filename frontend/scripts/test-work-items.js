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
    const filePath = [".ts", ".tsx", ".js", ".jsx"].map((extension) => `${resolved}${extension}`).find((candidate) => fs.existsSync(candidate));

    return filePath ?? resolved;
  }

  return originalResolveFilename.call(this, request, parent, isMain, options);
};

const { ApiContractError, ApiError, workItemAssignPath, workItemClosePath, workItemDetailPath, workItemSnoozePath } = require("../src/lib/api.ts");
const {
  WORK_ITEMS_ENDPOINT,
  WORK_ITEM_ASSIGN_ENDPOINT_SUFFIX,
  WORK_ITEM_ASSIGN_TO_SELF_ACTION_ENABLED,
  WORK_ITEM_CLOSE_ACTION_ENABLED,
  WORK_ITEM_CLOSE_ENDPOINT_SUFFIX,
  WORK_ITEM_SNOOZE_ACTION_ENABLED,
  WORK_ITEM_SNOOZE_ENDPOINT_SUFFIX,
  WORK_ITEM_SNOOZE_PRESETS,
  WORK_ITEMS_ORGANIZATION_REQUIRED_DESCRIPTION,
  WORK_ITEMS_ORGANIZATION_REQUIRED_TITLE,
  WORK_ITEMS_READ_ONLY,
  applyAssignedWorkItem,
  applyClosedWorkItem,
  applySnoozedWorkItem,
  buildAssignWorkItemToSelfPayload,
  buildCloseWorkItemPayload,
  buildWorkItemActionMenuItems,
  buildWorkItemRows,
  buildSnoozeWorkItemPayload,
  canAssignCurrentUserInOrganization,
  canAssignWorkItemToSelf,
  canCloseWorkItem,
  canSnoozeWorkItem,
  canUseWorkItemOrganizationScope,
  getWorkItemsErrorState,
  hasWorkItemsData,
  isWorkItemsEmpty,
  readCurrentUserId,
  readCurrentUserOrganizationId,
  readWorkItems,
  workItemPriorityTone,
  workItemStatusTone,
} = require("../src/modules/work-items/workItemsModel.ts");

function makeItem(overrides = {}) {
  return {
    work_item_id: 41,
    title: "Zweryfikowac sprawy SLA",
    description: "Minimalny rekord work item z backendu.",
    status: "w_toku",
    priority_level: "wysoki",
    priority_score: 72.5,
    source_type: "support",
    assigned_user_id: 9,
    assigned_user_name: "Ania Operator",
    organization_name: "CASI",
    due_at: "2099-04-10T10:00",
    sla_deadline_at: "2099-04-10T09:00",
    sla_stage: "warning",
    sla_state_label: "Ostrzezenie SLA",
    is_closed: false,
    is_due_overdue: false,
    is_sla_overdue: false,
    ...overrides,
  };
}

const items = readWorkItems([makeItem()]);
assert.equal(items.length, 1);
assert.equal(items[0].work_item_id, 41);
assert.equal(items[0].priority_score, 72.5);
assert.equal(items[0].assigned_user_id, 9);

const rows = buildWorkItemRows(items);
assert.equal(rows[0].title, "Zweryfikowac sprawy SLA");
assert.equal(rows[0].statusLabel, "W toku");
assert.equal(rows[0].priorityLabel, "Wysoki");
assert.equal(rows[0].priorityTone, "warning");
assert.equal(rows[0].ownerLabel, "Ania Operator");
assert.equal(rows[0].organizationLabel, "CASI");
assert.equal(rows[0].slaLabel, "Ostrzezenie SLA");
assert.equal(rows[0].sourceLabel, "Support");
assert.equal(rows[0].scoreLabel, "72.5");
assert.equal(rows[0].workItemId, 41);
assert.equal(rows[0].assignedUserId, 9);

assert.equal(workItemStatusTone(makeItem({ status: "zamkniete", is_closed: true })), "ok");
assert.equal(workItemStatusTone(makeItem({ sla_stage: "escalated" })), "danger");
assert.equal(workItemPriorityTone(makeItem({ priority_level: "krytyczny" })), "danger");
assert.equal(workItemPriorityTone(makeItem({ priority_level: "normalny", is_due_overdue: true })), "warning");
assert.equal(canCloseWorkItem(makeItem({ status: "w_toku", is_closed: false })), true);
assert.equal(canCloseWorkItem(makeItem({ status: "zamkniete", is_closed: true })), false);
assert.equal(canCloseWorkItem({ ...rows[0], statusLabel: "W toku", statusTone: "info" }), true);
assert.equal(canCloseWorkItem({ ...rows[0], statusLabel: "Zamkniete", statusTone: "ok" }), false);
assert.equal(canAssignWorkItemToSelf(makeItem({ status: "w_toku", is_closed: false, assigned_user_id: null }), 12), true);
assert.equal(canAssignWorkItemToSelf(makeItem({ status: "w_toku", is_closed: false, assigned_user_id: 12 }), 12), false);
assert.equal(canAssignWorkItemToSelf(makeItem({ status: "zamkniete", is_closed: true, assigned_user_id: null }), 12), false);
assert.equal(canAssignWorkItemToSelf(makeItem({ status: "anulowane", is_closed: false, assigned_user_id: null }), 12), false);
assert.equal(canAssignWorkItemToSelf(makeItem({ status: "w_toku", is_closed: false, assigned_user_id: null }), null), false);
assert.equal(canAssignWorkItemToSelf({ ...rows[0], statusLabel: "W toku", assignedUserId: null }, 12), true);
assert.equal(canAssignWorkItemToSelf({ ...rows[0], statusLabel: "W toku", assignedUserId: 12 }, 12), false);
assert.equal(canAssignWorkItemToSelf({ ...rows[0], statusLabel: "Anulowane", assignedUserId: null }, 12), false);
assert.equal(canSnoozeWorkItem(makeItem({ status: "w_toku", is_closed: false })), true);
assert.equal(canSnoozeWorkItem(makeItem({ status: "zamkniete", is_closed: true })), false);
assert.equal(canSnoozeWorkItem(makeItem({ status: "anulowane", is_closed: false })), false);
assert.equal(canSnoozeWorkItem({ ...rows[0], statusLabel: "W toku" }), true);
assert.equal(canSnoozeWorkItem({ ...rows[0], statusLabel: "Zamkniete" }), false);

const openActionMenu = buildWorkItemActionMenuItems({ ...rows[0], assignedUserId: null }, 12);
assert.deepEqual(
  openActionMenu.map((item) => item.label),
  ["Odloz 1h", "Jutro", "Przypisz do siebie", "Zamknij"],
);
assert.deepEqual(
  openActionMenu.map((item) => item.disabled),
  [false, false, false, false],
);
assert.equal(openActionMenu[3].danger, true);
const selfAssignedActionMenu = buildWorkItemActionMenuItems({ ...rows[0], assignedUserId: 12 }, 12);
assert.equal(selfAssignedActionMenu.find((item) => item.key === "assign-self").disabled, true);
const closedActionMenu = buildWorkItemActionMenuItems({ ...rows[0], statusLabel: "Zamkniete", statusTone: "ok" }, 12);
assert.deepEqual(
  closedActionMenu.map((item) => item.disabled),
  [true, true, true, true],
);

assert.deepEqual(buildAssignWorkItemToSelfPayload(12), {
  assigned_user_id: 12,
});
assert.deepEqual(buildSnoozeWorkItemPayload(WORK_ITEM_SNOOZE_PRESETS[0]), {
  mode: "1h",
});
assert.deepEqual(buildSnoozeWorkItemPayload(WORK_ITEM_SNOOZE_PRESETS[1]), {
  mode: "1d",
});
assert.deepEqual(buildCloseWorkItemPayload(" Zamkniete po kontakcie z klientem. "), {
  reason: "Zamkniete po kontakcie z klientem.",
});
assert.deepEqual(buildCloseWorkItemPayload("   "), {
  reason: "Zamkniete z poziomu CASI Workspace Next.",
});

const stillOpenResponse = readWorkItems([makeItem({ status: "w_toku", is_closed: false })])[0];
assert.equal(applyClosedWorkItem(items, stillOpenResponse).length, 1);
const closedResponse = readWorkItems([makeItem({ status: "zamkniete", is_closed: true })])[0];
assert.equal(applyClosedWorkItem(items, closedResponse).length, 0);
const assignedToOtherResponse = readWorkItems([makeItem({ assigned_user_id: 77, assigned_user_name: "Inna osoba" })])[0];
assert.equal(applyAssignedWorkItem(items, assignedToOtherResponse, 12)[0].assigned_user_id, 9);
const assignedToSelfResponse = readWorkItems([makeItem({ assigned_user_id: 12, assigned_user_name: "Ja Operator" })])[0];
assert.equal(applyAssignedWorkItem(items, assignedToSelfResponse, 12)[0].assigned_user_id, 12);
const snoozeNotConfirmedResponse = readWorkItems([makeItem({ sla_stage: "warning", sla_state_label: "Wciaz ostrzezenie" })])[0];
assert.equal(applySnoozedWorkItem(items, snoozeNotConfirmedResponse)[0].sla_stage, "warning");
const snoozedResponse = readWorkItems([makeItem({ sla_stage: "on_track", sla_state_label: "Odlozone", due_at: "2099-04-10T11:00" })])[0];
assert.equal(applySnoozedWorkItem(items, snoozedResponse)[0].sla_stage, "on_track");
assert.equal(applySnoozedWorkItem(items, snoozedResponse)[0].due_at, "2099-04-10T11:00");
assert.equal(readCurrentUserId({ user_id: 12, login: "ja" }), 12);
assert.equal(readCurrentUserId({ user: { user_id: "13", login: "ja" } }), 13);
assert.equal(readCurrentUserId({}), null);
assert.equal(readCurrentUserOrganizationId({ organization_id: 1, login: "ja" }), "1");
assert.equal(readCurrentUserOrganizationId({ user: { organization_id: "2", login: "ja" } }), "2");
assert.equal(readCurrentUserOrganizationId({}), null);
assert.equal(canAssignCurrentUserInOrganization("1", "1"), true);
assert.equal(canAssignCurrentUserInOrganization(1, "1"), true);
assert.equal(canAssignCurrentUserInOrganization(null, "1"), false);
assert.equal(canAssignCurrentUserInOrganization("2", "1"), false);

assert.equal(hasWorkItemsData("ready", items), true);
assert.equal(isWorkItemsEmpty("ready", []), true);
assert.equal(hasWorkItemsData("loading", items), false);

assert.equal(WORK_ITEMS_ENDPOINT, "/work-items");
assert.equal(WORK_ITEM_ASSIGN_TO_SELF_ACTION_ENABLED, true);
assert.equal(WORK_ITEM_ASSIGN_ENDPOINT_SUFFIX, "/assign");
assert.equal(WORK_ITEM_CLOSE_ACTION_ENABLED, true);
assert.equal(WORK_ITEM_CLOSE_ENDPOINT_SUFFIX, "/close");
assert.equal(WORK_ITEM_SNOOZE_ACTION_ENABLED, true);
assert.equal(WORK_ITEM_SNOOZE_ENDPOINT_SUFFIX, "/snooze");
assert.equal(WORK_ITEM_SNOOZE_PRESETS.length, 2);
assert.equal(WORK_ITEMS_ORGANIZATION_REQUIRED_TITLE, "Wybierz organizacje, aby zobaczyc work items");
assert.ok(WORK_ITEMS_ORGANIZATION_REQUIRED_DESCRIPTION.includes("organization_id"));
assert.equal(canUseWorkItemOrganizationScope("1"), true);
assert.equal(canUseWorkItemOrganizationScope(1), true);
assert.equal(canUseWorkItemOrganizationScope(null), false);
assert.equal(canUseWorkItemOrganizationScope(""), false);
assert.equal(workItemAssignPath(41), "/work-items/41/assign");
assert.equal(workItemClosePath(41), "/work-items/41/close");
assert.equal(workItemDetailPath(41), "/work-items/41");
assert.equal(workItemSnoozePath(41), "/work-items/41/snooze");
assert.equal(WORK_ITEMS_READ_ONLY, false);

assert.throws(() => readWorkItems({ items: [] }), ApiContractError);
assert.throws(() => readWorkItems([{ title: "Brak ID" }]), ApiContractError);

assert.equal(getWorkItemsErrorState(new ApiError("Brak sesji", 401, {})).status, "unauthenticated");
assert.equal(getWorkItemsErrorState(new ApiError("Brak uprawnien", 403, {})).status, "forbidden");
assert.equal(getWorkItemsErrorState(new ApiError("Backend padl", 500, {})).status, "server-error");
assert.equal(getWorkItemsErrorState(new ApiContractError(WORK_ITEMS_ENDPOINT, {})).title, "Niepoprawny format work items");

console.log("Work Items regression tests passed.");
