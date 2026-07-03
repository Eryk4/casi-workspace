import Link from "next/link";
import { LayoutDashboard } from "lucide-react";

import { EmptyState } from "@/components/ui/EmptyState";

export default function NotFound() {
  return (
    <div className="app-state-page">
      <EmptyState
        description="Ta trasa nie istnieje w produkcyjnej nawigacji CASI. Wroc do pulpitu albo wybierz modul z lewego menu."
        icon={<LayoutDashboard aria-hidden="true" size={18} />}
        title="Nie znaleziono widoku"
      />
      <div className="app-state-page__actions">
        <Link className="ui-button ui-button--primary ui-button--md" href="/pulpit">
          <span>Pulpit</span>
        </Link>
      </div>
    </div>
  );
}
