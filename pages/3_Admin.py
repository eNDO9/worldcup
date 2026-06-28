import streamlit as st
from styles import inject_css, flag
import db
from db import display_name

st.set_page_config(page_title="Admin", page_icon="⚙️", layout="wide")
inject_css()

if not st.session_state.get("user"):
    st.warning("Please log in first.")
    st.page_link("app.py", label="← Go to Login")
    st.stop()

user = st.session_state.user

with st.sidebar:
    st.markdown(f"### {display_name(user)}")
    st.markdown("---")
    if st.button("Log out", use_container_width=True):
        st.session_state.user = None
        st.rerun()

st.markdown("# ⚙️ Admin Panel")

# Password gate
if "admin_authed" not in st.session_state:
    st.session_state.admin_authed = False

if not st.session_state.admin_authed:
    with st.form("admin_login"):
        pw = st.text_input("Admin password", type="password")
        if st.form_submit_button("Enter"):
            if pw == st.secrets.get("admin", {}).get("password", ""):
                st.session_state.admin_authed = True
                st.rerun()
            else:
                st.error("Wrong password.")
    st.stop()

st.success("Admin access granted.")
st.markdown("---")

rounds = db.get_all_rounds()
round_map = {r["id"]: r for r in rounds}

# ── Section 1: Round status ────────────────────────────────────────────────────
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

# ── Section 2: Enter match results ────────────────────────────────────────────
st.markdown("### Enter Match Results")
selected_round_id = st.selectbox(
    "Select round",
    options=[r["id"] for r in rounds],
    format_func=lambda rid: round_map[rid]["name"],
)

matches = db.get_matches_for_round(selected_round_id)
if not matches:
    st.info("No matches found for this round. Add them below.")
else:
    changed = False
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
                    st.success(f"Winner saved: {winner}")
                    changed = True
                    st.rerun()

    st.markdown("---")
    all_results_in = all(m["winner"] for m in matches)
    if all_results_in:
        st.warning("All results entered. Finalizing will eliminate users whose picks lost and activate the next round.")
        if st.button("🏁 Finalize Round & Advance", type="primary"):
            result = db.finalize_round(selected_round_id)
            if result["eliminated"]:
                st.error(f"Eliminated: {', '.join(result['eliminated'])}")
            else:
                st.success("Round finalized — no one was eliminated!")
            st.rerun()
    else:
        pending = sum(1 for m in matches if not m["winner"])
        st.info(f"{pending} match result(s) still pending.")

st.markdown("---")

# ── Section 3: Add match (for future rounds) ──────────────────────────────────
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
