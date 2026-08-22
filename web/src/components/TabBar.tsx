"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

/* Bottom tab bar — the standard iOS/Android pattern: fixed, thumb-reachable,
 * always showing where you are. Icons are inline SVG (no icon dependency,
 * and they inherit currentColor so the active state is one class change). */

interface Tab {
  href: string;
  label: string;
  icon: (active: boolean) => React.ReactNode;
}

const stroke = {
  fill: "none",
  strokeWidth: 1.8,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};

const TABS: Tab[] = [
  {
    href: "/",
    label: "Pick",
    icon: (a) => (
      <svg viewBox="0 0 24 24" className="h-6 w-6" stroke="currentColor" {...stroke}
           fill={a ? "currentColor" : "none"} fillOpacity={a ? 0.18 : 0}>
        <path d="M20 6 9 17l-5-5" />
      </svg>
    ),
  },
  {
    href: "/pool",
    label: "Pool",
    icon: (a) => (
      <svg viewBox="0 0 24 24" className="h-6 w-6" stroke="currentColor" {...stroke}
           fill={a ? "currentColor" : "none"} fillOpacity={a ? 0.18 : 0}>
        <path d="M16 20v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
        <circle cx="9" cy="7" r="3.2" />
        <path d="M22 20v-2a4 4 0 0 0-3-3.87M16.5 4.1a4 4 0 0 1 0 7.75" />
      </svg>
    ),
  },
  {
    href: "/season",
    label: "Season",
    icon: (a) => (
      <svg viewBox="0 0 24 24" className="h-6 w-6" stroke="currentColor" {...stroke}
           fill={a ? "currentColor" : "none"} fillOpacity={a ? 0.18 : 0}>
        <rect x="3" y="4.5" width="18" height="16" rx="2.5" />
        <path d="M3 9.5h18M8 3v3M16 3v3" />
      </svg>
    ),
  },
  {
    href: "/rules",
    label: "Rules",
    icon: (a) => (
      <svg viewBox="0 0 24 24" className="h-6 w-6" stroke="currentColor" {...stroke}
           fill={a ? "currentColor" : "none"} fillOpacity={a ? 0.18 : 0}>
        <circle cx="12" cy="12" r="9" />
        <path d="M9.6 9.2a2.5 2.5 0 1 1 3.3 2.4c-.6.2-.9.8-.9 1.4v.5" />
        <path d="M12 17.2h.01" strokeWidth="2.2" />
      </svg>
    ),
  },
];

const isActive = (pathname: string, href: string) =>
  href === "/" ? pathname === "/" : pathname.startsWith(href);

export function TabBar() {
  const pathname = usePathname();
  return (
    <nav
      className="fixed inset-x-0 bottom-0 z-50 border-t border-border/80
                 bg-surface/85 backdrop-blur-xl backdrop-saturate-150"
      style={{ paddingBottom: "var(--safe-bottom)" }}
      aria-label="Main"
    >
      <ul className="mx-auto flex max-w-lg">
        {TABS.map((t) => {
          const active = isActive(pathname, t.href);
          return (
            <li key={t.href} className="flex-1">
              <Link
                href={t.href}
                aria-current={active ? "page" : undefined}
                className={`press flex h-[58px] flex-col items-center justify-center gap-1
                            ${active ? "text-accent" : "text-faint"}`}
              >
                {t.icon(active)}
                <span className={`text-[10.5px] leading-none tracking-wide
                                  ${active ? "font-semibold" : "font-medium"}`}>
                  {t.label}
                </span>
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
