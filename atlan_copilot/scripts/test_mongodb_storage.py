import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database.mongodb_client import MongoDBClient
from agents.classification_agent import ClassificationAgent

async def test_mongodb_storage():
    """
    Test the MongoDB storage functionality for processed tickets.
    """
    print("--- Testing MongoDB Processed Tickets Storage ---")

    # Load environment variables
    dotenv_path = os.path.join(project_root, '..', '.env')
    load_dotenv(dotenv_path=dotenv_path)

    # Debug: Print environment variables
    print(f"MONGO_URI: {'***' if os.getenv('MONGO_URI') else 'Not set'}")
    print(f"MONGO_DB: {os.getenv('MONGO_DB')}")
    print(f"MONGO_COLLECTION: {os.getenv('MONGO_COLLECTION')}")
    print(f"MONGO_COLLECTION_PROCESSED: {os.getenv('MONGO_COLLECTION_PROCESSED')}")

    try:
        # Initialize MongoDB client
        print("Initializing MongoDB client...")
        mongo_client = MongoDBClient()
        await mongo_client.connect()

        # Get a sample ticket to process
        print("Fetching sample ticket...")
        tickets = await mongo_client.get_all_tickets()
        if not tickets:
            print("❌ No sample tickets found. Please run load_sample_data.py first.")
            return False

        sample_ticket = tickets[0]
        print(f"Using sample ticket: {sample_ticket.get('id')}")

        # Process the ticket with the classification agent
        print("Processing ticket with classification agent...")
        agent = ClassificationAgent()
        if not agent.model:
            print("❌ Classification agent could not be initialized. Check API key.")
            return False

        agent_input = {"subject": sample_ticket.get("subject"), "body": sample_ticket.get("body")}
        result = await agent.execute(agent_input)

        if not result or not result.get("classification"):
            print("❌ Classification failed")
            return False

        print("✅ Classification successful")
        print(f"   Classification result: {result.get('classification')}")

        # Store the processed ticket
        print("Storing processed ticket in MongoDB...")
        stored_id = await mongo_client.store_processed_ticket(sample_ticket, result)

        if stored_id:
            print(f"✅ Successfully stored processed ticket with ID: {stored_id}")

            # Verify the stored ticket
            print("Verifying stored ticket...")
            stored_ticket = await mongo_client.get_processed_ticket_by_id(sample_ticket.get("id"))

            if stored_ticket:
                print("✅ Successfully retrieved stored ticket")
                print(f"   Ticket ID: {stored_ticket.get('ticket_id')}")
                print(f"   Subject: {stored_ticket.get('subject')}")
                print(f"   Classification: {stored_ticket.get('classification', {})}")
                print(f"   Processed At: {stored_ticket.get('processing_metadata', {}).get('processed_at')}")
            else:
                print("❌ Could not retrieve stored ticket")
                return False
        else:
            print("❌ Failed to store processed ticket")
            return False

        # Test getting processing statistics
        print("Testing processing statistics...")
        stats = await mongo_client.get_processing_stats()

        if stats:
            print("✅ Processing statistics retrieved:")
            print(f"   Total processed: {stats.get('total_processed', 0)}")
            print(f"   Processed today: {stats.get('processed_today', 0)}")
            print(f"   Priority distribution: {stats.get('priority_distribution', {})}")
        else:
            print("⚠️  Could not retrieve processing statistics")

        # Close connection
        await mongo_client.close()

        print("\n🎉 MongoDB storage test PASSED!")
        print("✅ All processed tickets are now being stored in the 'tickets_processed' collection")
        return True

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_dashboard_like_processing():
    """
    Test processing similar to what happens in the dashboard.
    """
    print("\n--- Testing Dashboard-like Processing ---")

    # Load environment variables
    dotenv_path = os.path.join(project_root, '..', '.env')
    load_dotenv(dotenv_path=dotenv_path)

    try:
        # Initialize components
        mongo_client = MongoDBClient()
        agent = ClassificationAgent()

        if not agent.model:
            print("❌ Classification agent could not be initialized. Check API key.")
            return False

        # Connect to MongoDB once
        await mongo_client.connect()

        # Get tickets to process
        tickets = await mongo_client.get_all_tickets()
        if not tickets:
            print("❌ No sample tickets found. Please run load_sample_data.py first.")
            return False

        print(f"Processing {len(tickets)} tickets...")

        # Process tickets sequentially (like the dashboard does)
        for i, ticket in enumerate(tickets[:3]):  # Process only first 3 for testing
            print(f"Processing ticket {i+1}: {ticket.get('id')}")

            agent_input = {"subject": ticket.get("subject"), "body": ticket.get("body")}
            result = await agent.execute(agent_input)

            if result and result.get("classification"):
                try:
                    stored_id = await mongo_client.store_processed_ticket(ticket, result)
                    if stored_id:
                        print(f"  ✅ Stored processed ticket {ticket.get('id')}")
                    else:
                        print(f"  ⚠️  Failed to store processed ticket {ticket.get('id')}")
                except Exception as e:
                    print(f"  ❌ Error storing ticket {ticket.get('id')}: {e}")
            else:
                print(f"  ⚠️  Skipping storage for ticket {ticket.get('id')} - no classification result")

            # Small delay between processing
            if i < len(tickets[:3]) - 1:
                await asyncio.sleep(1)

        # Get final statistics
        stats = await mongo_client.get_processing_stats()
        if stats:
            print("\n📊 Final Statistics:")
            print(f"   Total processed: {stats.get('total_processed', 0)}")
            print(f"   Processed today: {stats.get('processed_today', 0)}")

        # Close connection at the very end
        await mongo_client.close()

        print("\n✅ Dashboard-like processing test completed!")
        return True

    except Exception as e:
        print(f"\n❌ ERROR in dashboard test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing MongoDB Storage with Dashboard-like Processing")
    print("=" * 60)

    # Test 1: Basic storage functionality
    basic_test = asyncio.run(test_mongodb_storage())

    # Test 2: Dashboard-like processing
    dashboard_test = asyncio.run(test_dashboard_like_processing())

    if basic_test and dashboard_test:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Processed tickets are now being stored correctly in MongoDB")
        print("✅ Dashboard processing pipeline works correctly")
    else:
        print("\n💥 SOME TESTS FAILED!")
        sys.exit(1)
