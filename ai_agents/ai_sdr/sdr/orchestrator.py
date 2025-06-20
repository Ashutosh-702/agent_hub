"""
Workflow Orchestrator - Manages company processing with individual workflows

This orchestrator runs OUTSIDE of LangGraph and manages the execution
of individual LangGraph workflows for each company.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field

from ai_agents.ai_sdr.sdr.models import Company, WorkflowState
from ai_agents.ai_sdr.sdr.nodes.company_list_retriever import _read_google_sheet, _read_csv_file, \
    _normalize_company_data
from ai_agents.ai_sdr.sdr.nodes.error_reporter import save_error_summary
from ai_agents.ai_sdr.sdr.nodes.final_progress_saver import save_final_workflow_results
from ai_agents.ai_sdr.sdr.nodes.progress_saver import save_linkedin_progress
from ai_agents.ai_sdr.sdr.single_company_workflow import compile_single_company_workflow
from ai_agents.ai_sdr.sdr.logging_config import sdr_logger, clean_log
from loguru import logger


@dataclass
class OrchestratorResult:
    """Result container for orchestrator execution"""
    companies_processed: int = 0
    companies_succeeded: int = 0
    companies_failed: int = 0
    total_contacts: int = 0
    total_errors: List[str] = field(default_factory=list)
    company_results: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    consolidated_linkedin_profiles: List[Dict[str, Any]] = field(default_factory=list)
    run_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


def save_workflow_progress(consolidated_state, param):
    pass


class WorkflowOrchestrator:
    """
    Orchestrates the execution of individual company workflows.
    
    This class operates OUTSIDE of LangGraph and manages:
    1. Company list management
    2. Individual workflow execution per company
    3. Result consolidation
    4. Post-processing coordination
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize orchestrator with configuration.
        
        Args:
            config: Configuration dict containing data source, API keys, etc.
        """
        self.config = config
        self.single_company_workflow = compile_single_company_workflow()
        self.result = OrchestratorResult()

    async def fetch_companies(self) -> List[Company]:
        """
        Fetch companies from the configured data source.
        
        This is a standalone implementation that doesn't use LangGraph nodes.
        """
        sdr_logger.log_section_start(
            "Company Fetching",
            "Retrieving companies from data source"
        )

        try:
            data_source = self.config.get('data_source', {})
            source_type = data_source.get('type', 'csv')

            if source_type == 'google_sheets':
                sheet_url = data_source.get('sheet_url')
                worksheet_name = data_source.get('worksheet_name')

                if not sheet_url:
                    raise ValueError("Google Sheets URL is required")

                df = await _read_google_sheet(sheet_url, worksheet_name)

            elif source_type == 'csv':
                file_path = data_source.get('file_path', 'companies.csv')
                df = await _read_csv_file(file_path)

            else:
                raise ValueError(f"Unsupported data source type: {source_type}")

            # Normalize to Company objects
            companies = _normalize_company_data(df)

            # Apply max companies limit if configured
            max_companies = self.config.get('max_companies')
            if max_companies and 0 < max_companies < len(companies):
                companies = companies[:max_companies]
                logger.info(f"Limited to {max_companies} companies")

            sdr_logger.log_completion(
                "Company Fetching",
                {"Total Companies": len(companies)}
            )

            return companies

        except Exception as e:
            sdr_logger.log_error_with_context(
                e,
                "Failed to fetch companies"
            )
            raise

    async def process_single_company(
        self,
        company: Company,
        company_index: int,
        total_companies: int
    ) -> Dict[str, Any]:
        """
        Process a single company through its own workflow instance.
        
        Returns:
            Dict containing results for this company
        """
        sdr_logger.log_section_start(
            f"Company {company_index + 1}/{total_companies}",
            f"Processing: {company.name}"
        )

        # Create initial state for single company
        initial_state = WorkflowState(
            companies=[company],
            current_company=company,
            current_company_index=0,
            started_at=datetime.now(),
            run_id=self.result.run_id,
            run_directories=self.config.get('run_directories', {})
        )

        # Add user prompts if available
        if 'custom_prompts' in self.config:
            initial_state.enriched_data["user_prompts"] = self.config['custom_prompts']

        try:
            # Run the single company workflow
            final_state = await self.single_company_workflow.ainvoke(
                initial_state,
                config={"configurable": self.config, "recursion_limit": 10000}
            )

            # Extract results for this company
            company_result = {
                "status": "success",
                "company_name": company.name,
                "enriched_data": final_state.get("enriched_data", {}).get(company.name, {}),
                "contacts": final_state.get("contacts", {}).get(company.name, []),
                "linkedin_profiles": final_state.get("all_linkedin_profiles", []),
                "errors": final_state.get("errors", []),
                "files_saved": final_state.get("saved_files", [])
            }

            # Update orchestrator statistics
            self.result.companies_succeeded += 1
            contact_count = len(company_result["contacts"])
            self.result.total_contacts += contact_count

            sdr_logger.log_completion(
                f"Company Processing",
                {
                    "Company": company.name,
                    "Status": "Success",
                    "Contacts Found": contact_count
                }
            )

            return company_result

        except Exception as e:
            sdr_logger.log_error_with_context(
                e,
                f"Error processing company {company.name}"
            )

            # Return error result
            self.result.companies_failed += 1
            self.result.total_errors.append(f"{company.name}: {str(e)}")

            return {
                "status": "error",
                "company_name": company.name,
                "error": str(e)
            }

    def run_post_processing(self):
        """
        Run post-processing steps after all companies are processed.
        
        This imports and uses the post-processing nodes directly.
        """
        sdr_logger.log_section_start(
            "Post-Processing Phase",
            "Consolidating results and generating reports"
        )

        # Create a consolidated state for post-processing
        consolidated_state = WorkflowState(
            companies=[],  # Already processed
            all_linkedin_profiles=self.result.consolidated_linkedin_profiles,
            errors=self.result.total_errors,
            run_id=self.result.run_id,
            run_directories=self.config.get('run_directories', {}),
            started_at=self.result.started_at,
            completed_at=datetime.now()
        )

        try:
            # Run each post-processing step
            sdr_logger.log_subsection("LinkedIn Progress Backup", {})
            consolidated_state = save_linkedin_progress(
                consolidated_state,
                {"configurable": self.config}
            )

            sdr_logger.log_subsection("Final Progress Save", {})
            consolidated_state = save_final_workflow_results(
                consolidated_state,
                {"configurable": self.config}
            )

            sdr_logger.log_subsection("Error Summary Export", {})
            consolidated_state = save_error_summary(consolidated_state,{"configurable": self.config})

            sdr_logger.log_subsection("Save Final Results", {})
            save_workflow_progress(consolidated_state,{"configurable": self.config})

            sdr_logger.log_completion(
                "Post-Processing Complete",
                {
                    "Files Saved": len(consolidated_state.saved_files),
                    "Status": "Success"
                }
            )

        except Exception as e:
            sdr_logger.log_error_with_context(
                e,
                "Post-processing failed"
            )
            self.result.total_errors.append(f"Post-processing error: {str(e)}")

    async def run(self) -> OrchestratorResult:
        """
        Main orchestration method - coordinates the entire workflow.
        
        Returns:
            OrchestratorResult with complete execution summary
        """
        sdr_logger.log_section_start(
            "SDR Workflow Orchestration",
            "Starting company-by-company processing"
        )

        self.result.started_at = datetime.now()
        self.result.run_id = self.config.get('run_directories', {}).get('run_id',
                                                                        datetime.now().strftime('%Y%m%d_%H%M%S'))

        try:
            # Step 1: Fetch companies
            companies = await self.fetch_companies()

            if not companies:
                sdr_logger.log_warning_with_context(
                    "No companies found to process",
                    "Orchestration"
                )
                self.result.completed_at = datetime.now()
                return self.result

            # Step 2: Process each company
            for index, company in enumerate(companies):
                self.result.companies_processed += 1

                company_result = await self.process_single_company(
                    company, index, len(companies)
                )

                # Store result
                self.result.company_results[company.name] = company_result

                # Collect LinkedIn profiles
                if company_result.get("status") == "success":
                    self.result.consolidated_linkedin_profiles.extend(
                        company_result.get("linkedin_profiles", [])
                    )

            # Step 3: Run post-processing
            self.run_post_processing()

            self.result.completed_at = datetime.now()

            # Log final summary
            duration = self.result.completed_at - self.result.started_at
            sdr_logger.log_completion(
                "SDR Workflow Orchestration Complete",
                {
                    "Total Companies": self.result.companies_processed,
                    "Succeeded": self.result.companies_succeeded,
                    "Failed": self.result.companies_failed,
                    "Total Contacts": self.result.total_contacts,
                    "Duration": str(duration)
                }
            )

            return self.result

        except Exception as e:
            sdr_logger.log_error_with_context(
                e,
                "Orchestration failed"
            )
            self.result.total_errors.append(f"Orchestration error: {str(e)}")
            self.result.completed_at = datetime.now()
            return self.result
