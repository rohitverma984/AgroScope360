"""Guided tour of the package: run from the tools/ folder:  python quickstart.py"""
import pandas as pd
from ccn_tools import io as IO, reference_calculator as RC, score as SC, baselines as BL

raw = IO.load_raw()
print("Raw tables:", {k: len(v) for k, v in raw.items()})

# 1) Naive inventory for 2024 vs the public dev truth
T = IO.naive_canonical(raw)
inv24 = RC.summarise(RC.compute_inventory(T, 2024))
key24 = pd.read_csv(IO.DEFAULT_ROOT / "tasks/dev/A2_dev_inventory_2024.csv")
print("\nA2 naive score on 2024 (dev):", SC.score_a2(inv24, key24)["score"])
print(inv24[inv24.scope == "total"])

# 2) Where do the problems hide? Price-per-kg outliers in ERP
erp = raw["erp"].copy()
erp["qty_kg"] = erp.quantity.where(erp.uom != "TO", erp.quantity * 1000)
g = erp[(erp.uom != "EUR") & (erp.qty_kg > 0)].assign(eur_per_kg=lambda d: d.net_amount / d.qty_kg)
print("\nUnit price spread by material (look at max/median):")
print(g.groupby("material_id").eur_per_kg.describe()[["50%", "max"]].sort_values("max", ascending=False).head(8))

# 3) Yields vs weather: Finnish pea median by year
sv = raw["farm_survey"]
print("\nFinnish pea yield (median t/ha) by year:")
print(sv[(sv.crop == "pea") & (sv.yield_t_ha < 10)].groupby("year").yield_t_ha.median().round(2).to_string())

# 4) Nature: contract area by catchment in 2025
ch = raw["crop_history"]
ch = ch[(ch.year == 2025) & ch.crop.isin(BL.APETIT_CROPS)].merge(raw["parcels"][["parcel_id", "area_ha", "catchment_id"]], on="parcel_id")
print("\nApetit contract-crop area by catchment (2025, top 10):")
print(ch.groupby("catchment_id").area_ha.sum().sort_values(ascending=False).head(10).round(0))
