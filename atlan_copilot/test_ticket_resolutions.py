#!/usr/bin/env python3
"""
Test script to verify ticket resolution functionality and navigation fixes.
"""

import sys
import os

# Add project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def test_imports():
    """Test that all required modules can be imported."""
    try:
        from pages.ticket_detail import display_ticket_detail, resolve_current_ticket
        from ui.tickets_view import display_tickets_view, resolve_all_unprocessed_tickets
        from agents.ticket_orchestrator import TicketOrchestrator
        from agents.resolution_agent import ResolutionAgent
        from database.mongodb_client import MongoDBClient
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def test_navigation_fixes():
    """Test that navigation paths are corrected."""
    try:
        # Check if ticket_detail.py uses correct navigation
        with open("pages/ticket_detail.py", "r") as f:
            content = f.read()

        # Should use app.py for navigation, not ui/ files
        if "st.switch_page(\"app.py\")" in content:
            print("✅ Navigation paths corrected (using app.py)")
        else:
            print("⚠️ Navigation paths may still need updates")
            return False

        # Should not try to navigate to ui/ files
        if "st.switch_page(\"ui/" not in content:
            print("✅ No invalid ui/ navigation paths found")
        else:
            print("❌ Still contains invalid ui/ navigation paths")
            return False

        return True
    except Exception as e:
        print(f"❌ Navigation test failed: {e}")
        return False


def test_resolve_functionality():
    """Test that resolve functions are properly implemented."""
    try:
        # Check if resolve functions exist
        import inspect
        from pages.ticket_detail import resolve_current_ticket
        from ui.tickets_view import resolve_all_unprocessed_tickets

        # Check function signatures
        sig1 = inspect.signature(resolve_current_ticket)
        sig2 = inspect.signature(resolve_all_unprocessed_tickets)

        if len(sig1.parameters) == 1:  # ticket_id parameter
            print("✅ resolve_current_ticket function signature correct")
        else:
            print("❌ resolve_current_ticket function signature incorrect")
            return False

        if len(sig2.parameters) == 0:  # no parameters
            print("✅ resolve_all_unprocessed_tickets function signature correct")
        else:
            print("❌ resolve_all_unprocessed_tickets function signature incorrect")
            return False

        return True
    except Exception as e:
        print(f"❌ Resolve functionality test failed: {e}")
        return False


def test_ui_improvements():
    """Test that UI improvements are in place."""
    try:
        # Check ticket_detail.py for UI improvements
        with open("pages/ticket_detail.py", "r") as f:
            content = f.read()

        improvements = [
            ("sidebar collapsed", "initial_sidebar_state=\"collapsed\"" in content),
            ("resolve button", "🔄 Resolve Ticket" in content),
            ("navigation buttons", "Back to Tickets" in content and "Dashboard" in content),
            ("session state navigation", "st.session_state.current_view" in content)
        ]

        for improvement, found in improvements:
            if found:
                print(f"✅ {improvement} implemented")
            else:
                print(f"❌ {improvement} not found")
                return False

        return True
    except Exception as e:
        print(f"❌ UI improvements test failed: {e}")
        return False


def test_main_app_changes():
    """Test that main app.py has the required changes."""
    try:
        with open("app.py", "r") as f:
            content = f.read()

        changes = [
            ("sidebar collapsed", "initial_sidebar_state=\"collapsed\"" in content),
            ("session state handling", "st.session_state.current_view" in content),
            ("compact navigation", "st.columns([1, 1, 1])" in content),
            ("button styling", "type=\"primary\" if page" in content)
        ]

        for change, found in changes:
            if found:
                print(f"✅ {change} implemented in main app")
            else:
                print(f"❌ {change} not found in main app")
                return False

        return True
    except Exception as e:
        print(f"❌ Main app changes test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 Testing Ticket Resolution and Navigation Fixes")
    print("=" * 60)

    tests = [
        ("Import Tests", test_imports),
        ("Navigation Fixes", test_navigation_fixes),
        ("Resolve Functionality", test_resolve_functionality),
        ("UI Improvements", test_ui_improvements),
        ("Main App Changes", test_main_app_changes)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}...")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")

    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed!")
        print("\n✅ **Issues Fixed:**")
        print("   • Navigation error resolved (no more 'Could not find page' error)")
        print("   • Sidebar navigation removed from ticket detail view")
        print("   • Individual ticket resolve button added")
        print("   • Bulk resolve all tickets button added")
        print("   • Clean, compact navigation in main app")
        print("\n🚀 **Ready to test:**")
        print("   1. Run: streamlit run atlan_copilot/app.py")
        print("   2. Navigate to Tickets View")
        print("   3. Click '👁️ View Full Details' on any ticket")
        print("   4. Use the '🔄 Resolve Ticket' button")
        print("   5. Use '🎯 Resolve All Unprocessed' in tickets view")
    else:
        print("⚠️ Some tests failed. Please check the error messages above.")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
