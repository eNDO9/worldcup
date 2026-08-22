# Claude Instructions for worldcup

## Git / GitHub
- **Push changes automatically** after every meaningful commit — do not ask for confirmation.
- Always use the personal GitHub account (eNDO9), never the organizational account (ndo@isdglobal.org).

## Project stack
The app is mid-migration from a World Cup pool to an **NFL survivor pool**.

- **`web/`** — Next.js 16 + React 19 + Tailwind 4. This is the live target:
  mobile-first, bottom tab bar, PWA-installable. All new work goes here.
- **Legacy Streamlit** (`app.py` and the other root `.py` files) ran the
  2026 World Cup pool. Kept for reference; not the future.
- Supabase backend, shared between both.
- Credentials: `.streamlit/secrets.toml` (Streamlit) and `web/.env.local`
  (Next.js). Both gitignored, never commit.

## NFL data model
- `nfl_weeks.lock_at` is the week's FIRST kickoff. Picks close and all picks
  become visible at that same instant — see `arePicksRevealed` in `lib/nfl.ts`,
  which is deliberately an alias of `isWeekLocked`. Do not let those diverge.
- Pool rules are enforced by DB constraints: `UNIQUE(user_id, week_id)` is
  one-pick-per-week, `UNIQUE(user_id, season, team_abbr)` is no-reuse.
- Open rule calls live in `nfl_settings` (tie/all-out/no-pick/playoffs), not
  in code. Read them via `getSettings()`.
- Results come from ESPN's public undocumented API (`lib/espn.ts`). No key,
  no stability guarantee — every field access there is defensive on purpose.

## Trademark constraint
Never ship NFL logos or wordmarks. Teams render as a colored abbreviation
tile (`TeamTile`). Team *names* as text are fine; marks are not, and an App
Store build with them needs a license.

## Migrations
Hand-applied via the Supabase SQL editor. Paste the SQL inline in chat, not
just a file path. See `migrations/MIGRATION.md`.

## Streamlit Cloud
- Account: endo9 (linked to personal GitHub)
- Secrets must be re-entered in the Streamlit Cloud dashboard when new keys are added
