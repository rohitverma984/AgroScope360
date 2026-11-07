"""Loaders for the participant package and a *naive* raw -> canonical conversion.

`naive_canonical()` converts units and formats exactly as documented but does NOT clean data:
it is the starting point (and the A2 baseline), not the answer.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import factors as F
from .farm_calculator import farm_footprint_per_ha

DEFAULT_ROOT = Path(__file__).resolve().parents[2]


def data_dir(root: Path | str | None = None) -> Path:
    root = Path(root) if root else DEFAULT_ROOT
    return root / "data"


def load_raw(root=None) -> dict:
    d = data_dir(root)
    R = d / "02_raw_feeds"
    raw = {
        "sites": pd.read_csv(d / "01_master" / "sites.csv"),
        "materials": pd.read_csv(d / "01_master" / "materials.csv"),
        "suppliers": pd.read_csv(d / "01_master" / "suppliers.csv"),
        "ef_library": pd.read_csv(d / "01_master" / "emission_factor_library.csv"),
        "farm_registry": pd.read_csv(d / "01_master" / "farm_registry.csv"),
        "parcels": pd.read_csv(d / "01_master" / "parcels.csv"),
        "erp": pd.read_csv(R / "erp_purchase_lines_2021_2025.csv", dtype={"doc_no": str, "reference_doc": str}),
        "energy_meter": pd.read_csv(R / "energy_meter_readings.csv"),
        "fuel_deliveries": pd.read_csv(R / "fuel_deliveries.csv"),
        "fuel_stock": pd.read_csv(R / "fuel_stock_changes.csv"),
        "goo": pd.read_csv(R / "goo_cancellations.csv"),
        "heat_suppliers": pd.read_csv(R / "heat_supplier_factors.csv"),
        "refrigerants": pd.read_csv(R / "refrigerant_service_log.csv"),
        "waste": pd.read_csv(R / "waste_transfer_notes.csv"),
        "wastewater": pd.read_csv(R / "wastewater_third_party.csv"),
        "water": pd.read_csv(R / "water_balance.csv"),
        "travel": pd.read_csv(R / "travel_bookings.csv"),
        "commuting": pd.read_csv(R / "commuting_survey_2025.csv"),
        "headcount": pd.read_csv(R / "headcount.csv"),
        "shipments": pd.read_csv(R / "shipments.csv"),
        "warehousing": pd.read_csv(R / "frozen_warehousing.csv"),
        "sales": pd.read_csv(R / "sales_volumes.csv"),
        "farm_survey": pd.read_csv(d / "03_farming" / "farm_survey_fi.csv"),
        "crop_history": pd.read_csv(d / "03_farming" / "parcel_crop_history_and_plan.csv"),
    }
    pcfs = []
    for f in sorted((R / "supplier_pcfs").glob("*.json")):
        js = json.loads(f.read_text())
        sup, mat, year = f.stem.split("_")
        pcfs.append(dict(file=f.name, supplier_id=sup, material_id=mat, year=int(year),
                         value=float(js["pcf"]["pCfExcludingBiogenic"]), declared_unit=js["pcf"]["declaredUnit"],
                         ref_start=js["pcf"]["referencePeriodStart"][:10], ref_end=js["pcf"]["referencePeriodEnd"][:10]))
    raw["pcfs"] = pd.DataFrame(pcfs)
    return raw


def naive_canonical(raw: dict) -> dict:
    """Unit/format conversion only. No de-duplication, no outlier handling, no gap filling."""
    T = {k: raw[k] for k in ("sites", "materials", "ef_library", "goo", "heat_suppliers", "headcount", "warehousing", "wastewater")}
    erp = raw["erp"].copy()
    erp["year"] = erp.posting_date.str[:4].astype(int)
    erp["qty_kg"] = np.where(erp.uom == "TO", erp.quantity * 1000, np.where(erp.uom == "KG", erp.quantity, 0.0))
    erp["amount_eur"] = erp.net_amount / erp.currency.map(F.FX_PER_EUR).fillna(1.0)
    T["purchases"] = erp
    em = raw["energy_meter"].copy()
    em["mwh"] = np.where(em.unit == "kWh", em.value / 1000, em.value)
    fd = raw["fuel_deliveries"].copy()
    ncv = {"lng": F.NCV["lng_t"], "lpg": F.NCV["lpg_t"], "light_fuel_oil": F.NCV["lfo_l"], "diesel": F.NCV["diesel_l"]}
    fdy = fd.groupby(["site_id", "carrier", "year"]).quantity.sum().reset_index()
    fdy = fdy.merge(raw["fuel_stock"][["site_id", "carrier", "year", "stock_change"]], on=["site_id", "carrier", "year"], how="left").fillna({"stock_change": 0})
    fdy["mwh"] = (fdy.quantity - fdy.stock_change) * fdy.carrier.map(ncv)
    fdy["month"] = 0
    T["energy"] = pd.concat([em[["site_id", "year", "month", "carrier", "mwh"]], fdy[["site_id", "year", "month", "carrier", "mwh"]]], ignore_index=True)
    T["refrigerants"] = raw["refrigerants"][["site_id", "year", "refrigerant", "kg_added"]]
    w = raw["waste"].copy()
    w["t"] = w.quantity / 1000
    efmap = {"anaerobic_digestion": "EF-WASTE-BIO-AD", "composting": "EF-WASTE-BIO-COMPOST", "incineration": "EF-WASTE-MIXED-INC",
             "recycling": "EF-WASTE-RECYCLE", "landfill_codigestion": "EF-WASTE-SPENTEARTH"}
    w["ef_id"] = w.treatment.map(efmap)
    w.loc[w.waste_stream == "plastic_waste", "ef_id"] = "EF-WASTE-PLASTIC-INC"
    T["waste"] = w
    T["travel"] = raw["travel"]
    T["commuting_survey"] = raw["commuting"]
    T["shipments"] = raw["shipments"]
    T["sales"] = raw["sales"]
    p = raw["pcfs"]
    T["pcf_used"] = p.rename(columns={"value": "kgco2e_per_kg"})[["year", "supplier_id", "material_id", "kgco2e_per_kg"]] if len(p) else p
    T["farm_footprints"] = naive_farm_footprints(raw, erp)
    return T


def naive_farm_footprints(raw: dict, erp: pd.DataFrame) -> pd.DataFrame:
    """Farm-specific footprint from the survey (as reported) x delivered kg from ERP.
    Non-respondents get the crop-year average of respondents."""
    sv = raw["farm_survey"].copy()
    sv["organic_soil"] = sv.soil_type_reported.str.lower().str.startswith("organic")
    sv["kg_ha"] = farm_footprint_per_ha(sv)
    sv["kg_per_kg"] = sv.kg_ha / (sv.yield_t_ha * 1000)
    crop_mat = {"M100": "turnip_rape", "M110": "pea", "M111": "potato", "M112": "carrot", "M113": "spinach"}
    d = erp[erp.material_id.isin(crop_mat)].copy()
    d["crop"] = d.material_id.map(crop_mat)
    d = d.groupby(["supplier_id", "crop", "year"]).qty_kg.sum().reset_index().rename(columns={"supplier_id": "farm_id"})
    d = d.merge(sv[["farm_id", "crop", "year", "kg_per_kg"]], on=["farm_id", "crop", "year"], how="left")
    avg = sv.groupby(["crop", "year"]).kg_per_kg.median()
    d["kg_per_kg"] = d.kg_per_kg.fillna(pd.Series(list(zip(d.crop, d.year))).map(avg))
    d["tco2e"] = d.qty_kg * d.kg_per_kg / 1000
    d["region"] = "FI_SW"
    return d[["farm_id", "crop", "year", "region", "tco2e"]]
