import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path to allow for absolute imports
# This allows us to run this script directly
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from database.mongodb_client import MongoDBClient
from database.qdrant_client import QdrantDBClient

async def main():
    """
    Main asynchronous function to initialize and test database connections.
    """
    print("--- Testing Database Connections ---")

    # Load environment variables from the .env file in the project root
    dotenv_path = os.path.join(project_root, '.env')
    if not os.path.exists(dotenv_path):
        print(f"Error: .env file not found at {dotenv_path}")
        return
    load_dotenv(dotenv_path=dotenv_path)

    # --- Test MongoDB Connection ---
    mongo_client = None
    print("\n[1/2] Testing MongoDB connection...")
    try:
        mongo_client = MongoDBClient()
        await mongo_client.connect()
        print("✅ MongoDB connection test PASSED.")
    except Exception as e:
        print(f"❌ MongoDB connection test FAILED: {e}")
        print("   Please check your MONGO_URI and ensure the IP is whitelisted in MongoDB Atlas.")
    finally:
        if mongo_client:
            await mongo_client.close()

    # --- Test Qdrant Connection ---
    qdrant_client = None
    print("\n[2/2] Testing Qdrant connection...")
    qdrant_host = os.getenv("QDRANT_HOST")

    if not qdrant_host or "your-qdrant-cluster-url" in qdrant_host:
        print("⚠️  QDRANT_HOST is not set or is a placeholder. Skipping Qdrant connection test.")
        print("   To run this test, please update QDRANT_HOST in your .env file.")
    else:
        try:
            qdrant_client = QdrantDBClient()
            await qdrant_client.verify_connection()
            print("✅ Qdrant connection test PASSED.")
        except Exception as e:
            print(f"❌ Qdrant connection test FAILED: {e}")
            print("   Please check your QDRANT_HOST and QDRANT_API_KEY.")
        finally:
            if qdrant_client:
                await qdrant_client.close()

    print("\n--- Connection Tests Complete ---")

if __name__ == "__main__":
    # This allows the script to be run directly
    asyncio.run(main())
