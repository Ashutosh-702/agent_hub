"""
Workflow Adapter - Provides compatibility layer between old and new workflow architectures
"""
from typing import Dict, Any

from ai_agents.ai_sdr.sdr.graph import compile_workflow as compile_monolithic_workflow
from ai_agents.ai_sdr.sdr.logging_config import clean_log
from ai_agents.ai_sdr.sdr.models import WorkflowState
from ai_agents.ai_sdr.sdr.orchestrator import WorkflowOrchestrator, OrchestratorResult


class WorkflowAdapter:
    """Adapter to switch between monolithic and orchestrated workflows"""
    
    def __init__(self, config: Dict[str, Any], use_orchestrated: bool = True):
        self.use_orchestrated = use_orchestrated
        self.config = config
        
        if use_orchestrated:
            clean_log("Using orchestrated workflow architecture")
            self.orchestrator = WorkflowOrchestrator(config)
            self.workflow = None
        else:
            clean_log("Using monolithic workflow architecture")
            self.orchestrator = None
            self.workflow = compile_monolithic_workflow()
    
    async def run(self, initial_state: WorkflowState) -> WorkflowState:
        """Run the workflow using the selected architecture"""
        if self.use_orchestrated:
            # Run orchestrator and convert result to WorkflowState format
            result = await self.orchestrator.run()
            
            # Convert OrchestratorResult to WorkflowState for compatibility
            return self._convert_orchestrator_result_to_state(result, initial_state)
        else:
            # Run monolithic workflow
            return await self.workflow.ainvoke(
                initial_state,
                config={"configurable": self.config, "recursion_limit": 10000}
            )
    
    def _convert_orchestrator_result_to_state(
        self, 
        result: OrchestratorResult, 
        initial_state: WorkflowState
    ) -> WorkflowState:
        """Convert OrchestratorResult to WorkflowState for compatibility"""
        # Create a new state with orchestrator results
        final_state = WorkflowState(
            companies=[],  # Companies already processed
            enriched_data={},
            contacts={},
            all_linkedin_profiles=result.consolidated_linkedin_profiles,
            errors=result.total_errors,
            run_id=result.run_id,
            run_directories=initial_state.run_directories,
            started_at=result.started_at,
            completed_at=result.completed_at
        )
        
        # Extract enriched data and contacts from company results
        for company_name, company_result in result.company_results.items():
            if company_result.get("status") == "success":
                final_state.enriched_data[company_name] = company_result.get("enriched_data", {})
                final_state.contacts[company_name] = company_result.get("contacts", [])
        
        return final_state
    
    @staticmethod
    def create_orchestrated_workflow(config: Dict[str, Any]):
        """Factory method to create orchestrated workflow"""
        return WorkflowAdapter(config, use_orchestrated=True)
    
    @staticmethod
    def create_monolithic_workflow(config: Dict[str, Any]):
        """Factory method to create monolithic workflow"""
        return WorkflowAdapter(config, use_orchestrated=False)