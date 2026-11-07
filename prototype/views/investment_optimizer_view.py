"""
prototype/views/investment_optimizer_view.py — AI Sustainability Investment Optimiser
Connects sustainability investments with CFO capital allocation decisions:
- Multi-objective optimisation (Emissions, Adaptation, Nature, Financial Return, Feasibility)
- 10-Year Discounted Cash Flow (NPV @ 8% hurdle rate, IRR, Breakeven Year)
- Executive portfolio layout matching enterprise sustainability finance dashboards
"""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from core.api import NavigatorAPI
from core.investment_optimizer_service import InvestmentOptimizerService


def render(root: Path) -> None:
    api = NavigatorAPI(root)
    if not hasattr(api, "optimizer"):
        api.optimizer = InvestmentOptimizerService(root)

    # ── Page Header ───────────────────────────────────────────────────────────
    h_col1, h_col2 = st.columns([3, 1])
    with h_col1:
        st.title("💼 Sustainability Investment Optimiser")
        st.caption(
            "Multi-objective capital allocation engine connecting sustainability initiatives with "
            "CFO financial metrics (10-Yr NPV @ 8% hurdle rate, IRR, cash flow trajectory & payback)."
        )
    with h_col2:
        st.markdown(
            """
            <div style="text-align: right; padding-top: 20px;">
                <span class="pill-badge badge-approved">⚡ Multi-Objective Engine v1.0</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── Interactive Budget & Strategy Controller ──────────────────────────────
    with st.container():
        st.markdown(
            """
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px 20px; margin-bottom: 20px;">
            """,
            unsafe_allow_html=True,
        )
        ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([1.5, 1.4, 1.1])

        with ctrl_col1:
            budget = st.slider(
                "💶 Total Available Sustainability Budget:",
                min_value=20000,
                max_value=300000,
                value=100000,
                step=5000,
                format="€%d",
                help="Adjust the corporate sustainability capital budget to see how AI allocates it across initiatives.",
            )

        with ctrl_col2:
            strategy = st.selectbox(
                "🎯 Strategic Optimisation Priority:",
                [
                    "⚖️ Balanced Multi-Objective (Default)",
                    "🌿 Maximum Climate Abatement (Emissions First)",
                    "🌊 SBTN Nature & Freshwater First (Soil & Runoff)",
                    "💰 Highest Financial Return (Max 10-Yr NPV)",
                    "🛡️ Farm Climate Adaptation First (Drought & Heat)",
                    "⚙️ Custom Weights",
                ],
                index=0,
                help="Dictates how the multi-objective engine weighs conflicting priorities.",
            )

        with ctrl_col3:
            min_feas = st.slider(
                "🛡️ Min Feasibility Score:",
                min_value=0,
                max_value=90,
                value=70,
                step=5,
                format="%d%%",
                help="Filter out high-complexity initiatives that lack immediate operational or supplier readiness.",
            )

        # Custom Weights Expander
        weights = None
        if "Custom" in strategy:
            with st.expander("⚙️ Fine-Tune Multi-Objective Weights", expanded=True):
                w1, w2, w3, w4, w5 = st.columns(5)
                w_ghg = w1.slider("GHG Abatement", 0.0, 1.0, 0.25, 0.05)
                w_adapt = w2.slider("Climate Adaptation", 0.0, 1.0, 0.20, 0.05)
                w_nat = w3.slider("SBTN Nature", 0.0, 1.0, 0.20, 0.05)
                w_fin = w4.slider("Financial Return", 0.0, 1.0, 0.25, 0.05)
                w_feas = w5.slider("Feasibility", 0.0, 1.0, 0.10, 0.05)
                weights = {
                    "emissions": w_ghg,
                    "adaptation": w_adapt,
                    "nature": w_nat,
                    "financial": w_fin,
                    "feasibility": w_feas,
                }
        elif "Emissions" in strategy:
            weights = {"emissions": 0.50, "adaptation": 0.10, "nature": 0.10, "financial": 0.20, "feasibility": 0.10}
        elif "Nature" in strategy:
            weights = {"emissions": 0.15, "adaptation": 0.15, "nature": 0.45, "financial": 0.15, "feasibility": 0.10}
        elif "Financial" in strategy:
            weights = {"emissions": 0.10, "adaptation": 0.10, "nature": 0.10, "financial": 0.60, "feasibility": 0.10}
        elif "Adaptation" in strategy:
            weights = {"emissions": 0.15, "adaptation": 0.45, "nature": 0.20, "financial": 0.10, "feasibility": 0.10}

        st.markdown("</div>", unsafe_allow_html=True)

    # ── Run Multi-Objective Optimisation ─────────────────────────────────────
    res = api.optimizer.optimize_portfolio(
        budget=float(budget),
        weights=weights,
        min_feasibility=float(min_feas),
    )

    allocated_items = res["allocated_initiatives"]

    # ── Top 4 Executive Metric Cards ─────────────────────────────────────────
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)

    with m_col1:
        st.markdown(
            f"""
            <div class="pro-card" style="padding: 16px 20px;">
                <div style="font-size: 0.72rem; color: #64748b; font-weight: 700; text-transform: uppercase;">Allocated Investment</div>
                <div style="font-size: 1.85rem; font-weight: 900; color: #0f172a; margin: 4px 0;">€{res['allocated_capex']:,.0f}</div>
                <div style="font-size: 0.76rem; color: #059669; font-weight: 600;">{len(allocated_items)} initiatives funded · €{res['unallocated_reserve']:,.0f} reserve</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with m_col2:
        st.markdown(
            f"""
            <div class="pro-card" style="padding: 16px 20px;">
                <div style="font-size: 0.72rem; color: #64748b; font-weight: 700; text-transform: uppercase;">Internal Rate of Return (IRR)</div>
                <div style="font-size: 1.85rem; font-weight: 900; color: #0284c7; margin: 4px 0;">{res['irr_pct']:.1f}%</div>
                <div style="font-size: 0.76rem; color: #64748b; font-weight: 600;">{res['hurdle_rate_multiple']}x hurdle rate (8% baseline)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with m_col3:
        b_year = f"Year {res['breakeven_year']}" if isinstance(res['breakeven_year'], (int, float)) else str(res['breakeven_year'])
        st.markdown(
            f"""
            <div class="pro-card" style="padding: 16px 20px;">
                <div style="font-size: 0.72rem; color: #64748b; font-weight: 700; text-transform: uppercase;">Capital Payback Period</div>
                <div style="font-size: 1.85rem; font-weight: 900; color: #10b981; margin: 4px 0;">{b_year}</div>
                <div style="font-size: 0.76rem; color: #64748b; font-weight: 600;">Cumulative breakeven milestone</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with m_col4:
        st.markdown(
            f"""
            <div class="pro-card" style="padding: 16px 20px;">
                <div style="font-size: 0.72rem; color: #64748b; font-weight: 700; text-transform: uppercase;">Annual OPEX Savings</div>
                <div style="font-size: 1.85rem; font-weight: 900; color: #7c3aed; margin: 4px 0;">€{res['total_annual_savings']:,.0f}/yr</div>
                <div style="font-size: 0.76rem; color: #059669; font-weight: 600;">+{res['total_ghg_abated_tco2e']:,.0f} tCO₂e/yr permanent cut</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # ── Hero Split: Core Value Benchmark (Left) & Cumulative Cash Flow (Right) ─
    hero_col1, hero_col2 = st.columns([1.1, 1.9])

    with hero_col1:
        st.markdown(
            f"""
            <div style="background: linear-gradient(145deg, #059669 0%, #0d9488 100%); border-radius: 12px; padding: 24px 22px; color: #ffffff; min-height: 330px; box-shadow: 0 10px 25px rgba(5, 150, 105, 0.25); display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <span style="font-size: 0.80rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; opacity: 0.90;">Core Value Benchmark</span>
                        <span style="background: rgba(255,255,255,0.22); color: #ffffff; font-size: 0.65rem; font-weight: 800; border-radius: 12px; padding: 2px 8px; letter-spacing: 0.05em;">NET PRESENT VALUE</span>
                    </div>
                    <div style="font-size: 2.85rem; font-weight: 900; line-height: 1.05; margin: 8px 0 14px 0;">
                        €{res['npv_10y']:,.0f}
                    </div>
                    <p style="font-size: 0.82rem; line-height: 1.6; opacity: 0.92; margin-bottom: 0;">
                        Net Present Value (NPV) represents the present value of all cash outflows and operational savings generated over a 10-year transition timeline, discounted at an annual hurdle rate of <b>8%</b>.
                    </p>
                </div>
                <div style="padding-top: 18px; border-top: 1px solid rgba(255,255,255,0.22); display: flex; justify-content: space-between; font-size: 0.78rem;">
                    <span><b>Hurdle Rate:</b> 8.0%</span>
                    <span><b>EU ETS Shadow:</b> €85/t</span>
                    <span><b>Horizon:</b> 10 Yrs</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with hero_col2:
        st.markdown("##### 📈 Cumulative Cash Flow (10-Year Trajectory)")
        traj_df = pd.DataFrame(res["trajectory"])

        fig_traj = go.Figure()

        # Shaded area under cumulative curve
        fig_traj.add_trace(
            go.Scatter(
                x=traj_df["year"],
                y=traj_df["cumulative_cash_flow"],
                mode="lines+markers",
                name="Cumulative Cash Flow (€)",
                line=dict(color="#059669", width=3.5, shape="spline"),
                marker=dict(size=7, color="#059669"),
                fill="tozeroy",
                fillcolor="rgba(16, 185, 129, 0.12)",
                hovertemplate="<b>Year %{x}</b><br>Cumulative Cash: <b>€%{y:,.0f}</b><extra></extra>",
            )
        )

        # Baseline zero break-even line
        fig_traj.add_hline(
            y=0,
            line_dash="dot",
            line_color="#94a3b8",
            annotation_text="Breakeven Threshold (€0)",
            annotation_position="bottom right",
            annotation_font_size=10,
        )

        # Breakeven point annotation if reached
        if isinstance(res["breakeven_year"], (int, float)):
            fig_traj.add_annotation(
                x=res["breakeven_year"],
                y=0,
                text=f"Breakeven: Yr {res['breakeven_year']}",
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                arrowcolor="#0f172a",
                ax=0,
                ay=-35,
                font=dict(size=11, color="#ffffff"),
                bgcolor="#0f172a",
                borderpad=4,
                bordercolor="#334155",
            )

        fig_traj.update_layout(
            height=330,
            margin=dict(l=20, r=20, t=15, b=20),
            xaxis=dict(title="Year", tickmode="linear", tick0=0, dtick=1, gridcolor="#f1f5f9"),
            yaxis=dict(title="€ (EUR)", tickformat=",.0f", gridcolor="#f1f5f9"),
            plot_bgcolor="#ffffff",
            paper_bgcolor="#ffffff",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig_traj, use_container_width=True)

    # ── 5 Tab Navigation: Matches Enterprise Dashboard ───────────────────────
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    tab_exec, tab_deep, tab_whatif, tab_inaction, tab_calc = st.tabs([
        "📑 Executive Summary",
        "🔍 Deep Dive Initiatives",
        "🎛️ What-If Playground",
        "⚠️ Cost of Inaction",
        "🧮 Calculations & Governance",
    ])

    # ════════════════════════════════════════════════════════════════════════
    # TAB 1: Executive Summary
    # ════════════════════════════════════════════════════════════════════════
    with tab_exec:
        st.markdown("#### 🎯 Recommended Portfolio Allocation")
        st.caption(f"Engine allocated **€{res['allocated_capex']:,.0f}** across **{len(allocated_items)} high-impact levers** for budget €{budget:,.0f}.")

        # Table of allocated initiatives
        table_rows = []
        for a in allocated_items:
            table_rows.append({
                "Action / Initiative": a["title"],
                "Category": a["category"],
                "Investment (€)": f"€{a['allocated_investment']:,.0f}",
                "Funding": f"{a['funding_pct']:.0f}%",
                "Expected Benefit": a["primary_benefit"],
                "GHG Abatement": f"{a['ghg_abatement_tco2e']:,.0f} tCO₂e/yr",
                "Water Saved": f"{a['water_saved_m3']:,.0f} m³/yr",
                "Annual Savings": f"€{a['annual_opex_savings']:,.0f}/yr",
                "Feasibility": f"{a['feasibility_score']:.0f}%",
            })

        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

        # Multi-Objective Radar Chart
        st.markdown("##### 🕸️ Multi-Objective Performance Profile")
        radar_cats = ["Emissions Abatement", "Climate Adaptation", "SBTN Nature Benefit", "Financial Return (NPV)", "Operational Feasibility"]
        
        # Portfolio aggregate scores normalized to 100
        ghg_norm = min(100.0, (res["total_ghg_abated_tco2e"] / 600.0) * 100.0)
        adapt_norm = float(np.mean([a["adaptation_score"] for a in allocated_items])) if allocated_items else 0.0
        nat_norm = float(np.mean([a["nature_score"] for a in allocated_items])) if allocated_items else 0.0
        fin_norm = min(100.0, (res["npv_10y"] / max(res["allocated_capex"] * 2.0, 1.0)) * 100.0)
        feas_norm = res["avg_feasibility"]

        fig_radar = go.Figure()
        fig_radar.add_trace(
            go.Scatterpolar(
                r=[ghg_norm, adapt_norm, nat_norm, fin_norm, feas_norm, ghg_norm],
                theta=radar_cats + [radar_cats[0]],
                fill="toself",
                name="Optimised Portfolio",
                line=dict(color="#059669", width=2.5),
                fillcolor="rgba(5, 150, 105, 0.25)",
            )
        )
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100], gridcolor="#e2e8f0"),
                bgcolor="#f8fafc",
            ),
            height=320,
            margin=dict(l=40, r=40, t=20, b=20),
            showlegend=False,
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    # ════════════════════════════════════════════════════════════════════════
    # TAB 2: Deep Dive Initiatives
    # ════════════════════════════════════════════════════════════════════════
    with tab_deep:
        st.markdown("#### 🔬 Comprehensive Lever-by-Lever Breakdown")
        for a in allocated_items:
            with st.expander(f"📌 {a['title']} — Allocated: €{a['allocated_investment']:,.0f} ({a['funding_pct']:.0f}% funded)", expanded=True):
                d_c1, d_c2, d_c3, d_c4 = st.columns(4)
                d_c1.metric("Annual Cost Savings", f"€{a['annual_opex_savings']:,.0f}/yr")
                d_c2.metric("GHG Reduction", f"{a['ghg_abatement_tco2e']:,.0f} tCO₂e/yr")
                d_c3.metric("Water Conserved", f"{a['water_saved_m3']:,.0f} m³/yr")
                d_c4.metric("P-Loss Prevented", f"{a['p_loss_prevented_kg']:,.0f} kg P/yr")

                st.markdown(f"**Mechanism & Scope:** {a['mechanism']}")
                st.caption(f"Primary Benefit: {a['primary_benefit']} · Feasibility Readiness: {a['feasibility_score']:.0f}%")

    # ════════════════════════════════════════════════════════════════════════
    # TAB 3: What-If Playground
    # ════════════════════════════════════════════════════════════════════════
    with tab_whatif:
        st.markdown("#### 🎛️ Capital Scaling Sensitivity Frontier")
        st.caption("Inspect how returns scale across different budget levels (€20k to €250k). Notice diminishing marginal returns and efficiency thresholds.")

        curve_df = api.optimizer.get_budget_sensitivity_curve()

        fig_curve = go.Figure()
        fig_curve.add_trace(
            go.Scatter(
                x=curve_df["budget_eur"],
                y=curve_df["npv_10y_eur"],
                name="10-Yr NPV (€)",
                mode="lines+markers",
                line=dict(color="#059669", width=3),
                yaxis="y1",
            )
        )
        fig_curve.add_trace(
            go.Scatter(
                x=curve_df["budget_eur"],
                y=curve_df["ghg_abated_tco2e"],
                name="GHG Abatement (tCO₂e/yr)",
                mode="lines+markers",
                line=dict(color="#0284c7", width=2.5, dash="dash"),
                yaxis="y2",
            )
        )
        fig_curve.update_layout(
            height=350,
            margin=dict(l=20, r=20, t=30, b=20),
            xaxis=dict(title="Available Budget (€)", tickformat=",.0f"),
            yaxis=dict(title=dict(text="10-Year NPV (€)", font=dict(color="#059669")), tickformat=",.0f"),
            yaxis2=dict(title=dict(text="Annual GHG Abatement (tCO₂e)", font=dict(color="#0284c7")), overlaying="y", side="right"),
            plot_bgcolor="#f8fafc",
            paper_bgcolor="#ffffff",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig_curve, use_container_width=True)

    # ════════════════════════════════════════════════════════════════════════
    # TAB 4: Cost of Inaction
    # ════════════════════════════════════════════════════════════════════════
    with tab_inaction:
        st.markdown("#### ⚠️ Business & Climate Cost of Inaction (€0 Invested)")
        inaction = res["cost_of_inaction"]
        
        i_c1, i_c2, i_c3 = st.columns(3)
        with i_c1:
            st.markdown(
                f"""
                <div class="pro-card" style="padding: 16px; border-top: 3px solid #ef4444;">
                    <div style="font-size: 0.72rem; color: #64748b; font-weight: 700;">10-Year Inaction Penalty</div>
                    <div style="font-size: 1.8rem; font-weight: 800; color: #ef4444; margin: 4px 0;">€{inaction['ten_yr_financial_penalty_eur']:,.0f}</div>
                    <div style="font-size: 0.75rem; color: #64748b;">Cumulative lost energy & input efficiency</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with i_c2:
            st.markdown(
                f"""
                <div class="pro-card" style="padding: 16px; border-top: 3px solid #f59e0b;">
                    <div style="font-size: 0.72rem; color: #64748b; font-weight: 700;">Crop Yield Loss Exposure</div>
                    <div style="font-size: 1.8rem; font-weight: 800; color: #f59e0b; margin: 4px 0;">-{inaction['lost_crop_yield_tha']} t/ha</div>
                    <div style="font-size: 0.75rem; color: #64748b;">Drought vulnerability on unmitigated farms</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with i_c3:
            st.markdown(
                f"""
                <div class="pro-card" style="padding: 16px; border-top: 3px solid #6366f1;">
                    <div style="font-size: 0.72rem; color: #64748b; font-weight: 700;">Carbon Tax Exposure</div>
                    <div style="font-size: 1.8rem; font-weight: 800; color: #6366f1; margin: 4px 0;">€{inaction['cumulative_carbon_tax_exposure_eur']:,.0f}</div>
                    <div style="font-size: 0.75rem; color: #64748b;">Unhedged ETS liability @ €85/t</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.warning(f"**Freshwater Watershed Warning:** {inaction['sbtn_freshwater_risk']}")

    # ════════════════════════════════════════════════════════════════════════
    # TAB 5: Calculations & Governance
    # ════════════════════════════════════════════════════════════════════════
    with tab_calc:
        st.markdown("#### 🧮 Financial & Agronomic Calculation Methodology")
        st.markdown(
            """
            - **Discount Rate (Hurdle Rate):** Fixed at `8.0%` nominal WACC per corporate capital governance standards.
            - **Carbon Shadow Price:** `€85.00/tCO₂e` based on EU ETS trailing 12-month forward curve, escalating at `3.0%/yr`.
            - **NPV Formula:** $\\text{NPV} = -I_0 + \\sum_{t=1}^{10} \\frac{\\text{Annual Savings}_t + \\text{Carbon Tax Avoidance}_t}{(1 + 0.08)^t}$
            - **IRR:** Evaluated via root-finding bisection solving $\\text{NPV}(r) = 0$.
            - **Multi-Objective Optimization:** Greedy-density knapsack ranking by composite utility score per euro invested.
            - **Audit Guardrail:** 100% deterministic code calculations. Zero AI hallucinations.
            """
        )

    # ── Bottom Row: NPV Waterfall & Biggest Value Drivers (Matches Photo) ──────
    st.divider()
    b_col1, b_col2 = st.columns([1.6, 1.0])

    with b_col1:
        st.markdown("##### 🌊 NPV Waterfall (10-Year Value Build-Up)")
        wf = res["waterfall"]

        fig_wf = go.Figure(
            go.Waterfall(
                name="NPV Waterfall",
                orientation="v",
                measure=["relative", "relative", "relative", "relative", "relative", "relative", "total"],
                x=[
                    "Initial Outflow",
                    "Energy Savings",
                    "Input Reductions",
                    "Carbon Avoidance",
                    "Yield Protected",
                    "ESG Subsidies",
                    "Net Present Value",
                ],
                textposition="outside",
                text=[
                    f"€{wf['initial_investment']:,.0f}",
                    f"+€{wf['energy_fuel_savings']:,.0f}",
                    f"+€{wf['input_cost_cuts']:,.0f}",
                    f"+€{wf['carbon_avoidance']:,.0f}",
                    f"+€{wf['yield_protection']:,.0f}",
                    f"+€{wf['esg_subsidies']:,.0f}",
                    f"€{wf['net_present_value']:,.0f}",
                ],
                y=[
                    wf["initial_investment"],
                    wf["energy_fuel_savings"],
                    wf["input_cost_cuts"],
                    wf["carbon_avoidance"],
                    wf["yield_protection"],
                    wf["esg_subsidies"],
                    wf["net_present_value"],
                ],
                connector={"line": {"color": "#94a3b8"}},
                decreasing={"marker": {"color": "#ef4444"}},
                increasing={"marker": {"color": "#10b981"}},
                totals={"marker": {"color": "#059669"}},
            )
        )
        fig_wf.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=30, b=20),
            yaxis_title="€ (EUR)",
            plot_bgcolor="#f8fafc",
            paper_bgcolor="#ffffff",
        )
        st.plotly_chart(fig_wf, use_container_width=True)

    with b_col2:
        st.markdown("##### 🏆 Biggest Value Drivers (Largest Contributors to NPV)")
        for d in res["drivers"]:
            st.markdown(
                f"""
                <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:8px; padding:10px 14px; margin-bottom:8px;">
                    <div style="display:flex; justify-content:space-between; font-size:0.85rem; font-weight:700; color:#0f172a;">
                        <span>{d['driver']}</span>
                        <span style="color:#059669;">€{d['amount_eur']:,.0f}</span>
                    </div>
                    <div style="display:flex; align-items:center; gap:8px; margin-top:6px;">
                        <div style="flex:1; background:#e2e8f0; height:6px; border-radius:3px;">
                            <div style="width:{d['share_pct']}%; background:#059669; height:6px; border-radius:3px;"></div>
                        </div>
                        <span style="font-size:0.75rem; color:#64748b; font-weight:600;">{d['share_pct']:.0f}%</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ── Strategic AI Synthesis & Export Action ─────────────────────────────────
    st.markdown("### 🤖 Strategic Investment Advisor Memo")
    st.markdown(
        f"""
        <div class="evidence-drawer-box" style="background:#f0fdf4; border-left:4px solid #059669; font-size:0.92rem; line-height:1.65; color:#1e293b;">
            {res['ai_memo'].replace('\\n', '<br/>')}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Export Button
    exp_c1, exp_c2 = st.columns([3, 1])
    with exp_c2:
        memo_text = res["ai_memo"].replace("\\n", "\n")
        # Pure-python markdown table generator (zero dependency risk)
        if table_rows:
            headers = list(table_rows[0].keys())
            table_md = "| " + " | ".join(headers) + " |\n"
            table_md += "| " + " | ".join(["---"] * len(headers)) + " |\n"
            for row in table_rows:
                table_md += "| " + " | ".join(str(row.get(h, "")) for h in headers) + " |\n"
        else:
            table_md = "*No initiatives allocated.*"

        export_md = (
            f"# Apetit Sustainability Capital Investment Allocation Report\n\n"
            f"**Total Budget:** €{budget:,.0f} | **Allocated Investment:** €{res['allocated_capex']:,.0f}\n"
            f"**10-Year Net Present Value (NPV @ 8%):** €{res['npv_10y']:,.0f}\n"
            f"**Internal Rate of Return (IRR):** {res['irr_pct']:.1f}% | **Breakeven Year:** {res['breakeven_year']}\n\n"
            f"---\n\n{memo_text}\n\n---\n"
            f"## Funded Initiatives Table\n\n"
            f"{table_md}\n\n---\n*Synthetic data calibration only — deterministic audit compliant*"
        )
        st.download_button(
            "📄 Export Capital Allocation Brief (.md)",
            export_md,
            file_name=f"apetit_investment_allocation_{budget:.0f}.md",
            mime="text/markdown",
            use_container_width=True,
        )

