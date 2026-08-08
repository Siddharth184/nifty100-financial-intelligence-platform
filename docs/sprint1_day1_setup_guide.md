# 📘 Sprint 1 — Day 1: Production Environment Setup Guide
**Project:** Nifty100 Financial Intelligence Platform  
**Author:** Senior Data Engineer & Software Engineering Mentor  
**Target Audience:** Data Analyst & Engineering Interns  

---

## 📌 Executive Overview

Welcome to **Sprint 1 — Day 1** of building the **Nifty100 Financial Intelligence Platform**!

In real-world data engineering and analytics companies, writing code is only 20% of the job. The remaining 80% relies on **software architecture, environment reproducibility, configuration management, automated logging, and clean documentation**. 

Today, we are laying down the enterprise-grade foundation for our platform.

---

## 1. 📁 Scalable Production Folder Structure

### Folder Tree

```text
nifty100-financial-intelligence-platform/
│
├── config/                   # External configuration files & YAML definitions
│   └── .gitkeep
│
├── data/                     # Data storage hierarchy (Git ignored)
│   ├── raw/                  # Inbound raw 12 Excel dataset files
│   ├── processed/            # Standardized CSV/Parquet dataset outputs
│   └── backup/               # Immutable historical copies of raw data
│
├── db/                       # Database initialization scripts and SQLite storage
│   ├── schema.sql            # DDL database schema creation script
│   └── nifty100.db           # SQLite binary database file
│
├── docs/                     # Architecture specifications & Sprint documentation
│   └── sprint1_day1_setup_guide.md
│
├── logs/                     # Automated application log files (rotated)
│   └── app.log
│
├── notebooks/                # Jupyter notebooks for Exploratory Data Analysis (EDA)
│   └── .gitkeep
│
├── output/                   # Audit logs & ETL exception output files
│   ├── load_audit.csv
│   └── validation_failures.csv
│
├── reports/                  # Automated PDF & HTML financial reports
│   └── .gitkeep
│
├── scripts/                  # One-off database migration & utility scripts
│   └── .gitkeep
│
├── src/                      # Production Core Python Application Package
│   ├── __init__.py
│   ├── analytics/            # Financial ratio & KPI computation engine (50+ metrics)
│   ├── config/               # Environment & configuration loader
│   │   ├── __init__.py
│   │   └── config.py
│   ├── dashboard/            # Interactive Streamlit Web UI application
│   ├── etl/                  # Extract, Transform, Load (ETL) pipeline modules
│   └── utils/                # Logging and helper utility modules
│       ├── __init__.py
│       └── logger.py
│
├── tests/                    # Automated Pytest test suite
│   ├── unit/                 # Unit tests for functions/classes
│   └── integration/          # End-to-end ETL integration tests
│
├── .env                      # Local secret environment variables (Git ignored)
├── .gitignore                # Git repository exclusion rules
├── Makefile                  # Cross-platform automation task runner
├── requirements.txt          # Python dependency specifications
├── README.md                 # Project root GitHub documentation
└── main.py                   # Application entrypoint execution script
```

### Folder Purpose Breakdown

| Folder Name | Purpose | Why Companies Use This |
| :--- | :--- | :--- |
| `src/` | Holds all core business logic and executable Python modules. | Keeps application logic separated from configuration, scripts, and tests. |
| `data/raw/` | Stores original, unedited 12 Excel financial workbooks. | **Data Immutability Principle**: Raw incoming data should never be edited or overwritten. |
| `data/processed/` | Stores cleaned, validated, and normalized data formats. | Speeds up analytical queries without requiring re-parsing raw files every time. |
| `data/backup/` | Contains timestamped backup copies of inbound data. | Ensures disaster recovery if data files are corrupted during ETL runs. |
| `db/` | Holds DDL SQL scripts (`schema.sql`) and SQLite database files. | Centralizes relational schema management and database file paths. |
| `config/` | Stores external non-secret settings (YAML/JSON schema rules). | Allows business logic customization without altering Python source code. |
| `logs/` | Captures rotated application runtime logs. | Crucial for auditing, debugging, and production failure diagnosis. |
| `output/` | Holds ETL validation failure reports (`validation_failures.csv`). | Gives data analysts immediate feedback on bad data rows. |
| `reports/` | Stores generated PDF/HTML reports for executive leadership. | Decouples report generation outputs from internal data processing. |
| `scripts/` | One-off administrative or database setup scripts. | Keeps maintenance utilities isolated from production application code. |
| `tests/` | Unit and integration test suites using `pytest`. | Enables Continuous Integration (CI) and prevents regression bugs. |
| `notebooks/` | Interactive Jupyter notebooks for experimental EDA. | Keeps dirty exploratory code separated from clean, production-ready `src/` code. |

### Industry Context & Best Practices

- **Why this approach?** This separation of concerns follows the **Standard Python Project Layout** recommended by PEP 518 and top data engineering teams (Airbnb, Netflix).
- **Alternative Approaches:** Flat folder structure (putting everything in one root directory). 
- **Beginner Mistakes:** Putting raw data, Jupyter notebooks, and python scripts all in the root folder, leading to circular imports, lost raw data, and unmaintainable code.

---

## 2. 🐍 Python Virtual Environment & Dependency Isolation

### Why Virtual Environments are Mandatory

In Python, installing packages globally (`pip install pandas`) installs them into your computer's main Python installation. 

#### Why Companies Never Install Packages Globally:
1. **Dependency Hell (Version Conflicts):** Project A requires `Pandas 1.5`, while Project B requires `Pandas 2.2`. Global installation forces you to pick one, breaking the other project.
2. **Reproducibility:** A production server (AWS/GCP) must mirror the exact package versions used on your developer laptop.
3. **Security & Cleanliness:** Avoids polluting system Python files, which OS utilities (like macOS/Linux system scripts) depend on.

### How Dependency Isolation Works
A virtual environment creates a standalone directory (`venv/`) containing:
- Its own copy of the Python interpreter executable.
- Its own `site-packages/` directory for pip installations.

When activated, your terminal's `PATH` variable is modified to point to `venv/bin/python` instead of system Python.

### Setup Commands by Operating System

#### 🪟 Windows (PowerShell / Command Prompt)
```powershell
# 1. Navigate to project root
cd d:\imp_code\Data_Intern\N100\nifty100-financial-intelligence-platform

# 2. Create virtual environment named 'venv'
python -m venv venv

# 3. Activate environment (PowerShell)
.\venv\Scripts\Activate.ps1

# (Optional - If execution policy error occurs in PowerShell)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# 4. Deactivate when done
deactivate
```

#### 🍎 macOS (Terminal) / 🐧 Linux (Bash)
```bash
# 1. Navigate to project root
cd nifty100-financial-intelligence-platform

# 2. Create virtual environment
python3 -m venv venv

# 3. Activate environment
source venv/bin/activate

# 4. Deactivate when done
deactivate
```

---

## 3. 📦 `requirements.txt` Library Breakdown

Here is our production `requirements.txt`:

```text
# Data Processing & Analysis
pandas>=2.0.0
numpy>=1.24.0

# Database & ORM
SQLAlchemy>=2.0.0

# Excel File Handling
openpyxl>=3.1.0

# Dashboard & Visualization
streamlit>=1.25.0
plotly>=5.15.0

# PDF Report Generation
reportlab>=4.0.0

# HTTP Requests & APIs
requests>=2.31.0

# Environment Variable Management
python-dotenv>=1.0.0

# Testing Framework
pytest>=7.4.0

# Code Quality & Formatting
black>=23.7.0
ruff>=0.0.280

# Interactive Notebooks
jupyter>=1.0.0
ipykernel>=6.25.0
```

### Library Purpose Matrix

| Library | Category | Why We Need It in Nifty100 |
| :--- | :--- | :--- |
| `pandas` | Data Ingestion | Dataframe manipulation for high-performance financial data transformations. |
| `numpy` | Numerical Computing | Vectorized math functions for financial ratio calculations (CAGR, Volatility). |
| `SQLAlchemy` | Database ORM | Abstraction layer over SQLite, allowing modular SQL query execution. |
| `openpyxl` | Excel Engine | Under-the-hood engine required by Pandas to read complex multi-sheet `.xlsx` datasets. |
| `streamlit` | UI Web App | Rapid creation of interactive financial intelligence dashboards. |
| `plotly` | Financial Charts | Interactive candlestick, waterfall, and sectoral comparison charts. |
| `reportlab` | Reporting | Programmatic generation of executive PDF financial summary reports. |
| `requests` | HTTP Client | Fetching live stock market prices or macroeconomic indicators via REST APIs. |
| `python-dotenv` | Config Security | Dynamically loads environment variables from `.env` into Python `os.environ`. |
| `pytest` | Testing | Automated unit testing framework for ETL and ratio calculation validation. |
| `black` | Code Formatter | The uncompromised Python code formatter used across top tech companies. |
| `ruff` | Code Linter | Blazing-fast Rust-based linter that enforces PEP8 style rules and catches bugs. |
| `jupyter` | Exploratory Analysis | Interactive notebook environment for ad-hoc financial investigation. |

---

## 4. 🔒 Environment Variables (`.env`) & Security

### Why Configuration Should Never Be Hardcoded
Hardcoding database paths, credentials, API keys, or IP addresses inside `.py` code files is a major security risk and bad practice.

1. **Security Risk:** Hardcoded database passwords or secrets committed to GitHub can lead to instant security breaches.
2. **Environment Portability:** Your local machine might use `sqlite:///db/nifty100.db`, whereas the staging server uses PostgreSQL `postgresql://user:pass@staging-db:5432/nifty`. Using environment variables lets you change target environments without changing code.

### Production `.env` File
```env
APP_NAME="Nifty100 Financial Intelligence Platform"
ENVIRONMENT="development"
DEBUG=True

DATABASE_URL="sqlite:///db/nifty100.db"
DB_PATH="db/nifty100.db"
DB_SCHEMA_PATH="db/schema.sql"

LOG_LEVEL="INFO"
LOG_DIR="logs"
LOG_FILE="logs/app.log"

DATA_RAW_DIR="data/raw"
DATA_PROCESSED_DIR="data/processed"
DATA_BACKUP_DIR="data/backup"
OUTPUT_DIR="output"
REPORTS_DIR="reports"
```

### The 12-Factor App Methodology
Modern enterprise software follows the **12-Factor App** rules. Factor III explicitly states: **"Store config in the environment"**.

---

## 5. ⚙️ Configuration Module (`src/config/config.py`)

### Python Source Code
```python
"""
Configuration module for Nifty100 Financial Intelligence Platform.
Reads environment variables from .env file and provides structured configuration settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Define base directory of the project (3 levels up from src/config/config.py)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variables from .env file located at the project root
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

class Config:
    """Application Configuration class."""
    
    # Application identity settings
    APP_NAME: str = os.getenv("APP_NAME", "Nifty100 Financial Intelligence Platform")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")

    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'db' / 'nifty100.db'}")
    DB_PATH: Path = BASE_DIR / os.getenv("DB_PATH", "db/nifty100.db")
    DB_SCHEMA_PATH: Path = BASE_DIR / os.getenv("DB_SCHEMA_PATH", "db/schema.sql")

    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR: Path = BASE_DIR / os.getenv("LOG_DIR", "logs")
    LOG_FILE: Path = BASE_DIR / os.getenv("LOG_FILE", "logs/app.log")

    # Data directory paths
    DATA_RAW_DIR: Path = BASE_DIR / os.getenv("DATA_RAW_DIR", "data/raw")
    DATA_PROCESSED_DIR: Path = BASE_DIR / os.getenv("DATA_PROCESSED_DIR", "data/processed")
    DATA_BACKUP_DIR: Path = BASE_DIR / os.getenv("DATA_BACKUP_DIR", "data/backup")
    OUTPUT_DIR: Path = BASE_DIR / os.getenv("OUTPUT_DIR", "output")
    REPORTS_DIR: Path = BASE_DIR / os.getenv("REPORTS_DIR", "reports")

    @classmethod
    def ensure_directories(cls):
        """Create necessary project directories if they do not exist."""
        for dir_path in [
            cls.LOG_DIR,
            cls.DATA_RAW_DIR,
            cls.DATA_PROCESSED_DIR,
            cls.DATA_BACKUP_DIR,
            cls.OUTPUT_DIR,
            cls.REPORTS_DIR,
            cls.DB_PATH.parent,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)

def load_config() -> Config:
    """Helper function to load config and ensure required directory paths exist."""
    config = Config()
    config.ensure_directories()
    return config
```

### Detailed Code Line-by-Line Explanation

1. `from pathlib import Path`: Standard library module for object-oriented filesystem paths (cross-platform support for `/` vs `\`).
2. `from dotenv import load_dotenv`: Parses key-value pairs from `.env` file and adds them to environment variables.
3. `BASE_DIR = Path(__file__).resolve().parent.parent.parent`: Dynamically calculates absolute path to project root regardless of where script is launched.
4. `os.getenv("KEY", default_value)`: Reads environment variable safely. If key does not exist, falls back to default value.
5. `ensure_directories()`: Proactively creates all required folders (`data/raw/`, `logs/`, `db/`) automatically on application start.

---

## 6. 📝 Enterprise Logging Module (`src/utils/logger.py`)

### Why `print()` is Forbidden in Production
1. **No Timestamps or Context:** `print("Error loading file")` provides no information on when or where the error occurred.
2. **No Log Levels:** You cannot suppress debug messages in production when using `print()`.
3. **No Destination Control:** `print()` sends output only to standard console output, whereas production requires writing to rotated log files.

### Python Source Code (`src/utils/logger.py`)

```python
"""
Logging configuration module for Nifty100 Financial Intelligence Platform.
Configures both console stream logging and file logging with customizable formats.
"""

import sys
import logging
from logging.handlers import RotatingFileHandler
from src.config.config import load_config

def get_logger(name: str = "Nifty100_App") -> logging.Logger:
    """
    Creates and configures a logger instance.

    Args:
        name (str): Name of the logger module / component.

    Returns:
        logging.Logger: Configured logger instance.
    """
    config = load_config()
    
    # Create logger instance
    logger = logging.getLogger(name)
    
    # Set logging level from configuration
    log_level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Prevent duplicate handlers if logger is called multiple times
    if logger.handlers:
        return logger

    # Log line format standard: [timestamp] [level] [logger_name]: message
    log_format = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 1. Console Stream Handler (Outputs logs to stdout console)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)

    # 2. Rotating File Handler (Writes logs to file, rotates at 5MB)
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        filename=config.LOG_FILE,
        maxBytes=5 * 1024 * 1024,  # 5 MB size threshold
        backupCount=5,              # Retain last 5 rotated log files
        encoding="utf-8"
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)

    return logger
```

### Logging Levels Hierarchy

1. `DEBUG`: Detailed diagnostic information for developers (e.g., SQL queries executed).
2. `INFO`: Confirmation that things are working as expected (e.g., "50 records loaded successfully").
3. `WARNING`: Indication that something unexpected happened, but operation continues (e.g., missing optional column).
4. `ERROR`: Serious failure; software unable to perform a specific function (e.g., file not found).
5. `CRITICAL`: Fatal error; program terminates immediately (e.g., database connection down).

---

## 7. 🛠️ Automation Helper (`Makefile`)

### Makefile Content
```makefile
.PHONY: help install test load dashboard clean lint format

help:
	@echo "Available commands:"
	@echo "  make install    - Install required Python dependencies"
	@echo "  make test       - Run unit and integration tests using pytest"
	@echo "  make load       - Execute the ETL data pipeline"
	@echo "  make dashboard  - Launch the Streamlit analytics dashboard"
	@echo "  make lint       - Check code formatting and linting errors with ruff"
	@echo "  make format     - Automatically format Python code using black"
	@echo "  make clean      - Clean cache, bytecode, and log files"

install:
	pip install -r requirements.txt

test:
	pytest tests/ --verbose

load:
	python main.py

dashboard:
	streamlit run src/dashboard/app.py

lint:
	ruff check src/ tests/

format:
	black src/ tests/

clean:
	python -c "import shutil, os, glob; [shutil.rmtree(p, ignore_errors=True) for p in glob.glob('**/__pycache__', recursive=True)]; [shutil.rmtree(p, ignore_errors=True) for p in glob.glob('.pytest_cache')]; [shutil.rmtree(p, ignore_errors=True) for p in glob.glob('.ruff_cache')]"
```

*Note for Windows users:* If `make` is not natively installed on Windows PowerShell, commands can be run directly using Python or via WSL/Git Bash.

---

## 8. 🌿 Git Initialization & Professional Commit Workflow

### Initializing Git
```bash
# 1. Initialize Git repository
git init

# 2. Check status (verify .env and data files are ignored!)
git status

# 3. Add all files to staging
git add .

# 4. Commit initial setup
git commit -m "chore(setup): initialize Sprint 1 Day 1 project architecture and environment"
```

### Industry Branch Naming Standards
- `main` / `master`: Production-ready code.
- `develop`: Integration branch for sprint features.
- `feature/sprint1-day2-schema`: Feature-specific branch.
- `bugfix/fix-excel-nulls`: Hotfix branch.

### Conventional Commit Messages Standard
Format: `<type>(<scope>): <short description>`
- `feat(etl)`: Add Excel loader module for quarterly earnings.
- `fix(config)`: Fix database URL fallback path resolution.
- `docs(readme)`: Update installation instructions for macOS.
- `chore(deps)`: Upgrade pandas requirement to 2.1.0.

---

## 9. ✅ Day 1 Final Verification Checklist

| Verification Task | Command | Expected Outcome | Status |
| :--- | :--- | :--- | :---: |
| **Folder Structure** | `ls -la` | All 11 folders (`data`, `src`, `db`, `logs`, etc.) present | ✅ |
| **Virtual Environment** | `which python` / `where python` | Points inside `venv/` directory | ✅ |
| **Dependencies** | `pip list` | `pandas`, `sqlalchemy`, `streamlit`, `pytest` installed | ✅ |
| **Configuration** | `python -m src.config.config` | Prints loaded APP_NAME and valid absolute paths | ✅ |
| **Logging** | `python -m src.utils.logger` | Outputs formatted logs to stdout & `logs/app.log` | ✅ |
| **Pipeline Execution** | `python main.py` | Logs pipeline initialization without errors | ✅ |
| **Git Exclusion** | `git status` | `.env`, `logs/`, `db/*.db` are excluded by `.gitignore` | ✅ |

---

### 🚀 Next Steps (Sprint 1 — Day 2 Preview)
Tomorrow in **Day 2**, we will design the relational **SQLite Database Schema (`db/schema.sql`)** to model Nifty 100 companies, financial quarterly statements, and metrics!
