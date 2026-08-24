export type TodayBillingBucket = "overdue" | "today";

export type TodayBillingItem = {
  billingNextStepEventId: number;
  title: string;
  plannedFor: string;
  bucket: TodayBillingBucket;
  detailsUrl: string;
};

export type TodayBilling = {
  overdueCount: number;
  dueTodayCount: number;
  items: TodayBillingItem[];
};

function record(value: unknown, label: string): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error(`Nieprawidłowy kontrakt: ${label}.`);
  return value as Record<string, unknown>;
}

function integer(value: unknown, label: string): number {
  if (!Number.isInteger(value) || Number(value) < 0) throw new Error(`Nieprawidłowy kontrakt: ${label}.`);
  return Number(value);
}

function positiveInteger(value: unknown, label: string): number {
  const parsed = integer(value, label);
  if (parsed < 1) throw new Error(`Nieprawidłowy kontrakt: ${label}.`);
  return parsed;
}

function calendarDate(value: unknown): string {
  const date = text(value, "planned_for");
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(date);
  if (!match) throw new Error("Nieprawidłowy kontrakt: planned_for.");
  const parsed = new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
  if (parsed.getFullYear() !== Number(match[1]) || parsed.getMonth() !== Number(match[2]) - 1 || parsed.getDate() !== Number(match[3])) {
    throw new Error("Nieprawidłowy kontrakt: planned_for.");
  }
  return date;
}

function text(value: unknown, label: string): string {
  if (typeof value !== "string" || !value.trim()) throw new Error(`Nieprawidłowy kontrakt: ${label}.`);
  return value.trim();
}

function safePath(value: unknown): string {
  const path = text(value, "details_url");
  if (!path.startsWith("/") || path.startsWith("//")) throw new Error("Nieprawidłowy kontrakt: details_url.");
  return path;
}

export function readTodayBilling(payload: unknown): TodayBilling {
  const root = record(payload, "today billing");
  if (!Array.isArray(root.items) || root.items.length > 3) throw new Error("Nieprawidłowy kontrakt: items.");
  return {
    overdueCount: integer(root.overdue_count, "overdue_count"),
    dueTodayCount: integer(root.due_today_count, "due_today_count"),
    items: root.items.map((value) => {
      const item = record(value, "billing item");
      const bucket = text(item.bucket, "bucket");
      if (!(bucket === "overdue" || bucket === "today")) throw new Error("Nieprawidłowy kontrakt: bucket.");
      const plannedFor = calendarDate(item.planned_for);
      return {
        billingNextStepEventId: positiveInteger(item.billing_next_step_event_id, "billing_next_step_event_id"),
        title: text(item.title, "title"),
        plannedFor,
        bucket,
        detailsUrl: safePath(item.details_url),
      };
    }),
  };
}

export function todayBillingBucketLabel(bucket: TodayBillingBucket): string {
  return bucket === "overdue" ? "Po terminie" : "Dzisiaj";
}
