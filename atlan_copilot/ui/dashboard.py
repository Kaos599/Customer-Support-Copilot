import streamlit as st
import pandas as pd
import asyncio
from typing import List, Dict, Any
import sys
import os

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

    async def classify_all_sequentially():
        for i, ticket in enumerate(tickets_data):
            status_text.info(f"Processing ticket {i + 1} of {total_tickets}...")

            agent_input = {"subject": ticket.get("subject"), "body": ticket.get("body")}
            result = await agent.execute(agent_input)
            classified_results.append(result)

            progress_bar.progress((i + 1) / total_tickets, text=f"Ticket {i+1}/{total_tickets} classified.")

            # Wait after each request to respect rate limits (15 RPM = 4s/request)
            if i < total_tickets - 1:
                await asyncio.sleep(5)  # 5s delay = 12 RPM, which is safe.

    loop.run_until_complete(classify_all_sequentially())

    status_text.success("All tickets classified!")
    time.sleep(2) # Keep success message on screen for a moment
    progress_bar.empty()
    status_text.empty()

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


def display_dashboard():
    """
    Renders the main dashboard view with analytics and a data table.
    """
    st.header("Ticket Dashboard & Bulk Classification")
    st.markdown("""
        This dashboard loads all sample tickets, runs them through the AI classification agent in a batch,
        and displays the results below. The entire process is cached for performance, so it only runs once per session.
    """)

    df = run_classification_pipeline()

    if df is not None and not df.empty:
        st.subheader("High-Level Analytics")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("##### Sentiment Distribution")
            sentiment_counts = df['Sentiment'].value_counts()
            st.bar_chart(sentiment_counts, color="#FF4B4B")

        with col2:
            st.markdown("##### Priority Breakdown")
            priority_counts = df['Priority'].value_counts()
            st.bar_chart(priority_counts, color="#0068C9")

        st.markdown("---")

        st.subheader("Classified Tickets")

        # This function is now defined inside display_dashboard to capture df in its scope
        @st.cache_data
        def convert_df_to_csv(df_to_convert):
            return df_to_convert.to_csv(index=False).encode('utf-8')

        csv = convert_df_to_csv(df)

        st.download_button(
             label="📥 Download Results as CSV",
             data=csv,
             file_name='classified_tickets.csv',
             mime='text/csv',
        )

        # The deprecation warning for use_container_width is addressed by removing it,
        # as st.dataframe uses the full container width by default.
        st.dataframe(df, height=500)

    else:
        st.warning("Could not load or process ticket data. Check logs for errors.")
