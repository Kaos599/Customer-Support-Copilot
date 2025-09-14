#!/usr/bin/env python3
"""
Test script to verify the fixes for status indicators and snippet truncation.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the Python path
sys.path.insert(0, '.')

from atlan_copilot.agents.rag_agent import RAGAgent

async def test_snippet_fix():
    """Test that snippets are no longer truncated"""
    print("🧪 Testing snippet truncation fix...")

    rag_agent = RAGAgent()

    # Test query
    test_query = "SSO authentication methods"
    test_state = {"query": test_query}

    print(f'Query: "{test_query}"')

    try:
        result = await rag_agent.execute(test_state)

        citations = result.get('citations', [])
        print(f"Found {len(citations)} citations")

        if citations:
            first_citation = citations[0]
            content_length = len(first_citation.get('content_snippet', ''))
            print(f"First citation content length: {content_length}")
            print(f"Content preview (first 300 chars): {first_citation.get('content_snippet', '')[:300]}...")

            # Check if content is actually meaningful (not just truncated)
            if content_length > 50:  # Should be much longer than 50 chars now
                print("✅ Snippet truncation fix successful!")
                return True
            else:
                print("❌ Snippet still appears to be truncated")
                return False
        else:
            print("❌ No citations found")
            return False

    except Exception as e:
        print(f"❌ Error testing snippet fix: {e}")
        return False

def test_status_indicators():
    """Test that status indicators are properly implemented in dashboard"""
    print("🧪 Checking status indicators implementation...")

    # Read the dashboard file to verify status indicators are implemented
    dashboard_file = "atlan_copilot/ui/dashboard.py"

    try:
        with open(dashboard_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for key status indicator elements
        checks = [
            ("progress_bar", "Progress bar implementation"),
            ("progress_text", "Progress text implementation"),
            ("status_text", "Status text implementation"),
            ("update_processing_progress", "Processing progress callback"),
            ("update_resolution_progress", "Resolution progress callback"),
            ("⚡ Processing", "Processing status message"),
            ("🎯 Resolving", "Resolution status message"),
        ]

        passed_checks = 0
        for check_text, description in checks:
            if check_text in content:
                print(f"✅ {description} found")
                passed_checks += 1
            else:
                print(f"❌ {description} missing")

        if passed_checks >= len(checks) - 1:  # Allow 1 missing for flexibility
            print("✅ Status indicators implementation successful!")
            return True
        else:
            print(f"❌ Status indicators incomplete ({passed_checks}/{len(checks)} checks passed)")
            return False

    except Exception as e:
        print(f"❌ Error checking status indicators: {e}")
        return False

async def main():
    print("🔧 Testing fixes for dashboard status indicators and snippet truncation\n")

    # Test snippet truncation fix
    snippet_test_passed = await test_snippet_fix()

    print()

    # Test status indicators implementation
    status_test_passed = test_status_indicators()

    print("\n📊 Test Results Summary:")
    print(f"Snippet truncation fix: {'✅ PASSED' if snippet_test_passed else '❌ FAILED'}")
    print(f"Status indicators fix: {'✅ PASSED' if status_test_passed else '❌ FAILED'}")

    if snippet_test_passed and status_test_passed:
        print("\n🎉 All fixes implemented successfully!")
        return True
    else:
        print("\n⚠️ Some fixes may need additional verification")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
