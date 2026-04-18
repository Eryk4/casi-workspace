Object.assign(capabilityLabels, {
  "knowledge.download": "Pobieranie plikow firmowych",
  "knowledge.assistant_use": "Korzystanie z asystenta",
});

defaultCapabilitiesByRole.system_owner = [
  "knowledge.read",
  "knowledge.download",
  "knowledge.upload",
  "knowledge.sync",
  "knowledge.manage",
  "knowledge.assistant_use",
];
defaultCapabilitiesByRole.organization_admin = [...defaultCapabilitiesByRole.system_owner];
defaultCapabilitiesByRole.coordinator = [...defaultCapabilitiesByRole.system_owner];
defaultCapabilitiesByRole.operator = [
  "knowledge.read",
  "knowledge.download",
  "knowledge.upload",
  "knowledge.sync",
  "knowledge.assistant_use",
];
defaultCapabilitiesByRole.guest = ["knowledge.read", "knowledge.download"];

function czyMoznaPobieracPlikiFirmowe() {
  return czyUzytkownikMaCapability("knowledge.download");
}

function czyMoznaKorzystacZAsystentaDokumentow() {
  return czyUzytkownikMaCapability("knowledge.assistant_use");
}

function formatujLifecycleDokumentuBazyWiedzy(status) {
  return { active: "aktywny", archived: "archiwalny", deleted: "usuniety" }[String(status || "active")] || "aktywny";
}

function klasaLifecycleDokumentuBazyWiedzy(status) {
  if (status === "deleted") return "status-danger";
  if (status === "archived") return "status-warning";
  return "status-success";
}

function formatujStanObieguDokumentuBazyWiedzy(status) {
  return {
    roboczy: "roboczy",
    do_sprawdzenia: "do sprawdzenia",
    do_akceptacji: "do akceptacji",
    obowiazujacy: "obowiazujacy",
    archiwalny: "archiwalny",
  }[String(status || "roboczy")] || "roboczy";
}

function klasaStanuObieguDokumentuBazyWiedzy(status) {
  if (status === "do_akceptacji") return "status-warning";
  if (status === "do_sprawdzenia") return "status-info";
  if (status === "archiwalny") return "status-warning";
  return "status-success";
}

function pobierzEtykieteOsobyDokumentuBazyWiedzy(label, fallbackId) {
  const normalizedLabel = String(label || "").trim();
  if (normalizedLabel) return normalizedLabel;
  return fallbackId ? `uzytkownik #${fallbackId}` : "brak";
}

function zbudujPiguIPrzypisaniaDokumentuBazyWiedzy(dokument) {
  const items = [
    dokument.owner_user_id ? `Prowadzi: ${pobierzEtykieteOsobyDokumentuBazyWiedzy(dokument.owner_user_label, dokument.owner_user_id)}` : "",
    dokument.reviewer_user_id ? `Sprawdza: ${pobierzEtykieteOsobyDokumentuBazyWiedzy(dokument.reviewer_user_label, dokument.reviewer_user_id)}` : "",
    dokument.approver_user_id ? `Akceptuje: ${pobierzEtykieteOsobyDokumentuBazyWiedzy(dokument.approver_user_label, dokument.approver_user_id)}` : "",
  ].filter(Boolean);
  if (!items.length) return "";
  return `<div class="knowledge-audit-highlights">${items.map((item) => `<span class="pill history-pill">${bezpiecznyTekst(item)}</span>`).join("")}</div>`;
}

function formatujStatusDuplikatuBazyWiedzy(status) {
  return { exact_duplicate: "duplikat 1:1", similar_version: "podobna wersja", none: "" }[String(status || "none")] || "";
}

function pobierzAdresPobraniaDokumentuBazyWiedzy(dokument) {
  return zbudujAdresZOrganizacja(`/api/knowledge/documents/${dokument.knowledge_document_id}/download`);
}

function pobierzAdresPodgladuPlikuDokumentuBazyWiedzy(dokument) {
  return zbudujAdresZOrganizacja(`/api/knowledge/documents/${dokument.knowledge_document_id}/preview-file`);
}

function znormalizujCapabilitiesWiedzy(capabilities, role) {
  const normalized = new Set((capabilities || []).filter(Boolean));
  normalized.add("knowledge.read");
  if (normalized.has("knowledge.sync")) normalized.add("knowledge.upload");
  if (normalized.has("knowledge.upload") || normalized.has("knowledge.manage")) normalized.add("knowledge.download");
  if (role === "guest") return ["knowledge.read", "knowledge.download"];
  return Array.from(normalized);
}

function pobierzSkrotCzlonkostwUzytkownika(uzytkownik) {
  const memberships = Array.isArray(uzytkownik?.memberships) ? uzytkownik.memberships : [];
  if (!memberships.length) return "Brak";
  const primary = memberships.find((item) => item.is_primary) || memberships[0];
  const label = primary.organization_name || primary.organization_slug || `#${primary.organization_id || "?"}`;
  return memberships.length === 1 ? label : `${label} +${memberships.length - 1}`;
}

function zbudujWidokCzlonkostwUzytkownika(uzytkownik) {
  const memberships = Array.isArray(uzytkownik?.memberships) ? uzytkownik.memberships : [];
  if (!memberships.length) return '<span class="pill history-pill">brak</span>';
  return memberships
    .map((membership) => {
      const label =
        membership.organization_name || membership.organization_slug || `#${membership.organization_id || "?"}`;
      return `<span class="pill history-pill">${bezpiecznyTekst(label)}${membership.is_primary ? " (glowna)" : ""}</span>`;
    })
    .join("");
}

function pobierzDokumentyBibliotekiBazyWiedzy() {
  const documents = stan.dokumentyWiedzy || [];
  return czyMoznaZarzadzacPrzetwarzaniemBazyWiedzy() ? documents : documents.filter((document) => document.is_downloadable);
}

function pobierzZaznaczoneIdDokumentowBazyWiedzy() {
  zapewnijStanRozszerzenBazyWiedzy();
  return Array.from(new Set((stan.zaznaczoneDokumentyWiedzy || []).map((value) => Number(value)).filter((value) => Number.isFinite(value) && value > 0)));
}

function czyDokumentBazyWiedzyJestZaznaczony(knowledgeDocumentId) {
  return pobierzZaznaczoneIdDokumentowBazyWiedzy().includes(Number(knowledgeDocumentId || 0));
}

function ustawZaznaczoneDokumentyBazyWiedzy(documentIds) {
  stan.zaznaczoneDokumentyWiedzy = Array.from(
    new Set((documentIds || []).map((value) => Number(value)).filter((value) => Number.isFinite(value) && value > 0))
  );
}

function zsynchronizujWyborDokumentowBazyWiedzy(documents) {
  const allowedIds = new Set((documents || []).map((item) => Number(item.knowledge_document_id || 0)).filter((value) => value > 0));
  ustawZaznaczoneDokumentyBazyWiedzy(pobierzZaznaczoneIdDokumentowBazyWiedzy().filter((documentId) => allowedIds.has(documentId)));
}

function ustawZaznaczenieDokumentuBazyWiedzy(knowledgeDocumentId, isSelected) {
  const documentId = Number(knowledgeDocumentId || 0);
  if (!documentId) return;
  const selected = new Set(pobierzZaznaczoneIdDokumentowBazyWiedzy());
  if (isSelected) selected.add(documentId);
  else selected.delete(documentId);
  ustawZaznaczoneDokumentyBazyWiedzy(Array.from(selected));
}

function zapewnijStanRozszerzenBazyWiedzy() {
  if (!stan.filtryBazyWiedzy) {
    stan.filtryBazyWiedzy = { lifecycle: "", status: "", businessStatus: "", source: "", search: "" };
  } else if (!Object.prototype.hasOwnProperty.call(stan.filtryBazyWiedzy, "lifecycle")) {
    stan.filtryBazyWiedzy = { lifecycle: "", status: "", businessStatus: "", source: "", search: "", ...stan.filtryBazyWiedzy };
  }
  if (!Object.prototype.hasOwnProperty.call(stan.filtryBazyWiedzy, "businessStatus")) stan.filtryBazyWiedzy.businessStatus = "";
  if (!Object.prototype.hasOwnProperty.call(stan, "wybranyDokumentWiedzyId")) stan.wybranyDokumentWiedzyId = null;
  if (!Object.prototype.hasOwnProperty.call(stan, "ostatniPayloadBazyWiedzy")) stan.ostatniPayloadBazyWiedzy = null;
  if (!Object.prototype.hasOwnProperty.call(stan, "widokBazyWiedzy")) stan.widokBazyWiedzy = "assistant";
  if (!Object.prototype.hasOwnProperty.call(stan, "widokDokumentowBazyWiedzy")) stan.widokDokumentowBazyWiedzy = "recent";
  if (!Object.prototype.hasOwnProperty.call(stan, "szczegolyDokumentowWiedzy")) stan.szczegolyDokumentowWiedzy = {};
  if (!Object.prototype.hasOwnProperty.call(stan, "trwaPobieranieSzczegolowDokumentuWiedzy")) stan.trwaPobieranieSzczegolowDokumentuWiedzy = {};
  if (!Object.prototype.hasOwnProperty.call(stan, "bledySzczegolowDokumentuWiedzy")) stan.bledySzczegolowDokumentuWiedzy = {};
  if (!Object.prototype.hasOwnProperty.call(stan, "porownanieWersjiBazyWiedzy")) stan.porownanieWersjiBazyWiedzy = null;
  if (!Object.prototype.hasOwnProperty.call(stan, "trwaPobieraniePorownaniaWersjiBazyWiedzy")) stan.trwaPobieraniePorownaniaWersjiBazyWiedzy = false;
  if (!Object.prototype.hasOwnProperty.call(stan, "bladPorownaniaWersjiBazyWiedzy")) stan.bladPorownaniaWersjiBazyWiedzy = "";
  if (!Object.prototype.hasOwnProperty.call(stan, "widokPorownaniaWersjiBazyWiedzy")) stan.widokPorownaniaWersjiBazyWiedzy = "blocks";
  if (!Object.prototype.hasOwnProperty.call(stan, "trybPodgladuInlineBazyWiedzy")) stan.trybPodgladuInlineBazyWiedzy = "text";
  if (!Object.prototype.hasOwnProperty.call(stan, "zaznaczoneDokumentyWiedzy")) stan.zaznaczoneDokumentyWiedzy = [];
  if (!Object.prototype.hasOwnProperty.call(stan, "trwaAkcjaMasowaBazyWiedzy")) stan.trwaAkcjaMasowaBazyWiedzy = false;
  if (!Object.prototype.hasOwnProperty.call(stan, "ostatniWynikAkcjiMasowejBazyWiedzy")) stan.ostatniWynikAkcjiMasowejBazyWiedzy = null;
  if (!Object.prototype.hasOwnProperty.call(stan, "folderMasowyBazyWiedzy")) stan.folderMasowyBazyWiedzy = "";
  if (!Object.prototype.hasOwnProperty.call(stan, "kandydaciPrzypisanBazyWiedzy")) stan.kandydaciPrzypisanBazyWiedzy = [];
  if (!Object.prototype.hasOwnProperty.call(stan, "kandydaciPrzypisanBazyWiedzyOrgId")) stan.kandydaciPrzypisanBazyWiedzyOrgId = null;
  if (!Object.prototype.hasOwnProperty.call(stan, "trwaWczytywanieKandydatowPrzypisanBazyWiedzy")) stan.trwaWczytywanieKandydatowPrzypisanBazyWiedzy = false;
  if (!Object.prototype.hasOwnProperty.call(stan, "modalDecyzjiDokumentuWiedzy")) stan.modalDecyzjiDokumentuWiedzy = null;
  if (!Object.prototype.hasOwnProperty.call(stan, "modalZadaniaDokumentuWiedzy")) stan.modalZadaniaDokumentuWiedzy = null;
  if (!Object.prototype.hasOwnProperty.call(stan, "czySterowanieBazyWiedzyPodpiete")) stan.czySterowanieBazyWiedzyPodpiete = false;
  if (!stan.czySterowanieBazyWiedzyPodpiete) {
    document.getElementById("knowledge-mode-assistant")?.addEventListener("click", () => ustawTrybBazyWiedzy("assistant"));
    document.getElementById("knowledge-mode-documents")?.addEventListener("click", () => ustawTrybBazyWiedzy("documents"));
    document.getElementById("knowledge-documents-view-recent")?.addEventListener("click", () => ustawWidokDokumentowBazyWiedzy("recent"));
    document.getElementById("knowledge-documents-view-folders")?.addEventListener("click", () => ustawWidokDokumentowBazyWiedzy("folders"));
    stan.czySterowanieBazyWiedzyPodpiete = true;
  }
}

function zsynchronizujFiltryBazyWiedzyZFormularzem() {
  zapewnijStanRozszerzenBazyWiedzy();
  [["knowledge-filter-lifecycle", "lifecycle"], ["knowledge-filter-status", "status"], ["knowledge-filter-business-status", "businessStatus"], ["knowledge-filter-source", "source"], ["knowledge-filter-search", "search"]].forEach(
    ([id, key]) => {
      const element = document.getElementById(id);
      if (element) element.value = stan.filtryBazyWiedzy[key] || "";
    }
  );
}

function odczytajFiltryBazyWiedzyZFormularza() {
  zapewnijStanRozszerzenBazyWiedzy();
  stan.filtryBazyWiedzy = {
    lifecycle: document.getElementById("knowledge-filter-lifecycle")?.value || "",
    status: document.getElementById("knowledge-filter-status")?.value || "",
    businessStatus: document.getElementById("knowledge-filter-business-status")?.value || "",
    source: document.getElementById("knowledge-filter-source")?.value || "",
    search: document.getElementById("knowledge-filter-search")?.value.trim().toLowerCase() || "",
  };
}

function zsynchronizujCacheSzczegolowDokumentowBazyWiedzy(documents) {
  zapewnijStanRozszerzenBazyWiedzy();
  const nextDetails = {};
  const previousDetails = stan.szczegolyDokumentowWiedzy || {};
  const nextIds = new Set((documents || []).map((item) => Number(item.knowledge_document_id)));
  (documents || []).forEach((document) => {
    const id = Number(document.knowledge_document_id);
    const cached = previousDetails[id];
    if (
      cached &&
      String(cached.updated_at || "") === String(document.updated_at || "") &&
      Number(cached.current_version_number || 0) === Number(document.current_version_number || 0) &&
      String(cached.lifecycle_status || "active") === String(document.lifecycle_status || "active") &&
      String(cached.processing_status || "queued") === String(document.processing_status || "queued")
    ) {
      nextDetails[id] = cached;
    }
  });
  stan.szczegolyDokumentowWiedzy = nextDetails;
  Object.keys(stan.trwaPobieranieSzczegolowDokumentuWiedzy || {}).forEach((rawId) => {
    if (!nextIds.has(Number(rawId))) delete stan.trwaPobieranieSzczegolowDokumentuWiedzy[rawId];
  });
  Object.keys(stan.bledySzczegolowDokumentuWiedzy || {}).forEach((rawId) => {
    if (!nextIds.has(Number(rawId))) delete stan.bledySzczegolowDokumentuWiedzy[rawId];
  });
}

function pobierzDokumentBazyWiedzy(knowledgeDocumentId) {
  zapewnijStanRozszerzenBazyWiedzy();
  const id = Number(knowledgeDocumentId || 0);
  if (!id) return null;
  return stan.szczegolyDokumentowWiedzy[id] || (stan.dokumentyWiedzy || []).find((item) => Number(item.knowledge_document_id) === id) || null;
}

function pobierzAkcjeDecyzjiDokumentuBazyWiedzy(dokument) {
  return Array.isArray(dokument?.decision_actions) ? dokument.decision_actions.filter(Boolean) : [];
}

function czyMoznaTworzycZadaniaZDokuBazyWiedzy() {
  return typeof czyMoznaKorzystacZMojejPracy === "function" ? czyMoznaKorzystacZMojejPracy() : false;
}

function zbudujAkcjeOperacyjneDokumentuBazyWiedzy(dokument, options = {}) {
  const documentId = Number(dokument?.knowledge_document_id || 0);
  if (!documentId) return "";
  if (String(dokument?.lifecycle_status || "active") !== "active") return "";
  const compact = Boolean(options.compact);
  const maxActions = Math.max(0, Number(options.limit || 0)) || 3;
  const includeOpen = Boolean(options.includeOpen);
  const includeTask = options.includeTask !== false;
  const actions = pobierzAkcjeDecyzjiDokumentuBazyWiedzy(dokument).slice(0, maxActions);
  const buttonClass = compact ? "secondary small-action" : "secondary";
  const pieces = [];
  if (includeOpen) {
    pieces.push(
      `<button type="button" class="${buttonClass}" data-knowledge-open-document="${bezpiecznyTekst(documentId)}">Otworz</button>`
    );
  }
  actions.forEach((action) => {
    pieces.push(
      `<button type="button" class="${buttonClass}" data-knowledge-open-decision-modal="${bezpiecznyTekst(documentId)}" data-knowledge-decision-action="${bezpiecznyTekst(action.code || "")}">${bezpiecznyTekst(action.label || action.code || "Decyzja")}</button>`
    );
  });
  if (includeTask && czyMoznaTworzycZadaniaZDokuBazyWiedzy()) {
    pieces.push(
      `<button type="button" class="${buttonClass}" data-knowledge-open-task-modal="${bezpiecznyTekst(documentId)}">Utworz zadanie</button>`
    );
  }
  if (!pieces.length) return "";
  return `<div class="knowledge-inline-actions ${compact ? "is-compact" : ""}">${pieces.join("")}</div>`;
}

function zbudujPanelOperacyjnyDokumentuBazyWiedzy(dokument) {
  const actions = zbudujAkcjeOperacyjneDokumentuBazyWiedzy(dokument, {
    limit: 4,
    compact: false,
    includeOpen: false,
    includeTask: true,
  });
  const actionList = pobierzAkcjeDecyzjiDokumentuBazyWiedzy(dokument);
  const firstHint = String(actionList[0]?.hint || "").trim();
  if (!actions) {
    return `
      <div class="knowledge-action-panel">
        <strong>Decyzje i dalsza praca</strong>
        <div class="empty-state">Ten dokument nie ma teraz szybkich akcji decyzji. Nadal mozna pracowac na komentarzach, wersjach i audycie.</div>
      </div>
    `;
  }
  return `
    <div class="knowledge-action-panel knowledge-decision-panel">
      <strong>Decyzje i dalsza praca</strong>
      <p class="subtle-note">To jest operacyjny fragment dokumentu: podejmujesz decyzje z powodem, a w razie potrzeby od razu zakladasz zadanie powiazane z tym plikiem.</p>
      ${actions}
      ${firstHint ? `<div class="knowledge-inline-note knowledge-action-note">${bezpiecznyTekst(firstHint)}</div>` : ""}
    </div>
  `;
}

function pobierzDomyslnyTytulZadaniaZDokuBazyWiedzy(dokument) {
  const title = String(dokument?.title || "Dokument firmowy").trim();
  const businessStatus = String(dokument?.business_status || "roboczy");
  if (businessStatus === "do_akceptacji") return `Podejmij decyzje dla dokumentu: ${title}`;
  if (businessStatus === "do_sprawdzenia") return `Sprawdz dokument: ${title}`;
  if (businessStatus === "obowiazujacy") return `Wdrozenie zmian w dokumencie: ${title}`;
  return `Dalsza praca nad dokumentem: ${title}`;
}

function pobierzDomyslnyPriorytetZadaniaZDokuBazyWiedzy(dokument) {
  const businessStatus = String(dokument?.business_status || "roboczy");
  if (businessStatus === "do_akceptacji") return "wysoki";
  if (businessStatus === "do_sprawdzenia") return "normalny";
  return "normalny";
}

function pobierzDomyslniePrzypisanaOsobeDlaZadaniaZDokuBazyWiedzy(dokument) {
  const businessStatus = String(dokument?.business_status || "roboczy");
  if (businessStatus === "do_akceptacji") return Number(dokument?.approver_user_id || 0) || null;
  if (businessStatus === "do_sprawdzenia") return Number(dokument?.reviewer_user_id || 0) || null;
  return Number(dokument?.owner_user_id || 0) || null;
}

function zbudujPodsumowanieDokumentuDoModaluBazyWiedzy(dokument, extraNote = "") {
  const pills = [
    `<span class="pill history-pill">${bezpiecznyTekst(formatujStanObieguDokumentuBazyWiedzy(dokument?.business_status || "roboczy"))}</span>`,
    `<span class="pill history-pill">${bezpiecznyTekst(dokument?.library_path_label || "Bez folderu")}</span>`,
    dokument?.official_version_number ? `<span class="pill history-pill">obow. v${bezpiecznyTekst(dokument.official_version_number)}</span>` : "",
    dokument?.current_version_number ? `<span class="pill history-pill">najn. v${bezpiecznyTekst(dokument.current_version_number)}</span>` : "",
  ]
    .filter(Boolean)
    .join("");
  return `
    <div class="knowledge-modal-summary-card">
      <strong>${bezpiecznyTekst(dokument?.title || "Dokument firmowy")}</strong>
      <div class="knowledge-audit-highlights">${pills}</div>
      <div class="subtle-note">${bezpiecznyTekst(extraNote || dokument?.workflow_status_label || "Dokument jest gotowy do dalszej pracy.")}</div>
    </div>
  `;
}

async function odswiezDanePoAkcjiDokumentuBazyWiedzy(options = {}) {
  const tasks = [];
  if (typeof wczytajBazeWiedzy === "function" && czyModulWiedzyMaZakres()) {
    tasks.push(wczytajBazeWiedzy().catch(() => {}));
  }
  if (typeof wczytajLogi === "function") {
    tasks.push(wczytajLogi().catch(() => {}));
  }
  if (typeof wczytajDashboard === "function" && stan.biezacyUzytkownik) {
    tasks.push(wczytajDashboard().catch(() => {}));
  }
  if (options.refreshTasks && czyMoznaTworzycZadaniaZDokuBazyWiedzy()) {
    if (typeof wczytajZadania === "function") tasks.push(wczytajZadania().catch(() => {}));
    if (typeof wczytajPlannerZadan === "function") tasks.push(wczytajPlannerZadan().catch(() => {}));
    if (typeof wczytajFokusZadan === "function") tasks.push(wczytajFokusZadan().catch(() => {}));
  }
  await Promise.all(tasks);
  if (stan.szybkiPanelPracyOtwarty && typeof renderujSzybkiPanelPracy === "function") {
    renderujSzybkiPanelPracy();
  }
}

function zamknijModalDecyzjiDokumentuBazyWiedzy() {
  const shell = document.getElementById("knowledge-decision-modal");
  if (!shell) return;
  shell.classList.add("hidden");
  shell.setAttribute("aria-hidden", "true");
  stan.modalDecyzjiDokumentuWiedzy = null;
}

function renderujModalDecyzjiDokumentuBazyWiedzy() {
  const shell = document.getElementById("knowledge-decision-modal");
  const title = document.getElementById("knowledge-decision-modal-title");
  const subtitle = document.getElementById("knowledge-decision-modal-subtitle");
  const summary = document.getElementById("knowledge-decision-modal-summary");
  const reason = document.getElementById("knowledge-decision-modal-reason");
  const owner = document.getElementById("knowledge-decision-modal-owner");
  const reviewer = document.getElementById("knowledge-decision-modal-reviewer");
  const approver = document.getElementById("knowledge-decision-modal-approver");
  const submit = document.getElementById("knowledge-decision-modal-submit");
  if (!shell || !title || !subtitle || !summary || !reason || !owner || !reviewer || !approver || !submit) return;
  const modalState = stan.modalDecyzjiDokumentuWiedzy;
  if (!modalState) {
    shell.classList.add("hidden");
    shell.setAttribute("aria-hidden", "true");
    return;
  }
  const documentData = pobierzDokumentBazyWiedzy(modalState.documentId);
  const action = pobierzAkcjeDecyzjiDokumentuBazyWiedzy(documentData).find(
    (item) => String(item.code || "") === String(modalState.actionCode || "")
  );
  title.textContent = action?.label || "Decyzja dla dokumentu";
  subtitle.textContent = action?.hint || "Ta decyzja zapisze sie w historii dokumentu i odswiezy kolejke pracy.";
  summary.innerHTML = zbudujPodsumowanieDokumentuDoModaluBazyWiedzy(
    documentData,
    "Mozesz jednoczesnie zmienic osoby odpowiedzialne, jesli tego wymaga kolejny etap obiegu."
  );
  owner.innerHTML = zbudujOpcjeKandydatowPrzypisanBazyWiedzy(documentData?.owner_user_id, documentData?.owner_user_label);
  reviewer.innerHTML = zbudujOpcjeKandydatowPrzypisanBazyWiedzy(documentData?.reviewer_user_id, documentData?.reviewer_user_label);
  approver.innerHTML = zbudujOpcjeKandydatowPrzypisanBazyWiedzy(documentData?.approver_user_id, documentData?.approver_user_label);
  reason.value = modalState.reason || "";
  submit.textContent = modalState.isSaving ? "Zapisuje..." : action?.label || "Zapisz decyzje";
  submit.disabled = Boolean(modalState.isSaving);
  [reason, owner, reviewer, approver].forEach((element) => {
    element.disabled = Boolean(modalState.isSaving);
  });
  shell.classList.remove("hidden");
  shell.setAttribute("aria-hidden", "false");
}

async function otworzModalDecyzjiDokumentuBazyWiedzy(knowledgeDocumentId, actionCode) {
  const documentId = Number(knowledgeDocumentId || 0);
  if (!documentId) return;
  const detail = await wczytajSzczegolyDokumentuBazyWiedzy(documentId);
  if (czyMoznaZarzadzacPrzetwarzaniemBazyWiedzy()) {
    await wczytajKandydatowPrzypisanDokumentowBazyWiedzy().catch(() => []);
  }
  const availableAction = pobierzAkcjeDecyzjiDokumentuBazyWiedzy(detail).find(
    (item) => String(item.code || "") === String(actionCode || "")
  );
  if (!availableAction) {
    pokazPowiadomienie("Ta akcja nie jest teraz dostepna dla wybranego dokumentu.");
    return;
  }
  stan.modalDecyzjiDokumentuWiedzy = {
    documentId,
    actionCode: String(actionCode || ""),
    reason: "",
    isSaving: false,
  };
  renderujModalDecyzjiDokumentuBazyWiedzy();
  window.setTimeout(() => document.getElementById("knowledge-decision-modal-reason")?.focus(), 0);
}

async function zapiszDecyzjeDokumentuBazyWiedzyZModala() {
  const modalState = stan.modalDecyzjiDokumentuWiedzy;
  if (!modalState) return;
  const documentData = pobierzDokumentBazyWiedzy(modalState.documentId);
  const reason = String(document.getElementById("knowledge-decision-modal-reason")?.value || "").trim();
  if (!reason) return pokazPowiadomienie("Powod decyzji jest wymagany.");
  stan.modalDecyzjiDokumentuWiedzy = { ...modalState, isSaving: true, reason };
  renderujModalDecyzjiDokumentuBazyWiedzy();
  try {
    await api(zbudujAdresZOrganizacja(`/api/knowledge/documents/${modalState.documentId}/decision`), {
      method: "POST",
      body: JSON.stringify({
        action: modalState.actionCode,
        reason,
        owner_user_id: document.getElementById("knowledge-decision-modal-owner")?.value || null,
        reviewer_user_id: document.getElementById("knowledge-decision-modal-reviewer")?.value || null,
        approver_user_id: document.getElementById("knowledge-decision-modal-approver")?.value || null,
      }),
    });
    zamknijModalDecyzjiDokumentuBazyWiedzy();
    pokazPowiadomienie(`Zapisano decyzje dla dokumentu ${documentData?.title || ""}.`.trim());
    await odswiezDanePoAkcjiDokumentuBazyWiedzy();
  } catch (error) {
    stan.modalDecyzjiDokumentuWiedzy = { ...modalState, isSaving: false, reason };
    renderujModalDecyzjiDokumentuBazyWiedzy();
    pokazPowiadomienie(error.message);
  }
}

function zamknijModalZadaniaDokumentuBazyWiedzy() {
  const shell = document.getElementById("knowledge-task-modal");
  if (!shell) return;
  shell.classList.add("hidden");
  shell.setAttribute("aria-hidden", "true");
  stan.modalZadaniaDokumentuWiedzy = null;
}

function renderujModalZadaniaDokumentuBazyWiedzy() {
  const shell = document.getElementById("knowledge-task-modal");
  const title = document.getElementById("knowledge-task-modal-title");
  const subtitle = document.getElementById("knowledge-task-modal-subtitle");
  const summary = document.getElementById("knowledge-task-modal-summary");
  const titleInput = document.getElementById("knowledge-task-modal-title-input");
  const descriptionInput = document.getElementById("knowledge-task-modal-description");
  const assignedInput = document.getElementById("knowledge-task-modal-assigned-user");
  const priorityInput = document.getElementById("knowledge-task-modal-priority");
  const visibilityInput = document.getElementById("knowledge-task-modal-visibility");
  const dueAtInput = document.getElementById("knowledge-task-modal-due-at");
  const submit = document.getElementById("knowledge-task-modal-submit");
  if (!shell || !title || !subtitle || !summary || !titleInput || !descriptionInput || !assignedInput || !priorityInput || !visibilityInput || !dueAtInput || !submit) return;
  const modalState = stan.modalZadaniaDokumentuWiedzy;
  if (!modalState) {
    shell.classList.add("hidden");
    shell.setAttribute("aria-hidden", "true");
    return;
  }
  const documentData = pobierzDokumentBazyWiedzy(modalState.documentId);
  title.textContent = "Nowe zadanie z dokumentu";
  subtitle.textContent = "Zadanie zostanie powiazane z dokumentem, dzieki czemu historia pracy pozostanie wspolna i czytelna.";
  summary.innerHTML = zbudujPodsumowanieDokumentuDoModaluBazyWiedzy(
    documentData,
    "To dobry ruch, gdy decyzja wymaga dalszego dzialania poza samym dokumentem."
  );
  assignedInput.innerHTML = zbudujOpcjeKandydatowPrzypisanBazyWiedzy(modalState.assignedUserId, modalState.assignedUserLabel);
  titleInput.value = modalState.title || "";
  descriptionInput.value = modalState.description || "";
  priorityInput.value = modalState.priority || "normalny";
  visibilityInput.value = modalState.visibilityScope || "prywatne";
  dueAtInput.value = modalState.dueAt || "";
  submit.textContent = modalState.isSaving ? "Tworze..." : "Utworz zadanie";
  submit.disabled = Boolean(modalState.isSaving);
  [titleInput, descriptionInput, assignedInput, priorityInput, visibilityInput, dueAtInput].forEach((element) => {
    element.disabled = Boolean(modalState.isSaving);
  });
  shell.classList.remove("hidden");
  shell.setAttribute("aria-hidden", "false");
}

async function otworzModalZadaniaZDokuBazyWiedzy(knowledgeDocumentId) {
  const documentId = Number(knowledgeDocumentId || 0);
  if (!documentId) return;
  if (!czyMoznaTworzycZadaniaZDokuBazyWiedzy()) {
    pokazPowiadomienie("Ten zakres nie ma aktywnego modulu Asystent Szefa, wiec nie mozna teraz zalozyc zadania.");
    return;
  }
  const detail = await wczytajSzczegolyDokumentuBazyWiedzy(documentId);
  await wczytajKandydatowPrzypisanDokumentowBazyWiedzy().catch(() => []);
  const assignedUserId = pobierzDomyslniePrzypisanaOsobeDlaZadaniaZDokuBazyWiedzy(detail);
  const assignedUserLabel =
    assignedUserId && Number(detail?.owner_user_id || 0) === Number(assignedUserId)
      ? detail?.owner_user_label || ""
      : assignedUserId && Number(detail?.reviewer_user_id || 0) === Number(assignedUserId)
        ? detail?.reviewer_user_label || ""
        : assignedUserId && Number(detail?.approver_user_id || 0) === Number(assignedUserId)
          ? detail?.approver_user_label || ""
          : "";
  stan.modalZadaniaDokumentuWiedzy = {
    documentId,
    title: pobierzDomyslnyTytulZadaniaZDokuBazyWiedzy(detail),
    description: `Dokument: ${detail?.title || "Dokument firmowy"}\nFolder: ${detail?.library_path_label || "Bez folderu"}\nAktualny stan: ${formatujStanObieguDokumentuBazyWiedzy(detail?.business_status || "roboczy")}`,
    assignedUserId,
    assignedUserLabel,
    priority: pobierzDomyslnyPriorytetZadaniaZDokuBazyWiedzy(detail),
    visibilityScope: "prywatne",
    dueAt: "",
    isSaving: false,
  };
  renderujModalZadaniaDokumentuBazyWiedzy();
  window.setTimeout(() => document.getElementById("knowledge-task-modal-title-input")?.focus(), 0);
}

async function zapiszZadanieZDokuBazyWiedzyZModala() {
  const modalState = stan.modalZadaniaDokumentuWiedzy;
  if (!modalState) return;
  const documentData = pobierzDokumentBazyWiedzy(modalState.documentId);
  const title = String(document.getElementById("knowledge-task-modal-title-input")?.value || "").trim();
  if (!title) return pokazPowiadomienie("Tytul zadania jest wymagany.");
  const description = String(document.getElementById("knowledge-task-modal-description")?.value || "").trim();
  stan.modalZadaniaDokumentuWiedzy = {
    ...modalState,
    title,
    description,
    isSaving: true,
  };
  renderujModalZadaniaDokumentuBazyWiedzy();
  try {
    const payload = {
      title,
      description,
      task_type: "zadanie",
      priority: document.getElementById("knowledge-task-modal-priority")?.value || "normalny",
      visibility_scope: document.getElementById("knowledge-task-modal-visibility")?.value || "prywatne",
      assigned_user_id: document.getElementById("knowledge-task-modal-assigned-user")?.value || null,
      due_at: document.getElementById("knowledge-task-modal-due-at")?.value || null,
    };
    const result = await api(zbudujAdresZOrganizacja(`/api/knowledge/documents/${modalState.documentId}/tasks`), {
      method: "POST",
      body: JSON.stringify(payload),
    });
    zamknijModalZadaniaDokumentuBazyWiedzy();
    pokazPowiadomienie(`Utworzono zadanie: ${result?.task?.title || title}.`);
    await odswiezDanePoAkcjiDokumentuBazyWiedzy({ refreshTasks: true });
    if (result?.document?.knowledge_document_id) {
      ustawWybranyDokumentBazyWiedzy(result.document.knowledge_document_id, { fetchDetail: true });
    } else if (documentData?.knowledge_document_id) {
      ustawWybranyDokumentBazyWiedzy(documentData.knowledge_document_id, { fetchDetail: true });
    }
  } catch (error) {
    stan.modalZadaniaDokumentuWiedzy = {
      ...modalState,
      title,
      description,
      isSaving: false,
    };
    renderujModalZadaniaDokumentuBazyWiedzy();
    pokazPowiadomienie(error.message);
  }
}

async function otworzDokumentBazyWiedzyZWidokuPracy(knowledgeDocumentId) {
  const documentId = Number(knowledgeDocumentId || 0);
  if (!documentId) return;
  ustawWidok("knowledge");
  if (typeof ustawTrybBazyWiedzy === "function") {
    ustawTrybBazyWiedzy("documents");
  }
  if (typeof wczytajBazeWiedzy === "function") {
    await wczytajBazeWiedzy();
  }
  ustawWybranyDokumentBazyWiedzy(documentId, { fetchDetail: true, forceDetail: true });
  document.getElementById("knowledge-selected-document")?.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function wczytajSzczegolyDokumentuBazyWiedzy(knowledgeDocumentId, options = {}) {
  zapewnijStanRozszerzenBazyWiedzy();
  const id = Number(knowledgeDocumentId || 0);
  if (!id || !czyModulWiedzyMaZakres() || !czyMoznaCzytacBazeWiedzy()) return null;
  const baseDocument = (stan.dokumentyWiedzy || []).find((item) => Number(item.knowledge_document_id) === id) || null;
  const cached = stan.szczegolyDokumentowWiedzy[id];
  const cacheIsFresh =
    !options.force &&
    cached &&
    baseDocument &&
    String(cached.updated_at || "") === String(baseDocument.updated_at || "") &&
    Number(cached.current_version_number || 0) === Number(baseDocument.current_version_number || 0) &&
    String(cached.lifecycle_status || "active") === String(baseDocument.lifecycle_status || "active") &&
    String(cached.processing_status || "queued") === String(baseDocument.processing_status || "queued");
  if (cacheIsFresh) return cached;
  if (!options.force && stan.trwaPobieranieSzczegolowDokumentuWiedzy[id]) return stan.trwaPobieranieSzczegolowDokumentuWiedzy[id];

  delete stan.bledySzczegolowDokumentuWiedzy[id];
  const includeDeleted = czyMoznaZarzadzacPrzetwarzaniemBazyWiedzy() ? "?include_deleted=1" : "";
  const request = api(zbudujAdresZOrganizacja(`/api/knowledge/documents/${id}${includeDeleted}`))
    .then((detail) => {
      stan.szczegolyDokumentowWiedzy[id] = detail;
      return detail;
    })
    .catch((error) => {
      stan.bledySzczegolowDokumentuWiedzy[id] = error.message || "Nie udalo sie wczytac szczegolow dokumentu.";
      throw error;
    })
    .finally(() => {
      delete stan.trwaPobieranieSzczegolowDokumentuWiedzy[id];
      if (Number(stan.wybranyDokumentWiedzyId) === id) renderujPodgladDokumentuBazyWiedzy();
    });
  stan.trwaPobieranieSzczegolowDokumentuWiedzy[id] = request;
  return request;
}

function ustawWybranyDokumentBazyWiedzy(knowledgeDocumentId, options = {}) {
  zapewnijStanRozszerzenBazyWiedzy();
  const previousDocumentId = Number(stan.wybranyDokumentWiedzyId || 0);
  stan.wybranyDokumentWiedzyId = knowledgeDocumentId ? Number(knowledgeDocumentId) : null;
  if (previousDocumentId !== Number(stan.wybranyDokumentWiedzyId || 0)) {
    stan.porownanieWersjiBazyWiedzy = null;
    stan.trwaPobieraniePorownaniaWersjiBazyWiedzy = false;
    stan.bladPorownaniaWersjiBazyWiedzy = "";
    stan.trybPodgladuInlineBazyWiedzy = "text";
  }
  if (options.rerender !== false) odswiezWidokBazyWiedzyZPamieci();
  else renderujPodgladDokumentuBazyWiedzy();
  if (stan.wybranyDokumentWiedzyId && options.fetchDetail !== false) {
    wczytajSzczegolyDokumentuBazyWiedzy(stan.wybranyDokumentWiedzyId, { force: Boolean(options.forceDetail) }).catch(() => {});
  }
}

async function wczytajBazeWiedzy() {
  zapewnijStanRozszerzenBazyWiedzy();
  if (!stan.biezacyUzytkownik) {
    stan.szczegolyDokumentowWiedzy = {};
    stan.trwaPobieranieSzczegolowDokumentuWiedzy = {};
    stan.bledySzczegolowDokumentuWiedzy = {};
    stan.porownanieWersjiBazyWiedzy = null;
    stan.trwaPobieraniePorownaniaWersjiBazyWiedzy = false;
    stan.bladPorownaniaWersjiBazyWiedzy = "";
    stan.trybPodgladuInlineBazyWiedzy = "text";
    stan.zaznaczoneDokumentyWiedzy = [];
    stan.ostatniWynikAkcjiMasowejBazyWiedzy = null;
    stan.folderMasowyBazyWiedzy = "";
    stan.kandydaciPrzypisanBazyWiedzy = [];
    stan.kandydaciPrzypisanBazyWiedzyOrgId = null;
    wyczyscBazeWiedzy();
    anulujPollingBazyWiedzy();
    return;
  }
  if (!czyModulWiedzyMaZakres()) {
    stan.szczegolyDokumentowWiedzy = {};
    stan.trwaPobieranieSzczegolowDokumentuWiedzy = {};
    stan.bledySzczegolowDokumentuWiedzy = {};
    stan.porownanieWersjiBazyWiedzy = null;
    stan.trwaPobieraniePorownaniaWersjiBazyWiedzy = false;
    stan.bladPorownaniaWersjiBazyWiedzy = "";
    stan.trybPodgladuInlineBazyWiedzy = "text";
    stan.zaznaczoneDokumentyWiedzy = [];
    stan.ostatniWynikAkcjiMasowejBazyWiedzy = null;
    stan.folderMasowyBazyWiedzy = "";
    stan.kandydaciPrzypisanBazyWiedzy = [];
    stan.kandydaciPrzypisanBazyWiedzyOrgId = null;
    wyczyscBazeWiedzy();
    document.getElementById("knowledge-access-note").textContent = "Wybierz konkretna organizacje, aby otworzyc jej baze wiedzy.";
    anulujPollingBazyWiedzy();
    return;
  }
  const query = czyMoznaZarzadzacPrzetwarzaniemBazyWiedzy() ? "?include_deleted=1" : "";
  renderujBazeWiedzy(await api(zbudujAdresZOrganizacja(`/api/knowledge/documents${query}`)));
  if (czyMoznaZarzadzacPrzetwarzaniemBazyWiedzy()) {
    await wczytajKandydatowPrzypisanDokumentowBazyWiedzy();
  }
}

async function wczytajKandydatowPrzypisanDokumentowBazyWiedzy(options = {}) {
  zapewnijStanRozszerzenBazyWiedzy();
  if (!czyMoznaZarzadzacPrzetwarzaniemBazyWiedzy() || !czyModulWiedzyMaZakres()) {
    stan.kandydaciPrzypisanBazyWiedzy = [];
    stan.kandydaciPrzypisanBazyWiedzyOrgId = null;
    stan.trwaWczytywanieKandydatowPrzypisanBazyWiedzy = false;
    return [];
  }
  const organizationId = Number(stan.konfiguracjaBazyWiedzy?.organization_id || stan.wybranaOrganizacjaId || 0);
  if (!organizationId) {
    stan.kandydaciPrzypisanBazyWiedzy = [];
    stan.kandydaciPrzypisanBazyWiedzyOrgId = null;
    return [];
  }
  if (!options.force && Number(stan.kandydaciPrzypisanBazyWiedzyOrgId || 0) === organizationId && stan.kandydaciPrzypisanBazyWiedzy.length) {
    return stan.kandydaciPrzypisanBazyWiedzy;
  }
  stan.trwaWczytywanieKandydatowPrzypisanBazyWiedzy = true;
  try {
    const candidates = await api(zbudujAdresZOrganizacja("/api/knowledge/assignment-candidates"));
    stan.kandydaciPrzypisanBazyWiedzy = Array.isArray(candidates) ? candidates : [];
    stan.kandydaciPrzypisanBazyWiedzyOrgId = organizationId;
    return stan.kandydaciPrzypisanBazyWiedzy;
  } finally {
    stan.trwaWczytywanieKandydatowPrzypisanBazyWiedzy = false;
  }
}

function pobierzPrzefiltrowaneDokumentyBazyWiedzy() {
  zapewnijStanRozszerzenBazyWiedzy();
  const filters = stan.filtryBazyWiedzy || {};
  return pobierzDokumentyBibliotekiBazyWiedzy().filter((document) => {
    const lifecycleOk = !filters.lifecycle || String(document.lifecycle_status || "active") === filters.lifecycle;
    const statusOk = !filters.status || String(document.processing_status || "") === filters.status;
    const businessStatusOk = !filters.businessStatus || String(document.business_status || "roboczy") === filters.businessStatus;
    const sourceOk = !filters.source || String(document.source_type || "") === filters.source;
    const haystack = [
      document.title,
      document.file_name,
      document.snippet,
      document.content_preview,
      document.library_path,
      document.library_path_label,
      document.duplicate_reason,
      formatujZrodloBazyWiedzy(document.source_type || "manual"),
      formatujStatusPrzetwarzaniaBazyWiedzy(document.processing_status || "queued"),
      formatujStanObieguDokumentuBazyWiedzy(document.business_status || "roboczy"),
      formatujLifecycleDokumentuBazyWiedzy(document.lifecycle_status || "active"),
      formatujStatusDuplikatuBazyWiedzy(document.duplicate_status || "none"),
      document.owner_user_label,
      document.reviewer_user_label,
      document.approver_user_label,
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
    return lifecycleOk && statusOk && businessStatusOk && sourceOk && (!filters.search || haystack.includes(filters.search));
  });
}

function formatujTypJobaBazyWiedzy(jobType) {
  return (
    {
      ingest: "import",
      reprocess: "ponowne przetwarzanie",
      replace: "podmiana pliku",
      restore_version: "przywrocenie wersji",
    }[String(jobType || "ingest")] || "import"
  );
}

function zbudujKomentarzeDokumentuBazyWiedzy(dokument, options = {}) {
  const comments = Array.isArray(dokument.comments) ? dokument.comments : [];
  if (options.error) return `<div class="knowledge-error-note">${bezpiecznyTekst(options.error)}</div>`;
  if (options.loading && !comments.length) return `<div class="subtle-note">Wczytywanie komentarzy i adnotacji...</div>`;
  if (!comments.length) return `<div class="empty-state">Brak komentarzy i adnotacji. Ten panel moze sluzyc do uzgadniania zmian, zaznaczania zakresu i pracy nad nowymi wersjami.</div>`;
  return comments
    .map(
      (comment) => `
        <article class="knowledge-version-item knowledge-comment-item">
          <div class="knowledge-doc-selection">
            <strong>${bezpiecznyTekst(comment.author_label || "system")}</strong>
            <div class="knowledge-audit-highlights">
              <span class="pill history-pill">${bezpiecznyTekst(comment.annotation_kind_label || "Komentarz")}</span>
              <span class="pill history-pill">${bezpiecznyTekst(comment.target_label || "Dokument")}</span>
              ${comment.anchor_label ? `<span class="pill history-pill">zakres: ${bezpiecznyTekst(comment.anchor_label)}</span>` : ""}
            </div>
          </div>
          <div class="knowledge-preview-meta">
            <span>Dodano: ${formatujDateCzas(comment.created_at)}</span>
            ${comment.created_by_login ? `<span>Login: ${bezpiecznyTekst(comment.created_by_login)}</span>` : ""}
          </div>
          ${comment.anchor_excerpt ? `<div class="knowledge-inline-note knowledge-comment-anchor">${bezpiecznyTekst(comment.anchor_excerpt)}</div>` : ""}
          <p class="knowledge-audit-message">${bezpiecznyTekst(comment.note_text || "")}</p>
        </article>
      `
    )
    .join("");
}

function zbudujOpcjeKomentarzaDokumentuBazyWiedzy(dokument) {
  const versions = Array.isArray(dokument.versions) ? dokument.versions : [];
  const currentVersionNumber = Number(dokument.current_version_number || 0);
  const officialVersionNumber = Number(dokument.official_version_number || 0);
  return [
    '<option value="">Caly dokument</option>',
    ...versions.map((version) => {
      const versionNumber = Number(version.version_number || 0);
      const tags = [];
      if (versionNumber === officialVersionNumber && officialVersionNumber > 0) tags.push("obowiazujaca");
      if (versionNumber === currentVersionNumber && currentVersionNumber > 0) tags.push("najnowsza");
      const suffix = tags.length ? ` (${tags.join(", ")})` : "";
      return `<option value="${bezpiecznyTekst(versionNumber)}">Wersja v${bezpiecznyTekst(versionNumber)}${bezpiecznyTekst(suffix)}</option>`;
    }),
  ].join("");
}

function zbudujWersjeDokumentuBazyWiedzy(dokument) {
  if (!(dokument.versions || []).length) return `<div class="empty-state">Ten dokument nie ma jeszcze zapisanych wersji.</div>`;
  return dokument.versions
    .map((version, index, versions) => {
      const versionNumber = Number(version.version_number || 0);
      const isCurrent = Boolean(version.is_current);
      const isOfficial = Boolean(version.is_official);
      const restoreButton =
        czyMoznaZarzadzacPrzetwarzaniemBazyWiedzy() && String(dokument.lifecycle_status || "active") !== "deleted"
          ? `<button type="button" class="secondary" data-knowledge-restore-version="${bezpiecznyTekst(version.version_number)}">Przywroc te wersje</button>`
          : "";
      const markOfficialButton =
        czyMoznaZarzadzacPrzetwarzaniemBazyWiedzy() &&
        String(dokument.lifecycle_status || "active") !== "deleted" &&
        !isOfficial
          ? `<button type="button" class="secondary" data-knowledge-mark-official-version="${bezpiecznyTekst(version.version_number)}">Oznacz jako obowiazujaca</button>`
          : "";
      const compareButton =
        versionNumber === Number(dokument.current_version_number || 0)
          ? versions[index + 1]
            ? `<button type="button" class="secondary" data-knowledge-compare-left="${bezpiecznyTekst(version.version_number)}" data-knowledge-compare-right="${bezpiecznyTekst(versions[index + 1].version_number)}">Porownaj z v${bezpiecznyTekst(versions[index + 1].version_number)}</button>`
            : ""
          : `<button type="button" class="secondary" data-knowledge-compare-left="${bezpiecznyTekst(dokument.current_version_number || 0)}" data-knowledge-compare-right="${bezpiecznyTekst(version.version_number)}">Porownaj z aktualna</button>`;
      const versionLink =
        czyMoznaPobieracPlikiFirmowe() && version.file_link
          ? `<a href="${bezpiecznyTekst(version.file_link)}" target="_blank" rel="noreferrer">Plik wersji</a>`
          : "";
        return `
          <article class="knowledge-version-item">
            <div class="knowledge-doc-selection">
              <strong>Wersja v${bezpiecznyTekst(version.version_number)}</strong>
              <div class="knowledge-audit-highlights">
                <span class="pill history-pill">${bezpiecznyTekst(version.extraction_method || "import")}</span>
                ${isOfficial ? '<span class="pill history-pill">obowiazujaca</span>' : ""}
                ${isCurrent ? '<span class="pill history-pill">najnowsza</span>' : ""}
                ${Number(version.comment_count || 0) ? `<span class="pill history-pill">komentarze: ${bezpiecznyTekst(version.comment_count)}</span>` : ""}
              </div>
            </div>
            <div class="knowledge-preview-meta">
              <span>Znaki: ${bezpiecznyTekst(version.char_count || 0)}</span>
              <span>Zrodlo: ${bezpiecznyTekst(formatujZrodloBazyWiedzy(version.source_type || "manual"))}</span>
              <span>Utworzono: ${formatujDateCzas(version.created_at)}</span>
            </div>
            <p class="knowledge-version-snippet">${bezpiecznyTekst(version.snippet || "Brak fragmentu tresci dla tej wersji.")}</p>
            ${
              restoreButton || versionLink || compareButton || markOfficialButton
                ? `<div class="knowledge-admin-actions"><div class="subtle-note">Mozesz porownac zmiany, pobrac plik wersji, oznaczyc wersje obowiazujaca albo przywrocic ja do obiegu.</div><div class="filters-actions">${compareButton}${versionLink}${markOfficialButton}${restoreButton}</div></div>`
                : ""
            }
          </article>
        `;
    })
    .join("");
}

function zbudujZadaniaPrzetwarzaniaBazyWiedzy(dokument) {
  if (!(dokument.recent_jobs || []).length) return `<div class="empty-state">Brak zapisanych zadan przetwarzania.</div>`;
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

function klasaAudytuDokumentuBazyWiedzy(eventType) {
  if (eventType === "knowledge_document_downloaded") return "status-normal";
  if (eventType === "knowledge_document_deleted") return "status-danger";
  if (eventType === "knowledge_document_archived") return "status-warning";
  return "status-success";
}

function zbudujHistorieAudytuBazyWiedzy(dokument, options = {}) {
  const events = Array.isArray(dokument.audit_events) ? dokument.audit_events : [];
  if (options.error) return `<div class="knowledge-error-note">${bezpiecznyTekst(options.error)}</div>`;
  if (options.loading && !events.length) return `<div class="subtle-note">Wczytywanie pelnej historii dokumentu i pobran...</div>`;
  if (!events.length) return `<div class="empty-state">Brak zapisanych wpisow audytowych dla tego dokumentu.</div>`;
  return events
    .map((event) => {
      const highlights = Array.isArray(event.highlights) ? event.highlights : [];
      const transition =
        event.status_before && event.status_after && event.status_before !== event.status_after
          ? `<span class="pill history-pill">${bezpiecznyTekst(event.status_before)} -> ${bezpiecznyTekst(event.status_after)}</span>`
          : "";
      return `
        <article class="knowledge-version-item knowledge-audit-item">
          <div class="knowledge-doc-selection">
            <strong>${bezpiecznyTekst(event.action_label || event.event_type || "Zdarzenie")}</strong>
            <span class="status-badge ${klasaAudytuDokumentuBazyWiedzy(event.event_type)}">${bezpiecznyTekst(event.actor || "system")}</span>
          </div>
          <div class="knowledge-preview-meta">
            <span>Czas: ${formatujDateCzas(event.event_time)}</span>
            ${transition}
          </div>
          <p class="knowledge-audit-message">${bezpiecznyTekst(event.message || "Brak opisu zdarzenia.")}</p>
          ${highlights.length ? `<div class="knowledge-audit-highlights">${highlights.map((item) => `<span class="pill history-pill">${bezpiecznyTekst(item.label)}: ${bezpiecznyTekst(item.value)}</span>`).join("")}</div>` : ""}
        </article>
      `;
    })
    .join("");
}

async function pobierzPorownanieWersjiDokumentuBazyWiedzy(documentId, leftVersionNumber, rightVersionNumber) {
  zapewnijStanRozszerzenBazyWiedzy();
  const normalizedDocumentId = Number(documentId || 0);
  const normalizedLeft = Number(leftVersionNumber || 0);
  const normalizedRight = Number(rightVersionNumber || 0);
  if (!normalizedDocumentId || !normalizedLeft || !normalizedRight) {
    throw new Error("Brakuje dwoch poprawnych wersji do porownania.");
  }
  stan.trwaPobieraniePorownaniaWersjiBazyWiedzy = true;
  stan.bladPorownaniaWersjiBazyWiedzy = "";
  stan.porownanieWersjiBazyWiedzy = {
    knowledge_document_id: normalizedDocumentId,
    left_version: { version_number: normalizedLeft },
    right_version: { version_number: normalizedRight },
    summary: null,
    blocks: [],
  };
  renderujPodgladDokumentuBazyWiedzy();
  try {
    const result = await api(
      zbudujAdresZOrganizacja(
        `/api/knowledge/documents/${normalizedDocumentId}/compare?left_version=${normalizedLeft}&right_version=${normalizedRight}`
      )
    );
    stan.porownanieWersjiBazyWiedzy = result;
  } catch (error) {
    stan.bladPorownaniaWersjiBazyWiedzy = error.message || "Nie udalo sie porownac wersji dokumentu.";
    throw error;
  } finally {
    stan.trwaPobieraniePorownaniaWersjiBazyWiedzy = false;
    renderujPodgladDokumentuBazyWiedzy();
  }
}

function zbudujPanelObokSiebiePorownaniaBazyWiedzy(compareState) {
  const rows = Array.isArray(compareState?.side_by_side_rows) ? compareState.side_by_side_rows : [];
  if (!rows.length) return '<div class="empty-state">Brak wierszy do pokazania w widoku obok siebie.</div>';
  const bodyMarkup = rows
    .map(
      (row) => `
        <tr class="knowledge-compare-row is-${bezpiecznyTekst(row.type || "context")}">
          <td class="knowledge-compare-line-number">${bezpiecznyTekst(row.left_line_number || "")}</td>
          <td class="knowledge-compare-cell">${bezpiecznyTekst(row.left_text || "")}</td>
          <td class="knowledge-compare-line-number">${bezpiecznyTekst(row.right_line_number || "")}</td>
          <td class="knowledge-compare-cell">${bezpiecznyTekst(row.right_text || "")}</td>
        </tr>
      `
    )
    .join("");
  return `
    <div class="knowledge-compare-table-shell">
      <table class="knowledge-compare-table">
        <thead>
          <tr>
            <th colspan="2">Starsza v${bezpiecznyTekst(compareState?.base_version?.version_number || "?")}</th>
            <th colspan="2">Nowsza v${bezpiecznyTekst(compareState?.target_version?.version_number || "?")}</th>
          </tr>
        </thead>
        <tbody>${bodyMarkup}</tbody>
      </table>
    </div>
  `;
}

function zbudujPanelInlinePreviewDokumentuBazyWiedzy(dokument, options = {}) {
  const canPreviewFile = Boolean(options.canPreviewFile);
  const filePreviewKind = String(dokument.file_preview_kind || "none");
  const hasTextPreview = Boolean(dokument.content_text || dokument.content_preview);
  const fileModeAvailable = canPreviewFile && ["pdf", "image", "text"].includes(filePreviewKind);
  const previewMode = fileModeAvailable ? stan.trybPodgladuInlineBazyWiedzy || "text" : "text";
  const textMarkup = `<pre class="knowledge-inline-text-preview">${bezpiecznyTekst(dokument.content_text || dokument.content_preview || "Brak tresci do podgladu.")}</pre>`;
  let bodyMarkup = textMarkup;
  if (previewMode === "file" && fileModeAvailable) {
    const previewUrl = bezpiecznyTekst(pobierzAdresPodgladuPlikuDokumentuBazyWiedzy(dokument));
    if (filePreviewKind === "image") {
      bodyMarkup = `<img class="knowledge-file-preview-image" src="${previewUrl}" alt="Podglad pliku ${bezpiecznyTekst(dokument.file_name || dokument.title || "dokument")}" />`;
    } else {
      bodyMarkup = `<iframe class="knowledge-file-preview-frame" src="${previewUrl}" title="Podglad pliku ${bezpiecznyTekst(dokument.file_name || dokument.title || "dokument")}"></iframe>`;
    }
  } else if (!hasTextPreview && !fileModeAvailable) {
    bodyMarkup = '<div class="empty-state">Ten dokument nie ma jeszcze gotowego podgladu inline. Nadal mozna pobrac plik albo poczekac na przetworzenie.</div>';
  }
  const modeSwitchMarkup =
    fileModeAvailable && hasTextPreview
      ? `
        <div class="knowledge-documents-view-switch knowledge-inline-preview-switch">
          <button type="button" class="secondary ${previewMode === "text" ? "is-active" : ""}" data-knowledge-inline-mode="text">Tekst</button>
          <button type="button" class="secondary ${previewMode === "file" ? "is-active" : ""}" data-knowledge-inline-mode="file">Plik</button>
        </div>
      `
      : "";
  return `
    <div class="knowledge-inline-preview-card">
      <div class="knowledge-doc-selection">
        <div>
          <strong>Podglad inline</strong>
          <div class="subtle-note">Tekst pokazuje przetworzona tresc dokumentu, a tryb pliku otwiera obraz lub PDF bez wymuszania pobrania.</div>
        </div>
        ${modeSwitchMarkup}
      </div>
      ${bodyMarkup}
    </div>
  `;
}

function zbudujPanelPorownaniaWersjiBazyWiedzy(dokument) {
  const compareState = stan.porownanieWersjiBazyWiedzy;
  const isCurrentDocumentComparison =
    compareState && Number(compareState.knowledge_document_id || 0) === Number(dokument.knowledge_document_id || 0);
  const summary = isCurrentDocumentComparison ? compareState.summary || {} : {};
  const changeSummary = isCurrentDocumentComparison ? compareState.change_summary || {} : {};
  const blocks = isCurrentDocumentComparison ? compareState.blocks || [] : [];
  const versions = Array.isArray(dokument.versions) ? dokument.versions : [];
  const latestVersion = versions[0];
  const previousVersion = versions[1];
  const officialVersion = versions.find((version) => Number(version.version_number || 0) === Number(dokument.official_version_number || 0));

  if (stan.bladPorownaniaWersjiBazyWiedzy && isCurrentDocumentComparison) {
    return `<div class="knowledge-error-note">${bezpiecznyTekst(stan.bladPorownaniaWersjiBazyWiedzy)}</div>`;
  }
  if (stan.trwaPobieraniePorownaniaWersjiBazyWiedzy && isCurrentDocumentComparison) {
    return `<div class="subtle-note">Porownuje wersje v${bezpiecznyTekst(compareState?.target_version?.version_number || compareState?.left_version?.version_number || "?")} i v${bezpiecznyTekst(compareState?.base_version?.version_number || compareState?.right_version?.version_number || "?")}...</div>`;
  }
  if (!isCurrentDocumentComparison || !compareState?.summary) {
    if (latestVersion && officialVersion && Number(latestVersion.version_number || 0) !== Number(officialVersion.version_number || 0)) {
      return `
        <div class="knowledge-inline-note">
          W tym dokumencie najnowsza wersja nie jest jeszcze oznaczona jako obowiazujaca. To dobry moment, by porownac obieg roboczy z wersja oficjalna.
          <div class="knowledge-action-grid">
            <button type="button" class="secondary" data-knowledge-compare-left="${bezpiecznyTekst(latestVersion.version_number)}" data-knowledge-compare-right="${bezpiecznyTekst(officialVersion.version_number)}">
              Porownaj najnowsza v${bezpiecznyTekst(latestVersion.version_number)} z obowiazujaca v${bezpiecznyTekst(officialVersion.version_number)}
            </button>
          </div>
        </div>
      `;
    }
    if (latestVersion && previousVersion) {
      return `
        <div class="knowledge-inline-note">
          Najczesciej przydaje sie szybkie porownanie aktualnej wersji z poprzednia.
          <div class="knowledge-action-grid">
            <button type="button" class="secondary" data-knowledge-compare-left="${bezpiecznyTekst(latestVersion.version_number)}" data-knowledge-compare-right="${bezpiecznyTekst(previousVersion.version_number)}">
              Porownaj v${bezpiecznyTekst(latestVersion.version_number)} z v${bezpiecznyTekst(previousVersion.version_number)}
            </button>
          </div>
        </div>
      `;
    }
    return `<div class="empty-state">Dokument ma za malo wersji, aby pokazac porownanie zmian.</div>`;
  }

  const targetVersionNumber = compareState.target_version?.version_number || "?";
  const baseVersionNumber = compareState.base_version?.version_number || "?";
  const changeSummaryMarkup = changeSummary?.overview
    ? `
      <div class="knowledge-inline-note knowledge-compare-summary">
        <div class="knowledge-doc-selection">
          <strong>${bezpiecznyTekst(changeSummary.overview)}</strong>
          ${changeSummary.impact_label ? `<span class="pill history-pill">${bezpiecznyTekst(changeSummary.impact_label)}</span>` : ""}
        </div>
        ${
          Array.isArray(changeSummary.key_changes) && changeSummary.key_changes.length
            ? `<ul class="knowledge-summary-list">${changeSummary.key_changes
                .map((item) => `<li>${bezpiecznyTekst(item)}</li>`)
                .join("")}</ul>`
            : ""
        }
        ${
          (changeSummary.added_topics || []).length || (changeSummary.removed_topics || []).length
            ? `<div class="knowledge-audit-highlights">
                ${(changeSummary.added_topics || []).map((item) => `<span class="pill history-pill">nowe: ${bezpiecznyTekst(item)}</span>`).join("")}
                ${(changeSummary.removed_topics || []).map((item) => `<span class="pill history-pill">starsza: ${bezpiecznyTekst(item)}</span>`).join("")}
              </div>`
            : ""
        }
      </div>
    `
    : "";

  const blockMarkup = blocks
    .map((block) => {
      const prefix = block.type === "added" ? "+" : block.type === "removed" ? "-" : " ";
      const collapsed = Number(block.collapsed_line_count || 0);
      return `
        <article class="knowledge-diff-block ${block.type === "added" ? "is-added" : block.type === "removed" ? "is-removed" : "is-context"}">
          <div class="knowledge-preview-meta">
            <span>${block.type === "added" ? `Nowe w v${bezpiecznyTekst(targetVersionNumber)}` : block.type === "removed" ? `Tylko w v${bezpiecznyTekst(baseVersionNumber)}` : "Kontekst"}</span>
            <span>linie: ${bezpiecznyTekst(block.line_count || 0)}</span>
            ${collapsed ? `<span>ukryto: ${bezpiecznyTekst(collapsed)}</span>` : ""}
          </div>
          <pre class="knowledge-diff-lines">${(block.lines || []).map((line) => `${prefix} ${bezpiecznyTekst(line)}`).join("\n")}</pre>
        </article>
      `;
    })
    .join("");
  const compareViewSwitchMarkup = `
    <div class="knowledge-documents-view-switch knowledge-compare-view-switch">
      <button type="button" class="secondary ${stan.widokPorownaniaWersjiBazyWiedzy === "blocks" ? "is-active" : ""}" data-knowledge-compare-view="blocks">Zmiany</button>
      <button type="button" class="secondary ${stan.widokPorownaniaWersjiBazyWiedzy === "side_by_side" ? "is-active" : ""}" data-knowledge-compare-view="side_by_side">Obok siebie</button>
    </div>
  `;
  const compareBodyMarkup =
    stan.widokPorownaniaWersjiBazyWiedzy === "side_by_side"
      ? zbudujPanelObokSiebiePorownaniaBazyWiedzy(compareState)
      : blockMarkup || '<div class="empty-state">Brak roznic tekstowych miedzy tymi wersjami.</div>';

  return `
    ${changeSummaryMarkup}
    <div class="knowledge-audit-highlights">
      <span class="pill history-pill">${bezpiecznyTekst(compareState.compare_label || "Porownanie wersji")}</span>
      <span class="pill history-pill">nowe w nowszej: ${bezpiecznyTekst(summary.added_line_count || 0)}</span>
      <span class="pill history-pill">tylko w starszej: ${bezpiecznyTekst(summary.removed_line_count || 0)}</span>
      <span class="pill history-pill">bloki zmian: ${bezpiecznyTekst(summary.changed_block_count || 0)}</span>
      <span class="pill history-pill">podobienstwo: ${bezpiecznyTekst(`${Math.round(Number(summary.similarity_ratio || 0) * 100)}%`)}</span>
      ${summary.truncated_block_count ? `<span class="pill history-pill">ukryte bloki: ${bezpiecznyTekst(summary.truncated_block_count)}</span>` : ""}
    </div>
    <div class="knowledge-preview-meta">
      <span>Nowsza: v${bezpiecznyTekst(compareState.target_version?.version_number || compareState.left_version?.version_number || "?")} (${formatujDateCzas(compareState.target_version?.created_at || compareState.left_version?.created_at)})</span>
      <span>Starsza: v${bezpiecznyTekst(compareState.base_version?.version_number || compareState.right_version?.version_number || "?")} (${formatujDateCzas(compareState.base_version?.created_at || compareState.right_version?.created_at)})</span>
    </div>
    ${compareViewSwitchMarkup}
    ${compareBodyMarkup}
  `;
}

function zbudujPanelAktywnosciBazyWiedzy(feed, summary) {
  const items = Array.isArray(feed) ? feed : [];
  const activitySummary = summary || {};
  const itemMarkup = items.length
    ? items
        .map(
          (item) => `
            <article class="knowledge-version-item knowledge-activity-item ${item.is_unread ? "is-unread" : ""}">
              <div class="knowledge-doc-selection">
                <div>
                  <strong>${bezpiecznyTekst(item.document_title || item.action_label || "Aktywnosc dokumentu")}</strong>
                  <div class="knowledge-preview-meta">
                    <span>${bezpiecznyTekst(item.action_label || "Zdarzenie")}</span>
                    <span>${formatujDateCzas(item.event_time)}</span>
                    <span>${bezpiecznyTekst(item.actor || "system")}</span>
                    ${item.business_status_label ? `<span>${bezpiecznyTekst(item.business_status_label)}</span>` : ""}
                    ${item.workflow_status_label ? `<span>${bezpiecznyTekst(item.workflow_status_label)}</span>` : ""}
                  </div>
                </div>
                <div class="filters-actions">
                  ${item.is_unread ? '<span class="pill history-pill">nowe</span>' : ""}
                  ${item.knowledge_document_id ? `<button type="button" class="secondary" data-knowledge-open-activity-document="${bezpiecznyTekst(item.knowledge_document_id)}">Otworz dokument</button>` : ""}
                </div>
              </div>
              <p class="knowledge-audit-message">${bezpiecznyTekst(item.message || "Brak opisu zdarzenia.")}</p>
              ${
                Array.isArray(item.highlights) && item.highlights.length
                  ? `<div class="knowledge-audit-highlights">${item.highlights.map((highlight) => `<span class="pill history-pill">${bezpiecznyTekst(highlight.label)}: ${bezpiecznyTekst(highlight.value)}</span>`).join("")}</div>`
                  : ""
              }
            </article>
          `
        )
        .join("")
    : '<div class="empty-state">Brak nowych aktywnosci dokumentowych. Gdy ktos doda komentarz albo oznaczy nowa wersje jako obowiazujaca, zobaczysz to tutaj.</div>';
  return `
    <section class="knowledge-activity-panel">
      <div class="knowledge-doc-selection">
        <div>
          <strong>Aktywnosci i workflow</strong>
          <div class="subtle-note">To jest operacyjny feed zmian: komentarze, adnotacje, oznaczenia wersji obowiazujacej i ruch wokol dokumentow wymagajacych decyzji.</div>
        </div>
        <div class="filters-actions">
          <button type="button" class="secondary" data-knowledge-mark-activity-seen ${activitySummary.unread_count ? "" : "disabled"}>Oznacz jako przeczytane</button>
        </div>
      </div>
      <div class="knowledge-audit-highlights">
        <span class="pill history-pill">nieprzeczytane: ${bezpiecznyTekst(activitySummary.unread_count || 0)}</span>
        <span class="pill history-pill">wymaga decyzji: ${bezpiecznyTekst(activitySummary.pending_decision_count || 0)}</span>
        <span class="pill history-pill">do sprawdzenia: ${bezpiecznyTekst(activitySummary.awaiting_review_count || 0)}</span>
        <span class="pill history-pill">do akceptacji: ${bezpiecznyTekst(activitySummary.awaiting_approval_count || 0)}</span>
        <span class="pill history-pill">moja kolejka: ${bezpiecznyTekst(activitySummary.my_attention_count || 0)}</span>
        <span class="pill history-pill">stabilne: ${bezpiecznyTekst(activitySummary.stable_count || 0)}</span>
      </div>
      ${itemMarkup}
    </section>
  `;
}

function zbudujPanelAkcjiMasowychBazyWiedzy(documents) {
  if (!czyMoznaZarzadzacPrzetwarzaniemBazyWiedzy() || stan.widokBazyWiedzy !== "documents" || !(documents || []).length) return "";
  const selectedIds = pobierzZaznaczoneIdDokumentowBazyWiedzy();
  const selectedCount = selectedIds.length;
  const allSelected = selectedCount > 0 && selectedCount === documents.length;
  const busy = Boolean(stan.trwaAkcjaMasowaBazyWiedzy);
  const lastResult = stan.ostatniWynikAkcjiMasowejBazyWiedzy;
  const lastResultMarkup = lastResult
    ? `
      <div class="knowledge-bulk-summary">
        <div class="knowledge-audit-highlights">
          <span class="pill history-pill">${bezpiecznyTekst(lastResult.action_label || "Akcja masowa")}</span>
          <span class="pill history-pill">sukces: ${bezpiecznyTekst(lastResult.succeeded_count || 0)}</span>
          <span class="pill history-pill">pominiete: ${bezpiecznyTekst(lastResult.skipped_count || 0)}</span>
          <span class="pill history-pill">bledy: ${bezpiecznyTekst(lastResult.failed_count || 0)}</span>
        </div>
        ${
          Array.isArray(lastResult.failed) && lastResult.failed.length
            ? `<div class="knowledge-inline-note knowledge-bulk-failures">${lastResult.failed
                .slice(0, 4)
                .map((item) => `<div><strong>${bezpiecznyTekst(item.title || `#${item.knowledge_document_id || "?"}`)}</strong>: ${bezpiecznyTekst(item.message || "Nie udalo sie wykonac akcji.")}</div>`)
                .join("")}</div>`
            : ""
        }
      </div>
    `
    : "";
  return `
    <section class="knowledge-bulk-toolbar">
      <div class="knowledge-doc-selection">
        <div>
          <strong>Akcje masowe dla widocznych dokumentow</strong>
          <div class="subtle-note">Zaznaczone: ${bezpiecznyTekst(selectedCount)} z ${bezpiecznyTekst(documents.length)} widocznych pozycji. Zmiana filtrow automatycznie zaweza zaznaczenie do aktualnego widoku.</div>
        </div>
        <div class="filters-actions">
          <button type="button" class="secondary" data-knowledge-bulk-toggle-visible ${busy ? "disabled" : ""}>${allSelected ? "Odznacz widoczne" : "Zaznacz widoczne"}</button>
          <button type="button" class="secondary" data-knowledge-bulk-clear ${busy || !selectedCount ? "disabled" : ""}>Wyczysc zaznaczenie</button>
        </div>
      </div>
      <div class="knowledge-action-grid">
        <button type="button" class="secondary" data-knowledge-bulk-action="archive" ${busy || !selectedCount ? "disabled" : ""}>Zarchiwizuj</button>
        <button type="button" class="secondary" data-knowledge-bulk-action="restore" ${busy || !selectedCount ? "disabled" : ""}>Przywroc</button>
        <button type="button" class="secondary" data-knowledge-bulk-action="set_downloadable" data-knowledge-bulk-enabled="true" ${busy || !selectedCount ? "disabled" : ""}>Pokaz w bibliotece</button>
        <button type="button" class="secondary" data-knowledge-bulk-action="set_downloadable" data-knowledge-bulk-enabled="false" ${busy || !selectedCount ? "disabled" : ""}>Ukryj z biblioteki</button>
        <button type="button" class="secondary" data-knowledge-bulk-action="set_assistant_usage" data-knowledge-bulk-enabled="true" ${busy || !selectedCount ? "disabled" : ""}>Wlacz w asystencie</button>
        <button type="button" class="secondary" data-knowledge-bulk-action="set_assistant_usage" data-knowledge-bulk-enabled="false" ${busy || !selectedCount ? "disabled" : ""}>Wylacz w asystencie</button>
      </div>
      <div class="field-grid">
        <div class="field">
          <label>Folder docelowy</label>
          <input type="text" data-knowledge-bulk-folder value="${bezpiecznyTekst(stan.folderMasowyBazyWiedzy || "")}" placeholder="np. Wzory/HR" ${busy ? "disabled" : ""} />
        </div>
        <div class="field">
          <label>&nbsp;</label>
          <button type="button" class="secondary" data-knowledge-bulk-move-folder ${busy || !selectedCount ? "disabled" : ""}>Przenies do folderu</button>
        </div>
      </div>
      ${lastResultMarkup}
    </section>
  `;
}

function zbudujPillsWatcheraBazyWiedzy(watchStatus) {
  const status = watchStatus || {};
  if (!status.enabled) return '<span class="pill history-pill">watcher: wylaczony</span>';
  return [
    `watcher: ${status.watch_mode || "polling"}`,
    `scan: ${status.last_scan_status || "idle"}`,
    `nowe: ${status.queued_new || 0}`,
    `aktualizacje: ${status.queued_updates || 0}`,
    `duplikaty: ${status.duplicate_count || 0}`,
    `podobne: ${status.similar_count || 0}`,
  ]
    .map((item) => `<span class="pill history-pill">${bezpiecznyTekst(item)}</span>`)
    .join("");
}

function zbudujKarteDokumentuBazyWiedzy(dokument) {
  const extension = String(dokument.file_name || "").includes(".") ? String(dokument.file_name).split(".").pop().toUpperCase() : "";
  const createdBy = dokument.created_by_display_name || dokument.created_by_login;
  const isSelected = Number(dokument.knowledge_document_id) === Number(stan.wybranyDokumentWiedzyId);
  const isBulkSelectable = czyMoznaZarzadzacPrzetwarzaniemBazyWiedzy() && stan.widokBazyWiedzy === "documents";
  const isBulkSelected = isBulkSelectable && czyDokumentBazyWiedzyJestZaznaczony(dokument.knowledge_document_id);
  const retryButton = czyMoznaZarzadzacPrzetwarzaniemBazyWiedzy()
    ? `<button type="button" class="secondary" data-knowledge-retry-id="${dokument.knowledge_document_id}">Ponow przetwarzanie</button>`
    : "";
  const downloadLink =
    czyMoznaPobieracPlikiFirmowe() &&
    dokument.is_downloadable &&
    String(dokument.lifecycle_status || "active") !== "deleted"
      ? `<a href="${bezpiecznyTekst(pobierzAdresPobraniaDokumentuBazyWiedzy(dokument))}" target="_blank" rel="noreferrer">Pobierz</a>`
      : "";
  const duplicateLabel = formatujStatusDuplikatuBazyWiedzy(dokument.duplicate_status || "none");
  return `
    <article class="list-item knowledge-doc-item ${isSelected ? "is-selected" : ""} ${isBulkSelected ? "is-bulk-selected" : ""}" data-knowledge-select-id="${dokument.knowledge_document_id}">
      <div class="knowledge-doc-header">
        <div class="knowledge-doc-title-row">
          ${
            isBulkSelectable
              ? `<label class="knowledge-select-toggle"><input type="checkbox" data-knowledge-select-checkbox="${dokument.knowledge_document_id}" aria-label="Zaznacz dokument ${bezpiecznyTekst(dokument.title)}" ${isBulkSelected ? "checked" : ""} /></label>`
              : ""
          }
          <div>
          <div class="knowledge-doc-title">${bezpiecznyTekst(dokument.title)}</div>
          <div class="knowledge-doc-badges">
            <span class="status-badge ${klasaStanuObieguDokumentuBazyWiedzy(dokument.business_status || "roboczy")}">${bezpiecznyTekst(formatujStanObieguDokumentuBazyWiedzy(dokument.business_status || "roboczy"))}</span>
            <span class="status-badge ${klasaLifecycleDokumentuBazyWiedzy(dokument.lifecycle_status || "active")}">${bezpiecznyTekst(formatujLifecycleDokumentuBazyWiedzy(dokument.lifecycle_status || "active"))}</span>
            <span class="status-badge ${klasaStatusuPrzetwarzaniaBazyWiedzy(dokument.processing_status || "queued")}">${bezpiecznyTekst(formatujStatusPrzetwarzaniaBazyWiedzy(dokument.processing_status || "queued"))}</span>
            <span class="status-badge ${klasaStatusuZrodlaBazyWiedzy(dokument.source_type || "manual")}">${bezpiecznyTekst(formatujZrodloBazyWiedzy(dokument.source_type || "manual"))}</span>
            ${extension ? `<span class="pill knowledge-doc-pill">${bezpiecznyTekst(extension)}</span>` : ""}
            <span class="pill history-pill">v${bezpiecznyTekst(dokument.current_version_number || 0)}</span>
            ${Number(dokument.official_version_number || 0) ? `<span class="pill history-pill">obowiazuje v${bezpiecznyTekst(dokument.official_version_number)}</span>` : ""}
            ${
              dokument.workflow_status && !["stable", "archived", "deleted"].includes(String(dokument.workflow_status))
                ? `<span class="pill history-pill">${bezpiecznyTekst(dokument.workflow_status_label || dokument.workflow_status)}</span>`
                : ""
            }
            ${dokument.use_in_assistant ? '<span class="pill history-pill">Asystent</span>' : ""}
            ${dokument.is_downloadable ? '<span class="pill history-pill">Biblioteka</span>' : '<span class="pill history-pill">Tylko AI</span>'}
            ${duplicateLabel ? `<span class="pill history-pill">${bezpiecznyTekst(duplicateLabel)}</span>` : ""}
          </div>
        </div>
        </div>
        <div class="filters-actions">
          <button type="button" class="secondary" data-knowledge-open-id="${dokument.knowledge_document_id}">Podglad</button>
          ${downloadLink}
          ${retryButton}
        </div>
      </div>
      <div>${bezpiecznyTekst(dokument.snippet || "Brak podgladu tresci.")}</div>
      ${dokument.processing_error ? `<div class="knowledge-error-note">${bezpiecznyTekst(dokument.processing_error)}</div>` : ""}
      ${dokument.duplicate_reason ? `<div class="knowledge-inline-note">${bezpiecznyTekst(dokument.duplicate_reason)}</div>` : ""}
      ${zbudujPiguIPrzypisaniaDokumentuBazyWiedzy(dokument)}
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
      if (event.target?.closest?.("[data-knowledge-retry-id], [data-knowledge-open-id], [data-knowledge-select-checkbox], [data-knowledge-bulk-action], [data-knowledge-bulk-toggle-visible], [data-knowledge-bulk-clear], [data-knowledge-bulk-move-folder], a, input, label")) return;
      ustawWybranyDokumentBazyWiedzy(element.dataset.knowledgeSelectId);
    });
  });
  container.querySelectorAll("[data-knowledge-select-checkbox]").forEach((input) => {
    input.addEventListener("click", (event) => event.stopPropagation());
    input.addEventListener("change", () => {
      ustawZaznaczenieDokumentuBazyWiedzy(input.dataset.knowledgeSelectCheckbox, Boolean(input.checked));
      odswiezWidokBazyWiedzyZPamieci();
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
        await api(zbudujAdresZOrganizacja(`/api/knowledge/documents/${button.dataset.knowledgeRetryId}/reprocess`), { method: "POST" });
        pokazPowiadomienie("Dokument dodany ponownie do kolejki.");
        await Promise.all([wczytajBazeWiedzy(), wczytajLogi()]);
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
    });
  });
  container.querySelector("[data-knowledge-bulk-toggle-visible]")?.addEventListener("click", () => {
    const visibleDocumentIds = Array.from(container.querySelectorAll("[data-knowledge-select-checkbox]")).map((input) => Number(input.dataset.knowledgeSelectCheckbox));
    const allSelected = visibleDocumentIds.length > 0 && visibleDocumentIds.every((documentId) => czyDokumentBazyWiedzyJestZaznaczony(documentId));
    ustawZaznaczoneDokumentyBazyWiedzy(allSelected ? [] : visibleDocumentIds);
    odswiezWidokBazyWiedzyZPamieci();
  });
  container.querySelector("[data-knowledge-bulk-clear]")?.addEventListener("click", () => {
    ustawZaznaczoneDokumentyBazyWiedzy([]);
    odswiezWidokBazyWiedzyZPamieci();
  });
  container.querySelector("[data-knowledge-bulk-folder]")?.addEventListener("input", (event) => {
    stan.folderMasowyBazyWiedzy = event.currentTarget.value || "";
  });
  container.querySelectorAll("[data-knowledge-bulk-action]").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        await wykonajMasowaAkcjeDokumentowBazyWiedzy(button.dataset.knowledgeBulkAction, {
          enabled: button.dataset.knowledgeBulkEnabled,
        });
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
    });
  });
  container.querySelector("[data-knowledge-bulk-move-folder]")?.addEventListener("click", async () => {
    try {
      const folderValue = container.querySelector("[data-knowledge-bulk-folder]")?.value || stan.folderMasowyBazyWiedzy || "";
      stan.folderMasowyBazyWiedzy = folderValue;
      await wykonajMasowaAkcjeDokumentowBazyWiedzy("move_folder", { library_path: folderValue });
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  container.querySelector("[data-knowledge-mark-activity-seen]")?.addEventListener("click", async () => {
    try {
      await oznaczAktywnoscBazyWiedzyJakoPrzeczytana();
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  container.querySelectorAll("[data-knowledge-open-activity-document]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      ustawWybranyDokumentBazyWiedzy(button.dataset.knowledgeOpenActivityDocument);
    });
  });
}

async function wykonajAkcjeDokumentuBazyWiedzy(id, suffix, options, message, confirmMessage) {
  if (confirmMessage && !window.confirm(confirmMessage)) return;
  await api(zbudujAdresZOrganizacja(`/api/knowledge/documents/${id}${suffix}`), options);
  pokazPowiadomienie(message);
  await Promise.all([wczytajBazeWiedzy(), wczytajLogi()]);
}

async function wykonajMasowaAkcjeDokumentowBazyWiedzy(action, options = {}) {
  if (!czyMoznaZarzadzacPrzetwarzaniemBazyWiedzy()) return pokazPowiadomienie("To konto nie moze wykonywac akcji masowych na dokumentach.");
  const selectedIds = pobierzZaznaczoneIdDokumentowBazyWiedzy();
  if (!selectedIds.length) return pokazPowiadomienie("Najpierw zaznacz dokumenty, na ktorych chcesz pracowac.");
  const normalizedAction = String(action || "");
  if (normalizedAction === "move_folder" && !String(options.library_path || "").trim()) {
    return pokazPowiadomienie("Podaj folder docelowy dla zaznaczonych dokumentow.");
  }
  const confirmMessage =
    normalizedAction === "archive"
      ? `Zarchiwizowac ${selectedIds.length} dokumentow?`
      : normalizedAction === "restore"
        ? `Przywrocic ${selectedIds.length} dokumentow do aktywnego obiegu?`
        : "";
  if (confirmMessage && !window.confirm(confirmMessage)) return;

  stan.trwaAkcjaMasowaBazyWiedzy = true;
  stan.ostatniWynikAkcjiMasowejBazyWiedzy = null;
  odswiezWidokBazyWiedzyZPamieci();
  try {
    const result = await api(zbudujAdresZOrganizacja("/api/knowledge/documents/bulk"), {
      method: "POST",
      body: JSON.stringify({
        action: normalizedAction,
        knowledge_document_ids: selectedIds,
        library_path: options.library_path,
        enabled:
          typeof options.enabled === "string"
            ? options.enabled === "true"
            : typeof options.enabled === "boolean"
              ? options.enabled
              : undefined,
      }),
    });
    stan.ostatniWynikAkcjiMasowejBazyWiedzy = result;
    ustawZaznaczoneDokumentyBazyWiedzy((result.failed || []).map((item) => Number(item.knowledge_document_id || 0)).filter((value) => value > 0));
    const message = `Akcja masowa: ${result.action_label || normalizedAction}. Sukces: ${result.succeeded_count || 0}, pominiete: ${result.skipped_count || 0}, bledy: ${result.failed_count || 0}.`;
    pokazPowiadomienie(message);
    await Promise.all([wczytajBazeWiedzy(), wczytajLogi()]);
  } finally {
    stan.trwaAkcjaMasowaBazyWiedzy = false;
    odswiezWidokBazyWiedzyZPamieci();
  }
}

async function podmienPlikDokumentuBazyWiedzy(id, input) {
  const file = input?.files?.[0];
  if (!file) return pokazPowiadomienie("Wybierz nowy plik dokumentu.");
  const formData = new FormData();
  formData.append("file", file);
  await api(zbudujAdresZOrganizacja(`/api/knowledge/documents/${id}/replace`), { method: "POST", body: formData });
  pokazPowiadomienie("Nowa wersja dokumentu trafila do kolejki.");
  input.value = "";
  await Promise.all([wczytajBazeWiedzy(), wczytajLogi()]);
}

async function przywrocWersjeDokumentuBazyWiedzy(id, versionNumber) {
  await api(zbudujAdresZOrganizacja(`/api/knowledge/documents/${id}/restore-version`), {
    method: "POST",
    body: JSON.stringify({ version_number: Number(versionNumber) }),
  });
  pokazPowiadomienie(`Wersja v${versionNumber} trafila do kolejki przywrocenia.`);
  await Promise.all([wczytajBazeWiedzy(), wczytajLogi()]);
}

async function oznaczWersjeDokumentuBazyWiedzyJakoObowiazujaca(id, versionNumber) {
  if (!czyMoznaZarzadzacPrzetwarzaniemBazyWiedzy()) return pokazPowiadomienie("To konto nie moze oznaczac wersji obowiazujacych.");
  await api(zbudujAdresZOrganizacja(`/api/knowledge/documents/${id}/mark-official-version`), {
    method: "POST",
    body: JSON.stringify({ version_number: Number(versionNumber) }),
  });
  pokazPowiadomienie(`Wersja v${versionNumber} zostala oznaczona jako obowiazujaca.`);
  await Promise.all([wczytajBazeWiedzy(), wczytajLogi()]);
}

async function dodajKomentarzDoDokumentuBazyWiedzy(id, scope) {
  if (!czyMoznaCzytacBazeWiedzy()) return pokazPowiadomienie("To konto nie ma dostepu do komentarzy dokumentu.");
  const button = scope.querySelector("[data-knowledge-comment-submit]");
  if (!button) return;
  const noteText = scope.querySelector("[data-knowledge-comment-note]")?.value?.trim() || "";
  if (!noteText) return pokazPowiadomienie("Wpisz tresc komentarza albo adnotacji.");
  button.disabled = true;
  button.classList.add("is-busy");
  try {
    await api(zbudujAdresZOrganizacja(`/api/knowledge/documents/${id}/comments`), {
      method: "POST",
      body: JSON.stringify({
        note_text: noteText,
        version_number: scope.querySelector("[data-knowledge-comment-version]")?.value || "",
        annotation_kind: scope.querySelector("[data-knowledge-comment-kind]")?.value || "comment",
        anchor_label: scope.querySelector("[data-knowledge-comment-anchor]")?.value?.trim() || "",
      }),
    });
    pokazPowiadomienie("Dodano wpis do dokumentu.");
    const noteField = scope.querySelector("[data-knowledge-comment-note]");
    const anchorField = scope.querySelector("[data-knowledge-comment-anchor]");
    if (noteField) noteField.value = "";
    if (anchorField) anchorField.value = "";
    await Promise.all([wczytajBazeWiedzy(), wczytajLogi()]);
  } catch (error) {
    pokazPowiadomienie(error.message);
  } finally {
    button.disabled = false;
    button.classList.remove("is-busy");
  }
}

async function oznaczAktywnoscBazyWiedzyJakoPrzeczytana() {
  if (!czyMoznaCzytacBazeWiedzy()) return;
  await api(zbudujAdresZOrganizacja("/api/knowledge/activity/mark-seen"), {
    method: "POST",
    body: JSON.stringify({}),
  });
  pokazPowiadomienie("Aktywnosc dokumentow zostala oznaczona jako przeczytana.");
  await wczytajBazeWiedzy();
}

function zbudujOpcjeKandydatowPrzypisanBazyWiedzy(selectedUserId, selectedLabel = "") {
  const normalizedSelectedUserId = Number(selectedUserId || 0);
  const candidates = Array.isArray(stan.kandydaciPrzypisanBazyWiedzy) ? stan.kandydaciPrzypisanBazyWiedzy : [];
  const baseOption = '<option value="">nie przypisano</option>';
  const options = candidates
    .map((candidate) => {
      const candidateUserId = Number(candidate.user_id || 0);
      const selected = candidateUserId === normalizedSelectedUserId ? "selected" : "";
      const roleLabel = candidate.membership_role || candidate.role || "";
      const label = roleLabel ? `${candidate.label || candidate.display_name || candidate.login} (${roleLabel})` : candidate.label || candidate.display_name || candidate.login || `uzytkownik #${candidateUserId}`;
      return `<option value="${bezpiecznyTekst(candidateUserId)}" ${selected}>${bezpiecznyTekst(label)}</option>`;
    })
    .join("");
  const hasSelectedCandidate = candidates.some((candidate) => Number(candidate.user_id || 0) === normalizedSelectedUserId);
  const fallbackSelectedOption =
    normalizedSelectedUserId && !hasSelectedCandidate
      ? `<option value="${bezpiecznyTekst(normalizedSelectedUserId)}" selected>${bezpiecznyTekst(selectedLabel || `uzytkownik #${normalizedSelectedUserId}`)}</option>`
      : "";
  return `${baseOption}${fallbackSelectedOption}${options}`;
}

function ustawFokusKolejkiDokumentowFirmowych(bucket) {
  zapewnijStanRozszerzenBazyWiedzy();
  stan.widokBazyWiedzy = "documents";
  stan.widokDokumentowBazyWiedzy = "recent";
  if (bucket === "knowledge_review") {
    stan.filtryBazyWiedzy = { ...(stan.filtryBazyWiedzy || {}), lifecycle: "active", status: "", businessStatus: "do_sprawdzenia", source: "", search: "" };
  } else if (bucket === "knowledge_approval") {
    stan.filtryBazyWiedzy = { ...(stan.filtryBazyWiedzy || {}), lifecycle: "active", status: "", businessStatus: "do_akceptacji", source: "", search: "" };
  } else if (bucket === "knowledge_my_queue") {
    stan.filtryBazyWiedzy = { ...(stan.filtryBazyWiedzy || {}), lifecycle: "active", status: "", businessStatus: "", source: "", search: "" };
  }
  zsynchronizujFiltryBazyWiedzyZFormularzem();
  odswiezWidokBazyWiedzyZPamieci();
}

async function zapiszMetadaneDokumentuBazyWiedzy(id, scope) {
  if (!czyMoznaZarzadzacPrzetwarzaniemBazyWiedzy()) return pokazPowiadomienie("To konto nie moze edytowac ustawien dokumentu.");
  const button = scope.querySelector("[data-knowledge-save-meta]");
  if (!button) return;
  button.disabled = true;
  button.classList.add("is-busy");
  try {
    await api(zbudujAdresZOrganizacja(`/api/knowledge/documents/${id}`), {
      method: "PATCH",
      body: JSON.stringify({
        title: scope.querySelector("[data-knowledge-meta-title]")?.value?.trim() || "",
        library_path: scope.querySelector("[data-knowledge-meta-folder]")?.value?.trim() || "",
        is_downloadable: Boolean(scope.querySelector("[data-knowledge-meta-downloadable]")?.checked),
        use_in_assistant: Boolean(scope.querySelector("[data-knowledge-meta-assistant]")?.checked),
        business_status: scope.querySelector("[data-knowledge-meta-business-status]")?.value || "",
        owner_user_id: scope.querySelector("[data-knowledge-meta-owner]")?.value || null,
        reviewer_user_id: scope.querySelector("[data-knowledge-meta-reviewer]")?.value || null,
        approver_user_id: scope.querySelector("[data-knowledge-meta-approver]")?.value || null,
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
  if (!container || !versionBadge) return;
  zapewnijStanRozszerzenBazyWiedzy();
  const allDocuments = stan.dokumentyWiedzy || [];
  const filteredDocuments = pobierzPrzefiltrowaneDokumentyBazyWiedzy();
  let selectedDocument = pobierzDokumentBazyWiedzy(stan.wybranyDokumentWiedzyId);
  if (!selectedDocument) {
    const fallback = stan.widokBazyWiedzy === "documents" ? filteredDocuments[0] || null : pobierzDokumentyAsystentaBazyWiedzy()[0] || allDocuments[0] || null;
    selectedDocument = fallback;
    stan.wybranyDokumentWiedzyId = fallback ? Number(fallback.knowledge_document_id) : null;
  }
  if (stan.widokBazyWiedzy === "documents" && selectedDocument && !filteredDocuments.some((item) => Number(item.knowledge_document_id) === Number(selectedDocument.knowledge_document_id))) {
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

  const lifecycleStatus = String(selectedDocument.lifecycle_status || "active");
  const canManage = czyMoznaZarzadzacPrzetwarzaniemBazyWiedzy();
  const canUpload = czyMoznaDodawacPlikiDoBazyWiedzy();
  const canDownload = czyMoznaPobieracPlikiFirmowe() && selectedDocument.is_downloadable && lifecycleStatus !== "deleted";
  const canPreviewInlineFile =
    (canDownload || canManage) && lifecycleStatus !== "deleted" && String(selectedDocument.file_preview_kind || "none") !== "none";
  const selectedId = Number(selectedDocument.knowledge_document_id || 0);
  const detailLoading = Boolean(stan.trwaPobieranieSzczegolowDokumentuWiedzy[selectedId]);
  const detailError = stan.bledySzczegolowDokumentuWiedzy[selectedId];
  const auditSummary = selectedDocument.audit_summary || {};
  const commentSummary = selectedDocument.comment_summary || {};
  const createdBy = selectedDocument.created_by_display_name || selectedDocument.created_by_login || "system";
  const officialVersionNumber = Number(selectedDocument.official_version_number || 0);
  const currentVersionNumber = Number(selectedDocument.current_version_number || 0);
  const officialVersionActor =
    selectedDocument.official_version_marked_by_display_name ||
    selectedDocument.official_version_marked_by_login ||
    "";
  const canComment = czyMoznaCzytacBazeWiedzy() && lifecycleStatus !== "deleted";
  const duplicateLabel = formatujStatusDuplikatuBazyWiedzy(selectedDocument.duplicate_status || "none");
  const businessStatus = String(selectedDocument.business_status || "roboczy");
  const canEditBusinessStatus = canManage && lifecycleStatus === "active";
  const assignmentCandidatesLoading = Boolean(stan.trwaWczytywanieKandydatowPrzypisanBazyWiedzy);
  versionBadge.textContent = `v${selectedDocument.current_version_number || 0} | ${formatujStanObieguDokumentuBazyWiedzy(businessStatus)} | ${formatujStatusPrzetwarzaniaBazyWiedzy(selectedDocument.processing_status || "queued")}${officialVersionNumber ? ` | obow. v${officialVersionNumber}` : ""}`;
  container.className = "";
  container.innerHTML = `
    <div class="knowledge-preview-card">
      <div class="knowledge-doc-selection">
        <div>
          <div class="knowledge-doc-title">${bezpiecznyTekst(selectedDocument.title)}</div>
          <div class="knowledge-doc-badges">
            <span class="status-badge ${klasaStanuObieguDokumentuBazyWiedzy(businessStatus)}">${bezpiecznyTekst(formatujStanObieguDokumentuBazyWiedzy(businessStatus))}</span>
            <span class="status-badge ${klasaLifecycleDokumentuBazyWiedzy(lifecycleStatus)}">${bezpiecznyTekst(formatujLifecycleDokumentuBazyWiedzy(lifecycleStatus))}</span>
            <span class="status-badge ${klasaStatusuPrzetwarzaniaBazyWiedzy(selectedDocument.processing_status || "queued")}">${bezpiecznyTekst(formatujStatusPrzetwarzaniaBazyWiedzy(selectedDocument.processing_status || "queued"))}</span>
            <span class="status-badge ${klasaStatusuZrodlaBazyWiedzy(selectedDocument.source_type || "manual")}">${bezpiecznyTekst(formatujZrodloBazyWiedzy(selectedDocument.source_type || "manual"))}</span>
            <span class="pill history-pill">${bezpiecznyTekst(selectedDocument.file_name || "-")}</span>
            ${officialVersionNumber ? `<span class="pill history-pill">Obowiazuje v${bezpiecznyTekst(officialVersionNumber)}</span>` : '<span class="pill history-pill">Brak wersji obowiazujacej</span>'}
            ${currentVersionNumber && officialVersionNumber !== currentVersionNumber ? `<span class="pill history-pill">Najnowsza v${bezpiecznyTekst(currentVersionNumber)}</span>` : ""}
            ${selectedDocument.use_in_assistant ? '<span class="pill history-pill">Asystent</span>' : ""}
            ${selectedDocument.is_downloadable ? '<span class="pill history-pill">Biblioteka</span>' : '<span class="pill history-pill">Tylko AI</span>'}
            ${duplicateLabel ? `<span class="pill history-pill">${bezpiecznyTekst(duplicateLabel)}</span>` : ""}
          </div>
        </div>
        <div class="filters-actions">
          ${canDownload ? `<a href="${bezpiecznyTekst(pobierzAdresPobraniaDokumentuBazyWiedzy(selectedDocument))}" target="_blank" rel="noreferrer">Pobierz</a>` : ""}
          ${canManage ? `<button type="button" class="secondary" data-knowledge-preview-retry="${selectedDocument.knowledge_document_id}">Ponow przetwarzanie</button>` : ""}
        </div>
      </div>
      <div class="knowledge-preview-meta">
        <span>Folder: ${bezpiecznyTekst(selectedDocument.library_path_label || "Bez folderu")}</span>
        <span>Znaki: ${bezpiecznyTekst(selectedDocument.char_count || 0)}</span>
        <span>Dodane przez: ${bezpiecznyTekst(createdBy)}</span>
        <span>Ostatnie przetworzenie: ${formatujDateCzas(selectedDocument.last_processed_at || selectedDocument.updated_at)}</span>
        ${officialVersionNumber ? `<span>Wersja obowiazujaca: v${bezpiecznyTekst(officialVersionNumber)}</span>` : ""}
        ${selectedDocument.official_version_marked_at ? `<span>Oznaczono: ${formatujDateCzas(selectedDocument.official_version_marked_at)}</span>` : ""}
        ${officialVersionActor ? `<span>Oznaczyl: ${bezpiecznyTekst(officialVersionActor)}</span>` : ""}
        ${auditSummary.last_download_at ? `<span>Ostatnie pobranie: ${formatujDateCzas(auditSummary.last_download_at)}</span>` : ""}
        ${selectedDocument.archived_at ? `<span>Archiwizacja: ${formatujDateCzas(selectedDocument.archived_at)}</span>` : ""}
        ${selectedDocument.deleted_at ? `<span>Usuniecie: ${formatujDateCzas(selectedDocument.deleted_at)}</span>` : ""}
      </div>
      ${zbudujPiguIPrzypisaniaDokumentuBazyWiedzy(selectedDocument)}
      ${lifecycleStatus !== "active" ? `<div class="knowledge-inline-note">${lifecycleStatus === "archived" ? "Ten dokument jest archiwalny. Pozostaje w historii i bibliotece, ale nie powinien byc glownym zrodlem pracy operacyjnej." : "Ten dokument jest usuniety logicznie. Menedzer moze go przywrocic, ale nie jest dostepny do pobrania przez zwyklych uzytkownikow."}</div>` : ""}
      ${
        currentVersionNumber && officialVersionNumber && currentVersionNumber !== officialVersionNumber
          ? `<div class="knowledge-inline-note">Najnowsza wersja dokumentu to v${bezpiecznyTekst(currentVersionNumber)}, ale w obiegu nadal obowiazuje v${bezpiecznyTekst(officialVersionNumber)}. To celowe rozdzielenie: nowe pliki moga byc juz w systemie, ale nie musza jeszcze byc oficjalnie zatwierdzone do pracy.</div>`
          : ""
      }
      ${
        currentVersionNumber && !officialVersionNumber
          ? `<div class="knowledge-inline-note">Dokument ma juz zapisane wersje, ale zadna nie zostala oznaczona jako obowiazujaca. Warto zrobic to po weryfikacji, zeby pracownicy wiedzieli, na czym pracowac.</div>`
          : ""
      }
      ${selectedDocument.duplicate_reason ? `<div class="knowledge-inline-note">${bezpiecznyTekst(selectedDocument.duplicate_reason)}</div>` : ""}
      ${zbudujPanelOperacyjnyDokumentuBazyWiedzy(selectedDocument)}
      ${detailLoading ? `<div class="knowledge-inline-note">Dociagam pelna historie dokumentu, audyt i dodatkowe metadane dla tego podgladu.</div>` : ""}
      ${assignmentCandidatesLoading && canManage ? `<div class="knowledge-inline-note">Wczytuje liste osob odpowiedzialnych dla tej organizacji.</div>` : ""}
      <div class="knowledge-preview-main">${bezpiecznyTekst(selectedDocument.content_preview || selectedDocument.snippet || "Dokument jest jeszcze przetwarzany.")}</div>
      ${selectedDocument.processing_error ? `<div class="knowledge-error-note">${bezpiecznyTekst(selectedDocument.processing_error)}</div>` : ""}
      ${zbudujPanelInlinePreviewDokumentuBazyWiedzy(selectedDocument, { canPreviewFile: canPreviewInlineFile })}
      ${canUpload || canManage ? `<div class="knowledge-action-panel"><strong>Cykl zycia i operacje na pliku</strong><div class="knowledge-action-grid">${canUpload && lifecycleStatus !== "deleted" ? `<label class="secondary knowledge-inline-upload"><span>Podmien plik</span><input type="file" data-knowledge-replace-input accept="${bezpiecznyTekst(document.getElementById("knowledge-file")?.getAttribute("accept") || "")}" /></label>` : ""}${canManage && lifecycleStatus === "active" ? `<button type="button" class="secondary" data-knowledge-archive-document>Zarchiwizuj</button>` : ""}${canManage && lifecycleStatus !== "active" ? `<button type="button" class="secondary" data-knowledge-restore-document>Przywroc dokument</button>` : ""}${canManage && lifecycleStatus !== "deleted" ? `<button type="button" class="secondary" data-knowledge-delete-document>Usun logicznie</button>` : ""}</div><p class="subtle-note">Pobrania trafiaja do logow audytowych, a podmiana pliku lub przywrocenie wersji zawsze zapisuje nowa operacje w historii dokumentu.</p></div>` : ""}
      ${canManage ? `<div class="knowledge-metadata-editor"><strong>Ustawienia dokumentu</strong><div class="field-grid"><div class="field"><label>Tytul</label><input type="text" data-knowledge-meta-title value="${bezpiecznyTekst(selectedDocument.title)}" /></div><div class="field"><label>Folder</label><input type="text" data-knowledge-meta-folder value="${bezpiecznyTekst(selectedDocument.library_path || "")}" placeholder="np. Wzory/HR" /></div><div class="field"><label>Stan dokumentu</label><select data-knowledge-meta-business-status ${canEditBusinessStatus ? "" : "disabled"}><option value="roboczy" ${businessStatus === "roboczy" ? "selected" : ""}>roboczy</option><option value="do_sprawdzenia" ${businessStatus === "do_sprawdzenia" ? "selected" : ""}>do sprawdzenia</option><option value="do_akceptacji" ${businessStatus === "do_akceptacji" ? "selected" : ""}>do akceptacji</option><option value="obowiazujacy" ${businessStatus === "obowiazujacy" ? "selected" : ""}>obowiazujacy</option><option value="archiwalny" ${businessStatus === "archiwalny" ? "selected" : ""}>archiwalny</option></select></div><div class="field"><label>Prowadzi</label><select data-knowledge-meta-owner>${zbudujOpcjeKandydatowPrzypisanBazyWiedzy(selectedDocument.owner_user_id)}</select></div><div class="field"><label>Sprawdza</label><select data-knowledge-meta-reviewer>${zbudujOpcjeKandydatowPrzypisanBazyWiedzy(selectedDocument.reviewer_user_id)}</select></div><div class="field"><label>Akceptuje</label><select data-knowledge-meta-approver>${zbudujOpcjeKandydatowPrzypisanBazyWiedzy(selectedDocument.approver_user_id)}</select></div><div class="field field-full"><div class="knowledge-option-grid"><label class="checkbox-row"><input type="checkbox" data-knowledge-meta-downloadable ${selectedDocument.is_downloadable ? "checked" : ""} /><span>Pokazuj w bibliotece plikow i w wyszukiwarce</span></label><label class="checkbox-row"><input type="checkbox" data-knowledge-meta-assistant ${selectedDocument.use_in_assistant ? "checked" : ""} /><span>Uzywaj w odpowiedziach asystenta</span></label></div></div></div><p class="subtle-note">${canEditBusinessStatus ? "Stan obiegu opisuje realna prace nad dokumentem. Archiwizacja nadal pozostaje osobna operacja systemowa." : "Stan obiegu dla dokumentu archiwalnego lub usunietego zmienisz dopiero po jego przywroceniu do aktywnego obiegu."}</p><div class="filters-actions"><button type="button" class="secondary" data-knowledge-save-meta>Zapisz ustawienia dokumentu</button></div></div>` : ""}
      <div class="knowledge-preview-versions">
        <strong>Komentarze i adnotacje</strong>
        <div class="knowledge-audit-highlights">
          <span class="pill history-pill">wpisy: ${bezpiecznyTekst(commentSummary.comment_count || 0)}</span>
          <span class="pill history-pill">dla dokumentu: ${bezpiecznyTekst(commentSummary.document_comment_count || 0)}</span>
          <span class="pill history-pill">dla wersji: ${bezpiecznyTekst(commentSummary.version_comment_count || 0)}</span>
          ${commentSummary.last_comment_author ? `<span class="pill history-pill">ostatni autor: ${bezpiecznyTekst(commentSummary.last_comment_author)}</span>` : ""}
        </div>
        ${
          canComment
            ? `<div class="knowledge-comment-composer"><div class="field-grid"><div class="field"><label>Typ wpisu</label><select data-knowledge-comment-kind><option value="comment">Komentarz</option><option value="annotation">Adnotacja</option></select></div><div class="field"><label>Dotyczy</label><select data-knowledge-comment-version>${zbudujOpcjeKomentarzaDokumentuBazyWiedzy(selectedDocument)}</select></div><div class="field field-full"><label>Sekcja / zakres</label><input type="text" data-knowledge-comment-anchor placeholder="np. paragraf 4, sekcja rabaty, wzor do podpisu" /></div><div class="field field-full"><label>Tresc</label><textarea data-knowledge-comment-note rows="4" placeholder="Zostaw komentarz dla zespolu albo adnotacje do konkretnej wersji dokumentu."></textarea></div></div><div class="filters-actions"><button type="button" class="secondary" data-knowledge-comment-submit>Dodaj wpis</button></div></div>`
            : ""
        }
        ${zbudujKomentarzeDokumentuBazyWiedzy(selectedDocument, { loading: detailLoading, error: detailError })}
      </div>
      <div class="knowledge-preview-versions">
        <strong>Historia i audyt</strong>
        <div class="knowledge-audit-highlights">
          <span class="pill history-pill">zdarzenia: ${bezpiecznyTekst(auditSummary.event_count || 0)}</span>
          <span class="pill history-pill">zmiany: ${bezpiecznyTekst(auditSummary.change_count || 0)}</span>
          <span class="pill history-pill">pobrania: ${bezpiecznyTekst(auditSummary.download_count || 0)}</span>
          ${auditSummary.last_actor ? `<span class="pill history-pill">ostatni aktor: ${bezpiecznyTekst(auditSummary.last_actor)}</span>` : ""}
        </div>
        ${zbudujHistorieAudytuBazyWiedzy(selectedDocument, { loading: detailLoading, error: detailError })}
      </div>
      <div class="knowledge-preview-versions"><strong>Historia wersji</strong>${zbudujWersjeDokumentuBazyWiedzy(selectedDocument)}</div>
      <div class="knowledge-preview-versions"><strong>Porownanie wersji</strong>${zbudujPanelPorownaniaWersjiBazyWiedzy(selectedDocument)}</div>
      <div class="knowledge-preview-versions"><strong>Kolejka i zadania przetwarzania</strong>${zbudujZadaniaPrzetwarzaniaBazyWiedzy(selectedDocument)}</div>
    </div>
  `;
  if (canManage && !assignmentCandidatesLoading && !stan.kandydaciPrzypisanBazyWiedzy.length && czyModulWiedzyMaZakres()) {
    wczytajKandydatowPrzypisanDokumentowBazyWiedzy().then(() => renderujPodgladDokumentuBazyWiedzy()).catch(() => {});
  }
  if (lifecycleStatus === "deleted") {
    container.querySelectorAll("[data-knowledge-meta-title], [data-knowledge-meta-folder], [data-knowledge-meta-business-status], [data-knowledge-meta-owner], [data-knowledge-meta-reviewer], [data-knowledge-meta-approver], [data-knowledge-meta-downloadable], [data-knowledge-meta-assistant], [data-knowledge-save-meta]").forEach((element) => {
      element.disabled = true;
    });
  }

  container.querySelector("[data-knowledge-preview-retry]")?.addEventListener("click", async () => {
    try {
      await api(zbudujAdresZOrganizacja(`/api/knowledge/documents/${selectedDocument.knowledge_document_id}/reprocess`), { method: "POST" });
      pokazPowiadomienie("Dokument dodany ponownie do kolejki.");
      await Promise.all([wczytajBazeWiedzy(), wczytajLogi()]);
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  container.querySelector("[data-knowledge-save-meta]")?.addEventListener("click", async () => zapiszMetadaneDokumentuBazyWiedzy(selectedDocument.knowledge_document_id, container));
  container.querySelector("[data-knowledge-comment-submit]")?.addEventListener("click", async () => {
    try {
      await dodajKomentarzDoDokumentuBazyWiedzy(selectedDocument.knowledge_document_id, container);
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  container.querySelector("[data-knowledge-replace-input]")?.addEventListener("change", async (event) => {
    try {
      await podmienPlikDokumentuBazyWiedzy(selectedDocument.knowledge_document_id, event.currentTarget);
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  container.querySelector("[data-knowledge-archive-document]")?.addEventListener("click", async () => {
    try {
      await wykonajAkcjeDokumentuBazyWiedzy(selectedDocument.knowledge_document_id, "/archive", { method: "POST" }, "Dokument zostal zarchiwizowany.", "Zarchiwizowac ten dokument?");
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  container.querySelector("[data-knowledge-restore-document]")?.addEventListener("click", async () => {
    try {
      await wykonajAkcjeDokumentuBazyWiedzy(selectedDocument.knowledge_document_id, "/restore", { method: "POST" }, "Dokument zostal przywrocony.", "Przywrocic ten dokument do aktywnego obiegu?");
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  container.querySelector("[data-knowledge-delete-document]")?.addEventListener("click", async () => {
    try {
      await wykonajAkcjeDokumentuBazyWiedzy(selectedDocument.knowledge_document_id, "", { method: "DELETE" }, "Dokument zostal usuniety logicznie.", "Usunac logicznie ten dokument? Nadal bedzie mozliwy do przywrocenia.");
    } catch (error) {
      pokazPowiadomienie(error.message);
    }
  });
  container.querySelectorAll("[data-knowledge-restore-version]").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        await przywrocWersjeDokumentuBazyWiedzy(selectedDocument.knowledge_document_id, Number(button.dataset.knowledgeRestoreVersion));
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
    });
  });
  container.querySelectorAll("[data-knowledge-mark-official-version]").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        await oznaczWersjeDokumentuBazyWiedzyJakoObowiazujaca(
          selectedDocument.knowledge_document_id,
          Number(button.dataset.knowledgeMarkOfficialVersion)
        );
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
    });
  });
  container.querySelectorAll("[data-knowledge-compare-left][data-knowledge-compare-right]").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        await pobierzPorownanieWersjiDokumentuBazyWiedzy(
          selectedDocument.knowledge_document_id,
          Number(button.dataset.knowledgeCompareLeft),
          Number(button.dataset.knowledgeCompareRight)
        );
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
    });
  });
  container.querySelectorAll("[data-knowledge-compare-view]").forEach((button) => {
    button.addEventListener("click", () => {
      stan.widokPorownaniaWersjiBazyWiedzy = button.dataset.knowledgeCompareView || "blocks";
      renderujPodgladDokumentuBazyWiedzy();
    });
  });
  container.querySelectorAll("[data-knowledge-inline-mode]").forEach((button) => {
    button.addEventListener("click", () => {
      stan.trybPodgladuInlineBazyWiedzy = button.dataset.knowledgeInlineMode || "text";
      renderujPodgladDokumentuBazyWiedzy();
    });
  });
}

function renderujBazeWiedzy(payload) {
  zapewnijStanRozszerzenBazyWiedzy();
  const previousOrganizationId = Number(stan.konfiguracjaBazyWiedzy?.organization_id || 0);
  if (stan.ostatniImportBazyWiedzy && Number(stan.ostatniImportBazyWiedzy.organization_id || 0) !== Number(payload.organization_id || 0)) stan.ostatniImportBazyWiedzy = null;
  if (previousOrganizationId && previousOrganizationId !== Number(payload.organization_id || 0)) {
    stan.zaznaczoneDokumentyWiedzy = [];
    stan.ostatniWynikAkcjiMasowejBazyWiedzy = null;
    stan.folderMasowyBazyWiedzy = "";
  }
  stan.ostatniPayloadBazyWiedzy = payload;
  stan.dokumentyWiedzy = payload.documents || [];
  stan.aktywnoscBazyWiedzy = payload.activity_feed || [];
  stan.podsumowanieAktywnosciBazyWiedzy = payload.activity_summary || {};
  zsynchronizujCacheSzczegolowDokumentowBazyWiedzy(stan.dokumentyWiedzy);
  stan.folderBazyWiedzy = payload.folder_path || "";
  stan.konfiguracjaBazyWiedzy = { organization_id: payload.organization_id, supported_formats: payload.supported_formats || [], ocr_enabled: Boolean(payload.ocr_enabled), ocr_mode: payload.ocr_mode || "fallback", document_summary: payload.document_summary || {}, folder_summary: payload.folder_summary || [], watch_status: payload.watch_status || {}, limits: payload.limits || {} };

  const summary = payload.document_summary || {};
  const allDocuments = stan.dokumentyWiedzy || [];
  const libraryDocuments = pobierzDokumentyBibliotekiBazyWiedzy();
  const downloadableDocuments = allDocuments.filter((document) => document.is_downloadable);
  const filteredDocuments = pobierzPrzefiltrowaneDokumentyBazyWiedzy();
  if (czyMoznaZarzadzacPrzetwarzaniemBazyWiedzy() && stan.widokBazyWiedzy === "documents") zsynchronizujWyborDokumentowBazyWiedzy(filteredDocuments);
  else ustawZaznaczoneDokumentyBazyWiedzy([]);
  if (stan.widokBazyWiedzy === "documents" && !filteredDocuments.some((item) => Number(item.knowledge_document_id) === Number(stan.wybranyDokumentWiedzyId))) {
    stan.wybranyDokumentWiedzyId = filteredDocuments[0]?.knowledge_document_id || stan.wybranyDokumentWiedzyId || null;
  }

  document.getElementById("knowledge-count").textContent = `${allDocuments.length} dokumentow`;
  document.getElementById("knowledge-folder-path").textContent = stan.folderBazyWiedzy || "-";
  document.getElementById("knowledge-downloadable-count").textContent = czyMoznaZarzadzacPrzetwarzaniemBazyWiedzy()
    ? `${libraryDocuments.length} widoczne / ${downloadableDocuments.length} do pobrania`
    : `${libraryDocuments.length} plikow`;
  document.getElementById("knowledge-documents-summary").textContent = allDocuments.length
    ? `Aktywne: ${summary.active || 0}, archiwalne: ${summary.archived || 0}, usuniete: ${summary.deleted || 0}, robocze: ${summary.business_roboczy || 0}, do sprawdzenia: ${summary.business_do_sprawdzenia || 0}, do akceptacji: ${summary.business_do_akceptacji || 0}, obowiazujace: ${summary.business_obowiazujacy || 0}. Globalna wyszukiwarka obejmuje wszystkie dostepne pliki uzytkownika.`
    : "Ta organizacja nie ma jeszcze zadnych dokumentow wiedzy.";
  zsynchronizujFiltryBazyWiedzyZFormularzem();
  renderujSterowanieTrybemBazyWiedzy();

  document.getElementById("knowledge-pipeline-summary").innerHTML = `
    <span class="pill history-pill">gotowe: ${bezpiecznyTekst(summary.ready || 0)}</span>
    <span class="pill history-pill">kolejka: ${bezpiecznyTekst(summary.queued || 0)}</span>
    <span class="pill history-pill">przetwarzanie: ${bezpiecznyTekst(summary.processing || 0)}</span>
    <span class="pill history-pill">bledy: ${bezpiecznyTekst(summary.error || 0)}</span>
    ${zbudujPillsWatcheraBazyWiedzy(payload.watch_status)}
  `;

  const container = document.getElementById("knowledge-documents");
  const activityPanelMarkup = zbudujPanelAktywnosciBazyWiedzy(
    stan.aktywnoscBazyWiedzy || [],
    stan.podsumowanieAktywnosciBazyWiedzy || {}
  );
  const bulkPanelMarkup = zbudujPanelAkcjiMasowychBazyWiedzy(filteredDocuments);
  if (!libraryDocuments.length) {
    container.innerHTML = czyMoznaZarzadzacPrzetwarzaniemBazyWiedzy()
      ? `${activityPanelMarkup}<div class="empty-state">Brak dokumentow do pokazania w bibliotece. Menedzer widzi tu wszystkie rekordy, ale zaden nie zostal jeszcze przygotowany jako plik firmowy.</div>`
      : `${activityPanelMarkup}<div class="empty-state">Ta organizacja nie ma jeszcze plikow oznaczonych do pobrania. Dodaj dokument albo wlacz widocznosc biblioteki dla istniejacego pliku.</div>`;
  } else if (!filteredDocuments.length) {
    container.innerHTML = `${activityPanelMarkup}<div class="empty-state">Zadne pliki nie pasuja do biezacych filtrow. Wyczysc filtry albo zmien wyszukiwana fraze.</div>`;
  } else if (stan.widokDokumentowBazyWiedzy === "folders") {
    container.innerHTML = `${activityPanelMarkup}${bulkPanelMarkup}${grupujDokumentyWiedzyPoFolderach(filteredDocuments)
      .map((group) => `<section class="knowledge-folder-group"><div class="knowledge-folder-header"><div><strong>${bezpiecznyTekst(group.label)}</strong><div class="subtle-note">${bezpiecznyTekst(group.documents.length)} dokumentow</div></div><span class="pill history-pill">${bezpiecznyTekst(group.path || "root")}</span></div><div class="knowledge-folder-documents">${group.documents.map((document) => zbudujKarteDokumentuBazyWiedzy(document)).join("")}</div></section>`)
      .join("")}`;
  } else {
    container.innerHTML = `${activityPanelMarkup}${bulkPanelMarkup}${filteredDocuments.map((document) => zbudujKarteDokumentuBazyWiedzy(document)).join("")}`;
  }
  podpinaAkcjeListyDokumentowBazyWiedzy(container);
  if (stan.odpowiedzBazyWiedzy) renderujOdpowiedzBazyWiedzy(stan.odpowiedzBazyWiedzy);
  else {
    document.getElementById("knowledge-answer-empty").classList.remove("hidden");
    document.getElementById("knowledge-answer").classList.add("hidden");
    document.getElementById("knowledge-answer").innerHTML = "";
  }
  renderujPodgladDokumentuBazyWiedzy();
  if (stan.wybranyDokumentWiedzyId) wczytajSzczegolyDokumentuBazyWiedzy(stan.wybranyDokumentWiedzyId).catch(() => {});
  renderujPanelAdministratoraBazyWiedzy();
  renderujPodpowiedziPytanBazyWiedzy();
  odswiezStanBazyWiedzy();
}

function renderujPodpowiedziPytanBazyWiedzy() {
  const container = document.getElementById("knowledge-question-suggestions");
  const input = document.getElementById("knowledge-question");
  if (!container || !input) return;
  const assistantDocuments = pobierzDokumentyAsystentaBazyWiedzy();
  if (!stan.biezacyUzytkownik || !czyModulWiedzyMaZakres() || !czyMoznaKorzystacZAsystentaDokumentow()) {
    container.innerHTML = "";
    return;
  }
  if (!assistantDocuments.length) {
    container.innerHTML = '<div class="subtle-note">Brak dokumentow oznaczonych do pracy asystenta. W widoku Dokumenty mozna zdecydowac, ktore pliki maja byc uzywane w odpowiedziach.</div>';
    return;
  }
  const suggestions = assistantDocuments.slice(0, 4).map((document) => `Jakie zasady opisuje dokument ${document.title}?`);
  container.innerHTML = suggestions.map((question) => `<button type="button" class="knowledge-question-chip">${bezpiecznyTekst(question)}</button>`).join("");
  container.querySelectorAll(".knowledge-question-chip").forEach((button) => {
    button.addEventListener("click", () => {
      input.value = button.textContent || "";
      input.focus();
    });
  });
}

function odswiezStanBazyWiedzy() {
  zapewnijStanRozszerzenBazyWiedzy();
  renderujSterowanieTrybemBazyWiedzy();
  const saveButton = document.getElementById("knowledge-save-button");
  const syncButton = document.getElementById("knowledge-sync-button");
  const note = document.getElementById("knowledge-access-note");
  if (!saveButton || !syncButton || !note) return;
  const titleField = document.getElementById("knowledge-title");
  const fileField = document.getElementById("knowledge-file");
  const folderField = document.getElementById("knowledge-library-path");
  const downloadableField = document.getElementById("knowledge-is-downloadable");
  const assistantField = document.getElementById("knowledge-use-in-assistant");
  const contentField = document.getElementById("knowledge-content");
  const questionField = document.getElementById("knowledge-question");
  const askButton = document.querySelector('#knowledge-question-form button[type="submit"]');
  const assistantButton = document.getElementById("knowledge-mode-assistant");
  const documentsButton = document.getElementById("knowledge-mode-documents");
  const controls = [
    document.getElementById("knowledge-filter-lifecycle"),
    document.getElementById("knowledge-filter-status"),
    document.getElementById("knowledge-filter-business-status"),
    document.getElementById("knowledge-filter-source"),
    document.getElementById("knowledge-filter-search"),
    document.getElementById("knowledge-clear-filters"),
    document.getElementById("knowledge-documents-view-recent"),
    document.getElementById("knowledge-documents-view-folders"),
  ];

  if (!stan.biezacyUzytkownik) {
    [saveButton, syncButton, titleField, fileField, folderField, downloadableField, assistantField, contentField, questionField, askButton, assistantButton, documentsButton, ...controls].forEach(
      (element) => element && (element.disabled = true)
    );
    note.textContent = "Zaloguj sie, aby korzystac z bazy wiedzy.";
    anulujPollingBazyWiedzy();
    renderujPanelAdministratoraBazyWiedzy();
    renderujPodgladDokumentuBazyWiedzy();
    renderujPodpowiedziPytanBazyWiedzy();
    return;
  }

  const noOrg = czyGlobalnyAdministrator() && !stan.wybranaOrganizacjaId;
  const canImport = !noOrg && czyMoznaDodawacPlikiDoBazyWiedzy();
  const canSync = !noOrg && czyMoznaSynchronizowacBazeWiedzy();
  const canRead = czyModulWiedzyMaZakres() && czyMoznaCzytacBazeWiedzy();
  const canAsk = canRead && czyMoznaKorzystacZAsystentaDokumentow();
  saveButton.disabled = !canImport;
  syncButton.disabled = !canSync;
  [titleField, fileField, folderField, downloadableField, assistantField, contentField].forEach((element) => element && (element.disabled = !canImport));
  [questionField, askButton].forEach((element) => element && (element.disabled = !canAsk));
  controls.forEach((element) => element && (element.disabled = !canRead));
  if (assistantButton) assistantButton.disabled = !canAsk;
  if (documentsButton) documentsButton.disabled = !canRead;
  if (!canAsk && stan.widokBazyWiedzy === "assistant") {
    stan.widokBazyWiedzy = "documents";
    renderujSterowanieTrybemBazyWiedzy();
  }

  if (noOrg) note.textContent = "Wybierz konkretna organizacje, aby pracowac na jej bazie wiedzy.";
  else if (!czyMoznaCzytacBazeWiedzy()) note.textContent = "To konto nie ma dostepu do modulu wiedzy.";
  else if (!czyMoznaKorzystacZAsystentaDokumentow() && !czyMoznaPobieracPlikiFirmowe()) note.textContent = "Masz ograniczony dostep: widzisz rekordy wiedzy, ale bez pobierania plikow i bez trybu pytan.";
  else if (!czyMoznaKorzystacZAsystentaDokumentow()) note.textContent = "Masz dostep do dokumentow firmowych, ale bez trybu pytan do asystenta.";
  else if (!czyMoznaDodawacPlikiDoBazyWiedzy()) note.textContent = "Mozesz czytac, pobierac i pytac, ale import plikow oraz edycja dokumentow sa zablokowane dla tego konta.";
  else note.textContent = czyMoznaZarzadzacPrzetwarzaniemBazyWiedzy() ? "Masz pelen dostep do dokumentow firmowych, lifecycle, watcherow i kolejek przetwarzania." : "Mozesz dodawac dokumenty, pobierac pliki i zadawac pytania do bazy wiedzy.";

  odswiezPanelImportuBazyWiedzy();
  renderujPanelAdministratoraBazyWiedzy();
  renderujPodgladDokumentuBazyWiedzy();
  renderujPodpowiedziPytanBazyWiedzy();
  zaplanujPollingBazyWiedzy();
}

function renderujPanelAdministratoraBazyWiedzy() {
  const container = document.getElementById("knowledge-admin-panel");
  const count = document.getElementById("knowledge-admin-count");
  if (!container || !count) return;
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
    container.innerHTML = `<article class="knowledge-admin-user"><div class="knowledge-admin-header"><div><strong>Twoje prawa w module wiedzy</strong><p class="subtle-note">To konto nie moze zmieniac uprawnien innych osob, ale widzi swoj aktualny zakres i czlonkostwa.</p></div><div>${zbudujWidokCapabilityPills(myCapabilities)}</div></div><div class="knowledge-membership-row">${zbudujWidokCzlonkostwUzytkownika(stan.biezacyUzytkownik)}</div><p class="subtle-note">Glowny zakres: ${bezpiecznyTekst(pobierzSkrotCzlonkostwUzytkownika(stan.biezacyUzytkownik))}</p></article>`;
    return;
  }

  const users = Array.isArray(stan.uzytkownicy) ? stan.uzytkownicy : [];
  const membershipCount = users.reduce((sum, user) => sum + (Array.isArray(user.memberships) ? user.memberships.length : 0), 0);
  count.textContent = `${users.length} kont / ${membershipCount} czlonkostw`;
  if (!users.length) {
    container.className = "empty-state";
    container.textContent = "Brak kont w tej organizacji albo lista uzytkownikow nie zostala jeszcze zaladowana.";
    return;
  }

  const summaryPills = (stan.meta?.knowledge_capabilities || Object.keys(capabilityLabels))
    .map((capability) => {
      const usersWithCapability = users.filter((item) => (item.capabilities || []).includes(capability)).length;
      return `<span class="pill history-pill">${bezpiecznyTekst(capabilityLabels[capability] || capability)}: ${bezpiecznyTekst(usersWithCapability)}</span>`;
    })
    .join("");

  container.className = "";
  container.innerHTML = `<div class="knowledge-admin-summary">${summaryPills}</div><div class="knowledge-admin-list">${users
    .map((user) => {
      const capabilities = new Set(znormalizujCapabilitiesWiedzy(user.capabilities || [], user.role));
      const isGuestRole = user.role === "guest";
      const capabilityCheckboxes = (stan.meta?.knowledge_capabilities || Object.keys(capabilityLabels))
        .map((capability) => {
          const checked = capabilities.has(capability) ? "checked" : "";
          const disabled = capability === "knowledge.read" || isGuestRole ? "disabled" : "";
          return `<label><input type="checkbox" data-knowledge-admin-capability="${bezpiecznyTekst(capability)}" value="${bezpiecznyTekst(capability)}" ${checked} ${disabled} /><span>${bezpiecznyTekst(capabilityLabels[capability] || capability)}</span></label>`;
        })
        .join("");
      return `<article class="knowledge-admin-user" data-knowledge-admin-user="${user.user_id}"><div class="knowledge-admin-header"><div><strong>${bezpiecznyTekst(user.display_name || user.login)}</strong><p class="subtle-note">Login: ${bezpiecznyTekst(user.login)} | Rola: ${bezpiecznyTekst(formatujRole(user.role))}</p></div><div>${zbudujWidokCapabilityPills(Array.from(capabilities))}</div></div><div class="knowledge-membership-row">${zbudujWidokCzlonkostwUzytkownika(user)}</div><div class="knowledge-admin-capabilities">${capabilityCheckboxes}</div><div class="knowledge-admin-actions"><p class="subtle-note">${isGuestRole ? "Rola gosc pozostaje tylko do odczytu i pobierania. Aby dac szerszy dostep, zmien role uzytkownika." : "Zmiany zapisuja sie tylko dla modulu wiedzy, ale konto zachowuje czlonkostwa potrzebne do ekosystemu."}</p><button type="button" class="secondary knowledge-admin-save" data-knowledge-admin-save="${user.user_id}">Zapisz prawa</button></div></article>`;
    })
    .join("")}</div>`;
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
  if (!czyMoznaZarzadzacUzytkownikami()) return pokazPowiadomienie("To konto nie moze zmieniac praw innych uzytkownikow.");
  const row = button?.closest?.("[data-knowledge-admin-user]");
  if (!row) throw new Error("Nie znaleziono formularza praw tego uzytkownika.");
  const currentUser = (stan.uzytkownicy || []).find((item) => Number(item.user_id) === Number(userId));
  const selected = Array.from(row.querySelectorAll("[data-knowledge-admin-capability]:checked")).map((input) => input.value).filter(Boolean);
  const normalized = znormalizujCapabilitiesWiedzy(selected, currentUser?.role || "");
  button.disabled = true;
  button.classList.add("is-busy");
  const savedUser = await api(`/api/users/${userId}`, { method: "PATCH", body: JSON.stringify({ capabilities: normalized, can_upload_knowledge: normalized.includes("knowledge.upload") }) });
  const editedCurrentUser = stan.biezacyUzytkownik && Number(savedUser.user_id) === Number(stan.biezacyUzytkownik.user_id);
  if (editedCurrentUser) {
    stan.biezacyUzytkownik = savedUser;
    odswiezPasekSesji();
  }
  await wczytajLogi();
  if (czyMoznaZarzadzacUzytkownikami()) await wczytajUzytkownikow();
  else {
    stan.uzytkownicy = [];
    renderujPanelAdministratoraBazyWiedzy();
  }
  if (editedCurrentUser) {
    try {
      await wczytajBazeWiedzy();
    } catch (_error) {
      wyczyscBazeWiedzy();
      odswiezStanBazyWiedzy();
    }
  } else {
    odswiezStanBazyWiedzy();
  }
  pokazPowiadomienie(`Zapisano prawa wiedzy dla konta ${savedUser.login}.`);
}

function renderujUzytkownikow(uzytkownicy) {
  stan.uzytkownicy = uzytkownicy;
  const body = document.getElementById("users-table-body");
  if (!uzytkownicy.length) {
    body.innerHTML = `<tr><td colspan="12">Brak kont uzytkownikow.</td></tr>`;
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
          <td>${bezpiecznyTekst(pobierzSkrotCzlonkostwUzytkownika(uzytkownik))}</td>
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
      const user = stan.uzytkownicy.find((item) => Number(item.user_id) === userId);
      if (user) wypelnijFormularzUzytkownika(user);
    });
  });
}

async function wczytajUzytkownikow() {
  if (!czyMoznaZarzadzacUzytkownikami()) {
    stan.uzytkownicy = [];
    document.getElementById("users-table-body").innerHTML = `<tr><td colspan="12">Panel uzytkownikow jest dostepny tylko dla Wlasciciela systemu albo Administratora organizacji.</td></tr>`;
    renderujPanelAdministratoraBazyWiedzy();
    return;
  }
  renderujUzytkownikow(await api(zbudujAdresZOrganizacja("/api/users")));
  renderujPanelAdministratoraBazyWiedzy();
}

function inicjalizujRozszerzeniaBazyWiedzy() {
  zapewnijStanRozszerzenBazyWiedzy();
  if (stan.czyRozszerzeniaBazyWiedzyPodpiete) return;
  stan.czyRozszerzeniaBazyWiedzyPodpiete = true;
  ["knowledge-filter-lifecycle", "knowledge-filter-status", "knowledge-filter-business-status", "knowledge-filter-source"].forEach((id) =>
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
    stan.filtryBazyWiedzy = { lifecycle: "", status: "", businessStatus: "", source: "", search: "" };
    zsynchronizujFiltryBazyWiedzyZFormularzem();
    odswiezWidokBazyWiedzyZPamieci();
  });
  if (!stan.czyGlobalnaObslugaAkcjiDokumentowWiedzyPodpieta) {
    stan.czyGlobalnaObslugaAkcjiDokumentowWiedzyPodpieta = true;
    document.addEventListener("click", async (event) => {
      const openDocumentButton = event.target.closest("[data-knowledge-open-document]");
      if (openDocumentButton) {
        event.preventDefault();
        event.stopPropagation();
        try {
          await otworzDokumentBazyWiedzyZWidokuPracy(openDocumentButton.dataset.knowledgeOpenDocument);
        } catch (error) {
          pokazPowiadomienie(error.message);
        }
        return;
      }
      const openDecisionButton = event.target.closest("[data-knowledge-open-decision-modal][data-knowledge-decision-action]");
      if (openDecisionButton) {
        event.preventDefault();
        event.stopPropagation();
        try {
          await otworzModalDecyzjiDokumentuBazyWiedzy(
            openDecisionButton.dataset.knowledgeOpenDecisionModal,
            openDecisionButton.dataset.knowledgeDecisionAction
          );
        } catch (error) {
          pokazPowiadomienie(error.message);
        }
        return;
      }
      const openTaskButton = event.target.closest("[data-knowledge-open-task-modal]");
      if (openTaskButton) {
        event.preventDefault();
        event.stopPropagation();
        try {
          await otworzModalZadaniaZDokuBazyWiedzy(openTaskButton.dataset.knowledgeOpenTaskModal);
        } catch (error) {
          pokazPowiadomienie(error.message);
        }
        return;
      }
      if (event.target.closest("[data-knowledge-decision-close]")) {
        event.preventDefault();
        zamknijModalDecyzjiDokumentuBazyWiedzy();
        return;
      }
      if (event.target.closest("#knowledge-decision-modal-submit")) {
        event.preventDefault();
        await zapiszDecyzjeDokumentuBazyWiedzyZModala();
        return;
      }
      if (event.target.closest("[data-knowledge-task-close]")) {
        event.preventDefault();
        zamknijModalZadaniaDokumentuBazyWiedzy();
        return;
      }
      if (event.target.closest("#knowledge-task-modal-submit")) {
        event.preventDefault();
        await zapiszZadanieZDokuBazyWiedzyZModala();
        return;
      }
      if (event.target?.id === "knowledge-decision-modal") {
        zamknijModalDecyzjiDokumentuBazyWiedzy();
        return;
      }
      if (event.target?.id === "knowledge-task-modal") {
        zamknijModalZadaniaDokumentuBazyWiedzy();
      }
    });
  }
}

function odswiezPanelImportuBazyWiedzy() {
  const formats = bezpiecznyTekst(pobierzFormatyBazyWiedzy().join(", "));
  const limitMb = Number(stan.konfiguracjaBazyWiedzy?.limits?.max_upload_megabytes || 0);
  const watchStatus = stan.konfiguracjaBazyWiedzy?.watch_status || {};
  const watcherNote = watchStatus.enabled ? ` Watcher: ${bezpiecznyTekst(watchStatus.watch_mode || "polling")}, ostatni status: ${bezpiecznyTekst(watchStatus.last_scan_status || "idle")}.` : "";
  const baseDescription = `Obslugiwane formaty: ${formats}. ${opisOcrBazyWiedzy()}${limitMb ? ` Limit jednego pliku: ${bezpiecznyTekst(limitMb)} MB.` : ""}${watcherNote}`;
  const file = document.getElementById("knowledge-file")?.files?.[0];
  const title = document.getElementById("knowledge-title")?.value.trim() || "";
  const content = document.getElementById("knowledge-content")?.value.trim() || "";
  if (!stan.biezacyUzytkownik) return ustawPanelImportuBazyWiedzy({ title: "Import dokumentow", description: `Zaloguj sie, aby importowac dokumenty do bazy wiedzy. ${baseDescription}` });
  if (!czyModulWiedzyMaZakres()) return ustawPanelImportuBazyWiedzy({ title: "Wybierz organizacje", description: `Najpierw wybierz organizacje, a potem dodaj plik lub uruchom synchronizacje folderu. ${baseDescription}`, variant: "warning" });
  if (stan.ostatniImportBazyWiedzy?.kind === "sync") {
    const summary = stan.ostatniImportBazyWiedzy;
    const skippedCount = Array.isArray(summary.skipped) ? summary.skipped.length : 0;
    return ustawPanelImportuBazyWiedzy({ title: "Synchronizacja zakonczona", description: `Nowe: <strong>${bezpiecznyTekst(summary.imported_count || 0)}</strong>, zaktualizowane: <strong>${bezpiecznyTekst(summary.updated_count || 0)}</strong>, bez zmian: <strong>${bezpiecznyTekst(summary.unchanged_count || 0)}</strong>, pominiete: <strong>${bezpiecznyTekst(skippedCount)}</strong>, duplikaty: <strong>${bezpiecznyTekst(summary.duplicate_count || 0)}</strong>, podobne: <strong>${bezpiecznyTekst(summary.similar_count || 0)}</strong>. ${baseDescription}`, variant: skippedCount && !(summary.imported_count || summary.updated_count) ? "warning" : "success" });
  }
  if (stan.ostatniImportBazyWiedzy?.kind === "upload") {
    const summary = stan.ostatniImportBazyWiedzy;
    return ustawPanelImportuBazyWiedzy({ title: "Dokument dodany", description: `Zapisano <strong>${bezpiecznyTekst(summary.title || summary.file_name || "Dokument")}</strong> jako ${bezpiecznyTekst(formatujZrodloBazyWiedzy(summary.source_type).toLowerCase())}.${summary.file_name ? ` Plik: ${bezpiecznyTekst(summary.file_name)}.` : ""}${summary.file_size ? ` Rozmiar: ${bezpiecznyTekst(formatujRozmiarPliku(summary.file_size))}.` : ""} ${baseDescription}`, variant: "success" });
  }
  if (!czyMoznaDodawacPlikiDoBazyWiedzy()) return ustawPanelImportuBazyWiedzy({ title: "Tryb tylko do odczytu", description: `To konto moze czytac dokumenty i korzystac z tych praw, ktore wlaczyl administrator, ale nie moze importowac nowych plikow. ${baseDescription}`, variant: "warning" });
  if (file) return ustawPanelImportuBazyWiedzy({ title: "Plik gotowy do importu", description: `Wybrano <strong>${bezpiecznyTekst(file.name)}</strong> (${bezpiecznyTekst(formatujRozmiarPliku(file.size))}). ${title ? `Tytul dokumentu: ${bezpiecznyTekst(title)}. ` : ""}${/\.(jpg|jpeg|png|bmp|tif|tiff|webp)$/i.test(file.name) ? `${opisOcrBazyWiedzy()} ` : ""}${baseDescription}` });
  if (content) return ustawPanelImportuBazyWiedzy({ title: "Dokument tekstowy", description: `Wklejona tresc zostanie zapisana jako osobny dokument wiedzy.${title ? ` Tytul: ${bezpiecznyTekst(title)}.` : ""} ${baseDescription}` });
  ustawPanelImportuBazyWiedzy({ title: "Import dokumentow", description: `Mozesz dodac plik bezposrednio tutaj albo wrzucic go do folderu organizacji i uruchomic synchronizacje. ${baseDescription}` });
}
