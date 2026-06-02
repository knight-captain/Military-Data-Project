import sqlite3
import pandas as pd

DB_PATH = "data/db/military_equipment.db"

def list_tables(conn):
    q = "SELECT name FROM sqlite_master WHERE type='table'"
    return [row[0] for row in conn.execute(q).fetchall()]

def tables_with_column(conn, column):
    tables = list_tables(conn)
    hits = []
    for t in tables:
        cols = [c[1] for c in conn.execute(f"PRAGMA table_info('{t}')")]
        if column in cols:
            hits.append(t)
    return hits

def sample_values(conn, table, column, limit=20):
    q = f"SELECT DISTINCT \"{column}\" FROM '{table}' LIMIT {limit}"
    return pd.read_sql_query(q, conn)

def explore_column(column):
    conn = sqlite3.connect(DB_PATH)

    print(f"\n=== Exploring column: {column} ===")
    hits = tables_with_column(conn, column)
    print(f"Found in {len(hits)} tables")

    for t in hits[:10]:  # show first 10 tables
        print(f"\n--- {t} ---")
        print(sample_values(conn, t, column))

    conn.close()

if __name__ == "__main__":
    explore_column("caliber")
