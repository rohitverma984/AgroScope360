"""
prototype/core/geo_service.py — Geospatial Command Center Service
Integrates corporate sites, field parcel geometries, inbound logistics arcs, and live weather APIs.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import requests
import pandas as pd
import streamlit as st


class GeoService:
    def __init__(self, root: Path):
        self.root = root
        self.sites_path = root / "data" / "01_master" / "sites.csv"
        self.parcels_path = root / "data" / "01_master" / "parcels.csv"
        self.crop_path = root / "data" / "03_farming" / "parcel_crop_history_and_plan.csv"
        self.catchments_path = root / "data" / "06_nature" / "catchments.csv"
        self.shipments_path = root / "data" / "02_raw_feeds" / "shipments.csv"

    def get_sites(self) -> pd.DataFrame:
        """Return Apetit facilities with latitude, longitude, and operational status."""
        df = pd.read_csv(self.sites_path)
        # Custom color coding for sites: Säkylä (Green), Kantvik (Blue), Pudasjärvi (Orange), Bjuv (Purple)
        color_map = {
            "S-SAK": [46, 204, 113, 220],   # Emerald Green
            "S-KAN": [52, 152, 219, 220],   # Sky Blue
            "S-PUD": [230, 126, 34, 220],   # Orange
            "S-BJU": [155, 89, 182, 220],   # Purple
            "S-HQ":  [52, 73, 94, 220],     # Slate Navy
        }
        df["color"] = df["site_id"].map(color_map)
        df["radius"] = 3500  # meters
        return df

    def get_parcels(
        self,
        year: int = 2025,
        crop: Optional[str] = None,
        buffer_only: Optional[bool] = None,
        limit: int = 2500,
    ) -> pd.DataFrame:
        """Return sampled contract parcels with coordinates, crop, and nature attributes."""
        parcels = pd.read_csv(self.parcels_path)
        crops = pd.read_csv(self.crop_path)
        
        c_yr = crops[crops["year"] == year]
        merged = c_yr.merge(parcels, on="parcel_id", how="inner")

        if crop and crop != "all":
            merged = merged[merged["crop"] == crop]
        if buffer_only is True:
            merged = merged[merged["buffer_strip"] == True]
        elif buffer_only is False:
            merged = merged[merged["buffer_strip"] == False]

        # Sample for ultra-smooth Deck.gl browser rendering if dataset is huge
        if len(merged) > limit:
            merged = merged.sample(n=limit, random_state=42)

        # Color-coding by crop:
        # pea = bright green, potato = goldenrod, carrot = coral, turnip_rape = gold
        crop_colors = {
            "pea": [34, 197, 94, 180],
            "potato": [234, 179, 8, 180],
            "carrot": [249, 115, 22, 180],
            "turnip_rape": [234, 88, 12, 180],
            "spinach": [16, 185, 129, 180],
        }
        merged["color"] = merged["crop"].map(lambda c: crop_colors.get(c, [100, 116, 139, 160]))
        merged["radius"] = merged["area_ha"].clip(1.0, 15.0) * 80  # radius proportional to area

        return merged

    def get_logistics_arcs(self, year: int = 2025, limit: int = 150) -> pd.DataFrame:
        """Generate representative inbound logistics delivery arcs to Säkylä & Kantvik."""
        parcels = pd.read_csv(self.parcels_path)
        sites = pd.read_csv(self.sites_path).set_index("site_id")

        sak_lat, sak_lon = sites.loc["S-SAK", "lat"], sites.loc["S-SAK", "lon"]
        kan_lat, kan_lon = sites.loc["S-KAN", "lat"], sites.loc["S-KAN", "lon"]

        # Sample contract farm parcels and build arcs to Säkylä / Kantvik
        sample_parcels = parcels.sample(n=min(limit, len(parcels)), random_state=42)
        arcs = []
        for _, r in sample_parcels.iterrows():
            # Route to Säkylä or Kantvik based on distance
            dist_sak = (r["lat"] - sak_lat) ** 2 + (r["lon"] - sak_lon) ** 2
            dist_kan = (r["lat"] - kan_lat) ** 2 + (r["lon"] - kan_lon) ** 2
            
            dest_lat, dest_lon, dest_name = (sak_lat, sak_lon, "Säkylä Plant") if dist_sak <= dist_kan else (kan_lat, kan_lon, "Kantvik Mill")
            
            arcs.append({
                "origin_name": f"Parcel {r['parcel_id']}",
                "from_lat": r["lat"],
                "from_lon": r["lon"],
                "to_lat": dest_lat,
                "to_lon": dest_lon,
                "dest_name": dest_name,
                "color": [16, 185, 129, 140] if dest_name == "Säkylä Plant" else [59, 130, 246, 140],
            })

        return pd.DataFrame(arcs)

    @staticmethod
    def fetch_live_weather(lat: float = 61.0787, lon: float = 22.2538) -> Dict[str, Any]:
        """Fetch real-time weather from Open-Meteo for specified coordinates."""
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&"
            f"current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,weather_code&"
            f"daily=temperature_2m_max,temperature_2m_min,precipitation_sum&"
            f"timezone=Europe%2FHelsinki"
        )
        try:
            resp = requests.get(url, timeout=4)
            if resp.status_code == 200:
                data = resp.json()
                curr = data.get("current", {})
                daily = data.get("daily", {})
                temp = curr.get("temperature_2m", 15.0)
                precip = curr.get("precipitation", 0.0)
                wind = curr.get("wind_speed_10m", 10.0)
                humidity = curr.get("relative_humidity_2m", 60)

                # Agronomic risk interpretation
                risk_status = "Optimal Field Conditions"
                risk_color = "normal"
                if temp <= 0:
                    risk_status = "⚠️ Active Frost Warning — Risk to tender shoots"
                    risk_color = "off"
                elif temp >= 27:
                    risk_status = "⚠️ Heat Stress Alert — Flowering abortion risk"
                    risk_color = "off"
                elif precip >= 15:
                    risk_status = "⚠️ Heavy Rainfall / Saturated Soil — Machinery compaction risk"
                    risk_color = "off"

                return {
                    "status": "online",
                    "time": curr.get("time"),
                    "temp_c": temp,
                    "humidity_pct": humidity,
                    "precip_mm": precip,
                    "wind_kmh": wind,
                    "agronomic_status": risk_status,
                    "daily_max": daily.get("temperature_2m_max", [temp])[0],
                    "daily_min": daily.get("temperature_2m_min", [temp])[0],
                    "forecast_days": len(daily.get("temperature_2m_max", [])),
                }
        except Exception as exc:
            pass

        # Fallback offline simulation if internet is temporarily unreachable
        return {
            "status": "cached_offline",
            "time": "Real-time feed simulated",
            "temp_c": 16.4,
            "humidity_pct": 72,
            "precip_mm": 0.0,
            "wind_kmh": 12.0,
            "agronomic_status": "Optimal Field Conditions",
            "daily_max": 18.5,
            "daily_min": 11.2,
            "forecast_days": 3,
        }

