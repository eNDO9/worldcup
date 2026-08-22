// NFL survivor domain types + the week/lock helpers the whole app hangs off.
// Successor to rounds.ts (World Cup). The one rule that drives everything:
// a week's lock_at is the kickoff of its FIRST game. Picks close then, and
// every pick becomes visible at that same instant.

export type WeekStatus = "upcoming" | "active" | "locked" | "completed";
export type GameStatus = "scheduled" | "in_progress" | "final";
export type PickResult = "won" | "lost" | "tied" | "pending";
export type EliminatedReason = "loss" | "tie" | "no_pick";

export interface Team {
  abbr: string;
  location: string;
  nickname: string;
  display_name: string;
  color: string | null;
  alt_color: string | null;
}

export interface Week {
  id: number;
  season: number;
  week_number: number;
  name: string;
  lock_at: string;
  status: WeekStatus;
}

export interface Game {
  id: number;
  week_id: number;
  espn_event_id: string | null;
  home_abbr: string;
  away_abbr: string;
  kickoff: string;
  home_score: number | null;
  away_score: number | null;
  /** Winning team abbr, or "TIE" when final and level. Null until final. */
  winner: string | null;
  status: GameStatus;
}

export interface Entry {
  id: string;
  user_id: string;
  season: number;
  is_eliminated: boolean;
  eliminated_week_id: number | null;
  eliminated_reason: EliminatedReason | null;
}

export interface NflPick {
  id: string;
  user_id: string;
  week_id: number;
  season: number;
  team_abbr: string;
  created_at?: string;
}

/** Rule knobs from nfl_settings, so they change without a deploy. */
export interface PoolSettings {
  season: number;
  tieRule: "loss" | "survive";
  allOutRule: "void" | "eliminate";
  includePlayoffs: boolean;
  noPickRule: "eliminate" | "auto";
}

export const DEFAULT_SETTINGS: PoolSettings = {
  season: 2026,
  tieRule: "loss",
  allOutRule: "void",
  includePlayoffs: false,
  noPickRule: "eliminate",
};

export const TIE = "TIE";

export const parseTs = (ts: string): Date => new Date(ts);

// --- lock / reveal ---------------------------------------------------------

/** Picks are closed. Same instant as the reveal — that is the whole point. */
export function isWeekLocked(week: Week, now: Date = new Date()): boolean {
  return week.status === "locked" || week.status === "completed"
    || now >= parseTs(week.lock_at);
}

/** Everyone's picks are visible. Deliberately identical to isWeekLocked:
 * one timestamp, no window where picks are closed but still secret. */
export const arePicksRevealed = isWeekLocked;

export function hasKickedOff(game: Game, now: Date = new Date()): boolean {
  return parseTs(game.kickoff) <= now;
}

// --- results ---------------------------------------------------------------

/** The game a team plays in a given week, or undefined on their bye. */
export function gameForTeam(team: string, games: Game[]): Game | undefined {
  return games.find((g) => g.home_abbr === team || g.away_abbr === team);
}

/** Teams with no game this week — must be excluded from the pick grid. */
export function byeTeams(allTeams: Team[], games: Game[]): string[] {
  const playing = new Set(games.flatMap((g) => [g.home_abbr, g.away_abbr]));
  return allTeams.map((t) => t.abbr).filter((a) => !playing.has(a));
}

/** How a pick turned out. A tie is reported as "tied"; whether that kills
 * the entry is settings.tieRule's call, applied in the sync layer. */
export function pickResult(team: string, games: Game[]): PickResult {
  const g = gameForTeam(team, games);
  if (!g || g.status !== "final" || !g.winner) return "pending";
  if (g.winner === TIE) return "tied";
  return g.winner === team ? "won" : "lost";
}

export function isEliminatingResult(r: PickResult, s: PoolSettings): boolean {
  return r === "lost" || (r === "tied" && s.tieRule === "loss");
}

// --- formatting ------------------------------------------------------------

const et = (opts: Intl.DateTimeFormatOptions) =>
  new Intl.DateTimeFormat("en-US", { timeZone: "America/New_York", ...opts });

/** "Sun 1:00 PM" — the compact form the mobile pick rows use. */
export function formatKickoff(ts: string): string {
  const d = parseTs(ts);
  if (isNaN(d.getTime())) return "";
  return `${et({ weekday: "short" }).format(d)} ${et({ hour: "numeric", minute: "2-digit" }).format(d)}`;
}

/** "Thu, Sep 10 · 8:20 PM ET" — full form for the lock banner. */
export function formatLockTime(ts: string): string {
  const d = parseTs(ts);
  if (isNaN(d.getTime())) return "";
  return `${et({ weekday: "short", month: "short", day: "numeric" }).format(d)}`
    + ` · ${et({ hour: "numeric", minute: "2-digit" }).format(d)} ET`;
}

/** Day bucket key for grouping a week's games: "Sunday, Sep 13". */
export function dayLabel(ts: string): string {
  const d = parseTs(ts);
  if (isNaN(d.getTime())) return "";
  return et({ weekday: "long", month: "short", day: "numeric" }).format(d);
}

/** "2d 5h", "3h 12m", "4m" — granularity tightens as the lock approaches. */
export function countdown(lockAt: string, now: Date = new Date()): string {
  const secs = Math.max(0, (parseTs(lockAt).getTime() - now.getTime()) / 1000);
  if (secs >= 86400) return `${Math.floor(secs / 86400)}d ${Math.floor((secs % 86400) / 3600)}h`;
  if (secs >= 3600) return `${Math.floor(secs / 3600)}h ${Math.floor((secs % 3600) / 60)}m`;
  return `${Math.floor(secs / 60)}m`;
}

export function displayName(user: { email: string }): string {
  return user.email.split("@")[0];
}
