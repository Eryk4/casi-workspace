"use client";

import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";

import { findNavigationItem } from "@/config/navigation";
import { ActiveOrganizationProvider, useActiveOrganization } from "@/context/ActiveOrganizationContext";
import { AUTH_REQUIRED_EVENT } from "@/lib/api";

import { shouldClearSessionAttentionForPath } from "./appShellModel";
import { MainContent } from "./MainContent";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";

type AppShellProps = {
  children: ReactNode;
};

export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [sessionAttention, setSessionAttention] = useState(false);
  const currentModule = findNavigationItem(pathname);
  const isAuthPage = pathname === "/login";

  useEffect(() => {
    const handleAuthRequired = () => setSessionAttention(true);

    window.addEventListener(AUTH_REQUIRED_EVENT, handleAuthRequired);
    return () => window.removeEventListener(AUTH_REQUIRED_EVENT, handleAuthRequired);
  }, []);

  useEffect(() => {
    if (sessionAttention && shouldClearSessionAttentionForPath(pathname)) {
      setSessionAttention(false);
    }
  }, [pathname, sessionAttention]);

  if (isAuthPage) {
    return <>{children}</>;
  }

  return (
    <ActiveOrganizationProvider>
      <AppShellFrame
        currentModule={currentModule}
        pathname={pathname}
        sessionAttention={sessionAttention}
        sidebarCollapsed={sidebarCollapsed}
        onToggleSidebar={() => setSidebarCollapsed((value) => !value)}
      >
        {children}
      </AppShellFrame>
    </ActiveOrganizationProvider>
  );
}

type AppShellFrameProps = {
  children: ReactNode;
  currentModule: ReturnType<typeof findNavigationItem>;
  onToggleSidebar: () => void;
  pathname: string;
  sessionAttention: boolean;
  sidebarCollapsed: boolean;
};

function AppShellFrame({
  children,
  currentModule,
  onToggleSidebar,
  pathname,
  sessionAttention,
  sidebarCollapsed,
}: AppShellFrameProps) {
  const organizationContext = useActiveOrganization();

  return (
    <div className="app-shell" data-sidebar-collapsed={sidebarCollapsed}>
      <Sidebar activePath={pathname} collapsed={sidebarCollapsed} onToggleCollapsed={onToggleSidebar} />
      <div className="app-shell__workspace">
        <Topbar currentModule={currentModule} pathname={pathname} sessionAttention={sessionAttention} />
        <OrganizationContextBanner
          error={organizationContext.error}
          organizationCount={organizationContext.organizations.length}
          selectedOrganizationId={organizationContext.selectedOrganizationId}
          status={organizationContext.status}
        />
        <MainContent>{children}</MainContent>
      </div>
    </div>
  );
}

type OrganizationContextBannerProps = {
  error: ReturnType<typeof useActiveOrganization>["error"];
  organizationCount: number;
  selectedOrganizationId: string | null;
  status: ReturnType<typeof useActiveOrganization>["status"];
};

function OrganizationContextBanner({
  error,
  organizationCount,
  selectedOrganizationId,
  status,
}: OrganizationContextBannerProps) {
  if (status === "loading") {
    return (
      <div className="app-context-banner" role="status">
        <strong>Ładowanie kontekstu organizacji</strong>
        <span>Frontend pobiera aktualną sesję i listę organizacji.</span>
      </div>
    );
  }

  if (status === "unauthenticated") {
    return (
      <div className="app-context-banner app-context-banner--warning" role="status">
        <strong>{error?.title ?? "Sesja wygasła"}</strong>
        <span>{error?.description ?? "Zaloguj się ponownie, aby kontynuować pracę."}</span>
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className="app-context-banner app-context-banner--danger" role="alert">
        <strong>{error?.title ?? "Nie udało się pobrać organizacji"}</strong>
        <span>{error?.description ?? "Odśwież widok albo zaloguj się ponownie."}</span>
      </div>
    );
  }

  if (status === "ready" && organizationCount === 0) {
    return (
      <div className="app-context-banner app-context-banner--warning" role="status">
        <strong>Brak dostępnych organizacji</strong>
        <span>Twoje konto nie ma aktywnej organizacji do wyświetlenia danych operacyjnych.</span>
      </div>
    );
  }

  if (status === "ready" && organizationCount > 1 && !selectedOrganizationId) {
    return (
      <div className="app-context-banner" role="status">
        <strong>Wybierz organizację</strong>
        <span>Moduły operacyjne pobiorą dane dopiero po wskazaniu organizacji w górnym pasku.</span>
      </div>
    );
  }

  return null;
}
