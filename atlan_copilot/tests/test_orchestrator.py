import asyncio
import os
import sys
from dotenv import load_dotenv
import json

# Add project root to sys.path
# This allows the script to be run from the root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from agents.orchestrator import Orchestrator

async def main():
    """
    Main function to run a test of the full agent orchestrator.
    """
    print("--- Starting Orchestrator Test ---")

    # Load environment variables from the root .env file
    dotenv_path = os.path.join(project_root, '.env')
    load_dotenv(dotenv_path=dotenv_path)

    # Initialize the orchestrator after loading the environment
    orchestrator = Orchestrator()

    # --- Test Case: A query that should have context in the sample tickets ---
    print("\n" + "="*50)
    query = "How do I export the lineage view for a specific table for an audit?"
    print(f"Testing with query: '{query}'")
    print("="*50 + "\n")

    # Invoke the full graph
    final_state = await orchestrator.invoke(query)

    print("\n--- Orchestrator Test Complete ---")
    print("\nFinal State of the Graph:")
    try:
        print(json.dumps(final_state, indent=2))
    except TypeError:
        print(final_state)

    print("\n" + "="*50)


if __name__ == "__main__":
    asyncio.run(main())
