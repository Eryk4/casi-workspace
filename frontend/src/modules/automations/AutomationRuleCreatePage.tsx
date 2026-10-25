"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, Plus, Trash2 } from "lucide-react";
import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/Button";
import { PageHeader } from "@/components/ui/PageHeader";
import { useActiveOrganization } from "@/context/ActiveOrganizationContext";
import { api } from "@/lib/api";

import {
  automationActionFieldLabel,
  automationActionLabel,
  automationConditionLabel,
  automationOperatorLabel,
  automationTriggerLabel,
  conditionFieldsForTrigger,
  emptyAutomationRuleDraft,
  hasAutomationManage,
  isAutomationCatalogSupported,
  readAutomationCatalog,
  readAutomationValidationError,
  resetConditionsForTrigger,
  supportedManagementActions,
  validateAutomationRuleDraft,
  type AutomationCatalog,
  type AutomationRuleDraft,
} from "./automationManagementModel";

export function AutomationRuleCreatePage() {
  const router = useRouter();
  const { capabilities, selectedOrganizationId, status: organizationStatus } = useActiveOrganization();
  const canManage = hasAutomationManage(capabilities);
  const [catalog, setCatalog] = useState<AutomationCatalog | null>(null);
  const [draft, setDraft] = useState<AutomationRuleDraft>(emptyAutomationRuleDraft);
  const [loading, setLoading] = useState(false);
  const [catalogError, setCatalogError] = useState(false);
  const [unsupported, setUnsupported] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitError, setSubmitError] = useState<string | null>(null);
  const requestVersion = useRef(0);
  const mutationVersion = useRef(0);
  const submitInFlight = useRef(false);
  const initialOrganizationRef = useRef<string | null>(null);
  const organizationRef = useRef(selectedOrganizationId);
  organizationRef.current = selectedOrganizationId;

  const loadCatalog = useCallback(async () => {
    const organizationId = selectedOrganizationId;
    const version = ++requestVersion.current;
    setCatalog(null);
    setCatalogError(false);
    setUnsupported(false);
    if (organizationStatus !== "ready" || !organizationId || !canManage) return;
    setLoading(true);
    try {
      const nextCatalog = readAutomationCatalog(await api.automationCatalog());
      if (version !== requestVersion.current || organizationId !== organizationRef.current) return;
      if (!isAutomationCatalogSupported(nextCatalog)) {
        setUnsupported(true);
        return;
      }
      setCatalog(nextCatalog);
      const firstAction = supportedManagementActions(nextCatalog)[0];
      setDraft((current) => ({ ...current, actionKey: firstAction?.key ?? "", actionValues: {} }));
    } catch {
      if (version === requestVersion.current && organizationId === organizationRef.current) setCatalogError(true);
    } finally {
      if (version === requestVersion.current) setLoading(false);
    }
  }, [canManage, organizationStatus, selectedOrganizationId]);

  useEffect(() => {
    if (organizationStatus !== "ready") return;
    if (!canManage) {
      requestVersion.current += 1;
      mutationVersion.current += 1;
      submitInFlight.current = false;
      setDraft(emptyAutomationRuleDraft());
      router.replace("/automatyzacje");
      return;
    }
    if (!selectedOrganizationId) return;
    if (initialOrganizationRef.current === null) initialOrganizationRef.current = selectedOrganizationId;
    else if (initialOrganizationRef.current !== selectedOrganizationId) {
      requestVersion.current += 1;
      mutationVersion.current += 1;
      submitInFlight.current = false;
      setDraft(emptyAutomationRuleDraft());
      router.replace("/automatyzacje/reguly?organization_changed=1");
      return;
    }
    void loadCatalog();
  }, [canManage, loadCatalog, organizationStatus, router, selectedOrganizationId]);

  const trigger = catalog?.triggers.find((item) => item.key === draft.triggerKey);
  const availableConditionFields = catalog ? conditionFieldsForTrigger(catalog, draft.triggerKey) : [];
  const action = catalog ? supportedManagementActions(catalog).find((item) => item.key === draft.actionKey) : undefined;
  const organizationChanged = initialOrganizationRef.current !== null && initialOrganizationRef.current !== selectedOrganizationId;

  function addCondition() {
    if (!catalog || draft.conditions.length >= catalog.constraints.maxConditions) return;
    const field = availableConditionFields.find((item) => !draft.conditions.some((condition) => condition.fieldKey === item.key));
    if (!field) return;
    setDraft((current) => ({
      ...current,
      conditions: [...current.conditions, { fieldKey: field.key, operator: field.operators?.[0] ?? "", value: "" }],
    }));
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!catalog || submitInFlight.current) return;
    const nextValidation = validateAutomationRuleDraft(catalog, draft);
    setErrors(nextValidation.errors);
    setSubmitError(null);
    if (!nextValidation.payload) return;
    const organizationId = selectedOrganizationId;
    const version = ++mutationVersion.current;
    if (!organizationId || !canManage) return;
    submitInFlight.current = true;
    setSubmitting(true);
    try {
      await api.createAutomationRule(nextValidation.payload, organizationId);
      if (version !== mutationVersion.current || organizationId !== organizationRef.current) return;
      router.push("/automatyzacje/reguly?created=1");
    } catch (nextError) {
      if (version !== mutationVersion.current || organizationId !== organizationRef.current) return;
      const parsed = readAutomationValidationError(nextError);
      setSubmitError(parsed.message);
      if (parsed.field) setErrors((current) => ({ ...current, [parsed.field as string]: parsed.message }));
    } finally {
      if (version === mutationVersion.current) {
        submitInFlight.current = false;
        setSubmitting(false);
      }
    }
  }

  if (organizationStatus !== "ready" || loading) return <div className="loading-state" role="status">Ładowanie konfiguracji kreatora automatyzacji...</div>;
  if (!canManage) return <section className="empty-state"><h2>Brak dostępu</h2><p>Nie masz uprawnienia do tworzenia reguł automatyzacji.</p></section>;
  if (!selectedOrganizationId) return <section className="empty-state"><h2>Wybierz organizację</h2><p>Nowa reguła musi należeć do wybranej organizacji.</p></section>;
  if (organizationChanged) return <div className="loading-state" role="status">Czyszczenie formularza po zmianie organizacji...</div>;
  if (catalogError) return <div className="error-state" role="alert"><strong>Nie udało się wczytać konfiguracji kreatora automatyzacji.</strong><Button onClick={() => void loadCatalog()}>Spróbuj ponownie</Button></div>;
  if (unsupported) return <div className="error-state" role="alert"><strong>Ta konfiguracja automatyzacji nie jest obsługiwana przez tę wersję interfejsu.</strong></div>;
  if (!catalog) return null;

  return (
    <section className="automation-management automation-rule-create" aria-labelledby="automation-rule-create-title">
      <Link className="automation-management__back" href="/automatyzacje/reguly"><ArrowLeft aria-hidden="true" size={15} /> Wróć do reguł</Link>
      <PageHeader description="Określ, kiedy reguła ma zadziałać i co ma zrobić." eyebrow="Automatyzacje" title="Nowa reguła automatyzacji" />

      <ol className="automation-rule-steps" aria-label="Etapy konfiguracji reguły">
        {["Nazwa", "Gdy", "Jeśli", "Zrób", "Podsumowanie"].map((step, index) => <li key={step}><span>{index + 1}</span>{step}</li>)}
      </ol>

      <form className="automation-rule-form" onSubmit={submit}>
        <section className="automation-rule-form__section" aria-labelledby="rule-name-section">
          <div><span className="eyebrow">1. Nazwa</span><h2 id="rule-name-section">Nazwij regułę</h2></div>
          <label className="module-field" htmlFor="automation-rule-name">Nazwa reguły
            <input aria-describedby={errors.rule_name ? "automation-rule-name-error" : undefined} id="automation-rule-name" maxLength={160} onChange={(event) => setDraft((current) => ({ ...current, name: event.target.value }))} required value={draft.name} />
          </label>
          {errors.rule_name ? <p className="module-error" id="automation-rule-name-error">{errors.rule_name}</p> : null}
          <label className="module-field" htmlFor="automation-rule-description">Opis <span>(opcjonalnie)</span>
            <textarea id="automation-rule-description" maxLength={1000} onChange={(event) => setDraft((current) => ({ ...current, description: event.target.value }))} value={draft.description} />
          </label>
          {errors.description ? <p className="module-error">{errors.description}</p> : null}
        </section>

        <section className="automation-rule-form__section" aria-labelledby="rule-trigger-section">
          <div><span className="eyebrow">2. Gdy</span><h2 id="rule-trigger-section">Wybierz zdarzenie</h2></div>
          <label className="module-field" htmlFor="automation-rule-trigger">Gdy…
            <select id="automation-rule-trigger" onChange={(event) => setDraft((current) => resetConditionsForTrigger(current, event.target.value))} value={draft.triggerKey}>
              <option value="">Wybierz zdarzenie</option>
              {catalog.triggers.map((item) => <option key={item.key} value={item.key}>{automationTriggerLabel(item)}</option>)}
            </select>
          </label>
          {errors.trigger_event_type ? <p className="module-error">{errors.trigger_event_type}</p> : null}
        </section>

        <section className="automation-rule-form__section" aria-labelledby="rule-condition-section">
          <div><span className="eyebrow">3. Jeśli</span><h2 id="rule-condition-section">Dodaj opcjonalne warunki</h2><p>Bez dodatkowego warunku reguła zareaguje na każde zdarzenie wybranego typu.</p></div>
          <div className="automation-condition-list">
            {draft.conditions.map((condition, index) => {
              const field = availableConditionFields.find((item) => item.key === condition.fieldKey);
              const operators = field?.operators ?? [];
              return <div className="automation-condition-row" key={`${condition.fieldKey}-${index}`}>
                <label>Jeśli…<select aria-label={`Pole warunku ${index + 1}`} onChange={(event) => setDraft((current) => ({ ...current, conditions: current.conditions.map((item, itemIndex) => itemIndex === index ? { ...item, fieldKey: event.target.value, operator: availableConditionFields.find((candidate) => candidate.key === event.target.value)?.operators?.[0] ?? "", value: "" } : item) }))} value={condition.fieldKey}>
                  {availableConditionFields.filter((item) => item.key === condition.fieldKey || !draft.conditions.some((current) => current.fieldKey === item.key)).map((item) => <option key={item.key} value={item.key}>{automationConditionLabel(item.key)}</option>)}
                </select></label>
                {operators.length === 1 ? <span className="automation-condition-row__operator">{automationOperatorLabel(operators[0])}</span> : <label>Operator<select aria-label={`Operator warunku ${index + 1}`} onChange={(event) => setDraft((current) => ({ ...current, conditions: current.conditions.map((item, itemIndex) => itemIndex === index ? { ...item, operator: event.target.value } : item) }))} value={condition.operator}>{operators.map((operator) => <option key={operator} value={operator}>{automationOperatorLabel(operator)}</option>)}</select></label>}
                <label>Wartość<input aria-label={`Wartość warunku ${index + 1}`} maxLength={field?.maxLength ?? 120} onChange={(event) => setDraft((current) => ({ ...current, conditions: current.conditions.map((item, itemIndex) => itemIndex === index ? { ...item, value: event.target.value } : item) }))} value={condition.value} /></label>
                <Button aria-label={`Usuń warunek ${index + 1}`} icon={<Trash2 aria-hidden="true" size={15} />} onClick={() => setDraft((current) => ({ ...current, conditions: current.conditions.filter((_, itemIndex) => itemIndex !== index) }))} size="sm" variant="ghost">Usuń</Button>
                {errors[`conditions_json.${index}`] ? <p className="module-error">{errors[`conditions_json.${index}`]}</p> : null}
              </div>;
            })}
          </div>
          <Button disabled={!trigger || draft.conditions.length >= catalog.constraints.maxConditions || draft.conditions.length >= availableConditionFields.length} icon={<Plus aria-hidden="true" size={15} />} onClick={addCondition}>Dodaj warunek</Button>
          {errors.conditions_json ? <p className="module-error">{errors.conditions_json}</p> : null}
        </section>

        <section className="automation-rule-form__section" aria-labelledby="rule-action-section">
          <div><span className="eyebrow">4. Zrób</span><h2 id="rule-action-section">Wybierz działanie</h2></div>
          <label className="module-field" htmlFor="automation-rule-action">Zrób…
            <select id="automation-rule-action" onChange={(event) => setDraft((current) => ({ ...current, actionKey: event.target.value, actionValues: {} }))} value={draft.actionKey}>
              {supportedManagementActions(catalog).map((item) => <option key={item.key} value={item.key}>{automationActionLabel(item)}</option>)}
            </select>
          </label>
          {action?.fields.map((field) => <div key={field.key}>
            <label className="module-field" htmlFor={`automation-action-${field.key}`}>{automationActionFieldLabel(field.key)}{field.required ? "" : " (opcjonalnie)"}
              {field.key === "description" ? <textarea id={`automation-action-${field.key}`} maxLength={field.maxLength} onChange={(event) => setDraft((current) => ({ ...current, actionValues: { ...current.actionValues, [field.key]: event.target.value } }))} value={draft.actionValues[field.key] ?? ""} /> : <input id={`automation-action-${field.key}`} maxLength={field.maxLength} onChange={(event) => setDraft((current) => ({ ...current, actionValues: { ...current.actionValues, [field.key]: event.target.value } }))} required={field.required} value={draft.actionValues[field.key] ?? ""} />}
            </label>
            {errors[`actions_json.${field.key}`] ? <p className="module-error">{errors[`actions_json.${field.key}`]}</p> : null}
          </div>)}
          {errors.actions_json ? <p className="module-error">{errors.actions_json}</p> : null}
        </section>

        <section className="automation-rule-form__section automation-rule-summary" aria-labelledby="rule-summary-section">
          <div><span className="eyebrow">5. Podsumowanie</span><h2 id="rule-summary-section">Podsumowanie reguły</h2></div>
          <dl>
            <div><dt>Nazwa</dt><dd>{draft.name.trim() || "Nie podano"}</dd></div>
            <div><dt>Gdy</dt><dd>{automationTriggerLabel(trigger)}</dd></div>
            <div><dt>Jeśli</dt><dd>{draft.conditions.length === 0 ? "Bez dodatkowego warunku" : draft.conditions.map((condition) => `${automationConditionLabel(condition.fieldKey)} ${automationOperatorLabel(condition.operator)} ${condition.value || "…"}`).join("; ")}</dd></div>
            <div><dt>Zrób</dt><dd>{automationActionLabel(action)}{draft.actionValues.title ? ` „${draft.actionValues.title}”` : ""}</dd></div>
          </dl>
          <p className="automation-rule-summary__notice">Reguła zostanie zapisana jako wyłączona. Po zapisaniu możesz ją osobno włączyć.</p>
          <p className="module-note">W tej wersji zapisanej konfiguracji reguły nie można jeszcze edytować.</p>
        </section>

        {submitError ? <p className="module-error" role="alert">{submitError}</p> : null}
        <div className="automation-rule-form__actions">
          <Link className="ui-button ui-button--secondary ui-button--md" href="/automatyzacje/reguly">Anuluj</Link>
          <Button disabled={submitting} type="submit" variant="primary">{submitting ? "Zapisywanie..." : "Zapisz regułę"}</Button>
        </div>
      </form>
    </section>
  );
}
