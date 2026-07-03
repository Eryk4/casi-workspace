"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { ArrowLeft, FileText, RefreshCw, ShieldCheck } from "lucide-react";

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
  DOCUMENT_DETAIL_EDIT_ENABLED,
  DOCUMENT_DETAIL_DELETE_ENABLED,
  DOCUMENT_DETAIL_ENDPOINT_PREFIX,
  DOCUMENT_DETAIL_OCR_ENABLED,
  DOCUMENT_DETAIL_ORGANIZATION_REQUIRED_DESCRIPTION,
  DOCUMENT_DETAIL_ORGANIZATION_REQUIRED_TITLE,
  DOCUMENT_DETAIL_READ_ONLY,
  DOCUMENT_DETAIL_S3_ACTIONS_ENABLED,
  DOCUMENT_DETAIL_UPLOAD_ENABLED,
  buildDocumentAuditRows,
  buildDocumentDetailFacts,
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
  type DocumentDetailErrorState,
  type DocumentDetailStatus,
  type DocumentVersionRow,
  type KnowledgeDocumentDetail,
} from "./documentDetailModel";

const versionColumns: Array<TableColumn<DocumentVersionRow>> = [
  {
    key: "version",
    header: "Wersja",
    render: (row) => row.versionLabel,
  },
  {
    key: "file",
    header: "Plik",
    render: (row) => row.fileLabel,
  },
  {
    key: "status",
    header: "Status",
    render: (row) => row.statusLabel,
  },
  {
    key: "official",
    header: "Typ",
    render: (row) => row.officialLabel,
  },
  {
    key: "storage",
    header: "Storage",
    render: (row) => row.storageLabel,
  },
  {
    key: "created",
    header: "Utworzono",
    align: "right",
    render: (row) => row.createdLabel,
  },
];

const auditColumns: Array<TableColumn<DocumentAuditRow>> = [
  {
    key: "action",
    header: "Zdarzenie",
    render: (row) => row.actionLabel,
  },
  {
    key: "actor",
    header: "Aktor",
    render: (row) => row.actorLabel,
  },
  {
    key: "date",
    header: "Data",
    align: "right",
    render: (row) => row.dateLabel,
  },
];

export function DocumentDetailPage({ documentId: requestedDocumentId }: { documentId: number }) {
  const { selectedOrganizationId, status: organizationStatus } = useActiveOrganization();
  const [detail, setDetail] = useState<KnowledgeDocumentDetail | null>(null);
  const [status, setStatus] = useState<DocumentDetailStatus>("idle");
  const [errorState, setErrorState] = useState<DocumentDetailErrorState | null>(null);

  const loadDetail = useCallback(async () => {
    if (organizationStatus === "loading") {
      setStatus("loading");
      setErrorState(null);
      return;
    }

    if (!canUseDocumentDetailOrganizationScope(selectedOrganizationId)) {
      setDetail(null);
      setErrorState(null);
      setStatus("ready");
      return;
    }

    setStatus("loading");
    setErrorState(null);

    try {
      const payload = await api.knowledgeDocumentDetail(
        requestedDocumentId,
        withActiveOrganizationQuery(selectedOrganizationId),
      );
      const nextDetail = readKnowledgeDocumentDetail(payload, requestedDocumentId);
      setDetail(nextDetail);
      setStatus("ready");
    } catch (nextError) {
      const nextErrorState = getDocumentDetailErrorState(nextError);
      setDetail(null);
      setErrorState(nextErrorState);
      setStatus(nextErrorState.status);
    }
  }, [organizationStatus, requestedDocumentId, selectedOrganizationId]);

  useEffect(() => {
    void loadDetail();
  }, [loadDetail]);

  const facts = useMemo(() => (detail ? buildDocumentDetailFacts(detail) : []), [detail]);
  const versions = useMemo(() => (detail ? buildDocumentVersionRows(detail) : []), [detail]);
  const auditEvents = useMemo(() => (detail ? buildDocumentAuditRows(detail) : []), [detail]);
  const title = getDocumentDetailTitle(detail, requestedDocumentId);
  const canShowDetail = canRenderDocumentDetail(status, detail);
  const organizationMissing =
    organizationStatus === "ready" && !canUseDocumentDetailOrganizationScope(selectedOrganizationId);
  const readyWithoutDetail = !organizationMissing && isDocumentDetailEmpty(status, detail);

  return (
    <div className="module-page document-detail-page">
      <PageHeader
        badgeTone={status === "ready" ? "success" : status === "error" ? "danger" : "info"}
        description={`Read-only szczegol dokumentu pobierany z ${DOCUMENT_DETAIL_ENDPOINT_PREFIX}/{id}. Bez uploadu, edycji, OCR i linkow do plikow.`}
        eyebrow={status === "ready" ? "Dane live" : "Dokument"}
        title={title}
        actions={
          <>
            <Link className="ui-button ui-button--secondary ui-button--sm" href="/dokumenty">
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
          description={DOCUMENT_DETAIL_ORGANIZATION_REQUIRED_DESCRIPTION}
          title={DOCUMENT_DETAIL_ORGANIZATION_REQUIRED_TITLE}
        />
      ) : null}
      {readyWithoutDetail ? (
        <EmptyState description="Backend nie zwrocil danych dla tego dokumentu." title="Brak dokumentu" />
      ) : null}

      {canShowDetail && detail ? (
        <section className="invoice-detail-grid document-detail-grid">
          <div className="invoice-detail-grid__main">
            <Card
              action={<StatusBadge status={getDocumentStatusTone(detail)}>{facts[0]?.value ?? "Status nieznany"}</StatusBadge>}
              title="Metadane dokumentu"
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
              action={<StatusBadge status={getDocumentWorkflowTone(detail)}>{facts[1]?.value ?? "Workflow"}</StatusBadge>}
              description="Frontend pokazuje tylko bezpieczne metadane. Nie generuje publicznych linkow i nie otwiera plikow z lokalnego storage."
              title="Bezpieczny podglad"
            >
              <div className="module-readiness">
                <div className="module-readiness__item">
                  <FileText aria-hidden="true" size={17} />
                  <div>
                    <strong>{detail.file_name || "Brak pliku"}</strong>
                    <span>{detail.safe_content_preview || "API nie zwrocilo bezpiecznego skrotu tresci."}</span>
                  </div>
                </div>
                <div className="module-readiness__item">
                  <ShieldCheck aria-hidden="true" size={17} />
                  <div>
                    <strong>Tryb read-only</strong>
                    <span>
                      Upload: {DOCUMENT_DETAIL_UPLOAD_ENABLED ? "wlaczony" : "wylaczony"} · Edycja:{" "}
                      {DOCUMENT_DETAIL_EDIT_ENABLED ? "wlaczona" : "wylaczona"} · OCR:{" "}
                      {DOCUMENT_DETAIL_OCR_ENABLED ? "wlaczony" : "wylaczony"}
                    </span>
                  </div>
                </div>
              </div>
            </Card>

            <Card title="Wersje dokumentu">
              <Table
                columns={versionColumns}
                data={versions}
                emptyMessage="Backend nie zwrocil wersji dokumentu."
                getRowKey={(row) => row.id}
              />
            </Card>

            <Card title="Audyt i komentarze">
              <Table
                columns={auditColumns}
                data={auditEvents}
                emptyMessage="Brak zdarzen audytowych w odpowiedzi API."
                getRowKey={(row) => row.id}
              />
            </Card>
          </div>

          <aside className="module-activity-panel" aria-label="Kontekst dokumentu">
            <Card
              action={<Badge tone={DOCUMENT_DETAIL_READ_ONLY ? "info" : "warning"}>Read-only</Badge>}
              title="Zakres tego widoku"
            >
              <ol className="module-activity-list">
                <li className="module-activity-list__item">
                  <span>Organizacja</span>
                  <strong>{detail.organization_name || selectedOrganizationId || "-"}</strong>
                  <p>organization_id jest wymagane przy pobieraniu szczegolu.</p>
                </li>
                <li className="module-activity-list__item">
                  <span>Komentarze</span>
                  <strong>{detail.comment_summary?.comment_count ?? 0}</strong>
                  <p>Pokazane tylko jako licznik, bez akcji dodawania komentarza.</p>
                </li>
                <li className="module-activity-list__item">
                  <span>Pobrania</span>
                  <strong>{detail.audit_summary?.download_count ?? 0}</strong>
                  <p>Bez generowania linkow download w tym kroku.</p>
                </li>
                <li className="module-activity-list__item">
                  <span>Blokady funkcji</span>
                  <strong>
                    {DOCUMENT_DETAIL_DELETE_ENABLED || DOCUMENT_DETAIL_S3_ACTIONS_ENABLED
                      ? "Akcje wlaczone"
                      : "Brak akcji zapisu"}
                  </strong>
                  <p>Delete, S3, OCR, upload i edycja pozostaja poza zakresem.</p>
                </li>
              </ol>
            </Card>
          </aside>
        </section>
      ) : null}
    </div>
  );
}
