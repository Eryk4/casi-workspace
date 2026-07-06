"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import { ArrowLeft, Building2, FileText, ListChecks, MessageSquareText, RefreshCw, ShieldCheck } from "lucide-react";

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

import { invoiceApi } from "./api";
import type { InvoiceDetail } from "./types";
import {
  INVOICE_COMMENT_MAX_LENGTH,
  INVOICE_DETAIL_ORGANIZATION_REQUIRED_DESCRIPTION,
  INVOICE_DETAIL_ORGANIZATION_REQUIRED_TITLE,
  buildInvoiceBusinessSignals,
  buildInvoiceCenterSummary,
  buildInvoiceCommentRequest,
  buildInvoiceCommentEvents,
  buildInvoiceContractorContext,
  buildInvoiceDocumentTraceItems,
  buildInvoiceDetailFacts,
  buildInvoiceHistoryEvents,
  buildInvoiceRelatedDocumentRows,
  buildInvoiceRelatedTaskRows,
  buildInvoiceRelatedWorkItemRows,
  canUseInvoicesOrganizationScope,
  canRenderInvoiceDetailData,
  createInvoiceCommentSubmitter,
  getInvoiceDetailErrorState,
  getInvoiceDetailTitle,
  isInvoiceDetailEmpty,
  type InvoiceCommentErrorState,
  type InvoiceContractorContext,
  type InvoiceDetailErrorState,
  type InvoiceDetailEvent,
  type InvoiceDetailStatus,
  type InvoiceDetailTraceItem,
  type InvoiceRelatedDocumentRow,
  type InvoiceRelatedTaskRow,
  type InvoiceRelatedWorkItemRow,
} from "./invoicesModel";
import { readWorkItems, type WorkItemRecord } from "../work-items/workItemsModel";

const eventColumns: Array<TableColumn<InvoiceDetailEvent>> = [
  {
    key: "type",
    header: "Zdarzenie",
    render: (row) => row.type,
  },
  {
    key: "actor",
    header: "Aktor",
    render: (row) => row.actor,
  },
  {
    key: "date",
    header: "Data",
    render: (row) => row.date,
  },
  {
    key: "description",
    header: "Opis",
    render: (row) => row.description,
  },
];

const traceColumns: Array<TableColumn<InvoiceDetailTraceItem>> = [
  {
    key: "label",
    header: "Obszar",
    render: (row) => row.label,
  },
  {
    key: "value",
    header: "Status",
    render: (row) => row.value,
  },
  {
    key: "description",
    header: "Opis",
    render: (row) => row.description,
  },
];

const workItemColumns: Array<TableColumn<InvoiceRelatedWorkItemRow>> = [
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

const taskColumns: Array<TableColumn<InvoiceRelatedTaskRow>> = [
  {
    key: "title",
    header: "Zadanie",
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
    key: "due",
    header: "Termin",
    align: "right",
    render: (row) => row.dueLabel,
  },
];

const documentColumns: Array<TableColumn<InvoiceRelatedDocumentRow>> = [
  {
    key: "title",
    header: "Dokument",
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
    key: "context",
    header: "Kontekst",
    render: (row) => row.contextLabel,
  },
];

export function InvoiceDetailPage({ invoiceId: requestedInvoiceId }: { invoiceId: number }) {
  const { selectedOrganizationId, status: organizationStatus } = useActiveOrganization();
  const [detail, setDetail] = useState<InvoiceDetail | null>(null);
  const [workItems, setWorkItems] = useState<WorkItemRecord[]>([]);
  const [status, setStatus] = useState<InvoiceDetailStatus>("idle");
  const [errorState, setErrorState] = useState<InvoiceDetailErrorState | null>(null);
  const [commentText, setCommentText] = useState("");
  const [commentSubmitting, setCommentSubmitting] = useState(false);
  const [commentErrorState, setCommentErrorState] = useState<InvoiceCommentErrorState | null>(null);
  const [commentSuccessMessage, setCommentSuccessMessage] = useState<string | null>(null);
  const loadRequestIdRef = useRef(0);

  const loadDetail = useCallback(async () => {
    const requestId = loadRequestIdRef.current + 1;
    loadRequestIdRef.current = requestId;

    if (organizationStatus === "loading") {
      setStatus("loading");
      setErrorState(null);
      return;
    }

    if (!canUseInvoicesOrganizationScope(selectedOrganizationId)) {
      setDetail(null);
      setWorkItems([]);
      setErrorState(null);
      setStatus("ready");
      return;
    }

    setStatus("loading");
    setErrorState(null);

    try {
      const [nextDetail, workItemsPayload] = await Promise.all([
        invoiceApi.detail(
          requestedInvoiceId,
          withActiveOrganizationQuery(selectedOrganizationId),
        ),
        api.workItems(withActiveOrganizationQuery(selectedOrganizationId, { limit: 100 })),
      ]);
      const nextWorkItems = readWorkItems(workItemsPayload);
      if (loadRequestIdRef.current !== requestId) {
        return;
      }
      setDetail(nextDetail);
      setWorkItems(nextWorkItems);
      setErrorState(null);
      setStatus("ready");
    } catch (nextError) {
      if (loadRequestIdRef.current !== requestId) {
        return;
      }
      const nextErrorState = getInvoiceDetailErrorState(nextError);
      setDetail(null);
      setWorkItems([]);
      setErrorState(nextErrorState);
      setStatus(nextErrorState.status);
    }
  }, [organizationStatus, requestedInvoiceId, selectedOrganizationId]);

  useEffect(() => {
    void loadDetail();
  }, [loadDetail]);

  const refreshDetail = useCallback(async () => {
    if (!canUseInvoicesOrganizationScope(selectedOrganizationId)) {
      return;
    }

    const nextDetail = await invoiceApi.detail(
        requestedInvoiceId,
        withActiveOrganizationQuery(selectedOrganizationId),
      );
    setDetail(nextDetail);
  }, [requestedInvoiceId, selectedOrganizationId]);

  const commentSubmitter = useMemo(
    () =>
      createInvoiceCommentSubmitter({
        refreshDetail,
        setSubmitting: setCommentSubmitting,
        submitComment: (payload) =>
          invoiceApi.addComment(
            requestedInvoiceId,
            payload,
            withActiveOrganizationQuery(selectedOrganizationId),
          ),
      }),
    [refreshDetail, requestedInvoiceId, selectedOrganizationId],
  );

  const handleCommentSubmit = useCallback(
    async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();

      setCommentErrorState(null);
      setCommentSuccessMessage(null);

      const validation = buildInvoiceCommentRequest(commentText, selectedOrganizationId);
      const result = await commentSubmitter(validation);

      if (result.status === "success") {
        setCommentText("");
        setCommentSuccessMessage("Komentarz zostal dodany.");
        return;
      }

      if (result.status === "blocked") {
        setCommentErrorState({
          status: "error",
          title: "Nie mozna dodac komentarza",
          description: result.message,
        });
        return;
      }

      if (result.status === "error") {
        setCommentErrorState(result.errorState);
      }
    },
    [commentSubmitter, commentText, selectedOrganizationId],
  );

  const invoice = detail?.invoice;
  const title = getInvoiceDetailTitle(detail, requestedInvoiceId);
  const facts = useMemo(() => (invoice ? buildInvoiceDetailFacts(invoice) : []), [invoice]);
  const summary = useMemo(() => (detail ? buildInvoiceCenterSummary(detail) : null), [detail]);
  const contractorContext = useMemo(() => (detail ? buildInvoiceContractorContext(detail) : null), [detail]);
  const businessSignals = useMemo(() => (detail ? buildInvoiceBusinessSignals(detail) : []), [detail]);
  const historyEvents = useMemo(() => buildInvoiceHistoryEvents(detail), [detail]);
  const commentEvents = useMemo(() => buildInvoiceCommentEvents(detail), [detail]);
  const traceItems = useMemo(() => buildInvoiceDocumentTraceItems(detail), [detail]);
  const relatedWorkItems = useMemo(
    () => (detail ? buildInvoiceRelatedWorkItemRows(detail, workItems) : []),
    [detail, workItems],
  );
  const relatedTasks = useMemo(() => (detail ? buildInvoiceRelatedTaskRows(detail) : []), [detail]);
  const relatedDocuments = useMemo(() => (detail ? buildInvoiceRelatedDocumentRows(detail) : []), [detail]);
  const canShowDetail = canRenderInvoiceDetailData(status, detail);
  const organizationMissing = organizationStatus === "ready" && !canUseInvoicesOrganizationScope(selectedOrganizationId);
  const readyWithoutDetail = !organizationMissing && isInvoiceDetailEmpty(status, detail);

  return (
    <div className="module-page invoice-detail-page">
      <PageHeader
        badgeTone={status === "ready" ? "success" : status === "error" ? "danger" : "info"}
        description="Jedno miejsce do zrozumienia faktury, kontrahenta, dokumentów i spraw powiązanych z tym kosztem."
        eyebrow={status === "ready" ? "Centrum faktury" : "Faktura"}
        title={title}
        actions={
          <>
            <Link className="ui-button ui-button--secondary ui-button--sm" href="/faktury">
              <ArrowLeft aria-hidden="true" size={15} />
              <span>Wróć</span>
            </Link>
            <Button disabled={status === "loading"} icon={<RefreshCw size={15} />} onClick={loadDetail} size="sm">
              Odśwież
            </Button>
          </>
        }
      />

      {status === "loading" ? <LoadingState /> : null}
      {errorState ? <ErrorState description={errorState.description} title={errorState.title} /> : null}
      {organizationMissing ? (
        <EmptyState
          description={INVOICE_DETAIL_ORGANIZATION_REQUIRED_DESCRIPTION}
          title={INVOICE_DETAIL_ORGANIZATION_REQUIRED_TITLE}
        />
      ) : null}
      {readyWithoutDetail ? (
        <EmptyState description="Backend nie zwrocil danych dla tej faktury." title="Brak faktury" />
      ) : null}

      {canShowDetail && detail && invoice && summary && contractorContext ? (
        <section className="invoice-detail-grid">
          <div className="invoice-detail-grid__main">
            <Card
              action={<StatusBadge status={invoice.status === "weryfikacja" ? "warning" : "neutral"}>{invoice.status || "-"}</StatusBadge>}
              description={summary.reasonLabel}
              title="Profil faktury"
            >
              <div className="invoice-center-summary" aria-label="Podsumowanie faktury">
                <div>
                  <span>Co wymaga uwagi</span>
                  <strong>{summary.decisionLabel}</strong>
                </div>
                <div>
                  <span>Kontrahent</span>
                  <strong>{summary.contractorLabel}</strong>
                </div>
                <div>
                  <span>Kwota</span>
                  <strong>{summary.amountLabel}</strong>
                </div>
              </div>
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
              action={detail.ksef_protected ? <Badge tone="info">KSeF</Badge> : <Badge>Źródło lokalne</Badge>}
              description="Ta sekcja wyjaśnia stan faktury bez wykonywania decyzji workflow."
              title="Podsumowanie relacji"
            >
              <div className="invoice-workflow-strip">
                <div>
                  <span>Stan workflow</span>
                  <strong>{detail.workflow?.state_label || invoice.workflow_state || "W pracy"}</strong>
                </div>
                <div>
                  <span>Ryzyko duplikatu</span>
                  <strong>{invoice.duplicate_type || "brak"}</strong>
                </div>
                <div>
                  <span>Komentarze</span>
                  <strong>{invoice.invoice_comment_count ?? detail.comments?.length ?? 0}</strong>
                </div>
              </div>
            </Card>

            <Card
              description="Kontrahent powiązany z fakturą. Dane są tylko do odczytu; przejście prowadzi do Centrum kontrahenta."
              title="Kontrahent"
            >
              <InvoiceContractorCard contractor={contractorContext} />
            </Card>

            <Card
              description="Sprawy operacyjne powiązane z tą fakturą. Link prowadzi do read-only Karty sprawy."
              title="Sprawy do uwagi"
            >
              <Table
                columns={workItemColumns}
                data={relatedWorkItems}
                emptyMessage="Brak otwartych spraw powiązanych z tą fakturą."
                getRowKey={(row) => row.id}
              />
            </Card>

            <Card
              description="Zadania z modułu Asystenta Szefa powiązane z fakturą, jeśli backend zwrócił takie relacje."
              title="Zadania i kontekst operacyjny"
            >
              <Table
                columns={taskColumns}
                data={relatedTasks}
                emptyMessage="Brak zadań powiązanych z tą fakturą."
                getRowKey={(row) => row.id}
              />
            </Card>

            <Card
              description="Dokumenty i ślady wejściowe pokazane bez lokalnych ścieżek, storage key ani publicznych linków do plików."
              title="Dokumenty"
            >
              <Table
                columns={documentColumns}
                data={relatedDocuments}
                emptyMessage="Brak bezpiecznie powiązanych dokumentów dla tej faktury."
                getRowKey={(row) => row.id}
              />
            </Card>

            <Card
              description="Dodaje tylko notatkę operatora. Nie zmienia statusu, kwot, KSeF, OCR ani workflow faktury."
              title="Komentarz operatora"
            >
              <form className="invoice-comment-form" onSubmit={handleCommentSubmit}>
                <label className="invoice-comment-form__label" htmlFor="invoice-comment-note">
                  Treść komentarza
                </label>
                <textarea
                  className="invoice-comment-form__textarea"
                  disabled={commentSubmitting}
                  id="invoice-comment-note"
                  maxLength={INVOICE_COMMENT_MAX_LENGTH}
                  onChange={(event) => {
                    setCommentText(event.target.value);
                    if (commentErrorState) {
                      setCommentErrorState(null);
                    }
                    if (commentSuccessMessage) {
                      setCommentSuccessMessage(null);
                    }
                  }}
                  placeholder="Np. Poproszono kontrahenta o doprecyzowanie numeru zamówienia."
                  rows={4}
                  value={commentText}
                />
                <div className="invoice-comment-form__meta">
                  <span>Limit: {INVOICE_COMMENT_MAX_LENGTH} znaków</span>
                  <span>{commentText.trim().length}/{INVOICE_COMMENT_MAX_LENGTH}</span>
                </div>
                {commentErrorState ? (
                  <div className="invoice-comment-form__message invoice-comment-form__message--error" role="alert">
                    <strong>{commentErrorState.title}</strong>
                    <span>{commentErrorState.description}</span>
                  </div>
                ) : null}
                {commentSuccessMessage ? (
                  <div className="invoice-comment-form__message invoice-comment-form__message--success" role="status">
                    {commentSuccessMessage}
                  </div>
                ) : null}
                <Button disabled={commentSubmitting || !commentText.trim()} size="sm" type="submit">
                  {commentSubmitting ? "Dodawanie..." : "Dodaj komentarz"}
                </Button>
              </form>
            </Card>

            <Card
              description="Notatki operatorów są oddzielone od historii systemowej. Dodanie komentarza nie zmienia statusu ani workflow faktury."
              id="invoice-comments"
              title="Komentarze operatora"
            >
              <Table
                columns={eventColumns}
                data={commentEvents}
                emptyMessage="Brak komentarzy operatora dla tej faktury."
                getRowKey={(row) => row.id}
              />
            </Card>

            <Card
              description="Chronologiczny zapis zdarzeń systemowych. Treści komentarzy i techniczne szczegóły nie są tu ujawniane."
              title="Historia systemowa"
            >
              <Table
                columns={eventColumns}
                data={historyEvents}
                emptyMessage="Brak historii systemowej dla tej faktury."
                getRowKey={(row) => row.id}
              />
            </Card>
          </div>

          <aside className="module-activity-panel" aria-label="Kontekst faktury">
            <Card title="Kontekst biznesowy">
              <div className="invoice-business-signals">
                {businessSignals.map((signal) => (
                  <article className={`invoice-business-signal invoice-business-signal--${signal.tone}`} key={signal.id}>
                    <span>{signal.label}</span>
                    <strong>{signal.value}</strong>
                  </article>
                ))}
              </div>
            </Card>
            <Card title="Ślad dokumentu">
              <Table
                columns={traceColumns}
                data={traceItems}
                emptyMessage="Brak bezpiecznego śladu dokumentu."
                getRowKey={(row) => row.label}
              />
            </Card>
            <Card className="module-quick-actions" title="Powiązania">
              <Link className="module-quick-action" href={contractorContext.href ?? "/crm"}>
                <span>Kontrahent</span>
                <Building2 aria-hidden="true" size={15} />
              </Link>
              <Link className="module-quick-action" href="/work-items">
                <span>Sprawy</span>
                <ListChecks aria-hidden="true" size={15} />
              </Link>
              <Link className="module-quick-action" href="/dokumenty">
                <span>Dokumenty</span>
                <FileText aria-hidden="true" size={15} />
              </Link>
              <Link className="module-quick-action" href="#invoice-comments">
                <span>Komentarze</span>
                <MessageSquareText aria-hidden="true" size={15} />
              </Link>
            </Card>
          </aside>
        </section>
      ) : null}
    </div>
  );
}

function InvoiceContractorCard({ contractor }: { contractor: InvoiceContractorContext }) {
  return (
    <div className="invoice-contractor-card">
      <div>
        <span>Nazwa</span>
        <strong>{contractor.nameLabel}</strong>
      </div>
      <div>
        <span>NIP</span>
        <strong>{contractor.nipLabel}</strong>
      </div>
      <div>
        <span>Kontakt</span>
        <strong>{contractor.contactLabel}</strong>
      </div>
      <div>
        <span>Relacja</span>
        <strong>{contractor.typeLabel}</strong>
      </div>
      <div className="invoice-contractor-card__wide">
        <span>Historia</span>
        <strong>{contractor.knownBeforeLabel}</strong>
      </div>
      {contractor.href ? (
        <Link className="ui-button ui-button--secondary ui-button--sm invoice-contractor-card__link" href={contractor.href}>
          <ShieldCheck aria-hidden="true" size={15} />
          <span>Otwórz Centrum kontrahenta</span>
        </Link>
      ) : null}
    </div>
  );
}
