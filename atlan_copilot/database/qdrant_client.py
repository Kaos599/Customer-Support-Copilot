import os
from qdrant_client import AsyncQdrantClient, models
from typing import List, Dict, Optional

class QdrantDBClient:
    """
    An asynchronous client for interacting with a Qdrant vector database.
    """
    def __init__(self):
        """
        Initializes the Qdrant client by reading connection details from environment variables.
        """
        self.qdrant_host = os.getenv("QDRANT_HOST")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY")

        if not all([self.qdrant_host, self.qdrant_api_key]):
            raise ValueError("Qdrant environment variables (QDRANT_HOST, QDRANT_API_KEY) must be set.")

        self.client = AsyncQdrantClient(
            url=self.qdrant_host,
            api_key=self.qdrant_api_key,
        )

    async def verify_connection(self):
        """
        Verifies the connection to Qdrant by attempting to retrieve the list of collections.
        """
        try:
            await self.client.get_collections()
            print("Qdrant connection successful.")
        except Exception as e:
            print(f"Error connecting to Qdrant: {e}")
            raise

    async def create_collection_if_not_exists(self, collection_name: str, vector_size: int = 1536):
        """
        Creates a new collection in Qdrant if it does not already exist.

        Args:
            collection_name: The name of the collection to create.
            vector_size: The dimensionality of the vectors that will be stored in this collection.
        """
        try:
            collections_response = await self.client.get_collections()
            existing_collections = [c.name for c in collections_response.collections]
            if collection_name not in existing_collections:
                await self.client.recreate_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
                )
                print(f"Collection '{collection_name}' created successfully.")
            else:
                print(f"Collection '{collection_name}' already exists.")
        except Exception as e:
            print(f"Error creating or checking Qdrant collection '{collection_name}': {e}")
            raise

    async def upsert_points(self, collection_name: str, points: List[models.PointStruct]):
        """
        Upserts a list of points (documents with vectors) into a collection.

        Args:
            collection_name: The name of the collection to upsert into.
            points: A list of Qdrant PointStruct objects.
        """
        try:
            await self.client.upsert(
                collection_name=collection_name,
                points=points,
                wait=True
            )
            print(f"Successfully upserted {len(points)} points into '{collection_name}'.")
        except Exception as e:
            print(f"Error upserting points into Qdrant: {e}")
            raise

    async def search(self, collection_name: str, query_vector: List[float], limit: int = 5) -> List[models.ScoredPoint]:
        """
        Performs a similarity search in a specified collection.

        Args:
            collection_name: The name of the collection to search in.
            query_vector: The vector to search with.
            limit: The maximum number of results to return.

        Returns:
            A list of ScoredPoint objects representing the search results.
        """
        try:
            hits = await self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                with_payload=True
            )
            return hits
        except Exception as e:
            print(f"Error searching in Qdrant collection '{collection_name}': {e}")
            raise

    async def close(self):
        """
        Closes the Qdrant client connection.
        """
        await self.client.close()
        print("Qdrant connection closed.")
