import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from src.dashboard.utils.db import (
    get_companies, get_ratios, get_ratios_all, get_pl, get_bs, get_cf,
    get_sectors, get_peers, get_peer_group_names, get_proscons, get_documents, get_available_years
)
from src.screener.engine import ScreenerEngine

print("--- Testing Dashboard Database Queries ---")
companies = get_companies()
print(f"1. get_companies(): {len(companies)} rows")

years = get_available_years()
print(f"2. get_available_years(): {years}")

ratios_2024 = get_ratios_all(2024)
print(f"3. get_ratios_all(2024): {len(ratios_2024)} rows")

ratios_tatasteel = get_ratios("TATASTEEL")
print(f"4. get_ratios('TATASTEEL'): {len(ratios_tatasteel)} rows")

pl_tatasteel = get_pl("TATASTEEL")
print(f"5. get_pl('TATASTEEL'): {len(pl_tatasteel)} rows")

sectors = get_sectors()
print(f"6. get_sectors(): {len(sectors)} rows")

peer_groups = get_peer_group_names()
print(f"7. get_peer_group_names(): {len(peer_groups)} groups -> {peer_groups}")

peers_auto = get_peers("Automobile") if peer_groups else pd.DataFrame()
print(f"8. get_peers('Automobile'): {len(peers_auto)} rows")

pc_tatasteel = get_proscons("TATASTEEL")
print(f"9. get_proscons('TATASTEEL'): {len(pc_tatasteel)} rows")

docs_tatasteel = get_documents("TATASTEEL")
print(f"10. get_documents('TATASTEEL'): {len(docs_tatasteel)} rows")

print("\n--- Testing Capital Allocation Data ---")
print(f"capital_allocation_strategy non-null: {ratios_2024['capital_allocation_strategy'].notna().sum() if 'capital_allocation_strategy' in ratios_2024.columns else 'MISSING'}")

print("\n--- Testing Screener Data ---")
engine = ScreenerEngine()
univ = engine.load_universe_data()
print(f"screener universe: {len(univ)} rows")
filt_res = engine.apply_filters(univ, {"roe_min": 15.0})
print(f"screener roe_min=15 filter: {len(filt_res)} rows")

print("\nAll DB & Screener data queries passed!")
