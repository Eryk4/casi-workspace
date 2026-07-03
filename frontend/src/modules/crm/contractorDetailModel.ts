import { ApiContractError, ApiError } from "@/lib/api";
import type { DataViewErrorState, DataViewStatus } from "@/lib/types";
import {
  canUseCrmOrganizationScope,
  contractorStatusTone,
  type ContractorRecord,
  type ContractorViewRow,
} from "./crmModel";
import { buildWorkItemRows, type WorkItemRecord } from "../work-items/workItemsModel";

export type ContractorDetailStatus = DataViewStatus;

export type ContractorDetailErrorState = DataViewErrorState<ContractorDetailStatus>;

export type ContractorDetailFact = {
  label: string;
  value: string;
};

export type ContractorInvoiceRow = {
  id: string;
  numberLabel: string;
  statusLabel: string;
  amountLabel: string;
  dateLabel: string;
  href: string;
};

export type ContractorTaskRow = {
  id: string;
  titleLabel: string;
  statusLabel: string;
  dueLabel: string;
  href?: string;
};

export type ContractorWorkItemRow = {
  id: string;
  workItemId: number;
  titleLabel: string;
  statusLabel: string;
  priorityLabel: string;
  dueLabel: string;
  href: string;
};

export type ContractorDocumentRow = {
  id: string;
  titleLabel: string;
  statusLabel: string;
  contextLabel: string;
  href: string;
};

export type ContractorRelationshipSummary = {
  activeWorkItemsLabel: string;
  invoicesLabel: string;
  notesLabel: string;
  documentsLabel: string;
  lastActivityLabel: string;
  riskLabel: string;
};

export type ContractorNoteRecord = {
  id: string;
  contractorNoteId?: number;
  contractorId?: number;
  organizationId?: number;
  authorUserId?: number;
  authorLabel: string;
  dateLabel: string;
  noteText: string;
};

export type ContractorDetail = {
  contractor: ContractorRecord;
  invoices: ContractorInvoiceRow[];
  linkedTasks: ContractorTaskRow[];
  notes: ContractorNoteRecord[];
  workItems: ContractorWorkItemRow[];
  documents: ContractorDocumentRow[];
  safeNotes?: string | null;
};

export type ContractorNoteValidationResult =
  | {
      ok: true;
      payload: {
        note_text: string;
      };
    }
  | {
      ok: false;
      message: string;
    };

export type ContractorNoteErrorState = DataViewErrorState;

export type ContractorNoteSubmitResult =
  | {
      status: "success";
    }
  | {
      status: "blocked";
      message: string;
    }
  | {
      status: "ignored";
    }
  | {
      status: "error";
      errorState: ContractorNoteErrorState;
    };

export type ContractorNoteSubmitterDeps = {
  refreshDetail: () => Promise<void>;
  setSubmitting: (isSubmitting: boolean) => void;
  submitNote: (payload: { note_text: string }) => Promise<unknown>;
};

export const CONTRACTOR_DETAIL_ENDPOINT_PREFIX = "/contractors";
export const CONTRACTOR_NOTE_MAX_LENGTH = 2000;
export const CONTRACTOR_NOTE_ENDPOINT_SUFFIX = "/notes";
export const CONTRACTOR_NOTE_CREATE_ENABLED = true;
export const CONTRACTOR_DETAIL_READ_ONLY = true;
export const CONTRACTOR_DETAIL_CREATE_ENABLED = false;
export const CONTRACTOR_DETAIL_EDIT_ENABLED = false;
export const CONTRACTOR_DETAIL_DELETE_ENABLED = false;
export const CONTRACTOR_DETAIL_IMPORT_ENABLED = false;
export const CONTRACTOR_DETAIL_PIPELINE_ENABLED = false;
export const CONTRACTOR_DETAIL_ORGANIZATION_REQUIRED_TITLE = "Wybierz organizacje, aby zobaczyc kontrahenta";
export const CONTRACTOR_DETAIL_ORGANIZATION_REQUIRED_DESCRIPTION =
  "Wskaz organizacje w topbarze, zeby zobaczyc dane kontrahenta i powiazane sprawy.";

const UNSAFE_TEXT_PATTERNS = [
  /^[a-z]:\\/i,
  /^\\\\/,
  /^\/users\//i,
  /^\/home\//i,
  /\\users\\/i,
  /data[\\/]magazyn/i,
  /connection\s*string/i,
  /database_url/i,
  /postgres(ql)?:\/\//i,
  /secret/i,
  /token/i,
  /password/i,
  /api[_-]?key/i,
];

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
  if (typeof value === "boolean") {
    return value;
  }
  if (typeof value === "number") {
    return value === 1;
  }
  if (typeof value === "string") {
    const normalized = value.trim().toLowerCase();
    if (["1", "true", "tak", "yes"].includes(normalized)) {
      return true;
    }
    if (["0", "false", "nie", "no"].includes(normalized)) {
      return false;
    }
  }
  return undefined;
}

function readRecordArray(value: unknown): Record<string, unknown>[] {
  return Array.isArray(value) ? value.filter(isRecord) : [];
}

function isUnsafeText(value: string): boolean {
  return UNSAFE_TEXT_PATTERNS.some((pattern) => pattern.test(value.trim()));
}

export function safeContractorText(value: unknown, fallback = "-"): string {
  const nextValue = readOptionalString(value);
  if (!nextValue || isUnsafeText(nextValue)) {
    return fallback;
  }
  return nextValue;
}

function formatDateLabel(value: string | null | undefined, fallback = "Brak daty"): string {
  if (!value) {
    return fallback;
  }
  const [datePart, timePart] = value.replace("Z", "").split("T");
  return timePart ? `${datePart} ${timePart.slice(0, 5)}` : datePart || value;
}

function formatAmount(value: unknown, currency: unknown): string {
  const amount = readNumber(value);
  if (amount === undefined) {
    return "-";
  }
  const currencyLabel = safeContractorText(currency, "PLN");
  return `${amount.toLocaleString("pl-PL", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${currencyLabel}`;
}

function toLabel(value: string | undefined, fallback = "-"): string {
  if (!value) {
    return fallback;
  }
  return value.replace(/_/g, " ").replace(/^\w/, (character) => character.toUpperCase());
}

function readContractor(payload: unknown, fullPayload: unknown): ContractorRecord {
  if (!isRecord(payload)) {
    throw new ApiContractError(`${CONTRACTOR_DETAIL_ENDPOINT_PREFIX}/{id}`, fullPayload);
  }

  const contractorId = readNumber(payload.contractor_id);
  if (!contractorId) {
    throw new ApiContractError(`${CONTRACTOR_DETAIL_ENDPOINT_PREFIX}/{id}`, fullPayload);
  }

  return {
    contractor_id: contractorId,
    name: safeContractorText(payload.name, `Kontrahent #${contractorId}`),
    nip: safeContractorText(payload.nip, "") || null,
    email: safeContractorText(payload.email, "") || null,
    phone: safeContractorText(payload.phone, "") || null,
    is_new: readBoolean(payload.is_new),
    last_invoice_date: readOptionalString(payload.last_invoice_date) ?? null,
    last_invoice_number: safeContractorText(payload.last_invoice_number, "") || null,
    invoice_count: readNumber(payload.invoice_count) ?? 0,
    notes: safeContractorText(payload.notes, "") || null,
    organization_name: safeContractorText(payload.organization_name, "") || null,
    organization_slug: safeContractorText(payload.organization_slug, "") || null,
    created_at: readOptionalString(payload.created_at) ?? null,
    updated_at: readOptionalString(payload.updated_at) ?? null,
  };
}

function readInvoiceRow(item: Record<string, unknown>, index: number): ContractorInvoiceRow {
  const invoiceId = readNumber(item.invoice_id) ?? readNumber(item.id) ?? index + 1;
  return {
    id: String(invoiceId),
    numberLabel: safeContractorText(item.invoice_number ?? item.ksef_number, `Faktura #${invoiceId}`),
    statusLabel: safeContractorText(item.status, "Status nieznany"),
    amountLabel: formatAmount(item.gross_amount ?? item.total_amount ?? item.amount, item.currency),
    dateLabel: formatDateLabel(readOptionalString(item.issue_date) ?? readOptionalString(item.incoming_date) ?? null),
    href: `/faktury/${invoiceId}`,
  };
}

function readLinkedTaskRow(item: Record<string, unknown>, index: number): ContractorTaskRow {
  const taskId = readNumber(item.task_id) ?? readNumber(item.id) ?? index + 1;
  return {
    id: String(taskId),
    titleLabel: safeContractorText(item.title ?? item.task_title, `Zadanie #${taskId}`),
    statusLabel: safeContractorText(item.status_label ?? item.status, "Status nieznany"),
    dueLabel: formatDateLabel(readOptionalString(item.due_at) ?? readOptionalString(item.due_date) ?? null),
    href: "/asystent-szefa",
  };
}

export function contractorNoteEndpoint(contractorId: number | string): string {
  return `${CONTRACTOR_DETAIL_ENDPOINT_PREFIX}/${contractorId}${CONTRACTOR_NOTE_ENDPOINT_SUFFIX}`;
}

export function readContractorNote(item: unknown, index = 0): ContractorNoteRecord {
  if (!isRecord(item)) {
    throw new ApiContractError(`${CONTRACTOR_DETAIL_ENDPOINT_PREFIX}/{id}${CONTRACTOR_NOTE_ENDPOINT_SUFFIX}`, item);
  }

  const contractorNoteId = readNumber(item.contractor_note_id) ?? readNumber(item.id);
  const contractorId = readNumber(item.contractor_id);
  const organizationId = readNumber(item.organization_id);
  const authorUserId = readNumber(item.author_user_id);
  const authorLabel =
    safeContractorText(item.author_user_name, "") ||
    safeContractorText(item.author_name, "") ||
    (authorUserId ? `Uzytkownik #${authorUserId}` : "Operator");

  return {
    id: String(contractorNoteId ?? `${contractorId ?? "contractor"}-${index}`),
    contractorNoteId,
    contractorId,
    organizationId,
    authorUserId,
    authorLabel,
    dateLabel: formatDateLabel(readOptionalString(item.created_at) ?? null, "Brak daty"),
    noteText: safeContractorText(item.note_text, "Ukryto techniczna lub wrazliwa tresc notatki."),
  };
}

export function readContractorDetail(payload: unknown, requestedContractorId?: number): ContractorDetail {
  if (!isRecord(payload) || !isRecord(payload.contractor)) {
    throw new ApiContractError(`${CONTRACTOR_DETAIL_ENDPOINT_PREFIX}/{id}`, payload);
  }

  const contractor = readContractor(payload.contractor, payload);
  if (requestedContractorId && contractor.contractor_id !== requestedContractorId) {
    throw new ApiContractError(`${CONTRACTOR_DETAIL_ENDPOINT_PREFIX}/{id}`, payload);
  }

  return {
    contractor,
    invoices: readRecordArray(payload.invoices).map(readInvoiceRow),
    linkedTasks: readRecordArray(payload.linked_tasks).map(readLinkedTaskRow),
    notes: readRecordArray(payload.notes).map(readContractorNote),
    workItems: [],
    documents: [],
    safeNotes: contractor.notes,
  };
}

export function getContractorDetailTitle(detail: ContractorDetail | null, requestedContractorId: number): string {
  return detail?.contractor.name || `Kontrahent #${requestedContractorId}`;
}

export function getContractorStatusTone(contractor: ContractorRecord): ContractorViewRow["statusTone"] {
  return contractorStatusTone(contractor);
}

export function buildContractorDetailFacts(detail: ContractorDetail): ContractorDetailFact[] {
  const contractor = detail.contractor;
  return [
    { label: "Status", value: contractor.is_new ? "Nowy" : (contractor.invoice_count ?? 0) > 0 ? "Powiazany" : "Katalog" },
    { label: "NIP", value: safeContractorText(contractor.nip, "Brak NIP") },
    { label: "E-mail", value: safeContractorText(contractor.email, "Brak e-maila") },
    { label: "Telefon", value: safeContractorText(contractor.phone, "Brak telefonu") },
    { label: "Organizacja", value: safeContractorText(contractor.organization_name, "Organizacja nieznana") },
    { label: "Faktury", value: String(contractor.invoice_count ?? detail.invoices.length) },
    {
      label: "Ostatnia faktura",
      value: contractor.last_invoice_number
        ? `${contractor.last_invoice_number} - ${formatDateLabel(contractor.last_invoice_date, "brak daty")}`
        : formatDateLabel(contractor.last_invoice_date, "Brak faktur"),
    },
    { label: "Utworzono", value: formatDateLabel(contractor.created_at) },
    { label: "Aktualizacja", value: formatDateLabel(contractor.updated_at || contractor.created_at, "Brak aktualizacji") },
  ];
}

export function buildContractorInvoiceRows(detail: ContractorDetail): ContractorInvoiceRow[] {
  return detail.invoices;
}

export function buildContractorTaskRows(detail: ContractorDetail): ContractorTaskRow[] {
  return detail.linkedTasks;
}

export function buildContractorWorkItemRows(detail: ContractorDetail): ContractorWorkItemRow[] {
  return detail.workItems;
}

export function buildContractorDocumentRows(detail: ContractorDetail): ContractorDocumentRow[] {
  return detail.documents;
}

export function buildContractorNoteRows(detail: ContractorDetail): ContractorNoteRecord[] {
  return detail.notes;
}

export function enrichContractorDetailWithWorkItems(
  detail: ContractorDetail,
  workItems: WorkItemRecord[],
): ContractorDetail {
  const contractorId = detail.contractor.contractor_id;
  const relatedWorkItems = buildWorkItemRows(
    workItems.filter((item) => Number(item.metadata?.contractor_id ?? item.metadata?.linked_contractor_id ?? 0) === contractorId),
  ).map((row) => ({
    id: row.id,
    workItemId: row.workItemId,
    titleLabel: safeContractorText(row.title, `Sprawa #${row.workItemId}`),
    statusLabel: row.statusLabel,
    priorityLabel: row.priorityLabel,
    dueLabel: row.dueLabel,
    href: `/work-items/${row.workItemId}`,
  }));
  return {
    ...detail,
    workItems: relatedWorkItems,
    documents: buildContractorDocumentsFromWorkItems(workItems, contractorId),
  };
}

function buildContractorDocumentsFromWorkItems(workItems: WorkItemRecord[], contractorId: number): ContractorDocumentRow[] {
  const documents = new Map<number, ContractorDocumentRow>();
  workItems.forEach((item) => {
    if (Number(item.metadata?.contractor_id ?? item.metadata?.linked_contractor_id ?? 0) !== contractorId) {
      return;
    }
    const ids = Array.isArray(item.metadata?.knowledge_document_ids) ? item.metadata?.knowledge_document_ids : [];
    ids.forEach((rawId) => {
      const documentId = readNumber(rawId);
      if (!documentId || documents.has(documentId)) {
        return;
      }
      documents.set(documentId, {
        id: String(documentId),
        titleLabel: safeContractorText(item.metadata?.document_title, `Dokument #${documentId}`),
        statusLabel: safeContractorText(item.metadata?.document_folder, "Baza wiedzy"),
        contextLabel: safeContractorText(item.metadata?.document_context, "Dokument powiazany przez sprawe kontrahenta."),
        href: `/dokumenty/${documentId}`,
      });
    });
  });
  return Array.from(documents.values());
}

export function buildContractorRelationshipSummary(detail: ContractorDetail): ContractorRelationshipSummary {
  const invoiceCount = detail.invoices.length || detail.contractor.invoice_count || 0;
  const riskReasons = [
    detail.workItems.length > 0 ? `${detail.workItems.length} otwartych spraw` : "",
    detail.contractor.is_new ? "nowy kontrahent" : "",
    !detail.contractor.email && !detail.contractor.phone ? "brak danych kontaktowych" : "",
  ].filter(Boolean);

  return {
    activeWorkItemsLabel: `${detail.workItems.length} spraw`,
    invoicesLabel: `${invoiceCount} faktur`,
    notesLabel: `${detail.notes.length} notatek`,
    documentsLabel: `${detail.documents.length} dokumentow`,
    lastActivityLabel: formatDateLabel(detail.contractor.updated_at || detail.contractor.last_invoice_date || null, "Brak aktywnosci"),
    riskLabel: riskReasons.length ? riskReasons.join(" - ") : "Brak pilnych sygnalow",
  };
}

export function getContractorTypeLabel(contractor: ContractorRecord): string {
  if (contractor.is_new) {
    return "Nowy kontrahent";
  }
  if ((contractor.invoice_count ?? 0) > 0) {
    return "Kontrahent z fakturami";
  }
  return "Rekord katalogowy";
}

export function canRenderContractorDetail(status: ContractorDetailStatus, detail: ContractorDetail | null): boolean {
  return status === "ready" && Boolean(detail);
}

export function isContractorDetailEmpty(status: ContractorDetailStatus, detail: ContractorDetail | null): boolean {
  return status === "ready" && !detail;
}

export function canUseContractorDetailOrganizationScope(organizationId: string | number | null | undefined): boolean {
  return canUseCrmOrganizationScope(organizationId);
}

export function buildContractorNoteRequest(
  noteText: string,
  organizationId: string | number | null | undefined,
): ContractorNoteValidationResult {
  if (!canUseContractorDetailOrganizationScope(organizationId)) {
    return {
      ok: false,
      message: CONTRACTOR_DETAIL_ORGANIZATION_REQUIRED_TITLE,
    };
  }

  const trimmedNote = noteText.trim();

  if (!trimmedNote) {
    return {
      ok: false,
      message: "Notatka nie moze byc pusta.",
    };
  }

  if (trimmedNote.length > CONTRACTOR_NOTE_MAX_LENGTH) {
    return {
      ok: false,
      message: `Notatka moze miec maksymalnie ${CONTRACTOR_NOTE_MAX_LENGTH} znakow.`,
    };
  }

  return {
    ok: true,
    payload: {
      note_text: trimmedNote,
    },
  };
}

export function getContractorDetailErrorState(error: unknown): ContractorDetailErrorState {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      return {
        status: "unauthenticated",
        title: "Sesja wygasla",
        description: "Zaloguj sie ponownie, aby zobaczyc szczegol kontrahenta.",
      };
    }
    if (error.status === 403) {
      return {
        status: "forbidden",
        title: "Brak dostepu do kontrahenta",
        description: "Twoje konto nie ma uprawnien do odczytu tego kontrahenta.",
      };
    }
    if (error.status === 404) {
      return {
        status: "error",
        title: "Nie znaleziono kontrahenta",
        description: "Backend nie znalazl kontrahenta w wybranej organizacji albo rekord zostal usuniety.",
      };
    }
    if (error.status >= 500) {
      return {
        status: "server-error",
        title: "Backend nie zwrocil kontrahenta",
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
      title: "Niepoprawny format kontrahenta",
      description: "Backend odpowiedzial, ale dane nie pasuja do minimalnego kontraktu szczegolu kontrahenta.",
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
    title: "Nie udalo sie pobrac kontrahenta",
    description: error instanceof Error ? error.message : "Wystapil nieznany blad pobierania kontrahenta.",
  };
}

export function getContractorNoteErrorState(error: unknown): ContractorNoteErrorState {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      return {
        status: "unauthenticated",
        title: "Sesja wygasla",
        description: "Zaloguj sie ponownie, aby dodac notatke CRM.",
      };
    }

    if (error.status === 403) {
      return {
        status: "forbidden",
        title: "Brak uprawnien do notatki",
        description: "Twoje konto nie ma uprawnien do dodawania notatek dla tego kontrahenta.",
      };
    }

    if (error.status === 404) {
      return {
        status: "error",
        title: "Nie znaleziono kontrahenta",
        description: "Notatka nie zostala zapisana, bo backend nie znalazl kontrahenta w wybranej organizacji.",
      };
    }

    if (error.status >= 500) {
      return {
        status: "server-error",
        title: "Backend nie zapisal notatki",
        description: "Wystapil blad serwera. Notatka nie jest traktowana jako zapisana bez potwierdzenia backendu.",
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
      title: "Niepoprawny format notatki",
      description: "Backend odpowiedzial, ale zapisana notatka nie pasuje do oczekiwanego kontraktu.",
    };
  }

  if (error instanceof TypeError) {
    return {
      status: "error",
      title: "Problem z polaczeniem z API",
      description: "Nie udalo sie polaczyc z backendem. Notatka nie zostala potwierdzona.",
    };
  }

  return {
    status: "error",
    title: "Nie udalo sie dodac notatki",
    description: error instanceof Error ? error.message : "Wystapil nieznany blad dodawania notatki CRM.",
  };
}

export function createContractorNoteSubmitter(deps: ContractorNoteSubmitterDeps) {
  let inFlight = false;

  return async function submitContractorNote(
    validation: ContractorNoteValidationResult,
  ): Promise<ContractorNoteSubmitResult> {
    if (!validation.ok) {
      return {
        status: "blocked",
        message: validation.message,
      };
    }

    if (inFlight) {
      return { status: "ignored" };
    }

    inFlight = true;
    deps.setSubmitting(true);

    try {
      await deps.submitNote(validation.payload);
      await deps.refreshDetail();
      return { status: "success" };
    } catch (error) {
      return {
        status: "error",
        errorState: getContractorNoteErrorState(error),
      };
    } finally {
      inFlight = false;
      deps.setSubmitting(false);
    }
  };
}
