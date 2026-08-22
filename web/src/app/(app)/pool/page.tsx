import { AppHeader, Screen, Card, EmptyState, AliveBadge, TeamTile, Pill } from "@/components/ui";
import {
  getSettings, getCurrentWeek, getStandings, getTeams, getGamesForWeek,
} from "@/lib/nflDb";
import { arePicksRevealed, countdown, displayName, pickResult } from "@/lib/nfl";
import type { Team } from "@/lib/nfl";

export const dynamic = "force-dynamic";

export default async function PoolPage() {
  const settings = await getSettings();
  const week = await getCurrentWeek(settings.season);
  const [standings, teamList] = await Promise.all([
    getStandings(settings.season, week), getTeams(),
  ]);
  const teams: Record<string, Team> = Object.fromEntries(teamList.map((t) => [t.abbr, t]));
  const games = week ? await getGamesForWeek(week.id) : [];
  const revealed = week ? arePicksRevealed(week) : false;

  const alive = standings.filter((s) => !s.isEliminated);
  const out = standings.filter((s) => s.isEliminated);

  if (standings.length === 0) {
    return (
      <>
        <AppHeader title="Pool" />
        <Screen><EmptyState icon="👥" title="Nobody's in yet"
          body="Players appear here once they join the season." /></Screen>
      </>
    );
  }

  return (
    <>
      <AppHeader
        title="Pool"
        subtitle={`${alive.length} alive · ${out.length} out`}
        right={week && !revealed
          ? <Pill className="bg-raised text-muted">Hidden {countdown(week.lock_at)}</Pill>
          : undefined}
      />

      <Screen>
        {/* Before the lock the pool sees WHO has picked, never WHAT. */}
        {week && !revealed && (
          <p className="mt-4 rounded-xl border border-border bg-surface2 px-3 py-2.5
                        text-[12.5px] leading-relaxed text-muted">
            Picks stay hidden until {week.name}&apos;s first kickoff. You can see who&apos;s
            locked something in — just not what.
          </p>
        )}

        <div className="mt-4 space-y-2">
          {alive.map((s) => (
            <Card key={s.userId} className="flex items-center gap-3 p-3">
              <div className="min-w-0 flex-1">
                <p className="truncate text-[15px] font-semibold text-ink">
                  {displayName(s)}
                </p>
                <p className="text-[11.5px] text-faint">
                  {s.picksByWeek.size} {s.picksByWeek.size === 1 ? "week" : "weeks"} survived
                </p>
              </div>

              {revealed && s.currentPick ? (
                <div className="flex items-center gap-2">
                  <TeamTile team={teams[s.currentPick]} size="sm" />
                  <PickDot result={pickResult(s.currentPick, games)} />
                </div>
              ) : s.hasPickedThisWeek ? (
                <Pill className="bg-accent-dim text-accent">Locked in</Pill>
              ) : (
                <Pill className="bg-raised text-faint">No pick</Pill>
              )}
            </Card>
          ))}
        </div>

        {out.length > 0 && (
          <>
            <h2 className="px-1 pt-7 pb-2 text-[11px] font-semibold tracking-[0.09em]
                           text-faint uppercase">
              Eliminated
            </h2>
            <div className="space-y-2">
              {out.map((s) => (
                <Card key={s.userId} className="flex items-center gap-3 p-3 opacity-60">
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-[14px] font-semibold text-body line-through">
                      {displayName(s)}
                    </p>
                    <p className="text-[11.5px] text-faint">
                      Out in week {s.eliminatedWeekId ?? "?"}
                      {s.eliminatedReason === "no_pick" && " · no pick"}
                      {s.eliminatedReason === "tie" && " · tie"}
                    </p>
                  </div>
                  <AliveBadge alive={false} />
                </Card>
              ))}
            </div>
          </>
        )}
      </Screen>
    </>
  );
}

function PickDot({ result }: { result: ReturnType<typeof pickResult> }) {
  const cls = { won: "bg-alive", lost: "bg-out", tied: "bg-tie", pending: "bg-border2" }[result];
  return <span className={`h-2 w-2 shrink-0 rounded-full ${cls}`} aria-label={result} />;
}
