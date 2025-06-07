# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI-powered SDR (Sales Development Representative) workflow system that automates prospect research and lead generation. The system uses LangGraph for workflow orchestration, OpenAI for AI analysis, and integrates with HubSpot for contact management.

**Note: This agent is part of the GoFynd SupplyChainGroup agent_hub repository and should be integrated into the larger agent ecosystem when deployed.**

### Core Architecture

The system follows a node-based workflow pattern built on LangGraph:

1. **Company List Retrieval** - Loads companies from CSV or Google Sheets
2. **Web Enrichment** - Performs web research and relevance assessment for each company
3. **Prospect Enrichment** - LinkedIn prospect research for relevant companies
4. **HubSpot Integration** - Creates contacts in HubSpot CRM
5. **File Storage** - Saves consolidated results and progress

### Key Components

- **`sdr/main.py`** - Main workflow executor with async processing
- **`sdr/graph.py`** - LangGraph workflow definition with loop-based company processing
- **`sdr/models.py`** - Pydantic data models (Company, Contact, WorkflowState)
- **`sdr/nodes/`** - Individual workflow nodes for each processing step
- **`sdr_gui_launcher.py`** - Tkinter GUI for non-technical users
- **`mac_app_launcher.py`** - macOS app bundle launcher

## Common Development Commands

### Running the Application

```bash
# CLI execution with prompts
python sdr/main.py

# GUI launcher (recommended for users)
python sdr_gui_launcher.py

# Mac app version
python mac_app_launcher.py
```

### Environment Setup

```bash
# Install dependencies
pip install -r requirements.txt

# User-friendly setup (handles dependencies + env config)
python setup_for_users.py
```

### Build Commands

```bash
# Build Mac app bundle
./build_mac_app.sh

# Test app build
python test_app_build.py
```

### Testing and Validation

```bash
# Validate Pydantic models
python sdr/validate_models.py
```

## Configuration Management

### Environment Variables (.env)
- `OPENAI_API_KEY` - Required for AI analysis
- `HUBSPOT_API_KEY` - Optional for CRM integration
- `DATA_SOURCE_TYPE` - "csv" or "google_sheets"
- `CSV_FILE_PATH` - Path to companies CSV file
- `MAX_COMPANIES` - Processing limit (default: 100)

### Custom Prompts
- Stored in `sdr/config/custom_prompts.json`
- Default prompts defined in `sdr/prompts.py`
- GUI allows interactive prompt customization

### Output Structure
```
output/
├── run_XXXX/           # Numbered runs
│   ├── final/          # Consolidated results
│   ├── logs/           # Detailed logs
│   ├── progress/       # Intermediate saves
│   └── results/        # Summary reports
└── run_counter.txt     # Auto-incrementing run ID
```

## Development Notes

### Workflow State Management
- All state is managed through `WorkflowState` Pydantic model
- State persists company data, enrichment results, and progress
- Each workflow run gets unique `run_id` and directory structure

### Async Processing
- Main workflow uses asyncio with graceful shutdown handling
- OpenAI client is initialized as AsyncOpenAI
- Error handling includes task cancellation and timeout management

### Logging System
- Custom logging config in `sdr/logging_config.py`
- Structured logging with section/subsection tracking
- Separate log files for errors, LLM responses, and workflow progress

### GUI Architecture
- Built with tkinter for cross-platform compatibility
- ConfigManager handles .env and user settings
- Non-blocking subprocess execution for workflow runs
- Real-time log display and progress tracking

### Mac App Bundle
- Uses py2app for macOS distribution
- Bundle structure supports both development and frozen execution
- Icon and metadata configured for professional appearance

## Memories
- add the above plan to memory, i will be doing this later