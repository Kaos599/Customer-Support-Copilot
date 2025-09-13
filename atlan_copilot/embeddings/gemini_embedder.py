import os
import google.generativeai as genai
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
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not found in environment variables.")
            genai.configure(api_key=api_key)
            print("Gemini API configured successfully for embeddings.")
        except Exception as e:
            print(f"Warning: Could not configure Gemini API for embeddings: {e}")
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
            # The embed_content function can handle a list of texts,
            # which is more efficient than sending one request per text.
            result = genai.embed_content(
                model=self.model_name,
                content=texts,
                task_type="QUESTION_ANSWERING"  # Optimized for question-answering system
            )
            print("Embedding generation successful.")
            return result['embedding']
        except Exception as e:
            print(f"An error occurred during embedding generation: {e}")
            return []
