import re
import numpy as np
from typing import List, Dict, Any, Tuple
from langgraph.graph import StateGraph, END
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sklearn.metrics.pairwise import cosine_similarity
import asyncio
import os
import sys

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from embeddings.gemini_embedder import GeminiEmbedder

class SemanticChunker:
    """
    A semantic text chunker that uses LangGraph to create meaningful text chunks
    based on semantic similarity rather than fixed character counts.
    """

    def __init__(self, embedder=None, similarity_threshold: float = 0.7, min_chunk_size: int = 500, max_chunk_size: int = 2000):
        """
        Initialize the semantic chunker.

        Args:
            embedder: The embedder to use for generating embeddings
            similarity_threshold: Threshold for determining semantic boundaries (0-1)
            min_chunk_size: Minimum characters per chunk
            max_chunk_size: Maximum characters per chunk
        """
        self.embedder = embedder or GeminiEmbedder()
        self.similarity_threshold = similarity_threshold
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size

        # Initialize the LangGraph workflow
        self.workflow = self._create_chunking_workflow()

    def _create_chunking_workflow(self):
        """Create the LangGraph workflow for semantic chunking."""

        # Define the state structure as a TypedDict for better type safety
        from typing import TypedDict

        class ChunkingState(TypedDict):
            text: str
            sentences: List[str]
            embeddings: List[List[float]]
            chunks: List[str]
            metadata: Dict[str, Any]

        # Define the nodes
        def split_into_sentences(state: ChunkingState) -> ChunkingState:
            """Split text into sentences."""
            # Simple sentence splitting - could be enhanced with NLP libraries
            sentences = re.split(r'(?<=[.!?])\s+', state["text"].strip())
            sentences = [s.strip() for s in sentences if s.strip()]

            new_state = ChunkingState(
                text=state["text"],
                sentences=sentences,
                embeddings=state["embeddings"],
                chunks=state["chunks"],
                metadata=state["metadata"]
            )
            print(f"Split into {len(sentences)} sentences")
            return new_state

        def generate_embeddings(state: ChunkingState) -> ChunkingState:
            """Generate embeddings for each sentence."""
            if not state["sentences"]:
                return state

            # Generate embeddings in batches to avoid rate limits
            batch_size = 10
            embeddings = []

            for i in range(0, len(state["sentences"]), batch_size):
                batch = state["sentences"][i:i + batch_size]
                try:
                    batch_embeddings = self.embedder.embed_documents(batch)
                    embeddings.extend(batch_embeddings)
                except Exception as e:
                    print(f"Error generating embeddings for batch {i//batch_size}: {e}")
                    # Add zero vectors for failed embeddings
                    embeddings.extend([[0.0] * 768] * len(batch))

            new_state = ChunkingState(
                text=state["text"],
                sentences=state["sentences"],
                embeddings=embeddings,
                chunks=state["chunks"],
                metadata=state["metadata"]
            )
            print(f"Generated embeddings for {len(embeddings)} sentences")
            return new_state

        def find_semantic_boundaries(state: ChunkingState) -> ChunkingState:
            """Find semantic boundaries based on embedding similarity."""
            if len(state["sentences"]) <= 1:
                new_state = ChunkingState(
                    text=state["text"],
                    sentences=state["sentences"],
                    embeddings=state["embeddings"],
                    chunks=state["sentences"],
                    metadata=state["metadata"]
                )
                return new_state

            chunks = []
            current_chunk_sentences = [state["sentences"][0]]
            current_chunk_text = state["sentences"][0]

            for i in range(1, len(state["sentences"])):
                current_sentence = state["sentences"][i]
                prev_embedding = np.array(state["embeddings"][i-1]).reshape(1, -1)
                current_embedding = np.array(state["embeddings"][i]).reshape(1, -1)

                # Calculate cosine similarity
                similarity = cosine_similarity(prev_embedding, current_embedding)[0][0]

                # Check if we should start a new chunk
                should_split = (
                    similarity < self.similarity_threshold or
                    len(current_chunk_text + " " + current_sentence) > self.max_chunk_size
                )

                if should_split:
                    # Finalize current chunk
                    if len(current_chunk_text) >= self.min_chunk_size:
                        chunks.append(current_chunk_text)
                    else:
                        # Merge with next chunk if too small
                        if chunks:
                            chunks[-1] += " " + current_chunk_text
                        else:
                            chunks.append(current_chunk_text)

                    # Start new chunk
                    current_chunk_sentences = [current_sentence]
                    current_chunk_text = current_sentence
                else:
                    # Continue current chunk
                    current_chunk_sentences.append(current_sentence)
                    current_chunk_text += " " + current_sentence

            # Add the last chunk
            if current_chunk_text:
                if len(current_chunk_text) >= self.min_chunk_size:
                    chunks.append(current_chunk_text)
                elif chunks:
                    chunks[-1] += " " + current_chunk_text
                else:
                    chunks.append(current_chunk_text)

            new_state = ChunkingState(
                text=state["text"],
                sentences=state["sentences"],
                embeddings=state["embeddings"],
                chunks=chunks,
                metadata=state["metadata"]
            )
            print(f"Created {len(chunks)} semantic chunks")
            return new_state

        def refine_chunks(state: ChunkingState) -> ChunkingState:
            """Refine chunks to ensure they meet size requirements."""
            refined_chunks = []

            for chunk in state["chunks"]:
                if len(chunk) > self.max_chunk_size:
                    # Split oversized chunks using recursive text splitter as fallback
                    splitter = RecursiveCharacterTextSplitter(
                        chunk_size=self.max_chunk_size,
                        chunk_overlap=int(self.max_chunk_size * 0.1)
                    )
                    sub_chunks = splitter.split_text(chunk)
                    refined_chunks.extend(sub_chunks)
                else:
                    refined_chunks.append(chunk)

            new_state = ChunkingState(
                text=state["text"],
                sentences=state["sentences"],
                embeddings=state["embeddings"],
                chunks=refined_chunks,
                metadata=state["metadata"]
            )
            print(f"Refined to {len(refined_chunks)} final chunks")
            return new_state

        # Create the graph
        workflow = StateGraph(ChunkingState)

        # Add nodes
        workflow.add_node("split_sentences", split_into_sentences)
        workflow.add_node("generate_embeddings", generate_embeddings)
        workflow.add_node("find_boundaries", find_semantic_boundaries)
        workflow.add_node("refine_chunks", refine_chunks)

        # Define the flow
        workflow.set_entry_point("split_sentences")
        workflow.add_edge("split_sentences", "generate_embeddings")
        workflow.add_edge("generate_embeddings", "find_boundaries")
        workflow.add_edge("find_boundaries", "refine_chunks")
        workflow.add_edge("refine_chunks", END)

        return workflow.compile()

    async def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[str]:
        """
        Chunk text semantically using the LangGraph workflow.

        Args:
            text: The text to chunk
            metadata: Optional metadata about the text

        Returns:
            List of semantic chunks
        """
        if not text or not text.strip():
            return []

        # Initialize state as dictionary
        initial_state = {
            "text": text,
            "sentences": [],
            "embeddings": [],
            "chunks": [],
            "metadata": metadata or {}
        }

        # Run the workflow
        try:
            result = await self.workflow.ainvoke(initial_state)
            return result["chunks"]
        except Exception as e:
            print(f"Error in semantic chunking: {e}")
            # Fallback to simple character-based chunking
            return self._fallback_chunking(text)

    def chunk_text_sync(self, text: str, metadata: Dict[str, Any] = None) -> List[str]:
        """
        Synchronous version of chunk_text for compatibility.
        """
        try:
            # Try to get the current event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is already running, use fallback
                print("Event loop already running, using fallback chunking")
                return self._fallback_chunking(text)
            else:
                # Run the async version
                return loop.run_until_complete(self.chunk_text(text, metadata))
        except RuntimeError:
            # No event loop, create a new one
            try:
                return asyncio.run(self.chunk_text(text, metadata))
            except Exception as e:
                print(f"Error in async chunking: {e}")
                return self._fallback_chunking(text)

    def _fallback_chunking(self, text: str) -> List[str]:
        """Fallback character-based chunking when semantic chunking fails."""
        if len(text) <= self.max_chunk_size:
            return [text]

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.max_chunk_size,
            chunk_overlap=int(self.max_chunk_size * 0.1)
        )
        return splitter.split_text(text)

    def process_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process a list of documents using semantic chunking.

        Args:
            documents: List of document dictionaries with 'content' key

        Returns:
            List of chunk dictionaries ready for embedding
        """
        processed_chunks = []

        for doc in documents:
            if not doc.get("content"):
                continue

            # Clean the text
            clean_content = self._clean_text(doc["content"])
            if not clean_content:
                continue

            # Chunk the content semantically
            try:
                chunks = self.chunk_text_sync(clean_content, doc)
            except Exception as e:
                print(f"Error chunking document {doc.get('url', 'unknown')}: {e}")
                chunks = self._fallback_chunking(clean_content)

            # Create chunk payloads
            for i, chunk_text in enumerate(chunks):
                chunk_payload = {
                    "source": doc.get("source"),
                    "url": doc.get("url"),
                    "title": doc.get("title"),
                    "content": chunk_text,
                    "doc_type": "documentation",
                    "chunk_method": "semantic"
                }

                chunk_id = f"{doc.get('url', 'unknown')}-chunk-{i}"

                processed_chunks.append({
                    "id": chunk_id,
                    "payload": chunk_payload
                })

        print(f"Processed {len(documents)} documents into {len(processed_chunks)} semantic chunks.")
        return processed_chunks

    def _clean_text(self, text: str) -> str:
        """Clean the input text."""
        # Consolidate whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
