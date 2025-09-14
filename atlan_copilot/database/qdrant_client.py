import os
import asyncio
import platform
import threading
from qdrant_client import AsyncQdrantClient, models
from typing import List, Dict, Optional
import nest_asyncio

# Enable nested asyncio and set Windows event loop policy
nest_asyncio.apply()
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

class QdrantDBClient:
    """
    An asynchronous client for interacting with a Qdrant vector database.
    Uses singleton pattern to prevent connection issues and manages async loops properly.
    """
    _instance = None
    _lock = threading.Lock()
    _client = None
    _initialized = False
    
    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """
        Initializes the Qdrant client by reading connection details from environment variables.
        """
        if self._initialized:
            return
            
        self.qdrant_host = os.getenv("QDRANT_HOST")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY")

        if not all([self.qdrant_host, self.qdrant_api_key]):
            raise ValueError("Qdrant environment variables (QDRANT_HOST, QDRANT_API_KEY) must be set.")

        self._client = None
        self._initialized = True
    
    async def _get_client(self):
        """Get or create the async client with proper connection management"""
        try:
            # Reuse existing client if available and healthy
            if self._client:
                try:
                    # Test the connection with a simple operation
                    await self._client.get_collections()
                    return self._client
                except Exception:
                    # Client is not healthy, close and recreate
                    try:
                        await self._client.close()
                    except:
                        pass
                    self._client = None

            # Create new client
            self._client = AsyncQdrantClient(
                url=self.qdrant_host,
                api_key=self.qdrant_api_key,
                timeout=30,
            )

            # Test the new connection
            await self._client.get_collections()
            return self._client

        except Exception as e:
            print(f"Error creating or validating Qdrant client: {e}")
            # Clean up failed client
            if self._client:
                try:
                    await self._client.close()
                except:
                    pass
                self._client = None
            raise

    async def verify_connection(self):
        """
        Verifies the connection to Qdrant by attempting to retrieve the list of collections.
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                client = await self._get_client()
                await client.get_collections()
                print("Qdrant connection successful.")
                return
            except Exception as e:
                print(f"Qdrant connection attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    print(f"Failed to connect to Qdrant after {max_retries} attempts.")
                    raise
                await asyncio.sleep(1)  # Wait before retry
                # Clean up client on failure
                if self._client:
                    try:
                        await self._client.close()
                    except:
                        pass
                    self._client = None

    async def create_collection_if_not_exists(self, collection_name: str, vector_size: int = 1536):
        """
        Creates a new collection in Qdrant if it does not already exist.

        Args:
            collection_name: The name of the collection to create.
            vector_size: The dimensionality of the vectors that will be stored in this collection.
        """
        try:
            client = await self._get_client()
            collections_response = await client.get_collections()
            existing_collections = [c.name for c in collections_response.collections]
            if collection_name not in existing_collections:
                await client.recreate_collection(
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
            client = await self._get_client()
            await client.upsert(
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
        Performs a similarity search in a specified collection with proper error handling.

        Args:
            collection_name: The name of the collection to search in.
            query_vector: The vector to search with.
            limit: The maximum number of results to return.

        Returns:
            A list of ScoredPoint objects representing the search results.
        """
        try:
            client = await self._get_client()
            hits = await client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                with_payload=True
            )
            return hits
        except Exception as e:
            print(f"Error searching in Qdrant collection '{collection_name}': {e}")
            # Clean up client on search failure
            if self._client:
                try:
                    await self._client.close()
                except:
                    pass
                self._client = None
            raise

    async def close(self):
        """
        Closes the Qdrant client connection.
        """
        if self._client:
            try:
                await self._client.close()
                print("Qdrant connection closed.")
            except:
                print("Qdrant connection already closed or failed to close.")
            finally:
                self._client = None
