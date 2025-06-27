import pandas as pd
import sqlite3
from pathlib import Path

# --- Configuration ---
# Define project structure paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "03_primary" / "nber_papers.db"
OUTPUT_PATH = PROJECT_ROOT / "data" / "03_primary" / "nber_full_text.parquet"
DB_TABLE_NAME = "papers"


def create_searchable_dataset():
    """
    Loads paper data from the SQLite database, prepares a clean dataset with
    full text and all necessary metadata, and saves it to a Parquet file for the app.
    """
    print("--- Starting Full-Text Dataset Creation ---")

    # 1. Connect to the database and load the full dataset
    if not DB_PATH.exists():
        print(f"Error: Database not found at {DB_PATH}. Please run the ingest script first.")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql(f"SELECT * FROM {DB_TABLE_NAME}", conn)
        conn.close()
        print(f"Successfully loaded {len(df)} records from the database.")
    except Exception as e:
        print(f"Error reading from database: {e}")
        return

    # 2. Prepare the data for analysis
    print("Preparing full-text data...")
    # Fill any potential missing values in text columns
    df['abstract'] = df['abstract'].fillna('')
    df['title'] = df['title'].fillna('')
    # Combine title and abstract for a full text search and convert to lowercase
    df['full_text'] = (df['title'] + ' ' + df['abstract']).str.lower()
    
    # Convert issue_date to datetime objects
    df['issue_date'] = pd.to_datetime(df['issue_date'])
    # Extract year
    df['year'] = df['issue_date'].dt.year
    
    # Select and keep only the necessary columns for the app
    # This now includes metadata for the new tables.
    app_data = df[['year', 'paper', 'title', 'author', 'issue_date', 'doi', 'full_text']].copy()

    # 3. Save the final dataset to a Parquet file
    try:
        app_data.to_parquet(OUTPUT_PATH, index=False)
        print(f"Successfully saved enriched dataset to {OUTPUT_PATH}")
    except Exception as e:
        print(f"Error saving to Parquet file: {e}")


if __name__ == '__main__':
    create_searchable_dataset()
    print("\n--- Full-text processing finished. ---")
