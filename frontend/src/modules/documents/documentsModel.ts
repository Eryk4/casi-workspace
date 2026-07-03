import { ApiContractError, ApiError } from "@/lib/api";
import type { DataViewErrorState, DataViewStatus } from "@/lib/types";

export type DocumentsStatus = DataViewStatus;

export type DocumentsErrorState = DataViewErrorState<DocumentsStatus>;

export type KnowledgeDocumentRecord = {
  knowledge_document_id: number;
  title?: string;
  file_name?: string | null;
  mime_type?: string | null;
  source_type?: string;
  library_path?: string;
  library_path_label?: string;
  lifecycle_status?: string;
  duplicate_status?: string;
  processing_status?: string;
  processing_error?: string | null;
  current_version_number?: number;
  official_version_number?: number;
  business_status?: string;
  business_status_label?: string;
  workflow_status?: string;
  workflow_status_label?: string;
  owner_user_label?: string | null;
  reviewer_user_label?: string | null;
  approver_user_label?: string | null;
  organization_name?: string | null;
  created_by_login?: string | null;
  created_by_display_name?: string | null;
  updated_at?: string | null;
  created_at?: string | null;
  use_in_assistant?: boolean;
  is_downloadable?: boolean;
};

export type KnowledgeDocumentViewRow = {
  id: string;
  title: string;
  fileLabel: string;
  statusLabel: string;
  statusTone: "ok" | "warning" | "danger" | "info" | "neutral";
  workflowLabel: string;
  workflowTone: "ok" | "warning" | "danger" | "info" | "neutral";
  sourceLabel: string;
  ownerLabel: string;
  folderLabel: string;
  updatedLabel: string;
  versionLabel: string;
};

export type DocumentsKpis = {
  total: number;
  ready: number;
  needsDecision: number;
  processingOrErrors: number;
};

export const DOCUMENTS_ENDPOINT = "/knowledge/documents";
export const DOCUMENTS_READ_ONLY = true;
export const DOCUMENTS_ORGANIZATION_REQUIRED_TITLE = "Wybierz organizacje, aby zobaczyc dokumenty";
export const DOCUMENTS_ORGANIZATION_REQUIRED_DESCRIPTION =
  "Uzytkownik globalny musi najpierw wskazac organizacje w topbarze. Dopiero wtedy frontend przekaze organization_id do /api/knowledge/documents.";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function readString(value: unknown, fallback = "-"): string {
  return typeof value === "string" && value.trim() ? value : fallback;
}

function readOptionalString(value: unknown): string | undefined {
  return typeof value === "string" && value.trim() ? value : undefined;
}

function readNumber(value: unknown): number | undefined {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === "string" && value.trim() && Number.isFinite(Number(value))) {
    return Number(value);
  }
  return undefined;
}

function readBoolean(value: unknown): boolean | undefined {
  return typeof value === "boolean" ? value : undefined;
}

function toLabel(value: string | undefined, fallback = "-"): string {
  if (!value) {
    return fallback;
  }
  return value.replace(/_/g, " ").replace(/^\w/, (character) => character.toUpperCase());
}

function formatDateLabel(value: string | null | undefined): string {
  if (!value) {
    return "Brak daty";
  }

  const [datePart, timePart] = value.replace("Z", "").split("T");
  if (!datePart) {
    return value;
  }

  return timePart ? `${datePart} ${timePart.slice(0, 5)}` : datePart;
}

export function readKnowledgeDocuments(payload: unknown): KnowledgeDocumentRecord[] {
  if (!isRecord(payload) || !Array.isArray(payload.documents)) {
    throw new ApiContractError(DOCUMENTS_ENDPOINT, payload);
  }

  return payload.documents.map((item) => {
    if (!isRecord(item)) {
      throw new ApiContractError(DOCUMENTS_ENDPOINT, payload);
    }

    const documentId = readNumber(item.knowledge_document_id);
    if (!documentId) {
      throw new ApiContractError(DOCUMENTS_ENDPOINT, payload);
    }

    return {
      knowledge_document_id: documentId,
      title: readOptionalString(item.title),
      file_name: readOptionalString(item.file_name) ?? null,
      mime_type: readOptionalString(item.mime_type) ?? null,
      source_type: readOptionalString(item.source_type),
      library_path: readOptionalString(item.library_path),
      library_path_label: readOptionalString(item.library_path_label),
      lifecycle_status: readOptionalString(item.lifecycle_status),
      duplicate_status: readOptionalString(item.duplicate_status),
      processing_status: readOptionalString(item.processing_status),
      processing_error: readOptionalString(item.processing_error) ?? null,
      current_version_number: readNumber(item.current_version_number),
      official_version_number: readNumber(item.official_version_number),
      business_status: readOptionalString(item.business_status),
      business_status_label: readOptionalString(item.business_status_label),
      workflow_status: readOptionalString(item.workflow_status),
      workflow_status_label: readOptionalString(item.workflow_status_label),
      owner_user_label: readOptionalString(item.owner_user_label) ?? null,
      reviewer_user_label: readOptionalString(item.reviewer_user_label) ?? null,
      approver_user_label: readOptionalString(item.approver_user_label) ?? null,
      organization_name: readOptionalString(item.organization_name) ?? null,
      created_by_login: readOptionalString(item.created_by_login) ?? null,
      created_by_display_name: readOptionalString(item.created_by_display_name) ?? null,
      updated_at: readOptionalString(item.updated_at) ?? null,
      created_at: readOptionalString(item.created_at) ?? null,
      use_in_assistant: readBoolean(item.use_in_assistant),
      is_downloadable: readBoolean(item.is_downloadable),
    };
  });
}

export function getDocumentsErrorState(error: unknown): DocumentsErrorState {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      return {
        status: "unauthenticated",
        title: "Sesja wygasla",
        description: "Zaloguj sie ponownie, aby zobaczyc biblioteke dokumentow.",
      };
    }
    if (error.status === 403) {
      return {
        status: "forbidden",
        title: "Brak dostepu do dokumentow",
        description: "Twoje konto nie ma uprawnien do odczytu bazy wiedzy i dokumentow.",
      };
    }
    if (error.status >= 500) {
      return {
        status: "server-error",
        title: "Backend nie zwrocil dokumentow",
        description: "Wystapil blad serwera. Sprobuj odswiezyc widok albo sprawdz logi backendu.",
      };
    }
    return {
      status: "error",
      title: `Blad API (${error.status})`,
      description: error.message,
    };
  }

  if (error instanceof ApiContractError) {
    return {
      status: "error",
      title: "Niepoprawny format dokumentow",
      description: "Backend odpowiedzial, ale dane nie pasuja do minimalnego kontraktu widoku Dokumenty.",
    };
  }

  if (error instanceof TypeError) {
    return {
      status: "error",
      title: "Problem z polaczeniem z API",
      description: "Nie udalo sie polaczyc z backendem. Sprawdz, czy API jest dostepne i sprobuj ponownie.",
    };
  }

  return {
    status: "error",
    title: "Nie udalo sie pobrac dokumentow",
    description: error instanceof Error ? error.message : "Wystapil nieznany blad pobierania dokumentow.",
  };
}

export function documentStatusTone(item: KnowledgeDocumentRecord): KnowledgeDocumentViewRow["statusTone"] {
  if (item.lifecycle_status === "deleted" || item.processing_status === "error") {
    return "danger";
  }
  if (item.processing_status === "processing" || item.processing_status === "queued") {
    return "info";
  }
  if (item.business_status === "do_sprawdzenia" || item.business_status === "do_akceptacji") {
    return "warning";
  }
  if (item.business_status === "obowiazujacy") {
    return "ok";
  }
  if (item.lifecycle_status === "archived" || item.business_status === "archiwalny") {
    return "neutral";
  }
  return "info";
}

export function documentWorkflowTone(item: KnowledgeDocumentRecord): KnowledgeDocumentViewRow["workflowTone"] {
  if (item.workflow_status === "stable") {
    return "ok";
  }
  if (item.workflow_status === "review_needed" || item.workflow_status === "official_missing") {
    return "warning";
  }
  if (item.workflow_status === "processing") {
    return "info";
  }
  if (item.workflow_status === "deleted") {
    return "danger";
  }
  return "neutral";
}

export function buildKnowledgeDocumentRows(items: KnowledgeDocumentRecord[]): KnowledgeDocumentViewRow[] {
  return items.map((item) => {
    const owner =
      item.owner_user_label || item.reviewer_user_label || item.approver_user_label || item.created_by_display_name || item.created_by_login;

    return {
      id: String(item.knowledge_document_id),
      title: readString(item.title, `Dokument #${item.knowledge_document_id}`),
      fileLabel: readString(item.file_name, "Brak pliku"),
      statusLabel: readString(item.business_status_label, toLabel(item.business_status, "Status nieznany")),
      statusTone: documentStatusTone(item),
      workflowLabel: readString(item.workflow_status_label, toLabel(item.workflow_status, "Workflow nieznany")),
      workflowTone: documentWorkflowTone(item),
      sourceLabel: toLabel(item.source_type, "Zrodlo nieznane"),
      ownerLabel: readString(owner, "Nieprzypisane"),
      folderLabel: readString(item.library_path_label, "Bez folderu"),
      updatedLabel: formatDateLabel(item.updated_at || item.created_at),
      versionLabel:
        item.current_version_number || item.official_version_number
          ? `v${item.current_version_number ?? "-"} / oficj. ${item.official_version_number ?? "-"}`
          : "-",
    };
  });
}

export function buildDocumentsKpis(items: KnowledgeDocumentRecord[]): DocumentsKpis {
  return {
    total: items.length,
    ready: items.filter((item) => item.business_status === "obowiazujacy" || item.workflow_status === "stable").length,
    needsDecision: items.filter((item) => item.business_status === "do_sprawdzenia" || item.business_status === "do_akceptacji").length,
    processingOrErrors: items.filter((item) => ["queued", "processing", "error"].includes(item.processing_status ?? "")).length,
  };
}

export function hasDocumentsData(status: DocumentsStatus, items: KnowledgeDocumentRecord[] | null): boolean {
  return status === "ready" && Boolean(items?.length);
}

export function isDocumentsEmpty(status: DocumentsStatus, items: KnowledgeDocumentRecord[] | null): boolean {
  return status === "ready" && Array.isArray(items) && items.length === 0;
}

export function canUseDocumentsOrganizationScope(organizationId: string | number | null | undefined): boolean {
  return Boolean(String(organizationId ?? "").trim());
}
