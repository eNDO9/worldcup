// Round/deadline/lock helpers — ported from logic spread across app.py,
// home.py, pool.py, and bracket.py. All dates handled as ISO strings from
// Postgres (timestamptz) parsed to Date.

export type RoundStatus = "upcoming" | "active" | "locked" | "completed";

export interface Round {
  id: number;
  name: string;
  short_name: string | null;
  deadline: string;
  status: RoundStatus;
}

export interface Match {
  id: number;
  round_id: number;
  team1: string;
  team2: string;
  match_date: string | null;
  kickoff_time: string | null;
  venue: string | null;
  winner: string | null;
}

export interface AppUser {
  id: string;
  email: string;
  is_eliminated: boolean;
  eliminated_round_id: number | null;
  created_at?: string;
}

export interface Pick {
  id: string;
  user_id: string;
  round_id: number;
  team_picked: string;
  created_at?: string;
}

export type PickResult = "won" | "lost" | "pending";

export function displayName(user: { email: string }): string {
  return user.email.split("@")[0];
}

export function parseTs(ts: string): Date {
  return new Date(ts);
}

/** Round is locked for picking: deadline passed or explicitly locked (home.py). */
export function isRoundLocked(round: Round, now: Date = new Date()): boolean {
  return round.status === "locked" || now >= parseTs(round.deadline);
}

/** Round's picks are revealed to everyone (pool.py `_is_closed`). */
export function isRoundClosed(round: Round, now: Date = new Date()): boolean {
  if (round.status === "completed" || round.status === "locked") return true;
  if (round.status === "active") return parseTs(round.deadline) <= now;
  return false;
}

export function matchKickedOff(match: Match, now: Date = new Date()): boolean {
  return !!match.kickoff_time && parseTs(match.kickoff_time) <= now;
}

/** "Jul 9 · 4:00 PM ET" — real America/New_York, not the hardcoded UTC-4. */
export function formatET(ts: string): string {
  const d = parseTs(ts);
  if (isNaN(d.getTime())) return "";
  const date = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/New_York", month: "short", day: "numeric",
  }).format(d);
  const time = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/New_York", hour: "numeric", minute: "2-digit",
  }).format(d);
  return `${date} · ${time} ET`;
}

/** Time-only variant: "4:00 PM ET" (home.py kickoff labels). */
export function formatETTime(ts: string): string {
  const d = parseTs(ts);
  if (isNaN(d.getTime())) return "";
  return `${new Intl.DateTimeFormat("en-US", {
    timeZone: "America/New_York", hour: "numeric", minute: "2-digit",
  }).format(d)} ET`;
}

/** "Jul 9" from a YYYY-MM-DD match_date (home.py date group headers). */
export function formatMatchDate(dateStr: string): string {
  const d = new Date(`${dateStr}T12:00:00Z`);
  if (isNaN(d.getTime())) return dateStr;
  return new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", timeZone: "UTC" }).format(d);
}

/** "2d 5h" or "3h 12m" until the deadline (app.py banner / home.py metric). */
export function countdown(deadline: string, now: Date = new Date()): string {
  const secs = Math.max(0, (parseTs(deadline).getTime() - now.getTime()) / 1000);
  if (secs >= 86400) {
    return `${Math.floor(secs / 86400)}d ${Math.floor((secs % 86400) / 3600)}h`;
  }
  return `${Math.floor(secs / 3600)}h ${Math.floor((secs % 3600) / 60)}m`;
}
