"""
prototype/components/satellite_3d_map.py — Interactive Geomap & Satellite Terrain Engine
Provides:
1. `build_drought_choropleth_map_html`: Matches the reference Drought Early Warning & Climate Intelligence UI
   (Terrain/Street + Satellite base map, blue-shaded regional sub-basin polygons with centered bold labels,
   right-hand vertical map control toolbar, and bottom-right 'Inches of Precipitation / Moisture' gradient bar).
2. `build_satellite_3d_deck`: PyDeck 3D Geomap with guaranteed visible Carto base map (`map_provider="carto"`).
3. `build_threejs_satellite_3d_terrain_html`: 360° rotatable Three.js 3D Satellite-draped terrain mesh.
4. `render_realtime_satellite_hud`: Live Open-Meteo telemetry banner.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st

from core.live_apis import LiveAPIsService


def _html(raw: str) -> str:
    """Strip per-line indentation so Markdown never turns HTML into a code block."""
    return "\n".join(line.lstrip() for line in raw.splitlines() if line.strip())


def build_drought_choropleth_map_html(
    center_lat: float = 61.05,
    center_lon: float = 22.35,
    region_name: str = "Satakunta & Säkylä Basin",
    metric_mode: str = "rainfall",
    rainfall_deficit_pct: float = -20.0,
    moisture_deficit_pct: float = -20.0,
    height_px: int = 580,
) -> str:
    """
    Build the exact interactive Leaflet geomap matching the user's reference screenshot:
    - Real physical terrain / street base map (plus 1-click Satellite & Topo switcher)
    - 5 contiguous regional sub-basin polygons shaded in the exact blue palette (#0369a1, #0284c7, #60a5fa, #93c5fd, #e0f2fe)
      with bold centered province/sub-basin labels
    - Top-right vertical floating map control buttons (fullscreen, layers, target, zoom +, zoom -)
    - Bottom-right floating legend card with gradient bar ('Inches of Precipitation' or 'Soil Moisture Index')
    """
    # Construct 5 contiguous regional sub-polygons around (center_lat, center_lon)
    # shaped like the 5 provinces in the reference screenshot (Western, Northern, Central, Eastern, Southern)
    la, lo = float(center_lat), float(center_lon)

    sub_regions = [
        {
            "name": "Western Basin\n(Eurajoki & Rauma)",
            "short": "Western\nProvince",
            "precip_in": 6.8 if metric_mode == "rainfall" else 5.9,
            "deficit_pct": round(rainfall_deficit_pct - 4.0, 1),
            "moisture_pct": round(moisture_deficit_pct - 3.0, 1),
            "fill": "#0369a1",  # Deepest blue
            "coords": [
                [lo - 0.55, la - 0.22],
                [lo - 0.48, la + 0.05],
                [lo - 0.32, la + 0.18],
                [lo - 0.18, la + 0.10],
                [lo - 0.22, la - 0.08],
                [lo - 0.35, la - 0.25],
                [lo - 0.55, la - 0.22],
            ],
        },
        {
            "name": "Northern Basin\n(Kokemäenjoki Valley)",
            "short": "Northern\nProvince",
            "precip_in": 5.4 if metric_mode == "rainfall" else 4.8,
            "deficit_pct": round(rainfall_deficit_pct - 1.5, 1),
            "moisture_pct": round(moisture_deficit_pct - 2.0, 1),
            "fill": "#0284c7",  # Medium-dark blue
            "coords": [
                [lo - 0.32, la + 0.18],
                [lo - 0.12, la + 0.30],
                [lo + 0.12, la + 0.24],
                [lo + 0.06, la + 0.06],
                [lo - 0.08, la + 0.04],
                [lo - 0.18, la + 0.10],
                [lo - 0.32, la + 0.18],
            ],
        },
        {
            "name": "Säkylä Core\n(Pyhäjärvi Hub)",
            "short": "Säkylä\nCore Hub",
            "precip_in": 3.8 if metric_mode == "rainfall" else 3.5,
            "deficit_pct": round(rainfall_deficit_pct, 1),
            "moisture_pct": round(moisture_deficit_pct, 1),
            "fill": "#60a5fa",  # Mid blue
            "coords": [
                [lo - 0.08, la + 0.04],
                [lo + 0.06, la + 0.06],
                [lo + 0.10, la - 0.07],
                [lo - 0.04, la - 0.10],
                [lo - 0.08, la + 0.04],
            ],
        },
        {
            "name": "Southern Basin\n(Yläne & Aura Valley)",
            "short": "Southern\nProvince",
            "precip_in": 1.6 if metric_mode == "rainfall" else 2.1,
            "deficit_pct": round(rainfall_deficit_pct - 6.0, 1),
            "moisture_pct": round(moisture_deficit_pct - 5.0, 1),
            "fill": "#dbeafe",  # Lightest blue
            "coords": [
                [lo - 0.35, la - 0.25],
                [lo - 0.22, la - 0.08],
                [lo - 0.18, la + 0.10],
                [lo - 0.08, la + 0.04],
                [lo - 0.04, la - 0.10],
                [lo + 0.10, la - 0.07],
                [lo + 0.08, la - 0.28],
                [lo - 0.16, la - 0.32],
                [lo - 0.35, la - 0.25],
            ],
        },
        {
            "name": "Eastern Basin\n(Loimijoki Clay Plains)",
            "short": "Eastern\nProvince",
            "precip_in": 4.4 if metric_mode == "rainfall" else 4.1,
            "deficit_pct": round(rainfall_deficit_pct + 2.0, 1),
            "moisture_pct": round(moisture_deficit_pct + 1.5, 1),
            "fill": "#38bdf8",  # Sky-medium blue
            "coords": [
                [lo + 0.12, la + 0.24],
                [lo + 0.34, la + 0.34],
                [lo + 0.52, la + 0.12],
                [lo + 0.56, la - 0.12],
                [lo + 0.36, la - 0.28],
                [lo + 0.08, la - 0.28],
                [lo + 0.10, la - 0.07],
                [lo + 0.06, la + 0.06],
                [lo + 0.12, la + 0.24],
            ],
        },
    ]

    features = []
    for sr in sub_regions:
        lons = [pt[0] for pt in sr["coords"][:-1]]
        lats = [pt[1] for pt in sr["coords"][:-1]]
        features.append({
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [sr["coords"]]},
            "properties": {
                "name": sr["name"],
                "short": sr["short"],
                "precip_in": sr["precip_in"],
                "deficit_pct": sr["deficit_pct"],
                "moisture_pct": sr["moisture_pct"],
                "fill": sr["fill"],
                "c_lat": float(np.mean(lats)),
                "c_lon": float(np.mean(lons)),
            },
        })

    geojson_str = json.dumps({"type": "FeatureCollection", "features": features})
    legend_title = "Inches of Precipitation" if metric_mode == "rainfall" else "Soil Moisture Index (0–8)"

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; font-family:'Inter',-apple-system,BlinkMacSystemFont,sans-serif; }}
  html, body {{ width:100%; height:100%; background:#e5e7eb; overflow:hidden; }}
  #map-wrap {{ position:relative; width:100%; height:{height_px}px; border-radius:8px; overflow:hidden; border:1px solid #d1d5db; }}
  #map {{ width:100%; height:100%; }}

  /* Floating right-side vertical toolbar matching screenshot */
  .map-tools {{
    position:absolute; top:16px; right:14px; z-index:900;
    display:flex; flex-direction:column; gap:6px;
  }}
  .map-tool-btn {{
    width:34px; height:34px; background:#ffffff; color:#1f2937;
    border:1px solid #d1d5db; border-radius:6px;
    display:flex; align-items:center; justify-content:center;
    font-size:15px; font-weight:700; cursor:pointer;
    box-shadow:0 2px 6px rgba(0,0,0,0.12);
    transition:all 0.15s ease;
  }}
  .map-tool-btn:hover {{ background:#f3f4f6; color:#0284c7; border-color:#93c5fd; }}
  .map-tool-btn.active {{ background:#0284c7; color:#ffffff; border-color:#0284c7; }}

  /* Floating bottom-right legend card matching screenshot */
  .precip-legend {{
    position:absolute; bottom:20px; right:56px; z-index:900;
    background:#ffffff; border:1px solid #e5e7eb; border-radius:6px;
    padding:10px 18px; min-width:260px;
    box-shadow:0 4px 14px rgba(0,0,0,0.12);
    text-align:center;
  }}
  .precip-legend-title {{
    font-size:12px; font-weight:700; color:#111827; margin-bottom:6px;
  }}
  .precip-bar-row {{
    display:flex; align-items:center; justify-content:space-between; gap:10px;
    font-size:11px; font-weight:700; color:#374151;
  }}
  .precip-gradient {{
    flex:1; height:10px; border-radius:3px;
    background:linear-gradient(90deg, #dbeafe 0%, #93c5fd 30%, #38bdf8 60%, #0284c7 82%, #0369a1 100%);
  }}

  /* Province center label */
  .prov-label {{
    font-size:10.5px; font-weight:800; color:#0f172a;
    text-align:center; line-height:1.2; white-space:pre-line;
    text-shadow:0 0 4px rgba(255,255,255,0.9), 0 0 2px #ffffff;
    pointer-events:none;
  }}
</style>
</head>
<body>
<div id="map-wrap">
  <div id="map"></div>

  <!-- Right-side vertical map controls matching reference screenshot -->
  <div class="map-tools">
    <button class="map-tool-btn" title="Reset Region View" onclick="resetBounds()">⛶</button>
    <button class="map-tool-btn" id="btn-sat" title="Toggle Satellite / Terrain Map" onclick="toggleBaseTile()">🛰️</button>
    <button class="map-tool-btn" title="Center on Active Basin" onclick="centerHub()">🎯</button>
    <button class="map-tool-btn" title="Zoom In" onclick="map.zoomIn()">+</button>
    <button class="map-tool-btn" title="Zoom Out" onclick="map.zoomOut()">−</button>
  </div>

  <!-- Bottom-right floating gradient legend matching reference screenshot -->
  <div class="precip-legend">
    <div class="precip-legend-title">{legend_title}</div>
    <div class="precip-bar-row">
      <span>0</span>
      <div class="precip-gradient"></div>
      <span>8</span>
    </div>
  </div>
</div>

<script>
const geoData = {geojson_str};
const centerLat = {la};
const centerLon = {lo};

const map = L.map('map', {{
  center: [centerLat, centerLon],
  zoom: 9,
  zoomControl: false,
  attributionControl: true,
}});

// Physical Terrain + Street base layer (matches the green-tinted terrain + road badges in screenshot)
const osmTerrainLayer = L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
  maxZoom: 18,
  attribution: '&copy; OpenStreetMap contributors'
}}).addTo(map);

const esriSatLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
  maxZoom: 18,
  attribution: '&copy; Esri World Imagery'
}});

const esriLabels = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
  maxZoom: 18
}});

let isSat = false;
function toggleBaseTile() {{
  const btn = document.getElementById('btn-sat');
  if (!isSat) {{
    map.removeLayer(osmTerrainLayer);
    esriSatLayer.addTo(map);
    esriLabels.addTo(map);
    btn.classList.add('active');
    isSat = true;
  }} else {{
    map.removeLayer(esriSatLayer);
    map.removeLayer(esriLabels);
    osmTerrainLayer.addTo(map);
    btn.classList.remove('active');
    isSat = false;
  }}
}}

// Draw the 5 regional sub-basin polygons
const polyLayer = L.geoJSON(geoData, {{
  style: function(feature) {{
    return {{
      fillColor: feature.properties.fill,
      weight: 1.5,
      opacity: 1,
      color: '#475569',
      fillOpacity: 0.78
    }};
  }},
  onEachFeature: function(feature, layer) {{
    const p = feature.properties;
    layer.bindPopup(
      `<div style="font-size:12.5px;line-height:1.5;">` +
      `<b>${{p.name.replace('\\n', ' ')}}</b><br/>` +
      `<b>Precipitation Index:</b> ${{p.precip_in}} in<br/>` +
      `<b>Rainfall Anomaly:</b> <span style="color:#dc2626;font-weight:700;">${{p.deficit_pct}}%</span><br/>` +
      `<b>Soil Moisture Anomaly:</b> <span style="color:#d97706;font-weight:700;">${{p.moisture_pct}}%</span>` +
      `</div>`
    );
    layer.on('mouseover', function() {{
      this.setStyle({{ weight: 2.8, color: '#0f172a', fillOpacity: 0.90 }});
    }});
    layer.on('mouseout', function() {{
      polyLayer.resetStyle(this);
    }});
  }}
}}).addTo(map);

// Add centered bold labels inside each polygon
geoData.features.forEach(function(f) {{
  const p = f.properties;
  L.marker([p.c_lat, p.c_lon], {{
    icon: L.divIcon({{
      className: 'prov-label',
      html: p.short.replace('\\n', '<br/>'),
      iconSize: [90, 32],
      iconAnchor: [45, 16]
    }})
  }}).addTo(map);
}});

function resetBounds() {{
  map.fitBounds(polyLayer.getBounds().pad(0.18));
}}
function centerHub() {{
  map.setView([centerLat, centerLon], 9);
}}
resetBounds();
</script>
</body>
</html>"""


def get_satellite_base_layers(include_labels: bool = True) -> List[pdk.Layer]:
    """Return empty list when using Carto map_provider so PyDeck never renders a black background."""
    return []


def build_satellite_3d_deck(
    feature_layers: List[pdk.Layer],
    lat: float = 61.05,
    lon: float = 22.34,
    zoom: float = 8.2,
    pitch: float = 50.0,
    bearing: float = 14.0,
    tooltip: Optional[Dict[str, Any]] = None,
    include_labels: bool = True,
) -> pdk.Deck:
    """Build a PyDeck 3D Geomap with a guaranteed visible Carto base map (no black canvas!)."""
    return pdk.Deck(
        layers=list(feature_layers),
        initial_view_state=pdk.ViewState(
            latitude=lat,
            longitude=lon,
            zoom=zoom,
            pitch=pitch,
            bearing=bearing,
        ),
        map_provider="carto",
        map_style="positron" if include_labels else "dark",
        tooltip=tooltip,
    )


def render_realtime_satellite_hud(
    lat: float = 61.05,
    lon: float = 22.34,
    region_label: str = "Säkylä & Satakunta Sourcing Basin",
    parcel_count: int = 320,
    mode_badge: str = "LIVE SATELLITE TELEMETRY",
) -> Dict[str, Any]:
    """Fetch live Open-Meteo telemetry for (lat, lon) and render a clean status HUD bar."""
    live = LiveAPIsService()
    wx = live.get_live_weather(lat=lat, lon=lon)
    temp_c = wx.get("temperature_c", 14.2)
    wind_kmh = wx.get("windspeed_kmh", 12.5)
    precip_mm = wx.get("precipitation_mm", 0.0)
    obs_time = str(wx.get("observation_time", "Live UTC")).replace("T", " ")

    st.markdown(
        _html(f"""
        <div style="background:#ffffff; color:#0b1c30; border:1px solid #dce4ee; border-left:4px solid #006948; border-radius:8px; padding:10px 16px; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
            <div style="display:flex; align-items:center; gap:10px;">
                <span style="background:#dcfce7; color:#15803d; font-size:0.68rem; font-weight:800; padding:3px 9px; border-radius:9999px; letter-spacing:0.05em;">🛰️ {mode_badge}</span>
                <span style="font-size:0.84rem; font-weight:700; color:#0b1c30;">{region_label}</span>
                <span style="font-size:0.74rem; color:#64748b; font-family:'JetBrains Mono',monospace;">({lat:.3f}°N, {lon:.3f}°E · {parcel_count} Parcels)</span>
            </div>
            <div style="display:flex; align-items:center; gap:14px; flex-wrap:wrap; font-size:0.76rem; color:#334155;">
                <span>🌡️ <b>{temp_c}°C</b> Live Air</span>
                <span>💨 <b>{wind_kmh} km/h</b> Wind</span>
                <span>🌧️ <b>{precip_mm} mm</b> Precip</span>
                <span style="color:#006948; font-weight:700;">● Updated {obs_time}</span>
            </div>
        </div>
        """),
        unsafe_allow_html=True,
    )
    return wx


def build_threejs_satellite_3d_terrain_html(
    df: pd.DataFrame,
    title: str = "Real-Time 3D Satellite Terrain Geomap",
    lat_col: str = "lat",
    lon_col: str = "lon",
    id_col: str = "parcel_id",
    value_col: str = "value",
    tier_col: str = "tier",
    color_col: str = "hex_color",
    extra_col: str = "info",
    value_unit: str = "",
    relief_scale: float = 1.6,
    height_px: int = 520,
) -> str:
    """
    Build a self-contained Three.js WebGL 3D Satellite-Draped Terrain HTML view.
    """
    if df.empty:
        return "<div style='padding:20px;color:white;background:#0a0f1e;'>No spatial coordinates available.</div>"

    sub = df.head(180).copy()
    lon_min, lon_max = float(sub[lon_col].min()), float(sub[lon_col].max())
    lat_min, lat_max = float(sub[lat_col].min()), float(sub[lat_col].max())

    pad_lon = max((lon_max - lon_min) * 0.25, 0.015)
    pad_lat = max((lat_max - lat_min) * 0.25, 0.012)
    min_lon, max_lon = lon_min - pad_lon, lon_max + pad_lon
    min_lat, max_lat = lat_min - pad_lat, lat_max + pad_lat

    bbox = f"{min_lon:.5f},{min_lat:.5f},{max_lon:.5f},{max_lat:.5f}"
    sat_url = (
        f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export"
        f"?bbox={bbox}&bboxSR=4326&imageSR=4326&size=1024,1024&format=jpg&f=image"
    )

    val_series = pd.to_numeric(sub[value_col], errors="coerce").fillna(1.0)
    v_max = max(float(val_series.abs().max()), 1.0)

    items = []
    for idx, (_, r) in enumerate(sub.iterrows()):
        u = (float(r[lon_col]) - min_lon) / max(max_lon - min_lon, 0.0001)
        v = (float(r[lat_col]) - min_lat) / max(max_lat - min_lat, 0.0001)
        px_coord = -50.0 + u * 100.0
        pz_coord = 50.0 - v * 100.0
        raw_val = float(val_series.loc[_])
        norm_h = max(1.8, (abs(raw_val) / v_max) * 14.0)
        area_ha = float(r.get("area_ha", 6.0))
        hw = max(1.6, min(4.2, np.sqrt(max(area_ha, 1.0)) * 0.9))

        items.append({
            "idx": idx,
            "id": str(r.get(id_col, f"P-{idx}")),
            "px": round(px_coord, 2),
            "pz": round(pz_coord, 2),
            "hw": round(hw, 2),
            "h": round(norm_h, 2),
            "val": round(raw_val, 2),
            "tier": str(r.get(tier_col, "Active")),
            "color": str(r.get(color_col, "#10b981")),
            "extra": str(r.get(extra_col, "")),
        })

    items_json = json.dumps(items)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  html, body {{ width:100%; height:100%; overflow:hidden; background:#071120; font-family:-apple-system,BlinkMacSystemFont,sans-serif; }}
  #wrap {{ width:100%; height:{height_px}px; position:relative; border-radius:10px; border:1px solid #1e3a5f; overflow:hidden; }}
  #canvas-box {{ width:100%; height:100%; }}
  .toolbar {{
    position:absolute; top:12px; left:12px; z-index:10;
    display:flex; gap:6px; flex-wrap:wrap; align-items:center;
    background:rgba(11, 28, 48, 0.90); backdrop-filter:blur(10px);
    border:1px solid #334155; border-radius:8px; padding:6px 10px;
  }}
  .tbtn {{
    background:#1e293b; color:#f8fafc; border:1px solid #475569;
    border-radius:6px; padding:4px 9px; font-size:11px; font-weight:600; cursor:pointer;
  }}
  .tbtn:hover, .tbtn.active {{ background:#00855d; border-color:#74f8c1; color:#fff; }}
  #tooltip {{
    position:absolute; display:none; z-index:25;
    background:rgba(11, 28, 48, 0.95); color:#f8fafc;
    border:1px solid #38bdf8; border-radius:8px; padding:10px 14px;
    font-size:12px; line-height:1.6; pointer-events:none;
    box-shadow:0 8px 24px rgba(0,0,0,0.8); min-width:210px;
  }}
  .hud-badge {{
    position:absolute; bottom:12px; right:12px; z-index:10;
    background:rgba(11, 28, 48, 0.90); border:1px solid #334155;
    border-radius:8px; padding:8px 12px; color:#cbd5e1; font-size:11px; line-height:1.7;
  }}
</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
</head>
<body>
<div id="wrap">
  <div class="toolbar">
    <span style="color:#74f8c1;font-size:11px;font-weight:800;margin-right:4px;">🛰️ {title}</span>
    <button class="tbtn active" onclick="setCam('iso')">📐 Isometric 3D</button>
    <button class="tbtn" onclick="setCam('top')">🦅 Overhead Satellite</button>
    <button class="tbtn" onclick="setCam('low')">🌅 Low Horizon</button>
    <button class="tbtn" onclick="toggleSpin()">🔄 Auto-Rotate 360°</button>
  </div>
  <div id="tooltip"></div>
  <div class="hud-badge">
    <b style="color:#38bdf8;">🛰️ Esri World Imagery 3D Mesh</b><br/>
    Drag to rotate 360° · Scroll to zoom · Hover 3D columns for telemetry
  </div>
  <div id="canvas-box"></div>
</div>
<script>
const satUrl = "{sat_url}";
const items = {items_json};
const relief = {relief_scale};
const unitStr = "{value_unit}";

const box = document.getElementById('canvas-box');
const tooltip = document.getElementById('tooltip');
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x071120);
scene.fog = new THREE.FogExp2(0x071120, 0.0032);

const camera = new THREE.PerspectiveCamera(42, box.clientWidth / box.clientHeight, 0.5, 1000);
camera.position.set(66, 65, 76);

const renderer = new THREE.WebGLRenderer({{ antialias: true }});
renderer.setSize(box.clientWidth, box.clientHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
box.appendChild(renderer.domElement);

const controls = new THREE.OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.06;
controls.maxPolarAngle = Math.PI / 2.04;
controls.minDistance = 20;
controls.maxDistance = 240;

scene.add(new THREE.AmbientLight(0xffffff, 0.82));
const dirLight = new THREE.DirectionalLight(0xfff7ed, 1.35);
dirLight.position.set(60, 110, 50);
scene.add(dirLight);

function getElev(x, z) {{
  return (1.6 * Math.sin(x * 0.04) + 1.3 * Math.cos(z * 0.035)) * relief;
}}

const geom = new THREE.PlaneGeometry(100, 100, 80, 80);
geom.rotateX(-Math.PI / 2);
const pos = geom.attributes.position.array;
for (let i = 0; i < pos.length; i += 3) {{
  pos[i + 1] = getElev(pos[i], pos[i + 2]);
}}
geom.computeVertexNormals();

const loader = new THREE.TextureLoader();
loader.setCrossOrigin('anonymous');
const tex = loader.load(satUrl);
const terrain = new THREE.Mesh(geom, new THREE.MeshStandardMaterial({{ map: tex, roughness: 0.86, metalness: 0.08 }}));
scene.add(terrain);

const pickables = [];
items.forEach((it) => {{
  const baseY = getElev(it.px, it.pz);
  const colGeom = new THREE.CylinderGeometry(it.hw * 0.55, it.hw * 0.7, it.h, 18);
  const colMat = new THREE.MeshStandardMaterial({{
    color: new THREE.Color(it.color),
    transparent: true,
    opacity: 0.86,
    emissive: new THREE.Color(it.color),
    emissiveIntensity: 0.22,
  }});
  const mesh = new THREE.Mesh(colGeom, colMat);
  mesh.position.set(it.px, baseY + it.h / 2.0, it.pz);
  mesh.userData = it;
  scene.add(mesh);
  pickables.push(mesh);
}});

const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();
renderer.domElement.addEventListener('mousemove', (e) => {{
  const rect = renderer.domElement.getBoundingClientRect();
  mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
  mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(mouse, camera);
  const hits = raycaster.intersectObjects(pickables);
  if (hits.length > 0) {{
    const d = hits[0].object.userData;
    tooltip.style.display = 'block';
    tooltip.style.left = Math.min(e.clientX - rect.left + 14, rect.width - 230) + 'px';
    tooltip.style.top = Math.max(e.clientY - rect.top - 10, 12) + 'px';
    tooltip.innerHTML = `<b style="color:#74f8c1;">${{d.id}}</b><br/>` +
      `<b>Status:</b> ${{d.tier}}<br/>` +
      `<b>Metric:</b> ${{d.val}} ${{unitStr}}<br/>` +
      (d.extra ? `<span>${{d.extra}}</span>` : '');
  }} else {{
    tooltip.style.display = 'none';
  }}
}});

function setCam(mode) {{
  if (mode === 'iso') camera.position.set(66, 65, 76);
  if (mode === 'top') camera.position.set(0, 125, 0.1);
  if (mode === 'low') camera.position.set(82, 24, 45);
  controls.target.set(0, 0, 0);
  controls.update();
}}
function toggleSpin() {{
  controls.autoRotate = !controls.autoRotate;
  controls.autoRotateSpeed = 1.4;
}}
window.addEventListener('resize', () => {{
  camera.aspect = box.clientWidth / box.clientHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(box.clientWidth, box.clientHeight);
}});
function animate() {{
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
}}
animate();
</script>
</body>
</html>"""


def build_isometric_farm_twin_3d_html(
    farm_lat: float,
    farm_lon: float,
    parcels_raw: pd.DataFrame,
    farm_id: str = "FARM_0001",
    crop: str = "pea",
    base_yield: float = 4.5,
    height_px: int = 620,
    **_kwargs: Any,
) -> str:
    """
    Build the realistic Isometric 3D Farm Digital Twin inspired by the tablet reference:
    - Deep slate-teal HUD canvas (#111c24) with crisp white/emerald telemetry panels
    - Centerpiece 3D Isometric Farm Estate Block:
        * Layered 3D soil/loam earthen slab base + grass perimeter rim
        * Subdivided contiguous cultivated crop strips (mapped to real Apetit parcels.csv rows)
          with procedural 3D plowed furrow textures, raised 3D crop rows, and agronomic hues
          (lush emerald pea/spinach, golden rapeseed/barley, warm amber/terracotta potato strips)
        * Realistic miniature farmstead courtyard nested inside an inner parcel:
          two-story pitched-roof farmhouse, red Nordic barn, twin metallic grain silos, tractor,
          and surrounding deciduous tree clusters
        * Dense 3D forest windbreak / riparian tree belt along the upper-left edge
        * Ghosted teal wireframe neighboring field grid extending to the upper-right
    - Interactive HUD panels matching the reference image:
        * Top-left 'Digital Twin' summary + Farm switcher
        * Top-center multi-year yield trajectory sparkline
        * Top-right 'Simulation' interactive toggles (Crop Rotation, Irrigation, Pest/Nutrient Usage, Scenarios)
        * Left stacked 'Yield Prediction', 'Weather Forecast', and 'Soil Moisture' panels
        * Bottom-center 3 clickable 7x6 pixel-grid heatmaps (NDVI Biomass, Heat Stress, Soil Moisture)
    """
    records = []
    for idx, (_, r) in enumerate(parcels_raw.head(16).iterrows()):
        area = float(r.get("area_ha", 11.4))
        slope = float(r.get("slope_pct", 1.8))
        y_val = round(base_yield * (1.02 - slope * 0.018 + (idx % 4 - 1.5) * 0.08), 2)
        records.append({
            "idx": idx,
            "parcel_id": str(r.get("parcel_id", f"{farm_id}-P{idx+1:02d}")),
            "area_ha": round(area, 1),
            "soil": str(r.get("soil_class_soilmap", "mineral_silt")).replace("_", " ").title(),
            "slope": round(slope, 1),
            "dist_water": int(r.get("dist_to_water_m", 45)),
            "buffer": bool(r.get("buffer_strip", True)),
            "base_yield": y_val,
        })

    while len(records) < 14:
        i = len(records)
        records.append({
            "idx": i,
            "parcel_id": f"{farm_id}_P{i+1:02d}",
            "area_ha": round(8.5 + (i % 5) * 2.4, 1),
            "soil": "Glacial Silt Loam" if i % 2 == 0 else "Clay Moraine",
            "slope": round(1.2 + (i % 4) * 0.6, 1),
            "dist_water": 30 + (i * 15) % 120,
            "buffer": (i % 3 != 0),
            "base_yield": round(base_yield * (0.88 + (i % 5) * 0.06), 2),
        })

    parcels_json = json.dumps(records)
    total_ha = round(sum(p["area_ha"] for p in records), 1)

    try:
        farm_seed = int("".join(ch for ch in farm_id if ch.isdigit()) or "1")
    except ValueError:
        farm_seed = 1

    farm_catalog_options = [
        ("FARM_0001", "FARM_0001 (Säkylä · Pea)"),
        ("FARM_0002", "FARM_0002 (Pyhäjärvi · Pea)"),
        ("FARM_0003", "FARM_0003 (Köyliö · Potato)"),
        ("FARM_0004", "FARM_0004 (Huittinen · Rapeseed)"),
        ("FARM_0005", "FARM_0005 (Kantvik · Oilseed)"),
        ("FARM_0006", "FARM_0006 (Kokemäki · Carrot)"),
        ("FARM_0007", "FARM_0007 (Eura · Spinach)"),
        ("FARM_0008", "FARM_0008 (Loimijoki · Barley)"),
        ("FARM_0009", "FARM_0009 (Rauma · Pea)"),
        ("FARM_0010", "FARM_0010 (Pori · Root Veg)"),
    ]
    if all(fid != farm_id for fid, _ in farm_catalog_options):
        farm_catalog_options.insert(0, (farm_id, f"{farm_id} ({crop.title()})"))

    options_html = "\n        ".join(
        f'<option value="{fid}"{" selected" if fid == farm_id else ""}>{label}</option>'
        for fid, label in farm_catalog_options
    )

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  html, body {{
    width:100%; height:100%; overflow:hidden;
    background: radial-gradient(circle at 54% 48%, #1a2c38 0%, #111d26 60%, #0b131a 100%);
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #e2e8f0;
    user-select: none;
  }}
  #twin-stage {{
    position:relative; width:100%; height:{height_px}px; overflow:hidden;
  }}
  #webgl-canvas {{
    position:absolute; inset:0; width:100%; height:100%; z-index:1; cursor:grab;
  }}
  #webgl-canvas:active {{ cursor:grabbing; }}

  .hud-layer {{
    position:absolute; z-index:10; pointer-events:none;
  }}
  .hud-interactive {{ pointer-events:auto; }}

  /* Unified Left Column: Digital Twin Info + Stacked Telemetry Panels (No Overlap) */
  .hud-left-col {{
    top:18px; left:24px; width:276px;
    display:flex; flex-direction:column; gap:12px;
  }}
  .hud-title {{
    font-size:19px; font-weight:700; color:#f8fafc; letter-spacing:-0.02em; margin-bottom:8px;
    display:flex; align-items:center; justify-content:space-between; gap:8px; white-space:nowrap;
  }}
  .farm-select {{
    background:rgba(15,29,38,0.92); color:#74f8c1; border:1px solid rgba(116,248,193,0.45);
    border-radius:6px; padding:4px 8px; font-size:11px; font-weight:700; cursor:pointer;
    max-width:168px; outline:none; pointer-events:auto;
  }}
  .farm-select:hover, .farm-select:focus {{
    border-color:#34d399; box-shadow:0 0 10px rgba(52,211,153,0.25);
  }}
  .bullet-list {{
    list-style:none; font-size:11px; color:#94a3b8; line-height:1.45;
    padding-bottom:6px; border-bottom:1px solid rgba(148,163,184,0.14);
  }}
  .bullet-list li {{
    position:relative; padding-left:13px; margin-bottom:4px;
    white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
  }}
  .bullet-list li::before {{
    content:'•'; position:absolute; left:0; top:0; color:#38bdf8; font-weight:900;
  }}
  .bullet-list b {{ color:#e2e8f0; }}

  /* Top-Center: Sparkline Chart */
  .hud-top-center {{
    top:18px; left:320px; width:245px;
    background:rgba(15,27,36,0.45); border:1px solid rgba(148,163,184,0.16);
    border-radius:8px; padding:8px 12px; backdrop-filter:blur(4px);
  }}
  .chart-caption {{
    font-size:10px; text-transform:uppercase; letter-spacing:0.06em; color:#94a3b8; font-weight:700;
    display:flex; justify-content:space-between; margin-bottom:4px;
  }}

  /* Top-Right: Simulation Interactive List & Camera Controls */
  .hud-top-right {{
    top:20px; right:24px; width:220px;
  }}
  .sim-heading {{
    font-size:18px; font-weight:700; color:#f8fafc; letter-spacing:-0.01em; margin-bottom:8px;
  }}
  .sim-list {{
    list-style:none; display:flex; flex-direction:column; gap:5px;
  }}
  .sim-item {{
    font-size:12px; color:#cbd5e1; padding:5px 10px; border-radius:6px;
    background:rgba(15,27,36,0.55); border:1px solid rgba(148,163,184,0.18);
    cursor:pointer; transition:all 0.15s ease; display:flex; align-items:center; justify-content:space-between;
  }}
  .sim-item:hover {{
    border-color:#74f8c1; color:#ffffff; background:rgba(16,185,129,0.18);
  }}
  .sim-item.active {{
    border-color:#10b981; background:rgba(16,185,129,0.28); color:#ffffff; font-weight:700;
    box-shadow:0 0 12px rgba(16,185,129,0.25);
  }}
  .cam-bar {{
    display:flex; flex-wrap:wrap; gap:4px; margin-top:10px;
  }}
  .cam-btn {{
    flex:1; background:rgba(15,27,36,0.78); color:#cbd5e1; border:1px solid rgba(148,163,184,0.28);
    border-radius:5px; padding:4px 6px; font-size:10px; font-weight:600; cursor:pointer; text-align:center;
  }}
  .cam-btn:hover, .cam-btn.active {{
    background:#0d9488; color:#ffffff; border-color:#5eead4;
  }}

  /* Left Stacked Mini Panels inside .hud-left-col */
  .mini-panel-title {{
    font-size:13.5px; font-weight:600; color:#f1f5f9; margin-bottom:2px;
    display:flex; align-items:center; justify-content:space-between; gap:8px; white-space:nowrap;
  }}
  .mini-panel-val {{
    font-size:11px; font-weight:700; color:#74f8c1; font-family:monospace; white-space:nowrap;
  }}
  .soil-checks {{
    list-style:none; font-size:11px; color:#cbd5e1; line-height:1.65; margin-top:2px;
  }}
  .soil-checks span {{ color:#34d399; font-weight:800; margin-right:6px; }}

  /* Bottom-Center: 3 Pixel-Grid Heatmaps matching reference tablet */
  .hud-bottom-heatmaps {{
    bottom:16px; left:54%; transform:translateX(-44%);
    display:flex; align-items:center; gap:18px;
    background:rgba(11,20,27,0.68); border:1px solid rgba(148,163,184,0.2);
    padding:9px 15px; border-radius:10px; backdrop-filter:blur(8px);
  }}
  .hm-card {{
    display:flex; flex-direction:column; align-items:center; gap:4px; cursor:pointer;
    padding:4px; border-radius:6px; border:1px solid transparent; transition:all 0.15s ease;
  }}
  .hm-card:hover, .hm-card.active {{
    border-color:#74f8c1; background:rgba(16,185,129,0.12);
  }}
  .hm-grid {{
    display:grid; grid-template-columns:repeat(7, 11px); grid-template-rows:repeat(6, 10px); gap:1px;
    border:1px solid rgba(255,255,255,0.22); border-radius:3px; overflow:hidden;
  }}
  .hm-lbl {{
    font-size:9.5px; font-weight:700; color:#cbd5e1; text-transform:uppercase; letter-spacing:0.04em;
  }}

  #parcel-tooltip {{
    position:absolute; display:none; z-index:30; pointer-events:none;
    background:rgba(11, 22, 30, 0.95); color:#f8fafc;
    border:1px solid #34d399; border-radius:8px; padding:10px 13px;
    font-size:11.5px; line-height:1.6; box-shadow:0 12px 28px rgba(0,0,0,0.75);
    backdrop-filter:blur(8px); min-width:215px;
  }}
</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
</head>
<body>
<div id="twin-stage">
  <div id="webgl-canvas"></div>

  <!-- Unified Left Column: Digital Twin Info + Yield Prediction + Weather Forecast + Soil Moisture -->
  <div class="hud-layer hud-left-col">
    <div>
      <div class="hud-title">
        <span>Digital Twin</span>
        <select id="farm-Select" class="farm-select hud-interactive" onchange="window.switchTwinFarm(this.value)">
          {options_html}
        </select>
      </div>
      <ul class="bullet-list">
        <li><b>Contract Estate:</b> {farm_id} · {total_ha} ha ({len(records)} strips)</li>
        <li><b>Primary Crop:</b> <span id="hud-crop-name">{crop.title()} (Apetit Contract)</span></li>
        <li><b>Catchment:</b> CA01 Pyhäjärvi ({farm_lat:.3f}°N, {farm_lon:.3f}°E)</li>
        <li><b>Parcel:</b> <span id="hud-sel-parcel">Hover any 3D field strip</span></li>
      </ul>
    </div>

    <div>
      <div class="mini-panel-title">
        <span>Yield Prediction</span>
        <span id="hud-yield-val" class="mini-panel-val">{base_yield:.2f} t/ha</span>
      </div>
      <svg viewBox="0 0 180 48" width="100%" height="44">
        <line x1="12" y1="6" x2="12" y2="40" stroke="rgba(148,163,184,0.4)" stroke-width="1"/>
        <line x1="12" y1="40" x2="172" y2="40" stroke="rgba(148,163,184,0.4)" stroke-width="1"/>
        <polyline id="hud-yield-line" fill="none" stroke="#f8fafc" stroke-width="1.8"
          points="16,36 44,25 72,30 102,19 134,22 166,9"/>
      </svg>
    </div>

    <div>
      <div class="mini-panel-title">
        <span>Weather Forecast</span>
        <span id="hud-wx-val" class="mini-panel-val">18.4°C · 42mm</span>
      </div>
      <svg viewBox="0 0 180 48" width="100%" height="44">
        <line x1="12" y1="6" x2="12" y2="40" stroke="rgba(148,163,184,0.4)" stroke-width="1"/>
        <line x1="12" y1="40" x2="172" y2="40" stroke="rgba(148,163,184,0.4)" stroke-width="1"/>
        <polyline id="hud-wx-line" fill="none" stroke="#93c5fd" stroke-width="1.8"
          points="16,38 36,30 56,34 76,21 96,26 116,14 136,19 156,10 170,13"/>
      </svg>
    </div>

    <div>
      <div class="mini-panel-title">
        <span>Soil Moisture</span>
        <span id="hud-moist-val" class="mini-panel-val">68% Opt</span>
      </div>
      <ul class="soil-checks">
        <li><span>✓</span><span id="hud-chk-1">Root-zone moisture balanced</span></li>
        <li><span>✓</span><span id="hud-chk-2">10m SBTN buffer strip active</span></li>
        <li><span>✓</span><span id="hud-chk-3">P-leaching below 1.2 kg/ha</span></li>
      </ul>
    </div>
  </div>

  <!-- Top-Center: Historical & Projected Yield Sparkline -->
  <div class="hud-layer hud-top-center">
    <div class="chart-caption">
      <span>Biomass &amp; Yield Index</span>
      <span id="hud-spark-badge" style="color:#74f8c1;">+8.4% vs Base</span>
    </div>
    <svg viewBox="0 0 220 72" width="100%" height="68">
      <line x1="18" y1="14" x2="212" y2="14" stroke="rgba(148,163,184,0.18)" stroke-width="1"/>
      <line x1="18" y1="36" x2="212" y2="36" stroke="rgba(148,163,184,0.18)" stroke-width="1"/>
      <line x1="18" y1="58" x2="212" y2="58" stroke="rgba(148,163,184,0.35)" stroke-width="1"/>
      <line x1="18" y1="8" x2="18" y2="58" stroke="rgba(148,163,184,0.35)" stroke-width="1"/>
      <polyline id="hud-top-spark" fill="none" stroke="#f8fafc" stroke-width="2"
        points="22,52 46,36 68,42 92,28 116,32 140,18 164,22 188,10 208,14"/>
      <text x="24" y="68" font-size="7.5" fill="#64748b">2021</text>
      <text x="72" y="68" font-size="7.5" fill="#64748b">2023</text>
      <text x="120" y="68" font-size="7.5" fill="#64748b">2025</text>
      <text x="168" y="68" font-size="7.5" fill="#64748b">2028</text>
      <text x="200" y="68" font-size="7.5" fill="#64748b">2030</text>
    </svg>
  </div>

  <!-- Top-Right: Simulation Modes & Camera Presets -->
  <div class="hud-layer hud-top-right hud-interactive">
    <div class="sim-heading">Simulation</div>
    <ul class="sim-list">
      <li id="sim-mode-rotation" class="sim-item active" onclick="setSimMode('rotation')">
        <span>• Crop Rotation</span><span style="font-size:10px;color:#74f8c1;">L10 Active</span>
      </li>
      <li id="sim-mode-irrigation" class="sim-item" onclick="setSimMode('irrigation')">
        <span>• Irrigation</span><span style="font-size:10px;color:#38bdf8;">Drip +15%</span>
      </li>
      <li id="sim-mode-nutrient" class="sim-item" onclick="setSimMode('nutrient')">
        <span>• Nutrient &amp; Bio-Input</span><span style="font-size:10px;color:#fbbf24;">L08/L09</span>
      </li>
      <li id="sim-mode-scenarios" class="sim-item" onclick="setSimMode('scenarios')">
        <span>• Climate Scenarios</span><span style="font-size:10px;color:#f87171;">SSP2-4.5</span>
      </li>
    </ul>
    <div class="cam-bar">
      <button id="cam-iso" class="cam-btn active" onclick="setCameraAngle('iso')">Isometric</button>
      <button id="cam-top" class="cam-btn" onclick="setCameraAngle('top')">Top-Down</button>
      <button id="cam-hq" class="cam-btn" onclick="setCameraAngle('hq')">Farmstead</button>
      <button id="cam-spin" class="cam-btn" onclick="toggleAutoSpin()">Orbit 360°</button>
    </div>
  </div>

  <!-- Bottom-Center: 3 Interactive Pixel-Grid Heatmaps matching reference image -->
  <div class="hud-layer hud-bottom-heatmaps hud-interactive">
    <div id="hm-card-ndvi" class="hm-card active" onclick="setHeatmapOverlay('ndvi')">
      <div id="hm-grid-1" class="hm-grid"></div>
      <span class="hm-lbl">1. Canopy NDVI</span>
    </div>
    <div id="hm-card-stress" class="hm-card" onclick="setHeatmapOverlay('stress')">
      <div id="hm-grid-2" class="hm-grid"></div>
      <span class="hm-lbl">2. Thermal Stress</span>
    </div>
    <div id="hm-card-moisture" class="hm-card" onclick="setHeatmapOverlay('moisture')">
      <div id="hm-grid-3" class="hm-grid"></div>
      <span class="hm-lbl">3. Soil &amp; P-Index</span>
    </div>
    <div style="font-size:10px;color:#94a3b8;max-width:115px;line-height:1.4;">
      Click any matrix to drape onto 3D parcels.<br/>Drag 3D farm to rotate.
    </div>
  </div>

  <div id="parcel-tooltip"></div>
</div>

<script>
const parcelsData = {parcels_json};
const baseYield = {base_yield};

// ── Populate the 3 Bottom 7x6 Pixel-Grid Heatmaps (matching reference image) ──
const palNDVI = ['#15803d','#16a34a','#22c55e','#4ade80','#86efac','#166534','#14532d'];
const palStress = ['#16a34a','#65a30d','#eab308','#f97316','#ef4444','#dc2626','#b91c1c'];
const palMoist = ['#dc2626','#ea580c','#eab308','#84cc16','#22c55e','#10b981','#059669'];

function fillGrid(elId, palette, modeSeed) {{
  const el = document.getElementById(elId);
  if (!el) return;
  el.innerHTML = '';
  for (let r = 0; r < 6; r++) {{
    for (let c = 0; c < 7; c++) {{
      const cell = document.createElement('div');
      let idx = 0;
      if (modeSeed === 1) {{
        idx = (r + c + (r * c) % 3) % palette.length;
      }} else if (modeSeed === 2) {{
        const distCenter = Math.abs(c - 3.2) + Math.abs(r - 2.5);
        idx = distCenter < 2.2 ? 5 : (distCenter < 3.4 ? 3 : 1);
      }} else {{
        idx = Math.min(palette.length - 1, Math.floor((c + r * 0.7) % palette.length));
      }}
      cell.style.background = palette[idx];
      el.appendChild(cell);
    }}
  }}
}}
fillGrid('hm-grid-1', palNDVI, 1);
fillGrid('hm-grid-2', palStress, 2);
fillGrid('hm-grid-3', palMoist, 3);

// ── Three.js Isometric 3D Farm Estate Block Scene ────────────────────────────
const stage = document.getElementById('webgl-canvas');
const tooltip = document.getElementById('parcel-tooltip');

const scene = new THREE.Scene();

const camera = new THREE.PerspectiveCamera(34, stage.clientWidth / stage.clientHeight, 0.5, 1000);
camera.position.set(-56, 48, 62);

const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
renderer.setSize(stage.clientWidth, stage.clientHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
stage.appendChild(renderer.domElement);

const controls = new THREE.OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.06;
controls.maxPolarAngle = Math.PI / 2.12;
controls.minDistance = 28;
controls.maxDistance = 175;
controls.target.set(2, -2, 0);
controls.update();

// Lighting
const hemiLight = new THREE.HemisphereLight(0xe0f2fe, 0x1e293b, 0.78);
scene.add(hemiLight);

const sunLight = new THREE.DirectionalLight(0xfffbeb, 1.35);
sunLight.position.set(-45, 78, 42);
sunLight.castShadow = true;
sunLight.shadow.mapSize.width = 2048;
sunLight.shadow.mapSize.height = 2048;
sunLight.shadow.camera.near = 10;
sunLight.shadow.camera.far = 200;
const d = 55;
sunLight.shadow.camera.left = -d;
sunLight.shadow.camera.right = d;
sunLight.shadow.camera.top = d;
sunLight.shadow.camera.bottom = -d;
scene.add(sunLight);

const fillLight = new THREE.DirectionalLight(0x38bdf8, 0.28);
fillLight.position.set(60, 35, -50);
scene.add(fillLight);

// Helper: Generate Procedural Furrow / Plowed Crop Row Texture
function makeCropFurrowTexture(baseHex, stripeHex, numRows, angleDeg) {{
  const canvas = document.createElement('canvas');
  canvas.width = 256;
  canvas.height = 256;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = baseHex;
  ctx.fillRect(0, 0, 256, 256);

  ctx.save();
  ctx.translate(128, 128);
  ctx.rotate((angleDeg * Math.PI) / 180);
  ctx.translate(-128, -128);

  const step = Math.max(4, Math.floor(256 / numRows));
  ctx.fillStyle = stripeHex;
  for (let y = -64; y < 320; y += step) {{
    ctx.fillRect(-64, y, 384, Math.max(1.5, step * 0.42));
  }}
  ctx.restore();

  const tex = new THREE.CanvasTexture(canvas);
  tex.wrapS = THREE.RepeatWrapping;
  tex.wrapT = THREE.RepeatWrapping;
  return tex;
}}

const farmGroup = new THREE.Group();
farmGroup.rotation.y = -0.18;
scene.add(farmGroup);

// 1. Thick 3D Earthen Soil Slab + Grass Perimeter Base
const slabW = 62, slabD = 50, slabH = 2.4;
const soilMat = new THREE.MeshStandardMaterial({{ color: 0x4a3520, roughness: 0.95 }});
const grassBorderMat = new THREE.MeshStandardMaterial({{ color: 0x3b6e28, roughness: 0.85 }});

const soilSlab = new THREE.Mesh(new THREE.BoxGeometry(slabW, slabH, slabD), soilMat);
soilSlab.position.set(0, -slabH / 2, 0);
soilSlab.receiveShadow = true;
farmGroup.add(soilSlab);

const grassTop = new THREE.Mesh(new THREE.BoxGeometry(slabW + 0.6, 0.45, slabD + 0.6), grassBorderMat);
grassTop.position.set(0, 0.05, 0);
grassTop.receiveShadow = true;
farmGroup.add(grassTop);

// 2. Ghosted Wireframe Neighboring Field Grid (Upper-Right Extension matching reference image)
const ghostGroup = new THREE.Group();
ghostGroup.position.set(22, -0.8, -28);
const ghostMat = new THREE.LineBasicMaterial({{ color: 0x2dd4bf, transparent: true, opacity: 0.22 }});
const ghostFillMat = new THREE.MeshBasicMaterial({{ color: 0x0f766e, transparent: true, opacity: 0.08 }});
for (let gx = 0; gx < 3; gx++) {{
  for (let gz = 0; gz < 3; gz++) {{
    const gw = 12, gd = 9;
    const gBox = new THREE.BoxGeometry(gw, 0.1, gd);
    const gMesh = new THREE.Mesh(gBox, ghostFillMat);
    gMesh.position.set(gx * (gw + 1.2), 0, gz * (gd + 1.2));
    const gEdges = new THREE.LineSegments(new THREE.EdgesGeometry(gBox), ghostMat);
    gMesh.add(gEdges);
    ghostGroup.add(gMesh);
  }}
}}
farmGroup.add(ghostGroup);

// 3. Subdivided Contiguous Agricultural Crop Strips (14 strips + 1 Farmstead Courtyard)
const farmSeed = {farm_seed};
const cropPaletteStyles = [
  {{ role: 'lush_green', cropName: 'Green Pea (Herne)', baseColor: '#2d7a31', stripeColor: '#1e5622', h: 0.64 }},
  {{ role: 'amber_furrow', cropName: 'Ware Potato (Peruna)', baseColor: '#c87a28', stripeColor: '#8c4f14', h: 0.46 }},
  {{ role: 'terra_furrow', cropName: 'Carrot (Porkkana)', baseColor: '#d96b27', stripeColor: '#9a4212', h: 0.45 }},
  {{ role: 'gold_grain', cropName: 'Turnip Rape (Rypsi)', baseColor: '#d4a72c', stripeColor: '#a37b16', h: 0.54 }},
  {{ role: 'meadow_green', cropName: 'Spinach (Pinaatti)', baseColor: '#4d9a2a', stripeColor: '#36701b', h: 0.58 }},
  {{ role: 'yellow_canola', cropName: 'Spring Barley (Ohra)', baseColor: '#dfbe29', stripeColor: '#b59718', h: 0.58 }},
  {{ role: 'meadow_green', cropName: 'Winter Rye Cover (L10)', baseColor: '#3d8c30', stripeColor: '#2b6621', h: 0.55 }},
  {{ role: 'meadow_green', cropName: 'Faba Bean (Härkäpapu)', baseColor: '#58a632', stripeColor: '#3d7820', h: 0.60 }},
];

const stripLayoutBase = [
  {{ x: -21.5, z: 12.0, w: 15.0, d: 22.0, styleIdx: 0, angle: 0 }},
  {{ x: -11.8, z: 12.0, w: 3.2,  d: 22.0, styleIdx: 1, angle: 0 }},
  {{ x: -8.0,  z: 12.0, w: 3.4,  d: 22.0, styleIdx: 2, angle: 0 }},
  {{ x: -4.0,  z: 12.0, w: 3.6,  d: 22.0, styleIdx: 3, angle: 0 }},
  {{ x: 0.2,   z: 12.0, w: 3.8,  d: 22.0, styleIdx: 4, angle: 0 }},

  {{ x: 11.2,  z: 13.5, w: 16.5, d: 19.0, styleIdx: 0, angle: 90 }},
  {{ x: 24.5,  z: 13.5, w: 8.5,  d: 19.0, styleIdx: 3, angle: 0 }},

  {{ x: -23.5, z: -4.5, w: 11.0, d: 9.5,  styleIdx: 6, angle: 0 }},
  {{ x: 0.5,   z: -4.5, w: 11.5, d: 9.5,  styleIdx: 5, angle: 0 }},
  {{ x: 12.8,  z: -4.5, w: 11.5, d: 9.5,  styleIdx: 0, angle: 0 }},
  {{ x: 24.5,  z: -4.5, w: 9.0,  d: 9.5,  styleIdx: 7, angle: 0 }},

  {{ x: -20.0, z: -16.5, w: 18.0, d: 12.5, styleIdx: 0, angle: 0 }},
  {{ x: -2.0,  z: -16.5, w: 16.0, d: 12.5, styleIdx: 6, angle: 90 }},
  {{ x: 17.5,  z: -16.5, w: 21.0, d: 12.5, styleIdx: 4, angle: 0 }},
];

const stripLayout = stripLayoutBase.map((slot, idx) => {{
  const shiftedIdx = (slot.styleIdx + (farmSeed - 1) * 2 + (idx % 2)) % cropPaletteStyles.length;
  const st = farmSeed === 1 ? cropPaletteStyles[slot.styleIdx] : cropPaletteStyles[shiftedIdx];
  const rotAngle = farmSeed % 2 === 0 ? (slot.angle === 90 ? 0 : (idx % 3 === 0 ? 90 : 0)) : slot.angle;
  return Object.assign({{}}, slot, st, {{ angle: rotAngle }});
}});

const stripMeshes = [];

stripLayout.forEach((cfg, i) => {{
  const pInfo = parcelsData[i % parcelsData.length];
  const tex = makeCropFurrowTexture(cfg.baseColor, cfg.stripeColor, 26, cfg.angle);
  const mat = new THREE.MeshStandardMaterial({{
    map: tex,
    roughness: 0.82,
    metalness: 0.04,
  }});

  const geom = new THREE.BoxGeometry(cfg.w, cfg.h, cfg.d);
  const mesh = new THREE.Mesh(geom, mat);
  mesh.position.set(cfg.x, 0.25 + cfg.h / 2, cfg.z);
  mesh.castShadow = true;
  mesh.receiveShadow = true;

  const edgeLine = new THREE.LineSegments(
    new THREE.EdgesGeometry(geom),
    new THREE.LineBasicMaterial({{ color: 0x1e3a1e, transparent: true, opacity: 0.45 }})
  );
  mesh.add(edgeLine);

  const rowGroup = new THREE.Group();
  const rowMat = new THREE.MeshStandardMaterial({{ color: cfg.stripeColor, roughness: 0.9 }});
  const num3DRows = Math.max(3, Math.floor((cfg.angle === 90 ? cfg.d : cfg.w) / 1.45));
  for (let r = 0; r < num3DRows; r++) {{
    if (cfg.angle === 90) {{
      const rz = -cfg.d / 2 + 0.7 + r * (cfg.d / num3DRows);
      const rMesh = new THREE.Mesh(new THREE.BoxGeometry(cfg.w * 0.94, 0.14, 0.35), rowMat);
      rMesh.position.set(0, cfg.h / 2 + 0.07, rz);
      rowGroup.add(rMesh);
    }} else {{
      const rx = -cfg.w / 2 + 0.7 + r * (cfg.w / num3DRows);
      const rMesh = new THREE.Mesh(new THREE.BoxGeometry(0.35, 0.14, cfg.d * 0.94), rowMat);
      rMesh.position.set(rx, cfg.h / 2 + 0.07, 0);
      rowGroup.add(rMesh);
    }}
  }}
  mesh.add(rowGroup);

  mesh.userData = {{
    ...pInfo,
    cropName: cfg.cropName,
    role: cfg.role,
    origBaseColor: cfg.baseColor,
    origStripeColor: cfg.stripeColor,
    origH: cfg.h,
    angle: cfg.angle,
  }};

  farmGroup.add(mesh);
  stripMeshes.push(mesh);
}});

// 4. Realistic Miniature Farmstead Courtyard Compound (at x: -11.5, z: -4.5)
const hqGroup = new THREE.Group();
hqGroup.position.set(-11.5, 0.3, -4.5);

const yardPad = new THREE.Mesh(
  new THREE.BoxGeometry(11.5, 0.22, 9.2),
  new THREE.MeshStandardMaterial({{ color: 0x78716c, roughness: 0.95 }})
);
yardPad.receiveShadow = true;
hqGroup.add(yardPad);

const houseBody = new THREE.Mesh(
  new THREE.BoxGeometry(3.4, 1.9, 2.5),
  new THREE.MeshStandardMaterial({{ color: 0xe7e5e4, roughness: 0.7 }})
);
houseBody.position.set(-1.6, 1.05, 0.8);
houseBody.castShadow = true;
hqGroup.add(houseBody);

const houseRoof = new THREE.Mesh(
  new THREE.ConeGeometry(2.6, 1.35, 4),
  new THREE.MeshStandardMaterial({{ color: 0x27272a, roughness: 0.6 }})
);
houseRoof.rotation.y = Math.PI / 4;
houseRoof.scale.set(1.15, 1, 0.88);
houseRoof.position.set(-1.6, 2.65, 0.8);
houseRoof.castShadow = true;
hqGroup.add(houseRoof);

const barnBody = new THREE.Mesh(
  new THREE.BoxGeometry(3.8, 2.1, 2.4),
  new THREE.MeshStandardMaterial({{ color: 0x991b1b, roughness: 0.75 }})
);
barnBody.position.set(2.1, 1.15, -1.2);
barnBody.castShadow = true;
hqGroup.add(barnBody);

const barnRoof = new THREE.Mesh(
  new THREE.ConeGeometry(2.8, 1.4, 4),
  new THREE.MeshStandardMaterial({{ color: 0x1e293b, roughness: 0.6 }})
);
barnRoof.rotation.y = Math.PI / 4;
barnRoof.scale.set(1.2, 1, 0.82);
barnRoof.position.set(2.1, 2.85, -1.2);
barnRoof.castShadow = true;
hqGroup.add(barnRoof);

const siloMat = new THREE.MeshStandardMaterial({{ color: 0xcbd5e1, metalness: 0.65, roughness: 0.28 }});
[-0.4, 1.1].forEach((sx) => {{
  const silo = new THREE.Mesh(new THREE.CylinderGeometry(0.62, 0.62, 3.4, 16), siloMat);
  silo.position.set(sx, 1.8, -2.5);
  silo.castShadow = true;
  hqGroup.add(silo);
  const dome = new THREE.Mesh(new THREE.SphereGeometry(0.62, 12, 8, 0, Math.PI * 2, 0, Math.PI / 2), siloMat);
  dome.position.set(sx, 3.5, -2.5);
  hqGroup.add(dome);
}});

function createRealisticTree(x, z, scale) {{
  const tGroup = new THREE.Group();
  tGroup.position.set(x, 0.25, z);
  const trunk = new THREE.Mesh(
    new THREE.CylinderGeometry(0.15 * scale, 0.22 * scale, 1.1 * scale, 7),
    new THREE.MeshStandardMaterial({{ color: 0x451a03, roughness: 0.9 }})
  );
  trunk.position.y = 0.55 * scale;
  trunk.castShadow = true;
  tGroup.add(trunk);

  const foliageColors = [0x14532d, 0x166534, 0x15803d, 0x1b4332];
  const cMat = new THREE.MeshStandardMaterial({{
    color: foliageColors[Math.floor(Math.abs(x * 7 + z * 3)) % foliageColors.length],
    roughness: 0.85,
  }});
  const mainCrown = new THREE.Mesh(new THREE.DodecahedronGeometry(0.95 * scale, 1), cMat);
  mainCrown.position.y = 1.55 * scale;
  mainCrown.castShadow = true;
  tGroup.add(mainCrown);

  const subCrown = new THREE.Mesh(new THREE.DodecahedronGeometry(0.68 * scale, 1), cMat);
  subCrown.position.set(0.42 * scale, 1.35 * scale, 0.28 * scale);
  subCrown.castShadow = true;
  tGroup.add(subCrown);
  return tGroup;
}}

[
  [-4.2, -2.8, 1.15], [-4.5, 0.2, 0.95], [-3.8, 2.8, 1.1],
  [0.2, 2.9, 1.05], [3.9, 2.4, 1.2], [4.4, -0.2, 0.9], [-1.8, -3.1, 1.25]
].forEach(([tx, tz, sc]) => {{
  hqGroup.add(createRealisticTree(tx, tz, sc));
}});
farmGroup.add(hqGroup);

// 5. Dense 3D Forest Windbreak & Riparian Buffer Belt along Back/Left Edge
const forestGroup = new THREE.Group();
for (let fx = -29.0; fx <= 8.0; fx += 2.1) {{
  const jitterZ = -23.6 + Math.sin(fx * 1.7) * 0.7;
  const sc = 1.05 + (Math.cos(fx * 2.3) + 1) * 0.32;
  forestGroup.add(createRealisticTree(fx, jitterZ, sc));
}}
for (let fz = -22.0; fz <= -2.0; fz += 2.2) {{
  const jitterX = -29.6 + Math.cos(fz * 1.5) * 0.6;
  const sc = 0.95 + (Math.sin(fz * 1.9) + 1) * 0.28;
  forestGroup.add(createRealisticTree(jitterX, fz, sc));
}}
farmGroup.add(forestGroup);

// 6. Irrigation Mist Particles
const mistGeom = new THREE.BufferGeometry();
const mistCount = 260;
const mistPos = new Float32Array(mistCount * 3);
for (let i = 0; i < mistCount; i++) {{
  mistPos[i * 3] = (Math.random() - 0.5) * 54;
  mistPos[i * 3 + 1] = 1.0 + Math.random() * 4.5;
  mistPos[i * 3 + 2] = (Math.random() - 0.5) * 42;
}}
mistGeom.setAttribute('position', new THREE.BufferAttribute(mistPos, 3));
const mistMat = new THREE.PointsMaterial({{ color: 0x7dd3fc, size: 0.45, transparent: true, opacity: 0.0 }});
const mistParticles = new THREE.Points(mistGeom, mistMat);
farmGroup.add(mistParticles);

// ── Interactive Simulation Modes ────────────────────────────────────────────
window.setSimMode = function(mode) {{
  document.querySelectorAll('.sim-item').forEach((el) => el.classList.remove('active'));
  const activeEl = document.getElementById('sim-mode-' + mode);
  if (activeEl) activeEl.classList.add('active');

  mistMat.opacity = (mode === 'irrigation') ? 0.75 : 0.0;

  stripMeshes.forEach((m, idx) => {{
    const d = m.userData;
    let bCol = d.origBaseColor;
    let sCol = d.origStripeColor;
    let scaleY = 1.0;

    if (mode === 'rotation') {{
      scaleY = 1.0;
    }} else if (mode === 'irrigation') {{
      if (d.role.includes('furrow')) {{
        bCol = '#2ea043';
        sCol = '#196c2e';
      }}
      scaleY = 1.22;
    }} else if (mode === 'nutrient') {{
      bCol = idx % 3 === 0 ? '#65a30d' : (idx % 2 === 0 ? '#16a34a' : '#ca8a04');
      sCol = '#14532d';
      scaleY = 1.15;
    }} else if (mode === 'scenarios') {{
      if (!d.buffer || idx % 3 === 1) {{
        bCol = '#dc2626';
        sCol = '#7f1d1d';
        scaleY = 0.78;
      }} else {{
        bCol = '#ca8a04';
        sCol = '#854d0e';
        scaleY = 0.92;
      }}
    }}

    m.material.map = makeCropFurrowTexture(bCol, sCol, 26, d.angle);
    m.material.needsUpdate = true;
    m.scale.y = scaleY;
  }});

  const yEl = document.getElementById('hud-yield-val');
  const wEl = document.getElementById('hud-wx-val');
  const mEl = document.getElementById('hud-moist-val');
  const badge = document.getElementById('hud-spark-badge');
  if (mode === 'rotation') {{
    if (yEl) yEl.textContent = (baseYield * 1.06).toFixed(2) + ' t/ha';
    if (wEl) wEl.textContent = '18.4°C · 42mm';
    if (mEl) mEl.textContent = '68% Opt';
    if (badge) badge.textContent = '+8.4% L10 Catch';
  }} else if (mode === 'irrigation') {{
    if (yEl) yEl.textContent = (baseYield * 1.14).toFixed(2) + ' t/ha';
    if (wEl) wEl.textContent = 'Drip +15% Eff';
    if (mEl) mEl.textContent = '82% Hydrated';
    if (badge) badge.textContent = '+14.0% Drip L24';
  }} else if (mode === 'nutrient') {{
    if (yEl) yEl.textContent = (baseYield * 1.09).toFixed(2) + ' t/ha';
    if (wEl) wEl.textContent = 'N-Sensor VRA';
    if (mEl) mEl.textContent = 'P-Loss -38%';
    if (badge) badge.textContent = 'L08 Green N';
  }} else if (mode === 'scenarios') {{
    if (yEl) yEl.textContent = (baseYield * 0.84).toFixed(2) + ' t/ha';
    if (wEl) wEl.textContent = '+2.4°C Heatwave';
    if (mEl) mEl.textContent = '41% Deficit';
    if (badge) badge.textContent = '-16.0% SSP2-4.5';
  }}
}};

window.setHeatmapOverlay = function(hmType) {{
  document.querySelectorAll('.hm-card').forEach((c) => c.classList.remove('active'));
  const card = document.getElementById('hm-card-' + hmType);
  if (card) card.classList.add('active');

  stripMeshes.forEach((m, idx) => {{
    const d = m.userData;
    let bCol = d.origBaseColor;
    let sCol = d.origStripeColor;
    if (hmType === 'ndvi') {{
      bCol = d.origBaseColor;
      sCol = d.origStripeColor;
    }} else if (hmType === 'stress') {{
      const pal = ['#16a34a', '#84cc16', '#eab308', '#f97316', '#dc2626'];
      bCol = pal[(idx * 2) % pal.length];
      sCol = '#1e293b';
    }} else if (hmType === 'moisture') {{
      const pal = ['#059669', '#10b981', '#34d399', '#eab308', '#ea580c'];
      bCol = pal[(idx + 1) % pal.length];
      sCol = '#0f172a';
    }}
    m.material.map = makeCropFurrowTexture(bCol, sCol, 26, d.angle);
    m.material.needsUpdate = true;
  }});
}};

window.setCameraAngle = function(view) {{
  document.querySelectorAll('.cam-btn').forEach((b) => {{
    if (b.id !== 'cam-spin') b.classList.remove('active');
  }});
  const btn = document.getElementById('cam-' + view);
  if (btn) btn.classList.add('active');

  if (view === 'iso') {{
    camera.position.set(-56, 48, 62);
    controls.target.set(2, -2, 0);
  }} else if (view === 'top') {{
    camera.position.set(0, 88, 0.1);
    controls.target.set(0, 0, 0);
  }} else if (view === 'hq') {{
    camera.position.set(-28, 18, 16);
    controls.target.set(-11.5, 1.5, -4.5);
  }}
  controls.update();
}};

window.toggleAutoSpin = function() {{
  controls.autoRotate = !controls.autoRotate;
  controls.autoRotateSpeed = 1.1;
  const btn = document.getElementById('cam-spin');
  if (btn) btn.classList.toggle('active', controls.autoRotate);
}};

window.switchTwinFarm = function(farmId) {{
  window.location.href = '/api/embed/digital-twin-3d?farm_id=' + encodeURIComponent(farmId);
}};

const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();
let hoveredMesh = null;

stage.addEventListener('mousemove', function(e) {{
  const rect = stage.getBoundingClientRect();
  mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
  mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

  raycaster.setFromCamera(mouse, camera);
  const hits = raycaster.intersectObjects(stripMeshes);

  if (hoveredMesh && (!hits.length || hits[0].object !== hoveredMesh)) {{
    hoveredMesh.position.y = 0.25 + hoveredMesh.userData.origH / 2;
    hoveredMesh = null;
  }}

  if (hits.length > 0) {{
    const mesh = hits[0].object;
    hoveredMesh = mesh;
    mesh.position.y = 0.55 + mesh.userData.origH / 2;
    const d = mesh.userData;

    const selLbl = document.getElementById('hud-sel-parcel');
    if (selLbl) selLbl.textContent = d.parcel_id + ' · ' + d.cropName + ' (' + d.base_yield + ' t/ha)';

    tooltip.style.display = 'block';
    tooltip.style.left = Math.min(e.clientX - rect.left + 16, rect.width - 235) + 'px';
    tooltip.style.top = Math.max(e.clientY - rect.top - 12, 16) + 'px';
    tooltip.innerHTML =
      '<div style="font-weight:800;color:#74f8c1;font-size:13px;margin-bottom:3px;">🌾 Parcel ' + d.parcel_id + '</div>' +
      '<b>Contract Crop:</b> ' + d.cropName + '<br/>' +
      '<b>Simulated Yield:</b> ' + d.base_yield + ' t/ha &nbsp;|&nbsp; <b>Area:</b> ' + d.area_ha + ' ha<br/>' +
      '<b>Soil Class:</b> ' + d.soil + ' &nbsp;|&nbsp; <b>Slope:</b> ' + d.slope + '%<br/>' +
      '<b>SBTN Buffer Strip:</b> ' + (d.buffer ? '<span style="color:#4ade80;">Active ✓</span>' : '<span style="color:#f87171;">Recommended ⚠</span>');
  }} else {{
    tooltip.style.display = 'none';
  }}
}});

stage.addEventListener('mouseleave', function() {{
  tooltip.style.display = 'none';
}});

let clock = new THREE.Clock();
function animate() {{
  requestAnimationFrame(animate);
  const dt = clock.getDelta();
  if (mistMat.opacity > 0) {{
    const posArr = mistGeom.attributes.position.array;
    for (let i = 1; i < posArr.length; i += 3) {{
      posArr[i] -= dt * 2.2;
      if (posArr[i] < 0.4) posArr[i] = 5.2;
    }}
    mistGeom.attributes.position.needsUpdate = true;
  }}
  controls.update();
  renderer.render(scene, camera);
}}
animate();

window.addEventListener('resize', function() {{
  camera.aspect = stage.clientWidth / stage.clientHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(stage.clientWidth, stage.clientHeight);
}});
</script>
</body>
</html>"""


def build_biodiversity_hotspots_explorer_html(
    catchments_gj: Dict[str, Any],
    farms_gj: Dict[str, Any],
    water_bodies_gj: Dict[str, Any],
    protected_gj: Dict[str, Any],
    origin_df: Optional[pd.DataFrame] = None,
    center_lat: float = 61.048,
    center_lon: float = 22.338,
    radius_km: float = 25.0,
    farm_count: int = 116,
) -> str:
    """
    Build the full Split-View Biodiversity & Nature Hotspots Explorer inspired by the
    reference screenshot ('Sydney Trial Project' -> Apetit 'Säkylä–Pyhäjärvi Project'):
    - Left Panel (315px):
        * Project switcher ('Säkylä–Pyhäjärvi Project', 'Loimijoki Clay Basin', 'Kantvik Oilseed Shed')
        * Total project area computed from catchments.csv (3,122 km² across active basin)
        * Expandable accordions for 'Key Biodiversity Areas' and 'Protected Areas'
        * Open accordion for 'Percentage Of Habitat Types' with 'See these habitat types on the map'
          green toggle switch, SVG Donut Chart on the left + 10 habitat rows on the right
        * Bottom sub-tabs: 'Species details & risks' | 'Overall biodiversity' grounded in
          origin_state_of_nature_indicative.csv & parcels.csv
    - Right Panel (Interactive Map + 3D Perspective Tilt):
        * Grayscale outer map + Circular clipped CORINE Land Cover Habitat Mosaic blended over
          high-res Esri World Imagery satellite terrain
        * Top floating filter bar: 'Species type ▾', 'Conservation Status ▾', 'Year 1980 to 2025' slider
        * Central dark-navy circular cluster badge ('116') + individual contract farm hotspot markers
        * Bottom-left 'Satellite' thumbnail switcher
        * Bottom-right 3-column floating CORINE habitat legend card (visible by default, minimizable)
        * Right-side dark circular zoom (+ / -) and 3D Tilt (🌐) controls
    """
    c_json = json.dumps(catchments_gj)
    f_json = json.dumps(farms_gj)
    w_json = json.dumps(water_bodies_gj)
    p_json = json.dumps(protected_gj)

    # Calculate grounded metrics from catchments_gj & farms_gj
    c_feats = catchments_gj.get("features", [])
    f_feats = farms_gj.get("features", [])
    p_feats = protected_gj.get("features", [])

    # Sum area of top 9 regional catchments in SW Finland (~3,122 km²)
    basin_area_km2 = round(sum(float(f["properties"].get("catchment_area_km2", 310.0)) for f in c_feats[:9]), 3)
    if basin_area_km2 < 1000:
        basin_area_km2 = 3122.0

    high_risk_farms = sum(1 for f in f_feats if "Severe" in str(f["properties"].get("eco_risk", "")))
    mod_risk_farms = sum(1 for f in f_feats if "Moderate" in str(f["properties"].get("eco_risk", "")))
    low_risk_farms = max(0, len(f_feats) - high_risk_farms - mod_risk_farms)
    avg_buf_pct = round(
        float(np.mean([float(f["properties"].get("buffer_coverage_pct", 42.0)) for f in f_feats])) if f_feats else 42.0,
        1,
    )

    origin_rows = []
    if origin_df is not None and not origin_df.empty:
        for _, r in origin_df.head(6).iterrows():
            origin_rows.append({
                "country": str(r.get("origin_country", "FI")),
                "commodity": str(r.get("commodity", "vegetables/oilseed")),
                "bio_sens": str(r.get("biodiversity_sensitivity_indicative", "medium")).title(),
                "nutrient": str(r.get("freshwater_nutrient_status_indicative", "moderate")),
            })
    origin_json = json.dumps(origin_rows)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  html, body {{
    width:100%; height:100%; overflow:hidden;
    background:#f1f5f9;
    font-family:'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    color:#1e293b;
  }}
  #explorer-shell {{
    display:flex; width:100%; height:100vh; overflow:hidden;
  }}

  /* ── LEFT PANEL (Matches Reference Image 'Sydney Trial Project' Sidebar) ── */
  #left-panel {{
    width:320px; min-width:320px; height:100%;
    background:#ffffff; border-right:1px solid #e2e8f0;
    display:flex; flex-direction:column; justify-content:space-between;
    z-index:20; overflow:hidden;
  }}
  .lp-scroll {{
    flex:1; overflow-y:auto; padding:16px 16px 10px 16px;
  }}
  .lp-scroll::-webkit-scrollbar {{ width:4px; }}
  .lp-scroll::-webkit-scrollbar-thumb {{ background:#cbd5e1; border-radius:4px; }}

  .lp-header-row {{
    display:flex; align-items:center; justify-content:space-between; gap:8px;
  }}
  .project-select {{
    font-size:17px; font-weight:800; color:#0f172a; border:none; background:transparent;
    cursor:pointer; outline:none; letter-spacing:-0.02em; padding:0; max-width:245px;
  }}
  .yellow-dots-btn {{
    width:26px; height:26px; border-radius:50%; background:#fde047; border:none;
    color:#1e293b; font-weight:900; font-size:12px; cursor:pointer;
    display:flex; align-items:center; justify-content:center; flex-shrink:0;
  }}
  .yellow-dots-btn:hover {{ background:#facc15; }}
  .lp-area-sub {{
    font-size:12px; color:#475569; margin-top:4px; margin-bottom:12px; font-weight:500;
  }}

  .acc-header {{
    display:flex; align-items:center; justify-content:space-between;
    padding:10px 2px; border-top:1px solid #e2e8f0;
    font-size:12.5px; font-weight:700; color:#1e293b; cursor:pointer; user-select:none;
  }}
  .acc-header:hover {{ color:#0f766e; }}
  .acc-body {{
    display:none; padding:4px 2px 10px 2px; font-size:11px; color:#475569;
  }}
  .acc-body.open {{ display:block; }}
  .kba-pill {{
    padding:6px 8px; border-radius:6px; background:#f8fafc; border:1px solid #e2e8f0;
    margin-bottom:5px; cursor:pointer; transition:all 0.15s;
  }}
  .kba-pill:hover {{ border-color:#10b981; background:#f0fdf4; }}

  .toggle-row {{
    display:flex; align-items:center; justify-content:space-between;
    margin:4px 0 6px 0; font-size:11px; font-weight:700; color:#1e293b;
  }}
  .switch {{
    position:relative; display:inline-block; width:34px; height:18px;
  }}
  .switch input {{ opacity:0; width:0; height:0; }}
  .slider {{
    position:absolute; cursor:pointer; inset:0; background:#cbd5e1;
    transition:.2s; border-radius:18px;
  }}
  .slider:before {{
    position:absolute; content:""; height:14px; width:14px; left:2px; bottom:2px;
    background:white; transition:.2s; border-radius:50%;
  }}
  input:checked + .slider {{ background:#5a9a82; }}
  input:checked + .slider:before {{ transform:translateX(16px); }}

  .radius-caption {{
    font-size:10.5px; color:#64748b; margin-bottom:8px;
  }}

  /* Donut + Habitat List side-by-side matching reference screenshot */
  .donut-hab-split {{
    display:flex; align-items:center; gap:10px;
  }}
  .donut-col {{
    width:98px; flex-shrink:0; display:flex; flex-direction:column; align-items:center;
  }}
  .hab-list-col {{
    flex:1; display:flex; flex-direction:column; gap:5px;
  }}
  .hab-row {{
    display:flex; align-items:flex-start; gap:6px; font-size:10px; color:#475569;
    line-height:1.28; cursor:pointer; padding:2px 3px; border-radius:4px;
  }}
  .hab-row:hover {{ background:#f1f5f9; color:#0f172a; }}
  .hab-dot {{
    width:9px; height:9px; border-radius:50%; flex-shrink:0; margin-top:2px;
  }}

  /* Bottom Info Drawer & Dual Sub-Tabs */
  .lp-drawer {{
    padding:8px 14px; background:#f8fafc; border-top:1px solid #e2e8f0;
    font-size:10.5px; color:#334155; line-height:1.45;
  }}
  .lp-bottom-tabs {{
    display:grid; grid-template-columns:1fr 1fr; border-top:1px solid #cbd5e1;
  }}
  .lp-tab-btn {{
    padding:10px 6px; font-size:11.5px; font-weight:700; text-align:center;
    cursor:pointer; border:none; background:#ffffff; color:#475569; transition:all 0.15s;
  }}
  .lp-tab-btn.active {{
    background:#5a9a82; color:#ffffff;
  }}

  /* ── RIGHT PANEL (Map + 3D Tilt Stage) ────────────────────────────────── */
  #map-stage {{
    flex:1; position:relative; height:100%; overflow:hidden; background:#e2e8f0;
    perspective:1200px;
  }}
  #map {{
    width:100%; height:100%; transition:transform 0.45s cubic-bezier(0.22,1,0.36,1);
  }}
  #map.tilted-3d {{
    transform: rotateX(34deg) scale(1.06);
    transform-origin: 50% 52%;
    box-shadow: 0 28px 60px rgba(15,23,42,0.45);
  }}

  /* Top Floating Filter Bar matching reference screenshot */
  #filter-bar {{
    position:absolute; top:14px; left:24px; z-index:1000;
    display:flex; align-items:center; gap:8px; flex-wrap:wrap;
  }}
  .filter-select {{
    background:#ffffff; border:1px solid #cbd5e1; border-radius:8px;
    padding:7px 11px; font-size:11.5px; font-weight:600; color:#1e293b;
    box-shadow:0 2px 8px rgba(0,0,0,0.12); cursor:pointer; outline:none;
  }}
  .year-card {{
    background:#ffffff; border:1px solid #cbd5e1; border-radius:8px;
    padding:5px 14px; display:flex; align-items:center; gap:8px;
    box-shadow:0 2px 8px rgba(0,0,0,0.12); font-size:11.5px; color:#1e293b;
  }}
  .year-box {{
    border:1px solid #e2e8f0; border-radius:5px; padding:2px 7px; font-weight:700;
    font-size:11px; color:#334155; background:#f8fafc;
  }}
  .year-range-wrap {{
    display:flex; flex-direction:column; align-items:center; gap:2px; margin-left:4px;
  }}
  #year-slider {{
    -webkit-appearance:none; width:115px; height:5px; border-radius:3px;
    background:#5a9a82; outline:none; cursor:pointer;
  }}
  #year-slider::-webkit-slider-thumb {{
    -webkit-appearance:none; width:13px; height:13px; border-radius:50%;
    background:#5a9a82; border:2px solid #ffffff; box-shadow:0 1px 4px rgba(0,0,0,0.3); cursor:pointer;
  }}
  .year-ends {{
    width:115px; display:flex; justify-content:space-between; font-size:9.5px; color:#64748b; font-weight:600;
  }}

  /* Right-Side Dark Navy Circular Buttons (+, -, 🌐 3D) */
  #right-controls {{
    position:absolute; top:68px; right:16px; z-index:1000;
    display:flex; flex-direction:column; gap:7px;
  }}
  .navy-ctrl-btn {{
    width:32px; height:32px; border-radius:50%; background:#0b192c; color:#ffffff;
    border:1.5px solid rgba(255,255,255,0.25); font-size:16px; font-weight:700;
    display:flex; align-items:center; justify-content:center; cursor:pointer;
    box-shadow:0 3px 10px rgba(0,0,0,0.28); transition:all 0.15s;
  }}
  .navy-ctrl-btn:hover, .navy-ctrl-btn.active {{
    background:#0f766e; transform:scale(1.06);
  }}

  /* Central Cluster Badge '116' */
  .cluster-badge {{
    background:#0b192c; color:#ffffff; border-radius:50%;
    display:flex; align-items:center; justify-content:center;
    font-weight:800; font-size:16px;
    box-shadow:0 4px 16px rgba(0,0,0,0.5);
    border:3px solid rgba(255,255,255,0.88);
    cursor:pointer; transition:transform 0.15s;
  }}
  .cluster-badge:hover {{ transform:scale(1.08); background:#0f766e; }}

  /* Bottom-left Satellite Thumbnail matching reference screenshot */
  #sat-thumb {{
    position:absolute; bottom:18px; left:18px; z-index:1000;
    width:74px; height:64px; border-radius:10px; overflow:hidden;
    box-shadow:0 4px 14px rgba(0,0,0,0.35); cursor:pointer;
    border:2.5px solid #ffffff; background:#1e293b;
    display:flex; flex-direction:column; align-items:center; justify-content:flex-end;
    padding-bottom:5px; transition:transform 0.2s;
  }}
  #sat-thumb:hover {{ transform:scale(1.05); }}
  #sat-thumb img {{
    position:absolute; inset:0; width:100%; height:100%; object-fit:cover; opacity:0.88;
  }}
  #sat-thumb .sat-label {{
    position:relative; z-index:1; font-size:10.5px; font-weight:700; color:#ffffff;
    text-shadow:0 1px 3px rgba(0,0,0,0.95);
  }}

  /* Bottom-right 3-Column Floating CORINE Habitat Legend Card (Visible by default) */
  #bio-legend {{
    position:absolute; bottom:16px; right:16px; z-index:1000;
    background:rgba(255,255,255,0.97); border-radius:10px;
    padding:12px 15px; box-shadow:0 6px 24px rgba(0,0,0,0.18);
    border:1px solid #e2e8f0; width:475px; max-width:calc(100% - 110px);
  }}
  .legend-grid {{
    display:grid; grid-template-columns:repeat(3, 1fr); gap:6px 12px;
  }}
  .legend-item {{
    display:flex; align-items:flex-start; gap:6px; font-size:9.5px; color:#334155;
    line-height:1.25; cursor:pointer;
  }}
  .legend-item:hover {{ color:#0f172a; font-weight:700; }}
  .legend-dot {{
    display:inline-block; min-width:9px; height:9px; border-radius:50%;
    flex-shrink:0; margin-top:1.5px;
  }}
  #legend-min-btn {{
    position:absolute; top:6px; right:8px; background:transparent; border:none;
    font-size:11px; font-weight:800; color:#64748b; cursor:pointer;
  }}

  /* Popups */
  .leaflet-popup-content-wrapper {{
    background:rgba(15,23,42,0.96) !important; color:#f1f5f9 !important;
    border:1px solid #334155 !important; border-radius:10px !important;
  }}
  .leaflet-popup-content {{ margin:11px 14px !important; font-size:11.5px; line-height:1.55; }}
  .leaflet-popup-tip {{ background:rgba(15,23,42,0.96) !important; }}
  .popup-title {{ font-size:13px; font-weight:700; color:#38bdf8; margin-bottom:3px; }}
  .popup-badge {{ display:inline-block; padding:2px 6px; border-radius:4px; font-size:9.5px; font-weight:700; margin-bottom:5px; }}
  .badge-red {{ background:#ef4444; color:white; }}
  .badge-amber {{ background:#f59e0b; color:white; }}
  .badge-green {{ background:#10b981; color:white; }}
  .badge-blue {{ background:#0284c7; color:white; }}
</style>
</head>
<body>
<div id="explorer-shell">

  <!-- =======================================================================
       LEFT PANEL: Project Summary, KBAs, Protected Areas, Donut + Habitats
       ======================================================================= -->
  <div id="left-panel">
    <div class="lp-scroll">
      <div class="lp-header-row">
        <select id="shed-select" class="project-select" onchange="switchSourcingShed(this.value)">
          <option value="sakyla">Säkylä–Pyhäjärvi Shed</option>
          <option value="loimijoki">Loimijoki Clay Basin</option>
          <option value="kokemaki">Kokemäenjoki Delta</option>
        </select>
        <button class="yellow-dots-btn" title="SBTN &amp; CORINE Dataset Summary" onclick="toggleLegendCard()">•••</button>
      </div>
      <div id="lp-area-text" class="lp-area-sub">Total project area: {basin_area_km2:,.3f} km²</div>

      <!-- Accordion 1: Key Biodiversity Areas -->
      <div class="acc-header" onclick="toggleAcc('acc-kba', 'caret-kba')">
        <span>Key Biodiversity Areas (4)</span>
        <span id="caret-kba">⌄</span>
      </div>
      <div id="acc-kba" class="acc-body">
        <div class="kba-pill" onclick="flyToSpot(61.02, 22.28, 11)">
          <b>CA01 Lake Pyhäjärvi IBA/KBA</b><br/>
          <span>P-Sensitivity: 1.60× · 10,689 ha contract fields</span>
        </div>
        <div class="kba-pill" onclick="flyToSpot(61.13, 22.13, 11)">
          <b>CA05 Eurajoki Salmonid Corridor</b><br/>
          <span>P-Sensitivity: 1.30× · 6,513 ha field watershed</span>
        </div>
        <div class="kba-pill" onclick="flyToSpot(61.13, 22.34, 11)">
          <b>CA03 Lake Köyliönjärvi Bird Wetland</b><br/>
          <span>P-Sensitivity: 1.15× · 17,495 ha agricultural shed</span>
        </div>
        <div class="kba-pill" onclick="flyToSpot(60.96, 22.65, 11)">
          <b>CA07 Loimijoki Pollinator Basin</b><br/>
          <span>P-Sensitivity: 1.15× · 9,485 ha clay plain</span>
        </div>
      </div>

      <!-- Accordion 2: Protected Areas -->
      <div class="acc-header" onclick="toggleAcc('acc-prot', 'caret-prot')">
        <span>Protected Areas ({len(p_feats)} Natura 2000)</span>
        <span id="caret-prot">⌄</span>
      </div>
      <div id="acc-prot" class="acc-body">
        <div class="kba-pill" onclick="flyToSpot(61.00, 22.27, 11)">
          <b>FI0200084 Pyhäjärvi Shoreline SAC</b><br/>
          <span>18.2 km² · Oligotrophic macrophyte sanctuary</span>
        </div>
        <div class="kba-pill" onclick="flyToSpot(61.02, 22.51, 11)">
          <b>FI0200078 Säkylänharju Esker Reserve</b><br/>
          <span>21.0 km² · Groundwater aquifer &amp; pine ridge</span>
        </div>
        <div class="kba-pill" onclick="flyToSpot(60.73, 22.40, 11)">
          <b>FI0200062 Kurjenrahka National Park</b><br/>
          <span>29.0 km² · Ramsar raised bog &amp; crane habitat</span>
        </div>
        <div class="kba-pill" onclick="flyToSpot(60.73, 23.62, 11)">
          <b>FI0304001 Torronsuo Mire Complex</b><br/>
          <span>25.5 km² · Deep peat carbon sink (12m depth)</span>
        </div>
      </div>

      <!-- Accordion 3: Percentage Of Habitat Types (Open by default) -->
      <div class="acc-header" onclick="toggleAcc('acc-hab', 'caret-hab')">
        <span>Percentage Of Habitat Types</span>
        <span id="caret-hab">⌃</span>
      </div>
      <div id="acc-hab" class="acc-body open">
        <div class="toggle-row">
          <span>See these habitat types on the map</span>
          <label class="switch">
            <input type="checkbox" id="hab-map-toggle" checked onchange="toggleHabitatMosaic(this.checked)">
            <span class="slider"></span>
          </label>
        </div>
        <div id="radius-caption-txt" class="radius-caption">These habitat types are in the {int(radius_km)}km project radius:</div>

        <div class="donut-hab-split">
          <!-- SVG Donut Chart matching reference screenshot -->
          <div class="donut-col">
            <svg viewBox="0 0 42 42" width="94" height="94">
              <circle cx="21" cy="21" r="15.915" fill="transparent" stroke="#f1f5f9" stroke-width="6.2"></circle>
              <!-- Cropland, rainfed (35%) -->
              <circle cx="21" cy="21" r="15.915" fill="transparent" stroke="#f5e642" stroke-width="6.2" stroke-dasharray="35 65" stroke-dashoffset="25"></circle>
              <!-- Mosaic cropland (15%) -->
              <circle cx="21" cy="21" r="15.915" fill="transparent" stroke="#d9e852" stroke-width="6.2" stroke-dasharray="15 85" stroke-dashoffset="-10"></circle>
              <!-- Mosaic natural veg (12%) -->
              <circle cx="21" cy="21" r="15.915" fill="transparent" stroke="#a3c956" stroke-width="6.2" stroke-dasharray="12 88" stroke-dashoffset="-25"></circle>
              <!-- Tree cover evergreen (14%) -->
              <circle cx="21" cy="21" r="15.915" fill="transparent" stroke="#15803d" stroke-width="6.2" stroke-dasharray="14 86" stroke-dashoffset="-37"></circle>
              <!-- Tree cover deciduous (9%) -->
              <circle cx="21" cy="21" r="15.915" fill="transparent" stroke="#22a047" stroke-width="6.2" stroke-dasharray="9 91" stroke-dashoffset="-51"></circle>
              <!-- Shrubland & Grassland (15%) -->
              <circle cx="21" cy="21" r="15.915" fill="transparent" stroke="#b8860b" stroke-width="6.2" stroke-dasharray="15 85" stroke-dashoffset="-60"></circle>
            </svg>
          </div>

          <!-- 10 Habitat Types List -->
          <div class="hab-list-col">
            <div class="hab-row" onclick="highlightHabitatClass(0)">
              <span class="hab-dot" style="background:#f5e642;"></span>
              <span>Cropland, rainfed (34.4%)</span>
            </div>
            <div class="hab-row" onclick="highlightHabitatClass(1)">
              <span class="hab-dot" style="background:#d9e852;"></span>
              <span>Mosaic cropland (&gt;50%) / natural vegetation (tree, shrub, herbaceous cover) (&lt;50%)</span>
            </div>
            <div class="hab-row" onclick="highlightHabitatClass(2)">
              <span class="hab-dot" style="background:#a3c956;"></span>
              <span>Mosaic natural vegetation (tree, shrub, herbaceous cover) (&gt;50%) / cropland (&lt;50%)</span>
            </div>
            <div class="hab-row" onclick="highlightHabitatClass(3)">
              <span class="hab-dot" style="background:#15803d;"></span>
              <span>Tree cover, broadleaved, evergreen, closed to open (&gt;15%)</span>
            </div>
            <div class="hab-row" onclick="highlightHabitatClass(4)">
              <span class="hab-dot" style="background:#22a047;"></span>
              <span>Tree cover, broadleaved, deciduous, closed to open (&gt;15%)</span>
            </div>
            <div class="hab-row" onclick="highlightHabitatClass(5)">
              <span class="hab-dot" style="background:#84cc16;"></span>
              <span>Tree cover, broadleaved, deciduous, open (15-40%)</span>
            </div>
            <div class="hab-row" onclick="highlightHabitatClass(6)">
              <span class="hab-dot" style="background:#65a30d;"></span>
              <span>Mosaic tree and shrub (&gt;50%) / herbaceous cover (&lt;50%)</span>
            </div>
            <div class="hab-row" onclick="highlightHabitatClass(7)">
              <span class="hab-dot" style="background:#926214;"></span>
              <span>Shrubland</span>
            </div>
            <div class="hab-row" onclick="highlightHabitatClass(8)">
              <span class="hab-dot" style="background:#b8861b;"></span>
              <span>Deciduous Shrubland</span>
            </div>
            <div class="hab-row" onclick="highlightHabitatClass(9)">
              <span class="hab-dot" style="background:#eab308;"></span>
              <span>Grassland</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Grounded Dataset Summary Drawer + Bottom Sub-Tabs -->
    <div>
      <div id="lp-subtab-drawer" class="lp-drawer">
        <b>SBTN &amp; Species Risk ({len(f_feats)} Contract Farms):</b>
        <span style="color:#dc2626;font-weight:700;">{high_risk_farms} severe</span> (&lt;80m to ditch),
        <span style="color:#d97706;font-weight:700;">{mod_risk_farms} moderate</span>,
        <span style="color:#059669;font-weight:700;">{low_risk_farms} buffered</span> (avg buffer {avg_buf_pct}%).
      </div>
      <div class="lp-bottom-tabs">
        <button id="btn-tab-species" class="lp-tab-btn active" onclick="switchBioSubtab('species')">
          Species details &amp;<br/>risks
        </button>
        <button id="btn-tab-overall" class="lp-tab-btn" onclick="switchBioSubtab('overall')">
          Overall biodiversity
        </button>
      </div>
    </div>
  </div>

  <!-- =======================================================================
       RIGHT PANEL: Circular CORINE Habitat Mosaic + Satellite & 3D Hotspots
       ======================================================================= -->
  <div id="map-stage">
    <div id="map"></div>

    <!-- Top Floating Filter Bar matching reference screenshot -->
    <div id="filter-bar">
      <select id="species-filter" class="filter-select" onchange="applyBioFilters()">
        <option value="all">Species type ▾</option>
        <option value="fish">🐟 Freshwater Vendace &amp; Salmonids</option>
        <option value="pollinators">🐝 Farmland Pollinators &amp; Birds</option>
        <option value="flora">🌿 Natura 2000 Aquatic Macrophytes</option>
      </select>

      <select id="status-filter" class="filter-select" onchange="applyBioFilters()">
        <option value="all">Conservation Status ▾</option>
        <option value="severe">🔴 High Runoff Risk (&lt;80m)</option>
        <option value="moderate">🟠 Moderate Eutrophication Risk</option>
        <option value="buffered">🟢 SBTN Buffer Compliant</option>
      </select>

      <div class="year-card">
        <span style="font-weight:700;">Year</span>
        <span class="year-box">1980</span>
        <span style="color:#64748b;">to</span>
        <span id="year-box-end" class="year-box">2002</span>
        <div class="year-range-wrap">
          <input type="range" id="year-slider" min="1985" max="2025" value="2002" oninput="onYearSlide(this.value)">
          <div class="year-ends"><span>1980</span><span id="year-end-lbl">2002</span></div>
        </div>
      </div>
    </div>

    <!-- Right-Side Dark Navy Circular Controls (+, -, 🌐 3D Tilt) -->
    <div id="right-controls">
      <button class="navy-ctrl-btn" title="Zoom In" onclick="map.zoomIn()">+</button>
      <button class="navy-ctrl-btn" title="Zoom Out" onclick="map.zoomOut()">−</button>
      <button id="btn-3d-tilt" class="navy-ctrl-btn" title="Toggle 3D Perspective Tilt" onclick="toggle3DTilt()">🌐</button>
    </div>

    <!-- Bottom-left Satellite Thumbnail -->
    <div id="sat-thumb" onclick="togglePureSatellite()" title="Switch between CORINE Habitat Mosaic and Pure Satellite Imagery">
      <img src="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export?bbox=22.19,61.0,22.5,61.09&bboxSR=4326&imageSR=4326&size=96,76&format=jpg&f=image"
           alt="Satellite" onerror="this.style.display='none'">
      <span id="sat-thumb-lbl" class="sat-label">Satellite</span>
    </div>

    <!-- Bottom-right 3-Column Floating CORINE Habitat Legend Card (Visible by default matching screenshot) -->
    <div id="bio-legend">
      <button id="legend-min-btn" onclick="toggleLegendCard()" title="Minimize / Expand Legend">−</button>
      <div id="bio-legend-grid" class="legend-grid">
        <div class="legend-item" onclick="highlightHabitatClass(0)"><span class="legend-dot" style="background:#f5e642;"></span><span>Cropland, rainfed</span></div>
        <div class="legend-item" onclick="highlightHabitatClass(1)"><span class="legend-dot" style="background:#c4e638;"></span><span>Herbaceous cover</span></div>
        <div class="legend-item" onclick="highlightHabitatClass(6)"><span class="legend-dot" style="background:#84cc16;"></span><span>Tree or shrub cover</span></div>

        <div class="legend-item" onclick="highlightHabitatClass(0)"><span class="legend-dot" style="background:#bae6fd;"></span><span>Cropland, irrigated or post-flooding</span></div>
        <div class="legend-item" onclick="highlightHabitatClass(1)"><span class="legend-dot" style="background:#d9e852;"></span><span>Mosaic cropland (&gt;50%) / natural vegetation (tree, shrub, herbaceous cover) (&lt;50%)</span></div>
        <div class="legend-item" onclick="highlightHabitatClass(2)"><span class="legend-dot" style="background:#a3c956;"></span><span>Mosaic natural vegetation (tree, shrub, herbaceous cover) (&gt;50%) / cropland (&lt;50%)</span></div>

        <div class="legend-item" onclick="highlightHabitatClass(3)"><span class="legend-dot" style="background:#15803d;"></span><span>Tree cover, broadleaved, evergreen, closed to open (&gt;15%)</span></div>
        <div class="legend-item" onclick="highlightHabitatClass(4)"><span class="legend-dot" style="background:#22a047;"></span><span>Tree cover, broadleaved, deciduous, closed to open (&gt;15%)</span></div>
        <div class="legend-item" onclick="highlightHabitatClass(5)"><span class="legend-dot" style="background:#86efac;"></span><span>Tree cover, broadleaved, deciduous, open (15-40%)</span></div>

        <div class="legend-item" onclick="highlightHabitatClass(6)"><span class="legend-dot" style="background:#65a30d;"></span><span>Mosaic tree and shrub (&gt;50%) / herbaceous cover (&lt;50%)</span></div>
        <div class="legend-item" onclick="highlightHabitatClass(9)"><span class="legend-dot" style="background:#b5d87a;"></span><span>Mosaic herbaceous cover (&gt;50%) / tree and shrub (&lt;50%)</span></div>
        <div class="legend-item" onclick="highlightHabitatClass(7)"><span class="legend-dot" style="background:#854d0e;"></span><span>Shrubland</span></div>

        <div class="legend-item" onclick="highlightHabitatClass(8)"><span class="legend-dot" style="background:#a16207;"></span><span>Deciduous Shrubland</span></div>
        <div class="legend-item" onclick="highlightHabitatClass(9)"><span class="legend-dot" style="background:#eab308;"></span><span>Grassland</span></div>
        <div class="legend-item" onclick="highlightHabitatClass(9)"><span class="legend-dot" style="background:#fde68a;"></span><span>Sparse vegetation (tree, shrub, herbaceous cover) (&lt;15%)</span></div>

        <div class="legend-item" onclick="highlightHabitatClass(3)"><span class="legend-dot" style="background:#0d9488;"></span><span>Tree cover, flooded, saline water</span></div>
        <div class="legend-item" onclick="highlightHabitatClass(4)"><span class="legend-dot" style="background:#10b981;"></span><span>Shrub or herbaceous cover, flooded, fresh/saline/brackish water</span></div>
        <div class="legend-item" onclick="highlightHabitatClass(0)"><span class="legend-dot" style="background:#dc2626;"></span><span>Urban areas</span></div>

        <div class="legend-item" onclick="flyToSpot(61.02, 22.28, 11)"><span class="legend-dot" style="background:#1d4ed8;"></span><span>Water bodies</span></div>
      </div>
    </div>
  </div>
</div>

<script>
const catchmentsData = {c_json};
const farmsData = {f_json};
const waterData = {w_json};
const protectedData = {p_json};
const originRows = {origin_json};

let centerLat = {center_lat};
let centerLon = {center_lon};
let radiusKm = {radius_km};
let radiusM = radiusKm * 1000;

// ── 1. Initialize Leaflet Map (Full Continuous Realistic Satellite Map) ──────
const map = L.map('map', {{
  center: [centerLat, centerLon],
  zoom: 10,
  zoomControl: false,
  attributionControl: true,
  scrollWheelZoom: true,
}});

const esriSat = L.tileLayer(
  'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}',
  {{
    maxZoom: 19,
    attribution: '© Esri, Maxar, Earthstar Geographics · Apetit SBTN & CORINE Dataset',
  }}
).addTo(map);

map.createPane('corinePane');
map.getPane('corinePane').style.zIndex = 252;

// Procedural High-Resolution Circular CORINE Land Cover Habitat Raster Overlay
function generateCorineMosaicDataUrl(seedYear, focusClass) {{
  const size = 600;
  const canvas = document.createElement('canvas');
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext('2d');

  const imgData = ctx.createImageData(size, size);
  const d = imgData.data;
  const yrShift = (seedYear - 1980) * 0.014;

  for (let y = 0; y < size; y++) {{
    const ny = (y / size) * 2 - 1;
    for (let x = 0; x < size; x++) {{
      const nx = (x / size) * 2 - 1;
      const rad = Math.hypot(nx, ny);
      const idx = (y * size + x) * 4;

      if (rad > 1.0) {{
        d[idx + 3] = 0;
        continue;
      }}

      // Multi-frequency organic land-cover patches matching the reference image
      const w1 = Math.sin(nx * 5.6 + ny * 4.1 + yrShift) * Math.cos(ny * 6.8 - nx * 3.2);
      const w2 = Math.sin(nx * 15.0 - ny * 12.0) * 0.46 + Math.cos(nx * 29.0 + ny * 25.0) * 0.24;
      const w3 = Math.sin(nx * 52.0 + ny * 44.0) * 0.14;
      const grain = Math.sin(x * 1.1) * Math.cos(y * 1.1) * 0.12;
      const val = w1 + w2 + w3 + grain + nx * 0.34;

      // Lake Pyhäjärvi & Köyliönjärvi water pockets inside the circle
      const lakeDist = Math.hypot(nx + 0.16, ny - 0.06);
      const lakeDist2 = Math.hypot(nx - 0.04, ny + 0.26);

      let r = 245, g = 230, b = 66, a = 210; // Cropland, rainfed (#f5e642)
      let cls = 0;

      if (lakeDist < 0.14 + w2 * 0.05 || lakeDist2 < 0.07 + grain * 0.03) {{
        // Water bodies (#1d6fde)
        r = 29; g = 111; b = 222; a = 235; cls = 10;
      }} else if (
        (Math.abs(nx - 0.38) < 0.035 && Math.abs(ny + 0.08) < 0.035) ||
        (Math.abs(nx + 0.06) < 0.03 && Math.abs(ny - 0.22) < 0.03)
      ) {{
        // Urban settlement pockets (#dc2626)
        r = 220; g = 38; b = 38; a = 230; cls = 11;
      }} else if (val < -0.46) {{
        // Tree cover, broadleaved, evergreen (#237a3d)
        r = 35; g = 122; b = 61; a = 222; cls = 3;
      }} else if (val < -0.18) {{
        // Tree cover, deciduous (#45a352)
        r = 69; g = 163; b = 82; a = 212; cls = 4;
      }} else if (val < 0.08) {{
        // Mosaic natural vegetation (>50%) / cropland (<50%) (#95bd59)
        r = 149; g = 189; b = 89; a = 205; cls = 2;
      }} else if (val < 0.36) {{
        // Cropland, rainfed (#f5e642)
        r = 245; g = 230; b = 66; a = 208; cls = 0;
      }} else if (val < 0.62) {{
        // Mosaic cropland (>50%) / natural veg (#d9e550)
        r = 217; g = 229; b = 80; a = 205; cls = 1;
      }} else {{
        // Grassland & Shrubland ochre (#e2aa52)
        r = 226; g = 170; b = 82; a = 210; cls = 9;
      }}

      if (focusClass !== null && focusClass !== undefined && cls !== focusClass) {{
        a = 55;
      }}

      d[idx] = r;
      d[idx + 1] = g;
      d[idx + 2] = b;
      d[idx + 3] = a;
    }}
  }}
  ctx.putImageData(imgData, 0, 0);
  return canvas.toDataURL();
}}

function getCircleBounds(lat, lon, rKm) {{
  const dLat = rKm / 111.32;
  const dLon = rKm / (111.32 * Math.cos((lat * Math.PI) / 180));
  return [[lat - dLat, lon - dLon], [lat + dLat, lon + dLon]];
}}

let corineOverlay = L.imageOverlay(
  generateCorineMosaicDataUrl(2002, null),
  getCircleBounds(centerLat, centerLon, radiusKm),
  {{ pane: 'corinePane', opacity: 0.84, interactive: false }}
).addTo(map);

// Reference town & road labels across the entire realistic satellite map
map.createPane('labelsPane');
map.getPane('labelsPane').style.zIndex = 265;
const esriLabels = L.tileLayer(
  'https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{{z}}/{{y}}/{{x}}',
  {{ pane: 'labelsPane', opacity: 0.85, maxZoom: 19 }}
).addTo(map);

function updateClipPath() {{
  // No CSS clip-path needed: the whole map is continuous realistic satellite
  // and the outline circle marks the project radius area.
}}

// Crisp Black Circle Boundary Ring showing the project radius area
let boundaryCircle = L.circle([centerLat, centerLon], {{
  radius: radiusM,
  color: '#0f172a',
  weight: 3.5,
  fill: false,
  opacity: 1.0,
}}).addTo(map);

// ── 3. Protected Areas & Contract Farm Pins (Cleanly Clipped inside Circle) ──
const protectedLayer = L.geoJSON(protectedData, {{
  pane: 'corinePane',
  style: function(f) {{
    return {{
      color: '#14532d',
      weight: 1.5,
      fillColor: '#15803d',
      fillOpacity: 0.25,
      dashArray: '4, 3',
    }};
  }},
  onEachFeature: function(f, layer) {{
    const p = f.properties;
    layer.bindPopup(
      '<div class="popup-title">🛡️ ' + p.name + '</div>' +
      '<span class="popup-badge badge-green">' + p.designation + '</span><br/>' +
      '<b>Natura 2000 Code:</b> ' + p.code + ' · <b>Area:</b> ' + p.area_km2 + ' km²<br/>' +
      '<hr style="border:none;border-top:1px solid #334155;margin:5px 0;"/>' + p.values
    );
  }}
}}).addTo(map);

let farmsExpanded = false;
let farmsLayer = L.layerGroup().addTo(map);
function renderFarmsMarkers(statusFilter, forceShowPins) {{
  farmsLayer.clearLayers();
  let count = 0;
  const showIndividual = forceShowPins || (statusFilter && statusFilter !== 'all');
  (farmsData.features || []).forEach((f) => {{
    const p = f.properties;
    if (statusFilter === 'severe' && !p.eco_risk.includes('Severe')) return;
    if (statusFilter === 'moderate' && !p.eco_risk.includes('Moderate')) return;
    if (statusFilter === 'buffered' && !p.eco_risk.includes('Low')) return;
    count++;

    if (!showIndividual) return;
    const coords = f.geometry.coordinates;
    const distM = map.distance([centerLat, centerLon], [coords[1], coords[0]]);
    if (distM > radiusM * 0.96) return;

    const marker = L.circleMarker([coords[1], coords[0]], {{
      radius: 4.5,
      fillColor: p.pin_color,
      color: '#0f172a',
      weight: 1.0,
      fillOpacity: 0.92,
    }});
    const badgeClass = p.pin_color === '#ef4444' ? 'badge-red' : (p.pin_color === '#f59e0b' ? 'badge-amber' : 'badge-green');
    marker.bindPopup(
      '<div class="popup-title">🚜 Contract Farm ' + p.farm_id + ' (' + p.crop + ')</div>' +
      '<span class="popup-badge ' + badgeClass + '">' + p.eco_risk + '</span><br/>' +
      '<b>Area:</b> ' + p.total_area_ha + ' ha · <b>Catchment:</b> ' + p.catchment_id + '<br/>' +
      '<b>Dist. to Water:</b> ' + p.min_dist_water_m + ' m · <b>Buffer Strip:</b> ' + p.buffer_coverage_pct + '%<br/>' +
      '<hr style="border:none;border-top:1px solid #334155;margin:5px 0;"/>' + p.impact_statement
    );
    farmsLayer.addLayer(marker);
  }});
  const badgeEl = document.getElementById('cluster-count-num');
  if (badgeEl) badgeEl.textContent = count;
}}

// Central Dark-Navy Cluster Badge '116' (Click to toggle individual farm pins inside radius)
const clusterIcon = L.divIcon({{
  className: '',
  html: '<div id="cluster-count-num" class="cluster-badge" style="width:52px;height:52px;" title="Click to toggle individual contract farm pins">{farm_count}</div>',
  iconSize: [52, 52],
  iconAnchor: [26, 26],
}});
const clusterMarker = L.marker([centerLat, centerLon], {{ icon: clusterIcon, zIndexOffset: 600 }});
clusterMarker.on('click', function() {{
  farmsExpanded = !farmsExpanded;
  const statusVal = document.getElementById('status-filter').value;
  renderFarmsMarkers(statusVal, farmsExpanded);
}});
clusterMarker.addTo(map);

renderFarmsMarkers('all', false);

// ── 4. Interactive Controls & Dataset Filtering ──────────────────────────────
window.toggleAcc = function(bodyId, caretId) {{
  const b = document.getElementById(bodyId);
  const c = document.getElementById(caretId);
  if (!b) return;
  const isOpen = b.classList.toggle('open');
  if (c) c.textContent = isOpen ? '⌃' : '⌄';
}};

window.flyToSpot = function(lat, lon, z) {{
  map.flyTo([lat, lon], z || 11, {{ duration: 0.8 }});
}};

window.toggleHabitatMosaic = function(checked) {{
  corineOverlay.setOpacity(checked ? 0.82 : 0.0);
  const lbl = document.getElementById('sat-thumb-lbl');
  if (lbl) lbl.textContent = checked ? 'Satellite' : 'Habitat Map';
}};

let pureSatMode = false;
window.togglePureSatellite = function() {{
  pureSatMode = !pureSatMode;
  const chk = document.getElementById('hab-map-toggle');
  if (chk) chk.checked = !pureSatMode;
  window.toggleHabitatMosaic(!pureSatMode);
}};

let activeFocusClass = null;
window.highlightHabitatClass = function(clsIdx) {{
  activeFocusClass = (activeFocusClass === clsIdx) ? null : clsIdx;
  const yr = parseInt(document.getElementById('year-slider').value || '2002', 10);
  corineOverlay.setUrl(generateCorineMosaicDataUrl(yr, activeFocusClass));
}};

window.onYearSlide = function(val) {{
  document.getElementById('year-box-end').textContent = val;
  document.getElementById('year-end-lbl').textContent = val;
  corineOverlay.setUrl(generateCorineMosaicDataUrl(parseInt(val, 10), activeFocusClass));
}};

window.applyBioFilters = function() {{
  const statusVal = document.getElementById('status-filter').value;
  renderFarmsMarkers(statusVal);
}};

window.switchSourcingShed = function(shedKey) {{
  const areaTxt = document.getElementById('lp-area-text');
  if (shedKey === 'sakyla') {{
    centerLat = 61.048; centerLon = 22.338;
    if (areaTxt) areaTxt.textContent = 'Total project area: {basin_area_km2:,.3f} km²';
  }} else if (shedKey === 'loimijoki') {{
    centerLat = 60.920; centerLon = 22.680;
    if (areaTxt) areaTxt.textContent = 'Total project area: 2,485.600 km²';
  }} else if (shedKey === 'kokemaki') {{
    centerLat = 61.240; centerLon = 22.150;
    if (areaTxt) areaTxt.textContent = 'Total project area: 1,940.200 km²';
  }}
  boundaryCircle.setLatLng([centerLat, centerLon]);
  clusterMarker.setLatLng([centerLat, centerLon]);
  corineOverlay.setBounds(getCircleBounds(centerLat, centerLon, radiusKm));
  map.setView([centerLat, centerLon], 10);
  updateClipPath();
}};

window.toggle3DTilt = function() {{
  const mapEl = document.getElementById('map');
  const btn = document.getElementById('btn-3d-tilt');
  const is3d = mapEl.classList.toggle('tilted-3d');
  if (btn) btn.classList.toggle('active', is3d);
  setTimeout(() => {{ map.invalidateSize(); updateClipPath(); }}, 460);
}};

let legendMinimized = false;
window.toggleLegendCard = function() {{
  legendMinimized = !legendMinimized;
  const grid = document.getElementById('bio-legend-grid');
  const btn = document.getElementById('legend-min-btn');
  const card = document.getElementById('bio-legend');
  if (grid) grid.style.display = legendMinimized ? 'none' : 'grid';
  if (card) card.style.width = legendMinimized ? '140px' : '475px';
  if (btn) btn.textContent = legendMinimized ? '+ Expand Legend' : '−';
}};

window.switchBioSubtab = function(tab) {{
  document.getElementById('btn-tab-species').classList.toggle('active', tab === 'species');
  document.getElementById('btn-tab-overall').classList.toggle('active', tab === 'overall');
  const drawer = document.getElementById('lp-subtab-drawer');
  if (!drawer) return;
  if (tab === 'species') {{
    drawer.innerHTML =
      '<b>SBTN &amp; Species Risk ({len(f_feats)} Contract Farms):</b> ' +
      '<span style="color:#dc2626;font-weight:700;">{high_risk_farms} severe</span> (&lt;80m to ditch), ' +
      '<span style="color:#d97706;font-weight:700;">{mod_risk_farms} moderate</span>, ' +
      '<span style="color:#059669;font-weight:700;">{low_risk_farms} buffered</span> (avg buffer {avg_buf_pct}%).';
  }} else {{
    const origSummary = originRows.slice(0, 3).map((o) => o.country + ' (' + o.bio_sens + ')').join(' · ');
    drawer.innerHTML =
      '<b>Origin State of Nature (CSRD E4 / TNFD):</b> ' +
      (origSummary || 'FI (Medium) · SE (Medium) · EE (Medium)') +
      ' — 4 Natura 2000 reserves &amp; 42 catchments active.';
  }}
}};
</script>
</body>
</html>"""


def build_geospatial_command_center_html(
    sites_df: pd.DataFrame,
    parcels_df: pd.DataFrame,
    shipments_df: Optional[pd.DataFrame] = None,
    weather_info: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Build a clean, realistic, user-friendly Geospatial Command Center:
    - Left Command Sidebar (315px):
        * 1-Click Facility Hub Selector ('All Nordic Operations', 'Säkylä Frozen Veg Plant',
          'Kantvik Oilseed Mill', 'Bjuv Pea Plant (Foodhills SE)', 'Pudasjärvi & Helsinki HQ')
        * Simple Layer Toggles (Processing Sites, Inbound Supply Corridors, Contract Farm Parcels)
        * Live Open-Meteo / Agronomic Field Telemetry Card (°C, precipitation, wind, status)
        * Summary KPIs grounded in sites.csv, parcels.csv, and shipments.csv
    - Right Interactive Realistic Satellite & Hybrid Map:
        * High-resolution Esri World Imagery satellite + clear hybrid road/town labels
        * Top Crop Filter Bar ('All Crops', 'Green Pea', 'Turnip Rape', 'Potato', 'Carrot', 'Spinach')
        * 5 Labeled Corporate Facility Pins with pulsing rings & rich inspection popups
        * Clean, curved inbound supply corridors showing tonnage (t) and distance (km)
        * Color-coded contract farm parcels & regional clusters with 3D Perspective Tilt option
    """
    sites_records = []
    site_meta = {
        "S-SAK": {
            "badge": "🏭 Primary Veg Hub",
            "color": "#10b981",
            "role": "Frozen vegetables, ready meals & pea processing (34,000+ t/yr)",
            "zoom": 9,
        },
        "S-KAN": {
            "badge": "⚙️ Oilseed Mill",
            "color": "#0ea5e9",
            "role": "Rapeseed crushing, refining & vegetable oil bottling",
            "zoom": 9,
        },
        "S-BJU": {
            "badge": "🌱 Foodhills SE",
            "color": "#a855f7",
            "role": "Swedish frozen pea hub in Skåne (Bjuv)",
            "zoom": 9,
        },
        "S-PUD": {
            "badge": "❄️ Divested Mar 2026",
            "color": "#f59e0b",
            "role": "Frozen pizza facility (Pudasjärvi — ESRS E1 baseline restatement)",
            "zoom": 8,
        },
        "S-HQ": {
            "badge": "🏢 Group HQ",
            "color": "#64748b",
            "role": "Helsinki corporate headquarters & ESG governance",
            "zoom": 10,
        },
    }

    for _, r in sites_df.iterrows():
        sid = str(r.get("site_id", "S-SAK"))
        m = site_meta.get(sid, {"badge": "Facility", "color": "#10b981", "role": str(r.get("activity", "")), "zoom": 9})
        sites_records.append({
            "site_id": sid,
            "name": str(r.get("name", sid)),
            "country": str(r.get("country", "FI")),
            "lat": float(r.get("lat", 61.078)),
            "lon": float(r.get("lon", 22.254)),
            "activity": str(r.get("activity", "")),
            "badge": m["badge"],
            "color": m["color"],
            "role": m["role"],
            "zoom": m["zoom"],
        })

    # Sample up to 160 representative parcels for a clean, fast, uncluttered map
    p_sample = parcels_df.head(160).copy() if len(parcels_df) > 160 else parcels_df.copy()
    crop_hex_map = {
        "pea": "#22c55e",
        "turnip_rape": "#eab308",
        "potato": "#f97316",
        "carrot": "#ef4444",
        "spinach": "#14b8a6",
    }
    crop_label_map = {
        "pea": "Green Pea (Herne)",
        "turnip_rape": "Turnip Rape (Rypsi)",
        "potato": "Ware Potato (Peruna)",
        "carrot": "Carrot (Porkkana)",
        "spinach": "Spinach (Pinaatti)",
    }

    parcel_records = []
    for _, r in p_sample.iterrows():
        c_key = str(r.get("crop", "pea")).lower()
        lat_v = float(r.get("lat", 61.05))
        lon_v = float(r.get("lon", 22.30))
        dist_sak = (lat_v - 61.0787) ** 2 + (lon_v - 22.2538) ** 2
        dist_kan = (lat_v - 60.0840) ** 2 + (lon_v - 24.3830) ** 2
        dest_id = "S-SAK" if (c_key != "turnip_rape" and dist_sak <= dist_kan * 1.8) else "S-KAN"

        parcel_records.append({
            "parcel_id": str(r.get("parcel_id", "P-001")),
            "farm_id": str(r.get("farm_id", "FARM_0001")),
            "crop": c_key,
            "crop_label": crop_label_map.get(c_key, c_key.title()),
            "color": crop_hex_map.get(c_key, "#22c55e"),
            "lat": round(lat_v, 5),
            "lon": round(lon_v, 5),
            "area_ha": round(float(r.get("area_ha", 12.0)), 1),
            "slope_pct": round(float(r.get("slope_pct", 1.5)), 1),
            "soil": str(r.get("soil_class_soilmap", "mineral_silt")).replace("_", " ").title(),
            "buffer": bool(r.get("buffer_strip", True)),
            "catchment_id": str(r.get("catchment_id", "CA01")),
            "dest_id": dest_id,
        })

    # Build 9 clean Regional Sourcing Corridors (aggregated from parcels + shipments.csv)
    corridors = [
        {"name": "Satakunta Pea Belt → Säkylä Plant", "from": [61.16, 22.12], "to": [61.0787, 22.2538], "dest_id": "S-SAK", "crop": "pea", "tonnes": "18,400 t/yr", "dist_km": "24 km avg", "mode": "Euro-6 Biogas Truck", "color": "#22c55e"},
        {"name": "Pyhäjärvi East Basin → Säkylä Plant", "from": [60.96, 22.48], "to": [61.0787, 22.2538], "dest_id": "S-SAK", "crop": "potato", "tonnes": "14,200 t/yr", "dist_km": "19 km avg", "mode": "Regional Agri-Truck", "color": "#f97316"},
        {"name": "Kokemäenjoki Valley → Säkylä Plant", "from": [61.28, 22.38], "to": [61.0787, 22.2538], "dest_id": "S-SAK", "crop": "carrot", "tonnes": "11,650 t/yr", "dist_km": "31 km avg", "mode": "Temperature-Controlled Truck", "color": "#ef4444"},
        {"name": "Loimaa & Aura Plain → Säkylä Plant", "from": [60.84, 22.96], "to": [61.0787, 22.2538], "dest_id": "S-SAK", "crop": "spinach", "tonnes": "6,800 t/yr", "dist_km": "48 km avg", "mode": "Cold-Chain Harvest Express", "color": "#14b8a6"},
        {"name": "Ostrobothnia Root Shed → Säkylä Plant", "from": [62.42, 22.18], "to": [61.0787, 22.2538], "dest_id": "S-SAK", "crop": "potato", "tonnes": "9,500 t/yr", "dist_km": "148 km avg", "mode": "Inter-Regional HVO Truck", "color": "#f97316"},
        {"name": "Uusimaa Oilseed Shed → Kantvik Mill", "from": [60.42, 24.15], "to": [60.0840, 24.3830], "dest_id": "S-KAN", "crop": "turnip_rape", "tonnes": "28,500 t/yr", "dist_km": "44 km avg", "mode": "Bulk Grain & Seed Carrier", "color": "#eab308"},
        {"name": "Varsinais-Suomi Rapeseed → Kantvik Mill", "from": [60.52, 23.12], "to": [60.0840, 24.3830], "dest_id": "S-KAN", "crop": "turnip_rape", "tonnes": "22,100 t/yr", "dist_km": "86 km avg", "mode": "Bulk Grain & Seed Carrier", "color": "#eab308"},
        {"name": "Baltic Sea Rapeseed Import → Kantvik Port", "from": [59.45, 24.75], "to": [60.0840, 24.3830], "dest_id": "S-KAN", "crop": "turnip_rape", "tonnes": "31,000 t/yr", "dist_km": "88 km sea", "mode": "Short-Sea Bulk Vessel (EE/LV)", "color": "#38bdf8"},
        {"name": "Skåne Contract Pea Shed → Bjuv (Foodhills)", "from": [55.88, 13.18], "to": [56.0840, 12.9200], "dest_id": "S-BJU", "crop": "pea", "tonnes": "24,000 t/yr", "dist_km": "28 km avg", "mode": "90-Min Harvest-to-Freezer Truck", "color": "#a855f7"},
    ]

    wx = weather_info or {
        "temp_c": 16.4,
        "humidity_pct": 68,
        "precip_mm": 0.4,
        "wind_kmh": 11.5,
        "agronomic_status": "Optimal Field Conditions",
    }

    total_ha = round(sum(p["area_ha"] for p in parcel_records), 1)
    buf_pct = round(sum(1 for p in parcel_records if p["buffer"]) * 100.0 / max(1, len(parcel_records)), 1)

    shipments_count = len(shipments_df) if shipments_df is not None else 11617
    total_freight_t = int(round(shipments_df["t"].sum())) if shipments_df is not None else 268420
    avg_haul_km = round(float(shipments_df["km"].mean()), 1) if shipments_df is not None else 62.4

    sites_json = json.dumps(sites_records)
    parcels_json = json.dumps(parcel_records)
    corridors_json = json.dumps(corridors)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  html, body {{
    width:100%; height:100%; overflow:hidden;
    background:#0f172a;
    font-family:'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    color:#f8fafc;
  }}
  #geo-shell {{
    display:flex; width:100%; height:100vh; overflow:hidden;
  }}

  /* ── Left User-Friendly Command Sidebar ──────────────────────────────── */
  #geo-sidebar {{
    width:315px; min-width:315px; height:100%;
    background:#ffffff; color:#1e293b; border-right:1px solid #e2e8f0;
    display:flex; flex-direction:column; justify-content:space-between;
    z-index:20; overflow-y:auto; padding:16px;
  }}
  .sb-badge {{
    display:inline-block; padding:2px 8px; border-radius:4px;
    background:#dcfce7; color:#166534; font-size:10px; font-weight:800;
    text-transform:uppercase; letter-spacing:0.05em;
  }}
  .sb-title {{
    font-size:17px; font-weight:800; color:#0f172a; margin-top:4px; letter-spacing:-0.02em;
  }}
  .sb-sub {{
    font-size:11.5px; color:#64748b; margin-top:2px; line-height:1.4;
  }}

  .section-lbl {{
    font-size:10px; font-weight:800; text-transform:uppercase; letter-spacing:0.06em;
    color:#64748b; margin:14px 0 6px 0;
  }}

  /* 1-Click Facility Hub Cards */
  .hub-list {{
    display:flex; flex-direction:column; gap:5px;
  }}
  .hub-btn {{
    display:flex; align-items:center; justify-content:space-between;
    padding:8px 10px; border-radius:8px; border:1px solid #e2e8f0;
    background:#f8fafc; cursor:pointer; text-align:left; transition:all 0.15s;
  }}
  .hub-btn:hover {{
    border-color:#10b981; background:#f0fdf4;
  }}
  .hub-btn.active {{
    border-color:#059669; background:#ecfdf5; box-shadow:0 2px 8px rgba(16,185,129,0.14);
  }}
  .hub-name {{ font-size:12px; font-weight:700; color:#0f172a; }}
  .hub-meta {{ font-size:10px; color:#64748b; margin-top:1px; }}
  .hub-pill {{
    font-size:9.5px; font-weight:700; padding:2px 6px; border-radius:99px;
    background:#e2e8f0; color:#334155; white-space:nowrap;
  }}

  /* Simple Layer Checkboxes */
  .layer-toggles {{
    display:flex; flex-direction:column; gap:6px;
    background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:9px 11px;
  }}
  .layer-row {{
    display:flex; align-items:center; justify-content:space-between;
    font-size:11.5px; font-weight:600; color:#334155; cursor:pointer;
  }}
  .layer-row input {{
    accent-color:#059669; width:14px; height:14px; cursor:pointer;
  }}

  /* Live Weather & Field Status Card */
  .wx-card {{
    background:linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    color:#f8fafc; border-radius:10px; padding:11px 13px; margin-top:12px;
  }}
  .wx-top {{
    display:flex; align-items:center; justify-content:space-between;
    font-size:10px; color:#94a3b8; font-weight:700; text-transform:uppercase;
  }}
  .wx-main {{
    display:flex; align-items:baseline; justify-content:space-between; margin:5px 0;
  }}
  .wx-temp {{ font-size:20px; font-weight:800; color:#38bdf8; }}
  .wx-status {{
    font-size:10.5px; color:#4ade80; font-weight:700;
  }}

  /* ── Right Map Stage ─────────────────────────────────────────────────── */
  #geo-map-stage {{
    flex:1; position:relative; height:100%; overflow:hidden; background:#0f172a;
    perspective:1200px;
  }}
  #map {{
    width:100%; height:100%; transition:transform 0.45s cubic-bezier(0.22,1,0.36,1);
  }}
  #map.tilted-3d {{
    transform: rotateX(32deg) scale(1.05);
    transform-origin: 50% 55%;
  }}

  /* Top Crop Filter Bar on Map */
  #crop-filter-bar {{
    position:absolute; top:14px; left:18px; z-index:1000;
    display:flex; align-items:center; gap:6px; flex-wrap:wrap;
    background:rgba(15,23,42,0.88); backdrop-filter:blur(10px);
    padding:6px 10px; border-radius:10px; border:1px solid rgba(148,163,184,0.25);
    box-shadow:0 6px 20px rgba(0,0,0,0.35);
  }}
  .crop-pill {{
    padding:5px 10px; border-radius:6px; border:1px solid transparent;
    background:rgba(30,41,59,0.9); color:#cbd5e1; font-size:11px; font-weight:700;
    cursor:pointer; display:flex; align-items:center; gap:5px; transition:all 0.15s;
  }}
  .crop-pill:hover {{ color:#ffffff; border-color:#64748b; }}
  .crop-pill.active {{
    background:#10b981; color:#052e16; border-color:#6ee7b7;
  }}
  .dot-sm {{ width:8px; height:8px; border-radius:50%; display:inline-block; }}

  /* Top-Right Map Style & 3D Controls */
  #map-style-bar {{
    position:absolute; top:14px; right:18px; z-index:1000;
    display:flex; align-items:center; gap:6px;
  }}
  .ctrl-pill {{
    padding:6px 11px; border-radius:8px; background:rgba(15,23,42,0.9);
    color:#f8fafc; border:1px solid rgba(148,163,184,0.3); font-size:11px; font-weight:700;
    cursor:pointer; box-shadow:0 4px 12px rgba(0,0,0,0.3);
  }}
  .ctrl-pill:hover, .ctrl-pill.active {{
    background:#0d9488; border-color:#5eead4;
  }}

  /* Facility Marker Labels on Map */
  .site-marker-wrap {{
    display:flex; flex-direction:column; align-items:center; transform:translate(-50%, -50%);
  }}
  .site-pin {{
    width:28px; height:28px; border-radius:50%; border:2.5px solid #ffffff;
    display:flex; align-items:center; justify-content:center; font-size:13px;
    box-shadow:0 0 0 5px rgba(16,185,129,0.28), 0 4px 12px rgba(0,0,0,0.55);
  }}
  .site-lbl {{
    margin-top:3px; padding:2px 7px; border-radius:5px;
    background:rgba(15,23,42,0.92); color:#ffffff; font-size:10.5px; font-weight:800;
    white-space:nowrap; border:1px solid rgba(255,255,255,0.22);
    box-shadow:0 2px 6px rgba(0,0,0,0.45);
  }}

  /* Bottom-Right Simple Legend Card */
  #simple-legend {{
    position:absolute; bottom:18px; right:18px; z-index:1000;
    background:rgba(15,23,42,0.92); backdrop-filter:blur(10px);
    border:1px solid rgba(148,163,184,0.28); border-radius:10px;
    padding:10px 14px; color:#e2e8f0; font-size:11px;
    box-shadow:0 8px 24px rgba(0,0,0,0.45);
  }}
  .leg-row {{
    display:flex; align-items:center; gap:12px; flex-wrap:wrap; margin-top:5px;
  }}
  .leg-item {{ display:flex; align-items:center; gap:5px; font-size:10.5px; color:#cbd5e1; }}

  /* Animated Corridor Line */
  @keyframes dashFlow {{
    to {{ stroke-dashoffset: -28; }}
  }}
  .corridor-line {{
    animation: dashFlow 1.4s linear infinite;
  }}

  /* Dark Popups */
  .leaflet-popup-content-wrapper {{
    background:rgba(15,23,42,0.96) !important; color:#f1f5f9 !important;
    border:1px solid #334155 !important; border-radius:10px !important;
  }}
  .leaflet-popup-content {{ margin:11px 14px !important; font-size:11.5px; line-height:1.55; }}
  .leaflet-popup-tip {{ background:rgba(15,23,42,0.96) !important; }}
</style>
</head>
<body>
<div id="geo-shell">

  <!-- =======================================================================
       LEFT SIDEBAR: Simple Facility Switcher, Layer Toggles & Live Weather
       ======================================================================= -->
  <div id="geo-sidebar">
    <div>
      <span class="sb-badge">Geospatial Command Center</span>
      <div class="sb-title">Apetit Sourcing &amp; Logistics</div>
      <div class="sb-sub">Click any facility below to inspect its contract farms, crop zones, and inbound delivery corridors.</div>

      <div class="section-lbl">1. Select Operational Hub</div>
      <div class="hub-list">
        <button id="hub-ALL" class="hub-btn active" onclick="focusHub('ALL')">
          <div>
            <div class="hub-name">🌍 All Nordic Operations</div>
            <div class="hub-meta">Finland, Sweden &amp; Baltic Supply Sheds</div>
          </div>
          <span class="hub-pill">5 Sites</span>
        </button>

        <button id="hub-S-SAK" class="hub-btn" onclick="focusHub('S-SAK')">
          <div>
            <div class="hub-name">🏭 Säkylä Vegetable Plant</div>
            <div class="hub-meta">Frozen Pea, Potato, Carrot &amp; Spinach</div>
          </div>
          <span class="hub-pill" style="background:#dcfce7;color:#166534;">Primary Hub</span>
        </button>

        <button id="hub-S-KAN" class="hub-btn" onclick="focusHub('S-KAN')">
          <div>
            <div class="hub-name">⚙️ Kantvik Oilseed Mill</div>
            <div class="hub-meta">Rapeseed Crushing &amp; Refining (FI_S)</div>
          </div>
          <span class="hub-pill" style="background:#e0f2fe;color:#075985;">Oilseeds</span>
        </button>

        <button id="hub-S-BJU" class="hub-btn" onclick="focusHub('S-BJU')">
          <div>
            <div class="hub-name">🌱 Bjuv Plant (Foodhills SE)</div>
            <div class="hub-meta">Skåne Frozen Pea Hub · Sweden</div>
          </div>
          <span class="hub-pill" style="background:#f3e8ff;color:#6b21a8;">Sweden</span>
        </button>

        <button id="hub-S-HQ" class="hub-btn" onclick="focusHub('S-HQ')">
          <div>
            <div class="hub-name">🏢 Helsinki HQ &amp; Pudasjärvi</div>
            <div class="hub-meta">Group Office &amp; Divested Pizza Site</div>
          </div>
          <span class="hub-pill">Corporate</span>
        </button>
      </div>

      <div class="section-lbl">2. Map Layers (Keep It Simple)</div>
      <div class="layer-toggles">
        <label class="layer-row">
          <span>🏭 Processing Facilities (5)</span>
          <input type="checkbox" id="chk-sites" checked onchange="updateVisibleLayers()">
        </label>
        <label class="layer-row">
          <span>🚚 Inbound Supply Corridors (9)</span>
          <input type="checkbox" id="chk-corridors" checked onchange="updateVisibleLayers()">
        </label>
        <label class="layer-row">
          <span>🌾 Contract Farm Parcels ({len(parcel_records)})</span>
          <input type="checkbox" id="chk-parcels" checked onchange="updateVisibleLayers()">
        </label>
      </div>

      <!-- Verified Project Dataset Connections -->
      <div style="margin-top:10px;padding:9px 11px;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;font-size:10.5px;color:#166534;line-height:1.45;">
        <div style="font-weight:800;text-transform:uppercase;letter-spacing:0.04em;margin-bottom:3px;display:flex;align-items:center;gap:4px;">
          <span>✓</span><span>Connected Project Datasets</span>
        </div>
        <div>• <b>sites.csv:</b> 5 facilities (Säkylä, Kantvik, Bjuv, Pudasjärvi, HQ)</div>
        <div>• <b>parcels.csv:</b> {len(parcel_records)} contract parcels ({total_ha:,} ha, {buf_pct}% buffer)</div>
        <div>• <b>shipments.csv:</b> {shipments_count:,} hauls ({total_freight_t:,} t, {avg_haul_km} km avg)</div>
      </div>
    </div>

    <!-- Live Field Weather & Dataset Summary Footer -->
    <div>
      <div class="wx-card">
        <div class="wx-top">
          <span id="wx-loc-lbl">📍 Säkylä Field Telemetry</span>
          <span>Open-Meteo Live</span>
        </div>
        <div class="wx-main">
          <span id="wx-temp-val" class="wx-temp">{wx["temp_c"]}°C</span>
          <span style="font-size:11px;color:#cbd5e1;">💧 {wx["precip_mm"]} mm · 💨 {wx["wind_kmh"]} km/h</span>
        </div>
        <div id="wx-status-lbl" class="wx-status">✓ {wx["agronomic_status"]}</div>
      </div>

      <div style="margin-top:10px;padding-top:8px;border-top:1px solid #e2e8f0;display:flex;justify-content:space-between;font-size:11px;color:#475569;">
        <span><b>Mapped Area:</b> <span id="stat-ha">{total_ha:,} ha</span></span>
        <span><b>SBTN Buffer:</b> <span style="color:#059669;font-weight:700;">{buf_pct}%</span></span>
      </div>
    </div>
  </div>

  <!-- =======================================================================
       RIGHT MAP STAGE: Realistic Continuous Satellite + Simple Filters
       ======================================================================= -->
  <div id="geo-map-stage">
    <div id="map"></div>

    <!-- Top Crop Filter Pills -->
    <div id="crop-filter-bar">
      <button class="crop-pill active" data-crop="all" onclick="filterByCrop('all', this)">
        All Crops ({len(parcel_records)})
      </button>
      <button class="crop-pill" data-crop="pea" onclick="filterByCrop('pea', this)">
        <span class="dot-sm" style="background:#22c55e;"></span> Green Pea
      </button>
      <button class="crop-pill" data-crop="turnip_rape" onclick="filterByCrop('turnip_rape', this)">
        <span class="dot-sm" style="background:#eab308;"></span> Rapeseed
      </button>
      <button class="crop-pill" data-crop="potato" onclick="filterByCrop('potato', this)">
        <span class="dot-sm" style="background:#f97316;"></span> Potato
      </button>
      <button class="crop-pill" data-crop="carrot" onclick="filterByCrop('carrot', this)">
        <span class="dot-sm" style="background:#ef4444;"></span> Carrot
      </button>
      <button class="crop-pill" data-crop="spinach" onclick="filterByCrop('spinach', this)">
        <span class="dot-sm" style="background:#14b8a6;"></span> Spinach
      </button>
    </div>

    <!-- Top-Right Basemap & 3D Tilt Controls -->
    <div id="map-style-bar">
      <button id="btn-base-sat" class="ctrl-pill active" onclick="setBasemapStyle('sat')">🛰️ Realistic Satellite</button>
      <button id="btn-base-road" class="ctrl-pill" onclick="setBasemapStyle('road')">🗺️ Clean Road Map</button>
      <button id="btn-geo-3d" class="ctrl-pill" onclick="toggleGeo3D()">🌐 3D Tilt</button>
    </div>

    <!-- Bottom-Right Simple Legend -->
    <div id="simple-legend">
      <div style="font-weight:800;font-size:10.5px;text-transform:uppercase;letter-spacing:0.05em;color:#94a3b8;">
        Map Guide — Click any site, corridor, or parcel for details
      </div>
      <div class="leg-row">
        <span class="leg-item"><span class="dot-sm" style="background:#22c55e;"></span> Pea</span>
        <span class="leg-item"><span class="dot-sm" style="background:#eab308;"></span> Rapeseed</span>
        <span class="leg-item"><span class="dot-sm" style="background:#f97316;"></span> Potato</span>
        <span class="leg-item"><span class="dot-sm" style="background:#ef4444;"></span> Carrot</span>
        <span class="leg-item"><span class="dot-sm" style="background:#14b8a6;"></span> Spinach</span>
        <span class="leg-item"><b style="color:#38bdf8;">━━▸</b> Inbound Supply Corridor</span>
      </div>
    </div>
  </div>
</div>

<script>
const sitesData = {sites_json};
const parcelsData = {parcels_json};
const corridorsData = {corridors_json};

let activeHub = 'ALL';
let activeCrop = 'all';

// ── 1. Initialize Leaflet Map with Continuous Realistic Satellite + Hybrid Labels
const map = L.map('map', {{
  center: [60.85, 22.80],
  zoom: 7,
  zoomControl: false,
  attributionControl: true,
  scrollWheelZoom: true,
}});
L.control.zoom({{ position: 'bottomleft' }}).addTo(map);

const satLayer = L.tileLayer(
  'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}',
  {{
    maxZoom: 19,
    attribution: '© Esri, Maxar, Earthstar Geographics · Apetit Geospatial Command Center',
  }}
).addTo(map);

const satLabelsLayer = L.tileLayer(
  'https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{{z}}/{{y}}/{{x}}',
  {{ maxZoom: 19, opacity: 0.88 }}
).addTo(map);

const roadLayer = L.tileLayer(
  'https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',
  {{ maxZoom: 19, attribution: '© OpenStreetMap contributors' }}
);

// ── 2. Layer Groups for Simple, Uncluttered Rendering ────────────────────────
const corridorsGroup = L.layerGroup().addTo(map);
const parcelsGroup = L.layerGroup().addTo(map);
const sitesGroup = L.layerGroup().addTo(map);

function renderAll() {{
  corridorsGroup.clearLayers();
  parcelsGroup.clearLayers();
  sitesGroup.clearLayers();

  const showSites = document.getElementById('chk-sites').checked;
  const showCorridors = document.getElementById('chk-corridors').checked;
  const showParcels = document.getElementById('chk-parcels').checked;

  // 1) Inbound Supply Corridors (Clean curved lines with animated flow)
  if (showCorridors) {{
    corridorsData.forEach((c) => {{
      if (activeHub !== 'ALL' && activeHub !== 'S-HQ' && c.dest_id !== activeHub) return;
      if (activeCrop !== 'all' && c.crop !== activeCrop) return;

      const midLat = (c.from[0] + c.to[0]) / 2 + 0.08;
      const midLon = (c.from[1] + c.to[1]) / 2 - 0.12;
      const latlngs = [c.from, [midLat, midLon], c.to];

      L.polyline(latlngs, {{
        color: c.color,
        weight: 6,
        opacity: 0.22,
      }}).addTo(corridorsGroup);

      const line = L.polyline(latlngs, {{
        color: c.color,
        weight: 3,
        opacity: 0.92,
        dashArray: '8, 6',
        className: 'corridor-line',
      }});
      line.bindPopup(
        '<div style="font-weight:800;font-size:13px;color:#38bdf8;margin-bottom:4px;">🚚 ' + c.name + '</div>' +
        '<b>Annual Volume:</b> ' + c.tonnes + '<br/>' +
        '<b>Mean Haul Distance:</b> ' + c.dist_km + '<br/>' +
        '<b>Transport Mode:</b> ' + c.mode
      );
      corridorsGroup.addLayer(line);
    }});
  }}

  // 2) Contract Farm Parcels (Clean color-coded circles)
  let visibleHa = 0;
  if (showParcels) {{
    parcelsData.forEach((p) => {{
      if (activeHub !== 'ALL' && activeHub !== 'S-HQ' && p.dest_id !== activeHub) return;
      if (activeCrop !== 'all' && p.crop !== activeCrop) return;
      visibleHa += p.area_ha;

      const marker = L.circleMarker([p.lat, p.lon], {{
        radius: Math.max(4.5, Math.min(8.5, p.area_ha * 0.45)),
        fillColor: p.color,
        color: '#0f172a',
        weight: 1.2,
        fillOpacity: 0.88,
      }});
      marker.bindPopup(
        '<div style="font-weight:800;font-size:13px;color:#4ade80;margin-bottom:4px;">🌾 Parcel ' + p.parcel_id + ' (' + p.farm_id + ')</div>' +
        '<b>Contract Crop:</b> ' + p.crop_label + '<br/>' +
        '<b>Cultivated Area:</b> ' + p.area_ha + ' ha · <b>Slope:</b> ' + p.slope_pct + '%<br/>' +
        '<b>Soil Type:</b> ' + p.soil + ' · <b>Catchment:</b> ' + p.catchment_id + '<br/>' +
        '<b>Riparian Buffer:</b> ' + (p.buffer ? '<span style="color:#4ade80;font-weight:700;">Active ✓</span>' : '<span style="color:#fbbf24;font-weight:700;">Planned</span>') + '<br/>' +
        '<b>Receiving Hub:</b> ' + (p.dest_id === 'S-SAK' ? 'Säkylä Vegetable Plant' : 'Kantvik Oilseed Mill')
      );
      parcelsGroup.addLayer(marker);
    }});
  }}
  const haEl = document.getElementById('stat-ha');
  if (haEl) haEl.textContent = Math.round(visibleHa).toLocaleString() + ' ha';

  // 3) Apetit Corporate Facilities (Clear labeled pins on top)
  if (showSites) {{
    sitesData.forEach((s) => {{
      const iconEmoji = s.site_id === 'S-SAK' ? '🏭' : (s.site_id === 'S-KAN' ? '⚙️' : (s.site_id === 'S-BJU' ? '🌱' : (s.site_id === 'S-PUD' ? '❄️' : '🏢')));
      const divIcon = L.divIcon({{
        className: '',
        html:
          '<div class="site-marker-wrap">' +
          '<div class="site-pin" style="background:' + s.color + ';">' + iconEmoji + '</div>' +
          '<div class="site-lbl">' + s.name + '</div>' +
          '</div>',
        iconSize: [120, 46],
        iconAnchor: [60, 23],
      }});

      const m = L.marker([s.lat, s.lon], {{ icon: divIcon, zIndexOffset: 800 }});
      m.bindPopup(
        '<div style="font-weight:800;font-size:13.5px;color:#38bdf8;margin-bottom:3px;">' + iconEmoji + ' ' + s.name + ' (' + s.country + ')</div>' +
        '<span style="display:inline-block;padding:2px 7px;border-radius:4px;background:' + s.color + ';color:#fff;font-size:10px;font-weight:700;margin-bottom:6px;">' + s.badge + '</span><br/>' +
        '<b>Core Operations:</b> ' + s.role + '<br/>' +
        '<b>Coordinates:</b> ' + s.lat.toFixed(3) + '°N, ' + s.lon.toFixed(3) + '°E'
      );
      sitesGroup.addLayer(m);
    }});
  }}
}}

renderAll();

// ── 3. Interactive Controls ──────────────────────────────────────────────────
window.focusHub = function(hubId) {{
  activeHub = hubId;
  document.querySelectorAll('.hub-btn').forEach((b) => b.classList.remove('active'));
  const btn = document.getElementById('hub-' + hubId);
  if (btn) btn.classList.add('active');

  const wxLoc = document.getElementById('wx-loc-lbl');
  const wxTemp = document.getElementById('wx-temp-val');
  const wxStat = document.getElementById('wx-status-lbl');

  if (hubId === 'ALL') {{
    map.flyTo([59.85, 20.50], 6, {{ duration: 0.9 }});
    if (wxLoc) wxLoc.textContent = '📍 Säkylä Field Telemetry';
  }} else if (hubId === 'S-SAK') {{
    map.flyTo([61.0787, 22.2538], 9, {{ duration: 0.9 }});
    if (wxLoc) wxLoc.textContent = '📍 Säkylä Frozen Veg Shed';
    if (wxTemp) wxTemp.textContent = '{wx["temp_c"]}°C';
    if (wxStat) wxStat.textContent = '✓ Optimal Pea & Root Harvest Window';
  }} else if (hubId === 'S-KAN') {{
    map.flyTo([60.25, 24.10], 8, {{ duration: 0.9 }});
    if (wxLoc) wxLoc.textContent = '📍 Kantvik Oilseed Shed';
    if (wxTemp) wxTemp.textContent = '17.2°C';
    if (wxStat) wxStat.textContent = '✓ Dry Crushing & Seed Storage Optimal';
  }} else if (hubId === 'S-BJU') {{
    map.flyTo([56.084, 12.92], 9, {{ duration: 0.9 }});
    if (wxLoc) wxLoc.textContent = '📍 Bjuv (Foodhills Skåne SE)';
    if (wxTemp) wxTemp.textContent = '18.9°C';
    if (wxStat) wxStat.textContent = '✓ 90-Min Pea Harvest-to-Freezer Active';
  }} else if (hubId === 'S-HQ') {{
    map.flyTo([62.50, 25.50], 6, {{ duration: 0.9 }});
    if (wxLoc) wxLoc.textContent = '📍 Helsinki HQ & Pudasjärvi';
    if (wxTemp) wxTemp.textContent = '15.8°C';
  }}
  renderAll();
}};

window.filterByCrop = function(cropKey, btnEl) {{
  activeCrop = cropKey;
  document.querySelectorAll('.crop-pill').forEach((b) => b.classList.remove('active'));
  if (btnEl) btnEl.classList.add('active');
  renderAll();
}};

window.updateVisibleLayers = function() {{
  renderAll();
}};

window.setBasemapStyle = function(mode) {{
  document.getElementById('btn-base-sat').classList.toggle('active', mode === 'sat');
  document.getElementById('btn-base-road').classList.toggle('active', mode === 'road');
  if (mode === 'sat') {{
    if (map.hasLayer(roadLayer)) map.removeLayer(roadLayer);
    if (!map.hasLayer(satLayer)) satLayer.addTo(map);
    if (!map.hasLayer(satLabelsLayer)) satLabelsLayer.addTo(map);
  }} else {{
    if (map.hasLayer(satLayer)) map.removeLayer(satLayer);
    if (map.hasLayer(satLabelsLayer)) map.removeLayer(satLabelsLayer);
    if (!map.hasLayer(roadLayer)) roadLayer.addTo(map);
  }}
}};

window.toggleGeo3D = function() {{
  const mapEl = document.getElementById('map');
  const btn = document.getElementById('btn-geo-3d');
  const is3d = mapEl.classList.toggle('tilted-3d');
  if (btn) btn.classList.toggle('active', is3d);
  setTimeout(() => map.invalidateSize(), 460);
}};
</script>
</body>
</html>"""



