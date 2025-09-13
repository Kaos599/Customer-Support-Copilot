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
    sample_context = """
    ## Structured Information from Atlan Documentation

    ### Features
    - **AWS Lambda integration** [purpose: automate workflows, configuration_location: Settings > Integrations]
    - **data lineage tracking** [location: Assets > Lineage tab, requirement: admin permissions]

    ### Source Context
    --- Context Snippet 1 ---
    Source: docs.atlan.com
    URL: https://docs.atlan.com/product/integrations/automation
    Title: Automation Integrations | Atlan Documentation
    Content: Configure Atlan Integrations Automation Automation Integrations Integrate Atlan with automation tools such as AWS Lambda, Connections, Webhooks, Browser Exten...
    """

    query = "how can i use AWS lambda with atlan"

    print("Original context:")
    print(sample_context[:200] + "...")

    # Test citation creation
    cited_text, citations = handler.create_citations(sample_context, query)

    print(f"\nCreated {len(citations)} citations")
    print(f"\nCited text:")
    print(cited_text[:400] + "...")

    print(f"\nCitations details:")
    for citation in citations:
        print(f"[{citation['number']}] {citation['text'][:100]}...")
        print(f"   Source: {citation['source']}, URL: {citation['url']}")

if __name__ == "__main__":
    test_citation_handler()

