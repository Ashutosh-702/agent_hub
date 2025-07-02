"""
File Storage Node

Saves workflow progress and results to files for tracking and review.
"""
import csv
import json
import os
from datetime import datetime
from typing import Dict, Any

from ai_agents.ai_sdr.sdr.logging_config import clean_log, detailed_log
from ai_agents.ai_sdr.sdr.models import WorkflowState, Company


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


def save_company_relevance_report(run_directories: Dict[str, str], state: WorkflowState) -> str:
    """
    Generate company relevance report with all companies and their relevance status
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_dir = run_directories.get("results_dir", "output/results")
    os.makedirs(results_dir, exist_ok=True)
    
    # Create CSV file for company relevance report
    csv_filename = f"company_relevance_report_{timestamp}.csv"
    csv_filepath = os.path.join(results_dir, csv_filename)
    
    with open(csv_filepath, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['Company Name', 'Website', 'Industry', 'Location', 'Is Relevant', 
                     'Confidence Level', 'Reasoning', 'Key Factors', 'Assessment Timestamp']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for company in state.companies:
            # Get enriched data for this company
            enriched_data = state.enriched_data.get(company.name, {})
            web_analysis = enriched_data.get('web_search_analysis', {})
            relevance_assessment = web_analysis.get('relevance_assessment', {})
            
            # Extract relevance information
            is_relevant = relevance_assessment.get('is_relevant', False)
            confidence_level = relevance_assessment.get('confidence_level', 'unknown')
            reasoning = relevance_assessment.get('relevance_reason', relevance_assessment.get('reasoning', 'No analysis available'))
            key_factors = relevance_assessment.get('key_factors', [])
            
            # Get website from analysis or company data
            research_summary = web_analysis.get('research_summary', {})
            website_analyzed = research_summary.get('website_found', getattr(company, 'website', 'N/A'))
            industry_identified = research_summary.get('industry_identified', getattr(company, 'industry', 'N/A'))
            location_identified = research_summary.get('location_found', getattr(company, 'location', 'N/A'))
            
            # Get assessment timestamp from enriched data
            assessment_timestamp = enriched_data.get('research_timestamp', 'N/A')
            
            writer.writerow({
                'Company Name': company.name,
                'Website': website_analyzed,
                'Industry': industry_identified,
                'Location': location_identified,
                'Is Relevant': 'Yes' if is_relevant else 'No',
                'Confidence Level': confidence_level.title(),
                'Reasoning': reasoning,
                'Key Factors': ', '.join(key_factors) if key_factors else 'N/A',
                'Assessment Timestamp': assessment_timestamp
            })
    
    # Create JSON file with detailed data
    json_filename = f"company_relevance_report_{timestamp}.json"
    json_filepath = os.path.join(results_dir, json_filename)
    
    relevance_data = {
        "report_metadata": {
            "generation_timestamp": timestamp,
            "total_companies_analyzed": len(state.companies),
            "relevant_companies": len([c for c in state.companies if state.enriched_data.get(c.name, {}).get('web_search_analysis', {}).get('relevance_assessment', {}).get('is_relevant', False)]),
            "not_relevant_companies": len([c for c in state.companies if not state.enriched_data.get(c.name, {}).get('web_search_analysis', {}).get('relevance_assessment', {}).get('is_relevant', False)]),
        },
        "companies": []
    }
    
    for company in state.companies:
        enriched_data = state.enriched_data.get(company.name, {})
        web_analysis = enriched_data.get('web_search_analysis', {})
        relevance_assessment = web_analysis.get('relevance_assessment', {})
        research_summary = web_analysis.get('research_summary', {})
        
        company_relevance_data = {
            "company_info": {
                "name": company.name,
                "website": getattr(company, 'website', None),
                "industry": getattr(company, 'industry', None),
                "location": getattr(company, 'location', None)
            },
            "relevance_assessment": {
                "is_relevant": relevance_assessment.get('is_relevant', False),
                "confidence_level": relevance_assessment.get('confidence_level', 'unknown'),
                "reasoning": relevance_assessment.get('relevance_reason', relevance_assessment.get('reasoning', 'No analysis available')),
                "key_factors": relevance_assessment.get('key_factors', [])
            },
            "research_findings": {
                "website_analyzed": research_summary.get('website_found', 'N/A'),
                "industry_identified": research_summary.get('industry_identified', 'N/A'),
                "company_size": research_summary.get('company_size', 'N/A'),
                "business_model": research_summary.get('business_model', 'N/A')
            },
            "assessment_timestamp": enriched_data.get('research_timestamp', 'N/A')
        }
        
        relevance_data["companies"].append(company_relevance_data)
    
    with open(json_filepath, 'w', encoding='utf-8') as f:
        json.dump(relevance_data, f, indent=2, ensure_ascii=False)
    
    # Log results
    relevant_count = relevance_data["report_metadata"]["relevant_companies"]
    not_relevant_count = relevance_data["report_metadata"]["not_relevant_companies"]
    
    detailed_log(f"📊 Company Relevance Report generated:")
    detailed_log(f"   📄 CSV Report: {csv_filename}")
    detailed_log(f"   📋 JSON Report: {json_filename}")
    detailed_log(f"   ✅ Relevant: {relevant_count} companies")
    detailed_log(f"   ❌ Not Relevant: {not_relevant_count} companies")
    detailed_log(f"   📊 Total Analyzed: {len(state.companies)} companies")
    
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

        # Generate and save company relevance report
        relevance_report_path = save_company_relevance_report(run_directories, state)
        
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
