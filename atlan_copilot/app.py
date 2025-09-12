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
from ui.chat_interface import display_chat_interface

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

    st.title("🤖 Atlan Customer Support Copilot")

    # --- Sidebar for Navigation ---
    with st.sidebar:
        st.header("Navigation")
        page = st.selectbox(
            "Choose a page",
            ("Dashboard & Classification", "Live Chat"),
            label_visibility="collapsed"
        )
        st.markdown("---")
        st.info(
            "This application uses AI to automatically classify customer support tickets "
            "and assist with generating responses using Atlan's documentation."
        )
        st.markdown(
            "**Phase:** UI Development (with placeholder backend)"
        )

    # --- Page Rendering ---
    if page == "Dashboard & Classification":
        display_dashboard()
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
