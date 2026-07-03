"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  CalendarClock,
  CheckCircle2,
  Clock3,
  FileText,
  ListChecks,
  ReceiptText,
  RefreshCw,
} from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { FilterBar } from "@/components/ui/FilterBar";
import { LoadingState } from "@/components/ui/LoadingState";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Table, type TableColumn } from "@/components/ui/Table";
import { useActiveOrganization } from "@/context/ActiveOrganizationContext";
import { withActiveOrganizationQuery } from "@/context/organizationContextModel";
import { api } from "@/lib/api";
import { formatCount } from "@/lib/utils";
import type { DashboardSnapshot } from "@/lib/types";

import {
  DASHBOARD_ORGANIZATION_REQUIRED_DESCRIPTION,
  DASHBOARD_ORGANIZATION_REQUIRED_TITLE,
  buildSignals,
  canUseDashboardOrganizationScope,
  canRenderDashboardData,
  getDashboardErrorState,
  isDashboardEmpty,
  type DashboardErrorState,
  type DashboardFilter,
  type DashboardSignal,
  type DashboardStatus,
} from "./dashboardModel";

const columns: Array<TableColumn<DashboardSignal>> = [
  {
    key: "area",
    header: "Obszar",
    render: (row) => (
      <span className="module-row-title">
        <FileText aria-hidden="true" size={16} />
        {row.area}
      </span>
    ),
  },
  {
    key: "owner",
    header: "Modul",
    render: (row) => row.owner,
  },
  {
    key: "status",
    header: "Status",
    render: (row) => <StatusBadge status={row.status}>{row.statusLabel}</StatusBadge>,
  },
  {
    key: "source",
    header: "Zrodlo",
    render: (row) => row.source,
  },
  {
    key: "nextStep",
    header: "Nastepny krok",
    render: (row) => row.nextStep,
  },
];

export function DashboardPage() {
  const { selectedOrganizationId, selectedOrganization, status: organizationStatus } = useActiveOrganization();
  const [snapshot, setSnapshot] = useState<DashboardSnapshot | null>(null);
  const [status, setStatus] = useState<DashboardStatus>("idle");
  const [errorState, setErrorState] = useState<DashboardErrorState | null>(null);
  const [activeFilter, setActiveFilter] = useState<DashboardFilter>("all");

  const loadDashboard = useCallback(async () => {
    if (organizationStatus === "loading") {
      setStatus("loading");
      setErrorState(null);
      return;
    }

    if (!canUseDashboardOrganizationScope(selectedOrganizationId)) {
      setSnapshot(null);
      setErrorState(null);
      setStatus("ready");
      return;
    }

    setStatus("loading");
    setErrorState(null);

    try {
      const nextSnapshot = await api.dashboard(withActiveOrganizationQuery(selectedOrganizationId));
      setSnapshot(nextSnapshot);
      setStatus("ready");
    } catch (error) {
      const nextErrorState = getDashboardErrorState(error);
      setErrorState(nextErrorState);
      setSnapshot(null);
      setStatus(nextErrorState.status);
    }
  }, [organizationStatus, selectedOrganizationId]);

  useEffect(() => {
    void loadDashboard();
  }, [loadDashboard]);

  const signals = useMemo(() => buildSignals(snapshot, activeFilter), [activeFilter, snapshot]);
  const cards = snapshot?.cards;
  const reminders = snapshot?.active_reminders ?? [];
  const knowledgeQueue = snapshot?.knowledge_queue ?? [];
  const organizationMissing = organizationStatus === "ready" && !canUseDashboardOrganizationScope(selectedOrganizationId);
  const readyWithoutData = !organizationMissing && isDashboardEmpty(status, snapshot);
  const canShowDashboardData = canRenderDashboardData(status, snapshot);

  return (
    <div className="dashboard-page">
      <PageHeader
        badgeTone={status === "ready" ? "success" : status === "error" ? "warning" : "info"}
        description="Najwazniejsze sygnaly operacyjne, kolejki pracy i przypomnienia dla biezacej organizacji."
        eyebrow={status === "ready" ? "Dane live" : "Pulpit operacyjny"}
        title="Centrum pracy CASI"
        actions={
          <Button
            disabled={status === "loading"}
            icon={<RefreshCw size={15} />}
            onClick={loadDashboard}
            size="sm"
            variant="secondary"
          >
            Odswiez
          </Button>
        }
      />

      {status === "loading" ? <LoadingState /> : null}
      {errorState ? (
        <ErrorState
          action={
            errorState.status === "unauthenticated" ? (
              <Link className="ui-button ui-button--primary ui-button--sm" href="/login?next=/pulpit">
                Zaloguj sie
              </Link>
            ) : null
          }
          description={errorState.description}
          title={errorState.title}
        />
      ) : null}
      {organizationMissing ? (
        <EmptyState
          description={DASHBOARD_ORGANIZATION_REQUIRED_DESCRIPTION}
          title={DASHBOARD_ORGANIZATION_REQUIRED_TITLE}
        />
      ) : null}
      {readyWithoutData ? (
        <EmptyState
          description={`Backend odpowiedzial poprawnie, ale snapshot pulpitu nie zawiera jeszcze kart, alertow, przypomnien ani kolejki wiedzy dla organizacji ${selectedOrganization?.name ?? selectedOrganizationId}.`}
          title="Brak danych pulpitu"
        />
      ) : null}

      {canShowDashboardData ? (
        <>
          <section className="dashboard-kpi-grid" aria-label="Najwazniejsze metryki">
            <Card className="dashboard-kpi-card">
              <span className="dashboard-kpi-card__icon">
                <CheckCircle2 aria-hidden="true" size={19} />
              </span>
              <span>Nowe faktury</span>
              <strong>{formatCount(cards?.nowe_faktury ?? 0)}</strong>
              <p>Nowe rekordy widoczne w biezacym pulpicie organizacji.</p>
            </Card>
            <Card className="dashboard-kpi-card">
              <span className="dashboard-kpi-card__icon">
                <ReceiptText aria-hidden="true" size={19} />
              </span>
              <span>Do weryfikacji</span>
              <strong>{formatCount(cards?.do_weryfikacji ?? 0)}</strong>
              <p>Faktury, ktore wymagaja recznej decyzji operatora.</p>
            </Card>
            <Card className="dashboard-kpi-card">
              <span className="dashboard-kpi-card__icon">
                <ListChecks aria-hidden="true" size={19} />
              </span>
              <span>Duplikaty</span>
              <strong>{formatCount((cards?.podejrzenia_duplikatow ?? 0) + (cards?.pewne_duplikaty ?? 0))}</strong>
              <p>Podejrzenia i pewne duplikaty w obrebie organizacji.</p>
            </Card>
            <Card className="dashboard-kpi-card">
              <span className="dashboard-kpi-card__icon">
                <CalendarClock aria-hidden="true" size={19} />
              </span>
              <span>Przypomnienia</span>
              <strong>{formatCount(cards?.aktywne_przypomnienia ?? 0)}</strong>
              <p>Aktywne przypomnienia widoczne dla biezacego uzytkownika.</p>
            </Card>
          </section>

          <FilterBar>
            <Button onClick={() => setActiveFilter("all")} size="sm" variant={activeFilter === "all" ? "primary" : "secondary"}>
              Wszystkie
            </Button>
            <Button
              onClick={() => setActiveFilter("invoices")}
              size="sm"
              variant={activeFilter === "invoices" ? "primary" : "secondary"}
            >
              Faktury
            </Button>
            <Button
              onClick={() => setActiveFilter("tasks")}
              size="sm"
              variant={activeFilter === "tasks" ? "primary" : "secondary"}
            >
              Zadania
            </Button>
            <Button
              onClick={() => setActiveFilter("knowledge")}
              size="sm"
              variant={activeFilter === "knowledge" ? "primary" : "secondary"}
            >
              Wiedza
            </Button>
            <Button
              onClick={() => setActiveFilter("integrations")}
              size="sm"
              variant={activeFilter === "integrations" ? "primary" : "secondary"}
            >
              Integracje
            </Button>
          </FilterBar>

          <section className="dashboard-workspace">
            <Card className="dashboard-main-card" title="Alerty operacyjne">
              <Table
                columns={columns}
                data={signals}
                emptyMessage="Backend nie zwrocil aktywnych alertow operacyjnych."
                getRowKey={(row) => row.id}
              />
            </Card>

            <aside className="dashboard-side-panel" aria-label="Stan wdrozenia frontendu">
              <Card title="Najblizsze przypomnienia">
                {reminders.length ? (
                  <ol className="dashboard-step-list">
                    {reminders.slice(0, 4).map((reminder, index) => (
                      <li key={reminder.task_id ?? `${reminder.title}-${index}`}>
                        <Clock3 aria-hidden="true" size={16} />
                        <span>{reminder.title || "Przypomnienie bez tytulu"}</span>
                      </li>
                    ))}
                  </ol>
                ) : (
                  <EmptyState
                    description="Backend nie zwrocil aktywnych przypomnien dla biezacego uzytkownika."
                    title="Nie ma przypomnien do pokazania"
                  />
                )}
              </Card>

              <Card title="Kolejka wiedzy">
                {knowledgeQueue.length ? (
                  <ol className="dashboard-step-list">
                    {knowledgeQueue.slice(0, 4).map((item, index) => (
                      <li key={item.knowledge_document_id ?? `${item.title}-${index}`}>
                        <Clock3 aria-hidden="true" size={16} />
                        <span>
                          {item.title || "Dokument firmowy"} - {item.business_status_label || "status nieznany"}
                        </span>
                      </li>
                    ))}
                  </ol>
                ) : (
                  <EmptyState
                    description="Backend nie zwrocil dokumentow czekajacych w kolejce wiedzy."
                    icon={<AlertTriangle aria-hidden="true" size={18} />}
                    title="Brak dokumentow w kolejce"
                  />
                )}
              </Card>
            </aside>
          </section>
        </>
      ) : null}
    </div>
  );
}
