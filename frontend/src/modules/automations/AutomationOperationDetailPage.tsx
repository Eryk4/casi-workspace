"use client";

import Link from "next/link";
import { ArrowLeft, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { useActiveOrganization } from "@/context/ActiveOrganizationContext";
import { ApiError, api, withOrganizationQuery } from "@/lib/api";

import {
  automationConfigurationLabel,
  automationDescription,
  automationHealthLabel,
  automationKnowledgeJobTypeLabel,
  automationNavigationLinks,
  automationRunLabel,
  automationScheduleCadenceLabel,
  automationTechnicalStatusLabel,
  automationTypeLabel,
  automationWatcherModeLabel,
  emailImportResultLabel,
  emailImportTriggerLabel,
  ksefImportResultLabel,
  readAutomationOperationDetail,
  type AutomationOperationDetail,
} from "./automationOperationsModel";

type Props = { automationKey: string };

function dateTime(value: string | null): string {
  return value ? new Date(value).toLocaleString("pl-PL") : "—";
}

export function AutomationOperationDetailPage({ automationKey }: Props) {
  const { selectedOrganizationId, status: organizationStatus } = useActiveOrganization();
  const [detail, setDetail] = useState<AutomationOperationDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const requestVersion = useRef(0);
  const organizationRef = useRef(selectedOrganizationId);
  organizationRef.current = selectedOrganizationId;

  const load = useCallback(async () => {
    const organizationId = selectedOrganizationId;
    const version = ++requestVersion.current;
    setDetail(null);
    setError(null);
    setNotFound(false);
    if (organizationStatus !== "ready" || !organizationId) return;
    setLoading(true);
    try {
      const payload = await api.automationOperationDetail(automationKey, withOrganizationQuery(organizationId, { limit: 20 }));
      const nextDetail = readAutomationOperationDetail(payload);
      if (version !== requestVersion.current || organizationId !== organizationRef.current) return;
      setDetail(nextDetail);
    } catch (nextError) {
      if (version !== requestVersion.current) return;
      if (nextError instanceof ApiError && nextError.status === 404) setNotFound(true);
      else setError(nextError instanceof Error ? nextError.message : "Nie udało się pobrać szczegółów automatyzacji.");
    } finally {
      if (version === requestVersion.current) setLoading(false);
    }
  }, [automationKey, organizationStatus, selectedOrganizationId]);

  useEffect(() => {
    requestVersion.current += 1;
    setDetail(null);
    setError(null);
    setNotFound(false);
    void load();
  }, [load]);

  if (organizationStatus === "ready" && !selectedOrganizationId) return <section className="empty-state"><h2>Wybierz organizację</h2><p>Szczegóły są dostępne w zakresie jednej organizacji.</p></section>;

  return (
    <section className="automation-operations" aria-labelledby="automation-detail-title">
      <header className="automation-operations__header"><div><Link href="/automatyzacje"><ArrowLeft aria-hidden="true" size={15} /> Wróć do automatyzacji</Link><h2 id="automation-detail-title">{detail?.item.title ?? "Szczegóły automatyzacji"}</h2><p>Konfiguracja i historia ostatnich wykonań — wyłącznie do odczytu.</p></div><button className="button" disabled={loading || !selectedOrganizationId} onClick={() => void load()} type="button"><RefreshCw aria-hidden="true" size={16} /> {loading ? "Odświeżanie..." : "Odśwież"}</button></header>
      {loading ? <div className="loading-state" role="status">Ładowanie szczegółów automatyzacji...</div> : null}
      {!loading && notFound ? <div className="empty-state"><h3>Nie znaleziono automatyzacji</h3><p>Ten klucz nie jest dostępny w rejestrze centrum operacyjnego.</p><Link href="/automatyzacje">Wróć do listy</Link></div> : null}
      {!loading && error ? <div className="error-state" role="alert"><strong>Nie udało się pobrać szczegółów</strong><p>{error}</p><button className="button" onClick={() => void load()} type="button">Spróbuj ponownie</button></div> : null}
      {!loading && !error && detail ? (
        <>
          <article className="automation-detail-card">
            <div className="automation-card__heading"><div><span className="eyebrow">{automationTypeLabel(detail.item.automationType)}</span><h3>{detail.item.title}</h3></div><span className={`badge badge--${detail.item.health}`}>{automationHealthLabel(detail.item.health)}</span></div>
            <p>{automationDescription(detail.item)}</p>
            <dl className="automation-detail-grid">
              <div><dt>Stan konfiguracji</dt><dd>{automationConfigurationLabel(detail.item.status)}</dd></div><div><dt>Monitoring procesu</dt><dd>Brak monitoringu procesu</dd><small>System nie ma sygnału procesu pozwalającego wiarygodnie określić, czy jest on obecnie aktywny.</small></div>
              {detail.item.automationType === "automation_engine" ? <>
                <div><dt>Reguły łącznie</dt><dd>{detail.item.totalRulesCount}</dd></div><div><dt>Aktywne / wyłączone</dt><dd>{detail.item.enabledRulesCount} / {detail.item.disabledRulesCount}</dd></div>
                <div><dt>Ostatnia aktywność</dt><dd>{dateTime(detail.item.lastActivityAt)}</dd></div><div><dt>Ostatnie wykonanie</dt><dd>{dateTime(detail.item.lastRunAt)}</dd></div>
                <div><dt>Ostatni sukces</dt><dd>{dateTime(detail.item.lastSuccessAt)}</dd></div><div><dt>Ostatni błąd</dt><dd>{dateTime(detail.item.lastFailureAt)}</dd></div>
                <div><dt>Wykonania łącznie</dt><dd>{detail.item.executionsCount}</dd></div><div><dt>Udane / błędne</dt><dd>{detail.item.succeededCount} / {detail.item.failedCount}</dd></div>
              </> : detail.item.automationType === "ksef_import" ? <>
                <div><dt>Skonfigurowane połączenia</dt><dd>{detail.item.configuredConnectionsCount}</dd></div><div><dt>Ostatnia aktywność</dt><dd>{dateTime(detail.item.lastActivityAt)}</dd></div>
                <div><dt>Ostatni sukces</dt><dd>{dateTime(detail.item.lastSuccessAt)}</dd></div><div><dt>Ostatni błąd</dt><dd>{dateTime(detail.item.lastFailureAt)}</dd></div>
                <div><dt>Sprawdzone dokumenty</dt><dd>{detail.item.checkedDocumentCount}</dd></div><div><dt>Liczba uruchomień</dt><dd>{detail.item.runsCount}</dd></div>
                <div><dt>Zaimportowane / duplikaty / błędy</dt><dd>{detail.item.importedCount} / {detail.item.duplicateCount} / {detail.item.failedCount}</dd></div>
              </> : detail.item.automationType === "email_import" ? <>
                <div><dt>Skonfigurowane połączenia</dt><dd>{detail.item.configuredConnectionsCount}</dd></div><div><dt>Ostatnia aktywność</dt><dd>{dateTime(detail.item.lastActivityAt)}</dd></div>
                <div><dt>Ostatni sukces</dt><dd>{dateTime(detail.item.lastSuccessAt)}</dd></div><div><dt>Ostatni błąd</dt><dd>{dateTime(detail.item.lastFailureAt)}</dd></div>
                <div><dt>Sprawdzone / dopasowane wiadomości</dt><dd>{detail.item.checkedMessageCount} / {detail.item.matchedMessageCount}</dd></div><div><dt>Dopasowane załączniki</dt><dd>{detail.item.matchedAttachmentCount}</dd></div>
                <div><dt>Zaimportowane / duplikaty / błędy</dt><dd>{detail.item.importedCount} / {detail.item.duplicateCount} / {detail.item.failedCount}</dd></div><div><dt>Liczba uruchomień</dt><dd>{detail.item.runsCount}</dd></div>
              </> : detail.item.automationType === "task_reminders" ? <>
                <div><dt>Powód wyłączenia</dt><dd>{detail.item.disabledReason ?? "—"}</dd></div><div><dt>Ostatnia aktywność</dt><dd>{dateTime(detail.item.lastActivityAt)}</dd></div>
                <div><dt>Ostatnia próba</dt><dd>{dateTime(detail.item.lastAttemptAt)} · {automationTechnicalStatusLabel(detail.item.lastAttemptStatus)}</dd></div><div><dt>Ostatni sygnał procesu</dt><dd>{dateTime(detail.item.lastHeartbeatAt)} (informacyjnie)</dd></div>
                <div><dt>Oczekujące / przetwarzane</dt><dd>{detail.item.pendingCount} / {detail.item.processingCount}</dd></div><div><dt>Wysłane / nieudane / anulowane</dt><dd>{detail.item.sentCount} / {detail.item.failedCount} / {detail.item.cancelledCount}</dd></div>
              </> : detail.item.automationType === "knowledge_processing" ? <>
                <div><dt>Ostatnia aktywność</dt><dd>{dateTime(detail.item.lastActivityAt)}</dd></div><div><dt>Ostatnie zadanie przetwarzania</dt><dd>{dateTime(detail.item.lastJobAt)} · {automationTechnicalStatusLabel(detail.item.lastJobStatus)}</dd></div>
                <div><dt>Ostatni sukces</dt><dd>{dateTime(detail.item.lastSuccessAt)}</dd></div><div><dt>Ostatni błąd</dt><dd>{dateTime(detail.item.lastFailureAt)}</dd></div>
                <div><dt>Oczekujące / przetwarzane</dt><dd>{detail.item.pendingCount} / {detail.item.processingCount}</dd></div><div><dt>Zakończone / nieudane</dt><dd>{detail.item.succeededCount} / {detail.item.failedCount}</dd></div>
                <div><dt>Obserwowane foldery</dt><dd>{detail.item.watcherCount}</dd></div><div><dt>Ostatni skan</dt><dd>{dateTime(detail.item.lastScanAt)} · {automationTechnicalStatusLabel(detail.item.lastScanStatus)}</dd></div>
              </> : <>
                <div><dt>Harmonogram</dt><dd>{automationScheduleCadenceLabel(detail.item.schedule?.cadence)}, {detail.item.schedule?.localTime}</dd></div><div><dt>Strefa czasowa</dt><dd>{detail.item.schedule?.timezoneName}</dd></div>
                <div><dt>Następne uruchomienie</dt><dd>{dateTime(detail.item.nextRunAt)}</dd></div><div><dt>Ostatnie uruchomienie</dt><dd>{dateTime(detail.item.lastRunAt)}</dd></div>
                <div><dt>Czas ostatniego uruchomienia</dt><dd>{detail.item.lastRunDurationMs === null ? "—" : `${detail.item.lastRunDurationMs} ms`}</dd></div><div><dt>Próba</dt><dd>{detail.item.lastAttemptCount ?? "—"}</dd></div>
                <div><dt>Kandydaci</dt><dd>{detail.item.lastCandidatesCount ?? "—"}</dd></div><div><dt>Nowe / istniejące</dt><dd>{detail.item.lastCreatedCount ?? "—"} / {detail.item.lastExistingCount ?? "—"}</dd></div>
              </>}
            </dl>
            {detail.item.lastErrorSummary ? <p className="automation-card__error">{!(["email_import", "ksef_import"].includes(detail.item.automationType)) && detail.item.lastErrorCode ? `${detail.item.lastErrorCode}: ` : ""}{detail.item.lastErrorSummary}</p> : null}
            <div className="automation-card__links">{automationNavigationLinks(detail.item.automationKey).map((link) => <Link href={link.href} key={link.href}>{link.label}</Link>)}</div>
          </article>
          {detail.item.automationType === "automation_engine" ? <section className="automation-history"><h3>Reguły</h3>{detail.rules.length === 0 ? <div className="empty-state"><p>Brak reguł automatyzacji.</p></div> : <div className="table-shell"><table><thead><tr><th>ID</th><th>Nazwa</th><th>Stan</th><th>Wykonania</th><th>Utworzono</th><th>Zaktualizowano</th></tr></thead><tbody>{detail.rules.map((rule) => <tr key={rule.ruleId}><td>{rule.ruleId}</td><td>{rule.title}</td><td>{rule.enabled ? "Włączona" : "Wyłączona"}</td><td>{rule.executionCount}</td><td>{dateTime(rule.createdAt)}</td><td>{dateTime(rule.updatedAt)}</td></tr>)}</tbody></table></div>}</section> : null}
          <section className="automation-history" aria-labelledby="automation-history-title"><h3 id="automation-history-title">{detail.item.automationType === "automation_engine" ? "Ostatnie wykonania" : detail.item.automationType === "task_reminders" ? "Ostatnie próby" : detail.item.automationType === "knowledge_processing" ? "Ostatnie zadania przetwarzania" : "Historia ostatnich uruchomień"}</h3>
            {detail.history.length === 0 ? <div className="empty-state"><h4>Brak uruchomień</h4><p>Automatyzacja nie ma jeszcze zapisanej historii.</p></div> : (
              <div className="table-shell"><table><thead><tr>{detail.item.automationType === "automation_engine" ? <><th>ID</th><th>Reguła</th><th>Czas</th><th>Status</th><th>Błąd</th></> : detail.item.automationType === "task_reminders" ? <><th>Czas</th><th>Status</th><th>Próba</th><th>Kanał</th><th>Błąd</th></> : detail.item.automationType === "knowledge_processing" ? <><th>ID</th><th>Typ</th><th>Utworzono</th><th>Start</th><th>Koniec</th><th>Status</th><th>Próba</th><th>Czas</th><th>Błąd</th></> : detail.item.automationType === "email_import" ? <><th>ID</th><th>Tryb</th><th>Start</th><th>Koniec</th><th>Wynik</th><th>Wiadomości</th><th>Importy</th><th>Duplikaty</th><th>Błędy</th></> : detail.item.automationType === "ksef_import" ? <><th>ID</th><th>Tryb</th><th>Start</th><th>Koniec</th><th>Wynik</th><th>Dokumenty</th><th>Importy</th><th>Duplikaty</th><th>Błędy</th></> : <><th>Plan</th><th>Start</th><th>Koniec</th><th>Status</th><th>Próba</th><th>Kandydaci</th><th>Nowe</th><th>Istniejące</th><th>Czas</th><th>Błąd</th></>}</tr></thead><tbody>{detail.history.map((entry) => entry.historyType === "automation_execution" ? <tr key={`execution-${entry.executionId}`}><td>{entry.executionId}</td><td>Reguła #{entry.ruleId}</td><td>{dateTime(entry.executedAt)}</td><td>{automationRunLabel(entry.status)}</td><td>{entry.errorSummary ?? "—"}</td></tr> : entry.historyType === "reminder_attempt" ? <tr key={`attempt-${entry.attemptId}`}><td>{dateTime(entry.attemptedAt)}</td><td>{automationTechnicalStatusLabel(entry.status)}</td><td>{entry.attemptNo}</td><td>{entry.channel}</td><td>{entry.errorSummary ?? "—"}</td></tr> : entry.historyType === "knowledge_job" ? <tr key={`knowledge-${entry.jobId}`}><td>{entry.jobId}</td><td>{automationKnowledgeJobTypeLabel(entry.jobType)}</td><td>{dateTime(entry.createdAt)}</td><td>{dateTime(entry.startedAt)}</td><td>{dateTime(entry.finishedAt)}</td><td>{automationTechnicalStatusLabel(entry.status)}</td><td>{entry.attemptCount} / {entry.maxAttempts}</td><td>{entry.durationMs === null ? "—" : `${entry.durationMs} ms`}</td><td>{entry.errorSummary ?? "—"}</td></tr> : entry.historyType === "email_import_run" ? <tr key={`email-${entry.runId}`}><td>{entry.runId}</td><td>{emailImportTriggerLabel(entry.triggerMode)}</td><td>{dateTime(entry.startedAt)}</td><td>{dateTime(entry.finishedAt)}</td><td>{emailImportResultLabel(entry.resultStatus)}</td><td>{entry.checkedMessageCount}</td><td>{entry.importedCount}</td><td>{entry.duplicateCount}</td><td>{entry.failedCount}</td></tr> : entry.historyType === "ksef_import_run" ? <tr key={`ksef-${entry.runId}`}><td>{entry.runId}</td><td>{emailImportTriggerLabel(entry.triggerMode)}</td><td>{dateTime(entry.startedAt)}</td><td>{dateTime(entry.finishedAt)}</td><td>{ksefImportResultLabel(entry.resultStatus)}</td><td>{entry.checkedDocumentCount}</td><td>{entry.importedCount}</td><td>{entry.duplicateCount}</td><td>{entry.failedCount}</td></tr> : <tr key={entry.runId}><td>{dateTime(entry.scheduledForUtc)}</td><td>{dateTime(entry.startedAt)}</td><td>{dateTime(entry.finishedAt)}</td><td>{automationRunLabel(entry.status)}</td><td>{entry.attemptCount}</td><td>{entry.candidatesCount ?? "—"}</td><td>{entry.createdCount ?? "—"}</td><td>{entry.existingCount ?? "—"}</td><td>{entry.durationMs === null ? "—" : `${entry.durationMs} ms`}</td><td>{entry.errorSummary ?? "—"}</td></tr>)}</tbody></table></div>
            )}
          </section>
          {detail.item.automationType === "task_reminders" ? <section className="automation-history"><h3>Ostatnie wpisy kolejki</h3>{detail.outbox.length === 0 ? <div className="empty-state"><p>Kolejka jest pusta.</p></div> : <div className="table-shell"><table><thead><tr><th>ID</th><th>Status</th><th>Kanał</th><th>Dostępne od</th><th>Próby</th></tr></thead><tbody>{detail.outbox.map((item) => <tr key={item.outboxId}><td>{item.outboxId}</td><td>{automationTechnicalStatusLabel(item.status)}</td><td>{item.channel}</td><td>{dateTime(item.availableAt)}</td><td>{item.attemptCount}</td></tr>)}</tbody></table></div>}</section> : null}
          {detail.item.automationType === "knowledge_processing" ? <section className="automation-history"><h3>Obserwowane foldery</h3>{detail.watchers.length === 0 ? <div className="empty-state"><p>Brak zapisanej historii skanowania folderu.</p></div> : <div className="table-shell"><table><thead><tr><th>ID</th><th>Tryb</th><th>Status</th><th>Start skanu</th><th>Koniec skanu</th><th>Błąd</th></tr></thead><tbody>{detail.watchers.map((watcher) => <tr key={watcher.watcherId}><td>{watcher.watcherId}</td><td>{automationWatcherModeLabel(watcher.watchMode)}</td><td>{automationTechnicalStatusLabel(watcher.status)}</td><td>{dateTime(watcher.lastScanStartedAt)}</td><td>{dateTime(watcher.lastScanCompletedAt)}</td><td>{watcher.errorSummary ?? "—"}</td></tr>)}</tbody></table></div>}</section> : null}
        </>
      ) : null}
    </section>
  );
}
