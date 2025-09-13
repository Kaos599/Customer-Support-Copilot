#!/usr/bin/env python3
"""
Test script for the semantic chunker implementation.
"""

import asyncio
import os
import sys

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from scrapers.semantic_chunker import SemanticChunker

async def test_semantic_chunker():
    """Test the semantic chunker with sample text."""

    # Sample text about Atlan (customer data platform)
    sample_text = """
    Atlan is a modern data catalog and metadata management platform that helps organizations discover, understand, and govern their data assets. It provides a collaborative environment where data teams can work together to build a comprehensive understanding of their data landscape.

    The platform offers powerful search and discovery capabilities, allowing users to find relevant datasets quickly using natural language queries. Atlan's machine learning-powered suggestions help users understand data relationships and dependencies automatically.

    Key features include automated metadata discovery, data lineage tracking, and comprehensive data governance tools. The platform integrates seamlessly with popular data tools and platforms including Snowflake, BigQuery, Redshift, and many others.

    Atlan's collaborative features enable cross-functional teams to work together effectively. Data stewards can define and enforce data policies, while data consumers can easily access the information they need. The platform's intuitive interface makes it accessible to both technical and non-technical users.

    Security and compliance are core to Atlan's design. The platform offers robust access controls, audit trails, and compliance reporting features that help organizations meet their regulatory requirements.

    Atlan's API-first architecture enables deep integration with existing data infrastructure and workflows. Organizations can customize and extend the platform to meet their specific needs and requirements.
    """

    print("🧪 Testing Semantic Chunker")
    print("=" * 50)

    # Initialize the semantic chunker
    chunker = SemanticChunker(
        similarity_threshold=0.7,
        min_chunk_size=200,
        max_chunk_size=800
    )

    print(f"📝 Original text length: {len(sample_text)} characters")
    print(f"📊 Similarity threshold: {chunker.similarity_threshold}")
    print(f"📏 Min chunk size: {chunker.min_chunk_size} characters")
    print(f"📏 Max chunk size: {chunker.max_chunk_size} characters")
    print()

    # Test semantic chunking
    print("🔄 Processing text with semantic chunking...")
    chunks = await chunker.chunk_text(sample_text)

    print(f"✅ Created {len(chunks)} semantic chunks:")
    print()

    for i, chunk in enumerate(chunks, 1):
        print(f"📄 Chunk {i}:")
        print(f"   Length: {len(chunk)} characters")
        print(f"   Preview: {chunk[:150]}...")
        print()

    # Test with metadata
    print("🔄 Testing with metadata...")
    metadata = {
        "source": "atlan.com",
        "url": "https://atlan.com/features",
        "title": "Atlan Features Overview"
    }

    chunks_with_metadata = await chunker.chunk_text(sample_text, metadata)
    print(f"✅ Created {len(chunks_with_metadata)} chunks with metadata")

    # Test document processing
    print("\n🔄 Testing document processing...")
    documents = [{
        "url": "https://atlan.com/features",
        "title": "Atlan Features",
        "content": sample_text,
        "source": "atlan.com"
    }]

    processed_docs = chunker.process_documents(documents)
    print(f"✅ Processed {len(processed_docs)} document chunks")

    for i, doc in enumerate(processed_docs[:3]):  # Show first 3
        payload = doc.get("payload", {})
        print(f"📄 Document Chunk {i+1}:")
        print(f"   ID: {doc.get('id')}")
        print(f"   Method: {payload.get('chunk_method', 'unknown')}")
        print(f"   Content length: {len(payload.get('content', ''))}")
        print()

    print("🎉 Semantic chunker test completed!")

if __name__ == "__main__":
    asyncio.run(test_semantic_chunker())
