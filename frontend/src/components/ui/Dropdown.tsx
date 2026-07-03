"use client";

import type { ReactNode } from "react";
import { useState } from "react";

import { cn } from "@/lib/utils";

type DropdownItem = {
  label: string;
  onSelect: () => void;
  danger?: boolean;
  disabled?: boolean;
};

type DropdownProps = {
  items: DropdownItem[];
  label: ReactNode;
};

export function Dropdown({ items, label }: DropdownProps) {
  const [open, setOpen] = useState(false);

  return (
    <div className="ui-dropdown">
      <button
        aria-expanded={open}
        className="ui-dropdown__trigger"
        onClick={() => setOpen((value) => !value)}
        type="button"
      >
        {label}
      </button>
      {open ? (
        <div className="ui-dropdown__menu" role="menu">
          {items.map((item) => (
            <button
              aria-disabled={item.disabled || undefined}
              className={cn("ui-dropdown__item", item.danger && "is-danger")}
              disabled={item.disabled}
              key={item.label}
              onClick={() => {
                if (item.disabled) {
                  return;
                }
                item.onSelect();
                setOpen(false);
              }}
              role="menuitem"
              type="button"
            >
              {item.label}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}
