import sqlite3

def update_meta_columns(conn, table_name, df):
    """
    Updates a_meta_columns with the schema of this table.
    Creates the table if it doesn't exist.
    """

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS a_meta_table_of_columns (
            table_name TEXT,
            column_name TEXT,
            column_index INTEGER
        )
    """)

    # Remove old entries for this table
    cursor.execute("DELETE FROM a_meta_table_of_columns WHERE table_name = ?", (table_name,))

    # Insert new schema
    for idx, col in enumerate(df.columns):
        cursor.execute(
            "INSERT INTO a_meta_table_of_columns (table_name, column_name, column_index) VALUES (?, ?, ?)",
            (table_name, col, idx)
        )

    conn.commit()
