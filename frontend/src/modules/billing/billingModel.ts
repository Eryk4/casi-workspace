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

export type BillingPayerRecord = {
  billing_payer_id: number;
  display_name?: string;
  contact_phone?: string | null;
  payment_identifier?: string | null;
  email?: string | null;
  has_large_family_card?: boolean;
  notes?: string | null;
  is_active?: boolean;
  billing_total_charges?: number;
  billing_total_matches?: number;
  billing_balance_due?: number;
  billing_last_payment_at?: string | null;
  billing_last_payment_amount?: number | null;
  billing_last_payment_currency?: string | null;
  billing_last_payment_title?: string | null;
  billing_matched_payment_count?: number;
  latest_payment_date?: string | null;
  latest_payment_amount?: number | null;
  latest_payment_currency?: string | null;
  latest_payment_title?: string | null;
};

export type BillingStudentRecord = {
  billing_student_id: number;
  organization_id?: number;
  billing_payer_id: number;
  billing_school_id?: number | null;
  billing_model_id?: number | null;
  full_name?: string | null;
  lesson_day?: string | null;
  family_billing_order?: number;
  group_name?: string | null;
  notes?: string | null;
  is_active?: boolean;
  payer_label?: string | null;
  payer_display_name?: string | null;
  payer_contact_phone?: string | null;
  payer_payment_identifier?: string | null;
  payer_is_active?: boolean;
  school_full_name?: string | null;
  school_short_name?: string | null;
  school_city?: string | null;
  model_name?: string | null;
  model_school_year?: string | null;
  model_lesson_day?: string | null;
  model_settlement_mode?: string | null;
  family_last_payment_date?: string | null;
  family_last_payment_amount?: number | null;
  family_last_payment_currency?: string | null;
  family_last_payment_title?: string | null;
  family_balance_due?: number | null;
};

export type BillingChargeRecord = {
  billing_charge_id: number;
  billing_payer_id: number;
  billing_student_id?: number | null;
  period_label?: string | null;
  due_date?: string | null;
  base_amount?: number;
  intro_free_discount_amount?: number;
  sibling_discount_amount?: number;
  large_family_discount_amount?: number;
  total_amount?: number;
  status?: string | null;
  model_name?: string | null;
  student_full_name?: string | null;
  payer_display_name?: string | null;
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

export type BillingBalanceExplanationRow = {
  id: string;
  payerLabel: string;
  familyTypeLabel: string;
  chargedLabel: string;
  paidLabel: string;
  balanceLabel: string;
  balanceMeaningLabel: string;
  lastPaymentLabel: string;
  topItemsLabel: string;
  explanationLabel: string;
  statusTone: "ok" | "warning" | "danger" | "info" | "neutral";
};

export type BillingFamilyFoundationRow = {
  id: string;
  familyLabel: string;
  payerLabel: string;
  contactLabel: string;
  studentsLabel: string;
  studentSummaryLabel: string;
  siblingLabel: string;
  statusLabel: string;
  statusTone: "ok" | "warning" | "danger" | "info" | "neutral";
  balanceLabel: string;
  lastPaymentLabel: string;
  contextLabel: string;
};

export type BillingCompanyClientRow = {
  id: string;
  href: string;
  companyLabel: string;
  contactLabel: string;
  invoiceCountLabel: string;
  balanceLabel: string;
  contextLabel: string;
  statusLabel: string;
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
  payers: BillingPayerRecord[];
  students: BillingStudentRecord[];
  charges: BillingChargeRecord[];
  invoices: InvoiceRecord[];
  contractors: ContractorRecord[];
  workItems: WorkItemRecord[];
};

export const BILLING_BALANCES_ENDPOINT = "/billing/ledger/balances";
export const BILLING_PAYERS_ENDPOINT = "/billing/payers";
export const BILLING_STUDENTS_ENDPOINT = "/billing/students";
export const BILLING_CHARGES_ENDPOINT = "/billing/charges";
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

export function readBillingPayers(payload: unknown): BillingPayerRecord[] {
  if (!Array.isArray(payload)) {
    throw new ApiContractError(BILLING_PAYERS_ENDPOINT, payload);
  }

  return payload.map((item) => {
    if (!isRecord(item)) {
      throw new ApiContractError(BILLING_PAYERS_ENDPOINT, payload);
    }

    const payerId = readNumber(item.billing_payer_id);
    if (!payerId) {
      throw new ApiContractError(BILLING_PAYERS_ENDPOINT, payload);
    }

    return {
      billing_payer_id: payerId,
      display_name: readOptionalString(item.display_name),
      contact_phone: readOptionalString(item.contact_phone) ?? null,
      payment_identifier: readOptionalString(item.payment_identifier) ?? null,
      email: readOptionalString(item.email) ?? null,
      has_large_family_card: readBoolean(item.has_large_family_card),
      notes: readOptionalString(item.notes) ?? null,
      is_active: readBoolean(item.is_active),
      billing_total_charges: readNumber(item.billing_total_charges) ?? 0,
      billing_total_matches: readNumber(item.billing_total_matches) ?? 0,
      billing_balance_due: readNumber(item.billing_balance_due) ?? 0,
      billing_last_payment_at: readOptionalString(item.billing_last_payment_at) ?? null,
      billing_last_payment_amount: readNumber(item.billing_last_payment_amount) ?? null,
      billing_last_payment_currency: readOptionalString(item.billing_last_payment_currency) ?? null,
      billing_last_payment_title: readOptionalString(item.billing_last_payment_title) ?? null,
      billing_matched_payment_count: readNumber(item.billing_matched_payment_count) ?? 0,
      latest_payment_date: readOptionalString(item.latest_payment_date) ?? null,
      latest_payment_amount: readNumber(item.latest_payment_amount) ?? null,
      latest_payment_currency: readOptionalString(item.latest_payment_currency) ?? null,
      latest_payment_title: readOptionalString(item.latest_payment_title) ?? null,
    };
  });
}

export function readBillingStudents(payload: unknown): BillingStudentRecord[] {
  if (!Array.isArray(payload)) {
    throw new ApiContractError(BILLING_STUDENTS_ENDPOINT, payload);
  }

  return payload.map((item) => {
    if (!isRecord(item)) {
      throw new ApiContractError(BILLING_STUDENTS_ENDPOINT, payload);
    }

    const studentId = readNumber(item.billing_student_id);
    const payerId = readNumber(item.billing_payer_id);
    if (!studentId || !payerId) {
      throw new ApiContractError(BILLING_STUDENTS_ENDPOINT, payload);
    }

    return {
      billing_student_id: studentId,
      organization_id: readNumber(item.organization_id),
      billing_payer_id: payerId,
      billing_school_id: readNumber(item.billing_school_id) ?? null,
      billing_model_id: readNumber(item.billing_model_id) ?? null,
      full_name: readOptionalString(item.full_name) ?? null,
      lesson_day: readOptionalString(item.lesson_day) ?? null,
      family_billing_order: readNumber(item.family_billing_order) ?? 1,
      group_name: readOptionalString(item.group_name) ?? null,
      notes: readOptionalString(item.notes) ?? null,
      is_active: readBoolean(item.is_active),
      payer_label: readOptionalString(item.payer_label) ?? null,
      payer_display_name: readOptionalString(item.payer_display_name) ?? null,
      payer_contact_phone: readOptionalString(item.payer_contact_phone) ?? null,
      payer_payment_identifier: readOptionalString(item.payer_payment_identifier) ?? null,
      payer_is_active: readBoolean(item.payer_is_active),
      school_full_name: readOptionalString(item.school_full_name) ?? null,
      school_short_name: readOptionalString(item.school_short_name) ?? null,
      school_city: readOptionalString(item.school_city) ?? null,
      model_name: readOptionalString(item.model_name) ?? null,
      model_school_year: readOptionalString(item.model_school_year) ?? null,
      model_lesson_day: readOptionalString(item.model_lesson_day) ?? null,
      model_settlement_mode: readOptionalString(item.model_settlement_mode) ?? null,
      family_last_payment_date: readOptionalString(item.family_last_payment_date) ?? null,
      family_last_payment_amount: readNumber(item.family_last_payment_amount) ?? null,
      family_last_payment_currency: readOptionalString(item.family_last_payment_currency) ?? null,
      family_last_payment_title: readOptionalString(item.family_last_payment_title) ?? null,
      family_balance_due: readNumber(item.family_balance_due) ?? null,
    };
  });
}

export function readBillingCharges(payload: unknown): BillingChargeRecord[] {
  if (!Array.isArray(payload)) {
    throw new ApiContractError(BILLING_CHARGES_ENDPOINT, payload);
  }

  return payload.map((item) => {
    if (!isRecord(item)) {
      throw new ApiContractError(BILLING_CHARGES_ENDPOINT, payload);
    }

    const chargeId = readNumber(item.billing_charge_id);
    const payerId = readNumber(item.billing_payer_id);
    if (!chargeId || !payerId) {
      throw new ApiContractError(BILLING_CHARGES_ENDPOINT, payload);
    }

    return {
      billing_charge_id: chargeId,
      billing_payer_id: payerId,
      billing_student_id: readNumber(item.billing_student_id) ?? null,
      period_label: readOptionalString(item.period_label) ?? null,
      due_date: readOptionalString(item.due_date) ?? null,
      base_amount: readNumber(item.base_amount) ?? 0,
      intro_free_discount_amount: readNumber(item.intro_free_discount_amount) ?? 0,
      sibling_discount_amount: readNumber(item.sibling_discount_amount) ?? 0,
      large_family_discount_amount: readNumber(item.large_family_discount_amount) ?? 0,
      total_amount: readNumber(item.total_amount) ?? 0,
      status: readOptionalString(item.status) ?? null,
      model_name: readOptionalString(item.model_name) ?? null,
      student_full_name: readOptionalString(item.student_full_name) ?? null,
      payer_display_name: readOptionalString(item.payer_display_name) ?? null,
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

export function buildBillingFamilyFoundationRows(
  payers: BillingPayerRecord[],
  students: BillingStudentRecord[],
  balances: BillingBalanceRecord[],
  limit = 8,
): BillingFamilyFoundationRow[] {
  const studentsByPayer = new Map<number, BillingStudentRecord[]>();
  students.forEach((student) => {
    const current = studentsByPayer.get(student.billing_payer_id) ?? [];
    current.push(student);
    studentsByPayer.set(student.billing_payer_id, current);
  });

  return payers
    .slice()
    .sort((a, b) => {
      const balanceDiff = Math.abs(b.billing_balance_due ?? 0) - Math.abs(a.billing_balance_due ?? 0);
      if (balanceDiff) {
        return balanceDiff;
      }
      return getBalancePayerLabel({ billing_payer_id: a.billing_payer_id, display_name: a.display_name }).localeCompare(
        getBalancePayerLabel({ billing_payer_id: b.billing_payer_id, display_name: b.display_name }),
        "pl",
      );
    })
    .slice(0, limit)
    .map((payer) => {
      const payerStudents = (studentsByPayer.get(payer.billing_payer_id) ?? [])
        .slice()
        .sort((a, b) => (a.family_billing_order ?? 1) - (b.family_billing_order ?? 1));
      const studentNames = payerStudents.map((student) => readString(student.full_name, "Uczeń bez nazwy"));
      const balance = balances.find((item) => item.billing_payer_id === payer.billing_payer_id);
      const balanceDue = payer.billing_balance_due ?? balance?.balance_due ?? 0;
      const lastPaymentDate = payer.billing_last_payment_at ?? payer.latest_payment_date ?? balance?.last_payment_at;
      const lastPaymentAmount = payer.billing_last_payment_amount ?? payer.latest_payment_amount ?? balance?.last_payment_amount;
      const lastPaymentCurrency = payer.billing_last_payment_currency ?? payer.latest_payment_currency ?? balance?.last_payment_currency ?? DEFAULT_CURRENCY;
      const payerLabel = readString(payer.display_name, `Płatnik #${payer.billing_payer_id}`);
      const studentCount = payerStudents.length;
      const isActive = payer.is_active !== false;

      return {
        id: String(payer.billing_payer_id),
        familyLabel: payerLabel,
        payerLabel,
        contactLabel: readString(payer.contact_phone || payer.email || payer.payment_identifier, "Brak kontaktu"),
        studentsLabel: studentNames.length ? studentNames.join(", ") : "Brak uczniów w tym koncie",
        studentSummaryLabel:
          studentCount === 0 ? "Brak przypisanych uczniów" : studentCount === 1 ? "1 uczeń" : `${studentCount} uczniów`,
        siblingLabel: studentCount > 1 ? `Rodzeństwo: ${studentCount} uczniów` : "Bez rodzeństwa w danych rozliczeń",
        statusLabel: isActive ? "Aktywne" : "Nieaktywne",
        statusTone: isActive ? (balanceDue > 0 ? "warning" : "ok") : "neutral",
        balanceLabel: formatMoney(balanceDue, DEFAULT_CURRENCY),
        lastPaymentLabel: lastPaymentDate
          ? `${formatDateLabel(lastPaymentDate)} · ${formatMoney(lastPaymentAmount, lastPaymentCurrency)}`
          : "Brak ostatniej wpłaty",
        contextLabel:
          studentCount > 1
            ? "Rodzinne konto rozliczeniowe z kilkorgiem uczniów."
            : studentCount === 1
              ? "Rodzinne konto rozliczeniowe z jednym uczniem."
              : "Płatnik bez przypisanego ucznia w obecnych danych.",
      };
    });
}

export function buildBillingCompanyClientRows(
  contractors: ContractorRecord[],
  balances: BillingBalanceRecord[],
  payers: BillingPayerRecord[],
  limit = 5,
): BillingCompanyClientRow[] {
  const payerNames = new Set(payers.map((payer) => normalizeText(payer.display_name)));

  return contractors
    .filter((contractor) => {
      const contractorName = normalizeText(contractor.name);
      return contractorName && !payerNames.has(contractorName) && !contractorName.startsWith("rodzina");
    })
    .slice()
    .sort((a, b) => (b.invoice_count ?? 0) - (a.invoice_count ?? 0))
    .slice(0, limit)
    .map((contractor) => {
      const balance = findBalanceForContractor(contractor, balances);
      return {
        id: String(contractor.contractor_id),
        href: `/crm/${contractor.contractor_id}`,
        companyLabel: getContractorLabel(contractor),
        contactLabel: readString(contractor.email || contractor.phone, "Brak kontaktu"),
        invoiceCountLabel: `${contractor.invoice_count ?? 0}`,
        balanceLabel: balance ? formatMoney(balance.balance_due, DEFAULT_CURRENCY) : "Brak salda rodzinnego",
        contextLabel:
          (contractor.invoice_count ?? 0) > 0
            ? "Klient firmowy z historią faktur, oddzielony od rodzin i uczniów."
            : "Klient firmowy w CRM, bez rodzinnego konta ucznia.",
        statusLabel: contractor.is_new ? "Nowy kontrahent" : "Kontrahent",
      };
    });
}

export function buildBillingBalanceExplanationRows(
  balances: BillingBalanceRecord[],
  payers: BillingPayerRecord[],
  students: BillingStudentRecord[],
  charges: BillingChargeRecord[],
  limit = 6,
): BillingBalanceExplanationRow[] {
  const studentsByPayer = new Map<number, BillingStudentRecord[]>();
  students.forEach((student) => {
    const current = studentsByPayer.get(student.billing_payer_id) ?? [];
    current.push(student);
    studentsByPayer.set(student.billing_payer_id, current);
  });
  const chargesByPayer = new Map<number, BillingChargeRecord[]>();
  charges.forEach((charge) => {
    const current = chargesByPayer.get(charge.billing_payer_id) ?? [];
    current.push(charge);
    chargesByPayer.set(charge.billing_payer_id, current);
  });
  const payersById = new Map(payers.map((payer) => [payer.billing_payer_id, payer]));

  const balanceRows: BillingBalanceExplanationRow[] = balances.map((balance) => {
    const payer = payersById.get(balance.billing_payer_id);
    const payerStudents = studentsByPayer.get(balance.billing_payer_id) ?? [];
    const payerCharges = (chargesByPayer.get(balance.billing_payer_id) ?? [])
      .slice()
      .sort((a, b) => String(b.due_date ?? "").localeCompare(String(a.due_date ?? "")))
      .slice(0, 3);
    const totalCharges = balance.total_charges ?? payer?.billing_total_charges ?? 0;
    const totalMatches = balance.total_matches ?? payer?.billing_total_matches ?? 0;
    const balanceDue = balance.balance_due ?? payer?.billing_balance_due ?? 0;
    const lastPaymentDate = balance.last_payment_at ?? payer?.billing_last_payment_at ?? payer?.latest_payment_date;
    const lastPaymentAmount = balance.last_payment_amount ?? payer?.billing_last_payment_amount ?? payer?.latest_payment_amount;
    const lastPaymentCurrency = balance.last_payment_currency ?? payer?.billing_last_payment_currency ?? payer?.latest_payment_currency ?? DEFAULT_CURRENCY;
    const studentCount = payerStudents.length;
    const payerLabel = getBalancePayerLabel(balance);
    const topItemsLabel = payerCharges.length
      ? payerCharges
          .map((charge) => {
            const studentLabel = readString(charge.student_full_name, "uczeń");
            const periodLabel = readString(charge.period_label, "okres bez nazwy");
            return `${formatMoney(charge.total_amount, DEFAULT_CURRENCY)} za ${studentLabel}, ${periodLabel}`;
          })
          .join("; ")
      : "Brakuje szczegółowych naliczeń dla tego salda.";

    return {
      id: `balance-explanation-${balance.billing_payer_id}`,
      payerLabel,
      familyTypeLabel:
        studentCount > 1
          ? `Rodzina z rodzeństwem: ${studentCount} uczniów`
          : studentCount === 1
            ? "Rodzina z jednym uczniem"
            : "Płatnik bez przypisanych uczniów",
      chargedLabel: formatMoney(totalCharges, DEFAULT_CURRENCY),
      paidLabel: formatMoney(totalMatches, DEFAULT_CURRENCY),
      balanceLabel: formatMoney(balanceDue, DEFAULT_CURRENCY),
      balanceMeaningLabel:
        balanceDue > 0 ? `Do dopłaty pozostaje ${formatMoney(balanceDue, DEFAULT_CURRENCY)}`
        : balanceDue < 0 ? `Nadpłata wynosi ${formatMoney(Math.abs(balanceDue), DEFAULT_CURRENCY)}`
        : "Saldo jest rozliczone",
      lastPaymentLabel: lastPaymentDate
        ? `${formatDateLabel(lastPaymentDate)} · ${formatMoney(lastPaymentAmount, lastPaymentCurrency)}`
        : "Brak ostatniej wpłaty",
      topItemsLabel,
      explanationLabel:
        payerCharges.length > 0
          ? `Saldo wynika z naliczonych kwot pomniejszonych o wpłaty widoczne w ledgerze. To wyjaśnienie read-only, bez księgowania i bez dopasowywania przelewów.`
          : `Brakuje danych, żeby szczegółowo wyjaśnić saldo. Widoczna jest tylko suma naliczeń, wpłat i różnica.`,
      statusTone: balanceDue > 0 ? "warning" : balanceDue < 0 ? "info" : "ok",
    };
  });

  const payerOnlyRows = payers
    .filter((payer) => !balances.some((balance) => balance.billing_payer_id === payer.billing_payer_id))
    .map((payer) => {
      const payerStudents = studentsByPayer.get(payer.billing_payer_id) ?? [];
      return {
        id: `balance-explanation-payer-${payer.billing_payer_id}`,
        payerLabel: readString(payer.display_name, `Płatnik #${payer.billing_payer_id}`),
        familyTypeLabel:
          payerStudents.length > 1
            ? `Rodzina z rodzeństwem: ${payerStudents.length} uczniów`
            : payerStudents.length === 1
              ? "Rodzina z jednym uczniem"
              : "Płatnik bez przypisanych uczniów",
        chargedLabel: formatMoney(payer.billing_total_charges, DEFAULT_CURRENCY),
        paidLabel: formatMoney(payer.billing_total_matches, DEFAULT_CURRENCY),
        balanceLabel: formatMoney(payer.billing_balance_due, DEFAULT_CURRENCY),
        balanceMeaningLabel: "Brakuje pełnego ledgeru dla szczegółowego wyjaśnienia.",
        lastPaymentLabel: payer.latest_payment_date
          ? `${formatDateLabel(payer.latest_payment_date)} · ${formatMoney(payer.latest_payment_amount, payer.latest_payment_currency ?? DEFAULT_CURRENCY)}`
          : "Brak ostatniej wpłaty",
        topItemsLabel: "Brakuje szczegółowych naliczeń dla tego płatnika.",
        explanationLabel: "Widoczny jest tylko skrót danych płatnika. Pełniejsze wyjaśnienie wymaga danych naliczeń albo ledgeru.",
        statusTone: "neutral" as const,
      };
    });

  return [...balanceRows, ...payerOnlyRows].slice(0, limit);
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
        (snapshot.balances.length ||
          snapshot.payers.length ||
          snapshot.students.length ||
          snapshot.charges.length ||
          snapshot.invoices.length ||
          snapshot.contractors.length ||
          snapshot.workItems.length),
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
    snapshot.payers.length === 0 &&
    snapshot.students.length === 0 &&
    snapshot.charges.length === 0 &&
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
