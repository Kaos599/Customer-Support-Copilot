from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAgent(ABC):
    """
    Abstract base class for all agents in the Atlan Copilot system.

    This class defines the common interface that all agents must implement.
    Agents are responsible for processing a part of the state and returning
    an updated state.
    """

    @abstractmethod
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the core logic of the agent.

        This method should be implemented by all concrete agent classes. It takes the
        current state of the workflow, performs its specific task, and returns a
        dictionary containing the updated state.

        Args:
            state: The current state of the workflow graph, represented as a dictionary.

        Returns:
            A dictionary containing the updated state after the agent's execution.
        """
        pass
