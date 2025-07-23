# Lead Generation Agent - Complete Technical Plan

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Data Flow](#data-flow)
4. [Database Design](#database-design)
5. [Implementation Plan](#implementation-plan)
6. [Day 1 Requirements (MVP)](#day-1-requirements-mvp)
7. [Week 2-4 Enhancements](#week-2-4-enhancements)
8. [Week 5+ Advanced Features](#week-5-advanced-features)
9. [Timeline](#timeline)

---

## System Overview

A distributed lead generation system that processes natural language queries, converts them to CoreSignal API calls, and efficiently manages data retrieval with asynchronous processing and Kafka-based message queuing.

### Key Features
- Natural language to DSL query conversion using LangGraph
- Asynchronous processing with Kafka
- Efficient API credit management
- Multi-level caching strategy
- Real-time and batch processing capabilities

---

## Architecture

### High-Level Architecture Diagram

```
┌─────────────────────┐
│   API Gateway       │
│   (REST/GraphQL)    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐     ┌─────────────────────┐
│   Request Handler   │────▶│   LangGraph Agent   │
│   Service           │     │   (Query Parser)    │
└──────────┬──────────┘     └─────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────┐
│                 Kafka Topics                     │
│  ┌─────────────┐  ┌──────────────┐  ┌────────┐ │
│  │search-tasks │  │collect-tasks │  │api-dump│ │
│  └─────────────┘  └──────────────┘  └────────┘ │
└─────────────────────────────────────────────────┘
           │              │              │
           ▼              ▼              ▼
┌─────────────────┐ ┌──────────────┐ ┌──────────┐
│ Search Worker   │ │Collect Worker│ │Dump Worker│
│ Service         │ │Service       │ │Service    │
└────────┬────────┘ └──────┬───────┘ └────┬─────┘
         │                 │              │
         └─────────────────┴──────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   MongoDB    │
                    └──────────────┘
```

### Component Details

#### 1. API Gateway
- RESTful endpoints for client interactions
- Authentication and rate limiting
- Request validation
- Async response handling

#### 2. LangGraph Query Parser
- Natural language understanding
- Entity extraction
- DSL query generation
- Query optimization

#### 3. Kafka Message Queue
- **search-tasks**: Search requests
- **collect-tasks**: Company collection jobs
- **api-dump**: Raw API responses

#### 4. Worker Services
- **Search Worker**: Executes CoreSignal searches
- **Collect Worker**: Fetches company details
- **Dump Worker**: Stores raw API responses

#### 5. Data Stores
- **MongoDB**: Primary database for all collections
- **Redis**: Caching and distributed locking

---

## Data Flow

### Search Flow Sequence

```
1. User Input → API Endpoint
   └─> Generate search_id (UUID)
   └─> Create tracking record
   └─> Return search_id to user

2. Query Processing
   └─> LangGraph converts to DSL
   └─> Publish to search-tasks topic
   └─> Update status to "queued"

3. Search Execution
   └─> Search Worker consumes task
   └─> Check cache first
   └─> Call CoreSignal Search API if needed
   └─> Store API dump

4. Company Collection
   └─> Identify new companies needed
   └─> Publish to collect-tasks
   └─> Update tracking with found count

5. Collection Processing
   └─> Collect Worker fetches details
   └─> Store in companies collection
   └─> Update all related search_tracking

6. Result Delivery
   └─> Client polls/streams results
   └─> Paginated response
   └─> Real-time updates via WebSocket
```

### Task Tracking Strategy

Each search request is tracked through its lifecycle:
- **search_id**: Unique identifier returned to user
- **Status progression**: queued → searching → collecting → completed
- **Progressive results**: Available data returned as it's collected

---

## Database Design

### MongoDB Collections

#### 1. companies Collection
```javascript
{
  _id: 9073671,  // CoreSignal company ID
  company_name: "Apple Inc.",
  search_keywords: ["apple", "tech", "california", "cupertino"],
  data: {
    // Full CoreSignal response data
  },
  metadata: {
    fetched_at: ISODate("2024-01-15T10:30:00Z"),
    last_updated: ISODate("2024-01-15T10:30:00Z"),
    update_frequency: "monthly",
    data_completeness: 0.95
  },
  search_history: [
    {
      query: "tech companies in California",
      timestamp: ISODate("2024-01-15T10:30:00Z")
    }
  ]
}
```

#### 2. api_dumps Collection
```javascript
{
  _id: ObjectId(),
  api_endpoint: "company_multi_source/collect",
  request: {
    company_id: 9073671,
    timestamp: ISODate("2024-01-15T10:30:00Z"),
    headers: { /* sanitized headers */ }
  },
  response: {
    status_code: 200,
    data: { /* Complete raw response */ },
    credits_used: 1
  },
  processing_status: "completed",
  processed_at: ISODate("2024-01-15T10:30:05Z")
}
```

#### 3. search_tracking Collection
```javascript
{
  _id: "search_id_uuid",
  user_id: "user_123",
  query: {
    natural: "AI companies in SF",
    dsl: { /* parsed DSL */ },
    normalized_hash: "query_fingerprint"
  },
  status: "collecting", // queued → searching → collecting → completed
  timestamps: {
    created: ISODate(),
    search_started: ISODate(),
    search_completed: ISODate(),
    collection_started: ISODate(),
    completed: ISODate()
  },
  results: {
    total_found: 150,
    cached_count: 50,
    new_count: 100,
    collected_count: 75,
    pending_count: 25,
    failed_count: 0
  },
  company_ids: [123, 456, 789...],
  errors: []
}
```

#### 4. search_cache Collection
```javascript
{
  _id: "5f4dcc3b5aa765d61d8327deb882cf99",  // MD5 of DSL query
  natural_query: "Find AI companies in San Francisco with 50+ employees",
  dsl_query: {
    "query": {
      "bool": {
        "must": [
          { "match": { "industry": "artificial intelligence" }},
          { "match": { "hq_city": "San Francisco" }},
          { "range": { "employees_count": { "gte": 50 }}}
        ]
      }
    }
  },
  company_ids: [123, 456, 789],
  result_count: 3,
  created_at: ISODate("2024-01-15T10:30:00Z"),
  expire_at: ISODate("2024-01-22T10:30:00Z"),  // TTL
  hit_count: 5
}
```

#### 5. api_usage Collection
```javascript
{
  _id: ObjectId(),
  date: ISODate("2024-01-15T00:00:00Z"),
  hour: 10,
  user_id: "user_123",  // Optional for multi-tenant
  endpoints: {
    search: {
      calls: 15,
      credits: 15,
      errors: 0
    },
    collect: {
      calls: 45,
      credits: 45,
      errors: 2
    }
  },
  total_credits: 60,
  credit_limit: 1000
}
```

### Kafka Topic Design

#### search-tasks Topic
```json
{
  "key": "search_id",
  "value": {
    "search_id": "uuid",
    "user_id": "user_123",
    "dsl_query": {},
    "priority": "normal",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

#### collect-tasks Topic
```json
{
  "key": "company_id",
  "value": {
    "company_id": 9073671,
    "search_ids": ["uuid1", "uuid2"],
    "priority": "normal",
    "retry_count": 0
  }
}
```

#### api-dump Topic
```json
{
  "key": "request_id",
  "value": {
    "request_id": "uuid",
    "api_type": "search|collect",
    "request_data": {},
    "response_data": {},
    "credits_used": 1,
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

---

## Implementation Plan

### Technology Stack

#### Core Technologies
- **Backend**: Python 3.11+ with FastAPI
- **Message Queue**: Apache Kafka 3.0+
- **Database**: MongoDB 6.0+
- **Cache**: Redis 7.0+
- **AI/ML**: LangGraph, LangChain

#### Infrastructure
- **Container**: Docker & Docker Compose
- **Orchestration**: Kubernetes (future)
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack

---

## Day 1 Requirements (MVP) 🚀

### 1. Core API Endpoints ✅
```
POST /api/v1/search
GET /api/v1/search/{search_id}/status
GET /api/v1/search/{search_id}/results
```

### 2. Basic LangGraph Integration ✅
- Simple query parser
- Support basic filters (name, location, industry)
- Direct DSL conversion

### 3. Kafka Topics Setup ✅
- search-tasks (3 partitions)
- collect-tasks (3 partitions)
- api-dump (1 partition)

### 4. Essential Workers ✅
- **Search Worker**: Basic search execution
- **Collect Worker**: Sequential collection
- **API Dump Worker**: Raw storage only

### 5. MongoDB Collections (Minimal) ✅
- search_tracking (basic schema)
- companies (raw data storage)
- api_dumps (audit trail)

### 6. Basic Features ✅
- Simple error handling
- Basic retry (3 attempts)
- Manual credit tracking
- Console logging

---

## Week 2-4 Enhancements 📈

### 1. Caching System 🔄
- Search result caching
- Company data caching
- Cache invalidation logic
- TTL implementation

### 2. Advanced Query Parsing 🔄
- Complex filter support
- Entity extraction
- Query optimization
- Fuzzy matching

### 3. Performance Optimizations 🔄
- Batch collection
- Connection pooling
- Parallel processing
- Queue prioritization

### 4. Monitoring & Analytics 🔄
- Kafka lag monitoring
- API credit dashboard
- Performance metrics
- Error tracking

### 5. Enhanced Features 🔄
- WebSocket support
- Real-time updates
- Deduplication system
- Advanced error recovery

---

## Week 5+ Advanced Features 🚀

### 1. Smart Features 🔮
- Predictive caching
- ML-based query understanding
- Auto-complete suggestions
- Result ranking

### 2. Enterprise Features 🔮
- Multi-tenancy
- Role-based access
- Usage analytics
- Billing integration

### 3. Data Pipeline 🔮
- Data enrichment
- Change detection
- Historical tracking
- Quality scoring

### 4. Advanced Search 🔮
- Saved searches
- Search templates
- Bulk operations
- Export functionality

### 5. Scalability 🔮
- MongoDB sharding
- Kafka optimization
- Horizontal scaling
- Load balancing

---

## Timeline

### Week 1: MVP Launch
| Day | Tasks |
|-----|-------|
| 1-2 | Infrastructure setup (MongoDB, Kafka, Redis) |
| 3-4 | Core workers and API implementation |
| 5   | Integration testing |
| 6-7 | Deployment and monitoring |

### Week 2-3: Stabilization
- Bug fixes from production
- Performance monitoring
- Basic optimizations
- Documentation

### Week 4: Enhancement Phase 1
- Caching implementation
- Batch processing
- Monitoring dashboard
- WebSocket support

### Week 5-6: Enhancement Phase 2
- Advanced query parsing
- Multi-tenancy basics
- Analytics implementation
- API v2 planning

### Week 7-8: Scale & Optimize
- Performance tuning
- Advanced features
- SDK development
- ML integration planning

---

## Risk Management

### Technical Risks
1. **API Rate Limits**
   - Mitigation: Conservative limits, circuit breakers
2. **Data Volume**
   - Mitigation: Pagination, streaming responses
3. **Query Complexity**
   - Mitigation: Query validation, complexity limits

### Operational Risks
1. **Credit Overuse**
   - Mitigation: Daily limits, alerts
2. **System Overload**
   - Mitigation: Queue management, backpressure
3. **Data Consistency**
   - Mitigation: Idempotent operations, versioning

---

## Success Metrics

### Day 1 KPIs
- ✅ 100 successful searches
- ✅ < 1% error rate
- ✅ < 60s average completion
- ✅ Zero credit overages

### Week 4 KPIs
- 📊 1000+ daily searches
- 📊 50%+ cache hit rate
- 📊 < 30s average completion
- 📊 < 0.1% error rate

### Long-term Goals
- 🎯 10,000+ daily searches
- 🎯 80%+ cache hit rate
- 🎯 < 10s average completion
- 🎯 99.9% uptime

---

## Appendix

### API Examples

#### Search Request
```bash
POST /api/v1/search
{
  "query": "AI companies in San Francisco with more than 50 employees",
  "filters": {
    "min_employees": 50,
    "industries": ["artificial intelligence", "machine learning"]
  }
}

Response:
{
  "search_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "estimated_time": 30
}
```

#### Status Check
```bash
GET /api/v1/search/550e8400-e29b-41d4-a716-446655440000/status

Response:
{
  "search_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "collecting",
  "progress": {
    "total_found": 150,
    "collected": 75,
    "pending": 75
  }
}
```

### Configuration Examples

#### Kafka Configuration
```yaml
search-tasks:
  partitions: 10
  replication: 3
  retention.ms: 86400000  # 24 hours

collect-tasks:
  partitions: 20
  replication: 3
  retention.ms: 172800000  # 48 hours
```

#### MongoDB Indexes
```javascript
// Companies collection
db.companies.createIndex({ "company_name": 1 })
db.companies.createIndex({ "data.hq_country": 1, "data.industry": 1 })
db.companies.createIndex({ "metadata.fetched_at": 1 })

// Search tracking
db.search_tracking.createIndex({ "user_id": 1, "created_at": -1 })
db.search_tracking.createIndex({ "status": 1 })
```