"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { CheckCircle2, Clock3, ListChecks, RefreshCw, TriangleAlert, Workflow } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { PageHeader } from "@/components/ui/PageHeader";
import { useActiveOrganization } from "@/context/ActiveOrganizationContext";
import { withActiveOrganizationQuery } from "@/context/organizationContextModel";
import { api } from "@/lib/api";
import {
  automationActivityStatusLabel,
  automationAttentionCategoryLabel,
  readAutomationActivity,
  readAutomationOperationsDashboard,
  type AutomationActivityResponse,
  type AutomationOperationsDashboard,
} from "@/modules/automations/automationOperationsModel";
import { readTodayBilling, todayBillingBucketLabel, type TodayBilling } from "./todayBillingModel";
import { formatTodayHeadingDate, formatTodayItemDate, resolveTodaySections } from "./todayDashboardModel";
import { readTodayTasks, todayTaskBucketLabel, type TodayTasks } from "./todayTasksModel";

type SectionKey = "attention" | "tasks" | "billing" | "activity";
type SectionState<T> = {
  status: "idle" | "loading" | "ready" | "error";
  organizationId: string | null;
  data: T | null;
  error: string | null;
};

const idleState = <T,>(): SectionState<T> => ({ status: "idle", organizationId: null, data: null, error: null });

export function DailyBriefPage() {
  const { capabilities, selectedOrganization, selectedOrganizationId, status: organizationStatus } = useActiveOrganization();
  const visibility = useMemo(() => resolveTodaySections(capabilities), [capabilities]);
  const organizationRef = useRef(selectedOrganizationId);
  const visibilityRef = useRef(visibility);
  const versions = useRef<Record<SectionKey, number>>({ attention: 0, tasks: 0, billing: 0, activity: 0 });
  const [attention, setAttention] = useState<SectionState<AutomationOperationsDashboard>>(idleState);
  const [tasks, setTasks] = useState<SectionState<TodayTasks>>(idleState);
  const [billing, setBilling] = useState<SectionState<TodayBilling>>(idleState);
  const [activity, setActivity] = useState<SectionState<AutomationActivityResponse>>(idleState);

  organizationRef.current = selectedOrganizationId;
  visibilityRef.current = visibility;

  const loadSection = useCallback(async <T,>(key: SectionKey, organizationId: string, request: () => Promise<Record<string, unknown>>, reader: (payload: unknown) => T, setter: (state: SectionState<T>) => void) => {
    const version = ++versions.current[key];
    setter({ status: "loading", organizationId, data: null, error: null });
    try {
      const data = reader(await request());
      if (versions.current[key] !== version || organizationRef.current !== organizationId || !visibilityRef.current[key]) return;
      setter({ status: "ready", organizationId, data, error: null });
    } catch (error) {
      if (versions.current[key] !== version || organizationRef.current !== organizationId || !visibilityRef.current[key]) return;
      setter({ status: "error", organizationId, data: null, error: error instanceof Error ? error.message : "Nie udało się pobrać danych." });
    }
  }, []);

  const loadAttention = useCallback((organizationId: string) => loadSection("attention", organizationId, () => api.automationOperations(withActiveOrganizationQuery(organizationId)), readAutomationOperationsDashboard, setAttention), [loadSection]);
  const loadTasks = useCallback((organizationId: string) => loadSection("tasks", organizationId, () => api.todayTasks(withActiveOrganizationQuery(organizationId)), readTodayTasks, setTasks), [loadSection]);
  const loadBilling = useCallback((organizationId: string) => loadSection("billing", organizationId, () => api.todayBilling(withActiveOrganizationQuery(organizationId)), readTodayBilling, setBilling), [loadSection]);
  const loadActivity = useCallback((organizationId: string) => loadSection("activity", organizationId, () => api.automationOperationsActivity(withActiveOrganizationQuery(organizationId, { limit: 3 })), readAutomationActivity, setActivity), [loadSection]);

  useEffect(() => {
    (Object.keys(versions.current) as SectionKey[]).forEach((key) => { versions.current[key] += 1; });
    setAttention(idleState());
    setTasks(idleState());
    setBilling(idleState());
    setActivity(idleState());
    if (organizationStatus !== "ready" || !selectedOrganizationId) return;
    if (visibility.attention) void loadAttention(selectedOrganizationId);
    if (visibility.tasks) void loadTasks(selectedOrganizationId);
    if (visibility.billing) void loadBilling(selectedOrganizationId);
    if (visibility.activity) void loadActivity(selectedOrganizationId);
  }, [loadActivity, loadAttention, loadBilling, loadTasks, organizationStatus, selectedOrganizationId, visibility.activity, visibility.attention, visibility.billing, visibility.tasks]);

  const refresh = useCallback(() => {
    if (organizationStatus !== "ready" || !selectedOrganizationId) return;
    if (visibility.attention) void loadAttention(selectedOrganizationId);
    if (visibility.tasks) void loadTasks(selectedOrganizationId);
    if (visibility.billing) void loadBilling(selectedOrganizationId);
    if (visibility.activity) void loadActivity(selectedOrganizationId);
  }, [loadActivity, loadAttention, loadBilling, loadTasks, organizationStatus, selectedOrganizationId, visibility]);

  const hasVisibleSections = Object.values(visibility).some(Boolean);
  const actionableStates = [visibility.attention ? attention : null, visibility.tasks ? tasks : null, visibility.billing ? billing : null].filter(Boolean) as Array<SectionState<unknown>>;
  const allActionableEmpty = actionableStates.length > 0 && actionableStates.every((state) => {
    if (state.status !== "ready" || state.organizationId !== selectedOrganizationId || !state.data) return false;
    if (typeof state.data !== "object") return false;
    if ("attentionItems" in state.data) return Array.isArray(state.data.attentionItems) && state.data.attentionItems.length === 0;
    return "items" in state.data && Array.isArray(state.data.items) && state.data.items.length === 0;
  });

  return (
    <div className="module-page today-dashboard">
      <PageHeader badgeTone="info" description={`${selectedOrganization?.name ?? "Wybierz organizację"} · ${formatTodayHeadingDate()}`} eyebrow="Dzisiaj" title="Dzisiaj w CASI" actions={<Button disabled={organizationStatus !== "ready" || !selectedOrganizationId || !hasVisibleSections} icon={<RefreshCw size={15} />} onClick={refresh} size="sm">Odśwież</Button>} />
      {organizationStatus === "ready" && !selectedOrganizationId ? <EmptyState title="Wybierz organizację" description="Pulpit Dzisiaj działa wyłącznie w kontekście aktywnej organizacji." /> : null}
      {organizationStatus === "ready" && selectedOrganizationId && !hasVisibleSections ? <EmptyState title="Brak dodatkowych sekcji do wyświetlenia." description="Ten pulpit nie ma dodatkowych informacji dla bieżącego zakresu dostępu." /> : null}
      {allActionableEmpty ? <div className="today-dashboard__clear" role="status"><CheckCircle2 size={18} /><span>Na ten moment nie ma spraw wymagających Twojej uwagi.</span></div> : null}
      {selectedOrganizationId && hasVisibleSections ? (
        <div className="today-dashboard__sections" aria-label="Dzisiaj w CASI">
          {visibility.attention ? <AttentionSection state={visibleState(attention, selectedOrganizationId)} retry={() => loadAttention(selectedOrganizationId)} /> : null}
          {visibility.tasks ? <TasksSection state={visibleState(tasks, selectedOrganizationId)} retry={() => loadTasks(selectedOrganizationId)} /> : null}
          {visibility.billing ? <BillingSection state={visibleState(billing, selectedOrganizationId)} retry={() => loadBilling(selectedOrganizationId)} /> : null}
          {visibility.activity ? <ActivitySection state={visibleState(activity, selectedOrganizationId)} retry={() => loadActivity(selectedOrganizationId)} /> : null}
        </div>
      ) : null}
    </div>
  );
}

function visibleState<T>(state: SectionState<T>, organizationId: string): SectionState<T> {
  return state.organizationId === organizationId ? state : { status: "loading", organizationId, data: null, error: null };
}

function SectionFailure({ message, retry }: { message: string; retry: () => void }) {
  return <ErrorState title={message} description="Spróbuj ponownie za chwilę." action={<Button onClick={retry} size="sm">Spróbuj ponownie</Button>} />;
}

function AttentionSection({ state, retry }: { state: SectionState<AutomationOperationsDashboard>; retry: () => void }) {
  const items = state.data?.attentionItems.slice(0, 3) ?? [];
  return <Card className="today-section today-section--attention" title="Wymaga uwagi" description="Najważniejsze sygnały z automatyzacji" action={<TriangleAlert size={18} />}>
    {state.status === "loading" ? <LoadingState /> : null}{state.status === "error" ? <SectionFailure message="Nie udało się pobrać sygnałów wymagających uwagi." retry={retry} /> : null}
    {state.status === "ready" && items.length === 0 ? <p className="today-section__empty">Brak sygnałów wymagających uwagi.</p> : null}
    {items.length ? <div className="today-list">{items.map((item) => <Link className="today-list__item" href={item.detailsUrl} key={`${item.automationKey}-${item.reasonCode}`}><span className="today-list__badge">{automationAttentionCategoryLabel(item.attentionCategory)}</span><strong>{item.title}</strong><span>{item.summary}</span><small>{formatDateTime(item.occurredAt)} · Zobacz szczegóły</small></Link>)}</div> : null}
    {state.data && state.data.summary.attentionCount > 3 ? <Link className="today-section__more" href="/automatyzacje">Zobacz wszystkie</Link> : null}
  </Card>;
}

function TasksSection({ state, retry }: { state: SectionState<TodayTasks>; retry: () => void }) {
  return <Card className="today-section today-section--tasks" title="Twoje zadania" description={state.data ? `Po terminie: ${state.data.counts.overdue} · Dzisiaj: ${state.data.counts.today} · Najbliższe: ${state.data.counts.upcoming}` : "Zadania na dziś i najbliższy termin"} action={<ListChecks size={18} />}>
    {state.status === "loading" ? <LoadingState /> : null}{state.status === "error" ? <SectionFailure message="Nie udało się pobrać Twoich zadań." retry={retry} /> : null}
    {state.status === "ready" && state.data?.items.length === 0 ? <p className="today-section__empty">Nie masz zadań wymagających działania w najbliższym czasie.</p> : null}
    {state.data?.items.length ? <div className="today-list">{state.data.items.map((item) => <Link className="today-list__item" href={item.detailsUrl} key={item.taskId}><span className={`today-list__badge today-list__badge--${item.bucket}`}>{todayTaskBucketLabel(item.bucket)}</span><strong>{item.title}</strong><small>{formatTodayItemDate(item.dueAt)} · Zobacz szczegóły</small></Link>)}</div> : null}
    {state.data ? <Link className="today-section__more" href="/work-items">Zobacz wszystkie</Link> : null}
  </Card>;
}

function BillingSection({ state, retry }: { state: SectionState<TodayBilling>; retry: () => void }) {
  return <Card className="today-section today-section--billing" title="Rozliczenia do zrobienia" description={state.data ? `Po terminie: ${state.data.overdueCount} · Dzisiaj: ${state.data.dueTodayCount}` : "Następne kroki rozliczeniowe"} action={<Clock3 size={18} />}>
    {state.status === "loading" ? <LoadingState /> : null}{state.status === "error" ? <SectionFailure message="Nie udało się pobrać spraw rozliczeniowych." retry={retry} /> : null}
    {state.status === "ready" && state.data?.items.length === 0 ? <p className="today-section__empty">Brak kroków rozliczeniowych wymagających działania.</p> : null}
    {state.data?.items.length ? <div className="today-list">{state.data.items.map((item) => <Link className="today-list__item" href={item.detailsUrl} key={item.billingNextStepEventId}><span className={`today-list__badge today-list__badge--${item.bucket}`}>{todayBillingBucketLabel(item.bucket)}</span><strong>{item.title}</strong><small>{formatTodayItemDate(item.plannedFor)} · Zobacz szczegóły</small></Link>)}</div> : null}
    {state.data ? <Link className="today-section__more" href="/rozliczenia/kroki">Zobacz wszystkie</Link> : null}
  </Card>;
}

function ActivitySection({ state, retry }: { state: SectionState<AutomationActivityResponse>; retry: () => void }) {
  return <Card className="today-section today-section--activity" title="Ostatnia aktywność" description="Najnowsze bezpieczne zdarzenia automatyzacji" action={<Workflow size={18} />}>
    {state.status === "loading" ? <LoadingState /> : null}{state.status === "error" ? <SectionFailure message="Nie udało się pobrać ostatniej aktywności." retry={retry} /> : null}
    {state.status === "ready" && state.data?.items.length === 0 ? <p className="today-section__empty">Brak ostatniej aktywności.</p> : null}
    {state.data?.items.length ? <div className="today-list">{state.data.items.slice(0, 3).map((item) => <Link className="today-list__item" href={item.detailsUrl} key={item.activityId}><span className={`today-list__badge today-list__badge--${item.status}`}>{automationActivityStatusLabel(item.status)}</span><strong>{item.title}</strong><span>{item.summary}</span><small>{formatDateTime(item.occurredAt)} · Zobacz szczegóły</small></Link>)}</div> : null}
    {state.data ? <Link className="today-section__more" href="/automatyzacje">Przejdź do automatyzacji</Link> : null}
  </Card>;
}

function formatDateTime(value: string | null): string {
  if (!value) return "Czas niedostępny";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Czas niedostępny";
  return new Intl.DateTimeFormat("pl-PL", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }).format(date);
}
