import streamlit as st
from datetime import datetime, timezone
from styles import inject_css, hide_sidebar, flag
import db

st.set_page_config(
    page_title="World Cup Survivor",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
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
    hide_sidebar()

    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "login"

    _, col_m, _ = st.columns([1, 1.4, 1])
    with col_m:
        st.markdown("""
        <div style="text-align:center;padding:3rem 0 2rem;">
            <div style="font-size:3.5rem;line-height:1;">⚽</div>
            <h1 style="margin:0.6rem 0 0.3rem;font-size:2.2rem;font-weight:700;color:#f1f5f9;">
                World Cup Survivor
            </h1>
            <p style="color:#64748b;font-size:1rem;margin:0;">
                Pick one team per round &nbsp;·&nbsp; Never reuse &nbsp;·&nbsp; Last one standing wins
            </p>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.auth_mode == "login":
            with st.form("login"):
                st.text_input("Username", key="li_user", placeholder="Your username")
                st.text_input("Password", type="password", key="li_pass", placeholder="Your password")
                if st.form_submit_button("Log In", use_container_width=True):
                    u, p = st.session_state.li_user, st.session_state.li_pass
                    if u and p:
                        user = db.login_user(u, p)
                        if user:
                            st.session_state.user = user
                            st.rerun()
                        else:
                            st.error("Invalid username or password.")
                    else:
                        st.warning("Please fill in both fields.")

            st.markdown(
                '<p style="text-align:center;margin-top:1rem;color:#64748b;font-size:0.9rem;">'
                "Don't have an account?</p>",
                unsafe_allow_html=True,
            )
            if st.button("Create an account →", use_container_width=True, key="go_signup"):
                st.session_state.auth_mode = "signup"
                st.rerun()

        else:
            with st.form("signup"):
                st.text_input("Username", key="su_user", placeholder="Choose a username")
                st.text_input("Password", type="password", key="su_pass", placeholder="At least 6 characters")
                st.text_input("Confirm password", type="password", key="su_conf", placeholder="Repeat password")
                if st.form_submit_button("Create Account", use_container_width=True):
                    u = st.session_state.su_user
                    p = st.session_state.su_pass
                    c = st.session_state.su_conf
                    if not (u and p and c):
                        st.warning("Please fill in all fields.")
                    elif p != c:
                        st.error("Passwords don't match.")
                    elif len(p) < 6:
                        st.error("Password must be at least 6 characters.")
                    else:
                        user = db.create_user(u, p)
                        if user:
                            st.session_state.user = user
                            st.rerun()
                        else:
                            st.error("Username already taken — try another.")

            st.markdown(
                '<p style="text-align:center;margin-top:1rem;color:#64748b;font-size:0.9rem;">'
                "Already have an account?</p>",
                unsafe_allow_html=True,
            )
            if st.button("← Back to Log In", use_container_width=True, key="go_login"):
                st.session_state.auth_mode = "login"
                st.rerun()
