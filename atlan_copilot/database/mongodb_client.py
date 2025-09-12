import os
import motor.motor_asyncio
from typing import List, Dict, Optional

class MongoDBClient:
    """
    An asynchronous client for interacting with a MongoDB database.
    """
    def __init__(self):
        """
        Initializes the MongoDB client by reading connection details from environment variables.
        """
        self.mongo_uri = os.getenv("MONGO_URI")
        self.mongo_db_name = os.getenv("MONGO_DB")
        self.mongo_collection_name = os.getenv("MONGO_COLLECTION")

        if not all([self.mongo_uri, self.mongo_db_name, self.mongo_collection_name]):
            raise ValueError("MongoDB environment variables (MONGO_URI, MONGO_DB, MONGO_COLLECTION) must be set.")

        self.client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
        self.db: Optional[motor.motor_asyncio.AsyncIOMotorDatabase] = None
        self.collection: Optional[motor.motor_asyncio.AsyncIOMotorCollection] = None

    async def connect(self):
        """
        Establishes an asynchronous connection to the MongoDB server and database.
        Pings the server to verify the connection.
        """
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(self.mongo_uri)
            self.db = self.client[self.mongo_db_name]
            self.collection = self.db[self.mongo_collection_name]
            # The ismaster command is cheap and does not require auth.
            await self.client.admin.command('ismaster')
            print("MongoDB connection successful.")
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            self.client = None
            self.db = None
            self.collection = None
            raise

    async def close(self):
        """
        Closes the connection to MongoDB.
        """
        if self.client:
            self.client.close()
            print("MongoDB connection closed.")

    async def insert_tickets(self, tickets_data: List[Dict]) -> Optional[List[str]]:
        """
        Inserts a list of ticket documents into the collection.

        Args:
            tickets_data: A list of dictionaries, where each dictionary represents a ticket.

        Returns:
            A list of string representations of the inserted document IDs, or None if insertion fails.
        """
        if self.collection is None:
            print("Error: MongoDB connection not established. Call connect() first.")
            return None
        try:
            result = await self.collection.insert_many(tickets_data, ordered=False)
            return [str(doc_id) for doc_id in result.inserted_ids]
        except Exception as e:
            print(f"Error inserting tickets into MongoDB: {e}")
            return None

    async def get_all_tickets(self) -> List[Dict]:
        """
        Retrieves all tickets from the collection.

        Returns:
            A list of ticket documents.
        """
        if self.collection is None:
            print("Error: MongoDB connection not established. Call connect() first.")
            return []

        tickets = []
        try:
            async for document in self.collection.find({}):
                document['_id'] = str(document['_id'])
                tickets.append(document)
        except Exception as e:
            print(f"Error retrieving tickets from MongoDB: {e}")

        return tickets
