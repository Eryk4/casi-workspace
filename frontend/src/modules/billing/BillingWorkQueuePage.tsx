"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { ArrowLeft, RefreshCw } from "lucide-react";

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
  BILLING_DEBTS_ROUTE,
  BILLING_ORGANIZATION_REQUIRED_DESCRIPTION,
  BILLING_ORGANIZATION_REQUIRED_TITLE,
  BILLING_PAYMENTS_ROUTE,
  BILLING_PERIODS_ROUTE,
  buildBillingWorkQueueView,
  canUseBillingOrganizationScope,
  getBillingErrorState,
  readBillingBalances,
  readBillingCharges,
  readBillingPayerNotes,
  readBillingPaymentMatches,
  readBillingPaymentReviewStatuses,
  readBillingPayers,
  readBillingStudents,
  readBillingTransactions,
  type BillingCenterSnapshot,
  type BillingErrorState,
  type BillingStatus,
  type BillingWorkQueueIssue,
} from "./billingModel";

const issueColumns: Array<TableColumn<BillingWorkQueueIssue>> = [
  { key: "priority", header: "Priorytet", render: (row) => <StatusBadge status={row.tone}>{`${row.priority} priorytet`}</StatusBadge> },
  { key: "type", header: "Typ sprawy", render: (row) => row.type },
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
  { key: "amount", header: "Kwota", align: "right", render: (row) => row.amountLabel },
  { key: "reason", header: "Powód", render: (row) => row.reason },
  { key: "next", header: "Następny krok", render: (row) => row.nextStep },
  {
    key: "link",
    header: "Dalej",
    render: (row) => (
      <span className="billing-inline-links">
        <Link className="module-link" href={row.href}>Otwórz</Link>
        {row.paymentHref ? <Link className="module-link" href={row.paymentHref}>Szczegół wpłaty</Link> : null}
        {row.payerHref ? <Link className="module-link" href={row.payerHref}>Szczegół płatnika</Link> : null}
      </span>
    ),
  },
];

function WorkQueueSection({
  title,
  description,
  rows,
  emptyTitle,
  emptyDescription,
}: {
  title: string;
  description: string;
  rows: BillingWorkQueueIssue[];
  emptyTitle: string;
  emptyDescription: string;
}) {
  return (
    <Card description={description} title={title}>
      {rows.length ? (
        <Table<BillingWorkQueueIssue> columns={issueColumns} data={rows} getRowKey={(row) => row.id} />
      ) : (
        <EmptyState title={emptyTitle} description={emptyDescription} />
      )}
    </Card>
  );
}

export function BillingWorkQueuePage() {
  const { selectedOrganizationId, selectedOrganization, status: organizationStatus } = useActiveOrganization();
  const [snapshot, setSnapshot] = useState<BillingCenterSnapshot | null>(null);
  const [loadedOrganizationId, setLoadedOrganizationId] = useState<string | null>(null);
  const [status, setStatus] = useState<BillingStatus>("idle");
  const [errorState, setErrorState] = useState<BillingErrorState | null>(null);

  const loadWorkQueue = useCallback(async () => {
    if (organizationStatus === "loading") {
      setStatus("loading");
      setErrorState(null);
      return;
    }

    if (!canUseBillingOrganizationScope(selectedOrganizationId)) {
      setSnapshot(null);
      setLoadedOrganizationId(null);
      setErrorState(null);
      setStatus("ready");
      return;
    }

    const organizationId = String(selectedOrganizationId).trim();
    setSnapshot(null);
    setLoadedOrganizationId(null);
    setStatus("loading");
    setErrorState(null);

    try {
      const query = withActiveOrganizationQuery(organizationId);
      const [balancesPayload, payersPayload, studentsPayload, chargesPayload, matchesPayload, transactionsPayload, statusesPayload] = await Promise.all([
        api.ledgerBalances(query),
        api.billingPayers(query),
        api.billingStudents(query),
        api.billingCharges(withActiveOrganizationQuery(organizationId, { limit: 1000 })),
        api.billingLedgerMatches(withActiveOrganizationQuery(organizationId, { limit: 1000 })),
        api.billingTransactions(withActiveOrganizationQuery(organizationId, { limit: 1000 })),
        api.billingPaymentReviewStatuses(withActiveOrganizationQuery(organizationId, { limit: 1000 })),
      ]);

      const payers = readBillingPayers(payersPayload);
      const balances = readBillingBalances(balancesPayload);
      const notesPayloads = await Promise.all(
        payers
          .filter((payer) => Math.abs(payer.billing_balance_due ?? balances.find((balance) => balance.billing_payer_id === payer.billing_payer_id)?.balance_due ?? 0) > 0)
          .slice(0, 30)
          .map((payer) => api.billingPayerNotes(payer.billing_payer_id, withActiveOrganizationQuery(organizationId, { limit: 3 }))),
      );

      setSnapshot({
        balances,
        payers,
        students: readBillingStudents(studentsPayload),
        charges: readBillingCharges(chargesPayload),
        paymentMatches: readBillingPaymentMatches(matchesPayload),
        transactions: readBillingTransactions(transactionsPayload),
        paymentReviewStatuses: readBillingPaymentReviewStatuses(statusesPayload).statuses,
        payerNotes: notesPayloads.flatMap((payload) => readBillingPayerNotes(payload)),
        invoices: [],
        contractors: [],
        workItems: [],
      });
      setLoadedOrganizationId(organizationId);
      setStatus("ready");
    } catch (error) {
      const nextErrorState = getBillingErrorState(error);
      setSnapshot(null);
      setLoadedOrganizationId(null);
      setErrorState(nextErrorState);
      setStatus(nextErrorState.status);
    }
  }, [organizationStatus, selectedOrganizationId]);

  useEffect(() => {
    setSnapshot(null);
    setLoadedOrganizationId(null);
    void loadWorkQueue();
  }, [loadWorkQueue]);

  const activeOrganizationKey = canUseBillingOrganizationScope(selectedOrganizationId) ? String(selectedOrganizationId).trim() : null;
  const snapshotMatchesOrganization = Boolean(snapshot && activeOrganizationKey && loadedOrganizationId === activeOrganizationKey);
  const workQueueView = useMemo(() => (snapshotMatchesOrganization && snapshot ? buildBillingWorkQueueView(snapshot) : null), [snapshot, snapshotMatchesOrganization]);
  const organizationMissing = organizationStatus === "ready" && !canUseBillingOrganizationScope(selectedOrganizationId);
  const readyWithoutData =
    status === "ready" &&
    workQueueView &&
    !organizationMissing &&
    !workQueueView.firstRows.length &&
    !workQueueView.paymentRows.length &&
    !workQueueView.contactRows.length &&
    !workQueueView.overpaymentRows.length &&
    !workQueueView.checkedRows.length;

  return (
    <div className="module-page billing-page billing-work-queue-page">
      <PageHeader
        badgeTone={status === "ready" ? "success" : status === "error" ? "warning" : "info"}
        description="Lista spraw, które warto dziś sprawdzić w rozliczeniach. Ten widok nie zmienia sald, wpłat ani naliczeń. Pomaga tylko ustalić, gdzie kliknąć dalej."
        eyebrow="Rozliczenia"
        title="Sprawy rozliczeniowe"
        actions={
          <div className="module-page-actions">
            <Link className="ui-button ui-button--secondary ui-button--sm" href={BILLING_CANONICAL_ROUTE}>
              <span className="ui-button__icon"><ArrowLeft size={15} /></span>
              <span>Wróć do rozliczeń</span>
            </Link>
            <Button disabled={status === "loading"} icon={<RefreshCw size={15} />} onClick={loadWorkQueue} size="sm" variant="secondary">
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
          description="Nie ma dziś oczywistych spraw rozliczeniowych do obsłużenia w wybranej organizacji."
          title="Brak spraw do obsłużenia"
        />
      ) : null}

      {status === "ready" && workQueueView && !organizationMissing && !readyWithoutData ? (
        <>
          <div className="module-grid module-grid--three">
            <Card title="Wysoki priorytet" description="Sprawy, od których warto zacząć.">
              <strong>{workQueueView.summary.highPriorityCount}</strong>
            </Card>
            <Card title="Do wyjaśnienia" description="Wpłaty i salda z niepełnym kontekstem.">
              <strong>{workQueueView.summary.needsReviewCount}</strong>
            </Card>
            <Card title="Czeka na kontakt" description="Płatnicy albo wpłaty sugerujące kontakt.">
              <strong>{workQueueView.summary.contactCount}</strong>
            </Card>
            <Card title="Nadpłaty do decyzji" description="Nadpłaty, których ten widok nie rozlicza.">
              <strong>{workQueueView.summary.overpaymentCount}</strong>
            </Card>
            <Card title="Zaległości do sprawdzenia" description="Płatnicy z widoczną dopłatą.">
              <strong>{workQueueView.summary.debtCount}</strong>
            </Card>
            <Card title="Ostatnio sprawdzone" description="Wpłaty oznaczone jako sprawdzone.">
              <strong>{workQueueView.summary.checkedCount}</strong>
            </Card>
          </div>

          <WorkQueueSection
            title="Najpierw zrób"
            description="Najpilniejsze sprawy rozliczeniowe, maksymalnie kilka pozycji do przejrzenia na początku dnia."
            rows={workQueueView.firstRows}
            emptyTitle="Brak pilnych spraw"
            emptyDescription="Nie ma obecnie spraw z wysokim albo średnim priorytetem."
          />

          <WorkQueueSection
            title="Wpłaty do wyjaśnienia"
            description="Wpłaty ze statusem operacyjnym albo bez konkretnego przypisania do naliczenia."
            rows={workQueueView.paymentRows}
            emptyTitle="Brak wpłat do wyjaśnienia"
            emptyDescription="Nie ma wpłat oznaczonych jako problematyczne w obecnych danych."
          />

          <WorkQueueSection
            title="Płatnicy do kontaktu"
            description="Zaległości i statusy sugerujące rozmowę z płatnikiem albo sprawdzenie ostatniej wpłaty."
            rows={workQueueView.contactRows}
            emptyTitle="Brak płatników do kontaktu"
            emptyDescription="Nie ma obecnie płatników z sygnałem kontaktu w tym widoku."
          />

          <WorkQueueSection
            title="Nadpłaty do decyzji"
            description="Ten widok nie rozlicza nadpłaty. Pokazuje tylko, gdzie warto podjąć decyzję."
            rows={workQueueView.overpaymentRows}
            emptyTitle="Brak nadpłat do decyzji"
            emptyDescription="Nie ma widocznych nadpłat wymagających decyzji w tej organizacji."
          />

          <WorkQueueSection
            title="Ostatnio sprawdzone"
            description="Wpłaty oznaczone operacyjnie jako sprawdzone. Nie trafiają do najpilniejszych spraw."
            rows={workQueueView.checkedRows}
            emptyTitle="Brak ostatnio sprawdzonych wpłat"
            emptyDescription="Nie ma jeszcze wpłat oznaczonych jako sprawdzone."
          />

          <div className="module-grid module-grid--two">
            <Card className="module-quick-actions" title="Przejdź dalej">
              <Link className="module-quick-action" href={BILLING_PAYMENTS_ROUTE}>Wpłaty i przypisania</Link>
              <Link className="module-quick-action" href={BILLING_DEBTS_ROUTE}>Zaległości i nadpłaty</Link>
              <Link className="module-quick-action" href={BILLING_PERIODS_ROUTE}>Okresy rozliczeniowe</Link>
              <Link className="module-quick-action" href={BILLING_CANONICAL_ROUTE}>Centrum rozliczeń</Link>
            </Card>
            <Card title="Kontekst biznesowy">
              <div className="module-context-list">
                {workQueueView.contextItems.map((item) => (
                  <article key={item.label}>
                    <span>{item.label}</span>
                    <p>{item.value}</p>
                  </article>
                ))}
                <article>
                  <span>Organizacja</span>
                  <p>{selectedOrganization?.name ?? "Wybrana organizacja"}</p>
                </article>
              </div>
            </Card>
          </div>
        </>
      ) : null}
    </div>
  );
}
