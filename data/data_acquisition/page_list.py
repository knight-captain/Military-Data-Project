import csv
import os
from bs4 import Tag, BeautifulSoup
from data.data_acquisition.get_soup import get_soup
from urllib.parse import urljoin

BASE_URL = "https://en.wikipedia.org"
MASTER_LIST = "https://en.wikipedia.org/wiki/Lists_of_currently_active_military_equipment_by_country"

def edge_list():
    path = os.path.join("ontology", "edge_cases.csv")
    links = []

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            country = row["country_name"].strip()
            title = row[" page_title"].strip()
            url = row[" url"].strip()
            links.append((country, title, url))

    return links

def get_links():
    """Extract all relevant links from the master list page."""
    soup = get_soup(MASTER_LIST)
    content = soup.find("div", {"class": "mw-parser-output"})

    links = []
    current_country = None

    for element in content.children:

        # Skip whitespace, comments, NavigableString, etc.
        if not isinstance(element, Tag):
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

                # Keep only internal article links, skip namespaces
                # this grabs urls that are aren't just "equipment", like "aircraft" & "ships", as well as "Branch" pages
                if href.startswith("/wiki/") and ":" not in href:
                    page_title = a.get_text(strip=True)
                    full_url = urljoin(BASE_URL, href)
                    links.append((current_country, page_title, full_url))

    print(f"Found {len(links)} links on MASTER_LIST")
    return links
