"""Method constants used by the reference calculator (generated from the dataset build).
All values are documented in docs/METHODOLOGY.md with their sources."""

GRID_FI_LB = {2019: 0.09, 2020: 0.068, 2021: 0.075, 2022: 0.066, 2023: 0.038, 2024: 0.03, 2025: 0.026}

RESIDUAL_FI = {2019: 0.354, 2020: 0.37, 2021: 0.38, 2022: 0.39, 2023: 0.4, 2024: 0.406, 2025: 0.406}

GRID_SE_LB = {2019: 0.012, 2020: 0.012, 2021: 0.012, 2022: 0.012, 2023: 0.012, 2024: 0.012, 2025: 0.012}

RESIDUAL_SE = {2019: 0.04, 2020: 0.045, 2021: 0.04, 2022: 0.04, 2023: 0.038, 2024: 0.036, 2025: 0.035}

FUEL_EF_T_PER_MWH = {'natural_gas': 0.2009,
 'lng': 0.1991,
 'lpg': 0.2336,
 'light_fuel_oil': 0.2668,
 'heavy_fuel_oil': 0.284,
 'diesel': 0.211,
 'milled_peat': 0.3874,
 'wood_chips': 0.0,
 'wood_pellets': 0.0,
 'biogas': 0.0,
 'hvo': 0.0,
 'oilseed_sidestream': 0.0}

FUEL_BIOGENIC_T_PER_MWH = {'wood_chips': 0.4032,
 'wood_pellets': 0.4032,
 'biogas': 0.198,
 'hvo': 0.264,
 'oilseed_sidestream': 0.45,
 'diesel': 0.035}

FUEL_RENEWABLE = ['biogas', 'hvo', 'oilseed_sidestream', 'wood_chips', 'wood_pellets']

REFRIGERANT_GWP = {'R717_ammonia': 0,
 'R744_co2': 1,
 'R404A': 4728,
 'R507A': 4775,
 'R449A': 1504,
 'R410A': 2256,
 'R134a': 1530,
 'R32': 771}

HEAT_LB_EF = {2019: 0.16, 2020: 0.15, 2021: 0.15, 2022: 0.14, 2023: 0.13, 2024: 0.12, 2025: 0.11}

NCV = {'lng_t': 13.5, 'lpg_t': 12.8, 'lfo_l': 0.01, 'diesel_l': 0.0099, 'hvo_l': 0.0095, 'wood_m3': 0.8}

FARM_EF = {'ef1_synthetic': 0.016,
 'ef1_organic': 0.006,
 'ef1_n2o_n_per_n': 0.01,
 'frac_gasf': 0.05,
 'frac_gasm': 0.21,
 'frac_leach': 0.24,
 'ef4_n2o_n': 0.014,
 'ef5_n2o_n': 0.011,
 'n2o_gwp': 273,
 'ch4_gwp': 27.0,
 'n2o_n_to_n2o': 1.5714285714285714,
 'fert_n_prod': 3.7,
 'fert_n_prod_lowcarbon': 0.9,
 'fert_p_prod': 1.6,
 'fert_k_prod': 0.5,
 'diesel_ttw': 2.1,
 'diesel_ttw_fossil': 2.66,
 'diesel_wtt': 0.61,
 'lime': 0.44,
 'org_soil_co2_t_ha': 29.0,
 'org_soil_co2_grass_t_ha': 20.9,
 'org_soil_n2o_n_kg_ha': 13.0,
 'spray_pass': 8.0}

MGMT_NORMS = {'pea': {'n': 25, 'p': 12, 'diesel': 85, 'lime': 0.35, 'kwh_t': 8, 'irr': 0.1, 'sprays': 2},
 'potato': {'n': 95, 'p': 35, 'diesel': 170, 'lime': 0.35, 'kwh_t': 35, 'irr': 0.55, 'sprays': 8},
 'carrot': {'n': 100, 'p': 30, 'diesel': 160, 'lime': 0.35, 'kwh_t': 30, 'irr': 0.6, 'sprays': 5},
 'spinach': {'n': 130, 'p': 20, 'diesel': 110, 'lime': 0.35, 'kwh_t': 6, 'irr': 0.7, 'sprays': 2},
 'turnip_rape': {'n': 95, 'p': 15, 'diesel': 75, 'lime': 0.35, 'kwh_t': 45, 'irr': 0.0, 'sprays': 3},
 'barley': {'n': 95, 'p': 12, 'diesel': 80, 'lime': 0.35, 'kwh_t': 60, 'irr': 0.0, 'sprays': 2},
 'oats': {'n': 85, 'p': 12, 'diesel': 80, 'lime': 0.35, 'kwh_t': 60, 'irr': 0.0, 'sprays': 1},
 'wheat': {'n': 120, 'p': 14, 'diesel': 85, 'lime': 0.35, 'kwh_t': 60, 'irr': 0.0, 'sprays': 3},
 'grass_ley': {'n': 150, 'p': 15, 'diesel': 95, 'lime': 0.35, 'kwh_t': 0, 'irr': 0.0, 'sprays': 0},
 'fallow': {'n': 0, 'p': 0, 'diesel': 15, 'lime': 0.0, 'kwh_t': 0, 'irr': 0.0, 'sprays': 0}}

RESIDUE_N_PER_T = {'pea': 6.0,
 'potato': 1.2,
 'carrot': 1.0,
 'spinach': 1.5,
 'turnip_rape': 18.0,
 'barley': 6.5,
 'oats': 7.0,
 'wheat': 6.5,
 'grass_ley': 3.0,
 'fallow': 0.0}

USE_PHASE_KWH_PER_KG = {'frozen_vegetables': 0.71,
 'ready_meals_frozen': 0.96,
 'fish_products': 0.96,
 'frozen_pizza': 1.8099999999999998,
 'rapeseed_oil_bottled': 0.0,
 'rapeseed_oil_bulk': 0.0,
 'rapeseed_meal_expeller': 0.0,
 'blackgrain_powder': 0.0}

PACK_KG_PER_T = {'frozen_vegetables': (19.0, 32.0),
 'ready_meals_frozen': (24.0, 60.0),
 'fish_products': (22.0, 55.0),
 'frozen_pizza': (14.0, 85.0),
 'rapeseed_oil_bottled': (52.0, 18.0),
 'rapeseed_oil_bulk': (0.6, 0.0),
 'rapeseed_meal_expeller': (0.0, 0.0),
 'blackgrain_powder': (30.0, 20.0)}

EOL_PLASTIC_EF_T = 1.40485

EOL_BOARD_EF_T = 0.07934999999999999

FUEL_WTT = {'lng': 'EF-WTT-LNG',
 'lpg': 'EF-WTT-LPG',
 'light_fuel_oil': 'EF-WTT-LFO',
 'diesel': 'EF-WTT-DIESEL',
 'natural_gas': 'EF-WTT-NG',
 'wood_chips': 'EF-WTT-WOOD',
 'oilseed_sidestream': 'EF-WTT-WOOD',
 'biogas': 'EF-WTT-BIOGAS',
 'hvo': 'EF-WTT-HVO'}

FX_PER_EUR = {'EUR': 1.0, 'SEK': 11.4, 'USD': 1.08}

MARKET_GRID = {'FI': GRID_FI_LB, 'SE': GRID_SE_LB, 'EXPORT_EU': {y: 0.230 for y in range(2015, 2031)}}
