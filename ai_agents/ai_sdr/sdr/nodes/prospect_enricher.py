"""
Prospect Enricher Node

Uses browserMCP to find LinkedIn profiles of company executives and decision makers.
"""
from typing import Dict, Any

import orjson
from agents import Agent, Runner, ModelSettings
from agents.mcp.server import MCPServerStdio
from openai.types import Reasoning

from ai_agents.ai_sdr.sdr.logging_config import log_llm_request, log_llm_response, clean_log, detailed_log
from ai_agents.ai_sdr.sdr.models import WorkflowState, Company, LinkedInProspectResponse
from ai_agents.ai_sdr.sdr.prompts import PromptsConfig


class ProspectEnricher:
    """
    LinkedIn-based prospect enrichment using browserMCP
    Finds CXOs, Head of Operations, and other key decision makers
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        # Initialize prompts configuration
        custom_prompts = config.get('custom_prompts', {})
        self.prompts = PromptsConfig(custom_prompts)
        # Store all LinkedIn profiles collected across companies
        self.all_linkedin_profiles = []

    async def linkedin_prospect_search(self, company: Company, web_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use browserMCP to search LinkedIn for company executives with simple retry logic
        """
        company_name = company.name
        company_website = web_analysis.get('research_summary', {}).get('website_found', 'Not found')
        industry = web_analysis.get('research_summary', {}).get('industry_identified', 'Unknown')
        
        # Clean log for main status
        clean_log(f"LinkedIn Research: {company_name}")
        detailed_log("")
        detailed_log("─" * 50)
        detailed_log(f"🔍 LinkedIn Research: {company_name}")
        detailed_log("─" * 50)
        detailed_log(f"🌐 Website: {company_website}")
        detailed_log(f"🏢 Industry: {industry}")

        browser_mcp = None
        last_error = "Unknown error"
        
        try:
            # Create MCP connection once for all attempts
            browser_mcp = MCPServerStdio(
                name="browsermcp",
                params={
                    "command": "npx",
                    "args": ["@browsermcp/mcp@latest"],
                    "env": {
                        "MCP_AGENT_TOOL_MAX_STEPS": "300",
                        "MCP_AGENT_TOOL_MAX_ACTIONS_PER_STEP": "100",
                    },
                },
                cache_tools_list=True,
                client_session_timeout_seconds=1800
            )
            
            await browser_mcp.connect()
            detailed_log(f"MCP browser connected for {company_name}", "debug")
            
            # Simple retry loop - 3 attempts max
            for attempt in range(3):
                try:
                    detailed_log(f"🔄 Attempt {attempt + 1}/3 for {company_name}")
                    
                    result = await self._single_search_attempt(browser_mcp, company, web_analysis, attempt)
                    
                    # Check if search was successful
                    if result.get('linkedin_research', {}).get('search_successful', False):
                        detailed_log(f"✅ LinkedIn search successful for {company_name}")
                        return result
                    
                    # Search unsuccessful but no error - try again
                    last_error = "LinkedIn search was not successful"
                    detailed_log(f"⚠️ LinkedIn search unsuccessful for {company_name}, attempt {attempt + 1}")
                    
                except Exception as e:
                    last_error = str(e)
                    detailed_log(f"❌ LinkedIn search error for {company_name}, attempt {attempt + 1}: {e}", "error")
                    
                    # Don't log retry message on last attempt
                    if attempt < 2:
                        detailed_log(f"🔄 Retrying LinkedIn search for {company_name}...", "warning")

            # All attempts failed
            clean_log(f"LinkedIn search failed for {company_name}", "error")
            detailed_log(f"❌ Final LinkedIn search failure for {company_name}: {last_error}", "error")
            return self._create_error_fallback(company_name, last_error, 3)

        finally:
            # Single cleanup after all attempts
            if browser_mcp:
                try:
                    detailed_log(f"Cleaning up MCP browser for {company_name}", "debug")
                    await browser_mcp.cleanup()
                    detailed_log(f"MCP browser cleanup completed for {company_name}", "debug")
                except Exception as cleanup_error:
                    detailed_log(f"MCP cleanup error for {company_name}: {cleanup_error}", "warning")

    async def _single_search_attempt(self, browser_mcp, company: Company, web_analysis: Dict[str, Any], attempt: int) -> Dict[str, Any]:
        """Single LinkedIn search attempt without retry logic"""
        company_name = company.name
        company_website = web_analysis.get('research_summary', {}).get('website_found', 'Not found')
        industry = web_analysis.get('research_summary', {}).get('industry_identified', 'Unknown')

        # Build prompt
        prompt = self.prompts.get_prompt(
            "prospect_enricher_user_prompt",
            company_name=company_name,
            company_website=company_website,
            industry=industry
        )

        # Set up agent with structured output
        instructions = self.prompts.get_prompt("prospect_enricher_instructions")
        model = "o3"
        agent = Agent(
            name="LinkedInProspectAgent",
            model=model,
            model_settings=ModelSettings(reasoning=Reasoning(effort="high"),
                                       extra_body={"service_tier": "flex"}),
            mcp_servers=[browser_mcp],
            instructions=instructions,
            output_type=LinkedInProspectResponse
        )

        # Log the LLM request
        log_llm_request(model, prompt, f"LinkedIn prospect search for {company_name} (attempt {attempt + 1})")

        # Run the agent
        result = await Runner.run(
            starting_agent=agent,
            input=prompt,
            max_turns=100
        )

        # Log token usage if available
        total_tokens = 0
        if hasattr(result, 'usage_summary') and result.usage_summary:
            input_tokens = getattr(result.usage_summary, 'input_tokens', 0)
            output_tokens = getattr(result.usage_summary, 'output_tokens', 0)
            total_tokens = input_tokens + output_tokens
            detailed_log(f"💰 API Usage: {total_tokens:,} tokens")
        
        # Log the LLM response
        log_llm_response(model, str(result.final_output), f"LinkedIn prospect search for {company_name} (attempt {attempt + 1})", total_tokens)

        # Process the structured response (no retry logic here)
        return self._process_single_response(result.final_output, company_name)

    def _process_single_response(self, response_obj, company_name: str) -> Dict[str, Any]:
        """Process structured response without retry logic"""
        try:
            # Convert Pydantic model to dictionary
            if isinstance(response_obj, LinkedInProspectResponse):
                prospect_data = response_obj.model_dump()
            elif hasattr(response_obj, 'model_dump'):
                prospect_data = response_obj.model_dump()
            elif isinstance(response_obj, dict):
                prospect_data = response_obj
            else:
                # Fallback - try to parse as JSON
                prospect_data = orjson.loads(str(response_obj))

            # Log results and store profiles
            executives_count = len(prospect_data.get('executives_found', []))
            total_profiles = prospect_data.get('linkedin_research', {}).get('total_profiles_collected', 0)
            
            detailed_log("")
            detailed_log(f"✅ LinkedIn research completed for {company_name}")
            detailed_log(f"📊 Results: {total_profiles} profiles found, {executives_count} executives")

            self._log_prospect_results(prospect_data, company_name)
            self._store_profiles(prospect_data, company_name)

            return prospect_data

        except Exception as e:
            detailed_log(f"Response processing error for {company_name}: {e}", "error")
            # Return basic error structure
            return {
                "linkedin_research": {
                    "search_successful": False,
                    "total_executives_found": 0,
                    "total_profiles_collected": 0,
                    "csv_enrichment_note": f"Processing error: {str(e)}"
                },
                "executives_found": [],
                "all_profiles_found": []
            }


    def _log_prospect_results(self, prospect_data: Dict[str, Any], company_name: str):
        """Log the detailed results of LinkedIn prospect search"""
        executives_found = prospect_data.get('executives_found', [])
        if executives_found:
            detailed_log("")
            detailed_log("👔 Key Executives Found:")
            for i, exec_profile in enumerate(executives_found[:3], 1):  # Show first 3
                name = exec_profile.get('name', 'Unknown')
                title = exec_profile.get('title', 'Unknown Title')
                detailed_log(f"   {i}. {name} - {title}")
            if len(executives_found) > 3:
                detailed_log(f"   ... and {len(executives_found) - 3} more executives")
        else:
            detailed_log(f"⚠️ No executives found for {company_name}", "warning")

        # Log all profiles found (non-executives)
        all_profiles = prospect_data.get('all_profiles_found', [])
        if all_profiles:
            # Filter out executives from all profiles
            exec_urls = [p.get('linkedin_profile', '') for p in executives_found]
            non_exec_profiles = [p for p in all_profiles 
                               if p.get('linkedin_profile', '') not in exec_urls]
            
            if non_exec_profiles:
                detailed_log(f"👥 OTHER PROFILES FOUND for {company_name}:")
                for i, profile in enumerate(non_exec_profiles[:5], 1):  # Show first 5
                    name = profile.get('name', 'Unknown')
                    title = profile.get('title', 'Unknown Title')
                    linkedin_url = profile.get('linkedin_profile', 'No URL')
                    detailed_log(f"   {i}. {name} - {title}")
                    detailed_log(f"      LinkedIn: {linkedin_url}")
                
                if len(non_exec_profiles) > 5:
                    detailed_log(f"   ... and {len(non_exec_profiles) - 5} more profiles")

        company_linkedin = prospect_data.get('linkedin_research', {}).get('company_linkedin_url', '')
        if company_linkedin:
            detailed_log(f"🏢 Company LinkedIn Page: {company_linkedin}")

    def _store_profiles(self, prospect_data: Dict[str, Any], company_name: str):
        """Store the found profiles in the all_linkedin_profiles list"""
        # Process executives
        for profile in prospect_data.get('executives_found', []):
            profile['email'] = None
            profile['phone_number'] = None
            profile['company_name'] = company_name
            # Add to the combined list for CSV generation
            if 'linkedin_profile' in profile and profile['linkedin_profile']:
                self.all_linkedin_profiles.append({
                    'company_name': company_name,
                    'name': profile.get('name', ''),
                    'title': profile.get('title', ''),
                    'linkedin_profile': profile['linkedin_profile'],
                    'seniority_level': profile.get('seniority_level', ''),
                    'department': profile.get('department', ''),
                    'profile_type': 'Executive'
                })

        # Process other profiles
        for profile in prospect_data.get('all_profiles_found', []):
            profile['email'] = None
            profile['phone_number'] = None
            # Add to the combined list if not already in executives
            if 'linkedin_profile' in profile and profile['linkedin_profile']:
                exec_urls = [p['linkedin_profile'] for p in prospect_data.get('executives_found', [])]
                if profile['linkedin_profile'] not in exec_urls:
                    self.all_linkedin_profiles.append({
                        'company_name': company_name,
                        'name': profile.get('name', ''),
                        'title': profile.get('title', ''),
                        'linkedin_profile': profile['linkedin_profile'],
                        'department': profile.get('department', ''),
                        'profile_type': 'General'
                    })

    def _create_error_fallback(self, company_name: str, error_message: str, retry_count: int) -> Dict[str, Any]:
        """Create fallback data for general errors"""
        return {
            "linkedin_research": {
                "company_linkedin_url": "Search failed",
                "search_successful": False,
                "total_executives_found": 0,
                "total_profiles_collected": 0,
                "pages_scrolled": 0,
                "search_method": "error",
                "debug_info": f"Error after {retry_count} attempts: {error_message}"
            },
            "executives_found": [],
            "all_profiles_found": [],
            "research_notes": {
                "company_size_on_linkedin": "Unknown",
                "linkedin_presence": "unknown",
                "profile_accessibility": "unknown",
                "scrolling_completed": False,
                "pagination_used": False,
                "additional_contacts": []
            },
            "error": error_message,
            "retry_count": retry_count
        }


async def prospect_enricher(state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
    """
    LinkedIn prospect enrichment node
    
    Args:
        state: Current workflow state with web analysis data
        config: Configuration containing API keys and settings
        
    Returns:
        Updated workflow state with LinkedIn prospect data
    """
    detailed_log("")
    detailed_log("▶️ Starting LinkedIn prospect enrichment")
    
    config = config.get("configurable", {})
    company = state.current_company
    # Initialize enricher
    enricher = ProspectEnricher(config)

    # Get web analysis data
    web_analysis = state.enriched_data.get(company.name, {}).get('web_search_analysis', {})

    # Check if company is relevant before proceeding
    is_relevant = web_analysis.get('relevance_assessment', {}).get('is_relevant', False)

    if is_relevant:
        # Get LinkedIn prospect data
        prospect_data = await enricher.linkedin_prospect_search(company, web_analysis)

        # Check if LinkedIn search failed
        search_successful = prospect_data.get('linkedin_research', {}).get('search_successful', False)
        has_error = prospect_data.get('error') or prospect_data.get('json_parse_error')
        
        if has_error or not search_successful:
            # Track LinkedIn search failure
            error_msg = prospect_data.get('error') or prospect_data.get('json_parse_error') or "LinkedIn search was not successful"
            state.error_summary.prospect_enrichment_failures.append({
                "company": company.name,
                "error": str(error_msg),
                "retry_count": str(prospect_data.get('retry_count', 0))
            })
            clean_log(f"LinkedIn enrichment failed: {company.name}", "error")
            detailed_log(f"📊 LinkedIn enrichment failed: {company.name} - {error_msg}", "error")

        # Store the data in state
        state.enriched_data[company.name] = {
            **state.enriched_data.get(company.name, {}),
            "linkedin_prospect_data": prospect_data
        }

        # Add profiles to the global list
        if prospect_data.get("executives_found"):
            state.all_linkedin_profiles.extend(prospect_data["executives_found"])
    else:
        clean_log(f"Skipping {company.name} - not relevant")
        detailed_log(f"⏭️ Skipping {company.name} - not relevant for target criteria")
        
        # Log to enriched data for reference
        state.enriched_data[company.name] = {
            **state.enriched_data.get(company.name, {}),
            "prospect_enrichment_skipped": True,
            "skip_reason": "Company not relevant for grocery/FMCG criteria"
        }
        
        # Track in categorized error summary
        state.error_summary.skipped_companies.append({
            "company": company.name,
            "reason": "Not relevant for target criteria",
            "step": "prospect_enrichment"
        })
        
        detailed_log(f"📊 Company skipped: {company.name} (Not relevant for target criteria)")

    return state
