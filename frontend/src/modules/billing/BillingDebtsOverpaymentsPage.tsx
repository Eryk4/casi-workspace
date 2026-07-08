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
  BILLING_PAYMENTS_ROUTE,
  BILLING_PERIODS_ROUTE,
  BILLING_WORK_QUEUE_ROUTE,
  BILLING_READ_ONLY,
  buildBillingDebtsOverpaymentsView,
  canUseBillingOrganizationScope,
  getBillingErrorState,
  readBillingBalances,
  readBillingCharges,
  readBillingPayerNotes,
  readBillingPaymentMatches,
  readBillingPayers,
  readBillingStudents,
  readBillingTransactions,
  type BillingCenterSnapshot,
  type BillingDebtDecisionRow,
  type BillingErrorState,
  type BillingExplanationDecisionRow,
  type BillingOverpaymentDecisionRow,
  type BillingStatus,
  type BillingUrgentDecisionRow,
} from "./billingModel";

const urgentColumns: Array<TableColumn<BillingUrgentDecisionRow>> = [
  {
    key: "payer",
    header: "Płatnik",
    render: (row) => (
      <Link className="module-link" href={row.payerHref}>
        {row.payerLabel}
      </Link>
    ),
  },
  { key: "amount", header: "Kwota", align: "right", render: (row) => row.amountLabel },
  { key: "reason", header: "Dlaczego ważne", render: (row) => row.reasonLabel },
  { key: "next", header: "Następny krok", render: (row) => row.nextStepLabel },
  {
    key: "links",
    header: "Dalej",
    render: (row) => (
      <span className="billing-inline-links">
        <Link className="module-link" href={row.payerHref}>Płatnik</Link>
        {row.paymentsHref ? <Link className="module-link" href={row.paymentsHref}>Wpłaty</Link> : null}
      </span>
    ),
  },
];

const debtColumns: Array<TableColumn<BillingDebtDecisionRow>> = [
  {
    key: "payer",
    header: "Płatnik",
    render: (row) => (
      <span className="billing-family-cell">
        <Link className="module-link" href={row.payerHref}>{row.payerLabel}</Link>
        <span>{row.peopleLabel}</span>
      </span>
    ),
  },
  { key: "amount", header: "Zaległość", align: "right", render: (row) => row.amountLabel },
  {
    key: "scope",
    header: "Okresy i usługi",
    render: (row) => (
      <span className="billing-family-cell">
        <span>{row.periodsLabel}</span>
        <span>{row.servicesLabel}</span>
      </span>
    ),
  },
  { key: "lastPayment", header: "Ostatnia wpłata", render: (row) => row.lastPaymentLabel },
  { key: "status", header: "Status uwagi", render: (row) => <StatusBadge status={row.attentionTone}>{row.attentionStatusLabel}</StatusBadge> },
  { key: "reason", header: "Powód", render: (row) => row.reasonLabel },
  {
    key: "links",
    header: "Linki",
    render: (row) => (
      <span className="billing-inline-links">
        <Link className="module-link" href={row.payerHref}>Szczegół płatnika</Link>
        <Link className="module-link" href={row.paymentsHref}>Wpłaty</Link>
        {row.periodsHref ? <Link className="module-link" href={row.periodsHref}>Okresy</Link> : null}
      </span>
    ),
  },
];

const overpaymentColumns: Array<TableColumn<BillingOverpaymentDecisionRow>> = [
  {
    key: "payer",
    header: "Płatnik",
    render: (row) => (
      <span className="billing-family-cell">
        <Link className="module-link" href={row.payerHref}>{row.payerLabel}</Link>
        <span>{row.peopleLabel}</span>
      </span>
    ),
  },
  { key: "amount", header: "Nadpłata", align: "right", render: (row) => row.amountLabel },
  { key: "lastPayment", header: "Ostatnia wpłata", render: (row) => row.lastPaymentLabel },
  { key: "source", header: "Możliwe źródło", render: (row) => row.possibleSourceLabel },
  { key: "status", header: "Status", render: (row) => row.statusLabel },
  {
    key: "links",
    header: "Linki",
    render: (row) => (
      <span className="billing-inline-links">
        <Link className="module-link" href={row.payerHref}>Szczegół płatnika</Link>
        <Link className="module-link" href={row.paymentsHref}>Wpłaty</Link>
      </span>
    ),
  },
];

const explanationColumns: Array<TableColumn<BillingExplanationDecisionRow>> = [
  {
    key: "payer",
    header: "Płatnik",
    render: (row) =>
      row.payerHref ? (
        <Link className="module-link" href={row.payerHref}>{row.payerLabel}</Link>
      ) : (
        row.payerLabel
      ),
  },
  { key: "problem", header: "Problem", render: (row) => <StatusBadge status={row.tone}>{row.problemLabel}</StatusBadge> },
  { key: "amount", header: "Kwota", align: "right", render: (row) => row.amountLabel },
  { key: "reason", header: "Powód", render: (row) => row.reasonLabel },
  {
    key: "link",
    header: "Dalej",
    render: (row) => <Link className="module-link" href={row.nextHref}>Sprawdź dalej</Link>,
  },
];

export function BillingDebtsOverpaymentsPage() {
  const { selectedOrganizationId, selectedOrganization, status: organizationStatus } = useActiveOrganization();
  const [snapshot, setSnapshot] = useState<BillingCenterSnapshot | null>(null);
  const [status, setStatus] = useState<BillingStatus>("idle");
  const [errorState, setErrorState] = useState<BillingErrorState | null>(null);

  const loadDebts = useCallback(async () => {
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
      const [balancesPayload, payersPayload, studentsPayload, chargesPayload, matchesPayload, transactionsPayload] = await Promise.all([
        api.ledgerBalances(query),
        api.billingPayers(query),
        api.billingStudents(query),
        api.billingCharges(withActiveOrganizationQuery(selectedOrganizationId, { limit: 1000 })),
        api.billingLedgerMatches(withActiveOrganizationQuery(selectedOrganizationId, { limit: 1000 })),
        api.billingTransactions(withActiveOrganizationQuery(selectedOrganizationId, { limit: 1000 })),
      ]);

      const payers = readBillingPayers(payersPayload);
      const balances = readBillingBalances(balancesPayload);
      const notesPayloads = await Promise.all(
        payers
          .filter((payer) => Math.abs(payer.billing_balance_due ?? balances.find((balance) => balance.billing_payer_id === payer.billing_payer_id)?.balance_due ?? 0) > 0)
          .slice(0, 30)
          .map((payer) => api.billingPayerNotes(payer.billing_payer_id, withActiveOrganizationQuery(selectedOrganizationId, { limit: 3 }))),
      );

      setSnapshot({
        balances,
        payers,
        students: readBillingStudents(studentsPayload),
        charges: readBillingCharges(chargesPayload),
        paymentMatches: readBillingPaymentMatches(matchesPayload),
        transactions: readBillingTransactions(transactionsPayload),
        payerNotes: notesPayloads.flatMap((payload) => readBillingPayerNotes(payload)),
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
    void loadDebts();
  }, [loadDebts]);

  const debtsView = useMemo(() => (snapshot ? buildBillingDebtsOverpaymentsView(snapshot) : null), [snapshot]);
  const organizationMissing = organizationStatus === "ready" && !canUseBillingOrganizationScope(selectedOrganizationId);
  const readyWithoutData =
    status === "ready" &&
    debtsView &&
    !organizationMissing &&
    !debtsView.debtRows.length &&
    !debtsView.overpaymentRows.length &&
    !debtsView.explanationRows.length;

  return (
    <div className="module-page billing-page billing-debts-page">
      <PageHeader
        badgeTone={status === "ready" ? "success" : status === "error" ? "warning" : "info"}
        description="Sprawdź, którzy płatnicy wymagają kontaktu, kto ma nadpłatę i które rozliczenia trzeba wyjaśnić."
        eyebrow="Rozliczenia"
        title="Zaległości i nadpłaty"
        actions={
          <div className="module-page-actions">
            <Link className="ui-button ui-button--secondary ui-button--sm" href={BILLING_CANONICAL_ROUTE}>
              <span className="ui-button__icon"><ArrowLeft size={15} /></span>
              <span>Wróć do rozliczeń</span>
            </Link>
            <Button disabled={status === "loading"} icon={<RefreshCw size={15} />} onClick={loadDebts} size="sm" variant="secondary">
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
          description="Nie ma zaległości, nadpłat ani oczywistych spraw do wyjaśnienia w aktualnych danych tej organizacji."
          title="Brak zaległości i nadpłat"
        />
      ) : null}

      {status === "ready" && debtsView && !organizationMissing && !readyWithoutData ? (
        <>
          <Card
            action={<StatusBadge status="info">{BILLING_READ_ONLY ? "Tylko odczyt" : "Akcje włączone"}</StatusBadge>}
            description={`Widok dla organizacji ${selectedOrganization?.name ?? selectedOrganizationId}. Ten widok nie zmienia sald, wpłat ani naliczeń. Pokazuje tylko aktualny stan rozliczeń.`}
            title="Centrum decyzji rozliczeniowych"
          >
            <div className="billing-center-hero" aria-label="Podsumowanie zaległości i nadpłat">
              <div>
                <span>Suma zaległości</span>
                <strong>{debtsView.summary.debtTotalLabel}</strong>
              </div>
              <div>
                <span>Suma nadpłat</span>
                <strong>{debtsView.summary.overpaymentTotalLabel}</strong>
              </div>
              <div>
                <span>Do wyjaśnienia</span>
                <strong>{debtsView.summary.explanationCount}</strong>
              </div>
            </div>
          </Card>

          <section className="module-kpi-row" aria-label="Karty podsumowania zaległości i nadpłat">
            <Card className="module-metric"><span>Suma zaległości</span><strong>{debtsView.summary.debtTotalLabel}</strong></Card>
            <Card className="module-metric"><span>Płatnicy z zaległością</span><strong>{debtsView.summary.debtPayerCount}</strong></Card>
            <Card className="module-metric"><span>Suma nadpłat</span><strong>{debtsView.summary.overpaymentTotalLabel}</strong></Card>
            <Card className="module-metric"><span>Płatnicy z nadpłatą</span><strong>{debtsView.summary.overpaymentPayerCount}</strong></Card>
            <Card className="module-metric"><span>Sprawy do wyjaśnienia</span><strong>{debtsView.summary.explanationCount}</strong></Card>
            <Card className="module-metric"><span>Rozliczeni na zero</span><strong>{debtsView.summary.settledPayerCount}</strong></Card>
          </section>

          <Card description={debtsView.summary.limitationLabel} title="Najpilniejsze sprawy">
            <Table columns={urgentColumns} data={debtsView.urgentRows} emptyMessage="Brak pilnych spraw rozliczeniowych w aktualnych danych." getRowKey={(row) => row.id} />
          </Card>

          <section className="module-grid module-grid--wide-main" aria-label="Zaległości i nadpłaty">
            <div className="module-stack">
              <Card description="Największe zaległości są na górze. Jeśli widoczne są wpłaty tylko przy płatniku, widok oznacza je jako sprawę do sprawdzenia." title="Zaległości">
                <Table columns={debtColumns} data={debtsView.debtRows} emptyMessage="Brak zaległości w aktualnych danych." getRowKey={(row) => row.id} />
              </Card>

              <Card description="Nadpłata nie została automatycznie rozliczona ani przeniesiona. Ten widok tylko ją pokazuje." title="Nadpłaty">
                <Table columns={overpaymentColumns} data={debtsView.overpaymentRows} emptyMessage="Brak nadpłat w aktualnych danych." getRowKey={(row) => row.id} />
              </Card>

              <Card description="Lista sygnałów, które wymagają sprawdzenia danych albo rozmowy z płatnikiem. Widok nie zgaduje brakujących faktów." title="Do wyjaśnienia">
                <Table columns={explanationColumns} data={debtsView.explanationRows} emptyMessage="Brak spraw wymagających wyjaśnienia." getRowKey={(row) => row.id} />
              </Card>
            </div>

            <aside className="module-stack">
              <Card title="Kontekst biznesowy">
                <div className="billing-context-list">
                  {debtsView.contextItems.map((item) => (
                    <article key={item.label}>
                      <span>{item.label}</span>
                      <strong>{item.value}</strong>
                    </article>
                  ))}
                </div>
              </Card>

              <Card className="module-quick-actions" title="Przejdź dalej">
                <Link className="module-quick-action" href={BILLING_WORK_QUEUE_ROUTE}>
                  <span>Sprawy rozliczeniowe</span>
                  <WalletCards aria-hidden="true" size={15} />
                </Link>
                <Link className="module-quick-action" href={BILLING_CANONICAL_ROUTE}>
                  <span>Rozliczenia</span>
                  <CreditCard aria-hidden="true" size={15} />
                </Link>
                <Link className="module-quick-action" href={BILLING_PAYMENTS_ROUTE}>
                  <span>Wpłaty</span>
                  <WalletCards aria-hidden="true" size={15} />
                </Link>
                <Link className="module-quick-action" href={BILLING_PERIODS_ROUTE}>
                  <span>Okresy</span>
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
