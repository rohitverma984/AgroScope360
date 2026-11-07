"""
prototype/views/digital_twin_view.py — 3D Interactive Farm Digital Twin
Demeter-style split dashboard:
  Left  → Tab 1: Leaflet.js SATELLITE map (Esri World Imagery, free/no token)
                  with realistic organic irregular field polygons + hover popups + legend
          Tab 2: Plotly 3D Surface terrain (crop biomass topography, freely rotatable)
  Right → Grade cards, Farm Breakdown donut, Crop Rotation Earth-Score, KPI tiles
  Bottom → Financials bar chart, Environmental Strain area chart, AI Advisor
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from core.api import NavigatorAPI
from core.digital_twin_service import DigitalTwinService


# ── Constants ─────────────────────────────────────────────────────────────────

LAT_PER_M = 1.0 / 111_000.0   # 1 m → degrees latitude
LON_PER_M = 1.0 / 54_000.0    # 1 m → degrees longitude at ~61 °N

EARTH_SCORES: dict[str, int] = {
    "pea": 88, "potato": 72, "carrot": 76, "oilseed": 69,
    "barley": 81, "wheat": 78, "oat": 83, "faba bean": 90,
}
ROTATION_PARTNER: dict[str, str] = {
    "pea": "oat", "potato": "pea", "carrot": "barley",
    "oilseed": "wheat", "barley": "pea", "wheat": "oat",
    "oat": "pea", "faba bean": "wheat",
}

CAMERA_PRESETS: dict[str, dict] = {
    "📐 Isometric 3D (Tablet View)": dict(
        eye=dict(x=1.45, y=-1.55, z=1.25),
        center=dict(x=0, y=0, z=-0.1),
    ),
    "🦅 Overhead Drone (Top-Down)": dict(
        eye=dict(x=0.01, y=-0.01, z=2.35),
        center=dict(x=0, y=0, z=0),
    ),
    "🌅 Low Horizon Profile": dict(
        eye=dict(x=2.2, y=-0.9, z=0.45),
        center=dict(x=0, y=0, z=0),
    ),
    "🏠 Farm HQ Close-Up": dict(
        eye=dict(x=0.85, y=-0.85, z=0.55),
        center=dict(x=0.05, y=0.05, z=-0.05),
    ),
}


# ── Helper: realistic field polygon ──────────────────────────────────────────

def _realistic_field_polygon(
    farm_lat: float,
    farm_lon: float,
    area_ha: float,
    idx: int,
    seed: int = 42,
) -> list[list[float]]:
    """
    Generate an organic, irregular field polygon mimicking real Finnish farmland.
    Uses deterministic RNG so shapes are stable across re-renders.
    Finnish fields: elongated strips along drainage ditches, slight rotations,
    irregular quadrilateral edges following terrain/roads.
    """
    rng = np.random.default_rng(seed + idx * 31 + idx ** 2 % 13)

    # ── Field dimensions from area ────────────────────────────────────────────
    side_m = max(90.0, (area_ha * 10_000) ** 0.5)

    # Aspect ratio: mix of square parcels and elongated drainage strips
    aspect = rng.choice([0.8, 1.0, 1.0, 1.3, 1.6, 2.0, 2.5, 3.0, 0.65])
    w_m = side_m * np.sqrt(float(aspect))    # E-W width in metres
    h_m = side_m / np.sqrt(float(aspect))    # N-S height in metres

    # ── Rotation: fields follow drainage, roads, terrain ─────────────────────
    # Finnish fields tend to align N-S or E-W; some diagonal
    dominant_angles = [0, 0, 0, 90, 90, 15, -15, 30, 45, -30]
    base_angle = rng.choice(dominant_angles)
    angle_rad  = np.deg2rad(float(base_angle) + rng.uniform(-8.0, 8.0))

    # ── Layout position: organic clustering, NOT strict grid ─────────────────
    # Sector: each parcel gets a direction quadrant + distance from farm centre
    n_cols    = max(3, int(np.ceil(np.sqrt(16))))           # target ~4-col grid
    grid_col  = idx %  n_cols
    grid_row  = idx // n_cols

    # Grid spacing with jitter for organic feel
    jitter_x = rng.uniform(-0.25, 0.25) * w_m
    jitter_y = rng.uniform(-0.20, 0.20) * h_m

    base_x_m = grid_col * (w_m * 1.14) + jitter_x   # metres E of farm centre
    base_y_m = grid_row * (h_m * 1.14) + jitter_y   # metres N of farm centre

    # ── Irregular corners: each corner shifted independently ─────────────────
    jx = w_m * 0.11
    jy = h_m * 0.11
    corners_local = np.array([
        [-w_m / 2 + rng.uniform(-jx,  jx), -h_m / 2 + rng.uniform(-jy,  jy)],
        [ w_m / 2 + rng.uniform(-jx,  jx), -h_m / 2 + rng.uniform(-jy,  jy)],
        [ w_m / 2 + rng.uniform(-jx,  jx),  h_m / 2 + rng.uniform(-jy,  jy)],
        [-w_m / 2 + rng.uniform(-jx,  jx),  h_m / 2 + rng.uniform(-jy,  jy)],
    ])

    # ── Add a mid-edge point on the longer sides for curved-looking edges ────
    # Insert a mid-point on top and bottom edges with slight bow
    bow = rng.uniform(-h_m * 0.06, h_m * 0.06)
    top_mid    = np.array([rng.uniform(-w_m * 0.1, w_m * 0.1),  h_m / 2 + bow])
    bottom_mid = np.array([rng.uniform(-w_m * 0.1, w_m * 0.1), -h_m / 2 - bow])

    # Build polygon vertices (6-pt = 4 corners + 2 mid-edge points)
    if aspect > 1.5:
        # Elongated strip: add mid-point on long edges for subtle bow
        vertices = np.array([
            corners_local[0],
            bottom_mid,
            corners_local[1],
            corners_local[2],
            top_mid,
            corners_local[3],
        ])
    else:
        vertices = corners_local

    # ── Apply rotation ────────────────────────────────────────────────────────
    cos_a, sin_a = np.cos(angle_rad), np.sin(angle_rad)
    rot = np.array([[cos_a, -sin_a], [sin_a, cos_a]])
    rotated = vertices @ rot.T

    # ── Convert metres offset → lon/lat ──────────────────────────────────────
    result = []
    for dx_m, dy_m in rotated:
        lon = farm_lon + (base_x_m + dx_m) * LON_PER_M
        lat = farm_lat + (base_y_m + dy_m) * LAT_PER_M
        result.append([round(lon, 7), round(lat, 7)])
    result.append(result[0])    # close ring
    return result


# ── Helper: yield → RGBA ──────────────────────────────────────────────────────

def _yield_rgba(y: float, alpha: int = 215) -> list[int]:
    if y >= 3.5:  return [22,  163,  74, alpha]
    if y >= 2.8:  return [134, 239, 172, alpha]
    if y >= 2.1:  return [234, 179,   8, alpha]
    if y >= 1.5:  return [249, 115,  22, alpha]
    return             [239,  68,  68, alpha]


# ── Helper: grade ─────────────────────────────────────────────────────────────

def _grade(score: float) -> tuple[str, str]:
    if score >= 85: return "A",  "#10b981"
    if score >= 75: return "A−", "#22c55e"
    if score >= 65: return "B+", "#84cc16"
    if score >= 55: return "B",  "#eab308"
    if score >= 45: return "B−", "#f97316"
    return "C", "#ef4444"


# ── Helper: grid upsample (no scipy) ─────────────────────────────────────────

def _upsample(Z: np.ndarray, factor: int = 5) -> np.ndarray:
    return np.repeat(np.repeat(Z, factor, axis=0), factor, axis=1)


# ── Leaflet satellite map HTML builder ────────────────────────────────────────

def _build_satellite_html(
    farm_lat: float,
    farm_lon: float,
    parcels_data: list[dict],
    farm_id: str,
) -> str:
    """
    Build a self-contained Leaflet.js page with:
    - Esri World Imagery satellite base tiles (free, no token)
    - Esri Reference labels overlay (roads, place names)
    - GeoJSON polygon layer for farm parcels (semi-transparent coloured fills)
    - Hover highlight + click popup for each parcel
    - Blue Farm HQ circle marker + label
    - Bottom-right legend + scale bar
    """
    features: list[dict] = []
    for p in parcels_data:
        r, g, b = p["fill_color"][:3]
        features.append({
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [p["polygon"]]},
            "properties": {
                "parcel_id":  str(p["parcel_id"]),
                "sim_yield":  p["sim_yield"],
                "area_ha":    p["area_ha"],
                "soil":       p["soil"],
                "slope":      p["slope"],
                "dist_water": p["dist_water"],
                "buffer":     p["buffer"],
                "fill_r": r, "fill_g": g, "fill_b": b,
            },
        })

    geojson_js = json.dumps({"type": "FeatureCollection", "features": features})

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  html,body {{ height:100%; background:#0a0f1e; }}
  #map {{
    height: 500px; width: 100%;
    border-radius: 10px;
    border: 1px solid #1e3a5f;
    box-shadow: 0 4px 24px rgba(0,0,0,.6);
  }}

  /* ── Popup ─────────────────────────────────── */
  .leaflet-popup-content-wrapper {{
    background: rgba(10,15,30,0.95) !important;
    color: #f1f5f9 !important;
    border: 1px solid #334155 !important;
    border-radius: 10px !important;
    box-shadow: 0 8px 32px rgba(0,0,0,.7) !important;
    backdrop-filter: blur(12px);
  }}
  .leaflet-popup-content {{ margin: 12px 16px !important; line-height: 1.7; font-size: 12.5px; }}
  .leaflet-popup-tip {{ background: rgba(10,15,30,.95) !important; }}
  .leaflet-popup-close-button {{ color: #64748b !important; font-size: 18px !important; top: 8px !important; right: 10px !important; }}
  .popup-title {{ font-size: 14px; font-weight: 700; color: #38bdf8; }}
  .popup-divider {{ border: none; border-top: 1px solid #1e3a5f; margin: 5px 0; }}

  /* ── Legend ────────────────────────────────── */
  .legend {{
    background: rgba(10,15,30,0.90);
    color: #e2e8f0;
    padding: 10px 14px;
    border-radius: 8px;
    font-size: 11.5px;
    border: 1px solid #334155;
    backdrop-filter: blur(10px);
    line-height: 2.0;
    min-width: 190px;
  }}
  .legend b {{ font-size: 12px; color: #94a3b8; }}
  .ld {{
    display: inline-block;
    width: 13px; height: 13px;
    border-radius: 3px;
    margin-right: 5px;
    vertical-align: middle;
    border: 1px solid rgba(255,255,255,0.25);
  }}

  /* ── HQ label ──────────────────────────────── */
  .hq-label {{
    background: rgba(37,99,235,0.92);
    color: white;
    padding: 3px 9px;
    border-radius: 20px;
    font-weight: 700;
    font-size: 11px;
    border: 2px solid rgba(255,255,255,0.8);
    white-space: nowrap;
    box-shadow: 0 2px 10px rgba(0,0,0,.5);
    backdrop-filter: blur(4px);
  }}

  /* ── Attribution tweak ─────────────────────── */
  .leaflet-control-attribution {{
    background: rgba(10,15,30,0.80) !important;
    color: #64748b !important;
    font-size: 10px !important;
  }}
  .leaflet-control-attribution a {{ color: #38bdf8 !important; }}
  .leaflet-control-scale-line {{
    background: rgba(10,15,30,0.80) !important;
    color: #94a3b8 !important;
    border-color: #334155 !important;
  }}
</style>
</head>
<body>
<div id="map"></div>
<script>
// ── Map initialisation ─────────────────────────────────────────────────────
var map = L.map('map', {{
  center: [{farm_lat}, {farm_lon}],
  zoom: 14,
  zoomControl: true,
  attributionControl: true,
}});

// ── Esri World Imagery — free satellite tiles ──────────────────────────────
L.tileLayer(
  'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}',
  {{
    attribution: '© Esri — Source: Esri, Maxar, Earthstar Geographics, GeoEye, USDA FSA, USGS, AeroGRID, IGN',
    maxZoom: 20,
  }}
).addTo(map);

// ── Esri Reference Labels (place names, roads) — 50 % opacity ─────────────
L.tileLayer(
  'https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{{z}}/{{y}}/{{x}}',
  {{ opacity: 0.50, maxZoom: 20, attribution: '' }}
).addTo(map);

// ── Farm parcel polygons ───────────────────────────────────────────────────
var geojsonData = {geojson_js};

var geojsonLayer = L.geoJSON(geojsonData, {{
  style: function(f) {{
    var p = f.properties;
    return {{
      fillColor   : 'rgb(' + p.fill_r + ',' + p.fill_g + ',' + p.fill_b + ')',
      fillOpacity : 0.58,
      color       : 'rgba(255,255,255,0.88)',
      weight      : 1.8,
      opacity     : 1.0,
    }};
  }},

  onEachFeature: function(f, layer) {{
    var p = f.properties;
    var emoji = p.sim_yield >= 3.5 ? '🟢' :
                p.sim_yield >= 2.8 ? '🟩' :
                p.sim_yield >= 2.1 ? '🟡' :
                p.sim_yield >= 1.5 ? '🟠' : '🔴';

    layer.bindPopup(
      '<div class="popup-title">📍 Parcel ' + p.parcel_id + '</div>' +
      '<hr class="popup-divider"/>' +
      emoji + ' <b>Simulated Yield:</b> ' + p.sim_yield + ' t/ha<br/>' +
      '📐 <b>Area:</b> ' + p.area_ha + ' ha<br/>' +
      '🌱 <b>Soil:</b> ' + p.soil + '<br/>' +
      '⛰️ <b>Slope:</b> ' + p.slope + ' %<br/>' +
      '💧 <b>Nearest Ditch:</b> ' + p.dist_water + ' m<br/>' +
      '🏞️ <b>Buffer Strip:</b> ' + p.buffer,
      {{ maxWidth: 230 }}
    );

    layer.on('mouseover', function() {{
      this.setStyle({{ weight: 3.5, color: '#fbbf24', fillOpacity: 0.80 }});
      this.bringToFront();
    }});
    layer.on('mouseout', function() {{
      geojsonLayer.resetStyle(this);
    }});
  }},
}}).addTo(map);

// ── Farm HQ marker ────────────────────────────────────────────────────────
var hqIcon = L.divIcon({{
  html: '<div class="hq-label">🏭 Farm {farm_id}</div>',
  className: '',
  iconAnchor: [45, 12],
}});
L.marker([{farm_lat}, {farm_lon}], {{ icon: hqIcon }})
  .bindPopup('<b style="color:#38bdf8;">Farm {farm_id}</b><br/>📦 HQ & Cold Storage Hub<br/>📍 {farm_lat:.5f} °N, {farm_lon:.5f} °E')
  .addTo(map);

// Blue dot at farm centre
L.circleMarker([{farm_lat}, {farm_lon}], {{
  radius: 7, fillColor: '#3b82f6', color: '#fff',
  weight: 2.5, opacity: 1, fillOpacity: 1,
}}).addTo(map);

// ── Legend control ─────────────────────────────────────────────────────────
var legend = L.control({{ position: 'bottomright' }});
legend.onAdd = function() {{
  var div = L.DomUtil.create('div', 'legend');
  div.innerHTML =
    '<b>🌾 Crop Yield Stress</b><br/>' +
    '<span class="ld" style="background:rgb(22,163,74)"></span>Optimal (≥ 3.5 t/ha)<br/>' +
    '<span class="ld" style="background:rgb(134,239,172)"></span>Good (2.8 – 3.5)<br/>' +
    '<span class="ld" style="background:rgb(234,179,8)"></span>Mild Stress (2.1 – 2.8)<br/>' +
    '<span class="ld" style="background:rgb(249,115,22)"></span>Drought Risk (1.5 – 2.1)<br/>' +
    '<span class="ld" style="background:rgb(239,68,68)"></span>Severe Deficit (< 1.5)<br/>' +
    '<span class="ld" style="background:#3b82f6;border-radius:50%;"></span>Farm HQ / Silo';
  return div;
}};
legend.addTo(map);

// ── Scale bar ──────────────────────────────────────────────────────────────
L.control.scale({{ imperial: false, maxWidth: 150, position: 'bottomleft' }}).addTo(map);

// ── Auto-fit to parcel bounds ──────────────────────────────────────────────
if (geojsonData.features.length > 0) {{
  try {{
    map.fitBounds(geojsonLayer.getBounds().pad(0.12));
  }} catch(e) {{ /* fallback to default centre */ }}
}}
</script>
</body>
</html>"""


# ── True 3D Satellite Draped Terrain HTML Builder (Three.js WebGL) ────────────

def _build_satellite_3d_html(
    farm_lat: float,
    farm_lon: float,
    parcels_raw: pd.DataFrame,
    farm_id: str,
    crop: str,
    base_yield: float,
    sim_mult: float,
    sim_temp: float,
    sim_precip: float,
    opt_buffer: bool,
    relief_scale: float = 1.6,
) -> str:
    """
    Constructs a true photorealistic 3D satellite simulation:
    - Fetches high-resolution satellite photography from Esri World Imagery
    - Drapes the satellite imagery directly onto a 3D Finnish moraine elevation mesh
    - Carves the drainage ditch and raises physical 3D vegetative crop canopies
    - Places Finnish red barn & grain silo at Farm HQ
    - Places 3D floating parcel beacons with live raycasted hover tooltips
    - OrbitControls for effortless 360° rotation, tilt, and zoom
    """
    lon_min = float(parcels_raw["lon"].min())
    lon_max = float(parcels_raw["lon"].max())
    lat_min = float(parcels_raw["lat"].min())
    lat_max = float(parcels_raw["lat"].max())

    pad_lon = max((lon_max - lon_min) * 0.35, 0.012)
    pad_lat = max((lat_max - lat_min) * 0.35, 0.009)
    min_lon, max_lon = lon_min - pad_lon, lon_max + pad_lon
    min_lat, max_lat = lat_min - pad_lat, lat_max + pad_lat

    bbox = f"{min_lon:.5f},{min_lat:.5f},{max_lon:.5f},{max_lat:.5f}"
    sat_url = (
        f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export"
        f"?bbox={bbox}&bboxSR=4326&imageSR=4326&size=1024,1024&format=jpg&f=image"
    )

    parcels_list = []
    for idx, (_, r) in enumerate(parcels_raw.iterrows()):
        u = (float(r["lon"]) - min_lon) / max(max_lon - min_lon, 0.0001)
        v = (float(r["lat"]) - min_lat) / max(max_lat - min_lat, 0.0001)
        px = -50.0 + u * 100.0
        pz = 50.0 - v * 100.0
        area = float(r["area_ha"])
        hw = max(2.8, np.sqrt(area) * 2.2)
        hh = max(2.8, np.sqrt(area) * 1.8)

        slope_mod = 1.0 - (float(r["slope_pct"]) * 0.02)
        p_yield = base_yield * sim_mult * slope_mod

        if p_yield >= 3.5:
            col = "#16a34a"
        elif p_yield >= 2.8:
            col = "#84cc16"
        elif p_yield >= 2.1:
            col = "#eab308"
        else:
            col = "#ef4444"

        parcels_list.append({
            "idx": idx,
            "parcel_id": str(r["parcel_id"]),
            "px": round(px, 2),
            "pz": round(pz, 2),
            "hw": round(hw, 2),
            "hh": round(hh, 2),
            "sim_yield": round(p_yield, 2),
            "area_ha": round(area, 1),
            "soil": str(r["soil_class_soilmap"]).title(),
            "slope": round(float(r["slope_pct"]), 1),
            "dist_water": int(r["dist_to_water_m"]),
            "buffer": "Protected ✓" if r["buffer_strip"] else "Missing ✗",
            "color": col,
        })

    parcels_json = json.dumps(parcels_list)
    show_buffer_js = "true" if opt_buffer else "false"

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  html, body {{ width:100%; height:100%; overflow:hidden; background:#0a0f1e; font-family:-apple-system,BlinkMacSystemFont,sans-serif; }}
  #container {{ width:100%; height:520px; position:relative; border-radius:10px; border:1px solid #1e3a5f; overflow:hidden; }}
  #canvas-target {{ width:100%; height:100%; }}
  .toolbar {{
    position:absolute; top:12px; left:12px; z-index:10;
    display:flex; gap:6px; flex-wrap:wrap; align-items:center;
    background:rgba(10, 15, 30, 0.88); backdrop-filter:blur(12px);
    border:1px solid #334155; border-radius:8px; padding:6px 10px;
    box-shadow:0 4px 20px rgba(0,0,0,0.6);
  }}
  .tool-btn {{
    background:#1e293b; color:#f1f5f9; border:1px solid #475569;
    border-radius:6px; padding:4px 9px; font-size:11px; font-weight:600;
    cursor:pointer; transition:all 0.15s ease;
  }}
  .tool-btn:hover {{ background:#2563eb; border-color:#60a5fa; color:#fff; }}
  .tool-btn.active {{ background:#0284c7; border-color:#38bdf8; color:#fff; }}
  #tooltip {{
    position:absolute; display:none; z-index:25;
    background:rgba(10, 15, 30, 0.95); color:#f8fafc;
    border:1px solid #38bdf8; border-radius:8px; padding:10px 14px;
    font-size:12px; line-height:1.65; pointer-events:none;
    box-shadow:0 10px 30px rgba(0,0,0,0.85); backdrop-filter:blur(10px);
    min-width:210px;
  }}
  .legend-bar {{
    position:absolute; bottom:12px; right:12px; z-index:10;
    background:rgba(10, 15, 30, 0.88); backdrop-filter:blur(10px);
    border:1px solid #334155; border-radius:8px; padding:8px 12px;
    color:#cbd5e1; font-size:11px; line-height:1.9;
  }}
  .ld {{ display:inline-block; width:11px; height:11px; border-radius:2px; margin-right:5px; vertical-align:middle; }}
</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
</head>
<body>
<div id="container">
  <div class="toolbar">
    <button class="tool-btn active" id="btn-iso" onclick="setCamera('iso')">📐 Isometric 3D</button>
    <button class="tool-btn" id="btn-drone" onclick="setCamera('drone')">🦅 Overhead Drone</button>
    <button class="tool-btn" id="btn-horizon" onclick="setCamera('horizon')">🌅 Horizon Profile</button>
    <button class="tool-btn" id="btn-hq" onclick="setCamera('hq')">🏠 Farm HQ</button>
    <button class="tool-btn" id="btn-rot" onclick="toggleRotate()">🔄 Auto-Rotate</button>
    <button class="tool-btn active" id="btn-tint" onclick="toggleOverlay()">👁️ Field Overlay</button>
  </div>
  <div id="tooltip"></div>
  <div class="legend-bar">
    <b style="color:#38bdf8;">🛰️ Satellite 3D Terrain</b><br/>
    <span class="ld" style="background:#16a34a;"></span>Optimal Yield (≥3.5 t/ha)<br/>
    <span class="ld" style="background:#84cc16;"></span>Good Crop (2.8–3.5)<br/>
    <span class="ld" style="background:#eab308;"></span>Mild Stress (2.1–2.8)<br/>
    <span class="ld" style="background:#ef4444;"></span>Drought Stress (&lt;2.1)<br/>
    <span class="ld" style="background:#b91c1c;"></span>Red Barn &amp; Silo
  </div>
  <div id="canvas-target"></div>
</div>
<script>
const satUrl = "{sat_url}";
const parcels = {parcels_json};
const reliefScale = {relief_scale};
const showBuffer = {show_buffer_js};

const container = document.getElementById('canvas-target');
const tooltip = document.getElementById('tooltip');

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0a0f1e);
scene.fog = new THREE.FogExp2(0x0a0f1e, 0.0035);

const camera = new THREE.PerspectiveCamera(40, container.clientWidth / container.clientHeight, 0.5, 1000);
camera.position.set(65, 68, 75);

const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
renderer.setSize(container.clientWidth, container.clientHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
container.appendChild(renderer.domElement);

const controls = new THREE.OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.06;
controls.maxPolarAngle = Math.PI / 2.05;
controls.minDistance = 25;
controls.maxDistance = 260;
controls.target.set(0, 0, 0);

// Lighting
const sunLight = new THREE.DirectionalLight(0xfff7ed, 1.4);
sunLight.position.set(60, 110, 50);
scene.add(sunLight);

const ambientLight = new THREE.AmbientLight(0xffffff, 0.75);
scene.add(ambientLight);

const blueFill = new THREE.DirectionalLight(0x93c5fd, 0.35);
blueFill.position.set(-60, 40, -50);
scene.add(blueFill);

// Topography calculation
function getElevation(x, z) {{
  let elev = (1.8 * Math.sin(x * 0.038) + 1.4 * Math.cos(z * 0.032)) * reliefScale;
  const ditch_z = 2 + 12 * Math.sin(x * 0.045);
  const dist_ditch = Math.abs(z - ditch_z);
  elev -= 1.8 * reliefScale * Math.exp(-(dist_ditch * dist_ditch) / 16.0);
  return elev;
}}

// 3D Terrain Plane
const geom = new THREE.PlaneGeometry(100, 100, 85, 85);
geom.rotateX(-Math.PI / 2);

const pos = geom.attributes.position.array;
for (let i = 0; i < pos.length; i += 3) {{
  const vx = pos[i];
  const vz = pos[i + 2];
  let vy = getElevation(vx, vz);
  for (let j = 0; j < parcels.length; j++) {{
    const p = parcels[j];
    if (Math.abs(vx - p.px) <= p.hw && Math.abs(vz - p.pz) <= p.hh) {{
      vy += 0.40 * reliefScale * (p.sim_yield / 3.0);
      break;
    }}
  }}
  pos[i + 1] = vy;
}}
geom.computeVertexNormals();

// Load Esri World Imagery Satellite Texture
const textureLoader = new THREE.TextureLoader();
textureLoader.setCrossOrigin('anonymous');
const satTexture = textureLoader.load(satUrl, function() {{
  renderer.render(scene, camera);
}});
satTexture.generateMipmaps = true;

const terrainMat = new THREE.MeshStandardMaterial({{
  map: satTexture,
  roughness: 0.88,
  metalness: 0.08,
}});
const terrain = new THREE.Mesh(geom, terrainMat);
scene.add(terrain);

// Overlay group for parcels
const overlayGroup = new THREE.Group();
const interactiveObjects = [];

parcels.forEach((p) => {{
  const cy = getElevation(p.px, p.pz) + 0.35 * reliefScale * (p.sim_yield / 3.0);

  // Translucent 3D parcel box
  const boxGeom = new THREE.BoxGeometry(p.hw * 2, 0.25 * reliefScale, p.hh * 2);
  const boxMat = new THREE.MeshStandardMaterial({{
    color: new THREE.Color(p.color),
    transparent: true,
    opacity: 0.42,
    roughness: 0.6,
  }});
  const boxMesh = new THREE.Mesh(boxGeom, boxMat);
  boxMesh.position.set(p.px, cy + 0.12 * reliefScale, p.pz);

  // Border edges
  const edges = new THREE.EdgesGeometry(boxGeom);
  const line = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({{
    color: 0xffffff,
    transparent: true,
    opacity: 0.75,
  }}));
  boxMesh.add(line);

  boxMesh.userData = p;
  overlayGroup.add(boxMesh);
  interactiveObjects.push(boxMesh);

  // Floating Diamond Pin
  const pinGeom = new THREE.OctahedronGeometry(1.2);
  const pinMat = new THREE.MeshStandardMaterial({{
    color: new THREE.Color(p.color),
    emissive: new THREE.Color(p.color),
    emissiveIntensity: 0.45,
    roughness: 0.3,
  }});
  const pin = new THREE.Mesh(pinGeom, pinMat);
  pin.position.set(p.px, cy + 2.5 * reliefScale, p.pz);
  pin.userData = p;
  overlayGroup.add(pin);
  interactiveObjects.push(pin);
}});
scene.add(overlayGroup);

// Farm HQ Landmark: Red Barn + Silo
const hq_x = 0.0, hq_z = 0.0;
const hq_y = getElevation(hq_x, hq_z);

// Finnish Red Barn
const barnMat = new THREE.MeshStandardMaterial({{ color: 0xb91c1c, roughness: 0.7 }});
const barn = new THREE.Mesh(new THREE.BoxGeometry(5.0, 2.8, 3.8), barnMat);
barn.position.set(hq_x - 2.5, hq_y + 1.4, hq_z);
scene.add(barn);

const roofMat = new THREE.MeshStandardMaterial({{ color: 0x450a0a, roughness: 0.5 }});
const roof = new THREE.Mesh(new THREE.ConeGeometry(3.2, 1.8, 4), roofMat);
roof.rotation.y = Math.PI / 4;
roof.position.set(hq_x - 2.5, hq_y + 3.6, hq_z);
scene.add(roof);

// Silver Silo
const siloMat = new THREE.MeshStandardMaterial({{ color: 0x38bdf8, metalness: 0.6, roughness: 0.3 }});
const silo = new THREE.Mesh(new THREE.CylinderGeometry(1.5, 1.5, 6.5, 16), siloMat);
silo.position.set(hq_x + 2.5, hq_y + 3.2, hq_z);
scene.add(silo);

// Buffer Trees
if (showBuffer) {{
  const treeMat = new THREE.MeshStandardMaterial({{ color: 0x14532d, roughness: 0.9 }});
  for (let x = -40; x <= 40; x += 6.5) {{
    const tz = 2 + 12 * Math.sin(x * 0.045) + 3.5;
    const ty = getElevation(x, tz);
    const tree = new THREE.Mesh(new THREE.ConeGeometry(1.1, 3.2, 5), treeMat);
    tree.position.set(x, ty + 1.6, tz);
    scene.add(tree);
  }}
}}

// Camera views
window.setCamera = function(type) {{
  document.querySelectorAll('.tool-btn').forEach(b => b.classList.remove('active'));
  if (type === 'iso') {{
    document.getElementById('btn-iso').classList.add('active');
    camera.position.set(65, 68, 75);
    controls.target.set(0, 0, 0);
  }} else if (type === 'drone') {{
    document.getElementById('btn-drone').classList.add('active');
    camera.position.set(0.01, 115, 0.01);
    controls.target.set(0, 0, 0);
  }} else if (type === 'horizon') {{
    document.getElementById('btn-horizon').classList.add('active');
    camera.position.set(90, 16, 20);
    controls.target.set(0, 0, 0);
  }} else if (type === 'hq') {{
    document.getElementById('btn-hq').classList.add('active');
    camera.position.set(hq_x + 16, hq_y + 14, hq_z + 20);
    controls.target.set(hq_x, hq_y, hq_z);
  }}
  controls.update();
}};

window.toggleRotate = function() {{
  controls.autoRotate = !controls.autoRotate;
  controls.autoRotateSpeed = 1.2;
  const btn = document.getElementById('btn-rot');
  if (controls.autoRotate) btn.classList.add('active');
  else btn.classList.remove('active');
}};

window.toggleOverlay = function() {{
  overlayGroup.visible = !overlayGroup.visible;
  const btn = document.getElementById('btn-tint');
  if (overlayGroup.visible) btn.classList.add('active');
  else btn.classList.remove('active');
}};

// Raycasting for interactive hover
const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();

container.addEventListener('mousemove', function(e) {{
  const rect = container.getBoundingClientRect();
  mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
  mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

  raycaster.setFromCamera(mouse, camera);
  const intersects = raycaster.intersectObjects(interactiveObjects);

  if (intersects.length > 0) {{
    const p = intersects[0].object.userData;
    tooltip.style.display = 'block';
    tooltip.style.left = (e.clientX - rect.left + 16) + 'px';
    tooltip.style.top = (e.clientY - rect.top + 16) + 'px';

    const emoji = p.sim_yield >= 3.5 ? '🟢' : (p.sim_yield >= 2.8 ? '🟩' : (p.sim_yield >= 2.1 ? '🟡' : '🔴'));
    tooltip.innerHTML =
      '<b style="font-size:14px;color:#38bdf8;">📍 Parcel ' + p.parcel_id + '</b><hr style="border:none;border-top:1px solid #334155;margin:5px 0;">' +
      emoji + ' <b>Sim. Yield:</b> ' + p.sim_yield + ' t/ha<br/>' +
      '📐 <b>Area:</b> ' + p.area_ha + ' ha &nbsp;|&nbsp; <b>Soil:</b> ' + p.soil + '<br/>' +
      '⛰️ <b>Slope:</b> ' + p.slope + '% &nbsp;|&nbsp; <b>To Ditch:</b> ' + p.dist_water + ' m<br/>' +
      '🏞️ <b>Buffer Strip:</b> ' + p.buffer;
  }} else {{
    tooltip.style.display = 'none';
  }}
}});

container.addEventListener('mouseleave', function() {{
  tooltip.style.display = 'none';
}});

// Animation loop
function animate() {{
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
}}
animate();

window.addEventListener('resize', function() {{
  camera.aspect = container.clientWidth / container.clientHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(container.clientWidth, container.clientHeight);
}});
</script>
</body>
</html>"""


# ── Photorealistic 3D Farm Terrain Generator ─────────────────────────────────

def _build_photorealistic_3d_terrain(
    parcels_df: pd.DataFrame,
    farm_id: str,
    crop: str,
    base_yield: float,
    sim_mult: float,
    sim_temp: float,
    sim_precip: float,
    opt_buffer: bool,
    mode: str,
    camera_key: str,
    vertical_scale: float,
) -> go.Figure:
    """
    Constructs an interactive, realistic 3D agricultural landscape featuring:
    - Finnish moraine rolling topography with carved drainage stream
    - Discrete field parcels with realistic crop canopy heights
    - Unpaved tractor farm lanes framing each field
    - Finnish red barn & silver grain silo at Farm HQ
    - 3D interactive parcel pins with hover details
    - Riparian buffer trees along the stream
    - One-click camera presets matching tablet perspective
    """
    N = 65
    x_grid = np.linspace(0, 100, N)
    y_grid = np.linspace(0, 100, N)
    X, Y = np.meshgrid(x_grid, y_grid)

    # 1. Base Topography: Gentle rolling Finnish moraine terrain
    Z = (1.5 * np.sin(X * 0.038) + 1.2 * np.cos(Y * 0.032)) * vertical_scale

    # 2. Drainage ditch / stream depression
    ditch_y = 48 + 14 * np.sin(X * 0.045)
    dist_ditch = np.abs(Y - ditch_y)
    Z -= 1.6 * vertical_scale * np.exp(-(dist_ditch**2) / 14.0)

    # 3. Spatial projection of field parcels
    parcels_local = parcels_df.copy()
    lon_min, lon_max = parcels_local["lon"].min(), parcels_local["lon"].max()
    lat_min, lat_max = parcels_local["lat"].min(), parcels_local["lat"].max()
    d_lon = max(lon_max - lon_min, 0.001)
    d_lat = max(lat_max - lat_min, 0.001)

    parcels_local["px"] = 14.0 + ((parcels_local["lon"] - lon_min) / d_lon) * 72.0
    parcels_local["py"] = 14.0 + ((parcels_local["lat"] - lat_min) / d_lat) * 72.0

    # Surface color matrix
    if "Realistic" in mode:
        C = np.full_like(Z, 5.0)  # default pasture
        C[dist_ditch < 2.6] = 0.0  # water stream
        C[(dist_ditch >= 2.6) & (dist_ditch < 5.2)] = 2.0  # buffer strip
    else:
        C = np.full_like(Z, base_yield)  # continuous yield heatmap

    beacon_x, beacon_y, beacon_z = [], [], []
    beacon_text, beacon_hover, beacon_colors = [], [], []

    for _, r in parcels_local.iterrows():
        cx, cy = float(r["px"]), float(r["py"])
        area = float(r["area_ha"])
        hw = max(3.5, np.sqrt(area) * 2.6)
        hh = max(3.5, np.sqrt(area) * 2.2)

        mask = (np.abs(X - cx) <= hw) & (np.abs(Y - cy) <= hh)
        border = mask & ((np.abs(X - cx) >= hw - 1.2) | (np.abs(Y - cy) >= hh - 1.2))
        inside = mask & ~border

        slope_mod = 1.0 - (float(r["slope_pct"]) * 0.02)
        p_yield = base_yield * sim_mult * slope_mod

        if "Realistic" in mode:
            C[border] = 1.0  # unpaved tractor road
            if p_yield >= 3.5:
                val, b_col = 6.0, "#15803d"
            elif p_yield >= 2.8:
                val, b_col = 5.0, "#84cc16"
            elif p_yield >= 2.1:
                val, b_col = 4.0, "#eab308"
            else:
                val, b_col = 3.0, "#ef4444"
            C[inside] = val
        else:
            C[mask] = p_yield

        # Physical canopy elevation: higher-yielding crops create realistic 3D vegetative canopy
        Z[inside] += 0.35 * vertical_scale * (p_yield / 3.0)

        xi = int(np.clip(cx * (N / 100.0), 0, N - 1))
        yi = int(np.clip(cy * (N / 100.0), 0, N - 1))
        zc = Z[yi, xi]

        pid = str(r["parcel_id"]).split("-")[-1]
        beacon_x.append(cx)
        beacon_y.append(cy)
        beacon_z.append(zc + 1.2 * vertical_scale)
        beacon_text.append(f"{pid}: {p_yield:.1f}t")
        buf_txt = "Protected ✓" if r["buffer_strip"] else "Missing ✗"
        beacon_hover.append(
            f"<b>Parcel {r['parcel_id']}</b><br>"
            f"🌾 Crop: {crop.title()}<br>"
            f"📊 Sim. Yield: <b>{p_yield:.2f} t/ha</b><br>"
            f"📐 Area: {area:.1f} ha | Soil: {str(r['soil_class_soilmap']).title()}<br>"
            f"⛰️ Slope: {r['slope_pct']}% | To Ditch: {r['dist_to_water_m']} m<br>"
            f"🏞️ Buffer Strip: {buf_txt}"
        )
        if "Realistic" in mode:
            beacon_colors.append(b_col)
        else:
            beacon_colors.append(p_yield)

    fig = go.Figure()

    if "Realistic" in mode:
        discrete_colorscale = [
            [0.00, "#0284c7"], [0.14, "#0284c7"],  # 0: Water
            [0.15, "#78350f"], [0.28, "#78350f"],  # 1: Dirt road
            [0.29, "#14532d"], [0.42, "#14532d"],  # 2: Buffer trees
            [0.43, "#ef4444"], [0.57, "#ef4444"],  # 3: Stress
            [0.58, "#eab308"], [0.71, "#eab308"],  # 4: Golden harvest
            [0.72, "#84cc16"], [0.85, "#84cc16"],  # 5: Healthy
            [0.86, "#15803d"], [1.00, "#15803d"],  # 6: Optimal
        ]
        fig.add_trace(go.Surface(
            x=X, y=Y, z=Z, surfacecolor=C,
            cmin=0, cmax=6, colorscale=discrete_colorscale,
            showscale=False,
            lighting=dict(ambient=0.75, diffuse=0.9, roughness=0.35, specular=0.25),
            lightposition=dict(x=120, y=200, z=400),
            hovertemplate="<b>Agricultural Surface</b><br>Elevation: %{z:.1f} m<extra></extra>",
        ))
    else:
        fig.add_trace(go.Surface(
            x=X, y=Y, z=Z, surfacecolor=C,
            colorscale=[
                [0.00, "#7f1d1d"], [0.25, "#ef4444"],
                [0.45, "#f97316"], [0.60, "#eab308"],
                [0.78, "#86efac"], [1.00, "#15803d"],
            ],
            cmin=1.0, cmax=max(4.5, float(np.max(C))),
            colorbar=dict(
                title=dict(text="Yield<br>(t/ha)", side="right", font=dict(size=11)),
                tickfont=dict(size=10, color="#cbd5e1"), len=0.65, x=1.0,
            ),
            lighting=dict(ambient=0.7, diffuse=0.85, roughness=0.4, specular=0.2),
            lightposition=dict(x=120, y=200, z=400),
            hovertemplate="<b>Simulated Yield</b><br>%{surfacecolor:.2f} t/ha<extra></extra>",
        ))

    # 3D Field Parcel Pins
    fig.add_trace(go.Scatter3d(
        x=beacon_x, y=beacon_y, z=beacon_z,
        mode="markers+text",
        marker=dict(
            size=7,
            color=beacon_colors,
            colorscale="Viridis" if "Heatmap" in mode else None,
            symbol="diamond",
            line=dict(color="#ffffff", width=1.5),
        ),
        text=beacon_text,
        textposition="top center",
        textfont=dict(size=9.5, color="#ffffff"),
        hovertext=beacon_hover,
        hoverinfo="text",
        name="Field Parcels",
    ))

    # Farm HQ Landmark
    hq_x, hq_y = 50.0, 50.0
    hq_z = Z[int(N / 2), int(N / 2)]
    fig.add_trace(go.Scatter3d(
        x=[hq_x, hq_x + 3.0],
        y=[hq_y, hq_y - 2.0],
        z=[hq_z + 1.5 * vertical_scale, hq_z + 2.8 * vertical_scale],
        mode="markers+text",
        marker=dict(
            size=[13, 16],
            color=["#b91c1c", "#38bdf8"],
            symbol=["square", "diamond"],
            line=dict(color="#ffffff", width=2),
        ),
        text=["Barn", "HQ Silo"],
        textposition="top center",
        textfont=dict(size=10, color="#38bdf8"),
        hovertext=[
            f"<b>Farm {farm_id} Barn</b><br>Storage & Equipment Depot",
            f"<b>Farm {farm_id} Silo & HQ</b><br>Cold Storage & Sorting Hub",
        ],
        hoverinfo="text",
        name="Farm HQ",
    ))

    # Riparian buffer trees along water stream
    if opt_buffer:
        ditch_sample_x = np.linspace(10, 90, 14)
        ditch_sample_y = 48 + 14 * np.sin(ditch_sample_x * 0.045) + 3.8
        ditch_sample_z = [
            Z[int(np.clip(y * (N / 100.0), 0, N - 1)), int(np.clip(x * (N / 100.0), 0, N - 1))] + 0.6 * vertical_scale
            for x, y in zip(ditch_sample_x, ditch_sample_y)
        ]
        fig.add_trace(go.Scatter3d(
            x=ditch_sample_x, y=ditch_sample_y, z=ditch_sample_z,
            mode="markers",
            marker=dict(size=5, color="#15803d", symbol="circle", opacity=0.9),
            hoverinfo="text",
            hovertext=["🌲 Riparian Buffer Strip (SBTN Soil & Runoff Protection)"] * len(ditch_sample_x),
            name="Buffer Trees",
        ))

    cam = CAMERA_PRESETS.get(camera_key, CAMERA_PRESETS["📐 Isometric 3D (Tablet View)"])

    fig.update_layout(
        height=510,
        margin=dict(l=0, r=0, t=10, b=0),
        scene=dict(
            xaxis=dict(showticklabels=False, showgrid=False, title="", showbackground=True,
                       backgroundcolor="#0f172a", gridcolor="#1e3a5f"),
            yaxis=dict(showticklabels=False, showgrid=False, title="", showbackground=True,
                       backgroundcolor="#0f172a", gridcolor="#1e3a5f"),
            zaxis=dict(title="Topography / Canopy (m)", tickfont=dict(size=9, color="#94a3b8"),
                       showbackground=True, backgroundcolor="#0a0f1e",
                       gridcolor="#1e3a5f", zerolinecolor="#334155"),
            camera=cam,
            bgcolor="#0a0f1e",
            aspectmode="manual",
            aspectratio=dict(x=1.35, y=1.0, z=0.45 * vertical_scale),
        ),
        paper_bgcolor="#0f172a",
        font=dict(color="#f8fafc"),
        legend=dict(
            orientation="h", yanchor="bottom", y=0.01, xanchor="left", x=0.01,
            font=dict(size=10, color="#94a3b8"), bgcolor="rgba(15,23,42,0.85)"
        ),
        annotations=[dict(
            text=f"<b>{farm_id}</b> · {crop.title()} · +{sim_temp:.1f}°C / {sim_precip:+.0f}% rain",
            xref="paper", yref="paper", x=0.01, y=0.99,
            showarrow=False, font=dict(size=11, color="#94a3b8"), align="left",
        )],
    )
    return fig


# ── Main render ───────────────────────────────────────────────────────────────

def render(root: Path) -> None:
    api = NavigatorAPI(root)
    if not hasattr(api, "twin"):
        api.twin = DigitalTwinService(root)

    # ─── Title ────────────────────────────────────────────────────────────────
    st.title("🌾 Farm Digital Twin — 3D Interactive Model")
    st.caption(
        "Select a contract farm · explore the satellite aerial map · "
        "run climate scenario simulations · review agronomic grade scores."
    )

    # ─── Farm selector ────────────────────────────────────────────────────────
    farms_catalog = api.twin.get_farms_catalog()
    farm_options  = {f["label"]: f["farm_id"] for f in farms_catalog}

    sel_col, badge_col = st.columns([3, 1])
    with sel_col:
        selected_label = st.selectbox("Select Contract Farm:", list(farm_options.keys()), index=0)
    selected_fid = farm_options[selected_label]
    farm_data    = api.twin.get_farm_details(selected_fid)
    stats        = farm_data["stats"]
    parcels_raw  = farm_data["parcels"]
    crop         = str(farm_data.get("crop") or "pea").lower()
    farm_lat     = farm_data["lat"]
    farm_lon     = farm_data["lon"]

    with badge_col:
        badges = []
        if farm_data["organic_certified"]: badges.append("🌿 Organic")
        if farm_data["livestock"]:         badges.append("🐄 Livestock")
        if not badges:                     badges = ["🌾 Crops Only"]
        st.markdown(
            f"<div style='padding-top:28px;font-size:0.82rem;color:#475569;'>"
            f"{'&nbsp;&nbsp;'.join(badges)}</div>",
            unsafe_allow_html=True,
        )

    # ─── Climate controls ─────────────────────────────────────────────────────
    with st.expander("🎛️ Climate Scenario & Adaptation Controls", expanded=True):
        sc1, sc2, sc3, sc4 = st.columns(4)
        sim_temp     = sc1.slider("🌡️ Temp Rise (°C)",       0.0, 4.0,  2.0, 0.5)
        sim_precip   = sc2.slider("🌧️ Rainfall Change (%)", -40,  20,  -20,  5)
        opt_irrig    = sc3.checkbox("💧 Precision Irrigation",  value=stats["is_irrigated"])
        opt_cultivar = sc3.checkbox("🌱 Drought Cultivar",      value=False)
        opt_catch    = sc4.checkbox("🌿 Cover Crops",           value=True)
        opt_buffer   = sc4.checkbox("🏞️ Buffer Strips",        value=stats["buffer_strip_coverage_pct"] > 50)

    # ─── Run simulation ───────────────────────────────────────────────────────
    sim_out  = api.twin.simulate_digital_twin(
        farm_id=selected_fid,
        delta_temp_c=float(sim_temp),
        delta_precip_pct=float(sim_precip),
        upgrade_irrigation=opt_irrig,
        switch_drought_cultivar=opt_cultivar,
        apply_catch_crops=opt_catch,
        install_buffer_strips=opt_buffer,
    )
    sim_mult = sim_out["sim_yield_t_ha"] / max(stats["baseline_mean_yield_t_ha"], 0.1)

    # ─── Build parcel data ────────────────────────────────────────────────────
    poly_rows: list[dict]    = []
    surface_pts: list[dict]  = []

    if not parcels_raw.empty:
        cols_grid = max(3, int(np.ceil(np.sqrt(len(parcels_raw)))))
        for idx, (_, r) in enumerate(parcels_raw.iterrows()):
            slope_mod = 1.0 - (float(r["slope_pct"]) * 0.02)
            soil_mod  = 0.90 if "sand" in str(r["soil_class_soilmap"]).lower() else 1.02
            p_yield   = stats["baseline_mean_yield_t_ha"] * sim_mult * slope_mod * soil_mod

            # Realistic organic polygon (seed unique per parcel for stable shapes)
            parcel_seed = abs(hash(str(r["parcel_id"]))) % 10_000
            polygon = _realistic_field_polygon(
                farm_lat, farm_lon,
                float(r["area_ha"]),
                idx,
                seed=parcel_seed,
            )

            poly_rows.append({
                "polygon":    polygon,
                "parcel_id":  r["parcel_id"],
                "sim_yield":  round(p_yield, 2),
                "area_ha":    round(float(r["area_ha"]), 1),
                "soil":       str(r["soil_class_soilmap"]).title(),
                "slope":      round(float(r["slope_pct"]), 1),
                "dist_water": int(r["dist_to_water_m"]),
                "buffer":     "Protected ✓" if r["buffer_strip"] else "Missing ✗",
                "fill_color": _yield_rgba(p_yield),
            })
            ri, ci = idx // cols_grid, idx % cols_grid
            surface_pts.append({"row": ri, "col": ci, "yield": p_yield})

    # ─── Main 2-column layout ─────────────────────────────────────────────────
    map_col, stats_col = st.columns([1.55, 1.0])

    # ════════════════════════════════════════════════════════════════════════
    # LEFT — Map tabs
    # ════════════════════════════════════════════════════════════════════════
    with map_col:
        from components.satellite_3d_map import render_realtime_satellite_hud
        render_realtime_satellite_hud(
            lat=float(farm_lat),
            lon=float(farm_lon),
            region_label=f"Farm Digital Twin · {selected_fid} ({crop.title()})",
            parcel_count=len(parcels_raw),
            mode_badge="3D SATELLITE DIGITAL TWIN",
        )
        tab_3d, tab_sat = st.tabs(["🛰️ Real-Time 3D Satellite Terrain Model", "🗺️ 2D Satellite Field Polygons"])

        # ── Tab 2: Leaflet satellite map ──────────────────────────────────────
        with tab_sat:
            st.caption(
                "Real satellite imagery (Esri World Imagery). "
                "Click any field parcel for soil & yield details. "
                "Scroll to zoom · drag to pan."
            )
            if poly_rows:
                html_src = _build_satellite_html(farm_lat, farm_lon, poly_rows, selected_fid)
                components.html(html_src, height=510, scrolling=False)
            else:
                st.info("No parcel geometries available for this farm.")

        # ── Tab 2: Satellite-Realistic 3D Simulation ──────────────────────────
        with tab_3d:
            st.caption(
                "🛰️ **Satellite 3D Simulation**: High-resolution Esri satellite photography draped onto "
                "3D Finnish moraine terrain with Finnish red barns, silo, and interactive parcel pins. Click & drag to rotate in 3D."
            )

            # Simulation Mode Switcher: Satellite Realistic 3D vs Mathematical Topography
            m_col1, m_col2 = st.columns([1.7, 1.0])
            with m_col1:
                render_engine = st.radio(
                    "3D Simulation Engine:",
                    ["🛰️ Photorealistic Satellite 3D Terrain", "📊 Mathematical Topography & Contours"],
                    index=0,
                    horizontal=True,
                    key=f"engine_{selected_fid}",
                )
            with m_col2:
                relief_scale = st.slider(
                    "3D Relief Scale:",
                    min_value=1.0,
                    max_value=2.8,
                    value=1.6,
                    step=0.2,
                    key=f"relief_{selected_fid}",
                )

            if not parcels_raw.empty:
                if "Satellite" in render_engine:
                    sat_3d_html = _build_satellite_3d_html(
                        farm_lat=farm_lat,
                        farm_lon=farm_lon,
                        parcels_raw=parcels_raw,
                        farm_id=selected_fid,
                        crop=crop,
                        base_yield=stats["baseline_mean_yield_t_ha"],
                        sim_mult=sim_mult,
                        sim_temp=float(sim_temp),
                        sim_precip=float(sim_precip),
                        opt_buffer=opt_buffer,
                        relief_scale=relief_scale,
                    )
                    components.html(sat_3d_html, height=530, scrolling=False)
                else:
                    cam_choice = st.selectbox(
                        "Perspective:",
                        list(CAMERA_PRESETS.keys()),
                        index=0,
                        key=f"cam_{selected_fid}",
                    )
                    fig_3d = _build_photorealistic_3d_terrain(
                        parcels_df=parcels_raw,
                        farm_id=selected_fid,
                        crop=crop,
                        base_yield=stats["baseline_mean_yield_t_ha"],
                        sim_mult=sim_mult,
                        sim_temp=float(sim_temp),
                        sim_precip=float(sim_precip),
                        opt_buffer=opt_buffer,
                        mode="🌾 Realistic Farm Landscape",
                        camera_key=cam_choice,
                        vertical_scale=relief_scale,
                    )
                    st.plotly_chart(fig_3d, use_container_width=True)
            else:
                st.info("No parcel data to build a 3D terrain model.")

    # ════════════════════════════════════════════════════════════════════════
    # RIGHT — Demeter-style stats panel
    # ════════════════════════════════════════════════════════════════════════
    with stats_col:

        # ── Grade cards ───────────────────────────────────────────────────────
        soil_score  = max(20.0, 100.0
                          - stats["avg_slope_pct"] * 7.0
                          - max(0.0, 60.0 - stats["avg_clay_pct"]) * 0.4)
        water_score = max(20.0, 100.0 - (900.0 / max(stats["min_water_dist_m"], 10.0)) * 10.0)
        loc_score   = soil_score * 0.6 + water_score * 0.4

        env_score = min(100.0, max(20.0,
            stats["buffer_strip_coverage_pct"] * 0.4
            + (100.0 - max(0.0, sim_out["p_loss_delta_pct"]) * 0.4) * 0.3
            + (25.0 if farm_data["organic_certified"] else 0.0) * 0.4
            + 38.0
        ))

        loc_grade, loc_color = _grade(loc_score)
        env_grade, env_color = _grade(env_score)

        soil_desc = (
            f"Avg clay {stats['avg_clay_pct']:.0f}%, slope {stats['avg_slope_pct']:.1f}%. "
            + ("Good moisture retention." if stats["avg_clay_pct"] > 35
               else "Sandy — elevated drought risk.")
        )
        env_desc = (
            f"Buffer strips: {stats['buffer_strip_coverage_pct']:.0f}% coverage. "
            + ("Organic certified — lower chemical burden." if farm_data["organic_certified"]
               else "Install buffer strips to cut nutrient runoff.")
        )

        gc1, gc2 = st.columns(2)
        for col_obj, grade, color, label, sublabel, desc in [
            (gc1, loc_grade, loc_color, "Location Score",       "Soil · moisture · site",    soil_desc),
            (gc2, env_grade, env_color, "Environmental Impact", "Runoff · buffer · practices", env_desc),
        ]:
            with col_obj:
                st.markdown(f"""
                <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:10px;
                            padding:14px 16px;min-height:148px;">
                  <div style="font-size:0.68rem;font-weight:700;color:#94a3b8;
                              text-transform:uppercase;letter-spacing:.06em;">{label}</div>
                  <div style="font-size:0.62rem;color:#94a3b8;margin-bottom:5px;">{sublabel}</div>
                  <div style="font-size:3rem;font-weight:900;color:{color};
                              line-height:1;margin-bottom:4px;">{grade}</div>
                  <div style="font-size:0.70rem;color:#475569;">{desc}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

        # ── Farm breakdown donut ───────────────────────────────────────────────
        total_ha = stats["total_area_ha"]
        fig_donut = px.pie(
            names=[crop.title(), "Cover Crop", "Fallow / Set-Aside"],
            values=[total_ha * 0.72, total_ha * 0.18, total_ha * 0.10],
            hole=0.60,
            color_discrete_sequence=["#10b981", "#84cc16", "#cbd5e1"],
        )
        fig_donut.update_traces(
            textposition="outside", textinfo="label+percent",
            textfont_size=10, pull=[0.04, 0, 0],
        )
        fig_donut.update_layout(
            height=225,
            margin=dict(l=20, r=20, t=36, b=10),
            showlegend=False,
            title=dict(text=f"🌱 Farm Breakdown — {total_ha:.1f} ha total", font=dict(size=12), x=0.0),
            annotations=[dict(text=f"<b>{total_ha:.0f}<br>ha</b>", x=0.5, y=0.5,
                               font_size=14, showarrow=False)],
        )
        st.plotly_chart(fig_donut, use_container_width=True)

        # ── Crop rotations ─────────────────────────────────────────────────────
        st.markdown("**🔄 Recommended Crop Rotations**")
        primary_score  = EARTH_SCORES.get(crop, 75)
        rotation_crop  = ROTATION_PARTNER.get(crop, "oat")
        rotation_score = EARTH_SCORES.get(rotation_crop, 75)

        for c_name, c_score, season, is_now in [
            (crop.title(),         primary_score,  "Current Season", True),
            (rotation_crop.title(), rotation_score, "Following Year", False),
        ]:
            bar_color = "#10b981" if c_score >= 80 else "#eab308"
            bg        = "#f0fdf4"  if is_now else "#f8fafc"
            border    = "#bbf7d0"  if is_now else "#e2e8f0"
            badge     = ('<span style="font-size:0.62rem;background:#10b981;color:white;'
                         'border-radius:4px;padding:1px 6px;margin-left:6px;">Current</span>'
                         if is_now else "")
            st.markdown(f"""
            <div style="background:{bg};border:1px solid {border};
                        border-radius:8px;padding:10px 12px;margin-bottom:7px;">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                  <span style="font-size:0.85rem;font-weight:700;color:#0f172a;">🌾 {c_name}</span>{badge}
                </div>
                <div style="font-size:0.72rem;color:#64748b;">{season}</div>
              </div>
              <div style="display:flex;align-items:center;gap:8px;margin-top:7px;">
                <div style="flex:1;background:#e2e8f0;border-radius:4px;height:7px;">
                  <div style="width:{c_score}%;background:{bar_color};height:7px;border-radius:4px;"></div>
                </div>
                <span style="font-size:0.74rem;font-weight:700;color:{bar_color};">Earth {c_score}/100</span>
              </div>
            </div>""", unsafe_allow_html=True)

        # ── 4 KPI tiles ────────────────────────────────────────────────────────
        st.markdown("**📊 Simulated Outcomes**")
        m1, m2 = st.columns(2)
        m1.metric("Harvest Yield", f"{sim_out['sim_yield_t_ha']:.2f} t/ha",
                  f"{sim_out['yield_delta_pct']:+.1f}%",
                  delta_color="normal" if sim_out["yield_delta_pct"] >= 0 else "off")
        m2.metric("Net Margin Δ", f"€{sim_out['net_margin_delta_eur']:,.0f}",
                  "After adapt. costs",
                  delta_color="normal" if sim_out["net_margin_delta_eur"] >= 0 else "off")
        m3, m4 = st.columns(2)
        m3.metric("Water Need", f"{sim_out['sim_water_m3_ha']:.0f} m³/ha",
                  f"{sim_out['water_delta_pct']:+.1f}%",
                  delta_color="off" if sim_out["water_delta_pct"] > 10 else "normal")
        m4.metric("P-Loss Runoff", f"{sim_out['sim_p_loss_kg']:.1f} kg P",
                  f"{sim_out['p_loss_delta_pct']:+.1f}%",
                  delta_color="normal" if sim_out["p_loss_delta_pct"] <= 0 else "off")

    # ════════════════════════════════════════════════════════════════════════
    # BOTTOM — Financials + Environmental Strain + AI Advisor
    # ════════════════════════════════════════════════════════════════════════
    st.divider()
    bc1, bc2 = st.columns(2)

    with bc1:
        st.markdown("##### 💰 Estimated Farm Financials")
        seasons  = ["Spring", "Summer (Harvest)", "Autumn", "Winter"]
        price_t  = 380.0 if "pea" in crop else (220.0 if "potato" in crop else 300.0)
        base_rev = stats["baseline_mean_yield_t_ha"] * stats["total_area_ha"] * price_t
        sim_ratio = sim_out["sim_yield_t_ha"] / max(stats["baseline_mean_yield_t_ha"], 0.1)

        spend = [-base_rev * 0.32, -base_rev * 0.42, -base_rev * 0.14, -base_rev * 0.07]
        rev   = [base_rev * 0.02,
                 base_rev * 0.60 * sim_ratio,
                 base_rev * 0.08,
                 base_rev * 0.28]

        fig_fin = go.Figure()
        fig_fin.add_trace(go.Bar(x=seasons, y=spend, name="Spending (€)",
                                  marker_color="#ef4444", opacity=0.85))
        fig_fin.add_trace(go.Bar(x=seasons, y=rev,   name="Revenue (€)",
                                  marker_color="#10b981", opacity=0.85))
        fig_fin.update_layout(
            height=270, barmode="group",
            margin=dict(l=20, r=20, t=20, b=20),
            yaxis_title="€", yaxis_tickformat=",.0f",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
            plot_bgcolor="#f8fafc", paper_bgcolor="#ffffff",
        )
        st.plotly_chart(fig_fin, use_container_width=True)

    with bc2:
        st.markdown("##### 🌊 Environmental Strain Over Seasons")
        x_labels  = ["Spr '24", "Sum '24", "Aut '24", "Win '24", "Spr '25", "Sum '25"]
        base_y    = stats["baseline_mean_yield_t_ha"]
        sim_y     = sim_out["sim_yield_t_ha"]

        water_vals = [
            35,
            88  * (1.0 + sim_temp * 0.08),
            52  * (1.0 + sim_temp * 0.04),
            12, 37,
            95  * (1.0 + sim_temp * 0.08),
        ]
        yield_idx = [
            base_y * 0.08, base_y * 0.42,
            sim_y  * 0.95, sim_y,
            base_y * 0.07, base_y * 0.40,
        ]

        fig_env = go.Figure()
        fig_env.add_trace(go.Scatter(
            x=x_labels, y=water_vals, name="Water Demand (mm)",
            mode="lines", fill="tozeroy",
            fillcolor="rgba(59,130,246,0.15)",
            line=dict(color="#3b82f6", width=2.5),
        ))
        fig_env.add_trace(go.Scatter(
            x=x_labels, y=[v * 20 for v in yield_idx], name="Yield Index (×20)",
            mode="lines", fill="tozeroy",
            fillcolor="rgba(16,185,129,0.15)",
            line=dict(color="#10b981", width=2.5),
        ))
        fig_env.update_layout(
            height=270,
            margin=dict(l=20, r=20, t=20, b=20),
            yaxis_title="Intensity",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
            plot_bgcolor="#f8fafc", paper_bgcolor="#ffffff",
        )
        st.plotly_chart(fig_env, use_container_width=True)

    # ─── AI Agronomic Advisor ─────────────────────────────────────────────────
    st.markdown("### 🤖 AI Agronomic Advisor")
    st.info(sim_out["advisor_notes"].replace("\\n", "\n").replace("**", ""))

    # ─── Export ───────────────────────────────────────────────────────────────
    _, btn_col = st.columns([4, 1])
    with btn_col:
        md_content = (
            f"# Farm Digital Twin — Climate Adaptation Brief\n\n"
            f"**Farm:** {selected_fid} | **Crop:** {crop.title()}\n\n"
            f"**Scenario:** +{sim_temp:.1f} °C / {sim_precip:+d}% rainfall\n\n---\n\n"
            + sim_out["advisor_notes"].replace("\\n", "\n").replace("**", "")
            + "\n\n---\n*Synthetic data only — not real Apetit operational data*"
        )
        st.download_button(
            "📄 Export Adaptation Brief",
            md_content,
            file_name=f"climate_brief_{selected_fid}.md",
            mime="text/markdown",
            use_container_width=True,
        )
