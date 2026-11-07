# Tasks and scoring

The challenge brief asks for one thing: **turn fragmented climate and nature data into traceable
decisions about the future**. The tasks below break that into parts that can be checked.

* Teams may take on one track or several.
* The jury looks at demonstrated usefulness, sound reasoning and traceability, not at how many tasks a team covered.
* Auto-scores are evidence for the jury, not the verdict.

| Track | Task | Data | Auto-scored | Dev answers public |
|---|---|---|---|---|
| A Data → inventory | A1 Find and classify data-quality issues | 02_raw_feeds, 03_farming, 05_scenarios | yes (2025) | 2023–2024 labels |
| | A2 Compute the 2025 inventory with an audit trail | everything in 01–03 | yes (2025) | 2023 and 2024 inventories |
| B Pathways | B1 SBTi-aligned targets & pathway (incl. FLAG, base-year recalculation) | 05_scenarios, A2 output | rubric | — |
| | B2 Marginal abatement cost curve and action portfolio | levers, prices, scenarios | rubric | — |
| C Climate risk to farming | C1 Predict contract-crop yields for seasons 2027–2031 | 04_climate, 03_farming, 01_master | yes | — (backtest on history) |
| | C2 Climate yield risk 2041–2060 by SSP | 04_climate, 03_farming | yes | — |
| | C3 Translate C2 into € risk and adaptation options | prices, levers | rubric | — |
| D Nature (SBTN) | D1 Catchment nutrient pressure & priority ranking | 06_nature, 03_farming, 01_master | yes | 6 catchments |
| | D2 Value-chain materiality screening incl. imports | origin_state_of_nature, materials | rubric | — |
| E Copilot with audit trail | E Answer questions with evidence | all | numeric part yes | 3 dev questions |

## A1: data-quality issues

* **What to submit:** `tasks/templates/A1_issues_submission.csv` with one row per issue found in **2025 records**: `table, record_key, issue_type, confidence, explanation`. Add a `year` column if you also flag other years; rows with other years are ignored.
* **Issue types:** see `ISSUE_TYPES` below. Use exactly these strings.
* **Record keys:**

| Table / file | record_key format |
|---|---|
| erp_purchase_lines | `erp:{doc_no}:{line_no}` |
| energy_meter_readings (incl. missing months) | `energy:{site_id}:{YYYY-MM}:{carrier}` |
| fuel_deliveries | `fuel:{delivery_id}` |
| goo_cancellations | `goo:{site_id}:{year}` |
| refrigerant_service_log | `refrigerant:{event_id}` |
| waste_transfer_notes | `waste:{transfer_note}` |
| travel_bookings | `travel:{booking_id}`. A duplicate is a row with the same traveller, date, route, distance and nights as an earlier row in the file; flag the later row(s). |
| commuting_survey | `commute:{response_id}` |
| shipments (missing legs) | `ship:{ref_doc}:{ef_id}`, where ef_id is the expected missing leg's factor |
| farm_survey | `farm_survey:{survey_id}` |
| farm_registry | `farm:{farm_id}` |
| supplier_pcfs | `pcf:{supplier_id}:{material_id}:{year}` |
| draft_report_summary | `report:{year}:{line}` |

**ISSUE_TYPES:** unit_error, duplicate_record, currency_error, material_mismatch, decimal_shift,
missing_record, meter_spike, wrong_gas_code, certificate_mismatch, soil_misreport,
outlier_implausible, area_mismatch, coordinate_swap, pcf_unit_error, pcf_stale_period,
total_mismatch, missing_leg, mode_mislabel.

Legitimate edge cases are planted as well: credit notes, the vessel lots in tonnes (`uom = TO`), seasonal meter peaks and ammonia systems. Flagging them costs precision.

* **More than one issue on a record:** a record can carry two issue types. Any of them counts as the right type.
* **`soil_misreport`:** labelled when at least 30 % of a farm's crop area for that year lies on organic soil (true soil, which is not public) while the survey says "Mineral soil". Use the soil map and other evidence to decide.
* **GoO records:** the internal log is checked against `goo_registry_statement.csv`.

**Score.** 100 × F1 × (0.75 + 0.25 × type accuracy). Matching is on `record_key`.

## A2: 2025 inventory

* **What to submit:** `A2_inventory_2025_submission.csv`, with tCO2e for every `category` row in the template.
* **Scoring:**
  * Each line earns credit max(0, 1 − |error|/5 %).
  * Weights: Scope 1 15 %, Scope 2 location-based 3 %, Scope 2 market-based 12 %, Scope 3 total 20 %, category 1 20 %, category 4 8 %, other categories 22 % combined.
* **The Apetit sample is not the answer.** The synthetic company is close to the Apetit sample in scale, but not equal to it. Copying the sample scores poorly.
* **Audit trail is required for the jury:**
  * every number traces to source records;
  * every correction is logged with its reason;
  * the factor used and its source are recorded.
* **Checking yourself:** the 2023 and 2024 truths are public, so you can validate your pipeline end to end.

## B1/B2: pathways (rubric)

The jury expects:

* base year and recalculation logic (grain-trade divestment, Foodhills acquisition, Pudasjärvi, Kantvik steam);
* a FLAG/non-FLAG split;
* SBTi-rate targets (Scope 1+2 4.2 %/yr, Scope 3 2.5 %/yr, FLAG 3.03 %/yr; V1.3.1 vs V2 timing);
* a pathway under at least two transition scenarios;
* a MACC with honest uncertainty;
* recognition that measurement improvements (lever L27) are not reductions.

## C1: yields 2027–2031

* **The setting:** weather for 2027–2031 is one SSP2-4.5 realisation in `04_climate` (scenario `ssp245`). Crop plans are in `parcel_crop_history_and_plan.csv` (status `planned`).
* **What to submit:** `yield_t_ha_pred` for every parcel-year row in the template.
* **Score:**
  * 60 % aggregate production error: MAPE of Σ(area × yield) by region × crop × year, full credit at 0 % and none at 15 %.
  * 40 % parcel-level nRMSE: full credit at 0, none at 0.35.

## C2: climate yield risk 2041–2060

* **What to submit:** per region × crop × SSP, `mean_yield_change_pct` (relative to 1991–2020) and `p_bad_year` (share of years below 80 % of the 1991–2020 mean).
* **Hidden truth:** a Monte Carlo over the truth model, using the 2025 contract-parcel mix and current irrigation and management.
* **Score:**
  * 70 % MAE of the yield change (none at 5 percentage points);
  * 30 % MAE of p_bad_year (none at 0.1).

## D1: catchment priority (2025)

* **What to estimate:** for every catchment, the phosphorus and nitrogen that Apetit-contract parcels deliver to receiving waters in 2025 (`apetit_p_to_water_kg`, `apetit_n_to_water_kg`), plus a `priority_rank`.
* **Priority formula (SBTN-style pressure × state):**

  `priority = (P / median(P) + 0.5 × N / median(N)) × state_weight × p_sensitivity`

  * state_weight: good 1.0, moderate 1.2, poor 1.5, bad 1.8.
  * p_sensitivity is given in `catchments.csv`.
* **Calibration data:** outlet loads at 15 monitored catchments for 2019–2025. These include non-contract farmland and natural background.
* **Dev file:** `tasks/dev/D1_dev_catchments_2025.csv` gives the true loads for 6 catchments. These 6 are excluded from the test score.
* **Score (catchments with Apetit sourcing):**
  * 10 % Spearman ρ of rank;
  * 10 % top-5 overlap;
  * 40 % MAE of log10(P), none at 0.15 (a factor of 1.4);
  * 40 % MAE of log10(N), none at 0.15.
* **Why loads weigh most:** contract area alone already orders catchments roughly. The value lies in estimating *how much* phosphorus and nitrogen reach the water, field by field.

## E: questions with evidence

* **Questions:** `tasks/E_questions.csv`.
* **Numeric answers:** auto-checked against relative tolerances.
* **Rubric questions:** judged on correctness and on citing a source document.
* **Evidence:** answers without evidence (record keys, file and row, standard and section) get no rubric credit.

## Jury rubric (all tracks)

Apetit's experts judge every submission on these criteria, taken from the challenge brief:

| Criterion | Weight | What earns full marks |
|---|---|---|
| Usefulness for decisions | 30 % | Output an Apetit expert could act on next week: priorities, € and t figures, recommended actions with owners |
| Sound reasoning | 25 % | Correct use of GHG Protocol, SBTi, SBTN and scenario logic. Assumptions stated. Method changes not presented as reductions. |
| Traceability and expert review | 25 % | Every number links to source records and factors. Corrections are logged. A human approves before results are published. |
| Reliability | 10 % | Auto-scored results where applicable; robustness to the planted data issues |
| Technical quality | 10 % | Runs end to end from the raw package; reproducible; fits or maps onto Apetit's Microsoft stack |

Track-specific checklists (B pathways, C3 € risk, D2 screening) are in SCENARIOS_AND_RISK.md and NATURE_SBTN.md.

## What to submit

Submit through the hackathon platform by the deadline in the event guide (sinceai.ai/hackathon-2026/guide). Include:

1. A code repository link with a README that reproduces your results from the unzipped package.
2. The CSV files for the auto-scored tasks you attempted, using the names in `tasks/templates/`.
3. A short demo (live or recorded) and slides: problem → approach → evidence → what Apetit should do.
4. A one-page method note: data sources, assumptions, limitations, and how expert review works in your solution.

## Reference baselines (dev results)

| Baseline | Dev score | Note |
|---|---|---|
| A1 rules (price ratio, duplicates, meter gaps/spikes, yield outliers) | 52.17 (F1 0.5284) | 2023–2024 labels |
| A2 naive pipeline + reference calculator | 2023: 25.54, 2024: 23.24 | no cleaning at all |
| D1 contract area × state weight | 12.0 | 6 dev catchments |
| C1 farm historical mean yield | backtest yourself | ignores weather |
| C2 'no change' | — | null model |

Run them with `cd tools && python -m ccn_tools`. The baselines are deliberately simple.
