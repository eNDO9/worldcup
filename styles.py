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

    /* Hide all Streamlit chrome (sidebar nav on desktop, top tabs on mobile) */
    #MainMenu, footer { visibility: hidden; }
    header[data-testid="stHeader"],
    .stAppHeader,
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"] { display: none !important; }

    /* ── Sidebar (desktop nav) ── */
    section[data-testid="stSidebar"] {
        background-color: #1e293b;
        border-right: 1px solid #2d3f55;
    }
    section[data-testid="stSidebar"] * { color: #f1f5f9 !important; }
    [data-testid="stSidebarCollapseButton"] button { color: #94a3b8 !important; }
    [data-testid="stSidebarCollapseButton"] svg {
        fill: #94a3b8 !important;
        stroke: #94a3b8 !important;
    }
    /* Re-expand control when the sidebar is collapsed: it normally lives in
       the (hidden) header, so pin it as a visible floating tab instead. */
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"] {
        display: block !important;
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        border-left: none !important;
        border-radius: 0 0.5rem 0.5rem 0 !important;
        padding: 0.6rem 0.5rem !important;
        top: 5rem !important;
        left: 0 !important;
        position: fixed !important;
        z-index: 999999 !important;
    }
    [data-testid="stSidebarCollapsedControl"] button,
    [data-testid="collapsedControl"] button { color: #f1f5f9 !important; }
    [data-testid="stSidebarCollapsedControl"] svg,
    [data-testid="collapsedControl"] svg {
        fill: #f1f5f9 !important;
        stroke: #f1f5f9 !important;
    }

    /* Top bar + tabs are the MOBILE nav — hidden on desktop */
    @media (min-width: 641px) {
        .st-key-topbar, .st-key-topnav { display: none !important; }
    }

    .block-container {
        padding: 1.2rem 2.5rem 4rem;
        max-width: 1150px;
    }

    /* Collapse the invisible containers of height-0 script iframes so they
       don't add phantom vertical gaps (scripts still execute). */
    .stElementContainer:has(iframe[height="0"]) { display: none !important; }

    h1, h2, h3, h4 { color: #f1f5f9 !important; }
    p, label, span, div { color: #cbd5e1; }
    .block-container h1 { padding: 0.5rem 0 0.6rem !important; }
    .block-container hr { margin: 0.4rem 0 1.1rem !important; }

    /* ── Top bar: brand + account popover ── */
    .st-key-topbar .brand {
        font-size: 1.15rem;
        font-weight: 700;
        color: #f1f5f9 !important;
        white-space: nowrap;
    }
    .st-key-topbar button {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
        color: #f1f5f9 !important;
        min-height: 0 !important;
        padding: 0.35rem 0.6rem !important;
    }
    .st-key-topbar button p {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        font-size: 0.9rem;
    }
    [data-testid="stPopoverBody"] {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
    }

    /* ── Top nav tabs ── */
    .st-key-topnav { margin-bottom: 0.4rem; }
    .st-key-topnav .stButton > button {
        padding: 0.45rem 0.2rem;
        font-size: 0.9rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    /* ── No-pick warning banner ── */
    .warn-banner {
        background: #7f1d1d;
        border: 1px solid #ef4444;
        border-radius: 10px;
        padding: 0.7rem 1.2rem;
        margin-bottom: 1rem;
    }
    .warn-banner b { color: #fecaca; }
    .warn-banner span { color: #fca5a5; }

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

    /* Already-used team — red, non-interactive (can't be picked again) */
    .team-used {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.45rem;
        width: 100%;
        padding: 0.6rem 1rem;
        border-radius: 10px;
        border: 1px solid #7f1d1d;
        background-color: #2a1414;
        font-size: 0.95rem;
        cursor: not-allowed;
        box-sizing: border-box;
    }
    .team-used .team-used-name {
        color: #f87171 !important;
        text-decoration: line-through;
        font-weight: 600;
    }
    .team-used .used-tag {
        color: #fca5a5 !important;
        font-size: 0.66rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        background: #7f1d1d;
        padding: 1px 7px;
        border-radius: 999px;
    }

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

    /* ── Mobile ── */
    @media (max-width: 640px) {
        /* Sidebar is unusable on phones — the top tab bar is the nav there */
        section[data-testid="stSidebar"],
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="collapsedControl"] { display: none !important; }

        .block-container { padding: 0.7rem 0.8rem 3rem; }
        h1 { font-size: 1.5rem !important; }

        /* Rows that must stay side-by-side instead of stacking; everything
           else (login form, admin) keeps Streamlit's default stacking. */
        .st-key-topbar [data-testid="stHorizontalBlock"],
        .st-key-topnav [data-testid="stHorizontalBlock"],
        .st-key-round_metrics [data-testid="stHorizontalBlock"],
        .st-key-pool_metrics [data-testid="stHorizontalBlock"],
        .st-key-pick_grid [data-testid="stHorizontalBlock"] {
            flex-wrap: nowrap !important;
            gap: 0.4rem !important;
        }
        .st-key-topbar [data-testid="stColumn"],
        .st-key-topnav [data-testid="stColumn"],
        .st-key-round_metrics [data-testid="stColumn"],
        .st-key-pool_metrics [data-testid="stColumn"],
        .st-key-pick_grid [data-testid="stColumn"] {
            min-width: 0 !important;
        }

        .st-key-topbar .brand { font-size: 0.95rem; }
        .st-key-topnav .stButton > button {
            font-size: 0.74rem;
            padding: 0.45rem 0.1rem;
            border-radius: 8px;
        }

        .stButton > button {
            font-size: 0.78rem;
            padding: 0.5rem 0.4rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .team-used { font-size: 0.78rem; padding: 0.5rem 0.4rem; gap: 0.25rem; }
        .team-used .used-tag { display: none; }
        [data-testid="stMetricValue"] { font-size: 1.1rem !important; }
        [data-testid="stMetricValue"] > div {
            overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
        }
        [data-testid="stMetricLabel"] { font-size: 0.72rem !important; }
        .wc-card { padding: 0.8rem 0.9rem; }
        .warn-banner { padding: 0.55rem 0.8rem; font-size: 0.85rem; }
    }
    </style>
    """, unsafe_allow_html=True)
