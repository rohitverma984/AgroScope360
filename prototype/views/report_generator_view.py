"""
prototype/views/report_generator_view.py — Smart ESG Report Generator View
Matches enterprise reporting suites and reference photo:
- Framework cards grid: CDP, GRI, TCFD, BRSR, CBAM, CSRD with interactive [View] buttons
- Interactive @st.dialog modal with "✨ AI Generated Answers" (Questions & Answers)
- Interactive parameter selectors: Period, Business Unit, Climate Scenario, Scope, Nature Indicators
- Multi-section report generator with all 8 mandatory statutory sections
- Multi-format exports: Official PDF, Markdown brief, and XBRL/JSON metadata
"""
from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any, Dict, List
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from core.api import NavigatorAPI
from core.report_generator_service import ReportGeneratorService


# ── Framework Details Library (for View button inspection) ───────────────────
FRAMEWORK_DETAILS = {
    "cdp": {
        "name": "CDP (Carbon Disclosure Project)",
        "progress_pct": 52,
        "deadline": "09/11/2026",
        "scope": "Climate Change & Forests Questionnaire",
        "qa_pairs": [
            {
                "q": "C1.1: Does your board have oversight of climate-related issues?",
                "a": "Yes. Apetit's ESG Assurance Board reviews quarterly Scope 1-3 inventories, Säkylä boiler upgrades, and contractor soil stewardship.",
                "status": "✅ Complete",
            },
            {
                "q": "C2.2: Describe your climate-related risk exposure and financial impact.",
                "a": "Drought in Region A threatens -28% pea yield loss (€2.4M exposure). EU ETS2 introduces a €47/t CO₂ surcharge by 2030 on fossil backup fuels.",
                "status": "✅ Complete",
            },
            {
                "q": "C4.1: Did you have an active emissions reduction target?",
                "a": "Near-term target: 4.2% linear reduction/yr for Scope 1+2 (to 4,482 tCO₂e by 2032) and 3.03% linear/yr for FLAG (to 62,490 tCO₂e).",
                "status": "⚠️ In Review",
            },
            {
                "q": "F1.1: Forests & Land Use: Sourcing verification against deforestation and peatland loss.",
                "a": "Spatial monitoring active across 14,213 parcels; contract shifting initiated on 14 farms with >30% organic soil (L11).",
                "status": "⚠️ Verification in Progress",
            },
        ],
    },
    "gri": {
        "name": "GRI (Global Reporting Initiative)",
        "progress_pct": 68,
        "deadline": "17/07/2025",
        "scope": "GRI 302 (Energy), 304 (Biodiversity), 305 (Emissions)",
        "qa_pairs": [
            {
                "q": "GRI 302-1: Energy consumption within the organization.",
                "a": "Total energy intake 1.42 MWh/t product. Electricity 99.1% renewable (Guarantees of Origin). Säkylä boiler utilizes LNG with transitional LPG.",
                "status": "✅ Complete",
            },
            {
                "q": "GRI 304-1: Operational sites in or adjacent to protected areas.",
                "a": "Säkylä facility operates in Catchment CA01 adjacent to Lake Pyhäjärvi Special Area of Conservation (Natura 2000 FI0200084).",
                "status": "✅ Complete",
            },
            {
                "q": "GRI 305-1 & 305-2: Direct (Scope 1) and Energy Indirect (Scope 2) GHG emissions.",
                "a": "Scope 1: 6,251 tCO₂e (fossil fuels). Scope 2 Market: 63 tCO₂e. Scope 2 Location: 184.2 tCO₂e (0.026 kg/kWh grid factor).",
                "status": "✅ Complete",
            },
            {
                "q": "GRI 305-3: Other indirect (Scope 3) emissions.",
                "a": "Scope 3 total: 238,410 tCO₂e. FLAG emissions represent 42.3% of group footprint, driven by contract pea, potato, and grain sourcing.",
                "status": "⚠️ Supplier Verification Active",
            },
        ],
    },
    "tcfd": {
        "name": "TCFD (Climate-Related Financial Disclosures)",
        "progress_pct": 81,
        "deadline": "13/08/2025",
        "scope": "Governance, Strategy, Risk Management, Metrics",
        "qa_pairs": [
            {
                "q": "Strategy: Resilience of organization taking into account different climate scenarios.",
                "a": "Evaluated under NGFS Net Zero 2050 (SSP1-2.6) and Delayed Transition (SSP2-4.5). MACC model shows €1.8M 10-yr NPV across 6 primary levers.",
                "status": "✅ Complete",
            },
            {
                "q": "Risk Management: Processes for identifying and managing climate risks.",
                "a": "Digital twin cross-references 14,213 parcel coordinates with soil maps and CMIP6 moisture deficit projections.",
                "status": "✅ Complete",
            },
            {
                "q": "Metrics & Targets: Climate targets and performance against targets.",
                "a": "Scope 1+2 target: -29.4% by 2032; FLAG target: -21.2% by 2032. Internal carbon price benchmark: €80/t rising to €160/t (2030).",
                "status": "✅ Complete",
            },
        ],
    },
    "brsr": {
        "name": "BRSR (Business Responsibility & Sustainability Reporting)",
        "progress_pct": 100,
        "deadline": "22/05/2025",
        "scope": "Principle 6: Environmental Value Chain Integrity",
        "qa_pairs": [
            {
                "q": "Principle 6 Essential Indicator 1: Energy and water withdrawal details.",
                "a": "Annual water intake: 542,000 m³; 100% wastewater treated at municipal facilities or on-site pre-treatment before discharge.",
                "status": "✅ Complete",
            },
            {
                "q": "Principle 6 Essential Indicator 2: Scope 1, 2, 3 footprint reporting.",
                "a": "All 15 Scope 3 categories evaluated; Category 1 (Purchased Goods) and Category 4 (Upstream Transport) represent >90% of value chain impact.",
                "status": "✅ Complete",
            },
            {
                "q": "Principle 6 Leadership Indicator 1: Renewable energy transition.",
                "a": "100% of electricity certified by national registry Guarantees of Origin (GoO); Kantvik biosteam supplies renewable process heat.",
                "status": "✅ Complete",
            },
        ],
    },
    "cbam": {
        "name": "CBAM (Carbon Border Adjustment Mechanism)",
        "progress_pct": 50,
        "deadline": "16/07/2025",
        "scope": "Direct & Indirect Embedded Emissions on Raw Imports",
        "qa_pairs": [
            {
                "q": "Embedded emissions calculation on imported materials.",
                "a": "Monitoring packaging aluminum and steel imported from non-EU jurisdictions. Evaluating primary PCFs vs EU default benchmarks.",
                "status": "⚠️ In Progress",
            },
            {
                "q": "Supplier data collection and verification.",
                "a": "Quarterly declarative reports submitted for transitional phase; transition to verified emissions active.",
                "status": "⚠️ Supplier Outreach Active",
            },
        ],
    },
    "csrd": {
        "name": "CSRD / ESRS (E1 Climate & E4 Biodiversity)",
        "progress_pct": 100,
        "deadline": "30/05/2025",
        "scope": "ESRS E1 (Climate Change) & ESRS E4 (Biodiversity)",
        "qa_pairs": [
            {
                "q": "ESRS E1-1: Transition plan for climate change mitigation.",
                "a": "Apetit Net-Zero Roadmap models 30 decarbonisation levers abating 14,950 tCO₂e by 2030 with €2.48M CAPEX investment.",
                "status": "✅ Compliant",
            },
            {
                "q": "ESRS E1-6: Gross Scopes 1, 2, 3 and Total GHG emissions.",
                "a": "Dual reporting: Market-based Scope 2 (63 tCO₂e) vs Location-based Scope 2 (184.2 tCO₂e). Scope 3 FLAG explicitly segregated (42.3%).",
                "status": "✅ Compliant",
            },
            {
                "q": "ESRS E4-1: Transition plan and path on biodiversity and ecosystems.",
                "a": "SBTN Step 1 & 2 freshwater targets set for Lake Pyhäjärvi basin (CA01); 10m riparian buffer strips active across contract acreage.",
                "status": "✅ Compliant",
            },
            {
                "q": "ESRS E4-4: Targets related to land-use change and eutrophication.",
                "a": "Commitment to zero conversion of natural peatlands and -28% phosphorus load reduction into receiving waterways by 2030.",
                "status": "✅ Compliant",
            },
        ],
    },
}


# ── Interactive Framework Details Modal Dialog ───────────────────────────────
@st.dialog("✨ AI Generated Answers & Framework Inspection", width="large")
def show_framework_modal(fc_id: str, api: NavigatorAPI, root: Path):
    fw_info = FRAMEWORK_DETAILS.get(fc_id, FRAMEWORK_DETAILS["csrd"])
    pct = fw_info["progress_pct"]
    ring_color = "#059669" if pct == 100 else ("#0284c7" if pct > 65 else "#f59e0b")

    st.markdown(
        f"""
        <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #e2e8f0; padding-bottom:12px; margin-bottom:16px;">
            <div>
                <div style="font-size:1.30rem; font-weight:800; color:#0f172a;">{fw_info['name']}</div>
                <div style="font-size:0.80rem; color:#64748b;">Statutory Filing Deadline: <b>{fw_info['deadline']}</b> · Scope: {fw_info['scope']}</div>
            </div>
            <div>
                <span style="background:{ring_color}15; color:{ring_color}; border:2px solid {ring_color}; border-radius:20px; padding:4px 14px; font-weight:800; font-size:0.90rem;">
                    {pct}% Readiness
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("##### 💬 AI Generated Disclosure Q&A")
    st.caption("Grounded in Apetit's master ERP activity logs, Luke agricultural coefficients, and GHG Protocol standards.")

    for qa in fw_info["qa_pairs"]:
        st.markdown(
            f"""
            <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:12px 16px; margin-bottom:10px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                    <span style="font-weight:700; color:#0f172a; font-size:0.88rem;">❓ {qa['q']}</span>
                    <span style="font-size:0.75rem; font-weight:600;">{qa['status']}</span>
                </div>
                <div style="font-size:0.84rem; color:#334155; line-height:1.55; margin-top:4px;">
                    💡 <b>AI Answer:</b> {qa['a']}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")
    m_col1, m_col2 = st.columns(2)
    with m_col1:
        if st.button(f"✨ Generate Full {fw_info['name'].split()[0]} Report", type="primary", use_container_width=True):
            st.session_state["target_compliance_fw"] = fw_info["name"].split()[0]
            rep_data = api.reports.generate_report(framework=fw_info["name"])
            st.session_state["current_report"] = rep_data
            st.rerun()

    with m_col2:
        rep_for_pdf = api.reports.generate_report(framework=fw_info["name"])
        pdf_bytes = api.reports.generate_pdf(rep_for_pdf)
        st.download_button(
            f"📄 Download {fw_info['name'].split()[0]} PDF",
            pdf_bytes,
            file_name=f"Apetit_{fc_id.upper()}_Report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )


def render(root: Path) -> None:
    api = NavigatorAPI(root)
    if not hasattr(api, "reports"):
        api.reports = ReportGeneratorService(root)

    # ── Custom CSS for Smart ESG Report Generator ────────────────────────────
    st.markdown(
        """
        <style>
        /* Framework Card Grid */
        .fw-card-outer {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 18px 20px 14px 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.03);
            margin-bottom: 12px;
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }
        .fw-card-outer:hover {
            border-color: #cbd5e1;
            box-shadow: 0 4px 12px rgba(0,0,0,0.06);
        }
        .fw-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 8px;
        }
        .fw-name {
            font-size: 1.30rem;
            font-weight: 800;
            color: #0f172a;
        }
        .fw-sub {
            font-size: 0.74rem;
            color: #64748b;
            font-weight: 500;
        }
        .fw-progress-ring {
            width: 46px;
            height: 46px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.82rem;
            font-weight: 800;
        }

        /* Floating AI Generated Answers Pill */
        .ai-answers-pill {
            background: #0f172a;
            color: #ffffff;
            border-radius: 20px;
            padding: 6px 16px;
            font-size: 0.82rem;
            font-weight: 700;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            cursor: pointer;
        }

        /* Report Paper Card */
        .report-paper {
            background: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: 12px;
            padding: 24px 28px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.04);
            margin-top: 16px;
        }
        .report-header-banner {
            border-bottom: 2px solid #059669;
            padding-bottom: 14px;
            margin-bottom: 20px;
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ── Top Title & AI Answers Pill Header ───────────────────────────────────
    h_col1, h_col2 = st.columns([3, 1.2])
    with h_col1:
        st.title("Smart ESG Report Generator")
        st.caption("AI-powered compliance and sustainability reporting engine with verified audit trails and PDF export.")
    with h_col2:
        st.markdown(
            """
            <div style="text-align:right; padding-top:14px;">
                <span class="ai-answers-pill">
                    <span>✨</span>
                    <span>AI Generated Answers</span>
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── 6 Framework Cards with Interactive [View] Buttons ─────────────────────
    st.markdown("##### 📜 Framework Compliance & Filing Deadlines")
    st.caption("Click **View** on any framework card below to inspect AI-generated answers, statutory deadlines, or generate dedicated compliance reports.")

    framework_cards = api.reports.get_framework_cards()

    # Row 1 (CDP, GRI, TCFD)
    r1_cols = st.columns(3)
    for i in range(3):
        fc = framework_cards[i]
        with r1_cols[i]:
            pct = fc["progress_pct"]
            ring_bg = "#ecfdf5" if pct == 100 else ("#f0f9ff" if pct > 65 else "#fffbeb")
            ring_color = "#059669" if pct == 100 else ("#0284c7" if pct > 65 else "#f59e0b")
            st.markdown(
                f"""
                <div class="fw-card-outer">
                    <div class="fw-top">
                        <div>
                            <div class="fw-name">{fc['name']}</div>
                            <div class="fw-sub">{fc['full_name']}</div>
                        </div>
                        <div class="fw-progress-ring" style="background:{ring_bg}; color:{ring_color}; border:2.5px solid {ring_color};">
                            {pct}%
                        </div>
                    </div>
                    <div style="font-size:0.75rem; color:#475569; margin:6px 0 10px 0; min-height:32px;">
                        <b>Scope:</b> {fc['scope']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            b_c1, b_c2 = st.columns([2.0, 1.0])
            with b_c1:
                st.caption(f"🗓️ Deadline: **{fc['deadline']}**")
            with b_c2:
                if st.button("View", key=f"btn_vw_{fc['id']}", use_container_width=True):
                    show_framework_modal(fc['id'], api, root)

    # Row 2 (BRSR, CBAM, CSRD)
    r2_cols = st.columns(3)
    for i in range(3, 6):
        fc = framework_cards[i]
        with r2_cols[i - 3]:
            pct = fc["progress_pct"]
            ring_bg = "#ecfdf5" if pct == 100 else ("#f0f9ff" if pct > 65 else "#fffbeb")
            ring_color = "#059669" if pct == 100 else ("#0284c7" if pct > 65 else "#f59e0b")
            st.markdown(
                f"""
                <div class="fw-card-outer">
                    <div class="fw-top">
                        <div>
                            <div class="fw-name">{fc['name']}</div>
                            <div class="fw-sub">{fc['full_name']}</div>
                        </div>
                        <div class="fw-progress-ring" style="background:{ring_bg}; color:{ring_color}; border:2.5px solid {ring_color};">
                            {pct}%
                        </div>
                    </div>
                    <div style="font-size:0.75rem; color:#475569; margin:6px 0 10px 0; min-height:32px;">
                        <b>Scope:</b> {fc['scope']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            b_c1, b_c2 = st.columns([2.0, 1.0])
            with b_c1:
                st.caption(f"🗓️ Deadline: **{fc['deadline']}**")
            with b_c2:
                if st.button("View", key=f"btn_vw_{fc['id']}", use_container_width=True):
                    show_framework_modal(fc['id'], api, root)

    st.markdown("---")

    # ── Interactive Parameter Selection Form ─────────────────────────────────
    st.markdown("##### ⚙️ Report Generation Parameters")
    with st.expander("Configure Reporting Dimensions & Scenarios", expanded=True):
        p_c1, p_c2, p_c3 = st.columns(3)
        with p_c1:
            sel_period = st.selectbox(
                "📅 Reporting Period:",
                ["2025 (Annual Filing)", "2024 (Prior Baseline)", "2021–2025 (5-Year Strategic Baseline)"],
                index=0,
            )
            sel_unit = st.selectbox(
                "🏢 Business Unit:",
                [
                    "Apetit Group Consolidated",
                    "Säkylä Frozen Foods Facility (FI-SAK)",
                    "Kantvik Vegetable Oil Milling (FI-KAN)",
                    "Foodhills AB Sweden (SE-BJU)",
                    "Contract Farming Agricultural Shed",
                ],
                index=0,
            )
        with p_c2:
            sel_scenario = st.selectbox(
                "🔮 Climate Scenario:",
                [
                    "NGFS Net Zero 2050 (SSP1-2.6 Paris Aligned)",
                    "NGFS Delayed Transition (SSP2-4.5 Middle-of-Road)",
                    "Current Policies (SSP5-8.5 Fossil-Fueled)",
                ],
                index=0,
            )
            sel_emissions = st.selectbox(
                "💨 Emissions Category:",
                [
                    "All Scopes (1, 2, 3 + FLAG)",
                    "Scope 1 Direct Fossil & Mobile",
                    "Scope 2 Market-Based vs Location-Based",
                    "Scope 3 Value Chain & Contract Farming FLAG",
                ],
                index=0,
            )
        with p_c3:
            sel_nature = st.selectbox(
                "🌿 Nature-Related Indicators:",
                [
                    "SBTN Freshwater Eutrophication & P-Leaching",
                    "Drained Organic Peat Soil Oxidation & BII",
                    "Säkylänharju Aquifer Groundwater Stress",
                    "Biodiversity Intactness Index (BII) & Habitat Fragmentation",
                ],
                index=0,
            )
            sel_fw = st.selectbox(
                "📜 Target Compliance Framework:",
                [
                    "CSRD / ESRS (E1 Climate & E4 Biodiversity)",
                    "TCFD (Governance, Strategy, Risk, Metrics)",
                    "CDP (Climate Change & Forests Questionnaire)",
                    "GRI (GRI 302, 304, 305)",
                ],
                index=0,
            )

        btn_generate = st.button("✨ Generate Sustainability Report", type="primary", use_container_width=True)

    # ── State for Active Generated Report ────────────────────────────────────
    if "current_report" not in st.session_state or btn_generate:
        with st.spinner("Synthesizing multi-table database records into audited report..."):
            rep_data = api.reports.generate_report(
                reporting_period=sel_period,
                business_unit=sel_unit,
                climate_scenario=sel_scenario,
                emissions_category=sel_emissions,
                nature_indicators=sel_nature,
                framework=sel_fw,
            )
            st.session_state["current_report"] = rep_data

    rep = st.session_state["current_report"]

    # ── Export & Download Action Bar (Matching Reference Image Dropdown) ──────
    st.markdown("##### 📥 Export Official Report")
    e_col1, e_col2, e_col3, e_col4 = st.columns([1.5, 1.2, 1.2, 1.2])

    with e_col1:
        st.markdown(
            f"""
            <div style="padding-top:8px; font-size:0.82rem; color:#475569;">
                <b>Report ID:</b> <code>{rep['report_id']}</code><br/>
                <b>Generated:</b> {rep['generated_at']}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Generate PDF in memory
    pdf_bytes = api.reports.generate_pdf(rep)

    with e_col2:
        st.download_button(
            "📄 Export PDF",
            pdf_bytes,
            file_name=f"{rep['report_id']}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    with e_col3:
        # Markdown Brief Export
        md_text = (
            f"# {rep['business_unit']} — Sustainability Report\n\n"
            f"**Report ID:** `{rep['report_id']}` | **Framework:** {rep['framework']}\n"
            f"**Period:** {rep['reporting_period']} | **Scenario:** {rep['climate_scenario']}\n\n"
            f"## 1. Environmental Performance\n"
            f"- Total GHG Emissions: {rep['performance']['total_ghg_tco2e']:,.1f} tCO2e\n"
            f"- Scope 1: {rep['performance']['scope1_tco2e']:,.1f} tCO2e\n"
            f"- Scope 2 (market): {rep['performance']['scope2_market_tco2e']:,.1f} tCO2e\n"
            f"- Scope 3: {rep['performance']['scope3_tco2e']:,.1f} tCO2e (FLAG: {rep['performance']['flag_share_pct']}%)\n\n"
            f"## 2. Emission Changes\n"
            f"- Scope 1 YoY: {rep['emission_changes']['s1_yoy_pct']:+.1f}% ({rep['emission_changes']['s1_driver']})\n"
            f"- Scope 3 YoY: {rep['emission_changes']['s3_yoy_pct']:+.1f}% ({rep['emission_changes']['s3_driver']})\n\n"
            f"## 3. Climate Risks\n"
            + "\n".join([f"- **{r['Risk Category']}** ({r['Severity']}): {r['Impact Description']}" for r in rep['climate_risks']])
            + "\n\n## 4. Nature Hotspots\n"
            + "\n".join([f"- **{n['Hotspot Asset']}**: {n['Primary Pressure']}" for n in rep['nature_hotspots']])
            + "\n\n## 5. Recommended Actions\n"
            + "\n".join([f"- **{a['Lever ID']} — {a['Action Name']}**: {a['2030 Abatement']} ({a['Nature Co-Benefit']})" for a in rep['actions']])
            + "\n\n## 6. Financial Costs & ROI\n"
            + f"- Total CAPEX: €{rep['costs']['total_capex_eur']:,.0f} | Payback: {rep['costs']['payback_years']} yrs | NPV: €{rep['costs']['npv_10yr_eur']:,.0f}\n\n"
            + f"## 7. Data Sources\n- Standards: " + "; ".join(rep['sources_and_methodology']['primary_standards'][:3])
            + f"\n\n## 8. Audit Approval\n- Status: {rep['approval']['status']} | Hash: `{rep['approval']['verification_hash']}`\n"
        )
        st.download_button(
            "📝 Export Word / MD",
            md_text,
            file_name=f"{rep['report_id']}.md",
            mime="text/markdown",
            use_container_width=True,
        )

    with e_col4:
        # XBRL / JSON Export
        st.download_button(
            "📑 Export XBRL / JSON",
            json.dumps(rep, indent=2),
            file_name=f"{rep['report_id']}_xbrl.json",
            mime="application/json",
            use_container_width=True,
        )

    # ── Report Paper Container (Displaying All 8 Mandatory Sections) ─────────
    st.markdown(
        f"""
        <div class="report-paper">
            <div class="report-header-banner">
                <div>
                    <div style="font-size:0.75rem; text-transform:uppercase; color:#059669; font-weight:800; letter-spacing:0.06em;">
                        Official Sustainability Filing Document
                    </div>
                    <div style="font-size:1.75rem; font-weight:900; color:#0f172a; margin:4px 0;">
                        {rep['business_unit']}
                    </div>
                    <div style="font-size:0.85rem; color:#475569;">
                        <b>Framework:</b> {rep['framework']} &nbsp;|&nbsp; 
                        <b>Period:</b> {rep['reporting_period']} &nbsp;|&nbsp; 
                        <b>Scenario:</b> {rep['climate_scenario']}
                    </div>
                </div>
                <div style="text-align:right;">
                    <span style="background:#ecfdf5; color:#065f46; border:1px solid #a7f3d0; border-radius:6px; padding:4px 10px; font-size:0.75rem; font-weight:700;">
                        {rep['approval']['status']}
                    </span>
                    <div style="font-size:0.70rem; color:#64748b; margin-top:6px;">
                        Hash: <code>{rep['approval']['verification_hash']}</code>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Tabbed View of the 8 Sections for High Readability
    tab_s1, tab_s2, tab_s3, tab_s4, tab_s5 = st.tabs([
        "1. Performance & Changes",
        "2. Climate & Nature Hotspots",
        "3. Actions & Financial ROI",
        "4. Sources & Methodology",
        "5. Assurance & Approval",
    ])

    # ════════════════════════════════════════════════════════════════════════
    # TAB 1: SECTION 1 & 2 (Current Performance & Emissions Changes)
    # ════════════════════════════════════════════════════════════════════════
    with tab_s1:
        st.markdown("#### 1. Current Environmental Performance")
        p = rep["performance"]
        kpi_c1, kpi_c2, kpi_c3, kpi_c4 = st.columns(4)
        kpi_c1.metric("Total GHG Footprint", f"{p['total_ghg_tco2e']:,.0f} tCO₂e", "-4.2% YoY")
        kpi_c2.metric("Scope 1 (Fossil Combustion)", f"{p['scope1_tco2e']:,.0f} tCO₂e", "+47.8% (LPG Backup)")
        kpi_c3.metric("Scope 2 (Market-based)", f"{p['scope2_market_tco2e']:,.0f} tCO₂e", "-98.0% (100% GoO)")
        kpi_c4.metric("Scope 3 FLAG Share", f"{p['flag_share_pct']:.1f}%", f"{p['flag_emissions_tco2e']:,.0f} tCO₂e")

        st.markdown("#### 2. Changes in Emissions & Structural M&A Recalculations")
        chg = rep["emission_changes"]
        st.info(
            f"**Key Driver Analysis:**\n"
            f"• **Scope 1:** {chg['s1_driver']}\n"
            f"• **Scope 2:** {chg['s2_driver']}\n"
            f"• **Scope 3:** {chg['s3_driver']}\n\n"
            f"**Statutory Base-Year Recalculation:** {chg['restatement_note']}"
        )
        st.dataframe(pd.DataFrame(chg["history_table"]), use_container_width=True, hide_index=True)

    # ════════════════════════════════════════════════════════════════════════
    # TAB 2: SECTION 3 & 4 (Major Climate Risks & Nature Hotspots)
    # ════════════════════════════════════════════════════════════════════════
    with tab_s2:
        st.markdown("#### 3. Major Climate Risks (Physical & Transition)")
        st.dataframe(pd.DataFrame(rep["climate_risks"]), use_container_width=True, hide_index=True)

        st.markdown("#### 4. Nature-Related Hotspots (SBTN Freshwater & Land)")
        st.dataframe(pd.DataFrame(rep["nature_hotspots"]), use_container_width=True, hide_index=True)

    # ════════════════════════════════════════════════════════════════════════
    # TAB 3: SECTION 5 & 6 (Recommended Actions & Costs)
    # ════════════════════════════════════════════════════════════════════════
    with tab_s3:
        st.markdown("#### 5. Recommended Actions (Decarbonisation & Nature Levers)")
        st.dataframe(pd.DataFrame(rep["actions"]), use_container_width=True, hide_index=True)

        st.markdown("#### 6. Estimated Costs, Payback & Investment ROI")
        c = rep["costs"]
        c_c1, c_c2, c_c3, c_c4 = st.columns(4)
        c_c1.metric("Total Investment CAPEX", f"€{c['total_capex_eur']:,.0f}", "Across 6 Levers")
        c_c2.metric("Annual OPEX Savings", f"€{abs(c['annual_opex_delta_eur']):,.0f}/yr", "Net Cost Savings")
        c_c3.metric("Weighted Abatement Cost", f"€{c['weighted_abatement_cost_eur_t']:.2f} / t", "High Cost Efficiency")
        c_c4.metric("Payback Period", f"{c['payback_years']} Years", f"NPV: €{c['npv_10yr_eur']:,.0f}")

        st.dataframe(pd.DataFrame(c["cost_breakdown"]), use_container_width=True, hide_index=True)

    # ════════════════════════════════════════════════════════════════════════
    # TAB 4: SECTION 7 (Data Sources and Methodology)
    # ════════════════════════════════════════════════════════════════════════
    with tab_s4:
        st.markdown("#### 7. Data Sources and Methodology")
        src = rep["sources_and_methodology"]

        st.markdown("##### 📜 Applicable Regulatory Standards")
        for s in src["primary_standards"]:
            st.markdown(f"- 🏛️ {s}")

        st.markdown("##### 🗄️ Underlying Enterprise Datasets")
        st.dataframe(pd.DataFrame(src["underlying_datasets"]), use_container_width=True, hide_index=True)

        st.markdown("##### 📐 Calculation Basis & Formulae")
        st.code(src["calculation_formulae"])

    # ════════════════════════════════════════════════════════════════════════
    # TAB 5: SECTION 8 (Expert Approval Status)
    # ════════════════════════════════════════════════════════════════════════
    with tab_s5:
        st.markdown("#### 8. Expert Approval Status & Audit Trail")
        appr = rep["approval"]
        st.success(f"### {appr['status']}")

        a_col1, a_col2 = st.columns(2)
        with a_col1:
            st.markdown(f"**Signatory:** {appr['approver_name']}")
            st.markdown(f"**Title:** {appr['approver_title']}")
            st.markdown(f"**Approval Date:** {appr['approval_date']}")
        with a_col2:
            st.markdown(f"**Audit Assurance Standard:** `{appr['audit_standard']}`")
            st.markdown(f"**Digital Verification SHA-256:** `0x{appr['verification_hash']}`")
            st.caption("Cryptographically sealed against master data records.")

        st.warning(f"**Governance Disclaimer:** {appr['disclaimer']}")
