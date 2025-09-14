import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the Python path
sys.path.insert(0, '.')

from atlan_copilot.agents.response_agent import ResponseAgent

async def test_response_agent():
    print(f'GOOGLE_API_KEY: {os.getenv("GOOGLE_API_KEY", "Not set")[:20]}...')

    # Test Response Agent
    response_agent = ResponseAgent()

    # Use the same context that RAG agent produced
    test_context = """Here is some context I found that might be relevant to your question:

--- Context Snippet [1] ---
Source: docs.atlan.com
URL: https://docs.atlan.com/tags/connectors
Title: 299 docs tagged with "connectors" | Atlan Documentation
Content: Enable JumpCloud for SSO SSO group mappings are triggered every time a user authenticates in Atlan. A user may need to log out and then log into Atlan again to view the changes. If a user is added to a new group or removed from an existing one in JumpCloud, the group mapping will be updated accordingly. For Azure AD, group memberships are synchronized during each login. The synchronization process ensures that users have the correct group assignments based on their directory group membership.

--- Context Snippet [2] ---
Source: docs.atlan.com
URL: https://docs.atlan.com/product/integrations
Title: Integrations | Atlan Documentation
Content: SSO Configuration Atlan supports various SSO providers including Okta, Azure AD, and JumpCloud. When configuring SSO, ensure that group mappings are properly set up in your identity provider. The group mapping configuration determines which Atlan groups users are assigned to based on their directory groups."""

    test_query = "SSO login not assigning user to correct group"
    test_state = {
        "query": test_query,
        "context": test_context,
        "citations": [
            {
                "id": "1",
                "title": "299 docs tagged with \"connectors\" | Atlan Documentation",
                "url": "https://docs.atlan.com/tags/connectors",
                "source": "docs.atlan.com",
                "content_snippet": "Enable JumpCloud for SSO SSO group mappings are triggered every time a user authenticates in Atlan...",
                "relevance_score": 0.8,
                "confidence_score": 0.75
            }
        ]
    }

    print(f'Testing Response Agent with query: "{test_query}"')
    print(f'Context length: {len(test_context)}')

    try:
        result = await response_agent.execute(test_state)

        print("Response Agent Results:")
        response = result.get('response', '')
        print(f"Response length: {len(response)}")
        print(f"Response: {response}")

    except Exception as e:
        print(f'Error testing Response agent: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_response_agent())
