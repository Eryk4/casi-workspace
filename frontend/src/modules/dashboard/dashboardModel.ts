import { ApiContractError, ApiError } from "../../lib/api";
import type { ApiRequestMethod, DashboardAlert, DashboardAlertCategory, DashboardSnapshot, DataViewErrorState, DataViewStatus } from "../../lib/types";

export type DashboardSignal = {
  id: string;
  area: string;
  category?: DashboardAlertCategory;
  source: string;
  status: "ok" | "warning" | "danger" | "info";
  statusLabel: string;
  owner: string;
  nextStep: string;
};

export type DashboardStatus = DataViewStatus;
export type DashboardFilter = "all" | DashboardAlertCategory;

export type DashboardErrorState = DataViewErrorState<DashboardStatus>;

export const DASHBOARD_ENDPOINT = "/dashboard";
export const DASHBOARD_MUTATION_METHODS: ReadonlyArray<Exclude<ApiRequestMethod, "GET">> = [];
export const DASHBOARD_ORGANIZATION_REQUIRED_TITLE = "Wybierz organizacje, aby zobaczyc pulpit";
export const DASHBOARD_ORGANIZATION_REQUIRED_DESCRIPTION =
  "Globalny uzytkownik musi najpierw wskazac organizacje w topbarze. Dopiero wtedy frontend przekaze organization_id do /api/dashboard.";

export function toStatus(severity: DashboardAlert["severity"]): DashboardSignal["status"] {
  if (severity === "danger") {
    return "danger";
  }
  if (severity === "warning") {
    return "warning";
  }
  if (severity === "info") {
    return "info";
  }
  return "ok";
}

export function categoryToOwner(category?: string): string {
  switch (category) {
    case "invoices":
      return "Faktury";
    case "tasks":
      return "Asystent Szefa";
    case "knowledge":
      return "Asystent Firmowy";
    case "integrations":
      return "Ustawienia";
    default:
      return "Pulpit";
  }
}

export function categoryToSource(category?: string): string {
  switch (category) {
    case "invoices":
      return "Faktury";
    case "tasks":
      return "Zadania";
    case "knowledge":
      return "Baza wiedzy";
    case "integrations":
      return "Integracje";
    default:
      return "Pulpit";
  }
}

export function buildSignals(snapshot: DashboardSnapshot | null, filter: DashboardFilter): DashboardSignal[] {
  const alerts = snapshot?.operational_alerts ?? [];

  return alerts
    .filter((alert) => filter === "all" || alert.category === filter)
    .map((alert, index) => ({
      id: `${alert.category ?? "alert"}-${index}`,
      area: alert.title || "Alert operacyjny",
      category: alert.category,
      source: categoryToSource(alert.category),
      status: toStatus(alert.severity),
      statusLabel: alert.severity === "danger" ? "Pilne" : alert.severity === "warning" ? "Uwaga" : "Info",
      owner: categoryToOwner(alert.category),
      nextStep: alert.description || alert.action_label || "Sprawdz szczegoly w module",
    }));
}

export function getDashboardErrorState(error: unknown): DashboardErrorState {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      return {
        status: "unauthenticated",
        title: "Sesja wygasla",
        description: "Zaloguj sie ponownie, aby zobaczyc dane pulpitu organizacji.",
      };
    }

    if (error.status === 403) {
      return {
        status: "forbidden",
        title: "Brak dostepu do pulpitu",
        description: "Twoje konto nie ma uprawnien do odczytu danych tej organizacji.",
      };
    }

    if (error.status >= 500) {
      return {
        status: "server-error",
        title: "Backend nie zwrocil danych pulpitu",
        description: "Wystapil blad serwera. Sprobuj odswiezyc widok albo sprawdz logi backendu.",
      };
    }

    return {
      status: "error",
      title: `Blad API (${error.status})`,
      description: error.message,
    };
  }

  if (error instanceof Error) {
    if (error instanceof ApiContractError) {
      return {
        status: "error",
        title: "Niepoprawny format danych pulpitu",
        description:
          "Backend odpowiedzial, ale dane nie pasuja do kontraktu pulpitu. Widok nie pokazuje ich jako prawdziwego pulpitu.",
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
      title: "Nie udalo sie pobrac danych",
      description: error.message,
    };
  }

  return {
    status: "error",
    title: "Nie udalo sie pobrac danych",
    description: "Wystapil nieznany blad pobierania danych pulpitu.",
  };
}

export function hasDashboardData(snapshot: DashboardSnapshot | null): boolean {
  if (!snapshot) {
    return false;
  }

  const hasRealCards = Object.values(snapshot.cards).every((value) => typeof value === "number");

  return Boolean(
    hasRealCards ||
      snapshot.operational_alerts.length ||
      snapshot.active_reminders.length ||
      snapshot.knowledge_queue.length ||
      snapshot.recent_events.length,
  );
}

export function canRenderDashboardData(status: DashboardStatus, snapshot: DashboardSnapshot | null): boolean {
  return status === "ready" && Boolean(snapshot) && hasDashboardData(snapshot);
}

export function isDashboardEmpty(status: DashboardStatus, snapshot: DashboardSnapshot | null): boolean {
  return status === "ready" && !hasDashboardData(snapshot);
}

export function isDashboardReadOnly(): boolean {
  return DASHBOARD_MUTATION_METHODS.length === 0;
}

export function canUseDashboardOrganizationScope(organizationId: string | number | null | undefined): boolean {
  return organizationId !== null && organizationId !== undefined && String(organizationId).trim().length > 0;
}
