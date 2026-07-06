import { ApiContractError, ApiError } from "@/lib/api";
import type { DataViewErrorState, DataViewStatus } from "@/lib/types";
import {
  canUseDocumentsOrganizationScope,
  documentStatusTone,
  documentWorkflowTone,
  type KnowledgeDocumentRecord,
} from "./documentsModel";
import type { WorkItemRecord } from "../work-items/workItemsModel";

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
  descriptionLabel: string;
};

export type DocumentCommentRow = {
  id: string;
  authorLabel: string;
  targetLabel: string;
  dateLabel: string;
  noteLabel: string;
};

export type DocumentRelatedWorkItemRow = {
  id: string;
  workItemId: number;
  titleLabel: string;
  statusLabel: string;
  priorityLabel: string;
  dueLabel: string;
  href: string;
};

export type DocumentRelatedInvoiceRow = {
  id: string;
  invoiceId: number;
  numberLabel: string;
  contractorLabel: string;
  amountLabel: string;
  statusLabel: string;
  href: string;
};

export type DocumentRelatedContractorRow = {
  id: string;
  contractorId: number;
  nameLabel: string;
  contextLabel: string;
  href: string;
};

export type DocumentCenterSummary = {
  statusLabel: string;
  reasonLabel: string;
  processingLabel: string;
  relationshipLabel: string;
  riskLabels: string[];
};

export type DocumentSourceTraceItem = {
  id: string;
  label: string;
  value: string;
  description: string;
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
  event_id?: number;
  event_type?: string;
  action_label?: string;
  actor_label?: string;
  actor?: string;
  message?: string;
  event_time?: string | null;
};

export type KnowledgeDocumentComment = {
  knowledge_document_comment_id?: number;
  author_label?: string | null;
  target_label?: string | null;
  note_text?: string | null;
  created_at?: string | null;
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
  comments: KnowledgeDocumentComment[];
  comment_summary?: KnowledgeDocumentCommentSummary;
  audit_summary?: KnowledgeDocumentAuditSummary;
  safe_content_preview?: string | null;
  char_count?: number;
  has_text_preview?: boolean;
  file_preview_kind?: string | null;
  last_processed_at?: string | null;
};

export const DOCUMENT_DETAIL_ENDPOINT_PREFIX = "/knowledge/documents";
export const DOCUMENT_DETAIL_READ_ONLY = true;
export const DOCUMENT_DETAIL_UPLOAD_ENABLED = false;
export const DOCUMENT_DETAIL_EDIT_ENABLED = false;
export const DOCUMENT_DETAIL_DELETE_ENABLED = false;
export const DOCUMENT_DETAIL_OCR_ENABLED = false;
export const DOCUMENT_DETAIL_S3_ACTIONS_ENABLED = false;
export const DOCUMENT_DETAIL_ORGANIZATION_REQUIRED_TITLE = "Wybierz organizację, aby zobaczyć dokument";
export const DOCUMENT_DETAIL_ORGANIZATION_REQUIRED_DESCRIPTION =
  "Centrum dokumentu pokazuje dane tylko w kontekście wybranej organizacji.";

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
  const normalized = value.trim().toLowerCase();
  const labels: Record<string, string> = {
    manual: "Ręcznie",
    ready: "Gotowe",
    done: "Gotowe",
    pending: "Oczekuje",
    processing: "W trakcie",
    failed: "Wymaga uwagi",
    text: "Tekst",
    draft: "Roboczy",
    official_missing: "Brak wersji obowiązującej",
    "brak wersji obowiazujacej": "Brak wersji obowiązującej",
  };
  return labels[normalized] ?? value.replace(/_/g, " ").replace(/^\w/, (character) => character.toUpperCase());
}

function displayDocumentLabel(value: string | undefined, fallback: string): string {
  const label = safeDocumentText(value, "");
  return label ? toLabel(label, fallback) : fallback;
}

function metadataString(metadata: Record<string, unknown>, keys: string[], fallback = ""): string {
  for (const key of keys) {
    const value = safeDocumentText(metadata[key], "");
    if (value) {
      return value;
    }
  }
  return fallback;
}

function metadataNumber(metadata: Record<string, unknown>, keys: string[]): number | undefined {
  for (const key of keys) {
    const value = readNumber(metadata[key]);
    if (value) {
      return value;
    }
  }
  return undefined;
}

function metadataNumberList(metadata: Record<string, unknown>, keys: string[]): number[] {
  const values: number[] = [];
  keys.forEach((key) => {
    const rawValue = metadata[key];
    if (Array.isArray(rawValue)) {
      rawValue.forEach((item) => {
        const value = readNumber(item);
        if (value && !values.includes(value)) {
          values.push(value);
        }
      });
      return;
    }
    const value = readNumber(rawValue);
    if (value && !values.includes(value)) {
      values.push(value);
    }
  });
  return values;
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
    return "Brak śladu pliku";
  }

  if (nextValue === HIDDEN_STORAGE_KEY) {
    return "Ślad pliku ukryty";
  }

  return isUnsafePathLike(nextValue) ? "Ślad pliku ukryty" : "Ślad pliku zapisany";
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
    audit_event_id: readNumber(item.audit_event_id ?? item.event_id) ?? index + 1,
    event_id: readNumber(item.event_id),
    event_type: readOptionalString(item.event_type),
    action_label: readOptionalString(item.action_label),
    actor_label: readOptionalString(item.actor_label ?? item.actor),
    actor: readOptionalString(item.actor),
    message: readOptionalString(item.message),
    event_time: readOptionalString(item.event_time) ?? null,
  };
}

function readComment(item: Record<string, unknown>, index: number): KnowledgeDocumentComment {
  return {
    knowledge_document_comment_id: readNumber(item.knowledge_document_comment_id) ?? index + 1,
    author_label: readOptionalString(item.author_label ?? item.created_by_display_name ?? item.created_by_login) ?? null,
    target_label: readOptionalString(item.target_label) ?? null,
    note_text: readOptionalString(item.note_text) ?? null,
    created_at: readOptionalString(item.created_at) ?? null,
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
    comments: readRecordArray(payload.comments).map(readComment),
    comment_summary: readSummary(payload.comment_summary),
    audit_summary: readAuditSummary(payload.audit_summary),
    safe_content_preview: safeDocumentText(
      payload.content_preview ?? payload.extracted_text_preview ?? payload.summary,
      "",
    ),
    char_count: readNumber(payload.char_count),
    has_text_preview: readBoolean(payload.has_text_preview),
    file_preview_kind: readOptionalString(payload.file_preview_kind) ?? null,
    last_processed_at: readOptionalString(payload.last_processed_at) ?? null,
  };
}

export function getDocumentDetailTitle(detail: KnowledgeDocumentDetail | null, requestedDocumentId: number): string {
  return detail?.title || `Dokument #${requestedDocumentId}`;
}

export function buildDocumentDetailFacts(detail: KnowledgeDocumentDetail): DocumentDetailFact[] {
  const owner =
    detail.owner_user_label || detail.reviewer_user_label || detail.approver_user_label || detail.created_by_display_name || detail.created_by_login;

  return [
    { label: "Status", value: displayDocumentLabel(detail.business_status_label ?? detail.business_status, "Status nieznany") },
    { label: "Obieg", value: displayDocumentLabel(detail.workflow_status_label ?? detail.workflow_status, "Obieg nieznany") },
    { label: "Źródło", value: toLabel(detail.source_type, "Źródło nieznane") },
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
    actorLabel: safeDocumentText(event.actor_label || event.actor, "System"),
    dateLabel: formatDateLabel(event.event_time),
    descriptionLabel: safeDocumentText(event.message, "Zdarzenie zapisane w historii dokumentu."),
  }));
}

export function buildDocumentCommentRows(detail: KnowledgeDocumentDetail): DocumentCommentRow[] {
  return detail.comments.slice(0, 8).map((comment, index) => ({
    id: String(comment.knowledge_document_comment_id ?? `${detail.knowledge_document_id}-comment-${index}`),
    authorLabel: safeDocumentText(comment.author_label, "Użytkownik"),
    targetLabel: safeDocumentText(comment.target_label, "Dokument"),
    dateLabel: formatDateLabel(comment.created_at),
    noteLabel: safeDocumentText(comment.note_text, "Komentarz bez treści"),
  }));
}

export function buildDocumentCenterSummary(
  detail: KnowledgeDocumentDetail,
  workItems: WorkItemRecord[] = [],
): DocumentCenterSummary {
  const relatedWorkItemCount = buildDocumentRelatedWorkItemRows(detail, workItems).length;
  const relatedInvoiceCount = buildDocumentRelatedInvoiceRows(detail, workItems).length;
  const riskLabels = [
    detail.processing_status && detail.processing_status !== "done" ? "przetwarzanie nie jest zakończone" : "",
    detail.processing_error ? "jest błąd przetwarzania" : "",
    !detail.safe_content_preview ? "brak bezpiecznego skrótu treści" : "",
    !detail.official_version_number ? "brak oznaczonej wersji oficjalnej" : "",
    relatedWorkItemCount === 0 && relatedInvoiceCount === 0 ? "brak powiązanych spraw i faktur" : "",
  ].filter(Boolean);

  return {
    statusLabel: safeDocumentText(detail.business_status_label, toLabel(detail.business_status, "Status nieznany")),
    reasonLabel: riskLabels.length
      ? `Warto sprawdzić: ${riskLabels.slice(0, 2).join(", ")}.`
      : "Dokument ma podstawowe dane i nie pokazuje krytycznych sygnałów.",
    processingLabel: detail.processing_error
      ? "Przetwarzanie wymaga uwagi"
      : toLabel(detail.processing_status, "Status przetwarzania nieznany"),
    relationshipLabel:
      relatedWorkItemCount || relatedInvoiceCount
        ? `${relatedWorkItemCount} spraw, ${relatedInvoiceCount} faktur`
        : "Brak powiązań w obecnych danych",
    riskLabels,
  };
}

export function buildDocumentSourceTraceItems(detail: KnowledgeDocumentDetail): DocumentSourceTraceItem[] {
  return [
    {
      id: "source",
      label: "Źródło",
      value: toLabel(detail.source_type, "Źródło nieznane"),
      description: "Sposób, w jaki dokument trafił do bazy wiedzy.",
    },
    {
      id: "processing",
      label: "Przetwarzanie",
      value: detail.processing_error ? "Wymaga uwagi" : toLabel(detail.processing_status, "Status nieznany"),
      description: detail.processing_error
        ? "Backend zgłosił problem przetwarzania bez ujawniania technicznych szczegółów."
        : "Status przetworzenia dokumentu w systemie.",
    },
    {
      id: "preview",
      label: "Podgląd treści",
      value: detail.safe_content_preview ? "Dostępny bezpieczny skrót" : "Brak skrótu",
      description: detail.safe_content_preview || "API nie zwróciło bezpiecznego skrótu treści.",
    },
    {
      id: "file",
      label: "Plik",
      value: safeDocumentFileLabel(detail.file_name, "Plik ukryty"),
      description: detail.file_preview_kind ? `Typ podglądu: ${toLabel(detail.file_preview_kind, "brak")}` : "Bez publicznego linku do pliku.",
    },
  ];
}

function workItemMatchesDocument(item: WorkItemRecord, documentId: number): boolean {
  const metadata = item.metadata ?? {};
  const ids = metadataNumberList(metadata, ["knowledge_document_ids", "document_ids", "linked_document_ids"]);
  return ids.includes(documentId);
}

export function buildDocumentRelatedWorkItemRows(
  detail: KnowledgeDocumentDetail,
  workItems: WorkItemRecord[] = [],
): DocumentRelatedWorkItemRow[] {
  return workItems
    .filter((item) => workItemMatchesDocument(item, detail.knowledge_document_id))
    .slice(0, 8)
    .map((item) => ({
      id: String(item.work_item_id),
      workItemId: item.work_item_id,
      titleLabel: safeDocumentText(item.title, `Sprawa #${item.work_item_id}`),
      statusLabel: toLabel(item.status, "Status nieznany"),
      priorityLabel: toLabel(item.priority_level, "Priorytet nieznany"),
      dueLabel: formatDateLabel(item.due_at || item.sla_deadline_at),
      href: `/work-items/${item.work_item_id}`,
    }));
}

export function buildDocumentRelatedInvoiceRows(
  detail: KnowledgeDocumentDetail,
  workItems: WorkItemRecord[] = [],
): DocumentRelatedInvoiceRow[] {
  const invoices = new Map<number, DocumentRelatedInvoiceRow>();
  workItems.forEach((item) => {
    if (!workItemMatchesDocument(item, detail.knowledge_document_id)) {
      return;
    }
    const metadata = item.metadata ?? {};
    const invoiceId = metadataNumber(metadata, ["invoice_id", "linked_invoice_id", "source_invoice_id"]);
    if (!invoiceId || invoices.has(invoiceId)) {
      return;
    }
    invoices.set(invoiceId, {
      id: String(invoiceId),
      invoiceId,
      numberLabel: metadataString(metadata, ["invoice_number", "invoice_title"], `Faktura #${invoiceId}`),
      contractorLabel: metadataString(metadata, ["invoice_contractor_name", "contractor_name", "issuer_name"], "Kontrahent z faktury"),
      amountLabel: metadataString(metadata, ["invoice_amount_label", "gross_amount_label"], "Kwota w szczegółach faktury"),
      statusLabel: toLabel(metadataString(metadata, ["invoice_status_label", "invoice_status", "status_label"], ""), "Status nieznany"),
      href: `/faktury/${invoiceId}`,
    });
  });
  return Array.from(invoices.values()).slice(0, 8);
}

export function buildDocumentRelatedContractorRows(
  detail: KnowledgeDocumentDetail,
  workItems: WorkItemRecord[] = [],
): DocumentRelatedContractorRow[] {
  const contractors = new Map<number, DocumentRelatedContractorRow>();
  workItems.forEach((item) => {
    if (!workItemMatchesDocument(item, detail.knowledge_document_id)) {
      return;
    }
    const metadata = item.metadata ?? {};
    const contractorId = metadataNumber(metadata, ["contractor_id", "linked_contractor_id", "source_contractor_id"]);
    if (!contractorId || contractors.has(contractorId)) {
      return;
    }
    contractors.set(contractorId, {
      id: String(contractorId),
      contractorId,
      nameLabel: metadataString(metadata, ["contractor_name", "invoice_contractor_name", "customer_name"], `Kontrahent #${contractorId}`),
      contextLabel: metadataString(metadata, ["contractor_relation", "document_context"], "Powiązany przez sprawę lub fakturę."),
      href: `/crm/${contractorId}`,
    });
  });
  return Array.from(contractors.values()).slice(0, 8);
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
