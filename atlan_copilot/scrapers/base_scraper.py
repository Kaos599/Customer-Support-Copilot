import requests
from bs4 import BeautifulSoup
from typing import Optional

class BaseScraper:
    """
    A base class for web scrapers. Provides common functionality for fetching
    and parsing web pages.
    """
    def __init__(self, base_url: str):
        """
        Initializes the scraper with a base URL.

        Args:
            base_url: The starting URL for the scrape.
        """
        self.base_url = base_url
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetches the content of a single URL and returns a BeautifulSoup object.

        Args:
            url: The URL of the page to fetch.

        Returns:
            A BeautifulSoup object representing the parsed page, or None if fetching fails.
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
            return BeautifulSoup(response.content, "html.parser")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching URL {url}: {e}")
            return None
