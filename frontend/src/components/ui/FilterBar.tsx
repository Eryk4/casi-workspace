import type { ReactNode } from "react";

type FilterBarProps = {
  children: ReactNode;
  label?: string;
};

export function FilterBar({ children, label = "Filtry" }: FilterBarProps) {
  return (
    <section className="ui-filter-bar" aria-label={label}>
      {children}
    </section>
  );
}
