"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Building2, LockKeyhole, RefreshCw, ShieldCheck } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Table, type TableColumn } from "@/components/ui/Table";
import { ApiError, api } from "@/lib/api";
import {
  SETTINGS_ADMIN_ACTIONS_ENABLED,
  SETTINGS_ENDPOINTS,
  SETTINGS_READ_ONLY,
  buildAccountRows,
  buildSettingsKpis,
  getSettingsErrorState,
  hasSettingsData,
  isSettingsEmpty,
  readSettingsSnapshot,
  type SettingsErrorState,
  type SettingsInfoRow,
  type SettingsOrganization,
  type SettingsSnapshot,
  type SettingsStatus,
} from "./settingsModel";

const infoColumns: Array<TableColumn<SettingsInfoRow>> = [
  {
    key: "label",
    header: "Obszar",
    render: (row) => <span className="module-row-title">{row.label}</span>,
  },
  {
    key: "value",
    header: "Wartosc",
    render: (row) => row.value,
  },
  {
    key: "status",
    header: "Status",
    render: (row) => <StatusBadge status={row.tone}>{row.tone === "ok" ? "Aktywne" : row.tone === "warning" ? "Uwaga" : "Info"}</StatusBadge>,
  },
  {
    key: "hint",
    header: "Zrodlo",
    render: (row) => row.hint,
  },
];

const organizationColumns: Array<TableColumn<SettingsOrganization>> = [
  {
    key: "name",
    header: "Organizacja",
    render: (row) => (
      <span className="module-row-title">
        <Building2 aria-hidden="true" size={16} />
        {row.name}
      </span>
    ),
  },
  {
    key: "slug",
    header: "Slug / ID",
    render: (row) => row.slug ?? row.id,
  },
  {
    key: "modules",
    header: "Moduly",
    render: (row) => (row.enabledModules.length ? row.enabledModules.join(", ") : "Brak danych"),
  },
  {
    key: "status",
    header: "Status",
    render: (row) => <StatusBadge status={row.isActive === false ? "warning" : "ok"}>{row.isActive === false ? "Nieaktywna" : "Aktywna"}</StatusBadge>,
  },
];

type SourceResult = {
  key: string;
  payload?: unknown;
  error?: unknown;
};

export function SettingsPage() {
  const [snapshot, setSnapshot] = useState<SettingsSnapshot | null>(null);
  const [status, setStatus] = useState<SettingsStatus>("idle");
  const [errorState, setErrorState] = useState<SettingsErrorState | null>(null);

  const loadSettings = useCallback(async () => {
    setStatus("loading");
    setErrorState(null);

    try {
      const results = await Promise.allSettled([api.currentSession(), api.meta(), api.organizations(), api.users()]);
      const sources = mapSourceResults(["session", "meta", "organizations", "users"], results);
      const criticalFailure = sources
        .filter((source) => source.key === "session" || source.key === "meta")
        .find((source) => source.error instanceof ApiError && [401, 403].includes(source.error.status));
      if (criticalFailure?.error) {
        throw criticalFailure.error;
      }

      const nextSnapshot = readSettingsSnapshot({
        session: sources[0]?.payload,
        meta: sources[1]?.payload,
        organizations: sources[2]?.payload,
        users: sources[3]?.payload,
        missingSources: sources.filter((source) => source.error).map((source) => source.key),
      });

      setSnapshot(nextSnapshot);
      setStatus("ready");
    } catch (error) {
      const nextErrorState = getSettingsErrorState(error);
      setErrorState(nextErrorState);
      setSnapshot(null);
      setStatus(nextErrorState.status);
    }
  }, []);

  useEffect(() => {
    void loadSettings();
  }, [loadSettings]);

  const kpis = useMemo(() => (snapshot ? buildSettingsKpis(snapshot) : null), [snapshot]);
  const accountRows = useMemo(() => (snapshot ? buildAccountRows(snapshot) : []), [snapshot]);
  const hasData = hasSettingsData(status, snapshot);
  const readyWithoutData = isSettingsEmpty(status, snapshot);

  return (
    <div className="module-page settings-page">
      <PageHeader
        badgeTone={status === "ready" ? "success" : status === "error" ? "warning" : "info"}
        description="Bezpieczny, tylko-do-odczytu podglad konfiguracji konta, organizacji, uprawnien i statusu srodowiska."
        eyebrow={status === "ready" ? "Dane live" : "Konfiguracja"}
        title="Ustawienia"
        actions={
          <Button disabled={status === "loading"} icon={<RefreshCw size={15} />} onClick={loadSettings} size="sm" variant="secondary">
            Odswiez
          </Button>
        }
      />

      {status === "loading" ? <LoadingState /> : null}
      {errorState ? <ErrorState description={errorState.description} title={errorState.title} /> : null}
      {readyWithoutData ? (
        <EmptyState
          description="Endpointy odpowiedzialy, ale nie zwrocily danych konta, organizacji ani statusu srodowiska."
          title="Brak danych ustawien"
        />
      ) : null}

      {hasData && kpis && snapshot ? (
        <>
          <section className="module-kpi-row" aria-label="Podsumowanie ustawien">
            <Card className="module-metric">
              <span className="module-metric__label">Tryb ekranu</span>
              <strong>{kpis.readOnlyMode}</strong>
              <span>Bez edycji profilu, rol, sekretow, modulow i sesji.</span>
            </Card>
            <Card className="module-metric">
              <span className="module-metric__label">Organizacje</span>
              <strong>{kpis.organizations}</strong>
              <span>Widoczne z API organizacji albo z aktywnej sesji.</span>
            </Card>
            <Card className="module-metric">
              <span className="module-metric__label">Uzytkownicy</span>
              <strong>{kpis.users}</strong>
              <span>Lista pelna tylko dla kont z dostepem do /api/users.</span>
            </Card>
            <Card className="module-metric">
              <span className="module-metric__label">Uprawnienia</span>
              <strong>{kpis.capabilities}</strong>
              <span>Capabilities przypisane do aktualnego konta.</span>
            </Card>
          </section>

          {snapshot.missingSources.length ? (
            <Card
              description={`Czesc zrodel nie byla dostepna: ${snapshot.missingSources.join(", ")}. Widok pokazuje pozostale bezpieczne dane zamiast blokowac caly ekran.`}
              title="Widok czesciowy"
            />
          ) : null}

          <Card description="Podstawowe informacje z aktywnej sesji. Ekran niczego nie zapisuje i nie modyfikuje." title="Konto i dostep">
            <Table columns={infoColumns} data={accountRows} emptyMessage="Brak danych konta." getRowKey={(row) => row.id} />
          </Card>

          <Card
            description="Aktywne moduly i capabilities z sesji oraz organizacji. To podglad, nie konfigurator uprawnien."
            title="Moduly i uprawnienia"
          >
            <div className="module-kpi-row">
              <Card className="module-metric">
                <span className="module-metric__label">Aktywne moduly</span>
                <strong>{kpis.activeModules}</strong>
                <span>{snapshot.activeModules.length ? snapshot.activeModules.join(", ") : "Brak modulow w odpowiedzi API."}</span>
              </Card>
              <Card className="module-metric">
                <span className="module-metric__label">Capabilities</span>
                <strong>{snapshot.capabilities.length}</strong>
                <span>{snapshot.capabilities.length ? snapshot.capabilities.join(", ") : "Brak capabilities w sesji."}</span>
              </Card>
              <Card className="module-metric">
                <span className="module-metric__label">Akcje administracyjne</span>
                <strong>{SETTINGS_ADMIN_ACTIONS_ENABLED ? "Aktywne" : "Wylaczone"}</strong>
                <span>Ten ekran nie zarzadza rolami, haslami ani sekretami.</span>
              </Card>
            </div>
          </Card>

          <Card description="Organizacje zwrocone przez istniejacy endpoint, jezeli konto ma do niego dostep." title="Organizacje">
            <Table
              columns={organizationColumns}
              data={snapshot.organizations.length ? snapshot.organizations : snapshot.activeOrganization ? [snapshot.activeOrganization] : []}
              emptyMessage="Brak dostepnych organizacji."
              getRowKey={(row) => row.id}
            />
          </Card>

          <Card
            description="Tylko bezpieczne pola meta. Sekrety, tokeny, connection stringi i prywatne sciezki sa pomijane albo redagowane."
            title="Status srodowiska"
          >
            <Table columns={infoColumns} data={snapshot.environmentRows} emptyMessage="Brak bezpiecznych metadanych srodowiska." getRowKey={(row) => row.id} />
          </Card>

          <Card description="Zakres przyszlego panelu administracyjnego bez udawania, ze edycja jest juz gotowa." title="Planowane ustawienia">
            <div className="module-kpi-row">
              <Card className="module-metric">
                <span className="module-metric__label">Profil i haslo</span>
                <strong>Planowane</strong>
                <span>Brak formularzy i zapisu danych w tym kroku.</span>
              </Card>
              <Card className="module-metric">
                <span className="module-metric__label">Role i dostepy</span>
                <strong>Read-only</strong>
                <span>Widoczne tylko jako informacja z backendu.</span>
              </Card>
              <Card className="module-metric">
                <span className="module-metric__label">Sekrety integracji</span>
                <strong>Ukryte</strong>
                <span>Nie pokazujemy tokenow, hasel ani connection stringow.</span>
              </Card>
            </div>
          </Card>

          <Card
            description="Ustawienia sa teraz bezpiecznym ekranem informacyjnym w Next, zbudowanym na istniejacych endpointach."
            title="Kontrakt bezpieczenstwa"
          >
            <div className="module-action-strip">
              <span className="module-row-title">
                <LockKeyhole aria-hidden="true" size={16} />
                {SETTINGS_READ_ONLY ? "Tryb tylko do odczytu" : "Tryb edycji"}
              </span>
              <span className="module-row-title">
                <ShieldCheck aria-hidden="true" size={16} />
                Sekrety nie sa renderowane
              </span>
            </div>
          </Card>
        </>
      ) : null}
    </div>
  );
}

function mapSourceResults(keys: string[], results: Array<PromiseSettledResult<unknown>>): SourceResult[] {
  return results.map((result, index) => {
    if (result.status === "fulfilled") {
      return { key: keys[index] ?? String(index), payload: result.value };
    }
    return { key: keys[index] ?? String(index), error: result.reason };
  });
}

void SETTINGS_ENDPOINTS;
