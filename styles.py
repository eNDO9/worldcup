import streamlit as st

TEAM_FLAGS = {
    "Germany": "🇩🇪", "Paraguay": "🇵🇾", "France": "🇫🇷", "Sweden": "🇸🇪",
    "South Africa": "🇿🇦", "Canada": "🇨🇦", "Netherlands": "🇳🇱", "Morocco": "🇲🇦",
    "Portugal": "🇵🇹", "Croatia": "🇭🇷", "Spain": "🇪🇸", "Austria": "🇦🇹",
    "United States": "🇺🇸", "Bosnia and Herzegovina": "🇧🇦", "Belgium": "🇧🇪",
    "Senegal": "🇸🇳", "Brazil": "🇧🇷", "Japan": "🇯🇵", "Ivory Coast": "🇨🇮",
    "Norway": "🇳🇴", "Mexico": "🇲🇽", "Ecuador": "🇪🇨", "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "DR Congo": "🇨🇩", "Argentina": "🇦🇷", "Cape Verde": "🇨🇻", "Australia": "🇦🇺",
    "Egypt": "🇪🇬", "Switzerland": "🇨🇭", "Algeria": "🇩🇿", "Colombia": "🇨🇴",
    "Ghana": "🇬🇭",
}

def flag(team: str) -> str:
    return TEAM_FLAGS.get(team, "🏳️")

def inject_css():
    st.markdown("""
    <style>
    .stApp { background-color: #0f172a; }
    #MainMenu, footer { visibility: hidden; }

    section[data-testid="stSidebar"] {
        background-color: #1e293b;
        border-right: 1px solid #2d3f55;
    }
    section[data-testid="stSidebar"] * { color: #f1f5f9 !important; }

    h1, h2, h3, h4 { color: #f1f5f9 !important; }
    p, label, span, div { color: #cbd5e1; }

    .stButton > button {
        background-color: #1e293b;
        color: #f1f5f9 !important;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 0.6rem 1rem;
        width: 100%;
        font-size: 0.95rem;
        transition: all 0.15s ease;
    }
    .stButton > button:hover:not(:disabled) {
        border-color: #f59e0b;
        color: #f59e0b !important;
        background-color: #1e293b;
    }
    .stButton > button[kind="primary"] {
        background-color: #b45309 !important;
        border-color: #f59e0b !important;
        color: #fff !important;
    }
    .stButton > button:disabled { opacity: 0.3; }

    .stTextInput > div > div > input,
    .stSelectbox > div > div,
    .stDateInput > div > div > input {
        background-color: #1e293b !important;
        color: #f1f5f9 !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
    }

    .stTabs [data-baseweb="tab-list"] { background: #1e293b; border-radius: 10px; }
    .stTabs [data-baseweb="tab"] { color: #94a3b8 !important; }
    .stTabs [aria-selected="true"] { color: #f59e0b !important; }

    [data-testid="stMetricValue"] { color: #f59e0b !important; font-size: 1.6rem !important; }
    [data-testid="stMetricLabel"] { color: #94a3b8 !important; }

    hr { border-color: #2d3f55 !important; }

    .wc-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1.1rem 1.4rem;
        margin-bottom: 0.6rem;
    }
    .wc-card.gold { border-color: #f59e0b; }
    .wc-card.red  { border-color: #ef4444; }
    .wc-card.green { border-color: #22c55e; }

    .badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }
    .badge-green { background:#14532d; color:#86efac; }
    .badge-red   { background:#7f1d1d; color:#fca5a5; }
    .badge-gold  { background:#78350f; color:#fde68a; }
    .badge-gray  { background:#1e293b; color:#94a3b8; border:1px solid #334155; }
    </style>
    """, unsafe_allow_html=True)
