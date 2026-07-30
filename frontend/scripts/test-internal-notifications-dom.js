const assert = require("node:assert/strict");
const fs = require("node:fs");
const Module = require("node:module");
const path = require("node:path");
const ts = require("typescript");
const { JSDOM } = require("jsdom");

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

let currentOrganizationId = "42";
let failOrganizationId = null;
let materializeCalls = 0;
let refreshCountCalls = 0;
let scheduleSaveCalls = 0;
let savedSchedule = null;
let resolveDelayedOrganization = null;
const listCalls = [];
const stateCalls = [];

const rawNotification = (id, organizationId, overrides = {}) => ({
  internal_notification_id: id,
  organization_id: Number(organizationId),
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

const firstPage = [rawNotification(1, 42), rawNotification(2, 42, {
  reason_code: "due_today",
  planned_for: "2026-07-29",
  internal_link_snapshot: "https://unsafe.test",
})];
const secondPage = [rawNotification(3, 42, { state: "read", is_unread: false })];

const api = {
  internalNotifications: async (query) => {
    listCalls.push({ ...query });
    const organizationId = String(query.organization_id);
    if (organizationId === failOrganizationId) throw new Error("Kontrolowany błąd pobierania");
    if (organizationId === "46") {
      return new Promise((resolve) => {
        resolveDelayedOrganization = () => resolve({
          organization_id: 46,
          filter: query.filter,
          items: [rawNotification(46, 46)],
          next_cursor: null,
          has_more: false,
        });
      });
    }
    if (organizationId === "42") {
      const items = query.filter === "archived"
        ? []
        : query.cursor
          ? secondPage
          : firstPage;
      return {
        organization_id: 42,
        filter: query.filter,
        items,
        next_cursor: query.cursor ? null : "cursor-2",
        has_more: !query.cursor,
      };
    }
    if (organizationId === "43") {
      return { organization_id: 43, filter: query.filter, items: [rawNotification(43, 43)], next_cursor: null, has_more: false };
    }
    return { organization_id: Number(organizationId), filter: query.filter, items: [], next_cursor: null, has_more: false };
  },
  internalNotificationSchedule: async (query) => ({
    exists: savedSchedule !== null,
    organization_id: Number(query.organization_id),
    recipient_user_id: 7,
    source_type: "billing_next_step_attention",
    enabled: savedSchedule?.enabled ?? false,
    cadence: "daily",
    timezone_name: savedSchedule?.timezone_name ?? "Europe/Warsaw",
    local_time: savedSchedule?.local_time ?? "08:00",
    next_run_at_utc: savedSchedule?.enabled ? "2026-07-30T06:00:00+00:00" : null,
  }),
  internalNotificationScheduleRuns: async (query) => ({
    organization_id: Number(query.organization_id),
    recipient_user_id: 7,
    items: savedSchedule ? [{
      internal_notification_schedule_run_id: 81,
      schedule_id: 12,
      organization_id: Number(query.organization_id),
      recipient_user_id: 7,
      source_type: "billing_next_step_attention",
      scheduled_local_date: "2026-07-29",
      as_of_date: "2026-07-29",
      scheduled_for_utc: "2026-07-29T06:00:00+00:00",
      status: "succeeded",
      attempt_count: 1,
      candidates_count: 2,
      created_count: 1,
      existing_count: 1,
      error_code: null,
      error_summary: null,
      started_at: "2026-07-29T06:00:00+00:00",
      finished_at: "2026-07-29T06:00:01+00:00",
      created_at: "2026-07-29T06:00:00+00:00",
    }] : [],
  }),
  saveInternalNotificationSchedule: async (payload) => {
    scheduleSaveCalls += 1;
    await new Promise((resolve) => setTimeout(resolve, 5));
    savedSchedule = { ...payload };
    return {
      exists: true,
      internal_notification_schedule_id: 12,
      organization_id: Number(currentOrganizationId),
      recipient_user_id: 7,
      source_type: "billing_next_step_attention",
      enabled: payload.enabled,
      cadence: "daily",
      timezone_name: payload.timezone_name,
      local_time: payload.local_time,
      next_run_at_utc: payload.enabled ? "2026-07-30T06:00:00+00:00" : null,
    };
  },
  materializeInternalNotifications: async () => {
    materializeCalls += 1;
    await new Promise((resolve) => setTimeout(resolve, 5));
    return { as_of_date: "2026-07-29", candidates_count: 2, created_count: 1, existing_count: 1 };
  },
  updateInternalNotificationState: async (notificationId, action, organizationId) => {
    stateCalls.push({ notificationId, action, organizationId });
    await new Promise((resolve) => setTimeout(resolve, 5));
    return { changed: true };
  },
};

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
    return { Archive: Icon, Bell: Icon, Check: Icon, ChevronDown: Icon, RefreshCw: Icon, Undo2: Icon };
  }
  if (request === "@/context/ActiveOrganizationContext" || request.endsWith(`${path.sep}context${path.sep}ActiveOrganizationContext.tsx`)) {
    return { useActiveOrganization: () => ({ selectedOrganizationId: currentOrganizationId, status: "ready" }) };
  }
  if (request === "@/context/InternalNotificationCountContext" || request.endsWith(`${path.sep}context${path.sep}InternalNotificationCountContext.tsx`)) {
    return {
      useInternalNotificationCount: () => ({
        unreadCount: 2,
        refreshUnreadCount: async () => { refreshCountCalls += 1; },
      }),
    };
  }
  if (request === "@/lib/api" || request.endsWith(`${path.sep}lib${path.sep}api.ts`)) {
    return {
      api,
      withOrganizationQuery: (organizationId, query = {}) => ({ ...query, ...(organizationId ? { organization_id: organizationId } : {}) }),
    };
  }
  return originalLoad.call(this, request, parent, isMain);
};

const dom = new JSDOM("<!doctype html><html><body><div id=\"root\"></div></body></html>", {
  url: "http://127.0.0.1:3000/powiadomienia",
});
globalThis.window = dom.window;
globalThis.document = dom.window.document;
globalThis.navigator = dom.window.navigator;
globalThis.HTMLElement = dom.window.HTMLElement;
globalThis.Event = dom.window.Event;
globalThis.IS_REACT_ACT_ENVIRONMENT = true;

const React = require("react");
const { act } = React;
const { createRoot } = require("react-dom/client");
const { InternalNotificationsPage } = require("../src/modules/notifications/InternalNotificationsPage.tsx");

function buttonByText(container, text) {
  return [...container.querySelectorAll("button")].find((button) => button.textContent.trim() === text);
}

function setInputValue(input, value) {
  const valueSetter = Object.getOwnPropertyDescriptor(dom.window.HTMLInputElement.prototype, "value").set;
  valueSetter.call(input, value);
  input.dispatchEvent(new dom.window.Event("input", { bubbles: true }));
}

async function settle(delay = 0) {
  await act(async () => { await new Promise((resolve) => setTimeout(resolve, delay)); });
}

async function run() {
  const container = document.getElementById("root");
  const root = createRoot(container);
  await act(async () => root.render(React.createElement(InternalNotificationsPage)));
  await settle();

  assert.equal(materializeCalls, 0);
  assert.equal(stateCalls.length, 0);
  assert.equal(container.querySelectorAll(".notification-card").length, 2);
  assert.ok(container.querySelector('a[href="/rozliczenia/platnicy/1"]'));
  assert.match(container.textContent, /Źródło historyczne/);
  assert.match(container.textContent, /Samo otwarcie strony niczego nie zapisuje/);
  assert.match(container.textContent, /Automatyczne sprawdzanie/);
  assert.match(container.textContent, /Nie wysyła wiadomości i nie wykonuje działań rozliczeniowych/);
  assert.match(container.textContent, /Wyłączone/);
  assert.equal(scheduleSaveCalls, 0, "GET i zmiana pola nie mogą wykonywać autosave");

  const scheduleTime = container.querySelector('.notification-schedule input[type="time"]');
  const scheduleTimezone = container.querySelector('.notification-schedule input[type="text"]');
  const scheduleEnabled = container.querySelector('.notification-schedule input[type="checkbox"]');
  assert.equal(scheduleTime.value, "08:00");
  assert.equal(scheduleTimezone.value, "Europe/Warsaw");
  await act(async () => {
    scheduleEnabled.click();
    setInputValue(scheduleTime, "09:15");
  });
  assert.equal(scheduleSaveCalls, 0, "Zmiana kontrolek nie zapisuje ustawień");
  const saveScheduleButton = buttonByText(container, "Zapisz ustawienia");
  await act(async () => {
    saveScheduleButton.dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true }));
    saveScheduleButton.dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true }));
  });
  await settle(10);
  assert.equal(scheduleSaveCalls, 1, "Podwójne kliknięcie wykonuje jeden zapis");
  assert.deepEqual(savedSchedule, { enabled: true, local_time: "09:15", timezone_name: "Europe/Warsaw", cadence: "daily" });
  assert.match(container.textContent, /Ustawienia automatycznego sprawdzania zostały zapisane/);
  assert.match(container.textContent, /kandydaci 2, nowe 1, istniejące 1/);

  await act(async () => buttonByText(container, "Załaduj kolejne").dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true })));
  await settle();
  assert.equal(container.querySelectorAll(".notification-card").length, 3);
  assert.equal(listCalls.at(-1).cursor, "cursor-2");

  const materializeButton = buttonByText(container, "Sprawdź nowe powiadomienia");
  await act(async () => {
    materializeButton.dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true }));
    materializeButton.dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true }));
  });
  await settle(10);
  assert.equal(materializeCalls, 1);
  assert.match(container.textContent, /Utworzono 1 nowych powiadomień/);
  assert.equal(refreshCountCalls, 1);

  const readButton = buttonByText(container, "Oznacz jako przeczytane");
  await act(async () => {
    readButton.dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true }));
    readButton.dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true }));
  });
  await settle(10);
  assert.deepEqual(stateCalls, [{ notificationId: 1, action: "read", organizationId: "42" }]);
  assert.equal(refreshCountCalls, 2);

  await act(async () => buttonByText(container, "Archiwum").dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true })));
  await settle();
  assert.match(container.textContent, /Archiwum jest puste/);

  currentOrganizationId = "43";
  await act(async () => root.render(React.createElement(InternalNotificationsPage)));
  await settle();
  assert.match(container.textContent, /Powiadomienie 43/);
  assert.ok(!container.textContent.includes("Powiadomienie 1"));

  currentOrganizationId = "44";
  await act(async () => root.render(React.createElement(InternalNotificationsPage)));
  await settle();
  assert.match(container.textContent, /Archiwum jest puste/);

  currentOrganizationId = "46";
  await act(async () => root.render(React.createElement(InternalNotificationsPage)));
  await settle();
  currentOrganizationId = "43";
  await act(async () => root.render(React.createElement(InternalNotificationsPage)));
  await settle();
  assert.match(container.textContent, /Powiadomienie 43/);
  await act(async () => resolveDelayedOrganization());
  await settle();
  assert.match(container.textContent, /Powiadomienie 43/);
  assert.ok(!container.textContent.includes("Powiadomienie 46"));

  failOrganizationId = "45";
  currentOrganizationId = "45";
  await act(async () => root.render(React.createElement(InternalNotificationsPage)));
  await settle();
  assert.match(container.textContent, /Nie udało się pobrać powiadomień/);
  assert.ok(buttonByText(container, "Spróbuj ponownie"));

  await act(async () => root.unmount());
  console.log("Internal notifications DOM tests passed.");
}

run().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
