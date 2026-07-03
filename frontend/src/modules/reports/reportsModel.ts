import { ApiContractError, ApiError } from "@/lib/api";
import type { DashboardSnapshot, DataViewErrorState, DataViewStatus } from "@/lib/types";

export type ReportsStatus = DataViewStatus;

export type ReportsErrorState = DataViewErrorState<ReportsStatus>;

export type ReportsWorkItem = {
  work_item_id: number;
  status?: string;
  priority_level?: string;
  is_closed?: boolean;
  is_due_overdue?: boolean;
  is_sla_overdue?: boolean;
};

export type ReportsDocument = {
  knowledge_document_id: number;
  processing_status?: string;
  business_status?: string;
  workflow_status?: string;
};

export type ReportsBillingBalance = {
  billing_payer_id: number;
  balance_due?: number;
};

export type ReportsContractor = {
  contractor_id: number;
  is_new?: boolean;
  invoice_count?: number;
};

export type ReportsSnapshot = {
  dashboard?: DashboardSnapshot;
  workItems: ReportsWorkItem[];
  documents: ReportsDocument[];
  billingBalances: ReportsBillingBalance[];
  contractors: ReportsContractor[];
  missingSources: string[];
};

export type ReportsKpis = {
  invoicesToAttention: number;
  openWorkItems: number;
  documentsToAttention: number;
  billingBalanceDue: number;
  contractorsTotal: number;
};

export type ReportSignal = {
  id: string;
  area: string;
  value: string;
  statusLabel: string;
  statusTone: "ok" | "warning" | "danger" | "info" | "neutral";
  nextStep: string;
  href: string;
};

export type ReportModuleLink = {
  id: string;
  label: string;
  href: string;
  description: string;
  statusLabel: string;
  statusTone: "ok" | "warning" | "danger" | "info" | "neutral";
};

export const REPORTS_ENDPOINT = "/reports/operational-summary";
export const REPORTS_READ_ONLY = true;
export const REPORT_EXPORTS_ENABLED = false;
export const REPORT_GENERATOR_ENABLED = false;
export const REPORTS_ORGANIZATION_REQUIRED_TITLE = "Wybierz organizacje, aby zobaczyc raporty";
export const REPORTS_ORGANIZATION_REQUIRED_DESCRIPTION =
  "Globalny uzytkownik musi najpierw wskazac organizacje w topbarze. Dopiero wtedy frontend przekaze organization_id do zrodel raportu.";

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

function readBoolean(value: unknown): boolean | undefined {
  if (typeof value === "boolean") {
    return value;
  }
  if (typeof value === "number") {
    return value === 1;
  }
  if (typeof value === "string") {
    const normalized = value.trim().toLowerCase();
    if (["1", "true", "tak", "yes"].includes(normalized)) {
      return true;
    }
    if (["0", "false", "nie", "no"].includes(normalized)) {
      return false;
    }
  }
  return undefined;
}

function readOptionalString(value: unknown): string | undefined {
  return typeof value === "string" && value.trim() ? value : undefined;
}

export function readReportsSnapshot(payload: unknown): ReportsSnapshot {
  if (!isRecord(payload)) {
    throw new ApiContractError(REPORTS_ENDPOINT, payload);
  }

  return {
    dashboard: isRecord(payload.dashboard) ? (payload.dashboard as DashboardSnapshot) : undefined,
    workItems: payload.workItems === undefined ? [] : readReportWorkItems(payload.workItems, payload),
    documents: payload.documents === undefined ? [] : readReportDocuments(payload.documents, payload),
    billingBalances: payload.billingBalances === undefined ? [] : readReportBillingBalances(payload.billingBalances, payload),
    contractors: payload.contractors === undefined ? [] : readReportContractors(payload.contractors, payload),
    missingSources: Array.isArray(payload.missingSources)
      ? payload.missingSources.filter((item): item is string => typeof item === "string" && Boolean(item.trim()))
      : [],
  };
}

function readReportWorkItems(value: unknown, originalPayload: unknown): ReportsWorkItem[] {
  if (!Array.isArray(value)) {
    throw new ApiContractError(REPORTS_ENDPOINT, originalPayload);
  }
  return value.map((item) => {
    if (!isRecord(item)) {
      throw new ApiContractError(REPORTS_ENDPOINT, originalPayload);
    }
    const id = readNumber(item.work_item_id);
    if (!id) {
      throw new ApiContractError(REPORTS_ENDPOINT, originalPayload);
    }
    return {
      work_item_id: id,
      status: readOptionalString(item.status),
      priority_level: readOptionalString(item.priority_level),
      is_closed: readBoolean(item.is_closed),
      is_due_overdue: readBoolean(item.is_due_overdue),
      is_sla_overdue: readBoolean(item.is_sla_overdue),
    };
  });
}

function readReportDocuments(value: unknown, originalPayload: unknown): ReportsDocument[] {
  if (!isRecord(value) || !Array.isArray(value.documents)) {
    throw new ApiContractError(REPORTS_ENDPOINT, originalPayload);
  }
  return value.documents.map((item) => {
    if (!isRecord(item)) {
      throw new ApiContractError(REPORTS_ENDPOINT, originalPayload);
    }
    const id = readNumber(item.knowledge_document_id);
    if (!id) {
      throw new ApiContractError(REPORTS_ENDPOINT, originalPayload);
    }
    return {
      knowledge_document_id: id,
      processing_status: readOptionalString(item.processing_status),
      business_status: readOptionalString(item.business_status),
      workflow_status: readOptionalString(item.workflow_status),
    };
  });
}

function readReportBillingBalances(value: unknown, originalPayload: unknown): ReportsBillingBalance[] {
  if (!Array.isArray(value)) {
    throw new ApiContractError(REPORTS_ENDPOINT, originalPayload);
  }
  return value.map((item) => {
    if (!isRecord(item)) {
      throw new ApiContractError(REPORTS_ENDPOINT, originalPayload);
    }
    const id = readNumber(item.billing_payer_id);
    if (!id) {
      throw new ApiContractError(REPORTS_ENDPOINT, originalPayload);
    }
    return {
      billing_payer_id: id,
      balance_due: readNumber(item.balance_due) ?? 0,
    };
  });
}

function readReportContractors(value: unknown, originalPayload: unknown): ReportsContractor[] {
  if (!Array.isArray(value)) {
    throw new ApiContractError(REPORTS_ENDPOINT, originalPayload);
  }
  return value.map((item) => {
    if (!isRecord(item)) {
      throw new ApiContractError(REPORTS_ENDPOINT, originalPayload);
    }
    const id = readNumber(item.contractor_id);
    if (!id) {
      throw new ApiContractError(REPORTS_ENDPOINT, originalPayload);
    }
    return {
      contractor_id: id,
      is_new: readBoolean(item.is_new),
      invoice_count: readNumber(item.invoice_count) ?? 0,
    };
  });
}

export function getReportsErrorState(error: unknown): ReportsErrorState {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      return {
        status: "unauthenticated",
        title: "Sesja wygasla",
        description: "Zaloguj sie ponownie, aby zobaczyc raportowe podsumowanie firmy.",
      };
    }
    if (error.status === 403) {
      return {
        status: "forbidden",
        title: "Brak dostepu do raportow",
        description: "Twoje konto nie ma uprawnien do odczytu danych raportowych.",
      };
    }
    if (error.status >= 500) {
      return {
        status: "server-error",
        title: "Backend nie zwrocil danych raportowych",
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
      title: "Niepoprawny format raportow",
      description: "Jedno ze zrodel odpowiedzialo danymi niepasujacymi do minimalnego kontraktu raportowego.",
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
    title: "Nie udalo sie pobrac raportow",
    description: error instanceof Error ? error.message : "Wystapil nieznany blad pobierania raportow.",
  };
}

export function buildReportsKpis(snapshot: ReportsSnapshot): ReportsKpis {
  const cards = snapshot.dashboard?.cards;
  const invoicesToAttention =
    (cards?.do_weryfikacji ?? 0) + (cards?.podejrzenia_duplikatow ?? 0) + (cards?.pewne_duplikaty ?? 0);
  const openWorkItems = snapshot.workItems.filter((item) => !item.is_closed && item.status !== "zamkniete").length;
  const documentsToAttention = snapshot.documents.filter((item) =>
    ["queued", "processing", "error"].includes(item.processing_status ?? "") ||
    ["do_sprawdzenia", "do_akceptacji"].includes(item.business_status ?? "") ||
    ["review_needed", "official_missing"].includes(item.workflow_status ?? ""),
  ).length;
  const billingBalanceDue = roundMoney(snapshot.billingBalances.reduce((sum, item) => sum + (item.balance_due ?? 0), 0));

  return {
    invoicesToAttention,
    openWorkItems,
    documentsToAttention,
    billingBalanceDue,
    contractorsTotal: snapshot.contractors.length,
  };
}

export function buildReportSignals(snapshot: ReportsSnapshot): ReportSignal[] {
  const kpis = buildReportsKpis(snapshot);
  const workItemsAtRisk = snapshot.workItems.filter(
    (item) => item.is_due_overdue || item.is_sla_overdue || item.priority_level === "krytyczny",
  ).length;
  const newContractors = snapshot.contractors.filter((item) => item.is_new).length;

  return [
    {
      id: "invoices",
      area: "Faktury",
      value: String(kpis.invoicesToAttention),
      statusLabel: kpis.invoicesToAttention > 0 ? "Wymaga uwagi" : "Stabilnie",
      statusTone: kpis.invoicesToAttention > 0 ? "warning" : "ok",
      nextStep: "Otworz inbox faktur i kolejke weryfikacji.",
      href: "/faktury",
    },
    {
      id: "work-items",
      area: "Work Items",
      value: String(workItemsAtRisk),
      statusLabel: workItemsAtRisk > 0 ? "Ryzyko SLA" : "Bez ryzyka",
      statusTone: workItemsAtRisk > 0 ? "danger" : "ok",
      nextStep: "Sprawdz pozycje po terminie i wysokie priorytety.",
      href: "/work-items",
    },
    {
      id: "documents",
      area: "Dokumenty",
      value: String(kpis.documentsToAttention),
      statusLabel: kpis.documentsToAttention > 0 ? "Do decyzji" : "Stabilnie",
      statusTone: kpis.documentsToAttention > 0 ? "warning" : "ok",
      nextStep: "Przejrzyj dokumenty w przetwarzaniu lub workflow.",
      href: "/dokumenty",
    },
    {
      id: "billing",
      area: "Rozliczenia",
      value: formatMoney(kpis.billingBalanceDue),
      statusLabel: kpis.billingBalanceDue > 0 ? "Naleznosci" : "Rozliczone",
      statusTone: kpis.billingBalanceDue > 0 ? "warning" : "ok",
      nextStep: "Zobacz salda platnikow i dopasowane wplaty.",
      href: "/rozliczenia",
    },
    {
      id: "crm",
      area: "CRM",
      value: String(newContractors),
      statusLabel: newContractors > 0 ? "Nowi kontrahenci" : "Bez nowych",
      statusTone: newContractors > 0 ? "info" : "neutral",
      nextStep: "Przejrzyj katalog kontrahentow i brakujace dane.",
      href: "/crm",
    },
  ];
}

export function buildReportModuleLinks(snapshot: ReportsSnapshot): ReportModuleLink[] {
  const kpis = buildReportsKpis(snapshot);
  return [
    {
      id: "dashboard",
      label: "Pulpit",
      href: "/pulpit",
      description: "Biezace sygnaly operacyjne i przypomnienia.",
      statusLabel: snapshot.dashboard ? "Dane live" : "Brak zrodla",
      statusTone: snapshot.dashboard ? "ok" : "neutral",
    },
    {
      id: "invoices",
      label: "Faktury",
      href: "/faktury",
      description: `${kpis.invoicesToAttention} pozycji do uwagi.`,
      statusLabel: "Read-only raport",
      statusTone: kpis.invoicesToAttention > 0 ? "warning" : "ok",
    },
    {
      id: "work-items",
      label: "Work Items",
      href: "/work-items",
      description: `${kpis.openWorkItems} otwartych pozycji pracy.`,
      statusLabel: "Read-only raport",
      statusTone: kpis.openWorkItems > 0 ? "info" : "neutral",
    },
    {
      id: "billing",
      label: "Rozliczenia",
      href: "/rozliczenia",
      description: `Saldo: ${formatMoney(kpis.billingBalanceDue)}.`,
      statusLabel: "Read-only raport",
      statusTone: kpis.billingBalanceDue > 0 ? "warning" : "ok",
    },
  ];
}

export function hasReportsData(status: ReportsStatus, snapshot: ReportsSnapshot | null): boolean {
  return status === "ready" && snapshot !== null && buildReportSignals(snapshot).length > 0;
}

export function isReportsEmpty(status: ReportsStatus, snapshot: ReportsSnapshot | null): boolean {
  if (status !== "ready" || snapshot === null) {
    return false;
  }
  const kpis = buildReportsKpis(snapshot);
  return (
    !snapshot.dashboard &&
    snapshot.workItems.length === 0 &&
    snapshot.documents.length === 0 &&
    snapshot.billingBalances.length === 0 &&
    snapshot.contractors.length === 0 &&
    kpis.invoicesToAttention === 0
  );
}

export function canUseReportsOrganizationScope(organizationId: string | number | null | undefined): boolean {
  return organizationId !== null && organizationId !== undefined && String(organizationId).trim().length > 0;
}

export function formatMoney(value: number): string {
  return `${value.toLocaleString("pl-PL", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })} PLN`;
}

function roundMoney(value: number): number {
  return Math.round(value * 100) / 100;
}
