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

    /* Hide all Streamlit chrome */
    #MainMenu, footer { visibility: hidden; }
    header[data-testid="stHeader"],
    .stAppHeader,
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"] { display: none !important; }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #1e293b;
        border-right: 1px solid #2d3f55;
    }
    section[data-testid="stSidebar"] * { color: #f1f5f9 !important; }
    /* Sidebar collapse/expand toggle button */
    [data-testid="stSidebarCollapseButton"] button {
        color: #94a3b8 !important;
    }
    [data-testid="stSidebarCollapseButton"] svg {
        fill: #94a3b8 !important;
        stroke: #94a3b8 !important;
    }
    /* Re-expand tab that appears when sidebar is collapsed */
    [data-testid="collapsedControl"] {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        border-left: none !important;
        border-radius: 0 0.5rem 0.5rem 0 !important;
        padding: 0.6rem 0.5rem !important;
        top: 5rem !important;
        position: fixed !important;
        z-index: 999999 !important;
    }
    [data-testid="collapsedControl"] button {
        color: #f1f5f9 !important;
    }
    [data-testid="collapsedControl"] svg {
        fill: #f1f5f9 !important;
        stroke: #f1f5f9 !important;
    }

    h1, h2, h3, h4 { color: #f1f5f9 !important; }
    p, label, span, div { color: #cbd5e1; }

    /* Regular buttons */
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
        background-color: #2563eb !important;
        border-color: #2563eb !important;
        color: #fff !important;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #1d4ed8 !important;
        border-color: #1d4ed8 !important;
    }
    .stButton > button:disabled { opacity: 0.3; }

    /* Form submit buttons — blue */
    .stFormSubmitButton > button,
    [data-testid="stFormSubmitButton"] > button {
        background-color: #2563eb !important;
        border: none !important;
        border-radius: 10px !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        padding: 0.75rem 1rem !important;
        width: 100% !important;
        transition: background-color 0.15s ease !important;
    }
    .stFormSubmitButton > button:hover,
    [data-testid="stFormSubmitButton"] > button:hover {
        background-color: #1d4ed8 !important;
    }

    /* BaseWeb input container — this is what Streamlit actually renders */
    [data-baseweb="input"] {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        overflow: hidden !important;
    }
    /* Every child div inside the container (incl. the hidden button's wrapper) */
    [data-baseweb="input"] > div {
        background-color: #1e293b !important;
    }
    [data-baseweb="input"] input {
        background-color: #1e293b !important;
        color: #f1f5f9 !important;
        caret-color: #f1f5f9 !important;
    }
    [data-baseweb="input"] input::placeholder { color: #475569 !important; opacity: 1 !important; }

    /* Hide the password reveal toggle */
    [data-testid="stTextInput"] button { display: none !important; }

    /* Selectbox / date inputs */
    .stSelectbox > div > div,
    .stDateInput > div > div > input {
        background-color: #1e293b !important;
        color: #f1f5f9 !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
    }

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
    .wc-card.gold  { border-color: #f59e0b; }
    .wc-card.red   { border-color: #ef4444; }
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


def hide_sidebar():
    st.markdown("""
    <style>
    section[data-testid="stSidebar"],
    [data-testid="collapsedControl"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)
