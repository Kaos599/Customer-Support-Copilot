#!/usr/bin/env python3
"""
Quick Setup Script for Atlan Customer Support Copilot

This is a simplified script I created for quickly setting up the vector database
with essential documentation. Perfect for getting started quickly or for testing.

Author: [Your Name]
Created: As part of the Atlan Customer Support Copilot project

Usage:
    python atlan_copilot/utils/quick_setup.py
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
import logging

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from atlan_copilot.utils.populate_vector_db import VectorDBPopulator
from atlan_copilot.utils.logging_config import setup_logging

async def quick_setup():
    """
    Quick setup process I designed for immediate use.
    This focuses on the most essential documentation sources.
    """
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Load environment variables
    dotenv_path = os.path.join(project_root, '.env')
    load_dotenv(dotenv_path=dotenv_path)
    
    logger.info("🚀 Quick Setup for Atlan Customer Support Copilot")
    logger.info("=" * 60)
    
    # Check for required environment variables
    required_vars = ['GOOGLE_API_KEY', 'QDRANT_API_KEY', 'QDRANT_HOST']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        logger.error("Please set up your .env file first!")
        return False
    
    try:
        populator = VectorDBPopulator()
        
        logger.info("📋 I'm setting up the vector database with essential sources:")
        logger.info("   • Local documentation (setup, overview, etc.)")
        logger.info("   • Sample from docs.atlan.com (limited pages for speed)")
        
        # Start with local docs (fastest)
        logger.info("\n📖 Step 1: Processing local documentation...")
        await populator.initialize_collections()
        
        local_chunks = await populator.scrape_and_process_source('local')
        if local_chunks:
            await populator.populate_collection(local_chunks, 'local_docs')
        
        # Add a small sample from docs.atlan.com
        logger.info("\n🌐 Step 2: Processing sample from docs.atlan.com...")
        docs_chunks = await populator.scrape_and_process_source('docs', max_pages=10)
        if docs_chunks:
            await populator.populate_collection(docs_chunks, 'atlan_docs')
        
        logger.info("\n✅ Quick setup completed successfully!")
        logger.info("🎯 Your copilot is ready for basic queries!")
        logger.info("\nNext steps:")
        logger.info("  • Run 'streamlit run atlan_copilot/app.py' to start the UI")
        logger.info("  • Use the full populate script for comprehensive coverage")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Quick setup failed: {e}")
        return False


def main():
    """Main function for the quick setup script."""
    print("🚀 Atlan Customer Support Copilot - Quick Setup")
    print("=" * 50)
    print("I've designed this script to get you started quickly!")
    print("It will populate your vector database with essential documentation.")
    print("")
    
    try:
        success = asyncio.run(quick_setup())
        if success:
            print("\n🎉 Setup complete! You're ready to go!")
            return 0
        else:
            print("\n💥 Setup failed. Please check the logs above.")
            return 1
    except KeyboardInterrupt:
        print("\n⚠️ Setup interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
