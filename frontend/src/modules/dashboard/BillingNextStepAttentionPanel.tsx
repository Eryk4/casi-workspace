"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AlertTriangle, CalendarDays, RefreshCw } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useActiveOrganization } from "@/context/ActiveOrganizationContext";
import { withActiveOrganizationQuery } from "@/context/organizationContextModel";
import { api } from "@/lib/api";

import {
  buildBillingAttentionView,
  getBillingAttentionErrorState,
  readBillingAttentionResponse,
  type BillingAttentionErrorState,
  type BillingAttentionResponse,
  type BillingAttentionStatus,
} from "./billingAttentionModel";

export function BillingNextStepAttentionPanel() {
  const { selectedOrganizationId, status: organizationStatus } = useActiveOrganization();
  const [response, setResponse] = useState<BillingAttentionResponse | null>(null);
  const [status, setStatus] = useState<BillingAttentionStatus>("idle");
  const [errorState, setErrorState] = useState<BillingAttentionErrorState | null>(null);
  const requestVersion = useRef(0);

  const loadAttention = useCallback(async () => {
    const currentRequest = requestVersion.current + 1;
    requestVersion.current = currentRequest;
    setResponse(null);
    setErrorState(null);

    if (organizationStatus === "loading") {
      setStatus("loading");
      return;
    }
    if (!selectedOrganizationId) {
      setStatus("ready");
      return;
    }

    setStatus("loading");
    try {
      const payload = await api.billingNextStepAttention(withActiveOrganizationQuery(selectedOrganizationId));
      const nextResponse = readBillingAttentionResponse(payload);
      if (requestVersion.current !== currentRequest || String(nextResponse.organizationId) !== String(selectedOrganizationId)) {
        return;
      }
      setResponse(nextResponse);
      setStatus("ready");
    } catch (error) {
      if (requestVersion.current !== currentRequest) {
        return;
      }
      const nextError = getBillingAttentionErrorState(error);
      setErrorState(nextError);
      setStatus(nextError.status);
    }
  }, [organizationStatus, selectedOrganizationId]);

  useEffect(() => {
    void loadAttention();
    return () => {
      requestVersion.current += 1;
    };
  }, [loadAttention]);

  const view = useMemo(
    () => (response && String(response.organizationId) === String(selectedOrganizationId) ? buildBillingAttentionView(response) : null),
    [response, selectedOrganizationId],
  );

  if (!selectedOrganizationId && organizationStatus !== "loading") {
    return null;
  }

  return (
    <Card
      className="dashboard-attention-card"
      data-billing-attention
      description="Wewnętrzny, tylko do odczytu podgląd aktywnych kroków zaległych i przypadających na dzisiaj."
      title="Rozliczenia — wymagają uwagi"
      action={
        <Link className="ui-button ui-button--secondary ui-button--sm" href="/rozliczenia/kroki">
          Pokaż wszystkie
        </Link>
      }
    >
      {status === "loading" ? <LoadingState /> : null}
      {errorState ? (
        <ErrorState
          action={
            <Button icon={<RefreshCw aria-hidden="true" size={15} />} onClick={loadAttention} size="sm" variant="secondary">
              Spróbuj ponownie
            </Button>
          }
          description={errorState.description}
          title={errorState.title}
        />
      ) : null}
      {status === "ready" && view?.attentionCount === 0 ? (
        <EmptyState
          description={`Na ${view.asOfDate} nie ma zaległych ani dzisiejszych kroków. Przyszłe kroki i kroki bez daty nie są tu pokazywane.`}
          icon={<CalendarDays aria-hidden="true" size={18} />}
          title="Na dziś nic nie wymaga uwagi"
        />
      ) : null}
      {status === "ready" && view && view.attentionCount > 0 ? (
        <>
          <div className="dashboard-attention-summary" aria-label="Podsumowanie kroków wymagających uwagi">
            <span>Zaległe <strong>{view.overdueCount}</strong></span>
            <span>Dzisiaj <strong>{view.dueTodayCount}</strong></span>
            <span>Łącznie <strong>{view.attentionCount}</strong></span>
          </div>
          <ol className="dashboard-attention-list">
            {view.preview.map((candidate) => (
              <li data-attention-event-id={candidate.eventId} key={candidate.eventId}>
                <AlertTriangle aria-hidden="true" size={16} />
                <div>
                  <div className="dashboard-attention-list__title">
                    <strong>{candidate.title}</strong>
                    <StatusBadge status={candidate.reasonCode === "overdue" ? "danger" : "warning"}>
                      {candidate.reasonCode === "overdue" ? "Zaległe" : "Dzisiaj"}
                    </StatusBadge>
                  </div>
                  <p>{candidate.plannedFor} · {candidate.targetLabel}</p>
                  {candidate.targetHref ? <Link href={candidate.targetHref}>Otwórz cel</Link> : <span>Cel historyczny — brak bezpiecznego linku</span>}
                </div>
              </li>
            ))}
          </ol>
        </>
      ) : null}
    </Card>
  );
}
