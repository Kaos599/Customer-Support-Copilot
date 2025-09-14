#!/usr/bin/env python3
"""Test script to verify syntax fixes."""

import sys
import os

# Add project paths
sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.join(os.getcwd(), 'atlan_copilot'))

try:
    from scripts.resolve_tickets import resolve_processed_tickets, resolve_processed_tickets_with_progress
    print('✅ Syntax errors fixed - all imports successful')
    print('✅ Progress-aware resolution function available')
except SyntaxError as e:
    print(f'❌ Syntax error still exists: {e}')
except Exception as e:
    print(f'ℹ️ Other error (may be expected): {e}')
