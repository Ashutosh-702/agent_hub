# Lead Generation Prototype - Implementation Plan

## Step 1: User Input (CLI/API)

**Input Sources:**
- CLI: Command line arguments or interactive prompt
- API: HTTP POST request with JSON payload

**Expected Data:**
```json
{
  "query": "Public SaaS companies in California with 100+ employees using AWS",
  "max_results": 20,
  "timeout": 30,
  "output_format": "json"
}
```

---

## Step 2: Input Validation

**Validations:**
- Query: 3-500 chars, no injection patterns
- max_results: 1-100, default 20
- timeout: 5-300 seconds, default 30
- output_format: json|csv|summary

---

## Step 3: Cache Check (Optional)

**Cache Key:** MD5 hash of normalized query + parameters

**Cache Logic:**
- Check memory → file → MongoDB
- Return if found and not expired (24hr TTL)

---

## Step 4: Query Parsing (NL → DSL)

**Parser Components:**

**Entity Extractor:**
- Location detector (countries, cities, states)
- Number extractor (employees, revenue, year)
- Technology matcher (from known tech list)
- Industry classifier
- Boolean flags (public/private, B2B)

**Field Mappings Config:**
```json
{
  "location_fields": {
    "country": "hq_country",
    "city": "hq_city",
    "state": "hq_state"
  },
  "range_fields": {
    "employees": "employees_count",
    "revenue": "revenue_annual.source_1_annual_revenue.annual_revenue",
    "founded": "founded_year",
    "followers": "followers_count_linkedin"
  },
  "exact_fields": {
    "technology": "technologies_used.technology",
    "public": "is_public",
    "b2b": "is_b2b",
    "type": "type"
  }
}
```

**DSL Builder:**
```json
{
  "query": {
    "bool": {
      "must": [],     // AND conditions
      "should": [],   // OR conditions
      "filter": []    // Exact matches, ranges
    }
  },
  "size": 20,
  "from": 0
}
```

**Example Parse:**
Input: "AI startups in NYC founded after 2020 with 10-50 employees"
- Location: NYC → hq_city
- Industry: AI → industry
- Type: startups → type
- Founded: after 2020 → range query
- Employees: 10-50 → range query

---

## Step 5: CoreSignal Search API

**Request:**
- Method: POST
- URL: `/company_multi_source/search/es_dsl`
- Body: Generated DSL query
- Headers: API key

**Response:** Array of company IDs

---

## Step 6: Process Search Results

**Processing:**
- Extract company IDs
- Limit to max_results
- Track total found vs returned

---

## Step 7: Company Collection

**Batch Strategy:**
- Check existing companies in DB
- Group new IDs in batches of 10
- Parallel fetch using ThreadPoolExecutor

**Per Company:**
- GET `/company_multi_source/collect/{id}`
- Store full response
- Track credits used

---

## Step 8: Format Results

**Field Selection by Format:**

**JSON:** Full response

**CSV:** Key fields only
- company_name, industry, hq_location
- employees_count, founded_year
- website, technologies (top 5)

**Summary:** Name + industry + location

---

## Step 9: Update Caches

Store:
- Original query
- DSL query
- Results
- Timestamp
- Credits used

---

## Step 10: Return to User

**Response Structure:**
```json
{
  "search_id": "uuid",
  "query": {
    "original": "user input",
    "parsed_entities": {
      "location": "California",
      "industry": "SaaS",
      "min_employees": 100
    },
    "dsl": { /* generated query */ }
  },
  "results": {
    "total_found": 45,
    "returned": 20,
    "companies": [...]
  },
  "metadata": {
    "credits_used": 21,
    "processing_time": 12.5,
    "cached": false
  }
}
```

---

## Configuration Files

**query_mappings.json:** Field mappings and patterns
**industries.json:** Industry keywords and synonyms  
**technologies.json:** Technology name variations
**locations.json:** City/state/country mappings

---

## Error Handling

Each step wrapped in try-except with:
- Specific error types
- Partial result support
- User-friendly messages
- Full logging