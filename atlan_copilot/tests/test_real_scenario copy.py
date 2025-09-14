#!/usr/bin/env python3
"""
Test the real scenario that the user is experiencing.
"""

import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), 'atlan_copilot'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.citation_handler import CitationHandler

def test_real_user_scenario():
    """Test with the exact response the user is getting."""
    handler = CitationHandler()
    
    # This is the exact response the user reported
    user_response = """Atlan integrates with AWS Lambda as an automation tool to help automate workflows and extend Atlan's capabilities [1, 2]. This integration can be used to automate data workflows and streamline routine tasks [2]. To use AWS Lambda with Atlan: 1. Configure the necessary AWS Lambda permissions [3]. 2. Once permissions are configured, you can create an AWS Lambda trigger to run an AWS Lambda function [3]. Generally, the process for getting started with Atlan integrations involves selecting the integration, configuring the connection, and then testing and activating it [2]."""
    
    # Mock context that might have generated this response
    mock_context = """Here is some context I found that might be relevant to your question:

--- Context Snippet 1 ---
Source: Atlan Documentation
URL: https://docs.atlan.com/integrations/aws-lambda
Title: AWS Lambda Integration Guide
Content: Atlan integrates with AWS Lambda as an automation tool to help automate workflows and extend Atlan's capabilities.

--- Context Snippet 2 ---
Source: Atlan Documentation
URL: https://docs.atlan.com/integrations/automation/setup
Title: Integration Setup Process
Content: This integration can be used to automate data workflows and streamline routine tasks. Generally, the process for getting started with Atlan integrations involves selecting the integration, configuring the connection, and then testing and activating it.

--- Context Snippet 3 ---
Source: Atlan Developer Docs
URL: https://docs.atlan.com/product/integrations/automation/aws-lambda/permissions
Title: AWS Lambda Permissions
Content: Configure the necessary AWS Lambda permissions. Once permissions are configured, you can create an AWS Lambda trigger to run an AWS Lambda function.
"""
    
    print("Testing Real User Scenario...")
    print("=" * 50)
    print(f"Original response: {user_response}")
    print()
    
    # Test the citation extraction
    result = handler.extract_and_process_citations(user_response, mock_context)
    
    print(f"Citation processing result:")
    print(f"- Sources found: {len(result.sources)}")
    print(f"- Processed text: {result.text}")
    print()
    
    print("Source details:")
    for i, source in enumerate(result.sources, 1):
        print(f"[{i}] {source.title}")
        print(f"    URL: {source.url}")
        print(f"    Snippet: {source.content_snippet}")
        print()
    
    # Simulate what should be in the Streamlit metadata
    citation_sources = [source.to_dict() for source in result.sources]
    print(f"Citation sources for UI: {len(citation_sources)} items")
    
    for i, source_dict in enumerate(citation_sources, 1):
        print(f"  [{i}] {source_dict}")
    
    return result

if __name__ == "__main__":
    test_real_user_scenario()