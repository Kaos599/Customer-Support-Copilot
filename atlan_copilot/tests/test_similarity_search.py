import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the Python path
sys.path.insert(0, '.')

from atlan_copilot.embeddings.similarity_search import SimilaritySearch
from atlan_copilot.embeddings.gemini_embedder import GeminiEmbedder

async def test_similarity_search():
    print(f'QDRANT_HOST: {os.getenv("QDRANT_HOST")}')
    print(f'GOOGLE_API_KEY: {os.getenv("GOOGLE_API_KEY", "Not set")[:20]}...')

    # Test similarity search
    search_client = SimilaritySearch()
    embedder = GeminiEmbedder()

    # Generate embedding for a test query
    query = 'SSO authentication methods'
    query_embedding = embedder.embed_documents([query])

    if not query_embedding:
        print('Failed to generate embedding')
        return

    print(f'Generated embedding with {len(query_embedding[0])} dimensions')

    # Search the collections using SimilaritySearch
    try:
        docs_results = await search_client.search('atlan_docs', query_embedding[0], limit=2)
        dev_results = await search_client.search('atlan_developer', query_embedding[0], limit=2)

        print(f'Found {len(docs_results)} results in atlan_docs')
        print(f'Found {len(dev_results)} results in atlan_developer')

        # Print structure of first result
        if docs_results:
            print('Sample result structure from atlan_docs:')
            result = docs_results[0]
            print(f'Type: {type(result)}')
            print(f'Keys: {list(result.keys()) if hasattr(result, "keys") else "No keys"}')
            if isinstance(result, dict):
                print(f'Content preview: {result.get("content", "No content")[:200]}...')
                print(f'Source: {result.get("source", "No source")}')
                print(f'URL: {result.get("url", "No URL")}')
        elif dev_results:
            print('Sample result structure from atlan_developer:')
            result = dev_results[0]
            print(f'Type: {type(result)}')
            print(f'Keys: {list(result.keys()) if hasattr(result, "keys") else "No keys"}')
            if isinstance(result, dict):
                print(f'Content preview: {result.get("content", "No content")[:200]}...')
                print(f'Source: {result.get("source", "No source")}')
                print(f'URL: {result.get("url", "No URL")}')
        else:
            print('No results found in either collection')

    except Exception as e:
        print(f'Error during search: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_similarity_search())
