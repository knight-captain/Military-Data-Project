import sqlite3
from utils.safe_SQL_caller import q
from tabulate import tabulate
import random

DB_PATH = r"C:\Users\mckay\OneDrive\Documents\Code\Military Data Project\data\db\military_equipment_260610081832-SYNTHED.db"

def get_super_columns(conn):
    cur = conn.execute("PRAGMA table_info(a_master_equipment)")
    cols = [row[1] for row in cur.fetchall()]
    return [c for c in cols if c != "table_name"]

def count_non_null(conn, col):
    cur = conn.execute(
        f"SELECT COUNT({q(col)}) FROM a_master_equipment WHERE {q(col)} IS NOT NULL"
    )
    return cur.fetchone()[0]

def count_unique(conn, col):
    cur = conn.execute(
        f"SELECT COUNT(DISTINCT {q(col)}) FROM a_master_equipment WHERE {q(col)} IS NOT NULL"
    )
    return cur.fetchone()[0]

def sample_values(conn, col, n=10):
    cur = conn.execute(
        f"SELECT DISTINCT {q(col)} FROM a_master_equipment "
        f"WHERE {q(col)} IS NOT NULL ORDER BY RANDOM() LIMIT {n}"
    )
    return [r[0] for r in cur.fetchall()]


def one_random_row_per_table(conn):
    sql = """
    SELECT *
    FROM a_master_equipment
    WHERE rowid IN (
        SELECT MIN(rowid)
        FROM (
            SELECT rowid, table_name
            FROM a_master_equipment
            ORDER BY RANDOM()
        )
        GROUP BY table_name
    )
    ORDER BY table_name
    """
    cur = conn.execute(sql)
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    print("\n=== ONE RANDOM ROW PER TABLE ===")
    print(tabulate(rows, headers=cols, tablefmt="grid"))

def explore_columns():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    super_cols = get_super_columns(conn)

    print("\n=== COLUMN SUMMARY ===")
    summary = []
    for col in super_cols:
        nn = count_non_null(conn, col)
        uq = count_unique(conn, col)
        summary.append([col, nn, uq])

    print(tabulate(summary, headers=["Column", "Non-Null Count", "Unique Count"], tablefmt="grid"))

    print("\n=== COLUMNS WITH < 100 UNIQUE VALUES ===")
    small = [row for row in summary if row[2] < 100]
    print(tabulate(small, headers=["Column", "Non-Null Count", "Unique Count"], tablefmt="grid"))

    print("\n=== SAMPLE VALUES FOR SMALL COLUMNS ===")
    for col, nn, uq in small:
        print(f"\n--- {col} ({uq} uniques) ---")
        vals = sample_values(conn, col)
        for v in vals:
            print("  ", v)

    # one_random_row_per_table(conn)

    conn.close()

if __name__ == "__main__":
    explore_columns()
