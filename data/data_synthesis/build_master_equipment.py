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
            {col_defs}
        )
        """
    )

    # Get list of all cleaned tables
    table_rows = cursor.execute("SELECT table_name FROM a_meta_table").fetchall()
    all_tables = [r[0] for r in table_rows]

    # Filter out meta tables and ignored tables
    tables = [
        t for t in all_tables
        if not t.startswith("a_")
    ]

    # Process tables in chunks to avoid SQLite UNION limits
    for batch in chunked(tables, 50):

        for table_name in batch:

            # Get raw columns for this table
            raw_cols = cursor.execute(
                f"PRAGMA table_info({q(table_name)})"
            ).fetchall()

            raw_col_names = [r[1] for r in raw_cols]

            # Build SELECT for this table
            select_parts = [f"'{table_name}' AS table_name"]

            for super_col in super_cols:

                # Find raw columns that map to this super_col
                mapped_raw_cols = [
                    raw for raw in raw_col_names
                    if (table_name, raw) in contextual_mapping
                    and contextual_mapping[(table_name, raw)][0] == super_col
                ]

                if not mapped_raw_cols:
                    select_parts.append("NULL AS " + q(super_col))
                    continue

                # If multiple raw columns map to the same super_col,
                # choose the first (future: composite handling)
                raw = mapped_raw_cols[0]
                select_parts.append(f"{q(raw)} AS {q(super_col)}")

            select_sql = "SELECT " + ", ".join(select_parts) + f" FROM {q(table_name)}"

            # Insert into master table
            cursor.execute(
                f"INSERT INTO a_master_equipment {select_sql}"
            )

    conn.commit()
    print("Created a_master_equipment")
