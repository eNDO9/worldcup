// ← pool.py. Server component: picks-visibility is enforced here — opponents'
// picks are only revealed for closed rounds.
import { Badge, Card, Metric, PageTitle, TeamLabel } from "@/components/ui";
import {
  getActiveRound, getAllPicksForRound, getAllRounds, getMatchesForRound,
  getStandings, pickResult,
} from "@/lib/db";
import { displayName, isRoundClosed, type Round } from "@/lib/rounds";
import { getViewer } from "@/lib/viewer";

export const dynamic = "force-dynamic";

export default async function PoolPage() {
  const viewer = (await getViewer())!;
  const [allRounds, standings, activeRound] = await Promise.all([
    getAllRounds(), getStandings(), getActiveRound(),
  ]);

  const alive = standings.filter((u) => !u.is_eliminated);
  const out = standings.filter((u) => u.is_eliminated);
  const roundsMap = new Map(allRounds.map((r) => [r.id, r]));

  const now = new Date();
  const revealed = allRounds.filter((r) => isRoundClosed(r, now));
  const open: Round[] = allRounds.filter(
    (r) => r.status === "active" && !isRoundClosed(r, now));
  const openRound = open[0] ?? null;

  const pickedIds = new Set(
    openRound ? (await getAllPicksForRound(openRound.id)).map((p) => p.user_id) : []);

  const revealedData = await Promise.all(
    [...revealed].reverse().map(async (rnd) => ({
      rnd,
      picksByUser: new Map(
        (await getAllPicksForRound(rnd.id)).map((p) => [p.user_id, p])),
      matches: await getMatchesForRound(rnd.id),
    })),
  );

  return (
    <>
      <PageTitle>🏆 The Pool</PageTitle>

      <div className="grid grid-cols-3 gap-2">
        <Metric label="Players Alive" value={String(alive.length)} />
        <Metric label="Eliminated" value={String(out.length)} />
        <Metric label="Current Round" value={activeRound?.name ?? "—"} />
      </div>
      <hr className="my-4 border-border2" />

      <h3 className="mb-3 text-xl font-semibold text-ink">Players</h3>
      <div className="flex flex-col gap-2">
        {standings.map((u) => {
          const isMe = u.id === viewer.id;
          let status: React.ReactNode;
          let name: React.ReactNode;
          if (u.is_eliminated) {
            const rndName = u.eliminated_round_id
              ? roundsMap.get(u.eliminated_round_id)?.name ?? "" : "";
            status = <Badge tone="red">💀 Out — {rndName}</Badge>;
            name = <del className="text-muted">{displayName(u)}</del>;
          } else {
            name = <span className="text-ink">{displayName(u)}</span>;
            status = openRound
              ? pickedIds.has(u.id)
                ? <Badge tone="green">✅ Locked in</Badge>
                : <Badge tone="gray">⏳ Not yet</Badge>
              : <Badge tone="green">🟢 Alive</Badge>;
          }
          return (
            <Card key={u.id} tone={isMe ? "gold" : "default"}
                  className={`py-2 ${u.is_eliminated ? "opacity-55" : ""}`}>
              {status} <span className="ml-2">{name}</span>
              {isMe && <span className="ml-2 text-xs text-muted">you</span>}
            </Card>
          );
        })}
      </div>

      <hr className="my-4 border-border2" />
      <p className="mb-4 text-sm text-muted">
        Opponents&apos; picks are revealed after each round closes.
      </p>

      {revealedData.map(({ rnd, picksByUser, matches }) => (
        <section key={rnd.id} className="mb-6">
          <h3 className="mb-3 text-xl font-semibold text-ink">{rnd.name}</h3>
          <div className="flex flex-col gap-2">
            {standings.map((participant) => {
              const pick = picksByUser.get(participant.id);
              const isMe = participant.id === viewer.id;
              const name = displayName(participant);
              if (!pick) {
                return (
                  <Card key={participant.id} className="py-2 opacity-40">
                    <span className="text-sm text-muted">{name}</span>
                    {isMe && <span className="ml-2 text-xs text-muted">you</span>}
                    <span className="ml-2">— no pick</span>
                  </Card>
                );
              }
              const result = pickResult(pick.team_picked, matches);
              const icon = result === "won" ? "✅" : result === "lost" ? "❌" : "⏳";
              const tone = result === "won" ? "green" : result === "lost" ? "red" : "gray";
              const label = result === "won" ? "Won" : result === "lost" ? "Lost" : "Pending";
              return (
                <Card key={participant.id} tone={isMe ? "gold" : "default"} className="py-2">
                  <span className="text-sm text-muted">{name}</span>
                  {isMe && <span className="ml-1 text-xs text-muted">you</span>}
                  <span className="mx-2">
                    {icon} <TeamLabel team={pick.team_picked} className="font-bold text-ink" />
                  </span>
                  <Badge tone={tone}>{label}</Badge>
                </Card>
              );
            })}
          </div>
        </section>
      ))}

      {revealedData.length === 0 && !openRound && (
        <Card className="text-center text-muted">No rounds have started yet.</Card>
      )}
    </>
  );
}
