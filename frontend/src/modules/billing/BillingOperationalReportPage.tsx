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
  BILLING_WORK_QUEUE_ROUTE,
  buildBillingOperationalReport,
  canUseBillingOrganizationScope,
  getBillingErrorState,
  readBillingBalances,
  readBillingCharges,
  readBillingContactEvents,
  readBillingPayers,
  readBillingPaymentMatches,
  readBillingPaymentReviewStatuses,
  readBillingStudents,
  readBillingTransactions,
  readBillingWorkQueueEvents,
  type BillingCenterSnapshot,
  type BillingContactCenterRow,
  type BillingDebtDecisionRow,
  type BillingErrorState,
  type BillingOperationalReportImportantItem,
  type BillingOverpaymentDecisionRow,
  type BillingPaymentAssignmentRow,
  type BillingStatus,
  type BillingWorkQueueIssue,
} from "./billingModel";

const importantColumns: Array<TableColumn<BillingOperationalReportImportantItem>> = [
  { key: "type", header: "Typ", render: (row) => <StatusBadge status="warning">{row.typeLabel}</StatusBadge> },
  { key: "payer", header: "Płatnik", render: (row) => row.payerLabel },
  { key: "amount", header: "Kwota", align: "right", render: (row) => row.amountLabel ?? "Bez kwoty" },
  { key: "reason", header: "Powód", render: (row) => row.reasonLabel },
  { key: "next", header: "Następny krok", render: (row) => row.nextStepLabel },
  { key: "link", header: "Dalej", render: (row) => <Link className="module-link" href={row.href}>Otwórz</Link> },
];

const paymentColumns: Array<TableColumn<BillingPaymentAssignmentRow>> = [
  { key: "date", header: "Data", render: (row) => row.dateLabel },
  { key: "amount", header: "Kwota", align: "right", render: (row) => row.amountLabel },
  {
    key: "payer",
    header: "Płatnik",
    render: (row) => (row.payerHref ? <Link className="module-link" href={row.payerHref}>{row.payerLabel}</Link> : row.payerLabel),
  },
  { key: "assignment", header: "Przypisanie", render: (row) => row.assignmentLabel },
  { key: "status", header: "Status", render: (row) => <StatusBadge status={row.statusTone}>{row.statusLabel}</StatusBadge> },
  {
    key: "details",
    header: "Dalej",
    render: (row) => (row.paymentHref ? <Link className="module-link" href={row.paymentHref}>Szczegół wpłaty</Link> : "-"),
  },
];

const debtColumns: Array<TableColumn<BillingDebtDecisionRow>> = [
  { key: "payer", header: "Płatnik", render: (row) => <Link className="module-link" href={row.payerHref}>{row.payerLabel}</Link> },
  { key: "amount", header: "Zaległość", align: "right", render: (row) => row.amountLabel },
  { key: "reason", header: "Dlaczego sprawdzić", render: (row) => row.reasonLabel },
  { key: "next", header: "Następny krok", render: (row) => row.nextStepLabel },
];

const overpaymentColumns: Array<TableColumn<BillingOverpaymentDecisionRow>> = [
  { key: "payer", header: "Płatnik", render: (row) => <Link className="module-link" href={row.payerHref}>{row.payerLabel}</Link> },
  { key: "amount", header: "Nadpłata", align: "right", render: (row) => row.amountLabel },
  { key: "source", header: "Kontekst", render: (row) => row.possibleSourceLabel },
  { key: "status", header: "Status", render: (row) => row.statusLabel },
];

const workQueueColumns: Array<TableColumn<BillingWorkQueueIssue>> = [
  { key: "priority", header: "Priorytet", render: (row) => <StatusBadge status={row.tone}>{row.priority}</StatusBadge> },
  { key: "type", header: "Typ", render: (row) => row.type },
  { key: "payer", header: "Płatnik", render: (row) => (row.payerHref ? <Link className="module-link" href={row.payerHref}>{row.payerLabel}</Link> : row.payerLabel) },
  { key: "amount", header: "Kwota", align: "right", render: (row) => row.amountLabel },
  { key: "next", header: "Następny krok", render: (row) => row.nextStep },
  { key: "link", header: "Dalej", render: (row) => <Link className="module-link" href={row.href}>Otwórz</Link> },
];

const contactColumns: Array<TableColumn<BillingContactCenterRow>> = [
  { key: "date", header: "Data", render: (row) => row.dateLabel },
  { key: "payer", header: "Płatnik", render: (row) => <Link className="module-link" href={row.payerHref}>{row.payerLabel}</Link> },
  { key: "channel", header: "Kanał", render: (row) => row.channelLabel },
  { key: "action", header: "Typ wpisu", render: (row) => row.actionLabel },
  { key: "reason", header: "Dlaczego ważne", render: (row) => row.attentionReason },
  { key: "link", header: "Dalej", render: () => <Link className="module-link" href={BILLING_CONTACT_CENTER_ROUTE}>Kontakty</Link> },
];

export function BillingOperationalReportPage() {
  const { selectedOrganizationId, selectedOrganization, status: organizationStatus } = useActiveOrganization();
  const [snapshot, setSnapshot] = useState<BillingCenterSnapshot | null>(null);
  const [loadedOrganizationId, setLoadedOrganizationId] = useState<string | null>(null);
  const [status, setStatus] = useState<BillingStatus>("idle");
  const [errorState, setErrorState] = useState<BillingErrorState | null>(null);

  const activeOrganizationKey = canUseBillingOrganizationScope(selectedOrganizationId) ? String(selectedOrganizationId).trim() : null;

  const loadReport = useCallback(async () => {
    if (organizationStatus === "loading") {
      setSnapshot(null);
      setLoadedOrganizationId(null);
      setErrorState(null);
      setStatus("loading");
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
      const [
        balancesPayload,
        payersPayload,
        studentsPayload,
        chargesPayload,
        matchesPayload,
        transactionsPayload,
        statusesPayload,
        workQueueEventsPayload,
        contactEventsPayload,
      ] = await Promise.all([
        api.ledgerBalances(query),
        api.billingPayers(query),
        api.billingStudents(query),
        api.billingCharges(withActiveOrganizationQuery(organizationId, { limit: 1000 })),
        api.billingLedgerMatches(withActiveOrganizationQuery(organizationId, { limit: 1000 })),
        api.billingTransactions(withActiveOrganizationQuery(organizationId, { limit: 1000 })),
        api.billingPaymentReviewStatuses(withActiveOrganizationQuery(organizationId, { limit: 1000 })),
        api.billingWorkQueueEvents(withActiveOrganizationQuery(organizationId, { limit: 1000 })),
        api.billingContactEvents(withActiveOrganizationQuery(organizationId, { limit: 1000 })),
      ]);

      setSnapshot({
        balances: readBillingBalances(balancesPayload),
        payers: readBillingPayers(payersPayload),
        students: readBillingStudents(studentsPayload),
        charges: readBillingCharges(chargesPayload),
        paymentMatches: readBillingPaymentMatches(matchesPayload),
        transactions: readBillingTransactions(transactionsPayload),
        paymentReviewStatuses: readBillingPaymentReviewStatuses(statusesPayload).statuses,
        workQueueEvents: readBillingWorkQueueEvents(workQueueEventsPayload).events,
        contactEvents: readBillingContactEvents(contactEventsPayload).events,
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
    void loadReport();
  }, [loadReport]);

  const snapshotMatchesOrganization = Boolean(snapshot && activeOrganizationKey && loadedOrganizationId === activeOrganizationKey);
  const report = useMemo(
    () =>
      snapshotMatchesOrganization && snapshot
        ? buildBillingOperationalReport(snapshot, selectedOrganization?.name ?? "Wybrana organizacja")
        : null,
    [selectedOrganization?.name, snapshot, snapshotMatchesOrganization],
  );
  const organizationMissing = organizationStatus === "ready" && !canUseBillingOrganizationScope(selectedOrganizationId);

  return (
    <div className="module-page billing-page billing-operational-report-page">
      <PageHeader
        badgeTone={status === "ready" ? "success" : status === "error" ? "warning" : "info"}
        description="Zbiorcze podsumowanie zaległości, nadpłat, wpłat, spraw i kontaktów rozliczeniowych."
        eyebrow="Rozliczenia"
        title="Raport rozliczeniowy"
        actions={
          <div className="module-page-actions">
            <Link className="ui-button ui-button--secondary ui-button--sm" href={BILLING_CANONICAL_ROUTE}>
              <span className="ui-button__icon"><ArrowLeft size={15} /></span>
              <span>Wróć do rozliczeń</span>
            </Link>
            <Button disabled={status === "loading"} icon={<RefreshCw size={15} />} onClick={loadReport} size="sm" variant="secondary">
              Odśwież
            </Button>
          </div>
        }
      />

      <Card title="Tryb raportu operacyjnego">
        <p className="module-note">Ten raport nie zmienia danych i nie jest oficjalnym dokumentem księgowym.</p>
        <p className="module-note">CASI Workspace nie wysyła tego raportu. Możesz go tylko przeczytać lub ręcznie skopiować.</p>
      </Card>

      {status === "loading" ? <LoadingState /> : null}
      {errorState ? <ErrorState description={errorState.description} title={errorState.title} /> : null}
      {organizationMissing ? <EmptyState description={BILLING_ORGANIZATION_REQUIRED_DESCRIPTION} title={BILLING_ORGANIZATION_REQUIRED_TITLE} /> : null}

      {status === "ready" && report && !organizationMissing ? (
        <>
          <Card title="Zakres raportu" description="Raport obejmuje aktualnie widoczne dane organizacji. Filtrowanie po okresie będzie osobnym etapem, jeśli dane okresów będą wystarczająco kompletne.">
            <div className="module-context-list">
              <article>
                <span>Organizacja</span>
                <p>{selectedOrganization?.name ?? selectedOrganizationId}</p>
              </article>
              <article>
                <span>Stan danych</span>
                <p>Aktualny stan danych</p>
              </article>
            </div>
          </Card>

          <section className="module-kpi-row" aria-label="Podsumowanie raportu rozliczeniowego">
            {report.summaryCards.map((card) => (
              <Card className="module-metric" key={card.id}>
                <span>{card.label}</span>
                <strong>{card.value}</strong>
                <small>{card.description}</small>
              </Card>
            ))}
          </section>

          <Card title="Najważniejsze do sprawdzenia" description="Lista priorytetów do ręcznego przejrzenia. Ten widok nie tworzy zadań ani nie wykonuje operacji finansowych.">
            <Table columns={importantColumns} data={report.importantRows} emptyMessage="Brak oczywistych spraw do sprawdzenia w aktualnych danych." getRowKey={(row) => row.id} />
          </Card>

          <section className="module-grid module-grid--wide-main">
            <div className="module-stack">
              <Card title="Płatności i wpłaty" description="Rozróżnienie wpłat przypisanych do naliczeń, tylko do płatnika albo wymagających późniejszego wyjaśnienia.">
                <Table columns={paymentColumns} data={report.paymentRows} emptyMessage="Brak wpłat do pokazania w raporcie." getRowKey={(row) => row.id} />
                <p className="module-note">
                  <Link className="module-link" href={BILLING_PAYMENTS_ROUTE}>Przejdź do wpłat i przypisań</Link>
                </p>
              </Card>

              <Card title="Zaległości i nadpłaty" description="Najważniejsze salda płatników bez decyzji automatycznych.">
                <Table columns={debtColumns} data={report.debtRows} emptyMessage="Brak zaległości w aktualnych danych." getRowKey={(row) => row.id} />
                <Table columns={overpaymentColumns} data={report.overpaymentRows} emptyMessage="Brak nadpłat w aktualnych danych." getRowKey={(row) => row.id} />
                <p className="module-note">
                  <Link className="module-link" href={BILLING_DEBTS_ROUTE}>Przejdź do zaległości i nadpłat</Link>
                </p>
              </Card>

              <Card title="Sprawy rozliczeniowe" description="Aktywne, odłożone i obsłużone sprawy widoczne w aktualnym stanie pracy.">
                <Table columns={workQueueColumns} data={report.workQueueRows} emptyMessage="Brak aktywnych spraw rozliczeniowych w raporcie." getRowKey={(row) => row.id} />
                <p className="module-note">
                  <Link className="module-link" href={BILLING_WORK_QUEUE_ROUTE}>Przejdź do spraw rozliczeniowych</Link>
                </p>
              </Card>

              <Card title="Kontakty rozliczeniowe" description="Ostatnie wpisy i kontakty wymagające ponownego działania.">
                <Table columns={contactColumns} data={report.contactRows} emptyMessage="Brak kontaktów wymagających działania w aktualnych danych." getRowKey={(row) => row.id} />
                <p className="module-note">
                  <Link className="module-link" href={BILLING_CONTACT_CENTER_ROUTE}>Przejdź do kontaktów rozliczeniowych</Link>
                </p>
              </Card>
            </div>

            <aside className="module-stack">
              <Card title="Raport do skopiowania" description="Tekst możesz ręcznie zaznaczyć i skopiować do własnych notatek. CASI Workspace go nie wysyła.">
                <pre className="billing-report-copy" aria-label="Raport tekstowy do skopiowania">{report.reportText}</pre>
              </Card>

              <Card title="Ograniczenia danych">
                <ul className="module-list">
                  {report.limitations.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </Card>

              <Card className="module-quick-actions" title="Przejdź dalej">
                <Link className="module-quick-action" href={BILLING_PAYMENTS_ROUTE}>Wpłaty i przypisania</Link>
                <Link className="module-quick-action" href={BILLING_DEBTS_ROUTE}>Zaległości i nadpłaty</Link>
                <Link className="module-quick-action" href={BILLING_WORK_QUEUE_ROUTE}>Sprawy rozliczeniowe</Link>
                <Link className="module-quick-action" href={BILLING_CONTACT_CENTER_ROUTE}>Kontakty rozliczeniowe</Link>
                <Link className="module-quick-action" href={BILLING_PERIODS_ROUTE}>Okresy rozliczeniowe</Link>
              </Card>

              <Card title="Kontekst biznesowy">
                <div className="module-context-list">
                  {report.contextItems.map((item) => (
                    <article key={item.label}>
                      <span>{item.label}</span>
                      <p>{item.value}</p>
                    </article>
                  ))}
                </div>
              </Card>
            </aside>
          </section>
        </>
      ) : null}
    </div>
  );
}
