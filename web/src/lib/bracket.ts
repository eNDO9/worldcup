// Bracket layout algorithms — ported line-for-line from bracket.py.
import type { Match, Round } from "./rounds";
import type { StageFixture } from "./resultsSync";

export const EXPECTED: Record<string, number> = { R32: 16, R16: 8, QF: 4, SF: 2, F: 1 };
export const ROW_H = 90;

export interface BracketItem {
  team1: string | null;
  team2: string | null;
  winner: string | null;
  kickoff_time?: string | null;
  match_date?: string | null;
}

export interface BracketColumn {
  title: string;
  anyTeams: boolean;
  items: BracketItem[];
}

/** Order `earlier`-round matches so each pair feeds a `later` match in order. */
export function feederOrder(earlier: Match[], later: BracketItem[]): Match[] {
  const byTeam = new Map<string, Match>();
  for (const m of earlier) {
    if (!byTeam.has(m.team1)) byTeam.set(m.team1, m);
    if (!byTeam.has(m.team2)) byTeam.set(m.team2, m);
  }
  const ordered: Match[] = [];
  const seen = new Set<number>();
  for (const lm of later) {
    for (const t of [lm.team1, lm.team2]) {
      const em = t ? byTeam.get(t) : undefined;
      if (em && !seen.has(em.id)) {
        ordered.push(em);
        seen.add(em.id);
      }
    }
  }
  for (const m of earlier) {
    if (!seen.has(m.id)) ordered.push(m); // any that didn't map (safety) go last
  }
  return ordered;
}

const pairKey = (a: string, b: string) => [a, b].sort().join("|");

export function buildBracketColumns(
  rounds: Round[],
  matchesByRound: Map<number, Match[]>,
  apiByStage: Record<string, StageFixture[]>,
): BracketColumn[] {
  // Right-to-left: keep the rightmost populated round in id order, then order
  // each earlier round so its matches sit next to the later match they feed.
  const orderedByRound = new Map<number, Match[] | null>();
  let nextOrdered: Match[] | null = null;
  for (const r of [...rounds].reverse()) {
    const ms = matchesByRound.get(r.id) ?? [];
    if (ms.length) {
      const arr: Match[] = nextOrdered
        ? feederOrder(ms, nextOrdered)
        : [...ms].sort((a, b) => a.id - b.id);
      orderedByRound.set(r.id, arr);
      nextOrdered = arr;
    } else {
      orderedByRound.set(r.id, null);
    }
  }

  const cols: BracketColumn[] = [];
  let prevShown: BracketItem[] | null = null;

  for (const r of rounds) {
    const sn = r.short_name ?? "";
    const ms: Match[] = orderedByRound.get(r.id) ?? [];
    const n = Math.max(EXPECTED[sn] ?? 0, ms.length);

    let shown: BracketItem[];
    if (ms.length && ms.length >= n) {
      shown = [...ms];
    } else {
      // Pad the round to full size: DB matches go to their bracket slot (the
      // one below their feeder pair), then API fixtures — whose teams appear
      // the moment a feeder match is decided — then blank TBD cards.
      const dbPairs = new Set(ms.map((m) => pairKey(m.team1, m.team2)));
      const api = (apiByStage[sn] ?? []).filter(
        (a) => !(a.team1 && a.team2 && dbPairs.has(pairKey(a.team1, a.team2))),
      );

      const teamSlot = new Map<string, number>(); // prev-column team -> slot it feeds here
      prevShown?.forEach((pm, idx) => {
        for (const t of [pm.team1, pm.team2]) {
          if (t) teamSlot.set(t, Math.floor(idx / 2));
        }
      });

      const slots: (BracketItem | null)[] = Array(n).fill(null);
      const leftovers: BracketItem[] = [];
      for (const item of [...(ms as BracketItem[]), ...api]) {
        let s: number | null = null;
        for (const t of [item.team1, item.team2]) {
          if (t && teamSlot.has(t)) { s = teamSlot.get(t)!; break; }
        }
        if (s !== null && s < n && slots[s] === null) slots[s] = item;
        else leftovers.push(item);
      }
      leftovers.sort((a, b) =>
        (a.kickoff_time ?? "").localeCompare(b.kickoff_time ?? ""));
      for (let i = 0; i < n; i++) {
        if (slots[i] === null && leftovers.length) slots[i] = leftovers.shift()!;
      }
      shown = slots.map((s) => (s ? { ...s } : { team1: null, team2: null, winner: null }));

      // Advance a lone winner even before the API names it: when exactly one
      // matchup here is still fully unknown, its feeders must be the two
      // previous-round matches none of whose teams appear in this column —
      // so any decided winner among them belongs in it.
      if (prevShown) {
        const known = new Set(
          shown.flatMap((it) => [it.team1, it.team2]).filter((t): t is string => !!t));
        const unknown = shown.filter((it) => !it.team1 && !it.team2);
        if (unknown.length === 1) {
          const feeders = prevShown.filter(
            (pm) => (pm.team1 || pm.team2) &&
              ![pm.team1, pm.team2].some((t) => t && known.has(t)));
          if (feeders.length === 2) {
            unknown[0].team1 = feeders[0].winner ?? null;
            unknown[0].team2 = feeders[1].winner ?? null;
          }
        }
      }
    }

    cols.push({
      title: r.short_name ?? r.name,
      anyTeams: shown.some((it) => it.team1 || it.team2),
      items: shown,
    });
    prevShown = shown;
  }
  return cols;
}
