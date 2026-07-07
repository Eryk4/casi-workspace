"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import { ArrowLeft, CreditCard, FileText, ListChecks, MessageSquareText, RefreshCw, UsersRound, WalletCards } from "lucide-react";

import { Badge } from "@/components/ui/Badge";
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
  BILLING_PAYER_NOTE_HELP_TEXT,
  BILLING_PAYER_NOTE_MAX_LENGTH,
  BILLING_PAYER_DETAIL_ORGANIZATION_REQUIRED_DESCRIPTION,
  BILLING_PAYER_DETAIL_ORGANIZATION_REQUIRED_TITLE,
  BILLING_READ_ONLY,
  buildBillingPayerNoteRequest,
  buildBillingPayerDetailView,
  canUseBillingOrganizationScope,
  createBillingPayerNoteSubmitter,
  getBillingErrorState,
  readBillingBalances,
  readBillingCharges,
  readBillingInvoices,
  readBillingPayerNotes,
  readBillingPayers,
  readBillingStudents,
  type BillingBalanceExplanationRow,
  type BillingCenterSnapshot,
  type BillingErrorState,
  type BillingPayerChargeRow,
  type BillingPayerDetailView,
  type BillingPayerNoteErrorState,
  type BillingPayerNoteRow,
  type BillingPayerPaymentRow,
  type BillingPayerPersonRow,
  type BillingPayerRelatedInvoiceRow,
  type BillingPayerServiceRow,
  type BillingRelatedWorkItemRow,
  type BillingStatus,
} from "./billingModel";

const personColumns: Array<TableColumn<BillingPayerPersonRow>> = [
  {
    key: "person",
    header: "Osoba",
    render: (row) => (
      <span className="module-row-title">
        <UsersRound aria-hidden="true" size={16} />
        {row.personLabel}
      </span>
    ),
  },
  { key: "service", header: "Usługa", render: (row) => row.serviceLabel },
  { key: "group", header: "Grupa / termin", render: (row) => row.groupLabel },
  { key: "status", header: "Status", render: (row) => row.statusLabel },
  { key: "context", header: "Kontekst", render: (row) => row.contextLabel },
];

const serviceColumns: Array<TableColumn<BillingPayerServiceRow>> = [
  { key: "service", header: "Usługa", render: (row) => row.serviceLabel },
  { key: "type", header: "Typ", render: (row) => row.serviceTypeLabel },
  { key: "people", header: "Kogo dotyczy", render: (row) => row.peopleLabel },
  { key: "periods", header: "Okresy", render: (row) => row.periodsLabel },
  { key: "status", header: "Status", render: (row) => row.statusLabel },
  { key: "amount", header: "Naliczenia", align: "right", render: (row) => row.amountLabel },
  {
    key: "source",
    header: "Źródło danych",
    render: (row) => (
      <span className="billing-family-cell">
        <span>{row.chargeCountLabel}</span>
        <span>{row.sourceLabel}</span>
      </span>
    ),
  },
  { key: "context", header: "Kontekst", render: (row) => row.contextLabel },
];

const balanceColumns: Array<TableColumn<BillingBalanceExplanationRow>> = [
  { key: "charged", header: "Naliczono", align: "right", render: (row) => row.chargedLabel },
  { key: "paid", header: "Wpłacono", align: "right", render: (row) => row.paidLabel },
  { key: "result", header: "Wynik", render: (row) => <StatusBadge status={row.statusTone}>{row.balanceMeaningLabel}</StatusBadge> },
  { key: "lastPayment", header: "Ostatnia wpłata", render: (row) => row.lastPaymentLabel },
  {
    key: "explanation",
    header: "Wyjaśnienie",
    render: (row) => (
      <span className="billing-family-cell">
        <span>{row.topItemsLabel}</span>
        <span>{row.explanationLabel}</span>
      </span>
    ),
  },
];

const chargeColumns: Array<TableColumn<BillingPayerChargeRow>> = [
  { key: "period", header: "Okres", render: (row) => row.periodLabel },
  { key: "person", header: "Osoba", render: (row) => row.personLabel },
  { key: "service", header: "Usługa", render: (row) => row.serviceLabel },
  { key: "amount", header: "Kwota", align: "right", render: (row) => row.amountLabel },
  { key: "status", header: "Status", render: (row) => row.statusLabel },
];

const paymentColumns: Array<TableColumn<BillingPayerPaymentRow>> = [
  { key: "date", header: "Data", render: (row) => row.dateLabel },
  { key: "amount", header: "Kwota", align: "right", render: (row) => row.amountLabel },
  { key: "title", header: "Opis", render: (row) => row.titleLabel },
  { key: "context", header: "Kontekst", render: (row) => row.contextLabel },
];

const invoiceColumns: Array<TableColumn<BillingPayerRelatedInvoiceRow>> = [
  {
    key: "invoice",
    header: "Faktura",
    render: (row) => (
      <Link className="module-link" href={row.href}>
        {row.invoiceLabel}
      </Link>
    ),
  },
  { key: "contractor", header: "Kontrahent", render: (row) => row.contractorLabel },
  { key: "amount", header: "Kwota", align: "right", render: (row) => row.amountLabel },
  { key: "status", header: "Status", render: (row) => row.statusLabel },
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
  { key: "status", header: "Status", render: (row) => row.statusLabel },
  { key: "priority", header: "Priorytet", render: (row) => row.priorityLabel },
  { key: "reason", header: "Kontekst", render: (row) => row.reasonLabel },
];

export function BillingPayerDetailPage({ payerId }: { payerId: number }) {
  const { selectedOrganizationId, selectedOrganization, status: organizationStatus } = useActiveOrganization();
  const [snapshot, setSnapshot] = useState<BillingCenterSnapshot | null>(null);
  const [status, setStatus] = useState<BillingStatus>("idle");
  const [errorState, setErrorState] = useState<BillingErrorState | null>(null);
  const [noteText, setNoteText] = useState("");
  const [noteSubmitting, setNoteSubmitting] = useState(false);
  const [noteErrorState, setNoteErrorState] = useState<BillingPayerNoteErrorState | null>(null);
  const [noteSuccessMessage, setNoteSuccessMessage] = useState<string | null>(null);

  const loadPayer = useCallback(async () => {
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
      const [
        balancesPayload,
        payersPayload,
        studentsPayload,
        chargesPayload,
        payerNotesPayload,
        invoicesPayload,
        contractorsPayload,
        workItemsPayload,
      ] = await Promise.all([
        api.ledgerBalances(query),
        api.billingPayers(query),
        api.billingStudents(query),
        api.billingCharges(withActiveOrganizationQuery(selectedOrganizationId, { limit: 200 })),
        api.billingPayerNotes(payerId, withActiveOrganizationQuery(selectedOrganizationId, { limit: 100 })),
        api.invoices(query),
        api.contractors(query),
        api.workItems(withActiveOrganizationQuery(selectedOrganizationId, { limit: 100, only_open: 1 })),
      ]);

      setSnapshot({
        balances: readBillingBalances(balancesPayload),
        payers: readBillingPayers(payersPayload),
        students: readBillingStudents(studentsPayload),
        charges: readBillingCharges(chargesPayload),
        payerNotes: readBillingPayerNotes(payerNotesPayload),
        invoices: readBillingInvoices(invoicesPayload),
        contractors: readContractors(contractorsPayload),
        workItems: readWorkItems(workItemsPayload),
      });
      setStatus("ready");
    } catch (error) {
      const nextErrorState = getBillingErrorState(error);
      setSnapshot(null);
      setErrorState(nextErrorState);
      setStatus(nextErrorState.status);
    }
  }, [organizationStatus, payerId, selectedOrganizationId]);

  useEffect(() => {
    void loadPayer();
  }, [loadPayer]);

  const detail = useMemo<BillingPayerDetailView | null>(() => (snapshot ? buildBillingPayerDetailView(snapshot, payerId) : null), [payerId, snapshot]);
  const noteSubmitter = useMemo(
    () =>
      createBillingPayerNoteSubmitter({
        refreshDetail: loadPayer,
        setSubmitting: setNoteSubmitting,
        submitNote: (payload) => api.addBillingPayerNote(payerId, payload.note_text, selectedOrganizationId),
      }),
    [loadPayer, payerId, selectedOrganizationId],
  );
  const organizationMissing = organizationStatus === "ready" && !canUseBillingOrganizationScope(selectedOrganizationId);
  const notFound = status === "ready" && snapshot && !detail;
  const headerBadgeTone = detail?.statusTone === "ok" ? "success" : detail?.statusTone ?? (status === "error" ? "warning" : "info");

  const handleNoteSubmit = useCallback(
    async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      setNoteErrorState(null);
      setNoteSuccessMessage(null);

      const validation = buildBillingPayerNoteRequest(noteText, selectedOrganizationId);
      const result = await noteSubmitter(validation);

      if (result.status === "blocked") {
        setNoteErrorState({
          status: "error",
          title: "Nie można dodać notatki",
          description: result.message,
        });
        return;
      }

      if (result.status === "error") {
        setNoteErrorState(result.errorState);
        return;
      }

      if (result.status === "success") {
        setNoteText("");
        setNoteSuccessMessage("Notatka rozliczeniowa została dodana.");
      }
    },
    [noteSubmitter, noteText, selectedOrganizationId],
  );

  return (
    <div className="module-page billing-page billing-payer-detail-page">
      <PageHeader
        badgeTone={headerBadgeTone}
        description="Read-only kontekst płatnika: kto jest objęty rozliczeniem, z czego wynika saldo i jakie sprawy są powiązane."
        eyebrow="Szczegół płatnika"
        title={detail?.title ?? "Płatnik"}
        actions={
          <div className="module-page-actions">
            <Link className="ui-button ui-button--secondary ui-button--sm" href={BILLING_CANONICAL_ROUTE}>
              <span className="ui-button__icon"><ArrowLeft size={15} /></span>
              <span>Wróć do rozliczeń</span>
            </Link>
            <Button disabled={status === "loading"} icon={<RefreshCw size={15} />} onClick={loadPayer} size="sm" variant="secondary">
              Odśwież
            </Button>
          </div>
        }
      />

      {status === "loading" ? <LoadingState /> : null}
      {errorState ? <ErrorState description={errorState.description} title={errorState.title} /> : null}
      {organizationMissing ? (
        <EmptyState description={BILLING_PAYER_DETAIL_ORGANIZATION_REQUIRED_DESCRIPTION} title={BILLING_PAYER_DETAIL_ORGANIZATION_REQUIRED_TITLE} />
      ) : null}
      {notFound ? (
        <EmptyState
          description="Ten płatnik nie istnieje w wybranej organizacji albo nie jest dostępny dla bieżącego użytkownika."
          title="Nie znaleziono płatnika"
        />
      ) : null}

      {status === "ready" && detail ? (
        <>
          <Card
            action={<StatusBadge status={detail.statusTone}>{detail.statusLabel}</StatusBadge>}
            description={`Widok dla organizacji ${selectedOrganization?.name ?? selectedOrganizationId}. Nie wykonuje operacji finansowych.`}
            title="Profil płatnika"
          >
            <div className="billing-center-hero" aria-label="Profil płatnika">
              <div>
                <span>Typ</span>
                <strong>{detail.payerTypeLabel}</strong>
              </div>
              <div>
                <span>Saldo</span>
                <strong>{detail.balanceMeaningLabel}</strong>
              </div>
              <div>
                <span>Ostatnia wpłata</span>
                <strong>{detail.lastPaymentLabel}</strong>
              </div>
            </div>
          </Card>

          <section className="module-kpi-row" aria-label="Podsumowanie płatnika">
            <Card className="module-metric">
              <span className="module-metric__icon"><UsersRound aria-hidden="true" size={18} /></span>
              <span className="module-metric__label">Osoby</span>
              <strong>{detail.peopleRows.length || "Brak"}</strong>
              <span>Osoby objęte tym rozliczeniem.</span>
            </Card>
            <Card className="module-metric">
              <span className="module-metric__icon"><WalletCards aria-hidden="true" size={18} /></span>
              <span className="module-metric__label">Naliczono</span>
              <strong>{detail.chargedLabel}</strong>
              <span>Kwoty widoczne w obecnych danych.</span>
            </Card>
            <Card className="module-metric">
              <span className="module-metric__icon"><CreditCard aria-hidden="true" size={18} /></span>
              <span className="module-metric__label">Wpłacono</span>
              <strong>{detail.paidLabel}</strong>
              <span>Wpłaty widoczne w ledgerze.</span>
            </Card>
            <Card className="module-metric">
              <span className="module-metric__icon"><ListChecks aria-hidden="true" size={18} /></span>
              <span className="module-metric__label">Tryb</span>
              <strong>{BILLING_READ_ONLY ? "Tylko odczyt" : "Akcje włączone"}</strong>
              <span>Bez naliczania, importu i dopasowywania płatności.</span>
            </Card>
          </section>

          <section className="invoice-detail-grid billing-center-grid" aria-label="Szczegół płatnika">
            <div className="invoice-detail-grid__main">
              <Card description="Osoby, za które odpowiada ten płatnik. Rodzina jest tu szczególnym przypadkiem płatnika." title="Osoby objęte rozliczeniem">
                <Table columns={personColumns} data={detail.peopleRows} emptyMessage="Brak osób przypisanych do tego płatnika." getRowKey={(row) => row.id} />
              </Card>

              <Card description="Usługi widoczne przez naliczenia i modele rozliczeń. To nadal read-only fundament, bez pełnego modelu zapisów i cenników." title="Usługi do opłacenia">
                <Table columns={serviceColumns} data={detail.serviceRows} emptyMessage="Brak usług lub naliczeń przypisanych do tego płatnika." getRowKey={(row) => row.id} />
              </Card>

              <Card description="Proste wyjaśnienie salda: naliczenia, wpłaty i różnica. To nie jest pełna księgowość." title="Wyjaśnienie salda">
                <Table columns={balanceColumns} data={detail.balanceExplanationRows} emptyMessage="Brak danych do wyjaśnienia salda tego płatnika." getRowKey={(row) => row.id} />
              </Card>

              <Card description="Najważniejsze naliczenia widoczne dla płatnika. Widok nie tworzy i nie koryguje opłat." title="Naliczenia">
                <Table columns={chargeColumns} data={detail.chargeRows} emptyMessage="Brak naliczeń dla tego płatnika." getRowKey={(row) => row.id} />
              </Card>

              <Card description="Wpłaty widoczne w obecnym read-only modelu. Jeśli brak listy transakcji, pokazujemy ostatnią znaną wpłatę." title="Widoczne wpłaty">
                <Table columns={paymentColumns} data={detail.paymentRows} emptyMessage="Brak widocznych wpłat dla tego płatnika." getRowKey={(row) => row.id} />
              </Card>

              <Card
                action={<Badge tone="success">Addytywne</Badge>}
                description="Notatka rozliczeniowa zapisuje kontekst rozmowy lub ustalenia. Nie zmienia salda, naliczeń ani przypisań wpłat."
                title="Notatki rozliczeniowe"
              >
                <form className="invoice-comment-form" onSubmit={handleNoteSubmit}>
                  <label className="invoice-comment-form__label" htmlFor="billing-payer-note-text">
                    Treść notatki
                  </label>
                  <textarea
                    className="invoice-comment-form__textarea"
                    disabled={noteSubmitting}
                    id="billing-payer-note-text"
                    maxLength={BILLING_PAYER_NOTE_MAX_LENGTH}
                    onChange={(event) => {
                      setNoteText(event.target.value);
                      if (noteErrorState) {
                        setNoteErrorState(null);
                      }
                      if (noteSuccessMessage) {
                        setNoteSuccessMessage(null);
                      }
                    }}
                    placeholder="Np. Płatnik potwierdził, że prześle potwierdzenie wpłaty do piątku."
                    rows={4}
                    value={noteText}
                  />
                  <div className="invoice-comment-form__meta">
                    <span>{BILLING_PAYER_NOTE_HELP_TEXT}</span>
                    <span>{noteText.trim().length}/{BILLING_PAYER_NOTE_MAX_LENGTH}</span>
                  </div>
                  {noteErrorState ? (
                    <div className="invoice-comment-form__message invoice-comment-form__message--error" role="alert">
                      <strong>{noteErrorState.title}</strong>
                      <span>{noteErrorState.description}</span>
                    </div>
                  ) : null}
                  {noteSuccessMessage ? (
                    <div className="invoice-comment-form__message invoice-comment-form__message--success" role="status">
                      {noteSuccessMessage}
                    </div>
                  ) : null}
                  <Button disabled={noteSubmitting || !noteText.trim()} size="sm" type="submit">
                    {noteSubmitting ? "Dodawanie..." : "Dodaj notatkę"}
                  </Button>
                </form>

                <div className="module-readiness" aria-label="Notatki rozliczeniowe płatnika">
                  {detail.noteRows.length ? (
                    detail.noteRows.map((note: BillingPayerNoteRow) => (
                      <div className="module-readiness__item" key={note.id}>
                        <MessageSquareText aria-hidden="true" size={17} />
                        <div>
                          <strong>{note.authorLabel}</strong>
                          <span>{note.dateLabel} · {note.typeLabel}</span>
                          <p>{note.noteText}</p>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="module-readiness__item">
                      <MessageSquareText aria-hidden="true" size={17} />
                      <div>
                        <strong>Brak notatek rozliczeniowych</strong>
                        <span>Możesz dodać pierwszą notatkę operatora dla tego płatnika.</span>
                      </div>
                    </div>
                  )}
                </div>
              </Card>

              <Card description="Faktury powiązane z płatnikiem, jeśli obecne dane pozwalają je bezpiecznie połączyć." title="Powiązane faktury">
                <Table columns={invoiceColumns} data={detail.invoiceRows} emptyMessage="Brak faktur powiązanych z tym płatnikiem." getRowKey={(row) => row.id} />
              </Card>

              <Card description="Otwarte sprawy, które mogą dotyczyć płatnika, salda albo osób objętych rozliczeniem." title="Powiązane sprawy">
                <Table columns={workItemColumns} data={detail.workItemRows} emptyMessage="Brak otwartych spraw powiązanych z tym płatnikiem." getRowKey={(row) => row.id} />
              </Card>
            </div>

            <aside className="module-activity-panel" aria-label="Kontekst biznesowy płatnika">
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

              <Card title="Dane kontaktowe">
                <div className="billing-context-list">
                  <article>
                    <span>Kontakt</span>
                    <strong>{detail.contactLabel}</strong>
                  </article>
                  <article>
                    <span>Identyfikator płatności</span>
                    <strong>{detail.paymentIdentifierLabel}</strong>
                  </article>
                  <article>
                    <span>Saldo</span>
                    <strong>{detail.balanceLabel}</strong>
                  </article>
                </div>
              </Card>

              <Card className="module-quick-actions" title="Przejdź dalej">
                <Link className="module-quick-action" href={BILLING_CANONICAL_ROUTE}>
                  <span>Rozliczenia</span>
                  <CreditCard aria-hidden="true" size={15} />
                </Link>
                <Link className="module-quick-action" href="/faktury">
                  <span>Faktury</span>
                  <FileText aria-hidden="true" size={15} />
                </Link>
                <Link className="module-quick-action" href="/work-items">
                  <span>Sprawy</span>
                  <ListChecks aria-hidden="true" size={15} />
                </Link>
              </Card>
            </aside>
          </section>
        </>
      ) : null}
    </div>
  );
}
