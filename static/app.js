const stan = {
  meta: null,
  ustawieniaKomunikatorowSystemowych: null,
  faktury: [],
  zadania: [],
  rachunkiBankowe: [],
  transakcjeRozliczen: [],
  billingLedgerBalances: [],
  billingLedgerEntries: [],
  billingPaymentMatches: [],
  szkolyRozliczen: [],
  platnicyRozliczen: [],
  uczniowieRozliczen: [],
  modeleRozliczen: [],
  naleznosciRozliczen: [],
  ostatniImportWyciagu: null,
  kontrahenciWszyscy: [],
  kontrahenciWidoczni: [],
  logi: [],
  skrzynkaWeryfikacjiFaktur: null,
  workspaceWeryfikacjiFaktur: null,
  skrzynkaPrzyjeciaDokumentowFaktur: null,
  centrumWyjatkowFaktur: null,
  paczkiPrzekazaniaFaktur: null,
  szczegolyPaczkiPrzekazaniaFaktur: null,
  dokumentyWiedzy: [],
  odpowiedzBazyWiedzy: null,
  folderBazyWiedzy: "",
  konfiguracjaBazyWiedzy: null,
  ostatniImportBazyWiedzy: null,
  knowledgePollingTimeoutId: null,
  organizacje: [],
  notatkaOrganizacji: null,
  notatkaOrganizacjiTekstRoboczy: "",
  notatkaOrganizacjiOstatniTekst: "",
  notatkaOrganizacjiBrudna: false,
  notatkaOrganizacjiMaNowszaWersje: false,
  notatkaOrganizacjiZapisywanie: false,
  notatkaOsobista: null,
  notatkaOsobistaTekstRoboczy: "",
  notatkaOsobistaOstatniTekst: "",
  notatkaOsobistaBrudna: false,
  notatkaOsobistaMaNowszaWersje: false,
  notatkaOsobistaZapisywanie: false,
  uzytkownicy: [],
  inboxForms: [],
  inboxItems: [],
  inboxSelectedFormId: null,
  inboxSelectedItemDetail: null,
  inboxSelectedItemId: null,
  supportRequests: [],
  supportSelectedRequestId: null,
  supportSelectedRequestDetail: null,
  savedViews: [],
  savedViewSelectedId: null,
  invoiceSavedViews: [],
  invoiceSavedViewSelectedId: null,
  automationRules: [],
  automationExecutions: [],
  automationSelectedId: null,
  systemHealthSnapshot: null,
  googleCalendarAdminUsers: [],
  organizacyjneKalendarzeDoPrzypisania: [],
  centrumEmaila: null,
  uzytkownicyDoFaktur: [],
  uzytkownicyDoZadan: [],
  kalendarzeUzytkownika: [],
  statusPolaczeniaGoogleKalendarza: null,
  zewnetrzneKalendarzeGoogle: [],
  ustawieniaPrzypomnienUzytkownika: null,
  taskReminderStatus: null,
  taskReminderOutbox: [],
  taskReminderOutboxFilter: "all",
  taskTemplates: [],
  taskTemplateEditorId: null,
  taskNoteReplyTarget: null,
  powiazaniaEdytowanegoZadania: [],
  wybraneZadanieDetail: null,
  plannerZadan: null,
  fokusZadan: null,
  aktywnyWidokFokusu: "",
  taskCalendarMode: "miesiac",
  taskCalendarAnchor: null,
  taskCalendarDragTaskId: null,
  taskCalendarDragSourceDate: null,
  taskCalendarDragSourceField: null,
  taskCalendarConflictModalResolver: null,
  taskCalendarConflictModalContext: null,
  podgladNaturalnegoPolecenia: null,
  taskNaturalVoiceRecognition: null,
  taskNaturalVoiceBuffer: "",
  pwaInstallPrompt: null,
  pwaInstallable: false,
  wyszukiwanieGlobalneTimeoutId: null,
  contractorFilterApplyTimeoutId: null,
  invoiceFilterApplyTimeoutId: null,
  inboxFilterApplyTimeoutId: null,
  knowledgeFilterApplyTimeoutId: null,
  taskFilterApplyTimeoutId: null,
  wyszukiwanieGlobalneToken: 0,
  alertyPrzegladarkiWlaczone: window.localStorage.getItem("casi-browser-alerts-enabled") === "1",
  pokazaneAlertyPrzegladarki: new Set(),
  przypomnieniaPollingId: null,
  audioAlertUnlocked: false,
  biezacyUzytkownik: null,
  wybranaFakturaId: null,
  zaznaczoneFaktury: [],
  aktywnyKoszykWeryfikacjiFaktur: "verification",
  porownanieDuplikatowFaktur: null,
  podgladFaktury: null,
  wybraneZadanieId: null,
  wybranyKontrahentId: null,
  wybranaOrganizacjaId: "",
  wybranaOrganizacjaFormularzaId: null,
  czyZakresOrganizacjiZainicjalizowany: false,
  szybkiKalendarzOtwarty: false,
  szybkiPanelPracyOtwarty: false,
  szybkiPanelPracySekcja: "organization-note",
  szybkiPanelKalendarzaTryb: "miesiac",
  szybkiPanelKalendarzaZakres: "dzis",
  szybkiPanelKalendarzaKotwica: null,
  szybkiPanelZadanZakres: "dzis",
  szybkiPanelPodswietlonyTaskId: null,
  szybkiPanelPodswietlenieTimeoutId: null,
  miganieNawigacjiTimeoutId: null,
  profilMenuOtwarte: false,
  menuWiecejOtwarte: false,
  szybkiKalendarzZakres: "dzis",
  wybranyUzytkownikId: null,
  aktywnyWidok: "dashboard",
  czyFiltryFakturRozwiniete: false,
  czyZdarzeniaPodpiete: false,
  filtryKontrahentow: {
    szukaj: "",
    tylkoNowi: false,
  },
};

const QUICK_WORKSPACE_SEEN_STORAGE_KEY = "casi-quick-workspace-seen-v1";
const QUICK_WORKSPACE_TARGET_FLASH_CLASS = "quick-workspace-target-flash";
const QUICK_WORKSPACE_FLASH_OBSERVER_SELECTOR = [
  ".modal-shell",
  ".quick-add-sheet",
  ".sidebar-quick-calendar",
  ".topbar-menu-panel",
  "[id$='-detail']",
].join(", ");
const quickWorkspaceFlashTimestamps = new WeakMap();
let quickWorkspaceFlashObserver = null;
const quickWorkspaceSectionConfig = {
  "organization-note": {
    title: "Notatka organizacji",
    subtitle: "Wspolne ustalenia, statusy i dopiski dla calej organizacji.",
  },
  "personal-note": {
    title: "Notatka osobista",
    subtitle: "Twoja prywatna przestrzen robocza dostepna po zalogowaniu.",
  },
  calendar: {
    title: "Kalendarz",
    subtitle: "Najblizsze wpisy bez przechodzenia do calego modulu.",
  },
  tasks: {
    title: "Zadania",
    subtitle: "Szybki podglad rzeczy, ktore czekaja na reakcje.",
  },
  knowledge: {
    title: "Dokumenty firmowe",
    subtitle: "Twoje drafty, review i akceptacje bez przechodzenia przez cala biblioteke.",
  },
};

const opisyWidokow = {
  dashboard: {
    tytul: "Pulpit",
    podtytul: "PodglÄ…d najwaĹĽniejszych wskaĹşnikĂłw i ostatnich zdarzeĹ„.",
  },
  invoices: {
    tytul: "Faktury",
    podtytul: "Wyszukiwanie, filtrowanie i rÄ™czna weryfikacja dokumentĂłw.",
  },
  tasks: {
    tytul: "Asystent Szefa",
    podtytul: "Zadania, wydarzenia, terminy i notatki dla zespolu.",
  },
  billing: {
    tytul: "Rozliczenia",
    podtytul: "Aktualny etap modulu, import wyciagow CSV oraz mapa kolejnych wdrozen rozliczen.",
  },
  support: {
    tytul: "Pomoc",
    podtytul: "Zgloszenia, pytania do supportu i historia kontaktu w jednym miejscu.",
  },
  inbox: {
    tytul: "Inbox spraw",
    podtytul: "Zgloszenia, formularze, komentarze, zalaczniki i historia obiegu w jednym miejscu.",
  },
  views: {
    tytul: "Zapisane widoki",
    podtytul: "Szablony filtrowania i zestawy widokow per modul, gotowe do ponownego uzycia.",
  },
  automation: {
    tytul: "Automatyzacje",
    podtytul: "Reguly if/then oparte na zdarzeniach systemowych i wykonaniach w tle.",
  },
  health: {
    tytul: "Zdrowie systemu",
    podtytul: "Stan workera, backlog outboxa, inbox, automatyzacji, akceptacji i rozliczen.",
  },
  knowledge: {
    tytul: "Asystent Firmowy",
    podtytul: "Oddzielna baza wiedzy organizacji i odpowiedzi na pytania pracownikow.",
  },
  contractors: {
    tytul: "Kontrahenci",
    podtytul: "PrzeglÄ…d kontrahentĂłw, nowych podmiotĂłw i powiÄ…zanych faktur.",
  },
  logs: {
    tytul: "Historia systemu",
    podtytul: "PeĹ‚na historia zmian, decyzji i zdarzeĹ„ systemowych.",
  },
  organizations: {
    tytul: "Organizacje",
    podtytul: "Oddzielenie danych klientĂłw, folderĂłw i uĹĽytkownikĂłw wedĹ‚ug organizacji.",
  },
  "email-center": {
    tytul: "Centrum integracji",
    podtytul: "Stan e-maila, KSeF, OCR, Telegrama, Slacka i automatycznych cykli organizacji.",
  },
  users: {
    tytul: "UĹĽytkownicy",
    podtytul: "Konta uĹĽytkownikĂłw, role i podstawowa administracja dostÄ™pem.",
  },
};

const etykietyZrodel = {
  KSeF: "KSeF",
  KSEF: "KSeF",
  EMAIL: "E-mail",
  TELEGRAM: "Telegram",
  SLACK: "Slack",
  BANK_STATEMENT: "Wyciag bankowy",
};

const etykietyObieguFaktur = {
  w_pracy: "W pracy",
  gotowa_do_przekazania: "Gotowa do przekazania",
  przekazana: "Przekazana",
  zamknieta: "Zamknieta",
};

const etykietyZrodelBazyWiedzy = {
  manual: "Tekst reczny",
  upload: "Wgrany plik",
  folder_sync: "Folder organizacji",
};

const supportCategories = [
  {
    key: "problem_techniczny",
    label: "Problem techniczny",
    description: "Cos nie dziala, wyswietla blad albo zachowuje sie niepoprawnie.",
  },
  {
    key: "pytanie_o_funkcje",
    label: "Pytanie o funkcje",
    description: "Chcesz wiedziec, gdzie cos jest albo jak z tego korzystac.",
  },
  {
    key: "wdrozenie_i_konfiguracja",
    label: "Wdrozenie i konfiguracja",
    description: "Pomoc przy starcie, ustawieniach organizacji albo dostepach.",
  },
  {
    key: "dane_i_import",
    label: "Dane i import",
    description: "Problem z dokumentami, importem, synchronizacja albo historiÄ… danych.",
  },
  {
    key: "pomysl_i_rozwoj",
    label: "Pomysl i rozwoj",
    description: "Nowa funkcja, sugestia usprawnienia albo potrzeba biznesowa.",
  },
];

const domyslneFormatyBazyWiedzy = ["TXT", "MD", "CSV", "JSON", "XML", "HTML", "DOCX", "PDF", "XLSX", "JPG", "PNG", "TIFF"];

const etykietyZdarzen = {
  invoice_created: "Dodanie faktury",
  invoice_updated: "Aktualizacja faktury",
  invoice_status_changed: "Zmiana statusu faktury",
  ksef_authority_applied: "Potwierdzenie danych z KSeF",
  ksef_correction_requested: "Prosba o korekte danych KSeF",
  ksef_correction_applied: "Zatwierdzenie korekty danych KSeF",
  ksef_correction_rejected: "Odrzucenie korekty danych KSeF",
  duplicate_detected: "Wykrycie duplikatu",
  duplicate_rejected: "Odrzucenie podejrzenia duplikatu",
  duplicate_confirmed: "Potwierdzenie duplikatu",
  invoice_assigned: "Przypisanie faktury",
  invoice_reassigned: "Zmiana odpowiedzialnego za fakture",
  invoice_unassigned: "Usuniecie odpowiedzialnego za fakture",
  invoice_comment_added: "Dodanie komentarza do faktury",
  invoice_ready_for_handoff: "Gotowosc faktury do przekazania",
  invoice_handed_off: "Przekazanie faktury dalej",
  invoice_closed: "Zamkniecie faktury",
  invoice_reopened: "Ponowne otwarcie faktury",
  invoice_handoff_batch_created: "Utworzenie paczki przekazania",
  invoice_handoff_batch_exported: "Eksport paczki przekazania",
  email_connection_tested: "Test polaczenia e-mail",
  email_connection_test_failed: "Blad testu e-mail",
  email_check_executed: "Sprawdzenie e-mail",
  email_check_failed: "Blad sprawdzenia e-mail",
  ksef_connection_tested: "Test polaczenia KSeF",
  ksef_connection_test_failed: "Blad testu KSeF",
  ksef_check_executed: "Sprawdzenie KSeF",
  ksef_check_failed: "Blad sprawdzenia KSeF",
  contractor_created: "Utworzenie kontrahenta",
  telegram_notification_prepared: "Przygotowanie powiadomienia Telegram",
  mock_import_executed: "Wykonanie importu testowego",
  user_created: "Utworzenie uĹĽytkownika",
  user_updated: "Aktualizacja uĹĽytkownika",
  user_login: "Logowanie uĹĽytkownika",
  user_logout: "Wylogowanie uĹĽytkownika",
  organization_created: "Utworzenie organizacji",
  organization_updated: "Aktualizacja organizacji",
  organization_shared_note_updated: "Aktualizacja notatki organizacji",
  user_personal_note_updated: "Aktualizacja notatki osobistej",
  whiteboard_updated: "Aktualizacja tablicy",
  whiteboard_cleared: "Wyczyszczenie tablicy",
  whiteboard_image_added: "Dodanie obrazka do tablicy",
  whiteboard_image_transformed: "Przeksztalcenie obrazka na tablicy",
  task_created: "Dodanie zadania",
  task_updated: "Aktualizacja zadania",
  task_note_added: "Dodanie notatki do zadania",
  task_calendar_resynced: "Reczna synchronizacja kalendarza",
  task_calendar_checked: "Sprawdzenie stanu kalendarza",
  task_reminder_outbox_requeued: "Ponowienie wpisu outboxa",
  google_calendar_connected: "Polaczenie Google Calendar",
  google_calendar_disconnected: "Rozlaczenie Google Calendar",
  google_calendar_connection_pending: "Oczekiwanie na zatwierdzenie Google",
  google_calendar_connection_approved: "Zatwierdzenie konta Google",
  google_calendar_connection_rejected: "Odrzucenie konta Google",
  organization_calendar_assigned: "Przypisanie kalendarza organizacji",
  organization_calendar_assignment_removed: "Usuniecie przypisania kalendarza organizacji",
  user_calendar_created: "Dodanie kalendarza uĹĽytkownika",
  user_calendar_updated: "Aktualizacja kalendarza uĹĽytkownika",
  user_calendar_deleted: "UsuniÄ™cie kalendarza uĹĽytkownika",
  user_reminder_preferences_updated: "Aktualizacja ustawieĹ„ przypomnieĹ„",
  knowledge_document_created: "Dodanie dokumentu wiedzy",
  knowledge_document_updated: "Aktualizacja dokumentu wiedzy",
  knowledge_sync_executed: "Synchronizacja bazy wiedzy",
  billing_bank_account_created: "Dodanie rachunku bankowego",
  billing_statement_imported: "Import wyciagu bankowego",
};

const etykietyRol = {
  administrator: "WĹ‚aĹ›ciciel systemu",
  operator: "Operator",
  podglad: "GoĹ›Ä‡",
};

const etykietyRolSystemu = {
  system_owner: "WĹ‚aĹ›ciciel systemu",
  organization_admin: "Administrator organizacji",
  coordinator: "Koordynator",
  operator: "Operator",
  guest: "GoĹ›Ä‡",
};

etykietyRol.podglad = "GoĹ›Ä‡";
etykietyRol.guest = "GoĹ›Ä‡";

const roleGrupy = {
  userManagement: ["system_owner", "organization_admin"],
  organizationManagement: ["system_owner"],
  organizationSettings: ["system_owner", "organization_admin"],
  write: ["system_owner", "organization_admin", "coordinator", "operator"],
  invoiceDecision: ["system_owner", "organization_admin", "coordinator"],
  taskAssignment: ["system_owner", "organization_admin", "coordinator", "operator"],
  knowledgeUploadDefault: ["system_owner", "organization_admin", "coordinator", "operator"],
};

const organizationModuleCodes = {
  managerAssistant: "manager_assistant",
};

const moduleShortcutDefinitions = {
  dashboard: { label: "Pulpit", placeholder: "np. Ctrl+1" },
  invoices: { label: "Faktury", placeholder: "np. Ctrl+2" },
  knowledge: { label: "Asystent Firmowy", placeholder: "np. Ctrl+3" },
  contractors: { label: "Kontrahenci", placeholder: "np. Ctrl+4" },
  tasks: { label: "Asystent Szefa", placeholder: "np. Ctrl+5" },
  billing: { label: "Rozliczenia", placeholder: "np. Ctrl+6" },
  support: { label: "Pomoc", placeholder: "np. Ctrl+7" },
  inbox: { label: "Inbox", placeholder: "np. Ctrl+8" },
  views: { label: "Widoki", placeholder: "np. Ctrl+9" },
  automation: { label: "Automatyzacje", placeholder: "np. Ctrl+Shift+A" },
  health: { label: "Zdrowie systemu", placeholder: "np. Ctrl+Shift+H" },
  logs: { label: "Historia", placeholder: "np. Ctrl+Shift+L" },
  organizations: { label: "Organizacje", placeholder: "np. Alt+O" },
  "email-center": { label: "Centrum integracji", placeholder: "np. Alt+I" },
  users: { label: "Uzytkownicy", placeholder: "np. Alt+U" },
};

const capabilityLabels = {
  "knowledge.read": "Odczyt bazy wiedzy",
  "knowledge.upload": "Dodawanie plikow",
  "knowledge.sync": "Synchronizacja folderu",
  "knowledge.manage": "Zarzadzanie przetwarzaniem",
};

const defaultCapabilitiesByRole = {
  system_owner: ["knowledge.read", "knowledge.upload", "knowledge.sync", "knowledge.manage"],
  organization_admin: ["knowledge.read", "knowledge.upload", "knowledge.sync", "knowledge.manage"],
  coordinator: ["knowledge.read", "knowledge.upload", "knowledge.sync", "knowledge.manage"],
  operator: ["knowledge.read", "knowledge.upload", "knowledge.sync"],
  guest: ["knowledge.read"],
};

const etykietyTypowZadan = {
  zadanie: "Zadanie",
  wydarzenie: "Wydarzenie",
  przypomnienie: "Przypomnienie",
  notatka: "Notatka",
};

const etykietyStatusowZadan = {
  nowe: "Nowe",
  w_toku: "W toku",
  oczekuje: "Oczekuje",
  zakonczone: "Zakonczone",
  anulowane: "Anulowane",
};

const etykietyPriorytetowZadan = {
  niski: "Niski",
  normalny: "Normalny",
  wysoki: "Wysoki",
  krytyczny: "Krytyczny",
};

const etykietyStatusowSpraw = {
  nowe: "Nowe",
  w_toku: "W toku",
  oczekuje: "Oczekuje",
  zakonczone: "Zakonczone",
  zarchiwizowane: "Zarchiwizowane",
};

const etykietyWidocznosciZadan = {
  prywatne: "Prywatne",
  wybrane_osoby: "Wybrane osoby",
  organizacja: "Cala organizacja",
};

const etykietyCyklicznosciZadan = {
  brak: "Bez cyklu",
  codziennie: "Codziennie",
  co_tydzien: "Co tydzien",
  dni_robocze: "W dni robocze",
  co_miesiac: "Co miesiac",
};

const etykietyZakresowEdycjiSeriiZadan = {
  tylko_ten: "Tylko ten wpis",
  ten_i_nastepne: "Ten i nastepne",
  cala_seria: "Cala seria",
};

const etykietyWidokowFokusuZadan = {
  moj_dzien: "Moj dzien",
  przypisane_do_mnie: "Przypisane do mnie",
  do_decyzji: "Do decyzji",
  po_terminie: "Po terminie",
  czeka_na_kogos: "Czeka na kogos",
  prywatne: "Prywatne",
  organizacyjne: "Organizacyjne",
};

const etykietyRodzajowKalendarzy = {
  organizacja: "Organizacja",
  rodzinny: "Rodzinny",
  prywatny: "Prywatny",
  inne: "Sluzbowy osobisty",
};

const etykietyStatusowAkceptacji = {
  pending: "Oczekuje",
  approved: "Zatwierdzone",
  rejected: "Odrzucone",
  cancelled: "Anulowane",
};

const etykietyTypowAkceptacji = {
  task: "Zadanie",
  invoice: "Faktura",
  billing_charge: "Oplata",
  knowledge_document: "Dokument",
  decision: "Decyzja",
};

const chronionePolaKsef = [
  "invoice_number",
  "ksef_number",
  "issuer_nip",
  "issuer_name",
  "issue_date",
  "sale_date",
  "gross_amount",
  "currency",
];

const etykietyPolKsef = {
  invoice_number: "Numer faktury",
  ksef_number: "Numer KSeF",
  issuer_nip: "NIP wystawcy",
  issuer_name: "Nazwa wystawcy",
  issue_date: "Data wystawienia",
  sale_date: "Data sprzedazy",
  gross_amount: "Kwota brutto",
  currency: "Waluta",
};

const etykietyTypowNotatek = {
  comment: "Komentarz",
  reply: "Odpowiedz",
  decision: "Decyzja",
};

const skrotyPulpitu = {
  nowe_faktury: {
    etykieta: "Nowe faktury",
    zastosuj: async () => {
      wyczyscFiltryFaktur(false);
      document.querySelector('select[name="status"]').value = "nowa";
      ustawWidok("invoices");
      await wczytajFaktury();
    },
  },
  do_weryfikacji: {
    etykieta: "Do weryfikacji",
    zastosuj: async () => {
      wyczyscFiltryFaktur(false);
      document.querySelector('select[name="status"]').value = "weryfikacja";
      ustawWidok("invoices");
      await wczytajFaktury();
    },
  },
  podejrzenia_duplikatow: {
    etykieta: "Podejrzenia duplikatĂłw",
    zastosuj: async () => {
      wyczyscFiltryFaktur(false);
      document.querySelector('select[name="duplicate_type"]').value = "podejrzenie";
      ustawWidok("invoices");
      await wczytajFaktury();
    },
  },
  pewne_duplikaty: {
    etykieta: "Pewne duplikaty",
    zastosuj: async () => {
      wyczyscFiltryFaktur(false);
      document.querySelector('select[name="duplicate_type"]').value = "pewny";
      ustawWidok("invoices");
      await wczytajFaktury();
    },
  },
  nowi_kontrahenci: {
    etykieta: "Nowi kontrahenci",
    zastosuj: async () => {
      stan.filtryKontrahentow.szukaj = "";
      stan.filtryKontrahentow.tylkoNowi = true;
      document.getElementById("contractor-search").value = "";
      ustawWidok("contractors");
      await wczytajKontrahentow();
    },
  },
  aktywne_przypomnienia: {
    etykieta: "Aktywne przypomnienia",
    zastosuj: async () => {
      wyczyscFiltryZadan(false);
      document.getElementById("task-filter-due-reminders").checked = true;
      ustawWidok("tasks");
      await wczytajZadania();
    },
  },
};

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function humanizujKomunikatBledu(message) {
  const tekst = String(message || "");
  const tekstMaleLitery = tekst.toLowerCase();

  if (
    tekstMaleLitery.includes("unique constraint failed: invoices.invoice_hash") ||
    (tekstMaleLitery.includes("invoice_hash") &&
      (tekstMaleLitery.includes("duplicate key value violates unique constraint") ||
        tekstMaleLitery.includes("unique violation")))
  ) {
    return "Nie moĹĽna dodaÄ‡ dokumentu, poniewaĹĽ identyczna faktura zostaĹ‚a juĹĽ wczeĹ›niej zapisana.";
  }

  return tekst || "WystÄ…piĹ‚ bĹ‚Ä…d.";
}

async function api(url, options = {}, ustawienia = {}) {
  const body = options.body;
  const headers = { ...(options.headers || {}) };
  if (!(body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(url, {
    headers,
    credentials: "same-origin",
    ...options,
  });

  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : await response.text();

  if (!response.ok) {
    const rawMessage = typeof payload === "string" ? payload : payload.error || "WystÄ…piĹ‚ bĹ‚Ä…d.";
    const message = humanizujKomunikatBledu(rawMessage);
    const blad = new ApiError(message, response.status);
    if (response.status === 401 && !ustawienia.pominWylogowanie) {
      przygotujWidokPoWylogowaniu();
    }
    throw blad;
  }

  return payload;
}

function bezpiecznyTekst(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatujKwote(value, currency = "PLN") {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  return `${Number(value).toFixed(2)} ${currency}`;
}

function formatujWartosc(value) {
  return value === null || value === undefined || value === "" ? "-" : bezpiecznyTekst(value);
}

function formatujDateCzas(value) {
  if (!value) return "-";
  const data = new Date(value);
  if (Number.isNaN(data.getTime())) {
    return bezpiecznyTekst(value);
  }
  return bezpiecznyTekst(data.toLocaleString("pl-PL"));
}

function zbudujBadgeStanu(label, className = "") {
  const classes = ["status-badge"];
  if (className) {
    classes.push(className);
  }
  return `<span class="${classes.join(" ")}">${bezpiecznyTekst(label)}</span>`;
}

function formatujStatusAkceptacji(status) {
  const normalized = String(status || "").trim().toLowerCase();
  return etykietyStatusowAkceptacji[normalized] || normalized || "-";
}

function klasaStatusuAkceptacji(status) {
  const normalized = String(status || "").trim().toLowerCase();
  if (normalized === "approved") {
    return "status-success";
  }
  if (normalized === "rejected" || normalized === "cancelled") {
    return "status-danger";
  }
  return "status-warning";
}

function formatujTypAkceptacji(entityType) {
  const normalized = String(entityType || "").trim().toLowerCase();
  return etykietyTypowAkceptacji[normalized] || normalized || "-";
}

function formatujTypNotatki(noteKind) {
  const normalized = String(noteKind || "").trim().toLowerCase();
  return etykietyTypowNotatek[normalized] || normalized || "Komentarz";
}

function znajdzZadaniePoId(taskId) {
  return (Array.isArray(stan.zadania) ? stan.zadania : []).find((task) => Number(task.task_id) === Number(taskId)) || null;
}

function znajdzSzablonPoId(templateId) {
  return (Array.isArray(stan.taskTemplates) ? stan.taskTemplates : []).find(
    (template) => Number(template.task_template_id) === Number(templateId)
  ) || null;
}

function pobierzSzablonAkceptacjiDlaEncji(entityType) {
  const normalized = String(entityType || "").trim().toLowerCase();
  if (normalized === "invoice") {
    return {
      approve_status: "poprawna",
      reject_status: "odrzucona",
    };
  }
  if (normalized === "task") {
    return {
      approve_status: "w_toku",
      reject_status: "anulowane",
    };
  }
  return {
    approve_status: "approved",
    reject_status: "rejected",
  };
}

function pobierzStanEmailaOrganizacji(organizacja) {
  const inboxAddress = String(organizacja?.email_inbox_address || "").trim();
  const integrationEnabled = Number(organizacja?.email_integration_enabled || 0) === 1;
  const lastStatus = String(organizacja?.email_last_check_status || "").trim().toLowerCase();
  const lastConnectionStatus = String(organizacja?.email_last_connection_status || "").trim().toLowerCase();

  if (!inboxAddress) {
    return { label: "Brak skrzynki", className: "status-warning" };
  }
  if (stan.meta && !stan.meta.email_enabled) {
    return { label: "Brak IMAP", className: "status-danger" };
  }
  if (!integrationEnabled) {
    return { label: "Wylaczona", className: "status-warning" };
  }
  if (lastConnectionStatus) {
    if (lastConnectionStatus.includes("polaczenie imap dziala")) {
      if (!lastStatus) {
        return { label: "Polaczona", className: "status-success" };
      }
    } else {
      return { label: "Blad IMAP", className: "status-danger" };
    }
  }
  if (lastStatus.includes("zaimportowano")) {
    return { label: "Import OK", className: "status-success" };
  }
  if (lastStatus.includes("brak nowych")) {
    return { label: "Brak nowych", className: "" };
  }
  if (lastStatus.includes("wymaga") || lastStatus.includes("blad") || lastStatus.includes("nie udalo")) {
    return { label: "Wymaga uwagi", className: "status-danger" };
  }
  if (organizacja?.email_last_checked_at) {
    return { label: "Sprawdzona", className: "status-success" };
  }
  if (organizacja?.email_last_connection_tested_at) {
    return { label: "Testowana", className: "status-success" };
  }
  return { label: "Gotowa", className: "status-success" };
}

function renderujPodsumowanieEmailaOrganizacji(organizacja, overrideMessage = "") {
  const box = document.getElementById("organization-email-summary");
  if (!box) {
    return;
  }

  const komunikaty = [];
  if (overrideMessage) {
    komunikaty.push(overrideMessage);
  }

  if (stan.meta?.email_enabled) {
    komunikaty.push("Systemowy adapter e-mail jest gotowy. System pracuje na jednej centralnej skrzynce IMAP.");
  } else {
    komunikaty.push("Systemowy adapter e-mail nie jest jeszcze skonfigurowany. Uzupelnij .env.local albo data/local.env.");
  }

  const schedulerStatus = stan.meta?.email_scheduler_status || null;
  if (schedulerStatus?.active) {
    const intervalMinutes = Math.max(1, Math.round(Number(schedulerStatus.interval_seconds || 0) / 60));
    komunikaty.push(`Automatyczne sprawdzanie skrzynki jest wlaczone co ${intervalMinutes} min.`);
    if (schedulerStatus.last_finished_at && schedulerStatus.last_message) {
      komunikaty.push(`Ostatni cykl automatyczny: ${formatujDateCzas(schedulerStatus.last_finished_at)} - ${schedulerStatus.last_message}`);
    }
  } else if (schedulerStatus?.enabled && !schedulerStatus?.configured) {
    komunikaty.push("Automatyczne sprawdzanie jest przygotowane, ale czeka na konfiguracje IMAP.");
  }

  if (!organizacja || !organizacja.organization_id) {
    komunikaty.push("Zapisz organizacje, aby moc sprawdzac skrzynke e-mail.");
    box.innerHTML = komunikaty.map((tekst) => `<div>${bezpiecznyTekst(tekst)}</div>`).join("");
    return;
  }

  if (organizacja.email_inbox_address) {
    komunikaty.push(`Adres odbiorcy organizacji: ${organizacja.email_inbox_address}`);
  } else {
    komunikaty.push("Brakuje adresu odbiorcy organizacji.");
  }
  if (organizacja.email_allowed_sender) {
    komunikaty.push(`Dozwolony nadawca: ${organizacja.email_allowed_sender}`);
  }
  if (organizacja.email_subject_keyword) {
    komunikaty.push(`Fraza w temacie: ${organizacja.email_subject_keyword}`);
  }
  if (stan.meta?.email_routing_mode === "central_mailbox") {
    komunikaty.push("Dopasowanie odbywa sie po aliasie odbiorcy, nadawcy i frazie w temacie.");
  }
  if (stan.meta?.email_enabled && organizacja.email_inbox_address && !organizacja.email_last_connection_tested_at) {
    komunikaty.push("Najpierw kliknij 'Testuj polaczenie', aby sprawdzic skrzynke bez importu dokumentow.");
  }
  if (organizacja.email_last_connection_tested_at) {
    komunikaty.push(`Ostatni test polaczenia: ${formatujDateCzas(organizacja.email_last_connection_tested_at)}`);
  }
  if (organizacja.email_last_connection_status) {
    komunikaty.push(`Wynik testu polaczenia: ${organizacja.email_last_connection_status}`);
  }
  if (organizacja.email_last_checked_at) {
    komunikaty.push(`Ostatnie sprawdzenie skrzynki: ${formatujDateCzas(organizacja.email_last_checked_at)}`);
  }
  if (organizacja.email_last_check_status) {
    komunikaty.push(`Ostatni wynik importu: ${organizacja.email_last_check_status}`);
  }

  box.innerHTML = komunikaty.map((tekst) => `<div>${bezpiecznyTekst(tekst)}</div>`).join("");
}

function pobierzStanKsefOrganizacji(organizacja) {
  if (!organizacja) {
    return { label: "Brak konfiguracji", className: "status-warning" };
  }
  const integrationEnabled = Number(organizacja.ksef_integration_enabled || 0) === 1;
  const companyIdentifier = String(organizacja.ksef_company_identifier || "").trim();
  const lastStatus = String(organizacja.ksef_last_check_status || "").trim().toLowerCase();
  const lastConnectionStatus = String(organizacja.ksef_last_connection_status || "").trim().toLowerCase();

  if (!companyIdentifier) {
    return { label: "Brak identyfikatora", className: "status-warning" };
  }
  if (stan.meta && !stan.meta.ksef_enabled) {
    return { label: "Brak adaptera", className: "status-danger" };
  }
  if (!integrationEnabled) {
    return { label: "Wylaczona", className: "status-warning" };
  }
  if (lastConnectionStatus) {
    if (lastConnectionStatus.includes("gotowe") || lastConnectionStatus.includes("dziala")) {
      if (!lastStatus) {
        return { label: "Polaczona", className: "status-success" };
      }
    } else {
      return { label: "Blad KSeF", className: "status-danger" };
    }
  }
  if (lastStatus.includes("zaimportowano")) {
    return { label: "Import OK", className: "status-success" };
  }
  if (lastStatus.includes("brak nowych")) {
    return { label: "Brak nowych", className: "" };
  }
  if (lastStatus.includes("wymaga") || lastStatus.includes("blad") || lastStatus.includes("nie")) {
    return { label: "Wymaga uwagi", className: "status-danger" };
  }
  if (organizacja?.ksef_last_checked_at) {
    return { label: "Sprawdzona", className: "status-success" };
  }
  if (organizacja?.ksef_last_connection_tested_at) {
    return { label: "Testowana", className: "status-success" };
  }
  return { label: "Gotowa", className: "status-success" };
}

function renderujPodsumowanieKsefOrganizacji(organizacja, overrideMessage = "") {
  const box = document.getElementById("organization-ksef-summary");
  if (!box) {
    return;
  }

  const komunikaty = [];
  if (overrideMessage) {
    komunikaty.push(overrideMessage);
  }

  if (stan.meta?.ksef_enabled) {
    komunikaty.push("Systemowy adapter KSeF jest gotowy. Dane z KSeF sa nadrzedne wobec e-maila i Telegrama.");
  } else {
    komunikaty.push("Systemowy adapter KSeF nie jest jeszcze gotowy.");
  }

  if (!organizacja || !organizacja.organization_id) {
    komunikaty.push("Zapisz organizacje, aby moc testowac i sprawdzac KSeF.");
    box.innerHTML = komunikaty.map((tekst) => `<div>${bezpiecznyTekst(tekst)}</div>`).join("");
    return;
  }

  if (organizacja.ksef_company_identifier) {
    komunikaty.push(`Identyfikator firmy w KSeF: ${organizacja.ksef_company_identifier}`);
  } else {
    komunikaty.push("Brakuje identyfikatora firmy w KSeF.");
  }
  komunikaty.push(`Srodowisko: ${organizacja.ksef_environment === "production" ? "Produkcyjne" : "Demo"}`);
  if (organizacja.ksef_last_connection_tested_at) {
    komunikaty.push(`Ostatni test polaczenia: ${formatujDateCzas(organizacja.ksef_last_connection_tested_at)}`);
  }
  if (organizacja.ksef_last_connection_status) {
    komunikaty.push(`Wynik testu polaczenia: ${organizacja.ksef_last_connection_status}`);
  }
  if (organizacja.ksef_last_checked_at) {
    komunikaty.push(`Ostatnie sprawdzenie KSeF: ${formatujDateCzas(organizacja.ksef_last_checked_at)}`);
  }
  if (organizacja.ksef_last_check_status) {
    komunikaty.push(`Ostatni wynik importu: ${organizacja.ksef_last_check_status}`);
  }
  if (organizacja.ksef_correction_delegate_user_id) {
    const delegateName =
      organizacja.ksef_correction_delegate_user?.display_name ||
      organizacja.ksef_correction_delegate_user?.login ||
      pobierzNazweUzytkownika(organizacja.ksef_correction_delegate_user_id) ||
      `Uzytkownik #${organizacja.ksef_correction_delegate_user_id}`;
    komunikaty.push(`Tymczasowy kierownik korekt KSeF: ${delegateName}`);
    komunikaty.push(
      `Delegacja aktywna do: ${organizacja.ksef_correction_delegate_expires_at ? formatujDateCzas(organizacja.ksef_correction_delegate_expires_at) : "-"}`
    );
  } else {
    komunikaty.push("Prosby o korekte danych KSeF zatwierdza Administrator organizacji albo Wlasciciel systemu.");
  }

  box.innerHTML = komunikaty.map((tekst) => `<div>${bezpiecznyTekst(tekst)}</div>`).join("");
}

function pobierzEtykieteStatusuImportuEmaila(status) {
  const normalized = String(status || "").trim().toLowerCase();
  if (normalized === "completed") {
    return { label: "Import OK", className: "status-success" };
  }
  if (normalized === "completed_with_issues") {
    return { label: "Import z uwagami", className: "status-warning" };
  }
  if (normalized === "no_new_documents") {
    return { label: "Brak nowych", className: "" };
  }
  if (normalized === "failed") {
    return { label: "Blad importu", className: "status-danger" };
  }
  if (normalized === "running") {
    return { label: "W trakcie", className: "status-warning" };
  }
  return { label: "Nieznany", className: "status-warning" };
}

function pobierzEtykieteTrybuImportuEmaila(triggerMode) {
  const normalized = String(triggerMode || "").trim().toLowerCase();
  if (normalized === "automatic") {
    return { label: "Automatyczny", className: "status-success" };
  }
  return { label: "Reczny", className: "" };
}

function pobierzEtykieteStatusuImportuKsef(status) {
  return pobierzEtykieteStatusuImportuEmaila(status);
}

function pobierzEtykieteTrybuImportuKsef(triggerMode) {
  return pobierzEtykieteTrybuImportuEmaila(triggerMode);
}

function formatujAktoraImportuEmaila(run) {
  const triggerMode = String(run?.trigger_mode || "").trim().toLowerCase();
  if (triggerMode === "automatic") {
    return "Automat systemowy";
  }
  return String(run?.actor || "").trim() || "-";
}

function renderujHistorieImportowEmailaOrganizacji(runs, organizationId = null) {
  const container = document.getElementById("organization-email-import-runs");
  if (!container) {
    return;
  }

  if (!organizationId) {
    container.className = "empty-state";
    container.innerHTML = "Zapisz albo wybierz organizacje, aby zobaczyc historie sprawdzen skrzynki.";
    return;
  }

  if (!Array.isArray(runs) || !runs.length) {
    container.className = "empty-state";
    container.innerHTML = "Ta organizacja nie ma jeszcze historii importow e-mail.";
    return;
  }

  container.className = "list";
  container.innerHTML = runs
    .map((run) => {
      const status = pobierzEtykieteStatusuImportuEmaila(run.status);
      const triggerMode = pobierzEtykieteTrybuImportuEmaila(run.trigger_mode);
      const itemsPreview = Array.isArray(run.items_preview) ? run.items_preview : [];
      const previewHtml = itemsPreview.length
        ? `
          <div class="muted" style="margin-top: 10px;">Podglad dokumentow:</div>
          <div class="list" style="margin-top: 8px;">
            ${itemsPreview
              .map((item) => {
                const itemStatus = String(item.item_status || "").trim().toLowerCase();
                const itemBadge =
                  itemStatus === "imported"
                    ? zbudujBadgeStanu("Zaimportowano", "status-success")
                    : itemStatus === "skipped_existing"
                      ? zbudujBadgeStanu("Pominieto", "")
                      : zbudujBadgeStanu("Wymaga uwagi", "status-warning");
                const invoiceLink =
                  item.invoice_id && item.item_status === "imported"
                    ? `<button type="button" class="link-button" data-open-invoice-id="${item.invoice_id}">Otworz fakture #${item.invoice_id}</button>`
                    : "";
                return `
                  <article class="list-item">
                    <div style="display:flex; justify-content:space-between; gap:12px; align-items:flex-start; flex-wrap:wrap;">
                      <div>
                        <strong>${bezpiecznyTekst(item.attachment_name || item.subject || "Dokument e-mail")}</strong>
                        <div class="muted">${bezpiecznyTekst(item.sender_email || "-")}</div>
                        <div class="muted">${bezpiecznyTekst(item.subject || "-")}</div>
                      </div>
                      <div>${itemBadge}</div>
                    </div>
                    ${item.reason ? `<div style="margin-top:8px;">${bezpiecznyTekst(item.reason)}</div>` : ""}
                    ${invoiceLink ? `<div style="margin-top:8px;">${invoiceLink}</div>` : ""}
                  </article>
                `;
              })
              .join("")}
          </div>
        `
        : "";

      return `
        <article class="list-item">
          <div style="display:flex; justify-content:space-between; gap:12px; align-items:flex-start; flex-wrap:wrap;">
            <div>
              <strong>${bezpiecznyTekst(run.summary_message || "Sprawdzenie skrzynki e-mail")}</strong>
              <div class="muted">${formatujDateCzas(run.started_at)}${run.finished_at ? ` -> ${formatujDateCzas(run.finished_at)}` : ""}</div>
            </div>
            <div style="display:flex; gap:8px; flex-wrap:wrap;">
              ${zbudujBadgeStanu(triggerMode.label, triggerMode.className)}
              ${zbudujBadgeStanu(status.label, status.className)}
            </div>
          </div>
          <div style="margin-top:8px; display:grid; gap:4px;">
            <div class="muted">Uruchomione przez: ${bezpiecznyTekst(formatujAktoraImportuEmaila(run))}</div>
            <div class="muted">Sprawdzone wiadomosci: ${formatujWartosc(run.checked_message_count)}</div>
            <div class="muted">Dopasowane wiadomosci: ${formatujWartosc(run.matched_message_count)}</div>
            <div class="muted">Dopasowane zalaczniki: ${formatujWartosc(run.matched_attachment_count)}</div>
            <div class="muted">Zaimportowane faktury: ${formatujWartosc(run.imported_invoice_count)}</div>
            <div class="muted">Pominiete jako znane: ${formatujWartosc(run.skipped_existing_count)}</div>
            <div class="muted">Wymagajace uwagi: ${formatujWartosc(run.skipped_error_count)}</div>
          </div>
          ${previewHtml}
        </article>
      `;
    })
    .join("");

  container.querySelectorAll("[data-open-invoice-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      const invoiceId = Number(button.dataset.openInvoiceId || 0);
      if (!invoiceId) {
        return;
      }
      ustawWidok("invoices");
      stan.wybranaFakturaId = invoiceId;
      await Promise.all([wczytajFaktury(), wczytajSzczegolyFaktury(invoiceId)]);
    });
  });
}

async function wczytajHistorieImportowEmailaOrganizacji(organizationId) {
  const normalizedId = Number(organizationId || 0);
  if (!normalizedId) {
    renderujHistorieImportowEmailaOrganizacji([], null);
    return;
  }

  const runs = await api(`/api/organizations/${normalizedId}/email-import-runs?limit=6`);
  if (Number(stan.wybranaOrganizacjaFormularzaId || 0) !== normalizedId) {
    return;
  }
  renderujHistorieImportowEmailaOrganizacji(runs, normalizedId);
}

function renderujHistorieImportowKsefOrganizacji(runs, organizationId = null) {
  const container = document.getElementById("organization-ksef-import-runs");
  if (!container) {
    return;
  }

  if (!organizationId) {
    container.className = "empty-state";
    container.innerHTML = "Zapisz albo wybierz organizacje, aby zobaczyc historie sprawdzen KSeF.";
    return;
  }

  if (!Array.isArray(runs) || !runs.length) {
    container.className = "empty-state";
    container.innerHTML = "Ta organizacja nie ma jeszcze historii importow KSeF.";
    return;
  }

  container.className = "list";
  container.innerHTML = runs
    .map((run) => {
      const status = pobierzEtykieteStatusuImportuKsef(run.status);
      const triggerMode = pobierzEtykieteTrybuImportuKsef(run.trigger_mode);
      const itemsPreview = Array.isArray(run.items_preview) ? run.items_preview : [];
      const previewHtml = itemsPreview.length
        ? `
          <div class="muted" style="margin-top: 10px;">Podglad dokumentow:</div>
          <div class="list" style="margin-top: 8px;">
            ${itemsPreview
              .map((item) => {
                const itemStatus = String(item.item_status || "").trim().toLowerCase();
                const itemBadge =
                  itemStatus === "imported"
                    ? zbudujBadgeStanu("Zaimportowano", "status-success")
                    : itemStatus === "skipped_existing"
                      ? zbudujBadgeStanu("Pominieto", "")
                      : zbudujBadgeStanu("Wymaga uwagi", "status-warning");
                const invoiceLink =
                  item.invoice_id && itemStatus === "imported"
                    ? `<button type="button" class="link-button" data-open-ksef-invoice-id="${item.invoice_id}">Otworz fakture #${item.invoice_id}</button>`
                    : "";
                return `
                  <article class="list-item">
                    <div style="display:flex; justify-content:space-between; gap:12px; align-items:flex-start; flex-wrap:wrap;">
                      <div>
                        <strong>${bezpiecznyTekst(item.ksef_number || item.invoice_number || "Dokument KSeF")}</strong>
                        <div class="muted">${bezpiecznyTekst(item.invoice_number || "-")}</div>
                        <div class="muted">${bezpiecznyTekst(item.issuer_nip || "-")}</div>
                      </div>
                      <div>${itemBadge}</div>
                    </div>
                    ${item.reason ? `<div style="margin-top:8px;">${bezpiecznyTekst(item.reason)}</div>` : ""}
                    ${invoiceLink ? `<div style="margin-top:8px;">${invoiceLink}</div>` : ""}
                  </article>
                `;
              })
              .join("")}
          </div>
        `
        : "";

      return `
        <article class="list-item">
          <div style="display:flex; justify-content:space-between; gap:12px; align-items:flex-start; flex-wrap:wrap;">
            <div>
              <strong>${bezpiecznyTekst(run.summary_message || "Sprawdzenie KSeF")}</strong>
              <div class="muted">${formatujDateCzas(run.started_at)}${run.finished_at ? ` -> ${formatujDateCzas(run.finished_at)}` : ""}</div>
            </div>
            <div style="display:flex; gap:8px; flex-wrap:wrap;">
              ${zbudujBadgeStanu(triggerMode.label, triggerMode.className)}
              ${zbudujBadgeStanu(status.label, status.className)}
            </div>
          </div>
          <div style="margin-top:8px; display:grid; gap:4px;">
            <div class="muted">Uruchomione przez: ${bezpiecznyTekst(run.actor || "-")}</div>
            <div class="muted">Srodowisko: ${bezpiecznyTekst(run.environment || "-")}</div>
            <div class="muted">Identyfikator firmy: ${bezpiecznyTekst(run.company_identifier || "-")}</div>
            <div class="muted">Sprawdzone dokumenty: ${formatujWartosc(run.checked_document_count)}</div>
            <div class="muted">Zaimportowane faktury: ${formatujWartosc(run.imported_invoice_count)}</div>
            <div class="muted">Pominiete jako znane: ${formatujWartosc(run.skipped_existing_count)}</div>
            <div class="muted">Wymagajace uwagi: ${formatujWartosc(run.skipped_error_count)}</div>
          </div>
          ${previewHtml}
        </article>
      `;
    })
    .join("");

  container.querySelectorAll("[data-open-ksef-invoice-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      const invoiceId = Number(button.dataset.openKsefInvoiceId || 0);
      if (!invoiceId) {
        return;
      }
      ustawWidok("invoices");
      stan.wybranaFakturaId = invoiceId;
      await Promise.all([wczytajFaktury(), wczytajSzczegolyFaktury(invoiceId)]);
    });
  });
}

async function wczytajHistorieImportowKsefOrganizacji(organizationId) {
  const normalizedId = Number(organizationId || 0);
  if (!normalizedId) {
    renderujHistorieImportowKsefOrganizacji([], null);
    return;
  }

  const runs = await api(`/api/organizations/${normalizedId}/ksef-import-runs?limit=6`);
  if (Number(stan.wybranaOrganizacjaFormularzaId || 0) !== normalizedId) {
    return;
  }
  renderujHistorieImportowKsefOrganizacji(runs, normalizedId);
}

function renderujBiegiCentrumEmaila(runs) {
  const container = document.getElementById("email-center-runs");
  const count = document.getElementById("email-center-count");
  if (!container || !count) {
    return;
  }

  const items = Array.isArray(runs) ? runs : [];
  count.textContent = items.length ? `${items.length} wpisow` : "";

  if (!items.length) {
    container.className = "empty-state";
    container.innerHTML = "Brak zapisanych importow e-mail w tym zakresie.";
    return;
  }

  container.className = "list";
  container.innerHTML = items
    .map((run) => {
      const status = pobierzEtykieteStatusuImportuEmaila(run.status);
      const triggerMode = pobierzEtykieteTrybuImportuEmaila(run.trigger_mode);
      const itemsPreview = Array.isArray(run.items_preview) ? run.items_preview : [];
      const organizationLine = run.organization_name
        ? `<div class="muted">Organizacja: ${bezpiecznyTekst(run.organization_name)}</div>`
        : "";
      const previewHtml = itemsPreview.length
        ? `
          <div class="muted" style="margin-top: 10px;">Podglad dokumentow:</div>
          <div class="list" style="margin-top: 8px;">
            ${itemsPreview
              .map((item) => {
                const itemStatus = String(item.item_status || "").trim().toLowerCase();
                const itemBadge =
                  itemStatus === "imported"
                    ? zbudujBadgeStanu("Zaimportowano", "status-success")
                    : itemStatus === "skipped_existing"
                      ? zbudujBadgeStanu("Pominieto", "")
                      : zbudujBadgeStanu("Wymaga uwagi", "status-warning");
                const invoiceLink =
                  item.invoice_id && itemStatus === "imported"
                    ? `<button type="button" class="link-button" data-email-center-open-invoice-id="${item.invoice_id}">Otworz fakture #${item.invoice_id}</button>`
                    : "";
                return `
                  <article class="list-item">
                    <div style="display:flex; justify-content:space-between; gap:12px; align-items:flex-start; flex-wrap:wrap;">
                      <div>
                        <strong>${bezpiecznyTekst(item.attachment_name || item.subject || "Dokument e-mail")}</strong>
                        <div class="muted">${bezpiecznyTekst(item.sender_email || "-")}</div>
                        <div class="muted">${bezpiecznyTekst(item.subject || "-")}</div>
                      </div>
                      <div>${itemBadge}</div>
                    </div>
                    ${item.reason ? `<div style="margin-top:8px;">${bezpiecznyTekst(item.reason)}</div>` : ""}
                    ${invoiceLink ? `<div style="margin-top:8px;">${invoiceLink}</div>` : ""}
                  </article>
                `;
              })
              .join("")}
          </div>
        `
        : "";

      return `
        <article class="list-item">
          <div style="display:flex; justify-content:space-between; gap:12px; align-items:flex-start; flex-wrap:wrap;">
            <div>
              <strong>${bezpiecznyTekst(run.summary_message || "Sprawdzenie skrzynki e-mail")}</strong>
              <div class="muted">${formatujDateCzas(run.started_at)}${run.finished_at ? ` -> ${formatujDateCzas(run.finished_at)}` : ""}</div>
              ${organizationLine}
            </div>
            <div style="display:flex; gap:8px; flex-wrap:wrap;">
              ${zbudujBadgeStanu(triggerMode.label, triggerMode.className)}
              ${zbudujBadgeStanu(status.label, status.className)}
            </div>
          </div>
          <div style="margin-top:8px; display:grid; gap:4px;">
            <div class="muted">Uruchomione przez: ${bezpiecznyTekst(formatujAktoraImportuEmaila(run))}</div>
            <div class="muted">Sprawdzone wiadomosci: ${formatujWartosc(run.checked_message_count)}</div>
            <div class="muted">Dopasowane wiadomosci: ${formatujWartosc(run.matched_message_count)}</div>
            <div class="muted">Dopasowane zalaczniki: ${formatujWartosc(run.matched_attachment_count)}</div>
            <div class="muted">Zaimportowane faktury: ${formatujWartosc(run.imported_invoice_count)}</div>
            <div class="muted">Pominiete jako znane: ${formatujWartosc(run.skipped_existing_count)}</div>
            <div class="muted">Wymagajace uwagi: ${formatujWartosc(run.skipped_error_count)}</div>
          </div>
          ${previewHtml}
        </article>
      `;
    })
    .join("");

  container.querySelectorAll("[data-email-center-open-invoice-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      const invoiceId = Number(button.dataset.emailCenterOpenInvoiceId || 0);
      if (!invoiceId) {
        return;
      }
      ustawWidok("invoices");
      stan.wybranaFakturaId = invoiceId;
      await Promise.all([wczytajFaktury(), wczytajSzczegolyFaktury(invoiceId)]);
    });
  });
}

function renderujBiegiCentrumKsef(runs) {
  const container = document.getElementById("ksef-center-runs");
  const count = document.getElementById("ksef-center-count");
  if (!container || !count) {
    return;
  }

  const items = Array.isArray(runs) ? runs : [];
  count.textContent = items.length ? `${items.length} wpisow` : "";

  if (!items.length) {
    container.className = "empty-state";
    container.innerHTML = "Brak zapisanych importow KSeF w tym zakresie.";
    return;
  }

  container.className = "list";
  container.innerHTML = items
    .map((run) => {
      const status = pobierzEtykieteStatusuImportuKsef(run.status);
      const triggerMode = pobierzEtykieteTrybuImportuKsef(run.trigger_mode);
      const itemsPreview = Array.isArray(run.items_preview) ? run.items_preview : [];
      const organizationLine = run.organization_name
        ? `<div class="muted">Organizacja: ${bezpiecznyTekst(run.organization_name)}</div>`
        : "";
      const previewHtml = itemsPreview.length
        ? `
          <div class="muted" style="margin-top: 10px;">Podglad dokumentow:</div>
          <div class="list" style="margin-top: 8px;">
            ${itemsPreview
              .map((item) => {
                const itemStatus = String(item.item_status || "").trim().toLowerCase();
                const itemBadge =
                  itemStatus === "imported"
                    ? zbudujBadgeStanu("Zaimportowano", "status-success")
                    : itemStatus === "skipped_existing"
                      ? zbudujBadgeStanu("Pominieto", "")
                      : zbudujBadgeStanu("Wymaga uwagi", "status-warning");
                const invoiceLink =
                  item.invoice_id && itemStatus === "imported"
                    ? `<button type="button" class="link-button" data-ksef-center-open-invoice-id="${item.invoice_id}">Otworz fakture #${item.invoice_id}</button>`
                    : "";
                return `
                  <article class="list-item">
                    <div style="display:flex; justify-content:space-between; gap:12px; align-items:flex-start; flex-wrap:wrap;">
                      <div>
                        <strong>${bezpiecznyTekst(item.ksef_number || item.invoice_number || "Dokument KSeF")}</strong>
                        <div class="muted">${bezpiecznyTekst(item.invoice_number || "-")}</div>
                        <div class="muted">${bezpiecznyTekst(item.issuer_nip || "-")}</div>
                      </div>
                      <div>${itemBadge}</div>
                    </div>
                    ${item.reason ? `<div style="margin-top:8px;">${bezpiecznyTekst(item.reason)}</div>` : ""}
                    ${invoiceLink ? `<div style="margin-top:8px;">${invoiceLink}</div>` : ""}
                  </article>
                `;
              })
              .join("")}
          </div>
        `
        : "";

      return `
        <article class="list-item">
          <div style="display:flex; justify-content:space-between; gap:12px; align-items:flex-start; flex-wrap:wrap;">
            <div>
              <strong>${bezpiecznyTekst(run.summary_message || "Sprawdzenie KSeF")}</strong>
              <div class="muted">${formatujDateCzas(run.started_at)}${run.finished_at ? ` -> ${formatujDateCzas(run.finished_at)}` : ""}</div>
              ${organizationLine}
            </div>
            <div style="display:flex; gap:8px; flex-wrap:wrap;">
              ${zbudujBadgeStanu(triggerMode.label, triggerMode.className)}
              ${zbudujBadgeStanu(status.label, status.className)}
            </div>
          </div>
          <div style="margin-top:8px; display:grid; gap:4px;">
            <div class="muted">Uruchomione przez: ${bezpiecznyTekst(run.actor || "-")}</div>
            <div class="muted">Srodowisko: ${bezpiecznyTekst(run.environment || "-")}</div>
            <div class="muted">Identyfikator firmy: ${bezpiecznyTekst(run.company_identifier || "-")}</div>
            <div class="muted">Sprawdzone dokumenty: ${formatujWartosc(run.checked_document_count)}</div>
            <div class="muted">Zaimportowane faktury: ${formatujWartosc(run.imported_invoice_count)}</div>
            <div class="muted">Pominiete jako znane: ${formatujWartosc(run.skipped_existing_count)}</div>
            <div class="muted">Wymagajace uwagi: ${formatujWartosc(run.skipped_error_count)}</div>
          </div>
          ${previewHtml}
        </article>
      `;
    })
    .join("");

  container.querySelectorAll("[data-ksef-center-open-invoice-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      const invoiceId = Number(button.dataset.ksefCenterOpenInvoiceId || 0);
      if (!invoiceId) {
        return;
      }
      ustawWidok("invoices");
      stan.wybranaFakturaId = invoiceId;
      await Promise.all([wczytajFaktury(), wczytajSzczegolyFaktury(invoiceId)]);
    });
  });
}

function renderujCentrumEmaila(snapshot) {
  stan.centrumEmaila = snapshot || null;
  const summary = document.getElementById("email-center-summary");
  const connectButton = document.getElementById("email-center-google-connect");
  const disconnectButton = document.getElementById("email-center-google-disconnect");
  const refreshButton = document.getElementById("email-center-refresh");
  if (!summary || !connectButton || !disconnectButton || !refreshButton) {
    return;
  }

  if (!snapshot) {
    summary.className = "empty-state";
    summary.innerHTML = "Brak danych centrum integracji.";
    renderujBiegiCentrumEmaila([]);
    renderujBiegiCentrumKsef([]);
    return;
  }

  const emailSnapshot = snapshot.email || {};
  const ksefSnapshot = snapshot.ksef || {};
  const integration = emailSnapshot.integration || {};
  const ksefIntegration = ksefSnapshot.integration || {};
  const scheduler = snapshot.scheduler || {};
  const scope = snapshot.scope || {};
  const summaryStats = emailSnapshot.summary || {};
  const ksefSummary = ksefSnapshot.summary || {};
  const connection = integration.google_connection || null;
  const oauthEnabled = Boolean(stan.meta?.email_google_oauth_enabled || integration.google_oauth_enabled);
  const isOwner = czyGlobalnyAdministrator();
  const modeLabel =
    integration.mode === "google_oauth"
      ? "Google Workspace OAuth"
      : integration.mode === "imap"
        ? "IMAP"
        : "Brak konfiguracji";
  const schedulerLabel =
    scheduler.active
      ? `Automat wlaczony co ${Math.max(1, Math.round(Number(scheduler.interval_seconds || 0) / 60))} min.`
      : scheduler.enabled
        ? "Automat czeka na pelna konfiguracje skrzynki."
        : "Automatyczne sprawdzanie jest wylaczone w konfiguracji.";
  const connectionLabel = connection?.google_email
    ? `Polaczona centralna skrzynka Google Workspace: ${connection.google_email}`
    : oauthEnabled
      ? "Google Workspace jest gotowy do polaczenia, ale skrzynka nie jest jeszcze autoryzowana."
      : "Google Workspace OAuth nie jest jeszcze gotowy w konfiguracji systemu.";
  const scopeLabel = scope.organization_name
    ? `Zakres: ${scope.organization_name}`
    : "Zakres: wszystkie organizacje";
  const statusBadge = connection?.google_email
    ? zbudujBadgeStanu("Google Workspace polaczone", "status-success")
    : oauthEnabled
      ? zbudujBadgeStanu("Google Workspace niepolaczone", "status-warning")
      : zbudujBadgeStanu("OAuth niewlaczony", "status-warning");
  const ksefStatusBadge = ksefIntegration.enabled
    ? zbudujBadgeStanu("KSeF gotowy", "status-success")
    : zbudujBadgeStanu("KSeF niewlaczony", "status-warning");

  summary.className = "stack";
  summary.innerHTML = `
    <div class="history-header">
      <div>
        <strong>${bezpiecznyTekst(scopeLabel)}</strong>
        <div class="muted">${bezpiecznyTekst(connectionLabel)}</div>
      </div>
      <div>${statusBadge}</div>
    </div>
    <div>Tryb skrzynki: ${bezpiecznyTekst(modeLabel)}</div>
    <div>Adres skrzynki: ${bezpiecznyTekst(integration.mailbox_address || "-")}</div>
    <div>Folder: ${bezpiecznyTekst(integration.folder || "-")} | Limit na cykl: ${bezpiecznyTekst(integration.fetch_limit || "-")}</div>
    <div>${bezpiecznyTekst(schedulerLabel)}</div>
    ${
      scheduler.last_finished_at && scheduler.last_message
        ? `<div>Ostatni cykl: ${bezpiecznyTekst(formatujDateCzas(scheduler.last_finished_at))} - ${bezpiecznyTekst(
            scheduler.last_message
          )}</div>`
        : ""
    }
    <div>
      Gotowych organizacji: ${bezpiecznyTekst(emailSnapshot.ready_organization_count || 0)} |
      Ostatnio zaimportowane faktury: ${bezpiecznyTekst(summaryStats.imported_invoice_count || 0)} |
      Sprawdzone wiadomosci: ${bezpiecznyTekst(summaryStats.checked_message_count || 0)}
    </div>
    <hr />
    <div class="history-header">
      <div>
        <strong>KSeF</strong>
        <div class="muted">Tryb: ${bezpiecznyTekst(ksefIntegration.mode || "-")} | Limit na cykl: ${bezpiecznyTekst(ksefIntegration.fetch_limit || "-")}</div>
      </div>
      <div>${ksefStatusBadge}</div>
    </div>
    <div>
      Gotowych organizacji: ${bezpiecznyTekst(ksefSnapshot.ready_organization_count || 0)} |
      Ostatnio zaimportowane faktury: ${bezpiecznyTekst(ksefSummary.imported_invoice_count || 0)} |
      Sprawdzone dokumenty: ${bezpiecznyTekst(ksefSummary.checked_document_count || 0)}
    </div>
    <div>Telegram: ${bezpiecznyTekst(snapshot.telegram?.enabled ? "Wlaczony" : "Wylaczony")} | OCR: ${bezpiecznyTekst(snapshot.ocr?.mode || "-")} | Magazyn: ${bezpiecznyTekst(snapshot.storage?.backend || "-")}</div>
  `;

  connectButton.classList.toggle("hidden", !isOwner);
  disconnectButton.classList.toggle("hidden", !isOwner);
  connectButton.disabled = !isOwner || !oauthEnabled;
  disconnectButton.disabled = !isOwner || !connection;
  refreshButton.disabled = !czyMoznaOtworzycCentrumEmaila();
  connectButton.title = oauthEnabled ? "" : "Najpierw uzupelnij dane Google OAuth po stronie systemu.";
  disconnectButton.title = connection ? "" : "Brak polaczonej centralnej skrzynki Google Workspace.";
  refreshButton.title = "";

  renderujBiegiCentrumEmaila(emailSnapshot.runs || []);
  renderujBiegiCentrumKsef(ksefSnapshot.runs || []);
}

async function wczytajCentrumEmaila() {
  if (!czyMoznaOtworzycCentrumEmaila()) {
    stan.centrumEmaila = null;
    renderujCentrumEmaila(null);
    return null;
  }

  const summary = document.getElementById("email-center-summary");
  const runs = document.getElementById("email-center-runs");
  const count = document.getElementById("email-center-count");
  const ksefRuns = document.getElementById("ksef-center-runs");
  const ksefCount = document.getElementById("ksef-center-count");
  if (summary) {
    summary.className = "empty-state";
    summary.innerHTML = "Ladowanie centrum integracji...";
  }
  if (runs) {
    runs.className = "empty-state";
    runs.innerHTML = "Ladowanie historii importow e-mail...";
  }
  if (count) {
    count.textContent = "";
  }
  if (ksefRuns) {
    ksefRuns.className = "empty-state";
    ksefRuns.innerHTML = "Ladowanie historii importow KSeF...";
  }
  if (ksefCount) {
    ksefCount.textContent = "";
  }

  const snapshot = await api(zbudujAdresZOrganizacja("/api/integration-center?limit=25"));
  renderujCentrumEmaila(snapshot);
  return snapshot;
}

async function polaczGoogleEmail() {
  if (!czyGlobalnyAdministrator()) {
    pokazPowiadomienie("Tylko Wlasciciel systemu moze polaczyc centralna skrzynke Google Workspace.");
    return;
  }
  const loginHint = String(stan.meta?.email_google_connection?.google_email || "").trim();
  const response = await api("/api/email/google/connect", {
    method: "POST",
    body: JSON.stringify({ login_hint: loginHint || null }),
  });
  const popup = window.open(
    response.authorization_url,
    "email-google-connect",
    "popup=yes,width=640,height=780,resizable=yes,scrollbars=yes"
  );
  if (!popup) {
    window.location.href = response.authorization_url;
    return;
  }
  popup.focus();
  pokazPowiadomienie("Otwarto okno polaczenia Google Workspace dla e-mail.");
}

async function rozlaczGoogleEmail() {
  if (!czyGlobalnyAdministrator()) {
    pokazPowiadomienie("Tylko Wlasciciel systemu moze rozlaczyc centralna skrzynke Google Workspace.");
    return;
  }
  const result = await api("/api/email/google/disconnect", { method: "POST" });
  await Promise.all([wczytajMeta(), wczytajCentrumEmaila(), wczytajLogi()]);
  if (result.google_email) {
    pokazPowiadomienie(`Rozlaczono skrzynke ${result.google_email}.`);
  } else {
    pokazPowiadomienie("Rozlaczono centralna skrzynke Google Workspace.");
  }
}

function formatujRozmiarPliku(value) {
  const size = Number(value || 0);
  if (!Number.isFinite(size) || size <= 0) {
    return "0 B";
  }

  const units = ["B", "KB", "MB", "GB"];
  let current = size;
  let unitIndex = 0;
  while (current >= 1024 && unitIndex < units.length - 1) {
    current /= 1024;
    unitIndex += 1;
  }

  const digits = current >= 100 || unitIndex === 0 ? 0 : 1;
  return `${current.toFixed(digits).replace(".", ",")} ${units[unitIndex]}`;
}

function formatujZrodlo(value) {
  if (!value) return "-";
  return etykietyZrodel[value] || bezpiecznyTekst(value);
}

function formatujTypZdarzenia(value) {
  if (!value) return "-";
  return etykietyZdarzen[value] || bezpiecznyTekst(value);
}

function formatujRole(value) {
  if (!value) return "-";
  return etykietyRolSystemu[value] || etykietyRol[value] || bezpiecznyTekst(value);
}

function formatujObiegFaktury(value) {
  if (!value) return "-";
  return etykietyObieguFaktur[value] || bezpiecznyTekst(value);
}

function formatujTypZadania(value) {
  if (!value) return "-";
  return etykietyTypowZadan[value] || bezpiecznyTekst(value);
}

function formatujStatusZadania(value) {
  if (!value) return "-";
  return etykietyStatusowZadan[value] || bezpiecznyTekst(value);
}

function formatujPriorytetZadania(value) {
  if (!value) return "-";
  return etykietyPriorytetowZadan[value] || bezpiecznyTekst(value);
}

function formatujStatusSprawy(value) {
  if (!value) return "-";
  return etykietyStatusowSpraw[value] || bezpiecznyTekst(value);
}

function formatujPriorytetSprawy(value) {
  const labels = {
    niski: "Niski",
    normalny: "Normalny",
    wysoki: "Wysoki",
    pilny: "Pilny",
  };
  if (!value) return "-";
  return labels[value] || bezpiecznyTekst(value);
}

function klasaStatusuSprawy(value) {
  const normalized = String(value || "").trim().toLowerCase();
  if (normalized === "zakonczone" || normalized === "zarchiwizowane") {
    return "status-success";
  }
  if (normalized === "oczekuje") {
    return "status-warning";
  }
  return "status-normal";
}

function formatujKategorieSupportu(value) {
  const normalized = String(value || "").trim().toLowerCase();
  const found = supportCategories.find((item) => item.key === normalized);
  return found ? found.label : normalized || "OgĂłlne";
}

function pobierzKategorieSupportuZMetadanych(item) {
  const metadata = item?.metadata_json;
  if (!metadata || typeof metadata !== "object") {
    return "";
  }
  return String(metadata.support_category || metadata.category || "").trim().toLowerCase();
}

function formatujWidocznoscZadania(value) {
  if (!value) return "-";
  return etykietyWidocznosciZadan[value] || bezpiecznyTekst(value);
}

function formatujRodzajKalendarza(value) {
  if (!value) return "-";
  return etykietyRodzajowKalendarzy[value] || bezpiecznyTekst(value);
}

function formatujCyklicznoscZadania(value) {
  if (!value) return "-";
  return etykietyCyklicznosciZadan[value] || bezpiecznyTekst(value);
}

function formatujZakresEdycjiSeriiZadania(value) {
  if (!value) return "-";
  return etykietyZakresowEdycjiSeriiZadan[value] || bezpiecznyTekst(value);
}

function formatujWidokFokusuZadania(value) {
  if (!value) return "-";
  return etykietyWidokowFokusuZadan[value] || bezpiecznyTekst(value);
}

function pobierzNazweKalendarzaUzytkownika(calendarId) {
  const znaleziony = stan.kalendarzeUzytkownika.find((item) => Number(item.user_calendar_id) === Number(calendarId));
  return znaleziony ? znaleziony.display_name : "";
}

function pobierzKalendarzUzytkownika(calendarId) {
  return stan.kalendarzeUzytkownika.find((item) => Number(item.user_calendar_id) === Number(calendarId)) || null;
}

function pobierzDomyslnyCzasKalendarza(calendarId) {
  const kalendarz = pobierzKalendarzUzytkownika(calendarId);
  return kalendarz ? Number(kalendarz.default_duration_minutes || 60) : 60;
}

function formatujKierunekTransakcji(value) {
  if (value === "uznanie") return "Uznanie";
  if (value === "obciazenie") return "Obciazenie";
  return formatujWartosc(value);
}

function formatujStatusDopasowaniaTransakcji(value) {
  const etykiety = {
    nieprzypisana: "Nieprzypisana",
    czesciowo_rozliczona: "Czesciowo rozliczona",
    rozliczona: "Rozliczona",
  };
  return etykiety[value] || formatujWartosc(value);
}

function formatujIban(value) {
  const digits = String(value || "").replace(/\s+/g, "");
  if (!digits) return "-";
  return bezpiecznyTekst(digits.replace(/(.{4})/g, "$1 ").trim());
}

function pobierzStanPrzypomnienia(task) {
  if (!task?.remind_at) {
    return { etykieta: "Brak", klasa: "status-normal" };
  }
  const mapa = {
    brak: { etykieta: "Brak", klasa: "status-normal" },
    zaplanowane: { etykieta: "Zaplanowane", klasa: "status-normal" },
    oczekuje_wysylki: { etykieta: "Oczekuje wysylki", klasa: "status-warning" },
    wyslane: { etykieta: "Wyslane", klasa: "status-success" },
    blad: { etykieta: "Blad wysylki", klasa: "status-danger" },
    zamkniete: { etykieta: "Zamkniete", klasa: "status-success" },
  };
  const stanDostawy = String(task?.reminder_delivery_state || task?.reminder_state || "").trim();
  if (stanDostawy && mapa[stanDostawy]) {
    return mapa[stanDostawy];
  }
  const przypomnienie = new Date(task.remind_at);
  if (Number.isNaN(przypomnienie.getTime())) {
    return mapa.zaplanowane;
  }
  return przypomnienie <= new Date() ? mapa.oczekuje_wysylki : mapa.zaplanowane;
}

function pobierzStanSynchronizacjiGoogle(task) {
  if (!task?.calendar_name) {
    return {
      etykieta: "Brak kalendarza",
      klasa: "status-normal",
      opis: "Wpis nie jest jeszcze podpiety do zadnego kalendarza.",
      szczegoly: [],
    };
  }

  if (task?.calendar_provider !== "google_api") {
    return {
      etykieta: "Adres URL (.ics)",
      klasa: "status-normal",
      opis: "Ten wpis korzysta z adresu URL kalendarza i nie zapisuje sie bezposrednio w Google Calendar.",
      szczegoly: [],
    };
  }

  const stanSynchronizacji = String(task?.external_calendar_sync_state || "").trim();
  const komunikatSynchronizacji = String(task?.external_calendar_sync_message || "").trim();
  const bladSprawdzenia = String(task?.external_calendar_last_check_error || "").trim();
  if (stanSynchronizacji) {
    const mapaStanow = {
      oczekuje_synchronizacji: {
        etykieta: "Oczekuje synchronizacji",
        klasa: "status-warning",
        opis: komunikatSynchronizacji || "Wpis czeka na pierwszy poprawny zapis do Google Calendar.",
      },
      zsynchronizowano: {
        etykieta: "Zsynchronizowano",
        klasa: "status-success",
        opis: komunikatSynchronizacji || "Wpis jest zgodny z Google Calendar.",
      },
      wymaga_uwagi: {
        etykieta: "Wymaga uwagi",
        klasa: "status-warning",
        opis: komunikatSynchronizacji || "Wykryto roznice miedzy aplikacja a Google Calendar.",
      },
      brak_w_google: {
        etykieta: "Brak w Google",
        klasa: "status-danger",
        opis: komunikatSynchronizacji || "Nie znaleziono wydarzenia w Google Calendar.",
      },
      blad_sprawdzenia: {
        etykieta: "Blad sprawdzenia",
        klasa: "status-danger",
        opis: komunikatSynchronizacji || "Nie udalo sie sprawdzic stanu wpisu w Google Calendar.",
      },
      blad_zapisu: {
        etykieta: "Blad synchronizacji",
        klasa: "status-danger",
        opis: komunikatSynchronizacji || "Nie udalo sie zapisac wpisu do Google Calendar.",
      },
    };
    const wpis = mapaStanow[stanSynchronizacji] || mapaStanow.oczekuje_synchronizacji;
    const szczegoly = [];
    if (task?.external_calendar_last_checked_at) {
      szczegoly.push(`Ostatnie sprawdzenie: ${formatujDateCzas(task.external_calendar_last_checked_at)}`);
    }
    if (task?.external_calendar_synced_at) {
      szczegoly.push(`Ostatni zapis: ${formatujDateCzas(task.external_calendar_synced_at)}`);
    }
    if (task?.external_calendar_remote_updated_at) {
      szczegoly.push(`Ostatnia znana zmiana w Google: ${formatujDateCzas(task.external_calendar_remote_updated_at)}`);
    }
    if (String(task?.external_calendar_last_sync_source || "").trim() === "google" && stanSynchronizacji !== "zsynchronizowano") {
      szczegoly.push("Stan ustalono na podstawie danych odczytanych z Google Calendar.");
    }
    if (bladSprawdzenia) {
      szczegoly.push(`Szczegoly bledu: ${bladSprawdzenia}`);
    }
    return {
      etykieta: wpis.etykieta,
      klasa: wpis.klasa,
      opis: wpis.opis,
      szczegoly,
    };
  }

  const bladSynchronizacji = String(task?.external_calendar_sync_error || "").trim();
  if (bladSynchronizacji) {
    const szczegoly = [];
    if (task?.external_calendar_synced_at) {
      szczegoly.push(`Ostatni udany zapis: ${formatujDateCzas(task.external_calendar_synced_at)}`);
    }
    return {
      etykieta: "Blad synchronizacji",
      klasa: "status-danger",
      opis: bladSynchronizacji,
      szczegoly,
    };
  }

  if (String(task?.external_calendar_last_sync_source || "").trim() === "google") {
    const szczegoly = [];
    if (task?.external_calendar_remote_updated_at) {
      szczegoly.push(`Ostatnia znana zmiana w Google: ${formatujDateCzas(task.external_calendar_remote_updated_at)}`);
    }
    return {
      etykieta: "Zmiana po stronie Google",
      klasa: "status-warning",
      opis: "Wpis ma nowsza zmiane wykryta po stronie Google Calendar.",
      szczegoly,
    };
  }

  if (String(task?.external_calendar_event_id || "").trim() && task?.external_calendar_synced_at) {
    const szczegoly = [`Ostatni zapis: ${formatujDateCzas(task.external_calendar_synced_at)}`];
    if (task?.external_calendar_remote_updated_at) {
      szczegoly.push(`Ostatnia znana zmiana w Google: ${formatujDateCzas(task.external_calendar_remote_updated_at)}`);
    }
    if (String(task?.external_calendar_last_sync_source || "").trim() === "app") {
      szczegoly.push("Ostatni zapis wyszedl z aplikacji.");
    }
    return {
      etykieta: "Zsynchronizowano",
      klasa: "status-success",
      opis: "Wpis zostal zapisany w Google Calendar.",
      szczegoly,
    };
  }

  return {
    etykieta: "Oczekuje synchronizacji",
    klasa: "status-warning",
    opis: "Wpis czeka na pierwszy poprawny zapis do Google Calendar.",
    szczegoly: [],
  };
}

function renderujStanSynchronizacjiGoogle(task, options = {}) {
  const { szczegoly = false } = options;
  const info = pobierzStanSynchronizacjiGoogle(task);
  if (!szczegoly) {
    return zbudujBadgeStanu(info.etykieta, info.klasa);
  }
  const elementy = [zbudujBadgeStanu(info.etykieta, info.klasa)];
  if (info.opis) {
    elementy.push(`<div class="muted">${bezpiecznyTekst(info.opis)}</div>`);
  }
  (info.szczegoly || []).forEach((wiersz) => {
    elementy.push(`<div class="muted">${bezpiecznyTekst(wiersz)}</div>`);
  });
  return elementy.join("");
}

function formatujDateCzasDoInput(value) {
  if (!value) return "";
  const data = new Date(value);
  if (Number.isNaN(data.getTime())) {
    return String(value).slice(0, 16);
  }
  const przesunieta = new Date(data.getTime() - data.getTimezoneOffset() * 60000);
  return przesunieta.toISOString().slice(0, 16);
}

function etykietaPolaKsef(fieldName) {
  return etykietyPolKsef[String(fieldName || "").trim()] || formatujWartosc(fieldName);
}

function formatujWartoscPolaKsef(fieldName, value, currencyHint = "PLN") {
  const normalizedField = String(fieldName || "").trim();
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  if (normalizedField === "gross_amount") {
    return formatujKwote(value, currencyHint || "PLN");
  }
  if (normalizedField === "issue_date" || normalizedField === "sale_date") {
    const asDate = new Date(value);
    if (!Number.isNaN(asDate.getTime())) {
      return bezpiecznyTekst(asDate.toLocaleDateString("pl-PL"));
    }
  }
  return bezpiecznyTekst(value);
}

function pobierzNazweUzytkownika(userId) {
  if (userId === null || userId === undefined || userId === "") {
    return "";
  }
  const normalizedUserId = Number(userId);
  const allUsers = Array.isArray(stan.uzytkownicy) ? stan.uzytkownicy : [];
  const matchingUser = allUsers.find((user) => Number(user.user_id) === normalizedUserId);
  if (!matchingUser) {
    return String(userId);
  }
  return matchingUser.display_name || matchingUser.login || String(userId);
}

function pobierzUzytkownikowDlaDelegataKsef(organizationId) {
  const normalizedOrganizationId = Number(organizationId || 0);
  if (!normalizedOrganizationId) {
    return [];
  }
  return (Array.isArray(stan.uzytkownicy) ? stan.uzytkownicy : [])
    .filter(
      (user) =>
        Number(user.organization_id || 0) === normalizedOrganizationId &&
        Number(user.is_active || 0) === 1 &&
        String(user.role || "").trim().toLowerCase() !== "guest"
    )
    .sort((left, right) => {
      const leftName = `${left.display_name || ""} ${left.login || ""}`.trim().toLowerCase();
      const rightName = `${right.display_name || ""} ${right.login || ""}`.trim().toLowerCase();
      return leftName.localeCompare(rightName, "pl");
    });
}

function odswiezPoleDelegataKsef(organizationId, selectedUserId = "", selectedExpiresAt = "") {
  const select = document.getElementById("organization-ksef-delegate-user-id");
  const expiresAtInput = document.getElementById("organization-ksef-delegate-expires-at");
  if (!select || !expiresAtInput) {
    return;
  }
  const previousValue = String(selectedUserId ?? select.value ?? "").trim();
  const users = pobierzUzytkownikowDlaDelegataKsef(organizationId);
  const options = ['<option value="">Brak delegata</option>'].concat(
    users.map((user) => {
      const roleLabel = formatujRole(user.role);
      const label = `${user.display_name || user.login || user.user_id} | ${roleLabel}`;
      return `<option value="${user.user_id}">${bezpiecznyTekst(label)}</option>`;
    })
  );
  select.innerHTML = options.join("");
  select.value = users.some((user) => Number(user.user_id) === Number(previousValue)) ? String(previousValue) : "";
  expiresAtInput.value = formatujDateCzasDoInput(selectedExpiresAt);
}

function renderujZmianePolaKsef(change, authoritativeValues = {}, invoice = null) {
  const fieldName = String(change?.field_name || "").trim();
  const currencyHint =
    change?.field_name === "gross_amount"
      ? String(
          change?.currency ||
            authoritativeValues?.currency ||
            invoice?.currency ||
            invoice?.source_trace?.authoritative_values?.currency ||
            "PLN"
        )
      : "PLN";
  const sourceValue =
    change?.source_value !== undefined ? change.source_value : authoritativeValues?.[fieldName];
  return `
    <div class="ksef-correction-card">
      <div class="ksef-correction-card-header">
        <strong>${bezpiecznyTekst(change?.field_label || etykietaPolaKsef(fieldName))}</strong>
      </div>
      <div class="ksef-correction-values">
        <div class="ksef-correction-value is-authoritative">
          <span>Oryginal z KSeF</span>
          <strong>${formatujWartoscPolaKsef(fieldName, sourceValue, currencyHint)}</strong>
        </div>
        <div class="ksef-correction-value is-local">
          <span>Wartosc lokalna</span>
          <strong>${formatujWartoscPolaKsef(fieldName, change?.local_value, currencyHint)}</strong>
        </div>
      </div>
    </div>
  `;
}

function renderujSekcjeKorektKsef(detail) {
  const invoice = detail?.invoice || {};
  const correctionData = detail?.ksef_corrections || {};
  const authoritativeValues = correctionData.authoritative_values || {};
  const approved = Array.isArray(correctionData.approved) ? correctionData.approved : [];
  const pending = Array.isArray(correctionData.pending) ? correctionData.pending : [];
  const rejected = Array.isArray(correctionData.rejected) ? correctionData.rejected : [];
  const activeLocalValues = correctionData.active_local_values || {};
  const hasAnyCorrections = approved.length || pending.length || rejected.length || Object.keys(activeLocalValues).length;

  if (!detail?.ksef_protected && !hasAnyCorrections) {
    return "";
  }

  return `
    <div class="panel">
      <div class="panel-header">
        <h3>Korekty danych KSeF</h3>
      </div>
      <div class="subtle-note">
        Oryginalne wartosci z KSeF zostaja zachowane na stale. Zatwierdzone korekty lokalne dzialaja obok nich i sa widoczne w historii decyzji.
      </div>
      ${
        Object.keys(activeLocalValues).length
          ? `
            <div class="panel-header" style="margin-top: 16px;"><h3>Aktywne korekty lokalne</h3></div>
            <div class="ksef-correction-grid">
              ${Object.entries(activeLocalValues)
                .map(([fieldName, value]) =>
                  renderujZmianePolaKsef(
                    {
                      field_name: fieldName,
                      field_label: etykietaPolaKsef(fieldName),
                      source_value: authoritativeValues[fieldName],
                      local_value: value,
                    },
                    authoritativeValues,
                    invoice
                  )
                )
                .join("")}
            </div>
          `
          : `<div class="empty-state" style="margin-top: 16px;">Brak aktywnych lokalnych korekt dla danych z KSeF.</div>`
      }
      ${
        pending.length
          ? `
            <div class="panel-header" style="margin-top: 16px;"><h3>Oczekujace prosby</h3></div>
            <div class="ksef-correction-grid">
              ${pending.map((change) => renderujZmianePolaKsef(change, authoritativeValues, invoice)).join("")}
            </div>
          `
          : ""
      }
      ${
        rejected.length
          ? `
            <div class="panel-header" style="margin-top: 16px;"><h3>Odrzucone propozycje</h3></div>
            <div class="ksef-correction-grid">
              ${rejected.map((change) => renderujZmianePolaKsef(change, authoritativeValues, invoice)).join("")}
            </div>
          `
          : ""
      }
    </div>
  `;
}

function otworzModalZapisuKsef(result) {
  const shell = document.getElementById("invoice-ksef-save-modal");
  const title = document.getElementById("invoice-ksef-save-modal-title");
  const subtitle = document.getElementById("invoice-ksef-save-modal-subtitle");
  const message = document.getElementById("invoice-ksef-save-modal-message");
  const fields = document.getElementById("invoice-ksef-save-modal-fields");
  if (!shell || !title || !subtitle || !message || !fields) {
    return;
  }
  if (!result) {
    zamknijModalZapisuKsef();
    return;
  }
  const mode = String(result.mode || "").trim().toLowerCase();
  const titleText =
    result.title ||
    (mode === "request_created" ? "Zapisano zmiany i utworzono prosbe o korekte" : "Zapisano lokalna korekte danych KSeF");
  const subtitleText =
    mode === "request_created"
      ? "Chronione pola z KSeF nie zostaly nadpisane. Po zapisie utworzono prosbe do zatwierdzenia."
      : "Osoba z uprawnieniem do korekt KSeF zatwierdzila zmiane od razu po zapisie.";
  title.textContent = titleText;
  subtitle.textContent = subtitleText;
  message.textContent = result.message || "";
  const fieldChanges = Array.isArray(result.field_changes) ? result.field_changes : [];
  fields.innerHTML = fieldChanges.length
    ? fieldChanges.map((change) => renderujZmianePolaKsef(change, {}, stan.wybranaFakturaId ? { currency: document.querySelector('#invoice-edit-form [name=\"currency\"]')?.value || 'PLN' } : null)).join("")
    : '<div class="empty-state">Brak szczegolow zmian do wyswietlenia.</div>';
  shell.classList.remove("hidden");
  shell.setAttribute("aria-hidden", "false");
}

function zamknijModalZapisuKsef() {
  const shell = document.getElementById("invoice-ksef-save-modal");
  if (!shell) {
    return;
  }
  shell.classList.add("hidden");
  shell.setAttribute("aria-hidden", "true");
}

function parsujDateKalendarza(value) {
  if (!value) return null;
  const data = new Date(value);
  if (Number.isNaN(data.getTime())) {
    return null;
  }
  return data;
}

function sklonujDateNaPolnoc(data) {
  const clone = new Date(data);
  clone.setHours(0, 0, 0, 0);
  return clone;
}

function dodajDniDoDaty(data, days) {
  const clone = new Date(data);
  clone.setDate(clone.getDate() + days);
  return clone;
}

function poczatekTygodnia(data) {
  const clone = sklonujDateNaPolnoc(data);
  const day = clone.getDay();
  const offset = (day + 6) % 7;
  clone.setDate(clone.getDate() - offset);
  return clone;
}

function koniecTygodnia(data) {
  const start = poczatekTygodnia(data);
  return dodajDniDoDaty(start, 6);
}

function poczatekMiesiaca(data) {
  const clone = sklonujDateNaPolnoc(data);
  clone.setDate(1);
  return clone;
}

function koniecMiesiaca(data) {
  const clone = poczatekMiesiaca(data);
  clone.setMonth(clone.getMonth() + 1);
  clone.setDate(0);
  return clone;
}

function formatujDzienKalendarza(data) {
  return data.toLocaleDateString("pl-PL", {
    weekday: "short",
    day: "2-digit",
    month: "2-digit",
  });
}

function formatujNaglowekMiesiaca(data) {
  return data.toLocaleDateString("pl-PL", {
    month: "long",
    year: "numeric",
  });
}

function formatujWiekCzasu(value) {
  const data = parsujDateKalendarza(value);
  if (!data) {
    return "-";
  }
  const diffMs = Date.now() - data.getTime();
  if (diffMs < 60 * 1000) {
    return "przed chwila";
  }
  const diffMinutes = Math.round(diffMs / 60000);
  if (diffMinutes < 60) {
    return `${diffMinutes} min temu`;
  }
  const diffHours = Math.round(diffMinutes / 60);
  if (diffHours < 24) {
    return `${diffHours} godz. temu`;
  }
  const diffDays = Math.round(diffHours / 24);
  return `${diffDays} dni temu`;
}

function pobierzFiltrOutboxaPrzypomnien() {
  return String(stan.taskReminderOutboxFilter || "all").trim().toLowerCase() || "all";
}

function ustawFiltrOutboxaPrzypomnien(filter) {
  const normalized = String(filter || "all").trim().toLowerCase() || "all";
  stan.taskReminderOutboxFilter = normalized;
  renderujStatusPrzypomnien();
  wczytajStatusPrzypomnien().catch(() => {});
}

function czyWpisOutboxaZawieszony(item, processingTimeoutMinutes) {
  if (String(item?.status || "") !== "processing") {
    return false;
  }
  const claimedAt = new Date(String(item?.claimed_at || ""));
  if (Number.isNaN(claimedAt.getTime())) {
    return false;
  }
  return Date.now() - claimedAt.getTime() > Math.max(1, Number(processingTimeoutMinutes) || 10) * 60000;
}

function pobierzNajswiezszyHeartbeat(workers) {
  return [...(Array.isArray(workers) ? workers : [])]
    .map((worker) => ({
      ...worker,
      heartbeat_at: new Date(String(worker?.last_heartbeat_at || "")),
    }))
    .filter((worker) => !Number.isNaN(worker.heartbeat_at.getTime()))
    .sort((left, right) => right.heartbeat_at.getTime() - left.heartbeat_at.getTime())[0] || null;
}

function renderujPanelOutboxaPrzypomnien() {
  const workersNode = document.getElementById("task-reminder-workers");
  const workerCountNode = document.getElementById("task-reminder-worker-count");
  const summaryNode = document.getElementById("task-reminder-health-summary");
  const filterButtons = Array.from(document.querySelectorAll("[data-task-reminder-outbox-filter]"));
  const outboxBody = document.getElementById("task-reminder-outbox-body");
  if (!workersNode && !outboxBody && !summaryNode) {
    return;
  }

  const status = stan.taskReminderStatus || stan.meta?.task_reminder_status || {};
  const workers = Array.isArray(status.workers) ? status.workers : [];
  const deliveries = Array.isArray(stan.taskReminderOutbox) ? stan.taskReminderOutbox : [];
  const queue = status.queue || {};
  const filter = pobierzFiltrOutboxaPrzypomnien();
  const timeoutMinutes = Number(status.processing_timeout_minutes || 10);
  const visibleDeliveries = filter === "all" ? deliveries : deliveries.filter((item) => String(item?.status || "") === filter);
  const staleProcessingCount = deliveries.filter((item) => czyWpisOutboxaZawieszony(item, timeoutMinutes)).length;
  const latestHeartbeat = pobierzNajswiezszyHeartbeat(workers);
  const latestHeartbeatLabel = latestHeartbeat
    ? `${latestHeartbeat.worker_name || "worker"} â€˘ ${formatujDateCzas(latestHeartbeat.last_heartbeat_at)} (${formatujWiekCzasu(
        latestHeartbeat.last_heartbeat_at
      )})`
    : "Brak heartbeatow";

  if (workerCountNode) {
    workerCountNode.textContent = `${workers.length} workerow`;
  }

  if (summaryNode) {
    const healthTone = Number(queue.failed || 0) > 0 || staleProcessingCount > 0 ? "status-warning" : "status-success";
    const healthLabel =
      Number(queue.failed || 0) > 0
        ? "Wymaga uwagi"
        : staleProcessingCount > 0
          ? "Procesowanie zawieszone"
          : workers.length > 0
            ? "OK"
            : "Brak workerow";
    summaryNode.innerHTML = `
      <article class="task-reminder-health-chip">
        <strong>${bezpiecznyTekst(Number(queue.total || 0))}</strong>
        <span>Wszystkie wpisy w outboxie</span>
      </article>
      <article class="task-reminder-health-chip">
        <strong>${bezpiecznyTekst(Number(queue.due || 0))}</strong>
        <span>Do wysĹ‚ania teraz</span>
      </article>
      <article class="task-reminder-health-chip">
        <strong>${bezpiecznyTekst(Number(queue.processing || 0))}</strong>
        <span>W przetwarzaniu</span>
      </article>
      <article class="task-reminder-health-chip">
        <strong>${bezpiecznyTekst(Number(queue.failed || 0))}</strong>
        <span>BĹ‚Ä™dy</span>
      </article>
      <article class="task-reminder-health-chip">
        <strong>${bezpiecznyTekst(staleProcessingCount)}</strong>
        <span>Zawieszone przetwarzanie</span>
      </article>
      <article class="task-reminder-health-chip">
        <strong><span class="status-badge ${healthTone}">${bezpiecznyTekst(healthLabel)}</span></strong>
        <span>NajĹ›wieĹĽszy heartbeat: ${bezpiecznyTekst(latestHeartbeatLabel)}</span>
      </article>
    `;
  }

  filterButtons.forEach((button) => {
    const buttonFilter = String(button.dataset.taskReminderOutboxFilter || "all").trim().toLowerCase() || "all";
    const isActive = buttonFilter === filter;
    button.classList.toggle("active", isActive);
    button.setAttribute("aria-pressed", isActive ? "true" : "false");
  });

  if (workersNode) {
    if (!workers.length) {
      workersNode.className = "empty-state";
      workersNode.innerHTML = "Brak zapisanych heartbeatow workerow. Status pojawi sie po pierwszym cyklu pracy.";
    } else {
      workersNode.className = "worker-health-grid";
      workersNode.innerHTML = workers
        .map((worker) => {
          const state = String(worker.state || "idle").trim();
          const stateLabel = state === "error" ? "Blad" : state === "ok" ? "Aktywny" : "Bezczynny";
          const stateClass = state === "error" ? "status-danger" : state === "ok" ? "status-normal" : "status-muted";
          const details = [
            `Ostatni sygnal: ${formatujDateCzas(worker.last_heartbeat_at)} (${formatujWiekCzasu(worker.last_heartbeat_at)})`,
            worker.last_success_at ? `Ostatni sukces: ${formatujDateCzas(worker.last_success_at)}` : null,
            worker.last_error_message ? `Blad: ${worker.last_error_message}` : null,
            `Cykle: ${formatujWartosc(worker.cycles_completed || 0)}`,
            `W tym: ${formatujWartosc(worker.processed_total || 0)} przetworzonych, ${formatujWartosc(worker.sent_total || 0)} wyslanych, ${formatujWartosc(worker.failed_total || 0)} bledow`,
          ].filter(Boolean);
          return `
            <article class="worker-health-card">
              <div class="worker-health-header">
                <strong>${bezpiecznyTekst(worker.worker_name || "worker")}</strong>
                <span class="status-badge ${stateClass}">${bezpiecznyTekst(stateLabel)}</span>
              </div>
              <div class="muted">${bezpiecznyTekst(worker.worker_role || "worker")}</div>
              <div class="worker-health-meta">
                ${details.map((item) => `<span>${bezpiecznyTekst(item)}</span>`).join("")}
              </div>
            </article>
          `;
        })
        .join("");
    }
  }

  if (outboxBody) {
    if (!visibleDeliveries.length) {
      outboxBody.innerHTML = `<tr><td colspan="6">Brak wpisow w outboxie dla wybranego statusu.</td></tr>`;
    } else {
      outboxBody.innerHTML = visibleDeliveries
        .map((item) => {
          const normalizedStatus = String(item.status || "").trim();
          const statusClass =
            normalizedStatus === "failed"
              ? "status-danger"
              : normalizedStatus === "processing"
                ? "status-warning"
                : normalizedStatus === "cancelled"
                  ? "status-muted"
                  : normalizedStatus === "sent"
                    ? "status-success"
                    : "status-normal";
          const isStale = czyWpisOutboxaZawieszony(item, timeoutMinutes);
          const retryButton = ["failed", "cancelled"].includes(String(item.status))
            ? `<button type="button" class="secondary small-action" data-requeue-outbox-id="${item.task_reminder_outbox_id}">Ponow</button>`
            : `<span class="muted">-</span>`;
          const error = String(item.last_error || "").trim();
          return `
            <tr>
              <td data-label="Status"><span class="status-badge ${statusClass}">${bezpiecznyTekst(item.status || "-")}</span></td>
              <td data-label="Wpis">
                <strong>${bezpiecznyTekst(item.task_title || `Zadanie #${item.task_id}`)}</strong>
                <div class="muted">${bezpiecznyTekst(item.task_type || "-")} | ${bezpiecznyTekst(item.owner_user_name || "-")}</div>
                ${isStale ? '<div class="muted">Zawieszone przetwarzanie wymaga uwagi.</div>' : ""}
              </td>
              <td data-label="Odbiorca">${bezpiecznyTekst(item.recipient_user_name || "-")}</td>
              <td data-label="Dostepne od">
                <div>${bezpiecznyTekst(formatujDateCzas(item.available_at))}</div>
                <div class="muted">Prob: ${bezpiecznyTekst(item.attempt_count || 0)}</div>
              </td>
              <td data-label="Blad">${error ? `<div class="muted">${bezpiecznyTekst(error)}</div>` : "-"}</td>
              <td data-label="Akcja">${retryButton}</td>
            </tr>
          `;
        })
        .join("");

      outboxBody.querySelectorAll("[data-requeue-outbox-id]").forEach((button) => {
        button.addEventListener("click", async (event) => {
          event.preventDefault();
          event.stopPropagation();
          try {
            await ponowWpisOutboxaPrzypomnien(Number(button.dataset.requeueOutboxId));
          } catch (error) {
            pokazPowiadomienie(error.message);
          }
        });
      });
    }
  }
}

function renderujZalacznikiAkceptacji(attachments = [], approvalRequestId = 0, canWrite = false) {
  const normalized = Array.isArray(attachments) ? attachments : [];
  const listHtml = normalized.length
    ? normalized
        .map(
          (attachment) => `
            <article class="list-item">
              <strong>${bezpiecznyTekst(attachment.file_name || "Zalacznik")}</strong>
              <div class="muted">${bezpiecznyTekst(attachment.mime_type || "-")} | ${formatujWartosc(
                attachment.file_size ? `${attachment.file_size} B` : "-"
              )}</div>
              <div><a href="${bezpiecznyTekst(attachment.file_link)}" target="_blank" rel="noreferrer">Otworz zalacznik</a></div>
            </article>
          `
        )
        .join("")
    : `<div class="empty-state">Brak zalacznikow dla tego wniosku.</div>`;

  const uploadHtml = canWrite
    ? `
      <form class="stack approval-attachment-form" data-approval-attachment-form="${approvalRequestId}">
        <div class="inline-file-row">
          <input type="file" data-approval-attachment-file />
          <button type="submit" class="secondary">Dodaj plik</button>
        </div>
        <div class="inline-file-row">
          <input type="text" data-approval-attachment-link-title placeholder="Nazwa linku" />
          <input type="url" data-approval-attachment-link-url placeholder="https://..." />
          <button type="button" class="secondary" data-approval-attachment-link-submit>Dodaj link</button>
        </div>
      </form>
    `
    : "";

  return `
    <div class="approval-attachments-shell">
      <div class="detail-actions" style="margin-top: 12px;">
        <button type="button" class="secondary small-action" data-approval-attachments-toggle="${approvalRequestId}">Zalaczniki</button>
      </div>
      <div class="approval-attachments hidden" data-approval-attachments-panel="${approvalRequestId}">
        <div class="list" data-approval-attachments-list="${approvalRequestId}">${listHtml}</div>
        ${uploadHtml}
      </div>
    </div>
  `;
}

async function wczytajZalacznikiAkceptacji(approvalRequestId) {
  const panel = document.querySelector(`[data-approval-attachments-panel="${approvalRequestId}"]`);
  const list = document.querySelector(`[data-approval-attachments-list="${approvalRequestId}"]`);
  if (!panel || !list) {
    return;
  }
  try {
    panel.classList.remove("hidden");
    list.innerHTML = `<div class="empty-state">Ladowanie zalacznikow...</div>`;
    const detail = await api(zbudujAdresZOrganizacja(`/api/approvals/${approvalRequestId}`));
    const attachments = Array.isArray(detail.attachments) ? detail.attachments : [];
    list.innerHTML = renderujZalacznikiAkceptacji(attachments, approvalRequestId, czyMoznaZapisywac());
  } catch (error) {
    list.innerHTML = `<div class="empty-state">${bezpiecznyTekst(error.message)}</div>`;
  }
}

async function dodajZalacznikAkceptacji(approvalRequestId, payload) {
  if (!czyMoznaZapisywac()) {
    throw new Error("To konto nie ma prawa dodawania zalacznikow do akceptacji.");
  }
  const normalized = Number(approvalRequestId || 0);
  if (!normalized) {
    throw new Error("Nieprawidlowy wniosek akceptacyjny.");
  }
  await api(zbudujAdresZOrganizacja(`/api/approvals/${normalized}/attachments`), {
    method: "POST",
    body: JSON.stringify(payload),
  });
  pokazPowiadomienie("Dodano zalacznik do akceptacji.");
  await wczytajZalacznikiAkceptacji(normalized);
  await wczytajLogi();
}

function odswiezWartoscFormularzaSkrzynki(form = null) {
  const currentForm = form || document.getElementById("inbox-form-editor");
  if (!currentForm) return;
  const selected = stan.inboxSelectedFormId
    ? stan.inboxForms.find((item) => Number(item.intake_form_id) === Number(stan.inboxSelectedFormId))
    : null;
  document.getElementById("inbox-form-id").value = selected?.intake_form_id || "";
  document.getElementById("inbox-form-name").value = selected?.form_name || "";
  document.getElementById("inbox-form-slug").value = selected?.form_slug || "";
  document.getElementById("inbox-form-priority").value = selected?.default_priority || "normalny";
  document.getElementById("inbox-form-assigned-user").value = selected?.default_assigned_user_id || "";
  document.getElementById("inbox-form-description").value = selected?.description || "";
  document.getElementById("inbox-form-schema").value = JSON.stringify(selected?.field_schema_json || [], null, 2);
  document.getElementById("inbox-form-public").checked = Boolean(selected ? selected.is_public : true);
  document.getElementById("inbox-form-attachments").checked = Boolean(selected ? selected.allow_attachments : true);
  const archiveButton = document.getElementById("inbox-form-archive");
  if (archiveButton) {
    archiveButton.disabled = !selected;
  }
}

function wyczyscFormularzSkrzynki() {
  stan.inboxSelectedFormId = null;
  document.getElementById("inbox-form-editor")?.reset();
  odswiezWartoscFormularzaSkrzynki();
}

function ustawFormularzSkrzynki(formId) {
  const normalized = Number(formId || 0);
  const selected = stan.inboxForms.find((item) => Number(item.intake_form_id) === normalized);
  if (!selected) {
    pokazPowiadomienie("Nie znaleziono formularza.");
    return;
  }
  stan.inboxSelectedFormId = normalized;
  odswiezWartoscFormularzaSkrzynki();
  document.getElementById("inbox-form-name")?.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function zapiszFormularzSkrzynki() {
  if (!czyMoznaZapisywac()) {
    throw new Error("To konto nie ma prawa zapisu formularzy.");
  }
  const formId = Number(document.getElementById("inbox-form-id")?.value || 0);
  const payload = {
    form_name: document.getElementById("inbox-form-name").value.trim(),
    form_slug: document.getElementById("inbox-form-slug").value.trim(),
    description: document.getElementById("inbox-form-description").value.trim(),
    field_schema_json: document.getElementById("inbox-form-schema").value.trim(),
    is_public: document.getElementById("inbox-form-public").checked,
    allow_attachments: document.getElementById("inbox-form-attachments").checked,
    default_priority: document.getElementById("inbox-form-priority").value,
    default_assigned_user_id: document.getElementById("inbox-form-assigned-user").value || null,
  };
  const method = formId ? "PATCH" : "POST";
  const url = formId ? zbudujAdresZOrganizacja(`/api/intake/forms/${formId}`) : zbudujAdresZOrganizacja("/api/intake/forms");
  await api(url, { method, body: JSON.stringify(payload) });
  pokazPowiadomienie(formId ? "Zaktualizowano formularz." : "Dodano formularz.");
  await wczytajSkrzynkeWplywow();
}

async function usunFormularzSkrzynki() {
  if (!czyMoznaZapisywac()) {
    throw new Error("To konto nie ma prawa archiwizacji formularzy.");
  }
  const formId = Number(document.getElementById("inbox-form-id")?.value || stan.inboxSelectedFormId || 0);
  if (!formId) {
    pokazPowiadomienie("Wybierz formularz do archiwizacji.");
    return;
  }
  await api(zbudujAdresZOrganizacja(`/api/intake/forms/${formId}`), { method: "DELETE" });
  pokazPowiadomienie("Zarchiwizowano formularz.");
  wyczyscFormularzSkrzynki();
  await wczytajSkrzynkeWplywow();
}

async function zapiszSpraweSkrzynki() {
  if (!czyMoznaZapisywac()) {
    throw new Error("To konto nie ma prawa dodawania spraw.");
  }
  const payload = {
    intake_form_id: document.getElementById("inbox-item-form-id").value || null,
    title: document.getElementById("inbox-item-title").value.trim(),
    status: document.getElementById("inbox-item-status").value,
    priority: document.getElementById("inbox-item-priority").value,
    assigned_user_id: document.getElementById("inbox-item-assigned-user").value || null,
    due_at: document.getElementById("inbox-item-due-at").value || null,
    description: document.getElementById("inbox-item-description").value.trim(),
    metadata_json: document.getElementById("inbox-item-metadata").value.trim(),
  };
  await api(zbudujAdresZOrganizacja("/api/intake/items"), { method: "POST", body: JSON.stringify(payload) });
  pokazPowiadomienie("Dodano sprawÄ™.");
  await wczytajSkrzynkeWplywow();
}

async function aktualizujSpraweSkrzynki() {
  if (!czyMoznaZapisywac()) {
    throw new Error("To konto nie ma prawa edycji spraw.");
  }
  const itemId = Number(document.getElementById("inbox-item-id")?.value || stan.inboxSelectedItemId || 0);
  if (!itemId) {
    return;
  }
  const payload = {
    title: document.getElementById("inbox-item-edit-title").value.trim(),
    status: document.getElementById("inbox-item-edit-status").value,
    priority: document.getElementById("inbox-item-edit-priority").value,
    assigned_user_id: document.getElementById("inbox-item-edit-assigned-user").value || null,
    due_at: document.getElementById("inbox-item-edit-due-at").value || null,
    source_kind: document.getElementById("inbox-item-edit-source").value.trim(),
    description: document.getElementById("inbox-item-edit-description").value.trim(),
    metadata_json: document.getElementById("inbox-item-edit-metadata").value.trim(),
  };
  await api(zbudujAdresZOrganizacja(`/api/intake/items/${itemId}`), { method: "PATCH", body: JSON.stringify(payload) });
  pokazPowiadomienie("Zaktualizowano sprawÄ™.");
  await wczytajSzczegolySkrzynki(itemId);
  await wczytajSkrzynkeWplywow();
}

async function dodajKomentarzDoSkrzynki() {
  if (!czyMoznaZapisywac()) {
    throw new Error("To konto nie ma prawa dodawania komentarzy.");
  }
  const itemId = Number(stan.inboxSelectedItemId || 0);
  if (!itemId) return;
  const noteText = document.getElementById("inbox-comment-text").value.trim();
  if (!noteText) {
    pokazPowiadomienie("Wpisz treĹ›Ä‡ komentarza.");
    return;
  }
  await api(zbudujAdresZOrganizacja(`/api/intake/items/${itemId}/comments`), {
    method: "POST",
    body: JSON.stringify({ note_text: noteText }),
  });
  document.getElementById("inbox-comment-text").value = "";
  pokazPowiadomienie("Dodano komentarz.");
  await wczytajSzczegolySkrzynki(itemId);
}

async function dodajZalacznikDoSkrzynki(kind = "file") {
  if (!czyMoznaZapisywac()) {
    throw new Error("To konto nie ma prawa dodawania zalacznikow.");
  }
  const itemId = Number(stan.inboxSelectedItemId || 0);
  if (!itemId) return;
  const payload = kind === "link"
    ? {
        attachment_kind: "link",
        file_name: document.getElementById("inbox-attachment-link-title").value.trim(),
        attachment_url: document.getElementById("inbox-attachment-link-url").value.trim(),
      }
    : (() => {
        const file = document.getElementById("inbox-attachment-file").files?.[0];
        if (!file) {
          throw new Error("Wybierz plik do dodania.");
        }
        return { attachment_kind: "file", file_name: file.name, file, content_type: file.type };
      })();

  if (kind === "file") {
    payload.content_base64 = await odczytajPlikJakoBase64(payload.file);
    delete payload.file;
  }
  await api(zbudujAdresZOrganizacja(`/api/intake/items/${itemId}/attachments`), {
    method: "POST",
    body: JSON.stringify(payload),
  });
  pokazPowiadomienie("Dodano zalacznik.");
  await wczytajSzczegolySkrzynki(itemId);
}

async function wczytajPomoc() {
  if (!stan.biezacyUzytkownik) {
    stan.supportRequests = [];
    stan.supportSelectedRequestId = null;
    stan.supportSelectedRequestDetail = null;
    renderujPomoc();
    return;
  }
  const requests = await api(zbudujAdresZOrganizacja("/api/support/requests"));
  stan.supportRequests = Array.isArray(requests) ? requests : [];
  const activeExists = stan.supportRequests.some(
    (item) => Number(item.intake_item_id) === Number(stan.supportSelectedRequestId)
  );
  if (activeExists && stan.supportSelectedRequestId) {
    await wczytajSzczegolyPomocy(stan.supportSelectedRequestId, true);
    return;
  }
  if (stan.supportRequests.length) {
    await wczytajSzczegolyPomocy(stan.supportRequests[0].intake_item_id, true);
    return;
  }
  stan.supportSelectedRequestId = null;
  stan.supportSelectedRequestDetail = null;
  renderujPomoc();
}

async function wczytajSzczegolyPomocy(requestId, cichy = false) {
  const normalized = Number(requestId || 0);
  if (!normalized) {
    stan.supportSelectedRequestId = null;
    stan.supportSelectedRequestDetail = null;
    renderujPomoc();
    return null;
  }
  stan.supportSelectedRequestId = normalized;
  const detail = await api(zbudujAdresZOrganizacja(`/api/support/requests/${normalized}`));
  stan.supportSelectedRequestDetail = detail;
  renderujPomoc();
  if (!cichy) {
    document.getElementById("support-thread-panel")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }
  return detail;
}

async function utworzZgloszenieSupportowe() {
  const payload = {
    title: document.getElementById("support-request-title").value.trim(),
    support_category: document.getElementById("support-request-category").value,
    priority: document.getElementById("support-request-priority").value,
    description: document.getElementById("support-request-description").value.trim(),
  };
  const created = await api(zbudujAdresZOrganizacja("/api/support/requests"), {
    method: "POST",
    body: JSON.stringify(payload),
  });
  document.getElementById("support-request-form")?.reset();
  document.getElementById("support-request-priority").value = "normalny";
  pokazPowiadomienie("Wyslano zgloszenie do supportu.");
  await wczytajPomoc();
  if (created?.intake_item_id) {
    await wczytajSzczegolyPomocy(created.intake_item_id, true);
  }
}

async function dodajKomentarzDoPomocy() {
  const requestId = Number(stan.supportSelectedRequestId || 0);
  if (!requestId) {
    return;
  }
  const noteText = document.getElementById("support-comment-text").value.trim();
  if (!noteText) {
    pokazPowiadomienie("Wpisz tresc odpowiedzi.");
    return;
  }
  await api(zbudujAdresZOrganizacja(`/api/support/requests/${requestId}/comments`), {
    method: "POST",
    body: JSON.stringify({ note_text: noteText }),
  });
  document.getElementById("support-comment-text").value = "";
  pokazPowiadomienie("Dodano odpowiedz do zgloszenia.");
  await wczytajSzczegolyPomocy(requestId, true);
}

async function dodajZalacznikDoPomocy(kind = "file") {
  const requestId = Number(stan.supportSelectedRequestId || 0);
  if (!requestId) {
    return;
  }
  const payload = kind === "link"
    ? {
        attachment_kind: "link",
        file_name: document.getElementById("support-attachment-link-title").value.trim(),
        attachment_url: document.getElementById("support-attachment-link-url").value.trim(),
      }
    : (() => {
        const file = document.getElementById("support-attachment-file").files?.[0];
        if (!file) {
          throw new Error("Wybierz plik do dodania.");
        }
        return { attachment_kind: "file", file_name: file.name, file, content_type: file.type };
      })();

  if (kind === "file") {
    payload.content_base64 = await odczytajPlikJakoBase64(payload.file);
    delete payload.file;
  }

  await api(zbudujAdresZOrganizacja(`/api/support/requests/${requestId}/attachments`), {
    method: "POST",
    body: JSON.stringify(payload),
  });

  if (kind === "file") {
    const fileInput = document.getElementById("support-attachment-file");
    if (fileInput) {
      fileInput.value = "";
    }
  } else {
    document.getElementById("support-attachment-link-title").value = "";
    document.getElementById("support-attachment-link-url").value = "";
  }
  pokazPowiadomienie("Dodano zalacznik do zgloszenia.");
  await wczytajSzczegolyPomocy(requestId, true);
}

async function wczytajSkrzynkeWplywow() {
  if (!stan.biezacyUzytkownik) {
    stan.inboxForms = [];
    stan.inboxItems = [];
    stan.inboxSelectedItemDetail = null;
    renderujSkrzynkeWplywow();
    return;
  }
  const params = pobierzFiltrySkrzynkiWejsciowej();
  const formsUrl = zbudujAdresZOrganizacja("/api/intake/forms?include_inactive=1");
  const itemsUrl = zbudujAdresZOrganizacja(`/api/intake/items${params.toString() ? `?${params.toString()}` : ""}`);
  const [forms, items] = await Promise.all([api(formsUrl), api(itemsUrl)]);
  stan.inboxForms = Array.isArray(forms) ? forms : [];
  stan.inboxItems = Array.isArray(items) ? items : [];
  if (stan.inboxSelectedItemId) {
    await wczytajSzczegolySkrzynki(stan.inboxSelectedItemId, true);
  }
  renderujSkrzynkeWplywow();
}

async function wczytajSzczegolySkrzynki(itemId, cichy = false) {
  const normalized = Number(itemId || 0);
  if (!normalized) {
    stan.inboxSelectedItemDetail = null;
    stan.inboxSelectedItemId = null;
    renderujSkrzynkeWplywow();
    return null;
  }
  stan.inboxSelectedItemId = normalized;
  const detail = await api(zbudujAdresZOrganizacja(`/api/intake/items/${normalized}`));
  stan.inboxSelectedItemDetail = detail;
  renderujSkrzynkeWplywow();
  if (!cichy) {
    document.getElementById("inbox-item-edit-title")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }
  return detail;
}

function renderujPomoc() {
  const root = document.getElementById("support-root");
  if (!root) return;
  if (!stan.biezacyUzytkownik) {
    root.innerHTML = `<div class="empty-state">Zaloguj sie, aby otworzyc centrum pomocy i swoje zgloszenia.</div>`;
    return;
  }
  if (czyGlobalnyAdministrator() && !stan.wybranaOrganizacjaId) {
    root.innerHTML = `<div class="empty-state">Wybierz konkretna organizacje, aby otworzyc modul Pomoc.</div>`;
    return;
  }

  const requests = Array.isArray(stan.supportRequests) ? stan.supportRequests : [];
  const detail = stan.supportSelectedRequestDetail || null;
  const selectedRequest =
    detail?.item || requests.find((item) => Number(item.intake_item_id) === Number(stan.supportSelectedRequestId)) || null;
  const counts = {
    total: requests.length,
    active: requests.filter((item) => !["zakonczone", "zarchiwizowane"].includes(String(item.status || ""))).length,
    waiting: requests.filter((item) => String(item.status || "") === "oczekuje").length,
    done: requests.filter((item) => String(item.status || "") === "zakonczone").length,
  };

  const categoriesHtml = supportCategories
    .map(
      (category) => `
        <button type="button" class="support-category-tile" data-support-category="${category.key}">
          <strong>${bezpiecznyTekst(category.label)}</strong>
          <span>${bezpiecznyTekst(category.description)}</span>
        </button>
      `
    )
    .join("");

  const requestsHtml = requests.length
    ? requests
        .map((item) => {
          const category = formatujKategorieSupportu(pobierzKategorieSupportuZMetadanych(item));
          const active = Number(item.intake_item_id) === Number(stan.supportSelectedRequestId);
          return `
            <article class="support-request-card ${active ? "is-active" : ""}" data-support-request-open="${item.intake_item_id}">
              <div class="support-request-top">
                <strong>${bezpiecznyTekst(item.title || "Zgloszenie")}</strong>
                ${zbudujBadgeStanu(formatujStatusSprawy(item.status), klasaStatusuSprawy(item.status))}
              </div>
              <div class="muted">${bezpiecznyTekst(category)} â€˘ ${bezpiecznyTekst(formatujPriorytetSprawy(item.priority))}</div>
              <p>${bezpiecznyTekst(item.description || "Brak dodatkowego opisu.")}</p>
              <div class="muted">Ostatnia aktywnosc: ${formatujDateCzas(item.last_activity_at || item.updated_at)}</div>
            </article>
          `;
        })
        .join("")
    : `<div class="empty-state">Nie masz jeszcze zadnych zgĹ‚oszen. Mozesz od razu wyslac pierwsze z tego widoku.</div>`;

  const commentsHtml =
    Array.isArray(detail?.comments) && detail.comments.length
      ? detail.comments
          .map(
            (comment) => `
              <article class="support-thread-entry">
                <div class="support-thread-entry-top">
                  <strong>${bezpiecznyTekst(comment.created_by_user_name || "-")}</strong>
                  <span class="muted">${formatujDateCzas(comment.created_at)}</span>
                </div>
                <div>${bezpiecznyTekst(comment.note_text || "")}</div>
              </article>
            `
          )
          .join("")
      : `<div class="empty-state">Nie ma jeszcze odpowiedzi w tym zgĹ‚oszeniu.</div>`;

  const attachmentsHtml =
    Array.isArray(detail?.attachments) && detail.attachments.length
      ? detail.attachments
          .map(
            (attachment) => `
              <article class="support-attachment-item">
                <strong>${bezpiecznyTekst(attachment.file_name || "Zalacznik")}</strong>
                <div class="muted">${bezpiecznyTekst(attachment.mime_type || "-")}</div>
                <a href="${bezpiecznyTekst(attachment.file_link)}" target="_blank" rel="noreferrer">Otworz</a>
              </article>
            `
          )
          .join("")
      : `<div class="empty-state">Brak zalacznikow do tego zgĹ‚oszenia.</div>`;

  const historyHtml =
    Array.isArray(detail?.history) && detail.history.length
      ? detail.history
          .slice(0, 8)
          .map(
            (entry) => `
              <article class="support-history-item">
                <strong>${bezpiecznyTekst(entry.message || "-")}</strong>
                <div class="muted">${bezpiecznyTekst(entry.actor || "-")} â€˘ ${formatujDateCzas(entry.created_at)}</div>
              </article>
            `
          )
          .join("")
      : `<div class="empty-state">Historia pojawi sie po pierwszych zmianach i odpowiedziach.</div>`;

  root.innerHTML = `
    <div class="support-center">
      <section id="support-overview-shell" class="panel support-overview-panel">
        <div class="support-hero-grid">
          <div class="support-hero-copy">
            <span class="view-kicker">Centrum pomocy</span>
            <h3>Kontakt z supportem bez wychodzenia z aplikacji</h3>
            <p class="subtle-note">
              To jest docelowe, wbudowane miejsce na pytania, bledy, prosby wdrozeniowe i dalszy kontakt z naszym zespollem.
            </p>
          </div>
          <div class="support-summary-grid">
            <div class="summary-item"><strong>Twoje zgĹ‚oszenia</strong><div>${counts.total}</div></div>
            <div class="summary-item"><strong>Aktywne</strong><div>${counts.active}</div></div>
            <div class="summary-item"><strong>Czekaja</strong><div>${counts.waiting}</div></div>
            <div class="summary-item"><strong>Zakonczone</strong><div>${counts.done}</div></div>
          </div>
        </div>
      </section>

      <div class="support-layout-grid">
        <section id="support-compose-shell" class="panel support-compose-panel">
          <div class="panel-header">
            <h3>Nowe zgĹ‚oszenie</h3>
            <span class="pill">Pomoc</span>
          </div>
          <div class="support-category-grid">${categoriesHtml}</div>
          <form id="support-request-form" class="field-grid" style="margin-top: 16px;">
            <div class="field field-full">
              <label>Tytul</label>
              <input id="support-request-title" type="text" placeholder="np. Nie moge zmienic organizacji po zalogowaniu" />
            </div>
            <div class="field">
              <label>Kategoria</label>
              <select id="support-request-category">
                ${supportCategories
                  .map((category) => `<option value="${category.key}">${bezpiecznyTekst(category.label)}</option>`)
                  .join("")}
              </select>
            </div>
            <div class="field">
              <label>Priorytet</label>
              <select id="support-request-priority">
                <option value="normalny">Normalny</option>
                <option value="niski">Niski</option>
                <option value="wysoki">Wysoki</option>
                <option value="pilny">Pilny</option>
              </select>
            </div>
            <div class="field field-full">
              <label>Opis</label>
              <textarea id="support-request-description" rows="7" placeholder="Opisz, co dokladnie sie dzieje, czego oczekiwales i co pojawilo sie zamiast tego."></textarea>
            </div>
            <div class="filters-actions field-full">
              <button type="submit">Wyslij zgloszenie</button>
            </div>
          </form>
        </section>

        <section id="support-requests-shell" class="panel support-requests-panel">
          <div class="panel-header">
            <h3>Moje zgĹ‚oszenia</h3>
            <span class="pill">${counts.total}</span>
          </div>
          <div class="support-request-list">${requestsHtml}</div>
        </section>

        <section class="panel support-thread-panel" id="support-thread-panel">
          <div class="panel-header">
            <h3>${bezpiecznyTekst(selectedRequest?.title || "Szczegoly zgĹ‚oszenia")}</h3>
            ${
              selectedRequest
                ? zbudujBadgeStanu(formatujStatusSprawy(selectedRequest.status), klasaStatusuSprawy(selectedRequest.status))
                : '<span class="pill">Brak wyboru</span>'
            }
          </div>
          ${
            selectedRequest
              ? `
                <div class="support-thread-meta">
                  <div class="summary-item">
                    <strong>Kategoria</strong>
                    <div>${bezpiecznyTekst(formatujKategorieSupportu(pobierzKategorieSupportuZMetadanych(selectedRequest)))}</div>
                  </div>
                  <div class="summary-item">
                    <strong>Priorytet</strong>
                    <div>${bezpiecznyTekst(formatujPriorytetSprawy(selectedRequest.priority))}</div>
                  </div>
                  <div class="summary-item">
                    <strong>Utworzono</strong>
                    <div>${formatujDateCzas(selectedRequest.created_at)}</div>
                  </div>
                  <div class="summary-item">
                    <strong>Ostatnia aktywnosc</strong>
                    <div>${formatujDateCzas(selectedRequest.last_activity_at || selectedRequest.updated_at)}</div>
                  </div>
                </div>
                <div class="support-thread-description">${bezpiecznyTekst(selectedRequest.description || "Brak opisu.")}</div>
                <div class="support-thread-columns">
                  <div class="support-thread-section">
                    <div class="panel-header"><h3>Rozmowa</h3></div>
                    <div class="support-thread-list">${commentsHtml}</div>
                    <form id="support-comment-form" class="stack" style="margin-top: 16px;">
                      <textarea id="support-comment-text" rows="4" placeholder="Dopisz szczegoly albo odpowiedz supportowi."></textarea>
                      <button type="submit">Dodaj odpowiedz</button>
                    </form>
                  </div>
                  <div class="support-thread-section">
                    <div class="panel-header"><h3>Zalaczniki</h3></div>
                    <div class="support-attachment-list">${attachmentsHtml}</div>
                    <div class="stack" style="margin-top: 16px;">
                      <div class="inline-file-row">
                        <input id="support-attachment-file" type="file" />
                        <button type="button" class="secondary" id="support-attachment-file-submit">Dodaj plik</button>
                      </div>
                      <div class="inline-file-row">
                        <input id="support-attachment-link-title" type="text" placeholder="Nazwa linku" />
                        <input id="support-attachment-link-url" type="url" placeholder="https://..." />
                        <button type="button" class="secondary" id="support-attachment-link-submit">Dodaj link</button>
                      </div>
                    </div>
                    <div class="panel-header" style="margin-top: 18px;"><h3>Historia</h3></div>
                    <div class="support-history-list">${historyHtml}</div>
                  </div>
                </div>
              `
              : `<div class="empty-state">Wybierz zgĹ‚oszenie z listy po lewej, aby zobaczyc cala rozmowe, zalaczniki i historie.</div>`
          }
        </section>
      </div>
    </div>
  `;

  root.querySelectorAll("[data-support-category]").forEach((button) => {
    button.addEventListener("click", () => {
      const select = document.getElementById("support-request-category");
      if (select) {
        select.value = button.dataset.supportCategory || supportCategories[0].key;
      }
    });
  });
  root.querySelectorAll("[data-support-request-open]").forEach((button) => {
    button.addEventListener("click", async () => {
      await wczytajSzczegolyPomocy(Number(button.dataset.supportRequestOpen || 0));
    });
  });
  document.getElementById("support-request-form")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await utworzZgloszenieSupportowe();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  document.getElementById("support-comment-form")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await dodajKomentarzDoPomocy();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  document.getElementById("support-attachment-file-submit")?.addEventListener("click", async () => {
    try {
      await dodajZalacznikDoPomocy("file");
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  document.getElementById("support-attachment-link-submit")?.addEventListener("click", async () => {
    try {
      await dodajZalacznikDoPomocy("link");
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
}

function renderujZapisaneWidoki() {
  const root = document.getElementById("views-root");
  if (!root) return;
  if (!stan.biezacyUzytkownik) {
    root.innerHTML = `<div class="empty-state">Zaloguj sie, aby zarzadzac zapisanymi widokami.</div>`;
    return;
  }
  const canWrite = czyMoznaZapisywac();

  const views = Array.isArray(stan.savedViews) ? stan.savedViews : [];
  const selected = stan.savedViewSelectedId
    ? views.find((item) => Number(item.saved_view_id) === Number(stan.savedViewSelectedId))
    : null;
  const viewCards = views.length
    ? views
        .map(
          (view) => `
            <article class="list-item clickable ${Number(view.saved_view_id) === Number(stan.savedViewSelectedId) ? "is-selected" : ""}" data-view-edit-id="${view.saved_view_id}">
              <div style="display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; align-items:flex-start;">
                <div>
                  <strong>${bezpiecznyTekst(view.view_name)}</strong>
                  <div class="muted">${bezpiecznyTekst(view.module_key)} | ${bezpiecznyTekst(view.view_slug)}</div>
                </div>
                <span class="status-badge ${view.is_default ? "status-success" : view.is_shared ? "status-normal" : "status-muted"}">${view.is_default ? "domyslny" : view.is_shared ? "wspoldzielony" : "prywatny"}</span>
              </div>
              <div>${bezpiecznyTekst(view.description || "Brak opisu.")}</div>
              <div class="muted">Dodane przez: ${bezpiecznyTekst(view.created_by_user_name || "-")}</div>
            </article>
          `
        )
        .join("")
    : `<div class="empty-state">Brak zapisanych widokow.</div>`;

  root.innerHTML = `
    <div class="content-grid contractors-grid">
      <div id="views-list-shell" class="panel">
        <div class="panel-header">
          <h3>Lista zapisanych widokow</h3>
          <span class="pill">${views.length}</span>
        </div>
        <div class="list">${viewCards}</div>
      </div>
      <div id="views-editor-shell" class="panel detail-panel">
        <div class="panel-header">
          <h3>${selected ? "Edytuj widok" : "Nowy widok"}</h3>
        </div>
        <form id="saved-view-form" class="field-grid">
          <input type="hidden" id="saved-view-id" value="${selected?.saved_view_id || ""}" />
          <div class="field">
            <label>Modul</label>
            <select id="saved-view-module-key">
              <option value="dashboard">Pulpit</option>
              <option value="tasks">Zadania</option>
              <option value="billing">Rozliczenia</option>
              <option value="inbox">Inbox</option>
              <option value="health">Zdrowie</option>
              <option value="invoices">Faktury</option>
            </select>
          </div>
          <div class="field">
            <label>Nazwa widoku</label>
            <input id="saved-view-name" type="text" />
          </div>
          <div class="field">
            <label>Slug</label>
            <input id="saved-view-slug" type="text" />
          </div>
          <div class="field field-full">
            <label>Opis</label>
            <textarea id="saved-view-description" rows="3"></textarea>
          </div>
          <div class="field field-full">
            <label>Stan widoku (JSON)</label>
            <textarea id="saved-view-state-json" rows="6" placeholder='{"filters":{}}'></textarea>
          </div>
          <div class="field"><label class="checkbox-inline"><input id="saved-view-shared" type="checkbox" checked /> Wspoldzielony</label></div>
          <div class="field"><label class="checkbox-inline"><input id="saved-view-default" type="checkbox" /> Domyslny</label></div>
          <div class="filters-actions field-full">
            <button type="submit" ${canWrite ? "" : "disabled"}>Zapisz widok</button>
            <button type="button" class="secondary" id="saved-view-reset">Nowy widok</button>
            <button type="button" class="secondary" id="saved-view-delete" ${selected && canWrite ? "" : "disabled"}>Usun</button>
            <button type="button" class="secondary" id="saved-view-open" ${selected ? "" : "disabled"}>Otworz</button>
          </div>
        </form>
        <div class="panel-header" style="margin-top: 18px;">
          <h3>Aktualny stan</h3>
        </div>
        <div class="empty-state">${selected ? bezpiecznyTekst(JSON.stringify(selected.view_state_json || {}, null, 2)) : "Wybierz widok, aby zobaczyc stan JSON."}</div>
      </div>
    </div>
  `;
  ustawStanPola(
    [
      "saved-view-module-key",
      "saved-view-name",
      "saved-view-slug",
      "saved-view-description",
      "saved-view-state-json",
      "saved-view-shared",
      "saved-view-default",
    ],
    !canWrite
  );

  document.getElementById("saved-view-form")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await zapiszWidok();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  document.getElementById("saved-view-reset")?.addEventListener("click", () => {
    stan.savedViewSelectedId = null;
    wyczyscFormularzWidoku();
    renderujZapisaneWidoki();
  });
  document.getElementById("saved-view-delete")?.addEventListener("click", async () => {
    try {
      await usunWidok();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  document.getElementById("saved-view-open")?.addEventListener("click", async () => {
    try {
      await otworzWidok();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  document.querySelectorAll("[data-view-edit-id]").forEach((button) => {
    button.addEventListener("click", () => ustawWidokZapisanegoWidoku(Number(button.dataset.viewEditId)));
  });
  odswiezFormularzWidoku();
}

function odswiezFormularzWidoku() {
  const selected = stan.savedViewSelectedId
    ? stan.savedViews.find((item) => Number(item.saved_view_id) === Number(stan.savedViewSelectedId))
    : null;
  document.getElementById("saved-view-id").value = selected?.saved_view_id || "";
  document.getElementById("saved-view-module-key").value = selected?.module_key || "dashboard";
  document.getElementById("saved-view-name").value = selected?.view_name || "";
  document.getElementById("saved-view-slug").value = selected?.view_slug || "";
  document.getElementById("saved-view-description").value = selected?.description || "";
  document.getElementById("saved-view-state-json").value = JSON.stringify(selected?.view_state_json || {}, null, 2);
  document.getElementById("saved-view-shared").checked = Boolean(selected ? selected.is_shared : true);
  document.getElementById("saved-view-default").checked = Boolean(selected?.is_default);
}

function wyczyscFormularzWidoku() {
  stan.savedViewSelectedId = null;
  document.getElementById("saved-view-form")?.reset();
  odswiezFormularzWidoku();
}

function ustawWidokZapisanegoWidoku(viewId) {
  const selected = stan.savedViews.find((item) => Number(item.saved_view_id) === Number(viewId));
  if (!selected) {
    pokazPowiadomienie("Nie znaleziono widoku.");
    return;
  }
  stan.savedViewSelectedId = Number(viewId);
  odswiezFormularzWidoku();
}

async function zapiszWidok() {
  if (!czyMoznaZapisywac()) {
    throw new Error("To konto nie ma prawa zapisu widokow.");
  }
  const viewId = Number(document.getElementById("saved-view-id").value || 0);
  const payload = {
    module_key: document.getElementById("saved-view-module-key").value,
    view_name: document.getElementById("saved-view-name").value.trim(),
    view_slug: document.getElementById("saved-view-slug").value.trim(),
    description: document.getElementById("saved-view-description").value.trim(),
    view_state_json: document.getElementById("saved-view-state-json").value.trim(),
    is_shared: document.getElementById("saved-view-shared").checked,
    is_default: document.getElementById("saved-view-default").checked,
  };
  const url = viewId ? zbudujAdresZOrganizacja(`/api/dashboard/views/${viewId}`) : zbudujAdresZOrganizacja("/api/dashboard/views");
  await api(url, { method: viewId ? "PATCH" : "POST", body: JSON.stringify(payload) });
  pokazPowiadomienie(viewId ? "Zaktualizowano widok." : "Dodano widok.");
  await wczytajZapisaneWidoki();
}

async function usunWidok() {
  if (!czyMoznaZapisywac()) {
    throw new Error("To konto nie ma prawa usuwania widokow.");
  }
  const viewId = Number(document.getElementById("saved-view-id").value || stan.savedViewSelectedId || 0);
  if (!viewId) return;
  await api(zbudujAdresZOrganizacja(`/api/dashboard/views/${viewId}`), { method: "DELETE" });
  pokazPowiadomienie("Usunieto widok.");
  wyczyscFormularzWidoku();
  await wczytajZapisaneWidoki();
}

async function otworzWidok() {
  const viewId = Number(document.getElementById("saved-view-id").value || stan.savedViewSelectedId || 0);
  if (!viewId) return;
  const selected = stan.savedViews.find((item) => Number(item.saved_view_id) === viewId);
  if (!selected) return;
  if (String(selected.module_key || "").trim().toLowerCase() === "invoices") {
    ustawWidok("invoices");
    await zastosujStanWidokuFaktur(selected.view_state_json || {});
    pokazPowiadomienie("Widok otwarty.");
    return;
  }
  ustawWidok(selected.module_key || "dashboard");
  pokazPowiadomienie("Widok otwarty.");
}

async function wczytajZapisaneWidoki() {
  if (!stan.biezacyUzytkownik) {
    stan.savedViews = [];
    renderujZapisaneWidoki();
    return [];
  }
  const [views, tasks, billing, inbox, health, invoices] = await Promise.all([
    api(zbudujAdresZOrganizacja("/api/dashboard/views?module_key=dashboard&include_hidden=1")),
    api(zbudujAdresZOrganizacja("/api/dashboard/views?module_key=tasks&include_hidden=1")),
    api(zbudujAdresZOrganizacja("/api/dashboard/views?module_key=billing&include_hidden=1")),
    api(zbudujAdresZOrganizacja("/api/dashboard/views?module_key=inbox&include_hidden=1")),
    api(zbudujAdresZOrganizacja("/api/dashboard/views?module_key=health&include_hidden=1")),
    api(zbudujAdresZOrganizacja("/api/dashboard/views?module_key=invoices&include_hidden=1")),
  ]);
  stan.savedViews = [...views, ...tasks, ...billing, ...inbox, ...health, ...invoices];
  renderujZapisaneWidoki();
  return stan.savedViews;
}

function renderujAutomatyzacje() {
  const root = document.getElementById("automation-root");
  if (!root) return;
  if (!stan.biezacyUzytkownik) {
    root.innerHTML = `<div class="empty-state">Zaloguj sie, aby zarzadzac automatyzacjami.</div>`;
    return;
  }
  const canWrite = czyMoznaZapisywac();

  const rules = Array.isArray(stan.automationRules) ? stan.automationRules : [];
  const executions = Array.isArray(stan.automationExecutions) ? stan.automationExecutions : [];
  const selected = stan.automationSelectedId
    ? rules.find((item) => Number(item.automation_rule_id) === Number(stan.automationSelectedId))
    : null;
  const actionsText = selected ? JSON.stringify(selected.actions_json || [], null, 2) : "[]";
  const conditionsText = selected ? JSON.stringify(selected.conditions_json || {}, null, 2) : "{}";

  root.innerHTML = `
    <div class="content-grid contractors-grid">
      <div id="automation-rules-shell" class="panel">
        <div class="panel-header">
          <h3>Reguly automatyzacji</h3>
          <span class="pill">${rules.length}</span>
        </div>
        <div class="list">
          ${
            rules.length
              ? rules
                  .map(
                    (rule) => `
                      <article class="list-item clickable ${Number(rule.automation_rule_id) === Number(stan.automationSelectedId) ? "is-selected" : ""}" data-automation-edit-id="${rule.automation_rule_id}">
                        <div style="display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; align-items:flex-start;">
                          <div>
                            <strong>${bezpiecznyTekst(rule.rule_name)}</strong>
                            <div class="muted">${bezpiecznyTekst(rule.trigger_event_type)} | ${bezpiecznyTekst(rule.rule_slug)}</div>
                          </div>
                          <span class="status-badge ${rule.is_active ? "status-success" : "status-muted"}">${rule.is_active ? "aktywna" : "wylaczona"}</span>
                        </div>
                        <div>${bezpiecznyTekst(rule.description || "Brak opisu.")}</div>
                        <div class="muted">Wykonania: ${bezpiecznyTekst(rule.execution_count || 0)} | ${bezpiecznyTekst(rule.last_result || "-")}</div>
                      </article>
                    `
                  )
                  .join("")
              : `<div class="empty-state">Brak reguĹ‚ automatyzacji.</div>`
          }
        </div>
      </div>
      <div id="automation-editor-shell" class="panel detail-panel">
        <div class="panel-header">
          <h3>${selected ? "Edytuj reguĹ‚Ä™" : "Nowa reguĹ‚a"}</h3>
        </div>
        <form id="automation-rule-form" class="field-grid">
          <input type="hidden" id="automation-rule-id" value="${selected?.automation_rule_id || ""}" />
          <div class="field"><label>Nazwa</label><input id="automation-rule-name" type="text" /></div>
          <div class="field"><label>Slug</label><input id="automation-rule-slug" type="text" /></div>
          <div class="field"><label>Zdarzenie</label><input id="automation-rule-trigger" type="text" placeholder="np. invoice_created" /></div>
          <div class="field"><label>Opis</label><input id="automation-rule-description" type="text" /></div>
          <div class="field field-full"><label>Warunki JSON</label><textarea id="automation-rule-conditions" rows="5">${conditionsText}</textarea></div>
          <div class="field field-full"><label>Akcje JSON</label><textarea id="automation-rule-actions" rows="6">${actionsText}</textarea></div>
          <div class="field"><label class="checkbox-inline"><input id="automation-rule-active" type="checkbox" checked /> Aktywna</label></div>
          <div class="filters-actions field-full">
            <button type="submit" ${canWrite ? "" : "disabled"}>Zapisz regule</button>
            <button type="button" class="secondary" id="automation-rule-reset">Nowa reguĹ‚a</button>
            <button type="button" class="secondary" id="automation-rule-run" ${selected && canWrite ? "" : "disabled"}>Uruchom teraz</button>
            <button type="button" class="secondary" id="automation-rule-delete" ${selected && canWrite ? "" : "disabled"}>Wylacz</button>
          </div>
        </form>
      </div>
    </div>

    <div id="automation-executions-shell" class="panel" style="margin-top: 18px;">
      <div class="panel-header">
        <h3>Wykonania reguĹ‚</h3>
        <span class="pill">${executions.length}</span>
      </div>
      <div class="table-wrap">
        <table class="mobile-card-table">
          <thead>
            <tr>
              <th>Status</th>
              <th>Regula</th>
              <th>Zdarzenie</th>
              <th>Data</th>
              <th>Blad</th>
            </tr>
          </thead>
          <tbody>
            ${
              executions.length
                ? executions
              .map(
                (execution) => `
                        <tr>
                          <td data-label="Status"><span class="status-badge ${execution.execution_status === "failed" ? "status-danger" : "status-success"}">${bezpiecznyTekst(execution.execution_status)}</span></td>
                          <td data-label="Regula">${bezpiecznyTekst(execution.rule_name || "-")}</td>
                          <td data-label="Zdarzenie">${bezpiecznyTekst(execution.trigger_event_type || "-")}</td>
                          <td data-label="Data">${formatujDateCzas(execution.created_at)}</td>
                          <td data-label="Blad">${bezpiecznyTekst(execution.error_message || "-")}</td>
                        </tr>
                      `
                    )
                    .join("")
                : `<tr><td colspan="5">Brak wykonan.</td></tr>`
            }
          </tbody>
        </table>
      </div>
    </div>
  `;
  ustawStanPola(
    [
      "automation-rule-name",
      "automation-rule-slug",
      "automation-rule-trigger",
      "automation-rule-description",
      "automation-rule-conditions",
      "automation-rule-actions",
      "automation-rule-active",
    ],
    !canWrite
  );

  document.getElementById("automation-rule-form")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await zapiszReguleAutomatyzacji();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  document.getElementById("automation-rule-reset")?.addEventListener("click", () => {
    stan.automationSelectedId = null;
    wyczyscFormularzAutomatyzacji();
    renderujAutomatyzacje();
  });
  document.getElementById("automation-rule-run")?.addEventListener("click", async () => {
    try {
      await uruchomReguleAutomatyzacji();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  document.getElementById("automation-rule-delete")?.addEventListener("click", async () => {
    try {
      await usunReguleAutomatyzacji();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  document.querySelectorAll("[data-automation-edit-id]").forEach((button) => {
    button.addEventListener("click", () => ustawReguleAutomatyzacji(Number(button.dataset.automationEditId)));
  });
  odswiezFormularzAutomatyzacji();
}

function odswiezFormularzAutomatyzacji() {
  const selected = stan.automationSelectedId
    ? stan.automationRules.find((item) => Number(item.automation_rule_id) === Number(stan.automationSelectedId))
    : null;
  document.getElementById("automation-rule-id").value = selected?.automation_rule_id || "";
  document.getElementById("automation-rule-name").value = selected?.rule_name || "";
  document.getElementById("automation-rule-slug").value = selected?.rule_slug || "";
  document.getElementById("automation-rule-trigger").value = selected?.trigger_event_type || "";
  document.getElementById("automation-rule-description").value = selected?.description || "";
  document.getElementById("automation-rule-conditions").value = JSON.stringify(selected?.conditions_json || {}, null, 2);
  document.getElementById("automation-rule-actions").value = JSON.stringify(selected?.actions_json || [], null, 2);
  document.getElementById("automation-rule-active").checked = Boolean(selected ? selected.is_active : true);
}

function wyczyscFormularzAutomatyzacji() {
  stan.automationSelectedId = null;
  document.getElementById("automation-rule-form")?.reset();
  odswiezFormularzAutomatyzacji();
}

function ustawReguleAutomatyzacji(ruleId) {
  const selected = stan.automationRules.find((item) => Number(item.automation_rule_id) === Number(ruleId));
  if (!selected) {
    pokazPowiadomienie("Nie znaleziono reguly.");
    return;
  }
  stan.automationSelectedId = Number(ruleId);
  odswiezFormularzAutomatyzacji();
}

async function zapiszReguleAutomatyzacji() {
  if (!czyMoznaZapisywac()) {
    throw new Error("To konto nie ma prawa zapisu automatyzacji.");
  }
  const ruleId = Number(document.getElementById("automation-rule-id").value || 0);
  const payload = {
    rule_name: document.getElementById("automation-rule-name").value.trim(),
    rule_slug: document.getElementById("automation-rule-slug").value.trim(),
    trigger_event_type: document.getElementById("automation-rule-trigger").value.trim(),
    description: document.getElementById("automation-rule-description").value.trim(),
    conditions_json: document.getElementById("automation-rule-conditions").value.trim(),
    actions_json: document.getElementById("automation-rule-actions").value.trim(),
    is_active: document.getElementById("automation-rule-active").checked,
  };
  const url = ruleId ? zbudujAdresZOrganizacja(`/api/automation/rules/${ruleId}`) : zbudujAdresZOrganizacja("/api/automation/rules");
  await api(url, { method: ruleId ? "PATCH" : "POST", body: JSON.stringify(payload) });
  pokazPowiadomienie(ruleId ? "Zaktualizowano regule." : "Dodano regule.");
  await wczytajAutomatyzacje();
}

async function uruchomReguleAutomatyzacji() {
  if (!czyMoznaZapisywac()) {
    throw new Error("To konto nie ma prawa uruchamiania automatyzacji.");
  }
  const ruleId = Number(document.getElementById("automation-rule-id").value || stan.automationSelectedId || 0);
  if (!ruleId) return;
  await api(zbudujAdresZOrganizacja(`/api/automation/rules/${ruleId}/run`), { method: "POST" });
  pokazPowiadomienie("Uruchomiono regule.");
  await wczytajAutomatyzacje();
}

async function usunReguleAutomatyzacji() {
  if (!czyMoznaZapisywac()) {
    throw new Error("To konto nie ma prawa wylaczania automatyzacji.");
  }
  const ruleId = Number(document.getElementById("automation-rule-id").value || stan.automationSelectedId || 0);
  if (!ruleId) return;
  await api(zbudujAdresZOrganizacja(`/api/automation/rules/${ruleId}`), { method: "DELETE" });
  pokazPowiadomienie("Wylaczono regule.");
  wyczyscFormularzAutomatyzacji();
  await wczytajAutomatyzacje();
}

async function wczytajAutomatyzacje() {
  if (!stan.biezacyUzytkownik) {
    stan.automationRules = [];
    stan.automationExecutions = [];
    renderujAutomatyzacje();
    return [];
  }
  const [rules, executions] = await Promise.all([
    api(zbudujAdresZOrganizacja("/api/automation/rules?include_inactive=1")),
    api(zbudujAdresZOrganizacja("/api/automation/executions?limit=100")),
  ]);
  stan.automationRules = Array.isArray(rules) ? rules : [];
  stan.automationExecutions = Array.isArray(executions) ? executions : [];
  renderujAutomatyzacje();
  return stan.automationRules;
}

function renderujZdrowieSystemu() {
  const root = document.getElementById("health-root");
  if (!root) return;
  if (!stan.biezacyUzytkownik) {
    root.innerHTML = `<div class="empty-state">Zaloguj sie, aby zobaczyc zdrowie systemu.</div>`;
    return;
  }
  const snapshot = stan.systemHealthSnapshot || {};
  const worker = snapshot.worker || {};
  const inbox = snapshot.inbox || {};
  const savedViews = snapshot.saved_views || {};
  const automations = snapshot.automations || {};
  const billing = snapshot.billing || {};
  const approvals = snapshot.approvals || {};
  const summary = snapshot.summary || {};
  root.innerHTML = `
    <div class="summary-grid">
      <div class="summary-item"><strong>Worker</strong><div>${summary.worker_online ? "online" : "offline"}</div></div>
      <div class="summary-item"><strong>Inbox</strong><div>${formatujWartosc(inbox.counts?.items || 0)} spraw</div></div>
      <div class="summary-item"><strong>Widoki</strong><div>${formatujWartosc(savedViews.count || 0)} pozycji</div></div>
      <div class="summary-item"><strong>Automatyzacje</strong><div>${formatujWartosc(automations.rules_count || 0)} reguĹ‚</div></div>
      <div class="summary-item"><strong>Saldo platnikow</strong><div>${formatujWartosc(billing.overdue_count || 0)} zaleglosci</div></div>
      <div class="summary-item"><strong>Akceptacje</strong><div>${formatujWartosc(approvals.pending_count || 0)} pending</div></div>
    </div>
    <div class="content-grid contractors-grid">
      <div id="health-worker-shell" class="panel">
        <div class="panel-header"><h3>Przypomnienia i worker</h3></div>
        <div class="list">
          <article class="list-item">
            <strong>${bezpiecznyTekst(worker.delivery_channel || "-")}</strong>
            <div class="muted">Retry: ${bezpiecznyTekst(worker.retry_minutes || "-")} min</div>
            <div class="muted">Max prob: ${bezpiecznyTekst(worker.max_attempts || "-")}</div>
            <div class="muted">Tryb: ${bezpiecznyTekst(worker.mode || "-")}</div>
          </article>
          ${(Array.isArray(worker.workers) ? worker.workers : [])
            .map(
              (worker) => `
                <article class="list-item">
                  <strong>${bezpiecznyTekst(worker.worker_name || "worker")}</strong>
                  <div class="muted">${bezpiecznyTekst(worker.state || "-")} | ${formatujDateCzas(worker.last_heartbeat_at)}</div>
                  <div class="muted">${bezpiecznyTekst(worker.last_error_message || "Brak bledu.")}</div>
                </article>
              `
            )
            .join("")}
        </div>
      </div>
      <div id="health-platform-shell" class="panel">
        <div class="panel-header"><h3>Inbox / Widoki / Automatyzacje</h3></div>
        <div class="list">
          <article class="list-item"><strong>Formularze</strong><div class="muted">${bezpiecznyTekst(inbox.counts?.forms || 0)}</div></article>
          <article class="list-item"><strong>Sprawy</strong><div class="muted">${bezpiecznyTekst(inbox.counts?.items || 0)}</div></article>
          <article class="list-item"><strong>Zapisane widoki</strong><div class="muted">${bezpiecznyTekst(savedViews.count || 0)}</div></article>
          <article class="list-item"><strong>Reguly</strong><div class="muted">${bezpiecznyTekst(automations.rules_count || 0)}</div></article>
          <article class="list-item"><strong>Wykonania</strong><div class="muted">${bezpiecznyTekst(automations.execution_count || 0)}</div></article>
        </div>
      </div>
      <div id="health-billing-shell" class="panel">
        <div class="panel-header"><h3>Rozliczenia</h3></div>
        <div class="list">
          <article class="list-item"><strong>Platnicy z zalegloscia</strong><div class="muted">${bezpiecznyTekst(billing.overdue_count || 0)}</div></article>
          <article class="list-item"><strong>Suma sald</strong><div class="muted">${formatujKwote(billing.total_balance_due || 0)}</div></article>
          <article class="list-item"><strong>Dopasowania</strong><div class="muted">${bezpiecznyTekst(billing.recent_matches?.length || 0)}</div></article>
          <article class="list-item"><strong>Oczekujace akceptacje</strong><div class="muted">${bezpiecznyTekst(approvals.pending_count || 0)}</div></article>
        </div>
      </div>
    </div>
  `;
}

async function wczytajZdrowieSystemu() {
  if (!stan.biezacyUzytkownik) {
    stan.systemHealthSnapshot = null;
    renderujZdrowieSystemu();
    return null;
  }
  stan.systemHealthSnapshot = await api(zbudujAdresZOrganizacja("/api/system/health"));
  renderujZdrowieSystemu();
  return stan.systemHealthSnapshot;
}

function renderujKsiegeRozliczen() {
  const balances = Array.isArray(stan.billingLedgerBalances) ? stan.billingLedgerBalances : [];
  const entries = Array.isArray(stan.billingLedgerEntries) ? stan.billingLedgerEntries : [];
  const matches = Array.isArray(stan.billingPaymentMatches) ? stan.billingPaymentMatches : [];
  const canWrite = czyMoznaZapisywac();
  const balanceBody = document.getElementById("billing-balance-table-body");
  const entryBody = document.getElementById("billing-ledger-entry-table-body");
  const matchBody = document.getElementById("billing-payment-match-table-body");
  const balanceCount = document.getElementById("billing-balance-count");
  const entryCount = document.getElementById("billing-ledger-entry-count");
  const matchCount = document.getElementById("billing-payment-match-count");
  const payerSelect = document.getElementById("billing-match-payer-id");
  const transactionSelect = document.getElementById("billing-match-transaction-id");
  const chargeSelect = document.getElementById("billing-match-charge-id");

  if (balanceCount) balanceCount.textContent = balances.length ? `${balances.length} platnikow` : "";
  if (entryCount) entryCount.textContent = entries.length ? `${entries.length} wpisow` : "";
  if (matchCount) matchCount.textContent = matches.length ? `${matches.length} dopasowan` : "";

  if (balanceBody) {
    balanceBody.innerHTML = balances.length
      ? balances
          .map(
            (row) => `
              <tr>
                <td data-label="Platnik">${formatujWartosc(row.display_name || row.payer_display_name)}</td>
                <td data-label="Telefon">${formatujWartosc(row.contact_phone)}</td>
                <td data-label="Naliczone">${formatujKwote(row.total_charges || 0)}</td>
                <td data-label="Rozliczone">${formatujKwote(row.total_matches || 0)}</td>
                <td data-label="Saldo"><span class="status-badge ${Number(row.balance_due || 0) > 0 ? "status-warning" : "status-success"}">${formatujKwote(row.balance_due || 0)}</span></td>
                <td data-label="Ostatnia wplata">${row.last_payment_at ? `${formatujDateCzas(row.last_payment_at)}<div class="muted">${formatujKwote(row.last_payment_amount || 0, row.last_payment_currency || "PLN")}</div>` : "Brak dopasowanej wplaty"}</td>
              </tr>
            `
          )
          .join("")
      : `<tr><td colspan="6">Brak danych sald.</td></tr>`;
  }

  if (entryBody) {
    entryBody.innerHTML = entries.length
      ? entries
          .map(
            (entry) => `
              <tr>
                <td data-label="Data">${formatujDateCzas(entry.created_at)}</td>
                <td data-label="Platnik">${formatujWartosc(entry.payer_display_name || "-")}</td>
                <td data-label="Rodzaj">${bezpiecznyTekst(entry.entry_kind || "-")}</td>
                <td data-label="Zmiana">${formatujKwote(entry.amount_delta || 0)}</td>
                <td data-label="Saldo po">${formatujKwote(entry.balance_after || 0)}</td>
                <td data-label="Notatka">${bezpiecznyTekst(entry.note || "-")}</td>
              </tr>
            `
          )
          .join("")
      : `<tr><td colspan="6">Brak wpisow ksiegowych.</td></tr>`;
  }

  if (matchBody) {
    matchBody.innerHTML = matches.length
      ? matches
          .map(
            (match) => `
              <tr>
                <td data-label="Status"><span class="status-badge ${match.match_status === "rozliczona" ? "status-success" : match.match_status === "czesciowo_rozliczona" ? "status-warning" : "status-muted"}">${bezpiecznyTekst(match.match_status || "-")}</span></td>
                <td data-label="Transakcja">${bezpiecznyTekst(match.transaction_title || "-")}<div class="muted">${bezpiecznyTekst(match.transaction_reference || "-")}</div></td>
                <td data-label="Platnik">${bezpiecznyTekst(match.payer_display_name || "-")}</td>
                <td data-label="Dopasowana kwota">${formatujKwote(match.matched_amount || 0)}</td>
                <td data-label="Powod">${bezpiecznyTekst(match.match_reason || "-")}</td>
                <td data-label="Data">${formatujDateCzas(match.matched_at)}</td>
              </tr>
            `
          )
          .join("")
      : `<tr><td colspan="6">Brak dopasowan platnosci.</td></tr>`;
  }

  if (payerSelect) {
    zbudujOpcjePlatnikowRozliczen();
  }
  if (transactionSelect) {
    const currentValue = transactionSelect.value;
    transactionSelect.innerHTML =
      `<option value="">Wybierz transakcje</option>` +
      (Array.isArray(stan.transakcjeRozliczen) ? stan.transakcjeRozliczen : [])
        .map(
          (transaction) => `
            <option value="${transaction.billing_transaction_id}">
              ${bezpiecznyTekst(formatujDateCzas(transaction.booking_date))} | ${bezpiecznyTekst(transaction.title || transaction.counterparty_name || transaction.reference || transaction.billing_transaction_id)}
            </option>
          `
        )
        .join("");
    if (
      currentValue &&
      stan.transakcjeRozliczen.some((transaction) => String(transaction.billing_transaction_id) === String(currentValue))
    ) {
      transactionSelect.value = currentValue;
    }
  }
  if (chargeSelect) {
    zbudujOpcjeNaleznosciDoDopasowania();
  }
  ustawStanPola(
    ["billing-match-transaction-id", "billing-match-payer-id", "billing-match-charge-id", "billing-match-amount", "billing-match-reason"],
    !canWrite
  );
  const matchSubmit = document.querySelector("#billing-manual-match-form button[type='submit']");
  if (matchSubmit) {
    matchSubmit.disabled = !canWrite;
  }
  odswiezPomocDopasowaniaPlatnosci();
}

async function wczytajKsiegeRozliczen() {
  if (!stan.biezacyUzytkownik) {
    stan.billingLedgerBalances = [];
    stan.billingLedgerEntries = [];
    stan.billingPaymentMatches = [];
    renderujKsiegeRozliczen();
    return;
  }
  const [balances, entries, matches] = await Promise.all([
    api(zbudujAdresZOrganizacja("/api/billing/ledger/balances")),
    api(zbudujAdresZOrganizacja("/api/billing/ledger/entries?limit=200")),
    api(zbudujAdresZOrganizacja("/api/billing/ledger/matches?limit=200")),
  ]);
  stan.billingLedgerBalances = Array.isArray(balances) ? balances : [];
  stan.billingLedgerEntries = Array.isArray(entries) ? entries : [];
  stan.billingPaymentMatches = Array.isArray(matches) ? matches : [];
  renderujKsiegeRozliczen();
}

async function dopasujPlatnoscRecznie() {
  if (!czyMoznaZapisywac()) {
    throw new Error("To konto nie ma prawa dopasowywania platnosci.");
  }
  const transactionId = Number(document.getElementById("billing-match-transaction-id")?.value || 0);
  const payerId = Number(document.getElementById("billing-match-payer-id")?.value || 0);
  const chargeId = Number(document.getElementById("billing-match-charge-id")?.value || 0);
  const matchedAmount = Number(document.getElementById("billing-match-amount")?.value || 0);
  const matchReason = document.getElementById("billing-match-reason")?.value.trim() || "";
  if (!transactionId || !payerId || matchedAmount <= 0) {
    throw new Error("Wybierz transakcje, platnika i dodatnia kwote dopasowania.");
  }
  await api(zbudujAdresZOrganizacja("/api/billing/ledger/matches"), {
    method: "POST",
    body: JSON.stringify({
      billing_transaction_id: transactionId,
      billing_payer_id: payerId,
      billing_charge_id: chargeId || null,
      matched_amount: matchedAmount,
      match_reason: matchReason,
    }),
  });
  pokazPowiadomienie("Dopasowano platnosc.");
  await wczytajRozliczenia();
}

function pobierzFiltrySkrzynkiWejsciowej() {
  const form = document.getElementById("inbox-filters-form");
  const data = form ? new FormData(form) : new FormData();
  const params = new URLSearchParams();
  for (const [key, value] of data.entries()) {
    const normalized = String(value || "").trim();
    if (normalized) {
      params.set(key, normalized);
    }
  }
  return params;
}

function renderujSkrzynkeWplywow() {
  const root = document.getElementById("inbox-root");
  if (!root) return;
  if (!stan.biezacyUzytkownik) {
    root.innerHTML = `<div class="empty-state">Zaloguj sie, aby zobaczyc inbox spraw i dokumentow.</div>`;
    return;
  }
  const canWrite = czyMoznaZapisywac();

  const forms = Array.isArray(stan.inboxForms) ? stan.inboxForms : [];
  const items = Array.isArray(stan.inboxItems) ? stan.inboxItems : [];
  const detail = stan.inboxSelectedItemDetail || null;
  const selectedItem = detail?.item || items.find((item) => Number(item.intake_item_id) === Number(stan.inboxSelectedItemId));
  const counts = {
    forms: forms.length,
    items: items.length,
    pending: items.filter((item) => String(item.status || "") === "nowe" || String(item.status || "") === "w_toku").length,
    overdue: items.filter((item) => String(item.status || "") !== "zakonczone" && String(item.due_at || "") && new Date(item.due_at).getTime() < Date.now()).length,
  };
  const userOptions = (Array.isArray(stan.uzytkownicyDoZadan) && stan.uzytkownicyDoZadan.length
    ? stan.uzytkownicyDoZadan
    : Array.isArray(stan.uzytkownicy)
      ? stan.uzytkownicy
      : []
  )
    .map((user) => `<option value="${user.user_id}">${bezpiecznyTekst(user.display_name || user.login || user.user_id)}</option>`)
    .join("");
  const formsHtml = forms.length
    ? forms
        .map(
          (form) => `
            <article class="list-item clickable" data-inbox-form-edit="${form.intake_form_id}">
              <div style="display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; align-items:flex-start;">
                <div>
                  <strong>${bezpiecznyTekst(form.form_name)}</strong>
                  <div class="muted">${bezpiecznyTekst(form.organization_name || "-")} | ${bezpiecznyTekst(form.form_slug)}</div>
                </div>
                <span class="status-badge ${form.is_public ? "status-success" : "status-muted"}">${form.is_public ? "aktywny" : "ukryty"}</span>
              </div>
              <div>${bezpiecznyTekst(form.description || "Brak opisu.")}</div>
            </article>
          `
        )
        .join("")
    : `<div class="empty-state">Brak formularzy w tej organizacji.</div>`;
  const itemsHtml = items.length
    ? items
        .map(
          (item) => `
            <article class="list-item clickable ${Number(item.intake_item_id) === Number(stan.inboxSelectedItemId) ? "is-selected" : ""}" data-inbox-item-id="${item.intake_item_id}">
              <div style="display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; align-items:flex-start;">
                <div>
                  <strong>${bezpiecznyTekst(item.title)}</strong>
                  <div class="muted">${bezpiecznyTekst(item.form_name || "-")} | ${bezpiecznyTekst(item.source_kind || "-")} | ${bezpiecznyTekst(item.assigned_user_name || "-")}</div>
                </div>
                <span class="status-badge ${klasaStatusuZadania(item.status)}">${bezpiecznyTekst(formatujStatusZadania(item.status))}</span>
              </div>
              <div class="muted">Priorytet: ${bezpiecznyTekst(formatujPriorytetZadania(item.priority))} | Termin: ${bezpiecznyTekst(formatujDateCzas(item.due_at))}</div>
            </article>
          `
        )
        .join("")
    : `<div class="empty-state">Brak spraw w inboxie.</div>`;

  const attachmentForm = selectedItem
    ? `
      <form id="inbox-attachment-form" class="stack">
        <div class="inline-file-row">
          <input type="file" id="inbox-attachment-file" />
          <button type="button" class="secondary" id="inbox-attachment-file-submit" ${canWrite ? "" : "disabled"}>Dodaj plik</button>
        </div>
        <div class="inline-file-row">
          <input type="text" id="inbox-attachment-link-title" placeholder="Nazwa linku" />
          <input type="url" id="inbox-attachment-link-url" placeholder="https://..." />
          <button type="button" class="secondary" id="inbox-attachment-link-submit" ${canWrite ? "" : "disabled"}>Dodaj link</button>
        </div>
      </form>
    `
    : `<div class="empty-state">Wybierz sprawÄ™, aby dodaÄ‡ zalacznik.</div>`;

  root.innerHTML = `
    <div class="summary-grid">
      <div class="summary-item"><strong>Formularze</strong><div>${counts.forms}</div></div>
      <div class="summary-item"><strong>Sprawy</strong><div>${counts.items}</div></div>
      <div class="summary-item"><strong>Aktywne</strong><div>${counts.pending}</div></div>
      <div class="summary-item"><strong>Po terminie</strong><div>${counts.overdue}</div></div>
    </div>

    <div class="content-grid contractors-grid">
      <div id="inbox-forms-shell" class="panel">
        <div class="panel-header">
          <h3>Formularze wejĹ›ciowe</h3>
          <span class="pill">${counts.forms}</span>
        </div>
        <div class="list">${formsHtml}</div>
        <div class="panel-header" style="margin-top: 16px;"><h3>Dodaj albo edytuj formularz</h3></div>
        <form id="inbox-form-editor" class="field-grid">
          <input type="hidden" id="inbox-form-id" />
          <div class="field"><label>Nazwa formularza</label><input id="inbox-form-name" type="text" placeholder="np. Wniosek urlopowy" /></div>
          <div class="field"><label>Slug</label><input id="inbox-form-slug" type="text" placeholder="wniosek-urlopowy" /></div>
          <div class="field"><label>Domyslny priorytet</label><select id="inbox-form-priority"><option value="niski">Niski</option><option value="normalny" selected>Normalny</option><option value="wysoki">Wysoki</option><option value="pilny">Pilny</option></select></div>
          <div class="field"><label>Domyslnie przypisany</label><select id="inbox-form-assigned-user"><option value="">Bez przypisania</option>${userOptions}</select></div>
          <div class="field field-full"><label>Opis</label><textarea id="inbox-form-description" rows="3"></textarea></div>
          <div class="field field-full"><label>Schemat pol (JSON)</label><textarea id="inbox-form-schema" rows="4" placeholder='[{"name":"field","type":"text"}]'></textarea></div>
          <div class="field"><label class="checkbox-inline"><input id="inbox-form-public" type="checkbox" checked /> Formularz publiczny</label></div>
          <div class="field"><label class="checkbox-inline"><input id="inbox-form-attachments" type="checkbox" checked /> Pozwalaj na zalaczniki</label></div>
          <div class="filters-actions field-full">
            <button type="submit" ${canWrite ? "" : "disabled"}>Zapisz formularz</button>
            <button type="button" class="secondary" id="inbox-form-reset">Nowy formularz</button>
            <button type="button" class="secondary" id="inbox-form-archive" ${stan.inboxSelectedFormId && canWrite ? "" : "disabled"}>Archiwizuj</button>
          </div>
        </form>
      </div>

      <div id="inbox-items-shell" class="panel">
        <div class="panel-header">
          <h3>Sprawy</h3>
          <span class="pill">${counts.items}</span>
        </div>
        <form id="inbox-filters-form" class="filters-grid">
          <input name="search" type="search" placeholder="Szukaj sprawy..." />
          <select name="status">
            <option value="">Wszystkie statusy</option>
            <option value="nowe">Nowe</option>
            <option value="w_toku">W toku</option>
            <option value="oczekuje">Oczekuje</option>
            <option value="zakonczone">Zakonczone</option>
            <option value="zarchiwizowane">Zarchiwizowane</option>
          </select>
          <select name="source_kind">
            <option value="">Wszystkie zrodla</option>
            <option value="manual">Manualne</option>
            <option value="form">Z formularza</option>
            <option value="automation">Automatyzacja</option>
            <option value="email">E-mail</option>
            <option value="telegram">Telegram</option>
          </select>
          <select name="assigned_user_id">
            <option value="">Przypisane wszystkim</option>
            ${userOptions}
          </select>
          <div class="filters-actions">
            <button type="submit">Odswiez teraz</button>
            <button type="button" class="secondary" id="inbox-filters-reset">Wyczysc</button>
          </div>
        </form>
        <div class="list" id="inbox-items-list">${itemsHtml}</div>
        <div class="panel-header" style="margin-top: 16px;"><h3>Dodaj nowa sprawÄ™</h3></div>
        <form id="inbox-item-create-form" class="field-grid">
          <div class="field"><label>Formularz</label><select id="inbox-item-form-id"><option value="">Bez formularza</option>${forms.map((form) => `<option value="${form.intake_form_id}">${bezpiecznyTekst(form.form_name)}</option>`).join("")}</select></div>
          <div class="field"><label>TytuĹ‚</label><input id="inbox-item-title" type="text" /></div>
          <div class="field"><label>Status</label><select id="inbox-item-status"><option value="nowe">Nowe</option><option value="w_toku">W toku</option><option value="oczekuje">Oczekuje</option><option value="zakonczone">Zakonczone</option><option value="zarchiwizowane">Zarchiwizowane</option></select></div>
          <div class="field"><label>Priorytet</label><select id="inbox-item-priority"><option value="niski">Niski</option><option value="normalny" selected>Normalny</option><option value="wysoki">Wysoki</option><option value="pilny">Pilny</option></select></div>
          <div class="field"><label>Przypisany</label><select id="inbox-item-assigned-user"><option value="">Bez przypisania</option>${userOptions}</select></div>
          <div class="field"><label>Termin</label><input id="inbox-item-due-at" type="datetime-local" /></div>
          <div class="field field-full"><label>Opis</label><textarea id="inbox-item-description" rows="3"></textarea></div>
          <div class="field field-full"><label>Dane dodatkowe (JSON)</label><textarea id="inbox-item-metadata" rows="4" placeholder='{"source":"..."}'></textarea></div>
          <div class="filters-actions field-full"><button type="submit" ${canWrite ? "" : "disabled"}>Dodaj sprawÄ™</button></div>
        </form>
      </div>
    </div>

    <div id="inbox-detail-shell" class="panel" style="margin-top: 18px;">
      <div class="panel-header">
        <h3>Szczegoly sprawy</h3>
        <span class="pill">${selectedItem ? `#${selectedItem.intake_item_id}` : "brak"}</span>
      </div>
      ${
        selectedItem
          ? `
            <div class="content-grid contractors-grid">
              <div class="panel">
                <form id="inbox-item-edit-form" class="field-grid">
                  <input type="hidden" id="inbox-item-id" value="${selectedItem.intake_item_id}" />
                  <div class="field"><label>Tytul</label><input id="inbox-item-edit-title" type="text" value="${bezpiecznyTekst(selectedItem.title)}" /></div>
                  <div class="field"><label>Status</label><select id="inbox-item-edit-status"><option value="nowe">Nowe</option><option value="w_toku">W toku</option><option value="oczekuje">Oczekuje</option><option value="zakonczone">Zakonczone</option><option value="zarchiwizowane">Zarchiwizowane</option></select></div>
                  <div class="field"><label>Priorytet</label><select id="inbox-item-edit-priority"><option value="niski">Niski</option><option value="normalny">Normalny</option><option value="wysoki">Wysoki</option><option value="pilny">Pilny</option></select></div>
                  <div class="field"><label>Przypisany</label><select id="inbox-item-edit-assigned-user"><option value="">Bez przypisania</option>${userOptions}</select></div>
                  <div class="field"><label>Termin</label><input id="inbox-item-edit-due-at" type="datetime-local" value="${formatujDateCzasDoInput(selectedItem.due_at)}" /></div>
                  <div class="field"><label>ĹąrĂłdĹ‚o</label><input id="inbox-item-edit-source" type="text" value="${bezpiecznyTekst(selectedItem.source_kind)}" /></div>
                  <div class="field field-full"><label>Opis</label><textarea id="inbox-item-edit-description" rows="3">${bezpiecznyTekst(selectedItem.description || "")}</textarea></div>
                  <div class="field field-full"><label>Metadane (JSON)</label><textarea id="inbox-item-edit-metadata" rows="4">${bezpiecznyTekst(JSON.stringify(selectedItem.metadata_json || {}, null, 2))}</textarea></div>
                  <div class="filters-actions field-full"><button type="submit" ${canWrite ? "" : "disabled"}>Zapisz sprawÄ™</button></div>
                </form>
              </div>
              <div class="panel">
                <div class="panel-header"><h3>Komentarze</h3></div>
                <div class="list" id="inbox-comments-list">
                  ${(Array.isArray(detail?.comments) && detail.comments.length
                    ? detail.comments
                        .map(
                          (comment) => `
                            <article class="list-item">
                              <div style="display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap;">
                                <strong>${bezpiecznyTekst(comment.created_by_user_name || "-")}</strong>
                                <span class="muted">${formatujDateCzas(comment.created_at)}</span>
                              </div>
                              <div>${bezpiecznyTekst(comment.note_text)}</div>
                            </article>
                          `
                        )
                        .join("")
                    : `<div class="empty-state">Brak komentarzy.</div>`)}
                </div>
                <form id="inbox-comment-form" class="stack" style="margin-top: 16px;">
                  <textarea id="inbox-comment-text" rows="3" placeholder="Dodaj komentarz, odpowiedz albo wzmianke @login"></textarea>
                  <button type="submit" ${canWrite ? "" : "disabled"}>Dodaj komentarz</button>
                </form>
              </div>
              <div class="panel">
                <div class="panel-header"><h3>Zalaczniki</h3></div>
                <div class="list" id="inbox-attachments-list">
                  ${(Array.isArray(detail?.attachments) && detail.attachments.length
                    ? detail.attachments
                        .map(
                          (attachment) => `
                            <article class="list-item">
                              <strong>${bezpiecznyTekst(attachment.file_name)}</strong>
                              <div class="muted">${bezpiecznyTekst(attachment.mime_type || "-")} | ${bezpiecznyTekst(
                                attachment.file_size || "-"
                              )}</div>
                              <a href="${bezpiecznyTekst(attachment.file_link)}" target="_blank" rel="noreferrer">Otworz</a>
                            </article>
                          `
                        )
                        .join("")
                    : `<div class="empty-state">Brak zalacznikow.</div>`)}
                </div>
                ${attachmentForm}
              </div>
              <div class="panel">
                <div class="panel-header"><h3>Historia</h3></div>
                <div class="list">
                  ${(Array.isArray(detail?.history) && detail.history.length
                    ? detail.history
                        .map(
                          (entry) => `
                            <article class="list-item">
                              <div style="display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap;">
                                <strong>${bezpiecznyTekst(entry.action_type)}</strong>
                                <span class="muted">${formatujDateCzas(entry.created_at)}</span>
                              </div>
                              <div>${bezpiecznyTekst(entry.message || "-")}</div>
                              <div class="muted">${bezpiecznyTekst(entry.actor || "-")}</div>
                            </article>
                          `
                        )
                        .join("")
                    : `<div class="empty-state">Brak historii.</div>`)}
                </div>
              </div>
            </div>
          `
          : `<div class="empty-state">Wybierz sprawÄ™ z listy, aby zobaczyÄ‡ szczegĂłĹ‚y, komentarze i zaĹ‚Ä…czniki.</div>`
      }
    </div>
  `;
  ustawStanPola(
    [
      "inbox-form-name",
      "inbox-form-slug",
      "inbox-form-priority",
      "inbox-form-assigned-user",
      "inbox-form-description",
      "inbox-form-schema",
      "inbox-form-public",
      "inbox-form-attachments",
      "inbox-item-form-id",
      "inbox-item-title",
      "inbox-item-status",
      "inbox-item-priority",
      "inbox-item-assigned-user",
      "inbox-item-due-at",
      "inbox-item-description",
      "inbox-item-metadata",
      "inbox-item-edit-title",
      "inbox-item-edit-status",
      "inbox-item-edit-priority",
      "inbox-item-edit-assigned-user",
      "inbox-item-edit-due-at",
      "inbox-item-edit-source",
      "inbox-item-edit-description",
      "inbox-item-edit-metadata",
      "inbox-comment-text",
      "inbox-attachment-file",
      "inbox-attachment-link-title",
      "inbox-attachment-link-url",
    ],
    !canWrite
  );

  if (selectedItem) {
    const editStatus = document.getElementById("inbox-item-edit-status");
    const editPriority = document.getElementById("inbox-item-edit-priority");
    const editAssigned = document.getElementById("inbox-item-edit-assigned-user");
    const editSource = document.getElementById("inbox-item-edit-source");
    if (editStatus) editStatus.value = selectedItem.status || "nowe";
    if (editPriority) editPriority.value = selectedItem.priority || "normalny";
    if (editAssigned) editAssigned.value = selectedItem.assigned_user_id || "";
    if (editSource) editSource.value = selectedItem.source_kind || "";
  }

  const formEditor = document.getElementById("inbox-form-editor");
  formEditor?.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await zapiszFormularzSkrzynki();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  document.getElementById("inbox-form-reset")?.addEventListener("click", () => {
    stan.inboxSelectedFormId = null;
    wyczyscFormularzSkrzynki();
    renderujSkrzynkeWplywow();
  });
  document.getElementById("inbox-form-archive")?.addEventListener("click", async () => {
    try {
      await usunFormularzSkrzynki();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  document.getElementById("inbox-filters-form")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    await wczytajSkrzynkeWplywow();
  });
  podlaczAutomatyczneFiltrowanieFormularza("inbox-filters-form", "inboxFilterApplyTimeoutId", wczytajSkrzynkeWplywow);
  document.getElementById("inbox-filters-reset")?.addEventListener("click", () => {
    document.getElementById("inbox-filters-form")?.reset();
    wczytajSkrzynkeWplywow().catch(() => {});
  });
  document.querySelectorAll("[data-inbox-form-edit]").forEach((button) => {
    button.addEventListener("click", () => ustawFormularzSkrzynki(Number(button.dataset.inboxFormEdit)));
  });
  document.querySelectorAll("[data-inbox-item-id]").forEach((button) => {
    button.addEventListener("click", () => wczytajSzczegolySkrzynki(Number(button.dataset.inboxItemId)));
  });
  document.getElementById("inbox-item-create-form")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await zapiszSpraweSkrzynki();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  document.getElementById("inbox-item-edit-form")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await aktualizujSpraweSkrzynki();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  document.getElementById("inbox-comment-form")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await dodajKomentarzDoSkrzynki();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  document.getElementById("inbox-attachment-file-submit")?.addEventListener("click", async () => {
    try {
      await dodajZalacznikDoSkrzynki("file");
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  document.getElementById("inbox-attachment-link-submit")?.addEventListener("click", async () => {
    try {
      await dodajZalacznikDoSkrzynki("link");
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  odswiezWartoscFormularzaSkrzynki();
}

async function ponowWpisOutboxaPrzypomnien(outboxId) {
  const normalizedOutboxId = Number(outboxId || 0);
  if (!normalizedOutboxId || !czyMoznaZapisywac()) {
    return null;
  }
  const result = await api(
    zbudujAdresZOrganizacja(`/api/tasks/reminders/outbox/${normalizedOutboxId}/retry`),
    {
      method: "POST",
    }
  );
  pokazPowiadomienie("Ponowiono wpis outboxa.");
  await Promise.all([
    wczytajStatusPrzypomnien(),
    wczytajPulpit(),
    wczytajZadania(),
    wczytajPlannerZadan(),
    wczytajFokusZadan(),
    wczytajLogi(),
  ]);
  return result;
}

function pobierzSzczegolyJSON(value) {
  if (!value) return {};
  if (typeof value === "object") return value;
  try {
    return JSON.parse(value);
  } catch (error) {
    return {};
  }
}

function czyMaZnaczenieDlaKontekstu(value) {
  return value !== null && value !== undefined && String(value).trim() !== "";
}

function zbudujOpisKontekstuZdarzenia(event) {
  const elementy = [];
  const szczegoly = pobierzSzczegolyJSON(event.details);

  if (czyMaZnaczenieDlaKontekstu(event.invoice_id)) {
    elementy.push(`Faktura #${bezpiecznyTekst(event.invoice_id)}`);
  }

  if (czyMaZnaczenieDlaKontekstu(szczegoly.task_id)) {
    elementy.push(`Zadanie #${bezpiecznyTekst(szczegoly.task_id)}`);
  }

  if (czyMaZnaczenieDlaKontekstu(szczegoly.billing_bank_account_id)) {
    elementy.push(`Rachunek #${bezpiecznyTekst(szczegoly.billing_bank_account_id)}`);
  }

  if (czyMaZnaczenieDlaKontekstu(szczegoly.billing_statement_import_id)) {
    elementy.push(`Import wyciagu #${bezpiecznyTekst(szczegoly.billing_statement_import_id)}`);
  }

  if (czyMaZnaczenieDlaKontekstu(event.source)) {
    elementy.push(`ĹąrĂłdĹ‚o: ${formatujZrodlo(event.source)}`);
  }

  return elementy.join(" | ");
}

function formatujNazweOrganizacji(value) {
  return value ? bezpiecznyTekst(value) : "Brak przypisania";
}

function pobierzRoleUzytkownika() {
  return stan.biezacyUzytkownik?.role || "";
}

function czyWlascicielSystemu() {
  return Boolean(stan.biezacyUzytkownik?.is_global_admin) || pobierzRoleUzytkownika() === "system_owner";
}

function czyAdministratorOrganizacji() {
  return pobierzRoleUzytkownika() === "organization_admin";
}

function czyMenedzerskiWidokAsystenta() {
  return ["system_owner", "organization_admin", "coordinator"].includes(pobierzRoleUzytkownika());
}

function czyMozeTworzycKalendarzePrywatneLubRodzinne() {
  return czyWlascicielSystemu() || czyAdministratorOrganizacji();
}

function czyAdministrator() {
  return roleGrupy.userManagement.includes(pobierzRoleUzytkownika());
}

function czyGlobalnyAdministrator() {
  return czyWlascicielSystemu();
}

function czyMoznaZarzadzacUzytkownikami() {
  return roleGrupy.userManagement.includes(pobierzRoleUzytkownika());
}

function czyMoznaZarzadzacOrganizacjami() {
  return roleGrupy.organizationSettings.includes(pobierzRoleUzytkownika());
}

function czyMoznaTworzycOrganizacje() {
  return roleGrupy.organizationManagement.includes(pobierzRoleUzytkownika());
}

function czyMoznaOtworzycCentrumEmaila() {
  return roleGrupy.organizationSettings.includes(pobierzRoleUzytkownika());
}

function czyMoznaZapisywac() {
  return roleGrupy.write.includes(pobierzRoleUzytkownika());
}

function ustawStanPola(identyfikatory, disabled) {
  if (!Array.isArray(identyfikatory)) {
    return;
  }
  identyfikatory.forEach((identyfikator) => {
    const element = document.getElementById(identyfikator);
    if (element) {
      element.disabled = disabled;
    }
  });
}

function czyMoznaPodejmowacDecyzjeFaktur() {
  return roleGrupy.invoiceDecision.includes(pobierzRoleUzytkownika());
}

function czyMoznaPrzypisywacFaktury() {
  return roleGrupy.invoiceDecision.includes(pobierzRoleUzytkownika());
}

function czyMoznaPrzypisywacZadania() {
  return roleGrupy.taskAssignment.includes(pobierzRoleUzytkownika());
}

function pobierzAktywnaOrganizacjeDlaModulow() {
  if (!stan.biezacyUzytkownik) {
    return null;
  }
  const aktywnaOrganizacja = pobierzAktywnaOrganizacje();
  if (aktywnaOrganizacja) {
    return aktywnaOrganizacja;
  }
  if (czyGlobalnyAdministrator()) {
    return null;
  }
  return {
    organization_id: stan.biezacyUzytkownik.organization_id,
    name: stan.biezacyUzytkownik.organization_name,
    enabled_modules: Array.isArray(stan.biezacyUzytkownik.organization_modules)
      ? stan.biezacyUzytkownik.organization_modules
      : [],
    module_shortcuts:
      typeof stan.biezacyUzytkownik.organization_module_shortcuts === "object" &&
      stan.biezacyUzytkownik.organization_module_shortcuts !== null
        ? stan.biezacyUzytkownik.organization_module_shortcuts
        : {},
  };
}

function czyOrganizacjaMaModul(moduleCode) {
  const organizacja = pobierzAktywnaOrganizacjeDlaModulow();
  const aktywneModuly = Array.isArray(organizacja?.enabled_modules) ? organizacja.enabled_modules : [];
  return aktywneModuly.includes(moduleCode);
}

function czyModulAsystentaSzefaAktywny() {
  return czyOrganizacjaMaModul(organizationModuleCodes.managerAssistant);
}

function czyMoznaOtworzycWidokZeSkrotu(widok) {
  if (!stan.biezacyUzytkownik) {
    return widok === "dashboard";
  }
  if (widok === "users") {
    return czyMoznaZarzadzacUzytkownikami();
  }
  if (widok === "organizations") {
    return czyMoznaZarzadzacOrganizacjami();
  }
  if (widok === "email-center") {
    return czyMoznaOtworzycCentrumEmaila();
  }
  if (widok === "tasks") {
    return czyMoznaOtworzycAsystentaSzefa() || czyMoznaKorzystacZMojejPracy();
  }
  if (widok === "inbox") {
    return czyMoznaZapisywac();
  }
  if (widok === "knowledge") {
    return czyMoznaCzytacBazeWiedzy();
  }
  return Object.prototype.hasOwnProperty.call(opisyWidokow, widok);
}

function renderujPolaSkrotowModulowOrganizacji(moduleShortcuts = {}) {
  const container = document.getElementById("organization-module-shortcuts");
  if (!container) {
    return;
  }

  container.innerHTML = Object.entries(moduleShortcutDefinitions)
    .map(
      ([view, definition]) => `
        <div class="field">
          <label for="organization-shortcut-${view}">${bezpiecznyTekst(definition.label)}</label>
          <input
            id="organization-shortcut-${view}"
            data-organization-shortcut-view="${view}"
            type="text"
            inputmode="text"
            autocomplete="off"
            placeholder="${bezpiecznyTekst(definition.placeholder)}"
            value="${bezpiecznyTekst(moduleShortcuts?.[view] || "")}"
          />
        </div>
      `
    )
    .join("");
}

function pobierzSkrotyModulowZFormularza() {
  const wynik = {};
  document.querySelectorAll("[data-organization-shortcut-view]").forEach((input) => {
    const view = input.dataset.organizationShortcutView || "";
    if (!Object.prototype.hasOwnProperty.call(moduleShortcutDefinitions, view)) {
      return;
    }
    wynik[view] = String(input.value || "").trim();
  });
  return wynik;
}

function czyElementPrzyjmujeWpisKlawiatury(element) {
  if (!(element instanceof Element)) {
    return false;
  }
  if (element.isContentEditable) {
    return true;
  }
  return Boolean(element.closest("input, textarea, select, [contenteditable='true']"));
}

function pobierzAktywneSkrotyModulow() {
  const organizacja = pobierzAktywnaOrganizacjeDlaModulow();
  if (!organizacja || typeof organizacja.module_shortcuts !== "object" || organizacja.module_shortcuts === null) {
    return {};
  }
  return organizacja.module_shortcuts;
}

function zbudujSkrotZeZdarzeniaKlawiaturowego(event) {
  if (event.metaKey || !(event.ctrlKey || event.altKey) || event.repeat) {
    return "";
  }
  const key = String(event.key || "").trim();
  if (!key || ["Control", "Shift", "Alt", "Meta"].includes(key)) {
    return "";
  }
  if (key.length !== 1 || !/^[a-z0-9]$/i.test(key)) {
    return "";
  }
  const parts = [];
  if (event.ctrlKey) {
    parts.push("Ctrl");
  }
  if (event.altKey) {
    parts.push("Alt");
  }
  if (event.shiftKey) {
    parts.push("Shift");
  }
  parts.push(key.toUpperCase());
  return parts.join("+");
}

function obsluzSkrotyModulow(event) {
  if (!stan.biezacyUzytkownik || czyElementPrzyjmujeWpisKlawiatury(event.target)) {
    return;
  }
  const shortcut = zbudujSkrotZeZdarzeniaKlawiaturowego(event);
  if (!shortcut) {
    return;
  }
  const shortcuts = pobierzAktywneSkrotyModulow();
  const targetView =
    Object.entries(shortcuts).find(([view, configuredShortcut]) => configuredShortcut === shortcut && czyMoznaOtworzycWidokZeSkrotu(view))?.[0] ||
    "";
  if (!targetView) {
    return;
  }
  event.preventDefault();
  ustawWidok(targetView);
}

function czyMoznaKorzystacZMojejPracy() {
  return czyMoznaZapisywac() && czyModulAsystentaSzefaAktywny();
}

function czyMoznaOtworzycAsystentaSzefa() {
  return czyMoznaPrzypisywacZadania() && czyModulAsystentaSzefaAktywny();
}

function czyWidokZadanJestTrybemPracownika() {
  return czyMoznaKorzystacZMojejPracy() && !czyMenedzerskiWidokAsystenta();
}

function pobierzOpisWidoku(widok) {
  if (widok === "tasks" && czyWidokZadanJestTrybemPracownika()) {
    return {
      tytul: "Moja praca",
      podtytul: "Twoje zadania, wydarzenia, przypomnienia, notatki i kalendarze.",
    };
  }
  return opisyWidokow[widok] || opisyWidokow.dashboard;
}

function czyJestGosciem() {
  return pobierzRoleUzytkownika() === "guest";
}

function pobierzCapabilitiesUzytkownika() {
  return Array.isArray(stan.biezacyUzytkownik?.capabilities) ? stan.biezacyUzytkownik.capabilities : [];
}

function czyUzytkownikMaCapability(capability) {
  return pobierzCapabilitiesUzytkownika().includes(capability);
}

function czyMoznaCzytacBazeWiedzy() {
  return czyUzytkownikMaCapability("knowledge.read");
}

function czyMoznaDodawacPlikiDoBazyWiedzy() {
  return czyUzytkownikMaCapability("knowledge.upload");
}

function czyMoznaSynchronizowacBazeWiedzy() {
  return czyUzytkownikMaCapability("knowledge.sync");
}

function czyMoznaZarzadzacPrzetwarzaniemBazyWiedzy() {
  return czyUzytkownikMaCapability("knowledge.manage");
}

function formatujZrodloBazyWiedzy(sourceType) {
  return etykietyZrodelBazyWiedzy[sourceType] || "Dokument";
}

function klasaStatusuZrodlaBazyWiedzy(sourceType) {
  if (sourceType === "folder_sync") {
    return "status-success";
  }
  if (sourceType === "manual") {
    return "status-warning";
  }
  return "status-normal";
}

function formatujStatusPrzetwarzaniaBazyWiedzy(status) {
  const labels = {
    queued: "w kolejce",
    processing: "przetwarzanie",
    ready: "gotowy",
    error: "blad",
  };
  return labels[status] || "nieznany";
}

function klasaStatusuPrzetwarzaniaBazyWiedzy(status) {
  if (status === "ready") return "status-success";
  if (status === "error") return "status-danger";
  if (status === "processing") return "status-warning";
  return "status-normal";
}

function pobierzFormatyBazyWiedzy() {
  if (Array.isArray(stan.konfiguracjaBazyWiedzy?.supported_formats) && stan.konfiguracjaBazyWiedzy.supported_formats.length) {
    return stan.konfiguracjaBazyWiedzy.supported_formats;
  }
  return domyslneFormatyBazyWiedzy;
}

function opisOcrBazyWiedzy() {
  if (!stan.konfiguracjaBazyWiedzy?.ocr_enabled) {
    return "OCR jest obecnie niedostepny dla plikow graficznych.";
  }
  if (stan.konfiguracjaBazyWiedzy?.ocr_mode && stan.konfiguracjaBazyWiedzy.ocr_mode !== "fallback") {
    return `OCR aktywny (${bezpiecznyTekst(stan.konfiguracjaBazyWiedzy.ocr_mode)}) dla JPG, PNG i TIFF.`;
  }
  return "OCR aktywny dla JPG, PNG i TIFF.";
}

function ustawPanelImportuBazyWiedzy({ title, description, variant = "normal" }) {
  const box = document.getElementById("knowledge-import-feedback");
  const titleElement = document.getElementById("knowledge-import-title");
  const descriptionElement = document.getElementById("knowledge-import-description");
  if (!box || !titleElement || !descriptionElement) {
    return;
  }

  box.classList.toggle("is-success", variant === "success");
  box.classList.toggle("is-warning", variant === "warning");
  titleElement.textContent = title;
  descriptionElement.innerHTML = description;
}

function zbudujOpisPominietychPlikow(skipped) {
  if (!Array.isArray(skipped) || !skipped.length) {
    return "";
  }
  return skipped
    .slice(0, 3)
    .map((item) => {
      const fileName = bezpiecznyTekst(item.file_name || "plik");
      const reason = bezpiecznyTekst(item.reason || "brak szczegolow");
      return `${fileName} (${reason})`;
    })
    .join(", ");
}

function odswiezPanelImportuBazyWiedzy() {
  const formaty = bezpiecznyTekst(pobierzFormatyBazyWiedzy().join(", "));
  const podstawowyOpis = `Obslugiwane formaty: ${formaty}. ${opisOcrBazyWiedzy()}`;
  const plik = document.getElementById("knowledge-file")?.files?.[0];
  const tytul = document.getElementById("knowledge-title")?.value.trim() || "";
  const tresc = document.getElementById("knowledge-content")?.value.trim() || "";

  if (!stan.biezacyUzytkownik) {
    ustawPanelImportuBazyWiedzy({
      title: "Import dokumentow",
      description: `Zaloguj sie, aby importowac dokumenty do bazy wiedzy. ${podstawowyOpis}`,
    });
    return;
  }

  if (!czyModulWiedzyMaZakres()) {
    ustawPanelImportuBazyWiedzy({
      title: "Wybierz organizacje",
      description: `Najpierw wybierz organizacje, a potem dodaj plik lub uruchom synchronizacje folderu. ${podstawowyOpis}`,
      variant: "warning",
    });
    return;
  }

  if (stan.ostatniImportBazyWiedzy?.kind === "sync") {
    const summary = stan.ostatniImportBazyWiedzy;
    const skippedCount = Array.isArray(summary.skipped) ? summary.skipped.length : 0;
    const skippedDetails = zbudujOpisPominietychPlikow(summary.skipped);
    const queuedInfo =
      Number(summary.imported_count || 0) || Number(summary.updated_count || 0)
        ? " Dokumenty trafily do kolejki, a widok odswieza sie automatycznie do czasu zakonczenia przetwarzania."
        : "";
    ustawPanelImportuBazyWiedzy({
      title: "Synchronizacja zakonczona",
      description:
        `Nowe: <strong>${bezpiecznyTekst(summary.imported_count || 0)}</strong>, ` +
        `zaktualizowane: <strong>${bezpiecznyTekst(summary.updated_count || 0)}</strong>, ` +
        `bez zmian: <strong>${bezpiecznyTekst(summary.unchanged_count || 0)}</strong>, ` +
        `pominiete: <strong>${bezpiecznyTekst(skippedCount)}</strong>.` +
        (skippedDetails ? ` Pominieto: ${skippedDetails}.` : "") +
        queuedInfo +
        ` ${podstawowyOpis}`,
      variant: skippedCount && !(summary.imported_count || summary.updated_count) ? "warning" : "success",
    });
    return;
  }

  if (stan.ostatniImportBazyWiedzy?.kind === "upload") {
    const summary = stan.ostatniImportBazyWiedzy;
    const sourceLabel = formatujZrodloBazyWiedzy(summary.source_type).toLowerCase();
    const processingInfo =
      summary.processing_status && summary.processing_status !== "ready"
        ? " Dokument jest w kolejce i widok odswieza sie automatycznie."
        : " Dokument jest gotowy do pytan.";
    ustawPanelImportuBazyWiedzy({
      title: "Dokument dodany",
      description:
        `Zapisano <strong>${bezpiecznyTekst(summary.title || summary.file_name || "Dokument")}</strong> ` +
        `jako ${bezpiecznyTekst(sourceLabel)}.` +
        (summary.file_name ? ` Plik: ${bezpiecznyTekst(summary.file_name)}.` : "") +
        (summary.file_size ? ` Rozmiar: ${bezpiecznyTekst(formatujRozmiarPliku(summary.file_size))}.` : "") +
        processingInfo +
        ` ${podstawowyOpis}`,
      variant: "success",
    });
    return;
  }

  if (!czyMoznaDodawacPlikiDoBazyWiedzy()) {
    ustawPanelImportuBazyWiedzy({
      title: "Tryb tylko do odczytu",
      description:
        `To konto moze zadawac pytania do asystenta, ale nie moze importowac nowych plikow. ` +
        `Wlasciciel systemu albo Administrator organizacji moze wlaczyc to uprawnienie przy koncie uzytkownika. ${podstawowyOpis}`,
      variant: "warning",
    });
    return;
  }

  if (plik) {
    const czyObraz = /\.(jpg|jpeg|png|bmp|tif|tiff|webp)$/i.test(plik.name);
    ustawPanelImportuBazyWiedzy({
      title: "Plik gotowy do importu",
      description:
        `Wybrano <strong>${bezpiecznyTekst(plik.name)}</strong> ` +
        `(${bezpiecznyTekst(formatujRozmiarPliku(plik.size))}). ` +
        (tytul ? `Tytul dokumentu: ${bezpiecznyTekst(tytul)}. ` : "") +
        (czyObraz ? `${opisOcrBazyWiedzy()} ` : "") +
        podstawowyOpis,
    });
    return;
  }

  if (tresc) {
    ustawPanelImportuBazyWiedzy({
      title: "Dokument tekstowy",
      description:
        `Wklejona tresc zostanie zapisana jako osobny dokument wiedzy.` +
        (tytul ? ` Tytul: ${bezpiecznyTekst(tytul)}.` : "") +
        ` ${podstawowyOpis}`,
    });
    return;
  }

  ustawPanelImportuBazyWiedzy({
    title: "Import dokumentow",
    description:
      `Mozesz dodac plik bezposrednio tutaj albo wrzucic go do folderu organizacji i uruchomic synchronizacje. ` +
      podstawowyOpis,
  });
}

function ustawDomyslneUprawnienieBazyWiedzyDlaRoli() {
  const checkbox = document.getElementById("user-can-upload-knowledge");
  const roleSelect = document.getElementById("user-role");
  if (!checkbox || !roleSelect || stan.wybranyUzytkownikId) {
    return;
  }
  checkbox.checked = roleGrupy.knowledgeUploadDefault.includes(roleSelect.value || "operator");
}

function pobierzDomyslneCapabilitiesDlaRoli(role) {
  return [...(defaultCapabilitiesByRole[role] || ["knowledge.read"])];
}

function pobierzZaznaczoneCapabilitiesZFormularzaUzytkownika() {
  return Array.from(document.querySelectorAll('[data-user-capability]'))
    .filter((input) => input.checked)
    .map((input) => input.value);
}

function odswiezCapabilityFormularzaUzytkownika() {
  const checkbox = document.getElementById("user-can-upload-knowledge");
  const capabilityUpload = document.querySelector('[data-user-capability="knowledge.upload"]');
  const capabilitySync = document.querySelector('[data-user-capability="knowledge.sync"]');
  if (!checkbox || !capabilityUpload || !capabilitySync) {
    return;
  }
  const checked = checkbox.checked;
  capabilityUpload.checked = checked;
  capabilitySync.checked = checked;
}

function ustawCapabilitiesFormularzaUzytkownika(capabilities, options = {}) {
  const normalized = new Set((Array.isArray(capabilities) ? capabilities : []).filter(Boolean));
  if (!normalized.size) {
    normalized.add("knowledge.read");
  }
  document.querySelectorAll("[data-user-capability]").forEach((input) => {
    input.checked = normalized.has(input.value);
  });
  if (!options.skipUploadSyncRefresh) {
    const uploadEnabled = normalized.has("knowledge.upload");
    const uploadCheckbox = document.getElementById("user-can-upload-knowledge");
    if (uploadCheckbox) {
      uploadCheckbox.checked = uploadEnabled;
    }
  }
}

function renderujCapabilitiesFormularzaUzytkownika() {
  const container = document.getElementById("user-capabilities-list");
  if (!container) {
    return;
  }
  const selectedRole = document.getElementById("user-role")?.value || "operator";
  const disabled = !czyMoznaZarzadzacUzytkownikami();
  const currentCapabilities = stan.wybranyUzytkownikId
    ? stan.uzytkownicy.find((item) => Number(item.user_id) === Number(stan.wybranyUzytkownikId))?.capabilities || []
    : pobierzDomyslneCapabilitiesDlaRoli(selectedRole);

  container.innerHTML = (stan.meta?.knowledge_capabilities || Object.keys(capabilityLabels))
    .map((capability) => {
      const checked = currentCapabilities.includes(capability) ? "checked" : "";
      const inputDisabled = capability === "knowledge.read" ? "disabled" : disabled ? "disabled" : "";
      return `
        <label class="capability-item">
          <input type="checkbox" data-user-capability="${bezpiecznyTekst(capability)}" value="${bezpiecznyTekst(capability)}" ${checked} ${inputDisabled} />
          <span>${bezpiecznyTekst(capabilityLabels[capability] || capability)}</span>
        </label>
      `;
    })
    .join("");
  ustawCapabilitiesFormularzaUzytkownika(currentCapabilities, { skipUploadSyncRefresh: false });
}

function klasaStatusu(status, duplicateType = "") {
  if (duplicateType === "pewny" || status === "pewny_duplikat") return "status-danger";
  if (duplicateType === "podejrzenie" || status === "podejrzenie_duplikatu" || status === "weryfikacja") return "status-warning";
  if (status === "poprawna" || status === "zaksiegowana") return "status-success";
  return "status-normal";
}

function klasaStatusuObieguFaktury(workflowState) {
  if (workflowState === "przekazana") return "status-success";
  if (workflowState === "gotowa_do_przekazania") return "status-warning";
  if (workflowState === "zamknieta") return "status-neutral";
  return "status-normal";
}

function klasaStatusuZadania(status, priority = "") {
  if (status === "anulowane") return "status-danger";
  if (status === "zakonczone") return "status-success";
  if (priority === "krytyczny" || priority === "wysoki" || status === "oczekuje") return "status-warning";
  return "status-normal";
}

function klasaStatusuDopasowaniaTransakcji(status) {
  if (status === "rozliczona") return "status-success";
  if (status === "czesciowo_rozliczona") return "status-warning";
  return "status-normal";
}

function pokazPowiadomienie(message) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.classList.remove("hidden");
  window.clearTimeout(pokazPowiadomienie.timeoutId);
  pokazPowiadomienie.timeoutId = window.setTimeout(() => toast.classList.add("hidden"), 3200);
}

function pobierzInicjalyUzytkownika(user) {
  const zrodlo = String(user?.display_name || user?.login || "U").trim();
  const fragmenty = zrodlo.split(/\s+/).filter(Boolean);
  const inicjaly = fragmenty.slice(0, 2).map((fragment) => fragment.charAt(0).toUpperCase()).join("");
  return inicjaly || "U";
}

function ustawPozycjePaneluNaglowka(panelId, anchorId, preferredWidth = 320) {
  const panel = document.getElementById(panelId);
  const anchor = document.getElementById(anchorId);
  if (!panel || !anchor || panel.classList.contains("hidden")) {
    return;
  }
  const viewportWidth = window.innerWidth || document.documentElement.clientWidth || 0;
  const viewportHeight = window.innerHeight || document.documentElement.clientHeight || 0;
  if (!viewportWidth || !viewportHeight) {
    return;
  }
  const gutter = viewportWidth <= 760 ? 12 : 16;
  const panelWidth = Math.max(
    Math.min(preferredWidth, viewportWidth - gutter * 2),
    Math.min(220, viewportWidth - gutter * 2)
  );
  const anchorRect = anchor.getBoundingClientRect();
  const left = Math.min(
    Math.max(gutter, anchorRect.right - panelWidth),
    Math.max(gutter, viewportWidth - panelWidth - gutter)
  );
  const top = Math.min(
    Math.max(gutter, anchorRect.bottom + 10),
    Math.max(gutter, viewportHeight - gutter - 180)
  );
  panel.style.left = `${Math.round(left)}px`;
  panel.style.right = "auto";
  panel.style.top = `${Math.round(top)}px`;
  panel.style.bottom = "auto";
  panel.style.width = `${Math.round(panelWidth)}px`;
  panel.style.maxWidth = `${Math.round(panelWidth)}px`;
  panel.style.maxHeight = `${Math.round(Math.max(180, viewportHeight - top - gutter))}px`;
}

function ustawPozycjePaneliNaglowka() {
  ustawPozycjePaneluNaglowka("organization-switcher-box", "topbar-more-toggle", 320);
  ustawPozycjePaneluNaglowka("session-box", "profile-menu-toggle", 300);
}

function renderujMenuNaglowka() {
  const profileToggle = document.getElementById("profile-menu-toggle");
  const moreToggle = document.getElementById("topbar-more-toggle");
  const profileMenu = document.getElementById("session-box");
  const moreMenu = document.getElementById("organization-switcher-box");
  const profileAvatar = document.getElementById("profile-menu-avatar");
  const userChip = document.getElementById("topbar-user-chip");
  const userInline = document.getElementById("session-user-inline");
  const whiteboardLauncher = document.getElementById("whiteboard-launcher");
  const loggedIn = Boolean(stan.biezacyUzytkownik);
  const initials = pobierzInicjalyUzytkownika(stan.biezacyUzytkownik);
  const userName = stan.biezacyUzytkownik?.display_name || stan.biezacyUzytkownik?.login || "";

  if (profileAvatar) {
    profileAvatar.textContent = initials;
  }
  if (userInline) {
    userInline.textContent = userName;
  }
  if (userChip) {
    userChip.classList.toggle("hidden", !loggedIn);
  }
  if (whiteboardLauncher) {
    whiteboardLauncher.classList.toggle("hidden", !loggedIn);
  }
  if (profileToggle) {
    profileToggle.classList.toggle("hidden", !loggedIn);
    profileToggle.setAttribute("aria-expanded", stan.profilMenuOtwarte ? "true" : "false");
  }
  if (moreToggle) {
    moreToggle.classList.toggle("hidden", !loggedIn);
    moreToggle.setAttribute("aria-expanded", stan.menuWiecejOtwarte ? "true" : "false");
  }
  if (profileMenu) {
    profileMenu.classList.toggle("hidden", !loggedIn || !stan.profilMenuOtwarte);
  }
  if (moreMenu) {
    moreMenu.classList.toggle("hidden", !loggedIn || !stan.menuWiecejOtwarte);
  }
  window.requestAnimationFrame(() => ustawPozycjePaneliNaglowka());
}

function zamknijMenuNaglowka() {
  stan.profilMenuOtwarte = false;
  stan.menuWiecejOtwarte = false;
  renderujMenuNaglowka();
}

function pokazEkranLogowania() {
  document.body.classList.add("auth-required");
  document.getElementById("login-screen").classList.remove("hidden");
  zamknijMenuNaglowka();
}

function ukryjEkranLogowania() {
  document.body.classList.remove("auth-required");
  document.getElementById("login-screen").classList.add("hidden");
}

function ustawWidok(widok) {
  const poprzedniWidok = stan.aktywnyWidok;
  if (!stan.biezacyUzytkownik && widok !== "dashboard") {
    widok = "dashboard";
  }
  if (widok === "users" && !czyMoznaZarzadzacUzytkownikami()) {
    widok = "dashboard";
  }
  if (widok === "organizations" && !czyMoznaZarzadzacOrganizacjami()) {
    widok = "dashboard";
  }
  if (widok === "email-center" && !czyMoznaOtworzycCentrumEmaila()) {
    widok = "dashboard";
  }
  if (widok === "tasks" && !czyMoznaOtworzycAsystentaSzefa() && !czyMoznaKorzystacZMojejPracy()) {
    widok = czyMoznaCzytacBazeWiedzy() ? "knowledge" : "dashboard";
  }
  if (widok === "inbox" && !czyMoznaZapisywac()) {
    widok = "support";
  }
  stan.aktywnyWidok = widok;
  document.querySelectorAll(".view").forEach((sekcja) => sekcja.classList.remove("active"));
  document.getElementById(`${widok}-view`).classList.add("active");
  document.querySelectorAll(".nav-item").forEach((przycisk) => {
    przycisk.classList.toggle("active", przycisk.dataset.view === widok);
  });
  document.querySelectorAll("[data-launch-view]").forEach((przycisk) => {
    przycisk.classList.toggle("active", przycisk.dataset.launchView === widok);
  });
  const aktywnaKartaKaruzeli = document.querySelector(`.nav-item-carousel[data-view="${widok}"]`);
  if (aktywnaKartaKaruzeli) {
    aktywnaKartaKaruzeli.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
  }
  window.setTimeout(() => odswiezKaruzeleModulow(), 40);
  const opisWidoku = pobierzOpisWidoku(widok);
  document.getElementById("view-title").textContent = opisWidoku.tytul;
  document.getElementById("view-subtitle").textContent = opisWidoku.podtytul;
  if (poprzedniWidok !== widok) {
    podswietlPrzejscieDoWidoku(widok);
  }
  const loaders = {
    "email-center": () => wczytajCentrumEmaila(),
    billing: () => wczytajRozliczenia(),
    support: () => wczytajPomoc(),
    inbox: () => wczytajSkrzynkeWplywow(),
    views: () => wczytajZapisaneWidoki(),
    automation: () => wczytajAutomatyzacje(),
    health: () => wczytajZdrowieSystemu(),
    knowledge: () => wczytajBazeWiedzy(),
  };
  if (loaders[widok]) {
    loaders[widok]().catch((error) => pokazPowiadomienie(error.message));
  }
}

function czyImportTestowyWlaczony() {
  return Boolean(stan.meta?.test_imports_enabled);
}

function znajdzSekcjeImportuTestowego() {
  return document.getElementById("test-import-section");
}

function ustawWidocznoscElementowSrodowiska() {
  const sekcjaImportu = znajdzSekcjeImportuTestowego();
  const opisLogowania = document.querySelector("#login-screen .auth-card p");
  const notaBazyWiedzy = document.querySelector("#knowledge-upload-form .subtle-note:last-of-type");
  if (sekcjaImportu) {
    sekcjaImportu.classList.toggle("hidden", !czyImportTestowyWlaczony());
  }
  if (opisLogowania) {
    opisLogowania.textContent = "Zaloguj siÄ™ loginem i hasĹ‚em utworzonym przez WĹ‚aĹ›ciciela systemu albo Administratora organizacji.";
  }
  if (notaBazyWiedzy) {
    notaBazyWiedzy.textContent =
      "UĹĽytkownik z prawem zapisu moĹĽe dodaÄ‡ plik tutaj albo wrzuciÄ‡ dokument bezpoĹ›rednio do folderu organizacji i uĹĽyÄ‡ synchronizacji.";
  }

  const podpowiedzLogowania =
    document.getElementById("default-login-hint") || document.querySelector("#login-screen .subtle-note");
  const czyAktualneMetaSrodowiska =
    Boolean(stan.meta) && Object.prototype.hasOwnProperty.call(stan.meta, "task_visibility_scopes");
  const pokazPodpowiedzLogowania = Boolean(czyAktualneMetaSrodowiska && stan.meta?.default_login_hint_enabled);
  if (podpowiedzLogowania) {
    podpowiedzLogowania.textContent =
      "Wersja rozwojowa tworzy konto WĹ‚aĹ›ciciela systemu `admin` / `Admin1234`, jeĹ›li baza jest pusta.";
    podpowiedzLogowania.classList.toggle("hidden", !pokazPodpowiedzLogowania);
  }
  renderujSzybkieLogowaniaDemo();
}

function pobierzSzybkieLogowaniaDemo() {
  if (!Array.isArray(stan.meta?.quick_login_presets)) {
    return [];
  }
  return stan.meta.quick_login_presets.filter(
    (item) => item && String(item.login || "").trim() && String(item.password || "").trim()
  );
}

function renderujSzybkieLogowaniaDemo() {
  const sekcja = document.getElementById("quick-login-section");
  const kontener = document.getElementById("quick-login-buttons");
  if (!sekcja || !kontener) {
    return;
  }
  const szybkieKonta = pobierzSzybkieLogowaniaDemo();
  if (!szybkieKonta.length) {
    sekcja.classList.add("hidden");
    kontener.innerHTML = "";
    return;
  }
  kontener.innerHTML = szybkieKonta
    .map((konto, index) => {
      const meta = [konto.login, konto.role ? formatujRole(konto.role) : "", konto.organization_name || ""]
        .filter(Boolean)
        .join(" Â· ");
      return `
        <button type="button" class="auth-quick-login-button" data-quick-login-index="${index}">
          <strong>${bezpiecznyTekst(konto.display_name || konto.login)}</strong>
          <span class="auth-quick-login-meta">${bezpiecznyTekst(meta)}</span>
        </button>
      `;
    })
    .join("");
  sekcja.classList.remove("hidden");
}

function pobierzElementyKaruzeliModulow() {
  return {
    shell: document.getElementById("nav-carousel-shell"),
    track: document.getElementById("nav-carousel-track"),
    previousButton: document.getElementById("nav-carousel-prev"),
    nextButton: document.getElementById("nav-carousel-next"),
    progressBar: document.getElementById("nav-carousel-progress-bar"),
  };
}

function odswiezKaruzeleModulow() {
  const { shell, track, previousButton, nextButton, progressBar } = pobierzElementyKaruzeliModulow();
  if (!shell || !track) {
    return;
  }

  const maxScroll = Math.max(0, shell.scrollWidth - shell.clientWidth);
  const scrollLeft = Math.max(0, Math.min(maxScroll, shell.scrollLeft));
  const hasOverflow = maxScroll > 8;
  const visibleRatio = hasOverflow ? Math.max(0.18, shell.clientWidth / Math.max(shell.scrollWidth, 1)) : 1;
  const progressWidth = Math.max(18, Math.min(100, visibleRatio * 100));
  const progressShift = hasOverflow ? (scrollLeft / maxScroll) * (100 - progressWidth) : 0;

  shell.classList.toggle("is-static", !hasOverflow);
  if (previousButton) {
    previousButton.disabled = !hasOverflow || scrollLeft <= 4;
  }
  if (nextButton) {
    nextButton.disabled = !hasOverflow || scrollLeft >= maxScroll - 4;
  }
  if (progressBar) {
    progressBar.style.width = `${progressWidth}%`;
    progressBar.style.transform = `translateX(${progressShift}%)`;
  }
}

function przewinKaruzeleModulow(kierunek = 1) {
  const { shell } = pobierzElementyKaruzeliModulow();
  if (!shell) {
    return;
  }
  const distance = Math.max(220, Math.round(shell.clientWidth * 0.78)) * kierunek;
  shell.scrollBy({ left: distance, behavior: "smooth" });
}

function ustawInformacjeSystemowe() {
  const etykietaBazy = stan.meta?.database_label || "nieznana";
  const releaseId = String(stan.meta?.app_release_id || "brak");
  const statusTelegrama = stan.meta?.telegram_enabled ? "Telegram: aktywny." : "Telegram: wylaczony.";
  const statusSlacka = stan.meta?.slack_enabled ? "Slack: aktywny." : "Slack: wylaczony.";
  const statusOcr =
    stan.meta?.ocr_mode === "tesseract"
      ? "OCR: lokalny silnik aktywny."
      : "OCR: tryb awaryjny bez lokalnego silnika.";
  const statusImportuTestowego = czyImportTestowyWlaczony() ? "Import testowy: dostepny." : "Import testowy: wylaczony.";
  document.getElementById("system-info").textContent = `Wersja: ${releaseId}. Aktywna baza danych: ${etykietaBazy}. ${statusTelegrama} ${statusSlacka} ${statusOcr} ${statusImportuTestowego}`;
  document.getElementById("sidebar-system-info").textContent =
    `Wersja: ${releaseId}. Baza: ${etykietaBazy}. ${statusTelegrama} ${statusSlacka} ${statusOcr} Dokumenty i pliki OCR sa ukladane w osobnych folderach organizacji.`;
}
function odswiezPasekSesji() {
  const navUsers = document.querySelectorAll('[data-view="users"], [data-launch-view="users"]');
  const navOrganizations = document.querySelectorAll('[data-view="organizations"], [data-launch-view="organizations"]');
  const navEmailCenter = document.querySelectorAll('[data-view="email-center"], [data-launch-view="email-center"]');
  const navTasks = document.querySelectorAll('[data-view="tasks"], [data-launch-view="tasks"]');
  const navSupport = document.querySelectorAll('[data-view="support"], [data-launch-view="support"]');
  const navInbox = document.querySelectorAll('[data-view="inbox"], [data-launch-view="inbox"]');
  const navViews = document.querySelectorAll('[data-view="views"], [data-launch-view="views"]');
  const navAutomation = document.querySelectorAll('[data-view="automation"], [data-launch-view="automation"]');
  const navHealth = document.querySelectorAll('[data-view="health"], [data-launch-view="health"]');
  odswiezOpcjeWidokowFokusuZadan();
  const sekcjaImportu = znajdzSekcjeImportuTestowego();
  if (sekcjaImportu) {
    sekcjaImportu.classList.toggle("hidden", !czyImportTestowyWlaczony());
  }
  if (!stan.biezacyUzytkownik) {
    stan.profilMenuOtwarte = false;
    stan.menuWiecejOtwarte = false;
    navUsers.forEach((button) => button.classList.add("hidden"));
    navOrganizations.forEach((button) => button.classList.add("hidden"));
    navEmailCenter.forEach((button) => button.classList.add("hidden"));
    navTasks.forEach((button) => button.classList.add("hidden"));
    navSupport.forEach((button) => button.classList.add("hidden"));
    navInbox.forEach((button) => button.classList.add("hidden"));
    navViews.forEach((button) => button.classList.add("hidden"));
    navAutomation.forEach((button) => button.classList.add("hidden"));
    navHealth.forEach((button) => button.classList.add("hidden"));
    renderujMenuNaglowka();
    ustawMotywKontekstuInterfejsu();
    renderujSzybkiKalendarz();
    renderujPanelMojejPracy();
    renderujStatusPrzypomnien();
    odswiezKaruzeleModulow();
    return;
  }

  document.getElementById("session-user-name").textContent =
    stan.biezacyUzytkownik.display_name || stan.biezacyUzytkownik.login;
  document.getElementById("session-user-role").textContent = formatujRole(stan.biezacyUzytkownik.role);
  document.getElementById("session-user-organization").textContent = czyGlobalnyAdministrator()
    ? "Konto wlasciciela systemu"
    : `Organizacja: ${stan.biezacyUzytkownik.organization_name || "brak przypisania"}`;
  navUsers.forEach((button) => button.classList.toggle("hidden", !czyMoznaZarzadzacUzytkownikami()));
  navOrganizations.forEach((button) => button.classList.toggle("hidden", !czyMoznaZarzadzacOrganizacjami()));
  navEmailCenter.forEach((button) => button.classList.toggle("hidden", !czyMoznaOtworzycCentrumEmaila()));
  navTasks.forEach((button) => button.classList.toggle("hidden", !czyMoznaOtworzycAsystentaSzefa()));
  navSupport.forEach((button) => button.classList.toggle("hidden", false));
  navInbox.forEach((button) => button.classList.toggle("hidden", !czyMoznaZapisywac()));
  navViews.forEach((button) => button.classList.toggle("hidden", false));
  navAutomation.forEach((button) => button.classList.toggle("hidden", false));
  navHealth.forEach((button) => button.classList.toggle("hidden", false));
  if (!czyGlobalnyAdministrator()) {
    stan.menuWiecejOtwarte = false;
  }
  renderujMenuNaglowka();
  ustawMotywKontekstuInterfejsu();
  odswiezKaruzeleModulow();

  const czyTylkoPodglad = czyJestGosciem();
  document.querySelectorAll(".action-import").forEach((button) => {
    const brakWyboruOrganizacji = czyGlobalnyAdministrator() && !stan.wybranaOrganizacjaId;
    const importTestowyWylaczony = !czyImportTestowyWlaczony();
    button.disabled = importTestowyWylaczony || czyTylkoPodglad || brakWyboruOrganizacji;
    if (importTestowyWylaczony) {
      button.title = "Import testowy jest wylaczony w tym srodowisku.";
    } else if (czyTylkoPodglad) {
      button.title = "Rola GoĹ›cia nie moĹĽe dodawaÄ‡ dokumentĂłw.";
    } else if (brakWyboruOrganizacji) {
      button.title = "Wybierz konkretnÄ… organizacjÄ™ przed importem.";
    } else {
      button.title = "";
    }
    if (czyTylkoPodglad && !importTestowyWylaczony) {
      button.title = "Rola GoĹ›cia nie moĹĽe dodawaÄ‡ dokumentĂłw.";
    }
  });

  const przyciskNowegoZadania = document.getElementById("new-task-button");
  if (przyciskNowegoZadania) {
    const brakWyboruOrganizacji = czyGlobalnyAdministrator() && !stan.wybranaOrganizacjaId;
    const brakDostepuDoWorkspace = !czyMoznaKorzystacZMojejPracy();
    przyciskNowegoZadania.disabled = czyTylkoPodglad || brakWyboruOrganizacji || brakDostepuDoWorkspace;
    if (czyTylkoPodglad) {
      przyciskNowegoZadania.title = "Rola GoĹ›cia nie moĹĽe dodawaÄ‡ zadaĹ„.";
    } else if (brakWyboruOrganizacji) {
      przyciskNowegoZadania.title = "Wybierz konkretna organizacje przed dodaniem zadania.";
    } else if (brakDostepuDoWorkspace) {
      przyciskNowegoZadania.title = "Sekcja Moja praca jest dostepna dopiero po wlaczeniu modulu Asystent Szefa.";
    } else {
      przyciskNowegoZadania.title = "";
    }
    if (czyTylkoPodglad) {
      przyciskNowegoZadania.title = "Rola GoĹ›cia nie moĹĽe dodawaÄ‡ zadaĹ„.";
    }
  }

  odswiezStanBazyWiedzy();
  renderujPanelMojejPracy();
  renderujSzybkiKalendarz();
  odswiezUprawnieniaFormularzaOrganizacji();

  if (
    (stan.aktywnyWidok === "users" && !czyMoznaZarzadzacUzytkownikami()) ||
    (stan.aktywnyWidok === "organizations" && !czyMoznaZarzadzacOrganizacjami()) ||
    (stan.aktywnyWidok === "email-center" && !czyMoznaOtworzycCentrumEmaila()) ||
    (stan.aktywnyWidok === "tasks" && !czyMoznaOtworzycAsystentaSzefa() && !czyMoznaKorzystacZMojejPracy()) ||
    (stan.aktywnyWidok === "inbox" && !czyMoznaZapisywac()) ||
    !stan.biezacyUzytkownik
  ) {
    ustawWidok(stan.aktywnyWidok === "inbox" ? "support" : czyMoznaCzytacBazeWiedzy() ? "knowledge" : "dashboard");
  }

  odswiezStanModuluRozliczen();
  renderujStatusPrzypomnien();
  renderujSzybkiPanelPracy();
}

function renderujChipyMapyRozliczen(items) {
  if (!Array.isArray(items) || !items.length) {
    return `<div class="billing-roadmap-empty">Jeszcze nie ma danych podgladowych w tym obszarze.</div>`;
  }
  return `
    <div class="billing-roadmap-preview">
      ${items.map((item) => `<span class="billing-roadmap-chip">${bezpiecznyTekst(item)}</span>`).join("")}
    </div>
  `;
}

function renderujMapeModuluRozliczen() {
  const container = document.getElementById("billing-roadmap-grid");
  if (!container) {
    return;
  }

  const czyZalogowany = Boolean(stan.biezacyUzytkownik);
  const ostatniaWidocznaWplata = stan.uczniowieRozliczen.find(
    (student) => student.family_last_payment_date && student.family_last_payment_amount !== null && student.family_last_payment_amount !== undefined
  );

  const cards = [
    {
      title: "Wplaty i import wyciagow",
      kind: "Rachunki + CSV + historia transakcji",
      statusLabel: "Dziala teraz",
      statusClass: "status-success",
      meta: czyZalogowany
        ? `${stan.rachunkiBankowe.length} rachunkow i ${stan.transakcjeRozliczen.length} transakcji w aktualnym zakresie.`
        : "Zaloguj sie, aby zobaczyc rachunki i transakcje.",
      description:
        "To jest dzialajaca czesc modulu. Nizej masz aktywne tabele rachunkow, import CSV oraz podsumowanie ostatniego wyciagu.",
      preview: stan.transakcjeRozliczen.slice(0, 3).map((item) => {
        const label = item.title || item.counterparty_name || "Wplata";
        return `${formatujKwote(item.amount, item.currency)} | ${label}`;
      }),
    },
    {
      title: "Szkoly",
      kind: "Lista szkol i skrotow",
      statusLabel: "Dziala teraz",
      statusClass: "status-success",
      meta: czyZalogowany
        ? `Tabela szkol, skroty i liczba uczniow sa juz widoczne. W bazie teraz: ${stan.szkolyRozliczen.length}.`
        : "Po zalogowaniu zobaczysz, ile szkol jest juz w bazie.",
      description: "Masz juz osobna liste placowek z pelna nazwa, skrotem typu SP4 BP i gotowym miejscem na dalsze filtrowanie uczniow.",
      preview: stan.szkolyRozliczen.slice(0, 3).map((item) => `${item.short_name || "Skrot"} | ${item.city || "miasto"}`),
    },
    {
      title: "Rodziny i platnicy",
      kind: "Lista rodzin z telefonem i ulgami",
      statusLabel: "Dziala teraz",
      statusClass: "status-success",
      meta: czyZalogowany
        ? `Tabela rodzin z numerem telefonu, KDR, liczbami dzieci i saldem jest juz widoczna. W bazie teraz: ${stan.platnicyRozliczen.length}.`
        : "Po zalogowaniu zobaczysz rodziny i platnikow z aktualnej organizacji.",
      description:
        "To jest juz centrum dla przelewow rodzinnych, kiedy jeden numer telefonu oplaca jedno albo kilka dzieci.",
      preview: stan.platnicyRozliczen.slice(0, 3).map((item) => {
        const kdr = item.has_large_family_card ? "KDR" : "bez KDR";
        return `${item.display_name || "Rodzina"} | ${item.contact_phone || "-"} | ${kdr}`;
      }),
    },
    {
      title: "Uczniowie",
      kind: "Glowna lista dzieci do pracy operacyjnej",
      statusLabel: "Dziala teraz",
      statusClass: "status-success",
      meta: czyZalogowany
        ? `Widok po dziecku jest juz gotowy: szkola, model, telefon rodziny, ostatnia wplata i saldo rodzinne. W bazie teraz: ${stan.uczniowieRozliczen.length}.`
        : "Po zalogowaniu zobaczysz uczniow i ostatnie wplaty rodzinne.",
      description:
        "To jest juz glowny widok roboczy, bo pracujesz po dziecku, a nie po rodzicu. Numer telefonu rodzica zostaje obok jako kontekst.",
      preview: stan.uczniowieRozliczen.slice(0, 3).map((item) => {
        const szkola = item.school_short_name || "bez szkoly";
        const wplata = item.family_last_payment_amount
          ? `${formatujKwote(item.family_last_payment_amount, item.family_last_payment_currency || "PLN")} / ${item.family_last_payment_date || "-"}`
          : "bez wplaty";
        return `${item.full_name || "Uczen"} | ${szkola} | ${wplata}`;
      }),
    },
    {
      title: "Modele rozliczen",
      kind: "Konfigurator roku szkolnego i dnia tygodnia",
      statusLabel: "Dziala teraz",
      statusClass: "status-success",
      meta: czyZalogowany
        ? `Szablony typu 26/27 Wtorek, 26/27 Piatek i wlasne modele sa juz w module. W bazie teraz: ${stan.modeleRozliczen.length}.`
        : "Po zalogowaniu zobaczysz liczbe gotowych modeli rozliczen.",
      description:
        "Tutaj jest juz konfiguracja roku szkolnego, stawek miesiecznych i semestralnych, KDR, rodzenstwa oraz darmowego startu.",
      preview: stan.modeleRozliczen.slice(0, 3).map((item) => {
        return `${item.name || "Model"} | ${formatujKwote(item.monthly_rate_amount)} mies. | ${formatujKwote(item.semester_rate_amount)} sem.`;
      }),
    },
    {
      title: "Naleznosci",
      kind: "Tabela rat, semestrow i ulg",
      statusLabel: "Dziala teraz",
      statusClass: "status-success",
      meta: czyZalogowany
        ? `Generator naleznosci i tabela kwot do zaplaty sa juz gotowe. W bazie teraz: ${stan.naleznosciRozliczen.length}.`
        : "Po zalogowaniu zobaczysz wygenerowane naleznosci z modeli rozliczen.",
      description:
        "Tutaj masz juz glowna tabele kwot do zaplaty, z rozpisaniem pierwszych darmowych zajec, rodzenstwa i KDR.",
      preview: stan.naleznosciRozliczen.slice(0, 3).map((item) => {
        return `${item.student_full_name || "Uczen"} | ${item.period_label || "-"} | ${formatujKwote(item.total_amount)}`;
      }),
    },
    {
      title: "Saldo i ksiega",
      kind: "Ledger rodzinny i historia zmian",
      statusLabel: "Dziala teraz",
      statusClass: "status-success",
      meta: czyZalogowany
        ? `Masz juz salda rodzin, wpisy ledgerowe i dopasowania platnosci. Salda z zalegloscia: ${stan.billingLedgerBalances.filter((item) => Number(item.balance_due || 0) > 0).length}.`
        : "Po zalogowaniu zobaczysz salda rodzin i historie dopasowan.",
      description:
        "To jest juz finansowy slad systemu: naliczenia podnosza saldo, dopasowane wplaty je obnizaja.",
      preview: stan.billingLedgerBalances.slice(0, 3).map((item) => {
        return `${item.display_name || "Rodzina"} | saldo ${formatujKwote(item.balance_due || 0)}`;
      }),
    },
    {
      title: "Umowy i podpisy",
      kind: "Generator umowy i podpis rodzica",
      statusLabel: "Jeszcze nie wdrozone",
      statusClass: "status-normal",
      meta: "Forma: generator umowy, wybor modelu, sposobu platnosci, telefonu i dzieci pod jedna rodzina.",
      description:
        "To miejsce bedzie odpowiadalo za dokument umowy i proces podpisu elektronicznego. Na razie pokazujemy tylko docelowy slot w module.",
      preview: [],
      planned: true,
    },
    {
      title: "Formularz zgloszeniowy",
      kind: "Publiczne zapisy na zajecia dzieci",
      statusLabel: "Jeszcze nie wdrozone",
      statusClass: "status-normal",
      meta: "Forma: formularz online -> skrzynka zgloszen -> utworzenie ucznia i rodziny po numerze telefonu.",
      description:
        "Docelowo nowe zapisy nie beda omijaly systemu. Zgloszenie trafi najpierw do aplikacji, a potem jednym ruchem utworzy ucznia, rodzine i kontekst rozliczen.",
      preview: [],
      planned: true,
    },
    {
      title: "Rozksiegowanie wplat rodzinnych",
      kind: "Jedna wplata, wiele dzieci",
      statusLabel: "Czesciowo wdrozone",
      statusClass: "status-warning",
      meta: "Forma: reczne dopasowanie do platnika i konkretnej naleznosci, a pozniej dedykowany ekran propozycji podzialu.",
      description:
        "Masz juz pierwszy etap: jedna transakcja moze byc recznie dopasowana do wybranej naleznosci. Docelowo dojdzie osobny ekran z propozycjami podzialu.",
      preview: ostatniaWidocznaWplata
        ? [
            `${ostatniaWidocznaWplata.payer_label || "Rodzina"} | ostatnia wplata ${formatujKwote(
              ostatniaWidocznaWplata.family_last_payment_amount,
              ostatniaWidocznaWplata.family_last_payment_currency || "PLN"
            )}`,
          ]
        : [],
      planned: true,
    },
    {
      title: "Raport zaleglosci",
      kind: "Lista sald, zaleglosci i terminow",
      statusLabel: "Dziala teraz",
      statusClass: "status-success",
      meta: "Forma: rodzinny raport sald, zaleglosci i terminow. Raport per dziecko dojdzie po pelnym rozksiegowaniu.",
      description:
        "Szybki widok kto zalega, na jaka kwote i kiedy ostatnio zaplacil jest juz w module. Widok per dziecko dojdzie, gdy kazda wplata bedzie w pelni rozksiegowana.",
      preview: [],
    },
    {
      title: "Obecnosc",
      kind: "Osobny modul, nie mieszany z finansami",
      statusLabel: "Osobny modul",
      statusClass: "status-normal",
      meta: "Forma: oddzielna zakladka spieta z uczniami i harmonogramem.",
      description:
        "Celowo zostawiamy to poza ta zakladka, zeby rozliczenia zostaly czytelne, a obecnosci mialy wlasne miejsce operacyjne.",
      preview: [],
      planned: true,
    },
  ];

  container.innerHTML = cards
    .map(
      (card) => `
        <article class="billing-roadmap-card${card.planned ? " is-planned" : ""}">
          <div class="billing-roadmap-top">
            <div class="billing-roadmap-title">
              <span class="billing-roadmap-kind">${bezpiecznyTekst(card.kind)}</span>
              <h4>${bezpiecznyTekst(card.title)}</h4>
            </div>
            <span class="status-badge ${card.statusClass}">${bezpiecznyTekst(card.statusLabel)}</span>
          </div>
          <div class="billing-roadmap-meta">${bezpiecznyTekst(card.meta)}</div>
          <div class="billing-roadmap-meta">${bezpiecznyTekst(card.description)}</div>
          ${renderujChipyMapyRozliczen(card.preview)}
        </article>
      `
    )
    .join("");
}

function formatujTrybRozliczenBilling(value) {
  const normalized = String(value || "").trim().toLowerCase();
  if (normalized === "monthly") return "miesieczny";
  if (normalized === "semester") return "semestralny";
  if (normalized === "custom") return "wlasny";
  return normalized || "-";
}

function policzUczniowNaPlatnika() {
  const result = new Map();
  (Array.isArray(stan.uczniowieRozliczen) ? stan.uczniowieRozliczen : []).forEach((student) => {
    const payerId = Number(student.billing_payer_id || 0);
    result.set(payerId, (result.get(payerId) || 0) + 1);
  });
  return result;
}

function policzUczniowNaSzkole() {
  const result = new Map();
  (Array.isArray(stan.uczniowieRozliczen) ? stan.uczniowieRozliczen : []).forEach((student) => {
    const schoolId = Number(student.billing_school_id || 0);
    if (!schoolId) return;
    result.set(schoolId, (result.get(schoolId) || 0) + 1);
  });
  return result;
}

function policzUczniowNaModelu() {
  const result = new Map();
  (Array.isArray(stan.uczniowieRozliczen) ? stan.uczniowieRozliczen : []).forEach((student) => {
    const modelId = Number(student.billing_model_id || 0);
    if (!modelId) return;
    result.set(modelId, (result.get(modelId) || 0) + 1);
  });
  return result;
}

function policzDopasowaniaNaNaleznosci() {
  const result = new Map();
  (Array.isArray(stan.billingPaymentMatches) ? stan.billingPaymentMatches : []).forEach((match) => {
    const chargeId = Number(match.billing_charge_id || 0);
    if (!chargeId) return;
    result.set(chargeId, (result.get(chargeId) || 0) + Number(match.matched_amount || 0));
  });
  return result;
}

function policzDopasowaniaNaTransakcji() {
  const result = new Map();
  (Array.isArray(stan.billingPaymentMatches) ? stan.billingPaymentMatches : []).forEach((match) => {
    const transactionId = Number(match.billing_transaction_id || 0);
    if (!transactionId) return;
    result.set(transactionId, (result.get(transactionId) || 0) + Number(match.matched_amount || 0));
  });
  return result;
}

function obliczPozostalaKwoteNaleznosci(charge, matchedByChargeId = policzDopasowaniaNaNaleznosci()) {
  const chargeId = Number(charge?.billing_charge_id || 0);
  const totalAmount = Number(charge?.total_amount || 0);
  const matchedAmount = chargeId ? Number(matchedByChargeId.get(chargeId) || 0) : 0;
  return Math.max(0, Number((totalAmount - matchedAmount).toFixed(2)));
}

function obliczPozostalaKwoteTransakcji(transactionId, matchedByTransactionId = policzDopasowaniaNaTransakcji()) {
  const transaction = (Array.isArray(stan.transakcjeRozliczen) ? stan.transakcjeRozliczen : []).find(
    (item) => Number(item.billing_transaction_id) === Number(transactionId)
  );
  if (!transaction) {
    return 0;
  }
  const totalAmount = Math.abs(Number(transaction.amount || 0));
  const matchedAmount = Number(matchedByTransactionId.get(Number(transactionId)) || 0);
  return Math.max(0, Number((totalAmount - matchedAmount).toFixed(2)));
}

function pobierzOtwarteNaleznosciPlatnika(billingPayerId) {
  const matchedByChargeId = policzDopasowaniaNaNaleznosci();
  return (Array.isArray(stan.naleznosciRozliczen) ? stan.naleznosciRozliczen : [])
    .filter((charge) => Number(charge.billing_payer_id) === Number(billingPayerId))
    .map((charge) => ({
      ...charge,
      remaining_amount: obliczPozostalaKwoteNaleznosci(charge, matchedByChargeId),
    }))
    .filter((charge) => Number(charge.remaining_amount || 0) > 0)
    .sort((left, right) => {
      const leftDue = String(left.due_date || "");
      const rightDue = String(right.due_date || "");
      if (leftDue !== rightDue) {
        return leftDue.localeCompare(rightDue);
      }
      return String(left.student_full_name || "").localeCompare(String(right.student_full_name || ""));
    });
}

function renderujPodsumowanieRozliczen() {
  const root = document.getElementById("billing-summary-grid");
  if (!root) {
    return;
  }
  if (!stan.biezacyUzytkownik) {
    root.innerHTML = `
      <div class="summary-item"><strong>Status</strong><div>Zaloguj sie, aby pracowac z rozliczeniami.</div></div>
    `;
    return;
  }

  const balances = Array.isArray(stan.billingLedgerBalances) ? stan.billingLedgerBalances : [];
  const charges = Array.isArray(stan.naleznosciRozliczen) ? stan.naleznosciRozliczen : [];
  const transactions = Array.isArray(stan.transakcjeRozliczen) ? stan.transakcjeRozliczen : [];
  const matchedByChargeId = policzDopasowaniaNaNaleznosci();
  const openChargesTotal = charges.reduce(
    (sum, charge) => sum + obliczPozostalaKwoteNaleznosci(charge, matchedByChargeId),
    0
  );
  const overdueBalances = balances.filter((item) => Number(item.balance_due || 0) > 0);
  const unmatchedTransactions = transactions.filter((item) => String(item.matched_status || "") === "nieprzypisana");
  const partiallyMatchedTransactions = transactions.filter(
    (item) => String(item.matched_status || "") === "czesciowo_rozliczona"
  );

  root.innerHTML = `
    <div class="summary-item"><strong>Uczniowie</strong><div>${formatujWartosc(stan.uczniowieRozliczen.length)}</div></div>
    <div class="summary-item"><strong>Rodziny</strong><div>${formatujWartosc(stan.platnicyRozliczen.length)}</div></div>
    <div class="summary-item"><strong>Szkoly</strong><div>${formatujWartosc(stan.szkolyRozliczen.length)}</div></div>
    <div class="summary-item"><strong>Modele</strong><div>${formatujWartosc(stan.modeleRozliczen.length)}</div></div>
    <div class="summary-item"><strong>Otwarte naleznosci</strong><div>${formatujKwote(openChargesTotal)}</div></div>
    <div class="summary-item"><strong>Platnicy z zalegloscia</strong><div>${formatujWartosc(overdueBalances.length)}</div></div>
    <div class="summary-item"><strong>Nieprzypisane wplaty</strong><div>${formatujWartosc(unmatchedTransactions.length)}</div></div>
    <div class="summary-item"><strong>Czesciowo rozliczone</strong><div>${formatujWartosc(partiallyMatchedTransactions.length)}</div></div>
  `;
}

function renderujSzkolyRozliczen() {
  const body = document.getElementById("billing-school-table-body");
  const count = document.getElementById("billing-school-count");
  if (!body || !count) {
    return;
  }
  const schools = Array.isArray(stan.szkolyRozliczen) ? stan.szkolyRozliczen : [];
  const studentsBySchool = policzUczniowNaSzkole();
  count.textContent = `${schools.length} szkol`;
  if (!stan.biezacyUzytkownik) {
    body.innerHTML = `<tr><td colspan="5">Zaloguj sie, aby zobaczyc szkoly.</td></tr>`;
    return;
  }
  if (!schools.length) {
    body.innerHTML = `<tr><td colspan="5">Brak szkol dla wybranej organizacji.</td></tr>`;
    return;
  }
  body.innerHTML = schools
    .map(
      (school) => `
        <tr class="clickable" data-billing-school-id="${school.billing_school_id}">
          <td data-label="Skrot">${formatujWartosc(school.short_name)}</td>
          <td data-label="Pelna nazwa">${formatujWartosc(school.full_name)}</td>
          <td data-label="Miasto">${formatujWartosc(school.city || "-")}</td>
          <td data-label="Uczniowie">${formatujWartosc(studentsBySchool.get(Number(school.billing_school_id)) || 0)}</td>
          <td data-label="Aktywna">${school.is_active ? '<span class="status-badge status-success">tak</span>' : '<span class="status-badge status-danger">nie</span>'}</td>
        </tr>
      `
    )
    .join("");
  body.querySelectorAll("[data-billing-school-id]").forEach((row) => {
    row.addEventListener("click", () => {
      const schoolSelect = document.getElementById("billing-student-school-id");
      if (schoolSelect) {
        schoolSelect.value = row.dataset.billingSchoolId || "";
      }
    });
  });
}

function renderujPlatnikowRozliczen() {
  const body = document.getElementById("billing-payer-table-body");
  const count = document.getElementById("billing-payer-count");
  if (!body || !count) {
    return;
  }
  const payers = Array.isArray(stan.platnicyRozliczen) ? stan.platnicyRozliczen : [];
  const studentsByPayer = policzUczniowNaPlatnika();
  count.textContent = `${payers.length} rodzin`;
  if (!stan.biezacyUzytkownik) {
    body.innerHTML = `<tr><td colspan="8">Zaloguj sie, aby zobaczyc rodziny.</td></tr>`;
    return;
  }
  if (!payers.length) {
    body.innerHTML = `<tr><td colspan="8">Brak rodzin dla wybranej organizacji.</td></tr>`;
    return;
  }
  body.innerHTML = payers
    .map(
      (payer) => `
        <tr class="clickable" data-billing-payer-id="${payer.billing_payer_id}">
          <td data-label="Rodzina">${formatujWartosc(payer.display_name || payer.payer_label || "-")}</td>
          <td data-label="Telefon">${formatujWartosc(payer.contact_phone)}</td>
          <td data-label="Dzieci">${formatujWartosc(studentsByPayer.get(Number(payer.billing_payer_id)) || 0)}</td>
          <td data-label="KDR">${payer.has_large_family_card ? '<span class="status-badge status-success">tak</span>' : '<span class="status-badge status-normal">nie</span>'}</td>
          <td data-label="Naliczone">${formatujKwote(payer.billing_total_charges || 0)}</td>
          <td data-label="Rozliczone">${formatujKwote(payer.billing_total_matches || 0)}</td>
          <td data-label="Saldo"><span class="status-badge ${Number(payer.billing_balance_due || 0) > 0 ? "status-warning" : "status-success"}">${formatujKwote(payer.billing_balance_due || 0)}</span></td>
          <td data-label="Ostatnia wplata">${payer.billing_last_payment_at ? `${formatujDateCzas(payer.billing_last_payment_at)}<div class="muted">${formatujKwote(payer.billing_last_payment_amount || 0, payer.billing_last_payment_currency || "PLN")}</div>` : "Brak dopasowanej wplaty"}</td>
        </tr>
      `
    )
    .join("");
  body.querySelectorAll("[data-billing-payer-id]").forEach((row) => {
    row.addEventListener("click", () => {
      const payerId = row.dataset.billingPayerId || "";
      const studentPayerSelect = document.getElementById("billing-student-payer-id");
      const matchPayerSelect = document.getElementById("billing-match-payer-id");
      if (studentPayerSelect) {
        studentPayerSelect.value = payerId;
      }
      if (matchPayerSelect) {
        matchPayerSelect.value = payerId;
      }
      odswiezPowiazanieRodzinyWUczniu({ source: "payer" });
      zbudujOpcjeNaleznosciDoDopasowania();
      odswiezPomocDopasowaniaPlatnosci();
    });
  });
}

function renderujUczniowRozliczen() {
  const body = document.getElementById("billing-student-table-body");
  const count = document.getElementById("billing-student-count");
  if (!body || !count) {
    return;
  }
  const students = Array.isArray(stan.uczniowieRozliczen) ? stan.uczniowieRozliczen : [];
  count.textContent = `${students.length} uczniow`;
  if (!stan.biezacyUzytkownik) {
    body.innerHTML = `<tr><td colspan="8">Zaloguj sie, aby zobaczyc uczniow.</td></tr>`;
    return;
  }
  if (!students.length) {
    body.innerHTML = `<tr><td colspan="8">Brak uczniow dla wybranej organizacji.</td></tr>`;
    return;
  }
  body.innerHTML = students
    .map(
      (student) => `
        <tr class="clickable" data-billing-student-id="${student.billing_student_id}" data-billing-payer-id="${student.billing_payer_id}">
          <td data-label="Uczen">${formatujWartosc(student.full_name)}</td>
          <td data-label="Szkola">${formatujWartosc(student.school_short_name || student.school_full_name || "-")}</td>
          <td data-label="Model">${formatujWartosc(student.model_name || "-")}</td>
          <td data-label="Dzien">${formatujWartosc(student.lesson_day || student.model_lesson_day || "-")}</td>
          <td data-label="Grupa">${formatujWartosc(student.group_name || "-")}</td>
          <td data-label="Rodzina">${formatujWartosc(student.payer_label || student.payer_display_name || "-")}<div class="muted">${formatujWartosc(student.payer_contact_phone || "-")}</div></td>
          <td data-label="Ostatnia wplata rodziny">${student.family_last_payment_date ? `${formatujDateCzas(student.family_last_payment_date)}<div class="muted">${formatujKwote(student.family_last_payment_amount || 0, student.family_last_payment_currency || "PLN")}</div>` : "Brak dopasowanej wplaty"}</td>
          <td data-label="Saldo rodziny"><span class="status-badge ${Number(student.family_balance_due || 0) > 0 ? "status-warning" : "status-success"}">${formatujKwote(student.family_balance_due || 0)}</span></td>
        </tr>
      `
    )
    .join("");
  body.querySelectorAll("[data-billing-student-id]").forEach((row) => {
    row.addEventListener("click", () => {
      const payerId = row.dataset.billingPayerId || "";
      const matchPayerSelect = document.getElementById("billing-match-payer-id");
      if (matchPayerSelect) {
        matchPayerSelect.value = payerId;
      }
      zbudujOpcjeNaleznosciDoDopasowania();
      odswiezPomocDopasowaniaPlatnosci();
    });
  });
}

function renderujModeleRozliczen() {
  const body = document.getElementById("billing-model-table-body");
  const count = document.getElementById("billing-model-count");
  if (!body || !count) {
    return;
  }
  const models = Array.isArray(stan.modeleRozliczen) ? stan.modeleRozliczen : [];
  const studentsByModel = policzUczniowNaModelu();
  count.textContent = `${models.length} modeli`;
  if (!stan.biezacyUzytkownik) {
    body.innerHTML = `<tr><td colspan="11">Zaloguj sie, aby zobaczyc modele rozliczen.</td></tr>`;
    return;
  }
  if (!models.length) {
    body.innerHTML = `<tr><td colspan="11">Brak modeli rozliczen dla wybranej organizacji.</td></tr>`;
    return;
  }
  body.innerHTML = models
    .map(
      (model) => `
        <tr class="clickable" data-billing-model-id="${model.billing_model_id}">
          <td data-label="Model">${formatujWartosc(model.name)}</td>
          <td data-label="Rok">${formatujWartosc(model.school_year)}</td>
          <td data-label="Dzien">${formatujWartosc(model.lesson_day || "-")}</td>
          <td data-label="Tryb">${formatujWartosc(formatujTrybRozliczenBilling(model.settlement_mode))}</td>
          <td data-label="Mies.">${model.monthly_rate_amount !== null && model.monthly_rate_amount !== undefined ? formatujKwote(model.monthly_rate_amount) : "-"}</td>
          <td data-label="Sem.">${model.semester_rate_amount !== null && model.semester_rate_amount !== undefined ? formatujKwote(model.semester_rate_amount) : "-"}</td>
          <td data-label="Rodzenstwo">${formatujKwote(model.sibling_discount_amount || 0)}</td>
          <td data-label="KDR">${formatujKwote(model.large_family_discount_amount || 0)}</td>
          <td data-label="Darmowy start">${formatujWartosc(model.intro_free_lessons_count || 0)}</td>
          <td data-label="Umowa">${model.contract_required ? '<span class="status-badge status-warning">tak</span>' : '<span class="status-badge status-normal">nie</span>'}</td>
          <td data-label="Uczniowie">${formatujWartosc(studentsByModel.get(Number(model.billing_model_id)) || 0)}</td>
        </tr>
      `
    )
    .join("");
  body.querySelectorAll("[data-billing-model-id]").forEach((row) => {
    row.addEventListener("click", () => {
      const modelId = row.dataset.billingModelId || "";
      const studentModelSelect = document.getElementById("billing-student-model-id");
      const chargeModelSelect = document.getElementById("billing-charge-model-id");
      if (studentModelSelect) {
        studentModelSelect.value = modelId;
      }
      if (chargeModelSelect) {
        chargeModelSelect.value = modelId;
      }
    });
  });
}

function renderujNaleznosciRozliczen() {
  const body = document.getElementById("billing-charge-table-body");
  const count = document.getElementById("billing-charge-count");
  const summary = document.getElementById("billing-charge-total-summary");
  if (!body || !count || !summary) {
    return;
  }
  const charges = Array.isArray(stan.naleznosciRozliczen) ? stan.naleznosciRozliczen : [];
  const matchedByChargeId = policzDopasowaniaNaNaleznosci();
  const openTotal = charges.reduce((sum, charge) => sum + obliczPozostalaKwoteNaleznosci(charge, matchedByChargeId), 0);
  count.textContent = `${charges.length} naleznosci`;
  summary.textContent = stan.biezacyUzytkownik
    ? `Otwarte do rozliczenia: ${formatujKwote(openTotal)}. Kwota pokazuje, ile jeszcze zostalo po recznych albo automatycznych dopasowaniach.`
    : "";
  if (!stan.biezacyUzytkownik) {
    body.innerHTML = `<tr><td colspan="9">Zaloguj sie, aby zobaczyc naleznosci.</td></tr>`;
    return;
  }
  if (!charges.length) {
    body.innerHTML = `<tr><td colspan="9">Brak wygenerowanych naleznosci.</td></tr>`;
    return;
  }
  body.innerHTML = charges
    .map((charge) => {
      const remainingAmount = obliczPozostalaKwoteNaleznosci(charge, matchedByChargeId);
      const discounts = [];
      if (Number(charge.intro_free_discount_amount || 0) > 0) discounts.push(`start ${formatujKwote(charge.intro_free_discount_amount)}`);
      if (Number(charge.sibling_discount_amount || 0) > 0) discounts.push(`rodzenstwo ${formatujKwote(charge.sibling_discount_amount)}`);
      if (Number(charge.large_family_discount_amount || 0) > 0) discounts.push(`KDR ${formatujKwote(charge.large_family_discount_amount)}`);
      return `
        <tr class="clickable" data-billing-charge-id="${charge.billing_charge_id}" data-billing-payer-id="${charge.billing_payer_id}">
          <td data-label="Termin">${formatujWartosc(charge.due_date)}</td>
          <td data-label="Okres">${formatujWartosc(charge.period_label)}</td>
          <td data-label="Uczen">${formatujWartosc(charge.student_full_name)}</td>
          <td data-label="Rodzina">${formatujWartosc(charge.payer_display_name || "-")}</td>
          <td data-label="Model">${formatujWartosc(charge.model_name || "-")}</td>
          <td data-label="Zajec">${formatujWartosc(charge.lesson_count || 0)}</td>
          <td data-label="Bazowa">${formatujKwote(charge.base_amount || 0)}</td>
          <td data-label="Ulgi">${discounts.length ? discounts.join(" | ") : "brak"}</td>
          <td data-label="Do zaplaty"><span class="status-badge ${remainingAmount > 0 ? "status-warning" : "status-success"}">${formatujKwote(remainingAmount)}</span><div class="muted">pelna kwota: ${formatujKwote(charge.total_amount || 0)}</div></td>
        </tr>
      `;
    })
    .join("");
  body.querySelectorAll("[data-billing-charge-id]").forEach((row) => {
    row.addEventListener("click", () => {
      const payerSelect = document.getElementById("billing-match-payer-id");
      const chargeSelect = document.getElementById("billing-match-charge-id");
      if (payerSelect) {
        payerSelect.value = row.dataset.billingPayerId || "";
      }
      zbudujOpcjeNaleznosciDoDopasowania();
      if (chargeSelect) {
        chargeSelect.value = row.dataset.billingChargeId || "";
      }
      odswiezPomocDopasowaniaPlatnosci({ ustawDomyslnaKwote: true });
    });
  });
}

function renderujRaportZaleglosci() {
  const body = document.getElementById("billing-overdue-table-body");
  const count = document.getElementById("billing-overdue-count");
  if (!body || !count) {
    return;
  }
  const balances = (Array.isArray(stan.billingLedgerBalances) ? stan.billingLedgerBalances : []).filter(
    (row) => Number(row.balance_due || 0) > 0
  );
  const studentsByPayer = policzUczniowNaPlatnika();
  count.textContent = `${balances.length} zaleglosci`;
  if (!stan.biezacyUzytkownik) {
    body.innerHTML = `<tr><td colspan="6">Zaloguj sie, aby zobaczyc raport zaleglosci.</td></tr>`;
    return;
  }
  if (!balances.length) {
    body.innerHTML = `<tr><td colspan="6">Brak zaleglosci w aktualnym zakresie.</td></tr>`;
    return;
  }
  body.innerHTML = balances
    .map(
      (balance) => `
        <tr class="clickable" data-billing-payer-id="${balance.billing_payer_id}">
          <td data-label="Rodzina">${formatujWartosc(balance.display_name || "-")}</td>
          <td data-label="Telefon">${formatujWartosc(balance.contact_phone || "-")}</td>
          <td data-label="Dzieci">${formatujWartosc(studentsByPayer.get(Number(balance.billing_payer_id)) || 0)}</td>
          <td data-label="Saldo">${formatujKwote(balance.balance_due || 0)}</td>
          <td data-label="Ostatnia wplata">${balance.last_payment_at ? `${formatujDateCzas(balance.last_payment_at)}<div class="muted">${formatujKwote(balance.last_payment_amount || 0, balance.last_payment_currency || "PLN")}</div>` : "Brak dopasowanej wplaty"}</td>
          <td data-label="Status"><span class="status-badge status-warning">zaleglosc</span></td>
        </tr>
      `
    )
    .join("");
  body.querySelectorAll("[data-billing-payer-id]").forEach((row) => {
    row.addEventListener("click", () => {
      const payerSelect = document.getElementById("billing-match-payer-id");
      if (payerSelect) {
        payerSelect.value = row.dataset.billingPayerId || "";
      }
      zbudujOpcjeNaleznosciDoDopasowania();
      odswiezPomocDopasowaniaPlatnosci();
    });
  });
}

function zbudujOpcjePlatnikowRozliczen() {
  const selects = [
    document.getElementById("billing-student-payer-id"),
    document.getElementById("billing-match-payer-id"),
  ].filter(Boolean);
  const payers = Array.isArray(stan.platnicyRozliczen) ? stan.platnicyRozliczen : [];
  const options = payers
    .map((payer) => {
      const label = payer.display_name || payer.payer_label || payer.contact_phone || payer.billing_payer_id;
      return `<option value="${payer.billing_payer_id}">${bezpiecznyTekst(label)} | ${bezpiecznyTekst(payer.contact_phone || "-")}</option>`;
    })
    .join("");
  selects.forEach((select) => {
    const currentValue = select.value;
    const defaultLabel =
      select.id === "billing-student-payer-id"
        ? payers.length
          ? "Automatycznie po numerze albo wybierz rodzine"
          : "Pierwszy numer utworzy pierwsza rodzine"
        : payers.length
          ? "Wybierz rodzine"
          : "Najpierw dodaj rodzine";
    select.innerHTML = `<option value="">${defaultLabel}</option>${options}`;
    if (currentValue && payers.some((payer) => String(payer.billing_payer_id) === String(currentValue))) {
      select.value = currentValue;
    }
  });
  odswiezPowiazanieRodzinyWUczniu({ source: "data" });
}

function normalizujTelefonRozliczen(value) {
  let digits = String(value || "").replace(/\D+/g, "");
  if (!digits) {
    return "";
  }
  if (digits.startsWith("0048")) {
    digits = digits.slice(4);
  } else if (digits.startsWith("48") && digits.length > 9) {
    digits = digits.slice(2);
  }
  if (digits.length < 9) {
    return digits;
  }
  return digits.slice(-9);
}

function znajdzPlatnikaRozliczenPoTelefonie(phoneValue) {
  const normalizedPhone = normalizujTelefonRozliczen(phoneValue);
  if (normalizedPhone.length !== 9) {
    return null;
  }
  return (Array.isArray(stan.platnicyRozliczen) ? stan.platnicyRozliczen : []).find(
    (payer) => normalizujTelefonRozliczen(payer.contact_phone) === normalizedPhone
  ) || null;
}

function odswiezPowiazanieRodzinyWUczniu({ source = "data" } = {}) {
  const payerSelect = document.getElementById("billing-student-payer-id");
  const phoneInput = document.getElementById("billing-student-payer-phone");
  const help = document.getElementById("billing-student-payer-help");
  if (!payerSelect || !phoneInput || !help) {
    return;
  }

  const payers = Array.isArray(stan.platnicyRozliczen) ? stan.platnicyRozliczen : [];
  if (source === "payer") {
    const selectedPayer = payers.find((payer) => String(payer.billing_payer_id) === String(payerSelect.value || ""));
    if (selectedPayer?.contact_phone) {
      phoneInput.value = selectedPayer.contact_phone;
    }
  }

  const normalizedPhone = normalizujTelefonRozliczen(phoneInput.value);
  const hasFullPhone = normalizedPhone.length === 9;
  if (source === "phone" && hasFullPhone) {
    const matchedByPhone = znajdzPlatnikaRozliczenPoTelefonie(phoneInput.value);
    payerSelect.value = matchedByPhone ? String(matchedByPhone.billing_payer_id) : "";
  }

  const selectedPayer = payers.find((payer) => String(payer.billing_payer_id) === String(payerSelect.value || ""));
  const matchedPayer = hasFullPhone ? znajdzPlatnikaRozliczenPoTelefonie(phoneInput.value) : null;
  const selectedMatchesPhone =
    selectedPayer && (!hasFullPhone || normalizujTelefonRozliczen(selectedPayer.contact_phone) === normalizedPhone);
  const effectivePayer = selectedMatchesPhone ? selectedPayer : matchedPayer;

  if (effectivePayer && payerSelect.value !== String(effectivePayer.billing_payer_id)) {
    payerSelect.value = String(effectivePayer.billing_payer_id);
  }
  if (!phoneInput.value.trim() && effectivePayer?.contact_phone) {
    phoneInput.value = effectivePayer.contact_phone;
  }

  if (effectivePayer) {
    const label = effectivePayer.display_name || effectivePayer.payer_label || `Rodzina ${effectivePayer.contact_phone || ""}`;
    help.textContent = `Uczen trafi do istniejacej rodziny: ${label}. Telefon ${effectivePayer.contact_phone || "-"} zostanie tez uzyty jako identyfikator platnosci.`;
    return;
  }
  if (hasFullPhone) {
    help.textContent = "Nie ma jeszcze rodziny z tym numerem. Przy zapisie utworzymy nowa rodzine i od razu podepniemy do niej ucznia.";
    return;
  }
  if (payers.length) {
    help.textContent = "Mozesz wybrac rodzine z listy albo wpisac nowy numer telefonu. Jesli numer jest nowy, rodzina utworzy sie automatycznie.";
    return;
  }
  help.textContent = "W tej organizacji nie ma jeszcze zadnej rodziny. Wpisz numer telefonu, a przy zapisie utworzymy pierwsza rodzine automatycznie.";
}

function zbudujOpcjeSzkolRozliczen() {
  const select = document.getElementById("billing-student-school-id");
  if (!select) {
    return;
  }
  const currentValue = select.value;
  const schools = Array.isArray(stan.szkolyRozliczen) ? stan.szkolyRozliczen : [];
  select.innerHTML =
    `<option value="">${schools.length ? "Bez szkoly" : "Najpierw dodaj szkole albo zostaw puste"}</option>` +
    schools
      .map(
        (school) =>
          `<option value="${school.billing_school_id}">${bezpiecznyTekst(school.short_name || school.full_name || school.billing_school_id)}</option>`
      )
      .join("");
  if (currentValue && schools.some((school) => String(school.billing_school_id) === String(currentValue))) {
    select.value = currentValue;
  }
}

function zbudujOpcjeModeliRozliczen() {
  const studentSelect = document.getElementById("billing-student-model-id");
  const chargeSelect = document.getElementById("billing-charge-model-id");
  const models = Array.isArray(stan.modeleRozliczen) ? stan.modeleRozliczen : [];
  const options = models
    .map(
      (model) =>
        `<option value="${model.billing_model_id}">${bezpiecznyTekst(model.name)} | ${bezpiecznyTekst(model.school_year || "-")}</option>`
    )
    .join("");
  if (studentSelect) {
    const currentValue = studentSelect.value;
    studentSelect.innerHTML = `<option value="">${models.length ? "Bez modelu" : "Najpierw dodaj model albo zostaw puste"}</option>${options}`;
    if (currentValue && models.some((model) => String(model.billing_model_id) === String(currentValue))) {
      studentSelect.value = currentValue;
    }
  }
  if (chargeSelect) {
    const currentValue = chargeSelect.value;
    chargeSelect.innerHTML = `<option value="">${models.length ? "Wybierz model" : "Najpierw dodaj model"}</option>${options}`;
    if (currentValue && models.some((model) => String(model.billing_model_id) === String(currentValue))) {
      chargeSelect.value = currentValue;
    }
  }
}

function zbudujOpcjeNaleznosciDoDopasowania() {
  const chargeSelect = document.getElementById("billing-match-charge-id");
  if (!chargeSelect) {
    return;
  }
  const payerId = Number(document.getElementById("billing-match-payer-id")?.value || 0);
  const currentValue = chargeSelect.value;
  const openCharges = payerId ? pobierzOtwarteNaleznosciPlatnika(payerId) : [];
  chargeSelect.innerHTML =
    `<option value="">${payerId ? "Dopasuj tylko do rodziny albo wybierz naleznosc" : "Najpierw wybierz platnika"}</option>` +
    openCharges
      .map(
        (charge) => `
          <option value="${charge.billing_charge_id}">
            ${bezpiecznyTekst(charge.student_full_name || "Uczen")} | ${bezpiecznyTekst(charge.period_label || "-")} | ${bezpiecznyTekst(charge.due_date || "-")} | ${bezpiecznyTekst(formatujKwote(charge.remaining_amount || 0))}
          </option>
        `
      )
      .join("");
  if (currentValue && openCharges.some((charge) => String(charge.billing_charge_id) === String(currentValue))) {
    chargeSelect.value = currentValue;
  }
  renderujOtwarteNaleznosciPlatnika();
}

function renderujOtwarteNaleznosciPlatnika() {
  const body = document.getElementById("billing-open-charge-table-body");
  const count = document.getElementById("billing-open-charge-count");
  if (!body || !count) {
    return;
  }
  const payerId = Number(document.getElementById("billing-match-payer-id")?.value || 0);
  if (!payerId) {
    count.textContent = "";
    body.innerHTML = `<tr><td colspan="5">Wybierz platnika, aby zobaczyc jego otwarte naleznosci.</td></tr>`;
    return;
  }
  const openCharges = pobierzOtwarteNaleznosciPlatnika(payerId);
  count.textContent = `${openCharges.length} otwartych`;
  if (!openCharges.length) {
    body.innerHTML = `<tr><td colspan="5">Ten platnik nie ma juz otwartych naleznosci albo wszystkie zostaly rozliczone recznie.</td></tr>`;
    return;
  }
  body.innerHTML = openCharges
    .map(
      (charge) => `
        <tr class="clickable" data-billing-open-charge-id="${charge.billing_charge_id}">
          <td data-label="Uczen">${formatujWartosc(charge.student_full_name || "-")}</td>
          <td data-label="Okres">${formatujWartosc(charge.period_label || "-")}</td>
          <td data-label="Termin">${formatujWartosc(charge.due_date || "-")}</td>
          <td data-label="Kwota">${formatujKwote(charge.remaining_amount || 0)}</td>
          <td data-label="Model">${formatujWartosc(charge.model_name || "-")}</td>
        </tr>
      `
    )
    .join("");
  body.querySelectorAll("[data-billing-open-charge-id]").forEach((row) => {
    row.addEventListener("click", () => {
      const chargeSelect = document.getElementById("billing-match-charge-id");
      if (chargeSelect) {
        chargeSelect.value = row.dataset.billingOpenChargeId || "";
      }
      odswiezPomocDopasowaniaPlatnosci({ ustawDomyslnaKwote: true });
    });
  });
}

function odswiezPomocDopasowaniaPlatnosci({ ustawDomyslnaKwote = false } = {}) {
  const helper = document.getElementById("billing-match-helper-note");
  const amountInput = document.getElementById("billing-match-amount");
  if (!helper) {
    return;
  }
  const payerId = Number(document.getElementById("billing-match-payer-id")?.value || 0);
  const transactionId = Number(document.getElementById("billing-match-transaction-id")?.value || 0);
  const chargeId = Number(document.getElementById("billing-match-charge-id")?.value || 0);
  const remainingTransactionAmount = transactionId ? obliczPozostalaKwoteTransakcji(transactionId) : 0;
  const openCharges = payerId ? pobierzOtwarteNaleznosciPlatnika(payerId) : [];
  const selectedCharge = openCharges.find((charge) => Number(charge.billing_charge_id) === chargeId) || null;
  const suggestedAmount = selectedCharge
    ? Math.min(remainingTransactionAmount || Number.MAX_SAFE_INTEGER, Number(selectedCharge.remaining_amount || 0))
    : remainingTransactionAmount;

  if (!payerId && !transactionId) {
    helper.textContent = "Wybierz transakcje i platnika, aby recznie rozdzielic rodzinna wplate.";
  } else if (payerId && !openCharges.length) {
    helper.textContent = "Wybrany platnik nie ma otwartych naleznosci. Mozesz dopasowac wplate tylko na poziomie rodziny albo zostawic ja bez przypisania do konkretnej naleznosci.";
  } else if (selectedCharge) {
    helper.textContent = `Wybrana naleznosc: ${selectedCharge.student_full_name || "Uczen"} / ${selectedCharge.period_label || "-"} / pozostalo ${formatujKwote(selectedCharge.remaining_amount || 0)}.`;
  } else if (payerId) {
    helper.textContent = `Platnik ma ${openCharges.length} otwartych naleznosci. Mozesz wybrac konkretna pozycje albo dopasowac wplate tylko do rodziny.`;
  }

  if (ustawDomyslnaKwote && amountInput && suggestedAmount > 0) {
    amountInput.value = suggestedAmount.toFixed(2);
  }
}

function renderujPulpitRozliczen() {
  renderujPodsumowanieRozliczen();
  zbudujOpcjePlatnikowRozliczen();
  zbudujOpcjeSzkolRozliczen();
  zbudujOpcjeModeliRozliczen();
  renderujSzkolyRozliczen();
  renderujPlatnikowRozliczen();
  renderujUczniowRozliczen();
  renderujModeleRozliczen();
  renderujNaleznosciRozliczen();
  renderujRaportZaleglosci();
}

function odswiezStanModuluRozliczen() {
  const brakWyboruOrganizacji = czyGlobalnyAdministrator() && !stan.wybranaOrganizacjaId;
  const czyZablokowaneZapisywanie = !czyMoznaZapisywac() || brakWyboruOrganizacji;
  const czySaRachunki = stan.rachunkiBankowe.length > 0;
  const czySaPlatnicy = stan.platnicyRozliczen.length > 0;
  const czySaSzkoly = stan.szkolyRozliczen.length > 0;
  const czySaModele = stan.modeleRozliczen.length > 0;

  const polaRachunku = document
    .querySelectorAll("#billing-bank-account-form input, #billing-bank-account-form select, #billing-bank-account-form button");
  polaRachunku.forEach((element) => {
    element.disabled = czyZablokowaneZapisywanie;
  });

  const polaImportu = document.querySelectorAll(
    "#billing-statement-import-form input, #billing-statement-import-form select, #billing-statement-import-form button"
  );
  polaImportu.forEach((element) => {
    if (element.id === "billing-import-bank-account-id" || element.id === "billing-import-file" || element.id === "billing-import-button") {
      element.disabled = czyZablokowaneZapisywanie || !czySaRachunki;
    }
  });

  const przyciskDodaj = document.getElementById("billing-save-account-button");
  const przyciskImportu = document.getElementById("billing-import-button");
  if (przyciskDodaj) {
    przyciskDodaj.title = czyZablokowaneZapisywanie
      ? brakWyboruOrganizacji
        ? "Wybierz konkretna organizacje przed dodaniem rachunku bankowego."
        : "Ta rola nie moze dodawac rachunkow bankowych."
      : "";
  }
  if (przyciskImportu) {
    przyciskImportu.title = czyZablokowaneZapisywanie
      ? brakWyboruOrganizacji
        ? "Wybierz konkretna organizacje przed importem wyciagu."
        : "Ta rola nie moze importowac wyciagow."
      : !czySaRachunki
        ? "Najpierw dodaj rachunek bankowy."
        : "";
  }

  const polaSzkoly = document.querySelectorAll("#billing-school-form input, #billing-school-form textarea, #billing-school-form button");
  polaSzkoly.forEach((element) => {
    element.disabled = czyZablokowaneZapisywanie;
  });

  const polaRodziny = document.querySelectorAll("#billing-payer-form input, #billing-payer-form textarea, #billing-payer-form button");
  polaRodziny.forEach((element) => {
    element.disabled = czyZablokowaneZapisywanie;
  });

  const polaModelu = document.querySelectorAll("#billing-model-form input, #billing-model-form textarea, #billing-model-form select, #billing-model-form button");
  polaModelu.forEach((element) => {
    element.disabled = czyZablokowaneZapisywanie;
  });

  const polaUcznia = document.querySelectorAll("#billing-student-form input, #billing-student-form textarea, #billing-student-form select, #billing-student-form button");
  polaUcznia.forEach((element) => {
    if (element.id === "billing-student-payer-id") {
      element.disabled = czyZablokowaneZapisywanie || !czySaPlatnicy;
      return;
    }
    if (element.id === "billing-student-school-id") {
      element.disabled = czyZablokowaneZapisywanie || !czySaSzkoly;
      return;
    }
    if (element.id === "billing-student-model-id") {
      element.disabled = czyZablokowaneZapisywanie || !czySaModele;
      return;
    }
    element.disabled = czyZablokowaneZapisywanie;
  });

  const polaGeneratora = document.querySelectorAll("#billing-charge-generator-form input, #billing-charge-generator-form textarea, #billing-charge-generator-form select, #billing-charge-generator-form button");
  polaGeneratora.forEach((element) => {
    if (element.id === "billing-charge-model-id") {
      element.disabled = czyZablokowaneZapisywanie || !czySaModele;
      return;
    }
    element.disabled = czyZablokowaneZapisywanie || !czySaModele;
  });

  const polaDopasowania = document.querySelectorAll("#billing-manual-match-form input, #billing-manual-match-form textarea, #billing-manual-match-form select, #billing-manual-match-form button");
  polaDopasowania.forEach((element) => {
    element.disabled = czyZablokowaneZapisywanie || !czySaPlatnicy || !czySaRachunki;
  });
}

function przygotujWidokPoWylogowaniu() {
  stan.biezacyUzytkownik = null;
  stan.zadania = [];
  stan.kalendarzeUzytkownika = [];
  stan.statusPolaczeniaGoogleKalendarza = null;
  stan.zewnetrzneKalendarzeGoogle = [];
  stan.ustawieniaPrzypomnienUzytkownika = null;
  stan.pokazaneAlertyPrzegladarki.clear();
  if (stan.przypomnieniaPollingId) {
    window.clearInterval(stan.przypomnieniaPollingId);
    stan.przypomnieniaPollingId = null;
  }
  stan.rachunkiBankowe = [];
  stan.transakcjeRozliczen = [];
  stan.szkolyRozliczen = [];
  stan.platnicyRozliczen = [];
  stan.uczniowieRozliczen = [];
  stan.modeleRozliczen = [];
  stan.naleznosciRozliczen = [];
  stan.ostatniImportWyciagu = null;
  stan.dokumentyWiedzy = [];
  stan.odpowiedzBazyWiedzy = null;
  stan.folderBazyWiedzy = "";
  stan.uzytkownicyDoFaktur = [];
  stan.invoiceSavedViews = [];
  stan.invoiceSavedViewSelectedId = null;
  stan.podgladFaktury = null;
  stan.uzytkownicyDoZadan = [];
  stan.wybraneZadanieId = null;
  stan.uzytkownicy = [];
  stan.wybranyUzytkownikId = null;
  document.getElementById("password-input").value = "";
  if (typeof wyczyscWyszukiwanieGlobalne === "function") {
    wyczyscWyszukiwanieGlobalne({ clearInput: true, resetToken: true });
  } else {
    document.getElementById("global-search-results").classList.add("hidden");
    document.getElementById("global-search-results").innerHTML = "";
    document.getElementById("global-search").value = "";
  }
  document.getElementById("task-table-body").innerHTML = `<tr><td colspan="12">Zaloguj sie, aby zobaczyc zadania.</td></tr>`;
  document.getElementById("user-calendar-count").textContent = "0 rekordow";
  document.getElementById("user-calendar-table-body").innerHTML = `<tr><td colspan="8">Zaloguj sie, aby zobaczyc swoje kalendarze Google.</td></tr>`;
  renderujStatusPolaczeniaGoogleKalendarza(null);
  renderujZewnetrzneKalendarzeGoogle([]);
  wyczyscFormularzKalendarzaUzytkownika();
  renderujUstawieniaPrzypomnienUzytkownika({
    telegram_reminders_enabled: 1,
    quiet_hours_start: "",
    quiet_hours_end: "",
    repeat_interval_minutes: 0,
  });
  wyczyscSzczegolyZadania();
  stan.organizacje = [];
  stan.notatkaOrganizacji = null;
  stan.notatkaOrganizacjiTekstRoboczy = "";
  stan.notatkaOrganizacjiOstatniTekst = "";
  stan.notatkaOrganizacjiBrudna = false;
  stan.notatkaOrganizacjiMaNowszaWersje = false;
  stan.notatkaOrganizacjiZapisywanie = false;
  stan.notatkaOsobista = null;
  stan.notatkaOsobistaTekstRoboczy = "";
  stan.notatkaOsobistaOstatniTekst = "";
  stan.notatkaOsobistaBrudna = false;
  stan.notatkaOsobistaMaNowszaWersje = false;
  stan.notatkaOsobistaZapisywanie = false;
  stan.wybranaOrganizacjaId = "";
  stan.czyZakresOrganizacjiZainicjalizowany = false;
  stan.szybkiKalendarzOtwarty = false;
  stan.szybkiPanelPracyOtwarty = false;
  stan.szybkiPanelPracySekcja = "organization-note";
  stan.szybkiPanelKalendarzaTryb = "miesiac";
  stan.szybkiPanelKalendarzaZakres = "dzis";
  stan.szybkiPanelKalendarzaKotwica = null;
  stan.szybkiPanelZadanZakres = "dzis";
  stan.szybkiPanelPodswietlonyTaskId = null;
  if (stan.miganieNawigacjiTimeoutId) {
    window.clearTimeout(stan.miganieNawigacjiTimeoutId);
    stan.miganieNawigacjiTimeoutId = null;
  }
  stan.szybkiPanelPodswietlenieTimeoutId = null;
  wyczyscPodswietlenieNawigacji();
  stan.szybkiKalendarzZakres = "dzis";
  wyczyscBazeWiedzy();
  wyczyscFormularzUzytkownika();
  wyczyscFormularzOrganizacji();
  wyczyscWidokRozliczen();
  document.getElementById("users-table-body").innerHTML = `<tr><td colspan="10">Zaloguj siÄ™ jako WĹ‚aĹ›ciciel systemu albo Administrator organizacji, aby zarzÄ…dzaÄ‡ kontami.</td></tr>`;
  document.getElementById("organization-table-body").innerHTML = `<tr><td colspan="15">Zaloguj siÄ™ jako WĹ‚aĹ›ciciel systemu, aby zarzÄ…dzaÄ‡ organizacjami.</td></tr>`;
  document.getElementById("users-table-body").innerHTML =
    `<tr><td colspan="10">Zaloguj sie jako Wlasciciel systemu albo Administrator organizacji, aby zarzadzac kontami.</td></tr>`;
  document.getElementById("organization-table-body").innerHTML =
    `<tr><td colspan="15">Zaloguj sie jako Wlasciciel systemu, aby zarzadzac organizacjami.</td></tr>`;
  pokazEkranLogowania();
  odswiezPasekSesji();
  ustawMotywKontekstuInterfejsu();
  renderujNotatkeOrganizacji(null, { force: true });
  renderujNotatkeOsobista(null, { force: true });
  renderujSzybkiKalendarz();
  renderujSzybkiPanelPracy();
  ustawWidok("dashboard");
}

function zbudujOpcje(select, values, placeholder, formatter = (value) => value) {
  const options = [`<option value="">${placeholder}</option>`];
  values.forEach((value) => {
    options.push(`<option value="${bezpiecznyTekst(value)}">${bezpiecznyTekst(formatter(value))}</option>`);
  });
  select.innerHTML = options.join("");
}

function pobierzAktywnaOrganizacje() {
  return stan.organizacje.find((item) => String(item.organization_id) === String(stan.wybranaOrganizacjaId)) || null;
}

function pobierzIdNotatkiOrganizacji() {
  if (!stan.biezacyUzytkownik) {
    return "";
  }
  if (czyGlobalnyAdministrator()) {
    return String(stan.wybranaOrganizacjaId || "").trim();
  }
  return String(stan.biezacyUzytkownik.organization_id || "").trim();
}

function pobierzNazweNotatkiOrganizacji() {
  return (
    pobierzAktywnaOrganizacje()?.name ||
    stan.biezacyUzytkownik?.organization_name ||
    "organizacja"
  );
}

function pobierzStanOdczytowSzybkiegoPanelu() {
  try {
    const parsed = JSON.parse(window.localStorage.getItem(QUICK_WORKSPACE_SEEN_STORAGE_KEY) || "{}");
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch (error) {
    return {};
  }
}

function zapiszStanOdczytowSzybkiegoPanelu(snapshot) {
  window.localStorage.setItem(QUICK_WORKSPACE_SEEN_STORAGE_KEY, JSON.stringify(snapshot || {}));
}

function pobierzKluczOdczytuSzybkiegoPanelu(sectionKey) {
  if (sectionKey === "organization-note") {
    return `${sectionKey}:${pobierzIdNotatkiOrganizacji() || "brak-organizacji"}`;
  }
  if (sectionKey === "personal-note") {
    return `${sectionKey}:${stan.biezacyUzytkownik?.user_id || "brak-uzytkownika"}`;
  }
  return sectionKey;
}

function pobierzKluczOdczytuElementuSzybkiegoPanelu(sectionKey, itemId) {
  const userId = stan.biezacyUzytkownik?.user_id || "brak-uzytkownika";
  return `${sectionKey}:${userId}:${itemId}`;
}

function pobierzZnacznikOdczytuSzybkiegoPanelu(sectionKey) {
  const key = pobierzKluczOdczytuSzybkiegoPanelu(sectionKey);
  return String(pobierzStanOdczytowSzybkiegoPanelu()[key] || "");
}

function zapiszZnacznikOdczytuSzybkiegoPanelu(sectionKey, timestamp) {
  const key = pobierzKluczOdczytuSzybkiegoPanelu(sectionKey);
  const snapshot = pobierzStanOdczytowSzybkiegoPanelu();
  snapshot[key] = String(timestamp || new Date().toISOString());
  zapiszStanOdczytowSzybkiegoPanelu(snapshot);
}

function zapiszZnacznikOdczytuElementuSzybkiegoPanelu(sectionKey, itemId, timestamp) {
  const key = pobierzKluczOdczytuElementuSzybkiegoPanelu(sectionKey, itemId);
  const snapshot = pobierzStanOdczytowSzybkiegoPanelu();
  snapshot[key] = String(timestamp || new Date().toISOString());
  zapiszStanOdczytowSzybkiegoPanelu(snapshot);
}

function pobierzZnacznikOdczytuElementuSzybkiegoPanelu(sectionKey, itemId) {
  const key = pobierzKluczOdczytuElementuSzybkiegoPanelu(sectionKey, itemId);
  return String(pobierzStanOdczytowSzybkiegoPanelu()[key] || "");
}

function oznaczSekcjeSzybkiegoPaneluJakoOdczytana(sectionKey) {
  if (!stan.biezacyUzytkownik) {
    return;
  }
  let timestamp = new Date().toISOString();
  if (sectionKey === "organization-note") {
    timestamp = stan.notatkaOrganizacji?.shared_note_updated_at || timestamp;
  } else if (sectionKey === "personal-note") {
    timestamp = stan.notatkaOsobista?.personal_note_updated_at || timestamp;
  }
  zapiszZnacznikOdczytuSzybkiegoPanelu(sectionKey, timestamp);
  renderujBadgeSzybkiegoPanelu();
}

function formatujLicznikSzybkiegoPanelu(count) {
  if (count > 9) {
    return "9+";
  }
  return String(Math.max(0, count));
}

function pobierzLicznikZdarzenNotatkiOrganizacji() {
  const updatedAt = String(stan.notatkaOrganizacji?.shared_note_updated_at || "");
  if (stan.notatkaOrganizacjiMaNowszaWersje) {
    return 1;
  }
  if (!updatedAt) {
    return 0;
  }
  const seenAt = pobierzZnacznikOdczytuSzybkiegoPanelu("organization-note");
  if (!seenAt) {
    return 1;
  }
  return Date.parse(updatedAt) > Date.parse(seenAt) ? 1 : 0;
}

function pobierzLicznikZdarzenNotatkiOsobistej() {
  const updatedAt = String(stan.notatkaOsobista?.personal_note_updated_at || "");
  if (stan.notatkaOsobistaBrudna || stan.notatkaOsobistaMaNowszaWersje) {
    return 1;
  }
  if (!updatedAt) {
    return 0;
  }
  const seenAt = pobierzZnacznikOdczytuSzybkiegoPanelu("personal-note");
  if (!seenAt) {
    return 1;
  }
  return Date.parse(updatedAt) > Date.parse(seenAt) ? 1 : 0;
}

function pobierzLicznikZdarzenKalendarza() {
  if (!czyMoznaKorzystacZMojejPracy()) {
    return 0;
  }
  const wpisy = pobierzSzybkieWpisyKalendarza(stan.szybkiPanelKalendarzaZakres || "dzis");
  return wpisy.filter((task) => !czyElementSzybkiegoPaneluJestPrzeczytany("calendar", task)).length;
}

function pobierzLicznikZdarzenZadan() {
  if (!czyMoznaKorzystacZMojejPracy()) {
    return 0;
  }
  return pobierzSzybkieZadaniaZakresu(stan.szybkiPanelZadanZakres || "dzis", { limit: 999 })
    .filter((task) => !czyElementSzybkiegoPaneluJestPrzeczytany("tasks", task)).length;
}

function czyMoznaPodejrzecDokumentyFirmoweWSzybkimPanelu() {
  return typeof czyMoznaCzytacBazeWiedzy === "function" && typeof czyModulWiedzyMaZakres === "function"
    ? czyMoznaCzytacBazeWiedzy() && czyModulWiedzyMaZakres()
    : false;
}

function pobierzLicznikZdarzenDokumentowFirmowych() {
  if (!czyMoznaPodejrzecDokumentyFirmoweWSzybkimPanelu()) {
    return 0;
  }
  const summary = stan.podsumowanieAktywnosciBazyWiedzy || {};
  return Number(summary.my_attention_count || summary.pending_decision_count || 0);
}

function pobierzSzybkieDokumentyFirmoweDoPanelu(limit = 6) {
  if (!czyMoznaPodejrzecDokumentyFirmoweWSzybkimPanelu()) {
    return [];
  }
  const currentUserId = Number(stan.biezacyUzytkownik?.user_id || 0);
  const documents = Array.isArray(stan.dokumentyWiedzy) ? stan.dokumentyWiedzy : [];
  return [...documents]
    .filter((document) => {
      if (String(document.lifecycle_status || "active") !== "active") {
        return false;
      }
      const businessStatus = String(document.business_status || "roboczy");
      if (businessStatus === "roboczy" && Number(document.owner_user_id || 0) === currentUserId) {
        return true;
      }
      if (businessStatus === "do_sprawdzenia" && Number(document.reviewer_user_id || 0) === currentUserId) {
        return true;
      }
      if (businessStatus === "do_akceptacji" && Number(document.approver_user_id || 0) === currentUserId) {
        return true;
      }
      return ["do_sprawdzenia", "do_akceptacji"].includes(businessStatus);
    })
    .sort((left, right) => Date.parse(String(right.updated_at || "")) - Date.parse(String(left.updated_at || "")))
    .slice(0, limit);
}

function czyElementSzybkiegoPaneluJestPrzeczytany(sectionKey, task) {
  if (!task || !task.task_id) {
    return false;
  }
  const seenAt = pobierzZnacznikOdczytuElementuSzybkiegoPanelu(sectionKey, task.task_id);
  if (!seenAt) {
    return false;
  }
  const reference = String(task.updated_at || task.due_at || task.remind_at || "");
  if (!reference) {
    return true;
  }
  return Date.parse(seenAt) >= Date.parse(reference);
}

function oznaczElementSzybkiegoPaneluJakoPrzeczytany(sectionKey, taskId) {
  const task = znajdzZadaniePoId(taskId);
  const timestamp = String(task?.updated_at || task?.due_at || task?.remind_at || new Date().toISOString());
  zapiszZnacznikOdczytuElementuSzybkiegoPanelu(sectionKey, taskId, timestamp);
  renderujBadgeSzybkiegoPanelu();
}

function czyElementJestWidocznyDoPodswietlenia(element) {
  if (!(element instanceof HTMLElement)) {
    return false;
  }
  if (element.classList.contains("hidden") || element.hidden || element.getAttribute("aria-hidden") === "true") {
    return false;
  }
  const style = window.getComputedStyle(element);
  return style.display !== "none" && style.visibility !== "hidden" && element.getClientRects().length > 0;
}

function pobierzElementDocelowyPodswietlenia(element) {
  if (!(element instanceof HTMLElement)) {
    return null;
  }
  if (element.matches(".modal-shell")) {
    return element.querySelector(".modal-card") || element;
  }
  return element;
}

function wyczyscPodswietlenieNawigacji() {
  document.querySelectorAll(`.${QUICK_WORKSPACE_TARGET_FLASH_CLASS}`).forEach((element) => {
    element.classList.remove(QUICK_WORKSPACE_TARGET_FLASH_CLASS);
  });
}

function zaplanujWyczyszczeniePodswietleniaNawigacji() {
  if (stan.miganieNawigacjiTimeoutId) {
    window.clearTimeout(stan.miganieNawigacjiTimeoutId);
  }
  stan.miganieNawigacjiTimeoutId = window.setTimeout(() => {
    wyczyscPodswietlenieNawigacji();
    stan.szybkiPanelPodswietlonyTaskId = null;
    stan.miganieNawigacjiTimeoutId = null;
    stan.szybkiPanelPodswietlenieTimeoutId = null;
  }, 5000);
  stan.szybkiPanelPodswietlenieTimeoutId = stan.miganieNawigacjiTimeoutId;
}

function podswietlCeleNawigacji({ selectors = [], elements = [], clearExisting = true } = {}) {
  const collected = [];
  const seen = new Set();
  selectors.forEach((selector) => {
    if (!selector) {
      return;
    }
    document.querySelectorAll(selector).forEach((element) => {
      const target = pobierzElementDocelowyPodswietlenia(element);
      if (!czyElementJestWidocznyDoPodswietlenia(target) || seen.has(target)) {
        return;
      }
      seen.add(target);
      collected.push(target);
    });
  });
  elements.forEach((element) => {
    const target = pobierzElementDocelowyPodswietlenia(element);
    if (!czyElementJestWidocznyDoPodswietlenia(target) || seen.has(target)) {
      return;
    }
    seen.add(target);
    collected.push(target);
  });
  if (!collected.length) {
    return;
  }
  window.requestAnimationFrame(() => {
    if (clearExisting) {
      wyczyscPodswietlenieNawigacji();
    }
    collected.forEach((element) => {
      const lastAt = quickWorkspaceFlashTimestamps.get(element) || 0;
      if (Date.now() - lastAt < 220) {
        return;
      }
      element.classList.remove(QUICK_WORKSPACE_TARGET_FLASH_CLASS);
      void element.offsetWidth;
      element.classList.add(QUICK_WORKSPACE_TARGET_FLASH_CLASS);
      quickWorkspaceFlashTimestamps.set(element, Date.now());
    });
    zaplanujWyczyszczeniePodswietleniaNawigacji();
  });
}

function podswietlPrzejscieDoWidoku(widok, extraSelectors = []) {
  if (!widok) {
    return;
  }
  podswietlCeleNawigacji({
    selectors: [
      `#${widok}-view`,
      `#view-title`,
      `.nav-item[data-view="${widok}"]`,
      `[data-launch-view="${widok}"]`,
      ...extraSelectors,
    ],
  });
}

function rozpocznijObserwacjePodswietleniaNawigacji() {
  if (quickWorkspaceFlashObserver || !document.body) {
    return;
  }
  quickWorkspaceFlashObserver = new MutationObserver((mutations) => {
    const candidates = [];
    const seen = new Set();
    mutations.forEach((mutation) => {
      const target = mutation.target instanceof HTMLElement ? mutation.target : null;
      if (!target) {
        return;
      }
      const nodes = [target];
      if (typeof target.querySelectorAll === "function") {
        target.querySelectorAll(QUICK_WORKSPACE_FLASH_OBSERVER_SELECTOR).forEach((element) => nodes.push(element));
      }
      nodes.forEach((node) => {
        if (!(node instanceof HTMLElement) || !node.matches(QUICK_WORKSPACE_FLASH_OBSERVER_SELECTOR)) {
          return;
        }
        const normalized = pobierzElementDocelowyPodswietlenia(node);
        if (!czyElementJestWidocznyDoPodswietlenia(normalized) || seen.has(normalized)) {
          return;
        }
        const lastAt = quickWorkspaceFlashTimestamps.get(normalized) || 0;
        if (Date.now() - lastAt < 220) {
          return;
        }
        seen.add(normalized);
        candidates.push(normalized);
      });
    });
    if (candidates.length) {
      podswietlCeleNawigacji({ elements: candidates });
    }
  });
  quickWorkspaceFlashObserver.observe(document.body, {
    subtree: true,
    attributes: true,
    attributeFilter: ["class", "aria-hidden", "open"],
  });
}

function podswietlDoceloweZadanie(taskId) {
  const normalizedTaskId = Number(taskId || 0);
  if (!normalizedTaskId) {
    return;
  }
  stan.szybkiPanelPodswietlonyTaskId = normalizedTaskId;
  podswietlCeleNawigacji({
    selectors: [
      "#tasks-view",
      "#view-title",
      `[data-task-id="${normalizedTaskId}"]`,
      `[data-planner-task-id="${normalizedTaskId}"]`,
      "#task-detail",
    ],
  });
}

function renderujBadgeSzybkiegoPanelu() {
  const counts = {
    "organization-note": pobierzLicznikZdarzenNotatkiOrganizacji(),
    "personal-note": pobierzLicznikZdarzenNotatkiOsobistej(),
    calendar: pobierzLicznikZdarzenKalendarza(),
    tasks: pobierzLicznikZdarzenZadan(),
    knowledge: pobierzLicznikZdarzenDokumentowFirmowych(),
  };
  const launcherBadge = document.getElementById("quick-workspace-launcher-badge");
  const total = Object.values(counts).reduce((sum, value) => sum + Number(value || 0), 0);
  if (launcherBadge) {
    launcherBadge.classList.toggle("hidden", total <= 0);
    launcherBadge.textContent = formatujLicznikSzybkiegoPanelu(total);
  }
  Object.entries(counts).forEach(([sectionKey, count]) => {
    const badge = document.querySelector(`[data-quick-workspace-badge="${sectionKey}"]`);
    if (!badge) {
      return;
    }
    badge.classList.toggle("hidden", Number(count || 0) <= 0);
    badge.textContent = formatujLicznikSzybkiegoPanelu(Number(count || 0));
  });
}

function zbudujStatusNotatkiOrganizacji(snapshot = null) {
  if (!stan.biezacyUzytkownik) {
    return "Zaloguj sie, aby pracowac na wspolnej notatce organizacji.";
  }
  if (!pobierzIdNotatkiOrganizacji()) {
    return "Wybierz organizacje, aby odczytac albo zaktualizowac wspolna notatke.";
  }
  const statusy = [];
  const updatedAt = snapshot?.shared_note_updated_at;
  const updatedBy = snapshot?.shared_note_updated_by_name;
  if (updatedAt) {
    statusy.push(
      `Ostatnia zmiana: ${formatujDateCzas(updatedAt)}${updatedBy ? ` przez ${updatedBy}` : ""}.`
    );
  } else {
    statusy.push("Jeszcze nikt nie zapisal wspolnej notatki dla tej organizacji.");
  }
  if (stan.notatkaOrganizacjiBrudna) {
    statusy.push("Masz niezapisane zmiany.");
  }
  if (stan.notatkaOrganizacjiMaNowszaWersje) {
    statusy.push("Na serwerze pojawila sie nowsza wersja. Zapisz swoje zmiany albo odswiez pulpit.");
  }
  return statusy.join(" ");
}

function renderujNotatkeOrganizacji(snapshot = null, { force = false } = {}) {
  const editors = [
    {
      panel: document.querySelector(".dashboard-shared-note-panel"),
      pole: document.getElementById("organization-shared-note-text"),
      przycisk: document.getElementById("organization-shared-note-save"),
      status: document.getElementById("organization-shared-note-status"),
    },
    {
      panel: document.querySelector(".quick-workspace-card-organization-note"),
      pole: document.getElementById("quick-workspace-organization-note-text"),
      przycisk: document.getElementById("quick-workspace-organization-note-save"),
      status: document.getElementById("quick-workspace-organization-note-status"),
    },
  ].filter((item) => item.panel && item.pole && item.przycisk && item.status);
  if (!editors.length) {
    renderujBadgeSzybkiegoPanelu();
    return;
  }

  const hasScope = Boolean(pobierzIdNotatkiOrganizacji());
  const editable = Boolean(stan.biezacyUzytkownik) && hasScope;
  const remoteText = String(snapshot?.shared_note_text || "");
  const shouldApplyRemote =
    force ||
    !stan.notatkaOrganizacjiBrudna ||
    Number(stan.notatkaOrganizacji?.organization_id || 0) !== Number(snapshot?.organization_id || 0);

  if (!editable) {
    stan.notatkaOrganizacji = snapshot;
    stan.notatkaOrganizacjiTekstRoboczy = "";
    stan.notatkaOrganizacjiOstatniTekst = "";
    stan.notatkaOrganizacjiBrudna = false;
    stan.notatkaOrganizacjiMaNowszaWersje = false;
    editors.forEach(({ panel, pole, przycisk, status }) => {
      pole.value = "";
      pole.disabled = true;
      przycisk.disabled = true;
      status.textContent = zbudujStatusNotatkiOrganizacji(snapshot);
      panel.classList.remove("is-dirty");
    });
    renderujBadgeSzybkiegoPanelu();
    return;
  }

  if (shouldApplyRemote) {
    editors.forEach(({ pole }) => {
      pole.value = remoteText;
    });
    stan.notatkaOrganizacjiTekstRoboczy = remoteText;
    stan.notatkaOrganizacjiOstatniTekst = remoteText;
    stan.notatkaOrganizacjiBrudna = false;
    stan.notatkaOrganizacjiMaNowszaWersje = false;
  } else if (remoteText !== stan.notatkaOrganizacjiOstatniTekst) {
    stan.notatkaOrganizacjiMaNowszaWersje = true;
  }

  stan.notatkaOrganizacji = snapshot;
  editors.forEach(({ panel, pole, przycisk, status }) => {
    pole.disabled = stan.notatkaOrganizacjiZapisywanie;
    pole.placeholder = `Wspolna notatka dla ${pobierzNazweNotatkiOrganizacji()}.`;
    przycisk.disabled = stan.notatkaOrganizacjiZapisywanie || !hasScope;
    przycisk.textContent = stan.notatkaOrganizacjiZapisywanie ? "Zapisuje..." : "Zapisz notatke";
    status.textContent = zbudujStatusNotatkiOrganizacji(snapshot);
    panel.classList.toggle("is-dirty", stan.notatkaOrganizacjiBrudna);
  });
  renderujBadgeSzybkiegoPanelu();
}

async function wczytajNotatkeOrganizacji({ force = false } = {}) {
  if (!stan.biezacyUzytkownik) {
    renderujNotatkeOrganizacji(null, { force: true });
    return null;
  }
  const organizationId = pobierzIdNotatkiOrganizacji();
  if (!organizationId) {
    stan.notatkaOrganizacji = null;
    renderujNotatkeOrganizacji(null, { force: true });
    return null;
  }
  const snapshot = await api(zbudujAdresZOrganizacja("/api/organization-shared-note"));
  stan.notatkaOrganizacji = snapshot;
  renderujNotatkeOrganizacji(snapshot, { force });
  return snapshot;
}

async function zapiszNotatkeOrganizacji() {
  if (!stan.biezacyUzytkownik) {
    pokazPowiadomienie("Zaloguj sie, aby zapisac wspolna notatke.");
    return;
  }
  if (!pobierzIdNotatkiOrganizacji()) {
    pokazPowiadomienie("Wybierz organizacje przed zapisem wspolnej notatki.");
    return;
  }
  const pole =
    document.getElementById("quick-workspace-organization-note-text") ||
    document.getElementById("organization-shared-note-text");
  if (!pole) {
    return;
  }

  stan.notatkaOrganizacjiZapisywanie = true;
  renderujNotatkeOrganizacji(stan.notatkaOrganizacji);
  try {
    const updated = await api(zbudujAdresZOrganizacja("/api/organization-shared-note"), {
      method: "PATCH",
      body: JSON.stringify({ shared_note_text: pole.value }),
    });
    stan.notatkaOrganizacji = updated;
    stan.notatkaOrganizacjiTekstRoboczy = String(updated.shared_note_text || "");
    stan.notatkaOrganizacjiOstatniTekst = String(updated.shared_note_text || "");
    stan.notatkaOrganizacjiBrudna = false;
    stan.notatkaOrganizacjiMaNowszaWersje = false;
    renderujNotatkeOrganizacji(updated, { force: true });
    pokazPowiadomienie("Zapisano wspolna notatke organizacji.");
    wczytajLogi().catch(() => {});
  } finally {
    stan.notatkaOrganizacjiZapisywanie = false;
    renderujNotatkeOrganizacji(stan.notatkaOrganizacji);
  }
}

function zbudujStatusNotatkiOsobistej(snapshot = null) {
  if (!stan.biezacyUzytkownik) {
    return "Zaloguj sie, aby pracowac na notatce osobistej.";
  }
  const statusy = [];
  if (snapshot?.personal_note_updated_at) {
    statusy.push(`Ostatnia zmiana: ${formatujDateCzas(snapshot.personal_note_updated_at)}.`);
  } else {
    statusy.push("Jeszcze nic tu nie zapisales.");
  }
  if (stan.notatkaOsobistaBrudna) {
    statusy.push("Masz niezapisane zmiany.");
  }
  if (stan.notatkaOsobistaMaNowszaWersje) {
    statusy.push("Na serwerze jest nowsza wersja. Zapisz swoje zmiany albo odswiez panel.");
  }
  return statusy.join(" ");
}

function renderujNotatkeOsobista(snapshot = null, { force = false } = {}) {
  const editors = [
    {
      panel: document.querySelector(".quick-workspace-card-personal-note"),
      pole: document.getElementById("quick-workspace-personal-note-text"),
      przycisk: document.getElementById("quick-workspace-personal-note-save"),
      status: document.getElementById("quick-workspace-personal-note-status"),
    },
  ].filter((item) => item.panel && item.pole && item.przycisk && item.status);

  if (!stan.biezacyUzytkownik) {
    stan.notatkaOsobista = snapshot;
    stan.notatkaOsobistaTekstRoboczy = "";
    stan.notatkaOsobistaOstatniTekst = "";
    stan.notatkaOsobistaBrudna = false;
    stan.notatkaOsobistaMaNowszaWersje = false;
    editors.forEach(({ panel, pole, przycisk, status }) => {
      pole.value = "";
      pole.disabled = true;
      przycisk.disabled = true;
      status.textContent = zbudujStatusNotatkiOsobistej(snapshot);
      panel.classList.remove("is-dirty");
    });
    renderujBadgeSzybkiegoPanelu();
    return;
  }

  const remoteText = String(snapshot?.personal_note_text || "");
  const shouldApplyRemote = force || !stan.notatkaOsobistaBrudna;
  if (shouldApplyRemote) {
    editors.forEach(({ pole }) => {
      pole.value = remoteText;
    });
    stan.notatkaOsobistaTekstRoboczy = remoteText;
    stan.notatkaOsobistaOstatniTekst = remoteText;
    stan.notatkaOsobistaBrudna = false;
    stan.notatkaOsobistaMaNowszaWersje = false;
  } else if (remoteText !== stan.notatkaOsobistaOstatniTekst) {
    stan.notatkaOsobistaMaNowszaWersje = true;
  }

  stan.notatkaOsobista = snapshot;
  editors.forEach(({ panel, pole, przycisk, status }) => {
    pole.disabled = stan.notatkaOsobistaZapisywanie;
    pole.placeholder = "Twoja osobista notatka robocza.";
    przycisk.disabled = stan.notatkaOsobistaZapisywanie;
    przycisk.textContent = stan.notatkaOsobistaZapisywanie ? "Zapisuje..." : "Zapisz notatke";
    status.textContent = zbudujStatusNotatkiOsobistej(snapshot);
    panel.classList.toggle("is-dirty", stan.notatkaOsobistaBrudna);
  });
  renderujBadgeSzybkiegoPanelu();
}

async function wczytajNotatkeOsobista({ force = false } = {}) {
  if (!stan.biezacyUzytkownik) {
    renderujNotatkeOsobista(null, { force: true });
    return null;
  }
  const snapshot = await api("/api/user-personal-note");
  stan.notatkaOsobista = snapshot;
  renderujNotatkeOsobista(snapshot, { force });
  return snapshot;
}

async function zapiszNotatkeOsobista() {
  if (!stan.biezacyUzytkownik) {
    pokazPowiadomienie("Zaloguj sie, aby zapisac notatke osobista.");
    return;
  }
  const pole = document.getElementById("quick-workspace-personal-note-text");
  if (!pole) {
    return;
  }

  stan.notatkaOsobistaZapisywanie = true;
  renderujNotatkeOsobista(stan.notatkaOsobista);
  try {
    const updated = await api("/api/user-personal-note", {
      method: "PATCH",
      body: JSON.stringify({ personal_note_text: pole.value }),
    });
    stan.notatkaOsobista = updated;
    stan.notatkaOsobistaTekstRoboczy = String(updated.personal_note_text || "");
    stan.notatkaOsobistaOstatniTekst = String(updated.personal_note_text || "");
    stan.notatkaOsobistaBrudna = false;
    stan.notatkaOsobistaMaNowszaWersje = false;
    renderujNotatkeOsobista(updated, { force: true });
    oznaczSekcjeSzybkiegoPaneluJakoOdczytana("personal-note");
    pokazPowiadomienie("Zapisano notatke osobista.");
    wczytajLogi().catch(() => {});
  } finally {
    stan.notatkaOsobistaZapisywanie = false;
    renderujNotatkeOsobista(stan.notatkaOsobista);
  }
}

function pobierzAktywnaSekcjeSzybkiegoPanelu() {
  return quickWorkspaceSectionConfig[stan.szybkiPanelPracySekcja] ? stan.szybkiPanelPracySekcja : "organization-note";
}

function pobierzSzybkieZadaniaDoPanelu(limit = 6) {
  return pobierzSzybkieZadaniaZakresu(stan.szybkiPanelZadanZakres || "dzis", { limit });
}

function pobierzZakresSzybkiegoPanelu(rangeCode = "dzis") {
  const dzis = sklonujDateNaPolnoc(new Date());
  const jutro = dodajDniDoDaty(dzis, 1);
  const pojutrze = dodajDniDoDaty(dzis, 2);
  const zaTydzien = dodajDniDoDaty(dzis, 7);
  if (rangeCode === "jutro") {
    return { start: jutro, end: pojutrze, label: "Jutro" };
  }
  if (rangeCode === "tydzien") {
    return { start: dzis, end: dodajDniDoDaty(zaTydzien, 1), label: "7 dni" };
  }
  return { start: dzis, end: jutro, label: "Dzis" };
}

function pobierzSzybkieZadaniaZakresu(rangeCode = "dzis", { limit = 6 } = {}) {
  const zakres = pobierzZakresSzybkiegoPanelu(rangeCode);
  return [...(Array.isArray(stan.zadania) ? stan.zadania : [])]
    .filter((task) => {
      const status = String(task.status || "").trim().toLowerCase();
      if (["zakonczone", "anulowane"].includes(status)) {
        return false;
      }
      const anchor = pobierzZakotwiczenieSzybkiegoKalendarza(task);
      return Boolean(anchor && anchor >= zakres.start && anchor < zakres.end);
    })
    .sort((left, right) => {
      const leftAnchor = pobierzZakotwiczenieSzybkiegoKalendarza(left)?.getTime() || Number.MAX_SAFE_INTEGER;
      const rightAnchor = pobierzZakotwiczenieSzybkiegoKalendarza(right)?.getTime() || Number.MAX_SAFE_INTEGER;
      return leftAnchor - rightAnchor;
    })
    .slice(0, limit);
}

function pobierzKotwiceSzybkiegoPaneluKalendarza() {
  if (!(stan.szybkiPanelKalendarzaKotwica instanceof Date) || Number.isNaN(stan.szybkiPanelKalendarzaKotwica.getTime())) {
    stan.szybkiPanelKalendarzaKotwica = new Date();
  }
  return new Date(stan.szybkiPanelKalendarzaKotwica);
}

function pobierzWpisyMiesiacaSzybkiegoPanelu(anchor = pobierzKotwiceSzybkiegoPaneluKalendarza()) {
  const poczatek = poczatekMiesiaca(anchor);
  const koniec = dodajDniDoDaty(koniecMiesiaca(anchor), 1);
  return pobierzWpisyKalendarzaZadan(stan.zadania).filter((entry) => {
    const status = String(entry?.task?.status || "").trim().toLowerCase();
    return !["zakonczone", "anulowane"].includes(status) && entry.date >= poczatek && entry.date < koniec;
  });
}

function zbudujSzybkiPanelNotatkiOrganizacji() {
  return `
    <div class="quick-workspace-card quick-workspace-card-organization-note${stan.notatkaOrganizacjiBrudna ? " is-dirty" : ""}">
      <div class="quick-workspace-card-header">
        <strong>Notatka organizacji</strong>
        <div id="quick-workspace-organization-note-status" class="subtle-note">${bezpiecznyTekst(zbudujStatusNotatkiOrganizacji(stan.notatkaOrganizacji))}</div>
      </div>
      <textarea id="quick-workspace-organization-note-text" rows="9">${bezpiecznyTekst(stan.notatkaOrganizacjiBrudna ? stan.notatkaOrganizacjiTekstRoboczy : String(stan.notatkaOrganizacji?.shared_note_text || ""))}</textarea>
      <div class="filters-actions">
        <button type="button" id="quick-workspace-organization-note-save"${stan.notatkaOrganizacjiZapisywanie ? " disabled" : ""}>${stan.notatkaOrganizacjiZapisywanie ? "Zapisuje..." : "Zapisz notatke"}</button>
      </div>
    </div>
  `;
}

function zbudujSzybkiPanelNotatkiOsobistej() {
  return `
    <div class="quick-workspace-card quick-workspace-card-personal-note${stan.notatkaOsobistaBrudna ? " is-dirty" : ""}">
      <div class="quick-workspace-card-header">
        <strong>Notatka osobista</strong>
        <div id="quick-workspace-personal-note-status" class="subtle-note">${bezpiecznyTekst(zbudujStatusNotatkiOsobistej(stan.notatkaOsobista))}</div>
      </div>
      <textarea id="quick-workspace-personal-note-text" rows="9">${bezpiecznyTekst(stan.notatkaOsobistaBrudna ? stan.notatkaOsobistaTekstRoboczy : String(stan.notatkaOsobista?.personal_note_text || ""))}</textarea>
      <div class="filters-actions">
        <button type="button" id="quick-workspace-personal-note-save"${stan.notatkaOsobistaZapisywanie ? " disabled" : ""}>${stan.notatkaOsobistaZapisywanie ? "Zapisuje..." : "Zapisz notatke"}</button>
      </div>
    </div>
  `;
}

function zbudujSzybkiPanelKalendarza() {
  if (!stan.biezacyUzytkownik) {
    return `<div class="empty-state">Zaloguj sie, aby otworzyc kalendarz.</div>`;
  }
  if (czyWlascicielSystemuWTrybieGlobalnym()) {
    return `<div class="empty-state">Wybierz organizacje, aby podejrzec jej kalendarz pracy.</div>`;
  }
  if (!czyMoznaKorzystacZMojejPracy()) {
    return `<div class="empty-state">Ten kontekst nie ma aktywnego modulu Asystent Szefa.</div>`;
  }
  const labels = { dzis: "Dzis", jutro: "Jutro", tydzien: "7 dni" };
  const mode = stan.szybkiPanelKalendarzaTryb === "miesiac" ? "miesiac" : "zakres";
  const rangeCode = stan.szybkiPanelKalendarzaZakres || "dzis";
  const zakres = pobierzZakresSzybkiegoPanelu(rangeCode);
  const wpisy = pobierzSzybkieWpisyKalendarza(rangeCode);
  const monthAnchor = pobierzKotwiceSzybkiegoPaneluKalendarza();
  const monthEntries = pobierzWpisyMiesiacaSzybkiegoPanelu(monthAnchor);
  const pills = mode === "miesiac"
    ? [
        `<span class="quick-workspace-pill">${bezpiecznyTekst(formatujNaglowekMiesiaca(monthAnchor))}</span>`,
        `<span class="quick-workspace-pill">W miesiacu: ${monthEntries.length}</span>`,
      ]
    : [
        `<span class="quick-workspace-pill">${bezpiecznyTekst(zakres.label)}</span>`,
        `<span class="quick-workspace-pill">Wpisy: ${wpisy.length}</span>`,
      ];
  if (Number(stan.plannerZadan?.buckets?.zalegle?.count || 0)) {
    pills.push(`<span class="quick-workspace-pill">Zalegle: ${Number(stan.plannerZadan?.buckets?.zalegle?.count || 0)}</span>`);
  }

  const listHtml = (() => {
    if (mode === "miesiac") {
      const wydarzeniaDnia = new Map();
      monthEntries.forEach((entry) => {
        const key = kalendarzKluczDnia(entry.date);
        if (!wydarzeniaDnia.has(key)) {
          wydarzeniaDnia.set(key, []);
        }
        wydarzeniaDnia.get(key).push(entry);
      });
      const start = poczatekTygodnia(poczatekMiesiaca(monthAnchor));
      const cells = Array.from({ length: 42 }, (_, index) => dodajDniDoDaty(start, index));
      const todayKey = kalendarzKluczDnia(new Date());
      return `
        <div class="quick-workspace-calendar-header">
          <button type="button" class="secondary small-action quick-workspace-calendar-nav-button" data-quick-workspace-calendar-nav="-1" aria-label="Poprzedni miesiac">&lt;</button>
          <strong>${bezpiecznyTekst(formatujNaglowekMiesiaca(monthAnchor))}</strong>
          <button type="button" class="secondary small-action quick-workspace-calendar-nav-button" data-quick-workspace-calendar-nav="1" aria-label="Nastepny miesiac">&gt;</button>
        </div>
        <div class="quick-workspace-calendar-weekdays">
          ${["Pon", "Wt", "Sr", "Czw", "Pt", "Sob", "Nd"].map((item) => `<div>${item}</div>`).join("")}
        </div>
        <div class="quick-workspace-calendar-grid" role="grid" aria-label="${bezpiecznyTekst(formatujNaglowekMiesiaca(monthAnchor))}">
          ${cells
            .map((day) => {
              const key = kalendarzKluczDnia(day);
              const dayEntries = wydarzeniaDnia.get(key) || [];
              const outsideMonth = day.getMonth() !== monthAnchor.getMonth();
              const isToday = key === todayKey;
              const previewItems = dayEntries
                .slice(0, 2)
                .map((entry) => `<div class="quick-workspace-calendar-day-preview-item">${bezpiecznyTekst(entry.task.title || "Wpis")}</div>`)
                .join("");
              const moreCount = Math.max(0, dayEntries.length - 2);
              return `
                <button
                  type="button"
                  class="quick-workspace-calendar-day ${outsideMonth ? "is-outside-month" : ""} ${isToday ? "is-today" : ""} ${dayEntries.length ? "has-events" : ""}"
                  data-quick-workspace-calendar-day="${key}"
                  aria-label="${bezpiecznyTekst(`Dzien ${day.getDate()} ${formatujNaglowekMiesiaca(day)}${dayEntries.length ? `, wpisow ${dayEntries.length}` : ""}`)}"
                >
                  <div class="quick-workspace-calendar-day-top">
                    <strong class="quick-workspace-calendar-day-number">${day.getDate()}</strong>
                    ${dayEntries.length ? `<span class="quick-workspace-calendar-day-count">${dayEntries.length}</span>` : ""}
                  </div>
                  <div class="quick-workspace-calendar-day-preview">
                    ${previewItems || '<div class="quick-workspace-calendar-day-empty"></div>'}
                    ${moreCount ? `<div class="quick-workspace-calendar-day-more">+${moreCount} wiecej</div>` : ""}
                  </div>
                </button>
              `;
            })
            .join("")}
        </div>
      `;
    }
    if (!wpisy.length) {
      return `<div class="empty-state">Brak wpisow w tym zakresie.</div>`;
    }
    return `
      <div class="quick-workspace-list">
        ${wpisy
          .map((task) => {
            const anchor = pobierzZakotwiczenieSzybkiegoKalendarza(task);
            const isUnread = !czyElementSzybkiegoPaneluJestPrzeczytany("calendar", task);
            return `
              <article class="quick-workspace-list-item ${isUnread ? "is-unread" : ""}">
                <div class="quick-workspace-list-item-top">
                  <div class="quick-workspace-list-item-title">${bezpiecznyTekst(task.title || "(bez tytulu)")}</div>
                  <div class="quick-workspace-list-item-top-badges">
                    ${isUnread ? '<span class="quick-workspace-unread-dot" aria-hidden="true"></span>' : ""}
                    <span class="status-badge ${klasaStatusuZadania(task.status, task.priority)}">${bezpiecznyTekst(formatujTypZadania(task.task_type))}</span>
                  </div>
                </div>
                <div class="quick-workspace-list-item-meta">
                  <span>${bezpiecznyTekst(formatujDateCzas(anchor))}</span>
                  <span>${bezpiecznyTekst(task.assigned_user_name || task.owner_user_name || "brak osoby")}</span>
                </div>
                <div class="quick-workspace-list-item-actions">
                  <button type="button" class="secondary" data-quick-workspace-open-task="${task.task_id}" data-quick-workspace-open-source="calendar">Otworz</button>
                </div>
              </article>
            `;
          })
          .join("")}
      </div>
    `;
  })();
  return `
    <div class="quick-workspace-card">
      <div class="quick-workspace-range-bar">
        ${Object.entries(labels)
          .map(
            ([key, label]) =>
              `<button type="button" class="quick-workspace-range-button ${mode === "zakres" && key === rangeCode ? "active" : ""}" data-quick-workspace-range="${key}">${bezpiecznyTekst(label)}</button>`
          )
          .join("")}
        <button type="button" class="quick-workspace-range-button quick-workspace-range-button-icon ${mode === "miesiac" ? "active" : ""}" data-quick-workspace-calendar-mode="miesiac" aria-label="Widok miesieczny" title="Widok miesieczny">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M7 2a1 1 0 0 1 1 1v1h8V3a1 1 0 1 1 2 0v1h1a3 3 0 0 1 3 3v11a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V7a3 3 0 0 1 3-3h1V3a1 1 0 0 1 1-1Zm13 8H4v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8Z" fill="currentColor"/>
          </svg>
        </button>
      </div>
      <div class="quick-workspace-pills">${pills.join("")}</div>
      ${listHtml}
      <div class="filters-actions">
        <button type="button" class="secondary" data-quick-workspace-open-view="tasks">Otworz modul</button>
      </div>
    </div>
  `;
}

function zbudujSzybkiPanelZadan() {
  if (!stan.biezacyUzytkownik) {
    return `<div class="empty-state">Zaloguj sie, aby zobaczyc zadania.</div>`;
  }
  if (czyWlascicielSystemuWTrybieGlobalnym()) {
    return `<div class="empty-state">Wybierz organizacje, aby podejrzec zadania tej organizacji.</div>`;
  }
  if (!czyMoznaKorzystacZMojejPracy()) {
    return `<div class="empty-state">Ten kontekst nie ma aktywnego modulu Asystent Szefa.</div>`;
  }
  const rangeCode = stan.szybkiPanelZadanZakres || "dzis";
  const labels = { dzis: "Dzis", jutro: "Jutro", tydzien: "7 dni" };
  const zadania = pobierzSzybkieZadaniaZakresu(rangeCode);
  const pills = [
    `<span class="quick-workspace-pill">${bezpiecznyTekst(pobierzZakresSzybkiegoPanelu(rangeCode).label)}</span>`,
    `<span class="quick-workspace-pill">Aktywne: ${zadania.length}</span>`,
    Number(stan.plannerZadan?.buckets?.zalegle?.count || 0)
      ? `<span class="quick-workspace-pill">Zalegle: ${Number(stan.plannerZadan?.buckets?.zalegle?.count || 0)}</span>`
      : "",
    Number(stan.plannerZadan?.buckets?.dzis?.count || 0)
      ? `<span class="quick-workspace-pill">Dzis: ${Number(stan.plannerZadan?.buckets?.dzis?.count || 0)}</span>`
      : "",
  ]
    .filter(Boolean)
    .join("");
  const listHtml = zadania.length
    ? zadania
        .map((task) => {
          const isUnread = !czyElementSzybkiegoPaneluJestPrzeczytany("tasks", task);
          return `
          <article class="quick-workspace-list-item ${isUnread ? "is-unread" : ""}">
            <div class="quick-workspace-list-item-top">
              <div class="quick-workspace-list-item-title">${bezpiecznyTekst(task.title || "(bez tytulu)")}</div>
              <div class="quick-workspace-list-item-top-badges">
                ${isUnread ? '<span class="quick-workspace-unread-dot" aria-hidden="true"></span>' : ""}
                <span class="status-badge ${klasaStatusuZadania(task.status, task.priority)}">${bezpiecznyTekst(formatujPriorytetZadania(task.priority))}</span>
              </div>
            </div>
            <div class="quick-workspace-list-item-meta">
              <span>${bezpiecznyTekst(formatujTypZadania(task.task_type))}</span>
              <span>${bezpiecznyTekst(formatujDateCzas(pobierzZakotwiczenieSzybkiegoKalendarza(task)))}</span>
            </div>
            <div class="quick-workspace-list-item-actions">
              <button type="button" class="secondary" data-quick-workspace-open-task="${task.task_id}" data-quick-workspace-open-source="tasks">Otworz</button>
            </div>
          </article>
        `;
        })
        .join("")
    : `<div class="empty-state">Brak aktywnych zadan do szybkiego podgladu.</div>`;
  return `
    <div class="quick-workspace-card">
      <div class="quick-workspace-range-bar">
        ${Object.entries(labels)
          .map(
            ([key, label]) =>
              `<button type="button" class="quick-workspace-range-button ${key === rangeCode ? "active" : ""}" data-quick-workspace-task-range="${key}">${bezpiecznyTekst(label)}</button>`
          )
          .join("")}
      </div>
      <div class="quick-workspace-pills">${pills}</div>
      <div class="quick-workspace-list">${listHtml}</div>
      <div class="filters-actions">
        <button type="button" class="secondary" data-quick-workspace-open-view="tasks">Otworz modul</button>
      </div>
    </div>
  `;
}

function zbudujSzybkiPanelDokumentowFirmowych() {
  if (!stan.biezacyUzytkownik) {
    return `<div class="empty-state">Zaloguj sie, aby zobaczyc dokumenty firmowe.</div>`;
  }
  if (!czyMoznaPodejrzecDokumentyFirmoweWSzybkimPanelu()) {
    return `<div class="empty-state">Wybierz organizacje i konto z dostepem do Asystenta Firmowego.</div>`;
  }
  const summary = stan.podsumowanieAktywnosciBazyWiedzy || {};
  const documents = pobierzSzybkieDokumentyFirmoweDoPanelu();
  const listHtml = documents.length
    ? documents
        .map((document) => `
          <article class="quick-workspace-list-item">
            <div class="quick-workspace-list-item-top">
              <div class="quick-workspace-list-item-title">${bezpiecznyTekst(document.title || "(bez tytulu)")}</div>
              <span class="status-badge ${typeof klasaStanuObieguDokumentuBazyWiedzy === "function" ? klasaStanuObieguDokumentuBazyWiedzy(document.business_status || "roboczy") : ""}">${bezpiecznyTekst(typeof formatujStanObieguDokumentuBazyWiedzy === "function" ? formatujStanObieguDokumentuBazyWiedzy(document.business_status || "roboczy") : (document.business_status || "roboczy"))}</span>
            </div>
            <div class="quick-workspace-list-item-meta">
              <span>${bezpiecznyTekst(document.library_path_label || "Bez folderu")}</span>
              <span>${bezpiecznyTekst(document.owner_user_label || document.reviewer_user_label || document.approver_user_label || "brak osoby")}</span>
            </div>
            <div class="quick-workspace-list-item-actions">
              <button type="button" class="secondary" data-quick-workspace-open-knowledge-document="${document.knowledge_document_id}">Otworz</button>
              ${
                typeof zbudujAkcjeOperacyjneDokumentuBazyWiedzy === "function"
                  ? zbudujAkcjeOperacyjneDokumentuBazyWiedzy(document, {
                      limit: 2,
                      compact: true,
                      includeOpen: false,
                      includeTask: true,
                    })
                  : ""
              }
            </div>
          </article>
        `)
        .join("")
    : `<div class="empty-state">Brak dokumentow czekajacych na reakcje. Gdy pojawi sie review, akceptacja albo Twoj draft, zobaczysz to tutaj.</div>`;
  const pills = [
    `<span class="quick-workspace-pill">Moja kolejka: ${Number(summary.my_attention_count || 0)}</span>`,
    `<span class="quick-workspace-pill">Do sprawdzenia: ${Number(summary.awaiting_review_count || 0)}</span>`,
    `<span class="quick-workspace-pill">Do akceptacji: ${Number(summary.awaiting_approval_count || 0)}</span>`,
    summary.unread_count ? `<span class="quick-workspace-pill">Nieprzeczytane: ${Number(summary.unread_count || 0)}</span>` : "",
  ]
    .filter(Boolean)
    .join("");
  return `
    <div class="quick-workspace-card">
      <div class="quick-workspace-pills">${pills}</div>
      <div class="quick-workspace-list">${listHtml}</div>
      <div class="filters-actions">
        <button type="button" class="secondary" data-quick-workspace-open-view="knowledge">Otworz modul</button>
      </div>
    </div>
  `;
}

function renderujSzybkiPanelPracy() {
  const launcher = document.getElementById("quick-workspace-launcher");
  const panel = document.getElementById("quick-workspace-panel");
  const subtitle = document.getElementById("quick-workspace-panel-subtitle");
  const content = document.getElementById("quick-workspace-content");
  const tabs = document.getElementById("quick-workspace-tabs");
  if (!launcher || !panel || !subtitle || !content || !tabs) {
    return;
  }

  const visible = Boolean(stan.biezacyUzytkownik);
  launcher.classList.toggle("hidden", !visible);
  if (!visible) {
    launcher.classList.remove("is-active");
    launcher.setAttribute("aria-expanded", "false");
    panel.classList.add("hidden");
    panel.setAttribute("aria-hidden", "true");
    content.innerHTML = `<div class="empty-state">Zaloguj sie, aby otworzyc szybki panel pracy.</div>`;
    renderujBadgeSzybkiegoPanelu();
    return;
  }

  const activeSection = pobierzAktywnaSekcjeSzybkiegoPanelu();
  const config = quickWorkspaceSectionConfig[activeSection] || quickWorkspaceSectionConfig["organization-note"];
  subtitle.textContent = config.subtitle;
  tabs.querySelectorAll("[data-quick-workspace-section]").forEach((button) => {
    const isActive = button.dataset.quickWorkspaceSection === activeSection;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-pressed", isActive ? "true" : "false");
  });

  launcher.classList.toggle("is-active", stan.szybkiPanelPracyOtwarty);
  launcher.setAttribute("aria-expanded", stan.szybkiPanelPracyOtwarty ? "true" : "false");
  panel.classList.toggle("hidden", !stan.szybkiPanelPracyOtwarty);
  panel.setAttribute("aria-hidden", stan.szybkiPanelPracyOtwarty ? "false" : "true");
  if (!stan.szybkiPanelPracyOtwarty) {
    renderujBadgeSzybkiegoPanelu();
    return;
  }

  if (activeSection === "organization-note") {
    content.innerHTML = zbudujSzybkiPanelNotatkiOrganizacji();
    renderujNotatkeOrganizacji(stan.notatkaOrganizacji);
  } else if (activeSection === "personal-note") {
    content.innerHTML = zbudujSzybkiPanelNotatkiOsobistej();
    renderujNotatkeOsobista(stan.notatkaOsobista);
  } else if (activeSection === "calendar") {
    content.innerHTML = zbudujSzybkiPanelKalendarza();
  } else if (activeSection === "knowledge") {
    content.innerHTML = zbudujSzybkiPanelDokumentowFirmowych();
  } else {
    content.innerHTML = zbudujSzybkiPanelZadan();
  }

  renderujBadgeSzybkiegoPanelu();
  window.requestAnimationFrame(() => ustawPozycjeSzybkiegoPaneluPracy());
}

function ustawPozycjeSzybkiegoPaneluPracy() {
  const launcher = document.getElementById("quick-workspace-launcher");
  const panel = document.getElementById("quick-workspace-panel");
  if (!launcher || !panel || panel.classList.contains("hidden")) {
    return;
  }
  const viewportWidth = window.innerWidth || document.documentElement.clientWidth || 0;
  const viewportHeight = window.innerHeight || document.documentElement.clientHeight || 0;
  if (!viewportWidth || !viewportHeight) {
    return;
  }
  const compactViewport = viewportWidth <= 760;
  const gutter = compactViewport ? 12 : 16;
  const preferredWidth = compactViewport ? 420 : 380;
  const maxUsableWidth = Math.max(0, viewportWidth - gutter * 2);
  const panelWidth = Math.max(
    Math.min(preferredWidth, maxUsableWidth),
    Math.min(220, maxUsableWidth || preferredWidth)
  );
  const launcherRect = launcher.getBoundingClientRect();
  const left = Math.min(
    Math.max(gutter, launcherRect.right - panelWidth),
    Math.max(gutter, viewportWidth - panelWidth - gutter)
  );
  const availableAbove = Math.max(220, launcherRect.top - gutter - 12);
  const availableBelow = Math.max(180, viewportHeight - launcherRect.bottom - gutter - 12);
  const preferAbove = availableAbove >= 300 || availableAbove >= availableBelow;
  panel.style.left = `${Math.round(left)}px`;
  panel.style.right = "auto";
  panel.style.width = `${Math.round(panelWidth)}px`;
  panel.style.maxWidth = `${Math.round(panelWidth)}px`;
  if (preferAbove) {
    panel.style.top = "auto";
    panel.style.bottom = `${Math.round(Math.max(gutter, viewportHeight - launcherRect.top + 12))}px`;
    panel.style.maxHeight = `${Math.round(Math.min(680, availableAbove))}px`;
  } else {
    panel.style.bottom = "auto";
    panel.style.top = `${Math.round(Math.max(gutter, launcherRect.bottom + 12))}px`;
    panel.style.maxHeight = `${Math.round(Math.min(680, availableBelow))}px`;
  }
}

async function zapewnijDaneSzybkiegoPanelu(sectionKey, { force = false } = {}) {
  if (sectionKey === "organization-note") {
    await wczytajNotatkeOrganizacji({ force });
    return;
  }
  if (sectionKey === "personal-note") {
    await wczytajNotatkeOsobista({ force });
    return;
  }
  if (sectionKey === "knowledge") {
    if (czyMoznaPodejrzecDokumentyFirmoweWSzybkimPanelu() && typeof wczytajBazeWiedzy === "function") {
      await wczytajBazeWiedzy();
    }
    return;
  }
  if ((sectionKey === "calendar" || sectionKey === "tasks") && czyMoznaKorzystacZMojejPracy()) {
    await Promise.all([
      wczytajZadania(),
      wczytajPlannerZadan(),
    ]);
  }
}

async function otworzSzybkiPanelPracy(sectionKey = null) {
  if (!stan.biezacyUzytkownik) {
    return;
  }
  if (sectionKey && quickWorkspaceSectionConfig[sectionKey]) {
    stan.szybkiPanelPracySekcja = sectionKey;
  }
  stan.szybkiPanelPracyOtwarty = true;
  renderujSzybkiPanelPracy();
  await zapewnijDaneSzybkiegoPanelu(pobierzAktywnaSekcjeSzybkiegoPanelu());
  renderujSzybkiPanelPracy();
  oznaczSekcjeSzybkiegoPaneluJakoOdczytana(pobierzAktywnaSekcjeSzybkiegoPanelu());
}

function zamknijSzybkiPanelPracy() {
  stan.szybkiPanelPracyOtwarty = false;
  renderujSzybkiPanelPracy();
}

async function przelaczSekcjeSzybkiegoPanelu(sectionKey) {
  if (!quickWorkspaceSectionConfig[sectionKey]) {
    return;
  }
  stan.szybkiPanelPracySekcja = sectionKey;
  renderujSzybkiPanelPracy();
  await zapewnijDaneSzybkiegoPanelu(sectionKey);
  renderujSzybkiPanelPracy();
  oznaczSekcjeSzybkiegoPaneluJakoOdczytana(sectionKey);
}

function czyWlascicielSystemuWTrybieGlobalnym() {
  return czyGlobalnyAdministrator() && !stan.wybranaOrganizacjaId;
}

function czyPokazacSzybkiKalendarz() {
  if (!stan.biezacyUzytkownik) {
    return false;
  }
  if (czyWlascicielSystemu()) {
    return true;
  }
  return czyMoznaKorzystacZMojejPracy() || czyMoznaOtworzycAsystentaSzefa();
}

function ustawMotywKontekstuInterfejsu() {
  const isGlobalContext = czyWlascicielSystemuWTrybieGlobalnym();
  document.body.classList.toggle("global-owner-context", isGlobalContext);
  const themeColor = document.querySelector('meta[name="theme-color"]');
  if (themeColor) {
    themeColor.setAttribute("content", isGlobalContext ? "#4a2516" : "#0b1f33");
  }
  const contextNode = document.getElementById("quick-calendar-context");
  const subtitleNode = document.getElementById("quick-calendar-subtitle");
  if (contextNode) {
    contextNode.textContent = isGlobalContext
      ? "Tryb globalny wĹ‚aĹ›ciciela systemu."
      : pobierzAktywnaOrganizacje()?.name
        ? `Kontekst: ${pobierzAktywnaOrganizacje().name}`
        : "PodglÄ…d dzisiejszych i najbliĹĽszych wpisĂłw.";
  }
  if (subtitleNode) {
    subtitleNode.textContent = isGlobalContext
      ? "W tym trybie widzisz system globalnie. Wybierz organizacjÄ™, aby podejrzeÄ‡ jej kalendarz pracy."
      : "NajbliĹĽsze wpisy z aktualnego kontekstu pracy.";
  }
}

function pobierzZakotwiczenieSzybkiegoKalendarza(task) {
  return (
    parsujDateKalendarza(task?.planner_anchor_at) ||
    parsujDateKalendarza(task?.due_at) ||
    parsujDateKalendarza(task?.remind_at) ||
    null
  );
}

function pobierzSzybkieWpisyKalendarza(rangeCode = "dzis") {
  const wszystkie = Array.isArray(stan.zadania) ? stan.zadania : [];
  const dzis = sklonujDateNaPolnoc(new Date());
  const jutro = dodajDniDoDaty(dzis, 1);
  const pojutrze = dodajDniDoDaty(dzis, 2);
  const zaTydzien = dodajDniDoDaty(dzis, 7);

  return wszystkie
    .filter((task) => {
      if (["zakonczone", "anulowane"].includes(String(task?.status || ""))) {
        return false;
      }
      const anchor = pobierzZakotwiczenieSzybkiegoKalendarza(task);
      if (!anchor) {
        return false;
      }
      if (rangeCode === "dzis") {
        return anchor >= dzis && anchor < jutro;
      }
      if (rangeCode === "jutro") {
        return anchor >= jutro && anchor < pojutrze;
      }
      return anchor >= dzis && anchor < dodajDniDoDaty(zaTydzien, 1);
    })
    .sort((left, right) => {
      const leftAnchor = pobierzZakotwiczenieSzybkiegoKalendarza(left)?.getTime() || 0;
      const rightAnchor = pobierzZakotwiczenieSzybkiegoKalendarza(right)?.getTime() || 0;
      return leftAnchor - rightAnchor;
    })
    .slice(0, 8);
}

function renderujSzybkiKalendarz() {
  const tools = document.getElementById("sidebar-quick-tools");
  const panel = document.getElementById("quick-calendar-panel");
  const toggle = document.getElementById("quick-calendar-toggle");
  const summary = document.getElementById("quick-calendar-summary");
  const list = document.getElementById("quick-calendar-list");
  if (!tools || !panel || !toggle || !summary || !list) {
    return;
  }

  const visible = czyPokazacSzybkiKalendarz();
  tools.classList.toggle("hidden", !visible);
  if (!visible) {
    stan.szybkiKalendarzOtwarty = false;
    panel.classList.add("hidden");
    panel.setAttribute("aria-hidden", "true");
    toggle.setAttribute("aria-expanded", "false");
    return;
  }

  panel.classList.toggle("hidden", !stan.szybkiKalendarzOtwarty);
  panel.setAttribute("aria-hidden", stan.szybkiKalendarzOtwarty ? "false" : "true");
  toggle.setAttribute("aria-expanded", stan.szybkiKalendarzOtwarty ? "true" : "false");

  panel.querySelectorAll("[data-quick-calendar-range]").forEach((button) => {
    const isActive = button.dataset.quickCalendarRange === stan.szybkiKalendarzZakres;
    button.classList.toggle("active", isActive);
    button.setAttribute("aria-pressed", isActive ? "true" : "false");
  });

  if (!stan.biezacyUzytkownik) {
    summary.innerHTML = "";
    list.innerHTML = `<div class="empty-state">Zaloguj siÄ™, aby podejrzeÄ‡ kalendarz.</div>`;
    return;
  }

  if (czyWlascicielSystemuWTrybieGlobalnym()) {
    summary.innerHTML = `<span class="quick-calendar-summary-pill">Tryb globalny wĹ‚aĹ›ciciela systemu</span>`;
    list.innerHTML = `<div class="empty-state">Wybierz konkretnÄ… organizacjÄ™, aby zobaczyÄ‡ jej najbliĹĽsze wpisy i terminy.</div>`;
    return;
  }

  if (!czyMoznaKorzystacZMojejPracy()) {
    summary.innerHTML = `<span class="quick-calendar-summary-pill">ModuĹ‚ zaleĹĽny od organizacji</span>`;
    list.innerHTML = `<div class="empty-state">Ten kontekst nie ma jeszcze aktywnego moduĹ‚u Asystent Szefa albo ta rola ma tylko podglÄ…d.</div>`;
    return;
  }

  const rangeCode = stan.szybkiKalendarzZakres || "dzis";
  const wpisy = pobierzSzybkieWpisyKalendarza(rangeCode);
  const zalegleCount = Number(stan.plannerZadan?.buckets?.zalegle?.count || 0);
  const aktywnaOrganizacja = pobierzAktywnaOrganizacje()?.name || stan.biezacyUzytkownik?.organization_name || "bieĹĽÄ…cej organizacji";
  const labels = {
    dzis: "DziĹ›",
    jutro: "Jutro",
    tydzien: "NajbliĹĽsze 7 dni",
  };

  summary.innerHTML = [
    `<span class="quick-calendar-summary-pill">${bezpiecznyTekst(labels[rangeCode] || "Kalendarz")}</span>`,
    `<span class="quick-calendar-summary-pill">Organizacja: ${bezpiecznyTekst(aktywnaOrganizacja)}</span>`,
    zalegleCount ? `<span class="quick-calendar-summary-pill">ZalegĹ‚e: ${zalegleCount}</span>` : "",
  ]
    .filter(Boolean)
    .join("");

  if (!wpisy.length) {
    list.innerHTML = `<div class="empty-state">Brak wpisĂłw w tym zakresie. To dobry znak albo spokojniejszy dzieĹ„.</div>`;
    return;
  }

  list.innerHTML = wpisy
    .map((task) => {
      const anchor = pobierzZakotwiczenieSzybkiegoKalendarza(task);
      const osoba = task.assigned_user_name || task.owner_user_name || "brak osoby";
      const calendar = task.calendar_name || "bez wybranego kalendarza";
      return `
        <article class="quick-calendar-entry" data-quick-calendar-task-id="${task.task_id}">
          <div class="quick-calendar-entry-top">
            <div class="quick-calendar-entry-title">${bezpiecznyTekst(task.title || "(bez tytulu)")}</div>
            <span class="status-badge ${klasaStatusuZadania(task.status, task.priority)}">${bezpiecznyTekst(formatujTypZadania(task.task_type))}</span>
          </div>
          <div class="quick-calendar-entry-meta">
            <span>${bezpiecznyTekst(formatujDateCzas(anchor))}</span>
            <span>${bezpiecznyTekst(formatujPriorytetZadania(task.priority))}</span>
          </div>
          <div class="quick-calendar-entry-meta">
            <span>${bezpiecznyTekst(osoba)}</span>
            <span>${bezpiecznyTekst(calendar)}</span>
          </div>
          <div class="quick-calendar-entry-actions">
            <span class="subtle-note">${bezpiecznyTekst(formatujWidocznoscZadania(task.visibility_scope))}</span>
            <button type="button" class="quick-calendar-entry-link" data-quick-calendar-open-task="${task.task_id}">OtwĂłrz</button>
          </div>
        </article>
      `;
    })
    .join("");
}

function zbudujAdresZOrganizacja(adres) {
  if (!stan.biezacyUzytkownik || !czyGlobalnyAdministrator() || !stan.wybranaOrganizacjaId) {
    return adres;
  }
  const separator = adres.includes("?") ? "&" : "?";
  return `${adres}${separator}organization_id=${encodeURIComponent(stan.wybranaOrganizacjaId)}`;
}

function zbudujAdresZOpcjonalnaOrganizacja(adres, organizationId = null) {
  const normalizedOrganizationId = String(organizationId || "").trim();
  if (!normalizedOrganizationId) {
    return adres;
  }
  const separator = adres.includes("?") ? "&" : "?";
  return `${adres}${separator}organization_id=${encodeURIComponent(normalizedOrganizationId)}`;
}

function zbudujOpcjeOrganizacjiDlaFormularzy() {
  const switcher = document.getElementById("organization-switcher");
  if (czyGlobalnyAdministrator()) {
    const aktywneOrganizacje = stan.organizacje.filter((organizacja) => organizacja.is_active);
    const opcje = [`<option value="">Wszystkie organizacje</option>`]
      .concat(
        aktywneOrganizacje.map(
          (organizacja) =>
            `<option value="${organizacja.organization_id}">${bezpiecznyTekst(organizacja.name)}</option>`
        )
      )
      .join("");
    switcher.innerHTML = opcje;
    switcher.value = stan.wybranaOrganizacjaId || "";
  } else {
    switcher.innerHTML = "";
  }
  ustawMotywKontekstuInterfejsu();
  renderujSzybkiKalendarz();

  const selectUzytkownika = document.getElementById("user-organization-id");
  if (czyGlobalnyAdministrator()) {
    selectUzytkownika.disabled = false;
    selectUzytkownika.innerHTML = [
      `<option value="">Brak przypisania (konto globalne)</option>`,
      ...stan.organizacje.map(
        (organizacja) =>
          `<option value="${organizacja.organization_id}">${bezpiecznyTekst(organizacja.name)}</option>`
      ),
    ].join("");
  } else {
    const nazwaOrganizacji = stan.biezacyUzytkownik?.organization_name || "Brak przypisania";
    const idOrganizacji = stan.biezacyUzytkownik?.organization_id || "";
    selectUzytkownika.innerHTML = `<option value="${bezpiecznyTekst(idOrganizacji)}">${bezpiecznyTekst(nazwaOrganizacji)}</option>`;
    selectUzytkownika.disabled = true;
  }

  odswiezOpcjeRolUzytkownikow();
}

function odswiezOpcjeRolUzytkownikow() {
  const roleSelect = document.getElementById("user-role");
  if (!roleSelect || !stan.meta?.roles) {
    return;
  }
  const obecnaWartosc = roleSelect.value;
  let roleOptions = stan.meta.roles;

  if (!czyWlascicielSystemu()) {
    roleOptions = roleOptions.filter((rola) => rola !== "system_owner");
  }
  if (!czyMoznaZarzadzacUzytkownikami()) {
    roleOptions = roleOptions.filter((rola) => rola === "guest");
  }

  roleSelect.innerHTML = roleOptions
    .map((rola) => `<option value="${rola}">${formatujRole(rola)}</option>`)
    .join("");
  roleSelect.value = roleOptions.includes(obecnaWartosc) ? obecnaWartosc : roleOptions[0] || "";
}

function wyczyscFiltryFaktur(przeladuj = true) {
  document.getElementById("invoice-filters").reset();
  odswiezPasekFiltrowFaktur();
  if (przeladuj) {
    wczytajFaktury().catch((error) => pokazPowiadomienie(error.message));
  }
}

function ustawWidocznoscFiltrowFaktur(czyRozwiniete) {
  stan.czyFiltryFakturRozwiniete = czyRozwiniete;
  const kontener = document.getElementById("invoice-filters-shell");
  const przycisk = document.getElementById("toggle-invoice-filters");
  kontener.classList.toggle("collapsed", !czyRozwiniete);
  przycisk.textContent = czyRozwiniete ? "ZwiĹ„ filtry" : "RozwiĹ„ filtry";
  przycisk.setAttribute("aria-expanded", czyRozwiniete ? "true" : "false");
}

function przelaczWidocznoscFiltrowFaktur() {
  ustawWidocznoscFiltrowFaktur(!stan.czyFiltryFakturRozwiniete);
}

function odswiezPasekFiltrowFaktur() {
  const kontener = document.getElementById("invoice-active-filters");
  const formularz = document.getElementById("invoice-filters");
  const dane = new FormData(formularz);
  const etykiety = {
    search: "Fraza",
    source: "ĹąrĂłdĹ‚o",
    status: "Status",
    workflow_state: "Obieg",
    duplicate_type: "Typ duplikatu",
    date_from: "Data od",
    date_to: "Data do",
    nip: "NIP",
    invoice_number: "Numer faktury",
    ksef_number: "Numer KSeF",
    contractor_id: "Kontrahent",
    assigned_user_id: "Odpowiedzialny",
  };

  const wpisy = [];
  for (const [key, value] of dane.entries()) {
    const wartosc = String(value).trim();
    if (!wartosc || !etykiety[key]) {
      continue;
    }
    let tekst = wartosc;
    if (key === "source") tekst = etykietyZrodel[wartosc] || wartosc;
    if (key === "workflow_state") tekst = formatujObiegFaktury(wartosc);
    if (key === "contractor_id") {
      const kontrahent = stan.kontrahenciWszyscy.find((item) => Number(item.contractor_id) === Number(wartosc));
      tekst = kontrahent ? kontrahent.name : wartosc;
    }
    if (key === "assigned_user_id") {
      const user = stan.uzytkownicyDoFaktur.find((item) => Number(item.user_id) === Number(wartosc));
      tekst = user ? user.display_name || user.login : wartosc;
    }
    wpisy.push(`<span class="filter-chip">${bezpiecznyTekst(etykiety[key])}: ${bezpiecznyTekst(tekst)}</span>`);
  }

  if (!wpisy.length) {
    kontener.innerHTML = "";
    kontener.classList.add("hidden");
    return;
  }

  kontener.classList.remove("hidden");
  kontener.innerHTML = `${wpisy.join("")}<button type="button" class="secondary" id="clear-active-invoice-filters">WyczyĹ›Ä‡ wszystkie filtry</button>`;
  document.getElementById("clear-active-invoice-filters")?.addEventListener("click", () => wyczyscFiltryFaktur(true));
}

function pobierzSzybkieWidokiFaktur() {
  const currentUserId = Number(stan.biezacyUzytkownik?.user_id || 0);
  return [
    {
      key: "my_invoices",
      title: "Moje faktury",
      description: "Faktury przypisane do Ciebie.",
      filters: currentUserId ? { assigned_user_id: String(currentUserId) } : {},
    },
    {
      key: "verification",
      title: "Do weryfikacji",
      description: "Sprawy wymagajace recznej decyzji.",
      filters: { status: "weryfikacja" },
    },
    {
      key: "duplicates",
      title: "Duplikaty",
      description: "Podejrzenia i pewne duplikaty.",
      filters: { duplicate_type: "podejrzenie" },
    },
    {
      key: "ready_for_handoff",
      title: "Gotowe do przekazania",
      description: "Faktury czekajace na kolejny etap.",
      filters: { workflow_state: "gotowa_do_przekazania" },
    },
    {
      key: "waiting_for_ksef",
      title: "Czeka na KSeF",
      description: "Dokumenty pomocnicze wymagajace potwierdzenia z KSeF.",
      filters: { status: "weryfikacja", source: "EMAIL" },
    },
  ];
}

function zbudujStanWidokuFaktur() {
  const form = document.getElementById("invoice-filters");
  if (!(form instanceof HTMLFormElement)) {
    return { filters: {} };
  }
  const formData = new FormData(form);
  const filters = {};
  for (const [key, value] of formData.entries()) {
    const normalizedValue = String(value).trim();
    if (normalizedValue) {
      filters[key] = normalizedValue;
    }
  }
  return { filters };
}

function zastosujStanWidokuFaktur(viewState, { reload = true } = {}) {
  const form = document.getElementById("invoice-filters");
  if (!(form instanceof HTMLFormElement)) {
    return Promise.resolve();
  }
  form.reset();
  const filters = viewState && typeof viewState === "object" && viewState.filters && typeof viewState.filters === "object"
    ? viewState.filters
    : {};
  Object.entries(filters).forEach(([key, value]) => {
    const field = form.elements.namedItem(key);
    if (field instanceof RadioNodeList) {
      field.value = String(value);
      return;
    }
    if (field instanceof HTMLInputElement || field instanceof HTMLSelectElement || field instanceof HTMLTextAreaElement) {
      field.value = String(value);
    }
  });
  odswiezPasekFiltrowFaktur();
  return reload ? wczytajFaktury() : Promise.resolve();
}

function wyczyscFormularzWidokuFaktur() {
  stan.invoiceSavedViewSelectedId = null;
  document.getElementById("invoice-saved-view-id").value = "";
  document.getElementById("invoice-saved-view-name").value = "";
  document.getElementById("invoice-saved-view-slug").value = "";
  document.getElementById("invoice-saved-view-description").value = "";
  document.getElementById("invoice-saved-view-shared").checked = true;
  document.getElementById("invoice-saved-view-default").checked = false;
}

function odswiezFormularzWidokuFaktur() {
  const selected = stan.invoiceSavedViewSelectedId
    ? stan.invoiceSavedViews.find((item) => Number(item.saved_view_id) === Number(stan.invoiceSavedViewSelectedId))
    : null;
  document.getElementById("invoice-saved-view-id").value = selected?.saved_view_id || "";
  document.getElementById("invoice-saved-view-name").value = selected?.view_name || "";
  document.getElementById("invoice-saved-view-slug").value = selected?.view_slug || "";
  document.getElementById("invoice-saved-view-description").value = selected?.description || "";
  document.getElementById("invoice-saved-view-shared").checked = Boolean(selected ? selected.is_shared : true);
  document.getElementById("invoice-saved-view-default").checked = Boolean(selected?.is_default);
}

function renderujWidokiFaktur() {
  const quickRoot = document.getElementById("invoice-saved-views-quick");
  const listRoot = document.getElementById("invoice-saved-views-list");
  const count = document.getElementById("invoice-saved-views-count");
  if (!quickRoot || !listRoot || !count) {
    return;
  }
  const canWrite = czyMoznaZapisywac();
  const presets = pobierzSzybkieWidokiFaktur();
  const views = Array.isArray(stan.invoiceSavedViews) ? stan.invoiceSavedViews : [];
  const selectedView = stan.invoiceSavedViewSelectedId
    ? views.find((item) => Number(item.saved_view_id) === Number(stan.invoiceSavedViewSelectedId))
    : null;
  count.textContent = `${views.length}`;
  quickRoot.innerHTML = `
    <div class="subtle-note">Szybkie wejscia</div>
    <div class="invoice-saved-views-quick-grid">
      ${presets
        .map(
          (preset) => `
            <button type="button" class="secondary invoice-saved-view-preset" data-invoice-preset-view="${bezpiecznyTekst(preset.key)}">
              <strong>${bezpiecznyTekst(preset.title)}</strong>
              <div class="subtle-note">${bezpiecznyTekst(preset.description)}</div>
            </button>
          `
        )
        .join("")}
    </div>
  `;
  listRoot.innerHTML = views.length
    ? views
        .map(
          (view) => `
            <article class="invoice-saved-view-item clickable ${Number(view.saved_view_id) === Number(stan.invoiceSavedViewSelectedId) ? "is-selected" : ""}" data-invoice-saved-view-id="${view.saved_view_id}">
              <div class="invoice-saved-view-row">
                <div>
                  <strong>${bezpiecznyTekst(view.view_name)}</strong>
                  <div class="muted">${bezpiecznyTekst(view.view_slug)} | ${bezpiecznyTekst(view.created_by_user_name || "-")}</div>
                </div>
                <div class="invoice-field-provenance-meta">
                  ${view.is_default ? zbudujBadgeStanu("Domyslny", "status-success") : ""}
                  ${view.is_shared ? zbudujBadgeStanu("Wspoldzielony", "status-warning") : zbudujBadgeStanu("Prywatny", "status-normal")}
                </div>
              </div>
              <div>${bezpiecznyTekst(view.description || "Brak opisu widoku.")}</div>
            </article>
          `
        )
        .join("")
    : `<div class="empty-state">Nie masz jeszcze zapisanych widokow faktur.</div>`;

  quickRoot.querySelectorAll("[data-invoice-preset-view]").forEach((button) => {
    button.addEventListener("click", async () => {
      const preset = presets.find((item) => item.key === button.dataset.invoicePresetView);
      if (!preset) return;
      try {
        await zastosujStanWidokuFaktur({ filters: preset.filters });
        pokazPowiadomienie(`Otworzono widok: ${preset.title}.`);
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
    });
  });

  listRoot.querySelectorAll("[data-invoice-saved-view-id]").forEach((item) => {
    item.addEventListener("click", () => {
      stan.invoiceSavedViewSelectedId = Number(item.dataset.invoiceSavedViewId);
      odswiezFormularzWidokuFaktur();
      renderujWidokiFaktur();
    });
  });

  const form = document.getElementById("invoice-saved-view-form");
  form?.querySelectorAll("input, textarea, button").forEach((element) => {
    if (!(element instanceof HTMLInputElement || element instanceof HTMLTextAreaElement || element instanceof HTMLButtonElement)) {
      return;
    }
    if (element.id === "invoice-saved-view-apply-selected") {
      element.disabled = !selectedView;
      return;
    }
    if (element.id === "invoice-saved-view-reset") {
      element.disabled = false;
      return;
    }
    if (element.id === "invoice-saved-view-delete") {
      element.disabled = !canWrite || !selectedView;
      return;
    }
    element.disabled = !canWrite;
  });
}

async function wczytajWidokiFaktur() {
  if (!stan.biezacyUzytkownik) {
    stan.invoiceSavedViews = [];
    renderujWidokiFaktur();
    return [];
  }
  const views = await api(zbudujAdresZOrganizacja("/api/dashboard/views?module_key=invoices&include_hidden=1"));
  stan.invoiceSavedViews = Array.isArray(views) ? views : [];
  if (
    stan.invoiceSavedViewSelectedId &&
    !stan.invoiceSavedViews.some((item) => Number(item.saved_view_id) === Number(stan.invoiceSavedViewSelectedId))
  ) {
    stan.invoiceSavedViewSelectedId = null;
  }
  odswiezFormularzWidokuFaktur();
  renderujWidokiFaktur();
  return stan.invoiceSavedViews;
}

async function zapiszWidokFaktur() {
  if (!czyMoznaZapisywac()) {
    throw new Error("To konto nie ma prawa zapisywania widokow faktur.");
  }
  const viewId = Number(document.getElementById("invoice-saved-view-id").value || 0);
  const payload = {
    module_key: "invoices",
    view_name: document.getElementById("invoice-saved-view-name").value.trim(),
    view_slug: document.getElementById("invoice-saved-view-slug").value.trim(),
    description: document.getElementById("invoice-saved-view-description").value.trim(),
    view_state: zbudujStanWidokuFaktur(),
    is_shared: document.getElementById("invoice-saved-view-shared").checked,
    is_default: document.getElementById("invoice-saved-view-default").checked,
  };
  const url = viewId ? zbudujAdresZOrganizacja(`/api/dashboard/views/${viewId}`) : zbudujAdresZOrganizacja("/api/dashboard/views");
  await api(url, {
    method: viewId ? "PATCH" : "POST",
    body: JSON.stringify(payload),
  });
  pokazPowiadomienie(viewId ? "Zaktualizowano widok faktur." : "Zapisano nowy widok faktur.");
  await wczytajWidokiFaktur();
}

async function zastosujWybranyWidokFaktur() {
  const selected = stan.invoiceSavedViewSelectedId
    ? stan.invoiceSavedViews.find((item) => Number(item.saved_view_id) === Number(stan.invoiceSavedViewSelectedId))
    : null;
  if (!selected) {
    throw new Error("Wybierz widok faktur do otwarcia.");
  }
  await zastosujStanWidokuFaktur(selected.view_state_json || {});
  pokazPowiadomienie(`Otworzono widok: ${selected.view_name}.`);
}

async function usunWidokFaktur() {
  if (!czyMoznaZapisywac()) {
    throw new Error("To konto nie ma prawa usuwania widokow faktur.");
  }
  const viewId = Number(document.getElementById("invoice-saved-view-id").value || stan.invoiceSavedViewSelectedId || 0);
  if (!viewId) {
    throw new Error("Wybierz widok faktur do usuniecia.");
  }
  await api(zbudujAdresZOrganizacja(`/api/dashboard/views/${viewId}`), { method: "DELETE" });
  pokazPowiadomienie("Usunieto zapisany widok faktur.");
  wyczyscFormularzWidokuFaktur();
  await wczytajWidokiFaktur();
}

function odswiezPasekFiltrowKontrahentow() {
  const kontener = document.getElementById("contractor-active-filters");
  const wpisy = [];

  if (stan.filtryKontrahentow.szukaj) {
    wpisy.push(`<span class="filter-chip">Fraza: ${bezpiecznyTekst(stan.filtryKontrahentow.szukaj)}</span>`);
  }
  if (stan.filtryKontrahentow.tylkoNowi) {
    wpisy.push(`<span class="filter-chip">Tylko nowi kontrahenci</span>`);
  }

  if (!wpisy.length) {
    kontener.innerHTML = "";
    kontener.classList.add("hidden");
    return;
  }

  kontener.classList.remove("hidden");
  kontener.innerHTML = `${wpisy.join("")}<button type="button" class="secondary" id="clear-contractor-filters">WyczyĹ›Ä‡ filtry</button>`;
  document.getElementById("clear-contractor-filters")?.addEventListener("click", async () => {
    stan.filtryKontrahentow.szukaj = "";
    stan.filtryKontrahentow.tylkoNowi = false;
    document.getElementById("contractor-search").value = "";
    await wczytajKontrahentow();
  });
}

function zbudujOpcjeUzytkownikowDoZadan() {
  const select = document.getElementById("task-filter-assigned-user");
  const obecnaWartosc = select.value;
  const opcje = [`<option value="">Wszyscy uzytkownicy</option>`]
    .concat(
      stan.uzytkownicyDoZadan.map((uzytkownik) => {
        const suffix = czyGlobalnyAdministrator() && uzytkownik.organization_name ? ` | ${uzytkownik.organization_name}` : "";
        return `<option value="${uzytkownik.user_id}">${bezpiecznyTekst(uzytkownik.display_name)}${bezpiecznyTekst(suffix)}</option>`;
      })
    )
    .join("");
  select.innerHTML = opcje;
  if (obecnaWartosc) {
    select.value = obecnaWartosc;
  }
}

function zbudujOpcjeOrganizacjiDlaKalendarza(selectedOrganizationId = null) {
  const aktywnaOrganizacjaId = Number(selectedOrganizationId || 0);
  const dostepneOrganizacje = czyGlobalnyAdministrator()
    ? stan.organizacje
    : stan.organizacje.filter((item) => Number(item.organization_id) === Number(stan.biezacyUzytkownik?.organization_id || 0));
  const opcje = ['<option value="">Bez powiazania</option>'];
  dostepneOrganizacje.forEach((organizacja) => {
    const zaznaczone = Number(organizacja.organization_id) === aktywnaOrganizacjaId ? "selected" : "";
    opcje.push(
      `<option value="${organizacja.organization_id}" ${zaznaczone}>${bezpiecznyTekst(organizacja.name)}</option>`
    );
  });
  return opcje.join("");
}

function dostepneRodzajeKalendarzyDlaBiezacegoUzytkownika() {
  if (!stan.biezacyUzytkownik && Array.isArray(stan.meta?.calendar_kinds)) {
    return stan.meta.calendar_kinds;
  }
  const ownerKinds = Array.isArray(stan.meta?.calendar_kinds_owner) ? stan.meta.calendar_kinds_owner : ["organizacja", "rodzinny", "prywatny", "inne"];
  const workerKinds = Array.isArray(stan.meta?.calendar_kinds_worker) ? stan.meta.calendar_kinds_worker : ["inne"];
  return czyMozeTworzycKalendarzePrywatneLubRodzinne() ? ownerKinds : workerKinds;
}

function zbudujOpcjeRodzajowKalendarza(selectedKind = "inne", includeSelectedKind = false) {
  const allowedKinds = dostepneRodzajeKalendarzyDlaBiezacegoUzytkownika();
  const kinds = [...allowedKinds];
  if (includeSelectedKind && selectedKind && !kinds.includes(selectedKind)) {
    kinds.unshift(selectedKind);
  }
  const resolvedKind = kinds.includes(selectedKind) ? selectedKind : kinds[0] || "inne";
  return kinds
    .map((kind) => {
      const selected = kind === resolvedKind ? "selected" : "";
      return `<option value="${bezpiecznyTekst(kind)}" ${selected}>${bezpiecznyTekst(formatujRodzajKalendarza(kind))}</option>`;
    })
    .join("");
}

function dostepneWidokiFokusuDlaBiezacegoUzytkownika() {
  if (!stan.biezacyUzytkownik && Array.isArray(stan.meta?.task_focus_views)) {
    return stan.meta.task_focus_views;
  }
  const managerViews = Array.isArray(stan.meta?.task_focus_views_manager)
    ? stan.meta.task_focus_views_manager
    : ["moj_dzien", "do_decyzji", "po_terminie", "czeka_na_kogos", "organizacyjne", "prywatne"];
  const workerViews = Array.isArray(stan.meta?.task_focus_views_worker)
    ? stan.meta.task_focus_views_worker
    : ["moj_dzien", "przypisane_do_mnie", "po_terminie", "czeka_na_kogos", "organizacyjne", "prywatne"];
  return czyMenedzerskiWidokAsystenta() ? managerViews : workerViews;
}

function odswiezOpcjeWidokowFokusuZadan() {
  const select = document.getElementById("task-filter-focus-view");
  if (!select) {
    return;
  }
  const obecnaWartosc = select.value || "";
  zbudujOpcje(select, dostepneWidokiFokusuDlaBiezacegoUzytkownika(), "Wszystkie widoki pracy", formatujWidokFokusuZadania);
  if (obecnaWartosc && Array.from(select.options).some((option) => option.value === obecnaWartosc)) {
    select.value = obecnaWartosc;
  }
}

function czyGoogleCalendarBezposrednioWlaczone() {
  return Boolean(stan.meta?.google_calendar_direct_enabled);
}

function domyslnyProviderKalendarzaUzytkownika() {
  if (czyGoogleCalendarBezposrednioWlaczone() && stan.statusPolaczeniaGoogleKalendarza?.connected) {
    return "google_api";
  }
  return "google_ics";
}

function zbudujOpcjeZewnetrznychKalendarzyGoogle(selectedId = "") {
  const zaznaczonyId = String(selectedId || "");
  if (!czyGoogleCalendarBezposrednioWlaczone()) {
    return `<option value="">Integracja bezposrednia nie jest skonfigurowana</option>`;
  }
  if (!stan.statusPolaczeniaGoogleKalendarza?.connected) {
    return `<option value="">Najpierw polacz konto Google</option>`;
  }
  if (!stan.zewnetrzneKalendarzeGoogle.length) {
    return `<option value="">Nie znaleziono kalendarzy Google</option>`;
  }
  return stan.zewnetrzneKalendarzeGoogle
    .map((kalendarz) => {
      const id = String(kalendarz.external_calendar_id || "");
      const zaznaczone = id === zaznaczonyId ? "selected" : "";
      const dodatki = [];
      if (kalendarz.is_primary) dodatki.push("glowny");
      if (kalendarz.access_role) dodatki.push(kalendarz.access_role);
      const suffix = dodatki.length ? ` | ${dodatki.join(", ")}` : "";
      return `<option value="${bezpiecznyTekst(id)}" ${zaznaczone}>${bezpiecznyTekst(
        kalendarz.external_calendar_name || id
      )}${bezpiecznyTekst(suffix)}</option>`;
    })
    .join("");
}

function renderujOnboardingGoogleKalendarza(status = null) {
  const container = document.getElementById("google-calendar-onboarding");
  if (!container) {
    return;
  }

  if (!czyGoogleCalendarBezposrednioWlaczone()) {
    container.innerHTML = `
      <div class="google-onboarding-card">
        <div class="preview-meta-heading">Szybki start</div>
        <div class="muted">Tryb bezposredni Google Calendar bedzie dostepny po ustawieniu danych OAuth i publicznego adresu aplikacji. Do tego czasu mozesz korzystac z trybu adresu URL (.ics).</div>
      </div>
    `;
    return;
  }

  const checks = Array.isArray(status?.setup_checks) ? status.setup_checks : [];
  const isReady = (code) => {
    const item = checks.find((entry) => entry.code === code);
    return Boolean(item?.ok);
  };
  const opisWyboruKalendarza = czyMozeTworzycKalendarzePrywatneLubRodzinne()
    ? "Przy dodawaniu wpisu mozesz juz wybrac kalendarz organizacji, prywatny albo rodzinny."
    : "Przy dodawaniu wpisu wybierzesz swoj kalendarz sluzbowy albo przypisany kalendarz organizacji.";
  const steps = [
    {
      label: "Konfiguracja systemu",
      description: isReady("oauth_ready")
        ? "Dane OAuth i publiczny adres sa gotowe."
        : "Brakuje danych OAuth albo publicznego adresu aplikacji.",
      done: isReady("oauth_ready"),
    },
    {
      label: "Polacz konto Google",
      description: status?.connected
        ? `Konto ${status.google_email || "Google"} jest juz polaczone.`
        : "Po polaczeniu pobierzesz swoje istniejace kalendarze Google.",
      done: Boolean(status?.connected),
    },
    {
      label: "Powiaz wlasne kalendarze",
      description: Number(status?.mapped_calendar_count || 0) > 0
        ? `Masz juz ${Number(status?.mapped_calendar_count || 0)} powiazane kalendarze.`
        : "Nazwij kalendarze w aplikacji i mapuj je do konkretnych kalendarzy Google.",
      done: Number(status?.mapped_calendar_count || 0) > 0,
    },
    {
      label: "Wybieraj kalendarz przy wpisie",
      description: Number(status?.mapped_calendar_count || 0) > 0
        ? opisWyboruKalendarza
        : "Ten krok bedzie gotowy po zapisaniu co najmniej jednego kalendarza.",
      done: Boolean(status?.ready_for_direct_sync),
    },
  ];

  container.innerHTML = `
    <div class="google-onboarding-card">
      <div class="task-save-impact-header">
        <div class="preview-meta-heading">Szybki start z Google Calendar</div>
        <span class="status-badge ${status?.ready_for_direct_sync ? "status-success" : "status-warning"}">
          ${status?.ready_for_direct_sync ? "Gotowe do pracy" : "Wymaga domkniecia"}
        </span>
      </div>
      <div class="google-onboarding-grid">
        ${steps
          .map(
            (step, index) => `
              <div class="google-onboarding-step ${step.done ? "is-done" : ""}">
                <span class="google-onboarding-step-index">${index + 1}</span>
                <div class="google-onboarding-step-copy">
                  <strong>${bezpiecznyTekst(step.label)}</strong>
                  <div class="muted">${bezpiecznyTekst(step.description)}</div>
                </div>
              </div>
            `
          )
          .join("")}
      </div>
    </div>
  `;
}

function renderujStatusPolaczeniaGoogleKalendarza(status = null) {
  stan.statusPolaczeniaGoogleKalendarza = status;
  const statusNode = document.getElementById("google-calendar-connection-status");
  const emailNode = document.getElementById("google-calendar-connection-email");
  const diagnosticsNode = document.getElementById("google-calendar-connection-diagnostics");
  const connectButton = document.getElementById("connect-google-calendar");
  const refreshButton = document.getElementById("refresh-google-calendars");
  const disconnectButton = document.getElementById("disconnect-google-calendar");
  const visibilityCheckbox = document.getElementById("google-calendar-visibility-confirmation");
  if (!statusNode || !emailNode) return;

  if (!czyGoogleCalendarBezposrednioWlaczone()) {
    statusNode.textContent = "Bezposrednie polaczenie Google Calendar nie jest jeszcze skonfigurowane w tym srodowisku.";
    emailNode.textContent = "Mozesz nadal korzystac z trybu adresu URL (.ics).";
    if (diagnosticsNode) {
      diagnosticsNode.innerHTML = `
        <div class="connection-diagnostic">
          <strong>Tryb bezposredni Google</strong>
          <span class="status-badge status-warning">Niegotowe</span>
        </div>
      `;
    }
    if (connectButton) connectButton.disabled = true;
    if (refreshButton) refreshButton.disabled = true;
    if (disconnectButton) disconnectButton.disabled = true;
    if (visibilityCheckbox) visibilityCheckbox.checked = false;
    renderujOnboardingGoogleKalendarza(status);
    return;
  }

  if (visibilityCheckbox) {
    visibilityCheckbox.checked = Boolean(status?.employee_visibility_confirmed);
  }

  if (status?.connected) {
    const mappedCount = Number(status.mapped_calendar_count || 0);
    statusNode.textContent = `Konto Google Calendar jest polaczone. Powiazane kalendarze: ${mappedCount}.`;
    emailNode.textContent = [
      status.google_email ? `Polaczone konto: ${status.google_email}` : "Konto Google jest polaczone.",
      status.assigned_calendar?.display_name
        ? `Przypisany kalendarz organizacji: ${status.assigned_calendar.display_name}`
        : "",
    ]
      .filter(Boolean)
      .join(" | ");
    if (connectButton) connectButton.disabled = true;
    if (refreshButton) refreshButton.disabled = false;
    if (disconnectButton) disconnectButton.disabled = false;
  } else if (status?.approval_pending) {
    statusNode.textContent = "Konto Google zapisano, ale czeka jeszcze na zatwierdzenie przez administratora.";
    emailNode.textContent = [
      status.google_email ? `Podlaczone konto: ${status.google_email}` : "",
      status.assigned_calendar?.display_name
        ? `Do czasu zatwierdzenia mozesz korzystac z przypisanego kalendarza organizacji: ${status.assigned_calendar.display_name}`
        : "",
    ]
      .filter(Boolean)
      .join(" | ") || "Po zatwierdzeniu zobaczysz swoje kalendarze Google w tym miejscu.";
    if (connectButton) connectButton.disabled = true;
    if (refreshButton) refreshButton.disabled = true;
    if (disconnectButton) disconnectButton.disabled = false;
  } else {
    statusNode.textContent = "Konto Google Calendar nie jest jeszcze polaczone.";
    emailNode.textContent = status?.assigned_calendar?.display_name
      ? `Masz przypisany kalendarz organizacji: ${status.assigned_calendar.display_name}. Nadal mozesz podlaczyc tez wlasne konto Google.`
      : czyMozeTworzycKalendarzePrywatneLubRodzinne()
        ? "Po polaczeniu wybierzesz jeden lub wiele istniejacych kalendarzy Google dla roznych kontekstow."
        : "Po polaczeniu wybierzesz swoje kalendarze sluzbowe Google lub skorzystasz z kalendarza organizacji.";
    if (connectButton) connectButton.disabled = Boolean(status?.connection_exists);
    if (refreshButton) refreshButton.disabled = true;
    if (disconnectButton) disconnectButton.disabled = !Boolean(status?.connection_exists);
  }

  if (diagnosticsNode) {
    const checks = Array.isArray(status?.setup_checks) ? status.setup_checks : [];
    diagnosticsNode.innerHTML = checks.length
      ? checks
          .map((item) => {
            const isOk = Boolean(item.ok);
            const details = String(item.details || "").trim();
            return `
              <div class="connection-diagnostic">
                <div>
                  <strong>${bezpiecznyTekst(item.label || item.code || "Stan konfiguracji")}</strong>
                  ${details ? `<div class="muted">${bezpiecznyTekst(details)}</div>` : ""}
                </div>
                <span class="status-badge ${isOk ? "status-success" : "status-warning"}">${isOk ? "OK" : "Brak"}</span>
              </div>
            `;
          })
          .join("")
      : `<div class="connection-diagnostic"><strong>Diagnostyka</strong><span class="status-badge status-warning">Brak danych</span></div>`;
  }
  renderujOnboardingGoogleKalendarza(status);
}

function renderujZewnetrzneKalendarzeGoogle(kalendarze) {
  stan.zewnetrzneKalendarzeGoogle = Array.isArray(kalendarze) ? kalendarze : [];
  const select = document.getElementById("user-calendar-external-id");
  if (!select) return;
  const currentValue = select.value;
  select.innerHTML = zbudujOpcjeZewnetrznychKalendarzyGoogle(currentValue);
  if (currentValue) {
    select.value = currentValue;
  }
}

function odswiezWidocznoscPolGoogleKalendarza() {
  const providerSelect = document.getElementById("user-calendar-provider");
  const externalSelect = document.getElementById("user-calendar-external-id");
  const externalWrapper = document.getElementById("user-calendar-external-field");
  if (!providerSelect || !externalSelect || !externalWrapper) return;
  const provider = providerSelect.value || domyslnyProviderKalendarzaUzytkownika();
  const isDirect = provider === "google_api";
  externalWrapper.classList.toggle("hidden", !isDirect);
  externalSelect.disabled = !isDirect || !stan.statusPolaczeniaGoogleKalendarza?.connected;
  providerSelect.querySelectorAll("option").forEach((option) => {
    if (option.value === "google_api") {
      option.disabled = !czyGoogleCalendarBezposrednioWlaczone();
    }
  });
  if (!isDirect) {
    externalSelect.value = "";
  } else {
    externalSelect.innerHTML = zbudujOpcjeZewnetrznychKalendarzyGoogle(externalSelect.value);
    if (!externalSelect.value && stan.zewnetrzneKalendarzeGoogle.length === 1) {
      externalSelect.value = String(stan.zewnetrzneKalendarzeGoogle[0].external_calendar_id || "");
    }
  }
}

function renderujKalendarzeUzytkownika(kalendarze) {
  stan.kalendarzeUzytkownika = kalendarze;
  document.getElementById("user-calendar-count").textContent = `${kalendarze.length} rekordow`;
  const body = document.getElementById("user-calendar-table-body");
  if (!kalendarze.length) {
    body.innerHTML = `<tr><td colspan="9">${
      czyMozeTworzycKalendarzePrywatneLubRodzinne()
        ? "Nie masz jeszcze zadnego kalendarza."
        : "Nie masz jeszcze wlasnego kalendarza sluzbowego ani przypisanego kalendarza organizacji."
    }</td></tr>`;
    return;
  }
  body.innerHTML = kalendarze
    .map(
      (item) => `
        <tr class="clickable" data-user-calendar-id="${item.user_calendar_id}">
          <td>${item.user_calendar_id}</td>
          <td>${formatujWartosc(item.display_name)}</td>
          <td>${formatujWartosc(item.access_mode_label || "Wlasny kalendarz")}</td>
          <td>${formatujRodzajKalendarza(item.calendar_kind)}</td>
          <td>${formatujNazweOrganizacji(item.linked_organization_name)}</td>
          <td>${Number(item.default_duration_minutes || 60)} min</td>
          <td>${formatujWartosc(item.provider_label || item.provider)}</td>
          <td>${item.is_active ? '<span class="status-badge status-success">Aktywny</span>' : '<span class="status-badge status-danger">Nieaktywny</span>'}</td>
          <td>
            ${
              item.provider === "google_api"
                ? item.external_calendar_name
                  ? `<strong>${formatujWartosc(item.external_calendar_name)}</strong><div class="muted">${bezpiecznyTekst(
                      item.external_calendar_timezone || "Europe/Warsaw"
                    )}</div>`
                  : '<span class="muted">Wybierz docelowy kalendarz Google.</span>'
                : item.feed_url
                  ? `<button type="button" class="secondary small-action" data-copy-calendar-url="${bezpiecznyTekst(item.feed_url)}">Kopiuj adres</button>`
                  : '<span class="muted">Adres pojawi sie po wdrozeniu lub ustawieniu publicznego adresu.</span>'
            }
          </td>
        </tr>
      `
    )
    .join("");

  body.querySelectorAll("[data-user-calendar-id]").forEach((row) => {
    row.addEventListener("click", () => {
      const item = stan.kalendarzeUzytkownika.find(
        (calendar) => Number(calendar.user_calendar_id) === Number(row.dataset.userCalendarId)
      );
      if (item) {
        wypelnijFormularzKalendarzaUzytkownika(item);
      }
    });
  });

  body.querySelectorAll("[data-copy-calendar-url]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      try {
        await navigator.clipboard.writeText(button.dataset.copyCalendarUrl);
        pokazPowiadomienie("Skopiowano adres kalendarza.");
      } catch (error) {
        pokazPowiadomienie("Nie udalo sie skopiowac adresu kalendarza.");
      }
    });
  });
}

function ustawStanFormularzaKalendarzaUzytkownika(kalendarz = null) {
  const form = document.getElementById("user-calendar-form");
  const note = document.getElementById("user-calendar-access-note");
  const deleteButton = document.getElementById("delete-user-calendar-button");
  const saveButton = document.querySelector('#user-calendar-form button[type="submit"]');
  const editableFieldIds = [
    "user-calendar-display-name",
    "user-calendar-provider",
    "user-calendar-kind",
    "user-calendar-linked-organization",
    "user-calendar-external-id",
    "user-calendar-default-duration",
    "user-calendar-description",
    "user-calendar-active",
  ];
  const accessMode = String(kalendarz?.access_mode || "owner");
  const isAssigned = accessMode === "assigned";
  form.dataset.calendarAccessMode = accessMode;
  editableFieldIds.forEach((fieldId) => {
    const field = document.getElementById(fieldId);
    if (field) {
      field.disabled = isAssigned;
    }
  });
  if (saveButton) {
    saveButton.disabled = isAssigned;
  }
  if (deleteButton) {
    deleteButton.disabled = isAssigned;
    deleteButton.classList.toggle("hidden", !kalendarz || isAssigned);
  }
  if (note) {
    if (isAssigned) {
      note.textContent =
        "To jest przypisany kalendarz organizacji. Zmiany wprowadza Administrator organizacji albo Wlasciciel systemu.";
      note.classList.remove("hidden");
    } else if (!czyMozeTworzycKalendarzePrywatneLubRodzinne()) {
      note.textContent =
        "Na tym koncie mozesz dodawac wlasne kalendarze sluzbowe. Kalendarze organizacji, prywatne i rodzinne zaklada Administrator organizacji albo Wlasciciel systemu.";
      note.classList.remove("hidden");
    } else {
      note.textContent = "";
      note.classList.add("hidden");
    }
  }
}

function wypelnijFormularzKalendarzaUzytkownika(kalendarz) {
  const accessMode = String(kalendarz.access_mode || "owner");
  document.getElementById("user-calendar-id").value = kalendarz.user_calendar_id || "";
  document.getElementById("user-calendar-display-name").value = kalendarz.display_name || "";
  document.getElementById("user-calendar-provider").value = kalendarz.provider || domyslnyProviderKalendarzaUzytkownika();
  document.getElementById("user-calendar-kind").innerHTML = zbudujOpcjeRodzajowKalendarza(
    kalendarz.calendar_kind || "inne",
    accessMode === "assigned"
  );
  document.getElementById("user-calendar-kind").value = kalendarz.calendar_kind || "inne";
  document.getElementById("user-calendar-linked-organization").innerHTML = zbudujOpcjeOrganizacjiDlaKalendarza(
    kalendarz.linked_organization_id
  );
  document.getElementById("user-calendar-linked-organization").value = kalendarz.linked_organization_id || "";
  document.getElementById("user-calendar-external-id").innerHTML = zbudujOpcjeZewnetrznychKalendarzyGoogle(
    kalendarz.external_calendar_id || ""
  );
  document.getElementById("user-calendar-external-id").value = kalendarz.external_calendar_id || "";
  document.getElementById("user-calendar-default-duration").value = kalendarz.default_duration_minutes || 60;
  document.getElementById("user-calendar-description").value = kalendarz.description || "";
  document.getElementById("user-calendar-active").value = kalendarz.is_active ? "1" : "0";
  document.getElementById("user-calendar-form-title").textContent =
    String(kalendarz.access_mode || "owner") === "assigned"
      ? `Kalendarz #${kalendarz.user_calendar_id} (przypisany)`
      : `Kalendarz #${kalendarz.user_calendar_id}`;
  ustawStanFormularzaKalendarzaUzytkownika(kalendarz);
  odswiezWidocznoscPowiazanejOrganizacjiKalendarza();
}

function wyczyscFormularzKalendarzaUzytkownika() {
  document.getElementById("user-calendar-id").value = "";
  document.getElementById("user-calendar-display-name").value = "";
  document.getElementById("user-calendar-provider").value = domyslnyProviderKalendarzaUzytkownika();
  document.getElementById("user-calendar-kind").innerHTML = zbudujOpcjeRodzajowKalendarza("inne");
  document.getElementById("user-calendar-kind").value = "inne";
  document.getElementById("user-calendar-linked-organization").innerHTML = zbudujOpcjeOrganizacjiDlaKalendarza();
  document.getElementById("user-calendar-linked-organization").value = "";
  document.getElementById("user-calendar-external-id").innerHTML = zbudujOpcjeZewnetrznychKalendarzyGoogle();
  document.getElementById("user-calendar-external-id").value = "";
  document.getElementById("user-calendar-default-duration").value = "60";
  document.getElementById("user-calendar-description").value = "";
  document.getElementById("user-calendar-active").value = "1";
  document.getElementById("user-calendar-form-title").textContent = "Nowy kalendarz";
  ustawStanFormularzaKalendarzaUzytkownika(null);
  odswiezWidocznoscPowiazanejOrganizacjiKalendarza();
}

function odswiezWidocznoscPowiazanejOrganizacjiKalendarza() {
  const rodzaj = document.getElementById("user-calendar-kind");
  const poleOrganizacji = document.getElementById("user-calendar-linked-organization");
  if (!rodzaj || !poleOrganizacji) return;
  odswiezWidocznoscPolGoogleKalendarza();
  const accessMode = document.getElementById("user-calendar-form")?.dataset.calendarAccessMode || "owner";
  const allowedKinds = dostepneRodzajeKalendarzyDlaBiezacegoUzytkownika();
  if (accessMode !== "assigned" && !allowedKinds.includes(rodzaj.value)) {
    rodzaj.innerHTML = zbudujOpcjeRodzajowKalendarza("inne");
    rodzaj.value = allowedKinds[0] || "inne";
  }
  const kind = rodzaj.value || "inne";
  const wrapper = poleOrganizacji.closest(".field");
  if (wrapper) {
    wrapper.classList.toggle("hidden", kind !== "organizacja");
  }
  if (kind !== "organizacja") {
    poleOrganizacji.value = "";
    return;
  }
  const aktywneOpcje = Array.from(poleOrganizacji.options).filter((option) => option.value);
  if (!poleOrganizacji.value && aktywneOpcje.length === 1) {
    poleOrganizacji.value = aktywneOpcje[0].value;
  }
}

function renderujUstawieniaPrzypomnienUzytkownika(preferences) {
  stan.ustawieniaPrzypomnienUzytkownika = preferences;
  document.getElementById("user-own-telegram-reminders-enabled").checked = Boolean(
    preferences?.telegram_reminders_enabled
  );
  const browserNotifications = document.getElementById("user-own-browser-reminders-enabled");
  if (browserNotifications) {
    browserNotifications.checked = Boolean(preferences?.browser_notifications_enabled);
  }
  document.getElementById("user-own-quiet-hours-start").value = preferences?.quiet_hours_start || "";
  document.getElementById("user-own-quiet-hours-end").value = preferences?.quiet_hours_end || "";
  document.getElementById("user-own-repeat-interval").value = preferences?.repeat_interval_minutes ?? 0;
  renderujStanAlertowPrzegladarki();
}

function stanAlertowPrzegladarki() {
  if (!("Notification" in window)) {
    return { etykieta: "Ta przegladarka nie obsluguje alertow przegladarki.", aktywne: false, wspierane: false };
  }
  if (!stan.alertyPrzegladarkiWlaczone) {
    return { etykieta: "Alerty przegladarki sa wylaczone w tym panelu.", aktywne: false, wspierane: true };
  }
  if (Notification.permission === "granted") {
    return { etykieta: "Alerty przegladarki sa wlaczone.", aktywne: true, wspierane: true };
  }
  if (Notification.permission === "denied") {
    return { etykieta: "Przegladarka blokuje alerty. Zmien to w ustawieniach strony.", aktywne: false, wspierane: true };
  }
  return { etykieta: "Kliknij przycisk, aby zezwolic na alerty przegladarki.", aktywne: false, wspierane: true };
}

function renderujStanAlertowPrzegladarki() {
  const status = document.getElementById("browser-notification-status");
  if (!status) return;
  const stanAlertu = stanAlertowPrzegladarki();
  status.textContent = stanAlertu.etykieta;
  const wlacz = document.getElementById("enable-browser-notifications");
  const wylacz = document.getElementById("disable-browser-notifications");
  const test = document.getElementById("test-browser-notification");
  if (wlacz) wlacz.disabled = !stanAlertu.wspierane || stanAlertu.aktywne;
  if (wylacz) wylacz.disabled = !stanAlertu.wspierane || !stan.alertyPrzegladarkiWlaczone;
  if (test) test.disabled = !stanAlertu.wspierane || Notification.permission !== "granted" || !stan.alertyPrzegladarkiWlaczone;
}

async function wlaczAlertyPrzegladarki() {
  if (!("Notification" in window)) {
    throw new Error("Ta przegladarka nie obsluguje alertow przegladarki.");
  }
  stan.audioAlertUnlocked = true;
  const permission = await Notification.requestPermission();
  if (permission !== "granted") {
    throw new Error("Przegladarka nie przyznala zgody na alerty.");
  }
  stan.alertyPrzegladarkiWlaczone = true;
  window.localStorage.setItem("casi-browser-alerts-enabled", "1");
  renderujStanAlertowPrzegladarki();
}

function wylaczAlertyPrzegladarki() {
  stan.alertyPrzegladarkiWlaczone = false;
  window.localStorage.setItem("casi-browser-alerts-enabled", "0");
  renderujStanAlertowPrzegladarki();
}

function odtworzDzwiekAlertu() {
  if (!stan.audioAlertUnlocked || !window.AudioContext) return;
  try {
    const audioContext = new window.AudioContext();
    const oscillator = audioContext.createOscillator();
    const gain = audioContext.createGain();
    oscillator.type = "sine";
    oscillator.frequency.value = 880;
    gain.gain.value = 0.04;
    oscillator.connect(gain);
    gain.connect(audioContext.destination);
    oscillator.start();
    oscillator.stop(audioContext.currentTime + 0.18);
    oscillator.onended = () => {
      audioContext.close().catch(() => {});
    };
  } catch (error) {
    // Dzwiek jest dodatkiem; pomijamy cicho, jesli przegladarka go blokuje.
  }
}

function przypomnienieJestWymagalne(task) {
  if (!task?.remind_at) return false;
  if (["zakonczone", "anulowane"].includes(String(task.status || ""))) return false;
  const remindAt = new Date(task.remind_at);
  if (Number.isNaN(remindAt.getTime())) return false;
  return remindAt.getTime() <= Date.now();
}

function kluczAlertuPrzegladarki(task) {
  return `${task.task_id}:${task.remind_at || ""}:${task.status || ""}:${task.reminder_last_error || ""}`;
}

function pokazAlertPrzegladarki(task) {
  const tytul = `Przypomnienie: ${task.title || "Wpis"}`;
  const opis = [
    formatujTypZadania(task.task_type),
    task.organization_name ? `Organizacja: ${task.organization_name}` : null,
    task.calendar_name ? `Kalendarz: ${task.calendar_name}` : null,
    task.due_at ? `Termin: ${task.due_at}` : null,
  ]
    .filter(Boolean)
    .join(" | ");
  const notification = new Notification(tytul, {
    body: opis || "Masz nowe przypomnienie w systemie.",
    tag: `task-reminder-${task.task_id}`,
    renotify: true,
  });
  notification.onclick = () => {
    window.focus();
    ustawWidok("tasks");
    if (task.task_id) {
      wczytajSzczegolyZadania(task.task_id).catch(() => {});
    }
    notification.close();
  };
  odtworzDzwiekAlertu();
}

function obsluzAlertyPrzegladarki(reminders) {
  if (!stan.alertyPrzegladarkiWlaczone || !("Notification" in window) || Notification.permission !== "granted") {
    return;
  }
  reminders
    .filter((task) => przypomnienieJestWymagalne(task))
    .forEach((task) => {
      const klucz = kluczAlertuPrzegladarki(task);
      if (stan.pokazaneAlertyPrzegladarki.has(klucz)) {
        return;
      }
      stan.pokazaneAlertyPrzegladarki.add(klucz);
      pokazAlertPrzegladarki(task);
    });
}

function renderujStatusPrzypomnien() {
  const statusNode = document.getElementById("task-reminder-dispatch-status");
  const dispatchButton = document.getElementById("dispatch-task-reminders");
  if (!statusNode || !dispatchButton) {
    return;
  }

  const status = stan.taskReminderStatus || stan.meta?.task_reminder_status || {};
  stan.taskReminderStatus = status;
  const enabled = Boolean(status.enabled);
  const retryMinutes = Number(status.retry_minutes || 15);
  const channel = String(status.delivery_channel || "").trim();
  const channelLabel = channel === "telegram" ? "Telegram" : channel || "brak kanaĹ‚u";
  const queue = status.queue || {};
  const total = Number(queue.total || 0);
  const due = Number(queue.due || 0);
  const scheduled = Number(queue.scheduled || 0);
  const processing = Number(queue.processing || 0);
  const failed = Number(queue.failed || 0);
  const sent = Number(queue.sent || 0);
  const cancelled = Number(queue.cancelled || 0);
  const staleProcessingCount = Array.isArray(stan.taskReminderOutbox)
    ? stan.taskReminderOutbox.filter((item) => czyWpisOutboxaZawieszony(item, Number(status.processing_timeout_minutes || 10))).length
    : 0;
  const hasSession = Boolean(stan.biezacyUzytkownik);
  if (enabled) {
    const queueParts = [];
    queueParts.push(`outbox: ${total} wpisow`);
    queueParts.push(`${due} zaleglych`);
    queueParts.push(`${scheduled} zaplanowanych`);
    queueParts.push(`${processing} w przetwarzaniu`);
    queueParts.push(`${failed} bledow`);
    queueParts.push(`${sent} wyslanych`);
    if (cancelled > 0) {
      queueParts.push(`${cancelled} anulowanych`);
    }
    const warning = failed > 0
      ? ` Uwaga: ${failed} wpisow wymaga sprawdzenia.`
      : staleProcessingCount > 0
        ? ` Uwaga: ${staleProcessingCount} wpisow wyglada na zawieszone.`
      : processing > 0
        ? ` ${processing} wpisow jest teraz przetwarzanych.`
        : "";
    statusNode.textContent = `Kolejka przypomnien dziala w tle przez ${channelLabel}. ${queueParts.join(", ")}. Retry po bledzie: co ${retryMinutes} min.${warning}`;
  } else {
    statusNode.textContent = "Automatyczna wysylka jest teraz wylaczona. Przypomnienia nie beda sie wysylaly do czasu wlaczenia Telegrama.";
  }

  const canDispatch = hasSession && czyMoznaZapisywac() && enabled;
  dispatchButton.disabled = !canDispatch;
  dispatchButton.title = !hasSession
    ? "Zaloguj sie, aby uruchomic dispatcher przypomnien."
    : enabled
      ? canDispatch
        ? ""
        : "Ta rola nie moze wymuszac wysylki przypomnien."
      : "Wlacz Telegram, aby automatyczna wysylka przypomnien byla aktywna.";
  renderujPanelOutboxaPrzypomnien();
}

async function odswiezAlertyPrzegladarki() {
  if (!stan.biezacyUzytkownik || !stan.alertyPrzegladarkiWlaczone) {
    return;
  }
  try {
    const snapshot = await api(zbudujAdresZOrganizacja("/api/dashboard"));
    obsluzAlertyPrzegladarki(snapshot.active_reminders || []);
  } catch (error) {
    // Nie przerywamy pracy panelu przez chwilowy brak mozliwosci odswiezenia alertow.
  }
}

function uruchomPollingAlertowPrzegladarki() {
  if (stan.przypomnieniaPollingId) {
    window.clearInterval(stan.przypomnieniaPollingId);
  }
  if (!stan.biezacyUzytkownik) {
    stan.przypomnieniaPollingId = null;
    return;
  }
  stan.przypomnieniaPollingId = window.setInterval(() => {
    odswiezAlertyPrzegladarki().catch(() => {});
    wczytajStatusPrzypomnien().catch(() => {});
  }, 60000);
}

function pobierzWlascicielaWpisu(task = null) {
  return Number(task?.owner_user_id || stan.biezacyUzytkownik?.user_id || 0);
}

function pobierzWybraneIdWidocznosciZadania() {
  return Array.from(document.querySelectorAll('input[name="task-visible-user"]:checked')).map((element) =>
    Number(element.value)
  );
}

function pobierzZakresWidocznosciZadania() {
  const zaznaczone = document.querySelector('input[name="task-visibility-scope"]:checked');
  return zaznaczone ? zaznaczone.value : "prywatne";
}

function ustawZakresWidocznosciZadania(scope) {
  document.querySelectorAll('input[name="task-visibility-scope"]').forEach((element) => {
    element.checked = element.value === scope;
  });
}

function pobierzSugerowanyKalendarzDlaAktywnejOrganizacji() {
  const organizationId = Number(stan.wybranaOrganizacjaId || stan.biezacyUzytkownik?.organization_id || 0);
  if (!organizationId) return null;
  const dopasowany = stan.kalendarzeUzytkownika.find(
    (item) => item.is_active && Number(item.linked_organization_id) === organizationId
  );
  return dopasowany ? Number(dopasowany.user_calendar_id) : null;
}

function uzupelnijCzasZadanZKalendarza() {
  const selectKalendarza = document.getElementById("task-calendar-id");
  const poleCzasu = document.getElementById("task-calendar-duration");
  if (!selectKalendarza || !poleCzasu) return;
  const selectedCalendarId = Number(selectKalendarza.value || 0);
  if (!selectedCalendarId) return;
  poleCzasu.value = String(pobierzDomyslnyCzasKalendarza(selectedCalendarId));
}

function zbudujPrzelacznikWidocznosci(scope, disabled = false) {
  const opcje = stan.meta?.task_visibility_scopes || ["prywatne", "wybrane_osoby", "organizacja"];
  return `
    <div class="scope-toggle" id="task-visibility-scope-box">
      ${opcje
        .map((item) => {
          const aktywna = item === scope;
          return `
            <label class="scope-option ${aktywna ? "active" : ""}">
              <input type="radio" name="task-visibility-scope" value="${item}" ${aktywna ? "checked" : ""} ${disabled ? "disabled" : ""} />
              <span>${formatujWidocznoscZadania(item)}</span>
            </label>
          `;
        })
        .join("")}
    </div>
  `;
}

function zbudujListeWidocznosciUzytkownikow(task = null, detail = null, disabled = false) {
  const ownerUserId = pobierzWlascicielaWpisu(task);
  const zaznaczoneId = new Set((detail?.visible_users || task?.visible_users || []).map((item) => Number(item.user_id)));
  const dostepniUzytkownicy = stan.uzytkownicyDoZadan.filter((uzytkownik) => Number(uzytkownik.user_id) !== ownerUserId);

  if (!dostepniUzytkownicy.length) {
    return `<div class="empty-state">Brak innych uzytkownikow w tej organizacji.</div>`;
  }

  return `
    <div class="checkbox-list" id="task-visible-users-list">
      ${dostepniUzytkownicy
        .map((uzytkownik) => {
          const zaznaczone = zaznaczoneId.has(Number(uzytkownik.user_id)) ? "checked" : "";
          const suffix = czyGlobalnyAdministrator() && uzytkownik.organization_name ? ` | ${uzytkownik.organization_name}` : "";
          return `
            <label class="checkbox-card">
              <input type="checkbox" name="task-visible-user" value="${uzytkownik.user_id}" ${zaznaczone} ${disabled ? "disabled" : ""} />
              <span>
                <strong>${bezpiecznyTekst(uzytkownik.display_name)}</strong>
                <div class="muted">${bezpiecznyTekst(uzytkownik.login)}${bezpiecznyTekst(suffix)}</div>
              </span>
            </label>
          `;
        })
        .join("")}
    </div>
  `;
}

function odswiezWidocznoscFormularzaZadania() {
  const zakres = pobierzZakresWidocznosciZadania();
  const poleWybranychOsob = document.getElementById("task-visible-users-field");
  const notatka = document.getElementById("task-visibility-note");
  const selectPrzypisania = document.getElementById("task-assigned-user");
  const ownerUserId = pobierzWlascicielaWpisu();

  document.querySelectorAll(".scope-option").forEach((element) => {
    const input = element.querySelector('input[name="task-visibility-scope"]');
    element.classList.toggle("active", Boolean(input?.checked));
  });

  if (poleWybranychOsob) {
    poleWybranychOsob.classList.toggle("hidden", zakres !== "wybrane_osoby");
  }

  if (notatka) {
    if (!czyMoznaPrzypisywacZadania()) {
      notatka.textContent = "Ta rola nie zmienia przypisania ani widocznosci wpisu. Te pola ustawia operator, koordynator, administrator organizacji albo wlasciciel systemu.";
    } else if (zakres === "prywatne") {
      notatka.textContent = "Wpis widzi tylko wlasciciel. Prywatny wpis mozna przypisac tylko sobie.";
    } else if (zakres === "wybrane_osoby") {
      notatka.textContent = "Wpis widzi wlasciciel oraz wskazane osoby z tej samej organizacji.";
    } else {
      notatka.textContent = "Wpis widza wszyscy uzytkownicy tej organizacji.";
    }
  }

  if (zakres === "prywatne" && selectPrzypisania && selectPrzypisania.value && Number(selectPrzypisania.value) !== ownerUserId) {
    selectPrzypisania.value = "";
  }
  odswiezWidocznoscPolCyklicznosciZadania();
}

function odswiezPasekFiltrowZadan() {
  const kontener = document.getElementById("task-active-filters");
  const formularz = document.getElementById("task-filters");
  const dane = new FormData(formularz);
    const etykiety = {
      search: "Fraza",
      task_type: "Typ",
      status: "Status",
      priority: "Priorytet",
      focus_view: "Widok pracy",
      recurrence_pattern: "Cyklicznosc",
      assigned_user_id: "Przypisano",
      due_from: "Termin od",
      due_to: "Termin do",
      remind_from: "Przypomnienie od",
      remind_to: "Przypomnienie do",
      due_reminders_only: "Widok",
    };

  const wpisy = [];
  for (const [key, value] of dane.entries()) {
    const wartosc = String(value).trim();
    if (!wartosc || !etykiety[key]) {
      continue;
    }
    let tekst = wartosc;
    if (key === "task_type") tekst = formatujTypZadania(wartosc);
    if (key === "status") tekst = formatujStatusZadania(wartosc);
    if (key === "priority") tekst = formatujPriorytetZadania(wartosc);
    if (key === "focus_view") tekst = formatujWidokFokusuZadania(wartosc);
    if (key === "recurrence_pattern") tekst = formatujCyklicznoscZadania(wartosc);
    if (key === "due_reminders_only") tekst = "Tylko aktywne przypomnienia";
    if (key === "assigned_user_id") {
      const uzytkownik = stan.uzytkownicyDoZadan.find((item) => Number(item.user_id) === Number(wartosc));
      tekst = uzytkownik ? uzytkownik.display_name : wartosc;
    }
    wpisy.push(`<span class="filter-chip">${bezpiecznyTekst(etykiety[key])}: ${bezpiecznyTekst(tekst)}</span>`);
  }

  if (!wpisy.length) {
    kontener.innerHTML = "";
    kontener.classList.add("hidden");
    return;
  }

  kontener.classList.remove("hidden");
  kontener.innerHTML = `${wpisy.join("")}<button type="button" class="secondary" id="clear-active-task-filters">Wyczysc filtry</button>`;
  document.getElementById("clear-active-task-filters")?.addEventListener("click", () => wyczyscFiltryZadan(true));
}

function wyczyscFiltryZadan(przeladuj = true) {
  document.getElementById("task-filters").reset();
  odswiezPasekFiltrowZadan();
  if (przeladuj) {
    wczytajZadania().catch((error) => pokazPowiadomienie(error.message));
  }
}

function renderujPlannerZadan(snapshot) {
  stan.plannerZadan = snapshot;
  document.getElementById("task-planner-generated-at").textContent = snapshot?.generated_at
    ? `Stan na ${formatujDateCzas(snapshot.generated_at)}`
    : "Brak danych";

  ["zalegle", "dzis", "jutro", "tydzien"].forEach((bucketKey) => {
    const bucket = snapshot?.buckets?.[bucketKey] || { count: 0, groups: [] };
    const countElement = document.getElementById(`planner-count-${bucketKey}`);
    const container = document.getElementById(`task-planner-${bucketKey}`);
    if (countElement) {
      countElement.textContent = `${bucket.count || 0}`;
    }
    if (!container) {
      return;
    }
    const nonEmptyGroups = (bucket.groups || []).filter((group) => (group.items || []).length);
    if (!nonEmptyGroups.length) {
      container.innerHTML = `<div class="empty-state">Brak wpisow w tym zakresie.</div>`;
      return;
    }
    container.innerHTML = nonEmptyGroups
      .map(
        (group) => `
          <section class="planner-group">
            <div class="planner-group-title">${bezpiecznyTekst(group.label)}</div>
            ${(group.items || [])
              .map((task) => renderujKartePlanera(task, bucketKey))
              .join("")}
          </section>
        `
      )
      .join("");

    container.querySelectorAll("[data-planner-task-id]").forEach((element) => {
      element.addEventListener("click", async () => {
        try {
          await wczytajSzczegolyZadania(Number(element.dataset.plannerTaskId));
        } catch (error) {
          pokazPowiadomienie(error.message);
        }
      });
    });

    container.querySelectorAll("[data-planner-snooze-mode]").forEach((element) => {
      element.addEventListener("click", async (event) => {
        event.stopPropagation();
        try {
          await odlozPrzypomnienieZadania(Number(element.dataset.plannerTaskId), element.dataset.plannerSnoozeMode);
        } catch (error) {
          pokazPowiadomienie(error.message);
        }
      });
    });

    container.querySelectorAll("[data-planner-complete-task-id]").forEach((element) => {
      element.addEventListener("click", async (event) => {
        event.stopPropagation();
        try {
          await zaktualizujStatusZadania(Number(element.dataset.plannerCompleteTaskId), "zakonczone");
        } catch (error) {
          pokazPowiadomienie(error.message);
        }
      });
    });
  });
  if (stan.szybkiPanelPracyOtwarty && pobierzAktywnaSekcjeSzybkiegoPanelu() === "calendar") {
    renderujSzybkiPanelPracy();
  } else {
    renderujBadgeSzybkiegoPanelu();
  }
}

function renderujFokusZadan(snapshot) {
  stan.fokusZadan = snapshot;
  const generatedAtNode = document.getElementById("task-focus-generated-at");
  const grid = document.getElementById("task-focus-grid");
  if (!generatedAtNode || !grid) {
    return;
  }

  generatedAtNode.textContent = snapshot?.generated_at ? `Stan na ${formatujDateCzas(snapshot.generated_at)}` : "Brak danych";
  const views = Array.isArray(snapshot?.views) ? snapshot.views : [];
  if (!views.length) {
    grid.innerHTML = `<div class="empty-state">Widoki pracy pojawia sie po zaladowaniu danych.</div>`;
    return;
  }

  grid.innerHTML = views
    .map(
      (view) => `
        <section class="focus-column">
          <div class="focus-column-header">
            <h4>${bezpiecznyTekst(view.label || formatujWidokFokusuZadania(view.code))}</h4>
            <span class="pill">${Number(view.count || 0)}</span>
          </div>
          <div class="focus-list">
            ${
              Array.isArray(view.items) && view.items.length
                ? view.items.map((task) => renderujKarteFokusu(task, view.code)).join("")
                : `<div class="empty-state">Brak wpisow w tym widoku.</div>`
            }
          </div>
        </section>
      `
    )
    .join("");

  grid.querySelectorAll("[data-focus-task-id]").forEach((element) => {
    element.addEventListener("click", async () => {
      try {
        await wczytajSzczegolyZadania(Number(element.dataset.focusTaskId));
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
    });
  });
}

function renderujKarteFokusu(task, focusCode) {
  const anchor = task?.remind_at || task?.due_at;
  const recurrence = task?.recurrence_enabled ? task.recurrence_summary : "Jednorazowe";
  return `
    <article class="focus-card" data-focus-task-id="${task.task_id}">
      <div class="focus-card-title">${bezpiecznyTekst(task.title || "(bez tytulu)")}</div>
      <div class="focus-card-meta">
        <span>${formatujTypZadania(task.task_type)}</span>
        <span>${formatujPriorytetZadania(task.priority)}</span>
        <span>${formatujDateCzas(anchor)}</span>
      </div>
      <div class="focus-card-meta">
        <span>${bezpiecznyTekst(task.assigned_user_name || task.owner_user_name || "brak osoby")}</span>
        <span>${formatujWidocznoscZadania(task.visibility_scope)}</span>
      </div>
      <div class="focus-card-note">${bezpiecznyTekst(recurrence)}</div>
      ${
        focusCode === "do_decyzji" && task.calendar_name
          ? `<div class="focus-card-note">Kalendarz: ${bezpiecznyTekst(task.calendar_name)}</div>`
          : ""
      }
    </article>
  `;
}

function renderujKartePlanera(task, bucketKey) {
  const reminder = pobierzStanPrzypomnienia(task);
  const overdueClass = bucketKey === "zalegle" ? "is-overdue" : "";
  const canSnooze = Boolean(task?.remind_at && !["zakonczone", "anulowane"].includes(task?.status || "") && czyMoznaZapisywac());
  const canComplete = Boolean(task?.task_id && !["zakonczone", "anulowane"].includes(task?.status || "") && czyMoznaZapisywac());
  return `
    <article class="planner-card ${overdueClass}" data-planner-task-id="${task.task_id}">
      <div class="planner-card-header">
        <div class="planner-card-title">${bezpiecznyTekst(task.title || "(bez tytulu)")}</div>
        <span class="status-badge ${klasaStatusuZadania(task.status, task.priority)}">${formatujStatusZadania(task.status)}</span>
      </div>
      <div class="planner-card-meta">
        <span>${formatujTypZadania(task.task_type)}</span>
        <span>${formatujPriorytetZadania(task.priority)}</span>
        <span>${formatujDateCzas(task.planner_anchor_at || task.due_at || task.remind_at)}</span>
      </div>
      <div class="planner-card-meta">
        <span>Przypisano: ${bezpiecznyTekst(task.assigned_user_name || "brak")}</span>
        ${
          task.remind_at
            ? `<span>${formatujDateCzas(task.remind_at)} | ${bezpiecznyTekst(reminder.etykieta)}</span>`
            : `<span>Bez przypomnienia</span>`
        }
      </div>
      <div class="planner-card-actions">
        ${
          canComplete
            ? `<button type="button" class="secondary" data-planner-complete-task-id="${task.task_id}">Oznacz jako wykonane</button>`
            : ""
        }
        ${
          canSnooze
            ? `<button type="button" class="secondary" data-planner-task-id="${task.task_id}" data-planner-snooze-mode="10m">Odloz 10 min</button>`
            : ""
        }
        ${
          canSnooze
            ? `<button type="button" class="secondary" data-planner-task-id="${task.task_id}" data-planner-snooze-mode="1h">Odloz 1 h</button>`
            : ""
        }
        ${
          canSnooze
            ? `<button type="button" class="secondary" data-planner-task-id="${task.task_id}" data-planner-snooze-mode="jutro_rano">Jutro rano</button>`
            : ""
        }
      </div>
    </article>
  `;
}

function renderujPodgladNaturalnegoPolecenia(result = null) {
  stan.podgladNaturalnegoPolecenia = result;
  const container = document.getElementById("task-natural-preview");
  const applyButton = document.getElementById("apply-task-command-preview");
  const createButton = document.getElementById("create-task-from-preview");
  if (!container || !applyButton || !createButton) {
    return;
  }
  if (!result) {
    container.classList.remove("preview-card");
    container.classList.add("empty-state");
    container.innerHTML =
      "Tutaj pojawi sie szybki podglad rozpoznanego wpisu: typ, osoba, data, godzina, kalendarz i ostrzezenia.";
    applyButton.disabled = true;
    createButton.disabled = true;
    return;
  }

  const summary = result.summary || {};
  const warnings = Array.isArray(result.warnings) ? result.warnings : [];
  const fallback = result.fallback || null;
  const confidenceValue = typeof result.confidence === "number" ? result.confidence : fallback?.confidence;
  container.classList.remove("empty-state");
  container.classList.add("preview-card");
  container.innerHTML = `
    <div class="preview-meta-heading">Zrozumialem to tak</div>
    <div class="preview-list">
      <div class="preview-row"><strong>Typ wpisu</strong><span>${bezpiecznyTekst(summary.task_type_label || "-")}</span></div>
      <div class="preview-row"><strong>Tytul</strong><span>${bezpiecznyTekst(summary.title || "-")}</span></div>
      <div class="preview-row"><strong>Priorytet</strong><span>${bezpiecznyTekst(summary.priority_label || "-")}</span></div>
      <div class="preview-row"><strong>Widocznosc</strong><span>${bezpiecznyTekst(summary.visibility_label || "-")}</span></div>
      <div class="preview-row"><strong>Przypisano</strong><span>${bezpiecznyTekst(summary.assigned_user_name || "brak")}</span></div>
      <div class="preview-row"><strong>Kalendarz</strong><span>${bezpiecznyTekst(summary.calendar_name || "brak")}</span></div>
      <div class="preview-row"><strong>Termin</strong><span>${bezpiecznyTekst(formatujDateCzas(summary.due_at) || "-")}</span></div>
      <div class="preview-row"><strong>Przypomnienie</strong><span>${bezpiecznyTekst(formatujDateCzas(summary.remind_at) || "-")}</span></div>
      <div class="preview-row"><strong>Cyklicznosc</strong><span>${bezpiecznyTekst(summary.recurrence_label || "Brak cyklicznosci")}</span></div>
      <div class="preview-row"><strong>Pewnosc</strong><span>${typeof confidenceValue === "number" ? `${Math.round(confidenceValue * 100)}%` : "-"}</span></div>
    </div>
    ${
      fallback?.needs_review
        ? `<div class="warning-list"><div class="warning-item">Tryb ostroĹĽny: ${bezpiecznyTekst(fallback.reason || "Polecenie wymaga potwierdzenia.")}${typeof fallback.confidence === "number" ? ` (pewnoĹ›Ä‡ ${Math.round(fallback.confidence * 100)}%)` : ""}</div></div>`
        : ""
    }
    ${
      warnings.length
        ? `<div class="preview-meta-heading">Do sprawdzenia</div><div class="warning-list">${warnings
            .map((warning) => `<div class="warning-item">${bezpiecznyTekst(warning)}</div>`)
            .join("")}</div>`
        : `<div class="muted">Nie wykryto ostrzezen. Mozesz od razu utworzyc wpis albo wczytac dane do formularza.</div>`
    }
  `;
  container.innerHTML = container.innerHTML.replace(
    "Zrozumialem to tak",
    "Tak to zrozumialem, ale mozesz to dopracowac"
  );
  container.insertAdjacentHTML(
    "beforeend",
    `
      <div class="preview-meta-heading">Doprecyzuj w tym oknie</div>
      <div class="muted">Edytuj tytul, typ, priorytet, widocznosc, termin, przypomnienie i opis bez wychodzenia z tego panelu.</div>
      <div class="field-grid preview-edit-grid">
        <div class="field field-span-2">
          <label for="task-natural-preview-title">Tytul</label>
          <input id="task-natural-preview-title" type="text" value="${bezpiecznyTekst(summary.title || "")}" />
        </div>
        <div class="field">
          <label for="task-natural-preview-task-type">Typ wpisu</label>
          <select id="task-natural-preview-task-type">
            ${[
              ["zadanie", "Zadanie"],
              ["wydarzenie", "Wydarzenie"],
              ["przypomnienie", "Przypomnienie"],
              ["notatka", "Notatka"],
            ]
              .map(
                ([value, label]) =>
                  `<option value="${value}" ${value === String(payload.task_type || "zadanie") ? "selected" : ""}>${bezpiecznyTekst(label)}</option>`
              )
              .join("")}
          </select>
        </div>
        <div class="field">
          <label for="task-natural-preview-priority">Priorytet</label>
          <select id="task-natural-preview-priority">
            ${[
              ["niski", "Niski"],
              ["normalny", "Normalny"],
              ["wysoki", "Wysoki"],
              ["krytyczny", "Krytyczny"],
            ]
              .map(
                ([value, label]) =>
                  `<option value="${value}" ${value === String(payload.priority || "normalny") ? "selected" : ""}>${bezpiecznyTekst(label)}</option>`
              )
              .join("")}
          </select>
        </div>
        <div class="field">
          <label for="task-natural-preview-visibility">Widocznosc</label>
          <select id="task-natural-preview-visibility">
            ${[
              ["prywatne", "Prywatne"],
              ["organizacja", "Organizacja"],
              ["wybrane_osoby", "Wybrane osoby"],
            ]
              .map(
                ([value, label]) =>
                  `<option value="${value}" ${value === String(payload.visibility_scope || "prywatne") ? "selected" : ""}>${bezpiecznyTekst(label)}</option>`
              )
              .join("")}
          </select>
        </div>
        <div class="field">
          <label for="task-natural-preview-due-at">Termin</label>
          <input id="task-natural-preview-due-at" type="datetime-local" value="${bezpiecznyTekst(payload.due_at || "")}" />
        </div>
        <div class="field">
          <label for="task-natural-preview-remind-at">Przypomnienie</label>
          <input id="task-natural-preview-remind-at" type="datetime-local" value="${bezpiecznyTekst(payload.remind_at || "")}" />
        </div>
        <div class="field field-span-2">
          <label for="task-natural-preview-description">Opis</label>
          <textarea id="task-natural-preview-description" rows="3">${bezpiecznyTekst(payload.description || "")}</textarea>
        </div>
      </div>
    `
  );
  applyButton.disabled = false;
  createButton.disabled = false;
  applyButton.textContent = "Otworz pelny formularz";
  createButton.textContent = "Utworz z tego okna";
}

function pobierzDoprecyzowanyPodgladNaturalnegoPolecenia() {
  const preview = stan.podgladNaturalnegoPolecenia;
  if (!preview?.payload) {
    return null;
  }
  const payload = { ...preview.payload };
  const titleField = document.getElementById("task-natural-preview-title");
  const taskTypeField = document.getElementById("task-natural-preview-task-type");
  const priorityField = document.getElementById("task-natural-preview-priority");
  const visibilityField = document.getElementById("task-natural-preview-visibility");
  const dueAtField = document.getElementById("task-natural-preview-due-at");
  const remindAtField = document.getElementById("task-natural-preview-remind-at");
  const descriptionField = document.getElementById("task-natural-preview-description");
  const title = String(titleField?.value || "").trim();
  if (title) {
    payload.title = title;
  }
  if (taskTypeField?.value) {
    payload.task_type = taskTypeField.value;
  }
  if (priorityField?.value) {
    payload.priority = priorityField.value;
  }
  if (visibilityField?.value) {
    payload.visibility_scope = visibilityField.value;
  }
  if (dueAtField?.value) {
    payload.due_at = dueAtField.value;
  }
  if (remindAtField?.value) {
    payload.remind_at = remindAtField.value;
  }
  if (descriptionField) {
    payload.description = descriptionField.value.trim();
  }
  return payload;
}

function renderujStatusDyktowaniaNaturalnegoPolecenia(message = "", tone = "") {
  const status = document.getElementById("task-natural-voice-status");
  const startButton = document.getElementById("start-task-natural-voice");
  const stopButton = document.getElementById("stop-task-natural-voice");
  const supported = czyMoznaDyktowacNaturalnePolecenie();
  if (status) {
    status.textContent = message || "Mozesz podyktowac tresc wpisu i potem sprawdzic podglad przed zapisaniem.";
    status.className = `voice-status${tone ? ` ${tone}` : ""}`;
  }
  if (startButton) {
    startButton.disabled = !supported || Boolean(stan.taskNaturalVoiceRecognition);
  }
  if (stopButton) {
    stopButton.disabled = !supported || !stan.taskNaturalVoiceRecognition;
  }
}

function czyMoznaDyktowacNaturalnePolecenie() {
  return Boolean(window.SpeechRecognition || window.webkitSpeechRecognition);
}

function zatrzymajDyktowanieNaturalnegoPolecenia(cicho = false) {
  const recognition = stan.taskNaturalVoiceRecognition;
  stan.taskNaturalVoiceRecognition = null;
  stan.taskNaturalVoiceBuffer = "";
  if (recognition) {
    recognition.onend = null;
    recognition.onerror = null;
    recognition.onresult = null;
    try {
      recognition.stop();
    } catch (error) {
      // Nic nie robimy - zatrzymanie jest najlepszym wysilkiem.
    }
  }
  if (!cicho) {
    renderujStatusDyktowaniaNaturalnegoPolecenia("Dyktowanie zatrzymane.", "muted");
  } else {
    renderujStatusDyktowaniaNaturalnegoPolecenia();
  }
}

function uruchomDyktowanieNaturalnegoPolecenia() {
  if (!czyMoznaDyktowacNaturalnePolecenie()) {
    throw new Error("Ta przegladarka nie obsluguje dyktowania glosowego.");
  }
  if (stan.taskNaturalVoiceRecognition) {
    renderujStatusDyktowaniaNaturalnegoPolecenia("Dyktowanie jest juz uruchomione.", "muted");
    return;
  }
  const input = document.getElementById("task-natural-command");
  if (!input) {
    throw new Error("Nie znaleziono pola polecenia naturalnego.");
  }
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const recognition = new Recognition();
  recognition.lang = "pl-PL";
  recognition.continuous = true;
  recognition.interimResults = true;
  stan.taskNaturalVoiceBuffer = input.value ? `${input.value.trim()} ` : "";
  recognition.onresult = (event) => {
    const finalChunks = [];
    let interim = "";
    for (let index = event.resultIndex; index < event.results.length; index += 1) {
      const transcript = String(event.results[index][0]?.transcript || "").trim();
      if (!transcript) continue;
      if (event.results[index].isFinal) {
        finalChunks.push(transcript);
      } else {
        interim += `${transcript} `;
      }
    }
    if (finalChunks.length) {
      stan.taskNaturalVoiceBuffer = `${stan.taskNaturalVoiceBuffer}${finalChunks.join(" ")} `.trim();
    }
    input.value = `${stan.taskNaturalVoiceBuffer}${interim}`.trim();
    renderujStatusDyktowaniaNaturalnegoPolecenia("Dyktowanie trwa. Sprawdz podglad przed zapisaniem.", "active");
  };
  recognition.onerror = (event) => {
    const code = String(event?.error || "unknown");
    let message = "Nie udalo sie zakonczyc dyktowania.";
    if (code === "not-allowed") {
      message = "Przegladarka zablokowala mikrofon. Zezwol na dostep i sprobuj ponownie.";
    } else if (code === "no-speech") {
      message = "Nie wykryto mowy. Sprobuj jeszcze raz spokojniej lub blizej mikrofonu.";
    } else if (code === "audio-capture") {
      message = "Nie udalo sie uzyskac dostepu do mikrofonu.";
    }
    zatrzymajDyktowanieNaturalnegoPolecenia(true);
    renderujStatusDyktowaniaNaturalnegoPolecenia(message, "warning");
  };
  recognition.onend = () => {
    const field = document.getElementById("task-natural-command");
    if (field && stan.taskNaturalVoiceBuffer) {
      field.value = stan.taskNaturalVoiceBuffer.trim();
    }
    stan.taskNaturalVoiceRecognition = null;
    stan.taskNaturalVoiceBuffer = "";
    renderujStatusDyktowaniaNaturalnegoPolecenia("Dyktowanie zakonczone. Mozesz sprawdzic podglad.", "success");
  };
  recognition.start();
  stan.taskNaturalVoiceRecognition = recognition;
  renderujStatusDyktowaniaNaturalnegoPolecenia("Slucham. Podyktuj zadanie, wydarzenie albo przypomnienie.", "active");
}

function odswiezWidocznoscPolCyklicznosciZadania() {
  const patternField = document.getElementById("task-recurrence-pattern");
  const intervalField = document.getElementById("task-recurrence-interval");
  const endAtField = document.getElementById("task-recurrence-end-at");
  const weekdaysField = document.getElementById("task-recurrence-weekdays");
  const noteField = document.querySelector(".recurrence-note");
  const scopeField = document.getElementById("task-recurrence-scope-field");
  if (!patternField || !intervalField || !endAtField || !weekdaysField) {
    return;
  }
  const pattern = patternField.value || "brak";
  const canWrite = czyMoznaZapisywac();
  const noRecurrence = pattern === "brak";
  const businessDays = pattern === "dni_robocze";
  const istniejeTask = Boolean(document.getElementById("task-id")?.value?.trim());
  intervalField.disabled = !canWrite || noRecurrence || businessDays;
  endAtField.disabled = !canWrite || noRecurrence;
  if (scopeField) {
    scopeField.classList.toggle("hidden", !istniejeTask || noRecurrence);
  }
  if (businessDays && !Number(intervalField.value || 0)) {
    intervalField.value = "1";
  }
  if (businessDays) {
    intervalField.value = "1";
    weekdaysField.value = "0,1,2,3,4";
  } else if (noRecurrence || pattern !== "co_tydzien") {
    weekdaysField.value = "";
  }
  if (noteField) {
    if (noRecurrence) {
      noteField.textContent = "Wpis jednorazowy. Po zakonczeniu nic nie zostanie utworzone automatycznie.";
    } else if (businessDays) {
      noteField.textContent = "Nowe wystapienie pojawi sie po oznaczeniu wpisu jako wykonany, tylko w dni robocze.";
    } else {
      noteField.textContent = "Cykliczne wpisy tworza kolejne wystapienie po oznaczeniu biezacego wpisu jako wykonany.";
    }
  }
  renderujPodsumowanieSkutkuZapisuZadania();
}

function pobierzWybraneNazwyWidocznosciZadania() {
  return Array.from(document.querySelectorAll('input[name="task-visible-user"]:checked'))
    .map((element) => {
      const user = stan.uzytkownicyDoZadan.find((item) => Number(item.user_id) === Number(element.value));
      return user?.display_name || null;
    })
    .filter(Boolean);
}

function renderujHubNotatekZadan(items = []) {
  const container = document.getElementById("task-notes-hub");
  const count = document.getElementById("task-notes-hub-count");
  const showAllButton = document.getElementById("task-notes-show-all");
  const newPrivateButton = document.getElementById("task-notes-new-private");
  if (!container || !count) {
    return;
  }

  const allNotes = (Array.isArray(items) ? items : [])
    .filter((item) => item.task_type === "notatka")
    .sort((left, right) => String(right.updated_at || "").localeCompare(String(left.updated_at || "")));
  const notes = allNotes.slice(0, 8);

  count.textContent = `${allNotes.length}`;
  if (!notes.length) {
    container.className = "empty-state";
    container.innerHTML = "Brak notatek w aktualnym zakresie. Po dodaniu notatki pojawi sie tutaj szybki podglad.";
  } else {
    container.className = "task-note-hub";
    container.innerHTML = notes
      .map(
        (item) => `
          <article class="task-note-hub-item" data-note-task-id="${item.task_id}">
            <div class="task-note-hub-top">
              <strong>${bezpiecznyTekst(item.title || "Notatka")}</strong>
              <span class="status-badge status-normal">${bezpiecznyTekst(formatujWidocznoscZadania(item.visibility_scope))}</span>
            </div>
            <div>${bezpiecznyTekst((item.description || "").trim() || "Bez dodatkowego opisu.")}</div>
            <div class="task-note-hub-meta">
              <span>${bezpiecznyTekst(item.owner_user_name || "-")}</span>
              <span>${bezpiecznyTekst(item.organization_name || "-")}</span>
              <span>${bezpiecznyTekst(formatujDateCzas(item.updated_at) || "-")}</span>
            </div>
          </article>
        `
      )
      .join("");
    container.querySelectorAll("[data-note-task-id]").forEach((element) => {
      element.onclick = () => wczytajSzczegolyZadania(Number(element.dataset.noteTaskId));
    });
  }

  if (showAllButton) {
    showAllButton.onclick = async () => {
      const form = document.getElementById("task-filters");
      if (!form) return;
      form.querySelector('[name="task_type"]').value = "notatka";
      await wczytajZadania();
    };
  }
  if (newPrivateButton) {
    newPrivateButton.onclick = () => {
      przygotujNoweZadanie();
      const typeField = document.getElementById("task-type");
      if (typeField) {
        typeField.value = "notatka";
      }
      ustawZakresWidocznosciZadania("prywatne");
      odswiezWidocznoscFormularzaZadania();
      renderujPodsumowanieSkutkuZapisuZadania();
    };
  }
}

function pobierzPodsumowanieWidocznosciFormularza() {
  const scope = pobierzZakresWidocznosciZadania();
  if (scope === "organizacja") {
    return "Wpis zobacza wszyscy aktywni uzytkownicy tej organizacji.";
  }
  if (scope === "wybrane_osoby") {
    const names = pobierzWybraneNazwyWidocznosciZadania();
    if (!names.length) {
      return "Wpis bedzie ograniczony do wlasciciela, dopoki nie wybierzesz konkretnych osob.";
    }
    return `Wpis zobacza: ${names.join(", ")} oraz wlasciciel.`;
  }
  return "Wpis pozostanie prywatny i zobaczy go tylko wlasciciel.";
}

function pobierzPodsumowanieOdbiorcyPrzypomnienia(task = null) {
  const remindAt = document.getElementById("task-remind-at")?.value || "";
  if (!remindAt) {
    return "Brak przypomnienia. Telefon nie dostanie alertu.";
  }
  const assignedId = Number(document.getElementById("task-assigned-user")?.value || 0);
  const ownerUserId = Number(document.getElementById("task-owner-user-id")?.value || task?.owner_user_id || stan.biezacyUzytkownik?.user_id || 0);
  const assignedUser = stan.uzytkownicyDoZadan.find((item) => Number(item.user_id) === assignedId) || null;
  const ownerUser =
    stan.uzytkownicyDoZadan.find((item) => Number(item.user_id) === ownerUserId) ||
    (stan.biezacyUzytkownik ? {
      user_id: stan.biezacyUzytkownik.user_id,
      display_name: stan.biezacyUzytkownik.display_name || stan.biezacyUzytkownik.login,
      telegram_user_id: stan.biezacyUzytkownik.telegram_user_id,
      telegram_reminders_enabled: stan.ustawieniaPrzypomnienUzytkownika?.telegram_reminders_enabled ?? 1,
    } : null);

  if (assignedUser?.telegram_reminders_enabled && assignedUser?.telegram_user_id) {
    return `Telegram dostanie przypisana osoba: ${assignedUser.display_name}.`;
  }
  if (ownerUser?.telegram_reminders_enabled && ownerUser?.telegram_user_id) {
    return assignedUser
      ? `Przypisana osoba nie jest gotowa, wiec Telegram dostanie wlasciciel wpisu: ${ownerUser.display_name}.`
      : `Telegram dostanie wlasciciel wpisu: ${ownerUser.display_name}.`;
  }
  if (assignedUser && !assignedUser.telegram_user_id) {
    return `Przypisano ${assignedUser.display_name}, ale ta osoba nie ma jeszcze ID Telegram.`;
  }
  return "Przypomnienie jest ustawione, ale nie ma jeszcze gotowego odbiorcy Telegram.";
}

function pobierzPodsumowanieKalendarzaFormularza(task = null) {
  const calendarId = Number(document.getElementById("task-calendar-id")?.value || 0);
  if (!calendarId) {
    return "Wpis zostanie tylko w aplikacji i nie trafi do zadnego kalendarza.";
  }
  const calendar = pobierzKalendarzUzytkownika(calendarId);
  if (!calendar) {
    return "Wybrano kalendarz, ale jego szczegoly nie sa jeszcze dostepne.";
  }
  if (calendar.provider === "google_api") {
    return `Po zapisie wpis trafi bezposrednio do Google Calendar: ${calendar.display_name}${calendar.external_calendar_name ? ` -> ${calendar.external_calendar_name}` : ""}.`;
  }
  return `Wpis bedzie wystawiony przez adres URL (.ics) dla kalendarza: ${calendar.display_name}.`;
}

function pobierzPodsumowanieCyklicznosciFormularza(task = null) {
  const pattern = document.getElementById("task-recurrence-pattern")?.value || "brak";
  if (pattern === "brak") {
    return "To bedzie wpis jednorazowy.";
  }
  const interval = Number(document.getElementById("task-recurrence-interval")?.value || 1);
  const scope = document.getElementById("task-recurrence-apply-scope")?.value || "tylko_ten";
  const label = formatujCyklicznoscZadania(pattern);
  const base = interval > 1 && !["dni_robocze", "brak"].includes(pattern)
    ? `${label} co ${interval}`
    : label;
  if (!task?.task_id) {
    return `Po oznaczeniu wpisu jako wykonany system utworzy kolejne wystapienie. Tryb: ${base}.`;
  }
  return `Seria jest aktywna. Przy zapisie zastosujemy zakres: ${formatujZakresEdycjiSeriiZadania(scope)}.`;
}

function formatujEtykietePowiazaniaBiznesowego(item) {
  if (!item) {
    return "Powiazanie";
  }
  if (item.entity_type === "invoice") {
    return item.label || `Faktura #${item.entity_id}`;
  }
  if (item.entity_type === "contractor") {
    return item.label || `Kontrahent #${item.entity_id}`;
  }
  return item.label || "Powiazanie";
}

function normalizujPowiazaniaEdytowanegoZadania(items) {
  if (!Array.isArray(items)) {
    return [];
  }
  const normalized = [];
  const seen = new Set();
  items.forEach((item) => {
    const entityType = String(item?.entity_type || "").trim().toLowerCase();
    const entityId = Number(item?.entity_id || 0);
    if (!["invoice", "contractor"].includes(entityType) || !entityId) {
      return;
    }
    const key = `${entityType}:${entityId}`;
    if (seen.has(key)) {
      return;
    }
    seen.add(key);
    normalized.push({
      entity_type: entityType,
      entity_id: entityId,
      label: item?.label || "",
      subtitle: item?.subtitle || "",
      organization_name: item?.organization_name || "",
      status: item?.status || "",
      duplicate_type: item?.duplicate_type || "",
    });
  });
  return normalized.sort((left, right) => {
    const typeCompare = String(left.entity_type).localeCompare(String(right.entity_type));
    if (typeCompare !== 0) {
      return typeCompare;
    }
    return Number(left.entity_id) - Number(right.entity_id);
  });
}

function pobierzPowiazaniaEdytowanegoZadania() {
  return normalizujPowiazaniaEdytowanegoZadania(stan.powiazaniaEdytowanegoZadania);
}

function ustawPowiazaniaEdytowanegoZadania(items, options = {}) {
  stan.powiazaniaEdytowanegoZadania = normalizujPowiazaniaEdytowanegoZadania(items);
  renderujPolePowiazanBiznesowych(options);
  if (!options.silent) {
    renderujPodsumowanieSkutkuZapisuZadania(stan.wybraneZadanieDetail?.task || null);
  }
}

function usunPowiazanieEdytowanegoZadania(entityType, entityId) {
  stan.powiazaniaEdytowanegoZadania = pobierzPowiazaniaEdytowanegoZadania().filter(
    (item) => !(String(item.entity_type) === String(entityType) && Number(item.entity_id) === Number(entityId))
  );
  renderujPolePowiazanBiznesowych();
  renderujPodsumowanieSkutkuZapisuZadania(stan.wybraneZadanieDetail?.task || null);
}

function pobierzPodsumowaniePowiazanFormularza() {
  const items = pobierzPowiazaniaEdytowanegoZadania();
  if (!items.length) {
    return "Wpis nie jest jeszcze powiazany z zadna faktura ani kontrahentem.";
  }
  return items.map((item) => formatujEtykietePowiazaniaBiznesowego(item)).join(", ");
}

function renderujPolePowiazanBiznesowych(options = {}) {
  const editable = options.editable ?? czyMoznaZapisywac();
  const container = document.getElementById("task-linked-entities-shell");
  if (!container) {
    return;
  }
  const items = pobierzPowiazaniaEdytowanegoZadania();
  if (!items.length) {
    container.innerHTML = `<div class="empty-state">Brak powiazan biznesowych. Mozesz powiazac wpis z faktura albo kontrahentem.</div>`;
    return;
  }
  container.innerHTML = `
    <div class="list">
      ${items
        .map(
          (item) => `
            <article class="list-item">
              <strong>${bezpiecznyTekst(formatujEtykietePowiazaniaBiznesowego(item))}</strong>
              <div class="muted">${bezpiecznyTekst(item.subtitle || item.organization_name || "")}</div>
              <div class="detail-actions">
                <button
                  type="button"
                  class="secondary small-action"
                  data-open-linked-entity="${bezpiecznyTekst(item.entity_type)}"
                  data-linked-entity-id="${item.entity_id}"
                >
                  Otworz
                </button>
                ${
                  editable
                    ? `
                      <button
                        type="button"
                        class="secondary small-action"
                        data-remove-linked-entity="${bezpiecznyTekst(item.entity_type)}"
                        data-remove-linked-entity-id="${item.entity_id}"
                      >
                        Usun
                      </button>
                    `
                    : ""
                }
              </div>
            </article>
          `
        )
        .join("")}
    </div>
  `;

  container.querySelectorAll("[data-open-linked-entity]").forEach((button) => {
    button.addEventListener("click", async () => {
      const entityType = String(button.dataset.openLinkedEntity || "").trim();
      const entityId = Number(button.dataset.linkedEntityId || 0);
      if (!entityType || !entityId) {
        return;
      }
      try {
        if (entityType === "invoice") {
          ustawWidok("invoices");
          await wczytajSzczegolyFaktury(entityId);
          return;
        }
        if (entityType === "contractor") {
          ustawWidok("contractors");
          await wczytajSzczegolyKontrahenta(entityId);
        }
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
    });
  });

  container.querySelectorAll("[data-remove-linked-entity]").forEach((button) => {
    button.addEventListener("click", () => {
      usunPowiazanieEdytowanegoZadania(
        String(button.dataset.removeLinkedEntity || ""),
        Number(button.dataset.removeLinkedEntityId || 0)
      );
    });
  });
}

function renderujOtwarteSprawyPowiazane(items, emptyLabel = "Brak otwartych spraw.") {
  if (!Array.isArray(items) || !items.length) {
    return `<div class="empty-state">${bezpiecznyTekst(emptyLabel)}</div>`;
  }
  return `
    <div class="list">
      ${items
        .map(
          (task) => `
            <article class="list-item clickable" data-linked-task-id="${task.task_id}">
              <strong>${bezpiecznyTekst(task.title || `Wpis #${task.task_id}`)}</strong>
              <div class="muted">
                ${bezpiecznyTekst(formatujTypZadania(task.task_type))} | ${bezpiecznyTekst(formatujStatusZadania(task.status))} | ${bezpiecznyTekst(formatujWartosc(task.assigned_user_name || task.owner_user_name))}
              </div>
              <div class="muted">${bezpiecznyTekst(formatujDateCzas(task.due_at) || "Bez terminu")}</div>
            </article>
          `
        )
        .join("")}
    </div>
  `;
}

function zbudujSekcjeOtwartchSprawDlaEncji({
  title = "Otwarte sprawy",
  items = [],
  emptyLabel = "Brak otwartych spraw.",
  createLabel = "",
  createWithContractorLabel = "",
  buttonAttributes = "",
  note = "",
} = {}) {
  return `
    <div class="panel">
      <div class="panel-header"><h3>${bezpiecznyTekst(title)}</h3></div>
      ${renderujOtwarteSprawyPowiazane(items, emptyLabel)}
      ${
        createLabel
          ? `
            <div class="detail-actions" style="margin-top: 16px;">
              <button type="button" class="secondary" data-linked-task-create="primary" ${buttonAttributes}>${bezpiecznyTekst(createLabel)}</button>
              ${
                createWithContractorLabel
                  ? `<button type="button" class="secondary" data-linked-task-create="secondary" ${buttonAttributes}>${bezpiecznyTekst(createWithContractorLabel)}</button>`
                  : ""
              }
            </div>
          `
          : ""
      }
      ${note ? `<div class="field-note">${bezpiecznyTekst(note)}</div>` : ""}
    </div>
  `;
}

async function ustawKontekstOrganizacjiDlaAsystenta(organizationId) {
  if (!czyGlobalnyAdministrator() || !organizationId) {
    return;
  }
  if (String(stan.wybranaOrganizacjaId) !== String(organizationId)) {
    stan.wybranaOrganizacjaId = String(organizationId);
    stan.czyZakresOrganizacjiZainicjalizowany = true;
    const switcher = document.getElementById("organization-switcher");
    if (switcher) {
      switcher.value = String(organizationId);
    }
    odswiezPasekSesji();
    await odswiezDanePoZalogowaniu();
  }
}

async function rozpocznijNowyWpisPowiazany(payload, organizationId) {
  await ustawKontekstOrganizacjiDlaAsystenta(organizationId);
  if (!czyMoznaKorzystacZMojejPracy()) {
    pokazPowiadomienie("Asystent Szefa nie jest aktywny dla tej organizacji.");
    return;
  }
  ustawWidok("tasks");
  przygotujNoweZadanie();
  wypelnijFormularzZadaniaZPayload(payload);
}

async function otworzPowiazaneZadanieZKontekstu(taskId, organizationId) {
  const normalizedTaskId = Number(taskId || 0);
  if (!normalizedTaskId) {
    return;
  }
  await ustawKontekstOrganizacjiDlaAsystenta(organizationId);
  if (!czyMoznaKorzystacZMojejPracy()) {
    pokazPowiadomienie("Asystent Szefa nie jest aktywny dla tej organizacji.");
    return;
  }
  ustawWidok("tasks");
  await wczytajSzczegolyZadania(normalizedTaskId);
}

function renderujPodsumowanieSkutkuZapisuZadania(task = null) {
  const container = document.getElementById("task-save-impact");
  if (!container) {
    return;
  }
  container.innerHTML = `
    <div class="task-save-impact-header">
      <div class="preview-meta-heading">Po zapisie stanie sie to</div>
      <span class="status-badge status-normal">${task?.task_id ? "Edycja wpisu" : "Nowy wpis"}</span>
    </div>
    <div class="task-save-impact-grid">
      <div class="task-save-impact-item">
        <strong>Widocznosc</strong>
        <div>${bezpiecznyTekst(pobierzPodsumowanieWidocznosciFormularza())}</div>
      </div>
      <div class="task-save-impact-item">
        <strong>Przypomnienie</strong>
        <div>${bezpiecznyTekst(pobierzPodsumowanieOdbiorcyPrzypomnienia(task))}</div>
      </div>
      <div class="task-save-impact-item">
        <strong>Kalendarz</strong>
        <div>${bezpiecznyTekst(pobierzPodsumowanieKalendarzaFormularza(task))}</div>
      </div>
      <div class="task-save-impact-item">
        <strong>Cyklicznosc</strong>
        <div>${bezpiecznyTekst(pobierzPodsumowanieCyklicznosciFormularza(task))}</div>
      </div>
      <div class="task-save-impact-item">
        <strong>Powiazania</strong>
        <div>${bezpiecznyTekst(pobierzPodsumowaniePowiazanFormularza())}</div>
      </div>
    </div>
  `;
}

function renderujZalacznikiZadan(items) {
  if (!items?.length) {
    return `<div class="empty-state">Brak zalacznikow dla tego wpisu.</div>`;
  }
  return `
    <div class="attachment-list">
      ${items
        .map(
          (item) => `
            <article class="attachment-item">
              <div><strong>${bezpiecznyTekst(item.file_name)}</strong></div>
              <div class="attachment-meta">
                <span>${bezpiecznyTekst(item.mime_type || "plik")}</span>
                <span>${formatujRozmiarPliku(item.file_size)}</span>
                <span>${bezpiecznyTekst(item.uploaded_by_user_name || "-")}</span>
                <span>${formatujDateCzas(item.created_at)}</span>
              </div>
              <div><a href="${bezpiecznyTekst(item.file_link)}" target="_blank" rel="noopener noreferrer">Otworz zalacznik</a></div>
            </article>
          `
        )
        .join("")}
    </div>
  `;
}

function renderujZadania(zadania) {
  stan.zadania = zadania;
  document.getElementById("task-count").textContent = `${zadania.length} rekordow`;
  odswiezPasekFiltrowZadan();
  renderujHubNotatekZadan(zadania);
  renderujWidokKalendarzaZadan(zadania);
  renderujSzybkiKalendarz();
  if (stan.szybkiPanelPracyOtwarty && pobierzAktywnaSekcjeSzybkiegoPanelu() === "tasks") {
    renderujSzybkiPanelPracy();
  } else {
    renderujBadgeSzybkiegoPanelu();
  }
  if (!zadania.some((task) => Number(task.task_id) === Number(stan.wybraneZadanieId))) {
    wyczyscSzczegolyZadania();
  }

  const body = document.getElementById("task-table-body");
  if (!zadania.length) {
    body.innerHTML = `<tr><td colspan="13">Brak zadan dla wybranych filtrow.</td></tr>`;
    return;
  }

  body.innerHTML = zadania
    .map(
      (task) => `
          <tr class="clickable" data-task-id="${task.task_id}">
            <td>${task.task_id}</td>
            <td>${formatujNazweOrganizacji(task.organization_name)}</td>
              <td><span class="status-badge status-normal">${formatujWidocznoscZadania(task.visibility_scope)}</span></td>
              <td>${formatujTypZadania(task.task_type)}</td>
                <td>${formatujWartosc(task.title)}</td>
                <td>${formatujWartosc(task.calendar_name)}</td>
                <td>${task.calendar_name ? renderujStanSynchronizacjiGoogle(task) : "-"}</td>
                <td>${formatujWartosc(task.assigned_user_name)}</td>
                <td>${formatujDateCzas(task.due_at)}</td>
              <td>
              ${
                task.remind_at
                  ? `<div>${formatujDateCzas(task.remind_at)}</div><div class="muted"><span class="status-badge ${pobierzStanPrzypomnienia(task).klasa}">${pobierzStanPrzypomnienia(task).etykieta}</span></div>`
                  : "-"
              }
            </td>
            <td><span class="status-badge ${klasaStatusuZadania(task.status, task.priority)}">${formatujPriorytetZadania(task.priority)}</span></td>
            <td><span class="status-badge ${klasaStatusuZadania(task.status, task.priority)}">${formatujStatusZadania(task.status)}</span></td>
            <td>${formatujDateCzas(task.updated_at)}</td>
        </tr>
      `
    )
    .join("");

  body.querySelectorAll("[data-task-id]").forEach((row) => {
    row.addEventListener("click", () => wczytajSzczegolyZadania(Number(row.dataset.taskId)));
  });
}

function renderujHistorieZadan(items) {
  if (!items.length) {
    return `<div class="empty-state">Brak historii zmian dla tego zadania.</div>`;
  }

  return `
    <div class="list">
      ${items
        .map(
          (item) => `
            <article class="list-item">
              <strong>${formatujTypZdarzenia(item.action_type)}</strong>
              <div class="muted">${formatujDateCzas(item.created_at)}</div>
              <div>${formatujWartosc(item.message)}</div>
              <div class="muted">Aktor: ${formatujWartosc(item.actor)}</div>
            </article>
          `
        )
        .join("")}
    </div>
  `;
}

function renderujNotatkiZadan(items) {
  const notes = Array.isArray(items) ? items.map((item) => ({ ...item, task_note_id: Number(item.task_note_id || 0) })) : [];
  if (!notes.length) {
    return `<div class="empty-state">Brak komentarzy dla tego zadania.</div>`;
  }

  const noteMap = new Map();
  const roots = [];
  notes.forEach((note) => {
    note.replies = [];
    noteMap.set(note.task_note_id, note);
  });
  notes.forEach((note) => {
    const parentId = Number(note.parent_note_id || 0);
    if (parentId && noteMap.has(parentId)) {
      noteMap.get(parentId).replies.push(note);
    } else {
      roots.push(note);
    }
  });

  const renderNote = (note, depth = 0) => {
    const mentioned = Array.isArray(note.mentioned_user_names) ? note.mentioned_user_names : [];
    const replyCount = Array.isArray(note.replies) ? note.replies.length : 0;
    return `
      <article class="task-note-thread-item ${depth > 0 ? "is-reply" : ""}" data-task-note-id="${note.task_note_id}">
        <div class="task-note-thread-top">
          <div>
            <strong>${bezpiecznyTekst(note.created_by_user_name || "-")}</strong>
            <div class="task-note-thread-meta">
              <span>${bezpiecznyTekst(formatujDateCzas(note.created_at))}</span>
              <span class="status-badge status-muted">${bezpiecznyTekst(formatujTypNotatki(note.note_kind))}</span>
            </div>
          </div>
          <div class="task-note-thread-actions">
            <button type="button" class="secondary small-action" data-task-note-reply-to="${note.task_note_id}">Odpowiedz</button>
          </div>
        </div>
        <div class="task-note-thread-body">${bezpiecznyTekst(note.note_text)}</div>
        ${
          mentioned.length
            ? `<div class="task-note-mentions">${mentioned
                .map((user) => `<span class="mini-badge mini-badge-ksef">@${bezpiecznyTekst(user)}</span>`)
                .join("")}</div>`
            : ""
        }
        ${replyCount ? `<div class="muted">Odpowiedzi: ${replyCount}</div>` : ""}
        ${
          Array.isArray(note.replies) && note.replies.length
            ? `<div class="task-note-thread-replies">${note.replies.map((reply) => renderNote(reply, depth + 1)).join("")}</div>`
            : ""
        }
      </article>
    `;
  };

  return `
    <div class="task-note-thread">
      ${roots.map((item) => renderNote(item)).join("")}
    </div>
  `;
}

function renderujChecklistZadan(items, task = null, zablokowane = false) {
  const checklist = Array.isArray(items) ? items : [];
  const canInteract = Boolean(task?.task_id) && !zablokowane && czyMoznaZapisywac();
  const completed = checklist.filter((item) => Number(item.is_completed || 0) === 1).length;
  const total = checklist.length;
  if (!task?.task_id) {
    return `<div class="empty-state">Checklista pojawi sie po zapisaniu zadania.</div>`;
  }

  return `
    <div class="checklist-shell">
      <div class="task-checklist-progress">
        <span class="pill">${completed}/${total || 0}</span>
        <span class="muted">Wykonane elementy checklisty</span>
      </div>
      ${
        checklist.length
          ? `<div class="task-checklist-list">
              ${checklist
                .map(
                  (item) => `
                    <label class="task-checklist-item ${Number(item.is_completed || 0) === 1 ? "is-done" : ""}">
                      <input type="checkbox" data-task-checklist-toggle="${item.task_checklist_item_id}" ${Number(item.is_completed || 0) === 1 ? "checked" : ""} ${canInteract ? "" : "disabled"} />
                      <span>
                        <strong>${bezpiecznyTekst(item.item_text)}</strong>
                        <div class="muted">${bezpiecznyTekst(item.completed_by_user_name || item.created_by_user_name || "-")}</div>
                      </span>
                    </label>
                  `
                )
                .join("")}
            </div>`
          : `<div class="empty-state">Brak elementow checklisty.</div>`
      }
      ${
        canInteract
          ? `
            <form id="task-checklist-form" class="stack">
              <input id="task-checklist-text" type="text" placeholder="Dodaj kolejny krok lub zadanie czesciowe" />
              <button type="submit" class="secondary">Dodaj do checklisty</button>
            </form>
          `
          : ""
      }
    </div>
  `;
}

function renderujSekcjeAkceptacji(entityType, entityId, requests = [], options = {}) {
  const canWrite = Boolean(options.canWrite ?? czyMoznaZapisywac());
  const defaultStatuses = pobierzSzablonAkceptacjiDlaEncji(entityType);
  const pendingRequests = Array.isArray(requests) ? requests : [];
  const title = options.title || "Akceptacje";
  const emptyLabel = options.emptyLabel || "Brak wnioskow akceptacyjnych.";
  return `
    <div class="approval-shell" data-approval-entity-type="${bezpiecznyTekst(entityType)}" data-approval-entity-id="${bezpiecznyTekst(entityId)}">
      <div class="panel-header">
        <h3>${bezpiecznyTekst(title)}</h3>
        <span class="pill">${pendingRequests.length}</span>
      </div>
      ${
        pendingRequests.length
          ? `<div class="approval-list">
              ${pendingRequests
                .map(
                  (request) => {
                    const fieldChanges = Array.isArray(request.metadata?.field_changes) ? request.metadata.field_changes : [];
                    const canDecide = Boolean(request.can_decide);
                    return `
                    <article class="approval-card" data-approval-id="${request.approval_request_id}">
                      <div class="approval-card-top">
                        <div>
                          <strong>${bezpiecznyTekst(request.title || "Wniosek akceptacyjny")}</strong>
                          <div class="muted">${bezpiecznyTekst(formatujTypAkceptacji(request.entity_type))} #${bezpiecznyTekst(request.entity_id)}</div>
                        </div>
                        <span class="status-badge ${klasaStatusuAkceptacji(request.status)}">${bezpiecznyTekst(formatujStatusAkceptacji(request.status))}</span>
                      </div>
                      ${request.description ? `<div class="approval-card-body">${bezpiecznyTekst(request.description)}</div>` : ""}
                      ${
                        fieldChanges.length
                          ? `
                            <div class="approval-field-change-list">
                              ${fieldChanges
                                .map(
                                  (change) => `
                                    <div class="approval-field-change">
                                      <strong>${bezpiecznyTekst(change.field_label || etykietaPolaKsef(change.field_name))}</strong>
                                      <div>Oryginal z KSeF: ${formatujWartoscPolaKsef(change.field_name, change.source_value, change.currency || "PLN")}</div>
                                      <div>Proponowana wartosc lokalna: ${formatujWartoscPolaKsef(change.field_name, change.local_value, change.currency || "PLN")}</div>
                                    </div>
                                  `
                                )
                                .join("")}
                            </div>
                          `
                          : ""
                      }
                      <div class="approval-card-meta">
                        <span>${bezpiecznyTekst(request.requested_by_user_name || "-")}</span>
                        <span>${bezpiecznyTekst(formatujDateCzas(request.requested_at))}</span>
                        ${request.requested_user_name ? `<span>Do decyzji: ${bezpiecznyTekst(request.requested_user_name)}</span>` : ""}
                        ${request.decided_by_user_name ? `<span>Decyzja: ${bezpiecznyTekst(request.decided_by_user_name)}</span>` : ""}
                      </div>
                      ${request.decision_reason ? `<div class="muted">${bezpiecznyTekst(request.decision_reason)}</div>` : ""}
                      ${renderujZalacznikiAkceptacji([], request.approval_request_id, canWrite)}
                      ${
                        canDecide && String(request.status || "").toLowerCase() === "pending"
                          ? `
                            <div class="approval-card-actions">
                              <button type="button" class="secondary small-action" data-approval-action="approve" data-approval-id="${request.approval_request_id}">Zatwierdz</button>
                              <button type="button" class="secondary small-action" data-approval-action="reject" data-approval-id="${request.approval_request_id}">Odrzuc</button>
                            </div>
                          `
                          : ""
                      }
                    </article>
                  `;
                  }
                )
                .join("")}
            </div>`
          : `<div class="empty-state">${bezpiecznyTekst(emptyLabel)}</div>`
      }
      ${
        canWrite
          ? `
            <form id="approval-create-form" class="field-grid approval-form">
              <div class="field">
                <label>Tytul wniosku</label>
                <input id="approval-title" type="text" value="Wniosek akceptacyjny" />
              </div>
              <div class="field">
                <label>Odbiorca decyzji</label>
                <select id="approval-requested-user">
                  <option value="">Bez wskazania</option>
                  ${(Array.isArray(stan.uzytkownicyDoZadan) && stan.uzytkownicyDoZadan.length
                    ? stan.uzytkownicyDoZadan
                    : Array.isArray(stan.uzytkownicy)
                      ? stan.uzytkownicy
                      : [])
                        .map((user) => `<option value="${user.user_id}">${bezpiecznyTekst(user.display_name || user.login || user.user_id)}</option>`)
                        .join("")
                  }
                </select>
              </div>
              <div class="field field-full">
                <label>Opis</label>
                <textarea id="approval-description" rows="3" placeholder="Dodaj kontekst decyzji, uzasadnienie lub wymagane kroki."></textarea>
              </div>
              <div class="field">
                <label>Po akceptacji</label>
                <input id="approval-approve-status" type="text" value="${bezpiecznyTekst(defaultStatuses.approve_status)}" />
              </div>
              <div class="field">
                <label>Po odrzuceniu</label>
                <input id="approval-reject-status" type="text" value="${bezpiecznyTekst(defaultStatuses.reject_status)}" />
              </div>
              <div class="filters-actions field-full">
                <button type="submit">Utworz wniosek</button>
              </div>
            </form>
          `
          : ""
      }
    </div>
  `;
}

function renderujSzablonyZadan(task = null, checklistItems = []) {
  const templates = Array.isArray(stan.taskTemplates) ? stan.taskTemplates : [];
  const canWrite = czyMoznaZapisywac();
  const container = document.getElementById("task-templates-panel");
  if (!container) {
    return;
  }
  const currentTemplate = stan.taskTemplateEditorId ? znajdzSzablonPoId(stan.taskTemplateEditorId) : null;
  const selectedTask = task || (stan.wybraneZadanieId ? znajdzZadaniePoId(stan.wybraneZadanieId) : null);
  const itemLines = currentTemplate?.checklist_items?.length
    ? currentTemplate.checklist_items.join("\n")
    : Array.isArray(checklistItems) && checklistItems.length
      ? checklistItems.map((item) => item.item_text).join("\n")
      : "";
  const selectedTemplateId = currentTemplate?.task_template_id || "";
  const fieldDisabled = canWrite ? "" : "disabled";
  const templateOptions = templates.length
    ? templates
        .map(
          (template) =>
            `<option value="${template.task_template_id}" ${Number(template.task_template_id) === Number(selectedTemplateId) ? "selected" : ""}>${bezpiecznyTekst(template.template_name)}${template.is_active ? "" : " (nieaktywny)"}</option>`
        )
        .join("")
    : '<option value="">Brak szablonow</option>';

  container.innerHTML = `
    <div class="panel-header">
      <h3>Szablony zadan</h3>
      <span class="pill">${templates.length}</span>
    </div>
    <div class="panel-note">Szablon przenosi konfiguracje wpisu, terminy wzgledne i liste checklisty. To szybki sposob na powtarzalne dziaĹ‚ania.</div>
    <div class="template-quick-actions">
      <select id="task-template-select" ${fieldDisabled}>${templateOptions}</select>
      <div class="detail-actions">
        <button type="button" class="secondary" id="task-template-load" ${fieldDisabled}>Wczytaj</button>
        <button type="button" class="secondary" id="task-template-apply" ${fieldDisabled}>Utworz wpis</button>
      </div>
    </div>
    <form id="task-template-form" class="field-grid template-form">
      <input type="hidden" id="task-template-id" value="${bezpiecznyTekst(selectedTemplateId)}" />
      <div class="field">
        <label>Nazwa szablonu</label>
        <input id="task-template-name" type="text" value="${bezpiecznyTekst(currentTemplate?.template_name || "")}" placeholder="np. Cotygodniowe rozliczenie" ${fieldDisabled} />
      </div>
      <div class="field">
        <label>Typ wpisu</label>
        <select id="task-template-type" ${fieldDisabled}>
          ${(stan.meta?.task_types || ["zadanie"])
            .map(
              (item) => `<option value="${item}" ${item === (currentTemplate?.task_type || "zadanie") ? "selected" : ""}>${formatujTypZadania(item)}</option>`
            )
            .join("")}
        </select>
      </div>
      <div class="field">
        <label>Priorytet</label>
        <select id="task-template-priority" ${fieldDisabled}>
          ${(stan.meta?.task_priorities || ["normalny"])
            .map(
              (item) => `<option value="${item}" ${item === (currentTemplate?.priority || "normalny") ? "selected" : ""}>${formatujPriorytetZadania(item)}</option>`
            )
            .join("")}
        </select>
      </div>
      <div class="field">
        <label>Widocznosc</label>
        <select id="task-template-visibility" ${fieldDisabled}>
          ${(stan.meta?.task_visibility_scopes || ["prywatne"])
            .map(
              (item) => `<option value="${item}" ${item === (currentTemplate?.visibility_scope || "prywatne") ? "selected" : ""}>${formatujWidocznoscZadania(item)}</option>`
            )
            .join("")}
        </select>
      </div>
      <div class="field">
        <label>Termin wzgledny (min)</label>
        <input id="task-template-due-offset" type="number" min="-43200" max="43200" step="5" value="${bezpiecznyTekst(currentTemplate?.due_offset_minutes ?? "")}" placeholder="np. 60" ${fieldDisabled} />
      </div>
      <div class="field">
        <label>Przypomnienie wzgledne (min)</label>
        <input id="task-template-reminder-offset" type="number" min="-43200" max="43200" step="5" value="${bezpiecznyTekst(currentTemplate?.reminder_offset_minutes ?? "")}" placeholder="np. 30" ${fieldDisabled} />
      </div>
      <div class="field">
        <label>Czas wpisu w kalendarzu (min)</label>
        <input id="task-template-duration" type="number" min="1" max="1440" step="5" value="${bezpiecznyTekst(currentTemplate?.calendar_duration_minutes ?? 60)}" ${fieldDisabled} />
      </div>
      <div class="field">
        <label>Aktywny</label>
        <label class="checkbox-inline">
          <input id="task-template-active" type="checkbox" ${currentTemplate && !currentTemplate.is_active ? "" : "checked"} ${fieldDisabled} />
          Szablon jest dostepny przy tworzeniu wpisow.
        </label>
      </div>
      <div class="field field-full">
        <label>Opis</label>
        <textarea id="task-template-description" rows="3" placeholder="Krotki opis zastosowania szablonu." ${fieldDisabled}>${bezpiecznyTekst(currentTemplate?.template_description || "")}</textarea>
      </div>
      <div class="field field-full">
        <label>Checklista</label>
        <textarea id="task-template-checklist" rows="4" placeholder="Jeden element na linie." ${fieldDisabled}>${bezpiecznyTekst(itemLines)}</textarea>
      </div>
      <div class="filters-actions field-full">
        <button type="submit" ${canWrite ? "" : "disabled"}>Zapisz szablon</button>
        <button type="button" class="secondary" id="task-template-clear" ${fieldDisabled}>Wyczysc</button>
        <button type="button" class="secondary" id="task-template-prefill-from-task" ${selectedTask?.task_id ? "" : "disabled"} ${fieldDisabled}>Wczytaj z biezacego wpisu</button>
      </div>
    </form>
  `;

  const loadButton = document.getElementById("task-template-load");
  if (loadButton) {
    loadButton.onclick = () => {
      const select = document.getElementById("task-template-select");
      if (!select?.value) {
        return;
      }
      stan.taskTemplateEditorId = Number(select.value);
      renderujSzablonyZadan(selectedTask);
    };
  }
  const applyButton = document.getElementById("task-template-apply");
  if (applyButton) {
    applyButton.onclick = async () => {
      try {
        const select = document.getElementById("task-template-select");
        const templateId = Number(select?.value || 0);
        if (!templateId) {
          throw new Error("Wybierz szablon do utworzenia wpisu.");
        }
        await utworzWpisZSzablonu(templateId);
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
    };
  }
  const templateForm = document.getElementById("task-template-form");
  if (templateForm) {
    templateForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      try {
        await zapiszSzablonZadania();
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
    });
  }
  const clearButton = document.getElementById("task-template-clear");
  if (clearButton) {
    clearButton.onclick = () => wyczyscFormularzSzablonuZadania();
  }
  const prefillButton = document.getElementById("task-template-prefill-from-task");
  if (prefillButton) {
    prefillButton.onclick = () => wypelnijSzablonZBiezacegoZadania();
  }
}

function zbudujDateCzasNaDzien(targetDayKey, sourceDate = null) {
  const [year, month, day] = String(targetDayKey || "").split("-").map((part) => Number(part));
  if (!year || !month || !day) {
    return "";
  }
  const base = sourceDate instanceof Date && !Number.isNaN(sourceDate.getTime()) ? new Date(sourceDate) : new Date();
  base.setFullYear(year, month - 1, day);
  if (!sourceDate) {
    base.setHours(9, 0, 0, 0);
  }
  return formatujDateCzasDoInput(base);
}

async function przesunTerminZadaniaDoDaty(taskId, targetDayKey) {
  const task = znajdzZadaniePoId(taskId);
  if (!task) {
    throw new Error("Nie znaleziono wpisu do przeniesienia.");
  }
  const payload = {};
  if (task.due_at) {
    const newDueAt = zbudujDateCzasNaDzien(targetDayKey, new Date(task.due_at));
    payload.due_at = newDueAt;
    if (task.remind_at) {
      const dueDate = new Date(task.due_at);
      const remindDate = new Date(task.remind_at);
      const deltaMinutes = Math.round((remindDate.getTime() - dueDate.getTime()) / 60000);
      const movedRemind = new Date(new Date(newDueAt).getTime() + deltaMinutes * 60000);
      payload.remind_at = formatujDateCzasDoInput(movedRemind);
    }
  } else if (task.remind_at) {
    payload.remind_at = zbudujDateCzasNaDzien(targetDayKey, new Date(task.remind_at));
  } else {
    payload.due_at = zbudujDateCzasNaDzien(targetDayKey, null);
  }
  const targetStart = payload.due_at || payload.remind_at || "";
  if (!targetStart) {
    throw new Error("Nie mozna przeniesc wpisu bez terminu.");
  }
  const proceed = await potwierdzKolizjeKalendarza(task, targetStart, "przesuniecie na dzien");
  if (!proceed) {
    return null;
  }
  await api(zbudujAdresZOrganizacja(`/api/tasks/${taskId}`), {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
  pokazPowiadomienie("Przeniesiono termin wpisu.");
  await Promise.all([wczytajZadania(), wczytajPlannerZadan(), wczytajFokusZadan(), wczytajLogi()]);
  if (stan.wybraneZadanieId && Number(stan.wybraneZadanieId) === Number(taskId)) {
    await wczytajSzczegolyZadania(taskId);
  }
}

function pobierzTerminKalendarzaZadania(task) {
  const value = String(task?.due_at || task?.remind_at || "").trim();
  const date = parsujDateKalendarza(value);
  if (!date) {
    return null;
  }
  return {
    task,
    date,
    source: task?.due_at ? "termin" : "przypomnienie",
  };
}

function pobierzWpisyKalendarzaZadan(items) {
  return (Array.isArray(items) ? items : [])
    .map((task) => pobierzTerminKalendarzaZadania(task))
    .filter(Boolean)
    .sort((left, right) => {
      const diff = left.date.getTime() - right.date.getTime();
      if (diff !== 0) return diff;
      return Number(left.task.task_id || 0) - Number(right.task.task_id || 0);
    });
}

function kalendarzKluczDnia(data) {
  const year = data.getFullYear();
  const month = String(data.getMonth() + 1).padStart(2, "0");
  const day = String(data.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function renderujKarteKalendarzaZadania(entry, { compact = false } = {}) {
  const task = entry.task;
  const title = task.title || "Wpis";
  const calendarName = task.calendar_name || task.task_type || "";
  const meta = [
    formatujTypZadania(task.task_type),
    task.organization_name || null,
    task.priority ? formatujPriorytetZadania(task.priority) : null,
  ]
    .filter(Boolean)
    .join(" | ");
  const time = formatujDateCzas(entry.date);
  return `
    <article class="task-calendar-entry ${compact ? "compact" : ""}" data-task-id="${task.task_id}" data-task-calendar-source="${entry.source}" draggable="true">
      <div class="task-calendar-entry-top">
        <strong>${bezpiecznyTekst(title)}</strong>
        <span class="status-badge status-normal">${bezpiecznyTekst(formatujTypZadania(task.task_type))}</span>
      </div>
      <div class="muted">${bezpiecznyTekst(time)}</div>
      ${calendarName ? `<div class="muted">${bezpiecznyTekst(calendarName)}</div>` : ""}
      <div class="task-calendar-entry-meta">${bezpiecznyTekst(meta)}</div>
      ${
        compact
          ? ""
          : `
            <div class="task-calendar-entry-actions">
              <button type="button" class="secondary small-action" data-task-move-days="-1" data-task-id="${task.task_id}">-1d</button>
              <button type="button" class="secondary small-action" data-task-move-days="1" data-task-id="${task.task_id}">+1d</button>
              <button type="button" class="secondary small-action" data-task-move-hours="-1" data-task-id="${task.task_id}">-1h</button>
              <button type="button" class="secondary small-action" data-task-move-hours="1" data-task-id="${task.task_id}">+1h</button>
            </div>
          `
      }
    </article>
  `;
}

function pobierzGodzineKalendarza(data) {
  return data instanceof Date && !Number.isNaN(data.getTime()) ? data.getHours() : null;
}

function formatujGodzineKalendarza(hour) {
  return `${String(Math.max(0, Math.min(23, Number(hour) || 0))).padStart(2, "0")}:00`;
}

function zbudujDateCzasNaSlot(day, hour) {
  const slot = new Date(day);
  if (Number.isNaN(slot.getTime())) {
    return "";
  }
  slot.setHours(Math.max(0, Math.min(23, Number(hour) || 0)), 0, 0, 0);
  return formatujDateCzasDoInput(slot);
}

function pobierzTrwanieWpisuKalendarza(task) {
  const duration = Number(task?.calendar_duration_minutes || 0);
  if (Number.isFinite(duration) && duration > 0) {
    return Math.min(1440, duration);
  }
  return 60;
}

function pobierzKluczZakresuKalendarza(task) {
  const calendarId = Number(task?.calendar_id || 0);
  if (calendarId) {
    return `calendar:${calendarId}`;
  }
  const assignedUserId = Number(task?.assigned_user_id || 0);
  if (assignedUserId) {
    return `user:${assignedUserId}`;
  }
  const ownerUserId = Number(task?.owner_user_id || 0);
  if (ownerUserId) {
    return `owner:${ownerUserId}`;
  }
  const organizationId = Number(task?.organization_id || 0);
  if (organizationId) {
    return `organization:${organizationId}`;
  }
  return "global";
}

function pobierzZakresWpisuKalendarza(task, startOverride = null) {
  const rawStart = startOverride || task?.due_at || task?.remind_at || "";
  const start = parsujDateKalendarza(rawStart);
  if (!start) {
    return null;
  }
  const durationMinutes = pobierzTrwanieWpisuKalendarza(task);
  const end = new Date(start.getTime() + durationMinutes * 60000);
  return {
    start,
    end,
    durationMinutes,
  };
}

function czyZakresyWpisowKalendarzaSieNakladaja(left, right) {
  if (!left || !right) {
    return false;
  }
  return left.start.getTime() < right.end.getTime() && right.start.getTime() < left.end.getTime();
}

function pobierzKonfliktyKalendarzaDlaZadania(task, targetStart) {
  const candidateRange = pobierzZakresWpisuKalendarza(task, targetStart);
  if (!candidateRange) {
    return [];
  }
  const candidateScope = pobierzKluczZakresuKalendarza(task);
  const normalizedTaskId = Number(task?.task_id || 0);
  return pobierzWpisyKalendarzaZadan(stan.zadania)
    .filter((entry) => Number(entry?.task?.task_id || 0) !== normalizedTaskId)
    .filter((entry) => {
      const status = String(entry?.task?.status || "").trim().toLowerCase();
      if (["zakonczone", "anulowane"].includes(status)) {
        return false;
      }
      return pobierzKluczZakresuKalendarza(entry.task) === candidateScope;
    })
    .map((entry) => {
      const zakres = pobierzZakresWpisuKalendarza(entry.task, entry.date);
      return zakres ? { entry, zakres } : null;
    })
    .filter(Boolean)
    .filter((item) => czyZakresyWpisowKalendarzaSieNakladaja(candidateRange, item.zakres))
    .sort((left, right) => left.zakres.start.getTime() - right.zakres.start.getTime());
}

function formatujKonfliktKalendarza(item) {
  const task = item?.entry?.task || {};
  const zakres = item?.zakres || null;
  const title = task.title || "Wpis";
  const timeLabel = zakres
    ? `${formatujDateCzas(zakres.start)} - ${formatujDateCzas(zakres.end)}`
    : formatujDateCzas(item?.entry?.date || task.due_at || task.remind_at || "");
  const details = [
    formatujTypZadania(task.task_type),
    task.assigned_user_name || task.owner_user_name || null,
    task.calendar_name || null,
  ]
    .filter(Boolean)
    .join(" | ");
  return `
    <article class="calendar-conflict-item">
      <div class="calendar-conflict-item-top">
        <strong>${bezpiecznyTekst(title)}</strong>
        <span class="status-badge status-warning">${bezpiecznyTekst(formatujTypZadania(task.task_type))}</span>
      </div>
      <div class="muted">${bezpiecznyTekst(timeLabel)}</div>
      ${details ? `<div class="muted">${bezpiecznyTekst(details)}</div>` : ""}
    </article>
  `;
}

function zamknijModalKonfliktuKalendarza(confirm = false) {
  const shell = document.getElementById("task-calendar-conflict-modal");
  if (!shell) {
    return;
  }
  shell.classList.add("hidden");
  shell.setAttribute("aria-hidden", "true");
  const resolver = stan.taskCalendarConflictModalResolver;
  stan.taskCalendarConflictModalResolver = null;
  stan.taskCalendarConflictModalContext = null;
  if (typeof resolver === "function") {
    resolver(Boolean(confirm));
  }
}

function otworzModalKonfliktuKalendarza({ task, targetStart, conflicts, modeLabel }) {
  const shell = document.getElementById("task-calendar-conflict-modal");
  const titleNode = document.getElementById("task-calendar-conflict-modal-title");
  const subtitleNode = document.getElementById("task-calendar-conflict-modal-subtitle");
  const messageNode = document.getElementById("task-calendar-conflict-modal-message");
  const listNode = document.getElementById("task-calendar-conflict-modal-list");
  const confirmButton = document.getElementById("task-calendar-conflict-modal-confirm");
  if (!shell || !titleNode || !subtitleNode || !messageNode || !listNode || !confirmButton) {
    return Promise.resolve(false);
  }
  if (typeof stan.taskCalendarConflictModalResolver === "function") {
    zamknijModalKonfliktuKalendarza(false);
  }

  const parsedTarget = parsujDateKalendarza(targetStart);
  const candidateLabel = parsedTarget ? formatujDateCzas(parsedTarget) : formatujDateCzas(targetStart);
  const taskTitle = task?.title || "Wpis";
  titleNode.textContent = "Wykryto kolizje w kalendarzu";
  subtitleNode.textContent = `${taskTitle} (${modeLabel})`;
  messageNode.innerHTML = `
    <div class="stack">
      <div>Wybrany termin <strong>${bezpiecznyTekst(candidateLabel)}</strong> nachodzi na ${conflicts.length} innych wpis${conflicts.length === 1 ? "" : "y"} w tym samym zakresie.</div>
      <div class="subtle-note">Mozesz anulowac i wybrac inny slot albo potwierdzic przesuniecie mimo nakladania sie terminow.</div>
    </div>
  `;
  listNode.innerHTML = conflicts.length
    ? conflicts.map((item) => formatujKonfliktKalendarza(item)).join("")
    : '<div class="empty-state calendar-empty">Brak szczegolow kolizji.</div>';
  confirmButton.textContent = "Przesun mimo to";
  shell.classList.remove("hidden");
  shell.setAttribute("aria-hidden", "false");
  return new Promise((resolve) => {
    stan.taskCalendarConflictModalResolver = resolve;
    stan.taskCalendarConflictModalContext = {
      taskId: Number(task?.task_id || 0),
      targetStart,
      modeLabel,
    };
  });
}

async function potwierdzKolizjeKalendarza(task, targetStart, modeLabel) {
  const conflicts = pobierzKonfliktyKalendarzaDlaZadania(task, targetStart);
  if (!conflicts.length) {
    return true;
  }
  return otworzModalKonfliktuKalendarza({
    task,
    targetStart,
    conflicts,
    modeLabel,
  });
}

function renderujWidokKalendarzaZadan(items = stan.zadania) {
  const container = document.getElementById("task-calendar-body");
  const labelNode = document.getElementById("task-calendar-label");
  const countNode = document.getElementById("task-calendar-count");
  const modeButtons = Array.from(document.querySelectorAll("[data-task-calendar-mode]"));
  const prevButton = document.getElementById("task-calendar-prev");
  const nextButton = document.getElementById("task-calendar-next");
  const todayButton = document.getElementById("task-calendar-today");
  if (!container) {
    return;
  }

  if (!(stan.taskCalendarAnchor instanceof Date) || Number.isNaN(stan.taskCalendarAnchor.getTime())) {
    stan.taskCalendarAnchor = new Date();
  }
  const anchor = new Date(stan.taskCalendarAnchor);
  const mode = ["dzien", "tydzien", "miesiac"].includes(String(stan.taskCalendarMode || "")) ? stan.taskCalendarMode : "miesiac";
  stan.taskCalendarMode = mode;
  const entries = pobierzWpisyKalendarzaZadan(items);
  const activeDayKey = kalendarzKluczDnia(anchor);

  modeButtons.forEach((button) => {
    const isActive = String(button.dataset.taskCalendarMode || "") === mode;
    button.classList.toggle("active", isActive);
    button.setAttribute("aria-pressed", isActive ? "true" : "false");
    button.onclick = () => {
      stan.taskCalendarMode = String(button.dataset.taskCalendarMode || "miesiac");
      renderujWidokKalendarzaZadan(items);
    };
  });

  if (prevButton) {
    prevButton.onclick = () => {
      if (mode === "miesiac") {
        stan.taskCalendarAnchor = new Date(anchor.getFullYear(), anchor.getMonth() - 1, 1);
      } else if (mode === "tydzien") {
        stan.taskCalendarAnchor = dodajDniDoDaty(anchor, -7);
      } else {
        stan.taskCalendarAnchor = dodajDniDoDaty(anchor, -1);
      }
      renderujWidokKalendarzaZadan(items);
    };
  }
  if (nextButton) {
    nextButton.onclick = () => {
      if (mode === "miesiac") {
        stan.taskCalendarAnchor = new Date(anchor.getFullYear(), anchor.getMonth() + 1, 1);
      } else if (mode === "tydzien") {
        stan.taskCalendarAnchor = dodajDniDoDaty(anchor, 7);
      } else {
        stan.taskCalendarAnchor = dodajDniDoDaty(anchor, 1);
      }
      renderujWidokKalendarzaZadan(items);
    };
  }
  if (todayButton) {
    todayButton.onclick = () => {
      stan.taskCalendarAnchor = new Date();
      renderujWidokKalendarzaZadan(items);
    };
  }

  const zakres =
    mode === "miesiac"
      ? formatujNaglowekMiesiaca(anchor)
      : mode === "tydzien"
        ? `${formatujDzienKalendarza(poczatekTygodnia(anchor))} - ${formatujDzienKalendarza(koniecTygodnia(anchor))}`
        : formatujDzienKalendarza(anchor);
  if (labelNode) {
    labelNode.textContent = zakres;
  }
  if (countNode) {
    countNode.textContent = `${entries.length} terminow`;
  }

  const wydarzeniaDnia = new Map();
  entries.forEach((entry) => {
    const key = kalendarzKluczDnia(entry.date);
    if (!wydarzeniaDnia.has(key)) {
      wydarzeniaDnia.set(key, []);
    }
    wydarzeniaDnia.get(key).push(entry);
  });

  const renderujWierszDnia = (day, showHeader = true, compact = false) => {
    const key = kalendarzKluczDnia(day);
    const dayEntries = wydarzeniaDnia.get(key) || [];
    const dayEntriesByHour = new Map();
    dayEntries.forEach((entry) => {
      const hour = pobierzGodzineKalendarza(entry.date);
      if (hour === null) {
        return;
      }
      if (!dayEntriesByHour.has(hour)) {
        dayEntriesByHour.set(hour, []);
      }
      dayEntriesByHour.get(hour).push(entry);
    });
    const hasTimeSlots = mode === "dzien" && !compact;
    return `
      <section class="task-calendar-day ${key === activeDayKey ? "active" : ""}" data-calendar-drop-date="${key}">
        ${showHeader ? `<div class="task-calendar-day-header"><strong>${bezpiecznyTekst(formatujDzienKalendarza(day))}</strong><span class="pill">${dayEntries.length}</span></div>` : ""}
        ${
          hasTimeSlots
            ? `
              <div class="task-calendar-time-grid">
                ${Array.from({ length: 16 }, (_, index) => index + 6)
                  .map((hour) => {
                    const slotDateTime = zbudujDateCzasNaSlot(day, hour);
                    const slotEntries = (dayEntriesByHour.get(hour) || []).slice().sort((left, right) => {
                      const diff = left.date.getTime() - right.date.getTime();
                      if (diff !== 0) return diff;
                      return Number(left.task.task_id || 0) - Number(right.task.task_id || 0);
                    });
                    return `
                      <section class="task-calendar-time-slot ${key === activeDayKey ? "active" : ""}" data-calendar-drop-datetime="${slotDateTime}" data-calendar-drop-date="${key}">
                        <div class="task-calendar-time-slot-header">
                          <strong>${bezpiecznyTekst(formatujGodzineKalendarza(hour))}</strong>
                          <span class="pill">${slotEntries.length}</span>
                        </div>
                        <div class="task-calendar-time-slot-items">
                          ${
                            slotEntries.length
                              ? slotEntries.map((entry) => renderujKarteKalendarzaZadania(entry, { compact })).join("")
                              : '<div class="empty-state calendar-empty">Upusc wpis tutaj, aby ustawic ten slot.</div>'
                          }
                        </div>
                      </section>
                    `;
                  })
                  .join("")}
              </div>
            `
            : `
              <div class="task-calendar-day-items">
                ${
                  dayEntries.length
                    ? dayEntries.map((entry) => renderujKarteKalendarzaZadania(entry, { compact })).join("")
                    : '<div class="empty-state calendar-empty">Brak wpisow w tym dniu.</div>'
                }
              </div>
            `
        }
      </section>
    `;
  };

  if (!entries.length) {
    container.className = "empty-state task-calendar-body";
    container.innerHTML = "Brak wpisow z terminami w aktualnym zakresie.";
    return;
  }

  if (mode === "miesiac") {
    const start = poczatekTygodnia(poczatekMiesiaca(anchor));
    const cells = Array.from({ length: 42 }, (_, index) => dodajDniDoDaty(start, index));
    container.className = "task-calendar-body task-calendar-month";
    container.innerHTML = `
      <div class="task-calendar-weekdays">
        ${["Pon", "Wt", "Sr", "Czw", "Pt", "Sob", "Nd"].map((item) => `<div>${item}</div>`).join("")}
      </div>
      <div class="task-calendar-month-grid">
        ${cells
          .map((day) => {
            const key = kalendarzKluczDnia(day);
            const dayEntries = wydarzeniaDnia.get(key) || [];
            const outsideMonth = day.getMonth() !== anchor.getMonth();
            return `
              <button type="button" class="task-calendar-month-day ${outsideMonth ? "outside-month" : ""} ${key === activeDayKey ? "active" : ""}" data-task-calendar-focus="${key}" data-calendar-drop-date="${key}">
                <div class="task-calendar-month-day-top">
                  <strong>${day.getDate()}</strong>
                  <span class="pill">${dayEntries.length}</span>
                </div>
                <div class="task-calendar-month-day-items">
                  ${
                    dayEntries.length
                      ? dayEntries.slice(0, 3).map((entry) => `<div class="task-calendar-month-item">${bezpiecznyTekst(entry.date.toLocaleTimeString("pl-PL", { hour: "2-digit", minute: "2-digit" }))} ${bezpiecznyTekst(entry.task.title || "Wpis")}</div>`).join("")
                      : '<div class="muted calendar-empty">-</div>'
                  }
                </div>
                ${dayEntries.length > 3 ? `<div class="muted">+ ${dayEntries.length - 3} wiecej</div>` : ""}
              </button>
            `;
          })
          .join("")}
      </div>
    `;
    container.querySelectorAll("[data-task-calendar-focus]").forEach((button) => {
      button.addEventListener("click", () => {
        stan.taskCalendarMode = "dzien";
        stan.taskCalendarAnchor = new Date(`${button.dataset.taskCalendarFocus}T12:00:00`);
        renderujWidokKalendarzaZadan(items);
      });
    });
  } else if (mode === "tydzien") {
    const days = Array.from({ length: 7 }, (_, index) => dodajDniDoDaty(poczatekTygodnia(anchor), index));
    container.className = "task-calendar-body task-calendar-week-grid";
    container.innerHTML = `
      <div class="task-calendar-week-grid-columns">
        ${days
          .map((day) => {
            const key = kalendarzKluczDnia(day);
            const dayEntries = (wydarzeniaDnia.get(key) || []).slice().sort((left, right) => {
              const diff = left.date.getTime() - right.date.getTime();
              if (diff !== 0) return diff;
              return Number(left.task.task_id || 0) - Number(right.task.task_id || 0);
            });
            return `
              <section class="task-calendar-week-day ${key === activeDayKey ? "active" : ""}" data-calendar-drop-date="${key}">
                <div class="task-calendar-week-day-header">
                  <strong>${bezpiecznyTekst(formatujDzienKalendarza(day))}</strong>
                  <span class="pill">${dayEntries.length}</span>
                </div>
                <div class="task-calendar-week-day-items">
                  ${
                  dayEntries.length
                    ? dayEntries
                          .map((entry) => renderujKarteKalendarzaZadania(entry, { compact: true }))
                          .join("")
                      : '<div class="empty-state calendar-empty">Brak wpisow w tym dniu. Upusc tu wpis, aby przeniesc go na ten dzien.</div>'
                  }
                </div>
              </section>
            `;
          })
          .join("")}
      </div>
    `;
  } else {
    container.className = "task-calendar-body task-calendar-agenda task-calendar-day-view";
    container.innerHTML = renderujWierszDnia(anchor, true, false);
    container.querySelectorAll("[data-task-move-days]").forEach((button) => {
      button.addEventListener("click", async (event) => {
        event.preventDefault();
        event.stopPropagation();
        try {
          await przesunTerminZadania(Number(button.dataset.taskId), Number(button.dataset.taskMoveDays), "dni");
        } catch (error) {
          pokazPowiadomienie(error.message);
        }
      });
    });
    container.querySelectorAll("[data-task-move-hours]").forEach((button) => {
      button.addEventListener("click", async (event) => {
        event.preventDefault();
        event.stopPropagation();
        try {
          await przesunTerminZadania(Number(button.dataset.taskId), Number(button.dataset.taskMoveHours), "godziny");
        } catch (error) {
          pokazPowiadomienie(error.message);
        }
      });
    });
  }

  container.querySelectorAll(".task-calendar-entry").forEach((item) => {
    item.addEventListener("click", () => wczytajSzczegolyZadania(Number(item.dataset.taskId)));
    item.addEventListener("dragstart", (event) => {
      stan.taskCalendarDragTaskId = Number(item.dataset.taskId || 0);
      stan.taskCalendarDragSourceField = String(item.dataset.taskCalendarSource || "termin");
      stan.taskCalendarDragSourceDate = item.dataset.taskId ? znajdzZadaniePoId(item.dataset.taskId) : null;
      event.dataTransfer.effectAllowed = "move";
      event.dataTransfer.setData("text/plain", String(item.dataset.taskId || ""));
      item.classList.add("is-dragging");
    });
    item.addEventListener("dragend", () => {
      stan.taskCalendarDragTaskId = null;
      stan.taskCalendarDragSourceField = null;
      stan.taskCalendarDragSourceDate = null;
      item.classList.remove("is-dragging");
    });
  });

  container.querySelectorAll("[data-calendar-drop-date]:not([data-calendar-drop-datetime])").forEach((target) => {
    target.addEventListener("dragover", (event) => {
      if (!event.dataTransfer.types.includes("text/plain")) {
        return;
      }
      event.preventDefault();
      target.classList.add("is-drop-target");
    });
    target.addEventListener("dragleave", () => {
      target.classList.remove("is-drop-target");
    });
    target.addEventListener("drop", async (event) => {
      event.preventDefault();
      event.stopPropagation();
      target.classList.remove("is-drop-target");
      const taskId = Number(event.dataTransfer.getData("text/plain") || stan.taskCalendarDragTaskId || 0);
      const targetDate = String(target.dataset.calendarDropDate || "").trim();
      if (!taskId || !targetDate) {
        return;
      }
      try {
        await przesunTerminZadaniaDoDaty(taskId, targetDate);
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
    });
  });

  container.querySelectorAll("[data-calendar-drop-datetime]").forEach((target) => {
    target.addEventListener("dragover", (event) => {
      if (!event.dataTransfer.types.includes("text/plain")) {
        return;
      }
      event.preventDefault();
      target.classList.add("is-drop-target");
    });
    target.addEventListener("dragleave", () => {
      target.classList.remove("is-drop-target");
    });
    target.addEventListener("drop", async (event) => {
      event.preventDefault();
      event.stopPropagation();
      target.classList.remove("is-drop-target");
      const taskId = Number(event.dataTransfer.getData("text/plain") || stan.taskCalendarDragTaskId || 0);
      const targetDateTime = String(target.dataset.calendarDropDatetime || "").trim();
      if (!taskId || !targetDateTime) {
        return;
      }
      try {
        await przesunTerminZadaniaDoSlotu(taskId, targetDateTime);
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
    });
  });
}

function pobierzDomyslnaDateSzybkiegoWpisu() {
  const anchor = stan.taskCalendarAnchor instanceof Date && !Number.isNaN(stan.taskCalendarAnchor.getTime())
    ? new Date(stan.taskCalendarAnchor)
    : null;
  if (anchor) {
    return new Date(anchor.getFullYear(), anchor.getMonth(), anchor.getDate(), 9, 0, 0, 0);
  }
  const now = new Date();
  now.setMinutes(Math.ceil(now.getMinutes() / 15) * 15, 0, 0);
  return now;
}

function odejmijMinutyOdDaty(value, minutes) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  date.setMinutes(date.getMinutes() - Math.max(0, Number(minutes) || 0));
  return formatujDateCzasDoInput(date);
}

function odswiezWidocznoscSzybkiegoWpisu() {
  const sheet = document.getElementById("task-quick-add-sheet");
  if (!sheet) {
    return;
  }
  const isOpen = sheet.classList.contains("open");
  sheet.classList.toggle("hidden", !isOpen);
  sheet.setAttribute("aria-hidden", isOpen ? "false" : "true");
}

function wypelnijSzybkiWpisDomyslami(prefillDate = null) {
  const dueAtInput = document.getElementById("task-quick-add-due-at");
  const titleInput = document.getElementById("task-quick-add-title");
  const typeInput = document.getElementById("task-quick-add-type");
  const priorityInput = document.getElementById("task-quick-add-priority");
  const reminderOffsetInput = document.getElementById("task-quick-add-reminder-offset");
  const descriptionInput = document.getElementById("task-quick-add-description");
  const baseDate = prefillDate ? new Date(prefillDate) : pobierzDomyslnaDateSzybkiegoWpisu();
  if (dueAtInput) {
    dueAtInput.value = formatujDateCzasDoInput(baseDate);
  }
  if (titleInput) {
    titleInput.value = "";
  }
  if (typeInput) {
    typeInput.value = "zadanie";
  }
  if (priorityInput) {
    priorityInput.value = "normalny";
  }
  if (reminderOffsetInput) {
    reminderOffsetInput.value = "60";
  }
  if (descriptionInput) {
    descriptionInput.value = "";
  }
}

function otworzSzybkiWpis(prefillDate = null) {
  const sheet = document.getElementById("task-quick-add-sheet");
  if (!sheet || !czyMoznaZapisywac()) {
    return;
  }
  const titleInput = document.getElementById("task-quick-add-title");
  sheet.classList.remove("hidden");
  sheet.classList.add("open");
  sheet.setAttribute("aria-hidden", "false");
  wypelnijSzybkiWpisDomyslami(prefillDate);
  if (titleInput) {
    window.setTimeout(() => titleInput.focus(), 0);
  }
}

function zamknijSzybkiWpis() {
  const sheet = document.getElementById("task-quick-add-sheet");
  if (!sheet) {
    return;
  }
  sheet.classList.remove("open");
  sheet.classList.add("hidden");
  sheet.setAttribute("aria-hidden", "true");
}

async function przesunTerminZadania(taskId, przesuniecie, jednostka = "dni") {
  const normalizedTaskId = Number(taskId || 0);
  const delta = Number(przesuniecie || 0);
  const normalizedUnit = String(jednostka || "dni").trim().toLowerCase();
  if (!normalizedTaskId || !delta || !czyMoznaZapisywac()) {
    return null;
  }
  const task = Array.isArray(stan.zadania)
    ? stan.zadania.find((item) => Number(item.task_id) === normalizedTaskId)
    : null;
  if (!task) {
    throw new Error("Nie znaleziono wpisu do przesuniecia.");
  }

  const payload = {};
  const deltaMs = delta * (normalizedUnit === "godziny" ? 60 * 60 * 1000 : 24 * 60 * 60 * 1000);
  if (task.due_at) {
    const dueDate = new Date(task.due_at);
    if (!Number.isNaN(dueDate.getTime())) {
      dueDate.setTime(dueDate.getTime() + deltaMs);
      payload.due_at = formatujDateCzasDoInput(dueDate);
    }
  }
  if (task.remind_at) {
    const remindDate = new Date(task.remind_at);
    if (!Number.isNaN(remindDate.getTime())) {
      remindDate.setTime(remindDate.getTime() + deltaMs);
      payload.remind_at = formatujDateCzasDoInput(remindDate);
    }
  }

  if (!payload.due_at && !payload.remind_at) {
    throw new Error("Ten wpis nie ma jeszcze terminu do przesuniecia.");
  }
  const targetStart = payload.due_at || payload.remind_at || "";
  const proceed = await potwierdzKolizjeKalendarza(task, targetStart, normalizedUnit === "godziny" ? "przesuniecie o godzine" : "przesuniecie o dzien");
  if (!proceed) {
    return null;
  }

  const detail = await api(zbudujAdresZOrganizacja(`/api/tasks/${normalizedTaskId}`), {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
  const unitLabel = normalizedUnit === "godziny" ? (Math.abs(delta) === 1 ? "godzine" : "godziny") : Math.abs(delta) === 1 ? "dzien" : "dni";
  pokazPowiadomienie(`Przesunieto wpis o ${Math.abs(delta)} ${unitLabel}.`);
  await Promise.all([wczytajZadania(), wczytajPlannerZadan(), wczytajFokusZadan(), wczytajLogi(), wczytajPulpit()]);
  if (Number(stan.wybraneZadanieId) === normalizedTaskId) {
    renderujPanelZadania(detail);
  }
  return detail;
}

async function przesunTerminZadaniaDoSlotu(taskId, targetDateTime) {
  const normalizedTaskId = Number(taskId || 0);
  const task = Array.isArray(stan.zadania)
    ? stan.zadania.find((item) => Number(item.task_id) === normalizedTaskId)
    : null;
  if (!normalizedTaskId || !task || !czyMoznaZapisywac()) {
    return null;
  }
  const targetDate = new Date(String(targetDateTime || ""));
  if (Number.isNaN(targetDate.getTime())) {
    throw new Error("Nie udalo sie odczytac wybranego slotu czasu.");
  }
  const payload = {};
  if (task.due_at) {
    const dueDate = new Date(task.due_at);
    if (!Number.isNaN(dueDate.getTime())) {
      const offsetMinutes = task.remind_at
        ? Math.round((new Date(task.remind_at).getTime() - dueDate.getTime()) / 60000)
        : 0;
      payload.due_at = formatujDateCzasDoInput(targetDate);
      if (task.remind_at) {
        const movedRemind = new Date(targetDate.getTime() + offsetMinutes * 60000);
        payload.remind_at = formatujDateCzasDoInput(movedRemind);
      }
    }
  } else if (task.remind_at) {
    payload.remind_at = formatujDateCzasDoInput(targetDate);
  } else {
    payload.due_at = formatujDateCzasDoInput(targetDate);
  }
  const targetStart = payload.due_at || payload.remind_at || "";
  if (!targetStart) {
    throw new Error("Nie mozna przeniesc wpisu bez terminu.");
  }
  const proceed = await potwierdzKolizjeKalendarza(task, targetStart, "przesuniecie na slot");
  if (!proceed) {
    return null;
  }
  const detail = await api(zbudujAdresZOrganizacja(`/api/tasks/${normalizedTaskId}`), {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
  pokazPowiadomienie("Przeniesiono wpis do wybranego slotu czasu.");
  await Promise.all([wczytajZadania(), wczytajPlannerZadan(), wczytajFokusZadan(), wczytajLogi(), wczytajPulpit()]);
  if (Number(stan.wybraneZadanieId) === normalizedTaskId) {
    renderujPanelZadania(detail);
  }
  return detail;
}

async function zapiszSzybkiWpis() {
  if (!czyMoznaZapisywac()) {
    return;
  }
  const title = document.getElementById("task-quick-add-title")?.value?.trim() || "";
  if (!title) {
    throw new Error("Wpisz tytul szybkiego wpisu.");
  }
  const taskType = document.getElementById("task-quick-add-type")?.value || "zadanie";
  const priority = document.getElementById("task-quick-add-priority")?.value || "normalny";
  const reminderOffset = Number(document.getElementById("task-quick-add-reminder-offset")?.value || 0);
  const description = document.getElementById("task-quick-add-description")?.value?.trim() || "";
  let dueAt = document.getElementById("task-quick-add-due-at")?.value?.trim() || "";
  if (!dueAt && (taskType === "przypomnienie" || reminderOffset > 0)) {
    dueAt = formatujDateCzasDoInput(pobierzDomyslnaDateSzybkiegoWpisu());
  }

  const payload = {
    title,
    task_type: taskType,
    status: "nowe",
    priority,
    description,
    visibility_scope: "prywatne",
  };
  const ownerUserId = Number(stan.biezacyUzytkownik?.user_id || 0);
  if (ownerUserId) {
    payload.assigned_user_id = ownerUserId;
  }
  if (dueAt) {
    payload.due_at = dueAt;
  }
  if (taskType === "przypomnienie") {
    payload.remind_at = reminderOffset > 0 ? odejmijMinutyOdDaty(dueAt, reminderOffset) : dueAt;
  } else if (reminderOffset > 0 && dueAt) {
    payload.remind_at = odejmijMinutyOdDaty(dueAt, reminderOffset);
  }

  const created = await api(zbudujAdresZOrganizacja("/api/tasks"), {
    method: "POST",
    body: JSON.stringify(payload),
  });
  zamknijSzybkiWpis();
  pokazPowiadomienie("Dodano szybki wpis.");
  await Promise.all([wczytajZadania(), wczytajPlannerZadan(), wczytajFokusZadan(), wczytajLogi(), wczytajPulpit()]);
  if (created?.task_id && Number(stan.wybraneZadanieId) !== Number(created.task_id)) {
    renderujWidokKalendarzaZadan(stan.zadania);
  }
}

function renderujPanelZadania(detail = null) {
  const task = detail?.task || null;
  stan.wybraneZadanieDetail = detail || null;
  const zablokowane = !czyMoznaZapisywac();
  const atrybutPola = zablokowane ? 'disabled aria-disabled="true"' : "";
  const atrybutPrzycisku = zablokowane ? 'disabled title="Ta rola ma tylko podglÄ…d danych."' : "";
  const zablokowaneRelacje = zablokowane || !czyMoznaPrzypisywacZadania();
  const atrybutRelacji = zablokowaneRelacje
    ? 'disabled title="Ta rola nie moĹĽe zmieniaÄ‡ przypisania ani widocznoĹ›ci zadania."'
    : "";
  const taskId = task?.task_id || "";
  const ownerUserId = pobierzWlascicielaWpisu(task);
  const visibilityScope = task?.visibility_scope || "prywatne";
  const reminderInfo = pobierzStanPrzypomnienia(task);
  const reminderError = String(task?.reminder_last_error || "").trim();
  const syncInfo = pobierzStanSynchronizacjiGoogle(task);
  const selectedCalendarId = Number(task?.calendar_id || pobierzSugerowanyKalendarzDlaAktywnejOrganizacji() || 0);
  const selectedCalendar = pobierzKalendarzUzytkownika(selectedCalendarId);
  const initialCalendarDuration = Number(
    task?.calendar_duration_minutes || selectedCalendar?.default_duration_minutes || 60
  );
  const recurrenceApplyScope = task?.recurrence_enabled ? "tylko_ten" : "";
  const recurrenceScopeOptions = (stan.meta?.task_recurrence_edit_scopes || ["tylko_ten", "ten_i_nastepne", "cala_seria"])
    .map(
      (item) => `<option value="${item}" ${item === recurrenceApplyScope ? "selected" : ""}>${formatujZakresEdycjiSeriiZadania(item)}</option>`
    )
    .join("");
  const czyMoznaWyslacPrzypomnienieTeraz = Boolean(
    task?.task_id &&
      task?.remind_at &&
      czyMoznaZapisywac() &&
      !["zakonczone", "anulowane"].includes(task?.status || "")
  );
  const czyMoznaOdkladacPrzypomnienie = Boolean(
    task?.task_id &&
      task?.remind_at &&
      czyMoznaZapisywac() &&
      !["zakonczone", "anulowane"].includes(task?.status || "")
  );
  const czyMoznaSynchronizowacKalendarzTeraz = Boolean(
    task?.task_id &&
      task?.calendar_name &&
      task?.calendar_provider === "google_api" &&
      czyMoznaZapisywac()
  );
  const czyMoznaSprawdzicStanKalendarza = Boolean(
    task?.task_id &&
      task?.calendar_name &&
      task?.calendar_provider === "google_api" &&
      czyMoznaZapisywac()
  );
  const visibleUsersText =
    visibilityScope === "organizacja"
      ? "Wszyscy w organizacji"
      : visibilityScope === "prywatne"
        ? "Tylko wlasciciel"
        : task?.visible_user_names?.length
          ? task.visible_user_names.map((item) => bezpiecznyTekst(item)).join(", ")
          : "-";
  stan.wybraneZadanieId = task ? Number(task.task_id) : null;

  const opcjeUzytkownikow = [`<option value="">Bez przypisania</option>`]
    .concat(
      stan.uzytkownicyDoZadan.map((uzytkownik) => {
        const zaznaczone = Number(task?.assigned_user_id) === Number(uzytkownik.user_id) ? "selected" : "";
        const suffix = czyGlobalnyAdministrator() && uzytkownik.organization_name ? ` | ${uzytkownik.organization_name}` : "";
        return `<option value="${uzytkownik.user_id}" ${zaznaczone}>${bezpiecznyTekst(uzytkownik.display_name)}${bezpiecznyTekst(suffix)}</option>`;
      })
    )
    .join("");
  const opcjeKalendarzy = [`<option value="">Bez kalendarza Google</option>`]
    .concat(
      stan.kalendarzeUzytkownika
        .filter((kalendarz) => kalendarz.is_active || selectedCalendarId === Number(kalendarz.user_calendar_id))
        .map((kalendarz) => {
          const zaznaczone = selectedCalendarId === Number(kalendarz.user_calendar_id) ? "selected" : "";
          const status = kalendarz.is_active ? "" : " (nieaktywny)";
          const providerSuffix =
            kalendarz.provider === "google_api" && kalendarz.external_calendar_name
              ? ` | ${kalendarz.external_calendar_name}`
              : kalendarz.provider_label
                ? ` | ${kalendarz.provider_label}`
                : "";
          const scope = kalendarz.linked_organization_name
            ? ` | ${kalendarz.linked_organization_name}`
            : kalendarz.calendar_kind && kalendarz.calendar_kind !== "inne"
              ? ` | ${formatujRodzajKalendarza(kalendarz.calendar_kind)}`
              : "";
          return `<option value="${kalendarz.user_calendar_id}" ${zaznaczone}>${bezpiecznyTekst(
            kalendarz.display_name
          )}${bezpiecznyTekst(providerSuffix)}${bezpiecznyTekst(scope)}${bezpiecznyTekst(status)}</option>`;
        })
    )
    .join("");

  document.getElementById("task-detail-empty").classList.add("hidden");
  const container = document.getElementById("task-detail");
  container.classList.remove("hidden");

  container.innerHTML = `
    <div class="detail-grid">
        <div class="summary-grid">
          <div class="summary-item"><strong>ID zadania</strong>${taskId || "Nowe zadanie"}</div>
          <div class="summary-item"><strong>Organizacja</strong>${formatujNazweOrganizacji(task?.organization_name || pobierzAktywnaOrganizacje()?.name || stan.biezacyUzytkownik?.organization_name)}</div>
          <div class="summary-item"><strong>Widocznosc</strong>${task ? formatujWidocznoscZadania(task.visibility_scope) : "Prywatne"}</div>
          <div class="summary-item"><strong>Typ</strong>${task ? formatujTypZadania(task.task_type) : "-"}</div>
          <div class="summary-item"><strong>Status</strong>${task ? `<span class="status-badge ${klasaStatusuZadania(task.status, task.priority)}">${formatujStatusZadania(task.status)}</span>` : "-"}</div>
          <div class="summary-item"><strong>Priorytet</strong>${task ? formatujPriorytetZadania(task.priority) : "-"}</div>
            <div class="summary-item"><strong>Termin</strong>${formatujDateCzas(task?.due_at)}</div>
            <div class="summary-item"><strong>Przypomnienie</strong>${task?.remind_at ? `${formatujDateCzas(task.remind_at)}<div class="muted"><span class="status-badge ${reminderInfo.klasa}">${reminderInfo.etykieta}</span></div>${reminderError ? `<div class="muted">${bezpiecznyTekst(reminderError)}</div>` : ""}` : "-"}</div>
            <div class="summary-item"><strong>Odbiorca przypomnienia</strong>${task?.remind_at ? `${bezpiecznyTekst(task?.reminder_target_label || "Brak gotowego odbiorcy")}${task?.reminder_target_ready ? "" : '<div class="muted">Przypomnienie nie jest jeszcze gotowe do wysylki.</div>'}` : "Brak przypomnienia"}</div>
            <div class="summary-item"><strong>Kalendarz Google</strong>${task?.calendar_name ? `${formatujWartosc(task?.calendar_name)}<div class="muted">${bezpiecznyTekst(task?.calendar_provider_label || "Google Calendar")}${task?.calendar_external_calendar_name ? ` | ${bezpiecznyTekst(task?.calendar_external_calendar_name)}` : ""}</div><div class="muted">${bezpiecznyTekst(task?.calendar_linked_organization_name || formatujRodzajKalendarza(task?.calendar_kind))}</div>` : "-"}</div>
            <div class="summary-item"><strong>Synchronizacja Google</strong>${renderujStanSynchronizacjiGoogle(task, { szczegoly: true })}${task?.calendar_provider === "google_api" && task?.calendar_external_calendar_name ? `<div class="muted">Docelowy kalendarz Google: ${bezpiecznyTekst(task.calendar_external_calendar_name)}</div>` : ""}${task?.calendar_provider === "google_api" && task?.external_calendar_event_url ? `<div style="margin-top:8px;"><a href="${bezpiecznyTekst(task.external_calendar_event_url)}" target="_blank" rel="noopener noreferrer">Otworz wpis w Google Calendar</a></div>` : ""}${task?.calendar_provider === "google_api" && syncInfo?.etykieta === "Oczekuje synchronizacji" && task?.calendar_name ? `<div class="muted">Po zapisie wpis powinien pojawic sie w wybranym kalendarzu Google.</div>` : ""}</div>
            <div class="summary-item"><strong>Czas w kalendarzu</strong>${task?.calendar_name ? `${task?.calendar_duration_minutes || 60} min` : "-"}</div>
            <div class="summary-item"><strong>Cyklicznosc</strong>${bezpiecznyTekst(task?.recurrence_summary || "Brak cyklicznosci")}</div>
            <div class="summary-item"><strong>Wlasciciel</strong>${formatujWartosc(task?.owner_user_name || stan.biezacyUzytkownik?.display_name || stan.biezacyUzytkownik?.login)}</div>
            <div class="summary-item"><strong>Przypisano</strong>${formatujWartosc(task?.assigned_user_name)}</div>
            <div class="summary-item"><strong>Udostepniono</strong>${visibleUsersText}</div>
            <div class="summary-item"><strong>Powiazania biznesowe</strong>${task?.linked_entities?.length ? task.linked_entities.map((item) => `<div>${bezpiecznyTekst(formatujEtykietePowiazaniaBiznesowego(item))}</div>`).join("") : "Brak powiazan"}</div>
            <div class="summary-item"><strong>Dodane przez</strong>${formatujWartosc(task?.created_by_user_name)}</div>
        </div>

      <div class="detail-actions">
        <button id="save-task-button" ${atrybutPrzycisku}>Zapisz wpis</button>
        <button class="secondary" id="reset-task-button">Nowy wpis</button>
        ${
          task?.task_id
            ? `<button class="secondary" id="send-task-reminder-now-button" ${czyMoznaWyslacPrzypomnienieTeraz ? "" : 'disabled title="Ustaw aktywne przypomnienie, aby wyslac je teraz."'}>Wyslij przypomnienie teraz</button>`
            : ""
        }
        ${
          task?.task_id
            ? `<button class="secondary" id="task-snooze-10m-button" ${czyMoznaOdkladacPrzypomnienie ? "" : 'disabled title="Ten wpis nie ma aktywnego przypomnienia do odlozenia."'}>Odloz o 10 min</button>`
            : ""
        }
        ${
          task?.task_id
            ? `<button class="secondary" id="task-snooze-1h-button" ${czyMoznaOdkladacPrzypomnienie ? "" : 'disabled title="Ten wpis nie ma aktywnego przypomnienia do odlozenia."'}>Odloz o 1 h</button>`
            : ""
        }
        ${
          task?.task_id
            ? `<button class="secondary" id="task-snooze-tomorrow-button" ${czyMoznaOdkladacPrzypomnienie ? "" : 'disabled title="Ten wpis nie ma aktywnego przypomnienia do odlozenia."'}>Jutro rano</button>`
            : ""
        }
        ${
          task?.task_id
            ? `<button class="secondary" id="sync-task-calendar-button" ${czyMoznaSynchronizowacKalendarzTeraz ? "" : 'disabled title="Reczna synchronizacja jest dostepna tylko dla wpisow zapisanych bezposrednio do Google Calendar."'}>Synchronizuj ponownie</button>`
            : ""
        }
        ${
          task?.task_id
            ? `<button class="secondary" id="check-task-calendar-button" ${czyMoznaSprawdzicStanKalendarza ? "" : 'disabled title="Sprawdzenie stanu jest dostepne tylko dla wpisow zapisanych bezposrednio do Google Calendar."'}>Sprawdz stan w Google</button>`
            : ""
        }
      </div>

      <div id="task-save-impact" class="task-save-impact"></div>

      <div class="panel">
        <div class="panel-header"><h3>Formularz wpisu</h3></div>
        <form id="task-form" class="field-grid">
          <input type="hidden" id="task-id" value="${bezpiecznyTekst(taskId)}" />
          <input type="hidden" id="task-owner-user-id" value="${bezpiecznyTekst(ownerUserId)}" />
          <div class="field field-full task-form-section">
            <div class="task-form-section-title">Podstawowe</div>
            <div class="task-form-section-copy">Najpierw ustaw typ wpisu, tresc i priorytet. To jest glowny opis pracy.</div>
          </div>
          <div class="field">
            <label>Tytul</label>
            <input id="task-title" name="title" value="${bezpiecznyTekst(task?.title || "")}" ${atrybutPola} />
          </div>
          <div class="field">
            <label>Typ</label>
            <select id="task-type" name="task_type" ${atrybutPola}>
              ${stan.meta.task_types
                .map((item) => `<option value="${item}" ${item === (task?.task_type || "zadanie") ? "selected" : ""}>${formatujTypZadania(item)}</option>`)
                .join("")}
            </select>
          </div>
          <div class="field">
            <label>Status</label>
            <select id="task-status" name="status" ${atrybutPola}>
              ${stan.meta.task_statuses
                .map((item) => `<option value="${item}" ${item === (task?.status || "nowe") ? "selected" : ""}>${formatujStatusZadania(item)}</option>`)
                .join("")}
            </select>
          </div>
          <div class="field">
            <label>Priorytet</label>
            <select id="task-priority" name="priority" ${atrybutPola}>
              ${stan.meta.task_priorities
                .map((item) => `<option value="${item}" ${item === (task?.priority || "normalny") ? "selected" : ""}>${formatujPriorytetZadania(item)}</option>`)
                .join("")}
            </select>
          </div>
          <div class="field field-full task-form-section">
            <div class="task-form-section-title">Widocznosc i odpowiedzialnosc</div>
            <div class="task-form-section-copy">Tutaj ustawiasz kto zobaczy wpis i kto ma sie nim zajac.</div>
          </div>
          <div class="field field-full">
            <label>Widocznosc</label>
            ${zbudujPrzelacznikWidocznosci(visibilityScope, zablokowaneRelacje)}
            <div id="task-visibility-note" class="field-note"></div>
          </div>
            <div class="field">
              <label>Przypisano</label>
              <select id="task-assigned-user" name="assigned_user_id" ${atrybutRelacji}>${opcjeUzytkownikow}</select>
            </div>
          <div class="field">
            <label>Kalendarz Google</label>
            <select id="task-calendar-id" name="calendar_id" ${atrybutPola}>${opcjeKalendarzy}</select>
          </div>
          <div class="field field-full task-form-section">
            <div class="task-form-section-title">Powiazania biznesowe</div>
            <div class="task-form-section-copy">Tu widzisz, z jaka faktura albo kontrahentem jest polaczony wpis. Nowe powiazania najlepiej dodawac z poziomu szczegolow faktury lub kontrahenta.</div>
          </div>
          <div class="field field-full">
            <label>Powiazane obiekty</label>
            <div id="task-linked-entities-shell"></div>
            <div class="field-note">Powiazania pomagaja zobaczyc otwarte sprawy bezposrednio przy fakturze i kontrahencie.</div>
          </div>
            <div class="field field-full task-form-section">
              <div class="task-form-section-title">Terminy i przypomnienia</div>
              <div class="task-form-section-copy">To tutaj decydujesz, kiedy wpis ma sie wydarzyc i kto powinien dostac alert.</div>
            </div>
              <div class="field">
                <label>Termin</label>
                <input id="task-due-at" name="due_at" type="datetime-local" value="${bezpiecznyTekst(formatujDateCzasDoInput(task?.due_at))}" ${atrybutPola} />
              </div>
              <div class="field">
                <label>Przypomnij o</label>
                <input id="task-remind-at" name="remind_at" type="datetime-local" value="${bezpiecznyTekst(formatujDateCzasDoInput(task?.remind_at))}" ${atrybutPola} />
              </div>
              <div class="field field-full task-form-section">
                <div class="task-form-section-title">Kalendarz i cyklicznosc</div>
                <div class="task-form-section-copy">To jest warstwa bardziej zaawansowana: Google Calendar, czas wpisu i ustawienia serii.</div>
              </div>
              <div class="field">
                <label>Czas wpisu w kalendarzu (min)</label>
                <input id="task-calendar-duration" name="calendar_duration_minutes" type="number" min="1" max="1440" step="5" value="${bezpiecznyTekst(initialCalendarDuration)}" ${atrybutPola} />
              </div>
              <div class="field">
                <label>Cyklicznosc</label>
                <select id="task-recurrence-pattern" name="recurrence_pattern" ${atrybutPola}>
                  ${(stan.meta.task_recurrence_patterns || ["brak"])
                    .map(
                      (item) =>
                        `<option value="${item}" ${item === (task?.recurrence_pattern || "brak") ? "selected" : ""}>${formatujCyklicznoscZadania(item)}</option>`
                    )
                    .join("")}
                </select>
              </div>
              <div class="field">
                <label>Interwal cyklu</label>
                <input id="task-recurrence-interval" name="recurrence_interval" type="number" min="1" max="365" step="1" value="${bezpiecznyTekst(task?.recurrence_interval || 1)}" ${atrybutPola} />
              </div>
              <div class="field">
                <label>Koniec cyklu</label>
                <input id="task-recurrence-end-at" name="recurrence_end_at" type="datetime-local" value="${bezpiecznyTekst(formatujDateCzasDoInput(task?.recurrence_end_at))}" ${atrybutPola} />
              </div>
              <div class="field hidden" id="task-recurrence-scope-field">
                <label>Zakres zapisu serii</label>
                <select id="task-recurrence-apply-scope" ${atrybutPola}>${recurrenceScopeOptions}</select>
                <div class="field-note">Zamkniete historyczne wpisy pozostana bez zmian, nawet przy opcji Cala seria.</div>
              </div>
              <input id="task-recurrence-weekdays" name="recurrence_weekdays" type="hidden" value="${bezpiecznyTekst(task?.recurrence_weekdays || "")}" />
              <div class="field field-full hidden" id="task-visible-users-field">
              <label>Widoczne dla wybranych osob</label>
              ${zbudujListeWidocznosciUzytkownikow(task, detail, zablokowaneRelacje)}
              <div class="field-note">Wlasciciel zawsze widzi swoj wpis, nawet jesli nie jest na liscie.</div>
            </div>
            <div class="field field-full">
            <label>Opis</label>
            <textarea id="task-description" name="description" ${atrybutPola}>${bezpiecznyTekst(task?.description || "")}</textarea>
          </div>
          <div class="field field-full">
            <div class="recurrence-note">Cykliczne wpisy tworza kolejne wystapienie po oznaczeniu biezacego wpisu jako wykonany.</div>
          </div>
        </form>
      </div>

      <div class="detail-columns">
        <div class="panel">
          <div class="panel-header"><h3>Zalaczniki</h3></div>
          ${renderujZalacznikiZadan(detail?.attachments || [])}
          ${
            task
              ? `
                <div class="panel-header" style="margin-top: 16px;"><h3>Dodaj zalacznik</h3></div>
                <div class="stack">
                  <div class="inline-file-row">
                    <input id="task-attachment-file" type="file" ${atrybutPola} />
                    <button type="button" id="task-attachment-upload-button" ${atrybutPrzycisku}>Dodaj plik</button>
                  </div>
                  <div class="inline-file-row">
                    <input id="task-attachment-link-title" type="text" placeholder="Nazwa linku" ${atrybutPola} />
                    <input id="task-attachment-link-url" type="url" placeholder="https://..." ${atrybutPola} />
                    <button type="button" id="task-attachment-link-upload-button" class="secondary" ${atrybutPrzycisku}>Dodaj link</button>
                  </div>
                  <div class="field-note">Obsluga plikow do 8 MB. Mozesz tez dodac link do dokumentu, notatki lub materialu zewnetrznego.</div>
                </div>
              `
              : `<div class="empty-state">Zalaczniki mozna dodawac po zapisaniu wpisu.</div>`
          }
        </div>
        <div class="panel">
          <div class="panel-header"><h3>Komentarze i checklista</h3></div>
          ${renderujNotatkiZadan(detail?.notes || [])}
          <div class="panel-header" style="margin-top: 18px;"><h3>Checklista</h3></div>
          ${renderujChecklistZadan(detail?.checklist_items || [], task, zablokowane)}
          ${
            task
              ? `
                <div class="panel-header" style="margin-top: 16px;"><h3>Dodaj komentarz</h3></div>
                <form id="task-note-form" class="stack">
                  <div id="task-note-reply-target" class="field-note"></div>
                  <input type="hidden" id="task-note-parent-id" value="" />
                  <input type="hidden" id="task-note-kind" value="comment" />
                  <textarea id="task-note-text" placeholder="Zapisz ustalenie, komentarz albo wynik rozmowy. Uzyj @login, aby wspomniec osobe." ${atrybutPola}></textarea>
                  <div class="detail-actions">
                    <button type="button" class="secondary" id="task-note-clear-reply" ${atrybutPrzycisku}>Anuluj odpowiedz</button>
                    <button type="submit" ${atrybutPrzycisku}>Dodaj komentarz</button>
                  </div>
                </form>
              `
              : `<div class="empty-state">Komentarze mozna dodawac po zapisaniu zadania.</div>`
          }
        </div>
        <div class="panel">
          <div class="panel-header"><h3>Akceptacje</h3></div>
          ${renderujSekcjeAkceptacji("task", task?.task_id || 0, detail?.approval_requests || [], {
            canWrite: !zablokowane,
            title: "Akceptacje wpisu",
            emptyLabel: "Brak wnioskow akceptacyjnych dla tego wpisu.",
          })}
        </div>
        <div class="panel">
          <div id="task-templates-panel"></div>
        </div>
        <div class="panel">
          <div class="panel-header"><h3>Historia zadania</h3></div>
          ${renderujHistorieZadan(detail?.history || [])}
        </div>
      </div>
    </div>
  `;

  ustawPowiazaniaEdytowanegoZadania(task?.linked_entities || [], {
    silent: true,
    editable: !zablokowane,
  });
  renderujSzablonyZadan(task, detail?.checklist_items || []);
  ustawCelOdpowiedziNotatki(stan.taskNoteReplyTarget);

  document.getElementById("save-task-button")?.addEventListener("click", zapiszZadanie);
  document.getElementById("reset-task-button")?.addEventListener("click", przygotujNoweZadanie);
  const przyciskWysylkiPrzypomnienia = document.getElementById("send-task-reminder-now-button");
    if (przyciskWysylkiPrzypomnienia) {
      przyciskWysylkiPrzypomnienia.addEventListener("click", async () => {
        try {
          await wyslijPrzypomnienieZadaniaTeraz();
        } catch (error) {
          pokazPowiadomienie(error.message);
        }
      });
    }
    const przyciskOdlozenia10Min = document.getElementById("task-snooze-10m-button");
    if (przyciskOdlozenia10Min) {
      przyciskOdlozenia10Min.addEventListener("click", async () => {
        try {
          await odlozPrzypomnienieZadania(stan.wybraneZadanieId, "10m");
        } catch (error) {
          pokazPowiadomienie(error.message);
        }
      });
    }
    const przyciskOdlozenia1H = document.getElementById("task-snooze-1h-button");
    if (przyciskOdlozenia1H) {
      przyciskOdlozenia1H.addEventListener("click", async () => {
        try {
          await odlozPrzypomnienieZadania(stan.wybraneZadanieId, "1h");
        } catch (error) {
          pokazPowiadomienie(error.message);
        }
      });
    }
    const przyciskOdlozeniaJutro = document.getElementById("task-snooze-tomorrow-button");
    if (przyciskOdlozeniaJutro) {
      przyciskOdlozeniaJutro.addEventListener("click", async () => {
        try {
          await odlozPrzypomnienieZadania(stan.wybraneZadanieId, "jutro_rano");
        } catch (error) {
          pokazPowiadomienie(error.message);
        }
      });
    }
    const przyciskSynchronizacjiKalendarza = document.getElementById("sync-task-calendar-button");
    if (przyciskSynchronizacjiKalendarza) {
      przyciskSynchronizacjiKalendarza.addEventListener("click", async () => {
        try {
          await synchronizujKalendarzZadaniaTeraz();
        } catch (error) {
          pokazPowiadomienie(error.message);
        }
      });
    }
    const przyciskSprawdzeniaKalendarza = document.getElementById("check-task-calendar-button");
    if (przyciskSprawdzeniaKalendarza) {
      przyciskSprawdzeniaKalendarza.addEventListener("click", async () => {
        try {
          await sprawdzStanKalendarzaGoogleTeraz();
        } catch (error) {
          pokazPowiadomienie(error.message);
        }
      });
    }
    const selectKalendarza = document.getElementById("task-calendar-id");
    if (selectKalendarza) {
      selectKalendarza.addEventListener("change", () => {
        uzupelnijCzasZadanZKalendarza();
        renderujPodsumowanieSkutkuZapisuZadania(task);
      });
    }
    const poleCyklicznosci = document.getElementById("task-recurrence-pattern");
    if (poleCyklicznosci) {
      poleCyklicznosci.addEventListener("change", () => {
        odswiezWidocznoscPolCyklicznosciZadania();
      });
    }
    document.querySelectorAll('input[name="task-visibility-scope"]').forEach((element) => {
      element.addEventListener("change", odswiezWidocznoscFormularzaZadania);
    });
    [
      "task-title",
      "task-type",
      "task-status",
      "task-priority",
      "task-assigned-user",
      "task-due-at",
      "task-remind-at",
      "task-calendar-duration",
      "task-recurrence-interval",
      "task-recurrence-end-at",
      "task-recurrence-apply-scope",
      "task-description",
    ].forEach((fieldId) => {
      const field = document.getElementById(fieldId);
      if (field) {
        field.addEventListener("input", () => renderujPodsumowanieSkutkuZapisuZadania(task));
        field.addEventListener("change", () => renderujPodsumowanieSkutkuZapisuZadania(task));
      }
    });
    document.querySelectorAll('input[name="task-visible-user"]').forEach((element) => {
      element.addEventListener("change", () => renderujPodsumowanieSkutkuZapisuZadania(task));
    });
  const formularzNotatki = document.getElementById("task-note-form");
  if (formularzNotatki) {
    formularzNotatki.addEventListener("submit", async (event) => {
      event.preventDefault();
      try {
        await dodajNotatkeDoZadania();
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
    });
  }
  const przyciskWyczyscOdpowiedz = document.getElementById("task-note-clear-reply");
  if (przyciskWyczyscOdpowiedz) {
    przyciskWyczyscOdpowiedz.addEventListener("click", () => ustawCelOdpowiedziNotatki(null));
  }
  document.querySelectorAll("[data-task-note-reply-to]").forEach((button) => {
    button.addEventListener("click", () => {
      ustawCelOdpowiedziNotatki(Number(button.dataset.taskNoteReplyTo || 0));
    });
  });
  document.querySelectorAll("[data-task-checklist-toggle]").forEach((checkbox) => {
    checkbox.addEventListener("change", async () => {
      try {
        await przelaczElementChecklisty(Number(checkbox.dataset.taskChecklistToggle || 0));
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
    });
  });
  const formularzChecklisty = document.getElementById("task-checklist-form");
  if (formularzChecklisty) {
    formularzChecklisty.addEventListener("submit", async (event) => {
      event.preventDefault();
      try {
        await dodajElementChecklistyDoZadania();
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
    });
  }
  const formularzAkceptacji = document.getElementById("approval-create-form");
  if (formularzAkceptacji) {
    formularzAkceptacji.addEventListener("submit", async (event) => {
      event.preventDefault();
      try {
        const shell = formularzAkceptacji.closest("[data-approval-entity-type]");
        const entityType = shell?.dataset.approvalEntityType || "task";
        const entityId = Number(shell?.dataset.approvalEntityId || task?.task_id || 0);
        await utworzWniosekAkceptacjiDlaEncji(entityType, entityId);
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
    });
  }
  const formularzKomentarza = document.getElementById("invoice-comment-form");
  if (formularzKomentarza) {
    formularzKomentarza.addEventListener("submit", async (event) => {
      event.preventDefault();
      try {
        await dodajKomentarzDoFaktury();
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
    });
  }
  document.querySelectorAll("[data-approval-action]").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        const shell = button.closest("[data-approval-entity-type]");
        const entityType = shell?.dataset.approvalEntityType || "task";
        const entityId = Number(shell?.dataset.approvalEntityId || task?.task_id || 0);
        await zdecydujWniosekAkceptacji(
          Number(button.dataset.approvalId || 0),
          String(button.dataset.approvalAction || ""),
          entityType,
          entityId
        );
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
    });
  });
  const przyciskDodaniaZalacznika = document.getElementById("task-attachment-upload-button");
  if (przyciskDodaniaZalacznika) {
    przyciskDodaniaZalacznika.addEventListener("click", async () => {
      try {
        await dodajZalacznikDoZadania();
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
    });
  }
  const przyciskDodaniaLinkuZalacznika = document.getElementById("task-attachment-link-upload-button");
  if (przyciskDodaniaLinkuZalacznika) {
    przyciskDodaniaLinkuZalacznika.addEventListener("click", async () => {
      try {
        await dodajLinkZalacznikaDoZadania();
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
    });
  }
  odswiezWidocznoscFormularzaZadania();
  odswiezWidocznoscPolCyklicznosciZadania();
  renderujPodsumowanieSkutkuZapisuZadania(task);
}

function przygotujNoweZadanie() {
  if (!czyMoznaKorzystacZMojejPracy()) {
    pokazPowiadomienie("Sekcja Moja praca jest dostepna dopiero po wlaczeniu modulu Asystent Szefa.");
    return;
  }
  if (czyGlobalnyAdministrator() && !stan.wybranaOrganizacjaId) {
    pokazPowiadomienie("Wybierz organizacje przed dodaniem zadania.");
    return;
  }
  renderujPanelZadania(null);
}

function wypelnijFormularzZadaniaZPayload(payload) {
  document.getElementById("task-title").value = payload.title || "";
  document.getElementById("task-type").value = payload.task_type || "zadanie";
  document.getElementById("task-status").value = payload.status || "nowe";
  document.getElementById("task-priority").value = payload.priority || "normalny";
  document.getElementById("task-calendar-id").value = payload.calendar_id || "";
  document.getElementById("task-due-at").value = payload.due_at || "";
  document.getElementById("task-remind-at").value = payload.remind_at || "";
  document.getElementById("task-calendar-duration").value = payload.calendar_duration_minutes || 60;
  document.getElementById("task-recurrence-pattern").value = payload.recurrence_pattern || "brak";
  document.getElementById("task-recurrence-interval").value = payload.recurrence_interval || 1;
  document.getElementById("task-recurrence-end-at").value = payload.recurrence_end_at || "";
  document.getElementById("task-recurrence-weekdays").value = payload.recurrence_weekdays || "";
  const scopeField = document.getElementById("task-recurrence-apply-scope");
  if (scopeField) {
    scopeField.value = "tylko_ten";
  }
  document.getElementById("task-description").value = payload.description || "";
  if (czyMoznaPrzypisywacZadania()) {
    document.getElementById("task-assigned-user").value = payload.assigned_user_id || "";
    ustawZakresWidocznosciZadania(payload.visibility_scope || "prywatne");
    document.querySelectorAll('input[name="task-visible-user"]').forEach((checkbox) => {
      checkbox.checked = Array.isArray(payload.visible_user_ids) && payload.visible_user_ids.includes(Number(checkbox.value));
    });
  }
  ustawPowiazaniaEdytowanegoZadania(payload.linked_entities || [], {
    silent: true,
    editable: czyMoznaZapisywac(),
  });
  uzupelnijCzasZadanZKalendarza();
  odswiezWidocznoscFormularzaZadania();
  odswiezWidocznoscPolCyklicznosciZadania();
  renderujPodsumowanieSkutkuZapisuZadania();
}

function wyczyscSzczegolyZadania() {
  stan.wybraneZadanieId = null;
  stan.wybraneZadanieDetail = null;
  stan.powiazaniaEdytowanegoZadania = [];
  document.getElementById("task-detail").classList.add("hidden");
  document.getElementById("task-detail").innerHTML = "";
  document.getElementById("task-detail-empty").classList.remove("hidden");
}

function otworzMojaPrace(taskType = "") {
  if (!czyMoznaKorzystacZMojejPracy()) {
    pokazPowiadomienie("Sekcja Moja praca jest dostepna dopiero po wlaczeniu modulu Asystent Szefa.");
    return;
  }
  ustawWidok("tasks");
  if (!taskType) {
    return;
  }
  przygotujNoweZadanie();
  const poleTypu = document.getElementById("task-type");
  if (poleTypu) {
    poleTypu.value = taskType;
    odswiezWidocznoscFormularzaZadania();
  }
}

function wyczyscObszarMojejPracy(reason = "Sekcja pracy osobistej jest teraz niedostepna.") {
  zatrzymajDyktowanieNaturalnegoPolecenia(true);
  stan.uzytkownicyDoZadan = [];
  stan.zadania = [];
  stan.kalendarzeUzytkownika = [];
  stan.zewnetrzneKalendarzeGoogle = [];
  stan.statusPolaczeniaGoogleKalendarza = null;
  stan.ustawieniaPrzypomnienUzytkownika = null;
  stan.plannerZadan = null;
  stan.fokusZadan = null;
  stan.podgladNaturalnegoPolecenia = null;
  zbudujOpcjeUzytkownikowDoZadan();
  renderujStatusPolaczeniaGoogleKalendarza(null);
  renderujZewnetrzneKalendarzeGoogle([]);
  renderujKalendarzeUzytkownika([]);
  renderujUstawieniaPrzypomnienUzytkownika(null);
  renderujPlannerZadan(null);
  renderujFokusZadan(null);
  renderujPodgladNaturalnegoPolecenia(null);
  renderujHubNotatekZadan([]);
  renderujZadania([]);
  wyczyscSzczegolyZadania();
  const tabela = document.getElementById("task-table-body");
  if (tabela) {
    tabela.innerHTML = `<tr><td colspan="13">${bezpiecznyTekst(reason)}</td></tr>`;
  }
  ["zalegle", "dzis", "jutro", "tydzien"].forEach((bucketKey) => {
    const container = document.getElementById(`task-planner-${bucketKey}`);
    if (container) {
      container.innerHTML = `<div class="empty-state">${bezpiecznyTekst(reason)}</div>`;
    }
  });
  const generatedAt = document.getElementById("task-planner-generated-at");
  if (generatedAt) {
    generatedAt.textContent = "Modul nieaktywny";
  }
  renderujPanelMojejPracy();
}

function renderujPanelMojejPracy() {
  const container = document.getElementById("my-work-panel");
  const count = document.getElementById("my-work-count");
  if (!container || !count) {
    return;
  }

  if (!stan.biezacyUzytkownik) {
    count.textContent = "";
    container.className = "empty-state";
    container.textContent = "Zaloguj sie i wybierz organizacje, aby sprawdzic dostep do sekcji pracy osobistej.";
    return;
  }

  if (czyGlobalnyAdministrator() && !stan.wybranaOrganizacjaId) {
    count.textContent = "";
    container.className = "empty-state";
    container.textContent = "Wybierz konkretna organizacje, aby sprawdzic status modulu i wejsc do obszaru pracy.";
    return;
  }

  const organizacja = pobierzAktywnaOrganizacjeDlaModulow();
  if (!organizacja || !czyModulAsystentaSzefaAktywny()) {
    count.textContent = "Pakiet off";
    container.className = "empty-state";
    container.textContent =
      "Ta organizacja nie ma jeszcze wlaczonego modulu Asystent Szefa, wiec sekcja Moja praca pozostaje ukryta.";
    return;
  }

  if (!czyMoznaKorzystacZMojejPracy() && !czyMoznaOtworzycAsystentaSzefa()) {
    count.textContent = "Brak dostepu";
    container.className = "empty-state";
    container.textContent =
      "Pakiet jest aktywny dla organizacji, ale to konto nie ma dostepu do obszaru Moja praca.";
    return;
  }

  const zadania = Array.isArray(stan.zadania) ? stan.zadania : [];
  const aktywne = zadania.filter((item) => !["zakonczone", "anulowane"].includes(item.status)).length;
  const zPrzypomnieniem = zadania.filter((item) => item.remind_at).length;
  const kalendarze = Array.isArray(stan.kalendarzeUzytkownika) ? stan.kalendarzeUzytkownika.length : 0;
  const mojDzien = Number(
    (stan.fokusZadan?.views || []).find((item) => item.code === "moj_dzien")?.count || 0
  );
  const tytulDostepu = czyMenedzerskiWidokAsystenta()
    ? "Pelny Asystent Szefa jest aktywny dla tej organizacji."
    : "Sekcja Moja praca jest aktywna dla tego konta.";
  const opisDostepu = czyMenedzerskiWidokAsystenta()
    ? "Masz widok menedzerski z delegowaniem zadan i planowaniem pracy zespolu."
    : "Masz dostep do swoich zadan, wydarzen, notatek, kalendarzy sluzbowych i przypomnien.";

  count.textContent = `${aktywne} aktywnych`;
  container.className = "my-work-panel";
  container.innerHTML = `
    <div>
      <strong>${bezpiecznyTekst(tytulDostepu)}</strong>
      <p class="subtle-note">${bezpiecznyTekst(opisDostepu)}</p>
    </div>
    <div class="my-work-summary">
      <div class="summary-item">
        <strong>Aktywne wpisy</strong>
        <div>${bezpiecznyTekst(aktywne)}</div>
      </div>
      <div class="summary-item">
        <strong>Z przypomnieniem</strong>
        <div>${bezpiecznyTekst(zPrzypomnieniem)}</div>
      </div>
      <div class="summary-item">
        <strong>Moj dzien</strong>
        <div>${bezpiecznyTekst(mojDzien)}</div>
      </div>
      <div class="summary-item">
        <strong>Moje kalendarze</strong>
        <div>${bezpiecznyTekst(kalendarze)}</div>
      </div>
    </div>
    <div class="my-work-actions">
      <button type="button" data-my-work-open>Otworz moja prace</button>
      <button type="button" class="secondary" data-my-work-create="zadanie">Nowe zadanie</button>
      <button type="button" class="secondary" data-my-work-create="wydarzenie">Nowe wydarzenie</button>
      <button type="button" class="secondary" data-my-work-create="notatka">Nowa notatka</button>
    </div>
  `;

  container.querySelector("[data-my-work-open]")?.addEventListener("click", () => ustawWidok("tasks"));
  container.querySelectorAll("[data-my-work-create]").forEach((button) => {
    button.addEventListener("click", () => otworzMojaPrace(button.dataset.myWorkCreate || ""));
  });
}

function odczytajPlikJakoBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result || "");
      const marker = "base64,";
      const index = result.indexOf(marker);
      if (index === -1) {
        reject(new Error("Nie udalo sie przygotowac pliku do wysylki."));
        return;
      }
      resolve(result.slice(index + marker.length));
    };
    reader.onerror = () => reject(new Error("Nie udalo sie odczytac pliku."));
    reader.readAsDataURL(file);
  });
}

function renderujPulpit(snapshot) {
  const cards = snapshot.cards || {};
  const karty = [
    ["nowe_faktury", cards.nowe_faktury || 0],
    ["do_weryfikacji", cards.do_weryfikacji || 0],
    ["podejrzenia_duplikatow", cards.podejrzenia_duplikatow || 0],
    ["pewne_duplikaty", cards.pewne_duplikaty || 0],
    ["nowi_kontrahenci", cards.nowi_kontrahenci || 0],
    ["aktywne_przypomnienia", cards.aktywne_przypomnienia || 0],
  ];
  const alerty = Array.isArray(snapshot.operational_alerts) ? snapshot.operational_alerts : [];
  const przypomnienia = Array.isArray(snapshot.active_reminders) ? snapshot.active_reminders : [];
  const zdarzenia = Array.isArray(snapshot.recent_events) ? snapshot.recent_events : [];
  const priorytetAlertu = { danger: 0, warning: 1, info: 2, success: 3 };
  const posortowaneAlerty = [...alerty].sort((a, b) => {
    const severityA = String(a.severity || "info").trim().toLowerCase();
    const severityB = String(b.severity || "info").trim().toLowerCase();
    return (priorytetAlertu[severityA] ?? 9) - (priorytetAlertu[severityB] ?? 9);
  });

  const fokus = [];
  if ((cards.do_weryfikacji || 0) > 0) {
    fokus.push(`${cards.do_weryfikacji} dokumentow czeka na weryfikacje`);
  }
  if ((cards.podejrzenia_duplikatow || 0) > 0) {
    fokus.push(`${cards.podejrzenia_duplikatow} dokumentow ma podejrzenie duplikatu`);
  }
  if (przypomnienia.length > 0) {
    fokus.push(`${przypomnienia.length} przypomnien wraca dzisiaj do zespolu`);
  }
  if ((cards.nowi_kontrahenci || 0) > 0) {
    fokus.push(`${cards.nowi_kontrahenci} nowych kontrahentow wymaga sprawdzenia`);
  }
  document.getElementById("dashboard-focus-title").textContent = fokus.length
    ? "Dzisiaj potrzebuje uwagi"
    : "Rytm pracy jest spokojny";
  document.getElementById("dashboard-focus-summary").textContent = fokus.length
    ? `${fokus.join(". ")}.`
    : "Na ten moment nie ma nagromadzonych sygnalow krytycznych. Mozesz pracowac z glownego obszaru i wracac tu tylko kontrolnie.";

  const pasekKpi = [
    ["Nowe", cards.nowe_faktury || 0],
    ["Weryfikacja", cards.do_weryfikacji || 0],
    ["Duplikaty", (cards.podejrzenia_duplikatow || 0) + (cards.pewne_duplikaty || 0)],
    ["Przypomnienia", cards.aktywne_przypomnienia || 0],
  ];
  document.getElementById("dashboard-kpi-strip").innerHTML = pasekKpi
    .map(
      ([etykieta, wartosc]) => `
        <article class="dashboard-kpi-chip">
          <span class="dashboard-kpi-label">${bezpiecznyTekst(etykieta)}</span>
          <strong class="dashboard-kpi-value">${bezpiecznyTekst(wartosc)}</strong>
        </article>
      `
    )
    .join("");

  document.getElementById("dashboard-cards").innerHTML = karty
    .map(
      ([klucz, wartosc]) => `
        <button class="dashboard-action-button" type="button" data-shortcut="${klucz}">
          <span class="dashboard-action-label">${bezpiecznyTekst(skrotyPulpitu[klucz].etykieta)}</span>
          <strong class="dashboard-action-value">${bezpiecznyTekst(wartosc)}</strong>
          <span class="dashboard-action-meta">Otworz odpowiedni kontekst pracy</span>
        </button>
      `
    )
    .join("");

  document.querySelectorAll("[data-shortcut]").forEach((przycisk) => {
    przycisk.addEventListener("click", async () => {
      try {
        await skrotyPulpitu[przycisk.dataset.shortcut].zastosuj();
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
    });
  });

  const klasyAlertow = {
    danger: "status-danger",
    warning: "status-warning",
    info: "",
    success: "status-success",
  };
  const etykietyAlertow = {
    danger: "Wysoki priorytet",
    warning: "Uwaga",
    info: "Informacja",
    success: "OK",
  };
  const zbudujPrzyciskAlertu = (alert) =>
    alert.action_view && alert.action_label
      ? `
        <button
          type="button"
          class="secondary"
          data-operational-action-view="${bezpiecznyTekst(alert.action_view)}"
          data-operational-organization-id="${bezpiecznyTekst(alert.organization_id || "")}"
          data-operational-action-bucket="${bezpiecznyTekst(alert.action_bucket || "")}"
        >
          ${bezpiecznyTekst(alert.action_label)}
        </button>
      `
      : "";
  const podlaczAkcjeAlertow = (container) => {
    container.querySelectorAll("[data-operational-action-view]").forEach((button) => {
      button.addEventListener("click", async () => {
        const view = String(button.dataset.operationalActionView || "").trim();
        const organizationId = String(button.dataset.operationalOrganizationId || "").trim();
        const bucket = String(button.dataset.operationalActionBucket || "").trim();
        if (!view) {
          return;
        }

        if (czyGlobalnyAdministrator() && organizationId) {
          stan.wybranaOrganizacjaId = organizationId;
          stan.czyZakresOrganizacjiZainicjalizowany = true;
          const switcher = document.getElementById("organization-switcher");
          if (switcher) {
            switcher.value = organizationId;
          }
          odswiezPasekSesji();
        }

        ustawWidok(view);
        try {
          if (view === "invoices") {
            await Promise.all([wczytajFaktury(), wczytajKontrahentow()]);
            if (["verification", "duplicates", "ksef_corrections", "ocr_attention"].includes(bucket)) {
              ustawAktywnyKoszykWeryfikacjiFaktur(bucket);
              document.getElementById("invoice-verification-workspace-shell")?.scrollIntoView({
                behavior: "smooth",
                block: "start",
              });
            } else if (bucket === "exceptions") {
              document.getElementById("invoice-exception-center-shell")?.scrollIntoView({
                behavior: "smooth",
                block: "start",
              });
            } else if (bucket === "handoff_ready") {
              document.getElementById("invoice-handoff-batches-shell")?.scrollIntoView({
                behavior: "smooth",
                block: "start",
              });
            }
          } else if (view === "knowledge" && typeof wczytajBazeWiedzy === "function") {
            if (typeof ustawFokusKolejkiDokumentowFirmowych === "function" && bucket) {
              ustawFokusKolejkiDokumentowFirmowych(bucket);
            }
            await wczytajBazeWiedzy();
          } else if (view === "tasks") {
            await wczytajZadania();
          } else if (view === "email-center") {
            await wczytajCentrumEmaila();
          }
        } catch (error) {
          pokazPowiadomienie(error.message);
        }
      });
    });
  };

  const kontenerPriorytetow = document.getElementById("dashboard-priority-alerts");
  if (!posortowaneAlerty.length) {
    kontenerPriorytetow.innerHTML = `<div class="empty-state">Brak alertow o wysokim priorytecie.</div>`;
  } else {
    kontenerPriorytetow.innerHTML = `
      <div class="dashboard-priority-list">
        ${posortowaneAlerty
          .slice(0, 3)
          .map((alert) => {
            const severity = String(alert.severity || "info").trim().toLowerCase();
            const badgeLabel = etykietyAlertow[severity] || "Informacja";
            const badgeClass = klasyAlertow[severity] || "";
            return `
              <article class="dashboard-priority-card">
                <div class="dashboard-priority-top">
                  <strong>${bezpiecznyTekst(alert.title || "Alert operacyjny")}</strong>
                  ${zbudujBadgeStanu(badgeLabel, badgeClass)}
                </div>
                <p>${bezpiecznyTekst(alert.description || "-")}</p>
                <div class="muted">${bezpiecznyTekst(alert.category || "system")}</div>
                ${zbudujPrzyciskAlertu(alert)}
              </article>
            `;
          })
          .join("")}
      </div>
    `;
    podlaczAkcjeAlertow(kontenerPriorytetow);
  }

  const kontenerAlertow = document.getElementById("dashboard-operational-alerts");
  if (!alerty.length) {
    kontenerAlertow.innerHTML = `<div class="empty-state">Brak alertow operacyjnych.</div>`;
  } else {
    kontenerAlertow.innerHTML = `
      <div class="dashboard-stream-list">
        ${alerty
          .map((alert) => {
            const severity = String(alert.severity || "info").trim().toLowerCase();
            const badgeLabel = etykietyAlertow[severity] || "Informacja";
            const badgeClass = klasyAlertow[severity] || "";
            return `
              <article class="dashboard-stream-item">
                <div class="dashboard-stream-top">
                  <div>
                    <strong>${bezpiecznyTekst(alert.title || "Alert operacyjny")}</strong>
                    <div class="muted">${bezpiecznyTekst(alert.category || "system")}</div>
                  </div>
                  ${zbudujBadgeStanu(badgeLabel, badgeClass)}
                </div>
                <p>${bezpiecznyTekst(alert.description || "-")}</p>
                ${
                  alert.organization_name
                    ? `<div class="muted">Organizacja: ${bezpiecznyTekst(alert.organization_name)}</div>`
                    : ""
                }
                <div class="dashboard-stream-actions">${zbudujPrzyciskAlertu(alert)}</div>
              </article>
            `;
          })
          .join("")}
      </div>
    `;
    podlaczAkcjeAlertow(kontenerAlertow);
  }

  const kontenerPrzypomnien = document.getElementById("dashboard-reminders");
  if (!przypomnienia.length) {
    kontenerPrzypomnien.innerHTML = `<div class="empty-state">Brak aktywnych przypomnien.</div>`;
  } else {
    kontenerPrzypomnien.innerHTML = `
      <div class="dashboard-reminder-list">
        ${przypomnienia
          .slice(0, 5)
          .map((task) => {
            const stanPrzypomnienia = pobierzStanPrzypomnienia(task);
            return `
              <article class="dashboard-reminder-card">
                <strong>${formatujWartosc(task.title)}</strong>
                <div class="muted">${formatujTypZadania(task.task_type)} â€˘ ${formatujNazweOrganizacji(task.organization_name)}</div>
                <div>${formatujDateCzas(task.remind_at)}</div>
                <div><span class="status-badge ${stanPrzypomnienia.klasa}">${stanPrzypomnienia.etykieta}</span></div>
              </article>
            `;
          })
          .join("")}
      </div>
    `;
  }

  const kontenerKolejkiWiedzy = document.getElementById("dashboard-knowledge-queue");
  const kolejkaWiedzy = Array.isArray(snapshot.knowledge_queue) ? snapshot.knowledge_queue : [];
  if (kontenerKolejkiWiedzy) {
    if (!kolejkaWiedzy.length) {
      kontenerKolejkiWiedzy.innerHTML = `<div class="empty-state">Brak dokumentow wymagajacych szybkiej decyzji.</div>`;
    } else {
      kontenerKolejkiWiedzy.innerHTML = `
        <div class="dashboard-stream-list dashboard-knowledge-queue-list">
          ${kolejkaWiedzy
            .slice(0, 6)
            .map((document) => `
              <article class="dashboard-stream-item dashboard-knowledge-queue-item">
                <div class="dashboard-stream-top">
                  <div>
                    <strong>${bezpiecznyTekst(document.title || "(bez tytulu)")}</strong>
                    <div class="muted">${bezpiecznyTekst(document.library_path_label || "Bez folderu")}</div>
                  </div>
                  <span class="status-badge ${typeof klasaStanuObieguDokumentuBazyWiedzy === "function" ? klasaStanuObieguDokumentuBazyWiedzy(document.business_status || "roboczy") : ""}">${bezpiecznyTekst(document.business_status_label || document.business_status || "roboczy")}</span>
                </div>
                <div class="muted">
                  ${bezpiecznyTekst(document.workflow_status_label || document.workflow_status || "wymaga decyzji")}
                  ${document.official_version_number ? ` | obow. v${bezpiecznyTekst(document.official_version_number)}` : ""}
                  ${document.current_version_number ? ` | najn. v${bezpiecznyTekst(document.current_version_number)}` : ""}
                </div>
                <div class="muted">
                  ${bezpiecznyTekst(document.owner_user_label || document.reviewer_user_label || document.approver_user_label || "brak osoby odpowiedzialnej")}
                </div>
                <div class="dashboard-stream-actions">
                  ${
                    typeof zbudujAkcjeOperacyjneDokumentuBazyWiedzy === "function"
                      ? zbudujAkcjeOperacyjneDokumentuBazyWiedzy(document, {
                          limit: 3,
                          compact: true,
                          includeOpen: true,
                          includeTask: true,
                        })
                      : `<button type="button" class="secondary" data-knowledge-open-document="${bezpiecznyTekst(document.knowledge_document_id || "")}">Otworz</button>`
                  }
                </div>
              </article>
            `)
            .join("")}
        </div>
      `;
    }
  }

  const kontenerZdarzen = document.getElementById("dashboard-events");
  if (!zdarzenia.length) {
    kontenerZdarzen.innerHTML = `<div class="empty-state">Brak zdarzen do wyswietlenia.</div>`;
    return;
  }

  kontenerZdarzen.innerHTML = `
    <div class="dashboard-stream-list">
      ${zdarzenia
        .map((event) => {
          const opisKontekstu = zbudujOpisKontekstuZdarzenia(event);
          return `
            <article class="dashboard-stream-item">
              <div class="dashboard-stream-top">
                <strong>${formatujTypZdarzenia(event.event_type)}</strong>
                <span class="muted">${formatujDateCzas(event.event_time)}</span>
              </div>
              <div class="muted">Organizacja: ${formatujNazweOrganizacji(event.organization_name)}</div>
              ${opisKontekstu ? `<p>${opisKontekstu}</p>` : ""}
              <p>${formatujWartosc(event.decision_reason)}</p>
            </article>
          `;
        })
        .join("")}
    </div>
  `;
}

function renderujFaktury(faktury) {
  stan.faktury = faktury;
  zsynchronizujZaznaczoneFaktury(faktury);
  document.getElementById("invoice-count").textContent = `${faktury.length} rekordĂłw`;
  odswiezPasekFiltrowFaktur();
  if (!faktury.some((invoice) => Number(invoice.id) === Number(stan.wybranaFakturaId))) {
    wyczyscSzczegolyFaktury();
  }

  const body = document.getElementById("invoice-table-body");
  if (!faktury.length) {
    body.innerHTML = `<tr><td colspan="16">Brak faktur dla wybranych filtrow.</td></tr>`;
    const selectAll = document.getElementById("invoice-select-all");
    if (selectAll instanceof HTMLInputElement) {
      selectAll.checked = false;
      selectAll.indeterminate = false;
      selectAll.onchange = null;
    }
    renderujPodsumowanieZaznaczeniaPaczkiFaktur();
    return;
  }

  body.innerHTML = faktury
    .map(
      (invoice) => `
        <tr class="clickable" data-invoice-id="${invoice.id}">
          <td><input type="checkbox" data-invoice-select-id="${invoice.id}" ${czyFakturaJestZaznaczona(invoice.id) ? "checked" : ""} /></td>
          <td>${invoice.id}</td>
          <td>${formatujNazweOrganizacji(invoice.organization_name)}</td>
          <td>${formatujWartosc(invoice.incoming_date)}</td>
          <td>${formatujZrodlo(invoice.source)}</td>
          <td>
            <div>${formatujWartosc(invoice.file_name)}</div>
            <button type="button" class="secondary invoice-preview-inline" data-invoice-preview-id="${invoice.id}">Podglad</button>
          </td>
          <td>${formatujWartosc(invoice.invoice_number)}</td>
          <td>${formatujWartosc(invoice.ksef_number)}</td>
          <td>${formatujWartosc(invoice.issuer_nip)}</td>
          <td>${formatujWartosc(invoice.issuer_name)}</td>
          <td>${formatujKwote(invoice.gross_amount, invoice.currency)}</td>
          <td><span class="status-badge ${klasaStatusu(invoice.status, invoice.duplicate_type)}">${formatujWartosc(invoice.status)}</span></td>
          <td><span class="status-badge ${klasaStatusuObieguFaktury(invoice.workflow_state)}">${formatujObiegFaktury(invoice.workflow_state)}</span></td>
          <td><span class="status-badge ${klasaStatusu(invoice.status, invoice.duplicate_type)}">${formatujWartosc(invoice.duplicate_type)}</span></td>
          <td>${formatujWartosc(invoice.assigned_user_name)}</td>
          <td>${formatujWartosc(invoice.contractor_name)}</td>
        </tr>
      `
    )
    .join("");

  body.querySelectorAll("[data-invoice-id]").forEach((row) => {
    row.addEventListener("click", (event) => {
      if (event.target instanceof HTMLInputElement && event.target.type === "checkbox") {
        return;
      }
      wczytajSzczegolyFaktury(Number(row.dataset.invoiceId));
    });
  });
  body.querySelectorAll("[data-invoice-select-id]").forEach((checkbox) => {
    checkbox.addEventListener("click", (event) => {
      event.stopPropagation();
    });
    checkbox.addEventListener("change", () => {
      ustawZaznaczenieFaktury(Number(checkbox.dataset.invoiceSelectId || 0), checkbox.checked);
    });
  });
  body.querySelectorAll("[data-invoice-preview-id]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      try {
        await wczytajPodgladFaktury(Number(button.dataset.invoicePreviewId || 0));
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
    });
  });
  const selectAll = document.getElementById("invoice-select-all");
  if (selectAll instanceof HTMLInputElement) {
    const selectedCount = stan.zaznaczoneFaktury.length;
    selectAll.checked = faktury.length > 0 && selectedCount === faktury.length;
    selectAll.indeterminate = selectedCount > 0 && selectedCount < faktury.length;
    selectAll.onchange = () => {
      ustawZaznaczenieWszystkichFaktur(selectAll.checked);
    };
  }
  renderujPodsumowanieZaznaczeniaPaczkiFaktur();
}

function renderujRelacje(relations) {
  if (!relations.length) {
    return `<div class="empty-state">Brak aktywnych relacji duplikatĂłw.</div>`;
  }

  return `
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>PowiÄ…zana faktura</th>
            <th>Typ relacji</th>
            <th>PowĂłd</th>
          </tr>
        </thead>
        <tbody>
          ${relations
            .map(
              (relation) => `
                <tr>
                  <td>#${relation.related_invoice_id}</td>
                  <td>${formatujWartosc(relation.relation_type)}</td>
                  <td>${formatujWartosc(relation.reason)}</td>
                </tr>
              `
            )
            .join("")}
        </tbody>
      </table>
    </div>
  `;
}

function renderujPodobneFaktury(items) {
  if (!items.length) {
    return `<div class="empty-state">Brak podobnych faktur wedĹ‚ug aktualnych reguĹ‚.</div>`;
  }

  return `
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Numer faktury</th>
            <th>Numer KSeF</th>
            <th>NIP wystawcy</th>
            <th>Data</th>
            <th>Kwota</th>
            <th>Status</th>
            <th>PowĂłd</th>
          </tr>
        </thead>
        <tbody>
          ${items
            .map(
              (item) => `
                <tr>
                  <td>${item.id}</td>
                  <td>${formatujWartosc(item.invoice_number)}</td>
                  <td>${formatujWartosc(item.ksef_number)}</td>
                  <td>${formatujWartosc(item.issuer_nip)}</td>
                  <td>${formatujWartosc(item.issue_date)}</td>
                  <td>${formatujKwote(item.gross_amount, item.currency)}</td>
                  <td>${formatujWartosc(item.status)}</td>
                  <td>${formatujWartosc(item.match_reason)}</td>
                </tr>
              `
            )
            .join("")}
        </tbody>
      </table>
    </div>
  `;
}

function renderujHistorie(items) {
  if (!items.length) {
    return `<div class="empty-state">Brak historii dziaĹ‚aĹ„ dla tej faktury.</div>`;
  }

  return `
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Data</th>
            <th>Zdarzenie</th>
            <th>Status przed</th>
            <th>Status po</th>
            <th>PowĂłd</th>
            <th>Aktor</th>
          </tr>
        </thead>
        <tbody>
          ${items
            .map(
              (item) => `
                <tr>
                  <td>${formatujDateCzas(item.event_time)}</td>
                  <td>${formatujTypZdarzenia(item.event_type)}</td>
                  <td>${formatujWartosc(item.status_before)}</td>
                  <td>${formatujWartosc(item.status_after)}</td>
                  <td>${formatujWartosc(item.decision_reason)}</td>
                  <td>${formatujWartosc(item.actor)}</td>
                </tr>
              `
            )
            .join("")}
        </tbody>
      </table>
    </div>
  `;
}

function renderujMetadaneZrodla(metadata) {
  const wpisy = Object.entries(metadata || {});
  if (!wpisy.length) {
    return `<div class="empty-state">Brak dodatkowych metadanych ĹşrĂłdĹ‚a.</div>`;
  }

  return `
    <div class="list">
      ${wpisy
        .map(
          ([key, value]) => `
            <div class="list-item">
              <strong>${formatujWartosc(key)}</strong>
              <div>${formatujWartosc(typeof value === "object" ? JSON.stringify(value) : value)}</div>
            </div>
          `
        )
        .join("")}
      </div>
  `;
}

function renderujSkrzynkeWeryfikacjiFaktur(snapshot) {
  stan.skrzynkaWeryfikacjiFaktur = snapshot || null;
  const container = document.getElementById("invoice-verification-inbox");
  const count = document.getElementById("invoice-verification-inbox-count");
  if (!container || !count) {
    return;
  }

  if (!snapshot || !snapshot.sections) {
    count.textContent = "";
    container.className = "verification-inbox-grid";
    container.innerHTML = `<div class="empty-state">Nie udalo sie zaladowac skrzynki weryfikacji.</div>`;
    return;
  }

  const summary = snapshot.summary || {};
  count.textContent = `${Number(summary.total_open_count || 0)} otwartych spraw`;

  const sections = Object.values(snapshot.sections || {});
  if (!sections.length) {
    container.className = "verification-inbox-grid";
    container.innerHTML = `<div class="empty-state">Brak faktur wymagajacych uwagi.</div>`;
    return;
  }

  container.className = "verification-inbox-grid";
  container.innerHTML = sections
    .map((section) => {
      const bucketKey =
        section.action_key === "status_verification"
          ? "verification"
          : section.action_key === "duplicate_review"
            ? "duplicates"
            : section.action_key === "ksef_pending"
              ? "ksef_corrections"
              : "ocr_attention";
      const items = Array.isArray(section.items) ? section.items : [];
      const listHtml = items.length
        ? `
          <div class="verification-card-list">
            ${items
              .map(
                (item) => `
                  <article class="verification-card-item">
                    <strong>${bezpiecznyTekst(item.invoice_number || item.ksef_number || `Faktura #${item.invoice_id}`)}</strong>
                    <div class="muted">${bezpiecznyTekst(item.issuer_name || "-")} | ${bezpiecznyTekst(item.issuer_nip || "-")}</div>
                    <div class="muted">${formatujDateCzas(item.incoming_date || item.issue_date)} | ${formatujKwote(item.gross_amount, item.currency)}</div>
                    ${item.assigned_user_name ? `<div class="muted">Odpowiedzialny: ${bezpiecznyTekst(item.assigned_user_name)}</div>` : ""}
                    <div class="invoice-field-provenance-meta">
                      ${zbudujBadgeStanu(formatujWartosc(item.status), klasaStatusu(item.status, item.duplicate_type))}
                      ${item.duplicate_type && item.duplicate_type !== "brak" ? zbudujBadgeStanu(formatujWartosc(item.duplicate_type), klasaStatusu(item.status, item.duplicate_type)) : ""}
                      ${item.pending_override_count ? zbudujBadgeStanu(`${item.pending_override_count} oczekuje`, "status-warning") : ""}
                      ${item.invoice_comment_count ? zbudujBadgeStanu(`${Number(item.invoice_comment_count)} komentarzy`, "status-success") : ""}
                    </div>
                    ${item.flag_reason ? `<div>${bezpiecznyTekst(item.flag_reason)}</div>` : ""}
                    <div class="filters-actions">
                      <button type="button" class="secondary" data-preview-verification-invoice-id="${item.invoice_id}">Szybki podglad</button>
                      <button type="button" class="secondary" data-open-verification-invoice-id="${item.invoice_id}">Otworz fakture</button>
                    </div>
                  </article>
                `
              )
              .join("")}
          </div>
        `
        : `<div class="empty-state">Brak pozycji w tej sekcji.</div>`;
      return `
        <section class="verification-card">
          <div class="verification-card-header">
            <div>
              <strong>${bezpiecznyTekst(section.title || "-")}</strong>
              <div class="subtle-note">${bezpiecznyTekst(section.description || "")}</div>
            </div>
            <div>${zbudujBadgeStanu(`${Number(section.count || 0)}`, Number(section.count || 0) ? "status-warning" : "status-success")}</div>
          </div>
          ${listHtml}
          <div class="filters-actions">
            <button type="button" class="secondary" data-open-verification-bucket="${bezpiecznyTekst(bucketKey)}">Otworz workspace</button>
          </div>
        </section>
      `;
    })
    .join("");

  container.querySelectorAll("[data-open-verification-invoice-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      const invoiceId = Number(button.dataset.openVerificationInvoiceId || 0);
      if (!invoiceId) return;
      await wczytajSzczegolyFaktury(invoiceId);
    });
  });
  container.querySelectorAll("[data-preview-verification-invoice-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      const invoiceId = Number(button.dataset.previewVerificationInvoiceId || 0);
      if (!invoiceId) return;
      try {
        await wczytajPodgladFaktury(invoiceId);
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
    });
  });
  container.querySelectorAll("[data-open-verification-bucket]").forEach((button) => {
    button.addEventListener("click", async () => {
      await otworzWorkspaceWeryfikacjiFaktur(String(button.dataset.openVerificationBucket || "").trim());
    });
  });
}

function ustawAktywnyKoszykWeryfikacjiFaktur(bucket) {
  const snapshot = stan.workspaceWeryfikacjiFaktur;
  const order = Array.isArray(snapshot?.bucket_order) && snapshot.bucket_order.length
    ? snapshot.bucket_order
    : ["verification", "duplicates", "ksef_corrections", "ocr_attention"];
  if (bucket === "") {
    stan.aktywnyKoszykWeryfikacjiFaktur = "";
  } else if (bucket && order.includes(bucket)) {
    stan.aktywnyKoszykWeryfikacjiFaktur = bucket;
  } else if (stan.aktywnyKoszykWeryfikacjiFaktur && !order.includes(stan.aktywnyKoszykWeryfikacjiFaktur)) {
    stan.aktywnyKoszykWeryfikacjiFaktur = String(snapshot?.summary?.active_bucket || order[0] || "verification");
  }
  renderujWorkspaceWeryfikacjiFaktur(snapshot);
}

async function otworzWorkspaceWeryfikacjiFaktur(bucket) {
  if (bucket) {
    stan.aktywnyKoszykWeryfikacjiFaktur = bucket;
  }
  ustawWidok("invoices");
  await Promise.all([wczytajFaktury(), wczytajKontrahentow()]);
  document.getElementById("invoice-verification-workspace-shell")?.scrollIntoView({
    behavior: "smooth",
    block: "start",
  });
}

function renderujWorkspaceWeryfikacjiFaktur(snapshot) {
  stan.workspaceWeryfikacjiFaktur = snapshot || null;
  const shell = document.getElementById("invoice-verification-workspace-shell");
  const count = document.getElementById("invoice-verification-workspace-count");
  const tabs = document.getElementById("invoice-verification-workspace-tabs");
  const summary = document.getElementById("invoice-verification-workspace-sla");
  const container = document.getElementById("invoice-verification-workspace");
  if (!shell || !count || !tabs || !summary || !container) {
    return;
  }

  if (!snapshot || !snapshot.sections) {
    count.textContent = "";
    tabs.innerHTML = "";
    summary.innerHTML = `<div class="empty-state">Nie udalo sie zaladowac workspace weryfikacji.</div>`;
    container.innerHTML = `<div class="empty-state">Workspace weryfikacji pojawi sie po zaladowaniu danych.</div>`;
    return;
  }

  const bucketOrder = Array.isArray(snapshot.bucket_order) && snapshot.bucket_order.length
    ? snapshot.bucket_order
    : ["verification", "duplicates", "ksef_corrections", "ocr_attention"];
  if (stan.aktywnyKoszykWeryfikacjiFaktur && !bucketOrder.includes(stan.aktywnyKoszykWeryfikacjiFaktur)) {
    stan.aktywnyKoszykWeryfikacjiFaktur = String(snapshot.summary?.active_bucket || bucketOrder[0] || "verification");
  }

  const activeBucket = stan.aktywnyKoszykWeryfikacjiFaktur;
  const hasActiveBucket = bucketOrder.includes(activeBucket);
  const activeSection = hasActiveBucket ? snapshot.sections[activeBucket] || null : null;
  const totalOpenCount = Number(snapshot.summary?.total_open_count || 0);
  const totalSlaBreached = Number(snapshot.summary?.total_sla_breached || 0);
  const oldestAgeDays = Number(snapshot.summary?.oldest_age_days || 0);

  count.textContent = `${totalOpenCount} spraw`;
  tabs.innerHTML = bucketOrder
    .map((bucket) => {
      const section = snapshot.sections[bucket];
      if (!section) {
        return "";
      }
      const buttonLabel = `${section.title} (${Number(section.count || 0)})`;
      const buttonClass = bucket === activeBucket ? "secondary active" : "secondary";
      return `
        <button
          type="button"
          class="${buttonClass}"
          data-verification-workspace-bucket="${bezpiecznyTekst(bucket)}"
          aria-pressed="${bucket === activeBucket ? "true" : "false"}"
        >
          ${bezpiecznyTekst(buttonLabel)}
        </button>
      `;
    })
    .join("");

  summary.innerHTML = `
    <article class="verification-sla-card">
      <span class="subtle-note">Lacznie otwartych spraw</span>
      <strong>${bezpiecznyTekst(totalOpenCount)}</strong>
    </article>
    <article class="verification-sla-card ${totalSlaBreached ? "is-danger" : ""}">
      <span class="subtle-note">Po SLA</span>
      <strong>${bezpiecznyTekst(totalSlaBreached)}</strong>
    </article>
    <article class="verification-sla-card">
      <span class="subtle-note">Najstarsza sprawa</span>
      <strong>${bezpiecznyTekst(`${oldestAgeDays} dni`)}</strong>
    </article>
    <article class="verification-sla-card">
      <span class="subtle-note">Aktywny koszyk</span>
      <strong>${bezpiecznyTekst(activeSection?.title || "Wszystkie koszyki")}</strong>
    </article>
  `;

  const sectionsToRender = hasActiveBucket
    ? [activeSection].filter(Boolean)
    : bucketOrder.map((bucket) => snapshot.sections[bucket]).filter(Boolean);
  if (!sectionsToRender.length) {
    container.innerHTML = `<div class="empty-state">Brak sekcji do wyswietlenia.</div>`;
  } else {
    container.innerHTML = sectionsToRender
      .map((section) => {
        const items = Array.isArray(section.items) ? section.items : [];
        return `
          <section class="verification-workspace-section">
            <div class="verification-workspace-header">
              <div>
                <strong>${bezpiecznyTekst(section.title || "-")}</strong>
                <div class="subtle-note">${bezpiecznyTekst(section.description || "")}</div>
              </div>
              <div class="invoice-field-provenance-meta">
                ${zbudujBadgeStanu(`${Number(section.count || 0)} spraw`, Number(section.count || 0) ? "status-warning" : "status-success")}
                ${zbudujBadgeStanu(`SLA ${Number(section.sla_days || 0)} dni`, "status-warning")}
                ${section.sla_breached_count ? zbudujBadgeStanu(`${Number(section.sla_breached_count)} po SLA`, "status-danger") : ""}
              </div>
            </div>
            ${
              items.length
                ? `
                  <div class="verification-workspace-list">
                    ${items
                      .map((item) => {
                        const ageLabel =
                          item.age_days === null || item.age_days === undefined ? "-" : `${Number(item.age_days)} dni`;
                        return `
                          <article class="verification-workspace-item ${item.sla_breached ? "is-danger" : ""}">
                            <div class="verification-card-header">
                              <div>
                                <strong>${bezpiecznyTekst(item.invoice_number || item.ksef_number || `Faktura #${item.invoice_id}`)}</strong>
                                <div class="muted">${bezpiecznyTekst(item.issuer_name || "-")} | ${bezpiecznyTekst(item.issuer_nip || "-")}</div>
                              </div>
                              <div class="invoice-field-provenance-meta">
                                ${zbudujBadgeStanu(formatujWartosc(item.status), klasaStatusu(item.status, item.duplicate_type))}
                                ${item.duplicate_type && item.duplicate_type !== "brak" ? zbudujBadgeStanu(formatujWartosc(item.duplicate_type), klasaStatusu(item.status, item.duplicate_type)) : ""}
                                ${item.sla_breached ? zbudujBadgeStanu("Po SLA", "status-danger") : zbudujBadgeStanu(`W kolejce ${bezpiecznyTekst(ageLabel)}`, "status-warning")}
                              </div>
                            </div>
                            <div class="verification-workspace-meta">
                              <span>${formatujNazweOrganizacji(item.organization_name)}</span>
                              <span>${formatujZrodlo(item.source)}</span>
                              <span>${formatujDateCzas(item.incoming_date || item.issue_date)}</span>
                              <span>${formatujKwote(item.gross_amount, item.currency)}</span>
                              ${item.assigned_user_name ? `<span>Odpowiedzialny: ${bezpiecznyTekst(item.assigned_user_name)}</span>` : ""}
                              ${item.invoice_comment_count ? `<span>Komentarze: ${bezpiecznyTekst(item.invoice_comment_count)}</span>` : ""}
                            </div>
                            <p class="verification-workspace-reason">${bezpiecznyTekst(item.attention_label || item.flag_reason || "-")}</p>
                            ${item.flag_reason ? `<div class="subtle-note">${bezpiecznyTekst(item.flag_reason)}</div>` : ""}
                            <div class="filters-actions">
                              <button type="button" class="secondary" data-open-workspace-invoice-id="${item.invoice_id}">Otworz fakture</button>
                              <button type="button" class="secondary" data-preview-workspace-invoice-id="${item.invoice_id}">Szybki podglad</button>
                              ${
                                item.compare_target_invoice_id
                                  ? `<button type="button" class="secondary" data-compare-workspace-left-id="${item.invoice_id}" data-compare-workspace-right-id="${item.compare_target_invoice_id}">Porownaj obok siebie</button>`
                                  : ""
                              }
                            </div>
                          </article>
                        `;
                      })
                      .join("")}
                  </div>
                `
                : `
                  <div class="empty-state">
                    ${bezpiecznyTekst(section.title || "Sekcja")} jest pusta. Nic nie czeka tutaj na decyzje.
                  </div>
                `
            }
          </section>
        `;
      })
      .join("");
  }

  tabs.querySelectorAll("[data-verification-workspace-bucket]").forEach((button) => {
    button.addEventListener("click", () => {
      const bucket = String(button.dataset.verificationWorkspaceBucket || "").trim();
      ustawAktywnyKoszykWeryfikacjiFaktur(bucket === stan.aktywnyKoszykWeryfikacjiFaktur ? "" : bucket);
    });
  });
  container.querySelectorAll("[data-open-workspace-invoice-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      const invoiceId = Number(button.dataset.openWorkspaceInvoiceId || 0);
      if (!invoiceId) {
        return;
      }
      await wczytajSzczegolyFaktury(invoiceId);
      document.getElementById("invoice-detail")?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
  container.querySelectorAll("[data-preview-workspace-invoice-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      const invoiceId = Number(button.dataset.previewWorkspaceInvoiceId || 0);
      if (!invoiceId) {
        return;
      }
      await wczytajPodgladFaktury(invoiceId);
    });
  });
  container.querySelectorAll("[data-compare-workspace-left-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      const leftId = Number(button.dataset.compareWorkspaceLeftId || 0);
      const rightId = Number(button.dataset.compareWorkspaceRightId || 0);
      if (!leftId || !rightId) {
        return;
      }
      await wczytajPorownanieFaktur(leftId, rightId);
    });
  });
}

function pobierzEtykieteStatusuIntakeFaktury(status) {
  const labels = {
    nowe: "Nowe",
    w_toku: "W toku",
    zakonczone: "Zakonczone",
    zarchiwizowane: "Zarchiwizowane",
  };
  return labels[String(status || "").trim().toLowerCase()] || formatujWartosc(status);
}

function pobierzKlaseStatusuIntakeFaktury(status) {
  const normalized = String(status || "").trim().toLowerCase();
  if (normalized === "zakonczone") return "status-success";
  if (normalized === "w_toku") return "status-warning";
  if (normalized === "zarchiwizowane") return "status-neutral";
  return "status-normal";
}

function pobierzEtykieteWyjatkuFaktury(code) {
  const labels = {
    missing_contractor: "Brak kontrahenta",
    weak_ocr: "OCR wymaga uwagi",
    duplicate_requires_decision: "Duplikat do decyzji",
    missing_ksef_confirmation: "Brak potwierdzenia z KSeF",
  };
  return labels[String(code || "").trim()] || formatujWartosc(code);
}

function pobierzKlaseWyjatkuFaktury(code) {
  const normalized = String(code || "").trim();
  if (normalized === "missing_contractor" || normalized === "weak_ocr" || normalized === "duplicate_requires_decision") {
    return "status-warning";
  }
  if (normalized === "missing_ksef_confirmation") {
    return "status-normal";
  }
  return "status-neutral";
}

function zsynchronizujZaznaczoneFaktury(faktury) {
  const dostepneId = new Set((Array.isArray(faktury) ? faktury : []).map((invoice) => Number(invoice.id)));
  stan.zaznaczoneFaktury = stan.zaznaczoneFaktury.filter((invoiceId) => dostepneId.has(Number(invoiceId)));
  renderujPodsumowanieZaznaczeniaPaczkiFaktur();
}

function czyFakturaJestZaznaczona(invoiceId) {
  return stan.zaznaczoneFaktury.includes(Number(invoiceId));
}

function ustawZaznaczenieFaktury(invoiceId, checked) {
  const normalizedId = Number(invoiceId || 0);
  if (!normalizedId) {
    return;
  }
  const set = new Set(stan.zaznaczoneFaktury.map((value) => Number(value)));
  if (checked) {
    set.add(normalizedId);
  } else {
    set.delete(normalizedId);
  }
  stan.zaznaczoneFaktury = Array.from(set);
  renderujPodsumowanieZaznaczeniaPaczkiFaktur();
}

function ustawZaznaczenieWszystkichFaktur(checked) {
  if (!Array.isArray(stan.faktury) || !stan.faktury.length) {
    stan.zaznaczoneFaktury = [];
  } else if (checked) {
    stan.zaznaczoneFaktury = stan.faktury.map((invoice) => Number(invoice.id));
  } else {
    stan.zaznaczoneFaktury = [];
  }
  renderujFaktury(stan.faktury || []);
}

function renderujPodsumowanieZaznaczeniaPaczkiFaktur() {
  const summary = document.getElementById("invoice-handoff-selection-summary");
  const button = document.getElementById("invoice-create-handoff-batch");
  if (summary) {
    const count = stan.zaznaczoneFaktury.length;
    summary.textContent = count
      ? `Wybrano ${count} faktur(y) do paczki przekazania.`
      : "Zaznacz faktury na liscie, aby utworzyc paczke przekazania.";
  }
  if (button) {
    button.disabled = !stan.zaznaczoneFaktury.length || !czyMoznaPodejmowacDecyzjeFaktur();
  }
}

function renderujSkrzynkePrzyjeciaDokumentowFaktur(snapshot) {
  stan.skrzynkaPrzyjeciaDokumentowFaktur = snapshot || null;
  const container = document.getElementById("invoice-document-intake");
  const count = document.getElementById("invoice-document-intake-count");
  if (!container || !count) {
    return;
  }
  const items = Array.isArray(snapshot?.items) ? snapshot.items : [];
  const summary = snapshot?.summary || {};
  count.textContent = `${Number(summary.count || 0)} pozycji`;
  if (!items.length) {
    container.innerHTML = `<div class="empty-state">Brak dokumentow oczekujacych w skrzynce przyjecia.</div>`;
    return;
  }

  container.innerHTML = `
    <div class="invoice-ops-summary-row">
      ${Object.entries(summary.counts_by_status || {})
        .map(
          ([status, value]) =>
            `<span class="status-badge ${pobierzKlaseStatusuIntakeFaktury(status)}">${bezpiecznyTekst(pobierzEtykieteStatusuIntakeFaktury(status))}: ${bezpiecznyTekst(value)}</span>`
        )
        .join("")}
    </div>
    <div class="invoice-ops-list">
      ${items
        .map((item) => {
          const linkedInvoice = item.linked_invoice || {};
          const metadata = item.metadata || {};
          return `
            <article class="invoice-ops-item">
              <div class="verification-card-header">
                <div>
                  <strong>${bezpiecznyTekst(item.title || linkedInvoice.invoice_number || `Dokument #${item.intake_item_id}`)}</strong>
                  <div class="subtle-note">${bezpiecznyTekst(metadata.file_name || linkedInvoice.file_name || item.source_reference || "-")}</div>
                </div>
                <div>${zbudujBadgeStanu(pobierzEtykieteStatusuIntakeFaktury(item.status), pobierzKlaseStatusuIntakeFaktury(item.status))}</div>
              </div>
              <div class="invoice-ops-meta">
                <span>${formatujNazweOrganizacji(item.organization_name || linkedInvoice.organization_name)}</span>
                <span>${formatujZrodlo(metadata.source || linkedInvoice.source)}</span>
                <span>${formatujDateCzas(item.last_activity_at || item.updated_at || item.created_at)}</span>
              </div>
              <div>${bezpiecznyTekst(item.description || "-")}</div>
              <div class="filters-actions">
                ${
                  linkedInvoice.id
                    ? `<button type="button" class="secondary" data-open-document-intake-invoice-id="${linkedInvoice.id}">Otworz fakture</button>`
                    : ""
                }
                ${metadata.file_link ? `<a href="${metadata.file_link}" target="_blank" rel="noreferrer">Otworz dokument</a>` : ""}
                ${metadata.ocr_link ? `<a href="${metadata.ocr_link}" target="_blank" rel="noreferrer">Otworz OCR</a>` : ""}
              </div>
            </article>
          `;
        })
        .join("")}
    </div>
  `;

  container.querySelectorAll("[data-open-document-intake-invoice-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      const invoiceId = Number(button.dataset.openDocumentIntakeInvoiceId || 0);
      if (!invoiceId) {
        return;
      }
      await wczytajSzczegolyFaktury(invoiceId);
      document.getElementById("invoice-detail")?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
}

function renderujCentrumWyjatkowFaktur(snapshot) {
  stan.centrumWyjatkowFaktur = snapshot || null;
  const container = document.getElementById("invoice-exception-center");
  const count = document.getElementById("invoice-exception-center-count");
  if (!container || !count) {
    return;
  }
  const items = Array.isArray(snapshot?.items) ? snapshot.items : [];
  const summary = snapshot?.summary || {};
  count.textContent = `${Number(summary.count || 0)} otwartych`;
  if (!items.length) {
    container.innerHTML = `<div class="empty-state">Brak aktywnych wyjatkow fakturowych.</div>`;
    return;
  }

  container.innerHTML = `
    <div class="invoice-ops-summary-row">
      ${Object.entries(summary.counts_by_code || {})
        .map(
          ([code, value]) =>
            `<span class="status-badge ${pobierzKlaseWyjatkuFaktury(code)}">${bezpiecznyTekst(pobierzEtykieteWyjatkuFaktury(code))}: ${bezpiecznyTekst(value)}</span>`
        )
        .join("")}
    </div>
    <div class="invoice-ops-list">
      ${items
        .map((item) => {
          const linkedInvoice = item.linked_invoice || {};
          const metadata = item.metadata || {};
          const exceptionCode = item.source_reference || metadata.exception_code;
          return `
            <article class="invoice-ops-item">
              <div class="verification-card-header">
                <div>
                  <strong>${bezpiecznyTekst(item.title || pobierzEtykieteWyjatkuFaktury(exceptionCode))}</strong>
                  <div class="subtle-note">${bezpiecznyTekst(linkedInvoice.invoice_number || linkedInvoice.ksef_number || `Faktura #${linkedInvoice.id || "-"}`)}</div>
                </div>
                <div>${zbudujBadgeStanu(pobierzEtykieteWyjatkuFaktury(exceptionCode), pobierzKlaseWyjatkuFaktury(exceptionCode))}</div>
              </div>
              <div class="invoice-ops-meta">
                <span>${formatujNazweOrganizacji(item.organization_name || linkedInvoice.organization_name)}</span>
                <span>${formatujZrodlo(metadata.source || linkedInvoice.source)}</span>
                <span>${formatujDateCzas(item.last_activity_at || item.updated_at || item.created_at)}</span>
                ${item.assigned_user_name ? `<span>Odpowiedzialny: ${bezpiecznyTekst(item.assigned_user_name)}</span>` : ""}
              </div>
              <div>${bezpiecznyTekst(item.description || "-")}</div>
              <div class="filters-actions">
                ${
                  linkedInvoice.id
                    ? `<button type="button" class="secondary" data-open-exception-invoice-id="${linkedInvoice.id}">Otworz fakture</button>`
                    : ""
                }
                <button type="button" class="secondary" data-open-exception-bucket="verification">Otworz workspace</button>
              </div>
            </article>
          `;
        })
        .join("")}
    </div>
  `;

  container.querySelectorAll("[data-open-exception-invoice-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      const invoiceId = Number(button.dataset.openExceptionInvoiceId || 0);
      if (!invoiceId) {
        return;
      }
      await wczytajSzczegolyFaktury(invoiceId);
      document.getElementById("invoice-detail")?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
  container.querySelectorAll("[data-open-exception-bucket]").forEach((button) => {
    button.addEventListener("click", async () => {
      await otworzWorkspaceWeryfikacjiFaktur(String(button.dataset.openExceptionBucket || "").trim());
    });
  });
}

function renderujSzczegolyPaczkiPrzekazania(snapshot) {
  stan.szczegolyPaczkiPrzekazaniaFaktur = snapshot || null;
  const container = document.getElementById("invoice-handoff-batch-detail");
  if (!container) {
    return;
  }
  if (!snapshot?.batch) {
    container.classList.add("hidden");
    container.innerHTML = "";
    return;
  }
  const batch = snapshot.batch;
  const items = Array.isArray(snapshot.items) ? snapshot.items : [];
  container.classList.remove("hidden");
  container.innerHTML = `
    <div class="panel-header">
      <h3>Szczegoly paczki ${bezpiecznyTekst(batch.batch_number || "")}</h3>
      <span class="pill">${bezpiecznyTekst(items.length)} faktur</span>
    </div>
    <div class="list">
      <div class="list-item"><strong>Status</strong><div>${zbudujBadgeStanu(formatujWartosc(batch.status), batch.status === "wyeksportowana" ? "status-success" : "status-warning")}</div></div>
      <div class="list-item"><strong>Cel przekazania</strong><div>${formatujWartosc(batch.handoff_target)}</div></div>
      <div class="list-item"><strong>Notatka</strong><div>${formatujWartosc(batch.note)}</div></div>
      <div class="list-item"><strong>Utworzyl</strong><div>${formatujWartosc(batch.created_by_user_name)}</div></div>
      <div class="list-item"><strong>Utworzono</strong><div>${formatujDateCzas(batch.created_at)}</div></div>
      <div class="list-item"><strong>Eksport</strong><div>${formatujDateCzas(batch.exported_at)}</div></div>
    </div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Numer faktury</th>
            <th>Numer KSeF</th>
            <th>Wystawca</th>
            <th>Kwota</th>
            <th>Status</th>
            <th>Obieg</th>
            <th>Akcja</th>
          </tr>
        </thead>
        <tbody>
          ${
            items.length
              ? items
                  .map(
                    (item) => `
                      <tr>
                        <td>${bezpiecznyTekst(item.invoice_id)}</td>
                        <td>${formatujWartosc(item.invoice_number)}</td>
                        <td>${formatujWartosc(item.ksef_number)}</td>
                        <td>${formatujWartosc(item.issuer_name)}</td>
                        <td>${formatujKwote(item.gross_amount, item.currency)}</td>
                        <td>${zbudujBadgeStanu(formatujWartosc(item.current_status), klasaStatusu(item.current_status, ""))}</td>
                        <td>${zbudujBadgeStanu(formatujObiegFaktury(item.current_workflow_state), klasaStatusuObieguFaktury(item.current_workflow_state))}</td>
                        <td><button type="button" class="secondary" data-open-handoff-invoice-id="${item.invoice_id}">Otworz fakture</button></td>
                      </tr>
                    `
                  )
                  .join("")
              : `<tr><td colspan="8">Brak faktur w tej paczce.</td></tr>`
          }
        </tbody>
      </table>
    </div>
    <div class="filters-actions">
      <button type="button" class="secondary" data-export-handoff-batch-id="${batch.invoice_handoff_batch_id}">Eksportuj CSV</button>
      <button type="button" class="secondary" data-close-handoff-detail="1">Zwin szczegoly</button>
    </div>
  `;

  container.querySelectorAll("[data-open-handoff-invoice-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      const invoiceId = Number(button.dataset.openHandoffInvoiceId || 0);
      if (!invoiceId) {
        return;
      }
      await wczytajSzczegolyFaktury(invoiceId);
      document.getElementById("invoice-detail")?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
  container.querySelector('[data-export-handoff-batch-id]')?.addEventListener("click", async () => {
    await eksportujPaczkePrzekazania(Number(batch.invoice_handoff_batch_id));
  });
  container.querySelector('[data-close-handoff-detail="1"]')?.addEventListener("click", () => {
    renderujSzczegolyPaczkiPrzekazania(null);
  });
}

function renderujPaczkiPrzekazaniaFaktur(snapshot) {
  stan.paczkiPrzekazaniaFaktur = snapshot || null;
  const container = document.getElementById("invoice-handoff-batches");
  const count = document.getElementById("invoice-handoff-batches-count");
  const createButton = document.getElementById("invoice-create-handoff-batch");
  if (!container || !count) {
    return;
  }
  if (createButton) {
    createButton.onclick = () => {
      void utworzPaczkePrzekazaniaFaktur();
    };
  }
  const batches = Array.isArray(snapshot?.batches) ? snapshot.batches : [];
  count.textContent = `${Number(snapshot?.summary?.count || 0)} paczek`;
  renderujPodsumowanieZaznaczeniaPaczkiFaktur();
  if (!batches.length) {
    renderujSzczegolyPaczkiPrzekazania(null);
    container.innerHTML = `<div class="empty-state">Nie utworzono jeszcze paczek przekazania.</div>`;
    return;
  }

  container.innerHTML = `
    <div class="invoice-ops-list">
      ${batches
        .map(
          (batch) => `
            <article class="invoice-ops-item">
              <div class="verification-card-header">
                <div>
                  <strong>${bezpiecznyTekst(batch.batch_number || `Paczka #${batch.invoice_handoff_batch_id}`)}</strong>
                  <div class="subtle-note">${formatujWartosc(batch.handoff_target || "Bez wskazanego celu")}</div>
                </div>
                <div>${zbudujBadgeStanu(formatujWartosc(batch.status), batch.status === "wyeksportowana" ? "status-success" : "status-warning")}</div>
              </div>
              <div class="invoice-ops-meta">
                <span>Faktur: ${bezpiecznyTekst(batch.invoice_count || 0)}</span>
                <span>Utworzono: ${formatujDateCzas(batch.created_at)}</span>
                ${batch.exported_at ? `<span>Eksport: ${formatujDateCzas(batch.exported_at)}</span>` : ""}
                ${batch.created_by_user_name ? `<span>Autor: ${bezpiecznyTekst(batch.created_by_user_name)}</span>` : ""}
              </div>
              ${batch.note ? `<div>${bezpiecznyTekst(batch.note)}</div>` : ""}
              <div class="filters-actions">
                <button type="button" class="secondary" data-open-handoff-batch-id="${batch.invoice_handoff_batch_id}">Otworz paczke</button>
                <button type="button" class="secondary" data-export-handoff-batch-id="${batch.invoice_handoff_batch_id}">Eksportuj CSV</button>
              </div>
            </article>
          `
        )
        .join("")}
    </div>
  `;

  container.querySelectorAll("[data-open-handoff-batch-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      await otworzSzczegolyPaczkiPrzekazania(Number(button.dataset.openHandoffBatchId || 0));
    });
  });
  container.querySelectorAll("[data-export-handoff-batch-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      await eksportujPaczkePrzekazania(Number(button.dataset.exportHandoffBatchId || 0));
    });
  });
}

function renderujSekcjeDokumentowPrzyjeciaFaktury(items) {
  if (!Array.isArray(items) || !items.length) {
    return `<div class="empty-state">Brak dokumentow przyjecia powiazanych z ta faktura.</div>`;
  }
  return `
    <div class="invoice-inline-list">
      ${items
        .map((item) => {
          const metadata = item.metadata || {};
          return `
            <article class="invoice-inline-card">
              <div class="verification-card-header">
                <strong>${bezpiecznyTekst(item.title || `Dokument #${item.intake_item_id}`)}</strong>
                ${zbudujBadgeStanu(pobierzEtykieteStatusuIntakeFaktury(item.status), pobierzKlaseStatusuIntakeFaktury(item.status))}
              </div>
              <div class="subtle-note">${bezpiecznyTekst(metadata.file_name || item.source_reference || "-")}</div>
              <div>${bezpiecznyTekst(item.description || "-")}</div>
            </article>
          `;
        })
        .join("")}
    </div>
  `;
}

function renderujSekcjeWyjatkowFaktury(items) {
  if (!Array.isArray(items) || !items.length) {
    return `<div class="empty-state">Brak aktywnych wyjatkow dla tej faktury.</div>`;
  }
  return `
    <div class="invoice-inline-list">
      ${items
        .map((item) => `
          <article class="invoice-inline-card">
            <div class="verification-card-header">
              <strong>${bezpiecznyTekst(item.title || pobierzEtykieteWyjatkuFaktury(item.source_reference))}</strong>
              ${zbudujBadgeStanu(pobierzEtykieteWyjatkuFaktury(item.source_reference), pobierzKlaseWyjatkuFaktury(item.source_reference))}
            </div>
            <div>${bezpiecznyTekst(item.description || "-")}</div>
            <div class="subtle-note">Ostatnia aktywnosc: ${formatujDateCzas(item.last_activity_at || item.updated_at || item.created_at)}</div>
          </article>
        `)
        .join("")}
    </div>
  `;
}

function renderujSekcjePaczekPrzekazaniaFaktury(items) {
  if (!Array.isArray(items) || !items.length) {
    return `<div class="empty-state">Ta faktura nie byla jeszcze dodana do paczki przekazania.</div>`;
  }
  return `
    <div class="invoice-inline-list">
      ${items
        .map(
          (item) => `
            <article class="invoice-inline-card">
              <div class="verification-card-header">
                <strong>${bezpiecznyTekst(item.batch_number || `Paczka #${item.invoice_handoff_batch_id}`)}</strong>
                ${zbudujBadgeStanu(formatujWartosc(item.status), item.status === "wyeksportowana" ? "status-success" : "status-warning")}
              </div>
              <div class="subtle-note">${formatujDateCzas(item.created_at)} | ${formatujWartosc(item.handoff_target)}</div>
              ${item.note ? `<div>${bezpiecznyTekst(item.note)}</div>` : ""}
              <div class="filters-actions">
                <button type="button" class="secondary" data-open-related-handoff-batch-id="${item.invoice_handoff_batch_id}">Otworz paczke</button>
              </div>
            </article>
          `
        )
        .join("")}
    </div>
  `;
}

async function otworzSzczegolyPaczkiPrzekazania(batchId) {
  const normalizedBatchId = Number(batchId || 0);
  if (!normalizedBatchId) {
    return;
  }
  const detail = await api(zbudujAdresZOrganizacja(`/api/invoice-handoff-batches/${normalizedBatchId}`));
  renderujSzczegolyPaczkiPrzekazania(detail);
  document.getElementById("invoice-handoff-batch-detail")?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function pobierzNazwePlikuPaczki(batch) {
  return String(batch?.file_name || batch?.batch?.file_name || batch?.batch?.batch_number || "paczka-przekazania.csv")
    .replace(/[^a-zA-Z0-9._-]+/g, "-");
}

function pobierzPlikTekstowy(content, fileName, mimeType = "text/plain;charset=utf-8") {
  const blob = new Blob([content], { type: mimeType });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

async function eksportujPaczkePrzekazania(batchId) {
  const normalizedBatchId = Number(batchId || 0);
  if (!normalizedBatchId || !czyMoznaPodejmowacDecyzjeFaktur()) {
    return;
  }
  const result = await api(zbudujAdresZOrganizacja(`/api/invoice-handoff-batches/${normalizedBatchId}/export`));
  pobierzPlikTekstowy(result.csv_content || "", pobierzNazwePlikuPaczki(result), "text/csv;charset=utf-8");
  pokazPowiadomienie("Wyeksportowano paczke przekazania.");
  await wczytajFaktury();
  await otworzSzczegolyPaczkiPrzekazania(normalizedBatchId);
}

async function utworzPaczkePrzekazaniaFaktur() {
  if (!czyMoznaPodejmowacDecyzjeFaktur()) {
    return;
  }
  if (!stan.zaznaczoneFaktury.length) {
    pokazPowiadomienie("Zaznacz co najmniej jedna fakture do paczki przekazania.");
    return;
  }
  const handoffTarget = document.getElementById("invoice-handoff-target")?.value?.trim() || "";
  const note = document.getElementById("invoice-handoff-note")?.value?.trim() || "";
  const result = await api(zbudujAdresZOrganizacja("/api/invoice-handoff-batches"), {
    method: "POST",
    body: JSON.stringify({
      invoice_ids: stan.zaznaczoneFaktury,
      handoff_target: handoffTarget,
      note,
    }),
  });
  stan.zaznaczoneFaktury = [];
  renderujPodsumowanieZaznaczeniaPaczkiFaktur();
  const handoffNoteField = document.getElementById("invoice-handoff-note");
  if (handoffNoteField) {
    handoffNoteField.value = "";
  }
  pokazPowiadomienie(`Utworzono paczke przekazania dla ${Number(result?.batch?.invoice_count || result?.items?.length || 0)} faktur(y).`);
  await wczytajFaktury();
  if (result?.batch?.invoice_handoff_batch_id) {
    renderujSzczegolyPaczkiPrzekazania(result);
  }
}

function formatujPolePorownaniaFaktur(fieldName, value, currency) {
  if (fieldName === "gross_amount") {
    return formatujKwote(value, currency);
  }
  return formatujWartosc(value);
}

function renderujModalPorownaniaFaktur(snapshot) {
  stan.porownanieDuplikatowFaktur = snapshot || null;
  const shell = document.getElementById("invoice-compare-modal");
  const title = document.getElementById("invoice-compare-modal-title");
  const subtitle = document.getElementById("invoice-compare-modal-subtitle");
  const body = document.getElementById("invoice-compare-modal-body");
  if (!shell || !title || !subtitle || !body) {
    return;
  }

  if (!snapshot) {
    shell.classList.add("hidden");
    shell.setAttribute("aria-hidden", "true");
    title.textContent = "Porownanie faktur";
    subtitle.textContent = "";
    body.innerHTML = "";
    return;
  }

  const left = snapshot.left_invoice || {};
  const right = snapshot.right_invoice || {};
  const summary = snapshot.summary || {};
  title.textContent = "Porownanie duplikatow obok siebie";
  subtitle.textContent = summary.recommendation || "Zobacz roznice i zgodnosci pomiedzy dwiema fakturami.";
  body.innerHTML = `
    <div class="invoice-compare-modal-summary">
      <article class="invoice-compare-modal-card">
        <span class="subtle-note">Lewa faktura</span>
        <strong>#${bezpiecznyTekst(left.id || "-")} | ${bezpiecznyTekst(left.invoice_number || left.ksef_number || "-")}</strong>
        <div>${bezpiecznyTekst(left.issuer_name || "-")} | ${bezpiecznyTekst(left.issuer_nip || "-")}</div>
        <div>${formatujDateCzas(left.incoming_date || left.issue_date)} | ${formatujKwote(left.gross_amount, left.currency)}</div>
        <div class="invoice-field-provenance-meta">
          ${zbudujBadgeStanu(formatujZrodlo(left.authoritative_source || left.source), "status-warning")}
          ${left.duplicate_type && left.duplicate_type !== "brak" ? zbudujBadgeStanu(formatujWartosc(left.duplicate_type), klasaStatusu(left.status, left.duplicate_type)) : ""}
        </div>
      </article>
      <article class="invoice-compare-modal-card">
        <span class="subtle-note">Prawa faktura</span>
        <strong>#${bezpiecznyTekst(right.id || "-")} | ${bezpiecznyTekst(right.invoice_number || right.ksef_number || "-")}</strong>
        <div>${bezpiecznyTekst(right.issuer_name || "-")} | ${bezpiecznyTekst(right.issuer_nip || "-")}</div>
        <div>${formatujDateCzas(right.incoming_date || right.issue_date)} | ${formatujKwote(right.gross_amount, right.currency)}</div>
        <div class="invoice-field-provenance-meta">
          ${zbudujBadgeStanu(formatujZrodlo(right.authoritative_source || right.source), "status-warning")}
          ${right.duplicate_type && right.duplicate_type !== "brak" ? zbudujBadgeStanu(formatujWartosc(right.duplicate_type), klasaStatusu(right.status, right.duplicate_type)) : ""}
        </div>
      </article>
    </div>
    <div class="invoice-field-provenance-meta" style="margin-bottom: 16px;">
      ${zbudujBadgeStanu(`${Number(summary.matching_count || 0)} zgodnych pol`, "status-success")}
      ${zbudujBadgeStanu(`${Number(summary.different_count || 0)} roznych pol`, Number(summary.different_count || 0) ? "status-warning" : "status-success")}
      ${summary.same_ksef_number ? zbudujBadgeStanu("Ten sam numer KSeF", "status-danger") : ""}
      ${summary.same_invoice_number_and_nip ? zbudujBadgeStanu("Ten sam numer faktury i NIP", "status-warning") : ""}
    </div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Pole</th>
            <th>Lewa faktura</th>
            <th>Prawa faktura</th>
            <th>Ocena</th>
          </tr>
        </thead>
        <tbody>
          ${(Array.isArray(snapshot.rows) ? snapshot.rows : [])
            .map((row) => `
              <tr>
                <td>
                  <strong>${bezpiecznyTekst(row.label || row.field_name)}</strong>
                </td>
                <td>
                  <div>${formatujPolePorownaniaFaktur(row.field_name, row.left_value, left.currency)}</div>
                  <div class="subtle-note">${bezpiecznyTekst(row.left_source_label || "-")}</div>
                  <div class="invoice-field-provenance-meta">
                    ${row.left_is_ksef_protected ? zbudujBadgeStanu("KSeF", "status-warning") : ""}
                    ${row.left_has_local_override ? zbudujBadgeStanu("Korekta lokalna", "status-success") : ""}
                  </div>
                </td>
                <td>
                  <div>${formatujPolePorownaniaFaktur(row.field_name, row.right_value, right.currency)}</div>
                  <div class="subtle-note">${bezpiecznyTekst(row.right_source_label || "-")}</div>
                  <div class="invoice-field-provenance-meta">
                    ${row.right_is_ksef_protected ? zbudujBadgeStanu("KSeF", "status-warning") : ""}
                    ${row.right_has_local_override ? zbudujBadgeStanu("Korekta lokalna", "status-success") : ""}
                  </div>
                </td>
                <td>${zbudujBadgeStanu(row.matches ? "Zgodne" : "Rozne", row.matches ? "status-success" : "status-warning")}</td>
              </tr>
            `)
            .join("")}
        </tbody>
      </table>
    </div>
  `;
  shell.classList.remove("hidden");
  shell.setAttribute("aria-hidden", "false");
}

function zamknijModalPorownaniaFaktur() {
  renderujModalPorownaniaFaktur(null);
}

async function wczytajPorownanieFaktur(leftInvoiceId, rightInvoiceId) {
  const comparison = await api(
    zbudujAdresZOrganizacja(`/api/invoices/compare?left_id=${Number(leftInvoiceId)}&right_id=${Number(rightInvoiceId)}`)
  );
  renderujModalPorownaniaFaktur(comparison);
}

function renderujModalPodgladuFaktury(snapshot) {
  stan.podgladFaktury = snapshot || null;
  const shell = document.getElementById("invoice-preview-modal");
  const title = document.getElementById("invoice-preview-modal-title");
  const subtitle = document.getElementById("invoice-preview-modal-subtitle");
  const body = document.getElementById("invoice-preview-modal-body");
  const openDetail = document.getElementById("invoice-preview-modal-open-detail");
  if (!shell || !title || !subtitle || !body || !openDetail) {
    return;
  }

  if (!snapshot) {
    shell.classList.add("hidden");
    shell.setAttribute("aria-hidden", "true");
    title.textContent = "Szybki podglad dokumentu";
    subtitle.textContent = "";
    body.innerHTML = "";
    openDetail.disabled = true;
    return;
  }

  const invoice = snapshot.invoice || {};
  const documentTrace = snapshot.document_trace || {};
  const fieldProvenance = Array.isArray(snapshot.field_provenance) ? snapshot.field_provenance.slice(0, 5) : [];
  const previewKind = String(documentTrace.preview_kind || "none");

  let stageHtml = `<div class="empty-state">Brak dostepnego podgladu dokumentu. Skorzystaj z pelnych szczegolow albo OCR.</div>`;
  if (previewKind === "pdf" && documentTrace.file_link) {
    stageHtml = `<iframe class="invoice-preview-frame" src="${bezpiecznyTekst(documentTrace.file_link)}#toolbar=0"></iframe>`;
  } else if (previewKind === "image" && documentTrace.file_link) {
    stageHtml = `<img class="invoice-preview-image" src="${bezpiecznyTekst(documentTrace.file_link)}" alt="Podglad dokumentu faktury" />`;
  } else if (previewKind === "text") {
    stageHtml = `<div class="code-block">${bezpiecznyTekst(snapshot.ocr_excerpt || "Brak tekstu OCR.")}</div>`;
  }

  title.textContent = `Szybki podglad faktury #${bezpiecznyTekst(invoice.id || "-")}`;
  subtitle.textContent = `${bezpiecznyTekst(invoice.invoice_number || invoice.ksef_number || "Bez numeru")} | ${bezpiecznyTekst(invoice.issuer_name || "-")}`;
  body.innerHTML = `
    <div class="invoice-preview-grid">
      <section class="invoice-preview-stage">
        <article class="invoice-preview-stage-card">
          <div class="invoice-preview-meta">
            ${zbudujBadgeStanu(formatujZrodlo(invoice.authoritative_source || invoice.source), "status-warning")}
            ${zbudujBadgeStanu(formatujWartosc(invoice.status), klasaStatusu(invoice.status, invoice.duplicate_type))}
            ${invoice.duplicate_type && invoice.duplicate_type !== "brak" ? zbudujBadgeStanu(formatujWartosc(invoice.duplicate_type), klasaStatusu(invoice.status, invoice.duplicate_type)) : ""}
            ${zbudujBadgeStanu(formatujObiegFaktury(invoice.workflow_state), klasaStatusuObieguFaktury(invoice.workflow_state))}
          </div>
          ${stageHtml}
          <div class="invoice-preview-actions">
            ${documentTrace.file_link ? `<a href="${bezpiecznyTekst(documentTrace.file_link)}" target="_blank" rel="noreferrer">Otworz dokument</a>` : ""}
            ${documentTrace.ocr_link ? `<a href="${bezpiecznyTekst(documentTrace.ocr_link)}" target="_blank" rel="noreferrer">Otworz OCR</a>` : ""}
          </div>
        </article>
      </section>
      <aside class="invoice-preview-sidebar">
        <article class="invoice-preview-sidebar-card">
          <strong>Najwazniejsze dane</strong>
          <div><strong>Numer faktury</strong> ${formatujWartosc(invoice.invoice_number)}</div>
          <div><strong>Numer KSeF</strong> ${formatujWartosc(invoice.ksef_number)}</div>
          <div><strong>NIP</strong> ${formatujWartosc(invoice.issuer_nip)}</div>
          <div><strong>Wystawca</strong> ${formatujWartosc(invoice.issuer_name)}</div>
          <div><strong>Data wplywu</strong> ${formatujDateCzas(invoice.incoming_date)}</div>
          <div><strong>Data wystawienia</strong> ${formatujWartosc(invoice.issue_date)}</div>
          <div><strong>Kwota</strong> ${formatujKwote(invoice.gross_amount, invoice.currency)}</div>
          <div><strong>Odpowiedzialny</strong> ${formatujWartosc(invoice.assigned_user_name)}</div>
          <div><strong>Kontrahent</strong> ${formatujWartosc(invoice.contractor_name)}</div>
        </article>
        <article class="invoice-preview-sidebar-card">
          <strong>Pochodzenie kluczowych pol</strong>
          ${
            fieldProvenance.length
              ? fieldProvenance
                  .map(
                    (item) => `
                      <div class="list-item">
                        <strong>${bezpiecznyTekst(item.label || item.field_name)}</strong>
                        <div>${formatujWartosc(item.current_value)}</div>
                        <div class="subtle-note">${bezpiecznyTekst(item.source_label || "-")}</div>
                      </div>
                    `
                  )
                  .join("")
              : `<div class="empty-state">Brak danych o pochodzeniu pol.</div>`
          }
        </article>
        <article class="invoice-preview-sidebar-card">
          <strong>OCR</strong>
          <div class="subtle-note">
            ${snapshot.ocr_excerpt ? bezpiecznyTekst(snapshot.ocr_excerpt) : "Brak wycinka OCR dla tej faktury."}
            ${snapshot.ocr_excerpt_truncated ? " ..." : ""}
          </div>
        </article>
      </aside>
    </div>
  `;
  shell.classList.remove("hidden");
  shell.setAttribute("aria-hidden", "false");
  openDetail.disabled = false;
}

function zamknijModalPodgladuFaktury() {
  renderujModalPodgladuFaktury(null);
}

async function wczytajPodgladFaktury(invoiceId) {
  const preview = await api(zbudujAdresZOrganizacja(`/api/invoices/${invoiceId}/preview`));
  renderujModalPodgladuFaktury(preview);
}

function renderujPochodzeniePolFaktury(detail) {
  const items = Array.isArray(detail?.field_provenance) ? detail.field_provenance : [];
  if (!items.length) {
    return `<div class="empty-state">Brak danych o pochodzeniu pol tej faktury.</div>`;
  }

  return `
    <div class="invoice-field-provenance-list">
      ${items
        .map((item) => {
          const currentValue =
            item.field_name === "gross_amount"
              ? formatujKwote(item.current_value, detail?.invoice?.currency)
              : formatujWartosc(item.current_value);
          const authoritativeValue =
            item.field_name === "gross_amount"
              ? formatujKwote(item.authoritative_value, detail?.invoice?.currency)
              : formatujWartosc(item.authoritative_value);
          const pendingValues = Array.isArray(item.pending_local_values)
            ? item.pending_local_values
                .map((value) =>
                  item.field_name === "gross_amount"
                    ? formatujKwote(value, detail?.invoice?.currency)
                    : formatujWartosc(value)
                )
                .join(", ")
            : "";
          return `
            <article class="invoice-field-provenance-item">
              <div class="verification-card-header">
                <div>
                  <strong>${bezpiecznyTekst(item.label || item.field_name)}</strong>
                  <div class="subtle-note">${bezpiecznyTekst(item.source_label || "-")}</div>
                </div>
                <div class="invoice-field-provenance-meta">
                  ${item.is_ksef_protected ? zbudujBadgeStanu("Chronione z KSeF", "status-warning") : ""}
                  ${item.has_active_local_override ? zbudujBadgeStanu("Lokalna korekta aktywna", "status-success") : ""}
                  ${item.pending_count ? zbudujBadgeStanu(`${item.pending_count} oczekuje`, "status-warning") : ""}
                </div>
              </div>
              <div class="invoice-field-provenance-values">
                <div><strong>Biezaca wartosc</strong> ${currentValue}</div>
                ${
                  item.has_authoritative_value
                    ? `<div><strong>Oryginal z KSeF</strong> ${authoritativeValue}</div>`
                    : ""
                }
                ${
                  pendingValues
                    ? `<div><strong>Oczekujaca propozycja</strong> ${pendingValues}</div>`
                    : ""
                }
              </div>
            </article>
          `;
        })
        .join("")}
    </div>
  `;
}

function renderujCentrumDuplikatow(detail) {
  const center = detail?.duplicate_center || {};
  const candidates = Array.isArray(center.candidates) ? center.candidates : [];
  if (!candidates.length) {
    return `<div class="empty-state">Brak kandydatow do porownania w centrum duplikatow.</div>`;
  }

  return `
    <div class="invoice-compare-list">
      ${candidates
        .map(
          (candidate) => `
            <article class="invoice-compare-card">
              <div class="invoice-compare-header">
                <div>
                  <strong>#${candidate.invoice_id} | ${bezpiecznyTekst(candidate.invoice_number || candidate.ksef_number || "-")}</strong>
                  <div class="muted">${bezpiecznyTekst(candidate.issuer_name || "-")} | ${bezpiecznyTekst(candidate.issuer_nip || "-")}</div>
                </div>
                <div class="invoice-field-provenance-meta">
                  ${candidate.relation_type ? zbudujBadgeStanu(bezpiecznyTekst(candidate.relation_type), "status-warning") : ""}
                  ${candidate.duplicate_type && candidate.duplicate_type !== "brak" ? zbudujBadgeStanu(bezpiecznyTekst(candidate.duplicate_type), klasaStatusu(candidate.status, candidate.duplicate_type)) : ""}
                  ${zbudujBadgeStanu(`${Number(candidate.match_strength || 0)} zgodnych`, Number(candidate.match_strength || 0) >= 3 ? "status-success" : "status-warning")}
                </div>
              </div>
              <div class="muted">${formatujDateCzas(candidate.issue_date)} | ${formatujKwote(candidate.gross_amount, candidate.currency)} | ${formatujZrodlo(candidate.source)}</div>
              ${
                candidate.relation_reason
                  ? `<div style="margin-top:8px;">${bezpiecznyTekst(candidate.relation_reason)}</div>`
                  : ""
              }
              ${
                Array.isArray(candidate.matching_labels) && candidate.matching_labels.length
                  ? `<div style="margin-top:10px;"><strong>Zgodne pola:</strong> ${bezpiecznyTekst(candidate.matching_labels.join(", "))}</div>`
                  : ""
              }
              ${
                Array.isArray(candidate.different_fields) && candidate.different_fields.length
                  ? `
                    <div class="invoice-compare-diff-list">
                      ${candidate.different_fields
                        .map(
                          (field) => `
                            <div class="list-item">
                              <strong>${bezpiecznyTekst(field.label)}</strong>
                              <div>Ta faktura: ${bezpiecznyTekst(formatujWartosc(field.current_value))}</div>
                              <div>Powiazana: ${bezpiecznyTekst(formatujWartosc(field.candidate_value))}</div>
                            </div>
                          `
                        )
                        .join("")}
                    </div>
                  `
                  : ""
              }
              <div class="filters-actions">
                <button type="button" class="secondary" data-compare-duplicate-invoice-id="${candidate.invoice_id}">Porownaj obok siebie</button>
                <button type="button" class="secondary" data-open-duplicate-invoice-id="${candidate.invoice_id}">Otworz powiazana fakture</button>
              </div>
            </article>
          `
        )
        .join("")}
    </div>
  `;
}

function renderujKomentarzeFaktury(items) {
  const comments = Array.isArray(items) ? items : [];
  if (!comments.length) {
    return `<div class="empty-state">Brak komentarzy do tej faktury.</div>`;
  }
  return `
    <div class="list">
      ${comments
        .map(
          (comment) => `
            <article class="list-item">
              <strong>${bezpiecznyTekst(comment.created_by_user_name || "Uzytkownik")}</strong>
              <div class="muted">${bezpiecznyTekst(formatujRole(comment.created_by_user_role))} | ${bezpiecznyTekst(formatujDateCzas(comment.created_at))}</div>
              <div>${bezpiecznyTekst(comment.note_text || "")}</div>
            </article>
          `
        )
        .join("")}
    </div>
  `;
}

function renderujSzczegolyFaktury(detail) {
  const invoice = detail.invoice;
  stan.wybranaFakturaId = invoice.id;
  const zablokowane = !czyMoznaZapisywac();
  const atrybutPola = zablokowane ? 'disabled aria-disabled="true"' : "";
  const atrybutPrzycisku = zablokowane ? 'disabled title="Ta rola ma tylko podglÄ…d danych."' : "";
  const atrybutPrzyciskuDecyzji = czyMoznaPodejmowacDecyzjeFaktur()
    ? ""
    : 'disabled title="Ta rola nie moĹĽe potwierdzaÄ‡ duplikatĂłw ani oznaczaÄ‡ faktur jako poprawne."';
  const sourceTrace = detail.source_trace || {};
  const documentTrace = detail.document_trace || {};
  const workflow = detail.workflow || {};
  const atrybutPrzyciskuObiegu = workflow.can_mark_ready
    ? ""
    : 'disabled title="Ta rola nie moze przygotowac faktury do przekazania."';
  const atrybutPrzyciskuPrzekazania = workflow.can_handoff
    ? ""
    : 'disabled title="Ta rola nie moze przekazac faktury dalej."';
  const atrybutPrzyciskuZamkniecia =
    workflow.can_close && !["w_pracy", "zamknieta"].includes(String(workflow.state || "").trim())
      ? ""
      : 'disabled title="Ta rola nie moze zamknac tej faktury na obecnym etapie obiegu."';
  const atrybutPrzyciskuPonownegoOtwarcia = workflow.can_reopen
    ? ""
    : 'disabled title="Ta rola nie moze ponownie otworzyc faktury."';
  const atrybutPrzyciskuCofnieciaDecyzji =
    workflow.undo?.available
      ? workflow.undo?.can_undo
        ? ""
        : workflow.undo?.requires_decision_role
          ? 'disabled title="Cofniecie tej decyzji wymaga roli decyzyjnej."'
          : 'disabled title="Nie mozesz teraz cofnac ostatniej decyzji obiegu."'
      : 'disabled title="Brak decyzji obiegu, ktora mozna teraz cofnac."';
  const czyMoznaDodawacPowiazaneWpisy = czyMoznaZapisywac();
  const atrybutPrzyciskuPowiazan = czyMoznaDodawacPowiazaneWpisy
    ? ""
    : 'disabled title="Ta rola nie moze tworzyc nowych wpisow w Asystencie Szefa."';

  document.getElementById("invoice-detail-empty").classList.add("hidden");
  const container = document.getElementById("invoice-detail");
  container.classList.remove("hidden");

  const opcjeKontrahentow = stan.kontrahenciWszyscy
    .filter((contractor) => Number(contractor.organization_id) === Number(invoice.organization_id))
    .map(
      (contractor) =>
        `<option value="${contractor.contractor_id}" ${Number(invoice.contractor_id) === Number(contractor.contractor_id) ? "selected" : ""}>${bezpiecznyTekst(contractor.name)} (${bezpiecznyTekst(contractor.nip)})</option>`
    )
    .join("");
  const czyMoznaPrzypisacFakture = czyMoznaPrzypisywacFaktury();
  const atrybutPolaOdpowiedzialnego = czyMoznaPrzypisacFakture
    ? atrybutPola
    : 'disabled title="Ta rola nie moze przypisywac odpowiedzialnego za fakture."';
  const opcjeOdpowiedzialnych = stan.uzytkownicyDoFaktur
    .filter((user) => Number(user.organization_id) === Number(invoice.organization_id))
    .map(
      (user) =>
        `<option value="${user.user_id}" ${Number(invoice.assigned_user_id) === Number(user.user_id) ? "selected" : ""}>${bezpiecznyTekst(user.display_name || user.login)} (${bezpiecznyTekst(formatujRole(user.role))})</option>`
    )
    .join("");

  container.innerHTML = `
    <div class="detail-grid">
      ${
        detail.ksef_protected
          ? `
            <div class="panel">
              <div class="panel-header"><h3>Ochrona danych z KSeF</h3></div>
              <div class="subtle-note">
                Ta faktura ma pola potwierdzone z KSeF. Po zapisaniu edycji system zachowa oryginal z KSeF, zapisze wartosc lokalna
                i dopiero wtedy utworzy albo pokaze prosbe o zatwierdzenie. Zatwierdzic moze Administrator organizacji, Wlasciciel systemu
                albo wskazany tymczasowy kierownik korekt KSeF.
              </div>
            </div>
          `
          : ""
      }
      <div class="summary-grid">
        <div class="summary-item"><strong>ID faktury</strong>${invoice.id}</div>
        <div class="summary-item"><strong>Organizacja</strong>${formatujNazweOrganizacji(invoice.organization_name)}</div>
        <div class="summary-item"><strong>Zrodlo nadrzedne</strong>${formatujZrodlo(invoice.authoritative_source || invoice.source)}</div>
        <div class="summary-item"><strong>ĹąrĂłdĹ‚o</strong>${formatujZrodlo(invoice.source)}</div>
        <div class="summary-item"><strong>Status</strong><span class="status-badge ${klasaStatusu(invoice.status, invoice.duplicate_type)}">${formatujWartosc(invoice.status)}</span></div>
        <div class="summary-item"><strong>Obieg</strong><span class="status-badge ${klasaStatusuObieguFaktury(workflow.state)}">${formatujObiegFaktury(workflow.state)}</span></div>
        <div class="summary-item"><strong>Typ duplikatu</strong><span class="status-badge ${klasaStatusu(invoice.status, invoice.duplicate_type)}">${formatujWartosc(invoice.duplicate_type)}</span></div>
        <div class="summary-item"><strong>Odpowiedzialny</strong>${formatujWartosc(invoice.assigned_user_name)}</div>
        <div class="summary-item"><strong>Opis weryfikacji</strong>${formatujWartosc(invoice.flag_reason)}</div>
        <div class="summary-item"><strong>Identyfikator techniczny</strong>${formatujWartosc(invoice.invoice_hash)}</div>
      </div>

      <div class="panel">
        <div class="panel-header"><h3>Obieg operacyjny</h3></div>
        <div class="list">
          <div class="list-item"><strong>Stan obiegu</strong><div><span class="status-badge ${klasaStatusuObieguFaktury(workflow.state)}">${formatujObiegFaktury(workflow.state)}</span></div></div>
          <div class="list-item"><strong>Gotowa do przekazania od</strong><div>${formatujDateCzas(workflow.ready_for_handoff_at)}</div></div>
          <div class="list-item"><strong>Oznaczyl</strong><div>${formatujWartosc(workflow.ready_for_handoff_by_user_name)}</div></div>
          <div class="list-item"><strong>Cel przekazania</strong><div>${formatujWartosc(workflow.handoff_target)}</div></div>
          <div class="list-item"><strong>Notatka przekazania</strong><div>${formatujWartosc(workflow.handoff_note)}</div></div>
          <div class="list-item"><strong>Przekazano</strong><div>${formatujDateCzas(workflow.handed_off_at)}</div></div>
          <div class="list-item"><strong>Przekazal</strong><div>${formatujWartosc(workflow.handed_off_by_user_name)}</div></div>
          <div class="list-item"><strong>Zamknieto</strong><div>${formatujDateCzas(workflow.closed_at)}</div></div>
          <div class="list-item"><strong>Zamknal</strong><div>${formatujWartosc(workflow.closed_by_user_name)}</div></div>
          <div class="list-item"><strong>Powod zamkniecia</strong><div>${formatujWartosc(workflow.closed_reason)}</div></div>
          <div class="list-item"><strong>Ponownie otwarto</strong><div>${formatujDateCzas(workflow.reopened_at)}</div></div>
          <div class="list-item"><strong>Otwarta przez</strong><div>${formatujWartosc(workflow.reopened_by_user_name)}</div></div>
          <div class="list-item"><strong>Powod ponownego otwarcia</strong><div>${formatujWartosc(workflow.reopen_reason)}</div></div>
        </div>
        <div class="detail-actions">
          <button class="secondary" id="mark-invoice-ready" ${atrybutPrzyciskuObiegu}>Oznacz gotowa do przekazania</button>
          <button class="secondary" id="handoff-invoice" ${atrybutPrzyciskuPrzekazania}>Przekaz dalej</button>
          <button class="secondary" id="close-invoice" ${atrybutPrzyciskuZamkniecia}>Zamknij obieg</button>
          <button class="secondary" id="reopen-invoice" ${atrybutPrzyciskuPonownegoOtwarcia}>Ponownie otworz</button>
          <button class="secondary" id="undo-invoice-workflow" ${atrybutPrzyciskuCofnieciaDecyzji}>${bezpiecznyTekst(
            workflow.undo?.action_label || "Cofnij ostatnia decyzje"
          )}</button>
        </div>
      </div>

      <div class="detail-actions">
        <button id="save-invoice" ${atrybutPrzycisku}>Zapisz zmiany</button>
        <button class="secondary" id="confirm-duplicate" ${atrybutPrzyciskuDecyzji}>PotwierdĹş duplikat</button>
        <button class="secondary" id="reject-duplicate" ${atrybutPrzyciskuDecyzji}>Oznacz jako poprawnÄ…</button>
        <a href="${invoice.file_link || "#"}" target="_blank" rel="noreferrer">OtwĂłrz dokument</a>
        <a href="${invoice.ocr_link || "#"}" target="_blank" rel="noreferrer">OtwĂłrz OCR</a>
      </div>

      <div class="panel">
        <div class="panel-header"><h3>Edycja faktury</h3></div>
        <form id="invoice-edit-form" class="field-grid">
          <div class="field">
            <label>Nazwa pliku</label>
            <input name="file_name" value="${bezpiecznyTekst(invoice.file_name || "")}" ${atrybutPola} />
          </div>
          <div class="field">
            <label>Data wpĹ‚ywu</label>
            <input name="incoming_date" type="date" value="${bezpiecznyTekst(invoice.incoming_date || "")}" ${atrybutPola} />
          </div>
          <div class="field">
            <label>Numer faktury</label>
            <input name="invoice_number" value="${bezpiecznyTekst(invoice.invoice_number || "")}" ${atrybutPola} />
          </div>
          <div class="field">
            <label>Numer KSeF</label>
            <input name="ksef_number" value="${bezpiecznyTekst(invoice.ksef_number || "")}" ${atrybutPola} />
          </div>
          <div class="field">
            <label>NIP wystawcy</label>
            <input name="issuer_nip" value="${bezpiecznyTekst(invoice.issuer_nip || "")}" ${atrybutPola} />
          </div>
          <div class="field">
            <label>Nazwa wystawcy</label>
            <input name="issuer_name" value="${bezpiecznyTekst(invoice.issuer_name || "")}" ${atrybutPola} />
          </div>
          <div class="field">
            <label>Data wystawienia</label>
            <input name="issue_date" type="date" value="${bezpiecznyTekst(invoice.issue_date || "")}" ${atrybutPola} />
          </div>
          <div class="field">
            <label>Data sprzedaĹĽy</label>
            <input name="sale_date" type="date" value="${bezpiecznyTekst(invoice.sale_date || "")}" ${atrybutPola} />
          </div>
          <div class="field">
            <label>Kwota brutto</label>
            <input name="gross_amount" type="number" step="0.01" value="${bezpiecznyTekst(invoice.gross_amount ?? "")}" ${atrybutPola} />
          </div>
          <div class="field">
            <label>Waluta</label>
            <input name="currency" value="${bezpiecznyTekst(invoice.currency || "PLN")}" ${atrybutPola} />
          </div>
          <div class="field">
            <label>Status</label>
            <select name="status" ${atrybutPola}>
              ${stan.meta.statuses
                .map((status) => `<option value="${status}" ${status === invoice.status ? "selected" : ""}>${status}</option>`)
                .join("")}
            </select>
          </div>
          <div class="field">
            <label>Kontrahent</label>
            <select name="contractor_id" ${atrybutPola}>
              <option value="">Brak przypisania</option>
              ${opcjeKontrahentow}
            </select>
          </div>
          <div class="field">
            <label>Odpowiedzialny</label>
            <select name="assigned_user_id" ${atrybutPolaOdpowiedzialnego}>
              <option value="">Brak przypisania</option>
              ${opcjeOdpowiedzialnych}
            </select>
          </div>
          <div class="field" style="grid-column: 1 / -1;">
            <label>Notatki</label>
            <textarea name="notes" ${atrybutPola}>${bezpiecznyTekst(invoice.notes || "")}</textarea>
          </div>
        </form>
      </div>

      <div class="detail-columns">
        <div class="panel">
          <div class="panel-header"><h3>Ĺšlad ĹşrĂłdĹ‚a i dokumentu</h3></div>
          <div class="list">
            <div class="list-item"><strong>Organizacja</strong><div>${formatujNazweOrganizacji(sourceTrace.organization_name)}</div></div>
            <div class="list-item"><strong>Zrodlo nadrzedne</strong><div>${formatujZrodlo(sourceTrace.authoritative_source || sourceTrace.source)}</div></div>
            <div class="list-item"><strong>ĹąrĂłdĹ‚o</strong><div>${formatujZrodlo(sourceTrace.source)}</div></div>
            <div class="list-item"><strong>Typ dokumentu</strong><div>${formatujWartosc(sourceTrace.document_type)}</div></div>
            <div class="list-item"><strong>Identyfikator ĹşrĂłdĹ‚a</strong><div>${formatujWartosc(sourceTrace.source_external_id)}</div></div>
            <div class="list-item"><strong>Nadawca ĹşrĂłdĹ‚a</strong><div>${formatujWartosc(sourceTrace.source_sender_name)}</div></div>
            <div class="list-item"><strong>Id nadawcy</strong><div>${formatujWartosc(sourceTrace.source_sender_id)}</div></div>
            <div class="list-item"><strong>PowiÄ…zany uĹĽytkownik systemu</strong><div>${formatujWartosc(sourceTrace.linked_user?.display_name || sourceTrace.linked_user?.login)}</div></div>
            <div class="list-item"><strong>Nazwa pliku</strong><div>${formatujWartosc(documentTrace.file_name)}</div></div>
            <div class="list-item"><strong>Identyfikator techniczny</strong><div>${formatujWartosc(documentTrace.invoice_hash)}</div></div>
            <div class="list-item"><strong>Pewnosc OCR <span class="help-badge" title="OCR to automatyczne odczytywanie tekstu z PDF-u, skanu albo zdjecia faktury.">?</span></strong><div>${formatujWartosc(documentTrace.ocr_confidence)}</div></div>
          </div>
          <div class="panel-header" style="margin-top: 16px;"><h3>Tekst OCR</h3></div>
          <div class="code-block">${bezpiecznyTekst(invoice.ocr_raw_text || "Brak tekstu OCR dla tej faktury.")}</div>
          <div class="filters-actions">
            <a href="${documentTrace.file_link || "#"}" target="_blank" rel="noreferrer">OtwĂłrz zapisany dokument</a>
            <a href="${documentTrace.ocr_link || "#"}" target="_blank" rel="noreferrer">OtwĂłrz zapis OCR</a>
          </div>
          <div class="panel-header" style="margin-top: 16px;"><h3>Metadane ĹşrĂłdĹ‚a</h3></div>
          ${renderujMetadaneZrodla(sourceTrace.metadata)}
        </div>
        <div class="panel">
          <div class="panel-header"><h3>Dane kontrahenta</h3></div>
          ${
            detail.contractor
              ? `
                <div class="list">
                  <div class="list-item"><strong>Nazwa</strong><div>${formatujWartosc(detail.contractor.name)}</div></div>
                  <div class="list-item"><strong>NIP</strong><div>${formatujWartosc(detail.contractor.nip)}</div></div>
                  <div class="list-item"><strong>Nowy kontrahent</strong><div>${detail.contractor.is_new ? "tak" : "nie"}</div></div>
                  <div class="list-item"><strong>ByĹ‚ znany wczeĹ›niej</strong><div>${detail.contractor_known_before ? "tak" : "nie"}</div></div>
                  <div class="list-item"><strong>Liczba faktur</strong><div>${formatujWartosc(detail.contractor.invoice_count)}</div></div>
                  <div class="list-item"><strong>Notatki</strong><div>${formatujWartosc(detail.contractor.notes)}</div></div>
                </div>
              `
              : `<div class="empty-state">Brak powiÄ…zanego kontrahenta.</div>`
          }
        </div>
      </div>

      ${zbudujSekcjeOtwartchSprawDlaEncji({
        title: "Otwarte sprawy",
        items: detail.linked_tasks || [],
        emptyLabel: "Brak otwartych spraw powiazanych z ta faktura.",
        createLabel: "Dodaj wpis do tej faktury",
        createWithContractorLabel: detail.contractor ? "Dodaj wpis do faktury i kontrahenta" : "",
        buttonAttributes: atrybutPrzyciskuPowiazan,
        note: detail.contractor
          ? "Nowy wpis pozostanie domyslnie prywatny, ale od razu polaczy sie z faktura i kontrahentem."
          : "Nowy wpis pozostanie domyslnie prywatny, ale od razu polaczy sie z ta faktura.",
      })}

      <div class="panel">
        <div class="panel-header"><h3>Pochodzenie kluczowych pol</h3></div>
        ${renderujPochodzeniePolFaktury(detail)}
      </div>

      <div class="panel">
        <div class="panel-header"><h3>Dokumenty przyjecia</h3></div>
        ${renderujSekcjeDokumentowPrzyjeciaFaktury(detail.document_intake_items)}
      </div>

      <div class="panel">
        <div class="panel-header"><h3>Wyjatki operacyjne</h3></div>
        ${renderujSekcjeWyjatkowFaktury(detail.exceptions)}
      </div>

      <div class="panel">
        <div class="panel-header"><h3>Paczki przekazania</h3></div>
        ${renderujSekcjePaczekPrzekazaniaFaktury(detail.handoff_batches)}
      </div>

      <div class="panel">
        <div class="panel-header"><h3>Centrum duplikatow</h3></div>
        ${renderujCentrumDuplikatow(detail)}
      </div>

      ${renderujSekcjeKorektKsef(detail)}

      <div class="panel">
        <div class="panel-header"><h3>Aktywne relacje duplikatĂłw</h3></div>
        ${renderujRelacje(detail.relations)}
      </div>

      <div class="panel">
        <div class="panel-header"><h3>Podobne lub powiÄ…zane faktury</h3></div>
        ${renderujPodobneFaktury(detail.similar_invoices)}
      </div>

      <div class="panel">
        <div class="panel-header"><h3>Historia dziaĹ‚aĹ„</h3></div>
        ${renderujHistorie(detail.history)}
      </div>

      <div class="panel">
        <div class="panel-header"><h3>Komentarze do faktury</h3></div>
        ${renderujKomentarzeFaktury(detail.comments)}
        ${
          czyMoznaZapisywac()
            ? `
              <form id="invoice-comment-form" class="field-grid" style="margin-top: 16px;">
                <div class="field" style="grid-column: 1 / -1;">
                  <label>Nowy komentarz</label>
                  <textarea id="invoice-comment-text" placeholder="Dodaj komentarz zespolowy do tej faktury."></textarea>
                </div>
                <div class="filters-actions">
                  <button type="submit">Dodaj komentarz</button>
                </div>
              </form>
            `
            : ""
        }
      </div>

      <div class="panel">
        ${renderujSekcjeAkceptacji("invoice", invoice.id, detail.approval_requests || [], {
          canWrite: czyMoznaZapisywac(),
          title: "Akceptacje faktury",
          emptyLabel: "Brak wnioskow akceptacyjnych dla tej faktury.",
        })}
      </div>
    </div>
  `;

  document.getElementById("save-invoice")?.addEventListener("click", zapiszZmianyFaktury);
  document.getElementById("confirm-duplicate")?.addEventListener("click", potwierdzDuplikat);
  document.getElementById("reject-duplicate")?.addEventListener("click", odrzucPodejrzenieDuplikatu);
  document.getElementById("mark-invoice-ready")?.addEventListener("click", oznaczFaktureGotowaDoPrzekazania);
  document.getElementById("handoff-invoice")?.addEventListener("click", przekazFaktureDalej);
  document.getElementById("close-invoice")?.addEventListener("click", zamknijFakture);
  document.getElementById("reopen-invoice")?.addEventListener("click", ponownieOtworzFakture);
  document.getElementById("undo-invoice-workflow")?.addEventListener("click", cofnijOstatniaDecyzjeObieguFaktury);
  container.querySelectorAll("[data-linked-task-id]").forEach((item) => {
    item.addEventListener("click", async () => {
      try {
        await otworzPowiazaneZadanieZKontekstu(Number(item.dataset.linkedTaskId || 0), invoice.organization_id);
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
    });
  });
  container.querySelector('[data-linked-task-create="primary"]')?.addEventListener("click", async () => {
    try {
      await rozpocznijNowyWpisPowiazany(
        {
          title: `Sprawa do faktury ${invoice.invoice_number || `#${invoice.id}`}`,
          task_type: "zadanie",
          linked_entities: [{ entity_type: "invoice", entity_id: invoice.id }],
        },
        invoice.organization_id
      );
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  container.querySelector('[data-linked-task-create="secondary"]')?.addEventListener("click", async () => {
    try {
      await rozpocznijNowyWpisPowiazany(
        {
          title: `Sprawa do faktury ${invoice.invoice_number || `#${invoice.id}`}`,
          task_type: "zadanie",
          linked_entities: [
            { entity_type: "invoice", entity_id: invoice.id },
            ...(detail.contractor ? [{ entity_type: "contractor", entity_id: detail.contractor.contractor_id }] : []),
          ],
        },
        invoice.organization_id
      );
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  container.querySelectorAll("[data-open-duplicate-invoice-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      const invoiceId = Number(button.dataset.openDuplicateInvoiceId || 0);
      if (!invoiceId) {
        return;
      }
      await wczytajSzczegolyFaktury(invoiceId);
    });
  });
  container.querySelectorAll("[data-compare-duplicate-invoice-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      const rightInvoiceId = Number(button.dataset.compareDuplicateInvoiceId || 0);
      if (!rightInvoiceId || !stan.wybranaFakturaId) {
        return;
      }
      await wczytajPorownanieFaktur(stan.wybranaFakturaId, rightInvoiceId);
    });
  });
  container.querySelectorAll("[data-open-related-handoff-batch-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      await otworzSzczegolyPaczkiPrzekazania(Number(button.dataset.openRelatedHandoffBatchId || 0));
    });
  });
  const formularzAkceptacji = document.getElementById("approval-create-form");
  if (formularzAkceptacji) {
    formularzAkceptacji.addEventListener("submit", async (event) => {
      event.preventDefault();
      try {
        const shell = formularzAkceptacji.closest("[data-approval-entity-type]");
        const entityType = shell?.dataset.approvalEntityType || "invoice";
        const entityId = Number(shell?.dataset.approvalEntityId || invoice.id || 0);
        await utworzWniosekAkceptacjiDlaEncji(entityType, entityId);
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
    });
  }
  document.querySelectorAll("[data-approval-action]").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        const shell = button.closest("[data-approval-entity-type]");
        const entityType = shell?.dataset.approvalEntityType || "invoice";
        const entityId = Number(shell?.dataset.approvalEntityId || invoice.id || 0);
        await zdecydujWniosekAkceptacji(
          Number(button.dataset.approvalId || 0),
          String(button.dataset.approvalAction || ""),
          entityType,
          entityId
        );
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
    });
  });
}

function wyczyscSzczegolyFaktury() {
  stan.wybranaFakturaId = null;
  document.getElementById("invoice-detail").classList.add("hidden");
  document.getElementById("invoice-detail").innerHTML = "";
  document.getElementById("invoice-detail-empty").classList.remove("hidden");
}

function zsynchronizujFiltrKontrahenta() {
  const select = document.getElementById("filter-contractor");
  if (!select) {
    return;
  }
  const obecnaWartosc = select.value;
  select.innerHTML =
    `<option value="">Wszyscy kontrahenci</option>` +
    stan.kontrahenciWszyscy
      .map(
        (contractor) =>
          `<option value="${contractor.contractor_id}">${bezpiecznyTekst(contractor.name)} (${bezpiecznyTekst(contractor.nip)})</option>`
      )
      .join("");
  if (obecnaWartosc) {
    select.value = obecnaWartosc;
  }
}

function zsynchronizujFiltrOdpowiedzialnegoZaFakture() {
  const select = document.getElementById("filter-invoice-assignee");
  if (!select) {
    return;
  }
  const obecnaWartosc = select.value;
  select.innerHTML =
    `<option value="">Wszyscy odpowiedzialni</option>` +
    stan.uzytkownicyDoFaktur
      .map(
        (user) =>
          `<option value="${user.user_id}">${bezpiecznyTekst(user.display_name || user.login)} (${bezpiecznyTekst(formatujRole(user.role))})</option>`
      )
      .join("");
  if (obecnaWartosc) {
    select.value = obecnaWartosc;
  }
}

function renderujKontrahentow(kontrahenci) {
  stan.kontrahenciWidoczni = kontrahenci;
  odswiezPasekFiltrowKontrahentow();
  if (!kontrahenci.some((contractor) => Number(contractor.contractor_id) === Number(stan.wybranyKontrahentId))) {
    wyczyscSzczegolyKontrahenta();
  }

  const body = document.getElementById("contractor-table-body");
  if (!kontrahenci.length) {
    body.innerHTML = `<tr><td colspan="9">Brak kontrahentĂłw.</td></tr>`;
    return;
  }

  body.innerHTML = kontrahenci
    .map(
      (contractor) => `
        <tr class="clickable" data-contractor-id="${contractor.contractor_id}">
          <td>${contractor.contractor_id}</td>
                  <td>${formatujNazweOrganizacji(contractor.organization_name)}</td>
          <td>${formatujWartosc(contractor.name)}</td>
          <td>${formatujWartosc(contractor.nip)}</td>
                  <td>${formatujDateCzas(contractor.created_at)}</td>
                  <td>${formatujWartosc(contractor.email)}</td>
                  <td>${contractor.is_new ? '<span class="status-badge status-warning">tak</span>' : "nie"}</td>
                  <td>${formatujWartosc(contractor.invoice_count)}</td>
                  <td>${formatujWartosc(contractor.last_invoice_number)}</td>
        </tr>
      `
    )
    .join("");

  body.querySelectorAll("[data-contractor-id]").forEach((row) => {
    row.addEventListener("click", () => wczytajSzczegolyKontrahenta(Number(row.dataset.contractorId)));
  });
}

function renderujSzczegolyKontrahenta(detail) {
  document.getElementById("contractor-detail-empty").classList.add("hidden");
  const container = document.getElementById("contractor-detail");
  container.classList.remove("hidden");
  const contractor = detail.contractor;
  const czyMoznaDodawacPowiazaneWpisy = czyMoznaZapisywac();
  const atrybutPrzyciskuPowiazan = czyMoznaDodawacPowiazaneWpisy
    ? ""
    : 'disabled title="Ta rola nie moze tworzyc nowych wpisow w Asystencie Szefa."';

  container.innerHTML = `
    <div class="detail-grid">
      <div class="summary-grid">
        <div class="summary-item"><strong>ID kontrahenta</strong>${contractor.contractor_id}</div>
        <div class="summary-item"><strong>Organizacja</strong>${formatujNazweOrganizacji(contractor.organization_name)}</div>
        <div class="summary-item"><strong>Nazwa</strong>${formatujWartosc(contractor.name)}</div>
        <div class="summary-item"><strong>NIP</strong>${formatujWartosc(contractor.nip)}</div>
        <div class="summary-item"><strong>Data dodania</strong>${formatujDateCzas(contractor.created_at)}</div>
        <div class="summary-item"><strong>Nowy kontrahent</strong>${contractor.is_new ? "tak" : "nie"}</div>
        <div class="summary-item"><strong>Ostatnia faktura</strong>${formatujWartosc(contractor.last_invoice_number)}</div>
        <div class="summary-item"><strong>Liczba faktur</strong>${formatujWartosc(contractor.invoice_count)}</div>
      </div>
      <div class="panel">
        <div class="panel-header"><h3>Dane kontaktowe</h3></div>
        <div class="list">
          <div class="list-item"><strong>E-mail</strong><div>${formatujWartosc(contractor.email)}</div></div>
          <div class="list-item"><strong>Telefon</strong><div>${formatujWartosc(contractor.phone)}</div></div>
          <div class="list-item"><strong>Notatki</strong><div>${formatujWartosc(contractor.notes)}</div></div>
        </div>
      </div>
      <div class="panel">
        <div class="panel-header"><h3>PowiÄ…zane faktury</h3></div>
        ${renderujPodobneFaktury(detail.invoices)}
      </div>
      ${zbudujSekcjeOtwartchSprawDlaEncji({
        title: "Otwarte sprawy",
        items: detail.linked_tasks || [],
        emptyLabel: "Brak otwartych spraw powiazanych z tym kontrahentem.",
        createLabel: "Dodaj wpis dla kontrahenta",
        buttonAttributes: atrybutPrzyciskuPowiazan,
        note: "Nowy wpis pozostanie domyslnie prywatny, ale od razu polaczy sie z tym kontrahentem.",
      })}
    </div>
  `;

  container.querySelectorAll("[data-linked-task-id]").forEach((item) => {
    item.addEventListener("click", async () => {
      try {
        await otworzPowiazaneZadanieZKontekstu(Number(item.dataset.linkedTaskId || 0), contractor.organization_id);
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
    });
  });
  container.querySelector('[data-linked-task-create="primary"]')?.addEventListener("click", async () => {
    try {
      await rozpocznijNowyWpisPowiazany(
        {
          title: `Sprawa dla kontrahenta ${contractor.name || `#${contractor.contractor_id}`}`,
          task_type: "zadanie",
          linked_entities: [{ entity_type: "contractor", entity_id: contractor.contractor_id }],
        },
        contractor.organization_id
      );
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
}

function wyczyscSzczegolyKontrahenta() {
  stan.wybranyKontrahentId = null;
  document.getElementById("contractor-detail").classList.add("hidden");
  document.getElementById("contractor-detail").innerHTML = "";
  document.getElementById("contractor-detail-empty").classList.remove("hidden");
}

function zbudujOpcjeRachunkowBankowych() {
  const select = document.getElementById("billing-import-bank-account-id");
  if (!select) {
    return;
  }
  const obecnaWartosc = select.value;
  const opcje = [`<option value="">Wybierz rachunek do importu</option>`]
    .concat(
      stan.rachunkiBankowe.map((rachunek) => {
        const suffix =
          czyGlobalnyAdministrator() && rachunek.organization_name
            ? ` | ${rachunek.organization_name}`
            : "";
        return `<option value="${rachunek.billing_bank_account_id}">${bezpiecznyTekst(rachunek.account_name)}${bezpiecznyTekst(suffix)}</option>`;
      })
    )
    .join("");
  select.innerHTML = opcje;
  if (obecnaWartosc && stan.rachunkiBankowe.some((item) => String(item.billing_bank_account_id) === String(obecnaWartosc))) {
    select.value = obecnaWartosc;
  }
}

function renderujRachunkiBankowe(rachunki) {
  stan.rachunkiBankowe = rachunki;
  document.getElementById("billing-bank-account-count").textContent = `${rachunki.length} rachunkow`;
  zbudujOpcjeRachunkowBankowych();
  odswiezStanModuluRozliczen();

  const body = document.getElementById("billing-bank-account-table-body");
  if (!rachunki.length) {
    body.innerHTML = `<tr><td colspan="7">Brak rachunkow bankowych dla wybranego zakresu.</td></tr>`;
    return;
  }

  body.innerHTML = rachunki
    .map(
      (rachunek) => `
        <tr class="clickable" data-billing-bank-account-id="${rachunek.billing_bank_account_id}">
          <td>${rachunek.billing_bank_account_id}</td>
          <td>${formatujNazweOrganizacji(rachunek.organization_name)}</td>
          <td>${formatujWartosc(rachunek.account_name)}</td>
          <td>${formatujWartosc(rachunek.bank_name)}</td>
          <td>${formatujIban(rachunek.iban)}</td>
          <td>${formatujWartosc(rachunek.currency)}</td>
          <td>${rachunek.is_active ? '<span class="status-badge status-success">tak</span>' : '<span class="status-badge status-danger">nie</span>'}</td>
        </tr>
      `
    )
    .join("");

  body.querySelectorAll("[data-billing-bank-account-id]").forEach((row) => {
    row.addEventListener("click", () => {
      const bankAccountId = row.dataset.billingBankAccountId;
      document.getElementById("billing-import-bank-account-id").value = bankAccountId;
    });
  });
}

function renderujTransakcjeRozliczen(transactions) {
  stan.transakcjeRozliczen = transactions;
  document.getElementById("billing-transaction-count").textContent = `${transactions.length} transakcji`;
  const transactionSelect = document.getElementById("billing-match-transaction-id");
  if (transactionSelect) {
    const currentValue = transactionSelect.value;
    transactionSelect.innerHTML =
      `<option value="">Wybierz transakcje</option>` +
      transactions
        .map(
          (transaction) => `
            <option value="${transaction.billing_transaction_id}">
              ${bezpiecznyTekst(formatujDateCzas(transaction.booking_date))} | ${bezpiecznyTekst(transaction.title || transaction.counterparty_name || transaction.reference || transaction.billing_transaction_id)}
            </option>
          `
        )
        .join("");
    if (currentValue && transactions.some((transaction) => String(transaction.billing_transaction_id) === String(currentValue))) {
      transactionSelect.value = currentValue;
    }
  }

  const body = document.getElementById("billing-transaction-table-body");
  if (!transactions.length) {
    body.innerHTML = `<tr><td colspan="9">Brak transakcji z wyciagow dla wybranego zakresu.</td></tr>`;
    renderujKsiegeRozliczen();
    return;
  }

  body.innerHTML = transactions
    .map(
      (transaction) => `
        <tr class="clickable" data-billing-transaction-id="${transaction.billing_transaction_id}">
          <td>${formatujWartosc(transaction.booking_date)}</td>
          <td>${formatujNazweOrganizacji(transaction.organization_name)}</td>
          <td>${formatujWartosc(transaction.account_name)}</td>
          <td>${formatujKwote(transaction.amount, transaction.currency)}</td>
          <td>${formatujKierunekTransakcji(transaction.direction)}</td>
          <td>${formatujWartosc(transaction.counterparty_name)}</td>
          <td>${formatujWartosc(transaction.title)}</td>
          <td>${formatujWartosc(transaction.reference)}</td>
          <td><span class="status-badge ${klasaStatusuDopasowaniaTransakcji(transaction.matched_status)}">${formatujStatusDopasowaniaTransakcji(transaction.matched_status)}</span></td>
        </tr>
      `
    )
    .join("");

  body.querySelectorAll("[data-billing-transaction-id]").forEach((row) => {
    row.addEventListener("click", () => {
      const transactionId = row.dataset.billingTransactionId;
      const select = document.getElementById("billing-match-transaction-id");
      if (select) {
        select.value = transactionId;
      }
      odswiezPomocDopasowaniaPlatnosci({ ustawDomyslnaKwote: true });
      if (stan.aktywnyWidok !== "billing") {
        ustawWidok("billing");
      }
    });
  });
  renderujKsiegeRozliczen();
}

function renderujPodsumowanieImportuRozliczen() {
  const container = document.getElementById("billing-last-import-summary");
  const result = stan.ostatniImportWyciagu;
  if (!result || !result.statement_import) {
    container.className = "empty-state";
    container.innerHTML = "Po imporcie tutaj pojawi sie podsumowanie ostatniego wyciagu.";
    return;
  }

  const statementImport = result.statement_import;
  container.className = "summary-grid";
  container.innerHTML = `
    <div class="summary-item">
      <strong>Plik</strong>
      <div>${formatujWartosc(statementImport.source_file_name)}</div>
    </div>
    <div class="summary-item">
      <strong>Status importu</strong>
      <div>${formatujWartosc(statementImport.status)}</div>
    </div>
    <div class="summary-item">
      <strong>Wiersze w pliku</strong>
      <div>${formatujWartosc(statementImport.row_count)}</div>
    </div>
    <div class="summary-item">
      <strong>Dodane transakcje</strong>
      <div>${formatujWartosc(result.imported_transaction_count)}</div>
    </div>
    <div class="summary-item">
      <strong>Pominiete duplikaty</strong>
      <div>${formatujWartosc(result.skipped_transaction_count)}</div>
    </div>
    <div class="summary-item">
      <strong>Rachunek</strong>
      <div>${formatujWartosc(statementImport.account_name)}</div>
    </div>
  `;
}

function wyczyscWidokRozliczen() {
  stan.rachunkiBankowe = [];
  stan.transakcjeRozliczen = [];
  stan.billingLedgerBalances = [];
  stan.billingLedgerEntries = [];
  stan.billingPaymentMatches = [];
  stan.szkolyRozliczen = [];
  stan.platnicyRozliczen = [];
  stan.uczniowieRozliczen = [];
  stan.modeleRozliczen = [];
  stan.naleznosciRozliczen = [];
  stan.ostatniImportWyciagu = null;
  renderujPulpitRozliczen();
  document.getElementById("billing-bank-account-count").textContent = "0 rachunkow";
  document.getElementById("billing-transaction-count").textContent = "0 transakcji";
  document.getElementById("billing-bank-account-table-body").innerHTML =
    `<tr><td colspan="7">Zaloguj sie, aby zobaczyc rachunki bankowe.</td></tr>`;
  document.getElementById("billing-transaction-table-body").innerHTML =
    `<tr><td colspan="9">Zaloguj sie, aby zobaczyc transakcje z wyciagow.</td></tr>`;
  document.getElementById("billing-bank-account-form").reset();
  document.getElementById("billing-currency").value = "PLN";
  document.getElementById("billing-statement-import-form").reset();
  document.getElementById("billing-student-form")?.reset();
  const studentFamilyOrder = document.getElementById("billing-student-family-order");
  if (studentFamilyOrder) studentFamilyOrder.value = "1";
  odswiezPowiazanieRodzinyWUczniu({ source: "data" });
  document.getElementById("billing-payer-form")?.reset();
  document.getElementById("billing-school-form")?.reset();
  document.getElementById("billing-model-form")?.reset();
  const siblingDiscount = document.getElementById("billing-model-sibling-discount");
  if (siblingDiscount) siblingDiscount.value = "100";
  const largeFamilyDiscount = document.getElementById("billing-model-large-family-discount");
  if (largeFamilyDiscount) largeFamilyDiscount.value = "50";
  const introFreeLessons = document.getElementById("billing-model-intro-free-lessons");
  if (introFreeLessons) introFreeLessons.value = "1";
  document.getElementById("billing-charge-generator-form")?.reset();
  const chargeLessonCount = document.getElementById("billing-charge-lesson-count");
  if (chargeLessonCount) chargeLessonCount.value = "1";
  zbudujOpcjeRachunkowBankowych();
  renderujPodsumowanieImportuRozliczen();
  renderujMapeModuluRozliczen();
  renderujKsiegeRozliczen();
  odswiezStanModuluRozliczen();
}

function renderujUzytkownikow(uzytkownicy) {
  stan.uzytkownicy = uzytkownicy;
  const body = document.getElementById("users-table-body");
  if (!uzytkownicy.length) {
    body.innerHTML = `<tr><td colspan="10">Brak kont uĹĽytkownikĂłw.</td></tr>`;
    return;
  }

  body.innerHTML = uzytkownicy
    .map(
      (uzytkownik) => `
        <tr class="clickable" data-user-id="${uzytkownik.user_id}">
          <td>${uzytkownik.user_id}</td>
          <td>${formatujWartosc(uzytkownik.login)}</td>
          <td>${formatujWartosc(uzytkownik.display_name)}</td>
          <td>${formatujNazweOrganizacji(uzytkownik.organization_name)}</td>
          <td>${formatujWartosc(uzytkownik.telegram_user_id)}</td>
          <td>${uzytkownik.telegram_reminders_enabled ? '<span class="status-badge status-success">tak</span>' : '<span class="status-badge status-normal">nie</span>'}</td>
          <td>${formatujRole(uzytkownik.role)}</td>
          <td>${uzytkownik.can_upload_knowledge ? '<span class="status-badge status-success">tak</span>' : '<span class="status-badge status-normal">nie</span>'}</td>
          <td>${uzytkownik.is_active ? '<span class="status-badge status-success">tak</span>' : '<span class="status-badge status-danger">nie</span>'}</td>
          <td>${formatujDateCzas(uzytkownik.last_login_at)}</td>
          <td>${formatujWartosc(uzytkownik.created_by_login)}</td>
        </tr>
      `
    )
    .join("");

  body.querySelectorAll("[data-user-id]").forEach((row) => {
    row.addEventListener("click", () => {
      const userId = Number(row.dataset.userId);
      const uzytkownik = stan.uzytkownicy.find((item) => Number(item.user_id) === userId);
      if (uzytkownik) {
        wypelnijFormularzUzytkownika(uzytkownik);
      }
    });
  });
}

function wypelnijFormularzUzytkownika(uzytkownik) {
  stan.wybranyUzytkownikId = Number(uzytkownik.user_id);
  document.getElementById("user-form-title").textContent = `Edycja konta: ${uzytkownik.login}`;
  document.getElementById("user-id").value = String(uzytkownik.user_id);
  document.getElementById("user-login").value = uzytkownik.login || "";
  document.getElementById("user-login").disabled = true;
  document.getElementById("user-display-name").value = uzytkownik.display_name || "";
  document.getElementById("user-organization-id").value = uzytkownik.organization_id || "";
  document.getElementById("user-telegram-user-id").value = uzytkownik.telegram_user_id || "";
  document.getElementById("user-telegram-reminders-enabled").checked =
    uzytkownik.telegram_reminders_enabled !== 0;
  document.getElementById("user-role").value = uzytkownik.role || "operator";
  document.getElementById("user-can-upload-knowledge").checked = Boolean(uzytkownik.can_upload_knowledge);
  document.getElementById("user-active").value = uzytkownik.is_active ? "1" : "0";
  document.getElementById("user-password").value = "";
  document.getElementById("user-password").placeholder = "Podaj nowe hasĹ‚o tylko jeĹ›li chcesz je zmieniÄ‡";
  odswiezOpcjeRolUzytkownikow();
}

function wyczyscFormularzUzytkownika() {
  stan.wybranyUzytkownikId = null;
  document.getElementById("user-form-title").textContent = "Nowe konto";
  document.getElementById("user-form").reset();
  document.getElementById("user-id").value = "";
  document.getElementById("user-login").disabled = false;
  document.getElementById("user-organization-id").value = czyGlobalnyAdministrator()
    ? ""
    : String(stan.biezacyUzytkownik?.organization_id || "");
  document.getElementById("user-telegram-user-id").value = "";
  document.getElementById("user-telegram-reminders-enabled").checked = true;
  document.getElementById("user-role").value = "operator";
  document.getElementById("user-can-upload-knowledge").checked = true;
  document.getElementById("user-active").value = "1";
  document.getElementById("user-password").placeholder = "Podaj hasĹ‚o dla nowego konta lub nowe hasĹ‚o przy zmianie";
  odswiezOpcjeRolUzytkownikow();
}

function pobierzPustaKonfiguracjeKomunikacjiOrganizacji() {
  return {
    telegram: { chat_id: "", chat_name: "" },
    slack: { workspace_name: "", channel_id: "", channel_name: "" },
    whatsapp: { phone_number: "", display_name: "" },
  };
}

function pobierzDomyslneUstawieniaKomunikatorowSystemowych() {
  return {
    telegram: {
      provider: "telegram",
      display_name: "Telegram",
      enabled: false,
      outbound_enabled: false,
      mode: "wylaczony",
      bot_token: { configured: false, source: null, masked_value: "" },
      webhook_secret: { configured: false, source: null, masked_value: "" },
      webhook_path: null,
      webhook_url: null,
    },
    slack: {
      provider: "slack",
      display_name: "Slack",
      enabled: false,
      outbound_enabled: false,
      mode: "wylaczony",
      bot_token: { configured: false, source: null, masked_value: "" },
      signing_secret: { configured: false, source: null, masked_value: "" },
      webhook_path: null,
      webhook_url: null,
    },
    whatsapp: {
      provider: "whatsapp",
      display_name: "WhatsApp",
      enabled: false,
      mode: "planowany",
      note: "Konfiguracja live pojawi sie w kolejnym etapie.",
    },
  };
}

function normalizujUstawieniaKomunikatorowSystemowych(snapshot) {
  const defaults = pobierzDomyslneUstawieniaKomunikatorowSystemowych();
  const source = snapshot && typeof snapshot === "object" ? snapshot : {};
  return {
    telegram: {
      ...defaults.telegram,
      ...(source.telegram && typeof source.telegram === "object" ? source.telegram : {}),
      bot_token: {
        ...defaults.telegram.bot_token,
        ...(source.telegram?.bot_token && typeof source.telegram.bot_token === "object" ? source.telegram.bot_token : {}),
      },
      webhook_secret: {
        ...defaults.telegram.webhook_secret,
        ...(source.telegram?.webhook_secret && typeof source.telegram.webhook_secret === "object"
          ? source.telegram.webhook_secret
          : {}),
      },
    },
    slack: {
      ...defaults.slack,
      ...(source.slack && typeof source.slack === "object" ? source.slack : {}),
      bot_token: {
        ...defaults.slack.bot_token,
        ...(source.slack?.bot_token && typeof source.slack.bot_token === "object" ? source.slack.bot_token : {}),
      },
      signing_secret: {
        ...defaults.slack.signing_secret,
        ...(source.slack?.signing_secret && typeof source.slack.signing_secret === "object"
          ? source.slack.signing_secret
          : {}),
      },
    },
    whatsapp: {
      ...defaults.whatsapp,
      ...(source.whatsapp && typeof source.whatsapp === "object" ? source.whatsapp : {}),
    },
  };
}

function normalizujKonfiguracjeKomunikacjiOrganizacji(config) {
  const source = config && typeof config === "object" ? config : {};
  return {
    telegram: {
      chat_id: String(source.telegram?.chat_id || "").trim(),
      chat_name: String(source.telegram?.chat_name || "").trim(),
    },
    slack: {
      workspace_name: String(source.slack?.workspace_name || "").trim(),
      channel_id: String(source.slack?.channel_id || "").trim(),
      channel_name: String(source.slack?.channel_name || "").trim(),
    },
    whatsapp: {
      phone_number: String(source.whatsapp?.phone_number || "").trim(),
      display_name: String(source.whatsapp?.display_name || "").trim(),
    },
  };
}

function pobierzPublicznyAdresAplikacji() {
  const metaAddress = String(stan.meta?.public_base_url || "").trim().replace(/\/+$/, "");
  if (metaAddress) {
    return metaAddress;
  }
  const runtimeAddress = String(window.location?.origin || "").trim().replace(/\/+$/, "");
  return runtimeAddress;
}

function skopiujTekstDoSchowka(text, successMessage, failureMessage = "Nie udalo sie skopiowac wartosci.") {
  const normalizedText = String(text || "").trim();
  if (!normalizedText) {
    pokazPowiadomienie(failureMessage);
    return;
  }
  navigator.clipboard
    .writeText(normalizedText)
    .then(() => {
      pokazPowiadomienie(successMessage);
    })
    .catch(() => {
      pokazPowiadomienie(failureMessage);
    });
}

function pobierzKonfiguracjeKomunikatoraZFormularzaOrganizacji() {
  return normalizujKonfiguracjeKomunikacjiOrganizacji({
    telegram: {
      chat_id: document.getElementById("organization-telegram-chat-id")?.value || "",
      chat_name: document.getElementById("organization-telegram-chat-name")?.value || "",
    },
    slack: {
      workspace_name: document.getElementById("organization-slack-workspace-name")?.value || "",
      channel_id: document.getElementById("organization-slack-channel-id")?.value || "",
      channel_name: document.getElementById("organization-slack-channel-name")?.value || "",
    },
    whatsapp: {
      phone_number: document.getElementById("organization-whatsapp-phone-number")?.value || "",
      display_name: document.getElementById("organization-whatsapp-display-name")?.value || "",
    },
  });
}

function zbudujElementChecklistyKomunikatora(done, text) {
  return `
    <li>
      ${zbudujBadgeStanu(done ? "OK" : "Brak", done ? "status-success" : "status-warning")}
      <span>${bezpiecznyTekst(text)}</span>
    </li>
  `;
}

function renderujSetupKomunikatoraOrganizacji(provider, communicationConfig) {
  const container = document.getElementById("organization-communication-setup");
  if (!container) {
    return;
  }

  const settings = communicationConfig?.[provider] || {};
  const publicBaseUrl = pobierzPublicznyAdresAplikacji();
  const slackWebhookUrl = publicBaseUrl ? `${publicBaseUrl}/api/slack/events` : "";
  let systemBadge = "";
  let organizationBadge = "";
  let overallBadge = "";
  let description = "";
  let helperRows = "";
  let checklist = "";
  let copyActions = "";

  if (provider === "telegram") {
    const systemReady = Boolean(stan.meta?.telegram_enabled);
    const organizationReady = Boolean(settings.chat_id);
    systemBadge = zbudujBadgeStanu(systemReady ? "Bot Telegram gotowy" : "Brak bota Telegram", systemReady ? "status-success" : "status-danger");
    organizationBadge = zbudujBadgeStanu(
      organizationReady ? "Organizacja ma ID czatu" : "Wpisz ID czatu",
      organizationReady ? "status-success" : "status-warning"
    );
    overallBadge = zbudujBadgeStanu(
      systemReady && organizationReady ? "Telegram gotowy" : "Telegram wymaga uzupelnienia",
      systemReady && organizationReady ? "status-success" : "status-warning"
    );
    description =
      "Dla organizacji wpisujesz tylko ID grupy lub czatu. Bot i webhook ustawia sie raz dla calej aplikacji.";
    helperRows = `
      <div class="communication-setup-grid">
        <div class="summary-item"><strong>ID czatu</strong>${formatujWartosc(settings.chat_id)}</div>
        <div class="summary-item"><strong>Nazwa pomocnicza</strong>${formatujWartosc(settings.chat_name)}</div>
      </div>
    `;
    checklist = [
      zbudujElementChecklistyKomunikatora(systemReady, systemReady ? "System ma podlaczonego bota Telegram." : "Brakuje systemowego tokenu bota albo sekretu webhooka."),
      zbudujElementChecklistyKomunikatora(organizationReady, organizationReady ? "Organizacja ma wpisany ID czatu." : "Wpisz ID kanalu lub grupy Telegram."),
      zbudujElementChecklistyKomunikatora(Boolean(settings.chat_name), Boolean(settings.chat_name) ? "Masz zapisana czytelna nazwe kanalu." : "Nazwa kanalu jest opcjonalna, ale pomaga w administracji."),
    ].join("");
  } else if (provider === "slack") {
    const systemReady = Boolean(stan.meta?.slack_enabled);
    const organizationReady = Boolean(settings.channel_id);
    systemBadge = zbudujBadgeStanu(systemReady ? "Slack systemowo gotowy" : "Brak bota Slack", systemReady ? "status-success" : "status-danger");
    organizationBadge = zbudujBadgeStanu(
      organizationReady ? "Organizacja ma kanal Slack" : "Wpisz ID kanalu",
      organizationReady ? "status-success" : "status-warning"
    );
    overallBadge = zbudujBadgeStanu(
      systemReady && organizationReady && Boolean(slackWebhookUrl) ? "Slack gotowy" : "Slack wymaga uzupelnienia",
      systemReady && organizationReady && Boolean(slackWebhookUrl) ? "status-success" : "status-warning"
    );
    description =
      "W aplikacji ustawiasz tylko kanal organizacji. Request URL do Slacka generuje sie automatycznie, a bot i signing secret sa ustawiane raz dla calego systemu.";
    helperRows = `
      <div class="communication-setup-grid">
        <div class="summary-item"><strong>ID kanaĹ‚u</strong>${formatujWartosc(settings.channel_id)}</div>
        <div class="summary-item"><strong>Nazwa kanaĹ‚u</strong>${formatujWartosc(settings.channel_name)}</div>
        <div class="summary-item"><strong>Workspace</strong>${formatujWartosc(settings.workspace_name)}</div>
        <div class="summary-item"><strong>Request URL</strong>${formatujWartosc(slackWebhookUrl || "Brak publicznego adresu aplikacji")}</div>
      </div>
    `;
    checklist = [
      zbudujElementChecklistyKomunikatora(systemReady, systemReady ? "System ma podlaczony bot Slack i signing secret." : "Brakuje systemowego bota Slack albo signing secret."),
      zbudujElementChecklistyKomunikatora(Boolean(publicBaseUrl), Boolean(publicBaseUrl) ? "Aplikacja ma publiczny adres do webhooka." : "Brakuje publicznego adresu aplikacji."),
      zbudujElementChecklistyKomunikatora(organizationReady, organizationReady ? "Organizacja ma wpisany ID kanaĹ‚u Slack." : "Wpisz ID kanaĹ‚u Slack."),
    ].join("");
    if (slackWebhookUrl) {
      copyActions = `
        <div class="communication-copy-row">
          <input type="text" value="${bezpiecznyTekst(slackWebhookUrl)}" readonly />
          <button type="button" class="secondary" data-communication-copy-text="${bezpiecznyTekst(
            slackWebhookUrl
          )}" data-communication-copy-success="Skopiowano adres webhooka Slack.">Skopiuj adres</button>
        </div>
      `;
    }
  } else {
    const organizationReady = Boolean(settings.phone_number);
    systemBadge = zbudujBadgeStanu("Live integracja pozniej", "status-warning");
    organizationBadge = zbudujBadgeStanu(
      organizationReady ? "Konfiguracja zapisana" : "Wpisz numer telefonu",
      organizationReady ? "status-success" : "status-warning"
    );
    overallBadge = zbudujBadgeStanu("WhatsApp zapisuje ustawienia", "status-warning");
    description =
      "Mozesz juz zapisac numer i nazwe dla organizacji, ale sama integracja WhatsApp pozostaje kolejnym etapem wdrozenia.";
    helperRows = `
      <div class="communication-setup-grid">
        <div class="summary-item"><strong>Numer</strong>${formatujWartosc(settings.phone_number)}</div>
        <div class="summary-item"><strong>Nazwa widoczna</strong>${formatujWartosc(settings.display_name)}</div>
      </div>
    `;
    checklist = [
      zbudujElementChecklistyKomunikatora(organizationReady, organizationReady ? "Numer telefonu jest zapisany." : "Wpisz numer telefonu WhatsApp."),
      zbudujElementChecklistyKomunikatora(Boolean(settings.display_name), Boolean(settings.display_name) ? "Masz ustawiona nazwe widoczna." : "Nazwa widoczna jest opcjonalna."),
      zbudujElementChecklistyKomunikatora(false, "Integracja live nie jest jeszcze aktywna w systemie."),
    ].join("");
  }

  container.innerHTML = `
    <div class="communication-setup-header">
      <div>
        <strong>Szybka konfiguracja ${bezpiecznyTekst(provider === "slack" ? "Slacka" : provider === "telegram" ? "Telegrama" : "WhatsAppa")}</strong>
        <div class="subtle-note">${bezpiecznyTekst(description)}</div>
      </div>
      <div class="communication-setup-badges">
        ${overallBadge}
        ${systemBadge}
        ${organizationBadge}
      </div>
    </div>
    ${helperRows}
    ${copyActions}
    <ul class="communication-step-list">${checklist}</ul>
  `;

  container.querySelectorAll("[data-communication-copy-text]").forEach((button) => {
    button.addEventListener("click", () => {
      skopiujTekstDoSchowka(
        button.dataset.communicationCopyText || "",
        button.dataset.communicationCopySuccess || "Skopiowano wartosc."
      );
    });
  });
}

function renderujUstawieniaKomunikatorowSystemowych() {
  const shell = document.getElementById("system-communication-settings-shell");
  const container = document.getElementById("system-communication-settings");
  if (!shell || !container) {
    return;
  }

  if (!czyWlascicielSystemu()) {
    shell.classList.add("hidden");
    container.innerHTML = "";
    return;
  }

  shell.classList.remove("hidden");
  const settings = normalizujUstawieniaKomunikatorowSystemowych(stan.ustawieniaKomunikatorowSystemowych);
  const sourceLabel = (source) => {
    if (source === "panel") {
      return "Zapisane w aplikacji";
    }
    if (source === "env") {
      return "Dziedziczone z serwera";
    }
    return "Brak";
  };
  const telegramWebhookUrl = String(settings.telegram.webhook_url || "").trim();
  const slackWebhookUrl = String(settings.slack.webhook_url || "").trim();

  container.innerHTML = `
    <div class="communication-setup-header">
      <div>
        <strong>Ustawienia komunikatorow systemowych</strong>
        <div class="subtle-note">
          Tutaj wklejasz globalne tokeny i sekrety tylko raz. Organizacje wybieraja juz potem jedynie swoj kanal albo rozmowe.
        </div>
      </div>
      <div class="communication-setup-badges">
        ${zbudujBadgeStanu(settings.telegram.enabled ? "Telegram gotowy" : "Telegram czeka", settings.telegram.enabled ? "status-success" : "status-warning")}
        ${zbudujBadgeStanu(settings.slack.enabled ? "Slack gotowy" : "Slack czeka", settings.slack.enabled ? "status-success" : "status-warning")}
        <button type="button" data-system-communication-action="save">Zapisz ustawienia</button>
      </div>
    </div>
    <div class="system-communication-grid">
      <section class="system-communication-card">
        <div class="communication-setup-header">
          <div>
            <h4>Telegram</h4>
            <p class="subtle-note">Wklej token bota i sekret webhooka. Puste pola nie nadpisza niczego, co juz jest zapisane.</p>
          </div>
          <div class="communication-setup-badges">
            ${zbudujBadgeStanu(settings.telegram.mode, settings.telegram.enabled ? "status-success" : settings.telegram.outbound_enabled ? "status-warning" : "status-normal")}
          </div>
        </div>
        <div class="system-communication-field-list">
          <label>
            <span>Token bota</span>
            <input id="system-telegram-bot-token" type="password" placeholder="Wklej tylko jesli chcesz ustawic lub zmienic token" autocomplete="off" />
            <span class="system-communication-value">${bezpiecznyTekst(settings.telegram.bot_token.masked_value || "Brak zapisanego tokenu")} / ${bezpiecznyTekst(sourceLabel(settings.telegram.bot_token.source))}</span>
          </label>
          <label>
            <span>Sekret webhooka</span>
            <input id="system-telegram-webhook-secret" type="password" placeholder="Wklej tylko jesli chcesz ustawic lub zmienic sekret" autocomplete="off" />
            <span class="system-communication-value">${bezpiecznyTekst(settings.telegram.webhook_secret.masked_value || "Brak zapisanego sekretu")} / ${bezpiecznyTekst(sourceLabel(settings.telegram.webhook_secret.source))}</span>
          </label>
        </div>
        ${
          telegramWebhookUrl
            ? `<div class="communication-copy-row">
                <input type="text" value="${bezpiecznyTekst(telegramWebhookUrl)}" readonly />
                <button type="button" class="secondary" data-communication-copy-text="${bezpiecznyTekst(telegramWebhookUrl)}" data-communication-copy-success="Skopiowano adres webhooka Telegram.">Skopiuj webhook</button>
              </div>`
            : `<div class="subtle-note">Webhook Telegram pojawi sie od razu po zapisaniu sekretu.</div>`
        }
        <div class="system-communication-actions">
          <button type="button" class="secondary" data-system-communication-action="clear-provider" data-provider="telegram">Wyczysc Telegram</button>
        </div>
      </section>
      <section class="system-communication-card">
        <div class="communication-setup-header">
          <div>
            <h4>Slack</h4>
            <p class="subtle-note">Wklej token bota i signing secret. Organizacje beda juz tylko wpisywac konkretny kanal.</p>
          </div>
          <div class="communication-setup-badges">
            ${zbudujBadgeStanu(settings.slack.mode, settings.slack.enabled ? "status-success" : settings.slack.outbound_enabled ? "status-warning" : "status-normal")}
          </div>
        </div>
        <div class="system-communication-field-list">
          <label>
            <span>Token bota</span>
            <input id="system-slack-bot-token" type="password" placeholder="Wklej tylko jesli chcesz ustawic lub zmienic token" autocomplete="off" />
            <span class="system-communication-value">${bezpiecznyTekst(settings.slack.bot_token.masked_value || "Brak zapisanego tokenu")} / ${bezpiecznyTekst(sourceLabel(settings.slack.bot_token.source))}</span>
          </label>
          <label>
            <span>Signing secret</span>
            <input id="system-slack-signing-secret" type="password" placeholder="Wklej tylko jesli chcesz ustawic lub zmienic sekret" autocomplete="off" />
            <span class="system-communication-value">${bezpiecznyTekst(settings.slack.signing_secret.masked_value || "Brak zapisanego sekretu")} / ${bezpiecznyTekst(sourceLabel(settings.slack.signing_secret.source))}</span>
          </label>
        </div>
        ${
          slackWebhookUrl
            ? `<div class="communication-copy-row">
                <input type="text" value="${bezpiecznyTekst(slackWebhookUrl)}" readonly />
                <button type="button" class="secondary" data-communication-copy-text="${bezpiecznyTekst(slackWebhookUrl)}" data-communication-copy-success="Skopiowano adres webhooka Slack.">Skopiuj webhook</button>
              </div>`
            : `<div class="subtle-note">Webhook Slack pojawi sie od razu po zapisaniu signing secret.</div>`
        }
        <div class="system-communication-actions">
          <button type="button" class="secondary" data-system-communication-action="clear-provider" data-provider="slack">Wyczysc Slack</button>
        </div>
      </section>
    </div>
    <div class="system-communication-card">
      <div class="communication-setup-header">
        <div>
          <strong>WhatsApp</strong>
          <div class="subtle-note">${bezpiecznyTekst(settings.whatsapp.note || "Ta integracja pojawi sie pozniej.")}</div>
        </div>
        <div class="communication-setup-badges">
          ${zbudujBadgeStanu(settings.whatsapp.mode || "planowany", "status-normal")}
        </div>
      </div>
      <div class="subtle-note">Po stronie organizacji mozna juz wybrac WhatsApp jako kanal docelowy, ale bez systemowego tokenu nic nie trzeba tu jeszcze wpisywac.</div>
    </div>
  `;

  container.querySelectorAll("[data-communication-copy-text]").forEach((button) => {
    button.addEventListener("click", () => {
      skopiujTekstDoSchowka(
        button.dataset.communicationCopyText || "",
        button.dataset.communicationCopySuccess || "Skopiowano wartosc."
      );
    });
  });
}

function pobierzPayloadUstawienKomunikatorowSystemowychZFormularza() {
  return {
    telegram: {
      bot_token: document.getElementById("system-telegram-bot-token")?.value || "",
      webhook_secret: document.getElementById("system-telegram-webhook-secret")?.value || "",
    },
    slack: {
      bot_token: document.getElementById("system-slack-bot-token")?.value || "",
      signing_secret: document.getElementById("system-slack-signing-secret")?.value || "",
    },
  };
}

async function wczytajUstawieniaKomunikatorowSystemowych() {
  if (!czyWlascicielSystemu()) {
    stan.ustawieniaKomunikatorowSystemowych = null;
    renderujUstawieniaKomunikatorowSystemowych();
    return;
  }
  stan.ustawieniaKomunikatorowSystemowych = normalizujUstawieniaKomunikatorowSystemowych(
    await api("/api/system/communication-settings")
  );
  renderujUstawieniaKomunikatorowSystemowych();
}

async function zapiszUstawieniaKomunikatorowSystemowych() {
  const payload = pobierzPayloadUstawienKomunikatorowSystemowychZFormularza();
  const hasAnyValue =
    Object.values(payload.telegram).some((value) => String(value || "").trim()) ||
    Object.values(payload.slack).some((value) => String(value || "").trim());
  if (!hasAnyValue) {
    pokazPowiadomienie("Wpisz nowy token lub sekret albo uzyj przycisku wyczysc.");
    return;
  }
  stan.ustawieniaKomunikatorowSystemowych = normalizujUstawieniaKomunikatorowSystemowych(
    await api("/api/system/communication-settings", {
      method: "PATCH",
      body: JSON.stringify(payload),
    })
  );
  await wczytajMeta();
  renderujUstawieniaKomunikatorowSystemowych();
  renderujPolaKomunikatoraOrganizacji();
  pokazPowiadomienie("Zapisano ustawienia komunikatorow systemowych.");
}

async function wyczyscUstawieniaKomunikatoraSystemowego(provider) {
  const normalizedProvider = String(provider || "").trim().toLowerCase();
  if (!["telegram", "slack"].includes(normalizedProvider)) {
    return;
  }
  stan.ustawieniaKomunikatorowSystemowych = normalizujUstawieniaKomunikatorowSystemowych(
    await api("/api/system/communication-settings", {
      method: "PATCH",
      body: JSON.stringify({
        [normalizedProvider]: {
          clear: true,
        },
      }),
    })
  );
  await wczytajMeta();
  renderujUstawieniaKomunikatorowSystemowych();
  renderujPolaKomunikatoraOrganizacji();
  pokazPowiadomienie(
    `${normalizedProvider === "telegram" ? "Telegram" : "Slack"} wyczyszczono z ustawien aplikacji.`
  );
}

function renderujPolaKomunikatoraOrganizacji() {
  const providerSelect = document.getElementById("organization-communication-provider");
  const provider = String(providerSelect?.value || "telegram").trim().toLowerCase() || "telegram";
  const communicationConfig = pobierzKonfiguracjeKomunikatoraZFormularzaOrganizacji();
  document.querySelectorAll("[data-organization-communication-section]").forEach((section) => {
    section.classList.toggle("hidden", section.dataset.organizationCommunicationSection !== provider);
  });
  const summary = document.getElementById("organization-communication-provider-summary");
  if (summary) {
    const labels = {
      telegram: "Telegram: kanaĹ‚ lub grupa, z ktĂłrej organizacja odbiera dokumenty.",
      slack: "Slack: workspace i kanaĹ‚, z ktĂłrego organizacja odbiera dokumenty.",
      whatsapp: "WhatsApp: numer i nazwa rozmowy biznesowej do przyszĹ‚ej integracji.",
    };
    summary.textContent = labels[provider] || labels.telegram;
  }
  const note = document.getElementById("organization-communication-note");
  if (note) {
    note.textContent =
      provider === "whatsapp"
        ? "WhatsApp pozostaje gotowÄ… konfiguracjÄ… do przyszĹ‚ej integracji. Telegram i Slack obsĹ‚ugujÄ… juĹĽ import dokumentĂłw."
        : `${provider === "slack" ? "Slack" : "Telegram"} jest aktywnym komunikatorem tej organizacji i obsĹ‚uguje juĹĽ obecny import dokumentĂłw.`;
  }
  renderujSetupKomunikatoraOrganizacji(provider, communicationConfig);
}

function renderujOrganizacje(organizacje) {
  stan.organizacje = organizacje;
  zbudujOpcjeOrganizacjiDlaFormularzy();
  const body = document.getElementById("organization-table-body");
  if (!organizacje.length) {
    body.innerHTML = `<tr><td colspan="15">Brak organizacji.</td></tr>`;
    return;
  }

  body.innerHTML = organizacje
    .map(
      (organizacja) => {
        const stanEmaila = pobierzStanEmailaOrganizacji(organizacja);
        const stanKsef = pobierzStanKsefOrganizacji(organizacja);
        return `
          <tr class="clickable" data-organization-id="${organizacja.organization_id}">
            <td>${organizacja.organization_id}</td>
            <td>${formatujWartosc(organizacja.name)}</td>
            <td>${formatujWartosc(organizacja.slug)}</td>
            <td>${formatujWartosc(organizacja.email_inbox_address)}</td>
            <td>${zbudujBadgeStanu(stanEmaila.label, stanEmaila.className)}</td>
            <td>${formatujDateCzas(organizacja.email_last_checked_at)}</td>
            <td>${formatujWartosc(organizacja.ksef_company_identifier)}</td>
            <td>${zbudujBadgeStanu(stanKsef.label, stanKsef.className)}</td>
            <td>${formatujDateCzas(organizacja.ksef_last_checked_at)}</td>
            <td>${formatujWartosc(organizacja.communication_provider_label || organizacja.communication_provider)}</td>
            <td>${formatujWartosc(organizacja.communication_target_summary)}</td>
            <td>${organizacja.is_active ? zbudujBadgeStanu("tak", "status-success") : zbudujBadgeStanu("nie", "status-danger")}</td>
            <td>${formatujWartosc(organizacja.user_count)}</td>
            <td>${formatujWartosc(organizacja.invoice_count)}</td>
            <td>${formatujWartosc(organizacja.contractor_count)}</td>
        </tr>
      `;
      }
    )
    .join("");

  body.querySelectorAll("[data-organization-id]").forEach((row) => {
    row.addEventListener("click", () => {
      const organizationId = Number(row.dataset.organizationId);
      const organizacja = stan.organizacje.find((item) => Number(item.organization_id) === organizationId);
      if (organizacja) {
        wypelnijFormularzOrganizacji(organizacja);
      }
    });
  });

  if (
    !stan.wybranaOrganizacjaFormularzaId ||
    !organizacje.some((item) => Number(item.organization_id) === Number(stan.wybranaOrganizacjaFormularzaId))
  ) {
    wyczyscFormularzOrganizacji();
  }
}

function wypelnijFormularzOrganizacji(organizacja) {
  const communicationConfig = normalizujKonfiguracjeKomunikacjiOrganizacji(organizacja.communication_config);
  stan.wybranaOrganizacjaFormularzaId = Number(organizacja.organization_id);
  document.getElementById("organization-form-title").textContent = `Edycja organizacji: ${organizacja.name}`;
  document.getElementById("organization-id").value = String(organizacja.organization_id);
  document.getElementById("organization-name").value = organizacja.name || "";
  document.getElementById("organization-slug").value = organizacja.slug || "";
  document.getElementById("organization-communication-provider").value = organizacja.communication_provider || "telegram";
  document.getElementById("organization-telegram-chat-id").value = communicationConfig.telegram.chat_id;
  document.getElementById("organization-telegram-chat-name").value = communicationConfig.telegram.chat_name;
  document.getElementById("organization-slack-workspace-name").value = communicationConfig.slack.workspace_name;
  document.getElementById("organization-slack-channel-id").value = communicationConfig.slack.channel_id;
  document.getElementById("organization-slack-channel-name").value = communicationConfig.slack.channel_name;
  document.getElementById("organization-whatsapp-phone-number").value = communicationConfig.whatsapp.phone_number;
  document.getElementById("organization-whatsapp-display-name").value = communicationConfig.whatsapp.display_name;
  document.getElementById("organization-email-inbox-address").value = organizacja.email_inbox_address || "";
  document.getElementById("organization-email-allowed-sender").value = organizacja.email_allowed_sender || "";
  document.getElementById("organization-email-subject-keyword").value = organizacja.email_subject_keyword || "";
  document.getElementById("organization-email-integration-enabled").value =
    Number(organizacja.email_integration_enabled || 0) === 1 ? "1" : "0";
  document.getElementById("organization-ksef-company-identifier").value = organizacja.ksef_company_identifier || "";
  document.getElementById("organization-ksef-environment").value = organizacja.ksef_environment || "demo";
  document.getElementById("organization-ksef-integration-enabled").value =
    Number(organizacja.ksef_integration_enabled || 0) === 1 ? "1" : "0";
  renderujPolaSkrotowModulowOrganizacji(organizacja.module_shortcuts || {});
  odswiezPoleDelegataKsef(
    organizacja.organization_id,
    organizacja.ksef_correction_delegate_user_id || "",
    organizacja.ksef_correction_delegate_expires_at || ""
  );
  document.getElementById("organization-active").value = organizacja.is_active ? "1" : "0";
  document.getElementById("organization-module-manager-assistant").checked = Array.isArray(organizacja.enabled_modules)
    ? organizacja.enabled_modules.includes(organizationModuleCodes.managerAssistant)
    : false;
  renderujPodsumowanieEmailaOrganizacji(organizacja);
  renderujPodsumowanieKsefOrganizacji(organizacja);
  wczytajHistorieImportowEmailaOrganizacji(organizacja.organization_id).catch((error) => {
    renderujHistorieImportowEmailaOrganizacji([], organizacja.organization_id);
    console.error("Nie udalo sie pobrac historii importow e-mail:", error);
  });
  wczytajHistorieImportowKsefOrganizacji(organizacja.organization_id).catch((error) => {
    renderujHistorieImportowKsefOrganizacji([], organizacja.organization_id);
    console.error("Nie udalo sie pobrac historii importow KSeF:", error);
  });
  renderujPolaKomunikatoraOrganizacji();
  odswiezUprawnieniaFormularzaOrganizacji();
}

function wyczyscFormularzOrganizacji() {
  stan.wybranaOrganizacjaFormularzaId = null;
  const formularz = document.getElementById("organization-form");
  const aktywnaOrganizacja =
    stan.organizacje.find((item) => Number(item.organization_id) === Number(stan.biezacyUzytkownik?.organization_id)) || null;
  if (!czyMoznaTworzycOrganizacje() && aktywnaOrganizacja) {
    wypelnijFormularzOrganizacji(aktywnaOrganizacja);
    document.getElementById("organization-form-title").textContent = `Ustawienia organizacji: ${aktywnaOrganizacja.name}`;
    return;
  }

  document.getElementById("organization-form-title").textContent = "Nowa organizacja";
  formularz.reset();
  document.getElementById("organization-id").value = "";
  document.getElementById("organization-communication-provider").value = "telegram";
  document.getElementById("organization-telegram-chat-id").value = "";
  document.getElementById("organization-telegram-chat-name").value = "";
  document.getElementById("organization-slack-workspace-name").value = "";
  document.getElementById("organization-slack-channel-id").value = "";
  document.getElementById("organization-slack-channel-name").value = "";
  document.getElementById("organization-whatsapp-phone-number").value = "";
  document.getElementById("organization-whatsapp-display-name").value = "";
  document.getElementById("organization-email-inbox-address").value = "";
  document.getElementById("organization-email-allowed-sender").value = "";
  document.getElementById("organization-email-subject-keyword").value = "";
  document.getElementById("organization-email-integration-enabled").value = "0";
  document.getElementById("organization-ksef-company-identifier").value = "";
  document.getElementById("organization-ksef-environment").value = "demo";
  document.getElementById("organization-ksef-integration-enabled").value = "0";
  renderujPolaSkrotowModulowOrganizacji({});
  odswiezPoleDelegataKsef(stan.biezacyUzytkownik?.organization_id || "", "", "");
  document.getElementById("organization-active").value = "1";
  document.getElementById("organization-module-manager-assistant").checked = false;
  renderujPodsumowanieEmailaOrganizacji(null);
  renderujHistorieImportowEmailaOrganizacji([], null);
  renderujPodsumowanieKsefOrganizacji(null);
  renderujHistorieImportowKsefOrganizacji([], null);
  renderujPolaKomunikatoraOrganizacji();
  odswiezUprawnieniaFormularzaOrganizacji();
}

function odswiezUprawnieniaFormularzaOrganizacji() {
  const pola = document.querySelectorAll("#organization-form input, #organization-form select, #organization-form button");
  const mozeEdytowac = czyMoznaZarzadzacOrganizacjami();
  const mozeTworzyc = czyMoznaTworzycOrganizacje();
  const isExisting = Boolean(document.getElementById("organization-id").value);

  pola.forEach((element) => {
    element.disabled = !mozeEdytowac;
  });

  const poleAktywnosci = document.getElementById("organization-active");
  const poleModuluAsystenta = document.getElementById("organization-module-manager-assistant");
  const notaModulow = document.getElementById("organization-modules-note");
  const przyciskWyczysc = document.getElementById("reset-organization-form");
  const przyciskTestuEmail = document.getElementById("organization-test-email-connection");
  const przyciskSprawdzEmail = document.getElementById("organization-check-email");
  const przyciskTestuKsef = document.getElementById("organization-test-ksef-connection");
  const przyciskSprawdzKsef = document.getElementById("organization-check-ksef");
  if (poleAktywnosci) {
    poleAktywnosci.disabled = !mozeTworzyc;
    poleAktywnosci.title = mozeTworzyc ? "" : "Tylko WĹ‚aĹ›ciciel systemu moĹĽe aktywowaÄ‡ albo dezaktywowaÄ‡ organizacjÄ™.";
  }
  if (poleModuluAsystenta) {
    poleModuluAsystenta.disabled = !czyWlascicielSystemu();
  }
  if (notaModulow) {
    notaModulow.textContent = czyWlascicielSystemu()
      ? "Po wlaczeniu wlasciciel organizacji dostaje pelny Asystent Szefa, a pracownicy sekcje Moja praca."
      : "Status pakietu jest widoczny, ale tylko Wlasciciel systemu moze go zmieniac.";
  }
  if (przyciskWyczysc) {
    przyciskWyczysc.disabled = !mozeTworzyc && isExisting;
    przyciskWyczysc.title = !mozeTworzyc && isExisting ? "Administrator organizacji edytuje tylko swojÄ… organizacjÄ™." : "";
  }
  const emailInboxAddress = document.getElementById("organization-email-inbox-address").value.trim();
  const emailEnabled = document.getElementById("organization-email-integration-enabled").value === "1";
  const ksefIdentifier = document.getElementById("organization-ksef-company-identifier").value.trim();
  const ksefEnabled = document.getElementById("organization-ksef-integration-enabled").value === "1";
  const organizationActive = document.getElementById("organization-active").value === "1";
  const systemEmailReady = Boolean(stan.meta?.email_enabled);
  const systemKsefReady = Boolean(stan.meta?.ksef_enabled);

  if (przyciskTestuEmail) {
    przyciskTestuEmail.disabled = !mozeEdytowac || !isExisting || !emailInboxAddress || !systemEmailReady;

    if (!isExisting) {
      przyciskTestuEmail.title = "Najpierw zapisz organizacje.";
    } else if (!emailInboxAddress) {
      przyciskTestuEmail.title = "Uzupelnij skrzynke e-mail organizacji.";
    } else if (!systemEmailReady) {
      przyciskTestuEmail.title = "Najpierw skonfiguruj globalne IMAP w .env.local albo data/local.env.";
    } else {
      przyciskTestuEmail.title = "";
    }
  }

  if (przyciskSprawdzEmail) {
    przyciskSprawdzEmail.disabled =
      !mozeEdytowac || !isExisting || !emailInboxAddress || !emailEnabled || !organizationActive || !systemEmailReady;

    if (!isExisting) {
      przyciskSprawdzEmail.title = "Najpierw zapisz organizacje.";
    } else if (!emailInboxAddress) {
      przyciskSprawdzEmail.title = "Uzupelnij skrzynke e-mail organizacji.";
    } else if (!emailEnabled) {
      przyciskSprawdzEmail.title = "Wlacz integracje e-mail dla tej organizacji.";
    } else if (!organizationActive) {
      przyciskSprawdzEmail.title = "Nie mozna sprawdzac e-maila dla nieaktywnej organizacji.";
    } else if (!systemEmailReady) {
      przyciskSprawdzEmail.title = "Najpierw skonfiguruj globalne IMAP w .env.local albo data/local.env.";
    } else {
      przyciskSprawdzEmail.title = "";
    }
  }

  if (przyciskTestuKsef) {
    przyciskTestuKsef.disabled = !mozeEdytowac || !isExisting || !ksefIdentifier || !systemKsefReady;

    if (!isExisting) {
      przyciskTestuKsef.title = "Najpierw zapisz organizacje.";
    } else if (!ksefIdentifier) {
      przyciskTestuKsef.title = "Uzupelnij identyfikator firmy w KSeF.";
    } else if (!systemKsefReady) {
      przyciskTestuKsef.title = "Najpierw przygotuj systemowy adapter KSeF.";
    } else {
      przyciskTestuKsef.title = "";
    }
  }

  if (przyciskSprawdzKsef) {
    przyciskSprawdzKsef.disabled =
      !mozeEdytowac || !isExisting || !ksefIdentifier || !ksefEnabled || !organizationActive || !systemKsefReady;

    if (!isExisting) {
      przyciskSprawdzKsef.title = "Najpierw zapisz organizacje.";
    } else if (!ksefIdentifier) {
      przyciskSprawdzKsef.title = "Uzupelnij identyfikator firmy w KSeF.";
    } else if (!ksefEnabled) {
      przyciskSprawdzKsef.title = "Wlacz integracje KSeF dla tej organizacji.";
    } else if (!organizationActive) {
      przyciskSprawdzKsef.title = "Nie mozna sprawdzac KSeF dla nieaktywnej organizacji.";
    } else if (!systemKsefReady) {
      przyciskSprawdzKsef.title = "Najpierw przygotuj systemowy adapter KSeF.";
    } else {
      przyciskSprawdzKsef.title = "";
    }
  }
}

function renderujLogi(logs) {
  stan.logi = logs;
  const body = document.getElementById("log-table-body");
  if (!logs.length) {
    body.innerHTML = `<tr><td colspan="9">Brak logĂłw.</td></tr>`;
    return;
  }

  body.innerHTML = logs
    .map(
      (log) => {
        const opisKontekstu = zbudujOpisKontekstuZdarzenia(log);
        return `
        <tr data-log-id="${log.id}">
          <td>${formatujDateCzas(log.event_time)}</td>
          <td>${formatujNazweOrganizacji(log.organization_name)}</td>
          <td>${formatujTypZdarzenia(log.event_type)}</td>
          <td>${opisKontekstu || "Zdarzenie ogĂłlne"}</td>
          <td>${formatujWartosc(log.status_before)}</td>
          <td>${formatujWartosc(log.status_after)}</td>
          <td>${formatujWartosc(log.decision_reason)}</td>
          <td>${formatujWartosc(log.actor)}</td>
          <td><div class="code-block">${bezpiecznyTekst(log.details || "")}</div></td>
        </tr>
      `;
      }
    )
    .join("");
}

function renderujWynikiWyszukiwania(results) {
  const container = document.getElementById("global-search-results");
  if (!results.invoices.length && !results.contractors.length) {
    container.classList.add("hidden");
    container.innerHTML = "";
    return;
  }

  container.classList.remove("hidden");
  container.innerHTML = `
    <div class="detail-columns">
      <div>
        <h3>Faktury</h3>
        <div class="list">
          ${
            results.invoices.length
              ? results.invoices
                  .map(
                    (invoice) => `
                      <article class="list-item">
                        <strong>#${invoice.id}</strong> ${formatujWartosc(invoice.invoice_number)}
                        <div>${formatujNazweOrganizacji(invoice.organization_name)}</div>
                        <div>${formatujWartosc(invoice.issuer_name)} | ${formatujWartosc(invoice.issuer_nip)}</div>
                        <div>${formatujZrodlo(invoice.source)} | ${formatujWartosc(invoice.status)}</div>
                        <button class="ghost quick-open-invoice" data-id="${invoice.id}">OtwĂłrz fakturÄ™</button>
                      </article>
                    `
                  )
                  .join("")
              : `<div class="empty-state">Brak wynikĂłw.</div>`
          }
        </div>
      </div>
      <div>
        <h3>Kontrahenci</h3>
        <div class="list">
          ${
            results.contractors.length
              ? results.contractors
                  .map(
                    (contractor) => `
                      <article class="list-item">
                        <strong>#${contractor.contractor_id}</strong> ${formatujWartosc(contractor.name)}
                        <div>${formatujNazweOrganizacji(contractor.organization_name)}</div>
                        <div>${formatujWartosc(contractor.nip)} | ${formatujWartosc(contractor.email)}</div>
                        <button class="ghost quick-open-contractor" data-id="${contractor.contractor_id}">OtwĂłrz kontrahenta</button>
                      </article>
                    `
                  )
                  .join("")
              : `<div class="empty-state">Brak wynikĂłw.</div>`
          }
        </div>
      </div>
    </div>
  `;

  container.querySelectorAll(".quick-open-invoice").forEach((button) => {
    button.addEventListener("click", () => {
      ustawWidok("invoices");
      wczytajSzczegolyFaktury(Number(button.dataset.id)).catch((error) => pokazPowiadomienie(error.message));
    });
  });

  container.querySelectorAll(".quick-open-contractor").forEach((button) => {
    button.addEventListener("click", () => {
      ustawWidok("contractors");
      wczytajSzczegolyKontrahenta(Number(button.dataset.id)).catch((error) => pokazPowiadomienie(error.message));
    });
  });
}

function czyModulWiedzyMaZakres() {
  return Boolean(stan.biezacyUzytkownik) && (!czyGlobalnyAdministrator() || Boolean(stan.wybranaOrganizacjaId));
}

function odswiezStanBazyWiedzy() {
  const przyciskZapisu = document.getElementById("knowledge-save-button");
  const przyciskSynchronizacji = document.getElementById("knowledge-sync-button");
  const komunikat = document.getElementById("knowledge-access-note");
  const poleTytulu = document.getElementById("knowledge-title");
  const polePliku = document.getElementById("knowledge-file");
  const poleTresci = document.getElementById("knowledge-content");
  const polePytania = document.getElementById("knowledge-question");
  const przyciskPytania = document.querySelector('#knowledge-question-form button[type="submit"]');
  if (!przyciskZapisu || !przyciskSynchronizacji || !komunikat) {
    return;
  }

  if (!stan.biezacyUzytkownik) {
    przyciskZapisu.disabled = true;
    przyciskSynchronizacji.disabled = true;
    [poleTytulu, polePliku, poleTresci, polePytania, przyciskPytania].forEach((element) => {
      if (element) {
        element.disabled = true;
      }
    });
    komunikat.textContent = "Zaloguj siÄ™, aby korzystaÄ‡ z bazy wiedzy.";
    return;
  }

  const brakWyboruOrganizacji = czyGlobalnyAdministrator() && !stan.wybranaOrganizacjaId;
  const brakUprawnieniaDoDodawania = !czyMoznaDodawacPlikiDoBazyWiedzy();
  const moznaImportowac = !brakWyboruOrganizacji && !brakUprawnieniaDoDodawania;
  const moznaZadawacPytania = czyModulWiedzyMaZakres();
  przyciskZapisu.disabled = brakWyboruOrganizacji || brakUprawnieniaDoDodawania;
  przyciskSynchronizacji.disabled = brakWyboruOrganizacji || brakUprawnieniaDoDodawania;
  [poleTytulu, polePliku, poleTresci].forEach((element) => {
    if (element) {
      element.disabled = !moznaImportowac;
    }
  });
  [polePytania, przyciskPytania].forEach((element) => {
    if (element) {
      element.disabled = !moznaZadawacPytania;
    }
  });

  if (brakWyboruOrganizacji) {
    komunikat.textContent = "Wybierz konkretnÄ… organizacjÄ™, aby pracowaÄ‡ na jej bazie wiedzy.";
  } else if (brakUprawnieniaDoDodawania) {
    komunikat.textContent = "MoĹĽesz zadawaÄ‡ pytania, ale dodawanie dokumentĂłw wymaga wĹ‚Ä…czenia tego uprawnienia na koncie uĹĽytkownika.";
  } else {
    komunikat.textContent = "MoĹĽesz dodawaÄ‡ dokumenty, synchronizowaÄ‡ folder i zadawaÄ‡ pytania do bazy wiedzy.";
  }
  odswiezPanelImportuBazyWiedzy();
}

function wyczyscBazeWiedzy() {
  stan.dokumentyWiedzy = [];
  stan.odpowiedzBazyWiedzy = null;
  stan.folderBazyWiedzy = "";
  stan.konfiguracjaBazyWiedzy = null;
  stan.ostatniImportBazyWiedzy = null;
  document.getElementById("knowledge-count").textContent = "";
  document.getElementById("knowledge-folder-path").textContent = "-";
  document.getElementById("knowledge-documents").innerHTML =
    `<div class="empty-state">Brak dokumentĂłw w bazie wiedzy.</div>`;
  document.getElementById("knowledge-answer-empty").classList.remove("hidden");
  document.getElementById("knowledge-answer").classList.add("hidden");
  document.getElementById("knowledge-answer").innerHTML = "";
  document.getElementById("knowledge-title").value = "";
  document.getElementById("knowledge-file").value = "";
  document.getElementById("knowledge-content").value = "";
  document.getElementById("knowledge-question").value = "";
  odswiezPanelImportuBazyWiedzy();
  odswiezStanBazyWiedzy();
}

function renderujBazeWiedzy(payload) {
  if (
    stan.ostatniImportBazyWiedzy &&
    Number(stan.ostatniImportBazyWiedzy.organization_id || 0) !== Number(payload.organization_id || 0)
  ) {
    stan.ostatniImportBazyWiedzy = null;
  }
  stan.dokumentyWiedzy = payload.documents || [];
  stan.folderBazyWiedzy = payload.folder_path || "";
  stan.konfiguracjaBazyWiedzy = {
    organization_id: payload.organization_id,
    supported_formats: payload.supported_formats || [],
    ocr_enabled: Boolean(payload.ocr_enabled),
    ocr_mode: payload.ocr_mode || "fallback",
  };
  stan.odpowiedzBazyWiedzy = null;
  document.getElementById("knowledge-count").textContent = `${stan.dokumentyWiedzy.length} dokumentow`;
  document.getElementById("knowledge-folder-path").textContent = stan.folderBazyWiedzy || "-";
  document.getElementById("knowledge-answer-empty").classList.remove("hidden");
  document.getElementById("knowledge-answer").classList.add("hidden");
  document.getElementById("knowledge-answer").innerHTML = "";

  const container = document.getElementById("knowledge-documents");
  if (!stan.dokumentyWiedzy.length) {
    container.innerHTML = `<div class="empty-state">Ta organizacja nie ma jeszcze ĹĽadnych dokumentĂłw wiedzy.</div>`;
    odswiezStanBazyWiedzy();
    return;
  }

  container.innerHTML = stan.dokumentyWiedzy
    .map((dokument) => {
      const sourceType = dokument.source_type || "manual";
      const extension = String(dokument.file_name || "").includes(".")
        ? String(dokument.file_name).split(".").pop().toUpperCase()
        : "";
      const createdBy = dokument.created_by_display_name || dokument.created_by_login;
      const fileLink = dokument.file_link
        ? `<a href="${bezpiecznyTekst(dokument.file_link)}" target="_blank" rel="noreferrer">Otworz plik</a>`
        : "";
      return `
        <article class="list-item">
          <div class="knowledge-doc-header">
            <div class="knowledge-doc-title">${bezpiecznyTekst(dokument.title)}</div>
            <div class="knowledge-doc-badges">
              <span class="status-badge ${klasaStatusuZrodlaBazyWiedzy(sourceType)}">${bezpiecznyTekst(
                formatujZrodloBazyWiedzy(sourceType)
              )}</span>
              ${extension ? `<span class="pill knowledge-doc-pill">${bezpiecznyTekst(extension)}</span>` : ""}
            </div>
          </div>
          <div>${bezpiecznyTekst(dokument.snippet || "Brak podglÄ…du treĹ›ci.")}</div>
          <div class="knowledge-doc-meta">
            <span>Plik: ${bezpiecznyTekst(dokument.file_name)}</span>
            <span>Znaki: ${bezpiecznyTekst(dokument.char_count)}</span>
            <span>Aktualizacja: ${formatujDateCzas(dokument.updated_at)}</span>
            ${createdBy ? `<span>Dodane przez: ${bezpiecznyTekst(createdBy)}</span>` : ""}
            <a href="${bezpiecznyTekst(dokument.file_link)}" target="_blank" rel="noreferrer">OtwĂłrz plik</a>
          </div>
        </article>
      `;
    })
    .join("");
  odswiezStanBazyWiedzy();
}

function renderujOdpowiedzBazyWiedzy(wynik) {
  stan.odpowiedzBazyWiedzy = wynik;
  const emptyState = document.getElementById("knowledge-answer-empty");
  const container = document.getElementById("knowledge-answer");
  emptyState.classList.add("hidden");
  container.classList.remove("hidden");

  const zrodla = (wynik.matches || [])
    .map(
      (match) => `
        <article class="knowledge-source-item">
          <div class="knowledge-doc-header">
            <strong>${bezpiecznyTekst(match.title)}</strong>
            <span class="status-badge ${klasaStatusuZrodlaBazyWiedzy(match.source_type || "manual")}">${bezpiecznyTekst(
              formatujZrodloBazyWiedzy(match.source_type || "manual")
            )}</span>
          </div>
          <p>${bezpiecznyTekst(match.snippet)}</p>
          <div class="knowledge-doc-meta">
            <span>Wynik dopasowania: ${bezpiecznyTekst(match.score)}</span>
            <span>Aktualizacja: ${formatujDateCzas(match.updated_at)}</span>
            <a href="${bezpiecznyTekst(match.file_link)}" target="_blank" rel="noreferrer">ĹąrĂłdĹ‚o</a>
          </div>
        </article>
      `
    )
    .join("");

  container.innerHTML = `
    <div class="knowledge-answer-box">
      <div class="knowledge-answer-main">${bezpiecznyTekst(wynik.answer || "")}</div>
      ${
        zrodla
          ? `<div class="knowledge-source-list">${zrodla}</div>`
          : `<div class="empty-state">Brak bezpoĹ›rednich ĹşrĂłdeĹ‚ do pokazania.</div>`
      }
    </div>
  `;
}

async function wczytajBazeWiedzy() {
  if (!stan.biezacyUzytkownik) {
    wyczyscBazeWiedzy();
    return;
  }
  if (!czyModulWiedzyMaZakres()) {
    wyczyscBazeWiedzy();
    document.getElementById("knowledge-access-note").textContent =
      "Wybierz konkretnÄ… organizacjÄ™, aby otworzyÄ‡ jej bazÄ™ wiedzy.";
    return;
  }

  const wynik = await api(zbudujAdresZOrganizacja("/api/knowledge/documents"));
  renderujBazeWiedzy(wynik);
}

async function zapiszDokumentWiedzy() {
  if (!czyMoznaDodawacPlikiDoBazyWiedzy()) {
    pokazPowiadomienie("To konto nie moĹĽe dodawaÄ‡ dokumentĂłw wiedzy.");
    return;
  }
  if (!czyModulWiedzyMaZakres()) {
    pokazPowiadomienie("Wybierz organizacjÄ™ przed dodaniem dokumentu wiedzy.");
    return;
  }

  const title = document.getElementById("knowledge-title").value.trim();
  const contentText = document.getElementById("knowledge-content").value.trim();
  const fileInput = document.getElementById("knowledge-file");
  const plik = fileInput.files?.[0];

  if (!plik && !contentText) {
    pokazPowiadomienie("Dodaj plik albo wklej treĹ›Ä‡ dokumentu.");
    return;
  }

  let options;
  if (plik) {
    const formData = new FormData();
    formData.append("title", title);
    formData.append("content_text", contentText);
    formData.append("file", plik);
    options = { method: "POST", body: formData };
  } else {
    options = {
      method: "POST",
      body: JSON.stringify({
        title,
        file_name: title ? `${title.toLowerCase().replaceAll(" ", "_")}.txt` : "dokument_wiedzy.txt",
        content_text: contentText,
      }),
    };
  }

  const created = await api(zbudujAdresZOrganizacja("/api/knowledge/documents"), options);
  stan.ostatniImportBazyWiedzy = {
    kind: "upload",
    organization_id: created.organization_id,
    title: created.title || title,
    file_name: created.file_name || (plik ? plik.name : ""),
    file_size: plik?.size || contentText.length,
    source_type: created.source_type || (plik ? "upload" : "manual"),
  };
  document.getElementById("knowledge-title").value = "";
  document.getElementById("knowledge-file").value = "";
  document.getElementById("knowledge-content").value = "";
  pokazPowiadomienie("Dodano dokument do bazy wiedzy.");
  await Promise.all([wczytajBazeWiedzy(), wczytajLogi()]);
}

async function synchronizujBazeWiedzy() {
  if (!czyMoznaDodawacPlikiDoBazyWiedzy()) {
    pokazPowiadomienie("To konto nie moĹĽe synchronizowaÄ‡ bazy wiedzy.");
    return;
  }
  if (!czyModulWiedzyMaZakres()) {
    pokazPowiadomienie("Wybierz organizacjÄ™ przed synchronizacjÄ… bazy wiedzy.");
    return;
  }

  const wynik = await api(zbudujAdresZOrganizacja("/api/knowledge/sync"), { method: "POST" });
  stan.ostatniImportBazyWiedzy = {
    kind: "sync",
    organization_id: wynik.organization_id,
    imported_count: wynik.imported_count,
    updated_count: wynik.updated_count,
    unchanged_count: wynik.unchanged_count,
    skipped: wynik.skipped || [],
  };
  pokazPowiadomienie(
    `Synchronizacja zakoĹ„czona. Nowe: ${wynik.imported_count}, zaktualizowane: ${wynik.updated_count}, pominiÄ™te: ${(wynik.skipped || []).length}.`
  );
  await Promise.all([wczytajBazeWiedzy(), wczytajLogi()]);
}

async function zapytajBazeWiedzy() {
  if (!czyModulWiedzyMaZakres()) {
    pokazPowiadomienie("Wybierz organizacjÄ™ przed zadaniem pytania.");
    return;
  }
  const question = document.getElementById("knowledge-question").value.trim();
  if (!question) {
    pokazPowiadomienie("Wpisz pytanie do asystenta firmowego.");
    return;
  }

  const wynik = await api(zbudujAdresZOrganizacja("/api/knowledge/ask"), {
    method: "POST",
    body: JSON.stringify({ question }),
  });
  renderujOdpowiedzBazyWiedzy(wynik);
}

async function wczytajMeta() {
  stan.meta = await api("/api/meta", {}, { pominWylogowanie: true });
  Object.assign(etykietyWidokowFokusuZadan, stan.meta.task_focus_view_labels || {});
  Object.assign(etykietyRodzajowKalendarzy, stan.meta.calendar_kind_labels || {});
  ustawWidocznoscElementowSrodowiska();
  zbudujOpcje(document.querySelector('select[name="source"]'), stan.meta.sources, "Wszystkie ĹşrĂłdĹ‚a", formatujZrodlo);
  zbudujOpcje(document.querySelector('select[name="status"]'), stan.meta.statuses, "Wszystkie statusy");
  zbudujOpcje(document.querySelector('select[name="workflow_state"]'), stan.meta.workflow_states || [], "Kazdy obieg", formatujObiegFaktury);
  zbudujOpcje(document.querySelector('select[name="duplicate_type"]'), stan.meta.duplicate_types, "Wszystkie typy duplikatu");
  zbudujOpcje(document.getElementById("task-filter-type"), stan.meta.task_types, "Wszystkie typy", formatujTypZadania);
  zbudujOpcje(document.getElementById("task-filter-status"), stan.meta.task_statuses, "Wszystkie statusy", formatujStatusZadania);
  zbudujOpcje(document.getElementById("task-filter-priority"), stan.meta.task_priorities, "Wszystkie priorytety", formatujPriorytetZadania);
  odswiezOpcjeWidokowFokusuZadan();
  zbudujOpcje(
    document.getElementById("task-filter-recurrence-pattern"),
    stan.meta.task_recurrence_patterns || [],
    "Kazda cyklicznosc",
    formatujCyklicznoscZadania
  );

  const sortBy = document.getElementById("sort-by");
  sortBy.innerHTML = `
    <option value="incoming_date">Sortuj po dacie wpĹ‚ywu</option>
    <option value="id">Sortuj po identyfikatorze</option>
    <option value="invoice_number">Sortuj po numerze faktury</option>
    <option value="ksef_number">Sortuj po numerze KSeF</option>
    <option value="issuer_name">Sortuj po wystawcy</option>
    <option value="gross_amount">Sortuj po kwocie</option>
    <option value="status">Sortuj po statusie</option>
    <option value="workflow_state">Sortuj po obiegu</option>
    <option value="updated_at">Sortuj po ostatniej zmianie</option>
  `;

  odswiezOpcjeRolUzytkownikow();
  ustawDomyslneUprawnienieBazyWiedzyDlaRoli();

  ustawInformacjeSystemowe();
  renderujStatusPrzypomnien();
  zbudujOpcjeUzytkownikowDoZadan();
  if (czyWlascicielSystemu()) {
    await wczytajUstawieniaKomunikatorowSystemowych();
  } else {
    stan.ustawieniaKomunikatorowSystemowych = null;
    renderujUstawieniaKomunikatorowSystemowych();
  }
  wyczyscFormularzUzytkownika();
  wyczyscFormularzOrganizacji();
}

async function wczytajOrganizacje() {
  if (!czyMoznaZarzadzacOrganizacjami()) {
    stan.organizacje = [];
    zbudujOpcjeOrganizacjiDlaFormularzy();
    return;
  }

  const organizacje = await api("/api/organizations");
  renderujOrganizacje(organizacje);
  if (stan.biezacyUzytkownik?.organization_id) {
    const organizacjaBiezacegoUzytkownika =
      stan.organizacje.find((item) => Number(item.organization_id) === Number(stan.biezacyUzytkownik.organization_id)) || null;
    stan.biezacyUzytkownik.organization_module_shortcuts =
      typeof organizacjaBiezacegoUzytkownika?.module_shortcuts === "object" &&
      organizacjaBiezacegoUzytkownika.module_shortcuts !== null
        ? organizacjaBiezacegoUzytkownika.module_shortcuts
        : {};
  }

  if (czyGlobalnyAdministrator()) {
    const aktywneOrganizacje = stan.organizacje.filter((item) => item.is_active);
    const czyWybranaIstnieje = aktywneOrganizacje.some(
      (item) => String(item.organization_id) === String(stan.wybranaOrganizacjaId)
    );
    if ((!stan.czyZakresOrganizacjiZainicjalizowany && !stan.wybranaOrganizacjaId) || (!czyWybranaIstnieje && stan.wybranaOrganizacjaId)) {
      stan.wybranaOrganizacjaId = aktywneOrganizacje[0]?.organization_id ? String(aktywneOrganizacje[0].organization_id) : "";
    }
    stan.czyZakresOrganizacjiZainicjalizowany = true;
    zbudujOpcjeOrganizacjiDlaFormularzy();
    document.getElementById("organization-switcher").value = stan.wybranaOrganizacjaId || "";
  } else {
    stan.wybranaOrganizacjaId = stan.biezacyUzytkownik?.organization_id
      ? String(stan.biezacyUzytkownik.organization_id)
      : "";
    stan.czyZakresOrganizacjiZainicjalizowany = true;
    zbudujOpcjeOrganizacjiDlaFormularzy();
  }
}

async function wczytajRozliczenia() {
  if (!stan.biezacyUzytkownik) {
    wyczyscWidokRozliczen();
    return;
  }

  stan.ostatniImportWyciagu = null;
  renderujPodsumowanieImportuRozliczen();
  const [rachunki, transakcje] = await Promise.all([
    api(zbudujAdresZOrganizacja("/api/billing/bank-accounts")),
    api(zbudujAdresZOrganizacja("/api/billing/transactions")),
  ]);
  const wyniki = await Promise.allSettled([
    api(zbudujAdresZOrganizacja("/api/billing/schools")),
    api(zbudujAdresZOrganizacja("/api/billing/payers")),
    api(zbudujAdresZOrganizacja("/api/billing/students")),
    api(zbudujAdresZOrganizacja("/api/billing/models")),
    api(zbudujAdresZOrganizacja("/api/billing/charges")),
    api(zbudujAdresZOrganizacja("/api/billing/ledger/balances")),
    api(zbudujAdresZOrganizacja("/api/billing/ledger/entries?limit=200")),
    api(zbudujAdresZOrganizacja("/api/billing/ledger/matches?limit=200")),
  ]);
  const [szkoly, platnicy, uczniowie, modele, naleznosci, balances, entries, matches] = wyniki.map((wynik) =>
    wynik.status === "fulfilled" && Array.isArray(wynik.value) ? wynik.value : []
  );

  stan.szkolyRozliczen = szkoly;
  stan.platnicyRozliczen = platnicy;
  stan.uczniowieRozliczen = uczniowie;
  stan.modeleRozliczen = modele;
  stan.naleznosciRozliczen = naleznosci;
  stan.billingLedgerBalances = balances;
  stan.billingLedgerEntries = entries;
  stan.billingPaymentMatches = matches;
  renderujPulpitRozliczen();
  renderujRachunkiBankowe(rachunki);
  renderujTransakcjeRozliczen(transakcje);
  renderujMapeModuluRozliczen();
  renderujKsiegeRozliczen();
}

async function wczytajPulpit() {
  const [dashboardResult, noteResult] = await Promise.allSettled([
    api(zbudujAdresZOrganizacja("/api/dashboard")),
    wczytajNotatkeOrganizacji(),
  ]);
  if (noteResult.status === "rejected") {
    console.error("Nie udalo sie pobrac wspolnej notatki organizacji:", noteResult.reason);
  }
  if (dashboardResult.status !== "fulfilled") {
    throw dashboardResult.reason;
  }
  renderujPulpit(dashboardResult.value);
}

function zbudujZapytanieFaktur() {
  const form = document.getElementById("invoice-filters");
  const formData = new FormData(form);
  const params = new URLSearchParams();

  for (const [key, value] of formData.entries()) {
    const wartosc = String(value).trim();
    if (wartosc) {
      params.set(key, wartosc);
    }
  }

  return params.toString();
}

async function wczytajUzytkownikowDoFaktur() {
  if (!stan.biezacyUzytkownik) {
    stan.uzytkownicyDoFaktur = [];
    zsynchronizujFiltrOdpowiedzialnegoZaFakture();
    odswiezPasekFiltrowFaktur();
    return;
  }
  stan.uzytkownicyDoFaktur = await api(zbudujAdresZOrganizacja("/api/invoices/assignable-users"));
  zsynchronizujFiltrOdpowiedzialnegoZaFakture();
  odswiezPasekFiltrowFaktur();
}

async function wczytajFaktury() {
  const query = zbudujZapytanieFaktur();
  const invoiceUrl = zbudujAdresZOrganizacja(`/api/invoices${query ? `?${query}` : ""}`);
  const verificationInboxUrl = zbudujAdresZOrganizacja("/api/invoices/verification-inbox?limit=6");
  const verificationWorkspaceUrl = zbudujAdresZOrganizacja(
    `/api/invoices/verification-workspace?limit=20&bucket=${encodeURIComponent(stan.aktywnyKoszykWeryfikacjiFaktur || "verification")}`
  );
  const documentIntakeUrl = zbudujAdresZOrganizacja("/api/invoices/document-intake?limit=10");
  const exceptionCenterUrl = zbudujAdresZOrganizacja("/api/invoices/exceptions?limit=10");
  const handoffBatchesUrl = zbudujAdresZOrganizacja("/api/invoice-handoff-batches?limit=10");
  const [faktury, verificationInbox, verificationWorkspace, documentIntake, exceptionCenter, handoffBatches] = await Promise.all([
    api(invoiceUrl),
    api(verificationInboxUrl).catch(() => null),
    api(verificationWorkspaceUrl).catch(() => null),
    api(documentIntakeUrl).catch(() => null),
    api(exceptionCenterUrl).catch(() => null),
    api(handoffBatchesUrl).catch(() => null),
  ]);
  renderujFaktury(faktury);
  renderujSkrzynkeWeryfikacjiFaktur(verificationInbox);
  renderujWorkspaceWeryfikacjiFaktur(verificationWorkspace);
  renderujSkrzynkePrzyjeciaDokumentowFaktur(documentIntake);
  renderujCentrumWyjatkowFaktur(exceptionCenter);
  renderujPaczkiPrzekazaniaFaktur(handoffBatches);
}

async function wczytajSzczegolyFaktury(invoiceId) {
  const detail = await api(zbudujAdresZOrganizacja(`/api/invoices/${invoiceId}`));
  renderujSzczegolyFaktury(detail);
}

async function wczytajKontrahentow() {
  const params = new URLSearchParams();
  if (stan.filtryKontrahentow.szukaj) {
    params.set("search", stan.filtryKontrahentow.szukaj);
  }
  if (stan.filtryKontrahentow.tylkoNowi) {
    params.set("only_new", "1");
  }
  const kontrahenci = await api(zbudujAdresZOrganizacja(`/api/contractors${params.toString() ? `?${params.toString()}` : ""}`));
  renderujKontrahentow(kontrahenci);
}

async function wczytajWszystkichKontrahentow() {
  stan.kontrahenciWszyscy = await api(zbudujAdresZOrganizacja("/api/contractors"));
  zsynchronizujFiltrKontrahenta();
}

async function wczytajSzczegolyKontrahenta(contractorId) {
  const detail = await api(zbudujAdresZOrganizacja(`/api/contractors/${contractorId}`));
  stan.wybranyKontrahentId = contractorId;
  renderujSzczegolyKontrahenta(detail);
}

async function wczytajLogi() {
  const logi = await api(zbudujAdresZOrganizacja("/api/logs"));
  renderujLogi(logi);
}

async function wczytajUzytkownikowDoZadan() {
  if (!stan.biezacyUzytkownik || !czyMoznaKorzystacZMojejPracy()) {
    stan.uzytkownicyDoZadan = [];
    zbudujOpcjeUzytkownikowDoZadan();
    return;
  }
  const uzytkownicy = await api(zbudujAdresZOrganizacja("/api/tasks/users"));
  stan.uzytkownicyDoZadan = uzytkownicy;
  zbudujOpcjeUzytkownikowDoZadan();
}

function zbudujZapytanieZadan() {
  const form = document.getElementById("task-filters");
  const formData = new FormData(form);
  const params = new URLSearchParams();
  for (const [key, value] of formData.entries()) {
    if (String(value).trim()) {
      params.set(key, String(value).trim());
    }
  }
  return params.toString();
}

async function wczytajZadania() {
  if (!czyMoznaKorzystacZMojejPracy()) {
    wyczyscObszarMojejPracy("Sekcja Moja praca jest dostepna po wlaczeniu modulu Asystent Szefa.");
    renderujSzybkiKalendarz();
    return [];
  }
  const query = zbudujZapytanieZadan();
  const zadania = await api(zbudujAdresZOrganizacja(`/api/tasks${query ? `?${query}` : ""}`));
  renderujZadania(zadania);
  wczytajSzablonyZadan().catch(() => {});
  renderujPanelMojejPracy();
  wczytajStatusPrzypomnien().catch(() => {});
  return zadania;
}

function zaplanujAutomatyczneFiltrowanie(timeoutKey, onApply, delay = 0) {
  const wykonajFiltrowanie = async () => {
    window.clearTimeout(stan[timeoutKey]);
    stan[timeoutKey] = null;
    try {
      await onApply();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  };

  window.clearTimeout(stan[timeoutKey]);
  if (delay <= 0) {
    void wykonajFiltrowanie();
    return;
  }

  stan[timeoutKey] = window.setTimeout(() => {
    void wykonajFiltrowanie();
  }, delay);
}

function podlaczAutomatyczneFiltrowanieFormularza(formId, timeoutKey, onApply) {
  const form = document.getElementById(formId);
  if (!form) {
    return;
  }

  const czyPoleTekstowe = (element) =>
    element instanceof HTMLInputElement &&
    ["search", "text"].includes((element.type || "").toLowerCase());

  form.addEventListener("input", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLInputElement || target instanceof HTMLSelectElement || target instanceof HTMLTextAreaElement)) {
      return;
    }
    zaplanujAutomatyczneFiltrowanie(timeoutKey, onApply, czyPoleTekstowe(target) ? 300 : 0);
  });

  form.addEventListener("change", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLInputElement || target instanceof HTMLSelectElement || target instanceof HTMLTextAreaElement)) {
      return;
    }
    zaplanujAutomatyczneFiltrowanie(timeoutKey, onApply, 0);
  });
}

async function wczytajPlannerZadan() {
  if (!czyMoznaKorzystacZMojejPracy()) {
    wyczyscObszarMojejPracy("Sekcja Moja praca jest dostepna po wlaczeniu modulu Asystent Szefa.");
    renderujSzybkiKalendarz();
    return null;
  }
  const snapshot = await api(zbudujAdresZOrganizacja("/api/tasks/planner"));
  renderujPlannerZadan(snapshot);
  renderujSzybkiKalendarz();
  renderujPanelMojejPracy();
  return snapshot;
}

async function wczytajFokusZadan() {
  if (!czyMoznaKorzystacZMojejPracy()) {
    wyczyscObszarMojejPracy("Sekcja Moja praca jest dostepna po wlaczeniu modulu Asystent Szefa.");
    return null;
  }
  const snapshot = await api(zbudujAdresZOrganizacja("/api/tasks/focus"));
  renderujFokusZadan(snapshot);
  renderujPanelMojejPracy();
  return snapshot;
}

async function wczytajStatusPrzypomnien() {
  if (!czyMoznaKorzystacZMojejPracy()) {
    return null;
  }
  try {
    const filter = pobierzFiltrOutboxaPrzypomnien();
    const outboxUrl =
      filter === "all"
        ? "/api/tasks/reminders/outbox?limit=25"
        : `/api/tasks/reminders/outbox?limit=25&status=${encodeURIComponent(filter)}`;
    const [status, outbox] = await Promise.all([
      api(zbudujAdresZOrganizacja("/api/tasks/reminders/status")),
      api(zbudujAdresZOrganizacja(outboxUrl)),
    ]);
    stan.taskReminderStatus = status || {};
    stan.taskReminderOutbox = Array.isArray(outbox) ? outbox : [];
  } catch (error) {
    // status odswiezy sie przy kolejnej probie, nie blokujemy reszty panelu
  }
  renderujStatusPrzypomnien();
  renderujPanelOutboxaPrzypomnien();
  return stan.taskReminderStatus;
}

async function wczytajSzablonyZadan() {
  if (!czyMoznaKorzystacZMojejPracy()) {
    stan.taskTemplates = [];
    return [];
  }
  try {
    const templates = await api(zbudujAdresZOrganizacja("/api/task-templates"));
    stan.taskTemplates = Array.isArray(templates) ? templates : [];
  } catch (error) {
    stan.taskTemplates = [];
  }
  renderujSzablonyZadan(
    stan.wybraneZadanieDetail?.task || (stan.wybraneZadanieId ? znajdzZadaniePoId(stan.wybraneZadanieId) : null),
    stan.wybraneZadanieDetail?.checklist_items || []
  );
  return stan.taskTemplates;
}

async function wczytajSzczegolyZadania(taskId) {
  if (!czyMoznaKorzystacZMojejPracy()) {
    wyczyscObszarMojejPracy("Sekcja Moja praca jest dostepna po wlaczeniu modulu Asystent Szefa.");
    return null;
  }
  const detail = await api(zbudujAdresZOrganizacja(`/api/tasks/${taskId}`));
  renderujPanelZadania(detail);
  return detail;
}

async function wczytajStatusPolaczeniaGoogleKalendarza() {
  if (!czyMoznaKorzystacZMojejPracy()) {
    renderujStatusPolaczeniaGoogleKalendarza(null);
    return null;
  }
  const status = await api(zbudujAdresZOrganizacja("/api/google-calendar/status"));
  renderujStatusPolaczeniaGoogleKalendarza(status);
  return status;
}

async function wczytajZewnetrzneKalendarzeGoogle(cichyTryb = true) {
  if (!czyMoznaKorzystacZMojejPracy()) {
    renderujZewnetrzneKalendarzeGoogle([]);
    return [];
  }
  if (!czyGoogleCalendarBezposrednioWlaczone()) {
    renderujZewnetrzneKalendarzeGoogle([]);
    return [];
  }
  if (!stan.statusPolaczeniaGoogleKalendarza?.connected) {
    renderujZewnetrzneKalendarzeGoogle([]);
    return [];
  }
  try {
    const calendars = await api(zbudujAdresZOrganizacja("/api/google-calendar/external-calendars"));
    renderujZewnetrzneKalendarzeGoogle(calendars);
    return calendars;
  } catch (error) {
    renderujZewnetrzneKalendarzeGoogle([]);
    if (!cichyTryb) {
      pokazPowiadomienie(error.message);
    }
    return [];
  }
}

async function wczytajKalendarzeUzytkownika() {
  if (!czyMoznaKorzystacZMojejPracy()) {
    renderujKalendarzeUzytkownika([]);
    return [];
  }
  const calendars = await api(zbudujAdresZOrganizacja("/api/user-calendars"));
  renderujKalendarzeUzytkownika(calendars);
  renderujPanelMojejPracy();
  return calendars;
}

async function wczytajUstawieniaPrzypomnienUzytkownika() {
  if (!czyMoznaKorzystacZMojejPracy()) {
    renderujUstawieniaPrzypomnienUzytkownika(null);
    return null;
  }
  const preferences = await api(zbudujAdresZOrganizacja("/api/user-reminder-preferences"));
  renderujUstawieniaPrzypomnienUzytkownika(preferences);
  return preferences;
}

async function zapiszKalendarzUzytkownika() {
  if (!czyMoznaKorzystacZMojejPracy()) return;
  if (document.getElementById("user-calendar-form")?.dataset.calendarAccessMode === "assigned") {
    pokazPowiadomienie(
      "Ten kalendarz jest przypisany przez organizacje. Zmiany moze wprowadzic Administrator organizacji albo Wlasciciel systemu."
    );
    return;
  }
  const calendarId = document.getElementById("user-calendar-id").value.trim();
  const calendarKind = document.getElementById("user-calendar-kind").value || "inne";
  const provider = document.getElementById("user-calendar-provider").value || domyslnyProviderKalendarzaUzytkownika();
  const payload = {
    display_name: document.getElementById("user-calendar-display-name").value.trim(),
    provider,
    calendar_kind: calendarKind,
    linked_organization_id:
      calendarKind === "organizacja"
        ? document.getElementById("user-calendar-linked-organization").value || null
        : null,
    external_calendar_id:
      provider === "google_api" ? document.getElementById("user-calendar-external-id").value || null : null,
    default_duration_minutes: document.getElementById("user-calendar-default-duration").value || 60,
    description: document.getElementById("user-calendar-description").value.trim(),
    is_active: document.getElementById("user-calendar-active").value === "1",
  };

  let saved;
  if (!calendarId) {
    saved = await api(zbudujAdresZOrganizacja("/api/user-calendars"), {
      method: "POST",
      body: JSON.stringify(payload),
    });
    pokazPowiadomienie("Dodano kalendarz uzytkownika.");
  } else {
    saved = await api(zbudujAdresZOrganizacja(`/api/user-calendars/${calendarId}`), {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
    pokazPowiadomienie("Zapisano zmiany kalendarza.");
  }
  await Promise.all([wczytajStatusPolaczeniaGoogleKalendarza(), wczytajZewnetrzneKalendarzeGoogle(), wczytajKalendarzeUzytkownika(), wczytajZadania(), wczytajPlannerZadan(), wczytajFokusZadan(), wczytajLogi()]);
  wypelnijFormularzKalendarzaUzytkownika(saved);
  odswiezWidocznoscPowiazanejOrganizacjiKalendarza();
}

async function usunKalendarzUzytkownika() {
  const calendarId = document.getElementById("user-calendar-id").value.trim();
  if (!calendarId || !czyMoznaKorzystacZMojejPracy()) return;
  if (document.getElementById("user-calendar-form")?.dataset.calendarAccessMode === "assigned") {
    pokazPowiadomienie(
      "Ten kalendarz jest przypisany przez organizacje. Usuniecie moze wykonac Administrator organizacji albo Wlasciciel systemu."
    );
    return;
  }
  await api(zbudujAdresZOrganizacja(`/api/user-calendars/${calendarId}`), { method: "DELETE" });
  pokazPowiadomienie("Usunieto kalendarz.");
  wyczyscFormularzKalendarzaUzytkownika();
  await Promise.all([
    wczytajStatusPolaczeniaGoogleKalendarza(),
    wczytajZewnetrzneKalendarzeGoogle(),
    wczytajKalendarzeUzytkownika(),
    wczytajZadania(),
    wczytajPlannerZadan(),
    wczytajFokusZadan(),
    wczytajLogi(),
  ]);
}

async function rozpocznijPolaczenieGoogleKalendarza() {
  if (!czyMoznaKorzystacZMojejPracy()) return;
  const visibilityCheckbox = document.getElementById("google-calendar-visibility-confirmation");
  if (!visibilityCheckbox?.checked) {
    pokazPowiadomienie(
      "Potwierdz najpierw, ze podlaczasz konto uzywane do pracy i ze adres bedzie widoczny dla administratora."
    );
    return;
  }
  const response = await api(zbudujAdresZOrganizacja("/api/google-calendar/connect"), {
    method: "POST",
    body: JSON.stringify({
      confirm_work_account_visibility: true,
    }),
  });
  const popup = window.open(
    response.authorization_url,
    "google-calendar-connect",
    "popup=yes,width=640,height=780,resizable=yes,scrollbars=yes"
  );
  if (!popup) {
    window.location.href = response.authorization_url;
    return;
  }
  popup.focus();
  pokazPowiadomienie("Otwarto okno polaczenia Google Calendar.");
}

async function odswiezPolaczenieGoogleKalendarza(cichyTryb = false) {
  if (!czyMoznaKorzystacZMojejPracy()) {
    wyczyscObszarMojejPracy("Sekcja Moja praca jest dostepna po wlaczeniu modulu Asystent Szefa.");
    return;
  }
  await wczytajStatusPolaczeniaGoogleKalendarza();
  await wczytajZewnetrzneKalendarzeGoogle(cichyTryb);
  odswiezWidocznoscPolGoogleKalendarza();
}

async function odlaczGoogleKalendarz() {
  if (!czyMoznaKorzystacZMojejPracy()) return;
  await api(zbudujAdresZOrganizacja("/api/google-calendar/disconnect"), { method: "POST" });
  await Promise.all([odswiezPolaczenieGoogleKalendarza(true), wczytajKalendarzeUzytkownika(), wczytajZadania(), wczytajPlannerZadan(), wczytajFokusZadan(), wczytajLogi()]);
  wyczyscFormularzKalendarzaUzytkownika();
  pokazPowiadomienie("Rozlaczono konto Google Calendar.");
}

async function zapiszUstawieniaPrzypomnienUzytkownika() {
  if (!czyMoznaKorzystacZMojejPracy()) return;
  const saved = await api(zbudujAdresZOrganizacja("/api/user-reminder-preferences"), {
    method: "POST",
    body: JSON.stringify({
      telegram_reminders_enabled: document.getElementById("user-own-telegram-reminders-enabled").checked,
      browser_notifications_enabled: document.getElementById("user-own-browser-reminders-enabled")?.checked,
      quiet_hours_start: document.getElementById("user-own-quiet-hours-start").value,
      quiet_hours_end: document.getElementById("user-own-quiet-hours-end").value,
      repeat_interval_minutes: document.getElementById("user-own-repeat-interval").value,
    }),
  });
  renderujUstawieniaPrzypomnienUzytkownika(saved);
  pokazPowiadomienie("Zapisano ustawienia przypomnien.");
}

async function wczytajUzytkownikow() {
  if (!czyMoznaZarzadzacUzytkownikami()) {
    stan.uzytkownicy = [];
    document.getElementById("users-table-body").innerHTML = `<tr><td colspan="10">Panel uĹĽytkownikĂłw jest dostÄ™pny tylko dla WĹ‚aĹ›ciciela systemu albo Administratora organizacji.</td></tr>`;
    return;
  }
  const uzytkownicy = await api(zbudujAdresZOrganizacja("/api/users"));
  renderujUzytkownikow(uzytkownicy);
}

async function wczytajPanelOrganizacji() {
  if (!czyMoznaZarzadzacOrganizacjami()) {
    document.getElementById("organization-table-body").innerHTML =
      `<tr><td colspan="15">Panel organizacji jest dostÄ™pny tylko dla WĹ‚aĹ›ciciela systemu albo Administratora organizacji.</td></tr>`;
    return;
  }
  await wczytajOrganizacje();
}

async function odswiezDanePoZalogowaniu() {
  await wczytajOrganizacje();
  const emailCenterPromises = czyMoznaOtworzycCentrumEmaila() ? [wczytajCentrumEmaila()] : [];
  const workspaceMojejPracyAktywny = czyMoznaKorzystacZMojejPracy();
  if (workspaceMojejPracyAktywny) {
    await wczytajStatusPolaczeniaGoogleKalendarza();
    await wczytajZewnetrzneKalendarzeGoogle();
  } else {
    wyczyscObszarMojejPracy("Sekcja Moja praca jest dostepna po wlaczeniu modulu Asystent Szefa.");
  }
  const zadaniaPromises = workspaceMojejPracyAktywny
    ? [
        wczytajZadania(),
        wczytajPlannerZadan(),
        wczytajFokusZadan(),
        wczytajKalendarzeUzytkownika(),
        wczytajUstawieniaPrzypomnienUzytkownika(),
        wczytajUzytkownikowDoZadan(),
      ]
    : [];
  await Promise.all([
    wczytajPulpit(),
    wczytajNotatkeOsobista(),
    wczytajWszystkichKontrahentow(),
    wczytajUzytkownikowDoFaktur(),
    wczytajKontrahentow(),
    wczytajFaktury(),
    wczytajRozliczenia(),
    wczytajSkrzynkeWplywow(),
    wczytajZapisaneWidoki(),
    wczytajWidokiFaktur(),
    wczytajAutomatyzacje(),
    wczytajZdrowieSystemu(),
    wczytajBazeWiedzy(),
    wczytajLogi(),
    ...emailCenterPromises,
    ...zadaniaPromises,
  ]);
  if (czyMoznaZarzadzacUzytkownikami()) {
    await wczytajUzytkownikow();
  } else {
    wyczyscFormularzUzytkownika();
    document.getElementById("users-table-body").innerHTML = `<tr><td colspan="10">Panel uĹĽytkownikĂłw jest dostÄ™pny tylko dla WĹ‚aĹ›ciciela systemu albo Administratora organizacji.</td></tr>`;
  }
  if (czyMoznaZarzadzacOrganizacjami()) {
    await wczytajPanelOrganizacji();
  } else {
    document.getElementById("organization-table-body").innerHTML =
      `<tr><td colspan="15">Panel organizacji jest dostÄ™pny tylko dla WĹ‚aĹ›ciciela systemu albo Administratora organizacji.</td></tr>`;
  }
  odswiezWidocznoscPowiazanejOrganizacjiKalendarza();
  odswiezPasekSesji();
  renderujPanelMojejPracy();
  renderujStanAlertowPrzegladarki();
  uruchomPollingAlertowPrzegladarki();
  odswiezAlertyPrzegladarki().catch(() => {});
}

async function sprobujPrzywrocicSesje() {
  try {
    stan.biezacyUzytkownik = await api("/api/session/current", {}, { pominWylogowanie: true });
    ukryjEkranLogowania();
    odswiezPasekSesji();
    return true;
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      przygotujWidokPoWylogowaniu();
      return false;
    }
    throw error;
  }
}

async function zalogujDoSystemu(login, password) {
  const uzytkownik = await api(
    "/api/session/login",
    {
      method: "POST",
      body: JSON.stringify({ login, password }),
    },
    { pominWylogowanie: true }
  );
  stan.biezacyUzytkownik = uzytkownik;
  ukryjEkranLogowania();
  odswiezPasekSesji();
  await odswiezDanePoZalogowaniu();
}

async function zalogujSzybkimKontemDemo(index) {
  const szybkieKonta = pobierzSzybkieLogowaniaDemo();
  const konto = szybkieKonta[index];
  if (!konto) {
    pokazPowiadomienie("Wybrane konto probne nie jest juz dostepne.");
    return;
  }
  const kontener = document.getElementById("quick-login-buttons");
  const przyciski = kontener ? Array.from(kontener.querySelectorAll("[data-quick-login-index]")) : [];
  przyciski.forEach((przycisk) => {
    przycisk.disabled = true;
  });
  document.getElementById("login-input").value = konto.login;
  document.getElementById("password-input").value = konto.password;
  try {
    await zalogujDoSystemu(konto.login, konto.password);
    document.getElementById("password-input").value = "";
    pokazPowiadomienie(`Zalogowano jako ${konto.display_name || konto.login}.`);
  } catch (error) {
    pokazPowiadomienie(error.message);
  } finally {
    przyciski.forEach((przycisk) => {
      przycisk.disabled = false;
    });
  }
}

async function wylogujZSystemu() {
  try {
    await api("/api/session/logout", { method: "POST" }, { pominWylogowanie: true });
  } catch (error) {
    if (!(error instanceof ApiError) || error.status !== 401) {
      throw error;
    }
  } finally {
    przygotujWidokPoWylogowaniu();
  }
}

function czyBrakWyboruOrganizacjiRozliczen() {
  return czyGlobalnyAdministrator() && !stan.wybranaOrganizacjaId;
}

function pilnujZakresuOrganizacjiRozliczen(komunikat) {
  if (czyBrakWyboruOrganizacjiRozliczen()) {
    pokazPowiadomienie(komunikat);
    return true;
  }
  return false;
}

async function zapiszSzkoleRozliczen() {
  if (!czyMoznaZapisywac()) return;
  if (pilnujZakresuOrganizacjiRozliczen("Wybierz konkretna organizacje przed dodaniem szkoly.")) return;

  const payload = {
    full_name: document.getElementById("billing-school-full-name").value.trim(),
    short_name: document.getElementById("billing-school-short-name").value.trim(),
    city: document.getElementById("billing-school-city").value.trim(),
    notes: document.getElementById("billing-school-notes").value.trim(),
  };
  await api(zbudujAdresZOrganizacja("/api/billing/schools"), {
    method: "POST",
    body: JSON.stringify(payload),
  });
  document.getElementById("billing-school-form").reset();
  pokazPowiadomienie("Dodano szkole.");
  await Promise.all([wczytajRozliczenia(), wczytajLogi()]);
}

async function zapiszPlatnikaRozliczen() {
  if (!czyMoznaZapisywac()) return;
  if (pilnujZakresuOrganizacjiRozliczen("Wybierz konkretna organizacje przed dodaniem rodziny.")) return;

  const payload = {
    display_name: document.getElementById("billing-payer-display-name").value.trim(),
    contact_phone: document.getElementById("billing-payer-contact-phone").value.trim(),
    email: document.getElementById("billing-payer-email").value.trim(),
    has_large_family_card: document.getElementById("billing-payer-has-kdr").checked,
    notes: document.getElementById("billing-payer-notes").value.trim(),
  };
  await api(zbudujAdresZOrganizacja("/api/billing/payers"), {
    method: "POST",
    body: JSON.stringify(payload),
  });
  document.getElementById("billing-payer-form").reset();
  pokazPowiadomienie("Dodano rodzine.");
  await Promise.all([wczytajRozliczenia(), wczytajLogi()]);
}

async function zapiszUczniaRozliczen() {
  if (!czyMoznaZapisywac()) return;
  if (pilnujZakresuOrganizacjiRozliczen("Wybierz konkretna organizacje przed dodaniem ucznia.")) return;

  const payload = {
    full_name: document.getElementById("billing-student-full-name").value.trim(),
    billing_payer_id: document.getElementById("billing-student-payer-id").value || null,
    payer_contact_phone: document.getElementById("billing-student-payer-phone").value.trim(),
    payer_display_name: document.getElementById("billing-student-payer-display-name").value.trim(),
    payer_email: document.getElementById("billing-student-payer-email").value.trim(),
    payer_has_large_family_card: document.getElementById("billing-student-payer-has-kdr").checked,
    billing_school_id: document.getElementById("billing-student-school-id").value || null,
    billing_model_id: document.getElementById("billing-student-model-id").value || null,
    lesson_day: document.getElementById("billing-student-lesson-day").value.trim(),
    family_billing_order: document.getElementById("billing-student-family-order").value || 1,
    group_name: document.getElementById("billing-student-group-name").value.trim(),
    notes: document.getElementById("billing-student-notes").value.trim(),
  };
  await api(zbudujAdresZOrganizacja("/api/billing/students"), {
    method: "POST",
    body: JSON.stringify(payload),
  });
  document.getElementById("billing-student-form").reset();
  const studentFamilyOrder = document.getElementById("billing-student-family-order");
  if (studentFamilyOrder) studentFamilyOrder.value = "1";
  odswiezPowiazanieRodzinyWUczniu({ source: "data" });
  pokazPowiadomienie("Dodano ucznia.");
  await Promise.all([wczytajRozliczenia(), wczytajLogi()]);
}

async function zapiszModelRozliczen() {
  if (!czyMoznaZapisywac()) return;
  if (pilnujZakresuOrganizacjiRozliczen("Wybierz konkretna organizacje przed dodaniem modelu.")) return;

  const payload = {
    name: document.getElementById("billing-model-name").value.trim(),
    school_year: document.getElementById("billing-model-school-year").value.trim(),
    lesson_day: document.getElementById("billing-model-lesson-day").value.trim(),
    settlement_mode: document.getElementById("billing-model-settlement-mode").value,
    monthly_rate_amount: document.getElementById("billing-model-monthly-rate").value || null,
    semester_rate_amount: document.getElementById("billing-model-semester-rate").value || null,
    sibling_discount_amount: document.getElementById("billing-model-sibling-discount").value || null,
    large_family_discount_amount: document.getElementById("billing-model-large-family-discount").value || null,
    intro_free_lessons_count: document.getElementById("billing-model-intro-free-lessons").value || 1,
    contract_required: document.getElementById("billing-model-contract-required").checked,
    notes: document.getElementById("billing-model-notes").value.trim(),
  };
  await api(zbudujAdresZOrganizacja("/api/billing/models"), {
    method: "POST",
    body: JSON.stringify(payload),
  });
  document.getElementById("billing-model-form").reset();
  const siblingDiscount = document.getElementById("billing-model-sibling-discount");
  if (siblingDiscount) siblingDiscount.value = "100";
  const largeFamilyDiscount = document.getElementById("billing-model-large-family-discount");
  if (largeFamilyDiscount) largeFamilyDiscount.value = "50";
  const introFreeLessons = document.getElementById("billing-model-intro-free-lessons");
  if (introFreeLessons) introFreeLessons.value = "1";
  pokazPowiadomienie("Dodano model rozliczen.");
  await Promise.all([wczytajRozliczenia(), wczytajLogi()]);
}

async function generujNaleznosciRozliczen() {
  if (!czyMoznaZapisywac()) return;
  if (pilnujZakresuOrganizacjiRozliczen("Wybierz konkretna organizacje przed generowaniem naleznosci.")) return;

  const payload = {
    billing_model_id: document.getElementById("billing-charge-model-id").value || null,
    period_label: document.getElementById("billing-charge-period-label").value.trim(),
    due_date: document.getElementById("billing-charge-due-date").value,
    lesson_count: document.getElementById("billing-charge-lesson-count").value || 1,
    notes: document.getElementById("billing-charge-notes").value.trim(),
  };
  const result = await api(zbudujAdresZOrganizacja("/api/billing/charges/generate"), {
    method: "POST",
    body: JSON.stringify(payload),
  });
  document.getElementById("billing-charge-generator-form").reset();
  const chargeLessonCount = document.getElementById("billing-charge-lesson-count");
  if (chargeLessonCount) chargeLessonCount.value = "1";
  pokazPowiadomienie(`Wygenerowano ${formatujWartosc(result.charge_count || 0)} naleznosci.`);
  await Promise.all([wczytajRozliczenia(), wczytajLogi()]);
}

async function zapiszRachunekBankowy() {
  if (!czyMoznaZapisywac()) {
    return;
  }

  if (pilnujZakresuOrganizacjiRozliczen("Wybierz konkretna organizacje przed dodaniem rachunku bankowego.")) return;

  const payload = {
    account_name: document.getElementById("billing-account-name").value.trim(),
    bank_name: document.getElementById("billing-bank-name").value.trim(),
    iban: document.getElementById("billing-iban").value.trim(),
    currency: document.getElementById("billing-currency").value.trim().toUpperCase(),
  };

  await api(zbudujAdresZOrganizacja("/api/billing/bank-accounts"), {
    method: "POST",
    body: JSON.stringify(payload),
  });

  document.getElementById("billing-bank-account-form").reset();
  document.getElementById("billing-currency").value = "PLN";
  pokazPowiadomienie("Dodano rachunek bankowy.");
  await Promise.all([wczytajRozliczenia(), wczytajLogi()]);
}

async function importujWyciagCsv() {
  if (!czyMoznaZapisywac()) {
    return;
  }

  if (pilnujZakresuOrganizacjiRozliczen("Wybierz konkretna organizacje przed importem wyciagu.")) return;

  const bankAccountId = document.getElementById("billing-import-bank-account-id").value;
  if (!bankAccountId) {
    throw new Error("Wybierz rachunek bankowy do importu wyciagu.");
  }

  const fileInput = document.getElementById("billing-import-file");
  const file = fileInput.files?.[0];
  if (!file) {
    throw new Error("Wybierz plik CSV do importu.");
  }

  const csvContent = await file.text();
  const result = await api(zbudujAdresZOrganizacja("/api/billing/statements/import-csv"), {
    method: "POST",
    body: JSON.stringify({
      billing_bank_account_id: bankAccountId,
      source_file_name: file.name,
      csv_content: csvContent,
    }),
  });

  stan.ostatniImportWyciagu = result;
  renderujPodsumowanieImportuRozliczen();
  document.getElementById("billing-statement-import-form").reset();
  zbudujOpcjeRachunkowBankowych();
  pokazPowiadomienie("Zaimportowano wyciag CSV.");
  await Promise.all([wczytajRozliczenia(), wczytajLogi()]);
  stan.ostatniImportWyciagu = result;
  renderujPodsumowanieImportuRozliczen();
}

async function wyslijPrzypomnienieZadaniaTeraz() {
  if (!stan.wybraneZadanieId || !czyMoznaZapisywac()) {
    return;
  }

  const detail = await api(zbudujAdresZOrganizacja(`/api/tasks/${stan.wybraneZadanieId}/send-reminder`), {
    method: "POST",
  });
  pokazPowiadomienie("Wyslano przypomnienie Telegram.");
  await Promise.all([wczytajZadania(), wczytajPlannerZadan(), wczytajFokusZadan(), wczytajLogi(), wczytajPulpit()]);
  renderujPanelZadania(detail);
}

async function wymusWysylkePrzypomnien() {
  if (!czyMoznaZapisywac()) {
    return;
  }

  const response = await api(zbudujAdresZOrganizacja("/api/tasks/reminders/dispatch"), {
    method: "POST",
  });
  const result = response.result || {};
  const sent = Number(result.sent || 0);
  const failed = Number(result.failed || 0);
  const deferred = Number(result.deferred || 0);
  pokazPowiadomienie(`Dispatcher uruchomiony: ${sent} wyslanych, ${deferred} odlozonych, ${failed} bledow.`);
  await Promise.all([
    wczytajStatusPrzypomnien(),
    wczytajPulpit(),
    wczytajZadania(),
    wczytajPlannerZadan(),
    wczytajFokusZadan(),
    wczytajLogi(),
  ]);
}

async function odlozPrzypomnienieZadania(taskId, mode) {
  if (!taskId || !czyMoznaZapisywac()) {
    return;
  }
  const detail = await api(zbudujAdresZOrganizacja(`/api/tasks/${taskId}/snooze-reminder`), {
    method: "POST",
    body: JSON.stringify({ mode }),
  });
  pokazPowiadomienie("Odlozono przypomnienie.");
  await Promise.all([wczytajZadania(), wczytajPlannerZadan(), wczytajFokusZadan(), wczytajLogi(), wczytajPulpit()]);
  if (Number(stan.wybraneZadanieId) === Number(taskId)) {
    renderujPanelZadania(detail);
  }
}

async function synchronizujKalendarzZadaniaTeraz() {
  if (!stan.wybraneZadanieId || !czyMoznaZapisywac()) {
    return;
  }

  const detail = await api(zbudujAdresZOrganizacja(`/api/tasks/${stan.wybraneZadanieId}/sync-calendar`), {
    method: "POST",
  });
  pokazPowiadomienie("Zakonczono reczna synchronizacje z Google Calendar.");
  await Promise.all([wczytajZadania(), wczytajPlannerZadan(), wczytajFokusZadan(), wczytajLogi(), wczytajPulpit()]);
  renderujPanelZadania(detail);
}

async function sprawdzStanKalendarzaGoogleTeraz() {
  if (!stan.wybraneZadanieId || !czyMoznaZapisywac()) {
    return;
  }

  const detail = await api(zbudujAdresZOrganizacja(`/api/tasks/${stan.wybraneZadanieId}/check-calendar`), {
    method: "POST",
  });
  pokazPowiadomienie("Sprawdzono stan wpisu w Google Calendar.");
  await Promise.all([wczytajZadania(), wczytajPlannerZadan(), wczytajFokusZadan(), wczytajLogi(), wczytajPulpit()]);
  renderujPanelZadania(detail);
}

async function zaktualizujStatusZadania(taskId, status) {
  if (!taskId || !czyMoznaZapisywac()) {
    return;
  }
  const detail = await api(zbudujAdresZOrganizacja(`/api/tasks/${taskId}`));
  const task = detail?.task;
  if (!task) {
    throw new Error("Nie znaleziono wpisu do aktualizacji.");
  }
  const payload = {
    status,
    title: task?.title || "",
    task_type: task?.task_type || "zadanie",
    priority: task?.priority || "normalny",
    calendar_id: task?.calendar_id || "",
    due_at: task?.due_at || "",
    remind_at: task?.remind_at || "",
    calendar_duration_minutes: task?.calendar_duration_minutes || 60,
    recurrence_pattern: task?.recurrence_pattern || "brak",
    recurrence_interval: task?.recurrence_interval || 1,
    recurrence_weekdays: task?.recurrence_weekdays || "",
    recurrence_end_at: task?.recurrence_end_at || "",
    description: task?.description || "",
  };
  if (czyMoznaPrzypisywacZadania() && task) {
    payload.visibility_scope = task.visibility_scope || "prywatne";
    payload.assigned_user_id = task.assigned_user_id || "";
    payload.visible_user_ids = Array.isArray(task.visible_user_ids)
      ? task.visible_user_ids
      : (detail?.visible_users || []).map((item) => Number(item.user_id));
  }
  await api(zbudujAdresZOrganizacja(`/api/tasks/${taskId}`), {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
  pokazPowiadomienie("Zapisano zmiane statusu.");
  await Promise.all([wczytajZadania(), wczytajPlannerZadan(), wczytajFokusZadan(), wczytajPulpit(), wczytajLogi()]);
  if (Number(stan.wybraneZadanieId) === Number(taskId)) {
    await wczytajSzczegolyZadania(taskId);
  }
}

async function zapiszZadanie() {
  if (!czyMoznaZapisywac()) {
    return;
  }
  const taskId = document.getElementById("task-id").value.trim();
  const payload = {
    title: document.getElementById("task-title").value.trim(),
    task_type: document.getElementById("task-type").value,
    status: document.getElementById("task-status").value,
    priority: document.getElementById("task-priority").value,
    calendar_id: document.getElementById("task-calendar-id").value,
    due_at: document.getElementById("task-due-at").value,
    remind_at: document.getElementById("task-remind-at").value,
    calendar_duration_minutes: document.getElementById("task-calendar-duration").value,
    recurrence_pattern: document.getElementById("task-recurrence-pattern").value,
    recurrence_interval: document.getElementById("task-recurrence-interval").value,
    recurrence_weekdays: document.getElementById("task-recurrence-weekdays").value,
    recurrence_end_at: document.getElementById("task-recurrence-end-at").value,
    recurrence_apply_scope: document.getElementById("task-recurrence-apply-scope")?.value || "tylko_ten",
    description: document.getElementById("task-description").value.trim(),
    linked_entities: pobierzPowiazaniaEdytowanegoZadania(),
  };

  if (czyMoznaPrzypisywacZadania()) {
    const visibilityScope = pobierzZakresWidocznosciZadania();
    payload.visibility_scope = visibilityScope;
    payload.assigned_user_id = document.getElementById("task-assigned-user").value;
    payload.visible_user_ids = visibilityScope === "wybrane_osoby" ? pobierzWybraneIdWidocznosciZadania() : [];
  }

  let wynik;
  if (!taskId) {
    wynik = await api(zbudujAdresZOrganizacja("/api/tasks"), {
      method: "POST",
      body: JSON.stringify(payload),
    });
      pokazPowiadomienie("Dodano nowy wpis.");
  } else {
    wynik = await api(zbudujAdresZOrganizacja(`/api/tasks/${taskId}`), {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
    pokazPowiadomienie("Zapisano zmiany zadania.");
  }

  await Promise.all([wczytajZadania(), wczytajPlannerZadan(), wczytajFokusZadan(), wczytajPulpit(), wczytajLogi()]);
  await wczytajSzczegolyZadania(wynik.task_id);
}

async function dodajNotatkeDoZadania() {
  if (!stan.wybraneZadanieId || !czyMoznaZapisywac()) {
    return;
  }
  const pole = document.getElementById("task-note-text");
  const noteText = pole.value.trim();
  const parentId = Number(document.getElementById("task-note-parent-id")?.value || 0);
  const noteKind = String(document.getElementById("task-note-kind")?.value || "comment").trim() || "comment";
  const detail = await api(zbudujAdresZOrganizacja(`/api/tasks/${stan.wybraneZadanieId}/notes`), {
    method: "POST",
    body: JSON.stringify({
      note_text: noteText,
      parent_note_id: parentId || null,
      note_kind: parentId ? "reply" : noteKind,
    }),
  });
  pole.value = "";
  ustawCelOdpowiedziNotatki(null);
  pokazPowiadomienie("Dodano notatke do zadania.");
  await Promise.all([wczytajZadania(), wczytajLogi()]);
  renderujPanelZadania(detail);
}

function ustawCelOdpowiedziNotatki(noteId = null) {
  stan.taskNoteReplyTarget = noteId ? Number(noteId) : null;
  const parentInput = document.getElementById("task-note-parent-id");
  const kindInput = document.getElementById("task-note-kind");
  const targetBox = document.getElementById("task-note-reply-target");
  const clearButton = document.getElementById("task-note-clear-reply");
  if (parentInput) {
    parentInput.value = stan.taskNoteReplyTarget ? String(stan.taskNoteReplyTarget) : "";
  }
  if (kindInput) {
    kindInput.value = stan.taskNoteReplyTarget ? "reply" : "comment";
  }
  if (targetBox) {
    if (stan.taskNoteReplyTarget) {
      const replyTo = znajdzNotatkeWKontekscie(stan.taskNoteReplyTarget);
      targetBox.innerHTML = `Odpowiedz do: <strong>${bezpiecznyTekst(replyTo?.created_by_user_name || "komentarza")}</strong>`;
      targetBox.classList.remove("hidden");
    } else {
      targetBox.innerHTML = "";
      targetBox.classList.add("hidden");
    }
  }
  if (clearButton) {
    clearButton.disabled = !stan.taskNoteReplyTarget;
  }
}

function znajdzNotatkeWKontekscie(noteId) {
  const detailRoot = document.getElementById("task-detail");
  const note = detailRoot?.querySelector?.(`[data-task-note-id="${Number(noteId)}"]`);
  if (!note) {
    return null;
  }
  return {
    created_by_user_name: note.querySelector("strong")?.textContent || "",
  };
}

async function dodajElementChecklistyDoZadania() {
  if (!stan.wybraneZadanieId || !czyMoznaZapisywac()) {
    return;
  }
  const input = document.getElementById("task-checklist-text");
  const itemText = input?.value?.trim() || "";
  if (!itemText) {
    throw new Error("Wpisz tresc elementu checklisty.");
  }
  const detail = await api(zbudujAdresZOrganizacja(`/api/tasks/${stan.wybraneZadanieId}/checklist`), {
    method: "POST",
    body: JSON.stringify({ item_text: itemText }),
  });
  if (input) {
    input.value = "";
  }
  pokazPowiadomienie("Dodano element checklisty.");
  await Promise.all([wczytajZadania(), wczytajLogi()]);
  renderujPanelZadania(detail);
}

async function przelaczElementChecklisty(itemId) {
  if (!stan.wybraneZadanieId || !itemId || !czyMoznaZapisywac()) {
    return;
  }
  const detail = await api(zbudujAdresZOrganizacja(`/api/tasks/${stan.wybraneZadanieId}/checklist/${itemId}`), {
    method: "PATCH",
  });
  pokazPowiadomienie("Zaktualizowano checklistÄ™.");
  await Promise.all([wczytajZadania(), wczytajLogi()]);
  renderujPanelZadania(detail);
}

async function utworzWniosekAkceptacjiDlaEncji(entityType, entityId) {
  const normalizedEntityType = String(entityType || "").trim().toLowerCase();
  const normalizedEntityId = Number(entityId || 0);
  if (!normalizedEntityType || !normalizedEntityId || !czyMoznaZapisywac()) {
    return;
  }
  const title = document.getElementById("approval-title")?.value?.trim() || "Wniosek akceptacyjny";
  const description = document.getElementById("approval-description")?.value?.trim() || "";
  const requestedUserId = Number(document.getElementById("approval-requested-user")?.value || 0);
  const approveStatus = document.getElementById("approval-approve-status")?.value?.trim() || null;
  const rejectStatus = document.getElementById("approval-reject-status")?.value?.trim() || null;
  const created = await api(zbudujAdresZOrganizacja("/api/approvals"), {
    method: "POST",
    body: JSON.stringify({
      entity_type: normalizedEntityType,
      entity_id: normalizedEntityId,
      title,
      description,
      requested_user_id: requestedUserId || null,
      approve_status: approveStatus,
      reject_status: rejectStatus,
    }),
  });
  pokazPowiadomienie("Utworzono wniosek akceptacyjny.");
  await Promise.all([wczytajZadania(), wczytajLogi()]);
  if (normalizedEntityType === "task" && normalizedEntityId) {
    const detail = await wczytajSzczegolyZadania(normalizedEntityId);
    renderujPanelZadania(detail);
  } else if (normalizedEntityType === "invoice" && normalizedEntityId) {
    await wczytajSzczegolyFaktury(normalizedEntityId);
  }
  return created;
}

async function zdecydujWniosekAkceptacji(approvalId, action, entityType = "", entityId = 0) {
  if (!approvalId || !action || !czyMoznaZapisywac()) {
    return;
  }
  const path = action === "approve" ? "approve" : action === "reject" ? "reject" : null;
  if (!path) {
    return;
  }
  const payload = {
    reason: action === "reject" ? "Odrzucono z poziomu panelu zadan." : "Zatwierdzono z poziomu panelu zadan.",
  };
  await api(zbudujAdresZOrganizacja(`/api/approvals/${approvalId}/${path}`), {
    method: "POST",
    body: JSON.stringify(payload),
  });
  pokazPowiadomienie(action === "approve" ? "Zatwierdzono wniosek." : "Odrzucono wniosek.");
  await Promise.all([wczytajZadania(), wczytajLogi()]);
  const normalizedEntityType = String(entityType || "").trim().toLowerCase();
  if (normalizedEntityType === "task" && Number(entityId || stan.wybraneZadanieId || 0)) {
    const detail = await wczytajSzczegolyZadania(Number(entityId || stan.wybraneZadanieId));
    renderujPanelZadania(detail);
  } else if (normalizedEntityType === "invoice" && Number(entityId || stan.wybranaFakturaId || 0)) {
    await wczytajSzczegolyFaktury(Number(entityId || stan.wybranaFakturaId));
  }
}

function pobierzDaneSzablonuZFormularza() {
  const checklistText = String(document.getElementById("task-template-checklist")?.value || "");
  return {
    template_name: String(document.getElementById("task-template-name")?.value || "").trim(),
    template_description: String(document.getElementById("task-template-description")?.value || "").trim(),
    task_type: String(document.getElementById("task-template-type")?.value || "zadanie"),
    priority: String(document.getElementById("task-template-priority")?.value || "normalny"),
    visibility_scope: String(document.getElementById("task-template-visibility")?.value || "prywatne"),
    due_offset_minutes: document.getElementById("task-template-due-offset")?.value || "",
    reminder_offset_minutes: document.getElementById("task-template-reminder-offset")?.value || "",
    calendar_duration_minutes: document.getElementById("task-template-duration")?.value || "",
    is_active: Boolean(document.getElementById("task-template-active")?.checked),
    checklist_items: checklistText
      .split("\n")
      .map((item) => item.trim())
      .filter(Boolean),
  };
}

async function zapiszSzablonZadania() {
  if (!czyMoznaZapisywac()) {
    return;
  }
  const templateId = Number(document.getElementById("task-template-id")?.value || 0);
  const payload = pobierzDaneSzablonuZFormularza();
  if (!payload.template_name) {
    throw new Error("Nazwa szablonu jest wymagana.");
  }
  const detail = templateId
    ? await api(zbudujAdresZOrganizacja(`/api/task-templates/${templateId}`), {
        method: "PATCH",
        body: JSON.stringify(payload),
      })
    : await api(zbudujAdresZOrganizacja("/api/task-templates"), {
        method: "POST",
        body: JSON.stringify(payload),
      });
  pokazPowiadomienie(templateId ? "Zaktualizowano szablon." : "Zapisano nowy szablon.");
  stan.taskTemplateEditorId = Number(detail?.task_template_id || templateId || 0) || null;
  await wczytajSzablonyZadan();
}

function wyczyscFormularzSzablonuZadania() {
  stan.taskTemplateEditorId = null;
  renderujSzablonyZadan(stan.wybraneZadanieId ? znajdzZadaniePoId(stan.wybraneZadanieId) : null);
}

function wypelnijSzablonZBiezacegoZadania() {
  const task = stan.wybraneZadanieId ? znajdzZadaniePoId(stan.wybraneZadanieId) : null;
  if (!task) {
    throw new Error("Najpierw wybierz zadanie.");
  }
  const checklistItems = Array.isArray(stan.wybraneZadanieDetail?.checklist_items)
    ? stan.wybraneZadanieDetail.checklist_items.map((item) => item.item_text)
    : [];
  const formValues = {
    task_template_id: "",
    template_name: task.title || "Szablon z zadania",
    template_description: task.description || "",
    task_type: task.task_type || "zadanie",
    priority: task.priority || "normalny",
    visibility_scope: task.visibility_scope || "prywatne",
    due_offset_minutes: "",
    reminder_offset_minutes: "",
    calendar_duration_minutes: task.calendar_duration_minutes || 60,
    checklist_items: checklistItems.join("\n"),
  };
  stan.taskTemplateEditorId = null;
  requestAnimationFrame(() => {
    const map = {
      "task-template-id": formValues.task_template_id,
      "task-template-name": formValues.template_name,
      "task-template-description": formValues.template_description,
      "task-template-type": formValues.task_type,
      "task-template-priority": formValues.priority,
      "task-template-visibility": formValues.visibility_scope,
      "task-template-due-offset": formValues.due_offset_minutes,
      "task-template-reminder-offset": formValues.reminder_offset_minutes,
      "task-template-duration": formValues.calendar_duration_minutes,
      "task-template-checklist": formValues.checklist_items,
    };
    Object.entries(map).forEach(([fieldId, value]) => {
      const field = document.getElementById(fieldId);
      if (field) {
        field.value = value;
      }
    });
    const active = document.getElementById("task-template-active");
    if (active) {
      active.checked = true;
    }
  });
}

async function utworzWpisZSzablonu(templateId) {
  const template = znajdzSzablonPoId(templateId);
  if (!template) {
    throw new Error("Nie znaleziono szablonu.");
  }
  const anchorAt = document.getElementById("task-due-at")?.value || document.getElementById("task-remind-at")?.value || "";
  const detail = await api(zbudujAdresZOrganizacja(`/api/task-templates/${templateId}/apply${anchorAt ? `?anchor_at=${encodeURIComponent(anchorAt)}` : ""}`), {
    method: "POST",
    body: JSON.stringify({
      title: template.template_name,
      description: template.template_description || "",
    }),
  });
  pokazPowiadomienie("Utworzono wpis z szablonu.");
  await Promise.all([wczytajZadania(), wczytajPlannerZadan(), wczytajFokusZadan(), wczytajLogi()]);
  if (detail?.task_id) {
    await wczytajSzczegolyZadania(detail.task_id);
  }
  return detail;
}

async function dodajZalacznikDoZadania() {
  if (!stan.wybraneZadanieId || !czyMoznaZapisywac()) {
    return;
  }
  const input = document.getElementById("task-attachment-file");
  const file = input?.files?.[0];
  if (!file) {
    throw new Error("Wybierz plik do dodania.");
  }
  const contentBase64 = await odczytajPlikJakoBase64(file);
  const detail = await api(zbudujAdresZOrganizacja(`/api/tasks/${stan.wybraneZadanieId}/attachments`), {
    method: "POST",
    body: JSON.stringify({
      file_name: file.name,
      content_type: file.type || "application/octet-stream",
      content_base64: contentBase64,
    }),
  });
  if (input) {
    input.value = "";
  }
  pokazPowiadomienie("Dodano zalacznik.");
  await Promise.all([wczytajZadania(), wczytajLogi()]);
  renderujPanelZadania(detail);
}

async function dodajLinkZalacznikaDoZadania() {
  if (!stan.wybraneZadanieId || !czyMoznaZapisywac()) {
    return;
  }
  const titleInput = document.getElementById("task-attachment-link-title");
  const urlInput = document.getElementById("task-attachment-link-url");
  const attachmentUrl = urlInput?.value?.trim() || "";
  const attachmentTitle = titleInput?.value?.trim() || "";
  if (!attachmentUrl) {
    throw new Error("Wpisz adres linku do dodania.");
  }
  const detail = await api(zbudujAdresZOrganizacja(`/api/tasks/${stan.wybraneZadanieId}/attachments`), {
    method: "POST",
    body: JSON.stringify({
      attachment_kind: "link",
      attachment_url: attachmentUrl,
      file_name: attachmentTitle,
      content_type: "text/uri-list",
    }),
  });
  if (titleInput) {
    titleInput.value = "";
  }
  if (urlInput) {
    urlInput.value = "";
  }
  pokazPowiadomienie("Dodano link do zalacznika.");
  await Promise.all([wczytajZadania(), wczytajLogi()]);
  renderujPanelZadania(detail);
}

async function analizujNaturalnePolecenieZadania() {
  if (!czyMoznaZapisywac()) {
    return;
  }
  const field = document.getElementById("task-natural-command");
  const commandText = field?.value?.trim() || "";
  if (!commandText) {
    throw new Error("Wpisz tresc polecenia do analizy.");
  }
  const preview = await api(zbudujAdresZOrganizacja("/api/tasks/parse-natural"), {
    method: "POST",
    body: JSON.stringify({ command_text: commandText }),
  });
  renderujPodgladNaturalnegoPolecenia(preview);
  document.getElementById("task-natural-preview-title")?.focus();
  pokazPowiadomienie("Przygotowano podglad wpisu.");
}

function zastosujPodgladNaturalnegoPolecenia() {
  const payload = pobierzDoprecyzowanyPodgladNaturalnegoPolecenia();
  if (!payload) {
    throw new Error("Najpierw przygotuj podglad polecenia.");
  }
  przygotujNoweZadanie();
  wypelnijFormularzZadaniaZPayload(payload);
  pokazPowiadomienie("Wczytano podglad do formularza.");
}

async function utworzWpisZPodgladuNaturalnegoPolecenia() {
  const payload = pobierzDoprecyzowanyPodgladNaturalnegoPolecenia();
  if (!payload) {
    throw new Error("Najpierw przygotuj podglad polecenia.");
  }
  const wynik = await api(zbudujAdresZOrganizacja("/api/tasks"), {
    method: "POST",
    body: JSON.stringify(payload),
  });
  pokazPowiadomienie("Utworzono wpis z polecenia tekstowego.");
  const field = document.getElementById("task-natural-command");
  if (field) {
    field.value = "";
  }
  renderujPodgladNaturalnegoPolecenia(null);
  await Promise.all([wczytajZadania(), wczytajPlannerZadan(), wczytajFokusZadan(), wczytajPulpit(), wczytajLogi()]);
  await wczytajSzczegolyZadania(wynik.task_id);
}

async function zapiszZmianyFaktury() {
  if (!stan.wybranaFakturaId || !czyMoznaZapisywac()) return;
  const form = document.getElementById("invoice-edit-form");
  const dane = new FormData(form);
  const payload = {};
  for (const [key, value] of dane.entries()) {
    payload[key] = value;
  }

  const result = await api(zbudujAdresZOrganizacja(`/api/invoices/${stan.wybranaFakturaId}`), {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
  const correctionResult = result?.ksef_correction || null;
  if (correctionResult?.mode === "request_created") {
    pokazPowiadomienie("Zapisano zmiany i wyslano prosbe o korekte danych KSeF.");
  } else if (correctionResult?.mode === "applied_directly") {
    pokazPowiadomienie("Zapisano zmiany i zastosowano lokalna korekte danych KSeF.");
  } else {
    pokazPowiadomienie("Zapisano zmiany faktury.");
  }
  await Promise.all([wczytajFaktury(), wczytajPulpit(), wczytajLogi(), wczytajKontrahentow(), wczytajWszystkichKontrahentow()]);
  await wczytajSzczegolyFaktury(stan.wybranaFakturaId);
  if (correctionResult) {
    otworzModalZapisuKsef(correctionResult);
  }
}

async function dodajKomentarzDoFaktury() {
  if (!stan.wybranaFakturaId || !czyMoznaZapisywac()) {
    return;
  }
  const pole = document.getElementById("invoice-comment-text");
  const noteText = pole?.value?.trim() || "";
  if (!noteText) {
    pokazPowiadomienie("Wpisz komentarz do faktury.");
    return;
  }
  await api(zbudujAdresZOrganizacja(`/api/invoices/${stan.wybranaFakturaId}/comments`), {
    method: "POST",
    body: JSON.stringify({ note_text: noteText }),
  });
  pokazPowiadomienie("Dodano komentarz do faktury.");
  if (pole) {
    pole.value = "";
  }
  await Promise.all([wczytajFaktury(), wczytajPulpit(), wczytajLogi()]);
  await wczytajSzczegolyFaktury(stan.wybranaFakturaId);
}

async function potwierdzDuplikat() {
  if (!stan.wybranaFakturaId || !czyMoznaPodejmowacDecyzjeFaktur()) return;
  await api(zbudujAdresZOrganizacja(`/api/invoices/${stan.wybranaFakturaId}/actions/confirm-duplicate`), { method: "POST" });
  pokazPowiadomienie("Potwierdzono duplikat.");
  await Promise.all([wczytajFaktury(), wczytajPulpit(), wczytajLogi()]);
  await wczytajSzczegolyFaktury(stan.wybranaFakturaId);
}

async function odrzucPodejrzenieDuplikatu() {
  if (!stan.wybranaFakturaId || !czyMoznaPodejmowacDecyzjeFaktur()) return;
  await api(zbudujAdresZOrganizacja(`/api/invoices/${stan.wybranaFakturaId}/actions/reject-duplicate`), { method: "POST" });
  pokazPowiadomienie("Faktura zostaĹ‚a oznaczona jako poprawna.");
  await Promise.all([wczytajFaktury(), wczytajPulpit(), wczytajLogi()]);
  await wczytajSzczegolyFaktury(stan.wybranaFakturaId);
}

async function odswiezFakturePoAkcjiObiegu() {
  await Promise.all([wczytajFaktury(), wczytajPulpit(), wczytajLogi()]);
  await wczytajSzczegolyFaktury(stan.wybranaFakturaId);
}

async function oznaczFaktureGotowaDoPrzekazania() {
  if (!stan.wybranaFakturaId || !czyMoznaZapisywac()) return;
  const handoffTarget = window.prompt("Do kogo lub gdzie przekazujemy te fakture?", "") || "";
  const handoffNote = window.prompt("Dodaj krotka notatke do przekazania (opcjonalnie).", "") || "";
  await api(zbudujAdresZOrganizacja(`/api/invoices/${stan.wybranaFakturaId}/actions/mark-ready`), {
    method: "POST",
    body: JSON.stringify({
      handoff_target: handoffTarget,
      handoff_note: handoffNote,
    }),
  });
  pokazPowiadomienie("Faktura jest gotowa do przekazania.");
  await odswiezFakturePoAkcjiObiegu();
}

async function przekazFaktureDalej() {
  if (!stan.wybranaFakturaId || !czyMoznaPodejmowacDecyzjeFaktur()) return;
  const handoffTarget = window.prompt("Do kogo lub gdzie przekazujemy te fakture?", "") || "";
  const handoffNote = window.prompt("Dodaj notatke do przekazania (opcjonalnie).", "") || "";
  await api(zbudujAdresZOrganizacja(`/api/invoices/${stan.wybranaFakturaId}/actions/handoff`), {
    method: "POST",
    body: JSON.stringify({
      handoff_target: handoffTarget,
      handoff_note: handoffNote,
    }),
  });
  pokazPowiadomienie("Faktura zostala przekazana dalej.");
  await odswiezFakturePoAkcjiObiegu();
}

async function zamknijFakture() {
  if (!stan.wybranaFakturaId || !czyMoznaPodejmowacDecyzjeFaktur()) return;
  const reason = (window.prompt("Podaj powod zamkniecia obiegu faktury.", "Dokument zostal zamkniety po przekazaniu.") || "").trim();
  if (!reason) {
    pokazPowiadomienie("Podaj powod zamkniecia faktury.");
    return;
  }
  await api(zbudujAdresZOrganizacja(`/api/invoices/${stan.wybranaFakturaId}/actions/close`), {
    method: "POST",
    body: JSON.stringify({ reason }),
  });
  pokazPowiadomienie("Obieg faktury zostal zamkniety.");
  await odswiezFakturePoAkcjiObiegu();
}

async function ponownieOtworzFakture() {
  if (!stan.wybranaFakturaId || !czyMoznaPodejmowacDecyzjeFaktur()) return;
  const reason = (window.prompt("Dlaczego ponownie otwieramy te fakture?", "") || "").trim();
  if (!reason) {
    pokazPowiadomienie("Podaj powod ponownego otwarcia faktury.");
    return;
  }
  await api(zbudujAdresZOrganizacja(`/api/invoices/${stan.wybranaFakturaId}/actions/reopen`), {
    method: "POST",
    body: JSON.stringify({ reason }),
  });
  pokazPowiadomienie("Faktura wrocila do pracy.");
  await odswiezFakturePoAkcjiObiegu();
}

async function cofnijOstatniaDecyzjeObieguFaktury() {
  if (!stan.wybranaFakturaId) return;
  await api(zbudujAdresZOrganizacja(`/api/invoices/${stan.wybranaFakturaId}/actions/undo-last`), {
    method: "POST",
  });
  pokazPowiadomienie("Cofnieto ostatnia decyzje obiegu.");
  await odswiezFakturePoAkcjiObiegu();
}

async function wykonajImportTestowy(source) {
  if (!czyImportTestowyWlaczony()) {
    pokazPowiadomienie("Import testowy jest wylaczony w tym srodowisku.");
    return;
  }
  if (!czyMoznaZapisywac()) {
    pokazPowiadomienie("Ta rola nie moĹĽe dodawaÄ‡ dokumentĂłw.");
    return;
  }
  if (czyGlobalnyAdministrator() && !stan.wybranaOrganizacjaId) {
    pokazPowiadomienie("Wybierz organizacjÄ™ przed importem testowym.");
    return;
  }
  await api(zbudujAdresZOrganizacja(`/api/import/${source}`), { method: "POST" });
  pokazPowiadomienie(`Dodano przykĹ‚adowÄ… fakturÄ™ ze ĹşrĂłdĹ‚a ${formatujZrodlo(source)}.`);
  await Promise.all([wczytajPulpit(), wczytajFaktury(), wczytajKontrahentow(), wczytajWszystkichKontrahentow(), wczytajLogi()]);
}

async function zapiszUzytkownika() {
  if (!czyMoznaZarzadzacUzytkownikami()) return;

  const userId = document.getElementById("user-id").value.trim();
  const payload = {
    display_name: document.getElementById("user-display-name").value.trim(),
    organization_id: document.getElementById("user-organization-id").value,
    telegram_user_id: document.getElementById("user-telegram-user-id").value.trim(),
    telegram_reminders_enabled: document.getElementById("user-telegram-reminders-enabled").checked,
    role: document.getElementById("user-role").value,
    can_upload_knowledge: document.getElementById("user-can-upload-knowledge").checked,
    is_active: document.getElementById("user-active").value,
  };
  const login = document.getElementById("user-login").value.trim();
  const haslo = document.getElementById("user-password").value.trim();
  let zapisanyUzytkownik = null;

  if (!userId) {
    payload.login = login;
    payload.password = haslo;
    zapisanyUzytkownik = await api("/api/users", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    pokazPowiadomienie(`Utworzono konto ${login}.`);
  } else {
    if (haslo) {
      payload.password = haslo;
    }
    zapisanyUzytkownik = await api(`/api/users/${userId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
    pokazPowiadomienie("Zapisano zmiany konta.");
  }

  if (
    zapisanyUzytkownik &&
    stan.biezacyUzytkownik &&
    Number(zapisanyUzytkownik.user_id) === Number(stan.biezacyUzytkownik.user_id)
  ) {
    stan.biezacyUzytkownik = zapisanyUzytkownik;
    odswiezPasekSesji();
  }

  wyczyscFormularzUzytkownika();
  await Promise.all([wczytajUzytkownikow(), wczytajLogi()]);
}

async function zapiszOrganizacje() {
  if (!czyMoznaZarzadzacOrganizacjami()) return;

  const organizationId = document.getElementById("organization-id").value.trim();
  const communicationProvider = document.getElementById("organization-communication-provider").value;
  if (!organizationId && !czyMoznaTworzycOrganizacje()) {
    pokazPowiadomienie("Tylko WĹ‚aĹ›ciciel systemu moĹĽe tworzyÄ‡ nowe organizacje.");
    return;
  }
  const payload = {
    name: document.getElementById("organization-name").value.trim(),
    slug: document.getElementById("organization-slug").value.trim(),
    module_shortcuts: pobierzSkrotyModulowZFormularza(),
    communication_provider: communicationProvider,
    communication_config: {
      telegram: {
        chat_id: document.getElementById("organization-telegram-chat-id").value.trim(),
        chat_name: document.getElementById("organization-telegram-chat-name").value.trim(),
      },
      slack: {
        workspace_name: document.getElementById("organization-slack-workspace-name").value.trim(),
        channel_id: document.getElementById("organization-slack-channel-id").value.trim(),
        channel_name: document.getElementById("organization-slack-channel-name").value.trim(),
      },
      whatsapp: {
        phone_number: document.getElementById("organization-whatsapp-phone-number").value.trim(),
        display_name: document.getElementById("organization-whatsapp-display-name").value.trim(),
      },
    },
    email_inbox_address: document.getElementById("organization-email-inbox-address").value.trim(),
    email_allowed_sender: document.getElementById("organization-email-allowed-sender").value.trim(),
    email_subject_keyword: document.getElementById("organization-email-subject-keyword").value.trim(),
    email_integration_enabled: document.getElementById("organization-email-integration-enabled").value,
    ksef_company_identifier: document.getElementById("organization-ksef-company-identifier").value.trim(),
    ksef_environment: document.getElementById("organization-ksef-environment").value,
    ksef_integration_enabled: document.getElementById("organization-ksef-integration-enabled").value,
    ksef_correction_delegate_user_id: document.getElementById("organization-ksef-delegate-user-id").value,
    ksef_correction_delegate_expires_at: document.getElementById("organization-ksef-delegate-expires-at").value.trim(),
    is_active: document.getElementById("organization-active").value,
  };
  if (czyWlascicielSystemu()) {
    payload.enabled_modules = document.getElementById("organization-module-manager-assistant").checked
      ? [organizationModuleCodes.managerAssistant]
      : [];
  }
  let zapisanaOrganizacja = null;

  if (!organizationId) {
    zapisanaOrganizacja = await api("/api/organizations", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    pokazPowiadomienie(`Utworzono organizacjÄ™ ${payload.name}.`);
  } else {
    zapisanaOrganizacja = await api(`/api/organizations/${organizationId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
    if (
      stan.biezacyUzytkownik &&
      Number(stan.biezacyUzytkownik.organization_id) === Number(zapisanaOrganizacja.organization_id)
    ) {
      stan.biezacyUzytkownik.organization_name = zapisanaOrganizacja.name;
      stan.biezacyUzytkownik.organization_slug = zapisanaOrganizacja.slug;
      stan.biezacyUzytkownik.organization_modules = Array.isArray(zapisanaOrganizacja.enabled_modules)
        ? zapisanaOrganizacja.enabled_modules
        : [];
      stan.biezacyUzytkownik.organization_module_shortcuts =
        typeof zapisanaOrganizacja.module_shortcuts === "object" && zapisanaOrganizacja.module_shortcuts !== null
          ? zapisanaOrganizacja.module_shortcuts
          : {};
    }
    pokazPowiadomienie("Zapisano zmiany organizacji.");
  }

  renderujWynikiWyszukiwania({ invoices: [], contractors: [] });
  await odswiezDanePoZalogowaniu();
  const odswiezonaOrganizacja = stan.organizacje.find(
    (item) => Number(item.organization_id) === Number(zapisanaOrganizacja?.organization_id)
  );
  if (odswiezonaOrganizacja) {
    wypelnijFormularzOrganizacji(odswiezonaOrganizacja);
  } else {
    wyczyscFormularzOrganizacji();
  }
}

async function testujPolaczenieEmailOrganizacji() {
  if (!czyMoznaZarzadzacOrganizacjami()) return;

  const organizationId = document.getElementById("organization-id").value.trim();
  if (!organizationId) {
    pokazPowiadomienie("Najpierw zapisz organizacje.");
    return;
  }

  const button = document.getElementById("organization-test-email-connection");
  const previousLabel = button.textContent;
  button.textContent = "Testuje...";
  button.classList.add("is-busy");
  odswiezUprawnieniaFormularzaOrganizacji();

  try {
    const result = await api(`/api/organizations/${organizationId}/actions/test-email-connection`, {
      method: "POST",
    });
    const message = result.message || "Polaczenie e-mail zostalo sprawdzone.";
    pokazPowiadomienie(message);
    await Promise.all([wczytajOrganizacje(), wczytajLogi()]);
    if (czyMoznaOtworzycCentrumEmaila()) {
      await wczytajCentrumEmaila();
    }

    const organizacja =
      stan.organizacje.find((item) => Number(item.organization_id) === Number(organizationId)) || null;
    if (organizacja) {
      wypelnijFormularzOrganizacji(organizacja);
      renderujPodsumowanieEmailaOrganizacji(organizacja, `Test polaczenia: ${message}`);
    }
  } finally {
    button.textContent = previousLabel;
    button.classList.remove("is-busy");
    odswiezUprawnieniaFormularzaOrganizacji();
  }
}

async function testujPolaczenieKsefOrganizacji() {
  if (!czyMoznaZarzadzacOrganizacjami()) return;

  const organizationId = document.getElementById("organization-id").value.trim();
  if (!organizationId) {
    pokazPowiadomienie("Najpierw zapisz organizacje.");
    return;
  }

  const button = document.getElementById("organization-test-ksef-connection");
  const previousLabel = button.textContent;
  button.textContent = "Testuje...";
  button.classList.add("is-busy");
  odswiezUprawnieniaFormularzaOrganizacji();

  try {
    const result = await api(`/api/organizations/${organizationId}/actions/test-ksef-connection`, {
      method: "POST",
    });
    const message = result.message || "Polaczenie KSeF zostalo sprawdzone.";
    pokazPowiadomienie(message);
    await Promise.all([wczytajOrganizacje(), wczytajLogi()]);
    if (czyMoznaOtworzycCentrumEmaila()) {
      await wczytajCentrumEmaila();
    }

    const organizacja =
      stan.organizacje.find((item) => Number(item.organization_id) === Number(organizationId)) || null;
    if (organizacja) {
      wypelnijFormularzOrganizacji(organizacja);
      renderujPodsumowanieKsefOrganizacji(organizacja, `Test polaczenia: ${message}`);
    }
  } finally {
    button.textContent = previousLabel;
    button.classList.remove("is-busy");
    odswiezUprawnieniaFormularzaOrganizacji();
  }
}

async function sprawdzEmailOrganizacji() {

  if (!czyMoznaZarzadzacOrganizacjami()) return;

  const organizationId = document.getElementById("organization-id").value.trim();
  if (!organizationId) {
    pokazPowiadomienie("Najpierw zapisz organizacje.");
    return;
  }

  const button = document.getElementById("organization-check-email");
  const previousLabel = button.textContent;
  button.textContent = "Sprawdzam...";
  button.classList.add("is-busy");
  odswiezUprawnieniaFormularzaOrganizacji();

  try {
    const result = await api(`/api/organizations/${organizationId}/actions/check-email`, {
      method: "POST",
    });

    const importedCount = Number(result.imported_count || 0);
    const skippedExistingCount = Number(result.skipped_existing_count || 0);
    const skippedErrorCount = Number(result.skipped_error_count || 0);
    let message = result.message || "Sprawdzono skrzynke e-mail.";

    if (importedCount > 0) {
      message = `Zaimportowano ${importedCount} ${importedCount === 1 ? "nowa fakture" : "nowe faktury"} z e-maila.`;
      if (skippedExistingCount > 0) {
        message += ` Pominieto ${skippedExistingCount} juz znanych dokumentow.`;
      }
      if (skippedErrorCount > 0) {
        message += ` ${skippedErrorCount} dokument(y) wymaga(y) uwagi.`;
      }
    }

    pokazPowiadomienie(message);
    renderujWynikiWyszukiwania({ invoices: [], contractors: [] });
    await Promise.all([
      wczytajOrganizacje(),
      wczytajPulpit(),
      wczytajWszystkichKontrahentow(),
      wczytajKontrahentow(),
      wczytajFaktury(),
      wczytajLogi(),
    ]);
    if (czyMoznaOtworzycCentrumEmaila()) {
      await wczytajCentrumEmaila();
    }

    const odswiezonaOrganizacja = stan.organizacje.find(
      (item) => Number(item.organization_id) === Number(organizationId)
    );
    if (odswiezonaOrganizacja) {
      wypelnijFormularzOrganizacji(odswiezonaOrganizacja);
      await wczytajHistorieImportowEmailaOrganizacji(Number(organizationId));
    }

    if (importedCount > 0) {
      ustawWidok("invoices");
      if (importedCount === 1 && result.invoice?.id) {
        stan.wybranaFakturaId = Number(result.invoice.id);
        await wczytajSzczegolyFaktury(result.invoice.id);
      }
    }
  } finally {
    button.textContent = previousLabel;
    button.classList.remove("is-busy");
    odswiezUprawnieniaFormularzaOrganizacji();
  }
}

function podepnijZdarzenia() {
  if (stan.czyZdarzeniaPodpiete) {
    return;
  }
  stan.czyZdarzeniaPodpiete = true;
  rozpocznijObserwacjePodswietleniaNawigacji();

  document.querySelectorAll(".nav-item").forEach((button) => {
    button.addEventListener("click", () => ustawWidok(button.dataset.view));
  });
  document.querySelectorAll("[data-launch-view]").forEach((button) => {
    button.addEventListener("click", () => ustawWidok(button.dataset.launchView));
  });

  const navCarouselShell = document.getElementById("nav-carousel-shell");
  const navCarouselPrevious = document.getElementById("nav-carousel-prev");
  const navCarouselNext = document.getElementById("nav-carousel-next");
  if (navCarouselPrevious) {
    navCarouselPrevious.addEventListener("click", () => przewinKaruzeleModulow(-1));
  }
  if (navCarouselNext) {
    navCarouselNext.addEventListener("click", () => przewinKaruzeleModulow(1));
  }
  if (navCarouselShell) {
    navCarouselShell.addEventListener("scroll", () => odswiezKaruzeleModulow(), { passive: true });
  }
  window.addEventListener("resize", () => {
    odswiezKaruzeleModulow();
    ustawPozycjeSzybkiegoPaneluPracy();
    ustawPozycjePaneliNaglowka();
  });
  window.addEventListener(
    "scroll",
    () => {
      if (stan.szybkiPanelPracyOtwarty) {
        ustawPozycjeSzybkiegoPaneluPracy();
      }
      if (stan.profilMenuOtwarte || stan.menuWiecejOtwarte) {
        ustawPozycjePaneliNaglowka();
      }
    },
    { passive: true }
  );
  odswiezKaruzeleModulow();

  const quickCalendarToggle = document.getElementById("quick-calendar-toggle");
  const quickCalendarPanel = document.getElementById("quick-calendar-panel");
  const quickCalendarOpenTasks = document.getElementById("quick-calendar-open-tasks");
  if (quickCalendarToggle) {
    quickCalendarToggle.addEventListener("click", (event) => {
      event.stopPropagation();
      stan.szybkiKalendarzOtwarty = !stan.szybkiKalendarzOtwarty;
      renderujSzybkiKalendarz();
    });
  }
  if (quickCalendarOpenTasks) {
    quickCalendarOpenTasks.addEventListener("click", async () => {
      stan.szybkiKalendarzOtwarty = false;
      renderujSzybkiKalendarz();
      ustawWidok("tasks");
      if (czyMoznaKorzystacZMojejPracy()) {
        try {
          await Promise.all([wczytajZadania(), wczytajPlannerZadan(), wczytajFokusZadan()]);
        } catch (error) {
          pokazPowiadomienie(error.message);
        }
      }
    });
  }
  if (quickCalendarPanel) {
    quickCalendarPanel.addEventListener("click", async (event) => {
      const rangeButton = event.target.closest("[data-quick-calendar-range]");
      if (rangeButton) {
        stan.szybkiKalendarzZakres = rangeButton.dataset.quickCalendarRange || "dzis";
        renderujSzybkiKalendarz();
        return;
      }
      const openButton = event.target.closest("[data-quick-calendar-open-task]");
      if (openButton) {
        const taskId = Number(openButton.dataset.quickCalendarOpenTask || 0);
        if (!taskId) {
          return;
        }
        stan.szybkiKalendarzOtwarty = false;
        renderujSzybkiKalendarz();
        ustawWidok("tasks");
        try {
          await wczytajSzczegolyZadania(taskId);
          podswietlDoceloweZadanie(taskId);
        } catch (error) {
          pokazPowiadomienie(error.message);
        }
      }
    });
  }

  const quickWorkspaceLauncher = document.getElementById("quick-workspace-launcher");
  const quickWorkspacePanel = document.getElementById("quick-workspace-panel");
  const quickWorkspaceClose = document.getElementById("quick-workspace-close");
  if (quickWorkspaceLauncher) {
    quickWorkspaceLauncher.addEventListener("click", async (event) => {
      event.stopPropagation();
      if (stan.szybkiPanelPracyOtwarty) {
        zamknijSzybkiPanelPracy();
        return;
      }
      try {
        await otworzSzybkiPanelPracy();
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
    });
  }
  if (quickWorkspaceClose) {
    quickWorkspaceClose.addEventListener("click", () => zamknijSzybkiPanelPracy());
  }
  if (quickWorkspacePanel) {
    quickWorkspacePanel.addEventListener("input", (event) => {
      const target = event.target;
      if (target?.id === "quick-workspace-organization-note-text") {
        const nextValue = String(target.value || "");
        stan.notatkaOrganizacjiTekstRoboczy = nextValue;
        stan.notatkaOrganizacjiBrudna = nextValue !== stan.notatkaOrganizacjiOstatniTekst;
        if (!stan.notatkaOrganizacjiBrudna) {
          stan.notatkaOrganizacjiMaNowszaWersje = false;
        }
        renderujNotatkeOrganizacji(stan.notatkaOrganizacji);
        return;
      }
      if (target?.id === "quick-workspace-personal-note-text") {
        const nextValue = String(target.value || "");
        stan.notatkaOsobistaTekstRoboczy = nextValue;
        stan.notatkaOsobistaBrudna = nextValue !== stan.notatkaOsobistaOstatniTekst;
        if (!stan.notatkaOsobistaBrudna) {
          stan.notatkaOsobistaMaNowszaWersje = false;
        }
        renderujNotatkeOsobista(stan.notatkaOsobista);
      }
    });
    quickWorkspacePanel.addEventListener("click", async (event) => {
      event.stopPropagation();
      const sectionButton = event.target.closest("[data-quick-workspace-section]");
      if (sectionButton) {
        try {
          await przelaczSekcjeSzybkiegoPanelu(sectionButton.dataset.quickWorkspaceSection || "organization-note");
        } catch (error) {
          pokazPowiadomienie(error.message);
        }
        return;
      }
      if (event.target.closest("#quick-workspace-organization-note-save")) {
        try {
          await zapiszNotatkeOrganizacji();
          oznaczSekcjeSzybkiegoPaneluJakoOdczytana("organization-note");
        } catch (error) {
          pokazPowiadomienie(error.message);
        }
        return;
      }
      if (event.target.closest("#quick-workspace-personal-note-save")) {
        try {
          await zapiszNotatkeOsobista();
        } catch (error) {
          pokazPowiadomienie(error.message);
        }
        return;
      }
      const rangeButton = event.target.closest("[data-quick-workspace-range]");
      if (rangeButton) {
        stan.szybkiPanelKalendarzaTryb = "zakres";
        stan.szybkiPanelKalendarzaZakres = rangeButton.dataset.quickWorkspaceRange || "dzis";
        renderujSzybkiPanelPracy();
        return;
      }
      const monthModeButton = event.target.closest("[data-quick-workspace-calendar-mode]");
      if (monthModeButton) {
        stan.szybkiPanelKalendarzaTryb = "miesiac";
        renderujSzybkiPanelPracy();
        return;
      }
      const calendarNavButton = event.target.closest("[data-quick-workspace-calendar-nav]");
      if (calendarNavButton) {
        const delta = Number(calendarNavButton.dataset.quickWorkspaceCalendarNav || 0);
        const anchor = pobierzKotwiceSzybkiegoPaneluKalendarza();
        stan.szybkiPanelKalendarzaKotwica = new Date(anchor.getFullYear(), anchor.getMonth() + delta, 1);
        stan.szybkiPanelKalendarzaTryb = "miesiac";
        renderujSzybkiPanelPracy();
        return;
      }
      const calendarDayButton = event.target.closest("[data-quick-workspace-calendar-day]");
      if (calendarDayButton) {
        const dayKey = String(calendarDayButton.dataset.quickWorkspaceCalendarDay || "").trim();
        if (!dayKey) {
          return;
        }
        const [year, month, day] = dayKey.split("-").map((item) => Number(item));
        const clickedDate = new Date(year, (month || 1) - 1, day || 1, 12, 0, 0, 0);
        const today = sklonujDateNaPolnoc(new Date());
        const tomorrow = dodajDniDoDaty(today, 1);
        if (kalendarzKluczDnia(clickedDate) === kalendarzKluczDnia(today)) {
          stan.szybkiPanelKalendarzaZakres = "dzis";
        } else if (kalendarzKluczDnia(clickedDate) === kalendarzKluczDnia(tomorrow)) {
          stan.szybkiPanelKalendarzaZakres = "jutro";
        } else {
          stan.szybkiPanelKalendarzaZakres = "tydzien";
        }
        stan.szybkiPanelKalendarzaTryb = "zakres";
        renderujSzybkiPanelPracy();
        return;
      }
      const taskRangeButton = event.target.closest("[data-quick-workspace-task-range]");
      if (taskRangeButton) {
        stan.szybkiPanelZadanZakres = taskRangeButton.dataset.quickWorkspaceTaskRange || "dzis";
        renderujSzybkiPanelPracy();
        return;
      }
      const openViewButton = event.target.closest("[data-quick-workspace-open-view]");
      if (openViewButton) {
        const view = openViewButton.dataset.quickWorkspaceOpenView || "tasks";
        zamknijSzybkiPanelPracy();
        ustawWidok(view);
        if (view === "tasks" && czyMoznaKorzystacZMojejPracy()) {
          try {
            await Promise.all([wczytajZadania(), wczytajPlannerZadan(), wczytajFokusZadan()]);
          } catch (error) {
            pokazPowiadomienie(error.message);
          }
        } else if (view === "knowledge" && typeof wczytajBazeWiedzy === "function") {
          try {
            await wczytajBazeWiedzy();
          } catch (error) {
            pokazPowiadomienie(error.message);
          }
        }
        return;
      }
      const openKnowledgeDocumentButton = event.target.closest("[data-quick-workspace-open-knowledge-document]");
      if (openKnowledgeDocumentButton) {
        const knowledgeDocumentId = Number(openKnowledgeDocumentButton.dataset.quickWorkspaceOpenKnowledgeDocument || 0);
        if (!knowledgeDocumentId) {
          return;
        }
        zamknijSzybkiPanelPracy();
        ustawWidok("knowledge");
        try {
          if (typeof ustawFokusKolejkiDokumentowFirmowych === "function") {
            ustawFokusKolejkiDokumentowFirmowych("knowledge_my_queue");
          }
          if (typeof wczytajBazeWiedzy === "function") {
            await wczytajBazeWiedzy();
          }
          if (typeof ustawWybranyDokumentBazyWiedzy === "function") {
            ustawWybranyDokumentBazyWiedzy(knowledgeDocumentId, { forceDetail: true });
          }
        } catch (error) {
          pokazPowiadomienie(error.message);
        }
        return;
      }
      const quickDecisionButton = event.target.closest("[data-knowledge-open-decision-modal][data-knowledge-decision-action]");
      if (quickDecisionButton) {
        try {
          await otworzModalDecyzjiDokumentuBazyWiedzy(
            quickDecisionButton.dataset.knowledgeOpenDecisionModal,
            quickDecisionButton.dataset.knowledgeDecisionAction
          );
        } catch (error) {
          pokazPowiadomienie(error.message);
        }
        return;
      }
      const quickTaskFromDocumentButton = event.target.closest("[data-knowledge-open-task-modal]");
      if (quickTaskFromDocumentButton) {
        try {
          await otworzModalZadaniaZDokuBazyWiedzy(quickTaskFromDocumentButton.dataset.knowledgeOpenTaskModal);
        } catch (error) {
          pokazPowiadomienie(error.message);
        }
        return;
      }
      const openTaskButton = event.target.closest("[data-quick-workspace-open-task]");
      if (openTaskButton) {
        const taskId = Number(openTaskButton.dataset.quickWorkspaceOpenTask || 0);
        const source = String(openTaskButton.dataset.quickWorkspaceOpenSource || "").trim().toLowerCase();
        if (!taskId) {
          return;
        }
        if (source === "calendar" || source === "tasks") {
          oznaczElementSzybkiegoPaneluJakoPrzeczytany(source, taskId);
        }
        zamknijSzybkiPanelPracy();
        ustawWidok("tasks");
        try {
          await wczytajSzczegolyZadania(taskId);
          podswietlDoceloweZadanie(taskId);
        } catch (error) {
          pokazPowiadomienie(error.message);
        }
      }
    });
  }

  document.querySelectorAll(".action-import").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        await wykonajImportTestowy(button.dataset.source);
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
    });
  });

  document.getElementById("invoice-filters").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await wczytajFaktury();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  podlaczAutomatyczneFiltrowanieFormularza("invoice-filters", "invoiceFilterApplyTimeoutId", wczytajFaktury);

  document.getElementById("reset-invoice-filters").addEventListener("click", () => wyczyscFiltryFaktur(true));
  document.getElementById("toggle-invoice-filters").addEventListener("click", () => przelaczWidocznoscFiltrowFaktur());

  document.getElementById("task-filters").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await wczytajZadania();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  podlaczAutomatyczneFiltrowanieFormularza("task-filters", "taskFilterApplyTimeoutId", wczytajZadania);

  document.getElementById("reset-task-filters").addEventListener("click", () => wyczyscFiltryZadan(true));
  document.getElementById("new-task-button").addEventListener("click", () => przygotujNoweZadanie());
  const taskQuickAddOpenButton = document.getElementById("task-quick-add-open");
  if (taskQuickAddOpenButton) {
    taskQuickAddOpenButton.addEventListener("click", () => otworzSzybkiWpis());
  }
  const taskQuickAddFab = document.getElementById("task-quick-add-fab");
  if (taskQuickAddFab) {
    taskQuickAddFab.addEventListener("click", () => otworzSzybkiWpis());
  }
  const taskQuickAddCloseButton = document.getElementById("task-quick-add-close");
  if (taskQuickAddCloseButton) {
    taskQuickAddCloseButton.addEventListener("click", () => zamknijSzybkiWpis());
  }
  const taskQuickAddBackdrop = document.getElementById("task-quick-add-backdrop");
  if (taskQuickAddBackdrop) {
    taskQuickAddBackdrop.addEventListener("click", () => zamknijSzybkiWpis());
  }
  const taskQuickAddForm = document.getElementById("task-quick-add-form");
  if (taskQuickAddForm) {
    taskQuickAddForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      try {
        await zapiszSzybkiWpis();
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
    });
  }
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      if (!document.getElementById("task-calendar-conflict-modal")?.classList.contains("hidden")) {
        zamknijModalKonfliktuKalendarza(false);
      }
      zamknijSzybkiWpis();
      if (stan.szybkiKalendarzOtwarty) {
        stan.szybkiKalendarzOtwarty = false;
        renderujSzybkiKalendarz();
      }
      if (stan.szybkiPanelPracyOtwarty) {
        zamknijSzybkiPanelPracy();
      }
      if (stan.profilMenuOtwarte || stan.menuWiecejOtwarte) {
        zamknijMenuNaglowka();
      }
      return;
    }
    obsluzSkrotyModulow(event);
  });
  document.addEventListener("click", (event) => {
    const target = event.target instanceof Element ? event.target : null;
    if (!target) {
      return;
    }
    const clickedInsideTopbarMenu = target.closest(".topbar-menu-shell, .topbar-meta-grid, .topbar-menu-panel");
    if (!clickedInsideTopbarMenu && (stan.profilMenuOtwarte || stan.menuWiecejOtwarte)) {
      zamknijMenuNaglowka();
    }
    if (stan.szybkiKalendarzOtwarty) {
      const clickedInsidePanel = target.closest("#quick-calendar-panel");
      const clickedToggle = target.closest("#quick-calendar-toggle");
      if (!clickedInsidePanel && !clickedToggle) {
        stan.szybkiKalendarzOtwarty = false;
        renderujSzybkiKalendarz();
      }
    }
    if (stan.szybkiPanelPracyOtwarty) {
      const clickedInsideQuickWorkspace = target.closest("#quick-workspace-panel");
      const clickedQuickWorkspaceToggle = target.closest("#quick-workspace-launcher");
      if (!clickedInsideQuickWorkspace && !clickedQuickWorkspaceToggle) {
        zamknijSzybkiPanelPracy();
      }
    }
  });
  document.addEventListener("click", async (event) => {
    const approvalToggle = event.target.closest("[data-approval-attachments-toggle]");
    if (approvalToggle) {
      const approvalId = Number(approvalToggle.dataset.approvalAttachmentsToggle || 0);
      const panel = document.querySelector(`[data-approval-attachments-panel="${approvalId}"]`);
      if (!panel) return;
      const isHidden = panel.classList.contains("hidden");
      panel.classList.toggle("hidden");
      if (isHidden) {
        await wczytajZalacznikiAkceptacji(approvalId);
      }
      return;
    }
    const approvalLinkButton = event.target.closest("[data-approval-attachment-link-submit]");
    if (approvalLinkButton) {
      const form = approvalLinkButton.closest("[data-approval-attachment-form]");
      const approvalId = Number(form?.dataset.approvalAttachmentForm || 0);
      try {
        await dodajZalacznikAkceptacji(approvalId, {
          attachment_kind: "link",
          file_name: form?.querySelector("[data-approval-attachment-link-title]")?.value.trim() || "",
          attachment_url: form?.querySelector("[data-approval-attachment-link-url]")?.value.trim() || "",
        });
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
    }
  });
  document.addEventListener("submit", async (event) => {
    const approvalForm = event.target.closest("[data-approval-attachment-form]");
    if (!approvalForm) {
      return;
    }
    event.preventDefault();
    try {
      const approvalId = Number(approvalForm.dataset.approvalAttachmentForm || 0);
      const fileInput = approvalForm.querySelector("[data-approval-attachment-file]");
      const file = fileInput?.files?.[0];
      if (!file) {
        throw new Error("Wybierz plik do zalacznika.");
      }
      await dodajZalacznikAkceptacji(approvalId, {
        attachment_kind: "file",
        file_name: file.name,
        content_type: file.type,
        content_base64: await odczytajPlikJakoBase64(file),
      });
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  document.getElementById("analyze-task-command").addEventListener("click", async () => {
    try {
      await analizujNaturalnePolecenieZadania();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  document.getElementById("apply-task-command-preview").addEventListener("click", () => {
    try {
      zastosujPodgladNaturalnegoPolecenia();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  document.getElementById("create-task-from-preview").addEventListener("click", async () => {
    try {
      await utworzWpisZPodgladuNaturalnegoPolecenia();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  renderujPodgladNaturalnegoPolecenia(null);
  renderujStatusDyktowaniaNaturalnegoPolecenia(
    czyMoznaDyktowacNaturalnePolecenie()
      ? "Mozesz podyktowac tresc wpisu i sprawdzic podglad przed zapisaniem."
      : "Ta przegladarka nie obsluguje dyktowania glosowego."
  );
  document.getElementById("start-task-natural-voice").addEventListener("click", () => {
    try {
      uruchomDyktowanieNaturalnegoPolecenia();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  document.getElementById("stop-task-natural-voice").addEventListener("click", () => {
    try {
      zatrzymajDyktowanieNaturalnegoPolecenia();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });

  document.getElementById("user-calendar-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await zapiszKalendarzUzytkownika();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });

  document.getElementById("reset-user-calendar-form").addEventListener("click", () => {
    wyczyscFormularzKalendarzaUzytkownika();
  });

  document.getElementById("delete-user-calendar-button").addEventListener("click", async () => {
    try {
      await usunKalendarzUzytkownika();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });

  document.getElementById("user-calendar-provider").addEventListener("change", () => {
    odswiezWidocznoscPolGoogleKalendarza();
  });

  document.getElementById("connect-google-calendar").addEventListener("click", async () => {
    try {
      await rozpocznijPolaczenieGoogleKalendarza();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });

  document.getElementById("refresh-google-calendars").addEventListener("click", async () => {
    try {
      await odswiezPolaczenieGoogleKalendarza(false);
      pokazPowiadomienie("Odswiezono liste kalendarzy Google.");
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });

  document.getElementById("disconnect-google-calendar").addEventListener("click", async () => {
    try {
      await odlaczGoogleKalendarz();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });

  document.getElementById("approve-user-google-calendar").addEventListener("click", async () => {
    try {
      await zatwierdzGoogleKalendarzUzytkownika();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });

  document.getElementById("reject-user-google-calendar").addEventListener("click", async () => {
    try {
      await odrzucGoogleKalendarzUzytkownika();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });

  document.getElementById("assign-user-organization-calendar").addEventListener("click", async () => {
    try {
      await przypiszKalendarzOrganizacjiUzytkownikowi();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });

  document.getElementById("remove-user-organization-calendar").addEventListener("click", async () => {
    try {
      await usunPrzypisanieKalendarzaOrganizacji();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });

  document.getElementById("user-organization-calendar-select").addEventListener("change", () => {
    const selectedUser = stan.uzytkownicy.find(
      (item) => Number(item.user_id) === Number(stan.wybranyUzytkownikId)
    );
    renderujPanelGoogleKalendarzaUzytkownika(selectedUser || null);
  });

  document.getElementById("user-reminder-preferences-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await zapiszUstawieniaPrzypomnienUzytkownika();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });

  document.getElementById("dispatch-task-reminders").addEventListener("click", async () => {
    try {
      await wymusWysylkePrzypomnien();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });

  const refreshTaskRemindersButton = document.getElementById("refresh-task-reminders");
  if (refreshTaskRemindersButton) {
    refreshTaskRemindersButton.addEventListener("click", async () => {
      try {
        await wczytajStatusPrzypomnien();
        pokazPowiadomienie("Odswiezono status outboxa i workerow.");
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
    });
  }
  document.querySelectorAll("[data-task-reminder-outbox-filter]").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        ustawFiltrOutboxaPrzypomnien(button.dataset.taskReminderOutboxFilter || "all");
        pokazPowiadomienie("Zmieniono filtr outboxa.");
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
    });
  });

  document.getElementById("billing-school-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await zapiszSzkoleRozliczen();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });

  document.getElementById("billing-payer-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await zapiszPlatnikaRozliczen();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });

  document.getElementById("billing-student-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await zapiszUczniaRozliczen();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });

  document.getElementById("billing-model-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await zapiszModelRozliczen();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });

  document.getElementById("billing-charge-generator-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await generujNaleznosciRozliczen();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });

  document.getElementById("billing-manual-match-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await dopasujPlatnoscRecznie();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });

  document.getElementById("billing-match-payer-id")?.addEventListener("change", () => {
    zbudujOpcjeNaleznosciDoDopasowania();
    odswiezPomocDopasowaniaPlatnosci();
  });

  document.getElementById("billing-student-payer-id")?.addEventListener("change", () => {
    odswiezPowiazanieRodzinyWUczniu({ source: "payer" });
  });

  document.getElementById("billing-student-payer-phone")?.addEventListener("input", () => {
    odswiezPowiazanieRodzinyWUczniu({ source: "phone" });
  });

  document.getElementById("billing-student-model-id")?.addEventListener("change", (event) => {
    const modelId = Number(event.target.value || 0);
    const lessonDayInput = document.getElementById("billing-student-lesson-day");
    if (!lessonDayInput || lessonDayInput.value.trim()) {
      return;
    }
    const model = stan.modeleRozliczen.find((item) => Number(item.billing_model_id) === modelId);
    if (model?.lesson_day) {
      lessonDayInput.value = model.lesson_day;
    }
  });

  document.getElementById("billing-match-transaction-id")?.addEventListener("change", () => {
    odswiezPomocDopasowaniaPlatnosci({ ustawDomyslnaKwote: true });
  });

  document.getElementById("billing-match-charge-id")?.addEventListener("change", () => {
    odswiezPomocDopasowaniaPlatnosci({ ustawDomyslnaKwote: true });
  });

  document.getElementById("billing-bank-account-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await zapiszRachunekBankowy();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });

  document.getElementById("billing-statement-import-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await importujWyciagCsv();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });

  document.getElementById("contractor-search").addEventListener("input", async (event) => {
    stan.filtryKontrahentow.szukaj = event.target.value.trim();
    zaplanujAutomatyczneFiltrowanie("contractorFilterApplyTimeoutId", wczytajKontrahentow, 300);
  });

  document.getElementById("global-search").addEventListener("input", async (event) => {
    const fraza = event.target.value.trim();
    if (!fraza) {
      renderujWynikiWyszukiwania({ invoices: [], contractors: [] });
      return;
    }
    if (!stan.biezacyUzytkownik) {
      return;
    }
    try {
      const results = await api(zbudujAdresZOrganizacja(`/api/search?q=${encodeURIComponent(fraza)}`));
      renderujWynikiWyszukiwania(results);
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });

  const obsluzPrzelacznikProfilu = (event) => {
    event.stopPropagation();
    stan.profilMenuOtwarte = !stan.profilMenuOtwarte;
    if (stan.profilMenuOtwarte) {
      stan.menuWiecejOtwarte = false;
    }
    renderujMenuNaglowka();
  };
  const obsluzPrzelacznikWiecej = (event) => {
    event.stopPropagation();
    stan.menuWiecejOtwarte = !stan.menuWiecejOtwarte;
    if (stan.menuWiecejOtwarte) {
      stan.profilMenuOtwarte = false;
    }
    renderujMenuNaglowka();
  };

  document.addEventListener("click", (event) => {
    const target = event.target instanceof Element ? event.target : null;
    if (!target) {
      return;
    }
    const profileToggleClicked = target.closest("#profile-menu-toggle");
    if (profileToggleClicked) {
      obsluzPrzelacznikProfilu(event);
      return;
    }
    const moreToggleClicked = target.closest("#topbar-more-toggle");
    if (moreToggleClicked) {
      obsluzPrzelacznikWiecej(event);
    }
  });

  document.getElementById("organization-shared-note-text")?.addEventListener("input", (event) => {
    const nextValue = String(event.target.value || "");
    stan.notatkaOrganizacjiTekstRoboczy = nextValue;
    stan.notatkaOrganizacjiBrudna = nextValue !== stan.notatkaOrganizacjiOstatniTekst;
    if (!stan.notatkaOrganizacjiBrudna) {
      stan.notatkaOrganizacjiMaNowszaWersje = false;
    }
    renderujNotatkeOrganizacji(stan.notatkaOrganizacji);
  });

  document.getElementById("organization-shared-note-save")?.addEventListener("click", async () => {
    try {
      await zapiszNotatkeOrganizacji();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });

  document.getElementById("organization-switcher").addEventListener("change", async (event) => {
    stan.wybranaOrganizacjaId = event.target.value;
    stan.czyZakresOrganizacjiZainicjalizowany = true;
    stan.menuWiecejOtwarte = false;
    odswiezPasekSesji();
    try {
      if (typeof wyczyscWyszukiwanieGlobalne === "function") {
        wyczyscWyszukiwanieGlobalne({ resetToken: true });
      } else {
        renderujWynikiWyszukiwania({ invoices: [], contractors: [] });
      }
      await odswiezDanePoZalogowaniu();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });

  document.getElementById("login-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const login = document.getElementById("login-input").value.trim();
    const password = document.getElementById("password-input").value;
    try {
      await zalogujDoSystemu(login, password);
      document.getElementById("password-input").value = "";
      pokazPowiadomienie("Zalogowano do systemu.");
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });

  document.getElementById("quick-login-buttons")?.addEventListener("click", async (event) => {
    const przycisk = event.target.closest("[data-quick-login-index]");
    if (!przycisk) {
      return;
    }
    await zalogujSzybkimKontemDemo(Number(przycisk.dataset.quickLoginIndex));
  });

  document.getElementById("logout-button").addEventListener("click", async () => {
    try {
      zamknijMenuNaglowka();
      await wylogujZSystemu();
      pokazPowiadomienie("Wylogowano z systemu.");
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });

  document.getElementById("knowledge-upload-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await zapiszDokumentWiedzy();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });

  document.getElementById("knowledge-sync-button").addEventListener("click", async () => {
    try {
      await synchronizujBazeWiedzy();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });

  document.getElementById("knowledge-file").addEventListener("change", (event) => {
    const plik = event.target.files?.[0];
    const poleTytulu = document.getElementById("knowledge-title");
    if (plik && poleTytulu && !poleTytulu.value.trim()) {
      poleTytulu.value = plik.name.replace(/\.[^.]+$/, "").replace(/[_-]+/g, " ").trim();
    }
    stan.ostatniImportBazyWiedzy = null;
    odswiezPanelImportuBazyWiedzy();
  });

  document.getElementById("knowledge-title").addEventListener("input", () => {
    stan.ostatniImportBazyWiedzy = null;
    odswiezPanelImportuBazyWiedzy();
  });

  document.getElementById("knowledge-content").addEventListener("input", () => {
    stan.ostatniImportBazyWiedzy = null;
    odswiezPanelImportuBazyWiedzy();
  });

  document.getElementById("knowledge-question-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await zapytajBazeWiedzy();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });

  document.getElementById("user-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await zapiszUzytkownika();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });

  document.getElementById("user-role").addEventListener("change", () => {
    ustawDomyslneUprawnienieBazyWiedzyDlaRoli();
    if (!stan.wybranyUzytkownikId) {
      renderujCapabilitiesFormularzaUzytkownika();
      ustawCapabilitiesFormularzaUzytkownika(
        pobierzDomyslneCapabilitiesDlaRoli(document.getElementById("user-role").value || "operator")
      );
    }
  });

  renderujMenuNaglowka();

  document.getElementById("user-organization-id").addEventListener("change", async () => {
    const selectedUser = stan.uzytkownicy.find(
      (item) => Number(item.user_id) === Number(stan.wybranyUzytkownikId)
    );
    const organizationId = document.getElementById("user-organization-id").value || null;
    try {
      await wczytajKalendarzeOrganizacjiDoPrzypisania(organizationId);
      renderujPanelGoogleKalendarzaUzytkownika(
        selectedUser
          ? { ...selectedUser, organization_id: organizationId }
          : { user_id: stan.wybranyUzytkownikId, organization_id: organizationId }
      );
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  document.getElementById("invoice-saved-view-form")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await zapiszWidokFaktur();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  document.getElementById("invoice-saved-view-reset")?.addEventListener("click", () => {
    wyczyscFormularzWidokuFaktur();
    renderujWidokiFaktur();
  });
  document.getElementById("invoice-saved-view-apply-selected")?.addEventListener("click", async () => {
    try {
      await zastosujWybranyWidokFaktur();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  document.getElementById("invoice-saved-view-delete")?.addEventListener("click", async () => {
    try {
      await usunWidokFaktur();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });

  window.addEventListener("message", async (event) => {
    if (event?.data?.type === "google-calendar-connected") {
      try {
        await Promise.all([
          odswiezPolaczenieGoogleKalendarza(true),
          wczytajKalendarzeUzytkownika(),
          czyMoznaZarzadzacUzytkownikami() ? wczytajUzytkownikow() : Promise.resolve(),
        ]);
        wyczyscFormularzKalendarzaUzytkownika();
        pokazPowiadomienie("Konto Google zapisano. Moze jeszcze wymagac zatwierdzenia przez administratora.");
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
      return;
    }
    if (event?.data?.type === "email-google-connected") {
      try {
        await Promise.all([wczytajMeta(), wczytajCentrumEmaila(), wczytajLogi()]);
        pokazPowiadomienie("Polaczono centralna skrzynke Google Workspace.");
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
    }
  });
  document.getElementById("user-can-upload-knowledge").addEventListener("change", () => odswiezCapabilityFormularzaUzytkownika());
  document.getElementById("user-capabilities-list").addEventListener("change", (event) => {
    if (event.target?.matches?.('[data-user-capability]')) {
      const uploadCheckbox = document.getElementById("user-can-upload-knowledge");
      if (uploadCheckbox) {
        uploadCheckbox.checked = pobierzZaznaczoneCapabilitiesZFormularzaUzytkownika().includes("knowledge.upload");
      }
    }
  });
  document.getElementById("reset-user-form").addEventListener("click", () => wyczyscFormularzUzytkownika());

  document.getElementById("organization-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await zapiszOrganizacje();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });

  document.getElementById("organization-test-email-connection").addEventListener("click", async () => {
    try {
      await testujPolaczenieEmailOrganizacji();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  document.getElementById("organization-check-email").addEventListener("click", async () => {
    try {
      await sprawdzEmailOrganizacji();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  document.getElementById("organization-test-ksef-connection").addEventListener("click", async () => {
    try {
      await testujPolaczenieKsefOrganizacji();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  document.getElementById("organization-check-ksef").addEventListener("click", async () => {
    try {
      await sprawdzKsefOrganizacji();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  document.getElementById("email-center-google-connect").addEventListener("click", async () => {
    try {
      await polaczGoogleEmail();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  document.getElementById("email-center-google-disconnect").addEventListener("click", async () => {
    try {
      await rozlaczGoogleEmail();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  document.getElementById("email-center-refresh").addEventListener("click", async () => {
    try {
      await Promise.all([wczytajMeta(), wczytajCentrumEmaila()]);
      pokazPowiadomienie("Odswiezono centrum integracji.");
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  document.getElementById("invoice-ksef-save-modal-close")?.addEventListener("click", () => {
    zamknijModalZapisuKsef();
  });
  document.getElementById("invoice-ksef-save-modal-close-top")?.addEventListener("click", () => {
    zamknijModalZapisuKsef();
  });
  document.getElementById("invoice-compare-modal-close")?.addEventListener("click", () => {
    zamknijModalPorownaniaFaktur();
  });
  document.getElementById("invoice-compare-modal-close-top")?.addEventListener("click", () => {
    zamknijModalPorownaniaFaktur();
  });
  document.getElementById("invoice-compare-modal")?.addEventListener("click", (event) => {
    if (event.target?.id === "invoice-compare-modal") {
      zamknijModalPorownaniaFaktur();
    }
  });
  document.getElementById("invoice-preview-modal-close")?.addEventListener("click", () => {
    zamknijModalPodgladuFaktury();
  });
  document.getElementById("invoice-preview-modal-close-top")?.addEventListener("click", () => {
    zamknijModalPodgladuFaktury();
  });
  document.getElementById("invoice-preview-modal-open-detail")?.addEventListener("click", async () => {
    const invoiceId = Number(stan.podgladFaktury?.invoice?.id || 0);
    if (!invoiceId) {
      return;
    }
    zamknijModalPodgladuFaktury();
    await wczytajSzczegolyFaktury(invoiceId);
    document.getElementById("invoice-detail")?.scrollIntoView({ behavior: "smooth", block: "start" });
  });
  document.getElementById("invoice-preview-modal")?.addEventListener("click", (event) => {
    if (event.target?.id === "invoice-preview-modal") {
      zamknijModalPodgladuFaktury();
    }
  });
  document.getElementById("task-calendar-conflict-modal-cancel")?.addEventListener("click", () => {
    zamknijModalKonfliktuKalendarza(false);
  });
  document.getElementById("task-calendar-conflict-modal-close-top")?.addEventListener("click", () => {
    zamknijModalKonfliktuKalendarza(false);
  });
  document.getElementById("task-calendar-conflict-modal-confirm")?.addEventListener("click", () => {
    zamknijModalKonfliktuKalendarza(true);
  });
  document.getElementById("task-calendar-conflict-modal")?.addEventListener("click", (event) => {
    if (event.target?.id === "task-calendar-conflict-modal") {
      zamknijModalKonfliktuKalendarza(false);
    }
  });
  document.getElementById("reset-organization-form").addEventListener("click", () => wyczyscFormularzOrganizacji());
  document.getElementById("system-communication-settings")?.addEventListener("click", async (event) => {
    const button = event.target?.closest?.("[data-system-communication-action]");
    if (!button) {
      return;
    }
    try {
      if (button.dataset.systemCommunicationAction === "save") {
        await zapiszUstawieniaKomunikatorowSystemowych();
        return;
      }
      if (button.dataset.systemCommunicationAction === "clear-provider") {
        await wyczyscUstawieniaKomunikatoraSystemowego(button.dataset.provider || "");
      }
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  renderujPolaSkrotowModulowOrganizacji({});
  renderujPolaKomunikatoraOrganizacji();
  [
    "organization-name",
    "organization-slug",
    "organization-communication-provider",
    "organization-telegram-chat-id",
    "organization-telegram-chat-name",
    "organization-slack-workspace-name",
    "organization-slack-channel-id",
    "organization-slack-channel-name",
    "organization-whatsapp-phone-number",
    "organization-whatsapp-display-name",
    "organization-module-manager-assistant",
    "organization-email-inbox-address",
    "organization-email-allowed-sender",
    "organization-email-subject-keyword",
    "organization-email-integration-enabled",
    "organization-ksef-company-identifier",
    "organization-ksef-environment",
    "organization-ksef-integration-enabled",
    "organization-ksef-delegate-user-id",
    "organization-ksef-delegate-expires-at",
    "organization-active",
  ].forEach((elementId) => {
    const element = document.getElementById(elementId);
    const eventName = element.tagName === "SELECT" ? "change" : "input";
    element.addEventListener(eventName, () => {
      const organizationPreview = {
        organization_id: document.getElementById("organization-id").value.trim() || null,
        communication_provider: document.getElementById("organization-communication-provider").value,
        communication_provider_label:
          document.getElementById("organization-communication-provider").selectedOptions?.[0]?.textContent || "Telegram",
        communication_target_summary:
          document.getElementById("organization-communication-provider").value === "telegram"
            ? document.getElementById("organization-telegram-chat-name").value.trim() ||
              document.getElementById("organization-telegram-chat-id").value.trim()
            : document.getElementById("organization-communication-provider").value === "slack"
              ? document.getElementById("organization-slack-channel-name").value.trim() ||
                document.getElementById("organization-slack-channel-id").value.trim() ||
                document.getElementById("organization-slack-workspace-name").value.trim()
              : document.getElementById("organization-whatsapp-display-name").value.trim() ||
                document.getElementById("organization-whatsapp-phone-number").value.trim(),
        email_inbox_address: document.getElementById("organization-email-inbox-address").value.trim(),
        email_allowed_sender: document.getElementById("organization-email-allowed-sender").value.trim(),
        email_subject_keyword: document.getElementById("organization-email-subject-keyword").value.trim(),
        email_integration_enabled: document.getElementById("organization-email-integration-enabled").value,
        email_last_checked_at: "",
        email_last_check_status: "",
        email_last_connection_tested_at: "",
        email_last_connection_status: "",
        ksef_company_identifier: document.getElementById("organization-ksef-company-identifier").value.trim(),
        ksef_environment: document.getElementById("organization-ksef-environment").value,
        ksef_integration_enabled: document.getElementById("organization-ksef-integration-enabled").value,
        ksef_correction_delegate_user_id: document.getElementById("organization-ksef-delegate-user-id").value,
        ksef_correction_delegate_user: document.getElementById("organization-ksef-delegate-user-id").value
          ? {
              display_name:
                document.getElementById("organization-ksef-delegate-user-id").selectedOptions?.[0]?.textContent || "",
            }
          : null,
        ksef_correction_delegate_expires_at: document.getElementById("organization-ksef-delegate-expires-at").value,
        ksef_last_checked_at: "",
        ksef_last_check_status: "",
        ksef_last_connection_tested_at: "",
        ksef_last_connection_status: "",
      };
      renderujPolaKomunikatoraOrganizacji();
      renderujPodsumowanieEmailaOrganizacji(organizationPreview);
      renderujPodsumowanieKsefOrganizacji(organizationPreview);
      odswiezUprawnieniaFormularzaOrganizacji();
    });
  });
  document.getElementById("user-calendar-kind").addEventListener("change", () => {
    odswiezWidocznoscPowiazanejOrganizacjiKalendarza();
  });
  document.getElementById("enable-browser-notifications").addEventListener("click", async () => {
    try {
      await wlaczAlertyPrzegladarki();
      pokazPowiadomienie("Wlaczono alerty przegladarki.");
      await odswiezAlertyPrzegladarki();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  document.getElementById("disable-browser-notifications").addEventListener("click", () => {
    wylaczAlertyPrzegladarki();
    pokazPowiadomienie("Wylaczono alerty przegladarki.");
  });
  document.getElementById("test-browser-notification").addEventListener("click", () => {
    try {
      pokazAlertPrzegladarki({
        task_id: "test",
        title: "Test alertu",
        task_type: "przypomnienie",
        organization_name: stan.biezacyUzytkownik?.organization_name || "",
        calendar_name: "Przegladarka",
        due_at: new Date().toISOString(),
      });
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  zainicjalizujPWA();
}

function zainicjalizujPWA() {
  const installButton = document.getElementById("pwa-install-button");
  const odswiezPrzycisk = () => {
    if (!installButton) {
      return;
    }
    const visible = Boolean(stan.pwaInstallable && stan.pwaInstallPrompt);
    installButton.classList.toggle("hidden", !visible);
  };

  if ("serviceWorker" in navigator) {
    let controllerReloaded = false;
    navigator.serviceWorker
      .register("/sw.js", { updateViaCache: "none" })
      .then((registration) => {
        registration.update().catch(() => {});
        if (registration.waiting) {
          registration.waiting.postMessage({ type: "SKIP_WAITING" });
        }
        registration.addEventListener("updatefound", () => {
          const worker = registration.installing;
          if (!worker) {
            return;
          }
          worker.addEventListener("statechange", () => {
            if (worker.state === "installed" && navigator.serviceWorker.controller) {
              worker.postMessage({ type: "SKIP_WAITING" });
            }
          });
        });
      })
      .catch(() => {});
    navigator.serviceWorker.addEventListener("controllerchange", () => {
      if (controllerReloaded) {
        return;
      }
      controllerReloaded = true;
      window.location.reload();
    });
  }

  window.addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault();
    stan.pwaInstallPrompt = event;
    stan.pwaInstallable = true;
    odswiezPrzycisk();
  });

  window.addEventListener("appinstalled", () => {
    stan.pwaInstallPrompt = null;
    stan.pwaInstallable = false;
    odswiezPrzycisk();
  });

  if (installButton) {
    installButton.addEventListener("click", async () => {
      if (!stan.pwaInstallPrompt) {
        return;
      }
      const prompt = stan.pwaInstallPrompt;
      stan.pwaInstallPrompt = null;
      stan.pwaInstallable = false;
      odswiezPrzycisk();
      try {
        prompt.prompt();
        await prompt.userChoice;
      } catch (error) {
        // PWA install prompt is best-effort.
      }
    });
  }

  odswiezPrzycisk();
}

function zbudujWidokCapabilityPills(capabilities) {
  const normalized = Array.isArray(capabilities) ? capabilities : [];
  if (!normalized.length) {
    return '<span class="status-badge status-normal">brak</span>';
  }
  return normalized
    .map((capability) => `<span class="pill capability-pill">${bezpiecznyTekst(capabilityLabels[capability] || capability)}</span>`)
    .join("");
}

function sformatujCzlonkostwaUzytkownika(uzytkownik) {
  const memberships = Array.isArray(uzytkownik?.memberships) ? uzytkownik.memberships : [];
  if (!memberships.length) {
    return '<span class="status-badge status-normal">Brak</span>';
  }
  return memberships
    .map((membership) => {
      const organizationName = membership.organization_name || membership.organization_slug || "Organizacja";
      const roleLabel = formatujRole(membership.role);
      const parts = [organizationName, roleLabel];
      if (membership.is_primary) {
        parts.push("glowne");
      }
      if (membership.membership_status && membership.membership_status !== "active") {
        parts.push(membership.membership_status);
      }
      return `<span class="pill history-pill">${bezpiecznyTekst(parts.join(" | "))}</span>`;
    })
    .join("");
}

function pobierzSnapshotGoogleKalendarzaUzytkownika(uzytkownik) {
  if (!uzytkownik) {
    return null;
  }
  const fromState = stan.googleCalendarAdminUsers.find(
    (item) => Number(item.user_id) === Number(uzytkownik.user_id)
  );
  return { ...(uzytkownik || {}), ...(fromState || {}) };
}

function zbudujBadgeStatusuGoogleKalendarzaUzytkownika(uzytkownik) {
  const snapshot = pobierzSnapshotGoogleKalendarzaUzytkownika(uzytkownik) || {};
  const status = String(snapshot.google_connection_status || "disconnected").trim().toLowerCase();
  if (status === "approved") {
    return zbudujBadgeStanu("Zatwierdzone", "status-success");
  }
  if (status === "pending_approval") {
    return zbudujBadgeStanu("Czeka na zatwierdzenie", "status-warning");
  }
  if (status === "rejected") {
    return zbudujBadgeStanu("Odrzucone", "status-danger");
  }
  return zbudujBadgeStanu("Brak polaczenia", "status-normal");
}

function zbudujWidokPrzypisanegoKalendarzaOrganizacjiUzytkownika(uzytkownik) {
  const snapshot = pobierzSnapshotGoogleKalendarzaUzytkownika(uzytkownik) || {};
  const assignedCalendar = snapshot.assigned_organization_calendar || null;
  if (!assignedCalendar) {
    return '<span class="status-badge status-normal">Brak</span>';
  }
  const details = [
    assignedCalendar.display_name || assignedCalendar.external_calendar_name || "Kalendarz organizacji",
  ];
  if (assignedCalendar.owner_user_name) {
    details.push(`wlasciciel: ${assignedCalendar.owner_user_name}`);
  }
  return `<div><strong>${bezpiecznyTekst(details[0])}</strong>${
    details[1] ? `<div class="muted">${bezpiecznyTekst(details.slice(1).join(" | "))}</div>` : ""
  }</div>`;
}

function renderujPanelGoogleKalendarzaUzytkownika(uzytkownik) {
  const box = document.getElementById("user-google-calendar-admin-box");
  const statusNode = document.getElementById("user-google-calendar-status");
  const emailNode = document.getElementById("user-google-calendar-email");
  const approvedByNode = document.getElementById("user-google-calendar-approved-by");
  const assignedNode = document.getElementById("user-assigned-organization-calendar");
  const calendarSelect = document.getElementById("user-organization-calendar-select");
  const approveButton = document.getElementById("approve-user-google-calendar");
  const rejectButton = document.getElementById("reject-user-google-calendar");
  const assignButton = document.getElementById("assign-user-organization-calendar");
  const removeButton = document.getElementById("remove-user-organization-calendar");
  if (!box || !statusNode || !emailNode || !approvedByNode || !assignedNode || !calendarSelect) {
    return;
  }

  const snapshot = pobierzSnapshotGoogleKalendarzaUzytkownika(uzytkownik);
  if (!snapshot || !snapshot.user_id) {
    box.classList.add("hidden");
    statusNode.textContent = "Zapisz konto albo wybierz istniejace, aby sprawdzic stan polaczenia Google.";
    emailNode.textContent = "";
    approvedByNode.textContent = "";
    assignedNode.textContent = "Brak przypisanego kalendarza organizacji.";
    calendarSelect.innerHTML = '<option value="">Najpierw zapisz konto</option>';
    calendarSelect.disabled = true;
    if (approveButton) approveButton.disabled = true;
    if (rejectButton) rejectButton.disabled = true;
    if (assignButton) assignButton.disabled = true;
    if (removeButton) removeButton.disabled = true;
    return;
  }

  box.classList.remove("hidden");
  const approvalStatus = String(snapshot.google_connection_status || "disconnected").trim().toLowerCase();
  const hasConnection = Boolean(snapshot.google_connection_exists);
  const assignedCalendar = snapshot.assigned_organization_calendar || null;
  const hasOrganization = Boolean(snapshot.organization_id);
  const employeeConfirmation = snapshot.google_connection_employee_visibility_confirmed
    ? "Pracownik potwierdzil widocznosc adresu dla administratora."
    : "";

  if (approvalStatus === "approved") {
    statusNode.innerHTML = `${zbudujBadgeStanu("Konto Google zatwierdzone", "status-success")}<div class="muted">To konto moze juz synchronizowac wlasne kalendarze.</div>`;
  } else if (approvalStatus === "pending_approval") {
    statusNode.innerHTML = `${zbudujBadgeStanu("Konto Google czeka na zatwierdzenie", "status-warning")}<div class="muted">Pracownik podlaczyl konto, ale nie jest ono jeszcze aktywne w systemie.</div>`;
  } else {
    statusNode.innerHTML = `${zbudujBadgeStanu("Brak zatwierdzonego konta Google", "status-normal")}<div class="muted">Mozesz zatwierdzic konto pracownika albo przypisac mu kalendarz organizacji.</div>`;
  }

  emailNode.textContent = snapshot.google_connection_email
    ? `Podlaczony adres Google: ${snapshot.google_connection_email}${employeeConfirmation ? ` | ${employeeConfirmation}` : ""}`
    : "Pracownik nie ma jeszcze zapisanego konta Google.";

  const approvedBy = snapshot.google_connection_approved_by_display_name || snapshot.google_connection_approved_by_login || "";
  if (approvedBy || snapshot.google_connection_approved_at || snapshot.google_connection_employee_confirmation_at) {
    const details = [];
    if (approvedBy) {
      details.push(`Zatwierdzil: ${approvedBy}`);
    }
    if (snapshot.google_connection_approved_at) {
      details.push(`Data zatwierdzenia: ${formatujDateCzas(snapshot.google_connection_approved_at)}`);
    } else if (snapshot.google_connection_employee_confirmation_at) {
      details.push(`Podlaczone: ${formatujDateCzas(snapshot.google_connection_employee_confirmation_at)}`);
    }
    approvedByNode.textContent = details.join(" | ");
  } else {
    approvedByNode.textContent = "";
  }

  if (assignedCalendar) {
    assignedNode.innerHTML = `<strong>${bezpiecznyTekst(
      assignedCalendar.display_name || assignedCalendar.external_calendar_name || "Kalendarz organizacji"
    )}</strong><div class="muted">${bezpiecznyTekst(
      assignedCalendar.owner_user_name
        ? `Wlasciciel kalendarza: ${assignedCalendar.owner_user_name}`
        : assignedCalendar.access_mode_label || "Kalendarz organizacji"
    )}</div>`;
  } else {
    assignedNode.textContent = "Brak przypisanego kalendarza organizacji.";
  }

  if (!hasOrganization) {
    calendarSelect.innerHTML = '<option value="">Najpierw przypisz organizacje</option>';
    calendarSelect.disabled = true;
  } else if (!stan.organizacyjneKalendarzeDoPrzypisania.length) {
    calendarSelect.innerHTML = '<option value="">Brak aktywnych kalendarzy organizacji</option>';
    calendarSelect.disabled = true;
  } else {
    const currentAssignedId = assignedCalendar ? String(assignedCalendar.user_calendar_id || "") : "";
    calendarSelect.innerHTML = [
      '<option value="">Wybierz kalendarz organizacji</option>',
      ...stan.organizacyjneKalendarzeDoPrzypisania.map(
        (calendar) =>
          `<option value="${bezpiecznyTekst(calendar.user_calendar_id)}">${bezpiecznyTekst(
            calendar.display_name
          )}</option>`
      ),
    ].join("");
    calendarSelect.value = currentAssignedId;
    calendarSelect.disabled = false;
  }

  if (approveButton) {
    approveButton.disabled = approvalStatus !== "pending_approval";
  }
  if (rejectButton) {
    rejectButton.disabled = !hasConnection;
  }
  if (assignButton) {
    assignButton.disabled = !hasOrganization || calendarSelect.disabled || !calendarSelect.value;
  }
  if (removeButton) {
    removeButton.disabled = !assignedCalendar;
  }
}

async function sprawdzKsefOrganizacji() {
  if (!czyMoznaZarzadzacOrganizacjami()) return;

  const organizationId = document.getElementById("organization-id").value.trim();
  if (!organizationId) {
    pokazPowiadomienie("Najpierw zapisz organizacje.");
    return;
  }

  const button = document.getElementById("organization-check-ksef");
  const previousLabel = button.textContent;
  button.textContent = "Sprawdzam...";
  button.classList.add("is-busy");
  odswiezUprawnieniaFormularzaOrganizacji();

  try {
    const result = await api(`/api/organizations/${organizationId}/actions/check-ksef`, {
      method: "POST",
    });

    const importedCount = Number(result.imported_count || 0);
    const skippedExistingCount = Number(result.skipped_existing_count || 0);
    const skippedErrorCount = Number(result.skipped_error_count || 0);
    let message = result.message || "Sprawdzono KSeF.";

    if (importedCount > 0) {
      message = `Zaimportowano ${importedCount} ${importedCount === 1 ? "nowa fakture" : "nowe faktury"} z KSeF.`;
      if (skippedExistingCount > 0) {
        message += ` Pominieto ${skippedExistingCount} juz znanych dokumentow.`;
      }
      if (skippedErrorCount > 0) {
        message += ` ${skippedErrorCount} dokument(y) wymaga(y) uwagi.`;
      }
    }

    pokazPowiadomienie(message);
    renderujWynikiWyszukiwania({ invoices: [], contractors: [] });
    await Promise.all([
      wczytajOrganizacje(),
      wczytajPulpit(),
      wczytajWszystkichKontrahentow(),
      wczytajKontrahentow(),
      wczytajFaktury(),
      wczytajLogi(),
    ]);
    if (czyMoznaOtworzycCentrumEmaila()) {
      await wczytajCentrumEmaila();
    }

    const odswiezonaOrganizacja = stan.organizacje.find(
      (item) => Number(item.organization_id) === Number(organizationId)
    );
    if (odswiezonaOrganizacja) {
      wypelnijFormularzOrganizacji(odswiezonaOrganizacja);
      await wczytajHistorieImportowKsefOrganizacji(Number(organizationId));
    }

    if (importedCount > 0) {
      ustawWidok("invoices");
      if (importedCount === 1 && result.invoice?.id) {
        stan.wybranaFakturaId = Number(result.invoice.id);
        await wczytajSzczegolyFaktury(result.invoice.id);
      }
    }
  } finally {
    button.textContent = previousLabel;
    button.classList.remove("is-busy");
    odswiezUprawnieniaFormularzaOrganizacji();
  }
}

async function wczytajGoogleCalendarAdminUsers() {
  if (!czyMoznaZarzadzacUzytkownikami()) {
    stan.googleCalendarAdminUsers = [];
    return [];
  }
  const snapshot = await api(zbudujAdresZOrganizacja("/api/google-calendar/admin-users"));
  stan.googleCalendarAdminUsers = Array.isArray(snapshot) ? snapshot : [];
  return stan.googleCalendarAdminUsers;
}

async function wczytajKalendarzeOrganizacjiDoPrzypisania(organizationId) {
  const normalizedOrganizationId = String(organizationId || "").trim();
  if (!czyMoznaZarzadzacUzytkownikami() || !normalizedOrganizationId) {
    stan.organizacyjneKalendarzeDoPrzypisania = [];
    return [];
  }
  const calendars = await api(
    zbudujAdresZOpcjonalnaOrganizacja("/api/google-calendar/organization-calendars", normalizedOrganizationId)
  );
  stan.organizacyjneKalendarzeDoPrzypisania = Array.isArray(calendars) ? calendars : [];
  return stan.organizacyjneKalendarzeDoPrzypisania;
}

async function zatwierdzGoogleKalendarzUzytkownika() {
  if (!stan.wybranyUzytkownikId) {
    pokazPowiadomienie("Najpierw wybierz konto pracownika.");
    return;
  }
  await api(`/api/google-calendar/connections/${stan.wybranyUzytkownikId}/approve`, { method: "POST" });
  await Promise.all([wczytajUzytkownikow(), wczytajUzytkownikowDoFaktur(), wczytajLogi()]);
  pokazPowiadomienie("Zatwierdzono konto Google pracownika.");
}

async function odrzucGoogleKalendarzUzytkownika() {
  if (!stan.wybranyUzytkownikId) {
    pokazPowiadomienie("Najpierw wybierz konto pracownika.");
    return;
  }
  await api(`/api/google-calendar/connections/${stan.wybranyUzytkownikId}/reject`, { method: "POST" });
  await Promise.all([wczytajUzytkownikow(), wczytajLogi()]);
  pokazPowiadomienie("Odrzucono albo odlaczono konto Google pracownika.");
}

async function przypiszKalendarzOrganizacjiUzytkownikowi() {
  if (!stan.wybranyUzytkownikId) {
    pokazPowiadomienie("Najpierw wybierz konto pracownika.");
    return;
  }
  const select = document.getElementById("user-organization-calendar-select");
  const userCalendarId = String(select?.value || "").trim();
  if (!userCalendarId) {
    pokazPowiadomienie("Wybierz kalendarz organizacji do przypisania.");
    return;
  }
  await api("/api/google-calendar/assignments", {
    method: "POST",
    body: JSON.stringify({
      user_id: stan.wybranyUzytkownikId,
      user_calendar_id: Number(userCalendarId),
    }),
  });
  await Promise.all([wczytajUzytkownikow(), wczytajLogi()]);
  pokazPowiadomienie("Przypisano kalendarz organizacji do pracownika.");
}

async function usunPrzypisanieKalendarzaOrganizacji() {
  if (!stan.wybranyUzytkownikId) {
    pokazPowiadomienie("Najpierw wybierz konto pracownika.");
    return;
  }
  await api(`/api/google-calendar/assignments/${stan.wybranyUzytkownikId}`, { method: "DELETE" });
  await Promise.all([wczytajUzytkownikow(), wczytajLogi()]);
  pokazPowiadomienie("Usunieto przypisanie kalendarza organizacji.");
}

function renderujUzytkownikow(uzytkownicy) {
  stan.uzytkownicy = uzytkownicy;
  const body = document.getElementById("users-table-body");
  if (!uzytkownicy.length) {
    body.innerHTML = `<tr><td colspan="14">Brak kont uzytkownikow.</td></tr>`;
    return;
  }

  body.innerHTML = uzytkownicy
    .map(
      (uzytkownik) => `
        <tr class="clickable" data-user-id="${uzytkownik.user_id}">
          <td>${uzytkownik.user_id}</td>
          <td>${formatujWartosc(uzytkownik.login)}</td>
          <td>${formatujWartosc(uzytkownik.display_name)}</td>
          <td>${formatujNazweOrganizacji(uzytkownik.organization_name)}</td>
          <td>${sformatujCzlonkostwaUzytkownika(uzytkownik)}</td>
          <td>${formatujWartosc(uzytkownik.telegram_user_id)}</td>
          <td>${uzytkownik.telegram_reminders_enabled ? '<span class="status-badge status-success">tak</span>' : '<span class="status-badge status-normal">nie</span>'}</td>
          <td>${formatujRole(uzytkownik.role)}</td>
          <td>${zbudujWidokCapabilityPills(uzytkownik.capabilities)}</td>
          <td>${zbudujBadgeStatusuGoogleKalendarzaUzytkownika(uzytkownik)}</td>
          <td>${zbudujWidokPrzypisanegoKalendarzaOrganizacjiUzytkownika(uzytkownik)}</td>
          <td>${uzytkownik.is_active ? '<span class="status-badge status-success">tak</span>' : '<span class="status-badge status-danger">nie</span>'}</td>
          <td>${formatujDateCzas(uzytkownik.last_login_at)}</td>
          <td>${formatujWartosc(uzytkownik.created_by_login)}</td>
        </tr>
      `
    )
    .join("");

  body.querySelectorAll("[data-user-id]").forEach((row) => {
    row.addEventListener("click", async () => {
      const userId = Number(row.dataset.userId);
      const uzytkownik = stan.uzytkownicy.find((item) => Number(item.user_id) === userId);
      if (uzytkownik) {
        await wypelnijFormularzUzytkownika(uzytkownik);
      }
    });
  });

  odswiezPoleDelegataKsef(
    stan.wybranaOrganizacjaFormularzaId || document.getElementById("organization-id")?.value || "",
    document.getElementById("organization-ksef-delegate-user-id")?.value || "",
    document.getElementById("organization-ksef-delegate-expires-at")?.value || ""
  );
}

async function wypelnijFormularzUzytkownika(uzytkownik) {
  stan.wybranyUzytkownikId = Number(uzytkownik.user_id);
  document.getElementById("user-form-title").textContent = `Edycja konta: ${uzytkownik.login}`;
  document.getElementById("user-id").value = String(uzytkownik.user_id);
  document.getElementById("user-login").value = uzytkownik.login || "";
  document.getElementById("user-login").disabled = true;
  document.getElementById("user-display-name").value = uzytkownik.display_name || "";
  document.getElementById("user-organization-id").value = uzytkownik.organization_id || "";
  document.getElementById("user-telegram-user-id").value = uzytkownik.telegram_user_id || "";
  document.getElementById("user-telegram-reminders-enabled").checked = uzytkownik.telegram_reminders_enabled !== 0;
  document.getElementById("user-role").value = uzytkownik.role || "operator";
  document.getElementById("user-can-upload-knowledge").checked = Boolean(uzytkownik.can_upload_knowledge);
  renderujCapabilitiesFormularzaUzytkownika();
  ustawCapabilitiesFormularzaUzytkownika(uzytkownik.capabilities || []);
  document.getElementById("user-active").value = uzytkownik.is_active ? "1" : "0";
  document.getElementById("user-password").value = "";
  document.getElementById("user-password").placeholder = "Podaj nowe haslo tylko jesli chcesz je zmienic";
  odswiezOpcjeRolUzytkownikow();
  await wczytajKalendarzeOrganizacjiDoPrzypisania(uzytkownik.organization_id || null);
  const refreshedUser =
    stan.uzytkownicy.find((item) => Number(item.user_id) === Number(uzytkownik.user_id)) || uzytkownik;
  renderujPanelGoogleKalendarzaUzytkownika(refreshedUser);
}

function wyczyscFormularzUzytkownika() {
  stan.wybranyUzytkownikId = null;
  document.getElementById("user-form-title").textContent = "Nowe konto";
  document.getElementById("user-form").reset();
  document.getElementById("user-id").value = "";
  document.getElementById("user-login").disabled = false;
  document.getElementById("user-organization-id").value = czyGlobalnyAdministrator()
    ? ""
    : String(stan.biezacyUzytkownik?.organization_id || "");
  document.getElementById("user-telegram-user-id").value = "";
  document.getElementById("user-telegram-reminders-enabled").checked = true;
  document.getElementById("user-role").value = "operator";
  document.getElementById("user-can-upload-knowledge").checked = true;
  renderujCapabilitiesFormularzaUzytkownika();
  ustawCapabilitiesFormularzaUzytkownika(pobierzDomyslneCapabilitiesDlaRoli("operator"));
  document.getElementById("user-active").value = "1";
  document.getElementById("user-password").placeholder = "Podaj haslo dla nowego konta lub nowe haslo przy zmianie";
  odswiezOpcjeRolUzytkownikow();
  stan.organizacyjneKalendarzeDoPrzypisania = [];
  renderujPanelGoogleKalendarzaUzytkownika(null);
}

async function zapiszUzytkownika() {
  if (!czyMoznaZarzadzacUzytkownikami()) return;

  const userId = document.getElementById("user-id").value.trim();
  const login = document.getElementById("user-login").value.trim();
  const haslo = document.getElementById("user-password").value.trim();
  const payload = {
    display_name: document.getElementById("user-display-name").value.trim(),
    organization_id: document.getElementById("user-organization-id").value || null,
    telegram_user_id: document.getElementById("user-telegram-user-id").value.trim(),
    telegram_reminders_enabled: document.getElementById("user-telegram-reminders-enabled").checked,
    role: document.getElementById("user-role").value,
    can_upload_knowledge: document.getElementById("user-can-upload-knowledge").checked,
    capabilities: pobierzZaznaczoneCapabilitiesZFormularzaUzytkownika(),
    is_active: document.getElementById("user-active").value,
  };

  let zapisanyUzytkownik;
  if (!userId) {
    payload.login = login;
    payload.password = haslo;
    zapisanyUzytkownik = await api("/api/users", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  } else {
    if (haslo) {
      payload.password = haslo;
    }
    zapisanyUzytkownik = await api(`/api/users/${userId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  }

  if (
    stan.biezacyUzytkownik &&
    Number(zapisanyUzytkownik.user_id) === Number(stan.biezacyUzytkownik.user_id)
  ) {
    stan.biezacyUzytkownik = zapisanyUzytkownik;
    odswiezPasekSesji();
  }

  stan.wybranyUzytkownikId = Number(zapisanyUzytkownik.user_id);
  pokazPowiadomienie(`Zapisano konto ${zapisanyUzytkownik.login}.`);
  await Promise.all([wczytajUzytkownikow(), wczytajLogi()]);
  const odswiezonyUzytkownik =
    stan.uzytkownicy.find((item) => Number(item.user_id) === Number(zapisanyUzytkownik.user_id)) || zapisanyUzytkownik;
  await wypelnijFormularzUzytkownika(odswiezonyUzytkownik);
}

function anulujPollingBazyWiedzy() {
  if (stan.knowledgePollingTimeoutId) {
    window.clearTimeout(stan.knowledgePollingTimeoutId);
    stan.knowledgePollingTimeoutId = null;
  }
}

function zaplanujPollingBazyWiedzy() {
  anulujPollingBazyWiedzy();
  const pending = (stan.konfiguracjaBazyWiedzy?.document_summary?.queued || 0) + (stan.konfiguracjaBazyWiedzy?.document_summary?.processing || 0);
  if (!pending || stan.aktywnyWidok !== "knowledge" || !stan.biezacyUzytkownik || !czyModulWiedzyMaZakres()) {
    return;
  }
  stan.knowledgePollingTimeoutId = window.setTimeout(async () => {
    try {
      await wczytajBazeWiedzy();
    } catch (error) {
      console.error(error);
    }
  }, 4000);
}

function zbudujHistorieDokumentuBazyWiedzy(dokument) {
  const versions = (dokument.versions || [])
    .map((version) => `<span class="pill history-pill">v${bezpiecznyTekst(version.version_number)} | ${bezpiecznyTekst(version.extraction_method || "import")}</span>`)
    .join("");
  const jobs = (dokument.recent_jobs || [])
    .map((job) => `<span class="pill history-pill">${bezpiecznyTekst(formatujStatusPrzetwarzaniaBazyWiedzy(job.status))}</span>`)
    .join("");
  return `
    <div class="knowledge-doc-history">
      ${versions ? `<div><strong>Wersje</strong><div class="pill-row">${versions}</div></div>` : ""}
      ${jobs ? `<div><strong>Ostatnie zadania</strong><div class="pill-row">${jobs}</div></div>` : ""}
    </div>
  `;
}

function odswiezStanBazyWiedzy() {
  const przyciskZapisu = document.getElementById("knowledge-save-button");
  const przyciskSynchronizacji = document.getElementById("knowledge-sync-button");
  const komunikat = document.getElementById("knowledge-access-note");
  const poleTytulu = document.getElementById("knowledge-title");
  const polePliku = document.getElementById("knowledge-file");
  const poleTresci = document.getElementById("knowledge-content");
  const polePytania = document.getElementById("knowledge-question");
  const przyciskPytania = document.querySelector('#knowledge-question-form button[type="submit"]');
  if (!przyciskZapisu || !przyciskSynchronizacji || !komunikat) {
    return;
  }

  if (!stan.biezacyUzytkownik) {
    przyciskZapisu.disabled = true;
    przyciskSynchronizacji.disabled = true;
    [poleTytulu, polePliku, poleTresci, polePytania, przyciskPytania].forEach((element) => element && (element.disabled = true));
    komunikat.textContent = "Zaloguj sie, aby korzystac z bazy wiedzy.";
    anulujPollingBazyWiedzy();
    return;
  }

  const brakWyboruOrganizacji = czyGlobalnyAdministrator() && !stan.wybranaOrganizacjaId;
  const moznaImportowac = !brakWyboruOrganizacji && czyMoznaDodawacPlikiDoBazyWiedzy();
  const moznaSynchronizowac = !brakWyboruOrganizacji && czyMoznaSynchronizowacBazeWiedzy();
  const moznaCzytac = czyModulWiedzyMaZakres() && czyMoznaCzytacBazeWiedzy();
  przyciskZapisu.disabled = !moznaImportowac;
  przyciskSynchronizacji.disabled = !moznaSynchronizowac;
  [poleTytulu, polePliku, poleTresci].forEach((element) => element && (element.disabled = !moznaImportowac));
  [polePytania, przyciskPytania].forEach((element) => element && (element.disabled = !moznaCzytac));

  if (brakWyboruOrganizacji) {
    komunikat.textContent = "Wybierz konkretna organizacje, aby pracowac na jej bazie wiedzy.";
  } else if (!czyMoznaCzytacBazeWiedzy()) {
    komunikat.textContent = "To konto nie ma dostepu do modulu wiedzy.";
  } else if (!czyMoznaDodawacPlikiDoBazyWiedzy()) {
    komunikat.textContent = "Mozesz czytac i pytac, ale import plikow jest zablokowany dla tego konta.";
  } else {
    komunikat.textContent = czyMoznaZarzadzacPrzetwarzaniemBazyWiedzy()
      ? "Masz pelen dostep do bazy wiedzy, synchronizacji i kolejek przetwarzania."
      : "Mozesz dodawac dokumenty, synchronizowac folder i zadawac pytania do bazy wiedzy.";
  }
  odswiezPanelImportuBazyWiedzy();
  zaplanujPollingBazyWiedzy();
}

function renderujBazeWiedzy(payload) {
  if (stan.ostatniImportBazyWiedzy && Number(stan.ostatniImportBazyWiedzy.organization_id || 0) !== Number(payload.organization_id || 0)) {
    stan.ostatniImportBazyWiedzy = null;
  }
  stan.dokumentyWiedzy = payload.documents || [];
  stan.folderBazyWiedzy = payload.folder_path || "";
  stan.konfiguracjaBazyWiedzy = {
    organization_id: payload.organization_id,
    supported_formats: payload.supported_formats || [],
    ocr_enabled: Boolean(payload.ocr_enabled),
    ocr_mode: payload.ocr_mode || "fallback",
    document_summary: payload.document_summary || {},
  };
  stan.odpowiedzBazyWiedzy = null;
  const summary = payload.document_summary || {};
  document.getElementById("knowledge-count").textContent = `${stan.dokumentyWiedzy.length} dokumentow`;
  document.getElementById("knowledge-folder-path").textContent = stan.folderBazyWiedzy || "-";
  document.getElementById("knowledge-answer-empty").classList.remove("hidden");
  document.getElementById("knowledge-answer").classList.add("hidden");
  document.getElementById("knowledge-answer").innerHTML = "";
  const pipeline = document.getElementById("knowledge-pipeline-summary");
  if (pipeline) {
    pipeline.innerHTML = `
      <span class="pill history-pill">gotowe: ${bezpiecznyTekst(summary.ready || 0)}</span>
      <span class="pill history-pill">kolejka: ${bezpiecznyTekst(summary.queued || 0)}</span>
      <span class="pill history-pill">przetwarzanie: ${bezpiecznyTekst(summary.processing || 0)}</span>
      <span class="pill history-pill">bledy: ${bezpiecznyTekst(summary.error || 0)}</span>
    `;
  }

  const container = document.getElementById("knowledge-documents");
  if (!stan.dokumentyWiedzy.length) {
    container.innerHTML = `<div class="empty-state">Ta organizacja nie ma jeszcze zadnych dokumentow wiedzy.</div>`;
    odswiezStanBazyWiedzy();
    return;
  }

  container.innerHTML = stan.dokumentyWiedzy
    .map((dokument) => {
      const extension = String(dokument.file_name || "").includes(".") ? String(dokument.file_name).split(".").pop().toUpperCase() : "";
      const createdBy = dokument.created_by_display_name || dokument.created_by_login;
      const retryButton = czyMoznaZarzadzacPrzetwarzaniemBazyWiedzy()
        ? `<button type="button" class="secondary knowledge-retry-button" data-knowledge-retry-id="${dokument.knowledge_document_id}">Ponow przetwarzanie</button>`
        : "";
      return `
        <article class="list-item knowledge-doc-item">
          <div class="knowledge-doc-header">
            <div>
              <div class="knowledge-doc-title">${bezpiecznyTekst(dokument.title)}</div>
              <div class="knowledge-doc-badges">
                <span class="status-badge ${klasaStatusuPrzetwarzaniaBazyWiedzy(dokument.processing_status)}">${bezpiecznyTekst(formatujStatusPrzetwarzaniaBazyWiedzy(dokument.processing_status))}</span>
                <span class="status-badge ${klasaStatusuZrodlaBazyWiedzy(dokument.source_type || "manual")}">${bezpiecznyTekst(formatujZrodloBazyWiedzy(dokument.source_type || "manual"))}</span>
                ${extension ? `<span class="pill knowledge-doc-pill">${bezpiecznyTekst(extension)}</span>` : ""}
                <span class="pill history-pill">v${bezpiecznyTekst(dokument.current_version_number || 0)}</span>
              </div>
            </div>
            ${retryButton}
          </div>
          <div>${bezpiecznyTekst(dokument.snippet || "Brak podgladu tresci.")}</div>
          ${dokument.processing_error ? `<div class="knowledge-error-note">${bezpiecznyTekst(dokument.processing_error)}</div>` : ""}
          <div class="knowledge-doc-meta">
            <span>Plik: ${bezpiecznyTekst(dokument.file_name)}</span>
            <span>Znaki: ${bezpiecznyTekst(dokument.char_count)}</span>
            <span>Przetworzono: ${formatujDateCzas(dokument.last_processed_at || dokument.updated_at)}</span>
            ${createdBy ? `<span>Dodane przez: ${bezpiecznyTekst(createdBy)}</span>` : ""}
            <a href="${bezpiecznyTekst(dokument.file_link)}" target="_blank" rel="noreferrer">Otworz plik</a>
          </div>
          ${zbudujHistorieDokumentuBazyWiedzy(dokument)}
        </article>
      `;
    })
    .join("");
  container.querySelectorAll("[data-knowledge-retry-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        await api(zbudujAdresZOrganizacja(`/api/knowledge/documents/${button.dataset.knowledgeRetryId}/reprocess`), { method: "POST" });
        pokazPowiadomienie("Dokument dodany ponownie do kolejki.");
        await Promise.all([wczytajBazeWiedzy(), wczytajLogi()]);
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
    });
  });
  odswiezStanBazyWiedzy();
}

function renderujOdpowiedzBazyWiedzy(wynik) {
  stan.odpowiedzBazyWiedzy = wynik;
  const emptyState = document.getElementById("knowledge-answer-empty");
  const container = document.getElementById("knowledge-answer");
  emptyState.classList.add("hidden");
  container.classList.remove("hidden");
  const zrodla = (wynik.matches || [])
    .map(
      (match) => `
        <article class="knowledge-source-item">
          <div class="knowledge-doc-header">
            <strong>${bezpiecznyTekst(match.citation_label || match.title)}</strong>
            <span class="status-badge ${klasaStatusuPrzetwarzaniaBazyWiedzy(match.processing_status || "ready")}">${bezpiecznyTekst(formatujStatusPrzetwarzaniaBazyWiedzy(match.processing_status || "ready"))}</span>
          </div>
          <p>${bezpiecznyTekst(match.snippet)}</p>
          <div class="knowledge-doc-meta">
            <span>Wynik dopasowania: ${bezpiecznyTekst(match.score)}</span>
            <span>Wersja: ${bezpiecznyTekst(match.version_number || 0)}</span>
            <span>Przetworzono: ${formatujDateCzas(match.last_processed_at || match.updated_at)}</span>
            <a href="${bezpiecznyTekst(match.file_link)}" target="_blank" rel="noreferrer">Zrodlo</a>
          </div>
        </article>
      `
    )
    .join("");

  container.innerHTML = `
    <div class="knowledge-answer-box">
      <div class="knowledge-answer-main">${bezpiecznyTekst(wynik.answer || "")}</div>
      ${
        zrodla
          ? `<div class="knowledge-source-list">${zrodla}</div>`
          : `<div class="empty-state">Brak bezposrednich zrodel do pokazania.</div>`
      }
    </div>
  `;
}

async function wczytajBazeWiedzy() {
  if (!stan.biezacyUzytkownik) {
    wyczyscBazeWiedzy();
    anulujPollingBazyWiedzy();
    return;
  }
  if (!czyModulWiedzyMaZakres()) {
    wyczyscBazeWiedzy();
    document.getElementById("knowledge-access-note").textContent = "Wybierz konkretna organizacje, aby otworzyc jej baze wiedzy.";
    anulujPollingBazyWiedzy();
    return;
  }

  const wynik = await api(zbudujAdresZOrganizacja("/api/knowledge/documents"));
  renderujBazeWiedzy(wynik);
}

async function zapiszDokumentWiedzy() {
  if (!czyMoznaDodawacPlikiDoBazyWiedzy()) {
    pokazPowiadomienie("To konto nie moze dodawac dokumentow wiedzy.");
    return;
  }
  if (!czyModulWiedzyMaZakres()) {
    pokazPowiadomienie("Wybierz organizacje przed dodaniem dokumentu wiedzy.");
    return;
  }
  const title = document.getElementById("knowledge-title").value.trim();
  const contentText = document.getElementById("knowledge-content").value.trim();
  const fileInput = document.getElementById("knowledge-file");
  const plik = fileInput.files?.[0];
  if (!plik && !contentText) {
    pokazPowiadomienie("Dodaj plik albo wklej tresc dokumentu.");
    return;
  }

  let options;
  if (plik) {
    const formData = new FormData();
    formData.append("title", title);
    formData.append("content_text", contentText);
    formData.append("file", plik);
    options = { method: "POST", body: formData };
  } else {
    options = {
      method: "POST",
      body: JSON.stringify({
        title,
        file_name: title ? `${title.toLowerCase().replaceAll(" ", "_")}.txt` : "dokument_wiedzy.txt",
        content_text: contentText,
      }),
    };
  }
  const created = await api(zbudujAdresZOrganizacja("/api/knowledge/documents"), options);
  stan.ostatniImportBazyWiedzy = {
    kind: "upload",
    organization_id: created.organization_id,
    title: created.title || title,
    file_name: created.file_name || (plik ? plik.name : ""),
    file_size: plik?.size || contentText.length,
    source_type: created.source_type || (plik ? "upload" : "manual"),
    processing_status: created.processing_status || "queued",
  };
  document.getElementById("knowledge-title").value = "";
  document.getElementById("knowledge-file").value = "";
  document.getElementById("knowledge-content").value = "";
  pokazPowiadomienie("Dokument dodany do kolejki bazy wiedzy.");
  await Promise.all([wczytajBazeWiedzy(), wczytajLogi()]);
}

async function synchronizujBazeWiedzy() {
  if (!czyMoznaSynchronizowacBazeWiedzy()) {
    pokazPowiadomienie("To konto nie moze synchronizowac bazy wiedzy.");
    return;
  }
  if (!czyModulWiedzyMaZakres()) {
    pokazPowiadomienie("Wybierz organizacje przed synchronizacja bazy wiedzy.");
    return;
  }
  const wynik = await api(zbudujAdresZOrganizacja("/api/knowledge/sync"), { method: "POST" });
  stan.ostatniImportBazyWiedzy = {
    kind: "sync",
    organization_id: wynik.organization_id,
    imported_count: wynik.imported_count,
    updated_count: wynik.updated_count,
    unchanged_count: wynik.unchanged_count,
    skipped: wynik.skipped || [],
  };
  pokazPowiadomienie(`Synchronizacja dodala do kolejki: nowe ${wynik.imported_count}, aktualizacje ${wynik.updated_count}.`);
  await Promise.all([wczytajBazeWiedzy(), wczytajLogi()]);
}

function wyczyscBazeWiedzy() {
  anulujPollingBazyWiedzy();
  stan.dokumentyWiedzy = [];
  stan.odpowiedzBazyWiedzy = null;
  stan.folderBazyWiedzy = "";
  stan.konfiguracjaBazyWiedzy = null;
  stan.ostatniImportBazyWiedzy = null;
  document.getElementById("knowledge-count").textContent = "";
  document.getElementById("knowledge-folder-path").textContent = "-";
  document.getElementById("knowledge-documents").innerHTML = `<div class="empty-state">Brak dokumentow w bazie wiedzy.</div>`;
  document.getElementById("knowledge-answer-empty").classList.remove("hidden");
  document.getElementById("knowledge-answer").classList.add("hidden");
  document.getElementById("knowledge-answer").innerHTML = "";
  document.getElementById("knowledge-title").value = "";
  document.getElementById("knowledge-file").value = "";
  document.getElementById("knowledge-content").value = "";
  document.getElementById("knowledge-question").value = "";
  const pipeline = document.getElementById("knowledge-pipeline-summary");
  if (pipeline) {
    pipeline.innerHTML = "";
  }
  odswiezPanelImportuBazyWiedzy();
  odswiezStanBazyWiedzy();
}

async function start() {
  try {
    podepnijZdarzenia();
    odswiezPanelImportuBazyWiedzy();
    ustawWidocznoscElementowSrodowiska();
    ustawWidocznoscFiltrowFaktur(false);
    await wczytajMeta();
    renderujCapabilitiesFormularzaUzytkownika();
    const maSesje = await sprobujPrzywrocicSesje();
    if (maSesje) {
      await odswiezDanePoZalogowaniu();
    }
  } catch (error) {
    pokazPowiadomienie(error.message);
  }
}

start();

function zapewnijStanRozszerzenBazyWiedzy() {
  if (!stan.filtryBazyWiedzy) {
    stan.filtryBazyWiedzy = { status: "", source: "", search: "" };
  }
  if (!Object.prototype.hasOwnProperty.call(stan, "wybranyDokumentWiedzyId")) {
    stan.wybranyDokumentWiedzyId = null;
  }
  if (!Object.prototype.hasOwnProperty.call(stan, "ostatniPayloadBazyWiedzy")) {
    stan.ostatniPayloadBazyWiedzy = null;
  }
  if (!Object.prototype.hasOwnProperty.call(stan, "czyRozszerzeniaBazyWiedzyPodpiete")) {
    stan.czyRozszerzeniaBazyWiedzyPodpiete = false;
  }
}

function zsynchronizujFiltryBazyWiedzyZFormularzem() {
  zapewnijStanRozszerzenBazyWiedzy();
  const status = document.getElementById("knowledge-filter-status");
  const source = document.getElementById("knowledge-filter-source");
  const search = document.getElementById("knowledge-filter-search");
  if (status) {
    status.value = stan.filtryBazyWiedzy.status || "";
  }
  if (source) {
    source.value = stan.filtryBazyWiedzy.source || "";
  }
  if (search) {
    search.value = stan.filtryBazyWiedzy.search || "";
  }
}

function odczytajFiltryBazyWiedzyZFormularza() {
  zapewnijStanRozszerzenBazyWiedzy();
  stan.filtryBazyWiedzy = {
    status: document.getElementById("knowledge-filter-status")?.value || "",
    source: document.getElementById("knowledge-filter-source")?.value || "",
    search: document.getElementById("knowledge-filter-search")?.value.trim().toLowerCase() || "",
  };
}

function pobierzDokumentBazyWiedzy(knowledgeDocumentId) {
  return (stan.dokumentyWiedzy || []).find(
    (item) => Number(item.knowledge_document_id) === Number(knowledgeDocumentId)
  );
}

function pobierzPrzefiltrowaneDokumentyBazyWiedzy() {
  zapewnijStanRozszerzenBazyWiedzy();
  const filters = stan.filtryBazyWiedzy || {};
  return (stan.dokumentyWiedzy || []).filter((document) => {
    const statusOk = !filters.status || String(document.processing_status || "") === filters.status;
    const sourceOk = !filters.source || String(document.source_type || "") === filters.source;
    const haystack = [
      document.title,
      document.file_name,
      document.snippet,
      document.content_preview,
      formatujZrodloBazyWiedzy(document.source_type || "manual"),
      formatujStatusPrzetwarzaniaBazyWiedzy(document.processing_status || "queued"),
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
    const searchOk = !filters.search || haystack.includes(filters.search);
    return statusOk && sourceOk && searchOk;
  });
}

function renderujPodpowiedziPytanBazyWiedzy() {
  const container = document.getElementById("knowledge-question-suggestions");
  const input = document.getElementById("knowledge-question");
  if (!container || !input) {
    return;
  }

  if (!stan.biezacyUzytkownik || !czyModulWiedzyMaZakres() || !czyMoznaCzytacBazeWiedzy()) {
    container.innerHTML = "";
    return;
  }

  if (!(stan.dokumentyWiedzy || []).length) {
    container.innerHTML =
      '<div class="subtle-note">Dodaj pierwszy dokument albo uzyj synchronizacji folderu, aby od razu testowac pytania w tej zakladce.</div>';
    return;
  }

  const prompts = [
    "Kto zatwierdza delegacje?",
    "Jak zglaszac urlop?",
    "Kto nadaje dostep do systemow?",
  ];
  container.innerHTML = prompts
    .map(
      (prompt) =>
        `<button type="button" class="knowledge-question-chip" data-knowledge-question-prompt="${bezpiecznyTekst(prompt)}">${bezpiecznyTekst(
          prompt
        )}</button>`
    )
    .join("");

  container.querySelectorAll("[data-knowledge-question-prompt]").forEach((button) => {
    button.addEventListener("click", async () => {
      input.value = button.dataset.knowledgeQuestionPrompt || "";
      input.focus();
      try {
        await zapytajBazeWiedzy();
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
    });
  });
}

function odswiezWidokBazyWiedzyZPamieci() {
  if (stan.ostatniPayloadBazyWiedzy) {
    renderujBazeWiedzy(stan.ostatniPayloadBazyWiedzy);
    return;
  }
  renderujPodgladDokumentuBazyWiedzy();
  renderujPanelAdministratoraBazyWiedzy();
  renderujPodpowiedziPytanBazyWiedzy();
  odswiezStanBazyWiedzy();
}

function zapewnijStanRozszerzenBazyWiedzy() {
  if (!stan.filtryBazyWiedzy) {
    stan.filtryBazyWiedzy = { status: "", source: "", search: "" };
  }
  if (!Object.prototype.hasOwnProperty.call(stan, "wybranyDokumentWiedzyId")) {
    stan.wybranyDokumentWiedzyId = null;
  }
  if (!Object.prototype.hasOwnProperty.call(stan, "ostatniPayloadBazyWiedzy")) {
    stan.ostatniPayloadBazyWiedzy = null;
  }
  if (!Object.prototype.hasOwnProperty.call(stan, "widokBazyWiedzy")) {
    stan.widokBazyWiedzy = "assistant";
  }
  if (!Object.prototype.hasOwnProperty.call(stan, "widokDokumentowBazyWiedzy")) {
    stan.widokDokumentowBazyWiedzy = "recent";
  }
  if (!Object.prototype.hasOwnProperty.call(stan, "czySterowanieBazyWiedzyPodpiete")) {
    stan.czySterowanieBazyWiedzyPodpiete = false;
  }
  if (!stan.czySterowanieBazyWiedzyPodpiete) {
    document.getElementById("knowledge-mode-assistant")?.addEventListener("click", () => {
      ustawTrybBazyWiedzy("assistant");
    });
    document.getElementById("knowledge-mode-documents")?.addEventListener("click", () => {
      ustawTrybBazyWiedzy("documents");
    });
    document.getElementById("knowledge-documents-view-recent")?.addEventListener("click", () => {
      ustawWidokDokumentowBazyWiedzy("recent");
    });
    document.getElementById("knowledge-documents-view-folders")?.addEventListener("click", () => {
      ustawWidokDokumentowBazyWiedzy("folders");
    });
    stan.czySterowanieBazyWiedzyPodpiete = true;
  }
}

function ustawTrybBazyWiedzy(mode) {
  zapewnijStanRozszerzenBazyWiedzy();
  stan.widokBazyWiedzy = mode === "documents" ? "documents" : "assistant";
  odswiezWidokBazyWiedzyZPamieci();
}

function ustawWidokDokumentowBazyWiedzy(mode) {
  zapewnijStanRozszerzenBazyWiedzy();
  stan.widokDokumentowBazyWiedzy = mode === "folders" ? "folders" : "recent";
  odswiezWidokBazyWiedzyZPamieci();
}

function renderujSterowanieTrybemBazyWiedzy() {
  zapewnijStanRozszerzenBazyWiedzy();
  const assistantButton = document.getElementById("knowledge-mode-assistant");
  const documentsButton = document.getElementById("knowledge-mode-documents");
  const recentButton = document.getElementById("knowledge-documents-view-recent");
  const foldersButton = document.getElementById("knowledge-documents-view-folders");
  const documentsPane = document.getElementById("knowledge-documents-pane");
  const assistantPane = document.getElementById("knowledge-assistant-pane");
  const documentsSwitch = document.getElementById("knowledge-documents-view-switch");

  assistantButton?.classList.toggle("is-active", stan.widokBazyWiedzy === "assistant");
  documentsButton?.classList.toggle("is-active", stan.widokBazyWiedzy === "documents");
  recentButton?.classList.toggle("is-active", stan.widokDokumentowBazyWiedzy === "recent");
  foldersButton?.classList.toggle("is-active", stan.widokDokumentowBazyWiedzy === "folders");

  if (documentsPane) {
    documentsPane.classList.toggle("hidden", stan.widokBazyWiedzy !== "documents");
  }
  if (assistantPane) {
    assistantPane.classList.toggle("hidden", stan.widokBazyWiedzy !== "assistant");
  }
  if (documentsSwitch) {
    documentsSwitch.classList.toggle("hidden", stan.widokBazyWiedzy !== "documents");
  }
}

function zsynchronizujFiltryBazyWiedzyZFormularzem() {
  zapewnijStanRozszerzenBazyWiedzy();
  const status = document.getElementById("knowledge-filter-status");
  const source = document.getElementById("knowledge-filter-source");
  const search = document.getElementById("knowledge-filter-search");
  if (status) {
    status.value = stan.filtryBazyWiedzy.status || "";
  }
  if (source) {
    source.value = stan.filtryBazyWiedzy.source || "";
  }
  if (search) {
    search.value = stan.filtryBazyWiedzy.search || "";
  }
}

function odczytajFiltryBazyWiedzyZFormularza() {
  zapewnijStanRozszerzenBazyWiedzy();
  stan.filtryBazyWiedzy = {
    status: document.getElementById("knowledge-filter-status")?.value || "",
    source: document.getElementById("knowledge-filter-source")?.value || "",
    search: document.getElementById("knowledge-filter-search")?.value.trim().toLowerCase() || "",
  };
}

function pobierzDokumentBazyWiedzy(knowledgeDocumentId) {
  return (stan.dokumentyWiedzy || []).find((item) => Number(item.knowledge_document_id) === Number(knowledgeDocumentId));
}

function pobierzDokumentyBibliotekiBazyWiedzy() {
  return (stan.dokumentyWiedzy || []).filter((document) => document.is_downloadable);
}

function pobierzDokumentyAsystentaBazyWiedzy() {
  return (stan.dokumentyWiedzy || []).filter((document) => document.use_in_assistant);
}

function pobierzPrzefiltrowaneDokumentyBazyWiedzy() {
  zapewnijStanRozszerzenBazyWiedzy();
  const filters = stan.filtryBazyWiedzy || {};
  return pobierzDokumentyBibliotekiBazyWiedzy().filter((document) => {
    const statusOk = !filters.status || String(document.processing_status || "") === filters.status;
    const sourceOk = !filters.source || String(document.source_type || "") === filters.source;
    const haystack = [
      document.title,
      document.file_name,
      document.snippet,
      document.content_preview,
      document.library_path,
      document.library_path_label,
      formatujZrodloBazyWiedzy(document.source_type || "manual"),
      formatujStatusPrzetwarzaniaBazyWiedzy(document.processing_status || "queued"),
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
    const searchOk = !filters.search || haystack.includes(filters.search);
    return statusOk && sourceOk && searchOk;
  });
}

function grupujDokumentyWiedzyPoFolderach(documents) {
  const grouped = new Map();
  documents.forEach((document) => {
    const key = document.library_path || "";
    if (!grouped.has(key)) {
      grouped.set(key, {
        path: key,
        label: document.library_path_label || "Bez folderu",
        documents: [],
      });
    }
    grouped.get(key).documents.push(document);
  });
  return Array.from(grouped.values()).sort((left, right) => {
    if (left.path === right.path) {
      return left.label.localeCompare(right.label, "pl");
    }
    if (!left.path) {
      return -1;
    }
    if (!right.path) {
      return 1;
    }
    return left.label.localeCompare(right.label, "pl");
  });
}

function zbudujKarteDokumentuBazyWiedzy(dokument) {
  const extension = String(dokument.file_name || "").includes(".")
    ? String(dokument.file_name).split(".").pop().toUpperCase()
    : "";
  const createdBy = dokument.created_by_display_name || dokument.created_by_login;
  const isSelected = Number(dokument.knowledge_document_id) === Number(stan.wybranyDokumentWiedzyId);
  const retryButton = czyMoznaZarzadzacPrzetwarzaniemBazyWiedzy()
    ? `<button type="button" class="secondary" data-knowledge-retry-id="${dokument.knowledge_document_id}">Ponow przetwarzanie</button>`
    : "";
  const usageBadges = [
    dokument.use_in_assistant ? `<span class="pill history-pill">Asystent</span>` : "",
    dokument.is_downloadable ? `<span class="pill history-pill">Do pobrania</span>` : "",
  ]
    .filter(Boolean)
    .join("");
  return `
    <article class="list-item knowledge-doc-item ${isSelected ? "is-selected" : ""}" data-knowledge-select-id="${dokument.knowledge_document_id}">
      <div class="knowledge-doc-header">
        <div>
          <div class="knowledge-doc-title">${bezpiecznyTekst(dokument.title)}</div>
          <div class="knowledge-doc-badges">
            <span class="status-badge ${klasaStatusuPrzetwarzaniaBazyWiedzy(dokument.processing_status)}">${bezpiecznyTekst(
              formatujStatusPrzetwarzaniaBazyWiedzy(dokument.processing_status)
            )}</span>
            <span class="status-badge ${klasaStatusuZrodlaBazyWiedzy(dokument.source_type || "manual")}">${bezpiecznyTekst(
              formatujZrodloBazyWiedzy(dokument.source_type || "manual")
            )}</span>
            ${extension ? `<span class="pill knowledge-doc-pill">${bezpiecznyTekst(extension)}</span>` : ""}
            <span class="pill history-pill">v${bezpiecznyTekst(dokument.current_version_number || 0)}</span>
            ${usageBadges}
          </div>
        </div>
        <div class="filters-actions">
          <button type="button" class="secondary" data-knowledge-open-id="${dokument.knowledge_document_id}">Podglad</button>
          ${dokument.file_link ? `<a href="${bezpiecznyTekst(dokument.file_link)}" target="_blank" rel="noreferrer">Pobierz</a>` : ""}
          ${retryButton}
        </div>
      </div>
      <div>${bezpiecznyTekst(dokument.snippet || "Brak podgladu tresci.")}</div>
      ${dokument.processing_error ? `<div class="knowledge-error-note">${bezpiecznyTekst(dokument.processing_error)}</div>` : ""}
      <div class="knowledge-doc-meta">
        <span>Plik: ${bezpiecznyTekst(dokument.file_name)}</span>
        <span>Folder: ${bezpiecznyTekst(dokument.library_path_label || "Bez folderu")}</span>
        <span>Znaki: ${bezpiecznyTekst(dokument.char_count)}</span>
        <span>Przetworzono: ${formatujDateCzas(dokument.last_processed_at || dokument.updated_at)}</span>
        ${createdBy ? `<span>Dodane przez: ${bezpiecznyTekst(createdBy)}</span>` : ""}
      </div>
    </article>
  `;
}

function podpinaAkcjeListyDokumentowBazyWiedzy(container) {
  container.querySelectorAll("[data-knowledge-select-id]").forEach((element) => {
    element.addEventListener("click", (event) => {
      if (event.target?.closest?.("[data-knowledge-retry-id], [data-knowledge-open-id], a")) {
        return;
      }
      ustawWybranyDokumentBazyWiedzy(element.dataset.knowledgeSelectId);
    });
  });
  container.querySelectorAll("[data-knowledge-open-id]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      ustawWybranyDokumentBazyWiedzy(button.dataset.knowledgeOpenId);
    });
  });
  container.querySelectorAll("[data-knowledge-retry-id]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      try {
        await api(zbudujAdresZOrganizacja(`/api/knowledge/documents/${button.dataset.knowledgeRetryId}/reprocess`), {
          method: "POST",
        });
        pokazPowiadomienie("Dokument dodany ponownie do kolejki.");
        await Promise.all([wczytajBazeWiedzy(), wczytajLogi()]);
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
    });
  });
}

async function zapiszDokumentWiedzy() {
  if (!czyMoznaDodawacPlikiDoBazyWiedzy()) {
    pokazPowiadomienie("To konto nie moze dodawac dokumentow wiedzy.");
    return;
  }
  if (!czyModulWiedzyMaZakres()) {
    pokazPowiadomienie("Wybierz organizacje przed dodaniem dokumentu wiedzy.");
    return;
  }
  const title = document.getElementById("knowledge-title").value.trim();
  const contentText = document.getElementById("knowledge-content").value.trim();
  const libraryPath = document.getElementById("knowledge-library-path")?.value.trim() || "";
  const isDownloadable = Boolean(document.getElementById("knowledge-is-downloadable")?.checked);
  const useInAssistant = Boolean(document.getElementById("knowledge-use-in-assistant")?.checked);
  const fileInput = document.getElementById("knowledge-file");
  const plik = fileInput.files?.[0];
  if (!plik && !contentText) {
    pokazPowiadomienie("Dodaj plik albo wklej tresc dokumentu.");
    return;
  }

  let options;
  if (plik) {
    const formData = new FormData();
    formData.append("title", title);
    formData.append("content_text", contentText);
    formData.append("library_path", libraryPath);
    formData.append("is_downloadable", String(isDownloadable));
    formData.append("use_in_assistant", String(useInAssistant));
    formData.append("file", plik);
    options = { method: "POST", body: formData };
  } else {
    options = {
      method: "POST",
      body: JSON.stringify({
        title,
        file_name: title ? `${title.toLowerCase().replaceAll(" ", "_")}.txt` : "dokument_wiedzy.txt",
        content_text: contentText,
        library_path: libraryPath,
        is_downloadable: isDownloadable,
        use_in_assistant: useInAssistant,
      }),
    };
  }

  const created = await api(zbudujAdresZOrganizacja("/api/knowledge/documents"), options);
  stan.ostatniImportBazyWiedzy = {
    kind: "upload",
    organization_id: created.organization_id,
    title: created.title || title,
    file_name: created.file_name || (plik ? plik.name : ""),
    file_size: plik?.size || contentText.length,
    source_type: created.source_type || (plik ? "upload" : "manual"),
    processing_status: created.processing_status || "queued",
  };
  document.getElementById("knowledge-title").value = "";
  document.getElementById("knowledge-file").value = "";
  document.getElementById("knowledge-content").value = "";
  if (document.getElementById("knowledge-library-path")) {
    document.getElementById("knowledge-library-path").value = "";
  }
  if (document.getElementById("knowledge-is-downloadable")) {
    document.getElementById("knowledge-is-downloadable").checked = true;
  }
  if (document.getElementById("knowledge-use-in-assistant")) {
    document.getElementById("knowledge-use-in-assistant").checked = true;
  }
  pokazPowiadomienie("Dokument dodany do kolejki bazy wiedzy.");
  stan.widokBazyWiedzy = "documents";
  await Promise.all([wczytajBazeWiedzy(), wczytajLogi()]);
}

function wyczyscBazeWiedzy() {
  anulujPollingBazyWiedzy();
  zapewnijStanRozszerzenBazyWiedzy();
  stan.dokumentyWiedzy = [];
  stan.odpowiedzBazyWiedzy = null;
  stan.folderBazyWiedzy = "";
  stan.konfiguracjaBazyWiedzy = null;
  stan.ostatniImportBazyWiedzy = null;
  stan.ostatniPayloadBazyWiedzy = null;
  stan.wybranyDokumentWiedzyId = null;
  document.getElementById("knowledge-count").textContent = "";
  document.getElementById("knowledge-folder-path").textContent = "-";
  if (document.getElementById("knowledge-downloadable-count")) {
    document.getElementById("knowledge-downloadable-count").textContent = "";
  }
  document.getElementById("knowledge-documents-summary").textContent = "";
  document.getElementById("knowledge-documents").innerHTML = `<div class="empty-state">Brak dokumentow w bazie wiedzy.</div>`;
  document.getElementById("knowledge-answer-empty").classList.remove("hidden");
  document.getElementById("knowledge-answer").classList.add("hidden");
  document.getElementById("knowledge-answer").innerHTML = "";
  document.getElementById("knowledge-title").value = "";
  document.getElementById("knowledge-file").value = "";
  document.getElementById("knowledge-content").value = "";
  document.getElementById("knowledge-question").value = "";
  if (document.getElementById("knowledge-library-path")) {
    document.getElementById("knowledge-library-path").value = "";
  }
  if (document.getElementById("knowledge-is-downloadable")) {
    document.getElementById("knowledge-is-downloadable").checked = true;
  }
  if (document.getElementById("knowledge-use-in-assistant")) {
    document.getElementById("knowledge-use-in-assistant").checked = true;
  }
  const pipeline = document.getElementById("knowledge-pipeline-summary");
  if (pipeline) {
    pipeline.innerHTML = "";
  }
  const versionBadge = document.getElementById("knowledge-selected-version");
  if (versionBadge) {
    versionBadge.textContent = "";
  }
  const selectedDocument = document.getElementById("knowledge-selected-document");
  if (selectedDocument) {
    selectedDocument.className = "empty-state";
    selectedDocument.textContent = "Wybierz dokument z listy albo z odpowiedzi asystenta, aby zobaczyc szczegoly, folder i wersje.";
  }
  renderujSterowanieTrybemBazyWiedzy();
  odswiezPanelImportuBazyWiedzy();
  odswiezStanBazyWiedzy();
}

function odswiezWidokBazyWiedzyZPamieci() {
  renderujSterowanieTrybemBazyWiedzy();
  if (stan.ostatniPayloadBazyWiedzy) {
    renderujBazeWiedzy(stan.ostatniPayloadBazyWiedzy);
    return;
  }
  renderujPodgladDokumentuBazyWiedzy();
  renderujPanelAdministratoraBazyWiedzy();
  renderujPodpowiedziPytanBazyWiedzy();
  odswiezStanBazyWiedzy();
}

function renderujOdpowiedzBazyWiedzy(wynik) {
  stan.odpowiedzBazyWiedzy = wynik;
  const emptyState = document.getElementById("knowledge-answer-empty");
  const container = document.getElementById("knowledge-answer");
  emptyState.classList.add("hidden");
  container.classList.remove("hidden");
  const zrodla = (wynik.matches || [])
    .map(
      (match) => `
        <article class="knowledge-source-item">
          <div class="knowledge-doc-header">
            <strong>${bezpiecznyTekst(match.citation_label || match.title)}</strong>
            <span class="status-badge ${klasaStatusuPrzetwarzaniaBazyWiedzy(match.processing_status || "ready")}">${bezpiecznyTekst(
              formatujStatusPrzetwarzaniaBazyWiedzy(match.processing_status || "ready")
            )}</span>
          </div>
          <p>${bezpiecznyTekst(match.snippet)}</p>
          <div class="knowledge-doc-meta">
            <span>Wynik dopasowania: ${bezpiecznyTekst(match.score)}</span>
            <span>Wersja: ${bezpiecznyTekst(match.version_number || 0)}</span>
            <span>Przetworzono: ${formatujDateCzas(match.last_processed_at || match.updated_at)}</span>
            ${match.file_link ? `<a href="${bezpiecznyTekst(match.file_link)}" target="_blank" rel="noreferrer">Zrodlo</a>` : ""}
          </div>
          <div class="knowledge-admin-actions">
            <p class="subtle-note">Kliknij, aby przejsc do podgladu tego dokumentu i jego wersji.</p>
            <button type="button" class="secondary" data-knowledge-focus-id="${match.knowledge_document_id}">Pokaz dokument</button>
          </div>
        </article>
      `
    )
    .join("");

  container.innerHTML = `
    <div class="knowledge-answer-box">
      <div class="knowledge-answer-main">${bezpiecznyTekst(wynik.answer || "")}</div>
      ${
        zrodla
          ? `<div class="knowledge-source-list">${zrodla}</div>`
          : `<div class="empty-state">Brak bezposrednich zrodel do pokazania.</div>`
      }
    </div>
  `;

  container.querySelectorAll("[data-knowledge-focus-id]").forEach((button) => {
    button.addEventListener("click", () => {
      stan.widokBazyWiedzy = "assistant";
      ustawWidok("knowledge");
      ustawWybranyDokumentBazyWiedzy(button.dataset.knowledgeFocusId);
    });
  });
}

function renderujPodpowiedziPytanBazyWiedzy() {
  const container = document.getElementById("knowledge-question-suggestions");
  const input = document.getElementById("knowledge-question");
  if (!container || !input) {
    return;
  }
  const assistantDocuments = pobierzDokumentyAsystentaBazyWiedzy();
  if (!stan.biezacyUzytkownik || !czyModulWiedzyMaZakres() || !czyMoznaCzytacBazeWiedzy()) {
    container.innerHTML = "";
    return;
  }
  if (!assistantDocuments.length) {
    container.innerHTML =
      '<div class="subtle-note">Brak dokumentow oznaczonych do pracy asystenta. W zakladce Dokumenty mozesz zdecydowac, ktore pliki maja byc uzywane w odpowiedziach.</div>';
    return;
  }
  const suggestions = assistantDocuments.slice(0, 4).map((document) => `Jakie zasady opisuje dokument ${document.title}?`);
  container.innerHTML = suggestions
    .map((question) => `<button type="button" class="knowledge-question-chip">${bezpiecznyTekst(question)}</button>`)
    .join("");
  container.querySelectorAll(".knowledge-question-chip").forEach((button) => {
    button.addEventListener("click", () => {
      input.value = button.textContent || "";
      input.focus();
    });
  });
}

async function zapiszMetadaneDokumentuBazyWiedzy(knowledgeDocumentId, scope) {
  const titleInput = scope.querySelector("[data-knowledge-meta-title]");
  const folderInput = scope.querySelector("[data-knowledge-meta-folder]");
  const downloadableInput = scope.querySelector("[data-knowledge-meta-downloadable]");
  const assistantInput = scope.querySelector("[data-knowledge-meta-assistant]");
  const button = scope.querySelector("[data-knowledge-save-meta]");
  if (!button) {
    return;
  }
  button.disabled = true;
  button.classList.add("is-busy");
  try {
    await api(zbudujAdresZOrganizacja(`/api/knowledge/documents/${knowledgeDocumentId}`), {
      method: "PATCH",
      body: JSON.stringify({
        title: titleInput?.value?.trim() || "",
        library_path: folderInput?.value?.trim() || "",
        is_downloadable: Boolean(downloadableInput?.checked),
        use_in_assistant: Boolean(assistantInput?.checked),
      }),
    });
    pokazPowiadomienie("Zapisano ustawienia dokumentu.");
    await Promise.all([wczytajBazeWiedzy(), wczytajLogi()]);
  } catch (error) {
    pokazPowiadomienie(error.message);
  } finally {
    button.disabled = false;
    button.classList.remove("is-busy");
  }
}

function renderujPodgladDokumentuBazyWiedzy() {
  const container = document.getElementById("knowledge-selected-document");
  const versionBadge = document.getElementById("knowledge-selected-version");
  if (!container || !versionBadge) {
    return;
  }
  zapewnijStanRozszerzenBazyWiedzy();
  const allDocuments = stan.dokumentyWiedzy || [];
  const filteredDocuments = pobierzPrzefiltrowaneDokumentyBazyWiedzy();
  let selectedDocument = pobierzDokumentBazyWiedzy(stan.wybranyDokumentWiedzyId);

  if (!selectedDocument) {
    const fallback =
      stan.widokBazyWiedzy === "documents"
        ? filteredDocuments[0] || null
        : pobierzDokumentyAsystentaBazyWiedzy()[0] || allDocuments[0] || null;
    selectedDocument = fallback;
    stan.wybranyDokumentWiedzyId = fallback ? Number(fallback.knowledge_document_id) : null;
  }
  if (
    stan.widokBazyWiedzy === "documents" &&
    selectedDocument &&
    !filteredDocuments.some((item) => Number(item.knowledge_document_id) === Number(selectedDocument.knowledge_document_id))
  ) {
    selectedDocument = filteredDocuments[0] || null;
    stan.wybranyDokumentWiedzyId = selectedDocument ? Number(selectedDocument.knowledge_document_id) : null;
  }

  if (!selectedDocument) {
    versionBadge.textContent = "";
    container.className = "empty-state";
    container.textContent = allDocuments.length
      ? "Brak dokumentu pasujacego do biezacego widoku. Zmien filtry albo wybierz inny tryb modulu."
      : "Ta organizacja nie ma jeszcze dokumentow. Dodaj pierwszy plik albo uzyj synchronizacji folderu.";
    return;
  }

  versionBadge.textContent = `v${selectedDocument.current_version_number || 0} | ${formatujStatusPrzetwarzaniaBazyWiedzy(
    selectedDocument.processing_status || "queued"
  )}`;
  container.className = "";
  const createdBy = selectedDocument.created_by_display_name || selectedDocument.created_by_login || "system";
  const retryButton = czyMoznaZarzadzacPrzetwarzaniemBazyWiedzy()
    ? `<button type="button" class="secondary" data-knowledge-preview-retry="${selectedDocument.knowledge_document_id}">Ponow przetwarzanie</button>`
    : "";
  const canEditMetadata = czyMoznaDodawacPlikiDoBazyWiedzy();
  container.innerHTML = `
    <div class="knowledge-preview-card">
      <div class="knowledge-doc-selection">
        <div>
          <div class="knowledge-doc-title">${bezpiecznyTekst(selectedDocument.title)}</div>
          <div class="knowledge-doc-badges">
            <span class="status-badge ${klasaStatusuPrzetwarzaniaBazyWiedzy(selectedDocument.processing_status || "queued")}">${bezpiecznyTekst(
              formatujStatusPrzetwarzaniaBazyWiedzy(selectedDocument.processing_status || "queued")
            )}</span>
            <span class="status-badge ${klasaStatusuZrodlaBazyWiedzy(selectedDocument.source_type || "manual")}">${bezpiecznyTekst(
              formatujZrodloBazyWiedzy(selectedDocument.source_type || "manual")
            )}</span>
            <span class="pill history-pill">${bezpiecznyTekst(selectedDocument.file_name || "-")}</span>
            ${selectedDocument.use_in_assistant ? '<span class="pill history-pill">Asystent</span>' : ""}
            ${selectedDocument.is_downloadable ? '<span class="pill history-pill">Do pobrania</span>' : ""}
          </div>
        </div>
        <div class="filters-actions">
          ${selectedDocument.file_link ? `<a href="${bezpiecznyTekst(selectedDocument.file_link)}" target="_blank" rel="noreferrer">Pobierz</a>` : ""}
          ${retryButton}
        </div>
      </div>
      <div class="knowledge-preview-meta">
        <span>Folder: ${bezpiecznyTekst(selectedDocument.library_path_label || "Bez folderu")}</span>
        <span>Znaki: ${bezpiecznyTekst(selectedDocument.char_count || 0)}</span>
        <span>Dodane przez: ${bezpiecznyTekst(createdBy)}</span>
        <span>Ostatnie przetworzenie: ${formatujDateCzas(selectedDocument.last_processed_at || selectedDocument.updated_at)}</span>
      </div>
      <div class="knowledge-preview-main">${bezpiecznyTekst(
        selectedDocument.content_preview || selectedDocument.snippet || "Dokument jest jeszcze przetwarzany."
      )}</div>
      ${
        selectedDocument.processing_error
          ? `<div class="knowledge-error-note">${bezpiecznyTekst(selectedDocument.processing_error)}</div>`
          : ""
      }
      ${
        canEditMetadata
          ? `
            <div class="knowledge-metadata-editor">
              <strong>Ustawienia dokumentu</strong>
              <div class="field-grid">
                <div class="field">
                  <label>Tytul</label>
                  <input type="text" data-knowledge-meta-title value="${bezpiecznyTekst(selectedDocument.title)}" />
                </div>
                <div class="field">
                  <label>Folder</label>
                  <input type="text" data-knowledge-meta-folder value="${bezpiecznyTekst(selectedDocument.library_path || "")}" placeholder="np. Wzory/HR" />
                </div>
                <div class="field field-full">
                  <div class="knowledge-option-grid">
                    <label class="checkbox-row">
                      <input type="checkbox" data-knowledge-meta-downloadable ${selectedDocument.is_downloadable ? "checked" : ""} />
                      <span>Pokazuj w zakladce Dokumenty i w wyszukiwarce plikow</span>
                    </label>
                    <label class="checkbox-row">
                      <input type="checkbox" data-knowledge-meta-assistant ${selectedDocument.use_in_assistant ? "checked" : ""} />
                      <span>Uzywaj w odpowiedziach asystenta</span>
                    </label>
                  </div>
                </div>
              </div>
              <div class="filters-actions">
                <button type="button" class="secondary" data-knowledge-save-meta>Zapisz ustawienia dokumentu</button>
              </div>
            </div>
          `
          : ""
      }
      <div class="knowledge-preview-versions">
        <strong>Historia wersji</strong>
        ${zbudujWersjeDokumentuBazyWiedzy(selectedDocument)}
      </div>
      <div class="knowledge-preview-versions">
        <strong>Kolejka i zadania przetwarzania</strong>
        ${zbudujZadaniaPrzetwarzaniaBazyWiedzy(selectedDocument)}
      </div>
    </div>
  `;

  const retry = container.querySelector("[data-knowledge-preview-retry]");
  if (retry) {
    retry.addEventListener("click", async () => {
      try {
        await api(zbudujAdresZOrganizacja(`/api/knowledge/documents/${retry.dataset.knowledgePreviewRetry}/reprocess`), {
          method: "POST",
        });
        pokazPowiadomienie("Dokument dodany ponownie do kolejki.");
        await Promise.all([wczytajBazeWiedzy(), wczytajLogi()]);
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
    });
  }
  const saveMeta = container.querySelector("[data-knowledge-save-meta]");
  if (saveMeta) {
    saveMeta.addEventListener("click", async () => {
      await zapiszMetadaneDokumentuBazyWiedzy(selectedDocument.knowledge_document_id, container);
    });
  }
}

function odswiezStanBazyWiedzy() {
  zapewnijStanRozszerzenBazyWiedzy();
  renderujSterowanieTrybemBazyWiedzy();
  const przyciskZapisu = document.getElementById("knowledge-save-button");
  const przyciskSynchronizacji = document.getElementById("knowledge-sync-button");
  const komunikat = document.getElementById("knowledge-access-note");
  const poleTytulu = document.getElementById("knowledge-title");
  const polePliku = document.getElementById("knowledge-file");
  const poleFolderu = document.getElementById("knowledge-library-path");
  const polePobierania = document.getElementById("knowledge-is-downloadable");
  const poleAsystenta = document.getElementById("knowledge-use-in-assistant");
  const poleTresci = document.getElementById("knowledge-content");
  const polePytania = document.getElementById("knowledge-question");
  const przyciskPytania = document.querySelector('#knowledge-question-form button[type="submit"]');
  const filterControls = [
    document.getElementById("knowledge-filter-status"),
    document.getElementById("knowledge-filter-source"),
    document.getElementById("knowledge-filter-search"),
    document.getElementById("knowledge-clear-filters"),
    document.getElementById("knowledge-mode-assistant"),
    document.getElementById("knowledge-mode-documents"),
    document.getElementById("knowledge-documents-view-recent"),
    document.getElementById("knowledge-documents-view-folders"),
  ];
  if (!przyciskZapisu || !przyciskSynchronizacji || !komunikat) {
    return;
  }

  if (!stan.biezacyUzytkownik) {
    przyciskZapisu.disabled = true;
    przyciskSynchronizacji.disabled = true;
    [poleTytulu, polePliku, poleFolderu, polePobierania, poleAsystenta, poleTresci, polePytania, przyciskPytania, ...filterControls].forEach(
      (element) => element && (element.disabled = true)
    );
    komunikat.textContent = "Zaloguj sie, aby korzystac z bazy wiedzy.";
    anulujPollingBazyWiedzy();
    renderujPanelAdministratoraBazyWiedzy();
    renderujPodgladDokumentuBazyWiedzy();
    renderujPodpowiedziPytanBazyWiedzy();
    return;
  }

  const brakWyboruOrganizacji = czyGlobalnyAdministrator() && !stan.wybranaOrganizacjaId;
  const moznaImportowac = !brakWyboruOrganizacji && czyMoznaDodawacPlikiDoBazyWiedzy();
  const moznaSynchronizowac = !brakWyboruOrganizacji && czyMoznaSynchronizowacBazeWiedzy();
  const moznaCzytac = czyModulWiedzyMaZakres() && czyMoznaCzytacBazeWiedzy();
  przyciskZapisu.disabled = !moznaImportowac;
  przyciskSynchronizacji.disabled = !moznaSynchronizowac;
  [poleTytulu, polePliku, poleFolderu, polePobierania, poleAsystenta, poleTresci].forEach(
    (element) => element && (element.disabled = !moznaImportowac)
  );
  [polePytania, przyciskPytania, ...filterControls].forEach((element) => element && (element.disabled = !moznaCzytac));

  if (brakWyboruOrganizacji) {
    komunikat.textContent = "Wybierz konkretna organizacje, aby pracowac na jej bazie wiedzy.";
  } else if (!czyMoznaCzytacBazeWiedzy()) {
    komunikat.textContent = "To konto nie ma dostepu do modulu wiedzy.";
  } else if (!czyMoznaDodawacPlikiDoBazyWiedzy()) {
    komunikat.textContent = "Mozesz czytac i pytac, ale import plikow oraz edycja dokumentow sa zablokowane dla tego konta.";
  } else {
    komunikat.textContent = czyMoznaZarzadzacPrzetwarzaniemBazyWiedzy()
      ? "Masz pelen dostep do dokumentow firmowych, synchronizacji i kolejek przetwarzania."
      : "Mozesz dodawac dokumenty, pobierac pliki i zadawac pytania do bazy wiedzy.";
  }
  odswiezPanelImportuBazyWiedzy();
  renderujPanelAdministratoraBazyWiedzy();
  renderujPodgladDokumentuBazyWiedzy();
  renderujPodpowiedziPytanBazyWiedzy();
  zaplanujPollingBazyWiedzy();
}

function renderujBazeWiedzy(payload) {
  zapewnijStanRozszerzenBazyWiedzy();
  if (stan.ostatniImportBazyWiedzy && Number(stan.ostatniImportBazyWiedzy.organization_id || 0) !== Number(payload.organization_id || 0)) {
    stan.ostatniImportBazyWiedzy = null;
  }

  stan.ostatniPayloadBazyWiedzy = payload;
  stan.dokumentyWiedzy = payload.documents || [];
  stan.folderBazyWiedzy = payload.folder_path || "";
  stan.konfiguracjaBazyWiedzy = {
    organization_id: payload.organization_id,
    supported_formats: payload.supported_formats || [],
    ocr_enabled: Boolean(payload.ocr_enabled),
    ocr_mode: payload.ocr_mode || "fallback",
    document_summary: payload.document_summary || {},
    folder_summary: payload.folder_summary || [],
  };

  const summary = payload.document_summary || {};
  const allDocuments = stan.dokumentyWiedzy || [];
  const libraryDocuments = pobierzDokumentyBibliotekiBazyWiedzy();
  const filteredDocuments = pobierzPrzefiltrowaneDokumentyBazyWiedzy();
  if (stan.widokBazyWiedzy === "documents" && !filteredDocuments.some((item) => Number(item.knowledge_document_id) === Number(stan.wybranyDokumentWiedzyId))) {
    stan.wybranyDokumentWiedzyId = filteredDocuments[0]?.knowledge_document_id || stan.wybranyDokumentWiedzyId || null;
  }

  document.getElementById("knowledge-count").textContent = `${allDocuments.length} dokumentow`;
  document.getElementById("knowledge-folder-path").textContent = stan.folderBazyWiedzy || "-";
  if (document.getElementById("knowledge-downloadable-count")) {
    document.getElementById("knowledge-downloadable-count").textContent = `${libraryDocuments.length} plikow`;
  }
  document.getElementById("knowledge-documents-summary").textContent = allDocuments.length
    ? `Asystent widzi ${summary.assistant_enabled || 0} dokumentow, biblioteka plikow pokazuje ${summary.downloadable || 0}, foldery: ${summary.folders || 0}. Globalna wyszukiwarka obejmuje wszystkie dostepne pliki uzytkownika.`
    : "Ta organizacja nie ma jeszcze zadnych dokumentow wiedzy.";
  zsynchronizujFiltryBazyWiedzyZFormularzem();
  renderujSterowanieTrybemBazyWiedzy();

  const pipeline = document.getElementById("knowledge-pipeline-summary");
  if (pipeline) {
    pipeline.innerHTML = `
      <span class="pill history-pill">gotowe: ${bezpiecznyTekst(summary.ready || 0)}</span>
      <span class="pill history-pill">kolejka: ${bezpiecznyTekst(summary.queued || 0)}</span>
      <span class="pill history-pill">przetwarzanie: ${bezpiecznyTekst(summary.processing || 0)}</span>
      <span class="pill history-pill">bledy: ${bezpiecznyTekst(summary.error || 0)}</span>
    `;
  }

  const container = document.getElementById("knowledge-documents");
  if (!libraryDocuments.length) {
    container.innerHTML = `<div class="empty-state">Ta organizacja nie ma jeszcze plikow oznaczonych do pobrania. Dodaj dokument albo wlacz widocznosc biblioteki dla istniejacego pliku.</div>`;
  } else if (!filteredDocuments.length) {
    container.innerHTML = `<div class="empty-state">Zadne pliki nie pasuja do biezacych filtrow. Wyczysc filtry albo zmien wyszukiwana fraze.</div>`;
  } else if (stan.widokDokumentowBazyWiedzy === "folders") {
    container.innerHTML = grupujDokumentyWiedzyPoFolderach(filteredDocuments)
      .map(
        (group) => `
          <section class="knowledge-folder-group">
            <div class="knowledge-folder-header">
              <div>
                <strong>${bezpiecznyTekst(group.label)}</strong>
                <div class="subtle-note">${bezpiecznyTekst(group.documents.length)} plikow</div>
              </div>
              <span class="pill history-pill">${bezpiecznyTekst(group.path || "root")}</span>
            </div>
            <div class="knowledge-folder-documents">
              ${group.documents.map((document) => zbudujKarteDokumentuBazyWiedzy(document)).join("")}
            </div>
          </section>
        `
      )
      .join("");
  } else {
    container.innerHTML = filteredDocuments.map((document) => zbudujKarteDokumentuBazyWiedzy(document)).join("");
  }

  podpinaAkcjeListyDokumentowBazyWiedzy(container);

  if (stan.odpowiedzBazyWiedzy) {
    renderujOdpowiedzBazyWiedzy(stan.odpowiedzBazyWiedzy);
  } else {
    document.getElementById("knowledge-answer-empty").classList.remove("hidden");
    document.getElementById("knowledge-answer").classList.add("hidden");
    document.getElementById("knowledge-answer").innerHTML = "";
  }
  renderujPodgladDokumentuBazyWiedzy();
  renderujPanelAdministratoraBazyWiedzy();
  renderujPodpowiedziPytanBazyWiedzy();
  odswiezStanBazyWiedzy();
}

function renderujOdpowiedzBazyWiedzy(wynik) {
  stan.odpowiedzBazyWiedzy = wynik;
  const emptyState = document.getElementById("knowledge-answer-empty");
  const container = document.getElementById("knowledge-answer");
  emptyState.classList.add("hidden");
  container.classList.remove("hidden");
  const zrodla = (wynik.matches || [])
    .map(
      (match) => `
        <article class="knowledge-source-item">
          <div class="knowledge-doc-header">
            <strong>${bezpiecznyTekst(match.citation_label || match.title)}</strong>
            <span class="status-badge ${klasaStatusuPrzetwarzaniaBazyWiedzy(match.processing_status || "ready")}">${bezpiecznyTekst(
              formatujStatusPrzetwarzaniaBazyWiedzy(match.processing_status || "ready")
            )}</span>
          </div>
          <p>${bezpiecznyTekst(match.snippet)}</p>
          <div class="knowledge-doc-meta">
            <span>Wynik dopasowania: ${bezpiecznyTekst(match.score)}</span>
            <span>Wersja: ${bezpiecznyTekst(match.version_number || 0)}</span>
            <span>Przetworzono: ${formatujDateCzas(match.last_processed_at || match.updated_at)}</span>
            <a href="${bezpiecznyTekst(match.file_link)}" target="_blank" rel="noreferrer">Zrodlo</a>
          </div>
          <div class="knowledge-admin-actions">
            <p class="subtle-note">Kliknij, aby przejsc do podgladu tego dokumentu i jego wersji.</p>
            <button type="button" class="secondary" data-knowledge-focus-id="${match.knowledge_document_id}">Pokaz dokument</button>
          </div>
        </article>
      `
    )
    .join("");

  container.innerHTML = `
    <div class="knowledge-answer-box">
      <div class="knowledge-answer-main">${bezpiecznyTekst(wynik.answer || "")}</div>
      ${
        zrodla
          ? `<div class="knowledge-source-list">${zrodla}</div>`
          : `<div class="empty-state">Brak bezposrednich zrodel do pokazania.</div>`
      }
    </div>
  `;

  container.querySelectorAll("[data-knowledge-focus-id]").forEach((button) => {
    button.addEventListener("click", () => {
      ustawWidok("knowledge");
      ustawWybranyDokumentBazyWiedzy(button.dataset.knowledgeFocusId);
    });
  });
}

async function wczytajBazeWiedzy() {
  zapewnijStanRozszerzenBazyWiedzy();
  if (!stan.biezacyUzytkownik) {
    wyczyscBazeWiedzy();
    anulujPollingBazyWiedzy();
    return;
  }
  if (!czyModulWiedzyMaZakres()) {
    wyczyscBazeWiedzy();
    document.getElementById("knowledge-access-note").textContent =
      "Wybierz konkretna organizacje, aby otworzyc jej baze wiedzy.";
    anulujPollingBazyWiedzy();
    return;
  }

  const wynik = await api(zbudujAdresZOrganizacja("/api/knowledge/documents"));
  renderujBazeWiedzy(wynik);
}

function wyczyscBazeWiedzy() {
  zapewnijStanRozszerzenBazyWiedzy();
  anulujPollingBazyWiedzy();
  stan.dokumentyWiedzy = [];
  stan.odpowiedzBazyWiedzy = null;
  stan.folderBazyWiedzy = "";
  stan.konfiguracjaBazyWiedzy = null;
  stan.ostatniImportBazyWiedzy = null;
  stan.ostatniPayloadBazyWiedzy = null;
  stan.wybranyDokumentWiedzyId = null;
  document.getElementById("knowledge-count").textContent = "";
  document.getElementById("knowledge-folder-path").textContent = "-";
  document.getElementById("knowledge-documents-summary").textContent = "";
  document.getElementById("knowledge-documents").innerHTML = `<div class="empty-state">Brak dokumentow w bazie wiedzy.</div>`;
  document.getElementById("knowledge-answer-empty").classList.remove("hidden");
  document.getElementById("knowledge-answer").classList.add("hidden");
  document.getElementById("knowledge-answer").innerHTML = "";
  document.getElementById("knowledge-title").value = "";
  document.getElementById("knowledge-file").value = "";
  document.getElementById("knowledge-content").value = "";
  document.getElementById("knowledge-question").value = "";
  const pipeline = document.getElementById("knowledge-pipeline-summary");
  if (pipeline) {
    pipeline.innerHTML = "";
  }
  const versionBadge = document.getElementById("knowledge-selected-version");
  if (versionBadge) {
    versionBadge.textContent = "";
  }
  const selectedDocument = document.getElementById("knowledge-selected-document");
  if (selectedDocument) {
    selectedDocument.className = "empty-state";
    selectedDocument.textContent = "Wybierz dokument z listy, aby zobaczyc szczegoly, wersje i fragmenty tresci.";
  }
  odswiezPanelImportuBazyWiedzy();
  renderujPanelAdministratoraBazyWiedzy();
  odswiezStanBazyWiedzy();
}

async function start() {
  try {
    zapewnijStanRozszerzenBazyWiedzy();
    inicjalizujRozszerzeniaBazyWiedzy();
    podepnijZdarzenia();
    odswiezPanelImportuBazyWiedzy();
    ustawWidocznoscElementowSrodowiska();
    ustawWidocznoscFiltrowFaktur(false);
    await wczytajMeta();
    renderujCapabilitiesFormularzaUzytkownika();
    renderujPanelAdministratoraBazyWiedzy();
    renderujPodgladDokumentuBazyWiedzy();
    const maSesje = await sprobujPrzywrocicSesje();
    if (maSesje) {
      await odswiezDanePoZalogowaniu();
    } else {
      odswiezStanBazyWiedzy();
    }
  } catch (error) {
    pokazPowiadomienie(error.message);
  }
}

function formatujStatusJobaBazyWiedzy(status) {
  const labels = {
    pending: "oczekuje",
    processing: "przetwarzanie",
    completed: "zakonczone",
    failed: "blad",
  };
  return labels[status] || "oczekuje";
}

function klasaStatusuJobaBazyWiedzy(status) {
  if (status === "completed") return "status-success";
  if (status === "failed") return "status-danger";
  if (status === "processing") return "status-warning";
  return "status-normal";
}

function formatujTypJobaBazyWiedzy(jobType) {
  return jobType === "reprocess" ? "ponowne przetwarzanie" : "import";
}

function ustawWybranyDokumentBazyWiedzy(knowledgeDocumentId, options = {}) {
  zapewnijStanRozszerzenBazyWiedzy();
  stan.wybranyDokumentWiedzyId = knowledgeDocumentId ? Number(knowledgeDocumentId) : null;
  if (options.rerender === false) {
    renderujPodgladDokumentuBazyWiedzy();
    return;
  }
  odswiezWidokBazyWiedzyZPamieci();
}

function zbudujWersjeDokumentuBazyWiedzy(dokument) {
  if (!(dokument.versions || []).length) {
    return `<div class="empty-state">Ten dokument nie ma jeszcze zapisanych wersji.</div>`;
  }
  return dokument.versions
    .map(
      (version) => `
        <article class="knowledge-version-item">
          <div class="knowledge-doc-selection">
            <strong>Wersja v${bezpiecznyTekst(version.version_number)}</strong>
            <span class="pill history-pill">${bezpiecznyTekst(version.extraction_method || "import")}</span>
          </div>
          <div class="knowledge-preview-meta">
            <span>Znaki: ${bezpiecznyTekst(version.char_count || 0)}</span>
            <span>Zrodlo: ${bezpiecznyTekst(formatujZrodloBazyWiedzy(version.source_type || "manual"))}</span>
            <span>Utworzono: ${formatujDateCzas(version.created_at)}</span>
          </div>
          <p class="knowledge-version-snippet">${bezpiecznyTekst(version.snippet || "Brak fragmentu tresci dla tej wersji.")}</p>
        </article>
      `
    )
    .join("");
}

function zbudujZadaniaPrzetwarzaniaBazyWiedzy(dokument) {
  if (!(dokument.recent_jobs || []).length) {
    return `<div class="empty-state">Brak zapisanych zadan przetwarzania.</div>`;
  }
  return dokument.recent_jobs
    .map(
      (job) => `
        <article class="knowledge-version-item">
          <div class="knowledge-doc-selection">
            <strong>${bezpiecznyTekst(formatujTypJobaBazyWiedzy(job.job_type || "ingest"))}</strong>
            <span class="status-badge ${klasaStatusuJobaBazyWiedzy(job.status)}">${bezpiecznyTekst(formatujStatusJobaBazyWiedzy(job.status))}</span>
          </div>
          <div class="knowledge-preview-meta">
            <span>Proby: ${bezpiecznyTekst(job.attempts || 0)}</span>
            <span>Utworzono: ${formatujDateCzas(job.created_at)}</span>
            <span>Start: ${formatujDateCzas(job.started_at)}</span>
            <span>Koniec: ${formatujDateCzas(job.finished_at)}</span>
          </div>
          ${job.error_message ? `<p class="knowledge-version-snippet">${bezpiecznyTekst(job.error_message)}</p>` : ""}
        </article>
      `
    )
    .join("");
}

function renderujPodgladDokumentuBazyWiedzy() {
  const container = document.getElementById("knowledge-selected-document");
  const versionBadge = document.getElementById("knowledge-selected-version");
  if (!container || !versionBadge) {
    return;
  }

  const filteredDocuments = pobierzPrzefiltrowaneDokumentyBazyWiedzy();
  let selectedDocument = pobierzDokumentBazyWiedzy(stan.wybranyDokumentWiedzyId);
  if (!filteredDocuments.some((item) => Number(item.knowledge_document_id) === Number(stan.wybranyDokumentWiedzyId))) {
    selectedDocument = filteredDocuments[0] || null;
    stan.wybranyDokumentWiedzyId = selectedDocument ? Number(selectedDocument.knowledge_document_id) : null;
  }

  if (!selectedDocument) {
    versionBadge.textContent = "";
    container.className = "empty-state";
    container.textContent = filteredDocuments.length
      ? "Wybierz dokument z listy, aby zobaczyc podglad."
      : "Brak dokumentu pasujacego do biezacych filtrow lub tej organizacji. Dodaj dokument albo wyczysc filtry.";
    return;
  }

  versionBadge.textContent = `v${selectedDocument.current_version_number || 0} | ${formatujStatusPrzetwarzaniaBazyWiedzy(
    selectedDocument.processing_status || "queued"
  )}`;
  container.className = "";
  const createdBy = selectedDocument.created_by_display_name || selectedDocument.created_by_login || "system";
  const retryButton = czyMoznaZarzadzacPrzetwarzaniemBazyWiedzy()
    ? `<button type="button" class="secondary" data-knowledge-preview-retry="${selectedDocument.knowledge_document_id}">Ponow przetwarzanie</button>`
    : "";
  container.innerHTML = `
    <div class="knowledge-preview-card">
      <div class="knowledge-doc-selection">
        <div>
          <div class="knowledge-doc-title">${bezpiecznyTekst(selectedDocument.title)}</div>
          <div class="knowledge-doc-badges">
            <span class="status-badge ${klasaStatusuPrzetwarzaniaBazyWiedzy(selectedDocument.processing_status || "queued")}">${bezpiecznyTekst(
              formatujStatusPrzetwarzaniaBazyWiedzy(selectedDocument.processing_status || "queued")
            )}</span>
            <span class="status-badge ${klasaStatusuZrodlaBazyWiedzy(selectedDocument.source_type || "manual")}">${bezpiecznyTekst(
              formatujZrodloBazyWiedzy(selectedDocument.source_type || "manual")
            )}</span>
            <span class="pill history-pill">${bezpiecznyTekst(selectedDocument.file_name || "-")}</span>
          </div>
        </div>
        <div class="filters-actions">
          <a href="${bezpiecznyTekst(selectedDocument.file_link)}" target="_blank" rel="noreferrer">Otworz plik</a>
          ${retryButton}
        </div>
      </div>
      <div class="knowledge-preview-meta">
        <span>Znaki: ${bezpiecznyTekst(selectedDocument.char_count || 0)}</span>
        <span>Dodane przez: ${bezpiecznyTekst(createdBy)}</span>
        <span>Ostatnie przetworzenie: ${formatujDateCzas(selectedDocument.last_processed_at || selectedDocument.updated_at)}</span>
      </div>
      <div class="knowledge-preview-main">${bezpiecznyTekst(
        selectedDocument.content_preview || selectedDocument.snippet || "Dokument jest jeszcze przetwarzany."
      )}</div>
      ${
        selectedDocument.processing_error
          ? `<div class="knowledge-error-note">${bezpiecznyTekst(selectedDocument.processing_error)}</div>`
          : ""
      }
      <div class="knowledge-preview-versions">
        <strong>Historia wersji</strong>
        ${zbudujWersjeDokumentuBazyWiedzy(selectedDocument)}
      </div>
      <div class="knowledge-preview-versions">
        <strong>Kolejka i zadania przetwarzania</strong>
        ${zbudujZadaniaPrzetwarzaniaBazyWiedzy(selectedDocument)}
      </div>
    </div>
  `;

  const retry = container.querySelector("[data-knowledge-preview-retry]");
  if (retry) {
    retry.addEventListener("click", async () => {
      try {
        await api(
          zbudujAdresZOrganizacja(`/api/knowledge/documents/${retry.dataset.knowledgePreviewRetry}/reprocess`),
          { method: "POST" }
        );
        pokazPowiadomienie("Dokument dodany ponownie do kolejki.");
        await Promise.all([wczytajBazeWiedzy(), wczytajLogi()]);
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
    });
  }
}

function renderujPanelAdministratoraBazyWiedzy() {
  const container = document.getElementById("knowledge-admin-panel");
  const count = document.getElementById("knowledge-admin-count");
  if (!container || !count) {
    return;
  }

  if (!stan.biezacyUzytkownik) {
    count.textContent = "";
    container.className = "empty-state";
    container.textContent = "Zaloguj sie, aby zobaczyc prawa dostepu do bazy wiedzy.";
    return;
  }

  if (!czyModulWiedzyMaZakres()) {
    count.textContent = "";
    container.className = "empty-state";
    container.textContent = "Wybierz konkretna organizacje, aby zarzadzac uprawnieniami wiedzy.";
    return;
  }

  if (!czyMoznaZarzadzacUzytkownikami()) {
    const myCapabilities = pobierzCapabilitiesUzytkownika();
    count.textContent = `${myCapabilities.length} praw`;
    container.className = "";
    container.innerHTML = `
      <article class="knowledge-admin-user">
        <div class="knowledge-admin-header">
          <div>
            <strong>Twoje prawa w module wiedzy</strong>
            <p class="subtle-note">To konto nie moze zmieniac uprawnien innych osob, ale widzi swoj aktualny zakres.</p>
          </div>
          <div>${zbudujWidokCapabilityPills(myCapabilities)}</div>
        </div>
      </article>
    `;
    return;
  }

  const users = Array.isArray(stan.uzytkownicy) ? stan.uzytkownicy : [];
  count.textContent = `${users.length} kont`;
  if (!users.length) {
    container.className = "empty-state";
    container.textContent = "Brak kont w tej organizacji albo lista uzytkownikow nie zostala jeszcze zaladowana.";
    return;
  }

  const summaryPills = (stan.meta?.knowledge_capabilities || Object.keys(capabilityLabels))
    .map((capability) => {
      const usersWithCapability = users.filter((item) => (item.capabilities || []).includes(capability)).length;
      return `<span class="pill history-pill">${bezpiecznyTekst(capabilityLabels[capability] || capability)}: ${bezpiecznyTekst(
        usersWithCapability
      )}</span>`;
    })
    .join("");

  container.className = "";
  container.innerHTML = `
    <div class="knowledge-admin-summary">${summaryPills}</div>
    <div class="knowledge-admin-list">
      ${users
        .map((user) => {
          const capabilities = new Set(user.capabilities || []);
          capabilities.add("knowledge.read");
          const isGuestRole = user.role === "guest";
          const capabilityCheckboxes = (stan.meta?.knowledge_capabilities || Object.keys(capabilityLabels))
            .map((capability) => {
              const checked = capabilities.has(capability) ? "checked" : "";
              const disabled = capability === "knowledge.read" || isGuestRole ? "disabled" : "";
              return `
                <label>
                  <input
                    type="checkbox"
                    data-knowledge-admin-capability="${bezpiecznyTekst(capability)}"
                    value="${bezpiecznyTekst(capability)}"
                    ${checked}
                    ${disabled}
                  />
                  <span>${bezpiecznyTekst(capabilityLabels[capability] || capability)}</span>
                </label>
              `;
            })
            .join("");
          return `
            <article class="knowledge-admin-user" data-knowledge-admin-user="${user.user_id}">
              <div class="knowledge-admin-header">
                <div>
                  <strong>${bezpiecznyTekst(user.display_name || user.login)}</strong>
                  <p class="subtle-note">
                    Login: ${bezpiecznyTekst(user.login)} | Rola: ${bezpiecznyTekst(formatujRole(user.role))}
                  </p>
                </div>
                <div>${zbudujWidokCapabilityPills(user.capabilities || [])}</div>
              </div>
              <div class="knowledge-admin-capabilities">${capabilityCheckboxes}</div>
              <div class="knowledge-admin-actions">
                <p class="subtle-note">
                  ${
                    isGuestRole
                      ? "Rola gosc pozostaje tylko do odczytu. Aby dac szerszy dostep, zmien role uzytkownika."
                      : "Zmiany zapisuja sie tylko dla modulu wiedzy w aktualnej organizacji."
                  }
                </p>
                <button type="button" class="secondary knowledge-admin-save" data-knowledge-admin-save="${user.user_id}">
                  Zapisz prawa
                </button>
              </div>
            </article>
          `;
        })
        .join("")}
    </div>
  `;

  container.querySelectorAll("[data-knowledge-admin-save]").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        await zapiszUprawnieniaBazyWiedzyDlaUzytkownika(button.dataset.knowledgeAdminSave, button);
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
    });
  });
}

async function zapiszUprawnieniaBazyWiedzyDlaUzytkownika(userId, button) {
  if (!czyMoznaZarzadzacUzytkownikami()) {
    pokazPowiadomienie("To konto nie moze zmieniac praw innych uzytkownikow.");
    return;
  }
  const row = button?.closest?.("[data-knowledge-admin-user]");
  if (!row) {
    throw new Error("Nie znaleziono formularza praw tego uzytkownika.");
  }
  const selectedCapabilities = Array.from(row.querySelectorAll("[data-knowledge-admin-capability]:checked"))
    .map((input) => input.value)
    .filter(Boolean);
  if (!selectedCapabilities.includes("knowledge.read")) {
    selectedCapabilities.unshift("knowledge.read");
  }

  button.disabled = true;
  button.classList.add("is-busy");
  const savedUser = await api(`/api/users/${userId}`, {
    method: "PATCH",
    body: JSON.stringify({
      capabilities: selectedCapabilities,
      can_upload_knowledge: selectedCapabilities.includes("knowledge.upload"),
    }),
  });
  const editedCurrentUser =
    stan.biezacyUzytkownik && Number(savedUser.user_id) === Number(stan.biezacyUzytkownik.user_id);
  if (editedCurrentUser) {
    stan.biezacyUzytkownik = savedUser;
    odswiezPasekSesji();
  }

  await wczytajLogi();
  if (czyMoznaZarzadzacUzytkownikami()) {
    await wczytajUzytkownikow();
  } else {
    stan.uzytkownicy = [];
    renderujPanelAdministratoraBazyWiedzy();
  }

  if (editedCurrentUser) {
    try {
      await wczytajBazeWiedzy();
    } catch (error) {
      wyczyscBazeWiedzy();
      odswiezStanBazyWiedzy();
    }
  } else {
    odswiezStanBazyWiedzy();
  }
  pokazPowiadomienie(`Zapisano prawa wiedzy dla konta ${savedUser.login}.`);
}

function inicjalizujRozszerzeniaBazyWiedzy() {
  zapewnijStanRozszerzenBazyWiedzy();
  if (stan.czyRozszerzeniaBazyWiedzyPodpiete) {
    return;
  }
  stan.czyRozszerzeniaBazyWiedzyPodpiete = true;

  ["knowledge-filter-lifecycle", "knowledge-filter-status", "knowledge-filter-source"].forEach((id) =>
    document.getElementById(id)?.addEventListener("change", () => {
      odczytajFiltryBazyWiedzyZFormularza();
      zaplanujAutomatyczneFiltrowanie("knowledgeFilterApplyTimeoutId", odswiezWidokBazyWiedzyZPamieci, 0);
    })
  );
  document.getElementById("knowledge-filter-search")?.addEventListener("input", () => {
    odczytajFiltryBazyWiedzyZFormularza();
    zaplanujAutomatyczneFiltrowanie("knowledgeFilterApplyTimeoutId", odswiezWidokBazyWiedzyZPamieci, 250);
  });
  document.getElementById("knowledge-clear-filters")?.addEventListener("click", () => {
    stan.filtryBazyWiedzy = { lifecycle: "", status: "", source: "", search: "" };
    zsynchronizujFiltryBazyWiedzyZFormularzem();
    odswiezWidokBazyWiedzyZPamieci();
  });
}

async function wczytajUzytkownikow() {
  if (!czyMoznaZarzadzacUzytkownikami()) {
    stan.uzytkownicy = [];
    stan.googleCalendarAdminUsers = [];
    document.getElementById("users-table-body").innerHTML =
      `<tr><td colspan="14">Panel uzytkownikow jest dostepny tylko dla Wlasciciela systemu albo Administratora organizacji.</td></tr>`;
    odswiezPoleDelegataKsef(
      stan.wybranaOrganizacjaFormularzaId || document.getElementById("organization-id")?.value || "",
      "",
      document.getElementById("organization-ksef-delegate-expires-at")?.value || ""
    );
    renderujPanelGoogleKalendarzaUzytkownika(null);
    renderujPanelAdministratoraBazyWiedzy();
    return;
  }
  const [uzytkownicy, snapshot] = await Promise.all([
    api(zbudujAdresZOrganizacja("/api/users")),
    wczytajGoogleCalendarAdminUsers(),
  ]);
  const snapshotMap = new Map(
    (Array.isArray(snapshot) ? snapshot : []).map((item) => [Number(item.user_id), item])
  );
  const mergedUsers = (Array.isArray(uzytkownicy) ? uzytkownicy : []).map((uzytkownik) => ({
    ...uzytkownik,
    ...(snapshotMap.get(Number(uzytkownik.user_id)) || {}),
  }));
  renderujUzytkownikow(mergedUsers);
  if (stan.wybranyUzytkownikId) {
    const refreshedSelectedUser = mergedUsers.find(
      (item) => Number(item.user_id) === Number(stan.wybranyUzytkownikId)
    );
    if (refreshedSelectedUser) {
      await wypelnijFormularzUzytkownika(refreshedSelectedUser);
    } else {
      wyczyscFormularzUzytkownika();
    }
  }
  renderujPanelAdministratoraBazyWiedzy();
}

function odswiezStanBazyWiedzy() {
  const przyciskZapisu = document.getElementById("knowledge-save-button");
  const przyciskSynchronizacji = document.getElementById("knowledge-sync-button");
  const komunikat = document.getElementById("knowledge-access-note");
  const poleTytulu = document.getElementById("knowledge-title");
  const polePliku = document.getElementById("knowledge-file");
  const poleTresci = document.getElementById("knowledge-content");
  const polePytania = document.getElementById("knowledge-question");
  const przyciskPytania = document.querySelector('#knowledge-question-form button[type="submit"]');
  const filterControls = [
    document.getElementById("knowledge-filter-status"),
    document.getElementById("knowledge-filter-source"),
    document.getElementById("knowledge-filter-search"),
    document.getElementById("knowledge-clear-filters"),
  ];
  if (!przyciskZapisu || !przyciskSynchronizacji || !komunikat) {
    return;
  }

  if (!stan.biezacyUzytkownik) {
    przyciskZapisu.disabled = true;
    przyciskSynchronizacji.disabled = true;
    [poleTytulu, polePliku, poleTresci, polePytania, przyciskPytania, ...filterControls].forEach(
      (element) => element && (element.disabled = true)
    );
    komunikat.textContent = "Zaloguj sie, aby korzystac z bazy wiedzy.";
    anulujPollingBazyWiedzy();
    renderujPanelAdministratoraBazyWiedzy();
    renderujPodgladDokumentuBazyWiedzy();
    renderujPodpowiedziPytanBazyWiedzy();
    return;
  }

  const brakWyboruOrganizacji = czyGlobalnyAdministrator() && !stan.wybranaOrganizacjaId;
  const moznaImportowac = !brakWyboruOrganizacji && czyMoznaDodawacPlikiDoBazyWiedzy();
  const moznaSynchronizowac = !brakWyboruOrganizacji && czyMoznaSynchronizowacBazeWiedzy();
  const moznaCzytac = czyModulWiedzyMaZakres() && czyMoznaCzytacBazeWiedzy();
  przyciskZapisu.disabled = !moznaImportowac;
  przyciskSynchronizacji.disabled = !moznaSynchronizowac;
  [poleTytulu, polePliku, poleTresci].forEach((element) => element && (element.disabled = !moznaImportowac));
  [polePytania, przyciskPytania, ...filterControls].forEach((element) => element && (element.disabled = !moznaCzytac));

  if (brakWyboruOrganizacji) {
    komunikat.textContent = "Wybierz konkretna organizacje, aby pracowac na jej bazie wiedzy.";
  } else if (!czyMoznaCzytacBazeWiedzy()) {
    komunikat.textContent = "To konto nie ma dostepu do modulu wiedzy.";
  } else if (!czyMoznaDodawacPlikiDoBazyWiedzy()) {
    komunikat.textContent = "Mozesz czytac i pytac, ale import plikow jest zablokowany dla tego konta.";
  } else {
    komunikat.textContent = czyMoznaZarzadzacPrzetwarzaniemBazyWiedzy()
      ? "Masz pelen dostep do bazy wiedzy, synchronizacji i kolejek przetwarzania."
      : "Mozesz dodawac dokumenty, synchronizowac folder i zadawac pytania do bazy wiedzy.";
  }
  odswiezPanelImportuBazyWiedzy();
  renderujPanelAdministratoraBazyWiedzy();
  renderujPodgladDokumentuBazyWiedzy();
  renderujPodpowiedziPytanBazyWiedzy();
  zaplanujPollingBazyWiedzy();
}

function renderujBazeWiedzy(payload) {
  zapewnijStanRozszerzenBazyWiedzy();
  if (stan.ostatniImportBazyWiedzy && Number(stan.ostatniImportBazyWiedzy.organization_id || 0) !== Number(payload.organization_id || 0)) {
    stan.ostatniImportBazyWiedzy = null;
  }

  stan.ostatniPayloadBazyWiedzy = payload;
  stan.dokumentyWiedzy = payload.documents || [];
  stan.folderBazyWiedzy = payload.folder_path || "";
  stan.konfiguracjaBazyWiedzy = {
    organization_id: payload.organization_id,
    supported_formats: payload.supported_formats || [],
    ocr_enabled: Boolean(payload.ocr_enabled),
    ocr_mode: payload.ocr_mode || "fallback",
    document_summary: payload.document_summary || {},
  };

  const summary = payload.document_summary || {};
  const allDocuments = stan.dokumentyWiedzy || [];
  const filteredDocuments = pobierzPrzefiltrowaneDokumentyBazyWiedzy();
  if (!filteredDocuments.some((item) => Number(item.knowledge_document_id) === Number(stan.wybranyDokumentWiedzyId))) {
    stan.wybranyDokumentWiedzyId = filteredDocuments[0]?.knowledge_document_id || null;
  }

  document.getElementById("knowledge-count").textContent = `${allDocuments.length} dokumentow`;
  document.getElementById("knowledge-folder-path").textContent = stan.folderBazyWiedzy || "-";
  document.getElementById("knowledge-documents-summary").textContent = allDocuments.length
    ? `Pokazano ${filteredDocuments.length} z ${allDocuments.length} dokumentow w tej organizacji.`
    : "Ta organizacja nie ma jeszcze zadnych dokumentow wiedzy.";
  zsynchronizujFiltryBazyWiedzyZFormularzem();

  const pipeline = document.getElementById("knowledge-pipeline-summary");
  if (pipeline) {
    pipeline.innerHTML = `
      <span class="pill history-pill">gotowe: ${bezpiecznyTekst(summary.ready || 0)}</span>
      <span class="pill history-pill">kolejka: ${bezpiecznyTekst(summary.queued || 0)}</span>
      <span class="pill history-pill">przetwarzanie: ${bezpiecznyTekst(summary.processing || 0)}</span>
      <span class="pill history-pill">bledy: ${bezpiecznyTekst(summary.error || 0)}</span>
    `;
  }

  const container = document.getElementById("knowledge-documents");
  if (!filteredDocuments.length) {
    container.innerHTML = `<div class="empty-state">${
      allDocuments.length
        ? "Zadne dokumenty nie pasuja do biezacych filtrow. Wyczysc filtry albo zmien wyszukiwana fraze."
        : "Ta organizacja nie ma jeszcze zadnych dokumentow wiedzy. Dodaj pierwszy plik albo uzyj synchronizacji folderu."
    }</div>`;
    if (stan.odpowiedzBazyWiedzy) {
      renderujOdpowiedzBazyWiedzy(stan.odpowiedzBazyWiedzy);
    } else {
      document.getElementById("knowledge-answer-empty").classList.remove("hidden");
      document.getElementById("knowledge-answer").classList.add("hidden");
      document.getElementById("knowledge-answer").innerHTML = "";
    }
    renderujPodgladDokumentuBazyWiedzy();
    renderujPanelAdministratoraBazyWiedzy();
    renderujPodpowiedziPytanBazyWiedzy();
    odswiezStanBazyWiedzy();
    return;
  }

  container.innerHTML = filteredDocuments
    .map((dokument) => {
      const extension = String(dokument.file_name || "").includes(".")
        ? String(dokument.file_name).split(".").pop().toUpperCase()
        : "";
      const createdBy = dokument.created_by_display_name || dokument.created_by_login;
      const isSelected = Number(dokument.knowledge_document_id) === Number(stan.wybranyDokumentWiedzyId);
      const retryButton = czyMoznaZarzadzacPrzetwarzaniemBazyWiedzy()
        ? `<button type="button" class="secondary" data-knowledge-retry-id="${dokument.knowledge_document_id}">Ponow przetwarzanie</button>`
        : "";
      return `
        <article class="list-item knowledge-doc-item ${isSelected ? "is-selected" : ""}" data-knowledge-select-id="${dokument.knowledge_document_id}">
          <div class="knowledge-doc-header">
            <div>
              <div class="knowledge-doc-title">${bezpiecznyTekst(dokument.title)}</div>
              <div class="knowledge-doc-badges">
                <span class="status-badge ${klasaStatusuPrzetwarzaniaBazyWiedzy(dokument.processing_status)}">${bezpiecznyTekst(
                  formatujStatusPrzetwarzaniaBazyWiedzy(dokument.processing_status)
                )}</span>
                <span class="status-badge ${klasaStatusuZrodlaBazyWiedzy(dokument.source_type || "manual")}">${bezpiecznyTekst(
                  formatujZrodloBazyWiedzy(dokument.source_type || "manual")
                )}</span>
                ${extension ? `<span class="pill knowledge-doc-pill">${bezpiecznyTekst(extension)}</span>` : ""}
                <span class="pill history-pill">v${bezpiecznyTekst(dokument.current_version_number || 0)}</span>
              </div>
            </div>
            <div class="filters-actions">
              <button type="button" class="secondary" data-knowledge-open-id="${dokument.knowledge_document_id}">Podglad</button>
              ${retryButton}
            </div>
          </div>
          <div>${bezpiecznyTekst(dokument.snippet || "Brak podgladu tresci.")}</div>
          ${dokument.processing_error ? `<div class="knowledge-error-note">${bezpiecznyTekst(dokument.processing_error)}</div>` : ""}
          <div class="knowledge-doc-meta">
            <span>Plik: ${bezpiecznyTekst(dokument.file_name)}</span>
            <span>Znaki: ${bezpiecznyTekst(dokument.char_count)}</span>
            <span>Przetworzono: ${formatujDateCzas(dokument.last_processed_at || dokument.updated_at)}</span>
            ${createdBy ? `<span>Dodane przez: ${bezpiecznyTekst(createdBy)}</span>` : ""}
            <a href="${bezpiecznyTekst(dokument.file_link)}" target="_blank" rel="noreferrer">Otworz plik</a>
          </div>
          ${zbudujHistorieDokumentuBazyWiedzy(dokument)}
        </article>
      `;
    })
    .join("");

  container.querySelectorAll("[data-knowledge-select-id]").forEach((element) => {
    element.addEventListener("click", (event) => {
      if (event.target?.closest?.("[data-knowledge-retry-id], [data-knowledge-open-id], a")) {
        return;
      }
      ustawWybranyDokumentBazyWiedzy(element.dataset.knowledgeSelectId);
    });
  });
  container.querySelectorAll("[data-knowledge-open-id]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      ustawWybranyDokumentBazyWiedzy(button.dataset.knowledgeOpenId);
    });
  });
  container.querySelectorAll("[data-knowledge-retry-id]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      try {
        await api(zbudujAdresZOrganizacja(`/api/knowledge/documents/${button.dataset.knowledgeRetryId}/reprocess`), {
          method: "POST",
        });
        pokazPowiadomienie("Dokument dodany ponownie do kolejki.");
        await Promise.all([wczytajBazeWiedzy(), wczytajLogi()]);
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
    });
  });

  if (stan.odpowiedzBazyWiedzy) {
    renderujOdpowiedzBazyWiedzy(stan.odpowiedzBazyWiedzy);
  } else {
    document.getElementById("knowledge-answer-empty").classList.remove("hidden");
    document.getElementById("knowledge-answer").classList.add("hidden");
    document.getElementById("knowledge-answer").innerHTML = "";
  }
  renderujPodgladDokumentuBazyWiedzy();
  renderujPanelAdministratoraBazyWiedzy();
  renderujPodpowiedziPytanBazyWiedzy();
  odswiezStanBazyWiedzy();
}
