# Nifty100 Financial Intelligence Platform

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![FastAPI](https://img.shields.io/badge/FastAPI-1.0.0-009688.svg)](https://fastapi.tiangolo.com/)
[![Pytest](https://img.shields.io/badge/tests-182%20passed-brightgreen.svg)](https://docs.pytest.org/)

An enterprise-grade, end-to-end data engineering and financial intelligence platform designed to process multi-year financial statements of Nifty 100 Indian listed companies, execute automated ETL pipelines, perform schema validation, store relational metrics in SQLite, compute 50+ financial ratios, run KMeans machine learning clustering, serve a 16-endpoint REST API, and deliver interactive Streamlit executive dashboards and PDF tearsheets.

---

## 📌 Table of Contents

- [Project Overview](#-project-overview)
- [Architecture](#-architecture)
- [Directory Structure](#-directory-structure)
- [Features & Deliverables](#-features--deliverables)
- [REST API Reference (FastAPI)](#-rest-api-reference-fastapi)
- [KMeans Clustering & ML Archetypes](#-kmeans-clustering--ml-archetypes)
- [Environment Setup & Installation](#-environment-setup--installation)
- [CLI Commands & Usage](#-cli-commands--usage)
- [Testing & Quality Assurance](#-testing--quality-assurance)

---

## 🏢 Project Overview

Financial analysts and portfolio managers require fast, reliable, and standardized metrics across companies in the Nifty 100 index. Raw financial reports often arrive in unstructured Excel workbooks with varying accounting formats.

The **Nifty100 Financial Intelligence Platform** solves this by providing:
1. **Automated Excel ETL Pipeline:** Ingests and standardizes 12 core/supporting financial workbooks across 92 companies over FY2014–FY2024.
2. **Data Quality Validation:** 14 automated DQ rules catching composite key duplicates, foreign key violations, and balance sheet identity discrepancies.
3. **Structured Relational Storage:** SQLite database schema (`db/nifty100.db`) with 13 normalized tables.
4. **Financial Analytics Engine:** Computes 50+ financial KPIs (ROE, ROCE, P/E ratio, D/E, Operating Margin, CAGR, FCF conversion, CFO quality).
5. **KMeans Machine Learning Clustering:** Classifies 92 companies into 5 financial archetypes using 5 standardized financial features.
6. **FastAPI REST API Services:** 16 live endpoints for programmatic data access, screening, valuation, peer comparisons, and PDF downloads.
7. **Interactive Streamlit Dashboard:** 8 executive dashboard pages for interactive exploration.
8. **Automated PDF Reports:** 2-page institutional company tearsheets and 11-page Analyst User Guide.

---

## 🏗️ Architecture

```text
┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│   Raw Data     │ ───►│  ETL Pipeline  │ ───►│ Validation &   │
│ (12 Excel Files)│     │ (Loader/Clean) │     │ Normalization  │
└────────────────┘     └────────────────┘     └────────────────┘
                                                       │
                                                       ▼
┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│ Streamlit GUI  │ ◄───│ Financial KPIs │ ◄───│ Relational DB  │
│ & PDF Generator│     │ & ML Engine    │     │ (SQLite DB)    │
└────────────────┘     └────────────────┘     └────────────────┘
         ▲                      ▲
         │                      │
         └──────────┬───────────┘
                    │
           ┌────────────────┐
           │   FastAPI API  │
           │ (16 Endpoints) │
           └────────────────┘
```

---

## 📁 Directory Structure

```text
nifty100-financial-intelligence-platform/
│
├── config/                   # YAML configurations (screener_config.yaml, settings.yaml)
├── data/raw/                 # Ingested raw Excel workbooks
├── db/                       # SQLite database (nifty100.db)
├── docs/                     # OpenAPI schema, analyst_guide.pdf, setup guides
├── output/                   # Generated reports (cluster_labels.csv, portfolio_stats.csv, etc.)
├── pages/                    # Streamlit dashboard pages (pg_01 to pg_08)
├── reports/                  # Generated plots & PDF tearsheets
│   ├── elbow_plot.png
│   ├── correlation_heatmap.png
│   ├── pytest_report.html
│   └── tearsheets/           # 91 pre-generated company PDF tearsheets
├── src/                      # Source code modules
│   ├── analytics/            # Profitability, leverage, cagr, valuation, peer, clustering
│   ├── api/                  # FastAPI app & 8 router modules
│   ├── db/                   # SQLite connection & database managers
│   ├── dashboard/            # Dashboard visualization helpers
│   ├── etl/                  # Loader, normaliser, validator, dq_rules
│   ├── nlp/                  # Analysis text parser
│   ├── qa/                   # Audit & verification scripts
│   ├── reports/              # ReportLab PDF tearsheet generators
│   ├── screener/             # Financial Screener Filter Engine
│   └── utils/                # Logger & helpers
├── tests/                    # 182 Pytest unit & integration tests
│   ├── api/                  # FastAPI router integration tests
│   ├── dq/                   # DQ rule tests
│   ├── etl/                  # Normaliser & loader tests
│   └── kpis/                 # Financial ratio tests
├── main.py                   # Streamlit dashboard entrypoint
├── run_etl.py                # ETL pipeline runner
└── requirements.txt          # Python dependencies
```

---

## ⚡ FastAPI REST API Reference

The FastAPI service exposes 16 REST endpoints under the `/api/v1` prefix. Interactive Swagger documentation is available at `/docs`.

| Endpoint | Method | Description |
|:---|:---:|:---|
| `/api/v1/health` | GET | System health check & DB table row counts |
| `/api/v1/companies` | GET | List 92 companies (optional sector/search filters) |
| `/api/v1/companies/{ticker}` | GET | Full company profile + latest KPIs + cluster assignment |
| `/api/v1/companies/{ticker}/pl` | GET | Historical Income Statement |
| `/api/v1/companies/{ticker}/bs` | GET | Historical Balance Sheet |
| `/api/v1/companies/{ticker}/cashflow` | GET | Historical Cash Flow Statement |
| `/api/v1/companies/{ticker}/ratios` | GET | Annual Financial Ratios history |
| `/api/v1/companies/{ticker}/tearsheet` | GET | Download 2-page company PDF tearsheet |
| `/api/v1/screener` | GET | Screen universe with preset/custom filters |
| `/api/v1/sectors` | GET | List 10 broad sectors with summary stats |
| `/api/v1/sectors/{sector}/companies` | GET | Companies in a given sector |
| `/api/v1/peers/{group_name}` | GET | Peer group percentile rankings |
| `/api/v1/companies/{ticker}/peers/compare` | GET | Peer radar comparison data |
| `/api/v1/market-cap/{ticker}` | GET | Market cap and valuation multiple history |
| `/api/v1/portfolio/stats` | GET | P10..P90 universe metric distributions |
| `/api/v1/companies/{ticker}/documents` | GET | Annual report links with URL validity flag |

---

## 🤖 KMeans Clustering & ML Archetypes

All 92 Nifty 100 companies are clustered using Scikit-Learn KMeans (`n_clusters=5, random_state=42`) on 5 standardized financial features:
1. `return_on_equity_pct` (ROE)
2. `debt_to_equity` (D/E)
3. `revenue_cagr_5yr` (5-Year Sales Growth)
4. `pat_cagr_5yr` (5-Year Net Profit Growth)
5. `operating_profit_margin_pct` (OPM)

### Archetype Classifications:
- **High-Quality Compounders**: Superior ROE (>20%), robust CAGR, low leverage.
- **Defensive Stalwarts**: Stable margins, moderate growth, low debt.
- **Emerging Growth**: High revenue expansion, aggressive reinvestment.
- **Value Cyclicals**: Capital intensive, moderate ROE.
- **Leveraged Turnaround**: High leverage, recovering profitability.

---

## 🛠️ Environment Setup & Installation

```bash
# Clone the repository
git clone https://github.com/Siddharth184/nifty100-financial-intelligence-platform.git
cd nifty100-financial-intelligence-platform

# Install dependencies
pip install -r requirements.txt
```

---

## 🚀 CLI Commands & Usage

```bash
# 1. Run the full ETL pipeline & populate SQLite DB
python run_etl.py

# 2. Run KMeans Clustering & Statistics Generation
python -m src.analytics.clustering

# 3. Launch FastAPI Server (Port 8000)
uvicorn src.api.main:app --port 8000

# 4. Launch Interactive Streamlit Executive Dashboard (Port 8501)
streamlit run main.py

# 5. Run Full Pytest Test Suite (182 tests)
pytest --html=reports/pytest_report.html --self-contained-html
```

---

## 🧪 Testing & Quality Assurance

- **182 Passed Unit & Integration Tests** (0 Failures)
- Automated HTML Test Report generated at `reports/pytest_report.html`
- Strict non-fabrication rule enforced: Missing data (e.g. JIOFIN <3yrs, ATGL 0 cashflow rows) is handled without synthetic data generation.