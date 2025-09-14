#!/usr/bin/env python3
"""
Script for resolving processed customer support tickets.

This script processes tickets that have been classified and generates
resolutions using RAG for eligible topics or routes them to appropriate teams.
"""

import asyncio
import sys
import os
from typing import List, Dict, Any

# Add project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database.mongodb_client import MongoDBClient
from agents.ticket_orchestrator import TicketOrchestrator


async def resolve_processed_tickets(limit: int = 10) -> Dict[str, Any]:
    """
    Resolve processed tickets using the ticket orchestrator.

    Args:
        limit: Maximum number of tickets to process

    Returns:
        Summary of resolution results
    """
    print(f"Starting ticket resolution process for up to {limit} tickets...")

    # Initialize clients
    mongo_client = MongoDBClient()
    await mongo_client.connect()

    orchestrator = TicketOrchestrator()

    try:
        # Get unprocessed tickets (those without resolution data)
        unprocessed_tickets = await mongo_client.get_unprocessed_tickets_for_resolution(limit)

        if not unprocessed_tickets:
            print("No unprocessed tickets found.")
            return {"status": "success", "message": "No tickets to process", "resolved": 0, "routed": 0}

        print(f"Found {len(unprocessed_tickets)} tickets to resolve")

        resolved_count = 0
        routed_count = 0
        errors = []

        for ticket in unprocessed_tickets:
            try:
                print(f"Processing ticket {ticket.get('id', 'unknown')}...")

                # Check if ticket is already processed
                if not ticket.get('processed', False):
                    # Process unclassified ticket first
                    result = await orchestrator.process_ticket(ticket)
                else:
                    # Resolve already processed ticket
                    result = await orchestrator.resolve_ticket(ticket)

                resolution = result.get('resolution', {})

                if resolution.get('status') == 'resolved':
                    resolved_count += 1
                    print(f"✅ Ticket {ticket.get('id')} resolved with RAG response")
                elif resolution.get('status') == 'routed':
                    routed_count += 1
                    print(f"📋 Ticket {ticket.get('id')} routed to {resolution.get('routed_to', 'team')}")
                else:
                    errors.append(f"Ticket {ticket.get('id')}: {resolution.get('message', 'Unknown error')}")

            except Exception as e:
                error_msg = f"Failed to process ticket {ticket.get('id', 'unknown')}: {str(e)}"
                print(f"❌ {error_msg}")
                errors.append(error_msg)

        # Summary
        summary = {
            "status": "success",
            "resolved": resolved_count,
            "routed": routed_count,
            "errors": errors,
            "total_processed": resolved_count + routed_count
        }

        print("
Resolution Summary:")
        print(f"✅ Resolved with RAG: {resolved_count}")
        print(f"📋 Routed to teams: {routed_count}")
        print(f"❌ Errors: {len(errors)}")

        if errors:
            print("\nErrors encountered:")
            for error in errors[:5]:  # Show first 5 errors
                print(f"  - {error}")
            if len(errors) > 5:
                print(f"  ... and {len(errors) - 5} more errors")

        return summary

    finally:
        await mongo_client.close()


async def resolve_single_ticket(ticket_id: str) -> Dict[str, Any]:
    """
    Resolve a single ticket by ID.

    Args:
        ticket_id: ID of the ticket to resolve

    Returns:
        Resolution result
    """
    print(f"Resolving ticket {ticket_id}...")

    # Initialize clients
    mongo_client = MongoDBClient()
    await mongo_client.connect()

    orchestrator = TicketOrchestrator()

    try:
        # Get ticket by ID
        ticket = await mongo_client.get_processed_ticket_by_id(ticket_id)

        if not ticket:
            return {"status": "error", "message": f"Ticket {ticket_id} not found"}

        # Check if already resolved
        if ticket.get('resolution'):
            return {
                "status": "already_resolved",
                "message": f"Ticket {ticket_id} is already resolved",
                "resolution": ticket['resolution']
            }

        # Resolve the ticket
        result = await orchestrator.resolve_ticket(ticket)

        resolution = result.get('resolution', {})
        return {
            "status": "success",
            "ticket_id": ticket_id,
            "resolution": resolution
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

    finally:
        await mongo_client.close()


async def main():
    """
    Main function for command-line execution.
    """
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python resolve_tickets.py all [limit]  # Resolve multiple tickets")
        print("  python resolve_tickets.py <ticket_id>   # Resolve single ticket")
        return

    command = sys.argv[1]

    if command == "all":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        result = await resolve_processed_tickets(limit)
        print(f"\nFinal result: {result}")
    else:
        # Assume it's a ticket ID
        ticket_id = command
        result = await resolve_single_ticket(ticket_id)
        print(f"\nResult: {result}")


if __name__ == "__main__":
    asyncio.run(main())
