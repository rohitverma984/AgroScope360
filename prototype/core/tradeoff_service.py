"""
prototype/core/tradeoff_service.py — AI Trade-off Intelligence Engine
Analyzes multi-objective interconnected environmental and business trade-offs.
Identifies unintended consequences where improving one metric negatively impacts another:
- Water efficiency vs energy pumping demand
- Fertiliser reduction vs equipment investment & advisory load
- Drought-resilient varieties vs seed costs & texture validation
- Peatland protection vs farmer relations & alternative land yields
- Cold storage temperature adjustment vs food-safety customer alignment
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd


class TradeoffService:
    def __init__(self, root: Path):
        self.root = root
        self.levers_path = root / "data" / "05_scenarios" / "decarbonisation_levers.csv"
        self._actions_catalog: Optional[Dict[str, Dict[str, Any]]] = None

    def _init_catalog(self) -> Dict[str, Dict[str, Any]]:
        if self._actions_catalog is not None:
            return self._actions_catalog

        # Catalog of interconnected actions with deterministic data & trade-off models
        self._actions_catalog = {
            "irrigation_efficiency": {
                "id": "irrigation_efficiency",
                "title": "Improve Irrigation Efficiency",
                "category": "Water & Crop Resilience",
                "target_scope": "Contract Farming Sourcing Shed",
                "primary_metric": "Water use",
                "primary_value": "−20%",
                "primary_note": "Illustrative improvement",
                "primary_color": "#0284c7",
                "co_benefit_metric": "Crop resilience",
                "co_benefit_value": "Improved",
                "co_benefit_note": "Potential benefit during summer flowering",
                "co_benefit_color": "#059669",
                "investment_metric": "Investment",
                "investment_value": "€15,000",
                "investment_note": "Micro-drip & soil sensor retrofit per cluster",
                "investment_color": "#0f172a",
                "trade_off_metric": "Energy use",
                "trade_off_value": "Could increase pumping demand (+12% kWh)",
                "trade_off_color": "#ea580c",
                "trade_off_severity": "Moderate",
                "ai_conclusion": (
                    "Evaluate water savings against additional energy demand and investment costs before implementation. "
                    "In sandy-loam soils (Catchment CA01), the +18% drought yield protection easily outweighs the localized pumping power cost. "
                    "Recommendation: Pair with on-farm solar PV micro-arrays to neutralize the additional electricity demand."
                ),
                "scores": {
                    "Carbon Abatement": 65,
                    "Water Conservation": 92,
                    "Soil & Biodiversity": 78,
                    "Cost Efficiency": 80,
                    "Operational Feasibility": 62,
                },
                "mitigation_playbook": "Deploy smart pressure sensors and solar-assisted pump controllers to cap grid electricity draw during peak tariff hours.",
            },
            "precision_fertiliser": {
                "id": "precision_fertiliser",
                "title": "Precision N-Fertiliser & Variable-Rate Spreading (L09)",
                "category": "FLAG Agriculture & Eutrophication",
                "target_scope": "Contract Pea, Carrot & Grain Parcels",
                "primary_metric": "N₂O Emissions",
                "primary_value": "−22%",
                "primary_note": "900 tCO₂e/yr direct greenhouse gas reduction",
                "primary_color": "#059669",
                "co_benefit_metric": "Lake Pyhäjärvi P/N Leaching",
                "co_benefit_value": "−18 kg N/ha",
                "co_benefit_note": "Cuts toxic cyanobacteria algae bloom risk",
                "co_benefit_color": "#0284c7",
                "investment_metric": "Investment",
                "investment_value": "€28,000",
                "investment_note": "GPS tractor guidance & annual satellite soil scans",
                "investment_color": "#0f172a",
                "trade_off_metric": "Advisory Capacity & Agronomic Labor",
                "trade_off_value": "Requires intensive grower training & digital adoption",
                "trade_off_color": "#ea580c",
                "trade_off_severity": "Moderate",
                "ai_conclusion": (
                    "Emissions and nutrient run-off reductions are high, but program success depends on farmer technical adoption. "
                    "Without agronomic training, equipment misuse can cause localized nitrogen under-application and yield drags. "
                    "Recommendation: Structure contractor incentives with guaranteed yield insurance during the first two harvest cycles."
                ),
                "scores": {
                    "Carbon Abatement": 82,
                    "Water Conservation": 88,
                    "Soil & Biodiversity": 85,
                    "Cost Efficiency": 84,
                    "Operational Feasibility": 58,
                },
                "mitigation_playbook": "Partner with ProAgria and Luke advisors to deliver centralized prescription maps directly to tractor onboard consoles.",
            },
            "drought_crop_varieties": {
                "id": "drought_crop_varieties",
                "title": "Drought-Resilient Pea Cultivars",
                "category": "Agronomic Climate Adaptation",
                "target_scope": "Contract Vegetable Growers (FI-SAK & SE-BJU)",
                "primary_metric": "Drought Yield Stability",
                "primary_value": "+18%",
                "primary_note": "Maintains 3.4 t/ha yield during 25°C+ heatwaves",
                "primary_color": "#059669",
                "co_benefit_metric": "Supply Security",
                "co_benefit_value": "High",
                "co_benefit_note": "Prevents factory downtime at Säkylä processing plant",
                "co_benefit_color": "#0284c7",
                "investment_metric": "Investment",
                "investment_value": "€12,500",
                "investment_note": "Certified seed breeding premium & trial plots",
                "investment_color": "#0f172a",
                "trade_off_metric": "Processing Texture & Seed Unit Cost",
                "trade_off_value": "Seed price +14%; requires Säkylä tenderometer validation",
                "trade_off_color": "#ea580c",
                "trade_off_severity": "Moderate-High",
                "ai_conclusion": (
                    "Cultivar switching protects production volume against CMIP6 climate shifts, but altered pea skin thickness "
                    "can impact freezing texture and tenderometer readings. "
                    "Recommendation: Run parallel pilot blenders in factory lines to verify consumer mouthfeel before mandatory group rollout."
                ),
                "scores": {
                    "Carbon Abatement": 55,
                    "Water Conservation": 80,
                    "Soil & Biodiversity": 70,
                    "Cost Efficiency": 74,
                    "Operational Feasibility": 65,
                },
                "mitigation_playbook": "Co-finance seed premiums with Nordic seed breeders and establish strict tenderometer acceptance bands for factory grading.",
            },
            "shift_peat_soils": {
                "id": "shift_peat_soils",
                "title": "Shift Contract Acreage Away from Drained Peat Soils (L11)",
                "category": "FLAG Deep Decarbonisation",
                "target_scope": "14 Organic Soil Farms in Catchment CA04/CA07",
                "primary_metric": "FLAG Soil Emissions",
                "primary_value": "−8,500 tCO₂e",
                "primary_note": "Eliminates 29.0 tCO₂/ha/yr peat oxidation",
                "primary_color": "#059669",
                "co_benefit_metric": "River Siltation & Biodiversity",
                "co_benefit_value": "Major Improvement",
                "co_benefit_note": "Halts acidic runoff into Eurajoki salmon spawning grounds",
                "co_benefit_color": "#0284c7",
                "investment_metric": "Investment",
                "investment_value": "€750,000",
                "investment_note": "Long-term land swap contracts & transition subsidies",
                "investment_color": "#0f172a",
                "trade_off_metric": "Grower Relations & Mineral Yield Drag",
                "trade_off_value": "Risk of contractor churn; mineral soils yield -8% lower peas",
                "trade_off_color": "#ef4444",
                "trade_off_severity": "Severe",
                "ai_conclusion": (
                    "Delivers the largest single carbon abatement on the platform (8,500 tCO₂e/yr), but presents substantial social "
                    "and operational friction. Contract farmers rely on peat for high root-crop yields. "
                    "Recommendation: Phase across 5 years with multi-year premium price top-ups on mineral plots to preserve farmer loyalty."
                ),
                "scores": {
                    "Carbon Abatement": 98,
                    "Water Conservation": 90,
                    "Soil & Biodiversity": 95,
                    "Cost Efficiency": 88,
                    "Operational Feasibility": 40,
                },
                "mitigation_playbook": "Implement a phased 5-year acreage swap framework coupled with CAP subsidy top-ups for paludiculture on retired peat parcels.",
            },
            "biogas_boiler_conversion": {
                "id": "biogas_boiler_conversion",
                "title": "Secure Biogas Supply to Eliminate Säkylä Backup LNG/LPG (L01)",
                "category": "Scope 1 Operational Decarbonisation",
                "target_scope": "Säkylä Processing Facility (FI-SAK)",
                "primary_metric": "Scope 1 Emissions",
                "primary_value": "−1,650 tCO₂e",
                "primary_note": "Eliminates fossil fuel combustion in peak winter",
                "primary_color": "#059669",
                "co_benefit_metric": "Local Air Quality",
                "co_benefit_value": "Zero SOx/PM",
                "co_benefit_note": "Complies with stringent municipal clean air standards",
                "co_benefit_color": "#0284c7",
                "investment_metric": "Investment",
                "investment_value": "€180,000",
                "investment_note": "Burner dual-fuel retrofit & connection valves",
                "investment_color": "#0f172a",
                "trade_off_metric": "Fuel Cost Premium & Supply Volatility",
                "trade_off_value": "Biogas price premium (+€18/MWh vs fossil natural gas)",
                "trade_off_color": "#ea580c",
                "trade_off_severity": "Moderate",
                "ai_conclusion": (
                    "Directly eliminates the Scope 1 increase seen during 2023–2024, but introduces exposure to regional biomethane spot price spikes. "
                    "Recommendation: Negotiate a 5-year fixed-index PPA with regional agricultural biogas plants (e.g. Suomen Biovoima) to cap OPEX volatility."
                ),
                "scores": {
                    "Carbon Abatement": 90,
                    "Water Conservation": 50,
                    "Soil & Biodiversity": 60,
                    "Cost Efficiency": 78,
                    "Operational Feasibility": 85,
                },
                "mitigation_playbook": "Execute long-term biomethane offtake agreements indexed to agricultural residues rather than generic fossil gas hubs.",
            },
            "cold_chain_temp_optimization": {
                "id": "cold_chain_temp_optimization",
                "title": "Optimize Frozen Storage Temperature (−18°C to −15°C) (L22)",
                "category": "Scope 1 & 2 Energy Efficiency",
                "target_scope": "Säkylä & Bjuv Central Cold Stores",
                "primary_metric": "Electricity Draw",
                "primary_value": "−10%",
                "primary_note": "Saves ~1,100 MWh/yr electricity consumption",
                "primary_color": "#0284c7",
                "co_benefit_metric": "Energy OPEX Savings",
                "co_benefit_value": "€85,000 / yr",
                "co_benefit_note": "Immediate bottom-line operational cash savings",
                "co_benefit_color": "#059669",
                "investment_metric": "Investment",
                "investment_value": "€25,000",
                "investment_note": "High-precision digital temperature telemetry network",
                "investment_color": "#0f172a",
                "trade_off_metric": "Food Safety Validation & Retail Approvals",
                "trade_off_value": "Requires sensory quality trials & joint retail coalition sign-off",
                "trade_off_color": "#ef4444",
                "trade_off_severity": "High",
                "ai_conclusion": (
                    "Offers compelling financial and energy reductions with minimal CAPEX, but faces legal and retail customer hurdles. "
                    "Frozen food regulations historically prescribe strict -18°C baselines. "
                    "Recommendation: Join the global 'Move to -15°C' food industry coalition to present unified microbiological safety data to S-Group and Kesko."
                ),
                "scores": {
                    "Carbon Abatement": 75,
                    "Water Conservation": 45,
                    "Soil & Biodiversity": 50,
                    "Cost Efficiency": 95,
                    "Operational Feasibility": 45,
                },
                "mitigation_playbook": "Conduct 12-month accelerated shelf-life microbiological tests on frozen peas to prove zero sensory degradation at -15°C before customer renegotiation.",
            },
        }
        return self._actions_catalog

    def list_actions(self) -> List[Dict[str, Any]]:
        catalog = self._init_catalog()
        return list(catalog.values())

    def get_action_tradeoff(self, action_id: str) -> Dict[str, Any]:
        catalog = self._init_catalog()
        return catalog.get(action_id, catalog["irrigation_efficiency"])

    def compare_tradeoffs(self, action_ids: List[str]) -> List[Dict[str, Any]]:
        catalog = self._init_catalog()
        return [catalog[aid] for aid in action_ids if aid in catalog]

