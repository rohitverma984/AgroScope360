# Scenarios, pathways and climate risk

## Files

| File | What it is |
|---|---|
| `05_scenarios/transition_scenarios.csv` | Seven NGFS Phase V scenario names. Illustrative EU carbon price, ETS2 fuel price (from 2028), electricity price, N-fertiliser and diesel price indices, plant-based demand index, import premium. Each is mapped to a physical proxy (SSP). |
| `05_scenarios/structural_events.csv` | Divestments, acquisitions, plant changes and regulatory dates, with their inventory relevance. |
| `05_scenarios/decarbonisation_levers.csv` | 30 levers with indicative abatement, capex, opex, lifetime, start year, ramp, confidence, co-benefits and trade-offs. Abatement figures are design estimates: recompute them from your inventory. |
| `05_scenarios/contract_prices_and_replacement_premiums.csv` | Farm-gate contract prices 2018–2026 and the premium for replacing a shortfall with imports. |
| `05_scenarios/published_inventory_history.csv` | Apetit's published totals 2019–2024, including restatements. |
| `04_climate/weather_daily_1991_2060.parquet` | Daily weather per grid cell. `scenario` = historical (1991–2026), ssp126 / ssp245 / ssp585 (2027–2060). |
| `04_climate/climate_change_signals.csv` | Monthly deltas (2041–2060 vs 1991–2020), for delta-method approaches. |

The carbon-price paths are **illustrative values in NGFS ranges**. Replace them with official NGFS data
(IIASA explorer, `Price|Carbon`) before using them in a real decision.

## Track B: what a strong answer contains

1. **Base year.** SBTi V2 prefers the latest year with comprehensive data. The 2025 inventory is complete, but 2025 still needs a structural adjustment for Foodhills, because only December is in scope. Show both options: a recalculated 2019 base and a 2025 base.
2. **FLAG split.** Use the `flag_share` of factors and the FLAG components of contract farming. Apetit must set a FLAG target as a food processor.
3. **Targets.**
   * Scope 1+2: ≥ 4.2 %/yr linear.
   * Scope 3 non-FLAG: ≥ 2.5 %/yr (well-below 2 °C).
   * FLAG: ≥ 3.03 %/yr.
   * Coverage rules: near-term Scope 3 targets must cover the relevant categories (V2: every category ≥ 5 % of Scope 3).
4. **Pathway.** BAU drivers (volumes, structural events, grid decarbonisation) plus levers by start year and ramp, under at least two transition scenarios. Show the gap to target per year.
5. **MACC.** Cost per t, including co-benefits for water, nutrients and biodiversity. Separate structural changes and measurement changes from real abatement.
6. **Traceability.** Every pathway number links back to inventory lines and lever assumptions.

## Track C: climate risk to farming

* The truth yield model reacts to:
  * drought in sensitive stages, mitigated by irrigation;
  * heat days at flowering;
  * waterlogging after sowing on clay;
  * rain at harvest;
  * season length;
  * potato late blight;
  * pollen beetle in turnip rape.
* Learn these responses from the 2012–2026 history (farm survey yields, deliveries in ERP, the Foodhills file) and the daily weather. Then:
  * **C1:** predict the 2027–2031 seasons, for which weather is given and yields are hidden.
  * **C2:** estimate 2041–2060 risk under each SSP.
  * **C3:** price it, for example as shortfall volume × contract price × replacement premium, plus the emission impact of replacement imports and the value of adaptation such as irrigation, sowing date, varieties or a wider sourcing area.
* **Known 2026 contrast:** a record Finnish pea harvest and heat- and drought-hit Swedish peas. Sourcing from two regions is a hedge; quantify it.
