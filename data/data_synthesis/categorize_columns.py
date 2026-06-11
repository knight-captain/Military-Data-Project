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

from pathlib import Path
from utils import read_csv
from utils.normalization import normalize_text
from utils.safe_SQL_caller import q


#TODO: TEMP!!!!
def build_mapping_table(conn, table_categories, contextual_mapping, super_cols):
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS a_mapping_table")

    # Build dynamic CREATE TABLE with one column per super_col
    cols_sql = ",\n".join([f'"{col}" TEXT' for col in super_cols])

    cursor.execute(f"""
        CREATE TABLE a_mapping_table (
            table_name TEXT,
            classification TEXT,
            {cols_sql}
        )
    """)

    # Only process tables that categorize_tables approved
    table_names = [
        t for t in table_categories.keys()
        if not t.startswith("a_")
        and not table_categories[t].get("ignore", False)
    ]

    for table_name in table_names:

        # Classification string
        class_info = table_categories.get(table_name, {})
        classification = " | ".join(
            f"{k}:{v}" for k, v in class_info.items()
            if v not in (None, "", False)
        )

        # Build a dict: super_col → list of raw_cols
        mapping_for_table = {col: [] for col in super_cols}

        for (tbl, raw_col), (super_col, conf, notes) in contextual_mapping.items():
            if tbl == table_name:
                mapping_for_table[super_col].append(raw_col)

        # Convert lists to comma-separated strings
        row_values = [
            ", ".join(mapping_for_table[col]) if mapping_for_table[col] else None
            for col in super_cols
        ]

        cursor.execute(
            f"""
            INSERT INTO a_mapping_table
            (table_name, classification, {", ".join([f'"{c}"' for c in super_cols])})
            VALUES (?, ?, {", ".join(["?"] * len(super_cols))})
            """,
            [table_name, classification] + row_values
        )

    conn.commit()
    print("Created wide-format a_mapping_table")



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
        raw = normalize_text(raw)
        sup = normalize_text(sup)
        if raw:
            base_map[raw] = sup

    # Extract list of super columns (normalized)
    super_cols = sorted({col.strip().lower() for col in base_map.values()})

    cursor = conn.cursor()
    contextual_map = {}

    # Only process tables that categorize_tables approved
    table_names = [
        t for t in table_categories.keys()
        if not t.startswith("a_")
        and not table_categories[t].get("ignore", False)
    ]

    for table_name in table_names:
        # Build context dict (branch/role/domain/etc.)
        context = table_categories.get(table_name, {})

        # Get raw columns for this table from the actual schema
        raw_cols = cursor.execute(
            f"PRAGMA table_info({q(table_name)})"
        ).fetchall()
        raw_col_names = [r[1] for r in raw_cols]

        # Iterate through raw columns from this table
        for raw_col in raw_col_names:

            if raw_col not in base_map:
                print(f"{raw_col} from {table_name} not in column_mapping.csv")
                continue

            if raw_col == "JUNK":
                print(f"not adding to context map: {raw_col}")
                continue

            super_col, conf, notes = map_column(raw_col, base_map, context)
            normalized_super = normalize_text(super_col)
            contextual_map[(table_name, raw_col)] = (normalized_super, conf, notes)


    build_mapping_table(conn, table_categories, contextual_map, super_cols)

    return contextual_map, super_cols
