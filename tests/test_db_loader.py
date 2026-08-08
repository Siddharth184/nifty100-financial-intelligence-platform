import pytest
import sqlite3
import pandas as pd
import os
from src.db.connection import get_db_connection
from src.db.loader import create_tables, load_all_tables

TEST_DB = "tests/test.db"
SCHEMA = "db/schema.sql"

@pytest.fixture(autouse=True)
def setup_teardown():
    # Setup
    if os.path.exists(TEST_DB): os.remove(TEST_DB)
    os.makedirs("db", exist_ok=True)
    # create minimal schema for testing if actual not available
    if not os.path.exists(SCHEMA):
        with open(SCHEMA, "w") as f:
            f.write("CREATE TABLE sectors (sector_id TEXT PRIMARY KEY);\n")
            f.write("CREATE TABLE companies (company_id TEXT PRIMARY KEY, sector_id TEXT, FOREIGN KEY(sector_id) REFERENCES sectors(sector_id));\n")
    yield
    # Teardown
    if os.path.exists(TEST_DB): os.remove(TEST_DB)

def test_database_connection():
    with get_db_connection(TEST_DB) as conn:
        assert isinstance(conn, sqlite3.Connection)

def test_table_creation():
    create_tables(TEST_DB, SCHEMA)
    with get_db_connection(TEST_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        assert 'sectors' in tables
        assert 'companies' in tables

def test_foreign_key_violation_rollback():
    create_tables(TEST_DB, SCHEMA)
    
    # Intentionally bad data: loading company without creating sector first
    bad_data = {
        "companies.xlsx": pd.DataFrame({"company_id": ["TCS"], "sector_id": ["IT"]})
    }
    
    with pytest.raises(RuntimeError):
        # This will trigger a rollback because PRAGMA foreign_keys = ON
        load_all_tables(TEST_DB, bad_data, "tests/audit.csv")
        
    # Verify rollback worked (table should be empty)
    with get_db_connection(TEST_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM companies")
        assert cursor.fetchone()[0] == 0
