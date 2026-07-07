import { flag } from "@/lib/flags";

const badgeTones = {
  green: "bg-green-950 text-green-300",
  red: "bg-red-950 text-red-300",
  gold: "bg-amber-950 text-amber-200",
  gray: "bg-surface text-muted border border-border",
} as const;

export function Badge({ tone, children }: { tone: keyof typeof badgeTones; children: React.ReactNode }) {
  return (
    <span className={`inline-block rounded-full px-2.5 py-0.5 text-[0.72rem] font-bold uppercase tracking-wider ${badgeTones[tone]}`}>
      {children}
    </span>
  );
}

const cardTones = {
  default: "border-border",
  gold: "border-accent",
  red: "border-lose",
  green: "border-win",
} as const;

export function Card({
  tone = "default", className = "", children,
}: { tone?: keyof typeof cardTones; className?: string; children: React.ReactNode }) {
  return (
    <div className={`rounded-xl border bg-surface px-4 py-3 sm:px-5 ${cardTones[tone]} ${className}`}>
      {children}
    </div>
  );
}

export function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0">
      <div className="text-xs text-muted sm:text-sm">{label}</div>
      <div className="truncate text-lg font-semibold text-accent sm:text-2xl">{value}</div>
    </div>
  );
}

export function TeamLabel({ team, className = "" }: { team: string; className?: string }) {
  return (
    <span className={className}>
      {flag(team)} {team}
    </span>
  );
}

export function PageTitle({ children }: { children: React.ReactNode }) {
  return (
    <>
      <h1 className="text-2xl font-bold text-ink sm:text-3xl">{children}</h1>
      <hr className="my-3 border-border2" />
    </>
  );
}
