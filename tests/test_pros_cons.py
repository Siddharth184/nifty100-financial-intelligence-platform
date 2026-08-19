"""
Unit tests for Day 30 Auto Pros/Cons Generator.
"""

import pytest
import os
import pandas as pd
from src.nlp.pros_cons_generator import generate_pros_cons_report

class TestProsConsGenerator:
    def test_pros_cons_generation(self):
        df_rules = generate_pros_cons_report()
        assert not df_rules.empty
        assert "company_id" in df_rules.columns
        assert "type" in df_rules.columns
        assert "rule_id" in df_rules.columns
        assert "text" in df_rules.columns
        assert "confidence_pct" in df_rules.columns
        
        # Verify confidence filtering > 60%
        assert (df_rules["confidence_pct"] > 60).all()
        
        # Verify both pros and cons are generated
        types = df_rules["type"].unique()
        assert "pro" in types
        assert "con" in types
