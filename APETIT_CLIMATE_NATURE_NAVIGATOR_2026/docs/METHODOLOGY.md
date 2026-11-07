# Methodology: how the "truth" is calculated

This is the canonical method behind the hidden answer keys. `tools/ccn_tools/reference_calculator.py`
implements the same method. Clean input gives the right answer; raw input passes every
data-quality problem straight through.

Standards: GHG Protocol Corporate Standard, Scope 2 Guidance and Scope 3 Standard; IPCC AR6
GWP100 (N2O 273, fossil CH4 29.8); IPCC 2019 Refinement for agricultural N2O.

## 1. Organisational boundary and structural changes

* **Consolidation:** operational control.
* **Grain trade, divested 31 May 2022.** It appears in the published history (`05_scenarios/published_inventory_history.csv`) but is not in the activity data and is outside the canonical 2021–2025 inventory. That inventory covers continuing operations only, so base-year recalculation is part of task B.
* **Foodhills (Bjuv, Sweden), acquired 27 Nov 2025.**
  * Its own operations are included from December 2025.
  * Its pea growers delivered before the acquisition, so Swedish farm emissions are **not** in the 2025 inventory. They are in full from 2026.
  * Because of the acquisition, a base-year recalculation is needed.
* **Pudasjärvi (closure decided 2026) and the sale of the Kantvik biosteam plant (closing early 2027)** are future structural changes. They belong in pathway modelling (task B), not in the 2025 inventory.

## 2. Canonical tables (input to the reference calculator)

| Table | Key columns | Notes |
|---|---|---|
| `energy` | site_id, year, carrier, mwh | Fuels in MWh (NCV). Fuel deliveries are converted with: LNG 13.5 MWh/t, LPG 12.8 MWh/t, light fuel oil 0.0100 MWh/l, diesel 0.0099 MWh/l. Consumption = deliveries − stock change. |
| `refrigerants` | site_id, year, refrigerant, kg_added | Top-up mass equals emitted mass (mass-balance simplification). |
| `goo` | site_id, year, mwh_cancelled, vintage_year | Counts for year Y only if vintage_year = Y. Volume is capped at the site's consumption. `goo_cancellations.csv` is an internal manual log; `goo_registry_statement.csv`, the national registry export, is authoritative. The leased head office has no GoO coverage (landlord contract). |
| `heat_suppliers` | site_id, year, t_per_mwh | Supplier-specific factor for market-based purchased steam/heat. |
| `purchases` | year, material_id, supplier_id, qty_kg, amount_eur | Credit notes (movement 122) are legitimate and net against receipts. |
| `pcf_used` | year, supplier_id, material_id, kgco2e_per_kg | Valid supplier PCFs only (see §4). |
| `farm_footprints` | farm_id, crop, year, region, tco2e | Contract-farm emissions allocated to delivered kg (§5). |
| `shipments` | year, direction, ef_id, tkm | Inbound legs give category 4; outbound legs give category 9. |
| `warehousing` | year, pallet_days | Third-party frozen storage (category 9). |
| `waste`, `wastewater` | t / m3 per stream and treatment | Category 5. |
| `travel`, `commuting_survey`, `headcount` | — | Categories 6 and 7. |
| `sales` | year, product_group, market, t_sold | Categories 11 and 12. |

## 3. Scope 1 and 2

* **Combustion:** MWh × fossil CO2 factor (t/MWh): LNG 0.1991, natural gas 0.2009, LPG 0.2336, light fuel oil 0.2668, diesel (Finnish average bio-blend) 0.2110. Sources: Statistics Finland fuel classification 2025, converted from t/TJ.
* **Biogenic CO2:**
  * It is reported separately as a memo item, not in Scope 1.
  * Factors: wood chips 0.4032, oilseed side streams 0.45, biogas 0.198, plus the bio share of diesel.
* **Refrigerants:** kg × GWP100 (AR6). The gas codes are R717 ammonia (GWP 0), R744 CO2 (1), R404A (4,728), R449A (1,504), R134a (1,530) and R410A (2,256). Ammonia is not a greenhouse gas: a leak is a safety issue, not a CO2e issue.
* **Scope 2, location-based:**
  * Electricity: MWh × national production factor. Finland 2019–2025 (kg/kWh): 0.090, 0.068, 0.075, 0.066, 0.038, 0.030, 0.026. Sweden: 0.012.
  * Purchased heat: MWh × national district-heat average.
* **Scope 2, market-based:**
  * Electricity: (MWh − valid GoO MWh) × residual mix. Finland, from AIB: 0.406 in 2024, with a design value for 2025. Sweden: 0.035.
  * Purchased heat: MWh × supplier-specific factor.

## 4. Scope 3

| Category | Method |
|---|---|
| 1 Goods | kg × factor. Hierarchy: (1) valid supplier PCF, (2) material default factor from `emission_factor_library.csv`. Contract farming: farm-specific footprints (§5). |
| 1 Services | Spend (EUR) × EEIO-style factor. |
| 2 Capital goods | Capex spend × EEIO-style factor (no depreciation). |
| 3 Fuel & energy | Fuel MWh × well-to-tank factor + electricity MWh × upstream & T&D factor + purchased heat × upstream factor. |
| 4 Upstream transport | Inbound tkm × WTW factor per mode (GLEC-style). Every import lot has a road leg plus a sea or Ro-Pax leg where relevant. |
| 5 Waste | t × treatment factor; third-party wastewater m3 × factor. Spent bleaching earth goes to co-digestion/landfill. |
| 6 Business travel | Flight and rail pkm × factor + hotel nights. |
| 7 Commuting | 2025 survey: mean annual kg per respondent × site headcount. |
| 9 Downstream transport | Outbound tkm (reefer for frozen goods) + third-party frozen warehousing pallet-days. |
| 11 Use of sold products | Indirect use phase: consumer freezer storage (~45 days) plus cooking energy (kWh/kg by product group) × grid factor of the market where the product is sold. Apetit's sample reports 6,708 t; the location-based grid choice here gives a much lower figure. That is a method choice to discuss, not an error. |
| 12 End of life | Packaging put on market (kg/t by product group) × Finnish treatment mix: plastics 65 % incineration (2.15 t CO2/t), 35 % recycling; board 85 % recycling. This is higher than Apetit's sample (462 t). |
| 8, 10, 13–15 | Not calculated. Category 10 (processing of sold intermediate products: oil, meal) should be screened and its exclusion justified. That is part of task B. |

**Supplier PCFs** come in the PACT v2-style JSON format (`02_raw_feeds/supplier_pcfs/`). A PCF is valid
for year *Y* only if its reference period covers *Y* and its values are per declared unit (kg).

## 5. Contract-farm footprint (cradle to farm gate, per hectare)

| Source | Formula |
|---|---|
| Fertiliser manufacture | N × 3.7 kg CO2e/kg N (AN, Yara verified ≈ 3.73), or 0.9 for low-carbon AN; P × 1.6; K (= 2.2 × P) × 0.5 |
| Direct N2O (FLAG) | (N_mineral × 0.016 + (N_manure + N_residues) × 0.006) × 44/28 × 273 (IPCC 2019 wet climate) |
| Indirect N2O (FLAG) | [(N_min × 0.05 + N_man × 0.21) × 0.014 + (N_min + N_man + N_res) × 0.24 × 0.011] × 44/28 × 273 |
| Diesel | litres × (2.10 Finnish average blend or 2.45 Swedish, combustion + 0.61 WTT) |
| Liming (FLAG) | t × 0.44 t CO2/t |
| Drained organic soils (FLAG) | 29.0 t CO2/ha/yr for annual crops (20.9 for grass) + 13 kg N2O-N/ha/yr (Finnish GHG inventory; IPCC Wetlands Supplement) |
| Pesticides | 8 kg CO2e per spray pass |
| Electricity | Storage/drying kWh/t × yield + 180 kWh/ha if irrigated, × grid factor |

* Residue N per tonne of product is given in `tools/ccn_tools/factors.py` (`RESIDUE_N_PER_T`). Biological N fixation by peas is not an N input.
* **Allocation:** farm emissions for the crop are divided by delivered kg. Intake rejections stay with the delivered product.
* **FLAG (SBTi) part:** direct and indirect N2O, organic soils and liming. Fertiliser manufacture, diesel, electricity and pesticides are non-FLAG.
* **FLAG share of purchased commodities:** each library factor carries a `flag_share`.
* **Organic soils are included.** Finnish cropland is about 11 % organic soils nationally (Luke) and less in south-west Finland. The `current_calculator_footprints.csv` file reproduces the current practice, which assumes mineral soil and excludes these emissions, so teams can compare the two.

## 6. Weather, yields and nature (simulation, not accounting)

The generators behind the weather, crop yields and nutrient losses are described in SIMULATION_DESIGN.md.
The SBTN-style prioritisation formula used in task D1 is in NATURE_SBTN.md.
