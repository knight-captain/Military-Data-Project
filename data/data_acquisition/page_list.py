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
    soup = get_soup(MASTER_LIST)
    content = soup.find("div", {"class": "mw-parser-output"})

    links = []

    # Each country is now inside a <section>
    for section in content.find_all("section", recursive=False):

        # Find the country name
        heading = section.find("h2")
        if not heading:
            continue

        current_country = heading.get_text(strip=True)

        # Find the <ul> inside the same section
        ul = section.find("ul")
        if not ul:
            print(f"No links in {current_country}")
            continue

        # Extract links
        for a in ul.find_all("a", href=True):
            href = a["href"]

            # Accept both old and new formats
            if href.startswith("/wiki/") or href.startswith("//en.wikipedia.org/wiki/"):
                page_title = a.get_text(strip=True)
                full_url = urljoin(BASE_URL, href)
                links.append((current_country, page_title, full_url))

    print(f"Found {len(links)} links on MASTER_LIST")
    return links

