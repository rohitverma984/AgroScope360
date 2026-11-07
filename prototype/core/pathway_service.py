"""
prototype/core/pathway_service.py — Decarbonisation Pathways, MACC, & Governance Service
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd


class PathwayService:
    def __init__(self, root: Path):
        self.root = root
        self.levers_path = root / "data" / "05_scenarios" / "decarbonisation_levers.csv"
        self.scenarios_path = root / "data" / "05_scenarios" / "transition_scenarios.csv"
        self.events_path = root / "data" / "05_scenarios" / "structural_events.csv"
        self.prices_path = root / "data" / "05_scenarios" / "contract_prices_and_replacement_premiums.csv"
        self._levers_df: pd.DataFrame | None = None
        self._scenarios_df: pd.DataFrame | None = None
        self._events_df: pd.DataFrame | None = None

    def _load(self):
        if self._levers_df is None:
            self._levers_df = pd.read_csv(self.levers_path)
        if self._scenarios_df is None:
            self._scenarios_df = pd.read_csv(self.scenarios_path)
        if self._events_df is None:
            self._events_df = pd.read_csv(self.events_path)

    def get_levers(self) -> pd.DataFrame:
        self._load()
        return self._levers_df.copy()

    def get_structural_events(self) -> pd.DataFrame:
        self._load()
        return self._events_df.copy()

    def get_transition_scenarios(self) -> pd.DataFrame:
        self._load()
        return self._scenarios_df.copy()

    def get_macc_table(self) -> pd.DataFrame:
        """Return cleaned levers ordered by marginal cost for MACC plotting."""
        df = self.get_levers()
        # Exclude measurement-only levers (e.g. L27) from physical abatement MACC
        macc = df[df["lever_id"] != "L27"].sort_values("indicative_cost_eur_per_tco2e").reset_index(drop=True)
        macc["cumulative_abatement"] = macc["abatement_tco2e_2030_design"].cumsum()
        return macc

    def get_pathway_kpis(self) -> Dict[str, Any]:
        df = self.get_levers()
        phys = df[df["lever_id"] != "L27"]
        total_abat = float(phys["abatement_tco2e_2030_design"].sum())
        flag_abat = float(phys[phys["flag"] == True]["abatement_tco2e_2030_design"].sum())
        cost_neg = phys[phys["indicative_cost_eur_per_tco2e"] < 0]

        return {
            "total_levers": len(df),
            "physical_levers": len(phys),
            "total_abatement_tco2e": total_abat,
            "flag_abatement_share_pct": (flag_abat / total_abat * 100.0) if total_abat > 0 else 0.0,
            "net_savings_levers_count": len(cost_neg),
            "net_savings_potential_tco2e": float(cost_neg["abatement_tco2e_2030_design"].sum()),
        }

