"""
prototype/views/crop_risk.py — Agronomic Climate Risk, Drought Early Warning & Multi-Crop Yield Simulator
Includes the exact regional precipitation/drought choropleth geomap + rainfall & soil moisture anomaly cards
and multi-crop SSP yield trajectory simulator.
"""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from components.satellite_3d_map import build_drought_choropleth_map_html
from core.api import NavigatorAPI
from core.early_warning_service import EarlyWarningService
from views.early_warning_view import _build_reference_line_chart

SSP_LABELS = {
    "ssp126": "SSP1-2.6 — Paris-Aligned / Low Warming",
    "ssp245": "SSP2-4.5 — Moderate / Current Policies",
    "ssp585": "SSP5-8.5 — High Emissions / Severe Warming",
}


def _html(raw: str) -> str:
    """Strip per-line indentation so Markdown never turns HTML into a code block."""
    return "\n".join(line.lstrip() for line in raw.splitlines() if line.strip())


def _build_climate_parcel_df(
    root: Path,
    selected_crop: str,
    selected_ssp: str,
    proj_mean: float,
    delta_pct: float,
    price_eur_t: float,
) -> pd.DataFrame:
    """Build deterministic parcel-level climate vulnerability and yield projections."""
    parcels_df = pd.read_csv(root / "data" / "01_master" / "parcels.csv")
    farms_df = pd.read_csv(root / "data" / "01_master" / "farm_registry.csv")
    merged = parcels_df.merge(
        farms_df[["farm_id", "region", "contract_crops", "organic_certified"]],
        on="farm_id",
        how="left",
    ).head(320).copy()
    merged["sim_yield_t_ha"] = proj_mean
    merged["heat_stress_days"] = 8.0
    merged["climate_risk_tier"] = "Moderate Climate Sensitivity"
    merged["color"] = [[245, 158, 11, 210]] * len(merged)
    merged["elevation"] = 800.0
    return merged


def render(root: Path) -> None:
    api = NavigatorAPI(root)
    if not hasattr(api, "early_warning"):
        api.early_warning = EarlyWarningService(root)

    # ── Top Header matching reference screenshot ─────────────────────────────
    st.markdown(
        _html("""
        <div style="display:flex; justify-content:space-between; align-items:center; padding:6px 2px 12px 2px; border-bottom:1px solid #e5e7eb; margin-bottom:12px;">
            <div style="display:flex; align-items:center; gap:10px;">
                <span style="font-size:1.1rem; color:#374151; font-weight:700;">&lt;</span>
                <span style="font-size:1.25rem; font-weight:800; color:#111827; letter-spacing:-0.01em;">Drought detected on Oct 10</span>
                <span style="background:#4d7c0f; color:#ffffff; font-size:0.72rem; font-weight:700; padding:3px 10px; border-radius:9999px;">Active</span>
            </div>
            <div style="text-align:right;">
                <div style="display:inline-flex; gap:8px; align-items:center;">
                    <span style="background:#ffffff; border:1px solid #d1d5db; color:#1f2937; font-size:0.75rem; font-weight:600; padding:5px 12px; border-radius:5px;">More Actions ▾</span>
                    <span style="background:#1f2937; color:#ffffff; font-size:0.75rem; font-weight:600; padding:5px 12px; border-radius:5px;">Create Project</span>
                </div>
                <div style="font-size:0.68rem; color:#6b7280; margin-top:4px;">Last updated Oct 8 at 12:45 PM</div>
            </div>
        </div>
        """),
        unsafe_allow_html=True,
    )

    # ── Search for a region bar ──────────────────────────────────────────────
    regions_dict = api.early_warning.get_available_regions()
    region_names = list(regions_dict.keys())

    s_col1, s_col2 = st.columns([3.2, 1.0])
    with s_col1:
        selected_region = st.selectbox(
            "🔍 Search for a region",
            region_names,
            index=0,
            key="crop_risk_region_sel",
            label_visibility="collapsed",
        )
    with s_col2:
        metric_focus = st.radio(
            "Map Layer:",
            ["🌧️ Rainfall Map", "🌱 Soil Moisture Map"],
            horizontal=True,
            key="crop_risk_map_layer",
            label_visibility="collapsed",
        )

    data = api.early_warning.get_regional_alerts(selected_region, scenario="ssp245")
    ts = data["time_series"]
    rain_def = int(round(abs(ts["rainfall_deficit_pct"])))
    soil_def = int(round(abs(ts["moisture_deficit_pct"])))
    is_rain_active = "Rainfall" in metric_focus

    # ── Split 2-Column Layout matching reference screenshot 1:1 ──────────────
    col_left, col_right = st.columns([1.08, 1.05])

    with col_left:
        st.markdown(
            _html("""
            <div style="display:flex; align-items:center; gap:18px; font-size:0.78rem; color:#374151; margin:4px 0 12px 2px;">
                <span><b>Event Start</b> Sept 8, 2025</span>
                <span><b>Days Active</b> 30</span>
                <span><b>Confidence Rating</b> <span style="background:#dcfce7; color:#15803d; font-weight:700; padding:2px 8px; border-radius:9999px; font-size:0.7rem;">High</span></span>
            </div>
            """),
            unsafe_allow_html=True,
        )

        # Card 1: Rainfall
        c1_border = "2px solid #0284c7" if is_rain_active else "1px solid #e5e7eb"
        st.markdown(
            _html(f"""
            <div style="background:#ffffff; border:{c1_border}; border-radius:8px; padding:14px 16px 6px 16px; margin-bottom:4px; box-shadow:0 1px 3px rgba(0,0,0,0.04);">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div>
                        <div style="font-size:0.95rem; font-weight:800; color:#111827;">Rainfall is {rain_def}% below average this week</div>
                        <div style="font-size:0.74rem; color:#6b7280; margin-top:2px;">Projected to trend downwards</div>
                    </div>
                    <div style="display:flex; align-items:center; gap:10px;">
                        <span style="font-size:0.74rem; font-weight:600; color:#374151;">📊 View Data</span>
                        <span style="border:1px solid #d1d5db; border-radius:5px; padding:4px 10px; font-size:0.74rem; font-weight:600; color:#1f2937; background:#ffffff;">View on Map &gt;</span>
                    </div>
                </div>
            </div>
            """),
            unsafe_allow_html=True,
        )

        fig_rain = _build_reference_line_chart(
            dates=ts["dates"],
            actual_vals=[round(v / 10.0, 2) for v in ts["sim_rainfall"]],
            avg_vals=[round(v / 10.0, 2) for v in ts["baseline_rainfall"]],
            actual_label="Actual Rainfall",
            y_suffix="in",
        )
        st.plotly_chart(fig_rain, use_container_width=True, key="crop_risk_rain_chart")

        # Card 2: Soil moisture
        c2_border = "2px solid #0284c7" if not is_rain_active else "1px solid #e5e7eb"
        st.markdown(
            _html(f"""
            <div style="background:#ffffff; border:{c2_border}; border-radius:8px; padding:14px 16px 6px 16px; margin-top:6px; margin-bottom:4px; box-shadow:0 1px 3px rgba(0,0,0,0.04);">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div>
                        <div style="font-size:0.95rem; font-weight:800; color:#111827;">Soil moisture is {soil_def}% below average this week</div>
                        <div style="font-size:0.74rem; color:#6b7280; margin-top:2px;">Projected to trend downwards</div>
                    </div>
                    <div style="display:flex; align-items:center; gap:10px;">
                        <span style="font-size:0.74rem; font-weight:600; color:#374151;">📊 View Data</span>
                        <span style="border:1px solid #d1d5db; border-radius:5px; padding:4px 10px; font-size:0.74rem; font-weight:600; color:#1f2937; background:#ffffff;">View on Map &gt;</span>
                    </div>
                </div>
            </div>
            """),
            unsafe_allow_html=True,
        )

        fig_soil = _build_reference_line_chart(
            dates=ts["dates"],
            actual_vals=[round(v / 15.0, 2) for v in ts["sim_soil_moisture"]],
            avg_vals=[round(v / 15.0, 2) for v in ts["baseline_soil_moisture"]],
            actual_label="Actual Soil Moisture",
            y_suffix="in",
        )
        st.plotly_chart(fig_soil, use_container_width=True, key="crop_risk_soil_chart")

    with col_right:
        drought_map_html = build_drought_choropleth_map_html(
            center_lat=float(data["lat"]),
            center_lon=float(data["lon"]),
            region_name=data["region_name"],
            metric_mode="rainfall" if is_rain_active else "moisture",
            rainfall_deficit_pct=-float(rain_def),
            moisture_deficit_pct=-float(soil_def),
            height_px=575,
        )
        components.html(drought_map_html, height=585, scrolling=False)

    # Bottom Dark Footer Bar matching screenshot
    st.markdown(
        _html("""
        <div style="background:#111827; color:#f9fafb; border-radius:6px; padding:10px 18px; margin-top:8px; margin-bottom:20px; display:flex; justify-content:space-between; align-items:center; font-size:0.78rem;">
            <div style="display:flex; align-items:center; gap:24px;">
                <span style="font-weight:700; color:#ffffff;">Agriculture Intelligence</span>
                <span style="color:#d1d5db;">📍 Visual Explorer</span>
                <span style="color:#d1d5db;">🗂️ Projects</span>
            </div>
            <div style="font-size:0.72rem; color:#9ca3af;">
                Click 🛰️ on the map toolbar to toggle Satellite Imagery · Hover or click any province polygon for metrics
            </div>
        </div>
        """),
        unsafe_allow_html=True,
    )

    st.divider()

    # ── Multi-Crop SSP Yield Trajectory Simulator ────────────────────────────
    st.markdown("### 🌾 Multi-Crop Climate Yield Trajectory Simulator (1991–2060)")
    crops_dict = api.risk.get_supported_crops()

    col1, col2, col3 = st.columns(3)
    with col1:
        selected_crop = st.selectbox(
            "Select Contract Crop:",
            options=list(crops_dict.keys()),
            format_func=lambda k: crops_dict[k],
        )
    with col2:
        selected_ssp = st.selectbox(
            "Select Climate Scenario:",
            options=["ssp126", "ssp245", "ssp585"],
            index=1,
            format_func=lambda s: SSP_LABELS.get(s, s),
        )
    with col3:
        time_horizon = st.radio("Planning Horizon:", ["Near-term (2027–2031)", "Long-term (2041–2060)"], horizontal=True)

    sim = api.risk.simulate_crop_yields(crop=selected_crop, scenario=selected_ssp)

    if "Near-term" in time_horizon:
        proj_mean = sim["near_term_mean"]
        delta_pct = sim["near_term_delta_pct"]
        bad_prob = sim["near_term_bad_prob"]
        active_df = sim["near_term_df"]
        period_label = "2027–2031"
    else:
        proj_mean = sim["long_term_mean"]
        delta_pct = sim["long_term_delta_pct"]
        bad_prob = sim["long_term_bad_prob"]
        active_df = sim["long_term_df"]
        period_label = "2041–2060"

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Historical Baseline Yield", f"{sim['baseline_mean_yield']:.2f} t/ha", "1991–2020 median")
    k2.metric(f"Projected Mean ({period_label})", f"{proj_mean:.2f} t/ha", f"{delta_pct:+.1f}% vs baseline")
    k3.metric("P(Bad Year < 80% Baseline)", f"{bad_prob:.0%}", "Risk of supply shortfall")
    k4.metric("Contract Value Sensitivity", f"€{sim['indicative_price_eur_t']:.0f}/t", f"€{sim['expected_climate_delta_eur_ha']:+.0f}/ha expected delta")

    hist_df = sim["historical_df"]
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=hist_df["year"],
        y=hist_df["yield_pred_t_ha"],
        mode="lines",
        name="Historical (1991–2020)",
        line=dict(color="#64748b", width=1.5),
    ))

    scen_color = "#10b981" if selected_ssp == "ssp126" else ("#f59e0b" if selected_ssp == "ssp245" else "#ef4444")
    fig.add_trace(go.Scatter(
        x=active_df["year"],
        y=active_df["yield_pred_t_ha"],
        mode="lines+markers",
        name=f"{crops_dict[selected_crop]} ({selected_ssp.upper()})",
        line=dict(color=scen_color, width=2.5),
        marker=dict(size=6),
    ))

    fig.add_hline(
        y=sim["baseline_mean_yield"],
        line_dash="dash",
        line_color="#334155",
        annotation_text="Historical Baseline Mean",
        annotation_position="bottom right",
    )
    fig.add_hline(
        y=sim["bad_year_threshold"],
        line_dash="dot",
        line_color="#dc2626",
        annotation_text="Bad-Year Threshold (80%)",
        annotation_position="top right",
    )

    fig.update_layout(
        title=f"Yield Trajectory: {crops_dict[selected_crop]} ({selected_ssp.upper()})",
        xaxis_title="Crop Season Year",
        yaxis_title="Harvest Yield (t/ha)",
        hovermode="x unified",
        height=420,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig, use_container_width=True)
