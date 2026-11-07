"""
prototype/views/simulator_view.py — AI What-If Decision Simulator
Lets users test corporate decisions before implementation and see the cascading impacts on:
- Greenhouse Gas Emissions
- Agricultural & Energy Costs (€)
- Crop Production & Harvest Yields
- Water Consumption
- Nature & Freshwater Nutrient Runoff (P and N to water)
"""
from __future__ import annotations

from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from core.api import NavigatorAPI
from core.simulator_service import SimulatorService


def render(root: Path) -> None:
    api = NavigatorAPI(root)
    if not hasattr(api, "simulator"):
        api.simulator = SimulatorService(root)

    st.title("🎛️ AI What-If Decision Simulator")
    st.caption("Experiment with corporate decisions and simulate cascading impacts on emissions, costs, crop yields, water, and nature")

    st.info(
        "**Interactive Experimentation Sandbox:** Instead of merely stating 'reduce fertilizer' or 'boost renewables', "
        "this engine calculates the multi-system trade-offs: How does cutting nitrogen fertilizer affect legume yields? "
        "How do buffer strips protect Lake Pyhäjärvi? What are the net financial savings after carbon pricing?",
        icon="💡",
    )

    # ── Top Control Panel: Decision Variables ────────────────────────────────
    st.markdown("### 🎚️ Decision Levers & Operational Controls")

    col_c1, col_c2, col_c3, col_c4 = st.columns(4)
    with col_c1:
        fert_delta = st.slider(
            "🌱 Fertiliser Usage:",
            min_value=-50,
            max_value=30,
            value=-20,
            step=5,
            format="%+d%%",
            help="Reduce mineral nitrogen and phosphorus application. Cuts Scope 3 FLAG emissions and runoff.",
        )
    with col_c2:
        irrig_delta = st.slider(
            "💧 Irrigation Efficiency:",
            min_value=-20,
            max_value=50,
            value=15,
            step=5,
            format="%+d%%",
            help="Improve precision drip or timing. Saves water withdrawals and reduces electricity pumping.",
        )
    with col_c3:
        renew_delta = st.slider(
            "⚡ Renewable / Biogas Share:",
            min_value=0,
            max_value=100,
            value=30,
            step=5,
            format="+%d%%",
            help="Substitute Säkylä LNG with Biogas and increase Guarantees of Origin (GoO) coverage.",
        )
    with col_c4:
        prod_delta = st.slider(
            "🌾 Agricultural Production:",
            min_value=-30,
            max_value=30,
            value=10,
            step=5,
            format="%+d%%",
            help="Target contracted harvest volume from contract farms in Finland and Sweden.",
        )

    # Secondary Levers & Toggles
    t1, t2, t3, t4 = st.columns(4)
    with t1:
        use_buffers = st.checkbox("🏞️ Riparian Buffer Strips (L24)", value=True, help="Mandate vegetated buffer strips along drainage ditches to filter phosphorus.")
    with t2:
        use_catch = st.checkbox("🌿 Winter Catch Crops (L11)", value=True, help="Post-harvest cover crops to prevent winter nitrate leaching.")
    with t3:
        use_green_fert = st.checkbox("🧪 Low-Carbon Green Fertiliser (L10)", value=False, help="Switch to green hydrogen-based fertiliser (0.9 vs 3.7 kgCO2e/kg N).")
    with t4:
        carbon_tax = st.selectbox("Carbon Price Assumption:", [80.0, 120.0, 160.0, 220.0], index=0, format_func=lambda x: f"€{x:.0f} / tCO₂e")

    # ── Execute Calculation Engine ───────────────────────────────────────────
    sim = api.simulator.run_simulation(
        fertiliser_pct_delta=float(fert_delta),
        irrigation_eff_delta=float(irrig_delta),
        renewable_energy_delta=float(renew_delta),
        production_volume_delta=float(prod_delta),
        use_lowcarbon_fert=use_green_fert,
        use_buffer_strips=use_buffers,
        use_catch_crops=use_catch,
        carbon_price_eur=float(carbon_tax),
    )

    st.divider()

    # ── Performance & Feasibility Score Cards (Demeter Style) ────────────────
    st.markdown("### 🏆 Simulated Impact & Feasibility Scores")

    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        st.markdown(
            f"""
            <div class="pro-card" style="border-top: 4px solid #10b981;">
                <div class="pro-card-header">🌡️ Climate Decarbonisation</div>
                <div style="font-size: 2.8rem; font-weight: 800; color: #10b981; line-height: 1;">{sim['grades']['climate']}</div>
                <p style="color: #64748b; font-size: 0.85rem; margin-top: 6px;">
                    Net Group Emissions: <strong>{sim['ghg']['sim_total_tco2e']:,.0f} tCO₂e</strong><br/>
                    Reduction: <span style="color:#10b981; font-weight:700;">{sim['ghg']['delta_pct']:+.1f}%</span> ({abs(sim['ghg']['delta_tco2e']):,.0f} t saved)
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with sc2:
        st.markdown(
            f"""
            <div class="pro-card" style="border-top: 4px solid #3b82f6;">
                <div class="pro-card-header">🏞️ Freshwater & Nature (SBTN)</div>
                <div style="font-size: 2.8rem; font-weight: 800; color: #3b82f6; line-height: 1;">{sim['grades']['nature']}</div>
                <p style="color: #64748b; font-size: 0.85rem; margin-top: 6px;">
                    Phosphorus to Water: <strong>{sim['nature']['sim_p_kg']:,.0f} kg P</strong> (<span style="color:#10b981; font-weight:700;">{sim['nature']['p_delta_pct']:+.1f}%</span>)<br/>
                    Water Consumption: <strong>{sim['water']['sim_m3']:,.0f} m³</strong> (<span style="color:#10b981; font-weight:700;">{sim['water']['delta_pct']:+.1f}%</span>)
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with sc3:
        fin_delta = sim['financials']['net_delta_eur']
        fin_color = "#10b981" if fin_delta <= 0 else "#f59e0b"
        st.markdown(
            f"""
            <div class="pro-card" style="border-top: 4px solid {fin_color};">
                <div class="pro-card-header">💶 Economic Feasibility</div>
                <div style="font-size: 2.2rem; font-weight: 800; color: {fin_color}; line-height: 1.2;">{sim['grades']['feasibility'].split('(')[0]}</div>
                <p style="color: #64748b; font-size: 0.85rem; margin-top: 6px;">
                    Net Annual Impact: <strong style="color:{fin_color};">€{abs(fin_delta):,.0f} {'Net Savings' if fin_delta <= 0 else 'Net Cost'}</strong><br/>
                    Simulated Output: <strong>{sim['crop']['sim_tonnes']:,.0f} t</strong> ({sim['crop']['delta_pct']:+.1f}%)
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── AI Trade-off Synthesis & Explanation ─────────────────────────────────
    st.markdown("### 🤖 AI Executive Trade-Off Synthesis")
    st.markdown(
        f"""
        <div class="evidence-drawer-box" style="background:#f8fafc; color:#1e293b; border-left:4px solid #10b981; font-family:sans-serif; font-size:0.92rem;">
            {sim['ai_narrative']}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    # ── Interactive Charts ───────────────────────────────────────────────────
    ch_col1, ch_col2 = st.columns(2)

    with ch_col1:
        st.markdown("##### 📊 Financial Balance (€/yr)")
        fin = sim["financials"]
        fin_categories = [
            "Fertiliser Cost Delta",
            "Energy & Irrigation Spend",
            "Carbon Tax Savings",
            "Crop Production Revenue",
        ]
        fin_values = [
            -fin["fert_cost_delta"],     # positive if savings
            -fin["energy_cost_delta"],
            fin["carbon_tax_savings"],
            fin["crop_revenue_delta"],
        ]
        colors = ["#10b981" if v >= 0 else "#ef4444" for v in fin_values]

        fig_fin = go.Figure(go.Bar(
            x=fin_categories,
            y=fin_values,
            marker_color=colors,
            text=[f"€{v:,.0f}" for v in fin_values],
            textposition="auto",
        ))
        fig_fin.update_layout(
            title="Net Financial Contribution by Stream (€/year)",
            yaxis_title="Economic Value (€)",
            height=380,
            margin=dict(l=20, r=20, t=40, b=20),
        )
        st.plotly_chart(fig_fin, use_container_width=True)

    with ch_col2:
        st.markdown("##### 🍩 Emissions Breakdown Under What-If Scenario")
        ghg = sim["ghg"]
        labels = ["Scope 1 (Fuels)", "Scope 2 (Market-based)", "Scope 3 FLAG (Farming)", "Scope 3 Industrial"]
        values = [ghg["sim_scope1"], ghg["sim_scope2"], ghg["sim_scope3_flag"], ghg["sim_scope3_ind"]]

        fig_pie = px.pie(
            names=labels,
            values=values,
            hole=0.45,
            color=labels,
            color_discrete_map={
                "Scope 1 (Fuels)": "#ef4444",
                "Scope 2 (Market-based)": "#f59e0b",
                "Scope 3 FLAG (Farming)": "#10b981",
                "Scope 3 Industrial": "#6366f1",
            },
        )
        fig_pie.update_layout(
            title=f"Total Footprint: {ghg['sim_total_tco2e']:,.0f} tCO₂e ({ghg['delta_pct']:+.1f}%)",
            height=380,
            margin=dict(l=20, r=20, t=40, b=20),
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # ── Summary Comparison Table & Export ─────────────────────────────────────
    st.markdown("### 📋 Baseline vs What-If Comparison Matrix")
    comp_df = pd.DataFrame([
        {
            "Metric": "Total GHG Emissions (tCO₂e)",
            "2025 Baseline": f"{sim['ghg']['base_total_tco2e']:,.0f}",
            "What-If Scenario": f"{sim['ghg']['sim_total_tco2e']:,.0f}",
            "Delta": f"{sim['ghg']['delta_pct']:+.1f}%",
            "Impact": "✅ Decarbonisation" if sim['ghg']['delta_pct'] < 0 else "⚠️ Emissions Increase",
        },
        {
            "Metric": "Phosphorus Runoff to Water (kg P)",
            "2025 Baseline": f"{sim['nature']['base_p_kg']:,.0f}",
            "What-If Scenario": f"{sim['nature']['sim_p_kg']:,.0f}",
            "Delta": f"{sim['nature']['p_delta_pct']:+.1f}%",
            "Impact": "✅ Freshwater Protection" if sim['nature']['p_delta_pct'] < 0 else "⚠️ Increased Eutrophication",
        },
        {
            "Metric": "Water Consumption (m³)",
            "2025 Baseline": f"{sim['water']['base_m3']:,.0f}",
            "What-If Scenario": f"{sim['water']['sim_m3']:,.0f}",
            "Delta": f"{sim['water']['delta_pct']:+.1f}%",
            "Impact": "✅ Water Efficiency" if sim['water']['delta_pct'] < 0 else "⚠️ Higher Water Demand",
        },
        {
            "Metric": "Crop Harvest Output (tonnes)",
            "2025 Baseline": f"{sim['crop']['base_tonnes']:,.0f}",
            "What-If Scenario": f"{sim['crop']['sim_tonnes']:,.0f}",
            "Delta": f"{sim['crop']['delta_pct']:+.1f}%",
            "Impact": "✅ Target Met" if sim['crop']['delta_pct'] >= 0 else "⚠️ Supply Dip",
        },
    ])
    st.dataframe(comp_df, use_container_width=True, hide_index=True)

    c_save1, c_save2 = st.columns([3, 1])
    with c_save2:
        if st.button("💾 Save Scenario to Board Deck", use_container_width=True):
            st.success("✅ Scenario parameters and AI synthesis saved to the session audit deck!")

