// ← home.py, Phase 1: read-only (metrics, current pick, history, and the
// match grid rendered without actions). Interactive picking lands in Phase 3.
import { Badge, Card, Metric, PageTitle, TeamLabel } from "@/components/ui";
import {
  getActiveRound, getAllRounds, getMatchesForRound, getUserAllPicks,
  getUserPickForRound, getUsedTeams, pickResult,
} from "@/lib/db";
import { flag } from "@/lib/flags";
import {
  countdown, formatET, formatETTime, formatMatchDate, isRoundLocked,
  matchKickedOff, parseTs, type Match,
} from "@/lib/rounds";
import { getViewer } from "@/lib/viewer";

export const dynamic = "force-dynamic";

export default async function PickPage() {
  const viewer = (await getViewer())!;
  const [activeRound, allRounds, allPicks] = await Promise.all([
    getActiveRound(), getAllRounds(), getUserAllPicks(viewer.id),
  ]);
  const roundsMap = new Map(allRounds.map((r) => [r.id, r]));

  const now = new Date();
  let roundSection: React.ReactNode;
  const activeMatches = activeRound ? await getMatchesForRound(activeRound.id) : [];

  if (activeRound) {
    const locked = isRoundLocked(activeRound, now);
    const existingPick = await getUserPickForRound(viewer.id, activeRound.id);
    const usedTeams = await getUsedTeams(viewer.id);
    const priorUsed = new Set(
      [...usedTeams].filter((t) => t !== existingPick?.team_picked));

    const pickMatch = existingPick
      ? activeMatches.find((m) =>
          m.team1 === existingPick.team_picked || m.team2 === existingPick.team_picked)
      : undefined;
    const pickStarted = !!pickMatch && matchKickedOff(pickMatch, now);

    let pickCard: React.ReactNode = null;
    if (viewer.is_eliminated) {
      const elim = viewer.eliminated_round_id
        ? roundsMap.get(viewer.eliminated_round_id)?.name ?? "a previous round"
        : "a previous round";
      pickCard = (
        <Card tone="red">
          <h3 className="text-lg font-semibold text-red-300">💀 Eliminated in {elim}</h3>
          <p className="mt-1 text-sm text-muted">You can no longer make picks.</p>
        </Card>
      );
    } else if (existingPick) {
      const team = existingPick.team_picked;
      const result = pickResult(team, activeMatches);
      const tone = result === "won" ? "green" : result === "lost" ? "red" : "gold";
      const icon = result === "won" ? "✅" : result === "lost" ? "❌" : "⏳";
      const badgeTone = result === "won" ? "green" : result === "lost" ? "red" : "gold";
      const badgeLbl = result === "won" ? "Won — you advance!"
        : result === "lost" ? "Lost — eliminated" : "Awaiting result";
      pickCard = (
        <Card tone={tone}>
          <p className="text-xs tracking-wider text-muted uppercase">Your pick this round</p>
          <h2 className="my-1 text-2xl font-bold text-ink">
            {icon} <TeamLabel team={team} />
          </h2>
          <Badge tone={badgeTone}>{badgeLbl}</Badge>
          {locked && (
            <p className="mt-2 text-sm text-muted">🔒 Picks are locked — no more changes.</p>
          )}
          {!locked && pickStarted && (
            <p className="mt-2 text-sm text-muted">
              🔒 Your pick&apos;s match has kicked off — it&apos;s locked in.
            </p>
          )}
        </Card>
      );
    }

    const showGrid = !locked && !viewer.is_eliminated && !pickStarted && !existingPick;

    // Group matches by date (home.py)
    const byDate = new Map<string, Match[]>();
    for (const m of [...activeMatches].sort((a, b) =>
      (a.match_date ?? "").localeCompare(b.match_date ?? ""))) {
      const key = m.match_date ?? "";
      if (!byDate.has(key)) byDate.set(key, []);
      byDate.get(key)!.push(m);
    }

    roundSection = (
      <>
        <div className="grid grid-cols-3 gap-2">
          <Metric label="Round" value={activeRound.name} />
          <Metric label="Deadline"
                  value={locked ? "Locked 🔒" : countdown(activeRound.deadline, now)} />
          <Metric label="Your Pick"
                  value={existingPick
                    ? `${flag(existingPick.team_picked)} ${existingPick.team_picked}`
                    : "None yet"} />
        </div>
        {!locked && (
          <p className="mt-1 text-xs text-muted">
            All picks lock at the round&apos;s first kickoff: {formatET(activeRound.deadline)}.
          </p>
        )}
        <hr className="my-4 border-border2" />
        {pickCard}

        {showGrid && (
          <>
            <h3 className="mb-1 text-xl font-semibold text-ink">Pick your team</h3>
            <p className="mb-2 text-sm text-muted">
              Making picks from this app arrives in a later phase — use the
              current app to pick for now. Teams shown in red are already used.
            </p>
            {[...byDate.entries()].map(([date, ms]) => (
              <div key={date}>
                {date && (
                  <p className="mt-4 mb-1 text-xs tracking-wider text-muted uppercase">
                    {formatMatchDate(date)}
                  </p>
                )}
                {ms.map((m) => {
                  const kicked = matchKickedOff(m, now);
                  return (
                    <div key={m.id} className="mb-2 flex items-center gap-2">
                      {[m.team1, m.team2].map((team, i) => (
                        <div key={team} className={`min-w-0 flex-1 truncate rounded-lg border px-3 py-2 text-center text-sm ${
                          priorUsed.has(team)
                            ? "border-red-900 bg-red-950/40 text-red-400 line-through"
                            : kicked
                              ? "border-border bg-surface opacity-30"
                              : "border-border bg-surface text-ink"
                        } ${i === 0 ? "order-1" : "order-3"}`}>
                          <TeamLabel team={team} />
                        </div>
                      ))}
                      <div className="order-2 shrink-0 text-center text-xs text-muted">
                        {kicked ? <>🔒<br />started</> : (
                          <>vs{m.kickoff_time && (
                            <><br /><span className="text-[0.66rem] whitespace-nowrap">
                              {formatETTime(m.kickoff_time)}
                            </span></>
                          )}</>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            ))}
          </>
        )}
      </>
    );
  } else {
    roundSection = <Card className="text-center text-muted">No active round. Check back soon!</Card>;
  }

  // Pick history (home.py)
  const pastPicks = allPicks.filter((p) => p.round_id !== activeRound?.id);
  const historyMatches = new Map(
    await Promise.all(pastPicks.map(async (p) =>
      [p.round_id, await getMatchesForRound(p.round_id)] as [number, Match[]])));

  return (
    <>
      <PageTitle>✅ Make a Pick</PageTitle>
      {roundSection}

      {pastPicks.length > 0 && (
        <>
          <hr className="my-4 border-border2" />
          <h3 className="mb-3 text-xl font-semibold text-ink">Your pick history</h3>
          <div className="flex flex-col gap-2">
            {pastPicks.map((p) => {
              const result = pickResult(p.team_picked, historyMatches.get(p.round_id) ?? []);
              const icon = result === "won" ? "✅" : result === "lost" ? "❌" : "⏳";
              const tone = result === "won" ? "green" : result === "lost" ? "red" : "gray";
              const label = result === "won" ? "Won" : result === "lost" ? "Lost" : "Pending";
              return (
                <Card key={p.id}>
                  <span className="text-xs text-muted">
                    {roundsMap.get(p.round_id)?.name ?? ""}
                  </span>
                  <br />
                  <span>
                    {icon} <TeamLabel team={p.team_picked} className="font-bold text-ink" />
                  </span>{" "}
                  <Badge tone={tone}>{label}</Badge>
                </Card>
              );
            })}
          </div>
        </>
      )}
    </>
  );
}
