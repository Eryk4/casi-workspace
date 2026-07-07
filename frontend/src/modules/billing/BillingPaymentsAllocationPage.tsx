"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { ArrowLeft, CalendarDays, CreditCard, RefreshCw, WalletCards } from "lucide-react";

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
  BILLING_PERIODS_ROUTE,
  BILLING_READ_ONLY,
  buildBillingPaymentsAllocationView,
  canUseBillingOrganizationScope,
  getBillingErrorState,
  readBillingCharges,
  readBillingPaymentMatches,
  readBillingPayers,
  readBillingStudents,
  readBillingTransactions,
  type BillingCenterSnapshot,
  type BillingErrorState,
  type BillingPaymentAssignmentRow,
  type BillingStatus,
} from "./billingModel";

const paymentColumns: Array<TableColumn<BillingPaymentAssignmentRow>> = [
  { key: "date", header: "Data", render: (row) => row.dateLabel },
  { key: "amount", header: "Kwota", align: "right", render: (row) => row.amountLabel },
  {
    key: "payer",
    header: "Płatnik",
    render: (row) =>
      row.payerHref ? (
        <Link className="module-link" href={row.payerHref}>
          {row.payerLabel}
        </Link>
      ) : (
        row.payerLabel
      ),
  },
  { key: "description", header: "Opis wpłaty", render: (row) => row.descriptionLabel },
  { key: "assignment", header: "Przypisanie", render: (row) => row.assignmentLabel },
  {
    key: "period",
    header: "Okres",
    render: (row) =>
      row.periodHref ? (
        <Link className="module-link" href={row.periodHref}>
          {row.periodLabel}
        </Link>
      ) : (
        row.periodLabel
      ),
  },
  { key: "status", header: "Status", render: (row) => <StatusBadge status={row.statusTone}>{row.statusLabel}</StatusBadge> },
];

export function BillingPaymentsAllocationPage() {
  const { selectedOrganizationId, selectedOrganization, status: organizationStatus } = useActiveOrganization();
  const [snapshot, setSnapshot] = useState<BillingCenterSnapshot | null>(null);
  const [status, setStatus] = useState<BillingStatus>("idle");
  const [errorState, setErrorState] = useState<BillingErrorState | null>(null);

  const loadPayments = useCallback(async () => {
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
      const [payersPayload, studentsPayload, chargesPayload, matchesPayload, transactionsPayload] = await Promise.all([
        api.billingPayers(query),
        api.billingStudents(query),
        api.billingCharges(withActiveOrganizationQuery(selectedOrganizationId, { limit: 1000 })),
        api.billingLedgerMatches(withActiveOrganizationQuery(selectedOrganizationId, { limit: 1000 })),
        api.billingTransactions(withActiveOrganizationQuery(selectedOrganizationId, { limit: 1000 })),
      ]);

      setSnapshot({
        balances: [],
        payers: readBillingPayers(payersPayload),
        students: readBillingStudents(studentsPayload),
        charges: readBillingCharges(chargesPayload),
        paymentMatches: readBillingPaymentMatches(matchesPayload),
        transactions: readBillingTransactions(transactionsPayload),
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
    void loadPayments();
  }, [loadPayments]);

  const paymentsView = useMemo(() => (snapshot ? buildBillingPaymentsAllocationView(snapshot) : null), [snapshot]);
  const organizationMissing = organizationStatus === "ready" && !canUseBillingOrganizationScope(selectedOrganizationId);
  const readyWithoutData =
    status === "ready" &&
    paymentsView &&
    !organizationMissing &&
    !paymentsView.chargeAssignedRows.length &&
    !paymentsView.payerOnlyRows.length &&
    !paymentsView.unexplainedRows.length;

  return (
    <div className="module-page billing-page billing-payments-page">
      <PageHeader
        badgeTone={status === "ready" ? "success" : status === "error" ? "warning" : "info"}
        description="Sprawdź widoczne wpłaty i to, czy można je bezpiecznie powiązać z naliczeniem, płatnikiem albo późniejszym wyjaśnieniem."
        eyebrow="Rozliczenia"
        title="Wpłaty i przypisania"
        actions={
          <div className="module-page-actions">
            <Link className="ui-button ui-button--secondary ui-button--sm" href={BILLING_CANONICAL_ROUTE}>
              <span className="ui-button__icon"><ArrowLeft size={15} /></span>
              <span>Wróć do rozliczeń</span>
            </Link>
            <Button disabled={status === "loading"} icon={<RefreshCw size={15} />} onClick={loadPayments} size="sm" variant="secondary">
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
          description="Nie ma jeszcze widocznych wpłat dla wybranej organizacji. Ten widok pojawi się, gdy dane rozliczeń pokażą wpływy albo ich przypisania."
          title="Brak wpłat do pokazania"
        />
      ) : null}

      {status === "ready" && paymentsView && !organizationMissing && !readyWithoutData ? (
        <>
          <Card
            action={<StatusBadge status="info">{BILLING_READ_ONLY ? "Tylko odczyt" : "Akcje włączone"}</StatusBadge>}
            description={`Widok dla organizacji ${selectedOrganization?.name ?? selectedOrganizationId}. Nie dodaje wpłat i nie zmienia przypisań.`}
            title="Kontrola widocznych wpłat"
          >
            <div className="billing-center-hero" aria-label="Podsumowanie wpłat">
              <div>
                <span>Suma widocznych wpłat</span>
                <strong>{paymentsView.summary.totalVisibleAmountLabel}</strong>
              </div>
              <div>
                <span>Przypisane do naliczeń</span>
                <strong>{paymentsView.summary.chargeAssignedAmountLabel}</strong>
              </div>
              <div>
                <span>Do późniejszego wyjaśnienia</span>
                <strong>{paymentsView.summary.needsExplanationAmountLabel}</strong>
              </div>
            </div>
          </Card>

          <section className="module-kpi-row" aria-label="Podsumowanie wpłat i przypisań">
            <Card className="module-metric">
              <span className="module-metric__icon"><WalletCards aria-hidden="true" size={18} /></span>
              <span>Wpłaty</span>
              <strong>{paymentsView.summary.paymentCountLabel}</strong>
            </Card>
            <Card className="module-metric">
              <span className="module-metric__icon"><CreditCard aria-hidden="true" size={18} /></span>
              <span>Przy naliczeniach</span>
              <strong>{paymentsView.summary.chargeAssignedCountLabel}</strong>
            </Card>
            <Card className="module-metric">
              <span className="module-metric__icon"><WalletCards aria-hidden="true" size={18} /></span>
              <span>Tylko przy płatniku</span>
              <strong>{paymentsView.summary.payerOnlyCountLabel}</strong>
            </Card>
            <Card className="module-metric">
              <span className="module-metric__icon"><CalendarDays aria-hidden="true" size={18} /></span>
              <span>Bez jasnego przypisania</span>
              <strong>{paymentsView.summary.unexplainedCountLabel}</strong>
            </Card>
          </section>

          <section className="module-grid module-grid--wide-main">
            <div className="module-stack">
              <Card
                description="Te wpłaty mają relację z konkretnym naliczeniem, więc można je pokazać przy okresie."
                title="Wpłaty przypisane do naliczeń"
              >
                <Table
                  columns={paymentColumns}
                  data={paymentsView.chargeAssignedRows}
                  emptyMessage="Brak wpłat bezpiecznie powiązanych z naliczeniami."
                  getRowKey={(row) => row.id}
                />
              </Card>

              <Card
                description="Wpłata jest widoczna przy płatniku, ale nie została jeszcze przypisana do konkretnego naliczenia."
                title="Wpłaty przypisane tylko do płatnika"
              >
                <Table
                  columns={paymentColumns}
                  data={paymentsView.payerOnlyRows}
                  emptyMessage="Brak wpłat przypisanych wyłącznie do płatnika."
                  getRowKey={(row) => row.id}
                />
              </Card>

              <Card
                description="Te wpłaty nie mają jeszcze wystarczającego kontekstu, żeby uczciwie pokazać je przy płatniku albo okresie."
                title="Wpłaty wymagające wyjaśnienia"
              >
                <Table
                  columns={paymentColumns}
                  data={paymentsView.unexplainedRows}
                  emptyMessage="Brak osobnej listy nieprzypisanych wpłat w obecnym modelu danych."
                  getRowKey={(row) => row.id}
                />
              </Card>
            </div>

            <aside className="module-stack">
              <Card title="Kontekst biznesowy">
                <div className="billing-context-list">
                  {paymentsView.contextItems.map((item) => (
                    <article key={item.label}>
                      <span>{item.label}</span>
                      <strong>{item.value}</strong>
                    </article>
                  ))}
                </div>
              </Card>

              <Card className="module-quick-actions" title="Przejdź dalej">
                <Link className="module-quick-action" href={BILLING_CANONICAL_ROUTE}>
                  <span>Centrum rozliczeń</span>
                  <WalletCards aria-hidden="true" size={15} />
                </Link>
                <Link className="module-quick-action" href={BILLING_PERIODS_ROUTE}>
                  <span>Okresy rozliczeniowe</span>
                  <CalendarDays aria-hidden="true" size={15} />
                </Link>
              </Card>
            </aside>
          </section>
        </>
      ) : null}
    </div>
  );
}
