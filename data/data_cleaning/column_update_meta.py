import unicodedata
from data.utils.normalization import normalize_colname


def normalize_colname(name):
    if not isinstance(name, str):
        return name

    # Unicode normalization
    name = unicodedata.normalize("NFKC", name)

    # Strip whitespace
    name = name.strip()

    # Replace weird spaces with normal spaces
    name = name.replace("\u00A0", " ")  # NBSP
    name = name.replace("\u2009", " ")  # thin space
    name = name.replace("\u200A", " ")  # hair space
    name = name.replace("\u2002", " ")  # en space
    name = name.replace("\u2003", " ")  # em space
    name = name.replace("\u202F", " ")  # narrow NBSP

    # Lowercase for canonical form
    name = name.lower()

    return name


def update_meta_columns(conn, table_name, df):
    cursor = conn.cursor()

    # Ensure table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS a_meta_table_of_columns (
            table_name TEXT PRIMARY KEY
        )
    """)

    # Ensure row exists
    cursor.execute("""
        INSERT OR IGNORE INTO a_meta_table_of_columns (table_name)
        VALUES (?)
    """, (table_name,))

    # Get existing columns (normalized)
    cursor.execute("PRAGMA table_info(a_meta_table_of_columns)")
    existing_cols = {normalize_colname(row[1]) for row in cursor.fetchall()}

    # Add missing columns + update values
    for col in df.columns:
        norm = normalize_colname(col)

        # Add column if missing
        if norm not in existing_cols:
            cursor.execute(f'ALTER TABLE a_meta_table_of_columns ADD COLUMN "{norm}" TEXT')
            existing_cols.add(norm)
            print(f"Added column {norm}")

        # Set the value for this table
        cursor.execute(
            f'UPDATE a_meta_table_of_columns SET "{norm}" = ? WHERE table_name = ?',
            (norm, table_name)
        )

    conn.commit()
