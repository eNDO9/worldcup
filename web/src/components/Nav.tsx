"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export interface NavItem {
  href: string;
  label: string;
  shortLabel?: string;
  icon: string;
}

function isActive(pathname: string, href: string): boolean {
  return href === "/" ? pathname === "/" : pathname.startsWith(href);
}

/** Desktop: vertical sidebar links (matches the Streamlit sidebar nav). */
export function SidebarNav({ items }: { items: NavItem[] }) {
  const pathname = usePathname();
  return (
    <nav className="flex flex-col gap-1">
      {items.map((it) => (
        <Link
          key={it.href}
          href={it.href}
          className={`rounded-lg px-3 py-2 text-sm ${
            isActive(pathname, it.href)
              ? "bg-border/60 font-semibold text-ink"
              : "text-body hover:bg-border/30 hover:text-ink"
          }`}
        >
          {it.icon} {it.label}
        </Link>
      ))}
    </nav>
  );
}

/** Mobile: horizontal tab bar (matches the Streamlit top tabs). */
export function TabNav({ items }: { items: NavItem[] }) {
  const pathname = usePathname();
  return (
    <nav className="flex gap-2">
      {items.map((it) => (
        <Link
          key={it.href}
          href={it.href}
          className={`min-w-0 flex-1 truncate rounded-lg border px-1 py-2 text-center text-xs whitespace-nowrap ${
            isActive(pathname, it.href)
              ? "border-primary bg-primary font-semibold text-white"
              : "border-border bg-surface text-ink"
          }`}
        >
          {it.icon} {it.shortLabel ?? it.label}
        </Link>
      ))}
    </nav>
  );
}
