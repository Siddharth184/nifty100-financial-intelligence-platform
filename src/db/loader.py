import pandas as pd
import time
import os
from datetime import datetime
from typing import Dict
from src.utils.logger import get_logger
from src.db.connection import get_db_connection

logger = get_logger(__name__)

# Load order is critical to prevent Foreign Key constraint violations
LOAD_ORDER = [
    "sectors", "companies", "profitandloss", "balancesheet", 
    "cashflow", "analysis", "documents", "prosandcons", 
    "peer_groups", "stock_prices", "market_cap", "financial_ratios"
]

def create_tables(db_path: str, schema_path: str):
    """Reads schema.sql and executes it to create tables."""
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found at {schema_path}")
        
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
        
    with get_db_connection(db_path) as conn:
        try:
            conn.execute("PRAGMA foreign_keys = OFF;")
            cursor = conn.cursor()
            existing_tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
            for t in existing_tables:
                if t[0] != 'sqlite_sequence':
                    cursor.execute(f"DROP TABLE IF EXISTS {t[0]};")
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.executescript(schema_sql)
            conn.commit()
            logger.info("Database schema applied successfully.")
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to apply schema: {e}")
            raise

def transform_df_for_schema(table_name: str, df: pd.DataFrame, datasets: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Transforms raw/normalized DataFrame columns to align with SQLite schema DDL."""
    df = df.copy()
    if table_name == "sectors":
        if "broad_sector" in df.columns:
            uniq_sectors = df["broad_sector"].dropna().unique()
            return pd.DataFrame({"sector_id": uniq_sectors, "sector_name": uniq_sectors})
        return df[["sector_id", "sector_name"]]
        
    elif table_name == "companies":
        sec_df = datasets.get("sectors.xlsx", pd.DataFrame())
        sector_map = dict(zip(sec_df["company_id"], sec_df["broad_sector"])) if "broad_sector" in sec_df.columns else {}
        comp_id_col = "id" if "id" in df.columns else "company_id"
        return pd.DataFrame({
            "company_id": df[comp_id_col],
            "company_name": df["company_name"],
            "ticker": df[comp_id_col],
            "sector_id": df[comp_id_col].map(sector_map)
        })
        
    elif table_name == "profitandloss":
        res = df[["company_id", "year", "sales", "operating_profit", "net_profit", "eps"]].copy()
        return res.drop_duplicates(subset=["company_id", "year"])

    elif table_name == "balancesheet":
        res = pd.DataFrame()
        res["company_id"] = df["company_id"]
        res["year"] = df["year"]
        res["total_assets"] = df["total_assets"]
        res["total_liabilities"] = df["total_liabilities"]
        if "total_equity" in df.columns:
            res["total_equity"] = df["total_equity"]
        else:
            eq = df.get("equity_capital", 0).fillna(0) if hasattr(df.get("equity_capital"), "fillna") else 0
            res_v = df.get("reserves", 0).fillna(0) if hasattr(df.get("reserves"), "fillna") else 0
            res["total_equity"] = eq + res_v
        return res.drop_duplicates(subset=["company_id", "year"])

    elif table_name == "cashflow":
        res = pd.DataFrame({
            "company_id": df["company_id"],
            "year": df["year"],
            "operating_cash_flow": df["operating_activity"],
            "investing_cash_flow": df["investing_activity"],
            "financing_cash_flow": df["financing_activity"],
            "net_cash_flow": df["net_cash_flow"]
        })
        return res.drop_duplicates(subset=["company_id", "year"])

    elif table_name == "analysis":
        res = pd.DataFrame({
            "company_id": df["company_id"],
            "year": df.groupby("company_id").cumcount() + 1,
            "revenue_growth": None,
            "profit_margin": None
        })
        return res.drop_duplicates(subset=["company_id", "year"])

    elif table_name == "documents":
        id_col = "id" if "id" in df.columns else "doc_id"
        url_col = "annual_report" if "annual_report" in df.columns else "doc_url"
        res = pd.DataFrame({
            "doc_id": df[id_col].astype(str),
            "company_id": df["company_id"],
            "year": df["year"],
            "doc_url": df[url_col]
        })
        return res

    elif table_name == "prosandcons":
        id_col = "id" if "id" in df.columns else "pc_id"
        res = pd.DataFrame({
            "pc_id": df[id_col].astype(str),
            "company_id": df["company_id"],
            "year": df["year"] if "year" in df.columns else 2024,
            "pros": df["pros"],
            "cons": df["cons"]
        })
        return res

    elif table_name == "peer_groups":
        id_col = "id" if "id" in df.columns else "group_id"
        res = pd.DataFrame({
            "group_id": df[id_col].astype(str),
            "company_id": df["company_id"],
            "peer_company_id": df.get("peer_company_id", df["company_id"])
        })
        return res

    elif table_name == "stock_prices":
        res = pd.DataFrame({
            "company_id": df["company_id"],
            "date": df["date"].astype(str),
            "close_price": df["close_price"],
            "volume": df["volume"]
        })
        return res.drop_duplicates(subset=["company_id", "date"])

    elif table_name == "market_cap":
        date_col = "date" if "date" in df.columns else "year"
        cap_col = "market_cap" if "market_cap" in df.columns else "market_cap_crore"
        res = pd.DataFrame({
            "company_id": df["company_id"],
            "date": df[date_col].astype(str),
            "market_cap": df[cap_col]
        })
        return res.drop_duplicates(subset=["company_id", "date"])

    elif table_name == "financial_ratios":
        mc_raw = datasets.get("market_cap.xlsx", pd.DataFrame())
        mc_pe_map = dict(zip(zip(mc_raw["company_id"], mc_raw["year"]), mc_raw.get("pe_ratio"))) if "market_cap_crore" in mc_raw.columns else {}
        mc_pb_map = dict(zip(zip(mc_raw["company_id"], mc_raw["year"]), mc_raw.get("pb_ratio"))) if "market_cap_crore" in mc_raw.columns else {}
        pairs = list(zip(df["company_id"], df["year"]))
        res = pd.DataFrame({
            "company_id": df["company_id"],
            "year": df["year"],
            "pe_ratio": [mc_pe_map.get(p) for p in pairs],
            "pb_ratio": [mc_pb_map.get(p) for p in pairs],
            "debt_to_equity": df["debt_to_equity"]
        })
        return res.drop_duplicates(subset=["company_id", "year"])

    return df

def load_all_tables(db_path: str, datasets: Dict[str, pd.DataFrame], audit_path: str):
    """Loads datasets into SQLite using a secure transaction. Rollbacks on failure."""
    audit_records = []
    
    with get_db_connection(db_path) as conn:
        valid_companies = set()
        for table_name in LOAD_ORDER:
            filename = f"{table_name}.xlsx"
            if filename not in datasets:
                continue
                
            raw_df = datasets[filename]
            start_time = time.time()
            
            try:
                table_df = transform_df_for_schema(table_name, raw_df, datasets)
                if table_name == "companies":
                    valid_companies = set(table_df["company_id"])
                elif table_name != "sectors" and "company_id" in table_df.columns and valid_companies:
                    table_df = table_df[table_df["company_id"].isin(valid_companies)]

                # pandas to_sql uses the existing connection transaction
                table_df.to_sql(name=table_name, con=conn, if_exists='append', index=False)
                
                execution_time = time.time() - start_time
                rows_read = len(raw_df)
                rows_inserted = len(table_df)
                rows_rejected = max(0, rows_read - rows_inserted)

                audit_records.append({
                    "timestamp": datetime.now().isoformat(),
                    "table_name": table_name,
                    "rows_read": rows_read,
                    "rows_inserted": rows_inserted,
                    "rows_rejected": rows_rejected,
                    "status": "SUCCESS",
                    "error_message": "",
                    "execution_time_sec": round(execution_time, 4)
                })
                logger.info(f"Loaded {rows_inserted} rows into {table_name} (Read: {rows_read}, Rejected: {rows_rejected})")
                
            except Exception as e:
                conn.rollback()
                logger.error(f"Failed to load {table_name}. Rolling back transaction! Error: {e}")
                
                rows_read = len(raw_df)
                audit_records.append({
                    "timestamp": datetime.now().isoformat(),
                    "table_name": table_name,
                    "rows_read": rows_read,
                    "rows_inserted": 0,
                    "rows_rejected": rows_read,
                    "status": "FAILED",
                    "error_message": str(e),
                    "execution_time_sec": round(time.time() - start_time, 4)
                })
                
                os.makedirs(os.path.dirname(audit_path), exist_ok=True)
                pd.DataFrame(audit_records).to_csv(audit_path, index=False)
                raise RuntimeError(f"Database load aborted due to failure in {table_name}")
                
        conn.commit()
        logger.info("All tables committed to database successfully.")
        
    os.makedirs(os.path.dirname(audit_path), exist_ok=True)
    pd.DataFrame(audit_records).to_csv(audit_path, index=False)
    logger.info(f"Load audit saved to {audit_path}")

