import type { DashboardAlert, DashboardReminder, DashboardSnapshot, InvoiceVerificationInbox } from "@/lib/types";

import { buildBossAssistantRows, type TaskFocusSnapshot } from "../assistant-ceo/bossAssistantModel";
import { buildBillingBalanceRows, buildBillingKpis, type BillingBalanceRecord } from "../billing/billingModel";
import { buildContractorRows, buildCrmKpis, type ContractorRecord } from "../crm/crmModel";
import { buildKnowledgeDocumentRows, buildDocumentsKpis, type KnowledgeDocumentRecord } from "../documents/documentsModel";
import { buildWorkItemRows, type WorkItemRecord } from "../work-items/workItemsModel";

export type DailyBriefSourceKey =
  | "dashboard"
  | "taskFocus"
  | "workItems"
  | "invoiceInbox"
  | "billingBalances"
  | "contractors"
  | "documents";

export type DailyBriefSourceState = {
  key: DailyBriefSourceKey;
  label: string;
  status: "ready" | "empty" | "error";
  message?: string;
};

export type DailyBriefSnapshot = {
  dashboard: DashboardSnapshot | null;
  taskFocus: TaskFocusSnapshot | null;
  workItems: WorkItemRecord[];
  invoiceInbox: InvoiceVerificationInbox | null;
  billingBalances: BillingBalanceRecord[];
  contractors: ContractorRecord[];
  documents: KnowledgeDocumentRecord[];
  sourceStates: DailyBriefSourceState[];
};

export type DailyBriefTone = "danger" | "warning" | "info" | "ok" | "neutral";
export type DailyBriefCategory = "tasks" | "invoices" | "finance" | "crm" | "documents" | "other";

export type DailyBriefItem = {
  id: string;
  title: string;
  description: string;
  meta: string;
  href: string;
  source: string;
  category: DailyBriefCategory;
  tone: DailyBriefTone;
  priority: number;
};

export type DailyBriefKpis = {
  criticalCount: number;
  urgentCount: number;
  invoiceCount: number;
  documentCount: number;
  contractorCount: number;
  laterCount: number;
};

export type DailyBriefSections = {
  top: DailyBriefItem[];
  urgent: DailyBriefItem[];
  invoicesFinance: DailyBriefItem[];
  contractors: DailyBriefItem[];
  documents: DailyBriefItem[];
  later: DailyBriefItem[];
};

export const DAILY_BRIEF_READ_ONLY = true;
export const DAILY_BRIEF_WRITE_ACTIONS: ReadonlyArray<never> = [];
export const DAILY_BRIEF_ORGANIZATION_REQUIRED_TITLE = "Wybierz organizację, aby zobaczyć Pulpit dnia";
export const DAILY_BRIEF_ORGANIZATION_REQUIRED_DESCRIPTION =
  "Ten widok jest składany z danych bieżącej organizacji. Wybierz organizację w górnym pasku, żeby uniknąć globalnego albo mylącego stanu.";
export const DAILY_BRIEF_SECTION_LABELS = {
  top: "Najważniejsze dziś",
  urgent: "Sprawy pilne",
  invoicesFinance: "Faktury i finanse",
  contractors: "Kontrahenci",
  documents: "Dokumenty",
  later: "Można odłożyć",
} as const;
export const DAILY_BRIEF_REFRESH_LABEL = "Odśwież";

const SOURCE_LABELS: Record<DailyBriefSourceKey, string> = {
  dashboard: "Pulpit",
  taskFocus: "Asystent Szefa",
  workItems: "Sprawy",
  invoiceInbox: "Faktury",
  billingBalances: "Rozliczenia",
  contractors: "CRM",
  documents: "Dokumenty",
};

const TECHNICAL_PATTERNS = [/C:\\Users\\/i, /data\/magazyn/i, /storage_key/i, /connection string/i, /token/i, /secret/i, /payload/i, /raw json/i, /debug/i, /fixture/i, /DATABASE_URL/i, /INVOICE_DATABASE_URL/i];
const TOP_CATEGORY_LIMITS: Record<DailyBriefCategory, number> = {
  tasks: 2,
  invoices: 2,
  finance: 1,
  crm: 1,
  documents: 1,
  other: 1,
};
const TOP_CATEGORY_ORDER: DailyBriefCategory[] = ["tasks", "invoices", "crm", "documents", "finance", "other"];

export function canUseDailyBriefOrganizationScope(organizationId: string | number | null | undefined): boolean {
  return organizationId !== null && organizationId !== undefined && String(organizationId).trim().length > 0;
}

export function buildDailyBrief(snapshot: DailyBriefSnapshot): { sections: DailyBriefSections; kpis: DailyBriefKpis } {
  const topCandidates = rankItems([
    ...buildDashboardAlertItems(snapshot.dashboard),
    ...buildTaskFocusItems(snapshot.taskFocus),
    ...buildWorkItemItems(snapshot.workItems),
    ...buildInvoiceItems(snapshot.invoiceInbox),
    ...buildBillingItems(snapshot.billingBalances),
    ...buildDocumentItems(snapshot.documents),
    ...buildContractorItems(snapshot.contractors),
  ]);
  const top = buildBalancedTopItems(topCandidates, 7);

  const urgent = rankItems([...buildTaskFocusItems(snapshot.taskFocus), ...buildWorkItemItems(snapshot.workItems)]).slice(0, 8);
  const invoicesFinance = rankItems([...buildInvoiceItems(snapshot.invoiceInbox), ...buildBillingItems(snapshot.billingBalances)]).slice(0, 8);
  const contractors = rankItems(buildContractorItems(snapshot.contractors)).slice(0, 6);
  const documents = rankItems([...buildDocumentItems(snapshot.documents), ...buildDashboardKnowledgeItems(snapshot.dashboard)]).slice(0, 6);
  const later = rankItems(buildLaterItems(snapshot)).slice(0, 8);

  return {
    sections: { top, urgent, invoicesFinance, contractors, documents, later },
    kpis: {
      criticalCount: top.filter((item) => item.tone === "danger").length,
      urgentCount: urgent.length,
      invoiceCount: invoicesFinance.length,
      documentCount: documents.length,
      contractorCount: contractors.length,
      laterCount: later.length,
    },
  };
}

export function isDailyBriefEmpty(status: "idle" | "loading" | "ready" | "error", snapshot: DailyBriefSnapshot | null): boolean {
  if (status !== "ready" || !snapshot) {
    return false;
  }
  const { sections } = buildDailyBrief(snapshot);
  return Object.values(sections).every((items) => items.length === 0);
}

export function hasDailyBriefWriteActions(): boolean {
  return DAILY_BRIEF_WRITE_ACTIONS.length > 0;
}

export function sourceState(key: DailyBriefSourceKey, status: DailyBriefSourceState["status"], message?: string): DailyBriefSourceState {
  return { key, label: SOURCE_LABELS[key], status, message };
}

export function hasUnsafeTechnicalText(items: DailyBriefItem[]): boolean {
  return items.some((item) =>
    TECHNICAL_PATTERNS.some((pattern) =>
      [item.title, item.description, item.meta, item.source].some((value) => pattern.test(value)),
    ),
  );
}

function buildDashboardAlertItems(snapshot: DashboardSnapshot | null): DailyBriefItem[] {
  return (snapshot?.operational_alerts ?? []).map((alert, index) => ({
    id: `dashboard-alert-${index}`,
    title: sanitize(alert.title, "Sygnał operacyjny"),
    description: sanitize(alert.description, "Wymaga uwagi w bieżącym pulpicie."),
    meta: dashboardAlertCategoryLabel(alert),
    href: dashboardAlertHref(alert),
    source: "Pulpit",
    category: dashboardAlertCategory(alert),
    tone: alertTone(alert),
    priority: alertPriority(alert),
  }));
}

function buildDashboardKnowledgeItems(snapshot: DashboardSnapshot | null): DailyBriefItem[] {
  return (snapshot?.knowledge_queue ?? []).map((item, index) => ({
    id: `dashboard-document-${item.knowledge_document_id ?? index}`,
    title: sanitize(item.title, "Dokument w kolejce"),
    description: sanitize(item.business_status_label || item.workflow_status_label, "Dokument wymaga sprawdzenia w bazie wiedzy."),
    meta: sanitize(item.library_path_label || item.updated_at, "Dokumenty"),
    href: item.knowledge_document_id ? `/dokumenty/${item.knowledge_document_id}` : "/dokumenty",
    source: "Dokumenty",
    category: "documents",
    tone: "warning",
    priority: 58,
  }));
}

function buildTaskFocusItems(snapshot: TaskFocusSnapshot | null): DailyBriefItem[] {
  if (!snapshot) {
    return [];
  }
  return buildBossAssistantRows(snapshot, 12).map((row) => ({
    id: `task-focus-${row.id}`,
    title: sanitize(row.title, "Zadanie wymagające uwagi"),
    description: sanitize(row.contextLabel, "Sprawa z Asystenta Szefa."),
    meta: sanitize(`${row.focusLabel} · ${row.dueLabel}`, row.focusLabel),
    href: "/asystent-szefa",
    source: "Asystent Szefa",
    category: "tasks",
    tone: row.priorityTone === "danger" || row.statusTone === "danger" ? "danger" : row.priorityTone === "warning" ? "warning" : "info",
    priority: row.priorityTone === "danger" ? 95 : row.statusTone === "danger" ? 88 : row.priorityTone === "warning" ? 72 : 48,
  }));
}

function buildWorkItemItems(items: WorkItemRecord[]): DailyBriefItem[] {
  return buildWorkItemRows(items)
    .filter((row) => row.priorityTone === "danger" || row.priorityTone === "warning" || row.statusTone === "danger")
    .map((row) => ({
      id: `work-item-${row.workItemId}`,
      title: sanitize(row.title, `Sprawa #${row.workItemId}`),
      description: sanitize(`${row.description} · dlatego warto spojrzeć na nią dziś.`, "Sprawa operacyjna wymaga uwagi dziś."),
      meta: sanitize(`${row.priorityLabel} · ${row.slaLabel} · ${row.dueLabel}`, row.priorityLabel),
      href: `/work-items/${row.workItemId}`,
      source: "Sprawy",
      category: "tasks",
      tone: row.priorityTone === "danger" || row.statusTone === "danger" ? "danger" : row.priorityTone === "warning" ? "warning" : "info",
      priority: row.priorityTone === "danger" ? 92 : row.statusTone === "danger" ? 86 : row.priorityTone === "warning" ? 70 : 44,
    }));
}

function buildInvoiceItems(inbox: InvoiceVerificationInbox | null): DailyBriefItem[] {
  if (!inbox) {
    return [];
  }
  const items: DailyBriefItem[] = [];
  Object.entries(inbox.sections).forEach(([sectionKey, section]) => {
    if (section.count > 0) {
      items.push({
        id: `invoice-section-${sectionKey}`,
        title: sanitize(section.title, "Faktury wymagają uwagi"),
        description: sanitize(section.description, `${section.count} pozycji w inboxie faktur.`),
        meta: `${section.count} pozycji`,
        href: "/faktury",
        source: "Faktury",
        category: "invoices",
        tone: sectionKey.includes("overdue") || sectionKey.includes("duplicate") ? "danger" : "warning",
        priority: sectionKey.includes("overdue") ? 90 : sectionKey.includes("duplicate") ? 80 : 66,
      });
    }

    section.items.slice(0, 3).forEach((invoice) => {
      items.push({
        id: `invoice-${invoice.invoice_id}`,
        title: sanitize(invoice.invoice_number || invoice.issuer_name, `Faktura #${invoice.invoice_id}`),
        description: sanitize(invoice.flag_reason || invoice.issuer_name, "Faktura w kolejce weryfikacji."),
        meta: sanitize(`${invoice.gross_amount ?? "-"} ${invoice.currency ?? ""} · ${invoice.status ?? "status nieznany"}`, "Faktura"),
        href: `/faktury/${invoice.invoice_id}`,
        source: "Faktury",
        category: "invoices",
        tone: invoice.duplicate_type || invoice.pending_override_count ? "warning" : "info",
        priority: invoice.pending_override_count ? 74 : invoice.duplicate_type ? 68 : 52,
      });
    });
  });
  return items;
}

function buildBillingItems(items: BillingBalanceRecord[]): DailyBriefItem[] {
  return buildBillingBalanceRows(items)
    .filter((row) => row.statusTone === "warning" || row.statusTone === "danger")
    .map((row) => ({
      id: `billing-${row.id}`,
      title: sanitize(row.payerLabel, "Płatnik wymaga uwagi"),
      description: sanitize(`Saldo: ${row.balanceDueLabel}. Kontakt: ${row.contactLabel}`, "Rozliczenie wymaga uwagi."),
      meta: sanitize(row.lastPaymentLabel, "Rozliczenia"),
      href: "/rozliczenia",
      source: "Rozliczenia",
      category: "finance",
      tone: row.statusTone === "danger" ? "danger" : "warning",
      priority: row.statusTone === "danger" ? 82 : 64,
    }));
}

function buildContractorItems(items: ContractorRecord[]): DailyBriefItem[] {
  const kpis = buildCrmKpis(items);
  const contractorRows = buildContractorRows(items);
  const rows = contractorRows.filter((row) => row.statusTone === "info" || row.contactLabel === "Brak kontaktu").slice(0, 8);
  const result = rows.map((row) => ({
    id: `contractor-${row.id}`,
    title: sanitize(row.nameLabel, "Kontrahent wymaga uwagi"),
    description: row.contactLabel === "Brak kontaktu" ? "Brakuje danych kontaktowych." : sanitize(row.statusLabel, "Nowy kontrahent."),
    meta: sanitize(`${row.invoiceCountLabel} faktur · ${row.lastInvoiceLabel}`, "CRM"),
    href: `/crm/${row.id}`,
    source: "CRM",
    category: "crm",
    tone: row.contactLabel === "Brak kontaktu" ? "warning" : "info",
    priority: row.contactLabel === "Brak kontaktu" ? 50 : 38,
  } satisfies DailyBriefItem));

  if (kpis.newCount > 0) {
    result.unshift({
      id: "crm-new-contractors",
      title: "Nowi kontrahenci do przejrzenia",
      description: `${kpis.newCount} nowych pozycji w katalogu CRM.`,
      meta: `${kpis.missingContactCount} bez kontaktu`,
      href: "/crm",
      source: "CRM",
      category: "crm",
      tone: "info",
      priority: 54,
    });
  }

  return result;
}

function buildDocumentItems(items: KnowledgeDocumentRecord[]): DailyBriefItem[] {
  const kpis = buildDocumentsKpis(items);
  const rows = buildKnowledgeDocumentRows(items)
    .filter((row) => row.statusTone !== "ok" || row.workflowTone === "warning" || row.workflowTone === "danger")
    .slice(0, 8);
  const result = rows.map((row) => ({
    id: `document-${row.id}`,
    title: sanitize(row.title, "Dokument wymaga uwagi"),
    description: sanitize(`${row.statusLabel} · ${row.workflowLabel}`, "Dokument wymaga sprawdzenia."),
    meta: sanitize(`${row.folderLabel} · ${row.versionLabel}`, "Dokumenty"),
    href: `/dokumenty/${row.id}`,
    source: "Dokumenty",
    category: "documents",
    tone: row.statusTone === "danger" || row.workflowTone === "danger" ? "danger" : row.statusTone === "warning" || row.workflowTone === "warning" ? "warning" : "info",
    priority: row.statusTone === "danger" ? 78 : row.workflowTone === "warning" ? 60 : 42,
  } satisfies DailyBriefItem));

  if (kpis.processingOrErrors > 0) {
    result.unshift({
      id: "documents-processing-or-errors",
      title: "Dokumenty w przetwarzaniu lub z błędem",
      description: `${kpis.processingOrErrors} dokumentów wymaga kontroli statusu przetwarzania.`,
      meta: `${kpis.needsDecision} do decyzji`,
      href: "/dokumenty",
      source: "Dokumenty",
      category: "documents",
      tone: "warning",
      priority: 62,
    });
  }

  return result;
}

function buildLaterItems(snapshot: DailyBriefSnapshot): DailyBriefItem[] {
  const reminders = (snapshot.dashboard?.active_reminders ?? []).map((reminder, index) => reminderItem(reminder, index));
  const billingKpis = buildBillingKpis(snapshot.billingBalances);
  const calmItems: DailyBriefItem[] = [
    ...buildLowPriorityWorkItemItems(snapshot.workItems),
    ...buildLowPriorityContractorItems(snapshot.contractors),
    ...buildLowPriorityDocumentItems(snapshot.documents),
  ];

  if (billingKpis.paidOrSettledCount > 0) {
    calmItems.push({
      id: "billing-settled",
      title: "Rozliczenia stabilne",
      description: `${billingKpis.paidOrSettledCount} płatników bez salda do pilnej reakcji.`,
      meta: "Można odłożyć",
      href: "/rozliczenia",
      source: "Rozliczenia",
      category: "finance",
      tone: "ok",
      priority: 12,
    });
  }

  const documentKpis = buildDocumentsKpis(snapshot.documents);
  if (documentKpis.ready > 0) {
    calmItems.push({
      id: "documents-ready",
      title: "Dokumenty gotowe w bazie wiedzy",
      description: `${documentKpis.ready} dokumentów wygląda stabilnie i nie wymaga pilnej reakcji.`,
      meta: "Można odłożyć",
      href: "/dokumenty",
      source: "Dokumenty",
      category: "documents",
      tone: "ok",
      priority: 10,
    });
  }

  return [...reminders, ...calmItems];
}

function reminderItem(reminder: DashboardReminder, index: number): DailyBriefItem {
  const title = sanitize(reminder.title, `Przypomnienie #${index + 1}`);
  return {
    id: `reminder-${reminder.task_id ?? index}`,
    title,
    description: sanitize(reminder.task_type, "Przypomnienie z pulpitu organizacji."),
    meta: sanitize(reminder.due_at || reminder.remind_at || reminder.priority, "Bez terminu"),
    href: "/pulpit",
    source: "Pulpit",
    category: "other",
    tone: reminder.priority === "wysoki" || reminder.priority === "krytyczny" ? "warning" : "neutral",
    priority: reminder.priority === "krytyczny" ? 64 : reminder.priority === "wysoki" ? 48 : 20,
  };
}

function buildLowPriorityWorkItemItems(items: WorkItemRecord[]): DailyBriefItem[] {
  return buildWorkItemRows(items)
    .filter((row) => row.priorityTone !== "danger" && row.priorityTone !== "warning" && row.statusTone !== "danger")
    .slice(0, 3)
    .map((row) => ({
      id: `later-work-item-${row.workItemId}`,
      title: sanitize(row.title, `Sprawa #${row.workItemId}`),
      description: "Nie wygląda na ryzyko na dziś, ale warto mieć ją w tle.",
      meta: sanitize(`${row.priorityLabel} · ${row.slaLabel}`, "Niska pilność"),
      href: `/work-items/${row.workItemId}`,
      source: "Sprawy",
      category: "tasks",
      tone: "neutral",
      priority: 18,
    }));
}

function buildLowPriorityContractorItems(items: ContractorRecord[]): DailyBriefItem[] {
  return buildContractorRows(items)
    .filter((row) => row.statusTone === "ok" && row.contactLabel !== "Brak kontaktu")
    .slice(0, 3)
    .map((row) => ({
      id: `later-contractor-${row.id}`,
      title: sanitize(row.nameLabel, "Kontrahent do spokojnego przejrzenia"),
      description: "Relacja wygląda stabilnie, bez pilnego sygnału na dziś.",
      meta: sanitize(row.lastInvoiceLabel, "CRM"),
      href: `/crm/${row.id}`,
      source: "CRM",
      category: "crm",
      tone: "neutral",
      priority: 14,
    }));
}

function buildLowPriorityDocumentItems(items: KnowledgeDocumentRecord[]): DailyBriefItem[] {
  return buildKnowledgeDocumentRows(items)
    .filter((row) => row.statusTone !== "danger" && row.workflowTone !== "danger")
    .slice(0, 3)
    .map((row) => ({
      id: `later-document-${row.id}`,
      title: sanitize(row.title, "Dokument do spokojnego przejrzenia"),
      description: "Nie blokuje dzisiejszych decyzji, ale jest widoczny w bazie wiedzy.",
      meta: sanitize(`${row.folderLabel} · ${row.updatedLabel}`, "Dokumenty"),
      href: `/dokumenty/${row.id}`,
      source: "Dokumenty",
      category: "documents",
      tone: "neutral",
      priority: 12,
    }));
}

function dashboardAlertHref(alert: DashboardAlert): string {
  if (alert.category === "invoices") {
    return "/faktury";
  }
  if (alert.category === "tasks") {
    return "/work-items";
  }
  if (alert.category === "knowledge") {
    return "/dokumenty";
  }
  return "/pulpit";
}

function dashboardAlertCategory(alert: DashboardAlert): DailyBriefCategory {
  if (alert.category === "invoices") {
    return "invoices";
  }
  if (alert.category === "tasks") {
    return "tasks";
  }
  if (alert.category === "knowledge") {
    return "documents";
  }
  return "other";
}

function dashboardAlertCategoryLabel(alert: DashboardAlert): string {
  if (alert.category === "invoices") {
    return "Faktury";
  }
  if (alert.category === "tasks") {
    return "Sprawy";
  }
  if (alert.category === "knowledge") {
    return "Dokumenty";
  }
  if (alert.category === "integrations") {
    return "Integracje";
  }
  return "Pulpit";
}

function alertTone(alert: DashboardAlert): DailyBriefTone {
  if (alert.severity === "danger") {
    return "danger";
  }
  if (alert.severity === "warning") {
    return "warning";
  }
  if (alert.severity === "success") {
    return "ok";
  }
  return "info";
}

function alertPriority(alert: DashboardAlert): number {
  if (alert.severity === "danger") {
    return 96;
  }
  if (alert.severity === "warning") {
    return 74;
  }
  return 42;
}

function rankItems(items: DailyBriefItem[]): DailyBriefItem[] {
  const seen = new Set<string>();
  return items
    .filter((item) => {
      const key = `${item.source}:${item.href}:${item.title}`;
      if (seen.has(key)) {
        return false;
      }
      seen.add(key);
      return true;
    })
    .sort((first, second) => second.priority - first.priority || first.title.localeCompare(second.title, "pl"));
}

function buildBalancedTopItems(items: DailyBriefItem[], maxItems: number): DailyBriefItem[] {
  const ranked = rankItems(items);
  const selected: DailyBriefItem[] = [];
  const counts = new Map<DailyBriefCategory, number>();

  for (const category of TOP_CATEGORY_ORDER) {
    const nextItem = ranked.find((item) => item.category === category && !selected.includes(item));
    if (nextItem && selected.length < maxItems && canAddTopItem(nextItem, counts)) {
      selected.push(nextItem);
      counts.set(nextItem.category, (counts.get(nextItem.category) ?? 0) + 1);
    }
  }

  for (const item of ranked) {
    if (selected.length >= maxItems) {
      break;
    }
    if (selected.includes(item) || !canAddTopItem(item, counts)) {
      continue;
    }
    selected.push(item);
    counts.set(item.category, (counts.get(item.category) ?? 0) + 1);
  }

  return selected.sort((first, second) => second.priority - first.priority || first.title.localeCompare(second.title, "pl"));
}

function canAddTopItem(item: DailyBriefItem, counts: Map<DailyBriefCategory, number>): boolean {
  return (counts.get(item.category) ?? 0) < TOP_CATEGORY_LIMITS[item.category];
}

function sanitize(value: unknown, fallback: string): string {
  const text = typeof value === "string" && value.trim() ? value.trim() : fallback;
  if (TECHNICAL_PATTERNS.some((pattern) => pattern.test(text))) {
    return fallback;
  }
  return text.replace(/\s+/g, " ");
}
