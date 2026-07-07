"""Pull finished World Cup results from football-data.org and propose winners.

Design notes
------------
* We match an API result to one of our matches by the *pair of teams*, not by
  the API's stage label — so we never depend on how they name "Round of 32".
* If a team name can't be resolved to one of our two teams, the match simply
  produces no proposal. A name mismatch can therefore never write a wrong
  winner; it just shows up under "unmatched" for you to fix via NAME_MAP.
* Nothing is written to the DB here — admin.py previews proposals and you
  confirm before anything is saved.
"""
import streamlit as st
import requests
import db

API_BASE = "https://api.football-data.org/v4"
WC_COMPETITION = "WC"  # football-data.org World Cup competition code

# football-data.org team name  ->  our DB team name.
# Only list teams whose API name differs from ours. Extend as needed when a
# match shows up under "unmatched" in the admin preview.
NAME_MAP = {
    "USA": "United States",
    "Côte d'Ivoire": "Ivory Coast",
    "Cote d'Ivoire": "Ivory Coast",
    "Cabo Verde": "Cape Verde",
    "Cape Verde Islands": "Cape Verde",
    "Congo DR": "DR Congo",
    "Bosnia-Herzegovina": "Bosnia and Herzegovina",
}


def _norm(name: str) -> str:
    return NAME_MAP.get(name, name)


def _token() -> str | None:
    try:
        return st.secrets["football_data"]["token"]
    except Exception:
        return None


def fetch_finished_results() -> tuple[dict | None, str | None]:
    """Return ({frozenset({teamA, teamB}): winner_name}, None) or (None, error)."""
    token = _token()
    if not token:
        return None, ("No football-data.org token configured. Add this to "
                      ".streamlit/secrets.toml:\n\n[football_data]\ntoken = \"YOUR_KEY\"")
    try:
        resp = requests.get(
            f"{API_BASE}/competitions/{WC_COMPETITION}/matches",
            headers={"X-Auth-Token": token},
            params={"status": "FINISHED"},
            timeout=15,
        )
        resp.raise_for_status()
    except requests.HTTPError as e:
        code = e.response.status_code if e.response is not None else "?"
        if code == 403:
            return None, "API rejected the token (403). Check your football-data.org key / plan."
        if code == 429:
            return None, "Rate limited by football-data.org (429). Try again in a minute."
        return None, f"API HTTP error {code}."
    except Exception as e:
        return None, f"Could not reach football-data.org: {e}"

    results: dict = {}
    for m in resp.json().get("matches", []):
        home = _norm((m.get("homeTeam") or {}).get("name") or "")
        away = _norm((m.get("awayTeam") or {}).get("name") or "")
        side = (m.get("score") or {}).get("winner")  # HOME_TEAM | AWAY_TEAM | DRAW | None
        if not home or not away:
            continue
        if side == "HOME_TEAM":
            results[frozenset({home, away})] = home
        elif side == "AWAY_TEAM":
            results[frozenset({home, away})] = away
        # DRAW/None => undecided (a live knockout tie); skip
    return results, None


# Our round short_name  ->  football-data.org stage label.
STAGE_MAP = {
    "R32": "LAST_32", "R16": "LAST_16", "QF": "QUARTER_FINALS",
    "SF": "SEMI_FINALS", "F": "FINAL",
}


def fetch_fixtures() -> list:
    """Return [{stage, home, away, utc}] for every WC fixture (names normalized).

    `home`/`away` are None until the bracket resolves them — that's exactly how
    we tell which next-round matchups are known yet.
    """
    token = _token()
    if not token:
        return []
    try:
        resp = requests.get(
            f"{API_BASE}/competitions/{WC_COMPETITION}/matches",
            headers={"X-Auth-Token": token},
            timeout=15,
        )
        resp.raise_for_status()
    except Exception:
        return []
    out = []
    for m in resp.json().get("matches", []):
        h = (m.get("homeTeam") or {}).get("name")
        a = (m.get("awayTeam") or {}).get("name")
        out.append({
            "stage": m.get("stage"),
            "home": _norm(h) if h else None,
            "away": _norm(a) if a else None,
            "utc": m.get("utcDate"),
        })
    return out


def build_next_round(round_id: int, fixtures: list | None = None) -> int:
    """Seed round `round_id + 1` from the API's real, resolved fixtures.

    Reads the true bracket from football-data.org (so pairings are always
    correct — never guessed from match order), and creates any next-round match
    whose *both* teams are known and that we don't already have. Idempotent:
    matches are matched by team-pair, so re-running never duplicates. Also fills
    a kickoff time on a match that exists but is missing one. Returns how many
    matches were newly created.
    """
    nxt = next((r for r in db.get_all_rounds() if r["id"] == round_id + 1), None)
    if not nxt:
        return 0  # nothing after this round (the Final)
    stage = STAGE_MAP.get(nxt.get("short_name"))
    if not stage:
        return 0

    if fixtures is None:
        fixtures = fetch_fixtures()
    if not fixtures:
        return 0

    existing = {frozenset({m["team1"], m["team2"]}): m
                for m in db.get_matches_for_round(nxt["id"])}
    created = 0
    for fx in fixtures:
        if fx["stage"] != stage or not fx["home"] or not fx["away"]:
            continue
        pair = frozenset({fx["home"], fx["away"]})
        if pair in existing:  # already have it — just backfill a missing kickoff
            m = existing[pair]
            if fx["utc"] and not m.get("kickoff_time"):
                db.set_match_schedule(m["id"], fx["utc"])
            continue
        if db.create_match(nxt["id"], fx["home"], fx["away"], kickoff_time=fx["utc"]):
            existing[pair] = {"id": None, "team1": fx["home"], "team2": fx["away"],
                              "kickoff_time": fx["utc"]}
            created += 1
    return created


def auto_apply_results(round_id: int) -> int:
    """Apply finished results for the round straight to the DB. Returns count applied.

    Safe to call on every page load: only writes winners for matches whose
    team-pair matched an API result exactly, so a name mismatch can never
    record a wrong winner (it just stays pending). Whenever a round is fully
    decided, the next round's real matchups are pulled in automatically.
    """
    fixtures = fetch_fixtures()
    data, err = propose_winners(round_id)
    if not err and data:
        for m, w in data["proposals"]:
            db.mark_match_winner(m["id"], w)

    # As soon as the round is complete, seed the next round from the bracket.
    # (Even one resolved matchup is enough — partly-known rounds fill in later.)
    round_matches = db.get_matches_for_round(round_id)
    if round_matches and all(m["winner"] for m in round_matches):
        build_next_round(round_id, fixtures=fixtures)

    return len(data["proposals"]) if (not err and data) else 0


def propose_winners(round_id: int) -> tuple[dict | None, str | None]:
    """For matches in `round_id` with no winner yet, propose winners from the API.

    Returns ({"proposals": [(match, winner)], "unmatched": [match]}, None)
    or (None, error_message).
    """
    results, err = fetch_finished_results()
    if err:
        return None, err

    proposals, unmatched = [], []
    for m in db.get_matches_for_round(round_id):
        if m["winner"]:
            continue
        winner = results.get(frozenset({m["team1"], m["team2"]}))
        if winner in (m["team1"], m["team2"]):
            proposals.append((m, winner))
        else:
            unmatched.append(m)
    return {"proposals": proposals, "unmatched": unmatched}, None
