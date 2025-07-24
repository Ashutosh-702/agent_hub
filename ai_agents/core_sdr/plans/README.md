# Implementation Plans

This directory contains detailed implementation plans and architectural decisions for the lead generation system.

## Plans

### 1. `prototype_plan.md`
Original 10-step implementation plan for the rule-based system.
- **Status**: ✅ Completed
- **Approach**: Rule-based NL parsing with JSON configurations

### 2. `llm_parser_implementation_plan.md`  
Plan to replace rule-based NL parser with LLM-based approach (entity extraction).
- **Status**: 📋 Superseded
- **Approach**: OpenAI/Claude integration for entity extraction

### 3. `llm_direct_dsl_implementation_plan.md`
**CURRENT PLAN** - LLM directly generates Elasticsearch DSL queries.
- **Status**: 📋 Pending Approval  
- **Approach**: High reasoning model (GPT-4o) directly outputs DSL
- **Benefits**: Much simpler, more accurate, eliminates entire pipeline

## Future Plans

- **Vector Search Integration**: Use embeddings for company similarity search
- **Multi-Language Support**: Parse queries in multiple languages
- **Real-time Data Pipeline**: Stream updates from CoreSignal API
- **Advanced Analytics**: Query pattern analysis and optimization