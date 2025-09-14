import os
import sys
from typing import Dict, Any, List
import textwrap

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agents.base_agent import BaseAgent
from embeddings.gemini_embedder import GeminiEmbedder
from embeddings.similarity_search import SimilaritySearch
from utils.langextract_citation_handler import LangExtractCitationHandler

try:
    import langextract as lx
except ImportError:
    print("Warning: langextract not installed. Structured extraction will be disabled.")
    lx = None

class RAGAgent(BaseAgent):
    """
    Retrieval-Augmented Generation Agent with Structured Extraction.
    This agent takes a user query, retrieves relevant context from the vector store,
    uses LangExtract to structure the information with grounded sources,
    and adds it to the state for the next agent to use.
    """
    def __init__(self):
        super().__init__()
        self.embedder = GeminiEmbedder(model_name="models/text-embedding-004")
        self.search_client = SimilaritySearch()
        self.citation_handler = LangExtractCitationHandler(os.getenv("GOOGLE_API_KEY", ""))

        # LangExtract configuration
        self.extraction_prompt = textwrap.dedent("""\
            Extract key information from Atlan documentation and support content.
            Focus on:
            - Technical concepts, features, and capabilities
            - Configuration steps and setup instructions
            - Troubleshooting information and solutions
            - API endpoints, parameters, and usage examples
            - Integration details and requirements
            - Important URLs and documentation links
            - Version-specific information and limitations

            Extract entities with their exact text and provide meaningful context.
            Ensure all extractions are grounded to their source locations.
        """)

        # Define examples for the extraction task
        self.extraction_examples = [
            lx.data.ExampleData(
                text="Atlan integrates with AWS Lambda to automate workflows and extend Atlan's capabilities. Configure integrations through the Atlan UI under Settings > Integrations.",
                extractions=[
                    lx.data.Extraction(
                        extraction_class="feature",
                        extraction_text="AWS Lambda integration",
                        attributes={
                            "purpose": "automate workflows",
                            "configuration_location": "Settings > Integrations"
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="integration",
                        extraction_text="AWS Lambda",
                        attributes={
                            "type": "automation tool",
                            "benefit": "extend Atlan's capabilities"
                        }
                    )
                ]
            ) if lx else None,
            lx.data.ExampleData(
                text="To set up data lineage tracking, navigate to Assets > Lineage tab and enable the lineage feature. This requires admin permissions.",
                extractions=[
                    lx.data.Extraction(
                        extraction_class="feature",
                        extraction_text="data lineage tracking",
                        attributes={
                            "location": "Assets > Lineage tab",
                            "requirement": "admin permissions"
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="action",
                        extraction_text="enable the lineage feature",
                        attributes={
                            "prerequisite": "navigate to Assets > Lineage tab"
                        }
                    )
                ]
            ) if lx else None
        ]

        # Filter out None examples if lx is not available
        self.extraction_examples = [ex for ex in self.extraction_examples if ex is not None]

    def _is_langextract_available(self) -> bool:
        """Check if LangExtract is available and properly configured."""
        if lx is None:
            return False

        # Check if GOOGLE_API_KEY is set
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("Warning: GOOGLE_API_KEY not set for LangExtract")
            return False

        return True

    def _extract_structured_info(self, raw_context: str) -> Dict[str, Any]:
        """
        Extract structured information from the retrieved context using LangExtract.

        Args:
            raw_context: The raw retrieved context from vector search

        Returns:
            Dictionary containing structured extraction results
        """
        if not self._is_langextract_available():
            return {
                "structured_info": [],
                "error": "LangExtract not available or not configured",
                "success": False
            }

        try:
            print("--- Running LangExtract for structured information extraction ---")

            # Run extraction with LangExtract (optimized for speed)
            result = lx.extract(
                text_or_documents=raw_context,
                prompt_description=self.extraction_prompt,
                examples=self.extraction_examples[:1],  # Use only first example for speed
                model_id="gemini-2.5-flash",  # Use faster model
                api_key=os.getenv("GOOGLE_API_KEY"),
                extraction_passes=1,  # Single pass for speed
                max_workers=1,  # Single worker
                max_char_buffer=2000  # Smaller buffer for faster processing
            )

            # Process the results
            structured_info = []
            if result and hasattr(result, 'extractions'):
                for extraction in result.extractions:
                    structured_info.append({
                        "class": extraction.extraction_class,
                        "text": extraction.extraction_text,
                        "attributes": extraction.attributes or {},
                        "start_char": extraction.start_char if hasattr(extraction, 'start_char') else None,
                        "end_char": extraction.end_char if hasattr(extraction, 'end_char') else None
                    })

            return {
                "structured_info": structured_info,
                "extraction_count": len(structured_info),
                "success": True
            }

        except Exception as e:
            print(f"Error during LangExtract processing: {e}")
            return {
                "structured_info": [],
                "error": f"LangExtract processing failed: {str(e)}",
                "success": False
            }

    def _format_structured_context(self, raw_context: str, extraction_result: Dict[str, Any]) -> str:
        """
        Format the raw context and structured extraction results into a comprehensive context string.

        Args:
            raw_context: Original retrieved context
            extraction_result: Structured extraction results from LangExtract

        Returns:
            Formatted context string with both structured and raw information
        """
        if not extraction_result.get("success", False) or not extraction_result.get("structured_info"):
            # Fallback to original formatting if extraction fails
            return self._format_context([]) if raw_context.startswith("No relevant") else raw_context

        structured_info = extraction_result["structured_info"]
        context_parts = ["## Structured Information from Atlan Documentation\n"]

        # Group extractions by class for better organization
        grouped = {}
        for info in structured_info:
            class_name = info["class"]
            if class_name not in grouped:
                grouped[class_name] = []
            grouped[class_name].append(info)

        # Format each group
        for class_name, items in grouped.items():
            context_parts.append(f"### {class_name.title()}s")
            for item in items:
                context_parts.append(f"- **{item['text']}**")
                if item.get("attributes"):
                    for attr_key, attr_value in item["attributes"].items():
                        context_parts.append(f"  - {attr_key}: {attr_value}")
                context_parts.append("")

        # Add the original formatted context as additional reference
        context_parts.append("### Source Context")
        context_parts.append(raw_context)

        return "\n".join(context_parts)

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
                'content_snippet': result.get('content', '')[:200] + '...' if result.get('content') and len(result.get('content', '')) > 200 else result.get('content', ''),
                'relevance_score': 0.8,  # Default relevance score
                'confidence_score': 0.75  # Default confidence score
            }
            citations.append(citation)

        return citations

    def _format_structured_context_with_citations(self, raw_context: str, extraction_result: Dict[str, Any], citations: List[Dict[str, Any]]) -> str:
        """
        Format context with citations for the response generation.

        Args:
            raw_context: Original retrieved context
            extraction_result: Structured extraction results from LangExtract
            citations: Formatted citations

        Returns:
            Formatted context string with citations
        """
        context_parts = []

        # Add structured information if available
        if extraction_result.get("success", False) and extraction_result.get("structured_info"):
            structured_info = extraction_result["structured_info"]
            context_parts.append("## Structured Information from Atlan Documentation\n")

            # Group extractions by class for better organization
            grouped = {}
            for info in structured_info:
                class_name = info["class"]
                if class_name not in grouped:
                    grouped[class_name] = []
                grouped[class_name].append(info)

            # Format each group with citation markers
            citation_num = 1
            for class_name, items in grouped.items():
                context_parts.append(f"### {class_name.title()}s")
                for item in items:
                    context_parts.append(f"- **{item['text']}** [{citation_num}]")
                    if item.get("attributes"):
                        for attr_key, attr_value in item["attributes"].items():
                            context_parts.append(f"  - {attr_key}: {attr_value}")
                    context_parts.append("")
                    citation_num += 1

        # Add the original formatted context with citation markers
        context_parts.append("### Source Context")
        context_parts.append(raw_context)

        return "\n".join(context_parts)

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

            raw_context = self._format_context(all_results)

            # 3. Create optimized citations from search results (faster than LangExtract)
            citations = self._create_citations_from_search_results(all_results)

            # 4. Extract structured information using LangExtract (only once)
            extraction_result = self._extract_structured_info(raw_context)

            # 5. Format the structured context with citations
            structured_context = self._format_structured_context_with_citations(raw_context, extraction_result, citations)

        print(f"Retrieved context: {structured_context[:400]}...")
        if extraction_result.get("success"):
            print(f"Successfully extracted {extraction_result.get('extraction_count', 0)} structured entities")
        print(f"Created {len(citations)} citations")

        # Note: Don't close the search client connection here to avoid premature closing
        # The connection will be managed by the Qdrant client's singleton pattern

        # 7. Update the state with the structured cited context and metadata
        updated_state = state.copy()
        updated_state["context"] = structured_context
        updated_state["citations"] = citations
        updated_state["extraction_metadata"] = {
            "extraction_count": extraction_result.get("extraction_count", 0),
            "success": extraction_result.get("success", False),
            "error": extraction_result.get("error"),
            "citation_count": len(citations)
        }
        return updated_state
