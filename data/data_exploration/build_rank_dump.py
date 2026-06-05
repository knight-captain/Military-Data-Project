import sqlite3
from pathlib import Path

DB_PATH = "data/db/military_equipment_TESTED.db"

BASE_DIR = Path(__file__).resolve().parent
RANK_LIST_PATH = BASE_DIR / "rank_tables.txt"

def load_rank_tables():
    with open(RANK_LIST_PATH, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def delete_rank_tables(conn, rank_tables):
    for t in rank_tables:
        print(f"Dropping {t}...")
        conn.execute(f'DROP TABLE IF EXISTS "{t}"')

def get_all_rank_columns(conn, rank_tables):
    cols = set()
    for t in rank_tables:
        info = conn.execute(f"PRAGMA table_info('{t}')").fetchall()
        for _, name, *_ in info:
            cols.add(name)
    return sorted(cols)

def build_aligned_select(table, all_cols, conn):
    info = conn.execute(f"PRAGMA table_info('{table}')").fetchall()
    table_cols = {col[1] for col in info}

    parts = [f"'{table}' AS source_table"]
    for col in all_cols:
        if col in table_cols:
            parts.append(f'"{col}"')
        else:
            parts.append(f'NULL AS "{col}"')

    return "SELECT " + ", ".join(parts) + f' FROM "{table}"'

def build_union_sql(rank_tables, all_cols, conn):
    selects = [build_aligned_select(t, all_cols, conn) for t in rank_tables]
    return "\nUNION ALL\n".join(selects)

def build_rank_dump():
    conn = sqlite3.connect(DB_PATH)

    rank_tables = load_rank_tables()
    print(f"Loaded {len(rank_tables)} rank tables")

    all_cols = get_all_rank_columns(conn, rank_tables)
    print(f"Found {len(all_cols)} unique rank columns")

    union_sql = build_union_sql(rank_tables, all_cols, conn)

    conn.execute("DROP TABLE IF EXISTS a_unified_ranks")
    conn.execute(f"CREATE TABLE a_unified_ranks AS {union_sql}")

    delete_rank_tables(conn, rank_tables)
    print("Deleted original rank tables")

    conn.commit()
    conn.close()
    print("Created a_unified_ranks table")

if __name__ == "__main__":
    build_rank_dump()
