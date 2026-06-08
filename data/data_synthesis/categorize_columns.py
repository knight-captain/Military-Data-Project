"""
Builds a context-aware column mapping for every raw table.
Inputs:
    - a_table_categories (from categorize_tables.py)
    - ontology/column_mapping.csv (raw→super base mapping)
    - ontology/super_columns.txt (canonical schema)
    - raw table columns (from a_meta_table_of_columns or PRAGMA)
Output:
    - a_column_mapping_contextual (DB table)
    - dict mapping (table_name, raw_column) → super_column
"""

import csv
from pathlib import Path
from utils.safe_SQL_caller import q

# LOAD BASE ONTOLOGY MAPPING
def load_base_column_mapping(path):
    """
    Load raw→super mappings from ontology/column_mapping.csv.
    """
    mapping = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw = row["original_column"].strip()
            super_col = row["super_column"].strip()
            if raw and super_col:
                mapping[raw] = super_col
    return mapping


# LOAD TABLE CATEGORIES
def load_table_categories(conn):
    """
    Load table categories from a_table_categories.

    Returns:
        dict: { table_name : {branch, role, domain, type, platform, ignore} }
    """
    sql = """
        SELECT table_name, branch, role, domain, type, platform, ignore
        FROM a_table_categories
    """
    categories = {}
    for row in conn.execute(sql).fetchall():
        table_name, branch, role, domain, type_, platform, ignore = row
        categories[table_name] = {
            "branch": branch,
            "role": role,
            "domain": domain,
            "type": type_,
            "platform": platform,
            "ignore": bool(ignore)
        }
    return categories


# RAW COLUMN LOADING
def load_raw_columns(conn):
    """
    Load raw columns per table from a_list_of_columns.

    Returns:
        dict: { table_name : [raw_column1, raw_column2, ...] }
    """
    sql = """
        SELECT table_name, column_name
        FROM a_list_of_columns
    """
    out = {}
    for table, col in conn.execute(sql).fetchall():
        out.setdefault(table, []).append(col)
    return out


# CONTEXT STRING BUILDER
def build_context_string(cat):
    """
    Build a context string from table categories.

    Example:
        navy.surface.frigate
    """
    parts = [
        cat.get("branch") or "",
        cat.get("domain") or "",
        cat.get("type") or "",
        cat.get("platform") or ""
    ]
    return ".".join(p for p in parts if p)


# CONTEXT-AWARE COLUMN MAPPING
def map_column(raw_col, base_map, context):
    """
    Determine the super-column for a raw column given context.
    For now:
        - use base mapping if available
        - TODO: add context-aware overrides
    Returns:
        (super_column, confidence, notes)
    """
    if raw_col in base_map:
        return base_map[raw_col], 1.0, "base mapping"

    # Placeholder for future context-aware logic
    return None, 0.0, "unmapped"


# MAIN PIPELINE FUNCTION
def build_contextual_column_mapping(conn, mapping_path=None):
    """
    Build a_column_mapping_contextual using:
        - raw columns
        - table categories
        - base ontology mapping
        - context strings

    Returns:
        dict: { (table_name, raw_column) : super_column }
    """
    if mapping_path is None:
        mapping_path = Path(__file__).resolve().parents[2] / "ontology" / "column_mapping.csv"

    base_map = load_base_column_mapping(mapping_path)
    categories = load_table_categories(conn)
    raw_cols = load_raw_columns(conn)

    cursor = conn.cursor()

    # Drop + recreate output table
    cursor.execute("DROP TABLE IF EXISTS a_column_mapping_contextual")
    cursor.execute("""
        CREATE TABLE a_column_mapping_contextual (
            table_name TEXT,
            raw_column TEXT,
            super_column TEXT,
            confidence REAL,
            notes TEXT
        )
    """)

    contextual_map = {}

    for table, cols in raw_cols.items():

        # Skip ignored tables
        if categories.get(table, {}).get("ignore", False):
            continue

        context = build_context_string(categories[table])

        for raw_col in cols:
            super_col, conf, notes = map_column(raw_col, base_map, context)

            cursor.execute(
                """
                INSERT INTO a_column_mapping_contextual
                (table_name, raw_column, super_column, confidence, notes)
                VALUES (?, ?, ?, ?, ?)
                """,
                (table, raw_col, super_col, conf, notes)
            )

            contextual_map[(table, raw_col)] = super_col

    conn.commit()
    print("Created a_column_mapping_contextual")

    return contextual_map
