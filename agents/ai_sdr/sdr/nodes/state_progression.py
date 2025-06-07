"""
State Progression Node

Handles moving to the next company in the workflow
"""
from sdr.logging_config import sdr_logger
from sdr.models import WorkflowState


def company_progression(state: WorkflowState) -> WorkflowState:
    """Handle progression to the next company in the loop"""
    # Move to next company
    next_index = state.current_company_index + 1

    if next_index < len(state.companies):
        state.current_company_index = next_index
        state.current_company = state.companies[next_index]

        sdr_logger.log_progress(next_index + 1, len(state.companies), "company")
        sdr_logger.log_processing_item(
            f"Company {next_index + 1}/{len(state.companies)}: {state.current_company.name}",
            {
                "Previous Company": state.companies[next_index - 1].name,
                "Current Company": state.current_company.name,
                "Website": getattr(state.current_company, 'website', 'N/A')
            }
        )
    else:
        sdr_logger.log_completion(
            "Company Loop Progression",
            {"Status": "All companies processed", "Total Processed": len(state.companies)}
        )

    return state
