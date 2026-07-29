"use client";

import type { FormEvent } from "react";

import { Button } from "@/components/ui/Button";

import { addLocalCalendarDays, parseLocalCalendarDate } from "./billingModel";

type SnoozableNextStep = {
  id: string;
  eventId: number;
  plannedFor?: string;
};

export function BillingNextStepActionControls({
  row,
  completing,
  snoozing,
  snoozeDate,
  snoozeError,
  busy,
  onComplete,
  onStartSnooze,
  onSnoozeDateChange,
  onSnoozeSubmit,
  onCancelSnooze,
}: {
  row: SnoozableNextStep;
  completing: boolean;
  snoozing: boolean;
  snoozeDate: string;
  snoozeError?: string | null;
  busy: boolean;
  onComplete: () => void;
  onStartSnooze: () => void;
  onSnoozeDateChange: (value: string) => void;
  onSnoozeSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onCancelSnooze: () => void;
}) {
  const minimumDate = parseLocalCalendarDate(row.plannedFor) ? addLocalCalendarDays(row.plannedFor!, 1) : undefined;
  const inputId = `billing-next-step-snooze-${row.eventId}`;

  return (
    <div className="module-stack">
      <div className="module-page-actions">
        <Button
          data-snooze-next-step-id={row.eventId}
          disabled={busy}
          onClick={onStartSnooze}
          size="sm"
          type="button"
          variant="secondary"
        >
          Odłóż
        </Button>
        <Button
          data-next-step-id={row.eventId}
          disabled={busy}
          onClick={onComplete}
          size="sm"
          type="button"
          variant="secondary"
        >
          {completing ? "Zapisywanie..." : "Oznacz jako wykonany"}
        </Button>
      </div>
      {snoozing ? (
        <form className="module-form" data-snooze-form-id={row.eventId} onSubmit={onSnoozeSubmit}>
          <p className="module-note">Obecny termin: {row.plannedFor ?? "bez terminu"}</p>
          <label className="module-field" htmlFor={inputId}>
            <span>Nowy termin</span>
            <input
              autoFocus
              disabled={busy}
              id={inputId}
              min={minimumDate}
              onChange={(event) => onSnoozeDateChange(event.target.value)}
              required
              type="date"
              value={snoozeDate}
            />
          </label>
          {snoozeError ? <p className="module-error" role="alert">{snoozeError}</p> : null}
          <div className="module-page-actions">
            <Button disabled={busy || !snoozeDate} size="sm" type="submit">
              {busy ? "Zapisywanie..." : "Zatwierdź odłożenie"}
            </Button>
            <Button disabled={busy} onClick={onCancelSnooze} size="sm" type="button" variant="secondary">
              Anuluj
            </Button>
          </div>
        </form>
      ) : null}
    </div>
  );
}
