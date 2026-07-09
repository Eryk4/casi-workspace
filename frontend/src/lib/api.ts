import type { ApiQuery, ApiRequestMethod, CurrentSession, DashboardSnapshot, InvoiceVerificationInbox, SessionUser } from "./types";

export class ApiError extends Error {
  status: number;
  payload: unknown;

  constructor(message: string, status: number, payload: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

export class ApiContractError extends Error {
  endpoint: string;
  payload: unknown;

  constructor(endpoint: string, payload: unknown) {
    super(`API ${endpoint} zwrocilo dane niezgodne z kontraktem.`);
    this.name = "ApiContractError";
    this.endpoint = endpoint;
    this.payload = payload;
  }
}

export type ApiRequestOptions = {
  method?: ApiRequestMethod;
  body?: unknown;
  query?: ApiQuery;
};

const API_BASE_PATH = "/api";
export const AUTH_REQUIRED_EVENT = "casi:auth-required";
const DASHBOARD_CARD_KEYS = [
  "nowe_faktury",
  "do_weryfikacji",
  "podejrzenia_duplikatow",
  "pewne_duplikaty",
  "nowi_kontrahenci",
  "aktywne_przypomnienia",
] as const;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function notifyAuthRequired(): void {
  if (typeof window === "undefined") {
    return;
  }

  window.dispatchEvent(new CustomEvent(AUTH_REQUIRED_EVENT));
}

function isDashboardSnapshot(payload: unknown): payload is DashboardSnapshot {
  if (!isRecord(payload) || !isRecord(payload.cards)) {
    return false;
  }

  const cards = payload.cards;
  const hasNumericCards = DASHBOARD_CARD_KEYS.every((key) => typeof cards[key] === "number");

  return (
    hasNumericCards &&
    Array.isArray(payload.operational_alerts) &&
    Array.isArray(payload.active_reminders) &&
    Array.isArray(payload.knowledge_queue) &&
    Array.isArray(payload.recent_events)
  );
}

export function readDashboardSnapshot(payload: unknown): DashboardSnapshot {
  if (!isDashboardSnapshot(payload)) {
    throw new ApiContractError("/dashboard", payload);
  }

  return payload;
}

function isInvoiceVerificationItem(payload: unknown): payload is InvoiceVerificationInbox["sections"][string]["items"][number] {
  return isRecord(payload) && typeof payload.invoice_id === "number";
}

function isInvoiceVerificationSection(payload: unknown): payload is InvoiceVerificationInbox["sections"][string] {
  return (
    isRecord(payload) &&
    typeof payload.title === "string" &&
    typeof payload.count === "number" &&
    Array.isArray(payload.items) &&
    payload.items.every(isInvoiceVerificationItem)
  );
}

function isInvoiceVerificationInbox(payload: unknown): payload is InvoiceVerificationInbox {
  if (!isRecord(payload) || !isRecord(payload.summary) || !isRecord(payload.sections)) {
    return false;
  }

  return (
    typeof payload.summary.total_open_count === "number" &&
    Object.values(payload.sections).every(isInvoiceVerificationSection)
  );
}

export function readInvoiceVerificationInbox(payload: unknown): InvoiceVerificationInbox {
  if (!isInvoiceVerificationInbox(payload)) {
    throw new ApiContractError("/invoices/verification-inbox", payload);
  }

  return payload;
}

function toQueryString(query?: ApiQuery): string {
  const params = new URLSearchParams();

  Object.entries(query ?? {}).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") {
      return;
    }

    params.set(key, String(value));
  });

  const serialized = params.toString();
  return serialized ? `?${serialized}` : "";
}

export function withOrganizationQuery(
  organizationId: string | null | undefined,
  query: ApiQuery = {},
): ApiQuery {
  return organizationId ? { ...query, organization_id: organizationId } : query;
}

export function workItemClosePath(workItemId: number | string): string {
  return `/work-items/${workItemId}/close`;
}

export function workItemAssignPath(workItemId: number | string): string {
  return `/work-items/${workItemId}/assign`;
}

export function workItemSnoozePath(workItemId: number | string): string {
  return `/work-items/${workItemId}/snooze`;
}

export function workItemDetailPath(workItemId: number | string): string {
  return `/work-items/${workItemId}`;
}

export async function apiRequest<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const url = `${API_BASE_PATH}${normalizedPath}${toQueryString(options.query)}`;

  const response = await fetch(url, {
    method: options.method ?? "GET",
    credentials: "include",
    headers: options.body ? { "Content-Type": "application/json" } : undefined,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  const contentType = response.headers.get("content-type") ?? "";
  const payload = contentType.includes("application/json") ? await response.json() : await response.text();

  if (!response.ok) {
    const message =
      typeof payload === "object" && payload && "error" in payload
        ? String((payload as { error?: string }).error)
        : `Blad API (${response.status})`;

    if (response.status === 401) {
      notifyAuthRequired();
    }

    throw new ApiError(message, response.status, payload);
  }

  return payload as T;
}

export const api = {
  meta: () => apiRequest<Record<string, unknown>>("/meta"),
  currentSession: () => apiRequest<CurrentSession>("/session/current"),
  login: (login: string, password: string) =>
    apiRequest<SessionUser>("/session/login", {
      method: "POST",
      body: { login, password },
    }),
  dashboard: async (query?: ApiQuery) => readDashboardSnapshot(await apiRequest<unknown>("/dashboard", { query })),
  search: (query: ApiQuery) => apiRequest<Record<string, unknown>>("/search", { query }),
  invoices: (query?: ApiQuery) => apiRequest<Record<string, unknown>>("/invoices", { query }),
  invoiceVerificationInbox: async (query?: ApiQuery) =>
    readInvoiceVerificationInbox(await apiRequest<unknown>("/invoices/verification-inbox", { query })),
  tasks: (query?: ApiQuery) => apiRequest<Record<string, unknown>>("/tasks", { query }),
  taskFocus: (query?: ApiQuery) => apiRequest<Record<string, unknown>>("/tasks/focus", { query }),
  workItems: (query?: ApiQuery) => apiRequest<Record<string, unknown>>("/work-items", { query }),
  workItemDetail: (workItemId: number | string, query?: ApiQuery) =>
    apiRequest<Record<string, unknown>>(workItemDetailPath(workItemId), { query }),
  closeWorkItem: (workItemId: number | string, reason: string, organizationId?: string | null) =>
    apiRequest<Record<string, unknown>>(workItemClosePath(workItemId), {
      method: "POST",
      body: { reason },
      query: withOrganizationQuery(organizationId),
    }),
  assignWorkItem: (workItemId: number | string, assignedUserId: number | string, organizationId?: string | null) =>
    apiRequest<Record<string, unknown>>(workItemAssignPath(workItemId), {
      method: "POST",
      body: { assigned_user_id: Number(assignedUserId) },
      query: withOrganizationQuery(organizationId),
    }),
  snoozeWorkItem: (workItemId: number | string, mode: string, organizationId?: string | null) =>
    apiRequest<Record<string, unknown>>(workItemSnoozePath(workItemId), {
      method: "POST",
      body: { mode },
      query: withOrganizationQuery(organizationId),
    }),
  knowledgeDocuments: (query?: ApiQuery) => apiRequest<Record<string, unknown>>("/knowledge/documents", { query }),
  knowledgeDocumentDetail: (documentId: number | string, query?: ApiQuery) =>
    apiRequest<Record<string, unknown>>(`/knowledge/documents/${documentId}`, { query }),
  contractors: (query?: ApiQuery) => apiRequest<Record<string, unknown>>("/contractors", { query }),
  contractorDetail: (contractorId: number | string, query?: ApiQuery) =>
    apiRequest<Record<string, unknown>>(`/contractors/${contractorId}`, { query }),
  addContractorNote: (
    contractorId: number | string,
    noteText: string,
    organizationId?: string | null,
  ) =>
    apiRequest<Record<string, unknown>>(`/contractors/${contractorId}/notes`, {
      method: "POST",
      body: { note_text: noteText },
      query: withOrganizationQuery(organizationId),
    }),
  ledgerBalances: (query?: ApiQuery) => apiRequest<Record<string, unknown>>("/billing/ledger/balances", { query }),
  billingLedgerMatches: (query?: ApiQuery) => apiRequest<Record<string, unknown>>("/billing/ledger/matches", { query }),
  billingTransactions: (query?: ApiQuery) => apiRequest<Record<string, unknown>>("/billing/transactions", { query }),
  billingPaymentReviewStatuses: (query?: ApiQuery) =>
    apiRequest<Record<string, unknown>>("/billing/payment-review-statuses", { query }),
  billingWorkQueueEvents: (query?: ApiQuery) =>
    apiRequest<Record<string, unknown>>("/billing/work-queue/events", { query }),
  billingContactEvents: (query?: ApiQuery) =>
    apiRequest<Record<string, unknown>>("/billing/contact-events", { query }),
  billingPayers: (query?: ApiQuery) => apiRequest<Record<string, unknown>>("/billing/payers", { query }),
  billingPayerNotes: (payerId: number | string, query?: ApiQuery) =>
    apiRequest<Record<string, unknown>>(`/billing/payers/${payerId}/notes`, { query }),
  billingPaymentReviewStatus: (paymentId: number | string, query?: ApiQuery) =>
    apiRequest<Record<string, unknown>>(`/billing/payments/${paymentId}/review-status`, { query }),
  updateBillingPaymentReviewStatus: (
    paymentId: number | string,
    payload: { status: string; note_text?: string },
    organizationId?: string | null,
  ) =>
    apiRequest<Record<string, unknown>>(`/billing/payments/${paymentId}/review-status`, {
      method: "POST",
      body: payload,
      query: withOrganizationQuery(organizationId),
    }),
  addBillingWorkQueueEvent: (
    payload: {
      issue_key: string;
      issue_type: string;
      target_type: string;
      target_id?: number;
      action: string;
      note_text?: string;
    },
    organizationId?: string | null,
  ) =>
    apiRequest<Record<string, unknown>>("/billing/work-queue/events", {
      method: "POST",
      body: payload,
      query: withOrganizationQuery(organizationId),
    }),
  addBillingContactEvent: (
    payload: {
      payer_id: number;
      related_payment_id?: number;
      related_issue_key?: string;
      channel: string;
      contact_action: string;
      message_text?: string;
      note_text?: string;
    },
    organizationId?: string | null,
  ) =>
    apiRequest<Record<string, unknown>>("/billing/contact-events", {
      method: "POST",
      body: payload,
      query: withOrganizationQuery(organizationId),
    }),
  addBillingPayerNote: (
    payerId: number | string,
    noteText: string,
    organizationId?: string | null,
  ) =>
    apiRequest<Record<string, unknown>>(`/billing/payers/${payerId}/notes`, {
      method: "POST",
      body: { note_text: noteText },
      query: withOrganizationQuery(organizationId),
    }),
  billingStudents: (query?: ApiQuery) => apiRequest<Record<string, unknown>>("/billing/students", { query }),
  billingCharges: (query?: ApiQuery) => apiRequest<Record<string, unknown>>("/billing/charges", { query }),
  organizations: () => apiRequest<Record<string, unknown>>("/organizations"),
  users: () => apiRequest<Record<string, unknown>>("/users"),
};
