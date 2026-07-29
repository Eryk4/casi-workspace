"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import { ArrowLeft, CheckCircle2, ListChecks, RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Table, type TableColumn } from "@/components/ui/Table";
import { useActiveOrganization } from "@/context/ActiveOrganizationContext";
import { withActiveOrganizationQuery } from "@/context/organizationContextModel";
import { api } from "@/lib/api";
import { BillingNextStepActionControls } from "./BillingNextStepActionControls";
import {
  BILLING_CANONICAL_ROUTE,
  BILLING_NEXT_STEPS_OVERVIEW_FILTERS,
  BILLING_ORGANIZATION_REQUIRED_DESCRIPTION,
  BILLING_ORGANIZATION_REQUIRED_TITLE,
  buildBillingNextStepRequest,
  buildBillingNextStepSnoozeRequest,
  buildBillingNextStepsOverview,
  canUseBillingOrganizationScope,
  createBillingNextStepSubmitter,
  formatLocalCalendarDate,
  getBillingErrorState,
  readBillingActiveNextStepEvents,
  suggestBillingNextStepSnoozeDate,
  type BillingErrorState,
  type BillingNextStepErrorState,
  type BillingNextStepsOverviewEvent,
  type BillingNextStepsOverviewFilter,
  type BillingNextStepsOverviewRow,
  type BillingStatus,
} from "./billingModel";

export function BillingNextStepsOverviewPage() {
  const { selectedOrganizationId, selectedOrganization, status: organizationStatus } = useActiveOrganization();
  const [events, setEvents] = useState<BillingNextStepsOverviewEvent[] | null>(null);
  const [loadedOrganizationId, setLoadedOrganizationId] = useState<string | null>(null);
  const [status, setStatus] = useState<BillingStatus>("idle");
  const [errorState, setErrorState] = useState<BillingErrorState | null>(null);
  const [filter, setFilter] = useState<BillingNextStepsOverviewFilter>("all");
  const [today, setToday] = useState<string | null>(null);
  const [completingId, setCompletingId] = useState<string | null>(null);
  const [completionError, setCompletionError] = useState<BillingNextStepErrorState | null>(null);
  const [completionSuccess, setCompletionSuccess] = useState<string | null>(null);
  const [snoozingId, setSnoozingId] = useState<string | null>(null);
  const [snoozeDate, setSnoozeDate] = useState("");
  const [snoozeSubmitting, setSnoozeSubmitting] = useState(false);
  const [snoozeError, setSnoozeError] = useState<string | null>(null);
  const [snoozeSuccess, setSnoozeSuccess] = useState<string | null>(null);
  const requestVersion = useRef(0);

  useEffect(() => {
    setToday(formatLocalCalendarDate());
  }, []);

  const loadNextSteps = useCallback(async () => {
    const currentRequest = requestVersion.current + 1;
    requestVersion.current = currentRequest;
    if (organizationStatus === "loading") {
      setEvents(null);
      setLoadedOrganizationId(null);
      setStatus("loading");
      setErrorState(null);
      return;
    }
    if (!canUseBillingOrganizationScope(selectedOrganizationId)) {
      setEvents(null);
      setLoadedOrganizationId(null);
      setStatus("ready");
      setErrorState(null);
      return;
    }

    const organizationId = String(selectedOrganizationId).trim();
    setEvents(null);
    setLoadedOrganizationId(null);
    setStatus("loading");
    setErrorState(null);
    setCompletionError(null);
    setCompletionSuccess(null);
    setSnoozingId(null);
    setSnoozeDate("");
    setSnoozeError(null);
    setSnoozeSuccess(null);
    try {
      const payload = await api.billingActiveNextStepEvents(
        withActiveOrganizationQuery(organizationId, { limit: 2000 }),
      );
      if (requestVersion.current !== currentRequest) {
        return;
      }
      const response = readBillingActiveNextStepEvents(payload);
      setEvents(response.events);
      setLoadedOrganizationId(organizationId);
      setStatus("ready");
    } catch (error) {
      if (requestVersion.current !== currentRequest) {
        return;
      }
      const nextError = getBillingErrorState(error);
      setEvents(null);
      setLoadedOrganizationId(null);
      setErrorState(nextError);
      setStatus(nextError.status);
    }
  }, [organizationStatus, selectedOrganizationId]);

  useEffect(() => {
    setFilter("all");
    setEvents(null);
    setLoadedOrganizationId(null);
    void loadNextSteps();
  }, [loadNextSteps]);

  const activeOrganizationId = canUseBillingOrganizationScope(selectedOrganizationId)
    ? String(selectedOrganizationId).trim()
    : null;
  const dataMatchesOrganization = Boolean(
    events && activeOrganizationId && loadedOrganizationId === activeOrganizationId,
  );
  const view = useMemo(
    () => buildBillingNextStepsOverview(dataMatchesOrganization && events ? events : [], { filter, today: today ?? "0000-01-01" }),
    [dataMatchesOrganization, events, filter, today],
  );
  const completeSubmitter = useMemo(
    () =>
      createBillingNextStepSubmitter({
        refreshDetail: loadNextSteps,
        setSubmitting: (isSubmitting) => {
          if (!isSubmitting) {
            setCompletingId(null);
          }
        },
        submitNextStep: (payload) => api.addBillingNextStepEvent(payload, activeOrganizationId),
      }),
    [activeOrganizationId, loadNextSteps],
  );
  const snoozeSubmitter = useMemo(
    () =>
      createBillingNextStepSubmitter({
        refreshDetail: loadNextSteps,
        setSubmitting: setSnoozeSubmitting,
        submitNextStep: (payload) => api.addBillingNextStepEvent(payload, activeOrganizationId),
      }),
    [activeOrganizationId, loadNextSteps],
  );

  const handleComplete = useCallback(
    async (row: BillingNextStepsOverviewRow) => {
      if (!row.completionTargetType) {
        return;
      }
      setCompletingId(row.id);
      setCompletionError(null);
      setCompletionSuccess(null);
      const validation = buildBillingNextStepRequest({
        parentEventId: row.eventId,
        targetType: row.completionTargetType,
        targetId: row.targetId,
        relatedIssueKey: row.relatedIssueKey,
        stepType: row.stepType,
        eventAction: "completed",
        title: row.title,
        noteText: "",
        plannedFor: row.plannedFor,
        organizationId: activeOrganizationId,
      });
      const result = await completeSubmitter(validation);
      if (result.status === "blocked") {
        setCompletingId(null);
        setCompletionError({ status: "error", title: "Nie zakończono kroku", description: result.message });
      } else if (result.status === "error") {
        setCompletionError(result.errorState);
      } else if (result.status === "success") {
        setCompletionSuccess("Krok został oznaczony jako wykonany.");
      }
    },
    [activeOrganizationId, completeSubmitter],
  );
  const startSnooze = useCallback((row: BillingNextStepsOverviewRow) => {
    setSnoozingId(row.id);
    setSnoozeDate(suggestBillingNextStepSnoozeDate(row.plannedFor));
    setSnoozeError(null);
    setSnoozeSuccess(null);
  }, []);
  const cancelSnooze = useCallback(() => {
    setSnoozingId(null);
    setSnoozeDate("");
    setSnoozeError(null);
  }, []);
  const handleSnooze = useCallback(
    async (event: FormEvent<HTMLFormElement>, row: BillingNextStepsOverviewRow) => {
      event.preventDefault();
      if (snoozingId !== row.id) {
        return;
      }
      setSnoozeError(null);
      setSnoozeSuccess(null);
      const validation = buildBillingNextStepSnoozeRequest({
        parentEventId: row.eventId,
        currentPlannedFor: row.plannedFor,
        plannedFor: snoozeDate,
        organizationId: activeOrganizationId,
      });
      const result = await snoozeSubmitter(validation);
      if (result.status === "blocked") {
        setSnoozeError(result.message);
      } else if (result.status === "error") {
        setSnoozeError(result.errorState.description);
      } else if (result.status === "success") {
        setSnoozingId(null);
        setSnoozeDate("");
        setSnoozeSuccess("Krok został odłożony na nowy termin.");
      }
    },
    [activeOrganizationId, snoozeDate, snoozeSubmitter, snoozingId],
  );

  const columns = useMemo<Array<TableColumn<BillingNextStepsOverviewRow>>>(
    () => [
      {
        key: "step",
        header: "Następny krok",
        render: (row) => (
          <span className="billing-family-cell">
            <strong>{row.title}</strong>
            <span>{row.stepTypeLabel} · {row.eventActionLabel}</span>
          </span>
        ),
      },
      {
        key: "date",
        header: "Termin",
        render: (row) => (
          <span className="billing-family-cell">
            <StatusBadge status={row.dateTone}>{row.dateStatusLabel}</StatusBadge>
            <span>{row.dateLabel}</span>
          </span>
        ),
      },
      {
        key: "target",
        header: "Cel",
        render: (row) => (
          <span className="billing-family-cell">
            <span>{row.targetTypeLabel}</span>
            {row.targetHref ? <Link className="module-link" href={row.targetHref}>{row.targetLabel}</Link> : <strong>{row.targetLabel}</strong>}
          </span>
        ),
      },
      {
        key: "action",
        header: "Działanie",
        render: (row) => row.completionTargetType ? (
          <BillingNextStepActionControls
            busy={Boolean(completingId) || snoozeSubmitting}
            completing={completingId === row.id}
            onCancelSnooze={cancelSnooze}
            onComplete={() => handleComplete(row)}
            onSnoozeDateChange={(value) => {
              setSnoozeDate(value);
              setSnoozeError(null);
            }}
            onSnoozeSubmit={(event) => handleSnooze(event, row)}
            onStartSnooze={() => startSnooze(row)}
            row={row}
            snoozeDate={snoozeDate}
            snoozeError={snoozingId === row.id ? snoozeError : null}
            snoozing={snoozingId === row.id}
          />
        ) : <span>Brak bezpiecznej akcji</span>,
      },
    ],
    [cancelSnooze, completingId, handleComplete, handleSnooze, snoozeDate, snoozeError, snoozeSubmitting, snoozingId, startSnooze],
  );

  const organizationMissing = organizationStatus === "ready" && !activeOrganizationId;
  const ready = status === "ready" && dataMatchesOrganization && Boolean(today) && !organizationMissing;

  return (
    <div className="module-page billing-page billing-next-steps-overview-page">
      <PageHeader
        badgeTone={status === "ready" ? "success" : errorState ? "warning" : "info"}
        description="Jedna lista aktywnych działań rozliczeniowych dla wybranej organizacji. Kroki nie zmieniają sald, wpłat ani naliczeń."
        eyebrow="Rozliczenia"
        title="Następne kroki"
        actions={
          <div className="module-page-actions">
            <StatusBadge status="info">{`${view.counts.all} aktywnych`}</StatusBadge>
            <Link className="ui-button ui-button--secondary ui-button--sm" href={BILLING_CANONICAL_ROUTE}>
              <span className="ui-button__icon"><ArrowLeft size={15} /></span>
              <span>Wróć do rozliczeń</span>
            </Link>
            <Button disabled={status === "loading"} icon={<RefreshCw size={15} />} onClick={loadNextSteps} size="sm" variant="secondary">
              Odśwież
            </Button>
          </div>
        }
      />

      {status === "loading" || !today ? <LoadingState /> : null}
      {errorState ? (
        <Card title="Nie udało się wczytać następnych kroków">
          <ErrorState description={errorState.description} title={errorState.title} />
          <Button icon={<RefreshCw size={15} />} onClick={loadNextSteps} size="sm" variant="secondary">Spróbuj ponownie</Button>
        </Card>
      ) : null}
      {organizationMissing ? <EmptyState description={BILLING_ORGANIZATION_REQUIRED_DESCRIPTION} title={BILLING_ORGANIZATION_REQUIRED_TITLE} /> : null}

      {ready && !view.allRows.length ? (
        <EmptyState
          description={`W organizacji ${selectedOrganization?.name ?? "wybranej organizacji"} nie ma aktywnych ręcznych kroków rozliczeniowych.`}
          title="Brak aktywnych kroków"
        />
      ) : null}

      {ready && view.allRows.length ? (
        <>
          <Card description="Wybierz zakres terminów. Data jest traktowana jako lokalna data kalendarzowa." title="Filtry">
            <div className="module-page-actions" role="group" aria-label="Filtry następnych kroków">
              {BILLING_NEXT_STEPS_OVERVIEW_FILTERS.map((option) => (
                <Button
                  aria-pressed={filter === option.value}
                  key={option.value}
                  onClick={() => setFilter(option.value)}
                  size="sm"
                  variant={filter === option.value ? "primary" : "secondary"}
                >
                  {`${option.label} (${view.counts[option.value]})`}
                </Button>
              ))}
            </div>
          </Card>

          <Card
            action={<StatusBadge status="info">Append-only</StatusBadge>}
            description="Każdy wiersz odpowiada konkretnemu aktywnemu liściowi planned albo snoozed. Identyczne kroki pozostają osobnymi wpisami."
            title={BILLING_NEXT_STEPS_OVERVIEW_FILTERS.find((option) => option.value === filter)?.label ?? "Następne kroki"}
          >
            {view.filteredRows.length ? (
              <Table<BillingNextStepsOverviewRow> columns={columns} data={view.filteredRows} getRowKey={(row) => row.id} />
            ) : (
              <EmptyState description="W tym zakresie dat nie ma aktywnych kroków." title="Brak kroków dla wybranego filtra" />
            )}
          </Card>
          {completionError ? <ErrorState description={completionError.description} title={completionError.title} /> : null}
          {completionSuccess ? <p className="module-success"><CheckCircle2 aria-hidden="true" size={16} /> {completionSuccess}</p> : null}
          {snoozeSuccess ? <p className="module-success"><CheckCircle2 aria-hidden="true" size={16} /> {snoozeSuccess}</p> : null}
          <p className="module-note"><ListChecks aria-hidden="true" size={16} /> Widok nie udostępnia edycji, usuwania ani operacji masowych.</p>
        </>
      ) : null}
    </div>
  );
}
