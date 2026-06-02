import sqlite3
import pandas as pd

DB_PATH = "data/db/military_equipment.db"

def table_overview(table):
    conn = sqlite3.connect(DB_PATH)

    print(f"\n=== Table: {table} ===")

    # Columns
    cols = pd.read_sql_query(f"PRAGMA table_info('{table}')", conn)
    print("\nColumns:")
    print(cols[['cid', 'name', 'type']])

    # Row count
    count = conn.execute(f"SELECT COUNT(*) FROM '{table}'").fetchone()[0]
    print(f"\nRows: {count}")

    # Sample
    print("\nSample rows:")
    print(pd.read_sql_query(f"SELECT * FROM '{table}' LIMIT 10", conn))

    conn.close()

if __name__ == "__main__":
    table_overview("united_states_table_03_small_arms")
