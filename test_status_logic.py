#!/usr/bin/env python3
"""
Test the updated status logic for ticket counting.
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

async def test_stats():
    from database.mongodb_client import MongoDBClient

    mongo_client = MongoDBClient()
    await mongo_client.connect()
    stats = await mongo_client.get_processing_stats()
    await mongo_client.close()

    print('📊 Updated Statistics:')
    for key, value in stats.items():
        print(f'  {key}: {value}')

    # Check a sample resolved ticket
    resolved_tickets = await mongo_client.get_resolved_tickets(1)
    if resolved_tickets:
        ticket = resolved_tickets[0]
        print(f'\n✅ Sample resolved ticket: {ticket.get("id")}')
        print(f'   processed: {ticket.get("processed")}')
        print(f'   status: {ticket.get("status")}')
        print(f'   resolution.status: {ticket.get("resolution", {}).get("status")}')

    # Check a sample processed ticket
    processed_tickets = await mongo_client.get_processed_tickets(1)
    if processed_tickets:
        ticket = processed_tickets[0]
        print(f'\n✅ Sample processed ticket: {ticket.get("id")}')
        print(f'   processed: {ticket.get("processed")}')
        print(f'   status: {ticket.get("status")}')

if __name__ == "__main__":
    asyncio.run(test_stats())
