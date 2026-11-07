# Fitting Apetit's Microsoft stack (optional)

Apetit's preferred stack for a later implementation is Microsoft Azure, Fabric, Azure AI Foundry
and Copilot. At the hackathon you can use any tools. These notes show how the package maps onto
that stack, so your solution can explain the path to production.

| Layer | Hackathon (anything) | Apetit production path |
|---|---|---|
| Storage | Local files, DuckDB, Postgres | Fabric Lakehouse: CSV/Parquet in `Files/`, Delta tables in `Tables/` |
| Pipelines | Python, dbt, notebooks | Fabric Data Factory pipelines / notebooks; medallion layers bronze → silver → gold |
| Data quality | Rules + ML anomaly detection | Fabric notebooks with Great Expectations-style checks; issue log as a Delta table |
| Calculation | `ccn_tools.reference_calculator` | Versioned calculation notebook; factor library as a governed table |
| Knowledge / RAG | Any vector store | Azure AI Search index over framework PDFs (downloaded by Apetit) + `framework_digest.md` |
| Agents | Any framework | Azure AI Foundry Agent Service with tools: SQL on the Lakehouse, calculator, search |
| Review & approval | Simple UI | Power BI / Power Apps approval flow; reviewer decisions stored with the evidence |
| Geospatial | GeoPandas, shapely, kepler.gl | Fabric with GeoParquet or Azure Maps; real layers from SYKE and Ruokavirasto |

## Loading into a Fabric Lakehouse

1. Upload `data/` to the Lakehouse `Files/` area. Keep the folder structure: it encodes provenance.
2. Load the Parquet and CSV files as tables in a notebook, for example `spark.read.option("header", True).csv(...)`. `foodhills_odlingsdata_se.csv` uses `;` as the separator and a decimal comma.
3. Treat `02_raw_feeds` as **bronze**. Your cleaned canonical tables (METHODOLOGY.md §2) are **silver**. Inventory line items and KPIs are **gold**.

## Audit trail pattern

Store every correction as a row with these fields:

* `record_key`
* `field`
* `old_value`
* `new_value`
* `rule_or_model`
* `evidence`
* `proposed_by` (agent or person)
* `approved_by`
* `timestamp`

Gold numbers are then reproducible from bronze plus the approved corrections. This is the
"traceable, source-based, subject to expert review" requirement in the brief.
