"""
Company Designation Retriever Node
Reads data from Google Sheets with company_name and designation columns
"""
import os
import requests
import csv
import pandas as pd
import re
from io import StringIO
from typing import List, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential
from ai_agents.designation_finder.models import DesignationFinderState, CompanyDesignation
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
        gid_pattern = r'[#&]gid=([0-9]+)'
        gid_match = re.search(gid_pattern, sheet_url)
        
        if gid_match:
            gid = gid_match.group(1)
            print(f"Found GID in URL: {gid}. Using this GID for sheet selection.")
            if worksheet_name:
                print(f"Worksheet name '{worksheet_name}' was also provided, but the GID from the URL takes precedence.")
        elif worksheet_name:
            # worksheet_name is provided, but no GID in URL. This is an error.
            error_msg = (
                f"A worksheet name ('{worksheet_name}') was specified, but the sheet's GID was not found in the URL. "
                "The system cannot select the correct sheet by name alone.\n\n"
                "To fix this, please open your Google Sheet, select the correct worksheet tab, "
                "and copy the full URL from your browser's address bar. It should contain '#gid=...'. "
                "Use this full URL in your configuration."
            )
            print(error_msg)
            raise ValueError(error_msg)
        else:
            # No GID in URL and no worksheet_name specified. Default to the first sheet.
            gid = "0"
            print("No GID found in URL and no worksheet name specified. Defaulting to the first sheet (GID=0).")

        # Construct CSV export URL
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
        print(f"Generated CSV URL: {csv_url}")
        return csv_url

    except Exception as e:
        print(f"Error converting Google Sheets URL: {e}")
        raise


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def get_google_sheet_data(sheet_url: str, worksheet_name: str = None) -> List[List[str]]:
    """Read data from public Google Sheets via CSV export"""
    try:
        # Convert Google Sheets URL to CSV export URL
        csv_url = _convert_google_sheet_url_to_csv(sheet_url, worksheet_name)
        print(f"Reading from CSV export URL: {csv_url}")

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

        # Debug: Print first few lines of raw CSV content
        print("=== RAW CSV CONTENT DEBUG ===")
        lines = content.split('\n')[:10]  # First 10 lines
        for i, line in enumerate(lines):
            print(f"Line {i}: '{line}'")
        print("=== END RAW CSV CONTENT ===")

        # Parse CSV content using pandas
        df = pd.read_csv(StringIO(content))

        print(f"Read {len(df)} rows, {len(df.columns)} columns from Google Sheet")
        print(f"Successfully read {len(df)} rows and {len(df.columns)} columns from Google Sheet")
        print(f"Columns found: {df.columns.tolist()}")
        
        # Debug: Print first few rows of DataFrame
        print("=== DATAFRAME DEBUG ===")
        print(f"DataFrame shape: {df.shape}")
        print("DataFrame head:")
        print(df.head())
        print("=== END DATAFRAME DEBUG ===")

        # Convert DataFrame back to list of lists format
        data = [df.columns.tolist()] + df.values.tolist()
        
        return data

    except requests.exceptions.RequestException as e:
        print(f"Google Sheet network error: {e}")
        print(f"Network error reading Google Sheet: {e}")
        print("Make sure the Google Sheet is publicly accessible (Anyone with the link can view)")
        raise
    except Exception as e:
        print(f"Google Sheet error: {e}")
        print(f"Error reading Google Sheet: {e}")
        print("Make sure the Google Sheet is publicly accessible (Anyone with the link can view)")
        raise


def company_designation_retriever(state: DesignationFinderState, config: Dict[str, Any] = None) -> DesignationFinderState:
    """
    Read company designations from Google Sheets
    Expected format: company_name,designation columns
    """
    try:
        # Get config from LangGraph or fallback to state
        config_data = config.get("configurable", {})
        
        google_sheet_url = None
        # google_sheet_url = config_data.get("google_sheet_url")
        csv_file_path = config_data.get("csv_file_path", "sample_input.csv")
        
        company_designations = []
        
        if google_sheet_url:
            print(f"📊 Attempting to read from Google Sheet...")
            
            try:
                # Get data from Google Sheets
                rows = get_google_sheet_data(google_sheet_url)
                
                if not rows:
                    print("⚠️ No data found in Google Sheet, falling back to local CSV")
                    google_sheet_url = None  # Fall back to CSV
                else:
                    print(f"✅ Successfully loaded {len(rows)} rows from Google Sheet")
                    
                    # Check if first row is header
                    has_header = False
                    if rows and len(rows[0]) >= 2:
                        first_row = [str(cell).strip().lower() for cell in rows[0]]
                        # Check for common header patterns
                        has_header = (any('company' in cell for cell in first_row) and 
                                    any('designation' in cell for cell in first_row))
                    
                    # Skip header if present
                    start_row = 1 if has_header else 0
                    
                    print(f"📋 Processing rows starting from row {start_row + 1} (header {'detected' if has_header else 'not detected'})")
                    
                    for row_num, row in enumerate(rows[start_row:], start=start_row+1):
                        # Skip empty rows
                        if not row or all(not str(cell).strip() for cell in row):
                            continue
                            
                        if len(row) < 2:
                            error_msg = f"Invalid row {row_num}: Expected at least 2 columns, got {len(row)}"
                            state.errors.append(error_msg)
                            continue
                        
                        company_name = str(row[0]).strip()
                        designation = str(row[1]).strip()
                        
                        if not company_name or not designation:
                            error_msg = f"Empty values in row {row_num}: company='{company_name}', designation='{designation}'"
                            state.errors.append(error_msg)
                            continue
                        
                        company_designations.append(
                            CompanyDesignation(
                                company_name=company_name,
                                designation=designation
                            )
                        )
                    
                    print(f"✅ Loaded {len(company_designations)} company-designation pairs from Google Sheet")
                    
            except Exception as sheet_error:
                print(f"⚠️ Failed to access Google Sheet: {str(sheet_error)}")
                print("💡 Make sure the sheet is publicly viewable (Share → Anyone with link → Viewer)")
                print("📄 Falling back to local CSV file...")
                google_sheet_url = None  # Fall back to CSV
                rows = None  # Reset rows to None for fallback
        
        # Fallback to local CSV if Google Sheet failed or not provided
        if not google_sheet_url or not company_designations:
            # Fallback to local CSV file
            print(f"📄 Reading from local CSV: {csv_file_path}")
            
            if not os.path.exists(csv_file_path):
                error_msg = f"CSV file not found: {csv_file_path}"
                state.errors.append(error_msg)
                return state
            
            with open(csv_file_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                
                # Read first row to check if it's a header
                first_row = next(reader, None)
                if not first_row:
                    error_msg = f"CSV file is empty: {csv_file_path}"
                    state.errors.append(error_msg)
                    return state
                
                # Check if first row looks like a header (contains common header words)
                first_row_lower = [str(cell).strip().lower() for cell in first_row]
                has_header = (any('company name' in cell for cell in first_row_lower) and
                            any('designation' in cell for cell in first_row_lower))
                
                # If it's a header, start from row 2, otherwise include first row in processing
                rows_to_process = []
                if not has_header:
                    rows_to_process.append((1, first_row))  # Include first row with row number 1
                
                # Add remaining rows
                for row_num, row in enumerate(reader, start=1 if has_header else 2):
                    rows_to_process.append((row_num, row))
                
                print(f"📋 Processing CSV with {'header' if has_header else 'no header'} detected")
                
                for row_num, row in rows_to_process:
                    if len(row) < 2:
                        error_msg = f"Invalid row {row_num}: Expected at least 2 columns, got {len(row)}"
                        state.errors.append(error_msg)
                        continue
                    
                    company_name = row[0].strip()
                    designation = row[1].strip()
                    
                    if not company_name or not designation:
                        error_msg = f"Empty values in row {row_num}: company='{company_name}', designation='{designation}'"
                        state.errors.append(error_msg)
                        continue
                    
                    company_designations.append(
                        CompanyDesignation(
                            company_name=company_name,
                            designation=designation
                        )
                    )
            
            print(f"✅ Loaded {len(company_designations)} company-designation pairs from {csv_file_path}")
        
        # Update state
        state.company_designations = company_designations
        state.total_count = len(company_designations)
        state.current_index = 0
        
        # Set current company designation for processing
        if company_designations:
            state.current_company_designation = company_designations[0]
        
        if state.errors:
            print(f"⚠️ {len(state.errors)} errors encountered while reading data")
    
    except Exception as e:
        error_msg = f"Failed to read data: {str(e)}"
        state.errors.append(error_msg)
        print(f"❌ {error_msg}")
    
    return state