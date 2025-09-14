import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), 'atlan_copilot'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.citation_handler import CitationHandler

def test_citation_handler():
    """Test the citation handler directly"""

    print("Testing Citation Handler...")

    handler = CitationHandler()

    # Test with sample context similar to what RAG agent produces
    sample_context = """Here is some context I found that might be relevant to your question:

--- Context Snippet 1 ---
Source: Atlan Documentation
URL: https://docs.atlan.com/integrations/aws-lambda
Title: AWS Lambda Integration Guide
Content: Atlan integrates with AWS Lambda to automate workflows and extend Atlan's capabilities, helping you to automate data workflows and streamline routine tasks.

--- Context Snippet 2 ---
Source: Atlan Documentation
URL: https://docs.atlan.com/integrations/automation/setup
Title: Integration Setup Guide
Content: For general integration setup, Atlan suggests a three-step process: 1. Select an integration. 2. Configure the connection by following the integration-specific setup guide. 3. Test and activate the integration.
"""

    sample_response = """Atlan integrates with AWS Lambda to automate workflows Source. The setup process involves a three-step process Source, Source."""

    print("Original context:")
    print(sample_context[:200] + "...")

    print("Original response:")
    print(sample_response)

    # Test the extract and process method
    result = handler.extract_and_process_citations(sample_response, sample_context)

    print(f"\nProcessed response with {len(result.sources)} sources:")
    print(result.text)

    print(f"\nSource details:")
    for i, source in enumerate(result.sources, 1):
        print(f"[{i}] {source.title}")
        print(f"   URL: {source.url}")
        print(f"   Snippet: {source.content_snippet[:100]}...")
        print()

if __name__ == "__main__":
    test_citation_handler()

