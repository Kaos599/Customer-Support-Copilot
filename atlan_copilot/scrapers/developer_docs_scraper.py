from urllib.parse import urljoin, urlparse
from typing import List, Dict, Set
import os
import sys

from .base_scraper import BaseScraper

class DeveloperDocsScraper(BaseScraper):
    """
    A scraper specifically for the Atlan developer documentation site (developer.atlan.com).
    It uses the same logic as the main docs scraper, assuming a similar site structure.
    """
    def __init__(self):
        super().__init__("https://developer.atlan.com")

    def scrape(self, max_pages: int = 50) -> List[Dict[str, str]]:
        """
        Crawls the Atlan developer documentation site starting from the base URL.

        Args:
            max_pages: The maximum number of pages to scrape.

        Returns:
            A list of dictionaries, where each dictionary contains the URL, title,
            and extracted text content of a scraped page.
        """
        print(f"Starting scrape of {self.base_url}...")
        urls_to_visit: List[str] = [self.base_url]
        visited_urls: Set[str] = set()
        pages_content: List[Dict[str, str]] = []

        while urls_to_visit and len(pages_content) < max_pages:
            current_url = urls_to_visit.pop(0)
            if current_url in visited_urls:
                continue

            print(f"Scraping: {current_url} ({len(pages_content) + 1}/{max_pages})")
            visited_urls.add(current_url)

            soup = self.fetch_page(current_url)
            if not soup:
                continue

            # --- Site-specific Logic ---
            main_content = soup.find("main")
            if not main_content:
                main_content = soup.find("article")

            if main_content:
                content_text = main_content.get_text(separator=' ', strip=True)
                page_title = soup.title.string.strip() if soup.title else "No Title"

                pages_content.append({
                    "url": current_url,
                    "title": page_title,
                    "content": content_text,
                    "source": urlparse(self.base_url).netloc
                })

                # Find all valid links on the page to continue crawling
                for link in main_content.find_all("a", href=True):
                    href = link["href"]
                    full_url = urljoin(self.base_url, href)

                    parsed_url = urlparse(full_url)
                    clean_url = parsed_url._replace(query="", fragment="").geturl()

                    if (parsed_url.netloc == urlparse(self.base_url).netloc and
                        clean_url not in visited_urls and
                        not any(clean_url.endswith(ext) for ext in ['.pdf', '.zip', '.png', '.jpg', '.svg'])):
                        urls_to_visit.append(clean_url)
            else:
                print(f"Warning: Could not find <main> or <article> content for {current_url}")

        print(f"\nScraping complete. Found content from {len(pages_content)} pages.")
        return pages_content
