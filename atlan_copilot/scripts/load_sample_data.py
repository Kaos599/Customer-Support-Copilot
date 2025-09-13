import asyncio
import json
import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path for absolute imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ..database.mongodb_client import MongoDBClient

async def main():
    """
    Connects to MongoDB and loads the sample ticket data from the
    `data/sample_tickets.json` file into the specified collection.
    """
    print("--- Starting Sample Data Loading Script ---")

    # Load environment variables from the root .env file
    dotenv_path = os.path.join(project_root, '.env')
    load_dotenv(dotenv_path=dotenv_path)

    # 1. Read the sample tickets from the JSON file
    try:
        tickets_path = os.path.join(project_root, 'data', 'sample_tickets.json')
        with open(tickets_path, 'r') as f:
            sample_tickets = json.load(f)
        print(f"Successfully loaded {len(sample_tickets)} tickets from the JSON file.")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error: Could not read or parse sample_tickets.json: {e}")
        return

    if not sample_tickets:
        print("Warning: No tickets found in the JSON file. Nothing to load.")
        return

    # 2. Initialize client and insert data into MongoDB
    mongo_client = None
    try:
        mongo_client = MongoDBClient()
        await mongo_client.connect()

        # For idempotency, we can clear the collection before inserting.
        # This is useful for re-running the script.
        # count = await mongo_client.collection.count_documents({})
        # if count > 0:
        #     print(f"Deleting {count} existing documents from the collection...")
        #     await mongo_client.collection.delete_many({})

        print(f"Inserting {len(sample_tickets)} tickets into the '{mongo_client.mongo_collection_name}' collection...")
        inserted_ids = await mongo_client.insert_tickets(sample_tickets)

        if inserted_ids:
            print(f"✅ Successfully inserted {len(inserted_ids)} documents into MongoDB.")
        else:
            print("❌ Data insertion failed. The client might have logged more details.")

    except Exception as e:
        print(f"An error occurred during the database operation: {e}")
    finally:
        if mongo_client:
            await mongo_client.close()

    print("\n--- Data Loading Script Complete ---")

if __name__ == "__main__":
    asyncio.run(main())
