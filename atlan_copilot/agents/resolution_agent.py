from typing import Dict, Any, List
from datetime import datetime
import sys
import os

# Add project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agents.base_agent import BaseAgent
from agents.rag_agent import RAGAgent
from agents.classification_agent import ClassificationAgent
from agents.response_agent import ResponseAgent
from database.mongodb_client import MongoDBClient


class ResolutionAgent(BaseAgent):
    """
    Agent responsible for resolving tickets based on their classification.

    This agent determines whether a ticket should be:
    1. Resolved using RAG for eligible topics (How-to, Product, Best practices, API/SDK, SSO)
    2. Routed to appropriate teams for other topics
    """

    def __init__(self):
        self.rag_agent = RAGAgent()
        self.classification_agent = ClassificationAgent()
        self.response_agent = ResponseAgent()
        self.rag_eligible_topics = [
            'How-to', 'Product', 'Best practices', 'API/SDK', 'SSO'
        ]

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute resolution logic for a ticket.
        This will process the ticket if not already processed, then resolve it.

        Args:
            state: Dictionary containing ticket data

        Returns:
            Updated state with resolution information
        """
        try:
            ticket = state.get('ticket', {})

            # Step 1: Process ticket if not already processed
            if not ticket.get('processed', False):
                print("Ticket not processed yet, processing first...")
                ticket = await self._process_ticket(ticket)
                if not ticket.get('processed', False):
                    state['resolution'] = {
                        'status': 'error',
                        'message': 'Failed to process ticket'
                    }
                    return state

            # Step 2: Extract classification data
            classification = ticket.get('classification', {})
            topic_tags = classification.get('topic_tags', [])
            topic = self._determine_primary_topic(topic_tags)

            # Step 3: Store internal analysis for display
            internal_analysis = {
                'topic': topic,
                'topic_tags': topic_tags,
                'sentiment': classification.get('sentiment', 'Unknown'),
                'priority': classification.get('priority', 'Unknown'),
                'confidence_scores': ticket.get('confidence_scores', {}),
                'processed_at': ticket.get('processing_metadata', {}).get('processed_at')
            }

            # Step 4: Determine resolution approach and generate response
            if self._is_rag_eligible(topic):
                resolution_data = await self._resolve_with_rag(ticket, internal_analysis)
            else:
                resolution_data = self._route_to_team(ticket, topic, internal_analysis)

            # Step 5: Store comprehensive resolution data
            await self._store_resolution(ticket.get('id'), resolution_data)

            # Step 6: Update state with complete information
            state['ticket'] = ticket  # Updated ticket with processing if needed
            state['resolution'] = resolution_data
            state['internal_analysis'] = internal_analysis
            state['resolution_status'] = 'completed'

            return state

        except Exception as e:
            print(f"Error in ResolutionAgent: {e}")
            state['resolution'] = {
                'status': 'error',
                'message': str(e)
            }
            return state

    def _determine_primary_topic(self, topic_tags: List[str]) -> str:
        """
        Determine the primary topic from topic tags.

        Args:
            topic_tags: List of topic tags

        Returns:
            Primary topic string
        """
        if not topic_tags:
            return 'General'

        # Check for RAG-eligible topics first
        for tag in topic_tags:
            if tag in self.rag_eligible_topics:
                return tag

        # Return first tag as primary topic
        return topic_tags[0]

    async def _process_ticket(self, ticket: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a ticket that hasn't been processed yet.

        Args:
            ticket: Raw ticket data

        Returns:
            Processed ticket data
        """
        try:
            print(f"Processing ticket {ticket.get('id', 'unknown')}...")

            # Prepare classification input
            classification_input = {
                "subject": ticket.get("subject", ""),
                "body": ticket.get("body", "")
            }

            # Run classification
            classification_result = await self.classification_agent.execute(classification_input)

            # Update ticket with processing results
            processed_ticket = ticket.copy()
            processed_ticket.update({
                "processed": True,
                "classification": classification_result.get("classification", {}),
                "confidence_scores": classification_result.get("confidence_scores", {}),
                "processing_metadata": {
                    "processed_at": datetime.now(),
                    "model_version": "gemini-2.5-flash",
                    "processing_time_seconds": classification_result.get("processing_time", 0),
                    "agent_version": "2.0",
                    "status": "completed"
                },
                "updated_at": datetime.now()
            })

            # Store processed ticket in database
            mongo_client = MongoDBClient()
            await mongo_client.connect()

            # Remove _id field from update data to avoid MongoDB immutable field error
            update_data = processed_ticket.copy()
            update_data.pop('_id', None)  # Remove _id field if it exists

            # Update the ticket in database
            await mongo_client.collection.update_one(
                {"id": ticket.get("id")},
                {"$set": update_data}
            )

            await mongo_client.close()

            print(f"Successfully processed ticket {ticket.get('id', 'unknown')}")
            return processed_ticket

        except Exception as e:
            print(f"Error processing ticket: {e}")
            return ticket  # Return original ticket if processing fails

    def _is_rag_eligible(self, topic: str) -> bool:
        """
        Check if a topic is eligible for RAG resolution.

        Args:
            topic: Topic string

        Returns:
            True if eligible for RAG, False otherwise
        """
        return topic in self.rag_eligible_topics

    async def _resolve_with_rag(self, ticket: Dict[str, Any], internal_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve ticket using RAG agent with comprehensive response generation.

        Args:
            ticket: Ticket data dictionary
            internal_analysis: Internal analysis data for context

        Returns:
            Comprehensive resolution data dictionary
        """
        try:
            # Prepare enhanced query from ticket with context
            query = self._prepare_enhanced_query(ticket, internal_analysis)

            # Use RAG agent to get context and information
            rag_state = {
                'query': query,
                'ticket': ticket
            }

            rag_result = await self.rag_agent.execute(rag_state)

            # Generate comprehensive response based on RAG results
            response_data = await self._generate_rag_response(ticket, rag_result, internal_analysis)

            return {
                'status': 'resolved',
                'response': response_data['response'],
                'sources': response_data['sources'],
                'citations': response_data['citations'],
                'generated_at': datetime.now(),
                'confidence': response_data.get('confidence', 0.8),
                'resolution_method': 'RAG',
                'knowledge_base_used': response_data['knowledge_base_used'],
                'response_metadata': response_data['metadata']
            }

        except Exception as e:
            print(f"Error in RAG resolution: {e}")
            return {
                'status': 'error',
                'message': f'RAG resolution failed: {str(e)}',
                'generated_at': datetime.now()
            }

    def _route_to_team(self, ticket: Dict[str, Any], topic: str, internal_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route ticket to appropriate team based on topic with comprehensive information.

        Args:
            ticket: Ticket data dictionary
            topic: Primary topic
            internal_analysis: Internal analysis data

        Returns:
            Comprehensive routing data dictionary
        """
        # Define routing logic based on topics
        routing_map = {
            'Connector': 'Data Engineering Team',
            'Security': 'Security Team',
            'Performance': 'Infrastructure Team',
            'Integration': 'Integration Team',
            'Billing': 'Billing Team',
            'Account': 'Account Management',
            'General': 'General Support',
            'Feedback': 'Product Team'
        }

        # Default routing
        routed_to = routing_map.get(topic, 'General Support')
        routing_reason = f"Ticket classified as '{topic}' topic"

        # Generate routing response message
        response_message = f"""This ticket has been classified as a **'{topic}'** issue and routed to our **{routed_to}**.

**What happens next:**
- Our {routed_to} will review your ticket within 24 hours
- They will follow up with you directly if additional information is needed
- You can expect a response within 2-3 business days

**Internal Analysis Summary:**
- **Topic:** {topic}
- **Priority:** {internal_analysis.get('priority', 'Unknown')}
- **Sentiment:** {internal_analysis.get('sentiment', 'Unknown')}

If you have any urgent questions, please don't hesitate to follow up."""

        return {
            'status': 'routed',
            'response': response_message,
            'routed_to': routed_to,
            'routing_reason': routing_reason,
            'generated_at': datetime.now(),
            'resolution_method': 'routing',
            'internal_analysis': internal_analysis
        }

    def _prepare_enhanced_query(self, ticket: Dict[str, Any], internal_analysis: Dict[str, Any]) -> str:
        """
        Prepare an enhanced search query from ticket data with context.

        Args:
            ticket: Ticket data dictionary
            internal_analysis: Internal analysis data

        Returns:
            Enhanced query string with context
        """
        subject = ticket.get('subject', '')
        body = ticket.get('body', '')
        topic = internal_analysis.get('topic', '')

        # Build contextual query
        query_parts = []

        if subject:
            query_parts.append(f"Subject: {subject}")

        if body:
            query_parts.append(f"Question: {body}")

        if topic and topic in self.rag_eligible_topics:
            query_parts.append(f"Topic: {topic}")

        # Combine all parts
        query_text = " ".join(query_parts)

        # Limit query length
        if len(query_text) > 500:
            query_text = query_text[:500] + "..."

        return query_text.strip()

    async def _generate_rag_response(self, ticket: Dict[str, Any], rag_result: Dict[str, Any],
                                   internal_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a comprehensive RAG response using the ResponseAgent for proper formatting and citations.

        Args:
            ticket: Ticket data dictionary
            rag_result: RAG agent results
            internal_analysis: Internal analysis data

        Returns:
            Formatted response data
        """
        try:
            # Extract information from RAG results
            context = rag_result.get('context', '')
            citations = rag_result.get('citations', [])

            # Determine knowledge base used
            topic = internal_analysis.get('topic', '')
            if 'API' in topic or 'SDK' in topic:
                knowledge_base = "Developer Hub (https://developer.atlan.com/)"
            else:
                knowledge_base = "Atlan Documentation (https://docs.atlan.com/)"

            # Use ResponseAgent to generate proper response
            if context and len(context.strip()) > 50:
                # Prepare state for ResponseAgent
                response_state = {
                    'query': ticket.get('body', ticket.get('subject', 'General question')),
                    'context': context,
                    'citations': citations
                }

                # Generate response using ResponseAgent
                response_result = await self.response_agent.execute(response_state)
                response = response_result.get('response', '')
            else:
                # Fallback response when no good context is available
                response = self._generate_fallback_response(ticket, internal_analysis)

            # Create source citations for display
            sources = self._extract_sources_from_context(context)
            citations_formatted = self._format_citations(sources)

            return {
                'response': response,
                'sources': sources,
                'citations': citations_formatted,
                'knowledge_base_used': knowledge_base,
                'confidence': 0.85,  # Could be calculated based on context quality
                'metadata': {
                    'context_length': len(context),
                    'topic': internal_analysis.get('topic'),
                    'response_type': 'rag_generated'
                }
            }

        except Exception as e:
            print(f"Error generating RAG response: {e}")
            return {
                'response': "I apologize, but I was unable to generate a response based on the available information. Please try rephrasing your question or contact our support team.",
                'sources': [],
                'citations': "",
                'knowledge_base_used': "N/A",
                'confidence': 0.0,
                'metadata': {'error': str(e)}
            }

    def _format_rag_response(self, ticket: Dict[str, Any], context: str,
                           internal_analysis: Dict[str, Any]) -> str:
        """
        Format a comprehensive RAG response based on context and ticket information.
        """
        subject = ticket.get('subject', 'your question')
        topic = internal_analysis.get('topic', 'general')

        # Create a structured response
        response = f"""Based on your question about **"{subject}"**, here's the information from our documentation:

**Summary:**
{self._extract_summary_from_context(context)}

**Detailed Answer:**
{self._format_context_as_answer(context)}

**Additional Resources:**
For more detailed information, please refer to our documentation links provided below.

If this doesn't fully address your question, please provide additional details and I'll be happy to help further."""

        return response

    def _generate_fallback_response(self, ticket: Dict[str, Any],
                                  internal_analysis: Dict[str, Any]) -> str:
        """
        Generate a fallback response when RAG context is insufficient.
        """
        topic = internal_analysis.get('topic', 'general')

        fallback_responses = {
            'How-to': "While I don't have specific documentation for this exact scenario, here are some general best practices for Atlan usage:",
            'Product': "This appears to be a product-related question. Our documentation covers most product features comprehensively.",
            'Best practices': "For best practices in Atlan, I recommend reviewing our documentation which provides detailed guidance.",
            'API/SDK': "For API and SDK questions, our Developer Hub contains comprehensive technical documentation.",
            'SSO': "For Single Sign-On configuration questions, our documentation provides step-by-step setup guides."
        }

        base_response = fallback_responses.get(topic, "Thank you for your question about Atlan.")

        return f"""{base_response}

**What I can tell you:**
- Your question has been classified as: **{topic}**
- This topic is eligible for automated resolution using our knowledge base
- However, I need more specific context to provide a detailed answer

**Recommended next steps:**
1. Please provide additional details about your specific use case
2. Check our documentation links for related information
3. Contact our support team for personalized assistance

Would you like me to help you find more specific information or connect you with a support specialist?"""

    def _extract_summary_from_context(self, context: str) -> str:
        """
        Extract a concise summary from the context.
        """
        # Simple extraction - take first meaningful paragraph
        paragraphs = [p.strip() for p in context.split('\n\n') if p.strip()]

        for para in paragraphs[:2]:  # Check first 2 paragraphs
            if len(para) > 50 and len(para) < 200:
                return para

        # Fallback: take first 150 characters
        return context[:150] + "..." if len(context) > 150 else context

    def _format_context_as_answer(self, context: str) -> str:
        """
        Format raw context into a readable answer.
        """
        # Clean up the context and format it
        lines = context.split('\n')
        formatted_lines = []

        for line in lines:
            line = line.strip()
            if line and len(line) > 10:  # Skip very short lines
                # Add bullet points for lists
                if line.startswith('-') or line.startswith('•'):
                    formatted_lines.append(line)
                elif len(formatted_lines) > 0:
                    formatted_lines.append(line)
                else:
                    formatted_lines.append(line)

        return '\n'.join(formatted_lines[:5])  # Limit to first 5 meaningful lines

    def _extract_sources_from_context(self, context: str) -> List[Dict[str, Any]]:
        """
        Extract source URLs and create source citations from context.
        """
        sources = []

        # Look for URLs in the context
        import re
        url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'

        urls = re.findall(url_pattern, context)

        for i, url in enumerate(urls[:3]):  # Limit to 3 sources
            if 'docs.atlan.com' in url:
                source_name = "Atlan Documentation"
            elif 'developer.atlan.com' in url:
                source_name = "Developer Hub"
            else:
                source_name = "Reference"

            sources.append({
                'url': url if url.startswith('http') else f'https://{url}',
                'name': source_name,
                'snippet': self._extract_snippet_around_url(context, url)
            })

        # If no URLs found, add default sources based on topic
        if not sources:
            sources = [
                {
                    'url': 'https://docs.atlan.com/',
                    'name': 'Atlan Documentation',
                    'snippet': 'Comprehensive product documentation and guides'
                },
                {
                    'url': 'https://developer.atlan.com/',
                    'name': 'Developer Hub',
                    'snippet': 'Technical documentation and API references'
                }
            ]

        return sources

    def _extract_snippet_around_url(self, context: str, url: str) -> str:
        """
        Extract a text snippet around a URL in the context.
        """
        try:
            url_index = context.find(url)
            if url_index == -1:
                return "Reference documentation"

            # Extract 100 characters around the URL
            start = max(0, url_index - 50)
            end = min(len(context), url_index + len(url) + 50)

            snippet = context[start:end].strip()

            # Clean up the snippet
            if not snippet.startswith(' ') and start > 0:
                snippet = '...' + snippet
            if not snippet.endswith(' ') and end < len(context):
                snippet = snippet + '...'

            return snippet if len(snippet) > 20 else "Reference documentation"

        except:
            return "Reference documentation"

    def _format_citations(self, sources: List[Dict[str, Any]]) -> str:
        """
        Format sources into citation string.
        """
        if not sources:
            return ""

        citations = []
        for i, source in enumerate(sources, 1):
            citations.append(f"[{i}] {source['name']}")

        return " | ".join(citations)

    async def _store_resolution(self, ticket_id: str, resolution_data: Dict[str, Any]) -> bool:
        """
        Store resolution data in database.

        Args:
            ticket_id: Ticket ID
            resolution_data: Resolution data dictionary

        Returns:
            True if successful, False otherwise
        """
        try:
            mongo_client = MongoDBClient()
            await mongo_client.connect()
            success = await mongo_client.update_ticket_with_resolution(ticket_id, resolution_data)
            await mongo_client.close()
            return success
        except Exception as e:
            print(f"Error storing resolution data: {e}")
            return False

    async def resolve_tickets_batch(self, tickets: List[Dict[str, Any]],
                                   progress_callback=None) -> List[Dict[str, Any]]:
        """
        Resolve multiple tickets in parallel with controlled concurrency.

        Args:
            tickets: List of ticket dictionaries to resolve
            progress_callback: Optional callback function (current, total, message)

        Returns:
            List of resolution results
        """
        if not tickets:
            return []

        import asyncio
        from typing import Tuple

        semaphore = asyncio.Semaphore(5)  # Limit to 5 concurrent requests
        results = []

        async def resolve_single_ticket(ticket: Dict[str, Any], index: int) -> Tuple[int, Dict[str, Any]]:
            """Resolve a single ticket with semaphore control."""
            async with semaphore:
                try:
                    ticket_id = ticket.get('id', f'ticket_{index}')

                    if progress_callback:
                        progress_callback(index, len(tickets), f"Resolving {ticket_id}...")

                    # Prepare resolution state
                    resolution_state = {
                        'ticket': ticket,
                        'resolution_status': 'pending'
                    }

                    # Execute resolution
                    result = await self.execute(resolution_state)

                    # Add ticket metadata to result
                    result['ticket_id'] = ticket_id
                    result['original_ticket'] = ticket

                    return index, result

                except Exception as e:
                    print(f"Error resolving ticket {ticket.get('id', f'ticket_{index}')}: {e}")
                    return index, {
                        'ticket_id': ticket.get('id', f'ticket_{index}'),
                        'resolution': {
                            'status': 'error',
                            'message': str(e)
                        },
                        'original_ticket': ticket
                    }

        # Create tasks for parallel execution
        tasks = [resolve_single_ticket(ticket, i) for i, ticket in enumerate(tickets)]
        completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)

        # Sort results by original index and extract results
        sorted_results = sorted([task for task in completed_tasks if isinstance(task, tuple)],
                               key=lambda x: x[0])
        results = [result for _, result in sorted_results]

        return results