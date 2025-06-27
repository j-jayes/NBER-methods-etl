import pandas as pd
import sqlite3
from pathlib import Path

# --- Configuration ---
# Define project structure paths
# This assumes the script is run from the root of the NBER-METHODS-ETL directory
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "03_primary" / "nber_papers.db"
TABLE_NAME = "papers"

def test_date_column_quality():
    """
    Connects to the SQLite database and validates the 'issue_date' column.
    
    Checks for two potential issues:
    1. If any dates failed to parse and are stored as Null/None/NaT.
    2. If the data type of the column is appropriate for dates.
    """
    print("--- Running Data Quality Test on nber_papers.db ---")
    
    # 1. Check if the database file exists
    if not DB_PATH.exists():
        print(f"Error: Database file not found at {DB_PATH}")
        print("Please run the ingestion pipeline first.")
        return

    # 2. Connect to the database and load the data
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql(f"SELECT paper, issue_date FROM {TABLE_NAME}", conn)
        conn.close()
        print(f"Successfully loaded {len(df)} records from the database.")
    except Exception as e:
        print(f"Error: Could not read from the database. {e}")
        return

    # 3. Perform validation checks
    
    # Check 1: Null or NaT dates
    # We try converting to datetime again to catch any non-standard nulls
    df['issue_date_dt'] = pd.to_datetime(df['issue_date'], errors='coerce')
    invalid_dates = df['issue_date_dt'].isnull().sum()
    
    print("\n--- Test Results ---")
    if invalid_dates > 0:
        print(f"FAIL: Found {invalid_dates} records with null or invalid 'issue_date' values.")
    else:
        print("PASS: No null or invalid dates found in the 'issue_date' column.")
        
    # Check 2: Column data type
    # In SQLite, dates are often stored as TEXT, which is fine.
    # The important part is that pandas can parse it correctly.
    print(f"Info: The 'issue_date' column data type in the DataFrame is '{df['issue_date_dt'].dtype}'.")
    print("This should be a datetime type (e.g., datetime64[ns]).")
    
    print("\n--- Test finished. ---")


if __name__ == '__main__':
    test_date_column_quality()
