import { ApiContractError, ApiError } from "@/lib/api";
import type { DataViewErrorState, DataViewStatus } from "@/lib/types";

export type CrmStatus = DataViewStatus;

export type CrmErrorState = DataViewErrorState<CrmStatus>;

export type ContractorRecord = {
  contractor_id: number;
  name?: string;
  nip?: string | null;
  email?: string | null;
  phone?: string | null;
  is_new?: boolean;
  last_invoice_date?: string | null;
  last_invoice_number?: string | null;
  invoice_count?: number;
  notes?: string | null;
  organization_name?: string | null;
  organization_slug?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type ContractorViewRow = {
  id: string;
  nameLabel: string;
  nipLabel: string;
  contactLabel: string;
  statusLabel: string;
  statusTone: "ok" | "warning" | "danger" | "info" | "neutral";
  invoiceCountLabel: string;
  lastInvoiceLabel: string;
  organizationLabel: string;
  updatedLabel: string;
};

export type CrmKpis = {
  total: number;
  newCount: number;
  knownCount: number;
  missingContactCount: number;
  linkedToInvoicesCount: number;
};

export const CRM_CONTRACTORS_ENDPOINT = "/contractors";
export const CRM_READ_ONLY = true;
export const CRM_PIPELINE_ENABLED = false;
export const CRM_ORGANIZATION_REQUIRED_TITLE = "Wybierz organizacje, aby zobaczyc CRM";
export const CRM_ORGANIZATION_REQUIRED_DESCRIPTION =
  "Globalny uzytkownik musi najpierw wskazac organizacje w topbarze. Dopiero wtedy frontend przekaze organization_id do /api/contractors.";

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

function formatDateLabel(value: string | null | undefined, fallback = "Brak daty"): string {
  if (!value) {
    return fallback;
  }
  const [datePart, timePart] = value.replace("Z", "").split("T");
  return timePart ? `${datePart} ${timePart.slice(0, 5)}` : datePart || value;
}

export function readContractors(payload: unknown): ContractorRecord[] {
  if (!Array.isArray(payload)) {
    throw new ApiContractError(CRM_CONTRACTORS_ENDPOINT, payload);
  }

  return payload.map((item) => {
    if (!isRecord(item)) {
      throw new ApiContractError(CRM_CONTRACTORS_ENDPOINT, payload);
    }

    const contractorId = readNumber(item.contractor_id);
    if (!contractorId) {
      throw new ApiContractError(CRM_CONTRACTORS_ENDPOINT, payload);
    }

    return {
      contractor_id: contractorId,
      name: readOptionalString(item.name),
      nip: readOptionalString(item.nip) ?? null,
      email: readOptionalString(item.email) ?? null,
      phone: readOptionalString(item.phone) ?? null,
      is_new: readBoolean(item.is_new),
      last_invoice_date: readOptionalString(item.last_invoice_date) ?? null,
      last_invoice_number: readOptionalString(item.last_invoice_number) ?? null,
      invoice_count: readNumber(item.invoice_count) ?? 0,
      notes: readOptionalString(item.notes) ?? null,
      organization_name: readOptionalString(item.organization_name) ?? null,
      organization_slug: readOptionalString(item.organization_slug) ?? null,
      created_at: readOptionalString(item.created_at) ?? null,
      updated_at: readOptionalString(item.updated_at) ?? null,
    };
  });
}

export function getCrmErrorState(error: unknown): CrmErrorState {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      return {
        status: "unauthenticated",
        title: "Sesja wygasla",
        description: "Zaloguj sie ponownie, aby zobaczyc katalog kontrahentow.",
      };
    }
    if (error.status === 403) {
      return {
        status: "forbidden",
        title: "Brak dostepu do CRM",
        description: "Twoje konto nie ma uprawnien do odczytu kontrahentow.",
      };
    }
    if (error.status >= 500) {
      return {
        status: "server-error",
        title: "Backend nie zwrocil kontrahentow",
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
      title: "Niepoprawny format CRM",
      description: "Backend odpowiedzial, ale dane nie pasuja do minimalnego kontraktu katalogu kontrahentow.",
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
    title: "Nie udalo sie pobrac kontrahentow",
    description: error instanceof Error ? error.message : "Wystapil nieznany blad pobierania kontrahentow.",
  };
}

export function contractorStatusTone(item: ContractorRecord): ContractorViewRow["statusTone"] {
  if (item.is_new) {
    return "info";
  }
  if ((item.invoice_count ?? 0) > 0) {
    return "ok";
  }
  return "neutral";
}

export function buildContractorRows(items: ContractorRecord[]): ContractorViewRow[] {
  return items.map((item) => ({
    id: String(item.contractor_id),
    nameLabel: readString(item.name, `Kontrahent #${item.contractor_id}`),
    nipLabel: readString(item.nip, "Brak NIP"),
    contactLabel: readString(item.email || item.phone, "Brak kontaktu"),
    statusLabel: item.is_new ? "Nowy" : (item.invoice_count ?? 0) > 0 ? "Powiazany" : "Katalog",
    statusTone: contractorStatusTone(item),
    invoiceCountLabel: String(item.invoice_count ?? 0),
    lastInvoiceLabel: item.last_invoice_number
      ? `${item.last_invoice_number} · ${formatDateLabel(item.last_invoice_date, "brak daty")}`
      : formatDateLabel(item.last_invoice_date, "Brak faktur"),
    organizationLabel: readString(item.organization_name, "Organizacja nieznana"),
    updatedLabel: formatDateLabel(item.updated_at || item.created_at, "Brak aktualizacji"),
  }));
}

export function buildCrmKpis(items: ContractorRecord[]): CrmKpis {
  return {
    total: items.length,
    newCount: items.filter((item) => item.is_new).length,
    knownCount: items.filter((item) => !item.is_new).length,
    missingContactCount: items.filter((item) => !item.email && !item.phone).length,
    linkedToInvoicesCount: items.filter((item) => (item.invoice_count ?? 0) > 0).length,
  };
}

export function hasCrmData(status: CrmStatus, items: ContractorRecord[] | null): boolean {
  return status === "ready" && Boolean(items?.length);
}

export function isCrmEmpty(status: CrmStatus, items: ContractorRecord[] | null): boolean {
  return status === "ready" && Array.isArray(items) && items.length === 0;
}

export function canUseCrmOrganizationScope(organizationId: string | number | null | undefined): boolean {
  return organizationId !== null && organizationId !== undefined && String(organizationId).trim().length > 0;
}
