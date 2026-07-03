"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { BarChart3, FileText, RefreshCw } from "lucide-react";
import Link from "next/link";

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
import { ApiError, api } from "@/lib/api";
import {
  REPORT_EXPORTS_ENABLED,
  REPORT_GENERATOR_ENABLED,
  REPORTS_ORGANIZATION_REQUIRED_DESCRIPTION,
  REPORTS_ORGANIZATION_REQUIRED_TITLE,
  REPORTS_READ_ONLY,
  buildReportModuleLinks,
  buildReportSignals,
  buildReportsKpis,
  canUseReportsOrganizationScope,
  formatMoney,
  getReportsErrorState,
  hasReportsData,
  isReportsEmpty,
  readReportsSnapshot,
  type ReportModuleLink,
  type ReportSignal,
  type ReportsErrorState,
  type ReportsSnapshot,
  type ReportsStatus,
} from "./reportsModel";

const signalColumns: Array<TableColumn<ReportSignal>> = [
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
    key: "value",
    header: "Wartosc",
    align: "right",
    render: (row) => row.value,
  },
  {
    key: "status",
    header: "Status",
    render: (row) => <StatusBadge status={row.statusTone}>{row.statusLabel}</StatusBadge>,
  },
  {
    key: "nextStep",
    header: "Nastepny krok",
    render: (row) => row.nextStep,
  },
  {
    key: "link",
    header: "Modul",
    render: (row) => (
      <Link className="module-quick-action" href={row.href}>
        Otworz
      </Link>
    ),
  },
];

const moduleColumns: Array<TableColumn<ReportModuleLink>> = [
  {
    key: "label",
    header: "Modul",
    render: (row) => (
      <span className="module-row-title">
        <BarChart3 aria-hidden="true" size={16} />
        {row.label}
      </span>
    ),
  },
  {
    key: "description",
    header: "Zakres",
    render: (row) => row.description,
  },
  {
    key: "status",
    header: "Status",
    render: (row) => <StatusBadge status={row.statusTone}>{row.statusLabel}</StatusBadge>,
  },
  {
    key: "link",
    header: "Przejscie",
    render: (row) => (
      <Link className="module-quick-action" href={row.href}>
        Zobacz
      </Link>
    ),
  },
];

type SourceResult = {
  key: string;
  payload?: unknown;
  error?: unknown;
};

export function ReportsPage() {
  const { selectedOrganizationId, selectedOrganization, status: organizationStatus } = useActiveOrganization();
  const [snapshot, setSnapshot] = useState<ReportsSnapshot | null>(null);
  const [status, setStatus] = useState<ReportsStatus>("idle");
  const [errorState, setErrorState] = useState<ReportsErrorState | null>(null);

  const loadReports = useCallback(async () => {
    if (organizationStatus === "loading") {
      setStatus("loading");
      setErrorState(null);
      return;
    }

    if (!canUseReportsOrganizationScope(selectedOrganizationId)) {
      setSnapshot(null);
      setErrorState(null);
      setStatus("ready");
      return;
    }

    setStatus("loading");
    setErrorState(null);

    try {
      const organizationQuery = withActiveOrganizationQuery(selectedOrganizationId);
      const results = await Promise.allSettled([
        api.dashboard(organizationQuery),
        api.workItems(withActiveOrganizationQuery(selectedOrganizationId, { limit: 100, only_open: 1 })),
        api.knowledgeDocuments(organizationQuery),
        api.ledgerBalances(organizationQuery),
        api.contractors(organizationQuery),
      ]);
      const sources = mapSourceResults(["dashboard", "workItems", "documents", "billingBalances", "contractors"], results);
      const authFailure = sources.find((source) => source.error instanceof ApiError && [401, 403].includes(source.error.status));
      if (authFailure?.error) {
        throw authFailure.error;
      }

      const nextSnapshot = readReportsSnapshot({
        dashboard: sources[0]?.payload,
        workItems: sources[1]?.payload,
        documents: sources[2]?.payload,
        billingBalances: sources[3]?.payload,
        contractors: sources[4]?.payload,
        missingSources: sources.filter((source) => source.error).map((source) => source.key),
      });

      setSnapshot(nextSnapshot);
      setStatus("ready");
    } catch (error) {
      const nextErrorState = getReportsErrorState(error);
      setErrorState(nextErrorState);
      setSnapshot(null);
      setStatus(nextErrorState.status);
    }
  }, [organizationStatus, selectedOrganizationId]);

  useEffect(() => {
    void loadReports();
  }, [loadReports]);

  const signals = useMemo(() => (snapshot ? buildReportSignals(snapshot) : []), [snapshot]);
  const moduleLinks = useMemo(() => (snapshot ? buildReportModuleLinks(snapshot) : []), [snapshot]);
  const kpis = useMemo(() => (snapshot ? buildReportsKpis(snapshot) : null), [snapshot]);
  const hasData = hasReportsData(status, snapshot);
  const organizationMissing = organizationStatus === "ready" && !canUseReportsOrganizationScope(selectedOrganizationId);
  const readyWithoutData = !organizationMissing && isReportsEmpty(status, snapshot);

  return (
    <div className="module-page reports-page">
      <PageHeader
        badgeTone={status === "ready" ? "success" : status === "error" ? "warning" : "info"}
        description="Read-only podsumowanie operacyjne firmy z istniejacych modulow. To nie jest jeszcze generator raportow ani system BI."
        eyebrow={status === "ready" ? "Dane live" : "Raporty"}
        title="Raporty"
        actions={
          <Button disabled={status === "loading"} icon={<RefreshCw size={15} />} onClick={loadReports} size="sm" variant="secondary">
            Odswiez
          </Button>
        }
      />

      {status === "loading" ? <LoadingState /> : null}
      {errorState ? <ErrorState description={errorState.description} title={errorState.title} /> : null}
      {organizationMissing ? (
        <EmptyState
          description={REPORTS_ORGANIZATION_REQUIRED_DESCRIPTION}
          title={REPORTS_ORGANIZATION_REQUIRED_TITLE}
        />
      ) : null}
      {readyWithoutData ? (
        <EmptyState
          description={`Dostepne endpointy odpowiedzialy, ale nie ma jeszcze danych do raportowego podsumowania dla organizacji ${selectedOrganization?.name ?? selectedOrganizationId}.`}
          title="Brak danych raportowych"
        />
      ) : null}

      {hasData && kpis && snapshot ? (
        <>
          <section className="module-kpi-row" aria-label="Podsumowanie raportow">
            <Card className="module-metric">
              <span className="module-metric__label">Tryb ekranu</span>
              <strong>{REPORTS_READ_ONLY ? "Read-only" : "Akcje wlaczone"}</strong>
              <span>Bez eksportow, generatora BI, harmonogramow i automatyzacji.</span>
            </Card>
            <Card className="module-metric">
              <span className="module-metric__label">Faktury do uwagi</span>
              <strong>{kpis.invoicesToAttention}</strong>
              <span>Weryfikacja, podejrzenia i pewne duplikaty.</span>
            </Card>
            <Card className="module-metric">
              <span className="module-metric__label">Otwarte work items</span>
              <strong>{kpis.openWorkItems}</strong>
              <span>Operacyjne pozycje pracy z aktywnej kolejki.</span>
            </Card>
            <Card className="module-metric">
              <span className="module-metric__label">Saldo rozliczen</span>
              <strong>{formatMoney(kpis.billingBalanceDue)}</strong>
              <span>Podsumowanie dodatnich i ujemnych sald ledgeru.</span>
            </Card>
          </section>

          {snapshot.missingSources.length ? (
            <Card
              description={`Czesc zrodel nie byla dostepna: ${snapshot.missingSources.join(", ")}. Widok pokazuje pozostale dane zamiast blokowac caly raport.`}
              title="Raport czesciowy"
            />
          ) : null}

          <Card
            description="Najprostsza lista sygnalow operacyjnych z modulow, ktore maja juz realne ekrany Next."
            title="Co wymaga uwagi"
          >
            <Table columns={signalColumns} data={signals} emptyMessage="Brak sygnalow operacyjnych." getRowKey={(row) => row.id} />
          </Card>

          <Card description="Szybkie przejscia do modulow, z ktorych zlozono raport read-only." title="Przeglad modulow">
            <Table columns={moduleColumns} data={moduleLinks} emptyMessage="Brak modulow raportowych." getRowKey={(row) => row.id} />
          </Card>

          <Card
            description="Ten ekran celowo nie generuje plikow i nie zapisuje konfiguracji raportow. Najpierw stabilizujemy czytelny podglad danych."
            title="Zakres MVP raportow"
          >
            <div className="module-kpi-row">
              <Card className="module-metric">
                <span className="module-metric__label">Eksport PDF/XLSX</span>
                <strong>{REPORT_EXPORTS_ENABLED ? "Aktywny" : "Nieaktywny"}</strong>
                <span>Brak generowania i pobierania plikow.</span>
              </Card>
              <Card className="module-metric">
                <span className="module-metric__label">Generator raportow</span>
                <strong>{REPORT_GENERATOR_ENABLED ? "Aktywny" : "Nieaktywny"}</strong>
                <span>Brak konfiguratora i zapisanych definicji raportow.</span>
              </Card>
              <Card className="module-metric">
                <span className="module-metric__label">Kontrahenci</span>
                <strong>{kpis.contractorsTotal}</strong>
                <span>Rekordy CRM widoczne w biezacym zakresie.</span>
              </Card>
            </div>
          </Card>
        </>
      ) : null}
    </div>
  );
}

function mapSourceResults(keys: string[], results: Array<PromiseSettledResult<unknown>>): SourceResult[] {
  return results.map((result, index) => {
    if (result.status === "fulfilled") {
      return { key: keys[index] ?? `source-${index}`, payload: result.value };
    }
    return { key: keys[index] ?? `source-${index}`, error: result.reason };
  });
}
