from utils.get_country_for_table import get_country_for_table
from utils.normalization import normalize_text, strip_country_prefix

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
            print(f"new meta_col: {norm}")

        # Set the value for this table
        cursor.execute(
            f'UPDATE a_meta_table_of_columns SET "{norm}" = ? WHERE table_name = ?',
            (norm, table_name)
        )

    conn.commit()
