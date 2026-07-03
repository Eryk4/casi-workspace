import { ApiContractError, apiRequest } from "@/lib/api";
import type { ApiQuery } from "@/lib/types";

import type {
  InvoiceActionKind,
  InvoiceActionPayload,
  InvoiceActionResult,
  InvoiceCommentPayload,
  InvoiceCommentRecord,
  InvoiceDetail,
  InvoiceListFilters,
  InvoiceRecord,
  InvoiceVerificationWorkspace,
} from "./types";

export const INVOICE_DETAIL_ENDPOINT_PREFIX = "/invoices";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isInvoiceVerificationWorkspace(payload: unknown): payload is InvoiceVerificationWorkspace {
  if (!isRecord(payload) || !isRecord(payload.summary) || !isRecord(payload.sections)) {
    return false;
  }

  return (
    typeof payload.summary.total_open_count === "number" &&
    typeof payload.summary.total_sla_breached === "number" &&
    Array.isArray(payload.bucket_order)
  );
}

function isInvoiceDetail(payload: unknown): payload is InvoiceDetail {
  return isRecord(payload) && isRecord(payload.invoice);
}

function isInvoiceActionResult(payload: unknown): payload is InvoiceActionResult {
  return isRecord(payload) && (typeof payload.id === "number" || typeof payload.invoice_id === "number");
}

function isInvoiceCommentRecord(payload: unknown): payload is InvoiceCommentRecord {
  return isRecord(payload) && typeof payload.note_text === "string";
}

export function readVerificationWorkspace(payload: unknown): InvoiceVerificationWorkspace {
  if (!isInvoiceVerificationWorkspace(payload)) {
    throw new ApiContractError("/invoices/verification-workspace", payload);
  }

  return payload;
}

export function readInvoiceList(payload: unknown): InvoiceRecord[] {
  if (!Array.isArray(payload)) {
    throw new ApiContractError("/invoices", payload);
  }

  return payload as InvoiceRecord[];
}

export function invoiceDetailEndpoint(invoiceId: number): string {
  return `${INVOICE_DETAIL_ENDPOINT_PREFIX}/${invoiceId}`;
}

export function invoiceActionEndpoint(invoiceId: number, action: InvoiceActionKind): string {
  return `${invoiceDetailEndpoint(invoiceId)}/actions/${action}`;
}

export function invoiceCommentEndpoint(invoiceId: number): string {
  return `${invoiceDetailEndpoint(invoiceId)}/comments`;
}

export function readInvoiceDetail(payload: unknown, invoiceId: number): InvoiceDetail {
  if (!isInvoiceDetail(payload)) {
    throw new ApiContractError(invoiceDetailEndpoint(invoiceId), payload);
  }

  return payload;
}

export function readInvoiceActionResult(payload: unknown, invoiceId: number, action: InvoiceActionKind): InvoiceActionResult {
  if (!isInvoiceActionResult(payload)) {
    throw new ApiContractError(invoiceActionEndpoint(invoiceId, action), payload);
  }

  return payload;
}

export function readInvoiceComment(payload: unknown, invoiceId: number): InvoiceCommentRecord {
  if (!isInvoiceCommentRecord(payload)) {
    throw new ApiContractError(invoiceCommentEndpoint(invoiceId), payload);
  }

  return payload;
}

function toQuery(filters: InvoiceListFilters = {}): ApiQuery {
  return {
    search: filters.search,
    source: filters.source,
    status: filters.status,
    workflow_state: filters.workflow_state,
    duplicate_type: filters.duplicate_type,
    sort_by: filters.sort_by,
    sort_order: filters.sort_order,
  };
}

export const invoiceApi = {
  async verificationWorkspace(bucket?: string, limit = 25) {
    return readVerificationWorkspace(
      await apiRequest<unknown>("/invoices/verification-workspace", {
        query: {
          bucket,
          limit,
        },
      }),
    );
  },

  async list(filters: InvoiceListFilters = {}, query: ApiQuery = {}) {
    return readInvoiceList(await apiRequest<unknown>("/invoices", { query: { ...toQuery(filters), ...query } }));
  },

  async detail(invoiceId: number, query?: ApiQuery) {
    return readInvoiceDetail(await apiRequest<unknown>(invoiceDetailEndpoint(invoiceId), { query }), invoiceId);
  },

  async submitAction(invoiceId: number, action: InvoiceActionKind, payload?: InvoiceActionPayload) {
    return readInvoiceActionResult(
      await apiRequest<unknown>(invoiceActionEndpoint(invoiceId, action), {
        method: "POST",
        body: payload,
      }),
      invoiceId,
      action,
    );
  },

  async addComment(invoiceId: number, payload: InvoiceCommentPayload, query?: ApiQuery) {
    return readInvoiceComment(
      await apiRequest<unknown>(invoiceCommentEndpoint(invoiceId), {
        method: "POST",
        body: payload,
        query,
      }),
      invoiceId,
    );
  },
};
