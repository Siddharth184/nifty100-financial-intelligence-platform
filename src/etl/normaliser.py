import pandas as pd
import re
from typing import Optional, Union

def normalize_ticker(ticker: Union[str, float, None]) -> Optional[str]:
    """
    Normalizes a ticker symbol by stripping whitespace and converting to uppercase.
    Handles None, NaN, empty strings, and mixed case.
    """
    if pd.isna(ticker) or ticker is None:
        return None
        
    if not isinstance(ticker, str):
        ticker = str(ticker)
        
    cleaned = ticker.strip().upper()
    return cleaned if cleaned else None

def normalize_year(year_val: Union[str, int, float, None]) -> Optional[int]:
    """
    Normalizes various year formats into a standardized 4-digit integer year representing the financial year end.
    Supported formats: "FY2024", "FY 2024", "FY24", "2024", 2024, 2024.0, "2024.0", "2023-24", "2019-20", "Mar-24", "Dec-23", "Mar 2024"
    """
    if pd.isna(year_val) or year_val is None:
        return None
        
    if isinstance(year_val, float):
        if pd.isna(year_val):
            return None
        year_val = int(year_val)
        
    year_str = str(year_val).strip().upper()
    
    if not year_str or year_str in ("NONE", "NAN", "TTM"):
        return None
        
    # Strip trailing .0 if present (e.g., "2024.0" -> "2024")
    year_str = re.sub(r'\.0$', '', year_str)
    
    # Pattern 1: YYYY-YY (e.g., 2023-24 -> 2024, 2019-20 -> 2020)
    match = re.search(r'^(\d{2})(\d{2})-(\d{2})$', year_str)
    if match:
        century = match.group(1)
        end_year = match.group(3)
        # If it transitions across a century (e.g., 1999-00 -> 2000)
        if match.group(2) == '99' and end_year == '00':
            century = str(int(century) + 1)
        return int(f"{century}{end_year}")
        
    # Pattern 2: YYYY-YYYY (e.g., 2023-2024 -> 2024)
    match = re.search(r'^(\d{4})-(\d{4})$', year_str)
    if match:
        return int(match.group(2))

    # Pattern 3: Month-YY or Month YYYY (e.g., MAR-24 -> 2024, MAR 2024 -> 2024)
    match = re.search(r'^(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[\s\-](\d{2}|\d{4})$', year_str)
    if match:
        year_part = match.group(2)
        if len(year_part) == 2:
            return 2000 + int(year_part)
        return int(year_part)
        
    # Pattern 4: FY YYYY, FYYYYY, FY YY, FYYY (e.g., FY 2024, FY24)
    match = re.search(r'^FY\s*(\d{2}|\d{4})$', year_str)
    if match:
        year_part = match.group(1)
        if len(year_part) == 2:
            return 2000 + int(year_part)
        return int(year_part)
        
    # Pattern 5: Just 4 digits (e.g., 2024)
    match = re.search(r'^(\d{4})$', year_str)
    if match:
        return int(match.group(1))
        
    return None
