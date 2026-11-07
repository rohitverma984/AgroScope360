"""
prototype/views/inventory.py — Track A: Auditable GHG Inventory & Anomaly Detection
"""
from __future__ import annotations

from pathlib import Path
import pandas as pd
import streamlit as st

from core.api import NavigatorAPI


def render(root: Path) -> None:
    api = NavigatorAPI(root)

    st.title("📊 Auditable GHG Inventory (Scopes 1–3)")
    st.caption("Track A: Corporate GHG Protocol accounting with raw-feed anomaly detection and audit evidence")

    # ── Top Controls ────────────────────────────────────────────────────────
    col1, col2 = st.columns([1, 3])
    with col1:
        selected_year = st.selectbox("Reporting Year:", [2025, 2024, 2023], index=0)
    with col2:
        st.info(
            f"**Methodology:** GHG Protocol Corporate Standard · IPCC AR6 GWP100 (N₂O 273, fossil CH₄ 29.8) · "
            f"Deterministic execution via `reference_calculator.py`. Showing reporting year **{selected_year}**.",
            icon="ℹ️",
        )

    with st.spinner("Computing corporate emissions inventory …"):
        inv, summary = api.inventory.get_inventory(selected_year)
        kpis = api.inventory.get_kpis(selected_year)

    # ── Metric Tiles ─────────────────────────────────────────────────────────
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Group Gross Total", f"{kpis['total_market']:,.0f} tCO₂e", "Scope 1 + 2m + 3")
    m2.metric("Scope 1 (Direct)", f"{kpis['scope1']:,.0f} tCO₂e", "Combustion & refrigerants")
    m3.metric("Scope 2 (Market-based)", f"{kpis['scope2_market']:,.0f} tCO₂e", f"Loc-based: {kpis['scope2_location']:,.0f} t")
    m4.metric("Scope 3 (Value Chain)", f"{kpis['scope3']:,.0f} tCO₂e", "Purchases & transport")
    m5.metric("FLAG Land Share", f"{(kpis['flag_emissions'] / kpis['total_market']) * 100:.1f}%", f"{kpis['flag_emissions']:,.0f} tCO₂e")

    st.divider()

    # ── Detailed Tabs ────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Executive Scope Summary",
        "🔍 Line Items & Provenance",
        "⚠️ Raw Feed Quality Anomalies",
        "📐 Dev Benchmark Validation",
    ])

    with tab1:
        st.markdown("#### Emissions by Scope & Standard Category")
        scope_labels = {
            "scope1": "Scope 1 (Combustion & Refrigerants)",
            "scope2_location": "Scope 2 Location-based (Grid Average)",
            "scope2_market": "Scope 2 Market-based (Residual Mix - GoO)",
            "scope3": "Scope 3 (Value Chain)",
        }
        
        display_rows = []
        for s in ["scope1", "scope2_location", "scope2_market", "scope3"]:
            sub = summary[summary["scope"] == s]
            for _, r in sub.iterrows():
                display_rows.append({
                    "Scope": scope_labels.get(s, s),
                    "Category": str(r.get("category", "")).replace("_", " ").title(),
                    "Emissions (tCO₂e)": round(r["tco2e"], 1),
                    "Share (%)": f"{(r['tco2e'] / kpis['total_market']) * 100:.1f}%" if kpis["total_market"] > 0 else "0%",
                })
        
        df_disp = pd.DataFrame(display_rows)
        st.dataframe(df_disp, use_container_width=True, hide_index=True)

        try:
            import plotly.express as px  # noqa: PLC0415
            fig = px.pie(
                df_disp[df_disp["Scope"] != "Scope 2 Location-based (Grid Average)"],
                values="Emissions (tCO₂e)",
                names="Category",
                title=f"Emissions Distribution by Category ({selected_year})",
                hole=0.4,
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        except Exception:
            pass

    with tab2:
        st.markdown("#### Audit Line Items & Calculation Basis")
        st.caption("Every number in the group total originates from a specific activity record and emission factor.")

        show_cols = [c for c in ["scope", "category", "line_item", "tco2e", "basis"] if c in inv.columns]
        st.dataframe(inv[show_cols].sort_values("tco2e", ascending=False).reset_index(drop=True), use_container_width=True, hide_index=True)

        # Drilldown selector
        st.markdown("---")
        st.markdown("##### 🔎 Record Provenance Inspector")
        cats = sorted(inv["category"].dropna().unique().tolist())
        sel_c = st.selectbox("Select Category to view calculation basis:", cats)
        sub_items = inv[inv["category"] == sel_c]
        
        st.markdown(
            f"""
            <div class="evidence-drawer-box">
CATEGORY: {sel_c}
TOTAL EMISSIONS: {sub_items['tco2e'].sum():,.2f} tCO2e
RECORDS AGGREGATED: {len(sub_items)} lines
CALCULATION BASIS:
{chr(10).join('  • ' + str(b) for b in sub_items['basis'].unique() if b)}

EMISSION FACTOR SOURCE:
  • Reference: data/01_master/emission_factor_library.csv
  • Factor Rules: tools/ccn_tools/factors.py
  • Engine: tools/ccn_tools/reference_calculator.py:compute_inventory()
            </div>
            """,
            unsafe_allow_html=True,
        )

    with tab3:
        st.markdown(f"#### Data Quality Issues Planted in Raw Feeds ({selected_year})")
        st.caption("Automated anomaly detection screening raw ERP lines, energy meters, GoO cancellations, and farmer surveys.")

        issues = api.inventory.get_data_quality_issues(selected_year)
        if not issues.empty:
            st.warning(f"Detected **{len(issues)} data quality anomalies** in the {selected_year} raw data feeds requiring reconciliation.")
            st.dataframe(issues, use_container_width=True, hide_index=True)
            
            st.markdown(
                """
                **Common Real-World Error Types Detected:**
                - `unit_error`: ERP line items recorded in metric tonnes (`uom = TO`) instead of kilograms, causing a 1000x multiplier.
                - `duplicate_record`: Double-posted vendor purchase invoices.
                - `currency_error`: Invoices recorded in Swedish Krona (SEK) or USD without conversion to EUR.
                - `missing_record`: Monthly energy meters with missing winter log intervals.
                - `certificate_mismatch`: Guarantees of Origin (GoO) cancellations where the vintage year does not match the consumption year.
                """
            )

            # Live Currency Reconciler using Frankfurter API
            rates = api.live.get_live_currency_rates()
            st.markdown("##### 💱 Live Currency Reconciliation (European Central Bank / Frankfurter API)")
            c_curr1, c_curr2, c_curr3 = st.columns(3)
            with c_curr1:
                amt_in = st.number_input("Invoice Amount to Reconcile:", value=100000.0, step=10000.0)
            with c_curr2:
                from_curr = st.selectbox("Currency in ERP Invoice:", ["SEK (Swedish Krona - Foodhills)", "USD (US Dollar - Additives)", "GBP (British Pound)"])
            
            curr_code = from_curr.split()[0]
            rate = rates["rates"].get(curr_code, 1.0)
            converted_eur = amt_in / rate

            with c_curr3:
                st.metric(
                    label=f"Reconciled Value in EUR",
                    value=f"€{converted_eur:,.2f}",
                    delta=f"ECB Rate: 1 EUR = {rate:.3f} {curr_code}",
                )
        else:
            st.success(f"No anomalous records flagged in {selected_year} feeds.")

    with tab4:
        st.markdown("#### Validation Against Public Ground Truths")
        st.caption("The 2023 and 2024 development ground truths are published to verify pipeline calculation accuracy.")

        b_score = api.inventory.get_benchmark_score(2024)
        if b_score.get("score") is not None:
            st.metric("2024 Development Benchmark Score", f"{b_score['score'] * 100:.1f} / 100")
            st.json(b_score)
        else:
            st.info("Validation score available for reporting year 2024.")
