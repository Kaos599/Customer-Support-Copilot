import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the Python path
sys.path.insert(0, '.')

from atlan_copilot.agents.resolution_agent import ResolutionAgent

async def test_resolution_agent():
    print(f'QDRANT_HOST: {os.getenv("QDRANT_HOST")}')
    print(f'GOOGLE_API_KEY: {os.getenv("GOOGLE_API_KEY", "Not set")[:20]}...')

    # Test Resolution Agent with the example SSO ticket
    resolution_agent = ResolutionAgent()

    # Example ticket from the user's data
    test_ticket = {
        "id": "TICKET-262",
        "subject": "SSO login not assigning user to correct group",
        "body": "I've just had a new user, 'test.user@company.com', log in via our newly configured SSO. They were authenticated successfully, but they were not added to the 'Data Analysts' group as expected based on our SAML assertions. This is preventing them from accessing any assets. What could be the reason for this mis-assignment?",
        "classification": {
            "topic_tags": ["SSO"],
            "sentiment": "Neutral",
            "priority": "P0 (High)",
            "confidence_scores": {
                "topic": 1,
                "sentiment": 0.9,
                "priority": 1
            }
        },
        "processed": True,
        "status": "unprocessed"  # This should trigger resolution
    }

    print(f'Testing Resolution Agent with ticket: {test_ticket["subject"]}')

    try:
        # Test the resolution process
        result = await resolution_agent.execute({"ticket": test_ticket})

        print("Resolution Agent Results:")
        resolution_data = result.get('resolution', {})
        print(f"Status: {resolution_data.get('status', 'Unknown')}")
        print(f"Response length: {len(resolution_data.get('response', ''))}")
        print(f"Response preview: {resolution_data.get('response', '')[:500]}...")

        sources = resolution_data.get('sources', [])
        print(f"Number of sources: {len(sources)}")
        if sources:
            print(f"First source: {sources[0].get('name', 'Unknown')} - {sources[0].get('url', 'No URL')}")

        citations = resolution_data.get('citations', '')
        print(f"Citations: {citations[:200]}...")

    except Exception as e:
        print(f'Error testing Resolution agent: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_resolution_agent())
