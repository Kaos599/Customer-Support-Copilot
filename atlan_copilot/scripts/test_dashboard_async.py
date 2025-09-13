import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

async def test_dashboard_imports():
    """
    Test that dashboard imports work correctly without async issues.
    """
    print("--- Testing Dashboard Imports ---")

    try:
        # Test imports
        print("Testing imports...")
        from ui.dashboard import display_dashboard, run_classification_pipeline
        print("✅ Dashboard imports successful")

        # Test MongoDB client import
        from database.mongodb_client import MongoDBClient
        print("✅ MongoDB client import successful")

        # Test agent imports
        from agents.classification_agent import ClassificationAgent
        print("✅ Classification agent import successful")

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_mongodb_client_async():
    """
    Test MongoDB client async operations work correctly.
    """
    print("\n--- Testing MongoDB Client Async Operations ---")

    # Load environment variables
    dotenv_path = os.path.join(project_root, '..', '.env')
    load_dotenv(dotenv_path=dotenv_path)

    try:
        from database.mongodb_client import MongoDBClient

        mongo_client = MongoDBClient()
        await mongo_client.connect()
        print("✅ MongoDB connection successful")

        # Test getting tickets
        tickets = await mongo_client.get_all_tickets()
        print(f"✅ Retrieved {len(tickets)} tickets from database")

        # Test getting processed tickets
        processed = await mongo_client.get_processed_tickets(limit=5)
        print(f"✅ Retrieved {len(processed)} processed tickets from database")

        # Test getting statistics
        stats = await mongo_client.get_processing_stats()
        if stats:
            print(f"✅ Retrieved processing stats: {stats.get('total_processed', 0)} total processed")

        await mongo_client.close()
        print("✅ MongoDB connection closed successfully")

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing Dashboard Async Operations")
    print("=" * 50)

    # Test imports
    import_test = asyncio.run(test_dashboard_imports())

    # Test MongoDB operations
    mongodb_test = asyncio.run(test_mongodb_client_async())

    if import_test and mongodb_test:
        print("\n🎉 ALL DASHBOARD TESTS PASSED!")
        print("✅ Dashboard can be imported without async errors")
        print("✅ MongoDB client async operations work correctly")
        print("✅ Streamlit app should now run without syntax errors")
    else:
        print("\n💥 SOME DASHBOARD TESTS FAILED!")
        sys.exit(1)
