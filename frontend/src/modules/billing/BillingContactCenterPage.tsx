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
import { Table, type TableColumn } from "@/components/ui/Table";
import { useActiveOrganization } from "@/context/ActiveOrganizationContext";
import { withActiveOrganizationQuery } from "@/context/organizationContextModel";
import { api } from "@/lib/api";
import {
  BILLING_CANONICAL_ROUTE,
  BILLING_CONTACT_ACTION_OPTIONS,
  BILLING_CONTACT_CHANNEL_OPTIONS,
  BILLING_CONTACT_NO_SEND_HELP_TEXT,
  BILLING_OPERATIONAL_REPORT_ROUTE,
  BILLING_ORGANIZATION_REQUIRED_DESCRIPTION,
  BILLING_ORGANIZATION_REQUIRED_TITLE,
  BILLING_WORK_QUEUE_ROUTE,
  buildBillingContactCenterView,
  canUseBillingOrganizationScope,
  getBillingErrorState,
  readBillingContactEvents,
  type BillingContactAction,
  type BillingContactCenterRow,
  type BillingContactChannel,
  type BillingContactEventRecord,
  type BillingErrorState,
  type BillingStatus,
} from "./billingModel";

const contactColumns: Array<TableColumn<BillingContactCenterRow>> = [
  { key: "date", header: "Data", render: (row) => row.dateLabel },
  {
    key: "payer",
    header: "Płatnik",
    render: (row) => <Link className="module-link" href={row.payerHref}>{row.payerLabel}</Link>,
  },
  { key: "channel", header: "Kanał", render: (row) => row.channelLabel },
  { key: "action", header: "Typ wpisu", render: (row) => row.actionLabel },
  {
    key: "content",
    header: "Treść / notatka",
    render: (row) => (
      <span className="billing-family-cell">
        {row.messageExcerpt ? <span>{row.messageExcerpt}</span> : null}
        {row.noteExcerpt ? <span>{row.noteExcerpt}</span> : null}
        {!row.messageExcerpt && !row.noteExcerpt ? <span>Brak treści w danych.</span> : null}
      </span>
    ),
  },
  { key: "context", header: "Kontekst", render: (row) => row.contextLabel },
  {
    key: "links",
    header: "Dalej",
    render: (row) => (
      <span className="billing-inline-links">
        <Link className="module-link" href={row.payerHref}>Szczegół płatnika</Link>
        {row.paymentHref ? <Link className="module-link" href={row.paymentHref}>Szczegół wpłaty</Link> : null}
        <Link className="module-link" href={row.workQueueHref}>Sprawy rozliczeniowe</Link>
      </span>
    ),
  },
];

const attentionColumns: Array<TableColumn<BillingContactCenterRow>> = [
  {
    key: "payer",
    header: "Płatnik",
    render: (row) => <Link className="module-link" href={row.payerHref}>{row.payerLabel}</Link>,
  },
  { key: "channel", header: "Kanał", render: (row) => row.channelLabel },
  { key: "action", header: "Typ wpisu", render: (row) => row.actionLabel },
  { key: "reason", header: "Dlaczego sprawdzić", render: (row) => row.attentionReason },
  { key: "date", header: "Data", render: (row) => row.dateLabel },
  {
    key: "links",
    header: "Dalej",
    render: (row) => (
      <span className="billing-inline-links">
        <Link className="module-link" href={row.payerHref}>Szczegół płatnika</Link>
        {row.paymentHref ? <Link className="module-link" href={row.paymentHref}>Szczegół wpłaty</Link> : null}
        <Link className="module-link" href={BILLING_WORK_QUEUE_ROUTE}>Sprawy rozliczeniowe</Link>
      </span>
    ),
  },
];

function ContactListCard({
  title,
  description,
  rows,
  emptyMessage,
}: {
  title: string;
  description: string;
  rows: BillingContactCenterRow[];
  emptyMessage: string;
}) {
  return (
    <Card title={title} description={description}>
      <Table columns={contactColumns} data={rows} emptyMessage={emptyMessage} getRowKey={(row) => row.id} />
    </Card>
  );
}

export function BillingContactCenterPage() {
  const { selectedOrganizationId, selectedOrganization, status: organizationStatus } = useActiveOrganization();
  const [events, setEvents] = useState<BillingContactEventRecord[]>([]);
  const [loadedOrganizationId, setLoadedOrganizationId] = useState<string | null>(null);
  const [status, setStatus] = useState<BillingStatus>("idle");
  const [errorState, setErrorState] = useState<BillingErrorState | null>(null);
  const [channelFilter, setChannelFilter] = useState<BillingContactChannel | "all">("all");
  const [actionFilter, setActionFilter] = useState<BillingContactAction | "all">("all");
  const [payerQuery, setPayerQuery] = useState("");

  const activeOrganizationKey = canUseBillingOrganizationScope(selectedOrganizationId) ? String(selectedOrganizationId).trim() : null;

  const loadContacts = useCallback(async () => {
    if (organizationStatus === "loading") {
      setEvents([]);
      setLoadedOrganizationId(null);
      setErrorState(null);
      setStatus("loading");
      return;
    }

    if (!canUseBillingOrganizationScope(selectedOrganizationId)) {
      setEvents([]);
      setLoadedOrganizationId(null);
      setErrorState(null);
      setStatus("ready");
      return;
    }

    const organizationId = String(selectedOrganizationId).trim();
    setEvents([]);
    setLoadedOrganizationId(null);
    setStatus("loading");
    setErrorState(null);

    try {
      const payload = await api.billingContactEvents(withActiveOrganizationQuery(organizationId, { limit: 500 }));
      const contactEvents = readBillingContactEvents(payload);
      setEvents(contactEvents.events);
      setLoadedOrganizationId(organizationId);
      setStatus("ready");
    } catch (error) {
      const nextErrorState = getBillingErrorState(error);
      setEvents([]);
      setLoadedOrganizationId(null);
      setErrorState(nextErrorState);
      setStatus(nextErrorState.status);
    }
  }, [organizationStatus, selectedOrganizationId]);

  useEffect(() => {
    setEvents([]);
    setLoadedOrganizationId(null);
    void loadContacts();
  }, [loadContacts]);

  const snapshotMatchesOrganization = Boolean(activeOrganizationKey && loadedOrganizationId === activeOrganizationKey);
  const contactView = useMemo(
    () =>
      snapshotMatchesOrganization
        ? buildBillingContactCenterView(events, {
            channel: channelFilter,
            action: actionFilter,
            payerQuery,
          })
        : null,
    [actionFilter, channelFilter, events, payerQuery, snapshotMatchesOrganization],
  );
  const organizationMissing = organizationStatus === "ready" && !canUseBillingOrganizationScope(selectedOrganizationId);

  return (
    <div className="module-page billing-page billing-contact-center-page">
      <PageHeader
        badgeTone={status === "ready" ? "success" : status === "error" ? "warning" : "info"}
        description="Zobacz historię kontaktów z płatnikami i przygotowane wiadomości rozliczeniowe."
        eyebrow="Rozliczenia"
        title="Kontakty rozliczeniowe"
        actions={
          <div className="module-page-actions">
            <Link className="ui-button ui-button--secondary ui-button--sm" href={BILLING_CANONICAL_ROUTE}>
              <span className="ui-button__icon"><ArrowLeft size={15} /></span>
              <span>Wróć do rozliczeń</span>
            </Link>
            <Button disabled={status === "loading"} icon={<RefreshCw size={15} />} onClick={loadContacts} size="sm" variant="secondary">
              Odśwież
            </Button>
          </div>
        }
      />

      <Card title="Bezpieczny tryb kontaktów">
        <p className="module-note">Ten widok nie wysyła wiadomości i nie zmienia sald, wpłat ani naliczeń.</p>
        <p className="module-note">{BILLING_CONTACT_NO_SEND_HELP_TEXT}</p>
      </Card>

      {status === "loading" ? <LoadingState /> : null}
      {errorState ? <ErrorState description={errorState.description} title={errorState.title} /> : null}
      {organizationMissing ? <EmptyState description={BILLING_ORGANIZATION_REQUIRED_DESCRIPTION} title={BILLING_ORGANIZATION_REQUIRED_TITLE} /> : null}

      {status === "ready" && contactView && !organizationMissing ? (
        <>
          <div className="module-grid module-grid--three">
            <Card title="Wszystkie kontakty" description="Cała historia kontaktów rozliczeniowych w tej organizacji.">
              <strong>{contactView.summary.totalCount}</strong>
            </Card>
            <Card title="Przygotowane treści" description="Robocze wiadomości do ręcznego użycia poza CASI.">
              <strong>{contactView.summary.draftCount}</strong>
            </Card>
            <Card title="Deklaracje płatności" description="Deklaracje nie są wpłatą i nie zmieniają salda.">
              <strong>{contactView.summary.promisedPaymentCount}</strong>
            </Card>
            <Card title="Brak odpowiedzi" description="Kontakty, które mogą wymagać ponowienia.">
              <strong>{contactView.summary.noAnswerCount}</strong>
            </Card>
            <Card title="Wymaga ponownego kontaktu" description="Wpisy oznaczone jako wymagające ponowienia.">
              <strong>{contactView.summary.needsFollowupCount}</strong>
            </Card>
            <Card title="Ostatnie kontakty" description="Najświeższe wpisy widoczne na górze listy.">
              <strong>{contactView.summary.recentCount}</strong>
            </Card>
          </div>

          <Card title="Filtry" description="Filtry działają po stronie frontendu na już pobranej historii kontaktów.">
            <div className="module-filter-bar">
              <label className="module-filter">
                <span>Kanał</span>
                <select className="module-filter__select" onChange={(event) => setChannelFilter(event.target.value as BillingContactChannel | "all")} value={channelFilter}>
                  <option value="all">Wszystkie</option>
                  {BILLING_CONTACT_CHANNEL_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
              </label>
              <label className="module-filter">
                <span>Typ wpisu</span>
                <select className="module-filter__select" onChange={(event) => setActionFilter(event.target.value as BillingContactAction | "all")} value={actionFilter}>
                  <option value="all">Wszystkie</option>
                  {BILLING_CONTACT_ACTION_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
              </label>
              <label className="module-filter module-filter--grow">
                <span>Płatnik</span>
                <input
                  className="module-filter__input"
                  onChange={(event) => setPayerQuery(event.target.value)}
                  placeholder="Szukaj po nazwie płatnika"
                  type="search"
                  value={payerQuery}
                />
              </label>
            </div>
          </Card>

          {!contactView.summary.totalCount ? (
            <EmptyState title="Brak kontaktów rozliczeniowych" description="Brak kontaktów rozliczeniowych w aktualnych danych." />
          ) : null}

          <Card title="Najważniejsze do sprawdzenia" description="Kontakty, które mogą wymagać uwagi właściciela lub operatora rozliczeń.">
            <Table columns={attentionColumns} data={contactView.attentionRows} emptyMessage="Brak kontaktów wymagających dodatkowej uwagi." getRowKey={(row) => row.id} />
          </Card>

          <ContactListCard
            title="Historia kontaktów"
            description="Najnowsze kontakty są na górze. Wpisy nie oznaczają wysyłki wiadomości z CASI."
            rows={contactView.filteredRows}
            emptyMessage="Brak kontaktów pasujących do wybranych filtrów."
          />

          <ContactListCard
            title="Przygotowane treści"
            description="To są przygotowane treści. CASI Workspace nie wysłał tej wiadomości."
            rows={contactView.draftRows}
            emptyMessage="Brak przygotowanych treści w tej organizacji."
          />

          <ContactListCard
            title="Deklaracje płatności"
            description="Deklaracja płatności nie oznacza dodania wpłaty ani zmiany salda."
            rows={contactView.promisedPaymentRows}
            emptyMessage="Brak zapisanych deklaracji płatności."
          />

          <ContactListCard
            title="Brak odpowiedzi / ponowny kontakt"
            description="Lista kontaktów bez odpowiedzi albo oznaczonych jako wymagające ponowienia. Ten ekran nie tworzy przypomnień."
            rows={contactView.followupRows}
            emptyMessage="Brak wpisów typu brak odpowiedzi lub wymaga ponownego kontaktu."
          />

          <div className="module-grid module-grid--two">
            <Card className="module-quick-actions" title="Przejdź dalej">
              <Link className="module-quick-action" href={BILLING_CANONICAL_ROUTE}>Centrum rozliczeń</Link>
              <Link className="module-quick-action" href={BILLING_OPERATIONAL_REPORT_ROUTE}>Raport rozliczeniowy</Link>
              <Link className="module-quick-action" href={BILLING_WORK_QUEUE_ROUTE}>Sprawy rozliczeniowe</Link>
            </Card>
            <Card title="Kontekst biznesowy">
              <div className="module-context-list">
                {contactView.contextItems.map((item) => (
                  <article key={item.label}>
                    <span>{item.label}</span>
                    <p>{item.value}</p>
                  </article>
                ))}
                <article>
                  <span>Organizacja</span>
                  <p>{selectedOrganization?.name ?? "Wybrana organizacja"}</p>
                </article>
                <article>
                  <span>Gdzie zapisać kontakt</span>
                  <p>Nowy kontakt zapisuje się na szczególe płatnika. Ten ekran jest tylko centrum przeglądu.</p>
                </article>
              </div>
            </Card>
          </div>
        </>
      ) : null}
    </div>
  );
}
