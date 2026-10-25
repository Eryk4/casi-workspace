"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Plus, RefreshCw, Settings2 } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useActiveOrganization } from "@/context/ActiveOrganizationContext";
import { api, withOrganizationQuery } from "@/lib/api";

import {
  automationBusyMessage,
  automationTriggerLabel,
  hasAutomationManage,
  readAutomationCatalog,
  readAutomationRules,
  type AutomationCatalog,
  type AutomationRuleSummary,
} from "./automationManagementModel";

type PendingLifecycleAction = { rule: AutomationRuleSummary; nextActive: boolean } | null;

function dateTime(value: string | null): string {
  return value ? new Date(value).toLocaleString("pl-PL") : "Jeszcze nie uruchomiono";
}

export function AutomationRulesPage() {
  const router = useRouter();
  const { capabilities, selectedOrganizationId, status: organizationStatus } = useActiveOrganization();
  const canManage = hasAutomationManage(capabilities);
  const [rules, setRules] = useState<AutomationRuleSummary[] | null>(null);
  const [catalog, setCatalog] = useState<AutomationCatalog | null>(null);
  const [loadedOrganizationId, setLoadedOrganizationId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [pendingAction, setPendingAction] = useState<PendingLifecycleAction>(null);
  const [mutationLoading, setMutationLoading] = useState(false);
  const [mutationError, setMutationError] = useState<string | null>(null);
  const rulesRequestVersion = useRef(0);
  const catalogRequestVersion = useRef(0);
  const mutationVersion = useRef(0);
  const mutationInFlight = useRef(false);
  const organizationRef = useRef(selectedOrganizationId);
  organizationRef.current = selectedOrganizationId;

  const loadRules = useCallback(async () => {
    const organizationId = selectedOrganizationId;
    const version = ++rulesRequestVersion.current;
    setRules(null);
    setLoadedOrganizationId(null);
    setError(false);
    if (organizationStatus !== "ready" || !organizationId || !canManage) return;
    setLoading(true);
    try {
      const nextRules = readAutomationRules(
        await api.automationRules(withOrganizationQuery(organizationId, { include_inactive: 1 })),
      );
      if (version !== rulesRequestVersion.current || organizationId !== organizationRef.current) return;
      setRules(nextRules);
      setLoadedOrganizationId(organizationId);
    } catch {
      if (version === rulesRequestVersion.current && organizationId === organizationRef.current) setError(true);
    } finally {
      if (version === rulesRequestVersion.current) setLoading(false);
    }
  }, [canManage, organizationStatus, selectedOrganizationId]);

  const loadCatalogLabels = useCallback(async () => {
    const organizationId = selectedOrganizationId;
    const version = ++catalogRequestVersion.current;
    setCatalog(null);
    if (organizationStatus !== "ready" || !organizationId || !canManage) return;
    try {
      const nextCatalog = readAutomationCatalog(await api.automationCatalog());
      if (version !== catalogRequestVersion.current || organizationId !== organizationRef.current) return;
      setCatalog(nextCatalog);
    } catch {
      if (version === catalogRequestVersion.current && organizationId === organizationRef.current) setCatalog(null);
    }
  }, [canManage, organizationStatus, selectedOrganizationId]);

  useEffect(() => {
    rulesRequestVersion.current += 1;
    catalogRequestVersion.current += 1;
    mutationVersion.current += 1;
    mutationInFlight.current = false;
    setRules(null);
    setCatalog(null);
    setLoadedOrganizationId(null);
    setPendingAction(null);
    setMutationError(null);
    setMessage(null);
    if (typeof window !== "undefined") {
      const query = new URLSearchParams(window.location.search);
      if (query.get("created") === "1") setMessage("Reguła została utworzona i jest wyłączona. Włącz ją, gdy będziesz gotowy.");
      if (query.get("organization_changed") === "1") setMessage("Organizacja została zmieniona. Formularz nowej reguły został wyczyszczony.");
    }
    if (organizationStatus === "ready" && !canManage) {
      router.replace("/automatyzacje");
      return;
    }
    void loadRules();
    void loadCatalogLabels();
  }, [canManage, loadCatalogLabels, loadRules, organizationStatus, router, selectedOrganizationId]);

  async function confirmLifecycleAction() {
    if (!pendingAction || mutationInFlight.current) return;
    const organizationId = selectedOrganizationId;
    const version = ++mutationVersion.current;
    if (!organizationId || !canManage) return;
    mutationInFlight.current = true;
    setMutationLoading(true);
    setMutationError(null);
    try {
      await api.updateAutomationRule(pendingAction.rule.id, { is_active: pendingAction.nextActive }, organizationId);
      if (version !== mutationVersion.current || organizationId !== organizationRef.current) return;
      setPendingAction(null);
      setMessage(pendingAction.nextActive ? "Reguła została włączona." : "Reguła została wyłączona.");
      await loadRules();
    } catch (nextError) {
      if (version !== mutationVersion.current || organizationId !== organizationRef.current) return;
      setMutationError(
        automationBusyMessage(nextError) ??
          (pendingAction.nextActive ? "Nie udało się włączyć reguły." : "Nie udało się wyłączyć reguły."),
      );
    } finally {
      if (version === mutationVersion.current) {
        mutationInFlight.current = false;
        setMutationLoading(false);
      }
    }
  }

  if (organizationStatus !== "ready") {
    return <div className="loading-state" role="status">Ładowanie uprawnień do zarządzania automatyzacjami...</div>;
  }
  if (!canManage) {
    return <section className="empty-state"><h2>Brak dostępu</h2><p>Nie masz uprawnienia do zarządzania regułami automatyzacji.</p></section>;
  }
  if (!selectedOrganizationId) {
    return <section className="empty-state"><h2>Wybierz organizację</h2><p>Reguły są zarządzane osobno dla każdej organizacji.</p></section>;
  }
  const visibleRules = loadedOrganizationId === selectedOrganizationId ? rules : null;

  return (
    <section className="automation-management" aria-labelledby="automation-rules-title">
      <PageHeader
        actions={
          <div className="automation-management__header-actions">
            <Link className="ui-button ui-button--secondary ui-button--md" href="/automatyzacje/automation_engine">Monitoring automatyzacji</Link>
            <Link className="ui-button ui-button--primary ui-button--md" href="/automatyzacje/reguly/nowa"><Plus aria-hidden="true" size={16} /> Utwórz regułę</Link>
          </div>
        }
        description="Twórz reguły, które reagują na zdarzenia w CASI i wykonują określone działania."
        eyebrow="Automatyzacje"
        title="Reguły automatyzacji"
      />

      <div className="automation-management__runtime-note" role="note">
        <Settings2 aria-hidden="true" size={18} />
        <span>Automatyczne wykonywanie reguł nie jest jeszcze uruchomione w środowisku produkcyjnym.</span>
      </div>
      {message ? <p className="module-success" role="status">{message}</p> : null}

      <div className="automation-management__toolbar">
        <p>Reguły są wyświetlane dla aktualnie wybranej organizacji.</p>
        <Button disabled={loading} icon={<RefreshCw aria-hidden="true" size={16} />} onClick={() => void loadRules()}>
          {loading ? "Odświeżanie..." : "Odśwież"}
        </Button>
      </div>

      {loading ? <div className="loading-state" role="status">Ładowanie reguł automatyzacji...</div> : null}
      {!loading && error ? (
        <div className="error-state" role="alert">
          <strong>Nie udało się pobrać reguł automatyzacji.</strong>
          <Button onClick={() => void loadRules()}>Spróbuj ponownie</Button>
        </div>
      ) : null}
      {!loading && !error && visibleRules?.length === 0 ? (
        <div className="empty-state">
          <h3>Nie masz jeszcze żadnych reguł automatyzacji.</h3>
          <p>Nowe reguły są zapisywane jako wyłączone. Włączasz je osobno po sprawdzeniu konfiguracji.</p>
          <Link className="ui-button ui-button--primary ui-button--md" href="/automatyzacje/reguly/nowa">Utwórz pierwszą regułę</Link>
        </div>
      ) : null}

      {!loading && !error && visibleRules && visibleRules.length > 0 ? (
        <div className="automation-rules-grid">
          {visibleRules.map((rule) => {
            const trigger = catalog?.triggers.find((item) => item.key === rule.triggerKey);
            return (
              <article className="automation-rule-card" key={rule.id}>
                <div className="automation-rule-card__heading">
                  <div><span className="eyebrow">{automationTriggerLabel(trigger)}</span><h2>{rule.name}</h2></div>
                  <StatusBadge status={rule.active ? "ok" : "neutral"}>{rule.active ? "Aktywna" : "Wyłączona"}</StatusBadge>
                </div>
                {rule.description ? <p className="automation-rule-card__description">{rule.description}</p> : null}
                <dl>
                  <div><dt>Ostatnie wykonanie</dt><dd>{dateTime(rule.lastRunAt)}</dd></div>
                  <div><dt>Wykonania</dt><dd>{rule.executionCount}</dd></div>
                  {rule.updatedAt ? <div><dt>Ostatnia zmiana</dt><dd>{new Date(rule.updatedAt).toLocaleString("pl-PL")}</dd></div> : null}
                </dl>
                <Button
                  disabled={mutationLoading}
                  onClick={() => { setMutationError(null); setPendingAction({ rule, nextActive: !rule.active }); }}
                  variant={rule.active ? "secondary" : "primary"}
                >
                  {rule.active ? "Wyłącz" : "Włącz"}
                </Button>
              </article>
            );
          })}
        </div>
      ) : null}

      <Modal
        footer={pendingAction ? <><Button disabled={mutationLoading} onClick={() => setPendingAction(null)}>Anuluj</Button><Button autoFocus disabled={mutationLoading} onClick={() => void confirmLifecycleAction()} variant={pendingAction.nextActive ? "primary" : "danger"}>{mutationLoading ? "Zapisywanie..." : pendingAction.nextActive ? "Włącz regułę" : "Wyłącz regułę"}</Button></> : null}
        onClose={() => { if (!mutationLoading) setPendingAction(null); }}
        open={Boolean(pendingAction)}
        title={pendingAction?.nextActive ? "Włączyć regułę?" : "Wyłączyć regułę?"}
      >
        <p>{pendingAction?.nextActive
          ? "Po włączeniu reguła zacznie reagować na nowe zdarzenia od tego momentu. Wcześniejsze zdarzenia nie zostaną uruchomione ponownie."
          : "Po wyłączeniu reguła nie rozpocznie kolejnych działań. Jeśli jedno działanie już trwa, może się jeszcze zakończyć."}</p>
        {mutationError ? <p className="module-error" role="alert">{mutationError}</p> : null}
      </Modal>
    </section>
  );
}
