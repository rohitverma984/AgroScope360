"""
views/pathways.py — Track B: Decarbonisation Pathways, MACC, & Expert Sign-off

Covers:
- Marginal Abatement Cost Curve (MACC) across Decarbonisation Levers (L01-L28)
- Distinction: Physical Abatement vs Structural Boundary Events vs Measurement Improvements (L27)
- Transition Scenarios (NGFS-consistent: Net Zero 2050, Delayed, Fragmented)
- Human-in-the-Loop Expert Review & Approval Workflow
Data sources:
- data/05_scenarios/decarbonisation_levers.csv
- data/05_scenarios/transition_scenarios.csv
- data/05_scenarios/structural_events.csv
"""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st


@st.cache_data(show_spinner="Loading decarbonisation levers and scenarios …")
def _load_data(root: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    levers = pd.read_csv(root / "data" / "05_scenarios" / "decarbonisation_levers.csv")
    scenarios = pd.read_csv(root / "data" / "05_scenarios" / "transition_scenarios.csv")
    events = pd.read_csv(root / "data" / "05_scenarios" / "structural_events.csv")
    return levers, scenarios, events


def render(root: Path) -> None:
    st.title("🛣️ Decarbonisation Pathways & MACC")
    st.caption("⚠️ Synthetic estimates only — SBTi-aligned pathways & transition scenarios")

    st.info(
        "**Pathways & Abatement Architecture:** Integrates corporate Scope 1-3 decarbonisation levers with "
        "NGFS transition scenarios. "
        "Strictly distinguishes **Physical Abatement** from **Structural Boundary Events** (acquisitions/divestments) "
        "and **Measurement Improvements** (L27). "
        "Requires human expert sign-off before recommendations are marked final.",
        icon="🛣️",
    )

    try:
        levers_df, scenarios_df, events_df = _load_data(root)
    except Exception as exc:
        st.error(f"Error loading pathway data: {exc}")
        return

    # Initialize session state for expert reviews if not present
    if "lever_approvals" not in st.session_state:
        st.session_state.lever_approvals = {
            row["lever_id"]: {"status": "Pending", "reviewer": "Unassigned", "notes": ""}
            for _, row in levers_df.iterrows()
        }

    # ── Headline KPIs ────────────────────────────────────────────────────────
    total_levers = len(levers_df)
    total_abatement = levers_df["abatement_tco2e_2030_design"].sum()
    flag_abatement = levers_df[levers_df["flag"] == True]["abatement_tco2e_2030_design"].sum()
    approved_count = sum(1 for v in st.session_state.lever_approvals.values() if v["status"] == "Approved")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Catalog Levers", total_levers)
    col2.metric("2030 Abatement Potential", f"{total_abatement:,.0f} tCO₂e/yr")
    col3.metric("FLAG Abatement Share", f"{(flag_abatement/total_abatement)*100:.1f}%")
    col4.metric("Expert Sign-Offs", f"{approved_count} / {total_levers} Approved")

    st.divider()

    # ── Tabs ────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Marginal Abatement Cost Curve (MACC)",
        "🏛️ Structural Events vs Levers",
        "🔮 Transition Scenarios & Prices",
        "✍️ Expert Review & Approval",
    ])

    with tab1:
        st.markdown("#### Marginal Abatement Cost Curve (MACC 2030)")
        st.caption("Levers ordered from lowest (cost-negative / net savings) to highest marginal cost per tCO₂e abated.")

        # Filter out measurement improvements from MACC (e.g. L27 is measurement only)
        macc_df = levers_df.copy()
        macc_df["is_measurement_only"] = macc_df["lever_id"] == "L27"
        macc_plot = macc_df[~macc_df["is_measurement_only"]].sort_values("indicative_cost_eur_per_tco2e").reset_index(drop=True)

        macc_plot["cumulative_abatement"] = macc_plot["abatement_tco2e_2030_design"].cumsum()
        macc_plot["x_mid"] = macc_plot["cumulative_abatement"] - (macc_plot["abatement_tco2e_2030_design"] / 2)

        try:
            import plotly.graph_objects as go  # noqa: PLC0415
            fig = go.Figure()

            # Bars for each lever
            for _, r in macc_plot.iterrows():
                color = "#2ecc71" if r["indicative_cost_eur_per_tco2e"] < 0 else (
                    "#3498db" if r["flag"] else "#e67e22"
                )
                fig.add_trace(go.Bar(
                    name=f"{r['lever_id']}: {r['name'][:30]}...",
                    x=[r["abatement_tco2e_2030_design"]],
                    y=[r["indicative_cost_eur_per_tco2e"]],
                    orientation="v",
                    width=[r["abatement_tco2e_2030_design"]],
                    marker=dict(color=color),
                    hovertext=f"<b>{r['lever_id']}: {r['name']}</b><br>"
                              f"Scope: {r['scope']} (FLAG: {r['flag']})<br>"
                              f"Abatement: {r['abatement_tco2e_2030_design']:,.0f} tCO2e/yr<br>"
                              f"Cost: €{r['indicative_cost_eur_per_tco2e']:.1f}/tCO2e<br>"
                              f"Capex: €{r['capex_eur']:,.0f}",
                    hoverinfo="text",
                ))

            fig.add_hline(y=0, line_dash="solid", line_color="black", line_width=1)
            fig.update_layout(
                title="Marginal Abatement Cost Curve (€/tCO₂e vs Abatement)",
                xaxis_title="Abatement Potential (tCO₂e/yr in 2030)",
                yaxis_title="Net Cost (€ / tCO₂e abated)",
                showlegend=False,
                height=450,
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception:
            st.bar_chart(macc_plot.set_index("lever_id")["indicative_cost_eur_per_tco2e"])

        # Display table
        cols = ["lever_id", "name", "scope", "flag", "abatement_tco2e_2030_design", "indicative_cost_eur_per_tco2e", "capex_eur", "confidence"]
        st.dataframe(macc_plot[cols], use_container_width=True, hide_index=True)

    with tab2:
        st.markdown("#### Governance: Physical Reductions vs Structural Events vs Accounting")
        st.warning(
            "⚠️ **Critical Methodology Guardrail:** Mergers, acquisitions, divestments, and soil sampling "
            "do NOT count as physical decarbonisation abatement. They trigger SBTi base-year recalculations "
            "or improve inventory certainty.",
            icon="🛡️",
        )

        st.markdown("##### 1. Structural Boundary Events")
        st.caption("Events impacting corporate boundaries and requiring baseline recalculation (Task B1):")
        st.dataframe(events_df, use_container_width=True, hide_index=True)

        st.markdown("##### 2. Accounting & Measurement Levers (Non-Physical Abatement)")
        st.markdown(
            "- **Lever L27 (Contract-farm soil carbon & peat sampling campaign):** "
            "Abatement is 0 tCO₂e physically. This lever replaces the default mineral soil assumption with verified "
            "sampling, preventing misreporting and unlocking targeted water/peatland management."
        )

    with tab3:
        st.markdown("#### NGFS-Consistent Transition Scenarios")
        scenario_names = scenarios_df["scenario"].unique().tolist()
        sel_scen = st.selectbox("Select Scenario to inspect price trajectories:", scenario_names)
        scen_sub = scenarios_df[scenarios_df["scenario"] == sel_scen]

        st.dataframe(scen_sub, use_container_width=True, hide_index=True)

        try:
            import plotly.express as px  # noqa: PLC0415
            fig2 = px.line(
                scenarios_df,
                x="year",
                y="carbon_price_eur_t",
                color="scenario",
                markers=True,
                title="Carbon Price Projections across Scenarios (€/t)",
            )
            st.plotly_chart(fig2, use_container_width=True)
        except Exception:
            pass

    with tab4:
        st.markdown("#### Expert Review & Sign-Off Workflow")
        st.caption("Apetit sustainability governance requires documented sign-off before recommendations are operationalized.")

        selected_id = st.selectbox("Select Lever to Review:", levers_df["lever_id"].tolist())
        lever_info = levers_df[levers_df["lever_id"] == selected_id].iloc[0]

        curr_state = st.session_state.lever_approvals.get(selected_id, {"status": "Pending", "reviewer": "", "notes": ""})

        with st.form(key=f"review_form_{selected_id}"):
            st.markdown(f"**Lever:** `{lever_info['lever_id']}` — **{lever_info['name']}**")
            st.markdown(f"**Abatement:** {lever_info['abatement_tco2e_2030_design']:,.0f} tCO₂e | **Cost:** €{lever_info['indicative_cost_eur_per_tco2e']}/t")

            c_rev1, c_rev2 = st.columns(2)
            new_status = c_rev1.selectbox("Decision Status", ["Pending", "Approved", "Flagged for Audit"], index=["Pending", "Approved", "Flagged for Audit"].index(curr_state["status"]))
            reviewer_name = c_rev2.text_input("Reviewer Name / Title", value=curr_state["reviewer"] if curr_state["reviewer"] != "Unassigned" else "Sustainability Lead")
            review_notes = st.text_area("Review Comments / Audit Justification", value=curr_state["notes"])

            submitted = st.form_submit_button("Save Review Decision")
            if submitted:
                st.session_state.lever_approvals[selected_id] = {
                    "status": new_status,
                    "reviewer": reviewer_name,
                    "notes": review_notes,
                }
                st.success(f"Updated status for {selected_id} to {new_status}!")
                st.rerun()

        # Display current review audit log
        st.markdown("##### 📋 Current Sign-Off Audit Log")
        review_summary = []
        for lid, info in st.session_state.lever_approvals.items():
            review_summary.append({
                "Lever ID": lid,
                "Status": info["status"],
                "Reviewer": info["reviewer"],
                "Notes": info["notes"],
            })
        st.dataframe(pd.DataFrame(review_summary), use_container_width=True, hide_index=True)

