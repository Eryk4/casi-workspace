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
  BILLING_PAYMENT_DETAIL_ORGANIZATION_REQUIRED_DESCRIPTION,
  BILLING_PAYMENT_DETAIL_ORGANIZATION_REQUIRED_TITLE,
  BILLING_PAYMENTS_ROUTE,
  BILLING_PERIODS_ROUTE,
  buildBillingPaymentDetailView,
  canUseBillingOrganizationScope,
  getBillingErrorState,
  readBillingCharges,
  readBillingPaymentMatches,
  readBillingPayers,
  readBillingStudents,
  readBillingTransactions,
  type BillingCenterSnapshot,
  type BillingErrorState,
  type BillingPaymentDetailAssignmentRow,
  type BillingPaymentDetailChargeRow,
  type BillingPaymentDetailView,
  type BillingStatus,
} from "./billingModel";

const assignmentColumns: Array<TableColumn<BillingPaymentDetailAssignmentRow>> = [
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
  { key: "person", header: "Osoba", render: (row) => row.personLabel },
  { key: "service", header: "Usługa", render: (row) => row.serviceLabel },
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
  { key: "amount", header: "Kwota", align: "right", render: (row) => row.amountLabel },
  { key: "status", header: "Przypisanie", render: (row) => row.statusLabel },
  { key: "context", header: "Kontekst", render: (row) => row.contextLabel },
];

const chargeColumns: Array<TableColumn<BillingPaymentDetailChargeRow>> = [
  { key: "period", header: "Okres", render: (row) => row.periodLabel },
  { key: "person", header: "Osoba", render: (row) => row.personLabel },
  { key: "service", header: "Usługa", render: (row) => row.serviceLabel },
  { key: "amount", header: "Kwota naliczenia", align: "right", render: (row) => row.amountLabel },
  { key: "status", header: "Status naliczenia", render: (row) => row.statusLabel },
];

export function BillingPaymentDetailPage({ paymentId }: { paymentId: number }) {
  const { selectedOrganizationId, selectedOrganization, status: organizationStatus } = useActiveOrganization();
  const [snapshot, setSnapshot] = useState<BillingCenterSnapshot | null>(null);
  const [status, setStatus] = useState<BillingStatus>("idle");
  const [errorState, setErrorState] = useState<BillingErrorState | null>(null);

  const loadPayment = useCallback(async () => {
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
      const [payersPayload, studentsPayload, chargesPayload, matchesPayload, transactionsPayload] = await Promise.all([
        api.billingPayers(withActiveOrganizationQuery(selectedOrganizationId)),
        api.billingStudents(withActiveOrganizationQuery(selectedOrganizationId)),
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
    void loadPayment();
  }, [loadPayment]);

  const detail = useMemo<BillingPaymentDetailView | null>(() => (snapshot ? buildBillingPaymentDetailView(snapshot, paymentId) : null), [paymentId, snapshot]);
  const organizationMissing = organizationStatus === "ready" && !canUseBillingOrganizationScope(selectedOrganizationId);
  const notFound = status === "ready" && snapshot && !detail;
  const headerBadgeTone = detail?.statusTone === "ok" ? "success" : detail?.statusTone ?? (status === "error" ? "warning" : "info");

  return (
    <div className="module-page billing-page billing-payment-detail-page">
      <PageHeader
        badgeTone={headerBadgeTone}
        description="Read-only widok pojedynczej wpłaty: kwota, płatnik i obecne przypisanie bez zmiany salda."
        eyebrow="Rozliczenia"
        title={detail?.title ?? "Szczegół wpłaty"}
        actions={
          <div className="module-page-actions">
            <Link className="ui-button ui-button--secondary ui-button--sm" href={BILLING_PAYMENTS_ROUTE}>
              <span className="ui-button__icon"><ArrowLeft size={15} /></span>
              <span>Wróć do wpłat</span>
            </Link>
            <Button disabled={status === "loading"} icon={<RefreshCw size={15} />} onClick={loadPayment} size="sm" variant="secondary">
              Odśwież
            </Button>
          </div>
        }
      />

      {status === "loading" ? <LoadingState /> : null}
      {errorState ? <ErrorState description={errorState.description} title={errorState.title} /> : null}
      {organizationMissing ? (
        <EmptyState description={BILLING_PAYMENT_DETAIL_ORGANIZATION_REQUIRED_DESCRIPTION} title={BILLING_PAYMENT_DETAIL_ORGANIZATION_REQUIRED_TITLE} />
      ) : null}
      {notFound ? (
        <EmptyState
          description="Ta wpłata nie istnieje w wybranej organizacji albo nie jest dostępna dla bieżącego użytkownika."
          title="Nie znaleziono wpłaty"
        />
      ) : null}

      {status === "ready" && detail ? (
        <>
          <Card
            action={<StatusBadge status={detail.statusTone}>{detail.statusLabel}</StatusBadge>}
            description={`Widok dla organizacji ${selectedOrganization?.name ?? selectedOrganizationId}. Ten widok nie zmienia salda ani przypisania wpłaty.`}
            title="Profil wpłaty"
          >
            <div className="billing-center-hero" aria-label="Profil wpłaty">
              <div>
                <span>Kwota</span>
                <strong>{detail.amountLabel}</strong>
              </div>
              <div>
                <span>Data</span>
                <strong>{detail.dateLabel}</strong>
              </div>
              <div>
                <span>Przypisanie</span>
                <strong>{detail.statusLabel}</strong>
              </div>
            </div>
          </Card>

          <section className="module-kpi-row" aria-label="Podsumowanie wpłaty">
            <Card className="module-metric">
              <span className="module-metric__icon"><WalletCards aria-hidden="true" size={18} /></span>
              <span className="module-metric__label">Opis</span>
              <strong>{detail.descriptionLabel}</strong>
              <span>Bez surowych danych technicznych.</span>
            </Card>
            <Card className="module-metric">
              <span className="module-metric__icon"><CreditCard aria-hidden="true" size={18} /></span>
              <span className="module-metric__label">Płatnik</span>
              <strong>{detail.payerLabel}</strong>
              <span>{detail.payerHref ? "Płatnik jest znany w obecnym przypisaniu." : "Brak pewnego płatnika w danych."}</span>
            </Card>
            <Card className="module-metric">
              <span className="module-metric__icon"><CalendarDays aria-hidden="true" size={18} /></span>
              <span className="module-metric__label">Przypisano</span>
              <strong>{detail.assignedAmountLabel}</strong>
              <span>Kwota widoczna w obecnych przypisaniach.</span>
            </Card>
            <Card className="module-metric">
              <span className="module-metric__icon"><WalletCards aria-hidden="true" size={18} /></span>
              <span className="module-metric__label">Do wyjaśnienia</span>
              <strong>{detail.remainingAmountLabel}</strong>
              <span>Widok nie dopasowuje pozostałej kwoty.</span>
            </Card>
          </section>

          <section className="module-grid module-grid--wide-main" aria-label="Szczegół wpłaty">
            <div className="module-stack">
              <Card description={detail.assignmentSummaryLabel} title="Przypisanie wpłaty">
                <Table columns={assignmentColumns} data={detail.assignmentRows} emptyMessage="Ta wpłata wymaga późniejszego wyjaśnienia." getRowKey={(row) => row.id} />
              </Card>

              <Card description="Pokazujemy tylko naliczenia bezpiecznie powiązane z tą wpłatą." title="Powiązane naliczenia">
                <Table
                  columns={chargeColumns}
                  data={detail.chargeRows}
                  emptyMessage="Brak przypisanego naliczenia. Pełne przypisywanie wpłat będzie osobnym etapem."
                  getRowKey={(row) => row.id}
                />
              </Card>
            </div>

            <aside className="module-stack">
              <Card title="Kontekst biznesowy">
                <div className="billing-context-list">
                  {detail.contextItems.map((item) => (
                    <article key={item.label}>
                      <span>{item.label}</span>
                      <strong>{item.value}</strong>
                    </article>
                  ))}
                </div>
              </Card>

              <Card className="module-quick-actions" title="Przejdź dalej">
                <Link className="module-quick-action" href={BILLING_PAYMENTS_ROUTE}>
                  <span>Wpłaty i przypisania</span>
                  <WalletCards aria-hidden="true" size={15} />
                </Link>
                {detail.payerHref ? (
                  <Link className="module-quick-action" href={detail.payerHref}>
                    <span>Płatnik</span>
                    <CreditCard aria-hidden="true" size={15} />
                  </Link>
                ) : null}
                <Link className="module-quick-action" href={BILLING_PERIODS_ROUTE}>
                  <span>Okresy rozliczeniowe</span>
                  <CalendarDays aria-hidden="true" size={15} />
                </Link>
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
