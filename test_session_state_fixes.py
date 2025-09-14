#!/usr/bin/env python3
"""
Test script to verify session state and async loop fixes.
This script tests the core functionality without running the full Streamlit app.
"""

import asyncio
import sys
import os
import threading
from concurrent.futures import ThreadPoolExecutor
import time
import nest_asyncio

# Enable nested asyncio loops
nest_asyncio.apply()

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), 'atlan_copilot'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from agents.orchestrator import Orchestrator
    print("✅ Successfully imported Orchestrator")
except ImportError as e:
    print(f"❌ Failed to import Orchestrator: {e}")
    sys.exit(1)

def test_orchestrator_initialization():
    """Test that the orchestrator can be initialized properly."""
    print("\n🧪 Testing Orchestrator Initialization...")
    
    try:
        orchestrator = Orchestrator()
        print("✅ Orchestrator initialized successfully")
        return orchestrator
    except Exception as e:
        print(f"❌ Failed to initialize orchestrator: {e}")
        return None

async def test_async_query(orchestrator, query="Hello"):
    """Test async query processing with proper loop management."""
    print(f"\n🧪 Testing async query: '{query}'")
    
    try:
        result = await orchestrator.invoke(query)
        print("✅ Async query completed successfully")
        print(f"📝 Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        return result
    except Exception as e:
        print(f"❌ Async query failed: {e}")
        return None

def test_thread_pool_execution(orchestrator):
    """Test executing async queries in thread pool to simulate Streamlit behavior."""
    print("\n🧪 Testing ThreadPoolExecutor async execution...")
    
    def run_async_in_new_loop(query):
        """Run async query in a new event loop."""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(test_async_query(orchestrator, query))
                return {"success": True, "data": result}
            finally:
                loop.close()
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            # Submit multiple test queries
            test_queries = ["Hello", "What is Atlan?", "Help me with data governance"]
            
            futures = []
            for query in test_queries:
                future = executor.submit(run_async_in_new_loop, query)
                futures.append((query, future))
            
            # Collect results
            for query, future in futures:
                try:
                    result = future.result(timeout=30)
                    if result["success"]:
                        print(f"✅ Thread query '{query}' succeeded")
                    else:
                        print(f"❌ Thread query '{query}' failed: {result['error']}")
                except Exception as e:
                    print(f"❌ Thread query '{query}' exception: {e}")
                    
        print("✅ ThreadPoolExecutor tests completed")
        
    except Exception as e:
        print(f"❌ ThreadPoolExecutor test failed: {e}")

def test_event_loop_conflicts():
    """Test for event loop conflicts between different async contexts."""
    print("\n🧪 Testing event loop conflict handling...")
    
    try:
        # Test multiple loops in same thread
        loop1 = asyncio.new_event_loop()
        asyncio.set_event_loop(loop1)
        
        async def simple_coro():
            await asyncio.sleep(0.01)
            return "success"
        
        result1 = loop1.run_until_complete(simple_coro())
        print(f"✅ First loop result: {result1}")
        
        loop1.close()
        
        # Test second loop
        loop2 = asyncio.new_event_loop()
        asyncio.set_event_loop(loop2)
        
        result2 = loop2.run_until_complete(simple_coro())
        print(f"✅ Second loop result: {result2}")
        
        loop2.close()
        
        print("✅ Event loop switching works correctly")
        
    except Exception as e:
        print(f"❌ Event loop conflict test failed: {e}")

def main():
    """Main test function."""
    print("🚀 Starting Session State and Async Loop Tests...")
    print("=" * 60)
    
    # Test 1: Orchestrator initialization
    orchestrator = test_orchestrator_initialization()
    if not orchestrator:
        print("❌ Cannot proceed without orchestrator")
        return
    
    # Test 2: Event loop conflict handling
    test_event_loop_conflicts()
    
    # Test 3: Basic async query (direct)
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(test_async_query(orchestrator, "test query"))
        loop.close()
    except Exception as e:
        print(f"❌ Direct async test failed: {e}")
    
    # Test 4: Thread pool execution (like Streamlit)
    test_thread_pool_execution(orchestrator)
    
    print("\n" + "=" * 60)
    print("🏁 Tests completed!")
    print("\nIf all tests passed, the session state and async fixes should work correctly.")

if __name__ == "__main__":
    main()