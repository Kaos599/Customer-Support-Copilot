import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path for absolute imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database.mongodb_client import MongoDBClient

async def migrate_to_unified_schema():
    """
    Migrates from dual-collection architecture (tickets + tickets_processed)
    to unified schema where all data is stored in the tickets collection.
    """
    print("--- Starting Migration to Unified Schema ---")

    # Load environment variables from the root .env file
    dotenv_path = os.path.join(project_root, '.env')
    load_dotenv(dotenv_path=dotenv_path)

    # Initialize MongoDB client
    mongo_client = None
    try:
        mongo_client = MongoDBClient()
        await mongo_client.connect()

        # Check if processed collection exists
        processed_collection_name = os.getenv("MONGO_COLLECTION_PROCESSED", "tickets_processed")
        db = mongo_client.db

        # Get all processed tickets
        processed_collection = db[processed_collection_name]
        processed_count = await processed_collection.count_documents({})
        print(f"Found {processed_count} processed tickets to migrate")

        if processed_count == 0:
            print("No processed tickets found. Migration may already be complete.")
            return

        # Migrate each processed ticket
        migrated_count = 0
        skipped_count = 0

        async for processed_ticket in processed_collection.find({}):
            ticket_id = processed_ticket.get("ticket_id") or processed_ticket.get("original_ticket_id")

            if not ticket_id:
                print(f"⚠️  Skipping processed ticket without ID: {processed_ticket.get('_id')}")
                skipped_count += 1
                continue

            # Check if ticket already exists in main collection
            existing_ticket = await mongo_client.collection.find_one({"id": ticket_id})

            if existing_ticket:
                # Update existing ticket with processed data
                update_data = {
                    "processed": True,
                    "classification": processed_ticket.get("classification", {}),
                    "confidence_scores": processed_ticket.get("confidence_scores", {}),
                    "processing_metadata": processed_ticket.get("processing_metadata", {}),
                    "updated_at": processed_ticket.get("updated_at", processed_ticket.get("processing_metadata", {}).get("processed_at"))
                }

                success = await mongo_client.collection.update_one(
                    {"id": ticket_id},
                    {"$set": update_data}
                )

                if success.modified_count > 0:
                    print(f"✅ Migrated ticket: {ticket_id}")
                    migrated_count += 1
                else:
                    print(f"⚠️  Failed to update ticket: {ticket_id}")
                    skipped_count += 1
            else:
                # Create new ticket document with processed data
                new_ticket = {
                    "id": ticket_id,
                    "subject": processed_ticket.get("subject", ""),
                    "body": processed_ticket.get("body", ""),
                    "processed": True,
                    "classification": processed_ticket.get("classification", {}),
                    "confidence_scores": processed_ticket.get("confidence_scores", {}),
                    "processing_metadata": processed_ticket.get("processing_metadata", {}),
                    "created_at": processed_ticket.get("created_at", processed_ticket.get("processing_metadata", {}).get("processed_at")),
                    "updated_at": processed_ticket.get("updated_at", processed_ticket.get("processing_metadata", {}).get("processed_at"))
                }

                result = await mongo_client.collection.insert_one(new_ticket)
                if result.inserted_id:
                    print(f"✅ Created new ticket from processed data: {ticket_id}")
                    migrated_count += 1
                else:
                    print(f"⚠️  Failed to create ticket: {ticket_id}")
                    skipped_count += 1

        # Update any existing tickets that don't have the processed field
        result = await mongo_client.collection.update_many(
            {"processed": {"$exists": False}},
            {"$set": {"processed": False}}
        )
        print(f"✅ Added processed=false to {result.modified_count} existing tickets without the field")

        print("
--- Migration Summary ---")
        print(f"Migrated tickets: {migrated_count}")
        print(f"Skipped tickets: {skipped_count}")
        print(f"Total processed: {processed_count}")

        # Ask user if they want to drop the processed collection
        response = input(f"\nDrop the '{processed_collection_name}' collection? (y/N): ").lower().strip()
        if response == 'y' or response == 'yes':
            await db.drop_collection(processed_collection_name)
            print(f"✅ Dropped collection: {processed_collection_name}")
        else:
            print(f"ℹ️  Kept collection: {processed_collection_name}")

        # Verify migration by checking stats
        stats = await mongo_client.get_processing_stats()
        print("
--- Post-Migration Stats ---")
        print(f"Total tickets: {stats.get('total_tickets', 0)}")
        print(f"Processed tickets: {stats.get('total_processed', 0)}")
        print(f"Unprocessed tickets: {stats.get('total_unprocessed', 0)}")

    except Exception as e:
        print(f"An error occurred during migration: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if mongo_client:
            await mongo_client.close()

    print("\n--- Migration Complete ---")

if __name__ == "__main__":
    asyncio.run(migrate_to_unified_schema())

