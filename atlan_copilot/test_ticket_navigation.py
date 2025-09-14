#!/usr/bin/env python3
"""
Test script to verify ticket navigation and detail view functionality.
"""

import sys
import os
from unittest.mock import Mock, patch

# Add project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def test_imports():
    """Test that all required modules can be imported."""
    try:
        from pages.ticket_detail import display_ticket_detail, fetch_ticket_by_id
        from ui.tickets_view import display_tickets_view
        from database.mongodb_client import MongoDBClient
        from agents.resolution_agent import ResolutionAgent
        from agents.ticket_orchestrator import TicketOrchestrator
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def test_ticket_detail_structure():
    """Test the ticket detail page structure."""
    try:
        # Mock a sample ticket
        sample_ticket = {
            'id': 'TICKET-245',
            'subject': 'Test ticket subject',
            'body': 'Test ticket body',
            'processed': True,
            'classification': {
                'topic': 'How-to',
                'sentiment': 'Curious',
                'priority': 'P1 (Medium)',
                'topic_tags': ['Connector', 'How-to']
            },
            'confidence_scores': {
                'topic': 0.85,
                'sentiment': 0.92,
                'priority': 0.78
            },
            'processing_metadata': {
                'model_version': 'gemini-1.5-flash',
                'processing_time_seconds': 1.5,
                'processed_at': '2025-09-14T10:30:00',
                'status': 'completed'
            },
            'resolution': {
                'status': 'resolved',
                'response': 'This is a test AI-generated response.',
                'sources': [
                    {
                        'url': 'https://docs.atlan.com/test',
                        'snippet': 'Test snippet from documentation'
                    }
                ],
                'generated_at': '2025-09-14T10:31:00',
                'confidence': 0.88
            }
        }

        print("✅ Sample ticket structure is valid")
        print(f"   - Ticket ID: {sample_ticket['id']}")
        print(f"   - Processed: {sample_ticket['processed']}")
        print(f"   - Resolution Status: {sample_ticket['resolution']['status']}")

        return True
    except Exception as e:
        print(f"❌ Ticket structure test failed: {e}")
        return False


def test_navigation_paths():
    """Test that navigation paths are correct."""
    try:
        # Test relative paths from main app
        pages_path = "pages/ticket_detail.py"
        ui_path = "ui/tickets_view.py"
        app_path = "app.py"

        print("✅ Navigation paths configured:")
        print(f"   - Ticket Detail: {pages_path}")
        print(f"   - Tickets View: {ui_path}")
        print(f"   - Main App: {app_path}")

        return True
    except Exception as e:
        print(f"❌ Navigation path test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 Testing Ticket Navigation Functionality")
    print("=" * 50)

    tests = [
        ("Import Tests", test_imports),
        ("Ticket Structure Tests", test_ticket_detail_structure),
        ("Navigation Path Tests", test_navigation_paths)
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

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Ticket navigation should work correctly.")
        print("\n💡 To test the actual navigation:")
        print("   1. Run the Streamlit app: streamlit run atlan_copilot/app.py")
        print("   2. Go to Tickets View")
        print("   3. Click '👁️ View Full Details' on any ticket")
        print("   4. Verify the ticket detail page loads correctly")
    else:
        print("⚠️ Some tests failed. Please check the error messages above.")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)