#!/usr/bin/env python3
"""
Main Designation Finder Workflow Runner

Reads companies from CSV/Google Sheets and runs individual workflows per company.
Each workflow appends results to a shared CSV file.
"""

import asyncio
import os
import sys
import csv
from datetime import datetime
from typing import Dict, Any, List

from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import set_default_openai_client

from ai_agents.designation_finder.models import DesignationFinderState, CompanyDesignation
from ai_agents.designation_finder.graph import compile_workflow
from ai_agents.designation_finder.nodes.company_designation_retriever import get_google_sheet_data


def create_output_directories() -> Dict[str, str]:
    """Create output directories for the run"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = f"designation_finder_{timestamp}"
    
    # Get the current directory (designation_finder) and create output path explicitly
    current_dir = os.path.dirname(os.path.abspath(__file__))  # designation_finder/
    base_dir = os.path.join(current_dir, "output", run_id)
    os.makedirs(base_dir, exist_ok=True)
    
    # Create shared CSV file path
    csv_file_path = os.path.join(base_dir, f"linkedin_profiles_{timestamp}.csv")
    
    directories = {
        "run_id": run_id,
        "base_dir": base_dir,
        "output_dir": base_dir,
        "csv_file_path": csv_file_path
    }
    
    print(f"📁 [MAIN] Output directory: {base_dir}")
    print(f"📄 [MAIN] Shared CSV file: {csv_file_path}")
    return directories


def load_configuration() -> Dict[str, Any]:
    """Load and validate configuration"""
    # Load .env from designation_finder directory (current workflow folder)
    current_dir = os.path.dirname(os.path.abspath(__file__))  # designation_finder/
    env_path = os.path.join(current_dir, '.env')
    
    print(f"🔍 Looking for .env file at: {env_path}")
    
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"✅ Loaded .env from: {env_path}")
    else:
        load_dotenv()  # Fallback to default behavior
        print(f"⚠️ .env file not found at {env_path}, using system environment variables")
    
    # Required configuration
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("❌ OPENAI_API_KEY not found in environment variables")
        print(f"Please set your OpenAI API key in .env file at: {env_path}")
        print("Add this line: OPENAI_API_KEY=your-actual-api-key-here")
        sys.exit(1)
    
    # Data source configuration
    google_sheet_url = os.getenv("GOOGLE_SHEET_URL")
    csv_file_path = os.getenv("CSV_FILE_PATH", "sample_input.csv")
    
    config = {
        "openai_api_key": openai_api_key,
        "google_sheet_url": google_sheet_url,
        "csv_file_path": csv_file_path
    }
    
    print(f"⚙️ Configuration loaded")
    print(f"   OpenAI API: ✅")
    if google_sheet_url:
        print(f"   Data source: Google Sheet")
    else:
        print(f"   Data source: Local CSV - {csv_file_path}")
    
    return config


def load_company_designations(config: Dict[str, Any]) -> List[CompanyDesignation]:
    """Load company designations from Google Sheets or local CSV"""
    company_designations = []
    
    google_sheet_url = config.get("google_sheet_url")
    csv_file_path = config.get("csv_file_path", "sample_input.csv")
    
    if google_sheet_url:
        print(f"📊 Loading companies from Google Sheet...")
        try:
            rows = get_google_sheet_data(google_sheet_url)
            
            if not rows:
                print("⚠️ No data found in Google Sheet, falling back to local CSV")
                google_sheet_url = None
            else:
                print(f"✅ Successfully loaded {len(rows)} rows from Google Sheet")
                
                # Check if first row is header
                has_header = False
                if rows and len(rows[0]) >= 2:
                    first_row = [str(cell).strip().lower() for cell in rows[0]]
                    has_header = (any('company' in cell for cell in first_row) and 
                                any('designation' in cell for cell in first_row))
                
                # Skip header if present
                start_row = 1 if has_header else 0
                
                for row_num, row in enumerate(rows[start_row:], start=start_row+1):
                    if not row or all(not str(cell).strip() for cell in row):
                        continue
                        
                    if len(row) < 2:
                        print(f"⚠️ Skipping row {row_num}: Expected at least 2 columns, got {len(row)}")
                        continue
                    
                    company_name = str(row[0]).strip()
                    designation = str(row[1]).strip()
                    
                    if not company_name or not designation:
                        print(f"⚠️ Skipping row {row_num}: Empty values")
                        continue
                    
                    company_designations.append(
                        CompanyDesignation(
                            company_name=company_name,
                            designation=designation
                        )
                    )
                
                print(f"✅ Loaded {len(company_designations)} companies from Google Sheet")
                
        except Exception as sheet_error:
            print(f"⚠️ Failed to access Google Sheet: {str(sheet_error)}")
            print("📄 Falling back to local CSV file...")
            google_sheet_url = None
    
    # Fallback to local CSV
    if not google_sheet_url or not company_designations:
        print(f"📄 Loading companies from local CSV: {csv_file_path}")
        
        if not os.path.exists(csv_file_path):
            print(f"❌ CSV file not found: {csv_file_path}")
            return []
        
        with open(csv_file_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            
            # Read first row to check if it's a header
            first_row = next(reader, None)
            if not first_row:
                print(f"❌ CSV file is empty: {csv_file_path}")
                return []
            
            # Check if first row looks like a header
            first_row_lower = [str(cell).strip().lower() for cell in first_row]
            has_header = (any('company' in cell for cell in first_row_lower) and
                        any('designation' in cell for cell in first_row_lower))
            
            # Process rows
            rows_to_process = []
            if not has_header:
                rows_to_process.append((1, first_row))
            
            for row_num, row in enumerate(reader, start=1 if has_header else 2):
                rows_to_process.append((row_num, row))
            
            for row_num, row in rows_to_process:
                if len(row) < 2:
                    print(f"⚠️ Skipping row {row_num}: Expected at least 2 columns, got {len(row)}")
                    continue
                
                company_name = row[0].strip()
                designation = row[1].strip()
                
                if not company_name or not designation:
                    print(f"⚠️ Skipping row {row_num}: Empty values")
                    continue
                
                company_designations.append(
                    CompanyDesignation(
                        company_name=company_name,
                        designation=designation
                    )
                )
        
        print(f"✅ Loaded {len(company_designations)} companies from {csv_file_path}")
    
    return company_designations


async def run_single_company_workflow(
    company_designation: CompanyDesignation, 
    config: Dict[str, Any], 
    run_directories: Dict[str, str]
) -> DesignationFinderState:
    """Run workflow for a single company"""
    
    company_name = company_designation.company_name
    designation = company_designation.designation
    
    print(f"🚀 [WORKFLOW] Starting single company workflow for {company_name}")
    print(f"📋 [WORKFLOW] Company: {company_name}")
    print(f"👔 [WORKFLOW] Designation: {designation}")
    
    try:
        # Step 1: Initialize state for single company
        print(f"🔧 [WORKFLOW] Step 1: Initializing workflow state")
        start_time = datetime.now()
        
        initial_state = DesignationFinderState(
            current_company_designation=company_designation,
            started_at=start_time,
            csv_file_path=run_directories["csv_file_path"],
            run_id=run_directories["run_id"],
            run_directories={**run_directories}
        )
        
        print(f"✅ [WORKFLOW] State initialized")
        print(f"⏰ [WORKFLOW] Start time: {start_time}")
        print(f"📄 [WORKFLOW] CSV file: {initial_state.csv_file_path}")
        print(f"🆔 [WORKFLOW] Run ID: {initial_state.run_id}")
        
        # Step 2: Create and compile workflow
        print(f"🏗️ [WORKFLOW] Step 2: Compiling workflow graph")
        workflow = compile_workflow()
        print(f"✅ [WORKFLOW] Workflow compiled successfully")
        
        # Step 3: Execute workflow
        print(f"▶️ [WORKFLOW] Step 3: Executing workflow")
        print(f"🔄 [WORKFLOW] Running LangGraph workflow for {company_name}...")
        
        final_state = await workflow.ainvoke(
            initial_state,
            config={"configurable": config, "recursion_limit": 100000}
        )
        
        # Step 4: Validate results
        print(f"🔍 [WORKFLOW] Step 4: Validating workflow results")
        execution_time = datetime.now() - start_time
        print(f"⏱️ [WORKFLOW] Execution time: {execution_time}")
        
        profiles_found = len(final_state.found_profiles) if final_state.found_profiles else 0
        print(f"📊 [WORKFLOW] Profiles found: {profiles_found}")
        print(f"✅ [WORKFLOW] Processing successful: {final_state.processing_successful}")
        print(f"❌ [WORKFLOW] Errors: {len(final_state.errors)}")
        
        if final_state.errors:
            for i, error in enumerate(final_state.errors, 1):
                print(f"   [WORKFLOW] Error {i}: {error}")
        
        print(f"🎉 [WORKFLOW] Workflow completed successfully for {company_name}")
        return final_state
        
    except Exception as e:
        execution_time = datetime.now() - start_time if 'start_time' in locals() else "Unknown"
        print(f"❌ [WORKFLOW] ERROR: Workflow failed for {company_name}")
        print(f"🔍 [WORKFLOW] Error details: {type(e).__name__}: {str(e)}")
        print(f"⏱️ [WORKFLOW] Failed after: {execution_time}")
        
        # Additional error context
        try:
            print(f"🔍 [WORKFLOW] Error context:")
            print(f"   - Company: {company_name}")
            print(f"   - Designation: {designation}")
            print(f"   - CSV file path: {run_directories.get('csv_file_path', 'N/A')}")
            print(f"   - Run ID: {run_directories.get('run_id', 'N/A')}")
        except Exception as ctx_error:
            print(f"⚠️ [WORKFLOW] Could not gather error context: {ctx_error}")
        
        # Create error state
        error_state = DesignationFinderState(
            current_company_designation=company_designation,
            started_at=datetime.now(),
            completed_at=datetime.now(),
            csv_file_path=run_directories["csv_file_path"],
            errors=[f"Workflow failed: {str(e)}"]
        )
        
        print(f"🔄 [WORKFLOW] Created error state for failed workflow")
        return error_state


async def main():
    """Main entry point - processes all companies individually"""
    try:
        print("🎯 LinkedIn Designation Finder - Multi-Company Processing")
        print("=" * 60)
        
        # Create output directories
        run_directories = create_output_directories()
        
        # Load configuration
        config = load_configuration()
        
        # Initialize OpenAI client
        openai_client = AsyncOpenAI(api_key=config['openai_api_key'])
        set_default_openai_client(openai_client)
        
        # Load all companies
        company_designations = load_company_designations(config)
        
        if not company_designations:
            print("❌ No companies found to process")
            return
        
        print(f"🚀 Starting processing for {len(company_designations)} companies")
        print("=" * 60)
        
        # Process each company individually
        print(f"🔄 [MAIN] Starting sequential processing of companies")
        total_processed = 0
        total_errors = 0
        start_time = datetime.now()
        
        for i, company_designation in enumerate(company_designations, 1):
            company_name = company_designation.company_name
            designation = company_designation.designation
            
            print(f"\n{'='*80}")
            print(f"🏢 [MAIN] COMPANY {i}/{len(company_designations)}: {company_name}")
            print(f"👔 [MAIN] DESIGNATION: {designation}")
            print(f"⏰ [MAIN] Starting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*80}")
            
            company_start_time = datetime.now()
            
            try:
                print(f"🚀 [MAIN] Launching workflow for {company_name}")
                
                final_state = await run_single_company_workflow(
                    company_designation, config, run_directories
                )
                
                company_duration = datetime.now() - company_start_time
                print(f"⏱️ [MAIN] Company processing time: {company_duration}")
                
                # Detailed result analysis
                profiles_found = len(final_state.found_profiles) if final_state.found_profiles else 0
                has_errors = len(final_state.errors) > 0
                
                print(f"📊 [MAIN] Results summary for {company_name}:")
                print(f"   - Profiles found: {profiles_found}")
                print(f"   - Processing successful: {final_state.processing_successful}")
                print(f"   - Errors: {len(final_state.errors)}")
                print(f"   - CSV logged: {final_state.processing_successful}")
                
                if final_state.processing_successful:
                    total_processed += 1
                    print(f"✅ [MAIN] Successfully processed {company_name}")
                    
                    if profiles_found > 0:
                        print(f"🎉 [MAIN] Found {profiles_found} LinkedIn profiles!")
                    else:
                        print(f"⚠️ [MAIN] No profiles found, but logged to CSV")
                        
                else:
                    total_errors += 1
                    print(f"❌ [MAIN] Processing failed for {company_name}")
                
                if final_state.errors:
                    print(f"⚠️ [MAIN] Errors encountered:")
                    for j, error in enumerate(final_state.errors, 1):
                        print(f"   {j}. {error}")
                
                # Progress summary
                remaining = len(company_designations) - i
                elapsed = datetime.now() - start_time
                avg_time_per_company = elapsed / i
                estimated_remaining = avg_time_per_company * remaining
                
                print(f"📈 [MAIN] Progress update:")
                print(f"   - Completed: {i}/{len(company_designations)} ({(i/len(company_designations)*100):.1f}%)")
                print(f"   - Successful: {total_processed}")
                print(f"   - Errors: {total_errors}")
                print(f"   - Elapsed time: {elapsed}")
                print(f"   - Avg time per company: {avg_time_per_company}")
                print(f"   - Estimated remaining time: {estimated_remaining}")
                
            except Exception as e:
                company_duration = datetime.now() - company_start_time
                total_errors += 1
                
                print(f"❌ [MAIN] CRITICAL ERROR processing {company_name}")
                print(f"🔍 [MAIN] Error details: {type(e).__name__}: {str(e)}")
                print(f"⏱️ [MAIN] Failed after: {company_duration}")
                
                # Error context
                print(f"🔍 [MAIN] Error context:")
                print(f"   - Company: {company_name}")
                print(f"   - Designation: {designation}")
                print(f"   - Company index: {i}/{len(company_designations)}")
                print(f"   - Total processed so far: {total_processed}")
                print(f"   - Total errors so far: {total_errors}")
            
            print(f"🔚 [MAIN] Completed processing {company_name}")
            print(f"{'='*80}\n")
        
        # Print final summary
        print("\n" + "=" * 60)
        print("🎯 FINAL PROCESSING SUMMARY")
        print("=" * 60)
        print(f"📊 Total companies: {len(company_designations)}")
        print(f"✅ Successfully processed: {total_processed}")
        print(f"❌ Errors: {total_errors}")
        print(f"📄 Results logged to: {run_directories['csv_file_path']}")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n⚠️ Processing interrupted by user")
        
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProcessing interrupted by user")
    except Exception as e:
        print(f"Fatal error: {str(e)}")