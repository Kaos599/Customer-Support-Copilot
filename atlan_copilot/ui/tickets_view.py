import streamlit as st
import asyncio
from typing import List, Dict, Any, Optional
import sys
import os
from datetime import datetime

# Add project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database.mongodb_client import MongoDBClient


def fetch_processed_tickets_from_db() -> tuple[List[Dict[str, Any]], datetime]:
    """
    Fetch processed tickets data from MongoDB.

    Returns:
        tuple: (processed_tickets, timestamp)
    """
    async def fetch_tickets():
        mongo_client = MongoDBClient()
        await mongo_client.connect()
        try:
            tickets = await mongo_client.get_processed_tickets(limit=1000)
            return tickets
        finally:
            await mongo_client.close()

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    tickets = loop.run_until_complete(fetch_tickets())
    return tickets, datetime.now()


def display_tickets_view():
    """
    Displays the tickets view with card-based layout showing all processed tickets.
    Each card displays ticket ID, subject, status indicators, and pill-shaped badges.
    """
    st.header("🎫 Tickets View")
    st.markdown("""
    Browse all processed customer support tickets in a card-based layout.
    Each card shows key ticket information with visual status indicators and categorized badges.
    """)

    # Fetch processed tickets from database
    with st.spinner("Loading tickets..."):
        tickets_data, fetch_time = fetch_processed_tickets_from_db()

    if not tickets_data:
        st.info("No processed tickets found. Process some tickets in the Dashboard first.")
        return

    # Show data status
    st.caption(f"📊 Data last updated: {fetch_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Add refresh button
    if st.button("🔄 Refresh Data", key="refresh_tickets"):
        st.rerun()

    # Filters section
    st.subheader("🔍 Filters")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # Priority filter
        priorities = ["All"] + list(set(ticket.get('classification', {}).get('priority', 'Unknown')
                                       for ticket in tickets_data))
        selected_priority = st.selectbox("Priority", priorities, key="priority_filter")

    with col2:
        # Sentiment filter
        sentiments = ["All"] + list(set(ticket.get('classification', {}).get('sentiment', 'Unknown')
                                      for ticket in tickets_data))
        selected_sentiment = st.selectbox("Sentiment", sentiments, key="sentiment_filter")

    with col3:
        # Status filter (based on priority for now)
        status_options = ["All", "High Priority", "Medium Priority", "Low Priority"]
        selected_status = st.selectbox("Status", status_options, key="status_filter")

    with col4:
        # Text search
        search_query = st.text_input("Search tickets", placeholder="Search by subject or ID...",
                                   key="search_filter")

    # Apply filters
    filtered_tickets = tickets_data.copy()

    if selected_priority != "All":
        filtered_tickets = [t for t in filtered_tickets
                          if t.get('classification', {}).get('priority') == selected_priority]

    if selected_sentiment != "All":
        filtered_tickets = [t for t in filtered_tickets
                          if t.get('classification', {}).get('sentiment') == selected_sentiment]

    if selected_status != "All":
        priority_map = {
            "High Priority": "P0 (High)",
            "Medium Priority": "P1 (Medium)",
            "Low Priority": "P2 (Low)"
        }
        expected_priority = priority_map.get(selected_status)
        if expected_priority:
            filtered_tickets = [t for t in filtered_tickets
                              if t.get('classification', {}).get('priority') == expected_priority]

    if search_query:
        search_lower = search_query.lower()
        filtered_tickets = [t for t in filtered_tickets
                          if (search_lower in t.get('subject', '').lower() or
                              search_lower in t.get('id', '').lower())]

    # Display results count
    st.markdown(f"**Showing {len(filtered_tickets)} of {len(tickets_data)} tickets**")

    # Display tickets in a grid layout
    if filtered_tickets:
        # Create a responsive grid (3 cards per row on desktop)
        cols_per_row = 3

        # Group tickets into rows
        ticket_rows = [filtered_tickets[i:i + cols_per_row]
                      for i in range(0, len(filtered_tickets), cols_per_row)]

        for row in ticket_rows:
            cols = st.columns(cols_per_row)
            for i, ticket in enumerate(row):
                with cols[i]:
                    display_ticket_card(ticket)
    else:
        st.info("No tickets match the current filters.")


def display_ticket_card(ticket: Dict[str, Any]):
    """
    Display a single ticket as a card with all required information.

    Args:
        ticket: Dictionary containing ticket data
    """
    # Extract ticket information
    ticket_id = ticket.get('id', 'Unknown')
    subject = ticket.get('subject', 'No subject')
    classification = ticket.get('classification', {})
    priority = classification.get('priority', 'Unknown')
    sentiment = classification.get('sentiment', 'Unknown')
    topic_tags = classification.get('topic_tags', [])

    # Truncate subject if too long
    if len(subject) > 60:
        subject = subject[:57] + "..."

    # Get status color based on priority
    status_color = get_status_color(priority)

    # Card container with border
    with st.container(border=True):
        # Header with ID and status indicator
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**🎫 {ticket_id}**")
        with col2:
            # Status indicator badge
            st.markdown(f'<div style="text-align: right;"><span style="background-color: {status_color}; '
                       f'color: white; padding: 2px 8px; border-radius: 10px; font-size: 12px;">'
                       f'{priority.split(" ")[0]}</span></div>',
                       unsafe_allow_html=True)

        # Subject
        st.markdown(f"**{subject}**")

        # Topic tags as pills
        if topic_tags:
            st.markdown("**Topics:**")
            pill_html = ""
            for tag in topic_tags[:3]:  # Show max 3 tags
                pill_html += f'<span style="background-color: #e3f2fd; color: #1976d2; padding: 2px 8px; ' \
                           f'margin: 2px; border-radius: 12px; font-size: 12px; display: inline-block;">{tag}</span> '
            if len(topic_tags) > 3:
                pill_html += f'<span style="background-color: #f5f5f5; color: #666; padding: 2px 8px; ' \
                           f'margin: 2px; border-radius: 12px; font-size: 12px; display: inline-block;">+{len(topic_tags)-3}</span>'
            st.markdown(pill_html, unsafe_allow_html=True)

        # Sentiment and Priority pills in a row
        sentiment_color = get_sentiment_color(sentiment)
        priority_color = get_priority_color(priority)

        pills_col1, pills_col2 = st.columns(2)
        with pills_col1:
            st.markdown(f'<span style="background-color: {sentiment_color}; color: white; padding: 2px 8px; '
                       f'border-radius: 12px; font-size: 12px;">{sentiment}</span>',
                       unsafe_allow_html=True)
        with pills_col2:
            st.markdown(f'<span style="background-color: {priority_color}; color: white; padding: 2px 8px; '
                       f'border-radius: 12px; font-size: 12px;">{priority}</span>',
                       unsafe_allow_html=True)

        # Creation date
        created_at = ticket.get('created_at')
        if isinstance(created_at, str):
            try:
                # Try to parse the date string
                if 'T' in created_at:
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                else:
                    dt = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S.%f')
                formatted_date = dt.strftime('%b %d, %Y')
            except:
                formatted_date = created_at[:10]  # Fallback to first 10 chars
        else:
            formatted_date = "Unknown"

        st.caption(f"Created: {formatted_date}")

        # Expandable section for full details
        with st.expander("View Details", expanded=False):
            st.markdown("**Full Subject:**")
            st.write(ticket.get('subject', 'N/A'))

            st.markdown("**Body:**")
            body = ticket.get('body', 'N/A')
            if len(body) > 500:
                st.write(body[:500] + "...")
            else:
                st.write(body)

            # Processing metadata
            processing_meta = ticket.get('processing_metadata', {})
            if processing_meta:
                st.markdown("**Processing Info:**")
                st.write(f"- Model: {processing_meta.get('model_version', 'N/A')}")

                # Confidence scores - convert to float if string
                confidence_scores = ticket.get('confidence_scores', {})
                topic_conf = confidence_scores.get('topic', 'N/A')
                sentiment_conf = confidence_scores.get('sentiment', 'N/A')
                priority_conf = confidence_scores.get('priority', 'N/A')

                # Convert to float if string
                try:
                    if isinstance(topic_conf, str) and topic_conf != 'N/A':
                        topic_conf = float(topic_conf)
                    if isinstance(sentiment_conf, str) and sentiment_conf != 'N/A':
                        sentiment_conf = float(sentiment_conf)
                    if isinstance(priority_conf, str) and priority_conf != 'N/A':
                        priority_conf = float(priority_conf)
                except (ValueError, TypeError):
                    pass  # Keep as is if conversion fails

                # Format confidence scores
                if isinstance(topic_conf, (int, float)):
                    st.write(f"- Confidence - Topic: {topic_conf:.2f}")
                else:
                    st.write(f"- Confidence - Topic: {topic_conf}")

                if isinstance(sentiment_conf, (int, float)):
                    st.write(f"- Confidence - Sentiment: {sentiment_conf:.2f}")
                else:
                    st.write(f"- Confidence - Sentiment: {sentiment_conf}")

                if isinstance(priority_conf, (int, float)):
                    st.write(f"- Confidence - Priority: {priority_conf:.2f}")
                else:
                    st.write(f"- Confidence - Priority: {priority_conf}")

                # Handle datetime object properly
                processed_at = processing_meta.get('processed_at', 'N/A')
                if isinstance(processed_at, datetime):
                    processed_str = processed_at.strftime('%Y-%m-%d %H:%M:%S')
                    st.write(f"- Processed: {processed_str}")
                else:
                    # Handle string format or fallback
                    processed_str = str(processed_at)[:19] if processed_at != 'N/A' else 'N/A'
                    st.write(f"- Processed: {processed_str}")


def get_status_color(priority: str) -> str:
    """
    Get color for status indicator based on priority.

    Args:
        priority: Priority level string

    Returns:
        Hex color code
    """
    if "P0" in priority or "High" in priority:
        return "#dc3545"  # Red
    elif "P1" in priority or "Medium" in priority:
        return "#ffc107"  # Yellow/Orange
    elif "P2" in priority or "Low" in priority:
        return "#28a745"  # Green
    else:
        return "#6c757d"  # Gray


def get_sentiment_color(sentiment: str) -> str:
    """
    Get color for sentiment pill.

    Args:
        sentiment: Sentiment string

    Returns:
        Hex color code
    """
    sentiment_colors = {
        "Frustrated": "#dc3545",  # Red
        "Angry": "#dc3545",       # Red
        "Curious": "#17a2b8",     # Blue
        "Neutral": "#6c757d",     # Gray
        "Happy": "#28a745",       # Green
        "Satisfied": "#28a745"    # Green
    }
    return sentiment_colors.get(sentiment, "#6c757d")


def get_priority_color(priority: str) -> str:
    """
    Get color for priority pill.

    Args:
        priority: Priority string

    Returns:
        Hex color code
    """
    if "P0" in priority or "High" in priority:
        return "#dc3545"  # Red
    elif "P1" in priority or "Medium" in priority:
        return "#ffc107"  # Yellow
    elif "P2" in priority or "Low" in priority:
        return "#28a745"  # Green
    else:
        return "#6c757d"  # Gray
