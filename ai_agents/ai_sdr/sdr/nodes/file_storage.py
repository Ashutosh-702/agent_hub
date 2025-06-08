"""
File Storage Node

Saves workflow progress and results to files for tracking and review.
"""
import csv
import os
import json
from datetime import datetime
from typing import Dict, Any

from ai_agents.ai_sdr.sdr.models import WorkflowState, Company
from ai_agents.ai_sdr.sdr.logging_config import clean_log, detailed_log


def ensure_output_directory():
    """Ensure output directory exists"""
    os.makedirs("output", exist_ok=True)


def serialize_company_data(company: Company, enriched_data: Dict[str, Any]) -> Dict[str, Any]:
    """Serialize company and enriched data for JSON storage"""

    # Safely get attributes with default None values
    company_dict = {
        "name": company.name,
        "website": getattr(company, 'website', None),
        "domain": getattr(company, 'domain', None),
        "industry": getattr(company, 'industry', None),
        "size": getattr(company, 'size', None),
        "location": getattr(company, 'location', None),
        "description": getattr(company, 'description', None),
        "linkedin_url": getattr(company, 'linkedin_url', None)
    }

    return {
        "company_info": company_dict,
        "enriched_data": enriched_data,
        "processed_timestamp": datetime.now().isoformat()
    }


def generate_summary_report(state: WorkflowState) -> Dict[str, Any]:
    """Generate a summary report of the workflow execution"""

    total_companies = len(state.companies)
    processed_companies = len(state.enriched_data)

    # Analyze TMS priorities
    priority_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "DISQUALIFY": 0, "UNKNOWN": 0}
    high_priority_companies = []
    medium_priority_companies = []

    for company_name, data in state.enriched_data.items():
        tms_analysis = data.get('tms_analysis', {})
        action_plan = tms_analysis.get('action_plan', {})
        priority = action_plan.get('priority', 'UNKNOWN')

        priority_counts[priority] += 1

        if priority == "HIGH":
            high_priority_companies.append({
                "name": company_name,
                "score": action_plan.get('combined_score', 0),
                "next_steps": action_plan.get('next_steps', 'N/A')
            })
        elif priority == "MEDIUM":
            medium_priority_companies.append({
                "name": company_name,
                "score": action_plan.get('combined_score', 0),
                "next_steps": action_plan.get('next_steps', 'N/A')
            })

    # Sort by score
    high_priority_companies.sort(key=lambda x: x['score'], reverse=True)
    medium_priority_companies.sort(key=lambda x: x['score'], reverse=True)

    return {
        "workflow_summary": {
            "execution_date": datetime.now().isoformat(),
            "total_companies": total_companies,
            "processed_companies": processed_companies,
            "success_rate": f"{(processed_companies / total_companies * 100):.1f}%" if total_companies > 0 else "0%",
            "errors_count": len(state.errors)
        },
        "priority_analysis": {
            "priority_counts": priority_counts,
            "high_priority_companies": high_priority_companies,
            "medium_priority_companies": medium_priority_companies
        },
        "recommendations": {
            "immediate_action_needed": len(high_priority_companies),
            "follow_up_candidates": len(medium_priority_companies),
            "total_qualified_leads": len(high_priority_companies) + len(medium_priority_companies)
        },
        "errors": state.errors
    }



def save_consolidated_final_file(run_directories: Dict[str, str], state: WorkflowState) -> str | None:
    """
    Generate consolidated final file with all prospects from all companies
    """

    if not state.all_linkedin_profiles:
        clean_log("No LinkedIn profiles collected - skipping consolidated file", "warning")
        detailed_log("No LinkedIn profiles collected - skipping consolidated final file generation", "warning")
        return None

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    final_dir = run_directories.get("final_dir", "output/final")
    os.makedirs(final_dir, exist_ok=True)

    # Create consolidated CSV file for all prospects
    csv_filename = f"all_prospects_consolidated_{timestamp}.csv"
    csv_filepath = os.path.join(final_dir, csv_filename)

    with open(csv_filepath, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['Company Name', 'Person Name', 'Person Title', 'Person LinkedIn',
                      'Seniority Level', 'Department', 'Profile Type', 'Email', 'Phone Number']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for profile in state.all_linkedin_profiles:
            writer.writerow({
                'Company Name': profile['company_name'],
                'Person Name': profile['name'],
                'Person Title': profile['title'],
                'Person LinkedIn': profile['linkedin_profile'],
                'Seniority Level': profile.get('seniority_level', ''),
                'Department': profile.get('department', ''),
                'Profile Type': profile.get('profile_type', 'General'),
                'Email': '',  # To be filled by EasyLeadz
                'Phone Number': ''  # To be filled by EasyLeadz
            })

    # Create consolidated JSON file with complete data
    json_filename = f"all_prospects_consolidated_{timestamp}.json"
    json_filepath = os.path.join(final_dir, json_filename)

    with open(json_filepath, 'w', encoding='utf-8') as f:
        import json
        json.dump({
            "run_id": run_directories.get("run_id", "unknown"),
            "timestamp": timestamp,
            "total_profiles": len(state.all_linkedin_profiles),
            "total_companies": len(set(profile['company_name'] for profile in state.all_linkedin_profiles)),
            "file_purpose": "Consolidated final file with all prospects from all companies",
        }, f, indent=2, ensure_ascii=False)

    detailed_log(f"💾 Consolidated final files generated:")
    detailed_log(f"   📄 Master CSV: {csv_filename} ({len(state.all_linkedin_profiles)} profiles)")
    detailed_log(f"   📋 Master JSON: {json_filename}")
    detailed_log(
        f"   🏢 Companies covered: {len(set(profile['company_name'] for profile in state.all_linkedin_profiles))}")

    return csv_filepath


async def save_final_results(state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
    """
    LangGraph node to save final workflow results
    
    Args:
        state: Final workflow state
        config: Configuration
        
    Returns:
        Updated workflow state
    """
    # Clean log for main status
    clean_log("Saving final results to files")
    
    # Detailed logs
    detailed_log("")
    detailed_log("💾 Saving final results to files")

    config = config.get("configurable", {})
    run_directories = config.get("run_directories", {})
    results_dir = run_directories.get("results_dir")

    try:
        # Ensure results directory exists
        os.makedirs(results_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        consolidated_file_path = save_consolidated_final_file(run_directories, state)
        state.consolidated_prospects_file = consolidated_file_path

        clean_log(f"Final files saved: {len(state.all_linkedin_profiles)} prospects from {len(state.companies)} companies")
        
        detailed_log(f"💾 Consolidated final file generated:")
        detailed_log(f"   📄 Master CSV: {os.path.basename(consolidated_file_path or '')}")
        detailed_log(f"   🏢 Companies covered: {len(state.companies)}")
        detailed_log(f"   👥 Total prospects: {len(state.all_linkedin_profiles)}")

        # Save complete workflow data
        complete_data = {
            "workflow_metadata": {
                "execution_timestamp": timestamp,
                "total_companies": len(state.companies),
                "processed_companies": len(state.enriched_data),
                "configuration": {
                    "data_source_type": config.get('data_source', {}).get('type', 'unknown'),
                    "enrichment_methods": ["web_search", "browser_automation", "tms_analysis"]
                }
            },
            "companies": {}
        }

        # Add all company data
        for company in state.companies:
            enriched_data = state.enriched_data.get(company.name, {})
            complete_data["companies"][company.name] = serialize_company_data(company, enriched_data)

        # Save complete data
        complete_filename = f"{results_dir}/complete_workflow_data_{timestamp}.json"
        with open(complete_filename, 'w', encoding='utf-8') as f:
            json.dump(complete_data, f, indent=2, ensure_ascii=False)

        # Generate and save summary report
        summary_report = generate_summary_report(state)
        summary_filename = f"{results_dir}/summary_report_{timestamp}.json"
        with open(summary_filename, 'w', encoding='utf-8') as f:
            json.dump(summary_report, f, indent=2, ensure_ascii=False)

        # Add to saved files
        if hasattr(state, 'saved_files'):
            state.saved_files.append(complete_filename)
            state.saved_files.append(summary_filename)

        detailed_log(f"Final results saved:")
        detailed_log(f"  - Complete data: {complete_filename}")
        detailed_log(f"  - Summary: {summary_filename}")

        return state

    except Exception as e:
        error_msg = f"Failed to save final results: {str(e)}"
        clean_log(f"Failed to save final results: {str(e)}", "error")
        detailed_log(error_msg, "error")
        state.errors.append(error_msg)
        return state
