import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the Python path
sys.path.insert(0, '.')

from atlan_copilot.agents.rag_agent import RAGAgent

async def test_rag_agent():
    print(f'QDRANT_HOST: {os.getenv("QDRANT_HOST")}')
    print(f'GOOGLE_API_KEY: {os.getenv("GOOGLE_API_KEY", "Not set")[:20]}...')

    # Test RAG agent
    rag_agent = RAGAgent()

    # Test query
    test_query = "SSO login not assigning user to correct group"
    test_state = {"query": test_query}

    print(f'Testing RAG agent with query: "{test_query}"')

    try:
        result = await rag_agent.execute(test_state)

        print("RAG Agent Results:")
        print(f"Context length: {len(result.get('context', ''))}")
        print(f"Context preview: {result.get('context', '')[:500]}...")

        citations = result.get('citations', [])
        print(f"Number of citations: {len(citations)}")

        if citations:
            print("First citation:")
            citation = citations[0]
            print(f"  ID: {citation.get('id')}")
            print(f"  Title: {citation.get('title')}")
            print(f"  URL: {citation.get('url')}")
            print(f"  Source: {citation.get('source')}")
            print(f"  Content snippet length: {len(citation.get('content_snippet', ''))}")
            print(f"  Content snippet preview: {citation.get('content_snippet', '')[:200]}...")

    except Exception as e:
        print(f'Error testing RAG agent: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_rag_agent())
