import { Bell, CircleHelp, Plus, Search } from "lucide-react";
import Link from "next/link";

import type { NavigationItem } from "@/config/navigation";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useActiveOrganization } from "@/context/ActiveOrganizationContext";

type TopbarProps = {
  currentModule: NavigationItem;
  sessionAttention?: boolean;
};

const readinessToneByStatus = {
  foundation: "info",
  live: "success",
  planned: "neutral",
} as const satisfies Record<NavigationItem["readiness"], "neutral" | "success" | "warning" | "danger" | "info">;

export function Topbar({ currentModule, sessionAttention = false }: TopbarProps) {
  const {
    error: organizationError,
    organizations,
    selectedOrganizationId,
    selectOrganization,
    status: organizationStatus,
  } = useActiveOrganization();
  const showOrganizationSelector = organizations.length > 0 || organizationStatus === "loading";
  const organizationSelectorDisabled = organizationStatus === "loading" || organizations.length <= 1;

  return (
    <header className="app-topbar">
      <div className="app-topbar__module">
        <div className="app-topbar__module-meta">
          <span className="app-topbar__eyebrow">Aktualny modul</span>
          <Badge tone={readinessToneByStatus[currentModule.readiness]}>{currentModule.readinessLabel}</Badge>
        </div>
        <h1>{currentModule.label}</h1>
        <p>{currentModule.description}</p>
      </div>
      <div className="app-topbar__search">
        <Input
          aria-label="Szukaj w CASI"
          icon={<Search size={16} />}
          placeholder="Szukaj w module i bazie wiedzy..."
          type="search"
        />
        <kbd className="app-topbar__shortcut">Ctrl + K</kbd>
      </div>
      <div className="app-topbar__actions">
        {showOrganizationSelector ? (
          <label className="app-topbar__organization">
            <span>Organizacja</span>
            <select
              aria-label="Aktywna organizacja"
              disabled={organizationSelectorDisabled}
              onChange={(event) => selectOrganization(event.target.value || null)}
              value={selectedOrganizationId ?? ""}
            >
              {organizationStatus === "loading" ? <option value="">Ladowanie organizacji...</option> : null}
              {organizations.length > 1 ? <option value="">Wybierz organizacje</option> : null}
              {organizations.map((organization) => (
                <option key={organization.id} value={organization.id}>
                  {organization.name}
                </option>
              ))}
            </select>
          </label>
        ) : null}
        {organizationStatus === "error" || organizationStatus === "unauthenticated" ? (
          <div className="app-topbar__session-alert" role="status">
            <strong>{organizationError?.title ?? "Brak kontekstu organizacji"}</strong>
            {organizationStatus === "unauthenticated" ? <Link href="/login">Zaloguj sie</Link> : <span>Odswiez widok</span>}
          </div>
        ) : null}
        {sessionAttention ? (
          <div className="app-topbar__session-alert" role="status">
            <strong>Sesja wygasla</strong>
            <Link href="/login">Zaloguj sie ponownie</Link>
          </div>
        ) : null}
        <Button icon={<Plus size={15} />} size="sm" variant="primary">
          {currentModule.actionLabel}
        </Button>
        <button className="app-topbar__icon-button" type="button" aria-label="Powiadomienia">
          <Bell aria-hidden="true" size={17} />
          <span>3</span>
        </button>
        <button className="app-topbar__icon-button" type="button" aria-label="Pomoc">
          <CircleHelp aria-hidden="true" size={17} />
        </button>
        <button className="app-topbar__profile" type="button" aria-label="Profil uzytkownika">
          <span className="app-topbar__avatar">EK</span>
          <span className="app-topbar__profile-copy">
            <strong>Eryk Kowalski</strong>
            <span>Administrator</span>
          </span>
        </button>
      </div>
    </header>
  );
}
