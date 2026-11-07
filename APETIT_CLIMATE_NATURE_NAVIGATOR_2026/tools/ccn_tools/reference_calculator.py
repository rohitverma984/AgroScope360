"""Reference GHG inventory calculator (GHG Protocol, AR6 GWP100).

Input: a dict of *canonical clean tables* (see docs/METHODOLOGY.md, section "Canonical tables").
Output: long table of line items (scope, category, line_item, tco2e, basis).

This is the same method used to compute the hidden ground truth.  Feed it clean data and you
get the right answer; feed it raw data and you inherit every data-quality problem.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import factors as F


def compute_inventory(T: dict, year: int) -> pd.DataFrame:
    EF = dict(zip(T["ef_library"].ef_id, T["ef_library"].kgco2e_per_unit))
    rows = []

    def add(scope, cat, item, t, basis=""):
        rows.append(dict(year=year, scope=scope, category=cat, line_item=item, tco2e=float(t), basis=basis))

    en = T["energy"][T["energy"].year == year]
    fuels = en[~en.carrier.isin(["electricity", "steam", "district_heat"])]
    bio = 0.0
    for (site, carrier), g in fuels.groupby(["site_id", "carrier"]):
        mwh = g.mwh.sum()
        add("scope1", "stationary_and_mobile_combustion", f"{site}:{carrier}", mwh * F.FUEL_EF_T_PER_MWH[carrier], "fuel MWh x fossil EF")
        bio += mwh * F.FUEL_BIOGENIC_T_PER_MWH.get(carrier, 0.0)
    rf = T["refrigerants"][T["refrigerants"].year == year]
    for (site, gas), g in rf.groupby(["site_id", "refrigerant"]):
        add("scope1", "fugitive_refrigerants", f"{site}:{gas}", g.kg_added.sum() * F.REFRIGERANT_GWP[gas] / 1000, "kg top-up x GWP100")
    country = T["sites"].set_index("site_id").country.to_dict()
    g0 = T["goo"]
    g0 = g0[(g0.year == year) & (g0.vintage_year == year)]   # GoO counts only for its own production year
    goo = g0.groupby("site_id").mwh_cancelled.sum().to_dict()
    for site, g in en[en.carrier == "electricity"].groupby("site_id"):
        mwh = g.mwh.sum()
        c = country.get(site, "FI")
        lb = (F.GRID_FI_LB if c == "FI" else F.GRID_SE_LB)[year]
        res = (F.RESIDUAL_FI if c == "FI" else F.RESIDUAL_SE)[year]
        covered = min(mwh, goo.get(site, 0.0))
        add("scope2_location", "purchased_electricity", site, mwh * lb, "MWh x grid average")
        add("scope2_market", "purchased_electricity", site, (mwh - covered) * res, "uncovered MWh x residual mix")
    heat = en[en.carrier.isin(["steam", "district_heat"])]
    hef = T["heat_suppliers"]
    for site, g in heat.groupby("site_id"):
        mwh = g.mwh.sum()
        sup = hef[(hef.site_id == site) & (hef.year == year)]
        mb = float(sup.t_per_mwh.iloc[0]) if len(sup) else 0.0
        add("scope2_location", "purchased_heat_steam", site, mwh * F.HEAT_LB_EF[year], "MWh x national heat average")
        add("scope2_market", "purchased_heat_steam", site, mwh * mb, "MWh x supplier-specific EF")
    pur = T["purchases"][T["purchases"].year == year]
    mm = T["materials"].set_index("material_id")
    svc = set(mm[mm.material_group == "service"].index)
    cap = set(mm[mm.material_group == "capex"].index)
    goods = pur[~pur.material_id.isin(svc | cap)]
    pcf = T.get("pcf_used", pd.DataFrame(columns=["year", "supplier_id", "material_id", "kgco2e_per_kg"]))
    pcf_y = pcf[pcf.year == year].set_index(["supplier_id", "material_id"]).kgco2e_per_kg.to_dict() if len(pcf) else {}
    for (mat, sup), g in goods.groupby(["material_id", "supplier_id"]):
        m = mm.loc[mat]
        if m.default_ef_id == "FARM":
            continue
        kg = g.qty_kg.sum()
        if (sup, mat) in pcf_y:
            ef, basis = pcf_y[(sup, mat)], "supplier PCF (PACT)"
        else:
            ef, basis = EF[m.default_ef_id], m.default_ef_id
        add("scope3", "cat01_purchased_goods", f"{mat}:{sup}", kg * ef / 1000, basis)
    ff = T["farm_footprints"][T["farm_footprints"].year == year]
    for (crop, region), g in ff.groupby(["crop", "region"]):
        add("scope3", "cat01_purchased_goods", f"contract_farming:{region}:{crop}", g.tco2e.sum(), "farm-specific footprint x delivered kg")
    for mat, g in pur[pur.material_id.isin(svc)].groupby("material_id"):
        add("scope3", "cat01_purchased_services", mat, g.amount_eur.sum() * EF[mm.loc[mat].default_ef_id] / 1000, "spend x EEIO")
    for mat, g in pur[pur.material_id.isin(cap)].groupby("material_id"):
        add("scope3", "cat02_capital_goods", mat, g.amount_eur.sum() * EF[mm.loc[mat].default_ef_id] / 1000, "capex spend x EEIO")
    for carrier, g in fuels.groupby("carrier"):
        add("scope3", "cat03_fuel_energy", f"wtt:{carrier}", g.mwh.sum() * EF[F.FUEL_WTT[carrier]] / 1000, "fuel MWh x WTT")
    for site, g in en[en.carrier == "electricity"].groupby("site_id"):
        c = country.get(site, "FI")
        add("scope3", "cat03_fuel_energy", f"elec_upstream:{site}", g.mwh.sum() * EF[f"EF-ELEC-UPSTREAM-{c}"] / 1000, "MWh x upstream+T&D")
    if len(heat):
        add("scope3", "cat03_fuel_energy", "heat_upstream", heat.mwh.sum() * EF["EF-HEAT-UPSTREAM"] / 1000, "MWh x upstream")
    sh = T["shipments"][T["shipments"].year == year]
    for (direction, ef_id), g in sh.groupby(["direction", "ef_id"]):
        cat = "cat04_upstream_transport" if direction == "inbound" else "cat09_downstream_transport"
        add("scope3", cat, f"{direction}:{ef_id}", g.tkm.sum() * EF[ef_id] / 1000, "tkm x WTW EF")
    wh = T["warehousing"][T["warehousing"].year == year]
    if len(wh):
        add("scope3", "cat09_downstream_transport", "frozen_warehousing", wh.pallet_days.sum() * EF["EF-PALLETDAY-FROZEN"] / 1000, "pallet-days x EF")
    ws = T["waste"][T["waste"].year == year]
    for (site, stream, ef_id), g in ws.groupby(["site_id", "waste_stream", "ef_id"]):
        add("scope3", "cat05_waste", f"{site}:{stream}", g.t.sum() * EF[ef_id] / 1000, "t x treatment EF")
    ww = T["wastewater"][T["wastewater"].year == year]
    add("scope3", "cat05_waste", "wastewater_third_party", ww.m3.sum() * EF["EF-WASTEWATER-MUNI"] / 1000, "m3 x EF")
    tr = T["travel"][T["travel"].year == year]
    add("scope3", "cat06_business_travel", "flights", tr[tr["mode"] == "flight"].pkm.sum() * EF["EF-PKM-FLIGHT-SHORT"] / 1000, "pkm x EF")
    add("scope3", "cat06_business_travel", "rail", tr[tr["mode"] == "train"].pkm.sum() * EF["EF-PKM-TRAIN"] / 1000, "pkm x EF")
    add("scope3", "cat06_business_travel", "hotels", tr.nights.sum() * EF["EF-HOTEL-NIGHT"] / 1000, "nights x EF")
    cs = T["commuting_survey"]
    hc = T["headcount"][T["headcount"].year == year].set_index("site_id").headcount
    mode_ef = {"car": EF["EF-PKM-CAR"], "carpool": EF["EF-PKM-CAR"] / 2, "bus": EF["EF-PKM-BUS"], "train": EF["EF-PKM-TRAIN"],
               "bike_walk": 0.0, "ev_car": 0.03}
    for site, g in cs.groupby("site_id"):
        per = (g.one_way_km * 2 * g.days_on_site_per_week * 46 * g["mode"].map(mode_ef).fillna(EF["EF-PKM-CAR"])).mean()
        add("scope3", "cat07_employee_commuting", site, per * hc.get(site, 0) / 1000, "survey mean x headcount")
    sales = T["sales"][T["sales"].year == year]
    for (grp, market), g in sales.groupby(["product_group", "market"]):
        kwh = g.t_sold.sum() * 1000 * F.USE_PHASE_KWH_PER_KG[grp]
        if kwh > 0:
            add("scope3", "cat11_use_of_sold_products", f"{grp}:{market}", kwh * F.MARKET_GRID[market][year] / 1000, "kWh x market grid")
        pl, bd = F.PACK_KG_PER_T[grp]
        t = g.t_sold.sum()
        add("scope3", "cat12_end_of_life", f"{grp}:{market}", t * pl / 1000 * F.EOL_PLASTIC_EF_T + t * bd / 1000 * F.EOL_BOARD_EF_T, "packaging t x EoL EF")
    out = pd.DataFrame(rows)
    out.attrs["biogenic_co2_t"] = bio
    return out


def summarise(inv: pd.DataFrame) -> pd.DataFrame:
    s = inv.copy()
    s.loc[s.category.isin(["cat01_purchased_goods", "cat01_purchased_services"]), "category"] = "cat01_purchased_goods_services"
    s = s.groupby(["scope", "category"]).tco2e.sum().reset_index()
    tot = [dict(scope="total", category="scope1_total", tco2e=inv[inv.scope == "scope1"].tco2e.sum()),
           dict(scope="total", category="scope2_location_total", tco2e=inv[inv.scope == "scope2_location"].tco2e.sum()),
           dict(scope="total", category="scope2_market_total", tco2e=inv[inv.scope == "scope2_market"].tco2e.sum()),
           dict(scope="total", category="scope3_total", tco2e=inv[inv.scope == "scope3"].tco2e.sum()),
           dict(scope="memo", category="biogenic_co2_scope1", tco2e=inv.attrs.get("biogenic_co2_t", np.nan))]
    return pd.concat([s, pd.DataFrame(tot)], ignore_index=True)
