import { ApiContractError, ApiError } from "@/lib/api";
import type { DataViewStatus } from "@/lib/types";

export const BILLING_NEXT_STEP_ATTENTION_ENDPOINT = "/billing/next-step-attention";
export const BILLING_ATTENTION_PREVIEW_LIMIT = 5;
export const BILLING_ATTENTION_MUTATION_METHODS: readonly string[] = [];

export type BillingAttentionReasonCode = "overdue" | "due_today";

export type BillingAttentionCandidate = {
  eventId: number;
  organizationId: number;
  reasonCode: BillingAttentionReasonCode;
  plannedFor: string;
  targetType: string;
  targetId?: number;
  relatedIssueKey?: string;
  stepType: string;
  title: string;
  targetLabel: string;
  targetHref?: string;
  createdAt: string;
};

export type BillingAttentionResponse = {
  organizationId: number;
  asOfDate: string;
  overdueCount: number;
  dueTodayCount: number;
  attentionCount: number;
  candidates: BillingAttentionCandidate[];
};

export type BillingAttentionView = BillingAttentionResponse & {
  preview: BillingAttentionCandidate[];
};

export type BillingAttentionStatus = DataViewStatus;

export type BillingAttentionErrorState = {
  status: BillingAttentionStatus;
  title: string;
  description: string;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function readInteger(value: unknown): number | null {
  const parsed = typeof value === "number" ? value : Number(value);
  return Number.isInteger(parsed) && parsed >= 0 ? parsed : null;
}

function readRequiredString(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function readOptionalString(value: unknown): string | undefined {
  return typeof value === "string" && value.trim() ? value.trim() : undefined;
}

function isCalendarDate(value: string): boolean {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!match) {
    return false;
  }
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  const candidate = new Date(year, month - 1, day, 12, 0, 0, 0);
  return candidate.getFullYear() === year && candidate.getMonth() === month - 1 && candidate.getDate() === day;
}

function safeInternalHref(value: unknown): string | undefined {
  const href = readOptionalString(value);
  return href && /^\/rozliczenia(?:\/|$)/.test(href) && !href.includes("//") ? href : undefined;
}

function readCandidate(payload: unknown): BillingAttentionCandidate {
  if (!isRecord(payload)) {
    throw new ApiContractError(BILLING_NEXT_STEP_ATTENTION_ENDPOINT, payload);
  }

  const eventId = readInteger(payload.billing_next_step_event_id);
  const organizationId = readInteger(payload.organization_id);
  const reasonCode = payload.reason_code;
  const plannedFor = readRequiredString(payload.planned_for);
  const targetType = readRequiredString(payload.target_type);
  const stepType = readRequiredString(payload.step_type);
  const title = readRequiredString(payload.title);
  const targetLabel = readRequiredString(payload.target_label);
  const createdAt = readRequiredString(payload.created_at);
  if (
    !eventId ||
    !organizationId ||
    (reasonCode !== "overdue" && reasonCode !== "due_today") ||
    !plannedFor ||
    !isCalendarDate(plannedFor) ||
    !targetType ||
    !stepType ||
    !title ||
    !targetLabel ||
    !createdAt
  ) {
    throw new ApiContractError(BILLING_NEXT_STEP_ATTENTION_ENDPOINT, payload);
  }

  const targetId = readInteger(payload.target_id);
  return {
    eventId,
    organizationId,
    reasonCode,
    plannedFor,
    targetType,
    targetId: targetId && targetId > 0 ? targetId : undefined,
    relatedIssueKey: readOptionalString(payload.related_issue_key),
    stepType,
    title,
    targetLabel,
    targetHref: safeInternalHref(payload.target_href),
    createdAt,
  };
}

export function readBillingAttentionResponse(payload: unknown): BillingAttentionResponse {
  if (!isRecord(payload) || !Array.isArray(payload.candidates)) {
    throw new ApiContractError(BILLING_NEXT_STEP_ATTENTION_ENDPOINT, payload);
  }
  const organizationId = readInteger(payload.organization_id);
  const asOfDate = readRequiredString(payload.as_of_date);
  const overdueCount = readInteger(payload.overdue_count);
  const dueTodayCount = readInteger(payload.due_today_count);
  const attentionCount = readInteger(payload.attention_count);
  if (!organizationId || !asOfDate || !isCalendarDate(asOfDate) || overdueCount === null || dueTodayCount === null || attentionCount === null) {
    throw new ApiContractError(BILLING_NEXT_STEP_ATTENTION_ENDPOINT, payload);
  }
  const candidates = payload.candidates.map(readCandidate);
  if (
    candidates.some((candidate) => candidate.organizationId !== organizationId) ||
    candidates.some((candidate) =>
      candidate.reasonCode === "overdue" ? candidate.plannedFor >= asOfDate : candidate.plannedFor !== asOfDate,
    ) ||
    overdueCount !== candidates.filter((candidate) => candidate.reasonCode === "overdue").length ||
    dueTodayCount !== candidates.filter((candidate) => candidate.reasonCode === "due_today").length ||
    attentionCount !== candidates.length
  ) {
    throw new ApiContractError(BILLING_NEXT_STEP_ATTENTION_ENDPOINT, payload);
  }
  return { organizationId, asOfDate, overdueCount, dueTodayCount, attentionCount, candidates };
}

export function buildBillingAttentionView(
  response: BillingAttentionResponse,
  limit = BILLING_ATTENTION_PREVIEW_LIMIT,
): BillingAttentionView {
  const candidates = response.candidates.slice().sort(
    (a, b) =>
      Number(a.reasonCode === "due_today") - Number(b.reasonCode === "due_today") ||
      a.plannedFor.localeCompare(b.plannedFor) ||
      a.createdAt.localeCompare(b.createdAt) ||
      a.eventId - b.eventId,
  );
  return { ...response, candidates, preview: candidates.slice(0, Math.max(0, limit)) };
}

export function getBillingAttentionErrorState(error: unknown): BillingAttentionErrorState {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      return { status: "unauthenticated", title: "Sesja wygasla", description: "Zaloguj sie ponownie, aby pobrac kroki rozliczeniowe." };
    }
    if (error.status === 403) {
      return { status: "forbidden", title: "Brak dostepu", description: "Nie masz dostepu do krokow tej organizacji." };
    }
    return { status: error.status >= 500 ? "server-error" : "error", title: "Nie udalo sie pobrac krokow", description: error.message };
  }
  if (error instanceof ApiContractError) {
    return { status: "error", title: "Niepoprawne dane attention", description: "Backend zwrocil niezgodny kontrakt krokow wymagajacych uwagi." };
  }
  return {
    status: "error",
    title: "Nie udalo sie pobrac krokow",
    description: error instanceof Error ? error.message : "Wystapil nieznany blad pobierania.",
  };
}

export function isBillingAttentionReadOnly(): boolean {
  return BILLING_ATTENTION_MUTATION_METHODS.length === 0;
}
