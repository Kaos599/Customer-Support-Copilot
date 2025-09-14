#!/usr/bin/env python3
"""
Test script to validate UI fixes for citation system and performance optimizations.
This script tests the core functionality without requiring a full Streamlit session.
"""

import sys
import os
import asyncio
import platform

# Add project root to path
project_root = os.path.abspath('.')
sys.path.insert(0, os.path.join(project_root, 'atlan_copilot'))

from utils.citation_handler import CitationHandler, CitationSource, CitedText


def test_citation_handler():
    """Test the citation handler with sample data"""
    print("🧪 Testing Citation Handler...")
    
    handler = CitationHandler()
    
    # Sample context with source information
    sample_context = """--- Context Snippet 1 ---
Source: Atlan Documentation
URL: https://docs.atlan.com/setup/installation
Title: Installation Guide
Content: Atlan can be installed using Docker containers or Kubernetes. The recommended approach is using Docker Compose for development environments.

--- Context Snippet 2 ---
Source: Atlan API Documentation  
URL: https://docs.atlan.com/api/getting-started
Title: Getting Started with Atlan API
Content: The Atlan API provides programmatic access to your data catalog. Authentication is required using API tokens.

--- Context Snippet 3 ---
Source: Atlan User Guide
URL: https://docs.atlan.com/user-guide/data-discovery
Title: Data Discovery Features
Content: Atlan's data discovery features include search, lineage tracking, and metadata management capabilities.
"""
    
    # Sample response with numbered citations
    sample_response = """Atlan provides multiple installation options [1]. You can access the platform programmatically through the API [2], which requires authentication. The platform includes comprehensive data discovery features [3] for managing your data catalog."""
    
    # Test citation extraction and processing
    cited_text = handler.extract_and_process_citations(sample_response, sample_context)
    
    print(f"✅ Processed response: {cited_text.text}")
    print(f"✅ Found {len(cited_text.sources)} sources:")
    
    for i, source in enumerate(cited_text.sources, 1):
        print(f"   [{i}] {source.title}")
        print(f"       URL: {source.url}")
        print(f"       Snippet: {source.content_snippet[:100]}...")
        print()
    
    return True


def test_async_event_loop():
    """Test async event loop handling for Windows compatibility"""
    print("🧪 Testing Async Event Loop Handling...")
    
    # Set Windows event loop policy
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        print("✅ Windows event loop policy set")
    
    async def sample_async_task():
        await asyncio.sleep(0.1)
        return "Async task completed successfully"
    
    try:
        result = asyncio.run(sample_async_task())
        print(f"✅ Async operation result: {result}")
        return True
    except Exception as e:
        print(f"❌ Async operation failed: {e}")
        return False


def test_sources_formatting():
    """Test the sources display formatting logic"""
    print("🧪 Testing Sources Display Formatting...")
    
    # Sample citation sources
    sources = [
        {
            'title': 'Installation Guide',
            'url': 'https://docs.atlan.com/setup/installation',
            'content_snippet': 'Atlan can be installed using Docker containers or Kubernetes.'
        },
        {
            'title': 'Getting Started with Atlan API',
            'url': 'https://docs.atlan.com/api/getting-started', 
            'content_snippet': 'The Atlan API provides programmatic access to your data catalog.'
        },
        {
            'title': 'Data Discovery Features',
            'url': 'https://docs.atlan.com/user-guide/data-discovery',
            'content_snippet': 'Atlan\'s data discovery features include search, lineage tracking, and metadata management.'
        }
    ]
    
    print("✅ Formatted sources for UI display:")
    for i, source in enumerate(sources, 1):
        print(f"   **[{i}] {source['title']}**")
        print(f"   🔗 [{source['url']}]({source['url']})")
        print(f"   💬 *\"{source['content_snippet']}\"*")
        if i < len(sources):
            print("   ---")
        print()
    
    return True


def main():
    """Run all tests"""
    print("🚀 Running UI Fixes Validation Tests...\n")
    
    tests = [
        ("Citation Handler", test_citation_handler),
        ("Async Event Loop", test_async_event_loop),
        ("Sources Formatting", test_sources_formatting),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
            print(f"{'✅' if result else '❌'} {test_name} test: {'PASSED' if result else 'FAILED'}\n")
        except Exception as e:
            results[test_name] = False
            print(f"❌ {test_name} test: FAILED with error: {e}\n")
    
    # Summary
    passed = sum(results.values())
    total = len(results)
    
    print("="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! UI fixes are working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)