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

async def test_dashboard_mongodb_integration():
    """
    Test the dashboard MongoDB integration by simulating the dashboard processing pipeline.
    """
    print("--- Testing Dashboard MongoDB Integration ---")

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

        # Connect to MongoDB once (like dashboard does)
        await mongo_client.connect()
        print("✅ Connected to MongoDB")

        # Get tickets to process (like dashboard does)
        tickets_data = await mongo_client.get_all_tickets()
        if not tickets_data:
            print("❌ No tickets found in database")
            return False

        print(f"📋 Found {len(tickets_data)} tickets to process")

        # Process tickets sequentially (like dashboard does)
        classified_results = []
        total_tickets = len(tickets_data)
        processed_count = 0

        print("🔄 Processing tickets...")

        for i, ticket in enumerate(tickets_data[:5]):  # Process only first 5 for testing
            print(f"  Processing {i+1}/5: {ticket.get('id')}")

            agent_input = {"subject": ticket.get("subject"), "body": ticket.get("body")}
            result = await agent.execute(agent_input)
            classified_results.append(result)

            # Store the processed ticket in MongoDB (like dashboard does)
            if result and result.get("classification"):
                try:
                    stored_id = await mongo_client.store_processed_ticket(ticket, result)
                    if stored_id:
                        print(f"    ✅ Stored: {ticket.get('id')}")
                        processed_count += 1
                    else:
                        print(f"    ⚠️  Failed to store: {ticket.get('id')}")
                except Exception as e:
                    print(f"    ❌ Error storing {ticket.get('id')}: {e}")
            else:
                print(f"    ⚠️  No classification for: {ticket.get('id')}")

            # Rate limiting delay (like dashboard does)
            if i < 4:  # Don't delay after last ticket
                await asyncio.sleep(2)  # Shorter delay for testing

        print(f"\n📊 Successfully processed and stored {processed_count} tickets")

        # Get processing statistics (like dashboard does)
        stats = await mongo_client.get_processing_stats()
        if stats:
            print("📈 Processing Statistics:")
            print(f"   Total processed: {stats.get('total_processed', 0)}")
            print(f"   Processed today: {stats.get('processed_today', 0)}")
            print(f"   Priority distribution: {stats.get('priority_distribution', {})}")
        else:
            print("⚠️  Could not retrieve statistics")

        # Close connection at the very end (like dashboard does)
        await mongo_client.close()
        print("✅ MongoDB connection closed")

        return processed_count > 0

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing Dashboard MongoDB Integration")
    print("=" * 50)

    success = asyncio.run(test_dashboard_mongodb_integration())

    if success:
        print("\n🎉 DASHBOARD MONGODB INTEGRATION TEST PASSED!")
        print("✅ Dashboard processing pipeline working correctly")
        print("✅ Processed tickets being stored in MongoDB")
        print("✅ Connection management working properly")
    else:
        print("\n💥 DASHBOARD MONGODB INTEGRATION TEST FAILED!")
        sys.exit(1)
