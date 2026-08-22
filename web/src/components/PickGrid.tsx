"use client";

import { useState, useTransition } from "react";
import { TeamTile, Card } from "./ui";
import { formatKickoff, dayLabel } from "@/lib/nfl";
import type { Game, Team } from "@/lib/nfl";
import { submitPick } from "@/app/(app)/actions";

export interface PickGridProps {
  games: Game[];
  teams: Record<string, Team>;
  usedTeams: string[];
  currentPick: string | null;
  weekId: number;
  locked: boolean;
}

const ERRORS: Record<string, string> = {
  locked: "This week is locked — picks are final.",
  team_used: "You've already used that team this season.",
  team_on_bye: "That team is on a bye this week.",
  eliminated: "You're eliminated — no more picks.",
  unknown: "Couldn't save that pick. Try again.",
};

/** One tappable side of a matchup. The whole row half is the target, so
 * there's no small radio button to hunt for with a thumb. */
function TeamSide({
  team, abbr, selected, used, disabled, onPick,
}: {
  team: Team | undefined; abbr: string; selected: boolean;
  used: boolean; disabled: boolean; onPick: () => void;
}) {
  const label = team ? `${team.location} ${team.nickname}` : abbr;
  return (
    <button
      type="button"
      onClick={onPick}
      disabled={disabled || used}
      aria-pressed={selected}
      aria-label={used ? `${label} — already used` : label}
      className={`press flex flex-1 items-center gap-2.5 rounded-xl px-2.5 py-2.5 text-left
        ${selected ? "bg-accent-dim ring-2 ring-accent" : "bg-surface2"}
        ${used ? "opacity-40" : ""}
        ${disabled && !selected ? "opacity-60" : ""}`}
    >
      {team && <TeamTile team={team} size="sm" dim={used} />}
      <span className="min-w-0 flex-1">
        <span className={`block truncate text-[13.5px] leading-tight font-semibold
                          ${selected ? "text-ink" : "text-body"}`}>
          {team?.nickname ?? abbr}
        </span>
        {used && <span className="text-[10.5px] text-faint">used</span>}
      </span>
      {selected && (
        <svg viewBox="0 0 24 24" className="h-4 w-4 shrink-0 text-accent" fill="none"
             stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
          <path d="M20 6 9 17l-5-5" />
        </svg>
      )}
    </button>
  );
}

export function PickGrid({
  games, teams, usedTeams, currentPick, weekId, locked,
}: PickGridProps) {
  const [pick, setPick] = useState<string | null>(currentPick);
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();
  const used = new Set(usedTeams.filter((t) => t !== currentPick));

  function choose(team: string) {
    if (locked || pending) return;
    const previous = pick;
    setPick(team);              // optimistic — the tap feels instant
    setError(null);
    startTransition(async () => {
      const res = await submitPick(weekId, team);
      if (!res.ok) {
        setPick(previous);      // roll back to what the server still holds
        setError(ERRORS[res.error] ?? ERRORS.unknown);
      }
    });
  }

  // Group by day so the week reads as Thu / Sun / Mon, like a TV schedule.
  const byDay = new Map<string, Game[]>();
  for (const g of games) {
    const key = dayLabel(g.kickoff);
    if (!byDay.has(key)) byDay.set(key, []);
    byDay.get(key)!.push(g);
  }

  return (
    <div className="space-y-5">
      {error && (
        <div role="alert" className="rounded-xl border border-out/40 bg-out-dim px-3 py-2.5
                                     text-[13px] font-medium text-out">
          {error}
        </div>
      )}

      {[...byDay.entries()].map(([day, dayGames]) => (
        <section key={day}>
          <h3 className="px-1 pb-2 text-[11px] font-semibold tracking-[0.09em] text-faint uppercase">
            {day}
          </h3>
          <div className="space-y-2">
            {dayGames.map((g) => (
              <Card key={g.id} className="p-2">
                <div className="mb-1.5 flex items-center justify-between px-1">
                  <span className="text-[11px] font-medium text-faint tabular-nums">
                    {formatKickoff(g.kickoff)}
                  </span>
                  {g.status === "in_progress" && (
                    <span className="flex items-center gap-1 text-[10.5px] font-bold
                                     tracking-wide text-alive uppercase">
                      <span className="live-dot h-1.5 w-1.5 rounded-full bg-alive" />live
                    </span>
                  )}
                </div>
                <div className="flex items-stretch gap-1.5">
                  <TeamSide
                    abbr={g.away_abbr} team={teams[g.away_abbr]}
                    selected={pick === g.away_abbr} used={used.has(g.away_abbr)}
                    disabled={locked} onPick={() => choose(g.away_abbr)}
                  />
                  <span className="flex items-center px-0.5 text-[10px] font-bold text-faint">@</span>
                  <TeamSide
                    abbr={g.home_abbr} team={teams[g.home_abbr]}
                    selected={pick === g.home_abbr} used={used.has(g.home_abbr)}
                    disabled={locked} onPick={() => choose(g.home_abbr)}
                  />
                </div>
              </Card>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
