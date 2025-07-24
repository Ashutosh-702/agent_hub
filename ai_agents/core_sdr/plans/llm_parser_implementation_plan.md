# LLM-Based Query Parser Implementation Plan

## Overview
Replace the current rule-based NL parser with an LLM-based approach for more accurate and flexible query parsing.

## Current State Analysis

### What We Have (Rule-Based)
- `EntityExtractor`: Regex patterns + JSON config lookups
- `DSLBuilder`: Hardcoded field mappings
- `QueryParser`: Orchestrates entity extraction → DSL building

### Limitations
- Rigid pattern matching
- Can't handle complex/ambiguous queries
- Requires manual config updates for new entities
- Poor handling of context and intent

## Proposed LLM Solution

### 1. LLM Integration Options

**Option A: OpenAI GPT (Recommended)**
- Models: GPT-4o-mini (cost-effective) or GPT-4o (high accuracy)
- Structured output with function calling
- JSON mode for consistent formatting
- ~$0.15/1M tokens (4o-mini)

**Option B: Anthropic Claude**
- Models: Claude-3.5-haiku (fast) or Claude-3.5-sonnet (accurate)
- Structured output capabilities
- Good at following instructions

**Option C: Local Models**
- Ollama + Llama 3.1/3.2
- No API costs, but requires local setup
- Lower accuracy, but private

### 2. Implementation Architecture

```
NL Query → LLM Parser → Structured Entities → DSL Builder → Elasticsearch Query
```

#### New Components

**`LLMQueryParser`** (replaces EntityExtractor)
- Sends query + schema to LLM
- Gets structured JSON response
- Handles retries and validation

**`EntityValidator`** 
- Validates LLM-extracted entities
- Fallback to rule-based for invalid responses

**`PromptTemplates`**
- System prompts for consistent parsing
- Few-shot examples
- Schema definitions

### 3. Detailed Changes Required

#### A. New Dependencies
```toml
# Add to pyproject.toml
openai = ">=1.12.0"
anthropic = ">=0.18.0"  # if using Claude
pydantic = ">=2.5.0"    # upgrade for better validation
```

#### B. New Files to Create
```
src/parsers/
├── llm_parser.py           # Main LLM parser
├── prompt_templates.py     # System prompts
├── entity_validator.py     # Validation logic
└── llm_clients/            # LLM API clients
    ├── __init__.py
    ├── openai_client.py
    └── anthropic_client.py
```

#### C. Files to Modify
```
src/parsers/
├── query_parser.py         # Update to use LLM parser
└── dsl_builder.py         # Minor updates for new entity format

src/core/
├── models.py              # Enhanced ParsedEntity model
└── orchestrator.py        # Add LLM config params

config/
└── llm_prompts.json       # Prompt templates and examples
```

#### D. Configuration Changes
```bash
# New environment variables
LLM_PROVIDER=openai                    # openai, anthropic, or local
OPENAI_API_KEY=sk-...                 # if using OpenAI
ANTHROPIC_API_KEY=sk-ant-...          # if using Anthropic
LLM_MODEL=gpt-4o-mini                 # model name
LLM_TEMPERATURE=0.1                   # low for consistency
LLM_MAX_TOKENS=1000                   # response limit
LLM_TIMEOUT=30                        # request timeout
```

### 4. Implementation Strategy

#### Phase 1: Basic LLM Integration
- Implement OpenAI client
- Create basic prompt template
- Replace entity extraction only
- Keep existing DSL builder

#### Phase 2: Enhanced Parsing
- Add few-shot examples
- Implement entity validation
- Add retry logic with exponential backoff
- Performance optimization

#### Phase 3: Advanced Features
- Support multiple LLM providers
- Context-aware parsing
- Query intent classification
- Confidence scoring

### 5. Prompt Engineering Strategy

#### System Prompt Template
```
You are a company search query parser. Extract structured entities from natural language queries.

Output valid JSON with these fields:
- location: {country, state, city}
- industry: [list of industries]
- technology: [list of technologies]
- employees: {min, max}
- revenue: {min, max}
- founded: {min, max}
- company_type: string
- is_public: boolean
- is_b2b: boolean

Examples:
Query: "AI startups in SF with 10+ employees"
Output: {
  "location": {"city": "san_francisco"},
  "industry": ["technology", "artificial_intelligence"],
  "employees": {"min": 10},
  "company_type": "startup"
}
```

#### Few-Shot Examples
- 5-10 diverse query examples
- Cover edge cases and ambiguity
- Include negative examples (what NOT to extract)

### 6. Benefits of LLM Approach

**Accuracy Improvements**
- Handles ambiguous queries: "tech companies" → technology industry
- Context understanding: "Bay Area" → San Francisco region
- Intent recognition: "hiring Python developers" → uses Python technology

**Flexibility**
- No need to update config files for new entities
- Handles complex compound queries
- Natural language variations

**Maintainability**
- Simpler codebase (remove complex regex patterns)
- Easy to extend with new entity types
- Centralized logic in prompts

### 7. Migration Strategy

#### Backward Compatibility
- Keep rule-based parser as fallback
- A/B testing capability
- Gradual rollout

#### Testing
- Benchmark against current parser
- Create test dataset with complex queries
- Monitor API costs and latency

### 8. Cost Estimation

**OpenAI GPT-4o-mini:**
- ~200 tokens per query (input + output)
- $0.15/1M tokens
- Cost per query: ~$0.00003 (0.003 cents)
- 1000 queries/day = $0.03/day = $10.95/year

**Very cost-effective for most use cases.**

### 9. Risks & Mitigations

**API Availability**
- Risk: LLM API downtime
- Mitigation: Fallback to rule-based parser

**Cost Control**
- Risk: Unexpected usage spikes
- Mitigation: Rate limiting, usage monitoring

**Response Quality**
- Risk: Inconsistent LLM responses
- Mitigation: Response validation, retries

**Latency**
- Risk: Slower than rule-based
- Mitigation: Caching, async processing

## Implementation Timeline

**Week 1:** Basic LLM client + prompt engineering
**Week 2:** Entity validation + integration
**Week 3:** Testing + optimization
**Week 4:** Documentation + deployment

## Approval Required

**Key Decisions:**
1. **LLM Provider**: OpenAI GPT-4o-mini (recommended) vs alternatives?
2. **Migration Strategy**: Immediate replacement vs gradual rollout?
3. **Fallback Strategy**: Keep rule-based parser as backup?
4. **Cost Budget**: Acceptable monthly LLM API costs?

**Next Steps After Approval:**
1. Implement basic LLM client
2. Create prompt templates with examples
3. Replace entity extractor
4. Add comprehensive testing

**Questions for Approval:**
- Are you comfortable with OpenAI API dependency?
- Should we support multiple LLM providers from the start?
- Any specific parsing requirements or edge cases to handle?