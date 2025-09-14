import streamlit as st
from dotenv import load_dotenv
import os
import sys

# Add project root to the Python path for consistent imports
# The project root is the 'atlan_copilot' directory itself.
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import UI view functions
from ui.dashboard import display_dashboard
from ui.tickets_view import display_tickets_view
from ui.chat_interface import display_chat_interface

# Import data caching utilities
from utils.data_cache import initialize_app_data

def main():
    """
    Main function to configure and run the Streamlit application.
    This acts as the main entry point and router for the app.
    """
    st.set_page_config(
        page_title="Atlan Customer Support Copilot",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Initialize application data on first load
    data_loaded = initialize_app_data()

    # Handle navigation from session state
    if 'current_view' not in st.session_state:
        st.session_state.current_view = "Dashboard & Classification"

    page = st.session_state.current_view

    # --- Sidebar Navigation ---
    with st.sidebar:
        st.header("🎯 Navigation")

        # Navigation buttons
        if st.button("📊 Dashboard", use_container_width=True,
                    type="primary" if page == "Dashboard & Classification" else "secondary"):
            st.session_state.current_view = "Dashboard & Classification"
            st.rerun()

        if st.button("🎫 Tickets", use_container_width=True,
                    type="primary" if page == "Tickets View" else "secondary"):
            st.session_state.current_view = "Tickets View"
            st.rerun()

        if st.button("💬 Chat", use_container_width=True,
                    type="primary" if page == "Live Chat" else "secondary"):
            st.session_state.current_view = "Live Chat"
            st.rerun()

        st.markdown("---")

        # Additional sidebar content
        st.info(
            "🤖 **AI-Powered Support**\n\n"
            "• Automatic ticket classification\n"
            "• AI-generated responses\n"
            "• Knowledge base integration\n"
            "• Smart routing system"
        )

        st.markdown("### 📊 Quick Stats")
        try:
            from database.mongodb_client import MongoDBClient
            import asyncio

            async def get_stats():
                mongo_client = MongoDBClient()
                await mongo_client.connect()
                stats = await mongo_client.get_processing_stats()
                await mongo_client.close()
                return stats

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            stats = loop.run_until_complete(get_stats())

            st.metric("Total Tickets", stats.get("total_tickets", 0))
            st.metric("Processed", stats.get("total_processed", 0))
            st.metric("Resolved", stats.get("total_resolved", 0))
            st.metric("Routed", stats.get("total_routed", 0))
        except:
            st.caption("Stats loading...")

    # Show main header
    st.title("🤖 Atlan Customer Support Copilot")

    st.markdown("---")

    # --- Page Rendering ---
    if page == "Dashboard & Classification":
        display_dashboard()
    elif page == "Tickets View":
        display_tickets_view()
    elif page == "Live Chat":
        display_chat_interface()
    else:
        st.error("Page not found.")

if __name__ == "__main__":
    # Load environment variables from the .env file in the project root
    # To do this, we assume the .env file is in the parent directory of this app.py file
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    load_dotenv(dotenv_path=dotenv_path)
    main()
