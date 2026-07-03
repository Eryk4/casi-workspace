"use client";

import { cn } from "@/lib/utils";

export type TabItem = {
  id: string;
  label: string;
  disabled?: boolean;
};

type TabsProps = {
  activeId: string;
  items: TabItem[];
  onChange: (id: string) => void;
};

export function Tabs({ activeId, items, onChange }: TabsProps) {
  return (
    <div className="ui-tabs" role="tablist">
      {items.map((item) => (
        <button
          aria-selected={activeId === item.id}
          className={cn("ui-tabs__item", activeId === item.id && "is-active")}
          disabled={item.disabled}
          key={item.id}
          onClick={() => onChange(item.id)}
          role="tab"
          type="button"
        >
          {item.label}
        </button>
      ))}
    </div>
  );
}
