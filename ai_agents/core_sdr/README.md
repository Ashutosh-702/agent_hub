# Lead Generation System

Natural language to company search using CoreSignal API.

## Quick Start

### Prerequisites
- Python 3.8+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- CoreSignal API key
- MongoDB (optional, for caching)

### Installation & Usage

```bash
# Install uv (much faster than pip)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and install
git clone <repo>
cd core_sdr
uv pip install -e .

# Configure
cp .env.example .env
# Add your CORESIGNAL_API_KEY and OPENAI_API_KEY

# Use CLI
leadgen search "AI startups in SF with 10+ employees"
leadgen health
leadgen api  # Start REST API
```

### Package Management

**Uses pyproject.toml (modern Python packaging):**
- `uv pip install -e .` → fast installation with uv (10-100x faster than pip)
- `pip install -e .` → traditional pip (fallback)
- Dependencies defined in pyproject.toml only
- No requirements.txt needed

**Alternative installation methods:**
```bash
# With pip (slower)
pip install -e .

# With uv in a virtual environment
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uv pip install -e .

# With uv and sync (creates venv automatically)
uv sync
source .venv/bin/activate
```

## Architecture

### Package Structure
```
core_sdr/
├── __main__.py          # Entry: python -m core_sdr
├── src/
│   ├── core/            # Orchestrator + models
│   ├── parsers/         # LLM → Elasticsearch DSL
│   ├── schema/          # Feature-flagged schema management
│   ├── clients/         # CoreSignal API
│   ├── cache/           # MongoDB caching
│   ├── formatters/      # JSON/CSV/Summary output
│   ├── cli/             # Click interface
│   └── api/             # FastAPI interface
└── config/              # Unified system configuration
```

### Data Flow
```
"AI startups in SF" → LLM DSL Generator → CoreSignal API → Companies
```

### LLM Integration
Direct natural language to DSL conversion using GPT-4o:

- **System prompt** built from current CoreSignal schema
- **Predefined values** guide LLM field mappings
- **Fallback queries** when LLM unavailable
- **Schema-aware** DSL generation with validation

### Feature-Flagged Schema Management
```
config/system_config.json          # Single config file
├── coresignal_schema              # CoreSignal field definitions
├── feature_flags                  # Schema update controls
└── schema_update_config           # Auto-update settings
```

**Schema update features (disabled by default):**
- API-driven schema discovery
- Automatic predefined value updates
- Scheduled schema refreshes

## Environment Variables

```bash
# Required
CORESIGNAL_API_KEY=your_key_here          # CoreSignal API access
OPENAI_API_KEY=your_openai_key            # GPT-4o for DSL generation

# Optional
MONGODB_URI=mongodb://localhost:27017/db  # Caching
CACHE_TTL_HOURS=24                        # Cache expiration
LLM_MODEL=gpt-4o                          # LLM model selection

# Feature flags (override config file)
SCHEMA_AUTO_UPDATE=false                  # Master schema update switch
SCHEMA_API_DRIVEN_UPDATES=false           # API discovery
SCHEMA_SCHEDULED_UPDATES=false            # Scheduled updates
```

## CLI Commands

```bash
# Search
leadgen search "query"
leadgen search --format csv --max-results 50 "query"

# Utils
leadgen explain "query"    # Show parsing without search
leadgen health            # System status
leadgen stats             # Usage statistics
leadgen clear-cache       # Clear MongoDB cache
```

## API Usage

```bash
# Start server
leadgen api

# Search endpoint
curl -X POST http://localhost:8000/search \
  -d '{"query": "AI startups in SF", "max_results": 10}'
```

## Usage Examples

```python
# Direct Python usage
from core_sdr import QueryParser, ResultFormatter

parser = QueryParser()
formatter = ResultFormatter()

# Parse and search
dsl_query = parser.parse_query("AI startups in SF with 10+ employees")
companies = coresignal_client.search_companies(dsl_query)
results = formatter.format_results(companies, format_type="summary")

# Explain query parsing
explanation = parser.explain_parse("SaaS companies using AWS")
print(explanation["interpretation"])
```

```bash
# CLI usage examples
leadgen search "Public companies in healthcare with 500+ employees"
leadgen search --format csv --max-results 100 "Fintech startups in NYC"
leadgen explain "E-commerce companies using React and AWS"
leadgen health
```

## Development

### Key Components

1. **LLMDSLGenerator**: GPT-4o converts natural language to DSL
2. **SchemaManager**: Feature-flagged schema with auto-updates
3. **FeatureFlags**: Environment/config-based feature control
4. **CoreSignalClient**: API wrapper with rate limiting
5. **CacheManager**: MongoDB-only caching (when available)
6. **Orchestrator**: Coordinates all components

### Caching Strategy

- **MongoDB only** (when MONGODB_URI provided)
- **No-op cache** when MongoDB unavailable
- 24hr TTL, MD5 cache keys
- Graceful degradation if cache fails

### Testing

```bash
# Demo with sample queries
leadgen demo

# Health check
leadgen health

# Explain parsing
leadgen explain "SaaS companies using AWS"
```

This system converts queries like "Public SaaS companies in California with 100+ employees using AWS" into structured database searches via CoreSignal's API.