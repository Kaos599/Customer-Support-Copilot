import os
import time
import asyncio
from typing import List, Optional
import google.genai as genai

from google.genai import errors as genai_errors

class GeminiEmbedder:
    """
    A class to generate embeddings for text using the Google Gemini API.

    This class acts as a wrapper around the google.generativeai embedding functionality,
    configured for the specific needs of this application with rate limiting and retry logic.
    """
    def __init__(self, model_name: str = "models/text-embedding-004", requests_per_minute: int = 30):
        """
        Initializes the embedder.

        Args:
            model_name: The name of the embedding model to use.
            requests_per_minute: Rate limit for API calls (default: 30 RPM for safety)
        """
        self.model_name = model_name
        self.requests_per_minute = requests_per_minute
        self.request_times = []
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

    def _wait_for_rate_limit(self):
        """Implements rate limiting to avoid hitting API limits."""
        current_time = time.time()
        # Remove requests older than 1 minute
        self.request_times = [t for t in self.request_times if current_time - t < 60]

        if len(self.request_times) >= self.requests_per_minute:
            # Calculate wait time until we can make another request
            oldest_request = min(self.request_times)
            wait_time = 60 - (current_time - oldest_request)
            if wait_time > 0:
                print(f"Rate limit reached. Waiting {wait_time:.1f} seconds...")
                time.sleep(wait_time)

    def _should_retry(self, error: Exception, attempt: int) -> bool:
        """Determine if we should retry based on the error type and attempt count."""
        max_retries = 3

        if attempt >= max_retries:
            return False

        # Retry on rate limit errors (429)
        if hasattr(error, 'code') and error.code == 429:
            return True

        # Retry on temporary server errors (5xx)
        if hasattr(error, 'code') and str(error.code).startswith('5'):
            return True

        # Retry on specific Gemini API errors
        if isinstance(error, genai_errors.APIError):
            return True

        return False

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generates embeddings for a list of text documents with rate limiting and retry logic.

        Args:
            texts: A list of strings to be embedded.

        Returns:
            A list of embeddings, where each embedding is a list of floats.
            Returns an empty list if an error occurs or if the input is empty.
        """
        if not texts:
            return []

        print(f"Generating embeddings for {len(texts)} documents using '{self.model_name}'...")

        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                # Apply rate limiting
                self._wait_for_rate_limit()

                # Record this request time
                self.request_times.append(time.time())

                # The embed_content function can handle a list of texts,
                # which is more efficient than sending one request per text.
                result = genai.embed_content(
                    model=self.model_name,
                    content=texts,
                    task_type="QUESTION_ANSWERING"  # Optimized for question-answering system
                )

                if result and 'embedding' in result:
                    print(f"Embedding generation successful for {len(texts)} texts.")
                    return result['embedding']
                else:
                    print(f"Warning: Unexpected response format from embedding API: {result}")
                    return []

            except Exception as e:
                print(f"Attempt {attempt + 1}/{max_attempts} failed: {e}")

                if self._should_retry(e, attempt):
                    # Exponential backoff: wait 2^attempt seconds
                    wait_time = 2 ** attempt
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"Max retries exceeded or non-retryable error. Giving up.")
                    return []

        print("All embedding attempts failed.")
        return []
