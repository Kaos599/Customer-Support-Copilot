import os
import json
import google.generativeai as genai
from typing import Dict, Any, List

# Add the project root to the Python path to allow for absolute imports
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agents.base_agent import BaseAgent
from utils.validators import is_valid_classification_json

class ClassificationAgent(BaseAgent):
    """
    An agent responsible for classifying customer support tickets using the Gemini API.
    """

    def __init__(self, model_name: str = "gemini-2.5-flash"):
        """
        Initializes the ClassificationAgent.
        The API key is configured here, ensuring that dotenv has been loaded by the caller.
        """
        super().__init__()
        self._configure_api()
        self.tag_definitions = self._load_tag_definitions()
        self.model = self._initialize_model(model_name)

    def _configure_api(self):
        """Configures the Gemini API key from environment variables."""
        try:
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not found in environment variables.")
            genai.configure(api_key=api_key)
            print("Gemini API configured successfully.")
        except Exception as e:
            # This is not fatal, the model initialization will fail later.
            print(f"Warning: Could not configure Gemini API: {e}")

    def _initialize_model(self, model_name: str):
        """Initializes the GenerativeModel, returns None on failure."""
        try:
            # The _configure_api method is called before this.
            # If it fails, the constructor for GenerativeModel will raise an exception.
            model = genai.GenerativeModel(model_name)
            print(f"Gemini model '{model_name}' initialized successfully.")
            return model
        except Exception as e:
            print(f"Error initializing Gemini model '{model_name}': {e}")
            return None

    def _load_tag_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Loads the classification tag definitions from the JSON file."""
        try:
            path = os.path.join(project_root, 'config', 'tag_definitions.json')
            with open(path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("Error: `config/tag_definitions.json` not found.")
            return {}
        except json.JSONDecodeError:
            print("Error: `config/tag_definitions.json` is not valid JSON.")
            return {}

    def _construct_prompt(self, ticket_subject: str, ticket_body: str) -> str:
        """Constructs the detailed prompt for the Gemini API call."""
        if not self.tag_definitions:
            return ""

        # Extract tag names from the nested structure
        topic_tags = [tag["name"] for tag in self.tag_definitions.get('topic_tags', {}).get('tags', [])]
        sentiment_tags = [tag["name"] for tag in self.tag_definitions.get('sentiment', {}).get('tags', [])]
        priority_tags = [tag["name"] for tag in self.tag_definitions.get('priority', {}).get('tags', [])]

        topic_tags_str = ", ".join(f'"{tag}"' for tag in topic_tags)
        sentiment_tags_str = ", ".join(f'"{tag}"' for tag in sentiment_tags)
        priority_tags_str = ", ".join(f'"{tag}"' for tag in priority_tags)

        topic_desc = self._format_tags_with_descriptions('topic_tags')
        sentiment_desc = self._format_tags_with_descriptions('sentiment')
        priority_desc = self._format_tags_with_descriptions('priority')

        return f"""
        You are an expert AI assistant for Atlan, a data catalog company. Your task is to analyze and classify a customer support ticket based on its subject and body.

        **Instructions:**
        1.  Read the ticket content carefully to understand the user's issue.
        2.  Classify the ticket into three distinct categories: Topic, Sentiment, and Priority.
        3.  For each category, you MUST strictly choose from the provided list of valid tags.
        4.  Provide a confidence score (a float between 0.0 and 1.0) for each of the three classification categories.
        5.  Your final output MUST be a single, valid JSON object. Do not include any explanatory text, markdown formatting, or anything outside of the JSON structure.

        **Ticket Subject:** "{ticket_subject}"

        **Ticket Body:**
        ---
        {ticket_body}
        ---

        **Classification Categories and Valid Tags:**

        *   **topic_tags** (Select one or more from this list, based on the ticket's main subject):
            {topic_desc}

        *   **sentiment** (Select ONLY one from this list, based on the customer's emotional tone):
            {sentiment_desc}

        *   **priority** (Select ONLY one from this list based on urgency, user frustration, and business impact):
            {priority_desc}

        **Required JSON Output Format:**
        {{
          "classification": {{
            "topic_tags": ["<list of one or more chosen topic tags>"],
            "sentiment": "<the single chosen sentiment tag>",
            "priority": "<the single chosen priority tag>",
            "confidence_scores": {{
              "topic": <float>,
              "sentiment": <float>,
              "priority": <float>
            }}
          }}
        }}
        """

    def _format_tags_with_descriptions(self, category: str) -> str:
        """Formats tags with their descriptions for the prompt."""
        if not self.tag_definitions or category not in self.tag_definitions:
            return "No tags available"

        tags = self.tag_definitions[category].get('tags', [])
        formatted_tags = []

        for tag in tags:
            name = tag.get('name', '')
            description = tag.get('description', '')
            formatted_tags.append(f'- "{name}": {description}')

        return '\n            '.join(formatted_tags)

        return f"""
        You are an expert AI assistant for Atlan, a data catalog company. Your task is to analyze and classify a customer support ticket based on its subject and body.

        **Instructions:**
        1.  Read the ticket content carefully to understand the user's issue.
        2.  Classify the ticket into three distinct categories: Topic, Sentiment, and Priority.
        3.  For each category, you MUST strictly choose from the provided list of valid tags.
        4.  Provide a confidence score (a float between 0.0 and 1.0) for each of the three classification categories.
        5.  Your final output MUST be a single, valid JSON object. Do not include any explanatory text, markdown formatting, or anything outside of the JSON structure.

        **Ticket Subject:** "{ticket_subject}"

        **Ticket Body:**
        ---
        {ticket_body}
        ---

        **Classification Categories and Valid Tags:**

        *   **topic_tags** (Select one or more from this list, based on the ticket's main subject):
            {self._format_tags_with_descriptions('topic_tags')}

        *   **sentiment** (Select ONLY one from this list, based on the customer's emotional tone):
            {self._format_tags_with_descriptions('sentiment')}

        *   **priority** (Select ONLY one from this list based on urgency, user frustration, and business impact):
            {self._format_tags_with_descriptions('priority')}

        **Required JSON Output Format:**
        {{
          "classification": {{
            "topic_tags": ["<list of one or more chosen topic tags>"],
            "sentiment": "<the single chosen sentiment tag>",
            "priority": "<the single chosen priority tag>",
            "confidence_scores": {{
              "topic": <float>,
              "sentiment": <float>,
              "priority": <float>
            }}
          }}
        }}
        """

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the classification logic for a given ticket.

        Args:
            state: The current state, expected to contain 'subject' and 'body' of the ticket.

        Returns:
            The updated state with the 'classification' field added.
        """
        print("--- Executing Classification Agent ---")
        if not self.model:
            print("Error: Gemini model not initialized. Skipping classification.")
            return state

        ticket_subject = state.get("subject")
        ticket_body = state.get("body")

        if not ticket_subject or not ticket_body:
            print("Error: Ticket subject or body not found in state. Skipping classification.")
            return state

        prompt = self._construct_prompt(ticket_subject, ticket_body)
        if not prompt:
            print("Error: Could not construct prompt due to missing tag definitions. Skipping classification.")
            return state

        try:
            response = await self.model.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json"
                )
            )

            classification_data = json.loads(response.text)

            if not is_valid_classification_json(classification_data):
                print("Error: The classification JSON from the API is not in the expected format.")
                # Potentially add a retry logic here in a future version
                return state

            print(f"Classification successful: {json.dumps(classification_data, indent=2)}")

            updated_state = state.copy()
            updated_state.update(classification_data)

            return updated_state

        except Exception as e:
            print(f"An error occurred during classification: {e}")
            # Return the original state without modification in case of an error
            return state

    async def classify_ticket_batch(self, tickets: List[Dict[str, Any]],
                                   progress_callback=None) -> List[Dict[str, Any]]:
        """
        Classify multiple tickets in parallel with controlled concurrency.

        Args:
            tickets: List of ticket dictionaries to classify
            progress_callback: Optional callback function (current, total, message)

        Returns:
            List of classification results
        """
        if not self.model:
            print("Error: Gemini model not initialized. Skipping batch classification.")
            return []

        if not tickets:
            return []

        import asyncio
        from typing import Tuple

        semaphore = asyncio.Semaphore(5)  # Limit to 5 concurrent requests
        results = []

        async def classify_single_ticket(ticket: Dict[str, Any], index: int) -> Tuple[int, Dict[str, Any]]:
            """Classify a single ticket with semaphore control."""
            async with semaphore:
                try:
                    ticket_id = ticket.get('id', f'ticket_{index}')

                    if progress_callback:
                        progress_callback(index, len(tickets), f"Classifying {ticket_id}...")

                    # Prepare classification input
                    classification_input = {
                        "subject": ticket.get("subject", ""),
                        "body": ticket.get("body", "")
                    }

                    # Execute classification
                    result = await self.execute(classification_input)

                    # Add ticket metadata to result
                    result['ticket_id'] = ticket_id
                    result['original_ticket'] = ticket

                    return index, result

                except Exception as e:
                    print(f"Error classifying ticket {ticket.get('id', f'ticket_{index}')}: {e}")
                    return index, {
                        'ticket_id': ticket.get('id', f'ticket_{index}'),
                        'error': str(e),
                        'original_ticket': ticket
                    }

        # Create tasks for parallel execution
        tasks = [classify_single_ticket(ticket, i) for i, ticket in enumerate(tickets)]
        completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)

        # Sort results by original index and extract results
        sorted_results = sorted([task for task in completed_tasks if isinstance(task, tuple)],
                               key=lambda x: x[0])
        results = [result for _, result in sorted_results]

        return results
