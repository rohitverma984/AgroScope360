"""
prototype/views/map_view.py — Real-Time 3D Satellite Geospatial Command Center View
Powered by Free, Live Public APIs + Esri World Imagery 3D Satellite Tiles:
- Esri World Imagery Satellite + Hybrid Reference Labels (3D Deck.gl & 360° Three.js Terrain)
- Digitraffic Marine API (Live Baltic Sea Vessel Traffic)
- Open-Meteo API (Live Real-Time Weather & Agronomic Alerts)
- Frankfurter / European Central Bank API (Live Currency Conversions)
- Nominatim / OpenStreetMap (Live Geocoding Address Search)
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
    get_satellite_base_layers,
    render_realtime_satellite_hud,
)
from core.api import NavigatorAPI


def render(root: Path) -> None:
    api = NavigatorAPI(root)

    st.title("🌍 Real-Time 3D Satellite Geospatial Command Center")
    st.caption("Live 3D satellite spatial intelligence connecting facilities, contract field parcels, logistics flows, marine vessels, and weather")

    # ── Real-Time Top Indicator Strip ────────────────────────────────────────
    loc_coords = {
        "Säkylä Plant (Satakunta)": (61.0787, 22.2538),
        "Kantvik Oilseed Mill (Uusimaa)": (60.084, 24.383),
        "Bjuv Facility (Sweden)": (56.084, 12.92),
    }

    col_l1, col_l2 = st.columns([3, 1])
    with col_l1:
        st.markdown("##### 🌦️ Live Field Weather & Agronomic Conditions (Open-Meteo API)")
    with col_l2:
        loc_choice = st.selectbox("Active Facility:", list(loc_coords.keys()), label_visibility="collapsed")

    lat, lon = loc_coords[loc_choice]
    weather = api.geo.fetch_live_weather(lat=lat, lon=lon)
    rates_data = api.live.get_live_currency_rates()
    grid_data = api.live.get_live_grid_carbon_intensity()

    w1, w2, w3, w4, w5 = st.columns(5)
    w1.metric("Live Temperature", f"{weather['temp_c']} °C", f"Day High: {weather['daily_max']} °C")
    w2.metric("Precipitation", f"{weather['precip_mm']} mm", "Harvest soil limit")
    w3.metric("Surface Wind", f"{weather['wind_kmh']} km/h", "Spray drift limit")
    w4.metric("Grid Carbon (FI)", f"{grid_data['location_based_g_per_kwh']} g/kWh", "88% Clean Dispatch")
    w5.metric("ECB EUR/SEK", f"{rates_data['rates']['SEK']:.2f} SEK", f"EUR/USD: {rates_data['rates']['USD']:.2f}")

    st.divider()

    # ── Interactive Geocoding Address Search (Nominatim API) ──────────────────
    st.markdown("##### 🔎 Live Satellite Location Search (OpenStreetMap Nominatim Geocoding API)")
    c_geo1, c_geo2 = st.columns([3, 1])
    with c_geo1:
        geo_query = st.text_input("Search any Finnish town, municipality, or port to inspect in 3D Satellite:", placeholder="e.g. Säkylä, Naantali, Turku, Rauma, Bjuv, Kirkkonummi...")
    with c_geo2:
        search_btn = st.button("📍 Geocode & Fly 3D Camera", use_container_width=True)

    focus_lat, focus_lon, focus_zoom = 61.05, 22.45, 8.6
    if search_btn and geo_query:
        geo_res = api.live.geocode_location(geo_query)
        if geo_res:
            focus_lat, focus_lon = geo_res["lat"], geo_res["lon"]
            focus_zoom = 11.2
            st.success(f"📍 Geocoded: **{geo_res['display_name']}** (`{focus_lat:.4f}, {focus_lon:.4f}`)")
        else:
            st.warning(f"Could not find coordinates for '{geo_query}'. Showing default region.")

    # ── Map Controls & Layer Toggles ─────────────────────────────────────────
    st.markdown("#### 🛰️ Real-Time 3D Satellite Map Layers")
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        show_sites = st.checkbox("🏭 Facilities & Mills (3D Beacons)", value=True)
    with f2:
        show_parcels = st.checkbox("🌾 Contract Farm Fields (3D Extruded)", value=True)
    with f3:
        show_logistics = st.checkbox("🚚 Inbound 3D Freight Arcs", value=True)
    with f4:
        crop_filter = st.selectbox("Filter Crop:", ["all", "pea", "potato", "carrot", "turnip_rape"])

    f5, f6 = st.columns([2, 2])
    with f5:
        buffer_choice = st.radio(
            "Water Buffer Strip Filter:",
            ["All Fields", "Missing Buffer Strip (High Runoff Risk)", "Protected with Buffer Strip"],
            horizontal=True,
        )
    with f6:
        map_style_choice = st.selectbox(
            "Base Map Engine:",
            [
                "satellite-hybrid (Esri World Imagery 3D Satellite + Labels)",
                "satellite-pure (Esri World Imagery Pure Satellite 3D)",
                "dark (Carto High-Contrast Dark 3D)",
                "light (Carto Clean Light 3D)",
            ],
            index=0,
        )

    buffer_bool = None
    if "Missing" in buffer_choice:
        buffer_bool = False
    elif "Protected" in buffer_choice:
        buffer_bool = True

    # ── Load Map Data ────────────────────────────────────────────────────────
    sites_df = api.geo.get_sites()
    parcels_df = api.geo.get_parcels(year=2025, crop=crop_filter, buffer_only=buffer_bool, limit=1800).copy()
    arcs_df = api.geo.get_logistics_arcs(year=2025, limit=120)

    if not parcels_df.empty:
        parcels_df["elevation"] = (
            parcels_df["area_ha"].astype(float) * 55.0
            + parcels_df["slope_pct"].astype(float) * 180.0
            + np.where(parcels_df["buffer_strip"], 150.0, 650.0)
        ).round(0)
        parcels_df["hex_color"] = np.where(parcels_df["buffer_strip"], "#10b981", "#ef4444")
        parcels_df["tier"] = np.where(parcels_df["buffer_strip"], "Buffer Protected ✓", "Missing Buffer Strip ⚠️")
        parcels_df["info"] = "Crop: " + parcels_df["crop"].astype(str) + " | Slope: " + parcels_df["slope_pct"].astype(str) + "%"

    render_realtime_satellite_hud(
        lat=focus_lat,
        lon=focus_lon,
        region_label=f"Geospatial Command Center · {loc_choice}",
        parcel_count=len(parcels_df),
        mode_badge="LIVE 3D SATELLITE COMMAND",
    )

    geo_tab1, geo_tab2 = st.tabs([
        "🛰️ Real-Time 3D Satellite Deck.gl Map (Extruded Columns + Freight Arcs)",
        "🏔️ 3D Satellite-Draped Terrain Mesh (360° Three.js WebGL)",
    ])

    with geo_tab1:
        layers = []
        if "satellite" in map_style_choice:
            layers.extend(get_satellite_base_layers(include_labels="hybrid" in map_style_choice))

        # Layer 1: Inbound Logistics 3D Arcs
        if show_logistics and not arcs_df.empty:
            arc_layer = pdk.Layer(
                "ArcLayer",
                data=arcs_df,
                get_source_position=["from_lon", "from_lat"],
                get_target_position=["to_lon", "to_lat"],
                get_source_color=[16, 185, 129, 200],
                get_target_color=[56, 189, 248, 240],
                get_width=3.0,
                auto_highlight=True,
                pickable=True,
            )
            layers.append(arc_layer)

        # Layer 2: 3D Extruded Contract Farm Field Parcels
        if show_parcels and not parcels_df.empty:
            parcel_col_layer = pdk.Layer(
                "ColumnLayer",
                data=parcels_df,
                get_position=["lon", "lat"],
                get_elevation="elevation",
                elevation_scale=1,
                radius=340,
                get_fill_color="color",
                pickable=True,
                auto_highlight=True,
                extruded=True,
            )
            layers.append(parcel_col_layer)

        # Layer 3: Facilities (Säkylä, Kantvik, Bjuv, Pudasjärvi)
        if show_sites and not sites_df.empty:
            site_layer = pdk.Layer(
                "ScatterplotLayer",
                data=sites_df,
                get_position=["lon", "lat"],
                get_color="color",
                get_radius=4500,
                pickable=True,
                opacity=1.0,
                stroked=True,
                filled=True,
                radius_min_pixels=10,
                radius_max_pixels=25,
                line_width_min_pixels=2,
                get_line_color=[255, 255, 255, 255],
            )
            layers.append(site_layer)

        initial_view_state = pdk.ViewState(
            latitude=focus_lat,
            longitude=focus_lon,
            zoom=focus_zoom,
            pitch=52,
            bearing=16,
        )

        tooltip = {
            "html": """
            <div style="background:#0b1c30; color:#f8fafc; padding:8px 12px; border-radius:6px; font-family:sans-serif; font-size:12px; line-height:1.45;">
                <b>{name}</b> {site_id}<br/>
                <b>Parcel:</b> {parcel_id} | <b>Farm:</b> {farm_id}<br/>
                <b>Crop:</b> {crop} | <b>Area:</b> {area_ha} ha<br/>
                <b>Slope:</b> {slope_pct}% | <b>Buffer Strip:</b> {buffer_strip}<br/>
                <b>Catchment:</b> {catchment_id}<br/>
                <b>Activities:</b> {activity}
            </div>
            """,
            "style": {"zIndex": "1000"},
        }

        if "satellite" in map_style_choice:
            deck = pdk.Deck(
                layers=layers,
                initial_view_state=initial_view_state,
                map_style=None,
                tooltip=tooltip,
            )
        else:
            selected_style = "light" if "light" in map_style_choice else "dark"
            deck = pdk.Deck(
                layers=layers,
                initial_view_state=initial_view_state,
                map_provider="carto",
                map_style=selected_style,
                tooltip=tooltip,
            )

        st.pydeck_chart(deck, use_container_width=True)
        st.caption("🛰️ **Real-Time 3D Satellite View** · Right-click + drag to tilt/rotate 3D camera · **3D Column Height** = Parcel Area & Runoff Slope Exposure.")

    with geo_tab2:
        if not parcels_df.empty:
            three_html = build_threejs_satellite_3d_terrain_html(
                df=parcels_df,
                title=f"3D Satellite Sourcing Basin — {crop_filter.upper()}",
                lat_col="lat",
                lon_col="lon",
                id_col="parcel_id",
                value_col="area_ha",
                tier_col="tier",
                color_col="hex_color",
                extra_col="info",
                value_unit="ha parcel",
                relief_scale=1.7,
                height_px=520,
            )
            components.html(three_html, height=530, scrolling=False)

    # ── Live Maritime Logistics Panel (Digitraffic Marine API) ────────────────
    st.divider()
    st.markdown("### 🚢 Live Inbound Maritime Traffic (Digitraffic Marine API)")
    st.caption("Real-time automated AIS tracking of commercial vessels arriving at Finnish ports serving Apetit's raw materials (Naantali, Turku, Kantvik).")

    vessels = api.live.get_live_port_calls()
    df_vessels = pd.DataFrame(vessels)
    if not df_vessels.empty:
        df_vessels = df_vessels.rename(columns={
            "vessel_name": "Vessel Name",
            "ship_type": "Vessel Class",
            "port": "Destination Port",
            "eta": "Timestamp / ETA",
            "cargo_relevance": "Supply Chain Relevance",
            "source": "Telemetry Source",
        })
        st.dataframe(df_vessels, use_container_width=True, hide_index=True)

    with st.expander("🔌 Connected Free Public APIs & Telemetry Architecture"):
        st.markdown(
            """
            | API Provider | Endpoint | Authentication | Live Data Supplied |
            |---|---|---|---|
            | **Esri World Imagery** | `arcgisonline.com/ArcGIS/rest/services/World_Imagery` | Free / Open | High-resolution global satellite photography & hybrid labels |
            | **Open-Meteo** | `api.open-meteo.com/v1/forecast` | None (Open Source) | Live temperature, precipitation, wind speed at Säkylä, Kantvik & Bjuv |
            | **Digitraffic (Fintraffic)** | `meri.digitraffic.fi/api/port-call/v1/port-calls` | None (Open Data FI) | Real-time AIS vessel arrivals at Naantali, Turku & Kantvik ports |
            | **Frankfurter (ECB)** | `api.frankfurter.app/latest?from=EUR` | None (Open Data EU) | Official European Central Bank EUR/SEK, EUR/USD, EUR/NOK rates |
            | **Nominatim (OSM)** | `nominatim.openstreetmap.org/search` | None (OpenStreetMap) | Live forward geocoding for Finnish municipalities & farm clusters |
            """
        )
