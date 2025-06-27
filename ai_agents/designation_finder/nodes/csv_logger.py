"""
CSV Logger Node
Appends LinkedIn profile data to a CSV file after each company is processed
"""
import os
import csv
from datetime import datetime
from ai_agents.designation_finder.models import DesignationFinderState


def csv_logger(state: DesignationFinderState) -> DesignationFinderState:
    """
    Log found LinkedIn profiles to CSV file (append mode)
    Creates file with headers if it doesn't exist, otherwise appends data
    """
    company_name = state.current_company_designation.company_name if state.current_company_designation else "Unknown"
    designation = state.current_company_designation.designation if state.current_company_designation else "Unknown"
    
    print(f"📝 [CSV_LOGGER] Starting CSV logging for {company_name} ({designation})")
    
    try:
        # Step 1: Validate CSV file path
        print(f"🔍 [CSV_LOGGER] Step 1: Validating CSV file path")
        if not state.csv_file_path:
            error_msg = "No CSV file path specified for logging"
            state.errors.append(error_msg)
            print(f"❌ [CSV_LOGGER] {error_msg}")
            return state
        
        print(f"✅ [CSV_LOGGER] CSV file path validated: {state.csv_file_path}")
        
        # Step 2: Ensure directory exists
        print(f"📁 [CSV_LOGGER] Step 2: Ensuring output directory exists")
        output_dir = os.path.dirname(state.csv_file_path)
        print(f"🔍 [CSV_LOGGER] Output directory: {output_dir}")
        
        os.makedirs(output_dir, exist_ok=True)
        print(f"✅ [CSV_LOGGER] Output directory confirmed/created")
        
        # Step 3: Check if file exists to determine if we need headers
        print(f"🔍 [CSV_LOGGER] Step 3: Checking if CSV file already exists")
        file_exists = os.path.exists(state.csv_file_path)
        print(f"📄 [CSV_LOGGER] File exists: {file_exists}")
        
        # Step 4: Prepare data for logging
        print(f"📊 [CSV_LOGGER] Step 4: Preparing data for logging")
        profiles_count = len(state.found_profiles) if state.found_profiles else 0
        print(f"🔢 [CSV_LOGGER] Found {profiles_count} profiles to log")
        
        if state.found_profiles:
            for i, profile in enumerate(state.found_profiles, 1):
                print(f"   [CSV_LOGGER] Profile {i}: {profile.name} - {profile.linkedin_url}")
        else:
            print(f"⚠️ [CSV_LOGGER] No profiles found for {company_name}")
        
        # Step 5: Open file and write data
        print(f"📝 [CSV_LOGGER] Step 5: Opening CSV file for writing")
        with open(state.csv_file_path, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            print(f"✅ [CSV_LOGGER] CSV file opened successfully")
            
            # Write header if file is new
            if not file_exists:
                print(f"📋 [CSV_LOGGER] Writing CSV headers (new file)")
                headers = ['Name', 'LinkedIn_URL', 'Title', 'Company_Name', 'Designation_Searched', 'Processed_At']
                writer.writerow(headers)
                print(f"✅ [CSV_LOGGER] Headers written: {headers}")
                print(f"📄 [CSV_LOGGER] Created new CSV file: {state.csv_file_path}")
            else:
                print(f"📄 [CSV_LOGGER] Appending to existing CSV file")
            
            # Write profile data for current company
            processed_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"⏰ [CSV_LOGGER] Processing timestamp: {processed_at}")
            
            if state.found_profiles:
                print(f"✍️ [CSV_LOGGER] Writing {len(state.found_profiles)} profile records")
                
                for i, profile in enumerate(state.found_profiles, 1):
                    row_data = [
                        profile.name,
                        profile.linkedin_url,
                        profile.title or '',
                        profile.company_name,
                        profile.designation_searched,
                        processed_at
                    ]
                    writer.writerow(row_data)
                    print(f"   [CSV_LOGGER] Written profile {i}: {profile.name}")
                
                print(f"✅ [CSV_LOGGER] Successfully logged {len(state.found_profiles)} profiles for {company_name}")
                state.processing_successful = True
                
            else:
                # Log company even if no profiles found
                print(f"⚠️ [CSV_LOGGER] No profiles found - logging empty result")
                no_result_row = [
                    'No profiles found',
                    '',
                    '',
                    company_name,
                    designation,
                    processed_at
                ]
                writer.writerow(no_result_row)
                print(f"✅ [CSV_LOGGER] Logged no-results entry for {company_name}")
                state.processing_successful = True
        
        # Step 6: Finalize logging
        print(f"🏁 [CSV_LOGGER] Step 6: Finalizing logging process")
        state.completed_at = datetime.now()
        print(f"⏰ [CSV_LOGGER] Completion time set: {state.completed_at}")
        
        print(f"🎉 [CSV_LOGGER] CSV logging completed successfully for {company_name}")
        
    except Exception as e:
        error_msg = f"Failed to log to CSV: {str(e)}"
        state.errors.append(error_msg)
        print(f"❌ [CSV_LOGGER] ERROR: {error_msg}")
        print(f"🔍 [CSV_LOGGER] Error details: {type(e).__name__}: {str(e)}")
        
        # Additional error context
        try:
            print(f"🔍 [CSV_LOGGER] Error context:")
            print(f"   - CSV file path: {state.csv_file_path}")
            print(f"   - Company: {company_name}")
            print(f"   - Profiles count: {len(state.found_profiles) if state.found_profiles else 0}")
            print(f"   - Output directory exists: {os.path.exists(os.path.dirname(state.csv_file_path)) if state.csv_file_path else 'N/A'}")
        except Exception as ctx_error:
            print(f"⚠️ [CSV_LOGGER] Could not gather error context: {ctx_error}")
    
    print(f"🔚 [CSV_LOGGER] CSV logger node execution completed for {company_name}")
    return state