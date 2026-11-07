"""
prototype/core/investment_optimizer_service.py — AI Sustainability Investment Optimiser
Enterprise Multi-Objective Portfolio Allocation Engine connecting corporate sustainability
with CFO business metrics (NPV, IRR, Payback, Cumulative Cash Flow, and Hurdle Rates).

Evaluates initiatives across:
- Emissions reduction (tCO2e abated)
- Climate adaptation & yield resilience
- Nature & freshwater benefits (SBTN P-runoff & riparian buffer restoration)
- Financial returns (10-year discounted cash flows at 8% hurdle rate, OPEX savings)
- Implementation feasibility & regulatory readiness
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd


class InvestmentOptimizerService:
    def __init__(self, root: Optional[Path] = None):
        self.root = root
        self.discount_rate = 0.08  # Enterprise hurdle rate: 8%
        self.carbon_price_eur = 85.0  # EU ETS / internal carbon shadow price (€/tCO2e)
        self.horizon_years = 10

        # Initiative Master Catalog
        self._initiatives: List[Dict[str, Any]] = [
            {
                "id": "fert_opt",
                "title": "Fertiliser Optimisation",
                "category": "Agronomy",
                "base_capex": 20000.0,
                "annual_opex_savings": 5800.0,
                "ghg_abatement_tco2e": 165.0,
                "adaptation_score": 74.0,
                "nature_score": 88.0,
                "feasibility_score": 92.0,
                "water_saved_m3": 1200.0,
                "p_loss_prevented_kg": 240.0,
                "primary_benefit": "Emission reduction & lower fertilizer purchase costs",
                "mechanism": "Variable-rate precision N-sensors & nitrification inhibitors across 1,800 ha contract farmland.",
            },
            {
                "id": "water_eff",
                "title": "Water Efficiency & Drip Irrigation",
                "category": "Agronomy",
                "base_capex": 30000.0,
                "annual_opex_savings": 8200.0,
                "ghg_abatement_tco2e": 48.0,
                "adaptation_score": 95.0,
                "nature_score": 84.0,
                "feasibility_score": 86.0,
                "water_saved_m3": 14500.0,
                "p_loss_prevented_kg": 110.0,
                "primary_benefit": "Lower water stress & drought yield protection",
                "mechanism": "Precision micro-drip irrigation & soil tensiometers at high-vulnerability potato/pea parcels.",
            },
            {
                "id": "renew_energy",
                "title": "Renewable Energy & Heat Recovery",
                "category": "Factory & Energy",
                "base_capex": 35000.0,
                "annual_opex_savings": 11400.0,
                "ghg_abatement_tco2e": 210.0,
                "adaptation_score": 45.0,
                "nature_score": 52.0,
                "feasibility_score": 95.0,
                "water_saved_m3": 400.0,
                "p_loss_prevented_kg": 0.0,
                "primary_benefit": "Direct Scope 1 & 2 emission cuts + power bill savings",
                "mechanism": "Rooftop solar PV expansion + heat pump recovery on Säkylä freezing tunnels.",
            },
            {
                "id": "soil_regen",
                "title": "Soil Organic Health & Catch Crops",
                "category": "Nature & Soil",
                "base_capex": 15000.0,
                "annual_opex_savings": 3900.0,
                "ghg_abatement_tco2e": 95.0,
                "adaptation_score": 88.0,
                "nature_score": 94.0,
                "feasibility_score": 89.0,
                "water_saved_m3": 2800.0,
                "p_loss_prevented_kg": 310.0,
                "primary_benefit": "Soil ecosystem benefits & moisture retention",
                "mechanism": "Multi-species winter cover crops & biochar incorporation enhancing soil organic matter.",
            },
            {
                "id": "fleet_ev",
                "title": "Electric Logistics Fleet Transition",
                "category": "Logistics",
                "base_capex": 45000.0,
                "annual_opex_savings": 13800.0,
                "ghg_abatement_tco2e": 145.0,
                "adaptation_score": 30.0,
                "nature_score": 42.0,
                "feasibility_score": 82.0,
                "water_saved_m3": 0.0,
                "p_loss_prevented_kg": 0.0,
                "primary_benefit": "Scope 3 freight decarbonisation & diesel fuel savings",
                "mechanism": "Depot megawatt charging infrastructure & electric distribution truck leases for Naantali-Helsinki route.",
            },
            {
                "id": "buffer_wetlands",
                "title": "Riparian Buffer Strips & Constructed Wetlands",
                "category": "Nature & SBTN",
                "base_capex": 25000.0,
                "annual_opex_savings": 2800.0,
                "ghg_abatement_tco2e": 38.0,
                "adaptation_score": 86.0,
                "nature_score": 98.0,
                "feasibility_score": 91.0,
                "water_saved_m3": 3500.0,
                "p_loss_prevented_kg": 460.0,
                "primary_benefit": "SBTN Freshwater eutrophication prevention & biodiversity",
                "mechanism": "10m grass/shrub buffer zones along main agricultural ditches in Eurajoki & Loimijoki catchments.",
            },
            {
                "id": "biogas_circ",
                "title": "Vegetable Processing Biogas Circularity",
                "category": "Factory & Energy",
                "base_capex": 40000.0,
                "annual_opex_savings": 12200.0,
                "ghg_abatement_tco2e": 185.0,
                "adaptation_score": 50.0,
                "nature_score": 75.0,
                "feasibility_score": 80.0,
                "water_saved_m3": 1800.0,
                "p_loss_prevented_kg": 180.0,
                "primary_benefit": "Circular biomethane production & zero organic waste to landfill",
                "mechanism": "Anaerobic digestor off-take contract with local bio-refinery for pea pods and carrot peelings.",
            },
            {
                "id": "drought_seeds",
                "title": "Drought-Resilient Seed Cultivar Program",
                "category": "Agronomy",
                "base_capex": 20000.0,
                "annual_opex_savings": 4600.0,
                "ghg_abatement_tco2e": 30.0,
                "adaptation_score": 96.0,
                "nature_score": 70.0,
                "feasibility_score": 88.0,
                "water_saved_m3": 5200.0,
                "p_loss_prevented_kg": 50.0,
                "primary_benefit": "High-temperature flowering protection & yield security",
                "mechanism": "Co-funding heat-tolerant Nordic pea & potato seed lines with Finnish research institute Luke.",
            },
        ]

    def get_all_initiatives(self) -> List[Dict[str, Any]]:
        """Return the full initiative catalog."""
        return self._initiatives

    def optimize_portfolio(
        self,
        budget: float = 100000.0,
        weights: Optional[Dict[str, float]] = None,
        min_feasibility: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Multi-objective knapsack allocation prioritizing initiatives according to user weights:
        - emissions (GHG reduction)
        - adaptation (Climate risk & drought resilience)
        - nature (SBTN freshwater & soil biodiversity)
        - financial (10-year discounted cash flow & ROI)
        - feasibility (Operational readiness)
        """
        if weights is None:
            # Default balanced weights
            weights = {
                "emissions": 0.25,
                "adaptation": 0.20,
                "nature": 0.20,
                "financial": 0.25,
                "feasibility": 0.10,
            }

        # Normalize weights
        w_sum = sum(weights.values()) or 1.0
        w = {k: v / w_sum for k, v in weights.items()}

        candidates = [item for item in self._initiatives if item["feasibility_score"] >= min_feasibility]

        # Calculate multi-objective score per € invested
        scored = []
        for item in candidates:
            capex = item["base_capex"]
            # 10-year undiscounted cash return ratio
            ten_yr_flow = (item["annual_opex_savings"] * 10) / capex
            # GHG abatement intensity (tCO2e per €10k)
            ghg_intensity = (item["ghg_abatement_tco2e"] / capex) * 10000.0
            # SBTN Nature intensity
            nat_intensity = item["nature_score"] / 100.0
            # Climate Adaptation intensity
            adapt_intensity = item["adaptation_score"] / 100.0
            # Feasibility
            feas_norm = item["feasibility_score"] / 100.0

            # Composite weighted utility index
            utility_score = (
                w["emissions"] * ghg_intensity * 0.4
                + w["adaptation"] * adapt_intensity * 2.0
                + w["nature"] * nat_intensity * 2.0
                + w["financial"] * ten_yr_flow * 0.7
                + w["feasibility"] * feas_norm * 1.0
            )

            scored.append({
                **item,
                "utility_score": utility_score,
                "ten_yr_flow": ten_yr_flow,
            })

        # Rank candidates by utility density (benefit per euro)
        scored.sort(key=lambda x: x["utility_score"] / x["base_capex"], reverse=True)

        allocated = []
        remaining_budget = budget

        # Knapsack allocation
        for item in scored:
            cost = item["base_capex"]
            if remaining_budget >= cost:
                # Fully funded
                allocated.append({
                    **item,
                    "allocated_investment": cost,
                    "funding_pct": 100.0,
                })
                remaining_budget -= cost
            elif remaining_budget >= cost * 0.45:
                # Scaled / Phase 1 partial implementation
                partial_amt = round(remaining_budget, -2)
                pct = (partial_amt / cost) * 100.0
                scale = partial_amt / cost
                allocated.append({
                    **item,
                    "allocated_investment": partial_amt,
                    "funding_pct": round(pct, 1),
                    # Scale impacts linearly
                    "annual_opex_savings": item["annual_opex_savings"] * scale,
                    "ghg_abatement_tco2e": item["ghg_abatement_tco2e"] * scale,
                    "water_saved_m3": item["water_saved_m3"] * scale,
                    "p_loss_prevented_kg": item["p_loss_prevented_kg"] * scale,
                })
                remaining_budget -= partial_amt
                break  # Budget exhausted

        allocated_capex = budget - remaining_budget

        # Aggregate portfolio metrics
        total_annual_savings = sum(a["annual_opex_savings"] for a in allocated)
        total_ghg_abated = sum(a["ghg_abatement_tco2e"] for a in allocated)
        total_water_saved = sum(a["water_saved_m3"] for a in allocated)
        total_p_runoff_saved = sum(a["p_loss_prevented_kg"] for a in allocated)
        avg_feasibility = float(np.mean([a["feasibility_score"] for a in allocated])) if allocated else 0.0

        # Financial Cash Flow Modelling (10-Year Trajectory)
        r = self.discount_rate
        cash_flows = [-allocated_capex]
        trajectory = [{
            "year": 0,
            "annual_flow": -allocated_capex,
            "cumulative_cash_flow": -allocated_capex,
            "discounted_flow": -allocated_capex,
        }]

        cum_flow = -allocated_capex
        breakeven_year = None

        for yr in range(1, self.horizon_years + 1):
            # Carbon tax avoidance & ESG yield bonus adds ~6% to cash value over time
            carbon_benefit = total_ghg_abated * (self.carbon_price_eur * (1.0 + 0.03 * (yr - 1))) * 0.15
            net_annual = total_annual_savings + carbon_benefit
            cum_flow += net_annual
            disc_flow = net_annual / ((1.0 + r) ** yr)

            if cum_flow >= 0 and breakeven_year is None:
                # Fractional breakeven calculation
                prev = trajectory[-1]["cumulative_cash_flow"]
                fraction = abs(prev) / max(net_annual, 1.0)
                breakeven_year = round((yr - 1) + fraction, 1)

            cash_flows.append(net_annual)
            trajectory.append({
                "year": yr,
                "annual_flow": round(net_annual, 0),
                "cumulative_cash_flow": round(cum_flow, 0),
                "discounted_flow": round(disc_flow, 0),
            })

        if breakeven_year is None:
            breakeven_year = ">10 Years"

        # Net Present Value (NPV @ 8%)
        npv_10y = -allocated_capex + sum(
            cf["annual_flow"] / ((1.0 + r) ** cf["year"]) for cf in trajectory if cf["year"] > 0
        )

        # Internal Rate of Return (IRR)
        irr_pct = self._calculate_irr(cash_flows)

        # NPV Waterfall Components
        energy_savings_npv = total_annual_savings * 0.42 * 6.71  # 10y annuity factor @ 8%
        agri_inputs_npv = total_annual_savings * 0.38 * 6.71
        carbon_avoidance_npv = (total_ghg_abated * self.carbon_price_eur * 0.20) * 6.71
        yield_protection_npv = (total_annual_savings * 0.20) * 6.71
        esg_subsidies_npv = allocated_capex * 0.12  # Estimated EU CAP / Business Finland green subsidies

        waterfall = {
            "initial_investment": -allocated_capex,
            "energy_fuel_savings": round(energy_savings_npv, 0),
            "input_cost_cuts": round(agri_inputs_npv, 0),
            "carbon_avoidance": round(carbon_avoidance_npv, 0),
            "yield_protection": round(yield_protection_npv, 0),
            "esg_subsidies": round(esg_subsidies_npv, 0),
            "net_present_value": round(npv_10y, 0),
        }

        # Biggest Value Drivers
        drivers = [
            {"driver": "Operational Cost Cuts", "amount_eur": energy_savings_npv + agri_inputs_npv, "share_pct": 52.0},
            {"driver": "Carbon & Fuel Tax Shield", "amount_eur": carbon_avoidance_npv, "share_pct": 22.0},
            {"driver": "Harvest Yield Loss Averted", "amount_eur": yield_protection_npv, "share_pct": 14.0},
            {"driver": "ESG & CAP Co-Funding", "amount_eur": esg_subsidies_npv, "share_pct": 12.0},
        ]

        # Cost of Inaction (If €0 invested)
        cost_of_inaction = {
            "ten_yr_financial_penalty_eur": round(allocated_capex * 1.65, 0),
            "lost_crop_yield_tha": 0.42,
            "cumulative_carbon_tax_exposure_eur": round(total_ghg_abated * 10 * 85.0 * 0.35, 0),
            "sbtn_freshwater_risk": "Critical: high risk of summer algae bloom fines and local watershed sanctions.",
        }

        # Strategic AI Investment Justification
        top_titles = [f"**{a['title']}** (€{a['allocated_investment']:,.0f})" for a in allocated[:3]]
        ai_memo = (
            f"**Strategic Sustainability Capital Allocation Brief (Budget: €{budget:,.0f}):**\\n"
            f"• **Optimised Deployment:** The multi-objective engine allocated **€{allocated_capex:,.0f}** across "
            f"**{len(allocated)} key initiatives**, preserving €{remaining_budget:,.0f} in contingency reserves.\\n"
            f"• **Core Financial Value:** Generates a **10-Year Net Present Value (NPV) of €{npv_10y:,.0f}** at an 8% hurdle rate, "
            f"delivering an **Internal Rate of Return (IRR) of {irr_pct:.1f}%** with full capital payback in **Year {breakeven_year}**.\\n"
            f"• **Climate & Nature Balance:** Delivers **{total_ghg_abated:,.0f} tCO₂e/year** in permanent decarbonisation while "
            f"saving **{total_water_saved:,.0f} m³** of irrigation water and filtering **{total_p_runoff_saved:,.0f} kg** of phosphorus runoff.\\n"
            f"• **Priority Allocations:** {', '.join(top_titles)}."
        )

        return {
            "budget": budget,
            "allocated_capex": allocated_capex,
            "unallocated_reserve": remaining_budget,
            "allocated_initiatives": allocated,
            "total_annual_savings": total_annual_savings,
            "total_ghg_abated_tco2e": total_ghg_abated,
            "total_water_saved_m3": total_water_saved,
            "total_p_runoff_saved_kg": total_p_runoff_saved,
            "avg_feasibility": avg_feasibility,
            "npv_10y": npv_10y,
            "irr_pct": irr_pct,
            "breakeven_year": breakeven_year,
            "trajectory": trajectory,
            "waterfall": waterfall,
            "drivers": drivers,
            "cost_of_inaction": cost_of_inaction,
            "ai_memo": ai_memo,
            "hurdle_rate_multiple": round((npv_10y + allocated_capex) / max(allocated_capex, 1.0), 2),
        }

    def get_budget_sensitivity_curve(
        self,
        min_budget: float = 20000.0,
        max_budget: float = 250000.0,
        steps: int = 12,
    ) -> pd.DataFrame:
        """Calculate the efficiency frontier showing return scaling as budget increases."""
        budgets = np.linspace(min_budget, max_budget, steps)
        rows = []
        for b in budgets:
            res = self.optimize_portfolio(budget=float(b))
            rows.append({
                "budget_eur": b,
                "npv_10y_eur": res["npv_10y"],
                "ghg_abated_tco2e": res["total_ghg_abated_tco2e"],
                "water_saved_m3": res["total_water_saved_m3"],
                "p_runoff_kg": res["total_p_runoff_saved_kg"],
                "irr_pct": res["irr_pct"],
                "initiatives_count": len(res["allocated_initiatives"]),
            })
        return pd.DataFrame(rows)

    def _calculate_irr(self, cash_flows: List[float]) -> float:
        """Robust internal rate of return calculation via binary bisection."""
        if len(cash_flows) < 2 or cash_flows[0] >= 0:
            return 0.0

        low, high = -0.5, 3.0
        for _ in range(60):
            mid = (low + high) / 2.0
            npv = sum(cf / ((1.0 + mid) ** t) for t, cf in enumerate(cash_flows))
            if abs(npv) < 1.0:
                return round(mid * 100.0, 1)
            if npv > 0:
                low = mid
            else:
                high = mid
        return round(mid * 100.0, 1)

