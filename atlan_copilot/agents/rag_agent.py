import os
import sys
from typing import Dict, Any, List

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agents.base_agent import BaseAgent
from embeddings.gemini_embedder import GeminiEmbedder
from embeddings.similarity_search import SimilaritySearch

class RAGAgent(BaseAgent):
    """
    Retrieval-Augmented Generation Agent.
    This agent takes a user query, retrieves relevant context from the vector store,
    and adds it to the state for the next agent to use.
    """
    def __init__(self):
        super().__init__()
        self.embedder = GeminiEmbedder(model_name="models/text-embedding-004")
        self.search_client = SimilaritySearch()

    def _format_context(self, search_results: List[Dict]) -> str:
        """
        Formats the list of search result documents into a single string.
        This string will be passed to the response generation model.
        """
        if not search_results:
            return "No relevant documents were found in the knowledge base."

        context_str = "Here is some context I found that might be relevant to your question:\n\n"
        for i, doc in enumerate(search_results, 1):
            context_str += f"--- Context Snippet {i} ---\n"
            context_str += f"Source: {doc.get('source', 'N/A')}\n"
            context_str += f"URL: {doc.get('url', 'N/A')}\n"
            context_str += f"Title: {doc.get('title', 'N/A')}\n"
            content_snippet = doc.get('content', '')
            context_str += f"Content: {content_snippet}\n\n"

        return context_str

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the RAG pipeline: embed query, search, format context, update state.
        """
        print("--- Executing RAG Agent ---")
        query = state.get("query")
        if not query:
            print("Error: No query found in state for RAG agent.")
            return {**state, "context": "Error: No query was provided to the RAG agent."}

        # 1. Embed the user's query
        # The embedder expects a list of texts
        query_embedding = self.embedder.embed_documents([query])
        if not query_embedding:
            print("Error: Could not generate embedding for the query.")
            return {**state, "context": "Error: The query could not be processed into an embedding."}

        # 2. Search vector store collections
        qdrant_host = os.getenv("QDRANT_HOST")
        if not qdrant_host or "your-qdrant-cluster-url" in qdrant_host:
            print("Warning: QDRANT_HOST not set. RAG search is disabled.")
            context = "Placeholder: RAG search is disabled because the vector database (QDRANT_HOST) is not configured."
        else:
            print(f"Searching vector stores for query: '{query[:50]}...'")
            # Search both documentation collections and combine the results
            docs_results = await self.search_client.search("atlan_docs", query_embedding[0], limit=3)
            dev_results = await self.search_client.search("atlan_developer", query_embedding[0], limit=2)

            all_results = docs_results + dev_results
            # A more advanced implementation might re-rank the combined results.
            # For now, simple concatenation is sufficient.

            context = self._format_context(all_results)

        print(f"Retrieved context: {context[:400]}...")

        # 3. Update the state with the retrieved context
        updated_state = state.copy()
        updated_state["context"] = context
        return updated_state
