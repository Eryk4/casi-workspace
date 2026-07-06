import { ApiContractError, ApiError } from "@/lib/api";
import type { DataViewErrorState, DataViewStatus } from "@/lib/types";
import { readInvoiceList } from "../invoices/api";
import type { InvoiceRecord } from "../invoices/types";
import type { ContractorRecord } from "../crm/crmModel";
import type { WorkItemRecord } from "../work-items/workItemsModel";

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

export type BillingMoneySummary = {
  receivables: number;
  overpayments: number;
  netBalance: number;
  attentionCount: number;
  activePayerCount: number;
  payerCount: number;
  lastPaymentLabel: string;
  headline: string;
  headlineTone: "ok" | "warning" | "info" | "neutral";
};

export type BillingAttentionItem = {
  id: string;
  title: string;
  reason: string;
  category: "Rozliczenia" | "Faktury" | "Kontrahenci" | "Sprawy";
  tone: "ok" | "warning" | "danger" | "info" | "neutral";
  href: string;
};

export type BillingInvoicePaymentRow = {
  id: string;
  href: string;
  invoiceLabel: string;
  contractorLabel: string;
  statusLabel: string;
  amountLabel: string;
  dateLabel: string;
  reasonLabel: string;
};

export type BillingContractorSettlementRow = {
  id: string;
  href: string;
  contractorLabel: string;
  contactLabel: string;
  balanceLabel: string;
  invoiceCountLabel: string;
  reasonLabel: string;
};

export type BillingRelatedWorkItemRow = {
  id: string;
  href: string;
  titleLabel: string;
  statusLabel: string;
  priorityLabel: string;
  reasonLabel: string;
};

export type BillingRecentPaymentRow = {
  id: string;
  payerLabel: string;
  amountLabel: string;
  dateLabel: string;
  titleLabel: string;
};

export type BillingCenterSnapshot = {
  balances: BillingBalanceRecord[];
  invoices: InvoiceRecord[];
  contractors: ContractorRecord[];
  workItems: WorkItemRecord[];
};

export const BILLING_BALANCES_ENDPOINT = "/billing/ledger/balances";
export const BILLING_READ_ONLY = true;
export const BILLING_CANONICAL_ROUTE = "/rozliczenia";
export const BILLING_LEGACY_ROUTE = "/kasa";
export const DEFAULT_CURRENCY = "PLN";
export const BILLING_ORGANIZATION_REQUIRED_TITLE = "Wybierz organizację, aby zobaczyć rozliczenia";
export const BILLING_ORGANIZATION_REQUIRED_DESCRIPTION =
  "Najpierw wskaż organizację w topbarze. Rozliczenia pokazują dane tylko dla wybranej firmy.";
export const BILLING_FORBIDDEN_WRITE_ACTIONS = [
  "Dodaj płatność",
  "Edytuj płatność",
  "Usuń płatność",
  "Dopasuj wpłatę",
  "Importuj wyciąg",
  "Wygeneruj naliczenia",
  "Zaksięguj",
  "Eksportuj",
];

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

function normalizeText(value: unknown): string {
  return typeof value === "string"
    ? value
        .trim()
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
    : "";
}

export function formatMoney(value: number | null | undefined, currency = DEFAULT_CURRENCY): string {
  const amount = typeof value === "number" && Number.isFinite(value) ? value : 0;
  return `${amount.toLocaleString("pl-PL", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })} ${currency}`;
}

function formatDateLabel(value: string | null | undefined, fallback = "Brak daty"): string {
  if (!value) {
    return fallback;
  }
  const [datePart, timePart] = value.replace("Z", "").split("T");
  return timePart ? `${datePart} ${timePart.slice(0, 5)}` : datePart || value;
}

function roundMoney(value: number): number {
  return Math.round(value * 100) / 100;
}

function getInvoiceId(invoice: InvoiceRecord): number | null {
  return readNumber(invoice.invoice_id) ?? readNumber(invoice.id) ?? null;
}

function getContractorId(contractor: ContractorRecord | InvoiceRecord): number | null {
  return readNumber("contractor_id" in contractor ? contractor.contractor_id : contractor.contractor_id) ?? null;
}

function getInvoiceAmount(invoice: InvoiceRecord): number {
  return readNumber(invoice.gross_amount) ?? 0;
}

function getInvoiceLabel(invoice: InvoiceRecord): string {
  const invoiceId = getInvoiceId(invoice);
  return readString(invoice.invoice_number || invoice.ksef_number, invoiceId ? `Faktura #${invoiceId}` : "Faktura");
}

function getInvoiceContractorLabel(invoice: InvoiceRecord): string {
  return readString(invoice.contractor_name || invoice.issuer_name, "Kontrahent nieznany");
}

function getContractorLabel(contractor: ContractorRecord): string {
  return readString(contractor.name, `Kontrahent #${contractor.contractor_id}`);
}

function getBalancePayerLabel(balance: BillingBalanceRecord): string {
  return readString(balance.display_name, `Płatnik #${balance.billing_payer_id}`);
}

function findBalanceForContractor(contractor: ContractorRecord, balances: BillingBalanceRecord[]): BillingBalanceRecord | undefined {
  const contractorName = normalizeText(contractor.name);
  if (!contractorName) {
    return undefined;
  }
  return balances.find((balance) => normalizeText(balance.display_name) === contractorName);
}

function isInvoiceAttentionCandidate(invoice: InvoiceRecord): boolean {
  const status = normalizeText(invoice.status);
  const workflow = normalizeText(invoice.workflow_state);
  const duplicate = normalizeText(invoice.duplicate_type);
  return (
    status.includes("weryfik") ||
    workflow.includes("pracy") ||
    workflow.includes("gotowa") ||
    duplicate.includes("podejrzenie") ||
    duplicate.includes("pewn") ||
    Boolean(invoice.flag_reason)
  );
}

function invoiceReason(invoice: InvoiceRecord): string {
  if (invoice.flag_reason) {
    return readString(invoice.flag_reason);
  }
  if (normalizeText(invoice.duplicate_type).includes("podejrzenie")) {
    return "Wymaga sprawdzenia ryzyka duplikatu.";
  }
  if (normalizeText(invoice.status).includes("weryfik")) {
    return "Czeka na weryfikację przed dalszym obiegiem.";
  }
  return "Warto sprawdzić ją przy przeglądzie rozliczeń.";
}

function isBillingRelatedWorkItem(item: WorkItemRecord, invoices: InvoiceRecord[], contractors: ContractorRecord[]): boolean {
  const metadata = isRecord(item.metadata) ? item.metadata : {};
  const invoiceIds = new Set(invoices.map(getInvoiceId).filter((id): id is number => typeof id === "number"));
  const contractorIds = new Set(contractors.map((contractor) => contractor.contractor_id));
  const metadataInvoiceId = readNumber(metadata.invoice_id ?? metadata.linked_invoice_id ?? metadata.invoiceId);
  const metadataContractorId = readNumber(metadata.contractor_id ?? metadata.contractorId);
  if (metadataInvoiceId && invoiceIds.has(metadataInvoiceId)) {
    return true;
  }
  if (metadataContractorId && contractorIds.has(metadataContractorId)) {
    return true;
  }

  const haystack = normalizeText(`${item.title ?? ""} ${item.description ?? ""} ${item.source_type ?? ""}`);
  return ["faktur", "platn", "rozlicz", "saldo", "koszt", "kontrah"].some((keyword) => haystack.includes(keyword));
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

export function readBillingInvoices(payload: unknown): InvoiceRecord[] {
  return readInvoiceList(payload);
}

export function getBillingErrorState(error: unknown): BillingErrorState {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      return {
        status: "unauthenticated",
        title: "Sesja wygasła",
        description: "Zaloguj się ponownie, aby zobaczyć rozliczenia.",
      };
    }
    if (error.status === 403) {
      return {
        status: "forbidden",
        title: "Brak dostępu do rozliczeń",
        description: "Twoje konto nie ma uprawnień do odczytu danych rozliczeniowych.",
      };
    }
    if (error.status >= 500) {
      return {
        status: "server-error",
        title: "Nie udało się pobrać rozliczeń",
        description: "Wystąpił błąd serwera. Spróbuj odświeżyć widok albo wróć do niego później.",
      };
    }
    return {
      status: "error",
      title: `Błąd odczytu (${error.status})`,
      description: error.message,
    };
  }

  if (error instanceof ApiContractError) {
    return {
      status: "error",
      title: "Niepoprawny format rozliczeń",
      description: "Odpowiedź nie pasuje do kontraktu widoku Rozliczenia.",
    };
  }

  if (error instanceof TypeError) {
    return {
      status: "error",
      title: "Problem z połączeniem",
      description: "Nie udało się połączyć z backendem. Sprawdź, czy aplikacja działa lokalnie i spróbuj ponownie.",
    };
  }

  return {
    status: "error",
    title: "Nie udało się pobrać rozliczeń",
    description: error instanceof Error ? error.message : "Wystąpił nieznany błąd pobierania rozliczeń.",
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
      payerLabel: getBalancePayerLabel(item),
      contactLabel: readString(item.contact_phone || item.email || item.payment_identifier, "Brak kontaktu"),
      statusLabel: balanceDue > 0 ? "Do zapłaty" : balanceDue < 0 ? "Nadpłata" : item.is_active === false ? "Nieaktywny" : "Rozliczony",
      statusTone: billingBalanceTone(item),
      totalChargesLabel: formatMoney(item.total_charges, DEFAULT_CURRENCY),
      totalMatchesLabel: formatMoney(item.total_matches, DEFAULT_CURRENCY),
      balanceDueLabel: formatMoney(balanceDue, DEFAULT_CURRENCY),
      lastPaymentLabel: item.last_payment_at
        ? `${formatDateLabel(item.last_payment_at)} · ${formatMoney(lastPaymentAmount, currency)}`
        : "Brak wpłat",
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

export function buildBillingMoneySummary(items: BillingBalanceRecord[], attentionCount = 0): BillingMoneySummary {
  const receivables = roundMoney(items.reduce((sum, item) => sum + Math.max(item.balance_due ?? 0, 0), 0));
  const overpayments = roundMoney(Math.abs(items.reduce((sum, item) => sum + Math.min(item.balance_due ?? 0, 0), 0)));
  const netBalance = roundMoney(items.reduce((sum, item) => sum + (item.balance_due ?? 0), 0));
  const latestPayment = items
    .filter((item) => item.last_payment_at)
    .sort((a, b) => String(b.last_payment_at).localeCompare(String(a.last_payment_at)))[0];

  return {
    receivables,
    overpayments,
    netBalance,
    attentionCount,
    activePayerCount: items.filter((item) => item.is_active !== false).length,
    payerCount: items.length,
    lastPaymentLabel: latestPayment?.last_payment_at
      ? `${formatDateLabel(latestPayment.last_payment_at)} · ${getBalancePayerLabel(latestPayment)}`
      : "Brak ostatniej wpłaty",
    headline: receivables > 0 ? "Są należności do kontroli" : overpayments > 0 ? "Są nadpłaty do wyjaśnienia" : "Rozliczenia wyglądają spokojnie",
    headlineTone: receivables > 0 ? "warning" : overpayments > 0 ? "info" : "ok",
  };
}

export function buildBillingAttentionItems(snapshot: BillingCenterSnapshot, limit = 6): BillingAttentionItem[] {
  const balanceItems = snapshot.balances
    .filter((item) => (item.balance_due ?? 0) > 0)
    .sort((a, b) => (b.balance_due ?? 0) - (a.balance_due ?? 0))
    .slice(0, 2)
    .map((item) => ({
      id: `balance-${item.billing_payer_id}`,
      title: `Saldo do wyjaśnienia: ${getBalancePayerLabel(item)}`,
      reason: `Do rozliczenia pozostaje ${formatMoney(item.balance_due, DEFAULT_CURRENCY)}.`,
      category: "Rozliczenia" as const,
      tone: "warning" as const,
      href: BILLING_CANONICAL_ROUTE,
    }));

  const invoiceItems = snapshot.invoices
    .filter(isInvoiceAttentionCandidate)
    .sort((a, b) => getInvoiceAmount(b) - getInvoiceAmount(a))
    .slice(0, 2)
    .map((invoice) => {
      const invoiceId = getInvoiceId(invoice);
      return {
        id: `invoice-${invoiceId ?? getInvoiceLabel(invoice)}`,
        title: getInvoiceLabel(invoice),
        reason: invoiceReason(invoice),
        category: "Faktury" as const,
        tone: normalizeText(invoice.duplicate_type).includes("pewn") ? ("danger" as const) : ("warning" as const),
        href: invoiceId ? `/faktury/${invoiceId}` : "/faktury",
      };
    });

  const workItemItems = snapshot.workItems
    .filter((item) => !item.is_closed && isBillingRelatedWorkItem(item, snapshot.invoices, snapshot.contractors))
    .sort((a, b) => (b.priority_score ?? 0) - (a.priority_score ?? 0))
    .slice(0, 2)
    .map((item) => ({
      id: `work-item-${item.work_item_id}`,
      title: readString(item.title, `Sprawa #${item.work_item_id}`),
      reason: item.is_sla_overdue || item.is_due_overdue ? "Termin wymaga uwagi przy rozliczeniach." : "Sprawa może wpływać na płatność lub fakturę.",
      category: "Sprawy" as const,
      tone: item.is_sla_overdue || item.is_due_overdue ? ("danger" as const) : ("info" as const),
      href: `/work-items/${item.work_item_id}`,
    }));

  const contractorItems = snapshot.contractors
    .filter((contractor) => (contractor.invoice_count ?? 0) > 0 && !contractor.email && !contractor.phone)
    .slice(0, 1)
    .map((contractor) => ({
      id: `contractor-${contractor.contractor_id}`,
      title: getContractorLabel(contractor),
      reason: "Kontrahent ma faktury, ale brakuje kontaktu do szybkiego wyjaśnienia płatności.",
      category: "Kontrahenci" as const,
      tone: "info" as const,
      href: `/crm/${contractor.contractor_id}`,
    }));

  return [...balanceItems, ...invoiceItems, ...workItemItems, ...contractorItems].slice(0, limit);
}

export function buildBillingInvoiceRows(invoices: InvoiceRecord[], limit = 8): BillingInvoicePaymentRow[] {
  return invoices
    .slice()
    .sort((a, b) => {
      const attentionDiff = Number(isInvoiceAttentionCandidate(b)) - Number(isInvoiceAttentionCandidate(a));
      if (attentionDiff) {
        return attentionDiff;
      }
      return String(b.incoming_date || b.issue_date || "").localeCompare(String(a.incoming_date || a.issue_date || ""));
    })
    .slice(0, limit)
    .map((invoice, index) => {
      const invoiceId = getInvoiceId(invoice);
      return {
        id: String(invoiceId ?? index),
        href: invoiceId ? `/faktury/${invoiceId}` : "/faktury",
        invoiceLabel: getInvoiceLabel(invoice),
        contractorLabel: getInvoiceContractorLabel(invoice),
        statusLabel: readString(invoice.status || invoice.workflow_state, "Status nieznany"),
        amountLabel: formatMoney(getInvoiceAmount(invoice), invoice.currency || DEFAULT_CURRENCY),
        dateLabel: formatDateLabel(invoice.incoming_date || invoice.issue_date, "Brak daty"),
        reasonLabel: invoiceReason(invoice),
      };
    });
}

export function buildBillingContractorRows(
  contractors: ContractorRecord[],
  balances: BillingBalanceRecord[],
  limit = 8,
): BillingContractorSettlementRow[] {
  return contractors
    .slice()
    .sort((a, b) => (b.invoice_count ?? 0) - (a.invoice_count ?? 0))
    .slice(0, limit)
    .map((contractor) => {
      const balance = findBalanceForContractor(contractor, balances);
      const balanceDue = balance?.balance_due ?? 0;
      return {
        id: String(contractor.contractor_id),
        href: `/crm/${contractor.contractor_id}`,
        contractorLabel: getContractorLabel(contractor),
        contactLabel: readString(contractor.email || contractor.phone, "Brak kontaktu"),
        balanceLabel: balance ? formatMoney(balanceDue, DEFAULT_CURRENCY) : "Brak salda w rozliczeniach",
        invoiceCountLabel: `${contractor.invoice_count ?? 0}`,
        reasonLabel: balanceDue > 0 ? "Ma saldo do wyjaśnienia." : (contractor.invoice_count ?? 0) > 0 ? "Ma historię faktur w systemie." : "W katalogu kontrahentów.",
      };
    });
}

export function buildBillingRelatedWorkItemRows(
  workItems: WorkItemRecord[],
  invoices: InvoiceRecord[],
  contractors: ContractorRecord[],
  limit = 8,
): BillingRelatedWorkItemRow[] {
  return workItems
    .filter((item) => !item.is_closed && isBillingRelatedWorkItem(item, invoices, contractors))
    .sort((a, b) => (b.priority_score ?? 0) - (a.priority_score ?? 0))
    .slice(0, limit)
    .map((item) => ({
      id: String(item.work_item_id),
      href: `/work-items/${item.work_item_id}`,
      titleLabel: readString(item.title, `Sprawa #${item.work_item_id}`),
      statusLabel: readString(item.status, "Status nieznany"),
      priorityLabel: readString(item.priority_level, "Priorytet nieznany"),
      reasonLabel: item.description || "Sprawa powiązana z fakturą, płatnością albo kontrahentem.",
    }));
}

export function buildBillingRecentPaymentRows(items: BillingBalanceRecord[], limit = 5): BillingRecentPaymentRow[] {
  return items
    .filter((item) => item.last_payment_at)
    .sort((a, b) => String(b.last_payment_at).localeCompare(String(a.last_payment_at)))
    .slice(0, limit)
    .map((item) => ({
      id: String(item.billing_payer_id),
      payerLabel: getBalancePayerLabel(item),
      amountLabel: formatMoney(item.last_payment_amount, item.last_payment_currency || DEFAULT_CURRENCY),
      dateLabel: formatDateLabel(item.last_payment_at),
      titleLabel: readString(item.last_payment_title, "Ostatnia wpłata"),
    }));
}

export function hasBillingData(status: BillingStatus, items: BillingBalanceRecord[] | null): boolean {
  return status === "ready" && Boolean(items?.length);
}

export function hasBillingCenterData(status: BillingStatus, snapshot: BillingCenterSnapshot | null): boolean {
  return (
    status === "ready" &&
    Boolean(
      snapshot &&
        (snapshot.balances.length || snapshot.invoices.length || snapshot.contractors.length || snapshot.workItems.length),
    )
  );
}

export function isBillingEmpty(status: BillingStatus, items: BillingBalanceRecord[] | null): boolean {
  return status === "ready" && Array.isArray(items) && items.length === 0;
}

export function isBillingCenterEmpty(status: BillingStatus, snapshot: BillingCenterSnapshot | null): boolean {
  if (status !== "ready" || !snapshot) {
    return false;
  }

  return (
    snapshot.balances.length === 0 &&
    snapshot.invoices.length === 0 &&
    snapshot.contractors.length === 0 &&
    snapshot.workItems.length === 0
  );
}

export function canUseBillingOrganizationScope(organizationId: string | number | null | undefined): boolean {
  return organizationId !== null && organizationId !== undefined && String(organizationId).trim().length > 0;
}

export function billingScreenHasForbiddenTechnicalText(values: string[]): boolean {
  const normalized = values.map(normalizeText).join(" ");
  return ["storage_key", "data/magazyn", "c:\\users", "token", "secret", "connection string", "raw json", "payload"].some((term) =>
    normalized.includes(term),
  );
}
