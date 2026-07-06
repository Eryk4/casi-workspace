import type { LucideIcon } from "lucide-react";
import {
  BarChart3,
  Bot,
  Building2,
  ClipboardList,
  CreditCard,
  FileArchive,
  FileText,
  LayoutDashboard,
  ReceiptText,
  Settings,
  SunMedium,
} from "lucide-react";

export type NavigationGroup = "core" | "operations" | "management";
export type NavigationReadiness = "live" | "foundation" | "planned";

export type NavigationItem = {
  id:
    | "dashboard"
    | "daily-brief"
    | "assistant-ceo"
    | "assistant-company"
    | "documents"
    | "invoices"
    | "billing"
    | "crm"
    | "work-items"
    | "reports"
    | "settings";
  label: string;
  path: string;
  icon: LucideIcon;
  group: NavigationGroup;
  component: string;
  description: string;
  actionLabel: string;
  readiness: NavigationReadiness;
  readinessLabel: string;
  primaryEndpoint?: string;
  requiredCapabilities?: string[];
  featureFlag?: string;
  children?: NavigationItem[];
};

export const navigationItems: NavigationItem[] = [
  {
    id: "dashboard",
    label: "Pulpit",
    path: "/pulpit",
    icon: LayoutDashboard,
    group: "core",
    component: "DashboardPage",
    description: "Centralny widok operacyjny i najwazniejsze sygnaly.",
    actionLabel: "Odswiez pulpit",
    readiness: "live",
    readinessLabel: "Dane live",
    primaryEndpoint: "/api/dashboard",
  },
  {
    id: "daily-brief",
    label: "Pulpit dnia",
    path: "/pulpit-dnia",
    icon: SunMedium,
    group: "core",
    component: "DailyBriefPage",
    description: "Poranny przeglÄ…d najwaĹĽniejszych spraw firmy.",
    actionLabel: "OdĹ›wieĹĽ pulpit dnia",
    readiness: "live",
    readinessLabel: "Produkt v1",
  },
  {
    id: "assistant-ceo",
    label: "Asystent Szefa",
    path: "/asystent-szefa",
    icon: Bot,
    group: "core",
    component: "AssistantCeoPage",
    description: "Zadania, terminy, priorytety i organizacja pracy.",
    actionLabel: "Dodaj zadanie",
    readiness: "foundation",
    readinessLabel: "Fundament modulu",
    primaryEndpoint: "/api/tasks/focus",
  },
  {
    id: "assistant-company",
    label: "Asystent Firmowy",
    path: "/asystent-firmowy",
    icon: Building2,
    group: "core",
    component: "AssistantCompanyPage",
    description: "Wiedza organizacji, dokumenty i odpowiedzi kontekstowe.",
    actionLabel: "Dodaj dokument",
    readiness: "foundation",
    readinessLabel: "Fundament modulu",
    primaryEndpoint: "/api/knowledge/documents",
  },
  {
    id: "documents",
    label: "Dokumenty",
    path: "/dokumenty",
    icon: FileArchive,
    group: "operations",
    component: "DocumentsPage",
    description: "Biblioteka dokumentow, importy i statusy przetwarzania.",
    actionLabel: "Dodaj dokument",
    readiness: "foundation",
    readinessLabel: "Fundament modulu",
    primaryEndpoint: "/api/knowledge/documents",
  },
  {
    id: "invoices",
    label: "Faktury",
    path: "/faktury",
    icon: ReceiptText,
    group: "operations",
    component: "InvoicesPage",
    description: "Inbox faktur, weryfikacja, duplikaty i przekazania.",
    actionLabel: "Dodaj fakture",
    readiness: "foundation",
    readinessLabel: "Fundament modulu",
    primaryEndpoint: "/api/invoices",
  },
  {
    id: "billing",
    label: "Rozliczenia",
    path: "/rozliczenia",
    icon: CreditCard,
    group: "operations",
    component: "BillingPage",
    description: "Pieniądze, płatności, zaległości i kontrahenci w jednym widoku.",
    actionLabel: "Tylko odczyt",
    readiness: "foundation",
    readinessLabel: "Produkt v1",
    primaryEndpoint: "/api/billing/ledger/balances",
    requiredCapabilities: ["billing.read"],
  },
  {
    id: "crm",
    label: "CRM",
    path: "/crm",
    icon: FileText,
    group: "management",
    component: "CrmPage",
    description: "Kontrahenci, relacje i historia wspolpracy.",
    actionLabel: "Dodaj kontakt",
    readiness: "foundation",
    readinessLabel: "Fundament modulu",
    primaryEndpoint: "/api/contractors",
  },
  {
    id: "work-items",
    label: "Work Items",
    path: "/work-items",
    icon: ClipboardList,
    group: "management",
    component: "WorkItemsPage",
    description: "Triage spraw, priorytety, SLA i obciazenie zespolu.",
    actionLabel: "Dodaj sprawe",
    readiness: "foundation",
    readinessLabel: "Fundament modulu",
    primaryEndpoint: "/api/work-items",
    requiredCapabilities: ["work_items.read"],
  },
  {
    id: "reports",
    label: "Raporty",
    path: "/raporty",
    icon: BarChart3,
    group: "management",
    component: "ReportsPage",
    description: "Raporty, widoki zarzadcze i metryki pracy.",
    actionLabel: "Nowy raport",
    readiness: "foundation",
    readinessLabel: "Fundament modulu",
    primaryEndpoint: "/api/dashboard/views",
  },
  {
    id: "settings",
    label: "Ustawienia",
    path: "/ustawienia",
    icon: Settings,
    group: "management",
    component: "SettingsPage",
    description: "Organizacje, uzytkownicy, integracje i konfiguracja.",
    actionLabel: "Dodaj uzytkownika",
    readiness: "foundation",
    readinessLabel: "Fundament modulu",
    primaryEndpoint: "/api/organizations",
  },
];

export const defaultNavigationItem = navigationItems[0];

export const navigationGroups: Array<{ id: NavigationGroup; label: string }> = [
  { id: "core", label: "Glowny obszar" },
  { id: "operations", label: "Operacje" },
  { id: "management", label: "Zarzadzanie" },
];

export function findNavigationItem(pathname: string): NavigationItem {
  return [...navigationItems]
    .sort((first, second) => second.path.length - first.path.length)
    .find((item) => isNavigationItemActive(pathname, item)) ?? defaultNavigationItem;
}

export function isNavigationItemActive(pathname: string, item: NavigationItem): boolean {
  const normalizedPath = normalizePath(pathname);
  return normalizedPath === item.path || normalizedPath.startsWith(`${item.path}/`);
}

export function normalizePath(pathname: string): string {
  if (!pathname) {
    return "/";
  }

  const path = pathname.startsWith("/") ? pathname : `/${pathname}`;
  return path.length > 1 && path.endsWith("/") ? path.slice(0, -1) : path;
}
