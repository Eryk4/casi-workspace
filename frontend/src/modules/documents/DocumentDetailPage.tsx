"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ArrowLeft, FileText, Link2, MessageSquareText, RefreshCw } from "lucide-react";

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
  DOCUMENT_DETAIL_ORGANIZATION_REQUIRED_DESCRIPTION,
  DOCUMENT_DETAIL_ORGANIZATION_REQUIRED_TITLE,
  DOCUMENT_DETAIL_READ_ONLY,
  buildDocumentAuditRows,
  buildDocumentCenterSummary,
  buildDocumentCommentRows,
  buildDocumentDetailFacts,
  buildDocumentRelatedContractorRows,
  buildDocumentRelatedInvoiceRows,
  buildDocumentRelatedWorkItemRows,
  buildDocumentSourceTraceItems,
  buildDocumentVersionRows,
  canRenderDocumentDetail,
  canUseDocumentDetailOrganizationScope,
  getDocumentDetailErrorState,
  getDocumentDetailTitle,
  getDocumentStatusTone,
  getDocumentWorkflowTone,
  isDocumentDetailEmpty,
  readKnowledgeDocumentDetail,
  type DocumentAuditRow,
  type DocumentCommentRow,
  type DocumentDetailErrorState,
  type DocumentDetailStatus,
  type DocumentRelatedContractorRow,
  type DocumentRelatedInvoiceRow,
  type DocumentRelatedWorkItemRow,
  type DocumentSourceTraceItem,
  type DocumentVersionRow,
  type KnowledgeDocumentDetail,
} from "./documentDetailModel";
import { readWorkItems, type WorkItemRecord } from "../work-items/workItemsModel";

const versionColumns: Array<TableColumn<DocumentVersionRow>> = [
  { key: "version", header: "Wersja", render: (row) => row.versionLabel },
  { key: "file", header: "Plik", render: (row) => row.fileLabel },
  { key: "status", header: "Status", render: (row) => row.statusLabel },
  { key: "official", header: "Typ", render: (row) => row.officialLabel },
  { key: "storage", header: "Ślad", render: (row) => row.storageLabel },
  { key: "created", header: "Utworzono", align: "right", render: (row) => row.createdLabel },
];

const auditColumns: Array<TableColumn<DocumentAuditRow>> = [
  { key: "action", header: "Zdarzenie", render: (row) => row.actionLabel },
  { key: "actor", header: "Aktor", render: (row) => row.actorLabel },
  { key: "date", header: "Data", align: "right", render: (row) => row.dateLabel },
  { key: "description", header: "Opis", render: (row) => row.descriptionLabel },
];

const traceColumns: Array<TableColumn<DocumentSourceTraceItem>> = [
  { key: "label", header: "Obszar", render: (row) => row.label },
  { key: "value", header: "Stan", render: (row) => row.value },
  { key: "description", header: "Opis", render: (row) => row.description },
];

const workItemColumns: Array<TableColumn<DocumentRelatedWorkItemRow>> = [
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
  { key: "due", header: "Termin", align: "right", render: (row) => row.dueLabel },
];

const invoiceColumns: Array<TableColumn<DocumentRelatedInvoiceRow>> = [
  {
    key: "number",
    header: "Faktura",
    render: (row) => (
      <Link className="module-link" href={row.href}>
        {row.numberLabel}
      </Link>
    ),
  },
  { key: "contractor", header: "Kontrahent", render: (row) => row.contractorLabel },
  { key: "amount", header: "Kwota", render: (row) => row.amountLabel },
  { key: "status", header: "Status", render: (row) => row.statusLabel },
];

const contractorColumns: Array<TableColumn<DocumentRelatedContractorRow>> = [
  {
    key: "name",
    header: "Kontrahent",
    render: (row) => (
      <Link className="module-link" href={row.href}>
        {row.nameLabel}
      </Link>
    ),
  },
  { key: "context", header: "Kontekst", render: (row) => row.contextLabel },
];

const commentColumns: Array<TableColumn<DocumentCommentRow>> = [
  { key: "author", header: "Autor", render: (row) => row.authorLabel },
  { key: "target", header: "Zakres", render: (row) => row.targetLabel },
  { key: "date", header: "Data", render: (row) => row.dateLabel },
  { key: "note", header: "Komentarz", render: (row) => row.noteLabel },
];

export function DocumentDetailPage({ documentId: requestedDocumentId }: { documentId: number }) {
  const { selectedOrganizationId, status: organizationStatus } = useActiveOrganization();
  const [detail, setDetail] = useState<KnowledgeDocumentDetail | null>(null);
  const [workItems, setWorkItems] = useState<WorkItemRecord[]>([]);
  const [status, setStatus] = useState<DocumentDetailStatus>("idle");
  const [errorState, setErrorState] = useState<DocumentDetailErrorState | null>(null);
  const loadRequestIdRef = useRef(0);

  const loadDetail = useCallback(async () => {
    const requestId = loadRequestIdRef.current + 1;
    loadRequestIdRef.current = requestId;

    if (organizationStatus === "loading") {
      setStatus("loading");
      setErrorState(null);
      return;
    }

    if (!canUseDocumentDetailOrganizationScope(selectedOrganizationId)) {
      setDetail(null);
      setWorkItems([]);
      setErrorState(null);
      setStatus("ready");
      return;
    }

    setStatus("loading");
    setErrorState(null);

    try {
      const [payload, workItemsPayload] = await Promise.all([
        api.knowledgeDocumentDetail(requestedDocumentId, withActiveOrganizationQuery(selectedOrganizationId)),
        api.workItems(withActiveOrganizationQuery(selectedOrganizationId, { limit: 100 })).catch(() => ({ items: [] })),
      ]);

      if (loadRequestIdRef.current !== requestId) {
        return;
      }

      setDetail(readKnowledgeDocumentDetail(payload, requestedDocumentId));
      setWorkItems(readWorkItems(workItemsPayload));
      setErrorState(null);
      setStatus("ready");
    } catch (nextError) {
      if (loadRequestIdRef.current !== requestId) {
        return;
      }

      const nextErrorState = getDocumentDetailErrorState(nextError);
      setDetail(null);
      setWorkItems([]);
      setErrorState(nextErrorState);
      setStatus(nextErrorState.status);
    }
  }, [organizationStatus, requestedDocumentId, selectedOrganizationId]);

  useEffect(() => {
    void loadDetail();
  }, [loadDetail]);

  const facts = useMemo(() => (detail ? buildDocumentDetailFacts(detail) : []), [detail]);
  const summary = useMemo(() => (detail ? buildDocumentCenterSummary(detail, workItems) : null), [detail, workItems]);
  const traceItems = useMemo(() => (detail ? buildDocumentSourceTraceItems(detail) : []), [detail]);
  const relatedWorkItems = useMemo(() => (detail ? buildDocumentRelatedWorkItemRows(detail, workItems) : []), [detail, workItems]);
  const relatedInvoices = useMemo(() => (detail ? buildDocumentRelatedInvoiceRows(detail, workItems) : []), [detail, workItems]);
  const relatedContractors = useMemo(() => (detail ? buildDocumentRelatedContractorRows(detail, workItems) : []), [detail, workItems]);
  const versions = useMemo(() => (detail ? buildDocumentVersionRows(detail) : []), [detail]);
  const auditEvents = useMemo(() => (detail ? buildDocumentAuditRows(detail) : []), [detail]);
  const comments = useMemo(() => (detail ? buildDocumentCommentRows(detail) : []), [detail]);
  const title = getDocumentDetailTitle(detail, requestedDocumentId);
  const canShowDetail = canRenderDocumentDetail(status, detail);
  const organizationMissing = organizationStatus === "ready" && !canUseDocumentDetailOrganizationScope(selectedOrganizationId);
  const readyWithoutDetail = !organizationMissing && isDocumentDetailEmpty(status, detail);

  return (
    <div className="module-page document-detail-page">
      <PageHeader
        badgeTone={status === "ready" ? "success" : status === "error" ? "danger" : "info"}
        description="Jedno miejsce do zrozumienia dokumentu, jego źródła, wersji i powiązań operacyjnych."
        eyebrow={status === "ready" ? "Centrum dokumentu" : "Dokument"}
        title={title}
        actions={
          <>
            <Link className="ui-button ui-button--secondary ui-button--sm" href="/dokumenty">
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
        <EmptyState description={DOCUMENT_DETAIL_ORGANIZATION_REQUIRED_DESCRIPTION} title={DOCUMENT_DETAIL_ORGANIZATION_REQUIRED_TITLE} />
      ) : null}
      {readyWithoutDetail ? <EmptyState description="Nie znaleziono danych dokumentu w wybranej organizacji." title="Brak dokumentu" /> : null}

      {canShowDetail && detail && summary ? (
        <section className="invoice-detail-grid document-detail-grid">
          <div className="invoice-detail-grid__main">
            <Card
              action={<StatusBadge status={getDocumentStatusTone(detail)}>{facts[0]?.value ?? "Status nieznany"}</StatusBadge>}
              description={summary.reasonLabel}
              title="Profil dokumentu"
            >
              <div className="invoice-center-summary">
                <div>
                  <span>Stan dokumentu</span>
                  <strong>{summary.statusLabel}</strong>
                </div>
                <div>
                  <span>Przetwarzanie</span>
                  <strong>{summary.processingLabel}</strong>
                </div>
                <div>
                  <span>Powiązania</span>
                  <strong>{summary.relationshipLabel}</strong>
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
              action={<StatusBadge status={getDocumentWorkflowTone(detail)}>{facts[1]?.value ?? "Workflow"}</StatusBadge>}
              description="Bezpieczny opis pochodzenia i przetwarzania dokumentu, bez ścieżek lokalnych i kluczy plików."
              title="Źródło i ślad dokumentu"
            >
              <Table columns={traceColumns} data={traceItems} emptyMessage="Brak bezpiecznych informacji o źródle dokumentu." getRowKey={(row) => row.id} />
            </Card>

            <Card description="Sprawy operacyjne powiązane z dokumentem przez obecne dane organizacji." title="Powiązane sprawy">
              <Table columns={workItemColumns} data={relatedWorkItems} emptyMessage="Brak spraw powiązanych z tym dokumentem." getRowKey={(row) => row.id} />
            </Card>

            <Card description="Faktury wynikające z powiązanych spraw albo metadanych dokumentu." title="Powiązane faktury">
              <Table columns={invoiceColumns} data={relatedInvoices} emptyMessage="Brak faktur powiązanych z tym dokumentem." getRowKey={(row) => row.id} />
            </Card>

            <Card description="Kontrahenci powiązani z dokumentem przez sprawy lub faktury." title="Powiązani kontrahenci">
              <Table columns={contractorColumns} data={relatedContractors} emptyMessage="Brak kontrahentów powiązanych z tym dokumentem." getRowKey={(row) => row.id} />
            </Card>

            <Card title="Wersje dokumentu">
              <Table columns={versionColumns} data={versions} emptyMessage="Brak wersji dokumentu w odpowiedzi API." getRowKey={(row) => row.id} />
            </Card>

            <Card id="document-comments" description="Komentarze i adnotacje są pokazane tylko do odczytu. Ten ekran nie dodaje nowych komentarzy." title="Komentarze i adnotacje">
              <Table columns={commentColumns} data={comments} emptyMessage="Brak komentarzy lub adnotacji dla tego dokumentu." getRowKey={(row) => row.id} />
            </Card>

            <Card description="Historia dokumentu bez technicznych szczegółów przetwarzania." title="Aktywność dokumentu">
              <Table columns={auditColumns} data={auditEvents} emptyMessage="Brak zdarzeń w historii dokumentu." getRowKey={(row) => row.id} />
            </Card>
          </div>

          <aside className="module-activity-panel" aria-label="Kontekst dokumentu">
            <Card action={<Badge tone={DOCUMENT_DETAIL_READ_ONLY ? "info" : "warning"}>Read-only</Badge>} title="Kontekst biznesowy">
              <ol className="module-activity-list">
                <li className="module-activity-list__item">
                  <span>Organizacja</span>
                  <strong>{detail.organization_name || selectedOrganizationId || "-"}</strong>
                  <p>Dokument jest pokazywany wyłącznie w aktywnej organizacji.</p>
                </li>
                <li className="module-activity-list__item">
                  <span>Do czego służy</span>
                  <strong>{detail.use_in_assistant ? "Może zasilać wiedzę firmy" : "Dokument operacyjny"}</strong>
                  <p>{detail.safe_content_preview || "Warto uzupełnić opis albo powiązać dokument ze sprawą."}</p>
                </li>
                <li className="module-activity-list__item">
                  <span>Co sprawdzić dalej</span>
                  <strong>{summary.riskLabels.length ? "Wymaga uwagi" : "Brak pilnych sygnałów"}</strong>
                  <p>{summary.riskLabels[0] || "Sprawdź powiązane sprawy, faktury i kontrahentów, jeśli dokument ma wspierać pracę operacyjną."}</p>
                </li>
                <li className="module-activity-list__item">
                  <span>Bezpieczny zakres</span>
                  <strong>Brak akcji zapisu</strong>
                  <p>Nie ma uploadu, edycji, usuwania, OCR ani zmian wersji dokumentu.</p>
                </li>
                <li className="module-activity-list__item">
                  <span>Szybkie przejścia</span>
                  <strong>Istniejące moduły</strong>
                  <div className="module-quick-actions">
                    <Link className="module-quick-action" href="/dokumenty">
                      <FileText aria-hidden="true" size={15} />
                      Dokumenty
                    </Link>
                    <Link className="module-quick-action" href="/work-items">
                      <Link2 aria-hidden="true" size={15} />
                      Sprawy
                    </Link>
                    <Link className="module-quick-action" href="#document-comments">
                      <MessageSquareText aria-hidden="true" size={15} />
                      Komentarze
                    </Link>
                  </div>
                </li>
              </ol>
            </Card>
          </aside>
        </section>
      ) : null}
    </div>
  );
}
