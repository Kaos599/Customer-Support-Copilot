from typing import List, Dict, Any
from qdrant_client import models
import os
import sys
import uuid
import asyncio
from datetime import datetime, timezone

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
    def __init__(self, qdrant_client=None, batch_size: int = 20):
        if qdrant_client:
            self.qdrant_client = qdrant_client
        else:
            self.qdrant_client = QdrantDBClient()
        self.embedder = GeminiEmbedder()
        # The vector size for models/text-embedding-004 is 768 (recommended)
        self.vector_size = 768
        self.batch_size = batch_size  # Smaller batch size to avoid rate limits

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
            return True

        # 1. Ensure the Qdrant collection exists
        await self.qdrant_client.create_collection_if_not_exists(
            collection_name,
            vector_size=self.vector_size
        )

        # 2. Process documents in smaller batches to avoid rate limits
        successful_upserts = 0
        failed_upserts = 0

        for i in range(0, len(documents), self.batch_size):
            batch_docs = documents[i:i + self.batch_size]
            batch_number = i // self.batch_size + 1
            total_batches = (len(documents) + self.batch_size - 1) // self.batch_size

            print(f"Processing batch {batch_number}/{total_batches} ({len(batch_docs)} documents)...")

            try:
                # Extract text content for embedding
                texts_to_embed = [doc["payload"]["content"] for doc in batch_docs]

                # Generate embeddings with rate limiting
                embeddings = self.embedder.embed_documents(texts_to_embed)

                if not embeddings or len(embeddings) != len(batch_docs):
                    print(f"Error: Embedding generation failed for batch {batch_number}. Expected {len(batch_docs)} embeddings, got {len(embeddings) if embeddings else 0}")
                    failed_upserts += len(batch_docs)
                    continue

                # Create Qdrant PointStruct objects
                points = []
                for doc, vector in zip(batch_docs, embeddings):
                    # Generate a UUID for the point ID (Qdrant requires UUID or integer)
                    point_id = str(uuid.uuid4())

                    # Add the original string ID to the payload for reference
                    enhanced_payload = doc["payload"].copy()
                    enhanced_payload["original_id"] = doc["id"]
                    enhanced_payload["indexed_at"] = datetime.now(timezone.utc).isoformat()

                    points.append(models.PointStruct(
                        id=point_id,
                        vector=vector,
                        payload=enhanced_payload
                    ))

                # Upsert points into Qdrant
                print(f"Upserting {len(points)} points into Qdrant collection '{collection_name}'...")
                await self.qdrant_client.upsert_points(collection_name, points)

                successful_upserts += len(points)
                print(f"✅ Successfully upserted batch {batch_number}/{total_batches}")

                # Add a small delay between batches to be extra safe with rate limits
                if batch_number < total_batches:
                    await asyncio.sleep(1)

            except Exception as e:
                print(f"❌ Failed to process batch {batch_number}: {e}")
                failed_upserts += len(batch_docs)
                continue

        # Summary
        total_processed = successful_upserts + failed_upserts
        success_rate = (successful_upserts / total_processed * 100) if total_processed > 0 else 0

        print(f"\n📊 Batch Processing Summary:")
        print(f"   ✅ Successful upserts: {successful_upserts}")
        print(f"   ❌ Failed upserts: {failed_upserts}")
        print(f"   📈 Success rate: {success_rate:.1f}%")

        if successful_upserts > 0:
            print(f"Successfully upserted a total of {successful_upserts} points.")
            return True
        else:
            print("No points were successfully upserted.")
            return False
