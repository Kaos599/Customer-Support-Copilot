#!/usr/bin/env python3
"""
Test script to verify the citation system is working properly after fixes
"""
import os
import sys
import asyncio
import platform

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), 'atlan_copilot'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Set event loop policy for Windows
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

async def test_citation_system():
    """Test the citation system with mock data"""
    
    try:
        from utils.citation_handler import CitationHandler
        from agents.response_agent import ResponseAgent
        
        print("🔍 Testing Citation System...")
        
        # Mock context similar to what RAG agent provides
        mock_context = """--- Context Snippet 1 ---
Source: docs.atlan.com
URL: https://docs.atlan.com/product/integrations/automation
Title: Automation Integrations | Atlan Documentation
Content: Configure Atlan Integrations Automation Automation Integrations Integrate Atlan with automation tools such as AWS Lambda, Connections, Webhooks, Browser Extensions, and more.

--- Context Snippet 2 ---
Source: docs.atlan.com
URL: https://docs.atlan.com/product/integrations/automation/aws-lambda
Title: AWS Lambda Integration Setup
Content: To use AWS Lambda with Atlan, you need to configure the necessary AWS Lambda permissions and create triggers for workflow automation.

--- Context Snippet 3 ---
Source: docs.atlan.com
URL: https://docs.atlan.com/product/integrations/setup
Title: Integration Setup Guide
Content: Generally, Atlan integrations involve selecting the integration, configuring the connection, and then testing and activating it for your use case."""
        
        # Mock response with numbered citations (similar to what Gemini generates)
        mock_response = "Atlan integrates with AWS Lambda as an automation tool to automate workflows and extend Atlan's capabilities [1, 2]. These integrations connect your data catalog with the tools your teams already use [2]. To use AWS Lambda with Atlan: 1. Configure the necessary AWS Lambda permissions [3]. 2. Once permissions are configured, you can create an AWS Lambda trigger to run an AWS Lambda function [3]. Generally, Atlan integrations involve selecting the integration, configuring the connection, and then testing and activating it [2]."
        
        # Test citation handler
        citation_handler = CitationHandler()
        cited_text = citation_handler.extract_and_process_citations(mock_response, mock_context)
        
        print(f"✅ Citation processing successful!")
        print(f"📝 Response text: {cited_text.text[:100]}...")
        print(f"📚 Found {len(cited_text.sources)} sources:")
        
        for i, source in enumerate(cited_text.sources, 1):
            print(f"   [{i}] {source.title}")
            print(f"       URL: {source.url}")
            print(f"       Snippet: {source.content_snippet[:100]}...")
            print()
        
        # Format for UI display
        ui_sources = []
        for i, source in enumerate(cited_text.sources, 1):
            formatted_source = {
                "number": i,
                "id": str(i),
                "title": source.title,
                "url": source.url if not any(invalid in source.url.lower() for invalid in ['localhost', '127.0.0.1', 'local:', 'file://']) else "Internal Document",
                "source": source.source,
                "content_snippet": source.content_snippet,
                "confidence_score": 0.85
            }
            ui_sources.append(formatted_source)
        
        print("🎨 UI Display Format:")
        for source in ui_sources:
            print(f"   [{source['number']}] {source['title']}")
            print(f"       🔗 {source['url']}")
            print(f"       💬 \"{source['content_snippet'][:100]}...\"")
            print(f"       📊 Confidence: {source['confidence_score']:.1%}")
            print()
        
        print("✅ Citation system test completed successfully!")
        
    except Exception as e:
        print(f"❌ Citation system test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_citation_system())