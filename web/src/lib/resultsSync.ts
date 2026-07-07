// football-data.org integration — ported from results_sync.py.
// Phase 1 needs fetchFixtures (bracket overlay); propose/apply/buildNextRound
// arrive with the admin/sync phase.
import "server-only";
import { ttlCached } from "./ttlCache";

const API_BASE = "https://api.football-data.org/v4";
const WC_COMPETITION = "WC";

// football-data.org team name -> our DB team name (results_sync.py NAME_MAP)
export const NAME_MAP: Record<string, string> = {
  USA: "United States",
  "Côte d'Ivoire": "Ivory Coast",
  "Cote d'Ivoire": "Ivory Coast",
  "Cabo Verde": "Cape Verde",
  "Cape Verde Islands": "Cape Verde",
  "Congo DR": "DR Congo",
  "Bosnia-Herzegovina": "Bosnia and Herzegovina",
};

const norm = (name: string): string => NAME_MAP[name] ?? name;

// Our round short_name -> football-data.org stage label
export const STAGE_MAP: Record<string, string> = {
  R32: "LAST_32", R16: "LAST_16", QF: "QUARTER_FINALS",
  SF: "SEMI_FINALS", F: "FINAL",
};

export interface Fixture {
  stage: string | null;
  home: string | null;
  away: string | null;
  utc: string | null;
}

/** Every WC fixture, names normalized. home/away are null until the bracket
 * resolves them — the API fills each side the moment it's determined. */
export async function fetchFixtures(): Promise<Fixture[]> {
  const token = process.env.FOOTBALL_DATA_TOKEN;
  if (!token) return [];
  try {
    const resp = await fetch(`${API_BASE}/competitions/${WC_COMPETITION}/matches`, {
      headers: { "X-Auth-Token": token },
      signal: AbortSignal.timeout(15_000),
      cache: "no-store",
    });
    if (!resp.ok) return [];
    const body = (await resp.json()) as {
      matches?: { stage?: string; utcDate?: string;
        homeTeam?: { name?: string | null }; awayTeam?: { name?: string | null } }[];
    };
    return (body.matches ?? []).map((m) => ({
      stage: m.stage ?? null,
      home: m.homeTeam?.name ? norm(m.homeTeam.name) : null,
      away: m.awayTeam?.name ? norm(m.awayTeam.name) : null,
      utc: m.utcDate ?? null,
    }));
  } catch {
    return [];
  }
}

export interface StageFixture {
  team1: string | null;
  team2: string | null;
  kickoff_time: string | null;
  winner: null;
}

/** bracket.py api_fixtures(): fixtures grouped by our stage short-name,
 * sorted by kickoff. Cached ~5 min. */
export const fixturesByStage = ttlCached(300, async (): Promise<Record<string, StageFixture[]>> => {
  const byStage: Record<string, string> = Object.fromEntries(
    Object.entries(STAGE_MAP).map(([sn, stage]) => [stage, sn]));
  const out: Record<string, StageFixture[]> = {};
  for (const fx of await fetchFixtures()) {
    const sn = fx.stage ? byStage[fx.stage] : undefined;
    if (!sn) continue;
    (out[sn] ??= []).push({
      team1: fx.home, team2: fx.away, kickoff_time: fx.utc, winner: null,
    });
  }
  for (const sn of Object.keys(out)) {
    out[sn].sort((a, b) => (a.kickoff_time ?? "").localeCompare(b.kickoff_time ?? ""));
  }
  return out;
});
