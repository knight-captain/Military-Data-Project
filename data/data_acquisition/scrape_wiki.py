import pandas as pd
import sqlite3
import time
from bs4 import Tag, BeautifulSoup
from io import StringIO

import traceback

#Modules:
from data.data_acquisition.build_meta_table import insert_meta_row
from data.data_acquisition.get_soup import get_soup
from data.data_acquisition.header_detector import is_header_like, expanded_col_count
from utils.safe_SQL_caller import clean_name

# Main functions
def extract_tables_from_page(url):
    """Extract all tables from a Wikipedia page with section headers."""
    soup = get_soup(url)
    tables = soup.find_all("table")

    extracted = []

    for idx, table in enumerate(tables):
        html = str(table)

        # if it's a Navigation section, skip it, i.e.: <div role="navigation" class="navbox" ...>. These usually get associated with a "references" or "external links" section
        #FIXED: don't need the article's meta issues: those get ruled out when checking for empty cols & 1 col tables
        if table.find_parent("div", {"role": "navigation"}) is not None and table.find_parent("div", class_="navbox") is not None:
            continue

        # Detect proper headers, or a handful of folks that don't know proper html will ruin this whole project /jk
        rows = table.find_all("tr")

        # Compute max column count
        max_cols = max(expanded_col_count(tr) for tr in rows)

        # Find the first real header row
        header_row_index = None
        for i, tr in enumerate(rows):
            if is_header_like(tr, max_cols):
                header_row_index = i
                break

        # Fallback
        if header_row_index is None:
            print(f"fallback header in {rows[0]}")
            header_row_index = 0

        df = pd.read_html(StringIO(html), header=header_row_index)[0]


        # Find nearest section headers; but now with more hierarchy
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

        # Build a meaningful title
        section_title = "_".join([p for p in [h2, h3, h4] if p]) or "untitled"

        extracted.append({
            "index": idx,
            "h2": h2,
            "h3": h3,
            "h4": h4,
            "section_title": section_title,
            "data": df
        })

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

