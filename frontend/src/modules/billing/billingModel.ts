import { ApiContractError, ApiError } from "@/lib/api";
import type { DataViewErrorState, DataViewStatus } from "@/lib/types";

export type BillingStatus = DataViewStatus;

export type BillingErrorState = DataViewErrorState<BillingStatus>;

export type BillingBalanceRecord = {
  billing_payer_id: number;
  display_name?: string;
  contact_phone?: string | null;
  payment_identifier?: string | null;
  email?: string | null;
  is_active?: boolean;
  total_charges?: number;
  total_matches?: number;
  balance_due?: number;
  last_payment_at?: string | null;
  last_payment_amount?: number | null;
  last_payment_currency?: string | null;
  last_payment_title?: string | null;
  last_payment_reference?: string | null;
  matched_payment_count?: number;
};

export type BillingBalanceViewRow = {
  id: string;
  payerLabel: string;
  contactLabel: string;
  statusLabel: string;
  statusTone: "ok" | "warning" | "danger" | "info" | "neutral";
  totalChargesLabel: string;
  totalMatchesLabel: string;
  balanceDueLabel: string;
  lastPaymentLabel: string;
  matchedPaymentCountLabel: string;
};

export type BillingKpis = {
  payerCount: number;
  activePayerCount: number;
  totalCharges: number;
  totalMatches: number;
  totalBalanceDue: number;
  overdueCount: number;
  paidOrSettledCount: number;
};

export const BILLING_BALANCES_ENDPOINT = "/billing/ledger/balances";
export const BILLING_READ_ONLY = true;
export const DEFAULT_CURRENCY = "PLN";
export const BILLING_ORGANIZATION_REQUIRED_TITLE = "Wybierz organizacje, aby zobaczyc rozliczenia";
export const BILLING_ORGANIZATION_REQUIRED_DESCRIPTION =
  "Globalny uzytkownik musi najpierw wskazac organizacje w topbarze. Dopiero wtedy frontend przekaze organization_id do /api/billing/ledger/balances.";

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

export function formatMoney(value: number | null | undefined, currency = DEFAULT_CURRENCY): string {
  const amount = typeof value === "number" && Number.isFinite(value) ? value : 0;
  return `${amount.toLocaleString("pl-PL", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })} ${currency}`;
}

function formatDateLabel(value: string | null | undefined): string {
  if (!value) {
    return "Brak wplat";
  }
  const [datePart, timePart] = value.replace("Z", "").split("T");
  return timePart ? `${datePart} ${timePart.slice(0, 5)}` : datePart || value;
}

export function readBillingBalances(payload: unknown): BillingBalanceRecord[] {
  if (!Array.isArray(payload)) {
    throw new ApiContractError(BILLING_BALANCES_ENDPOINT, payload);
  }

  return payload.map((item) => {
    if (!isRecord(item)) {
      throw new ApiContractError(BILLING_BALANCES_ENDPOINT, payload);
    }

    const payerId = readNumber(item.billing_payer_id);
    if (!payerId) {
      throw new ApiContractError(BILLING_BALANCES_ENDPOINT, payload);
    }

    return {
      billing_payer_id: payerId,
      display_name: readOptionalString(item.display_name),
      contact_phone: readOptionalString(item.contact_phone) ?? null,
      payment_identifier: readOptionalString(item.payment_identifier) ?? null,
      email: readOptionalString(item.email) ?? null,
      is_active: readBoolean(item.is_active),
      total_charges: readNumber(item.total_charges) ?? 0,
      total_matches: readNumber(item.total_matches) ?? 0,
      balance_due: readNumber(item.balance_due) ?? 0,
      last_payment_at: readOptionalString(item.last_payment_at) ?? null,
      last_payment_amount: readNumber(item.last_payment_amount) ?? null,
      last_payment_currency: readOptionalString(item.last_payment_currency) ?? null,
      last_payment_title: readOptionalString(item.last_payment_title) ?? null,
      last_payment_reference: readOptionalString(item.last_payment_reference) ?? null,
      matched_payment_count: readNumber(item.matched_payment_count) ?? 0,
    };
  });
}

export function getBillingErrorState(error: unknown): BillingErrorState {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      return {
        status: "unauthenticated",
        title: "Sesja wygasla",
        description: "Zaloguj sie ponownie, aby zobaczyc rozliczenia.",
      };
    }
    if (error.status === 403) {
      return {
        status: "forbidden",
        title: "Brak dostepu do rozliczen",
        description: "Twoje konto nie ma uprawnien do odczytu danych billingowych.",
      };
    }
    if (error.status >= 500) {
      return {
        status: "server-error",
        title: "Backend nie zwrocil rozliczen",
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
      title: "Niepoprawny format rozliczen",
      description: "Backend odpowiedzial, ale dane nie pasuja do minimalnego kontraktu widoku Rozliczenia.",
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
    title: "Nie udalo sie pobrac rozliczen",
    description: error instanceof Error ? error.message : "Wystapil nieznany blad pobierania rozliczen.",
  };
}

export function billingBalanceTone(item: BillingBalanceRecord): BillingBalanceViewRow["statusTone"] {
  const balanceDue = item.balance_due ?? 0;
  if (balanceDue > 0) {
    return "warning";
  }
  if (balanceDue < 0) {
    return "info";
  }
  if (item.is_active === false) {
    return "neutral";
  }
  return "ok";
}

export function buildBillingBalanceRows(items: BillingBalanceRecord[]): BillingBalanceViewRow[] {
  return items.map((item) => {
    const balanceDue = item.balance_due ?? 0;
    const currency = item.last_payment_currency || DEFAULT_CURRENCY;
    const lastPaymentAmount = item.last_payment_amount ?? 0;

    return {
      id: String(item.billing_payer_id),
      payerLabel: readString(item.display_name, `Platnik #${item.billing_payer_id}`),
      contactLabel: readString(item.contact_phone || item.email || item.payment_identifier, "Brak kontaktu"),
      statusLabel: balanceDue > 0 ? "Do zaplaty" : balanceDue < 0 ? "Nadplata" : item.is_active === false ? "Nieaktywny" : "Rozliczony",
      statusTone: billingBalanceTone(item),
      totalChargesLabel: formatMoney(item.total_charges, DEFAULT_CURRENCY),
      totalMatchesLabel: formatMoney(item.total_matches, DEFAULT_CURRENCY),
      balanceDueLabel: formatMoney(balanceDue, DEFAULT_CURRENCY),
      lastPaymentLabel: item.last_payment_at
        ? `${formatDateLabel(item.last_payment_at)} · ${formatMoney(lastPaymentAmount, currency)}`
        : "Brak wplat",
      matchedPaymentCountLabel: String(item.matched_payment_count ?? 0),
    };
  });
}

export function buildBillingKpis(items: BillingBalanceRecord[]): BillingKpis {
  return {
    payerCount: items.length,
    activePayerCount: items.filter((item) => item.is_active !== false).length,
    totalCharges: roundMoney(items.reduce((sum, item) => sum + (item.total_charges ?? 0), 0)),
    totalMatches: roundMoney(items.reduce((sum, item) => sum + (item.total_matches ?? 0), 0)),
    totalBalanceDue: roundMoney(items.reduce((sum, item) => sum + (item.balance_due ?? 0), 0)),
    overdueCount: items.filter((item) => (item.balance_due ?? 0) > 0).length,
    paidOrSettledCount: items.filter((item) => (item.balance_due ?? 0) <= 0).length,
  };
}

function roundMoney(value: number): number {
  return Math.round(value * 100) / 100;
}

export function hasBillingData(status: BillingStatus, items: BillingBalanceRecord[] | null): boolean {
  return status === "ready" && Boolean(items?.length);
}

export function isBillingEmpty(status: BillingStatus, items: BillingBalanceRecord[] | null): boolean {
  return status === "ready" && Array.isArray(items) && items.length === 0;
}

export function canUseBillingOrganizationScope(organizationId: string | number | null | undefined): boolean {
  return organizationId !== null && organizationId !== undefined && String(organizationId).trim().length > 0;
}
