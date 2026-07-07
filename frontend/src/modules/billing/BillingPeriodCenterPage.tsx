"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { ArrowLeft, CalendarDays, CreditCard, RefreshCw, UsersRound, WalletCards } from "lucide-react";

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
  BILLING_CANONICAL_ROUTE,
  BILLING_ORGANIZATION_REQUIRED_DESCRIPTION,
  BILLING_ORGANIZATION_REQUIRED_TITLE,
  BILLING_READ_ONLY,
  buildBillingPeriodView,
  canUseBillingOrganizationScope,
  getBillingErrorState,
  readBillingBalances,
  readBillingCharges,
  readBillingPaymentMatches,
  readBillingPayers,
  readBillingStudents,
  type BillingCenterSnapshot,
  type BillingErrorState,
  type BillingPeriodAttentionRow,
  type BillingPeriodOptionRow,
  type BillingPeriodPayerRow,
  type BillingPeriodServiceRow,
  type BillingStatus,
} from "./billingModel";

const periodOptionColumns: Array<TableColumn<BillingPeriodOptionRow>> = [
  {
    key: "period",
    header: "Okres rozliczeniowy",
    render: (row) => (
      <span className="billing-family-cell">
        <strong>{row.label}</strong>
        <span>{row.hintLabel}</span>
      </span>
    ),
  },
  { key: "charged", header: "Naliczono", align: "right", render: (row) => row.chargedLabel },
  { key: "paid", header: "Wpłacono", align: "right", render: (row) => row.paidLabel },
  { key: "balance", header: "Saldo", align: "right", render: (row) => row.balanceLabel },
  { key: "status", header: "Status", render: (row) => <StatusBadge status={row.statusTone}>{row.statusLabel}</StatusBadge> },
];

const payerColumns: Array<TableColumn<BillingPeriodPayerRow>> = [
  {
    key: "payer",
    header: "Płatnik",
    render: (row) => (
      <Link className="module-link" href={row.href}>
        {row.payerLabel}
      </Link>
    ),
  },
  { key: "people", header: "Osoby objęte rozliczeniem", render: (row) => row.peopleLabel },
  { key: "services", header: "Usługi", render: (row) => row.servicesLabel },
  { key: "charged", header: "Naliczono", align: "right", render: (row) => row.chargedLabel },
  { key: "paid", header: "Wpłacono", align: "right", render: (row) => row.paidLabel },
  { key: "balance", header: "Saldo", align: "right", render: (row) => row.balanceLabel },
  { key: "status", header: "Status", render: (row) => <StatusBadge status={row.statusTone}>{row.statusLabel}</StatusBadge> },
];

const serviceColumns: Array<TableColumn<BillingPeriodServiceRow>> = [
  { key: "service", header: "Usługa", render: (row) => row.serviceLabel },
  { key: "type", header: "Typ", render: (row) => row.serviceTypeLabel },
  { key: "payers", header: "Płatnicy", align: "right", render: (row) => row.payerCountLabel },
  { key: "people", header: "Osoby", align: "right", render: (row) => row.personCountLabel },
  { key: "charged", header: "Suma naliczeń", align: "right", render: (row) => row.chargedLabel },
  { key: "source", header: "Źródło danych", render: (row) => row.sourceLabel },
];

const attentionColumns: Array<TableColumn<BillingPeriodAttentionRow>> = [
  {
    key: "title",
    header: "Sygnał",
    render: (row) => (
      <Link className="module-link" href={row.href}>
        {row.titleLabel}
      </Link>
    ),
  },
  { key: "reason", header: "Dlaczego wymaga uwagi", render: (row) => row.reasonLabel },
  { key: "status", header: "Status", render: (row) => <StatusBadge status={row.tone}>{row.tone === "danger" ? "Pilne" : row.tone === "warning" ? "Do kontroli" : "Informacja"}</StatusBadge> },
];

export function BillingPeriodCenterPage() {
  const { selectedOrganizationId, selectedOrganization, status: organizationStatus } = useActiveOrganization();
  const [snapshot, setSnapshot] = useState<BillingCenterSnapshot | null>(null);
  const [status, setStatus] = useState<BillingStatus>("idle");
  const [errorState, setErrorState] = useState<BillingErrorState | null>(null);
  const [selectedPeriodId, setSelectedPeriodId] = useState<string | null>(null);

  const loadPeriods = useCallback(async () => {
    if (organizationStatus === "loading") {
      setStatus("loading");
      setErrorState(null);
      return;
    }

    if (!canUseBillingOrganizationScope(selectedOrganizationId)) {
      setSnapshot(null);
      setErrorState(null);
      setStatus("ready");
      return;
    }

    setStatus("loading");
    setErrorState(null);

    try {
      const query = withActiveOrganizationQuery(selectedOrganizationId);
      const [balancesPayload, payersPayload, studentsPayload, chargesPayload, matchesPayload] = await Promise.all([
        api.ledgerBalances(query),
        api.billingPayers(query),
        api.billingStudents(query),
        api.billingCharges(withActiveOrganizationQuery(selectedOrganizationId, { limit: 500 })),
        api.billingLedgerMatches(withActiveOrganizationQuery(selectedOrganizationId, { limit: 1000 })),
      ]);

      setSnapshot({
        balances: readBillingBalances(balancesPayload),
        payers: readBillingPayers(payersPayload),
        students: readBillingStudents(studentsPayload),
        charges: readBillingCharges(chargesPayload),
        paymentMatches: readBillingPaymentMatches(matchesPayload),
        invoices: [],
        contractors: [],
        workItems: [],
      });
      setStatus("ready");
    } catch (error) {
      const nextErrorState = getBillingErrorState(error);
      setSnapshot(null);
      setErrorState(nextErrorState);
      setStatus(nextErrorState.status);
    }
  }, [organizationStatus, selectedOrganizationId]);

  useEffect(() => {
    void loadPeriods();
  }, [loadPeriods]);

  const periodView = useMemo(() => (snapshot ? buildBillingPeriodView(snapshot, selectedPeriodId) : null), [selectedPeriodId, snapshot]);

  useEffect(() => {
    if (periodView && periodView.selectedPeriodId !== selectedPeriodId) {
      setSelectedPeriodId(periodView.selectedPeriodId);
    }
  }, [periodView, selectedPeriodId]);

  const organizationMissing = organizationStatus === "ready" && !canUseBillingOrganizationScope(selectedOrganizationId);
  const readyWithoutData = status === "ready" && snapshot && !periodView && !organizationMissing;

  return (
    <div className="module-page billing-page billing-period-page">
      <PageHeader
        badgeTone={status === "ready" ? "success" : status === "error" ? "warning" : "info"}
        description="Sprawdź, jak wygląda rozliczenie za konkretny miesiąc, semestr albo turnus. Widok jest tylko do odczytu."
        eyebrow="Rozliczenia"
        title="Okresy rozliczeniowe"
        actions={
          <div className="module-page-actions">
            <Link className="ui-button ui-button--secondary ui-button--sm" href={BILLING_CANONICAL_ROUTE}>
              <span className="ui-button__icon"><ArrowLeft size={15} /></span>
              <span>Wróć do rozliczeń</span>
            </Link>
            <Button disabled={status === "loading"} icon={<RefreshCw size={15} />} onClick={loadPeriods} size="sm" variant="secondary">
              Odśwież
            </Button>
          </div>
        }
      />

      {status === "loading" ? <LoadingState /> : null}
      {errorState ? <ErrorState description={errorState.description} title={errorState.title} /> : null}
      {organizationMissing ? <EmptyState description={BILLING_ORGANIZATION_REQUIRED_DESCRIPTION} title={BILLING_ORGANIZATION_REQUIRED_TITLE} /> : null}
      {readyWithoutData ? (
        <EmptyState
          description="Nie ma jeszcze naliczeń z etykietą okresu dla wybranej organizacji. Widok okresowy pojawi się, gdy dane rozliczeń pozwolą wskazać miesiąc, semestr albo turnus."
          title="Brak okresów rozliczeniowych"
        />
      ) : null}

      {status === "ready" && periodView ? (
        <>
          <Card
            action={<StatusBadge status={periodView.summary.balanceLabel.startsWith("0,00") ? "ok" : "warning"}>{BILLING_READ_ONLY ? "Tylko odczyt" : "Akcje włączone"}</StatusBadge>}
            description={`Widok dla organizacji ${selectedOrganization?.name ?? selectedOrganizationId}. ${periodView.selectedPeriodHint}`}
            title="Nagłówek okresów"
          >
            <div className="billing-center-hero" aria-label="Podsumowanie okresu">
              <div>
                <span>Wybrany okres</span>
                <strong>{periodView.selectedPeriodLabel}</strong>
              </div>
              <div>
                <span>Naliczono</span>
                <strong>{periodView.summary.chargedLabel}</strong>
              </div>
              <div>
                <span>Wpłacono</span>
                <strong>{periodView.summary.paidLabel}</strong>
              </div>
            </div>
          </Card>

          <section className="module-kpi-row" aria-label="Podsumowanie okresu rozliczeniowego">
            <Card className="module-metric">
              <span className="module-metric__icon"><WalletCards aria-hidden="true" size={18} /></span>
              <span className="module-metric__label">Saldo okresu</span>
              <strong>{periodView.summary.balanceLabel}</strong>
              <span>{periodView.summary.sourceLabel}</span>
            </Card>
            <Card className="module-metric">
              <span className="module-metric__icon"><UsersRound aria-hidden="true" size={18} /></span>
              <span className="module-metric__label">Płatnicy i osoby</span>
              <strong>{periodView.summary.payerCountLabel} / {periodView.summary.personCountLabel}</strong>
              <span>Płatnicy oraz osoby objęte rozliczeniem.</span>
            </Card>
            <Card className="module-metric">
              <span className="module-metric__icon"><CalendarDays aria-hidden="true" size={18} /></span>
              <span className="module-metric__label">Usługi</span>
              <strong>{periodView.summary.serviceCountLabel}</strong>
              <span>Usługi widoczne przez naliczenia okresu.</span>
            </Card>
            <Card className="module-metric">
              <span className="module-metric__icon"><CreditCard aria-hidden="true" size={18} /></span>
              <span className="module-metric__label">Statusy</span>
              <strong>{periodView.summary.dueCountLabel} / {periodView.summary.overpaidCountLabel} / {periodView.summary.settledCountLabel}</strong>
              <span>Do dopłaty / nadpłata / rozliczone.</span>
            </Card>
          </section>

          <section className="invoice-detail-grid billing-center-grid" aria-label="Okres rozliczeniowy">
            <div className="invoice-detail-grid__main">
              <Card description="Lista okresów wyprowadzona z naliczeń. Wybór zmienia podsumowanie bez wykonywania operacji finansowych." title="Wybór okresu">
                <label className="ui-field">
                  <span>Okres rozliczeniowy</span>
                  <select value={periodView.selectedPeriodId} onChange={(event) => setSelectedPeriodId(event.target.value)}>
                    {periodView.options.map((option) => (
                      <option key={option.id} value={option.id}>{option.label}</option>
                    ))}
                  </select>
                </label>
                <Table columns={periodOptionColumns} data={periodView.options} emptyMessage="Brak okresów do pokazania." getRowKey={(row) => row.id} />
              </Card>

              <Card description="Płatnicy, osoby i usługi widoczne w wybranym okresie. Wpłaty obejmują tylko dopasowania do naliczeń tego okresu." title="Płatnicy w okresie">
                <Table columns={payerColumns} data={periodView.payerRows} emptyMessage="Brak płatników w tym okresie." getRowKey={(row) => row.id} />
              </Card>

              <Card description="Usługi z naliczeń wybranego okresu. To nie jest jeszcze pełny cennik ani model zapisów." title="Usługi w okresie">
                <Table columns={serviceColumns} data={periodView.serviceRows} emptyMessage="Brak usług w tym okresie." getRowKey={(row) => row.id} />
              </Card>

              <Card description="Deterministyczne sygnały z naliczeń i widocznych dopasowań płatności." title="Co wymaga uwagi">
                <Table columns={attentionColumns} data={periodView.attentionRows} emptyMessage="Brak oczywistych sygnałów wymagających uwagi w tym okresie." getRowKey={(row) => row.id} />
              </Card>
            </div>

            <aside className="module-activity-panel" aria-label="Kontekst biznesowy okresu">
              <Card title="Kontekst biznesowy">
                <div className="billing-context-list">
                  {periodView.contextItems.map((item) => (
                    <article key={item.label}>
                      <span>{item.label}</span>
                      <strong>{item.value}</strong>
                    </article>
                  ))}
                </div>
              </Card>
              <Card className="module-quick-actions" title="Przejdź dalej">
                <Link className="module-quick-action" href={BILLING_CANONICAL_ROUTE}>
                  <span>Rozliczenia</span>
                  <CreditCard aria-hidden="true" size={15} />
                </Link>
              </Card>
            </aside>
          </section>
        </>
      ) : null}
    </div>
  );
}
