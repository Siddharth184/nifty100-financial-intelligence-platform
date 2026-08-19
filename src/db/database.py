"""
Database initialization and management entry point for Nifty100 Platform.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.logger import get_logger
from src.db.connection import get_db_connection
from src.db.loader import create_tables, LOAD_ORDER


logger = get_logger(__name__)

DB_PATH = "db/nifty100.db"
SCHEMA_PATH = "db/schema.sql"

def init_database(db_path: str = DB_PATH, schema_path: str = SCHEMA_PATH) -> bool:
    """Creates database file, applies DDL schema, and verifies foreign key pragma."""
    logger.info(f"Initializing database at: {db_path}")
    create_tables(db_path, schema_path)
    
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        fk_status = cursor.execute("PRAGMA foreign_keys;").fetchone()[0]
        tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
        table_names = [t[0] for t in tables if t[0] != 'sqlite_sequence']

    logger.info(f"PRAGMA foreign_keys status: {fk_status}")
    logger.info(f"Total tables created: {len(table_names)} ({', '.join(table_names)})")
    
    if fk_status == 1 and len(table_names) >= len(LOAD_ORDER):
        print("\n[SUCCESS] Database initialized cleanly with PRAGMA foreign_keys=ON!")
        return True
    else:
        logger.error("Database initialization failed PRAGMA or table check!")
        return False

def main():
    init_database()

if __name__ == "__main__":
    main()
