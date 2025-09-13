import re
from typing import List, Dict, Any
from .semantic_chunker import SemanticChunker

class ContentProcessor:
    """
    Processes raw text content extracted from web pages and splits it into
    semantic chunks using LangGraph-based semantic chunking.
    """
    def __init__(self, chunk_size: int = 1500, chunk_overlap: int = 300, similarity_threshold: float = 0.7):
        """
        Initializes the content processor with semantic chunking parameters.

        Args:
            chunk_size: The target size for each text chunk in characters (used for fallback).
            chunk_overlap: The number of characters to overlap between consecutive chunks (used for fallback).
            similarity_threshold: Threshold for semantic similarity in chunking (0-1).
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.similarity_threshold = similarity_threshold

        # Initialize the semantic chunker
        self.semantic_chunker = SemanticChunker(
            similarity_threshold=similarity_threshold,
            min_chunk_size=int(chunk_size * 0.5),  # 50% of target size as minimum
            max_chunk_size=int(chunk_size * 1.5)   # 150% of target size as maximum
        )

    def _clean_text(self, text: str) -> str:
        """
        Performs basic cleaning operations on the text content.
        - Replaces multiple whitespace characters with a single space.
        - Removes non-printable characters.
        """
        # Consolidate whitespace (including newlines, tabs, etc.) into a single space
        text = re.sub(r'\s+', ' ', text)
        # Further cleanup can be added here if needed (e.g., removing specific boilerplate)
        return text.strip()

    def process(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Processes a list of scraped documents using semantic chunking.

        For each document, it cleans the text content and splits it into semantic chunks
        that preserve meaning and context better than fixed-size chunks.

        Args:
            documents: A list of dictionaries from the scraper, each with a "content" key.

        Returns:
            A list of chunk dictionaries, ready to be embedded. Each chunk includes
            the original metadata and a unique chunk ID.
        """
        print("🔍 Starting semantic chunking process...")

        # Clean documents first
        cleaned_documents = []
        for doc in documents:
            if not doc.get("content"):
                continue

            clean_content = self._clean_text(doc["content"])
            if not clean_content:
                continue

            # Add cleaned content to document
            cleaned_doc = doc.copy()
            cleaned_doc["content"] = clean_content
            cleaned_documents.append(cleaned_doc)

        if not cleaned_documents:
            print("⚠️  No valid documents to process")
            return []

        # Use semantic chunker to process all documents
        try:
            processed_chunks = self.semantic_chunker.process_documents(cleaned_documents)
            print(f"✅ Semantic chunking completed: {len(processed_chunks)} chunks created")
            return processed_chunks

        except Exception as e:
            print(f"❌ Error in semantic chunking: {e}")
            print("🔄 Falling back to character-based chunking...")

            # Fallback to character-based chunking
            return self._fallback_chunking(cleaned_documents)

    def _fallback_chunking(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Fallback character-based chunking when semantic chunking fails.
        """
        print("Using fallback character-based chunking...")

        processed_chunks = []
        for doc in documents:
            if not doc.get("content"):
                continue

            clean_content = doc["content"]
            if not clean_content:
                continue

            # Simple character-based chunking
            chunks = self._chunk_text_recursively(clean_content)

            for i, chunk_text in enumerate(chunks):
                # The payload for the vector store should contain all relevant metadata
                chunk_payload = {
                    "source": doc.get("source"),
                    "url": doc.get("url"),
                    "title": doc.get("title"),
                    "content": chunk_text,
                    "doc_type": "documentation",
                    "chunk_method": "character_fallback"  # Indicate this is fallback
                }
                # The chunk_id can be used as the Point ID in Qdrant
                chunk_id = f"{doc.get('url')}-chunk-{i}"

                processed_chunks.append({
                    "id": chunk_id,
                    "payload": chunk_payload
                })

        print(f"Fallback chunking created {len(processed_chunks)} chunks")
        return processed_chunks

    def _chunk_text_recursively(self, text: str) -> List[str]:
        """
        Legacy character-based chunking method (kept for fallback).
        Splits text into chunks of a specified size with overlap.
        """
        if not text:
            return []

        # If the text is smaller than the chunk size, no need to chunk.
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start_index = 0
        while start_index < len(text):
            end_index = start_index + self.chunk_size
            chunks.append(text[start_index:end_index])
            start_index += self.chunk_size - self.chunk_overlap

        return chunks
