import { ApiContractError, ApiError } from "@/lib/api";
import type { DataViewErrorState, DataViewStatus } from "@/lib/types";

export type SettingsStatus = DataViewStatus;
export type SettingsErrorState = DataViewErrorState<SettingsStatus>;
export type SettingsBadgeTone = "ok" | "warning" | "danger" | "info" | "neutral";

export type SettingsUser = {
  id: string;
  login: string;
  displayName: string;
  role: string;
  organizationId?: string;
  organizationName?: string;
  isActive?: boolean;
  isGlobalAdmin?: boolean;
  capabilities: string[];
  organizationModules: string[];
};

export type SettingsOrganization = {
  id: string;
  name: string;
  slug?: string;
  isActive?: boolean;
  enabledModules: string[];
};

export type SettingsInfoRow = {
  id: string;
  label: string;
  value: string;
  hint: string;
  tone: SettingsBadgeTone;
};

export type SettingsKpis = {
  readOnlyMode: string;
  organizations: number;
  users: number;
  activeModules: number;
  capabilities: number;
};

export type SettingsSnapshot = {
  currentUser?: SettingsUser;
  activeOrganization?: SettingsOrganization;
  organizations: SettingsOrganization[];
  users: SettingsUser[];
  capabilities: string[];
  activeModules: string[];
  environmentRows: SettingsInfoRow[];
  missingSources: string[];
};

export const SETTINGS_READ_ONLY = true;
export const SETTINGS_ADMIN_ACTIONS_ENABLED = false;
export const SETTINGS_ENDPOINTS = {
  session: "/session/current",
  meta: "/meta",
  organizations: "/organizations",
  users: "/users",
} as const;

const SETTINGS_CONTRACT_ENDPOINT = "/settings/read-only";
const REDACTED_VALUE = "Ukryte";

const META_LABELS: Record<string, string> = {
  app_release_id: "Release aplikacji",
  database_label: "Baza danych",
  db_engine: "Silnik bazy",
  default_login_hint_enabled: "Podpowiedz logowania",
  email_enabled: "E-mail",
  email_mode: "Tryb e-mail",
  google_calendar_direct_enabled: "Google Calendar",
  ksef_enabled: "KSeF",
  ksef_mode: "Tryb KSeF",
  ocr_enabled: "OCR",
  ocr_mode: "Tryb OCR",
  public_base_url: "Publiczny URL",
  storage_backend: "Storage backend",
  telegram_enabled: "Telegram",
  test_imports_enabled: "Importy testowe",
};

const SAFE_META_KEYS = Object.keys(META_LABELS);
const SENSITIVE_KEY_PATTERN = /(secret|token|password|passwd|database_url|connection_string|private|credential|oauth|access_key|secret_key|dsn|cookie|session)/i;
const PATH_KEY_PATTERN = /(path|root|directory|folder|file_system|filesystem)/i;

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

function readBoolean(value: unknown): boolean | undefined {
  if (typeof value === "boolean") {
    return value;
  }
  if (typeof value === "number") {
    return value === 1;
  }
  if (typeof value === "string") {
    const normalized = value.trim().toLowerCase();
    if (["1", "true", "tak", "yes", "enabled", "on"].includes(normalized)) {
      return true;
    }
    if (["0", "false", "nie", "no", "disabled", "off"].includes(normalized)) {
      return false;
    }
  }
  return undefined;
}

function readStringList(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value
      .map((item) => readOptionalString(item))
      .filter((item): item is string => Boolean(item));
  }
  if (typeof value === "string") {
    return value
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
  }
  return [];
}

function uniqueSorted(values: string[]): string[] {
  return [...new Set(values.filter(Boolean))].sort((left, right) => left.localeCompare(right));
}

function looksLikePrivatePath(value: string): boolean {
  const normalized = value.replaceAll("/", "\\");
  return /^[a-z]:\\/i.test(normalized) || normalized.includes("\\Users\\") || normalized.includes("\\home\\") || normalized.includes("\\OneDrive\\");
}

function isSensitiveKey(key: string): boolean {
  return SENSITIVE_KEY_PATTERN.test(key) || PATH_KEY_PATTERN.test(key);
}

export function sanitizeSettingValue(key: string, value: unknown): string {
  if (isSensitiveKey(key)) {
    return REDACTED_VALUE;
  }

  if (value === null || value === undefined || value === "") {
    return "Brak danych";
  }

  if (typeof value === "boolean") {
    return value ? "Tak" : "Nie";
  }

  if (typeof value === "number" && Number.isFinite(value)) {
    return String(value);
  }

  if (Array.isArray(value)) {
    return value.map((item) => sanitizeSettingValue(key, item)).join(", ") || "Brak danych";
  }

  if (typeof value === "string") {
    if (looksLikePrivatePath(value) || SENSITIVE_KEY_PATTERN.test(value)) {
      return REDACTED_VALUE;
    }
    return value.trim() || "Brak danych";
  }

  return "Obiekt konfiguracyjny";
}

export function buildSafeEnvironmentRows(meta: unknown): SettingsInfoRow[] {
  if (meta === undefined || meta === null) {
    return [];
  }
  if (!isRecord(meta)) {
    throw new ApiContractError(SETTINGS_ENDPOINTS.meta, meta);
  }

  return SAFE_META_KEYS.filter((key) => key in meta).map((key) => ({
    id: key,
    label: META_LABELS[key] ?? key,
    value: sanitizeSettingValue(key, meta[key]),
    hint: key,
    tone: environmentTone(key, meta[key]),
  }));
}

function environmentTone(key: string, value: unknown): SettingsBadgeTone {
  if (key.endsWith("_enabled") || key === "test_imports_enabled" || key === "google_calendar_direct_enabled") {
    return readBoolean(value) ? "ok" : "neutral";
  }
  if (key === "storage_backend" || key === "db_engine") {
    return "info";
  }
  return "neutral";
}

function readUser(value: unknown, originalPayload: unknown): SettingsUser {
  if (!isRecord(value)) {
    throw new ApiContractError(SETTINGS_CONTRACT_ENDPOINT, originalPayload);
  }

  const id = readOptionalString(value.user_id) ?? readOptionalString(value.id);
  const login = readOptionalString(value.login);
  if (!id || !login) {
    throw new ApiContractError(SETTINGS_CONTRACT_ENDPOINT, originalPayload);
  }

  return {
    id,
    login,
    displayName: readOptionalString(value.display_name) ?? login,
    role: readOptionalString(value.role) ?? "nieznana",
    organizationId: readOptionalString(value.organization_id),
    organizationName: readOptionalString(value.organization_name),
    isActive: readBoolean(value.is_active),
    isGlobalAdmin: readBoolean(value.is_global_admin),
    capabilities: uniqueSorted(readStringList(value.capabilities)),
    organizationModules: uniqueSorted(readStringList(value.organization_modules)),
  };
}

function readSessionUser(session: unknown): SettingsUser | undefined {
  if (session === undefined || session === null) {
    return undefined;
  }
  if (!isRecord(session)) {
    throw new ApiContractError(SETTINGS_ENDPOINTS.session, session);
  }
  if (session.authenticated === false) {
    return undefined;
  }
  return readUser(isRecord(session.user) ? session.user : session, session);
}

function readOrganization(value: unknown, originalPayload: unknown): SettingsOrganization {
  if (!isRecord(value)) {
    throw new ApiContractError(SETTINGS_ENDPOINTS.organizations, originalPayload);
  }

  const id = readOptionalString(value.organization_id) ?? readOptionalString(value.id);
  if (!id) {
    throw new ApiContractError(SETTINGS_ENDPOINTS.organizations, originalPayload);
  }

  return {
    id,
    name: readOptionalString(value.name) ?? readOptionalString(value.organization_name) ?? `Organizacja #${id}`,
    slug: readOptionalString(value.slug) ?? readOptionalString(value.organization_slug),
    isActive: readBoolean(value.is_active),
    enabledModules: uniqueSorted(readStringList(value.enabled_modules ?? value.organization_modules ?? value.modules)),
  };
}

function readOrganizations(payload: unknown): SettingsOrganization[] {
  if (payload === undefined || payload === null) {
    return [];
  }
  const source = isRecord(payload) && Array.isArray(payload.organizations) ? payload.organizations : payload;
  if (!Array.isArray(source)) {
    throw new ApiContractError(SETTINGS_ENDPOINTS.organizations, payload);
  }
  return source.map((item) => readOrganization(item, payload));
}

function readUsers(payload: unknown): SettingsUser[] {
  if (payload === undefined || payload === null) {
    return [];
  }
  const source = isRecord(payload) && Array.isArray(payload.users) ? payload.users : payload;
  if (!Array.isArray(source)) {
    throw new ApiContractError(SETTINGS_ENDPOINTS.users, payload);
  }
  return source.map((item) => readUser(item, payload));
}

function fallbackOrganizationFromUser(user: SettingsUser | undefined): SettingsOrganization | undefined {
  if (!user?.organizationId) {
    return undefined;
  }
  return {
    id: user.organizationId,
    name: user.organizationName ?? `Organizacja #${user.organizationId}`,
    enabledModules: user.organizationModules,
  };
}

export function readSettingsSnapshot(payload: unknown): SettingsSnapshot {
  if (!isRecord(payload)) {
    throw new ApiContractError(SETTINGS_CONTRACT_ENDPOINT, payload);
  }

  const currentUser = readSessionUser(payload.session);
  const organizations = readOrganizations(payload.organizations);
  const users = readUsers(payload.users);
  const environmentRows = buildSafeEnvironmentRows(payload.meta);
  const activeOrganization =
    organizations.find((organization) => organization.id === currentUser?.organizationId) ?? fallbackOrganizationFromUser(currentUser);
  const capabilities = uniqueSorted(currentUser?.capabilities ?? []);
  const activeModules = uniqueSorted([...(activeOrganization?.enabledModules ?? []), ...(currentUser?.organizationModules ?? [])]);

  return {
    currentUser,
    activeOrganization,
    organizations,
    users,
    capabilities,
    activeModules,
    environmentRows,
    missingSources: readStringList(payload.missingSources),
  };
}

export function buildSettingsKpis(snapshot: SettingsSnapshot): SettingsKpis {
  return {
    readOnlyMode: SETTINGS_READ_ONLY ? "Read-only" : "Akcje aktywne",
    organizations: snapshot.organizations.length || (snapshot.activeOrganization ? 1 : 0),
    users: snapshot.users.length || (snapshot.currentUser ? 1 : 0),
    activeModules: snapshot.activeModules.length,
    capabilities: snapshot.capabilities.length,
  };
}

export function buildAccountRows(snapshot: SettingsSnapshot): SettingsInfoRow[] {
  const user = snapshot.currentUser;
  return [
    {
      id: "user",
      label: "Uzytkownik",
      value: user ? `${user.displayName} (${user.login})` : "Brak aktywnej sesji",
      hint: user?.id ? `ID ${user.id}` : "session/current",
      tone: user ? "ok" : "warning",
    },
    {
      id: "role",
      label: "Rola",
      value: user?.role ?? "Brak danych",
      hint: user?.isGlobalAdmin ? "operator globalny" : "rola konta",
      tone: user?.isGlobalAdmin ? "info" : "neutral",
    },
    {
      id: "organization",
      label: "Organizacja",
      value: snapshot.activeOrganization?.name ?? "Brak przypisanej organizacji",
      hint: snapshot.activeOrganization?.slug ?? snapshot.activeOrganization?.id ?? "organizacja z sesji",
      tone: snapshot.activeOrganization ? "ok" : "warning",
    },
    {
      id: "mode",
      label: "Tryb ustawien",
      value: SETTINGS_READ_ONLY ? "Tylko podglad" : "Edycja wlaczona",
      hint: SETTINGS_ADMIN_ACTIONS_ENABLED ? "akcje administracyjne aktywne" : "bez akcji administracyjnych",
      tone: SETTINGS_READ_ONLY ? "info" : "warning",
    },
  ];
}

export function hasSettingsData(status: SettingsStatus, snapshot: SettingsSnapshot | null): boolean {
  return status === "ready" && Boolean(snapshot?.currentUser || snapshot?.activeOrganization || snapshot?.environmentRows.length);
}

export function isSettingsEmpty(status: SettingsStatus, snapshot: SettingsSnapshot | null): boolean {
  return status === "ready" && !hasSettingsData(status, snapshot);
}

export function getSettingsErrorState(error: unknown): SettingsErrorState {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      return {
        status: "unauthenticated",
        title: "Sesja wygasla",
        description: "Zaloguj sie ponownie, aby zobaczyc konfiguracje konta i organizacji.",
      };
    }
    if (error.status === 403) {
      return {
        status: "forbidden",
        title: "Brak dostepu do ustawien",
        description: "Twoje konto nie ma uprawnien do odczytu tej czesci konfiguracji.",
      };
    }
    if (error.status >= 500) {
      return {
        status: "server-error",
        title: "Backend nie zwrocil konfiguracji",
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
      title: "Niepoprawny format ustawien",
      description: "Jedno ze zrodel odpowiedzialo danymi niepasujacymi do minimalnego kontraktu ekranu Ustawienia.",
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
    title: "Nie udalo sie pobrac ustawien",
    description: error instanceof Error ? error.message : "Wystapil nieznany blad pobierania ustawien.",
  };
}
