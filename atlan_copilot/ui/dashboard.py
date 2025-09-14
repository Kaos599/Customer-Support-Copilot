import streamlit as st
import pandas as pd
import asyncio
from typing import List, Dict, Any
import sys
import os
from datetime import datetime, timedelta

# Add project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database.mongodb_client import MongoDBClient
from agents.classification_agent import ClassificationAgent

import time
import json

@st.cache_data(show_spinner=False) # Spinner is now handled manually
def run_classification_pipeline() -> pd.DataFrame:
    """
    This function runs the full pipeline for the dashboard:
    1. Fetches tickets from MongoDB.
    2. Runs ClassificationAgent on each ticket sequentially with delays to respect API rate limits.
    3. Returns a pandas DataFrame with the combined data.
    This function is cached to prevent re-running on every UI interaction.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # --- 1. Fetch tickets from MongoDB ---
    mongo_client = MongoDBClient()

    async def fetch_tickets_from_db():
        await mongo_client.connect()
        tickets = await mongo_client.get_all_tickets()
        await mongo_client.close()
        return tickets

    status_text = st.empty()
    status_text.info("Fetching tickets from database...")
    tickets_data = loop.run_until_complete(fetch_tickets_from_db())
    status_text.empty()

    if not tickets_data:
        st.error("No tickets found in the database. Please run the `load_sample_data.py` script first.")
        return pd.DataFrame()

    agent = ClassificationAgent()
    if not agent.model:
        st.error("Classification agent could not be initialized. Check API key.")
        return pd.DataFrame()

    # --- Process tickets sequentially to handle rate limits ---
    classified_results = []
    total_tickets = len(tickets_data)
    progress_bar = st.progress(0, text="Initializing classification...")
    status_text = st.empty()

    # Wrap all async operations in a single async function for Streamlit compatibility
    async def process_all_tickets():
        # Connect to MongoDB once for the entire processing pipeline
        await mongo_client.connect()

        try:
            for i, ticket in enumerate(tickets_data):
                status_text.info(f"Processing ticket {i + 1} of {total_tickets}...")

                agent_input = {"subject": ticket.get("subject"), "body": ticket.get("body")}
                result = await agent.execute(agent_input)
                classified_results.append(result)

                # Store the processed ticket in MongoDB
                if result and result.get("classification"):
                    try:
                        stored_id = await mongo_client.store_processed_ticket(ticket, result)
                        if stored_id:
                            print(f"✅ Stored processed ticket {ticket.get('id')} in database")
                        else:
                            print(f"⚠️  Failed to store processed ticket {ticket.get('id')}")
                    except Exception as e:
                        print(f"❌ Error storing ticket {ticket.get('id')}: {e}")
                else:
                    print(f"⚠️  Skipping storage for ticket {ticket.get('id')} - no classification result")

                progress_bar.progress((i + 1) / total_tickets, text=f"Ticket {i+1}/{total_tickets} classified.")

                # Wait after each request to respect rate limits (15 RPM = 4s/request)
                if i < total_tickets - 1:
                    await asyncio.sleep(5)  # 5s delay = 12 RPM, which is safe.

            # Get processing statistics
            stats = await mongo_client.get_processing_stats()
            return stats

        finally:
            # Close MongoDB connection at the very end
            try:
                await mongo_client.close()
            except Exception as e:
                print(f"❌ Error closing MongoDB connection: {e}")

    # Run the async processing
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    stats = loop.run_until_complete(process_all_tickets())

    status_text.success("All tickets classified and stored!")
    time.sleep(2) # Keep success message on screen for a moment
    progress_bar.empty()
    status_text.empty()

    # Display processing statistics
    if stats:
        st.info(f"📊 **Processing Summary:** {stats.get('processed_today', 0)} tickets processed today, {stats.get('total_processed', 0)} total processed")
    else:
        st.warning("Could not retrieve processing statistics. Database connection may have issues.")

    # --- Combine and process data for display ---
    processed_data = []
    for original, result in zip(tickets_data, classified_results):
        if result and result.get("classification"):
            classification = result["classification"]
            processed_data.append({
                "Ticket ID": original.get("id"),
                "Subject": original.get("subject"),
                "Topic(s)": ", ".join(classification.get("topic_tags", ["N/A"])),
                "Sentiment": classification.get("sentiment", "N/A"),
                "Priority": classification.get("priority", "N/A"),
                "Topic Confidence": classification.get("confidence_scores", {}).get("topic"),
                "Sentiment Confidence": classification.get("confidence_scores", {}).get("sentiment"),
                "Priority Confidence": classification.get("confidence_scores", {}).get("priority"),
                "Body": original.get("body")
            })
        else:
            processed_data.append({
                "Ticket ID": original.get("id"),
                "Subject": original.get("subject"),
                "Topic(s)": "Classification Failed",
                "Sentiment": "N/A", "Priority": "N/A",
                "Topic Confidence": 0.0, "Sentiment Confidence": 0.0, "Priority Confidence": 0.0,
                "Body": original.get("body")
            })

    return pd.DataFrame(processed_data)


def display_statistics():
    """
    Displays ticket statistics in metric cards.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    mongo_client = MongoDBClient()

    async def get_stats():
        await mongo_client.connect()
        stats = await mongo_client.get_processing_stats()
        await mongo_client.close()
        return stats

    stats = loop.run_until_complete(get_stats())

    if stats:
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric("Total Tickets", stats.get("total_tickets", 0))

        with col2:
            st.metric("Unprocessed", stats.get("total_unprocessed", 0))

        with col3:
            st.metric("Processed", stats.get("total_processed", 0))

        with col4:
            st.metric("Resolved", stats.get("total_resolved", 0))

        with col5:
            st.metric("Processed Today", stats.get("processed_today", 0))
    else:
        st.warning("Could not retrieve statistics. Database connection may have issues.")


@st.cache_data(show_spinner=False, ttl=300)  # Cache for 5 minutes
def display_overall_analytics_data():
    """
    Displays comprehensive analytics data for all tickets in the system.
    This function is cached and contains no UI widgets.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    mongo_client = MongoDBClient()

    async def get_analytics_data():
        await mongo_client.connect()

        # Get all tickets for analysis
        all_tickets = await mongo_client.get_all_tickets()

        # Get processing statistics
        stats = await mongo_client.get_processing_stats()

        await mongo_client.close()
        return all_tickets, stats

    all_tickets, stats = loop.run_until_complete(get_analytics_data())

    if all_tickets and stats:
        # Create analytics DataFrame
        analytics_data = []
        for ticket in all_tickets:
            analytics_data.append({
                "id": ticket.get("id", ""),
                "processed": ticket.get("processed", False),
                "priority": ticket.get("classification", {}).get("priority", "N/A") if ticket.get("processed") else "Unprocessed",
                "sentiment": ticket.get("classification", {}).get("sentiment", "N/A") if ticket.get("processed") else "Unprocessed",
                "topic_tags": ticket.get("classification", {}).get("topic_tags", []) if ticket.get("processed") else [],
                "created_at": ticket.get("created_at")
            })

        df_analytics = pd.DataFrame(analytics_data)

        # Calculate metrics
        total_tickets = stats.get("total_tickets", 0)
        processed_count = stats.get("total_processed", 0)
        processed_pct = (processed_count / total_tickets * 100) if total_tickets > 0 else 0
        unprocessed_count = stats.get("total_unprocessed", 0)
        unprocessed_pct = (unprocessed_count / total_tickets * 100) if total_tickets > 0 else 0
        processed_today = stats.get("processed_today", 0)

        # Priority Distribution (only for processed tickets)
        priority_data = None
        if processed_count > 0:
            processed_df = df_analytics[df_analytics["processed"] == True]
            priority_counts = processed_df["priority"].value_counts()
            if not priority_counts.empty:
                priority_data = pd.DataFrame({
                    "Priority": priority_counts.index,
                    "Count": priority_counts.values
                })

        # Sentiment Distribution (only for processed tickets)
        sentiment_data = None
        if processed_count > 0:
            processed_df = df_analytics[df_analytics["processed"] == True]
            sentiment_counts = processed_df["sentiment"].value_counts()
            if not sentiment_counts.empty:
                sentiment_data = pd.DataFrame({
                    "Sentiment": sentiment_counts.index,
                    "Count": sentiment_counts.values
                })

        # Topic Analysis (only for processed tickets)
        topic_data = None
        if processed_count > 0:
            processed_df = df_analytics[df_analytics["processed"] == True]
            # Flatten topic tags
            all_topics = []
            for tags in processed_df["topic_tags"]:
                if isinstance(tags, list):
                    all_topics.extend(tags)

            if all_topics:
                topic_counts = pd.Series(all_topics).value_counts().head(10)  # Top 10 topics
                topic_data = pd.DataFrame({
                    "Topic": topic_counts.index,
                    "Count": topic_counts.values
                })

        # Time-based analysis
        df_analytics["created_at"] = pd.to_datetime(df_analytics["created_at"], errors='coerce')
        daily_counts = df_analytics.groupby(df_analytics["created_at"].dt.date).size()
        time_data = daily_counts if not daily_counts.empty else None

        return {
            "stats": stats,
            "total_tickets": total_tickets,
            "processed_count": processed_count,
            "processed_pct": processed_pct,
            "unprocessed_count": unprocessed_count,
            "unprocessed_pct": unprocessed_pct,
            "processed_today": processed_today,
            "priority_data": priority_data,
            "sentiment_data": sentiment_data,
            "topic_data": topic_data,
            "time_data": time_data,
            "daily_counts": daily_counts if not daily_counts.empty else None
        }

    return None


def display_overall_analytics():
    """
    Displays comprehensive analytics for all tickets in the system.
    This function contains UI widgets and calls the cached data function.
    """
    st.markdown("---")

    # Analytics section header with controls
    col1, col2 = st.columns([3, 1])

    with col1:
        st.header("📊 System Analytics Overview")

    with col2:
        if st.button("🔄 Refresh Analytics", key="refresh_analytics"):
            # Clear the cache to force refresh
            display_overall_analytics_data.clear()
            st.rerun()

    # Make analytics expandable to save space
    with st.expander("📈 View Detailed Analytics", expanded=True):
        analytics_data = display_overall_analytics_data()

        if analytics_data:
            stats = analytics_data["stats"]
            total_tickets = analytics_data["total_tickets"]
            processed_count = analytics_data["processed_count"]
            processed_pct = analytics_data["processed_pct"]
            unprocessed_count = analytics_data["unprocessed_count"]
            unprocessed_pct = analytics_data["unprocessed_pct"]
            processed_today = analytics_data["processed_today"]
            priority_data = analytics_data["priority_data"]
            sentiment_data = analytics_data["sentiment_data"]
            topic_data = analytics_data["topic_data"]
            time_data = analytics_data["time_data"]
            daily_counts = analytics_data["daily_counts"]

            # Overall metrics in a nice layout
            st.subheader("📈 Key Metrics")

            # Row 1: Main metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Tickets", total_tickets)

            with col2:
                st.metric("Processed", f"{processed_count} ({processed_pct:.1f}%)")

            with col3:
                st.metric("Unprocessed", f"{unprocessed_count} ({unprocessed_pct:.1f}%)")

            with col4:
                st.metric("Processed Today", processed_today)

            # Row 2: Processing status visualization
            st.subheader("🔄 Processing Status")

            # Display as columns with progress bars
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Processed Tickets**")
                st.progress(processed_pct / 100)
                st.write(f"{processed_count} tickets")

            with col2:
                st.markdown("**Unprocessed Tickets**")
                st.progress(unprocessed_pct / 100)
                st.write(f"{unprocessed_count} tickets")

            # Priority Distribution (only for processed tickets)
            if processed_count > 0 and priority_data is not None:
                st.subheader("🎯 Priority Distribution")

                # Create a bar chart
                st.bar_chart(priority_data.set_index("Priority"), color="#0068C9")

                # Show as table too
                st.dataframe(priority_data, hide_index=True, use_container_width=True)

            # Sentiment Distribution (only for processed tickets)
            if processed_count > 0 and sentiment_data is not None:
                st.subheader("😊 Sentiment Analysis")

                # Create a bar chart
                st.bar_chart(sentiment_data.set_index("Sentiment"), color="#FF4B4B")

                # Show as table
                st.dataframe(sentiment_data, hide_index=True, use_container_width=True)

            # Topic Analysis (only for processed tickets)
            if processed_count > 0 and topic_data is not None:
                st.subheader("🏷️ Top Topics")

                # Create horizontal bar chart for topics
                st.bar_chart(topic_data.set_index("Topic"), horizontal=True, color="#859900")

                # Show as table
                st.dataframe(topic_data, hide_index=True, use_container_width=True)

            # Time-based analysis
            if time_data is not None:
                st.subheader("📅 Ticket Creation Trends")

                # Create a line chart for daily ticket creation
                st.line_chart(time_data, color="#DC3545")

                # Show recent activity
                st.markdown("**Recent Activity (Last 7 days)**")
                last_week = time_data.tail(7)
                if not last_week.empty:
                    recent_df = pd.DataFrame({
                        "Date": last_week.index,
                        "Tickets Created": last_week.values
                    })
                    st.dataframe(recent_df, hide_index=True, use_container_width=True)

        else:
            st.warning("Unable to load analytics data. Please check database connection.")


def process_unprocessed_tickets():
    """
    Provides simple batch processing options for unprocessed tickets with status indicators.
    Uses loaded ticket data for efficiency.
    """
    st.markdown("### ⚡ Process Unprocessed Tickets")

    # Get tickets from session state (already loaded)
    tickets_data = st.session_state.get("ticket_data", [])

    # Filter for unprocessed tickets
    unprocessed_tickets = [t for t in tickets_data if not t.get('processed', False)]
    unprocessed_count = len(unprocessed_tickets)

    # Status indicator
    if unprocessed_count > 0:
        # Visual status card for unprocessed tickets
        st.markdown("""
        <div style="background-color: #fff3e0; padding: 15px; border-radius: 10px; border-left: 5px solid #ff9800; margin-bottom: 15px;">
            <h4 style="color: #f57c00; margin: 0; display: flex; align-items: center;">
                <span style="font-size: 20px; margin-right: 8px;">🟡</span>
                Ready for AI Processing
            </h4>
            <p style="margin: 8px 0 0 0; color: #424242;">
                <strong>{} tickets</strong> waiting for AI classification and analysis.
            </p>
        </div>
        """.format(unprocessed_count), unsafe_allow_html=True)

        # Simple process button
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🚀 Start AI Processing", type="primary", use_container_width=True):
                # Debug: Show that button was clicked
                st.info("🚀 AI Processing started! Classifying tickets...")
                # Use loaded data instead of fetching from DB again
                process_tickets_from_loaded_data(unprocessed_tickets)

        with col2:
            st.markdown("""
            <div style="background-color: #e8f5e8; padding: 10px; border-radius: 5px; text-align: center;">
                <small style="color: #2e7d32;">
                    ⏱️ ~{:.1f} min estimated
                </small>
            </div>
            """.format(unprocessed_count * 0.5), unsafe_allow_html=True)

    else:
        # Success status for all processed
        st.markdown("""
        <div style="background-color: #e8f5e8; padding: 15px; border-radius: 10px; border-left: 5px solid #4caf50;">
            <h4 style="color: #2e7d32; margin: 0; display: flex; align-items: center;">
                <span style="font-size: 20px; margin-right: 8px;">✅</span>
                All Tickets Processed
            </h4>
            <p style="margin: 8px 0 0 0; color: #424242;">
                All tickets have been analyzed and classified by AI.
            </p>
        </div>
        """, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def process_tickets_batch(mode: str, batch_size: int = None, priority_filter: List[str] = None):
    """
    Processes tickets in batches based on the selected mode.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    mongo_client = MongoDBClient()

    async def fetch_and_process_batch():
        await mongo_client.connect()

        try:
            # Determine which tickets to process based on mode
            if mode == "Process All Unprocessed":
                tickets_to_process = await mongo_client.get_unprocessed_tickets()
            elif mode == "Process by Count Limit":
                tickets_to_process = await mongo_client.get_tickets_by_status(processed=False, limit=batch_size)
            elif mode == "Process by Priority":
                # This is complex - we'd need to classify first to know priorities
                # For now, process all and filter results
                tickets_to_process = await mongo_client.get_unprocessed_tickets()
            elif mode == "Process Specific Tickets":
                # This would require ticket selection UI
                tickets_to_process = await mongo_client.get_unprocessed_tickets()
            else:
                tickets_to_process = await mongo_client.get_unprocessed_tickets()

            if not tickets_to_process:
                st.info("No tickets to process.")
                return pd.DataFrame()

            agent = ClassificationAgent()
            if not agent.model:
                st.error("Classification agent could not be initialized. Check API key.")
                return pd.DataFrame()

            # Process tickets sequentially
            classified_results = []
            processed_count = 0
            total_tickets = len(tickets_to_process)

            progress_bar = st.progress(0, text="Initializing batch processing...")
            status_text = st.empty()

            for i, ticket in enumerate(tickets_to_process):
                status_text.info(f"Processing ticket {i + 1} of {total_tickets} (ID: {ticket.get('id', 'N/A')})...")

                agent_input = {"subject": ticket.get("subject"), "body": ticket.get("body")}
                result = await agent.execute(agent_input)

                # Check if result meets priority filter (for priority-based processing)
                should_process = True
                if mode == "Process by Priority" and priority_filter and result and result.get("classification"):
                    ticket_priority = result["classification"].get("priority")
                    if ticket_priority not in priority_filter:
                        should_process = False

                if should_process and result and result.get("classification"):
                    ticket_id = ticket.get("id")
                    if ticket_id:
                        success = await mongo_client.update_ticket_with_classification(ticket_id, result)
                        if success:
                            classified_results.append((ticket, result))
                            processed_count += 1
                            print(f"✅ Updated ticket {ticket_id} with classification")
                        else:
                            print(f"⚠️  Failed to update ticket {ticket_id}")

                progress_bar.progress((i + 1) / total_tickets, text=f"Processed {i+1}/{total_tickets} tickets.")

                # Rate limiting delay (12 RPM = 5s delay)
                if i < total_tickets - 1:
                    await asyncio.sleep(5)

            status_text.success(f"Batch processing complete! Successfully processed {processed_count} tickets.")
            time.sleep(2)
            progress_bar.empty()
            status_text.empty()

            # Return processed data for display
            processed_data = []
            for original, result in classified_results:
                if result and result.get("classification"):
                    classification = result["classification"]
                    processed_data.append({
                        "Ticket ID": original.get("id"),
                        "Subject": original.get("subject"),
                        "Topic(s)": ", ".join(classification.get("topic_tags", ["N/A"])),
                        "Sentiment": classification.get("sentiment", "N/A"),
                        "Priority": classification.get("priority", "N/A"),
                        "Topic Confidence": classification.get("confidence_scores", {}).get("topic"),
                        "Sentiment Confidence": classification.get("confidence_scores", {}).get("sentiment"),
                        "Priority Confidence": classification.get("confidence_scores", {}).get("priority"),
                        "Body": original.get("body")
                    })

            return pd.DataFrame(processed_data)

        finally:
            await mongo_client.close()

    df = loop.run_until_complete(fetch_and_process_batch())

    # Clear analytics cache and trigger dashboard refresh
    if not df.empty:
        display_overall_analytics.clear()
        st.rerun()

    return df


def add_tickets_from_file():
    """
    Provides file upload functionality for adding tickets from CSV or JSON files.
    """
    st.markdown("### Upload Tickets from File")

    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["csv", "json"],
        help="Upload a CSV or JSON file containing ticket data"
    )

    if uploaded_file is not None:
        try:
            file_extension = uploaded_file.name.split('.')[-1].lower()

            if file_extension == 'csv':
                # Handle CSV files
                import io
                df = pd.read_csv(io.StringIO(uploaded_file.getvalue().decode('utf-8')))

                # Validate required columns
                required_cols = ['id', 'subject', 'body']
                missing_cols = [col for col in required_cols if col not in df.columns]

                if missing_cols:
                    st.error(f"CSV file is missing required columns: {', '.join(missing_cols)}")
                    st.info("Required columns: id, subject, body")
                    return

                # Convert to ticket format
                tickets_data = []
                for _, row in df.iterrows():
                    ticket = {
                        'id': str(row['id']),
                        'subject': str(row['subject']),
                        'body': str(row['body'])
                    }
                    tickets_data.append(ticket)

            elif file_extension == 'json':
                # Handle JSON files
                import json
                json_data = json.loads(uploaded_file.getvalue().decode('utf-8'))

                # Support both array of tickets or object with tickets key
                if isinstance(json_data, list):
                    tickets_data = json_data
                elif isinstance(json_data, dict) and 'tickets' in json_data:
                    tickets_data = json_data['tickets']
                else:
                    st.error("JSON file must contain an array of tickets or an object with a 'tickets' key")
                    return

                # Validate ticket structure
                for i, ticket in enumerate(tickets_data):
                    if not isinstance(ticket, dict):
                        st.error(f"Ticket at index {i} is not a valid object")
                        return
                    if 'id' not in ticket or 'subject' not in ticket or 'body' not in ticket:
                        st.error(f"Ticket at index {i} is missing required fields (id, subject, body)")
                        return

            else:
                st.error("Unsupported file type")
                return

            # Display preview
            st.success(f"Successfully parsed {len(tickets_data)} tickets from file")

            with st.expander("Preview first 5 tickets"):
                preview_df = pd.DataFrame([
                    {
                        'ID': ticket.get('id', 'N/A'),
                        'Subject': ticket.get('subject', 'N/A')[:50] + '...' if len(ticket.get('subject', '')) > 50 else ticket.get('subject', 'N/A'),
                        'Body Preview': ticket.get('body', 'N/A')[:100] + '...' if len(ticket.get('body', '')) > 100 else ticket.get('body', 'N/A')
                    }
                    for ticket in tickets_data[:5]
                ])
                st.dataframe(preview_df)

            # Insert button
            if st.button("✅ Confirm & Add Tickets to Database", type="primary"):
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                mongo_client = MongoDBClient()

                async def insert_tickets():
                    await mongo_client.connect()
                    inserted_ids = await mongo_client.insert_tickets(tickets_data)
                    await mongo_client.close()
                    return inserted_ids

                with st.spinner("Adding tickets to database..."):
                    inserted_ids = loop.run_until_complete(insert_tickets())

                if inserted_ids:
                    st.success(f"✅ Successfully added {len(inserted_ids)} tickets to the database!")
                    # Clear analytics cache and refresh the page
                    display_overall_analytics.clear()
                    st.rerun()
                else:
                    st.error("❌ Failed to add tickets to database. Check logs for details.")

        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            st.info("Please ensure your file is properly formatted and contains the required columns/fields.")


def resolve_processed_tickets():
    """
    Provides simple resolution options for tickets with status indicators.
    Uses loaded ticket data for efficiency and parallel processing.
    """
    st.markdown("### 🎯 Resolve All Tickets")

    # Get tickets from session state (already loaded)
    tickets_data = st.session_state.get("ticket_data", [])

    # Filter for tickets that need resolution
    tickets_needing_resolution = []
    for ticket in tickets_data:
        if not ticket.get('processed', False):
            # Unprocessed ticket needs both processing and resolution
            tickets_needing_resolution.append(ticket)
        elif not ticket.get('resolution'):
            # Processed ticket without resolution needs resolution
            tickets_needing_resolution.append(ticket)

    ticket_count = len(tickets_needing_resolution)

    if ticket_count > 0:
        # Check how many are unprocessed vs processed but unresolved
        unprocessed_count = sum(1 for t in tickets_needing_resolution if not t.get('processed', False))
        processed_unresolved_count = ticket_count - unprocessed_count

        # Status indicator based on ticket types
        if unprocessed_count > 0 and processed_unresolved_count > 0:
            # Mixed status - both unprocessed and unresolved
            st.markdown("""
            <div style="background-color: #fff3e0; padding: 15px; border-radius: 10px; border-left: 5px solid #ff9800; margin-bottom: 15px;">
                <h4 style="color: #f57c00; margin: 0; display: flex; align-items: center;">
                    <span style="font-size: 20px; margin-right: 8px;">🔄</span>
                    Mixed Status - Ready for Resolution
                </h4>
                <p style="margin: 8px 0 0 0; color: #424242;">
                    <strong>{} unprocessed tickets</strong> will be classified first, then <strong>{} processed tickets</strong> will be resolved.
                </p>
            </div>
            """.format(unprocessed_count, processed_unresolved_count), unsafe_allow_html=True)

        elif unprocessed_count > 0:
            # Only unprocessed tickets
            st.markdown("""
            <div style="background-color: #fff3e0; padding: 15px; border-radius: 10px; border-left: 5px solid #ff9800; margin-bottom: 15px;">
                <h4 style="color: #f57c00; margin: 0; display: flex; align-items: center;">
                    <span style="font-size: 20px; margin-right: 8px;">🟡</span>
                    Unprocessed Tickets Found
                </h4>
                <p style="margin: 8px 0 0 0; color: #424242;">
                    <strong>{} tickets</strong> need AI classification and resolution.
                </p>
            </div>
            """.format(unprocessed_count), unsafe_allow_html=True)

        else:
            # Only processed but unresolved tickets
            st.markdown("""
            <div style="background-color: #e3f2fd; padding: 15px; border-radius: 10px; border-left: 5px solid #2196f3; margin-bottom: 15px;">
                <h4 style="color: #1976d2; margin: 0; display: flex; align-items: center;">
                    <span style="font-size: 20px; margin-right: 8px;">🎯</span>
                    Ready for AI Resolution
                </h4>
                <p style="margin: 8px 0 0 0; color: #424242;">
                    <strong>{} processed tickets</strong> ready for AI-powered resolution.
                </p>
            </div>
            """.format(processed_unresolved_count), unsafe_allow_html=True)

        # Simple resolve button
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🎯 Start AI Resolution", type="primary", use_container_width=True):
                # Debug: Show that button was clicked
                st.info("🎯 AI Resolution started! Processing tickets in parallel...")

                # Create progress containers
                progress_container = st.container()
                status_container = st.container()

                try:
                    with progress_container:
                        progress_bar = st.progress(0)
                        progress_text = st.empty()

                    with status_container:
                        status_text = st.empty()

                    # Show initial status
                    progress_text.write(f"🎯 Preparing to resolve **{ticket_count} tickets** with parallel processing...")
                    status_text.write("📊 Status: Initializing parallel resolution process...")

                    # Use loaded data instead of fetching from DB again
                    resolve_tickets_with_loaded_data_parallel(tickets_needing_resolution,
                                                            lambda current, total, message: update_progress_parallel(current, total, message))

                    def update_progress_parallel(current, total, message):
                        """Update progress indicators for parallel processing"""
                        if total > 0:
                            progress = min(current / total, 1.0)
                            progress_bar.progress(progress)
                            progress_text.write(f"🎯 Parallel resolution: **{current}/{total}** completed")
                            status_text.write(f"📊 {message}")

                    # Final status update
                    progress_bar.progress(1.0)
                    progress_text.write("✅ Parallel resolution completed!")
                    status_text.write("📊 All tickets processed successfully!")

                except Exception as e:
                    progress_text.write("❌ Resolution setup failed")
                    status_text.write(f"❌ Setup Error: {str(e)}")
                    st.error(f"❌ Resolution setup failed: {str(e)}")

        with col2:
            st.markdown("""
            <div style="background-color: #e8f5e8; padding: 10px; border-radius: 5px; text-align: center;">
                <small style="color: #2e7d32;">
                    ⏱️ ~{:.1f} min estimated (5x faster)
                </small>
            </div>
            """.format(ticket_count * 0.1), unsafe_allow_html=True)

    else:
        # Success status for all resolved
        st.markdown("""
        <div style="background-color: #e8f5e8; padding: 15px; border-radius: 10px; border-left: 5px solid #4caf50;">
            <h4 style="color: #2e7d32; margin: 0; display: flex; align-items: center;">
                <span style="font-size: 20px; margin-right: 8px;">✅</span>
                All Tickets Resolved
            </h4>
            <p style="margin: 8px 0 0 0; color: #424242;">
                All tickets have been processed and resolved by AI.
            </p>
        </div>
        """, unsafe_allow_html=True)

    # Show resolution statistics
    with st.expander("📊 Resolution Statistics"):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        mongo_client = MongoDBClient()

        async def get_resolution_stats():
            await mongo_client.connect()
            resolved = await mongo_client.get_resolved_tickets()
            routed = await mongo_client.get_routed_tickets()
            await mongo_client.close()
            return len(resolved), len(routed)

        resolved_count, routed_count = loop.run_until_complete(get_resolution_stats())

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🤖 Resolved with RAG", resolved_count)
        with col2:
            st.metric("📋 Routed to Teams", routed_count)
        with col3:
            st.metric("📊 Total Resolved", resolved_count + routed_count)

def process_tickets_with_loaded_data_parallel(tickets_data: List[Dict], progress_callback=None):
    """
    Process tickets using already loaded data with parallel classification.

    Args:
        tickets_data: List of ticket dictionaries already loaded from database
        progress_callback: Optional callback for progress updates
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    from agents.classification_agent import ClassificationAgent
    mongo_client = MongoDBClient()
    classification_agent = ClassificationAgent()

    async def process_parallel():
        await mongo_client.connect()

        try:
            # Filter for unprocessed tickets only
            unprocessed_tickets = [t for t in tickets_data if not t.get('processed', False)]

            if not unprocessed_tickets:
                if progress_callback:
                    progress_callback(0, 0, "No unprocessed tickets found")
                return {"processed": 0, "errors": 0, "message": "No unprocessed tickets found"}

            # Process in parallel using the agent's batch method
            classification_results = await classification_agent.classify_ticket_batch(
                unprocessed_tickets,
                progress_callback=progress_callback
            )

            # Process results and update database
            processed_count = 0
            errors = []

            for result in classification_results:
                ticket_id = result.get('ticket_id')
                original_ticket = result.get('original_ticket', {})

                if result.get('error'):
                    errors.append(f"Ticket {ticket_id}: {result['error']}")
                    continue

                # Update ticket with classification results
                try:
                    # Create processed ticket data
                    processed_ticket = original_ticket.copy()
                    processed_ticket.update({
                        "processed": True,
                        "classification": result.get("classification", {}),
                        "confidence_scores": result.get("confidence_scores", {}),
                        "processing_metadata": {
                            "processed_at": datetime.now(),
                            "model_version": "gemini-2.5-flash",
                            "processing_time_seconds": 0,  # Could be calculated if needed
                            "agent_version": "2.0",
                            "status": "completed"
                        },
                        "updated_at": datetime.now()
                    })

                    # Update the ticket in database
                    success = await mongo_client.update_ticket_with_classification(ticket_id, result)
                    if success:
                        processed_count += 1
                        if progress_callback:
                            progress_callback(processed_count, len(unprocessed_tickets),
                                            f"✅ Processed ticket {ticket_id}")
                    else:
                        errors.append(f"Failed to update ticket {ticket_id}")

                except Exception as e:
                    errors.append(f"Error updating ticket {ticket_id}: {str(e)}")

            return {
                "processed": processed_count,
                "errors": len(errors),
                "total": len(unprocessed_tickets),
                "message": f"Processed {processed_count}/{len(unprocessed_tickets)} tickets"
            }

        finally:
            await mongo_client.close()

    result = loop.run_until_complete(process_parallel())

    # Clear analytics cache and trigger dashboard refresh
    if result and result.get("processed", 0) > 0:
        display_overall_analytics.clear()
        st.rerun()

    return result


def resolve_tickets_with_loaded_data_parallel(tickets_data: List[Dict], progress_callback=None):
    """
    Resolve tickets using already loaded data with parallel processing.

    Args:
        tickets_data: List of ticket dictionaries already loaded from database
        progress_callback: Optional callback for progress updates
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    from agents.resolution_agent import ResolutionAgent
    mongo_client = MongoDBClient()
    resolution_agent = ResolutionAgent()

    async def resolve_parallel():
        await mongo_client.connect()

        try:
            # Filter for tickets that need resolution
            tickets_needing_resolution = []
            for ticket in tickets_data:
                if not ticket.get('processed', False):
                    # Unprocessed ticket needs both processing and resolution
                    tickets_needing_resolution.append(ticket)
                elif not ticket.get('resolution'):
                    # Processed ticket without resolution needs resolution
                    tickets_needing_resolution.append(ticket)

            if not tickets_needing_resolution:
                if progress_callback:
                    progress_callback(0, 0, "No tickets need resolution")
                return {"resolved": 0, "routed": 0, "errors": 0, "message": "No tickets need resolution"}

            # Process in parallel using the agent's batch method
            resolution_results = await resolution_agent.resolve_tickets_batch(
                tickets_needing_resolution,
                progress_callback=progress_callback
            )

            # Process results and update database
            resolved_count = 0
            routed_count = 0
            errors = []

            for result in resolution_results:
                ticket_id = result.get('ticket_id')
                resolution = result.get('resolution', {})

                if resolution.get('status') == 'resolved':
                    resolved_count += 1
                    if progress_callback:
                        progress_callback(resolved_count + routed_count, len(tickets_needing_resolution),
                                        f"🤖 Resolved ticket {ticket_id}")
                elif resolution.get('status') == 'routed':
                    routed_count += 1
                    if progress_callback:
                        progress_callback(resolved_count + routed_count, len(tickets_needing_resolution),
                                        f"📋 Routed ticket {ticket_id}")
                elif resolution.get('status') == 'error':
                    errors.append(f"Ticket {ticket_id}: {resolution.get('message', 'Unknown error')}")

            return {
                "resolved": resolved_count,
                "routed": routed_count,
                "errors": len(errors),
                "total": len(tickets_needing_resolution),
                "message": f"Resolved {resolved_count} tickets, routed {routed_count} tickets"
            }

        finally:
            await mongo_client.close()

    result = loop.run_until_complete(resolve_parallel())

    # Clear analytics cache and trigger dashboard refresh
    if result and (result.get("resolved", 0) > 0 or result.get("routed", 0) > 0):
        display_overall_analytics.clear()
        st.rerun()

    return result


def fetch_new_tickets():
    """
    Fetches new tickets that have been added since the last fetch operation.
    Updates the dashboard with new ticket statistics.
    """
    st.markdown("### 🔄 Fetch New Tickets from Database")

    # Initialize session state for tracking last fetch time
    if "last_fetch_time" not in st.session_state:
        st.session_state.last_fetch_time = datetime.utcnow() - timedelta(hours=24)  # Default to last 24 hours

    # Display current fetch status
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Last Fetch", st.session_state.last_fetch_time.strftime("%Y-%m-%d %H:%M"))

    with col2:
        time_since = datetime.utcnow() - st.session_state.last_fetch_time
        st.metric("Time Since Last Fetch", f"{time_since.seconds // 3600}h {(time_since.seconds % 3600) // 60}m ago")

    # Fetch options
    st.markdown("#### Fetch Options")

    fetch_mode = st.radio(
        "Fetch Mode:",
        ["Since Last Fetch", "Last 24 Hours", "Last 7 Days", "All Unprocessed"],
        horizontal=True,
        help="Choose what constitutes 'new' tickets to fetch"
    )

    # Calculate fetch timestamp based on mode
    fetch_timestamp = None
    if fetch_mode == "Since Last Fetch":
        fetch_timestamp = st.session_state.last_fetch_time
    elif fetch_mode == "Last 24 Hours":
        fetch_timestamp = datetime.utcnow() - timedelta(hours=24)
    elif fetch_mode == "Last 7 Days":
        fetch_timestamp = datetime.utcnow() - timedelta(days=7)
    # For "All Unprocessed", we'll fetch all unprocessed tickets

    # Fetch button
    if st.button("🔍 Fetch New Tickets", type="secondary"):
        with st.spinner("Fetching new tickets..."):
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            mongo_client = MongoDBClient()

            async def fetch_tickets():
                await mongo_client.connect()

                if fetch_mode == "All Unprocessed":
                    tickets = await mongo_client.get_unprocessed_tickets()
                else:
                    tickets = await mongo_client.get_new_tickets_since(fetch_timestamp)

                # Update last fetch time
                st.session_state.last_fetch_time = datetime.utcnow()

                await mongo_client.close()
                return tickets

            new_tickets = loop.run_until_complete(fetch_tickets())

            if new_tickets:
                st.success(f"✅ Found {len(new_tickets)} new tickets!")

                # Display fetched tickets
                with st.expander(f"📋 Fetched Tickets ({len(new_tickets)})", expanded=True):
                    # Convert to DataFrame for display
                    ticket_data = []
                    for ticket in new_tickets:
                        ticket_data.append({
                            "ID": ticket.get("id", "N/A"),
                            "Subject": ticket.get("subject", "N/A")[:60] + "..." if len(ticket.get("subject", "")) > 60 else ticket.get("subject", "N/A"),
                            "Status": "Unprocessed" if not ticket.get("processed", False) else "Processed",
                            "Created": ticket.get("created_at", "N/A")
                        })

                    df = pd.DataFrame(ticket_data)
                    st.dataframe(df, height=min(400, len(df) * 35 + 40))

                    # Summary stats
                    unprocessed_count = sum(1 for t in new_tickets if not t.get("processed", False))
                    processed_count = len(new_tickets) - unprocessed_count

                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Unprocessed", unprocessed_count)
                    with col2:
                        st.metric("Already Processed", processed_count)

                # Clear analytics cache and trigger dashboard refresh
                display_overall_analytics.clear()
                st.rerun()
            else:
                st.info("ℹ️ No new tickets found in the selected time range.")

    # Advanced options
    with st.expander("⚙️ Advanced Fetch Options"):
        st.markdown("**Custom Date Range:**")
        col1, col2 = st.columns(2)

        with col1:
            custom_start = st.date_input("From Date", value=datetime.utcnow().date() - timedelta(days=1))

        with col2:
            custom_end = st.date_input("To Date", value=datetime.utcnow().date())

        if st.button("🔍 Fetch Custom Range"):
            custom_start_dt = datetime.combine(custom_start, datetime.min.time())
            custom_end_dt = datetime.combine(custom_end, datetime.max.time())

            with st.spinner("Fetching tickets from custom range..."):
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                mongo_client = MongoDBClient()

                async def fetch_custom_range():
                    await mongo_client.connect()
                    tickets = await mongo_client.get_tickets_with_advanced_filters(
                        date_from=custom_start_dt,
                        date_to=custom_end_dt
                    )
                    await mongo_client.close()
                    return tickets

                custom_tickets = loop.run_until_complete(fetch_custom_range())

                if custom_tickets:
                    st.success(f"✅ Found {len(custom_tickets)} tickets in date range!")

                    # Display summary
                    processed_in_range = sum(1 for t in custom_tickets if t.get("processed", False))
                    unprocessed_in_range = len(custom_tickets) - processed_in_range

                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Processed in Range", processed_in_range)
                    with col2:
                        st.metric("Unprocessed in Range", unprocessed_in_range)
                else:
                    st.info("ℹ️ No tickets found in the specified date range.")


def display_dashboard():
    """
    Renders the main dashboard view with manual controls and analytics.
    """
    st.header("🎫 Atlan Customer Support Copilot Dashboard")

    st.markdown("""
        Manage customer support tickets with AI-powered classification and analytics.
        Use the control buttons below to manage your ticket processing workflow.
    """)

    # Control Buttons Row
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("➕ Add Tickets", type="secondary", use_container_width=True):
            add_tickets_from_file()

    with col2:
        if st.button("🔄 Fetch New Tickets", type="secondary", use_container_width=True):
            fetch_new_tickets()
            st.rerun()

    with col3:
        if st.button("⚡ Process Tickets", type="primary", use_container_width=True):
            # Get loaded ticket data from session state
            tickets_data = st.session_state.get("ticket_data", [])

            if not tickets_data:
                st.warning("No ticket data loaded. Please refresh the page.")
                process_unprocessed_tickets()
            else:
                # Filter for unprocessed tickets
                unprocessed_tickets = [t for t in tickets_data if not t.get('processed', False)]

                if not unprocessed_tickets:
                    st.success("✅ All tickets are already processed!")
                else:
                    # Show processing status indicators
                    st.info(f"⚡ Processing {len(unprocessed_tickets)} tickets...")

                    # Create progress containers
                    progress_container = st.container()
                    status_container = st.container()

                    # Define progress callback function before using it
                    def update_processing_progress(current, total, message, progress_bar, progress_text, status_text):
                        """Update progress indicators for ticket processing"""
                        if total > 0:
                            progress = min(current / total, 1.0)
                            progress_bar.progress(progress)
                            progress_text.write(f"⚡ Processing: **{current}/{total}** completed")
                            status_text.write(f"📊 {message}")

                    try:
                        with progress_container:
                            progress_bar = st.progress(0)
                            progress_text = st.empty()

                        with status_container:
                            status_text = st.empty()

                        # Show initial status
                        progress_text.write(f"⚡ Preparing to process **{len(unprocessed_tickets)} tickets**...")
                        status_text.write("📊 Status: Initializing processing...")

                        # Use parallel processing with progress callback
                        result = process_tickets_with_loaded_data_parallel(unprocessed_tickets,
                                                                        lambda current, total, message: update_processing_progress(current, total, message, progress_bar, progress_text, status_text))

                        # Final status update
                        if result and result.get("processed", 0) > 0:
                            progress_bar.progress(1.0)
                            progress_text.write("✅ Ticket processing completed!")
                            status_text.write(f"📊 Successfully processed {result.get('processed', 0)} tickets!")
                            st.success(f"✅ Successfully processed {result.get('processed', 0)} tickets!")
                        else:
                            progress_text.write("ℹ️ No tickets were processed")
                            status_text.write("📊 Processing complete")

                    except Exception as e:
                        progress_text.write("❌ Processing failed")
                        status_text.write(f"❌ Error: {str(e)}")
                        st.error(f"❌ Processing failed: {str(e)}")

    # Resolution Section
    st.markdown("---")
    st.subheader("🎯 Ticket Resolution")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 Resolve All", type="secondary", use_container_width=True):
            # Get loaded ticket data from session state
            tickets_data = st.session_state.get("ticket_data", [])

            if not tickets_data:
                st.warning("No ticket data loaded. Please refresh the page.")
                resolve_processed_tickets()
            else:
                # Filter for tickets needing resolution
                tickets_needing_resolution = []
                for ticket in tickets_data:
                    if not ticket.get('processed', False) or not ticket.get('resolution'):
                        tickets_needing_resolution.append(ticket)

                if not tickets_needing_resolution:
                    st.success("✅ All tickets are already resolved!")
                else:
                    # Show resolution status indicators
                    st.info(f"🎯 Resolving {len(tickets_needing_resolution)} tickets...")

                    # Create progress containers
                    progress_container = st.container()
                    status_container = st.container()

                    # Define progress callback function before using it
                    def update_resolution_progress(current, total, message, progress_bar, progress_text, status_text):
                        """Update progress indicators for ticket resolution"""
                        if total > 0:
                            progress = min(current / total, 1.0)
                            progress_bar.progress(progress)
                            progress_text.write(f"🎯 Resolution: **{current}/{total}** completed")
                            status_text.write(f"📊 {message}")

                    try:
                        with progress_container:
                            progress_bar = st.progress(0)
                            progress_text = st.empty()

                        with status_container:
                            status_text = st.empty()

                        # Show initial status
                        progress_text.write(f"🎯 Preparing to resolve **{len(tickets_needing_resolution)} tickets**...")
                        status_text.write("📊 Status: Initializing resolution...")

                        # Use parallel resolution with progress callback
                        result = resolve_tickets_with_loaded_data_parallel(tickets_needing_resolution,
                                                                        lambda current, total, message: update_resolution_progress(current, total, message, progress_bar, progress_text, status_text))

                        # Final status update
                        if result and (result.get("resolved", 0) > 0 or result.get("routed", 0) > 0):
                            progress_bar.progress(1.0)
                            progress_text.write("✅ Ticket resolution completed!")
                            resolved_count = result.get("resolved", 0)
                            routed_count = result.get("routed", 0)
                            status_text.write(f"📊 Resolved {resolved_count} tickets, routed {routed_count} tickets!")
                            st.success(f"✅ Successfully resolved {resolved_count} tickets and routed {routed_count} tickets!")
                        else:
                            progress_text.write("ℹ️ No tickets were resolved")
                            status_text.write("📊 Resolution complete")

                    except Exception as e:
                        progress_text.write("❌ Resolution failed")
                        status_text.write(f"❌ Error: {str(e)}")
                        st.error(f"❌ Resolution failed: {str(e)}")

    with col2:
        if st.button("📊 View Resolved", type="secondary", use_container_width=True):
            st.info("Resolved tickets view will be implemented")

    with col3:
        if st.button("📋 View Routed", type="secondary", use_container_width=True):
            st.info("Routed tickets view will be implemented")

    # Statistics Display
    display_statistics()

    # Overall Analytics Section
    display_overall_analytics()

    # Add tabs for different views
    tab1, tab2 = st.tabs(["🎫 All Tickets", "📈 Processed Tickets History"])

    with tab1:
        st.subheader("All Tickets Overview")

        # Load all tickets from cached session state
        tickets_data = st.session_state.get("ticket_data", [])

        # Show cache status
        if st.session_state.get("data_cached_at"):
            cache_time = st.session_state.data_cached_at
            st.caption(f"📊 Data last updated: {cache_time.strftime('%Y-%m-%d %H:%M:%S')}")

        if tickets_data:
            # Convert to DataFrame for display
            ticket_data = []
            for ticket in tickets_data:
                classification = ticket.get("classification", {})
                confidence_scores = ticket.get("confidence_scores", {})

                ticket_data.append({
                    "Ticket ID": ticket.get("id", "N/A"),
                    "Subject": ticket.get("subject", "N/A"),
                    "Status": "Processed" if ticket.get("processed", False) else "Unprocessed",
                    "Topic(s)": ", ".join(classification.get("topic_tags", ["N/A"])) if ticket.get("processed") else "Not processed",
                    "Sentiment": classification.get("sentiment", "N/A") if ticket.get("processed") else "Not processed",
                    "Priority": classification.get("priority", "N/A") if ticket.get("processed") else "Not processed",
                    "Created": ticket.get("created_at", "N/A")
                })

            df = pd.DataFrame(ticket_data)

            # Advanced filters
            with st.expander("🔍 Advanced Filters", expanded=False):
                col1, col2, col3 = st.columns(3)

                with col1:
                    status_filter = st.selectbox(
                        "Status:",
                        ["All", "Processed", "Unprocessed"],
                        key="status_filter"
                    )

                with col2:
                    priority_options = ["All"] + sorted([p for p in df["Priority"].unique() if p != "Not processed"])
                    priority_filter = st.multiselect(
                        "Priorities:",
                        priority_options,
                        default=["All"] if "All" in priority_options else [],
                        key="priority_multiselect"
                    )
                    # Convert multiselect to single value for backward compatibility
                    if "All" in priority_filter or len(priority_filter) == 0:
                        priority_filter = "All"
                    elif len(priority_filter) == 1:
                        priority_filter = priority_filter[0]
                    else:
                        priority_filter = priority_filter  # Keep as list

                with col3:
                    sentiment_options = ["All"] + sorted([s for s in df["Sentiment"].unique() if s != "Not processed"])
                    sentiment_filter = st.multiselect(
                        "Sentiments:",
                        sentiment_options,
                        default=["All"] if "All" in sentiment_options else [],
                        key="sentiment_multiselect"
                    )
                    if "All" in sentiment_filter or len(sentiment_filter) == 0:
                        sentiment_filter = "All"
                    elif len(sentiment_filter) == 1:
                        sentiment_filter = sentiment_filter[0]
                    else:
                        sentiment_filter = sentiment_filter  # Keep as list

                # Date range filters
                col1, col2 = st.columns(2)
                with col1:
                    date_from = st.date_input(
                        "From Date:",
                        value=None,
                        key="date_from_filter"
                    )

                with col2:
                    date_to = st.date_input(
                        "To Date:",
                        value=None,
                        key="date_to_filter"
                    )

                # Text search
                search_text = st.text_input(
                    "Search in Subject/Body:",
                    placeholder="Enter keywords...",
                    key="text_search_filter"
                )

                # Apply filters button
                if st.button("Apply Filters", key="apply_filters"):
                    # Apply status filter
                    if status_filter != "All":
                        df = df[df["Status"] == status_filter]

                    # Apply priority filter
                    if priority_filter != "All":
                        if isinstance(priority_filter, list):
                            df = df[df["Priority"].isin(priority_filter)]
                        else:
                            df = df[df["Priority"] == priority_filter]

                    # Apply sentiment filter
                    if sentiment_filter != "All":
                        if isinstance(sentiment_filter, list):
                            df = df[df["Sentiment"].isin(sentiment_filter)]
                        else:
                            df = df[df["Sentiment"] == sentiment_filter]

                    # Apply date filters
                    if date_from:
                        df = df[pd.to_datetime(df["Created"]) >= pd.to_datetime(date_from)]
                    if date_to:
                        df = df[pd.to_datetime(df["Created"]) <= pd.to_datetime(date_to)]

                    # Apply text search
                    if search_text:
                        # For this simple implementation, we'll search in the displayed DataFrame
                        # In production, this should be done at the database level
                        mask = (
                            df["Subject"].str.contains(search_text, case=False, na=False) |
                            df["Topic(s)"].str.contains(search_text, case=False, na=False) |
                            df["Sentiment"].str.contains(search_text, case=False, na=False)
                        )
                        df = df[mask]

                    st.success(f"✅ Filters applied! Showing {len(df)} tickets.")

            # Simple filters (always visible)
            col1, col2 = st.columns(2)

            with col1:
                quick_status = st.selectbox(
                    "Quick Status Filter:",
                    ["All", "Processed", "Unprocessed"],
                    key="quick_status"
                )

            with col2:
                quick_search = st.text_input(
                    "Quick Search:",
                    placeholder="Ticket ID or keyword...",
                    key="quick_search"
                )

            # Apply quick filters
            if quick_status != "All":
                df = df[df["Status"] == quick_status]

            if quick_search:
                mask = (
                    df["Ticket ID"].str.contains(quick_search, case=False, na=False) |
                    df["Subject"].str.contains(quick_search, case=False, na=False)
                )
                df = df[mask]

            st.dataframe(df, height=400)
        else:
            st.info("No tickets found in the database. Use the 'Add Tickets' button to upload tickets.")

    with tab2:
        st.subheader("Processed Tickets History")
        display_processed_tickets_history()

def display_processed_tickets_history():
    """
    Displays the processed tickets history from MongoDB.
    """
    # Button to load processed tickets
    if st.button("🔄 Load Processed Tickets History", type="secondary"):
        display_processed_tickets()

@st.cache_data(show_spinner=False)
def display_processed_tickets():
    """
    Loads and displays processed tickets from MongoDB.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    mongo_client = MongoDBClient()

    async def load_processed_tickets():
        await mongo_client.connect()
        tickets = await mongo_client.get_processed_tickets(limit=100)
        stats = await mongo_client.get_processing_stats()
        await mongo_client.close()
        return tickets, stats

    tickets_data, stats = loop.run_until_complete(load_processed_tickets())

    if not tickets_data:
        st.info("No processed tickets found in the database. Process some tickets first to see history.")
        return

    # Display processing statistics
    if stats:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Processed", stats.get("total_processed", 0))

        with col2:
            st.metric("Processed Today", stats.get("processed_today", 0))

        with col3:
            # Calculate processing rate
            priority_dist = stats.get("priority_distribution", {})
            if priority_dist:
                most_common_priority = max(priority_dist.items(), key=lambda x: x[1])
                st.metric("Top Priority", f"{most_common_priority[0]} ({most_common_priority[1]})")
            else:
                st.metric("Top Priority", "N/A")

    # Display priority distribution chart
    if stats and stats.get("priority_distribution"):
        st.subheader("Priority Distribution")
        priority_data = pd.DataFrame(
            list(stats["priority_distribution"].items()),
            columns=["Priority", "Count"]
        )
        st.bar_chart(priority_data.set_index("Priority"), color="#0068C9")

    st.markdown("---")

    # Display processed tickets table
    st.subheader("Processed Tickets")

    processed_data = []
    for ticket in tickets_data:
        classification = ticket.get("classification", {})
        confidence_scores = ticket.get("confidence_scores", {})
        processing_metadata = ticket.get("processing_metadata", {})

        processed_data.append({
            "Ticket ID": ticket.get("ticket_id", "N/A"),
            "Subject": ticket.get("subject", "N/A")[:50] + "..." if len(ticket.get("subject", "")) > 50 else ticket.get("subject", "N/A"),
            "Topic(s)": ", ".join(classification.get("topic_tags", ["N/A"])),
            "Sentiment": classification.get("sentiment", "N/A"),
            "Priority": classification.get("priority", "N/A"),
            "Topic Confidence": confidence_scores.get("topic", 0.0),
            "Sentiment Confidence": confidence_scores.get("sentiment", 0.0),
            "Priority Confidence": confidence_scores.get("priority", 0.0),
            "Processed At": processing_metadata.get("processed_at", "N/A").strftime("%Y-%m-%d %H:%M") if processing_metadata.get("processed_at") else "N/A",
            "Model Version": processing_metadata.get("model_version", "N/A")
        })

    df = pd.DataFrame(processed_data)

    # Add search functionality
    search_term = st.text_input("🔍 Search tickets by subject or ID:", "")
    if search_term:
        df = df[
            df["Ticket ID"].str.contains(search_term, case=False, na=False) |
            df["Subject"].str.contains(search_term, case=False, na=False)
        ]

    # Add priority filter
    priority_filter = st.selectbox(
        "Filter by Priority:",
        ["All"] + sorted(df["Priority"].unique().tolist())
    )
    if priority_filter != "All":
        df = df[df["Priority"] == priority_filter]

    st.dataframe(df, height=400)

    # Export functionality for processed tickets
    if st.button("📥 Export Processed Tickets as CSV"):
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f'processed_tickets_{pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")}.csv',
            mime='text/csv',
            key="processed_download"
        )
