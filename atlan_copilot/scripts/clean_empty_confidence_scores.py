#!/usr/bin/env python3
"""
Script to remove empty confidence_scores fields from ticket documents.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(dotenv_path)

# Add project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database.mongodb_client import MongoDBClient


async def clean_empty_confidence_scores():
    """
    Remove empty confidence_scores fields from all tickets.
    """
    mongo_client = MongoDBClient()

    try:
        await mongo_client.connect()
        print("✅ Connected to MongoDB")

        # Find tickets with empty confidence_scores
        tickets_with_empty_confidence = await mongo_client.collection.count_documents({
            "confidence_scores": {}
        })

        print(f"📊 Found {tickets_with_empty_confidence} tickets with empty confidence_scores")

        if tickets_with_empty_confidence > 0:
            # Remove empty confidence_scores fields
            result = await mongo_client.collection.update_many(
                {"confidence_scores": {}},
                {"$unset": {"confidence_scores": 1}}
            )

            print(f"🧹 Removed empty confidence_scores field from {result.modified_count} tickets")
        else:
            print("✅ No tickets found with empty confidence_scores fields")

        # Verify cleanup
        remaining_empty = await mongo_client.collection.count_documents({
            "confidence_scores": {}
        })
        print(f"🔍 Verification: {remaining_empty} tickets still have empty confidence_scores")

    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        raise
    finally:
        await mongo_client.close()
        print("🔌 Disconnected from MongoDB")


async def verify_schema_cleanliness():
    """
    Verify that the schema is clean.
    """
    mongo_client = MongoDBClient()

    try:
        await mongo_client.connect()
        print("🔍 Verifying schema cleanliness...")

        # Check various counts
        total_tickets = await mongo_client.collection.count_documents({})
        tickets_with_empty_confidence = await mongo_client.collection.count_documents({"confidence_scores": {}})
        tickets_with_confidence_data = await mongo_client.collection.count_documents({"confidence_scores": {"$ne": {}}})
        tickets_with_confidence_in_classification = await mongo_client.collection.count_documents({"classification.confidence_scores": {"$exists": True}})

        print("\n📊 Schema Verification:")
        print(f"Total tickets: {total_tickets}")
        print(f"Tickets with empty confidence_scores: {tickets_with_empty_confidence}")
        print(f"Tickets with confidence_scores data: {tickets_with_confidence_data}")
        print(f"Tickets with confidence_scores in classification: {tickets_with_confidence_in_classification}")

        if tickets_with_empty_confidence == 0:
            print("✅ No tickets have empty confidence_scores fields")
        else:
            print(f"⚠️  {tickets_with_empty_confidence} tickets still have empty confidence_scores")

    except Exception as e:
        print(f"❌ Verification failed: {e}")
    finally:
        await mongo_client.close()


async def main():
    """
    Main cleanup function.
    """
    print("🧹 Starting confidence_scores cleanup...")

    # Run cleanup
    await clean_empty_confidence_scores()

    # Verify results
    await verify_schema_cleanliness()

    print("\n🎉 Confidence_scores cleanup completed!")


if __name__ == "__main__":
    asyncio.run(main())
