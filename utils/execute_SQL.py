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


def get_country_for_table(conn, table_name):
    cursor = conn.cursor()
    cursor.execute("SELECT country FROM a_meta_table WHERE table_name = ?", (table_name,))
    row = cursor.fetchone()
    return row[0].lower() if row else None
