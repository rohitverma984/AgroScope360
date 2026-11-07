"""
prototype/core/simulator_service.py — AI What-If Decision Simulator Engine
Calculates the cascading effects of agricultural, energy, and operational decisions on:
1. GHG Emissions (Scope 1, 2, 3 FLAG & Industrial)
2. Agricultural & Operational Financials (€)
3. Crop Production & Yield (tonnes)
4. Water Consumption (m³)
5. Nature & Freshwater Nutrient Runoff (P & N to water)
Plus generates an evidence-backed AI synthesis of trade-offs and feasibility.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd


class SimulatorService:
    def __init__(self, root: Path):
        self.root = root

    def run_simulation(
        self,
        fertiliser_pct_delta: float = -20.0,      # e.g. -20%
        irrigation_eff_delta: float = 15.0,       # e.g. +15%
        renewable_energy_delta: float = 30.0,     # e.g. +30%
        production_volume_delta: float = 10.0,    # e.g. +10%
        use_lowcarbon_fert: bool = False,
        use_buffer_strips: bool = True,
        use_catch_crops: bool = True,
        carbon_price_eur: float = 80.0,
    ) -> Dict[str, Any]:
        """
        Deterministic what-if multi-variable simulation engine.
        Calibrated to Apetit 2025 baseline figures.
        """
        # ── 1. Baseline 2025 Core Anchors ───────────────────────────────────
        base_scope1 = 132163.0             # tCO2e (fuels + refrigerants)
        base_scope2 = 1117416.0            # tCO2e (market-based net of baseline GoO)
        base_scope3_flag = 7400000.0       # tCO2e (farm direct/indirect N2O, peat soils, lime)
        base_scope3_ind = 10134592.0       # tCO2e (goods, transport, packaging, waste, energy)
        base_total = base_scope1 + base_scope2 + base_scope3_flag + base_scope3_ind

        base_crop_tonnes = 42000.0         # tonnes contracted produce
        base_water_m3 = 680000.0           # m3 (irrigation + processing)
        base_p_to_water_kg = 2450.0        # kg P delivered to water
        base_n_to_water_kg = 33800.0       # kg N delivered to water
        base_farm_spend_eur = 14200000.0   # € (contract payments + seed/fert inputs)
        base_energy_spend_eur = 4800000.0  # € (electricity, gas, fuels)

        # ── 2. Apply Decision Levers ─────────────────────────────────────────
        prod_mult = 1.0 + (production_volume_delta / 100.0)
        fert_mult = 1.0 + (fertiliser_pct_delta / 100.0)
        irrig_mult = 1.0 - (irrigation_eff_delta / 100.0)
        renew_add = min(1.0, max(0.0, renewable_energy_delta / 100.0))

        # Crop production response:
        # Fertiliser reduction has a mild non-linear yield penalty unless compensated by catch crops/precision
        if fertiliser_pct_delta < 0:
            raw_yield_drop = abs(fertiliser_pct_delta) * 0.12  # -20% fert -> ~2.4% yield dip
            if use_catch_crops:
                raw_yield_drop *= 0.4  # catch crops mitigate 60% of nutrient loss
            sim_crop_tonnes = base_crop_tonnes * prod_mult * (1.0 - (raw_yield_drop / 100.0))
        else:
            sim_crop_tonnes = base_crop_tonnes * prod_mult * (1.0 + (fertiliser_pct_delta * 0.04 / 100.0))

        # Water consumption:
        # Irrigation accounts for ~40% of group water, processing is ~60%
        sim_water_m3 = (base_water_m3 * 0.40 * irrig_mult * prod_mult) + (base_water_m3 * 0.60 * prod_mult)
        water_saved_m3 = base_water_m3 - sim_water_m3
        water_pct_delta = ((sim_water_m3 / base_water_m3) - 1.0) * 100.0

        # Nature: Nutrient Runoff (P and N to water):
        p_runoff_mult = fert_mult * prod_mult
        n_runoff_mult = fert_mult * prod_mult
        if use_buffer_strips:
            p_runoff_mult *= 0.65  # Buffer strips trap ~35% of particulate P
            n_runoff_mult *= 0.85  # Buffer strips trap ~15% of surface N
        if use_catch_crops:
            n_runoff_mult *= 0.75  # Winter cover crops capture residual nitrate

        sim_p_kg = base_p_to_water_kg * p_runoff_mult
        sim_n_kg = base_n_to_water_kg * n_runoff_mult
        p_delta_pct = ((sim_p_kg / base_p_to_water_kg) - 1.0) * 100.0
        n_delta_pct = ((sim_n_kg / base_n_to_water_kg) - 1.0) * 100.0

        # GHG Emissions:
        # Scope 1 (Fuels): Biogas/renewable shift cuts fossil combustion
        sim_scope1 = base_scope1 * (1.0 - (renew_add * 0.60))

        # Scope 2 (Electricity): Renewable power reduces residual mix towards 0
        sim_scope2 = base_scope2 * max(0.0, 1.0 - renew_add)

        # Scope 3 FLAG: Driven by fertiliser N2O, peat soil management, liming
        fert_n2o_mult = fert_mult if not use_lowcarbon_fert else (fert_mult * 0.85)
        sim_scope3_flag = base_scope3_flag * prod_mult * fert_n2o_mult

        # Scope 3 Industrial: Manufacturing of fertilisers + processing + transport
        fert_mfg_factor = 0.35 if use_lowcarbon_fert else 1.0
        sim_scope3_ind = (base_scope3_ind * 0.75 * prod_mult) + (base_scope3_ind * 0.25 * prod_mult * fert_mult * fert_mfg_factor)

        sim_total = sim_scope1 + sim_scope2 + sim_scope3_flag + sim_scope3_ind
        total_ghg_saved = base_total - sim_total
        ghg_pct_delta = ((sim_total / base_total) - 1.0) * 100.0

        # Financial Calculations (€):
        fert_cost_delta = (fert_mult - 1.0) * 1800000.0   # baseline fertiliser bill ~1.8M€
        if use_lowcarbon_fert:
            fert_cost_delta += 140000.0  # slight premium for green fertilizer
        if use_catch_crops:
            fert_cost_delta += 45000.0   # seed & sowing cost
        if use_buffer_strips:
            fert_cost_delta += 25000.0   # buffer maintenance

        # Energy savings vs premium for renewables:
        energy_cost_delta = (base_energy_spend_eur * renew_add * 0.05) - (base_energy_spend_eur * (irrigation_eff_delta / 100.0) * 0.08)

        # Carbon tax / ETS2 savings from lower Scope 1 + 2:
        scope1_2_saved = (base_scope1 + base_scope2) - (sim_scope1 + sim_scope2)
        carbon_tax_savings = scope1_2_saved * (carbon_price_eur / 1000.0) * 1.5

        # Revenue impact from crop volume:
        crop_revenue_delta = (sim_crop_tonnes - base_crop_tonnes) * 320.0  # blended €320/t value

        net_financial_delta = fert_cost_delta + energy_cost_delta - carbon_tax_savings - crop_revenue_delta

        # ── 3. Performance Scoring & Grades ──────────────────────────────────
        # Climate Score
        if ghg_pct_delta <= -20:
            climate_grade = "A+"
        elif ghg_pct_delta <= -12:
            climate_grade = "A"
        elif ghg_pct_delta <= -5:
            climate_grade = "B+"
        elif ghg_pct_delta <= 0:
            climate_grade = "B"
        else:
            climate_grade = "C"

        # Nature & Water Score (P/N runoff + water saved)
        nature_score_val = (-p_delta_pct * 0.6) + (-water_pct_delta * 0.4)
        if nature_score_val >= 25:
            nature_grade = "A+"
        elif nature_score_val >= 15:
            nature_grade = "A"
        elif nature_score_val >= 5:
            nature_grade = "B+"
        else:
            nature_grade = "B-"

        # Feasibility Grade
        if net_financial_delta <= 0:
            feasibility_grade = "High (Net Economic Savings)"
        elif net_financial_delta < 200000:
            feasibility_grade = "Medium (Moderate Capital Cost)"
        else:
            feasibility_grade = "Low (Substantial Capital Required)"

        # ── 4. AI Explanation & Trade-Off Synthesis ──────────────────────────
        ai_narrative = (
            f"**Strategic Trade-Off Analysis:**\\n"
            f"• **Climate Decarbonisation:** Reduces group footprint by **{total_ghg_saved:,.0f} tCO₂e ({ghg_pct_delta:+.1f}%)**, "
            f"primarily driven by {'green fertilizer substitution' if use_lowcarbon_fert else 'synthetic nitrogen reduction'} and renewable power additions.\\n"
            f"• **Nature & Freshwater Resilience:** Phosphorus delivery to local lakes drops by **{abs(p_delta_pct):.1f}%** ({abs(base_p_to_water_kg - sim_p_kg):,.1f} kg P/yr), "
            f"alleviating eutrophication pressure in high-risk catchments like Lake Pyhäjärvi.\\n"
            f"• **Agricultural & Financial Feasibility:** Net annual operational impact is **€{abs(net_financial_delta):,.0f} {'savings' if net_financial_delta <= 0 else 'investment'}**. "
            f"Yield changes are managed to **{((sim_crop_tonnes/base_crop_tonnes)-1.0)*100:+.1f}%** (simulated output: {sim_crop_tonnes:,.0f} tonnes)."
        )

        return {
            "inputs": {
                "fertiliser_pct_delta": fertiliser_pct_delta,
                "irrigation_eff_delta": irrigation_eff_delta,
                "renewable_energy_delta": renewable_energy_delta,
                "production_volume_delta": production_volume_delta,
                "use_lowcarbon_fert": use_lowcarbon_fert,
                "use_buffer_strips": use_buffer_strips,
                "use_catch_crops": use_catch_crops,
                "carbon_price_eur": carbon_price_eur,
            },
            "ghg": {
                "base_total_tco2e": base_total,
                "sim_total_tco2e": sim_total,
                "delta_tco2e": -total_ghg_saved,
                "delta_pct": ghg_pct_delta,
                "sim_scope1": sim_scope1,
                "sim_scope2": sim_scope2,
                "sim_scope3_flag": sim_scope3_flag,
                "sim_scope3_ind": sim_scope3_ind,
            },
            "financials": {
                "net_delta_eur": net_financial_delta,
                "fert_cost_delta": fert_cost_delta,
                "energy_cost_delta": energy_cost_delta,
                "carbon_tax_savings": carbon_tax_savings,
                "crop_revenue_delta": crop_revenue_delta,
            },
            "crop": {
                "base_tonnes": base_crop_tonnes,
                "sim_tonnes": sim_crop_tonnes,
                "delta_tonnes": sim_crop_tonnes - base_crop_tonnes,
                "delta_pct": ((sim_crop_tonnes / base_crop_tonnes) - 1.0) * 100.0,
            },
            "water": {
                "base_m3": base_water_m3,
                "sim_m3": sim_water_m3,
                "delta_m3": -water_saved_m3,
                "delta_pct": water_pct_delta,
            },
            "nature": {
                "base_p_kg": base_p_to_water_kg,
                "sim_p_kg": sim_p_kg,
                "p_delta_pct": p_delta_pct,
                "base_n_kg": base_n_to_water_kg,
                "sim_n_kg": sim_n_kg,
                "n_delta_pct": n_delta_pct,
            },
            "grades": {
                "climate": climate_grade,
                "nature": nature_grade,
                "feasibility": feasibility_grade,
            },
            "ai_narrative": ai_narrative,
        }

