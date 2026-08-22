// ESPN NFL scoreboard client — replaces the football-data.org integration
// in resultsSync.ts (World Cup).
//
// This is ESPN's public, undocumented site API: no key, no quota, and no
// stability guarantee. Every field access below is defensive because the
// shape can change without notice; a bad response degrades to an empty
// result rather than throwing into a page render.
import "server-only";
import { ttlCached } from "./ttlCache";
import { TIE } from "./nfl";

const BASE = "https://site.api.espn.com/apis/site/v2/sports/football/nfl";

/** ESPN seasontype: 1 = pre, 2 = regular, 3 = post. */
export const SEASON_REGULAR = 2;
export const SEASON_POST = 3;

export interface EspnGame {
  espnEventId: string;
  homeAbbr: string;
  awayAbbr: string;
  kickoff: string;
  homeScore: number | null;
  awayScore: number | null;
  /** Team abbr, TIE, or null while the game is not final. */
  winner: string | null;
  status: "scheduled" | "in_progress" | "final";
}

export interface EspnTeam {
  abbr: string;
  location: string;
  nickname: string;
  displayName: string;
  color: string | null;
  altColor: string | null;
}

interface RawCompetitor {
  homeAway?: string;
  score?: string | number;
  winner?: boolean;
  team?: { abbreviation?: string };
}

interface RawEvent {
  id?: string;
  date?: string;
  competitions?: {
    competitors?: RawCompetitor[];
    status?: { type?: { state?: string; completed?: boolean } };
  }[];
  status?: { type?: { state?: string; completed?: boolean } };
}

async function getJson<T>(url: string): Promise<T | null> {
  try {
    const resp = await fetch(url, {
      headers: { "User-Agent": "worldcup-survivor/1.0" },
      signal: AbortSignal.timeout(15_000),
      cache: "no-store",
    });
    if (!resp.ok) return null;
    return (await resp.json()) as T;
  } catch {
    return null;
  }
}

const num = (v: string | number | undefined): number | null => {
  if (v === undefined || v === null || v === "") return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
};

function mapStatus(state?: string, completed?: boolean): EspnGame["status"] {
  if (completed || state === "post") return "final";
  if (state === "in") return "in_progress";
  return "scheduled";
}

function toGame(ev: RawEvent): EspnGame | null {
  const comp = ev.competitions?.[0];
  const id = ev.id;
  const kickoff = ev.date;
  if (!comp || !id || !kickoff) return null;

  const home = comp.competitors?.find((c) => c.homeAway === "home");
  const away = comp.competitors?.find((c) => c.homeAway === "away");
  const homeAbbr = home?.team?.abbreviation;
  const awayAbbr = away?.team?.abbreviation;
  if (!homeAbbr || !awayAbbr) return null;

  const status = mapStatus(
    comp.status?.type?.state ?? ev.status?.type?.state,
    comp.status?.type?.completed ?? ev.status?.type?.completed,
  );
  const homeScore = num(home?.score);
  const awayScore = num(away?.score);

  // Winner only once final. ESPN sets competitor.winner, but it is absent on
  // a tie — so fall back to comparing scores, which is where TIE comes from.
  let winner: string | null = null;
  if (status === "final") {
    if (home?.winner) winner = homeAbbr;
    else if (away?.winner) winner = awayAbbr;
    else if (homeScore !== null && awayScore !== null) {
      winner = homeScore > awayScore ? homeAbbr
        : awayScore > homeScore ? awayAbbr
        : TIE;
    }
  }

  return { espnEventId: id, homeAbbr, awayAbbr, kickoff, homeScore, awayScore, winner, status };
}

/** Every game in one week. Empty array on any API failure — callers treat
 * that as "no new information", never as "all games cancelled". */
export async function fetchWeek(
  season: number,
  week: number,
  seasonType: number = SEASON_REGULAR,
): Promise<EspnGame[]> {
  const body = await getJson<{ events?: RawEvent[] }>(
    `${BASE}/scoreboard?dates=${season}&seasontype=${seasonType}&week=${week}`,
  );
  if (!body?.events) return [];
  return body.events.map(toGame).filter((g): g is EspnGame => g !== null);
}

/** Whole regular season (weeks 1-18) — used by the seeder, not per-request. */
export async function fetchSeason(season: number): Promise<Map<number, EspnGame[]>> {
  const weeks = Array.from({ length: 18 }, (_, i) => i + 1);
  const results = await Promise.all(weeks.map((w) => fetchWeek(season, w)));
  return new Map(weeks.map((w, i) => [w, results[i]]));
}

/** Team metadata for the trademark-safe UI: names and colors, no logos. */
export async function fetchTeams(): Promise<EspnTeam[]> {
  const body = await getJson<{
    sports?: { leagues?: { teams?: { team?: {
      abbreviation?: string; location?: string; name?: string;
      displayName?: string; color?: string; alternateColor?: string;
    } }[] }[] }[];
  }>(`${BASE}/teams?limit=40`);

  const raw = body?.sports?.[0]?.leagues?.[0]?.teams ?? [];
  return raw.flatMap((entry) => {
    const t = entry.team;
    if (!t?.abbreviation || !t.location || !t.name) return [];
    return [{
      abbr: t.abbreviation,
      location: t.location,
      nickname: t.name,
      displayName: t.displayName ?? `${t.location} ${t.name}`,
      color: t.color ? `#${t.color}` : null,
      altColor: t.alternateColor ? `#${t.alternateColor}` : null,
    }];
  });
}

/** Live scores for one week, memoized 30s so a burst of page loads during
 * Sunday afternoon games hits ESPN once per week, not once per render.
 * The memo is keyed — ttlCached only wraps zero-arg functions, so each
 * (season, week) needs its own retained instance. */
const weekMemos = new Map<string, () => Promise<EspnGame[]>>();

export function fetchWeekCached(season: number, week: number): Promise<EspnGame[]> {
  const key = `${season}:${week}`;
  let memo = weekMemos.get(key);
  if (!memo) {
    memo = ttlCached(30, () => fetchWeek(season, week));
    weekMemos.set(key, memo);
  }
  return memo();
}
