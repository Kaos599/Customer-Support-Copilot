import asyncio
import os
import sys
from datetime import datetime, timezone

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from embeddings.gemini_embedder_improved import GeminiEmbedder
from embeddings.vector_store_improved import VectorStore
from database.qdrant_client import QdrantDBClient

async def test_improved_components():
    """
    Test the improved embedder and vector store components.
    """
    print("🧪 Testing improved components...")
    print("=" * 50)

    # Test 1: Initialize components
    print("\n1️⃣ Testing component initialization...")
    try:
        embedder = GeminiEmbedder()
        vector_store = VectorStore(batch_size=5)
        print("✅ Components initialized successfully")
    except Exception as e:
        print(f"❌ Component initialization failed: {e}")
        return False

    # Test 2: Test embedding generation with rate limiting
    print("\n2️⃣ Testing embedding generation...")
    test_texts = [
        "This is a test document about Atlan's data catalog features.",
        "Another test document discussing data governance and metadata management.",
        "A third document about customer support and troubleshooting."
    ]

    try:
        print(f"   Generating embeddings for {len(test_texts)} test documents...")
        embeddings = embedder.embed_documents(test_texts)

        if embeddings and len(embeddings) == len(test_texts):
            print(f"✅ Successfully generated {len(embeddings)} embeddings")
            print(f"   Embedding dimensions: {len(embeddings[0])}")
        else:
            print(f"❌ Embedding generation failed. Expected {len(test_texts)}, got {len(embeddings) if embeddings else 0}")
            return False
    except Exception as e:
        print(f"❌ Embedding generation error: {e}")
        return False

    # Test 3: Test vector store operations
    print("\n3️⃣ Testing vector store operations...")

    # Create test documents
    test_documents = [
        {
            "id": f"test_doc_{i+1}",
            "payload": {
                "content": text,
                "title": f"Test Document {i+1}",
                "source": "test_source",
                "url": f"https://example.com/test{i+1}",
                "chunk_index": 0,
                "total_chunks": 1
            }
        }
        for i, text in enumerate(test_texts)
    ]

    collection_name = "test_collection"

    try:
        print(f"   Upserting {len(test_documents)} test documents...")
        success = await vector_store.upsert_documents(collection_name, test_documents)

        if success:
            print("✅ Vector store operations successful")
        else:
            print("❌ Vector store operations failed")
            return False
    except Exception as e:
        print(f"❌ Vector store error: {e}")
        return False

    # Test 4: Verify collection contents
    print("\n4️⃣ Verifying collection contents...")
    try:
        collection_info = await vector_store.qdrant_client.get_collection_info(collection_name)
        print(f"✅ Collection '{collection_name}' contains {collection_info.points_count} points")
        print(f"   Vector size: {collection_info.config.params.vectors.size}")
    except Exception as e:
        print(f"❌ Could not verify collection: {e}")
        return False

    # Test 5: Test search functionality
    print("\n5️⃣ Testing search functionality...")
    try:
        query_text = "data catalog features"
        query_embedding = embedder.embed_documents([query_text])[0]

        search_results = await vector_store.qdrant_client.search_points(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=3
        )

        if search_results:
            print(f"✅ Search successful, found {len(search_results)} results")
            for i, result in enumerate(search_results[:2]):  # Show first 2 results
                print(f"   Result {i+1}: Score {result.score:.3f}")
        else:
            print("❌ Search returned no results")
            return False
    except Exception as e:
        print(f"❌ Search error: {e}")
        return False

    print("\n🎉 All tests passed successfully!")
    print("The improved components are working correctly.")
    return True

async def main():
    """
    Main entry point for the test script.
    """
    print("🧪 Atlan Copilot - Component Test Suite")
    print("=" * 50)

    # Check environment variables
    required_vars = ["GOOGLE_API_KEY", "QDRANT_API_KEY", "QDRANT_URL"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables before running tests.")
        return

    print("✅ Environment variables verified")

    # Run tests
    success = await test_improved_components()

    if success:
        print("\n✅ All component tests passed!")
        print("You can now safely use the improved embedder and vector store.")
    else:
        print("\n❌ Some tests failed.")
        print("Please check the error messages above and fix any issues.")

if __name__ == "__main__":
    asyncio.run(main())
