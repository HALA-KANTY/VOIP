"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import {
  IconDashboard,
  IconUsers,
  IconToken,
  IconCall,
  IconStats,
  IconLogout,
} from "@/components/ui/icons";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: IconDashboard },
  { href: "/utilisateurs", label: "Utilisateurs", icon: IconUsers },
  { href: "/tokens", label: "Tokens", icon: IconToken },
  { href: "/services-ivr", label: "Services IVR", icon: IconCall},
  { href: "/cdr", label: "Journal d'appels", icon: IconCall },
  { href: "/statistiques", label: "Statistiques", icon: IconStats },
  // 🔴 AJOUT DU NOUVEL ONGLET POUR LA MODIFICATION DU TARIF A CHAUD
  { href: "/tarifs", label: "Tarification", icon: IconStats },
];

export function Sidebar() {
  const pathname = usePathname();
  const { logout } = useAuth();

  return (
    <aside className="flex h-screen w-60 shrink-0 flex-col border-r border-border bg-sidebar">
      <div className="flex items-center gap-2.5 px-5 py-6">
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent text-sm font-bold text-white">
          K
        </span>
        <div>
          <p className="text-sm font-semibold leading-none">KANTYVOIP</p>
          <p className="mt-0.5 text-xs text-ink-muted">Administration</p>
        </div>
      </div>

      <nav className="flex-1 px-3">
        <p className="mb-2 px-2 text-xs font-medium tracking-wide text-ink-muted">MENU</p>
        <ul className="space-y-1">
          {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
            const actif = href === "/" ? pathname === "/" : pathname.startsWith(href);
            return (
              <li key={href}>
                <Link
                  href={href}
                  className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors ${
                    actif
                      ? "bg-accent-soft text-accent"
                      : "text-ink-secondary hover:bg-surface-2 hover:text-ink"
                  }`}
                >
                  <Icon />
                  {label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="border-t border-border p-3">
        <button
          onClick={logout}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-ink-secondary transition-colors hover:bg-surface-2 hover:text-ink"
        >
          <IconLogout />
          Deconnexion
        </button>
      </div>
    </aside>
  );
}
