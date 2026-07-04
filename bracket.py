import streamlit as st
from styles import flag
import db

st.markdown("# 🗓️ Bracket")
st.caption("Live from the pool — updates automatically as results are entered.")
st.markdown("---")

# Expected match count per round, used to draw TBD placeholders for rounds
# whose matches haven't been created yet.
EXPECTED = {"R32": 16, "R16": 8, "QF": 4, "SF": 2, "F": 1}

CSS = """
<style>
.bracket-scroll { overflow-x: auto; padding-bottom: 1rem; }
.bracket { display: flex; gap: 20px; min-width: 760px; }
.bcol { display: flex; flex-direction: column; flex: 1; min-width: 150px; }
.bcol-title {
    text-align: center; color: #94a3b8; font-size: 0.72rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 10px;
    padding-bottom: 6px; border-bottom: 1px solid #2d3f55;
}
.bcol-body { display: flex; flex-direction: column; justify-content: space-around; flex: 1; }
.bmatch {
    background: #1e293b; border: 1px solid #334155; border-radius: 8px;
    overflow: hidden; margin: 7px 0;
}
.bteam {
    padding: 6px 10px; font-size: 0.8rem; display: flex; align-items: center;
    gap: 6px; color: #cbd5e1; white-space: nowrap; border-bottom: 1px solid #0f172a;
}
.bteam:last-child { border-bottom: none; }
.bteam span { overflow: hidden; text-overflow: ellipsis; }
.bteam.win {
    background: rgba(34,197,94,0.12); color: #86efac !important;
    font-weight: 700; border-left: 3px solid #22c55e;
}
.bteam.lose { opacity: 0.45; }
.bteam.lose span { text-decoration: line-through; }
.bteam.tbd { color: #475569; font-style: italic; }
</style>
"""


def _team_cell(team: str, winner: str | None) -> str:
    if winner and winner == team:
        cls = "bteam win"
    elif winner and winner != team:
        cls = "bteam lose"
    else:
        cls = "bteam"
    return f'<div class="{cls}">{flag(team)} <span>{team}</span></div>'


cols = []
for r in db.get_all_rounds():
    matches = db.get_matches_for_round(r["id"])
    cards = []
    if matches:
        for m in sorted(matches, key=lambda x: x["id"]):
            cards.append(
                f'<div class="bmatch">{_team_cell(m["team1"], m["winner"])}'
                f'{_team_cell(m["team2"], m["winner"])}</div>'
            )
    else:
        tbd = '<div class="bteam tbd">🏳️ <span>TBD</span></div>'
        for _ in range(EXPECTED.get(r.get("short_name"), 0)):
            cards.append(f'<div class="bmatch">{tbd}{tbd}</div>')
    cols.append(
        f'<div class="bcol"><div class="bcol-title">{r.get("short_name", r["name"])}</div>'
        f'<div class="bcol-body">{"".join(cards)}</div></div>'
    )

st.markdown(CSS + f'<div class="bracket-scroll"><div class="bracket">{"".join(cols)}</div></div>',
            unsafe_allow_html=True)
