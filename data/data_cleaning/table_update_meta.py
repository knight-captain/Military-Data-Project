from utils.get_country_for_table import get_country_for_table
from utils.normalization import normalize_text, strip_country_prefix

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

    # For each table, check which wide columns it actually has
    rows = cursor.execute("SELECT * FROM a_meta_table_of_columns").fetchall()
    col_names = [desc[0] for desc in cursor.description]

    for row in rows:
        row_dict = dict(zip(col_names, row))
        table = row_dict["table_name"]

        for col in wide_cols:
            # If the wide meta-table has a non-null entry, the table had that column
            if row_dict.get(col) is not None:
                cursor.execute(
                    "INSERT INTO a_list_of_columns (table_name, column_name) VALUES (?, ?)",
                    (table, col)
                )


def update_meta_table(conn, table_name, df):
    cursor = conn.cursor()

    # Get country for this table
    country = get_country_for_table(conn, table_name)
    
    # Ensure table exists
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

    # Get existing columns (normalized)
    cursor.execute("PRAGMA table_info(a_meta_table_of_columns)")
    existing_cols = {normalize_text(row[1]) for row in cursor.fetchall()}

    # Add missing columns + update values
    for col in df.columns:
        # Normalize and strip country prefix 
        #TODO: need to add demonyms to a table to lookup
        norm = normalize_text(col)
        if country:
            norm = strip_country_prefix(norm, country)
            norm = normalize_text(norm)  # ensure normalized after stripping

        # Skip empty column names
        if not norm:
            continue

        # Add column if missing
        if norm not in existing_cols:
            cursor.execute(f'ALTER TABLE a_meta_table_of_columns ADD COLUMN "{norm}" TEXT')
            existing_cols.add(norm)
            # print(f"new meta_col: {norm}")

        # Set the value for this table
        cursor.execute(
            f'UPDATE a_meta_table_of_columns SET "{norm}" = ? WHERE table_name = ?',
            (norm, table_name)
        )
    
    build_list_of_columns(conn)

    conn.commit()
