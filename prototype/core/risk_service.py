"""
prototype/core/risk_service.py — Deterministic Agronomic Climate Risk & Crop Yield Model
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

CROP_SPECS = {
    "pea": {
        "name": "Green Pea (Herne)",
        "months": [6, 7, 8],
        "beta_temp": 0.08,
        "beta_temp2": -0.025,
        "beta_precip": 0.003,
        "beta_hot": -0.15,
        "price_per_t": 380.0,
    },
    "potato": {
        "name": "Ware Potato (Peruna)",
        "months": [6, 7, 8, 9],
        "beta_temp": 0.25,
        "beta_temp2": -0.04,
        "beta_precip": 0.015,
        "beta_hot": -0.30,
        "price_per_t": 220.0,
    },
    "carrot": {
        "name": "Carrot (Porkkana)",
        "months": [6, 7, 8, 9],
        "beta_temp": 0.30,
        "beta_temp2": -0.035,
        "beta_precip": 0.020,
        "beta_hot": -0.25,
        "price_per_t": 260.0,
    },
    "turnip_rape": {
        "name": "Spring Oilseed / Turnip Rape (Rypsi)",
        "months": [5, 6, 7, 8],
        "beta_temp": 0.05,
        "beta_temp2": -0.015,
        "beta_precip": 0.002,
        "beta_hot": -0.08,
        "price_per_t": 480.0,
    },
}


class ClimateRiskService:
    def __init__(self, root: Path):
        self.root = root
        self.climate_path = root / "data" / "04_climate" / "weather_monthly_1991_2060.csv"
        self.survey_path = root / "data" / "03_farming" / "farm_survey_fi.csv"
        self._climate_df: pd.DataFrame | None = None
        self._survey_df: pd.DataFrame | None = None

    def _load(self):
        if self._climate_df is None:
            self._climate_df = pd.read_csv(self.climate_path)
        if self._survey_df is None:
            self._survey_df = pd.read_csv(self.survey_path)

    def get_supported_crops(self) -> Dict[str, str]:
        return {k: v["name"] for k, v in CROP_SPECS.items()}

    def get_crop_baseline_mean(self, crop: str) -> float:
        self._load()
        sv = self._survey_df[(self._survey_df["crop"] == crop) & (self._survey_df["year"].between(1991, 2020))]
        if not sv.empty:
            return float(sv["yield_t_ha"].median())
        return 3.0  # fallback reasonable agronomic default

    def simulate_crop_yields(
        self, crop: str = "pea", scenario: str = "ssp245"
    ) -> Dict[str, Any]:
        """Simulate historical vs future yields and climate risk indicators."""
        self._load()
        spec = CROP_SPECS.get(crop, CROP_SPECS["pea"])
        months = spec["months"]
        base_mean = self.get_crop_baseline_mean(crop)

        # Aggregate weather
        df = self._climate_df[self._climate_df["month"].isin(months)].copy()
        
        def calc_series(scen: str, y_start: int, y_end: int) -> pd.DataFrame:
            sub = df[(df["scenario"] == scen) & (df["year"].between(y_start, y_end))]
            agg = sub.groupby("year").agg(
                tmean=("tmean_c", "mean"),
                precip=("precip_mm", "sum"),
                hot_days=("hot_days_tmax_ge_27", "sum"),
            ).reset_index()

            # Deterministic empirical yield formula
            y_pred = (
                base_mean
                + spec["beta_temp"] * (agg["tmean"] - 15.5)
                + spec["beta_temp2"] * (agg["tmean"] - 15.5) ** 2
                + spec["beta_precip"] * (agg["precip"] - 180.0)
                + spec["beta_hot"] * agg["hot_days"]
            ).clip(lower=0.5)
            agg["yield_pred_t_ha"] = y_pred
            return agg

        hist = calc_series("historical", 1991, 2020)
        hist_mean = float(hist["yield_pred_t_ha"].mean())
        bad_threshold = hist_mean * 0.80

        near = calc_series(scenario, 2027, 2031)
        long_term = calc_series(scenario, 2041, 2060)

        near_mean = float(near["yield_pred_t_ha"].mean())
        long_mean = float(long_term["yield_pred_t_ha"].mean())

        near_bad_p = float((near["yield_pred_t_ha"] < bad_threshold).mean())
        long_bad_p = float((long_term["yield_pred_t_ha"] < bad_threshold).mean())

        # Financial risk sensitivity (€ / ha loss in bad years)
        price = spec["price_per_t"]
        loss_per_ha = max(0.0, (hist_mean - long_mean) * price)

        return {
            "crop": crop,
            "crop_name": spec["name"],
            "scenario": scenario,
            "baseline_mean_yield": hist_mean,
            "bad_year_threshold": bad_threshold,
            "near_term_mean": near_mean,
            "near_term_delta_pct": ((near_mean / hist_mean) - 1.0) * 100.0,
            "near_term_bad_prob": near_bad_p,
            "long_term_mean": long_mean,
            "long_term_delta_pct": ((long_mean / hist_mean) - 1.0) * 100.0,
            "long_term_bad_prob": long_bad_p,
            "indicative_price_eur_t": price,
            "expected_climate_delta_eur_ha": -loss_per_ha if loss_per_ha > 0 else (long_mean - hist_mean) * price,
            "historical_df": hist,
            "near_term_df": near,
            "long_term_df": long_term,
        }

