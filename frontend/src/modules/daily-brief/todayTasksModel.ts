export type TodayTaskBucket = "overdue" | "today" | "upcoming";

export type TodayTaskItem = {
  taskId: number;
  title: string;
  dueAt: string | null;
  bucket: TodayTaskBucket;
  detailsUrl: string;
};

export type TodayTasks = {
  counts: Record<TodayTaskBucket, number>;
  items: TodayTaskItem[];
};

function record(value: unknown, label: string): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error(`Nieprawidłowy kontrakt: ${label}.`);
  }
  return value as Record<string, unknown>;
}

function nonNegativeInteger(value: unknown, label: string): number {
  if (!Number.isInteger(value) || Number(value) < 0) {
    throw new Error(`Nieprawidłowy kontrakt: ${label}.`);
  }
  return Number(value);
}

function positiveInteger(value: unknown, label: string): number {
  const parsed = nonNegativeInteger(value, label);
  if (parsed < 1) throw new Error(`Nieprawidłowy kontrakt: ${label}.`);
  return parsed;
}

function text(value: unknown, label: string): string {
  if (typeof value !== "string" || !value.trim()) {
    throw new Error(`Nieprawidłowy kontrakt: ${label}.`);
  }
  return value.trim();
}

function safePath(value: unknown): string {
  const path = text(value, "details_url");
  if (!path.startsWith("/") || path.startsWith("//")) {
    throw new Error("Nieprawidłowy kontrakt: details_url.");
  }
  return path;
}

export function readTodayTasks(payload: unknown): TodayTasks {
  const root = record(payload, "today tasks");
  const counts = record(root.counts, "counts");
  if (!Array.isArray(root.items) || root.items.length > 5) {
    throw new Error("Nieprawidłowy kontrakt: items.");
  }

  return {
    counts: {
      overdue: nonNegativeInteger(counts.overdue, "counts.overdue"),
      today: nonNegativeInteger(counts.today, "counts.today"),
      upcoming: nonNegativeInteger(counts.upcoming, "counts.upcoming"),
    },
    items: root.items.map((value) => {
      const item = record(value, "task item");
      const bucket = text(item.bucket, "bucket");
      if (!(bucket === "overdue" || bucket === "today" || bucket === "upcoming")) {
        throw new Error("Nieprawidłowy kontrakt: bucket.");
      }
      if (item.due_at !== null && item.due_at !== undefined && (typeof item.due_at !== "string" || Number.isNaN(new Date(item.due_at).getTime()))) {
        throw new Error("Nieprawidłowy kontrakt: due_at.");
      }
      return {
        taskId: positiveInteger(item.task_id, "task_id"),
        title: text(item.title, "title"),
        dueAt: typeof item.due_at === "string" && item.due_at.trim() ? item.due_at : null,
        bucket,
        detailsUrl: safePath(item.details_url),
      };
    }),
  };
}

export function todayTaskBucketLabel(bucket: TodayTaskBucket): string {
  if (bucket === "overdue") return "Po terminie";
  if (bucket === "today") return "Dzisiaj";
  return "Najbliższe";
}
