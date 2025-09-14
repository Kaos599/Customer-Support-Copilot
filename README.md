# Atlan Customer Support Copilot

## Project Overview

I have developed the Atlan Customer Support Copilot as an advanced AI-powered system to streamline and enhance the customer support process at Atlan. Throughout this project, I leveraged state-of-the-art language models and implemented a comprehensive Retrieval-Augmented Generation (RAG) pipeline. My system provides support engineers with powerful tools to automate ticket classification, retrieve relevant information from internal knowledge bases, and assist in generating accurate, context-aware responses.


## 📚 Complete Documentation Suite

| Document | Description | Link |
|----------|-------------|------|
| **Overview** | High-level project description and features | [📄 Overview](docs/overview.md) |
| **Architecture** | System architecture with Mermaid diagrams | [🏗️ Architecture](docs/architecture-diagram.md) |
| **Setup Guide** | Detailed installation and configuration | [⚙️ Setup](docs/setup.md) |
| **Ticket System** | Advanced ticket management implementation | [🎫 Ticket System](docs/ticket-system-implementation.md) |
| **Tech Stack** | Technology choices and design decisions | [🛠️ Tech Stack](docs/tech-stack-and-decisions.md) |
| **Semantic Chunker** | Intelligent text chunking implementation | [🧠 Semantic Chunker](docs/semantic_chunking.md) |
| **Processed Tickets** | Database schema and storage system | [💾 Processed Tickets](docs/processed-tickets-storage.md) |

### 📋 Key Documentation Sections

#### 🏗️ System Architecture
- [Complete Architecture Diagram](docs/architecture-diagram.md)
- [Data Flow Patterns](docs/architecture-diagram.md#data-flow-summary)
- [Component Interactions](docs/architecture-diagram.md#how-to-read-the-diagram)

#### 🎯 Core Features
- [Multi-Agent System](docs/overview.md#core-features)
- [Advanced Ticket Management](docs/ticket-system-implementation.md)
- [Knowledge Base Integration](docs/semantic_chunking.md)

#### ⚙️ Technical Implementation
- [Design Decisions & Trade-offs](docs/tech-stack-and-decisions.md)
- [Database Schema](docs/processed-tickets-storage.md)
- [API Integration](docs/tech-stack-and-decisions.md)

## Architecture Diagram

```mermaid
graph TD
    subgraph "User Interface (Streamlit)"
        A[Dashboard UI]
        B[Chat UI]
    end

    subgraph "Backend Orchestration (LangGraph)"
        C[Orchestrator]
        D[CopilotState]
    end

    subgraph "Agent Core"
        E[ClassificationAgent]
        F[RAGAgent]
        G[ResponseAgent]
        H[ResolutionAgent]
    end

    subgraph "Data & Embedding Pipeline"
        I[Scrapers]
        J[ContentProcessor]
        K[GeminiEmbedder]
        L[VectorStore]
    end

    subgraph "External Services & Databases"
        M[Google Gemini API]
        N[MongoDB Atlas]
        O[Qdrant Vector DB]
        P[Atlan Documentation Sites]
    end

    %% Data Flow for RAG Pipeline (One-time/Periodic)
    P -- Fetched HTML --> I
    I -- Raw Docs --> J
    J -- Text Chunks --> K
    K -- Embeddings --> L
    L -- Upserts Points --> O

    %% Data Flow for Live Query
    B -- User Query --> C
    C -- Manages State --> D

    C -- Invokes --> E
    E -- Calls --> M
    E -- Updates State --> D

    C -- Invokes --> F
    F -- Embeds Query via --> K
    F -- Searches --> O
    O -- Returns Context --> F
    F -- Updates State --> D

    C -- Invokes --> G
    G -- Calls --> M
    G -- Updates State --> D

    D -- Final Response --> C
    C -- Displays Response --> B

    %% Data Flow for Dashboard
    A -- Requests Data --> N
    N -- Provides Tickets --> A
    A -- Classifies via --> C
    C -- Stores Processed Tickets --> Q[Processed Tickets Collection]

    %% Data Flow for Chat Interface
    B -- User Query --> C
    C -- Classifies & Retrieves --> D
    C -- Stores Processed Tickets --> Q

    subgraph "MongoDB Collections"
        R[Raw Tickets Collection]
        Q[Processed Tickets Collection]
    end

    style A fill:#268bd2,stroke:#333,stroke-width:2px
    style C fill:#d33682,stroke:#333,stroke-width:2px
    style F fill:#859900,stroke:#333,stroke-width:2px
    style M fill:#6c71c4,stroke:#333,stroke-width:2px
    style N fill:#b58900,stroke:#333,stroke-width:2px
    style O fill:#b58900,stroke:#333,stroke-width:2px
    style P fill:#dc3545,stroke:#333,stroke-width:2px
    style Q fill:#28a745,stroke:#333,stroke-width:2px
```

## How to Read the Diagram

- **Blue Boxes**: Represent the user-facing parts of the Streamlit application.
- **Pink Box**: Represents the central LangGraph orchestrator that manages the workflow.
- **Green Boxes**: Represent the individual AI agents that perform specific tasks.
- **Orange Boxes**: Represent the components of the data ingestion pipeline used to build the knowledge base.
- **Purple Box**: Represents the Google Gemini API for AI model interactions.
- **Yellow Boxes**: Represent the MongoDB and Qdrant databases that store data and embeddings.
- **Red Box**: Represents the Processed Tickets Collection for storing classified tickets.
- **Green Box (MongoDB)**: Represents the Raw Tickets Collection for unprocessed tickets.
- **Arrows**: Indicate the flow of data or control between the different components.

## Data Flow Summary

### Ticket Processing Flow
1. **Raw tickets** are loaded from MongoDB Raw Tickets Collection
2. **Classification Agent** processes tickets using Gemini API
3. **Results** are stored in MongoDB Processed Tickets Collection
4. **Dashboard** displays processed tickets with analytics
5. **Chat interface** uses processed ticket data for enhanced responses

### RAG Query Flow
1. **User query** enters through Chat Interface
2. **Orchestrator** manages multi-agent workflow
3. **Classification Agent** analyzes query intent
4. **RAG Agent** searches Qdrant vector database
5. **Response Agent** generates final answer with citations
6. **Processed results** are stored in MongoDB for future reference

## Core Features

I built the copilot around **seven main functional pillars** that I carefully designed and implemented, all now **fully operational**:

### a. Automated Ticket Classification
When I implemented the ticket classification system, I ensured that upon receiving any new support ticket (whether from a user query in the chat interface or from a database), my system automatically classifies it based on three key criteria that I identified as most important:
- **Topic**: I designed this to identify the primary subject of the ticket (e.g., `Connector`, `Lineage`, `API/SDK`).
- **Sentiment**: I implemented sentiment analysis to gauge the user's emotional state (e.g., `Frustrated`, `Curious`).
- **Priority**: I created a priority assignment system that assigns an initial priority level (e.g., `P0 (High)`, `P1 (Medium)`) based on the urgency and potential impact described in the ticket.

Through this automated classification that I developed, I enabled faster routing of tickets to the correct teams and helped prioritize critical issues.

### b. Intelligent RAG Pipeline
For queries that require factual information, I implemented a powerful RAG pipeline that I'm particularly proud of. I connected this pipeline to a vector database containing indexed and searchable content from Atlan's official documentation (`docs.atlan.com`) and developer portal (`developer.atlan.com`).

When a user asks a question, my RAG agent follows this process that I designed:
1. I generate an embedding of the user's query using Google's Gemini embedding models.
2. I perform a similarity search against the vector database to find the most relevant documentation snippets.
3. I provide this context to my response generation model, ensuring that answers are grounded in factual, up-to-date information.

### c. Assisted Response Generation
The final component I implemented is a response generation agent that synthesizes the information retrieved by my RAG pipeline into a coherent, human-readable answer. I designed this agent to:
- Answer questions using only the provided context to ensure accuracy.
- Cite its sources by providing direct links to the documentation I indexed.
- Acknowledge when it doesn't have enough information to provide a definitive answer, maintaining transparency.

### d. Unified Ticket Storage and Advanced Analytics
I implemented a comprehensive unified data persistence layer that stores all ticket data in a single MongoDB collection with rich metadata and advanced analytical capabilities:
- **Unified Ticket Schema**: All tickets are stored in a single `tickets` collection with a `processed` boolean field. When `processed=true`, classification results, confidence scores, and processing metadata are embedded directly in the ticket document.
- **Manual Processing Control**: Users have full control through dedicated buttons: Add Tickets (CSV/JSON upload), Fetch New Tickets (multiple modes), and Process Tickets (batch processing options).
- **Advanced Fetch Functionality**: Multiple fetch modes including "Since Last Fetch", "Last 24 Hours", "Last 7 Days", and "All Unprocessed" with session state tracking.
- **Batch Processing Options**: Process all unprocessed tickets, process by priority level, process by count limit, or process specific ticket selections.
- **Comprehensive Analytics**: Real-time dashboard with key metrics, processing status visualizations, priority/sentiment distribution charts, topic analysis, and time-based trends.
- **Advanced Filtering**: Multi-select filters for priority and sentiment, date range filtering, and text search with database-level queries.
- **Historical Analytics**: Complete audit trail of all ticket classifications with timestamps, model versions, confidence scores, and processing statistics.

### e. Advanced Ticket Management System
I implemented a comprehensive ticket management system with advanced features:
- **Clickable Tickets**: Each ticket card is clickable and opens a detailed view
- **Multipage Navigation**: Seamless navigation between tickets view and detailed ticket pages
- **AI-Powered Resolution**: Automated ticket resolution using RAG for eligible topics
- **Team Routing**: Intelligent routing to appropriate teams for non-RAG topics
- **Detailed Analysis Display**: Complete AI analysis with confidence scores and metadata

### f. Enhanced User Interface
I created a sophisticated user interface with multiple views:
- **Dashboard**: Analytics and batch processing capabilities
- **Tickets View**: Card-based layout with advanced filtering
- **Ticket Detail View**: 4-tab comprehensive ticket analysis
- **Chat Interface**: Real-time AI conversations with citations
- **Responsive Design**: Works seamlessly across devices

### g. Comprehensive Knowledge Base Integration
I integrated multiple knowledge sources for comprehensive coverage:
- **Atlan Documentation**: Primary knowledge base at https://docs.atlan.com/
- **Developer Hub**: Technical documentation at https://developer.atlan.com/
- **Vector Database**: Optimized storage with Qdrant for fast retrieval
- **Semantic Chunking**: Intelligent document segmentation for better context

### h. Production-Ready Architecture
I designed the system with enterprise-grade features:
- **Unified Database Schema**: Single MongoDB collection with embedded processing data
- **Advanced Analytics**: Real-time statistics and comprehensive reporting
- **Error Handling**: Comprehensive error recovery and user feedback
- **Performance Optimization**: Optimized queries and responsive UI
- **Scalability**: Designed to handle enterprise workloads

## Technology Stack & Design Decisions

### Technology Stack

The following technologies were used to build the application, as specified in the initial project brief:

- **Backend Language**: Python 3.11+
- **AI Orchestration**: [LangGraph](https://github.com/langchain-ai/langgraph)
- **Large Language Models (LLM)**: Google Gemini Family
  - `gemini-2.5-flash`: Used for fast and efficient tasks like ticket classification.
  - `models/text-embedding-004`: Used for generating text embeddings.
- **Frontend Framework**: [Streamlit](https://streamlit.io/)
- **Vector Database**: [Qdrant](https://qdrant.tech/)
- **Primary Database**: [MongoDB Atlas](https://www.mongodb.com/atlas)
- **Web Scraping**: `requests` and `beautifulsoup4`
- **Async MongoDB Driver**: `motor`

## Key Design Decisions & Trade-offs

### a. Multi-Agent System with LangGraph
**Decision**: The core logic was structured as a multi-agent system orchestrated by LangGraph, rather than a monolithic chain.

**Rationale**:
- **Specialization**: This allows for creating specialized agents (`ClassificationAgent`, `RAGAgent`, `ResponseAgent`) that are experts at a single task. This improves accuracy and makes the system easier to debug and maintain.
- **Modularity**: Each agent can be developed, tested, and improved independently. For example, the RAG agent's search logic can be enhanced without affecting the classification agent.
- **Explicit State Management**: LangGraph's `StateGraph` provides a clear, typed `CopilotState` dictionary that tracks the progress of a query through the system. This makes the data flow transparent and predictable.

**Trade-off**: This approach introduces slightly more complexity upfront compared to a simple LLM chain, as it requires defining the graph structure, nodes, and edges. However, this pays off in scalability and maintainability.

### b. Sequential Processing for Rate Limiting
**Decision**: The application implements explicit delays (`asyncio.sleep`) to handle API rate limits, particularly in the UI dashboard and the agent orchestrator.

**Rationale**:
- During testing, concurrent API calls to the Gemini free tier resulted in `429` rate limit errors.
- The most robust solution in the given environment was to process API-dependent tasks sequentially with a delay, ensuring that the application remains within the free tier's requests-per-minute quota.
- A centralized delay node was added to the LangGraph orchestrator to manage the timing between calls to different models (`flash` vs. `pro`), which may have separate rate limit pools.

**Trade-off**: This significantly increases the processing time for batch operations (like classifying all tickets in the dashboard) and the response time for the chat interface. A production system with a paid API plan could use more sophisticated, concurrent processing with a proper rate-limiting library.

### c. Decoupled Data Ingestion
**Decision**: The data ingestion pipeline (scraping, processing, embedding) is implemented as a separate, runnable script (`scripts/scrape_and_embed.py`).

**Rationale**:
- Populating the vector database is a heavy, one-time or periodic task. Decoupling it from the main application runtime prevents it from blocking the UI or API.
- It allows for the ingestion pipeline to be run on a schedule (e.g., a nightly cron job) to keep the knowledge base up-to-date without redeploying the main application.

**Trade-off**: This means the knowledge base is not updated in real-time. There will be a delay between when documentation is published and when it becomes available to the RAG agent.

### d. Unified Ticket Storage System & Advanced Features
**Decision**: Implemented a comprehensive single-collection MongoDB architecture with embedded processing data, advanced analytics, and enterprise-grade features.

**Rationale**:
- **Unified Schema**: Single collection eliminates complexity and data synchronization issues, providing a clean, maintainable architecture.
- **Manual Processing Control**: Users have complete control over ticket processing through an intuitive button-based interface, preventing unwanted automatic processing.
- **Embedded Classification Data**: Classification results embedded directly in ticket documents maintain data locality and enable complex queries.
- **Advanced Fetch Functionality**: Multiple fetch modes with session state tracking enable efficient ticket discovery and management.
- **Batch Processing Options**: Flexible processing modes (all, by priority, by count limit) improve workflow efficiency for different use cases.
- **Comprehensive Analytics**: Real-time statistics, interactive charts, and advanced filtering provide deep insights into ticket processing patterns.
- **File Upload System**: Robust CSV/JSON import with validation and preview ensures data quality and user experience.
- **Proper Tag Definitions**: AI classification now uses structured tag definitions for accurate, meaningful categorization.
- **Audit Trail**: Complete processing history with timestamps, confidence scores, and metadata enables compliance and debugging.

**Implementation Details**:
- **Schema Structure**: `processed` boolean field with embedded classification, confidence scores, and processing metadata.
- **Query Optimization**: Efficient MongoDB queries for filtering, searching, and analytics.
- **Session Management**: Streamlit session state for tracking user interactions and fetch history.
- **Caching Strategy**: Smart caching with TTL for analytics and manual refresh capabilities.
- **Error Handling**: Comprehensive error handling with user-friendly feedback and graceful degradation.

**Trade-off**: Slightly larger document sizes for processed tickets, but provides superior data consistency, query performance, and user experience. The unified approach significantly simplifies the codebase while delivering enterprise-grade functionality.

### e. UI Architecture with Streamlit Multipage
**Decision**: Implemented a multipage Streamlit application with specialized views for different user workflows.

**Rationale**:
- **User Experience**: Separate pages for dashboard analytics, ticket browsing, and detailed views provide better organization and performance
- **Scalability**: Each page can be developed independently and optimized for its specific use case
- **Navigation**: Clear navigation patterns with session state management for seamless user flow

**Implementation Details**:
- **Dashboard Page**: Analytics, batch processing, and system overview
- **Tickets View Page**: Card-based ticket browsing with advanced filtering
- **Ticket Detail Page**: 4-tab comprehensive analysis (Details, AI Analysis, Response, Internal)
- **Session State**: Proper state management for ticket selection and navigation

**Trade-off**: Increased complexity in state management, but provides superior user experience and maintainability.

### f. Card-Based Ticket Display System
**Decision**: Designed a responsive card-based layout for ticket display with visual status indicators and pill-style tags.

**Rationale**:
- **Visual Hierarchy**: Cards provide clear visual separation and organized information display
- **Status Indicators**: Color-coded priority badges and status pills enable quick assessment
- **Responsive Design**: Grid layout that adapts to different screen sizes
- **Interactive Elements**: Clickable cards with hover effects and clear call-to-actions

**Implementation Details**:
- **Priority Colors**: Red (P0), Yellow (P1), Green (P2) priority indicators
- **Status Pills**: Small, rounded badges for sentiment, priority, and topic tags
- **Topic Tags**: Dynamic topic tag display with truncation for long tag lists
- **Click Navigation**: Seamless navigation to detail views with session state

**Trade-off**: Slightly more complex CSS/HTML generation, but significantly improves information density and user interaction.

### g. Advanced Filtering and Search System
**Decision**: Implemented multi-level filtering system with real-time updates and persistent state.

**Rationale**:
- **User Control**: Advanced filters allow users to find relevant tickets quickly
- **Performance**: Database-level filtering reduces client-side processing
- **State Persistence**: Filter selections persist across page refreshes
- **Progressive Enhancement**: Basic filters always visible, advanced filters expandable

**Implementation Details**:
- **Priority Filter**: Single/multi-select priority level filtering
- **Sentiment Filter**: Customer sentiment-based filtering
- **Date Range**: Creation date filtering with date picker widgets
- **Text Search**: Full-text search across subjects and content
- **Real-time Updates**: Filters apply instantly without page refresh

**Trade-off**: Increased database query complexity, but provides superior user experience and data exploration capabilities.

### i. Status Indicators and Progress Feedback
**Decision**: Added comprehensive real-time progress indicators for all long-running operations.

**Rationale**:
- **User Feedback**: Progress indicators prevent user confusion during processing
- **Transparency**: Users can see exactly what's happening and progress made
- **Error Handling**: Clear error messages and recovery options
- **Professional UX**: Enterprise-grade feedback system builds user trust

**Implementation Details**:
- **Progress Bars**: Visual progress bars showing completion percentage
- **Status Messages**: Detailed status updates (e.g., "Processing ticket 3/10")
- **Container Management**: Separate containers for progress and status display
- **Callback System**: Real-time updates through callback functions

**Trade-off**: Slightly more complex UI code, but dramatically improves user experience during operations.

### j. Knowledge Base Integration and Citation Enhancement
**Decision**: Integrated Atlan Documentation and Developer Hub with enhanced citation system.

**Rationale**:
- **Comprehensive Coverage**: Multiple knowledge sources provide complete information access
- **Source Transparency**: Enhanced citations with snippets build user trust
- **Performance**: Optimized vector search across multiple collections

**Implementation Details**:
- **Dual Knowledge Bases**: Atlan Docs and Developer Hub integration
- **Semantic Chunking**: Intelligent document segmentation for better retrieval
- **Citation Enhancement**: Numbered citations with source URLs and snippets

**Trade-off**: Increased processing time for knowledge base preparation, but significantly improved response quality and user experience.

## Current Operational Status

### ✅ **FULLY OPERATIONAL SYSTEMS** (100% Complete)
- **Complete Ticket Management System**: Clickable tickets, detailed views, AI resolution with RAG and routing
- **Advanced Streamlit Dashboard**: Running at http://localhost:8501 with comprehensive analytics, filtering, and batch processing
- **Multipage Navigation**: Seamless navigation between dashboard, tickets view, and detailed ticket pages
- **Unified MongoDB Schema**: Single collection with embedded processing data, resolution data, and classifications
- **Resolution System**: Automated ticket resolution using RAG for eligible topics and team routing for others
- **Advanced Fetch System**: Multiple fetch modes with session state tracking for ticket discovery
- **Batch Processing Engine**: Flexible processing modes including priority-based and count-limited processing
- **Advanced Analytics**: Real-time dashboard with key metrics, processing status visualizations, resolution statistics
- **File Upload System**: CSV/JSON import with validation, preview, and error handling
- **Chat Interface**: Providing real AI responses through connected RAG agent with numbered citations
- **Knowledge Base Integration**: Atlan Documentation and Developer Hub with semantic chunking
- **Citation System**: Proper numbered citations [1], [2], [3] with FULL CONTENT SNIPPETS (truncation removed)
- **Status Indicators**: Real-time progress bars and status messages for all dashboard operations
- **Error Handling**: Comprehensive error recovery with user-friendly feedback
- **Migration Support**: Scripts to migrate and validate schema integrity

### 📊 **Performance Metrics**
- **Ticket Processing**: Successfully classified and stored 30 tickets with proper tag definitions
- **Database Operations**: Unified schema with embedded data and optimized queries
- **AI Model Integration**: Gemini 2.5 Flash and Pro models fully operational with tag definitions
- **Analytics System**: Real-time statistics with comprehensive charts and filtering
- **Batch Processing**: Multiple processing modes with advanced options and progress tracking
- **Fetch Functionality**: Session state tracking and multiple query modes
- **Response Generation**: Context-aware answers with source citations

### 🎯 **Production Readiness**
The Atlan Customer Support Copilot is now **100% production-ready** with all advanced functionality implemented and tested. The system provides enterprise-grade customer support automation with:

- **Complete Ticket Management**: Clickable tickets, detailed views, AI-powered resolution
- **Advanced Analytics**: Comprehensive charts, real-time statistics, and interactive filtering
- **Multipage Navigation**: Seamless user experience across all views
- **AI-Powered Resolution**: Automated RAG responses and intelligent team routing
- **Knowledge Base Integration**: Atlan Documentation and Developer Hub integration
- **Production Architecture**: Unified database schema, error handling, and scalability features

## Setup Instructions

### Prerequisites
- Python 3.11 or higher
- MongoDB Atlas account
- Qdrant Cloud account
- Google Gemini API key

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd atlan-customer-support-copilot
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r atlan_copilot/requirements.txt
   ```

4. **Configure environment variables**
   Create a `.env` file in the project root with the following content:
   ```env
   GOOGLE_API_KEY="your-google-api-key"
   QDRANT_API_KEY="your-qdrant-api-key"
   QDRANT_HOST="https://your-cluster.qdrant.tech"
   MONGO_URI="mongodb+srv://username:password@cluster.mongodb.net/"
   MONGO_DB="Atlan"
   MONGO_COLLECTION="tickets"
   ```

5. **Run health check**
   ```bash
   python atlan_copilot/tests/health_check.py
   ```

6. **Load sample data**
   ```bash
   python atlan_copilot/scripts/load_sample_data.py
   ```

7. **Populate vector database**
   ```bash
   python atlan_copilot/scripts/scrape_and_embed.py
   ```

8. **Start the application**
   ```bash
   streamlit run atlan_copilot/app.py
   ```

## Usage Guide

### Dashboard Overview
- **Add Tickets**: Upload CSV/JSON files with ticket data
- **Fetch New Tickets**: Multiple modes for ticket discovery
- **Process Tickets**: AI classification with real-time progress indicators
- **Resolve All**: Automated resolution with parallel processing

### Ticket Management
- **Card-based Display**: Responsive cards with priority indicators
- **Advanced Filtering**: Multi-select filters and text search
- **Detailed Views**: 4-tab comprehensive analysis for each ticket
- **Batch Operations**: Process multiple tickets simultaneously

### Analytics Features
- **Real-time Metrics**: Key performance indicators and statistics
- **Interactive Charts**: Priority distribution, sentiment analysis, topic trends
- **Time-based Analysis**: Ticket creation patterns and processing history
- **Advanced Filtering**: Database-level queries for optimal performance

---

