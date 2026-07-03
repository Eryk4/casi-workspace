"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Bot, ClipboardList, FileArchive, RefreshCw, ShieldCheck } from "lucide-react";

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
  COMPANY_ASSISTANT_AI_AGENT_ENABLED,
  COMPANY_ASSISTANT_ORGANIZATION_REQUIRED_DESCRIPTION,
  COMPANY_ASSISTANT_ORGANIZATION_REQUIRED_TITLE,
  COMPANY_ASSISTANT_READ_ONLY,
  buildCompanyAssistantAttentionRows,
  buildCompanyAssistantKnowledgeRows,
  buildCompanyAssistantKpis,
  canUseCompanyAssistantOrganizationScope,
  getCompanyAssistantErrorState,
  hasCompanyAssistantData,
  isCompanyAssistantEmpty,
  readCompanyAssistantSnapshot,
  sourceError,
  sourceReady,
  type CompanyAssistantAttentionRow,
  type CompanyAssistantErrorState,
  type CompanyAssistantKnowledgeRow,
  type CompanyAssistantSnapshot,
  type CompanyAssistantStatus,
  type CompanyAssistantSourceKey,
  type CompanyAssistantSourceState,
} from "./companyAssistantModel";

const knowledgeColumns: Array<TableColumn<CompanyAssistantKnowledgeRow>> = [
  {
    key: "title",
    header: "Zrodlo",
    render: (row) => (
      <span className="module-row-title">
        <FileArchive aria-hidden="true" size={16} />
        {row.title}
      </span>
    ),
  },
  {
    key: "status",
    header: "Status",
    render: (row) => <StatusBadge status={row.statusTone}>{row.statusLabel}</StatusBadge>,
  },
  {
    key: "owner",
    header: "Opiekun",
    render: (row) => row.ownerLabel,
  },
  {
    key: "updated",
    header: "Aktualizacja",
    render: (row) => row.updatedLabel,
  },
];

const attentionColumns: Array<TableColumn<CompanyAssistantAttentionRow>> = [
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
    key: "type",
    header: "Typ",
    render: (row) => row.typeLabel,
  },
  {
    key: "status",
    header: "Sygnal",
    render: (row) => <StatusBadge status={row.statusTone}>{row.statusLabel}</StatusBadge>,
  },
  {
    key: "detail",
    header: "Kontekst",
    render: (row) => row.detail,
  },
];

type SettledSource = {
  key: CompanyAssistantSourceKey;
  result: PromiseSettledResult<unknown>;
};

function sourceTone(status: CompanyAssistantSourceState["status"]): "ok" | "warning" | "danger" | "info" | "neutral" {
  if (status === "ready") {
    return "ok";
  }
  if (status === "error") {
    return "warning";
  }
  return "neutral";
}

function buildSourcePayload(sources: SettledSource[]) {
  const payload: Record<string, unknown> = {};
  const sourceStates: CompanyAssistantSourceState[] = [];

  for (const source of sources) {
    if (source.result.status === "fulfilled") {
      sourceStates.push(sourceReady(source.key));
      if (source.key === "dashboard") {
        payload.dashboard = source.result.value;
      }
      if (source.key === "documents") {
        payload.documents = source.result.value;
      }
      if (source.key === "workItems") {
        payload.workItems = source.result.value;
      }
      if (source.key === "invoices") {
        payload.invoiceInbox = source.result.value;
      }
      continue;
    }

    sourceStates.push(sourceError(source.key, source.result.reason));
  }

  return {
    ...payload,
    sourceStates,
  };
}

export function AssistantCompanyPage() {
  const [snapshot, setSnapshot] = useState<CompanyAssistantSnapshot | null>(null);
  const [status, setStatus] = useState<CompanyAssistantStatus>("idle");
  const [errorState, setErrorState] = useState<CompanyAssistantErrorState | null>(null);
  const { selectedOrganizationId, selectedOrganization, status: organizationStatus } = useActiveOrganization();

  const loadContext = useCallback(async () => {
    if (organizationStatus === "loading") {
      setStatus("loading");
      setErrorState(null);
      return;
    }

    if (!canUseCompanyAssistantOrganizationScope(selectedOrganizationId)) {
      setStatus("ready");
      setErrorState(null);
      setSnapshot(null);
      return;
    }

    setStatus("loading");
    setErrorState(null);

    try {
      const organizationQuery = withActiveOrganizationQuery(selectedOrganizationId);
      const results = await Promise.allSettled([
        api.dashboard(organizationQuery),
        api.knowledgeDocuments(organizationQuery),
        api.workItems(withActiveOrganizationQuery(selectedOrganizationId, { limit: 50, only_open: 1 })),
        api.invoiceVerificationInbox(organizationQuery),
      ]);

      const settledSources: SettledSource[] = [
        { key: "dashboard", result: results[0] },
        { key: "documents", result: results[1] },
        { key: "workItems", result: results[2] },
        { key: "invoices", result: results[3] },
      ];

      const firstRejectedSource = settledSources.find(
        (source): source is { key: CompanyAssistantSourceKey; result: PromiseRejectedResult } => source.result.status === "rejected",
      );

      if (settledSources.every((source) => source.result.status === "rejected") && firstRejectedSource) {
        throw firstRejectedSource.result.reason;
      }

      setSnapshot(readCompanyAssistantSnapshot(buildSourcePayload(settledSources)));
      setStatus("ready");
    } catch (error) {
      setErrorState(getCompanyAssistantErrorState(error));
      setSnapshot(null);
      setStatus(getCompanyAssistantErrorState(error).status);
    }
  }, [organizationStatus, selectedOrganizationId]);

  useEffect(() => {
    void loadContext();
  }, [loadContext]);

  const organizationMissing =
    organizationStatus === "ready" && !canUseCompanyAssistantOrganizationScope(selectedOrganizationId);
  const kpis = useMemo(() => (snapshot ? buildCompanyAssistantKpis(snapshot) : null), [snapshot]);
  const knowledgeRows = useMemo(() => (snapshot ? buildCompanyAssistantKnowledgeRows(snapshot) : []), [snapshot]);
  const attentionRows = useMemo(() => (snapshot ? buildCompanyAssistantAttentionRows(snapshot) : []), [snapshot]);
  const sourceStates = snapshot?.sourceStates ?? [];
  const hasData = hasCompanyAssistantData(status, snapshot);
  const readyWithoutData = !organizationMissing && isCompanyAssistantEmpty(status, snapshot);

  return (
    <div className="module-page assistant-company-page">
      <PageHeader
        badgeTone={status === "ready" ? "success" : status === "error" ? "warning" : "info"}
        description="Read-only fundament asystenta firmowego dla wiedzy, spraw i kontekstu organizacji. Prawdziwy agent AI bedzie osobnym etapem."
        eyebrow={status === "ready" ? "Dane live" : "Asystent Firmowy"}
        title="Asystent Firmowy"
        actions={
          <Button disabled={status === "loading"} icon={<RefreshCw size={15} />} onClick={loadContext} size="sm" variant="secondary">
            Odswiez
          </Button>
        }
      />

      {status === "loading" ? <LoadingState /> : null}
      {errorState ? <ErrorState description={errorState.description} title={errorState.title} /> : null}
      {organizationMissing ? (
        <EmptyState
          description={COMPANY_ASSISTANT_ORGANIZATION_REQUIRED_DESCRIPTION}
          title={COMPANY_ASSISTANT_ORGANIZATION_REQUIRED_TITLE}
        />
      ) : null}
      {readyWithoutData ? (
        <EmptyState
          description={`Zrodla odpowiedzialy, ale nie ma jeszcze dokumentow, spraw, alertow ani faktur do pokazania dla organizacji ${selectedOrganization?.name ?? selectedOrganizationId}.`}
          title="Brak kontekstu organizacji do pokazania"
        />
      ) : null}

      {hasData && kpis ? (
        <>
          <section className="module-kpi-row" aria-label="Podsumowanie Asystenta Firmowego">
            <Card className="module-metric">
              <span className="module-metric__label">Dokumenty wiedzy</span>
              <strong>{kpis.knowledgeDocuments}</strong>
              <span>{kpis.readyKnowledgeDocuments} gotowych do uzycia w przyszlym asystencie.</span>
            </Card>
            <Card className="module-metric">
              <span className="module-metric__label">Sprawy otwarte</span>
              <strong>{kpis.openWorkItems}</strong>
              <span>Read-only podglad kolejki pracy organizacji.</span>
            </Card>
            <Card className="module-metric">
              <span className="module-metric__label">Faktury do uwagi</span>
              <strong>{kpis.invoicesToReview}</strong>
              <span>Pobrane z inboxu weryfikacji faktur.</span>
            </Card>
            <Card className="module-metric">
              <span className="module-metric__label">Sygnaly decyzyjne</span>
              <strong>{kpis.decisionSignals}</strong>
              <span>Dokumenty, faktury i alerty wymagajace uwagi.</span>
            </Card>
          </section>

          <Card
            description={`Aktywny kontekst: ${selectedOrganization?.name ?? selectedOrganizationId}. Kazde zrodlo jest pobierane z organization_id, a bledy czesciowe nie udaja pelnego sukcesu.`}
            title="Kontekst organizacji"
          >
            <div className="module-kpi-row">
              {sourceStates.map((source) => (
                <Card className="module-metric" key={source.key}>
                  <span className="module-metric__label">
                    <ShieldCheck aria-hidden="true" size={14} /> {source.label}
                  </span>
                  <strong>
                    <StatusBadge status={sourceTone(source.status)}>
                      {source.status === "ready" ? "Dane live" : source.status === "error" ? "Problem" : "Pominiete"}
                    </StatusBadge>
                  </strong>
                  <span>{source.endpoint}</span>
                </Card>
              ))}
            </div>
          </Card>

          <Card
            description="Najswiezsze dokumenty i materialy, ktore moga pozniej stac sie baza odpowiedzi agenta. Ten widok niczego nie indeksuje ani nie generuje."
            title="Zrodla wiedzy"
          >
            <Table
              columns={knowledgeColumns}
              data={knowledgeRows}
              emptyMessage="Ta organizacja nie ma jeszcze dokumentow wiedzy do pokazania."
              getRowKey={(row) => row.id}
            />
          </Card>

          <Card
            description="Operacyjne sygnaly z work items, dashboardu i faktur. To nadal podglad read-only, bez automatyzacji i bez akcji zapisu."
            title="Sprawy do uwagi"
          >
            <Table
              columns={attentionColumns}
              data={attentionRows}
              emptyMessage="Nie ma spraw, alertow ani faktur wymagajacych uwagi."
              getRowKey={(row) => row.id}
            />
          </Card>

          <Card
            description="Ten ekran celowo nie jest chatem i nie wysyla promptow. Pokazuje fundament danych, na ktorym dopiero pozniej mozna bezpiecznie budowac agenta."
            title="Agent AI zaplanowany jako kolejny etap"
          >
            <div className="module-kpi-row">
              <Card className="module-metric">
                <span className="module-metric__label">
                  <Bot aria-hidden="true" size={14} /> Agent AI
                </span>
                <strong>{COMPANY_ASSISTANT_AI_AGENT_ENABLED ? "Aktywny" : "Nieaktywny"}</strong>
                <span>Brak chatu, generowania odpowiedzi i wysylania promptow.</span>
              </Card>
              <Card className="module-metric">
                <span className="module-metric__label">Tryb ekranu</span>
                <strong>{COMPANY_ASSISTANT_READ_ONLY ? "Read-only" : "Akcje wlaczone"}</strong>
                <span>Brak uploadu, edycji dokumentow, zmian faktur i tworzenia zadan.</span>
              </Card>
              <Card className="module-metric">
                <span className="module-metric__label">Automatyzacje</span>
                <strong>Nieaktywne</strong>
                <span>Brak Telegram, Slack, e-mail, harmonogramow i workflow z UI.</span>
              </Card>
            </div>
          </Card>
        </>
      ) : null}
    </div>
  );
}
