import sqlite3
import pandas as pd

from data.data_cleaning.rows_detect_type import detect_row_type
from data.data_cleaning.rows_propagate_sections import propagate_sections
from data.data_cleaning.column_update_meta import update_meta_columns


def clean_rows(table_name: str, conn=None, db_path="data/db/military_equipment.db"):
    """
    Row-cleaning pipeline.
    Uses existing DB connection if provided; otherwise opens its own.
    """

    own_connection = False
    if conn is None:
        conn = sqlite3.connect(db_path)
        own_connection = True

    df = pd.read_sql_query(f"SELECT * FROM '{table_name}'", conn)

    # Step 1: Detect row types
    section_rows, quantity_rows, empty_rows = detect_row_type(df)

    # Step 2: Propagate metadata downward
    df = propagate_sections(df, section_rows, quantity_rows, empty_rows)

    # Step 3: Delete empty rows -> move into propagate_sections

    # Step 4: refresh column name standardizer
    update_meta_columns(conn, table_name, df)

    # Save cleaned table
    df.to_sql(table_name, conn, if_exists="replace", index=False)

    if own_connection:
        conn.close()

    return df


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        clean_rows(sys.argv[1])
        print(f"Row cleaning complete for {sys.argv[1]}")
