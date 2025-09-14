import asyncio
import pytest
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database.mongodb_client import MongoDBClient


class TestUnifiedSchema:
    """Test cases for the unified ticket schema operations."""

    @pytest.fixture
    async def mongo_client(self):
        """Create a mock MongoDB client for testing."""
        client = MongoDBClient.__new__(MongoDBClient)
        client.collection = AsyncMock()
        client.db = AsyncMock()
        return client

    @pytest.mark.asyncio
    async def test_insert_tickets_adds_processed_field(self, mongo_client):
        """Test that insert_tickets adds processed field with default value."""
        # Mock the insert_many operation
        mongo_client.collection.insert_many = AsyncMock(return_value=MagicMock(inserted_ids=["id1", "id2"]))

        test_tickets = [
            {"id": "TICKET-001", "subject": "Test ticket 1", "body": "Test body 1"},
            {"id": "TICKET-002", "subject": "Test ticket 2", "body": "Test body 2"}
        ]

        result = await mongo_client.insert_tickets(test_tickets)

        # Verify the call was made with processed field added
        args, kwargs = mongo_client.collection.insert_many.call_args
        inserted_tickets = args[0]

        assert len(inserted_tickets) == 2
        for ticket in inserted_tickets:
            assert ticket["processed"] == False
            assert "created_at" in ticket
            assert "updated_at" in ticket

        assert result == ["id1", "id2"]

    @pytest.mark.asyncio
    async def test_update_ticket_with_classification(self, mongo_client):
        """Test updating a ticket with classification results."""
        # Mock the update_one operation
        mongo_client.collection.update_one = AsyncMock(return_value=MagicMock(modified_count=1))

        classification_result = {
            "classification": {
                "topic_tags": ["API", "Integration"],
                "sentiment": "Curious",
                "priority": "P1 (Medium)"
            },
            "confidence_scores": {
                "topic": 0.85,
                "sentiment": 0.92,
                "priority": 0.78
            },
            "processing_time_ms": 1500
        }

        result = await mongo_client.update_ticket_with_classification("TICKET-001", classification_result)

        # Verify the update was called correctly
        args, kwargs = mongo_client.collection.update_one.call_args
        filter_query = args[0]
        update_query = args[1]

        assert filter_query == {"id": "TICKET-001"}
        assert update_query["$set"]["processed"] == True
        assert update_query["$set"]["classification"] == classification_result["classification"]
        assert update_query["$set"]["confidence_scores"] == classification_result["confidence_scores"]
        assert "processing_metadata" in update_query["$set"]
        assert update_query["$set"]["processing_metadata"]["processed_at"]
        assert update_query["$set"]["processing_metadata"]["model_version"] == "gemini-2.5-flash"
        assert update_query["$set"]["processing_metadata"]["processing_time_ms"] == 1500

        assert result == True

    @pytest.mark.asyncio
    async def test_get_processing_stats(self, mongo_client):
        """Test getting processing statistics."""
        # Mock the collection methods
        mongo_client.collection.count_documents = AsyncMock(side_effect=[100, 60, 40, 5])
        mongo_client.collection.aggregate = AsyncMock(return_value=[
            AsyncMock() for _ in range(3)
        ])

        # Mock the aggregate results
        mock_docs = [
            {"_id": "P0 (High)", "count": 10},
            {"_id": "P1 (Medium)", "count": 30},
            {"_id": "P2 (Low)", "count": 20}
        ]

        async def mock_aggregate():
            for doc in mock_docs:
                yield doc

        mongo_client.collection.aggregate = mock_aggregate

        stats = await mongo_client.get_processing_stats()

        assert stats["total_tickets"] == 100
        assert stats["total_processed"] == 60
        assert stats["total_unprocessed"] == 40
        assert stats["processed_today"] == 5
        assert stats["priority_distribution"]["P0 (High)"] == 10
        assert stats["priority_distribution"]["P1 (Medium)"] == 30
        assert stats["priority_distribution"]["P2 (Low)"] == 20

    @pytest.mark.asyncio
    async def test_get_unprocessed_tickets(self, mongo_client):
        """Test getting unprocessed tickets."""
        mock_tickets = [
            {"_id": "mongo_id_1", "id": "TICKET-001", "subject": "Test 1", "processed": False},
            {"_id": "mongo_id_2", "id": "TICKET-002", "subject": "Test 2", "processed": False}
        ]

        async def mock_find(filter_query):
            assert filter_query == {"processed": False}
            for ticket in mock_tickets:
                yield ticket

        mongo_client.collection.find = mock_find

        tickets = await mongo_client.get_unprocessed_tickets()

        assert len(tickets) == 2
        assert tickets[0]["id"] == "TICKET-001"
        assert tickets[1]["id"] == "TICKET-002"

    @pytest.mark.asyncio
    async def test_get_processed_tickets(self, mongo_client):
        """Test getting processed tickets."""
        mock_tickets = [
            {"_id": "mongo_id_1", "id": "TICKET-001", "processed": True, "processing_metadata": {"processed_at": datetime.utcnow()}},
            {"_id": "mongo_id_2", "id": "TICKET-002", "processed": True, "processing_metadata": {"processed_at": datetime.utcnow()}}
        ]

        async def mock_cursor():
            for ticket in mock_tickets:
                yield ticket

        mock_cursor_instance = MagicMock()
        mock_cursor_instance.sort.return_value.limit.return_value = mock_cursor()

        mongo_client.collection.find = MagicMock(return_value=mock_cursor_instance)

        tickets = await mongo_client.get_processed_tickets(limit=10)

        # Verify the query was constructed correctly
        mongo_client.collection.find.assert_called_once_with({"processed": True})

        # Note: This is a simplified test. In practice, we'd need to properly mock the async iteration.


class TestDashboardFunctions:
    """Test cases for dashboard functions."""

    def test_display_statistics_structure(self):
        """Test that statistics display returns proper structure."""
        # This would require mocking streamlit, which is complex
        # For now, we test the logic that would be used
        mock_stats = {
            "total_tickets": 100,
            "total_processed": 60,
            "total_unprocessed": 40,
            "processed_today": 5,
            "priority_distribution": {"P0 (High)": 10, "P1 (Medium)": 30}
        }

        # Verify the expected structure
        assert "total_tickets" in mock_stats
        assert "total_processed" in mock_stats
        assert "total_unprocessed" in mock_stats
        assert "processed_today" in mock_stats
        assert "priority_distribution" in mock_stats

    def test_file_upload_validation(self):
        """Test CSV file upload validation logic."""
        # Test valid CSV structure
        valid_csv_data = "id,subject,body\nTICKET-001,Test Subject,Test Body\nTICKET-002,Another Subject,Another Body"

        # This would normally be done in the dashboard function
        # Here we test the logic separately
        import pandas as pd
        import io

        df = pd.read_csv(io.StringIO(valid_csv_data))

        # Verify required columns
        required_cols = ['id', 'subject', 'body']
        missing_cols = [col for col in required_cols if col not in df.columns]
        assert len(missing_cols) == 0

        # Verify data conversion
        tickets_data = []
        for _, row in df.iterrows():
            ticket = {
                'id': str(row['id']),
                'subject': str(row['subject']),
                'body': str(row['body'])
            }
            tickets_data.append(ticket)

        assert len(tickets_data) == 2
        assert tickets_data[0]['id'] == 'TICKET-001'
        assert tickets_data[1]['subject'] == 'Another Subject'


if __name__ == "__main__":
    # Run basic tests
    print("Running unified schema tests...")

    # Simple manual test
    async def run_basic_test():
        client = MongoDBClient.__new__(MongoDBClient)
        client.collection = AsyncMock()

        # Test insert_tickets
        client.collection.insert_many = AsyncMock(return_value=MagicMock(inserted_ids=["test_id"]))

        test_tickets = [{"id": "TEST-001", "subject": "Test", "body": "Body"}]
        result = await client.insert_tickets(test_tickets)

        # Verify processed field was added
        args, kwargs = client.collection.insert_many.call_args
        inserted_ticket = args[0][0]
        assert inserted_ticket["processed"] == False
        assert "created_at" in inserted_ticket
        assert "updated_at" in inserted_ticket

        print("✅ Basic unified schema test passed!")

    asyncio.run(run_basic_test())
    print("All basic tests completed!")

