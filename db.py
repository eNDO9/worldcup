from datetime import datetime, timezone, timedelta

import bcrypt
from supabase_client import get_client

_ET = timezone(timedelta(hours=-4))  # US Eastern (EDT) — tournament runs Jun–Jul


def _et_date(kickoff_iso: str) -> str:
    """Calendar date of a kickoff in US Eastern time. UTC dates roll past
    midnight for evening ET games, so slicing the ISO string is wrong."""
    dt = datetime.fromisoformat(kickoff_iso.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_ET).date().isoformat()


# ── Auth ──────────────────────────────────────────────────────────────────────

def create_user(email: str, password: str) -> dict | None:
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    try:
        res = get_client().table("app_users").insert(
            {"email": email.lower().strip(), "password_hash": hashed}
        ).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None

def login_user(email: str, password: str) -> dict | None:
    res = get_client().table("app_users").select("*").eq("email", email.lower().strip()).execute()
    if not res.data:
        return None
    user = res.data[0]
    if bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        return user
    return None

def display_name(user: dict) -> str:
    return user.get("email", "").split("@")[0]

def get_user_by_id(user_id: str) -> dict | None:
    res = get_client().table("app_users").select("*").eq("id", user_id).execute()
    return res.data[0] if res.data else None


# ── Rounds ────────────────────────────────────────────────────────────────────

def get_all_rounds() -> list:
    res = get_client().table("rounds").select("*").order("id").execute()
    return res.data or []

def get_active_round() -> dict | None:
    res = (get_client().table("rounds").select("*")
           .in_("status", ["active", "locked"]).order("id").limit(1).execute())
    return res.data[0] if res.data else None

def sync_round_deadline(round_id: int) -> str | None:
    """Set the round's deadline to its earliest kickoff. Returns it, or None if no kickoffs."""
    kickoffs = [m["kickoff_time"] for m in get_matches_for_round(round_id) if m.get("kickoff_time")]
    if not kickoffs:
        return None
    first = min(kickoffs)
    get_client().table("rounds").update({"deadline": first}).eq("id", round_id).execute()
    return first

def update_round_status(round_id: int, status: str) -> bool:
    try:
        get_client().table("rounds").update({"status": status}).eq("id", round_id).execute()
        return True
    except Exception:
        return False


# ── Matches ───────────────────────────────────────────────────────────────────

def get_matches_for_round(round_id: int) -> list:
    res = (get_client().table("matches").select("*")
           .eq("round_id", round_id).order("match_date").execute())
    return res.data or []

def add_match(round_id: int, team1: str, team2: str, match_date: str, venue: str) -> bool:
    try:
        get_client().table("matches").insert({
            "round_id": round_id, "team1": team1, "team2": team2,
            "match_date": match_date, "venue": venue,
        }).execute()
        return True
    except Exception:
        return False

def mark_match_winner(match_id: int, winner: str) -> bool:
    try:
        res = get_client().table("matches").select("round_id").eq("id", match_id).execute()
        get_client().table("matches").update({"winner": winner}).eq("id", match_id).execute()
        # Losing a match eliminates its pickers immediately — no waiting for finalize.
        if res.data:
            eliminate_losing_pickers(res.data[0]["round_id"])
        return True
    except Exception:
        return False

def create_match(round_id: int, team1: str, team2: str,
                 match_date: str | None = None, kickoff_time: str | None = None) -> bool:
    """Insert a match, optionally with its scheduled date/kickoff. Used by the
    bracket auto-advance to seed the next round from resolved API fixtures."""
    try:
        row = {"round_id": round_id, "team1": team1, "team2": team2}
        if kickoff_time:
            row["kickoff_time"] = kickoff_time
            row["match_date"] = match_date or _et_date(kickoff_time)
        elif match_date:
            row["match_date"] = match_date
        get_client().table("matches").insert(row).execute()
        return True
    except Exception:
        return False

def set_match_schedule(match_id: int, kickoff_utc: str) -> bool:
    """Set a match's kickoff_time (and match_date as its US-Eastern date)."""
    if not kickoff_utc:
        return False
    try:
        get_client().table("matches").update({
            "kickoff_time": kickoff_utc, "match_date": _et_date(kickoff_utc),
        }).eq("id", match_id).execute()
        return True
    except Exception:
        return False

def existing_pairs_for_round(round_id: int) -> set:
    """Set of frozenset({team1, team2}) already present in a round."""
    return {frozenset({m["team1"], m["team2"]}) for m in get_matches_for_round(round_id)}

def eliminate_losing_pickers(round_id: int) -> list:
    """Eliminate alive players whose pick in this round has already lost."""
    losers = set()
    for m in get_matches_for_round(round_id):
        if m["winner"]:
            losers.add(m["team2"] if m["winner"] == m["team1"] else m["team1"])
    if not losers:
        return []
    client = get_client()
    eliminated = []
    for p in get_all_picks_for_round(round_id):
        if p["team_picked"] in losers:
            user = get_user_by_id(p["user_id"])
            if user and not user["is_eliminated"]:
                client.table("app_users").update({
                    "is_eliminated": True,
                    "eliminated_round_id": round_id,
                }).eq("id", p["user_id"]).execute()
                eliminated.append(display_name(user))
    return eliminated

def eliminate_no_picks(round_id: int) -> list:
    """Eliminate alive players with no pick for this round. Only call after
    the round's deadline has passed. Idempotent."""
    client = get_client()
    picked = {p["user_id"] for p in get_all_picks_for_round(round_id)}
    alive = (client.table("app_users").select("*")
             .eq("is_eliminated", False).execute().data or [])
    eliminated = []
    for user in alive:
        if user["id"] not in picked:
            client.table("app_users").update({
                "is_eliminated": True,
                "eliminated_round_id": round_id,
            }).eq("id", user["id"]).execute()
            eliminated.append(display_name(user) + " (no pick)")
    return eliminated


def teams_in_round(round_id: int) -> set:
    matches = get_matches_for_round(round_id)
    return {t for m in matches for t in (m["team1"], m["team2"])}

def pick_result(team: str, round_id: int) -> str:
    """'won' | 'lost' | 'pending'"""
    res = (get_client().table("matches").select("*")
           .eq("round_id", round_id)
           .or_(f"team1.eq.{team},team2.eq.{team}").execute())
    if not res.data:
        return "pending"
    m = res.data[0]
    if not m["winner"]:
        return "pending"
    return "won" if m["winner"] == team else "lost"


# ── Picks ─────────────────────────────────────────────────────────────────────

def get_user_pick_for_round(user_id: str, round_id: int) -> dict | None:
    res = (get_client().table("picks").select("*")
           .eq("user_id", user_id).eq("round_id", round_id).execute())
    return res.data[0] if res.data else None

def get_user_all_picks(user_id: str) -> list:
    res = (get_client().table("picks").select("*")
           .eq("user_id", user_id).order("round_id").execute())
    return res.data or []

def get_used_teams(user_id: str) -> set:
    return {p["team_picked"] for p in get_user_all_picks(user_id)}

def submit_pick(user_id: str, round_id: int, team: str) -> bool:
    try:
        # Enforce the no-reuse rule server-side: a team picked in any *other*
        # round can never be picked again (belt-and-suspenders behind the UI).
        prior = (get_client().table("picks").select("round_id")
                 .eq("user_id", user_id).eq("team_picked", team).execute().data or [])
        if any(p["round_id"] != round_id for p in prior):
            return False
        get_client().table("picks").upsert(
            {"user_id": user_id, "round_id": round_id, "team_picked": team},
            on_conflict="user_id,round_id",
        ).execute()
        return True
    except Exception:
        return False

def get_all_picks_for_round(round_id: int) -> list:
    res = get_client().table("picks").select("*").eq("round_id", round_id).execute()
    return res.data or []


# ── Standings ─────────────────────────────────────────────────────────────────

def get_standings() -> list:
    users = get_client().table("app_users").select(
        "id, email, is_eliminated, eliminated_round_id, created_at"
    ).order("email").execute().data or []

    picks_all = get_client().table("picks").select("*").execute().data or []
    rounds = {r["id"]: r for r in get_all_rounds()}

    picks_by_user: dict[str, list] = {}
    for p in picks_all:
        picks_by_user.setdefault(p["user_id"], []).append(p)

    result = []
    for u in users:
        result.append({
            **u,
            "picks": sorted(picks_by_user.get(u["id"], []), key=lambda x: x["round_id"]),
            "rounds": rounds,
        })

    result.sort(key=lambda u: (u["is_eliminated"], u.get("email", "")))
    return result


# ── Admin: finalize round ─────────────────────────────────────────────────────

def finalize_round(round_id: int) -> dict:
    client = get_client()
    matches = get_matches_for_round(round_id)

    losers = set()
    for m in matches:
        if m["winner"]:
            loser = m["team2"] if m["winner"] == m["team1"] else m["team1"]
            losers.add(loser)

    picks = get_all_picks_for_round(round_id)
    picks_by_user = {p["user_id"]: p for p in picks}

    # A player is eliminated if their pick lost OR they never made a pick.
    alive = (client.table("app_users").select("*")
             .eq("is_eliminated", False).execute().data or [])
    eliminated_names = []
    for user in alive:
        pick = picks_by_user.get(user["id"])
        if pick is None or pick["team_picked"] in losers:
            client.table("app_users").update({
                "is_eliminated": True,
                "eliminated_round_id": round_id,
            }).eq("id", user["id"]).execute()
            eliminated_names.append(display_name(user)
                                    + ("" if pick else " (no pick)"))

    client.table("rounds").update({"status": "completed"}).eq("id", round_id).execute()

    # Build the next round's bracket from the real fixtures and activate it.
    advanced = 0
    next_round = client.table("rounds").select("*").eq("id", round_id + 1).execute()
    if next_round.data:
        client.table("rounds").update({"status": "active"}).eq("id", round_id + 1).execute()
        try:  # best-effort: pull the next round's real matchups from the API
            import results_sync
            advanced = results_sync.build_next_round(round_id)
        except Exception:
            pass

    return {"eliminated": eliminated_names, "loser_teams": list(losers), "advanced": advanced}
