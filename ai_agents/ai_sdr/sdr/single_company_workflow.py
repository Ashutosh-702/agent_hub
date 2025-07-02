"""
Single Company Workflow - Processes one company at a time
"""
from typing import Literal

from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph

from ai_agents.ai_sdr.sdr.logging_config import sdr_logger
from ai_agents.ai_sdr.sdr.models import WorkflowState
from ai_agents.ai_sdr.sdr.nodes.company_progress_saver import (
    linkedin_progress_saver as company_linkedin_saver,
    hubspot_progress_saver
)
from ai_agents.ai_sdr.sdr.nodes.hubspot_contact_creator import hubspot_contact_creator
from ai_agents.ai_sdr.sdr.nodes.prospect_enricher import prospect_enricher
from ai_agents.ai_sdr.sdr.nodes.streamlined_web_enricher import streamlined_web_enricher
from ai_agents.ai_sdr.sdr.nodes.web_enrichment_saver import save_web_enrichment_results


def check_relevance_for_prospect_enrichment(state: WorkflowState) -> Literal[
    "prospect_enricher", "end"]:
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
            f"⏭️ {company_name} - Not relevant, skipping LinkedIn Enrichment", 
            {"Relevance": "NOT RELEVANT", "Next Step": "End workflow for this company"}
        )
        return "end"


def create_single_company_workflow() -> StateGraph:
    """Create workflow for processing a single company"""
    
    sdr_logger.log_section_start(
        "Single Company Workflow Creation",
        "Building workflow for individual company processing"
    )

    # Create the state graph
    workflow = StateGraph(WorkflowState)

    # Add nodes for single company processing
    nodes_config = {
        "streamlined_web_enricher": streamlined_web_enricher,
        "web_enrichment_saver": save_web_enrichment_results,
        "prospect_enricher": prospect_enricher,
        "company_linkedin_progress": company_linkedin_saver,
        "hubspot_individual": hubspot_contact_creator,
        "hubspot_progress_saver": hubspot_progress_saver,
    }
    
    sdr_logger.log_subsection(
        "Adding Single Company Workflow Nodes",
        {"Node Count": len(nodes_config), "Node Names": list(nodes_config.keys())}
    )
    
    for node_name, node_func in nodes_config.items():
        workflow.add_node(node_name, node_func)

    # Set entry point
    workflow.set_entry_point("streamlined_web_enricher")
    
    # After web analysis, save the results
    workflow.add_edge("streamlined_web_enricher", "web_enrichment_saver")

    # After saving, check relevance
    workflow.add_conditional_edges(
        "web_enrichment_saver",
        check_relevance_for_prospect_enrichment,
        {
            "prospect_enricher": "prospect_enricher",
            "end": END
        }
    )

    # After prospect enrichment, save LinkedIn progress
    workflow.add_edge("prospect_enricher", "company_linkedin_progress")

    # After LinkedIn progress save, go to HubSpot processing
    workflow.add_edge("company_linkedin_progress", "hubspot_individual")

    # After HubSpot processing, save HubSpot progress
    workflow.add_edge("hubspot_individual", "hubspot_progress_saver")

    # After HubSpot progress save, end
    workflow.add_edge("hubspot_progress_saver", END)
    
    sdr_logger.log_completion(
        "Single Company Workflow Creation",
        {
            "Total Nodes": len(nodes_config),
            "Entry Point": "streamlined_web_enricher",
            "Status": "Ready for compilation"
        }
    )

    return workflow


def compile_single_company_workflow() -> CompiledStateGraph:
    """Compile and return the single company workflow"""
    sdr_logger.log_section_start(
        "Single Company Workflow Compilation",
        "Compiling workflow for individual company processing"
    )
    
    workflow = create_single_company_workflow()
    compiled_workflow = workflow.compile()
    
    sdr_logger.log_completion(
        "Single Company Workflow Compilation",
        {"Status": "Successfully compiled", "Type": "CompiledStateGraph"}
    )
    
    return compiled_workflow