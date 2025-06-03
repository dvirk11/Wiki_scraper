from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from bs4.element import Tag
import requests


def parse_cell_text(cell: Tag) -> List[str]:
    """
    Extract and clean comma-separated text values from a table cell,
    removing footnotes and line breaks.

    Args:
        cell (Tag): The table cell (td or th) to parse.

    Returns:
        List[str]: A list of cleaned text entries.
    """
    for sup in cell.find_all("sup"):
        sup.decompose()

    parts: List[str] = []
    for element in cell.contents:
        if isinstance(element, str):
            parts.extend([p.strip() for p in element.split(",") if p.strip()])
        elif element.name == "br":
            continue
        else:
            parts.extend([p.strip() for p in element.get_text().split(",") if p.strip()])
    return parts


class CollateralAdjectiveScraper:
    """
    A scraper for extracting collateral adjectives from the Wikipedia page
    'List of animal names'. Returns a mapping from adjectives to associated animals.
    """

    WIKI_URL = "https://en.wikipedia.org/wiki/List_of_animal_names"

    def __init__(self):
        self.session = requests.Session()

    def fetch_html(self) -> BeautifulSoup:
        """
        Fetch the HTML content of the Wikipedia page.

        Returns:
            BeautifulSoup: Parsed HTML of the Wikipedia page.

        Raises:
            Exception: If the page could not be retrieved.
        """
        response = self.session.get(self.WIKI_URL, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")

    def get_collateral_adjectives_map(self) -> Dict[str, List[Dict[str, Optional[str]]]]:
        """
        Parse the Wikipedia table and return a mapping of collateral adjectives to animals.

        Returns:
            Dict[str, List[Dict[str, Optional[str]]]]:
                Dictionary where each key is a collateral adjective,
                and the value is a list of dictionaries with 'name' and 'wiki_url' keys.

        Raises:
            Exception: If the expected table or columns are not found.
        """
        soup = self.fetch_html()
        tables = soup.find_all("table", class_="wikitable")

        if len(tables) < 2:
            raise Exception("Couldn't find the target table with collateral adjectives.")

        table = tables[1]
        headers = [th.text.strip().lower() for th in table.find_all("th")]

        try:
            name_idx = headers.index("animal")
            adjective_idx = headers.index("collateral adjective")
        except ValueError:
            raise Exception(f"Could not find required columns. Found headers: {headers}")

        mapping: Dict[str, List[Dict[str, Optional[str]]]] = {}

        for row in table.find_all("tr")[1:]:
            cells = row.find_all(["td", "th"])
            if len(cells) <= max(name_idx, adjective_idx):
                continue

            name_cell = cells[name_idx]
            adj_cell = cells[adjective_idx]

            link_tag = name_cell.find("a")
            href = f"https://en.wikipedia.org{link_tag.get('href')}" if link_tag else None
            name_text = (link_tag.get_text() if link_tag else name_cell.get_text()).strip()
            name_text = name_text.split(" (")[0]

            adjectives = [adj.lower() for adj in parse_cell_text(adj_cell)]

            for adj in adjectives:
                if adj not in mapping:
                    mapping[adj] = []

                mapping[adj].append({
                    "name": name_text,
                    "wiki_url": href
                })

        return mapping
