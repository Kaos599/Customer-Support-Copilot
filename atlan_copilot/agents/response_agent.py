import os
import sys
from typing import Dict, Any
import google.generativeai as genai

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agents.base_agent import BaseAgent

class ResponseAgent(BaseAgent):
    """
    The agent responsible for generating a final, human-readable response.
    It uses the context retrieved by the RAG agent to answer the user's query.
    """
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        """
        Initializes the ResponseAgent.
        Uses a more powerful model for generation, as specified in the project brief.
        """
        super().__init__()
        self._configure_api()
        self.model = self._initialize_model(model_name)

    def _configure_api(self):
        """Configures the Gemini API key from environment variables."""
        try:
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not found in environment variables.")
            genai.configure(api_key=api_key)
            print("Gemini API configured successfully for ResponseAgent.")
        except Exception as e:
            print(f"Warning: Could not configure Gemini API for ResponseAgent: {e}")

    def _initialize_model(self, model_name: str):
        """Initializes the GenerativeModel, returns None on failure."""
        try:
            model = genai.GenerativeModel(model_name)
            print(f"Gemini model '{model_name}' initialized successfully for ResponseAgent.")
            return model
        except Exception as e:
            print(f"Error initializing Gemini model '{model_name}' for ResponseAgent: {e}")
            return None

    def _construct_prompt(self, query: str, context: str) -> str:
        """Constructs the prompt for the response generation model."""
        return f"""
        You are a helpful and friendly customer support assistant for Atlan.
        Your primary goal is to provide accurate and concise answers based ONLY on the provided context.

        **Instructions:**
        1.  Carefully analyze the user's query and the context provided below. The context is retrieved from Atlan's official documentation and knowledge base.
        2.  Synthesize a helpful answer that directly addresses the user's query.
        3.  **Crucially, you must base your answer strictly on the information given in the context.** Do not add any information that is not present in the context.
        4.  If the context contains source URLs, you should cite them in your response using markdown links, like `[Source](https://...url...)`. This is very important for user trust.
        5.  If the provided context does not contain enough information to answer the query, you MUST explicitly state that you could not find a specific answer in the documentation. Do not try to guess. You can suggest rephrasing the question or trying a broader query.
        6.  Keep the tone professional, helpful, and clear.

        **User Query:** "{query}"

        **Context from Documentation:**
        ---
        {context}
        ---

        **Your Answer:**
        """

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a final response based on the query and retrieved context.
        """
        print("--- Executing Response Agent ---")
        if not self.model:
            return {**state, "response": "Error: The response generation model is not available."}

        query = state.get("query")
        context = state.get("context")

        if not query or not context:
            return {**state, "response": "Error: Missing query or context for response generation."}

        prompt = self._construct_prompt(query, context)

        try:
            response = await self.model.generate_content_async(prompt)
            final_response = response.text
        except Exception as e:
            print(f"Error during response generation API call: {e}")
            final_response = "Sorry, I encountered an error while trying to generate a response. Please try again."

        print(f"Generated response: {final_response[:300]}...")

        return {**state, "response": final_response}
