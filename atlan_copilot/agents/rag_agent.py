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

    def _create_citations_from_search_results(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create citations directly from search results.
        Citations reference the actual retrieved content that supports the response.

        Args:
            search_results: List of search result dictionaries

        Returns:
            List of citation dictionaries with actual content references
        """
        citations = []
        for i, result in enumerate(search_results, 1):
            # Filter out localhost URLs
            url = result.get('url', '')
            if url and url.startswith(('http://localhost', 'http://127.0.0.1')):
                url = ''

            citation = {
                'id': str(i),
                'title': result.get('title', f'Source {i}'),
                'url': url,
                'source': result.get('source', 'Atlan Documentation'),
                'content_snippet': result.get('content', ''),
                'relevance_score': result.get('score', 0.8),  # Use actual similarity score
                'confidence_score': 0.75  # Default confidence score
            }
            citations.append(citation)

        return citations

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

    def _format_context_with_citations(self, search_results: List[Dict]) -> str:
        """
        Formats the search results with numbered citations that will be used by the response generation.
        This ensures citations reference actual retrieved content.

        Args:
            search_results: List of search result dictionaries

        Returns:
            Formatted context string with numbered citation markers
        """
        if not search_results:
            return "No relevant documents were found in the knowledge base."

        context_str = "Here is some context I found that might be relevant to your question:\n\n"
        for i, doc in enumerate(search_results, 1):
            context_str += f"--- Context Snippet [{i}] ---\n"
            context_str += f"Source: {doc.get('source', 'N/A')}\n"
            context_str += f"URL: {doc.get('url', 'N/A')}\n"
            context_str += f"Title: {doc.get('title', 'N/A')}\n"
            content_snippet = doc.get('content', '')
            context_str += f"Content: {content_snippet}\n\n"

        return context_str

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the RAG pipeline: embed query, search, format context, update state.
        Uses standard retrieval with proper citations of actual retrieved content.
        """
        print("--- Executing RAG Agent ---")
        query = state.get("query")
        if not query:
            print("Error: No query found in state for RAG agent.")
            return {**state, "context": "Error: No query was provided to the RAG agent."}

        # 1. Embed the user's query
        query_embedding = self.embedder.embed_documents([query])
        if not query_embedding:
            print("Error: Could not generate embedding for the query.")
            return {**state, "context": "Error: The query could not be processed into an embedding."}

        # 2. Search vector store collections
        qdrant_host = os.getenv("QDRANT_HOST")
        if not qdrant_host or "your-qdrant-cluster-url" in qdrant_host:
            print("Warning: QDRANT_HOST not set. RAG search is disabled.")
            context = "Placeholder: RAG search is disabled because the vector database (QDRANT_HOST) is not configured."
            citations = []
        else:
            print(f"Searching vector stores for query: '{query[:50]}...'")
            # Search both documentation collections and combine the results
            docs_results = await self.search_client.search("atlan_docs", query_embedding[0], limit=3)
            dev_results = await self.search_client.search("atlan_developer", query_embedding[0], limit=2)

            all_results = docs_results + dev_results

            # Format context with numbered citations for the response generation
            context = self._format_context_with_citations(all_results)

            # Create citations from actual search results
            citations = self._create_citations_from_search_results(all_results)

        print(f"Retrieved context: {context[:400]}...")
        print(f"Created {len(citations)} citations from actual retrieved content")

        # Update the state with context and citations
        updated_state = state.copy()
        updated_state["context"] = context
        updated_state["citations"] = citations
        return updated_state

    def _is_langextract_available(self) -> bool:
        """
        Check if LangExtract is available.
        Since we're using standard RAG without LangExtract, this always returns False.
        """
        return False

    def _extract_structured_info(self, raw_context: str) -> Dict[str, Any]:
        """
        Extract structured information from the retrieved context.
        Since LangExtract is not available, this returns a simple fallback.

        Args:
            raw_context: The raw retrieved context from vector search

        Returns:
            Dictionary containing structured extraction results
        """
        return {
            "structured_info": [],
            "error": "LangExtract not available - using standard RAG",
            "success": False
        }


    def _create_citations_from_search_results(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create citations directly from search results for faster processing.
        This avoids the slow LangExtract citation processing.

        Args:
            search_results: List of search result dictionaries

        Returns:
            List of citation dictionaries
        """
        citations = []
        for i, result in enumerate(search_results, 1):
            # Filter out localhost URLs
            url = result.get('url', '')
            if url and url.startswith(('http://localhost', 'http://127.0.0.1')):
                url = ''

            citation = {
                'id': str(i),
                'title': result.get('title', f'Source {i}'),
                'url': url,
                'source': result.get('source', 'Atlan Documentation'),
                'content_snippet': result.get('content', ''),
                'relevance_score': 0.8,  # Default relevance score
                'confidence_score': 0.75  # Default confidence score
            }
            citations.append(citation)

        return citations


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

