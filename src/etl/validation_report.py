from dataclasses import dataclass, asdict
from typing import Any, List, Optional
import pandas as pd
import time
import os
from src.utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class ValidationFailure:
    timestamp: str
    rule_id: str
    severity: str
    dataset: str
    company_id: Optional[str]
    year: Optional[int]
    column: Optional[str]
    actual_value: Any
    expected_value: Any
    failure_description: str
    suggested_fix: str

class ValidationReport:
    """Manages the collection and reporting of DQ failures."""
    
    def __init__(self):
        self.failures: List[ValidationFailure] = []
        self.start_time = time.time()
        self.rules_executed = 0
        self.rules_passed = 0
        self.rules_failed = 0
        self.critical_count = 0
        self.warning_count = 0

    def add_failures(self, rule_id: str, new_failures: List[ValidationFailure]):
        """Adds failures and updates counters."""
        self.rules_executed += 1
        if not new_failures:
            self.rules_passed += 1
            logger.info(f"PASS {rule_id}")
            return
            
        self.rules_failed += 1
        self.failures.extend(new_failures)
        
        for f in new_failures:
            if f.severity == "CRITICAL":
                self.critical_count += 1
            elif f.severity == "WARNING":
                self.warning_count += 1
                
        logger.warning(f"FAIL {rule_id}: {len(new_failures)} anomalies detected.")

    def save_to_csv(self, filepath: str):
        """Saves the audit trail to a CSV file."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        if not self.failures:
            logger.info("No validation failures to save. Data is 100% clean!")
            # Creating empty file with headers for consistency
            pd.DataFrame(columns=[f.name for f in ValidationFailure.__dataclass_fields__.values()]).to_csv(filepath, index=False)
            return
            
        df = pd.DataFrame([asdict(f) for f in self.failures])
        df.to_csv(filepath, index=False)
        logger.info(f"Validation report saved to {filepath}")

    def get_summary(self):
        """Prints a professional summary to the console."""
        execution_time = round(time.time() - self.start_time, 2)
        success_rate = 0
        if self.rules_executed > 0:
            success_rate = round((self.rules_passed / self.rules_executed) * 100, 2)
            
        summary = f"""
=========================================
       DATA QUALITY VALIDATION SUMMARY    
=========================================
Total Rules Executed : {self.rules_executed}
Passed               : {self.rules_passed}
Failed               : {self.rules_failed}
-----------------------------------------
CRITICAL Failures    : {self.critical_count}
WARNING Failures     : {self.warning_count}
-----------------------------------------
Execution Time       : {execution_time} seconds
Success Rate         : {success_rate}%
=========================================
"""
        print(summary)
        return summary
