import streamlit as st
from styles import inject_css, flag
import db

st.set_page_config(page_title="Standings", page_icon="📊", layout="wide")
inject_css()

if not st.session_state.get("user"):
    st.warning("Please log in first.")
    st.page_link("app.py", label="← Go to Login")
    st.stop()

user = st.session_state.user

with st.sidebar:
    st.markdown(f"### {user['username']}")
    badge = '<span class="badge badge-red">Eliminated</span>' if user["is_eliminated"] else '<span class="badge badge-green">Still alive ✓</span>'
    st.markdown(badge, unsafe_allow_html=True)
    st.markdown("---")
    if st.button("Log out", use_container_width=True):
        st.session_state.user = None
        st.rerun()

st.markdown("# 📊 Standings")

standings = db.get_standings()
rounds = db.get_all_rounds()

if not standings:
    st.info("No players yet.")
    st.stop()

alive = [u for u in standings if not u["is_eliminated"]]
out   = [u for u in standings if u["is_eliminated"]]

st.metric("Players Remaining", len(alive), delta=f"-{len(out)} eliminated" if out else None)
st.markdown("---")

def render_player(u, rounds):
    is_me = u["id"] == user["id"]
    border = "gold" if is_me else ("red" if u["is_eliminated"] else "")
    badge = ('<span class="badge badge-red">Eliminated</span>' if u["is_eliminated"]
             else '<span class="badge badge-green">Alive</span>')
    name_html = f'<b>{u["username"]}</b>{"&nbsp; 👈 you" if is_me else ""}'

    picks_html = ""
    for p in u["picks"]:
        rnd = u["rounds"].get(p["round_id"], {})
        result = db.pick_result(p["team_picked"], p["round_id"])
        icon = "✅" if result == "won" else "❌" if result == "lost" else "⏳"
        picks_html += f'<span style="margin-right:1rem;font-size:0.9rem;">{icon} {flag(p["team_picked"])} {p["team_picked"]} <span style="color:#475569;font-size:0.75rem;">({rnd.get("short_name","")})</span></span>'

    st.markdown(
        f'<div class="wc-card {border}">'
        f'{name_html} &nbsp; {badge}<br>'
        f'<div style="margin-top:6px;">{picks_html if picks_html else "<span style=\'color:#475569;font-size:0.85rem;\'>No picks yet</span>"}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

if alive:
    st.markdown(f"### 🟢 Still In ({len(alive)})")
    for u in alive:
        render_player(u, rounds)

if out:
    st.markdown(f"### 💀 Eliminated ({len(out)})")
    for u in out:
        render_player(u, rounds)
