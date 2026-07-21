# import re

def get_a_meta_table(conn):
    cursor = conn.cursor()
    sql = """
        SELECT table_name, section_h2, section_h3, section_h4, country, url
        FROM a_meta_table
    """
    rows = cursor.execute(sql).fetchall()

    a_meta_table = {}

    for table_name, h2, h3, h4, country, url in rows:
        a_meta_table[table_name] = {
            "section_h2": h2,
            "section_h3": h3,
            "section_h4": h4,
            "country": country,
            "url": url
        }

    return a_meta_table

def get_a_meta_table_of_columns(conn):
    cursor = conn.cursor()
    sql = "SELECT * FROM a_meta_table_of_columns"
    rows = cursor.execute(sql).fetchall()

    # Get column names from cursor description
    colnames = [desc[0] for desc in cursor.description]

    # First column is table_name, rest are raw column names
    a_meta_table_of_columns = {}

    for row in rows:
        table_name = row[0]
        raw_cols = [col for col in row[1:] if col not in (None, "", "null")]

        a_meta_table_of_columns[table_name] = {
            "raw_cols": raw_cols
        }

    return a_meta_table_of_columns

def get_country_for_table(conn, table_name):
    cursor = conn.cursor()
    cursor.execute("SELECT country FROM a_meta_table WHERE table_name = ?", (table_name,))
    row = cursor.fetchone()
    return row[0].lower() if row else None

def build_mapping_table(conn, table_classes, contextual_mapping, super_cols_list):
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS a_mapping_table")

    # Build dynamic CREATE TABLE with one column per super_col
    cols_sql = ",\n".join([f'"{col}" TEXT' for col in super_cols_list])

    cursor.execute(f"""
        CREATE TABLE a_mapping_table (
            table_name TEXT,
            equipment_class TEXT,
            other_classes TEXT,
            confidence REAL,
            {cols_sql}
        )
    """)

    # Iterate over all tables in table_classes
    for table_name, class_info in table_classes.items():

        # Skip meta tables
        if table_name.startswith("a_"):
            continue

        # Extract classification info
        equipment_class = class_info.get("equipment_class")
        other_classes = ", ".join(class_info.get("other_classes", []))
        confidence = class_info.get("confidence")

        # Extract contextual mapping for this table
        mapping_for_table = contextual_mapping.get(table_name, {})

        # Convert lists to comma-separated strings
        row_values = []
        for col in super_cols_list:
            values = mapping_for_table.get(col, [])
            if not values:
                row_values.append(None)
            else:
                # Filter out None and convert everything to string
                clean_values = [str(v) for v in values if v is not None]
                row_values.append(", ".join(clean_values) if clean_values else None)


        cursor.execute(
            f"""
            INSERT INTO a_mapping_table
            (table_name, equipment_class, other_classes, confidence,
             {", ".join([f'"{c}"' for c in super_cols_list])})
            VALUES (?, ?, ?, ?, {", ".join(["?"] * len(super_cols_list))})
            """,
            [table_name, equipment_class, other_classes, confidence] + row_values
        )

    conn.commit()
    print("Created wide-format a_mapping_table")
