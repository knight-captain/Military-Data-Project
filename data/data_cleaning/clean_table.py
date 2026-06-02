import pandas as pd

from data.data_cleaning.table_update_meta import update_meta_table

def load_table_as_df(conn, table_name):
    return pd.read_sql_query(f'SELECT * FROM "{table_name}"', conn)

def table_exists(conn, table_name):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name=?
    """, (table_name,))
    return cursor.fetchone() is not None

def drop_table(conn, table_name):
    cursor = conn.cursor()

    # Drop the actual table
    cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')

    # Delete from meta tables only if they exist
    if table_exists(conn, "a_meta_table"):
        cursor.execute("DELETE FROM a_meta_table WHERE table_name = ?", (table_name,))

    if table_exists(conn, "a_meta_table_of_columns"):
        cursor.execute("DELETE FROM a_meta_table_of_columns WHERE table_name = ?", (table_name,))

    conn.commit()


def clean_table(table_name, conn, db_path=None):
    # This doesn't need it's own connection handler, as it's for table-level cleanup, so it shouldn't just be called outside of pipeline.py

    # If table was already dropped, skip
    if not table_exists(conn, table_name):
        return None

    df = load_table_as_df(conn, table_name)

    # 1. Known junk tables
    junk_suffixes = [
        "_contents", "_references", "_external_links",
        "_see_also", "_notes", "_bibliography"
    ]
    if any(table_name.endswith(s) for s in junk_suffixes):
        drop_table(conn, table_name)
        return None

    # 2. No data rows
    if df.shape[0] == 0:
        drop_table(conn, table_name)
        return None

    # 3. Only header row
    if df.shape[0] == 1:
        drop_table(conn, table_name)
        return None

    # 4. Only one column
    if df.shape[1] <= 1:
        drop_table(conn, table_name)
        return None

    # 5. All columns are junk
    cols = [str(c).lower().strip() for c in df.columns]
    if all(c.isdigit() or c.startswith("unnamed") or c.startswith("col_") for c in cols):
        drop_table(conn, table_name)
        return None

    # Table survived → update metadata
    update_meta_table(conn, table_name, df)

    return df

if __name__ == "__main__":
    # Example usage:
    # python clean_columns.py my_table_name
    import sys
    if len(sys.argv) > 1:
        clean_table(sys.argv[1])
        print(f"Table cleanup complete for {sys.argv[1]}")