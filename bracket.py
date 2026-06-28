import streamlit as st

st.markdown("# 🗓️ Live Bracket")
st.markdown("---")

BRACKET_IMG = "https://a57.foxsports.com/statics.foxsports.com/www.foxsports.com/content/uploads/2026/06/0/0/image-20.png?ve=1&tl=1"
BRACKET_URL = "https://www.foxsports.com/stories/soccer/world-cup-live-bracket-knockout-games-32"

st.image(BRACKET_IMG, use_container_width=True)

st.markdown(
    f'<div style="text-align:center;margin-top:0.5rem;">'
    f'<a href="{BRACKET_URL}" target="_blank" style="color:#2563eb;font-size:0.9rem;">'
    f'View full bracket on Fox Sports ↗</a></div>',
    unsafe_allow_html=True,
)
