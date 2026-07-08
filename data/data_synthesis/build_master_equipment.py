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
from utils.normalization import normalize_text, esc_literal, esc_ident
from utils.safe_SQL_caller import q

def chunked(iterable, size):
    for i in range(0, len(iterable), size):
        yield iterable[i:i+size]


def build_master_equipment(conn, contextual_mapping, super_cols):
    """
    Build the canonical a_master_equipment table using the simplified
    contextual_mapping and super_cols list.

    contextual_mapping: dict
        (table_name, raw_col) -> super_col
    super_cols: list
        [super_col_1, super_col_2, ...]
    """

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
    tables = [t for t in all_tables if not t.startswith("a_")]

    # Process tables in chunks to avoid SQLite UNION limits
    for batch in chunked(tables, 50):

        for table_name in batch:

            # Get raw columns for this table & normalize
            raw_cols = cursor.execute(
                f"PRAGMA table_info({q(table_name)})"
            ).fetchall()
            raw_col_names = [normalize_text(r[1]) for r in raw_cols]

            # Prepare mapping for this table
            mapping_for_table = {col: [] for col in super_cols}

            for raw_col in raw_col_names:
                base = re.sub(r'\.\d+$', '', raw_col) #TODO: is this messing with normaizaiton?
                key = (table_name, base)

                if key in contextual_mapping:
                    super_col = contextual_mapping[key]
                    mapping_for_table[super_col].append(raw_col)

            # Build SELECT for this table
            url = table_to_url.get(table_name)
            select_parts = [
                f"'{esc_literal(table_name)}' AS table_name",
                f"'{esc_literal(url)}' AS url"
            ]

            for super_col in super_cols:
                raw_list = mapping_for_table[super_col]
                unique_raws = list(dict.fromkeys(raw_list))

                if len(unique_raws) == 0:
                    select_parts.append(f"NULL AS \"{esc_ident(super_col)}\"")

                elif len(unique_raws) == 1:
                    raw = unique_raws[0]
                    select_parts.append(
                        f'"{esc_ident(raw)}" AS "{esc_ident(super_col)}"'
                    )

                else:
                    # Merge multiple raw columns
                    expr = f'"{esc_ident(unique_raws[0])}"'
                    for r in unique_raws[1:]:
                        expr = (
                            f"CASE WHEN {expr} = \"{esc_ident(r)}\" "
                            f"THEN {expr} ELSE {expr} || '; ' || \"{esc_ident(r)}\" END"
                        )

                    select_parts.append(f"({expr}) AS \"{esc_ident(super_col)}\"")

            select_sql = (
                "SELECT " + ", ".join(select_parts) +
                f" FROM \"{esc_ident(table_name)}\""
            )

            cursor.execute(f"INSERT INTO a_master_equipment {select_sql}")

            # Drop cleaned table now that it's merged
            cursor.execute(f"DROP TABLE IF EXISTS {q(table_name)}")

    conn.commit()
    cursor.execute("VACUUM")
    print("Created a_master_equipment and cleaned up after myself.")

