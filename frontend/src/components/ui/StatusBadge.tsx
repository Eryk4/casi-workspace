import { Badge } from "./Badge";

type StatusBadgeProps = {
  children: string;
  status?: "ok" | "warning" | "danger" | "info" | "neutral";
};

const toneByStatus = {
  danger: "danger",
  info: "info",
  neutral: "neutral",
  ok: "success",
  warning: "warning",
} as const;

export function StatusBadge({ children, status = "neutral" }: StatusBadgeProps) {
  return <Badge tone={toneByStatus[status]}>{children}</Badge>;
}
