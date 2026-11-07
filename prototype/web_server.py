"""
prototype/web_server.py — FastAPI Backend for the Stitch-powered Modern Web UI
Serves the Stitch "Nordic Climate Precision" web frontend and exposes REST API
endpoints backed by NavigatorAPI (all 14 platform services + grounded Gemini).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core.api import NavigatorAPI
from core.llm_service import LLMService

PROTO_DIR = Path(__file__).resolve().parent
ROOT_DIR = PROTO_DIR.parent / "APETIT_CLIMATE_NATURE_NAVIGATOR_2026"
WEB_DIR = PROTO_DIR / "web"

app = FastAPI(
    title="AgroScope360 API",
    version="2.4.0",
    description="Unified backend for the Stitch-designed Nordic Climate Precision web interface.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

if (WEB_DIR / "static").exists():
    app.mount("/static", StaticFiles(directory=str(WEB_DIR / "static")), name="static")

api = NavigatorAPI(ROOT_DIR)

# ── Framework Q&A Disclosures (for interactive View Disclosures modal) ───────
FRAMEWORK_DETAILS: Dict[str, Dict[str, Any]] = {
    "cdp": {
        "id": "cdp",
        "name": "CDP 2025 — Climate & Water",
        "progress_pct": 52,
        "deadline": "31 Jul 2025",
        "scope": "Climate Change & Forests Questionnaire (Scope 1, 2, 3 + FLAG)",
        "qa_pairs": [
            {
                "q": "C1.1: Does your board have oversight of climate-related issues?",
                "a": "Yes. Apetit's ESG Assurance Board reviews quarterly Scope 1–3 inventories, Säkylä boiler upgrades, and contractor soil stewardship.",
                "status": "✅ Complete",
            },
            {
                "q": "C2.2: Describe your climate-related risk exposure and financial impact.",
                "a": "Drought in Region A threatens -28% pea yield loss (€2.4M exposure). EU ETS2 introduces a €47/t CO₂ surcharge by 2030 on fossil backup fuels.",
                "status": "✅ Complete",
            },
            {
                "q": "C4.1: Did you have an active emissions reduction target?",
                "a": "Near-term target: 4.2% linear reduction/yr for Scope 1+2 (to 4,482 tCO₂e by 2032) and 3.03% linear/yr for FLAG (to 62,490 tCO₂e).",
                "status": "⚠️ In Review",
            },
            {
                "q": "F1.1: Forests & Land Use: Sourcing verification against deforestation and peatland loss.",
                "a": "Spatial monitoring active across 14,213 parcels; contract shifting initiated on 14 farms with >30% organic soil (L11).",
                "status": "⚠️ Verification in Progress",
            },
        ],
    },
    "gri": {
        "id": "gri",
        "name": "GRI Standards — Agriculture Sector",
        "progress_pct": 68,
        "deadline": "30 Sep 2025",
        "scope": "GRI 302 (Energy), 304 (Biodiversity), 305 (Emissions), Topic 13 (AFPB)",
        "qa_pairs": [
            {
                "q": "GRI 302-1: Energy consumption within the organization.",
                "a": "Total energy intake 1.42 MWh/t product. Electricity 99.1% renewable (Guarantees of Origin). Säkylä boiler utilizes LNG with transitional LPG.",
                "status": "✅ Complete",
            },
            {
                "q": "GRI 304-1: Operational sites in or adjacent to protected areas.",
                "a": "Säkylä facility operates in Catchment CA01 adjacent to Lake Pyhäjärvi Special Area of Conservation (Natura 2000 FI0200084).",
                "status": "✅ Complete",
            },
            {
                "q": "GRI 305-1 & 305-2: Direct (Scope 1) and Energy Indirect (Scope 2) GHG emissions.",
                "a": "Scope 1: 6,251 tCO₂e (fossil fuels). Scope 2 Market: 63 tCO₂e. Scope 2 Location: 184.2 tCO₂e (0.026 kg/kWh grid factor).",
                "status": "✅ Complete",
            },
            {
                "q": "GRI 305-3: Other indirect (Scope 3) emissions.",
                "a": "Scope 3 total: 238,410 tCO₂e. FLAG emissions represent 42.3% of group footprint, driven by contract pea, potato, and grain sourcing.",
                "status": "⚠️ Supplier Verification Active",
            },
        ],
    },
    "tcfd": {
        "id": "tcfd",
        "name": "TCFD Report — Physical Risk & MACC",
        "progress_pct": 81,
        "deadline": "31 Aug 2025",
        "scope": "Governance, Strategy, Risk Management, Metrics & Targets",
        "qa_pairs": [
            {
                "q": "Strategy: Resilience of organization taking into account different climate scenarios.",
                "a": "Evaluated under NGFS Net Zero 2050 (SSP1-2.6) and Delayed Transition (SSP2-4.5). MACC model shows €1.8M 10-yr NPV across 6 primary levers.",
                "status": "✅ Complete",
            },
            {
                "q": "Risk Management: Processes for identifying and managing climate risks.",
                "a": "Digital twin cross-references 14,213 parcel coordinates with soil maps and CMIP6 moisture deficit projections.",
                "status": "✅ Complete",
            },
            {
                "q": "Metrics & Targets: Climate targets and performance against targets.",
                "a": "Scope 1+2 target: -29.4% by 2032; FLAG target: -21.2% by 2032. Internal carbon price benchmark: €80/t rising to €160/t (2030).",
                "status": "✅ Complete",
            },
        ],
    },
    "brsr": {
        "id": "brsr",
        "name": "BRSR Core — Assurance Locked",
        "progress_pct": 100,
        "deadline": "12 Jan 2025",
        "scope": "Principle 6: Environmental Value Chain Integrity",
        "qa_pairs": [
            {
                "q": "Principle 6 Essential Indicator 1: Energy and water withdrawal details.",
                "a": "Annual water intake: 542,000 m³; 100% wastewater treated at municipal facilities or on-site pre-treatment before discharge.",
                "status": "✅ Complete",
            },
            {
                "q": "Principle 6 Essential Indicator 2: Scope 1, 2, 3 footprint reporting.",
                "a": "All 15 Scope 3 categories evaluated; Category 1 (Purchased Goods) and Category 4 (Upstream Transport) represent >90% of value chain impact.",
                "status": "✅ Complete",
            },
            {
                "q": "Principle 6 Leadership Indicator 1: Renewable energy transition.",
                "a": "100% of electricity certified by national registry Guarantees of Origin (GoO); Kantvik biosteam supplies renewable process heat.",
                "status": "✅ Complete",
            },
        ],
    },
    "cbam": {
        "id": "cbam",
        "name": "CBAM EU — Fertilizer & Packaging Embedded",
        "progress_pct": 50,
        "deadline": "15 Oct 2025",
        "scope": "Direct & Indirect Embedded Emissions on Raw Imports",
        "qa_pairs": [
            {
                "q": "Embedded emissions calculation on imported materials.",
                "a": "Monitoring packaging aluminum, steel, and nitrate fertilizer precursors imported from non-EU jurisdictions against EU default benchmarks.",
                "status": "⚠️ In Progress",
            },
            {
                "q": "Supplier data collection and verification.",
                "a": "Quarterly declarative reports submitted for transitional phase; transition to verified supplier-specific PCFs active.",
                "status": "⚠️ Supplier Outreach Active",
            },
        ],
    },
    "csrd": {
        "id": "csrd",
        "name": "EU CSRD Mandatory — ESRS E1–E5 Package",
        "progress_pct": 100,
        "deadline": "30 May 2025",
        "scope": "ESRS E1 (Climate Change), E2 (Pollution), E3 (Water), E4 (Biodiversity)",
        "qa_pairs": [
            {
                "q": "ESRS E1-6: Gross Scopes 1, 2, 3 and Total GHG emissions.",
                "a": "Dual reporting Scope 2 enforced (63 t market vs 184.2 t location). FLAG emissions separately disclosed at 100,847 tCO₂e (42.3% of total).",
                "status": "✅ Complete",
            },
            {
                "q": "ESRS E1-1: Transition plan for climate change mitigation.",
                "a": "30-lever MACC pathway modeled through 2030/2050, backed by €1.48M priority CAPEX allocation and SBTi 1.5°C alignment.",
                "status": "✅ Complete",
            },
            {
                "q": "ESRS E4-5: Impact metrics related to biodiversity and ecosystems change.",
                "a": "SBTN Freshwater assessment completed across 42 catchments; Lake Pyhäjärvi (CA01) and Eurajoki (CA04) prioritized for buffer strip intervention.",
                "status": "✅ Complete",
            },
        ],
    },
}


def _clean(obj: Any) -> Any:
    """Convert numpy/pandas types into JSON-safe primitives."""
    if isinstance(obj, dict):
        return {str(k): _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    if isinstance(obj, pd.DataFrame):
        return _clean(obj.where(pd.notnull(obj), None).to_dict(orient="records"))
    if isinstance(obj, pd.Series):
        return _clean(obj.where(pd.notnull(obj), None).to_dict())
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        return None if np.isnan(obj) or np.isinf(obj) else float(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj


# ── HTML Pages ───────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    target = WEB_DIR / "index.html"
    if not target.exists():
        target = WEB_DIR / "stitch_template.html"
    return HTMLResponse(target.read_text(encoding="utf-8"))


@app.get("/stitch-template", response_class=HTMLResponse)
def stitch_template() -> HTMLResponse:
    return HTMLResponse((WEB_DIR / "stitch_template.html").read_text(encoding="utf-8"))


@app.get("/stitch-preview.png")
def stitch_preview_img() -> FileResponse:
    return FileResponse(str(WEB_DIR / "stitch_preview.png"), media_type="image/png")


# ── Core REST Endpoints ──────────────────────────────────────────────────────
@app.get("/api/overview")
def get_overview() -> JSONResponse:
    summary = api.get_executive_summary(2025)
    inv_hist = pd.read_csv(ROOT_DIR / "data" / "05_scenarios" / "published_inventory_history.csv")
    events = pd.read_csv(ROOT_DIR / "data" / "05_scenarios" / "structural_events.csv")
    levers = pd.read_csv(ROOT_DIR / "data" / "05_scenarios" / "decarbonisation_levers.csv")
    catchments = pd.read_csv(ROOT_DIR / "data" / "06_nature" / "catchments.csv")
    farms_df = pd.read_csv(ROOT_DIR / "data" / "01_master" / "farm_registry.csv")
    parcels_df = pd.read_csv(ROOT_DIR / "data" / "01_master" / "parcels.csv")
    top_c = catchments[catchments["catchment_id"] == summary.get("top_nature_priority_catchment")]
    platform_stats = {
        "farms": int(len(farms_df)),
        "parcels": int(len(parcels_df)),
        "catchments_total": int(len(catchments)),
        "levers_total": int(len(levers)),
        "levers_capex_eur": float(levers["capex_eur"].fillna(0).sum()),
        "top_catchment_region": str(top_c["region"].iloc[0]) if len(top_c) else "",
        "top_catchment_status": str(top_c["ecological_status_class"].iloc[0]) if len(top_c) else "",
    }
    return JSONResponse(
        _clean({
            "summary": summary,
            "platform_stats": platform_stats,
            "inventory_history": inv_hist,
            "structural_events": events,
            "top_levers": levers.dropna(subset=["abatement_tco2e_2030_design"]).head(12),
            "catchments": catchments.head(12),
            "tradeoffs": api.tradeoffs.list_actions(),
            "frameworks": list(FRAMEWORK_DETAILS.values()),
            "gemini_available": LLMService().is_available,
        })
    )


@app.get("/api/tradeoffs")
def list_tradeoffs() -> JSONResponse:
    return JSONResponse(_clean({"actions": api.tradeoffs.list_actions()}))


@app.get("/api/tradeoffs/{action_id}")
def get_tradeoff(action_id: str) -> JSONResponse:
    return JSONResponse(_clean(api.tradeoffs.get_action_tradeoff(action_id)))


@app.get("/api/reports/frameworks")
def get_frameworks() -> JSONResponse:
    return JSONResponse(_clean({"frameworks": list(FRAMEWORK_DETAILS.values())}))


@app.get("/api/reports/frameworks/{fw_id}")
@app.get("/api/reports/framework/{fw_id}")
def get_framework_detail(fw_id: str) -> JSONResponse:
    fw = FRAMEWORK_DETAILS.get(fw_id.lower())
    if not fw:
        raise HTTPException(status_code=404, detail=f"Unknown framework '{fw_id}'")
    return JSONResponse(_clean(fw))


# Active simulator & investment state synced to Smart ESG Reports & MACC
ACTIVE_SIMULATOR_SYNC: Optional[Dict[str, Any]] = None
ACTIVE_INVESTMENT_SYNC: Optional[Dict[str, Any]] = None


class InvestmentOptimizeRequest(BaseModel):
    focus_id: str = "all"
    budget_eur: float = 180000.0
    enterprise_scale_mult: float = 10.0  # Scales pilot initiatives to enterprise MACC CAPEX (~€1.8M)
    w_emissions: float = 0.25
    w_adaptation: float = 0.20
    w_nature: float = 0.20
    w_financial: float = 0.25
    w_feasibility: float = 0.10
    carbon_price_eur: float = 85.0
    hurdle_rate_pct: float = 8.0


FOCUS_META: Dict[str, Dict[str, Any]] = {
    "all": {
        "title": "Apetit Net-Zero & SBTN Consolidated Transition Portfolio",
        "subtitle": "Multi-Objective Allocation across Säkylä, Kantvik, Foodhills Bjuv & 41 Sourcing Catchments",
        "lever_refs": "MACC Levers L01, L02, L06, L08, L09, L10, L11, L23, L24",
    },
    "fleet_ev": {
        "title": "Electric Yard & Logistics Fleet Transition (L02 / L20 / L21)",
        "subtitle": "Säkylä Electric Forklifts, Naantali–Helsinki E-Freight & Vessel Modal Shift",
        "lever_refs": "MACC Levers L02 (€420k CAPEX, -€35k/yr OPEX) + L21 Modal Shift (-€50k/yr OPEX)",
    },
    "renew_energy": {
        "title": "Kantvik Heat Recovery & Säkylä Biogas Transition (L01 / L06 / L03)",
        "subtitle": "Industrial Oil-Press Heat Pump Recovery, Ammonia Cold Store & LNG-to-Biogas Switch",
        "lever_refs": "MACC Levers L06 (€900k CAPEX, -€60k/yr OPEX) + L01 (1,650 tCO₂e/yr)",
    },
    "fert_opt": {
        "title": "Precision N-Fertiliser & Peat Soil Contract Shift (L08 / L09 / L11)",
        "subtitle": "Variable-Rate N-Sensors, Low-Carbon Ammonia & Shifting 14 Farms off Drained Peat",
        "lever_refs": "MACC Levers L11 (8,500 tCO₂e/yr @ €11/t) + L08 (2,100 tCO₂e/yr) + L09 (900 tCO₂e/yr)",
    },
    "water_eff": {
        "title": "Micro-Drip Irrigation, Riparian Buffers & Tenderometer AI (L23 / L24)",
        "subtitle": "Lake Pyhäjärvi (CA01) Eutrophication Shield, Drip Scheduling & Harvest Intake AI",
        "lever_refs": "MACC Levers L23 (-€80k/yr food-loss savings) + L24 Drip Irrigation + SBTN Buffers",
    },
}


@app.post("/api/investments/optimize")
def optimize_sustainability_investments(req: InvestmentOptimizeRequest) -> JSONResponse:
    """
    Run Apetit's InvestmentOptimizerService + MACC dataset (decarbonisation_levers.csv)
    and return the full portfolio financial analysis (NPV, IRR, Payback, 10-Yr Cumulative
    Cash Flow, NPV Waterfall, Biggest Value Drivers, Cost of Inaction, and Deep Dive table).
    """
    api.optimizer.discount_rate = max(0.02, min(0.20, req.hurdle_rate_pct / 100.0))
    api.optimizer.carbon_price_eur = max(20.0, req.carbon_price_eur)

    weights = {
        "emissions": req.w_emissions,
        "adaptation": req.w_adaptation,
        "nature": req.w_nature,
        "financial": req.w_financial,
        "feasibility": req.w_feasibility,
    }
    raw_res = api.optimizer.optimize_portfolio(budget=req.budget_eur, weights=weights)

    # Scale to enterprise CAPEX scale (so €180k pilot budget -> €1.80M enterprise MACC portfolio)
    mult = max(1.0, req.enterprise_scale_mult)
    focus = FOCUS_META.get(req.focus_id, FOCUS_META["all"])
    if req.focus_id != "all":
        mult = mult * 0.68

    allocated_capex = round(raw_res["allocated_capex"] * mult, 0)
    annual_savings = round(raw_res["total_annual_savings"] * mult, 0)
    npv_10y = round(raw_res["npv_10y"] * mult, 0)
    ghg_abated = round(raw_res["total_ghg_abated_tco2e"] * (mult * 0.85), 0)
    water_saved = round(raw_res["total_water_saved_m3"] * mult, 0)
    p_saved = round(raw_res["total_p_runoff_saved_kg"] * mult, 0)

    # Build 10-Year Cumulative Cash Flow + Annual Oscillating Cash Trajectory (Years 0..10)
    trajectory = []
    for pt in raw_res["trajectory"]:
        yr = int(pt["year"])
        trajectory.append({
            "year": yr,
            "annual_flow": round(float(pt["annual_flow"]) * mult, 0),
            "cumulative_cash_flow": round(float(pt["cumulative_cash_flow"]) * mult, 0),
            "discounted_flow": round(float(pt["discounted_flow"]) * mult, 0),
        })

    wf = raw_res["waterfall"]
    waterfall = {
        "initial_investment": round(float(wf["initial_investment"]) * mult, 0),
        "energy_fuel_savings": round(float(wf["energy_fuel_savings"]) * mult, 0),
        "input_cost_cuts": round(float(wf["input_cost_cuts"]) * mult, 0),
        "carbon_avoidance": round(float(wf["carbon_avoidance"]) * mult, 0),
        "yield_protection": round(float(wf["yield_protection"]) * mult, 0),
        "esg_subsidies": round(float(wf["esg_subsidies"]) * mult, 0),
        "net_present_value": npv_10y,
    }

    gross_benefits_npv = (
        waterfall["energy_fuel_savings"]
        + waterfall["input_cost_cuts"]
        + waterfall["carbon_avoidance"]
        + waterfall["yield_protection"]
        + waterfall["esg_subsidies"]
    )

    drivers = [
        {
            "driver": "Energy, Biogas & Fleet Savings",
            "lever_tag": "L01 · L02 · L06",
            "amount_eur": waterfall["energy_fuel_savings"],
            "delta_badge": "+14.2%",
        },
        {
            "driver": "Agri-Input & Tenderometer Cuts",
            "lever_tag": "L08 · L09 · L23",
            "amount_eur": waterfall["input_cost_cuts"],
            "delta_badge": "+11.8%",
        },
        {
            "driver": "EU ETS2 & Carbon Tax Shields",
            "lever_tag": f"€{req.carbon_price_eur:.0f}/t Shadow Price",
            "amount_eur": waterfall["carbon_avoidance"],
            "delta_badge": "+11.4%",
        },
        {
            "driver": "Drought Yield & CAP Subsidies",
            "lever_tag": "L11 · L24 · EU CAP",
            "amount_eur": waterfall["yield_protection"] + waterfall["esg_subsidies"],
            "delta_badge": "+9.6%",
        },
    ]

    # Load real MACC levers from decarbonisation_levers.csv
    levers_df = pd.read_csv(ROOT_DIR / "data" / "05_scenarios" / "decarbonisation_levers.csv")
    levers_clean = levers_df.dropna(subset=["abatement_tco2e_2030_design"]).copy()
    levers_clean = levers_clean[levers_clean["abatement_tco2e_2030_design"] > 0].sort_values(
        by="abatement_tco2e_2030_design", ascending=False
    )

    allocated_initiatives = []
    for item in raw_res["allocated_initiatives"]:
        allocated_initiatives.append({
            **item,
            "allocated_investment": round(float(item["allocated_investment"]) * mult, 0),
            "annual_opex_savings": round(float(item["annual_opex_savings"]) * mult, 0),
            "ghg_abatement_tco2e": round(float(item["ghg_abatement_tco2e"]) * (mult * 0.85), 0),
            "water_saved_m3": round(float(item["water_saved_m3"]) * mult, 0),
            "p_loss_prevented_kg": round(float(item["p_loss_prevented_kg"]) * mult, 0),
        })

    inaction = {
        "ten_yr_financial_penalty_eur": round(float(raw_res["cost_of_inaction"]["ten_yr_financial_penalty_eur"]) * mult, 0),
        "lost_crop_yield_tha": raw_res["cost_of_inaction"]["lost_crop_yield_tha"],
        "cumulative_carbon_tax_exposure_eur": round(float(raw_res["cost_of_inaction"]["cumulative_carbon_tax_exposure_eur"]) * mult, 0),
        "sbtn_freshwater_risk": raw_res["cost_of_inaction"]["sbtn_freshwater_risk"],
    }

    return JSONResponse(
        _clean({
            "focus_id": req.focus_id,
            "title": focus["title"],
            "subtitle": focus["subtitle"],
            "lever_refs": focus["lever_refs"],
            "budget_eur": round(req.budget_eur * mult, 0),
            "allocated_capex_eur": allocated_capex,
            "unallocated_reserve_eur": round(raw_res["unallocated_reserve"] * mult, 0),
            "annual_savings_eur": annual_savings,
            "npv_10y_eur": npv_10y,
            "gross_benefits_npv_eur": gross_benefits_npv,
            "irr_pct": raw_res["irr_pct"],
            "breakeven_year": raw_res["breakeven_year"],
            "hurdle_rate_pct": req.hurdle_rate_pct,
            "hurdle_rate_multiple": raw_res["hurdle_rate_multiple"],
            "carbon_price_eur": req.carbon_price_eur,
            "ghg_abated_tco2e": ghg_abated,
            "water_saved_m3": water_saved,
            "p_runoff_saved_kg": p_saved,
            "avg_feasibility": round(raw_res["avg_feasibility"], 1),
            "trajectory": trajectory,
            "waterfall": waterfall,
            "drivers": drivers,
            "allocated_initiatives": allocated_initiatives,
            "macc_levers": levers_clean.head(14),
            "cost_of_inaction": inaction,
        })
    )


@app.post("/api/investments/sync-report")
def sync_investments_to_esg_report(req: InvestmentOptimizeRequest) -> JSONResponse:
    """Sync the optimised Sustainability Investment Portfolio into the Smart ESG Report Generator."""
    global ACTIVE_INVESTMENT_SYNC
    resp = optimize_sustainability_investments(req)
    data = json.loads(resp.body.decode("utf-8"))
    ACTIVE_INVESTMENT_SYNC = {
        "synced_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "title": data["title"],
        "allocated_capex_eur": data["allocated_capex_eur"],
        "annual_savings_eur": data["annual_savings_eur"],
        "npv_10y_eur": data["npv_10y_eur"],
        "irr_pct": data["irr_pct"],
        "breakeven_year": data["breakeven_year"],
        "ghg_abated_tco2e": data["ghg_abated_tco2e"],
        "p_runoff_saved_kg": data["p_runoff_saved_kg"],
    }
    return JSONResponse(_clean({"status": "ok", "synced_investment": ACTIVE_INVESTMENT_SYNC}))


class SimulatorRunRequest(BaseModel):
    cluster_id: str = "sakyla"
    crop: str = "pea"
    climate_scenario: str = "ssp245"
    fertiliser_pct_delta: float = -20.0
    irrigation_eff_delta: float = 15.0
    renewable_energy_delta: float = 30.0
    production_volume_delta: float = 10.0
    use_lowcarbon_fert: bool = True
    use_buffer_strips: bool = True
    use_catch_crops: bool = True
    carbon_price_eur: float = 80.0


CLUSTER_PROFILES: Dict[str, Dict[str, Any]] = {
    "sakyla": {
        "id": "sakyla",
        "name": "Säkylä Frozen Veg Cluster — FI_SW (CA01 Lake Pyhäjärvi)",
        "catchment_id": "CA01",
        "catchment_name": "Pyhäjärvi (Säkylä)",
        "contract_ha": 1842.0,
        "parcel_count": 412,
        "flag_share_pct": 68.4,
        "ring_offset": 82,
        "bbox": "22.20,60.98,22.48,61.12",
        "soil_note": "Fine sandy-silt glacial moraine adjacent to Lake Pyhäjärvi Class I aquifer (P-sensitivity 1.6×).",
    },
    "kantvik": {
        "id": "kantvik",
        "name": "Kantvik Oilseed & Rapeseed Shed — FI_S (Uusimaa)",
        "catchment_id": "CA04",
        "catchment_name": "Eurajoki & Southern Clay Belt",
        "contract_ha": 2410.0,
        "parcel_count": 538,
        "flag_share_pct": 61.2,
        "ring_offset": 98,
        "bbox": "24.25,60.05,24.55,60.20",
        "soil_note": "Heavy marine clay plain requiring winter cover crops and gypsum amendments to curb particulate P loss.",
    },
    "ostrobothnia": {
        "id": "ostrobothnia",
        "name": "Ostrobothnia Root & Potato Basin — FI_W",
        "catchment_id": "CA07",
        "catchment_name": "Kyrönjoki & Loimijoki",
        "contract_ha": 1590.0,
        "parcel_count": 346,
        "flag_share_pct": 54.8,
        "ring_offset": 114,
        "bbox": "22.50,62.70,22.90,62.90",
        "soil_note": "Includes 14 organic/peat soil farms (29.0 tCO₂e/ha/yr oxidation) targeted by MACC Lever L11.",
    },
    "bjuv": {
        "id": "bjuv",
        "name": "Foodhills AB Contract Pea Hub — Bjuv, Skåne (SE_S)",
        "catchment_id": "CA12",
        "catchment_name": "Råån & Skåne Lowlands",
        "contract_ha": 3120.0,
        "parcel_count": 620,
        "flag_share_pct": 74.5,
        "ring_offset": 68,
        "bbox": "12.82,56.02,13.08,56.14",
        "soil_note": "High-yielding southern Swedish loam integrated via 2025 Foodhills AB acquisition (+18.2 kt Scope 3 FLAG).",
    },
}

CROP_LABELS: Dict[str, str] = {
    "pea": "Green Pea (Herne)",
    "potato": "Ware Potato (Peruna)",
    "carrot": "Carrot (Porkkana)",
    "rapeseed": "Turnip Rape (Rypsi)",
}


@app.post("/api/simulator/run")
def run_whatif_simulator(req: SimulatorRunRequest) -> JSONResponse:
    """
    Execute Apetit's multi-variable What-If Simulation combining:
    - SimulatorService (GHG Scopes 1-3+FLAG, Water m3, P & N runoff kg, Financials €)
    - ClimateRiskService (CMIP6 1991-2060 yield t/ha & bad-year probability %)
    - MACC Lever & Regenerative Rotation pairings from decarbonisation_levers.csv
    """
    sim = api.simulator.run_simulation(
        fertiliser_pct_delta=req.fertiliser_pct_delta,
        irrigation_eff_delta=req.irrigation_eff_delta,
        renewable_energy_delta=req.renewable_energy_delta,
        production_volume_delta=req.production_volume_delta,
        use_lowcarbon_fert=req.use_lowcarbon_fert,
        use_buffer_strips=req.use_buffer_strips,
        use_catch_crops=req.use_catch_crops,
        carbon_price_eur=req.carbon_price_eur,
    )
    crop_key = req.crop if req.crop in CROP_LABELS else "pea"
    scen_key = req.climate_scenario if req.climate_scenario in ("ssp126", "ssp245", "ssp585") else "ssp245"
    risk_data = api.risk.simulate_crop_yields(crop=crop_key, scenario=scen_key)
    risk_kpis = risk_data.get("kpis", {})

    cluster = CLUSTER_PROFILES.get(req.cluster_id, CLUSTER_PROFILES["sakyla"])
    crop_label = CROP_LABELS[crop_key]

    # Calculate Agronomic Resilience Score (Card 1) from CMIP6 risk + irrigation/catch-crop mitigation
    bad_yr_prob = float(risk_kpis.get("future_2050_bad_year_prob_pct", 18.0))
    if req.irrigation_eff_delta >= 15:
        bad_yr_prob = max(4.0, bad_yr_prob - 7.5)
    if req.use_catch_crops:
        bad_yr_prob = max(4.0, bad_yr_prob - 3.0)

    if bad_yr_prob <= 10.0:
        agro_grade = "A"
    elif bad_yr_prob <= 16.0:
        agro_grade = "A-"
    elif bad_yr_prob <= 24.0:
        agro_grade = "B+"
    elif bad_yr_prob <= 32.0:
        agro_grade = "B"
    else:
        agro_grade = "C+"

    base_yield_tha = float(risk_kpis.get("baseline_mean_yield_t_ha", 4.6))
    sim_yield_tha = round(base_yield_tha * (1.0 + sim["crop"]["delta_pct"] / 100.0 / max(0.5, 1.0 + req.production_volume_delta / 100.0)), 2)

    agro_advisory = (
        f"{cluster['soil_note']} Under {scen_key.upper()}, {crop_label} baseline yield is {base_yield_tha:.2f} t/ha "
        f"(simulated output: {sim['crop']['sim_tonnes']:,.0f} t, {sim['crop']['delta_pct']:+.1f}% vs. 2025 baseline). "
        f"Precision irrigation (+{req.irrigation_eff_delta:.0f}%) and {'winter catch crops (Lever L10)' if req.use_catch_crops else 'standard tillage'} "
        f"hold bad-year failure risk to {bad_yr_prob:.1f}%."
    )

    env_advisory = (
        f"Group GHG changes by {sim['ghg']['delta_pct']:+.1f}% ({sim['ghg']['delta_tco2e']:+,.0f} tCO₂e). "
        f"In {cluster['catchment_name']} ({cluster['catchment_id']}), phosphorus runoff drops {sim['nature']['p_delta_pct']:+.1f}% "
        f"(to {sim['nature']['sim_p_kg']:,.0f} kg P/yr) and nitrogen leaching drops {sim['nature']['n_delta_pct']:+.1f}% "
        f"via {'riparian buffer strips (L24) & low-carbon N (L08)' if (req.use_buffer_strips or req.use_lowcarbon_fert) else 'rate adjustment'}."
    )

    # Regenerative Crop Rotations & MACC Lever Pairings (Card 4)
    rotations = [
        {
            "c1": f"{crop_label}",
            "s1": f"{min(98, int(86 - req.fertiliser_pct_delta * 0.3))}/100",
            "sea1": "Summer Main",
            "c2": "Autumn Oat + Catch Crops (Lever L10)",
            "s2": f"{92 if req.use_catch_crops else 74}/100",
            "sea2": "Autumn Cover",
            "lever_note": "MACC Lever L10 · Captures residual soil nitrate & cuts clay erosion (-600 tCO₂e/yr)",
        },
        {
            "c1": "Ware Potato (Peruna)",
            "s1": "81/100",
            "sea1": "Summer Main",
            "c2": "Winter Rye + Buffer Strips (Lever L24)",
            "s2": f"{94 if req.use_buffer_strips else 76}/100",
            "sea2": "Winter Shield",
            "lever_note": "SBTN CA01 Action · Traps 35% of particulate P runoff into Lake Pyhäjärvi",
        },
        {
            "c1": "Turnip Rape (Rypsi)",
            "s1": "84/100",
            "sea1": "Summer Oilseed",
            "c2": "Spring Barley + Low-Carbon N (Lever L08)",
            "s2": f"{90 if req.use_lowcarbon_fert else 78}/100",
            "sea2": "Spring Rotation",
            "lever_note": "MACC Lever L08 · Green ammonia fertiliser cuts Scope 3 FLAG by 2,100 tCO₂e/yr",
        },
        {
            "c1": "Carrot (Porkkana)",
            "s1": "79/100",
            "sea1": "Summer Root",
            "c2": "Mineral Soil Shift off Peat (Lever L11)",
            "s2": "95/100",
            "sea2": "Multi-Year",
            "lever_note": "MACC Lever L11 · Eliminates 29.0 tCO₂e/ha/yr organic soil oxidation (-8,500 tCO₂e/yr)",
        },
    ]

    # Quarterly Financials (Card 5) scaled from simulator financials
    # Spend = fertiliser/seed/buffer/energy investment; Revenue = crop value + carbon tax & efficiency savings
    total_spend_k = max(40.0, (1800.0 * (1.0 + req.fertiliser_pct_delta / 100.0) + (140.0 if req.use_lowcarbon_fert else 0.0) + (70.0 if req.use_buffer_strips or req.use_catch_crops else 0.0)) / 45.0)
    total_rev_k = max(45.0, (sim["crop"]["sim_tonnes"] * 320.0 / 280000.0) + (sim["financials"]["carbon_tax_savings"] / 15000.0))

    quarterly_financials = {
        "q1_spend_k": round(total_spend_k * 0.58, 1),   # Spring seeding & fertilizer purchase
        "q1_rev_k": round(total_rev_k * 0.72, 1),       # Contract forward off-take & Q1 frozen sales
        "q2_spend_k": round(total_spend_k * 0.28, 1),   # Summer drip irrigation & precision scouting
        "q2_rev_k": round(total_rev_k * 0.34, 1),       # Early pea harvest & Kantvik oilseed margin
        "q3_spend_k": round(total_spend_k * 0.10, 1),   # Autumn harvest & catch crop seeding
        "q3_rev_k": round(total_rev_k * 0.14, 1),       # Autumn root crop delivery
        "q4_spend_k": round(total_spend_k * 0.04, 1),   # Winter storage & cold-chain
        "q4_rev_k": round(total_rev_k * 0.08, 1),       # Carbon credit & GoO optimization
        "net_annual_delta_eur": sim["financials"]["net_delta_eur"],
        "carbon_savings_eur": sim["financials"]["carbon_tax_savings"],
    }

    # Seasonal Environmental Strain vs Yield Trajectory (Card 6)
    water_strain_idx = round((sim["water"]["sim_m3"] / 680000.0) * 115.0, 1)
    yield_output_idx = round((sim["crop"]["sim_tonnes"] / 42000.0) * 128.0, 1)

    return JSONResponse(
        _clean({
            "sim": sim,
            "cluster": cluster,
            "crop_key": crop_key,
            "crop_label": crop_label,
            "climate_scenario": scen_key.upper(),
            "cards": {
                "agro_grade": agro_grade,
                "agro_advisory": agro_advisory,
                "bad_year_prob_pct": round(bad_yr_prob, 1),
                "sim_yield_tha": sim_yield_tha,
                "env_grade": sim["grades"]["nature"],
                "climate_grade": sim["grades"]["climate"],
                "env_advisory": env_advisory,
                "rotations": rotations,
                "quarterly_financials": quarterly_financials,
                "water_strain_idx": water_strain_idx,
                "yield_output_idx": yield_output_idx,
            },
        })
    )


@app.post("/api/simulator/sync-report")
def sync_simulator_to_esg_report(req: SimulatorRunRequest) -> JSONResponse:
    """
    Push the active What-If Simulator scenario into the Smart ESG Report Generator
    so CSRD/TCFD/CDP disclosures and PDF/XBRL downloads reflect the simulated pathway.
    """
    global ACTIVE_SIMULATOR_SYNC
    sim = api.simulator.run_simulation(
        fertiliser_pct_delta=req.fertiliser_pct_delta,
        irrigation_eff_delta=req.irrigation_eff_delta,
        renewable_energy_delta=req.renewable_energy_delta,
        production_volume_delta=req.production_volume_delta,
        use_lowcarbon_fert=req.use_lowcarbon_fert,
        use_buffer_strips=req.use_buffer_strips,
        use_catch_crops=req.use_catch_crops,
        carbon_price_eur=req.carbon_price_eur,
    )
    cluster = CLUSTER_PROFILES.get(req.cluster_id, CLUSTER_PROFILES["sakyla"])
    ACTIVE_SIMULATOR_SYNC = {
        "synced_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cluster_name": cluster["name"],
        "crop_label": CROP_LABELS.get(req.crop, "Green Pea (Herne)"),
        "climate_scenario": req.climate_scenario.upper(),
        "inputs": sim["inputs"],
        "ghg": sim["ghg"],
        "water": sim["water"],
        "nature": sim["nature"],
        "financials": sim["financials"],
        "crop": sim["crop"],
        "grades": sim["grades"],
        "ai_narrative": sim["ai_narrative"],
    }
    return JSONResponse(_clean({"status": "ok", "synced_scenario": ACTIVE_SIMULATOR_SYNC}))


class ReportRequest(BaseModel):
    reporting_period: str = "2025 (Annual)"
    business_unit: str = "Apetit Group Consolidated"
    climate_scenario: str = "NGFS Net Zero 2050 (SSP1-2.6)"
    emissions_category: str = "All Scopes (1, 2, 3 + FLAG)"
    nature_indicators: str = "SBTN Freshwater Eutrophication & P-Leaching"
    framework: str = "CSRD / ESRS (E1–E4)"


@app.post("/api/reports/generate")
@app.post("/api/reports/custom")
def generate_custom_report(req: ReportRequest) -> JSONResponse:
    rep = api.reports.generate_report(
        reporting_period=req.reporting_period,
        business_unit=req.business_unit,
        climate_scenario=req.climate_scenario,
        emissions_category=req.emissions_category,
        nature_indicators=req.nature_indicators,
        framework=req.framework,
    )
    if ACTIVE_SIMULATOR_SYNC:
        rep["simulator_scenario"] = ACTIVE_SIMULATOR_SYNC
    if ACTIVE_INVESTMENT_SYNC:
        rep["investment_portfolio"] = ACTIVE_INVESTMENT_SYNC
        rep["costs"]["total_capex_eur"] = ACTIVE_INVESTMENT_SYNC["allocated_capex_eur"]
        rep["costs"]["annual_opex_delta_eur"] = -ACTIVE_INVESTMENT_SYNC["annual_savings_eur"]
        rep["costs"]["npv_10yr_eur"] = ACTIVE_INVESTMENT_SYNC["npv_10y_eur"]
        rep["costs"]["irr_pct"] = ACTIVE_INVESTMENT_SYNC["irr_pct"]
        rep["costs"]["payback_years"] = ACTIVE_INVESTMENT_SYNC["breakeven_year"]
    return JSONResponse(_clean(rep))


@app.get("/api/reports/pdf")
def download_report_pdf(
    framework: str = Query("CSRD / ESRS (E1–E4)"),
    reporting_period: str = Query("2025 (Annual)"),
    business_unit: str = Query("Apetit Group Consolidated"),
    climate_scenario: str = Query("NGFS Net Zero 2050 (SSP1-2.6)"),
) -> Response:
    rep = api.reports.generate_report(
        reporting_period=reporting_period,
        business_unit=business_unit,
        climate_scenario=climate_scenario,
        framework=framework,
    )
    pdf_bytes = api.reports.generate_pdf(rep)
    safe_fw = "".join(c if c.isalnum() else "_" for c in framework).strip("_")
    filename = f"Apetit_ESG_Report_{safe_fw}_{rep['report_id']}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/reports/xbrl")
def download_report_xbrl(framework: str = Query("CSRD / ESRS (E1–E4)")) -> Response:
    rep = api.reports.generate_report(framework=framework)
    payload = json.dumps(_clean(rep), indent=2, ensure_ascii=False).encode("utf-8")
    safe_fw = "".join(c if c.isalnum() else "_" for c in framework).strip("_")
    filename = f"Apetit_XBRL_Package_{safe_fw}_{rep['report_id']}.json"
    return Response(
        content=payload,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


class ChatRequest(BaseModel):
    query: str
    history: Optional[List[Dict[str, str]]] = None
    api_key: Optional[str] = None
    use_llm: bool = True


@app.get("/api/copilot/suggestions")
def copilot_suggestions() -> JSONResponse:
    return JSONResponse(
        _clean({
            "suggested": api.copilot.get_suggested_queries(),
            "gemini_available": LLMService().is_available,
        })
    )


@app.post("/api/copilot/ask")
def copilot_ask(req: ChatRequest) -> JSONResponse:
    res = api.copilot.research_query(
        query=req.query,
        history=req.history,
        api_key=req.api_key,
        use_llm=req.use_llm,
    )
    return JSONResponse(_clean(res))


@app.get("/api/inventory/details")
def get_inventory_details(year: int = Query(default=2025)) -> JSONResponse:
    """Supply complete auditable GHG inventory, line-item provenance, and raw-feed anomaly data."""
    inv, summary = api.inventory.get_inventory(year)
    kpis = api.inventory.get_kpis(year)
    issues = api.inventory.get_data_quality_issues(year)
    inv_hist = pd.read_csv(ROOT_DIR / "data" / "05_scenarios" / "published_inventory_history.csv")
    rates = api.live.get_live_currency_rates()
    score = api.inventory.get_benchmark_score(year if year in (2023, 2024) else 2024)

    # Clean and structure summary rows
    summary_rows = []
    tot = float(kpis.get("total_market", 1.0))
    for _, r in summary.iterrows():
        sc = str(r.get("scope", ""))
        cat = str(r.get("category", ""))
        val = float(r.get("tco2e", 0.0))
        share = round((val / tot) * 100.0, 2) if tot > 0 else 0.0
        summary_rows.append({
            "scope": sc,
            "category": cat,
            "tco2e": round(val, 2),
            "share_pct": share,
        })

    # Sort line items by tCO2e descending
    line_items = inv.sort_values("tco2e", ascending=False).head(150).to_dict(orient="records")

    payload = {
        "year": year,
        "kpis": kpis,
        "summary": summary_rows,
        "line_items": line_items,
        "issues": issues.to_dict(orient="records"),
        "issues_count": len(issues),
        "history": inv_hist.to_dict(orient="records"),
        "exchange_rates": rates,
        "benchmark": score,
        "data_lineage": {
            "erp_lines": "data/02_raw_feeds/erp_purchase_lines_2021_2025.csv (10,480 ERP records)",
            "energy_meters": "data/02_raw_feeds/energy_meter_readings.csv (monthly Säkylä & Kantvik meters)",
            "goo_registry": "data/02_raw_feeds/goo_registry_statement.csv (100% wind GoOs cancelled)",
            "fuels": "data/02_raw_feeds/fuel_deliveries.csv & fuel_stock_changes.csv",
            "refrigerants": "data/02_raw_feeds/refrigerant_service_log.csv (R404A/R449A service logs)",
            "emission_factors": "data/01_master/emission_factor_library.csv (IPCC AR6 GWP100)",
            "published_history": "data/05_scenarios/published_inventory_history.csv (2019-2024 published)",
        },
    }
    return JSONResponse(_clean(payload))


@app.get("/api/nature/catchments-data")
def get_nature_catchments_data(year: int = Query(default=2025)) -> JSONResponse:
    """Supply complete SBTN Freshwater Step 1 & 2 Prioritization, Catchment Ledger, and Riparian Buffer Telemetry."""
    c_df, merged_par = api.nature.get_catchment_priorities(year)
    nat_kpis = api.nature.get_catchment_kpis(year)

    # Hotspot parcels (steep slope > 3% and missing buffer strip)
    hotspots = (
        merged_par[(merged_par["slope_pct"] > 3.0) & (merged_par["buffer_strip"] == False)]
        .sort_values("slope_pct", ascending=False)
        .head(40)
        .copy()
    )
    hotspot_rows = []
    for _, h in hotspots.iterrows():
        hotspot_rows.append({
            "parcel_id": str(h["parcel_id"]),
            "farm_id": str(h.get("farm_id_x", h.get("farm_id", ""))),
            "catchment_id": str(h["catchment_id"]),
            "crop": str(h.get("crop", "pea")),
            "area_ha": round(float(h["area_ha"]), 2),
            "slope_pct": round(float(h["slope_pct"]), 1),
            "dist_to_water_m": round(float(h.get("dist_to_water_m", 150.0)), 0),
            "p_test_mgl": round(float(h.get("p_test_mgl_latest", 12.0)), 1),
            "soil_class": str(h.get("soil_class_soilmap", "Mineral")),
        })

    origins_path = ROOT_DIR / "data" / "06_nature" / "origin_state_of_nature_indicative.csv"
    origins_df = pd.read_csv(origins_path) if origins_path.exists() else pd.DataFrame()

    loads_path = ROOT_DIR / "data" / "06_nature" / "monitored_catchment_loads.csv"
    loads_df = pd.read_csv(loads_path) if loads_path.exists() else pd.DataFrame()

    payload = {
        "year": year,
        "kpis": nat_kpis,
        "catchments": c_df.to_dict(orient="records"),
        "hotspots": hotspot_rows,
        "hotspots_total_count": int(((merged_par["slope_pct"] > 3.0) & (merged_par["buffer_strip"] == False)).sum()),
        "total_parcels_evaluated": len(merged_par),
        "buffer_protected_parcels": int((merged_par["buffer_strip"] == True).sum()),
        "unprotected_parcels": int((merged_par["buffer_strip"] == False).sum()),
        "origins": origins_df.to_dict(orient="records"),
        "monitored_loads": loads_df.head(40).to_dict(orient="records"),
        "data_lineage": {
            "catchments": "data/06_nature/catchments.csv (42 Finnish & Nordic sub-basins)",
            "parcels": f"data/01_master/parcels.csv ({len(merged_par):,} contract parcels, slope & buffer strips)",
            "crops": "data/03_farming/parcel_crop_history_and_plan.csv (Apetit contract crop plans)",
            "monitored_loads": f"data/06_nature/monitored_catchment_loads.csv ({len(loads_df):,} river station nutrient samples)",
            "origins": f"data/06_nature/origin_state_of_nature_indicative.csv ({len(origins_df):,} sourcing origin WRI Aqueduct baselines)",
        },
    }
    return JSONResponse(_clean(payload))


@app.get("/api/pathways/details")
def get_pathways_details(scope: str = Query(default="all")) -> JSONResponse:
    """Supply complete Decarbonisation Levers, MACC Curve data, Structural Events, and NGFS Transition Scenarios."""
    levers = api.pathway.get_levers()
    events = api.pathway.get_structural_events()
    scenarios = api.pathway.get_transition_scenarios()

    sc_lower = str(scope).lower().strip()
    if sc_lower != "all":
        if sc_lower == "flag":
            filtered_levers = levers[levers["flag"] == True]
        elif sc_lower in ("non_flag", "non-flag"):
            filtered_levers = levers[levers["flag"] == False]
        elif sc_lower in ("scope1", "scope2", "scope3"):
            filtered_levers = levers[levers["scope"].astype(str).str.contains(sc_lower, case=False)]
        else:
            filtered_levers = levers
    else:
        filtered_levers = levers

    # Compute physical levers and MACC curve on the filtered set
    phys = filtered_levers[filtered_levers["lever_id"] != "L27"].copy()
    macc = phys.sort_values("indicative_cost_eur_per_tco2e").reset_index(drop=True)
    macc["cumulative_abatement"] = macc["abatement_tco2e_2030_design"].cumsum()

    total_abat = float(phys["abatement_tco2e_2030_design"].fillna(0).sum())
    flag_abat = float(phys[phys["flag"] == True]["abatement_tco2e_2030_design"].fillna(0).sum())
    cost_neg = phys[phys["indicative_cost_eur_per_tco2e"] < 0]

    kpis = {
        "total_levers": len(filtered_levers),
        "physical_levers": len(phys),
        "total_abatement_tco2e": total_abat,
        "flag_abatement_share_pct": (flag_abat / total_abat * 100.0) if total_abat > 0 else 0.0,
        "net_savings_levers_count": len(cost_neg),
        "net_savings_potential_tco2e": float(cost_neg["abatement_tco2e_2030_design"].fillna(0).sum()),
        "total_capex_eur": float(filtered_levers["capex_eur"].fillna(0).sum()),
    }

    payload = {
        "scope": sc_lower,
        "kpis": kpis,
        "macc_levers": macc.to_dict(orient="records"),
        "all_levers": filtered_levers.to_dict(orient="records"),
        "events": events.to_dict(orient="records"),
        "scenarios": scenarios.to_dict(orient="records"),
        "data_lineage": {
            "levers": f"data/05_scenarios/decarbonisation_levers.csv ({len(filtered_levers)} of {len(levers)} active levers)",
            "events": f"data/05_scenarios/structural_events.csv ({len(events)} corporate boundary events)",
            "scenarios": f"data/05_scenarios/transition_scenarios.csv ({len(scenarios)} NGFS carbon price pathways)",
            "prices": "data/05_scenarios/contract_prices_and_replacement_premiums.csv",
        },
    }
    return JSONResponse(_clean(payload))


@app.get("/api/modules/{module_id}")
def get_module_data(module_id: str) -> JSONResponse:
    """Supply real dataset payloads for every sidebar navigation module."""
    m = module_id.lower()
    if m == "ghg":
        return get_inventory_details(2025)
    if m in ("sbtn", "nature"):
        return get_nature_catchments_data(2025)
    if m in ("macc", "pathways", "decarbonisation"):
        return get_pathways_details("all")
    if m == "risk":
        clim = pd.read_csv(ROOT_DIR / "data" / "04_climate" / "climate_change_signals.csv")
        pea = api.risk.simulate_crop_yields(crop="pea", scenario="ssp245")
        reg_alerts = api.early_warning.get_regional_alerts("Satakunta (Säkylä Core)", scenario="ssp245")
        return JSONResponse(_clean({
            "climate_signals": clim,
            "pea_simulation": pea,
            "regional_alerts": reg_alerts,
        }))
    if m in ("sbtn", "biodiversity"):
        return get_nature_catchments_data(2025)
    if m in ("macc", "investments"):
        return get_pathways_details("all")
    if m in ("geospatial", "twin", "simulator"):
        parcels = pd.read_csv(ROOT_DIR / "data" / "01_master" / "parcels.csv").head(250)
        farms = pd.read_csv(ROOT_DIR / "data" / "01_master" / "farm_registry.csv").head(120)
        scen = pd.read_csv(ROOT_DIR / "data" / "05_scenarios" / "transition_scenarios.csv")
        return JSONResponse(_clean({"parcels": parcels, "farms": farms, "scenarios": scen}))
    raise HTTPException(status_code=404, detail=f"Unknown module '{module_id}'")


@app.get("/api/embed/digital-twin-3d", response_class=HTMLResponse)
def embed_digital_twin_3d(farm_id: str = Query(default="FARM_0001")) -> HTMLResponse:
    """Render the realistic 3D Isometric Farm Digital Twin Estate + Telemetry HUD."""
    from components.satellite_3d_map import build_isometric_farm_twin_3d_html
    farm_data = api.twin.get_farm_details(farm_id)
    stats = farm_data["stats"]
    parcels_raw = farm_data["parcels"]
    crop = str(farm_data.get("crop") or "pea").lower()
    html = build_isometric_farm_twin_3d_html(
        farm_lat=float(farm_data["lat"]),
        farm_lon=float(farm_data["lon"]),
        parcels_raw=parcels_raw,
        farm_id=farm_id,
        crop=crop,
        base_yield=float(stats["baseline_mean_yield_t_ha"]),
        height_px=620,
    )
    return HTMLResponse(content=html)


@app.get("/api/embed/biodiversity-map", response_class=HTMLResponse)
def embed_biodiversity_map(radius_km: float = Query(default=25.0)) -> HTMLResponse:
    """Render the Split-View Circular CORINE Habitat Mosaic + Satellite Biodiversity Explorer."""
    from components.satellite_3d_map import build_biodiversity_hotspots_explorer_html
    catchments_gj = api.biodiversity.get_catchments_geojson()
    farms_gj = api.biodiversity.get_farms_geojson(max_farms=116)
    water_gj = api.biodiversity.get_water_bodies_geojson()
    prot_gj = api.biodiversity.get_protected_areas_geojson()
    origin_path = ROOT_DIR / "data" / "06_nature" / "origin_state_of_nature_indicative.csv"
    origin_df = pd.read_csv(origin_path) if origin_path.exists() else None
    html = build_biodiversity_hotspots_explorer_html(
        catchments_gj=catchments_gj,
        farms_gj=farms_gj,
        water_bodies_gj=water_gj,
        protected_gj=prot_gj,
        origin_df=origin_df,
        center_lat=61.048,
        center_lon=22.338,
        radius_km=float(radius_km),
        farm_count=len(farms_gj["features"]),
    )
    return HTMLResponse(content=html)


@app.get("/api/embed/geospatial-map", response_class=HTMLResponse)
def embed_geospatial_map() -> HTMLResponse:
    """Render the User-Friendly Realistic Satellite Geospatial Command Center."""
    from components.satellite_3d_map import build_geospatial_command_center_html
    sites_df = api.geo.get_sites()
    parcels_df = api.geo.get_parcels(year=2025, crop="all", buffer_only=None, limit=200).copy()
    shipments_path = ROOT_DIR / "data" / "02_raw_feeds" / "shipments.csv"
    shipments_df = pd.read_csv(shipments_path) if shipments_path.exists() else None
    wx = api.geo.fetch_live_weather()
    html = build_geospatial_command_center_html(
        sites_df=sites_df,
        parcels_df=parcels_df,
        shipments_df=shipments_df,
        weather_info=wx,
    )
    return HTMLResponse(content=html)


@app.get("/api/risk/regional-data")
def get_risk_regional_data(
    region: str = Query(default="Satakunta (Säkylä Core)"),
    scenario: str = Query(default="ssp245"),
    crop: str = Query(default="pea"),
    metric: str = Query(default="rainfall"),
) -> JSONResponse:
    """Supply comprehensive multi-crop risk, regional early warning alerts, and verified dataset lineage."""
    reg_alerts = api.early_warning.get_regional_alerts(region, scenario=scenario)
    crop_sim = api.risk.simulate_crop_yields(crop=crop, scenario=scenario)

    hist_pts = crop_sim.pop("historical_df").to_dict(orient="records") if "historical_df" in crop_sim else []
    near_pts = crop_sim.pop("near_term_df").to_dict(orient="records") if "near_term_df" in crop_sim else []
    long_pts = crop_sim.pop("long_term_df").to_dict(orient="records") if "long_term_df" in crop_sim else []
    crop_sim["historical_series"] = hist_pts[-10:]
    crop_sim["near_term_series"] = near_pts
    crop_sim["long_term_series"] = long_pts

    signals_df = pd.read_csv(ROOT_DIR / "data" / "04_climate" / "climate_change_signals.csv")
    scen_signals = signals_df[signals_df["scenario"] == scenario].to_dict(orient="records")

    sv = pd.read_csv(ROOT_DIR / "data" / "03_farming" / "farm_survey_fi.csv")
    crop_sv = sv[sv["crop"] == crop]
    sv_stats = {
        "crop": crop,
        "sample_size": len(crop_sv),
        "mean_yield_t_ha": round(float(crop_sv["yield_t_ha"].mean()), 2) if not crop_sv.empty else 0.0,
        "median_yield_t_ha": round(float(crop_sv["yield_t_ha"].median()), 2) if not crop_sv.empty else 0.0,
        "irrigated_pct": round(float(crop_sv["irrigated"].mean() * 100.0), 1) if not crop_sv.empty else 0.0,
        "catch_crop_adoption_pct": round(float(crop_sv["catch_crop_share"].mean() * 100.0), 1) if not crop_sv.empty else 0.0,
        "avg_n_fert_kg_ha": round(float(crop_sv["n_mineral_kg_ha"].mean()), 1) if not crop_sv.empty else 0.0,
    }

    # Aggregate empirical weather stats from weather_monthly_1991_2060.csv
    api.risk._load()
    clim_df = api.risk._climate_df
    hist_wx = clim_df[(clim_df["scenario"] == "historical") & (clim_df["year"].between(1991, 2020))]
    fut_wx = clim_df[(clim_df["scenario"] == scenario) & (clim_df["year"].between(2041, 2060))]
    weather_summary = {
        "baseline_tmean_c": round(float(hist_wx["tmean_c"].mean()), 2),
        "baseline_precip_mm": round(float(hist_wx["precip_mm"].mean()), 1),
        "baseline_hot_days_per_yr": round(float(hist_wx.groupby("year")["hot_days_tmax_ge_27"].sum().mean()), 1),
        "future_tmean_c": round(float(fut_wx["tmean_c"].mean()), 2),
        "future_precip_mm": round(float(fut_wx["precip_mm"].mean()), 1),
        "future_hot_days_per_yr": round(float(fut_wx.groupby("year")["hot_days_tmax_ge_27"].sum().mean()), 1),
        "warming_delta_c": round(float(fut_wx["tmean_c"].mean() - hist_wx["tmean_c"].mean()), 2),
    }

    avail_regions = list(api.early_warning.get_available_regions().keys())
    avail_crops = api.risk.get_supported_crops()

    payload = {
        "region": region,
        "scenario": scenario,
        "crop": crop,
        "metric": metric,
        "available_regions": avail_regions,
        "available_crops": avail_crops,
        "regional_alerts": reg_alerts,
        "crop_simulation": crop_sim,
        "climate_signals": scen_signals,
        "survey_ground_truth": sv_stats,
        "weather_summary": weather_summary,
        "data_lineage": {
            "climate_monthly": "data/04_climate/weather_monthly_1991_2060.csv (139,104 records · 84 grid cells)",
            "climate_signals": "data/04_climate/climate_change_signals.csv (AR6 downscaled monthly factors)",
            "grid_cells": "data/01_master/climate_grid_cells.csv (84 sub-regional geographic cells)",
            "farm_survey": f"data/03_farming/farm_survey_fi.csv ({len(crop_sv):,} {crop} field survey audits)",
            "parcels": f"data/01_master/parcels.csv ({reg_alerts.get('parcels_at_risk', 0):,} contract parcels at risk)",
        },
    }
    return JSONResponse(_clean(payload))


@app.get("/api/embed/climate-map", response_class=HTMLResponse)
def embed_climate_map(
    region: str = Query(default="Satakunta (Säkylä Core)"),
    metric: str = Query(default="rainfall"),
    scenario: str = Query(default="ssp245"),
    crop: str = Query(default="pea"),
) -> HTMLResponse:
    """Render the exact reference Drought Early Warning & Regional Precipitation Choropleth Geomap."""
    from components.satellite_3d_map import build_drought_choropleth_map_html
    alerts = api.early_warning.get_regional_alerts(region, scenario=scenario)
    ts = alerts.get("time_series", {})
    rain_def = float(ts.get("rainfall_deficit_pct", -20.0))
    soil_def = float(ts.get("moisture_deficit_pct", -20.0))

    map_iframe_html = build_drought_choropleth_map_html(
        center_lat=float(alerts.get("lat", 61.05)),
        center_lon=float(alerts.get("lon", 22.35)),
        region_name=alerts.get("region_name", region),
        metric_mode="rainfall" if "rain" in metric.lower() else "moisture",
        rainfall_deficit_pct=rain_def,
        moisture_deficit_pct=soil_def,
        height_px=470,
    )
    return HTMLResponse(content=map_iframe_html)
