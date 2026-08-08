import sys
from src.etl.pipeline import run_pipeline

if __name__ == "__main__":
    success = run_pipeline()
    if not success:
        print("\n[ERROR] Pipeline failed. Check logs for details.")
        sys.exit(1)
    print("\n[SUCCESS] Pipeline executed cleanly!")