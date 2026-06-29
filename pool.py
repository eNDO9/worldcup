import streamlit as st
from datetime import datetime, timezone
from styles import flag
import db
from db import display_name

user = st.session_state.user
all_rounds   = db.get_all_rounds()
standings    = db.get_standings()
active_round = db.get_active_round()

alive = [u for u in standings if not u["is_eliminated"]]
out   = [u for u in standings if u["is_eliminated"]]

st.markdown("# 🏆 The Pool")
st.markdown("---")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Players Alive", len(alive))
with col2:
    st.metric("Eliminated", len(out))
with col3:
    st.metric("Current Round", active_round["name"] if active_round else "—")

st.markdown("---")

# ── Standings ─────────────────────────────────────────────────────────────────
st.markdown("### Standings")
if alive:
    st.markdown(f"**🟢 Still in ({len(alive)})**")
    for u in alive:
        me = " 👈 you" if u["id"] == user["id"] else ""
        st.markdown(f"- {display_name(u)}{me}")
if out:
    st.markdown(f"**💀 Eliminated ({len(out)})**")
    for u in out:
        rnd_name = u["rounds"].get(u["eliminated_round_id"], {}).get("name", "") if u["eliminated_round_id"] else ""
        st.markdown(f"- ~~{display_name(u)}~~ *(out in {rnd_name})*")
if not alive and not out:
    st.info("No players yet.")

st.markdown("---")

# ── Round picks ───────────────────────────────────────────────────────────────
st.markdown("Opponents' picks are revealed after each round closes.")

now = datetime.now(timezone.utc)

def _is_closed(r):
    if r["status"] in ("completed", "locked"):
        return True
    if r["status"] == "active" and r.get("deadline"):
        deadline = datetime.fromisoformat(r["deadline"].replace("Z", "+00:00"))
        return deadline <= now
    return False

revealed = [r for r in all_rounds if _is_closed(r)]
active   = [r for r in all_rounds if r["status"] == "active" and not _is_closed(r)]

if revealed:
    for rnd in reversed(revealed):
        st.markdown(f"### {rnd['name']}")
        picks_this_round = db.get_all_picks_for_round(rnd["id"])
        picks_by_user = {p["user_id"]: p for p in picks_this_round}

        for participant in standings:
            uid    = participant["id"]
            pick   = picks_by_user.get(uid)
            is_me  = uid == user["id"]
            name   = display_name(participant)
            border = "gold" if is_me else ""
            me_tag = " &nbsp;<span style='color:#94a3b8;font-size:0.8rem;'>you</span>" if is_me else ""

            if pick:
                team = pick["team_picked"]
                result    = db.pick_result(team, rnd["id"])
                icon      = "✅" if result == "won" else "❌" if result == "lost" else "⏳"
                badge_cls = "badge-green" if result == "won" else "badge-red" if result == "lost" else "badge-gray"
                badge_lbl = "Won" if result == "won" else "Lost" if result == "lost" else "Pending"
                st.markdown(
                    f'<div class="wc-card {border}" style="padding:0.7rem 1.2rem;">'
                    f'<span style="color:#94a3b8;font-size:0.85rem;">{name}{me_tag}</span> &nbsp;'
                    f'{icon} {flag(team)} <b>{team}</b> &nbsp;'
                    f'<span class="badge {badge_cls}">{badge_lbl}</span></div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div class="wc-card" style="padding:0.7rem 1.2rem;opacity:0.4;">'
                    f'<span style="color:#94a3b8;font-size:0.85rem;">{name}{me_tag}</span> &nbsp;— no pick</div>',
                    unsafe_allow_html=True,
                )
        st.markdown("")

for rnd in active:
    picks_count = len(db.get_all_picks_for_round(rnd["id"]))
    st.markdown(f"### {rnd['name']} *(active)*")
    st.markdown(
        f'<div class="wc-card" style="text-align:center;padding:1.4rem;">'
        f'<span style="font-size:1.5rem;">🔒</span><br>'
        f'<b style="color:#f1f5f9;">{picks_count} player{"s" if picks_count != 1 else ""} have locked in picks</b><br>'
        f'<span style="color:#64748b;font-size:0.85rem;">Picks revealed when the round closes</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

if not revealed and not active:
    st.info("No rounds have started yet.")
