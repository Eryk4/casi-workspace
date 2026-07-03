import { ApiContractError, ApiError } from "@/lib/api";
import type { DataViewErrorState, DataViewStatus } from "@/lib/types";

export type BossAssistantStatus = DataViewStatus;

export type BossAssistantErrorState = DataViewErrorState<BossAssistantStatus>;

export type TaskFocusTask = {
  task_id: number;
  title?: string;
  description?: string | null;
  task_type?: string;
  status?: string;
  priority?: string;
  due_at?: string | null;
  remind_at?: string | null;
  visibility_scope?: string;
  organization_name?: string | null;
  owner_user_name?: string | null;
  assigned_user_name?: string | null;
  calendar_name?: string | null;
  reminder_state?: string;
  linked_entity_count?: number;
};

export type TaskFocusView = {
  code: string;
  label: string;
  count: number;
  items: TaskFocusTask[];
};

export type TaskFocusSnapshot = {
  generated_at?: string;
  available_views: string[];
  views: TaskFocusView[];
};

export type BossAssistantViewRow = {
  id: string;
  title: string;
  contextLabel: string;
  sourceLabel: string;
  statusLabel: string;
  statusTone: "ok" | "warning" | "danger" | "info" | "neutral";
  priorityLabel: string;
  priorityTone: "ok" | "warning" | "danger" | "info" | "neutral";
  dueLabel: string;
  ownerLabel: string;
  focusLabel: string;
};

export type BossAssistantKpis = {
  urgent: number;
  overdue: number;
  decisions: number;
  blockers: number;
  today: number;
  totalVisible: number;
};

export const BOSS_ASSISTANT_ENDPOINT = "/tasks/focus";
export const BOSS_ASSISTANT_READ_ONLY = true;
export const BOSS_ASSISTANT_AI_ACTIONS_ENABLED = false;
export const BOSS_ASSISTANT_ORGANIZATION_REQUIRED_TITLE = "Wybierz organizacje, aby zobaczyc Asystenta Szefa";
export const BOSS_ASSISTANT_ORGANIZATION_REQUIRED_DESCRIPTION =
  "Globalny uzytkownik musi najpierw wskazac organizacje w topbarze. Dopiero wtedy frontend pobierze focus snapshot dla konkretnego organization_id.";

const FOCUS_PRIORITY = ["do_decyzji", "po_terminie", "moj_dzien", "czeka_na_kogos", "organizacyjne", "prywatne"];

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

function toLabel(value: string | undefined, fallback = "-"): string {
  if (!value) {
    return fallback;
  }
  return value.replace(/_/g, " ").replace(/^\w/, (character) => character.toUpperCase());
}

function formatDateLabel(value: string | null | undefined): string {
  if (!value) {
    return "Brak terminu";
  }
  const [datePart, timePart] = value.replace("Z", "").split("T");
  return timePart ? `${datePart} ${timePart.slice(0, 5)}` : datePart || value;
}

export function readTaskFocusSnapshot(payload: unknown): TaskFocusSnapshot {
  if (!isRecord(payload) || !Array.isArray(payload.views)) {
    throw new ApiContractError(BOSS_ASSISTANT_ENDPOINT, payload);
  }

  const availableViews = Array.isArray(payload.available_views)
    ? payload.available_views.filter((item): item is string => typeof item === "string")
    : [];

  return {
    generated_at: readOptionalString(payload.generated_at),
    available_views: availableViews,
    views: payload.views.map((view) => {
      if (!isRecord(view) || !Array.isArray(view.items)) {
        throw new ApiContractError(BOSS_ASSISTANT_ENDPOINT, payload);
      }

      const code = readOptionalString(view.code);
      if (!code) {
        throw new ApiContractError(BOSS_ASSISTANT_ENDPOINT, payload);
      }

      return {
        code,
        label: readString(view.label, toLabel(code)),
        count: readNumber(view.count) ?? view.items.length,
        items: view.items.map((item) => readTaskFocusTask(item, payload)),
      };
    }),
  };
}

function readTaskFocusTask(item: unknown, originalPayload: unknown): TaskFocusTask {
  if (!isRecord(item)) {
    throw new ApiContractError(BOSS_ASSISTANT_ENDPOINT, originalPayload);
  }

  const taskId = readNumber(item.task_id);
  if (!taskId) {
    throw new ApiContractError(BOSS_ASSISTANT_ENDPOINT, originalPayload);
  }

  return {
    task_id: taskId,
    title: readOptionalString(item.title),
    description: readOptionalString(item.description) ?? null,
    task_type: readOptionalString(item.task_type),
    status: readOptionalString(item.status),
    priority: readOptionalString(item.priority),
    due_at: readOptionalString(item.due_at) ?? null,
    remind_at: readOptionalString(item.remind_at) ?? null,
    visibility_scope: readOptionalString(item.visibility_scope),
    organization_name: readOptionalString(item.organization_name) ?? null,
    owner_user_name: readOptionalString(item.owner_user_name) ?? null,
    assigned_user_name: readOptionalString(item.assigned_user_name) ?? null,
    calendar_name: readOptionalString(item.calendar_name) ?? null,
    reminder_state: readOptionalString(item.reminder_state),
    linked_entity_count: readNumber(item.linked_entity_count) ?? 0,
  };
}

export function getBossAssistantErrorState(error: unknown): BossAssistantErrorState {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      return {
        status: "unauthenticated",
        title: "Sesja wygasla",
        description: "Zaloguj sie ponownie, aby zobaczyc sprawy wymagajace uwagi.",
      };
    }
    if (error.status === 403) {
      return {
        status: "forbidden",
        title: "Brak dostepu do Asystenta Szefa",
        description: "Twoje konto nie ma uprawnien do widoku spraw managerskich.",
      };
    }
    if (error.status >= 500) {
      return {
        status: "server-error",
        title: "Backend nie zwrocil focus snapshot",
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
      title: "Niepoprawny format Asystenta Szefa",
      description: "Backend odpowiedzial, ale dane nie pasuja do minimalnego kontraktu widoku focus.",
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
    title: "Nie udalo sie pobrac spraw",
    description: error instanceof Error ? error.message : "Wystapil nieznany blad pobierania focus snapshot.",
  };
}

export function buildBossAssistantKpis(snapshot: TaskFocusSnapshot): BossAssistantKpis {
  const countByCode = new Map(snapshot.views.map((view) => [view.code, view.count]));
  const allTasks = uniqueTasksFromViews(snapshot.views);

  return {
    urgent: allTasks.filter((task) => task.priority === "krytyczny" || task.priority === "wysoki").length,
    overdue: countByCode.get("po_terminie") ?? 0,
    decisions: countByCode.get("do_decyzji") ?? 0,
    blockers: countByCode.get("czeka_na_kogos") ?? 0,
    today: countByCode.get("moj_dzien") ?? 0,
    totalVisible: allTasks.length,
  };
}

export function buildBossAssistantRows(snapshot: TaskFocusSnapshot, limit = 12): BossAssistantViewRow[] {
  const orderedViews = [...snapshot.views].sort((first, second) => focusRank(first.code) - focusRank(second.code));
  const seen = new Set<number>();
  const rows: BossAssistantViewRow[] = [];

  for (const view of orderedViews) {
    for (const task of view.items) {
      if (seen.has(task.task_id)) {
        continue;
      }
      seen.add(task.task_id);
      rows.push(buildBossAssistantRow(task, view));
      if (rows.length >= limit) {
        return rows;
      }
    }
  }

  return rows;
}

function uniqueTasksFromViews(views: TaskFocusView[]): TaskFocusTask[] {
  const seen = new Set<number>();
  const tasks: TaskFocusTask[] = [];
  for (const view of views) {
    for (const task of view.items) {
      if (!seen.has(task.task_id)) {
        seen.add(task.task_id);
        tasks.push(task);
      }
    }
  }
  return tasks;
}

function buildBossAssistantRow(task: TaskFocusTask, view: TaskFocusView): BossAssistantViewRow {
  const owner = task.assigned_user_name || task.owner_user_name || task.organization_name;
  const anchor = task.remind_at || task.due_at;

  return {
    id: String(task.task_id),
    title: readString(task.title, `Sprawa #${task.task_id}`),
    contextLabel: readString(task.description, "Brak opisu"),
    sourceLabel: toLabel(task.task_type, "Zadanie"),
    statusLabel: toLabel(task.status, "Status nieznany"),
    statusTone: taskStatusTone(task),
    priorityLabel: toLabel(task.priority, "Priorytet nieznany"),
    priorityTone: taskPriorityTone(task),
    dueLabel: formatDateLabel(anchor),
    ownerLabel: readString(owner, "Brak wlasciciela"),
    focusLabel: view.label,
  };
}

export function taskStatusTone(task: TaskFocusTask): BossAssistantViewRow["statusTone"] {
  if (task.status === "zakonczone") {
    return "ok";
  }
  if (task.status === "anulowane") {
    return "neutral";
  }
  if (task.status === "oczekuje") {
    return "warning";
  }
  if (task.reminder_state === "blad") {
    return "danger";
  }
  if (task.status === "w_toku") {
    return "info";
  }
  return "neutral";
}

export function taskPriorityTone(task: TaskFocusTask): BossAssistantViewRow["priorityTone"] {
  if (task.priority === "krytyczny") {
    return "danger";
  }
  if (task.priority === "wysoki") {
    return "warning";
  }
  if (task.priority === "niski") {
    return "neutral";
  }
  return "info";
}

function focusRank(code: string): number {
  const rank = FOCUS_PRIORITY.indexOf(code);
  return rank >= 0 ? rank : FOCUS_PRIORITY.length;
}

export function hasBossAssistantData(status: BossAssistantStatus, snapshot: TaskFocusSnapshot | null): boolean {
  return status === "ready" && Boolean(snapshot && buildBossAssistantRows(snapshot).length);
}

export function isBossAssistantEmpty(status: BossAssistantStatus, snapshot: TaskFocusSnapshot | null): boolean {
  return status === "ready" && snapshot !== null && buildBossAssistantRows(snapshot).length === 0;
}

export function canUseBossAssistantOrganizationScope(organizationId: string | number | null | undefined): boolean {
  return organizationId !== null && organizationId !== undefined && String(organizationId).trim().length > 0;
}
