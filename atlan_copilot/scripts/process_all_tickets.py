import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path for absolute imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database.mongodb_client import MongoDBClient
from agents.classification_agent import ClassificationAgent

async def process_all_tickets():
    """
    Process all unprocessed tickets and update them with classification data
    using the unified schema.
    """
    print("--- Processing All Tickets with Unified Schema ---")

    # Load environment variables from the root .env file
    dotenv_path = os.path.join(project_root, '..', '.env')
    load_dotenv(dotenv_path=dotenv_path)

    # Initialize clients
    mongo_client = None
    agent = None

    try:
        mongo_client = MongoDBClient()
        await mongo_client.connect()

        agent = ClassificationAgent()
        if not agent.model:
            print("❌ Classification agent could not be initialized. Check API key.")
            return

        # Get all tickets (both processed and unprocessed) to ensure all have correct classifications
        all_tickets = await mongo_client.get_all_tickets()
        print(f"Found {len(all_tickets)} total tickets in database")

        # Filter to get tickets that need processing (unprocessed or incorrectly processed)
        tickets_to_process = []
        for ticket in all_tickets:
            # Check if ticket is properly processed with valid tag names
            if not ticket.get('processed', False):
                tickets_to_process.append(ticket)
            else:
                # Check if classification has valid tags (not the old incorrect ones)
                classification = ticket.get('classification', {})
                topic_tags = classification.get('topic_tags', [])
                sentiment = classification.get('sentiment', '')
                priority = classification.get('priority', '')

                # If any tag is still using the old incorrect values, reprocess
                invalid_tags = ['category', 'description', 'tags']
                has_invalid_topic = any(tag in invalid_tags for tag in topic_tags)
                has_invalid_sentiment = sentiment in invalid_tags
                has_invalid_priority = priority in invalid_tags

                if has_invalid_topic or has_invalid_sentiment or has_invalid_priority:
                    tickets_to_process.append(ticket)

        print(f"Found {len(tickets_to_process)} tickets that need (re)processing")

        if not tickets_to_process:
            print("✅ All tickets are already properly classified.")
            return

        # Process tickets sequentially
        processed_count = 0
        total_tickets = len(tickets_to_process)

        print(f"Starting classification of {total_tickets} tickets...")

        for i, ticket in enumerate(tickets_to_process):
            ticket_id = ticket.get("id")
            print(f"Processing ticket {i+1}/{total_tickets}: {ticket_id}")

            # Prepare input for classification agent
            agent_input = {
                "subject": ticket.get("subject", ""),
                "body": ticket.get("body", "")
            }

            # Classify the ticket
            result = await agent.execute(agent_input)

            if result and result.get("classification"):
                # Update ticket with classification data
                success = await mongo_client.update_ticket_with_classification(ticket_id, result)

                if success:
                    processed_count += 1
                    print(f"✅ Successfully processed ticket {ticket_id}")
                else:
                    print(f"❌ Failed to update ticket {ticket_id}")
            else:
                print(f"⚠️  Classification failed for ticket {ticket_id}")

            # Rate limiting delay (12 RPM = 5 seconds between requests)
            if i < total_tickets - 1:
                await asyncio.sleep(5)

        print(f"\n✅ Processing complete! Successfully processed {processed_count} out of {total_tickets} tickets")

        # Show final statistics
        final_stats = await mongo_client.get_processing_stats()
        print("\n--- Final Statistics ---")
        print(f"Total tickets: {final_stats.get('total_tickets', 0)}")
        print(f"Processed tickets: {final_stats.get('total_processed', 0)}")
        print(f"Unprocessed tickets: {final_stats.get('total_unprocessed', 0)}")

        # Show a sample of processed tickets
        if processed_count > 0:
            print("\n--- Sample Processed Tickets ---")
            processed_tickets = await mongo_client.get_processed_tickets(limit=3)
            for ticket in processed_tickets:
                print(f"ID: {ticket.get('id')}")
                print(f"Priority: {ticket.get('classification', {}).get('priority', 'N/A')}")
                print(f"Sentiment: {ticket.get('classification', {}).get('sentiment', 'N/A')}")
                print("---")

    except Exception as e:
        print(f"An error occurred during processing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if mongo_client:
            await mongo_client.close()

    print("\n--- Processing Complete ---")

if __name__ == "__main__":
    asyncio.run(process_all_tickets())
