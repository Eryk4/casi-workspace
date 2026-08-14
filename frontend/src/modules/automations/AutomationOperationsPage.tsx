"use client";

import Link from "next/link";
import { RefreshCw, Workflow } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { useActiveOrganization } from "@/context/ActiveOrganizationContext";
import { api, withOrganizationQuery } from "@/lib/api";

import {
  AUTOMATION_OPERATIONS_FILTERS,
  automationActivityStatusLabel,
  automationAttentionCategoryLabel,
  automationConfigurationLabel,
  automationDescription,
  automationHealthLabel,
  automationNavigationLinks,
  automationRunLabel,
  automationTechnicalStatusLabel,
  automationTypeLabel,
  buildAutomationOperationsPresentationSummary,
  filterAutomationOperations,
  readAutomationActivity,
  readAutomationOperationsDashboard,
  type AutomationActivityResponse,
  type AutomationOperationsDashboard,
  type AutomationOperationsFilter,
} from "./automationOperationsModel";

function dateTime(value: string | null): string {
  return value ? new Date(value).toLocaleString("pl-PL") : "—";
}

export function AutomationOperationsPage() {
  const { selectedOrganizationId, status: organizationStatus } = useActiveOrganization();
  const [dashboard, setDashboard] = useState<AutomationOperationsDashboard | null>(null);
  const [activity, setActivity] = useState<AutomationActivityResponse | null>(null);
  const [filter, setFilter] = useState<AutomationOperationsFilter>("all");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activityLoading, setActivityLoading] = useState(false);
  const [activityError, setActivityError] = useState(false);
  const requestVersion = useRef(0);
  const activityRequestVersion = useRef(0);
  const organizationRef = useRef(selectedOrganizationId);
  organizationRef.current = selectedOrganizationId;

  const loadDashboard = useCallback(async () => {
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

  const loadActivity = useCallback(async () => {
    const organizationId = selectedOrganizationId;
    const version = ++activityRequestVersion.current;
    setActivity(null);
    setActivityError(false);
    if (organizationStatus !== "ready" || !organizationId) return;
    setActivityLoading(true);
    try {
      const payload = await api.automationOperationsActivity(withOrganizationQuery(organizationId, { limit: 8 }));
      const nextActivity = readAutomationActivity(payload);
      if (version !== activityRequestVersion.current || organizationId !== organizationRef.current) return;
      setActivity(nextActivity);
    } catch {
      if (version === activityRequestVersion.current && organizationId === organizationRef.current) setActivityError(true);
    } finally {
      if (version === activityRequestVersion.current) setActivityLoading(false);
    }
  }, [organizationStatus, selectedOrganizationId]);

  const loadAll = useCallback(() => {
    void loadDashboard();
    void loadActivity();
  }, [loadActivity, loadDashboard]);

  useEffect(() => {
    requestVersion.current += 1;
    activityRequestVersion.current += 1;
    setDashboard(null);
    setActivity(null);
    setError(null);
    setActivityError(false);
    loadAll();
  }, [loadAll]);

  if (organizationStatus === "ready" && !selectedOrganizationId) {
    return <section className="empty-state"><h2>Wybierz organizację</h2><p>Centrum automatyzacji pokazuje stan jednej organizacji i zalogowanego użytkownika.</p></section>;
  }

  const items = filterAutomationOperations(dashboard?.items ?? [], filter);
  const summary = buildAutomationOperationsPresentationSummary(dashboard?.items ?? []);

  return (
    <section className="automation-operations" aria-labelledby="automation-operations-title">
      <header className="automation-operations__header">
        <div>
          <span className="eyebrow">Operacyjne centrum</span>
          <h2 id="automation-operations-title">Automatyzacje</h2>
          <p>Status harmonogramów i procesów automatycznych CASI Workspace. Ten widok jest wyłącznie do odczytu.</p>
        </div>
        <button className="button" disabled={(loading || activityLoading) || !selectedOrganizationId} onClick={loadAll} type="button">
          <RefreshCw aria-hidden="true" size={16} /> {loading || activityLoading ? "Odświeżanie..." : "Odśwież"}
        </button>
      </header>

      {dashboard ? (
        <div className="automation-summary" aria-label="Podsumowanie automatyzacji">
          <div><span>Aktywne</span><strong>{summary.activeCount}</strong></div>
          <div><span>Nieskonfigurowane</span><strong>{summary.notConfiguredCount}</strong></div>
          <div><span>Wyłączone</span><strong>{summary.disabledCount}</strong></div>
          <div><span>Wymagają uwagi</span><strong>{summary.attentionCount}</strong></div>
        </div>
      ) : null}

      {dashboard ? (
        <section className={dashboard.attentionItems.length === 0 ? "automation-attention automation-attention--empty" : "automation-attention"} aria-labelledby="automation-attention-title">
          <div className="automation-attention__heading">
            <div>
              <h3 id="automation-attention-title">Wymaga uwagi</h3>
              <p>Ostatnie znane sygnały, które warto sprawdzić.</p>
            </div>
            <span className="badge badge--attention">{dashboard.attentionItems.length}</span>
          </div>
          {dashboard.attentionItems.length === 0 ? (
            <p className="automation-attention__empty">Brak sygnałów wymagających uwagi.</p>
          ) : (
            <div className="automation-attention__list">
              {dashboard.attentionItems.map((item) => (
                <article className="automation-attention__item" key={item.automationKey}>
                  <div className="automation-attention__content">
                    <span className="automation-attention__category">{automationAttentionCategoryLabel(item.attentionCategory)}</span>
                    <h4>{item.title}</h4>
                    <p>{item.summary}</p>
                    <time dateTime={item.occurredAt ?? undefined}>{item.occurredAt ? dateTime(item.occurredAt) : "Czas niedostępny"}</time>
                  </div>
                  <div className="automation-attention__links">
                    <Link href={item.detailsUrl}>Zobacz szczegóły</Link>
                    {automationNavigationLinks(item.automationKey).map((link) => <Link href={link.href} key={link.href}>{link.label}</Link>)}
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      ) : null}

      <section className="automation-activity" aria-labelledby="automation-activity-title">
        <div className="automation-activity__heading">
          <div><h3 id="automation-activity-title">Ostatnia aktywność</h3><p>Zakończone działania automatyzacji w bieżącej organizacji.</p></div>
        </div>
        {activityLoading ? <div className="loading-state" role="status">Ładowanie ostatniej aktywności...</div> : null}
        {!activityLoading && activityError ? <div className="error-state" role="alert"><strong>Nie udało się pobrać ostatniej aktywności.</strong><button className="button" onClick={() => void loadActivity()} type="button">Spróbuj ponownie</button></div> : null}
        {!activityLoading && !activityError && activity && activity.items.length === 0 ? <p className="automation-activity__empty">Brak ostatniej aktywności.</p> : null}
        {!activityLoading && !activityError && activity && activity.items.length > 0 ? (
          <div className="automation-activity__list">
            {activity.items.map((item) => (
              <article className="automation-activity__item" data-status={item.status} key={item.activityId}>
                <div className="automation-activity__content">
                  <div className="automation-activity__title-row"><h4>{item.title}</h4><span className={"badge badge--activity-" + item.status}>{automationActivityStatusLabel(item.status)}</span></div>
                  <p>{item.summary}</p>
                  <time dateTime={item.occurredAt}>{dateTime(item.occurredAt)}</time>
                </div>
                <Link href={item.detailsUrl}>Zobacz szczegóły</Link>
              </article>
            ))}
          </div>
        ) : null}
      </section>

      <div className="automation-filters" role="group" aria-label="Filtry automatyzacji">
        {AUTOMATION_OPERATIONS_FILTERS.map((option) => (
          <button aria-pressed={filter === option.id} className={filter === option.id ? "filter-chip filter-chip--active" : "filter-chip"} key={option.id} onClick={() => setFilter(option.id)} type="button">
            {option.label}
          </button>
        ))}
      </div>

      {loading ? <div className="loading-state" role="status">Ładowanie stanu automatyzacji...</div> : null}
      {!loading && error ? <div className="error-state" role="alert"><strong>Nie udało się pobrać automatyzacji</strong><p>{error}</p><button className="button" onClick={() => void loadDashboard()} type="button">Spróbuj ponownie</button></div> : null}
      {!loading && !error && dashboard && items.length === 0 ? <div className="empty-state"><Workflow aria-hidden="true" size={22} /><h3>Brak automatyzacji</h3><p>Żadna automatyzacja nie odpowiada wybranemu filtrowi.</p></div> : null}

      {!loading && !error && items.length > 0 ? (
        <div className="automation-grid">
          {items.map((item) => (
            <article className="automation-card" data-health={item.health} key={item.automationKey}>
              <div className="automation-card__heading"><div><span className="eyebrow">{automationTypeLabel(item.automationType)}</span><h3>{item.title}</h3></div><span className={`badge badge--${item.health}`}>{automationHealthLabel(item.health)}</span></div>
              <p>{automationDescription(item)}</p>
              <dl>
                <div><dt>Konfiguracja</dt><dd>{automationConfigurationLabel(item.status)}</dd></div>
                {item.automationType === "automation_engine" ? <>
                  <div><dt>Aktywne / wyłączone reguły</dt><dd>{item.enabledRulesCount} / {item.disabledRulesCount}</dd></div>
                  <div><dt>Ostatnie wykonanie</dt><dd>{dateTime(item.lastRunAt)}</dd></div>
                  <div><dt>Ostatni wynik</dt><dd>{automationRunLabel(item.lastRunStatus)}</dd></div>
                  <div><dt>Udane / błędne wykonania</dt><dd>{item.succeededCount} / {item.failedCount}</dd></div>
                </> : item.automationType === "ksef_import" ? <>
                  <div><dt>Ostatnie uruchomienie</dt><dd>{dateTime(item.lastRunAt)}</dd></div>
                  <div><dt>Ostatni wynik</dt><dd>{automationRunLabel(item.lastRunStatus)}</dd></div>
                  <div><dt>Sprawdzone dokumenty</dt><dd>{item.checkedDocumentCount}</dd></div>
                  <div><dt>Zaimportowane / duplikaty / błędy</dt><dd>{item.importedCount} / {item.duplicateCount} / {item.failedCount}</dd></div>
                  <div><dt>Skonfigurowane połączenia</dt><dd>{item.configuredConnectionsCount}</dd></div>
                </> : item.automationType === "email_import" ? <>
                  <div><dt>Ostatnie uruchomienie</dt><dd>{dateTime(item.lastRunAt)}</dd></div>
                  <div><dt>Ostatni wynik</dt><dd>{automationRunLabel(item.lastRunStatus)}</dd></div>
                  <div><dt>Sprawdzone / dopasowane wiadomości</dt><dd>{item.checkedMessageCount} / {item.matchedMessageCount}</dd></div>
                  <div><dt>Zaimportowane / duplikaty / błędy</dt><dd>{item.importedCount} / {item.duplicateCount} / {item.failedCount}</dd></div>
                  <div><dt>Skonfigurowane połączenia</dt><dd>{item.configuredConnectionsCount}</dd></div>
                </> : item.automationType === "task_reminders" ? <>
                  <div><dt>Ostatnia aktywność</dt><dd>{dateTime(item.lastActivityAt)}</dd></div>
                  <div><dt>Ostatnia próba</dt><dd>{dateTime(item.lastAttemptAt)} · {automationTechnicalStatusLabel(item.lastAttemptStatus)}</dd></div>
                  <div><dt>Kolejka / przetwarzane</dt><dd>{item.pendingCount} / {item.processingCount}</dd></div>
                  <div><dt>Wysłane / błędy</dt><dd>{item.sentCount} / {item.failedCount}</dd></div>
                </> : item.automationType === "knowledge_processing" ? <>
                  <div><dt>Ostatnia aktywność</dt><dd>{dateTime(item.lastActivityAt)}</dd></div>
                  <div><dt>Ostatnie zadanie przetwarzania</dt><dd>{dateTime(item.lastJobAt)} · {automationTechnicalStatusLabel(item.lastJobStatus)}</dd></div>
                  <div><dt>Oczekujące / przetwarzane</dt><dd>{item.pendingCount} / {item.processingCount}</dd></div>
                  <div><dt>Zakończone / nieudane</dt><dd>{item.succeededCount} / {item.failedCount}</dd></div>
                  <div><dt>Obserwowane foldery / ostatni skan</dt><dd>{item.watcherCount} / {dateTime(item.lastScanAt)}</dd></div>
                </> : <>
                  <div><dt>Następne uruchomienie</dt><dd>{dateTime(item.nextRunAt)}</dd></div>
                  <div><dt>Ostatnie uruchomienie</dt><dd>{dateTime(item.lastRunAt)}</dd></div>
                  <div><dt>Ostatni wynik</dt><dd>{automationRunLabel(item.lastRunStatus)}</dd></div>
                  <div><dt>Utworzone / istniejące</dt><dd>{item.lastCreatedCount ?? "—"} / {item.lastExistingCount ?? "—"}</dd></div>
                </>}
              </dl>
              {item.lastErrorSummary ? <p className="automation-card__error">{item.lastErrorSummary}</p> : null}
              <div className="automation-card__links"><Link href={item.detailsUrl}>Zobacz szczegóły</Link>{automationNavigationLinks(item.automationKey).map((link) => <Link href={link.href} key={link.href}>{link.label}</Link>)}</div>
            </article>
          ))}
        </div>
      ) : null}
    </section>
  );
}
