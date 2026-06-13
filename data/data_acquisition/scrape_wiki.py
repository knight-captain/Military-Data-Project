import pandas as pd
import sqlite3
import time
from bs4 import Tag, BeautifulSoup
from io import StringIO

import traceback

#Modules:
from data.data_acquisition.build_meta_table import insert_meta_row
from data.data_acquisition.get_soup import get_soup
from data.data_acquisition.header_detector import header_detector
from data.data_acquisition.junk_detector import is_junk_table
from utils.safe_SQL_caller import clean_name

def find_nearest_section(table):
    h2 = h3 = h4 = None
    prev = table

    while True:
        prev = prev.find_previous()
        if prev is None:
            break

        if prev.name == "h4" and h4 is None:
            h4 = prev.get_text(strip=True)
        elif prev.name == "h3" and h3 is None:
            h3 = prev.get_text(strip=True)
        elif prev.name == "h2" and h2 is None:
            h2 = prev.get_text(strip=True)
            break

    return h2, h3, h4


# Main functions
def extract_tables_from_page(url):
    soup = get_soup(url)
    tables = soup.find_all("table")

    extracted = []
    kept_index = 0

    for table in tables:

        # 1. Find nearest section headers
        h2, h3, h4 = find_nearest_section(table)
        
        # 6. Build metadata/title
        section_title = "_".join([p for p in [h2, h3, h4] if p]) or "untitled"

        # 2. Extract metadata needed for junk detection
        classes = table.get("class", []) or []

        parent = table.find_parent()
        parent_classes = parent.get("class", []) if parent else []

        # optional: lineage extractor
        lineage = extract_lineage(table) if "extract_lineage" in globals() else None

        # Extract first row text
        first_row = table.find("tr")
        first_text = ""
        if first_row:
            cells = first_row.find_all(["th", "td"])
            if cells:
                first_text = cells[0].get_text(strip=True).lower()

        # 3. Junk filter
        if is_junk_table(
            table=table,
            section_title=section_title,
            lineage=lineage,
            first_text=first_text,
            classes=classes,
            parent_classes=parent_classes
        ):
            continue

        # 4. Header detection + row reordering
        html_reordered = header_detector(table)

        # 5. Parse with pandas
        try:
            df = pd.read_html(StringIO(html_reordered), header=0)[0]
        except Exception:
            continue

        extracted.append({
            "index": kept_index,
            "h2": h2,
            "h3": h3,
            "h4": h4,
            "section_title": section_title,
            "data": df
        })
        kept_index += 1

    return extracted



def save_to_sqlite(country, page_title, url, tables, conn):
    """Save all tables for a country/page into SQLite and update a_meta_table."""
    base_name = clean_name(country)

    for t in tables:
        idx = t["index"]
        df = t["data"]

        # Zero-pad table index to 2 digits
        idx_str = str(idx).zfill(2)

        #cleans and builds table title
        title_clean = clean_name(t["section_title"])
        table_name = f"{base_name}_table_{idx_str}_{title_clean}"

        # Save table & data
        df.to_sql(table_name, conn, if_exists="replace", index=False)

        # Insert metadata row in a_meta_table
        insert_meta_row(
            conn=conn,
            table_name=table_name,
            country=country,
            h2=t["h2"],
            h3=t["h3"],
            h4=t["h4"],
            section_title=t["section_title"],
            table_idx=idx,
            url=url
        )


# Main function: Opens DB, runs get_country_links, for each page returned from get_country_links it runs extract_tables_from_page and save_to_sqlite
def scrape_all_to_sqlite(db_path="data/db/military_equipment.db", links=None):
    """Scrape all equipment tables for all countries and save to SQLite."""
    conn = sqlite3.connect(db_path)
    country_links = links

    current_country = None
    for country, page_title, url in country_links:
        if current_country != country:
            print(f"Scraping pages for {country}")
            current_country = country
        
        try:
            tables = extract_tables_from_page(url)
            # print(f"{country}: {len(tables)} tables found")
            if tables:
                save_to_sqlite(country, page_title, url, tables, conn)
        except Exception as e:
            print(f"Error scraping {country} ({url}): {e}")
            traceback.print_exc()

        time.sleep(1)

    conn.close()


if __name__ == "__main__":
    default_path = "data/db/military_equipment.db" #<- will overwrite if run from here
    scrape_all_to_sqlite(db_path=default_path)
    print(f"Scrape complete. Data saved to {default_path}")

