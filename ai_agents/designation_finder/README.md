# LinkedIn Designation Finder

A simplified workflow to find LinkedIn profiles of people with specific designations at target companies.

## Overview

This workflow takes a CSV file with company names and job designations, then searches LinkedIn to find people matching those designations at those companies. It uses fuzzy matching to find similar titles and returns up to 5 profiles per company.

## Features

- **Simple CSV Input**: Just company_name and designation columns
- **Fuzzy Matching**: Finds similar titles (e.g., "CEO" matches "Chief Executive Officer", "Co-CEO", etc.)
- **LinkedIn Search**: Uses browserMCP to search LinkedIn profiles
- **Clean Output**: Returns only names and LinkedIn URLs as requested
- **Error Handling**: Skips companies/designations that can't be found
- **No Rate Limiting**: Processes requests without delays

## Setup

1. **Environment Variables** (`.env` file in `/designation_finder/` directory):
   ```bash
   # Required
   OPENAI_API_KEY=your-openai-api-key
   
   # Data Source (Google Sheet takes priority)
   GOOGLE_SHEET_URL=https://docs.google.com/spreadsheets/d/your-sheet-id/edit?gid=your-gid
   
   # Optional fallback to local CSV
   CSV_FILE_PATH=sample_input.csv
   ```
   
   **Note**: The `.env` file should be in the workflow directory (`/ai_agents/designation_finder/`), not in the project root.

2. **Google Sheets Setup**:
   - **IMPORTANT**: Make your Google Sheet publicly viewable:
     1. Open your Google Sheet
     2. Click "Share" button (top right)
     3. Change access to "Anyone with the link" → "Viewer"
     4. Copy the share link
   - Sheet should have columns: `company_name` and `designation`
   - The workflow will automatically detect headers
   - Default sheet: https://docs.google.com/spreadsheets/d/1Z5S1Tr8ftbj6teWyWAcvYbsBqkpaRbE0/edit?gid=1107711838#gid=1107711838
   - If sheet is not accessible, workflow will fall back to local CSV

3. **Input Format** (Google Sheet or CSV):
   ```csv
   company_name,designation
   Apple,CEO
   Microsoft,CTO
   Google,VP Sales
   Meta,Head of Marketing
   ```

4. **Sample Input**: Use the provided `sample_input.csv` as a template for local testing

## Usage

### Run the workflow:
```bash
# Make sure you have a .env file in designation_finder/ with OPENAI_API_KEY
cd ai_agents/designation_finder
python main.py

# The script will automatically load .env from the current directory
```

### Expected Flow:
1. **Data Loading**: Loads company-designation pairs from Google Sheet (or CSV fallback)
2. **LinkedIn Search**: For each pair, searches LinkedIn with fuzzy matching
3. **Results Collection**: Collects up to 5 profiles per company
4. **Output Generation**: Saves results to CSV and JSON files

## Output Files

The workflow generates three files in the output directory:

1. **`linkedin_profiles_YYYYMMDD_HHMMSS.csv`**: 
   - Main output with Name and LinkedIn_URL columns only
   - Ready for immediate use

2. **`linkedin_profiles_YYYYMMDD_HHMMSS.json`**: 
   - Detailed results with additional metadata
   - Includes company names, job titles, search metadata

3. **`search_summary_YYYYMMDD_HHMMSS.txt`**: 
   - Summary report with statistics
   - Lists successful results, skipped companies, and errors

## Example Output

**CSV Output:**
```csv
Name,LinkedIn_URL
Tim Cook,https://linkedin.com/in/tim-cook
Satya Nadella,https://linkedin.com/in/satya-nadella
```

**Summary:**
```
✅ 15 LinkedIn profiles found
🏢 8 companies with results  
⏭️ 2 companies skipped
❌ 0 errors
```

## Fuzzy Matching Examples

The system intelligently matches variations:
- **"CEO"** → "Chief Executive Officer", "Co-CEO", "Chief Executive"
- **"CTO"** → "Chief Technology Officer", "Chief Technical Officer"  
- **"VP Sales"** → "Vice President Sales", "VP of Sales", "Sales VP"
- **"Marketing Manager"** → "Marketing Director", "Head of Marketing"

## Error Handling

- **Company not found**: Skipped and logged
- **Designation not found**: Skipped and logged  
- **LinkedIn search fails**: Retried once, then skipped
- **Processing errors**: Logged but don't stop workflow

## Directory Structure

```
ai_agents/designation_finder/
├── __init__.py
├── main.py                 # Main entry point
├── models.py              # Data models
├── graph.py               # LangGraph workflow
├── sample_input.csv       # Example input file
├── README.md              # This file
├── nodes/
│   ├── __init__.py
│   ├── company_designation_retriever.py  # CSV reader
│   ├── linkedin_designation_finder.py    # LinkedIn search
│   └── results_saver.py                  # Output generation
├── config/                # Configuration files (if needed)
└── output/                # Generated results
    └── designation_finder_YYYYMMDD_HHMMSS/
        ├── linkedin_profiles_YYYYMMDD_HHMMSS.csv
        ├── linkedin_profiles_YYYYMMDD_HHMMSS.json
        └── search_summary_YYYYMMDD_HHMMSS.txt
```

## Key Differences from SDR Workflow

- ✅ **Simpler**: No relevance checking or web enrichment
- ✅ **Focused**: Only LinkedIn profile finding
- ✅ **Linear**: Straightforward workflow without complex conditionals
- ✅ **Targeted**: Searches for specific designations rather than general executives
- ✅ **Clean Output**: Only names and LinkedIn URLs as requested