import { invoiceActionEndpoint } from "./api";
import { INVOICE_ACTION_DEFINITIONS } from "./invoicesModel";
import type { InvoiceActionKind, InvoiceDetail } from "./types";

// Frontend-only preview model.
// It helps users understand which decisions may become available, but it is not
// a business authority. The backend must validate and decide every future action.
export type InvoiceDecisionAvailability = "preview-ready" | "blocked";

export type InvoiceDecisionAction = {
  action: InvoiceActionKind;
  label: string;
  description: string;
  availability: InvoiceDecisionAvailability;
  reason: string;
  requiresReason: boolean;
  requiresHandoffTarget: boolean;
  requiresConfirmation: boolean;
  futureEndpoint: string;
  futureEndpointLabel: string;
};

const DEFAULT_DECISION_ORDER: InvoiceActionKind[] = [
  "mark-ready",
  "confirm-duplicate",
  "reject-duplicate",
  "handoff",
  "undo-last",
  "reopen",
  "close",
];

function normalize(value: unknown): string {
  return String(value ?? "").trim().toLowerCase();
}

function getInvoiceId(detail: InvoiceDetail): number {
  return Number(detail.invoice.id ?? detail.invoice.invoice_id ?? 0);
}

function hasOpenApprovalRequests(detail: InvoiceDetail): boolean {
  return (detail.approval_requests ?? []).some((request) => {
    const status = normalize(request.status ?? request.workflow_status ?? request.state);
    return !status || ["open", "pending", "oczekuje", "weryfikacja"].includes(status);
  });
}

function hasBlockingExceptions(detail: InvoiceDetail): boolean {
  return (detail.exceptions ?? []).length > 0;
}

function resolveActionReason(detail: InvoiceDetail, action: InvoiceActionKind): string {
  const invoice = detail.invoice;
  const status = normalize(invoice.status);
  const workflowState = normalize(invoice.workflow_state ?? detail.workflow?.state);
  const duplicateType = normalize(invoice.duplicate_type);

  if (!getInvoiceId(detail)) {
    return "Brak stabilnego identyfikatora faktury.";
  }

  if (action === "confirm-duplicate" && !["podejrzenie", "pewny"].includes(duplicateType)) {
    return "Ta faktura nie jest teraz oznaczona jako duplikat, wiec nie ma czego potwierdzac.";
  }

  if (action === "reject-duplicate" && !["podejrzenie", "pewny"].includes(duplicateType)) {
    return "Ta faktura nie ma aktywnego oznaczenia duplikatu do odrzucenia.";
  }

  if (action === "mark-ready") {
    if (status !== "weryfikacja" && workflowState !== "w_pracy") {
      return "Faktura nie jest juz w roboczej weryfikacji.";
    }
    if (hasBlockingExceptions(detail)) {
      return "Najpierw trzeba wyjasnic wyjatki wykryte przy dokumencie.";
    }
    if (hasOpenApprovalRequests(detail)) {
      return "Najpierw trzeba zamknac otwarte prosby o decyzje.";
    }
  }

  if (action === "handoff" && workflowState !== "gotowa_do_przekazania") {
    return "Przekazanie bedzie mozliwe dopiero po oznaczeniu faktury jako gotowej.";
  }

  if (action === "reopen" && !["przekazana", "zamknieta"].includes(workflowState)) {
    return "Ponowne otwarcie dotyczy tylko faktur juz przekazanych albo zamknietych.";
  }

  if (action === "close" && workflowState !== "przekazana") {
    return "Zamkniecie bedzie mozliwe dopiero po przekazaniu faktury dalej.";
  }

  if (action === "undo-last" && !(detail.history ?? []).length) {
    return "Nie ma jeszcze zapisanej decyzji, ktora mozna cofnac.";
  }

  return "Frontend pokazuje te decyzje jako mozliwa przyszla akcje. Backend nadal musi ja potwierdzic przed zapisem.";
}

function resolveAvailability(reason: string): InvoiceDecisionAvailability {
  return reason.startsWith("Frontend pokazuje") ? "preview-ready" : "blocked";
}

export function buildInvoiceDecisionActions(detail: InvoiceDetail): InvoiceDecisionAction[] {
  const invoiceId = getInvoiceId(detail);

  return DEFAULT_DECISION_ORDER.map((action) => {
    const definition = INVOICE_ACTION_DEFINITIONS[action];
    const reason = resolveActionReason(detail, action);

    return {
      action,
      label: definition.label,
      description: definition.successMessage,
      availability: resolveAvailability(reason),
      reason,
      requiresReason: definition.requiresReason,
      requiresHandoffTarget: definition.requiresHandoffTarget,
      requiresConfirmation: definition.requiresConfirmation,
      futureEndpoint: invoiceId ? invoiceActionEndpoint(invoiceId, action) : "-",
      futureEndpointLabel: invoiceId ? `Planowany endpoint: ${invoiceActionEndpoint(invoiceId, action)}` : "Planowany endpoint niedostepny bez ID faktury",
    };
  });
}
