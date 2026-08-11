"use client";

import Link from "next/link";
import { RefreshCw, Workflow } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { useActiveOrganization } from "@/context/ActiveOrganizationContext";
import { api, withOrganizationQuery } from "@/lib/api";

import {
  AUTOMATION_OPERATIONS_FILTERS,
  automationConfigurationLabel,
  automationHealthLabel,
  automationRunLabel,
  automationTypeLabel,
  filterAutomationOperations,
  readAutomationOperationsDashboard,
  type AutomationOperationsDashboard,
  type AutomationOperationsFilter,
} from "./automationOperationsModel";

function dateTime(value: string | null): string {
  return value ? new Date(value).toLocaleString("pl-PL") : "—";
}

export function AutomationOperationsPage() {
  const { selectedOrganizationId, status: organizationStatus } = useActiveOrganization();
  const [dashboard, setDashboard] = useState<AutomationOperationsDashboard | null>(null);
  const [filter, setFilter] = useState<AutomationOperationsFilter>("all");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const requestVersion = useRef(0);
  const organizationRef = useRef(selectedOrganizationId);
  organizationRef.current = selectedOrganizationId;

  const load = useCallback(async () => {
    const organizationId = selectedOrganizationId;
    const version = ++requestVersion.current;
    setDashboard(null);
    setError(null);
    if (organizationStatus !== "ready" || !organizationId) return;
    setLoading(true);
    try {
      const payload = await api.automationOperations(withOrganizationQuery(organizationId));
      const nextDashboard = readAutomationOperationsDashboard(payload);
      if (version !== requestVersion.current || organizationId !== organizationRef.current) return;
      setDashboard(nextDashboard);
    } catch (nextError) {
      if (version === requestVersion.current) {
        setError(nextError instanceof Error ? nextError.message : "Nie udało się pobrać stanu automatyzacji.");
      }
    } finally {
      if (version === requestVersion.current) setLoading(false);
    }
  }, [organizationStatus, selectedOrganizationId]);

  useEffect(() => {
    requestVersion.current += 1;
    setDashboard(null);
    setError(null);
    void load();
  }, [load]);

  if (organizationStatus === "ready" && !selectedOrganizationId) {
    return <section className="empty-state"><h2>Wybierz organizację</h2><p>Centrum automatyzacji pokazuje stan jednej organizacji i zalogowanego użytkownika.</p></section>;
  }

  const items = filterAutomationOperations(dashboard?.items ?? [], filter);

  return (
    <section className="automation-operations" aria-labelledby="automation-operations-title">
      <header className="automation-operations__header">
        <div>
          <span className="eyebrow">Operacyjne centrum</span>
          <h2 id="automation-operations-title">Automatyzacje</h2>
          <p>Status harmonogramów i procesów automatycznych CASI Workspace. Ten widok jest wyłącznie do odczytu.</p>
        </div>
        <button className="button" disabled={loading || !selectedOrganizationId} onClick={() => void load()} type="button">
          <RefreshCw aria-hidden="true" size={16} /> {loading ? "Odświeżanie..." : "Odśwież"}
        </button>
      </header>

      {dashboard ? (
        <div className="automation-summary" aria-label="Podsumowanie automatyzacji">
          <div><span>Aktywne</span><strong>{dashboard.summary.activeCount}</strong></div>
          <div><span>Wyłączone</span><strong>{dashboard.summary.disabledCount}</strong></div>
          <div><span>Wymagają uwagi</span><strong>{dashboard.summary.attentionCount}</strong></div>
          <div><span>Ostatnie błędy</span><strong>{dashboard.summary.recentFailureCount}</strong></div>
        </div>
      ) : null}

      <div className="automation-filters" role="group" aria-label="Filtry automatyzacji">
        {AUTOMATION_OPERATIONS_FILTERS.map((option) => (
          <button aria-pressed={filter === option.id} className={filter === option.id ? "filter-chip filter-chip--active" : "filter-chip"} key={option.id} onClick={() => setFilter(option.id)} type="button">
            {option.label}
          </button>
        ))}
      </div>

      {loading ? <div className="loading-state" role="status">Ładowanie stanu automatyzacji...</div> : null}
      {!loading && error ? <div className="error-state" role="alert"><strong>Nie udało się pobrać automatyzacji</strong><p>{error}</p><button className="button" onClick={() => void load()} type="button">Spróbuj ponownie</button></div> : null}
      {!loading && !error && dashboard && items.length === 0 ? <div className="empty-state"><Workflow aria-hidden="true" size={22} /><h3>Brak automatyzacji</h3><p>Żadna automatyzacja nie odpowiada wybranemu filtrowi.</p></div> : null}

      {!loading && !error && items.length > 0 ? (
        <div className="automation-grid">
          {items.map((item) => (
            <article className="automation-card" data-health={item.health} key={item.automationKey}>
              <div className="automation-card__heading"><div><span className="eyebrow">{automationTypeLabel(item.automationType)}</span><h3>{item.title}</h3></div><span className={`badge badge--${item.health}`}>{automationHealthLabel(item.health)}</span></div>
              <p>{item.description}</p>
              <dl>
                <div><dt>Konfiguracja</dt><dd>{automationConfigurationLabel(item.status)}</dd></div>
                {item.automationType === "automation_engine" ? <>
                  <div><dt>Runtime</dt><dd>Nieznany</dd></div>
                  <div><dt>Aktywne / wyłączone reguły</dt><dd>{item.enabledRulesCount} / {item.disabledRulesCount}</dd></div>
                  <div><dt>Ostatnie wykonanie</dt><dd>{dateTime(item.lastRunAt)}</dd></div>
                  <div><dt>Ostatni wynik</dt><dd>{automationRunLabel(item.lastRunStatus)}</dd></div>
                  <div><dt>Udane / błędne wykonania</dt><dd>{item.succeededCount} / {item.failedCount}</dd></div>
                </> : item.automationType === "ksef_import" ? <>
                  <div><dt>Runtime</dt><dd>Nieznany</dd></div>
                  <div><dt>Ostatnie uruchomienie</dt><dd>{dateTime(item.lastRunAt)}</dd></div>
                  <div><dt>Ostatni wynik</dt><dd>{automationRunLabel(item.lastRunStatus)}</dd></div>
                  <div><dt>Sprawdzone dokumenty</dt><dd>{item.checkedDocumentCount}</dd></div>
                  <div><dt>Zaimportowane / duplikaty / błędy</dt><dd>{item.importedCount} / {item.duplicateCount} / {item.failedCount}</dd></div>
                  <div><dt>Skonfigurowane połączenia</dt><dd>{item.configuredConnectionsCount}</dd></div>
                </> : item.automationType === "email_import" ? <>
                  <div><dt>Runtime</dt><dd>Nieznany</dd></div>
                  <div><dt>Ostatnie uruchomienie</dt><dd>{dateTime(item.lastRunAt)}</dd></div>
                  <div><dt>Ostatni wynik</dt><dd>{automationRunLabel(item.lastRunStatus)}</dd></div>
                  <div><dt>Sprawdzone / dopasowane wiadomości</dt><dd>{item.checkedMessageCount} / {item.matchedMessageCount}</dd></div>
                  <div><dt>Zaimportowane / duplikaty / błędy</dt><dd>{item.importedCount} / {item.duplicateCount} / {item.failedCount}</dd></div>
                  <div><dt>Skonfigurowane połączenia</dt><dd>{item.configuredConnectionsCount}</dd></div>
                </> : item.automationType === "task_reminders" ? <>
                  <div><dt>Runtime</dt><dd>Nieznany</dd></div>
                  <div><dt>Ostatnia aktywność</dt><dd>{dateTime(item.lastActivityAt)}</dd></div>
                  <div><dt>Ostatnia próba</dt><dd>{dateTime(item.lastAttemptAt)} · {item.lastAttemptStatus ?? "—"}</dd></div>
                  <div><dt>Kolejka / przetwarzane</dt><dd>{item.pendingCount} / {item.processingCount}</dd></div>
                  <div><dt>Wysłane / błędy</dt><dd>{item.sentCount} / {item.failedCount}</dd></div>
                  <div><dt>Ostatni heartbeat</dt><dd>{dateTime(item.lastHeartbeatAt)} (informacyjnie)</dd></div>
                </> : item.automationType === "knowledge_processing" ? <>
                  <div><dt>Runtime</dt><dd>Nieznany</dd></div>
                  <div><dt>Ostatnia aktywność</dt><dd>{dateTime(item.lastActivityAt)}</dd></div>
                  <div><dt>Ostatni job</dt><dd>{dateTime(item.lastJobAt)} · {item.lastJobStatus ?? "—"}</dd></div>
                  <div><dt>Queued / processing</dt><dd>{item.pendingCount} / {item.processingCount}</dd></div>
                  <div><dt>Completed / failed</dt><dd>{item.succeededCount} / {item.failedCount}</dd></div>
                  <div><dt>Watchery / ostatni skan</dt><dd>{item.watcherCount} / {dateTime(item.lastScanAt)}</dd></div>
                </> : <>
                  <div><dt>Następne uruchomienie</dt><dd>{dateTime(item.nextRunAt)}</dd></div>
                  <div><dt>Ostatnie uruchomienie</dt><dd>{dateTime(item.lastRunAt)}</dd></div>
                  <div><dt>Ostatni wynik</dt><dd>{automationRunLabel(item.lastRunStatus)}</dd></div>
                  <div><dt>Utworzone / istniejące</dt><dd>{item.lastCreatedCount ?? "—"} / {item.lastExistingCount ?? "—"}</dd></div>
                </>}
              </dl>
              {item.lastErrorSummary ? <p className="automation-card__error">{item.lastErrorSummary}</p> : null}
              <div className="automation-card__links"><Link href={item.detailsUrl}>Szczegóły</Link>{item.settingsUrl ? <Link href={item.settingsUrl}>Ustawienia</Link> : null}</div>
            </article>
          ))}
        </div>
      ) : null}
    </section>
  );
}
