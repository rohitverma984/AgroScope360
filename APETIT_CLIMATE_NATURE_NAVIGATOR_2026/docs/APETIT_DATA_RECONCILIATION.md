# Reconciliation of the Apetit sample workbook

File: `data/00_apetit_original/ApetitGroup_sample_data.xlsx`, received from Apetit on
2 October 2026 and included here unchanged. Apetit describes the figures as indicative, not exact
company data. This note records the arithmetic checks we ran on the workbook before using it to
anchor the simulation. It does not judge Apetit's reporting. The checks illustrate the work that
task A1 asks teams to automate.

## Checks that reconcile

| Check | Result |
|---|---|
| Scope 3 upstream categories 1–7 | Sum 201,818 t = stated "Total upstream" 201,818 t |
| Scope 3 downstream categories 9, 11, 12 | Sum 11,807 t = stated "Total downstream" 11,807 t |
| Scope 3 total from categories | 213,625 t vs stated 213,624 t (rounding) |
| Group total, market-based | 4,475 + 40 + 213,624 = 218,139 t vs stated 218,140 t (rounding) |
| Water consumption | Component withdrawals 956,077 m³ − component discharges 892,052 m³ = 64,025 m³ = stated consumption. Note: the components include "reused water" (11,187 m³). GRI 303 does not count internal reuse as a withdrawal. |
| Headcount | Permanent 300 + temporary 72 = 372 = full-time 354 + part-time 14 + non-guaranteed hours 4 |

## Checks that do not reconcile

| Item | Stated | From components | Likely explanation |
|---|---|---|---|
| "Scope 3" headline row | 231,624 t | 213,624 t (category total) | Digits transposed (31 ↔ 13). The group total uses 213,624. |
| Water withdrawal total | 965,077 m³ | 956,077 m³ | Digits transposed (56 ↔ 65). |
| Water discharge total | 854,101 m³ | 892,052 m³ | The total leaves out runoff water (892,052 − 854,101 = 37,951 = runoff). The consumption figure includes it. |
| Energy total | 80,829 MWh | 80,866 MWh | Difference of 37 MWh (0.05 %). Likely rounding or an unlisted carrier. |
| Permanent staff by gender | 300 | 152 + 130 = 282 | Possibly staff with gender not reported. The same pattern shows for full-time (337 vs 354) and part-time (13 vs 14). |

## Observations relevant to the challenge

* **Pea carbon footprints:** 30 growers, sampled from about 100.
  * Delivery-weighted mean 0.33 kg CO2e/kg; median 0.27; range 0.05–1.46.
  * Two growers (1.35 and 1.46) are about five times the median. Possible causes are a crop failure, a data-entry error, or emissions the calculator handles differently. A data-quality agent should route these to an expert, not drop them.
* **Soil and land-use change:**
  * Every pea footprint is labelled "Mineral soil" and excludes land-use change.
  * Drained organic soils emit about 29 t CO2/ha/yr under annual crops (Finnish GHG inventory). That is roughly 30–50 times a typical mineral-soil pea field.
  * If some contract fields are on organic soil, the footprints are understated. A soil map or parcel register is the way to check, which is why parcel geometries are part of this package.
* **Supplier factors:** "kg CO2e/kg product without Land Use Change". For soy protein isolate (5.0 kg/kg, China), land-use change can be material, because soy is a high-impact commodity for deforestation. The EU Deforestation Regulation sets its scope by HS code, and soy protein isolate (HS 3504) is not in Annex I. Soybeans, soy oil and soy meal are.
* **Farming location:** one example coordinate represents all contract farming. Nature-related assessment under SBTN needs locations at catchment level, so this package adds parcel-level geometry (synthetic).

## How the simulation uses the workbook

* **Scale anchors.** Group Scope 1/2/3, category totals, energy, water and headcount anchor the *scale* of the synthetic company.
  * The synthetic 2025 inventory is of the same order, but deliberately not equal, so copying the workbook does not answer task A2. Several categories differ by more than 20 %.
  * Part of the difference comes from documented method choices (categories 11 and 12; see METHODOLOGY.md). The rest comes from synthetic activity, such as a higher 2025 rapeseed crush.
  * The public 2023 and 2024 dev inventories in `tasks/dev/` show the synthetic company's level.
* **Lines kept as given.** The supplier lines (materials, countries, factors) are carried into the material master unchanged, with Apetit's factor values flagged `partner_supplied`.
* **Contract-farming volumes.** Areas and volumes calibrate the farm simulator.
* **Site coordinates.** The Säkylä coordinates are used as given.
