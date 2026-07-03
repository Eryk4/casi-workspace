"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { ClipboardList, RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Dropdown } from "@/components/ui/Dropdown";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Table, type TableColumn } from "@/components/ui/Table";
import { useActiveOrganization } from "@/context/ActiveOrganizationContext";
import { api } from "@/lib/api";
import { withActiveOrganizationQuery } from "@/context/organizationContextModel";
import type { WorkItemRecord } from "./workItemsModel";
import {
  DEFAULT_WORK_ITEM_CLOSE_REASON,
  WORK_ITEM_ASSIGN_TO_SELF_ACTION_ENABLED,
  WORK_ITEM_CLOSE_ACTION_ENABLED,
  WORK_ITEM_SNOOZE_ACTION_ENABLED,
  WORK_ITEM_SNOOZE_PRESETS,
  WORK_ITEMS_ORGANIZATION_REQUIRED_DESCRIPTION,
  WORK_ITEMS_ORGANIZATION_REQUIRED_TITLE,
  WORK_ITEMS_READ_ONLY,
  applyAssignedWorkItem,
  applyClosedWorkItem,
  applySnoozedWorkItem,
  buildAssignWorkItemToSelfPayload,
  buildWorkItemActionMenuItems,
  buildWorkItemRows,
  buildCloseWorkItemPayload,
  buildSnoozeWorkItemPayload,
  canAssignCurrentUserInOrganization,
  canAssignWorkItemToSelf,
  canCloseWorkItem,
  canSnoozeWorkItem,
  canUseWorkItemOrganizationScope,
  getWorkItemsErrorState,
  hasWorkItemsData,
  isWorkItemsEmpty,
  readCurrentUserId,
  readCurrentUserOrganizationId,
  readWorkItems,
  type WorkItemSnoozePreset,
  type WorkItemViewRow,
  type WorkItemsErrorState,
  type WorkItemsStatus,
} from "./workItemsModel";

export function WorkItemsPage() {
  const { selectedOrganizationId, selectedOrganization, status: organizationStatus } = useActiveOrganization();
  const [items, setItems] = useState<WorkItemRecord[] | null>(null);
  const [status, setStatus] = useState<WorkItemsStatus>("idle");
  const [errorState, setErrorState] = useState<WorkItemsErrorState | null>(null);
  const [closingItemId, setClosingItemId] = useState<number | null>(null);
  const [assigningItemId, setAssigningItemId] = useState<number | null>(null);
  const [snoozingItemId, setSnoozingItemId] = useState<number | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [currentUserId, setCurrentUserId] = useState<number | null>(null);
  const [currentUserOrganizationId, setCurrentUserOrganizationId] = useState<string | null>(null);

  const loadWorkItems = useCallback(async () => {
    if (organizationStatus === "loading") {
      setStatus("loading");
      setErrorState(null);
      return;
    }

    if (!canUseWorkItemOrganizationScope(selectedOrganizationId)) {
      setItems([]);
      setCurrentUserId(null);
      setCurrentUserOrganizationId(null);
      setErrorState(null);
      setActionError(null);
      setStatus("ready");
      return;
    }

    setStatus("loading");
    setErrorState(null);

    try {
      const [workItemsPayload, sessionPayload] = await Promise.all([
        api.workItems(withActiveOrganizationQuery(selectedOrganizationId, { limit: 100, only_open: 1 })),
        api.currentSession(),
      ]);
      const nextItems = readWorkItems(workItemsPayload);
      setItems(nextItems);
      setCurrentUserId(readCurrentUserId(sessionPayload));
      setCurrentUserOrganizationId(readCurrentUserOrganizationId(sessionPayload));
      setStatus("ready");
      setActionError(null);
    } catch (error) {
      const nextErrorState = getWorkItemsErrorState(error);
      setErrorState(nextErrorState);
      setItems(null);
      setStatus(nextErrorState.status);
    }
  }, [organizationStatus, selectedOrganizationId]);

  useEffect(() => {
    void loadWorkItems();
  }, [loadWorkItems]);

  const closeWorkItem = useCallback(async (row: WorkItemViewRow) => {
    if (!canUseWorkItemOrganizationScope(selectedOrganizationId) || !WORK_ITEM_CLOSE_ACTION_ENABLED || !canCloseWorkItem(row)) {
      return;
    }

    setClosingItemId(row.workItemId);
    setActionError(null);

    try {
      const payload = await api.closeWorkItem(
        row.workItemId,
        buildCloseWorkItemPayload(DEFAULT_WORK_ITEM_CLOSE_REASON).reason,
        selectedOrganizationId,
      );
      const [updated] = readWorkItems([payload]);
      setItems((currentItems) => (currentItems ? applyClosedWorkItem(currentItems, updated) : currentItems));
    } catch (error) {
      const nextError = getWorkItemsErrorState(error);
      setActionError(nextError.description);
    } finally {
      setClosingItemId(null);
    }
  }, [selectedOrganizationId]);

  const assignWorkItemToSelf = useCallback(async (row: WorkItemViewRow) => {
    if (
      !canUseWorkItemOrganizationScope(selectedOrganizationId) ||
      !canAssignCurrentUserInOrganization(currentUserOrganizationId, selectedOrganizationId) ||
      !WORK_ITEM_ASSIGN_TO_SELF_ACTION_ENABLED ||
      !canAssignWorkItemToSelf(row, currentUserId) ||
      !currentUserId
    ) {
      return;
    }

    setAssigningItemId(row.workItemId);
    setActionError(null);

    try {
      const payload = buildAssignWorkItemToSelfPayload(currentUserId);
      const response = await api.assignWorkItem(row.workItemId, payload.assigned_user_id, selectedOrganizationId);
      const [updated] = readWorkItems([response]);
      setItems((currentItems) => (currentItems ? applyAssignedWorkItem(currentItems, updated, currentUserId) : currentItems));
    } catch (error) {
      const nextError = getWorkItemsErrorState(error);
      setActionError(nextError.description);
    } finally {
      setAssigningItemId(null);
    }
  }, [currentUserId, currentUserOrganizationId, selectedOrganizationId]);

  const snoozeWorkItem = useCallback(async (row: WorkItemViewRow, preset: WorkItemSnoozePreset) => {
    if (!canUseWorkItemOrganizationScope(selectedOrganizationId) || !WORK_ITEM_SNOOZE_ACTION_ENABLED || !canSnoozeWorkItem(row)) {
      return;
    }

    setSnoozingItemId(row.workItemId);
    setActionError(null);

    try {
      const payload = buildSnoozeWorkItemPayload(preset);
      const response = await api.snoozeWorkItem(row.workItemId, payload.mode, selectedOrganizationId);
      const [updated] = readWorkItems([response]);
      setItems((currentItems) => (currentItems ? applySnoozedWorkItem(currentItems, updated) : currentItems));
    } catch (error) {
      const nextError = getWorkItemsErrorState(error);
      setActionError(nextError.description);
    } finally {
      setSnoozingItemId(null);
    }
  }, [selectedOrganizationId]);

  const triggerWorkItemAction = useCallback((row: WorkItemViewRow, actionKey: string) => {
    if (actionKey === "snooze-1h") {
      void snoozeWorkItem(row, WORK_ITEM_SNOOZE_PRESETS[0]);
      return;
    }
    if (actionKey === "snooze-1d") {
      void snoozeWorkItem(row, WORK_ITEM_SNOOZE_PRESETS[1]);
      return;
    }
    if (actionKey === "assign-self") {
      void assignWorkItemToSelf(row);
      return;
    }
    if (actionKey === "close") {
      void closeWorkItem(row);
    }
  }, [assignWorkItemToSelf, closeWorkItem, snoozeWorkItem]);

  const rows = useMemo(() => buildWorkItemRows(items ?? []), [items]);
  const columns = useMemo<Array<TableColumn<WorkItemViewRow>>>(
    () => [
      {
        key: "title",
        header: "Sprawa",
        render: (row) => (
          <div className="work-item-title-cell">
            <span className="module-row-title">
              <ClipboardList aria-hidden="true" size={16} />
              {row.title}
            </span>
            <span className="work-item-description">{row.description}</span>
            <span className="work-item-meta">
              {row.sourceLabel} / {row.organizationLabel}
            </span>
          </div>
        ),
      },
      {
        key: "state",
        header: "Stan",
        render: (row) => (
          <div className="work-item-state-stack">
            <StatusBadge status={row.statusTone}>{row.statusLabel}</StatusBadge>
            <StatusBadge status={row.priorityTone}>{row.priorityLabel}</StatusBadge>
            <span className="work-item-meta">Score {row.scoreLabel}</span>
          </div>
        ),
      },
      {
        key: "owner",
        header: "Wlasciciel",
        render: (row) => (
          <div className="work-item-owner-cell">
            <span className="work-item-owner">{row.ownerLabel}</span>
            {currentUserId && row.assignedUserId === currentUserId ? <span className="work-item-chip">Przypisane do mnie</span> : null}
          </div>
        ),
      },
      {
        key: "timing",
        header: "Terminy",
        render: (row) => (
          <div className="work-item-timing-cell">
            <span>{row.dueLabel}</span>
            <span className={row.priorityTone === "danger" || row.priorityTone === "warning" ? "work-item-sla is-risk" : "work-item-sla"}>
              SLA: {row.slaLabel}
            </span>
          </div>
        ),
      },
      {
        key: "actions",
        header: "Akcja",
        align: "right",
        render: (row) => (
          <Dropdown
            items={buildWorkItemActionMenuItems(row, currentUserId).map((item) => ({
              danger: item.danger,
              disabled:
                item.disabled ||
                (item.key === "assign-self" && !canAssignCurrentUserInOrganization(currentUserOrganizationId, selectedOrganizationId)) ||
                (item.key.startsWith("snooze") && snoozingItemId === row.workItemId) ||
                (item.key === "assign-self" && assigningItemId === row.workItemId) ||
                (item.key === "close" && closingItemId === row.workItemId),
              label:
                item.key.startsWith("snooze") && snoozingItemId === row.workItemId
                  ? "Odkladanie"
                  : item.key === "assign-self" && assigningItemId === row.workItemId
                    ? "Przypisywanie"
                    : item.key === "close" && closingItemId === row.workItemId
                      ? "Zamykanie"
                      : item.label,
              onSelect: () => triggerWorkItemAction(row, item.key),
            }))}
            label="Akcje"
          />
        ),
      },
    ],
    [assigningItemId, closingItemId, currentUserId, currentUserOrganizationId, selectedOrganizationId, snoozingItemId, triggerWorkItemAction],
  );
  const hasData = hasWorkItemsData(status, items);
  const organizationMissing = organizationStatus === "ready" && !canUseWorkItemOrganizationScope(selectedOrganizationId);
  const readyWithoutData = !organizationMissing && isWorkItemsEmpty(status, items);

  return (
    <div className="module-page work-items-page">
      <PageHeader
        badgeTone={status === "ready" ? "success" : status === "error" ? "warning" : "info"}
        description="Minimalny podglad operacyjnych pozycji pracy z /api/work-items. Ten ekran jest teraz read-only MVP."
        eyebrow={status === "ready" ? "Dane live" : "Work Items"}
        title="Work Items"
        actions={
          <Button disabled={status === "loading"} icon={<RefreshCw size={15} />} onClick={loadWorkItems} size="sm" variant="secondary">
            Odswiez
          </Button>
        }
      />

      {status === "loading" ? <LoadingState /> : null}
      {errorState ? <ErrorState description={errorState.description} title={errorState.title} /> : null}
      {organizationMissing ? (
        <EmptyState
          description={WORK_ITEMS_ORGANIZATION_REQUIRED_DESCRIPTION}
          title={WORK_ITEMS_ORGANIZATION_REQUIRED_TITLE}
        />
      ) : null}
      {readyWithoutData ? (
        <EmptyState
          description={`Backend odpowiedzial poprawnie, ale nie zwrocil otwartych pozycji pracy dla organizacji ${selectedOrganization?.name ?? selectedOrganizationId}.`}
          title="Brak otwartych work items"
        />
      ) : null}

      {hasData ? (
        <>
          <section className="module-kpi-row" aria-label="Podsumowanie work items">
            <Card className="module-metric">
              <span className="module-metric__label">Tryb ekranu</span>
              <strong>{WORK_ITEMS_READ_ONLY ? "Read-only" : "Male akcje"}</strong>
              <span>Odkladanie, przypisanie do siebie i zamykanie bez tworzenia, edycji, bulk actions i drag and drop.</span>
            </Card>
            <Card className="module-metric">
              <span className="module-metric__label">Otwarte sprawy</span>
              <strong>{rows.length}</strong>
              <span>Pobrane z /api/work-items?only_open=1.</span>
            </Card>
            <Card className="module-metric">
              <span className="module-metric__label">SLA / ryzyko</span>
              <strong>{rows.filter((row) => row.priorityTone === "danger" || row.priorityTone === "warning").length}</strong>
              <span>Pozycje z priorytetem wysokim, krytycznym albo po terminie.</span>
            </Card>
          </section>

          <Card
            description="Lista jest minimalnym widokiem operacyjnym. Dostepne akcje pojedynczego wiersza sa zebrane w menu."
            title="Lista work items"
          >
            {actionError ? (
              <Card
                description={actionError}
                title="Nie udalo sie wykonac akcji"
              />
            ) : null}
            <Table
              columns={columns}
              data={rows}
              emptyMessage="Backend nie zwrocil work items."
              getRowKey={(row) => row.id}
            />
          </Card>
        </>
      ) : null}
    </div>
  );
}
