# Assumptions and limitations

## What the data can and cannot tell you

* **Synthetic, calibrated, not Apetit's books.**
  * The 2025 Scope 1, Scope 2 and Scope 3 totals are close to the Apetit sample, but categories differ, some by more than 20 % (table in APETIT_DATA_RECONCILIATION.md). This is intended: copying the sample does not answer task A2.
  * Earlier years follow the public trajectory for Scope 1 and 2. Scope 3 for 2021–2024 deviates from the published figures, by up to about ±18 %, because the activity data is synthetic and the published figures include method changes and the divested grain trade.
  * Conclusions about the method transfer to the real company. Conclusions about absolute numbers do not.
* **Only some factors are public values.** The supplier and commodity factors marked `calibrated_synthetic` are plausible but invented. FLAG shares are design values.
* **Weather.**
  * Historical weather is synthetic and only *inspired by* real seasons. Do not compare it day by day with FMI or SMHI observations.
  * Only one realisation per SSP is given; the C2 truth uses a Monte Carlo ensemble.
  * No CO2 fertilisation effect is modelled.
  * No adaptation (new varieties, changed sowing windows beyond the temperature trigger) is modelled.
* **Yield model.** Its structure is deliberately learnable, but it is a simplification. It has no hail, frost after emergence or market-driven harvest decisions.
* **Nature.**
  * Catchments are Voronoi polygons and parcels are synthetic quadrilaterals, so they may overlap real water bodies on a basemap. Lake exclusion is approximate.
  * The nutrient-loss model is a simple export-coefficient model. It is not VEMALA.
  * Import-origin state-of-nature values are indicative categories.
* **Scope 3 categories 11 and 12** use explicit method choices (market-grid use phase; Finnish packaging treatment mix). They differ from the Apetit sample figures. Discuss the choice; do not just copy one.
* **Scenario prices** are illustrative values within NGFS Phase V ranges.
* **Lever abatement and costs** are design estimates for teaching. Recompute them from the data.
* **Not modelled:**
  * consumer-level food waste;
  * category 10 (processing of sold intermediates);
  * removals (for example soil carbon from catch crops), which are optional under the GHG Protocol LSR Standard and require monitoring;
  * biogenic CO2 from products.
* **Organic soils.**
  * About 6 % of the synthetic Finnish contract parcels are drained organic soils. This is a design assumption: the national share is about 11 %, and it is lower in south-west Finland. Apetit's real share is unknown; its own parcel data would settle it.
  * Because organic soils emit about 29 t CO2/ha/yr, even this share dominates contract-farm emissions in the dataset. This is the intended lesson, not a statement about Apetit's growers.
  * The farm-level classification is truth in the private files, but the public soil map is only about 88 % accurate. This is intentional.

## Known simplifications in the accounting

* Refrigerant top-ups are treated as emissions in the same year.
* A GoO counts for consumption year Y only if its production (vintage) year is Y. The internal log may contain typos; the registry statement is authoritative.
* Spend-based factors use 2025 euros without inflation adjustment.
* Commuting is based on one survey year (2025), scaled by headcount.
