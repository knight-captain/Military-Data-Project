def get_country_for_table(conn, table_name):
    cursor = conn.cursor()
    cursor.execute("SELECT country FROM a_meta_table WHERE table_name = ?", (table_name,))
    row = cursor.fetchone()
    return row[0].lower() if row else None
