# build a_meta_table if it doesn't exist. Use SQL 
def ensure_meta_table(conn):
    '''builds a_meta_table that other functions will reference'''
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS a_meta_table (
            table_name TEXT PRIMARY KEY,
            country TEXT,
            url TEXT,
            table_idx INTEGER,
            section_h2 TEXT,
            section_h3 TEXT,
            section_h4 TEXT,
            section_title TEXT,
            scrape_timestamp TEXT
        )
    """)
    conn.commit()

# updates it: 
def insert_meta_row(conn, table_name, country, h2, h3, h4, section_title, table_idx, url):
    ensure_meta_table(conn)
    '''updates a_meta_table with meta-data from scrape
        - table_name
        - country
        - section_h2
        - section_h3
        - section_h4, 
        - section_title
        - table_index
        - source_url
        - current scrape_timestamp'''

    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO a_meta_table (
            table_name, country, section_h2, section_h3, section_h4, section_title, table_idx, url, scrape_timestamp
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (table_name, country, h2, h3, h4, section_title, table_idx, url))

    conn.commit()