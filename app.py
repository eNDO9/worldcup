import streamlit as st
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
    st.Page("home.py",    title="Home",     icon="🏠", default=True),
    st.Page("pool.py",    title="The Pool", icon="🏆"),
    st.Page("bracket.py", title="Bracket",  icon="🗓️"),
]
if user.get("email", "").lower() == ADMIN_EMAIL.lower():
    pages.append(st.Page("admin.py", title="Admin", icon="⚙️"))

pg = st.navigation(pages)
pg.run()
