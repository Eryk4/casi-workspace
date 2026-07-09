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
  BILLING_CONTACT_CENTER_ROUTE,
  BILLING_DEBTS_ROUTE,
  BILLING_ORGANIZATION_REQUIRED_DESCRIPTION,
  BILLING_ORGANIZATION_REQUIRED_TITLE,
  BILLING_PAYMENTS_ROUTE,
  BILLING_PERIODS_ROUTE,
  BILLING_WORK_QUEUE_DECISION_HELP_TEXT,
  buildBillingWorkQueueView,
  buildBillingWorkQueueDecisionRequest,
  canUseBillingOrganizationScope,
  getBillingErrorState,
  readBillingBalances,
  readBillingCharges,
  readBillingPayerNotes,
  readBillingPaymentMatches,
  readBillingPaymentReviewStatuses,
  readBillingWorkQueueEvents,
  readBillingPayers,
  readBillingStudents,
  readBillingTransactions,
  type BillingCenterSnapshot,
  type BillingErrorState,
  type BillingStatus,
  type BillingWorkQueueEventAction,
  type BillingWorkQueueIssue,
} from "./billingModel";

function buildIssueColumns(
  onDecision?: (issue: BillingWorkQueueIssue, action: BillingWorkQueueEventAction) => void,
): Array<TableColumn<BillingWorkQueueIssue>> {
  return [
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
        {row.payerHref ? <Link className="module-link" href={row.payerHref}>Przygotuj kontakt</Link> : null}
      </span>
    ),
  },
  ...(onDecision
    ? [
        {
          key: "decision",
          header: "Decyzja",
          render: (row: BillingWorkQueueIssue) => (
            <span className="billing-inline-links">
              <Button onClick={() => onDecision(row, "handled")} size="sm" variant="secondary">
                Oznacz jako obsłużoną
              </Button>
              <Button onClick={() => onDecision(row, "snoozed")} size="sm" variant="secondary">
                Odłóż
              </Button>
            </span>
          ),
        } satisfies TableColumn<BillingWorkQueueIssue>,
      ]
    : []),
  ];
}

function WorkQueueSection({
  title,
  description,
  rows,
  emptyTitle,
  emptyDescription,
  onDecision,
}: {
  title: string;
  description: string;
  rows: BillingWorkQueueIssue[];
  emptyTitle: string;
  emptyDescription: string;
  onDecision?: (issue: BillingWorkQueueIssue, action: BillingWorkQueueEventAction) => void;
}) {
  const columns = useMemo(() => buildIssueColumns(onDecision), [onDecision]);
  return (
    <Card description={description} title={title}>
      {rows.length ? (
        <Table<BillingWorkQueueIssue> columns={columns} data={rows} getRowKey={(row) => row.id} />
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
  const [decisionIssue, setDecisionIssue] = useState<BillingWorkQueueIssue | null>(null);
  const [decisionAction, setDecisionAction] = useState<BillingWorkQueueEventAction | null>(null);
  const [decisionNote, setDecisionNote] = useState("");
  const [decisionError, setDecisionError] = useState<string | null>(null);
  const [decisionSuccess, setDecisionSuccess] = useState<string | null>(null);
  const [isDecisionSubmitting, setDecisionSubmitting] = useState(false);

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
      const [balancesPayload, payersPayload, studentsPayload, chargesPayload, matchesPayload, transactionsPayload, statusesPayload, workQueueEventsPayload] = await Promise.all([
        api.ledgerBalances(query),
        api.billingPayers(query),
        api.billingStudents(query),
        api.billingCharges(withActiveOrganizationQuery(organizationId, { limit: 1000 })),
        api.billingLedgerMatches(withActiveOrganizationQuery(organizationId, { limit: 1000 })),
        api.billingTransactions(withActiveOrganizationQuery(organizationId, { limit: 1000 })),
        api.billingPaymentReviewStatuses(withActiveOrganizationQuery(organizationId, { limit: 1000 })),
        api.billingWorkQueueEvents(withActiveOrganizationQuery(organizationId, { limit: 1000 })),
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
        workQueueEvents: readBillingWorkQueueEvents(workQueueEventsPayload).events,
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

  const activeOrganizationKey = canUseBillingOrganizationScope(selectedOrganizationId) ? String(selectedOrganizationId).trim() : null;

  const startDecision = useCallback((issue: BillingWorkQueueIssue, action: BillingWorkQueueEventAction) => {
    setDecisionIssue(issue);
    setDecisionAction(action);
    setDecisionNote("");
    setDecisionError(null);
    setDecisionSuccess(null);
  }, []);

  const submitDecision = useCallback(async () => {
    if (!decisionIssue || !decisionAction || !activeOrganizationKey) {
      return;
    }
    const validation = buildBillingWorkQueueDecisionRequest(
      decisionIssue,
      decisionAction,
      decisionNote,
      activeOrganizationKey,
    );
    if (!validation.ok) {
      setDecisionError(validation.message);
      return;
    }
    setDecisionSubmitting(true);
    setDecisionError(null);
    setDecisionSuccess(null);
    try {
      await api.addBillingWorkQueueEvent(validation.payload, activeOrganizationKey);
      setDecisionNote("");
      setDecisionIssue(null);
      setDecisionAction(null);
      setDecisionSuccess(decisionAction === "handled" ? "Sprawa została oznaczona jako obsłużona." : "Sprawa została odłożona.");
      await loadWorkQueue();
    } catch (error) {
      const nextError = getBillingErrorState(error);
      setDecisionError(nextError.description || nextError.title);
    } finally {
      setDecisionSubmitting(false);
    }
  }, [activeOrganizationKey, decisionAction, decisionIssue, decisionNote, loadWorkQueue]);

  useEffect(() => {
    setSnapshot(null);
    setLoadedOrganizationId(null);
    void loadWorkQueue();
  }, [loadWorkQueue]);

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
    !workQueueView.checkedRows.length &&
    !workQueueView.snoozedRows.length &&
    !workQueueView.handledRows.length;

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
        <>
          <EmptyState
            description="Nie ma dziś oczywistych spraw rozliczeniowych do obsłużenia w wybranej organizacji."
            title="Brak spraw do obsłużenia"
          />
          <Card className="module-quick-actions" title="Przejdź dalej">
            <Link className="module-quick-action" href={BILLING_CONTACT_CENTER_ROUTE}>Kontakty rozliczeniowe</Link>
            <Link className="module-quick-action" href={BILLING_CANONICAL_ROUTE}>Centrum rozliczeń</Link>
          </Card>
        </>
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
            <Card title="Odłożone sprawy" description="Sprawy odłożone decyzją operatora.">
              <strong>{workQueueView.summary.snoozedCount}</strong>
            </Card>
            <Card title="Ostatnio obsłużone" description="Sprawy oznaczone jako obsłużone.">
              <strong>{workQueueView.summary.handledCount}</strong>
            </Card>
          </div>

          <Card
            description="Decyzja porządkuje listę pracy. Nie oznacza rozliczenia płatności ani zamknięcia salda."
            title="Decyzja operacyjna sprawy"
          >
            <p className="module-note">{BILLING_WORK_QUEUE_DECISION_HELP_TEXT}</p>
            {decisionIssue && decisionAction ? (
              <div className="module-form">
                <div className="module-context-list">
                  <article>
                    <span>Sprawa</span>
                    <p>{decisionIssue.type} · {decisionIssue.payerLabel} · {decisionIssue.amountLabel}</p>
                  </article>
                  <article>
                    <span>Decyzja</span>
                    <p>{decisionAction === "handled" ? "Obsłużona" : "Odłożona"}</p>
                  </article>
                </div>
                <label className="module-field">
                  <span>Notatka opcjonalna</span>
                  <textarea
                    maxLength={1000}
                    onChange={(event) => setDecisionNote(event.target.value)}
                    placeholder="Krótko opisz, co ustalono. Notatka nie zmienia finansów."
                    value={decisionNote}
                  />
                </label>
                {decisionError ? <p className="module-error">{decisionError}</p> : null}
                <div className="module-page-actions">
                  <Button disabled={isDecisionSubmitting} onClick={submitDecision} size="sm">
                    {isDecisionSubmitting ? "Zapisywanie..." : "Zapisz decyzję"}
                  </Button>
                  <Button
                    disabled={isDecisionSubmitting}
                    onClick={() => {
                      setDecisionIssue(null);
                      setDecisionAction(null);
                      setDecisionNote("");
                      setDecisionError(null);
                    }}
                    size="sm"
                    variant="secondary"
                  >
                    Anuluj
                  </Button>
                </div>
              </div>
            ) : (
              <EmptyState
                title="Wybierz sprawę z listy"
                description="Użyj przycisku Oznacz jako obsłużoną albo Odłóż przy sprawie, którą chcesz uporządkować."
              />
            )}
            {decisionSuccess ? <p className="module-success">{decisionSuccess}</p> : null}
          </Card>

          <WorkQueueSection
            title="Najpierw zrób"
            description="Najpilniejsze sprawy rozliczeniowe, maksymalnie kilka pozycji do przejrzenia na początku dnia."
            rows={workQueueView.firstRows}
            emptyTitle="Brak pilnych spraw"
            emptyDescription="Nie ma obecnie spraw z wysokim albo średnim priorytetem."
            onDecision={startDecision}
          />

          <WorkQueueSection
            title="Wpłaty do wyjaśnienia"
            description="Wpłaty ze statusem operacyjnym albo bez konkretnego przypisania do naliczenia."
            rows={workQueueView.paymentRows}
            emptyTitle="Brak wpłat do wyjaśnienia"
            emptyDescription="Nie ma wpłat oznaczonych jako problematyczne w obecnych danych."
            onDecision={startDecision}
          />

          <WorkQueueSection
            title="Płatnicy do kontaktu"
            description="Zaległości i statusy sugerujące rozmowę z płatnikiem albo sprawdzenie ostatniej wpłaty."
            rows={workQueueView.contactRows}
            emptyTitle="Brak płatników do kontaktu"
            emptyDescription="Nie ma obecnie płatników z sygnałem kontaktu w tym widoku."
            onDecision={startDecision}
          />

          <WorkQueueSection
            title="Nadpłaty do decyzji"
            description="Ten widok nie rozlicza nadpłaty. Pokazuje tylko, gdzie warto podjąć decyzję."
            rows={workQueueView.overpaymentRows}
            emptyTitle="Brak nadpłat do decyzji"
            emptyDescription="Nie ma widocznych nadpłat wymagających decyzji w tej organizacji."
            onDecision={startDecision}
          />

          <WorkQueueSection
            title="Odłożone sprawy"
            description="Sprawy odłożone decyzją operatora. Nie trafiają do sekcji Najpierw zrób."
            rows={workQueueView.snoozedRows}
            emptyTitle="Brak odłożonych spraw"
            emptyDescription="Nie ma jeszcze spraw odłożonych w tej organizacji."
          />

          <WorkQueueSection
            title="Ostatnio obsłużone"
            description="Sprawy oznaczone jako obsłużone. To nie znaczy, że saldo zostało rozliczone."
            rows={workQueueView.handledRows}
            emptyTitle="Brak obsłużonych spraw"
            emptyDescription="Nie ma jeszcze spraw oznaczonych jako obsłużone."
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
              <Link className="module-quick-action" href={BILLING_CONTACT_CENTER_ROUTE}>Kontakty rozliczeniowe</Link>
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
