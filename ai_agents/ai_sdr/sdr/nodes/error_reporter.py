"""
Error Reporter Node

Saves categorized error summaries to separate files for easy analysis and tracking.
"""

import csv
import json
import os
from datetime import datetime
from typing import Dict, Any

from ai_agents.ai_sdr.sdr.models import WorkflowState
from ai_agents.ai_sdr.sdr.logging_config import sdr_logger, clean_log, detailed_log


def save_error_summary(state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
    """
    Save categorized error summary to files
    
    Args:
        state: Current workflow state containing error summary
        config: Configuration dictionary with run directories
        
    Returns:
        Updated workflow state
    """
    
    sdr_logger.log_section_start(
        "Error Summary Export",
        "Saving categorized error reports"
    )
    
    try:
        run_directories = state.run_directories
        error_summary = state.error_summary
        
        # Create error reports directory
        error_reports_dir = os.path.join(run_directories["results_dir"], "error_reports")
        os.makedirs(error_reports_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. Save comprehensive error summary as JSON
        error_summary_file = os.path.join(error_reports_dir, f"error_summary_{timestamp}.json")
        
        summary_data = {
            "run_id": state.run_id,
            "timestamp": timestamp,
            "total_companies": len(state.companies),
            "error_counts": {
                "skipped_companies": len(error_summary.skipped_companies),
                "prospect_enrichment_failures": len(error_summary.prospect_enrichment_failures),
                "hubspot_failures": len(error_summary.hubspot_failures),
                "web_enrichment_failures": len(error_summary.web_enrichment_failures),
                "general_errors": len(error_summary.general_errors)
            },
            "detailed_errors": {
                "skipped_companies": error_summary.skipped_companies,
                "prospect_enrichment_failures": error_summary.prospect_enrichment_failures,
                "hubspot_failures": error_summary.hubspot_failures,
                "web_enrichment_failures": error_summary.web_enrichment_failures,
                "general_errors": error_summary.general_errors
            }
        }
        
        with open(error_summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        
        sdr_logger.log_file_saved(error_summary_file, "JSON error summary")
        
        # 2. Save skipped companies as CSV
        if error_summary.skipped_companies:
            skipped_file = os.path.join(error_reports_dir, f"skipped_companies_{timestamp}.csv")
            
            with open(skipped_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['company', 'reason', 'step'])
                writer.writeheader()
                writer.writerows(error_summary.skipped_companies)
            
            sdr_logger.log_file_saved(skipped_file, f"CSV report with {len(error_summary.skipped_companies)} skipped companies")
        
        # 3. Save LinkedIn failures as CSV
        if error_summary.prospect_enrichment_failures:
            linkedin_failures_file = os.path.join(error_reports_dir, f"linkedin_failures_{timestamp}.csv")
            
            with open(linkedin_failures_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['company', 'error', 'retry_count'])
                writer.writeheader()
                writer.writerows(error_summary.prospect_enrichment_failures)
            
            sdr_logger.log_file_saved(linkedin_failures_file, f"CSV report with {len(error_summary.prospect_enrichment_failures)} LinkedIn failures")
        
        # 4. Save HubSpot failures as CSV
        if error_summary.hubspot_failures:
            hubspot_failures_file = os.path.join(error_reports_dir, f"hubspot_failures_{timestamp}.csv")
            
            with open(hubspot_failures_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['contact', 'error'])
                writer.writeheader()
                writer.writerows(error_summary.hubspot_failures)
            
            sdr_logger.log_file_saved(hubspot_failures_file, f"CSV report with {len(error_summary.hubspot_failures)} HubSpot failures")
        
        # 5. Save web enrichment failures as CSV
        if error_summary.web_enrichment_failures:
            web_failures_file = os.path.join(error_reports_dir, f"web_failures_{timestamp}.csv")
            
            with open(web_failures_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['company', 'error'])
                writer.writeheader()
                writer.writerows(error_summary.web_enrichment_failures)
            
            sdr_logger.log_file_saved(web_failures_file, f"CSV report with {len(error_summary.web_enrichment_failures)} web enrichment failures")
        
        # Calculate totals
        total_errors = (len(error_summary.skipped_companies) + 
                       len(error_summary.prospect_enrichment_failures) + 
                       len(error_summary.hubspot_failures) + 
                       len(error_summary.web_enrichment_failures))
        
        # Update state with saved error report files
        error_report_files = [f for f in [error_summary_file, 
                                         skipped_file if error_summary.skipped_companies else None,
                                         linkedin_failures_file if error_summary.prospect_enrichment_failures else None,
                                         hubspot_failures_file if error_summary.hubspot_failures else None,
                                         web_failures_file if error_summary.web_enrichment_failures else None] if f]
        
        state.saved_files.extend(error_report_files)
        
        sdr_logger.log_completion(
            "Error Summary Export",
            {
                "Total Issues": total_errors,
                "Reports Created": len(error_report_files),
                "Output Directory": error_reports_dir
            }
        )
        
        clean_log(f"📊 Error summary export completed - {total_errors} issues categorized and saved")
        
    except Exception as e:
        error_msg = f"Error summary export failed: {str(e)}"
        sdr_logger.log_error_with_context(e, "Error Summary Export")
        state.error_summary.general_errors.append(error_msg)
        clean_log(error_msg, level="error")
    
    return state


# Async wrapper for workflow integration
async def error_reporter(state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
    """
    Async wrapper for error summary export
    """
    return save_error_summary(state, config) 