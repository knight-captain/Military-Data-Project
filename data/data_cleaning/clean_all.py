"""
Runs Phase II cleaning on all raw tables:
- clean_columns
- clean_rows
- clean_table

This module loads its own table list from a_meta_table.
"""
import shutil
import sqlite3
from pathlib import Path
import pandas as pd

from data.data_cleaning.clean_columns import clean_columns
from data.data_cleaning.clean_rows import clean_rows
from data.data_cleaning.clean_table import clean_table
from data.data_cleaning.table_update_meta import (
    update_meta_table,
    drop_table,
    build_list_of_columns
)


def clean_all(conn=None, db_path=None):
    """
    Phase II: Cleaning.
    Takes a RAW db_path (and optionally an open connection to RAW),
    copies RAW → CLEANED, opens a connection to CLEANED,
    cleans all tables, and returns CLEANED path.
    """

    # Input validation
    if db_path is None:
        raise ValueError("db_path must be provided.")

    # Build CLEANED path & copy RAW → CLEANED
    cleaned_path = Path(str(db_path).replace("-RAW.db", "-CLEANED.db"))
    shutil.copy(db_path, cleaned_path)

    # Open connection to CLEANED
    conn = sqlite3.connect(cleaned_path)
    cursor = conn.cursor()

    # Load table list (skip meta tables)
    tables = [
        row[0]
        for row in cursor.execute("SELECT table_name FROM a_meta_table").fetchall()
        if not row[0].startswith("a_")
    ]

    # Run cleaning steps
    for table in tables:
        # Load table ONCE
        try:
            df = pd.read_sql_query(f"SELECT * FROM '{table}'", conn)
        except Exception:
            print(f"Skipping table {table}: could not load")
            continue

        # Run cleaning pipeline IN MEMORY
        df = clean_columns(df)
        df = clean_rows(df)
        df = clean_table(df)

        # If cleaning produced a table with no columns → drop it
        if df is None or df.shape[1] == 0:
            print(f"Dropping table {table}: no columns after cleaning")
            drop_table(conn, table)
            continue

        # Write cleaned table ONCE
        df.to_sql(table, conn, if_exists="replace", index=False)

        # Update metadata for this table
        update_meta_table(conn, table, df)

    # Rebuild list of columns AFTER all tables are processed
    build_list_of_columns(conn)

    conn.close()

    print(f"CLEANED DB created: {cleaned_path}")
    return cleaned_path
