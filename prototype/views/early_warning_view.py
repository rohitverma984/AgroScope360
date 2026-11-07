"""
prototype/views/early_warning_view.py — Climate Risk Early Warning System
Matches the exact reference Agriculture Intelligence UI:
- Top header: '< Drought detected on Oct 10 [Active]' + 'More Actions' / 'Create Project'
- Full-width 'Search for a region' bar
- Left column:
  - 'Event Start Sept 8, 2025 · Days Active 30 · Confidence Rating [High]'
  - Blue-bordered Card 1: 'Rainfall is 20% below average this week' + 'View Data' / 'View on Map >' + Actual vs Average (5 yr) chart with 'Today' line
  - Card 2: 'Soil moisture is 20% below average this week' + 'View Data' / 'View on Map >' + Actual vs Average (5 yr) chart with 'Today' line
- Right column:
  - Full-height interactive Leaflet Geomap with 5 blue-shaded regional provinces/sub-basins, centered labels, right-hand vertical map controls, and bottom-right 'Inches of Precipitation' (0–8) gradient legend.
"""
from __future__ import annotations

from pathlib import Path
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from components.satellite_3d_map import build_drought_choropleth_map_html
from core.api import NavigatorAPI
from core.early_warning_service import EarlyWarningService


def _html(raw: str) -> str:
    """Strip per-line indentation so Markdown never turns HTML into a code block."""
    return "\n".join(line.lstrip() for line in raw.splitlines() if line.strip())


def _build_reference_line_chart(
    dates: list[str],
    actual_vals: list[float],
    avg_vals: list[float],
    actual_label: str,
    y_suffix: str = "in",
) -> go.Figure:
    """Build the clean white-background orange vs dotted-grey line chart with 'Today' vertical divider matching the screenshot."""
    fig = go.Figure()

    # Average (5 year) — dotted grey line
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=avg_vals,
            mode="lines",
            name="Average (5 year)",
            line=dict(color="#9ca3af", width=2, dash="dot"),
        )
    )

    # Actual — solid warm amber/orange line up to 'Today' (index -2), then dashed projection
    today_idx = max(0, len(dates) - 2)
    fig.add_trace(
        go.Scatter(
            x=dates[: today_idx + 1],
            y=actual_vals[: today_idx + 1],
            mode="lines",
            name=actual_label,
            line=dict(color="#d97706", width=2.5),
        )
    )
    # Forecast tail after Today with subtle uncertainty cone
    if today_idx < len(dates) - 1:
        tail_x = dates[today_idx:]
        tail_y = actual_vals[today_idx:]
        upper_y = [v * 1.15 for v in tail_y]
        lower_y = [max(0.0, v * 0.85) for v in tail_y]

        fig.add_trace(
            go.Scatter(
                x=tail_x + tail_x[::-1],
                y=upper_y + lower_y[::-1],
                fill="toself",
                fillcolor="rgba(217, 119, 6, 0.12)",
                line=dict(color="rgba(255,255,255,0)"),
                hoverinfo="skip",
                showlegend=False,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=tail_x,
                y=tail_y,
                mode="lines",
                name="Projected Trend",
                line=dict(color="#d97706", width=2, dash="dot"),
                showlegend=False,
            )
        )

    # Vertical 'Today' line
    today_x = dates[today_idx]
    fig.add_vline(
        x=today_x,
        line_width=1.5,
        line_color="#9ca3af",
    )
    fig.add_annotation(
        x=today_x,
        y=1.06,
        yref="paper",
        text="Today",
        showarrow=False,
        font=dict(size=10, color="#4b5563"),
    )

    fig.update_layout(
        height=205,
        margin=dict(l=36, r=16, t=22, b=32),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        xaxis=dict(
            showgrid=True,
            gridcolor="#f3f4f6",
            tickfont=dict(size=10, color="#6b7280"),
            linecolor="#e5e7eb",
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#f3f4f6",
            ticksuffix=f" {y_suffix}",
            tickfont=dict(size=10, color="#6b7280"),
            linecolor="#e5e7eb",
        ),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.22,
            xanchor="center",
            x=0.5,
            font=dict(size=10.5, color="#374151"),
        ),
        hovermode="x unified",
    )
    return fig


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
            label_visibility="collapsed",
        )
    with s_col2:
        metric_focus = st.radio(
            "Map Layer:",
            ["🌧️ Rainfall Map", "🌱 Soil Moisture Map"],
            horizontal=True,
            label_visibility="collapsed",
        )

    data = api.early_warning.get_regional_alerts(selected_region, scenario="ssp245")
    alert = data["alert"]
    ts = data["time_series"]

    rain_def = int(round(abs(ts["rainfall_deficit_pct"])))
    soil_def = int(round(abs(ts["moisture_deficit_pct"])))
    is_rain_active = "Rainfall" in metric_focus

    # ── Split 2-Column Layout (Charts on Left, Regional Choropleth Map on Right)
    col_left, col_right = st.columns([1.08, 1.05])

    with col_left:
        # Event Start · Days Active · Confidence Rating strip
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

        # ── Card 1: Rainfall is 20% below average this week ──────────────────
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
        st.plotly_chart(fig_rain, use_container_width=True)

        # ── Card 2: Soil moisture is 20% below average this week ─────────────
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
        st.plotly_chart(fig_soil, use_container_width=True)

    with col_right:
        # ── Right Column: Exact Regional Choropleth + Terrain/Satellite Geomap
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

    # ── Bottom Dark Footer Bar matching screenshot ('Agriculture Intelligence · Visual Explorer · Projects')
    st.markdown(
        _html("""
        <div style="background:#111827; color:#f9fafb; border-radius:6px; padding:10px 18px; margin-top:8px; display:flex; justify-content:space-between; align-items:center; font-size:0.78rem;">
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
