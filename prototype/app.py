"""
Apetit Climate & Nature Navigator — Main Streamlit Application
Enterprise decision-making platform connecting emissions, crop risk, freshwater nature, and MACC pathways.
"""
from __future__ import annotations

import sys
from pathlib import Path
import streamlit as st

# ── Ensure tools & modules are importable ────────────────────────────────────
CURRENT_DIR = Path(__file__).resolve().parent
ROOT = CURRENT_DIR.parent / "APETIT_CLIMATE_NATURE_NAVIGATOR_2026"
TOOLS = ROOT / "tools"

for p in [str(CURRENT_DIR), str(TOOLS)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# ── Page Configuration ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="AgroScope360",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Inject Modern Design System & Synthetic Banner ──────────────────────────
from components.theme import apply_custom_theme, render_synthetic_banner  # noqa: E402
apply_custom_theme()
render_synthetic_banner()

# ── Sidebar Navigation & Mode Switcher (Stitch SideNavBar) ──────────────────
with st.sidebar:
    st.markdown(
        """<div style="display:flex; align-items:center; gap:10px; padding:4px 2px 10px 2px;">
<div style="width:36px; height:36px; border-radius:8px; background:#00855d; color:#ffffff; display:flex; align-items:center; justify-content:center; font-weight:800; font-size:18px; box-shadow:0 1px 3px rgba(0,105,72,0.25);">🌱</div>
<div>
<div style="font-family:'Plus Jakarta Sans',sans-serif; font-weight:800; font-size:1.05rem; color:#0b1c30; line-height:1.15;">AgroScope360</div>
<div style="font-size:0.72rem; color:#565e74; font-weight:600;">Agri-Food Climate &amp; Nature Intelligence</div>
</div>
</div>""",
        unsafe_allow_html=True,
    )

    # Persona Quick-Filter
    st.markdown("<div style='font-size:0.68rem; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; color:#565e74; margin-bottom:4px;'>Operational Scope &amp; Perspective</div>", unsafe_allow_html=True)
    role_mode = st.selectbox(
        "Perspective",
        ["Finland & Baltics Group (Executive)", "Auditor & Sustainability Specialist"],
        label_visibility="collapsed",
    )

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:0.68rem; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; color:#565e74; margin-bottom:4px;'>Platform Modules</div>", unsafe_allow_html=True)
    page = st.radio(
        "Navigation",
        [
            "🏠  Executive Overview",
            "📑  Smart ESG Report Generator",
            "⚖️  Trade-off Intelligence",
            "💼  Sustainability Investment Optimiser",
            "🎛️  AI What-If Decision Simulator",
            "🌾  Farm Digital Twin Simulator",
            "🌿  Biodiversity & Nature Hotspots",
            "🚨  Climate Early Warning System",
            "🌍  Geospatial Command Center",
            "📊  GHG Inventory (Scopes 1–3)",
            "🌾  Agronomic Climate Risk",
            "🏞️  Nature & Catchments (SBTN)",
            "🛣️  Decarbonisation & MACC",
            "🤖  AI Sustainability Research Assistant",
        ],
        key="nav_page",
        label_visibility="collapsed",
    )

    st.markdown(
        """<div style="margin-top:14px; padding-top:12px; border-top:1px solid #dce4ee;">
<div style="background:#eff4ff; border:1px solid #dce4ee; border-radius:8px; padding:10px 12px; margin-bottom:10px;">
<div style="font-size:0.74rem; font-weight:800; color:#0b1c30;">✓ Nordic CSRD v2.4</div>
<div style="font-size:0.68rem; color:#006948; font-weight:600;">Audit XBRL Ready · Deterministic Math</div>
</div>
<div style="display:flex; align-items:center; gap:10px; padding:2px 4px;">
<div style="width:30px; height:30px; border-radius:9999px; background:#dae2fd; color:#131b2e; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:0.75rem;">EM</div>
<div>
<div style="font-size:0.78rem; font-weight:700; color:#0b1c30; line-height:1.15;">Esa Mäkinen</div>
<div style="font-size:0.68rem; color:#565e74;">Head of Agronomy &amp; ESG</div>
</div>
</div>
</div>""",
        unsafe_allow_html=True,
    )

import importlib

# ── Page Routing ─────────────────────────────────────────────────────────────
if "Executive Overview" in page:
    import views.overview as v
    importlib.reload(v)
    v.render(ROOT)
elif "Smart ESG Report" in page or "Report Generator" in page:
    import views.report_generator_view as v
    importlib.reload(v)
    v.render(ROOT)
elif "Trade-off" in page:
    import core.tradeoff_service as ts
    importlib.reload(ts)
    import views.tradeoff_view as v
    importlib.reload(v)
    v.render(ROOT)
elif "Sustainability Investment Optimiser" in page:
    import views.investment_optimizer_view as v
    importlib.reload(v)
    v.render(ROOT)
elif "AI What-If Decision Simulator" in page:
    import views.simulator_view as v
    importlib.reload(v)
    v.render(ROOT)
elif "Farm Digital Twin Simulator" in page:
    import views.digital_twin_view as v
    importlib.reload(v)
    v.render(ROOT)
elif "Biodiversity & Nature Hotspots" in page:
    import views.biodiversity_view as v
    importlib.reload(v)
    v.render(ROOT)
elif "Climate Early Warning System" in page:
    import views.early_warning_view as v
    importlib.reload(v)
    v.render(ROOT)
elif "Geospatial Command Center" in page:
    import views.map_view as v
    importlib.reload(v)
    v.render(ROOT)
elif "GHG Inventory" in page:
    import views.inventory as v
    importlib.reload(v)
    v.render(ROOT)
elif "Agronomic Climate Risk" in page:
    import views.crop_risk as v
    importlib.reload(v)
    v.render(ROOT)
elif "Nature & Catchments" in page:
    import views.nature_sbtn as v
    importlib.reload(v)
    v.render(ROOT)
elif "Decarbonisation & MACC" in page:
    import views.pathways as v
    importlib.reload(v)
    v.render(ROOT)
elif "AI Evidence Copilot" in page or "AI Sustainability" in page:
    import core.copilot_service as cs
    importlib.reload(cs)
    import views.copilot as v
    importlib.reload(v)
    v.render(ROOT)
