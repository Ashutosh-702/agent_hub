# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Agent Hub is a centralized repository for AI-powered business automation agents. Currently houses the AI SDR (Sales Development Representative) agent with infrastructure to support additional agents.

## Development Commands

### Running the AI SDR Agent

**Interactive CLI Mode (Recommended for setup):**
```bash
source venv/bin/activate
python ai_agents/ai_sdr/run_cli.py
```

**GUI Mode:**
```bash
source venv/bin/activate
python ai_agents/ai_sdr/run_gui.py
```

**Responsive GUI Mode (Better for small screens):**
```bash
source venv/bin/activate
python ai_agents/ai_sdr/run_gui_responsive.py
```

**Direct Command Line Mode:**
```bash
source venv/bin/activate
python ai_agents/ai_sdr/sdr/main.py
```

**Model Validation:**
```bash
source venv/bin/activate
python ai_agents/ai_sdr/sdr/validate_models.py
```

**Create Desktop Shortcut (macOS):**
```bash
source venv/bin/activate
python ai_agents/ai_sdr/create_desktop_shortcut.py
```

### Environment Setup

**Initialize Python environment:**
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r ai_agents/ai_sdr/requirements.txt
```

**Key Dependencies:**
- LangGraph 0.4.8+ for workflow orchestration
- PyQt6 6.4.0+ for GUI applications
- OpenAI 1.0.0+ for LLM integration
- Pydantic 2.11.5+ for data validation
- MCP 1.9.1+ for browser automation

Required environment variables (create `.env` file in `ai_agents/ai_sdr/`):
```
OPENAI_API_KEY=your-api-key
HUBSPOT_API_KEY=your-hubspot-key (optional)
HUBSPOT_OWNER_EMAIL=your-email@company.com
CLEARBIT_API_KEY=your-clearbit-key (optional)
DATA_SOURCE_TYPE=csv  # or google_sheets
CSV_FILE_PATH=companies.csv
GOOGLE_SHEET_URL=https://docs.google.com/spreadsheets/d/...
GOOGLE_WORKSHEET_NAME=Sheet1
MAX_COMPANIES=100
BROWSER_TIMEOUT=30
CREATE_HUBSPOT_CONTACTS=true
```

## Architecture Overview

### AI SDR Agent (`ai_agents/ai_sdr/`)

**LangGraph Workflow System:**
- Uses LangGraph state management for multi-step prospect research workflow
- Loop-based company processing with conditional routing
- Async execution with graceful error handling and recovery

**Core Components:**
- `sdr/graph.py` - LangGraph workflow definition with conditional edges
- `sdr/models.py` - Pydantic models for workflow state and data structures
- `sdr/main.py` - Async workflow runner with logging and configuration
- `sdr/nodes/` - Individual workflow steps (web enrichment, LinkedIn research, HubSpot integration)

**Workflow Flow:**
1. Company retrieval from CSV/Excel
2. Loop: Web analysis → Relevance check → LinkedIn enrichment → HubSpot contact creation
3. LinkedIn data backup and batch HubSpot processing
4. Error summary and results export

**Data Processing:**
- Streamlined web enricher analyzes company relevance using OpenAI
- Prospect enricher finds LinkedIn profiles for decision makers
- HubSpot contact creator manages CRM integration with duplicate detection
- File storage system with numbered runs (`output/run_NNNN/`)

**Logging System:**
- Dual-mode logging: "clean" (terminal-friendly) and "detailed" (comprehensive)
- Structured logging with section tracking and progress indicators
- Error categorization (skipped companies, LinkedIn failures, HubSpot failures, web failures)

**GUI Interface:**
- PyQt6-based desktop application (`sdr_gui.py`)
- Real-time progress tracking with log streaming
- Custom prompt configuration and file input handling

### Key Design Patterns

**State Management:**
- WorkflowState model tracks companies, enrichment data, LinkedIn profiles, and categorized errors
- Current company index and loop progression state maintained across workflow steps
- Run directories structure for organized output (`progress/`, `final/`, `results/`, `logs/`)

**Error Handling:**
- Categorized error tracking in ErrorSummary model
- Graceful degradation when companies are not relevant or LinkedIn enrichment fails
- Individual company failures don't stop workflow execution

**Configuration:**
- Environment-based configuration with .env file support
- Interactive prompt customization with save/load functionality
- Optional HubSpot integration with configurable contact creation

## Development Notes

- All workflow nodes are async functions that take WorkflowState and return modified state
- Use the logging system (`sdr_logger`) for consistent output formatting
- GUI spawns subprocess for workflow execution to prevent UI freezing
- Model validation available for debugging Pydantic issues
- Output files are versioned with run numbers for traceability

## Recent Updates

1. **CLI Application**: Interactive CLI for workflow configuration
2. **Responsive GUI**: Improved GUI with better small window support
3. **Deprecation Fixes**: Fixed PyQt6 deprecation warnings
4. **Real-time Features**: Added real-time log monitoring and results viewing
5. **Enhanced LinkedIn Navigation**: Improved prompt to handle navigation from any starting page
6. **Real-time Logging**: Integrated loguru output with Qt signals for live updates
7. **Fixed UI Issues**: Resolved black background in collapsible sections
8. **Improved Log Performance**: Faster refresh rates and efficient log updates

## Understanding Logs

- **Progress Log** (Execution Tab): Shows real-time workflow status updates from the thread via Qt signals
- **Logs Tab**: Displays complete file-based logs (`workflow.log`) with auto-refresh
- Logging uses `loguru` with line buffering for immediate file writes
- Console output and file logs are synchronized for consistency

## Testing and Validation

### Running Pydantic Model Validation
```bash
python ai_agents/ai_sdr/sdr/validate_models.py
```
This validates all Pydantic models used in the workflow to ensure data structures are correctly defined.

### Manual Testing Workflow
1. Start with a small CSV file (2-3 companies) for testing
2. Use CLI mode first to verify configuration
3. Monitor logs in `output/run_NNNN/logs/` for detailed debugging
4. Check `errors.log` for specific failures

## Troubleshooting

### Common Issues

**MCP Browser Connection**
- Ensure MCP browser server is running before starting workflow
- Check browser timeout settings (default: 30 seconds)

**LinkedIn Navigation Failures**
- The enhanced prompt handles navigation from any starting page
- If failures persist, increase `BROWSER_TIMEOUT` in configuration

**HubSpot Integration**
- Verify API key has correct permissions
- Check owner email exists in HubSpot
- Monitor duplicate detection in logs

**Log File Access**
- Logs are written with line buffering for real-time updates
- If logs appear delayed, check file permissions in output directory

## Adding New Agents to the Hub

### Agent Structure
New agents should follow this structure:
```
ai_agents/
  new_agent/
    __init__.py
    requirements.txt
    main.py           # Entry point
    models.py         # Pydantic models
    nodes/            # Workflow nodes
    prompts.py        # AI prompts
    gui.py            # Optional GUI
```

### Integration Guidelines
1. Use LangGraph for workflow orchestration
2. Implement Pydantic models for state management
3. Use loguru for consistent logging
4. Create numbered output directories for runs
5. Support both CLI and GUI interfaces

## Performance Optimization

### Workflow Performance
- Use `MAX_COMPANIES` to limit batch size
- Monitor `llm_responses.log` for token usage
- Implement retry logic with exponential backoff

### GUI Performance
- Real-time logs use 0.5-second refresh interval
- Progress updates are throttled via Qt signals
- Large log files are efficiently handled with scroll position tracking

## Debugging Workflows

### Enable Detailed Logging
```bash
export LOG_MODE=detailed
python ai_agents/ai_sdr/sdr/main.py
```

### Analyze Workflow State
- Check `progress/` directory for intermediate state saves
- Review `final/` directory for completed results
- Use model validation to debug data structure issues

### LangGraph Debugging
- Workflow compilation errors appear early in logs
- Node execution order is logged with timestamps
- State transitions are tracked in workflow.log