# 🌾 AgroScope360 — Corporate ESG & Climate Intelligence Platform

> **Full-Spectrum Carbon, Catchment & Climate Risk Intelligence for the Agri-Food Value Chain**

AgroScope360 is an enterprise-grade sustainability decision cockpit linking primary agricultural production, 3D farm digital twins, watershed nature metrics (SBTN), multi-decadal climate risk projections (1991–2060), and auditable greenhouse gas (GHG) accounting to 2030 Marginal Abatement Cost Curve (MACC) investment pathways.

---

## 🚀 Key Modules & Capabilities

1. **Executive Overview Cockpit**
   * Board-level intelligence uniting audited GHG footprints (Scopes 1–3, AR6), contract farm networks, river catchment loads, and 2030 MACC decarbonisation investments.
   * Multi-year historical corporate emissions trajectory with structural baseline restatements and SBTi 1.5°C reduction milestones.

2. **🚜 3D Farm Digital Twin**
   * WebGL Three.js interactive 3D terrain mesh with contract farm polygon layouts, soil organic carbon %, parcel slope gradients, and field moisture telemetry.

3. **🌍 3D Geospatial Command Center**
   * High-resolution spatial mapping of industrial processing facilities, supplier clusters, procurement catchments, and inbound freight logistics routes.

4. **⚠️ Agronomic Climate Risk & Crop Yield Simulator**
   * Multi-decadal daily & monthly weather projections (1991–2060) across Nordic grid cells.
   * Quantifies flowering heat-stress indices and drought volatility across key field crops (Green Pea, Ware Potato, Carrot, Turnip Rape).

5. **🌲 Biodiversity & Nature Hotspots**
   * High-resolution satellite lens with 19-class CORINE Land Cover legends, Natura 2000 conservation habitats, and riparian buffer strip opportunities.

6. **📊 GHG Protocol Inventory (Scopes 1, 2 & 3)**
   * Audited line-item accounting with automated anomaly screening (detecting unit slips, duplicate invoices, and missing meter logs).
   * Supports market-based vs location-based Scope 2 and SBTi FLAG (Forest, Land and Agriculture) guidance.

7. **🏞️ SBTN Nature & Freshwater Catchments**
   * Stage 3 Science Based Targets for Nature freshwater analysis across 41 Nordic river basins.
   * Ranks catchments by agricultural nutrient delivery (Phosphorus & Nitrogen) combined with ecological receiving-water sensitivity.

8. **🛣️ Decarbonisation Pathways & 2030 MACC**
   * Dynamic Marginal Abatement Cost Curve across 30 validated levers.
   * Interactive scope filtering (`Scope 3 FLAG`, `Scopes 1–3 Non-FLAG`, `Scope 1`, `Scope 2`, `Scope 3`) with dynamic CAPEX, OPEX, and net-savings tracking.

9. **🧪 TCFD Transition Scenario Simulator**
   * Stress-test corporate performance against three forward-looking climate pathways: Net Zero 2040, Delayed Transition, and Current Policies.

10. **🤖 Grounded AI Research Assistant & Evidence Engine**
    * Deterministic CSV query retrieval with 12 verifiable scientific evidence cards ([E1]–[E12]), plus optional Google Gemini natural language synthesis.

---

## 🛠️ Architecture & Tech Stack

* **Frontend:** Responsive Nordic Climate Precision UI built with Tailwind CSS, Three.js WebGL, Leaflet, and vanilla modern JavaScript.
* **Backend:** FastAPI high-performance asynchronous REST API (`web_server.py`) + Streamlit multi-view analytics studio (`app.py`).
* **Core Analytics & Data Engine:** Python, Pandas, NumPy, PyArrow for local parquet and CSV data streaming.
* **Audit & Compliance Standards:** GHG Protocol Corporate Standard (AR6 GWP100), CSRD ESRS E1 & E4, SBTi FLAG v1.1, SBTN Freshwater Stage 3.

---

## 💻 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/rohitverma984/AgroScope360.git
cd AgroScope360
```

### 2. Set up virtual environment & dependencies
```bash
cd prototype
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Launch the platform
* **FastAPI Web Application:**
  ```bash
  uvicorn web_server:app --host 0.0.0.0 --port 8000 --reload
  ```
  Open **`http://localhost:8000`** in your browser.

* **Streamlit Multi-View Studio:**
  ```bash
  streamlit run app.py --server.port 8501
  ```
  Open **`http://localhost:8501`** in your browser.

---

## 📄 License
This project is licensed under the Apache 2.0 License.
