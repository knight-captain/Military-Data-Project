import sqlite3
import pandas as pd

from data.data_cleaning.rows_detect_type import detect_row_type
from data.data_cleaning.rows_propagate_sections import propagate_sections


def clean_rows(table_name: str, db_path="data/db/military_equipment.db"):
    """
    Standalone row-cleaning pipeline.
    Opens its own DB connection so it can be run independently.
    """

    conn = sqlite3.connect(db_path)

    df = pd.read_sql_query(f"SELECT * FROM '{table_name}'", conn)

    # Step 1: Detect row types
    section_rows, quantity_rows, empty_rows = detect_row_type(df)

    # Step 2: Propagate metadata downward
    df = propagate_sections(df, section_rows, quantity_rows)

    # Step 3: Delete empty rows
    if empty_rows:
        df = df.drop(empty_rows).reset_index(drop=True)

    # Save cleaned table
    df.to_sql(table_name, conn, if_exists="replace", index=False)

    conn.close()
    return df


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        clean_rows(sys.argv[1])
        print(f"Row cleaning complete for {sys.argv[1]}")
