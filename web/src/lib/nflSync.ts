// Sync engine: pull ESPN results into Supabase, then settle the week.
// Successor to results_sync.py. Every function here is idempotent — the
// page-load sync, a cron, and a manual admin click can all run at once
// without double-eliminating anyone.
import "server-only";
import { getAdminClient } from "./supabase/admin";
import { fetchWeekCached, fetchTeams } from "./espn";
import { getSettings, getWeek, getGamesForWeek, getPicksForWeek, getAliveEntries } from "./nflDb";
import { TIE, isEliminatingResult, pickResult, isWeekLocked } from "./nfl";
import type { Week } from "./nfl";

export interface SyncReport {
  weekNumber: number;
  gamesUpdated: number;
  eliminated: number;
  noPickEliminated: number;
  allOutVoided: boolean;
  weekCompleted: boolean;
}

/** Refresh scores/winners for a week from ESPN. Returns rows changed.
 * Only writes games whose score or status actually moved, so a quiet
 * poll during the week costs one API call and zero writes. */
export async function syncGames(week: Week): Promise<number> {
  const [live, stored] = await Promise.all([
    fetchWeekCached(week.season, week.week_number),
    getGamesForWeek(week.id),
  ]);
  if (live.length === 0) return 0;

  const byEspnId = new Map(stored.map((g) => [g.espn_event_id, g]));
  const changed = live.filter((l) => {
    const cur = byEspnId.get(l.espnEventId);
    if (!cur) return false;
    return cur.status !== l.status
      || cur.home_score !== l.homeScore
      || cur.away_score !== l.awayScore
      || cur.winner !== l.winner;
  });
  if (changed.length === 0) return 0;

  const client = getAdminClient();
  await Promise.all(changed.map((l) =>
    client.from("nfl_games").update({
      home_score: l.homeScore,
      away_score: l.awayScore,
      winner: l.winner,
      status: l.status,
    }).eq("espn_event_id", l.espnEventId)
  ));
  return changed.length;
}

/** Eliminate anyone whose pick has already lost. Runs as results land, so
 * a bad Thursday pick is out Thursday night — not at week's end. */
async function eliminateLosers(week: Week): Promise<number> {
  const [settings, games, picks, alive] = await Promise.all([
    getSettings(), getGamesForWeek(week.id), getPicksForWeek(week.id), getAliveEntries(week.season),
  ]);
  const aliveByUser = new Map(alive.map((e) => [e.user_id, e]));

  const doomed = picks.filter((p) => {
    if (!aliveByUser.has(p.user_id)) return false;
    return isEliminatingResult(pickResult(p.team_abbr, games), settings);
  });
  if (doomed.length === 0) return 0;

  const client = getAdminClient();
  await Promise.all(doomed.map((p) => {
    const reason = pickResult(p.team_abbr, games) === "tied" ? "tie" : "loss";
    return client.from("nfl_entries").update({
      is_eliminated: true,
      eliminated_week_id: week.id,
      eliminated_reason: reason,
    }).eq("user_id", p.user_id).eq("season", week.season).eq("is_eliminated", false);
  }));
  return doomed.length;
}

/** Anyone still alive who never picked before the lock is out. Idempotent:
 * the is_eliminated=false guard means a second run is a no-op. */
async function eliminateNoPicks(week: Week): Promise<number> {
  const settings = await getSettings();
  if (settings.noPickRule !== "eliminate") return 0;
  if (!isWeekLocked(week)) return 0;

  const [picks, alive] = await Promise.all([
    getPicksForWeek(week.id), getAliveEntries(week.season),
  ]);
  const picked = new Set(picks.map((p) => p.user_id));
  const missing = alive.filter((e) => !picked.has(e.user_id));
  if (missing.length === 0) return 0;

  const client = getAdminClient();
  await Promise.all(missing.map((e) =>
    client.from("nfl_entries").update({
      is_eliminated: true,
      eliminated_week_id: week.id,
      eliminated_reason: "no_pick",
    }).eq("id", e.id).eq("is_eliminated", false)
  ));
  return missing.length;
}

/** Every remaining player went out in the same week. Under the default
 * 'void' rule the week is rolled back and everyone who entered it survives
 * — otherwise the pool ends with nobody standing. */
async function handleAllOut(week: Week, aliveBefore: number): Promise<boolean> {
  const settings = await getSettings();
  if (settings.allOutRule !== "void" || aliveBefore === 0) return false;

  const stillAlive = await getAliveEntries(week.season);
  if (stillAlive.length > 0) return false;

  const { error } = await getAdminClient()
    .from("nfl_entries")
    .update({ is_eliminated: false, eliminated_week_id: null, eliminated_reason: null })
    .eq("season", week.season)
    .eq("eliminated_week_id", week.id);
  return !error;
}

const allGamesFinal = (games: { status: string }[]) =>
  games.length > 0 && games.every((g) => g.status === "final");

/** Full pass for one week: scores -> eliminations -> all-out check ->
 * status roll-forward. Safe to call on every page load. */
export async function syncWeek(weekId: number): Promise<SyncReport | null> {
  const week = await getWeek(weekId);
  if (!week) return null;

  const aliveBefore = (await getAliveEntries(week.season)).length;
  const gamesUpdated = await syncGames(week);

  const client = getAdminClient();
  if (isWeekLocked(week) && week.status === "active") {
    await client.from("nfl_weeks").update({ status: "locked" }).eq("id", week.id);
    week.status = "locked";
  }

  const noPickEliminated = await eliminateNoPicks(week);
  const eliminated = await eliminateLosers(week);
  const allOutVoided = await handleAllOut(week, aliveBefore);

  // Close the week and open the next one only when every game is final.
  const games = await getGamesForWeek(week.id);
  let weekCompleted = false;
  if (allGamesFinal(games) && week.status !== "completed") {
    await client.from("nfl_weeks").update({ status: "completed" }).eq("id", week.id);
    await client.from("nfl_weeks").update({ status: "active" })
      .eq("season", week.season).eq("week_number", week.week_number + 1)
      .eq("status", "upcoming");
    weekCompleted = true;
  }

  return {
    weekNumber: week.week_number,
    gamesUpdated,
    eliminated,
    noPickEliminated,
    allOutVoided,
    weekCompleted,
  };
}

/** Refresh team names/colors from ESPN. Rarely needed — rebrands only. */
export async function syncTeams(): Promise<number> {
  const teams = await fetchTeams();
  if (teams.length === 0) return 0;
  const { error } = await getAdminClient().from("nfl_teams").upsert(
    teams.map((t) => ({
      abbr: t.abbr, location: t.location, nickname: t.nickname,
      display_name: t.displayName, color: t.color, alt_color: t.altColor,
    })),
    { onConflict: "abbr" },
  );
  return error ? 0 : teams.length;
}

export { TIE };
