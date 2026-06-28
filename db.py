import bcrypt
from supabase_client import get_client


# ── Auth ──────────────────────────────────────────────────────────────────────

def create_user(username: str, password: str) -> dict | None:
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    try:
        res = get_client().table("app_users").insert(
            {"username": username, "password_hash": hashed}
        ).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None

def login_user(username: str, password: str) -> dict | None:
    res = get_client().table("app_users").select("*").eq("username", username).execute()
    if not res.data:
        return None
    user = res.data[0]
    if bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        return user
    return None

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
        get_client().table("matches").update({"winner": winner}).eq("id", match_id).execute()
        return True
    except Exception:
        return False

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
        get_client().table("picks").upsert({
            "user_id": user_id, "round_id": round_id, "team_picked": team
        }).execute()
        return True
    except Exception:
        return False

def get_all_picks_for_round(round_id: int) -> list:
    res = get_client().table("picks").select("*").eq("round_id", round_id).execute()
    return res.data or []


# ── Standings ─────────────────────────────────────────────────────────────────

def get_standings() -> list:
    users = get_client().table("app_users").select(
        "id, username, is_eliminated, eliminated_round_id, created_at"
    ).order("username").execute().data or []

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

    result.sort(key=lambda u: (u["is_eliminated"], u["username"]))
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
    eliminated_names = []
    for p in picks:
        if p["team_picked"] in losers:
            user = get_user_by_id(p["user_id"])
            client.table("app_users").update({
                "is_eliminated": True,
                "eliminated_round_id": round_id,
            }).eq("id", p["user_id"]).execute()
            if user:
                eliminated_names.append(user["username"])

    client.table("rounds").update({"status": "completed"}).eq("id", round_id).execute()

    next_round = client.table("rounds").select("*").eq("id", round_id + 1).execute()
    if next_round.data:
        client.table("rounds").update({"status": "active"}).eq("id", round_id + 1).execute()

    return {"eliminated": eliminated_names, "loser_teams": list(losers)}
