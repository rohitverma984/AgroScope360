"""
prototype/views/overview.py — Executive Dashboard & 3-Minute Walkthrough (Stitch Nordic Climate Precision UI)
"""
from pathlib import Path
import streamlit as st

from core.api import NavigatorAPI


def _html(raw: str) -> str:
    """Strip per-line indentation so Markdown never turns HTML into a code block."""
    return "\n".join(line.lstrip() for line in raw.splitlines() if line.strip())


def _jump_to(target_page: str) -> None:
    st.session_state["nav_page"] = target_page


def render(root: Path) -> None:
    api = NavigatorAPI(root)
    summary = api.get_executive_summary(2025)

    # ── Stitch Nordic Climate Precision Executive Hero ───────────────────────
    st.markdown(
        _html("""
        <div style="background:linear-gradient(135deg, #ffffff 0%, #eff4ff 100%); border:1px solid #dce4ee; border-left:5px solid #006948; border-radius:10px; padding:18px 22px; margin-bottom:16px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px; box-shadow:0 1px 3px rgba(11,28,48,0.04);">
            <div>
                <div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">
                    <span style="background:#74f8c1; color:#005137; font-size:0.68rem; font-weight:800; padding:2px 8px; border-radius:9999px; text-transform:uppercase; letter-spacing:0.06em;">Stitch UI · Nordic Climate Precision</span>
                    <span style="background:#e5eeff; color:#006194; font-size:0.68rem; font-weight:700; padding:2px 8px; border-radius:9999px;">CSRD ESRS E1 / E4 + SBTi FLAG + SBTN</span>
                </div>
                <div style="font-family:'Plus Jakarta Sans',sans-serif; font-size:1.6rem; font-weight:800; color:#0b1c30; letter-spacing:-0.025em; line-height:1.2;">🌱 Apetit Climate &amp; Nature Navigator</div>
                <div style="font-size:0.86rem; color:#565e74; margin-top:4px; font-weight:500;">Strategic decision platform connecting greenhouse gas accounting, 3D farm digital twins, satellite geomaps, and multi-objective trade-off intelligence across the value chain.</div>
            </div>
        </div>
        """),
        unsafe_allow_html=True,
    )

    # ── Executive KPI Ribbon ──────────────────────────────────────────────────
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("2025 Group GHG Total", f"{summary['emissions_total_tco2e']:,.0f} t", "Scope 1+2m+3")
    k2.metric("FLAG Land Share", f"{summary['flag_emissions_share_pct']:.1f}%", "SBTi Mandated")
    k3.metric("Pea Climate Yield Risk", f"{summary['pea_near_term_yield_delta_pct']:+.1f}%", f"{summary['pea_bad_year_prob']:.0%} bad year risk")
    k4.metric("Nature Hotspots", f"{summary['active_sourcing_catchments']} Catchments", f"Top: {summary['top_nature_priority_catchment']}")
    k5.metric("2030 Abatement", f"{summary['total_abatement_potential_tco2e']:,.0f} t/yr", f"{summary['net_savings_levers_count']} Net-saving levers")

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    # ── Interactive 3D Models, Geomaps & AI Cockpits Quick-Launch Grid ───────
    st.markdown("### 🌐 Interactive 3D Models, Satellite Geomaps & Decision Studios")
    g1, g2, g3, g4, g5 = st.columns(5)

    with g1:
        st.markdown(
            _html("""
            <div style="background:#ffffff; border:1px solid #dce4ee; border-top:4px solid #006948; border-radius:8px; padding:14px 16px; margin-bottom:8px;">
                <div style="font-size:0.68rem; font-weight:800; color:#006948; text-transform:uppercase; letter-spacing:0.06em;">3D Terrain + Esri Satellite</div>
                <div style="font-family:'Plus Jakarta Sans',sans-serif; font-size:0.95rem; font-weight:800; color:#0b1c30; margin:4px 0;">🌾 3D Farm Digital Twin</div>
                <div style="font-size:0.76rem; color:#565e74; line-height:1.4;">3D satellite terrain mesh, organic field polygons, soil moisture &amp; Earth-Score.</div>
            </div>
            """),
            unsafe_allow_html=True,
        )
        st.button(
            "3D Digital Twin →",
            key="btn_launch_twin",
            on_click=_jump_to,
            args=("🌾  Farm Digital Twin Simulator",),
            use_container_width=True,
        )

    with g2:
        st.markdown(
            _html("""
            <div style="background:#ffffff; border:1px solid #dce4ee; border-top:4px solid #006194; border-radius:8px; padding:14px 16px; margin-bottom:8px;">
                <div style="font-size:0.68rem; font-weight:800; color:#006194; text-transform:uppercase; letter-spacing:0.06em;">3D PyDeck WebGL + Live APIs</div>
                <div style="font-family:'Plus Jakarta Sans',sans-serif; font-size:0.95rem; font-weight:800; color:#0b1c30; margin:4px 0;">🌍 3D Geospatial Map</div>
                <div style="font-size:0.76rem; color:#565e74; line-height:1.4;">Extruded field columns, inbound freight arcs, Open-Meteo &amp; Baltic marine AIS.</div>
            </div>
            """),
            unsafe_allow_html=True,
        )
        st.button(
            "3D Geospatial Map →",
            key="btn_launch_geomap",
            on_click=_jump_to,
            args=("🌍  Geospatial Command Center",),
            use_container_width=True,
        )

    with g3:
        st.markdown(
            _html("""
            <div style="background:#ffffff; border:1px solid #dce4ee; border-top:4px solid #ef4444; border-radius:8px; padding:14px 16px; margin-bottom:8px;">
                <div style="font-size:0.68rem; font-weight:800; color:#dc2626; text-transform:uppercase; letter-spacing:0.06em;">3D SSP Stress + Basin Map</div>
                <div style="font-family:'Plus Jakarta Sans',sans-serif; font-size:0.95rem; font-weight:800; color:#0b1c30; margin:4px 0;">🌡️ Climate Risk Geomap</div>
                <div style="font-size:0.76rem; color:#565e74; line-height:1.4;">3D flowering heat-stress columns, drought deficit geomap &amp; multi-crop SSP yields.</div>
            </div>
            """),
            unsafe_allow_html=True,
        )
        st.button(
            "Climate Geomap →",
            key="btn_launch_clim_map",
            on_click=_jump_to,
            args=("🌾  Agronomic Climate Risk",),
            use_container_width=True,
        )

    with g4:
        st.markdown(
            _html("""
            <div style="background:#ffffff; border:1px solid #dce4ee; border-top:4px solid #059669; border-radius:8px; padding:14px 16px; margin-bottom:8px;">
                <div style="font-size:0.68rem; font-weight:800; color:#059669; text-transform:uppercase; letter-spacing:0.06em;">Circular Satellite Mask + CORINE</div>
                <div style="font-family:'Plus Jakarta Sans',sans-serif; font-size:0.95rem; font-weight:800; color:#0b1c30; margin:4px 0;">🌿 Biodiversity Map</div>
                <div style="font-size:0.76rem; color:#565e74; line-height:1.4;">High-res satellite lens over Säkylä Pyhäjärvi with Natura 2000 &amp; water bodies.</div>
            </div>
            """),
            unsafe_allow_html=True,
        )
        st.button(
            "Biodiversity Map →",
            key="btn_launch_bio",
            on_click=_jump_to,
            args=("🌿  Biodiversity & Nature Hotspots",),
            use_container_width=True,
        )

    with g5:
        st.markdown(
            _html("""
            <div style="background:#ffffff; border:1px solid #dce4ee; border-top:4px solid #d97706; border-radius:8px; padding:14px 16px; margin-bottom:8px;">
                <div style="font-size:0.68rem; font-weight:800; color:#b45309; text-transform:uppercase; letter-spacing:0.06em;">Multi-Objective AI Analysis</div>
                <div style="font-family:'Plus Jakarta Sans',sans-serif; font-size:0.95rem; font-weight:800; color:#0b1c30; margin:4px 0;">⚖️ Trade-off Studio</div>
                <div style="font-size:0.76rem; color:#565e74; line-height:1.4;">Evaluate water savings vs. pumping energy, fertilizer efficiency &amp; CAPEX across 6 axes.</div>
            </div>
            """),
            unsafe_allow_html=True,
        )
        st.button(
            "Trade-off Studio →",
            key="btn_launch_tradeoff",
            on_click=_jump_to,
            args=("⚖️  Trade-off Intelligence",),
            use_container_width=True,
        )

    st.divider()

    # ── 3-Minute Pitch Walkthrough ───────────────────────────────────────────
    st.markdown("### 🧭 3-Minute Executive Tour: From Fragmented Data to Action")

    tour_tab1, tour_tab2, tour_tab3, tour_tab4 = st.tabs([
        "1️⃣ Auditable 2025 Baseline",
        "2️⃣ Future Climate Risk to Crops",
        "3️⃣ SBTN Freshwater Nature",
        "4️⃣ Decarbonisation & MACC",
    ])

    with tour_tab1:
        st.markdown("#### Step 1: Trustworthy Baseline with Audit Proof")
        st.write(
            "Corporate data contains planted real-world errors: unit slips, duplicate invoices, and missing meter logs. "
            "Our automated screening identifies data quality issues before computing canonical GHG totals."
        )
        c1, c2, c3 = st.columns(3)
        c1.metric("Scope 1 (Combustion/Refrigerants)", f"{summary['scope1_tco2e']:,.0f} tCO₂e")
        c2.metric("Scope 2 (Market-based)", f"{summary['scope2_market_tco2e']:,.0f} tCO₂e")
        c3.metric("Scope 3 (Value Chain)", f"{summary['scope3_tco2e']:,.0f} tCO₂e")
        st.caption("👉 Drill into individual ERP doc lines and meter logs in **📊 GHG Inventory 2025**.")

    with tour_tab2:
        st.markdown("#### Step 2: Predicting Yield Volatility Under Climate Change")
        st.write(
            "Weather drives yields, and yields drive costs and emissions per kilogram. "
            "Using daily and monthly simulations from 1991 to 2060, we quantify the probability of heat stress and bad harvest years for contract green peas and root crops."
        )
        st.info(
            f"Under intermediate warming (SSP2-4.5), Finnish contract green pea yields face a "
            f"**{summary['pea_bad_year_prob']:.0%} probability of falling below 80% of historical baseline** in 2027–2031.",
            icon="🌾",
        )
        st.caption("👉 Test multi-crop scenarios (Pea, Potato, Carrot, Turnip Rape) in **🌾 Crop Climate Risk**.")

    with tour_tab3:
        st.markdown("#### Step 3: Science Based Targets for Nature (SBTN)")
        st.write(
            "Climate action alone misses local water impacts. Agricultural phosphorus (P) and nitrogen (N) "
            "drive eutrophication in Finnish lakes and the Baltic Sea. We rank catchments combining delivered loads with ecological vulnerability."
        )
        st.warning(
            f"Priority Catchment **{summary['top_nature_priority_catchment']}** has contract fields with only "
            f"**{summary['buffer_strip_coverage_pct']:.1f}% riparian buffer strip coverage**, representing an immediate, high-impact intervention opportunity.",
            icon="🏞️",
        )
        st.caption("👉 Explore parcel maps and buffer strip opportunities in **🏞️ Nature & Catchments**.")

    with tour_tab4:
        st.markdown("#### Step 4: Cost-Optimized Abatement & Governance")
        st.write(
            "We construct a 2030 Marginal Abatement Cost Curve (MACC) across 28 levers, strictly separating physical emissions cuts "
            "from structural M&A changes and accounting improvements. Recommendations require explicit human sign-off."
        )
        st.success(
            f"Identified **{summary['net_savings_levers_count']} cost-negative levers** delivering net economic savings while reducing emissions. "
            f"Total group abatement capacity is **{summary['total_abatement_potential_tco2e']:,.0f} tCO₂e/yr** by 2030.",
            icon="💡",
        )
        st.caption("👉 Review the MACC curve and sign off on levers in **🛣️ Pathways & Actions**.")

    st.divider()

    # ── Executive Report Exporter ─────────────────────────────────────────────
    st.markdown("### 📥 Compliance & Audit Export")
    col_exp1, col_exp2 = st.columns([3, 1])
    with col_exp1:
        st.write("Generate a consolidated audit summary markdown report containing key figures, formulas, and data provenance.")
    with col_exp2:
        export_text = f"""# Apetit Climate & Nature Navigator — Executive Audit Report
Generated: 2026-11-07
Dataset Twin: v1.0.0 (Synthetic estimates calibrated to Apetit public disclosures)

## 1. 2025 GHG Inventory (GHG Protocol AR6 GWP100)
- Scope 1: {summary['scope1_tco2e']:,.2f} tCO2e
- Scope 2 (Market-based): {summary['scope2_market_tco2e']:,.2f} tCO2e
- Scope 3: {summary['scope3_tco2e']:,.2f} tCO2e
- Total Group: {summary['emissions_total_tco2e']:,.2f} tCO2e
- FLAG Share: {summary['flag_emissions_share_pct']:.1f}%

## 2. Agronomic Climate Risk (SSP2-4.5)
- Finnish Pea Near-Term Yield Delta: {summary['pea_near_term_yield_delta_pct']:+.1f}%
- Near-Term Bad Year Probability: {summary['pea_bad_year_prob']:.0%}

## 3. Freshwater Nature Prioritisation (SBTN)
- Active Sourcing Catchments: {summary['active_sourcing_catchments']}
- Top Nature Hotspot: {summary['top_nature_priority_catchment']}
- Buffer Strip Coverage: {summary['buffer_strip_coverage_pct']:.1f}%

## 4. Decarbonisation Strategy (2030 MACC)
- 2030 Abatement Capacity: {summary['total_abatement_potential_tco2e']:,.0f} tCO2e/yr
- Net Savings Levers: {summary['net_savings_levers_count']} levers
"""
        st.download_button(
            label="📄 Download Audit Summary (MD)",
            data=export_text,
            file_name="Apetit_Climate_Nature_Audit_Summary_2025.md",
            mime="text/markdown",
        )
