# Data dictionary

Auto-generated from the files in `data/`. Raw feeds contain planted data-quality issues by design.

## `01_master/sites.csv`

Group sites (public facts; coordinates approximate except Säkylä).

Rows: 5

| Column | Type | Example | Description |
|---|---|---|---|
| `site_id` | str | S-SAK | Site code |
| `name` | str | Säkylä plant | Site name |
| `country` | str | FI | ISO country |
| `lat` | float64 | 61.078744 | Latitude (WGS84) |
| `lon` | float64 | 22.253773 | Longitude (WGS84) |
| `activity` | str | frozen vegetables, frozen foods, ready m | Main activity |
| `in_group_from` | int64 | 1990 | First year in group |
| `in_group_to` | float64 | 2026.0 | Last year (closure/divestment decided), empty if ongoing |

## `01_master/materials.csv`

Material master. ERP texts partly Finnish (as in Apetit's ERP sample).

Rows: 48

| Column | Type | Example | Description |
|---|---|---|---|
| `material_id` | str | M100 | Material code |
| `erp_name` | str | Rypsi/rapsi siemen, kotimainen sopimus | ERP material text |
| `name_en` | str | Rapeseed/turnip rape, FI contract grower | English name |
| `material_group` | str | oilseed | Group |
| `base_uom` | str | kg | Base unit (kg or EUR for spend-based) |
| `default_ef_id` | str | FARM | Default emission factor (FARM = farm-specific footprint) |
| `receiving_site` | str | S-KAN | Receiving plant |
| `origin_countries` | str | FI | Typical origin countries (;-separated) |
| `eudr_commodity` | bool | False | In EU Deforestation Regulation scope |
| `sbtn_high_impact_commodity` | bool | False | On / derived from SBTN High Impact Commodity List |

## `01_master/suppliers.csv`

Supplier master (synthetic names).

Rows: 86

| Column | Type | Example | Description |
|---|---|---|---|
| `supplier_id` | str | SUP001 | Supplier code |
| `supplier_name` | str | Supplier 001 (synthetic) | Placeholder name |
| `supplier_type` | str | grain_trader | grain_trader / manufacturer / service_provider |
| `country` | str | FI | Supplier country |
| `material_id` | str | M101 | Material supplied |
| `sbti_status` | str | targets_set | Supplier climate-target status |
| `provides_pcf` | bool | False | Supplier provides product carbon footprints (PACT) |
| `cdp_score` | str | D | Supplier CDP climate score |

## `01_master/emission_factor_library.csv`

Emission-factor library with provenance. See SOURCES_AND_LICENCES.md for value_status.

Rows: 84

| Column | Type | Example | Description |
|---|---|---|---|
| `ef_id` | str | EF-RAP-EE | Factor id |
| `name` | str | Rapeseed, at farm gate, Estonia | Description |
| `unit` | str | kg | Activity unit |
| `kgco2e_per_unit` | float64 | 1.31 | kg CO2e per unit (AR6 GWP100) |
| `flag_share` | float64 | 0.86 | Share of factor that is FLAG (land-based) |
| `luc_included` | bool | False | Statistical land-use change included |
| `source_type` | str | lca_database | Type of source |
| `reference_source` | str | Agri-footprint / national LCA studies | Real-world source this factor stands in for |
| `geography` | str | EE | Geography |
| `version` | int64 | 2025 | Factor version (year) |
| `value_status` | str | calibrated_synthetic | public_value / partner_supplied / calibrated_synthetic |
| `gwp_set` | str | IPCC AR6 GWP100 | GWP set |

## `01_master/farm_registry.csv`

Contract-farm registry (FI vegetables, FI oilseeds, SE peas).

Rows: 680

| Column | Type | Example | Description |
|---|---|---|---|
| `farm_id` | str | F0001 | Farm id (F = Finland, S = Sweden) |
| `segment` | str | veg | veg / oil / se_pea |
| `region` | str | FI_SW | FI_SW / SE_SKANE |
| `country` | str | FI | Country |
| `lat` | float64 | 61.00931 | Farm centre latitude |
| `lon` | float64 | 22.53619 | Farm centre longitude |
| `organic_certified` | bool | False | Certified organic production |
| `livestock` | bool | False | Farm has livestock (manure) |
| `joined_year` | int64 | 1997 | Year contract relationship started |
| `contract_crops` | str | pea | Contract crops (;-separated) |

## `01_master/parcels.csv`

Field parcels (attributes of parcels.geojson). Soil from a soil map, not field truth.

Rows: 14,213

| Column | Type | Example | Description |
|---|---|---|---|
| `parcel_id` | str | F0001-P01 | Parcel id |
| `farm_id` | str | F0001 | Farm id |
| `lat` | float64 | 61.03505 | Parcel centroid latitude |
| `lon` | float64 | 22.51367 | Parcel centroid longitude |
| `area_ha` | float64 | 6.66 | Area (ha) |
| `soil_class_soilmap` | str | clay | Soil class from soil map (clay/silt/fine_sand/sand/organic), ~88 % accurate |
| `clay_pct_soilmap` | float64 | 48.0 | Clay content estimate (%) |
| `slope_pct` | float64 | 2.3 | Mean slope (%) |
| `dist_to_water_m` | int64 | 404 | Distance to nearest water body / main ditch (m) |
| `drainage` | str | open_ditch | subsurface / open_ditch |
| `catchment_id` | str | CA28 | Catchment id |
| `p_test_mgl_latest` | float64 | 6.4 | Latest soil P test (mg/l, acid ammonium acetate); empty = missing |
| `buffer_strip` | bool | False | Buffer strip along water |

## `01_master/climate_grid_cells.csv`

Climate grid cells (0.25 degree).

Rows: 84

| Column | Type | Example | Description |
|---|---|---|---|
| `cell_id` | str | GF0000 | Cell id |
| `region` | str | FI_SW | Region |
| `lat` | float64 | 60.725 | Cell centre latitude |
| `lon` | float64 | 21.625 | Cell centre longitude |
| `continentality` | float64 | 0.056 | 0 = coastal .. 1 = inland |
| `elevation_m` | float64 | 5.0 | Mean elevation (m) |

## `02_raw_feeds/erp_purchase_lines_2021_2025.csv`

ERP purchase lines (goods receipts / invoices). Raw: contains planted issues.

Rows: 7,427

| Column | Type | Example | Description |
|---|---|---|---|
| `doc_no` | int64 | 4500000470 | Document number |
| `line_no` | int64 | 10 | Line |
| `posting_date` | str | 2021-01-01 | Posting date |
| `company_code` | str | C200 | C100 Apetit Oyj, C200 Kasviöljy (Kantvik), C400 Foodhills (SE) |
| `plant` | str | S-KAN | Site |
| `material_id` | str | M101 | Material |
| `material_text` | str | Rypsi/rapsi siemen, kotimainen kauppa | Material text as on the document |
| `supplier_id` | str | SUP002 | Supplier or contract farm |
| `quantity` | float64 | 23308.0 | Quantity in `uom` |
| `uom` | str | KG | KG / TO (tonnes; vessel lots) / EUR (spend items) |
| `net_amount` | float64 | 8657.94 | Net amount in `currency` |
| `currency` | str | EUR | EUR / SEK / USD |
| `origin_country` | str | FI | Origin country |
| `lot_id` | str | V20210239M101 | Lot (V = vessel, L = farm oilseed, G = vegetable intake) |
| `movement_type` | int64 | 101 | 101 = receipt, 122 = return to supplier (credit, legitimate) |
| `reference_doc` | float64 | 4500000723.0 | Original document for returns |
| `wbs_element` | str | Biosteam plant (wood chips / side stream | Capex project |

## `02_raw_feeds/energy_meter_readings.csv`

Monthly meter readings (electricity, purchased steam/heat, biogas, wood chips, side streams, natural gas). Raw.

Rows: 610

| Column | Type | Example | Description |
|---|---|---|---|
| `site_id` | str | S-SAK | Site |
| `year` | int64 | 2019 | Year |
| `month` | int64 | 1 | Month |
| `carrier` | str | electricity | Energy carrier |
| `value` | float64 | 1271.112 | Reading |
| `unit` | str | MWh | Unit (MWh) |

## `02_raw_feeds/fuel_deliveries.csv`

Fuel deliveries in native units (LNG/LPG in t, oil/diesel in litres). Raw.

Rows: 263

| Column | Type | Example | Description |
|---|---|---|---|
| `delivery_id` | str | FD00001 | Delivery id |
| `site_id` | str | FLEET | Site (FLEET = vehicles) |
| `carrier` | str | diesel | Fuel |
| `year` | int64 | 2019 | Year |
| `delivery_date` | str | 2019-06-01 | Date |
| `quantity` | float64 | 21.133 | Quantity |
| `unit` | str | l | t or l |

## `02_raw_feeds/fuel_stock_changes.csv`

Year-end tank stock change. Consumption = deliveries - stock_change.

Rows: 27

| Column | Type | Example | Description |
|---|---|---|---|
| `site_id` | str | FLEET | Site |
| `carrier` | str | diesel | Fuel |
| `year` | int64 | 2019 | Year |
| `unit` | str | l | Unit |
| `stock_change` | float64 | -2786.751 | Closing minus opening stock |
| `note` | str | closing stock minus opening stock; consu | Note |

## `02_raw_feeds/goo_cancellations.csv`

Guarantee-of-origin cancellations. Raw.

Rows: 19

| Column | Type | Example | Description |
|---|---|---|---|
| `year` | int64 | 2020 | Consumption year claimed |
| `site_id` | str | S-SAK | Site |
| `mwh_cancelled` | float64 | 19800.0 | MWh cancelled |
| `technology` | str | wind | Technology |
| `production_country` | str | FI | Production country |
| `vintage_year` | int64 | 2020 | Production (vintage) year |

## `02_raw_feeds/heat_supplier_factors.csv`

Supplier-specific emission factors for purchased steam / district heat.

Rows: 13

| Column | Type | Example | Description |
|---|---|---|---|
| `site_id` | str | S-SAK | Site |
| `year` | int64 | 2019 | Year |
| `supplier` | str | Heat supplier SAK | Supplier |
| `t_per_mwh` | float64 | 0.33 | t CO2e per MWh |

## `02_raw_feeds/refrigerant_service_log.csv`

Refrigerant service events (top-ups). Raw.

Rows: 84

| Column | Type | Example | Description |
|---|---|---|---|
| `site_id` | str | S-SAK | Site |
| `system` | str | Main freezing plant | Cooling system |
| `refrigerant` | str | R717_ammonia | Gas code |
| `year` | int64 | 2019 | Year |
| `service_date` | str | 2019-05-20 | Date |
| `reason` | str | leak repair | Reason |
| `event_id` | str | RS00001 | Event id |
| `kg_added` | float64 | 55.35 | kg added |

## `02_raw_feeds/waste_transfer_notes.csv`

Monthly waste transfer notes. Raw.

Rows: 1,008

| Column | Type | Example | Description |
|---|---|---|---|
| `transfer_note` | str | WT000001 | Note id |
| `site_id` | str | S-SAK | Site |
| `year` | int64 | 2019 | Year |
| `month` | int64 | 1 | Month |
| `waste_stream` | str | vegetable_biowaste | Stream |
| `treatment` | str | anaerobic_digestion | Treatment |
| `quantity` | float64 | 851619.0 | Quantity |
| `unit` | str | kg | kg |

## `02_raw_feeds/wastewater_third_party.csv`

Wastewater to municipal treatment.

Rows: 22

| Column | Type | Example | Description |
|---|---|---|---|
| `year` | int64 | 2019 | Year |
| `site_id` | str | S-PUD | Site |
| `m3` | int64 | 9600 | m3 |

## `02_raw_feeds/water_balance.csv`

Annual water withdrawals and discharges by source/destination.

Rows: 100

| Column | Type | Example | Description |
|---|---|---|---|
| `site_id` | str | S-SAK | Site |
| `year` | int64 | 2019 | Year |
| `flow` | str | withdrawal | withdrawal / discharge |
| `source_or_destination` | str | lake_water | Source or destination |
| `m3` | int64 | 47532 | m3 |

## `02_raw_feeds/travel_bookings.csv`

Travel bookings exported from the booking tool. Raw.

Rows: 3,532

| Column | Type | Example | Description |
|---|---|---|---|
| `year` | int64 | 2019 | Year |
| `traveller_id` | str | EMP025 | Pseudonymous traveller |
| `travel_date` | str | 2019-01-03 | Departure date |
| `mode` | str | flight | flight / train |
| `route` | str | HEL-AMS | Route |
| `pkm` | float64 | 3000.0 | Passenger-km (return) |
| `nights` | int64 | 1 | Hotel nights |
| `booking_id` | str | BK102196 | Booking id |

## `02_raw_feeds/goo_registry_statement.csv`

Guarantee-of-origin cancellations exported from the national registry (authoritative).

Rows: 55

| Column | Type | Example | Description |
|---|---|---|---|
| `cancellation_id` | str | GO-2020-SAK-01 | Cancellation id |
| `consumption_year` | int64 | 2020 | Consumption year the cancellation is for |
| `beneficiary_site` | str | S-SAK | Site |
| `mwh` | float64 | 6678.716 | MWh |
| `technology` | str | wind | Technology |
| `production_country` | str | FI | Production country |
| `production_period_start` | str | 2020-10-01 | Production period start |
| `production_period_end` | str | 2020-12-28 | Production period end |
| `issuing_body` | str | national registry (synthetic) | Issuing body |

## `02_raw_feeds/commuting_survey_2025.csv`

Employee commuting survey 2025 (respondents only). Raw.

Rows: 208

| Column | Type | Example | Description |
|---|---|---|---|
| `response_id` | str | CS0001 | Response id |
| `site_id` | str | S-SAK | Site |
| `one_way_km` | float64 | 6.6 | One-way distance (km) |
| `mode` | str | ev_car | Main mode |
| `days_on_site_per_week` | int64 | 4 | Days on site per week |
| `shift_worker` | bool | True | Shift worker |

## `02_raw_feeds/headcount.csv`

Year-end headcount by site.

Rows: 29

| Column | Type | Example | Description |
|---|---|---|---|
| `year` | int64 | 2019 | Year |
| `site_id` | str | S-SAK | Site |
| `headcount` | int64 | 217 | Headcount |

## `02_raw_feeds/shipments.csv`

Transport legs. Inbound legs reference ERP documents; outbound legs reference sales.

Rows: 11,617

| Column | Type | Example | Description |
|---|---|---|---|
| `shipment_id` | str | SH0000001 | Leg id |
| `year` | int64 | 2021 | Year |
| `direction` | str | inbound | inbound / outbound |
| `ref_doc` | str | 4500000001 | ERP doc_no or sales reference |
| `ef_id` | str | EF-TKM-TRUCK | Transport factor id |
| `mode` | str | truck | Mode |
| `t` | float64 | 13.079 | Tonnes |
| `km` | float64 | 82.2 | Distance (km) |
| `tkm` | float64 | 1075.09 | Tonne-km |

## `02_raw_feeds/frozen_warehousing.csv`

Third-party frozen warehousing.

Rows: 5

| Column | Type | Example | Description |
|---|---|---|---|
| `year` | int64 | 2021 | Year |
| `pallet_days` | float64 | 1468032.0 | Pallet-days |

## `02_raw_feeds/sales_volumes.csv`

Monthly sales by product group and market.

Rows: 1,440

| Column | Type | Example | Description |
|---|---|---|---|
| `year` | int64 | 2021 | Year |
| `month` | int64 | 1 | Month |
| `product_group` | str | frozen_vegetables | Product group |
| `site_id` | str | S-SAK | Producing site |
| `market` | str | FI | FI / SE / EXPORT_EU |
| `t_sold` | float64 | 2006.112 | Tonnes sold |
| `net_sales_eur` | float64 | 2736337.0 | Net sales (EUR) |

## `02_raw_feeds/capex_projects.csv`

Capital projects.

Rows: 15

| Column | Type | Example | Description |
|---|---|---|---|
| `year` | int64 | 2021 | Year |
| `site_id` | str | S-KAN | Site |
| `project` | str | Biosteam plant (wood chips / side stream | Project |
| `capex_type` | str | machinery | machinery / construction |
| `capex_eur` | float64 | 6500000.0 | EUR |

## `03_farming/farm_survey_fi.csv`

Finnish contract-farm survey (self-reported, farm x crop x year). ~42 % response before 2019, ~74 % after. Raw.

Rows: 3,437

| Column | Type | Example | Description |
|---|---|---|---|
| `survey_id` | str | FS00001 | Survey id |
| `farm_id` | str | F0001 | Farm |
| `crop` | str | pea | Crop |
| `year` | int64 | 2016 | Harvest year |
| `area_ha` | float64 | 4.05 | Reported area (ha) |
| `soil_type_reported` | str | Mineral soil | Farmer-reported soil type |
| `n_mineral_kg_ha` | float64 | 26.3 | Mineral N (kg/ha) |
| `n_manure_kg_ha` | float64 | 0.0 | Manure N (kg/ha) |
| `fertiliser_product` | str | NPK 20-3-8 | Main N product |
| `p_kg_ha` | float64 | 11.3 | P (kg/ha) |
| `diesel_l_ha` | float64 | 83.5 | Diesel (l/ha) |
| `lime_t_ha` | float64 | 0.0 | Lime (t/ha) this year |
| `sprays` | float64 | 2.0 | Plant-protection passes |
| `irrigated` | bool | False | Irrigated |
| `catch_crop_share` | float64 | 0.0 | Share of area with catch crop |
| `yield_t_ha` | float64 | 2.39 | Reported yield (t/ha) |

## `03_farming/foodhills_odlingsdata_se.csv`

Foodhills (SE) grower data 2018-2026 in the acquired company's format: Swedish headers, ';' separator, decimal comma.

Rows: 2,683

| Column | Type | Example | Description |
|---|---|---|---|
| `odlar_id` | str | S0381 | Grower id |
| `skördeår` | int64 | 2018 | Harvest year |
| `gröda` | str | Ärt (frysärt) | Crop |
| `areal_ha` | str | 7,31 | Area (ha) |
| `levererad_mängd_ton` | str | 14,91 | Delivered (t) |
| `kvävegiva_kg_ha` | int64 | 0 | N applied (kg/ha) |
| `diesel_l_ha` | int64 | 92 | Diesel (l/ha) |
| `bevattnad` | str | nej | Irrigated (ja/nej) |

## `03_farming/parcel_crop_history_and_plan.csv`

Crop per parcel and year: declared 2012-2026, planned 2027-2031.

Rows: 284,260

| Column | Type | Example | Description |
|---|---|---|---|
| `parcel_id` | str | F0001-P07 | Parcel |
| `farm_id` | str | F0001 | Farm |
| `year` | int64 | 2012 | Year |
| `crop` | str | pea | Crop |
| `catch_crop` | bool | True | Catch crop after main crop |
| `status` | str | declared | declared / planned |

## `03_farming/current_calculator_footprints.csv`

Footprints from the current calculator practice (mineral soil assumed; organic-soil emissions and LUC excluded).

Rows: 3,437

| Column | Type | Example | Description |
|---|---|---|---|
| `farm_id` | str | F0001 | Farm |
| `crop` | str | pea | Crop |
| `year` | int64 | 2016 | Year |
| `carbon_footprint_kgco2e_per_kg` | float64 | 0.31 | kg CO2e / kg harvested |
| `calculator_note` | str | current calculator: mineral soil assumed | Method note |

## `04_climate/weather_monthly_1991_2060.csv`

Monthly aggregates of the daily weather.

Rows: 139,104

| Column | Type | Example | Description |
|---|---|---|---|
| `cell_id` | str | GF0000 | Grid cell |
| `scenario` | str | historical | historical / ssp126 / ssp245 / ssp585 |
| `year` | int64 | 1991 | Year |
| `month` | int64 | 1 | Month |
| `tmean_c` | float64 | -4.4 | Mean temperature (C) |
| `tmax_c_max` | float64 | 2.4 | Highest daily max (C) |
| `precip_mm` | float64 | 29.1 | Precipitation (mm) |
| `pet_mm` | float64 | 2.69 | Potential evapotranspiration (mm) |
| `hot_days_tmax_ge_27` | int64 | 0 | Days with Tmax >= 27 C |

## `04_climate/climate_change_signals.csv`

Monthly change signals 2041-2060 vs 1991-2020 by SSP.

Rows: 36

| Column | Type | Example | Description |
|---|---|---|---|
| `scenario` | str | ssp126 | SSP |
| `period` | str | 2041-2060 vs 1991-2020 | Period |
| `month` | int64 | 1 | Month |
| `delta_tmean_c` | float64 | 2.2 | Temperature change (C) |
| `precip_factor` | float64 | 1.09 | Precipitation amount factor |
| `wetday_factor` | float64 | 1.03 | Wet-day frequency factor |

## `05_scenarios/transition_scenarios.csv`

NGFS-style transition scenarios (illustrative values).

Rows: 49

| Column | Type | Example | Description |
|---|---|---|---|
| `scenario` | str | net_zero_2050 | Scenario |
| `ngfs_category` | str | orderly | NGFS category |
| `narrative` | str | Immediate, ambitious policy; global net  | Narrative |
| `year` | int64 | 2025 | Year |
| `physical_pathway_proxy` | str | ssp126 | Matching SSP |
| `carbon_price_eur_t` | int64 | 80 | EU carbon price (EUR/t) |
| `eu_ets2_fuel_price_eur_t` | float64 | 0.0 | ETS2 price on fuels (EUR/t, from 2028) |
| `electricity_price_eur_mwh` | float64 | 62.0 | Electricity price (EUR/MWh) |
| `n_fertiliser_price_index` | float64 | 1.0 | N fertiliser price index (2025 = 1) |
| `diesel_price_index` | float64 | 1.0 | Diesel price index |
| `plant_based_demand_index` | float64 | 1.0 | Plant-based demand index |
| `frozen_veg_import_premium_pct` | float64 | 4.0 | Import premium (%) |
| `value_status` | str | illustrative (NGFS Phase V-consistent ra | Status |

## `05_scenarios/decarbonisation_levers.csv`

Lever catalogue (design estimates).

Rows: 30

| Column | Type | Example | Description |
|---|---|---|---|
| `lever_id` | str | L01 | Id |
| `name` | str | Secure biogas supply to eliminate LNG/LP | Lever |
| `scope` | str | scope1 | Scope/category |
| `flag` | bool | False | FLAG lever |
| `lever_type` | str | energy | Type |
| `abatement_tco2e_2030_design` | int64 | 1650 | Indicative abatement in 2030 at full ramp (t) |
| `capex_eur` | int64 | 150000 | Capex (EUR) |
| `opex_delta_eur_per_yr` | int64 | 180000 | Opex change (EUR/yr, negative = saving) |
| `lifetime_yr` | int64 | 10 | Lifetime (yr) |
| `earliest_start` | int64 | 2027 | Earliest start |
| `ramp_years` | int64 | 2 | Years to full effect |
| `confidence` | str | high | Confidence |
| `co_benefits` | str | air quality | Co-benefits |
| `trade_offs` | str | biogas price/availability | Trade-offs |
| `indicative_cost_eur_per_tco2e` | float64 | 118.0 | Annualised cost per t |
| `value_status` | str | design estimate for the hackathon; teams | Status |

## `06_nature/catchments.csv`

Catchments (synthetic geometry).

Rows: 42

| Column | Type | Example | Description |
|---|---|---|---|
| `catchment_id` | str | CA01 | Catchment |
| `region` | str | FI_SW | Region |
| `receiving_water_type` | str | lake | lake / river / coastal |
| `ecological_status_class` | str | good | WFD ecological status |
| `nutrient_retention_frac_estimate` | float64 | 0.358 | Estimated in-catchment retention |
| `catchment_area_km2` | float64 | 615.0 | Area (km2) |
| `field_area_total_ha` | float64 | 10689.0 | All field area incl. non-contract farms (ha) |
| `p_sensitivity` | float64 | 1.6 | Phosphorus sensitivity weight |
| `monitoring_station` | bool | True | Outlet monitoring station |

## `06_nature/monitored_catchment_loads.csv`

Monitored outlet loads (all sources).

Rows: 105

| Column | Type | Example | Description |
|---|---|---|---|
| `catchment_id` | str | CA01 | Catchment |
| `year` | int64 | 2019 | Year |
| `total_p_load_kg` | float64 | 5369.0 | P load (kg/yr) |
| `total_n_load_kg` | float64 | 109522.0 | N load (kg/yr) |
| `method` | str | flow-weighted sampling, ±10-15 % uncerta | Method |

## Other files

| File | Format | Content |
|---|---|---|
| `00_apetit_original/ApetitGroup_sample_data.xlsx` | xlsx | Apetit's sample workbook, unchanged (see APETIT_DATA_RECONCILIATION.md) |
| `02_raw_feeds/supplier_pcfs/*.json` | JSON | Supplier product carbon footprints, PACT Technical Specification v2-style. File name `{supplier}_{material}_{year}.json`. Raw. |
| `04_climate/weather_daily_1991_2060.parquet` | Parquet | Daily weather per cell: cell_id, date, tmean_c, tmax_c, tmin_c, precip_mm, rad_mj_m2, pet_mm, scenario |
| `06_nature/parcels.geojson` | GeoJSON (CRS84) | Parcel polygons with the attributes of parcels.csv |
| `06_nature/catchments.geojson` | GeoJSON (CRS84) | Catchment polygons |
| `05_scenarios/structural_events.csv` | CSV | Dated structural / regulatory events and their inventory relevance |
| `05_scenarios/published_inventory_history.csv` | CSV | Apetit's published totals 2019-2024 (public reports) |
| `05_scenarios/draft_report_summary_2025.csv` | CSV | A draft 2025 summary table as it might be typed into a report (raw) |
| `05_scenarios/contract_prices_and_replacement_premiums.csv` | CSV | Contract prices and replacement premiums |
| `06_nature/origin_state_of_nature_indicative.csv` | CSV | Indicative state-of-nature categories for import origins |
| `07_frameworks/framework_digest.md`, `source_registry.csv` | MD/CSV | Framework summaries (status 3 Nov 2026) and sources with licences |
