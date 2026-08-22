import { AppHeader, Screen, Card } from "@/components/ui";
import { getSettings } from "@/lib/nflDb";

export const dynamic = "force-dynamic";

const RULES = (tie: string, allOut: string) => [
  { n: "01", t: "One team a week", d: "Pick a single NFL team you think wins that week." },
  { n: "02", t: "Never twice", d: "Once you use a team, they're burned for the rest of the season. 32 teams, 18 weeks — plan ahead." },
  { n: "03", t: "Lock at first kickoff", d: "All picks close the moment the week's first game starts. That's usually Thursday night." },
  { n: "04", t: "Everyone's revealed at once", d: "The instant picks lock, every pick in the pool becomes visible. No hiding, no late edits." },
  { n: "05", t: "Lose and you're out", d: `If your team loses, your season ends. A tie ${tie}.` },
  { n: "06", t: "No pick = elimination", d: "Miss the lock without a pick and you're out, same as picking a loser." },
  { n: "07", t: "Last one standing", d: `Survive longest and the pot is yours. If everyone falls in the same week, that week ${allOut}.` },
];

export default async function RulesPage() {
  const s = await getSettings();
  const tie = s.tieRule === "loss" ? "counts as a loss" : "lets you survive";
  const allOut = s.allOutRule === "void"
    ? "is voided and all survivors continue"
    : "eliminates everyone and the pool ends";

  return (
    <>
      <AppHeader title="Rules" subtitle={`${s.season} season · weeks 1–18`} />
      <Screen>
        <div className="mt-4 space-y-2">
          {RULES(tie, allOut).map((r) => (
            <Card key={r.n} className="flex gap-3 p-4">
              <span className="text-[12px] font-bold text-accent tabular-nums">{r.n}</span>
              <div>
                <p className="text-[15px] leading-tight font-bold text-ink">{r.t}</p>
                <p className="mt-1 text-[13px] leading-relaxed text-muted">{r.d}</p>
              </div>
            </Card>
          ))}
        </div>
        <p className="px-1 pt-6 text-[11.5px] leading-relaxed text-faint">
          Scores from ESPN. Not affiliated with or endorsed by the NFL or any team.
        </p>
      </Screen>
    </>
  );
}
