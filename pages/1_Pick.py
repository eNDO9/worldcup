import streamlit as st
from datetime import datetime, timezone
from styles import inject_css, flag
import db

st.set_page_config(page_title="Pick", page_icon="🎯", layout="wide")
inject_css()

if not st.session_state.get("user"):
    st.warning("Please log in first.")
    st.page_link("app.py", label="← Go to Login")
    st.stop()

user = db.get_user_by_id(st.session_state.user["id"]) or st.session_state.user
st.session_state.user = user

with st.sidebar:
    st.markdown(f"### {user['username']}")
    badge = '<span class="badge badge-red">Eliminated</span>' if user["is_eliminated"] else '<span class="badge badge-green">Still alive ✓</span>'
    st.markdown(badge, unsafe_allow_html=True)
    st.markdown("---")
    if st.button("Log out", use_container_width=True):
        st.session_state.user = None
        st.rerun()

st.markdown("# 🎯 Make Your Pick")

if user["is_eliminated"]:
    rounds = {r["id"]: r for r in db.get_all_rounds()}
    elim_round = rounds.get(user["eliminated_round_id"], {}).get("name", "a previous round")
    st.markdown(f"""
    <div class="wc-card red">
        <h3 style="color:#fca5a5;">💀 Eliminated in {elim_round}</h3>
        <p>Your picked team was knocked out. See your picks below.</p>
    </div>
    """, unsafe_allow_html=True)
    picks = db.get_user_all_picks(user["id"])
    for p in picks:
        rnd = rounds.get(p["round_id"], {})
        result = db.pick_result(p["team_picked"], p["round_id"])
        icon = "✅" if result == "won" else "❌" if result == "lost" else "⏳"
        st.markdown(f"**{rnd.get('name','')}:** {icon} {flag(p['team_picked'])} {p['team_picked']}")
    st.stop()

active_round = db.get_active_round()
if not active_round:
    st.info("No active round. Check back when the next round opens.")
    st.stop()

now = datetime.now(timezone.utc)
deadline = datetime.fromisoformat(active_round["deadline"].replace("Z", "+00:00"))
time_left = deadline - now
locked = time_left.total_seconds() <= 0 or active_round["status"] == "locked"

# Round header
col_a, col_b = st.columns(2)
with col_a:
    st.markdown(f"### {active_round['name']}")
with col_b:
    if not locked:
        h, m = int(time_left.total_seconds() // 3600), int((time_left.total_seconds() % 3600) // 60)
        st.markdown(f"🕐 Deadline: **{deadline.strftime('%b %d, %I:%M %p UTC')}** &nbsp;|&nbsp; ⏳ {h}h {m}m left", unsafe_allow_html=True)
    else:
        st.markdown("🔒 **Picks are locked**")

st.markdown("---")

existing_pick = db.get_user_pick_for_round(user["id"], active_round["id"])
used_teams = db.get_used_teams(user["id"])
matches = db.get_matches_for_round(active_round["id"])

# Already picked this round
if existing_pick:
    team = existing_pick["team_picked"]
    result = db.pick_result(team, active_round["id"])
    color = "green" if result == "won" else "red" if result == "lost" else "gold"
    icon  = "✅" if result == "won" else "❌" if result == "lost" else "⏳"
    badge_cls = "badge-green" if result == "won" else "badge-red" if result == "lost" else "badge-gold"
    badge_lbl = result.capitalize() if result != "pending" else "Awaiting result"
    st.markdown(f"""
    <div class="wc-card {color}">
        <p style="color:#94a3b8;margin:0;font-size:0.8rem;text-transform:uppercase;letter-spacing:.06em;">Your pick this round</p>
        <h2 style="margin:6px 0 4px;">{icon} {flag(team)} {team}</h2>
        <span class="badge {badge_cls}">{badge_lbl}</span>
    </div>
    """, unsafe_allow_html=True)

    if locked:
        st.markdown("---")
        st.markdown("### Teams You've Used")
        _prev = [p for p in db.get_user_all_picks(user["id"]) if p["round_id"] != active_round["id"]]
        rounds_map = {r["id"]: r["name"] for r in db.get_all_rounds()}
        for p in _prev:
            st.markdown(f"~~{flag(p['team_picked'])} {p['team_picked']}~~ — *{rounds_map.get(p['round_id'], '')}*")
        st.stop()
    else:
        st.caption("Want to change? Select a different team below before the deadline.")

if locked and not existing_pick:
    st.warning("Picks are closed and you didn't submit one for this round.")
    st.stop()

if not locked:
    if "selected_team" not in st.session_state:
        st.session_state.selected_team = existing_pick["team_picked"] if existing_pick else None

    # Exclude already-used teams from prior rounds (not current round pick — that can be changed)
    prior_used = used_teams - ({existing_pick["team_picked"]} if existing_pick else set())

    st.markdown("### Select a Team")
    st.caption("Gray = already used in a previous round and cannot be picked again.")

    for match in matches:
        c1, mid, c2 = st.columns([5, 1, 5])

        for team, col in [(match["team1"], c1), (match["team2"], c2)]:
            used = team in prior_used
            selected = st.session_state.selected_team == team
            label = f"{'✓ ' if selected else ''}{flag(team)} {team}"
            with col:
                if st.button(label, key=f"pick_{match['id']}_{team}", disabled=used, use_container_width=True):
                    st.session_state.selected_team = team
                    st.rerun()

        with mid:
            st.markdown(
                f"<div style='text-align:center;padding-top:10px;color:#475569;font-size:0.85rem;'>"
                f"{match.get('match_date','')}<br><b>vs</b></div>",
                unsafe_allow_html=True,
            )

    st.markdown("---")

    sel = st.session_state.get("selected_team")
    if sel:
        c_info, c_btn = st.columns([3, 2])
        with c_info:
            st.markdown(f"**Selected:** {flag(sel)} **{sel}**")
        with c_btn:
            if st.button(f"✅ Confirm — {sel}", type="primary", use_container_width=True):
                if db.submit_pick(user["id"], active_round["id"], sel):
                    st.session_state.selected_team = None
                    st.success(f"Pick saved: {flag(sel)} {sel}")
                    st.rerun()
                else:
                    st.error("Something went wrong. Please try again.")
    else:
        st.info("Select a team above, then confirm.")

st.markdown("---")
st.markdown("### Teams You've Already Used")
rounds_map = {r["id"]: r["name"] for r in db.get_all_rounds()}
prior_picks = [p for p in db.get_user_all_picks(user["id"]) if p["round_id"] != active_round["id"]]
if prior_picks:
    for p in prior_picks:
        st.markdown(f"~~{flag(p['team_picked'])} {p['team_picked']}~~ — *{rounds_map.get(p['round_id'], '')}*")
else:
    st.caption("None yet.")
