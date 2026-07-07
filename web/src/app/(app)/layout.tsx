// Authed shell — ported from app.py: sidebar nav + account on desktop,
// top bar + tab nav on mobile, no-pick warning banner on every page.
import { SidebarNav, TabNav, type NavItem } from "@/components/Nav";
import { Badge } from "@/components/ui";
import { getActiveRound, getUserPickForRound } from "@/lib/db";
import { countdown, displayName, formatET, parseTs } from "@/lib/rounds";
import { getViewer } from "@/lib/viewer";

export const dynamic = "force-dynamic";

const ADMIN_EMAIL = "nathanwdoctor@gmail.com";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const viewer = await getViewer();
  if (!viewer) {
    return (
      <main className="mx-auto max-w-lg p-8 text-center text-muted">
        No viewer configured. Set VIEW_AS_EMAIL in .env.local (Phase 1) —
        real login arrives with the auth phase.
      </main>
    );
  }

  const items: NavItem[] = [
    { href: "/", label: "Make a Pick", shortLabel: "Pick", icon: "✅" },
    { href: "/pool", label: "The Pool", shortLabel: "Pool", icon: "🏆" },
    { href: "/bracket", label: "Bracket", icon: "🗓️" },
    { href: "/rules", label: "Rules", icon: "📋" },
  ];
  if (viewer.email.toLowerCase() === ADMIN_EMAIL.toLowerCase()) {
    items.push({ href: "/admin", label: "Admin", icon: "⚙️" });
  }

  // No-pick warning banner (app.py)
  let banner: string | null = null;
  const active = await getActiveRound();
  if (active && !viewer.is_eliminated && active.status !== "locked") {
    const now = new Date();
    if (now < parseTs(active.deadline) &&
        !(await getUserPickForRound(viewer.id, active.id))) {
      banner = `⚠️ No pick yet for the ${active.name} — all picks lock at the round's first kickoff, in ${countdown(active.deadline, now)} (${formatET(active.deadline)}). Head to ✅ Make a Pick.`;
    }
  }

  const badge = viewer.is_eliminated
    ? <Badge tone="red">Eliminated</Badge>
    : <Badge tone="green">Still alive ✓</Badge>;

  return (
    <div className="flex min-h-screen">
      {/* Desktop sidebar */}
      <aside className="hidden w-60 shrink-0 flex-col gap-4 border-r border-border2 bg-surface p-4 sm:flex">
        <div className="text-lg font-bold text-ink">⚽ World Cup Survivor</div>
        <SidebarNav items={items} />
        <div className="mt-auto border-t border-border2 pt-4">
          <div className="mb-1 font-semibold text-ink">{displayName(viewer)}</div>
          {badge}
        </div>
      </aside>

      <div className="min-w-0 flex-1">
        {/* Mobile top bar + tabs */}
        <div className="flex flex-col gap-2 border-b border-border2 p-3 sm:hidden">
          <div className="flex items-center justify-between">
            <div className="text-sm font-bold whitespace-nowrap text-ink">⚽ World Cup Survivor</div>
            <div className="flex items-center gap-2 text-xs text-muted">
              <span className="max-w-24 truncate">👤 {displayName(viewer)}</span>
              {badge}
            </div>
          </div>
          <TabNav items={items} />
        </div>

        <main className="mx-auto max-w-5xl p-3 pb-16 sm:p-8">
          {banner && (
            <div className="mb-4 rounded-lg border border-lose bg-red-950 px-4 py-3 text-sm">
              <span className="text-red-200">{banner}</span>
            </div>
          )}
          {children}
        </main>
      </div>
    </div>
  );
}
