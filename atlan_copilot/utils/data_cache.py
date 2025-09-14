"""
Data initialization utilities for the Atlan Customer Support Copilot.

This module handles initial data loading from MongoDB with proper loading indicators.
"""

import streamlit as st
import asyncio
from typing import List, Dict, Any
import sys
import os
from datetime import datetime

# Add project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database.mongodb_client import MongoDBClient


def initialize_app_data():
    """
    Initialize application data on first load by fetching from MongoDB.
    Shows loading indicator and blocks access until data is loaded.
    """
    if "app_data_initialized" not in st.session_state:
        # Show loading message
        with st.spinner("🔄 Fetching data from MongoDB... Please wait."):
            st.info("📡 Connecting to database and loading ticket data...")
            try:
                # Fetch all tickets from database
                tickets_data, fetch_time = fetch_all_tickets_from_db()

                # Store in session state for easy access
                st.session_state.ticket_data = tickets_data
                st.session_state.data_cached_at = fetch_time
                st.session_state.app_data_initialized = True

                st.success(f"✅ Application data loaded successfully! ({len(tickets_data)} tickets)")
                return True

            except Exception as e:
                st.error(f"❌ Failed to initialize application data: {str(e)}")
                st.session_state.app_data_initialized = False
                return False

    return True


def fetch_all_tickets_from_db() -> tuple[List[Dict[str, Any]], datetime]:
    """
    Fetch all ticket data from MongoDB.

    Returns:
        tuple: (tickets_data, timestamp) where timestamp indicates when data was fetched
    """
    async def fetch_tickets():
        mongo_client = MongoDBClient()
        await mongo_client.connect()
        try:
            # Fetch both processed and unprocessed tickets
            processed_tickets = await mongo_client.get_processed_tickets(limit=1000)
            unprocessed_tickets = await mongo_client.get_unprocessed_tickets(limit=1000)
            return processed_tickets, unprocessed_tickets
        finally:
            await mongo_client.close()

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    processed_tickets, unprocessed_tickets = loop.run_until_complete(fetch_tickets())

    # Combine tickets for dashboard display
    all_tickets = processed_tickets + unprocessed_tickets

    return all_tickets, datetime.now()
