# Setup and Installation Guide

This guide provides detailed instructions on how to set up the environment and run my Atlan Customer Support Copilot on your local machine. I've designed this setup process to be as straightforward as possible while ensuring all components work seamlessly together.

## 1. Prerequisites

Throughout my development process, I used and tested the following requirements:
-   Python 3.11 or higher (I recommend 3.11+ for optimal performance)
-   `pip` for package management
-   `git` for cloning the repository

## 2. Step-by-Step Installation

I've structured the installation process into clear steps that I've tested multiple times to ensure reliability.

### Step 2.1: Clone the Repository
First, I want you to clone my project repository to your local machine using git:
```bash
git clone <repository-url>
cd <repository-name>
```

### Step 2.2: Set Up a Virtual Environment (Recommended)
I highly recommend using a virtual environment, as I designed the project dependencies to be isolated and avoid conflicts with other Python projects you might have.

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
# venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 2.3: Install Dependencies
I've carefully curated all the required Python packages in the `requirements.txt` file. Install them using:
```bash
pip install -r atlan_copilot/requirements.txt
```

## 3. Configuration

I designed my application to use environment variables for connecting to external services, ensuring security and flexibility.

### Step 3.1: Create the `.env` File
I use a `.env` file in the root directory to manage secrets and configuration. I've structured this to keep sensitive information separate from the codebase. You can create this file by copying the `atlan_copilot/.env` file if it exists, or by creating a new one from scratch.

Create a file named `.env` in the root of the project and add the following content that I've configured:

```env
# API Key for Google Gemini Services (I use this for embeddings and generation)
GOOGLE_API_KEY="your-google-api-key"

# API Key for your Qdrant Cloud instance (I use this for vector storage)
QDRANT_API_KEY="your-qdrant-api-key"

# URL for your Qdrant cluster (I connect to this for similarity searches)
# e.g., https://<cluster-id>.<region>.cloud.qdrant.com:6333
QDRANT_HOST="your-qdrant-cluster-url"

# Connection string for your MongoDB Atlas cluster (I store tickets here)
MONGO_URI="mongodb+srv://..."

# Name of the MongoDB database (I use this for organization)
MONGO_DB="Atlan"

# Name of the MongoDB collection for tickets (I store classified tickets here)
MONGO_COLLECTION="tickets"
```

### Step 3.2: Populate the Environment Variables
I need you to obtain the following credentials for my system to work properly:
-   **`GOOGLE_API_KEY`**: I use this for accessing Gemini models. Obtain this from the [Google AI Studio](https://aistudio.google.com/app/apikey).
-   **`QDRANT_API_KEY`** and **`QDRANT_HOST`**: I use these for vector database operations. Obtain these from your [Qdrant Cloud dashboard](https://cloud.qdrant.io/).
-   **`MONGO_URI`**: I use this for storing and retrieving ticket data. Obtain this from your [MongoDB Atlas dashboard](https://cloud.mongodb.com/). Ensure your local IP address is whitelisted to allow connections.

## 4. Running the Application and Scripts

I've organized all commands to be run from the **root of the project directory** for consistency.

### Step 4.1: Run the Health Check (My Recommended First Step)
I created a comprehensive health check script to verify that all your connections and credentials are set up correctly. Run my health check:
```bash
python atlan_copilot/tests/health_check.py
```
This will test the connections to MongoDB, Qdrant, and both Gemini models that I integrated, providing you with a detailed summary of the status.

### Step 4.2: Populate the Database
I've prepared sample ticket data that you can load into your MongoDB database using my data loading script:
```bash
python atlan_copilot/scripts/load_sample_data.py
```

### Step 4.3: Populate the Vector Store with My Enhanced Script
To enable my RAG agent's search capabilities, you need to run my enhanced documentation scraping script that I've improved. I've created a comprehensive script that populates the Qdrant vector database with content from docs.atlan.com and other documentation sources.

**Note**: I designed this as a thorough process that may take some time but ensures high-quality embeddings.

You can use my new enhanced script:
```bash
# Use my comprehensive population script (recommended)
python atlan_copilot/utils/populate_vector_db.py

# Or use my original scraping script with various options
python atlan_copilot/scripts/scrape_and_embed.py

# I also provide these specific options:
# Scrape only a specific source
python atlan_copilot/scripts/scrape_and_embed.py --source docs

# Scrape with a different page limit that I've configured
python atlan_copilot/scripts/scrape_and_embed.py --max_pages 10
```
*You must have a valid `QDRANT_HOST` configured for my scripts to work properly.*

### Step 4.4: Launch My Streamlit UI
To start the user interface that I designed, run the following command:
```bash
streamlit run atlan_copilot/app.py
```
You can now open the provided URL (e.g., `http://localhost:8501`) in your web browser to interact with my application and explore all the features I've implemented.
