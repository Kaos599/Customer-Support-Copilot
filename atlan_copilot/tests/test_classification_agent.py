import asyncio
import json
import os
import sys
from dotenv import load_dotenv
from typing import Dict, Any

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agents.classification_agent import ClassificationAgent

async def test_single_ticket(agent: ClassificationAgent, ticket: Dict[str, Any]):
    """
    Tests the classification agent with a single ticket.
    """
    print("-" * 50)
    print(f"Testing classification for ticket: {ticket.get('id', 'N/A')}")
    print(f"Subject: {ticket.get('subject')}")
    print("-" * 50)

    initial_state = {
        "subject": ticket.get("subject"),
        "body": ticket.get("body")
    }

    # Execute the agent
    final_state = await agent.execute(initial_state)

    # Print the result
    classification = final_state.get("classification")
    if classification:
        print("✅ Classification successful!")
        print(json.dumps(classification, indent=2))
    else:
        print("❌ Classification failed or was skipped.")
        print("Final state:", final_state)

    print("\n")


async def main():
    """
    Main function to run the classification agent test.
    """
    print("--- Starting Classification Agent Test ---")

    # Load environment variables
    dotenv_path = os.path.join(project_root, '.env')
    load_dotenv(dotenv_path=dotenv_path)

    if not os.getenv("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY not found. Please set it in your .env file.")
        return

    # Load sample tickets
    try:
        tickets_path = os.path.join(project_root, 'data', 'sample_tickets.json')
        with open(tickets_path, 'r') as f:
            sample_tickets = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading sample tickets: {e}")
        return

    if not sample_tickets:
        print("No sample tickets found to test.")
        return

    # Initialize the agent
    classification_agent = ClassificationAgent()

    # Test the first ticket
    await test_single_ticket(classification_agent, sample_tickets[0])

    # Test another, more complex ticket (e.g., the one with "infuriating" sentiment)
    frustrated_ticket = next((t for t in sample_tickets if "infuriating" in t.get("body", "")), None)
    if frustrated_ticket:
        await test_single_ticket(classification_agent, frustrated_ticket)
    else:
        # As a fallback, test the 9th ticket (index 8) if the specific one isn't found
        if len(sample_tickets) > 8:
            await test_single_ticket(classification_agent, sample_tickets[8])


    print("--- Classification Agent Test Complete ---")


if __name__ == "__main__":
    asyncio.run(main())
