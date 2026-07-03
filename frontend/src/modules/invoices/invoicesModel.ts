import { ApiContractError, ApiError } from "../../lib/api";
import type {
  ApiRequestMethod,
  DataViewErrorState,
  DataViewStatus,
  InvoiceVerificationInbox,
  InvoiceVerificationItem,
  InvoiceVerificationSection,
} from "../../lib/types";
import { formatCurrency, formatDate } from "../../lib/utils";

import type { InvoiceCommentPayload, InvoiceDetail, InvoiceRecord } from "./types";
import type { InvoiceActionKind, InvoiceActionPayload, InvoiceActionRequest } from "./types";

export type InvoicesStatus = DataViewStatus;

export type InvoicesErrorState = DataViewErrorState<InvoicesStatus>;

export type InvoiceStatusTone = "warning" | "danger" | "neutral";

export const INVOICE_INBOX_ENDPOINT = "/invoices/verification-inbox";
export const INVOICE_INBOX_MUTATION_METHODS: ReadonlyArray<Exclude<ApiRequestMethod, "GET">> = [];
export const INVOICE_DETAIL_MUTATION_METHODS: ReadonlyArray<Exclude<ApiRequestMethod, "GET">> = [];
export const INVOICE_COMMENT_MUTATION_METHODS: ReadonlyArray<Exclude<ApiRequestMethod, "GET">> = ["POST"];
export const INVOICE_COMMENT_MAX_LENGTH = 2000;
export const INVOICES_ORGANIZATION_REQUIRED_TITLE = "Wybierz organizacje, aby zobaczyc faktury";
export const INVOICES_ORGANIZATION_REQUIRED_DESCRIPTION =
  "Globalny uzytkownik musi najpierw wskazac organizacje w topbarze. Dopiero wtedy frontend przekaze organization_id do endpointow faktur.";
export const INVOICE_DETAIL_ORGANIZATION_REQUIRED_TITLE = "Wybierz organizacje, aby zobaczyc fakture";
export const INVOICE_DETAIL_ORGANIZATION_REQUIRED_DESCRIPTION =
  "Szczegoly faktury sa pobierane w kontekscie organizacji, zeby nie pokazywac danych z niejednoznacznego zakresu.";

export type InvoiceDetailStatus = DataViewStatus;

export type InvoiceDetailErrorState = DataViewErrorState<InvoiceDetailStatus>;

export type InvoiceDetailFact = {
  label: string;
  value: string;
};

export type InvoiceDetailEvent = {
  id: string;
  type: string;
  actor: string;
  date: string;
  description: string;
};

export type InvoiceDetailTraceItem = {
  label: string;
  value: string;
  description: string;
};

export type InvoiceActionDefinition = {
  action: InvoiceActionKind;
  label: string;
  tone: "neutral" | "warning" | "danger";
  requiresReason: boolean;
  requiresHandoffTarget: boolean;
  requiresConfirmation: boolean;
  successMessage: string;
  confirmationEffect: string;
};

export type InvoiceActionInput = {
  reason?: string;
  handoffTarget?: string;
  handoffNote?: string;
};

export type InvoiceActionValidationResult =
  | {
      ok: true;
      request: InvoiceActionRequest;
    }
  | {
      ok: false;
      message: string;
    };

export type InvoiceActionErrorState = DataViewErrorState;

export type InvoiceActionConfirmation = {
  actionLabel: string;
  invoiceTitle: string;
  invoiceNumber: string;
  contractor: string;
  effect: string;
};

export type InvoiceActionSubmitResult =
  | {
      status: "success";
    }
  | {
      status: "error";
      errorState: InvoiceActionErrorState;
    }
  | {
      status: "ignored";
    };

export type InvoiceActionSubmitterDeps = {
  refreshDetail: () => Promise<void>;
  setSubmittingAction: (action: InvoiceActionKind | null) => void;
  submitAction: (request: InvoiceActionRequest) => Promise<unknown>;
};

export type InvoiceCommentValidationResult =
  | {
      ok: true;
      payload: InvoiceCommentPayload;
    }
  | {
      ok: false;
      message: string;
    };

export type InvoiceCommentErrorState = DataViewErrorState;

export type InvoiceCommentSubmitResult =
  | {
      status: "success";
    }
  | {
      status: "error";
      errorState: InvoiceCommentErrorState;
    }
  | {
      status: "blocked";
      message: string;
    }
  | {
      status: "ignored";
    };

export type InvoiceCommentSubmitterDeps = {
  refreshDetail: () => Promise<void>;
  setSubmitting: (submitting: boolean) => void;
  submitComment: (payload: InvoiceCommentPayload) => Promise<unknown>;
};

export const INVOICE_ACTION_DEFINITIONS: Record<InvoiceActionKind, InvoiceActionDefinition> = {
  "confirm-duplicate": {
    action: "confirm-duplicate",
    label: "Potwierdz duplikat",
    tone: "danger",
    requiresReason: false,
    requiresHandoffTarget: false,
    requiresConfirmation: true,
    successMessage: "Duplikat zostal potwierdzony.",
    confirmationEffect: "Faktura zostanie oznaczona jako pewny duplikat.",
  },
  "reject-duplicate": {
    action: "reject-duplicate",
    label: "Odrzuc duplikat",
    tone: "warning",
    requiresReason: false,
    requiresHandoffTarget: false,
    requiresConfirmation: true,
    successMessage: "Faktura wrocila do dalszej weryfikacji.",
    confirmationEffect: "Oznaczenie duplikatu zostanie odrzucone, a faktura wroci do dalszej weryfikacji.",
  },
  "mark-ready": {
    action: "mark-ready",
    label: "Oznacz jako gotowa",
    tone: "neutral",
    requiresReason: false,
    requiresHandoffTarget: true,
    requiresConfirmation: true,
    successMessage: "Faktura zostala oznaczona jako gotowa do przekazania.",
    confirmationEffect: "Faktura zostanie oznaczona jako gotowa do przekazania wskazanemu odbiorcy.",
  },
  handoff: {
    action: "handoff",
    label: "Przekaz dalej",
    tone: "neutral",
    requiresReason: false,
    requiresHandoffTarget: true,
    requiresConfirmation: true,
    successMessage: "Faktura zostala przekazana dalej.",
    confirmationEffect: "Faktura zostanie przekazana do wskazanego odbiorcy.",
  },
  "undo-last": {
    action: "undo-last",
    label: "Cofnij ostatnia decyzje",
    tone: "warning",
    requiresReason: false,
    requiresHandoffTarget: false,
    requiresConfirmation: true,
    successMessage: "Ostatnia decyzja faktury zostala cofnieta.",
    confirmationEffect: "Ostatnia decyzja workflow zostanie cofnieta zgodnie z historia faktury.",
  },
  reopen: {
    action: "reopen",
    label: "Otworz ponownie",
    tone: "warning",
    requiresReason: true,
    requiresHandoffTarget: false,
    requiresConfirmation: true,
    successMessage: "Faktura zostala ponownie otwarta.",
    confirmationEffect: "Faktura zostanie ponownie otwarta do pracy, a powod trafi do historii.",
  },
  close: {
    action: "close",
    label: "Zamknij fakture",
    tone: "danger",
    requiresReason: true,
    requiresHandoffTarget: false,
    requiresConfirmation: true,
    successMessage: "Faktura zostala zamknieta.",
    confirmationEffect: "Faktura zostanie zamknieta jako zakonczona, a powod trafi do historii.",
  },
};

const amountFormatter = new Intl.NumberFormat("pl-PL", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

export function getInvoicesErrorState(error: unknown): InvoicesErrorState {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      return {
        status: "unauthenticated",
        title: "Sesja wygasla",
        description: "Zaloguj sie ponownie, aby zobaczyc inbox weryfikacji faktur.",
      };
    }

    if (error.status === 403) {
      return {
        status: "forbidden",
        title: "Brak dostepu do faktur",
        description: "Twoje konto nie ma uprawnien do odczytu inboxu weryfikacji.",
      };
    }

    if (error.status >= 500) {
      return {
        status: "server-error",
        title: "Backend nie zwrocil inboxu faktur",
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
      title: "Niepoprawny format inboxu faktur",
      description: "Backend odpowiedzial, ale dane nie pasuja do kontraktu widoku faktur.",
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
    title: "Nie udalo sie pobrac faktur",
    description: error instanceof Error ? error.message : "Wystapil nieznany blad pobierania inboxu faktur.",
  };
}

export function getInvoiceDetailErrorState(error: unknown): InvoiceDetailErrorState {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      return {
        status: "unauthenticated",
        title: "Sesja wygasla",
        description: "Zaloguj sie ponownie, aby zobaczyc szczegoly faktury.",
      };
    }

    if (error.status === 403) {
      return {
        status: "forbidden",
        title: "Brak dostepu do faktury",
        description: "Twoje konto nie ma uprawnien do odczytu szczegolow tej faktury.",
      };
    }

    if (error.status >= 500) {
      return {
        status: "server-error",
        title: "Backend nie zwrocil szczegolow faktury",
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
      title: "Niepoprawny format szczegolow faktury",
      description: "Backend odpowiedzial, ale dane nie pasuja do kontraktu szczegolow faktury.",
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
    title: "Nie udalo sie pobrac szczegolow faktury",
    description: error instanceof Error ? error.message : "Wystapil nieznany blad pobierania szczegolow faktury.",
  };
}

export function getInvoiceActionErrorState(error: unknown): InvoiceActionErrorState {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      return {
        status: "unauthenticated",
        title: "Sesja wygasla",
        description: "Zaloguj sie ponownie, aby wykonac akcje na fakturze.",
      };
    }

    if (error.status === 403) {
      return {
        status: "forbidden",
        title: "Brak uprawnien do akcji",
        description: "Twoje konto nie ma uprawnien do wykonania tej decyzji na fakturze.",
      };
    }

    if (error.status >= 500) {
      return {
        status: "server-error",
        title: "Backend nie wykonal akcji faktury",
        description: "Wystapil blad serwera. Nie zakladaj, ze decyzja zostala zapisana bez ponownego odczytu faktury.",
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
      title: "Niepoprawny format odpowiedzi po akcji",
      description: "Backend odpowiedzial, ale wynik akcji faktury nie pasuje do oczekiwanego kontraktu.",
    };
  }

  if (error instanceof TypeError) {
    return {
      status: "error",
      title: "Problem z polaczeniem z API",
      description: "Nie udalo sie polaczyc z backendem. Przed ponowieniem sprawdz aktualny stan faktury.",
    };
  }

  return {
    status: "error",
    title: "Nie udalo sie wykonac akcji faktury",
    description: error instanceof Error ? error.message : "Wystapil nieznany blad akcji faktury.",
  };
}

export function getInvoiceCommentErrorState(error: unknown): InvoiceCommentErrorState {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      return {
        status: "unauthenticated",
        title: "Sesja wygasla",
        description: "Zaloguj sie ponownie, aby dodac komentarz do faktury.",
      };
    }

    if (error.status === 403) {
      return {
        status: "forbidden",
        title: "Brak uprawnien do komentarza",
        description: "Twoje konto nie ma uprawnien do komentowania tej faktury.",
      };
    }

    if (error.status >= 500) {
      return {
        status: "server-error",
        title: "Backend nie zapisal komentarza",
        description: "Wystapil blad serwera. Komentarz nie jest traktowany jako zapisany bez potwierdzenia backendu.",
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
      title: "Niepoprawny format komentarza",
      description: "Backend odpowiedzial, ale zapisany komentarz nie pasuje do oczekiwanego kontraktu.",
    };
  }

  if (error instanceof TypeError) {
    return {
      status: "error",
      title: "Problem z polaczeniem z API",
      description: "Nie udalo sie polaczyc z backendem. Komentarz nie zostal potwierdzony.",
    };
  }

  return {
    status: "error",
    title: "Nie udalo sie dodac komentarza",
    description: error instanceof Error ? error.message : "Wystapil nieznany blad dodawania komentarza.",
  };
}

export function getInboxSections(inbox: InvoiceVerificationInbox | null): InvoiceVerificationSection[] {
  return inbox ? Object.values(inbox.sections) : [];
}

export function flattenInboxItems(inbox: InvoiceVerificationInbox | null): InvoiceVerificationItem[] {
  return getInboxSections(inbox).flatMap((section) => section.items);
}

export function hasInvoiceInboxData(status: InvoicesStatus, inbox: InvoiceVerificationInbox | null): boolean {
  return status === "ready" && flattenInboxItems(inbox).length > 0;
}

export function isInvoiceInboxEmpty(status: InvoicesStatus, inbox: InvoiceVerificationInbox | null): boolean {
  return status === "ready" && Boolean(inbox) && flattenInboxItems(inbox).length === 0;
}

export function formatInvoiceAmount(row: InvoiceVerificationItem): string {
  return `${amountFormatter.format(row.gross_amount ?? 0)} ${row.currency || "PLN"}`;
}

export function invoiceStatusTone(row: InvoiceVerificationItem): InvoiceStatusTone {
  if (row.duplicate_type === "brak") {
    return "warning";
  }

  return row.duplicate_type ? "danger" : "neutral";
}

export function isInvoiceInboxReadOnly(): boolean {
  return INVOICE_INBOX_MUTATION_METHODS.length === 0;
}

export function isInvoiceDetailReadOnly(): boolean {
  return INVOICE_DETAIL_MUTATION_METHODS.length === 0;
}

export function canUseInvoicesOrganizationScope(organizationId: string | number | null | undefined): boolean {
  return organizationId !== null && organizationId !== undefined && String(organizationId).trim().length > 0;
}

export function readDisplayString(value: unknown, fallback = "-"): string {
  if (typeof value === "string" && value.trim()) {
    return value;
  }

  if (typeof value === "number") {
    return String(value);
  }

  return fallback;
}

export function isUnsafeTechnicalValue(value: unknown): boolean {
  if (typeof value !== "string") {
    return false;
  }

  const normalizedValue = value.trim();

  if (!normalizedValue) {
    return false;
  }

  return (
    /^[A-Za-z]:[\\/]/.test(normalizedValue) ||
    normalizedValue.includes("C:\\Users\\") ||
    normalizedValue.includes("data/magazyn") ||
    normalizedValue.includes("postgres://") ||
    normalizedValue.includes("postgresql://") ||
    normalizedValue.includes("://") ||
    normalizedValue.includes("\\")
  );
}

export function readSafeDisplayString(value: unknown, fallback = "-"): string {
  if (isUnsafeTechnicalValue(value)) {
    return fallback;
  }

  return readDisplayString(value, fallback);
}

export function getInvoiceRecordId(invoice: InvoiceRecord): number | null {
  return invoice.id ?? invoice.invoice_id ?? null;
}

export function getInvoiceDetailHref(invoiceId: number | string | null | undefined): string | null {
  if (invoiceId === null || invoiceId === undefined) {
    return null;
  }

  const normalizedInvoiceId = String(invoiceId).trim();

  return normalizedInvoiceId ? `/faktury/${normalizedInvoiceId}` : null;
}

export function getInvoiceDetailTitle(detail: InvoiceDetail | null, requestedInvoiceId: number): string {
  const invoice = detail?.invoice;
  const resolvedInvoiceId = invoice ? getInvoiceRecordId(invoice) : requestedInvoiceId;

  return invoice?.invoice_number || invoice?.ksef_number || `Faktura #${resolvedInvoiceId}`;
}

export function buildInvoiceDetailFacts(invoice: InvoiceRecord): InvoiceDetailFact[] {
  return [
    { label: "Kontrahent", value: invoice.issuer_name || invoice.contractor_name || "-" },
    { label: "NIP", value: invoice.issuer_nip || "-" },
    { label: "Kwota brutto", value: formatCurrency(invoice.gross_amount, invoice.currency || "PLN") },
    { label: "Data wplywu", value: formatDate(invoice.incoming_date) },
    { label: "Data wystawienia", value: formatDate(invoice.issue_date) },
    { label: "Zrodlo", value: invoice.source || "-" },
    { label: "Organizacja", value: invoice.organization_name || "-" },
    { label: "Operator", value: invoice.assigned_user_name || "Nieprzypisane" },
  ];
}

export function buildInvoiceHistoryEvents(detail: InvoiceDetail | null): InvoiceDetailEvent[] {
  const history = detail?.history ?? [];

  return history.slice(0, 8).map((event, index) => ({
    id: `history-${readDisplayString(event.id, String(index))}`,
    type: readDisplayString(event.event_type, "Historia"),
    actor: readDisplayString(event.actor, "System"),
    date: formatDate(readDisplayString(event.event_time, "")),
    description: readDisplayString(event.decision_reason || event.description || event.details, "Zdarzenie operacyjne"),
  }));
}

export function buildInvoiceCommentEvents(detail: InvoiceDetail | null): InvoiceDetailEvent[] {
  const comments = detail?.comments ?? [];

  return comments.slice(0, 6).map((comment, index) => ({
    id: `comment-${readDisplayString(comment.invoice_comment_id || comment.comment_id || comment.id, String(index))}`,
    type: "Komentarz operatora",
    actor: readDisplayString(comment.author_name || comment.created_by_name || comment.created_by_user_name, "Uzytkownik"),
    date: formatDate(readDisplayString(comment.created_at, "")),
    description: readDisplayString(comment.body || comment.comment || comment.note_text, "Komentarz bez tresci"),
  }));
}

export function buildInvoiceDetailEvents(detail: InvoiceDetail | null): InvoiceDetailEvent[] {
  return [...buildInvoiceHistoryEvents(detail), ...buildInvoiceCommentEvents(detail)];
}

export function buildInvoiceDocumentTraceItems(detail: InvoiceDetail | null): InvoiceDetailTraceItem[] {
  const invoice = detail?.invoice;
  const documentTrace = detail?.document_trace ?? {};
  const sourceTrace = detail?.source_trace ?? {};
  const hasOcrTrace = Boolean(documentTrace.ocr_storage_key || documentTrace.ocr_link);
  const ocrConfidence = readDisplayString(documentTrace.ocr_confidence, "-");

  return [
    {
      label: "Plik",
      value: readSafeDisplayString(documentTrace.file_name || invoice?.file_name, "Plik zarejestrowany"),
      description: `Storage: ${readSafeDisplayString(documentTrace.storage_backend, "ukryty")}`,
    },
    {
      label: "OCR",
      value: hasOcrTrace ? "Slad OCR dostepny" : "Brak sladu OCR",
      description: `Pewnosc: ${ocrConfidence}`,
    },
    {
      label: "Zrodlo",
      value: readSafeDisplayString(sourceTrace.source || invoice?.source, "Zrodlo nieokreslone"),
      description: readSafeDisplayString(sourceTrace.source_external_id || sourceTrace.message_id, "Brak zewnetrznego ID"),
    },
  ];
}

export function canRenderInvoiceDetailData(status: InvoiceDetailStatus, detail: InvoiceDetail | null): boolean {
  return status === "ready" && Boolean(detail?.invoice);
}

export function isInvoiceDetailEmpty(status: InvoiceDetailStatus, detail: InvoiceDetail | null): boolean {
  return status === "ready" && !detail?.invoice;
}

export function getInvoiceActionDefinition(action: InvoiceActionKind): InvoiceActionDefinition {
  return INVOICE_ACTION_DEFINITIONS[action];
}

export function buildInvoiceActionRequest(
  action: InvoiceActionKind,
  input: InvoiceActionInput = {},
): InvoiceActionValidationResult {
  const definition = getInvoiceActionDefinition(action);
  const reason = input.reason?.trim();
  const handoffTarget = input.handoffTarget?.trim();
  const handoffNote = input.handoffNote?.trim();

  if (definition.requiresReason && !reason) {
    return {
      ok: false,
      message: "Podaj powod decyzji przed wykonaniem tej akcji.",
    };
  }

  if (definition.requiresHandoffTarget && !handoffTarget) {
    return {
      ok: false,
      message: "Podaj cel przekazania faktury przed wykonaniem tej akcji.",
    };
  }

  const payload: InvoiceActionPayload = {};

  if (reason) {
    payload.reason = reason;
  }

  if (handoffTarget) {
    payload.handoff_target = handoffTarget;
  }

  if (handoffNote) {
    payload.handoff_note = handoffNote;
  }

  return {
    ok: true,
    request: {
      action,
      payload: Object.keys(payload).length ? payload : undefined,
    },
  };
}

export function buildInvoiceCommentRequest(
  noteText: string,
  organizationId: string | number | null | undefined,
): InvoiceCommentValidationResult {
  if (!canUseInvoicesOrganizationScope(organizationId)) {
    return {
      ok: false,
      message: INVOICE_DETAIL_ORGANIZATION_REQUIRED_TITLE,
    };
  }

  const trimmedNote = noteText.trim();

  if (!trimmedNote) {
    return {
      ok: false,
      message: "Komentarz nie moze byc pusty.",
    };
  }

  if (trimmedNote.length > INVOICE_COMMENT_MAX_LENGTH) {
    return {
      ok: false,
      message: `Komentarz moze miec maksymalnie ${INVOICE_COMMENT_MAX_LENGTH} znakow.`,
    };
  }

  return {
    ok: true,
    payload: {
      note_text: trimmedNote,
    },
  };
}

export function requiresInvoiceActionConfirmation(action: InvoiceActionKind): boolean {
  return getInvoiceActionDefinition(action).requiresConfirmation;
}

export function buildInvoiceActionConfirmation(
  detail: InvoiceDetail,
  action: InvoiceActionKind,
): InvoiceActionConfirmation {
  const definition = getInvoiceActionDefinition(action);
  const invoice = detail.invoice;

  return {
    actionLabel: definition.label,
    invoiceTitle: getInvoiceDetailTitle(detail, getInvoiceRecordId(invoice) ?? 0),
    invoiceNumber: invoice.invoice_number || invoice.ksef_number || `#${getInvoiceRecordId(invoice) ?? "-"}`,
    contractor: invoice.issuer_name || invoice.contractor_name || "Brak nazwy kontrahenta",
    effect: definition.confirmationEffect,
  };
}

export function createInvoiceActionSubmitter(deps: InvoiceActionSubmitterDeps) {
  let inFlight = false;

  return async function submitInvoiceAction(request: InvoiceActionRequest): Promise<InvoiceActionSubmitResult> {
    if (inFlight) {
      return { status: "ignored" };
    }

    inFlight = true;
    deps.setSubmittingAction(request.action);

    try {
      await deps.submitAction(request);
      await deps.refreshDetail();
      return { status: "success" };
    } catch (error) {
      return {
        status: "error",
        errorState: getInvoiceActionErrorState(error),
      };
    } finally {
      inFlight = false;
      deps.setSubmittingAction(null);
    }
  };
}

export function createInvoiceCommentSubmitter(deps: InvoiceCommentSubmitterDeps) {
  let inFlight = false;

  return async function submitInvoiceComment(
    validation: InvoiceCommentValidationResult,
  ): Promise<InvoiceCommentSubmitResult> {
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
      await deps.submitComment(validation.payload);
      await deps.refreshDetail();
      return { status: "success" };
    } catch (error) {
      return {
        status: "error",
        errorState: getInvoiceCommentErrorState(error),
      };
    } finally {
      inFlight = false;
      deps.setSubmitting(false);
    }
  };
}
