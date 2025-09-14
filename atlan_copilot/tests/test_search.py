import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the Python path
sys.path.insert(0, '.')

from atlan_copilot.database.qdrant_client import QdrantDBClient
from atlan_copilot.embeddings.gemini_embedder import GeminiEmbedder

async def test_search():
    print(f'QDRANT_HOST: {os.getenv("QDRANT_HOST")}')
    print(f'GOOGLE_API_KEY: {os.getenv("GOOGLE_API_KEY", "Not set")[:20]}...')

    # Test similarity search
    search_client = QdrantDBClient()
    embedder = GeminiEmbedder()

    # Generate embedding for a test query
    query = 'SSO authentication methods'
    query_embedding = embedder.embed_documents([query])

    if not query_embedding:
        print('Failed to generate embedding')
        return

    print(f'Generated embedding with {len(query_embedding[0])} dimensions')

    # Search the collections
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
            if hasattr(result, 'payload'):
                payload = result.payload
                print(f'Payload type: {type(payload)}')
                print(f'Payload keys: {list(payload.keys()) if hasattr(payload, "keys") else "No keys method"}')
                print(f'Content preview: {payload.get("content", "No content")[:200]}...')
                print(f'Full payload: {payload}')
            else:
                print(f'No payload attribute. Result: {result}')
        elif dev_results:
            print('Sample result structure from atlan_developer:')
            result = dev_results[0]
            print(f'Type: {type(result)}')
            if hasattr(result, 'payload'):
                payload = result.payload
                print(f'Payload type: {type(payload)}')
                print(f'Payload keys: {list(payload.keys()) if hasattr(payload, "keys") else "No keys method"}')
                print(f'Content preview: {payload.get("content", "No content")[:200]}...')
                print(f'Full payload: {payload}')
            else:
                print(f'No payload attribute. Result: {result}')
        else:
            print('No results found in either collection')

    except Exception as e:
        print(f'Error during search: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_search())
