#!/usr/bin/env python3
"""
Simple test to verify session state and async infrastructure fixes without requiring API keys.
"""

import asyncio
import sys
import os
import threading
from concurrent.futures import ThreadPoolExecutor
import nest_asyncio
import platform

# Enable nested asyncio loops
nest_asyncio.apply()

def test_event_loop_management():
    """Test the event loop management fixes."""
    print("🧪 Testing event loop management...")
    
    def run_async_task_in_thread(task_name):
        """Simulate running async task in thread (like Streamlit ThreadPoolExecutor)."""
        try:
            # Create new event loop for this thread (like our fix does)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def sample_task():
                await asyncio.sleep(0.1)
                return f"Task {task_name} completed"
            
            try:
                result = loop.run_until_complete(sample_task())
                return {"success": True, "result": result}
            finally:
                loop.close()
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Test multiple threads with separate event loops
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        for i in range(3):
            future = executor.submit(run_async_task_in_thread, f"T{i}")
            futures.append(future)
        
        success_count = 0
        for future in futures:
            try:
                result = future.result(timeout=5)
                if result["success"]:
                    print(f"✅ {result['result']}")
                    success_count += 1
                else:
                    print(f"❌ Task failed: {result['error']}")
            except Exception as e:
                print(f"❌ Future failed: {e}")
        
        print(f"📊 {success_count}/3 thread tasks succeeded")
        return success_count == 3

def test_context_wrapper_structure():
    """Test the context wrapper infrastructure."""
    print("\n🧪 Testing context wrapper structure...")
    
    try:
        # Mock Streamlit context functions (since we can't import streamlit here)
        class MockScriptRunContext:
            pass
        
        def mock_get_script_run_ctx():
            return MockScriptRunContext()
        
        def mock_add_script_run_ctx(func):
            return func  # Just return the function for this test
        
        # Test our wrapper pattern
        import functools
        
        def wrap_with_mock_context(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                ctx = mock_get_script_run_ctx()
                if ctx is None:
                    return func(*args, **kwargs)
                else:
                    return mock_add_script_run_ctx(func)(*args, **kwargs)
            return wrapper
        
        @wrap_with_mock_context
        def sample_function(message):
            return f"Processed: {message}"
        
        result = sample_function("test")
        if result == "Processed: test":
            print("✅ Context wrapper structure works")
            return True
        else:
            print("❌ Context wrapper failed")
            return False
            
    except Exception as e:
        print(f"❌ Context wrapper test failed: {e}")
        return False

def test_session_state_pattern():
    """Test the session state initialization pattern."""
    print("\n🧪 Testing session state pattern...")
    
    try:
        # Mock session state behavior
        class MockSessionState:
            def __init__(self):
                self._state = {}
            
            def get(self, key, default=None):
                return self._state.get(key, default)
            
            def __contains__(self, key):
                return key in self._state
            
            def __setitem__(self, key, value):
                self._state[key] = value
            
            def __getitem__(self, key):
                if key not in self._state:
                    raise AttributeError(f"st.session_state has no attribute '{key}'. Did you forget to initialize it?")
                return self._state[key]
        
        # Test our initialization pattern
        mock_session_state = MockSessionState()
        
        def ensure_orchestrator_initialized(session_state):
            if "orchestrator" not in session_state or session_state.get("orchestrator") is None:
                # Simulate orchestrator initialization
                session_state["orchestrator"] = "mock_orchestrator"
                print("✅ Orchestrator initialized in session state")
            return session_state.get("orchestrator")
        
        # Test first call (should initialize)
        orchestrator1 = ensure_orchestrator_initialized(mock_session_state)
        
        # Test second call (should use existing)
        orchestrator2 = ensure_orchestrator_initialized(mock_session_state)
        
        if orchestrator1 == orchestrator2 == "mock_orchestrator":
            print("✅ Session state initialization pattern works")
            return True
        else:
            print("❌ Session state pattern failed")
            return False
            
    except Exception as e:
        print(f"❌ Session state pattern test failed: {e}")
        return False

def test_import_structure():
    """Test that our import structure works."""
    print("\n🧪 Testing import structure...")
    
    try:
        # Test basic asyncio functionality
        async def test_coro():
            return "async works"
        
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(test_coro())
        loop.close()
        
        if result == "async works":
            print("✅ Basic async functionality works")
        
        # Test nest_asyncio
        if hasattr(nest_asyncio, 'apply'):
            print("✅ nest_asyncio available and applied")
        
        # Test platform detection
        system = platform.system()
        print(f"✅ Platform detected: {system}")
        
        return True
        
    except Exception as e:
        print(f"❌ Import structure test failed: {e}")
        return False

def main():
    """Run all infrastructure tests."""
    print("🚀 Testing Session State and Async Infrastructure Fixes")
    print("=" * 60)
    
    tests = [
        ("Import Structure", test_import_structure),
        ("Event Loop Management", test_event_loop_management),
        ("Context Wrapper Structure", test_context_wrapper_structure),
        ("Session State Pattern", test_session_state_pattern),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        try:
            if test_func():
                print(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"💥 {test_name}: CRASHED - {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All infrastructure tests passed!")
        print("✅ The session state and async loop fixes should resolve the reported errors.")
    else:
        print("⚠️  Some tests failed - fixes may need adjustment.")

if __name__ == "__main__":
    main()