import type { NavigationItem } from "@/config/navigation";

export function shouldClearSessionAttentionForPath(pathname: string): boolean {
  return pathname === "/login";
}

export function shouldShowTopbarPrimaryAction(currentModule: NavigationItem, pathname: string): boolean {
  if (currentModule.id === "work-items" && pathname.startsWith("/work-items/")) {
    return false;
  }
  if (currentModule.id === "crm" && pathname.startsWith("/crm/")) {
    return false;
  }
  if (currentModule.id === "invoices" && pathname.startsWith("/faktury/")) {
    return false;
  }
  return true;
}
