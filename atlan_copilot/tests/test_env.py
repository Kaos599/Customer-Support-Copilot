import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print('Environment variables after loading .env:')
print(f'QDRANT_HOST: {os.getenv("QDRANT_HOST")}')
print(f'GOOGLE_API_KEY: {os.getenv("GOOGLE_API_KEY", "Not set")[:20]}...')
print(f'MONGO_URI: {os.getenv("MONGO_URI", "Not set")[:20]}...')
