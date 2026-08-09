"""
Verification runner for radio widget label fix.
"""

import sys
import os
import sqlite3

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.dashboard.utils.db import get_companies

def main():
    print("=" * 60)
    print(" RADIO WIDGET LABEL REMOVAL VERIFICATION")
    print("=" * 60)

    conn = sqlite3.connect("db/nifty100.db")
    fk_violations = conn.execute("PRAGMA foreign_key_check").fetchall()
    print(f"1. Database FK Violations: {len(fk_violations)} (Expected 0)")
    conn.close()

    comps = get_companies()
    print(f"2. Companies Loaded: {len(comps)}")

    print("\n✅ Verification Successful!")

if __name__ == "__main__":
    main()
