import os
import motor.motor_asyncio
from typing import List, Dict, Optional, Union
from datetime import datetime

class MongoDBClient:
    """
    An asynchronous client for interacting with a MongoDB database.
    Uses a unified ticket collection with embedded processing data.
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
        Adds processed field with default value of false.

        Args:
            tickets_data: A list of dictionaries, where each dictionary represents a ticket.

        Returns:
            A list of string representations of the inserted document IDs, or None if insertion fails.
        """
        if self.collection is None:
            print("Error: MongoDB connection not established. Call connect() first.")
            return None
        try:
            # Add required fields to each ticket
            for ticket in tickets_data:
                ticket.setdefault('processed', False)
                ticket.setdefault('status', 'unprocessed')
                ticket.setdefault('created_at', datetime.utcnow())
                ticket.setdefault('updated_at', datetime.utcnow())

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

    async def update_ticket_with_classification(self, ticket_id: str, classification_result: Dict) -> bool:
        """
        Updates a ticket in the unified collection with classification results.
        Sets processed=true and embeds classification data.

        Args:
            ticket_id: The ticket ID to update
            classification_result: The classification results from the AI agent

        Returns:
            True if update was successful, False otherwise.
        """
        if self.collection is None:
            print("Error: MongoDB connection not established. Call connect() first.")
            return False

        try:
            # Prepare update data
            update_data = {
                "processed": True,
                "status": "processed",  # Set status to processed when classification is done
                "classification": classification_result.get("classification", {}),
                "confidence_scores": classification_result.get("confidence_scores", {}),
                "processing_metadata": {
                    "processed_at": datetime.utcnow(),
                    "model_version": "gemini-2.5-flash",
                    "processing_time_ms": classification_result.get("processing_time_ms", 0),
                    "agent_version": "1.0"
                },
                "updated_at": datetime.utcnow()
            }

            # Update the ticket
            result = await self.collection.update_one(
                {"id": ticket_id},
                {"$set": update_data}
            )

            success = result.modified_count > 0
            if success:
                print(f"✅ Successfully updated ticket with classification: {ticket_id}")
            else:
                print(f"⚠️  No ticket found with ID: {ticket_id}")
            return success

        except Exception as e:
            print(f"❌ Error updating ticket {ticket_id}: {e}")
            return False

    async def get_processed_tickets(self, limit: int = 100) -> List[Dict]:
        """
        Retrieves processed tickets from the unified collection.

        Args:
            limit: Maximum number of tickets to retrieve

        Returns:
            A list of processed ticket documents.
        """
        if self.collection is None:
            print("Error: MongoDB connection not established. Call connect() first.")
            return []

        tickets = []
        try:
            cursor = self.collection.find({"processed": True}).sort("processing_metadata.processed_at", -1).limit(limit)
            async for document in cursor:
                document['_id'] = str(document['_id'])
                tickets.append(document)
        except Exception as e:
            print(f"Error retrieving processed tickets from MongoDB: {e}")

        return tickets

    async def get_processed_ticket_by_id(self, ticket_id: str) -> Optional[Dict]:
        """
        Retrieves a specific processed ticket by its ticket_id.

        Args:
            ticket_id: The ticket ID to search for

        Returns:
            The processed ticket document, or None if not found.
        """
        if self.collection is None:
            print("Error: MongoDB connection not established. Call connect() first.")
            return None

        try:
            ticket = await self.collection.find_one({"id": ticket_id, "processed": True})
            if ticket:
                ticket['_id'] = str(ticket['_id'])
            return ticket
        except Exception as e:
            print(f"Error retrieving processed ticket {ticket_id}: {e}")
            return None

    async def update_processed_ticket(self, ticket_id: str, updates: Dict) -> bool:
        """
        Updates a processed ticket with additional information.

        Args:
            ticket_id: The ticket ID to update
            updates: Dictionary of fields to update

        Returns:
            True if update was successful, False otherwise.
        """
        if self.collection is None:
            print("Error: MongoDB connection not established. Call connect() first.")
            return False

        try:
            updates["updated_at"] = datetime.utcnow()
            result = await self.collection.update_one(
                {"id": ticket_id, "processed": True},
                {"$set": updates}
            )
            success = result.modified_count > 0
            if success:
                print(f"✅ Successfully updated processed ticket: {ticket_id}")
            else:
                print(f"⚠️  No processed ticket found with ID: {ticket_id}")
            return success
        except Exception as e:
            print(f"❌ Error updating processed ticket {ticket_id}: {e}")
            return False

    async def get_processing_stats(self) -> Dict[str, int]:
        """
        Gets statistics about tickets in the unified collection.

        Returns:
            Dictionary with processing statistics.
        """
        if self.collection is None:
            print("Error: MongoDB connection not established. Call connect() first.")
            return {}

        try:
            # Get total tickets count
            total_tickets = await self.collection.count_documents({})

            # Get status-based counts with correct logic
            # A ticket is unprocessed if status is "unprocessed"
            total_unprocessed = await self.collection.count_documents({"status": "unprocessed"})

            # A ticket is processed if processed=true AND status="processed"
            total_processed = await self.collection.count_documents({
                "processed": True,
                "status": "processed"
            })

            # A ticket is resolved if processed=true AND status="resolved"
            total_resolved = await self.collection.count_documents({
                "processed": True,
                "status": "resolved"
            })

            # Get processed today count (using processing_metadata.processed_at for backward compatibility)
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            processed_today = await self.collection.count_documents({
                "processing_metadata.processed_at": {"$gte": today}
            })

            # Get routed count (processed=true AND resolution.status="routed")
            routed_count = await self.collection.count_documents({
                "processed": True,
                "resolution.status": "routed"
            })

            # Get priority distribution for processed tickets
            pipeline = [
                {"$match": {"$or": [{"status": {"$in": ["processed", "resolved"]}}, {"processed": True}]}},
                {"$group": {"_id": "$classification.priority", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            priority_stats = {}
            async for doc in self.collection.aggregate(pipeline):
                priority_stats[doc["_id"] or "Unknown"] = doc["count"]

            return {
                "total_tickets": total_tickets,
                "total_processed": total_processed,
                "total_unprocessed": total_unprocessed,
                "total_resolved": total_resolved,
                "total_routed": routed_count,
                "processed_today": processed_today,
                "priority_distribution": priority_stats
            }
        except Exception as e:
            print(f"❌ Error getting processing stats: {e}")
            return {}

    async def get_unprocessed_tickets(self, limit: int = 1000) -> List[Dict]:
        """
        Retrieves unprocessed tickets from the unified collection.

        Args:
            limit: Maximum number of tickets to retrieve

        Returns:
            A list of unprocessed ticket documents.
        """
        if self.collection is None:
            print("Error: MongoDB connection not established. Call connect() first.")
            return []

        tickets = []
        try:
            cursor = self.collection.find({"processed": False}).limit(limit)
            async for document in cursor:
                document['_id'] = str(document['_id'])
                tickets.append(document)
        except Exception as e:
            print(f"Error retrieving unprocessed tickets from MongoDB: {e}")

        return tickets

    async def get_tickets_by_status(self, processed: bool, limit: int = 100) -> List[Dict]:
        """
        Retrieves tickets by processing status.

        Args:
            processed: True for processed tickets, False for unprocessed
            limit: Maximum number of tickets to retrieve

        Returns:
            A list of ticket documents.
        """
        if self.collection is None:
            print("Error: MongoDB connection not established. Call connect() first.")
            return []

        tickets = []
        try:
            cursor = self.collection.find({"processed": processed}).limit(limit)
            async for document in cursor:
                document['_id'] = str(document['_id'])
                tickets.append(document)
        except Exception as e:
            print(f"Error retrieving tickets from MongoDB: {e}")

        return tickets

    async def get_new_tickets_since(self, since_timestamp: datetime, limit: int = 100) -> List[Dict]:
        """
        Retrieves tickets created since a specific timestamp.
        Used for fetching "new" tickets since last fetch operation.

        Args:
            since_timestamp: Datetime to fetch tickets created after
            limit: Maximum number of tickets to retrieve

        Returns:
            A list of ticket documents created since the timestamp.
        """
        if self.collection is None:
            print("Error: MongoDB connection not established. Call connect() first.")
            return []

        tickets = []
        try:
            cursor = self.collection.find(
                {"created_at": {"$gt": since_timestamp}}
            ).sort("created_at", -1).limit(limit)

            async for document in cursor:
                document['_id'] = str(document['_id'])
                tickets.append(document)
        except Exception as e:
            print(f"Error retrieving new tickets from MongoDB: {e}")

        return tickets

    async def get_tickets_with_advanced_filters(
        self,
        processed_status: Optional[bool] = None,
        priority_levels: Optional[List[str]] = None,
        sentiment_types: Optional[List[str]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        search_text: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Retrieves tickets with advanced filtering options.

        Args:
            processed_status: None for all, True for processed, False for unprocessed
            priority_levels: List of priority levels to filter by
            sentiment_types: List of sentiment types to filter by
            date_from: Start date filter
            date_to: End date filter
            search_text: Text to search in subject/body
            limit: Maximum number of tickets to retrieve

        Returns:
            A list of filtered ticket documents.
        """
        if self.collection is None:
            print("Error: MongoDB connection not established. Call connect() first.")
            return []

        # Build query filter
        query_filter = {}

        # Processed status filter
        if processed_status is not None:
            query_filter["processed"] = processed_status

        # Priority filter (only applies to processed tickets)
        if priority_levels and processed_status is not False:  # Allow if processed=True or None
            query_filter["classification.priority"] = {"$in": priority_levels}

        # Sentiment filter (only applies to processed tickets)
        if sentiment_types and processed_status is not False:  # Allow if processed=True or None
            query_filter["classification.sentiment"] = {"$in": sentiment_types}

        # Date range filter
        date_filter = {}
        if date_from:
            date_filter["$gte"] = date_from
        if date_to:
            date_filter["$lte"] = date_to
        if date_filter:
            query_filter["created_at"] = date_filter

        # Text search filter
        if search_text:
            query_filter["$or"] = [
                {"subject": {"$regex": search_text, "$options": "i"}},
                {"body": {"$regex": search_text, "$options": "i"}}
            ]

        tickets = []
        try:
            cursor = self.collection.find(query_filter).sort("created_at", -1).limit(limit)
            async for document in cursor:
                document['_id'] = str(document['_id'])
                tickets.append(document)
        except Exception as e:
            print(f"Error retrieving tickets with advanced filters: {e}")

        return tickets

    async def update_ticket_with_resolution(self, ticket_id: str, resolution_data: Dict) -> bool:
        """
        Updates a processed ticket with resolution data (RAG response or routing information).

        Args:
            ticket_id: The ticket ID to update
            resolution_data: Dictionary containing resolution information with the following structure:
                {
                    "status": "resolved" or "routed",
                    "response": "AI-generated response text" (for resolved status),
                    "sources": [{"url": "source_url", "snippet": "relevant_text"}] (for resolved status),
                    "generated_at": "timestamp",
                    "confidence": 0.85,
                    "routed_to": "team_name" (for routed status),
                    "routing_reason": "reason for routing" (for routed status)
                }

        Returns:
            True if update was successful, False otherwise
        """
        if self.collection is None:
            print("Error: MongoDB connection not established. Call connect() first.")
            return False

        try:
            # Add timestamp if not provided
            if 'generated_at' not in resolution_data:
                resolution_data['generated_at'] = datetime.now()

            # Update the ticket with resolution data
            status_update = "resolved" if resolution_data.get('status') == 'resolved' else "processed"
            update_result = await self.collection.update_one(
                {"id": ticket_id},
                {
                    "$set": {
                        "resolution": resolution_data,
                        "status": status_update,
                        "updated_at": datetime.now()
                    }
                }
            )

            if update_result.modified_count > 0:
                print(f"Successfully updated ticket {ticket_id} with resolution data")
                return True
            else:
                print(f"No ticket found with ID {ticket_id} or no changes made")
                return False

        except Exception as e:
            print(f"Error updating ticket {ticket_id} with resolution data: {e}")
            return False

    async def get_resolved_tickets(self, limit: int = 100) -> List[Dict]:
        """
        Retrieves tickets that have been resolved with RAG responses.

        Args:
            limit: Maximum number of tickets to retrieve

        Returns:
            List of resolved ticket documents
        """
        if self.collection is None:
            print("Error: MongoDB connection not established. Call connect() first.")
            return []

        tickets = []
        try:
            cursor = self.collection.find(
                {"processed": True, "resolution.status": "resolved"}
            ).sort("resolution.generated_at", -1).limit(limit)

            async for document in cursor:
                document['_id'] = str(document['_id'])
                tickets.append(document)
        except Exception as e:
            print(f"Error retrieving resolved tickets: {e}")

        return tickets

    async def get_routed_tickets(self, limit: int = 100) -> List[Dict]:
        """
        Retrieves tickets that have been routed to teams.

        Args:
            limit: Maximum number of tickets to retrieve

        Returns:
            List of routed ticket documents
        """
        if self.collection is None:
            print("Error: MongoDB connection not established. Call connect() first.")
            return []

        tickets = []
        try:
            cursor = self.collection.find(
                {"processed": True, "resolution.status": "routed"}
            ).sort("resolution.generated_at", -1).limit(limit)

            async for document in cursor:
                document['_id'] = str(document['_id'])
                tickets.append(document)
        except Exception as e:
            print(f"Error retrieving routed tickets: {e}")

        return tickets

    async def get_unprocessed_tickets_for_resolution(self, limit: int = 100) -> List[Dict]:
        """
        Retrieves processed tickets that haven't been resolved yet.

        Args:
            limit: Maximum number of tickets to retrieve

        Returns:
            List of processed tickets without resolution data
        """
        if self.collection is None:
            print("Error: MongoDB connection not established. Call connect() first.")
            return []

        tickets = []
        try:
            # Find processed tickets that don't have resolution data
            cursor = self.collection.find(
                {"processed": True, "resolution": {"$exists": False}}
            ).sort("created_at", -1).limit(limit)

            async for document in cursor:
                document['_id'] = str(document['_id'])
                tickets.append(document)
        except Exception as e:
            print(f"Error retrieving unprocessed tickets for resolution: {e}")

        return tickets
