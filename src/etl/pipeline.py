import os
import sys
import time
from datetime import datetime
from pathlib import Path
import pandas as pd

# Ensure project root is in sys.path when executed directly
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.logger import get_logger
from src.etl.loader import load_all_datasets
from src.etl.normaliser import normalize_ticker, normalize_year
from src.utils.helpers import normalize_dataframe
from src.etl.validator import ValidatorEngine
from src.db.connection import get_db_connection
from src.db.loader import create_tables, load_all_tables
from src.db.database_manager import verify_foreign_keys, get_row_counts

logger = get_logger(__name__)

# System Paths
DATA_DIR = "data/raw"
DB_PATH = "db/nifty100.db"
SCHEMA_PATH = "db/schema.sql"
AUDIT_PATH = "output/load_audit.csv"
VALIDATION_REPORT_PATH = "output/validation_failures.csv"

def run_pipeline() -> bool:
    """
    Executes the full End-to-End ETL Pipeline for Nifty100 Platform.
    
    Steps:
    1. Extract: Load 12 Excel files
    2. Transform: Normalize Tickers, Years, and Column headers
    3. Validate: Execute DQ rules; abort if CRITICAL issues occur
    4. Load: Apply schema & insert into SQLite within a transaction
    5. Audit & Verify: Check row counts & Foreign Keys
    """
    pipeline_start = time.time()
    logger.info("==================================================")
    logger.info("STARTING SPRINT 1 DAY 5 FULL ETL PIPELINE LOAD")
    logger.info("==================================================")
    
    # ----------------------------------------------------
    # STEP 1: EXTRACT
    # ----------------------------------------------------
    logger.info("Step 1: Extracting raw Excel datasets...")
    if not os.path.exists(DATA_DIR):
        logger.error(f"Data directory '{DATA_DIR}' not found!")
        return False

    raw_datasets = load_all_datasets(DATA_DIR)
    if not raw_datasets:
        logger.error("No datasets extracted. Aborting pipeline.")
        return False
        
    logger.info(f"Successfully extracted {len(raw_datasets)} raw datasets.")

    # ----------------------------------------------------
    # STEP 2: TRANSFORM / NORMALIZE
    # ----------------------------------------------------
    logger.info("Step 2: Normalizing extracted datasets...")
    normalized_datasets = {}
    
    for filename, df in raw_datasets.items():
        cleaned_df = normalize_dataframe(df)
        
        if 'ticker' in cleaned_df.columns:
            cleaned_df['ticker'] = cleaned_df['ticker'].apply(normalize_ticker)

        if 'year' in cleaned_df.columns:
            cleaned_df['year'] = cleaned_df['year'].apply(normalize_year)
            cleaned_df = cleaned_df.dropna(subset=['year'])
            
        if 'company_id' in cleaned_df.columns and 'year' in cleaned_df.columns:
            cleaned_df = cleaned_df.drop_duplicates(subset=['company_id', 'year'])
            
        normalized_datasets[filename] = cleaned_df
        logger.info(f"Normalized {filename} ({len(cleaned_df)} rows).")

    # ----------------------------------------------------
    # STEP 3: DATA QUALITY VALIDATION
    # ----------------------------------------------------
    logger.info("Step 3: Running Data Quality Engine...")
    validator = ValidatorEngine()
    is_valid = validator.run_all_validations(normalized_datasets)
    validator.save_report(VALIDATION_REPORT_PATH)

    if not is_valid:
        logger.error("Pipeline aborted due to CRITICAL Data Quality failures. Check validation report.")
        return False

    # ----------------------------------------------------
    # STEP 4: DATABASE INGESTION (LOAD)
    # ----------------------------------------------------
    logger.info("Step 4: Applying Schema & Ingesting into SQLite...")
    try:
        create_tables(DB_PATH, SCHEMA_PATH)
        load_all_tables(DB_PATH, normalized_datasets, AUDIT_PATH)
    except Exception as e:
        logger.error(f"Database loading failed and was rolled back! Error: {e}")
        return False

    # ----------------------------------------------------
    # STEP 5: POST-LOAD VERIFICATION & AUDIT
    # ----------------------------------------------------
    logger.info("Step 5: Performing Post-Load Integrity Checks...")
    fk_ok = verify_foreign_keys(DB_PATH)
    if not fk_ok:
        logger.error("CRITICAL: Foreign key check failed post-load!")
        return False

    tables_to_verify = [
        "sectors", "companies", "profitandloss", "balancesheet", 
        "cashflow", "analysis", "documents", "prosandcons", 
        "peer_groups", "stock_prices", "market_cap", "financial_ratios"
    ]
    row_counts = get_row_counts(DB_PATH, tables_to_verify)
    total_rows = sum(row_counts.values())

    pipeline_elapsed = round(time.time() - pipeline_start, 2)
    
    logger.info("==================================================")
    logger.info("ETL PIPELINE EXECUTION SUMMARY")
    logger.info("==================================================")
    logger.info("Pipeline Status     : SUCCESS")
    logger.info(f"Total Tables Loaded : {len(row_counts)}")
    logger.info(f"Total Rows Inserted : {total_rows}")
    logger.info(f"Execution Time      : {pipeline_elapsed} seconds")
    logger.info(f"Audit Trail Saved   : {AUDIT_PATH}")
    logger.info("==================================================")

    return True
