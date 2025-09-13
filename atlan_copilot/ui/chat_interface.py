import streamlit as st
import time
import asyncio
import sys
import os
from typing import Dict, Any, Optional

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agents.orchestrator import Orchestrator

def display_chat_interface():
    """
    Renders the live chat interface with actual RAG agent integration.
    This function manages the chat session and displays messages.
    The backend is now connected to the full AI pipeline.
    """
    st.header("🤖 Live AI Support Assistant")
    st.markdown("""
        Interact with the AI assistant in real-time. Ask questions about Atlan, customer tickets, or documentation.
        The assistant will search through Atlan's documentation and provide accurate, cited responses.
    """)

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I'm here to help you with Atlan. Ask me anything about our platform, documentation, or customer support!"}
        ]

    if "orchestrator" not in st.session_state:
        try:
            st.session_state.orchestrator = Orchestrator()
        except Exception as e:
            st.error(f"Failed to initialize AI assistant: {str(e)}")
            return

    # Display prior chat messages from history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            # Show additional metadata for assistant messages
            if message["role"] == "assistant" and "metadata" in message:
                metadata = message["metadata"]
                if metadata.get("classification"):
                    with st.expander("📋 Query Analysis", expanded=False):
                        classification = metadata["classification"]
                        st.write(f"**Topic Tags:** {', '.join(classification.get('topic_tags', []))}")
                        st.write(f"**Sentiment:** {classification.get('sentiment', 'N/A')}")
                        st.write(f"**Priority:** {classification.get('priority', 'N/A')}")

                if metadata.get("citations") and len(metadata["citations"]) > 0:
                    with st.expander("📚 Sources", expanded=False):
                        for citation in metadata["citations"]:
                            st.markdown(f"• {citation}")

    # Accept and process user input
    if prompt := st.chat_input("Ask me anything about Atlan..."):
        # Add user message to chat history and display it
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Process the query with the AI assistant
        with st.chat_message("assistant"):
            message_placeholder = st.empty()

            # Show processing indicator
            with st.spinner("🤔 Analyzing your question..."):
                try:
                    # Get the event loop for async operations
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                # Process the query asynchronously
                result = loop.run_until_complete(process_query_async(prompt))

                if result["success"]:
                    # Extract the final response
                    final_response = result["data"].get("response", "I apologize, but I couldn't generate a response at this time.")

                    # Show the response with typing effect
                    full_response = ""
                    for chunk in final_response.split():
                        full_response += chunk + " "
                        time.sleep(0.02)  # Faster typing for better UX
                        message_placeholder.markdown(full_response + "▌")

                    message_placeholder.markdown(full_response)

                    # Prepare metadata for the message
                    metadata = {}

                    # Add classification info if available
                    if "classification" in result["data"]:
                        metadata["classification"] = result["data"]["classification"]

                    # Add citations if available
                    if "citations" in result["data"] and result["data"]["citations"]:
                        metadata["citations"] = result["data"]["citations"]

                    # Add the assistant response to chat history with metadata
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": full_response,
                        "metadata": metadata
                    })

                else:
                    # Handle error case
                    error_message = result["error"]
                    message_placeholder.error(f"❌ {error_message}")

                    # Add error message to chat history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"❌ {error_message}"
                    })

async def process_query_async(query: str) -> Dict[str, Any]:
    """
    Process a user query using the AI orchestrator.

    Args:
        query: The user's input query

    Returns:
        Dict containing success status and either data or error message
    """
    try:
        # Get the orchestrator from session state
        orchestrator = st.session_state.orchestrator

        # Invoke the full AI pipeline
        result = await orchestrator.invoke(query)

        # Extract additional metadata for display
        enhanced_result = result.copy()

        # If we have classification data, extract citations from context
        if "context" in result and result["context"]:
            citations = extract_citations_from_context(result["context"])
            enhanced_result["citations"] = citations

        return {
            "success": True,
            "data": enhanced_result
        }

    except Exception as e:
        error_msg = f"I encountered an error while processing your request: {str(e)}"
        print(f"Error in process_query_async: {e}")
        return {
            "success": False,
            "error": error_msg
        }

def extract_citations_from_context(context: str) -> list:
    """
    Extract citation URLs from the context string.

    Args:
        context: The context string returned by RAG

    Returns:
        List of citation strings
    """
    citations = []
    if not context:
        return citations

    # Look for URL patterns in the context
    import re

    # Pattern to match URLs in the context
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'

    # Find all URLs in the context
    urls = re.findall(url_pattern, context)

    # Also look for markdown-style links [text](url)
    markdown_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    markdown_links = re.findall(markdown_pattern, context)

    # Add direct URLs
    for url in urls:
        if url not in [link[1] for link in markdown_links]:  # Avoid duplicates
            citations.append(url)

    # Add markdown links
    for text, url in markdown_links:
        citations.append(f"[{text}]({url})")

    # Remove duplicates while preserving order
    seen = set()
    unique_citations = []
    for citation in citations:
        if citation not in seen:
            unique_citations.append(citation)
            seen.add(citation)

    return unique_citations
