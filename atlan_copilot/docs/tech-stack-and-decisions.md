# Technology Stack & Design Decisions

This document outlines the technology stack chosen for the Atlan Customer Support Copilot and explains the key design decisions made during its development.

## 1. Technology Stack

The following technologies were used to build the application, as specified in the initial project brief:

-   **Backend Language**: Python 3.11+
-   **AI Orchestration**: [LangGraph](https://github.com/langchain-ai/langgraph)
-   **Large Language Models (LLM)**: Google Gemini Family
    -   `gemini-1.5-flash`: Used for fast and efficient tasks like ticket classification.
    -   `gemini-1.5-pro`: Used for more complex reasoning and high-quality response generation.
        -   `models/text-embedding-004`: Used for generating text embeddings.
-   **Frontend Framework**: [Streamlit](https://streamlit.io/)
-   **Vector Database**: [Qdrant](https://qdrant.tech/)
-   **Primary Database**: [MongoDB Atlas](https://www.mongodb.com/atlas)
-   **Web Scraping**: `requests` and `beautifulsoup4`
-   **Async MongoDB Driver**: `motor`

## 2. Key Design Decisions & Trade-offs

### a. Multi-Agent System with LangGraph
-   **Decision**: The core logic was structured as a multi-agent system orchestrated by LangGraph, rather than a monolithic chain.
-   **Rationale**:
    -   **Specialization**: This allows for creating specialized agents (`ClassificationAgent`, `RAGAgent`, `ResponseAgent`) that are experts at a single task. This improves accuracy and makes the system easier to debug and maintain.
    -   **Modularity**: Each agent can be developed, tested, and improved independently. For example, the RAG agent's search logic can be enhanced without affecting the classification agent.
    -   **Explicit State Management**: LangGraph's `StateGraph` provides a clear, typed `CopilotState` dictionary that tracks the progress of a query through the system. This makes the data flow transparent and predictable.
-   **Trade-off**: This approach introduces slightly more complexity upfront compared to a simple LLM chain, as it requires defining the graph structure, nodes, and edges. However, this pays off in scalability and maintainability.

### b. Sequential Processing for Rate Limiting
-   **Decision**: The application implements explicit delays (`asyncio.sleep`) to handle API rate limits, particularly in the UI dashboard and the agent orchestrator.
-   **Rationale**:
    -   During testing, concurrent API calls to the Gemini free tier resulted in `429` rate limit errors.
    -   The most robust solution in the given environment was to process API-dependent tasks sequentially with a delay, ensuring that the application remains within the free tier's requests-per-minute quota.
    -   A centralized delay node was added to the LangGraph orchestrator to manage the timing between calls to different models (`flash` vs. `pro`), which may have separate rate limit pools.
-   **Trade-off**: This significantly increases the processing time for batch operations (like classifying all tickets in the dashboard) and the response time for the chat interface. A production system with a paid API plan could use more sophisticated, concurrent processing with a proper rate-limiting library.

### c. Decoupled Data Ingestion
-   **Decision**: The data ingestion pipeline (scraping, processing, embedding) is implemented as a separate, runnable script (`scripts/scrape_and_embed.py`).
-   **Rationale**:
    -   Populating the vector database is a heavy, one-time or periodic task. Decoupling it from the main application runtime prevents it from blocking the UI or API.
    -   It allows for the ingestion pipeline to be run on a schedule (e.g., a nightly cron job) to keep the knowledge base up-to-date without redeploying the main application.
-   **Trade-off**: This means the knowledge base is not updated in real-time. There will be a delay between when documentation is published and when it becomes available to the RAG agent.

### d. Python `sys.path` Manipulation
-   **Decision**: The project uses a `sys.path.insert()` call at the top of each script to ensure correct module resolution.
-   **Rationale**:
    -   During development, standard module resolution techniques (`python -m`) failed unexpectedly within the execution environment.
    -   To overcome this environmental blocker and ensure the application was runnable, a pragmatic decision was made to use `sys.path` manipulation, which proved to be a reliable workaround.
-   **Trade-off**: This is not standard Python best practice. In a typical environment, the project would be installed as an editable package or run as a module. This is a known issue that would need to be revisited if the execution environment changes.

### e. UI Development with Placeholder Backend
-   **Decision**: The Streamlit UI was developed with a placeholder chat backend before the LangGraph orchestrator was fully implemented.
-   **Rationale**: This allowed for parallel development and rapid prototyping of the user interface. The UI components were built and tested independently, with a clear contract for how they would eventually connect to the backend logic.
-   **Trade-off**: The UI provided a "mock" experience that was not fully representative of the final system's performance (e.g., response times).
