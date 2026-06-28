import streamlit as st
from datetime import datetime, timezone
from styles import flag
import db

user = st.session_state.user
active_round = db.get_active_round()
rounds_map = {r["id"]: r for r in db.get_all_rounds()}

st.markdown("# ⚽ World Cup Survivor")
st.markdown("---")

if active_round:
    now = datetime.now(timezone.utc)
    deadline = datetime.fromisoformat(active_round["deadline"].replace("Z", "+00:00"))
    time_left = deadline - now
    locked = time_left.total_seconds() <= 0 or active_round["status"] == "locked"

    existing_pick = db.get_user_pick_for_round(user["id"], active_round["id"])
    used_teams = db.get_used_teams(user["id"])
    matches = db.get_matches_for_round(active_round["id"])

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("Round", active_round["name"])
    with col_b:
        if not locked:
            h = int(time_left.total_seconds() // 3600)
            m = int((time_left.total_seconds() % 3600) // 60)
            st.metric("Deadline", f"{h}h {m}m")
        else:
            st.metric("Deadline", "Locked 🔒")
    with col_c:
        if existing_pick:
            st.metric("Your Pick", f"{flag(existing_pick['team_picked'])} {existing_pick['team_picked']}")
        else:
            st.metric("Your Pick", "None yet")

    st.markdown("---")

    if user["is_eliminated"]:
        elim = rounds_map.get(user["eliminated_round_id"], {}).get("name", "a previous round")
        st.markdown(f'<div class="wc-card red"><h3 style="color:#fca5a5;margin:0;">💀 Eliminated in {elim}</h3></div>',
                    unsafe_allow_html=True)

    elif existing_pick:
        team = existing_pick["team_picked"]
        result = db.pick_result(team, active_round["id"])
        color = "green" if result == "won" else "red" if result == "lost" else "gold"
        icon  = "✅" if result == "won" else "❌" if result == "lost" else "⏳"
        badge_cls = "badge-green" if result == "won" else "badge-red" if result == "lost" else "badge-gold"
        badge_lbl = "Won — you advance!" if result == "won" else "Lost — eliminated" if result == "lost" else "Awaiting result"
        st.markdown(f"""
        <div class="wc-card {color}">
            <p style="color:#94a3b8;margin:0;font-size:0.8rem;text-transform:uppercase;letter-spacing:.06em;">Your pick this round</p>
            <h2 style="margin:6px 0 4px;">{icon} {flag(team)} {team}</h2>
            <span class="badge {badge_cls}">{badge_lbl}</span>
        </div>
        """, unsafe_allow_html=True)
        if not locked:
            st.caption("Want to change? Select a different team below before the deadline.")

    if not locked and not user["is_eliminated"]:
        prior_used = used_teams - ({existing_pick["team_picked"]} if existing_pick else set())

        if not existing_pick:
            st.markdown("### Pick your team")
            st.caption("Select a team, then confirm. Grayed out = already used in a previous round.")

        if "selected_team" not in st.session_state:
            st.session_state.selected_team = None

        for match in matches:
            c1, mid, c2 = st.columns([5, 1, 5])
            for team, col in [(match["team1"], c1), (match["team2"], c2)]:
                used = team in prior_used
                selected = st.session_state.selected_team == team
                with col:
                    if st.button(f"{flag(team)} {team}", key=f"pick_{match['id']}_{team}",
                                 disabled=used, use_container_width=True,
                                 type="primary" if selected else "secondary"):
                        st.session_state.selected_team = team
                        st.rerun()
            with mid:
                st.markdown(
                    f"<div style='text-align:center;padding-top:10px;color:#475569;font-size:0.8rem;'>"
                    f"{match.get('match_date','')}<br><b style='color:#64748b;'>vs</b></div>",
                    unsafe_allow_html=True,
                )

        sel = st.session_state.get("selected_team")
        if sel:
            st.markdown("---")
            ci, cb = st.columns([3, 2])
            with ci:
                st.markdown(f"**Selected:** {flag(sel)} **{sel}**")
            with cb:
                if st.button(f"✅ Confirm — {sel}", type="primary", use_container_width=True):
                    if db.submit_pick(user["id"], active_round["id"], sel):
                        st.session_state.selected_team = None
                        st.rerun()
                    else:
                        st.error("Something went wrong.")
else:
    st.info("No active round. Check back soon!")

# ── Pick history ──────────────────────────────────────────────────────────────
all_picks = db.get_user_all_picks(user["id"])
past_picks = [p for p in all_picks if p["round_id"] != (active_round["id"] if active_round else None)]

if past_picks:
    st.markdown("---")
    st.markdown("### Your pick history")
    for p in past_picks:
        rnd = rounds_map.get(p["round_id"], {})
        result = db.pick_result(p["team_picked"], p["round_id"])
        icon  = "✅" if result == "won" else "❌" if result == "lost" else "⏳"
        badge = (f'<span class="badge badge-green">Won</span>' if result == "won"
                 else f'<span class="badge badge-red">Lost</span>' if result == "lost"
                 else f'<span class="badge badge-gray">Pending</span>')
        st.markdown(
            f'<div class="wc-card"><span style="color:#94a3b8;font-size:0.8rem;">{rnd.get("name","")}</span><br>'
            f'<span style="font-size:1.05rem;">{icon} {flag(p["team_picked"])} <b>{p["team_picked"]}</b></span>'
            f' &nbsp;{badge}</div>',
            unsafe_allow_html=True,
        )

# ── Can't reuse reminder ──────────────────────────────────────────────────────
if all_picks and active_round:
    prior = [p for p in all_picks if p["round_id"] != active_round["id"]]
    if prior:
        st.markdown("---")
        st.markdown("### Teams you can't reuse")
        cols = st.columns(4)
        for i, p in enumerate(prior):
            with cols[i % 4]:
                st.markdown(
                    f'<div style="text-align:center;padding:8px;background:#1e293b;border:1px solid #334155;'
                    f'border-radius:8px;margin-bottom:6px;opacity:0.5;">'
                    f'{flag(p["team_picked"])}<br><small>~~{p["team_picked"]}~~</small></div>',
                    unsafe_allow_html=True,
                )
