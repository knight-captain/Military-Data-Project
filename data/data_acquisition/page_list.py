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
    # content = soup.find("div", {"class": "mw-parser-output"})

    links = []

    # Find ALL <section> tags anywhere in the document
    sections = soup.find_all("section")

    # Each country is now inside a <section>
    for section in sections:

        # Find the country name
        heading = section.find("h2")
        if not heading:
            continue

        current_country = heading.get_text(strip=True)

        # Find ALL <li> tags inside the section (nested allowed)
        li_tags = section.find_all("li")
        if not li_tags:
            print(f"No links in {current_country}")
            continue

        # Extract links from each <li>
        for li in li_tags:
            a = li.find("a", href=True)
            if not a:
                continue

            href = a["href"]

            # Normalize absolute URLs to internal format
            if href.startswith("https://en.wikipedia.org/wiki/"):
                href = href.replace("https://en.wikipedia.org", "")
            elif href.startswith("//en.wikipedia.org/wiki/"):
                href = href.replace("//en.wikipedia.org", "")

            # Accept internal wiki article links only; both old and new formats
            # this changes sometimes: if you get "Found 0 links on MASTER_LIST" check the format here
            if href.startswith("/wiki/") and ":" not in href:
                page_title = a.get_text(strip=True)
                full_url = urljoin(BASE_URL, href)
                links.append((current_country, page_title, full_url))

    print(f"Found {len(links)} links on MASTER_LIST")
    return links

