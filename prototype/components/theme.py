"""
prototype/components/theme.py — Stitch "Nordic Climate Precision" Design System for Streamlit
Applies the Stitch-generated website UI styling (Plus Jakarta Sans + Inter, Emerald Forest #006948,
Polar Night #0b1c30, Glacial Blue #006194, modern SaaS sidebar navigation, top header bar, and
elevated KPI cards) while preserving 100% of existing views, 3D models, and geomaps.
"""
import streamlit as st


def apply_custom_theme() -> None:
    """Inject the Stitch 'Nordic Climate Precision' web design system into Streamlit."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@500;600;700;800&family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap');

        :root {
            --stitch-bg: #f8f9ff;
            --stitch-surface: #ffffff;
            --stitch-surface-low: #eff4ff;
            --stitch-surface-container: #e5eeff;
            --stitch-primary: #006948;
            --stitch-primary-container: #00855d;
            --stitch-primary-fixed: #85f8c4;
            --stitch-on-primary-fixed: #002114;
            --stitch-tertiary: #006194;
            --stitch-on-surface: #0b1c30;
            --stitch-secondary: #565e74;
            --stitch-border: #dce4ee;
            --stitch-amber: #ea580c;
        }

        /* Global App Canvas & Typography */
        html, body, .stApp {
            background-color: var(--stitch-bg) !important;
            color: var(--stitch-on-surface) !important;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        }

        h1, h2, h3, h4, .stitch-headline {
            font-family: 'Plus Jakarta Sans', 'Inter', sans-serif !important;
            color: var(--stitch-on-surface) !important;
            letter-spacing: -0.02em !important;
        }

        h1 {
            font-size: 1.85rem !important;
            font-weight: 800 !important;
            line-height: 1.2 !important;
        }

        /* Tighten top container padding to match a modern web app */
        .block-container {
            padding-top: 1.25rem !important;
            padding-bottom: 2.5rem !important;
            max-width: 1560px !important;
        }

        /* Hide default Streamlit chrome header decoration */
        header[data-testid="stHeader"] {
            background: rgba(248, 249, 255, 0.85) !important;
            backdrop-filter: blur(10px) !important;
            border-bottom: 1px solid rgba(220, 228, 238, 0.5) !important;
        }

        /* ── Modern Website Sidebar (Stitch SideNavBar) ───────────────────── */
        section[data-testid="stSidebar"] {
            background-color: #ffffff !important;
            border-right: 1px solid var(--stitch-border) !important;
            box-shadow: 2px 0 12px rgba(11, 28, 48, 0.02) !important;
        }
        section[data-testid="stSidebar"] .block-container {
            padding-top: 1rem !important;
        }

        /* Transform st.sidebar.radio into sleek SaaS Web Navigation Pills */
        section[data-testid="stSidebar"] div[role="radiogroup"] {
            gap: 3px !important;
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] > label {
            background: transparent !important;
            border-radius: 8px !important;
            padding: 8px 12px !important;
            margin: 0 !important;
            border: 1px solid transparent !important;
            transition: all 0.15s ease !important;
            cursor: pointer !important;
            width: 100% !important;
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
            background: var(--stitch-surface-low) !important;
            border-color: rgba(0, 105, 72, 0.15) !important;
        }
        /* Hide the ugly default radio circle dot in sidebar nav */
        section[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child {
            display: none !important;
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] > label p {
            font-size: 0.84rem !important;
            font-weight: 500 !important;
            color: #3d4a42 !important;
            margin: 0 !important;
        }
        /* Active selected nav item in sidebar */
        section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {
            background: var(--stitch-surface-low) !important;
            border-left: 3px solid var(--stitch-primary) !important;
            border-radius: 4px 8px 8px 4px !important;
            box-shadow: 0 1px 2px rgba(11, 28, 48, 0.04) !important;
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) p {
            color: var(--stitch-primary) !important;
            font-weight: 700 !important;
        }

        /* ── KPI Metric Cards (Stitch KPI Decision Metric Tiles) ─────────── */
        div[data-testid="stMetric"] {
            background: #ffffff !important;
            border: 1px solid var(--stitch-border) !important;
            border-top: 3px solid var(--stitch-primary) !important;
            border-radius: 10px !important;
            padding: 16px 18px !important;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04), 0 1px 2px rgba(15, 23, 42, 0.02) !important;
            transition: transform 0.15s ease, box-shadow 0.15s ease !important;
        }
        div[data-testid="stMetric"]:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 6px 16px rgba(15, 23, 42, 0.06) !important;
        }
        div[data-testid="stMetricLabel"] p {
            font-family: 'Inter', sans-serif !important;
            font-size: 0.72rem !important;
            font-weight: 700 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.06em !important;
            color: var(--stitch-secondary) !important;
        }
        div[data-testid="stMetricValue"] {
            font-family: 'Plus Jakarta Sans', sans-serif !important;
            font-size: 1.75rem !important;
            font-weight: 800 !important;
            color: var(--stitch-on-surface) !important;
            font-variant-numeric: tabular-nums !important;
        }
        div[data-testid="stMetricDelta"] {
            font-family: 'Inter', sans-serif !important;
            font-size: 0.75rem !important;
            font-weight: 600 !important;
        }

        /* ── Modern SaaS Tabs ─────────────────────────────────────────────── */
        div[data-baseweb="tab-list"] {
            background: #ffffff !important;
            border: 1px solid var(--stitch-border) !important;
            border-radius: 10px !important;
            padding: 4px !important;
            gap: 4px !important;
        }
        button[data-baseweb="tab"] {
            border-radius: 7px !important;
            padding: 8px 16px !important;
            font-family: 'Inter', sans-serif !important;
            font-weight: 600 !important;
            font-size: 0.84rem !important;
            color: var(--stitch-secondary) !important;
            border: none !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            background: var(--stitch-primary) !important;
            color: #ffffff !important;
            box-shadow: 0 1px 3px rgba(0, 105, 72, 0.25) !important;
        }
        div[data-baseweb="tab-highlight"] {
            display: none !important;
        }

        /* ── Buttons (Stitch Emerald Forest Primary & Slate Secondary) ───── */
        .stButton > button, .stDownloadButton > button {
            font-family: 'Inter', sans-serif !important;
            font-weight: 600 !important;
            font-size: 0.84rem !important;
            border-radius: 8px !important;
            border: 1px solid #cbd5e1 !important;
            background: #ffffff !important;
            color: var(--stitch-on-surface) !important;
            transition: all 0.15s ease !important;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03) !important;
        }
        .stButton > button:hover, .stDownloadButton > button:hover {
            background: var(--stitch-surface-low) !important;
            border-color: var(--stitch-primary) !important;
            color: var(--stitch-primary) !important;
        }
        .stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {
            background: var(--stitch-primary) !important;
            color: #ffffff !important;
            border-color: var(--stitch-primary) !important;
        }
        .stButton > button[kind="primary"]:hover, .stDownloadButton > button[kind="primary"]:hover {
            background: var(--stitch-primary-container) !important;
            color: #ffffff !important;
        }

        /* ── Expanders, DataFrames & Alerts ───────────────────────────────── */
        details[data-testid="stExpander"] {
            background: #ffffff !important;
            border: 1px solid var(--stitch-border) !important;
            border-radius: 10px !important;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.02) !important;
        }
        div[data-testid="stDataFrame"] {
            border: 1px solid var(--stitch-border) !important;
            border-radius: 10px !important;
            overflow: hidden !important;
            background: #ffffff !important;
        }

        /* ── Stitch Top Navigation Bar ────────────────────────────────────── */
        .stitch-topbar {
            background: #ffffff;
            border: 1px solid var(--stitch-border);
            border-radius: 12px;
            padding: 10px 18px;
            margin-bottom: 1.25rem;
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.03);
        }
        .stitch-topbar-left {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .stitch-brand-icon {
            width: 34px;
            height: 34px;
            border-radius: 8px;
            background: #00855d;
            color: #ffffff;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 16px;
            box-shadow: 0 1px 2px rgba(0, 105, 72, 0.25);
        }
        .stitch-pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 12px;
            border-radius: 9999px;
            background: #f8f9ff;
            border: 1px solid var(--stitch-border);
            font-size: 0.74rem;
            font-weight: 600;
            color: var(--stitch-on-surface);
        }
        .stitch-pulse-dot {
            width: 8px;
            height: 8px;
            border-radius: 9999px;
            background: #006948;
            box-shadow: 0 0 0 3px rgba(0, 105, 72, 0.18);
        }
        .stitch-badge-green {
            background: #85f8c4;
            color: #002114;
            padding: 3px 10px;
            border-radius: 6px;
            font-size: 0.72rem;
            font-weight: 700;
        }

        /* Legacy helper classes preserved for existing views */
        .pro-card {
            background: #ffffff;
            border: 1px solid var(--stitch-border);
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.03);
            margin-bottom: 1.2rem;
        }
        .pro-card-header {
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--stitch-on-surface);
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .metric-tile {
            background: #ffffff;
            border: 1px solid var(--stitch-border);
            border-top: 3px solid var(--stitch-primary);
            border-radius: 8px;
            padding: 14px 18px;
            text-align: left;
        }
        .metric-tile-label {
            font-size: 0.75rem;
            color: var(--stitch-secondary);
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .metric-tile-val {
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-size: 1.5rem;
            font-weight: 800;
            color: var(--stitch-on-surface);
            margin: 4px 0;
        }
        .metric-tile-delta { font-size: 0.80rem; font-weight: 600; }
        .delta-good { color: #006948; }
        .delta-warn { color: #d97706; }
        .delta-bad  { color: #dc2626; }
        .pill-badge {
            display: inline-block;
            padding: 2px 10px;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        .badge-approved { background: #85f8c4; color: #002114; }
        .badge-pending  { background: #fef3c7; color: #92400e; }
        .badge-flagged  { background: #fee2e2; color: #991b1b; }
        .badge-flag     { background: #dae2fd; color: #131b2e; }
        .badge-scope    { background: #eff4ff; color: #0b1c30; }
        .evidence-drawer-box {
            background: #0b1c30;
            color: #eaf1ff;
            font-family: 'JetBrains Mono', monospace, Consolas;
            font-size: 0.80rem;
            padding: 16px;
            border-radius: 8px;
            line-height: 1.5;
            white-space: pre-wrap;
            border-left: 4px solid #68dba9;
            margin-top: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_synthetic_banner() -> None:
    """Render the Stitch 'Nordic Climate Precision' Top Navigation Header Bar."""
    st.markdown(
        """<div class="stitch-topbar">
<div class="stitch-topbar-left">
<div class="stitch-brand-icon">🌱</div>
<div>
<div style="font-family:'Plus Jakarta Sans',sans-serif; font-weight:800; font-size:0.95rem; color:#0b1c30; line-height:1.1;">Apetit Climate &amp; Nature Navigator</div>
<div style="font-size:0.72rem; color:#565e74;">Nordic Corporate ESG, 3D Digital Twin &amp; Value-Chain Decision Platform</div>
</div>
</div>
<div style="display:flex; flex-wrap:wrap; align-items:center; gap:8px;">
<span class="stitch-pill"><span class="stitch-pulse-dot"></span><span>14,213 Parcels · 680 Farms Monitored</span></span>
<span class="stitch-pill">🛡️ Synthetic Twin Governance: <strong style="color:#006948;">Active (Calibrated Demo)</strong></span>
<span class="stitch-badge-green">✓ CSRD / SBTi / SBTN Audit Ready</span>
</div>
</div>""",
        unsafe_allow_html=True,
    )
