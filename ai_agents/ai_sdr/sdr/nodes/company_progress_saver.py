"""
Company Progress Saver Node

Saves progress after LinkedIn and HubSpot processing for each individual company.
This provides incremental backups and enables workflow recovery if needed.
"""

import csv
import json
import os
from datetime import datetime
from typing import Dict, Any, List
import requests
from ai_agents.ai_sdr.sdr.logging_config import clean_log, detailed_log, sdr_logger
from ai_agents.ai_sdr.sdr.models import WorkflowState
from config.loaded_config import loaded_config

def save_company_linkedin_progress(state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
    """
    Save company progress after LinkedIn processing
    
    Args:
        state: Current workflow state with LinkedIn data for current company
        config: Configuration dictionary with run directories
        
    Returns:
        Updated workflow state
    """
    
    if not state.current_company:
        detailed_log("No current company to save LinkedIn progress for", "warning")
        return state
    
    company = state.current_company
    
    # Clean log for main status
    clean_log(f"Saving LinkedIn progress: {company.name}")
    
    # Detailed logs
    detailed_log(f"Saving LinkedIn progress for company: {company.name}")

    try:
        # Get run directories from config
        config_dict = config.get("configurable", {})
        run_directories = config_dict.get("run_directories", {})
        progress_dir = run_directories.get("progress_dir", "output/progress")

        # Ensure directory exists
        os.makedirs(progress_dir, exist_ok=True)

        # Get enriched data for this company
        company_data = state.enriched_data.get(company.name, {})
        
        # Generate timestamp for unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create safe filename from company name
        safe_company_name = "".join(c for c in company.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_company_name = safe_company_name.replace(' ', '_')[:50]  # Limit length
        
        # Create progress data structure
        progress_data = {
            "metadata": {
                "run_id": run_directories.get("run_id", "unknown"),
                "company_name": company.name,
                "processing_step": "linkedin_completed",
                "save_timestamp": timestamp,
                "company_index": state.current_company_index,
                "total_companies": len(state.companies)
            },
            "company_info": {
                "name": company.name,
                "website": getattr(company, 'website', None),
                "domain": getattr(company, 'domain', None),
                "industry": getattr(company, 'industry', None),
                "size": getattr(company, 'size', None),
                "location": getattr(company, 'location', None),
                "description": getattr(company, 'description', None),
                "linkedin_url": getattr(company, 'linkedin_url', None)
            },
            "web_analysis": company_data.get('web_search_analysis', {}),
            "linkedin_data": company_data.get('linkedin_prospect_data', {}),
            "processing_status": {
                "web_enrichment_completed": 'web_search_analysis' in company_data,
                "linkedin_enrichment_completed": 'linkedin_prospect_data' in company_data,
                "hubspot_processing_completed": False
            }
        }
        
        # Save LinkedIn progress file
        filename = f"company_{safe_company_name}_linkedin_{timestamp}.json"
        filepath = os.path.join(progress_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, indent=2, ensure_ascii=False, default=str)
        
        # Save LinkedIn prospects as CSV
        linkedin_data = company_data.get('linkedin_prospect_data', {})
        executives_found = linkedin_data.get('executives_found', [])
        
        if executives_found:
            csv_filename = f"company_{safe_company_name}_prospects_{timestamp}.csv"
            csv_filepath = os.path.join(progress_dir, csv_filename)
            data_source_type = config_dict.get("data_source",{}).get("type","")
            campaign_id = config_dict.get("data_source",{}).get("campaign_id","")
            company_id = getattr(state.current_company, "company_id", None)
            if data_source_type == "mongo":
                _save_company_prospects_mongo(executives_found,company.name,campaign_id=campaign_id,company_id=company_id)
                clean_log("Stored in Database")
            _save_company_prospects_csv(executives_found, company.name, csv_filepath)
            sdr_logger.log_file_saved(csv_filepath, f"LinkedIn prospects CSV for {company.name}")
            detailed_log(f"LinkedIn prospects CSV saved to: {csv_filename}")
            
            # Track CSV file
            state.company_progress_files.append(csv_filepath)
        
        # Log success
        sdr_logger.log_file_saved(filepath, f"LinkedIn progress for {company.name}")
        clean_log(f"LinkedIn progress saved: {company.name}")
        detailed_log(f"LinkedIn progress saved to: {filename}")
        
        # Track in state
        if not hasattr(state, 'company_progress_files'):
            state.company_progress_files = []
        state.company_progress_files.append(filepath)
        
        # Update LinkedIn save count
        if not hasattr(state, 'linkedin_save_count'):
            state.linkedin_save_count = 0
        state.linkedin_save_count += 1

        return state

    except Exception as e:
        error_msg = f"Failed to save LinkedIn progress for {company.name}: {str(e)}"
        clean_log(f"LinkedIn progress save failed: {company.name}", "error")
        detailed_log(error_msg, "error")
        state.errors.append(error_msg)
        return state


def save_company_hubspot_progress(state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
    """
    Save company progress after HubSpot processing
    
    Args:
        state: Current workflow state with HubSpot data for current company
        config: Configuration dictionary with run directories
        
    Returns:
        Updated workflow state
    """
    
    if not state.current_company:
        detailed_log("No current company to save HubSpot progress for", "warning")
        return state
    
    company = state.current_company
    
    # Clean log for main status
    clean_log(f"Saving HubSpot progress: {company.name}")
    
    # Detailed logs
    detailed_log(f"Saving HubSpot progress for company: {company.name}")

    try:
        # Get run directories from config
        config_dict = config.get("configurable", {})
        run_directories = config_dict.get("run_directories", {})
        progress_dir = run_directories.get("progress_dir", "output/progress")

        # Ensure directory exists
        os.makedirs(progress_dir, exist_ok=True)

        # Get enriched data for this company
        company_data = state.enriched_data.get(company.name, {})
        
        # Generate timestamp for unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create safe filename from company name
        safe_company_name = "".join(c for c in company.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_company_name = safe_company_name.replace(' ', '_')[:50]  # Limit length
        
        # Create progress data structure
        progress_data = {
            "metadata": {
                "run_id": run_directories.get("run_id", "unknown"),
                "company_name": company.name,
                "processing_step": "hubspot_completed",
                "save_timestamp": timestamp,
                "company_index": state.current_company_index,
                "total_companies": len(state.companies)
            },
            "company_info": {
                "name": company.name,
                "website": getattr(company, 'website', None),
                "domain": getattr(company, 'domain', None),
                "industry": getattr(company, 'industry', None),
                "size": getattr(company, 'size', None),
                "location": getattr(company, 'location', None),
                "description": getattr(company, 'description', None),
                "linkedin_url": getattr(company, 'linkedin_url', None)
            },
            "web_analysis": company_data.get('web_search_analysis', {}),
            "linkedin_data": company_data.get('linkedin_prospect_data', {}),
            "hubspot_results": company_data.get('hubspot_results', {}),
            "processing_status": {
                "web_enrichment_completed": 'web_search_analysis' in company_data,
                "linkedin_enrichment_completed": 'linkedin_prospect_data' in company_data,
                "hubspot_processing_completed": 'hubspot_results' in company_data
            }
        }
        
        # Save HubSpot progress file
        filename = f"company_{safe_company_name}_hubspot_{timestamp}.json"
        filepath = os.path.join(progress_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, indent=2, ensure_ascii=False, default=str)
        
        # Log success
        sdr_logger.log_file_saved(filepath, f"HubSpot progress for {company.name}")
        clean_log(f"HubSpot progress saved: {company.name}")
        detailed_log(f"HubSpot progress saved to: {filename}")
        
        # Track in state
        if not hasattr(state, 'company_progress_files'):
            state.company_progress_files = []
        state.company_progress_files.append(filepath)
        
        # Update HubSpot save count
        if not hasattr(state, 'hubspot_save_count'):
            state.hubspot_save_count = 0
        state.hubspot_save_count += 1

        return state

    except Exception as e:
        error_msg = f"Failed to save HubSpot progress for {company.name}: {str(e)}"
        clean_log(f"HubSpot progress save failed: {company.name}", "error")
        detailed_log(error_msg, "error")
        state.errors.append(error_msg)
        return state


def _save_company_prospects_csv(prospects: List[Dict[str, Any]], company_name: str, filepath: str):
    """Save company's LinkedIn prospects to CSV file"""
    
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        fieldnames = [
            'Company Name', 'Person Name', 'Person Title', 'Person LinkedIn',
            'Seniority Level', 'Department', 'Company LinkedIn URL'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for prospect in prospects:
            writer.writerow({
                'Company Name': company_name,
                'Person Name': prospect.get('name', ''),
                'Person Title': prospect.get('title', ''),
                'Person LinkedIn': prospect.get('linkedin_profile', ''),
                'Seniority Level': prospect.get('seniority_level', ''),
                'Department': prospect.get('department', ''),
                'Company LinkedIn URL': prospect.get('company_linkedin_url', '')
            })

def _save_company_prospects_mongo(prospects: List[Dict[str, Any]], company_name: str, campaign_id: str, company_id: str):
    """Save company's LinkedIn prospects to Database"""
    payload = {
        "prospects":prospects,
        "company_name":company_name,
        "campaign_id": campaign_id,
        "company_id": company_id
    }
    try:
        BASE_URL = loaded_config.base_url
        requests.post(f"{BASE_URL}/api/v1/save_prospects_data_to_mongo",json=payload)
    except Exception as e:
        clean_log(f"error {e}")
        raise Exception("Error",str(e))
# Async wrappers for LangGraph compatibility
async def linkedin_progress_saver(state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
    """
    Async wrapper for LinkedIn progress saving
    """
    return save_company_linkedin_progress(state, config)


async def hubspot_progress_saver(state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
    """
    Async wrapper for HubSpot progress saving
    """
    return save_company_hubspot_progress(state, config)