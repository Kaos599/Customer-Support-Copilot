import os
import sys
from typing import Dict, Any, List
import textwrap

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agents.base_agent import BaseAgent

try:
    import langextract as lx
except ImportError:
    print("Warning: langextract not installed. Extraction agent will be disabled.")
    lx = None

class ExtractionAgent(BaseAgent):
    """
    Structured Information Extraction Agent.
    Uses LangExtract to extract structured information from retrieved context,
    ensuring sources are always grounded and information is properly structured.
    """

    def __init__(self):
        super().__init__()
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

    def _extract_structured_info(self, context: str) -> Dict[str, Any]:
        """
        Extract structured information from the retrieved context using LangExtract.

        Args:
            context: The retrieved context from RAG search

        Returns:
            Dictionary containing structured extraction results
        """
        if not self._is_langextract_available():
            return {
                "structured_info": [],
                "error": "LangExtract not available or not configured",
                "raw_context": context
            }

        try:
            print("--- Running LangExtract for structured information extraction ---")

            # Run extraction with LangExtract
            result = lx.extract(
                text_or_documents=context,
                prompt_description=self.extraction_prompt,
                examples=self.extraction_examples,
                model_id="gemini-2.5-flash",  # Using the same model as other agents
                api_key=os.getenv("GOOGLE_API_KEY")
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
                "raw_context": context,
                "success": True
            }

        except Exception as e:
            print(f"Error during LangExtract processing: {e}")
            return {
                "structured_info": [],
                "error": f"LangExtract processing failed: {str(e)}",
                "raw_context": context,
                "success": False
            }

    def _format_structured_context(self, extraction_result: Dict[str, Any]) -> str:
        """
        Format the structured extraction results into a readable context string.

        Args:
            extraction_result: The result from LangExtract processing

        Returns:
            Formatted context string with structured information
        """
        if not extraction_result.get("success", False) or not extraction_result.get("structured_info"):
            return extraction_result.get("raw_context", "No context available")

        context_parts = ["## Structured Information Extracted from Sources\n"]

        structured_info = extraction_result["structured_info"]

        # Group extractions by class
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

        # Add original context as fallback
        context_parts.append("### Original Context\n")
        context_parts.append(extraction_result.get("raw_context", ""))

        return "\n".join(context_parts)

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute structured information extraction on the retrieved context.

        Args:
            state: Current copilot state containing retrieved context

        Returns:
            Updated state with structured context
        """
        print("--- Executing Extraction Agent ---")

        raw_context = state.get("context", "")
        if not raw_context or raw_context.startswith("Error:") or raw_context.startswith("No relevant"):
            print("No valid context to extract from, skipping extraction")
            updated_state = state.copy()
            updated_state["structured_context"] = raw_context
            return updated_state

        # Extract structured information
        extraction_result = self._extract_structured_info(raw_context)

        # Format the structured context
        structured_context = self._format_structured_context(extraction_result)

        print(f"Extracted {extraction_result.get('extraction_count', 0)} structured entities")

        # Update state with structured context
        updated_state = state.copy()
        updated_state["structured_context"] = structured_context
        updated_state["extraction_metadata"] = {
            "extraction_count": extraction_result.get("extraction_count", 0),
            "success": extraction_result.get("success", False),
            "error": extraction_result.get("error")
        }

        return updated_state

