import {
  ArrowRight,
  CheckCircle2,
  ChevronRight,
  FileText,
  Filter,
  Layers3,
  MessageSquare,
  MoreHorizontal,
  RefreshCw,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Table, type TableColumn } from "@/components/ui/Table";
import type { ModuleMetric } from "@/lib/types";

export type ModuleBlueprintRow = {
  area: string;
  status: string;
  owner: string;
  nextStep: string;
  source?: string;
};

type WorkTableRow = ModuleBlueprintRow & {
  source: string;
  phase: string;
};

export type ModuleBlueprintPageProps = {
  eyebrow: string;
  title: string;
  description: string;
  metrics: ModuleMetric[];
  rows: ModuleBlueprintRow[];
  emptyTitle: string;
  emptyDescription: string;
  badgeTone?: "neutral" | "success" | "warning" | "danger" | "info";
};

const columns: Array<TableColumn<WorkTableRow>> = [
  {
    key: "area",
    header: "Dokument / obszar",
    render: (row) => (
      <span className="module-row-title">
        <FileText aria-hidden="true" size={16} />
        {row.area}
      </span>
    ),
  },
  {
    key: "type",
    header: "Typ",
    render: (row) => row.owner,
  },
  {
    key: "status",
    header: "Status",
    render: (row) => (
      <StatusBadge status={row.status === "Do migracji" ? "warning" : "info"}>{row.status}</StatusBadge>
    ),
  },
  {
    key: "source",
    header: "Zrodlo",
    render: (row) => row.source,
  },
  {
    key: "phase",
    header: "Etap",
    render: (row) => row.phase,
  },
  {
    key: "actions",
    header: "",
    align: "right",
    render: () => (
      <button className="module-row-action" type="button" aria-label="Wiecej opcji">
        <MoreHorizontal aria-hidden="true" size={16} />
      </button>
    ),
  },
];

const metricIcons = [FileText, MessageSquare, ShieldCheck, RefreshCw];

function inferSource(row: ModuleBlueprintRow): string {
  const endpoint = row.nextStep.match(/\/api\/[A-Za-z0-9/_-]+/)?.[0];
  return row.source ?? endpoint ?? "Kontrakt modulu";
}

function buildTableRows(rows: ModuleBlueprintRow[]): WorkTableRow[] {
  return rows.map((row, index) => ({
    ...row,
    source: inferSource(row),
    phase: `Etap ${index + 1}`,
  }));
}

export function ModuleBlueprintPage({
  badgeTone = "neutral",
  description,
  emptyDescription,
  emptyTitle,
  eyebrow,
  metrics,
  rows,
  title,
}: ModuleBlueprintPageProps) {
  const tableRows = buildTableRows(rows);
  const visibleMetrics = [
    ...metrics,
    {
      label: "Tryb MVP",
      value: "On-demand",
      hint: "bez kosztownego stalego pollingu",
    },
  ].slice(0, 4);

  return (
    <div className="module-page">
      <PageHeader
        badgeTone={badgeTone}
        description={description}
        eyebrow={eyebrow}
        title={title}
        actions={
          <Button icon={<ArrowRight size={15} />} size="sm" variant="secondary">
            Plan migracji
          </Button>
        }
      />

      <section className="module-readiness" aria-label="Stan przygotowania modulu">
        <div className="module-readiness__item">
          <CheckCircle2 aria-hidden="true" size={17} />
          <div>
            <strong>Wspolny AppShell</strong>
            <span>Modul dziala w produkcyjnym layoucie i centralnej nawigacji.</span>
          </div>
        </div>
        <div className="module-readiness__item">
          <Layers3 aria-hidden="true" size={17} />
          <div>
            <strong>Kontrakt API zachowany</strong>
            <span>Widok opisuje docelowe endpointy bez zmiany logiki backendu.</span>
          </div>
        </div>
        <div className="module-readiness__item">
          <RefreshCw aria-hidden="true" size={17} />
          <div>
            <strong>Automatyzacje etapowane</strong>
            <span>Domyslnie projektujemy akcje reczne lub konfigurowalna intensywnosc.</span>
          </div>
        </div>
      </section>

      <section className="module-kpi-row" aria-label="Metryki modulu">
        {visibleMetrics.map((metric, index) => {
          const MetricIcon = metricIcons[index] ?? FileText;

          return (
            <Card className="module-metric" key={metric.label}>
              <span className="module-metric__icon">
                <MetricIcon aria-hidden="true" size={18} />
              </span>
              <span className="module-metric__label">{metric.label}</span>
              <strong>{metric.value}</strong>
              <span>{metric.hint}</span>
            </Card>
          );
        })}
      </section>

      <section className="module-workspace">
        <div className="module-workspace__main">
          <Card
            action={
              <div className="module-card-actions">
                <Button icon={<Filter size={14} />} size="sm" variant="secondary">
                  Filtry
                </Button>
                <button className="module-row-action" type="button" aria-label="Wiecej opcji">
                  <MoreHorizontal aria-hidden="true" size={16} />
                </button>
              </div>
            }
            className="module-data-card"
            title="Baza robocza"
          >
            <Table columns={columns} data={tableRows} getRowKey={(row) => row.area} />
            <footer className="module-table-footer">
              <span>Pokaz 1-{tableRows.length} z {tableRows.length}</span>
              <div className="module-pagination">
                <button type="button" aria-label="Poprzednia strona">
                  {"<"}
                </button>
                <strong>1</strong>
                <button type="button" aria-label="Nastepna strona">
                  {">"}
                </button>
              </div>
            </footer>
          </Card>

          <Card
            action={
              <Button icon={<Sparkles size={14} />} size="sm" variant="primary">
                Zapytaj
              </Button>
            }
            className="module-query-card"
            title="Asystent wiedzy - zapytaj"
          >
            <Input
              aria-label="Zadaj pytanie"
              placeholder="Zadaj pytanie dotyczace procedur, dokumentow lub polityk..."
            />
            <div className="module-question-list" aria-label="Ostatnie pytania">
              {tableRows.slice(0, 3).map((row, index) => (
                <button className="module-question-list__item" key={row.area} type="button">
                  <span>{row.nextStep}</span>
                  <small>{index + 1} zrodlo</small>
                  <ChevronRight aria-hidden="true" size={15} />
                </button>
              ))}
            </div>
          </Card>
        </div>

        {rows.length ? (
          <aside className="module-activity-panel" aria-label="Aktywnosc modulu">
            <Card className="module-activity-card" description={emptyDescription} title={emptyTitle}>
              <ol className="module-activity-list">
                {rows.map((row) => (
                  <li className="module-activity-list__item" key={row.area}>
                    <span>{row.status}</span>
                    <strong>{row.area}</strong>
                    <p>{row.nextStep}</p>
                  </li>
                ))}
              </ol>
            </Card>
            <Card className="module-quick-actions" title="Szybkie akcje">
              {["Dodaj wpis", "Uruchom recznie", "Popros o dostep", "Nowe pytanie", "Eksport raportu"].map(
                (action) => (
                  <button className="module-quick-action" key={action} type="button">
                    <span>{action}</span>
                    <ChevronRight aria-hidden="true" size={15} />
                  </button>
                ),
              )}
            </Card>
          </aside>
        ) : null}
      </section>
    </div>
  );
}

export const ModulePlaceholder = ModuleBlueprintPage;
