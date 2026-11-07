"""
prototype/views/biodiversity_view.py — Biodiversity & Nature Hotspot Explorer
Matches the reference image: circular satellite mask, grayscale outer map,
top filter bar, navy cluster badge, 3-column floating legend, and left-panel accordions.
"""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from core.api import NavigatorAPI
from core.biodiversity_service import BiodiversityService


# ── CORINE Land Cover colours (matching the reference image) ──────────────────
CORINE_LEGEND = [
    {"label": "Cropland, rainfed",                        "color": "#f5e642"},
    {"label": "Cropland, irrigated or post-flooding",      "color": "#c8d44e"},
    {"label": "Mosaic cropland (>50%) / nat. veg. (<50%)", "color": "#a3c154"},
    {"label": "Mosaic natural veg. (>50%) / cropland (<50%)", "color": "#8db567"},
    {"label": "Tree cover, broadleaved, evergreen (>15%)", "color": "#2d8b57"},
    {"label": "Tree cover, broadleaved, deciduous, closed to open (>15%)", "color": "#45a35e"},
    {"label": "Tree cover, broadleaved, deciduous, closed (>40%)", "color": "#1e7a40"},
    {"label": "Tree cover, broadleaved, deciduous, open (15-40%)", "color": "#6ab56e"},
    {"label": "Mosaic tree and shrub (>50%) / herbaceous (<50%)", "color": "#78c46e"},
    {"label": "Mosaic herbaceous cover (>50%) / tree and shrub (<50%)", "color": "#b5d87a"},
    {"label": "Shrubland",                                 "color": "#b8860b"},
    {"label": "Deciduous Shrubland",                       "color": "#c9a048"},
    {"label": "Grassland",                                 "color": "#dcc85c"},
    {"label": "Shrub or herbaceous cover, flooded, fresh/saline/brackish water", "color": "#77b6a0"},
    {"label": "Tree cover, flooded, saline water",          "color": "#4a9080"},
    {"label": "Herbaceous cover",                          "color": "#e8e040"},
    {"label": "Sparse vegetation (<15%)",                  "color": "#e0d080"},
    {"label": "Water bodies",                              "color": "#4a90d4"},
    {"label": "Urban areas",                               "color": "#d94040"},
]


def _build_nature_map_html(
    catchments_gj: dict,
    farms_gj: dict,
    water_bodies_gj: dict,
    protected_gj: dict,
    center_lat: float = 61.048,
    center_lon: float = 22.338,
    radius_km: float = 25.0,
    farm_count: int = 116,
) -> str:
    """Build the self-contained Leaflet.js biodiversity map matching the reference image exactly."""
    c_json = json.dumps(catchments_gj)
    f_json = json.dumps(farms_gj)
    w_json = json.dumps(water_bodies_gj)
    p_json = json.dumps(protected_gj)

    # Build CORINE legend rows — 3 columns
    legend_rows_html = ""
    for item in CORINE_LEGEND:
        legend_rows_html += (
            f'<div class="legend-item">'
            f'<span class="legend-dot" style="background:{item["color"]};"></span>'
            f'<span class="legend-text">{item["label"]}</span>'
            f'</div>'
        )

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  html, body {{ width:100%; height:100%; overflow:hidden; background:#f8f9fa; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; }}
  #map {{ width:100%; height:100vh; }}

  /* ── Zoom controls ────────────────────────────────────────────────── */
  .leaflet-control-zoom {{
    border: none !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.25) !important;
    border-radius: 8px !important;
  }}
  .leaflet-control-zoom a {{
    background: #fff !important;
    color: #334155 !important;
    border: none !important;
    font-size: 16px !important;
    line-height: 30px !important;
    width: 30px !important;
    height: 30px !important;
  }}
  .leaflet-control-zoom a:hover {{ background:#f1f5f9 !important; }}

  /* ── Top filter toolbar ───────────────────────────────────────────── */
  #filter-bar {{
    position: absolute;
    top: 12px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 1000;
    display: flex;
    align-items: center;
    gap: 10px;
    background: rgba(255,255,255,0.95);
    backdrop-filter: blur(12px);
    padding: 8px 16px;
    border-radius: 24px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.18);
    white-space: nowrap;
    font-size: 13px;
    color: #1e293b;
    border: 1px solid #e2e8f0;
  }}
  .filter-pill {{
    display: flex;
    align-items: center;
    gap: 5px;
    background: #f1f5f9;
    border: 1px solid #e2e8f0;
    border-radius: 20px;
    padding: 5px 12px;
    font-size: 12.5px;
    font-weight: 500;
    color: #334155;
    cursor: pointer;
    transition: background 0.2s;
  }}
  .filter-pill:hover {{ background: #e2e8f0; }}
  .filter-pill .caret {{ color: #64748b; font-size: 10px; margin-left: 2px; }}
  .filter-divider {{ width: 1px; height: 20px; background: #e2e8f0; }}
  .year-label {{ font-size: 11px; color: #64748b; font-weight: 600; }}
  #year-slider {{
    -webkit-appearance: none;
    width: 120px; height: 4px;
    border-radius: 2px;
    background: linear-gradient(to right, #10b981 0%, #10b981 70%, #e2e8f0 70%);
    outline: none; cursor: pointer;
  }}
  #year-slider::-webkit-slider-thumb {{
    -webkit-appearance: none;
    width: 14px; height: 14px;
    border-radius: 50%; background: #fff;
    border: 2px solid #10b981;
    box-shadow: 0 1px 4px rgba(0,0,0,0.2); cursor: pointer;
  }}
  #year-val {{ font-size: 12px; font-weight: 700; color: #10b981; min-width: 32px; }}

  /* ── Cluster badge ──────────────────────────────────────────────────── */
  .cluster-badge {{
    background: #0f172a; color: #ffffff;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-weight: 800; font-size: 18px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.5);
    border: 2.5px solid rgba(255,255,255,0.3);
  }}

  /* ── Legend toggle button (bottom-right) ────────────────────────────── */
  #legend-toggle-btn {{
    position: absolute;
    bottom: 20px; right: 14px;
    z-index: 1001;
    background: rgba(255,255,255,0.97);
    border: 1px solid #e2e8f0;
    border-radius: 20px;
    padding: 7px 14px;
    font-size: 12px; font-weight: 700;
    color: #0f172a;
    cursor: pointer;
    box-shadow: 0 2px 10px rgba(0,0,0,0.15);
    display: flex; align-items: center; gap: 5px;
    user-select: none;
    transition: background 0.2s;
  }}
  #legend-toggle-btn:hover {{ background: #f1f5f9; }}

  /* ── Legend panel (hidden by default) ──────────────────────────────── */
  #bio-legend {{
    position: absolute;
    bottom: 56px; right: 14px;
    z-index: 1000;
    background: rgba(255,255,255,0.97);
    border-radius: 10px;
    padding: 12px 14px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.18);
    border: 1px solid #e2e8f0;
    max-width: 480px;
    display: none;   /* ← hidden by default */
    animation: fadeIn 0.2s ease;
  }}
  @keyframes fadeIn {{ from {{ opacity:0; transform:translateY(6px); }} to {{ opacity:1; transform:translateY(0); }} }}
  .legend-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 4px 14px;
    margin-top: 6px;
  }}
  .legend-item {{
    display: flex; align-items: flex-start; gap: 5px;
    font-size: 10.5px; color: #334155; line-height: 1.3;
  }}
  .legend-dot {{
    display: inline-block; min-width: 10px; height: 10px;
    border-radius: 50%; flex-shrink: 0; margin-top: 1px;
  }}
  .legend-title {{
    font-size: 11.5px; font-weight: 700; color: #0f172a;
    border-bottom: 1px solid #e2e8f0;
    padding-bottom: 6px; margin-bottom: 4px;
    display: flex; justify-content: space-between; align-items: center;
  }}
  .legend-close {{
    cursor: pointer; color: #94a3b8; font-size: 14px; line-height: 1;
    padding: 0 2px;
  }}
  .legend-close:hover {{ color: #ef4444; }}

  /* ── Bottom-left Satellite thumbnail ───────────────────────────────── */
  #sat-thumb {{
    position: absolute; bottom: 20px; left: 14px;
    z-index: 1000;
    width: 72px; height: 54px;
    border-radius: 8px; overflow: hidden;
    box-shadow: 0 3px 12px rgba(0,0,0,0.3);
    cursor: pointer;
    border: 2px solid rgba(255,255,255,0.9);
    background: #334155;
    display: flex; flex-direction: column;
    align-items: center; justify-content: flex-end;
    padding-bottom: 4px;
    transition: transform 0.2s;
  }}
  #sat-thumb:hover {{ transform: scale(1.05); }}
  #sat-thumb img {{
    position: absolute; top:0; left:0; width:100%; height:100%; object-fit: cover; opacity: 0.85;
  }}
  #sat-thumb .sat-label {{
    position: relative; z-index: 1;
    font-size: 10px; font-weight: 700; color: #fff;
    text-shadow: 0 1px 3px rgba(0,0,0,0.9);
  }}

  /* ── Popup styling ──────────────────────────────────────────────────── */
  .leaflet-popup-content-wrapper {{
    background: rgba(15,23,42,0.96) !important;
    color: #f1f5f9 !important;
    border: 1px solid #334155 !important;
    border-radius: 10px !important;
    box-shadow: 0 10px 32px rgba(0,0,0,0.6) !important;
  }}
  .leaflet-popup-content {{ margin: 12px 16px !important; line-height: 1.65; font-size: 12px; }}
  .leaflet-popup-tip {{ background: rgba(15,23,42,0.96) !important; }}
  .popup-title {{ font-size: 14px; font-weight: 700; color: #38bdf8; margin-bottom: 4px; }}
  .popup-badge {{ display:inline-block; padding:2px 7px; border-radius:4px; font-size:10px; font-weight:700; margin-bottom:6px; }}
  .badge-red   {{ background:#ef4444; color:white; }}
  .badge-amber {{ background:#f59e0b; color:white; }}
  .badge-green {{ background:#10b981; color:white; }}
  .badge-blue  {{ background:#0284c7; color:white; }}

  /* ── Interaction lock overlay ───────────────────────────────────────── */
  #map-lock {{
    position: absolute; top:0; left:0; width:100%; height:100%;
    z-index: 2000; cursor: pointer;
    background: transparent;
    display: flex; align-items: center; justify-content: center;
  }}
  #map-lock-hint {{
    background: rgba(15,23,42,0.72);
    color: #fff;
    padding: 10px 20px;
    border-radius: 24px;
    font-size: 13px; font-weight: 600;
    pointer-events: none;
    box-shadow: 0 4px 16px rgba(0,0,0,0.3);
    display: flex; align-items: center; gap: 8px;
  }}

  .leaflet-control-attribution {{ font-size: 9px !important; }}
</style>
</head>
<body>
<div id="map"></div>

<!-- Interaction lock overlay — prevents scroll hijack until user deliberately clicks -->
<div id="map-lock" onclick="unlockMap()">
  <div id="map-lock-hint">🗺️ Click to interact with map</div>
</div>

<!-- Top Filter Bar -->
<div id="filter-bar">
  <div class="filter-pill">🦅 Species type <span class="caret">▾</span></div>
  <div class="filter-divider"></div>
  <div class="filter-pill">🛡️ Conservation Status <span class="caret">▾</span></div>
  <div class="filter-divider"></div>
  <span class="year-label">Year</span>
  <span class="year-label">1980</span>
  <span class="year-label">to</span>
  <input type="range" id="year-slider" min="1980" max="2026" value="2002"
         oninput="document.getElementById('year-val').textContent=this.value">
  <span id="year-val">2002</span>
</div>

<!-- Bottom-left Satellite Thumbnail -->
<div id="sat-thumb" onclick="toggleSatView()" title="Toggle Satellite View">
  <img src="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export?bbox=22.19,61.0,22.5,61.09&bboxSR=4326&imageSR=4326&size=72,54&format=jpg&f=image"
       alt="Satellite" onerror="this.style.display='none'">
  <span class="sat-label">Satellite</span>
</div>

<!-- Legend toggle button -->
<div id="legend-toggle-btn" onclick="toggleLegend()">
  🌿 Land Cover Legend <span id="legend-caret">▲</span>
</div>

<!-- Legend panel (collapsed by default) -->
<div id="bio-legend">
  <div class="legend-title">
    🌿 Land Cover / Habitat Types
    <span class="legend-close" onclick="toggleLegend()">✕</span>
  </div>
  <div class="legend-grid">
    {legend_rows_html}
  </div>
</div>

<script>
// ── Map setup ──────────────────────────────────────────────────────────────
var map = L.map('map', {{
  center: [{center_lat}, {center_lon}],
  zoom: 10,
  zoomControl: true,
  attributionControl: true,
  scrollWheelZoom: false,   // ← disabled: prevents scroll hijack inside iframe
  dragging: true,
  tap: true,
}});

// Position zoom controls to top-right to avoid filter bar overlap
map.zoomControl.setPosition('topright');

// ── 1. Esri World Light Gray Canvas (outer map — free, no API key) ─────────
var lightGray = L.tileLayer(
  'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Canvas/MapServer/tile/{{z}}/{{y}}/{{x}}',
  {{
    maxZoom: 16,
    attribution: '© Esri — Esri, HERE, Garmin, © OpenStreetMap contributors',
  }}
).addTo(map);

// Light gray reference labels
L.tileLayer(
  'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Reference/MapServer/tile/{{z}}/{{y}}/{{x}}',
  {{ maxZoom: 16, opacity: 0.7, attribution: '' }}
).addTo(map);

// ── 2. Create a custom pane for satellite tiles that will be clipped ────────
map.createPane('satPane');
map.getPane('satPane').style.zIndex = 250;  // above base, below overlays

var esriSat = L.tileLayer(
  'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}',
  {{
    pane: 'satPane',
    maxZoom: 20,
    attribution: '© Esri — Maxar, Earthstar Geographics',
  }}
).addTo(map);

// Esri reference labels on top of satellite
map.createPane('labelsPane');
map.getPane('labelsPane').style.zIndex = 260;
var esriLabels = L.tileLayer(
  'https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{{z}}/{{y}}/{{x}}',
  {{ pane: 'labelsPane', opacity: 0.6, maxZoom: 20, attribution: '' }}
).addTo(map);

// ── 3. Clip the satellite pane to the project circle ───────────────────────
var centerLat = {center_lat};
var centerLon = {center_lon};
var radiusM   = {radius_km} * 1000;

function updateClipPath() {{
  var cp = map.latLngToContainerPoint(L.latLng(centerLat, centerLon));
  // Compute radius in pixels at current zoom
  var edgePt = map.latLngToContainerPoint(
    L.latLng(centerLat, centerLon + {radius_km} / (111.32 * Math.cos(centerLat * Math.PI / 180)))
  );
  var rx = Math.abs(edgePt.x - cp.x);
  var pane = map.getPane('satPane');
  var clip = 'circle(' + rx + 'px at ' + cp.x + 'px ' + cp.y + 'px)';
  pane.style.clipPath = clip;
  pane.style.webkitClipPath = clip;

  var labPane = map.getPane('labelsPane');
  labPane.style.clipPath = clip;
  labPane.style.webkitClipPath = clip;
}}

map.on('move zoom viewreset moveend zoomend', updateClipPath);
updateClipPath();

// ── 4. Black circle boundary ring ─────────────────────────────────────────
var boundaryCircle = L.circle([centerLat, centerLon], {{
  radius: radiusM,
  color: '#1e293b',
  weight: 3.5,
  fill: false,
  opacity: 1.0,
}}).addTo(map);

// ── 5. Catchment polygons ──────────────────────────────────────────────────
var catchmentsData = {c_json};
var catchmentsLayer = L.geoJSON(catchmentsData, {{
  style: function(f) {{
    var p = f.properties;
    return {{
      color: p.stroke_color || '#38bdf8',
      weight: 1.0,
      fillColor: p.stroke_color || '#38bdf8',
      fillOpacity: 0.14,
      dashArray: '3, 5',
    }};
  }},
  onEachFeature: function(f, layer) {{
    var p = f.properties;
    var badgeClass = p.risk_level.includes("High") ? "badge-red" : (p.risk_level.includes("Moderate") ? "badge-amber" : "badge-green");
    layer.bindPopup(
      '<div class="popup-title">🌊 Catchment ' + p.catchment_id + '</div>' +
      '<span class="popup-badge ' + badgeClass + '">' + p.risk_level + '</span><br/>' +
      '<b>Ecological Status:</b> ' + p.ecological_status + '<br/>' +
      '<b>P-Sensitivity:</b> ' + p.p_sensitivity + '× benchmark<br/>' +
      '<b>Waterbody:</b> ' + p.receiving_water_type + '<br/>' +
      '<b>Basin Area:</b> ' + p.catchment_area_km2 + ' km²'
    );
    layer.on('mouseover', function() {{ this.setStyle({{ fillOpacity: 0.30, weight: 2.0 }}); }});
    layer.on('mouseout',  function() {{ this.setStyle({{ fillOpacity: 0.14, weight: 1.0 }}); }});
  }}
}}).addTo(map);

// ── 6. Water bodies ───────────────────────────────────────────────────────
var waterData = {w_json};
var waterLayer = L.geoJSON(waterData, {{
  style: function(f) {{
    return {{
      color: f.properties.color,
      weight: f.geometry.type === 'LineString' ? 3.5 : 2,
      fillColor: f.properties.color,
      fillOpacity: f.geometry.type === 'LineString' ? 0 : 0.60,
    }};
  }},
  onEachFeature: function(f, layer) {{
    var p = f.properties;
    layer.bindPopup(
      '<div class="popup-title">💧 ' + p.name + '</div>' +
      '<span class="popup-badge badge-blue">' + p.type + '</span><br/>' +
      '<b>Status:</b> ' + p.status + '<br/>' +
      '<hr style="border:none;border-top:1px solid #334155;margin:6px 0;"/>' +
      p.dependency
    );
  }}
}}).addTo(map);

// ── 7. Protected areas ────────────────────────────────────────────────────
var protectedData = {p_json};
var protectedLayer = L.geoJSON(protectedData, {{
  style: function(f) {{
    return {{
      color: f.properties.color,
      weight: 1.5,
      fillColor: f.properties.color,
      fillOpacity: 0.32,
      dashArray: '5, 4',
    }};
  }},
  onEachFeature: function(f, layer) {{
    var p = f.properties;
    layer.bindPopup(
      '<div class="popup-title">🛡️ ' + p.name + '</div>' +
      '<span class="popup-badge badge-green">' + p.designation + '</span><br/>' +
      '<b>Natura 2000:</b> ' + p.code + '<br/>' +
      '<b>Protected Area:</b> ' + p.area_km2 + ' km²<br/>' +
      '<hr style="border:none;border-top:1px solid #334155;margin:6px 0;"/>' +
      p.values
    );
  }}
}}).addTo(map);

// ── 8. Contract farm points ───────────────────────────────────────────────
var farmsData = {f_json};
var farmsLayer = L.geoJSON(farmsData, {{
  pointToLayer: function(f, latlng) {{
    var p = f.properties;
    return L.circleMarker(latlng, {{
      radius: 5,
      fillColor: p.pin_color,
      color: '#ffffff',
      weight: 1.2,
      opacity: 1.0,
      fillOpacity: 0.88,
    }});
  }},
  onEachFeature: function(f, layer) {{
    var p = f.properties;
    var badgeClass = p.pin_color === "#ef4444" ? "badge-red" : (p.pin_color === "#f59e0b" ? "badge-amber" : "badge-green");
    layer.bindPopup(
      '<div class="popup-title">🚜 Farm ' + p.farm_id + ' — ' + p.crop + '</div>' +
      '<span class="popup-badge ' + badgeClass + '">' + p.eco_risk + '</span><br/>' +
      '<b>Area:</b> ' + p.total_area_ha + ' ha | <b>Catchment:</b> ' + p.catchment_id + '<br/>' +
      '<b>Dist. to Ditch:</b> ' + p.min_dist_water_m + ' m | <b>Buffer Strip:</b> ' + p.buffer_coverage_pct + '%<br/>' +
      '<hr style="border:none;border-top:1px solid #334155;margin:6px 0;"/>' +
      p.impact_statement
    );
  }}
}}).addTo(map);

// ── 9. Central cluster badge "116" ────────────────────────────────────────
var clusterIcon = L.divIcon({{
  className: '',
  html: '<div class="cluster-badge" style="width:52px;height:52px;">{farm_count}</div>',
  iconSize: [52, 52],
  iconAnchor: [26, 26],
}});
var clusterMarker = L.marker([centerLat, centerLon], {{ icon: clusterIcon, zIndexOffset: 500 }})
  .bindPopup(
    '<div class="popup-title">📍 Apetit Säkylä Sourcing Hub</div>' +
    '<span class="popup-badge badge-blue">Central Processing Facility</span><br/>' +
    '<b>Contract Farms in Radius:</b> {farm_count}<br/>' +
    '<b>Sourcing Shed:</b> {radius_km} km radius<br/>' +
    '<b>Primary Waterbody Risk:</b> Lake Pyhäjärvi (Phosphorus)'
  ).addTo(map);

// ── 10. Scale bar ─────────────────────────────────────────────────────────
L.control.scale({{ imperial: false, position: 'bottomleft', maxWidth: 100 }}).addTo(map);

// ── Satellite toggle ──────────────────────────────────────────────────────
var satVisible = true;
function toggleSatView() {{
  satVisible = !satVisible;
  if (satVisible) {{
    map.addLayer(esriSat);
    map.addLayer(esriLabels);
    updateClipPath();
  }} else {{
    map.removeLayer(esriSat);
    map.removeLayer(esriLabels);
  }}
}}

// ── Legend toggle (collapsed by default) ─────────────────────────────────
var legendOpen = false;
function toggleLegend() {{
  legendOpen = !legendOpen;
  var panel  = document.getElementById('bio-legend');
  var caret  = document.getElementById('legend-caret');
  panel.style.display = legendOpen ? 'block' : 'none';
  if (caret) caret.textContent = legendOpen ? '▼' : '▲';
}}

// ── Map interaction lock (prevents scroll hijack in Streamlit iframe) ─────
var mapLocked = true;
var lockDiv   = document.getElementById('map-lock');

function unlockMap() {{
  mapLocked = false;
  lockDiv.style.display = 'none';
  map.scrollWheelZoom.enable();
  map.dragging.enable();
}}

// Re-lock when mouse leaves the map area entirely
document.addEventListener('mouseleave', function() {{
  if (!mapLocked) {{
    mapLocked = true;
    map.scrollWheelZoom.disable();
    lockDiv.style.display = 'flex';
  }}
}});

</script>
</body>
</html>"""


def render(root: Path) -> None:
    api = NavigatorAPI(root)
    if not hasattr(api, "biodiversity"):
        api.biodiversity = BiodiversityService(root)

    # ── Custom CSS for the left panel ─────────────────────────────────────────
    st.markdown("""
    <style>
    /* Sidebar panel cards */
    .bio-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px 18px;
        margin-bottom: 12px;
    }
    .bio-card-header {
        font-size: 0.70rem;
        color: #64748b;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    .bio-card-title {
        font-size: 1.10rem;
        font-weight: 900;
        color: #0f172a;
        margin: 4px 0 2px 0;
        line-height: 1.3;
    }
    .bio-card-sub {
        font-size: 0.78rem;
        color: #0284c7;
        font-weight: 600;
    }
    .bio-metric-row {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-top: 10px;
    }
    .bio-metric {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-radius: 8px;
        padding: 8px 12px;
        text-align: center;
        flex: 1;
    }
    .bio-metric-val { font-size: 1.15rem; font-weight: 800; color: #059669; }
    .bio-metric-lbl { font-size: 0.65rem; color: #64748b; font-weight: 600; margin-top: 1px; }

    /* Habitat list items */
    .hab-item {
        display: flex;
        align-items: center;
        gap: 7px;
        font-size: 0.74rem;
        color: #475569;
        margin-bottom: 5px;
        line-height: 1.4;
    }
    .hab-dot {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        flex-shrink: 0;
    }
    .hab-name { flex: 1; color: #0f172a; font-weight: 500; }
    .hab-pct { font-weight: 800; color: #334155; }

    /* Species & risk list */
    .species-row {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-left: 3px solid #ef4444;
        border-radius: 8px;
        padding: 10px 12px;
        margin-bottom: 8px;
        font-size: 0.80rem;
        color: #1e293b;
        line-height: 1.6;
    }
    .species-row.moderate { border-left-color: #f59e0b; }
    .species-row.low { border-left-color: #10b981; }
    .species-name { font-weight: 700; font-size: 0.84rem; color: #0f172a; margin-bottom: 2px; }

    /* Impact assessment card */
    .impact-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 18px 20px;
        margin-top: 12px;
        font-size: 0.84rem;
    }
    .impact-card-title {
        font-size: 1.0rem;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .risk-badge-high { background:#fef2f2; color:#ef4444; border:1px solid #fecaca; border-radius:6px; padding:3px 8px; font-size:0.74rem; font-weight:700; }
    .risk-badge-low  { background:#f0fdf4; color:#059669; border:1px solid #bbf7d0; border-radius:6px; padding:3px 8px; font-size:0.74rem; font-weight:700; }

    /* Disclaimer */
    .data-disclaimer {
        background: #fffbeb;
        border: 1px solid #fde68a;
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 0.72rem;
        color: #92400e;
        margin-top: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── 2-Column layout: Left panel + Map ─────────────────────────────────────
    col_panel, col_map = st.columns([1.05, 2.3])

    # ════════════════════════════════════════════════════════════════════════
    # LEFT PANEL
    # ════════════════════════════════════════════════════════════════════════
    with col_panel:
        # Header card
        st.markdown("""
        <div class="bio-card">
            <div style="display:flex; align-items:flex-start; justify-content:space-between; gap:8px;">
                <div>
                    <div class="bio-card-header">Sourcing Project Basin</div>
                    <div class="bio-card-title">Eurajoki &amp; Pyhäjärvi Basin</div>
                    <div class="bio-card-sub">Southwest Finland · 61.048°N 22.338°E</div>
                </div>
                <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:50%;width:40px;height:40px;display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0;">🌿</div>
            </div>
            <div class="bio-metric-row">
                <div class="bio-metric">
                    <div class="bio-metric-val">615</div>
                    <div class="bio-metric-lbl">Total km²</div>
                </div>
                <div class="bio-metric">
                    <div class="bio-metric-val">116</div>
                    <div class="bio-metric-lbl">Contract Farms</div>
                </div>
                <div class="bio-metric" style="background:#fff7ed;border-color:#fed7aa;">
                    <div class="bio-metric-val" style="color:#ea580c;">1.6×</div>
                    <div class="bio-metric-lbl">Eutroph. Risk</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Accordion 1: Key Biodiversity Areas ───────────────────────────
        with st.expander("🦅 Key Biodiversity Areas", expanded=True):
            st.markdown("""
            <div style="font-size:0.80rem; color:#475569; line-height:1.75;">
            <b style="color:#0f172a;">📍 Lake Pyhäjärvi Shoreline & Islets</b><br>
            Breeding habitat for Whooper Swan (<i>Cygnus cygnus</i>) and aquatic Lobelia (<i>Lobelia dortmanna</i>).
            High vulnerability to phosphorus enrichment.<br><br>
            <b style="color:#0f172a;">🏔️ Säkylänharju Glacial Esker</b><br>
            Class I groundwater recharge aquifer supplying municipal drinking water.
            Rare endemic dry pine heath and lichen communities.<br><br>
            <b style="color:#0f172a;">🌊 Yläneenjoki Riparian Floodplain</b><br>
            Critical nutrient interception buffer before lake inlet.
            Atlantic salmon (<i>Salmo salar</i>) spawning run corridor.
            </div>
            """, unsafe_allow_html=True)

        # ── Accordion 2: Protected Areas ──────────────────────────────────
        with st.expander("🛡️ Protected Areas", expanded=True):
            st.markdown("""
            <div style="font-size:0.80rem; color:#475569; line-height:1.75;">
            <b style="color:#0f172a; display:flex; justify-content:space-between;">
                Pyhäjärvi Shoreline & Islets SAC
                <span style="background:#dcfce7;color:#15803d;border-radius:4px;padding:1px 6px;font-size:0.68rem;">Natura 2000</span>
            </b>
            FI0200084 · 18.2 km² · EU Habitats Directive<br><br>
            <b style="color:#0f172a;">Kurjenrahka National Park</b>
            <span style="background:#dcfce7;color:#15803d;border-radius:4px;padding:1px 6px;font-size:0.68rem;">Ramsar</span><br>
            FI0200062 · 29.0 km² · Pristine ombrotrophic peatland<br><br>
            <b style="color:#0f172a;">Torronsuo Mire Complex</b>
            <span style="background:#dbeafe;color:#1d4ed8;border-radius:4px;padding:1px 6px;font-size:0.68rem;">Ramsar</span><br>
            FI0304001 · 25.5 km² · Wetland of International Importance<br><br>
            <b style="color:#0f172a;">Säkylänharju Esker Forest</b>
            <span style="background:#dcfce7;color:#15803d;border-radius:4px;padding:1px 6px;font-size:0.68rem;">Natura 2000</span><br>
            FI0200078 · 21.0 km² · Groundwater protection
            </div>
            """, unsafe_allow_html=True)

        # ── Accordion 3: Habitat Types + Donut chart ──────────────────────
        with st.expander("🌾 Percentage Of Habitat Types", expanded=True):
            # Toggle switch row
            st.markdown("""
            <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px;">
                <span style="font-size:0.76rem; color:#475569; font-weight:500;">See these habitat types on the map</span>
                <div style="background:#10b981;border-radius:12px;width:34px;height:18px;display:flex;align-items:center;justify-content:flex-end;padding:2px;cursor:pointer;">
                    <div style="background:white;border-radius:50%;width:14px;height:14px;"></div>
                </div>
            </div>
            <div style="font-size:0.72rem; color:#64748b; margin-bottom:8px;">These habitat types are in the 25km project radius:</div>
            """, unsafe_allow_html=True)

            habitat_data = api.biodiversity.get_habitat_breakdown("CA01")["habitats"]
            df_hab = pd.DataFrame(habitat_data)

            fig_donut = go.Figure(go.Pie(
                labels=df_hab["label"],
                values=df_hab["pct"],
                hole=0.62,
                marker_colors=df_hab["color"].tolist(),
                textinfo="none",
                hovertemplate="<b>%{label}</b><br>%{percent}<extra></extra>",
            ))
            fig_donut.update_layout(
                height=190,
                margin=dict(l=5, r=5, t=5, b=5),
                paper_bgcolor="#ffffff",
                plot_bgcolor="#ffffff",
                showlegend=False,
                annotations=[dict(
                    text="<b>615<br>km²</b>",
                    x=0.5, y=0.5,
                    font=dict(size=13, color="#0f172a"),
                    showarrow=False
                )],
            )
            st.plotly_chart(fig_donut, use_container_width=True, config={"displayModeBar": False})

            # Habitat list with coloured bullets
            for h in habitat_data:
                st.markdown(
                    f'<div class="hab-item">'
                    f'<span class="hab-dot" style="background:{h["color"]};"></span>'
                    f'<span class="hab-name">{h["label"]}</span>'
                    f'<span class="hab-pct">{h["pct"]:.0f}%</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        # ── Bottom dual tabs ─────────────────────────────────────────────
        tab_sp, tab_bio = st.tabs(["🐾 Species details & risks", "📊 Overall biodiversity"])

        with tab_sp:
            st.markdown("""
            <div class="species-row">
                <div class="species-name">Freshwater Pearl Mussel <i>(Margaritifera margaritifera)</i></div>
                High vulnerability to agricultural sediment &amp; siltation. 
                Critically dependent on clean, well-oxygenated cold water.
                Present in upper Eurajoki tributaries.
            </div>
            <div class="species-row moderate">
                <div class="species-name">Atlantic Salmon <i>(Salmo salar)</i></div>
                Spawning runs threatened by elevated water temperature, hypoxia, 
                and elevated turbidity in Eurajoki. 
                Migration route bisects agricultural zone CA04–CA07.
            </div>
            <div class="species-row low">
                <div class="species-name">Eurasian Crane <i>(Grus grus)</i></div>
                Autumn staging populations of 1,200–1,800 birds use post-harvest 
                pea &amp; cereal fields within the sourcing basin for pre-migration foraging.
            </div>
            """, unsafe_allow_html=True)

        with tab_bio:
            m1, m2 = st.columns(2)
            m1.metric("Biodiversity Intactness Index", "74 / 100", "+3 pts vs 2021")
            m2.metric("Eutrophication Threat Index", "1.60×", "High sensitivity", delta_color="off")
            st.metric("Species Richness Index (5-km radius)", "142 species", "+6 vs baseline")
            st.caption("🏔️ Groundwater: Säkylänharju Class I Aquifer · High vulnerability rating")
            st.caption("📊 Synthetic data for demonstration · SBTN Step 1–2 methodology")

    # ════════════════════════════════════════════════════════════════════════
    # RIGHT COLUMN: Leaflet Map + Assessment Card
    # ════════════════════════════════════════════════════════════════════════
    with col_map:
        # Controls row above the map
        ctrl_c1, ctrl_c2 = st.columns([1.5, 1.0])
        with ctrl_c1:
            radius_sel = st.select_slider(
                "Sourcing Shed Radius",
                options=[5, 10, 15, 20, 25, 35, 40],
                value=25,
                format_func=lambda x: f"⭕ {x} km",
            )
        with ctrl_c2:
            farms_catalog = api.biodiversity.get_farms_geojson(max_farms=100)["features"]
            farm_opts = {
                f["properties"]["farm_id"]: f"{f['properties']['farm_id']} — {f['properties']['crop']} ({f['properties']['total_area_ha']} ha)"
                for f in farms_catalog
            }
            selected_fid = st.selectbox(
                "Inspect Farm:",
                list(farm_opts.keys()),
                format_func=lambda k: farm_opts[k],
                index=0,
            )

        # Build and render the 3D Satellite Geomap + Circular Satellite Mask Map
        catchments_gj = api.biodiversity.get_catchments_geojson()
        farms_gj      = api.biodiversity.get_farms_geojson(max_farms=116)
        water_gj      = api.biodiversity.get_water_bodies_geojson()
        prot_gj       = api.biodiversity.get_protected_areas_geojson()

        from components.satellite_3d_map import (
            build_satellite_3d_deck,
            build_threejs_satellite_3d_terrain_html,
            render_realtime_satellite_hud,
        )
        import pydeck as pdk

        render_realtime_satellite_hud(
            lat=61.048,
            lon=22.338,
            region_label=f"Lake Pyhäjärvi & Satakunta Biodiversity Shed ({radius_sel} km)",
            parcel_count=len(farms_gj["features"]),
            mode_badge="3D SATELLITE BIODIVERSITY",
        )

        bio_t1, bio_t2, bio_t3 = st.tabs([
            "⭕ Circular Satellite Lens + CORINE Habitat Map",
            "🛰️ Real-Time 3D Satellite Deck.gl Geomap",
            "🏔️ 3D Satellite Terrain Mesh (360° Three.js)",
        ])

        with bio_t1:
            map_html = _build_nature_map_html(
                catchments_gj=catchments_gj,
                farms_gj=farms_gj,
                water_bodies_gj=water_gj,
                protected_gj=prot_gj,
                center_lat=61.048,
                center_lon=22.338,
                radius_km=float(radius_sel),
                farm_count=len(farms_gj["features"]),
            )
            components.html(map_html, height=640, scrolling=False)

        with bio_t2:
            bio_rows = []
            for feat in farms_gj["features"]:
                coords = feat["geometry"]["coordinates"]
                props = feat["properties"]
                has_buf = float(props.get("buffer_pct", 50)) >= 50.0
                bio_rows.append({
                    "farm_id": props.get("farm_id", "F001"),
                    "lon": float(coords[0]),
                    "lat": float(coords[1]),
                    "crop": props.get("crop", "Pea"),
                    "area_ha": float(props.get("total_area_ha", 18.0)),
                    "buffer_pct": float(props.get("buffer_pct", 50.0)),
                    "elevation": round((100.0 - float(props.get("buffer_pct", 50.0))) * 22.0 + float(props.get("total_area_ha", 18.0)) * 25.0, 0),
                    "color": [16, 185, 129, 220] if has_buf else [239, 68, 68, 225],
                    "hex_color": "#10b981" if has_buf else "#ef4444",
                    "tier": "Habitat Buffer Protected ✓" if has_buf else "High Eutrophication Pressure ⚠️",
                    "info": f"Crop: {props.get('crop', 'Pea')} | Buffer: {props.get('buffer_pct', 50)}%",
                })
            df_bio_3d = pd.DataFrame(bio_rows)
            bio_col_layer = pdk.Layer(
                "ColumnLayer",
                data=df_bio_3d,
                get_position=["lon", "lat"],
                get_elevation="elevation",
                elevation_scale=1,
                radius=340,
                get_fill_color="color",
                pickable=True,
                auto_highlight=True,
                extruded=True,
            )
            bio_deck = build_satellite_3d_deck(
                feature_layers=[bio_col_layer],
                lat=61.048,
                lon=22.338,
                zoom=9.5,
                pitch=54.0,
                bearing=16.0,
                tooltip={
                    "html": "<b>Farm:</b> {farm_id} ({tier})<br/><b>Crop:</b> {crop} | <b>Area:</b> {area_ha} ha<br/><b>Riparian Buffer:</b> {buffer_pct}%",
                    "style": {"zIndex": "1000"},
                },
                include_labels=True,
            )
            st.pydeck_chart(bio_deck, use_container_width=True)

        with bio_t3:
            if not df_bio_3d.empty:
                bio_three = build_threejs_satellite_3d_terrain_html(
                    df=df_bio_3d,
                    title="Lake Pyhäjärvi & Natura 2000 3D Satellite Terrain",
                    lat_col="lat",
                    lon_col="lon",
                    id_col="farm_id",
                    value_col="area_ha",
                    tier_col="tier",
                    color_col="hex_color",
                    extra_col="info",
                    value_unit="ha contract farm",
                    relief_scale=1.7,
                    height_px=560,
                )
                components.html(bio_three, height=570, scrolling=False)

        # ── Environmental Dependency & Impact Assessment Card ─────────────
        impact_data = api.biodiversity.assess_target("farm", selected_fid)

        is_high = impact_data["eutrophication_risk"] == "High"
        risk_badge = (
            '<span class="risk-badge-high">⚠️ High Eutrophication Risk</span>'
            if is_high else
            '<span class="risk-badge-low">✅ Low / Moderate Risk</span>'
        )
        border_color = "#ef4444" if is_high else "#10b981"

        st.markdown(
            f"""
            <div class="impact-card" style="border-left:4px solid {border_color};">
                <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:12px;">
                    <div class="impact-card-title">📍 {impact_data['title']}</div>
                    {risk_badge}
                </div>
                <div style="font-size:0.76rem; color:#64748b; margin-bottom:12px;">
                    Catchment: <b>{impact_data['catchment']}</b> &nbsp;|&nbsp;
                    Dist. to water: <b>{impact_data['proximity_water']}</b> &nbsp;|&nbsp;
                    Buffer strip coverage: <b>{impact_data['buffer_coverage']}</b>
                </div>
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:14px; font-size:0.82rem; line-height:1.7; margin-bottom:14px;">
                    <div>
                        <b style="color:#0284c7;">🌿 Ecosystem Dependencies (ENCORE):</b><br>
                        {impact_data['ecosystem_dependency'].replace(chr(10), '<br>')}
                    </div>
                    <div>
                        <b style="color:#ef4444;">🌊 Potential Environmental Pressures:</b><br>
                        {impact_data['potential_impact'].replace(chr(10), '<br>')}
                    </div>
                </div>
                <div style="background:#f0fdf4; border:1px solid #bbf7d0; border-radius:8px; padding:12px 14px; font-size:0.82rem; color:#1e293b; line-height:1.7;">
                    <b style="color:#059669;">🛡️ SBTN Freshwater Mitigation Action:</b><br>
                    {impact_data['recommended_action'].replace(chr(10), '<br>')}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Disclaimer + Export
        exp_col1, exp_col2 = st.columns([2.5, 1.5])
        with exp_col1:
            st.markdown(
                '<div class="data-disclaimer">⚠️ Synthetic demonstration data · '
                'Calibrated to SBTN Step 1 & 2 freshwater methodology · '
                'All species and habitat data are illustrative only.</div>',
                unsafe_allow_html=True,
            )
        with exp_col2:
            brief_md = (
                f"# SBTN Biodiversity & Nature Hotspot Assessment\n\n"
                f"**Target:** {impact_data['title']} | **Catchment:** {impact_data['catchment']}\n"
                f"**Eutrophication Risk:** {impact_data['eutrophication_risk']}\n"
                f"**Dist. to Ditch:** {impact_data['proximity_water']} | **Buffer Coverage:** {impact_data['buffer_coverage']}\n\n"
                f"## Natural Capital Dependencies\n{impact_data['ecosystem_dependency']}\n\n"
                f"## Environmental Pressures\n{impact_data['potential_impact']}\n\n"
                f"## SBTN Recommended Mitigation\n{impact_data['recommended_action']}\n\n"
                f"---\n*Synthetic data · SBTN Step 1–2 methodology*"
            )
            st.download_button(
                "📄 Export Biodiversity Brief",
                brief_md,
                file_name=f"biodiversity_assessment_{selected_fid}.md",
                mime="text/markdown",
                use_container_width=True,
            )
