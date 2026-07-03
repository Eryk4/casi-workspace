"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { RefreshCw, ReceiptText } from "lucide-react";

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
import { formatCount } from "@/lib/utils";
import type { InvoiceVerificationInbox, InvoiceVerificationItem } from "@/lib/types";
import {
  INVOICES_ORGANIZATION_REQUIRED_DESCRIPTION,
  INVOICES_ORGANIZATION_REQUIRED_TITLE,
  canUseInvoicesOrganizationScope,
  flattenInboxItems,
  formatInvoiceAmount,
  getInvoiceDetailHref,
  getInboxSections,
  getInvoicesErrorState,
  hasInvoiceInboxData,
  invoiceStatusTone,
  isInvoiceInboxEmpty,
  type InvoicesErrorState,
  type InvoicesStatus,
} from "./invoicesModel";

const columns: Array<TableColumn<InvoiceVerificationItem>> = [
  {
    key: "invoice",
    header: "Faktura",
    render: (row) => {
      const detailHref = getInvoiceDetailHref(row.invoice_id);
      const label = row.invoice_number || `#${row.invoice_id}`;

      return (
      <span className="module-row-title">
        <ReceiptText aria-hidden="true" size={16} />
        {detailHref ? <Link href={detailHref}>{label}</Link> : label}
      </span>
      );
    },
  },
  {
    key: "issuer",
    header: "Wystawca",
    render: (row) => row.issuer_name || "Brak nazwy",
  },
  {
    key: "source",
    header: "Zrodlo",
    render: (row) => row.source || "Nieznane",
  },
  {
    key: "status",
    header: "Status",
    render: (row) => <StatusBadge status={invoiceStatusTone(row)}>{row.status || "Do decyzji"}</StatusBadge>,
  },
  {
    key: "amount",
    header: "Kwota",
    align: "right",
    render: (row) => formatInvoiceAmount(row),
  },
];

export function InvoicesPage() {
  const { selectedOrganizationId, selectedOrganization, status: organizationStatus } = useActiveOrganization();
  const [inbox, setInbox] = useState<InvoiceVerificationInbox | null>(null);
  const [status, setStatus] = useState<InvoicesStatus>("idle");
  const [errorState, setErrorState] = useState<InvoicesErrorState | null>(null);

  const loadInbox = useCallback(async () => {
    if (organizationStatus === "loading") {
      setStatus("loading");
      setErrorState(null);
      return;
    }

    if (!canUseInvoicesOrganizationScope(selectedOrganizationId)) {
      setInbox(null);
      setErrorState(null);
      setStatus("ready");
      return;
    }

    setStatus("loading");
    setErrorState(null);

    try {
      const nextInbox = await api.invoiceVerificationInbox(withActiveOrganizationQuery(selectedOrganizationId));
      setInbox(nextInbox);
      setStatus("ready");
    } catch (error) {
      const nextErrorState = getInvoicesErrorState(error);
      setErrorState(nextErrorState);
      setInbox(null);
      setStatus(nextErrorState.status);
    }
  }, [organizationStatus, selectedOrganizationId]);

  useEffect(() => {
    void loadInbox();
  }, [loadInbox]);

  const items = useMemo(() => flattenInboxItems(inbox), [inbox]);
  const sections = useMemo(() => getInboxSections(inbox), [inbox]);
  const hasInboxData = hasInvoiceInboxData(status, inbox);
  const organizationMissing = organizationStatus === "ready" && !canUseInvoicesOrganizationScope(selectedOrganizationId);
  const readyWithoutData = !organizationMissing && isInvoiceInboxEmpty(status, inbox);

  return (
    <div className="dashboard-page">
      <PageHeader
        badgeTone={status === "ready" ? "success" : status === "error" ? "warning" : "info"}
        description="Pierwszy podglad realnego inboxu faktur wymagajacych weryfikacji, bez akcji mutujacych dane."
        eyebrow={status === "ready" ? "Dane live" : "Faktury"}
        title="Faktury"
        actions={
          <Button disabled={status === "loading"} icon={<RefreshCw size={15} />} onClick={loadInbox} size="sm" variant="secondary">
            Odswiez
          </Button>
        }
      />

      {status === "loading" ? <LoadingState /> : null}
      {errorState ? <ErrorState description={errorState.description} title={errorState.title} /> : null}
      {organizationMissing ? (
        <EmptyState
          description={INVOICES_ORGANIZATION_REQUIRED_DESCRIPTION}
          title={INVOICES_ORGANIZATION_REQUIRED_TITLE}
        />
      ) : null}
      {readyWithoutData ? (
        <EmptyState
          description={`Backend odpowiedzial poprawnie, ale inbox weryfikacji nie zawiera aktualnie faktur do decyzji dla organizacji ${selectedOrganization?.name ?? selectedOrganizationId}.`}
          title="Brak faktur do weryfikacji"
        />
      ) : null}

      {hasInboxData ? (
        <>
          <section className="module-kpi-row" aria-label="Sekcje inboxu faktur">
            {sections.map((section) => (
              <Card className="module-kpi-card" key={section.action_key || section.title}>
                <span>{section.title}</span>
                <strong>{formatCount(section.count)}</strong>
                <p>{section.description || "Sekcja inboxu weryfikacji faktur."}</p>
              </Card>
            ))}
          </section>

          <Card title="Inbox weryfikacji">
            <Table
              columns={columns}
              data={items}
              emptyMessage="Backend nie zwrocil faktur wymagajacych weryfikacji."
              getRowKey={(row) => String(row.invoice_id)}
            />
          </Card>
        </>
      ) : null}
    </div>
  );
}
