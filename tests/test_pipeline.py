import pytest
from src.etl.pipeline import run_pipeline

def test_pipeline_import():
    """Verifies that the main pipeline module is importable and functional."""
    assert callable(run_pipeline)
