-- 001_nfl_survivor.sql — NFL Survivor pool schema (season 2026)
-- Hand-apply in the Supabase SQL editor. Idempotent: safe to re-run.
--
-- Design notes:
--   * All new tables are nfl_* prefixed. The World Cup tables (rounds,
--     matches, picks) are left untouched as historical data.
--   * app_users is REUSED so existing accounts keep working. Per-season
--     survivor state lives in nfl_entries, not on app_users.
--   * Pool rules are enforced by DB constraints where possible:
--       one pick per week      -> UNIQUE (user_id, week_id)
--       never reuse a team     -> UNIQUE (user_id, season, team_abbr)
--   * RLS is ON for every table. Reference data (teams/weeks/games) is
--     publicly readable; picks and entries are server-only.

BEGIN;

-- ===========================================================================
-- 0. SECURITY HOTFIX for the existing World Cup tables.
--    app_users currently has RLS OFF, so anyone holding the publishable key
--    can read every row INCLUDING password_hash. Close that now.
-- ===========================================================================
ALTER TABLE public.app_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.picks     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rounds    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.matches   ENABLE ROW LEVEL SECURITY;
-- No policies added => only a secret/service key can read them. The
-- Streamlit app must move to a secret key (see MIGRATION.md).

-- ===========================================================================
-- 1. TEAMS  (no NFL logos or marks stored - name + colors only)
-- ===========================================================================
CREATE TABLE IF NOT EXISTS public.nfl_teams (
    abbr        TEXT PRIMARY KEY,
    location    TEXT NOT NULL,
    nickname    TEXT NOT NULL,
    display_name TEXT NOT NULL,
    color       TEXT,
    alt_color   TEXT,
    espn_id     TEXT
);

-- ===========================================================================
-- 2. WEEKS   lock_at = kickoff of the week's FIRST game. Everything about
--            the pool hangs off this one timestamp: picks close, and all
--            picks become visible, the moment it passes.
-- ===========================================================================
CREATE TABLE IF NOT EXISTS public.nfl_weeks (
    id          SERIAL PRIMARY KEY,
    season      INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    name        TEXT NOT NULL,
    lock_at     TIMESTAMPTZ NOT NULL,
    status      TEXT NOT NULL DEFAULT 'upcoming'
                CHECK (status IN ('upcoming','active','locked','completed')),
    UNIQUE (season, week_number)
);

-- ===========================================================================
-- 3. GAMES
-- ===========================================================================
CREATE TABLE IF NOT EXISTS public.nfl_games (
    id            SERIAL PRIMARY KEY,
    week_id       INTEGER NOT NULL REFERENCES public.nfl_weeks(id) ON DELETE CASCADE,
    espn_event_id TEXT UNIQUE,
    home_abbr     TEXT NOT NULL REFERENCES public.nfl_teams(abbr),
    away_abbr     TEXT NOT NULL REFERENCES public.nfl_teams(abbr),
    kickoff       TIMESTAMPTZ NOT NULL,
    home_score    INTEGER,
    away_score    INTEGER,
    -- winner: team abbr, or 'TIE' once final with equal scores. NULL until final.
    winner        TEXT,
    status        TEXT NOT NULL DEFAULT 'scheduled'
                  CHECK (status IN ('scheduled','in_progress','final')),
    CHECK (home_abbr <> away_abbr)
);
CREATE INDEX IF NOT EXISTS nfl_games_week_idx ON public.nfl_games(week_id);

-- ===========================================================================
-- 4. ENTRIES  one row per user per season. Survivor state lives here so the
--             World Cup columns on app_users are never overwritten.
-- ===========================================================================
CREATE TABLE IF NOT EXISTS public.nfl_entries (
    id                UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id           UUID NOT NULL REFERENCES public.app_users(id) ON DELETE CASCADE,
    season            INTEGER NOT NULL,
    is_eliminated     BOOLEAN NOT NULL DEFAULT FALSE,
    eliminated_week_id INTEGER REFERENCES public.nfl_weeks(id),
    -- why they went out: 'loss', 'tie', or 'no_pick'
    eliminated_reason TEXT CHECK (eliminated_reason IN ('loss','tie','no_pick')),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, season)
);

-- ===========================================================================
-- 5. PICKS    the two UNIQUE constraints ARE the pool rules.
-- ===========================================================================
CREATE TABLE IF NOT EXISTS public.nfl_picks (
    id         UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id    UUID NOT NULL REFERENCES public.app_users(id) ON DELETE CASCADE,
    week_id    INTEGER NOT NULL REFERENCES public.nfl_weeks(id) ON DELETE CASCADE,
    season     INTEGER NOT NULL,
    team_abbr  TEXT NOT NULL REFERENCES public.nfl_teams(abbr),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, week_id),
    UNIQUE (user_id, season, team_abbr)
);
CREATE INDEX IF NOT EXISTS nfl_picks_week_idx ON public.nfl_picks(week_id);

-- ===========================================================================
-- 6. SETTINGS  the rule calls that are still open - change without a deploy.
-- ===========================================================================
CREATE TABLE IF NOT EXISTS public.nfl_settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    note  TEXT
);
INSERT INTO public.nfl_settings (key, value, note) VALUES
  ('season',        '2026',    'Active season'),
  ('tie_rule',      'loss',    'loss | survive  - what a tied NFL game does to your pick'),
  ('all_out_rule',  'void',    'void | eliminate - when every survivor loses in the same week'),
  ('include_playoffs','false', 'false = regular season only, weeks 1-18'),
  ('no_pick_rule',  'eliminate','eliminate | auto - missing the lock')
ON CONFLICT (key) DO NOTHING;

-- ===========================================================================
-- 7. ROW LEVEL SECURITY
-- ===========================================================================
ALTER TABLE public.nfl_teams    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.nfl_weeks    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.nfl_games    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.nfl_picks    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.nfl_entries  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.nfl_settings ENABLE ROW LEVEL SECURITY;

-- Reference data is public-read: no secrets in schedules or team colors.
DROP POLICY IF EXISTS nfl_teams_read ON public.nfl_teams;
CREATE POLICY nfl_teams_read ON public.nfl_teams FOR SELECT USING (true);
DROP POLICY IF EXISTS nfl_weeks_read ON public.nfl_weeks;
CREATE POLICY nfl_weeks_read ON public.nfl_weeks FOR SELECT USING (true);
DROP POLICY IF EXISTS nfl_games_read ON public.nfl_games;
CREATE POLICY nfl_games_read ON public.nfl_games FOR SELECT USING (true);

-- nfl_picks / nfl_entries / nfl_settings get NO anon policy on purpose.
-- Only the server's secret key touches them, so a pick can never leak
-- before its week locks - the reveal rule is enforced by absence of access,
-- not by client-side hiding.

COMMIT;


-- ===========================================================================
-- SEED: 32 teams
-- ===========================================================================
INSERT INTO public.nfl_teams (abbr, location, nickname, display_name, color, alt_color) VALUES
  ('ARI', 'Arizona', 'Cardinals', 'Arizona Cardinals', '#a40227', '#ffffff'),
  ('ATL', 'Atlanta', 'Falcons', 'Atlanta Falcons', '#a71930', '#000000'),
  ('BAL', 'Baltimore', 'Ravens', 'Baltimore Ravens', '#29126f', '#000000'),
  ('BUF', 'Buffalo', 'Bills', 'Buffalo Bills', '#00338d', '#d50a0a'),
  ('CAR', 'Carolina', 'Panthers', 'Carolina Panthers', '#0085ca', '#000000'),
  ('CHI', 'Chicago', 'Bears', 'Chicago Bears', '#0b1c3a', '#e64100'),
  ('CIN', 'Cincinnati', 'Bengals', 'Cincinnati Bengals', '#fb4f14', '#000000'),
  ('CLE', 'Cleveland', 'Browns', 'Cleveland Browns', '#472a08', '#ff3c00'),
  ('DAL', 'Dallas', 'Cowboys', 'Dallas Cowboys', '#002a5c', '#b0b7bc'),
  ('DEN', 'Denver', 'Broncos', 'Denver Broncos', '#0a2343', '#fc4c02'),
  ('DET', 'Detroit', 'Lions', 'Detroit Lions', '#0076b6', '#bbbbbb'),
  ('GB', 'Green Bay', 'Packers', 'Green Bay Packers', '#204e32', '#ffb612'),
  ('HOU', 'Houston', 'Texans', 'Houston Texans', '#021018', '#eb0028'),
  ('IND', 'Indianapolis', 'Colts', 'Indianapolis Colts', '#003b75', '#ffffff'),
  ('JAX', 'Jacksonville', 'Jaguars', 'Jacksonville Jaguars', '#007487', '#d7a22a'),
  ('KC', 'Kansas City', 'Chiefs', 'Kansas City Chiefs', '#e31837', '#ffb612'),
  ('LAC', 'Los Angeles', 'Chargers', 'Los Angeles Chargers', '#0080c6', '#ffc20e'),
  ('LAR', 'Los Angeles', 'Rams', 'Los Angeles Rams', '#003594', '#ffd100'),
  ('LV', 'Las Vegas', 'Raiders', 'Las Vegas Raiders', '#000000', '#a5acaf'),
  ('MIA', 'Miami', 'Dolphins', 'Miami Dolphins', '#008e97', '#fc4c02'),
  ('MIN', 'Minnesota', 'Vikings', 'Minnesota Vikings', '#4f2683', '#ffc62f'),
  ('NE', 'New England', 'Patriots', 'New England Patriots', '#002a5c', '#c60c30'),
  ('NO', 'New Orleans', 'Saints', 'New Orleans Saints', '#d3bc8d', '#000000'),
  ('NYG', 'New York', 'Giants', 'New York Giants', '#003c7f', '#c9243f'),
  ('NYJ', 'New York', 'Jets', 'New York Jets', '#115740', '#ffffff'),
  ('PHI', 'Philadelphia', 'Eagles', 'Philadelphia Eagles', '#06424d', '#000000'),
  ('PIT', 'Pittsburgh', 'Steelers', 'Pittsburgh Steelers', '#000000', '#ffb612'),
  ('SEA', 'Seattle', 'Seahawks', 'Seattle Seahawks', '#002a5c', '#69be28'),
  ('SF', 'San Francisco', '49ers', 'San Francisco 49ers', '#aa0000', '#b3995d'),
  ('TB', 'Tampa Bay', 'Buccaneers', 'Tampa Bay Buccaneers', '#bd1c36', '#3e3a35'),
  ('TEN', 'Tennessee', 'Titans', 'Tennessee Titans', '#4495d2', '#001532'),
  ('WSH', 'Washington', 'Commanders', 'Washington Commanders', '#5a1414', '#ffb612')
ON CONFLICT (abbr) DO UPDATE SET
  location=EXCLUDED.location, nickname=EXCLUDED.nickname,
  display_name=EXCLUDED.display_name, color=EXCLUDED.color, alt_color=EXCLUDED.alt_color;

-- ===========================================================================
-- SEED: 18 weeks. lock_at is the week's first kickoff, straight from ESPN.
-- ===========================================================================
INSERT INTO public.nfl_weeks (season, week_number, name, lock_at, status) VALUES
  (2026, 1, 'Week 1', '2026-09-10T00:20+00:00', 'active'),
  (2026, 2, 'Week 2', '2026-09-18T00:15+00:00', 'upcoming'),
  (2026, 3, 'Week 3', '2026-09-25T00:15+00:00', 'upcoming'),
  (2026, 4, 'Week 4', '2026-10-02T00:15+00:00', 'upcoming'),
  (2026, 5, 'Week 5', '2026-10-09T00:15+00:00', 'upcoming'),
  (2026, 6, 'Week 6', '2026-10-16T00:15+00:00', 'upcoming'),
  (2026, 7, 'Week 7', '2026-10-23T00:15+00:00', 'upcoming'),
  (2026, 8, 'Week 8', '2026-10-30T00:15+00:00', 'upcoming'),
  (2026, 9, 'Week 9', '2026-11-06T01:15+00:00', 'upcoming'),
  (2026, 10, 'Week 10', '2026-11-13T01:15+00:00', 'upcoming'),
  (2026, 11, 'Week 11', '2026-11-20T01:15+00:00', 'upcoming'),
  (2026, 12, 'Week 12', '2026-11-26T01:00+00:00', 'upcoming'),
  (2026, 13, 'Week 13', '2026-12-04T01:15+00:00', 'upcoming'),
  (2026, 14, 'Week 14', '2026-12-11T01:15+00:00', 'upcoming'),
  (2026, 15, 'Week 15', '2026-12-18T01:15+00:00', 'upcoming'),
  (2026, 16, 'Week 16', '2026-12-25T01:15+00:00', 'upcoming'),
  (2026, 17, 'Week 17', '2027-01-01T01:15+00:00', 'upcoming'),
  (2026, 18, 'Week 18', '2027-01-10T05:00+00:00', 'upcoming')
ON CONFLICT (season, week_number) DO UPDATE SET lock_at=EXCLUDED.lock_at;

-- ===========================================================================
-- SEED: 272 games
-- ===========================================================================
INSERT INTO public.nfl_games (week_id, espn_event_id, home_abbr, away_abbr, kickoff) VALUES
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=1), '401872656', 'SEA', 'NE', '2026-09-10T00:20+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=1), '401872657', 'LAR', 'SF', '2026-09-11T00:35+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=1), '401872925', 'CIN', 'TB', '2026-09-13T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=1), '401872923', 'DET', 'NO', '2026-09-13T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=1), '401872924', 'TEN', 'NYJ', '2026-09-13T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=1), '401872659', 'IND', 'BAL', '2026-09-13T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=1), '401872658', 'PIT', 'ATL', '2026-09-13T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=1), '401872661', 'CAR', 'CHI', '2026-09-13T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=1), '401872922', 'JAX', 'CLE', '2026-09-13T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=1), '401872660', 'HOU', 'BUF', '2026-09-13T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=1), '401872928', 'LV', 'MIA', '2026-09-13T20:25+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=1), '401872927', 'MIN', 'GB', '2026-09-13T20:25+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=1), '401872929', 'PHI', 'WSH', '2026-09-13T20:25+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=1), '401872926', 'LAC', 'ARI', '2026-09-13T20:25+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=1), '401872930', 'NYG', 'DAL', '2026-09-14T00:20+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=1), '401872931', 'KC', 'DEN', '2026-09-15T00:15+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=2), '401872932', 'BUF', 'DET', '2026-09-18T00:15+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=2), '401872933', 'ATL', 'CAR', '2026-09-20T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=2), '401872937', 'CHI', 'MIN', '2026-09-20T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=2), '401872939', 'TEN', 'PHI', '2026-09-20T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=2), '401872946', 'NE', 'PIT', '2026-09-20T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=2), '401872936', 'NYJ', 'GB', '2026-09-20T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=2), '401872935', 'TB', 'CLE', '2026-09-20T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=2), '401872938', 'BAL', 'NO', '2026-09-20T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=2), '401872934', 'HOU', 'CIN', '2026-09-20T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=2), '401872940', 'DEN', 'JAX', '2026-09-20T20:05+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=2), '401872941', 'LAC', 'LV', '2026-09-20T20:05+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=2), '401872944', 'DAL', 'WSH', '2026-09-20T20:25+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=2), '401872943', 'ARI', 'SEA', '2026-09-20T20:25+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=2), '401872942', 'SF', 'MIA', '2026-09-20T20:25+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=2), '401872945', 'KC', 'IND', '2026-09-21T00:20+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=2), '401872947', 'LAR', 'NYG', '2026-09-22T00:15+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=3), '401872948', 'GB', 'ATL', '2026-09-25T00:15+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=3), '401872953', 'BUF', 'LAC', '2026-09-27T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=3), '401872949', 'CLE', 'CAR', '2026-09-27T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=3), '401872954', 'DET', 'NYJ', '2026-09-27T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=3), '401872951', 'IND', 'HOU', '2026-09-27T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=3), '401872952', 'MIA', 'KC', '2026-09-27T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=3), '401872956', 'NYG', 'TEN', '2026-09-27T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=3), '401872950', 'PIT', 'CIN', '2026-09-27T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=3), '401872955', 'WSH', 'SEA', '2026-09-27T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=3), '401872957', 'JAX', 'NE', '2026-09-27T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=3), '401872958', 'SF', 'ARI', '2026-09-27T20:05+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=3), '401872959', 'TB', 'MIN', '2026-09-27T20:05+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=3), '401872960', 'DAL', 'BAL', '2026-09-27T20:25+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=3), '401872961', 'NO', 'LV', '2026-09-27T20:25+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=3), '401872962', 'DEN', 'LAR', '2026-09-28T00:20+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=3), '401872963', 'CHI', 'PHI', '2026-09-29T00:15+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=4), '401872964', 'CLE', 'PIT', '2026-10-02T00:15+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=4), '401872965', 'WSH', 'IND', '2026-10-04T13:30+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=4), '401872971', 'BUF', 'NE', '2026-10-04T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=4), '401872972', 'CHI', 'NYJ', '2026-10-04T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=4), '401872969', 'CIN', 'JAX', '2026-10-04T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=4), '401872966', 'NYG', 'ARI', '2026-10-04T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=4), '401872970', 'PHI', 'LAR', '2026-10-04T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=4), '401872968', 'TB', 'GB', '2026-10-04T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=4), '401872973', 'BAL', 'TEN', '2026-10-04T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=4), '401872967', 'HOU', 'DAL', '2026-10-04T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=4), '401872974', 'MIN', 'MIA', '2026-10-04T20:05+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=4), '401872976', 'LV', 'KC', '2026-10-04T20:25+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=4), '401872975', 'SF', 'DEN', '2026-10-04T20:25+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=4), '401872977', 'SEA', 'LAC', '2026-10-04T20:25+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=4), '401872978', 'CAR', 'DET', '2026-10-05T00:20+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=4), '401872979', 'NO', 'ATL', '2026-10-06T00:15+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=5), '401872980', 'DAL', 'TB', '2026-10-09T00:15+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=5), '401872981', 'JAX', 'PHI', '2026-10-11T13:30+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=5), '401872984', 'TEN', 'HOU', '2026-10-11T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=5), '401872982', 'MIA', 'CIN', '2026-10-11T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=5), '401872986', 'NE', 'LV', '2026-10-11T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=5), '401872987', 'NO', 'MIN', '2026-10-11T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=5), '401872983', 'NYJ', 'CLE', '2026-10-11T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=5), '401872985', 'PIT', 'IND', '2026-10-11T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=5), '401872988', 'WSH', 'NYG', '2026-10-11T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=5), '401872989', 'LAC', 'DEN', '2026-10-11T20:05+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=5), '401872990', 'GB', 'CHI', '2026-10-11T20:25+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=5), '401872991', 'ARI', 'DET', '2026-10-11T20:25+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=5), '401872992', 'SEA', 'SF', '2026-10-11T20:25+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=5), '401872993', 'ATL', 'BAL', '2026-10-12T00:20+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=5), '401872994', 'LAR', 'BUF', '2026-10-13T00:15+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=6), '401872995', 'DEN', 'SEA', '2026-10-16T00:15+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=6), '401872996', 'JAX', 'HOU', '2026-10-18T13:30+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=6), '401872999', 'ATL', 'CHI', '2026-10-18T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=6), '401872997', 'CLE', 'BAL', '2026-10-18T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=6), '401873003', 'IND', 'TEN', '2026-10-18T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=6), '401873001', 'NE', 'NYJ', '2026-10-18T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=6), '401873000', 'NYG', 'NO', '2026-10-18T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=6), '401872998', 'PHI', 'CAR', '2026-10-18T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=6), '401873002', 'TB', 'PIT', '2026-10-18T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=6), '401873004', 'LAR', 'ARI', '2026-10-18T20:05+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=6), '401873006', 'KC', 'LAC', '2026-10-18T20:25+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=6), '401873005', 'LV', 'BUF', '2026-10-18T20:25+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=6), '401873007', 'GB', 'DAL', '2026-10-19T00:20+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=6), '401873008', 'SF', 'WSH', '2026-10-20T00:15+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=7), '401873010', 'CHI', 'NE', '2026-10-23T00:15+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=7), '401873011', 'NO', 'PIT', '2026-10-25T13:30+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=7), '401873017', 'ATL', 'SF', '2026-10-25T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=7), '401873013', 'TEN', 'CLE', '2026-10-25T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=7), '401873014', 'MIN', 'IND', '2026-10-25T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=7), '401873015', 'NYJ', 'MIA', '2026-10-25T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=7), '401873018', 'CAR', 'TB', '2026-10-25T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=7), '401873012', 'BAL', 'CIN', '2026-10-25T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=7), '401873016', 'HOU', 'NYG', '2026-10-25T17:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=7), '401873019', 'ARI', 'DEN', '2026-10-25T20:05+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=7), '401873020', 'DET', 'GB', '2026-10-25T20:25+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=7), '401873021', 'LV', 'LAR', '2026-10-25T20:25+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=7), '401873022', 'SEA', 'KC', '2026-10-26T00:20+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=7), '401873009', 'PHI', 'DAL', '2026-10-27T00:15+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=8), '401873023', 'GB', 'CAR', '2026-10-30T00:15+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=8), '401873026', 'BUF', 'BAL', '2026-11-01T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=8), '401873031', 'CIN', 'TEN', '2026-11-01T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=8), '401873024', 'DAL', 'ARI', '2026-11-01T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=8), '401873030', 'DET', 'MIN', '2026-11-01T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=8), '401873029', 'NYJ', 'LV', '2026-11-01T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=8), '401873027', 'PIT', 'CLE', '2026-11-01T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=8), '401873025', 'TB', 'ATL', '2026-11-01T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=8), '401873028', 'JAX', 'IND', '2026-11-01T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=8), '401873032', 'LAR', 'LAC', '2026-11-01T21:05+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=8), '401873033', 'DEN', 'KC', '2026-11-01T21:25+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=8), '401873034', 'MIA', 'NE', '2026-11-01T21:25+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=8), '401873035', 'WSH', 'PHI', '2026-11-02T01:20+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=8), '401873036', 'SEA', 'CHI', '2026-11-03T01:15+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=9), '401873037', 'BAL', 'JAX', '2026-11-06T01:15+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=9), '401873038', 'ATL', 'CIN', '2026-11-08T14:30+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=9), '401873040', 'IND', 'DAL', '2026-11-08T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=9), '401873045', 'KC', 'NYJ', '2026-11-08T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=9), '401873042', 'MIA', 'DET', '2026-11-08T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=9), '401873039', 'NO', 'CLE', '2026-11-08T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=9), '401873044', 'PHI', 'NYG', '2026-11-08T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=9), '401873043', 'WSH', 'LAR', '2026-11-08T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=9), '401873041', 'CAR', 'DEN', '2026-11-08T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=9), '401873046', 'LAC', 'HOU', '2026-11-08T21:05+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=9), '401873047', 'SF', 'LV', '2026-11-08T21:05+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=9), '401873049', 'NE', 'GB', '2026-11-08T21:25+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=9), '401873048', 'SEA', 'ARI', '2026-11-08T21:25+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=9), '401873050', 'CHI', 'TB', '2026-11-09T01:20+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=9), '401873051', 'MIN', 'BUF', '2026-11-10T01:15+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=10), '401873052', 'NYG', 'WSH', '2026-11-13T01:15+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=10), '401873053', 'DET', 'NE', '2026-11-15T14:30+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=10), '401873058', 'ATL', 'KC', '2026-11-15T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=10), '401873056', 'CLE', 'HOU', '2026-11-15T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=10), '401873060', 'GB', 'MIN', '2026-11-15T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=10), '401873057', 'TEN', 'JAX', '2026-11-15T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=10), '401873059', 'IND', 'MIA', '2026-11-15T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=10), '401873055', 'NO', 'CAR', '2026-11-15T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=10), '401873054', 'NYJ', 'BUF', '2026-11-15T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=10), '401873062', 'LV', 'SEA', '2026-11-15T21:05+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=10), '401873061', 'ARI', 'LAR', '2026-11-15T21:05+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=10), '401873063', 'DAL', 'SF', '2026-11-15T21:25+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=10), '401873064', 'CIN', 'PIT', '2026-11-16T01:20+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=10), '401873065', 'BAL', 'LAC', '2026-11-17T01:15+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=11), '401873066', 'HOU', 'IND', '2026-11-20T01:15+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=11), '401873070', 'BUF', 'MIA', '2026-11-22T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=11), '401873071', 'CHI', 'NO', '2026-11-22T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=11), '401873073', 'DAL', 'TEN', '2026-11-22T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=11), '401873072', 'DET', 'TB', '2026-11-22T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=11), '401873067', 'KC', 'ARI', '2026-11-22T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=11), '401873069', 'NYG', 'JAX', '2026-11-22T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=11), '401873068', 'CAR', 'BAL', '2026-11-22T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=11), '401873074', 'LAC', 'NYJ', '2026-11-22T21:05+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=11), '401873075', 'DEN', 'LV', '2026-11-22T21:25+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=11), '401873076', 'PHI', 'PIT', '2026-11-22T21:25+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=11), '401873077', 'SF', 'MIN', '2026-11-23T01:20+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=11), '401873078', 'WSH', 'CIN', '2026-11-24T01:15+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=12), '401873079', 'LAR', 'GB', '2026-11-26T01:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=12), '401873081', 'DET', 'CHI', '2026-11-26T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=12), '401873080', 'DAL', 'PHI', '2026-11-26T21:30+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=12), '401873082', 'BUF', 'KC', '2026-11-27T01:20+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=12), '401873083', 'PIT', 'DEN', '2026-11-27T20:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=12), '401873087', 'CIN', 'NO', '2026-11-29T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=12), '401873086', 'CLE', 'LV', '2026-11-29T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=12), '401873088', 'IND', 'NYG', '2026-11-29T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=12), '401873089', 'MIA', 'NYJ', '2026-11-29T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=12), '401873084', 'MIN', 'ATL', '2026-11-29T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=12), '401873085', 'HOU', 'BAL', '2026-11-29T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=12), '401873090', 'JAX', 'TEN', '2026-11-29T21:05+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=12), '401873092', 'ARI', 'WSH', '2026-11-29T21:25+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=12), '401873091', 'SF', 'SEA', '2026-11-29T21:25+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=12), '401873093', 'LAC', 'NE', '2026-11-30T01:20+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=12), '401873094', 'TB', 'CAR', '2026-12-01T01:15+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=13), '401873096', 'LAR', 'KC', '2026-12-04T01:15+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=13), '401873098', 'ATL', 'DET', '2026-12-06T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=13), '401873100', 'CHI', 'JAX', '2026-12-06T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=13), '401873097', 'CLE', 'CIN', '2026-12-06T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=13), '401873102', 'TEN', 'WSH', '2026-12-06T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=13), '401873099', 'NO', 'GB', '2026-12-06T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=13), '401873095', 'NYG', 'SF', '2026-12-06T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=13), '401873101', 'TB', 'LAC', '2026-12-06T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=13), '401873103', 'DEN', 'MIA', '2026-12-06T21:05+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=13), '401873104', 'ARI', 'PHI', '2026-12-06T21:05+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=13), '401873106', 'MIN', 'CAR', '2026-12-06T21:25+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=13), '401873105', 'NE', 'BUF', '2026-12-06T21:25+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=13), '401873107', 'PIT', 'HOU', '2026-12-07T01:20+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=13), '401873108', 'SEA', 'DAL', '2026-12-08T01:15+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=14), '401873109', 'NE', 'MIN', '2026-12-11T01:15+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=14), '401873110', 'CLE', 'ATL', '2026-12-13T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=14), '401873117', 'DET', 'TEN', '2026-12-13T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=14), '401873111', 'MIA', 'CHI', '2026-12-13T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=14), '401873112', 'NYJ', 'DEN', '2026-12-13T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=14), '401873114', 'PHI', 'IND', '2026-12-13T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=14), '401873113', 'WSH', 'HOU', '2026-12-13T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=14), '401873115', 'CAR', 'NO', '2026-12-13T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=14), '401873116', 'BAL', 'TB', '2026-12-13T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=14), '401873118', 'LV', 'LAC', '2026-12-13T21:05+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=14), '401873119', 'CIN', 'KC', '2026-12-13T21:25+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=14), '401873120', 'SF', 'LAR', '2026-12-13T21:25+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=14), '401873121', 'SEA', 'NYG', '2026-12-13T21:25+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=14), '401873122', 'GB', 'BUF', '2026-12-14T01:20+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=14), '401873123', 'JAX', 'PIT', '2026-12-15T01:15+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=15), '401873124', 'LAC', 'SF', '2026-12-18T01:15+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=15), '401873125', 'PHI', 'SEA', '2026-12-19T22:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=15), '401873126', 'BUF', 'CHI', '2026-12-20T01:20+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=15), '401873133', 'GB', 'MIA', '2026-12-20T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=15), '401873131', 'TEN', 'IND', '2026-12-20T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=15), '401873130', 'NYG', 'CLE', '2026-12-20T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=15), '401873128', 'PIT', 'BAL', '2026-12-20T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=15), '401873134', 'TB', 'NO', '2026-12-20T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=15), '401873127', 'WSH', 'ATL', '2026-12-20T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=15), '401873129', 'CAR', 'CIN', '2026-12-20T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=15), '401873132', 'HOU', 'JAX', '2026-12-20T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=15), '401873135', 'ARI', 'NYJ', '2026-12-20T21:05+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=15), '401873137', 'LV', 'DEN', '2026-12-20T21:25+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=15), '401873136', 'LAR', 'DAL', '2026-12-20T21:25+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=15), '401873138', 'MIN', 'DET', '2026-12-21T01:20+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=15), '401873139', 'KC', 'NE', '2026-12-22T01:15+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=16), '401873140', 'PHI', 'HOU', '2026-12-25T01:15+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=16), '401873141', 'CHI', 'GB', '2026-12-25T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=16), '401873142', 'DEN', 'BUF', '2026-12-25T21:30+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=16), '401873143', 'SEA', 'LAR', '2026-12-26T01:15+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=16), '401873146', 'ATL', 'TB', '2026-12-27T05:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=16), '401873145', 'IND', 'CIN', '2026-12-27T05:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=16), '401873147', 'MIN', 'WSH', '2026-12-27T05:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=16), '401873144', 'PIT', 'CAR', '2026-12-27T05:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=16), '401873150', 'MIA', 'LAC', '2026-12-27T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=16), '401873148', 'NO', 'ARI', '2026-12-27T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=16), '401873151', 'NYJ', 'NE', '2026-12-27T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=16), '401873149', 'BAL', 'CLE', '2026-12-27T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=16), '401873152', 'LV', 'TEN', '2026-12-27T21:05+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=16), '401873153', 'KC', 'SF', '2026-12-27T21:25+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=16), '401873154', 'DAL', 'JAX', '2026-12-28T01:20+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=16), '401873155', 'DET', 'NYG', '2026-12-29T01:15+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=17), '401873156', 'CIN', 'BAL', '2027-01-01T01:15+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=17), '401873157', 'NE', 'DEN', '2027-01-03T05:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=17), '401873158', 'LAC', 'KC', '2027-01-03T05:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=17), '401873159', 'TB', 'LAR', '2027-01-03T05:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=17), '401873160', 'JAX', 'WSH', '2027-01-03T05:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=17), '401873164', 'ATL', 'NO', '2027-01-03T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=17), '401873162', 'CLE', 'IND', '2027-01-03T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=17), '401873165', 'DAL', 'NYG', '2027-01-03T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=17), '401873166', 'TEN', 'PIT', '2027-01-03T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=17), '401873161', 'MIA', 'BUF', '2027-01-03T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=17), '401873163', 'NYJ', 'MIN', '2027-01-03T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=17), '401873167', 'CAR', 'SEA', '2027-01-03T18:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=17), '401873168', 'ARI', 'LV', '2027-01-03T21:05+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=17), '401873169', 'CHI', 'DET', '2027-01-03T21:25+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=17), '401873170', 'SF', 'PHI', '2027-01-04T01:20+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=17), '401873171', 'GB', 'HOU', '2027-01-05T01:15+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=18), '401873181', 'BUF', 'NYJ', '2027-01-10T05:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=18), '401873174', 'CIN', 'CLE', '2027-01-10T05:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=18), '401873179', 'DEN', 'LAC', '2027-01-10T05:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=18), '401873176', 'GB', 'DET', '2027-01-10T05:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=18), '401873177', 'IND', 'JAX', '2027-01-10T05:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=18), '401873178', 'KC', 'LV', '2027-01-10T05:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=18), '401873185', 'LAR', 'SEA', '2027-01-10T05:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=18), '401873173', 'MIN', 'CHI', '2027-01-10T05:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=18), '401873180', 'NE', 'MIA', '2027-01-10T05:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=18), '401873186', 'NO', 'TB', '2027-01-10T05:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=18), '401873182', 'NYG', 'PHI', '2027-01-10T05:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=18), '401873184', 'ARI', 'SF', '2027-01-10T05:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=18), '401873175', 'WSH', 'DAL', '2027-01-10T05:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=18), '401873172', 'CAR', 'ATL', '2027-01-10T05:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=18), '401873183', 'BAL', 'PIT', '2027-01-10T05:00+00:00'),
  ((SELECT id FROM public.nfl_weeks WHERE season=2026 AND week_number=18), '401873187', 'HOU', 'TEN', '2027-01-10T05:00+00:00')
ON CONFLICT (espn_event_id) DO UPDATE SET kickoff=EXCLUDED.kickoff;
