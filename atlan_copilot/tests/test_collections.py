import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the Python path
sys.path.insert(0, '.')

from atlan_copilot.database.qdrant_client import QdrantDBClient

async def test_collections():
    print(f'QDRANT_HOST: {os.getenv("QDRANT_HOST")}')

    # Test Qdrant collections
    client = QdrantDBClient()
    qdrant_client = await client._get_client()

    try:
        # List all collections
        collections = await qdrant_client.get_collections()
        print(f'Available collections: {[c.name for c in collections.collections]}')

        # Check specific collections
        for collection_name in ['atlan_docs', 'atlan_developer']:
            try:
                collection_info = await qdrant_client.get_collection(collection_name)
                print(f'Collection {collection_name}: {collection_info.points_count} points')

                # Get a sample point to check payload structure
                if collection_info.points_count > 0:
                    points = await qdrant_client.retrieve(collection_name, ids=[0], with_payload=True)
                    if points:
                        print(f'Sample point from {collection_name}:')
                        print(f'  Payload keys: {list(points[0].payload.keys())}')
                        content = points[0].payload.get('content', '')
                        print(f'  Content length: {len(content)}')
                        print(f'  Content preview: {content[:200]}...')

            except Exception as e:
                print(f'Error checking collection {collection_name}: {e}')

    except Exception as e:
        print(f'Error listing collections: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_collections())
