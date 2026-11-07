"""
prototype/core/api.py — Unified Backend API for Apetit Climate & Nature Navigator
Single entry point providing clean, typed interfaces for all services.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from .biodiversity_service import BiodiversityService
from .copilot_service import CopilotService
from .digital_twin_service import DigitalTwinService
from .early_warning_service import EarlyWarningService
from .geo_service import GeoService
from .inventory_service import InventoryService
from .investment_optimizer_service import InvestmentOptimizerService
from .live_apis import LiveAPIsService
from .nature_service import NatureService
from .pathway_service import PathwayService
from .report_generator_service import ReportGeneratorService
from .risk_service import ClimateRiskService
from .simulator_service import SimulatorService
from .tradeoff_service import TradeoffService


class NavigatorAPI:
    def __init__(self, root: Optional[Path] = None):
        if root is None:
            # Default to APETIT_CLIMATE_NATURE_NAVIGATOR_2026 directory
            self.root = Path(__file__).resolve().parents[2] / "APETIT_CLIMATE_NATURE_NAVIGATOR_2026"
        else:
            self.root = Path(root)

        self.inventory = InventoryService(self.root)
        self.risk = ClimateRiskService(self.root)
        self.nature = NatureService(self.root)
        self.biodiversity = BiodiversityService(self.root)
        self.pathway = PathwayService(self.root)
        self.copilot = CopilotService(self.root)
        self.geo = GeoService(self.root)
        self.live = LiveAPIsService()
        self.simulator = SimulatorService(self.root)
        self.early_warning = EarlyWarningService(self.root)
        self.twin = DigitalTwinService(self.root)
        self.optimizer = InvestmentOptimizerService(self.root)
        self.reports = ReportGeneratorService(self.root)
        self.tradeoffs = TradeoffService(self.root)

    def get_executive_summary(self, year: int = 2025) -> Dict[str, Any]:
        """Aggregate cross-track metrics for the Executive Dashboard."""
        inv_kpis = self.inventory.get_kpis(year)
        pea_risk = self.risk.simulate_crop_yields(crop="pea", scenario="ssp245")
        nat_kpis = self.nature.get_catchment_kpis(year)
        pw_kpis = self.pathway.get_pathway_kpis()

        return {
            "year": year,
            "emissions_total_tco2e": inv_kpis["total_market"],
            "scope1_tco2e": inv_kpis["scope1"],
            "scope2_market_tco2e": inv_kpis["scope2_market"],
            "scope3_tco2e": inv_kpis["scope3"],
            "flag_emissions_share_pct": (inv_kpis["flag_emissions"] / inv_kpis["total_market"]) * 100.0,
            "pea_near_term_yield_delta_pct": pea_risk["near_term_delta_pct"],
            "pea_bad_year_prob": pea_risk["near_term_bad_prob"],
            "active_sourcing_catchments": nat_kpis["active_sourcing_catchments"],
            "top_nature_priority_catchment": nat_kpis["top_priority_catchment"],
            "buffer_strip_coverage_pct": nat_kpis["buffer_strip_coverage_pct"],
            "total_abatement_potential_tco2e": pw_kpis["total_abatement_tco2e"],
            "net_savings_levers_count": pw_kpis["net_savings_levers_count"],
        }

