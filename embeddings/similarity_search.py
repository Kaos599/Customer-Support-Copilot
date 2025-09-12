from typing import List, Dict
import os
import sys

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from atlan_copilot.database.qdrant_client import QdrantDBClient
from qdrant_client.models import ScoredPoint

class SimilaritySearch:
    """
    A class dedicated to performing similarity searches in the Qdrant vector database.
    """
    def __init__(self):
        """
        Initializes the similarity search client.
        """
        self.qdrant_client = QdrantDBClient()

    async def search(self, collection_name: str, query_vector: List[float], limit: int = 5) -> List[Dict]:
        """
        Performs a similarity search in the specified Qdrant collection.

        Args:
            collection_name: The name of the collection to search within.
            query_vector: The embedding vector of the user's query.
            limit: The maximum number of results to return.

        Returns:
            A list of payload dictionaries from the most relevant documents.
        """
        try:
            hits: List[ScoredPoint] = await self.qdrant_client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit
            )
            # Extract the payload from each search result (hit)
            return [hit.payload for hit in hits] if hits else []
        except Exception as e:
            # This can happen if the collection doesn't exist or there's a connection issue.
            print(f"An error occurred during similarity search in '{collection_name}': {e}")
            return []
        finally:
            # Ensure the client connection is closed
            await self.qdrant_client.close()
