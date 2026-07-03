"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import { ArrowLeft, Building2, MessageSquareText, RefreshCw, ShieldCheck } from "lucide-react";

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
  CONTRACTOR_DETAIL_ENDPOINT_PREFIX,
  CONTRACTOR_DETAIL_IMPORT_ENABLED,
  CONTRACTOR_DETAIL_ORGANIZATION_REQUIRED_DESCRIPTION,
  CONTRACTOR_DETAIL_ORGANIZATION_REQUIRED_TITLE,
  CONTRACTOR_DETAIL_PIPELINE_ENABLED,
  CONTRACTOR_DETAIL_READ_ONLY,
  CONTRACTOR_NOTE_MAX_LENGTH,
  buildContractorDetailFacts,
  buildContractorInvoiceRows,
  buildContractorNoteRequest,
  buildContractorNoteRows,
  buildContractorTaskRows,
  canRenderContractorDetail,
  canUseContractorDetailOrganizationScope,
  createContractorNoteSubmitter,
  getContractorDetailErrorState,
  getContractorDetailTitle,
  getContractorStatusTone,
  getContractorTypeLabel,
  isContractorDetailEmpty,
  readContractorDetail,
  type ContractorDetail,
  type ContractorDetailErrorState,
  type ContractorDetailStatus,
  type ContractorInvoiceRow,
  type ContractorNoteErrorState,
  type ContractorTaskRow,
} from "./contractorDetailModel";

const invoiceColumns: Array<TableColumn<ContractorInvoiceRow>> = [
  {
    key: "number",
    header: "Faktura",
    render: (row) => row.numberLabel,
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

const taskColumns: Array<TableColumn<ContractorTaskRow>> = [
  {
    key: "title",
    header: "Sprawa",
    render: (row) => row.titleLabel,
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
      const nextDetail = readContractorDetail(payload, requestedContractorId);
      setDetail(nextDetail);
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
  const notes = useMemo(() => (detail ? buildContractorNoteRows(detail) : []), [detail]);
  const title = getContractorDetailTitle(detail, requestedContractorId);
  const canShowDetail = canRenderContractorDetail(status, detail);
  const organizationMissing =
    organizationStatus === "ready" && !canUseContractorDetailOrganizationScope(selectedOrganizationId);
  const readyWithoutDetail = !organizationMissing && isContractorDetailEmpty(status, detail);

  return (
    <div className="module-page contractor-detail-page">
      <PageHeader
        badgeTone={status === "ready" ? "success" : status === "error" ? "danger" : "info"}
        description={`Read-only szczegol kontrahenta pobierany z ${CONTRACTOR_DETAIL_ENDPOINT_PREFIX}/{id}. Bez tworzenia, edycji, usuwania i automatyzacji CRM.`}
        eyebrow={status === "ready" ? "Dane live" : "CRM"}
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
        <EmptyState description="Backend nie zwrocil danych dla tego kontrahenta." title="Brak kontrahenta" />
      ) : null}

      {canShowDetail && detail ? (
        <section className="invoice-detail-grid contractor-detail-grid">
          <div className="invoice-detail-grid__main">
            <Card
              action={<StatusBadge status={getContractorStatusTone(detail.contractor)}>{facts[0]?.value ?? "Status"}</StatusBadge>}
              title="Dane kontrahenta"
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
              action={<Badge tone="info">Read-only</Badge>}
              description="Frontend pokazuje tylko bezpieczne pola biznesowe. Nie pokazuje debug payloadow, sekretow ani technicznych connection stringow."
              title="Bezpieczny podglad"
            >
              <div className="module-readiness">
                <div className="module-readiness__item">
                  <Building2 aria-hidden="true" size={17} />
                  <div>
                    <strong>{getContractorTypeLabel(detail.contractor)}</strong>
                    <span>{detail.safeNotes || "API nie zwrocilo notatki kontrahenta albo notatka zostala ukryta."}</span>
                  </div>
                </div>
                <div className="module-readiness__item">
                  <ShieldCheck aria-hidden="true" size={17} />
                  <div>
                    <strong>Tylko notatki CRM</strong>
                    <span>
                      Tworzenie: {CONTRACTOR_DETAIL_CREATE_ENABLED ? "wlaczone" : "wylaczone"} · Edycja:{" "}
                      {CONTRACTOR_DETAIL_EDIT_ENABLED ? "wlaczona" : "wylaczona"} · Pipeline:{" "}
                      {CONTRACTOR_DETAIL_PIPELINE_ENABLED ? "aktywny" : "nieaktywny"}
                    </span>
                  </div>
                </div>
              </div>
            </Card>

            <Card
              action={<Badge tone="success">Addytywne</Badge>}
              description="Dodaje tylko notatke operatora. Nie zmienia danych kontrahenta, faktur, rozliczen ani pipeline CRM."
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
                      <span>Dodaj pierwsza addytywna notatke operatora dla tego kontrahenta.</span>
                    </div>
                  </div>
                )}
              </div>
            </Card>

            <Card title="Powiazane faktury">
              <Table
                columns={invoiceColumns}
                data={invoices}
                emptyMessage="Backend nie zwrocil faktur powiazanych z kontrahentem."
                getRowKey={(row) => row.id}
              />
            </Card>

            <Card title="Powiazane sprawy">
              <Table
                columns={taskColumns}
                data={linkedTasks}
                emptyMessage="Brak otwartych spraw powiazanych z kontrahentem."
                getRowKey={(row) => row.id}
              />
            </Card>
          </div>

          <aside className="module-activity-panel" aria-label="Kontekst kontrahenta">
            <Card
              action={<Badge tone={CONTRACTOR_DETAIL_READ_ONLY ? "info" : "warning"}>Read-only</Badge>}
              title="Zakres tego widoku"
            >
              <ol className="module-activity-list">
                <li className="module-activity-list__item">
                  <span>Organizacja</span>
                  <strong>{detail.contractor.organization_name || selectedOrganizationId || "-"}</strong>
                  <p>organization_id jest wymagane przy pobieraniu szczegolu.</p>
                </li>
                <li className="module-activity-list__item">
                  <span>Faktury</span>
                  <strong>{invoices.length}</strong>
                  <p>Lista powiazan tylko do odczytu, bez zmian w module Faktury.</p>
                </li>
                <li className="module-activity-list__item">
                  <span>Sprawy</span>
                  <strong>{linkedTasks.length}</strong>
                  <p>Widoczne tylko otwarte sprawy zwrocone przez backend dla tego uzytkownika.</p>
                </li>
                <li className="module-activity-list__item">
                  <span>Blokady funkcji</span>
                  <strong>
                    {CONTRACTOR_DETAIL_DELETE_ENABLED || CONTRACTOR_DETAIL_IMPORT_ENABLED
                      ? "Akcje wlaczone"
                      : "Tylko notatki"}
                  </strong>
                  <p>Create, edit, delete, import, pipeline i automatyzacje sa poza zakresem.</p>
                </li>
              </ol>
            </Card>
          </aside>
        </section>
      ) : null}
    </div>
  );
}
