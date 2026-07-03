"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Bot, ClipboardList, RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Table, type TableColumn } from "@/components/ui/Table";
import { useActiveOrganization } from "@/context/ActiveOrganizationContext";
import { withActiveOrganizationQuery } from "@/context/organizationContextModel";
import { api } from "@/lib/api";
import {
  BOSS_ASSISTANT_AI_ACTIONS_ENABLED,
  BOSS_ASSISTANT_ENDPOINT,
  BOSS_ASSISTANT_ORGANIZATION_REQUIRED_DESCRIPTION,
  BOSS_ASSISTANT_ORGANIZATION_REQUIRED_TITLE,
  BOSS_ASSISTANT_READ_ONLY,
  buildBossAssistantKpis,
  buildBossAssistantRows,
  canUseBossAssistantOrganizationScope,
  getBossAssistantErrorState,
  hasBossAssistantData,
  isBossAssistantEmpty,
  readTaskFocusSnapshot,
  type BossAssistantErrorState,
  type BossAssistantStatus,
  type BossAssistantViewRow,
  type TaskFocusSnapshot,
} from "./bossAssistantModel";

const columns: Array<TableColumn<BossAssistantViewRow>> = [
  {
    key: "title",
    header: "Sprawa",
    render: (row) => (
      <span className="module-row-title">
        <ClipboardList aria-hidden="true" size={16} />
        {row.title}
      </span>
    ),
  },
  {
    key: "focus",
    header: "Widok",
    render: (row) => <StatusBadge status="info">{row.focusLabel}</StatusBadge>,
  },
  {
    key: "status",
    header: "Status",
    render: (row) => <StatusBadge status={row.statusTone}>{row.statusLabel}</StatusBadge>,
  },
  {
    key: "priority",
    header: "Priorytet",
    render: (row) => <StatusBadge status={row.priorityTone}>{row.priorityLabel}</StatusBadge>,
  },
  {
    key: "due",
    header: "Termin",
    render: (row) => row.dueLabel,
  },
  {
    key: "source",
    header: "Typ",
    render: (row) => row.sourceLabel,
  },
  {
    key: "owner",
    header: "Wlasciciel",
    render: (row) => row.ownerLabel,
  },
];

export function AssistantCeoPage() {
  const [snapshot, setSnapshot] = useState<TaskFocusSnapshot | null>(null);
  const [status, setStatus] = useState<BossAssistantStatus>("idle");
  const [errorState, setErrorState] = useState<BossAssistantErrorState | null>(null);
  const { selectedOrganizationId, selectedOrganization, status: organizationStatus } = useActiveOrganization();

  const loadFocus = useCallback(async () => {
    if (organizationStatus === "loading") {
      setStatus("loading");
      setErrorState(null);
      return;
    }

    if (!canUseBossAssistantOrganizationScope(selectedOrganizationId)) {
      setStatus("ready");
      setErrorState(null);
      setSnapshot(null);
      return;
    }

    setStatus("loading");
    setErrorState(null);

    try {
      const payload = await api.taskFocus(withActiveOrganizationQuery(selectedOrganizationId));
      const nextSnapshot = readTaskFocusSnapshot(payload);
      setSnapshot(nextSnapshot);
      setStatus("ready");
    } catch (error) {
      const nextErrorState = getBossAssistantErrorState(error);
      setErrorState(nextErrorState);
      setSnapshot(null);
      setStatus(nextErrorState.status);
    }
  }, [organizationStatus, selectedOrganizationId]);

  useEffect(() => {
    void loadFocus();
  }, [loadFocus]);

  const rows = useMemo(() => buildBossAssistantRows(snapshot ?? { available_views: [], views: [] }), [snapshot]);
  const kpis = useMemo(() => buildBossAssistantKpis(snapshot ?? { available_views: [], views: [] }), [snapshot]);
  const organizationMissing =
    organizationStatus === "ready" && !canUseBossAssistantOrganizationScope(selectedOrganizationId);
  const hasData = hasBossAssistantData(status, snapshot);
  const readyWithoutData = !organizationMissing && isBossAssistantEmpty(status, snapshot);

  return (
    <div className="module-page assistant-ceo-page">
      <PageHeader
        badgeTone={status === "ready" ? "success" : status === "error" ? "warning" : "info"}
        description="Centrum decyzji i spraw wymagajacych uwagi wlasciciela lub managera. Ten ekran jest read-only MVP bez agenta AI."
        eyebrow={status === "ready" ? "Dane live" : "Asystent Szefa"}
        title="Asystent Szefa"
        actions={
          <Button disabled={status === "loading"} icon={<RefreshCw size={15} />} onClick={loadFocus} size="sm" variant="secondary">
            Odswiez
          </Button>
        }
      />

      {status === "loading" ? <LoadingState /> : null}
      {errorState ? <ErrorState description={errorState.description} title={errorState.title} /> : null}
      {organizationMissing ? (
        <EmptyState
          description={BOSS_ASSISTANT_ORGANIZATION_REQUIRED_DESCRIPTION}
          title={BOSS_ASSISTANT_ORGANIZATION_REQUIRED_TITLE}
        />
      ) : null}
      {readyWithoutData ? (
        <EmptyState
          description={`Backend odpowiedzial poprawnie, ale focus snapshot nie zawiera spraw wymagajacych uwagi dla organizacji ${selectedOrganization?.name ?? selectedOrganizationId}.`}
          title="Brak spraw do pokazania"
        />
      ) : null}

      {hasData ? (
        <>
          <section className="module-kpi-row" aria-label="Podsumowanie Asystenta Szefa">
            <Card className="module-metric">
              <span className="module-metric__label">Tryb ekranu</span>
              <strong>{BOSS_ASSISTANT_READ_ONLY ? "Read-only" : "Akcje wlaczone"}</strong>
              <span>Bez chatu AI, rekomendacji, zmian statusu i automatyzacji.</span>
            </Card>
            <Card className="module-metric">
              <span className="module-metric__label">Na dzis</span>
              <strong>{kpis.today}</strong>
              <span>Pobrane z {BOSS_ASSISTANT_ENDPOINT}.</span>
            </Card>
            <Card className="module-metric">
              <span className="module-metric__label">Do decyzji / blokery</span>
              <strong>{kpis.decisions + kpis.blockers}</strong>
              <span>{kpis.decisions} decyzji, {kpis.blockers} spraw czeka na kogos.</span>
            </Card>
            <Card className="module-metric">
              <span className="module-metric__label">Zalegle / pilne</span>
              <strong>{kpis.overdue + kpis.urgent}</strong>
              <span>{kpis.overdue} po terminie, {kpis.urgent} z wysokim priorytetem.</span>
            </Card>
          </section>

          <Card
            description="Lista laczy najwazniejsze pozycje z widokow focus: do decyzji, po terminie, moj dzien i sprawy czekajace na innych."
            title="Najwazniejsze sprawy do uwagi"
          >
            <Table
              columns={columns}
              data={rows}
              emptyMessage="Focus snapshot nie zwrocil spraw."
              getRowKey={(row) => row.id}
            />
          </Card>

          <Card
            description="Ten panel celowo nie wykonuje zadnych akcji. Pokazuje tylko granice MVP przed budowa prawdziwego agenta."
            title="Wersja read-only, bez agenta AI"
          >
            <div className="module-kpi-row">
              <Card className="module-metric">
                <span className="module-metric__label">
                  <Bot aria-hidden="true" size={14} /> Rekomendacje AI
                </span>
                <strong>{BOSS_ASSISTANT_AI_ACTIONS_ENABLED ? "Aktywne" : "Nieaktywne"}</strong>
                <span>Brak generowania decyzji i sugestii przez LLM.</span>
              </Card>
              <Card className="module-metric">
                <span className="module-metric__label">Akcje na zadaniach</span>
                <strong>Nieaktywne</strong>
                <span>Widok nie tworzy, nie zamyka i nie deleguje zadan.</span>
              </Card>
              <Card className="module-metric">
                <span className="module-metric__label">Automatyzacje</span>
                <strong>Nieaktywne</strong>
                <span>Brak wysylek Telegram, Slack, e-mail i przypomnien z UI.</span>
              </Card>
            </div>
          </Card>
        </>
      ) : null}
    </div>
  );
}
