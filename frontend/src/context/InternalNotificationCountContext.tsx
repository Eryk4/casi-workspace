"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";

import { useActiveOrganization } from "@/context/ActiveOrganizationContext";
import { api, withOrganizationQuery } from "@/lib/api";
import { readUnreadCount } from "@/modules/notifications/internalNotificationsModel";

type InternalNotificationCountContextValue = {
  unreadCount: number | null;
  refreshUnreadCount: () => Promise<void>;
};

const InternalNotificationCountContext = createContext<InternalNotificationCountContextValue | null>(null);

export function InternalNotificationCountProvider({ children }: { children: ReactNode }) {
  const { selectedOrganizationId, status } = useActiveOrganization();
  const [unreadCount, setUnreadCount] = useState<number | null>(null);
  const requestVersion = useRef(0);
  const selectedOrganizationRef = useRef(selectedOrganizationId);
  selectedOrganizationRef.current = selectedOrganizationId;

  const refreshUnreadCount = useCallback(async () => {
    const version = ++requestVersion.current;
    const organizationId = selectedOrganizationId;
    if (status !== "ready" || !organizationId) {
      setUnreadCount(null);
      return;
    }
    try {
      const payload = await api.internalNotificationUnreadCount(withOrganizationQuery(organizationId));
      if (version === requestVersion.current && organizationId === selectedOrganizationRef.current) {
        setUnreadCount(readUnreadCount(payload));
      }
    } catch {
      if (version === requestVersion.current) setUnreadCount(null);
    }
  }, [selectedOrganizationId, status]);

  useEffect(() => {
    setUnreadCount(null);
    void refreshUnreadCount();
  }, [refreshUnreadCount]);

  const value = useMemo(() => ({ unreadCount, refreshUnreadCount }), [refreshUnreadCount, unreadCount]);
  return <InternalNotificationCountContext.Provider value={value}>{children}</InternalNotificationCountContext.Provider>;
}

export function useInternalNotificationCount() {
  const value = useContext(InternalNotificationCountContext);
  if (!value) throw new Error("useInternalNotificationCount must be used inside its provider.");
  return value;
}
