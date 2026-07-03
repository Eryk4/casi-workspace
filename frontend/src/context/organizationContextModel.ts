import { ApiContractError, ApiError } from "@/lib/api";
import type { ApiQuery, OrganizationId } from "@/lib/types";

export const ACTIVE_ORGANIZATION_STORAGE_KEY = "casi.activeOrganizationId";

export type OrganizationOption = {
  id: OrganizationId;
  name: string;
  slug?: string;
  isActive: boolean;
};

export type SessionOrganizationSnapshot = {
  organizationId: OrganizationId | null;
  organizationName: string | null;
  isGlobalAdmin: boolean;
};

export type ActiveOrganizationStatus = "loading" | "ready" | "unauthenticated" | "error";

export type OrganizationContextErrorKind = "session" | "organizations" | "contract";

export type OrganizationContextError = {
  kind: OrganizationContextErrorKind;
  title: string;
  description: string;
};

export type OrganizationContextResolution = {
  status: Exclude<ActiveOrganizationStatus, "loading">;
  organizations: OrganizationOption[];
  selectedOrganizationId: OrganizationId | null;
  error: OrganizationContextError | null;
  shouldClearStoredOrganization: boolean;
};

type SettledValue<T> =
  | {
      status: "fulfilled";
      value: T;
    }
  | {
      reason: unknown;
      status: "rejected";
    };

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function readOptionalString(value: unknown): string | undefined {
  if (typeof value === "string" && value.trim()) {
    return value.trim();
  }
  if (typeof value === "number" && Number.isFinite(value)) {
    return String(value);
  }
  return undefined;
}

function readBoolean(value: unknown, fallback = true): boolean {
  if (typeof value === "boolean") {
    return value;
  }
  if (typeof value === "number") {
    return value !== 0;
  }
  if (typeof value === "string") {
    const normalized = value.trim().toLowerCase();
    if (["0", "false", "nie", "no", "off"].includes(normalized)) {
      return false;
    }
    if (["1", "true", "tak", "yes", "on"].includes(normalized)) {
      return true;
    }
  }
  return fallback;
}

export function readSessionOrganizationSnapshot(payload: unknown): SessionOrganizationSnapshot {
  if (!isRecord(payload)) {
    return {
      organizationId: null,
      organizationName: null,
      isGlobalAdmin: false,
    };
  }

  const source = isRecord(payload.user) ? payload.user : payload;

  return {
    organizationId: readOptionalString(source.organization_id) ?? null,
    organizationName: readOptionalString(source.organization_name) ?? null,
    isGlobalAdmin: readBoolean(source.is_global_admin, false),
  };
}

export function isAuthenticatedSession(payload: unknown): boolean {
  if (!isRecord(payload)) {
    return false;
  }

  if ("authenticated" in payload) {
    return payload.authenticated !== false;
  }

  return Boolean(readOptionalString(payload.user_id) ?? readOptionalString(payload.id) ?? readOptionalString(payload.login));
}

export function readOrganizations(payload: unknown): OrganizationOption[] {
  const source = isRecord(payload) && Array.isArray(payload.value) ? payload.value : payload;

  if (!Array.isArray(source)) {
    throw new ApiContractError("/organizations", payload);
  }

  return source
    .map((item) => {
      if (!isRecord(item)) {
        throw new ApiContractError("/organizations", payload);
      }

      const id = readOptionalString(item.organization_id) ?? readOptionalString(item.id);
      if (!id) {
        throw new ApiContractError("/organizations", payload);
      }

      return {
        id,
        name: readOptionalString(item.name) ?? readOptionalString(item.organization_name) ?? `Organizacja #${id}`,
        slug: readOptionalString(item.slug) ?? readOptionalString(item.organization_slug),
        isActive: readBoolean(item.is_active, true),
      };
    })
    .filter((organization) => organization.isActive);
}

export function buildFallbackOrganization(snapshot: SessionOrganizationSnapshot): OrganizationOption | null {
  if (!snapshot.organizationId) {
    return null;
  }

  return {
    id: snapshot.organizationId,
    name: snapshot.organizationName ?? `Organizacja #${snapshot.organizationId}`,
    isActive: true,
  };
}

export function mergeOrganizationOptions(
  organizations: OrganizationOption[],
  fallback: OrganizationOption | null,
): OrganizationOption[] {
  if (!fallback || organizations.some((organization) => organization.id === fallback.id)) {
    return organizations;
  }
  return [fallback, ...organizations];
}

export function resolveInitialOrganizationId(params: {
  organizations: OrganizationOption[];
  sessionOrganizationId: OrganizationId | null;
  storedOrganizationId?: OrganizationId | null;
  isGlobalAdmin?: boolean;
}): OrganizationId | null {
  const validIds = new Set(params.organizations.map((organization) => organization.id));

  if (params.organizations.length === 1) {
    return params.organizations[0].id;
  }

  if (params.storedOrganizationId && validIds.has(params.storedOrganizationId)) {
    return params.storedOrganizationId;
  }

  if (!params.isGlobalAdmin && params.sessionOrganizationId && validIds.has(params.sessionOrganizationId)) {
    return params.sessionOrganizationId;
  }

  return null;
}

function sessionError(reason?: unknown): OrganizationContextError {
  if (reason instanceof ApiError && reason.status === 401) {
    return {
      kind: "session",
      title: "Sesja wygasla",
      description: "Zaloguj sie ponownie, aby pobrac kontekst organizacji.",
    };
  }

  return {
    kind: "session",
    title: "Nie udalo sie pobrac sesji",
    description: "Frontend nie mogl pobrac aktualnej sesji uzytkownika z API.",
  };
}

function organizationsError(reason?: unknown): OrganizationContextError {
  if (reason instanceof ApiContractError) {
    return {
      kind: "contract",
      title: "Niepoprawny format organizacji",
      description: "Backend odpowiedzial, ale lista organizacji nie pasuje do kontraktu frontendu.",
    };
  }

  if (reason instanceof ApiError && reason.status === 401) {
    return sessionError(reason);
  }

  return {
    kind: "organizations",
    title: "Nie udalo sie pobrac organizacji",
    description: "Odswiez widok albo zaloguj sie ponownie, aby pobrac liste organizacji.",
  };
}

export function resolveOrganizationContext(params: {
  organizationsResult: SettledValue<unknown>;
  sessionResult: SettledValue<unknown>;
  storedOrganizationId?: OrganizationId | null;
}): OrganizationContextResolution {
  if (params.sessionResult.status === "rejected") {
    return {
      status: params.sessionResult.reason instanceof ApiError && params.sessionResult.reason.status === 401 ? "unauthenticated" : "error",
      organizations: [],
      selectedOrganizationId: null,
      error: sessionError(params.sessionResult.reason),
      shouldClearStoredOrganization: Boolean(params.storedOrganizationId),
    };
  }

  if (!isAuthenticatedSession(params.sessionResult.value)) {
    return {
      status: "unauthenticated",
      organizations: [],
      selectedOrganizationId: null,
      error: sessionError(new ApiError("Brak aktywnej sesji.", 401, null)),
      shouldClearStoredOrganization: Boolean(params.storedOrganizationId),
    };
  }

  const sessionSnapshot = readSessionOrganizationSnapshot(params.sessionResult.value);
  const fallbackOrganization = buildFallbackOrganization(sessionSnapshot);
  let nextOrganizations: OrganizationOption[] = [];
  let error: OrganizationContextError | null = null;

  if (params.organizationsResult.status === "fulfilled") {
    try {
      nextOrganizations = readOrganizations(params.organizationsResult.value);
    } catch (nextError) {
      error = organizationsError(nextError);
    }
  } else {
    error = organizationsError(params.organizationsResult.reason);
  }

  nextOrganizations = mergeOrganizationOptions(nextOrganizations, fallbackOrganization);

  if (nextOrganizations.length === 0 && error) {
    return {
      status: error.kind === "session" ? "unauthenticated" : "error",
      organizations: [],
      selectedOrganizationId: null,
      error,
      shouldClearStoredOrganization: Boolean(params.storedOrganizationId),
    };
  }

  const validIds = new Set(nextOrganizations.map((organization) => organization.id));
  const selectedOrganizationId = resolveInitialOrganizationId({
    organizations: nextOrganizations,
    sessionOrganizationId: sessionSnapshot.organizationId,
    storedOrganizationId: params.storedOrganizationId,
    isGlobalAdmin: sessionSnapshot.isGlobalAdmin,
  });

  return {
    status: "ready",
    organizations: nextOrganizations,
    selectedOrganizationId,
    error,
    shouldClearStoredOrganization: Boolean(params.storedOrganizationId && !validIds.has(params.storedOrganizationId)),
  };
}

export function withActiveOrganizationQuery(
  organizationId: OrganizationId | null | undefined,
  query: ApiQuery = {},
): ApiQuery {
  return organizationId ? { ...query, organization_id: organizationId } : query;
}
