# Processed Tickets Storage System

This document describes the MongoDB-based storage system for processed customer support tickets in the Atlan Customer Support Copilot.

## Overview

The unified ticket storage system provides comprehensive data management and advanced analytics capabilities for all customer support tickets. The system uses a single MongoDB collection to store both raw and processed tickets, with embedded classification data and rich metadata for complete audit trails and analytical insights.

## Architecture

### Unified Collection Structure

The system uses a single MongoDB collection with embedded processing data:

#### `tickets` Collection (Unified Tickets)
- Stores all customer support tickets in a single collection
- Contains original ticket data and embedded processing results
- Uses a `processed` boolean field to distinguish between raw and classified tickets
- When `processed=true`, classification metadata, confidence scores, and processing history are embedded in the same document
- Supports advanced querying and analytics for both processed and unprocessed tickets

## Data Schema

### Unified Ticket Document Structure

#### Raw Ticket (processed: false)
```json
{
  "_id": "ObjectId('68c51177935550a5f53c38e6')",
  "id": "TICKET-246",
  "subject": "Which connectors automatically capture lineage?",
  "body": "Full ticket content...",
  "processed": false,
  "created_at": "2025-09-13T06:38:47.513000",
  "updated_at": "2025-09-13T06:38:47.513000"
}
```

#### Processed Ticket (processed: true)
```json
{
  "_id": "ObjectId('68c51177935550a5f53c38e6')",
  "id": "TICKET-246",
  "subject": "Which connectors automatically capture lineage?",
  "body": "Full ticket content...",
  "processed": true,
  "classification": {
    "topic_tags": ["Connector", "How-to"],
    "sentiment": "Curious",
    "priority": "P1 (Medium)"
  },
  "confidence_scores": {
    "topic": 0.85,
    "sentiment": 0.92,
    "priority": 0.78
  },
  "processing_metadata": {
    "processed_at": "2025-09-13T06:38:47.513000",
    "model_version": "gemini-1.5-flash",
    "processing_time_ms": 1500,
    "agent_version": "1.0"
  },
  "created_at": "2025-09-13T06:38:47.513000",
  "updated_at": "2025-09-13T06:38:47.513000"
}
```

### Field Descriptions

#### Core Fields
- **`id`**: Unique identifier for the ticket (used for deduplication)
- **`subject`**: Ticket subject line
- **`body`**: Full ticket content
- **`processed`**: Boolean flag indicating if ticket has been processed by AI (false = raw ticket, true = classified ticket)
- **`created_at`**: Timestamp when ticket was first created/inserted
- **`updated_at`**: Timestamp when ticket was last modified

#### Classification Results (only present when processed=true)
- **`classification.topic_tags`**: Array of relevant topic categories
- **`classification.sentiment`**: Detected user sentiment (Frustrated, Curious, Angry, Neutral)
- **`classification.priority`**: Assigned priority level (P0 High, P1 Medium, P2 Low)

#### Confidence Scores (only present when processed=true)
- **`confidence_scores.topic`**: Confidence in topic classification (0.0-1.0)
- **`confidence_scores.sentiment`**: Confidence in sentiment analysis (0.0-1.0)
- **`confidence_scores.priority`**: Confidence in priority assignment (0.0-1.0)

#### Processing Metadata (only present when processed=true)
- **`processing_metadata.processed_at`**: Timestamp when ticket was processed
- **`processing_metadata.model_version`**: AI model used for classification
- **`processing_metadata.processing_time_ms`**: Time taken to process the ticket
- **`processing_metadata.agent_version`**: Version of the classification agent

## Storage Workflow

### Manual Processing Pipeline

1. **Ticket Loading**: Raw tickets are loaded from the unified `tickets` collection (where `processed=false`)
2. **AI Classification**: Tickets are processed through the ClassificationAgent when user clicks "Process Tickets"
3. **In-Place Updates**: Tickets are updated in the same collection with `processed=true` and embedded classification data
4. **Metadata Enrichment**: Processing metadata and timestamps are added to existing documents
5. **Analytics Update**: Statistics are updated for dashboard display

### Storage Triggers

Tickets are processed and updated when:
- **Manual Processing**: User clicks "Process Tickets" button in the dashboard
- **File Upload**: New tickets uploaded via CSV/JSON are initially stored with `processed=false`
- **Future API Integration**: External systems can add tickets that will be processed on demand

## Database Operations

### Core Methods

#### `insert_tickets(tickets_data)`
Inserts new tickets with processed=false.

**Parameters:**
- `tickets_data`: List of ticket dictionaries

**Returns:** List of inserted document IDs

#### `update_ticket_with_classification(ticket_id, classification_result)`
Updates a ticket in-place with classification results.

**Parameters:**
- `ticket_id`: The ticket ID to update
- `classification_result`: Dict containing AI classification results

**Returns:** True if update was successful

#### `get_unprocessed_tickets()`
Retrieves all tickets where processed=false.

**Returns:** List of unprocessed ticket documents

#### `get_processed_tickets(limit=100)`
Retrieves processed tickets (processed=true) with optional pagination.

**Parameters:**
- `limit`: Maximum number of tickets to retrieve (default: 100)

**Returns:** List of processed ticket documents

#### `get_tickets_by_status(processed, limit=100)`
Retrieves tickets by processing status.

**Parameters:**
- `processed`: Boolean indicating processing status
- `limit`: Maximum number of tickets to retrieve

**Returns:** List of ticket documents

#### `get_processing_stats()`
Retrieves comprehensive processing statistics.

**Returns:** Dictionary containing:
- `total_tickets`: Total number of tickets
- `total_processed`: Total number of processed tickets
- `total_unprocessed`: Total number of unprocessed tickets
- `processed_today`: Number of tickets processed today
- `priority_distribution`: Count of processed tickets by priority level

## Analytics and Reporting

### Real-time Statistics

The system provides comprehensive real-time analytics including:

- **Total Tickets**: Cumulative count of all tickets in the system
- **Total Processed**: Count of tickets that have been AI-classified
- **Total Unprocessed**: Count of tickets awaiting processing
- **Daily Processing**: Number of tickets processed in the current day
- **Priority Distribution**: Breakdown of processed tickets by priority level
- **Processing Time**: Average time to process tickets
- **Model Performance**: Success rates and confidence score distributions

### Dashboard Features

#### Control Panel
- **Add Tickets Button**: Upload tickets from CSV/JSON files with validation and preview
- **Fetch New Tickets Button**: Multiple fetch modes (since last fetch, 24h, 7d, all unprocessed) with session state tracking
- **Process Tickets Button**: Advanced batch processing with multiple modes and options

#### Statistics Display
- **Metrics Cards**: Real-time counts for total, processed, unprocessed, and daily processing
- **Progress Indicators**: Visual progress bars for processing status
- **Percentage Displays**: Clear percentage breakdowns for quick understanding

#### System Analytics Overview
- **Key Metrics Dashboard**: Comprehensive metrics with trend indicators
- **Processing Status Visualization**: Interactive progress bars and status breakdowns
- **Priority Distribution Charts**: Bar charts showing P0, P1, P2 priority distributions
- **Sentiment Analysis Charts**: Bar charts showing customer sentiment distributions
- **Topic Analysis**: Horizontal bar charts showing most common topic tags
- **Time-based Trends**: Line charts showing ticket creation patterns over time
- **Manual Refresh**: Button to refresh analytics cache for real-time updates

#### All Tickets Tab
- **Comprehensive Overview**: View all tickets with processing status indicators
- **Advanced Filtering**: Multi-select filters for status, priority, and sentiment
- **Date Range Filtering**: Filter tickets by creation date ranges
- **Text Search**: Search across ticket subjects, bodies, and classification data
- **Real-time Filtering**: Apply filters dynamically with instant results
- **Analytics Integration**: Charts update based on filtered data

#### Processed Tickets History Tab
- **Detailed History**: Complete audit trail of processed tickets
- **Advanced Search**: Find tickets by ID, subject, or classification data
- **Export Capabilities**: Download processed tickets as CSV
- **Metadata Display**: Processing timestamps, model versions, confidence scores, and agent versions

## Indexing Strategy

### Database Indexes

The system automatically creates the following indexes for optimal performance:

```javascript
// Ticket ID index for fast lookups
db.tickets_processed.createIndex({ "ticket_id": 1 }, { unique: true })

// Processing timestamp index for time-based queries
db.tickets_processed.createIndex({ "processing_metadata.processed_at": -1 })

// Priority index for priority-based filtering
db.tickets_processed.createIndex({ "classification.priority": 1 })

// Topic tags index for tag-based searches
db.tickets_processed.createIndex({ "classification.topic_tags": 1 })
```

### Query Optimization

Indexes are designed to support common query patterns:
- **Ticket lookup by ID**: O(1) complexity
- **Time-based filtering**: Efficient range queries
- **Priority-based filtering**: Fast priority distribution queries
- **Topic-based searches**: Optimized tag-based filtering

## Error Handling and Reliability

### Duplicate Prevention
- **Unique Constraints**: Ticket IDs are enforced as unique in the database
- **Upsert Operations**: Update existing tickets if they already exist
- **Idempotent Processing**: Safe to reprocess the same ticket multiple times

### Error Recovery
- **Graceful Degradation**: System continues processing other tickets if one fails
- **Error Logging**: All processing errors are logged with context
- **Retry Logic**: Automatic retry for transient failures
- **Data Validation**: Input validation prevents malformed data storage

### Monitoring and Alerts
- **Processing Metrics**: Track success rates and error rates
- **Performance Monitoring**: Monitor processing times and throughput
- **Storage Alerts**: Notifications for storage capacity issues
- **Data Quality**: Automated checks for data consistency

## Security and Compliance

### Data Protection
- **PII Masking**: Sensitive information is automatically masked
- **Access Controls**: Role-based access to processed ticket data
- **Audit Logging**: All data access is logged for compliance
- **Encryption**: Data is encrypted at rest and in transit

### Compliance Features
- **Retention Policies**: Configurable data retention periods
- **Export Controls**: Secure data export capabilities
- **Access Logging**: Complete audit trail of data access
- **Data Anonymization**: Optional anonymization for analytics

## API Integration

### RESTful Endpoints

The processed tickets system provides RESTful API endpoints:

```
GET    /api/processed-tickets          # List processed tickets
GET    /api/processed-tickets/{id}     # Get specific ticket
GET    /api/processing-stats           # Get processing statistics
POST   /api/processed-tickets          # Store new processed ticket
PUT    /api/processed-tickets/{id}     # Update processed ticket
DELETE /api/processed-tickets/{id}     # Delete processed ticket
```

### Integration Examples

#### Python Client
```python
from mongodb_client import MongoDBClient

client = MongoDBClient()
await client.connect()

# Store processed ticket
ticket_id = await client.store_processed_ticket(ticket_data, classification_result)

# Get processing statistics
stats = await client.get_processing_stats()
print(f"Total processed: {stats['total_processed']}")
```

#### Dashboard Integration
```python
# Get recent processed tickets
recent_tickets = await mongo_client.get_processed_tickets(limit=50)

# Display in dashboard
for ticket in recent_tickets:
    st.write(f"Ticket {ticket['ticket_id']}: {ticket['classification']['priority']}")
```

## Performance Considerations

### Scalability
- **Horizontal Scaling**: Database can be scaled horizontally
- **Batch Processing**: Efficient bulk operations for large datasets
- **Caching Layer**: Redis integration for frequently accessed data
- **Async Operations**: Non-blocking database operations

### Optimization Techniques
- **Connection Pooling**: Reused database connections
- **Query Optimization**: Efficient index usage
- **Batch Writes**: Group multiple writes into single operations
- **Memory Management**: Controlled memory usage for large datasets

## Future Enhancements

### Planned Features
- **Advanced Analytics**: Machine learning insights from processed tickets
- **Real-time Dashboards**: Live processing metrics and alerts
- **Automated Reporting**: Scheduled report generation
- **Integration APIs**: Third-party system integrations
- **Data Archiving**: Long-term storage and archival strategies

### Performance Improvements
- **Query Caching**: Cache frequently accessed data
- **Background Processing**: Async processing for improved UX
- **Distributed Processing**: Multi-node processing capabilities
- **Advanced Indexing**: Specialized indexes for complex queries

This processed tickets storage system provides a robust, scalable foundation for managing AI-classified customer support tickets with comprehensive analytics and reporting capabilities.
