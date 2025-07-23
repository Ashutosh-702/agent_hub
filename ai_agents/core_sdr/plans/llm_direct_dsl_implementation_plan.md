# LLM Direct DSL Query Implementation Plan

## Overview
Replace the entire NL parsing pipeline (EntityExtractor + DSLBuilder) with a single LLM that directly outputs Elasticsearch DSL queries.

## Proposed Architecture

### Current Flow (3 Steps)
```
NL Query → EntityExtractor → DSLBuilder → Elasticsearch DSL
```

### New Flow (1 Step)
```
NL Query → LLM Direct DSL Generator → Elasticsearch DSL
```

**Key Benefits:**
- **Simpler**: Single step instead of 3
- **More Accurate**: High reasoning models understand complex queries better
- **Flexible**: No intermediate entity mapping needed
- **Maintainable**: One prompt instead of complex rule-based logic

## Implementation Strategy

### 1. LLM Model Selection

**Recommended: OpenAI GPT-4o** (High Reasoning)
- Best at complex structured output
- Excellent JSON generation
- Function calling capabilities
- Cost: ~$2.50/1M tokens (reasonable for accuracy gained)

**Alternative: Claude-3.5-Sonnet**
- Great reasoning capabilities
- Good at following complex instructions
- Cost: ~$3/1M tokens

### 2. Core Component

**`LLMDSLGenerator`** (replaces EntityExtractor + DSLBuilder)
```python
class LLMDSLGenerator:
    def generate_dsl(self, query: str, max_results: int = 20) -> Dict[str, Any]:
        """
        Convert natural language query directly to Elasticsearch DSL.
        
        Args:
            query: "AI startups in SF with 10+ employees"
            max_results: Maximum results to return
            
        Returns:
            Complete Elasticsearch DSL query dict
        """
```

### 3. Detailed Implementation

#### A. New Dependencies
```toml
# Add to pyproject.toml
openai = ">=1.12.0"
# OR
anthropic = ">=0.18.0"
```

#### B. Files to Create
```
src/parsers/
├── llm_dsl_generator.py    # Main LLM DSL generator
├── dsl_templates.py        # DSL examples and templates
└── llm_clients/            # LLM API clients
    ├── __init__.py
    ├── openai_client.py
    └── anthropic_client.py
```

#### C. Files to Replace/Remove
```
src/parsers/
├── entity_extractor.py    # DELETE - replaced by LLM
├── dsl_builder.py         # DELETE - replaced by LLM
└── query_parser.py        # SIMPLIFY - just call LLM

config/
├── industries.json        # DELETE - LLM knows industries
├── technologies.json      # DELETE - LLM knows technologies  
├── locations.json         # DELETE - LLM knows locations
└── query_mappings.json    # DELETE - LLM knows field mappings
```

#### D. Files to Modify
```
src/core/
├── orchestrator.py        # Update to use LLM DSL generator
└── models.py             # Remove ParsedEntity (not needed)
```

### 4. Prompt Engineering

#### System Prompt Template
```
You are an expert Elasticsearch DSL query generator for company search.

Convert natural language queries into valid Elasticsearch DSL queries.

COMPANY SCHEMA:
- company_name (text)
- industry (keyword)
- hq_country, hq_state, hq_city (keywords)
- employees_count (integer)
- founded_year (integer) 
- revenue_annual.source_1_annual_revenue.annual_revenue (long)
- is_public (boolean)
- is_b2b (boolean)
- type (keyword: startup, enterprise, sme)
- technologies_used.technology (nested array)
- website (keyword)

RULES:
1. Always return valid JSON
2. Use appropriate query types (match, term, range, nested)
3. Combine multiple conditions with bool/must
4. Use fuzzy matching for text fields
5. Handle numeric ranges properly
6. Include size and from fields

OUTPUT FORMAT:
{
  "query": { ... elasticsearch query ... },
  "size": 20,
  "from": 0
}
```

#### Few-Shot Examples
```json
INPUT: "AI startups in San Francisco with 10+ employees"
OUTPUT: {
  "query": {
    "bool": {
      "must": [
        {"match": {"industry": {"query": "technology artificial intelligence", "fuzziness": "AUTO"}}},
        {"term": {"type": "startup"}},
        {"term": {"hq_city": "san_francisco"}},
        {"range": {"employees_count": {"gte": 10}}}
      ]
    }
  },
  "size": 20,
  "from": 0
}

INPUT: "Public SaaS companies using AWS"
OUTPUT: {
  "query": {
    "bool": {
      "must": [
        {"match": {"industry": {"query": "software saas", "fuzziness": "AUTO"}}},
        {"term": {"is_public": true}},
        {"nested": {
          "path": "technologies_used",
          "query": {"match": {"technologies_used.technology": "aws"}}
        }}
      ]
    }
  },
  "size": 20,
  "from": 0
}
```

### 5. Implementation Details

#### A. Core LLM DSL Generator
```python
class LLMDSLGenerator:
    def __init__(self, llm_client, model="gpt-4o"):
        self.llm_client = llm_client
        self.model = model
        self.system_prompt = self._load_system_prompt()
        self.examples = self._load_examples()
    
    def generate_dsl(self, query: str, max_results: int = 20) -> Dict[str, Any]:
        prompt = self._build_prompt(query, max_results)
        response = self.llm_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1000,
            response_format={"type": "json_object"}
        )
        
        dsl = json.loads(response.choices[0].message.content)
        self._validate_dsl(dsl)
        return dsl
```

#### B. DSL Validation
```python
def _validate_dsl(self, dsl: Dict[str, Any]) -> None:
    """Validate LLM-generated DSL query"""
    required_fields = ["query", "size"]
    for field in required_fields:
        if field not in dsl:
            raise ValueError(f"Missing required field: {field}")
    
    # Additional validation logic
    if not isinstance(dsl["size"], int) or dsl["size"] <= 0:
        raise ValueError("Invalid size field")
```

### 6. Updated Query Parser
```python
class QueryParser:
    def __init__(self, llm_dsl_generator):
        self.llm_dsl_generator = llm_dsl_generator
    
    def parse_query(self, query: str, max_results: int = 20) -> DSLQuery:
        """Parse natural language query into DSL query using LLM"""
        dsl_dict = self.llm_dsl_generator.generate_dsl(query, max_results)
        return DSLQuery(**dsl_dict)
    
    def explain_parse(self, query: str) -> Dict[str, Any]:
        """Show what DSL would be generated for a query"""
        dsl_dict = self.llm_dsl_generator.generate_dsl(query)
        return {
            "original_query": query,
            "generated_dsl": dsl_dict,
            "interpretation": self._generate_interpretation(dsl_dict)
        }
```

### 7. Environment Configuration
```bash
# New environment variables
LLM_PROVIDER=openai                    # openai or anthropic
OPENAI_API_KEY=sk-...                 # if using OpenAI
ANTHROPIC_API_KEY=sk-ant-...          # if using Anthropic
LLM_MODEL=gpt-4o                      # high reasoning model
LLM_TEMPERATURE=0.1                   # low for consistency
LLM_MAX_TOKENS=1000                   # DSL response limit
LLM_TIMEOUT=30                        # request timeout
```

### 8. Benefits of Direct DSL Approach

**Simplicity**
- Remove 3 complex components (EntityExtractor, DSLBuilder, config JSONs)
- Single LLM call instead of multi-step pipeline
- Much less code to maintain

**Accuracy**
- High reasoning models understand query intent better
- No information loss between entity extraction and DSL building
- Handle complex, compound queries naturally

**Flexibility**
- Support any Elasticsearch query pattern
- Easy to extend with new query types
- No need to update configuration files

**Performance**
- Fewer components = fewer failure points
- Single API call instead of multiple processing steps
- Better caching opportunities

### 9. Migration Strategy

#### Phase 1: Core Implementation (Week 1)
- Implement `LLMDSLGenerator` with OpenAI
- Create comprehensive prompt with examples
- Basic DSL validation

#### Phase 2: Integration (Week 2)
- Replace query parser pipeline
- Remove old components and config files
- Update orchestrator

#### Phase 3: Testing & Optimization (Week 3)
- Comprehensive testing with complex queries
- Prompt optimization
- Error handling and retries

#### Phase 4: Deployment (Week 4)
- Documentation updates
- Performance monitoring
- Gradual rollout

### 10. Cost Analysis

**OpenAI GPT-4o:**
- Input: ~150 tokens (prompt + query)
- Output: ~300 tokens (DSL + reasoning)
- Total: ~450 tokens per query
- Cost: ~$0.001125 per query (0.1 cents)
- 1000 queries/day: ~$1.12/day = $410/year

**Still very reasonable for a high-reasoning model.**

### 11. Risk Mitigations

**Invalid DSL Output**
- Comprehensive validation
- Retry with corrective prompt
- Fallback to simple match_all query

**API Latency**
- Async processing for bulk queries
- Response caching for common queries
- Timeout handling

**Cost Control**
- Query rate limiting
- Usage monitoring and alerts
- Prompt optimization to reduce tokens

### 12. Testing Strategy

**DSL Quality Tests**
- Compare against manually crafted DSL queries
- Test complex query edge cases
- Validate Elasticsearch compatibility

**Performance Tests**
- Measure latency vs current system
- Load testing with concurrent requests
- Cost monitoring

## Approval Questions

1. **Model Choice**: OpenAI GPT-4o (recommended) or Claude-3.5-Sonnet?
2. **Cost Budget**: ~$400/year for 1000 queries/day acceptable?
3. **Migration**: Remove all config JSONs and rule-based logic immediately?
4. **Fallback**: Simple match_all query if LLM fails, or more complex fallback?
5. **Timeline**: 4-week implementation for direct DSL approach?

This approach is much cleaner and leverages the full power of high reasoning models!