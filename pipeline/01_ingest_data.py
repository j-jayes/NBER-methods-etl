import pandas as pd
import sqlite3
from pathlib import Path
import csv

# --- Configuration ---
# Define the base URL for NBER data
BASE_URL = "http://data.nber.org/nber_paper_chapter_metadata/tsv/"

# Define project structure paths
# This assumes the script is run from the root of the NBER-METHODS-ETL directory
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "03_primary" / "nber_papers.db"
TABLE_NAME = "papers"

def ingest_and_update_db():
    """
    Downloads the latest NBER metadata, cleans the data, compares it against
    an existing SQLite database, and appends only the new papers.

    Returns:
        pd.DataFrame: A DataFrame containing the newly added papers. Returns
                      an empty DataFrame if no new papers were found or if an
                      error occurred.
    """
    print("--- Starting NBER Data Ingestion and Update ---")
    
    # 1. Ensure the destination directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # 2. Download and merge the latest data from NBER URLs
    try:
        print("Downloading core reference data (ref.tsv)...")
        latest_df = pd.read_csv(
            f"{BASE_URL}ref.tsv",
            sep='\t',
            names=['paper', 'author', 'title', 'issue_date', 'doi'],
            header=0,
            engine='python',
            quoting=csv.QUOTE_NONE
        )
        print(f"Successfully loaded {latest_df.shape[0]} total records from ref.tsv.")
        
        print("Downloading abstracts (abs.tsv)...")
        abstracts_df = pd.read_csv(
            f"{BASE_URL}abs.tsv",
            sep='\t',
            names=['paper', 'abstract'],
            header=0,
            engine='python',
            quoting=csv.QUOTE_NONE
        )
        latest_df = pd.merge(latest_df, abstracts_df, on="paper", how="left")
        print("Successfully merged abstracts.")

    except Exception as e:
        print(f"Error: Failed to download or process NBER data. {e}")
        return pd.DataFrame()

    # --- MORE ROBUST Data Cleaning Step ---
    print("Cleaning 'issue_date' column...")
    original_rows = len(latest_df)
    
    # Force the column to string type first to ensure consistent parsing behavior
    latest_df['issue_date'] = latest_df['issue_date'].astype(str)
    
    # Convert to datetime, coercing errors will turn invalid dates like '0000-00-00' into NaT
    latest_df['issue_date'] = pd.to_datetime(latest_df['issue_date'], errors='coerce')
    
    # Drop rows where the date conversion resulted in NaT (Not a Time) using reassignment
    latest_df = latest_df.dropna(subset=['issue_date'])
    
    rows_dropped = original_rows - len(latest_df)
    if rows_dropped > 0:
        print(f"Dropped {rows_dropped} rows due to invalid dates.")
    # --- End of Cleaning Step ---

    # 3. Connect to SQLite DB and get existing paper IDs
    existing_ids = set()
    try:
        conn = sqlite3.connect(DB_PATH)
        if pd.io.sql.table_exists(TABLE_NAME, conn):
            print(f"Database found at {DB_PATH}. Fetching existing paper IDs...")
            existing_ids_df = pd.read_sql(f"SELECT paper FROM {TABLE_NAME}", conn)
            existing_ids = set(existing_ids_df['paper'])
            print(f"Found {len(existing_ids)} existing papers in the database.")
        else:
            print("No existing database found. A new one will be created.")
        conn.close()
    except Exception as e:
        print(f"Error connecting to or reading from the database: {e}")
        pass
        
    # 4. Identify new papers by filtering
    new_papers_df = latest_df[~latest_df['paper'].isin(existing_ids)]

    # 5. If there are new papers, append them to the database
    if not new_papers_df.empty:
        print(f"Found {len(new_papers_df)} new papers to add.")
        try:
            conn = sqlite3.connect(DB_PATH)
            new_papers_df.to_sql(
                TABLE_NAME,
                conn,
                if_exists='append',
                index=False
            )
            conn.close()
            print("Successfully appended new papers to the database.")
            return new_papers_df
        except Exception as e:
            print(f"Error: Failed to write new papers to the database. {e}")
            return pd.DataFrame()
    else:
        print("No new papers found. The database is already up-to-date.")
        return pd.DataFrame()

if __name__ == '__main__':
    newly_added_papers = ingest_and_update_db()
    if not newly_added_papers.empty:
        print("\n--- Summary of Newly Added Papers ---")
        print(newly_added_papers[['paper', 'title', 'issue_date']].head())
    print("\n--- Pipeline execution finished. ---")
