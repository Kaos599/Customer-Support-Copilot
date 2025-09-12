from typing import List, Dict, Any
from qdrant_client import models
import os
import sys
import uuid

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database.qdrant_client import QdrantDBClient
from embeddings.gemini_embedder import GeminiEmbedder

class VectorStore:
    """
    Manages the process of embedding documents and storing them in a Qdrant vector store.
    """
    def __init__(self, qdrant_client=None):
        if qdrant_client:
            self.qdrant_client = qdrant_client
        else:
            self.qdrant_client = QdrantDBClient()
        self.embedder = GeminiEmbedder()
        # The vector size for models/text-embedding-004 is 768 (recommended)
        self.vector_size = 768

    async def upsert_documents(self, collection_name: str, documents: List[Dict[str, Any]]):
        """
        Embeds and upserts a list of processed documents into the specified Qdrant collection.

        Args:
            collection_name: The name of the Qdrant collection to upsert into.
            documents: A list of processed chunk dictionaries from the ContentProcessor.
                       Each dictionary must have an 'id' and a 'payload' with a 'content' key.
        """
        if not documents:
            print("No documents to upsert.")
            return

        # 1. Ensure the Qdrant collection exists
        await self.qdrant_client.create_collection_if_not_exists(
            collection_name,
            vector_size=self.vector_size
        )

        # 2. Extract text content for embedding
        texts_to_embed = [doc["payload"]["content"] for doc in documents]

        # 3. Generate embeddings
        # Note: The embedder runs synchronously for simplicity in this script.
        # For a large-scale application, this could be a bottleneck.
        embeddings = self.embedder.embed_documents(texts_to_embed)

        if not embeddings or len(embeddings) != len(documents):
            print("Error: Embedding generation failed or returned an incorrect number of vectors.")
            return False

        # 4. Create Qdrant PointStruct objects
        points = []
        for doc, vector in zip(documents, embeddings):
            # Generate a UUID for the point ID (Qdrant requires UUID or integer)
            point_id = str(uuid.uuid4())
            
            # Add the original string ID to the payload for reference
            enhanced_payload = doc["payload"].copy()
            enhanced_payload["original_id"] = doc["id"]
            
            points.append(models.PointStruct(
                id=point_id,
                vector=vector,
                payload=enhanced_payload
            ))

        # 5. Upsert points into Qdrant in batches to avoid large requests
        batch_size = 100
        num_batches = (len(points) + batch_size - 1) // batch_size

        for i in range(num_batches):
            start_idx = i * batch_size
            end_idx = start_idx + batch_size
            batch_points = points[start_idx:end_idx]

            print(f"Upserting batch {i + 1}/{num_batches} ({len(batch_points)} points) into Qdrant collection '{collection_name}'...")
            await self.qdrant_client.upsert_points(collection_name, batch_points)

        print(f"Successfully upserted a total of {len(points)} points.")
        # Note: Don't close the client here - let the caller handle client lifecycle
        # await self.qdrant_client.close()
        return True
