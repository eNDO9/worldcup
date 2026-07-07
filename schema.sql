CREATE TABLE IF NOT EXISTS public.rounds (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    short_name TEXT,
    deadline TIMESTAMPTZ NOT NULL,
    status TEXT DEFAULT 'upcoming' CHECK (status IN ('upcoming', 'active', 'locked', 'completed'))
);

CREATE TABLE IF NOT EXISTS public.matches (
    id SERIAL PRIMARY KEY,
    round_id INTEGER REFERENCES public.rounds(id),
    team1 TEXT NOT NULL,
    team2 TEXT NOT NULL,
    match_date DATE,
    kickoff_time TIMESTAMPTZ,
    venue TEXT,
    winner TEXT
);

CREATE TABLE IF NOT EXISTS public.app_users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    is_eliminated BOOLEAN DEFAULT FALSE,
    eliminated_round_id INTEGER REFERENCES public.rounds(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.picks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.app_users(id) ON DELETE CASCADE,
    round_id INTEGER REFERENCES public.rounds(id),
    team_picked TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, round_id)
);

-- Rounds
INSERT INTO public.rounds (name, short_name, deadline, status) VALUES
('Round of 32', 'R32', '2026-06-28 23:59:59+00', 'active'),
('Round of 16', 'R16', '2026-07-04 17:00:00+00', 'upcoming'),
('Quarterfinals', 'QF',  '2026-07-09 17:00:00+00', 'upcoming'),
('Semifinals',   'SF',  '2026-07-14 17:00:00+00', 'upcoming'),
('Final',        'F',   '2026-07-19 17:00:00+00', 'upcoming')
ON CONFLICT DO NOTHING;

-- Round of 32 matches
INSERT INTO public.matches (round_id, team1, team2, match_date, venue) VALUES
(1, 'South Africa', 'Canada',                  '2026-06-28', 'Inglewood'),
(1, 'Germany',      'Paraguay',                '2026-06-29', 'Foxborough'),
(1, 'Netherlands',  'Morocco',                 '2026-06-29', 'Guadalupe'),
(1, 'Brazil',       'Japan',                   '2026-06-29', 'Houston'),
(1, 'France',       'Sweden',                  '2026-06-30', 'East Rutherford'),
(1, 'Ivory Coast',  'Norway',                  '2026-06-30', 'Arlington'),
(1, 'Mexico',       'Ecuador',                 '2026-06-30', 'Mexico City'),
(1, 'United States','Bosnia and Herzegovina',  '2026-07-01', 'Santa Clara'),
(1, 'Belgium',      'Senegal',                 '2026-07-01', 'Seattle'),
(1, 'England',      'DR Congo',                '2026-07-01', 'Atlanta'),
(1, 'Portugal',     'Croatia',                 '2026-07-02', 'Toronto'),
(1, 'Spain',        'Austria',                 '2026-07-02', 'Inglewood'),
(1, 'Switzerland',  'Algeria',                 '2026-07-02', 'Vancouver'),
(1, 'Argentina',    'Cape Verde',              '2026-07-03', 'Miami Gardens'),
(1, 'Australia',    'Egypt',                   '2026-07-03', 'Arlington'),
(1, 'Colombia',     'Ghana',                   '2026-07-03', 'Kansas City')
ON CONFLICT DO NOTHING;
