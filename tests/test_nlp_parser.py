"""
Unit tests for Day 29 NLP Analysis Text Parser.
"""

import pytest
import os
import pandas as pd
from src.nlp.parser import parse_text_entry, load_analysis_dataframe, run_analysis_parser

class TestNLPParser:
    def test_parse_text_entry_standard(self):
        text = "10 Years: 21%\n5 Years: 15.5%\n3 Years: 18%"
        results = parse_text_entry(text)
        assert len(results) == 3
        assert results[0] == (10, 21.0)
        assert results[1] == (5, 15.5)
        assert results[2] == (3, 18.0)

    def test_parse_text_entry_spaces(self):
        text = "10    Years:     23%    10 Years:          9%        10 Years:      -9%"
        results = parse_text_entry(text)
        assert len(results) == 3
        assert results[0] == (10, 23.0)
        assert results[1] == (10, 9.0)
        assert results[2] == (10, -9.0)

    def test_parse_text_entry_single(self):
        text = "5 Years: 12%"
        results = parse_text_entry(text)
        assert len(results) == 1
        assert results[0] == (5, 12.0)

    def test_parse_text_entry_negative_cagr(self):
        text = "3 Years: -4.5%"
        results = parse_text_entry(text)
        assert len(results) == 1
        assert results[0] == (3, -4.5)

    def test_load_analysis_dataframe(self):
        df = load_analysis_dataframe("data/raw/analysis.xlsx")
        assert not df.empty
        assert "company_id" in df.columns or "company" in df.columns or "id" in df.columns

    def test_run_analysis_parser(self):
        p_df, f_df, d_df = run_analysis_parser()
        assert not p_df.empty
        assert "company_id" in p_df.columns
        assert "metric_type" in p_df.columns
        assert "period_years" in p_df.columns
        assert "value_pct" in p_df.columns
