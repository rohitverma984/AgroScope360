"""
prototype/core/biodiversity_service.py — Biodiversity & Nature Hotspot Engine
Provides geospatial analytics and ENCORE/SBTN environmental dependencies & impacts:
- Contract farm spatial coordinates & proximity to waterbodies
- Lake Pyhäjärvi & river network polygons / lines
- Natura 2000 & Finnish protected area reserves
- Key Biodiversity Areas (KBAs) & fragile peatland habitats
- Catchment eutrophication & water stress indices
- Real-time environmental impact & dependency reasoning
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd


class BiodiversityService:
    def __init__(self, root: Path):
        self.root = root
        self.farms_path = root / "data" / "01_master" / "farm_registry.csv"
        self.parcels_path = root / "data" / "01_master" / "parcels.csv"
        self.catchments_path = root / "data" / "06_nature" / "catchments.csv"
        self.catchments_geojson_path = root / "data" / "06_nature" / "catchments.geojson"
        self.nature_ind_path = root / "data" / "06_nature" / "origin_state_of_nature_indicative.csv"

        self._cached_farms: Optional[pd.DataFrame] = None
        self._cached_catchments_gj: Optional[Dict[str, Any]] = None

    def _load_data(self):
        if self._cached_farms is None:
            farms = pd.read_csv(self.farms_path)
            parcels = pd.read_csv(self.parcels_path)

            p_summary = parcels.groupby("farm_id").agg(
                total_area_ha=("area_ha", "sum"),
                parcels_count=("parcel_id", "count"),
                min_dist_water_m=("dist_to_water_m", "min"),
                avg_slope_pct=("slope_pct", "mean"),
                avg_clay_pct=("clay_pct_soilmap", "mean"),
                buffer_coverage_pct=("buffer_strip", lambda s: float((s == True).mean() * 100.0)),
                catchment_id=("catchment_id", "first"),
            ).reset_index()

            self._cached_farms = farms.merge(p_summary, on="farm_id", how="left").fillna({
                "total_area_ha": 25.0,
                "parcels_count": 1,
                "min_dist_water_m": 250.0,
                "avg_slope_pct": 2.0,
                "avg_clay_pct": 40.0,
                "buffer_coverage_pct": 0.0,
                "catchment_id": "CA01",
            })

    # ── 1. Catchments with SBTN Nature Indicators ────────────────────────────
    def get_catchments_geojson(self) -> Dict[str, Any]:
        """Load 42 SBTN catchment polygons enriched with ecological and water-stress metrics."""
        with open(self.catchments_geojson_path, "r", encoding="utf-8") as f:
            gj = json.load(f)

        c_meta = pd.read_csv(self.catchments_path).set_index("catchment_id").to_dict(orient="index")

        for feat in gj["features"]:
            cid = feat["properties"]["catchment_id"]
            meta = c_meta.get(cid, {})
            status = meta.get("ecological_status_class", "moderate")
            p_sens = float(meta.get("p_sensitivity", 1.0))

            # Color coding by SBTN water stress & eutrophication vulnerability
            if status in ["poor", "bad"] or p_sens >= 1.4:
                risk_level = "High Eutrophication Risk"
                color = "#ef4444"  # Red
                fill_color = "rgba(239, 68, 68, 0.40)"
            elif status == "moderate" or p_sens >= 1.15:
                risk_level = "Moderate Eutrophication Risk"
                color = "#f59e0b"  # Amber
                fill_color = "rgba(245, 158, 11, 0.35)"
            else:
                risk_level = "Good / Resilient Status"
                color = "#10b981"  # Emerald
                fill_color = "rgba(16, 185, 129, 0.30)"

            feat["properties"].update({
                "ecological_status": status.title(),
                "p_sensitivity": p_sens,
                "receiving_water_type": str(meta.get("receiving_water_type", "river")).title(),
                "catchment_area_km2": float(meta.get("catchment_area_km2", 200.0)),
                "field_area_total_ha": float(meta.get("field_area_total_ha", 4500.0)),
                "risk_level": risk_level,
                "stroke_color": color,
                "fill_color": fill_color,
            })
        return gj

    # ── 2. Contract Farm Hotspots ────────────────────────────────────────────
    def get_farms_geojson(self, max_farms: int = 150) -> Dict[str, Any]:
        """Convert contract farms into GeoJSON point features with environmental impact attributes."""
        self._load_data()
        features = []

        for _, r in self._cached_farms.head(max_farms).iterrows():
            fid = r["farm_id"]
            dist_w = float(r["min_dist_water_m"])
            buf_cov = float(r["buffer_coverage_pct"])
            crop = str(r.get("contract_crops", "pea")).title()

            # Determine eutrophication impact rating
            if dist_w < 80 and buf_cov < 30:
                eco_risk = "Severe Nutrient Runoff Risk"
                pin_color = "#ef4444"
            elif dist_w < 200 or buf_cov < 50:
                eco_risk = "Moderate Eutrophication Risk"
                pin_color = "#f59e0b"
            else:
                eco_risk = "Well-Buffered / Low Impact"
                pin_color = "#10b981"

            # Environmental dependency statement
            dependency_statement = (
                f"This farm ({fid}) is located within {dist_w:.0f}m of receiving drainage waters "
                f"(Catchment {r['catchment_id']}). "
                f"Increased fertiliser nitrogen and phosphorus runoff directly contributes to freshwater eutrophication "
                f"and cyanobacterial algae blooms in downstream Lake Pyhäjärvi / Eurajoki. "
                f"Buffer strip coverage is currently {buf_cov:.0f}%. "
                f"{'Recommended: install 10m riparian grass buffer strips and precision N-fertilisation.' if buf_cov < 60 else 'Good buffer strip stewardship active.'}"
            )

            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(r["lon"]), float(r["lat"])],
                },
                "properties": {
                    "farm_id": fid,
                    "crop": crop,
                    "total_area_ha": round(float(r["total_area_ha"]), 1),
                    "min_dist_water_m": int(dist_w),
                    "buffer_coverage_pct": round(buf_cov, 1),
                    "catchment_id": r["catchment_id"],
                    "organic": bool(r.get("organic_certified", False)),
                    "eco_risk": eco_risk,
                    "pin_color": pin_color,
                    "impact_statement": dependency_statement,
                },
            })

        return {"type": "FeatureCollection", "features": features}

    # ── 3. Major Finnish Water Bodies ────────────────────────────────────────
    def get_water_bodies_geojson(self) -> Dict[str, Any]:
        """Return GeoJSON polygons & linestrings for key waterbodies in Apetit's sourcing shed."""
        features = [
            # Lake Pyhäjärvi (Main oligotrophic/mesotrophic lake beside Säkylä)
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [22.18, 61.05], [22.25, 61.08], [22.36, 61.07],
                        [22.38, 61.02], [22.34, 60.95], [22.28, 60.91],
                        [22.20, 60.93], [22.16, 61.00], [22.18, 61.05]
                    ]],
                },
                "properties": {
                    "name": "Lake Pyhäjärvi (Säkylä)",
                    "type": "Sensitive Mesotrophic Freshwater Lake",
                    "area_km2": 155.0,
                    "status": "Good / Vulnerable to Phosphorus Loading",
                    "color": "#0284c7",
                    "fill": "rgba(2, 132, 199, 0.55)",
                    "dependency": "Primary source for Säkylä vegetable washing & cooling. High vulnerability to agricultural P-runoff causing summer blue-green algae.",
                },
            },
            # Lake Köyliönjärvi
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [22.32, 61.16], [22.37, 61.15], [22.36, 61.09],
                        [22.31, 61.10], [22.32, 61.16]
                    ]],
                },
                "properties": {
                    "name": "Lake Köyliönjärvi",
                    "type": "Cultural Landscape Shallow Lake",
                    "area_km2": 12.5,
                    "status": "Satisfactory / Nutrient Saturated",
                    "color": "#0369a1",
                    "fill": "rgba(3, 105, 161, 0.50)",
                    "dependency": "High agricultural density in watershed. Strict municipal limits on summer phosphorus discharge.",
                },
            },
            # Eurajoki River Corridor
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [22.21, 61.05], [22.18, 61.09], [22.13, 61.13],
                        [22.05, 61.17], [21.90, 61.20], [21.65, 61.22]
                    ],
                },
                "properties": {
                    "name": "Eurajoki River Salmonid Migration Channel",
                    "type": "River Discharge Corridor to Bothnian Sea",
                    "length_km": 53.0,
                    "status": "Moderate Ecological Status",
                    "color": "#0ea5e9",
                    "fill": "rgba(14, 165, 233, 0.9)",
                    "dependency": "Critical salmon and trout migratory river. High vulnerability to agricultural sediment siltation.",
                },
            },
            # Loimijoki River Channel
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [22.85, 60.85], [22.75, 60.92], [22.65, 61.02], [22.45, 61.15]
                    ],
                },
                "properties": {
                    "name": "Loimijoki Clay-Plain River",
                    "type": "Intensive Agricultural Drainage River",
                    "length_km": 114.0,
                    "status": "Poor Ecological Status (High Clay Silt & Turbidity)",
                    "color": "#0284c7",
                    "fill": "rgba(2, 132, 199, 0.9)",
                    "dependency": "Highest clay turbidity in Finland. Demands 100% winter catch crop coverage to reduce erosion.",
                },
            },
        ]
        return {"type": "FeatureCollection", "features": features}

    # ── 4. Protected Areas & Natura 2000 Sites ───────────────────────────────
    def get_protected_areas_geojson(self) -> Dict[str, Any]:
        """Return Natura 2000 conservation sites and National Parks in the sourcing basin."""
        features = [
            # Kurjenrahka National Park
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [22.34, 60.75], [22.46, 60.76], [22.47, 60.71],
                        [22.36, 60.70], [22.34, 60.75]
                    ]],
                },
                "properties": {
                    "name": "Kurjenrahka National Park (Natura 2000)",
                    "code": "FI0200062",
                    "designation": "National Park & Ramsar Peatland",
                    "area_km2": 29.0,
                    "color": "#16a34a",
                    "fill": "rgba(22, 163, 74, 0.40)",
                    "values": "Pristine ombrotrophic raised bogs, breeding habitat for cranes, whooper swans, and Eurasian eagle-owl.",
                },
            },
            # Torronsuo National Park
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [23.58, 60.74], [23.68, 60.75], [23.69, 60.71],
                        [23.60, 60.70], [23.58, 60.74]
                    ]],
                },
                "properties": {
                    "name": "Torronsuo Mire Complex (Natura 2000)",
                    "code": "FI0304001",
                    "designation": "National Park & Wetland of International Importance",
                    "area_km2": 25.5,
                    "color": "#15803d",
                    "fill": "rgba(21, 128, 61, 0.40)",
                    "values": "Deepest peat layer in Southern Finland (12m). Crucial autumn staging ground for thousands of migratory cranes.",
                },
            },
            # Pyhäjärvi Shoreline & Islets Special Area of Conservation (SAC)
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [22.22, 61.02], [22.30, 61.04], [22.32, 60.99],
                        [22.25, 60.96], [22.22, 61.02]
                    ]],
                },
                "properties": {
                    "name": "Pyhäjärvi Shoreline & Islets SAC",
                    "code": "FI0200084",
                    "designation": "Natura 2000 Special Area of Conservation",
                    "area_km2": 18.2,
                    "color": "#10b981",
                    "fill": "rgba(16, 185, 129, 0.42)",
                    "values": "Habitat for rare aquatic macrophytes (Isoëtes lacustris, Lobelia dortmanna) sensitive to nutrient enrichment.",
                },
            },
            # Säkylänharju Glacial Esker Nature Reserve
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [22.48, 61.05], [22.56, 61.03], [22.54, 60.98],
                        [22.46, 61.00], [22.48, 61.05]
                    ]],
                },
                "properties": {
                    "name": "Säkylänharju Glacial Esker & Peat Reserve",
                    "code": "FI0200078",
                    "designation": "Natura 2000 Esker Forest & Groundwater Protection Area",
                    "area_km2": 21.0,
                    "color": "#059669",
                    "fill": "rgba(5, 150, 105, 0.40)",
                    "values": "Critical groundwater recharge aquifer supplying municipal drinking water. Endemic dry pine heath flora.",
                },
            },
        ]
        return {"type": "FeatureCollection", "features": features}

    # ── 5. Land Cover Habitat Breakdown (Matching Donut Photo) ───────────────
    def get_habitat_breakdown(self, catchment_id: str = "CA01") -> Dict[str, Any]:
        """Return land cover / habitat distribution percentages within the sourcing shed."""
        # Realistic CORINE Land Cover breakdown for Southwest Finnish agricultural basin
        habitats = [
            {"label": "Cropland, rainfed", "pct": 42.0, "color": "#facc15", "desc": "Annual field crops (pea, potato, carrot, cereals)"},
            {"label": "Mosaic natural vegetation & cropland", "pct": 18.0, "color": "#a3e635", "desc": "Mixed field borders, pastures, and small farm groves"},
            {"label": "Tree cover, needleleaved evergreen (spruce/pine)", "pct": 22.0, "color": "#15803d", "desc": "Boreal conifer forest buffering streams"},
            {"label": "Tree cover, broadleaved deciduous (birch/alder)", "pct": 8.0, "color": "#4ade80", "desc": "Riparian bank woodland corridors"},
            {"label": "Water bodies & lakes", "pct": 6.0, "color": "#0284c7", "desc": "Freshwater lakes (Pyhäjärvi) and rivers"},
            {"label": "Wetland bogs & shrubland", "pct": 4.0, "color": "#b45309", "desc": "Peatland mires with high carbon storage"},
        ]
        return {
            "catchment_id": catchment_id,
            "total_area_km2": 615.0,
            "habitats": habitats,
        }

    # ── 6. Environmental Dependency & Impact Reasoning Engine ────────────────
    def assess_target(self, target_type: str, target_id: str) -> Dict[str, Any]:
        """Generate tailored ENCORE / SBTN impact and dependency assessment."""
        self._load_data()

        if target_type == "farm":
            farm_row = self._cached_farms[self._cached_farms["farm_id"] == target_id]
            if farm_row.empty:
                farm_row = self._cached_farms.iloc[0]
                target_id = farm_row["farm_id"]
            else:
                farm_row = farm_row.iloc[0]

            dist_w = float(farm_row["min_dist_water_m"])
            buf_cov = float(farm_row["buffer_coverage_pct"])
            crop = str(farm_row.get("contract_crops", "pea")).title()
            cid = farm_row["catchment_id"]

            return {
                "type": "Contract Farm",
                "id": target_id,
                "title": f"Farm {target_id} ({crop})",
                "catchment": f"Catchment {cid}",
                "proximity_water": f"{dist_w:.0f} meters",
                "buffer_coverage": f"{buf_cov:.0f}%",
                "ecosystem_dependency": (
                    "• **Surface Freshwater Withdrawal:** Relies on local drainage water availability for supplemental irrigation.\n"
                    "• **Natural Pollination:** Adjacent forest fringes support wild bumblebee and solitary bee populations crucial for pea pod set.\n"
                    "• **Soil Structural Quality:** Relies on stable organic matter to prevent topsoil compaction during heavy spring rains."
                ),
                "potential_impact": (
                    f"• **Phosphorus Eutrophication:** Located only {dist_w:.0f}m from water ditch. "
                    f"High seasonal fertiliser runoff can discharge dissolved phosphorus directly into the receiving catchment.\n"
                    f"• **Algal Bloom Pressure:** Contributes to summer cyanobacteria blooms in downstream Lake Pyhäjärvi if unmitigated.\n"
                    f"• **Sediment Runoff:** Field slope ({farm_row['avg_slope_pct']:.1f}%) increases particulate phosphorus loss during autumn rains."
                ),
                "recommended_action": (
                    f"1. Mandatory installation of a **10m permanent grass/shrub riparian buffer strip** along the drainage boundary.\n"
                    f"2. Transition to **precision variable-rate N-fertilisation**.\n"
                    f"3. Plant **winter catch crops (oil radish / ryegrass)** to hold residual nitrogen over winter."
                ),
                "eutrophication_risk": "High" if dist_w < 100 and buf_cov < 40 else ("Moderate" if dist_w < 250 else "Low"),
            }

        else:
            # Water body / Protected area assessment
            return {
                "type": "Water Ecosystem",
                "id": "Lake Pyhäjärvi",
                "title": "Lake Pyhäjärvi & Eurajoki River Basin",
                "catchment": "Catchment CA01",
                "proximity_water": "Adjacent to 180+ contract field parcels",
                "buffer_coverage": "38% average buffer strip coverage across watershed",
                "ecosystem_dependency": (
                    "• **Municipal & Food Processing Water Supply:** Supplies 100% of potable and process water for Apetit Säkylä.\n"
                    "• **Commercial Freshwater Fishery:** Supports Finland's most productive inland vendace (Coregonus albula) fishery.\n"
                    "• **Hydrological Regulation:** Regulates downstream flood mitigation along the Eurajoki corridor."
                ),
                "potential_impact": (
                    "• **Cyanobacteria Toxicity:** Sensitive to external phosphorus loads above 45 kg P/day, which trigger toxic Anabaena blooms.\n"
                    "• **Hypoxia in Deep Water:** Decomposition of autumn algae depletes benthic oxygen, threatening salmonid spawning beds.\n"
                    "• **Biodiversity Degradation:** Siltation chokes sensitive macrophyte beds protected under Natura 2000 (FI0200084)."
                ),
                "recommended_action": (
                    "1. Priority catchment designation for Apetit SBTN freshwater reduction targets.\n"
                    "2. 100% contract farm buffer strip compliance within 200m of lake tributaries.\n"
                    "3. Cooperative wetland construction with the Pyhäjärvi Protection Institute (Pyhäjärvi-instituutti)."
                ),
                "eutrophication_risk": "Critical Monitoring Zone",
            }

