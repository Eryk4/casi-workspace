"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Banknote, CreditCard, RefreshCw } from "lucide-react";

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
import {
  BILLING_BALANCES_ENDPOINT,
  BILLING_ORGANIZATION_REQUIRED_DESCRIPTION,
  BILLING_ORGANIZATION_REQUIRED_TITLE,
  BILLING_READ_ONLY,
  buildBillingBalanceRows,
  buildBillingKpis,
  canUseBillingOrganizationScope,
  formatMoney,
  getBillingErrorState,
  hasBillingData,
  isBillingEmpty,
  readBillingBalances,
  type BillingBalanceRecord,
  type BillingBalanceViewRow,
  type BillingErrorState,
  type BillingStatus,
} from "./billingModel";

type BillingLedgerOverviewProps = {
  title: "Kasa" | "Rozliczenia";
  eyebrow: string;
  description: string;
};

const columns: Array<TableColumn<BillingBalanceViewRow>> = [
  {
    key: "payer",
    header: "Platnik",
    render: (row) => (
      <span className="module-row-title">
        <CreditCard aria-hidden="true" size={16} />
        {row.payerLabel}
      </span>
    ),
  },
  {
    key: "status",
    header: "Status",
    render: (row) => <StatusBadge status={row.statusTone}>{row.statusLabel}</StatusBadge>,
  },
  {
    key: "contact",
    header: "Kontakt",
    render: (row) => row.contactLabel,
  },
  {
    key: "charges",
    header: "Naliczenia",
    align: "right",
    render: (row) => row.totalChargesLabel,
  },
  {
    key: "matches",
    header: "Wplaty",
    align: "right",
    render: (row) => row.totalMatchesLabel,
  },
  {
    key: "balance",
    header: "Saldo",
    align: "right",
    render: (row) => row.balanceDueLabel,
  },
  {
    key: "lastPayment",
    header: "Ostatnia wplata",
    render: (row) => row.lastPaymentLabel,
  },
  {
    key: "matchedCount",
    header: "Dopas.",
    align: "right",
    render: (row) => row.matchedPaymentCountLabel,
  },
];

export function BillingLedgerOverview({ title, eyebrow, description }: BillingLedgerOverviewProps) {
  const { selectedOrganizationId, selectedOrganization, status: organizationStatus } = useActiveOrganization();
  const [balances, setBalances] = useState<BillingBalanceRecord[] | null>(null);
  const [status, setStatus] = useState<BillingStatus>("idle");
  const [errorState, setErrorState] = useState<BillingErrorState | null>(null);

  const loadBalances = useCallback(async () => {
    if (organizationStatus === "loading") {
      setStatus("loading");
      setErrorState(null);
      return;
    }

    if (!canUseBillingOrganizationScope(selectedOrganizationId)) {
      setBalances([]);
      setErrorState(null);
      setStatus("ready");
      return;
    }

    setStatus("loading");
    setErrorState(null);

    try {
      const payload = await api.ledgerBalances(withActiveOrganizationQuery(selectedOrganizationId));
      const nextBalances = readBillingBalances(payload);
      setBalances(nextBalances);
      setStatus("ready");
    } catch (error) {
      const nextErrorState = getBillingErrorState(error);
      setErrorState(nextErrorState);
      setBalances(null);
      setStatus(nextErrorState.status);
    }
  }, [organizationStatus, selectedOrganizationId]);

  useEffect(() => {
    void loadBalances();
  }, [loadBalances]);

  const rows = useMemo(() => buildBillingBalanceRows(balances ?? []), [balances]);
  const kpis = useMemo(() => buildBillingKpis(balances ?? []), [balances]);
  const hasData = hasBillingData(status, balances);
  const organizationMissing = organizationStatus === "ready" && !canUseBillingOrganizationScope(selectedOrganizationId);
  const readyWithoutData = !organizationMissing && isBillingEmpty(status, balances);

  return (
    <div className="module-page billing-page">
      <PageHeader
        badgeTone={status === "ready" ? "success" : status === "error" ? "warning" : "info"}
        description={description}
        eyebrow={status === "ready" ? "Dane live" : eyebrow}
        title={title}
        actions={
          <Button disabled={status === "loading"} icon={<RefreshCw size={15} />} onClick={loadBalances} size="sm" variant="secondary">
            Odswiez
          </Button>
        }
      />

      {status === "loading" ? <LoadingState /> : null}
      {errorState ? <ErrorState description={errorState.description} title={errorState.title} /> : null}
      {organizationMissing ? (
        <EmptyState
          description={BILLING_ORGANIZATION_REQUIRED_DESCRIPTION}
          title={BILLING_ORGANIZATION_REQUIRED_TITLE}
        />
      ) : null}
      {readyWithoutData ? (
        <EmptyState
          description={`Backend odpowiedzial poprawnie, ale nie zwrocil jeszcze platnikow ani sald dla organizacji ${selectedOrganization?.name ?? selectedOrganizationId}.`}
          title="Brak danych rozliczeniowych"
        />
      ) : null}

      {hasData ? (
        <>
          <section className="module-kpi-row" aria-label="Podsumowanie rozliczen">
            <Card className="module-metric">
              <span className="module-metric__label">Tryb ekranu</span>
              <strong>{BILLING_READ_ONLY ? "Read-only" : "Akcje wlaczone"}</strong>
              <span>Bez importu wyciagow, edycji naliczen i recznego dopasowania.</span>
            </Card>
            <Card className="module-metric">
              <span className="module-metric__label">Platnicy aktywni</span>
              <strong>
                {kpis.activePayerCount}/{kpis.payerCount}
              </strong>
              <span>Pobrane z {BILLING_BALANCES_ENDPOINT}.</span>
            </Card>
            <Card className="module-metric">
              <span className="module-metric__label">Naliczenia / wplaty</span>
              <strong>{formatMoney(kpis.totalCharges)}</strong>
              <span>Wplaty dopasowane: {formatMoney(kpis.totalMatches)}.</span>
            </Card>
            <Card className="module-metric">
              <span className="module-metric__label">Saldo do rozliczenia</span>
              <strong>{formatMoney(kpis.totalBalanceDue)}</strong>
              <span>{kpis.overdueCount} platnikow z dodatnim saldem.</span>
            </Card>
          </section>

          <Card
            description="Minimalny podglad ledgeru platnikow. Import wyciagow, generowanie naliczen, reczne dopasowania i raporty zostaja poza zakresem tego kroku."
            title="Salda platnikow"
          >
            <Table
              columns={columns}
              data={rows}
              emptyMessage="Backend nie zwrocil sald rozliczen."
              getRowKey={(row) => row.id}
            />
          </Card>

          <Card
            description="Ten panel celowo nie uruchamia operacji finansowych. Pokazuje tylko, ktore funkcje sa nastepnymi kandydatami po stabilizacji read-only."
            title="Nastepne akcje, jeszcze wylaczone"
          >
            <div className="module-kpi-row">
              <Card className="module-metric">
                <span className="module-metric__label">
                  <Banknote aria-hidden="true" size={14} /> Import wyciagu
                </span>
                <strong>Nieaktywny</strong>
                <span>Wymaga osobnego kroku i walidacji CSV.</span>
              </Card>
              <Card className="module-metric">
                <span className="module-metric__label">Dopasowanie wplat</span>
                <strong>Nieaktywne</strong>
                <span>Backend istnieje, ale UI akcji nie jest czescia MVP read-only.</span>
              </Card>
              <Card className="module-metric">
                <span className="module-metric__label">Naliczenia</span>
                <strong>Nieaktywne</strong>
                <span>Widok nie generuje ani nie edytuje oplat.</span>
              </Card>
            </div>
          </Card>
        </>
      ) : null}
    </div>
  );
}
