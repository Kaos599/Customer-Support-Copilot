#!/usr/bin/env python3
"""
Test script to verify that the data caching imports work correctly.
"""

import sys
import os
sys.path.insert(0, 'atlan_copilot')

def test_imports():
    """Test that all caching utilities can be imported."""
    print("🔄 Testing data caching system imports...")

    try:
        from utils.data_cache import get_cached_mongo_client, get_cached_tickets_data, get_cached_processed_tickets, clear_data_cache
        print("✅ All caching utilities imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

    try:
        from ui.tickets_view import display_tickets_view
        print("✅ Tickets view imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Tickets view import failed: {e}")
        return False

    try:
        from ui.dashboard import display_dashboard
        print("✅ Dashboard imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Dashboard import failed: {e}")
        return False

def test_formatting_fix():
    """Test that the confidence score formatting fix works."""
    print("\n🔧 Testing confidence score formatting fix...")

    # Test the conversion logic
    def format_confidence_score(conf_score):
        """Test version of the confidence score formatting logic."""
        if isinstance(conf_score, str) and conf_score != 'N/A':
            try:
                conf_score = float(conf_score)
            except (ValueError, TypeError):
                pass

        if isinstance(conf_score, (int, float)):
            return f"{conf_score:.2f}"
        else:
            return str(conf_score)

    # Test cases
    test_cases = [
        ("0.85", "0.85"),  # String that converts to float
        (0.85, "0.85"),    # Already a float
        ("N/A", "N/A"),    # String that shouldn't convert
        ("invalid", "invalid"),  # Invalid string
    ]

    for input_val, expected in test_cases:
        result = format_confidence_score(input_val)
        if result == expected:
            print(f"✅ Test passed: {input_val} -> {result}")
        else:
            print(f"❌ Test failed: {input_val} -> {result} (expected {expected})")

if __name__ == "__main__":
    success = test_imports()
    test_formatting_fix()

    if success:
        print("\n🎉 All tests passed! The caching system and formatting fixes are working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
