import sqlite3
import pandas as pd

DB_PATH = "data/db/military_equipment.db"

def column_frequency():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM a_meta_table_of_columns", conn)
    conn.close()

    counts = df.notna().sum().sort_values(ascending=False)
    print(counts)

if __name__ == "__main__":
    column_frequency()
