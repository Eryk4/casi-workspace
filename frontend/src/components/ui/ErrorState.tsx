import type { ReactNode } from "react";

type ErrorStateProps = {
  action?: ReactNode;
  title?: string;
  description: string;
};

export function ErrorState({ action, description, title = "Nie udalo sie pobrac danych" }: ErrorStateProps) {
  return (
    <div className="ui-error-state" role="alert">
      <strong>{title}</strong>
      <p>{description}</p>
      {action ? <div className="ui-error-state__action">{action}</div> : null}
    </div>
  );
}
