import streamlit as st

st.markdown("# 🗓️ Bracket")
st.markdown("---")

BRACKET_IMG = "https://globelynews.com/wp-content/uploads/2026/06/2026-fifa-world-cup-bracket-6-29-26.jpg"

st.markdown(
    f'<img src="{BRACKET_IMG}" style="width:100%;border-radius:8px;" />'
    f'<div style="text-align:center;margin-top:0.5rem;">'
    f'<a href="{BRACKET_IMG}" target="_blank" style="color:#2563eb;font-size:0.9rem;">'
    f'Open full image ↗</a></div>',
    unsafe_allow_html=True,
)
