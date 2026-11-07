"""Cradle-to-farm-gate footprint per hectare (IPCC 2019 wet-climate Tier 1 + Finnish inventory
organic-soil factors).  Same formulas as the ground truth; see docs/METHODOLOGY.md."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import factors as F


def farm_footprint_per_ha(df: pd.DataFrame, grid_kg_per_kwh: float = 0.03) -> np.ndarray:
    """df needs: crop, n_mineral_kg_ha, n_manure_kg_ha, p_kg_ha, diesel_l_ha, lime_t_ha, sprays,
    yield_t_ha, organic_soil (bool), irrigated (bool); optional lowcarbon_fert (bool)."""
    E = F.FARM_EF
    n2o = E["n2o_n_to_n2o"] * E["n2o_gwp"]
    nmin = df.n_mineral_kg_ha.fillna(0).values
    nman = df.n_manure_kg_ha.fillna(0).values
    yld = df.yield_t_ha.values
    res_n = df.crop.map(F.RESIDUE_N_PER_T).values * yld
    low = df["lowcarbon_fert"].fillna(False).values if "lowcarbon_fert" in df else \
        (df["fertiliser_product"].fillna("").str.contains("low-carbon").values if "fertiliser_product" in df else np.zeros(len(df), bool))
    fert = np.where(low, E["fert_n_prod_lowcarbon"], E["fert_n_prod"])
    k = df.p_kg_ha.fillna(0).values * 2.2
    c_fert = nmin * fert + df.p_kg_ha.fillna(0).values * E["fert_p_prod"] + k * E["fert_k_prod"]
    c_dir = (nmin * E["ef1_synthetic"] + (nman + res_n) * E["ef1_organic"]) * n2o
    c_ind = ((nmin * E["frac_gasf"] + nman * E["frac_gasm"]) * E["ef4_n2o_n"] + (nmin + nman + res_n) * E["frac_leach"] * E["ef5_n2o_n"]) * n2o
    c_dsl = df.diesel_l_ha.fillna(0).values * (E["diesel_ttw"] + E["diesel_wtt"])
    c_lime = df.lime_t_ha.fillna(0).values * E["lime"] * 1000
    org = df.organic_soil.fillna(False).values.astype(bool)
    co2 = np.where(df.crop.values == "grass_ley", E["org_soil_co2_grass_t_ha"], E["org_soil_co2_t_ha"]) * 1000
    c_org = np.where(org, co2 + E["org_soil_n2o_n_kg_ha"] * n2o, 0.0)
    c_spr = df.sprays.fillna(0).values * E["spray_pass"]
    kwh = df.crop.map({c: v["kwh_t"] for c, v in F.MGMT_NORMS.items()}).values * yld + np.where(df.irrigated.fillna(False).values.astype(bool), 180.0, 0.0)
    return c_fert + c_dir + c_ind + c_dsl + c_lime + c_org + c_spr + kwh * grid_kg_per_kwh
