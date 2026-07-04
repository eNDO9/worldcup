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


def auto_apply_results(round_id: int) -> int:
    """Apply finished results for the round straight to the DB. Returns count applied.

    Safe to call on every page load: only writes winners for matches whose
    team-pair matched an API result exactly, so a name mismatch can never
    record a wrong winner (it just stays pending).
    """
    data, err = propose_winners(round_id)
    if err or not data:
        return 0
    for m, w in data["proposals"]:
        db.mark_match_winner(m["id"], w)
    return len(data["proposals"])


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
