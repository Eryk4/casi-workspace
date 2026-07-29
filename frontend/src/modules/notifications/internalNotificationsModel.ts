export type InternalNotificationFilter = "inbox" | "unread" | "all" | "archived";
export type InternalNotificationState = "unread" | "read" | "archived";

export type InternalNotificationItem = {
  id: number;
  organizationId: number;
  recipientUserId: number;
  sourceEventId: number;
  reasonCode: "overdue" | "due_today";
  detectedOn: string;
  plannedFor: string | null;
  title: string;
  targetLabel: string;
  targetHref: string | null;
  createdAt: string;
  state: InternalNotificationState;
  isUnread: boolean;
  isArchived: boolean;
};

export type InternalNotificationPage = {
  organizationId: number;
  filter: InternalNotificationFilter;
  items: InternalNotificationItem[];
  nextCursor: string | null;
  hasMore: boolean;
};

export type MaterializationResult = {
  asOfDate: string;
  candidatesCount: number;
  createdCount: number;
  existingCount: number;
};

export const INTERNAL_NOTIFICATION_FILTERS: Array<{ id: InternalNotificationFilter; label: string }> = [
  { id: "inbox", label: "Skrzynka" },
  { id: "unread", label: "Nieprzeczytane" },
  { id: "all", label: "Wszystkie" },
  { id: "archived", label: "Archiwum" },
];

export const INTERNAL_NOTIFICATION_WRITE_ACTIONS = ["read", "unread", "archived"] as const;
export const INTERNAL_NOTIFICATION_BILLING_ACTIONS: string[] = [];
export const INTERNAL_NOTIFICATION_POLL_INTERVAL = null;

function record(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error("Nieprawidlowy kontrakt powiadomien.");
  return value as Record<string, unknown>;
}

function integer(value: unknown): number {
  const parsed = typeof value === "number" ? value : Number(value);
  if (!Number.isInteger(parsed) || parsed <= 0) throw new Error("Nieprawidlowy identyfikator powiadomienia.");
  return parsed;
}

function text(value: unknown): string {
  const parsed = typeof value === "string" ? value.trim() : "";
  if (!parsed) throw new Error("Brak wymaganego pola powiadomienia.");
  return parsed;
}

function calendarDate(value: unknown, nullable = false): string | null {
  if ((value === null || value === undefined || value === "") && nullable) return null;
  const parsed = text(value);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(parsed)) throw new Error("Nieprawidlowa data kalendarzowa.");
  return parsed;
}

export function safeNotificationHref(value: unknown): string | null {
  const parsed = typeof value === "string" ? value.trim() : "";
  return parsed.startsWith("/rozliczenia") && !parsed.startsWith("//") ? parsed : null;
}

export function readInternalNotification(value: unknown): InternalNotificationItem {
  const source = record(value);
  const reason = text(source.reason_code);
  if (reason !== "overdue" && reason !== "due_today") throw new Error("Nieprawidlowy powod powiadomienia.");
  const state = text(source.state);
  if (state !== "unread" && state !== "read" && state !== "archived") throw new Error("Nieprawidlowy stan powiadomienia.");
  return {
    id: integer(source.internal_notification_id),
    organizationId: integer(source.organization_id),
    recipientUserId: integer(source.recipient_user_id),
    sourceEventId: integer(source.source_event_id),
    reasonCode: reason,
    detectedOn: calendarDate(source.detected_on) as string,
    plannedFor: calendarDate(source.planned_for, true),
    title: text(source.title_snapshot),
    targetLabel: text(source.target_label_snapshot),
    targetHref: safeNotificationHref(source.internal_link_snapshot),
    createdAt: text(source.created_at),
    state,
    isUnread: source.is_unread === true,
    isArchived: source.is_archived === true,
  };
}

export function readInternalNotificationPage(value: unknown): InternalNotificationPage {
  const source = record(value);
  const filter = text(source.filter);
  if (!INTERNAL_NOTIFICATION_FILTERS.some((item) => item.id === filter)) throw new Error("Nieprawidlowy filtr odpowiedzi.");
  if (!Array.isArray(source.items)) throw new Error("Brak listy powiadomien.");
  const organizationId = integer(source.organization_id);
  const items = source.items.map(readInternalNotification);
  if (items.some((item) => item.organizationId !== organizationId)) throw new Error("Niezgodny zakres organizacji.");
  return {
    organizationId,
    filter: filter as InternalNotificationFilter,
    items,
    nextCursor: typeof source.next_cursor === "string" && source.next_cursor ? source.next_cursor : null,
    hasMore: source.has_more === true,
  };
}

export function readUnreadCount(value: unknown): number {
  const source = record(value);
  const parsed = Number(source.unread_count);
  if (!Number.isInteger(parsed) || parsed < 0) throw new Error("Nieprawidlowy licznik powiadomien.");
  return parsed;
}

export function formatUnreadCount(count: number | null): string | null {
  if (count === null || count <= 0) return null;
  return count > 99 ? "99+" : String(count);
}

export function readMaterializationResult(value: unknown): MaterializationResult {
  const source = record(value);
  const nonNegative = (field: string) => {
    const parsed = Number(source[field]);
    if (!Number.isInteger(parsed) || parsed < 0) throw new Error("Nieprawidlowy wynik materializacji.");
    return parsed;
  };
  return {
    asOfDate: calendarDate(source.as_of_date) as string,
    candidatesCount: nonNegative("candidates_count"),
    createdCount: nonNegative("created_count"),
    existingCount: nonNegative("existing_count"),
  };
}

export function emptyStateCopy(filter: InternalNotificationFilter): { title: string; description: string } {
  if (filter === "unread") return { title: "Brak nieprzeczytanych", description: "Wszystkie bieżące powiadomienia zostały przeczytane." };
  if (filter === "archived") return { title: "Archiwum jest puste", description: "Zarchiwizowane powiadomienia pozostaną tutaj jako historia." };
  return { title: "Skrzynka jest pusta", description: "Użyj jawnej akcji sprawdzenia, aby zmaterializować aktualne sygnały attention." };
}
