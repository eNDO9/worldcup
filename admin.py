import streamlit as st
from styles import flag
import db
import results_sync

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

# ── Auto-sync from football-data.org ──────────────────────────────────────────
with st.expander("🔄 Auto-sync results from football-data.org"):
    st.caption("Pulls finished matches from the API and proposes winners. "
               "Nothing is saved until you click Apply.")
    if st.button("Fetch proposed results", key=f"sync_fetch_{selected_round_id}"):
        data, err = results_sync.propose_winners(selected_round_id)
        if err:
            st.session_state.sync_result = {"err": err}
        else:
            st.session_state.sync_result = {
                "round_id": selected_round_id,
                "proposals": [(m["id"], m["team1"], m["team2"], w) for m, w in data["proposals"]],
                "unmatched": [(m["team1"], m["team2"]) for m in data["unmatched"]],
            }

    sr = st.session_state.get("sync_result")
    if sr and sr.get("err"):
        st.error(sr["err"])
    elif sr and sr.get("round_id") == selected_round_id:
        props = sr["proposals"]
        if props:
            st.markdown("**Proposed winners:**")
            for mid, t1, t2, w in props:
                st.markdown(f"- {flag(t1)} {t1} vs {flag(t2)} {t2} → **{flag(w)} {w}**")
            if st.button("✅ Apply all proposed winners", type="primary",
                         key=f"sync_apply_{selected_round_id}"):
                for mid, t1, t2, w in props:
                    db.mark_match_winner(mid, w)
                st.session_state.pop("sync_result", None)
                st.success(f"Applied {len(props)} result(s).")
                st.rerun()
        else:
            st.info("No new finished results found for this round.")
        if sr["unmatched"]:
            st.caption("No API result matched these (pending, or a team-name mismatch "
                       "to fix in results_sync.NAME_MAP):")
            for t1, t2 in sr["unmatched"]:
                st.markdown(f"- {t1} vs {t2}")

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
