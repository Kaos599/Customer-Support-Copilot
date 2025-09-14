#!/usr/bin/env python3
"""
Quick test to verify schema updates are working correctly.
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = os.path.abspath('.')
sys.path.insert(0, project_root)

async def test_stats():
    from database.mongodb_client import MongoDBClient

    mongo_client = MongoDBClient()
    await mongo_client.connect()
    stats = await mongo_client.get_processing_stats()
    await mongo_client.close()

    print('📊 Current Statistics:')
    for key, value in stats.items():
        print(f'  {key}: {value}')

    # Verify resolved tickets exist
    resolved_tickets = await mongo_client.get_resolved_tickets(5)
    print(f'\n✅ Found {len(resolved_tickets)} resolved tickets in database')

    # Check if tickets have new fields
    all_tickets = await mongo_client.get_all_tickets()
    if all_tickets:
        sample_ticket = all_tickets[0]
        print(f'\n🔍 Sample ticket fields:')
        print(f'  id: {sample_ticket.get("id")}')
        print(f'  status: {sample_ticket.get("status")}')
        print(f'  created_at: {sample_ticket.get("created_at")}')
        print(f'  has confidence_in: {"confidence_in" in sample_ticket}')

if __name__ == "__main__":
    asyncio.run(test_stats())
