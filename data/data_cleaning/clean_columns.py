import sqlite3
import pandas as pd
from data.data_cleaning.column_name_standardizer import column_name_standardizer
from data.data_cleaning.column_remove_superfluous import remove_superfluous_columns
from data.data_cleaning.column_split_doublewide import split_doublewide


def clean_columns(table_name: str, conn=None, db_path="data/db/military_equipment.db"):
    """
    Column-cleaning pipeline.
    Uses existing DB connection if provided; otherwise opens its own.
    """

    own_connection = False
    if conn is None:
        conn = sqlite3.connect(db_path)
        own_connection = True

    # Load table
    df = pd.read_sql_query(f"SELECT * FROM '{table_name}'", conn)

    # Step 2: check for double-wide columns
    dfs = split_doublewide(df)
    if len(dfs) > 1:
        # Stack the halves vertically
        df = pd.concat(dfs, ignore_index=True)

    # Step 1: Standardize column names
    df = column_name_standardizer(df)

    # Step 3: Remove superfluous columns, and skip the table if nothing is left
    df = remove_superfluous_columns(df)
    if df is None:
        print(f"Skipping table {table_name}: no meaningful columns")
        return  # do NOT continue cleaning

    # Save cleaned table
    df.to_sql(table_name, conn, if_exists="replace", index=False)

    if own_connection:
        conn.close()
        
    return df


# do I still need this?
if __name__ == "__main__":
    # Example usage:
    # python clean_columns.py my_table_name
    import sys
    if len(sys.argv) > 1:
        clean_columns(sys.argv[1])
        print(f"Column cleaning complete for {sys.argv[1]}")
