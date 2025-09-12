import asyncio
import os
import sys
from typing import List, Dict, Any
from datetime import datetime, timezone

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ..scrapers.atlan_docs_scraper import AtlanDocsScraper
from ..scrapers.developer_docs_scraper import DeveloperDocsScraper
from ..scrapers.content_processor import ContentProcessor
from embeddings.vector_store_improved import VectorStore
from database.qdrant_client import QdrantDBClient
from utils.logging_config import setup_logging

logger = setup_logging()

async def populate_vector_database():
    """
    Main function to populate the vector database with scraped and processed content.
    """
    print("🚀 Starting vector database population process...")
    start_time = datetime.now(timezone.utc)

    try:
        # Initialize components
        print("🔧 Initializing components...")

        # Scrapers
        atlan_scraper = AtlanDocsScraper()
        dev_scraper = DeveloperDocsScraper()

        # Content processor with semantic chunking
        processor = ContentProcessor(
            chunk_size=1500,
            chunk_overlap=300,
            similarity_threshold=0.7  # Semantic similarity threshold
        )

        # Vector store with improved embedder
        vector_store = VectorStore(batch_size=10)  # Smaller batch size for safety

        print("✅ All components initialized successfully")

        # Step 1: Scrape content
        print("\n📄 Step 1: Scraping content from sources...")

        scraped_content = []

        # Scrape Atlan docs
        print("   📖 Scraping Atlan documentation...")
        try:
            atlan_content = atlan_scraper.scrape()
            scraped_content.extend(atlan_content)
            print(f"   ✅ Scraped {len(atlan_content)} items from Atlan docs")
        except Exception as e:
            print(f"   ⚠️  Failed to scrape Atlan docs: {e}")
            logger.error(f"Atlan docs scraping failed: {e}")

        # Scrape developer docs
        print("   📚 Scraping developer documentation...")
        try:
            dev_content = dev_scraper.scrape()
            scraped_content.extend(dev_content)
            print(f"   ✅ Scraped {len(dev_content)} items from developer docs")
        except Exception as e:
            print(f"   ⚠️  Failed to scrape developer docs: {e}")
            logger.error(f"Developer docs scraping failed: {e}")

        if not scraped_content:
            print("❌ No content was scraped. Aborting population.")
            return False

        print(f"📊 Total scraped content: {len(scraped_content)} items")

        # Step 2: Process content
        print("\n🔄 Step 2: Processing scraped content...")

        processed_documents = []
        processing_errors = 0

        try:
            # Process all content at once using the processor's process method
            processed_documents = processor.process(scraped_content)
            print(f"   ✅ Content processing complete")
            print(f"   � Processed {len(processed_documents)} document chunks")
        except Exception as e:
            processing_errors = len(scraped_content)
            logger.error(f"Failed to process content: {e}")
            print(f"   ❌ Content processing failed: {e}")

        if not processed_documents:
            print("❌ No documents were successfully processed. Aborting population.")
            return False

        # Step 3: Store in vector database
        print("\n💾 Step 3: Storing documents in vector database...")

        collection_name = "atlan_support_docs"
        success = await vector_store.upsert_documents(collection_name, processed_documents)

        if success:
            print("✅ Vector database population completed successfully!")
        else:
            print("❌ Vector database population failed.")
            return False

        # Step 4: Verification
        print("\n🔍 Step 4: Verifying database contents...")

        try:
            collection_info = await vector_store.qdrant_client.client.get_collection(collection_name)
            print(f"   📊 Collection '{collection_name}' now contains {collection_info.points_count} points")
            print(f"   🔍 Vector size: {collection_info.config.params.vectors.size}")
        except Exception as e:
            print(f"   ⚠️  Could not verify collection contents: {e}")

        # Calculate and display summary
        end_time = datetime.now(timezone.utc)
        duration = end_time - start_time

        # Count semantic vs fallback chunks
        semantic_chunks = sum(1 for chunk in processed_documents if chunk.get("payload", {}).get("chunk_method") == "semantic")
        fallback_chunks = len(processed_documents) - semantic_chunks

        print("\n🎉 Population Summary:")
        print(f"   ⏱️  Total duration: {duration}")
        print(f"   📄 Content scraped: {len(scraped_content)} items")
        print(f"   🔄 Documents processed: {len(processed_documents)} chunks")
        print(f"   🧠 Semantic chunks: {semantic_chunks}")
        print(f"   📝 Fallback chunks: {fallback_chunks}")
        print(f"   💾 Documents stored: {len(processed_documents)} vectors")
        print(f"   📊 Success rate: {(len(processed_documents) / len(scraped_content) * 100):.1f}%" if scraped_content else "0%")

        return True

    except Exception as e:
        print(f"❌ Critical error during vector database population: {e}")
        logger.error(f"Critical error: {e}", exc_info=True)
        return False

async def main():
    """
    Main entry point for the script.
    """
    print("🌟 Atlan Customer Support Copilot - Vector Database Population")
    print("=" * 60)

    # Check environment variables
    required_vars = ["GOOGLE_API_KEY", "QDRANT_API_KEY", "QDRANT_URL"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables and try again.")
        return

    print("✅ Environment variables verified")

    # Run the population process
    success = await populate_vector_database()

    if success:
        print("\n🎊 Vector database population completed successfully!")
        print("Your Atlan Customer Support Copilot is ready to use.")
    else:
        print("\n💥 Vector database population failed.")
        print("Check the logs for more details and try again.")

if __name__ == "__main__":
    asyncio.run(main())
