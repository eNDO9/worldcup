import streamlit as st
from datetime import datetime, timezone, timedelta
from styles import flag
import db

st.markdown("# 🗓️ Bracket")
st.caption("Live from the pool — updates automatically as results are entered.")
st.markdown("---")

ET = timezone(timedelta(hours=-4))  # US Eastern (EDT) — tournament runs Jun–Jul
EXPECTED = {"R32": 16, "R16": 8, "QF": 4, "SF": 2, "F": 1}


def match_when(m: dict) -> str:
    kt = m.get("kickoff_time")
    if kt:
        try:
            dt = datetime.fromisoformat(str(kt).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(ET).strftime("%b %-d · %-I:%M %p ET")
        except ValueError:
            pass
    d = m.get("match_date")
    if d:
        try:
            return datetime.strptime(d, "%Y-%m-%d").strftime("%b %-d")
        except ValueError:
            return d
    return ""


def feeder_order(earlier: list, later: list) -> list:
    """Order `earlier`-round matches so each pair feeds a `later` match in order."""
    by_team = {}
    for m in earlier:
        by_team.setdefault(m["team1"], m)
        by_team.setdefault(m["team2"], m)
    ordered, seen = [], set()
    for lm in later:
        for t in (lm["team1"], lm["team2"]):
            em = by_team.get(t)
            if em and em["id"] not in seen:
                ordered.append(em)
                seen.add(em["id"])
    for m in earlier:  # any that didn't map (safety) go last
        if m["id"] not in seen:
            ordered.append(m)
    return ordered


rounds = db.get_all_rounds()
matches_by_round = {r["id"]: db.get_matches_for_round(r["id"]) for r in rounds}

# Right-to-left: keep the rightmost populated round in id order, then order each
# earlier round so its matches sit next to the later match they feed.
ordered_by_round, next_ordered = {}, None
for r in reversed(rounds):
    ms = matches_by_round[r["id"]]
    if ms:
        ms = feeder_order(ms, next_ordered) if next_ordered else sorted(ms, key=lambda x: x["id"])
        ordered_by_round[r["id"]] = ms
        next_ordered = ms
    else:
        ordered_by_round[r["id"]] = None


user = st.session_state.user
my_picks = {p["round_id"]: p["team_picked"] for p in db.get_user_all_picks(user["id"])}


def team_row(team: str, winner: str | None, my_team: str | None) -> str:
    cls = "bteam win" if winner == team else "bteam lose" if winner else "bteam"
    if team == my_team:
        cls += " mine"
    star = ' <span class="mystar">★</span>' if team == my_team else ""
    return f'<div class="{cls}">{flag(team)} <span>{team}{star}</span></div>'


def match_cell(m: dict, my_team: str | None) -> str:
    when = match_when(m)
    date_row = f'<div class="bdate">{when}</div>' if when else ""
    return (f'<div class="bmatch"><div class="bcard">{date_row}'
            f'{team_row(m["team1"], m["winner"], my_team)}{team_row(m["team2"], m["winner"], my_team)}'
            f'</div></div>')


def placeholder_cell() -> str:
    tbd = '<div class="bteam tbd">🏳️ <span>TBD</span></div>'
    return f'<div class="bmatch"><div class="bcard">{tbd}{tbd}</div></div>'


cols = []
for r in rounds:
    ms = ordered_by_round[r["id"]]
    my_team = my_picks.get(r["id"])
    if ms:
        cells = [match_cell(m, my_team) for m in ms]
        col_cls = "bcol"
    else:
        cells = [placeholder_cell() for _ in range(EXPECTED.get(r.get("short_name"), 0))]
        col_cls = "bcol bcol-empty"
    cols.append(
        f'<div class="{col_cls}"><div class="bcol-title">{r.get("short_name", r["name"])}</div>'
        f'<div class="bcol-body">{"".join(cells)}</div></div>'
    )

# Bracket height must fit the first (largest) round's cards without overlap.
# Row height is kept safely above the real card height so the equal-height
# flex cells stay aligned (otherwise the first column overflows and the
# connectors miss their targets).
ROW_H = 90
height = EXPECTED["R32"] * ROW_H + 34

CSS = f"""
<style>
.bracket-scroll {{ overflow-x: auto; padding-bottom: 1rem; }}
.bracket {{ display: flex; min-width: 920px; height: {height}px; padding-right: 20px; }}
.bcol {{ display: flex; flex-direction: column; flex: 1 1 0; min-width: 172px; }}
.bcol.bcol-empty {{ flex: 0.72 1 0; min-width: 118px; }}
.bcol-title {{
    flex: 0 0 auto; height: 26px; text-align: center; color: #94a3b8;
    font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.08em; border-bottom: 1px solid #2d3f55; margin-bottom: 6px;
}}
.bcol-body {{ display: flex; flex-direction: column; flex: 1 1 auto; }}
.bmatch {{ flex: 1 1 0; display: flex; align-items: center; position: relative; padding: 0 12px; }}
.bcard {{
    width: 100%; background: #1e293b; border: 1px solid #334155;
    border-radius: 8px; overflow: hidden;
}}
.bdate {{
    font-size: 0.68rem; color: #8fa2b8; text-align: center; padding: 1px 6px;
    background: #172033; border-bottom: 1px solid #0f172a;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}}
.bteam {{
    padding: 4px 9px; font-size: 0.74rem; display: flex; align-items: center;
    gap: 6px; color: #cbd5e1; white-space: nowrap; border-bottom: 1px solid #0f172a;
}}
.bteam:last-child {{ border-bottom: none; }}
.bteam span {{ overflow: hidden; text-overflow: ellipsis; }}
.bteam.win {{ background: rgba(34,197,94,0.12); color: #86efac !important; font-weight: 700; border-left: 3px solid #22c55e; }}
.bteam.lose {{ opacity: 0.45; }}
.bteam.lose span {{ text-decoration: line-through; }}
.bteam.tbd {{ color: #64748b; font-style: italic; }}
.bteam.mine {{ box-shadow: inset 0 0 0 1.5px #f59e0b; }}
.bteam .mystar {{ color: #f59e0b; font-size: 0.7rem; }}

/* Connectors: each odd match draws a "]" bracket linking its pair; each match
   after the first column draws a short stub reaching left to meet it. */
.bcol:not(:last-child) .bmatch:nth-child(odd)::after {{
    content: ''; position: absolute; right: 0; top: 50%; width: 12px; height: 100%;
    border: 2px solid #2d3f55; border-left: 0;
    border-top-right-radius: 7px; border-bottom-right-radius: 7px;
}}
.bcol:not(:first-child) .bmatch::before {{
    content: ''; position: absolute; left: 0; top: 50%; width: 12px; height: 2px; background: #2d3f55;
}}
</style>
"""

st.markdown(CSS + f'<div class="bracket-scroll"><div class="bracket">{"".join(cols)}</div></div>',
            unsafe_allow_html=True)
