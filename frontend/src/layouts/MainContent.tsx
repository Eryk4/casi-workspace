import type { ReactNode } from "react";

type MainContentProps = {
  children: ReactNode;
};

export function MainContent({ children }: MainContentProps) {
  return (
    <main className="app-main" id="main-content">
      <div className="app-main__inner">{children}</div>
    </main>
  );
}
