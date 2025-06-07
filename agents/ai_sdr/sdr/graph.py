"""
LangGraph workflow for SDR prospect research with loop-based per-company processing
"""
from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph

from sdr.models import WorkflowState
from sdr.nodes.company_list_retriever import company_list_retriever
from sdr.nodes.hubspot_contact_creator import hubspot_contact_creator
from sdr.nodes.state_progression import company_progression
from sdr.nodes.streamlined_web_enricher import streamlined_web_enricher
from sdr.nodes.prospect_enricher import prospect_enricher
from sdr.nodes.file_storage import save_final_results
from sdr.nodes.progress_saver import linkedin_progress_saver
from sdr.nodes.error_reporter import error_reporter
from sdr.logging_config import sdr_logger


def start_company_loop(state: WorkflowState) -> Literal["streamlined_web_enricher", "end"]:
    """Start the company processing loop or end if no companies"""
    if state.companies and len(state.companies) > 0:
        # Set up for first company
        state.current_company_index = 0
        state.current_company = state.companies[0]
        
        sdr_logger.log_section_start(
            "Company Processing Loop", 
            f"Processing {len(state.companies)} companies"
        )
        sdr_logger.log_progress(1, len(state.companies), "company")
        sdr_logger.log_processing_item(
            f"Company 1/{len(state.companies)}: {state.current_company.name}",
            {"Website": getattr(state.current_company, 'website', 'N/A')}
        )
        
        return "streamlined_web_enricher"
    else:
        sdr_logger.log_warning_with_context(
            "No companies found to process", 
            "Company Loop Initialization"
        )
        return "end"


def check_relevance_for_prospect_enrichment(state: WorkflowState) -> Literal[
    "prospect_enricher", "company_progression"]:
    """Check if company is relevant for LinkedIn prospect enrichment"""
    # Get web analysis data
    company_name = state.current_company.name
    web_analysis = state.enriched_data.get(company_name, {}).get('web_search_analysis', {})
    is_relevant = web_analysis.get('relevance_assessment', {}).get('is_relevant', False)

    if is_relevant:
        sdr_logger.log_subsection(
            f"✅ {company_name} - Proceeding to LinkedIn Enrichment",
            {"Relevance": "CONFIRMED", "Next Step": "Prospect Research"}
        )
        return "prospect_enricher"
    else:
        sdr_logger.log_subsection(
            f"⏭️ {company_name} - Skipping LinkedIn Enrichment", 
            {"Relevance": "NOT RELEVANT", "Next Step": "Continue to Next Company"}
        )
        return "company_progression"


def continue_company_loop(state: WorkflowState) -> Literal["streamlined_web_enricher", "linkedin_progress_backup"]:
    """Determine whether to continue the loop or proceed to LinkedIn backup"""
    # Check if we have more companies to process
    if state.current_company_index + 1 < len(state.companies):
        remaining = len(state.companies) - (state.current_company_index + 1)
        sdr_logger.log_subsection(
            "Continuing Company Processing Loop",
            {
                "Remaining Companies": remaining,
                "Next Action": "Web Enrichment for Next Company"
            }
        )
        return "streamlined_web_enricher"
    else:
        # After processing all companies, backup LinkedIn URLs before HubSpot
        sdr_logger.log_section_start(
            "LinkedIn Data Backup Phase",
            "All companies processed - backing up LinkedIn URLs before HubSpot"
        )
        return "linkedin_progress_backup"


def proceed_after_backup(state: WorkflowState) -> Literal["hubspot_batch", "error_summary_export"]:
    """Decide whether to proceed to HubSpot batch processing or skip to error summary"""
    # Check if we have LinkedIn profiles and HubSpot is enabled
    has_profiles = hasattr(state, 'all_linkedin_profiles') and state.all_linkedin_profiles
    
    if has_profiles:
        sdr_logger.log_section_start(
            "HubSpot Batch Processing",
            f"Processing {len(state.all_linkedin_profiles)} LinkedIn profiles for HubSpot"
        )
        return "hubspot_batch"
    else:
        sdr_logger.log_warning_with_context(
            "No LinkedIn profiles found - skipping HubSpot processing",
            "HubSpot Batch Processing"
        )
        return "error_summary_export"


def create_workflow_graph() -> StateGraph:
    """Create the loop-based LangGraph workflow"""
    
    sdr_logger.log_section_start(
        "SDR Workflow Graph Creation",
        "Building LangGraph workflow with loop-based company processing"
    )

    # Create the state graph
    sdr_workflow = StateGraph(WorkflowState)

    # Add nodes
    nodes_config = {
        "company_retriever": company_list_retriever,
        "streamlined_web_enricher": streamlined_web_enricher,
        "prospect_enricher": prospect_enricher,
        "hubspot_individual": hubspot_contact_creator,
        "company_progression": company_progression,
        "linkedin_progress_backup": linkedin_progress_saver,
        "hubspot_batch": hubspot_contact_creator,
        "error_summary_export": error_reporter,
        "save_results": save_final_results
    }
    
    sdr_logger.log_subsection(
        "Adding Workflow Nodes",
        {"Node Count": len(nodes_config), "Node Names": list(nodes_config.keys())}
    )
    
    for node_name, node_func in nodes_config.items():
        sdr_workflow.add_node(node_name, node_func)

    # Set entry point
    sdr_workflow.set_entry_point("company_retriever")
    
    sdr_logger.log_subsection(
        "Configuring Workflow Edges",
        {"Entry Point": "company_retriever", "Flow Type": "Conditional and Linear"}
    )

    # After company retrieval, start the loop or end if no companies
    sdr_workflow.add_conditional_edges(
        "company_retriever",
        start_company_loop,
        {
            "streamlined_web_enricher": "streamlined_web_enricher",
            "end": END
        }
    )

    # After web analysis, check relevance for prospect enrichment
    sdr_workflow.add_conditional_edges(
        "streamlined_web_enricher",
        check_relevance_for_prospect_enrichment,
        {
            "prospect_enricher": "prospect_enricher",
            "company_progression": "company_progression"
        }
    )

    # After prospect enrichment, go to individual HubSpot processing
    sdr_workflow.add_edge("prospect_enricher", "hubspot_individual")

    # After individual HubSpot processing, progress to next company
    sdr_workflow.add_edge("hubspot_individual", "company_progression")

    # After company progression, continue loop or backup LinkedIn data
    sdr_workflow.add_conditional_edges(
        "company_progression",
        continue_company_loop,
        {
            "streamlined_web_enricher": "streamlined_web_enricher",
            "linkedin_progress_backup": "linkedin_progress_backup"
        }
    )

    # After LinkedIn backup, proceed to HubSpot batch or error summary
    sdr_workflow.add_conditional_edges(
        "linkedin_progress_backup",
        proceed_after_backup,
        {
            "hubspot_batch": "hubspot_batch",
            "error_summary_export": "error_summary_export"
        }
    )

    # After HubSpot batch processing, export error summary
    sdr_workflow.add_edge("hubspot_batch", "error_summary_export")

    # After error summary export, save final results
    sdr_workflow.add_edge("error_summary_export", "save_results")

    # After saving results, end
    sdr_workflow.add_edge("save_results", END)
    
    sdr_logger.log_completion(
        "Workflow Graph Creation",
        {
            "Total Nodes": len(nodes_config),
            "Conditional Edges": 4,
            "Linear Edges": 4,
            "Status": "Ready for compilation"
        }
    )

    return sdr_workflow


def compile_workflow() -> CompiledStateGraph:
    """Compile and return the workflow"""
    sdr_logger.log_section_start(
        "Workflow Compilation",
        "Compiling LangGraph workflow for execution"
    )
    
    sdr_workflow = create_workflow_graph()
    compiled_workflow = sdr_workflow.compile()
    
    sdr_logger.log_completion(
        "Workflow Compilation",
        {"Status": "Successfully compiled", "Type": "CompiledStateGraph"}
    )
    
    return compiled_workflow
