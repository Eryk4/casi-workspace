"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { api } from "@/lib/api";
import type { OrganizationId } from "@/lib/types";
import {
  ACTIVE_ORGANIZATION_STORAGE_KEY,
  resolveOrganizationContext,
  type ActiveOrganizationStatus,
  type OrganizationContextError,
  type OrganizationOption,
} from "./organizationContextModel";

type ActiveOrganizationContextValue = {
  status: ActiveOrganizationStatus;
  organizations: OrganizationOption[];
  selectedOrganizationId: OrganizationId | null;
  selectedOrganization: OrganizationOption | null;
  error: OrganizationContextError | null;
  selectOrganization: (organizationId: OrganizationId | null) => void;
};

const ActiveOrganizationContext = createContext<ActiveOrganizationContextValue | null>(null);

type ActiveOrganizationProviderProps = {
  children: ReactNode;
};

function readStoredOrganizationId(): OrganizationId | null {
  if (typeof window === "undefined") {
    return null;
  }
  const stored = window.localStorage.getItem(ACTIVE_ORGANIZATION_STORAGE_KEY);
  return stored && stored.trim() ? stored : null;
}

function storeOrganizationId(organizationId: OrganizationId | null): void {
  if (typeof window === "undefined") {
    return;
  }
  if (organizationId) {
    window.localStorage.setItem(ACTIVE_ORGANIZATION_STORAGE_KEY, organizationId);
    return;
  }
  window.localStorage.removeItem(ACTIVE_ORGANIZATION_STORAGE_KEY);
}

export function ActiveOrganizationProvider({ children }: ActiveOrganizationProviderProps) {
  const [status, setStatus] = useState<ActiveOrganizationStatus>("loading");
  const [organizations, setOrganizations] = useState<OrganizationOption[]>([]);
  const [selectedOrganizationId, setSelectedOrganizationId] = useState<OrganizationId | null>(null);
  const [error, setError] = useState<OrganizationContextError | null>(null);

  useEffect(() => {
    let mounted = true;

    async function loadOrganizationContext() {
      setStatus("loading");
      setError(null);

      const [sessionResult, organizationsResult] = await Promise.allSettled([api.currentSession(), api.organizations()]);

      if (!mounted) {
        return;
      }

      const storedOrganizationId = readStoredOrganizationId();
      const resolution = resolveOrganizationContext({
        organizationsResult,
        sessionResult,
        storedOrganizationId,
      });

      if (resolution.shouldClearStoredOrganization) {
        storeOrganizationId(null);
      } else if (resolution.selectedOrganizationId) {
        storeOrganizationId(resolution.selectedOrganizationId);
      }

      setOrganizations(resolution.organizations);
      setSelectedOrganizationId(resolution.selectedOrganizationId);
      setError(resolution.error);
      setStatus(resolution.status);
    }

    void loadOrganizationContext();

    return () => {
      mounted = false;
    };
  }, []);

  const selectOrganization = useCallback((organizationId: OrganizationId | null) => {
    setSelectedOrganizationId(organizationId);
    storeOrganizationId(organizationId);
  }, []);

  const selectedOrganization = useMemo(
    () => organizations.find((organization) => organization.id === selectedOrganizationId) ?? null,
    [organizations, selectedOrganizationId],
  );

  const value = useMemo<ActiveOrganizationContextValue>(
    () => ({
      status,
      organizations,
      selectedOrganizationId,
      selectedOrganization,
      error,
      selectOrganization,
    }),
    [error, organizations, selectOrganization, selectedOrganization, selectedOrganizationId, status],
  );

  return <ActiveOrganizationContext.Provider value={value}>{children}</ActiveOrganizationContext.Provider>;
}

export function useActiveOrganization() {
  const value = useContext(ActiveOrganizationContext);
  if (!value) {
    throw new Error("useActiveOrganization must be used inside ActiveOrganizationProvider.");
  }
  return value;
}
