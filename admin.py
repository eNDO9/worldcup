import streamlit as st
from styles import flag
import db

user = st.session_state.user

st.markdown("# ⚙️ Admin Panel")

rounds = db.get_all_rounds()
round_map = {r["id"]: r for r in rounds}

# ── Round status ──────────────────────────────────────────────────────────────
st.markdown("### Round Status")
for r in rounds:
    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown(f"**{r['name']}** — `{r['status']}`")
    with col2:
        options = ["upcoming", "active", "locked", "completed"]
        new_status = st.selectbox("", options, index=options.index(r["status"]),
                                  key=f"status_{r['id']}", label_visibility="collapsed")
        if new_status != r["status"]:
            if st.button("Update", key=f"upd_{r['id']}"):
                db.update_round_status(r["id"], new_status)
                st.success(f"Updated {r['name']} → {new_status}")
                st.rerun()

st.markdown("---")

# ── Match results ─────────────────────────────────────────────────────────────
st.markdown("### Enter Match Results")
selected_round_id = st.selectbox(
    "Select round",
    options=[r["id"] for r in rounds],
    format_func=lambda rid: round_map[rid]["name"],
)
matches = db.get_matches_for_round(selected_round_id)

if not matches:
    st.info("No matches for this round yet. Add them below.")
else:
    for m in matches:
        c1, c2, c3 = st.columns([4, 4, 3])
        with c1:
            st.markdown(f"{flag(m['team1'])} **{m['team1']}**")
        with c2:
            st.markdown(f"{flag(m['team2'])} **{m['team2']}**")
        with c3:
            options = ["— pending —", m["team1"], m["team2"]]
            current = m["winner"] if m["winner"] in (m["team1"], m["team2"]) else "— pending —"
            winner = st.selectbox("", options, index=options.index(current),
                                  key=f"winner_{m['id']}", label_visibility="collapsed")
            if winner != current and winner != "— pending —":
                if st.button("Save", key=f"save_{m['id']}"):
                    db.mark_match_winner(m["id"], winner)
                    st.success(f"Saved: {winner}")
                    st.rerun()

    st.markdown("---")
    all_done = all(m["winner"] for m in matches)
    if all_done:
        st.warning("All results entered. Finalizing eliminates players whose pick lost and activates the next round.")
        if st.button("🏁 Finalize Round & Advance", type="primary"):
            result = db.finalize_round(selected_round_id)
            if result["eliminated"]:
                st.error(f"Eliminated: {', '.join(result['eliminated'])}")
            else:
                st.success("Round finalized — no one eliminated!")
            st.rerun()
    else:
        pending = sum(1 for m in matches if not m["winner"])
        st.info(f"{pending} result(s) still pending.")

st.markdown("---")

# ── Add match ─────────────────────────────────────────────────────────────────
st.markdown("### Add Match")
with st.form("add_match"):
    col1, col2 = st.columns(2)
    with col1:
        a_round = st.selectbox("Round", options=[r["id"] for r in rounds],
                               format_func=lambda rid: round_map[rid]["name"])
        team1 = st.text_input("Team 1")
        team2 = st.text_input("Team 2")
    with col2:
        match_date = st.date_input("Date")
        venue = st.text_input("Venue")
    if st.form_submit_button("Add Match"):
        if team1 and team2:
            if db.add_match(a_round, team1, team2, str(match_date), venue):
                st.success(f"Added: {team1} vs {team2}")
                st.rerun()
            else:
                st.error("Failed to add match.")
        else:
            st.warning("Enter both team names.")
