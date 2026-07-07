// ← bracket.py. Server component; layout math in lib/bracket.ts.
import { PageTitle } from "@/components/ui";
import { buildBracketColumns, EXPECTED, ROW_H, type BracketItem } from "@/lib/bracket";
import { getAllRounds, getMatchesForRound, getUserAllPicks } from "@/lib/db";
import { flag } from "@/lib/flags";
import { formatET, formatMatchDate, type Match } from "@/lib/rounds";
import { fixturesByStage } from "@/lib/resultsSync";
import { getViewer } from "@/lib/viewer";
import styles from "./bracket.module.css";

export const dynamic = "force-dynamic";

function matchWhen(m: BracketItem): string {
  if (m.kickoff_time) {
    const when = formatET(m.kickoff_time);
    if (when) return when;
  }
  return m.match_date ? formatMatchDate(m.match_date) : "";
}

function TeamRow({ team, winner, myTeam }: {
  team: string | null; winner: string | null; myTeam: string | null;
}) {
  if (!team) {
    return <div className={`${styles.bteam} ${styles.tbd}`}>🏳️ <span>TBD</span></div>;
  }
  const cls = [
    styles.bteam,
    winner === team ? styles.win : winner ? styles.lose : "",
    team === myTeam ? styles.mine : "",
  ].join(" ");
  return (
    <div className={cls}>
      {flag(team)}{" "}
      <span>
        {team}
        {team === myTeam && <span className={styles.mystar}> ★</span>}
      </span>
    </div>
  );
}

export default async function BracketPage() {
  const viewer = (await getViewer())!;
  const rounds = await getAllRounds();
  const matchesEntries = await Promise.all(
    rounds.map(async (r) => [r.id, await getMatchesForRound(r.id)] as [number, Match[]]));
  const matchesByRound = new Map(matchesEntries);
  const [apiByStage, myPicksList] = await Promise.all([
    fixturesByStage(), getUserAllPicks(viewer.id),
  ]);
  const myPicks = new Map(myPicksList.map((p) => [p.round_id, p.team_picked]));

  const cols = buildBracketColumns(rounds, matchesByRound, apiByStage);
  // Bracket height must fit the first (largest) round's cards without overlap.
  const height = EXPECTED.R32 * ROW_H + 34;

  return (
    <>
      <PageTitle>🗓️ Bracket</PageTitle>
      <div className={styles.scroll}>
        <div className={styles.bracket} style={{ height }}>
          {cols.map((col, ci) => {
            const round = rounds[ci];
            const myTeam = myPicks.get(round.id) ?? null;
            return (
              <div key={col.title}
                   className={`${styles.bcol} ${col.anyTeams ? "" : styles.bcolEmpty}`}>
                <div className={styles.title}>{col.title}</div>
                <div className={styles.body}>
                  {col.items.map((m, i) => {
                    const when = matchWhen(m);
                    return (
                      <div key={i} className={styles.bmatch}>
                        <div className={styles.bcard}>
                          {when && <div className={styles.bdate}>{when}</div>}
                          <TeamRow team={m.team1} winner={m.winner} myTeam={myTeam} />
                          <TeamRow team={m.team2} winner={m.winner} myTeam={myTeam} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </>
  );
}
