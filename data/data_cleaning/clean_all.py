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

from data.data_cleaning.clean_columns import clean_columns
from data.data_cleaning.clean_rows import clean_rows
from data.data_cleaning.clean_table import clean_table


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

    # Load table list
    tables = [
        row[0]
        for row in cursor.execute("SELECT table_name FROM a_meta_table").fetchall()
        if not row[0].startswith("a_")
    ]

    # Run cleaning steps
    for table in tables:
        # print(f"Cleaning {table}")
        clean_columns(table, conn=conn, db_path=cleaned_path)
        clean_rows(table, conn=conn, db_path=cleaned_path)
        clean_table(table, conn=conn, db_path=cleaned_path)

    conn.close()

    print(f"CLEANED DB created: {cleaned_path}")
    return cleaned_path
