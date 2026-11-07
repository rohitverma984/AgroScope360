"""
views/nature_sbtn.py — Track D: SBTN Catchment Nature-Priority View + Real-Time 3D Satellite Geomap

Implements the official SBTN pressure x state prioritization formula:
    priority = (P / median(P) + 0.5 * N / median(N)) * state_weight * p_sensitivity
Includes Esri World Imagery 3D Satellite Deck.gl Geomap & 360° Three.js 3D Satellite Terrain.
"""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st
import streamlit.components.v1 as components

from components.satellite_3d_map import (
    build_satellite_3d_deck,
    build_threejs_satellite_3d_terrain_html,
    render_realtime_satellite_hud,
)

STATE_WEIGHT = {"good": 1.0, "moderate": 1.2, "poor": 1.5, "bad": 1.8}
APETIT_CROPS = ["pea", "potato", "carrot", "spinach", "turnip_rape"]


@st.cache_data(show_spinner="Calculating catchment nutrient pressures and SBTN priorities …")
def _compute_catchment_priorities(root: Path, year: int = 2025) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Compute SBTN catchment priorities from contract field parcel data."""
    cat_df = pd.read_csv(root / "data" / "06_nature" / "catchments.csv")
    par_df = pd.read_csv(root / "data" / "01_master" / "parcels.csv")
    crop_df = pd.read_csv(root / "data" / "03_farming" / "parcel_crop_history_and_plan.csv")

    dev_path = root / "tasks" / "dev" / "D1_dev_catchments_2025.csv"
    dev_truth = pd.read_csv(dev_path) if dev_path.exists() else pd.DataFrame()

    crops_yr = crop_df[(crop_df["year"] == year) & (crop_df["crop"].isin(APETIT_CROPS))].copy()
    merged_par = crops_yr.merge(par_df, on="parcel_id", how="inner")

    grp = (
        merged_par.groupby("catchment_id")
        .agg(
            contract_area_ha=("area_ha", "sum"),
            parcel_count=("parcel_id", "count"),
            buffer_strip_ha=("area_ha", lambda s: merged_par.loc[s.index, "area_ha"][merged_par.loc[s.index, "buffer_strip"] == True].sum()),
            avg_slope=("slope_pct", "mean"),
            avg_clay=("clay_pct_soilmap", "mean"),
        )
        .reset_index()
    )

    c = cat_df.merge(grp, on="catchment_id", how="left").fillna({
        "contract_area_ha": 0.0,
        "parcel_count": 0,
        "buffer_strip_ha": 0.0,
        "avg_slope": 0.0,
        "avg_clay": 0.0,
    })

    retention = c["nutrient_retention_frac_estimate"].fillna(0.2)
    p_load = c["contract_area_ha"] * 1.1 * (1.0 - retention)
    n_load = c["contract_area_ha"] * 15.0 * (1.0 - retention)

    c["apetit_p_to_water_kg"] = p_load.round(2)
    c["apetit_n_to_water_kg"] = n_load.round(1)

    med_p = max(c[c["contract_area_ha"] > 0]["apetit_p_to_water_kg"].median(), 1.0)
    med_n = max(c[c["contract_area_ha"] > 0]["apetit_n_to_water_kg"].median(), 1.0)

    st_weight = c["ecological_status_class"].map(STATE_WEIGHT).fillna(1.2)
    p_sens = c["p_sensitivity"].fillna(1.0)

    score = np.where(
        c["contract_area_ha"] > 0,
        (c["apetit_p_to_water_kg"] / med_p + 0.5 * (c["apetit_n_to_water_kg"] / med_n)) * st_weight * p_sens,
        0.0,
    )
    c["sbtn_priority_score"] = np.round(score, 3)
    c["priority_rank"] = c["sbtn_priority_score"].rank(ascending=False, method="min").astype(int)

    return c.sort_values("priority_rank"), merged_par, dev_truth


def render(root: Path) -> None:
    st.title("🏞️ Nature & Catchment Priorities (SBTN + 3D Satellite Geomap)")
    st.caption("⚠️ Synthetic estimates only — SBTN Step 1 & 2 pressure-state assessment with real-time 3D satellite runoff telemetry")

    st.info(
        "**SBTN Freshwater Prioritisation:** Prioritises catchments combining agricultural nutrient pressures "
        "(P and N loads delivered from Apetit contract parcels to receiving waters) with ecological state and sensitivity.\n"
        "$$\\text{Priority} = \\left(\\frac{P}{\\text{median}(P)} + 0.5 \\times \\frac{N}{\\text{median}(N)}\\right) "
        "\\times \\text{state\\_weight} \\times p\\_sensitivity$$\n"
        "State weights: Good = 1.0, Moderate = 1.2, Poor = 1.5, Bad = 1.8. Limiting nutrient in Finnish waters is typically Phosphorus.",
        icon="🏞️",
    )

    try:
        catchment_table, parcels_merged, dev_truth = _compute_catchment_priorities(root, 2025)
    except Exception as exc:
        st.error(f"Error computing catchment priorities: {exc}")
        return

    # ── Headline KPIs ────────────────────────────────────────────────────────
    sourced_catchments = catchment_table[catchment_table["contract_area_ha"] > 0]
    total_area = sourced_catchments["contract_area_ha"].sum()
    total_p = sourced_catchments["apetit_p_to_water_kg"].sum()
    total_n = sourced_catchments["apetit_n_to_water_kg"].sum()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Active Sourcing Catchments", f"{len(sourced_catchments)} / {len(catchment_table)}")
    col2.metric("Contract Farmland (2025)", f"{total_area:,.0f} ha")
    col3.metric("Est. P to Water", f"{total_p:,.0f} kg P/yr")
    col4.metric("Est. N to Water", f"{total_n:,.0f} kg N/yr")

    st.divider()

    # ── Real-Time 3D Satellite Catchment & Buffer Strip Geomap ───────────────
    st.markdown("### 🛰️ Real-Time 3D Satellite Freshwater Runoff & Buffer Strip Geomap")
    sbtn_parcels = parcels_merged.merge(
        sourced_catchments[["catchment_id", "priority_rank", "ecological_status_class", "sbtn_priority_score"]],
        on="catchment_id",
        how="left",
    ).head(480).copy()

    def _sbtn_rgba(row: pd.Series) -> list[int]:
        if not row["buffer_strip"] and row.get("priority_rank", 10) <= 5:
            return [239, 68, 68, 230]     # Red: Missing buffer in Top-5 priority catchment
        if not row["buffer_strip"]:
            return [245, 158, 11, 220]    # Amber: Missing buffer strip
        return [16, 185, 129, 215]        # Green: Protected with riparian buffer strip

    def _sbtn_hex(row: pd.Series) -> str:
        if not row["buffer_strip"] and row.get("priority_rank", 10) <= 5:
            return "#ef4444"
        if not row["buffer_strip"]:
            return "#f59e0b"
        return "#10b981"

    def _sbtn_tier(row: pd.Series) -> str:
        if not row["buffer_strip"] and row.get("priority_rank", 10) <= 5:
            return "Critical P Runoff Hotspot (No Buffer)"
        if not row["buffer_strip"]:
            return "Missing Riparian Buffer Strip"
        return "Riparian Buffer Protected ✓"

    sbtn_parcels["color"] = sbtn_parcels.apply(_sbtn_rgba, axis=1)
    sbtn_parcels["hex_color"] = sbtn_parcels.apply(_sbtn_hex, axis=1)
    sbtn_parcels["tier"] = sbtn_parcels.apply(_sbtn_tier, axis=1)
    sbtn_parcels["est_p_kg"] = (
        sbtn_parcels["area_ha"].astype(float)
        * (1.35 if not sbtn_parcels["buffer_strip"].all() else 0.85)
        * (1.0 + sbtn_parcels["slope_pct"].astype(float) * 0.08)
    ).round(1)
    sbtn_parcels["elevation"] = (sbtn_parcels["est_p_kg"] * 110.0 + sbtn_parcels["slope_pct"].astype(float) * 160.0).round(0)
    sbtn_parcels["info"] = (
        "Catchment: " + sbtn_parcels["catchment_id"].astype(str)
        + " | Crop: " + sbtn_parcels["crop"].astype(str)
    )

    render_realtime_satellite_hud(
        lat=61.05,
        lon=22.34,
        region_label="SBTN Freshwater Catchments & Riparian Buffer Coverage",
        parcel_count=len(sbtn_parcels),
        mode_badge="SBTN 3D SATELLITE HYDROLOGY",
    )

    smap_tab1, smap_tab2 = st.tabs([
        "🛰️ 3D Satellite Deck.gl Catchment Geomap (Extruded P-Load Columns)",
        "🏔️ 3D Satellite Terrain Mesh (360° Three.js WebGL)",
    ])

    with smap_tab1:
        sbtn_col_layer = pdk.Layer(
            "ColumnLayer",
            data=sbtn_parcels,
            get_position=["lon", "lat"],
            get_elevation="elevation",
            elevation_scale=1,
            radius=360,
            get_fill_color="color",
            pickable=True,
            auto_highlight=True,
            extruded=True,
        )
        sbtn_tooltip = {
            "html": """
            <div style="background:#0b1c30; color:#f8fafc; padding:8px 12px; border-radius:6px; font-family:sans-serif; font-size:12px; line-height:1.45;">
                <b>Parcel:</b> {parcel_id} ({tier})<br/>
                <b>Catchment:</b> {catchment_id} (Rank #{priority_rank})<br/>
                <b>Crop:</b> {crop} | <b>Area:</b> {area_ha} ha<br/>
                <b>Est. Delivered P:</b> {est_p_kg} kg P/yr | <b>Slope:</b> {slope_pct}%
            </div>
            """,
            "style": {"zIndex": "1000"},
        }
        sbtn_deck = build_satellite_3d_deck(
            feature_layers=[sbtn_col_layer],
            lat=61.05,
            lon=22.34,
            zoom=8.6,
            pitch=54.0,
            bearing=16.0,
            tooltip=sbtn_tooltip,
            include_labels=True,
        )
        st.pydeck_chart(sbtn_deck, use_container_width=True)
        st.caption("🛰️ **Esri World Imagery 3D Satellite Geomap** · Red = Missing Buffer in Priority Catchment · Amber = Missing Buffer · Green = Buffer Protected.")

    with smap_tab2:
        sbtn_three = build_threejs_satellite_3d_terrain_html(
            df=sbtn_parcels,
            title="SBTN Catchment Phosphorus Runoff 3D Terrain",
            lat_col="lat",
            lon_col="lon",
            id_col="parcel_id",
            value_col="est_p_kg",
            tier_col="tier",
            color_col="hex_color",
            extra_col="info",
            value_unit="kg P/yr runoff",
            relief_scale=1.7,
            height_px=480,
        )
        components.html(sbtn_three, height=490, scrolling=False)

    st.divider()

    # ── Tabs ────────────────────────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs(["🏆 Catchment Rankings", "🔍 Catchment Deep-Dive", "📐 SBTN Methodology & Calibration"])

    with tab1:
        st.markdown("#### Catchments Ranked by Nature Priority (2025)")
        st.caption("Catchments with higher ranks represent highest urgency for agricultural nutrient stewardship.")

        display_cols = [
            "priority_rank",
            "catchment_id",
            "region",
            "receiving_water_type",
            "ecological_status_class",
            "contract_area_ha",
            "apetit_p_to_water_kg",
            "apetit_n_to_water_kg",
            "sbtn_priority_score",
        ]
        col_names = {
            "priority_rank": "Rank",
            "catchment_id": "Catchment ID",
            "region": "Region",
            "receiving_water_type": "Water Body",
            "ecological_status_class": "Eco Status",
            "contract_area_ha": "Contract Area (ha)",
            "apetit_p_to_water_kg": "P to Water (kg)",
            "apetit_n_to_water_kg": "N to Water (kg)",
            "sbtn_priority_score": "SBTN Score",
        }

        st.dataframe(
            sourced_catchments[display_cols].rename(columns=col_names),
            use_container_width=True,
            hide_index=True,
        )

        try:
            import plotly.express as px  # noqa: PLC0415
            fig = px.scatter(
                sourced_catchments,
                x="apetit_p_to_water_kg",
                y="apetit_n_to_water_kg",
                size="contract_area_ha",
                color="ecological_status_class",
                hover_name="catchment_id",
                text="catchment_id",
                title="Catchment Nutrient Footprint vs Ecological Status",
                labels={"apetit_p_to_water_kg": "P Load delivered to water (kg)", "apetit_n_to_water_kg": "N Load delivered to water (kg)"},
                color_discrete_map={"good": "#2ecc71", "moderate": "#f1c40f", "poor": "#e67e22", "bad": "#e74c3c"},
            )
            fig.update_traces(textposition="top center")
            fig.update_layout(height=450)
            st.plotly_chart(fig, use_container_width=True)
        except Exception:
            pass

    with tab2:
        st.markdown("#### Catchment Field Parcel Deep-Dive")
        cid = st.selectbox("Select Catchment to inspect parcels:", sourced_catchments["catchment_id"].tolist())
        c_row = sourced_catchments[sourced_catchments["catchment_id"] == cid].iloc[0]

        d1, d2, d3 = st.columns(3)
        d1.markdown(f"**Receiving Water:** {c_row['receiving_water_type'].title()} ({c_row['region']})")
        d2.markdown(f"**Ecological Status:** `{c_row['ecological_status_class']}`")
        d3.markdown(f"**P-Sensitivity Factor:** `{c_row['p_sensitivity']}`")

        c_parcels = parcels_merged[parcels_merged["catchment_id"] == cid]
        st.markdown(f"**Active Contract Parcels ({len(c_parcels)} parcels, {c_row['contract_area_ha']:.1f} ha)**")

        p_cols = ["parcel_id", "farm_id", "crop", "area_ha", "soil_class_soilmap", "slope_pct", "buffer_strip", "drainage"]
        st.dataframe(c_parcels[p_cols], use_container_width=True, hide_index=True)

        no_buffer = c_parcels[~c_parcels["buffer_strip"]]
        st.markdown("##### 💡 Recommended Nature Stewardship Actions:")
        st.markdown(
            f"- **Buffer Strips (Lever L24):** {len(no_buffer)} parcels ({no_buffer['area_ha'].sum():.1f} ha) lack vegetated riparian buffer strips along drainage pathways."
        )
        st.markdown(
            "- **Catch Crops (Lever L11):** Introduce post-harvest winter cover crops to reduce leaching during autumn rains."
        )

    with tab3:
        st.markdown("#### Calibration & Dev Truth Comparison")
        st.markdown(
            "Task D1 provides true loads for 6 development catchments in `tasks/dev/D1_dev_catchments_2025.csv`. "
            "These help calibrate delivery factors and retention models."
        )
        if not dev_truth.empty:
            merged_dev = dev_truth.merge(
                sourced_catchments[["catchment_id", "apetit_p_to_water_kg", "apetit_n_to_water_kg"]],
                on="catchment_id",
                suffixes=("_true", "_pred"),
            )
            st.dataframe(merged_dev, use_container_width=True, hide_index=True)

        st.markdown(
            """<div class="evidence-box">
Reference: docs/NATURE_SBTN.md &amp; tools/ccn_tools/baselines.py:d1_area()
Formula: priority = (P / median(P) + 0.5 * N / median(N)) * state_weight * p_sensitivity
State weights: good=1.0, moderate=1.2, poor=1.5, bad=1.8
P sensitivity source: data/06_nature/catchments.csv
Deterministic execution: prototype/views/nature_sbtn.py
</div>""",
            unsafe_allow_html=True,
        )
