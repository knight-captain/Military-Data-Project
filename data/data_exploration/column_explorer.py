import sqlite3
import csv
from pathlib import Path
from tabulate import tabulate

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = PROJECT_ROOT / "data" / "db" / "military_equipment_TESTED.db"
MAPPING_PATH = PROJECT_ROOT / "ontology" / "column_mapping.csv"


def load_mapping():
    mapping = {}
    with open(MAPPING_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw = row["raw_col"].strip()
            supercol = row["super_col"].strip()
            mapping[raw] = supercol
    return mapping


def reverse_mapping(mapping):
    rev = {}
    for raw, supercol in mapping.items():
        if supercol:
            rev.setdefault(supercol, []).append(raw)
    return rev


def get_all_columns(conn):
    q = "PRAGMA table_info(a_master_equipment)"
    return [row[1] for row in conn.execute(q).fetchall()]


def get_nonempty_columns(conn, raw_col):
    cols = get_all_columns(conn)
    nonempty = []

    for c in cols:
        q = f"""
        SELECT COUNT(*) 
        FROM a_master_equipment
        WHERE "{raw_col}" IS NOT NULL
          AND TRIM("{raw_col}") <> ''
          AND "{c}" IS NOT NULL
          AND TRIM("{c}") <> '';
        """
        count = conn.execute(q).fetchone()[0]
        if count > 0:
            nonempty.append(c)

    return nonempty


def fetch_table(conn, raw_col, cols, limit=50):
    col_list = ", ".join(f'"{c}"' for c in cols)
    q = f"""
    SELECT {col_list}
    FROM a_master_equipment
    WHERE "{raw_col}" IS NOT NULL
      AND TRIM("{raw_col}") <> ''
    LIMIT {limit};
    """
    rows = conn.execute(q).fetchall()
    return rows


def explore_column(raw_col):
    conn = sqlite3.connect(DB_PATH)
    mapping = load_mapping()
    rev = reverse_mapping(mapping)

    print("\n==============================")
    print(f" EXPLORING COLUMN: {raw_col}")
    print("==============================\n")

    # 1. Current mapping
    current = mapping.get(raw_col, "")
    print(f"Current mapping: {current if current else '(unmapped)'}")

    # 2. Reverse mapping (other raw columns mapped to same super-col)
    if current:
        print("\nOther raw columns mapped to this super-column:")
        for c in rev.get(current, []):
            if c != raw_col:
                print("  -", c)
    else:
        print("\nThis column is currently unmapped.")

    # 3. Co-occurring columns
    print("\nFinding co-occurring columns...")
    nonempty_cols = get_nonempty_columns(conn, raw_col)
    print(f"Found {len(nonempty_cols)} relevant columns.")

    # 4. Table output
    rows = fetch_table(conn, raw_col, nonempty_cols)
    print("\n=== DATA SAMPLE (first 50 rows) ===\n")
    print(tabulate(rows, headers=nonempty_cols, tablefmt="grid"))

    conn.close()



def main():
    conn = sqlite3.connect(DB_PATH)
    cols = get_all_columns(conn)
    conn.close()

    mapping = load_mapping()
    print("\nAvailable columns:")
    for c in cols:
        print("  -", c)

    while True:

        print("\nEnter a column to explore (blank = show unmapped, Ctrl+C to exit):")
        raw_col = input("> ").strip()

        # If blank: show unmapped columns
        if raw_col == "":
            print("\n=== UNMAPPED COLUMNS ===")
            unmapped = [raw for raw, supercol in mapping.items() if not supercol]
            for u in unmapped:
                print("  -", u)
            print("\n(Press Enter again to refresh, or type a column to explore.)")
            continue

        # Validate column
        if raw_col not in cols:
            print("Column not found.")
            continue

        explore_column(raw_col)


if __name__ == "__main__":
    main()
