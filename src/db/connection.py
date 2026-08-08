import sqlite3
import os
from contextlib import contextmanager
from src.utils.logger import get_logger

logger = get_logger(__name__)

@contextmanager
def get_db_connection(db_path: str):
    """
    Context manager for SQLite connection.
    Yields a connection and safely closes it afterward.
    Enforces PRAGMA foreign_keys = ON.
    """
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = None
    try:
        conn = sqlite3.connect(db_path, timeout=10.0)
        conn.execute("PRAGMA foreign_keys = ON;")
        yield conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        if conn:
            conn.close()

def execute_query(db_path: str, query: str, params: tuple = ()) -> list:
    """Executes a single read query and returns results."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()
