export const TODAY_CAPABILITIES = {
  attention: "automation.read",
  tasks: "work_items.read",
  billing: "billing.read",
  activity: "automation.read",
} as const;

export type TodaySectionVisibility = {
  attention: boolean;
  tasks: boolean;
  billing: boolean;
  activity: boolean;
};

export function resolveTodaySections(capabilities: readonly string[]): TodaySectionVisibility {
  const available = new Set(capabilities);
  return {
    attention: available.has(TODAY_CAPABILITIES.attention),
    tasks: available.has(TODAY_CAPABILITIES.tasks),
    billing: available.has(TODAY_CAPABILITIES.billing),
    activity: available.has(TODAY_CAPABILITIES.activity),
  };
}

export function formatTodayHeadingDate(value = new Date()): string {
  const label = new Intl.DateTimeFormat("pl-PL", { weekday: "long", day: "numeric", month: "long" }).format(value);
  return label.charAt(0).toLocaleUpperCase("pl-PL") + label.slice(1);
}

export function formatTodayItemDate(value: string | null): string {
  if (!value) return "Bez terminu";
  const [year, month, day] = value.slice(0, 10).split("-").map(Number);
  const date = new Date(year, month - 1, day);
  if (Number.isNaN(date.getTime())) return "Termin niedostępny";
  return new Intl.DateTimeFormat("pl-PL", { day: "numeric", month: "short" }).format(date);
}
