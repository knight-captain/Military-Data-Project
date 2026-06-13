import pandas as pd
from utils.get_country_for_table import get_country_for_table
from utils.normalization import normalize_text, strip_country_prefix

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


def update_meta_table(conn, table_name, df):
    cursor = conn.cursor()

    # Ensure meta table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS a_meta_table_of_columns (
            table_name TEXT PRIMARY KEY
        )
    """)

    # Ensure row exists
    cursor.execute("""
        INSERT OR REPLACE INTO a_meta_table_of_columns (table_name)
        VALUES (?)
    """, (table_name,))

    # Get country for this table
    country = get_country_for_table(conn, table_name)

    # Get existing columns
    cursor.execute("PRAGMA table_info(a_meta_table_of_columns)")
    existing_cols = {normalize_text(row[1]) for row in cursor.fetchall()}

    # Add/update columns
    for col in df.columns:
        norm = normalize_text(col)
        if country:
            norm = strip_country_prefix(norm, country)
            norm = normalize_text(norm)

        if not norm:
            continue

        if norm not in existing_cols:
            cursor.execute(f'ALTER TABLE a_meta_table_of_columns ADD COLUMN "{norm}" TEXT')
            existing_cols.add(norm)

        cursor.execute(
            f'UPDATE a_meta_table_of_columns SET "{norm}" = ? WHERE table_name = ?',
            (norm, table_name)
        )

    conn.commit()


def build_list_of_columns(conn):
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS a_list_of_columns")
    cursor.execute("""
        CREATE TABLE a_list_of_columns (
            table_name TEXT,
            column_name TEXT
        )
    """)

    # Get all wide meta-table columns except table_name
    wide_cols = [
        row[1]
        for row in cursor.execute('PRAGMA table_info("a_meta_table_of_columns")').fetchall()
        if row[1] != "table_name"
    ]

    rows = cursor.execute("SELECT * FROM a_meta_table_of_columns").fetchall()
    col_names = [desc[0] for desc in cursor.description]

    for row in rows:
        row_dict = dict(zip(col_names, row))
        table = row_dict["table_name"]

        for col in wide_cols:
            if row_dict.get(col) is not None:
                cursor.execute(
                    "INSERT INTO a_list_of_columns (table_name, column_name) VALUES (?, ?)",
                    (table, col)
                )

    conn.commit()
