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
from agents.rag_agent import RAGAgent
from agents.response_agent import ResponseAgent

# 1. Define the state for the graph
class CopilotState(TypedDict):
    """
    Represents the state of our LangGraph.
    It is passed between nodes and updated at each step.
    """
    query: str
    classification: Optional[Dict[str, Any]]
    context: Optional[str]
    response: Optional[str]

class Orchestrator:
    """
    The main orchestrator for the Atlan Copilot.
    It builds and manages the LangGraph state machine that connects all the agents.
    """
    def __init__(self):
        self.classification_agent = ClassificationAgent()
        self.rag_agent = RAGAgent()
        self.response_agent = ResponseAgent()
        self.graph = self._build_graph()

    async def _run_classification(self, state: CopilotState) -> Dict[str, Any]:
        """
        Wrapper for the ClassificationAgent node.
        It adapts the input state for the classification agent.
        """
        print("Orchestrator: Running Classification...")
        # The classification agent expects 'subject' and 'body'.
        # We can use the user's query for both as a simple adaptation.
        classification_input_state = {
            "subject": state["query"],
            "body": state["query"]
        }
        result_state = await self.classification_agent.execute(classification_input_state)
        return {"classification": result_state.get("classification")}

    async def _run_rag(self, state: CopilotState) -> Dict[str, Any]:
        """Wrapper for the RAGAgent node."""
        result_state = await self.rag_agent.execute(state)
        return {"context": result_state.get("context")}

    async def _run_response(self, state: CopilotState) -> Dict[str, Any]:
        """Wrapper for the ResponseAgent node."""
        print("Orchestrator: Running Response Generation...")
        result_state = await self.response_agent.execute(state)
        return {"response": result_state.get("response")}

    async def _delay_before_response(self, state: CopilotState) -> Dict[str, Any]:
        """A simple delay node to handle API rate limiting between agent calls."""
        # For chat interface, use minimal delay. For batch operations, use full delay.
        delay_seconds = 1  # Reduced from 60 seconds for better UX in chat
        print(f"Orchestrator: Delaying for {delay_seconds} seconds to respect API rate limits...")
        await asyncio.sleep(delay_seconds)
        print("Orchestrator: Delay complete.")
        return {} # This node does not modify the state

    def _build_graph(self):
        """
        Builds the LangGraph state machine.
        """
        workflow = StateGraph(CopilotState)

        # Add the agent nodes to the graph
        workflow.add_node("classify", self._run_classification)
        workflow.add_node("retrieve_context", self._run_rag)
        workflow.add_node("delay_before_response", self._delay_before_response)
        workflow.add_node("generate_response", self._run_response)

        # Define the edges that determine the flow
        workflow.set_entry_point("classify")
        workflow.add_edge("classify", "retrieve_context")
        workflow.add_edge("retrieve_context", "delay_before_response")
        workflow.add_edge("delay_before_response", "generate_response")
        workflow.add_edge("generate_response", END)

        # Compile the graph into a runnable object
        print("Compiling the LangGraph orchestrator...")
        return workflow.compile()

    async def invoke(self, query: str) -> Dict[str, Any]:
        """
        Runs the full copilot pipeline for a given query.

        Args:
            query: The user's input query.

        Returns:
            The final state of the graph after execution.
        """
        if not self.graph:
            raise RuntimeError("Graph is not compiled.")

        initial_state = {"query": query}
        # Use ainvoke for asynchronous execution
        final_state = await self.graph.ainvoke(initial_state)
        return final_state
