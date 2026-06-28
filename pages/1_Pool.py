import streamlit as st
from styles import inject_css, flag
import db
from db import display_name

st.set_page_config(page_title="The Pool", page_icon="🏆", layout="wide")
inject_css()

if not st.session_state.get("user"):
    st.warning("Please log in first.")
    st.page_link("app.py", label="← Go to Login")
    st.stop()

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

st.markdown("# 🏆 The Pool")
st.markdown("Opponents' picks are revealed after each round closes.")
st.markdown("---")

all_rounds = db.get_all_rounds()
standings = db.get_standings()
active_round = db.get_active_round()

alive = [u for u in standings if not u["is_eliminated"]]
out   = [u for u in standings if u["is_eliminated"]]

# ── Quick scoreboard ──────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Players Alive", len(alive))
with col2:
    st.metric("Eliminated", len(out))
with col3:
    current_round_name = active_round["name"] if active_round else "—"
    st.metric("Current Round", current_round_name)

st.markdown("---")

# ── Rounds (only completed/locked — opponents' picks hidden for active round) ──
revealed_rounds = [r for r in all_rounds if r["status"] in ("completed", "locked")]
hidden_rounds   = [r for r in all_rounds if r["status"] == "active"]

if revealed_rounds:
    for rnd in reversed(revealed_rounds):
        st.markdown(f"### {rnd['name']}")
        picks_this_round = db.get_all_picks_for_round(rnd["id"])
        picks_by_user = {p["user_id"]: p for p in picks_this_round}

        for participant in standings:
            uid = participant["id"]
            pick = picks_by_user.get(uid)
            is_me = uid == user["id"]
            name = display_name(participant)
            border = "gold" if is_me else ""

            if pick:
                team = pick["team_picked"]
                result = db.pick_result(team, rnd["id"])
                icon  = "✅" if result == "won" else "❌" if result == "lost" else "⏳"
                badge_cls = "badge-green" if result == "won" else "badge-red" if result == "lost" else "badge-gray"
                badge_lbl = "Won" if result == "won" else "Lost" if result == "lost" else "Pending"
                me_tag = " &nbsp;<span style='color:#94a3b8;font-size:0.8rem;'>you</span>" if is_me else ""
                st.markdown(
                    f'<div class="wc-card {border}" style="padding:0.7rem 1.2rem;">'
                    f'<span style="color:#94a3b8;font-size:0.85rem;">{name}{me_tag}</span> &nbsp;'
                    f'{icon} {flag(team)} <b>{team}</b> &nbsp;'
                    f'<span class="badge {badge_cls}">{badge_lbl}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div class="wc-card" style="padding:0.7rem 1.2rem;opacity:0.4;">'
                    f'<span style="color:#94a3b8;font-size:0.85rem;">{name}</span> &nbsp;— no pick</div>',
                    unsafe_allow_html=True,
                )
        st.markdown("")

if hidden_rounds:
    for rnd in hidden_rounds:
        picks_count = len(db.get_all_picks_for_round(rnd["id"]))
        st.markdown(f"### {rnd['name']} *(active)*")
        st.markdown(
            f'<div class="wc-card" style="text-align:center;padding:1.2rem;">'
            f'<span style="font-size:1.5rem;">🔒</span><br>'
            f'<b style="color:#f1f5f9;">{picks_count} player{"s" if picks_count != 1 else ""} have locked in picks</b><br>'
            f'<span style="color:#64748b;font-size:0.85rem;">Picks revealed when the round closes</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

if not revealed_rounds and not hidden_rounds:
    st.info("No rounds have started yet.")

# ── Full standings ────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Standings")

if alive:
    st.markdown(f"**🟢 Still in ({len(alive)})**")
    for u in alive:
        is_me = u["id"] == user["id"]
        me_tag = " 👈 you" if is_me else ""
        st.markdown(f"- {display_name(u)}{me_tag}")

if out:
    st.markdown(f"**💀 Eliminated ({len(out)})**")
    for u in out:
        elim_rnd = u["rounds"].get(u["eliminated_round_id"], {}).get("name", "") if u["eliminated_round_id"] else ""
        st.markdown(f"- ~~{display_name(u)}~~ *(out in {elim_rnd})*")
