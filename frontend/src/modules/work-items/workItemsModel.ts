import { ApiContractError, ApiError } from "@/lib/api";
import type { DataViewErrorState, DataViewStatus } from "@/lib/types";

export type WorkItemsStatus = DataViewStatus;

export type WorkItemsErrorState = DataViewErrorState<WorkItemsStatus>;

export type WorkItemRecord = {
  work_item_id: number;
  title?: string;
  description?: string | null;
  status?: string;
  priority_level?: string;
  priority_score?: number;
  source_type?: string;
  assigned_user_id?: number | null;
  assigned_user_name?: string | null;
  organization_name?: string | null;
  due_at?: string | null;
  sla_deadline_at?: string | null;
  sla_stage?: string;
  sla_state_label?: string;
  is_closed?: boolean;
  is_due_overdue?: boolean;
  is_sla_overdue?: boolean;
  updated_at?: string;
  metadata?: Record<string, unknown>;
};

export type WorkItemViewRow = {
  id: string;
  workItemId: number;
  assignedUserId: number | null;
  title: string;
  description: string;
  statusLabel: string;
  statusTone: "ok" | "warning" | "danger" | "info" | "neutral";
  priorityLabel: string;
  priorityTone: "ok" | "warning" | "danger" | "info" | "neutral";
  ownerLabel: string;
  organizationLabel: string;
  dueLabel: string;
  slaLabel: string;
  sourceLabel: string;
  scoreLabel: string;
};

export type WorkItemSnoozePreset = {
  key: "1h" | "1d";
  label: string;
};

export type WorkItemActionMenuItem = {
  key: "snooze-1h" | "snooze-1d" | "assign-self" | "close";
  label: string;
  disabled: boolean;
  danger?: boolean;
};

export const WORK_ITEMS_ENDPOINT = "/work-items";
export const WORK_ITEMS_READ_ONLY = false;
export const WORK_ITEM_CLOSE_ACTION_ENABLED = true;
export const WORK_ITEM_CLOSE_ENDPOINT_SUFFIX = "/close";
export const DEFAULT_WORK_ITEM_CLOSE_REASON = "Zamkniete z poziomu CASI Workspace Next.";
export const WORK_ITEM_ASSIGN_TO_SELF_ACTION_ENABLED = true;
export const WORK_ITEM_ASSIGN_ENDPOINT_SUFFIX = "/assign";
export const WORK_ITEM_SNOOZE_ACTION_ENABLED = true;
export const WORK_ITEM_SNOOZE_ENDPOINT_SUFFIX = "/snooze";
export const WORK_ITEM_SNOOZE_PRESETS: WorkItemSnoozePreset[] = [
  { key: "1h", label: "Odloz 1h" },
  { key: "1d", label: "Jutro" },
];
export const WORK_ITEMS_ORGANIZATION_REQUIRED_TITLE = "Wybierz organizacje, aby zobaczyc work items";
export const WORK_ITEMS_ORGANIZATION_REQUIRED_DESCRIPTION =
  "Uzytkownik globalny musi najpierw wskazac organizacje w topbarze. Dopiero wtedy frontend przekaze organization_id do /api/work-items i akcji zapisu.";

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

function readRecord(value: unknown): Record<string, unknown> | undefined {
  return isRecord(value) ? value : undefined;
}

function toLabel(value: string | undefined, fallback = "-"): string {
  if (!value) {
    return fallback;
  }
  return value.replace(/_/g, " ").replace(/^\w/, (character) => character.toUpperCase());
}

export function readWorkItems(payload: unknown): WorkItemRecord[] {
  if (!Array.isArray(payload)) {
    throw new ApiContractError(WORK_ITEMS_ENDPOINT, payload);
  }

  return payload.map((item) => {
    if (!isRecord(item)) {
      throw new ApiContractError(WORK_ITEMS_ENDPOINT, payload);
    }

    const workItemId = readNumber(item.work_item_id);
    if (!workItemId) {
      throw new ApiContractError(WORK_ITEMS_ENDPOINT, payload);
    }

    return {
      work_item_id: workItemId,
      title: readOptionalString(item.title),
      description: readOptionalString(item.description) ?? null,
      status: readOptionalString(item.status),
      priority_level: readOptionalString(item.priority_level),
      priority_score: readNumber(item.priority_score),
      source_type: readOptionalString(item.source_type),
      assigned_user_id: readNumber(item.assigned_user_id) ?? null,
      assigned_user_name: readOptionalString(item.assigned_user_name) ?? null,
      organization_name: readOptionalString(item.organization_name) ?? null,
      due_at: readOptionalString(item.due_at) ?? null,
      sla_deadline_at: readOptionalString(item.sla_deadline_at) ?? null,
      sla_stage: readOptionalString(item.sla_stage),
      sla_state_label: readOptionalString(item.sla_state_label),
      is_closed: readBoolean(item.is_closed),
      is_due_overdue: readBoolean(item.is_due_overdue),
      is_sla_overdue: readBoolean(item.is_sla_overdue),
      updated_at: readOptionalString(item.updated_at),
      metadata: readRecord(item.metadata),
    };
  });
}

export function getWorkItemsErrorState(error: unknown): WorkItemsErrorState {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      return {
        status: "unauthenticated",
        title: "Sesja wygasla",
        description: "Zaloguj sie ponownie, aby zobaczyc liste work items.",
      };
    }
    if (error.status === 403) {
      return {
        status: "forbidden",
        title: "Brak dostepu do work items",
        description: "Twoje konto nie ma uprawnien do odczytu operacyjnych pozycji pracy.",
      };
    }
    if (error.status >= 500) {
      return {
        status: "server-error",
        title: "Backend nie zwrocil work items",
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
      title: "Niepoprawny format work items",
      description: "Backend odpowiedzial, ale dane nie pasuja do minimalnego kontraktu widoku Work Items.",
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
    title: "Nie udalo sie pobrac work items",
    description: error instanceof Error ? error.message : "Wystapil nieznany blad pobierania work items.",
  };
}

export function workItemStatusTone(item: WorkItemRecord): WorkItemViewRow["statusTone"] {
  if (item.is_closed || item.status === "zamkniete") {
    return "ok";
  }
  if (item.status === "eskalowane" || item.sla_stage === "escalated") {
    return "danger";
  }
  if (item.status === "w_toku") {
    return "info";
  }
  return "neutral";
}

export function workItemPriorityTone(item: WorkItemRecord): WorkItemViewRow["priorityTone"] {
  if (item.priority_level === "krytyczny" || item.is_sla_overdue) {
    return "danger";
  }
  if (item.priority_level === "wysoki" || item.is_due_overdue || item.sla_stage === "warning") {
    return "warning";
  }
  if (item.priority_level === "niski") {
    return "neutral";
  }
  return "info";
}

export function buildWorkItemRows(items: WorkItemRecord[]): WorkItemViewRow[] {
  return items.map((item) => ({
    id: String(item.work_item_id),
    workItemId: item.work_item_id,
    assignedUserId: item.assigned_user_id ?? null,
    title: readString(item.title, `Work item #${item.work_item_id}`),
    description: readString(item.description, "Brak opisu"),
    statusLabel: toLabel(item.status, "Status nieznany"),
    statusTone: workItemStatusTone(item),
    priorityLabel: toLabel(item.priority_level, "Priorytet nieznany"),
    priorityTone: workItemPriorityTone(item),
    ownerLabel: readString(item.assigned_user_name, "Nieprzypisane"),
    organizationLabel: readString(item.organization_name, "Organizacja nieznana"),
    dueLabel: readString(item.due_at, "Brak terminu"),
    slaLabel: readString(item.sla_state_label, toLabel(item.sla_stage, "SLA nieznane")),
    sourceLabel: toLabel(item.source_type, "Zrodlo nieznane"),
    scoreLabel: typeof item.priority_score === "number" ? String(item.priority_score) : "-",
  }));
}

export function readCurrentUserId(session: unknown): number | null {
  if (!isRecord(session)) {
    return null;
  }
  const source = isRecord(session.user) ? session.user : session;
  return readNumber(source.user_id) ?? readNumber(source.id) ?? null;
}

export function readCurrentUserOrganizationId(session: unknown): string | null {
  if (!isRecord(session)) {
    return null;
  }
  const source = isRecord(session.user) ? session.user : session;
  const organizationId = readNumber(source.organization_id) ?? readOptionalString(source.organization_id);
  return organizationId ? String(organizationId) : null;
}

export function canAssignCurrentUserInOrganization(
  currentUserOrganizationId: string | number | null | undefined,
  selectedOrganizationId: string | number | null | undefined,
): boolean {
  if (!currentUserOrganizationId || !selectedOrganizationId) {
    return false;
  }
  return String(currentUserOrganizationId) === String(selectedOrganizationId);
}

export function canCloseWorkItem(item: WorkItemRecord | WorkItemViewRow): boolean {
  if ("work_item_id" in item) {
    return WORK_ITEM_CLOSE_ACTION_ENABLED && !item.is_closed && item.status !== "zamkniete" && item.status !== "anulowane";
  }
  const status = item.statusLabel.toLowerCase().replace(/\s+/g, "_");
  const isClosed = item.statusTone === "ok" && status === "zamkniete";
  return WORK_ITEM_CLOSE_ACTION_ENABLED && !isClosed && status !== "zamkniete" && status !== "anulowane";
}

export function canAssignWorkItemToSelf(
  item: WorkItemRecord | WorkItemViewRow,
  currentUserId: number | null | undefined,
): boolean {
  if (!WORK_ITEM_ASSIGN_TO_SELF_ACTION_ENABLED || !currentUserId) {
    return false;
  }
  if ("work_item_id" in item) {
    return (
      !item.is_closed &&
      item.status !== "zamkniete" &&
      item.status !== "anulowane" &&
      Number(item.assigned_user_id ?? 0) !== Number(currentUserId)
    );
  }
  const status = item.statusLabel.toLowerCase().replace(/\s+/g, "_");
  return status !== "zamkniete" && status !== "anulowane" && Number(item.assignedUserId ?? 0) !== Number(currentUserId);
}

export function canSnoozeWorkItem(item: WorkItemRecord | WorkItemViewRow): boolean {
  if (!WORK_ITEM_SNOOZE_ACTION_ENABLED) {
    return false;
  }
  if ("work_item_id" in item) {
    return !item.is_closed && item.status !== "zamkniete" && item.status !== "anulowane";
  }
  const status = item.statusLabel.toLowerCase().replace(/\s+/g, "_");
  return status !== "zamkniete" && status !== "anulowane";
}

export function buildWorkItemActionMenuItems(
  item: WorkItemRecord | WorkItemViewRow,
  currentUserId: number | null | undefined,
): WorkItemActionMenuItem[] {
  const snoozeDisabled = !canSnoozeWorkItem(item);
  return [
    {
      key: "snooze-1h",
      label: WORK_ITEM_SNOOZE_PRESETS[0].label,
      disabled: snoozeDisabled,
    },
    {
      key: "snooze-1d",
      label: WORK_ITEM_SNOOZE_PRESETS[1].label,
      disabled: snoozeDisabled,
    },
    {
      key: "assign-self",
      label: "Przypisz do siebie",
      disabled: !canAssignWorkItemToSelf(item, currentUserId),
    },
    {
      key: "close",
      label: "Zamknij",
      disabled: !canCloseWorkItem(item),
      danger: true,
    },
  ];
}

export function canUseWorkItemOrganizationScope(organizationId: string | number | null | undefined): boolean {
  return Boolean(String(organizationId ?? "").trim());
}

export function buildAssignWorkItemToSelfPayload(currentUserId: number): { assigned_user_id: number } {
  return {
    assigned_user_id: currentUserId,
  };
}

export function buildSnoozeWorkItemPayload(preset: WorkItemSnoozePreset): { mode: WorkItemSnoozePreset["key"] } {
  return {
    mode: preset.key,
  };
}

export function buildCloseWorkItemPayload(reason = DEFAULT_WORK_ITEM_CLOSE_REASON): { reason: string } {
  const normalizedReason = reason.trim();
  return {
    reason: normalizedReason || DEFAULT_WORK_ITEM_CLOSE_REASON,
  };
}

export function applyClosedWorkItem(items: WorkItemRecord[], updated: WorkItemRecord): WorkItemRecord[] {
  if (!updated.is_closed && updated.status !== "zamkniete" && updated.status !== "anulowane") {
    return items;
  }
  return items.filter((item) => item.work_item_id !== updated.work_item_id);
}

export function applyAssignedWorkItem(items: WorkItemRecord[], updated: WorkItemRecord, currentUserId: number): WorkItemRecord[] {
  if (Number(updated.assigned_user_id ?? 0) !== Number(currentUserId)) {
    return items;
  }
  return items.map((item) => (item.work_item_id === updated.work_item_id ? updated : item));
}

export function applySnoozedWorkItem(items: WorkItemRecord[], updated: WorkItemRecord): WorkItemRecord[] {
  if (updated.sla_stage !== "on_track" || updated.status === "zamkniete" || updated.status === "anulowane") {
    return items;
  }
  return items.map((item) => (item.work_item_id === updated.work_item_id ? updated : item));
}

export function hasWorkItemsData(status: WorkItemsStatus, items: WorkItemRecord[] | null): boolean {
  return status === "ready" && Boolean(items?.length);
}

export function isWorkItemsEmpty(status: WorkItemsStatus, items: WorkItemRecord[] | null): boolean {
  return status === "ready" && Array.isArray(items) && items.length === 0;
}
