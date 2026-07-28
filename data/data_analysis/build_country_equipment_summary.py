import sqlite3

def build_country_equipment_summary(conn):
    """
    Phase V: Analyze
    Build an aggregated table showing total quantities
    by country and equipment subtype.
    """
    cur = conn.cursor()

    # Drop old version if exists
    cur.execute("DROP TABLE IF EXISTS country_equipment_summary;")

    # Build new aggregated table
    cur.execute("""
        CREATE TABLE country_equipment_summary AS
        SELECT
            country,
            class_path,
            sub_class,
            SUM(quantity_clean) AS total_quantity
        FROM a_canonical_equipment
        WHERE (quantity_clean IS NOT NULL AND class_path IS NOT NULL AND sub_class IS NOT "Equipment")
        GROUP BY country, class_path, sub_class
        ORDER BY country, class_path, sub_class;
    """)

    conn.commit()

    print("Built Phase V table: country_equipment_summary")
