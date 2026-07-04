import streamlit as st

st.markdown("# 📋 Rules")
st.markdown("---")

st.markdown("""
<div class="wc-card">
  <h3 style="margin-top:0;margin-bottom:1.2rem;">How it works</h3>
  <p><strong>1. Pick one team per round.</strong><br>
  <span style="color:#94a3b8;">Each round, choose one team you think will win their match.</span></p>
  <p><strong>2. No repeats.</strong><br>
  <span style="color:#94a3b8;">Once you've picked a team, you can't pick them again in a later round.</span></p>
  <p><strong>3. Stay alive.</strong><br>
  <span style="color:#94a3b8;">If your picked team loses, you're eliminated. If they win, you advance.</span></p>
  <p><strong>4. Beat the first kickoff.</strong><br>
  <span style="color:#94a3b8;">All picks are due before the round's first match kicks off. Once that first game starts, the whole round is locked.</span></p>
  <p><strong>5. No pick = eliminated.</strong><br>
  <span style="color:#94a3b8;">If the round closes and you haven't made a pick, you're out — same as picking a loser.</span></p>
  <p style="margin-bottom:0;"><strong>6. Last one standing wins.</strong><br>
  <span style="color:#94a3b8;">The last player with a surviving pick at the end of the tournament wins a secret mystery prize. 🎁</span></p>
</div>
""", unsafe_allow_html=True)
