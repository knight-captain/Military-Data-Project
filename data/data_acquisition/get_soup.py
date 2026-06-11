import requests
from bs4 import BeautifulSoup

from utils.normalization import clean_html

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; MilitaryDataScraper/1.0; +https://github.com/knight-captain)"
}

def get_soup(url):
    """Fetch a URL and return a BeautifulSoup object."""
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    
    html = response.text
    if not isinstance(html, str):
        print(f"response is not a not-string: {html}")
        html = str(html)

    html = clean_html(html)

    if not isinstance(html, str):
        print(f"HTML is not a not-string: {html}")
        html = str(html)

    return BeautifulSoup(html, "lxml")
