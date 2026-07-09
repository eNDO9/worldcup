import streamlit as st
from datetime import datetime, timezone, timedelta
from styles import inject_css
import auth_session
import db
from db import display_name

ADMIN_EMAIL = "nathanwdoctor@gmail.com"

st.set_page_config(
    page_title="World Cup Survivor",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

if "user" not in st.session_state:
    st.session_state.user = None

# ── Restore login from the session cookie on a fresh browser session ──────────
if st.session_state.user is None and not st.session_state.get("logged_out"):
    uid = auth_session.user_id_from_token(auth_session.read_cookie())
    if uid:
        st.session_state.user = db.get_user_by_id(uid)

# ── Logged out: show login ─────────────────────────────────────────────────────
if not st.session_state.user:
    # Inlined (not imported from styles) so a half-reloaded styles module on
    # Streamlit Cloud can never break the login page with an ImportError.
    st.markdown("""
    <style>
    section[data-testid="stSidebar"],
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)
    if st.session_state.get("logged_out"):
        # Keep clearing on every rerun: st.context still reports the old
        # cookie until the next full page load.
        auth_session.clear_cookie()
    import login as _login
    _login.render()
    st.stop()

# ── Auto-sync results from the API on load (cached 2 min across sessions) ─────
@st.cache_data(ttl=120, show_spinner=False)
def _auto_sync_results(round_id: int, past_deadline: bool) -> int:
    try:
        import results_sync
        applied = results_sync.auto_apply_results(round_id)
        # Once picks lock, having no pick is an instant elimination — same as
        # a loss (rule 5). past_deadline is part of the cache key, so the
        # sweep runs on the first load after the deadline, not up to 2 min
        # later.
        if past_deadline:
            db.eliminate_no_picks(round_id)
        return applied
    except Exception:
        return 0

_active_for_sync = db.get_active_round()
if _active_for_sync:
    _sync_now = datetime.now(timezone.utc)
    _sync_ddl = datetime.fromisoformat(_active_for_sync["deadline"].replace("Z", "+00:00"))
    _applied = _auto_sync_results(_active_for_sync["id"], _sync_now >= _sync_ddl)
    if _applied:
        st.toast(f"⚽ {_applied} new result{'s' if _applied != 1 else ''} synced")

# ── Logged in ─────────────────────────────────────────────────────────────────
user = db.get_user_by_id(st.session_state.user["id"]) or st.session_state.user
st.session_state.user = user
st.session_state.logged_out = False

# Persist the login across page loads (30-day signed cookie).
if not st.session_state.get("session_cookie_set"):
    auth_session.write_cookie(user["id"])
    st.session_state.session_cookie_set = True

nav_items = [
    (st.Page("home.py",    title="Make a Pick", icon="✅", default=True), "✅ Pick"),
    (st.Page("pool.py",    title="The Pool",    icon="🏆"), "🏆 Pool"),
    (st.Page("bracket.py", title="Bracket",     icon="🗓️"), "🗓️ Bracket"),
    (st.Page("rules.py",   title="Rules",       icon="📋"), "📋 Rules"),
]
if user.get("email", "").lower() == ADMIN_EMAIL.lower():
    nav_items.append((st.Page("admin.py", title="Admin", icon="⚙️"), "⚙️ Admin"))

# Nav lives in the sidebar on desktop; on phones (where the sidebar is hidden)
# the top tab bar below is the navigation instead.
pg = st.navigation([p for p, _ in nav_items])

# ── Sidebar: account (desktop) ────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"### {display_name(user)}")
    badge = ('<span class="badge badge-red">Eliminated</span>' if user["is_eliminated"]
             else '<span class="badge badge-green">Still alive ✓</span>')
    st.markdown(badge, unsafe_allow_html=True)
    st.markdown("---")
    if st.button("Log out", use_container_width=True, key="logout_sidebar"):
        st.session_state.user = None
        st.session_state.logged_out = True
        st.session_state.session_cookie_set = False
        st.rerun()

# ── Top bar: brand + account menu (mobile only, via CSS) ─────────────────────
with st.container(key="topbar"):
    brand_col, account_col = st.columns([3, 1], vertical_alignment="center")
    with brand_col:
        st.markdown('<div class="brand">⚽ World Cup Survivor</div>', unsafe_allow_html=True)
    with account_col:
        with st.popover(f"👤 {display_name(user)}", use_container_width=True):
            st.markdown(badge, unsafe_allow_html=True)
            if st.button("Log out", use_container_width=True, key="logout_popover"):
                st.session_state.user = None
                st.session_state.logged_out = True
                st.session_state.session_cookie_set = False
                st.rerun()

# ── Top nav tabs (mobile only, via CSS) ───────────────────────────────────────
with st.container(key="topnav"):
    cols = st.columns(len(nav_items), gap="small")
    for col, (page, label) in zip(cols, nav_items):
        with col:
            if st.button(label, key=f"nav_{page.url_path or 'home'}",
                         type="primary" if page.url_path == pg.url_path else "secondary",
                         use_container_width=True):
                st.switch_page(page)

# ── No-pick warning banner (all pages) ────────────────────────────────────────
active = db.get_active_round()
if active and not user["is_eliminated"] and active["status"] != "locked":
    now = datetime.now(timezone.utc)
    deadline = datetime.fromisoformat(active["deadline"].replace("Z", "+00:00"))
    if now < deadline and not db.get_user_pick_for_round(user["id"], active["id"]):
        left = deadline - now
        if left.total_seconds() >= 86400:
            countdown = f"{int(left.total_seconds() // 86400)}d {int((left.total_seconds() % 86400) // 3600)}h"
        else:
            countdown = f"{int(left.total_seconds() // 3600)}h {int((left.total_seconds() % 3600) // 60)}m"
        abs_et = (deadline - timedelta(hours=4)).strftime("%b %-d · %-I:%M %p ET")
        st.markdown(
            f'<div class="warn-banner">'
            f'<b>⚠️ No pick yet for the {active["name"]}</b>'
            f'<span> — all picks lock at the round\'s first kickoff, '
            f'in {countdown} ({abs_et}). Head to ✅ Pick.</span></div>',
            unsafe_allow_html=True,
        )

pg.run()
