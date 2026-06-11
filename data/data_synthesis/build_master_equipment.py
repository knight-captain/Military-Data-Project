"""
Creates a unified a_master_equipment table by mapping raw columns
from each cleaned equipment table into a canonical super-column schema.

Inputs:
    conn                : sqlite3.Connection
    contextual_mapping  : dict[(table_name, raw_col)] → (super_col, confidence, notes)
    super_cols          : list of canonical super columns

Reads:
    a_meta_table_of_columns   (to know which raw columns each table has)
    all cleaned tables        (to extract actual values)

Writes:
    a_master_equipment        (final unified table)
"""

import re
from utils.normalization import normalize_text
from pathlib import Path
from utils.safe_SQL_caller import q, ql


def chunked(iterable, size):
    for i in range(0, len(iterable), size):
        yield iterable[i:i+size]


def build_master_equipment(conn, contextual_mapping, super_cols):
    cursor = conn.cursor()

    # Drop old master table
    cursor.execute("DROP TABLE IF EXISTS a_master_equipment")

    # Create empty master table with canonical schema
    col_defs = ", ".join(f"{q(col)} TEXT" for col in super_cols)

    cursor.execute(
        f"""
        CREATE TABLE a_master_equipment (
            table_name TEXT,
            url TEXT,
            {col_defs}
        )
        """
    )

    # Get list of all cleaned tables
    table_rows = cursor.execute("SELECT table_name FROM a_meta_table").fetchall()
    all_tables = [r[0] for r in table_rows]

    meta_rows = cursor.execute("SELECT table_name, url FROM a_meta_table").fetchall()
    table_to_url = {t: url for t, url in meta_rows}

    # Filter out meta tables and ignored tables
    tables = [
        t for t in all_tables
        if not t.startswith("a_")
    ]

    # Process tables in chunks to avoid SQLite UNION limits
    for batch in chunked(tables, 50):

        for table_name in batch:

            # Get raw columns for this table & normalize
            raw_cols = cursor.execute(
                f"PRAGMA table_info({q(table_name)})"
            ).fetchall()
            raw_col_names = [normalize_text(r[1]) for r in raw_cols]
            
            mapping_for_table = {col: [] for col in super_cols}

            for raw_col in raw_col_names:
                base = re.sub(r'\.\d+$', '', raw_col) #pull any ".x" off of raw_cols that got panda-ed in scrape
                key = (table_name, base)

                if key in contextual_mapping:
                    super_col, conf, notes = contextual_mapping[key]
                    mapping_for_table[super_col].append(raw_col)


            # Build SELECT for this table
            url = table_to_url.get(table_name)
            select_parts = [
                f"'{table_name}' AS table_name",
                f"'{url}' AS url"
            ]

            for super_col in super_cols:
                raw_list = mapping_for_table[super_col]
                # Deduplicate column names while preserving order
                unique_raws = list(dict.fromkeys(raw_list))

                if len(unique_raws) == 0:
                    select_parts.append(f"NULL AS {q(super_col)}")

                elif len(unique_raws) == 1:
                    raw = unique_raws[0]
                    select_parts.append(f"{q(raw)} AS {q(super_col)}")

                else:
                    # Build SQL that merges values but removes duplicates
                    # Example output:
                    # CASE WHEN col1 = col2 THEN col1 ELSE col1 || '; ' || col2 END
                    expr = q(unique_raws[0])
                    for r in unique_raws[1:]:
                        expr = f"CASE WHEN {expr} = {q(r)} THEN {expr} ELSE {expr} || '; ' || {q(r)} END"

                    select_parts.append(f"({expr}) AS {q(super_col)}")


            select_sql = "SELECT " + ", ".join(select_parts) + f" FROM {q(table_name)}"

            # Insert into master table
            cursor.execute(
                f"INSERT INTO a_master_equipment {select_sql}"
            )

    conn.commit()
    print("Created a_master_equipment")
