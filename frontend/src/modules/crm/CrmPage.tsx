"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Building2, RefreshCw, UsersRound } from "lucide-react";

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
  CRM_CONTRACTORS_ENDPOINT,
  CRM_ORGANIZATION_REQUIRED_DESCRIPTION,
  CRM_ORGANIZATION_REQUIRED_TITLE,
  CRM_PIPELINE_ENABLED,
  CRM_READ_ONLY,
  buildContractorRows,
  buildCrmKpis,
  canUseCrmOrganizationScope,
  getCrmErrorState,
  hasCrmData,
  isCrmEmpty,
  readContractors,
  type ContractorRecord,
  type ContractorViewRow,
  type CrmErrorState,
  type CrmStatus,
} from "./crmModel";

const columns: Array<TableColumn<ContractorViewRow>> = [
  {
    key: "name",
    header: "Kontrahent",
    render: (row) => (
      <Link className="module-row-title module-row-link" href={`/crm/${row.id}`}>
        <Building2 aria-hidden="true" size={16} />
        {row.nameLabel}
      </Link>
    ),
  },
  {
    key: "status",
    header: "Status",
    render: (row) => <StatusBadge status={row.statusTone}>{row.statusLabel}</StatusBadge>,
  },
  {
    key: "nip",
    header: "NIP",
    render: (row) => row.nipLabel,
  },
  {
    key: "contact",
    header: "Kontakt",
    render: (row) => row.contactLabel,
  },
  {
    key: "invoices",
    header: "Faktury",
    align: "right",
    render: (row) => row.invoiceCountLabel,
  },
  {
    key: "lastInvoice",
    header: "Ostatnia faktura",
    render: (row) => row.lastInvoiceLabel,
  },
  {
    key: "organization",
    header: "Organizacja",
    render: (row) => row.organizationLabel,
  },
  {
    key: "updated",
    header: "Aktualizacja",
    align: "right",
    render: (row) => row.updatedLabel,
  },
];

export function CrmPage() {
  const { selectedOrganizationId, selectedOrganization, status: organizationStatus } = useActiveOrganization();
  const [contractors, setContractors] = useState<ContractorRecord[] | null>(null);
  const [status, setStatus] = useState<CrmStatus>("idle");
  const [errorState, setErrorState] = useState<CrmErrorState | null>(null);

  const loadContractors = useCallback(async () => {
    if (organizationStatus === "loading") {
      setStatus("loading");
      setErrorState(null);
      return;
    }

    if (!canUseCrmOrganizationScope(selectedOrganizationId)) {
      setContractors([]);
      setErrorState(null);
      setStatus("ready");
      return;
    }

    setStatus("loading");
    setErrorState(null);

    try {
      const payload = await api.contractors(withActiveOrganizationQuery(selectedOrganizationId));
      const nextContractors = readContractors(payload);
      setContractors(nextContractors);
      setStatus("ready");
    } catch (error) {
      const nextErrorState = getCrmErrorState(error);
      setErrorState(nextErrorState);
      setContractors(null);
      setStatus(nextErrorState.status);
    }
  }, [organizationStatus, selectedOrganizationId]);

  useEffect(() => {
    void loadContractors();
  }, [loadContractors]);

  const rows = useMemo(() => buildContractorRows(contractors ?? []), [contractors]);
  const kpis = useMemo(() => buildCrmKpis(contractors ?? []), [contractors]);
  const hasData = hasCrmData(status, contractors);
  const organizationMissing = organizationStatus === "ready" && !canUseCrmOrganizationScope(selectedOrganizationId);
  const readyWithoutData = !organizationMissing && isCrmEmpty(status, contractors);

  return (
    <div className="module-page crm-page">
      <PageHeader
        badgeTone={status === "ready" ? "success" : status === "error" ? "warning" : "info"}
        description="Read-only katalog kontrahentow z istniejacego API. Ten krok nie buduje pipeline CRM sprzedazy ani edycji CRM."
        eyebrow={status === "ready" ? "Dane live" : "CRM"}
        title="CRM"
        actions={
          <Button disabled={status === "loading"} icon={<RefreshCw size={15} />} onClick={loadContractors} size="sm" variant="secondary">
            Odswiez
          </Button>
        }
      />

      {status === "loading" ? <LoadingState /> : null}
      {errorState ? <ErrorState description={errorState.description} title={errorState.title} /> : null}
      {organizationMissing ? (
        <EmptyState description={CRM_ORGANIZATION_REQUIRED_DESCRIPTION} title={CRM_ORGANIZATION_REQUIRED_TITLE} />
      ) : null}
      {readyWithoutData ? (
        <EmptyState
          description={`Backend odpowiedzial poprawnie, ale nie zwrocil kontrahentow dla organizacji ${selectedOrganization?.name ?? selectedOrganizationId}.`}
          title="Brak kontrahentow w katalogu"
        />
      ) : null}

      {hasData ? (
        <>
          <section className="module-kpi-row" aria-label="Podsumowanie CRM">
            <Card className="module-metric">
              <span className="module-metric__label">Tryb ekranu</span>
              <strong>{CRM_READ_ONLY ? "Read-only" : "Akcje wlaczone"}</strong>
              <span>Bez tworzenia, edycji, importu i pipeline CRM sprzedazy.</span>
            </Card>
            <Card className="module-metric">
              <span className="module-metric__label">Kontrahenci</span>
              <strong>{kpis.total}</strong>
              <span>Pobrane z {CRM_CONTRACTORS_ENDPOINT}.</span>
            </Card>
            <Card className="module-metric">
              <span className="module-metric__label">Nowi / znani</span>
              <strong>
                {kpis.newCount}/{kpis.knownCount}
              </strong>
              <span>Nowi kontrahenci i rekordy znane z historii.</span>
            </Card>
            <Card className="module-metric">
              <span className="module-metric__label">Dane kontaktowe</span>
              <strong>{kpis.missingContactCount}</strong>
              <span>Rekordy bez e-maila i telefonu.</span>
            </Card>
          </section>

          <Card
            description="Lista pokazuje realne rekordy contractors. Szczegoly, historia kontaktow, notatki handlowe i edycja zostaja poza tym krokiem."
            title="Katalog kontrahentow"
          >
            <Table
              columns={columns}
              data={rows}
              emptyMessage="Backend nie zwrocil kontrahentow."
              getRowKey={(row) => row.id}
            />
          </Card>

          <Card
            description="Ten panel jest informacyjny. Nie uruchamia automatyzacji CRM ani zadnych zmian w danych."
            title="Zakres MVP CRM"
          >
            <div className="module-kpi-row">
              <Card className="module-metric">
                <span className="module-metric__label">
                  <UsersRound aria-hidden="true" size={14} /> Pipeline CRM
                </span>
                <strong>{CRM_PIPELINE_ENABLED ? "Aktywny" : "Nieaktywny"}</strong>
                <span>Brak lejka sprzedazy i etapow handlowych.</span>
              </Card>
              <Card className="module-metric">
                <span className="module-metric__label">Powiazane faktury</span>
                <strong>{kpis.linkedToInvoicesCount}</strong>
                <span>Kontrahenci z co najmniej jedna faktura.</span>
              </Card>
              <Card className="module-metric">
                <span className="module-metric__label">Akcje</span>
                <strong>Nieaktywne</strong>
                <span>Brak dodawania, edycji, usuwania i importu kontaktow.</span>
              </Card>
            </div>
          </Card>
        </>
      ) : null}
    </div>
  );
}
