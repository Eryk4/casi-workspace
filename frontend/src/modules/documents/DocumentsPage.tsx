"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { FileText, FolderOpen, RefreshCw } from "lucide-react";

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
  DOCUMENTS_ENDPOINT,
  DOCUMENTS_ORGANIZATION_REQUIRED_DESCRIPTION,
  DOCUMENTS_ORGANIZATION_REQUIRED_TITLE,
  DOCUMENTS_READ_ONLY,
  buildDocumentsKpis,
  buildKnowledgeDocumentRows,
  canUseDocumentsOrganizationScope,
  getDocumentsErrorState,
  hasDocumentsData,
  isDocumentsEmpty,
  readKnowledgeDocuments,
  type DocumentsErrorState,
  type DocumentsStatus,
  type KnowledgeDocumentRecord,
  type KnowledgeDocumentViewRow,
} from "./documentsModel";

const columns: Array<TableColumn<KnowledgeDocumentViewRow>> = [
  {
    key: "title",
    header: "Dokument",
    render: (row) => (
      <Link className="module-row-title module-row-link" href={`/dokumenty/${row.id}`}>
        <FileText aria-hidden="true" size={16} />
        {row.title}
      </Link>
    ),
  },
  {
    key: "status",
    header: "Status",
    render: (row) => <StatusBadge status={row.statusTone}>{row.statusLabel}</StatusBadge>,
  },
  {
    key: "workflow",
    header: "Workflow",
    render: (row) => <StatusBadge status={row.workflowTone}>{row.workflowLabel}</StatusBadge>,
  },
  {
    key: "folder",
    header: "Folder",
    render: (row) => (
      <span className="module-row-title">
        <FolderOpen aria-hidden="true" size={15} />
        {row.folderLabel}
      </span>
    ),
  },
  {
    key: "owner",
    header: "Odpowiedzialny",
    render: (row) => row.ownerLabel,
  },
  {
    key: "source",
    header: "Zrodlo",
    render: (row) => row.sourceLabel,
  },
  {
    key: "version",
    header: "Wersja",
    render: (row) => row.versionLabel,
  },
  {
    key: "updated",
    header: "Aktualizacja",
    align: "right",
    render: (row) => row.updatedLabel,
  },
];

export function DocumentsPage() {
  const { selectedOrganizationId, selectedOrganization, status: organizationStatus } = useActiveOrganization();
  const [documents, setDocuments] = useState<KnowledgeDocumentRecord[] | null>(null);
  const [status, setStatus] = useState<DocumentsStatus>("idle");
  const [errorState, setErrorState] = useState<DocumentsErrorState | null>(null);

  const loadDocuments = useCallback(async () => {
    if (organizationStatus === "loading") {
      setStatus("loading");
      setErrorState(null);
      return;
    }

    if (!canUseDocumentsOrganizationScope(selectedOrganizationId)) {
      setDocuments([]);
      setErrorState(null);
      setStatus("ready");
      return;
    }

    setStatus("loading");
    setErrorState(null);

    try {
      const payload = await api.knowledgeDocuments(withActiveOrganizationQuery(selectedOrganizationId));
      const nextDocuments = readKnowledgeDocuments(payload);
      setDocuments(nextDocuments);
      setStatus("ready");
    } catch (error) {
      const nextErrorState = getDocumentsErrorState(error);
      setErrorState(nextErrorState);
      setDocuments(null);
      setStatus(nextErrorState.status);
    }
  }, [organizationStatus, selectedOrganizationId]);

  useEffect(() => {
    void loadDocuments();
  }, [loadDocuments]);

  const rows = useMemo(() => buildKnowledgeDocumentRows(documents ?? []), [documents]);
  const kpis = useMemo(() => buildDocumentsKpis(documents ?? []), [documents]);
  const hasData = hasDocumentsData(status, documents);
  const organizationMissing = organizationStatus === "ready" && !canUseDocumentsOrganizationScope(selectedOrganizationId);
  const readyWithoutData = !organizationMissing && isDocumentsEmpty(status, documents);

  return (
    <div className="module-page documents-page">
      <PageHeader
        badgeTone={status === "ready" ? "success" : status === "error" ? "warning" : "info"}
        description="Minimalny podglad bazy wiedzy i dokumentow z /api/knowledge/documents. Ten ekran jest teraz read-only MVP."
        eyebrow={status === "ready" ? "Dane live" : "Dokumenty"}
        title="Dokumenty"
        actions={
          <Button disabled={status === "loading"} icon={<RefreshCw size={15} />} onClick={loadDocuments} size="sm" variant="secondary">
            Odswiez
          </Button>
        }
      />

      {status === "loading" ? <LoadingState /> : null}
      {errorState ? <ErrorState description={errorState.description} title={errorState.title} /> : null}
      {organizationMissing ? (
        <EmptyState
          description={DOCUMENTS_ORGANIZATION_REQUIRED_DESCRIPTION}
          title={DOCUMENTS_ORGANIZATION_REQUIRED_TITLE}
        />
      ) : null}
      {readyWithoutData ? (
        <EmptyState
          description={`Backend odpowiedzial poprawnie, ale nie zwrocil dokumentow dla organizacji ${selectedOrganization?.name ?? selectedOrganizationId}.`}
          title="Brak dokumentow w bazie wiedzy"
        />
      ) : null}

      {hasData ? (
        <>
          <section className="module-kpi-row" aria-label="Podsumowanie dokumentow">
            <Card className="module-metric">
              <span className="module-metric__label">Tryb ekranu</span>
              <strong>{DOCUMENTS_READ_ONLY ? "Read-only" : "Akcje wlaczone"}</strong>
              <span>Bez uploadu, edycji, wersjonowania i bulk actions.</span>
            </Card>
            <Card className="module-metric">
              <span className="module-metric__label">Dokumenty</span>
              <strong>{kpis.total}</strong>
              <span>Pobrane z {DOCUMENTS_ENDPOINT}.</span>
            </Card>
            <Card className="module-metric">
              <span className="module-metric__label">Gotowe / stabilne</span>
              <strong>{kpis.ready}</strong>
              <span>Obowiazujace albo stabilne w workflow.</span>
            </Card>
            <Card className="module-metric">
              <span className="module-metric__label">Do decyzji / OCR</span>
              <strong>{kpis.needsDecision + kpis.processingOrErrors}</strong>
              <span>Pozycje wymagajace uwagi albo przetwarzania.</span>
            </Card>
          </section>

          <Card
            description="Lista pokazuje realne dokumenty knowledge. Podglad pliku, download, decyzje i komentarze zostaja poza zakresem tego kroku."
            title="Biblioteka dokumentow"
          >
            <Table
              columns={columns}
              data={rows}
              emptyMessage="Backend nie zwrocil dokumentow."
              getRowKey={(row) => row.id}
            />
          </Card>
        </>
      ) : null}
    </div>
  );
}
