"""
Builds a context-aware column mapping for every raw table.

Inputs:
    conn : sqlite3.Connection
    table_categories : dict {
        table_name : {
            branch, role, domain, group_1, group_2, platform, ignore
        }
    }

Reads:
    ontology/column_mapping.csv   (raw_col → super_col)
    a_meta_table_of_columns       (wide table: table_name + raw columns)

Outputs:
    contextual_map : dict {
        (table_name, raw_col) : (super_col, confidence, notes)
    }

    super_cols : sorted list of unique super columns
"""

import re
from pathlib import Path
from utils import read_csv


# Base column-mapping logic (context-aware later)
def map_column(raw_col, base_map, context):
    """
    Determine the super-column for a raw column given context.

    For now:
        - use base mapping if available
        - TODO: add context-aware overrides
        - TODO: add composite handling
        - TODO: compute confidence based on similar tables

    Returns:
        (super_col, confidence, notes)
    """

    # TODO: composite detection (e.g., "size")
    # TODO: flags in column_mapping.csv (future)

    if raw_col in base_map:
        return base_map[raw_col], 1.0, "base mapping"

    # Placeholder for future logic
    return None, 0.0, "unmapped"


# Main pipeline function
def build_contextual_column_mapping(conn, table_categories):
    """
    Build a context-aware mapping from raw columns to super columns.

    Returns:
        contextual_map : dict[(table_name, raw_col)] → (super_col, confidence, notes)
        super_cols     : sorted list of unique super columns
    """

    # Load raw → super mapping from CSV
    raw_map = read_csv.to_dict(
        Path(__file__).resolve().parents[2]
        / "ontology"
        / "column_mapping.csv"
    )

    # Build simple base mapping: raw_col → super_col
    base_map = {}
    for raw, sup in raw_map.items():
        raw = raw.strip()
        sup = sup.strip()
        if raw:
            base_map[raw] = sup

    # Extract list of super columns
    super_cols = sorted({col.strip().lower() for col in base_map.values()})

    # Load raw columns from a_meta_table_of_columns
    cursor = conn.cursor()
    sql = "SELECT * FROM a_meta_table_of_columns"
    table_rows = cursor.execute(sql).fetchall()

    # Column names (raw columns) come from the DB schema
    col_names = [desc[0] for desc in cursor.description]

    # table_name is the key; all other columns are raw columns
    raw_columns = [c for c in col_names if c != "table_name"]

    contextual_map = {}

    # Iterate through each table
    for row in table_rows:
        row_dict = dict(zip(col_names, row))
        table_name = row_dict["table_name"]

        # Skip meta tables (already filtered in categorize_tables)
        if table_name.startswith("a_"):
            continue

        # Skip ignored tables
        if table_name in table_categories:
            if table_categories[table_name].get("ignore", False):
                continue

        # Build context string (future use)
        context = table_categories.get(table_name, {})

        # Iterate through raw columns
        for raw_col in raw_columns:

            # Column is present if the cell is not NULL
            if row_dict[raw_col] is None:
                continue

            super_col, conf, notes = map_column(raw_col, base_map, context)

            contextual_map[(table_name, raw_col)] = (super_col, conf, notes)

    return contextual_map, super_cols
