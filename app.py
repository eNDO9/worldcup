import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime, timezone, timedelta
from styles import inject_css, hide_sidebar
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

# ── Logged out: show login, no sidebar ────────────────────────────────────────
if not st.session_state.user:
    hide_sidebar()
    import login as _login
    _login.render()
    st.stop()

# ── Force sidebar open on first load of each browser session ──────────────────
if "sidebar_initialized" not in st.session_state:
    st.session_state.sidebar_initialized = True
    components.html("""
        <script>
            try {
                var p = window.parent;
                Object.keys(p.localStorage).forEach(function(k) {
                    if (k.toLowerCase().indexOf('sidebar') !== -1) {
                        p.localStorage.removeItem(k);
                    }
                });
            } catch(e) {}
        </script>
    """, height=0)

# ── Auto-sync results from the API on load (cached 2 min across sessions) ─────
@st.cache_data(ttl=120, show_spinner=False)
def _auto_sync_results(round_id: int) -> int:
    try:
        import results_sync
        return results_sync.auto_apply_results(round_id)
    except Exception:
        return 0

_active_for_sync = db.get_active_round()
if _active_for_sync:
    _applied = _auto_sync_results(_active_for_sync["id"])
    if _applied:
        st.toast(f"⚽ {_applied} new result{'s' if _applied != 1 else ''} synced")

# ── Logged in ─────────────────────────────────────────────────────────────────
user = db.get_user_by_id(st.session_state.user["id"]) or st.session_state.user
st.session_state.user = user

with st.sidebar:
    st.markdown(f"### {display_name(user)}")
    badge = ('<span class="badge badge-red">Eliminated</span>' if user["is_eliminated"]
             else '<span class="badge badge-green">Still alive ✓</span>')
    st.markdown(badge, unsafe_allow_html=True)
    st.markdown("---")
    if st.button("Log out", use_container_width=True):
        st.session_state.user = None
        st.rerun()

pages = [
    st.Page("home.py",    title="Make a Pick", icon="✅", default=True),
    st.Page("pool.py",    title="The Pool", icon="🏆"),
    st.Page("bracket.py", title="Bracket", icon="🗓️"),
    st.Page("rules.py",   title="Rules",    icon="📋"),
]
if user.get("email", "").lower() == ADMIN_EMAIL.lower():
    pages.append(st.Page("admin.py", title="Admin", icon="⚙️"))

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
            f'<div style="background:#7f1d1d;border:1px solid #ef4444;border-radius:10px;'
            f'padding:0.7rem 1.2rem;margin-bottom:1rem;">'
            f'<b style="color:#fecaca;">⚠️ No pick yet for the {active["name"]}</b>'
            f'<span style="color:#fca5a5;"> — all picks lock at the round\'s first kickoff, '
            f'in {countdown} ({abs_et}). Head to ✅ Make a Pick.</span></div>',
            unsafe_allow_html=True,
        )

pg = st.navigation(pages)
pg.run()
