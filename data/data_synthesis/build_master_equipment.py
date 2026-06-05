import sqlite3
import csv
from pathlib import Path
from utils.safe_SQL_caller import q, ql

# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = PROJECT_ROOT / "data" / "db" / "military_equipment_TESTED.db"
MAPPING_PATH = PROJECT_ROOT / "ontology" / "column_mapping.csv"
SUPER_COLS_PATH = PROJECT_ROOT / "ontology" / "super_columns.txt"


def load_column_mapping():
    mapping = {}
    with open(MAPPING_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            orig = row["original_column"].strip()
            super_col = row["super_column"].strip()
            if orig and super_col:
                mapping[orig] = super_col
    return mapping

def load_super_columns():
    cols = []
    with open(SUPER_COLS_PATH, encoding="utf-8") as f:
        for line in f:
            c = line.strip()
            if c:
                cols.append(c)
    return cols

def list_tables(conn):
    q = "SELECT name FROM sqlite_master WHERE type='table'"
    tables = [row[0] for row in conn.execute(q).fetchall()]
    return [
        t for t in tables
        if not t.startswith("a_")
    ]


def get_table_columns(conn, table):
    info = conn.execute(f'PRAGMA table_info("{table}")').fetchall()
    return [col[1] for col in info]

def load_table_countries(conn):
    q = 'SELECT table_name, country FROM a_meta_table'
    return {row[0]: row[1] for row in conn.execute(q).fetchall()}

def build_aligned_select(table, conn, mapping, super_cols, table_countries):
    table_cols = get_table_columns(conn, table)

    parts = [f'{q(table)} AS source_table']

    # country if present
    country = table_countries.get(table, None)
    if country:
        parts.append(f"{ql(country)} AS country")
    else:
        parts.append("NULL AS country")

    # canonical super-columns
    for super_col in super_cols:
        orig_matches = [oc for oc in table_cols if mapping.get(oc) == super_col]
        if orig_matches:
            parts.append(f'{q(orig_matches[0])} AS {q(super_col)}')
        else:
            parts.append(f'NULL AS "{super_col}"')

    return "SELECT " + ", ".join(parts) + f" FROM {q(table)}"

# def build_union_sql(conn, mapping, super_cols):
#     selects = []
#     for t in list_tables(conn):
#         selects.append(build_aligned_select(t, conn, mapping, super_cols))
#     return "\nUNION ALL\n".join(selects)

def chunked(iterable, size):
    for i in range(0, len(iterable), size):
        yield iterable[i:i+size]

def build_master_equipment():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    mapping = load_column_mapping()
    super_cols = load_super_columns()

    tables = list_tables(conn)

    # Chunk tables to avoid SQLite's 500-term UNION limit
    batches = list(chunked(tables, 300))  # 300 is safe

    temp_tables = []

    for i, batch in enumerate(batches):
        temp_name = f"temp_batch_{i}"
        temp_tables.append(temp_name)

        # Build aligned SELECTs for this batch
        table_countries = load_table_countries(conn)

        selects = [
            build_aligned_select(t, conn, mapping, super_cols, table_countries)
            for t in batch
        ]


        union_sql = " UNION ALL ".join(selects)

        cursor.execute(f"CREATE TEMP TABLE {temp_name} AS {union_sql}")

    # Final merge of all temp tables
    final_union = " UNION ALL ".join(
        f"SELECT * FROM {q(t)}" for t in temp_tables
    )

    cursor.execute("DROP TABLE IF EXISTS a_master_equipment")
    cursor.execute(f"CREATE TABLE a_master_equipment AS {final_union}")

    conn.commit()
    conn.close()

    print("Created a_master_equipment")


if __name__ == "__main__":
    build_master_equipment()
