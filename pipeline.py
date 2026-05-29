import os
import shutil
import sqlite3

# --- Modules ---
from data.data_acquisition.scrape_wiki import scrape_all_to_sqlite
from data.data_cleaning.clean_columns import clean_columns
from data.data_cleaning.clean_rows import clean_rows


def get_next_db_path():
    DB_DIR = os.path.join("data", "db")
    os.makedirs(DB_DIR, exist_ok=True)

    existing = [
        f for f in os.listdir(DB_DIR)
        if f.startswith("military_equipment_") and f.endswith(".db")
    ]

    if not existing:
        next_num = 1
    else:
        nums = [
            int(f.split("_")[-1].split(".")[0])
            for f in existing
        ]
        next_num = max(nums) + 1

    return os.path.join(DB_DIR, f"military_equipment_{next_num:02d}.db")


def run_pipeline():
    '''Run the whole project:
    - Scraper (set T or F)
    - Comment out clean_columns() or clean_rows() if necessary
    '''
    # --- Phase I: Scrape ---
    RUN_SCRAPER = False #<- set True to run scraper, or False to just work on a test .db 
    TEST_DB = "data/db/military_equipment_TEST.db"
    DEV_DB = "data/db/military_equipment_TESTED.db" 
    if RUN_SCRAPER:
        db_path = get_next_db_path()
        print("\n=== PHASE I: SCRAPING WIKIPEDIA ===")
        print(f"\nUsing next database: {db_path}")
        scrape_all_to_sqlite(db_path=db_path)
    else:
        # Make a fresh copy of the TEST DB for development
        if os.path.exists(DEV_DB):
            os.remove(DEV_DB)
        shutil.copy(TEST_DB, DEV_DB)
        db_path = DEV_DB
        print(f"\nSkipping Phase I: Scrape. Using database: {db_path}")


    # --- Phase II: Clean tables ---
    print("\n=== PHASE II: CLEANING TABLES ===")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    tables = cursor.execute("SELECT table_name FROM a_meta_table").fetchall()
    tables = [t[0] for t in tables]

    for table in tables:
        if table.startswith("a_"):
            continue

        print(f"Cleaning {table}")
        clean_columns(table, conn=conn, db_path=db_path)
        clean_rows(table, conn=conn, db_path=db_path)
    
    # --- Phase III: Join tables ---
    #TODO

    # Don't close the connection until other Pipeline funcs have had a chance to use it, so it doesn't strobe.
    conn.close()

    print("\n=== PIPELINE COMPLETE ===")
    print(f"All tables scraped and cleaned into: {db_path}\n")


if __name__ == "__main__":
    run_pipeline()
