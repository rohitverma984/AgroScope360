# Nature: SBTN-style assessment

The brief asks for a system that combines emissions, raw-material and geospatial data to
prioritise nature-related impacts and dependencies, such as biodiversity, eutrophication and
water availability. It also asks that the system be built so geospatial data can be added later.

## Data

| File | Content |
|---|---|
| `06_nature/parcels.geojson`, `01_master/parcels.csv` | Synthetic parcels with farm, soil class (soil map, ~88 % accurate), clay %, slope, distance to water, drainage, latest soil-P test (18 % missing), buffer strip and catchment |
| `03_farming/parcel_crop_history_and_plan.csv` | Crop and catch crop per parcel and year, 2012–2026, plus the 2027–2031 plan |
| `06_nature/catchments.geojson`, `catchments.csv` | Catchment polygons; receiving-water type; ecological status class; retention estimate; P sensitivity; total field area |
| `06_nature/monitored_catchment_loads.csv` | Outlet P and N loads at 15 stations, 2019–2025 (±10–15 %). These include non-contract farmland and natural background. |
| `06_nature/origin_state_of_nature_indicative.csv` | Indicative state-of-nature categories for import origins (water stress, deforestation/conversion risk, biodiversity sensitivity, nutrient status) |

The geometries are synthetic. The coordinates are placed in the real sourcing regions, so the same
pipeline will run on real layers:

* **Finland:** Finnish Food Authority field parcels; SYKE catchments, Corine land cover and Natura 2000 (CC BY 4.0).
* **Imports:** WRI Aqueduct 4.0 (CC BY 4.0) and GFW tree-cover loss (CC BY 4.0).
* **Not redistributed, because of their licences:** EXIOBASE, the NHM Biodiversity Intactness Index and IBAT/KBA data.

## Mapping to SBTN steps

| SBTN step | In this dataset |
|---|---|
| 1a Materiality screening (ENCORE pressures) | Materials and commodities × pressure categories: land use, water use, nutrient pollution, GHG, pesticides. Note: soy is on SBTN's High Impact Commodity List, and dairy and meat come from cattle. |
| 1b Value-chain assessment | Volumes by origin from ERP, contract parcels, FLAG emissions |
| 2 Interpret and prioritise | **Task D1**: pressure × state of nature at catchment level |
| 3 Targets | Freshwater quality: the limiting nutrient in Finnish lakes is often phosphorus. Land: organic soils and land conversion. |
| 4–5 Act and track | Levers L09–L12 and L24; monitoring stations |

## D1 priority formula

`priority = (P / median(P) + 0.5 × N / median(N)) × state_weight × p_sensitivity`

* **P and N:** the phosphorus and nitrogen that Apetit-contract parcels deliver to receiving water in 2025 (kg/yr), after delivery from field to water and catchment retention.
* **state_weight:** good 1.0, moderate 1.2, poor 1.5, bad 1.8.
* **p_sensitivity:** from `catchments.csv`. It is high for a clear lake in good status that is under protection, because preventing deterioration counts as much as restoring a degraded lake.

The hidden part is the *true* load. Estimate it from parcel attributes, crops, fertilisation, weather
and the monitored outlet loads. The ranking logic itself is public.
