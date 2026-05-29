import sqlite3
import pandas as pd
from data.data_cleaning.column_name_standardizer import column_name_standardizer
from data.data_cleaning.column_remove_superfluous import remove_superfluous_columns
from data.data_cleaning.column_update_meta import update_meta_columns


def clean_columns(table_name: str, db_path="data/db/military_equipment.db"):
    """
    Standalone column-cleaning pipeline.
    Opens its own DB connection so it can be run independently.
    """

    conn = sqlite3.connect(db_path)

    # Load table
    df = pd.read_sql_query(f"SELECT * FROM '{table_name}'", conn)

    # Step 1: Standardize column names
    df = column_name_standardizer(df)

    # Step 2: Remove superfluous columns
    df = remove_superfluous_columns(df)

    # Step 3: Update meta-schema
    update_meta_columns(conn, table_name, df)

    # Save cleaned table
    df.to_sql(table_name, conn, if_exists="replace", index=False)

    conn.close()
    return df


if __name__ == "__main__":
    # Example usage:
    # python clean_columns.py my_table_name
    import sys
    if len(sys.argv) > 1:
        clean_columns(sys.argv[1])
        print(f"Column cleaning complete for {sys.argv[1]}")
