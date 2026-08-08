# ==============================================================================
# Nifty100 Financial Intelligence Platform - Makefile
# Cross-platform task automation helper
# ==============================================================================

.PHONY: help install test load dashboard clean lint format

help:
	@echo "Available commands:"
	@echo "  make install    - Install required Python dependencies"
	@echo "  make test       - Run unit and integration tests using pytest"
	@echo "  make load       - Execute the ETL data pipeline"
	@echo "  make dashboard  - Launch the Streamlit analytics dashboard"
	@echo "  make lint       - Check code formatting and linting errors with ruff"
	@echo "  make format     - Automatically format Python code using black"
	@echo "  make clean      - Clean cache, bytecode, and log files"

install:
	pip install -r requirements.txt

test:
	pytest tests/ --verbose

load:
	python main.py

dashboard:
	streamlit run src/dashboard/app.py

lint:
	ruff check src/ tests/

format:
	black src/ tests/

clean:
	python -c "import shutil, os, glob; [shutil.rmtree(p, ignore_errors=True) for p in glob.glob('**/__pycache__', recursive=True)]; [shutil.rmtree(p, ignore_errors=True) for p in glob.glob('.pytest_cache')]; [shutil.rmtree(p, ignore_errors=True) for p in glob.glob('.ruff_cache')]"
