"""
Scraping and Embedding Script
"""

import asyncio
import argparse
import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path for module resolution
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ..scrapers.atlan_docs_scraper import AtlanDocsScraper
from ..scrapers.developer_docs_scraper import DeveloperDocsScraper
from ..scrapers.content_processor import ContentProcessor
from ..embeddings.vector_store import VectorStore

async def run_pipeline(source: str, max_pages: int):
    """
    I designed this function to run the full data ingestion pipeline for a single documentation source.
    This involves the complete process I created: scraping, processing, embedding, and storing the content.
    
    The pipeline I built handles each source independently and provides comprehensive error handling
    and progress reporting throughout the process.
    """
    print(f"\n{'='*50}")
    print(f"--- Starting Ingestion Pipeline for: {source.upper()} ---")
    print(f"{'='*50}")

    # 1. I select and run the appropriate scraper based on the source
    if source == 'docs':
        scraper = AtlanDocsScraper()
        collection_name = "atlan_docs"
    elif source == 'developer':
        scraper = DeveloperDocsScraper()
        collection_name = "atlan_developer"
    else:
        print(f"❌ Error: Unknown source '{source}'")
        return

    raw_docs = scraper.scrape(max_pages=max_pages)
    if not raw_docs:
        print(f"No documents were scraped for source '{source}'. Stopping pipeline.")
        return

    # 2. I process the raw HTML content into clean, chunked documents using my content processor
    processor = ContentProcessor()
    processed_chunks = processor.process(raw_docs)
    if not processed_chunks:
        print("No text chunks were produced after processing. Stopping pipeline.")
        return

    # 3. I embed and store the chunks in my vector store (Qdrant)
    qdrant_host = os.getenv("QDRANT_HOST")
    if not qdrant_host or "your-qdrant-cluster-url" in qdrant_host:
        print("\n---")
        print("⚠️  QDRANT_HOST is not set or is a placeholder.")
        print("Skipping embedding and vector store upload steps.")
        print("To complete the pipeline, please set a valid QDRANT_HOST in the .env file.")
        print("---")
    else:
        vector_store = VectorStore()
        await vector_store.upsert_documents(collection_name, processed_chunks)

    print(f"\n--- Ingestion Pipeline for {source.upper()} Complete ---")


async def main():
    """
    Main function to parse command-line arguments and run the ingestion pipeline(s).
    """
    print("--- Atlan Documentation Ingestion Script ---")

    # Load environment variables from .env file
    dotenv_path = os.path.join(project_root, '.env')
    load_dotenv(dotenv_path=dotenv_path)

    parser = argparse.ArgumentParser(description="Scrape and embed Atlan documentation into a vector store.")
    parser.add_argument(
        '--source',
        type=str,
        choices=['docs', 'developer', 'all'],
        default='all',
        help="The documentation source to scrape. Choose 'docs', 'developer', or 'all'."
    )
    parser.add_argument(
        '--max_pages',
        type=int,
        default=50,
        help="The maximum number of pages to scrape per source. Helps in limiting run time for tests."
    )
    args = parser.parse_args()

    sources_to_run = ['docs', 'developer'] if args.source == 'all' else [args.source]

    for source in sources_to_run:
        await run_pipeline(source, args.max_pages)


if __name__ == "__main__":
    asyncio.run(main())
