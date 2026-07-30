"use client";

import Link from "next/link";
import { Archive, Bell, Check, ChevronDown, RefreshCw, Undo2 } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { useActiveOrganization } from "@/context/ActiveOrganizationContext";
import { useInternalNotificationCount } from "@/context/InternalNotificationCountContext";
import { api, withOrganizationQuery } from "@/lib/api";

import {
  emptyStateCopy,
  INTERNAL_NOTIFICATION_FILTERS,
  readInternalNotificationPage,
  readInternalNotificationSchedule,
  readInternalNotificationScheduleRuns,
  readMaterializationResult,
  type InternalNotificationFilter,
  type InternalNotificationItem,
  type InternalNotificationScheduleRun,
} from "./internalNotificationsModel";

export function InternalNotificationsPage() {
  const { selectedOrganizationId, status: organizationStatus } = useActiveOrganization();
  const { refreshUnreadCount, unreadCount } = useInternalNotificationCount();
  const [filter, setFilter] = useState<InternalNotificationFilter>("inbox");
  const [items, setItems] = useState<InternalNotificationItem[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pendingActionId, setPendingActionId] = useState<number | null>(null);
  const [materializing, setMaterializing] = useState(false);
  const [resultMessage, setResultMessage] = useState<string | null>(null);
  const [scheduleScopeId, setScheduleScopeId] = useState<string | null>(null);
  const [scheduleEnabled, setScheduleEnabled] = useState(false);
  const [scheduleLocalTime, setScheduleLocalTime] = useState("08:00");
  const [scheduleTimezone, setScheduleTimezone] = useState("Europe/Warsaw");
  const [scheduleNextRun, setScheduleNextRun] = useState<string | null>(null);
  const [lastScheduleRun, setLastScheduleRun] = useState<InternalNotificationScheduleRun | null>(null);
  const [scheduleLoading, setScheduleLoading] = useState(false);
  const [scheduleSaving, setScheduleSaving] = useState(false);
  const [scheduleError, setScheduleError] = useState<string | null>(null);
  const [scheduleMessage, setScheduleMessage] = useState<string | null>(null);
  const requestVersion = useRef(0);
  const scheduleRequestVersion = useRef(0);
  const materializingRef = useRef(false);
  const scheduleSavingRef = useRef(false);
  const pendingActionRef = useRef(false);
  const selectedOrganizationRef = useRef(selectedOrganizationId);
  selectedOrganizationRef.current = selectedOrganizationId;

  const loadPage = useCallback(async (append: boolean, cursorOverride?: string | null) => {
    const organizationId = selectedOrganizationId;
    const version = ++requestVersion.current;
    if (organizationStatus !== "ready" || !organizationId) {
      setItems([]);
      setNextCursor(null);
      setHasMore(false);
      return;
    }
    append ? setLoadingMore(true) : setLoading(true);
    setError(null);
    try {
      const payload = await api.internalNotifications(
        withOrganizationQuery(organizationId, {
          filter,
          limit: 50,
          cursor: append ? cursorOverride ?? undefined : undefined,
        }),
      );
      const page = readInternalNotificationPage(payload);
      if (version !== requestVersion.current || organizationId !== selectedOrganizationRef.current) return;
      setItems((current) => {
        if (!append) return page.items;
        const knownIds = new Set(current.map((item) => item.id));
        return [...current, ...page.items.filter((item) => !knownIds.has(item.id))];
      });
      setNextCursor(page.nextCursor);
      setHasMore(page.hasMore);
    } catch (nextError) {
      if (version === requestVersion.current) {
        setError(nextError instanceof Error ? nextError.message : "Nie udało się pobrać powiadomień.");
      }
    } finally {
      if (version === requestVersion.current) {
        setLoading(false);
        setLoadingMore(false);
      }
    }
  }, [filter, organizationStatus, selectedOrganizationId]);

  const loadSchedule = useCallback(async () => {
    const organizationId = selectedOrganizationId;
    const version = ++scheduleRequestVersion.current;
    if (organizationStatus !== "ready" || !organizationId) {
      setScheduleScopeId(null);
      setLastScheduleRun(null);
      return;
    }
    setScheduleLoading(true);
    setScheduleError(null);
    try {
      const [settingsPayload, runsPayload] = await Promise.all([
        api.internalNotificationSchedule(withOrganizationQuery(organizationId)),
        api.internalNotificationScheduleRuns(withOrganizationQuery(organizationId, { limit: 20 })),
      ]);
      const settings = readInternalNotificationSchedule(settingsPayload);
      const runs = readInternalNotificationScheduleRuns(runsPayload);
      if (version !== scheduleRequestVersion.current || organizationId !== selectedOrganizationRef.current) return;
      setScheduleScopeId(organizationId);
      setScheduleEnabled(settings.enabled);
      setScheduleLocalTime(settings.localTime);
      setScheduleTimezone(settings.timezoneName);
      setScheduleNextRun(settings.nextRunAtUtc);
      setLastScheduleRun(runs[0] ?? null);
    } catch (nextError) {
      if (version === scheduleRequestVersion.current) {
        setScheduleScopeId(organizationId);
        setScheduleError(nextError instanceof Error ? nextError.message : "Nie udało się pobrać ustawień harmonogramu.");
      }
    } finally {
      if (version === scheduleRequestVersion.current) setScheduleLoading(false);
    }
  }, [organizationStatus, selectedOrganizationId]);

  useEffect(() => {
    requestVersion.current += 1;
    setItems([]);
    setNextCursor(null);
    setHasMore(false);
    setError(null);
    setResultMessage(null);
    void loadPage(false);
  }, [loadPage]);

  useEffect(() => {
    scheduleRequestVersion.current += 1;
    setScheduleScopeId(null);
    setScheduleEnabled(false);
    setScheduleLocalTime("08:00");
    setScheduleTimezone("Europe/Warsaw");
    setScheduleNextRun(null);
    setLastScheduleRun(null);
    setScheduleError(null);
    setScheduleMessage(null);
    void loadSchedule();
  }, [loadSchedule]);

  const materialize = async () => {
    if (!selectedOrganizationId || materializingRef.current) return;
    materializingRef.current = true;
    setMaterializing(true);
    setResultMessage(null);
    try {
      const payload = await api.materializeInternalNotifications(selectedOrganizationId);
      const result = readMaterializationResult(payload);
      if (selectedOrganizationId !== selectedOrganizationRef.current) return;
      setResultMessage(
        result.createdCount > 0
          ? `Utworzono ${result.createdCount} nowych powiadomień.`
          : "Brak nowych powiadomień — wszystkie aktualne sygnały są już zapisane.",
      );
      await Promise.all([loadPage(false), loadSchedule(), refreshUnreadCount()]);
    } catch (nextError) {
      setResultMessage(nextError instanceof Error ? nextError.message : "Nie udało się sprawdzić nowych powiadomień.");
    } finally {
      materializingRef.current = false;
      setMaterializing(false);
    }
  };

  const saveSchedule = async () => {
    const organizationId = selectedOrganizationId;
    if (!organizationId || scheduleSavingRef.current) return;
    scheduleSavingRef.current = true;
    setScheduleSaving(true);
    setScheduleError(null);
    setScheduleMessage(null);
    try {
      const payload = await api.saveInternalNotificationSchedule(
        {
          enabled: scheduleEnabled,
          local_time: scheduleLocalTime,
          timezone_name: scheduleTimezone,
          cadence: "daily",
        },
        organizationId,
      );
      const settings = readInternalNotificationSchedule(payload);
      if (organizationId !== selectedOrganizationRef.current) return;
      setScheduleScopeId(organizationId);
      setScheduleEnabled(settings.enabled);
      setScheduleLocalTime(settings.localTime);
      setScheduleTimezone(settings.timezoneName);
      setScheduleNextRun(settings.nextRunAtUtc);
      setScheduleMessage("Ustawienia automatycznego sprawdzania zostały zapisane.");
      await loadSchedule();
    } catch (nextError) {
      if (organizationId === selectedOrganizationRef.current) {
        setScheduleError(nextError instanceof Error ? nextError.message : "Nie udało się zapisać ustawień harmonogramu.");
      }
    } finally {
      scheduleSavingRef.current = false;
      setScheduleSaving(false);
    }
  };

  const changeState = async (item: InternalNotificationItem, action: "read" | "unread" | "archived") => {
    if (!selectedOrganizationId || pendingActionRef.current) return;
    pendingActionRef.current = true;
    setPendingActionId(item.id);
    setResultMessage(null);
    try {
      await api.updateInternalNotificationState(item.id, action, selectedOrganizationId);
      if (selectedOrganizationId !== selectedOrganizationRef.current) return;
      await Promise.all([loadPage(false), refreshUnreadCount()]);
    } catch (nextError) {
      setResultMessage(nextError instanceof Error ? nextError.message : "Nie udało się zmienić stanu powiadomienia.");
    } finally {
      pendingActionRef.current = false;
      setPendingActionId(null);
    }
  };

  if (organizationStatus === "ready" && !selectedOrganizationId) {
    return <section className="empty-state"><h2>Wybierz organizację</h2><p>Centrum powiadomień działa w zakresie jednej organizacji i zalogowanego odbiorcy.</p></section>;
  }

  const emptyCopy = emptyStateCopy(filter);

  return (
    <section className="notifications-page" aria-labelledby="notifications-title">
      <header className="notifications-page__header">
        <div>
          <span className="eyebrow">Wewnętrzne centrum</span>
          <h2 id="notifications-title">Powiadomienia</h2>
          <p>Trwałe sygnały dla wybranej organizacji i Twojego konta. Samo otwarcie strony niczego nie zapisuje.</p>
        </div>
        <div className="notifications-page__header-actions">
          <span className="notifications-page__unread">Nieprzeczytane: <strong>{unreadCount ?? "—"}</strong></span>
          <button className="button button--primary" disabled={!selectedOrganizationId || materializing} onClick={() => void materialize()} type="button">
            <RefreshCw aria-hidden="true" size={16} />
            {materializing ? "Sprawdzanie..." : "Sprawdź nowe powiadomienia"}
          </button>
          <small>Sprawdza zaległe i dzisiejsze kroki; nie wykonuje żadnych działań rozliczeniowych.</small>
        </div>
      </header>

      {resultMessage ? <div className="notifications-page__message" role="status">{resultMessage}</div> : null}

      <section className="notification-schedule" aria-labelledby="notification-schedule-title">
        <div className="notification-schedule__heading">
          <div>
            <span className="eyebrow">Scheduler v1</span>
            <h3 id="notification-schedule-title">Automatyczne sprawdzanie</h3>
          </div>
          <span className={scheduleEnabled && scheduleScopeId === selectedOrganizationId ? "badge badge--success" : "badge"}>
            {scheduleEnabled && scheduleScopeId === selectedOrganizationId ? "Włączone" : "Wyłączone"}
          </span>
        </div>
        <p>Automatyczne sprawdzanie tworzy wyłącznie brakujące wewnętrzne powiadomienia. Nie wysyła wiadomości i nie wykonuje działań rozliczeniowych.</p>
        {scheduleLoading || scheduleScopeId !== selectedOrganizationId ? <div className="loading-state" role="status">Ładowanie ustawień...</div> : (
          <>
            <div className="notification-schedule__fields">
              <label className="notification-schedule__toggle">
                <input
                  checked={scheduleEnabled}
                  onChange={(event) => setScheduleEnabled(event.currentTarget.checked)}
                  type="checkbox"
                />
                Włącz codzienne sprawdzanie
              </label>
              <label>
                Godzina lokalna
                <input
                  onChange={(event) => setScheduleLocalTime(event.currentTarget.value)}
                  type="time"
                  value={scheduleLocalTime}
                />
              </label>
              <label>
                Strefa czasowa IANA
                <input
                  onChange={(event) => setScheduleTimezone(event.currentTarget.value)}
                  type="text"
                  value={scheduleTimezone}
                />
              </label>
            </div>
            <div className="notification-schedule__meta">
              <span>Następne uruchomienie: <strong>{scheduleNextRun ? new Date(scheduleNextRun).toLocaleString("pl-PL") : "brak — harmonogram wyłączony"}</strong></span>
              {lastScheduleRun ? (
                <span>
                  Ostatni run: <strong>{lastScheduleRun.status}</strong> · próba {lastScheduleRun.attemptCount}
                  {lastScheduleRun.candidatesCount !== null ? ` · kandydaci ${lastScheduleRun.candidatesCount}, nowe ${lastScheduleRun.createdCount ?? 0}, istniejące ${lastScheduleRun.existingCount ?? 0}` : ""}
                </span>
              ) : <span>Brak dotychczasowych uruchomień.</span>}
              {lastScheduleRun?.errorSummary ? <span className="notification-schedule__error">Ostatni błąd: {lastScheduleRun.errorSummary}</span> : null}
            </div>
            {scheduleError ? <div className="error-state" role="alert"><strong>Nie udało się obsłużyć harmonogramu</strong><p>{scheduleError}</p><button className="button" onClick={() => void loadSchedule()} type="button">Spróbuj ponownie</button></div> : null}
            {scheduleMessage ? <div className="notifications-page__message" role="status">{scheduleMessage}</div> : null}
            <button className="button" disabled={scheduleSaving} onClick={() => void saveSchedule()} type="button">
              {scheduleSaving ? "Zapisywanie..." : "Zapisz ustawienia"}
            </button>
          </>
        )}
      </section>

      <div className="notifications-page__filters" role="group" aria-label="Filtry powiadomień">
        {INTERNAL_NOTIFICATION_FILTERS.map((option) => (
          <button
            aria-pressed={filter === option.id}
            className={filter === option.id ? "filter-chip filter-chip--active" : "filter-chip"}
            key={option.id}
            onClick={() => setFilter(option.id)}
            type="button"
          >
            {option.label}
          </button>
        ))}
      </div>

      {loading ? <div className="loading-state" role="status">Ładowanie powiadomień...</div> : null}
      {!loading && error ? (
        <div className="error-state" role="alert">
          <strong>Nie udało się pobrać powiadomień</strong>
          <p>{error}</p>
          <button className="button" onClick={() => void loadPage(false)} type="button">Spróbuj ponownie</button>
        </div>
      ) : null}
      {!loading && !error && items.length === 0 ? (
        <div className="empty-state">
          <Bell aria-hidden="true" size={22} />
          <h3>{emptyCopy.title}</h3>
          <p>{emptyCopy.description}</p>
        </div>
      ) : null}

      {!loading && !error && items.length > 0 ? (
        <ul className="notifications-list">
          {items.map((item) => {
            const pending = pendingActionId === item.id;
            return (
              <li className="notification-card" data-state={item.state} key={item.id}>
                <div className="notification-card__main">
                  <div className="notification-card__title-row">
                    <strong>{item.title}</strong>
                    <span className={item.reasonCode === "overdue" ? "badge badge--danger" : "badge badge--info"}>
                      {item.reasonCode === "overdue" ? "Zaległe" : "Dzisiaj"}
                    </span>
                    <span className="badge">{item.isUnread ? "Nieprzeczytane" : item.isArchived ? "Archiwum" : "Przeczytane"}</span>
                  </div>
                  <p>{item.plannedFor ?? "Bez terminu"} · {item.targetLabel}</p>
                  <small>Utworzono: {new Date(item.createdAt).toLocaleString("pl-PL")}</small>
                  {item.targetHref ? <Link href={item.targetHref}>Otwórz źródło</Link> : <span>Źródło historyczne — brak bezpiecznego linku</span>}
                </div>
                {!item.isArchived ? (
                  <div className="notification-card__actions">
                    {item.isUnread ? (
                      <button disabled={pendingActionId !== null} onClick={() => void changeState(item, "read")} type="button"><Check size={15} />{pending ? "Zapisywanie..." : "Oznacz jako przeczytane"}</button>
                    ) : (
                      <button disabled={pendingActionId !== null} onClick={() => void changeState(item, "unread")} type="button"><Undo2 size={15} />{pending ? "Zapisywanie..." : "Oznacz jako nieprzeczytane"}</button>
                    )}
                    <button disabled={pendingActionId !== null} onClick={() => void changeState(item, "archived")} type="button"><Archive size={15} />{pending ? "Zapisywanie..." : "Archiwizuj"}</button>
                  </div>
                ) : null}
              </li>
            );
          })}
        </ul>
      ) : null}

      {!loading && !error && hasMore ? (
        <button className="button notifications-page__more" disabled={loadingMore} onClick={() => void loadPage(true, nextCursor)} type="button">
          <ChevronDown aria-hidden="true" size={16} />{loadingMore ? "Ładowanie..." : "Załaduj kolejne"}
        </button>
      ) : null}
    </section>
  );
}
