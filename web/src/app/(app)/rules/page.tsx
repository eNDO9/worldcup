// ← rules.py, copy verbatim
import { Card, PageTitle } from "@/components/ui";

const RULES: [string, string][] = [
  ["1. Pick one team per round.",
   "Each round, choose one team you think will win their match."],
  ["2. No repeats.",
   "Once you've picked a team, you can't pick them again in a later round."],
  ["3. Stay alive.",
   "If your picked team loses, you're eliminated. If they win, you advance."],
  ["4. Beat the first kickoff.",
   "All picks are due before the round's first match kicks off. Once that first game starts, the whole round is locked."],
  ["5. No pick = eliminated.",
   "If the round closes and you haven't made a pick, you're out — same as picking a loser."],
  ["6. Last one standing wins.",
   "The last player with a surviving pick at the end of the tournament wins a secret mystery prize. 🎁"],
];

export default function RulesPage() {
  return (
    <>
      <PageTitle>📋 Rules</PageTitle>
      <Card>
        <h3 className="mb-5 text-lg font-semibold text-ink">How it works</h3>
        <div className="flex flex-col gap-4">
          {RULES.map(([title, body]) => (
            <p key={title}>
              <strong className="text-ink">{title}</strong>
              <br />
              <span className="text-muted">{body}</span>
            </p>
          ))}
        </div>
      </Card>
    </>
  );
}
