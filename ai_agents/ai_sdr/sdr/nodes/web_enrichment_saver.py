"""
Web Enrichment Saver Node

Saves the results of the web enrichment process to a CSV file incrementally.
"""

import os
import csv
from typing import Dict, Any

from ai_agents.ai_sdr.sdr.models import WorkflowState
from ai_agents.ai_sdr.sdr.logging_config import sdr_logger, clean_log, detailed_log


def save_web_enrichment_results(state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
    """
    Save web enrichment results to a CSV file incrementally after each company.

    Args:
        state: Current workflow state.
        config: Configuration dictionary.

    Returns:
        Updated workflow state.
    """
    clean_log(f"Saving web enrichment results for: {state.current_company.name}")

    try:
        config_dict = config.get("configurable", {})
        run_directories = config_dict.get("run_directories", {})
        # Use the progress directory to save incremental results
        progress_dir = run_directories.get("final_dir", "output/final")
        run_id = run_directories.get("run_id", "unknown")

        os.makedirs(progress_dir, exist_ok=True)

        # Define the CSV file path
        file_path = os.path.join(progress_dir, f"web_enrichment_relevance_{run_id}.csv")

        # Get the latest relevance assessment from the state
        if not hasattr(state, 'company_relevance_assessments') or not state.company_relevance_assessments:
            detailed_log("No web enrichment data to save.", "warning")
            return state

        relevance_assessment = state.company_relevance_assessments[-1]

        # Prepare data for CSV
        data_to_save = {
            "company_name": relevance_assessment.company_name,
            "is_relevant": relevance_assessment.is_relevant,
            "confidence_level": relevance_assessment.confidence_level,
            "reasoning": relevance_assessment.reasoning,
            "key_factors": ", ".join(relevance_assessment.key_factors),
            "website_analyzed": relevance_assessment.website_analyzed,
            "industry_identified": relevance_assessment.industry_identified,
            "assessment_timestamp": relevance_assessment.assessment_timestamp
        }

        # Write to CSV, appending if file exists
        file_exists = os.path.isfile(file_path)
        with open(file_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=data_to_save.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(data_to_save)

        detailed_log(f"Saved web enrichment results for '{relevance_assessment.company_name}' to {file_path}")

        # Optionally, track the saved file in the state
        if not hasattr(state, 'web_enrichment_files'):
            state.web_enrichment_files = []
        if file_path not in state.web_enrichment_files:
            state.web_enrichment_files.append(file_path)

    except Exception as e:
        error_msg = f"Failed to save web enrichment results for {state.current_company.name}: {e}"
        detailed_log(error_msg, "error")
        state.errors.append(error_msg)

    return state
