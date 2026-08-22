// Data layer for the NFL survivor pool. Successor to db.ts (World Cup).
// Server-only: every query runs through the secret-key client, and picks
// are never exposed to a client component before their week locks.
import "server-only";
import { getAdminClient } from "./supabase/admin";
import { DEFAULT_SETTINGS, arePicksRevealed, pickResult } from "./nfl";
import type {
  Entry, Game, NflPick, PoolSettings, Team, Week, PickResult,
} from "./nfl";

// --- settings --------------------------------------------------------------

export async function getSettings(): Promise<PoolSettings> {
  const { data, error } = await getAdminClient().from("nfl_settings").select("key, value");
  if (error || !data) return DEFAULT_SETTINGS;
  const m = new Map(data.map((r) => [r.key as string, r.value as string]));
  const pick = <T extends string>(k: string, fallback: T, allowed: readonly T[]): T => {
    const v = m.get(k) as T | undefined;
    return v && allowed.includes(v) ? v : fallback;
  };
  return {
    season: Number(m.get("season")) || DEFAULT_SETTINGS.season,
    tieRule: pick("tie_rule", DEFAULT_SETTINGS.tieRule, ["loss", "survive"] as const),
    allOutRule: pick("all_out_rule", DEFAULT_SETTINGS.allOutRule, ["void", "eliminate"] as const),
    includePlayoffs: m.get("include_playoffs") === "true",
    noPickRule: pick("no_pick_rule", DEFAULT_SETTINGS.noPickRule, ["eliminate", "auto"] as const),
  };
}

// --- reference data --------------------------------------------------------

export async function getTeams(): Promise<Team[]> {
  const { data, error } = await getAdminClient()
    .from("nfl_teams").select("*").order("abbr");
  if (error) throw error;
  return (data ?? []) as Team[];
}

export async function getWeek(weekId: number): Promise<Week | null> {
  const { data, error } = await getAdminClient()
    .from("nfl_weeks").select("*").eq("id", weekId).limit(1);
  if (error) throw error;
  return (data?.[0] ?? null) as Week | null;
}

export async function getAllWeeks(season: number): Promise<Week[]> {
  const { data, error } = await getAdminClient()
    .from("nfl_weeks").select("*").eq("season", season).order("week_number");
  if (error) throw error;
  return (data ?? []) as Week[];
}

/** The week the app should show: the one in play, else the next one up,
 * else the last of the season once it is over. */
export async function getCurrentWeek(season: number): Promise<Week | null> {
  const weeks = await getAllWeeks(season);
  if (weeks.length === 0) return null;
  return weeks.find((w) => w.status === "active" || w.status === "locked")
    ?? weeks.find((w) => w.status === "upcoming")
    ?? weeks[weeks.length - 1];
}

export async function getGamesForWeek(weekId: number): Promise<Game[]> {
  const { data, error } = await getAdminClient()
    .from("nfl_games").select("*").eq("week_id", weekId).order("kickoff");
  if (error) throw error;
  return (data ?? []) as Game[];
}

// --- entries ---------------------------------------------------------------

export async function getEntry(userId: string, season: number): Promise<Entry | null> {
  const { data, error } = await getAdminClient()
    .from("nfl_entries").select("*").eq("user_id", userId).eq("season", season).limit(1);
  if (error) throw error;
  return (data?.[0] ?? null) as Entry | null;
}

export async function getAliveEntries(season: number): Promise<Entry[]> {
  const { data, error } = await getAdminClient()
    .from("nfl_entries").select("*").eq("season", season).eq("is_eliminated", false);
  if (error) throw error;
  return (data ?? []) as Entry[];
}

/** Join an entry to the season. Idempotent via the (user_id, season) key. */
export async function ensureEntry(userId: string, season: number): Promise<Entry> {
  const existing = await getEntry(userId, season);
  if (existing) return existing;
  const { data, error } = await getAdminClient()
    .from("nfl_entries").insert({ user_id: userId, season }).select().limit(1);
  if (error) throw error;
  return data![0] as Entry;
}

// --- picks -----------------------------------------------------------------

export async function getPicksForWeek(weekId: number): Promise<NflPick[]> {
  const { data, error } = await getAdminClient()
    .from("nfl_picks").select("*").eq("week_id", weekId);
  if (error) throw error;
  return (data ?? []) as NflPick[];
}

export async function getUserPick(userId: string, weekId: number): Promise<NflPick | null> {
  const { data, error } = await getAdminClient()
    .from("nfl_picks").select("*").eq("user_id", userId).eq("week_id", weekId).limit(1);
  if (error) throw error;
  return (data?.[0] ?? null) as NflPick | null;
}

export async function getUserPicks(userId: string, season: number): Promise<NflPick[]> {
  const { data, error } = await getAdminClient()
    .from("nfl_picks").select("*")
    .eq("user_id", userId).eq("season", season).order("week_id");
  if (error) throw error;
  return (data ?? []) as NflPick[];
}

/** Teams this user has already burned — the core survivor constraint. */
export async function getUsedTeams(userId: string, season: number): Promise<Set<string>> {
  return new Set((await getUserPicks(userId, season)).map((p) => p.team_abbr));
}

export type SavePickError =
  | "locked" | "team_used" | "team_on_bye" | "eliminated" | "unknown";

/** Save or change a pick. Re-checks every rule server-side: the client is
 * never trusted about the lock, and the DB's UNIQUE constraints are the
 * final backstop if two requests race. */
export async function savePick(
  userId: string, week: Week, teamAbbr: string,
): Promise<{ ok: true; pick: NflPick } | { ok: false; error: SavePickError }> {
  if (arePicksRevealed(week)) return { ok: false, error: "locked" };

  const entry = await getEntry(userId, week.season);
  if (entry?.is_eliminated) return { ok: false, error: "eliminated" };

  const games = await getGamesForWeek(week.id);
  const playing = new Set(games.flatMap((g) => [g.home_abbr, g.away_abbr]));
  if (!playing.has(teamAbbr)) return { ok: false, error: "team_on_bye" };

  const used = await getUsedTeams(userId, week.season);
  const current = await getUserPick(userId, week.id);
  if (used.has(teamAbbr) && current?.team_abbr !== teamAbbr) {
    return { ok: false, error: "team_used" };
  }

  const { data, error } = await getAdminClient().from("nfl_picks").upsert(
    {
      user_id: userId, week_id: week.id, season: week.season,
      team_abbr: teamAbbr, updated_at: new Date().toISOString(),
    },
    { onConflict: "user_id,week_id" },
  ).select().limit(1);

  if (error) {
    // 23505 = unique violation, i.e. the no-reuse index caught a race.
    return { ok: false, error: error.code === "23505" ? "team_used" : "unknown" };
  }
  return { ok: true, pick: data![0] as NflPick };
}

// --- standings -------------------------------------------------------------

export interface Standing {
  userId: string;
  email: string;
  isEliminated: boolean;
  eliminatedWeekId: number | null;
  eliminatedReason: Entry["eliminated_reason"];
  /** week_id -> pick. Only weeks already revealed are present. */
  picksByWeek: Map<number, { team: string; result: PickResult }>;
  /** This week's pick, or null if hidden/not made. */
  currentPick: string | null;
  hasPickedThisWeek: boolean;
}

/** Everyone's season, with the reveal rule applied per week: a pick is only
 * included once its own week has locked. Before that the pool sees that a
 * player HAS picked, never what. */
export async function getStandings(season: number, currentWeek: Week | null): Promise<Standing[]> {
  const client = getAdminClient();
  const [weeks, { data: users, error: uErr }, { data: picks, error: pErr },
         { data: entries, error: eErr }] = await Promise.all([
    getAllWeeks(season),
    client.from("app_users").select("id, email").order("email"),
    client.from("nfl_picks").select("*").eq("season", season),
    client.from("nfl_entries").select("*").eq("season", season),
  ]);
  if (uErr) throw uErr;
  if (pErr) throw pErr;
  if (eErr) throw eErr;

  const revealed = new Set(weeks.filter((w) => arePicksRevealed(w)).map((w) => w.id));
  const gamesByWeek = new Map<number, Game[]>(
    await Promise.all([...revealed].map(async (id) =>
      [id, await getGamesForWeek(id)] as [number, Game[]])),
  );
  const entryByUser = new Map((entries ?? []).map((e) => [e.user_id as string, e as Entry]));
  const picksByUser = new Map<string, NflPick[]>();
  for (const p of (picks ?? []) as NflPick[]) {
    if (!picksByUser.has(p.user_id)) picksByUser.set(p.user_id, []);
    picksByUser.get(p.user_id)!.push(p);
  }

  const rows: Standing[] = ((users ?? []) as { id: string; email: string }[])
    .filter((u) => entryByUser.has(u.id))
    .map((u) => {
      const entry = entryByUser.get(u.id)!;
      const mine = picksByUser.get(u.id) ?? [];
      const picksByWeek = new Map<number, { team: string; result: PickResult }>();
      for (const p of mine) {
        if (!revealed.has(p.week_id)) continue;
        picksByWeek.set(p.week_id, {
          team: p.team_abbr,
          result: pickResult(p.team_abbr, gamesByWeek.get(p.week_id) ?? []),
        });
      }
      const thisWeek = currentWeek ? mine.find((p) => p.week_id === currentWeek.id) : undefined;
      return {
        userId: u.id,
        email: u.email,
        isEliminated: entry.is_eliminated,
        eliminatedWeekId: entry.eliminated_week_id,
        eliminatedReason: entry.eliminated_reason,
        picksByWeek,
        currentPick: thisWeek && currentWeek && revealed.has(currentWeek.id)
          ? thisWeek.team_abbr : null,
        hasPickedThisWeek: !!thisWeek,
      };
    });

  rows.sort((a, b) =>
    Number(a.isEliminated) - Number(b.isEliminated)
    || b.picksByWeek.size - a.picksByWeek.size
    || a.email.localeCompare(b.email));
  return rows;
}
