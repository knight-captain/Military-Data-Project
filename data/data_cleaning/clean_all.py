import sqlite3
import pandas as pd
from clean_table import clean_table
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # goes from data_cleaning → data
DB_PATH = BASE_DIR / "db" / "military_equipment_01-Copy.db"

def clean_all():
    conn = sqlite3.connect(DB_PATH)

    tables = pd.read_sql_query(
        "SELECT table_name FROM a_meta_table",
        conn
    )["table_name"].tolist()

    cursor = conn.cursor()

    for table in tables:
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,)
        )
        exists = cursor.fetchone()

        if not exists:
            print(f"Skipping missing table: {table}")
            continue

        clean_table(conn, table)

    conn.close()
    print("All tables cleaned.")

if __name__ == "__main__":
    clean_all()