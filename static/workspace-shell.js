(function () {
  if (window.__casiWorkspaceShellInstalled) {
    return;
  }
  window.__casiWorkspaceShellInstalled = true;

  const WORKSPACE_DEVICE_ID_KEY = "casi-workspace-device-id";
  const WORKSPACE_LOCAL_STATE_KEY = "casi-workspace-state-v1";
  const MAX_WORKSPACE_SLOTS = 5;
  const WORKSPACE_SAVE_DEBOUNCE_MS = 1200;
  const WORKSPACE_REFRESH_INTERVAL_MS = 120000;
  const WORKSPACE_ALLOWED_VIEWS = new Set([
    "dashboard",
    "invoices",
    "knowledge",
    "contractors",
    "tasks",
    "billing",
    "support",
    "inbox",
    "views",
    "automation",
    "health",
    "logs",
    "organizations",
    "email-center",
    "users",
  ]);

  const WORKSPACE_MODULES = {
    dashboard: {
      key: "dashboard",
      label: "Lobby",
      view: "dashboard",
      fixed: true,
      subtabs: [
        { key: "lobby", label: "Start" },
        { key: "note", label: "Notatka" },
        { key: "priorities", label: "Priorytety" },
        { key: "reminders", label: "Przypomnienia" },
        { key: "alerts", label: "Alerty" },
        { key: "events", label: "Zdarzenia" },
      ],
    },
    invoices: {
      key: "invoices",
      label: "Faktury",
      view: "invoices",
      subtabs: [
        { key: "start", label: "Start" },
        { key: "filtry", label: "Filtry" },
        { key: "skrzynka", label: "Skrzynka" },
        { key: "weryfikacja", label: "Weryfikacja" },
        { key: "przyjecie", label: "Przyjecie" },
        { key: "wyjatki", label: "Wyjatki" },
        { key: "przekazania", label: "Przekazania" },
        { key: "lista", label: "Lista" },
        { key: "szczegoly", label: "Szczegoly" },
        { key: "saldo", label: "Saldo" },
        { key: "ksiega", label: "Ksiega" },
        { key: "dopasowania", label: "Dopasowania" },
      ],
    },
    knowledge: {
      key: "knowledge",
      label: "Asystent Firmowy",
      view: "knowledge",
      subtabs: [
        { key: "overview", label: "Start" },
        { key: "documents", label: "Dokumenty" },
        { key: "assistant", label: "Asystent" },
        { key: "preview", label: "Podglad" },
        { key: "my_work", label: "Moja praca" },
        { key: "admin", label: "Uprawnienia" },
      ],
    },
    contractors: {
      key: "contractors",
      label: "Kontrahenci",
      view: "contractors",
      subtabs: [
        { key: "lista", label: "Lista" },
        { key: "szczegoly", label: "Szczegoly" },
      ],
    },
    tasks: {
      key: "tasks",
      label: "Asystent Szefa",
      view: "tasks",
      subtabs: [
        { key: "filters", label: "Filtry" },
        { key: "focus", label: "Moja praca" },
        { key: "planner", label: "Planner" },
        { key: "calendar", label: "Kalendarz" },
        { key: "command", label: "Polecenie" },
        { key: "notes", label: "Notatki" },
        { key: "calendars", label: "Kalendarze" },
        { key: "settings", label: "Ustawienia" },
        { key: "list", label: "Lista" },
        { key: "detail", label: "Szczegoly" },
      ],
    },
    billing: {
      key: "billing",
      label: "Rozliczenia",
      view: "billing",
      subtabs: [
        { key: "roadmap", label: "Start" },
        { key: "accounts", label: "Rachunki" },
        { key: "imports", label: "Importy" },
      ],
    },
    support: {
      key: "support",
      label: "Pomoc",
      view: "support",
      subtabs: [
        { key: "overview", label: "Start" },
        { key: "compose", label: "Nowe" },
        { key: "requests", label: "Zgloszenia" },
        { key: "thread", label: "Szczegoly" },
      ],
    },
    inbox: {
      key: "inbox",
      label: "Inbox",
      view: "inbox",
      subtabs: [
        { key: "forms", label: "Formularze" },
        { key: "items", label: "Sprawy" },
        { key: "detail", label: "Szczegoly" },
      ],
    },
    views: {
      key: "views",
      label: "Widoki",
      view: "views",
      subtabs: [
        { key: "list", label: "Lista" },
        { key: "editor", label: "Edytor" },
      ],
    },
    automation: {
      key: "automation",
      label: "Automatyzacje",
      view: "automation",
      subtabs: [
        { key: "rules", label: "Reguly" },
        { key: "editor", label: "Edytor" },
        { key: "executions", label: "Wykonania" },
      ],
    },
    health: {
      key: "health",
      label: "Zdrowie",
      view: "health",
      subtabs: [
        { key: "worker", label: "Worker" },
        { key: "platform", label: "Platforma" },
        { key: "billing", label: "Rozliczenia" },
      ],
    },
    logs: { key: "logs", label: "Historia", view: "logs", subtabs: [{ key: "logs", label: "Logi" }] },
    organizations: {
      key: "organizations",
      label: "Organizacje",
      view: "organizations",
      subtabs: [
        { key: "list", label: "Lista" },
        { key: "config", label: "Konfiguracja" },
      ],
    },
    "email-center": {
      key: "email-center",
      label: "Centrum integracji",
      view: "email-center",
      subtabs: [
        { key: "overview", label: "Polaczenia" },
        { key: "email_runs", label: "E-mail" },
        { key: "ksef_runs", label: "KSeF" },
      ],
    },
    users: {
      key: "users",
      label: "Uzytkownicy",
      view: "users",
      subtabs: [
        { key: "list", label: "Lista" },
        { key: "form", label: "Konto" },
      ],
    },
  };

  const SUBTAB_SCROLL_TARGETS = {
    dashboard: {
      lobby: "dashboard-focus-shell",
      note: "dashboard-shared-note-shell",
      priorities: "dashboard-priority-shell",
      reminders: "dashboard-reminders-shell",
      alerts: "dashboard-alerts-shell",
      events: "dashboard-events-shell",
    },
    invoices: {
      start: "invoice-command-shell",
      filtry: "invoice-filters-panel-shell",
      skrzynka: "invoice-verification-inbox-shell",
      weryfikacja: "invoice-verification-workspace-shell",
      przyjecie: "invoice-document-intake-shell",
      wyjatki: "invoice-exception-center-shell",
      przekazania: "invoice-handoff-batches-shell",
      lista: "invoice-list-shell",
      szczegoly: "invoice-detail-shell",
      saldo: "invoice-billing-balances-shell",
      ksiega: "invoice-billing-ledger-shell",
      dopasowania: "invoice-billing-matches-shell",
    },
    knowledge: {
      overview: "knowledge-overview-shell",
      documents: "knowledge-documents-pane",
      assistant: "knowledge-assistant-pane",
      preview: "knowledge-preview-shell",
      my_work: "knowledge-my-work-shell",
      admin: "knowledge-admin-shell",
    },
    tasks: {
      filters: "task-filters-shell",
      focus: "task-focus-shell",
      planner: "task-planner-shell",
      calendar: "task-calendar-shell",
      command: "task-command-shell",
      notes: "task-notes-shell",
      calendars: "task-calendars-shell",
      settings: "task-calendar-settings-shell",
      list: "task-list-shell",
      detail: "task-detail-shell",
    },
    contractors: {
      lista: "contractors-list-shell",
      szczegoly: "contractors-detail-shell",
    },
    billing: {
      roadmap: "billing-roadmap-shell",
      accounts: "billing-accounts-shell",
      imports: "billing-import-shell",
    },
    support: {
      overview: "support-overview-shell",
      compose: "support-compose-shell",
      requests: "support-requests-shell",
      thread: "support-thread-panel",
    },
    inbox: {
      forms: "inbox-forms-shell",
      items: "inbox-items-shell",
      detail: "inbox-detail-shell",
    },
    views: {
      list: "views-list-shell",
      editor: "views-editor-shell",
    },
    automation: {
      rules: "automation-rules-shell",
      editor: "automation-editor-shell",
      executions: "automation-executions-shell",
    },
    health: {
      worker: "health-worker-shell",
      platform: "health-platform-shell",
      billing: "health-billing-shell",
    },
    logs: { logs: "logs-shell" },
    organizations: {
      list: "organizations-list-shell",
      config: "organizations-form-shell",
    },
    "email-center": {
      overview: "email-center-summary-shell",
      email_runs: "email-center-runs-shell",
      ksef_runs: "ksef-center-runs-shell",
    },
    users: {
      list: "users-list-shell",
      form: "users-form-shell",
    },
  };

  const legacyApi = api;
  const legacySetView = ustawWidok;
  const legacyTryRestoreSession = sprobujPrzywrocicSesje;
  const legacyLogin = zalogujDoSystemu;
  const legacyPrepareLoggedOutView = przygotujWidokPoWylogowaniu;
  const legacyRefreshSessionBar = odswiezPasekSesji;

  function ensureWorkspaceState() {
    if (!stan.workspaceShell) {
      stan.workspaceShell = {
        activePrimary: "lobby",
        slots: [],
        expanded: false,
        pendingModuleKey: null,
        replaceDialogOpen: false,
        saveTimeoutId: null,
        lastTouchStart: null,
        refreshIntervalId: null,
        counter: 0,
      };
    }
    return stan.workspaceShell;
  }

  function nowTimestamp() {
    return Date.now();
  }

  function newIsoTimestamp() {
    return new Date().toISOString();
  }

  function getWorkspaceRoot() {
    return document.getElementById("workspace-shell-root");
  }

  function getWorkspaceModalRoot() {
    return document.getElementById("workspace-replace-modal-root");
  }

  function getCurrentDeviceId() {
    let deviceId = window.localStorage.getItem(WORKSPACE_DEVICE_ID_KEY);
    if (!deviceId) {
      deviceId =
        typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
          ? crypto.randomUUID()
          : `device-${Math.random().toString(36).slice(2)}-${Date.now()}`;
      window.localStorage.setItem(WORKSPACE_DEVICE_ID_KEY, deviceId);
    }
    return deviceId;
  }

  function getCurrentDeviceLabel() {
    return window.matchMedia("(max-width: 900px)").matches ? "Telefon lub tablet" : "Komputer";
  }

  api = async function workspaceAwareApi(url, options = {}, settings = {}) {
    const headers = { ...(options.headers || {}) };
    headers["X-CASI-Device-Id"] = getCurrentDeviceId();
    headers["X-CASI-Device-Label"] = getCurrentDeviceLabel();
    return legacyApi(url, { ...options, headers }, settings);
  };

  function isWorkspaceEnabled() {
    return Boolean(stan.biezacyUzytkownik);
  }

  function getModuleDefinition(moduleKey) {
    return WORKSPACE_MODULES[moduleKey] || WORKSPACE_MODULES.dashboard;
  }

  function canUseWorkspaceModule(moduleKey) {
    if (!isWorkspaceEnabled()) {
      return moduleKey === "dashboard";
    }
    if (moduleKey === "dashboard" || moduleKey === "invoices" || moduleKey === "knowledge" || moduleKey === "contractors") {
      return true;
    }
    const matchingButtons = Array.from(document.querySelectorAll(`.nav-item[data-view="${moduleKey}"]`));
    if (matchingButtons.length) {
      return matchingButtons.some((button) => !button.classList.contains("hidden"));
    }
    return true;
  }

  function getVisibleSubtabs(moduleKey) {
    return [...(getModuleDefinition(moduleKey).subtabs || [])];
  }

  function getDefaultSubtabKey(moduleKey) {
    const subtabs = getVisibleSubtabs(moduleKey);
    return subtabs[0] ? subtabs[0].key : "overview";
  }

  function nextSlotId() {
    const workspace = ensureWorkspaceState();
    workspace.counter += 1;
    return `slot-${workspace.counter}`;
  }

  function findSlotById(slotId) {
    return ensureWorkspaceState().slots.find((slot) => slot.slotId === slotId) || null;
  }

  function findSlotByModule(moduleKey) {
    return ensureWorkspaceState().slots.find((slot) => slot.moduleKey === moduleKey) || null;
  }

  function getActiveSlot() {
    const workspace = ensureWorkspaceState();
    return workspace.activePrimary === "lobby" ? null : findSlotById(workspace.activePrimary);
  }

  function markPrimaryAsRecentlyUsed(primaryId) {
    const workspace = ensureWorkspaceState();
    if (primaryId === "lobby") {
      workspace.lobbyLastUsedAt = nowTimestamp();
      return;
    }
    const slot = findSlotById(primaryId);
    if (slot) {
      slot.lastActiveAt = nowTimestamp();
    }
  }

  function normalizeSnapshot(snapshot) {
    if (!snapshot || typeof snapshot !== "object") {
      return null;
    }
    return {
      viewKey: String(snapshot.viewKey || "").trim() || null,
      fieldState: snapshot.fieldState && typeof snapshot.fieldState === "object" ? snapshot.fieldState : {},
      customState: snapshot.customState && typeof snapshot.customState === "object" ? snapshot.customState : {},
      scrollTop: Number(snapshot.scrollTop || 0) || 0,
      capturedAt: String(snapshot.capturedAt || ""),
    };
  }

  function normalizeHistoryEntry(entry, index = 0) {
    const moduleKey = String(entry?.moduleKey || "").trim();
    if (!moduleKey || !WORKSPACE_MODULES[moduleKey] || moduleKey === "dashboard" || !canUseWorkspaceModule(moduleKey)) {
      return null;
    }
    return {
      entryId: String(entry?.entryId || `history-${index + 1}`),
      moduleKey,
      subtabKey: String(entry?.subtabKey || getDefaultSubtabKey(moduleKey)),
      snapshot: normalizeSnapshot(entry?.snapshot),
      restoredAt: Number(entry?.restoredAt || 0) || nowTimestamp(),
    };
  }

  function normalizeSlotShape(slot, index = 0) {
    const moduleKey = String(slot?.moduleKey || "").trim();
    if (!moduleKey || moduleKey === "dashboard" || !WORKSPACE_MODULES[moduleKey] || !canUseWorkspaceModule(moduleKey)) {
      return null;
    }
    const subtabs = getVisibleSubtabs(moduleKey);
    const requestedSubtab = String(slot?.subtabKey || "").trim();
    return {
      slotId: String(slot?.slotId || `slot-restored-${index + 1}`),
      moduleKey,
      subtabKey: subtabs.some((item) => item.key === requestedSubtab) ? requestedSubtab : getDefaultSubtabKey(moduleKey),
      lastActiveAt: Number(slot?.lastActiveAt || 0) || nowTimestamp(),
      snapshot: normalizeSnapshot(slot?.snapshot),
      history: Array.isArray(slot?.history)
        ? slot.history.map((entry, historyIndex) => normalizeHistoryEntry(entry, historyIndex)).filter(Boolean)
        : [],
      needsRestore: true,
    };
  }

  function createEmptySlot(moduleKey, options = {}) {
    return {
      slotId: nextSlotId(),
      moduleKey,
      subtabKey: options.subtabKey || getDefaultSubtabKey(moduleKey),
      lastActiveAt: nowTimestamp(),
      snapshot: normalizeSnapshot(options.snapshot) || null,
      history: [],
      needsRestore: Boolean(options.snapshot),
    };
  }

  function readSerializableWorkspaceState() {
    const workspace = ensureWorkspaceState();
    return {
      version: 1,
      app_name: "CASI Workspace",
      user_id: Number(stan.biezacyUzytkownik?.user_id || 0) || null,
      organization_id: stan.wybranaOrganizacjaId || stan.biezacyUzytkownik?.organization_id || null,
      current_device_id: getCurrentDeviceId(),
      active_primary: workspace.activePrimary,
      lobby_last_used_at: Number(workspace.lobbyLastUsedAt || 0) || 0,
      expanded: Boolean(workspace.expanded),
      updated_at: newIsoTimestamp(),
      slots: workspace.slots.map((slot) => ({
        slotId: slot.slotId,
        moduleKey: slot.moduleKey,
        subtabKey: slot.subtabKey,
        lastActiveAt: slot.lastActiveAt,
        snapshot: slot.snapshot || null,
        history: Array.isArray(slot.history) ? slot.history.map((entry) => ({ ...entry })) : [],
      })),
    };
  }

  function saveWorkspaceStateLocally() {
    if (!isWorkspaceEnabled()) {
      return;
    }
    try {
      window.localStorage.setItem(WORKSPACE_LOCAL_STATE_KEY, JSON.stringify(readSerializableWorkspaceState()));
    } catch (error) {
      console.warn("Nie udalo sie zapisac lokalnego stanu workspace.", error);
    }
  }

  async function saveWorkspaceStateRemotely() {
    if (!isWorkspaceEnabled()) {
      return;
    }
    try {
      const updatedUser = await api(
        "/api/session/workspace-state",
        {
          method: "PATCH",
          body: JSON.stringify({ workspace_state: readSerializableWorkspaceState() }),
        },
        { pominWylogowanie: true }
      );
      if (updatedUser && typeof updatedUser === "object") {
        stan.biezacyUzytkownik = updatedUser;
        legacyRefreshSessionBar();
      }
    } catch (error) {
      console.warn("Nie udalo sie zapisac stanu workspace na serwerze.", error);
    }
  }

  function scheduleWorkspacePersistence() {
    const workspace = ensureWorkspaceState();
    saveWorkspaceStateLocally();
    if (workspace.saveTimeoutId) {
      window.clearTimeout(workspace.saveTimeoutId);
    }
    workspace.saveTimeoutId = window.setTimeout(() => {
      workspace.saveTimeoutId = null;
      void saveWorkspaceStateRemotely();
    }, WORKSPACE_SAVE_DEBOUNCE_MS);
  }

  function loadLocalWorkspaceState() {
    try {
      const raw = window.localStorage.getItem(WORKSPACE_LOCAL_STATE_KEY);
      if (!raw) {
        return null;
      }
      const parsed = JSON.parse(raw);
      if (!parsed || typeof parsed !== "object") {
        return null;
      }
      if (Number(parsed.user_id || 0) !== Number(stan.biezacyUzytkownik?.user_id || 0)) {
        return null;
      }
      const currentScope = String(stan.wybranaOrganizacjaId || stan.biezacyUzytkownik?.organization_id || "");
      const savedScope = String(parsed.organization_id || "");
      if (currentScope && savedScope && currentScope !== savedScope) {
        return null;
      }
      return parsed;
    } catch (error) {
      console.warn("Nie udalo sie odczytac lokalnego stanu workspace.", error);
      return null;
    }
  }

  function pickBestWorkspaceState(localState, serverState, serverUpdatedAt) {
    if (!localState && !serverState) {
      return null;
    }
    if (localState && !serverState) {
      return localState;
    }
    if (!localState && serverState) {
      return serverState;
    }
    const localUpdatedAt = Date.parse(String(localState.updated_at || "")) || 0;
    const remoteUpdatedAt =
      Date.parse(String(serverUpdatedAt || serverState.updated_at || "")) ||
      Date.parse(String(serverState.updated_at || "")) ||
      0;
    return localUpdatedAt >= remoteUpdatedAt ? localState : serverState;
  }

  function captureFieldStateForView(viewKey) {
    const root = document.getElementById(`${viewKey}-view`);
    if (!root) {
      return {};
    }
    const fieldState = {};
    const namedCounts = {};
    root.querySelectorAll("input, select, textarea").forEach((field) => {
      if (!field || field.closest(".modal-shell")) {
        return;
      }
      const fieldType = String(field.type || "").toLowerCase();
      if (fieldType === "password" || fieldType === "file") {
        return;
      }
      const idKey = field.id ? `id:${field.id}` : "";
      const nameKey = field.name ? `name:${field.name}:${namedCounts[field.name] || 0}` : "";
      if (field.name) {
        namedCounts[field.name] = (namedCounts[field.name] || 0) + 1;
      }
      const key = idKey || nameKey;
      if (!key) {
        return;
      }
      fieldState[key] = {
        type: fieldType,
        value: fieldType === "checkbox" || fieldType === "radio" ? Boolean(field.checked) : field.value,
      };
    });
    return fieldState;
  }

  function restoreFieldStateForView(viewKey, fieldState) {
    const root = document.getElementById(`${viewKey}-view`);
    if (!root || !fieldState || typeof fieldState !== "object") {
      return;
    }
    const namedMatches = {};
    root.querySelectorAll("input, select, textarea").forEach((field) => {
      const fieldType = String(field.type || "").toLowerCase();
      if (fieldType === "password" || fieldType === "file") {
        return;
      }
      let key = "";
      if (field.id) {
        key = `id:${field.id}`;
      } else if (field.name) {
        const currentIndex = namedMatches[field.name] || 0;
        key = `name:${field.name}:${currentIndex}`;
        namedMatches[field.name] = currentIndex + 1;
      }
      if (!key || !Object.prototype.hasOwnProperty.call(fieldState, key)) {
        return;
      }
      const snapshot = fieldState[key];
      if (fieldType === "checkbox" || fieldType === "radio") {
        field.checked = Boolean(snapshot.value);
      } else if (snapshot.value !== undefined && snapshot.value !== null) {
        field.value = String(snapshot.value);
      }
      field.dispatchEvent(new Event("input", { bubbles: true }));
      field.dispatchEvent(new Event("change", { bubbles: true }));
    });
  }

  function captureCustomState(viewKey) {
    if (viewKey === "invoices") {
      return {
        wybranaFakturaId: stan.wybranaFakturaId,
        zaznaczoneFaktury: Array.isArray(stan.zaznaczoneFaktury) ? [...stan.zaznaczoneFaktury] : [],
        aktywnyKoszykWeryfikacjiFaktur: stan.aktywnyKoszykWeryfikacjiFaktur,
        czyFiltryFakturRozwiniete: Boolean(stan.czyFiltryFakturRozwiniete),
      };
    }
    if (viewKey === "knowledge") {
      return {
        widokBazyWiedzy: stan.widokBazyWiedzy || "assistant",
        widokDokumentowBazyWiedzy: stan.widokDokumentowBazyWiedzy || "recent",
        wybranyDokumentWiedzyId: stan.wybranyDokumentWiedzyId || null,
        folderBazyWiedzy: stan.folderBazyWiedzy || "",
      };
    }
    if (viewKey === "tasks") {
      return {
        wybraneZadanieId: stan.wybraneZadanieId || null,
        aktywnyWidokFokusu: stan.aktywnyWidokFokusu || "",
        taskCalendarMode: stan.taskCalendarMode || "miesiac",
        taskCalendarAnchor: stan.taskCalendarAnchor ? new Date(stan.taskCalendarAnchor).toISOString() : null,
      };
    }
    if (viewKey === "contractors") {
      return {
        wybranyKontrahentId: stan.wybranyKontrahentId || null,
        filtryKontrahentow: { ...(stan.filtryKontrahentow || {}) },
      };
    }
    return {};
  }

  function restoreCustomState(viewKey, customState) {
    if (!customState || typeof customState !== "object") {
      return;
    }
    if (viewKey === "invoices") {
      stan.wybranaFakturaId = customState.wybranaFakturaId || null;
      stan.zaznaczoneFaktury = Array.isArray(customState.zaznaczoneFaktury) ? [...customState.zaznaczoneFaktury] : [];
      if (customState.aktywnyKoszykWeryfikacjiFaktur) {
        stan.aktywnyKoszykWeryfikacjiFaktur = customState.aktywnyKoszykWeryfikacjiFaktur;
      }
      if (typeof ustawWidocznoscFiltrowFaktur === "function") {
        ustawWidocznoscFiltrowFaktur(Boolean(customState.czyFiltryFakturRozwiniete));
      }
      if (typeof renderujWorkspaceWeryfikacjiFaktur === "function" && stan.workspaceWeryfikacjiFaktur) {
        renderujWorkspaceWeryfikacjiFaktur(stan.workspaceWeryfikacjiFaktur);
      }
      if (typeof renderujFaktury === "function" && Array.isArray(stan.faktury)) {
        renderujFaktury(stan.faktury);
      }
      return;
    }
    if (viewKey === "knowledge") {
      stan.folderBazyWiedzy = String(customState.folderBazyWiedzy || "");
      if (typeof ustawTrybBazyWiedzy === "function") {
        ustawTrybBazyWiedzy(customState.widokBazyWiedzy || "assistant");
      }
      if (typeof ustawWidokDokumentowBazyWiedzy === "function") {
        ustawWidokDokumentowBazyWiedzy(customState.widokDokumentowBazyWiedzy || "recent");
      }
      if (typeof ustawWybranyDokumentBazyWiedzy === "function" && customState.wybranyDokumentWiedzyId) {
        ustawWybranyDokumentBazyWiedzy(customState.wybranyDokumentWiedzyId, { rerender: false });
      }
      if (typeof odswiezWidokBazyWiedzyZPamieci === "function") {
        odswiezWidokBazyWiedzyZPamieci();
      }
      return;
    }
    if (viewKey === "tasks") {
      stan.wybraneZadanieId = customState.wybraneZadanieId || null;
      stan.aktywnyWidokFokusu = customState.aktywnyWidokFokusu || "";
      stan.taskCalendarMode = customState.taskCalendarMode || "miesiac";
      stan.taskCalendarAnchor = customState.taskCalendarAnchor ? new Date(customState.taskCalendarAnchor) : null;
      if (typeof renderujWidokKalendarzaZadan === "function") {
        renderujWidokKalendarzaZadan(stan.zadania);
      }
      if (typeof renderujFokusZadan === "function" && stan.fokusZadan) {
        renderujFokusZadan(stan.fokusZadan);
      }
      if (typeof renderujPlannerZadan === "function" && stan.plannerZadan) {
        renderujPlannerZadan(stan.plannerZadan);
      }
      return;
    }
    if (viewKey === "contractors") {
      stan.wybranyKontrahentId = customState.wybranyKontrahentId || null;
      stan.filtryKontrahentow = { ...(stan.filtryKontrahentow || {}), ...(customState.filtryKontrahentow || {}) };
      if (typeof renderujKontrahentow === "function" && Array.isArray(stan.kontrahenciWidoczni)) {
        renderujKontrahentow(stan.kontrahenciWidoczni);
      }
    }
  }

  function captureModuleSnapshot(moduleKey) {
    const definition = getModuleDefinition(moduleKey);
    return {
      viewKey: definition.view,
      fieldState: captureFieldStateForView(definition.view),
      customState: captureCustomState(definition.view),
      scrollTop: document.querySelector(".main")?.scrollTop || document.scrollingElement?.scrollTop || 0,
      capturedAt: newIsoTimestamp(),
    };
  }

  function restoreModuleSnapshot(moduleKey, snapshot) {
    const normalized = normalizeSnapshot(snapshot);
    if (!normalized) {
      return;
    }
    const viewKey = normalized.viewKey || getModuleDefinition(moduleKey).view;
    window.setTimeout(() => {
      restoreCustomState(viewKey, normalized.customState);
      restoreFieldStateForView(viewKey, normalized.fieldState);
      const scrollContainer = document.querySelector(".main");
      if (scrollContainer) {
        scrollContainer.scrollTop = Number(normalized.scrollTop || 0) || 0;
      } else if (document.scrollingElement) {
        document.scrollingElement.scrollTop = Number(normalized.scrollTop || 0) || 0;
      }
    }, 40);
  }

  function scrollToSubtabTarget(moduleKey, subtabKey) {
    const targetId = SUBTAB_SCROLL_TARGETS[moduleKey]?.[subtabKey];
    if (!targetId) {
      return;
    }
    window.setTimeout(() => {
      document.getElementById(targetId)?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 50);
  }

  function applySubtabBehavior(slot) {
    if (!slot) {
      return;
    }
    if (slot.moduleKey === "knowledge") {
      if (slot.subtabKey === "assistant") {
        if (typeof ustawTrybBazyWiedzy === "function") {
          ustawTrybBazyWiedzy("assistant");
        }
      } else if (["documents", "preview", "my_work", "admin", "recent", "folders"].includes(slot.subtabKey)) {
        if (typeof ustawTrybBazyWiedzy === "function") {
          ustawTrybBazyWiedzy("documents");
        }
        if (typeof ustawWidokDokumentowBazyWiedzy === "function") {
          ustawWidokDokumentowBazyWiedzy(slot.subtabKey === "folders" ? "folders" : "recent");
        }
      }
    }
    if (slot.moduleKey === "invoices" && slot.subtabKey === "weryfikacja" && typeof otworzWorkspaceWeryfikacjiFaktur === "function") {
      void otworzWorkspaceWeryfikacjiFaktur(stan.aktywnyKoszykWeryfikacjiFaktur);
    }
    scrollToSubtabTarget(slot.moduleKey, slot.subtabKey);
  }

  function activateLobby(options = {}) {
    const workspace = ensureWorkspaceState();
    workspace.activePrimary = "lobby";
    markPrimaryAsRecentlyUsed("lobby");
    legacySetView("dashboard");
    renderWorkspaceShell();
    if (!options.skipPersist) {
      scheduleWorkspacePersistence();
    }
  }

  function activateSlot(slotId, options = {}) {
    const workspace = ensureWorkspaceState();
    const slot = findSlotById(slotId);
    if (!slot) {
      activateLobby(options);
      return;
    }
    workspace.activePrimary = slot.slotId;
    markPrimaryAsRecentlyUsed(slot.slotId);
    legacySetView(getModuleDefinition(slot.moduleKey).view);
    applySubtabBehavior(slot);
    if (slot.needsRestore || options.forceRestore) {
      restoreModuleSnapshot(slot.moduleKey, slot.snapshot);
      slot.needsRestore = false;
    }
    renderWorkspaceShell();
    if (!options.skipPersist) {
      scheduleWorkspacePersistence();
    }
  }

  function closeReplaceDialog() {
    const workspace = ensureWorkspaceState();
    workspace.pendingModuleKey = null;
    workspace.replaceDialogOpen = false;
    renderWorkspaceModal();
  }

  function openReplaceDialog(moduleKey) {
    const workspace = ensureWorkspaceState();
    workspace.pendingModuleKey = moduleKey;
    workspace.replaceDialogOpen = true;
    renderWorkspaceModal();
  }

  function switchSubtab(slotId, subtabKey, options = {}) {
    const slot = findSlotById(slotId);
    if (!slot) {
      return;
    }
    const visibleSubtabs = getVisibleSubtabs(slot.moduleKey);
    if (!visibleSubtabs.some((item) => item.key === subtabKey)) {
      return;
    }
    slot.subtabKey = subtabKey;
    if (ensureWorkspaceState().activePrimary === slot.slotId) {
      legacySetView(getModuleDefinition(slot.moduleKey).view);
      applySubtabBehavior(slot);
    }
    renderWorkspaceShell();
    if (!options.skipPersist) {
      scheduleWorkspacePersistence();
    }
  }

  function captureActiveSlotSnapshot() {
    const activeSlot = getActiveSlot();
    if (!activeSlot) {
      return;
    }
    activeSlot.snapshot = captureModuleSnapshot(activeSlot.moduleKey);
  }

  function openModuleInWorkspace(moduleKey, options = {}) {
    const workspace = ensureWorkspaceState();
    if (!WORKSPACE_ALLOWED_VIEWS.has(moduleKey)) {
      legacySetView(moduleKey);
      return;
    }
    if (moduleKey === "dashboard") {
      activateLobby(options);
      return;
    }
    if (!canUseWorkspaceModule(moduleKey)) {
      legacySetView(moduleKey);
      return;
    }
    const existingSlot = findSlotByModule(moduleKey);
    if (existingSlot) {
      if (options.subtabKey) {
        existingSlot.subtabKey = options.subtabKey;
      }
      activateSlot(existingSlot.slotId, options);
      return;
    }
    captureActiveSlotSnapshot();
    if (workspace.slots.length < MAX_WORKSPACE_SLOTS) {
      const slot = createEmptySlot(moduleKey, { subtabKey: options.subtabKey });
      workspace.slots.push(slot);
      activateSlot(slot.slotId, options);
      return;
    }
    openReplaceDialog(moduleKey);
  }

  function replaceSlotModule(slotId, nextModuleKey) {
    const slot = findSlotById(slotId);
    if (!slot || !nextModuleKey) {
      closeReplaceDialog();
      return;
    }
    const currentSnapshot = captureModuleSnapshot(slot.moduleKey);
    slot.history.push({
      entryId: `history-${slot.slotId}-${nowTimestamp()}`,
      moduleKey: slot.moduleKey,
      subtabKey: slot.subtabKey,
      snapshot: currentSnapshot,
      restoredAt: nowTimestamp(),
    });
    slot.moduleKey = nextModuleKey;
    slot.subtabKey = getDefaultSubtabKey(nextModuleKey);
    slot.snapshot = null;
    slot.needsRestore = false;
    slot.lastActiveAt = nowTimestamp();
    closeReplaceDialog();
    activateSlot(slot.slotId);
  }

  function closeWorkspaceSlot(slotId) {
    const workspace = ensureWorkspaceState();
    const slot = findSlotById(slotId);
    if (!slot) {
      return;
    }
    captureActiveSlotSnapshot();
    workspace.slots = workspace.slots.filter((item) => item.slotId !== slotId);
    const remainingSlots = [...workspace.slots].sort((left, right) => Number(right.lastActiveAt || 0) - Number(left.lastActiveAt || 0));
    if (remainingSlots[0]) {
      activateSlot(remainingSlots[0].slotId);
    } else {
      activateLobby();
    }
    renderWorkspaceShell();
    scheduleWorkspacePersistence();
  }

  function goBackToPreviousModuleInActiveSlot() {
    const slot = getActiveSlot();
    if (!slot || !Array.isArray(slot.history) || !slot.history.length) {
      return;
    }
    captureActiveSlotSnapshot();
    const previousEntry = slot.history.pop();
    if (!previousEntry) {
      return;
    }
    slot.moduleKey = previousEntry.moduleKey;
    slot.subtabKey = previousEntry.subtabKey || getDefaultSubtabKey(previousEntry.moduleKey);
    slot.snapshot = previousEntry.snapshot || null;
    slot.needsRestore = true;
    activateSlot(slot.slotId, { forceRestore: true });
  }

  function sanitizeWorkspaceAgainstPermissions() {
    const workspace = ensureWorkspaceState();
    workspace.slots = workspace.slots
      .map((slot, index) => normalizeSlotShape(slot, index))
      .filter(Boolean)
      .slice(0, MAX_WORKSPACE_SLOTS);
    if (workspace.activePrimary !== "lobby" && !findSlotById(workspace.activePrimary)) {
      workspace.activePrimary = workspace.slots[0] ? workspace.slots[0].slotId : "lobby";
    }
  }

  function renderWorkspaceModal() {
    const modalRoot = getWorkspaceModalRoot();
    const workspace = ensureWorkspaceState();
    if (!modalRoot) {
      return;
    }
    if (!workspace.replaceDialogOpen || !workspace.pendingModuleKey) {
      modalRoot.innerHTML = "";
      return;
    }
    const nextModule = getModuleDefinition(workspace.pendingModuleKey);
    modalRoot.innerHTML = `
      <div class="modal-shell">
        <div class="modal-card">
          <div class="modal-header">
            <div>
              <h3>Podmien jeden z aktywnych modulow</h3>
              <p class="subtle-note">Wszystkie ${MAX_WORKSPACE_SLOTS} slotow sa zajete. Wybierz, ktory modul ma zostac zastapiony przez ${bezpiecznyTekst(nextModule.label)}.</p>
            </div>
            <button type="button" class="secondary" data-workspace-close-replace="1">Anuluj</button>
          </div>
          <div class="workspace-slot-choice-grid">
            ${workspace.slots
              .map(
                (slot) => `
                  <button type="button" class="workspace-slot-choice" data-workspace-replace-slot="${bezpiecznyTekst(slot.slotId)}">
                    <strong>${bezpiecznyTekst(getModuleDefinition(slot.moduleKey).label)}</strong>
                    <span>Aktywna podzakladka: ${bezpiecznyTekst(
                      getVisibleSubtabs(slot.moduleKey).find((item) => item.key === slot.subtabKey)?.label || getDefaultSubtabKey(slot.moduleKey)
                    )}</span>
                  </button>
                `
              )
              .join("")}
          </div>
        </div>
      </div>
    `;
  }

  function renderWorkspaceShell() {
    const root = getWorkspaceRoot();
    const workspace = ensureWorkspaceState();
    document.body.classList.toggle("workspace-shell-enabled", isWorkspaceEnabled());
    if (!root) {
      return;
    }
    if (!isWorkspaceEnabled()) {
      root.classList.add("hidden");
      root.innerHTML = "";
      renderWorkspaceModal();
      return;
    }
    sanitizeWorkspaceAgainstPermissions();
    root.classList.remove("hidden");

    const activeSlot = getActiveSlot();
    const activeModuleKey = activeSlot ? activeSlot.moduleKey : "dashboard";
    const activeSubtabs = activeSlot ? getVisibleSubtabs(activeModuleKey) : [];
    const activeDefinition = getModuleDefinition(activeModuleKey);

    root.innerHTML = `
      <div class="workspace-shell-card">
        <div class="workspace-shell-topbar">
          <div class="workspace-tab-list" id="workspace-primary-tabs">
            <button type="button" class="workspace-primary-tab workspace-primary-tab-lobby ${workspace.activePrimary === "lobby" ? "active" : ""}" data-workspace-primary="lobby">
              <span class="workspace-primary-tab-title">Lobby</span>
            </button>
            ${workspace.slots
              .map(
                (slot) => `
                  <button type="button" class="workspace-primary-tab ${workspace.activePrimary === slot.slotId ? "active" : ""}" data-workspace-primary="${bezpiecznyTekst(slot.slotId)}">
                    <span class="workspace-primary-tab-title">${bezpiecznyTekst(getModuleDefinition(slot.moduleKey).label)}</span>
                    <span class="workspace-primary-tab-close" role="button" tabindex="-1" aria-label="Zamknij modul ${bezpiecznyTekst(
                      getModuleDefinition(slot.moduleKey).label
                    )}" data-workspace-close-slot="${bezpiecznyTekst(slot.slotId)}">x</span>
                  </button>
                `
              )
              .join("")}
          </div>
          <div class="workspace-shell-actions">
            <button type="button" class="workspace-shell-icon" title="Wroc do poprzednio podmienionego modulu w tym slocie" aria-label="Wroc do poprzednio podmienionego modulu w tym slocie" ${activeSlot && activeSlot.history.length ? "" : "disabled"} data-workspace-slot-back="1">&#8592;</button>
            <button type="button" class="workspace-shell-icon" title="Rozwin cala liste otwartych modulow i podzakladek" aria-label="Rozwin cala liste otwartych modulow i podzakladek" aria-pressed="${workspace.expanded ? "true" : "false"}" data-workspace-toggle-map="1">${workspace.expanded ? "-" : "+"}</button>
          </div>
        </div>
        <div class="workspace-subtabs">
          ${
            activeSlot
              ? `
                <div class="workspace-subtabs-header">
                  <div class="workspace-subtabs-copy">
                    <span class="workspace-subtabs-kicker">Aktywny modul</span>
                    <p class="workspace-subtabs-title">${bezpiecznyTekst(activeDefinition.label)}</p>
                  </div>
                </div>
                <div class="workspace-subtabs-strip" id="workspace-subtabs-strip">
                  ${activeSubtabs
                    .map(
                      (subtab) => `
                        <button type="button" class="workspace-subtab ${subtab.key === activeSlot.subtabKey ? "active" : ""}" data-workspace-subtab="${bezpiecznyTekst(
                          subtab.key
                        )}" data-workspace-subtab-slot="${bezpiecznyTekst(activeSlot.slotId)}">${bezpiecznyTekst(subtab.label)}</button>
                      `
                    )
                    .join("")}
                </div>
              `
              : `<div class="workspace-shell-empty">Lobby jest strona startowa. Otworz modul z lewego docka albo z pasa rozszerzen.</div>`
          }
        </div>
        ${
          workspace.expanded
            ? `
              <div class="workspace-map">
                <div class="workspace-map-body">
                  <div class="workspace-map-group">
                    <div class="workspace-map-group-header">
                      <span class="workspace-map-group-title">Lobby</span>
                      <span class="workspace-map-group-meta">Strona startowa</span>
                    </div>
                    <button type="button" class="workspace-map-open ${workspace.activePrimary === "lobby" ? "active" : ""}" data-workspace-primary="lobby">Otworz Lobby</button>
                  </div>
                  ${workspace.slots
                    .map(
                      (slot) => `
                        <div class="workspace-map-group">
                          <div class="workspace-map-group-header">
                            <span class="workspace-map-group-title">${bezpiecznyTekst(getModuleDefinition(slot.moduleKey).label)}</span>
                            <span class="workspace-map-group-meta">${slot.history.length ? `Historia: ${slot.history.length}` : "Slot roboczy"}</span>
                          </div>
                          <button type="button" class="workspace-map-open ${workspace.activePrimary === slot.slotId ? "active" : ""}" data-workspace-primary="${bezpiecznyTekst(slot.slotId)}">Otworz modul</button>
                          <div class="workspace-map-subtabs">
                            ${getVisibleSubtabs(slot.moduleKey)
                              .map(
                                (subtab) => `
                                  <button type="button" class="workspace-map-subtab ${slot.subtabKey === subtab.key ? "active" : ""}" data-workspace-subtab="${bezpiecznyTekst(
                                    subtab.key
                                  )}" data-workspace-subtab-slot="${bezpiecznyTekst(slot.slotId)}">${bezpiecznyTekst(subtab.label)}</button>
                                `
                              )
                              .join("")}
                          </div>
                        </div>
                      `
                    )
                    .join("")}
                </div>
              </div>
            `
            : ""
        }
      </div>
    `;

    renderWorkspaceModal();
  }

  function restoreWorkspaceFromSnapshot(snapshot) {
    const workspace = ensureWorkspaceState();
    workspace.slots = Array.isArray(snapshot?.slots)
      ? snapshot.slots.map((slot, index) => normalizeSlotShape(slot, index)).filter(Boolean).slice(0, MAX_WORKSPACE_SLOTS)
      : [];
    workspace.expanded = Boolean(snapshot?.expanded);
    workspace.lobbyLastUsedAt = Number(snapshot?.lobby_last_used_at || 0) || nowTimestamp();
    workspace.activePrimary =
      snapshot?.active_primary === "lobby" || !snapshot?.active_primary ? "lobby" : String(snapshot.active_primary);
    if (workspace.activePrimary !== "lobby" && !findSlotById(workspace.activePrimary)) {
      workspace.activePrimary = workspace.slots[0] ? workspace.slots[0].slotId : "lobby";
    }
    renderWorkspaceShell();
    if (workspace.activePrimary === "lobby") {
      activateLobby({ skipPersist: true });
    } else {
      activateSlot(workspace.activePrimary, { skipPersist: true, forceRestore: true });
    }
  }

  function initializeDefaultWorkspace() {
    const workspace = ensureWorkspaceState();
    workspace.slots = [];
    workspace.expanded = false;
    workspace.activePrimary = "lobby";
    workspace.lobbyLastUsedAt = nowTimestamp();
    renderWorkspaceShell();
    activateLobby({ skipPersist: true });
  }

  async function refreshCurrentUserWithDeviceContext() {
    if (!isWorkspaceEnabled()) {
      return;
    }
    try {
      const currentUser = await api("/api/session/current", {}, { pominWylogowanie: true });
      if (currentUser && typeof currentUser === "object") {
        stan.biezacyUzytkownik = currentUser;
      }
    } catch (error) {
      console.warn("Nie udalo sie odswiezyc kontekstu sesji workspace.", error);
    }
  }

  function hydrateWorkspaceAfterSession() {
    const serverState = stan.biezacyUzytkownik?.workspace_state || null;
    const serverUpdatedAt = stan.biezacyUzytkownik?.workspace_state_updated_at || null;
    const localState = loadLocalWorkspaceState();
    const bestState = pickBestWorkspaceState(localState, serverState, serverUpdatedAt);
    if (bestState) {
      restoreWorkspaceFromSnapshot(bestState);
    } else if (stan.aktywnyWidok && stan.aktywnyWidok !== "dashboard" && canUseWorkspaceModule(stan.aktywnyWidok)) {
      const workspace = ensureWorkspaceState();
      const slot = createEmptySlot(stan.aktywnyWidok);
      workspace.slots = [slot];
      workspace.activePrimary = slot.slotId;
      renderWorkspaceShell();
      activateSlot(slot.slotId, { skipPersist: true });
    } else {
      initializeDefaultWorkspace();
    }
    scheduleWorkspacePersistence();
  }

  function resetWorkspaceState() {
    const workspace = ensureWorkspaceState();
    if (workspace.saveTimeoutId) {
      window.clearTimeout(workspace.saveTimeoutId);
      workspace.saveTimeoutId = null;
    }
    if (workspace.refreshIntervalId) {
      window.clearInterval(workspace.refreshIntervalId);
      workspace.refreshIntervalId = null;
    }
    workspace.activePrimary = "lobby";
    workspace.slots = [];
    workspace.expanded = false;
    workspace.pendingModuleKey = null;
    workspace.replaceDialogOpen = false;
    renderWorkspaceShell();
  }

  function moveToAdjacentSubtab(direction) {
    const slot = getActiveSlot();
    if (!slot) {
      return;
    }
    const subtabs = getVisibleSubtabs(slot.moduleKey);
    if (subtabs.length < 2) {
      return;
    }
    const currentIndex = subtabs.findIndex((item) => item.key === slot.subtabKey);
    if (currentIndex === -1) {
      return;
    }
    const nextIndex = currentIndex + direction;
    if (nextIndex < 0 || nextIndex >= subtabs.length) {
      return;
    }
    switchSubtab(slot.slotId, subtabs[nextIndex].key);
  }

  function isInteractiveTarget(target) {
    return Boolean(target?.closest("input, textarea, select, button, a, [contenteditable='true']"));
  }

  function bindWorkspaceInteractions() {
    const root = getWorkspaceRoot();
    const modalRoot = getWorkspaceModalRoot();
    const main = document.querySelector(".main");
    if (root && !root.dataset.workspaceBound) {
      root.dataset.workspaceBound = "1";
      root.addEventListener("click", (event) => {
        const closeButton = event.target.closest("[data-workspace-close-slot]");
        if (closeButton) {
          event.stopPropagation();
          closeWorkspaceSlot(closeButton.dataset.workspaceCloseSlot || "");
          return;
        }
        if (event.target.closest("[data-workspace-slot-back]")) {
          goBackToPreviousModuleInActiveSlot();
          return;
        }
        if (event.target.closest("[data-workspace-toggle-map]")) {
          const workspace = ensureWorkspaceState();
          workspace.expanded = !workspace.expanded;
          renderWorkspaceShell();
          scheduleWorkspacePersistence();
          return;
        }
        const primaryButton = event.target.closest("[data-workspace-primary]");
        if (primaryButton) {
          const primary = primaryButton.dataset.workspacePrimary || "lobby";
          if (primary === "lobby") {
            activateLobby();
          } else {
            activateSlot(primary);
          }
          return;
        }
        const subtabButton = event.target.closest("[data-workspace-subtab]");
        if (subtabButton) {
          switchSubtab(subtabButton.dataset.workspaceSubtabSlot || "", subtabButton.dataset.workspaceSubtab || "");
        }
      });
    }
    if (modalRoot && !modalRoot.dataset.workspaceBound) {
      modalRoot.dataset.workspaceBound = "1";
      modalRoot.addEventListener("click", (event) => {
        if (event.target === modalRoot.querySelector(".modal-shell") || event.target.closest("[data-workspace-close-replace]")) {
          closeReplaceDialog();
          return;
        }
        const replaceButton = event.target.closest("[data-workspace-replace-slot]");
        if (replaceButton) {
          replaceSlotModule(replaceButton.dataset.workspaceReplaceSlot || "", ensureWorkspaceState().pendingModuleKey);
        }
      });
    }
    if (main && !main.dataset.workspaceGesturesBound) {
      main.dataset.workspaceGesturesBound = "1";
      main.addEventListener(
        "wheel",
        (event) => {
          if (!isWorkspaceEnabled() || event.target.closest("#workspace-subtabs-strip") || isInteractiveTarget(event.target)) {
            return;
          }
          if (Math.abs(event.deltaX) > 26 && Math.abs(event.deltaX) > Math.abs(event.deltaY)) {
            event.preventDefault();
            moveToAdjacentSubtab(event.deltaX > 0 ? 1 : -1);
          }
        },
        { passive: false }
      );
      main.addEventListener(
        "touchstart",
        (event) => {
          if (!isWorkspaceEnabled() || event.target.closest("#workspace-subtabs-strip") || isInteractiveTarget(event.target)) {
            return;
          }
          const touch = event.changedTouches?.[0];
          if (!touch) {
            return;
          }
          ensureWorkspaceState().lastTouchStart = { x: touch.clientX, y: touch.clientY };
        },
        { passive: true }
      );
      main.addEventListener(
        "touchend",
        (event) => {
          const workspace = ensureWorkspaceState();
          const start = workspace.lastTouchStart;
          workspace.lastTouchStart = null;
          if (!start || event.target.closest("#workspace-subtabs-strip") || isInteractiveTarget(event.target)) {
            return;
          }
          const touch = event.changedTouches?.[0];
          if (!touch) {
            return;
          }
          const deltaX = touch.clientX - start.x;
          const deltaY = touch.clientY - start.y;
          if (Math.abs(deltaX) < 45 || Math.abs(deltaX) < Math.abs(deltaY)) {
            return;
          }
          moveToAdjacentSubtab(deltaX < 0 ? 1 : -1);
        },
        { passive: true }
      );
    }
  }

  function getRefreshPromiseForView(viewKey) {
    if (viewKey === "dashboard" && typeof wczytajPulpit === "function") return wczytajPulpit();
    if (viewKey === "invoices" && typeof wczytajFaktury === "function") return wczytajFaktury();
    if (viewKey === "knowledge" && typeof wczytajBazeWiedzy === "function") return wczytajBazeWiedzy();
    if (viewKey === "contractors" && typeof wczytajKontrahentow === "function") return wczytajKontrahentow();
    if (viewKey === "tasks") {
      const promises = [];
      if (typeof wczytajZadania === "function") promises.push(wczytajZadania());
      if (typeof wczytajPlannerZadan === "function") promises.push(wczytajPlannerZadan());
      if (typeof wczytajFokusZadan === "function") promises.push(wczytajFokusZadan());
      return Promise.all(promises);
    }
    if (viewKey === "billing" && typeof wczytajRozliczenia === "function") return wczytajRozliczenia();
    if (viewKey === "support" && typeof wczytajPomoc === "function") return wczytajPomoc();
    if (viewKey === "inbox" && typeof wczytajSkrzynkeWplywow === "function") return wczytajSkrzynkeWplywow();
    if (viewKey === "views" && typeof wczytajZapisaneWidoki === "function") return wczytajZapisaneWidoki();
    if (viewKey === "automation" && typeof wczytajAutomatyzacje === "function") return wczytajAutomatyzacje();
    if (viewKey === "health" && typeof wczytajZdrowieSystemu === "function") return wczytajZdrowieSystemu();
    if (viewKey === "logs" && typeof wczytajLogi === "function") return wczytajLogi();
    if (viewKey === "organizations" && typeof wczytajOrganizacje === "function") return wczytajOrganizacje();
    if (viewKey === "email-center" && typeof wczytajCentrumEmaila === "function") return wczytajCentrumEmaila();
    if (viewKey === "users" && typeof wczytajUzytkownikow === "function") return wczytajUzytkownikow();
    return Promise.resolve();
  }

  function shouldSkipAutoRefresh() {
    const activeElement = document.activeElement;
    return Boolean(activeElement && activeElement.matches("input, textarea, select"));
  }

  function refreshActiveWorkspaceView() {
    if (!isWorkspaceEnabled() || document.visibilityState === "hidden" || shouldSkipAutoRefresh()) {
      return;
    }
    const activeSlot = getActiveSlot();
    const viewKey = activeSlot ? getModuleDefinition(activeSlot.moduleKey).view : "dashboard";
    void Promise.resolve(getRefreshPromiseForView(viewKey)).catch(() => {});
  }

  function ensureWorkspaceRefreshLoop() {
    const workspace = ensureWorkspaceState();
    if (workspace.refreshIntervalId) {
      window.clearInterval(workspace.refreshIntervalId);
      workspace.refreshIntervalId = null;
    }
    if (!isWorkspaceEnabled()) {
      return;
    }
    workspace.refreshIntervalId = window.setInterval(() => {
      refreshActiveWorkspaceView();
    }, WORKSPACE_REFRESH_INTERVAL_MS);
  }

  function installWrappers() {
    ustawWidok = function workspaceAwareSetView(viewKey, options = {}) {
      if (!isWorkspaceEnabled() || options?.skipWorkspace === true || !WORKSPACE_ALLOWED_VIEWS.has(viewKey)) {
        return legacySetView(viewKey);
      }
      openModuleInWorkspace(viewKey, options);
    };

    sprobujPrzywrocicSesje = async function workspaceAwareSessionRestore() {
      const restored = await legacyTryRestoreSession();
      if (restored) {
        await refreshCurrentUserWithDeviceContext();
        renderWorkspaceShell();
        bindWorkspaceInteractions();
        ensureWorkspaceRefreshLoop();
      }
      return restored;
    };

    zalogujDoSystemu = async function workspaceAwareLogin(login, password) {
      await legacyLogin(login, password);
      await refreshCurrentUserWithDeviceContext();
      hydrateWorkspaceAfterSession();
      ensureWorkspaceRefreshLoop();
    };

    przygotujWidokPoWylogowaniu = function workspaceAwareLogoutReset() {
      resetWorkspaceState();
      return legacyPrepareLoggedOutView();
    };

    odswiezPasekSesji = function workspaceAwareRefreshSessionBar() {
      const result = legacyRefreshSessionBar();
      sanitizeWorkspaceAgainstPermissions();
      renderWorkspaceShell();
      return result;
    };
  }

  function bootWorkspaceShell() {
    ensureWorkspaceState();
    installWrappers();
    bindWorkspaceInteractions();
    renderWorkspaceShell();

    document.addEventListener("visibilitychange", () => {
      if (document.visibilityState === "visible") {
        refreshActiveWorkspaceView();
      }
    });
    window.addEventListener("focus", () => {
      refreshActiveWorkspaceView();
    });
    window.addEventListener("beforeunload", () => {
      saveWorkspaceStateLocally();
    });

    if (isWorkspaceEnabled()) {
      void refreshCurrentUserWithDeviceContext().finally(() => {
        hydrateWorkspaceAfterSession();
        ensureWorkspaceRefreshLoop();
      });
    } else {
      initializeDefaultWorkspace();
    }
  }

  bootWorkspaceShell();
})();
