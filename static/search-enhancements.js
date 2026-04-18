function pobierzPusteWynikiWyszukiwania() {
  return {
    query: "",
    scope_label: "",
    modules: [],
    groups: [],
    assistant_answer: null,
    invoices: [],
    contractors: [],
  };
}

function normalizujWynikiWyszukiwania(results) {
  const payload = results && typeof results === "object" ? results : pobierzPusteWynikiWyszukiwania();
  const modules = Array.isArray(payload.modules)
    ? payload.modules.filter(Boolean).map((item) => ({
        entity_type: String(item.entity_type || "module"),
        entity_id: item.entity_id ?? item.key ?? "",
        organization_id: item.organization_id ?? null,
        view: String(item.view || "dashboard"),
        section: item.section || "",
        category: String(item.category || "Modul"),
        badge: String(item.badge || "Modul"),
        title: String(item.title || "Modul"),
        subtitle: String(item.subtitle || ""),
        meta: String(item.meta || ""),
      }))
    : [];

  let groups = Array.isArray(payload.groups)
    ? payload.groups
        .filter(Boolean)
        .map((group) => ({
          key: String(group.key || "results"),
          label: String(group.label || "Wyniki"),
          items: Array.isArray(group.items)
            ? group.items.filter(Boolean).map((item) => ({
                entity_type: String(item.entity_type || "record"),
                entity_id: item.entity_id ?? item.id ?? "",
                organization_id: item.organization_id ?? null,
                view: String(item.view || "dashboard"),
                section: item.section || "",
                category: String(item.category || group.label || "Wyniki"),
                badge: String(item.badge || "Wynik"),
                title: String(item.title || "Bez nazwy"),
                subtitle: String(item.subtitle || ""),
                meta: String(item.meta || ""),
              }))
            : [],
        }))
    : [];

  if (!groups.length) {
    const legacyInvoices = Array.isArray(payload.invoices) ? payload.invoices : [];
    const legacyContractors = Array.isArray(payload.contractors) ? payload.contractors : [];
    groups = [];

    if (legacyInvoices.length) {
      groups.push({
        key: "invoices",
        label: "Faktury",
        items: legacyInvoices.map((invoice) => ({
          entity_type: "invoice",
          entity_id: invoice.id,
          organization_id: invoice.organization_id ?? null,
          view: "invoices",
          section: "",
          category: "Faktury",
          badge: `#${invoice.id}`,
          title: String(invoice.invoice_number || invoice.file_name || `Faktura #${invoice.id}`),
          subtitle: [invoice.organization_name, invoice.issuer_name].filter(Boolean).join(" | "),
          meta: [invoice.issuer_nip, invoice.source, invoice.status].filter(Boolean).join(" | "),
        })),
      });
    }

    if (legacyContractors.length) {
      groups.push({
        key: "contractors",
        label: "Kontrahenci",
        items: legacyContractors.map((contractor) => ({
          entity_type: "contractor",
          entity_id: contractor.contractor_id,
          organization_id: contractor.organization_id ?? null,
          view: "contractors",
          section: "",
          category: "Kontrahenci",
          badge: `#${contractor.contractor_id}`,
          title: String(contractor.name || `Kontrahent #${contractor.contractor_id}`),
          subtitle: [contractor.organization_name, contractor.nip].filter(Boolean).join(" | "),
          meta: [contractor.email, contractor.phone].filter(Boolean).join(" | "),
        })),
      });
    }
  }

  return {
    query: String(payload.query || ""),
    scope_label: String(payload.scope_label || ""),
    modules,
    groups,
    assistantAnswer: payload.assistant_answer && typeof payload.assistant_answer === "object" ? payload.assistant_answer : null,
  };
}

function maWynikiWyszukiwania(results) {
  const normalized = normalizujWynikiWyszukiwania(results);
  return normalized.modules.length > 0 || normalized.groups.some((group) => group.items.length > 0);
}

function wyczyscWyszukiwanieGlobalne(options = {}) {
  const { clearInput = false, resetToken = false } = options;
  if (stan.wyszukiwanieGlobalneTimeoutId) {
    window.clearTimeout(stan.wyszukiwanieGlobalneTimeoutId);
    stan.wyszukiwanieGlobalneTimeoutId = null;
  }
  if (resetToken) {
    stan.wyszukiwanieGlobalneToken += 1;
  }
  const container = document.getElementById("global-search-results");
  if (container) {
    container.classList.add("hidden");
    container.innerHTML = "";
  }
  if (clearInput) {
    const input = document.getElementById("global-search");
    if (input) {
      input.value = "";
    }
  }
}

function renderujKarteWynikuWyszukiwania(item, attributes = "") {
  return `
    <button type="button" class="search-result-item" ${attributes}>
      <div class="search-result-category">${bezpiecznyTekst(item.category || "Wynik")}</div>
      <div class="search-result-header">
        <span class="search-result-badge">${bezpiecznyTekst(item.badge || "Wynik")}</span>
        <span class="search-result-title">${bezpiecznyTekst(item.title || "Bez nazwy")}</span>
      </div>
      ${item.subtitle ? `<div class="search-result-subtitle">${bezpiecznyTekst(item.subtitle)}</div>` : ""}
      ${item.meta ? `<div class="search-result-meta">${bezpiecznyTekst(item.meta)}</div>` : ""}
    </button>
  `;
}

function czyFrazaWygladaJakPytanieDoAsystenta(fraza) {
  const normalized = String(fraza || "").trim().toLowerCase();
  if (!normalized) {
    return false;
  }
  if (normalized.includes("?")) {
    return true;
  }
  if (normalized.split(/\s+/).length >= 5) {
    return true;
  }
  return /^(kto|co|jak|gdzie|kiedy|czy|dlaczego|po co|ile|jaki|jaka|jakie|ktory|ktora|ktore|w jaki sposob|na czym)/.test(
    normalized
  );
}

function czyMoznaUruchomicAsystentaFirmowegoZGlobalSearch() {
  return Boolean(
    stan.biezacyUzytkownik &&
      typeof czyMoznaCzytacBazeWiedzy === "function" &&
      typeof czyModulWiedzyMaZakres === "function" &&
      czyMoznaCzytacBazeWiedzy() &&
      czyModulWiedzyMaZakres()
  );
}

function renderujKarteAsystentaFirmowego(wynik) {
  if (!wynik || typeof wynik !== "object") {
    return "";
  }
  const matches = Array.isArray(wynik.matches) ? wynik.matches : [];
  return `
    <section class="search-ai-card">
      <div class="search-group-header">
        <div>
          <div class="search-section-label">Asystent Firmowy</div>
          <strong>Odpowiedz na podstawie plikow firmowych</strong>
          <div class="subtle-note">${bezpiecznyTekst(
            wynik.organization_name || "Biezaca organizacja"
          )} | dokumenty gotowe: ${bezpiecznyTekst(wynik.ready_document_count || 0)}</div>
        </div>
        <span class="search-result-category">AI</span>
      </div>
      <div class="search-ai-answer">${bezpiecznyTekst(wynik.answer || "")}</div>
      ${
        matches.length
          ? `
            <div class="search-ai-sources">
              ${matches
                .map(
                  (match, index) => `
                    <button
                      type="button"
                      class="search-ai-source"
                      data-search-ai-doc-id="${match.knowledge_document_id}"
                      data-search-ai-doc-index="${index}"
                    >
                      <div class="search-result-category">${bezpiecznyTekst(match.citation_label || "Zrodlo")}</div>
                      <div class="search-result-subtitle">${bezpiecznyTekst(match.snippet || "")}</div>
                      <div class="search-result-meta">
                        ${bezpiecznyTekst(match.file_name || "")} | wynik: ${bezpiecznyTekst(match.score || 0)}
                      </div>
                    </button>
                  `
                )
                .join("")}
            </div>
          `
          : `<div class="subtle-note">Brak bezposrednich fragmentow do pokazania dla tego pytania.</div>`
      }
    </section>
  `;
}

function podswietlElementWyszukiwania(element) {
  if (!element) {
    return false;
  }
  element.scrollIntoView({ behavior: "smooth", block: "center" });
  element.classList.remove("search-target-flash");
  void element.offsetWidth;
  element.classList.add("search-target-flash");
  window.setTimeout(() => element.classList.remove("search-target-flash"), 1600);
  return true;
}

function podswietlSelectorWyszukiwania(selector) {
  const element = document.querySelector(selector);
  return podswietlElementWyszukiwania(element);
}

function przewinDoSekcjiWyszukiwania(sectionId) {
  if (!sectionId) {
    return null;
  }
  const element = document.getElementById(sectionId);
  if (!element) {
    return null;
  }
  const target = element.closest(".panel, .table-wrap, .detail-grid, .summary-grid") || element;
  target.scrollIntoView({ behavior: "smooth", block: "start" });
  return target;
}

async function ustawZakresOrganizacjiDlaWyniku(organizationId) {
  if (!czyGlobalnyAdministrator() || !organizationId) {
    return false;
  }
  const nextOrganizationId = String(organizationId);
  if (String(stan.wybranaOrganizacjaId || "") === nextOrganizationId) {
    return false;
  }
  stan.wybranaOrganizacjaId = nextOrganizationId;
  stan.czyZakresOrganizacjiZainicjalizowany = true;
  const switcher = document.getElementById("organization-switcher");
  if (switcher) {
    switcher.value = nextOrganizationId;
  }
  odswiezPasekSesji();
  await odswiezDanePoZalogowaniu();
  return true;
}

async function przejdzDoWynikuWyszukiwania(item) {
  if (!item || !item.view) {
    return;
  }

  await ustawZakresOrganizacjiDlaWyniku(item.organization_id);
  ustawWidok(item.view);

  switch (item.entity_type) {
    case "module":
      if (item.view === "dashboard") {
        await wczytajPulpit();
      } else if (item.view === "invoices") {
        await Promise.all([wczytajWszystkichKontrahentow(), wczytajFaktury()]);
      } else if (item.view === "tasks") {
        await wczytajZadania();
      } else if (item.view === "contractors") {
        await wczytajKontrahentow();
      } else if (item.view === "billing") {
        await wczytajRozliczenia();
      } else if (item.view === "knowledge") {
        await wczytajBazeWiedzy();
      } else if (item.view === "logs") {
        await wczytajLogi();
      } else if (item.view === "users") {
        await wczytajUzytkownikow();
      } else if (item.view === "organizations") {
        await wczytajPanelOrganizacji();
      }
      if (item.section) {
        const target = przewinDoSekcjiWyszukiwania(item.section);
        if (target) {
          podswietlElementWyszukiwania(target);
        }
      } else {
        podswietlSelectorWyszukiwania(`#${item.view}-view`);
      }
      break;
    case "invoice":
      await Promise.all([wczytajWszystkichKontrahentow(), wczytajFaktury()]);
      await wczytajSzczegolyFaktury(Number(item.entity_id));
      if (!podswietlSelectorWyszukiwania(`[data-invoice-id="${item.entity_id}"]`)) {
        podswietlSelectorWyszukiwania("#invoice-detail");
      }
      break;
    case "task":
      await wczytajZadania();
      await wczytajSzczegolyZadania(Number(item.entity_id));
      if (!podswietlSelectorWyszukiwania(`[data-task-id="${item.entity_id}"]`)) {
        podswietlSelectorWyszukiwania("#task-detail");
      }
      break;
    case "contractor":
      await wczytajKontrahentow();
      await wczytajSzczegolyKontrahenta(Number(item.entity_id));
      if (!podswietlSelectorWyszukiwania(`[data-contractor-id="${item.entity_id}"]`)) {
        podswietlSelectorWyszukiwania("#contractor-detail");
      }
      break;
    case "knowledge_document":
      await wczytajBazeWiedzy();
      ustawWybranyDokumentBazyWiedzy(item.entity_id);
      if (!podswietlSelectorWyszukiwania(`[data-knowledge-select-id="${item.entity_id}"]`)) {
        podswietlSelectorWyszukiwania("#knowledge-selected-document");
      }
      break;
    case "billing_bank_account":
      await wczytajRozliczenia();
      document.getElementById("billing-import-bank-account-id").value = String(item.entity_id);
      if (!podswietlSelectorWyszukiwania(`[data-billing-bank-account-id="${item.entity_id}"]`)) {
        const bankAccountTarget = przewinDoSekcjiWyszukiwania(item.section || "billing-bank-account-table-body");
        if (bankAccountTarget) {
          podswietlElementWyszukiwania(bankAccountTarget);
        }
      }
      break;
    case "billing_transaction":
      await wczytajRozliczenia();
      if (!podswietlSelectorWyszukiwania(`[data-billing-transaction-id="${item.entity_id}"]`)) {
        const transactionTarget = przewinDoSekcjiWyszukiwania(item.section || "billing-transaction-table-body");
        if (transactionTarget) {
          podswietlElementWyszukiwania(transactionTarget);
        }
      }
      break;
    case "log":
      await wczytajLogi();
      if (!podswietlSelectorWyszukiwania(`[data-log-id="${item.entity_id}"]`)) {
        const logTarget = przewinDoSekcjiWyszukiwania(item.section || "log-table-body");
        if (logTarget) {
          podswietlElementWyszukiwania(logTarget);
        }
      }
      break;
    case "user": {
      await wczytajUzytkownikow();
      const user = (stan.uzytkownicy || []).find((entry) => Number(entry.user_id) === Number(item.entity_id));
      if (user) {
        wypelnijFormularzUzytkownika(user);
      }
      if (!podswietlSelectorWyszukiwania(`[data-user-id="${item.entity_id}"]`)) {
        podswietlSelectorWyszukiwania("#user-form");
      }
      break;
    }
    case "organization": {
      await wczytajPanelOrganizacji();
      const organization = (stan.organizacje || []).find(
        (entry) => Number(entry.organization_id) === Number(item.entity_id)
      );
      if (organization) {
        wypelnijFormularzOrganizacji(organization);
      }
      if (!podswietlSelectorWyszukiwania(`[data-organization-id="${item.entity_id}"]`)) {
        podswietlSelectorWyszukiwania("#organization-form");
      }
      break;
    }
    default:
      if (item.section) {
        const target = przewinDoSekcjiWyszukiwania(item.section);
        if (target) {
          podswietlElementWyszukiwania(target);
        }
      }
      break;
  }

  wyczyscWyszukiwanieGlobalne({ clearInput: true, resetToken: true });
}

function renderujWynikiWyszukiwania(results) {
  const container = document.getElementById("global-search-results");
  if (!container) {
    return;
  }

  const normalized = normalizujWynikiWyszukiwania(results);
  if (!normalized.query) {
    container.classList.add("hidden");
    container.innerHTML = "";
    return;
  }

  const totalItemCount =
    normalized.modules.length +
    normalized.groups.reduce((sum, group) => sum + (Array.isArray(group.items) ? group.items.length : 0), 0);
  const hasResults = maWynikiWyszukiwania(normalized);

  container.classList.remove("hidden");
  container.innerHTML = `
    <div class="search-results-shell">
      <div class="search-results-main-header">
        <div>
          <div class="search-section-label">Wyniki globalnego wyszukiwania</div>
          <strong>${bezpiecznyTekst(normalized.query)}</strong>
          <div class="subtle-note">${bezpiecznyTekst(
            normalized.scope_label || "Tylko dane dostepne w Twoim aktualnym zakresie."
          )}</div>
        </div>
        <span class="pill history-pill">${bezpiecznyTekst(totalItemCount)} wynikow</span>
      </div>
      ${normalized.assistantAnswer ? renderujKarteAsystentaFirmowego(normalized.assistantAnswer) : ""}
      ${
        normalized.modules.length
          ? `
            <div class="search-modules-shell">
              <div class="search-section-label">Moduly i kategorie</div>
              <div class="search-modules-grid">
                ${normalized.modules
                  .map((item, moduleIndex) =>
                    renderujKarteWynikuWyszukiwania(
                      item,
                      `data-search-module-index="${moduleIndex}" data-search-result-kind="module"`
                    )
                  )
                  .join("")}
              </div>
            </div>
          `
          : ""
      }
      ${
        hasResults
          ? `
            <div class="search-group-grid">
              ${normalized.groups
                .filter((group) => group.items.length)
                .map(
                  (group, groupIndex) => `
                    <section class="search-group-card">
                      <div class="search-group-header">
                        <div>
                          <div class="search-section-label">${bezpiecznyTekst(group.label)}</div>
                          <div class="subtle-note">${bezpiecznyTekst(group.items.length)} trafien</div>
                        </div>
                      </div>
                      <div class="search-results-list">
                        ${group.items
                          .map((item, itemIndex) =>
                            renderujKarteWynikuWyszukiwania(
                              item,
                              `data-search-group-index="${groupIndex}" data-search-item-index="${itemIndex}" data-search-result-kind="record"`
                            )
                          )
                          .join("")}
                      </div>
                    </section>
                  `
                )
                .join("")}
            </div>
          `
          : `<div class="empty-state">Brak wynikow w Twoim zakresie dostepu dla tej frazy.</div>`
      }
    </div>
  `;

  container.querySelectorAll("[data-search-module-index]").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        const item = normalized.modules[Number(button.dataset.searchModuleIndex)];
        await przejdzDoWynikuWyszukiwania(item);
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
    });
  });

  container.querySelectorAll("[data-search-group-index][data-search-item-index]").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        const group = normalized.groups[Number(button.dataset.searchGroupIndex)];
        const item = group?.items?.[Number(button.dataset.searchItemIndex)];
        await przejdzDoWynikuWyszukiwania(item);
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
    });
  });

  container.querySelectorAll("[data-search-ai-doc-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        const match = normalized.assistantAnswer?.matches?.[Number(button.dataset.searchAiDocIndex)];
        if (!match) {
          return;
        }
        await przejdzDoWynikuWyszukiwania({
          entity_type: "knowledge_document",
          entity_id: match.knowledge_document_id,
          organization_id: normalized.assistantAnswer?.organization_id ?? null,
          view: "knowledge",
          section: "",
          category: "Asystent Firmowy",
          badge: `v${match.version_number || 0}`,
          title: match.title || "Dokument",
          subtitle: match.file_name || "",
          meta: match.citation_label || "",
        });
      } catch (error) {
        pokazPowiadomienie(error.message);
      }
    });
  });
}

function obsluzRozszerzoneWyszukiwanieGlobalne(event) {
  event.stopImmediatePropagation();
  const fraza = String(event.target?.value || "").trim();

  if (stan.wyszukiwanieGlobalneTimeoutId) {
    window.clearTimeout(stan.wyszukiwanieGlobalneTimeoutId);
    stan.wyszukiwanieGlobalneTimeoutId = null;
  }

  if (!fraza || !stan.biezacyUzytkownik) {
    wyczyscWyszukiwanieGlobalne({ resetToken: true });
    return;
  }

  const token = ++stan.wyszukiwanieGlobalneToken;
  stan.wyszukiwanieGlobalneTimeoutId = window.setTimeout(async () => {
    try {
      const canAskKnowledge = czyMoznaUruchomicAsystentaFirmowegoZGlobalSearch();
      const shouldAskKnowledge = canAskKnowledge && czyFrazaWygladaJakPytanieDoAsystenta(fraza);
      const [searchResult, assistantResult] = await Promise.allSettled([
        api(zbudujAdresZOrganizacja(`/api/search?q=${encodeURIComponent(fraza)}`)),
        shouldAskKnowledge
          ? api(zbudujAdresZOrganizacja("/api/knowledge/ask"), {
              method: "POST",
              body: JSON.stringify({ question: fraza }),
            })
          : Promise.resolve(null),
      ]);
      if (token !== stan.wyszukiwanieGlobalneToken) {
        return;
      }
      if (searchResult.status !== "fulfilled") {
        throw searchResult.reason;
      }
      renderujWynikiWyszukiwania({
        ...searchResult.value,
        assistant_answer: assistantResult.status === "fulfilled" ? assistantResult.value : null,
      });
    } catch (error) {
      if (token === stan.wyszukiwanieGlobalneToken) {
        pokazPowiadomienie(error.message);
      }
    } finally {
      if (token === stan.wyszukiwanieGlobalneToken) {
        stan.wyszukiwanieGlobalneTimeoutId = null;
      }
    }
  }, 200);
}

function inicjalizujRozszerzoneWyszukiwanieGlobalne() {
  if (window.__casiSearchEnhancementsReady) {
    return;
  }
  window.__casiSearchEnhancementsReady = true;

  const input = document.getElementById("global-search");
  if (input) {
    input.addEventListener("input", obsluzRozszerzoneWyszukiwanieGlobalne, true);
  }

  const organizationSwitcher = document.getElementById("organization-switcher");
  if (organizationSwitcher) {
    organizationSwitcher.addEventListener(
      "change",
      () => {
        wyczyscWyszukiwanieGlobalne({ resetToken: true });
      },
      true
    );
  }

  const logoutButton = document.getElementById("logout-button");
  if (logoutButton) {
    logoutButton.addEventListener(
      "click",
      () => {
        wyczyscWyszukiwanieGlobalne({ clearInput: true, resetToken: true });
      },
      true
    );
  }
}

window.renderujWynikiWyszukiwania = renderujWynikiWyszukiwania;
window.wyczyscWyszukiwanieGlobalne = wyczyscWyszukiwanieGlobalne;

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", inicjalizujRozszerzoneWyszukiwanieGlobalne, { once: true });
} else {
  inicjalizujRozszerzoneWyszukiwanieGlobalne();
}
