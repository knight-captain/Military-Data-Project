import re
from utils.normalization import normalize_text
from utils.safe_SQL_caller import q

#TODO: TEMP! (not necessary, but useful) IDK: maybe I'll just have build_master_equip work off of this?
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

        for (tbl, raw_col), (super_col) in contextual_mapping.items():
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

def recategorize_ontologically(conn, table_categories, super_col_map):
    """
    Step 3: Ontological Re-Categorization (expanded skeleton)

    This version:
      - builds contextual_mapping from PRAGMA + super_col_map
      - strips conf/notes
      - builds a_mapping_table
      - returns contextual_mapping + super_cols
    """

    cursor = conn.cursor()

    # --- 1. Build contextual_mapping ---
    contextual_mapping = {}
    table_names = [
        t for t in table_categories.keys()
        if not t.startswith("a_")
        and not table_categories[t].get("ignore", False)
    ]

    for table_name in table_names:
        context = table_categories.get(table_name, {})

        raw_cols = cursor.execute(
            f"PRAGMA table_info({q(table_name)})"
        ).fetchall()
        raw_col_names = [normalize_text(r[1]) for r in raw_cols]

        for raw_col in raw_col_names:
            base = re.sub(r'\.\d+$', '', raw_col)

            if base not in super_col_map:
                continue

            super_col = super_col_map[base]
            contextual_mapping[(table_name, raw_col)] = super_col

    # --- 2. Build super_cols list ---
    super_cols = sorted(set(super_col_map.values()))

    # --- 3. Build a_mapping_table ---
    build_mapping_table(conn, table_categories, contextual_mapping, super_cols)

    return contextual_mapping, super_cols
