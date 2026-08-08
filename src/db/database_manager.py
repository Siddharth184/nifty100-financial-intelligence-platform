from src.db.connection import execute_query
from src.utils.logger import get_logger

logger = get_logger(__name__)

def verify_foreign_keys(db_path: str) -> bool:
    """Uses SQLite's built-in pragma to check for orphaned records."""
    violations = execute_query(db_path, "PRAGMA foreign_key_check;")
    if violations:
        logger.error(f"CRITICAL: Foreign Key Violations detected: {violations}")
        return False
    logger.info("Foreign key integrity verified.")
    return True

def get_row_counts(db_path: str, tables: list) -> dict:
    """Verifies data was actually inserted by counting rows."""
    counts = {}
    for table in tables:
        try:
            result = execute_query(db_path, f"SELECT COUNT(*) FROM {table}")
            counts[table] = result[0][0]
        except Exception as e:
            logger.warning(f"Could not count rows for {table}: {e}")
            counts[table] = 0
    return counts
