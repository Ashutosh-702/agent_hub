"""
Progress Saver Node

Saves LinkedIn URLs and prospect data before HubSpot contact creation.
This provides a backup of all collected LinkedIn profiles in case HubSpot processing fails.
"""

import os
from typing import Dict, Any, List
from datetime import datetime
import csv
import json

from sdr.models import WorkflowState
from sdr.logging_config import clean_log, detailed_log


def save_linkedin_progress(state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
    """
    Save all LinkedIn URLs and prospect data before HubSpot processing
    
    Args:
        state: Current workflow state containing LinkedIn profiles
        config: Configuration dictionary with run directories
        
    Returns:
        Updated workflow state
    """

    # Clean log for main status
    clean_log("LinkedIn Progress Backup: Saving collected URLs")
    
    # Detailed logs
    detailed_log("LinkedIn Progress Backup Starting")
    detailed_log("Saving all collected LinkedIn URLs before HubSpot processing")

    try:
        # Get run directories from config
        config_dict = config.get("configurable", {})
        run_directories = config_dict.get("run_directories", {})
        progress_dir = run_directories.get("progress_dir", "output/progress")

        # Ensure directory exists
        os.makedirs(progress_dir, exist_ok=True)

        # Check if we have LinkedIn profiles
        if not hasattr(state, 'all_linkedin_profiles') or not state.all_linkedin_profiles:
            clean_log("No LinkedIn profiles to save", "warning")
            detailed_log("No LinkedIn profiles found to save", "warning")
            return state

        linkedin_profiles = state.all_linkedin_profiles

        # Generate timestamp for unique filenames
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Save LinkedIn URLs as CSV (for easy import to other tools)
        csv_filename = f"linkedin_urls_backup_{timestamp}.csv"
        csv_filepath = os.path.join(progress_dir, csv_filename)

        detailed_log(f"Saving LinkedIn URLs to CSV: {csv_filename}")
        detailed_log(f"  Total Profiles: {len(linkedin_profiles)}")
        detailed_log(f"  Location: {progress_dir}")

        with open(csv_filepath, 'w', encoding='utf-8', newline='') as f:
            fieldnames = [
                'Company Name', 'Person Name', 'Person Title', 'Person LinkedIn',
                'Seniority Level', 'Department', 'Profile Type', 'Email', 'Phone Number',
                'Collection Timestamp'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for profile in linkedin_profiles:
                writer.writerow({
                    'Company Name': profile.get('company_name', ''),
                    'Person Name': profile.get('name', ''),
                    'Person Title': profile.get('title', ''),
                    'Person LinkedIn': profile.get('linkedin_profile', ''),
                    'Seniority Level': profile.get('seniority_level', ''),
                    'Department': profile.get('department', ''),
                    'Profile Type': profile.get('profile_type', 'General'),
                    'Email': profile.get('email', ''),  # Usually empty at this stage
                    'Phone Number': profile.get('phone_number', ''),  # Usually empty at this stage
                    'Collection Timestamp': timestamp
                })

        # Save as JSON (for programmatic processing)
        json_filename = f"linkedin_profiles_backup_{timestamp}.json"
        json_filepath = os.path.join(progress_dir, json_filename)

        with open(json_filepath, 'w', encoding='utf-8') as f:
            backup_data = {
                "metadata": {
                    "run_id": run_directories.get("run_id", "unknown"),
                    "backup_timestamp": timestamp,
                    "total_profiles": len(linkedin_profiles),
                    "total_companies": len(set(profile.get('company_name', '') for profile in linkedin_profiles)),
                    "purpose": "Pre-HubSpot backup of all collected LinkedIn URLs"
                },
                "profiles": linkedin_profiles,
                "summary_by_company": _generate_company_summary(linkedin_profiles)
            }
            json.dump(backup_data, f, indent=2, ensure_ascii=False)

        # Generate summary statistics
        companies_with_profiles = set(profile.get('company_name', '') for profile in linkedin_profiles)
        executives_count = len([p for p in linkedin_profiles if p.get('profile_type') == 'Executive'])

        # Clean completion
        clean_log(f"LinkedIn backup completed: {len(linkedin_profiles)} profiles saved")
        
        # Detailed completion
        detailed_log("LinkedIn Progress Backup completed successfully")
        detailed_log(f"  CSV File: {csv_filename}")
        detailed_log(f"  JSON File: {json_filename}")
        detailed_log(f"  Total Profiles: {len(linkedin_profiles)}")
        detailed_log(f"  Companies: {len(companies_with_profiles)}")
        detailed_log(f"  Executive Profiles: {executives_count}")
        detailed_log(f"  Status: SUCCESS")

        # Detailed summary for verbose mode
        detailed_log("")
        detailed_log("💾 LinkedIn Progress Backup Completed")
        detailed_log("─" * 50)
        detailed_log(f"📊 Total LinkedIn URLs Saved: {len(linkedin_profiles)}")
        detailed_log(f"🏢 Companies with Profiles: {len(companies_with_profiles)}")
        detailed_log(f"👔 Executive Profiles: {executives_count}")
        detailed_log(f"📄 CSV Backup: {csv_filename}")
        detailed_log(f"🗂️ JSON Backup: {json_filename}")
        detailed_log(f"📁 Location: {progress_dir}")
        detailed_log("")

        # Add backup info to state for tracking
        if not hasattr(state, 'backup_files'):
            state.backup_files = []

        state.backup_files.extend([csv_filepath, json_filepath])

        return state

    except Exception as e:
        error_msg = f"Failed to save LinkedIn progress backup: {str(e)}"
        clean_log(f"LinkedIn backup failed: {str(e)}", "error")
        detailed_log(error_msg, "error")
        state.errors.append(error_msg)
        return state


def _generate_company_summary(linkedin_profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate summary statistics by company"""

    company_stats = {}

    for profile in linkedin_profiles:
        company = profile.get('company_name', 'Unknown')

        if company not in company_stats:
            company_stats[company] = {
                'total_profiles': 0,
                'executives': 0,
                'managers': 0,
                'other': 0,
                'linkedin_urls': []
            }

        company_stats[company]['total_profiles'] += 1
        company_stats[company]['linkedin_urls'].append(profile.get('linkedin_profile', ''))

        # Categorize by seniority
        seniority = profile.get('seniority_level', '').lower()
        profile_type = profile.get('profile_type', '').lower()

        if 'c-level' in seniority or 'ceo' in seniority or 'founder' in seniority or profile_type == 'executive':
            company_stats[company]['executives'] += 1
        elif 'manager' in seniority or 'director' in seniority or 'head' in seniority:
            company_stats[company]['managers'] += 1
        else:
            company_stats[company]['other'] += 1

    return company_stats


async def linkedin_progress_saver(state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
    """
    Async wrapper for LinkedIn progress saving (for LangGraph compatibility)
    
    Args:
        state: Current workflow state
        config: Configuration dictionary
        
    Returns:
        Updated workflow state
    """
    return save_linkedin_progress(state, config)
