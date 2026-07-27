import shutil
import sqlite3
from utils.update_path import update_path

from data.data_analysis.build_country_equipment_summary import build_country_equipment_summary

def analyze_data(db_path):
    if db_path is None:
        raise ValueError("db_path must be provided.")

    # Build REFINED path & Copy SYNTHED → REFINED, then connect to the new .db
    analyzed_path = update_path(db_path)
    shutil.copy(db_path, analyzed_path)
    conn = sqlite3.connect(analyzed_path)

    build_country_equipment_summary(conn)

    conn.close()
    print("\nData Analysis complete")

    return analyzed_path