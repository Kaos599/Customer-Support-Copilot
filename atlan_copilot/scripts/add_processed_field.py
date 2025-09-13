import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path for absolute imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database.mongodb_client import MongoDBClient

async def add_processed_field():
    """
    Add the 'processed' field with default value false to all existing tickets
    that don't have this field.
    """
    print("--- Adding 'processed' field to existing tickets ---")

    # Load environment variables from the root .env file
    dotenv_path = os.path.join(project_root, '..', '.env')
    load_dotenv(dotenv_path=dotenv_path)

    # Initialize MongoDB client
    mongo_client = None
    try:
        mongo_client = MongoDBClient()
        await mongo_client.connect()

        # Get all tickets
        all_tickets = await mongo_client.get_all_tickets()
        print(f"Found {len(all_tickets)} tickets in database")

        # Count tickets that need the processed field added
        tickets_without_processed = [t for t in all_tickets if 'processed' not in t]
        print(f"{len(tickets_without_processed)} tickets need the 'processed' field added")

        if tickets_without_processed:
            # Add processed=false to all tickets that don't have it
            result = await mongo_client.collection.update_many(
                {"processed": {"$exists": False}},  # Only update documents that don't have the field
                {"$set": {"processed": False}}
            )

            print(f"✅ Updated {result.modified_count} tickets to add 'processed: false' field")

            # Verify the update
            updated_stats = await mongo_client.get_processing_stats()
            print("Updated statistics:")
            print(f"  Total tickets: {updated_stats.get('total_tickets', 0)}")
            print(f"  Processed tickets: {updated_stats.get('total_processed', 0)}")
            print(f"  Unprocessed tickets: {updated_stats.get('total_unprocessed', 0)}")
        else:
            print("✅ All tickets already have the 'processed' field")

    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if mongo_client:
            await mongo_client.close()

    print("\n--- Processed field addition complete ---")

if __name__ == "__main__":
    asyncio.run(add_processed_field())
