import Link from "next/link";
import { ChevronsLeft, PanelLeftClose, PanelLeftOpen } from "lucide-react";

import { isNavigationItemActive, navigationGroups, navigationItems } from "@/config/navigation";
import { cn } from "@/lib/utils";

import { Button } from "@/components/ui/Button";

type SidebarProps = {
  activePath: string;
  collapsed: boolean;
  onToggleCollapsed: () => void;
};

export function Sidebar({ activePath, collapsed, onToggleCollapsed }: SidebarProps) {
  return (
    <aside className="app-sidebar" aria-label="Glowna nawigacja">
      <div className="app-sidebar__brand">
        <Link className="app-sidebar__logo" href="/pulpit" aria-label="CASI Workspace">
          <span className="app-sidebar__logo-text">
            <strong>CASI</strong>
            <span>Workspace</span>
          </span>
        </Link>
        <Button
          aria-label={collapsed ? "Rozwin sidebar" : "Zwin sidebar"}
          className="app-sidebar__toggle"
          icon={collapsed ? <PanelLeftOpen size={16} /> : <PanelLeftClose size={16} />}
          onClick={onToggleCollapsed}
          size="sm"
          variant="ghost"
        >
          <span className="app-sidebar__toggle-label">{collapsed ? "Rozwin" : "Zwin"}</span>
        </Button>
      </div>

      <nav className="app-sidebar__nav">
        {navigationGroups.map((group) => {
          const items = navigationItems.filter((item) => item.group === group.id);

          return (
            <section className="app-sidebar__group" key={group.id}>
              <p className="app-sidebar__group-label">{group.label}</p>
              <div className="app-sidebar__links">
                {items.map((item) => {
                  const active = isNavigationItemActive(activePath, item);
                  const Icon = item.icon;

                  return (
                    <Link
                      aria-current={active ? "page" : undefined}
                      className={cn("app-sidebar__link", active && "is-active")}
                      href={item.path}
                      key={item.id}
                      title={collapsed ? item.label : undefined}
                    >
                      <Icon aria-hidden="true" size={16} />
                      <span className="app-sidebar__link-label">{item.label}</span>
                    </Link>
                  );
                })}
              </div>
            </section>
          );
        })}
      </nav>
      <button className="app-sidebar__footer-toggle" onClick={onToggleCollapsed} type="button">
        <ChevronsLeft aria-hidden="true" size={15} />
        <span>{collapsed ? "Rozwin menu" : "Zwin menu"}</span>
      </button>
    </aside>
  );
}
