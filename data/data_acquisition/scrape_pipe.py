"""
scrape_pipe.py
--------------
Handles Phase I of the pipeline.
"""

from datetime import datetime
from pathlib import Path

from data.data_acquisition.page_list import *
from data.data_acquisition.scrape_wiki import scrape_all_to_sqlite


# CONFIG

DB_DIR = Path("data/db/runs")

# MAIN ENTRY POINT
def scrape_pipe(scrape_mode):
    """
    mode:
        True  → full scrape
        False → skip (handled in pipeline)
        str   → test scrape using edge-case list, DB named after mode
    """
    DB_DIR.mkdir(parents=True, exist_ok=True)

    if scrape_mode is True:
        stamp = datetime.now().strftime("%y%m%d%H%M%S")
        raw_path = DB_DIR / f"military_equipment_{stamp}-RAW.db"
        list_of_links = get_links()
    else: 
        list_of_links = edge_list()
        raw_path = DB_DIR / f"military_equipment_{scrape_mode}-RAW.db"

    scrape_all_to_sqlite(db_path=raw_path, links=list_of_links)
    
    print(f"Scrape complete. Using DB: {raw_path}")
    return raw_path

