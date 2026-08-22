import { AppHeader, Screen, Card, EmptyState, LockChip, TeamTile, ResultBadge } from "@/components/ui";
import { PickGrid } from "@/components/PickGrid";
import { getViewer } from "@/lib/viewer";
import {
  getSettings, getCurrentWeek, getGamesForWeek, getTeams,
  getUserPick, getUsedTeams, getAliveEntries,
} from "@/lib/nflDb";
import { syncWeek } from "@/lib/nflSync";
import {
  isWeekLocked, countdown, formatLockTime, byeTeams, pickResult,
} from "@/lib/nfl";
import type { Team } from "@/lib/nfl";

export const dynamic = "force-dynamic";

export default async function PickPage() {
  const settings = await getSettings();
  const week = await getCurrentWeek(settings.season);
  const viewer = await getViewer();

  if (!week) {
    return (
      <>
        <AppHeader title="Survivor" />
        <Screen><EmptyState icon="🏈" title="No season loaded"
          body="Run the schedule seed migration to load the 2026 season." /></Screen>
      </>
    );
  }

  // Keep scores/eliminations current on view. Cheap: ESPN is memoized 30s
  // and syncGames only writes rows that actually changed.
  await syncWeek(week.id);

  const [games, teamList, alive] = await Promise.all([
    getGamesForWeek(week.id), getTeams(), getAliveEntries(settings.season),
  ]);
  const teams: Record<string, Team> = Object.fromEntries(teamList.map((t) => [t.abbr, t]));
  const locked = isWeekLocked(week);

  const myPick = viewer ? await getUserPick(viewer.id, week.id) : null;
  const used = viewer ? [...(await getUsedTeams(viewer.id, settings.season))] : [];
  const eliminated = viewer?.entry.is_eliminated ?? false;
  const byes = byeTeams(teamList, games);

  return (
    <>
      <AppHeader
        title={week.name}
        subtitle={locked
          ? `${alive.length} still alive`
          : `Locks ${formatLockTime(week.lock_at)}`}
        right={<LockChip locked={locked} countdown={countdown(week.lock_at)} />}
      />

      <Screen>
        {/* Current pick summary — the one thing you open the app to check. */}
        <Card className="mt-4 p-4">
          {eliminated ? (
            <div className="flex items-center gap-3">
              <span className="text-2xl">💀</span>
              <div>
                <p className="text-[15px] font-bold text-out">You're eliminated</p>
                <p className="text-[12.5px] text-muted">Stick around and watch the carnage.</p>
              </div>
            </div>
          ) : myPick ? (
            <div className="flex items-center gap-3">
              <TeamTile team={teams[myPick.team_abbr]} size="lg" />
              <div className="min-w-0 flex-1">
                <p className="text-[11px] font-semibold tracking-[0.09em] text-faint uppercase">
                  {locked ? "Your pick" : "Your pick · tap below to change"}
                </p>
                <p className="truncate text-[17px] leading-tight font-bold text-ink">
                  {teams[myPick.team_abbr]?.display_name ?? myPick.team_abbr}
                </p>
              </div>
              {locked && <ResultBadge result={pickResult(myPick.team_abbr, games)} />}
            </div>
          ) : (
            <div className="flex items-center gap-3">
              <span className="text-2xl">{locked ? "❌" : "👇"}</span>
              <div>
                <p className="text-[15px] font-bold text-ink">
                  {locked ? "No pick made" : "Make your pick"}
                </p>
                <p className="text-[12.5px] text-muted">
                  {locked
                    ? "Missing the lock counts as a loss."
                    : `${used.length} of 32 teams used so far.`}
                </p>
              </div>
            </div>
          )}
        </Card>

        <div className="mt-5">
          {viewer ? (
            <PickGrid
              games={games} teams={teams} usedTeams={used}
              currentPick={myPick?.team_abbr ?? null}
              weekId={week.id} locked={locked || eliminated}
            />
          ) : (
            <EmptyState icon="🔒" title="Not signed in"
              body="Set VIEW_AS_EMAIL until auth ships." />
          )}
        </div>

        {byes.length > 0 && (
          <p className="px-1 pt-6 text-[12px] leading-relaxed text-faint">
            <span className="font-semibold text-muted">On bye:</span>{" "}
            {byes.join(" · ")}
          </p>
        )}
      </Screen>
    </>
  );
}
