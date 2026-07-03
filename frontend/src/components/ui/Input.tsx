import type { InputHTMLAttributes, ReactNode } from "react";

import { cn } from "@/lib/utils";

type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  icon?: ReactNode;
  label?: string;
};

export function Input({ className, icon, id, label, ...props }: InputProps) {
  const inputId = id ?? (label ? label.toLowerCase().replace(/\s+/g, "-") : undefined);

  return (
    <label className="ui-input">
      {label ? <span className="ui-input__label">{label}</span> : null}
      <span className="ui-input__control">
        {icon ? <span className="ui-input__icon">{icon}</span> : null}
        <input className={cn("ui-input__field", className)} id={inputId} {...props} />
      </span>
    </label>
  );
}
