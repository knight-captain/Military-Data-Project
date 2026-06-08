"""
scrape_pipe.py
--------------
Handles Phase I of the pipeline:

This module does NOT open DB connections or run cleaning/synthesis.
"""

import shutil
from datetime import datetime
from pathlib import Path

from data.data_acquisition.scrape_wiki import scrape_all_to_sqlite

# CONFIG

DB_DIR = Path("data/db")

# MAIN ENTRY POINT
def scrape_pipe():
    DB_DIR.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%y%m%d%H%M%S")
    raw_path = DB_DIR / f"military_equipment_{stamp}-RAW.db"
    scrape_all_to_sqlite(db_path=raw_path)
    print(f"Scrape complete. Using DB: {raw_path}")
    return raw_path

