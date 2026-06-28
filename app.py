import streamlit as st
from datetime import datetime, timezone
from styles import inject_css, flag
import db

st.set_page_config(
    page_title="World Cup Survivor",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

if "user" not in st.session_state:
    st.session_state.user = None


def sidebar_user(user):
    with st.sidebar:
        st.markdown(f"### {user['username']}")
        if user["is_eliminated"]:
            st.markdown('<span class="badge badge-red">Eliminated</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="badge badge-green">Still alive ✓</span>', unsafe_allow_html=True)
        st.markdown("---")
        if st.button("Log out", use_container_width=True):
            st.session_state.user = None
            st.rerun()


# ── Logged in ─────────────────────────────────────────────────────────────────
if st.session_state.user:
    user = db.get_user_by_id(st.session_state.user["id"]) or st.session_state.user
    st.session_state.user = user
    sidebar_user(user)

    st.markdown("# ⚽ World Cup Survivor Pool")
    st.markdown("Pick one team per round. Never reuse a team. Pick a loser and you're out.")
    st.markdown("---")

    active_round = db.get_active_round()
    if active_round:
        now = datetime.now(timezone.utc)
        deadline = datetime.fromisoformat(active_round["deadline"].replace("Z", "+00:00"))
        time_left = deadline - now
        locked = time_left.total_seconds() <= 0 or active_round["status"] == "locked"

        pick = db.get_user_pick_for_round(user["id"], active_round["id"])

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current Round", active_round["name"])
        with col2:
            if not locked:
                h = int(time_left.total_seconds() // 3600)
                m = int((time_left.total_seconds() % 3600) // 60)
                st.metric("Deadline", f"{h}h {m}m")
            else:
                st.metric("Deadline", "Locked 🔒")
        with col3:
            if pick:
                st.metric("Your Pick", f"{flag(pick['team_picked'])} {pick['team_picked']}")
            else:
                st.metric("Your Pick", "None yet")

        st.markdown("---")
        if not pick and not locked and not user["is_eliminated"]:
            st.info("👈 Head to **Pick** in the sidebar to make your selection.")
        elif pick:
            result = db.pick_result(pick["team_picked"], active_round["id"])
            if result == "won":
                st.success(f"✅ {flag(pick['team_picked'])} **{pick['team_picked']}** won — you advance!")
            elif result == "lost":
                st.error(f"❌ {flag(pick['team_picked'])} **{pick['team_picked']}** lost — you've been eliminated.")
            else:
                st.info(f"⏳ Awaiting result for {flag(pick['team_picked'])} **{pick['team_picked']}**")
    else:
        st.info("No active round right now. Check back soon!")

    # Past picks summary
    all_picks = db.get_user_all_picks(user["id"])
    rounds = {r["id"]: r for r in db.get_all_rounds()}
    if all_picks:
        st.markdown("### Your Pick History")
        for p in all_picks:
            rnd = rounds.get(p["round_id"], {})
            result = db.pick_result(p["team_picked"], p["round_id"])
            icon = "✅" if result == "won" else ("❌" if result == "lost" else "⏳")
            badge = (f'<span class="badge badge-green">Won</span>' if result == "won"
                     else f'<span class="badge badge-red">Lost</span>' if result == "lost"
                     else f'<span class="badge badge-gray">Pending</span>')
            st.markdown(
                f'<div class="wc-card">'
                f'<span style="color:#94a3b8;font-size:0.8rem;">{rnd.get("name","")}</span><br>'
                f'<span style="font-size:1.1rem;">{icon} {flag(p["team_picked"])} <b>{p["team_picked"]}</b></span>'
                f' &nbsp; {badge}'
                f'</div>',
                unsafe_allow_html=True,
            )

# ── Logged out ────────────────────────────────────────────────────────────────
else:
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        st.markdown("# ⚽ World Cup Survivor")
        st.markdown("#### Pick one team per round. Never reuse a team. Last one standing wins.")
        st.markdown("---")

        tab1, tab2 = st.tabs(["Log In", "Sign Up"])

        with tab1:
            with st.form("login"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Log In", use_container_width=True):
                    if username and password:
                        user = db.login_user(username, password)
                        if user:
                            st.session_state.user = user
                            st.rerun()
                        else:
                            st.error("Invalid username or password.")
                    else:
                        st.warning("Please fill in both fields.")

        with tab2:
            with st.form("signup"):
                new_user = st.text_input("Choose a username")
                new_pass = st.text_input("Choose a password", type="password")
                confirm  = st.text_input("Confirm password", type="password")
                if st.form_submit_button("Create Account", use_container_width=True):
                    if not (new_user and new_pass and confirm):
                        st.warning("Please fill in all fields.")
                    elif new_pass != confirm:
                        st.error("Passwords don't match.")
                    elif len(new_pass) < 6:
                        st.error("Password must be at least 6 characters.")
                    else:
                        user = db.create_user(new_user, new_pass)
                        if user:
                            st.session_state.user = user
                            st.rerun()
                        else:
                            st.error("Username already taken — try another.")
