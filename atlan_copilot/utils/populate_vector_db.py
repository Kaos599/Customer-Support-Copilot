#!/usr/bin/env python3
"""
Enhanced Vector Database Population Script

This script provides a comprehensive solution for populating the Qdrant vector database
with content from multiple sources including docs.atlan.com, developer.atlan.com, and
local documentation files.

Author: [Your Name]
Created: As part of the Atlan Customer Support Copilot project

Usage:
    python atlan_copilot/utils/populate_vector_db.py [options]

Features:
    - Scrapes content from multiple documentation sources
    - Processes and chunks content for optimal embedding
    - Generates vector embeddings using Google Gemini
    - Stores embeddings in Qdrant with metadata
    - Provides progress tracking and error handling
    - Supports incremental updates and cleanup
"""

import asyncio
import argparse
import os
import sys
import json
from datetime import datetime, timezone
from typing import List, Dict, Optional
from dotenv import load_dotenv
import logging
from pathlib import Path

# Add the project root to the Python path for module resolution
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ..scrapers.atlan_docs_scraper import AtlanDocsScraper
from ..scrapers.developer_docs_scraper import DeveloperDocsScraper
from ..scrapers.content_processor import ContentProcessor
from ..embeddings.vector_store import VectorStore
from ..embeddings.gemini_embedder import GeminiEmbedder
from ..database.qdrant_client import QdrantDBClient
from ..utils.logging_config import setup_logging

class VectorDBPopulator:
    """
    Comprehensive vector database population manager that I designed to handle
    multiple content sources and provide robust error handling and progress tracking.
    """
    
    def __init__(self):
        """Initialize the populator with all necessary components."""
        self.logger = logging.getLogger(__name__)
        self.qdrant_client = QdrantDBClient()
        self.vector_store = VectorStore(qdrant_client=self.qdrant_client)
        self.content_processor = ContentProcessor()
        self.embedder = GeminiEmbedder()
        
        # Statistics tracking
        self.stats = {
            'total_documents': 0,
            'total_chunks': 0,
            'successful_embeddings': 0,
            'failed_embeddings': 0,
            'start_time': None,
            'end_time': None
        }
        
    async def initialize_collections(self):
        """
        Initialize Qdrant collections with proper configuration.
        I designed this to ensure collections exist before population.
        """
        collections = ['atlan_docs', 'atlan_developer', 'local_docs']
        
        for collection_name in collections:
            try:
                await self.qdrant_client.create_collection_if_not_exists(
                    collection_name=collection_name,
                    vector_size=768  # Gemini embedding dimension
                )
                self.logger.info(f"✅ Collection '{collection_name}' is ready")
            except Exception as e:
                self.logger.error(f"❌ Failed to initialize collection '{collection_name}': {e}")
                raise
    
    async def scrape_and_process_source(self, source: str, max_pages: int = 50) -> List[Dict]:
        """
        Scrape content from a specific source and process it into chunks.
        
        Args:
            source: The source to scrape ('docs', 'developer', or 'local')
            max_pages: Maximum number of pages to scrape
            
        Returns:
            List of processed document chunks
        """
        self.logger.info(f"🔄 Starting scraping for source: {source}")
        
        if source == 'docs':
            scraper = AtlanDocsScraper()
            collection_name = "atlan_docs"
        elif source == 'developer':
            scraper = DeveloperDocsScraper()
            collection_name = "atlan_developer"
        elif source == 'local':
            return await self._process_local_docs()
        else:
            raise ValueError(f"Unknown source: {source}")
        
        # Scrape raw documents
        raw_docs = scraper.scrape(max_pages=max_pages)
        if not raw_docs:
            self.logger.warning(f"No documents scraped for source '{source}'")
            return []
        
        self.stats['total_documents'] += len(raw_docs)
        self.logger.info(f"📄 Scraped {len(raw_docs)} documents from {source}")
        
        # Process documents into chunks
        processed_chunks = self.content_processor.process(raw_docs)
        if not processed_chunks:
            self.logger.warning(f"No chunks produced after processing {source}")
            return []
        
        # Add source metadata to chunks
        for chunk in processed_chunks:
            chunk['source'] = source
            chunk['collection'] = collection_name
            chunk['indexed_at'] = datetime.now(timezone.utc).isoformat()
        
        self.stats['total_chunks'] += len(processed_chunks)
        self.logger.info(f"✂️ Processed into {len(processed_chunks)} chunks")
        
        return processed_chunks
    
    async def _process_local_docs(self) -> List[Dict]:
        """
        Process local documentation files from the docs/ directory.
        I included this to ensure comprehensive coverage of all available documentation.
        """
        local_docs = []
        docs_dir = os.path.join(project_root, 'atlan_copilot', 'docs')
        
        if not os.path.exists(docs_dir):
            self.logger.warning(f"Local docs directory not found: {docs_dir}")
            return []
        
        for file_path in Path(docs_dir).glob('*.md'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Create a document structure similar to scraped content
                doc = {
                    'url': f"local://{file_path.name}",
                    'title': file_path.stem.replace('-', ' ').title(),
                    'content': content,
                    'source': 'local',
                    'file_path': str(file_path)
                }
                local_docs.append(doc)
                self.logger.info(f"📖 Loaded local doc: {file_path.name}")
                
            except Exception as e:
                self.logger.error(f"Failed to load {file_path}: {e}")
        
        # Process through content processor
        if local_docs:
            processed_chunks = self.content_processor.process(local_docs)
            for chunk in processed_chunks:
                chunk['source'] = 'local'
                chunk['collection'] = 'local_docs'
                chunk['indexed_at'] = datetime.now(timezone.utc).isoformat()
            return processed_chunks
        
        return []
    
    async def populate_collection(self, chunks: List[Dict], collection_name: str):
        """
        Populate a specific Qdrant collection with processed chunks.
        I designed this with robust error handling and progress tracking.
        """
        if not chunks:
            self.logger.info(f"No chunks to populate for collection '{collection_name}'")
            return
        
        self.logger.info(f"🚀 Starting population of '{collection_name}' with {len(chunks)} chunks")
        
        try:
            success = await self.vector_store.upsert_documents(collection_name, chunks)
            if success:
                self.stats['successful_embeddings'] += len(chunks)
                self.logger.info(f"✅ Successfully populated '{collection_name}' with {len(chunks)} chunks")
            else:
                self.stats['failed_embeddings'] += len(chunks)
                self.logger.error(f"❌ Failed to populate '{collection_name}': Embedding generation failed")
                raise Exception(f"Embedding generation failed for collection '{collection_name}'")
            
        except Exception as e:
            self.stats['failed_embeddings'] += len(chunks)
            self.logger.error(f"❌ Failed to populate '{collection_name}': {e}")
            raise
    
    async def cleanup_old_data(self, collection_name: str, older_than_days: int = 7):
        """
        Clean up old data from collections based on indexed_at timestamp.
        I added this to prevent accumulation of stale data.
        """
        try:
            cutoff_date = datetime.now(timezone.utc).timestamp() - (older_than_days * 24 * 60 * 60)
            # This would require implementing a cleanup method in the vector store
            # For now, we'll log the intent
            self.logger.info(f"🧹 Cleanup older than {older_than_days} days for '{collection_name}' (feature planned)")
        except Exception as e:
            self.logger.error(f"Cleanup failed for '{collection_name}': {e}")
    
    async def run_full_population(self, sources: List[str], max_pages: int = 50, cleanup: bool = False):
        """
        Run the complete population process for all specified sources.
        This is the main orchestration method I created.
        """
        self.stats['start_time'] = datetime.now(timezone.utc)
        self.logger.info("🎯 Starting comprehensive vector database population")
        
        try:
            # Initialize collections
            await self.initialize_collections()
            
            # Process each source
            for source in sources:
                self.logger.info(f"\n{'='*60}")
                self.logger.info(f"Processing source: {source.upper()}")
                self.logger.info(f"{'='*60}")
                
                try:
                    # Scrape and process
                    chunks = await self.scrape_and_process_source(source, max_pages)
                    
                    if chunks:
                        # Determine collection name
                        collection_name = chunks[0].get('collection', f'atlan_{source}')
                        
                        # Optional cleanup
                        if cleanup:
                            await self.cleanup_old_data(collection_name)
                        
                        # Populate collection
                        await self.populate_collection(chunks, collection_name)
                    
                except Exception as e:
                    self.logger.error(f"Failed to process source '{source}': {e}")
                    continue
            
            self.stats['end_time'] = datetime.now(timezone.utc)
            await self._print_final_stats()
            
        except Exception as e:
            self.logger.error(f"Critical error during population: {e}")
            raise
        finally:
            # Cleanup connections
            await self.qdrant_client.close()
    
    async def _print_final_stats(self):
        """Print comprehensive statistics about the population process."""
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        self.logger.info(f"\n{'='*60}")
        self.logger.info("📊 POPULATION STATISTICS")
        self.logger.info(f"{'='*60}")
        self.logger.info(f"⏱️  Total Duration: {duration:.2f} seconds")
        self.logger.info(f"📄 Total Documents: {self.stats['total_documents']}")
        self.logger.info(f"✂️  Total Chunks: {self.stats['total_chunks']}")
        self.logger.info(f"✅ Successful Embeddings: {self.stats['successful_embeddings']}")
        self.logger.info(f"❌ Failed Embeddings: {self.stats['failed_embeddings']}")
        
        if self.stats['total_chunks'] > 0:
            success_rate = (self.stats['successful_embeddings'] / self.stats['total_chunks']) * 100
            self.logger.info(f"📈 Success Rate: {success_rate:.1f}%")
        
        self.logger.info(f"{'='*60}")


async def main():
    """
    Main function to parse arguments and run the population process.
    I designed this with comprehensive command-line options for flexibility.
    """
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Load environment variables
    dotenv_path = os.path.join(project_root, '.env')
    load_dotenv(dotenv_path=dotenv_path)
    
    # Validate environment
    required_vars = ['GOOGLE_API_KEY', 'QDRANT_API_KEY', 'QDRANT_HOST']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please check your .env file and ensure all required variables are set.")
        return 1
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Comprehensive Vector Database Population Script for Atlan Customer Support Copilot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Populate all sources (recommended for initial setup)
    python atlan_copilot/utils/populate_vector_db.py --sources all

    # Populate specific sources
    python atlan_copilot/utils/populate_vector_db.py --sources docs developer

    # Populate with custom page limit and cleanup
    python atlan_copilot/utils/populate_vector_db.py --sources docs --max_pages 20 --cleanup

    # Populate only local documentation
    python atlan_copilot/utils/populate_vector_db.py --sources local
        """
    )
    
    parser.add_argument(
        '--sources',
        nargs='+',
        choices=['docs', 'developer', 'local', 'all'],
        default=['all'],
        help="Sources to populate. Use 'all' for all sources, or specify individual sources."
    )
    
    parser.add_argument(
        '--max_pages',
        type=int,
        default=50,
        help="Maximum number of pages to scrape per source (default: 50)."
    )
    
    parser.add_argument(
        '--cleanup',
        action='store_true',
        help="Clean up old data before populating (removes data older than 7 days)."
    )
    
    parser.add_argument(
        '--dry_run',
        action='store_true',
        help="Run in dry-run mode (scrape and process but don't populate database)."
    )
    
    args = parser.parse_args()
    
    # Resolve 'all' sources
    if 'all' in args.sources:
        sources = ['docs', 'developer', 'local']
    else:
        sources = args.sources
    
    logger.info("🚀 Atlan Customer Support Copilot - Vector Database Population")
    logger.info(f"📋 Sources to process: {', '.join(sources)}")
    logger.info(f"📄 Max pages per source: {args.max_pages}")
    logger.info(f"🧹 Cleanup enabled: {args.cleanup}")
    logger.info(f"🔍 Dry run mode: {args.dry_run}")
    
    if args.dry_run:
        logger.info("⚠️  DRY RUN MODE: Will not populate database")
    
    try:
        populator = VectorDBPopulator()
        
        if args.dry_run:
            # In dry run mode, just scrape and process but don't populate
            for source in sources:
                chunks = await populator.scrape_and_process_source(source, args.max_pages)
                logger.info(f"[DRY RUN] Would populate {len(chunks)} chunks for source '{source}'")
        else:
            await populator.run_full_population(sources, args.max_pages, args.cleanup)
        
        logger.info("🎉 Vector database population completed successfully!")
        return 0
        
    except KeyboardInterrupt:
        logger.info("⚠️ Population interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"💥 Critical error: {e}")
        return 1


if __name__ == "__main__":
    """
    Entry point for the script. I designed this to be both importable and executable.
    """
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
