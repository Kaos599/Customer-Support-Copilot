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

    # Initialize session state for orchestrator with better error handling
    if "orchestrator" not in st.session_state or st.session_state.orchestrator is None:
        try:
            # Initialize orchestrator in a new event loop to avoid conflicts
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                # If we're in a running loop, create task for initialization
                if loop:
                    # For now, create a simple placeholder and initialize later
                    st.session_state.orchestrator = "initializing"
            except RuntimeError:
                # No running loop, safe to initialize
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                st.session_state.orchestrator = Orchestrator()

        except Exception as e:
            st.error(f"❌ AI assistant initialization failed: {str(e)}")
            st.info("Please refresh the page to try again.")
            return

    # Check if orchestrator is still initializing
    if st.session_state.orchestrator == "initializing":
        try:
            # Try to initialize now
            st.session_state.orchestrator = Orchestrator()
        except Exception as e:
            st.error(f"❌ AI assistant is not properly initialized. Please refresh the page.")
            return

    # Display prior chat messages from history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            # Show additional metadata for assistant messages only if they have metadata (responses to user queries)
            if message["role"] == "assistant" and "metadata" in message:
                metadata = message["metadata"]

                # Show query analysis section if classification data exists
                if metadata.get("classification"):
                    with st.expander("📋 Query Analysis", expanded=True):
                        classification = metadata["classification"]
                        st.write(f"**Topic Tags:** {', '.join(classification.get('topic_tags', []))}")
                        st.write(f"**Sentiment:** {classification.get('sentiment', 'N/A')}")
                        st.write(f"**Priority:** {classification.get('priority', 'N/A')}")

                # Show sources section if citations exist
                if metadata.get("citations") and len(metadata["citations"]) > 0:
                    with st.expander("📚 Sources", expanded=True):
                        citations = metadata["citations"]

                        for i, citation in enumerate(citations, 1):
                            # Format each citation with number and content
                            st.markdown(f"**[{i}]** {citation.get('title', 'Source')}")

                            # Show URL if available and not localhost
                            url = citation.get('url', '')
                            if url and not url.startswith(('http://localhost', 'http://127.0.0.1')):
                                st.markdown(f"🔗 [{url}]({url})")

                            # Show content snippet
                            content = citation.get('content_snippet', '').strip()
                            if content:
                                # Limit snippet length for better UX
                                if len(content) > 150:
                                    content = content[:150] + "..."
                                st.markdown(f"💬 {content}")

                            st.divider()

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
                import asyncio  # Ensure asyncio is available
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

                    # Process citations (already formatted by RAG agent)
                    if "citations" in result["data"] and result["data"]["citations"]:
                        # Citations are already properly formatted by the RAG agent
                        # Just assign them directly to metadata
                        metadata["citations"] = result["data"]["citations"]

                    # Add the assistant response to chat history with metadata
                    message_with_metadata = {
                        "role": "assistant",
                        "content": full_response,
                        "metadata": metadata
                    }
                    st.session_state.messages.append(message_with_metadata)

                    # Update the message placeholder with final response
                    message_placeholder.markdown(final_response)

                    # Display metadata immediately in the current chat message context
                    if metadata.get("classification"):
                        with st.expander("📋 Query Analysis", expanded=True):
                            classification = metadata["classification"]
                            st.write(f"**Topic Tags:** {', '.join(classification.get('topic_tags', []))}")
                            st.write(f"**Sentiment:** {classification.get('sentiment', 'N/A')}")
                            st.write(f"**Priority:** {classification.get('priority', 'N/A')}")

                    if metadata.get("citations") and len(metadata["citations"]) > 0:
                        with st.expander("📚 Sources", expanded=True):
                            citations = metadata["citations"]
                            for i, citation in enumerate(citations, 1):
                                st.markdown(f"**[{i}]** {citation.get('title', 'Source')}")
                                url = citation.get('url', '')
                                if url and not url.startswith(('http://localhost', 'http://127.0.0.1')):
                                    st.markdown(f"🔗 [{url}]({url})")
                                content = citation.get('content_snippet', '').strip()
                                if content:
                                    if len(content) > 150:
                                        content = content[:150] + "..."
                                    st.markdown(f"💬 {content}")
                                st.divider()

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

        # Citations are now provided by the RAG agent with detailed metadata
        # Citations are generated directly from retrieved search results

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

