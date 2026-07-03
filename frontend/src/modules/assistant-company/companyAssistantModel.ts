import { ApiContractError, ApiError, readDashboardSnapshot } from "@/lib/api";
import type { DashboardSnapshot, DataViewErrorState, DataViewStatus, InvoiceVerificationInbox } from "@/lib/types";

import { readInvoiceVerificationInbox } from "@/lib/api";
import { buildDocumentsKpis, buildKnowledgeDocumentRows, readKnowledgeDocuments, type KnowledgeDocumentRecord } from "../documents/documentsModel";
import { buildWorkItemRows, readWorkItems, type WorkItemRecord } from "../work-items/workItemsModel";

export type CompanyAssistantStatus = DataViewStatus;

export type CompanyAssistantErrorState = DataViewErrorState<CompanyAssistantStatus>;

export type CompanyAssistantSourceKey = "dashboard" | "documents" | "workItems" | "invoices";

export type CompanyAssistantSourceState = {
  key: CompanyAssistantSourceKey;
  label: string;
  endpoint: string;
  status: "ready" | "missing" | "error";
  message: string;
};

export type CompanyAssistantSnapshot = {
  dashboard?: DashboardSnapshot;
  documents: KnowledgeDocumentRecord[];
  workItems: WorkItemRecord[];
  invoiceInbox?: InvoiceVerificationInbox;
  sourceStates: CompanyAssistantSourceState[];
};

export type CompanyAssistantKpis = {
  knowledgeDocuments: number;
  readyKnowledgeDocuments: number;
  openWorkItems: number;
  invoicesToReview: number;
  decisionSignals: number;
};

export type CompanyAssistantKnowledgeRow = {
  id: string;
  title: string;
  statusLabel: string;
  statusTone: "ok" | "warning" | "danger" | "info" | "neutral";
  ownerLabel: string;
  updatedLabel: string;
};

export type CompanyAssistantAttentionRow = {
  id: string;
  typeLabel: string;
  title: string;
  statusLabel: string;
  statusTone: "ok" | "warning" | "danger" | "info" | "neutral";
  detail: string;
};

export const COMPANY_ASSISTANT_READ_ONLY = true;
export const COMPANY_ASSISTANT_AI_AGENT_ENABLED = false;
export const COMPANY_ASSISTANT_ORGANIZATION_REQUIRED_TITLE = "Wybierz organizacje, aby zobaczyc Asystenta Firmowego";
export const COMPANY_ASSISTANT_ORGANIZATION_REQUIRED_DESCRIPTION =
  "Globalny uzytkownik musi najpierw wskazac organizacje w topbarze. Dopiero wtedy frontend pobierze wiedze, sprawy i kontekst dla konkretnego organization_id.";

export const COMPANY_ASSISTANT_SOURCES: Record<CompanyAssistantSourceKey, Omit<CompanyAssistantSourceState, "status" | "message">> = {
  dashboard: {
    key: "dashboard",
    label: "Kontekst operacyjny",
    endpoint: "/dashboard",
  },
  documents: {
    key: "documents",
    label: "Zrodla wiedzy",
    endpoint: "/knowledge/documents",
  },
  workItems: {
    key: "workItems",
    label: "Sprawy do uwagi",
    endpoint: "/work-items",
  },
  invoices: {
    key: "invoices",
    label: "Faktury do uwagi",
    endpoint: "/invoices/verification-inbox",
  },
};

type RawCompanyAssistantSnapshot = {
  dashboard?: unknown;
  documents?: unknown;
  workItems?: unknown;
  invoiceInbox?: unknown;
  sourceStates?: CompanyAssistantSourceState[];
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function readString(value: unknown, fallback = "-"): string {
  return typeof value === "string" && value.trim() ? value : fallback;
}

function errorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return "Zrodlo nie zwrocilo danych.";
}

export function sourceReady(key: CompanyAssistantSourceKey, message = "Dane live"): CompanyAssistantSourceState {
  return {
    ...COMPANY_ASSISTANT_SOURCES[key],
    status: "ready",
    message,
  };
}

export function sourceMissing(key: CompanyAssistantSourceKey, message = "Zrodlo nie zostalo pobrane."): CompanyAssistantSourceState {
  return {
    ...COMPANY_ASSISTANT_SOURCES[key],
    status: "missing",
    message,
  };
}

export function sourceError(key: CompanyAssistantSourceKey, error: unknown): CompanyAssistantSourceState {
  return {
    ...COMPANY_ASSISTANT_SOURCES[key],
    status: "error",
    message: errorMessage(error),
  };
}

export function readCompanyAssistantSnapshot(payload: unknown): CompanyAssistantSnapshot {
  if (!isRecord(payload)) {
    throw new ApiContractError("/assistant-company", payload);
  }

  const raw = payload as RawCompanyAssistantSnapshot;

  return {
    dashboard: raw.dashboard === undefined ? undefined : readDashboardSnapshot(raw.dashboard),
    documents: raw.documents === undefined ? [] : readKnowledgeDocuments(raw.documents),
    workItems: raw.workItems === undefined ? [] : readWorkItems(raw.workItems),
    invoiceInbox: raw.invoiceInbox === undefined ? undefined : readInvoiceVerificationInbox(raw.invoiceInbox),
    sourceStates: Array.isArray(raw.sourceStates) ? raw.sourceStates : [],
  };
}

export function buildCompanyAssistantKpis(snapshot: CompanyAssistantSnapshot): CompanyAssistantKpis {
  const documentKpis = buildDocumentsKpis(snapshot.documents);
  const openWorkItems = snapshot.workItems.filter((item) => !item.is_closed && item.status !== "zamkniete").length;
  const invoicesToReview = snapshot.invoiceInbox?.summary.total_open_count ?? snapshot.dashboard?.cards.do_weryfikacji ?? 0;

  return {
    knowledgeDocuments: documentKpis.total,
    readyKnowledgeDocuments: documentKpis.ready,
    openWorkItems,
    invoicesToReview,
    decisionSignals: documentKpis.needsDecision + invoicesToReview + (snapshot.dashboard?.operational_alerts.length ?? 0),
  };
}

export function buildCompanyAssistantKnowledgeRows(snapshot: CompanyAssistantSnapshot, limit = 5): CompanyAssistantKnowledgeRow[] {
  return buildKnowledgeDocumentRows(snapshot.documents)
    .slice(0, limit)
    .map((row) => ({
      id: row.id,
      title: row.title,
      statusLabel: row.statusLabel,
      statusTone: row.statusTone,
      ownerLabel: row.ownerLabel,
      updatedLabel: row.updatedLabel,
    }));
}

export function buildCompanyAssistantAttentionRows(snapshot: CompanyAssistantSnapshot, limit = 8): CompanyAssistantAttentionRow[] {
  const workItemRows = buildWorkItemRows(snapshot.workItems).map((row) => ({
    id: `work-item-${row.id}`,
    typeLabel: "Work item",
    title: row.title,
    statusLabel: row.priorityLabel,
    statusTone: row.priorityTone,
    detail: `${row.slaLabel} / ${row.ownerLabel}`,
  }));

  const alertRows = (snapshot.dashboard?.operational_alerts ?? []).map((alert, index) => ({
    id: `dashboard-alert-${index}`,
    typeLabel: "Sygnal",
    title: readString(alert.title, "Alert operacyjny"),
    statusLabel: readString(alert.severity, "info"),
    statusTone: (alert.severity === "danger" ? "danger" : alert.severity === "warning" ? "warning" : alert.severity === "success" ? "ok" : "info") as CompanyAssistantAttentionRow["statusTone"],
    detail: readString(alert.description, "Brak opisu"),
  }));

  const invoiceRows = Object.entries(snapshot.invoiceInbox?.sections ?? {})
    .filter(([, section]) => section.count > 0)
    .map(([key, section]) => ({
      id: `invoice-section-${key}`,
      typeLabel: "Faktury",
      title: section.title,
      statusLabel: `${section.count}`,
      statusTone: "warning" as const,
      detail: readString(section.description, "Sekcja faktur wymaga uwagi."),
    }));

  return [...workItemRows, ...alertRows, ...invoiceRows].slice(0, limit);
}

export function hasCompanyAssistantData(status: CompanyAssistantStatus, snapshot: CompanyAssistantSnapshot | null): boolean {
  return status === "ready" && Boolean(snapshot) && !isCompanyAssistantEmpty(status, snapshot);
}

export function isCompanyAssistantEmpty(status: CompanyAssistantStatus, snapshot: CompanyAssistantSnapshot | null): boolean {
  if (status !== "ready" || !snapshot) {
    return false;
  }

  return (
    snapshot.documents.length === 0 &&
    snapshot.workItems.length === 0 &&
    (snapshot.dashboard?.operational_alerts.length ?? 0) === 0 &&
    (snapshot.invoiceInbox?.summary.total_open_count ?? 0) === 0
  );
}

export function canUseCompanyAssistantOrganizationScope(organizationId: string | number | null | undefined): boolean {
  return Boolean(String(organizationId ?? "").trim());
}

export function getCompanyAssistantErrorState(error: unknown): CompanyAssistantErrorState {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      return {
        status: "unauthenticated",
        title: "Sesja wygasla",
        description: "Zaloguj sie ponownie, aby zobaczyc Asystenta Firmowego.",
      };
    }
    if (error.status === 403) {
      return {
        status: "forbidden",
        title: "Brak dostepu do Asystenta Firmowego",
        description: "Twoje konto nie ma uprawnien do odczytu kontekstu organizacji.",
      };
    }
    if (error.status >= 500) {
      return {
        status: "server-error",
        title: "Backend nie zwrocil kontekstu Asystenta Firmowego",
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
      title: "Niepoprawny format Asystenta Firmowego",
      description: "Jedno ze zrodel odpowiedzialo, ale dane nie pasuja do minimalnego kontraktu widoku.",
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
    title: "Nie udalo sie pobrac kontekstu organizacji",
    description: error instanceof Error ? error.message : "Wystapil nieznany blad pobierania danych Asystenta Firmowego.",
  };
}
