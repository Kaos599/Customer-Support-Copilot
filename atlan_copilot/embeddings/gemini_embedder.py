import os
from google import genai

from typing import List

class GeminiEmbedder:
    """
    A class to generate embeddings for text using the Google Gemini API.

    This class acts as a wrapper around the google.generativeai embedding functionality,
    configured for the specific needs of this application.
    """
    def __init__(self, model_name: str = "models/text-embedding-004"):
        """
        Initializes the embedder.

        It assumes that the genai library has been configured with an API key
        at the application's entry point.

        Args:
            model_name: The name of the embedding model to use.
        """
        self.model_name = model_name
        self._configure_api()

    def _configure_api(self):
        """Configures the Gemini API key from environment variables."""
        try:
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY not found in environment variables.")
            self.api_key = api_key
            self.client = genai.Client(api_key=self.api_key)
            print("Gemini client configured successfully for embeddings.")
        except Exception as e:
            print(f"Warning: Could not configure Gemini client for embeddings: {e}")
            raise

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generates embeddings for a list of text documents.

        Args:
            texts: A list of strings to be embedded.

        Returns:
            A list of embeddings, where each embedding is a list of floats.
            Returns an empty list if an error occurs or if the input is empty.
        """
        if not texts:
            return []

        print(f"Generating embeddings for {len(texts)} documents using '{self.model_name}'...")
        try:
            # The embed_content method can handle a list of texts,
            # which is more efficient than sending one request per text.
            result = self.client.models.embed_content(
                model=self.model_name,
                contents=texts,
                config=genai.types.EmbedContentConfig(
                    task_type="QUESTION_ANSWERING"  
                )
            )
            print("Embedding generation successful.")
            return result.embeddings
        except Exception as e:
            print(f"An error occurred during embedding generation: {e}")
            return []
