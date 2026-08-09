"use client";

import Link from "next/link";
import { ArrowLeft, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { useActiveOrganization } from "@/context/ActiveOrganizationContext";
import { ApiError, api, withOrganizationQuery } from "@/lib/api";

import { automationHealthLabel, automationRunLabel, readAutomationOperationDetail, type AutomationOperationDetail } from "./automationOperationsModel";

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
            <div className="automation-card__heading"><div><span className="eyebrow">{detail.item.automationType}</span><h3>{detail.item.title}</h3></div><span className={`badge badge--${detail.item.health}`}>{automationHealthLabel(detail.item.health)}</span></div>
            <p>{detail.item.description}</p>
            <dl className="automation-detail-grid">
              <div><dt>Stan konfiguracji</dt><dd>{detail.item.status}</dd></div><div><dt>Runtime</dt><dd>Nieznany — centrum nie monitoruje procesu workera</dd></div>
              <div><dt>Harmonogram</dt><dd>{detail.item.schedule.cadence}, {detail.item.schedule.localTime}</dd></div><div><dt>Strefa czasowa</dt><dd>{detail.item.schedule.timezoneName}</dd></div>
              <div><dt>Następne uruchomienie</dt><dd>{dateTime(detail.item.nextRunAt)}</dd></div><div><dt>Ostatnie uruchomienie</dt><dd>{dateTime(detail.item.lastRunAt)}</dd></div>
              <div><dt>Czas ostatniego runu</dt><dd>{detail.item.lastRunDurationMs === null ? "—" : `${detail.item.lastRunDurationMs} ms`}</dd></div><div><dt>Próba</dt><dd>{detail.item.lastAttemptCount ?? "—"}</dd></div>
              <div><dt>Kandydaci</dt><dd>{detail.item.lastCandidatesCount ?? "—"}</dd></div><div><dt>Nowe / istniejące</dt><dd>{detail.item.lastCreatedCount ?? "—"} / {detail.item.lastExistingCount ?? "—"}</dd></div>
            </dl>
            {detail.item.lastErrorSummary ? <p className="automation-card__error">{detail.item.lastErrorCode ? `${detail.item.lastErrorCode}: ` : ""}{detail.item.lastErrorSummary}</p> : null}
            <Link href={detail.item.settingsUrl}>Przejdź do ustawień</Link>
          </article>
          <section className="automation-history" aria-labelledby="automation-history-title"><h3 id="automation-history-title">Historia ostatnich uruchomień</h3>
            {detail.history.length === 0 ? <div className="empty-state"><h4>Brak uruchomień</h4><p>Automatyzacja nie ma jeszcze zapisanej historii.</p></div> : (
              <div className="table-shell"><table><thead><tr><th>Plan</th><th>Start</th><th>Koniec</th><th>Status</th><th>Próba</th><th>Kandydaci</th><th>Nowe</th><th>Istniejące</th><th>Czas</th><th>Błąd</th></tr></thead><tbody>{detail.history.map((run) => <tr key={run.runId}><td>{dateTime(run.scheduledForUtc)}</td><td>{dateTime(run.startedAt)}</td><td>{dateTime(run.finishedAt)}</td><td>{automationRunLabel(run.status)}</td><td>{run.attemptCount}</td><td>{run.candidatesCount ?? "—"}</td><td>{run.createdCount ?? "—"}</td><td>{run.existingCount ?? "—"}</td><td>{run.durationMs === null ? "—" : `${run.durationMs} ms`}</td><td>{run.errorSummary ?? "—"}</td></tr>)}</tbody></table></div>
            )}
          </section>
        </>
      ) : null}
    </section>
  );
}
