const stan = {
  meta: null,
  faktury: [],
  zadania: [],
  kontrahenciWszyscy: [],
  kontrahenciWidoczni: [],
  logi: [],
  organizacje: [],
  uzytkownicy: [],
  uzytkownicyDoZadan: [],
  biezacyUzytkownik: null,
  wybranaFakturaId: null,
  wybraneZadanieId: null,
  wybranyKontrahentId: null,
  wybranaOrganizacjaId: "",
  wybranaOrganizacjaFormularzaId: null,
  czyZakresOrganizacjiZainicjalizowany: false,
  wybranyUzytkownikId: null,
  aktywnyWidok: "dashboard",
  czyFiltryFakturRozwiniete: false,
  czyZdarzeniaPodpiete: false,
  filtryKontrahentow: {
    szukaj: "",
    tylkoNowi: false,
  },
};

const opisyWidokow = {
  dashboard: {
    tytul: "Pulpit",
    podtytul: "Podgląd najważniejszych wskaźników i ostatnich zdarzeń.",
  },
  invoices: {
    tytul: "Faktury",
    podtytul: "Wyszukiwanie, filtrowanie i ręczna weryfikacja dokumentów.",
  },
  tasks: {
    tytul: "Asystent Szefa",
    podtytul: "Zadania, wydarzenia, terminy i notatki dla zespolu.",
  },
  contractors: {
    tytul: "Kontrahenci",
    podtytul: "Przegląd kontrahentów, nowych podmiotów i powiązanych faktur.",
  },
  logs: {
    tytul: "Historia systemu",
    podtytul: "Pełna historia zmian, decyzji i zdarzeń systemowych.",
  },
  organizations: {
    tytul: "Organizacje",
    podtytul: "Oddzielenie danych klientów, folderów i użytkowników według organizacji.",
  },
  users: {
    tytul: "Użytkownicy",
    podtytul: "Konta użytkowników, role i podstawowa administracja dostępem.",
  },
};

const etykietyZrodel = {
  KSeF: "KSeF",
  EMAIL: "E-mail",
  TELEGRAM: "Telegram",
};

const etykietyZdarzen = {
  invoice_created: "Dodanie faktury",
  invoice_updated: "Aktualizacja faktury",
  invoice_status_changed: "Zmiana statusu faktury",
  duplicate_detected: "Wykrycie duplikatu",
  duplicate_rejected: "Odrzucenie podejrzenia duplikatu",
  duplicate_confirmed: "Potwierdzenie duplikatu",
  contractor_created: "Utworzenie kontrahenta",
  telegram_notification_prepared: "Przygotowanie powiadomienia Telegram",
  mock_import_executed: "Wykonanie importu testowego",
  user_created: "Utworzenie użytkownika",
  user_updated: "Aktualizacja użytkownika",
  user_login: "Logowanie użytkownika",
  user_logout: "Wylogowanie użytkownika",
  organization_created: "Utworzenie organizacji",
  organization_updated: "Aktualizacja organizacji",
  task_created: "Dodanie zadania",
  task_updated: "Aktualizacja zadania",
  task_note_added: "Dodanie notatki do zadania",
};

const etykietyRol = {
  administrator: "Administrator",
  operator: "Operator",
  podglad: "Podgląd",
};

const etykietyTypowZadan = {
  zadanie: "Zadanie",
  wydarzenie: "Wydarzenie",
  przypomnienie: "Przypomnienie",
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
    etykieta: "Podejrzenia duplikatów",
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
    return "Nie można dodać dokumentu, ponieważ identyczna faktura została już wcześniej zapisana.";
  }

  return tekst || "Wystąpił błąd.";
}

async function api(url, options = {}, ustawienia = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    credentials: "same-origin",
    ...options,
  });

  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : await response.text();

  if (!response.ok) {
    const rawMessage = typeof payload === "string" ? payload : payload.error || "Wystąpił błąd.";
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
  return etykietyRol[value] || bezpiecznyTekst(value);
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

function pobierzStanPrzypomnienia(task) {
  if (!task?.remind_at) {
    return { etykieta: "Brak", klasa: "status-normal" };
  }
  if (["zakonczone", "anulowane"].includes(task.status)) {
    return { etykieta: "Zamkniete", klasa: "status-success" };
  }
  const przypomnienie = new Date(task.remind_at);
  if (Number.isNaN(przypomnienie.getTime())) {
    return { etykieta: "Zaplanowane", klasa: "status-normal" };
  }
  return przypomnienie <= new Date()
    ? { etykieta: "Do przypomnienia", klasa: "status-warning" }
    : { etykieta: "Zaplanowane", klasa: "status-normal" };
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

  if (czyMaZnaczenieDlaKontekstu(event.source)) {
    elementy.push(`Źródło: ${formatujZrodlo(event.source)}`);
  }

  return elementy.join(" | ");
}

function formatujNazweOrganizacji(value) {
  return value ? bezpiecznyTekst(value) : "Brak przypisania";
}

function czyAdministrator() {
  return stan.biezacyUzytkownik?.role === "administrator";
}

function czyGlobalnyAdministrator() {
  return Boolean(stan.biezacyUzytkownik?.is_global_admin);
}

function czyMoznaZapisywac() {
  return ["administrator", "operator"].includes(stan.biezacyUzytkownik?.role || "");
}

function klasaStatusu(status, duplicateType = "") {
  if (duplicateType === "pewny" || status === "pewny_duplikat") return "status-danger";
  if (duplicateType === "podejrzenie" || status === "podejrzenie_duplikatu" || status === "weryfikacja") return "status-warning";
  if (status === "poprawna" || status === "zaksiegowana") return "status-success";
  return "status-normal";
}

function klasaStatusuZadania(status, priority = "") {
  if (status === "anulowane") return "status-danger";
  if (status === "zakonczone") return "status-success";
  if (priority === "krytyczny" || priority === "wysoki" || status === "oczekuje") return "status-warning";
  return "status-normal";
}

function pokazPowiadomienie(message) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.classList.remove("hidden");
  window.clearTimeout(pokazPowiadomienie.timeoutId);
  pokazPowiadomienie.timeoutId = window.setTimeout(() => toast.classList.add("hidden"), 3200);
}

function pokazEkranLogowania() {
  document.body.classList.add("auth-required");
  document.getElementById("login-screen").classList.remove("hidden");
  document.getElementById("session-box").classList.add("hidden");
}

function ukryjEkranLogowania() {
  document.body.classList.remove("auth-required");
  document.getElementById("login-screen").classList.add("hidden");
}

function ustawWidok(widok) {
  if (widok === "users" && !czyAdministrator()) {
    widok = "dashboard";
  }
  if (widok === "organizations" && !czyGlobalnyAdministrator()) {
    widok = "dashboard";
  }
  stan.aktywnyWidok = widok;
  document.querySelectorAll(".view").forEach((sekcja) => sekcja.classList.remove("active"));
  document.getElementById(`${widok}-view`).classList.add("active");
  document.querySelectorAll(".nav-item").forEach((przycisk) => {
    przycisk.classList.toggle("active", przycisk.dataset.view === widok);
  });
  document.getElementById("view-title").textContent = opisyWidokow[widok].tytul;
  document.getElementById("view-subtitle").textContent = opisyWidokow[widok].podtytul;
}

function czyImportTestowyWlaczony() {
  return Boolean(stan.meta?.test_imports_enabled);
}

function znajdzSekcjeImportuTestowego() {
  return document.getElementById("test-import-section");
}

function ustawWidocznoscElementowSrodowiska() {
  const sekcjaImportu = znajdzSekcjeImportuTestowego();
  if (sekcjaImportu) {
    sekcjaImportu.classList.toggle("hidden", !czyImportTestowyWlaczony());
  }

  const podpowiedzLogowania =
    document.getElementById("default-login-hint") || document.querySelector("#login-screen .subtle-note");
  if (podpowiedzLogowania) {
    podpowiedzLogowania.classList.toggle("hidden", !stan.meta?.default_login_hint_enabled);
  }
}

function ustawInformacjeSystemowe() {
  const etykietaBazy = stan.meta?.database_label || "nieznana";
  const statusTelegrama = stan.meta?.telegram_enabled ? "Telegram: aktywny." : "Telegram: wyłączony.";
  const statusImportuTestowego = czyImportTestowyWlaczony() ? "Import testowy: dostepny." : "Import testowy: wylaczony.";
  document.getElementById("system-info").textContent = `Aktywna baza danych: ${etykietaBazy}. ${statusTelegrama} ${statusImportuTestowego}`;
  document.getElementById("sidebar-system-info").textContent =
    `Baza: ${etykietaBazy}. ${statusTelegrama} Dokumenty i pliki OCR są układane w osobnych folderach organizacji.`;
}

function odswiezPasekSesji() {
  const box = document.getElementById("session-box");
  const navUsers = document.getElementById("users-nav-button");
  const navOrganizations = document.getElementById("organizations-nav-button");
  const switcherBox = document.getElementById("organization-switcher-box");
  const sekcjaImportu = znajdzSekcjeImportuTestowego();
  if (sekcjaImportu) {
    sekcjaImportu.classList.toggle("hidden", !czyImportTestowyWlaczony());
  }
  if (!stan.biezacyUzytkownik) {
    box.classList.add("hidden");
    navUsers.classList.add("hidden");
    navOrganizations.classList.add("hidden");
    switcherBox.classList.add("hidden");
    return;
  }

  box.classList.remove("hidden");
  document.getElementById("session-user-name").textContent =
    stan.biezacyUzytkownik.display_name || stan.biezacyUzytkownik.login;
  document.getElementById("session-user-role").textContent = formatujRole(stan.biezacyUzytkownik.role);
  document.getElementById("session-user-organization").textContent = czyGlobalnyAdministrator()
    ? "Konto globalne"
    : `Organizacja: ${stan.biezacyUzytkownik.organization_name || "brak przypisania"}`;
  navUsers.classList.toggle("hidden", stan.biezacyUzytkownik.role !== "administrator");
  navOrganizations.classList.toggle("hidden", !czyGlobalnyAdministrator());
  switcherBox.classList.toggle("hidden", !czyGlobalnyAdministrator());

  const czyTylkoPodglad = stan.biezacyUzytkownik.role === "podglad";
  document.querySelectorAll(".action-import").forEach((button) => {
    const brakWyboruOrganizacji = czyGlobalnyAdministrator() && !stan.wybranaOrganizacjaId;
    const importTestowyWylaczony = !czyImportTestowyWlaczony();
    button.disabled = importTestowyWylaczony || czyTylkoPodglad || brakWyboruOrganizacji;
    if (importTestowyWylaczony) {
      button.title = "Import testowy jest wylaczony w tym srodowisku.";
    } else if (czyTylkoPodglad) {
      button.title = "Rola podglądu nie może importować dokumentów.";
    } else if (brakWyboruOrganizacji) {
      button.title = "Wybierz konkretną organizację przed importem.";
    } else {
      button.title = "";
    }
  });

  const przyciskNowegoZadania = document.getElementById("new-task-button");
  if (przyciskNowegoZadania) {
    const brakWyboruOrganizacji = czyGlobalnyAdministrator() && !stan.wybranaOrganizacjaId;
    przyciskNowegoZadania.disabled = czyTylkoPodglad || brakWyboruOrganizacji;
    if (czyTylkoPodglad) {
      przyciskNowegoZadania.title = "Rola podgladu nie moze dodawac zadan.";
    } else if (brakWyboruOrganizacji) {
      przyciskNowegoZadania.title = "Wybierz konkretna organizacje przed dodaniem zadania.";
    } else {
      przyciskNowegoZadania.title = "";
    }
  }

  if (!czyAdministrator() && ["users", "organizations"].includes(stan.aktywnyWidok)) {
    ustawWidok("dashboard");
  }
}

function przygotujWidokPoWylogowaniu() {
  stan.biezacyUzytkownik = null;
  stan.zadania = [];
  stan.uzytkownicyDoZadan = [];
  stan.wybraneZadanieId = null;
  stan.uzytkownicy = [];
  stan.wybranyUzytkownikId = null;
  document.getElementById("password-input").value = "";
  document.getElementById("global-search-results").classList.add("hidden");
  document.getElementById("global-search-results").innerHTML = "";
  document.getElementById("global-search").value = "";
  document.getElementById("task-table-body").innerHTML = `<tr><td colspan="10">Zaloguj sie, aby zobaczyc zadania.</td></tr>`;
  wyczyscSzczegolyZadania();
  stan.organizacje = [];
  stan.wybranaOrganizacjaId = "";
  stan.czyZakresOrganizacjiZainicjalizowany = false;
  wyczyscFormularzUzytkownika();
  wyczyscFormularzOrganizacji();
  document.getElementById("users-table-body").innerHTML = `<tr><td colspan="9">Zaloguj się jako administrator, aby zarządzać kontami.</td></tr>`;
  document.getElementById("organization-table-body").innerHTML = `<tr><td colspan="7">Zaloguj się jako administratorem globalnym, aby zarządzać organizacjami.</td></tr>`;
  pokazEkranLogowania();
  odswiezPasekSesji();
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

function zbudujAdresZOrganizacja(adres) {
  if (!stan.biezacyUzytkownik || !czyGlobalnyAdministrator() || !stan.wybranaOrganizacjaId) {
    return adres;
  }
  const separator = adres.includes("?") ? "&" : "?";
  return `${adres}${separator}organization_id=${encodeURIComponent(stan.wybranaOrganizacjaId)}`;
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
  przycisk.textContent = czyRozwiniete ? "Zwiń filtry" : "Rozwiń filtry";
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
    source: "Źródło",
    status: "Status",
    duplicate_type: "Typ duplikatu",
    date_from: "Data od",
    date_to: "Data do",
    nip: "NIP",
    invoice_number: "Numer faktury",
    ksef_number: "Numer KSeF",
    contractor_id: "Kontrahent",
  };

  const wpisy = [];
  for (const [key, value] of dane.entries()) {
    const wartosc = String(value).trim();
    if (!wartosc || !etykiety[key]) {
      continue;
    }
    let tekst = wartosc;
    if (key === "source") tekst = etykietyZrodel[wartosc] || wartosc;
    if (key === "contractor_id") {
      const kontrahent = stan.kontrahenciWszyscy.find((item) => Number(item.contractor_id) === Number(wartosc));
      tekst = kontrahent ? kontrahent.name : wartosc;
    }
    wpisy.push(`<span class="filter-chip">${bezpiecznyTekst(etykiety[key])}: ${bezpiecznyTekst(tekst)}</span>`);
  }

  if (!wpisy.length) {
    kontener.innerHTML = "";
    kontener.classList.add("hidden");
    return;
  }

  kontener.classList.remove("hidden");
  kontener.innerHTML = `${wpisy.join("")}<button type="button" class="secondary" id="clear-active-invoice-filters">Wyczyść wszystkie filtry</button>`;
  document.getElementById("clear-active-invoice-filters").addEventListener("click", () => wyczyscFiltryFaktur(true));
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
  kontener.innerHTML = `${wpisy.join("")}<button type="button" class="secondary" id="clear-contractor-filters">Wyczyść filtry</button>`;
  document.getElementById("clear-contractor-filters").addEventListener("click", async () => {
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

function odswiezPasekFiltrowZadan() {
  const kontener = document.getElementById("task-active-filters");
  const formularz = document.getElementById("task-filters");
  const dane = new FormData(formularz);
    const etykiety = {
      search: "Fraza",
      task_type: "Typ",
      status: "Status",
      priority: "Priorytet",
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
  document.getElementById("clear-active-task-filters").addEventListener("click", () => wyczyscFiltryZadan(true));
}

function wyczyscFiltryZadan(przeladuj = true) {
  document.getElementById("task-filters").reset();
  odswiezPasekFiltrowZadan();
  if (przeladuj) {
    wczytajZadania().catch((error) => pokazPowiadomienie(error.message));
  }
}

function renderujZadania(zadania) {
  stan.zadania = zadania;
  document.getElementById("task-count").textContent = `${zadania.length} rekordow`;
  odswiezPasekFiltrowZadan();
  if (!zadania.some((task) => Number(task.task_id) === Number(stan.wybraneZadanieId))) {
    wyczyscSzczegolyZadania();
  }

  const body = document.getElementById("task-table-body");
  if (!zadania.length) {
    body.innerHTML = `<tr><td colspan="10">Brak zadan dla wybranych filtrow.</td></tr>`;
    return;
  }

  body.innerHTML = zadania
    .map(
      (task) => `
        <tr class="clickable" data-task-id="${task.task_id}">
          <td>${task.task_id}</td>
          <td>${formatujNazweOrganizacji(task.organization_name)}</td>
          <td>${formatujTypZadania(task.task_type)}</td>
            <td>${formatujWartosc(task.title)}</td>
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
  if (!items.length) {
    return `<div class="empty-state">Brak notatek dla tego zadania.</div>`;
  }

  return `
    <div class="list">
      ${items
        .map(
          (item) => `
            <article class="list-item">
              <strong>${formatujWartosc(item.created_by_user_name)}</strong>
              <div class="muted">${formatujDateCzas(item.created_at)}</div>
              <div>${formatujWartosc(item.note_text)}</div>
            </article>
          `
        )
        .join("")}
    </div>
  `;
}

function renderujPanelZadania(detail = null) {
  const task = detail?.task || null;
  const zablokowane = !czyMoznaZapisywac();
  const atrybutPola = zablokowane ? 'disabled aria-disabled="true"' : "";
  const atrybutPrzycisku = zablokowane ? 'disabled title="Ta rola ma tylko podglad danych."' : "";
  const taskId = task?.task_id || "";
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

  document.getElementById("task-detail-empty").classList.add("hidden");
  const container = document.getElementById("task-detail");
  container.classList.remove("hidden");

  container.innerHTML = `
    <div class="detail-grid">
        <div class="summary-grid">
          <div class="summary-item"><strong>ID zadania</strong>${taskId || "Nowe zadanie"}</div>
          <div class="summary-item"><strong>Organizacja</strong>${formatujNazweOrganizacji(task?.organization_name || pobierzAktywnaOrganizacje()?.name || stan.biezacyUzytkownik?.organization_name)}</div>
          <div class="summary-item"><strong>Typ</strong>${task ? formatujTypZadania(task.task_type) : "-"}</div>
          <div class="summary-item"><strong>Status</strong>${task ? `<span class="status-badge ${klasaStatusuZadania(task.status, task.priority)}">${formatujStatusZadania(task.status)}</span>` : "-"}</div>
          <div class="summary-item"><strong>Priorytet</strong>${task ? formatujPriorytetZadania(task.priority) : "-"}</div>
          <div class="summary-item"><strong>Termin</strong>${formatujDateCzas(task?.due_at)}</div>
          <div class="summary-item"><strong>Przypomnienie</strong>${task?.remind_at ? `${formatujDateCzas(task.remind_at)}<div class="muted"><span class="status-badge ${pobierzStanPrzypomnienia(task).klasa}">${pobierzStanPrzypomnienia(task).etykieta}</span></div>` : "-"}</div>
          <div class="summary-item"><strong>Przypisano</strong>${formatujWartosc(task?.assigned_user_name)}</div>
          <div class="summary-item"><strong>Dodane przez</strong>${formatujWartosc(task?.created_by_user_name)}</div>
        </div>

      <div class="detail-actions">
        <button id="save-task-button" ${atrybutPrzycisku}>Zapisz zadanie</button>
        <button class="secondary" id="reset-task-button">Nowe zadanie</button>
      </div>

      <div class="panel">
        <div class="panel-header"><h3>Formularz zadania</h3></div>
        <form id="task-form" class="field-grid">
          <input type="hidden" id="task-id" value="${bezpiecznyTekst(taskId)}" />
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
          <div class="field">
            <label>Przypisano</label>
            <select id="task-assigned-user" name="assigned_user_id" ${atrybutPola}>${opcjeUzytkownikow}</select>
          </div>
            <div class="field">
              <label>Termin</label>
              <input id="task-due-at" name="due_at" type="datetime-local" value="${bezpiecznyTekst(formatujDateCzasDoInput(task?.due_at))}" ${atrybutPola} />
            </div>
            <div class="field">
              <label>Przypomnij o</label>
              <input id="task-remind-at" name="remind_at" type="datetime-local" value="${bezpiecznyTekst(formatujDateCzasDoInput(task?.remind_at))}" ${atrybutPola} />
            </div>
            <div class="field" style="grid-column: 1 / -1;">
            <label>Opis</label>
            <textarea id="task-description" name="description" ${atrybutPola}>${bezpiecznyTekst(task?.description || "")}</textarea>
          </div>
        </form>
      </div>

      <div class="detail-columns">
        <div class="panel">
          <div class="panel-header"><h3>Notatki</h3></div>
          ${renderujNotatkiZadan(detail?.notes || [])}
          ${
            task
              ? `
                <div class="panel-header" style="margin-top: 16px;"><h3>Dodaj notatke</h3></div>
                <form id="task-note-form" class="stack">
                  <textarea id="task-note-text" placeholder="Zapisz ustalenie, komentarz albo wynik rozmowy." ${atrybutPola}></textarea>
                  <button type="submit" ${atrybutPrzycisku}>Dodaj notatke</button>
                </form>
              `
              : `<div class="empty-state">Notatki mozna dodawac po zapisaniu zadania.</div>`
          }
        </div>
        <div class="panel">
          <div class="panel-header"><h3>Historia zadania</h3></div>
          ${renderujHistorieZadan(detail?.history || [])}
        </div>
      </div>
    </div>
  `;

  document.getElementById("save-task-button").addEventListener("click", zapiszZadanie);
  document.getElementById("reset-task-button").addEventListener("click", przygotujNoweZadanie);
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
}

function przygotujNoweZadanie() {
  if (czyGlobalnyAdministrator() && !stan.wybranaOrganizacjaId) {
    pokazPowiadomienie("Wybierz organizacje przed dodaniem zadania.");
    return;
  }
  renderujPanelZadania(null);
}

function wyczyscSzczegolyZadania() {
  stan.wybraneZadanieId = null;
  document.getElementById("task-detail").classList.add("hidden");
  document.getElementById("task-detail").innerHTML = "";
  document.getElementById("task-detail-empty").classList.remove("hidden");
}

function renderujPulpit(snapshot) {
  const karty = [
    ["nowe_faktury", snapshot.cards.nowe_faktury],
    ["do_weryfikacji", snapshot.cards.do_weryfikacji],
    ["podejrzenia_duplikatow", snapshot.cards.podejrzenia_duplikatow],
    ["pewne_duplikaty", snapshot.cards.pewne_duplikaty],
    ["nowi_kontrahenci", snapshot.cards.nowi_kontrahenci],
    ["aktywne_przypomnienia", snapshot.cards.aktywne_przypomnienia],
  ];

  document.getElementById("dashboard-cards").innerHTML = karty
    .map(
      ([klucz, wartosc]) => `
        <button class="card card-button" type="button" data-shortcut="${klucz}">
          <div class="card-label">${bezpiecznyTekst(skrotyPulpitu[klucz].etykieta)}</div>
          <div class="card-value">${bezpiecznyTekst(wartosc)}</div>
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

  const kontenerPrzypomnien = document.getElementById("dashboard-reminders");
  if (!snapshot.active_reminders?.length) {
    kontenerPrzypomnien.innerHTML = `<div class="empty-state">Brak aktywnych przypomnien.</div>`;
  } else {
    kontenerPrzypomnien.innerHTML = `
      <div class="list">
        ${snapshot.active_reminders
          .map(
            (task) => `
              <article class="list-item">
                <strong>${formatujWartosc(task.title)}</strong>
                <div class="muted">${formatujTypZadania(task.task_type)} | Organizacja: ${formatujNazweOrganizacji(task.organization_name)}</div>
                <div>Przypomnienie: ${formatujDateCzas(task.remind_at)}</div>
                <div>Status: <span class="status-badge ${pobierzStanPrzypomnienia(task).klasa}">${pobierzStanPrzypomnienia(task).etykieta}</span></div>
              </article>
            `
          )
          .join("")}
      </div>
    `;
  }

  const kontenerZdarzen = document.getElementById("dashboard-events");
  if (!snapshot.recent_events.length) {
    kontenerZdarzen.innerHTML = `<div class="empty-state">Brak zdarzeń do wyświetlenia.</div>`;
    return;
  }

  kontenerZdarzen.innerHTML = `
    <div class="list">
      ${snapshot.recent_events
        .map(
          (event) => {
            const opisKontekstu = zbudujOpisKontekstuZdarzenia(event);
            return `
            <article class="list-item">
              <strong>${formatujTypZdarzenia(event.event_type)}</strong>
              <div class="muted">${formatujDateCzas(event.event_time)}</div>
              <div>Organizacja: ${formatujNazweOrganizacji(event.organization_name)}</div>
              ${opisKontekstu ? `<div>${opisKontekstu}</div>` : ""}
              <div>${formatujWartosc(event.decision_reason)}</div>
            </article>
          `;
          }
        )
        .join("")}
    </div>
  `;
}

function renderujFaktury(faktury) {
  stan.faktury = faktury;
  document.getElementById("invoice-count").textContent = `${faktury.length} rekordów`;
  odswiezPasekFiltrowFaktur();
  if (!faktury.some((invoice) => Number(invoice.id) === Number(stan.wybranaFakturaId))) {
    wyczyscSzczegolyFaktury();
  }

  const body = document.getElementById("invoice-table-body");
  if (!faktury.length) {
    body.innerHTML = `<tr><td colspan="13">Brak faktur dla wybranych filtrów.</td></tr>`;
    return;
  }

  body.innerHTML = faktury
    .map(
      (invoice) => `
        <tr class="clickable" data-invoice-id="${invoice.id}">
          <td>${invoice.id}</td>
          <td>${formatujNazweOrganizacji(invoice.organization_name)}</td>
          <td>${formatujWartosc(invoice.incoming_date)}</td>
          <td>${formatujZrodlo(invoice.source)}</td>
          <td>${formatujWartosc(invoice.file_name)}</td>
          <td>${formatujWartosc(invoice.invoice_number)}</td>
          <td>${formatujWartosc(invoice.ksef_number)}</td>
          <td>${formatujWartosc(invoice.issuer_nip)}</td>
          <td>${formatujWartosc(invoice.issuer_name)}</td>
          <td>${formatujKwote(invoice.gross_amount, invoice.currency)}</td>
          <td><span class="status-badge ${klasaStatusu(invoice.status, invoice.duplicate_type)}">${formatujWartosc(invoice.status)}</span></td>
          <td><span class="status-badge ${klasaStatusu(invoice.status, invoice.duplicate_type)}">${formatujWartosc(invoice.duplicate_type)}</span></td>
          <td>${formatujWartosc(invoice.contractor_name)}</td>
        </tr>
      `
    )
    .join("");

  body.querySelectorAll("[data-invoice-id]").forEach((row) => {
    row.addEventListener("click", () => wczytajSzczegolyFaktury(Number(row.dataset.invoiceId)));
  });
}

function renderujRelacje(relations) {
  if (!relations.length) {
    return `<div class="empty-state">Brak aktywnych relacji duplikatów.</div>`;
  }

  return `
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Powiązana faktura</th>
            <th>Typ relacji</th>
            <th>Powód</th>
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
    return `<div class="empty-state">Brak podobnych faktur według aktualnych reguł.</div>`;
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
            <th>Powód</th>
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
    return `<div class="empty-state">Brak historii działań dla tej faktury.</div>`;
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
            <th>Powód</th>
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
    return `<div class="empty-state">Brak dodatkowych metadanych źródła.</div>`;
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

function renderujSzczegolyFaktury(detail) {
  const invoice = detail.invoice;
  stan.wybranaFakturaId = invoice.id;
  const zablokowane = !czyMoznaZapisywac();
  const atrybutPola = zablokowane ? 'disabled aria-disabled="true"' : "";
  const atrybutPrzycisku = zablokowane ? 'disabled title="Ta rola ma tylko podgląd danych."' : "";
  const sourceTrace = detail.source_trace || {};
  const documentTrace = detail.document_trace || {};

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

  container.innerHTML = `
    <div class="detail-grid">
      <div class="summary-grid">
        <div class="summary-item"><strong>ID faktury</strong>${invoice.id}</div>
        <div class="summary-item"><strong>Organizacja</strong>${formatujNazweOrganizacji(invoice.organization_name)}</div>
        <div class="summary-item"><strong>Źródło</strong>${formatujZrodlo(invoice.source)}</div>
        <div class="summary-item"><strong>Status</strong><span class="status-badge ${klasaStatusu(invoice.status, invoice.duplicate_type)}">${formatujWartosc(invoice.status)}</span></div>
        <div class="summary-item"><strong>Typ duplikatu</strong><span class="status-badge ${klasaStatusu(invoice.status, invoice.duplicate_type)}">${formatujWartosc(invoice.duplicate_type)}</span></div>
        <div class="summary-item"><strong>Opis weryfikacji</strong>${formatujWartosc(invoice.flag_reason)}</div>
        <div class="summary-item"><strong>Identyfikator techniczny</strong>${formatujWartosc(invoice.invoice_hash)}</div>
      </div>

      <div class="detail-actions">
        <button id="save-invoice" ${atrybutPrzycisku}>Zapisz zmiany</button>
        <button class="secondary" id="confirm-duplicate" ${atrybutPrzycisku}>Potwierdź duplikat</button>
        <button class="secondary" id="reject-duplicate" ${atrybutPrzycisku}>Oznacz jako poprawną</button>
        <a href="${invoice.file_link || "#"}" target="_blank" rel="noreferrer">Otwórz dokument</a>
        <a href="${invoice.ocr_link || "#"}" target="_blank" rel="noreferrer">Otwórz OCR</a>
      </div>

      <div class="panel">
        <div class="panel-header"><h3>Edycja faktury</h3></div>
        <form id="invoice-edit-form" class="field-grid">
          <div class="field">
            <label>Nazwa pliku</label>
            <input name="file_name" value="${bezpiecznyTekst(invoice.file_name || "")}" ${atrybutPola} />
          </div>
          <div class="field">
            <label>Data wpływu</label>
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
            <label>Data sprzedaży</label>
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
          <div class="field" style="grid-column: 1 / -1;">
            <label>Notatki</label>
            <textarea name="notes" ${atrybutPola}>${bezpiecznyTekst(invoice.notes || "")}</textarea>
          </div>
        </form>
      </div>

      <div class="detail-columns">
        <div class="panel">
          <div class="panel-header"><h3>Ślad źródła i dokumentu</h3></div>
          <div class="list">
            <div class="list-item"><strong>Organizacja</strong><div>${formatujNazweOrganizacji(sourceTrace.organization_name)}</div></div>
            <div class="list-item"><strong>Źródło</strong><div>${formatujZrodlo(sourceTrace.source)}</div></div>
            <div class="list-item"><strong>Typ dokumentu</strong><div>${formatujWartosc(sourceTrace.document_type)}</div></div>
            <div class="list-item"><strong>Identyfikator źródła</strong><div>${formatujWartosc(sourceTrace.source_external_id)}</div></div>
            <div class="list-item"><strong>Nadawca źródła</strong><div>${formatujWartosc(sourceTrace.source_sender_name)}</div></div>
            <div class="list-item"><strong>Id nadawcy</strong><div>${formatujWartosc(sourceTrace.source_sender_id)}</div></div>
            <div class="list-item"><strong>Powiązany użytkownik systemu</strong><div>${formatujWartosc(sourceTrace.linked_user?.display_name || sourceTrace.linked_user?.login)}</div></div>
            <div class="list-item"><strong>Nazwa pliku</strong><div>${formatujWartosc(documentTrace.file_name)}</div></div>
            <div class="list-item"><strong>Identyfikator techniczny</strong><div>${formatujWartosc(documentTrace.invoice_hash)}</div></div>
            <div class="list-item"><strong>Pewność OCR</strong><div>${formatujWartosc(documentTrace.ocr_confidence)}</div></div>
          </div>
          <div class="panel-header" style="margin-top: 16px;"><h3>Tekst OCR</h3></div>
          <div class="code-block">${bezpiecznyTekst(invoice.ocr_raw_text || "Brak tekstu OCR dla tej faktury.")}</div>
          <div class="filters-actions">
            <a href="${documentTrace.file_link || "#"}" target="_blank" rel="noreferrer">Otwórz zapisany dokument</a>
            <a href="${documentTrace.ocr_link || "#"}" target="_blank" rel="noreferrer">Otwórz zapis OCR</a>
          </div>
          <div class="panel-header" style="margin-top: 16px;"><h3>Metadane źródła</h3></div>
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
                  <div class="list-item"><strong>Był znany wcześniej</strong><div>${detail.contractor_known_before ? "tak" : "nie"}</div></div>
                  <div class="list-item"><strong>Liczba faktur</strong><div>${formatujWartosc(detail.contractor.invoice_count)}</div></div>
                  <div class="list-item"><strong>Notatki</strong><div>${formatujWartosc(detail.contractor.notes)}</div></div>
                </div>
              `
              : `<div class="empty-state">Brak powiązanego kontrahenta.</div>`
          }
        </div>
      </div>

      <div class="panel">
        <div class="panel-header"><h3>Aktywne relacje duplikatów</h3></div>
        ${renderujRelacje(detail.relations)}
      </div>

      <div class="panel">
        <div class="panel-header"><h3>Podobne lub powiązane faktury</h3></div>
        ${renderujPodobneFaktury(detail.similar_invoices)}
      </div>

      <div class="panel">
        <div class="panel-header"><h3>Historia działań</h3></div>
        ${renderujHistorie(detail.history)}
      </div>
    </div>
  `;

  document.getElementById("save-invoice").addEventListener("click", zapiszZmianyFaktury);
  document.getElementById("confirm-duplicate").addEventListener("click", potwierdzDuplikat);
  document.getElementById("reject-duplicate").addEventListener("click", odrzucPodejrzenieDuplikatu);
}

function wyczyscSzczegolyFaktury() {
  stan.wybranaFakturaId = null;
  document.getElementById("invoice-detail").classList.add("hidden");
  document.getElementById("invoice-detail").innerHTML = "";
  document.getElementById("invoice-detail-empty").classList.remove("hidden");
}

function zsynchronizujFiltrKontrahenta() {
  const select = document.getElementById("filter-contractor");
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

function renderujKontrahentow(kontrahenci) {
  stan.kontrahenciWidoczni = kontrahenci;
  odswiezPasekFiltrowKontrahentow();
  if (!kontrahenci.some((contractor) => Number(contractor.contractor_id) === Number(stan.wybranyKontrahentId))) {
    wyczyscSzczegolyKontrahenta();
  }

  const body = document.getElementById("contractor-table-body");
  if (!kontrahenci.length) {
    body.innerHTML = `<tr><td colspan="9">Brak kontrahentów.</td></tr>`;
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
        <div class="panel-header"><h3>Powiązane faktury</h3></div>
        ${renderujPodobneFaktury(detail.invoices)}
      </div>
    </div>
  `;
}

function wyczyscSzczegolyKontrahenta() {
  stan.wybranyKontrahentId = null;
  document.getElementById("contractor-detail").classList.add("hidden");
  document.getElementById("contractor-detail").innerHTML = "";
  document.getElementById("contractor-detail-empty").classList.remove("hidden");
}

function renderujUzytkownikow(uzytkownicy) {
  stan.uzytkownicy = uzytkownicy;
  const body = document.getElementById("users-table-body");
  if (!uzytkownicy.length) {
    body.innerHTML = `<tr><td colspan="9">Brak kont użytkowników.</td></tr>`;
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
          <td>${formatujRole(uzytkownik.role)}</td>
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
  document.getElementById("user-role").value = uzytkownik.role || "operator";
  document.getElementById("user-active").value = uzytkownik.is_active ? "1" : "0";
  document.getElementById("user-password").value = "";
  document.getElementById("user-password").placeholder = "Podaj nowe hasło tylko jeśli chcesz je zmienić";
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
  document.getElementById("user-role").value = "operator";
  document.getElementById("user-active").value = "1";
  document.getElementById("user-password").placeholder = "Podaj hasło dla nowego konta lub nowe hasło przy zmianie";
}

function renderujOrganizacje(organizacje) {
  stan.organizacje = organizacje;
  zbudujOpcjeOrganizacjiDlaFormularzy();
  const body = document.getElementById("organization-table-body");
  if (!organizacje.length) {
    body.innerHTML = `<tr><td colspan="9">Brak organizacji.</td></tr>`;
    return;
  }

  body.innerHTML = organizacje
    .map(
      (organizacja) => `
          <tr class="clickable" data-organization-id="${organizacja.organization_id}">
            <td>${organizacja.organization_id}</td>
            <td>${formatujWartosc(organizacja.name)}</td>
            <td>${formatujWartosc(organizacja.slug)}</td>
            <td>${formatujWartosc(organizacja.telegram_chat_id)}</td>
            <td>${formatujWartosc(organizacja.telegram_chat_name)}</td>
            <td>${organizacja.is_active ? '<span class="status-badge status-success">tak</span>' : '<span class="status-badge status-danger">nie</span>'}</td>
            <td>${formatujWartosc(organizacja.user_count)}</td>
            <td>${formatujWartosc(organizacja.invoice_count)}</td>
          <td>${formatujWartosc(organizacja.contractor_count)}</td>
        </tr>
      `
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
}

function wypelnijFormularzOrganizacji(organizacja) {
  stan.wybranaOrganizacjaFormularzaId = Number(organizacja.organization_id);
  document.getElementById("organization-form-title").textContent = `Edycja organizacji: ${organizacja.name}`;
  document.getElementById("organization-id").value = String(organizacja.organization_id);
  document.getElementById("organization-name").value = organizacja.name || "";
  document.getElementById("organization-slug").value = organizacja.slug || "";
  document.getElementById("organization-telegram-chat-id").value = organizacja.telegram_chat_id || "";
  document.getElementById("organization-telegram-chat-name").value = organizacja.telegram_chat_name || "";
  document.getElementById("organization-active").value = organizacja.is_active ? "1" : "0";
}

function wyczyscFormularzOrganizacji() {
  stan.wybranaOrganizacjaFormularzaId = null;
  document.getElementById("organization-form-title").textContent = "Nowa organizacja";
  document.getElementById("organization-form").reset();
  document.getElementById("organization-id").value = "";
  document.getElementById("organization-telegram-chat-id").value = "";
  document.getElementById("organization-telegram-chat-name").value = "";
  document.getElementById("organization-active").value = "1";
}

function renderujLogi(logs) {
  stan.logi = logs;
  const body = document.getElementById("log-table-body");
  if (!logs.length) {
    body.innerHTML = `<tr><td colspan="9">Brak logów.</td></tr>`;
    return;
  }

  body.innerHTML = logs
    .map(
      (log) => {
        const opisKontekstu = zbudujOpisKontekstuZdarzenia(log);
        return `
        <tr>
          <td>${formatujDateCzas(log.event_time)}</td>
          <td>${formatujNazweOrganizacji(log.organization_name)}</td>
          <td>${formatujTypZdarzenia(log.event_type)}</td>
          <td>${opisKontekstu || "Zdarzenie ogólne"}</td>
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
                        <button class="ghost quick-open-invoice" data-id="${invoice.id}">Otwórz fakturę</button>
                      </article>
                    `
                  )
                  .join("")
              : `<div class="empty-state">Brak wyników.</div>`
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
                        <button class="ghost quick-open-contractor" data-id="${contractor.contractor_id}">Otwórz kontrahenta</button>
                      </article>
                    `
                  )
                  .join("")
              : `<div class="empty-state">Brak wyników.</div>`
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

async function wczytajMeta() {
  stan.meta = await api("/api/meta", {}, { pominWylogowanie: true });
  ustawWidocznoscElementowSrodowiska();
  zbudujOpcje(document.querySelector('select[name="source"]'), stan.meta.sources, "Wszystkie źródła", formatujZrodlo);
  zbudujOpcje(document.querySelector('select[name="status"]'), stan.meta.statuses, "Wszystkie statusy");
  zbudujOpcje(document.querySelector('select[name="duplicate_type"]'), stan.meta.duplicate_types, "Wszystkie typy duplikatu");
  zbudujOpcje(document.getElementById("task-filter-type"), stan.meta.task_types, "Wszystkie typy", formatujTypZadania);
  zbudujOpcje(document.getElementById("task-filter-status"), stan.meta.task_statuses, "Wszystkie statusy", formatujStatusZadania);
  zbudujOpcje(document.getElementById("task-filter-priority"), stan.meta.task_priorities, "Wszystkie priorytety", formatujPriorytetZadania);

  const sortBy = document.getElementById("sort-by");
  sortBy.innerHTML = `
    <option value="incoming_date">Sortuj po dacie wpływu</option>
    <option value="id">Sortuj po identyfikatorze</option>
    <option value="invoice_number">Sortuj po numerze faktury</option>
    <option value="ksef_number">Sortuj po numerze KSeF</option>
    <option value="issuer_name">Sortuj po wystawcy</option>
    <option value="gross_amount">Sortuj po kwocie</option>
    <option value="status">Sortuj po statusie</option>
    <option value="updated_at">Sortuj po ostatniej zmianie</option>
  `;

  const roleSelect = document.getElementById("user-role");
  roleSelect.innerHTML = stan.meta.roles
    .map((rola) => `<option value="${rola}">${formatujRole(rola)}</option>`)
    .join("");

  ustawInformacjeSystemowe();
  zbudujOpcjeUzytkownikowDoZadan();
  wyczyscFormularzUzytkownika();
  wyczyscFormularzOrganizacji();
}

async function wczytajOrganizacje() {
  if (!czyAdministrator()) {
    stan.organizacje = [];
    zbudujOpcjeOrganizacjiDlaFormularzy();
    return;
  }

  const organizacje = await api("/api/organizations");
  renderujOrganizacje(organizacje);

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

async function wczytajPulpit() {
  const snapshot = await api(zbudujAdresZOrganizacja("/api/dashboard"));
  renderujPulpit(snapshot);
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

async function wczytajFaktury() {
  const query = zbudujZapytanieFaktur();
  const faktury = await api(zbudujAdresZOrganizacja(`/api/invoices${query ? `?${query}` : ""}`));
  renderujFaktury(faktury);
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
  if (!stan.biezacyUzytkownik) {
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
  const query = zbudujZapytanieZadan();
  const zadania = await api(zbudujAdresZOrganizacja(`/api/tasks${query ? `?${query}` : ""}`));
  renderujZadania(zadania);
}

async function wczytajSzczegolyZadania(taskId) {
  const detail = await api(zbudujAdresZOrganizacja(`/api/tasks/${taskId}`));
  renderujPanelZadania(detail);
}

async function wczytajUzytkownikow() {
  if (!czyAdministrator()) {
    stan.uzytkownicy = [];
    document.getElementById("users-table-body").innerHTML = `<tr><td colspan="9">Panel użytkowników jest dostępny tylko dla administratora.</td></tr>`;
    return;
  }
  const uzytkownicy = await api(zbudujAdresZOrganizacja("/api/users"));
  renderujUzytkownikow(uzytkownicy);
}

async function wczytajPanelOrganizacji() {
  if (!czyGlobalnyAdministrator()) {
    document.getElementById("organization-table-body").innerHTML =
      `<tr><td colspan="7">Panel organizacji jest dostępny tylko dla administratora globalnego.</td></tr>`;
    return;
  }
  await wczytajOrganizacje();
}

async function odswiezDanePoZalogowaniu() {
  await wczytajOrganizacje();
  await Promise.all([
    wczytajPulpit(),
    wczytajWszystkichKontrahentow(),
    wczytajKontrahentow(),
    wczytajFaktury(),
    wczytajZadania(),
    wczytajLogi(),
    wczytajUzytkownikowDoZadan(),
  ]);
  if (czyAdministrator()) {
    await wczytajUzytkownikow();
  } else {
    wyczyscFormularzUzytkownika();
    document.getElementById("users-table-body").innerHTML = `<tr><td colspan="9">Panel użytkowników jest dostępny tylko dla administratora.</td></tr>`;
  }
  if (czyGlobalnyAdministrator()) {
    await wczytajPanelOrganizacji();
  } else {
    document.getElementById("organization-table-body").innerHTML =
      `<tr><td colspan="7">Panel organizacji jest dostępny tylko dla administratora globalnego.</td></tr>`;
  }
  odswiezPasekSesji();
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
    assigned_user_id: document.getElementById("task-assigned-user").value,
    due_at: document.getElementById("task-due-at").value,
    remind_at: document.getElementById("task-remind-at").value,
    description: document.getElementById("task-description").value.trim(),
  };

  let wynik;
  if (!taskId) {
    wynik = await api(zbudujAdresZOrganizacja("/api/tasks"), {
      method: "POST",
      body: JSON.stringify(payload),
    });
    pokazPowiadomienie("Dodano nowe zadanie.");
  } else {
    wynik = await api(zbudujAdresZOrganizacja(`/api/tasks/${taskId}`), {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
    pokazPowiadomienie("Zapisano zmiany zadania.");
  }

  await Promise.all([wczytajZadania(), wczytajLogi()]);
  await wczytajSzczegolyZadania(wynik.task_id);
}

async function dodajNotatkeDoZadania() {
  if (!stan.wybraneZadanieId || !czyMoznaZapisywac()) {
    return;
  }
  const pole = document.getElementById("task-note-text");
  const noteText = pole.value.trim();
  const detail = await api(zbudujAdresZOrganizacja(`/api/tasks/${stan.wybraneZadanieId}/notes`), {
    method: "POST",
    body: JSON.stringify({ note_text: noteText }),
  });
  pole.value = "";
  pokazPowiadomienie("Dodano notatke do zadania.");
  await Promise.all([wczytajZadania(), wczytajLogi()]);
  renderujPanelZadania(detail);
}

async function zapiszZmianyFaktury() {
  if (!stan.wybranaFakturaId || !czyMoznaZapisywac()) return;
  const form = document.getElementById("invoice-edit-form");
  const dane = new FormData(form);
  const payload = {};
  for (const [key, value] of dane.entries()) {
    payload[key] = value;
  }

  await api(zbudujAdresZOrganizacja(`/api/invoices/${stan.wybranaFakturaId}`), {
    method: "PATCH",
    body: JSON.stringify(payload),
  });

  pokazPowiadomienie("Zapisano zmiany faktury.");
  await Promise.all([wczytajFaktury(), wczytajPulpit(), wczytajLogi(), wczytajKontrahentow(), wczytajWszystkichKontrahentow()]);
  await wczytajSzczegolyFaktury(stan.wybranaFakturaId);
}

async function potwierdzDuplikat() {
  if (!stan.wybranaFakturaId || !czyMoznaZapisywac()) return;
  await api(zbudujAdresZOrganizacja(`/api/invoices/${stan.wybranaFakturaId}/actions/confirm-duplicate`), { method: "POST" });
  pokazPowiadomienie("Potwierdzono duplikat.");
  await Promise.all([wczytajFaktury(), wczytajPulpit(), wczytajLogi()]);
  await wczytajSzczegolyFaktury(stan.wybranaFakturaId);
}

async function odrzucPodejrzenieDuplikatu() {
  if (!stan.wybranaFakturaId || !czyMoznaZapisywac()) return;
  await api(zbudujAdresZOrganizacja(`/api/invoices/${stan.wybranaFakturaId}/actions/reject-duplicate`), { method: "POST" });
  pokazPowiadomienie("Faktura została oznaczona jako poprawna.");
  await Promise.all([wczytajFaktury(), wczytajPulpit(), wczytajLogi()]);
  await wczytajSzczegolyFaktury(stan.wybranaFakturaId);
}

async function wykonajImportTestowy(source) {
  if (!czyImportTestowyWlaczony()) {
    pokazPowiadomienie("Import testowy jest wylaczony w tym srodowisku.");
    return;
  }
  if (!czyMoznaZapisywac()) {
    pokazPowiadomienie("Ta rola nie może dodawać dokumentów.");
    return;
  }
  if (czyGlobalnyAdministrator() && !stan.wybranaOrganizacjaId) {
    pokazPowiadomienie("Wybierz organizację przed importem testowym.");
    return;
  }
  await api(zbudujAdresZOrganizacja(`/api/import/${source}`), { method: "POST" });
  pokazPowiadomienie(`Dodano przykładową fakturę ze źródła ${formatujZrodlo(source)}.`);
  await Promise.all([wczytajPulpit(), wczytajFaktury(), wczytajKontrahentow(), wczytajWszystkichKontrahentow(), wczytajLogi()]);
}

async function zapiszUzytkownika() {
  if (!czyAdministrator()) return;

  const userId = document.getElementById("user-id").value.trim();
  const payload = {
    display_name: document.getElementById("user-display-name").value.trim(),
    organization_id: document.getElementById("user-organization-id").value,
    telegram_user_id: document.getElementById("user-telegram-user-id").value.trim(),
    role: document.getElementById("user-role").value,
    is_active: document.getElementById("user-active").value,
  };
  const login = document.getElementById("user-login").value.trim();
  const haslo = document.getElementById("user-password").value.trim();

  if (!userId) {
    payload.login = login;
    payload.password = haslo;
    await api("/api/users", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    pokazPowiadomienie(`Utworzono konto ${login}.`);
  } else {
    if (haslo) {
      payload.password = haslo;
    }
    await api(`/api/users/${userId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
    pokazPowiadomienie("Zapisano zmiany konta.");
  }

  wyczyscFormularzUzytkownika();
  await Promise.all([wczytajUzytkownikow(), wczytajLogi()]);
}

async function zapiszOrganizacje() {
  if (!czyGlobalnyAdministrator()) return;

  const organizationId = document.getElementById("organization-id").value.trim();
  const payload = {
    name: document.getElementById("organization-name").value.trim(),
    slug: document.getElementById("organization-slug").value.trim(),
    telegram_chat_id: document.getElementById("organization-telegram-chat-id").value.trim(),
    telegram_chat_name: document.getElementById("organization-telegram-chat-name").value.trim(),
    is_active: document.getElementById("organization-active").value,
  };

  if (!organizationId) {
    await api("/api/organizations", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    pokazPowiadomienie(`Utworzono organizację ${payload.name}.`);
  } else {
    await api(`/api/organizations/${organizationId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
    pokazPowiadomienie("Zapisano zmiany organizacji.");
  }

  wyczyscFormularzOrganizacji();
  renderujWynikiWyszukiwania({ invoices: [], contractors: [] });
  await odswiezDanePoZalogowaniu();
}

function podepnijZdarzenia() {
  if (stan.czyZdarzeniaPodpiete) {
    return;
  }
  stan.czyZdarzeniaPodpiete = true;

  document.querySelectorAll(".nav-item").forEach((button) => {
    button.addEventListener("click", () => ustawWidok(button.dataset.view));
  });

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

  document.getElementById("reset-task-filters").addEventListener("click", () => wyczyscFiltryZadan(true));
  document.getElementById("new-task-button").addEventListener("click", () => przygotujNoweZadanie());

  document.getElementById("contractor-search").addEventListener("input", async (event) => {
    stan.filtryKontrahentow.szukaj = event.target.value.trim();
    try {
      await wczytajKontrahentow();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
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

  document.getElementById("organization-switcher").addEventListener("change", async (event) => {
    stan.wybranaOrganizacjaId = event.target.value;
    stan.czyZakresOrganizacjiZainicjalizowany = true;
    odswiezPasekSesji();
    try {
      renderujWynikiWyszukiwania({ invoices: [], contractors: [] });
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

  document.getElementById("logout-button").addEventListener("click", async () => {
    try {
      await wylogujZSystemu();
      pokazPowiadomienie("Wylogowano z systemu.");
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

  document.getElementById("reset-user-form").addEventListener("click", () => wyczyscFormularzUzytkownika());

  document.getElementById("organization-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await zapiszOrganizacje();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });

  document.getElementById("reset-organization-form").addEventListener("click", () => wyczyscFormularzOrganizacji());
}

async function start() {
  try {
    podepnijZdarzenia();
    ustawWidocznoscElementowSrodowiska();
    ustawWidocznoscFiltrowFaktur(false);
    await wczytajMeta();
    const maSesje = await sprobujPrzywrocicSesje();
    if (maSesje) {
      await odswiezDanePoZalogowaniu();
    }
  } catch (error) {
    pokazPowiadomienie(error.message);
  }
}

start();
