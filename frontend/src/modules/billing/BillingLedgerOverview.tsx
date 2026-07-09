"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { ArrowRight, Building2, CalendarDays, CreditCard, FileText, ListChecks, MessageSquareText, RefreshCw, UsersRound, WalletCards } from "lucide-react";

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
import { readContractors } from "../crm/crmModel";
import { readWorkItems } from "../work-items/workItemsModel";
import {
  BILLING_CANONICAL_ROUTE,
  BILLING_CONTACT_CENTER_ROUTE,
  BILLING_DEBTS_ROUTE,
  BILLING_WORK_QUEUE_ROUTE,
  BILLING_ORGANIZATION_REQUIRED_DESCRIPTION,
  BILLING_ORGANIZATION_REQUIRED_TITLE,
  BILLING_READ_ONLY,
  buildBillingAttentionItems,
  buildBillingBalanceRows,
  buildBillingBalanceExplanationRows,
  buildBillingCompanyClientRows,
  buildBillingContractorRows,
  buildBillingFamilyFoundationRows,
  buildBillingInvoiceRows,
  buildBillingMoneySummary,
  buildBillingRecentPaymentRows,
  buildBillingRelatedWorkItemRows,
  buildBillingServiceEnrollmentRows,
  canUseBillingOrganizationScope,
  formatMoney,
  getBillingErrorState,
  hasBillingCenterData,
  isBillingCenterEmpty,
  readBillingBalances,
  readBillingCharges,
  readBillingInvoices,
  readBillingPayers,
  readBillingStudents,
  type BillingAttentionItem,
  type BillingBalanceExplanationRow,
  type BillingBalanceViewRow,
  type BillingCenterSnapshot,
  type BillingCompanyClientRow,
  type BillingContractorSettlementRow,
  type BillingFamilyFoundationRow,
  type BillingErrorState,
  type BillingInvoicePaymentRow,
  type BillingRecentPaymentRow,
  type BillingRelatedWorkItemRow,
  type BillingServiceEnrollmentRow,
  type BillingStatus,
} from "./billingModel";

type BillingLedgerOverviewProps = {
  title: "Rozliczenia";
  eyebrow: string;
  description: string;
};

const balanceColumns: Array<TableColumn<BillingBalanceViewRow>> = [
  {
    key: "payer",
    header: "Płatnik",
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
    key: "balance",
    header: "Saldo",
    align: "right",
    render: (row) => row.balanceDueLabel,
  },
  {
    key: "lastPayment",
    header: "Ostatnia wpłata",
    render: (row) => row.lastPaymentLabel,
  },
];

const familyFoundationColumns: Array<TableColumn<BillingFamilyFoundationRow>> = [
  {
    key: "family",
    header: "Płatnik",
    render: (row) => (
      <Link className="module-row-title module-link" href={row.href}>
        <UsersRound aria-hidden="true" size={16} />
        {row.familyLabel}
      </Link>
    ),
  },
  {
    key: "students",
    header: "Uczniowie",
    render: (row) => (
      <span className="billing-family-cell">
        <strong>{row.studentSummaryLabel}</strong>
        <span>{row.studentsLabel}</span>
      </span>
    ),
  },
  {
    key: "siblings",
    header: "Rodzeństwo",
    render: (row) => row.siblingLabel,
  },
  {
    key: "status",
    header: "Status",
    render: (row) => <StatusBadge status={row.statusTone}>{row.statusLabel}</StatusBadge>,
  },
  {
    key: "balance",
    header: "Saldo",
    align: "right",
    render: (row) => row.balanceLabel,
  },
  {
    key: "context",
    header: "Kontekst",
    render: (row) => row.contextLabel,
  },
];

const balanceExplanationColumns: Array<TableColumn<BillingBalanceExplanationRow>> = [
  {
    key: "payer",
    header: "Płatnik",
    render: (row) => (
      <span className="billing-family-cell">
        <strong>{row.payerLabel}</strong>
        <span>{row.familyTypeLabel}</span>
      </span>
    ),
  },
  {
    key: "charged",
    header: "Naliczono",
    align: "right",
    render: (row) => row.chargedLabel,
  },
  {
    key: "paid",
    header: "Wpłacono",
    align: "right",
    render: (row) => row.paidLabel,
  },
  {
    key: "balance",
    header: "Wynik",
    render: (row) => <StatusBadge status={row.statusTone}>{row.balanceMeaningLabel}</StatusBadge>,
  },
  {
    key: "lastPayment",
    header: "Ostatnia wpłata",
    render: (row) => row.lastPaymentLabel,
  },
  {
    key: "items",
    header: "Najważniejsze pozycje",
    render: (row) => (
      <span className="billing-family-cell">
        <span>{row.topItemsLabel}</span>
        <span>{row.explanationLabel}</span>
      </span>
    ),
  },
];

const serviceEnrollmentColumns: Array<TableColumn<BillingServiceEnrollmentRow>> = [
  {
    key: "service",
    header: "Usługa",
    render: (row) => (
      <Link className="module-link" href={row.href}>
        {row.serviceLabel}
      </Link>
    ),
  },
  { key: "type", header: "Typ", render: (row) => row.serviceTypeLabel },
  {
    key: "payer",
    header: "Płatnik",
    render: (row) => (
      <span className="billing-family-cell">
        <strong>{row.payerLabel}</strong>
        <span>{row.personLabel}</span>
      </span>
    ),
  },
  { key: "period", header: "Okres", render: (row) => row.periodLabel },
  { key: "status", header: "Status", render: (row) => row.statusLabel },
  { key: "amount", header: "Naliczenia", align: "right", render: (row) => row.amountLabel },
  {
    key: "source",
    header: "Źródło danych",
    render: (row) => (
      <span className="billing-family-cell">
        <span>{row.sourceLabel}</span>
        <span>{row.contextLabel}</span>
      </span>
    ),
  },
];

const companyClientColumns: Array<TableColumn<BillingCompanyClientRow>> = [
  {
    key: "company",
    header: "Klient firmowy",
    render: (row) => (
      <Link className="module-link" href={row.href}>
        {row.companyLabel}
      </Link>
    ),
  },
  {
    key: "contact",
    header: "Kontakt",
    render: (row) => row.contactLabel,
  },
  {
    key: "invoices",
    header: "Faktury",
    align: "right",
    render: (row) => row.invoiceCountLabel,
  },
  {
    key: "balance",
    header: "Saldo",
    align: "right",
    render: (row) => row.balanceLabel,
  },
  {
    key: "context",
    header: "Kontekst",
    render: (row) => row.contextLabel,
  },
];

const invoiceColumns: Array<TableColumn<BillingInvoicePaymentRow>> = [
  {
    key: "invoice",
    header: "Faktura",
    render: (row) => (
      <Link className="module-link" href={row.href}>
        {row.invoiceLabel}
      </Link>
    ),
  },
  {
    key: "contractor",
    header: "Kontrahent",
    render: (row) => row.contractorLabel,
  },
  {
    key: "status",
    header: "Status",
    render: (row) => row.statusLabel,
  },
  {
    key: "amount",
    header: "Kwota",
    align: "right",
    render: (row) => row.amountLabel,
  },
  {
    key: "reason",
    header: "Dlaczego ważne",
    render: (row) => row.reasonLabel,
  },
];

const contractorColumns: Array<TableColumn<BillingContractorSettlementRow>> = [
  {
    key: "contractor",
    header: "Kontrahent",
    render: (row) => (
      <Link className="module-link" href={row.href}>
        {row.contractorLabel}
      </Link>
    ),
  },
  {
    key: "contact",
    header: "Kontakt",
    render: (row) => row.contactLabel,
  },
  {
    key: "balance",
    header: "Saldo",
    align: "right",
    render: (row) => row.balanceLabel,
  },
  {
    key: "invoices",
    header: "Faktury",
    align: "right",
    render: (row) => row.invoiceCountLabel,
  },
  {
    key: "reason",
    header: "Kontekst",
    render: (row) => row.reasonLabel,
  },
];

const workItemColumns: Array<TableColumn<BillingRelatedWorkItemRow>> = [
  {
    key: "title",
    header: "Sprawa",
    render: (row) => (
      <Link className="module-link" href={row.href}>
        {row.titleLabel}
      </Link>
    ),
  },
  {
    key: "status",
    header: "Status",
    render: (row) => row.statusLabel,
  },
  {
    key: "priority",
    header: "Priorytet",
    render: (row) => row.priorityLabel,
  },
  {
    key: "reason",
    header: "Kontekst",
    render: (row) => row.reasonLabel,
  },
];

const recentPaymentColumns: Array<TableColumn<BillingRecentPaymentRow>> = [
  {
    key: "payer",
    header: "Płatnik",
    render: (row) => row.payerLabel,
  },
  {
    key: "amount",
    header: "Kwota",
    align: "right",
    render: (row) => row.amountLabel,
  },
  {
    key: "date",
    header: "Data",
    render: (row) => row.dateLabel,
  },
  {
    key: "title",
    header: "Opis",
    render: (row) => row.titleLabel,
  },
];

export function BillingLedgerOverview({ title, eyebrow, description }: BillingLedgerOverviewProps) {
  const { selectedOrganizationId, selectedOrganization, status: organizationStatus } = useActiveOrganization();
  const [snapshot, setSnapshot] = useState<BillingCenterSnapshot | null>(null);
  const [status, setStatus] = useState<BillingStatus>("idle");
  const [errorState, setErrorState] = useState<BillingErrorState | null>(null);

  const loadBillingCenter = useCallback(async () => {
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
      const openWorkItemsQuery = withActiveOrganizationQuery(selectedOrganizationId, { limit: 100, only_open: 1 });
      const [balancesPayload, payersPayload, studentsPayload, chargesPayload, invoicesPayload, contractorsPayload, workItemsPayload] = await Promise.all([
        api.ledgerBalances(query),
        api.billingPayers(query),
        api.billingStudents(query),
        api.billingCharges(withActiveOrganizationQuery(selectedOrganizationId, { limit: 100 })),
        api.invoices(query),
        api.contractors(query),
        api.workItems(openWorkItemsQuery),
      ]);

      setSnapshot({
        balances: readBillingBalances(balancesPayload),
        payers: readBillingPayers(payersPayload),
        students: readBillingStudents(studentsPayload),
        charges: readBillingCharges(chargesPayload),
        invoices: readBillingInvoices(invoicesPayload),
        contractors: readContractors(contractorsPayload),
        workItems: readWorkItems(workItemsPayload),
      });
      setStatus("ready");
    } catch (error) {
      const nextErrorState = getBillingErrorState(error);
      setErrorState(nextErrorState);
      setSnapshot(null);
      setStatus(nextErrorState.status);
    }
  }, [organizationStatus, selectedOrganizationId]);

  useEffect(() => {
    void loadBillingCenter();
  }, [loadBillingCenter]);

  const attentionItems = useMemo(() => (snapshot ? buildBillingAttentionItems(snapshot) : []), [snapshot]);
  const moneySummary = useMemo(
    () => (snapshot ? buildBillingMoneySummary(snapshot.balances, attentionItems.length) : null),
    [attentionItems.length, snapshot],
  );
  const balanceRows = useMemo(() => buildBillingBalanceRows(snapshot?.balances ?? []), [snapshot]);
  const familyRows = useMemo(
    () => buildBillingFamilyFoundationRows(snapshot?.payers ?? [], snapshot?.students ?? [], snapshot?.balances ?? []),
    [snapshot],
  );
  const balanceExplanationRows = useMemo(
    () =>
      buildBillingBalanceExplanationRows(
        snapshot?.balances ?? [],
        snapshot?.payers ?? [],
        snapshot?.students ?? [],
        snapshot?.charges ?? [],
      ),
    [snapshot],
  );
  const serviceEnrollmentRows = useMemo(() => (snapshot ? buildBillingServiceEnrollmentRows(snapshot) : []), [snapshot]);
  const companyClientRows = useMemo(
    () => buildBillingCompanyClientRows(snapshot?.contractors ?? [], snapshot?.balances ?? [], snapshot?.payers ?? []),
    [snapshot],
  );
  const invoiceRows = useMemo(() => buildBillingInvoiceRows(snapshot?.invoices ?? []), [snapshot]);
  const contractorRows = useMemo(() => buildBillingContractorRows(snapshot?.contractors ?? [], snapshot?.balances ?? []), [snapshot]);
  const workItemRows = useMemo(
    () => buildBillingRelatedWorkItemRows(snapshot?.workItems ?? [], snapshot?.invoices ?? [], snapshot?.contractors ?? []),
    [snapshot],
  );
  const recentPaymentRows = useMemo(() => buildBillingRecentPaymentRows(snapshot?.balances ?? []), [snapshot]);
  const hasData = hasBillingCenterData(status, snapshot);
  const organizationMissing = organizationStatus === "ready" && !canUseBillingOrganizationScope(selectedOrganizationId);
  const readyWithoutData = !organizationMissing && isBillingCenterEmpty(status, snapshot);

  return (
    <div className="module-page billing-page billing-center-page">
      <PageHeader
        badgeTone={status === "ready" ? "success" : status === "error" ? "warning" : "info"}
        description={description}
        eyebrow={status === "ready" ? "Centrum rozliczeń" : eyebrow}
        title={title}
        actions={
          <Button disabled={status === "loading"} icon={<RefreshCw size={15} />} onClick={loadBillingCenter} size="sm" variant="secondary">
            Odśwież
          </Button>
        }
      />

      {status === "loading" ? <LoadingState /> : null}
      {errorState ? <ErrorState description={errorState.description} title={errorState.title} /> : null}
      {organizationMissing ? (
        <EmptyState description={BILLING_ORGANIZATION_REQUIRED_DESCRIPTION} title={BILLING_ORGANIZATION_REQUIRED_TITLE} />
      ) : null}
      {readyWithoutData ? (
        <EmptyState
          description={`Nie ma jeszcze danych rozliczeniowych, faktur ani powiązanych spraw dla organizacji ${selectedOrganization?.name ?? selectedOrganizationId}.`}
          title="Brak rozliczeń do pokazania"
        />
      ) : null}

      {hasData && snapshot && moneySummary ? (
        <>
          <Card
            action={<StatusBadge status={moneySummary.headlineTone}>{moneySummary.headline}</StatusBadge>}
            description={`Widok dla organizacji ${selectedOrganization?.name ?? selectedOrganizationId}. Pokazuje sytuację pieniędzy, płatności i zaległości bez wykonywania operacji finansowych.`}
            title="Nagłówek finansowy"
          >
            <div className="billing-center-hero" aria-label="Sytuacja rozliczeń">
              <div>
                <span>Saldo netto</span>
                <strong>{formatMoney(moneySummary.netBalance)}</strong>
              </div>
              <div>
                <span>Do kontroli</span>
                <strong>{moneySummary.attentionCount}</strong>
              </div>
              <div>
                <span>Ostatnia wpłata</span>
                <strong>{moneySummary.lastPaymentLabel}</strong>
              </div>
            </div>
          </Card>

          <section className="module-kpi-row" aria-label="Podsumowanie pieniędzy">
            <Card className="module-metric">
              <span className="module-metric__icon"><WalletCards aria-hidden="true" size={18} /></span>
              <span className="module-metric__label">Należności</span>
              <strong>{formatMoney(moneySummary.receivables)}</strong>
              <span>Kwoty, które nadal wymagają rozliczenia.</span>
            </Card>
            <Card className="module-metric">
              <span className="module-metric__icon"><CreditCard aria-hidden="true" size={18} /></span>
              <span className="module-metric__label">Nadpłaty</span>
              <strong>{formatMoney(moneySummary.overpayments)}</strong>
              <span>Środki lub korekty do wyjaśnienia.</span>
            </Card>
            <Card className="module-metric">
              <span className="module-metric__icon"><Building2 aria-hidden="true" size={18} /></span>
              <span className="module-metric__label">Płatnicy</span>
              <strong>{moneySummary.activePayerCount}/{moneySummary.payerCount}</strong>
              <span>Aktywni płatnicy w rozliczeniach.</span>
            </Card>
            <Card className="module-metric">
              <span className="module-metric__icon"><ListChecks aria-hidden="true" size={18} /></span>
              <span className="module-metric__label">Tryb</span>
              <strong>{BILLING_READ_ONLY ? "Tylko odczyt" : "Akcje włączone"}</strong>
              <span>Bez zapisu, importu i dopasowywania płatności.</span>
            </Card>
          </section>

          <section className="invoice-detail-grid billing-center-grid" aria-label="Centrum rozliczeń">
            <div className="invoice-detail-grid__main">
              <Card
                description="Najkrótsza lista spraw finansowych, które warto zobaczyć przed fakturami i tabelami."
                title="Co wymaga uwagi"
              >
                <BillingAttentionList items={attentionItems} />
              </Card>

              <Card
                description="Pierwsza warstwa pełnego modułu rozliczeń: kto jest płatnikiem, za kogo płaci i czy klient jest rodziną ucznia czy firmą."
                title="Płatnicy i osoby objęte rozliczeniem"
              >
                <Table
                  columns={familyFoundationColumns}
                  data={familyRows}
                  emptyMessage="Brak płatników i osób objętych rozliczeniem dla tej organizacji."
                  getRowKey={(row) => row.id}
                />

                <div className="billing-subsection">
                  <h3>Klienci firmowi</h3>
                  <p>Kontrahenci firmowi są pokazani osobno, żeby nie mieszać ich z rodzinnymi kontami uczniów.</p>
                </div>
                <Table
                  columns={companyClientColumns}
                  data={companyClientRows}
                  emptyMessage="Brak klientów firmowych do pokazania w tej organizacji."
                  getRowKey={(row) => row.id}
                />
              </Card>

              <Card
                description="Read-only fundament odpowiedzi: za co płatnik płaci. W tej wersji część usług jest odczytywana z modeli, naliczeń i faktur, bez pełnego modelu zapisów."
                title="Usługi i zapisy"
              >
                <Table
                  columns={serviceEnrollmentColumns}
                  data={serviceEnrollmentRows}
                  emptyMessage="Brak usług do pokazania. W tej wersji usługi są widoczne tylko wtedy, gdy wynikają z naliczeń albo faktur."
                  getRowKey={(row) => row.id}
                />
              </Card>

              <Card
                description="Wyjaśnienie salda tylko do odczytu: naliczone kwoty, widoczne wpłaty i różnica. To nie jest jeszcze pełny silnik naliczeń ani księgowanie."
                title="Skąd wynika saldo"
              >
                <Table
                  columns={balanceExplanationColumns}
                  data={balanceExplanationRows}
                  emptyMessage="Brakuje danych, żeby szczegółowo wyjaśnić saldo dla tej organizacji."
                  getRowKey={(row) => row.id}
                />
              </Card>

              <Card
                description="Faktury pokazane w kontekście kwot, statusów i powodów, dla których warto je sprawdzić."
                title="Faktury i płatności"
              >
                <Table
                  columns={invoiceColumns}
                  data={invoiceRows}
                  emptyMessage="Brak faktur do pokazania w rozliczeniach tej organizacji."
                  getRowKey={(row) => row.id}
                />
              </Card>

              <Card
                description="Kontrahenci, którzy mają historię faktur albo saldo widoczne w rozliczeniach."
                title="Kontrahenci z rozliczeniami"
              >
                <Table
                  columns={contractorColumns}
                  data={contractorRows}
                  emptyMessage="Brak kontrahentów z widocznym kontekstem rozliczeń."
                  getRowKey={(row) => row.id}
                />
              </Card>

              <Card
                description="Sprawy operacyjne, które mogą wpływać na faktury, płatności albo wyjaśnienia z kontrahentami."
                title="Powiązane sprawy"
              >
                <Table
                  columns={workItemColumns}
                  data={workItemRows}
                  emptyMessage="Brak otwartych spraw powiązanych z rozliczeniami."
                  getRowKey={(row) => row.id}
                />
              </Card>

              <Card
                description="Bieżące salda płatników w uproszczonym widoku. Szczegółowe operacje finansowe nie są wykonywane z tego ekranu."
                title="Podsumowanie pieniędzy"
              >
                <Table
                  columns={balanceColumns}
                  data={balanceRows}
                  emptyMessage="Brak sald płatników dla tej organizacji."
                  getRowKey={(row) => row.id}
                />
              </Card>
            </div>

            <aside className="module-activity-panel" aria-label="Kontekst biznesowy rozliczeń">
              <Card title="Historia / ostatnie zdarzenia" description="Ostatnie wpłaty widoczne w rozliczeniach, bez technicznych danych bankowych.">
                <Table
                  columns={recentPaymentColumns}
                  data={recentPaymentRows}
                  emptyMessage="Brak ostatnich wpłat w danych rozliczeń."
                  getRowKey={(row) => row.id}
                />
              </Card>

              <Card title="Kontekst biznesowy">
                <div className="billing-context-list">
                  <article>
                    <span>Cel widoku</span>
                    <strong>Jedno miejsce do szybkiej oceny pieniędzy, płatności i zaległości.</strong>
                  </article>
                  <article>
                    <span>Zakres</span>
                    <strong>Widok łączy rozliczenia, faktury, kontrahentów i sprawy operacyjne.</strong>
                  </article>
                  <article>
                    <span>Bezpieczeństwo</span>
                    <strong>Centrum rozliczeń jest tylko do odczytu i nie wykonuje operacji finansowych.</strong>
                  </article>
                </div>
              </Card>

              <Card className="module-quick-actions" title="Przejdź do modułów">
                <Link className="module-quick-action" href={BILLING_WORK_QUEUE_ROUTE}>
                  <span>Sprawy rozliczeniowe</span>
                  <ListChecks aria-hidden="true" size={15} />
                </Link>
                <Link className="module-quick-action" href={BILLING_CONTACT_CENTER_ROUTE}>
                  <span>Kontakty rozliczeniowe</span>
                  <MessageSquareText aria-hidden="true" size={15} />
                </Link>
                <Link className="module-quick-action" href="/faktury">
                  <span>Faktury</span>
                  <FileText aria-hidden="true" size={15} />
                </Link>
                <Link className="module-quick-action" href="/crm">
                  <span>Kontrahenci</span>
                  <Building2 aria-hidden="true" size={15} />
                </Link>
                <Link className="module-quick-action" href="/work-items">
                  <span>Sprawy</span>
                  <ListChecks aria-hidden="true" size={15} />
                </Link>
                <Link className="module-quick-action" href="/rozliczenia/okresy">
                  <span>Okresy rozliczeniowe</span>
                  <CalendarDays aria-hidden="true" size={15} />
                </Link>
                <Link className="module-quick-action" href="/rozliczenia/wplaty">
                  <span>Wpłaty i przypisania</span>
                  <WalletCards aria-hidden="true" size={15} />
                </Link>
                <Link className="module-quick-action" href={BILLING_DEBTS_ROUTE}>
                  <span>Zaległości i nadpłaty</span>
                  <CreditCard aria-hidden="true" size={15} />
                </Link>
                <Link className="module-quick-action" href="/pulpit-dnia">
                  <span>Pulpit dnia</span>
                  <ArrowRight aria-hidden="true" size={15} />
                </Link>
              </Card>
            </aside>
          </section>
        </>
      ) : null}
    </div>
  );
}

function BillingAttentionList({ items }: { items: BillingAttentionItem[] }) {
  if (!items.length) {
    return <p className="daily-brief-empty">Nie ma pilnych sygnałów finansowych. Rozliczenia wyglądają spokojnie.</p>;
  }

  return (
    <div className="daily-brief-list billing-attention-list">
      {items.map((item) => (
        <Link className="daily-brief-item" href={item.href} key={item.id}>
          <span className={`daily-brief-item__tone daily-brief-item__tone--${item.tone}`} aria-hidden="true" />
          <span className="daily-brief-item__copy">
            <span className="daily-brief-item__category">{item.category}</span>
            <strong>{item.title}</strong>
            <span>{item.reason}</span>
          </span>
          <span className="daily-brief-item__meta">Otwórz</span>
        </Link>
      ))}
    </div>
  );
}
