import asyncio
import os
import sys
from dotenv import load_dotenv

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database.mongodb_client import MongoDBClient
from database.qdrant_client import QdrantDBClient
from agents.classification_agent import ClassificationAgent
from agents.response_agent import ResponseAgent

async def check_mongodb():
    """Checks the connection to MongoDB."""
    print("Checking MongoDB connection...")
    client = None
    try:
        client = MongoDBClient()
        await client.connect()
        return "[OK]"
    except Exception as e:
        return f"[FAIL] - {e}"
    finally:
        if client:
            await client.close()

async def check_qdrant():
    """Checks the connection to Qdrant."""
    print("Checking Qdrant connection...")
    qdrant_host = os.getenv("QDRANT_HOST")
    if not qdrant_host or "your-qdrant-cluster-url" in qdrant_host:
        return "[SKIPPED] - QDRANT_HOST not configured."

    client = None
    try:
        client = QdrantDBClient()
        await client.verify_connection()
        return "[OK]"
    except Exception as e:
        return f"[FAIL] - {e}"
    finally:
        if client:
            await client.close()

async def check_gemini_flash():
    """Checks the connection to the Gemini Flash API."""
    print("Checking Gemini Flash (gemini-2.5-flash) API...")
    try:
        agent = ClassificationAgent()
        # A simple, non-empty input to test the API
        dummy_state = {"subject": "test", "body": "test"}
        result = await agent.execute(dummy_state)
        if result.get("classification"):
            return "[OK]"
        else:
            return "[FAIL] - API call did not return a valid classification."
    except Exception as e:
        return f"[FAIL] - {e}"

async def check_gemini_pro():
    """Checks the connection to the Gemini Pro API."""
    print("Checking Gemini Pro (gemini-2.5-flash) API...")
    try:
        agent = ResponseAgent()
        # A simple, non-empty input to test the API
        dummy_state = {"query": "test", "context": "test"}
        result = await agent.execute(dummy_state)
        # The agent returns a default error message on failure, so check for that
        if "Sorry, I encountered an error" not in result.get("response", ""):
            return "[OK]"
        else:
            return "[FAIL] - API call failed. Likely a rate limit issue."
    except Exception as e:
        return f"[FAIL] - {e}"

async def main():
    """Runs all health checks and prints a summary."""
    print("--- Running System Health Checks ---")
    load_dotenv(os.path.join(project_root, '.env'))

    # Run checks concurrently
    results = await asyncio.gather(
        check_mongodb(),
        check_qdrant(),
        check_gemini_flash(),
        check_gemini_pro()
    )

    mongodb_status, qdrant_status, flash_status, pro_status = results

    print("\n--- Health Check Summary ---")
    print(f"{'MongoDB Connection:'.ljust(30)} {mongodb_status}")
    print(f"{'Qdrant Connection:'.ljust(30)} {qdrant_status}")
    print(f"{'Gemini Flash API:'.ljust(30)} {flash_status}")
    print(f"{'Gemini Pro API:'.ljust(30)} {pro_status}")
    print("----------------------------")

if __name__ == "__main__":
    asyncio.run(main())
