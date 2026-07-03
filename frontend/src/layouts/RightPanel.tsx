import type { ReactNode } from "react";

type RightPanelProps = {
  children: ReactNode;
  title: string;
};

export function RightPanel({ children, title }: RightPanelProps) {
  return (
    <aside className="app-right-panel" aria-label={title}>
      <header className="app-right-panel__header">
        <h2>{title}</h2>
      </header>
      <div className="app-right-panel__body">{children}</div>
    </aside>
  );
}
