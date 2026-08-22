import { AppHeader, Screen, Card, EmptyState, TeamTile, ResultBadge, AliveBadge } from "@/components/ui";
import { getViewer } from "@/lib/viewer";
import {
  getSettings, getAllWeeks, getUserPicks, getTeams, getGamesForWeek,
} from "@/lib/nflDb";
import { arePicksRevealed, pickResult } from "@/lib/nfl";
import type { Team, PickResult } from "@/lib/nfl";

export const dynamic = "force-dynamic";

export default async function SeasonPage() {
  const settings = await getSettings();
  const viewer = await getViewer();

  if (!viewer) {
    return (
      <>
        <AppHeader title="Season" />
        <Screen><EmptyState icon="🔒" title="Not signed in" /></Screen>
      </>
    );
  }

  const [weeks, picks, teamList] = await Promise.all([
    getAllWeeks(settings.season), getUserPicks(viewer.id, settings.season), getTeams(),
  ]);
  const teams: Record<string, Team> = Object.fromEntries(teamList.map((t) => [t.abbr, t]));
  const pickByWeek = new Map(picks.map((p) => [p.week_id, p]));

  // Results only for weeks already revealed — one fetch per such week.
  const revealedIds = weeks.filter((w) => arePicksRevealed(w)).map((w) => w.id);
  const gamesByWeek = new Map(await Promise.all(
    revealedIds.map(async (id) => [id, await getGamesForWeek(id)] as const),
  ));

  const used = new Set(picks.map((p) => p.team_abbr));
  const remaining = teamList.filter((t) => !used.has(t.abbr));

  return (
    <>
      <AppHeader
        title="My Season"
        subtitle={`${used.size} of 32 teams used`}
        right={<AliveBadge alive={!viewer.entry.is_eliminated} />}
      />

      <Screen>
        {/* Week ladder — the whole season at a glance, one row per week. */}
        <div className="mt-4 space-y-1.5">
          {weeks.map((w) => {
            const p = pickByWeek.get(w.id);
            const revealed = arePicksRevealed(w);
            const result: PickResult | null =
              p && revealed ? pickResult(p.team_abbr, gamesByWeek.get(w.id) ?? []) : null;

            return (
              <Card key={w.id} className="flex items-center gap-3 px-3 py-2.5">
                <span className="w-8 shrink-0 text-[12px] font-bold text-faint tabular-nums">
                  {w.week_number}
                </span>

                {p ? (
                  <>
                    <TeamTile team={teams[p.team_abbr]} size="sm" />
                    <span className="min-w-0 flex-1 truncate text-[14px] font-semibold text-ink">
                      {revealed ? (teams[p.team_abbr]?.nickname ?? p.team_abbr) : "Locked in"}
                    </span>
                    {result && <ResultBadge result={result} />}
                  </>
                ) : (
                  <span className="flex-1 text-[13px] text-faint">
                    {revealed ? "No pick" : "—"}
                  </span>
                )}
              </Card>
            );
          })}
        </div>

        <h2 className="px-1 pt-7 pb-2 text-[11px] font-semibold tracking-[0.09em]
                       text-faint uppercase">
          Still available · {remaining.length}
        </h2>
        <Card className="p-3">
          <div className="flex flex-wrap gap-1.5">
            {remaining.map((t) => <TeamTile key={t.abbr} team={t} size="sm" />)}
          </div>
        </Card>

        {used.size > 0 && (
          <>
            <h2 className="px-1 pt-6 pb-2 text-[11px] font-semibold tracking-[0.09em]
                           text-faint uppercase">
              Burned · {used.size}
            </h2>
            <Card className="p-3">
              <div className="flex flex-wrap gap-1.5">
                {[...used].map((abbr) => (
                  <TeamTile key={abbr} team={teams[abbr]} size="sm" dim />
                ))}
              </div>
            </Card>
          </>
        )}
      </Screen>
    </>
  );
}
