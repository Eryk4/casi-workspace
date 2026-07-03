import type { ReactNode } from "react";

import { Button } from "./Button";

type EmptyStateProps = {
  title: string;
  description: string;
  icon?: ReactNode;
  actionLabel?: string;
  onAction?: () => void;
};

export function EmptyState({ actionLabel, description, icon, onAction, title }: EmptyStateProps) {
  return (
    <div className="ui-empty-state">
      {icon ? <span className="ui-empty-state__icon">{icon}</span> : null}
      <div>
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
      {actionLabel ? (
        <Button onClick={onAction} size="sm" variant="secondary">
          {actionLabel}
        </Button>
      ) : null}
    </div>
  );
}
