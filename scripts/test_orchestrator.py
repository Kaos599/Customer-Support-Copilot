import asyncio
import os
import sys
from dotenv import load_dotenv
import json

# This script should be run as a module from the project root, e.g.,
# python -m atlan_copilot.scripts.test_orchestrator
# This ensures that the Python path is set up correctly for package imports.
from atlan_copilot.agents.orchestrator import Orchestrator

async def main():
    """
    Main function to run a test of the full agent orchestrator.
    """
    print("--- Starting Orchestrator Test ---")

    # Load environment variables from the root .env file
    # Assumes the script is run from the project root directory.
    load_dotenv()

    # Initialize the orchestrator after loading the environment
    orchestrator = Orchestrator()

    # --- Test Case: A query that should have context in the sample tickets ---
    # Although we are not scraping yet, the RAG agent has a placeholder response
    # for when Qdrant is not available. This will test the full flow.
    print("\n" + "="*50)
    query = "How do I export the lineage view for a specific table for an audit?"
    print(f"Testing with query: '{query}'")
    print("="*50 + "\n")

    # Invoke the full graph
    final_state = await orchestrator.invoke(query)

    print("\n--- Orchestrator Test Complete ---")
    print("\nFinal State of the Graph:")
    # Pretty print the final state dictionary for readability
    # Use a custom encoder to handle any non-serializable objects if necessary
    # For now, a simple dump should work as the state is a TypedDict of simple types.
    try:
        print(json.dumps(final_state, indent=2))
    except TypeError:
        # Fallback for complex objects
        print(final_state)

    print("\n" + "="*50)


if __name__ == "__main__":
    asyncio.run(main())
