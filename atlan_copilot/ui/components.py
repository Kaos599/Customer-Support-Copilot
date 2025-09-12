"""
This file is intended to hold reusable Streamlit components for the Atlan Copilot UI.

As the application grows, any UI elements that are used in multiple places
(e.g., custom headers, footers, specific data display cards, styled containers)
should be abstracted into functions here to maintain a consistent look and feel and
to keep the code DRY (Don't Repeat Yourself).

Currently, no components have been abstracted as the UI is still simple,
but this file establishes the pattern for future development.
"""

# Example of a potential reusable component that could be added in the future:
#
# import streamlit as st
#
# def display_app_header():
#     """Displays a consistent header and sub-header across all pages."""
#     st.title("🤖 Atlan Customer Support Copilot")
#     st.markdown("---")
#
# def display_error_message(message: str):
#     """Formats and displays a consistent error message."""
#     st.error(f"An error occurred: {message}", icon="🚨")
#
