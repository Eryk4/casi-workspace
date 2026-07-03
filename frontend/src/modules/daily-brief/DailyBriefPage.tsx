"use client";

import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { AlertTriangle, CheckCircle2, FileText, ListChecks, RefreshCw, ShieldCheck } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useActiveOrganization } from "@/context/ActiveOrganizationContext";
import { withActiveOrganizationQuery } from "@/context/organizationContextModel";
import { api } from "@/lib/api";
import { formatCount } from "@/lib/utils";
import { readTaskFocusSnapshot } from "../assistant-ceo/bossAssistantModel";
import { readBillingBalances } from "../billing/billingModel";
import { readContractors } from "../crm/crmModel";
import { readKnowledgeDocuments } from "../documents/documentsModel";
import { readWorkItems } from "../work-items/workItemsModel";

import {
  DAILY_BRIEF_ORGANIZATION_REQUIRED_DESCRIPTION,
  DAILY_BRIEF_ORGANIZATION_REQUIRED_TITLE,
  DAILY_BRIEF_REFRESH_LABEL,
  DAILY_BRIEF_SECTION_LABELS,
  buildDailyBrief,
  canUseDailyBriefOrganizationScope,
  isDailyBriefEmpty,
  sourceState,
  type DailyBriefItem,
  type DailyBriefSnapshot,
  type DailyBriefSourceKey,
  type DailyBriefSourceState,
} from "./dailyBriefModel";

type DailyBriefStatus = "idle" | "loading" | "ready" | "error";

type LoadedSource<T> = {
  data: T | null;
  state: DailyBriefSourceState;
};

export function DailyBriefPage() {
  const { selectedOrganizationId, selectedOrganization, status: organizationStatus } = useActiveOrganization();
  const [snapshot, setSnapshot] = useState<DailyBriefSnapshot | null>(null);
  const [status, setStatus] = useState<DailyBriefStatus>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const loadDailyBrief = useCallback(async () => {
    if (organizationStatus === "loading") {
      setStatus("loading");
      setErrorMessage(null);
      return;
    }

    if (!canUseDailyBriefOrganizationScope(selectedOrganizationId)) {
      setSnapshot(null);
      setErrorMessage(null);
      setStatus("ready");
      return;
    }

    setStatus("loading");
    setErrorMessage(null);

    const query = withActiveOrganizationQuery(selectedOrganizationId);
    const openWorkItemsQuery = withActiveOrganizationQuery(selectedOrganizationId, { limit: 100, only_open: 1 });

    try {
      const [dashboard, taskFocus, workItems, invoiceInbox, billingBalances, contractors, documents] = await Promise.all([
        loadSource("dashboard", () => api.dashboard(query), (payload) => payload),
        loadSource("taskFocus", () => api.taskFocus(query), readTaskFocusSnapshot),
        loadSource("workItems", () => api.workItems(openWorkItemsQuery), readWorkItems),
        loadSource("invoiceInbox", () => api.invoiceVerificationInbox(query), (payload) => payload),
        loadSource("billingBalances", () => api.ledgerBalances(query), readBillingBalances),
        loadSource("contractors", () => api.contractors(query), readContractors),
        loadSource("documents", () => api.knowledgeDocuments(query), readKnowledgeDocuments),
      ]);

      setSnapshot({
        dashboard: dashboard.data,
        taskFocus: taskFocus.data,
        workItems: workItems.data ?? [],
        invoiceInbox: invoiceInbox.data,
        billingBalances: billingBalances.data ?? [],
        contractors: contractors.data ?? [],
        documents: documents.data ?? [],
        sourceStates: [
          dashboard.state,
          taskFocus.state,
          workItems.state,
          invoiceInbox.state,
          billingBalances.state,
          contractors.state,
          documents.state,
        ],
      });
      setStatus("ready");
    } catch (error) {
      setSnapshot(null);
      setStatus("error");
      setErrorMessage(error instanceof Error ? error.message : "Nie udało się zbudować Pulpitu dnia.");
    }
  }, [organizationStatus, selectedOrganizationId]);

  useEffect(() => {
    void loadDailyBrief();
  }, [loadDailyBrief]);

  const brief = useMemo(() => (snapshot ? buildDailyBrief(snapshot) : null), [snapshot]);
  const organizationMissing = organizationStatus === "ready" && !canUseDailyBriefOrganizationScope(selectedOrganizationId);
  const empty = isDailyBriefEmpty(status, snapshot);

  return (
    <div className="module-page daily-brief-page">
      <PageHeader
        badgeTone="info"
        description="Poranny przegląd najważniejszych spraw z zadań, faktur, CRM, dokumentów i rozliczeń. Widok jest tylko do odczytu."
        eyebrow="Pulpit dnia"
        title="Co dzisiaj wymaga mojej uwagi?"
        actions={
          <Button disabled={status === "loading"} icon={<RefreshCw size={15} />} onClick={loadDailyBrief} size="sm" variant="secondary">
            {DAILY_BRIEF_REFRESH_LABEL}
          </Button>
        }
      />

      {status === "loading" ? <LoadingState /> : null}
      {status === "error" && errorMessage ? <ErrorState description={errorMessage} title="Nie udało się zbudować Pulpitu dnia" /> : null}
      {organizationMissing ? (
        <EmptyState description={DAILY_BRIEF_ORGANIZATION_REQUIRED_DESCRIPTION} title={DAILY_BRIEF_ORGANIZATION_REQUIRED_TITLE} />
      ) : null}
      {empty ? (
        <EmptyState
          description={`Nie ma dziś spraw wymagających pilnej uwagi dla organizacji ${selectedOrganization?.name ?? selectedOrganizationId}.`}
          title="Spokojny poranek"
        />
      ) : null}

      {brief && snapshot && !organizationMissing && !empty ? (
        <>
          <section className="daily-brief-kpis" aria-label="Podsumowanie Pulpitu dnia">
            <DailyBriefKpi icon={<AlertTriangle size={17} />} label="Krytyczne" value={brief.kpis.criticalCount} />
            <DailyBriefKpi icon={<ListChecks size={17} />} label="Pilne sprawy" value={brief.kpis.urgentCount} />
            <DailyBriefKpi icon={<FileText size={17} />} label="Faktury i finanse" value={brief.kpis.invoiceCount} />
            <DailyBriefKpi icon={<ShieldCheck size={17} />} label="Można odłożyć" value={brief.kpis.laterCount} />
          </section>

          <section className="daily-brief-layout" aria-label="Sekcje Pulpitu dnia">
            <div className="daily-brief-layout__main">
              <DailyBriefSection
                description="Krótka mieszanka spraw, które najlepiej opisują dzisiejszy rytm firmy."
                emptyText="Brak najważniejszych sygnałów."
                items={brief.sections.top}
                title={DAILY_BRIEF_SECTION_LABELS.top}
              />
              <DailyBriefSection
                description="Zadania, sprawy operacyjne i terminy, które najłatwiej zgubić w codziennej pracy."
                emptyText="Brak pilnych spraw operacyjnych."
                items={brief.sections.urgent}
                title={DAILY_BRIEF_SECTION_LABELS.urgent}
              />
              <DailyBriefSection
                description="Faktury, salda płatników i finansowe sygnały wymagające spojrzenia."
                emptyText="Brak pilnych sygnałów finansowych."
                items={brief.sections.invoicesFinance}
                title={DAILY_BRIEF_SECTION_LABELS.invoicesFinance}
              />
            </div>

            <aside className="daily-brief-layout__side" aria-label="Kontekst organizacji">
              <Card title="Kontekst organizacji" description={selectedOrganization?.name ?? `Organizacja ${selectedOrganizationId}`}>
                <div className="daily-brief-source-list">
                  {snapshot.sourceStates.map((source) => (
                    <div className="daily-brief-source" key={source.key}>
                      <span>{source.label}</span>
                      <StatusBadge status={source.status === "ready" ? "ok" : source.status === "empty" ? "neutral" : "warning"}>
                        {source.status === "ready" ? "OK" : source.status === "empty" ? "Brak spraw" : "Błąd"}
                      </StatusBadge>
                    </div>
                  ))}
                </div>
              </Card>
              <DailyBriefSection
                compact
                description="Nowi kontrahenci, braki kontaktowe i relacje do sprawdzenia."
                emptyText="Brak pilnych sygnałów CRM."
                items={brief.sections.contractors}
                title={DAILY_BRIEF_SECTION_LABELS.contractors}
              />
              <DailyBriefSection
                compact
                description="Dokumenty w przetwarzaniu, z błędem albo wymagające decyzji."
                emptyText="Brak pilnych dokumentów."
                items={brief.sections.documents}
                title={DAILY_BRIEF_SECTION_LABELS.documents}
              />
              <DailyBriefSection
                compact
                description="Sprawy widoczne w systemie, ale bez pilnej reakcji."
                emptyText="Dziś nie ma oczywistych spraw do odłożenia. To zwykle znaczy, że lista jest krótka albo wymaga normalnej uwagi."
                items={brief.sections.later}
                title={DAILY_BRIEF_SECTION_LABELS.later}
              />
            </aside>
          </section>
        </>
      ) : null}
    </div>
  );
}

async function loadSource<TPayload, TData>(
  key: DailyBriefSourceKey,
  loader: () => Promise<TPayload>,
  reader: (payload: TPayload) => TData,
): Promise<LoadedSource<TData>> {
  try {
    const payload = await loader();
    const data = reader(payload);
    const empty = Array.isArray(data) ? data.length === 0 : data === null;
    return { data, state: sourceState(key, empty ? "empty" : "ready") };
  } catch (error) {
    return {
      data: null,
      state: sourceState(key, "error", error instanceof Error ? error.message : "Błąd pobierania danych"),
    };
  }
}

function DailyBriefKpi({ icon, label, value }: { icon: ReactNode; label: string; value: number }) {
  return (
    <Card className="daily-brief-kpi">
      <span className="daily-brief-kpi__icon">{icon}</span>
      <span>{label}</span>
      <strong>{formatCount(value)}</strong>
    </Card>
  );
}

function DailyBriefSection({
  compact = false,
  description,
  emptyText,
  items,
  title,
}: {
  compact?: boolean;
  description: string;
  emptyText: string;
  items: DailyBriefItem[];
  title: string;
}) {
  return (
    <Card className={compact ? "daily-brief-section daily-brief-section--compact" : "daily-brief-section"} description={description} title={title}>
      {items.length ? (
        <div className="daily-brief-list">
          {items.map((item) => (
            <Link className="daily-brief-item" href={item.href} key={item.id}>
              <span className={`daily-brief-item__tone daily-brief-item__tone--${item.tone}`} aria-hidden="true" />
              <span className="daily-brief-item__copy">
                <span className="daily-brief-item__category">{item.source}</span>
                <strong>{item.title}</strong>
                <span>{item.description}</span>
              </span>
              <span className="daily-brief-item__meta">{item.meta}</span>
            </Link>
          ))}
        </div>
      ) : (
        <p className="daily-brief-empty">{emptyText}</p>
      )}
    </Card>
  );
}
