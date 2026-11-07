"""
prototype/core/nature_service.py — SBTN Freshwater & Catchment Prioritization Service
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

STATE_WEIGHT = {"good": 1.0, "moderate": 1.2, "poor": 1.5, "bad": 1.8}
APETIT_CROPS = ["pea", "potato", "carrot", "spinach", "turnip_rape"]


class NatureService:
    def __init__(self, root: Path):
        self.root = root
        self.cat_path = root / "data" / "06_nature" / "catchments.csv"
        self.par_path = root / "data" / "01_master" / "parcels.csv"
        self.crop_path = root / "data" / "03_farming" / "parcel_crop_history_and_plan.csv"
        self.loads_path = root / "data" / "06_nature" / "monitored_catchment_loads.csv"
        self.dev_truth_path = root / "tasks" / "dev" / "D1_dev_catchments_2025.csv"

    def get_catchment_priorities(self, year: int = 2025) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Compute SBTN catchment priorities from contract field parcel data."""
        cat_df = pd.read_csv(self.cat_path)
        par_df = pd.read_csv(self.par_path)
        crop_df = pd.read_csv(self.crop_path)

        # Filter contract parcels for specified year
        crops_yr = crop_df[(crop_df["year"] == year) & (crop_df["crop"].isin(APETIT_CROPS))].copy()
        merged_par = crops_yr.merge(par_df, on="parcel_id", how="inner")

        # Aggregate area and parcel stats per catchment
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

        # SBTN Nutrient Delivery Calculation
        retention = c["nutrient_retention_frac_estimate"].fillna(0.2)
        p_load = c["contract_area_ha"] * 1.1 * (1.0 - retention)
        n_load = c["contract_area_ha"] * 15.0 * (1.0 - retention)

        c["apetit_p_to_water_kg"] = p_load.round(2)
        c["apetit_n_to_water_kg"] = n_load.round(1)

        # SBTN Priority Formula
        active = c[c["contract_area_ha"] > 0]
        med_p = max(active["apetit_p_to_water_kg"].median(), 1.0)
        med_n = max(active["apetit_n_to_water_kg"].median(), 1.0)

        st_weight = c["ecological_status_class"].map(STATE_WEIGHT).fillna(1.2)
        p_sens = c["p_sensitivity"].fillna(1.0)

        score = np.where(
            c["contract_area_ha"] > 0,
            (c["apetit_p_to_water_kg"] / med_p + 0.5 * (c["apetit_n_to_water_kg"] / med_n)) * st_weight * p_sens,
            0.0,
        )
        c["sbtn_priority_score"] = np.round(score, 3)
        c["priority_rank"] = c["sbtn_priority_score"].rank(ascending=False, method="min").astype(int)

        return c.sort_values("priority_rank").reset_index(drop=True), merged_par

    def get_catchment_kpis(self, year: int = 2025) -> Dict[str, Any]:
        c_df, _ = self.get_catchment_priorities(year)
        active = c_df[c_df["contract_area_ha"] > 0]
        return {
            "total_catchments": len(c_df),
            "active_sourcing_catchments": len(active),
            "total_contract_ha": float(active["contract_area_ha"].sum()),
            "total_p_kg": float(active["apetit_p_to_water_kg"].sum()),
            "total_n_kg": float(active["apetit_n_to_water_kg"].sum()),
            "buffer_strip_coverage_pct": float(active["buffer_strip_ha"].sum() / max(active["contract_area_ha"].sum(), 1.0) * 100.0),
            "top_priority_catchment": active.iloc[0]["catchment_id"] if not active.empty else "N/A",
        }

