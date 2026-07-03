"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import {
  ArrowLeft,
  Building2,
  FileText,
  ListChecks,
  MessageSquareText,
  RefreshCw,
  ShieldCheck,
} from "lucide-react";

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
import {
  CONTRACTOR_DETAIL_CREATE_ENABLED,
  CONTRACTOR_DETAIL_DELETE_ENABLED,
  CONTRACTOR_DETAIL_EDIT_ENABLED,
  CONTRACTOR_DETAIL_IMPORT_ENABLED,
  CONTRACTOR_DETAIL_ORGANIZATION_REQUIRED_DESCRIPTION,
  CONTRACTOR_DETAIL_ORGANIZATION_REQUIRED_TITLE,
  CONTRACTOR_DETAIL_PIPELINE_ENABLED,
  CONTRACTOR_DETAIL_READ_ONLY,
  CONTRACTOR_NOTE_MAX_LENGTH,
  buildContractorDetailFacts,
  buildContractorDocumentRows,
  buildContractorInvoiceRows,
  buildContractorNoteRequest,
  buildContractorNoteRows,
  buildContractorRelationshipSummary,
  buildContractorTaskRows,
  buildContractorWorkItemRows,
  canRenderContractorDetail,
  canUseContractorDetailOrganizationScope,
  createContractorNoteSubmitter,
  enrichContractorDetailWithWorkItems,
  getContractorDetailErrorState,
  getContractorDetailTitle,
  getContractorStatusTone,
  getContractorTypeLabel,
  isContractorDetailEmpty,
  readContractorDetail,
  type ContractorDetail,
  type ContractorDetailErrorState,
  type ContractorDetailStatus,
  type ContractorDocumentRow,
  type ContractorInvoiceRow,
  type ContractorNoteErrorState,
  type ContractorTaskRow,
  type ContractorWorkItemRow,
} from "./contractorDetailModel";
import { readWorkItems, type WorkItemRecord } from "../work-items/workItemsModel";

const invoiceColumns: Array<TableColumn<ContractorInvoiceRow>> = [
  {
    key: "number",
    header: "Faktura",
    render: (row) => (
      <Link className="module-link" href={row.href}>
        {row.numberLabel}
      </Link>
    ),
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
    key: "date",
    header: "Data",
    align: "right",
    render: (row) => row.dateLabel,
  },
];

const workItemColumns: Array<TableColumn<ContractorWorkItemRow>> = [
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
    key: "due",
    header: "Termin",
    align: "right",
    render: (row) => row.dueLabel,
  },
];

const taskColumns: Array<TableColumn<ContractorTaskRow>> = [
  {
    key: "title",
    header: "Zadanie",
    render: (row) =>
      row.href ? (
        <Link className="module-link" href={row.href}>
          {row.titleLabel}
        </Link>
      ) : (
        row.titleLabel
      ),
  },
  {
    key: "status",
    header: "Status",
    render: (row) => row.statusLabel,
  },
  {
    key: "due",
    header: "Termin",
    align: "right",
    render: (row) => row.dueLabel,
  },
];

const documentColumns: Array<TableColumn<ContractorDocumentRow>> = [
  {
    key: "title",
    header: "Dokument",
    render: (row) => (
      <Link className="module-link" href={row.href}>
        {row.titleLabel}
      </Link>
    ),
  },
  {
    key: "status",
    header: "Kontekst",
    render: (row) => row.statusLabel,
  },
  {
    key: "description",
    header: "Powiazanie",
    render: (row) => row.contextLabel,
  },
];

export function ContractorDetailPage({ contractorId: requestedContractorId }: { contractorId: number }) {
  const { selectedOrganizationId, status: organizationStatus } = useActiveOrganization();
  const [detail, setDetail] = useState<ContractorDetail | null>(null);
  const [status, setStatus] = useState<ContractorDetailStatus>("idle");
  const [errorState, setErrorState] = useState<ContractorDetailErrorState | null>(null);
  const [noteText, setNoteText] = useState("");
  const [noteSubmitting, setNoteSubmitting] = useState(false);
  const [noteErrorState, setNoteErrorState] = useState<ContractorNoteErrorState | null>(null);
  const [noteSuccessMessage, setNoteSuccessMessage] = useState<string | null>(null);

  const loadDetail = useCallback(async () => {
    if (organizationStatus === "loading") {
      setStatus("loading");
      setErrorState(null);
      return;
    }

    if (!canUseContractorDetailOrganizationScope(selectedOrganizationId)) {
      setDetail(null);
      setErrorState(null);
      setStatus("ready");
      return;
    }

    setStatus("loading");
    setErrorState(null);

    try {
      const payload = await api.contractorDetail(
        requestedContractorId,
        withActiveOrganizationQuery(selectedOrganizationId),
      );
      const baseDetail = readContractorDetail(payload, requestedContractorId);
      let workItems: WorkItemRecord[] = [];

      try {
        const workItemsPayload = await api.workItems(
          withActiveOrganizationQuery(selectedOrganizationId, { limit: 100, only_open: 1 }),
        );
        workItems = readWorkItems(workItemsPayload);
      } catch {
        workItems = [];
      }

      setDetail(enrichContractorDetailWithWorkItems(baseDetail, workItems));
      setStatus("ready");
    } catch (nextError) {
      const nextErrorState = getContractorDetailErrorState(nextError);
      setDetail(null);
      setErrorState(nextErrorState);
      setStatus(nextErrorState.status);
    }
  }, [organizationStatus, requestedContractorId, selectedOrganizationId]);

  useEffect(() => {
    void loadDetail();
  }, [loadDetail]);

  const noteSubmitter = useMemo(
    () =>
      createContractorNoteSubmitter({
        refreshDetail: loadDetail,
        setSubmitting: setNoteSubmitting,
        submitNote: (payload) =>
          api.addContractorNote(requestedContractorId, payload.note_text, selectedOrganizationId),
      }),
    [loadDetail, requestedContractorId, selectedOrganizationId],
  );

  const handleNoteSubmit = useCallback(
    async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();

      setNoteErrorState(null);
      setNoteSuccessMessage(null);

      const validation = buildContractorNoteRequest(noteText, selectedOrganizationId);
      const result = await noteSubmitter(validation);

      if (result.status === "success") {
        setNoteText("");
        setNoteSuccessMessage("Notatka CRM zostala dodana.");
        return;
      }

      if (result.status === "blocked") {
        setNoteErrorState({
          status: "error",
          title: "Nie mozna dodac notatki",
          description: result.message,
        });
        return;
      }

      if (result.status === "error") {
        setNoteErrorState(result.errorState);
      }
    },
    [noteSubmitter, noteText, selectedOrganizationId],
  );

  const facts = useMemo(() => (detail ? buildContractorDetailFacts(detail) : []), [detail]);
  const invoices = useMemo(() => (detail ? buildContractorInvoiceRows(detail) : []), [detail]);
  const linkedTasks = useMemo(() => (detail ? buildContractorTaskRows(detail) : []), [detail]);
  const workItems = useMemo(() => (detail ? buildContractorWorkItemRows(detail) : []), [detail]);
  const documents = useMemo(() => (detail ? buildContractorDocumentRows(detail) : []), [detail]);
  const notes = useMemo(() => (detail ? buildContractorNoteRows(detail) : []), [detail]);
  const summary = useMemo(() => (detail ? buildContractorRelationshipSummary(detail) : null), [detail]);
  const title = getContractorDetailTitle(detail, requestedContractorId);
  const canShowDetail = canRenderContractorDetail(status, detail);
  const organizationMissing =
    organizationStatus === "ready" && !canUseContractorDetailOrganizationScope(selectedOrganizationId);
  const readyWithoutDetail = !organizationMissing && isContractorDetailEmpty(status, detail);

  return (
    <div className="module-page contractor-detail-page">
      <PageHeader
        badgeTone={status === "ready" ? "success" : status === "error" ? "danger" : "info"}
        description="Relacja, faktury, sprawy, dokumenty i notatki w jednym miejscu. Dane kontrahenta pozostaja tylko do odczytu."
        eyebrow="Centrum kontrahenta"
        title={title}
        actions={
          <>
            <Link className="ui-button ui-button--secondary ui-button--sm" href="/crm">
              <ArrowLeft aria-hidden="true" size={15} />
              <span>Wroc</span>
            </Link>
            <Button disabled={status === "loading"} icon={<RefreshCw size={15} />} onClick={loadDetail} size="sm">
              Odswiez
            </Button>
          </>
        }
      />

      {status === "loading" ? <LoadingState /> : null}
      {errorState ? <ErrorState description={errorState.description} title={errorState.title} /> : null}
      {organizationMissing ? (
        <EmptyState
          description={CONTRACTOR_DETAIL_ORGANIZATION_REQUIRED_DESCRIPTION}
          title={CONTRACTOR_DETAIL_ORGANIZATION_REQUIRED_TITLE}
        />
      ) : null}
      {readyWithoutDetail ? (
        <EmptyState description="Nie znaleziono kontrahenta w wybranej organizacji." title="Brak kontrahenta" />
      ) : null}

      {canShowDetail && detail && summary ? (
        <section className="invoice-detail-grid contractor-detail-grid">
          <div className="invoice-detail-grid__main">
            <Card
              action={<StatusBadge status={getContractorStatusTone(detail.contractor)}>{facts[0]?.value ?? "Status"}</StatusBadge>}
              description="Najwazniejsze informacje potrzebne do oceny relacji z kontrahentem."
              title="Profil kontrahenta"
            >
              <div className="invoice-fact-grid">
                {facts.map((fact) => (
                  <article className="invoice-fact" key={fact.label}>
                    <span>{fact.label}</span>
                    <strong>{fact.value}</strong>
                  </article>
                ))}
              </div>
            </Card>

            <Card
              action={<Badge tone={CONTRACTOR_DETAIL_READ_ONLY ? "info" : "warning"}>Tylko do odczytu</Badge>}
              description="Szybki obraz tego, co dzieje sie wokol kontrahenta."
              title="Podsumowanie relacji"
            >
              <div className="invoice-fact-grid">
                <article className="invoice-fact">
                  <span>Otwarte sprawy</span>
                  <strong>{summary.activeWorkItemsLabel}</strong>
                </article>
                <article className="invoice-fact">
                  <span>Faktury</span>
                  <strong>{summary.invoicesLabel}</strong>
                </article>
                <article className="invoice-fact">
                  <span>Dokumenty</span>
                  <strong>{summary.documentsLabel}</strong>
                </article>
                <article className="invoice-fact">
                  <span>Notatki</span>
                  <strong>{summary.notesLabel}</strong>
                </article>
                <article className="invoice-fact">
                  <span>Ostatnia aktywnosc</span>
                  <strong>{summary.lastActivityLabel}</strong>
                </article>
                <article className="invoice-fact">
                  <span>Sygnał</span>
                  <strong>{summary.riskLabel}</strong>
                </article>
              </div>
            </Card>

            <Card
              action={<Badge tone={workItems.length ? "warning" : "neutral"}>{workItems.length} otwarte</Badge>}
              description="Sprawy operacyjne powiazane z kontrahentem."
              title="Sprawy do uwagi"
            >
              <Table
                columns={workItemColumns}
                data={workItems}
                emptyMessage="Nie ma otwartych spraw powiazanych z tym kontrahentem."
                getRowKey={(row) => row.id}
              />
            </Card>

            <Card
              description="Faktury powiazane z kontrahentem. Szczegoly otwieraja istniejacy modul Faktury."
              title="Faktury i rozliczenia"
            >
              <Table
                columns={invoiceColumns}
                data={invoices}
                emptyMessage="Brak faktur powiazanych z tym kontrahentem."
                getRowKey={(row) => row.id}
              />
            </Card>

            <Card
              description="Dokumenty widoczne przez powiazane sprawy. Jezeli brak danych, relacja nie zostala jeszcze opisana w sandboxie danych."
              title="Dokumenty"
            >
              <Table
                columns={documentColumns}
                data={documents}
                emptyMessage="Brak dokumentow powiazanych z tym kontrahentem."
                getRowKey={(row) => row.id}
              />
            </Card>

            <Card
              action={<Badge tone="success">Addytywne</Badge>}
              description="Notatka nie zmienia danych kontrahenta, faktur ani rozliczen. Zapis jest potwierdzany przez backend."
              title="Notatki CRM"
            >
              <form className="invoice-comment-form" onSubmit={handleNoteSubmit}>
                <label className="invoice-comment-form__label" htmlFor="contractor-note-text">
                  Tresc notatki
                </label>
                <textarea
                  className="invoice-comment-form__textarea"
                  disabled={noteSubmitting}
                  id="contractor-note-text"
                  maxLength={CONTRACTOR_NOTE_MAX_LENGTH}
                  onChange={(event) => {
                    setNoteText(event.target.value);
                    if (noteErrorState) {
                      setNoteErrorState(null);
                    }
                    if (noteSuccessMessage) {
                      setNoteSuccessMessage(null);
                    }
                  }}
                  placeholder="Np. Kontrahent preferuje kontakt mailowy w sprawach rozliczeniowych."
                  rows={4}
                  value={noteText}
                />
                <div className="invoice-comment-form__meta">
                  <span>Limit: {CONTRACTOR_NOTE_MAX_LENGTH} znakow</span>
                  <span>{noteText.trim().length}/{CONTRACTOR_NOTE_MAX_LENGTH}</span>
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
                  {noteSubmitting ? "Dodawanie..." : "Dodaj notatke"}
                </Button>
              </form>

              <div className="module-readiness" aria-label="Notatki CRM kontrahenta">
                {notes.length ? (
                  notes.map((note) => (
                    <div className="module-readiness__item" key={note.id}>
                      <MessageSquareText aria-hidden="true" size={17} />
                      <div>
                        <strong>{note.authorLabel}</strong>
                        <span>{note.dateLabel}</span>
                        <p>{note.noteText}</p>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="module-readiness__item">
                    <MessageSquareText aria-hidden="true" size={17} />
                    <div>
                      <strong>Brak notatek CRM</strong>
                      <span>Mozesz dodac pierwsza notatke operatora dla tego kontrahenta.</span>
                    </div>
                  </div>
                )}
              </div>
            </Card>

            <Card
              description="Zadania z istniejacego modulu Asystenta Szefa powiazane z kontrahentem."
              title="Zadania i przypomnienia"
            >
              <Table
                columns={taskColumns}
                data={linkedTasks}
                emptyMessage="Brak otwartych zadan powiazanych z tym kontrahentem."
                getRowKey={(row) => row.id}
              />
            </Card>
          </div>

          <aside className="module-activity-panel" aria-label="Kontekst kontrahenta">
            <Card title="Kontekst biznesowy">
              <div className="module-readiness">
                <div className="module-readiness__item">
                  <Building2 aria-hidden="true" size={17} />
                  <div>
                    <strong>{getContractorTypeLabel(detail.contractor)}</strong>
                    <span>{detail.safeNotes || "Brak dodatkowego opisu relacji."}</span>
                  </div>
                </div>
                <div className="module-readiness__item">
                  <ListChecks aria-hidden="true" size={17} />
                  <div>
                    <strong>{summary.riskLabel}</strong>
                    <span>Najkrotszy sygnal, czy kontrahent wymaga dzis uwagi.</span>
                  </div>
                </div>
                <div className="module-readiness__item">
                  <FileText aria-hidden="true" size={17} />
                  <div>
                    <strong>{summary.documentsLabel}</strong>
                    <span>Dokumenty sa pokazywane tylko wtedy, gdy wynikaja z istniejacych powiazan.</span>
                  </div>
                </div>
                <div className="module-readiness__item">
                  <ShieldCheck aria-hidden="true" size={17} />
                  <div>
                    <strong>Dane kontrahenta bez edycji</strong>
                    <span>
                      Tworzenie: {CONTRACTOR_DETAIL_CREATE_ENABLED ? "wlaczone" : "wylaczone"} - Edycja:{" "}
                      {CONTRACTOR_DETAIL_EDIT_ENABLED ? "wlaczona" : "wylaczona"} - Import:{" "}
                      {CONTRACTOR_DETAIL_IMPORT_ENABLED ? "wlaczony" : "wylaczony"} - Pipeline:{" "}
                      {CONTRACTOR_DETAIL_PIPELINE_ENABLED ? "aktywny" : "nieaktywny"} - Usuwanie:{" "}
                      {CONTRACTOR_DETAIL_DELETE_ENABLED ? "wlaczone" : "wylaczone"}
                    </span>
                  </div>
                </div>
              </div>
            </Card>
          </aside>
        </section>
      ) : null}
    </div>
  );
}
