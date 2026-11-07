"""
prototype/core/digital_twin_service.py — Agricultural Farm Digital Twin Engine
Constructs a high-fidelity digital representation of contract farms combining:
- Geographic coordinates & parcel geometries
- Soil profile (clay %, organic peat, slope, drainage, distance to water)
- 10-year historical production & input survey
- Climate scenario sensitivity simulation
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd


class DigitalTwinService:
    def __init__(self, root: Path):
        self.root = root
        self.registry_path = root / "data" / "01_master" / "farm_registry.csv"
        self.parcels_path = root / "data" / "01_master" / "parcels.csv"
        self.survey_path = root / "data" / "03_farming" / "farm_survey_fi.csv"
        self.crop_path = root / "data" / "03_farming" / "parcel_crop_history_and_plan.csv"
        self._farms_df: Optional[pd.DataFrame] = None
        self._parcels_df: Optional[pd.DataFrame] = None
        self._survey_df: Optional[pd.DataFrame] = None

    def _load(self):
        if self._farms_df is None:
            self._farms_df = pd.read_csv(self.registry_path)
        if self._parcels_df is None:
            self._parcels_df = pd.read_csv(self.parcels_path)
        if self._survey_df is None:
            self._survey_df = pd.read_csv(self.survey_path)

    def get_farms_catalog(self) -> List[Dict[str, Any]]:
        """Return list of farms with summary statistics."""
        self._load()
        # Merge with parcel counts
        p_counts = self._parcels_df.groupby("farm_id").size().to_dict()
        p_area = self._parcels_df.groupby("farm_id")["area_ha"].sum().to_dict()

        catalog = []
        for _, r in self._farms_df.head(60).iterrows():
            fid = r["farm_id"]
            crop = r.get("contract_crops", "pea")
            if pd.isna(crop) or not crop:
                crop = "pea"
            
            catalog.append({
                "farm_id": fid,
                "label": f"{fid} — {crop.title()} ({p_counts.get(fid, 1)} parcels, {p_area.get(fid, 15.0):.1f} ha)",
                "primary_crop": crop,
                "lat": float(r["lat"]),
                "lon": float(r["lon"]),
                "parcels_count": p_counts.get(fid, 1),
                "total_area_ha": p_area.get(fid, 15.0),
                "organic_certified": bool(r.get("organic_certified", False)),
                "livestock": bool(r.get("livestock", False)),
            })
        return catalog

    def get_farm_details(self, farm_id: str) -> Dict[str, Any]:
        """Return comprehensive digital twin attributes for a specific farm."""
        self._load()
        farm_row = self._farms_df[self._farms_df["farm_id"] == farm_id]
        if farm_row.empty:
            farm_row = self._farms_df.iloc[0]
            farm_id = farm_row["farm_id"]
        else:
            farm_row = farm_row.iloc[0]

        # Field Parcels for this farm
        parcels = self._parcels_df[self._parcels_df["farm_id"] == farm_id].copy()
        
        # Historical survey
        survey = self._survey_df[self._survey_df["farm_id"] == farm_id].sort_values("year").copy()
        if survey.empty:
            # Fallback survey history
            survey = pd.DataFrame({
                "year": list(range(2016, 2027)),
                "crop": farm_row.get("contract_crops", "pea"),
                "yield_t_ha": [3.2 + np.sin(y)*0.4 for y in range(2016, 2027)],
                "n_mineral_kg_ha": [25.0] * 11,
                "p_kg_ha": [12.0] * 11,
                "irrigated": [False] * 11,
                "area_ha": [parcels["area_ha"].sum()] * 11,
            })

        # Calculate average soil characteristics
        avg_clay = float(parcels["clay_pct_soilmap"].mean()) if not parcels.empty else 45.0
        avg_slope = float(parcels["slope_pct"].mean()) if not parcels.empty else 1.8
        min_water_dist = float(parcels["dist_to_water_m"].min()) if not parcels.empty else 250.0
        buffer_coverage = float((parcels["buffer_strip"] == True).mean() * 100.0) if not parcels.empty else 0.0

        # Baseline metrics
        hist_mean_yield = float(survey["yield_t_ha"].median())
        last_fert_n = float(survey.iloc[-1].get("n_mineral_kg_ha", 25.0))
        last_fert_p = float(survey.iloc[-1].get("p_kg_ha", 12.0))
        is_irrigated = bool(survey.iloc[-1].get("irrigated", False))

        return {
            "farm_id": farm_id,
            "crop": farm_row.get("contract_crops", "pea"),
            "lat": float(farm_row["lat"]),
            "lon": float(farm_row["lon"]),
            "organic_certified": bool(farm_row.get("organic_certified", False)),
            "livestock": bool(farm_row.get("livestock", False)),
            "parcels": parcels,
            "survey": survey,
            "stats": {
                "total_area_ha": float(parcels["area_ha"].sum()),
                "parcels_count": len(parcels),
                "avg_clay_pct": avg_clay,
                "avg_slope_pct": avg_slope,
                "min_water_dist_m": min_water_dist,
                "buffer_strip_coverage_pct": buffer_coverage,
                "baseline_mean_yield_t_ha": hist_mean_yield,
                "baseline_n_fert_kg_ha": last_fert_n,
                "baseline_p_fert_kg_ha": last_fert_p,
                "is_irrigated": is_irrigated,
            },
        }

    def simulate_digital_twin(
        self,
        farm_id: str,
        delta_temp_c: float = 2.0,           # e.g. +2.0 °C
        delta_precip_pct: float = -20.0,     # e.g. -20% summer rain
        upgrade_irrigation: bool = False,
        switch_drought_cultivar: bool = False,
        apply_catch_crops: bool = True,
        install_buffer_strips: bool = True,
    ) -> Dict[str, Any]:
        """Simulate farm-specific response to climate scenarios and management adaptations."""
        details = self.get_farm_details(farm_id)
        stats = details["stats"]
        crop = details["crop"]
        base_yield = stats["baseline_mean_yield_t_ha"]

        # Agronomic response function:
        # Temperature effect
        temp_effect = (0.06 * delta_temp_c) - (0.04 * (delta_temp_c ** 2))
        
        # Drought penalty (moisture deficit)
        precip_penalty = (delta_precip_pct / 100.0) * 0.45   # -20% rain -> ~9% yield penalty
        
        # Mitigation offsets
        mitigation_offset = 0.0
        if upgrade_irrigation:
            mitigation_offset += 0.12   # Irrigation eliminates drought penalty
        if switch_drought_cultivar:
            mitigation_offset += 0.08   # Resilient root system protects yield
        if apply_catch_crops:
            mitigation_offset += 0.04   # Soil organic matter improves moisture holding

        total_yield_mult = max(0.4, 1.0 + temp_effect + precip_penalty + mitigation_offset)
        sim_yield = base_yield * total_yield_mult
        yield_delta_pct = ((sim_yield / base_yield) - 1.0) * 100.0

        # Water requirement:
        # Warmer temperature + drought increases evapotranspiration (PET)
        base_water_m3_ha = 180.0 if stats["is_irrigated"] else 40.0
        water_mult = 1.0 + (delta_temp_c * 0.08) - (delta_precip_pct * 0.01)
        if upgrade_irrigation:
            water_mult *= 1.35  # Active irrigation withdrawal
        sim_water_m3_ha = base_water_m3_ha * water_mult

        # Nutrient Runoff to water (P to water):
        # Slope and buffer strip directly determine nutrient loss
        base_p_loss_kg = stats["total_area_ha"] * 1.1 * (stats["avg_slope_pct"] / 2.0)
        p_loss_mult = 1.0
        if install_buffer_strips:
            p_loss_mult *= 0.55  # 45% reduction from riparian buffer strips
        if apply_catch_crops:
            p_loss_mult *= 0.85
        sim_p_loss_kg = base_p_loss_kg * p_loss_mult

        # Financial exposure (€ per farm):
        price_per_t = 380.0 if "pea" in crop else (220.0 if "potato" in crop else 300.0)
        crop_value_delta = (sim_yield - base_yield) * stats["total_area_ha"] * price_per_t
        
        # Implementation cost of interventions:
        intervention_cost = 0.0
        if upgrade_irrigation:
            intervention_cost += 120.0 * stats["total_area_ha"]
        if switch_drought_cultivar:
            intervention_cost += 35.0 * stats["total_area_ha"]
        if apply_catch_crops:
            intervention_cost += 40.0 * stats["total_area_ha"]

        net_margin_delta = crop_value_delta - intervention_cost

        # AI Agronomic Advisor Synthesis
        advisor_notes = (
            f"**Farm Digital Twin Assessment for {farm_id} ({crop.title()}):**\\n"
            f"• **Climate Stress:** A +{delta_temp_c:.1f}°C warming combined with {delta_precip_pct:+.0f}% summer rainfall "
            f"threatens an unmitigated **{abs(precip_penalty)*100:.1f}% yield dip** during flowering/tuber bulking.\\n"
            f"• **Field Vulnerability:** Farm operates {stats['parcels_count']} parcels with average clay {stats['avg_clay_pct']:.0f}% "
            f"and slope {stats['avg_slope_pct']:.1f}%. Closest drainage ditch is only {stats['min_water_dist_m']:.0f}m away.\\n"
            f"• **Selected Response Impact:** With {'precision irrigation' if upgrade_irrigation else 'current management'} and "
            f"{'catch crops' if apply_catch_crops else 'standard rotation'}, harvest yield is protected to **{sim_yield:.2f} t/ha ({yield_delta_pct:+.1f}%)**.\\n"
            f"• **Freshwater Stewardship:** Phosphorus runoff to receiving waters is reduced by **{((1.0 - p_loss_mult)*100):.1f}%** "
            f"({sim_p_loss_kg:.1f} kg P vs baseline {base_p_loss_kg:.1f} kg P)."
        )

        return {
            "farm_id": farm_id,
            "crop": crop,
            "stats": stats,
            "sim_yield_t_ha": sim_yield,
            "yield_delta_pct": yield_delta_pct,
            "base_yield_t_ha": base_yield,
            "sim_water_m3_ha": sim_water_m3_ha,
            "water_delta_pct": ((sim_water_m3_ha / base_water_m3_ha) - 1.0) * 100.0,
            "sim_p_loss_kg": sim_p_loss_kg,
            "p_loss_delta_pct": ((sim_p_loss_kg / base_p_loss_kg) - 1.0) * 100.0,
            "crop_value_delta_eur": crop_value_delta,
            "net_margin_delta_eur": net_margin_delta,
            "advisor_notes": advisor_notes,
        }

