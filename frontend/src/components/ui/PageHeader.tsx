import type { ReactNode } from "react";

import { Badge } from "./Badge";

type PageHeaderProps = {
  eyebrow?: string;
  title: string;
  description: string;
  badgeTone?: "neutral" | "success" | "warning" | "danger" | "info";
  actions?: ReactNode;
};

export function PageHeader({ actions, badgeTone = "neutral", description, eyebrow, title }: PageHeaderProps) {
  return (
    <header className="ui-page-header">
      <div className="ui-page-header__copy">
        {eyebrow ? <Badge tone={badgeTone}>{eyebrow}</Badge> : null}
        <div>
          <h2>{title}</h2>
          <p>{description}</p>
        </div>
      </div>
      {actions ? <div className="ui-page-header__actions">{actions}</div> : null}
    </header>
  );
}
