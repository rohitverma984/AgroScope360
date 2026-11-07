"""Reference baselines.  Deliberately simple: they show the mechanics and set a floor.

    python -m ccn_tools.baselines            # runs all baselines, writes outputs/, scores on dev keys
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import io as IO
from . import reference_calculator as RC
from . import score as SC

STATE_WEIGHT = {"good": 1.0, "moderate": 1.2, "poor": 1.5, "bad": 1.8}
APETIT_CROPS = ["pea", "potato", "carrot", "spinach", "turnip_rape"]


# ------------------------------------------------------------------ A1
def a1_rules(raw: dict) -> pd.DataFrame:
    """Price-ratio outliers and duplicates in ERP, energy-meter gaps/spikes, survey yield outliers."""
    out = []
    erp = raw["erp"].copy()
    erp["year"] = erp.posting_date.str[:4].astype(int)
    erp["qty_kg"] = np.where(erp.uom == "TO", erp.quantity * 1000, erp.quantity)
    goods = erp[(erp.uom != "EUR") & (erp.movement_type == 101) & (erp.qty_kg > 0)].copy()
    goods["unit_price"] = goods.net_amount / goods.qty_kg
    med = goods.groupby("material_id").unit_price.transform("median")
    goods["ratio"] = goods.unit_price / med
    for _, r in goods[(goods.ratio > 4) | (goods.ratio < 0.25)].iterrows():
        ratio = r.ratio
        if ratio > 300:
            t = "unit_error"
        elif 8 < ratio < 13 or 0.075 < ratio < 0.13:
            t = "decimal_shift"
        else:
            t = "material_mismatch"
        out.append(("erp_purchase_lines", f"erp:{r.doc_no}:{r.line_no}", t, r.year))
    key = ["supplier_id", "material_id", "quantity", "net_amount"]
    norm = erp[erp.movement_type == 101]
    dup = norm[norm.duplicated(key, keep="first")]
    for _, r in dup.iterrows():
        out.append(("erp_purchase_lines", f"erp:{r.doc_no}:{r.line_no}", "duplicate_record", int(r.posting_date[:4])))
    em = raw["energy_meter"].copy()
    for (site, carrier, year), g in em.groupby(["site_id", "carrier", "year"]):
        if len(g) >= 8:
            for m in sorted(set(range(1, 13)) - set(g.month)):
                out.append(("energy_meter_readings", f"energy:{site}:{year}-{m:02d}:{carrier}", "missing_record", year))
        medv = g.value.median()
        for _, r in g.iterrows():
            if medv > 0 and r.value > 200 * medv:
                out.append(("energy_meter_readings", f"energy:{site}:{year}-{int(r.month):02d}:{carrier}", "unit_error", year))
            elif medv > 0 and r.value > 2.4 * medv:
                out.append(("energy_meter_readings", f"energy:{site}:{year}-{int(r.month):02d}:{carrier}", "meter_spike", year))
    sv = raw["farm_survey"]
    medy = sv.groupby("crop").yield_t_ha.transform("median")
    for _, r in sv[sv.yield_t_ha > 3 * medy].iterrows():
        out.append(("farm_survey", f"farm_survey:{r.survey_id}", "outlier_implausible", r.year))
    return pd.DataFrame(out, columns=["table", "record_key", "issue_type", "year"]).drop_duplicates("record_key")


# ------------------------------------------------------------------ A2
def a2_naive(raw: dict, year: int) -> pd.DataFrame:
    T = IO.naive_canonical(raw)
    return RC.summarise(RC.compute_inventory(T, year))


# ------------------------------------------------------------------ C1
def c1_climatology(raw: dict, template: pd.DataFrame) -> pd.DataFrame:
    sv = raw["farm_survey"]
    sv = sv[sv.yield_t_ha < 3 * sv.groupby("crop").yield_t_ha.transform("median")]
    farm_mean = sv[sv.year >= 2016].groupby(["farm_id", "crop"]).yield_t_ha.mean()
    crop_mean = sv[sv.year >= 2016].groupby("crop").yield_t_ha.mean()
    se_default = {"pea": 3.4}
    sub = template.copy()
    pred = []
    for _, r in sub.iterrows():
        v = farm_mean.get((r.farm_id, r.crop), np.nan)
        if np.isnan(v):
            v = crop_mean.get(r.crop, se_default.get(r.crop, np.nan)) if r.region == "FI_SW" else se_default.get(r.crop, crop_mean.get(r.crop))
        pred.append(v)
    sub["yield_t_ha_pred"] = np.round(pred, 3)
    return sub


# ------------------------------------------------------------------ C2
def c2_null(template: pd.DataFrame) -> pd.DataFrame:
    sub = template.copy()
    sub["mean_yield_change_pct"] = 0.0
    sub["p_bad_year"] = 0.10
    return sub


# ------------------------------------------------------------------ D1
def d1_area(raw: dict, catchments: pd.DataFrame, year: int = 2025) -> pd.DataFrame:
    ch = raw["crop_history"]
    ch = ch[(ch.year == year) & ch.crop.isin(APETIT_CROPS)]
    par = raw["parcels"].set_index("parcel_id")
    ch = ch.join(par[["area_ha", "catchment_id"]], on="parcel_id")
    g = ch.groupby("catchment_id").area_ha.sum()
    c = catchments.set_index("catchment_id")
    p = (g.reindex(c.index).fillna(0) * 1.1 * (1 - c.nutrient_retention_frac_estimate))
    n = (g.reindex(c.index).fillna(0) * 15.0 * (1 - c.nutrient_retention_frac_estimate))
    score = (p / max(p.median(), 1e-6) + 0.5 * n / max(n.median(), 1e-6)) * c.ecological_status_class.map(STATE_WEIGHT) * c.p_sensitivity
    sub = pd.DataFrame(dict(catchment_id=c.index.values, region=c.region.values, apetit_p_to_water_kg=p.round(2).values,
                            apetit_n_to_water_kg=n.round(1).values))
    sub["priority_rank"] = score.rank(ascending=False, method="first").astype(int).values
    return sub


def main(root=None):
    root = Path(root) if root else IO.DEFAULT_ROOT
    raw = IO.load_raw(root)
    out = root / "outputs"
    out.mkdir(exist_ok=True)
    tasks = root / "tasks"
    res = {}
    a1 = a1_rules(raw)
    a1.to_csv(out / "A1_baseline_issues.csv", index=False)
    res["A1_dev"] = SC.score_a1(a1, pd.read_csv(tasks / "dev" / "A1_dev_issue_labels_2023_2024.csv"))
    for y in (2023, 2024):
        s = a2_naive(raw, y)
        s.to_csv(out / f"A2_baseline_inventory_{y}.csv", index=False)
        res[f"A2_dev_{y}"] = SC.score_a2(s, pd.read_csv(tasks / "dev" / f"A2_dev_inventory_{y}.csv"))["score"]
    a2_naive(raw, 2025).to_csv(out / "A2_baseline_inventory_2025.csv", index=False)
    c1 = c1_climatology(raw, pd.read_csv(tasks / "templates" / "C1_yields_2027_2031_submission.csv"))
    c1.to_csv(out / "C1_baseline_yields.csv", index=False)
    c2_null(pd.read_csv(tasks / "templates" / "C2_climate_yield_risk_submission.csv")).to_csv(out / "C2_baseline.csv", index=False)
    cat = pd.read_csv(root / "data" / "06_nature" / "catchments.csv")
    d1 = d1_area(raw, cat)
    d1.to_csv(out / "D1_baseline.csv", index=False)
    res["D1_dev"] = SC.score_d1(d1, pd.read_csv(tasks / "dev" / "D1_dev_catchments_2025.csv"))
    print(json.dumps(res, indent=1, default=str))
    return res


if __name__ == "__main__":
    main()
