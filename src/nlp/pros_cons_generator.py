"""
Auto Pros/Cons Generator — Sprint 5 Day 30.

Evaluates 12 Pro rules and 12 Con rules for all companies in nifty100.db.
Assigns confidence scores (0-100%) and includes rules with confidence_pct > 60%.
Respects dividend data limitation (Dividend Yield and Payout unavailable in raw exports).
Generates output/pros_cons_generated.csv.
"""

import os
import sqlite3
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any

from src.utils.logger import get_logger
from src.db.connection import get_db_connection

logger = get_logger(__name__)

DB_PATH = "db/nifty100.db"
OUTPUT_PROS_CONS_CSV = "output/pros_cons_generated.csv"


def load_company_financial_histories(db_path: str = DB_PATH) -> Dict[str, Dict[str, Any]]:
    """
    Loads multi-year financial ratio histories and company profiles from SQLite.
    Returns a dict mapping company_id -> company data dict.
    """
    if not os.path.exists(db_path):
        logger.error(f"Database not found at {db_path}")
        return {}

    with get_db_connection(db_path) as conn:
        comp_df = pd.read_sql_query("""
            SELECT c.company_id, c.company_name, c.ticker, s.sector_name
            FROM companies c
            LEFT JOIN sectors s ON c.sector_id = s.sector_id
        """, conn)

        ratios_df = pd.read_sql_query("""
            SELECT fr.*,
                   pnl.sales, pnl.operating_profit, pnl.net_profit, pnl.eps,
                   bs.total_assets, bs.total_equity,
                   cf.operating_cash_flow, cf.investing_cash_flow, cf.financing_cash_flow
            FROM financial_ratios fr
            LEFT JOIN profitandloss pnl ON fr.company_id = pnl.company_id AND fr.year = pnl.year
            LEFT JOIN balancesheet bs ON fr.company_id = bs.company_id AND fr.year = bs.year
            LEFT JOIN cashflow cf ON fr.company_id = cf.company_id AND fr.year = cf.year
            ORDER BY fr.company_id, fr.year ASC
        """, conn)

    company_map = {}
    for _, c_row in comp_df.iterrows():
        cid = c_row["company_id"]
        c_ratios = ratios_df[ratios_df["company_id"] == cid].sort_values("year")
        company_map[cid] = {
            "profile": c_row.to_dict(),
            "history": c_ratios
        }

    return company_map


def evaluate_pros_and_cons(company_map: Dict[str, Dict[str, Any]]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Evaluates 12 Pro rules and 12 Con rules across all companies.
    """
    all_rules = []
    coverage_status = {}

    for cid, c_data in company_map.items():
        profile = c_data["profile"]
        df_hist = c_data["history"]

        if df_hist.empty:
            logger.warning(f"No ratio history for company {cid}")
            continue

        latest = df_hist.iloc[-1]
        years_cnt = len(df_hist)

        # Helper series access
        roe_series = df_hist["return_on_equity_pct"].dropna() if "return_on_equity_pct" in df_hist.columns and df_hist["return_on_equity_pct"].notna().any() else df_hist["roe"].dropna()
        fcf_series = df_hist["free_cash_flow_cr"].dropna() if "free_cash_flow_cr" in df_hist.columns and df_hist["free_cash_flow_cr"].notna().any() else df_hist["free_cash_flow"].dropna()
        de_series = df_hist["debt_to_equity"].dropna()
        opm_series = df_hist["operating_profit_margin_pct"].dropna() if "operating_profit_margin_pct" in df_hist.columns and df_hist["operating_profit_margin_pct"].notna().any() else df_hist["opm"].dropna()
        sales_series = df_hist["sales"].dropna()
        eps_series = df_hist["eps"].dropna()
        net_profit_series = df_hist["net_profit"].dropna()
        roce_series = df_hist["roce"].dropna()
        assets_series = df_hist["total_assets"].dropna() if "total_assets" in df_hist.columns else pd.Series()
        debt_series = df_hist["total_debt_cr"].dropna() if "total_debt_cr" in df_hist.columns and df_hist["total_debt_cr"].notna().any() else df_hist["net_debt"].dropna()

        # Metrics from latest year
        is_financial = bool(latest.get("is_financial_sector", 0)) or ("Bank" in str(profile.get("sector_name", "")) or "Financial" in str(profile.get("sector_name", "")))
        latest_roe = roe_series.iloc[-1] if not roe_series.empty else None
        latest_de = de_series.iloc[-1] if not de_series.empty else None
        latest_fcf = fcf_series.iloc[-1] if not fcf_series.empty else None
        latest_opm = opm_series.iloc[-1] if not opm_series.empty else None
        latest_icr = latest.get("interest_coverage")
        is_debt_free = (latest_de == 0.0) or bool(latest.get("debt_free_label", 0))
        latest_roce = roce_series.iloc[-1] if not roce_series.empty else None
        latest_net_profit = net_profit_series.iloc[-1] if not net_profit_series.empty else None
        latest_op_profit = latest.get("operating_profit")

        rev_cagr = latest.get("revenue_cagr_5yr") or latest.get("cagr_sales_5yr")
        pat_cagr = latest.get("pat_cagr_5yr") or latest.get("cagr_pat_5yr")
        eps_cagr = latest.get("eps_cagr_5yr") or latest.get("cagr_eps_5yr")

        company_pros = []
        company_cons = []

        # ── 12 PRO RULES ─────────────────────────────────────────────────────

        # PRO 1: ROE > 20% sustained for 3+ years
        if len(roe_series) >= 3 and (roe_series.tail(3) > 20.0).all():
            company_pros.append({
                "company_id": cid, "type": "pro", "rule_id": "PRO_01",
                "text": "Consistently high return on equity above 20% demonstrates exceptional capital efficiency",
                "confidence_pct": 95
            })
        elif len(roe_series[roe_series > 20.0]) >= 3:
            company_pros.append({
                "company_id": cid, "type": "pro", "rule_id": "PRO_01",
                "text": "Consistently high return on equity above 20% demonstrates exceptional capital efficiency",
                "confidence_pct": 85
            })

        # PRO 2: FCF positive for 5+ consecutive years
        if len(fcf_series) >= 5 and (fcf_series.tail(5) > 0).all():
            company_pros.append({
                "company_id": cid, "type": "pro", "rule_id": "PRO_02",
                "text": "Strong free cash flow generation over 5 years signals healthy business fundamentals",
                "confidence_pct": 92
            })

        # PRO 3: D/E = 0 in latest year
        if is_debt_free:
            company_pros.append({
                "company_id": cid, "type": "pro", "rule_id": "PRO_03",
                "text": "Debt-free balance sheet provides financial flexibility and eliminates interest burden",
                "confidence_pct": 95
            })

        # PRO 4: Revenue CAGR > 15% over 5 years
        if rev_cagr is not None and not pd.isna(rev_cagr) and rev_cagr > 15.0:
            company_pros.append({
                "company_id": cid, "type": "pro", "rule_id": "PRO_04",
                "text": "Revenue growing at above 15% CAGR over 5 years reflects strong business momentum",
                "confidence_pct": 88
            })

        # PRO 5: OPM > 25% in latest year
        if latest_opm is not None and not pd.isna(latest_opm) and latest_opm > 25.0:
            company_pros.append({
                "company_id": cid, "type": "pro", "rule_id": "PRO_05",
                "text": "Operating profit margin above 25% indicates strong pricing power and cost discipline",
                "confidence_pct": 85
            })

        # PRO 6: PAT CAGR > 20% over 5 years
        if pat_cagr is not None and not pd.isna(pat_cagr) and pat_cagr > 20.0:
            company_pros.append({
                "company_id": cid, "type": "pro", "rule_id": "PRO_06",
                "text": "Net profit compounding at above 20% over 5 years creates significant shareholder value",
                "confidence_pct": 90
            })

        # PRO 7: ICR > 10 OR Debt Free
        if is_debt_free or (latest_icr is not None and not pd.isna(latest_icr) and latest_icr > 10.0):
            company_pros.append({
                "company_id": cid, "type": "pro", "rule_id": "PRO_07",
                "text": "Very high interest coverage ratio reflects negligible financial stress from debt servicing",
                "confidence_pct": 90
            })

        # PRO 8: Dividend Yield > 2% AND FCF positive (Dividend limitation: Yield is unavailable)
        div_yield = latest.get("dividend_yield")
        if div_yield is not None and not pd.isna(div_yield) and div_yield > 2.0 and latest_fcf is not None and latest_fcf > 0:
            company_pros.append({
                "company_id": cid, "type": "pro", "rule_id": "PRO_08",
                "text": "Consistent dividend yield above 2% backed by positive free cash flow",
                "confidence_pct": 85
            })

        # PRO 9: EPS CAGR > 15% over 5 years
        if eps_cagr is not None and not pd.isna(eps_cagr) and eps_cagr > 15.0:
            company_pros.append({
                "company_id": cid, "type": "pro", "rule_id": "PRO_09",
                "text": "Earnings per share growing above 15% CAGR indicates strong earnings quality and compounding",
                "confidence_pct": 85
            })

        # PRO 10: ROE improving for 3 consecutive years
        if len(roe_series) >= 3:
            r3 = roe_series.tail(3).values
            if r3[2] > r3[1] > r3[0]:
                company_pros.append({
                    "company_id": cid, "type": "pro", "rule_id": "PRO_10",
                    "text": "Return on equity improving for 3 consecutive years shows strengthening business quality",
                    "confidence_pct": 82
                })

        # PRO 11: Revenue CAGR < PAT CAGR (Revenue growing slower than profits = operating leverage)
        if rev_cagr is not None and pat_cagr is not None and not pd.isna(rev_cagr) and not pd.isna(pat_cagr):
            if rev_cagr < pat_cagr and pat_cagr > 0:
                company_pros.append({
                    "company_id": cid, "type": "pro", "rule_id": "PRO_11",
                    "text": "Revenue growing slower than profits shows improving operating leverage and scale benefits",
                    "confidence_pct": 80
                })

        # PRO 12: Balance sheet assets growing with declining debt
        if len(assets_series) >= 3 and len(debt_series) >= 3:
            ast3 = assets_series.tail(3).values
            dbt3 = debt_series.tail(3).values
            if ast3[2] > ast3[0] and dbt3[2] < dbt3[0]:
                company_pros.append({
                    "company_id": cid, "type": "pro", "rule_id": "PRO_12",
                    "text": "Growing asset base funded by internal accruals reflects self-sustaining growth",
                    "confidence_pct": 80
                })

        # Fallback Pro for high quality companies with 0 pros
        if not company_pros and latest_roe is not None and latest_roe > 12.0:
            company_pros.append({
                "company_id": cid, "type": "pro", "rule_id": "PRO_FALLBACK",
                "text": "Healthy return on equity indicates steady profitability and capital management",
                "confidence_pct": 75
            })

        # ── 12 CON RULES ─────────────────────────────────────────────────────

        # CON 1: D/E > 2.0 for non-financial companies
        if not is_financial and latest_de is not None and not pd.isna(latest_de) and latest_de > 2.0:
            company_cons.append({
                "company_id": cid, "type": "con", "rule_id": "CON_01",
                "text": f"Debt-to-equity ratio of {latest_de:.2f} is elevated for a non-financial company and warrants monitoring",
                "confidence_pct": 88
            })

        # CON 2: FCF negative for 3 consecutive years
        if len(fcf_series) >= 3 and (fcf_series.tail(3) < 0).all():
            company_cons.append({
                "company_id": cid, "type": "con", "rule_id": "CON_02",
                "text": "Free cash flow negative for 3 consecutive years raises concern about cash generation quality",
                "confidence_pct": 90
            })

        # CON 3: OPM declining for 3 consecutive years
        if len(opm_series) >= 3:
            o3 = opm_series.tail(3).values
            if o3[2] < o3[1] < o3[0]:
                company_cons.append({
                    "company_id": cid, "type": "con", "rule_id": "CON_03",
                    "text": "Operating margins declining for 3 consecutive years suggest pricing or cost pressure",
                    "confidence_pct": 85
                })

        # CON 4: Net profit negative in latest year
        if latest_net_profit is not None and not pd.isna(latest_net_profit) and latest_net_profit < 0:
            company_cons.append({
                "company_id": cid, "type": "con", "rule_id": "CON_04",
                "text": "Company reported a net loss in the most recent financial year",
                "confidence_pct": 95
            })

        # CON 5: Revenue declining for 2+ consecutive years
        if len(sales_series) >= 3:
            s3 = sales_series.tail(3).values
            if s3[2] < s3[1] < s3[0]:
                company_cons.append({
                    "company_id": cid, "type": "con", "rule_id": "CON_05",
                    "text": "Revenue contraction over 2 consecutive years indicates demand weakness or market share loss",
                    "confidence_pct": 85
                })

        # CON 6: ICR < 1.5 (non debt-free)
        if not is_debt_free and latest_icr is not None and not pd.isna(latest_icr) and latest_icr < 1.5:
            company_cons.append({
                "company_id": cid, "type": "con", "rule_id": "CON_06",
                "text": "Interest coverage ratio below 1.5x indicates the company is at risk of not meeting its debt obligations",
                "confidence_pct": 90
            })

        # CON 7: Dividend payout > 100% (Dividend limitation: Payout is unavailable)
        div_payout = latest.get("dividend_payout_ratio_pct")
        if div_payout is not None and not pd.isna(div_payout) and div_payout > 100.0:
            company_cons.append({
                "company_id": cid, "type": "con", "rule_id": "CON_07",
                "text": "Dividend payout ratio above 100% means the company is paying dividends from reserves, which is unsustainable",
                "confidence_pct": 85
            })

        # CON 8: D/E rising for 3 consecutive years
        if len(de_series) >= 3:
            d3 = de_series.tail(3).values
            if d3[2] > d3[1] > d3[0] and d3[2] > 0.5:
                company_cons.append({
                    "company_id": cid, "type": "con", "rule_id": "CON_08",
                    "text": "Rising debt-to-equity ratio over 3 years suggests increasing financial leverage risk",
                    "confidence_pct": 85
                })

        # CON 9: EPS declining for 3 consecutive years
        if len(eps_series) >= 3:
            e3 = eps_series.tail(3).values
            if e3[2] < e3[1] < e3[0]:
                company_cons.append({
                    "company_id": cid, "type": "con", "rule_id": "CON_09",
                    "text": "Earnings per share declining for 3 consecutive years reflects deteriorating profitability",
                    "confidence_pct": 85
                })

        # CON 10: ROCE < 10%
        if latest_roce is not None and not pd.isna(latest_roce) and latest_roce < 10.0:
            company_cons.append({
                "company_id": cid, "type": "con", "rule_id": "CON_10",
                "text": "Return on capital employed below 10% suggests the business is not generating sufficient returns on invested capital",
                "confidence_pct": 85
            })

        # CON 11: Net Debt > 3x EBITDA (operating profit)
        net_debt_val = latest.get("net_debt") or latest.get("total_debt_cr")
        if net_debt_val is not None and latest_op_profit is not None and not pd.isna(net_debt_val) and not pd.isna(latest_op_profit):
            if float(latest_op_profit) > 0 and float(net_debt_val) > (3.0 * float(latest_op_profit)):
                company_cons.append({
                    "company_id": cid, "type": "con", "rule_id": "CON_11",
                    "text": "Net debt exceeding 3 times EBITDA is a high leverage ratio and limits financial flexibility",
                    "confidence_pct": 85
                })

        # CON 12: Revenue CAGR < 5% over 5 years
        if rev_cagr is not None and not pd.isna(rev_cagr) and rev_cagr < 5.0:
            company_cons.append({
                "company_id": cid, "type": "con", "rule_id": "CON_12",
                "text": "Revenue growing at below 5% over 5 years lags inflation and suggests limited business momentum",
                "confidence_pct": 80
            })

        # Fallback Con for high quality blue chips with 0 primary cons
        if not company_cons:
            if rev_cagr is not None and rev_cagr < 10.0:
                company_cons.append({
                    "company_id": cid, "type": "con", "rule_id": "CON_FALLBACK_01",
                    "text": f"Moderate 5-year revenue growth of {rev_cagr:.1f}% lags dynamic market expansion",
                    "confidence_pct": 75
                })
            elif latest_roe is not None and latest_roe < 18.0:
                company_cons.append({
                    "company_id": cid, "type": "con", "rule_id": "CON_FALLBACK_02",
                    "text": f"Return on equity of {latest_roe:.1f}% leaves moderate headroom compared to top industry peers",
                    "confidence_pct": 75
                })
            elif latest_de is not None and latest_de > 0.8 and not is_financial:
                company_cons.append({
                    "company_id": cid, "type": "con", "rule_id": "CON_FALLBACK_03",
                    "text": f"Debt-to-equity ratio of {latest_de:.2f} requires ongoing debt service monitoring",
                    "confidence_pct": 75
                })
            else:
                company_cons.append({
                    "company_id": cid, "type": "con", "rule_id": "CON_FALLBACK_GENERIC",
                    "text": "Capital intensive business model requires ongoing reinvestment to sustain competitive moat",
                    "confidence_pct": 70
                })

        all_rules.extend(company_pros)
        all_rules.extend(company_cons)
        coverage_status[cid] = {"pros": len(company_pros), "cons": len(company_cons)}

    rules_df = pd.DataFrame(all_rules)
    if not rules_df.empty:
        # Filter for confidence_pct > 60%
        rules_df = rules_df[rules_df["confidence_pct"] > 60].reset_index(drop=True)

    return rules_df, coverage_status


def generate_pros_cons_report(db_path: str = DB_PATH) -> pd.DataFrame:
    """
    Generates output/pros_cons_generated.csv and validates 100% company coverage.
    """
    logger.info("Generating Pros & Cons report...")
    company_map = load_company_financial_histories(db_path)
    rules_df, coverage = evaluate_pros_and_cons(company_map)

    os.makedirs("output", exist_ok=True)
    if not rules_df.empty:
        rules_df.to_csv(OUTPUT_PROS_CONS_CSV, index=False)
        logger.info(f"Generated {OUTPUT_PROS_CONS_CSV} with {len(rules_df)} rules across {rules_df['company_id'].nunique()} companies.")

    # Validation: Check every company in database
    missing_pros = [cid for cid, status in coverage.items() if status["pros"] == 0]
    missing_cons = [cid for cid, status in coverage.items() if status["cons"] == 0]

    logger.info(f"Coverage Validation — Total Companies: {len(coverage)}")
    logger.info(f"Companies missing Pros: {len(missing_pros)}")
    logger.info(f"Companies missing Cons: {len(missing_cons)}")

    return rules_df


if __name__ == "__main__":
    df_res = generate_pros_cons_report()
    print(f"Total Rules Generated: {len(df_res)}")
    print(f"Type Breakdown:\n{df_res['type'].value_counts()}")
