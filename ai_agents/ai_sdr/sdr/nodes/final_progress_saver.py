"""
Final Progress Saver Node

Saves complete workflow results after all processing is finished.
Creates comprehensive final reports and consolidated data files.
"""

import csv
import json
import os
from datetime import datetime
from typing import Dict, Any, List

from ai_agents.ai_sdr.sdr.logging_config import clean_log, detailed_log, sdr_logger
from ai_agents.ai_sdr.sdr.models import WorkflowState


def save_final_workflow_results(state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
    """
    Save complete workflow results to final directory
    
    Args:
        state: Final workflow state with all processing complete
        config: Configuration dictionary with run directories
        
    Returns:
        Updated workflow state
    """
    
    # Clean log for main status
    clean_log("Saving final workflow results")
    
    # Detailed logs
    detailed_log("Saving final workflow results and comprehensive reports")

    try:
        # Get run directories from config
        config_dict = config.get("configurable", {})
        run_directories = config_dict.get("run_directories", {})
        final_dir = run_directories.get("final_dir", "output/final")
        run_id = run_directories.get("run_id", "unknown")

        # Ensure directory exists
        os.makedirs(final_dir, exist_ok=True)

        # Generate timestamp for final files
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 1. Save comprehensive workflow results as JSON
        workflow_results = _create_comprehensive_workflow_data(state, run_id, timestamp)
        
        workflow_filename = f"complete_workflow_{run_id}_{timestamp}.json"
        workflow_filepath = os.path.join(final_dir, workflow_filename)
        
        with open(workflow_filepath, 'w', encoding='utf-8') as f:
            json.dump(workflow_results, f, indent=2, ensure_ascii=False, default=str)
        
        sdr_logger.log_file_saved(workflow_filepath, "Complete workflow results")
        
        # 2. Save successful LinkedIn profiles as CSV
        successful_linkedin, failed_linkedin = _separate_linkedin_results(state)
        
        success_csv_filename = f"linkedin_prospects_success_final_{run_id}_{timestamp}.csv"
        success_csv_filepath = os.path.join(final_dir, success_csv_filename)
        if successful_linkedin:
            _save_linkedin_profiles_csv(successful_linkedin, success_csv_filepath)
            sdr_logger.log_file_saved(success_csv_filepath, f"Successful LinkedIn prospects CSV ({len(successful_linkedin)} profiles)")
        
        failure_csv_filename = f"linkedin_prospects_failures_final_{run_id}_{timestamp}.csv"
        failure_csv_filepath = os.path.join(final_dir, failure_csv_filename)
        if failed_linkedin:
            _save_linkedin_failures_csv(failed_linkedin, failure_csv_filepath)
            sdr_logger.log_file_saved(failure_csv_filepath, f"Failed LinkedIn searches CSV ({len(failed_linkedin)} companies)")
        
        # 3. Save HubSpot contacts separated by success/failure
        successful_hubspot, failed_hubspot = _separate_hubspot_results(state)
        
        hubspot_success_filename = f"hubspot_contacts_success_final_{run_id}_{timestamp}.csv"
        hubspot_success_filepath = os.path.join(final_dir, hubspot_success_filename)
        if successful_hubspot:
            _save_hubspot_contacts_csv(successful_hubspot, hubspot_success_filepath)
            sdr_logger.log_file_saved(hubspot_success_filepath, f"Successful HubSpot contacts CSV ({len(successful_hubspot)} contacts)")
        
        hubspot_failure_filename = f"hubspot_contacts_failures_final_{run_id}_{timestamp}.csv"
        hubspot_failure_filepath = os.path.join(final_dir, hubspot_failure_filename)
        if failed_hubspot:
            _save_hubspot_failures_csv(failed_hubspot, hubspot_failure_filepath)
            sdr_logger.log_file_saved(hubspot_failure_filepath, f"Failed HubSpot contacts CSV ({len(failed_hubspot)} failures)")
        
        # 4. Save workflow summary report
        summary_data = _create_workflow_summary(state, run_id, timestamp)
        
        summary_filename = f"workflow_summary_{run_id}_{timestamp}.json"
        summary_filepath = os.path.join(final_dir, summary_filename)
        
        with open(summary_filepath, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False, default=str)
        
        sdr_logger.log_file_saved(summary_filepath, "Workflow summary report")
        
        # Log completion
        clean_log("Final workflow results saved")
        detailed_log("Final workflow results saved successfully")
        detailed_log(f"  Complete workflow data: {workflow_filename}")
        if successful_linkedin:
            detailed_log(f"  LinkedIn success CSV: {success_csv_filename} ({len(successful_linkedin)} profiles)")
        if failed_linkedin:
            detailed_log(f"  LinkedIn failures CSV: {failure_csv_filename} ({len(failed_linkedin)} companies)")
        if successful_hubspot:
            detailed_log(f"  HubSpot success CSV: {hubspot_success_filename} ({len(successful_hubspot)} contacts)")
        if failed_hubspot:
            detailed_log(f"  HubSpot failures CSV: {hubspot_failure_filename} ({len(failed_hubspot)} failures)")
        detailed_log(f"  Workflow summary: {summary_filename}")
        detailed_log(f"  Location: {final_dir}")
        
        # Track in state
        if not hasattr(state, 'final_progress_files'):
            state.final_progress_files = []
        
        final_files = [workflow_filepath, summary_filepath]
        if successful_linkedin:
            final_files.append(success_csv_filepath)
        if failed_linkedin:
            final_files.append(failure_csv_filepath)
        if successful_hubspot:
            final_files.append(hubspot_success_filepath)
        if failed_hubspot:
            final_files.append(hubspot_failure_filepath)
            
        state.final_progress_files.extend(final_files)

        return state

    except Exception as e:
        error_msg = f"Failed to save final workflow results: {str(e)}"
        clean_log(f"Final results save failed: {str(e)}", "error")
        detailed_log(error_msg, "error")
        state.errors.append(error_msg)
        return state


def _create_comprehensive_workflow_data(state: WorkflowState, run_id: str, timestamp: str) -> Dict[str, Any]:
    """Create comprehensive workflow data structure"""
    
    return {
        "workflow_metadata": {
            "run_id": run_id,
            "completion_timestamp": timestamp,
            "started_at": getattr(state, 'started_at', None),
            "completed_at": getattr(state, 'completed_at', None),
            "total_companies": len(state.companies) if state.companies else 0,
            "total_errors": len(state.errors) if state.errors else 0
        },
        "company_processing_results": {
            company.name: state.enriched_data.get(company.name, {})
            for company in (state.companies or [])
        },
        "linkedin_summary": {
            "total_profiles_collected": len(state.all_linkedin_profiles) if hasattr(state, 'all_linkedin_profiles') else 0,
            "companies_with_profiles": len(set(
                profile.get('company_name', '') for profile in (state.all_linkedin_profiles or [])
            )) if hasattr(state, 'all_linkedin_profiles') else 0,
            "executives_found": len([
                p for p in (state.all_linkedin_profiles or []) 
                if p.get('profile_type') == 'Executive'
            ]) if hasattr(state, 'all_linkedin_profiles') else 0
        },
        "hubspot_summary": _create_hubspot_summary(state),
        "error_summary": {
            "general_errors": state.errors or [],
            "categorized_errors": state.error_summary.__dict__ if hasattr(state, 'error_summary') else {}
        },
        "progress_tracking": {
            "company_progress_files": getattr(state, 'company_progress_files', []),
            "linkedin_save_count": getattr(state, 'linkedin_save_count', 0),
            "hubspot_save_count": getattr(state, 'hubspot_save_count', 0)
        },
        "all_linkedin_profiles": state.all_linkedin_profiles if hasattr(state, 'all_linkedin_profiles') else []
    }


def _create_hubspot_summary(state: WorkflowState) -> Dict[str, Any]:
    """Create HubSpot processing summary"""
    
    hubspot_summary = {
        "total_contacts_processed": 0,
        "successful_creations": 0,
        "failed_creations": 0,
        "duplicates_found": 0
    }
    
    # Aggregate HubSpot results from all companies
    for company_data in (state.enriched_data or {}).values():
        hubspot_results = company_data.get('hubspot_results', {})
        if hubspot_results:
            hubspot_summary["successful_creations"] += hubspot_results.get('created_count', 0)
            hubspot_summary["duplicates_found"] += hubspot_results.get('duplicate_count', 0)
            hubspot_summary["failed_creations"] += hubspot_results.get('failed_count', 0)
    
    hubspot_summary["total_contacts_processed"] = (
        hubspot_summary["successful_creations"] + 
        hubspot_summary["failed_creations"] + 
        hubspot_summary["duplicates_found"]
    )
    
    return hubspot_summary


def _create_workflow_summary(state: WorkflowState, run_id: str, timestamp: str) -> Dict[str, Any]:
    """Create workflow summary report"""
    
    # Calculate processing statistics
    total_companies = len(state.companies) if state.companies else 0
    companies_processed = len(state.enriched_data) if state.enriched_data else 0
    
    relevant_companies = 0
    skipped_companies = 0
    
    for company_data in (state.enriched_data or {}).values():
        web_analysis = company_data.get('web_search_analysis', {})
        is_relevant = web_analysis.get('relevance_assessment', {}).get('is_relevant', False)
        if is_relevant:
            relevant_companies += 1
        else:
            skipped_companies += 1
    
    return {
        "summary_metadata": {
            "run_id": run_id,
            "summary_timestamp": timestamp,
            "workflow_version": "enhanced_with_progress_tracking"
        },
        "processing_statistics": {
            "total_companies_loaded": total_companies,
            "companies_processed": companies_processed,
            "relevant_companies_found": relevant_companies,
            "companies_skipped": skipped_companies,
            "processing_completion_rate": f"{(companies_processed/total_companies*100):.1f}%" if total_companies > 0 else "0%"
        },
        "linkedin_statistics": {
            "total_profiles_collected": len(state.all_linkedin_profiles) if hasattr(state, 'all_linkedin_profiles') else 0,
            "linkedin_save_operations": getattr(state, 'linkedin_save_count', 0)
        },
        "hubspot_statistics": _create_hubspot_summary(state),
        "error_statistics": {
            "total_errors": len(state.errors) if state.errors else 0,
            "error_categories": {
                "skipped_companies": len(getattr(state.error_summary, 'skipped_companies', [])) if hasattr(state, 'error_summary') else 0,
                "linkedin_failures": len(getattr(state.error_summary, 'prospect_enrichment_failures', [])) if hasattr(state, 'error_summary') else 0,
                "hubspot_failures": len(getattr(state.error_summary, 'hubspot_failures', [])) if hasattr(state, 'error_summary') else 0,
                "web_failures": len(getattr(state.error_summary, 'web_enrichment_failures', [])) if hasattr(state, 'error_summary') else 0
            }
        },
        "file_tracking": {
            "progress_files_created": len(getattr(state, 'company_progress_files', [])),
            "final_files_created": len(getattr(state, 'final_progress_files', []))
        }
    }


def _save_linkedin_profiles_csv(profiles: List[Dict[str, Any]], filepath: str):
    """Save LinkedIn profiles to CSV file"""
    
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        fieldnames = [
            'Company Name', 'Person Name', 'Person Title', 'Person LinkedIn',
            'Seniority Level', 'Department', 'Profile Type', 'Email', 'Phone Number'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for profile in profiles:
            writer.writerow({
                'Company Name': profile.get('company_name', ''),
                'Person Name': profile.get('name', ''),
                'Person Title': profile.get('title', ''),
                'Person LinkedIn': profile.get('linkedin_profile', ''),
                'Seniority Level': profile.get('seniority_level', ''),
                'Department': profile.get('department', ''),
                'Profile Type': profile.get('profile_type', 'General'),
                'Email': profile.get('email', ''),
                'Phone Number': profile.get('phone_number', '')
            })


def _extract_hubspot_contacts(state: WorkflowState) -> List[Dict[str, Any]]:
    """Extract HubSpot contacts from workflow state"""
    
    hubspot_contacts = []
    
    for company_data in (state.enriched_data or {}).values():
        hubspot_results = company_data.get('hubspot_results', {})
        if hubspot_results:
            # Add created contacts
            created_contacts = hubspot_results.get('created_contacts', [])
            hubspot_contacts.extend(created_contacts)
    
    return hubspot_contacts


def _save_hubspot_contacts_csv(contacts: List[Dict[str, Any]], filepath: str):
    """Save HubSpot contacts to CSV file"""
    
    if not contacts:
        return
    
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        # Get all possible fieldnames from contacts
        all_fieldnames = set()
        for contact in contacts:
            all_fieldnames.update(contact.keys())
        
        fieldnames = sorted(list(all_fieldnames))
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for contact in contacts:
            writer.writerow(contact)


def _separate_linkedin_results(state: WorkflowState) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Separate successful LinkedIn profiles from failed searches"""
    
    successful = []
    failed = []
    
    # Collect all successful LinkedIn profiles
    if hasattr(state, 'all_linkedin_profiles') and state.all_linkedin_profiles:
        successful.extend(state.all_linkedin_profiles)
    
    # Collect failed LinkedIn searches from error summary
    if hasattr(state, 'error_summary'):
        for failure in state.error_summary.prospect_enrichment_failures:
            failed.append({
                'company': failure.get('company', ''),
                'error': failure.get('error', ''),
                'retry_count': failure.get('retry_count', '')
            })
    
    return successful, failed


def _save_linkedin_failures_csv(failures: List[Dict[str, Any]], filepath: str):
    """Save failed LinkedIn searches to CSV file"""
    
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['Company', 'Error', 'Retry Count']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for failure in failures:
            writer.writerow({
                'Company': failure.get('company', ''),
                'Error': failure.get('error', ''),
                'Retry Count': failure.get('retry_count', '')
            })


def _separate_hubspot_results(state: WorkflowState) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Separate successful HubSpot contacts from failed ones"""
    
    successful = []
    failed = []
    
    for company_data in (state.enriched_data or {}).values():
        hubspot_results = company_data.get('hubspot_results', {})
        if hubspot_results:
            # Add successful contacts
            created_contacts = hubspot_results.get('created_contacts', [])
            successful.extend(created_contacts)
            
            # Add failed contacts
            failed_contacts = hubspot_results.get('failed_contacts', [])
            failed.extend(failed_contacts)
    
    return successful, failed


def _save_hubspot_failures_csv(failures: List[Dict[str, Any]], filepath: str):
    """Save failed HubSpot contacts to CSV file"""
    
    if not failures:
        return
    
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['Name', 'Email', 'LinkedIn URL', 'Company', 'Error', 'Status']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for failure in failures:
            writer.writerow({
                'Name': failure.get('name', ''),
                'Email': failure.get('email', ''),
                'LinkedIn URL': failure.get('linkedin_url', failure.get('hs_linkedin_url', '')),
                'Company': failure.get('company', ''),
                'Error': failure.get('error', ''),
                'Status': failure.get('status', 'Failed')
            })


# Async wrapper for LangGraph compatibility
async def final_progress_saver(state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
    """
    Async wrapper for final progress saving
    """
    return save_final_workflow_results(state, config)