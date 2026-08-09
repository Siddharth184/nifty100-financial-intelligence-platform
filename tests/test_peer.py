"""
Unit tests for Peer Percentile Engine (Sprint 3 Day 18).
"""

import pytest
import pandas as pd

from src.analytics.peer import calculate_percent_rank, compute_peer_percentiles

class TestPeerEngine:
    def test_percent_rank_standard(self):
        s = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0])
        ranks = calculate_percent_rank(s, invert=False)
        assert round(ranks.iloc[0], 2) == 0.2
        assert round(ranks.iloc[4], 2) == 1.0

    def test_percent_rank_inverted_de(self):
        # Inverted D/E: lower D/E gets HIGHER percentile rank
        de_series = pd.Series([0.1, 0.5, 1.5, 2.5])
        ranks = calculate_percent_rank(de_series, invert=True)
        # Lowest D/E (0.1) should get highest rank
        assert ranks.iloc[0] > ranks.iloc[3]

    def test_peer_percentiles_execution(self):
        records = compute_peer_percentiles()
        assert not records.empty
        assert "percentile_rank" in records.columns
        assert "peer_group_name" in records.columns
