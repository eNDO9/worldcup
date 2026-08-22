import type { ReactNode } from "react";
import type { PickResult, Team } from "@/lib/nfl";

/* Shared primitives for the mobile shell. Server components — anything
 * needing interaction lives in its own "use client" file. */

// --- layout ----------------------------------------------------------------

/** Sticky frosted app header. Pads under the notch on installed iOS. */
export function AppHeader({
  title, subtitle, right,
}: { title: string; subtitle?: ReactNode; right?: ReactNode }) {
  return (
    <header
      className="sticky top-0 z-40 border-b border-border/70 bg-bg/80
                 px-4 pb-3 backdrop-blur-xl backdrop-saturate-150"
      style={{ paddingTop: "calc(var(--safe-top) + 14px)" }}
    >
      <div className="mx-auto flex max-w-lg items-center justify-between gap-3">
        <div className="min-w-0">
          <h1 className="truncate text-[26px] leading-tight font-bold tracking-tight text-ink">
            {title}
          </h1>
          {subtitle && <div className="mt-0.5 text-[13px] text-muted">{subtitle}</div>}
        </div>
        {right}
      </div>
    </header>
  );
}

/** Scroll region that always clears the fixed tab bar. */
export function Screen({ children }: { children: ReactNode }) {
  return (
    <main
      className="mx-auto w-full max-w-lg px-4"
      style={{ paddingBottom: "calc(var(--tabbar-h) + var(--safe-bottom) + 24px)" }}
    >
      {children}
    </main>
  );
}

export function SectionLabel({ children }: { children: ReactNode }) {
  return (
    <h2 className="px-1 pt-6 pb-2 text-[11px] font-semibold tracking-[0.09em]
                   text-faint uppercase">
      {children}
    </h2>
  );
}

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div className={`rounded-card border border-border bg-surface ${className}`}>
      {children}
    </div>
  );
}

export function EmptyState({ icon, title, body }: { icon: string; title: string; body?: string }) {
  return (
    <div className="flex flex-col items-center gap-2 px-6 py-14 text-center">
      <div className="text-4xl opacity-70">{icon}</div>
      <p className="text-[15px] font-semibold text-ink">{title}</p>
      {body && <p className="max-w-[34ch] text-[13px] leading-relaxed text-muted">{body}</p>}
    </div>
  );
}

// --- team identity ---------------------------------------------------------
// No NFL logos or wordmarks anywhere: App Store submissions need a license
// for those. A colored abbreviation tile is both legal and more legible at
// phone size than a 20px logo would be.

export function TeamTile({
  team, size = "md", dim = false,
}: { team: Team; size?: "sm" | "md" | "lg"; dim?: boolean }) {
  const dims = {
    sm: "h-8 w-8 text-[10px]",
    md: "h-11 w-11 text-[12px]",
    lg: "h-14 w-14 text-[15px]",
  }[size];
  return (
    <span
      className={`${dims} inline-flex shrink-0 items-center justify-center rounded-xl
                  font-bold tracking-tight text-white tabular-nums
                  ${dim ? "opacity-35 grayscale" : ""}`}
      style={{
        backgroundColor: team.color ?? "#333a48",
        // Thin light rim keeps very dark team colors from vanishing on near-black.
        boxShadow: "inset 0 0 0 1px rgba(255,255,255,0.14)",
      }}
      aria-hidden="true"
    >
      {team.abbr}
    </span>
  );
}

// --- status ----------------------------------------------------------------

const RESULT_STYLES: Record<PickResult, { label: string; cls: string }> = {
  won:     { label: "Won",     cls: "bg-alive-dim text-alive" },
  lost:    { label: "Lost",    cls: "bg-out-dim text-out" },
  tied:    { label: "Tied",    cls: "bg-tie-dim text-tie" },
  pending: { label: "Pending", cls: "bg-raised text-muted" },
};

export function ResultBadge({ result }: { result: PickResult }) {
  const s = RESULT_STYLES[result];
  return <Pill className={s.cls}>{s.label}</Pill>;
}

export function Pill({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1
                      text-[11px] font-semibold ${className}`}>
      {children}
    </span>
  );
}

export function AliveBadge({ alive }: { alive: boolean }) {
  return alive
    ? <Pill className="bg-alive-dim text-alive">
        <span className="h-1.5 w-1.5 rounded-full bg-alive" />Alive
      </Pill>
    : <Pill className="bg-out-dim text-out">Eliminated</Pill>;
}

/** The lock countdown / locked state, top-right of the Pick screen. */
export function LockChip({ locked, countdown }: { locked: boolean; countdown: string }) {
  if (locked) {
    return (
      <Pill className="bg-raised text-muted">
        <svg viewBox="0 0 24 24" className="h-3 w-3" fill="none" stroke="currentColor" strokeWidth="2.4">
          <rect x="4" y="10.5" width="16" height="10" rx="2" />
          <path d="M8 10.5V7a4 4 0 0 1 8 0v3.5" />
        </svg>
        Locked
      </Pill>
    );
  }
  return (
    <Pill className="live-dot bg-accent-dim text-accent tabular-nums">
      Locks in {countdown}
    </Pill>
  );
}
