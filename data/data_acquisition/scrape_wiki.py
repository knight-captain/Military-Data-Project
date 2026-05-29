import os
import pandas as pd
import re
import requests
import sqlite3
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from io import StringIO

from data.utils.normalization import clean_html
from data.data_acquisition.build_meta_table import insert_meta_row

BASE_URL = "https://en.wikipedia.org"
MASTER_LIST = "https://en.wikipedia.org/wiki/Lists_of_currently_active_military_equipment_by_country"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; MilitaryDataScraper/1.0; +https://github.com/knight-captain)"
}

# -----------------------------
# Utility functions
# -----------------------------

def clean_name(name: str) -> str:
    """Convert a country/page name into a safe SQLite table name."""
    name = name.lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    name = re.sub(r"_+", "_", name)
    return name.strip("_")

def get_soup(url):
    """Fetch a URL and return a BeautifulSoup object."""
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    html = clean_html(response.text)
    return BeautifulSoup(html, "lxml")

def get_country_links():
    """Extract all relevant links from the master list page."""
    soup = get_soup(MASTER_LIST)
    content = soup.find("div", {"class": "mw-parser-output"})

    links = []
    current_country = None

    # Iterate through all elements in order
    for element in content.children:
        # skip whitespace, comment, etc.
        if not hasattr(element, "name"):
            continue

        # Detect <div class="mw-heading mw-heading2"><h2>Country</h2></div>. This is a sibpling of the actual <ul>
        if element.name == "div" and "mw-heading2" in element.get("class", []):
            h2 = element.find("h2")
            if h2:
                current_country = h2.get_text(strip=True)

        # Collect links under <ul>
        if element.name == "ul" and current_country:
            for a in element.find_all("a", href=True):
                href = a["href"]

                # Keep only internal article links, skip namespaces like Category:, File:, Help:, etc. 
                # this grabs urls that are aren't just "equipment", like "aircraft" & "ships", as well as "Branch" pages
                if href.startswith("/wiki/") and ":" not in href:
                    page_title = a.get_text(strip=True)
                    full_url = urljoin(BASE_URL, href)
                    links.append((current_country, page_title, full_url))

    return links

# -----------------------------
# Main functions
# -----------------------------

def extract_tables_from_page(url):
    """Extract all tables from a Wikipedia page with section headers."""
    soup = get_soup(url)
    tables = soup.find_all("table")

    extracted = []

    for idx, table in enumerate(tables):
        try:
            df = pd.read_html(StringIO(str(table)))[0]
        except Exception:
            continue

        #TODO: "or" instead? if it's a Navigation section, skip it, i.e.: <div role="navigation" class="navbox" ...>. These usually get associated with a "references" or "external links" section
        if table.find_parent("div", {"role": "navigation"}) is not None and table.find_parent("div", class_="navbox") is not None:
            continue

        # Find nearest section headers
        h2 = h3 = h4 = None
        prev = table

        while True:
            prev = prev.find_previous()
            if prev is None:
                break

            if prev.name == "h2" and h2 is None:
                h2 = prev.get_text(strip=True)
            elif prev.name == "h3" and h3 is None:
                h3 = prev.get_text(strip=True)
            elif prev.name == "h4" and h4 is None:
                h4 = prev.get_text(strip=True)

            # Stop early if we found all three
            if h2 and h3 and h4:
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
def scrape_all_to_sqlite(db_path="data/db/military_equipment.db"):
    """Scrape all equipment tables for all countries and save to SQLite."""
    conn = sqlite3.connect(db_path)
    country_links = get_country_links()

    print(f"Found {len(country_links)} links on MASTER_LIST")

    for country, page_title, url in country_links:
        try:
            tables = extract_tables_from_page(url)
            print(f"{country}: {len(tables)} tables found")
            if tables:
                save_to_sqlite(country, page_title, url, tables, conn)
        except Exception as e:
            print(f"Error scraping {country} ({url}): {e}")

        time.sleep(1)

    conn.close()


if __name__ == "__main__":
    default_path = "data/db/military_equipment.db" #<- will overwrite if run from here
    scrape_all_to_sqlite(db_path=default_path)
    print(f"Scrape complete. Data saved to {default_path}")

