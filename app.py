import streamlit as st
from datetime import datetime, timezone
from styles import inject_css, hide_sidebar, flag
import db
from db import display_name

st.set_page_config(
    page_title="World Cup Survivor",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

if "user" not in st.session_state:
    st.session_state.user = None


def render_sidebar(user):
    with st.sidebar:
        st.markdown(f"### {display_name(user)}")
        badge = ('<span class="badge badge-red">Eliminated</span>' if user["is_eliminated"]
                 else '<span class="badge badge-green">Still alive ✓</span>')
        st.markdown(badge, unsafe_allow_html=True)
        st.markdown("---")
        if st.button("Log out", use_container_width=True):
            st.session_state.user = None
            st.rerun()


# ── Logged in ─────────────────────────────────────────────────────────────────
if st.session_state.user:
    user = db.get_user_by_id(st.session_state.user["id"]) or st.session_state.user
    st.session_state.user = user
    render_sidebar(user)

    st.markdown("# ⚽ World Cup Survivor")
    st.markdown("---")

    active_round = db.get_active_round()
    rounds_map = {r["id"]: r for r in db.get_all_rounds()}

    # ── Current round / pick interface ────────────────────────────────────────
    if active_round:
        now = datetime.now(timezone.utc)
        deadline = datetime.fromisoformat(active_round["deadline"].replace("Z", "+00:00"))
        time_left = deadline - now
        locked = time_left.total_seconds() <= 0 or active_round["status"] == "locked"

        existing_pick = db.get_user_pick_for_round(user["id"], active_round["id"])
        used_teams = db.get_used_teams(user["id"])
        matches = db.get_matches_for_round(active_round["id"])

        # Round header
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
            elim_round = rounds_map.get(user["eliminated_round_id"], {}).get("name", "a previous round")
            st.markdown(f"""
            <div class="wc-card red">
                <h3 style="color:#fca5a5;margin:0;">💀 Eliminated in {elim_round}</h3>
                <p style="margin:4px 0 0;">Your picked team was knocked out.</p>
            </div>
            """, unsafe_allow_html=True)

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
                st.caption("Select a team, then confirm. Grayed out = already used.")

            if "selected_team" not in st.session_state:
                st.session_state.selected_team = None

            for match in matches:
                c1, mid, c2 = st.columns([5, 1, 5])
                for team, col in [(match["team1"], c1), (match["team2"], c2)]:
                    used = team in prior_used
                    selected = st.session_state.selected_team == team
                    label = f"{'✓ ' if selected else ''}{flag(team)} {team}"
                    with col:
                        if st.button(label, key=f"pick_{match['id']}_{team}",
                                     disabled=used, use_container_width=True):
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

    # ── Pick history ──────────────────────────────────────────────────────────
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
                f'<div class="wc-card">'
                f'<span style="color:#94a3b8;font-size:0.8rem;">{rnd.get("name","")}</span><br>'
                f'<span style="font-size:1.05rem;">{icon} {flag(p["team_picked"])} <b>{p["team_picked"]}</b></span>'
                f' &nbsp;{badge}</div>',
                unsafe_allow_html=True,
            )

    # ── Used teams reminder ───────────────────────────────────────────────────
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
                st.text_input("Email", key="li_user", placeholder="you@example.com")
                st.text_input("Password", type="password", key="li_pass", placeholder="Your password")
                if st.form_submit_button("Log In", use_container_width=True):
                    u, p = st.session_state.li_user, st.session_state.li_pass
                    if u and p:
                        user = db.login_user(u, p)
                        if user:
                            st.session_state.user = user
                            st.rerun()
                        else:
                            st.error("Invalid email or password.")
                    else:
                        st.warning("Please fill in both fields.")

            st.markdown('<p style="text-align:center;margin-top:1rem;color:#64748b;font-size:0.9rem;">Don\'t have an account?</p>',
                        unsafe_allow_html=True)
            if st.button("Create an account →", use_container_width=True, key="go_signup"):
                st.session_state.auth_mode = "signup"
                st.rerun()

        else:
            with st.form("signup"):
                st.text_input("Email", key="su_user", placeholder="you@example.com")
                st.text_input("Password", type="password", key="su_pass", placeholder="At least 6 characters")
                st.text_input("Confirm password", type="password", key="su_conf", placeholder="Repeat password")
                if st.form_submit_button("Create Account", use_container_width=True):
                    u, p, c = st.session_state.su_user, st.session_state.su_pass, st.session_state.su_conf
                    if not (u and p and c):
                        st.warning("Please fill in all fields.")
                    elif "@" not in u:
                        st.error("Please enter a valid email address.")
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
                            st.error("An account with that email already exists.")

            st.markdown('<p style="text-align:center;margin-top:1rem;color:#64748b;font-size:0.9rem;">Already have an account?</p>',
                        unsafe_allow_html=True)
            if st.button("← Back to Log In", use_container_width=True, key="go_login"):
                st.session_state.auth_mode = "login"
                st.rerun()
