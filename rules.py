import streamlit as st

st.markdown("# 📋 Rules")
st.markdown("---")

st.markdown("""
<div class="wc-card">
<h3 style="margin-top:0;">How it works</h3>

**1. Pick one team per round**
Each round, choose one team you think will win their match.

**2. No repeats**
Once you've picked a team, you can't pick them again in a later round.

**3. Stay alive**
If your picked team loses, you're eliminated. If they win, you advance to the next round.

**4. Deadline**
Picks must be submitted before the round deadline. Once a match kicks off, those teams are no longer available.

**5. Last one standing wins**
The last player (or players) with a surviving pick at the end of the tournament wins a secret mystery prize. 🎁
</div>
""", unsafe_allow_html=True)
