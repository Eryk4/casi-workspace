import { ApiContractError, ApiError } from "@/lib/api";
import type { DataViewErrorState, DataViewStatus } from "@/lib/types";

import {
  buildWorkItemRows,
  canUseWorkItemOrganizationScope,
  readWorkItems,
  type WorkItemRecord,
  type WorkItemViewRow,
} from "./workItemsModel";

export type WorkItemDetailStatus = DataViewStatus;

export type WorkItemDetailErrorState = DataViewErrorState<WorkItemDetailStatus>;

export type WorkItemDetailRecord = WorkItemRecord & {
  source_id?: number | null;
  created_at?: string | null;
  created_by_user_name?: string | null;
  updated_by_user_name?: string | null;
  metadata?: Record<string, unknown>;
};

export type WorkItemHistoryEvent = {
  id: string;
  actionType: string;
  title: string;
  description: string;
  actorLabel: string;
  dateLabel: string;
};

export type WorkItemContextLink = {
  id: string;
  title: string;
  description: string;
  href: string;
  meta: string;
  kind: "invoice" | "contractor" | "document" | "task" | "case";
};

export type WorkItemDetailFact = {
  label: string;
  value: string;
};

export type WorkItemDetailView = {
  row: WorkItemViewRow;
  title: string;
  attentionReason: string;
  facts: WorkItemDetailFact[];
  relatedInvoices: WorkItemContextLink[];
  relatedContractors: WorkItemContextLink[];
  relatedDocuments: WorkItemContextLink[];
  relatedTasks: WorkItemContextLink[];
  history: WorkItemHistoryEvent[];
};

export const WORK_ITEM_DETAIL_ENDPOINT_PREFIX = "/work-items";
export const WORK_ITEM_DETAIL_READ_ONLY = true;
export const WORK_ITEM_DETAIL_WRITE_ACTIONS: ReadonlyArray<never> = [];
export const WORK_ITEM_DETAIL_ORGANIZATION_REQUIRED_TITLE = "Wybierz organizację, aby zobaczyć kartę sprawy";
export const WORK_ITEM_DETAIL_ORGANIZATION_REQUIRED_DESCRIPTION =
  "Karta sprawy wymaga aktywnej organizacji. Dzięki temu CASI pobiera tylko sprawę z wybranego kontekstu firmy.";

const TECHNICAL_PATTERNS = [
  /storage_key/i,
  /data[\\/]magazyn/i,
  /c:\\users\\/i,
  /token/i,
  /secret/i,
  /connection string/i,
  /database_url/i,
  /invoice_database_url/i,
  /raw json/i,
  /payload/i,
  /debug/i,
  /metadata_json/i,
];

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
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

function readOptionalString(value: unknown): string | undefined {
  return typeof value === "string" && value.trim() ? value.trim() : undefined;
}

function readMetadata(value: unknown): Record<string, unknown> {
  return isRecord(value) ? value : {};
}

function normalizeDate(value: string | null | undefined): string {
  if (!value) {
    return "Brak daty";
  }

  const [datePart, timePart] = value.replace("Z", "").split("T");
  if (!datePart) {
    return safeText(value, "Brak daty");
  }

  return timePart ? `${datePart} ${timePart.slice(0, 5)}` : datePart;
}

function labelize(value: string | undefined, fallback = "-"): string {
  if (!value) {
    return fallback;
  }
  return value.replace(/_/g, " ").replace(/^\w/, (character) => character.toUpperCase());
}

export function safeText(value: unknown, fallback = "-"): string {
  const text = readOptionalString(value) ?? fallback;
  const normalized = text.replace(/\s+/g, " ").trim();
  if (!normalized || TECHNICAL_PATTERNS.some((pattern) => pattern.test(normalized))) {
    return fallback;
  }
  return normalized;
}

function metadataString(metadata: Record<string, unknown>, keys: string[], fallback = ""): string {
  const value = keys.map((key) => safeText(metadata[key], "")).find(Boolean);
  return value || fallback;
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
  for (const key of keys) {
    const value = metadata[key];
    if (Array.isArray(value)) {
      return value.map(readNumber).filter((item): item is number => Boolean(item));
    }
    const numberValue = readNumber(value);
    if (numberValue) {
      return [numberValue];
    }
  }
  return [];
}

function sourceMatches(workItem: WorkItemDetailRecord, pattern: RegExp): boolean {
  return pattern.test(String(workItem.source_type ?? ""));
}

function sourceId(workItem: WorkItemDetailRecord): number | undefined {
  return readNumber(workItem.source_id);
}

export function workItemDetailPath(workItemId: number | string): string {
  return `/work-items/${workItemId}`;
}

export function canUseWorkItemDetailOrganizationScope(
  organizationId: string | number | null | undefined,
): boolean {
  return canUseWorkItemOrganizationScope(organizationId);
}

export function hasWorkItemDetailWriteActions(): boolean {
  return WORK_ITEM_DETAIL_WRITE_ACTIONS.length > 0;
}

export function readWorkItemDetail(payload: unknown, requestedWorkItemId?: number): {
  workItem: WorkItemDetailRecord;
  history: WorkItemHistoryEvent[];
} {
  if (!isRecord(payload) || !isRecord(payload.work_item)) {
    throw new ApiContractError(`${WORK_ITEM_DETAIL_ENDPOINT_PREFIX}/{id}`, payload);
  }

  const [base] = readWorkItems([payload.work_item]);
  if (!base || (requestedWorkItemId && base.work_item_id !== requestedWorkItemId)) {
    throw new ApiContractError(`${WORK_ITEM_DETAIL_ENDPOINT_PREFIX}/{id}`, payload);
  }

  const rawWorkItem = payload.work_item;
  const workItem: WorkItemDetailRecord = {
    ...base,
    source_id: readNumber(rawWorkItem.source_id) ?? null,
    created_at: readOptionalString(rawWorkItem.created_at) ?? null,
    created_by_user_name: readOptionalString(rawWorkItem.created_by_user_name) ?? null,
    updated_by_user_name: readOptionalString(rawWorkItem.updated_by_user_name) ?? null,
    metadata: readMetadata(rawWorkItem.metadata),
  };

  return {
    workItem,
    history: readHistory(payload.history, workItem.work_item_id),
  };
}

function readHistory(value: unknown, workItemId: number): WorkItemHistoryEvent[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.filter(isRecord).map((event, index) => {
    const actionType = safeText(event.action_type, "work_item_event");
    return {
      id: String(readNumber(event.work_item_history_id) ?? `${workItemId}-${index}`),
      actionType,
      title: actionLabel(actionType),
      description: safeText(event.message, "Zapisano zmianę w historii sprawy."),
      actorLabel: safeText(event.actor_user_name ?? event.actor_login ?? event.actor, "System"),
      dateLabel: normalizeDate(readOptionalString(event.created_at)),
    };
  });
}

function actionLabel(actionType: string): string {
  return (
    {
      work_item_created: "Utworzono sprawę",
      work_item_updated: "Zaktualizowano sprawę",
      work_item_assigned: "Przypisano sprawę",
      work_item_snoozed: "Odłożono sprawę",
      work_item_closed: "Zamknięto sprawę",
      work_item_reopened: "Wznowiono sprawę",
      work_item_escalated: "Eskalowano sprawę",
      work_item_sla_escalated: "Eskalowano SLA",
      work_item_sla_warning: "Ostrzeżenie SLA",
    }[actionType] ?? labelize(actionType, "Zdarzenie")
  );
}

export function buildWorkItemDetailView(detail: {
  workItem: WorkItemDetailRecord;
  history: WorkItemHistoryEvent[];
}): WorkItemDetailView {
  const [row] = buildWorkItemRows([detail.workItem]);
  const metadata = detail.workItem.metadata ?? {};

  return {
    row,
    title: row.title,
    attentionReason: buildAttentionReason(row, detail.workItem),
    facts: buildFacts(row, detail.workItem),
    relatedInvoices: buildRelatedInvoices(detail.workItem, metadata),
    relatedContractors: buildRelatedContractors(detail.workItem, metadata),
    relatedDocuments: buildRelatedDocuments(detail.workItem, metadata),
    relatedTasks: buildRelatedTasks(detail.workItem, metadata),
    history: detail.history,
  };
}

function buildAttentionReason(row: WorkItemViewRow, workItem: WorkItemDetailRecord): string {
  if (row.priorityTone === "danger" || row.statusTone === "danger") {
    return "Ta sprawa wymaga uwagi, bo jest oznaczona jako krytyczna albo przekroczyła SLA.";
  }
  if (row.priorityTone === "warning") {
    return "Warto zająć się nią dzisiaj, bo ma podwyższony priorytet lub zbliżający się termin.";
  }
  if (workItem.assigned_user_name) {
    return "Sprawa ma właściciela i może być spokojnie śledzona w bieżącej kolejce.";
  }
  return "Sprawa jest widoczna w kolejce operacyjnej i czeka na dalsze uporządkowanie.";
}

function buildFacts(row: WorkItemViewRow, workItem: WorkItemDetailRecord): WorkItemDetailFact[] {
  return [
    { label: "Status", value: row.statusLabel },
    { label: "Priorytet", value: row.priorityLabel },
    { label: "SLA", value: row.slaLabel },
    { label: "Termin", value: row.dueLabel },
    { label: "Właściciel", value: row.ownerLabel },
    { label: "Organizacja", value: row.organizationLabel },
    { label: "Źródło", value: sourceLabel(workItem.source_type) },
    { label: "Utworzono", value: normalizeDate(workItem.created_at) },
    { label: "Aktualizacja", value: normalizeDate(workItem.updated_at) },
  ];
}

function sourceLabel(sourceType: string | undefined): string {
  const normalized = String(sourceType ?? "").toLowerCase();
  if (normalized.includes("invoice") || normalized.includes("fakt")) {
    return "Faktury";
  }
  if (normalized.includes("contractor") || normalized.includes("crm")) {
    return "CRM";
  }
  if (normalized.includes("knowledge") || normalized.includes("document")) {
    return "Dokumenty";
  }
  if (normalized.includes("task")) {
    return "Zadania";
  }
  if (normalized.includes("support")) {
    return "Obsługa klienta";
  }
  if (normalized.includes("manual")) {
    return "Sprawa ręczna";
  }
  return labelize(sourceType, "Źródło nieznane");
}

function buildRelatedInvoices(workItem: WorkItemDetailRecord, metadata: Record<string, unknown>): WorkItemContextLink[] {
  const invoiceId =
    metadataNumber(metadata, ["invoice_id", "linked_invoice_id", "source_invoice_id"]) ??
    (sourceMatches(workItem, /invoice|faktur/i) ? sourceId(workItem) : undefined);
  if (!invoiceId) {
    return [];
  }

  const amount = metadataString(metadata, ["invoice_amount_label", "gross_amount_label"]);
  const status = metadataString(metadata, ["invoice_status_label", "invoice_status", "status_label"]);

  return [
    {
      id: `invoice-${invoiceId}`,
      title: metadataString(metadata, ["invoice_number", "invoice_title"], "Powiązana faktura"),
      description: metadataString(metadata, ["invoice_contractor_name", "contractor_name", "issuer_name"], "Szczegóły w module Faktury"),
      href: `/faktury/${invoiceId}`,
      meta: [amount, status].filter(Boolean).join(" · ") || "Otwórz szczegół faktury",
      kind: "invoice",
    },
  ];
}

function buildRelatedContractors(workItem: WorkItemDetailRecord, metadata: Record<string, unknown>): WorkItemContextLink[] {
  const contractorId =
    metadataNumber(metadata, ["contractor_id", "linked_contractor_id", "source_contractor_id"]) ??
    (sourceMatches(workItem, /contractor|crm/i) ? sourceId(workItem) : undefined);
  if (!contractorId) {
    return [];
  }

  return [
    {
      id: `contractor-${contractorId}`,
      title: metadataString(metadata, ["contractor_name", "customer_name"], "Powiązany kontrahent"),
      description: metadataString(metadata, ["contractor_relation", "relation_type"], "Kontekst kontrahenta w CRM"),
      href: `/crm/${contractorId}`,
      meta: metadataString(metadata, ["contractor_status", "contractor_type"], "Otwórz kartę kontrahenta"),
      kind: "contractor",
    },
  ];
}

function buildRelatedDocuments(workItem: WorkItemDetailRecord, metadata: Record<string, unknown>): WorkItemContextLink[] {
  const ids = metadataNumberList(metadata, ["knowledge_document_ids", "document_ids", "linked_document_ids"]);
  const fallbackId = sourceMatches(workItem, /knowledge|document/i) ? sourceId(workItem) : undefined;
  const documentIds = ids.length ? ids : fallbackId ? [fallbackId] : [];

  return documentIds.slice(0, 5).map((documentId, index) => ({
    id: `document-${documentId}`,
    title: metadataString(metadata, ["document_title", "knowledge_document_title"], "Powiązany dokument"),
    description: metadataString(metadata, ["document_status", "document_context"], "Dokument wspierający tę sprawę"),
    href: `/dokumenty/${documentId}`,
    meta: metadataString(metadata, ["document_folder", "library_path_label"], index === 0 ? "Otwórz dokument" : "Powiązany dokument"),
    kind: "document",
  }));
}

function buildRelatedTasks(workItem: WorkItemDetailRecord, metadata: Record<string, unknown>): WorkItemContextLink[] {
  const taskId =
    metadataNumber(metadata, ["task_id", "linked_task_id", "source_task_id"]) ??
    (sourceMatches(workItem, /task|zad/i) ? sourceId(workItem) : undefined);
  if (!taskId) {
    return [];
  }

  return [
    {
      id: `task-${taskId}`,
      title: metadataString(metadata, ["task_title"], "Powiązane zadanie"),
      description: metadataString(metadata, ["task_context"], "Kontekst dostępny w module Asystent Szefa"),
      href: "/asystent-szefa",
      meta: "Zobacz fokus operacyjny",
      kind: "task",
    },
  ];
}

export function canRenderWorkItemDetail(
  status: WorkItemDetailStatus,
  detail: { workItem: WorkItemDetailRecord; history: WorkItemHistoryEvent[] } | null,
): boolean {
  return status === "ready" && Boolean(detail);
}

export function isWorkItemDetailEmpty(
  status: WorkItemDetailStatus,
  detail: { workItem: WorkItemDetailRecord; history: WorkItemHistoryEvent[] } | null,
): boolean {
  return status === "ready" && !detail;
}

export function hasUnsafeWorkItemDetailText(view: WorkItemDetailView): boolean {
  const values = [
    view.title,
    view.attentionReason,
    ...view.facts.flatMap((fact) => [fact.label, fact.value]),
    ...view.relatedInvoices.flatMap(linkValues),
    ...view.relatedContractors.flatMap(linkValues),
    ...view.relatedDocuments.flatMap(linkValues),
    ...view.relatedTasks.flatMap(linkValues),
    ...view.history.flatMap((event) => [event.title, event.description, event.actorLabel, event.dateLabel]),
  ];
  return values.some((value) => TECHNICAL_PATTERNS.some((pattern) => pattern.test(value)));
}

function linkValues(link: WorkItemContextLink): string[] {
  return [link.title, link.description, link.href, link.meta];
}

export function getWorkItemDetailErrorState(error: unknown): WorkItemDetailErrorState {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      return {
        status: "unauthenticated",
        title: "Sesja wygasła",
        description: "Zaloguj się ponownie, aby zobaczyć kartę sprawy.",
      };
    }
    if (error.status === 403) {
      return {
        status: "forbidden",
        title: "Brak dostępu do sprawy",
        description: "Twoje konto nie ma uprawnień do odczytu tej sprawy w wybranej organizacji.",
      };
    }
    if (error.status === 404) {
      return {
        status: "error",
        title: "Nie znaleziono sprawy",
        description: "Sprawa nie istnieje w wybranej organizacji albo została usunięta.",
      };
    }
    if (error.status >= 500) {
      return {
        status: "server-error",
        title: "Backend nie zwrócił sprawy",
        description: "Wystąpił błąd serwera. Odśwież widok albo sprawdź logi backendu.",
      };
    }
    return {
      status: "error",
      title: `Błąd API (${error.status})`,
      description: error.message,
    };
  }

  if (error instanceof ApiContractError) {
    return {
      status: "error",
      title: "Niepoprawny format sprawy",
      description: "Backend odpowiedział, ale dane nie pasują do kontraktu karty sprawy.",
    };
  }

  if (error instanceof TypeError) {
    return {
      status: "error",
      title: "Problem z połączeniem z API",
      description: "Nie udało się połączyć z backendem. Sprawdź, czy API jest dostępne i spróbuj ponownie.",
    };
  }

  return {
    status: "error",
    title: "Nie udało się pobrać sprawy",
    description: error instanceof Error ? error.message : "Wystąpił nieznany błąd pobierania sprawy.",
  };
}
