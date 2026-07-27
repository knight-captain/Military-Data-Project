import shutil
import sqlite3
import pandas as pd
from utils.update_path import update_path
from data.data_analysis.build_country_equipment_summary import build_country_equipment_summary

def analyze_data(db_path):
    if db_path is None:
        raise ValueError("db_path must be provided.")

    # 1. Create timestamped ANALYZED DB
    analyzed_path = update_path(db_path)
    shutil.copy(db_path, analyzed_path)

    # 2. Run analysis SQL on ANALYZED
    conn = sqlite3.connect(analyzed_path)
    build_country_equipment_summary(conn)
    conn.close()

    # 3. Copy ANALYZED → PROD
    prod_path = "data/db/military_equipment_PROD.db"
    shutil.copy(analyzed_path, prod_path)

    # 4. Export Phase V table to Excel for Tableau Public
    conn = sqlite3.connect(prod_path)
    df = pd.read_sql("SELECT * FROM country_equipment_summary", conn)
    df.to_excel("data/db/military_equipment_PROD.xlsx", index=False)
    conn.close()

    print("\nData Analysis complete.")
    print(f"ANALYZED DB: {analyzed_path}")
    print(f"PROD DB: {prod_path}")
    print("Exported Excel for Tableau Public.")

    return analyzed_path
