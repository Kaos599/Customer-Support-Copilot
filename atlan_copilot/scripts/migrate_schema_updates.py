#!/usr/bin/env python3
"""
Migration script to update MongoDB schema for ticket system enhancements.

This script:
1. Adds 'status' field to all tickets (unprocessed/processed/resolved)
2. Adds 'created_at' field with default timestamp
3. Removes unused 'confidence_in' field if it exists
4. Consolidates confidence_scores to be consistent
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment variables from .env file
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(dotenv_path)

# Add project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database.mongodb_client import MongoDBClient


async def migrate_ticket_schema():
    """
    Migrate all tickets in the database to the new schema.
    """
    mongo_client = MongoDBClient()

    try:
        await mongo_client.connect()
        print("✅ Connected to MongoDB")

        # Get all tickets
        all_tickets = await mongo_client.get_all_tickets()
        print(f"📊 Found {len(all_tickets)} tickets to migrate")

        migrated_count = 0
        error_count = 0

        for ticket in all_tickets:
            try:
                ticket_id = ticket.get('id')
                updates = {}

                # 1. Add status field based on current state
                if 'status' not in ticket:
                    if ticket.get('resolution') and ticket.get('resolution', {}).get('status') == 'resolved':
                        updates['status'] = 'resolved'
                    elif ticket.get('processed', False):
                        updates['status'] = 'processed'
                    else:
                        updates['status'] = 'unprocessed'

                # 2. Add created_at field if missing
                if 'created_at' not in ticket:
                    # Use updated_at if available, otherwise use current timestamp
                    if 'updated_at' in ticket and ticket['updated_at']:
                        if isinstance(ticket['updated_at'], str):
                            try:
                                # Try to parse ISO format
                                if 'T' in ticket['updated_at']:
                                    created_at = datetime.fromisoformat(ticket['updated_at'].replace('Z', '+00:00'))
                                else:
                                    created_at = datetime.strptime(ticket['updated_at'], '%Y-%m-%d %H:%M:%S.%f')
                            except:
                                created_at = datetime(2025, 9, 14, 17, 12, 36)
                        else:
                            created_at = ticket['updated_at']
                    else:
                        # Default timestamp as requested
                        created_at = datetime(2025, 9, 14, 17, 12, 36)
                    updates['created_at'] = created_at

                # 3. Remove confidence_in field if it exists
                if 'confidence_in' in ticket:
                    # MongoDB doesn't have a direct way to unset fields in update_one with our current method
                    # We'll handle this separately
                    pass

                # 4. Consolidate confidence_scores - move them inside classification if they're at root level
                # Remove empty confidence_scores at root level
                if 'confidence_scores' in ticket and not ticket['confidence_scores']:
                    # Remove empty confidence_scores from root level
                    pass  # Will be handled by $unset

                # 5. Update model version to correct format
                if 'processing_metadata' in ticket and ticket['processing_metadata']:
                    current_model = ticket['processing_metadata'].get('model_version', '')
                    if current_model in ['gemini-1.5-flash', '1.5 flash', '2.5 flash']:
                        updates['processing_metadata.model_version'] = 'gemini-2.5-flash'

                # If confidence_scores at root has data, move it to classification
                elif 'confidence_scores' in ticket and ticket['confidence_scores']:
                    if 'classification' in ticket:
                        # Move confidence_scores inside classification
                        if 'confidence_scores' not in ticket['classification']:
                            updates['classification.confidence_scores'] = ticket['confidence_scores']
                        # Remove from root level
                        updates['confidence_scores'] = {}
                    else:
                        # Create classification object with confidence_scores
                        updates['classification'] = {
                            'topic_tags': ticket.get('topic_tags', []),
                            'sentiment': ticket.get('sentiment', 'Unknown'),
                            'priority': ticket.get('priority', 'Unknown'),
                            'confidence_scores': ticket['confidence_scores']
                        }

                # Apply updates if any
                if updates:
                    success = await mongo_client.update_processed_ticket(ticket_id, updates)
                    if success:
                        migrated_count += 1
                        print(f"✅ Migrated ticket {ticket_id}")
                    else:
                        # Try updating any ticket (not just processed)
                        # Prepare unset operations
                        unset_fields = {}
                        if 'confidence_in' in ticket:
                            unset_fields["confidence_in"] = 1
                        if 'confidence_scores' in ticket and not ticket['confidence_scores']:
                            unset_fields["confidence_scores"] = 1

                        update_operation = {"$set": updates}
                        if unset_fields:
                            update_operation["$unset"] = unset_fields

                        try:
                            result = await mongo_client.collection.update_one(
                                {"id": ticket_id},
                                update_operation
                            )
                            if result.modified_count > 0:
                                migrated_count += 1
                                print(f"✅ Migrated ticket {ticket_id} (fallback method)")
                            else:
                                print(f"⚠️  No changes needed for ticket {ticket_id}")
                        except Exception as e:
                            error_count += 1
                            print(f"❌ Failed to migrate ticket {ticket_id}: {e}")
                else:
                    print(f"ℹ️  No updates needed for ticket {ticket_id}")

            except Exception as e:
                error_count += 1
                print(f"❌ Error processing ticket {ticket.get('id', 'Unknown')}: {e}")

        # Handle confidence_in removal separately for all tickets
        try:
            result = await mongo_client.collection.update_many(
                {"confidence_in": {"$exists": True}},
                {"$unset": {"confidence_in": 1}}
            )
            if result.modified_count > 0:
                print(f"🧹 Removed confidence_in field from {result.modified_count} tickets")
        except Exception as e:
            print(f"⚠️  Could not remove confidence_in field: {e}")

        print("\n📈 Migration Summary:")
        print(f"✅ Successfully migrated: {migrated_count} tickets")
        print(f"❌ Errors: {error_count} tickets")
        print(f"📊 Total processed: {len(all_tickets)} tickets")

        # Verify migration by checking a few tickets
        print("\n🔍 Verification:")
        all_tickets_for_verification = await mongo_client.get_all_tickets()
        sample_tickets = all_tickets_for_verification[:3]
        for ticket in sample_tickets:
            status = ticket.get('status', 'MISSING')
            created_at = ticket.get('created_at', 'MISSING')
            has_confidence_in = 'confidence_in' in ticket
            print(f"  Ticket {ticket.get('id')}: status={status}, created_at={created_at}, has_confidence_in={has_confidence_in}")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        await mongo_client.close()
        print("🔌 Disconnected from MongoDB")


async def verify_schema():
    """
    Verify that the schema migration was successful.
    """
    mongo_client = MongoDBClient()

    try:
        await mongo_client.connect()
        print("🔍 Verifying schema migration...")

        # Check that all tickets have status field
        total_tickets = await mongo_client.collection.count_documents({})
        tickets_with_status = await mongo_client.collection.count_documents({"status": {"$exists": True}})
        tickets_with_created_at = await mongo_client.collection.count_documents({"created_at": {"$exists": True}})
        tickets_with_confidence_in = await mongo_client.collection.count_documents({"confidence_in": {"$exists": True}})

        print("\n📊 Schema Verification:")
        print(f"Total tickets: {total_tickets}")
        print(f"Tickets with status field: {tickets_with_status}")
        print(f"Tickets with created_at field: {tickets_with_created_at}")
        print(f"Tickets with confidence_in field: {tickets_with_confidence_in}")

        if tickets_with_status == total_tickets:
            print("✅ All tickets have status field")
        else:
            print(f"⚠️  {total_tickets - tickets_with_status} tickets missing status field")

        if tickets_with_created_at == total_tickets:
            print("✅ All tickets have created_at field")
        else:
            print(f"⚠️  {total_tickets - tickets_with_created_at} tickets missing created_at field")

        if tickets_with_confidence_in == 0:
            print("✅ No tickets have confidence_in field (successfully removed)")
        else:
            print(f"⚠️  {tickets_with_confidence_in} tickets still have confidence_in field")

    except Exception as e:
        print(f"❌ Verification failed: {e}")
    finally:
        await mongo_client.close()


async def main():
    """
    Main migration function.
    """
    print("🚀 Starting MongoDB schema migration...")
    print("This will update all tickets with new schema fields.")

    # Run migration
    await migrate_ticket_schema()

    # Verify results
    await verify_schema()

    print("\n🎉 Schema migration completed!")


if __name__ == "__main__":
    asyncio.run(main())
