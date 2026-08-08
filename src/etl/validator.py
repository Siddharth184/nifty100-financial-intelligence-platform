import pandas as pd
import sys
from pathlib import Path
from typing import Dict, List, Callable

# Ensure project root is in sys.path when executed directly
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.logger import get_logger
from src.etl.validation_report import ValidationReport, ValidationFailure
from src.etl import dq_rules

logger = get_logger(__name__)

class ValidatorEngine:
    def __init__(self):
        self.report = ValidationReport()

    def run_validation(self, rule_id: str, rule_func: Callable, df: pd.DataFrame, dataset_name: str, **kwargs):
        """Safely executes a single validation rule."""
        try:
            logger.info(f"Running {rule_id} on {dataset_name}")
            failures = rule_func(df, dataset_name, **kwargs)
            self.report.add_failures(rule_id, failures)
        except Exception as e:
            logger.error(f"Rule {rule_id} crashed on {dataset_name}: {str(e)}")
            self.report.add_failures(rule_id, [ValidationFailure(
                timestamp=dq_rules.current_time(), rule_id=f"{rule_id}_CRASH", severity="CRITICAL",
                dataset=dataset_name, company_id=None, year=None, column=None,
                actual_value="ERROR", expected_value="SUCCESS",
                failure_description=f"Rule crashed: {str(e)}", suggested_fix="Debug Python rule logic"
            )])

    def run_all_validations(self, datasets: Dict[str, pd.DataFrame]) -> bool:
        """Runs the entire suite of Data Quality rules across all provided datasets."""
        
        # Base validations for all datasets
        for name, df in datasets.items():
            self.run_validation("DQ-12", dq_rules.dq_12_mandatory_columns, df, name, expected_cols=['company_id'] if name != 'companies.xlsx' else [])
            if name != 'companies.xlsx':
                self.run_validation("DQ-15", dq_rules.dq_15_missing_company_ref, df, name)

        if 'companies.xlsx' in datasets:
            df = datasets['companies.xlsx']
            self.run_validation("DQ-01", dq_rules.dq_01_primary_key, df, "companies.xlsx", pk_col="company_id")
            self.run_validation("DQ-11", dq_rules.dq_11_valid_url, df, "companies.xlsx")
            self.run_validation("DQ-13", dq_rules.dq_13_duplicate_ticker, df, "companies.xlsx")
            
        if 'profitandloss.xlsx' in datasets:
            df = datasets['profitandloss.xlsx']
            self.run_validation("DQ-02", dq_rules.dq_02_composite_key, df, "profitandloss.xlsx", cols=["company_id", "year"])
            self.run_validation("DQ-05", dq_rules.dq_05_opm_crosscheck, df, "profitandloss.xlsx")
            self.run_validation("DQ-06", dq_rules.dq_06_positive_sales, df, "profitandloss.xlsx")
            self.run_validation("DQ-08", dq_rules.dq_08_tax_rate, df, "profitandloss.xlsx")
            self.run_validation("DQ-09", dq_rules.dq_09_dividend_payout, df, "profitandloss.xlsx")
            self.run_validation("DQ-10", dq_rules.dq_10_eps_sign, df, "profitandloss.xlsx")
            self.run_validation("DQ-14", dq_rules.dq_14_fy_consistency, df, "profitandloss.xlsx")
            self.run_validation("DQ-16", dq_rules.dq_16_coverage, df, "profitandloss.xlsx", col="sales", threshold=0.1)
            
        if 'balancesheet.xlsx' in datasets:
            df = datasets['balancesheet.xlsx']
            self.run_validation("DQ-04", dq_rules.dq_04_balance_sheet, df, "balancesheet.xlsx")

        if 'cashflow.xlsx' in datasets:
            df = datasets['cashflow.xlsx']
            self.run_validation("DQ-07", dq_rules.dq_07_net_cash, df, "cashflow.xlsx")
            
        # Foreign Key Integrity (requires both parent and child)
        if 'profitandloss.xlsx' in datasets and 'companies.xlsx' in datasets:
            self.run_validation("DQ-03", dq_rules.dq_03_foreign_key, datasets['profitandloss.xlsx'], "profitandloss.xlsx", fk_col="company_id", parent_df=datasets['companies.xlsx'], pk_col="company_id")

        self.report.get_summary()
        
        if self.report.critical_count > 0:
            logger.error("Validation aborted: CRITICAL data quality failures detected.")
            return False
            
        logger.info("Validation successful. Data is clean.")
        return True

    def save_report(self, filepath: str):
        self.report.save_to_csv(filepath)

def main():
    from src.etl.loader import load_all_datasets
    from src.etl.normaliser import normalize_ticker, normalize_year
    from src.utils.helpers import normalize_dataframe

    data_dir = "data/raw"
    logger.info("Loading raw datasets for validation...")
    raw_datasets = load_all_datasets(data_dir)
    
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

    validator = ValidatorEngine()
    validator.run_all_validations(normalized_datasets)
    output_path = "output/validation_failures.csv"
    validator.save_report(output_path)
    logger.info(f"Validation report generated at: {output_path}")

if __name__ == "__main__":
    main()
