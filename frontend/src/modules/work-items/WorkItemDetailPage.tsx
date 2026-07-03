"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { ArrowLeft, ClipboardList, RefreshCw, ShieldCheck } from "lucide-react";

import { Badge } from "@/components/ui/Badge";
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

import {
  WORK_ITEM_DETAIL_ORGANIZATION_REQUIRED_DESCRIPTION,
  WORK_ITEM_DETAIL_ORGANIZATION_REQUIRED_TITLE,
  WORK_ITEM_DETAIL_READ_ONLY,
  buildWorkItemDetailView,
  canRenderWorkItemDetail,
  canUseWorkItemDetailOrganizationScope,
  getWorkItemDetailErrorState,
  isWorkItemDetailEmpty,
  readWorkItemDetail,
  type WorkItemContextLink,
  type WorkItemDetailErrorState,
  type WorkItemDetailStatus,
  type WorkItemHistoryEvent,
} from "./workItemDetailModel";

function RelatedLinkList({
  emptyMessage,
  items,
}: {
  emptyMessage: string;
  items: WorkItemContextLink[];
}) {
  if (!items.length) {
    return (
      <div className="work-item-context-empty">
        <strong>Brak powiązań</strong>
        <span>{emptyMessage}</span>
      </div>
    );
  }

  return (
    <div className="work-item-context-list">
      {items.map((item) => (
        <Link className="work-item-context-link" href={item.href} key={item.id}>
          <span>{item.title}</span>
          <strong>{item.description}</strong>
          <small>{item.meta}</small>
        </Link>
      ))}
    </div>
  );
}

function HistoryList({ events }: { events: WorkItemHistoryEvent[] }) {
  if (!events.length) {
    return (
      <div className="work-item-context-empty">
        <strong>Brak historii</strong>
        <span>Backend nie zwrócił jeszcze bezpiecznych zdarzeń dla tej sprawy.</span>
      </div>
    );
  }

  return (
    <ol className="module-activity-list">
      {events.map((event) => (
        <li className="module-activity-list__item" key={event.id}>
          <span>{event.dateLabel}</span>
          <strong>{event.title}</strong>
          <p>{event.description}</p>
          <p>Autor: {event.actorLabel}</p>
        </li>
      ))}
    </ol>
  );
}

export function WorkItemDetailPage({ workItemId: requestedWorkItemId }: { workItemId: number }) {
  const { selectedOrganizationId, status: organizationStatus } = useActiveOrganization();
  const [detail, setDetail] = useState<ReturnType<typeof readWorkItemDetail> | null>(null);
  const [status, setStatus] = useState<WorkItemDetailStatus>("idle");
  const [errorState, setErrorState] = useState<WorkItemDetailErrorState | null>(null);

  const loadDetail = useCallback(async () => {
    if (organizationStatus === "loading") {
      setStatus("loading");
      setErrorState(null);
      return;
    }

    if (!canUseWorkItemDetailOrganizationScope(selectedOrganizationId)) {
      setDetail(null);
      setErrorState(null);
      setStatus("ready");
      return;
    }

    setStatus("loading");
    setErrorState(null);

    try {
      const payload = await api.workItemDetail(
        requestedWorkItemId,
        withActiveOrganizationQuery(selectedOrganizationId),
      );
      setDetail(readWorkItemDetail(payload, requestedWorkItemId));
      setStatus("ready");
    } catch (error) {
      const nextErrorState = getWorkItemDetailErrorState(error);
      setDetail(null);
      setErrorState(nextErrorState);
      setStatus(nextErrorState.status);
    }
  }, [organizationStatus, requestedWorkItemId, selectedOrganizationId]);

  useEffect(() => {
    void loadDetail();
  }, [loadDetail]);

  const view = useMemo(() => (detail ? buildWorkItemDetailView(detail) : null), [detail]);
  const canShowDetail = canRenderWorkItemDetail(status, detail);
  const organizationMissing =
    organizationStatus === "ready" && !canUseWorkItemDetailOrganizationScope(selectedOrganizationId);
  const readyWithoutDetail = !organizationMissing && isWorkItemDetailEmpty(status, detail);

  return (
    <div className="module-page work-item-detail-page">
      <PageHeader
        badgeTone={status === "ready" ? "success" : status === "error" ? "danger" : "info"}
        description="Centrum sprawy pokazuje, o co chodzi, dlaczego sprawa jest ważna i z czym jest powiązana. Widok jest tylko do odczytu."
        eyebrow="Karta sprawy"
        title={view?.title ?? `Sprawa ${requestedWorkItemId}`}
        actions={
          <>
            <Link className="ui-button ui-button--secondary ui-button--sm" href="/work-items">
              <ArrowLeft aria-hidden="true" size={15} />
              <span>Wróć</span>
            </Link>
            <Button disabled={status === "loading"} icon={<RefreshCw size={15} />} onClick={loadDetail} size="sm">
              Odśwież
            </Button>
          </>
        }
      />

      {status === "loading" ? <LoadingState /> : null}
      {errorState ? <ErrorState description={errorState.description} title={errorState.title} /> : null}
      {organizationMissing ? (
        <EmptyState
          description={WORK_ITEM_DETAIL_ORGANIZATION_REQUIRED_DESCRIPTION}
          title={WORK_ITEM_DETAIL_ORGANIZATION_REQUIRED_TITLE}
        />
      ) : null}
      {readyWithoutDetail ? (
        <EmptyState description="Nie znaleziono sprawy w wybranej organizacji." title="Brak sprawy" />
      ) : null}

      {canShowDetail && view ? (
        <section className="invoice-detail-grid work-item-detail-grid">
          <div className="invoice-detail-grid__main">
            <Card
              action={<StatusBadge status={view.row.priorityTone}>{view.row.priorityLabel}</StatusBadge>}
              description={view.attentionReason}
              title="Najważniejsze informacje"
            >
              <div className="invoice-fact-grid">
                {view.facts.map((fact) => (
                  <article className="invoice-fact" key={fact.label}>
                    <span>{fact.label}</span>
                    <strong>{fact.value}</strong>
                  </article>
                ))}
              </div>
            </Card>

            <Card
              action={<StatusBadge status={view.row.statusTone}>{view.row.statusLabel}</StatusBadge>}
              title="Opis sprawy"
            >
              <div className="module-readiness">
                <div className="module-readiness__item">
                  <ClipboardList aria-hidden="true" size={17} />
                  <div>
                    <strong>{view.row.title}</strong>
                    <span>{view.row.description}</span>
                  </div>
                </div>
                <div className="module-readiness__item">
                  <ShieldCheck aria-hidden="true" size={17} />
                  <div>
                    <strong>Widok tylko do odczytu</strong>
                    <span>
                      Karta nie dodaje akcji typu przypisz, odłóż, zamknij, edytuj ani usuń. Służy do zrozumienia
                      kontekstu sprawy.
                    </span>
                  </div>
                </div>
              </div>
            </Card>

            <Card title="Powiązana faktura">
              <RelatedLinkList
                emptyMessage="Ta sprawa nie ma w odpowiedzi API powiązanej faktury."
                items={view.relatedInvoices}
              />
            </Card>

            <Card title="Powiązany kontrahent">
              <RelatedLinkList
                emptyMessage="Ta sprawa nie ma w odpowiedzi API powiązanego kontrahenta."
                items={view.relatedContractors}
              />
            </Card>

            <Card title="Dokumenty">
              <RelatedLinkList
                emptyMessage="Ta sprawa nie ma w odpowiedzi API powiązanych dokumentów."
                items={view.relatedDocuments}
              />
            </Card>

            <Card title="Zadania i inne sprawy">
              <RelatedLinkList
                emptyMessage="Nie znaleziono dodatkowych zadań ani spraw powiązanych z tym rekordem."
                items={view.relatedTasks}
              />
            </Card>
          </div>

          <aside className="module-activity-panel" aria-label="Historia sprawy">
            <Card
              action={<Badge tone={WORK_ITEM_DETAIL_READ_ONLY ? "info" : "warning"}>Read-only</Badge>}
              title="Historia systemowa"
            >
              <HistoryList events={view.history} />
            </Card>
          </aside>
        </section>
      ) : null}
    </div>
  );
}
