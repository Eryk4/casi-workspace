import { ApiContractError, ApiError } from "@/lib/api";
import type { DataViewErrorState, DataViewStatus } from "@/lib/types";
import {
  canUseDocumentsOrganizationScope,
  documentStatusTone,
  documentWorkflowTone,
  type KnowledgeDocumentRecord,
} from "./documentsModel";

export type DocumentDetailStatus = DataViewStatus;

export type DocumentDetailErrorState = DataViewErrorState<DocumentDetailStatus>;

export type DocumentDetailFact = {
  label: string;
  value: string;
};

export type DocumentVersionRow = {
  id: string;
  versionLabel: string;
  fileLabel: string;
  statusLabel: string;
  officialLabel: string;
  createdLabel: string;
  storageLabel: string;
};

export type DocumentAuditRow = {
  id: string;
  actionLabel: string;
  actorLabel: string;
  dateLabel: string;
};

export type KnowledgeDocumentVersion = {
  knowledge_document_version_id?: number;
  version_number?: number;
  file_name?: string | null;
  mime_type?: string | null;
  file_size_bytes?: number;
  storage_key?: string | null;
  processing_status?: string;
  content_preview?: string | null;
  extracted_text_preview?: string | null;
  created_at?: string | null;
  created_by_display_name?: string | null;
  created_by_login?: string | null;
  is_official?: boolean;
};

export type KnowledgeDocumentAuditEvent = {
  audit_event_id?: number;
  event_type?: string;
  action_label?: string;
  actor_label?: string;
  event_time?: string | null;
};

export type KnowledgeDocumentCommentSummary = {
  comment_count?: number;
  annotation_count?: number;
  last_comment_at?: string | null;
};

export type KnowledgeDocumentAuditSummary = {
  download_count?: number;
  event_count?: number;
  last_download_at?: string | null;
};

export type KnowledgeDocumentDetail = KnowledgeDocumentRecord & {
  versions: KnowledgeDocumentVersion[];
  audit_events: KnowledgeDocumentAuditEvent[];
  comment_summary?: KnowledgeDocumentCommentSummary;
  audit_summary?: KnowledgeDocumentAuditSummary;
  safe_content_preview?: string | null;
};

export const DOCUMENT_DETAIL_ENDPOINT_PREFIX = "/knowledge/documents";
export const DOCUMENT_DETAIL_READ_ONLY = true;
export const DOCUMENT_DETAIL_UPLOAD_ENABLED = false;
export const DOCUMENT_DETAIL_EDIT_ENABLED = false;
export const DOCUMENT_DETAIL_DELETE_ENABLED = false;
export const DOCUMENT_DETAIL_OCR_ENABLED = false;
export const DOCUMENT_DETAIL_S3_ACTIONS_ENABLED = false;
export const DOCUMENT_DETAIL_ORGANIZATION_REQUIRED_TITLE = "Wybierz organizacje, aby zobaczyc dokument";
export const DOCUMENT_DETAIL_ORGANIZATION_REQUIRED_DESCRIPTION =
  "Szczegol dokumentu wymaga aktywnej organizacji. Frontend wysyla organization_id do /api/knowledge/documents/{id}.";

const UNSAFE_PATH_PATTERNS = [
  /^[a-z]:\\/i,
  /^\\\\/,
  /^\/users\//i,
  /^\/home\//i,
  /\\users\\/i,
  /data[\\/]magazyn/i,
  /onedrive/i,
  /secret/i,
  /token/i,
  /password/i,
];
const HIDDEN_STORAGE_KEY = "__casi_hidden_storage_key__";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
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

function readRecordArray(value: unknown): Record<string, unknown>[] {
  return Array.isArray(value) ? value.filter(isRecord) : [];
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

function toLabel(value: string | undefined, fallback = "-"): string {
  if (!value) {
    return fallback;
  }
  return value.replace(/_/g, " ").replace(/^\w/, (character) => character.toUpperCase());
}

function isUnsafePathLike(value: string): boolean {
  const normalized = value.trim();
  return UNSAFE_PATH_PATTERNS.some((pattern) => pattern.test(normalized));
}

export function safeDocumentText(value: unknown, fallback = "-"): string {
  const nextValue = readOptionalString(value);
  if (!nextValue || isUnsafePathLike(nextValue)) {
    return fallback;
  }
  return nextValue;
}

export function safeDocumentFileLabel(value: unknown, fallback = "Plik ukryty"): string {
  const nextValue = readOptionalString(value);
  if (!nextValue) {
    return fallback;
  }

  if (!isUnsafePathLike(nextValue) && !nextValue.includes("\\") && !nextValue.includes("/")) {
    return nextValue;
  }

  const fileName = nextValue.split(/[\\/]/).filter(Boolean).pop();
  return fileName && !isUnsafePathLike(fileName) ? fileName : fallback;
}

export function safeStorageLabel(value: unknown): string {
  const nextValue = readOptionalString(value);
  if (!nextValue) {
    return "Brak storage key";
  }

  if (nextValue === HIDDEN_STORAGE_KEY) {
    return "Storage key ukryty";
  }

  return isUnsafePathLike(nextValue) ? "Storage key ukryty" : "Storage key zapisany";
}

function readSafeStorageKey(value: unknown): string | null {
  const nextValue = readOptionalString(value);
  if (!nextValue) {
    return null;
  }
  return isUnsafePathLike(nextValue) ? HIDDEN_STORAGE_KEY : nextValue;
}

function readVersion(item: Record<string, unknown>, index: number): KnowledgeDocumentVersion {
  return {
    knowledge_document_version_id: readNumber(item.knowledge_document_version_id),
    version_number: readNumber(item.version_number) ?? index + 1,
    file_name: safeDocumentFileLabel(item.file_name, "Plik ukryty"),
    mime_type: readOptionalString(item.mime_type) ?? null,
    file_size_bytes: readNumber(item.file_size_bytes),
    storage_key: readSafeStorageKey(item.storage_key),
    processing_status: readOptionalString(item.processing_status),
    content_preview: readOptionalString(item.content_preview) ?? null,
    extracted_text_preview: readOptionalString(item.extracted_text_preview) ?? null,
    created_at: readOptionalString(item.created_at) ?? null,
    created_by_display_name: readOptionalString(item.created_by_display_name) ?? null,
    created_by_login: readOptionalString(item.created_by_login) ?? null,
    is_official: readBoolean(item.is_official),
  };
}

function readAuditEvent(item: Record<string, unknown>, index: number): KnowledgeDocumentAuditEvent {
  return {
    audit_event_id: readNumber(item.audit_event_id) ?? index + 1,
    event_type: readOptionalString(item.event_type),
    action_label: readOptionalString(item.action_label),
    actor_label: readOptionalString(item.actor_label),
    event_time: readOptionalString(item.event_time) ?? null,
  };
}

function readSummary(payload: unknown): KnowledgeDocumentCommentSummary | undefined {
  if (!isRecord(payload)) {
    return undefined;
  }

  return {
    comment_count: readNumber(payload.comment_count) ?? 0,
    annotation_count: readNumber(payload.annotation_count) ?? 0,
    last_comment_at: readOptionalString(payload.last_comment_at) ?? null,
  };
}

function readAuditSummary(payload: unknown): KnowledgeDocumentAuditSummary | undefined {
  if (!isRecord(payload)) {
    return undefined;
  }

  return {
    download_count: readNumber(payload.download_count) ?? 0,
    event_count: readNumber(payload.event_count) ?? 0,
    last_download_at: readOptionalString(payload.last_download_at) ?? null,
  };
}

export function readKnowledgeDocumentDetail(payload: unknown, requestedDocumentId?: number): KnowledgeDocumentDetail {
  if (!isRecord(payload)) {
    throw new ApiContractError(`${DOCUMENT_DETAIL_ENDPOINT_PREFIX}/{id}`, payload);
  }

  const documentId = readNumber(payload.knowledge_document_id);
  if (!documentId || (requestedDocumentId && documentId !== requestedDocumentId)) {
    throw new ApiContractError(`${DOCUMENT_DETAIL_ENDPOINT_PREFIX}/{id}`, payload);
  }

  return {
    knowledge_document_id: documentId,
    title: safeDocumentText(payload.title, `Dokument #${documentId}`),
    file_name: safeDocumentFileLabel(payload.file_name, "Brak pliku"),
    mime_type: readOptionalString(payload.mime_type) ?? null,
    source_type: readOptionalString(payload.source_type),
    library_path: safeDocumentText(payload.library_path, undefined),
    library_path_label: safeDocumentText(payload.library_path_label, "Bez folderu"),
    lifecycle_status: readOptionalString(payload.lifecycle_status),
    duplicate_status: readOptionalString(payload.duplicate_status),
    processing_status: readOptionalString(payload.processing_status),
    processing_error: readOptionalString(payload.processing_error) ?? null,
    current_version_number: readNumber(payload.current_version_number),
    official_version_number: readNumber(payload.official_version_number),
    business_status: readOptionalString(payload.business_status),
    business_status_label: readOptionalString(payload.business_status_label),
    workflow_status: readOptionalString(payload.workflow_status),
    workflow_status_label: readOptionalString(payload.workflow_status_label),
    owner_user_label: readOptionalString(payload.owner_user_label) ?? null,
    reviewer_user_label: readOptionalString(payload.reviewer_user_label) ?? null,
    approver_user_label: readOptionalString(payload.approver_user_label) ?? null,
    organization_name: readOptionalString(payload.organization_name) ?? null,
    created_by_login: readOptionalString(payload.created_by_login) ?? null,
    created_by_display_name: readOptionalString(payload.created_by_display_name) ?? null,
    updated_at: readOptionalString(payload.updated_at) ?? null,
    created_at: readOptionalString(payload.created_at) ?? null,
    use_in_assistant: readBoolean(payload.use_in_assistant),
    is_downloadable: readBoolean(payload.is_downloadable),
    versions: readRecordArray(payload.versions).map(readVersion),
    audit_events: readRecordArray(payload.audit_events).map(readAuditEvent),
    comment_summary: readSummary(payload.comment_summary),
    audit_summary: readAuditSummary(payload.audit_summary),
    safe_content_preview: safeDocumentText(
      payload.content_preview ?? payload.extracted_text_preview ?? payload.summary,
      "",
    ),
  };
}

export function getDocumentDetailTitle(detail: KnowledgeDocumentDetail | null, requestedDocumentId: number): string {
  return detail?.title || `Dokument #${requestedDocumentId}`;
}

export function buildDocumentDetailFacts(detail: KnowledgeDocumentDetail): DocumentDetailFact[] {
  const owner =
    detail.owner_user_label || detail.reviewer_user_label || detail.approver_user_label || detail.created_by_display_name || detail.created_by_login;

  return [
    { label: "Status", value: safeDocumentText(detail.business_status_label, toLabel(detail.business_status, "Status nieznany")) },
    { label: "Workflow", value: safeDocumentText(detail.workflow_status_label, toLabel(detail.workflow_status, "Workflow nieznany")) },
    { label: "Zrodlo", value: toLabel(detail.source_type, "Zrodlo nieznane") },
    { label: "Typ", value: safeDocumentText(detail.mime_type, "Typ nieznany") },
    { label: "Folder", value: safeDocumentText(detail.library_path_label || detail.library_path, "Bez folderu") },
    { label: "Odpowiedzialny", value: safeDocumentText(owner, "Nieprzypisane") },
    { label: "Utworzono", value: formatDateLabel(detail.created_at) },
    { label: "Aktualizacja", value: formatDateLabel(detail.updated_at || detail.created_at) },
    {
      label: "Wersja",
      value:
        detail.current_version_number || detail.official_version_number
          ? `v${detail.current_version_number ?? "-"} / oficj. ${detail.official_version_number ?? "-"}`
          : "Brak wersji",
    },
  ];
}

export function buildDocumentVersionRows(detail: KnowledgeDocumentDetail): DocumentVersionRow[] {
  return detail.versions.map((version, index) => ({
    id: String(version.knowledge_document_version_id ?? `${detail.knowledge_document_id}-${index}`),
    versionLabel: `v${version.version_number ?? index + 1}`,
    fileLabel: safeDocumentFileLabel(version.file_name, "Plik ukryty"),
    statusLabel: toLabel(version.processing_status, "Status nieznany"),
    officialLabel: version.is_official ? "Oficjalna" : "Robocza",
    createdLabel: formatDateLabel(version.created_at),
    storageLabel: safeStorageLabel(version.storage_key),
  }));
}

export function buildDocumentAuditRows(detail: KnowledgeDocumentDetail): DocumentAuditRow[] {
  return detail.audit_events.map((event, index) => ({
    id: String(event.audit_event_id ?? `${detail.knowledge_document_id}-audit-${index}`),
    actionLabel: safeDocumentText(event.action_label, toLabel(event.event_type, "Zdarzenie")),
    actorLabel: safeDocumentText(event.actor_label, "System"),
    dateLabel: formatDateLabel(event.event_time),
  }));
}

export function getDocumentStatusTone(detail: KnowledgeDocumentDetail) {
  return documentStatusTone(detail);
}

export function getDocumentWorkflowTone(detail: KnowledgeDocumentDetail) {
  return documentWorkflowTone(detail);
}

export function canRenderDocumentDetail(status: DocumentDetailStatus, detail: KnowledgeDocumentDetail | null): boolean {
  return status === "ready" && Boolean(detail);
}

export function isDocumentDetailEmpty(status: DocumentDetailStatus, detail: KnowledgeDocumentDetail | null): boolean {
  return status === "ready" && !detail;
}

export function canUseDocumentDetailOrganizationScope(organizationId: string | number | null | undefined): boolean {
  return canUseDocumentsOrganizationScope(organizationId);
}

export function getDocumentDetailErrorState(error: unknown): DocumentDetailErrorState {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      return {
        status: "unauthenticated",
        title: "Sesja wygasla",
        description: "Zaloguj sie ponownie, aby zobaczyc szczegol dokumentu.",
      };
    }
    if (error.status === 403) {
      return {
        status: "forbidden",
        title: "Brak dostepu do dokumentu",
        description: "Twoje konto nie ma uprawnien do odczytu tego dokumentu.",
      };
    }
    if (error.status === 404) {
      return {
        status: "error",
        title: "Nie znaleziono dokumentu",
        description: "Backend nie znalazl dokumentu w wybranej organizacji albo dokument zostal usuniety.",
      };
    }
    if (error.status >= 500) {
      return {
        status: "server-error",
        title: "Backend nie zwrocil dokumentu",
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
      title: "Niepoprawny format dokumentu",
      description: "Backend odpowiedzial, ale dane nie pasuja do minimalnego kontraktu szczegolu dokumentu.",
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
    title: "Nie udalo sie pobrac dokumentu",
    description: error instanceof Error ? error.message : "Wystapil nieznany blad pobierania dokumentu.",
  };
}
