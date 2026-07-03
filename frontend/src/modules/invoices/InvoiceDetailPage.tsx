"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import { AlertTriangle, ArrowLeft, FileText, RefreshCw, ShieldCheck } from "lucide-react";

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

import { invoiceApi } from "./api";
import { buildInvoiceDecisionActions } from "./decisionModel";
import type { InvoiceDetail } from "./types";
import {
  INVOICE_COMMENT_MAX_LENGTH,
  INVOICE_DETAIL_ORGANIZATION_REQUIRED_DESCRIPTION,
  INVOICE_DETAIL_ORGANIZATION_REQUIRED_TITLE,
  buildInvoiceCommentRequest,
  buildInvoiceCommentEvents,
  buildInvoiceDocumentTraceItems,
  buildInvoiceDetailFacts,
  buildInvoiceHistoryEvents,
  canUseInvoicesOrganizationScope,
  canRenderInvoiceDetailData,
  createInvoiceCommentSubmitter,
  getInvoiceDetailErrorState,
  getInvoiceDetailTitle,
  isInvoiceDetailEmpty,
  type InvoiceCommentErrorState,
  type InvoiceDetailErrorState,
  type InvoiceDetailEvent,
  type InvoiceDetailStatus,
  type InvoiceDetailTraceItem,
} from "./invoicesModel";

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

export function InvoiceDetailPage({ invoiceId: requestedInvoiceId }: { invoiceId: number }) {
  const { selectedOrganizationId, status: organizationStatus } = useActiveOrganization();
  const [detail, setDetail] = useState<InvoiceDetail | null>(null);
  const [status, setStatus] = useState<InvoiceDetailStatus>("idle");
  const [errorState, setErrorState] = useState<InvoiceDetailErrorState | null>(null);
  const [commentText, setCommentText] = useState("");
  const [commentSubmitting, setCommentSubmitting] = useState(false);
  const [commentErrorState, setCommentErrorState] = useState<InvoiceCommentErrorState | null>(null);
  const [commentSuccessMessage, setCommentSuccessMessage] = useState<string | null>(null);

  const loadDetail = useCallback(async () => {
    if (organizationStatus === "loading") {
      setStatus("loading");
      setErrorState(null);
      return;
    }

    if (!canUseInvoicesOrganizationScope(selectedOrganizationId)) {
      setDetail(null);
      setErrorState(null);
      setStatus("ready");
      return;
    }

    setStatus("loading");
    setErrorState(null);

    try {
      const nextDetail = await invoiceApi.detail(
        requestedInvoiceId,
        withActiveOrganizationQuery(selectedOrganizationId),
      );
      setDetail(nextDetail);
      setStatus("ready");
    } catch (nextError) {
      const nextErrorState = getInvoiceDetailErrorState(nextError);
      setDetail(null);
      setErrorState(nextErrorState);
      setStatus(nextErrorState.status);
    }
  }, [organizationStatus, requestedInvoiceId, selectedOrganizationId]);

  useEffect(() => {
    void loadDetail();
  }, [loadDetail]);

  const commentSubmitter = useMemo(
    () =>
      createInvoiceCommentSubmitter({
        refreshDetail: loadDetail,
        setSubmitting: setCommentSubmitting,
        submitComment: (payload) =>
          invoiceApi.addComment(
            requestedInvoiceId,
            payload,
            withActiveOrganizationQuery(selectedOrganizationId),
          ),
      }),
    [loadDetail, requestedInvoiceId, selectedOrganizationId],
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
  const historyEvents = useMemo(() => buildInvoiceHistoryEvents(detail), [detail]);
  const commentEvents = useMemo(() => buildInvoiceCommentEvents(detail), [detail]);
  const decisions = useMemo(() => (detail ? buildInvoiceDecisionActions(detail) : []), [detail]);
  const traceItems = useMemo(() => buildInvoiceDocumentTraceItems(detail), [detail]);
  const canShowDetail = canRenderInvoiceDetailData(status, detail);
  const organizationMissing = organizationStatus === "ready" && !canUseInvoicesOrganizationScope(selectedOrganizationId);
  const readyWithoutDetail = !organizationMissing && isInvoiceDetailEmpty(status, detail);

  return (
    <div className="module-page invoice-detail-page">
      <PageHeader
        badgeTone={status === "ready" ? "success" : status === "error" ? "danger" : "info"}
        description="Szczegoly faktury pobierane z /api/invoices/[id], bez zmiany kontraktu backendu."
        eyebrow={status === "ready" ? "Dane live" : "Faktura"}
        title={title}
        actions={
          <>
            <Link className="ui-button ui-button--secondary ui-button--sm" href="/faktury">
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
          description={INVOICE_DETAIL_ORGANIZATION_REQUIRED_DESCRIPTION}
          title={INVOICE_DETAIL_ORGANIZATION_REQUIRED_TITLE}
        />
      ) : null}
      {readyWithoutDetail ? (
        <EmptyState description="Backend nie zwrocil danych dla tej faktury." title="Brak faktury" />
      ) : null}

      {canShowDetail && detail && invoice ? (
        <section className="invoice-detail-grid">
          <div className="invoice-detail-grid__main">
            <Card
              action={<StatusBadge status={invoice.status === "weryfikacja" ? "warning" : "neutral"}>{invoice.status || "-"}</StatusBadge>}
              title="Dane faktury"
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
              action={detail.ksef_protected ? <Badge tone="info">KSeF protected</Badge> : <Badge>Local</Badge>}
              title="Workflow"
            >
              <div className="invoice-workflow-strip">
                <div>
                  <span>Stan workflow</span>
                  <strong>{detail.workflow?.state_label || invoice.workflow_state || "W pracy"}</strong>
                </div>
                <div>
                  <span>Duplikat</span>
                  <strong>{invoice.duplicate_type || "brak"}</strong>
                </div>
                <div>
                  <span>Komentarze</span>
                  <strong>{invoice.invoice_comment_count ?? detail.comments?.length ?? 0}</strong>
                </div>
              </div>
            </Card>

            <Card
              description="Dodaje tylko notatke operatora. Nie zmienia statusu, kwot, KSeF, OCR ani workflow faktury."
              title="Komentarz operatora"
            >
              <form className="invoice-comment-form" onSubmit={handleCommentSubmit}>
                <label className="invoice-comment-form__label" htmlFor="invoice-comment-note">
                  Tresc komentarza
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
                  placeholder="Np. Poproszono kontrahenta o doprecyzowanie numeru zamowienia."
                  rows={4}
                  value={commentText}
                />
                <div className="invoice-comment-form__meta">
                  <span>Limit: {INVOICE_COMMENT_MAX_LENGTH} znakow</span>
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
              description="Frontend pokazuje przewidywany model decyzji tylko informacyjnie. W przyszlosci backend musi ponownie sprawdzic uprawnienia, stan faktury i zapis decyzji."
              title="Dostepne decyzje"
            >
              <div className="module-readiness" aria-label="Model decyzji faktury">
                {decisions.map((decision) => (
                  <div className="module-readiness__item" key={decision.action}>
                    <AlertTriangle aria-hidden="true" size={17} />
                    <div>
                      <strong>{decision.label}</strong>
                      <span>{decision.reason}</span>
                      <span>{decision.futureEndpointLabel}</span>
                      <span>
                        Wymaga: {decision.requiresReason ? "powodu" : "bez powodu"}
                        {decision.requiresHandoffTarget ? ", celu przekazania" : ""}
                      </span>
                      <Button
                        disabled
                        size="sm"
                        variant={decision.availability === "blocked" ? "secondary" : "primary"}
                      >
                        Preview read-only
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            <Card
              description="Notatki operatorow sa oddzielone od historii systemowej. Dodanie komentarza nie zmienia statusu ani workflow faktury."
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
              description="Chronologiczny zapis zdarzen systemowych, importow i decyzji backendu."
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

          <aside className="module-activity-panel" aria-label="Slad faktury">
            <Card title="Slad dokumentu">
              <Table
                columns={traceColumns}
                data={traceItems}
                emptyMessage="Brak bezpiecznego sladu dokumentu."
                getRowKey={(row) => row.label}
              />
            </Card>
            <Card className="module-quick-actions" title="Powiazania">
              <Link className="module-quick-action" href="/dokumenty">
                <span>Dokumenty</span>
                <FileText aria-hidden="true" size={15} />
              </Link>
              <Link className="module-quick-action" href="/crm">
                <span>Kontrahent</span>
                <ShieldCheck aria-hidden="true" size={15} />
              </Link>
            </Card>
          </aside>
        </section>
      ) : null}
    </div>
  );
}
