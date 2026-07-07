// Data layer — ported function-for-function from db.py (reads; write
// functions arrive with the pick/admin phases). All queries use the
// service-role client and run server-side only.
import "server-only";
import { getAdminClient } from "./supabase/admin";
import type { AppUser, Match, Pick, PickResult, Round } from "./rounds";

export async function getAllRounds(): Promise<Round[]> {
  const { data, error } = await getAdminClient().from("rounds").select("*").order("id");
  if (error) throw error;
  return (data ?? []) as Round[];
}

export async function getActiveRound(): Promise<Round | null> {
  const { data, error } = await getAdminClient()
    .from("rounds").select("*")
    .in("status", ["active", "locked"])
    .order("id").limit(1);
  if (error) throw error;
  return (data?.[0] ?? null) as Round | null;
}

export async function getMatchesForRound(roundId: number): Promise<Match[]> {
  const { data, error } = await getAdminClient()
    .from("matches").select("*")
    .eq("round_id", roundId)
    .order("match_date");
  if (error) throw error;
  return (data ?? []) as Match[];
}

export async function getUserById(userId: string): Promise<AppUser | null> {
  const { data, error } = await getAdminClient()
    .from("app_users").select("*").eq("id", userId);
  if (error) throw error;
  return (data?.[0] ?? null) as AppUser | null;
}

export async function getUserByEmail(email: string): Promise<AppUser | null> {
  const { data, error } = await getAdminClient()
    .from("app_users").select("*").eq("email", email.toLowerCase().trim());
  if (error) throw error;
  return (data?.[0] ?? null) as AppUser | null;
}

export async function getUserPickForRound(userId: string, roundId: number): Promise<Pick | null> {
  const { data, error } = await getAdminClient()
    .from("picks").select("*")
    .eq("user_id", userId).eq("round_id", roundId);
  if (error) throw error;
  return (data?.[0] ?? null) as Pick | null;
}

export async function getUserAllPicks(userId: string): Promise<Pick[]> {
  const { data, error } = await getAdminClient()
    .from("picks").select("*")
    .eq("user_id", userId).order("round_id");
  if (error) throw error;
  return (data ?? []) as Pick[];
}

export async function getUsedTeams(userId: string): Promise<Set<string>> {
  return new Set((await getUserAllPicks(userId)).map((p) => p.team_picked));
}

export async function getAllPicksForRound(roundId: number): Promise<Pick[]> {
  const { data, error } = await getAdminClient()
    .from("picks").select("*").eq("round_id", roundId);
  if (error) throw error;
  return (data ?? []) as Pick[];
}

export interface Standing extends AppUser {
  picks: Pick[];
}

/** Ported from db.py get_standings: users ordered by email, alive first. */
export async function getStandings(): Promise<Standing[]> {
  const client = getAdminClient();
  const [{ data: users, error: uErr }, { data: picksAll, error: pErr }] = await Promise.all([
    client.from("app_users")
      .select("id, email, is_eliminated, eliminated_round_id, created_at")
      .order("email"),
    client.from("picks").select("*"),
  ]);
  if (uErr) throw uErr;
  if (pErr) throw pErr;

  const picksByUser = new Map<string, Pick[]>();
  for (const p of (picksAll ?? []) as Pick[]) {
    if (!picksByUser.has(p.user_id)) picksByUser.set(p.user_id, []);
    picksByUser.get(p.user_id)!.push(p);
  }

  const result: Standing[] = ((users ?? []) as AppUser[]).map((u) => ({
    ...u,
    picks: (picksByUser.get(u.id) ?? []).sort((a, b) => a.round_id - b.round_id),
  }));

  result.sort((a, b) =>
    Number(a.is_eliminated) - Number(b.is_eliminated) || a.email.localeCompare(b.email));
  return result;
}

/** db.py pick_result, computed over the round's already-fetched matches
 * (same semantics, avoids one query per pick). */
export function pickResult(team: string, roundMatches: Match[]): PickResult {
  const m = roundMatches.find((x) => x.team1 === team || x.team2 === team);
  if (!m || !m.winner) return "pending";
  return m.winner === team ? "won" : "lost";
}
