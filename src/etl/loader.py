import pandas as pd
import os
import sys
from pathlib import Path

# Ensure project root is in sys.path when executed directly
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.logger import get_logger

logger = get_logger(__name__)

CORE_DATASETS = {
    "companies.xlsx", "profitandloss.xlsx", "balancesheet.xlsx",
    "cashflow.xlsx", "analysis.xlsx", "documents.xlsx", "prosandcons.xlsx"
}

SUPPORTING_DATASETS = {
    "sectors.xlsx", "stock_prices.xlsx", "market_cap.xlsx",
    "financial_ratios.xlsx", "peer_groups.xlsx"
}

def get_dataset_type(filename: str) -> str:
    """Identifies if a dataset is core, supporting, or unknown."""
    if filename in CORE_DATASETS:
        return "core"
    elif filename in SUPPORTING_DATASETS:
        return "supporting"
    return "unknown"

def validate_file_exists(filepath: str) -> bool:
    """Checks if a file exists at the given path."""
    if not os.path.exists(filepath):
        logger.error(f"File not found: {filepath}")
        return False
    return True

def load_excel(filepath: str) -> pd.DataFrame:
    """Loads an Excel file into a pandas DataFrame based on its dataset type."""
    filename = os.path.basename(filepath)
    
    if not validate_file_exists(filepath):
        raise FileNotFoundError(f"Missing file: {filepath}")
    
    dataset_type = get_dataset_type(filename)
    logger.info(f"Loading {filename} (Type: {dataset_type})")
    
    try:
        # Core datasets use header=1, Supporting use header=0
        header_row = 1 if dataset_type == "core" else 0
        
        if dataset_type == "unknown":
            logger.warning(f"Unknown dataset type for {filename}. Defaulting to header=0.")
            
        df = pd.read_excel(filepath, header=header_row)
            
        if df.empty:
            logger.warning(f"The loaded DataFrame for {filename} is completely empty.")
            
        logger.info(f"Successfully loaded {len(df)} rows from {filename}.")
        return df
        
    except Exception as e:
        logger.error(f"Failed to load {filename}: {str(e)}")
        raise

def load_all_datasets(data_dir: str) -> dict[str, pd.DataFrame]:
    """Loads all core and supporting datasets from the given directory."""
    datasets = {}
    all_files = list(CORE_DATASETS) + list(SUPPORTING_DATASETS)
    
    for filename in all_files:
        filepath = os.path.join(data_dir, filename)
        try:
            datasets[filename] = load_excel(filepath)
        except Exception as e:
            logger.error(f"Skipping {filename} due to error: {str(e)}")
            
    return datasets


def main():
    data_dir = "data/raw"

    logger.info("Starting dataset loading...")

    datasets = load_all_datasets(data_dir)

    logger.info(f"Successfully loaded {len(datasets)} datasets.")

    for name, df in datasets.items():
        print(f"{name} -> {df.shape}")


if __name__ == "__main__":
    main()