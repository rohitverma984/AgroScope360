# Sources and licences

## Licence of this package

* **Data:** CC BY 4.0. **Code** (`tools/`): MIT. **Copyright:** Since AI ry, 2026.
* **Attribution:** "Apetit Climate & Nature Navigator synthetic dataset, Since AI ry 2026 (CC BY 4.0)".
* **The Apetit sample workbook** (`data/00_apetit_original/`) is **not** CC BY 4.0. Apetit Plc supplied it and confirmed on 2 October 2026 that it may be used publicly at the hackathon. Apetit describes its figures as indicative.
* **Synthetic data.** All farms, parcels, suppliers, transactions and readings are synthetic. Supplier names are placeholders ("Supplier 012 (synthetic)"). The PACT-format PCF files are not real supplier declarations.

## Public facts used for calibration

Every source used is listed with its URL in `data/07_frameworks/source_registry.csv`. The main ones:

* **Apetit:**
  * annual reports 2023–2024;
  * ESEF filing 2025: structure, sites and the Foodhills acquisition;
  * stock-exchange and press releases: the 2026 pea harvest, the sale of the Kantvik biosteam plant, the Pudasjärvi closure and the SBTi commitment.
* **Climate and crops:**
  * FMI normals and CMIP6 projections (Ruosteenoja & Jylhä 2021);
  * Luke crop statistics.
* **Emission factors:**
  * Statistics Finland fuel classification 2025;
  * Energiateollisuus / Statistics Finland electricity factors;
  * AIB residual mix 2024;
  * IPCC 2019 Refinement; IPCC AR6 GWP100;
  * Yara fertiliser carbon-footprint verification.
* **Nature:**
  * SYKE: organic-soil emission factors and field nutrient losses;
  * Pyhäjärvi Institute: lake catchment phosphorus.
* **Frameworks:** SBTi (CNZS V1.3.1 and V2.0, FLAG), GHG Protocol (Corporate, Scope 2, Scope 3, LSR), SBTN, TNFD, EFRAG ESRS, NGFS Phase V, EUDR, PACT.

## Emission-factor library: value status

| value_status | Meaning |
|---|---|
| `public_value` | Taken from the cited public source. Used for constants in METHODOLOGY.md. |
| `partner_supplied` | From the Apetit sample workbook. |
| `calibrated_synthetic` | Order of magnitude follows the named reference source, but the value is not a copy. Replace it with licensed data in production. |

## Third-party data you may add (and licences)

| Use freely (CC BY 4.0) | Check terms first | Do not redistribute |
|---|---|---|
| WRI Aqueduct 4.0, SYKE catchments and Corine, Luke statistics, FMI open data, Fingrid, Statistics Finland, GFW tree-cover loss, SBTN state-of-nature water layers, Copernicus ERA5 (CC BY since July 2025) | NGFS data licence, Paituli climate scenarios, Finnish Food Authority parcels, ENCORE, Agribalyse (Etalab; ecoinvent background separate), FAOSTAT (CC BY + FAO terms) | EXIOBASE (non-commercial), NHM BII (CC BY-NC-SA), IBAT/KBA (restricted), Climate Guide website content (non-commercial) |

Framework PDFs (SBTi, GHG Protocol, SBTN, EFRAG) are free to download but copyrighted. Index them
locally for RAG, and do not republish them.
