# Apetit × Since AI 2026 — Climate & Nature Navigator

**Synthetic dataset, v1.0.0. Data CC BY 4.0, code MIT, © Since AI ry. Exception: Apetit's sample workbook in `data/00_apetit_original` is shared with Apetit's permission and is not CC BY.**

> *How can AI help us to understand, prioritise and quantify climate and nature impacts across the
> value chain, and turn sustainability data into actionable decisions while taking into
> consideration different future climate scenarios?* (Apetit challenge brief)

This package is a **synthetic twin** of a Nordic food company's climate and nature data. The company
makes frozen vegetables and rapeseed oil and works with contract farmers in Finland and Sweden. The
package covers:

* contract farms with field parcels on real-world coordinates, with 15 years of crops, inputs and yields;
* 2021–2025 corporate data in the raw formats that real systems produce (ERP lines, meters, fuel deliveries, refrigerant logs, supplier PCFs in PACT format);
* daily weather from 1991 to 2060 under three climate scenarios;
* catchments with ecological status and monitored nutrient loads;
* transition scenarios, structural events and a lever catalogue.

All of it is calibrated to Apetit's public figures and partner-supplied sample, and to Finnish
statistics. **Nothing in it is real company-confidential data.**

## What is in the box

| Folder | What |
|---|---|
| `data/00_apetit_original` | Apetit's sample workbook, unchanged |
| `data/01_master` | Sites, materials, suppliers, emission-factor library, farms, parcels, climate grid |
| `data/02_raw_feeds` | ERP, energy, fuels, GoOs, refrigerants, waste, water, travel, commuting, shipments, sales, capex, supplier PCFs. **Raw, with errors.** |
| `data/03_farming` | Finnish farm survey, Swedish (Foodhills) grower file, crop history and plan, current-calculator footprints |
| `data/04_climate` | Daily weather (Parquet), monthly CSV, climate-change signals |
| `data/05_scenarios` | Transition scenarios, structural events, levers, prices, published inventory history |
| `data/06_nature` | Parcels and catchments (GeoJSON), monitored loads, import-origin indicators |
| `data/07_frameworks` | Framework digest (status 3 Nov 2026) and source registry |
| `tasks/` | Tasks, dev answer keys, submission templates, question set |
| `tools/ccn_tools` | Loaders, reference GHG calculator, farm-footprint calculator, scorer, baselines |
| `docs/` | Methodology, data dictionary, tasks and scoring, simulation design, scenarios, nature/SBTN, licences, limitations, Azure/Fabric notes, glossary |

## Quick start (10 minutes)

```bash
pip install pandas pyarrow numpy        # plus anything you like
cd tools
python -m ccn_tools                     # runs every baseline and scores it on the dev keys
python quickstart.py                    # a guided tour: data → inventory → yields → catchments
```

## The tracks

| Track | You build | Scored by |
|---|---|---|
| **A** Data → inventory | A data-quality agent and an auditable 2025 GHG inventory | A1 F1 on hidden 2025 issues; A2 error vs hidden 2025 inventory; jury on audit trail |
| **B** Pathways | SBTi-aligned targets (incl. FLAG, base-year recalculation) and a MACC under NGFS-style scenarios | Jury rubric |
| **C** Climate risk to farming | Yield models: forecast the 2027–2031 seasons, estimate 2041–2060 risk by SSP, price it | C1/C2 hidden truths; jury on C3 |
| **D** Nature (SBTN) | Catchment nutrient pressure × state prioritisation; value-chain screening | D1 hidden truth; jury on D2 |
| **E** Copilot | Answers with evidence (record keys, documents) | Numeric auto-check; jury on rubric questions |

Teams may take on one track or several. Apetit judges **demonstrated usefulness, sound reasoning and
traceability**: every number should lead back to its source records and assumptions, and expert
review and approval should be built in.

Full rules: `docs/TASKS_AND_SCORING.md`. Method: `docs/METHODOLOGY.md`.

## What makes this data realistic

* **Raw feeds carry real-world error types:** unit slips, duplicates, currency mix-ups, missing meter months, wrong refrigerant codes, certificates that do not match consumption, stale supplier PCFs, and farmers reporting mineral soil for peat fields. They also carry *legitimate* oddities that are not errors, such as credit notes, vessel lots in tonnes, seasonal peaks and ammonia systems.
* **The company changes shape over time:** divestments, an acquisition in Sweden, plant changes and new standards (SBTi V2, GHG Protocol LSR, SBTN 2.0, EUDR). All of them are dated in `structural_events.csv`.
* **Weather drives yields, and yields drive sourcing, cost and emissions per kg.** The history contains good and bad years; the future comes in three climates.


## Contacts during the hackathon

* Apetit: Jani Kielenniva (IT) and Minna Päällysaho (sustainability). Use the challenge Discord channel or the emails in the challenge brief.
* Since AI organisers: Discord.

Synthetic data. Do not present results as Apetit's actual emissions or as facts about real farms.
