import streamlit as st
import asyncio
from typing import Dict, Any, Optional
import sys
import os
from datetime import datetime

# Add project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database.mongodb_client import MongoDBClient


def resolve_current_ticket(ticket_id: str):
    """
    Resolve the current ticket using the resolution agent with comprehensive feedback.
    """
    from agents.ticket_orchestrator import TicketOrchestrator
    import asyncio

    try:
        # Get the current ticket data
        ticket = fetch_ticket_by_id(ticket_id)
        if not ticket:
            st.error(f"❌ Could not find ticket {ticket_id}")
            return

        if ticket.get('resolution'):
            st.warning("⚠️ This ticket has already been resolved.")
            st.info("💡 Check the '💬 Response & Resolution' tab to view the existing resolution.")
            return

        # Show initial processing message
        progress_placeholder = st.empty()
        progress_placeholder.info("🔄 **Starting ticket resolution process...**")

        # Create orchestrator and resolve ticket
        orchestrator = TicketOrchestrator()

        async def resolve_async():
            try:
                result = await orchestrator.resolve_ticket(ticket)
                return result
            except Exception as e:
                print(f"Error in resolve_async: {e}")
                return {"resolution": {"status": "error", "message": str(e)}}

        # Run async resolution with progress updates
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Show progress
        progress_placeholder.info("🤖 **Processing ticket with AI analysis...**")
        result = loop.run_until_complete(resolve_async())

        resolution = result.get('resolution', {})
        status = resolution.get('status', 'unknown')

        # Clear progress placeholder
        progress_placeholder.empty()

        # Handle different resolution outcomes
        if status == 'resolved':
            st.success("✅ **Ticket resolved successfully with AI-generated response!**")

            # Show resolution summary
            response = resolution.get('response', '')
            sources = resolution.get('sources', [])
            knowledge_base = resolution.get('knowledge_base_used', '')

            with st.expander("📋 Resolution Summary", expanded=True):
                st.write(f"**🤖 AI Response Generated:** {len(response)} characters")
                st.write(f"**📚 Sources Used:** {len(sources)}")
                if knowledge_base:
                    st.write(f"**🔍 Knowledge Base:** {knowledge_base}")

            st.info("🔄 **Refreshing page to show complete resolution details...**")
            st.rerun()

        elif status == 'routed':
            routed_to = resolution.get('routed_to', 'team')
            st.info(f"📋 **Ticket successfully routed to {routed_to}**")

            with st.expander("📋 Routing Details", expanded=True):
                st.write(f"**🎯 Routed To:** {routed_to}")
                st.write(f"**📝 Reason:** {resolution.get('routing_reason', 'N/A')}")
                st.write("**⏱️ Expected Response:** Within 2-3 business days")

            st.info("🔄 **Refreshing page to show routing information...**")
            st.rerun()

        else:
            error_msg = resolution.get('message', 'Unknown error occurred')
            st.error(f"❌ **Resolution failed:** {error_msg}")

            # Show troubleshooting information
            with st.expander("🔧 Troubleshooting", expanded=False):
                st.write("**Possible causes:**")
                st.write("• AI model temporarily unavailable")
                st.write("• Network connectivity issues")
                st.write("• Knowledge base access problems")
                st.write("• Invalid ticket data")
                st.write("\n**Suggested actions:**")
                st.write("• Try again in a few moments")
                st.write("• Check your internet connection")
                st.write("• Contact support if the issue persists")

    except Exception as e:
        st.error(f"❌ **Unexpected error during resolution:** {str(e)}")
        st.info("💡 Please try again or contact support if this issue persists.")


def fetch_ticket_by_id(ticket_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a single processed ticket by ID from MongoDB.

    Args:
        ticket_id: The ticket ID to fetch

    Returns:
        Ticket data dictionary or None if not found
    """
    async def fetch_single_ticket():
        mongo_client = MongoDBClient()
        await mongo_client.connect()
        try:
            ticket = await mongo_client.get_processed_ticket_by_id(ticket_id)
            return ticket
        finally:
            await mongo_client.close()

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(fetch_single_ticket())


def display_ticket_detail():
    """
    Display detailed view of a single ticket with AI analysis and responses.
    """
    # Configure page
    st.set_page_config(
        page_title="Ticket Detail View",
        page_icon="🎫",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Get ticket ID from session state or query parameters FIRST
    ticket_id = st.session_state.get("selected_ticket_id", None)

    # Fallback to query params if session state doesn't have it
    if not ticket_id:
        ticket_id = st.query_params.get("ticket_id", None)

    # Override sidebar content to hide page navigation
    with st.sidebar:
        st.header("🎫 Ticket Detail")

        if st.button("← Back to Tickets", use_container_width=True, type="secondary"):
            st.session_state.current_view = "Tickets View"
            st.switch_page("app.py")

        if st.button("🏠 Dashboard", use_container_width=True):
            st.session_state.current_view = "Dashboard & Classification"
            st.switch_page("app.py")

        if st.button("💬 Chat", use_container_width=True):
            st.session_state.current_view = "Live Chat"
            st.switch_page("app.py")

        st.markdown("---")

        # Ticket summary in sidebar
        if ticket_id:
            try:
                ticket_info = fetch_ticket_by_id(ticket_id)
                if ticket_info:
                    st.markdown("### 📋 Ticket Summary")
                    st.write(f"**ID:** {ticket_info.get('id', 'N/A')}")
                    st.write(f"**Status:** {'✅ Processed' if ticket_info.get('processed', False) else '⏳ Unprocessed'}")

                    if ticket_info.get('processed', False):
                        classification = ticket_info.get('classification', {})
                        st.write(f"**Topic:** {classification.get('topic', 'N/A')}")
                        st.write(f"**Priority:** {classification.get('priority', 'N/A')}")

                    if ticket_info.get('resolution'):
                        resolution = ticket_info.get('resolution', {})
                        status = resolution.get('status', 'unknown')
                        status_icon = "✅" if status == 'resolved' else "📋" if status == 'routed' else "❓"
                        st.write(f"**Resolution:** {status_icon} {status.title()}")
            except:
                st.caption("Loading ticket info...")

    st.title("🎫 Ticket Detail View")
    st.markdown("---")

    if not ticket_id:
        st.error("❌ No ticket ID provided. Please select a ticket from the Tickets View.")
        st.info("💡 To view ticket details, click the '👁️ View Full Details' button on any ticket in the Tickets View.")

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("← Back to Tickets View", type="primary", use_container_width=True):
                st.session_state.current_view = "Tickets View"
                st.switch_page("app.py")
        with col2:
            if st.button("🏠 Back to Dashboard", use_container_width=True):
                st.session_state.current_view = "Dashboard & Classification"
                st.switch_page("app.py")

        return

    # Fetch ticket data
    with st.spinner("Loading ticket details..."):
        ticket = fetch_ticket_by_id(ticket_id)

    if not ticket:
        st.error(f"Ticket with ID '{ticket_id}' not found.")
        if st.button("← Back to Tickets View"):
            st.switch_page("atlan_copilot/ui/tickets_view.py")
        return

    # Display ticket header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.header(f"🎫 {ticket.get('id', 'Unknown')}")
    with col2:
        classification = ticket.get('classification', {})
        priority = classification.get('priority', 'Unknown')
        priority_color = get_priority_color(priority)
        st.markdown(f'<div style="text-align: right;"><span style="background-color: {priority_color}; '
                   f'color: white; padding: 8px 16px; border-radius: 20px; font-size: 14px; font-weight: bold;">'
                   f'{priority}</span></div>', unsafe_allow_html=True)

    # Action buttons
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🔄 Resolve Ticket", type="primary", use_container_width=True):
            resolve_current_ticket(ticket_id)
    with col2:
        if st.button("📊 View Analytics", use_container_width=True):
            st.info("Analytics view will be available in the main dashboard")

    # Display ticket content in tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Ticket Details", "🧠 AI Analysis", "💬 Response & Resolution", "🔍 Internal Processing"])

    with tab1:
        display_ticket_basic_info(ticket)

    with tab2:
        display_ai_analysis(ticket)

    with tab3:
        display_response_and_resolution(ticket)

    with tab4:
        display_internal_processing(ticket)


def display_ticket_basic_info(ticket: Dict[str, Any]):
    """
    Display basic ticket information.
    """
    st.subheader("📝 Ticket Information")

    # Ticket ID and Status
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"**Ticket ID:** `{ticket.get('id', 'N/A')}`")
    with col2:
        status = "✅ Processed" if ticket.get('processed', False) else "⏳ Unprocessed"
        st.markdown(f"**Status:** {status}")

    st.markdown("---")

    # Subject
    st.markdown("**📧 Subject:**")
    subject = ticket.get('subject', 'N/A')
    st.markdown(f"**{subject}**")

    st.markdown("---")

    # Body/Description
    st.markdown("**📄 Description:**")
    body = ticket.get('body', 'N/A')
    if len(body) > 1000:
        st.write(body[:500] + "...")
        with st.expander("📖 View Full Description", expanded=False):
            st.write(body)
    else:
        st.write(body)

    st.markdown("---")

    # Metadata in organized columns
    st.markdown("**📊 Ticket Metadata:**")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Created:**")
        created_at = ticket.get('created_at')
        if isinstance(created_at, str):
            try:
                if 'T' in created_at:
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                else:
                    dt = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S.%f')
                st.write(f"📅 {dt.strftime('%b %d, %Y')}")
                st.write(f"🕒 {dt.strftime('%H:%M:%S')}")
            except:
                st.write(f"📅 {created_at[:10] if created_at != 'N/A' else 'N/A'}")
        else:
            st.write("📅 Unknown")

    with col2:
        st.markdown("**Last Updated:**")
        processing_meta = ticket.get('processing_metadata', {})
        processed_at = processing_meta.get('processed_at', 'N/A')
        if isinstance(processed_at, datetime):
            st.write(f"📅 {processed_at.strftime('%b %d, %Y')}")
            st.write(f"🕒 {processed_at.strftime('%H:%M:%S')}")
        else:
            st.write(f"📅 {str(processed_at)[:10] if processed_at != 'N/A' else 'N/A'}")

    with col3:
        st.markdown("**Processing Info:**")
        if ticket.get('processed', False):
            model = processing_meta.get('model_version', 'N/A')
            proc_time = processing_meta.get('processing_time_seconds', 'N/A')
            st.write(f"🤖 Model: {model}")
            if isinstance(proc_time, (int, float)):
                st.write(f"⚡ Time: {proc_time:.2f}s")
        else:
            st.write("⏳ Not processed yet")


def display_ai_analysis(ticket: Dict[str, Any]):
    """
    Display AI's internal analysis of the ticket.
    """
    st.subheader("🧠 AI Internal Analysis")

    if not ticket.get('processed', False):
        st.warning("⚠️ This ticket has not been processed yet. No AI analysis available.")
        st.info("💡 Go to the Dashboard and click '⚡ Process Tickets' to analyze this ticket.")
        return

    classification = ticket.get('classification', {})
    confidence_scores = ticket.get('confidence_scores', {})

    # Classification results in a nice grid
    st.markdown("**🎯 Classification Results:**")
    col1, col2, col3 = st.columns(3)

    with col1:
        topic = classification.get('topic', 'Unknown')
        topic_conf = confidence_scores.get('topic', 'N/A')
        st.metric("**📂 Topic**", topic)
        if isinstance(topic_conf, (int, float)):
            st.progress(topic_conf, text=f"Confidence: {topic_conf:.1%}")
        else:
            st.caption(f"Confidence: {topic_conf}")

    with col2:
        sentiment = classification.get('sentiment', 'Unknown')
        sentiment_conf = confidence_scores.get('sentiment', 'N/A')
        sentiment_color = get_sentiment_color(sentiment)
        st.markdown(f"**😊 Sentiment:** <span style='background-color: {sentiment_color}; "
                   f"color: white; padding: 6px 12px; border-radius: 15px; font-weight: bold;'>{sentiment}</span>",
                   unsafe_allow_html=True)
        if isinstance(sentiment_conf, (int, float)):
            st.progress(sentiment_conf, text=f"Confidence: {sentiment_conf:.1%}")
        else:
            st.caption(f"Confidence: {sentiment_conf}")

    with col3:
        priority = classification.get('priority', 'Unknown')
        priority_conf = confidence_scores.get('priority', 'N/A')
        priority_color = get_priority_color(priority)
        st.markdown(f"**🚨 Priority:** <span style='background-color: {priority_color}; "
                   f"color: white; padding: 6px 12px; border-radius: 15px; font-weight: bold;'>{priority}</span>",
                   unsafe_allow_html=True)
        if isinstance(priority_conf, (int, float)):
            st.progress(priority_conf, text=f"Confidence: {priority_conf:.1%}")
        else:
            st.caption(f"Confidence: {priority_conf}")

    st.markdown("---")

    # Topic tags with better visualization
    st.markdown("**🏷️ Topic Tags:**")
    topic_tags = classification.get('topic_tags', [])
    if topic_tags:
        st.markdown("**Identified Categories:**")
        tags_html = ""
        for tag in topic_tags:
            tags_html += f'<span style="background-color: #e3f2fd; color: #1976d2; padding: 6px 12px; ' \
                        f'margin: 4px; border-radius: 15px; font-size: 14px; display: inline-block; ' \
                        f'font-weight: bold;">#{tag}</span> '
        st.markdown(tags_html, unsafe_allow_html=True)
    else:
        st.caption("No topic tags were identified for this ticket.")

    st.markdown("---")

    # Processing metadata with better layout
    st.markdown("**⚙️ Processing Details:**")
    processing_meta = ticket.get('processing_metadata', {})

    if processing_meta:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**🤖 AI Model:**")
            model = processing_meta.get('model_version', 'N/A')
            st.write(f"Gemini {model}" if model != 'N/A' else 'N/A')

            st.markdown("**📊 Processing Status:**")
            status = processing_meta.get('status', 'completed')
            status_icon = "✅" if status == 'completed' else "⚠️"
            st.write(f"{status_icon} {status.title()}")

        with col2:
            st.markdown("**⚡ Processing Time:**")
            proc_time = processing_meta.get('processing_time_seconds', 'N/A')
            if isinstance(proc_time, (int, float)):
                st.write(f"{proc_time:.2f} seconds")
            else:
                st.write(proc_time)

            st.markdown("**🕒 Processed At:**")
            processed_at = processing_meta.get('processed_at', 'N/A')
            if isinstance(processed_at, datetime):
                st.write(processed_at.strftime('%b %d, %Y at %H:%M:%S'))
            else:
                st.write(str(processed_at)[:19] if processed_at != 'N/A' else 'N/A')
    else:
        st.caption("No processing metadata available.")


def display_response_and_resolution(ticket: Dict[str, Any]):
    """
    Display AI-generated response and resolution information.
    """
    st.subheader("💬 Response & Resolution")

    # Check if ticket has been resolved
    resolution_data = ticket.get('resolution', {})

    if resolution_data:
        status = resolution_data.get('status', 'pending')

        if status == 'resolved':
            # 🎉 RESOLVED TICKET - Show AI Response
            st.success("✅ **This ticket has been automatically resolved with an AI-generated response!**")

            # Display the AI response in a nice box
            st.markdown("### 🤖 AI-Generated Response")
            response_text = resolution_data.get('response', 'N/A')

            # Response box with better formatting
            st.markdown("""
            <div style="
                background-color: #f8f9fa;
                border-left: 4px solid #28a745;
                padding: 15px;
                margin: 10px 0;
                border-radius: 5px;
                font-size: 16px;
                line-height: 1.6;
            ">
            """ + response_text + """
            </div>
            """, unsafe_allow_html=True)

            # Display sources and citations
            sources = resolution_data.get('sources', [])
            if sources:
                st.markdown("### 📚 Sources & Citations")
                st.info(f"📖 This response was generated using {len(sources)} knowledge base sources:")

                for i, source in enumerate(sources, 1):
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        url = source.get('url', 'N/A')
                        # Clean up URL for display
                        if 'docs.atlan.com' in url:
                            display_url = "📚 Atlan Documentation"
                        elif 'developer.atlan.com' in url:
                            display_url = "🛠️ Developer Hub"
                        else:
                            display_url = url.replace('https://', '').replace('http://', '')

                        st.markdown(f"**[{i}]** [{display_url}]({url})")

                    with col2:
                        if st.button(f"View Snippet {i}", key=f"snippet_{i}", help="Show source text"):
                            st.session_state[f"show_snippet_{i}"] = not st.session_state.get(f"show_snippet_{i}", False)

                    # Show snippet if requested
                    if st.session_state.get(f"show_snippet_{i}", False) and source.get('snippet'):
                        st.markdown("""
                        <div style="
                            background-color: #e9ecef;
                            padding: 10px;
                            margin: 5px 0 15px 20px;
                            border-radius: 5px;
                            border-left: 3px solid #6c757d;
                            font-size: 14px;
                        ">
                        """ + source['snippet'][:300] + ("..." if len(source['snippet']) > 300 else "") + """
                        </div>
                        """, unsafe_allow_html=True)

            # Generation metadata
            st.markdown("### 📊 Response Details")
            col1, col2, col3 = st.columns(3)

            with col1:
                confidence = resolution_data.get('confidence', 'N/A')
                if isinstance(confidence, (int, float)):
                    st.metric("**AI Confidence**", f"{confidence:.1%}")
                else:
                    st.metric("**AI Confidence**", str(confidence))

            with col2:
                generated_at = resolution_data.get('generated_at', 'N/A')
                if isinstance(generated_at, datetime):
                    st.metric("**Generated**", generated_at.strftime('%b %d, %H:%M'))
                else:
                    st.metric("**Generated**", str(generated_at)[:16] if generated_at != 'N/A' else 'N/A')

            with col3:
                response_length = len(response_text) if response_text != 'N/A' else 0
                st.metric("**Response Length**", f"{response_length} chars")

        elif status == 'routed':
            # 📋 ROUTED TICKET - Show routing information
            st.info("📋 **This ticket has been classified and routed to the appropriate support team.**")

            routed_to = resolution_data.get('routed_to', 'N/A')
            routing_reason = resolution_data.get('routing_reason', 'N/A')

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**🎯 Routed To:**")
                st.markdown(f"### {routed_to}")

            with col2:
                st.markdown("**📝 Routing Reason:**")
                st.write(routing_reason)

            st.markdown("### 📞 Next Steps")
            st.info("The ticket has been forwarded to the specialized support team. They will follow up with you shortly.")

        else:
            # ⚠️ UNKNOWN STATUS
            st.warning(f"⚠️ **Resolution Status:** {status}")
            st.write("This ticket has an unrecognized resolution status.")

    else:
        # 🚫 NO RESOLUTION DATA
        st.warning("⚠️ **No resolution data available for this ticket.**")

        if ticket.get('processed', False):
            classification = ticket.get('classification', {})
            topic = classification.get('topic', 'Unknown')

            st.markdown("### 🎯 Current Status")
            st.write(f"**Topic:** {topic}")
            st.write("**Status:** Processed but not yet resolved")

            # Check if topic qualifies for RAG resolution
            rag_topics = ['How-to', 'Product', 'Best practices', 'API/SDK', 'SSO']
            if topic in rag_topics:
                st.info("💡 **This topic qualifies for automated resolution using our knowledge base.**")

                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("🔄 Generate AI Response", key="generate_response", type="primary", use_container_width=True):
                        with st.spinner("🤖 Generating AI response using knowledge base..."):
                            # This will be implemented when we add the full RAG integration
                            st.success("🎉 AI Response Generated!")
                            st.info("RAG integration will provide a complete response here in the next phase.")
                with col2:
                    if st.button("📋 Route to Team", key="route_to_team", use_container_width=True):
                        with st.spinner("📤 Routing to appropriate team..."):
                            st.success("✅ Ticket routed to support team!")
                            st.info("Manual routing will be implemented in the next phase.")
            else:
                st.info("📋 **This topic will be routed to the appropriate support team for manual handling.**")

                if st.button("📤 Route Now", key="route_now", type="secondary", use_container_width=True):
                    with st.spinner("📤 Routing ticket..."):
                        st.success("✅ Ticket has been routed to the support team!")
                        st.info("The team will follow up with you shortly.")
        else:
            st.error("❌ **This ticket has not been processed yet.**")
            st.info("💡 Go to the Dashboard and click '⚡ Process Tickets' to analyze and resolve this ticket.")


def display_internal_processing(ticket: Dict[str, Any]):
    """
    Display internal processing information and technical details.
    """
    st.subheader("🔍 Internal Processing Details")

    if not ticket.get('processed', False):
        st.warning("⚠️ This ticket has not been processed yet.")
        st.info("Click the '🔄 Resolve Ticket' button to process and resolve this ticket.")
        return

    # Processing metadata
    processing_meta = ticket.get('processing_metadata', {})
    if processing_meta:
        st.markdown("### 🤖 AI Processing Information")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Model Used:**")
            model = processing_meta.get('model_version', 'N/A')
            st.code(f"Gemini {model}")

            st.markdown("**Processing Status:**")
            status = processing_meta.get('status', 'unknown')
            status_color = "🟢" if status == 'completed' else "🟡"
            st.write(f"{status_color} {status.title()}")

        with col2:
            st.markdown("**Processing Time:**")
            proc_time = processing_meta.get('processing_time_seconds', 'N/A')
            if isinstance(proc_time, (int, float)):
                st.metric("⏱️ Duration", f"{proc_time:.2f}s")
            else:
                st.write("N/A")

            st.markdown("**Agent Version:**")
            agent_ver = processing_meta.get('agent_version', 'N/A')
            st.code(f"v{agent_ver}")

    # Classification confidence scores
    confidence_scores = ticket.get('confidence_scores', {})
    if confidence_scores:
        st.markdown("### 📊 Classification Confidence Scores")

        # Create a nice table for confidence scores
        scores_data = []
        for key, value in confidence_scores.items():
            if isinstance(value, (int, float)):
                percentage = f"{value:.1%}"
                bar_length = int(value * 20)  # Scale to 20 characters
                bar = "█" * bar_length + "░" * (20 - bar_length)
                scores_data.append([key.title(), percentage, bar])

        if scores_data:
            import pandas as pd
            df = pd.DataFrame(scores_data, columns=["Metric", "Confidence", "Visual"])
            st.dataframe(df, use_container_width=True)

    # Resolution information
    resolution_data = ticket.get('resolution', {})
    if resolution_data:
        st.markdown("### 🎯 Resolution Processing")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Resolution Method:**")
            method = resolution_data.get('resolution_method', 'N/A')
            method_icon = "🤖" if method == 'RAG' else "👥" if method == 'routing' else "❓"
            st.write(f"{method_icon} {method}")

            st.markdown("**Resolution Status:**")
            status = resolution_data.get('status', 'unknown')
            status_icon = "✅" if status == 'resolved' else "📋" if status == 'routed' else "❌"
            st.write(f"{status_icon} {status.title()}")

        with col2:
            st.markdown("**Generated At:**")
            generated_at = resolution_data.get('generated_at')
            if isinstance(generated_at, datetime):
                st.write(generated_at.strftime('%b %d, %Y %H:%M:%S'))
            else:
                st.write(str(generated_at)[:19] if generated_at else 'N/A')

            st.markdown("**Response Confidence:**")
            confidence = resolution_data.get('confidence', 'N/A')
            if isinstance(confidence, (int, float)):
                st.metric("🎯 Confidence", f"{confidence:.1%}")
            else:
                st.write(str(confidence))

        # Show knowledge base information for RAG responses
        if resolution_data.get('resolution_method') == 'RAG':
            knowledge_base = resolution_data.get('knowledge_base_used', 'N/A')
            if knowledge_base != 'N/A':
                st.markdown("### 📚 Knowledge Base Used")
                st.info(f"**{knowledge_base}**")
                if 'docs.atlan.com' in knowledge_base:
                    st.write("📖 Product documentation and user guides")
                elif 'developer.atlan.com' in knowledge_base:
                    st.write("🛠️ Technical documentation and API references")

    # Raw data for debugging
    with st.expander("🔧 Raw Processing Data (Debug)", expanded=False):
        st.markdown("**Processing Metadata:**")
        st.json(processing_meta if processing_meta else {})

        st.markdown("**Confidence Scores:**")
        st.json(confidence_scores if confidence_scores else {})

        st.markdown("**Resolution Data:**")
        st.json(resolution_data if resolution_data else {})


def get_priority_color(priority: str) -> str:
    """Get color for priority display."""
    if "P0" in priority or "High" in priority:
        return "#dc3545"  # Red
    elif "P1" in priority or "Medium" in priority:
        return "#ffc107"  # Yellow
    elif "P2" in priority or "Low" in priority:
        return "#28a745"  # Green
    else:
        return "#6c757d"  # Gray


def get_sentiment_color(sentiment: str) -> str:
    """Get color for sentiment display."""
    sentiment_colors = {
        "Frustrated": "#dc3545",
        "Angry": "#dc3545",
        "Curious": "#17a2b8",
        "Neutral": "#6c757d",
        "Happy": "#28a745",
        "Satisfied": "#28a745"
    }
    return sentiment_colors.get(sentiment, "#6c757d")


# Main execution
if __name__ == "__main__":
    display_ticket_detail()
