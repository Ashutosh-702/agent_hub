"""
Company List Retriever Node

Retrieves company data from Google Sheets or CSV files.
"""

import pandas as pd
import re
import requests
from io import StringIO
from typing import Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential

from ai_agents.ai_sdr.sdr.models import Company, WorkflowState
from ai_agents.ai_sdr.sdr.logging_config import clean_log, detailed_log
import urllib3
from urllib3.exceptions import InsecureRequestWarning

urllib3.disable_warnings(InsecureRequestWarning)


def _convert_google_sheet_url_to_csv(sheet_url: str, worksheet_name: str = None) -> str:
    """Convert Google Sheets URL to CSV export URL"""
    try:
        # Extract sheet ID from various Google Sheets URL formats
        sheet_id_pattern = r'/spreadsheets/d/([a-zA-Z0-9-_]+)'
        match = re.search(sheet_id_pattern, sheet_url)

        if not match:
            raise ValueError("Invalid Google Sheets URL format")

        sheet_id = match.group(1)

        # Extract GID from URL if present (e.g., #gid=123456 or &gid=123456)
        gid = "0"  # Default to first sheet
        gid_pattern = r'[#&]gid=([0-9]+)'
        gid_match = re.search(gid_pattern, sheet_url)
        
        if gid_match:
            gid = gid_match.group(1)
            detailed_log(f"Found GID in URL: {gid}")
        elif worksheet_name:
            detailed_log(f"Worksheet name '{worksheet_name}' specified, but no GID found in URL. Using default GID=0", "warning")
            detailed_log("To use a specific worksheet, include #gid=WORKSHEET_ID in your Google Sheets URL", "info")

        # Construct CSV export URL
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
        detailed_log(f"Generated CSV URL: {csv_url}")
        return csv_url

    except Exception as e:
        detailed_log(f"Error converting Google Sheets URL: {e}", "error")
        raise


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def _read_google_sheet(sheet_url: str, worksheet_name: str = None) -> pd.DataFrame:
    """Read data from public Google Sheets via CSV export"""
    try:
        # Convert Google Sheets URL to CSV export URL
        csv_url = _convert_google_sheet_url_to_csv(sheet_url, worksheet_name)
        detailed_log(f"Reading from CSV export URL: {csv_url}")

        # Use requests with SSL verification disabled for Google Sheets
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(csv_url, headers=headers, verify=False, timeout=30)
        response.raise_for_status()

        # Check if response looks like CSV
        content = response.text
        if not content.strip():
            raise ValueError("Empty response from Google Sheets")

        # Check if it's an error page
        if "<!DOCTYPE html>" in content.lower() or "<html>" in content.lower():
            raise ValueError("Google Sheets returned HTML instead of CSV. Check if the sheet is publicly accessible.")

        # Parse CSV content using pandas
        df = pd.read_csv(StringIO(content))

        clean_log(f"Read {len(df)} rows, {len(df.columns)} columns from Google Sheet")
        detailed_log(f"Successfully read {len(df)} rows and {len(df.columns)} columns from Google Sheet")
        detailed_log(f"Columns found: {df.columns.tolist()}")

        return df

    except requests.exceptions.RequestException as e:
        clean_log(f"Google Sheet network error: {e}", "error")
        detailed_log(f"Network error reading Google Sheet: {e}", "error")
        detailed_log("Make sure the Google Sheet is publicly accessible (Anyone with the link can view)", "error")
        raise
    except Exception as e:
        clean_log(f"Google Sheet error: {e}", "error")
        detailed_log(f"Error reading Google Sheet: {e}", "error")
        detailed_log("Make sure the Google Sheet is publicly accessible (Anyone with the link can view)", "error")
        raise


async def _read_csv_file(file_path: str) -> pd.DataFrame:
    """Read data from CSV file"""
    try:
        return pd.read_csv(file_path)
    except Exception as e:
        clean_log(f"CSV file error: {e}", "error")
        detailed_log(f"Error reading CSV file: {e}", "error")
        raise


def _normalize_company_data(df: pd.DataFrame) -> list[Company]:
    """Normalize DataFrame to Company objects"""
    companies = []

    # Common column name mappings
    column_mapping = {
        'name': 'name',  # Direct mapping
        'company_name': 'name',
        'company': 'name',  # This will match "Company" column
        'organization': 'name',
        'website_url': 'website',
        'website': 'website',
        'url': 'website',
        'company_domain': 'domain',
        'domain': 'domain',
        'industry': 'industry',
        'sector': 'industry',
        'company_size': 'size',
        'size': 'size',
        'employees': 'size',
        'location': 'location',
        'city': 'location',
        'country': 'location',
        'description': 'description',
        'about': 'description',
        'linkedin': 'linkedin_url',
        'linkedin_url': 'linkedin_url',
        'linkedin_page': 'linkedin_url'
    }

    # Normalize column names
    df_normalized = df.copy()
    df_normalized.columns = df_normalized.columns.str.lower().str.strip()

    detailed_log(f"Columns found in data: {df_normalized.columns.tolist()}")

    # Check if we only have a company name column
    has_only_company_name = len(df_normalized.columns) == 1 and any(
        col in column_mapping and column_mapping[col] == 'name'
        for col in df_normalized.columns
    )

    if has_only_company_name:
        detailed_log("Detected single-column format with only company names")

    for _, row in df_normalized.iterrows():
        company_data = {
            # Initialize all fields with None by default
            'name': None,
            'website': None,
            'domain': None,
            'industry': None,
            'size': None,
            'location': None,
            'description': None,
            'linkedin_url': None
        }

        # Map columns to Company fields
        for col in df_normalized.columns:
            if col in column_mapping:
                field_name = column_mapping[col]
                value = row[col]
                if pd.notna(value) and str(value).strip():
                    company_data[field_name] = str(value).strip()

        # Ensure we have at least a company name
        if company_data['name'] is not None and company_data['name'].strip():
            try:
                # Create the Company object with all fields properly initialized
                company = Company(**company_data)
                companies.append(company)
                detailed_log(f"Created company record: {company.name}", "debug")
            except Exception as e:
                detailed_log(f"Error creating company from row: {e}", "warning")
                detailed_log(f"Problematic data: {company_data}", "warning")
        else:
            detailed_log(f"Skipping row without company name: {row.to_dict()}", "warning")

    clean_log(f"Created {len(companies)} company records")
    detailed_log(f"Successfully created {len(companies)} company records")
    if has_only_company_name:
        detailed_log("All companies created with minimal data (name only)")

    return companies


async def company_list_retriever(state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
    """
    LangGraph node to retrieve company list from Google Sheets or CSV
    
    Args:
        state: Current workflow state
        config: Configuration containing data source info
        
    Returns:
        Updated workflow state with companies loaded
    """
    clean_log("Starting company list retrieval")
    detailed_log("Starting company list retrieval")

    # Debug: Print the actual config to see what we're receiving
    detailed_log(f"Config received: {config}", "debug")
    detailed_log(f"Config keys: {list(config.keys()) if config else 'Config is None/empty'}", "debug")

    try:
        config = config.get("configurable")
        # Get data source configuration
        data_source = config.get('data_source', {})
        source_type = data_source.get('type', 'csv')

        if source_type == 'google_sheets':
            sheet_url = data_source.get('sheet_url')
            worksheet_name = data_source.get('worksheet_name')

            if not sheet_url:
                raise ValueError("Google Sheets URL is required")

            clean_log(f"Reading from Google Sheets")
            detailed_log(f"Reading from Google Sheets: {sheet_url}")
            df = await _read_google_sheet(sheet_url, worksheet_name)

        elif source_type == 'csv':
            file_path = data_source.get('file_path', 'companies.csv')
            clean_log(f"Reading from CSV file: {file_path}")
            detailed_log(f"Reading from CSV file: {file_path}")
            df = await _read_csv_file(file_path)

        else:
            raise ValueError(f"Unsupported data source type: {source_type}")

        # Normalize and convert to Company objects
        companies = _normalize_company_data(df)

        # Enhanced validation for company list
        if not companies or len(companies) == 0:
            error_msg = "No valid companies found in data source - company list is empty"
            clean_log(error_msg, "error")
            detailed_log(error_msg, "error")
            state.companies = []
            state.current_company_index = 0
            state.current_company = None
            state.errors.append(error_msg)
            
            # Track in categorized errors
            if not hasattr(state, 'error_summary') or state.error_summary is None:
                from ai_agents.ai_sdr.sdr.models import ErrorSummary
                state.error_summary = ErrorSummary()
            state.error_summary.general_errors.append(error_msg)
            
            return state

        # Validate company data quality
        valid_companies = []
        invalid_count = 0
        
        for company in companies:
            if company.name and company.name.strip():
                valid_companies.append(company)
            else:
                invalid_count += 1
                detailed_log(f"Skipping company with empty/invalid name: {company}", "warning")

        if not valid_companies:
            error_msg = f"No companies with valid names found. {invalid_count} companies had empty/invalid names"
            clean_log(error_msg, "error")
            detailed_log(error_msg, "error")
            state.companies = []
            state.current_company_index = 0
            state.current_company = None
            state.errors.append(error_msg)
            
            # Track in categorized errors
            if not hasattr(state, 'error_summary') or state.error_summary is None:
                from ai_agents.ai_sdr.sdr.models import ErrorSummary
                state.error_summary = ErrorSummary()
            state.error_summary.general_errors.append(error_msg)
            
            return state

        # Apply MAX_COMPANIES limit if configured
        max_companies = config.get('max_companies', None)
        if max_companies and max_companies > 0 and len(valid_companies) > max_companies:
            original_count = len(valid_companies)
            valid_companies = valid_companies[:max_companies]
            clean_log(f"Limited to {max_companies} companies (MAX_COMPANIES setting)")
            detailed_log(f"Applied MAX_COMPANIES limit: {original_count} -> {max_companies} companies")

        # Update state with validated companies
        state.companies = valid_companies
        state.current_company_index = 0
        state.current_company = valid_companies[0]

        # Log validation results
        clean_log(f"Loaded {len(valid_companies)} valid companies")
        detailed_log(f"Successfully loaded {len(valid_companies)} valid companies")
        if invalid_count > 0:
            detailed_log(f"Filtered out {invalid_count} companies with invalid names", "warning")
        detailed_log(f"First company: {state.current_company.name}")

        return state

    except Exception as e:
        error_msg = f"Failed to retrieve company list: {str(e)}"
        clean_log(f"Company list retrieval failed: {str(e)}", "error")
        detailed_log(error_msg, "error")
        state.errors.append(error_msg)
        return state
