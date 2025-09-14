from typing import TypedDict, Optional, Dict, Any
from langgraph.graph import StateGraph, END
import os
import sys
import asyncio

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agents.classification_agent import ClassificationAgent
from agents.resolution_agent import ResolutionAgent


# Define the state for ticket processing
class TicketState(TypedDict):
    """
    Represents the state of a ticket processing workflow.
    """
    ticket: Dict[str, Any]
    classification: Optional[Dict[str, Any]]
    resolution: Optional[Dict[str, Any]]
    resolution_status: str


class TicketOrchestrator:
    """
    Orchestrator for processing customer support tickets.
    Handles classification and resolution of tickets.
    """

    def __init__(self):
        self.classification_agent = ClassificationAgent()
        self.resolution_agent = ResolutionAgent()
        self.graph = self._build_graph()

    async def _run_classification(self, state: TicketState) -> Dict[str, Any]:
        """
        Wrapper for the ClassificationAgent node for ticket processing.
        """
        print("TicketOrchestrator: Running Classification...")
        ticket = state["ticket"]

        # Prepare classification input from ticket
        classification_input_state = {
            "subject": ticket.get("subject", ""),
            "body": ticket.get("body", "")
        }

        result_state = await self.classification_agent.execute(classification_input_state)

        # Update ticket with classification results
        updated_ticket = ticket.copy()
        updated_ticket["classification"] = result_state.get("classification", {})
        updated_ticket["processed"] = True

        return {"classification": result_state.get("classification"), "ticket": updated_ticket}

    async def _run_resolution(self, state: TicketState) -> Dict[str, Any]:
        """
        Wrapper for the ResolutionAgent node.
        """
        print("TicketOrchestrator: Running Resolution...")
        result_state = await self.resolution_agent.execute(state)
        return result_state

    def _build_graph(self):
        """
        Builds the LangGraph state machine for ticket processing.
        """
        workflow = StateGraph(TicketState)

        # Add the agent nodes to the graph
        workflow.add_node("classify_ticket", self._run_classification)
        workflow.add_node("resolve_ticket", self._run_resolution)

        # Define the edges that determine the flow
        workflow.set_entry_point("classify_ticket")
        workflow.add_edge("classify_ticket", "resolve_ticket")
        workflow.add_edge("resolve_ticket", END)

        # Compile the graph into a runnable object
        print("Compiling the Ticket Processing Graph...")
        return workflow.compile()

    async def process_ticket(self, ticket: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single ticket through the classification and resolution pipeline.

        Args:
            ticket: Ticket data dictionary

        Returns:
            Final state after processing
        """
        if not self.graph:
            raise RuntimeError("Graph is not compiled.")

        initial_state = {
            "ticket": ticket,
            "resolution_status": "pending"
        }

        try:
            # Use ainvoke for asynchronous execution
            final_state = await self.graph.ainvoke(initial_state)
            print(f"Ticket processing completed for ticket {ticket.get('id', 'unknown')}")
            return final_state
        except Exception as e:
            # Handle event loop conflicts by creating a new event loop
            if "attached to a different loop" in str(e):
                print("Event loop conflict detected, using fallback execution...")
                return await self._process_with_new_loop(initial_state)
            else:
                raise e

    async def _process_with_new_loop(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fallback processing method that creates a new event loop to avoid conflicts.

        Args:
            initial_state: Initial state for the graph

        Returns:
            Final state after processing
        """
        # Create a new event loop for this execution
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Execute the graph in the new loop
            final_state = await self.graph.ainvoke(initial_state)
            return final_state
        finally:
            # Clean up the loop
            loop.close()
            # Restore the original loop if it exists
            try:
                asyncio.set_event_loop(asyncio.get_event_loop())
            except RuntimeError:
                pass  # No original loop to restore

    async def resolve_ticket(self, ticket: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve an already processed ticket.

        Args:
            ticket: Processed ticket data dictionary

        Returns:
            Resolution result
        """
        if not ticket.get("processed", False):
            raise ValueError("Ticket must be processed before resolution")

        state = {
            "ticket": ticket,
            "classification": ticket.get("classification", {}),
            "resolution_status": "pending"
        }

        return await self.resolution_agent.execute(state)
