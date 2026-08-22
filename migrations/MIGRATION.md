# NFL Survivor — migration runbook

Apply `001_nfl_survivor.sql` **before** deploying the new `web/` app. It is
idempotent, so a partial run can simply be re-run.

## 1. Generate a secret API key (required — the app will not work without it)

The project currently uses a **publishable** key everywhere, including in
`SUPABASE_SERVICE_ROLE_KEY`. Publishable keys are designed to be exposed in
browsers and they do **not** bypass RLS. Once this migration turns RLS on,
every write will start failing until a real secret key is in place.

1. Supabase dashboard → Project Settings → API Keys
2. Create a **secret key** (`sb_secret_...`)
3. Put it in `web/.env.local` as `SUPABASE_SERVICE_ROLE_KEY`
4. Put it in the Streamlit Cloud secrets as `supabase.key` too — the old
   Streamlit app reads the World Cup tables, which this migration also
   locks down.

Never expose the secret key to the client. It is server-only.

## 2. Run the SQL

Supabase dashboard → SQL Editor → paste `001_nfl_survivor.sql` → Run.

It does four things:

- **Enables RLS on the World Cup tables** (`app_users`, `picks`, `rounds`,
  `matches`). These are currently world-readable to anyone holding the
  publishable key — including `app_users.password_hash`. This is the fix.
- Creates `nfl_teams`, `nfl_weeks`, `nfl_games`, `nfl_entries`,
  `nfl_picks`, `nfl_settings`, all with RLS on.
- Seeds 32 teams, 18 weeks, and all 272 regular-season games for 2026,
  pulled live from ESPN. `nfl_weeks.lock_at` is each week's first kickoff.
- Seeds the rule knobs in `nfl_settings`.

The World Cup tables are **not** dropped or modified beyond enabling RLS.

## 3. Verify

```sql
select week_number, name, lock_at, status from public.nfl_weeks order by week_number;
select count(*) from public.nfl_games;   -- expect 272
select count(*) from public.nfl_teams;   -- expect 32
select * from public.nfl_settings;
```

Week 1 should be `active` with `lock_at = 2026-09-10 00:20:00+00`
(Wed Sep 9, 8:20 PM ET).

## 4. Rule knobs

Change these in `nfl_settings` any time — no deploy needed:

| key | default | options |
|---|---|---|
| `tie_rule` | `loss` | `loss`, `survive` |
| `all_out_rule` | `void` | `void`, `eliminate` |
| `no_pick_rule` | `eliminate` | `eliminate`, `auto` |
| `include_playoffs` | `false` | `false`, `true` |
| `season` | `2026` | any year |

**These are my defaults, not your decisions.** They were the three open
questions; change any row and the app and the Rules screen both follow.

## 5. Re-seeding a later season

`syncTeams()` refreshes team metadata. For a new season's schedule,
re-run the generator that produced this file against the new year — the
ESPN endpoint is `/scoreboard?dates=<season>&seasontype=2&week=<n>`.
