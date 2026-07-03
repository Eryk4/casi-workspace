import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "@/lib/utils";

type CardProps = HTMLAttributes<HTMLElement> & {
  title?: string;
  description?: string;
  action?: ReactNode;
  footer?: ReactNode;
};

export function Card({ action, children, className, description, footer, title, ...props }: CardProps) {
  return (
    <section className={cn("ui-card", className)} {...props}>
      {title || description || action ? (
        <header className="ui-card__header">
          <div>
            {title ? <h2 className="ui-card__title">{title}</h2> : null}
            {description ? <p className="ui-card__description">{description}</p> : null}
          </div>
          {action ? <div className="ui-card__action">{action}</div> : null}
        </header>
      ) : null}
      <div className="ui-card__body">{children}</div>
      {footer ? <footer className="ui-card__footer">{footer}</footer> : null}
    </section>
  );
}
