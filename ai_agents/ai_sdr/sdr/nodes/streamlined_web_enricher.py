"""
Streamlined Web Search Enricher Node

Two-step LLM-driven approach:
1. Web Search Analysis LLM - Uses web search tool to gather and analyze data
2. Browser Enhancement LLM - Uses browser to visit sites and enrich data
"""

from typing import Dict, Any
from datetime import datetime

import orjson
from openai import OpenAI

from ai_agents.ai_sdr.sdr.logging_config import log_llm_response, log_llm_request, log_llm_error, clean_log, detailed_log, sdr_logger
from ai_agents.ai_sdr.sdr.models import WorkflowState, Company, CompanyRelevance
from ai_agents.ai_sdr.sdr.prompts import PromptsConfig


class StreamlinedWebEnricher:
    """
    Streamlined company research with 2 LLM calls:
    1. Web search analysis and data gathering
    2. Browser-based data enrichment
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.openai_client = OpenAI(api_key=config.get('openai_api_key'))
        custom_prompts = config.get('custom_prompts', {})
        self.prompts = PromptsConfig(custom_prompts)

    async def web_search_analysis(self, company: Company, retry_count: int = 0, previous_context: str = "") -> Dict[str, Any]:
        """
        Step 1: LLM-driven web search analysis with retry logic
        Uses web search tool to gather comprehensive company data
        """

        # Get system prompt from centralized prompts - safely handle None values
        company_website = getattr(company, 'website', None) or 'Unknown - MUST FIND'
        company_industry = getattr(company, 'industry', None) or 'Unknown - MUST DETERMINE'
        company_location = getattr(company, 'location', None) or 'Unknown - MUST FIND'

        # Clean log for main status
        clean_log(f"Web Search Analysis: {company.name}")
        
        # Detailed logs for extra info
        detailed_log(f"Web Search Analysis: {company.name}")
        detailed_log(f"  Website: {company_website}")
        detailed_log(f"  Industry: {company_industry}")
        detailed_log(f"  Location: {company_location}")
        if retry_count > 0:
            detailed_log(f"  Retry Attempt: {retry_count + 1}/4")

        system_prompt = self.prompts.get_prompt(
            "web_enricher_system_prompt",
            company_name=company.name,
            company_website=company_website,
            company_industry=company_industry,
            company_location=company_location
        )

        # Get user prompt from centralized prompts
        base_user_prompt = self.prompts.get_prompt("web_enricher_user_prompt")
        
        # Add retry context if this is a retry attempt
        if retry_count > 0 and previous_context:
            user_prompt = f"""RETRY ATTEMPT {retry_count + 1}/4:

Previous attempt context: {previous_context}

Please try a different search approach or be more thorough in your analysis.

{base_user_prompt}"""
        else:
            user_prompt = base_user_prompt

        # Get output format prompt from centralized prompts
        output_format_prompt = self.prompts.get_prompt("web_enricher_output_format")

        try:
            model = "gpt-4o"
            log_llm_request(model, system_prompt, f"Web search analysis for {company.name} (attempt {retry_count + 1})")
            log_llm_request(model, user_prompt, f"Web search analysis for {company.name} (attempt {retry_count + 1})")
            log_llm_request(model, output_format_prompt, f"Web search analysis for {company.name} (attempt {retry_count + 1})")

            response = self.openai_client.responses.create(
                model=model,
                input=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    },
                    {
                        "role": "user",
                        "content": output_format_prompt
                    }
                ],
                tools=[
                    {
                        "type": "web_search_preview",
                        "user_location": {
                            "type": "approximate",
                            "country": "IN"
                        },
                        "search_context_size": "medium"
                    }
                ],
                temperature=0,
            )

            total_tokens = 0
            # Log token usage
            if hasattr(response, 'usage'):
                input_tokens = getattr(response.usage, 'input_tokens', 0)
                output_tokens = getattr(response.usage, 'output_tokens', 0)
                total_tokens = getattr(response.usage, 'total_tokens', 0)
                detailed_log(f"API Usage: {total_tokens:,} tokens (Input: {input_tokens:,}, Output: {output_tokens:,})")

            # Extract the analysis from the response
            analysis_content = response.output_text
            log_llm_response(model, analysis_content, f"Web search result for {company.name} (attempt {retry_count + 1})", total_tokens)

            try:
                # Remove any markdown formatting if present
                if analysis_content.startswith('```json'):
                    analysis_content = analysis_content[7:]
                if analysis_content.startswith('```'):
                    analysis_content = analysis_content[3:]
                if analysis_content.endswith('```'):
                    analysis_content = analysis_content[:-3]

                analysis_content = analysis_content.strip()
                # Try to parse as JSON
                analysis_data = orjson.loads(analysis_content)
                
                # Validate that we have meaningful data
                if self._validate_analysis_data(analysis_data, company.name):
                    clean_log(f"Web analysis completed: {company.name}")
                    detailed_log(f"Web Search Analysis completed for {company.name}")
                    detailed_log(f"  Status: SUCCESS")
                    detailed_log(f"  Retry Count: {retry_count}")
                    detailed_log(f"  Data Quality: Valid JSON with required fields")
                    return analysis_data
                else:
                    # Data validation failed, retry if possible
                    if retry_count < 3:
                        detailed_log(f"Web search data validation failed for {company.name} (attempt {retry_count + 1}). Retrying...", "warning")
                        context = f"Previous attempt returned incomplete data. Analysis content preview: {str(analysis_data)[:200]}..."
                        return await self.web_search_analysis(company, retry_count + 1, context)
                    else:
                        clean_log(f"Web search validation failed: {company.name}", "error")
                        detailed_log(f"Web search data validation failed after {retry_count + 1} attempts for {company.name}", "error")
                        return self._create_fallback_data(company.name, "validation_failed", retry_count + 1, analysis_data)
                        
            except Exception as json_error:
                # JSON parsing failed, retry if possible
                if retry_count < 3:
                    detailed_log(f"Web search JSON parse error for {company.name} (attempt {retry_count + 1}): {json_error}. Retrying...", "warning")
                    context = f"Previous attempt failed with JSON parse error. Raw response preview: {analysis_content[:200]}..."
                    return await self.web_search_analysis(company, retry_count + 1, context)
                else:
                    log_llm_error(model, f"JSON parse error after {retry_count + 1} attempts: {json_error}", f"Web search for {company.name}")
                    return self._create_fallback_data(company.name, "json_parse_error", retry_count + 1, analysis_content, json_error)

        except Exception as e:
            # General error, retry if possible
            if retry_count < 3:
                detailed_log(f"Web search analysis error for {company.name} (attempt {retry_count + 1}): {e}. Retrying...", "warning")
                context = f"Previous attempt failed with error: {str(e)}"
                return await self.web_search_analysis(company, retry_count + 1, context)
            else:
                log_llm_error("gpt-4o", f"Web search failed after {retry_count + 1} attempts: {e}", f"Web search for {company.name}")
                return self._create_fallback_data(company.name, "api_error", retry_count + 1, None, e)

    def _validate_analysis_data(self, data: Dict[str, Any], company_name: str) -> bool:
        """Validate that the analysis data contains required fields and meaningful content"""
        try:
            # Check for basic structure
            if not isinstance(data, dict):
                return False
            
            # Check for relevance assessment
            relevance = data.get('relevance_assessment', {})
            if not isinstance(relevance, dict) or 'is_relevant' not in relevance:
                detailed_log(f"Missing relevance_assessment for {company_name}", "warning")
                return False
            
            return True
            
        except Exception as e:
            detailed_log(f"Data validation error for {company_name}: {e}", "warning")
            return False

    def _create_fallback_data(self, company_name: str, error_type: str, retry_count: int, raw_data: Any = None, error: Exception = None) -> Dict[str, Any]:
        """Create fallback data structure when web search fails"""
        fallback_data = {
            "relevance_assessment": {
                "is_relevant": False,
                "confidence_level": "low",
                "reasoning": f"Analysis failed after {retry_count} attempts due to {error_type}",
                "key_factors": ["analysis_failed"]
            },
            "research_summary": {
                "company_overview": f"Research failed for {company_name}",
                "website_found": "Research failed",
                "industry_identified": "Unknown due to research failure",
                "location_identified": "Unknown due to research failure",
                "company_size": "Unknown due to research failure",
                "business_model": "Unknown due to research failure"
            },
            "web_search_analysis": {
                "search_successful": False,
                "total_sources_found": 0,
                "search_method": "failed",
                "debug_info": f"{error_type} after {retry_count} attempts"
            },
            "error_info": {
                "error_type": error_type,
                "retry_count": retry_count,
                "error_message": str(error) if error else "Unknown error",
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Include raw data if available for debugging
        if raw_data is not None:
            if error_type == "json_parse_error":
                fallback_data["raw_response"] = str(raw_data)[:500]  # Truncate for safety
            else:
                fallback_data["partial_data"] = raw_data
        
        detailed_log(f"Created fallback data for {company_name} - Error type: {error_type}, Retry count: {retry_count}", "error")
        
        return fallback_data


async def streamlined_web_enricher(state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
    """
    Streamlined LangGraph node with 2-step LLM-driven research:
    1. Web search analysis with retry logic
    
    Args:
        state: Current workflow state
        config: Configuration containing API keys and settings
        
    Returns:
        Updated workflow state with comprehensive research data
    """
    # Clean log for main status
    clean_log(f"Web Enrichment: {state.current_company.name if state.current_company else 'Unknown'}")
    
    # Detailed logs
    detailed_log("Streamlined Web Enrichment Starting")
    detailed_log(f"Processing company: {state.current_company.name if state.current_company else 'Unknown'}")

    config = config.get("configurable", {})

    if not state.current_company:
        error_msg = "No current company to research"
        clean_log("No current company to research", "error")
        detailed_log(error_msg, "error")
        state.errors.append(error_msg)
        return state

    company = state.current_company

    try:
        enricher = StreamlinedWebEnricher(config)

        # Get previously enriched data
        existing_data = state.enriched_data.get(company.name, {})

        # Step 1: Web Search Analysis with retry logic
        detailed_log(f"Web Search Analysis - Company: {company.name}, Website: {getattr(company, 'website', 'N/A')}")
        web_analysis = await enricher.web_search_analysis(company)

        # Combine all research data
        comprehensive_data = {
            **existing_data,
            "web_search_analysis": web_analysis,
            "research_timestamp": datetime.now().isoformat(),
            "research_steps_completed": ["web_search_analysis"]
        }
        state.enriched_data[company.name] = comprehensive_data

        # Log results and create relevance assessment
        relevance = web_analysis.get('relevance_assessment', {})
        is_relevant = relevance.get('is_relevant', False)
        confidence = relevance.get('confidence_level', 'unknown')
        reasoning = relevance.get('relevance_reason', 'No reasoning provided')
        key_factors = relevance.get('key_factors', [])
        
        # Get additional data from research summary
        research_summary = web_analysis.get('research_summary', {})
        website_analyzed = research_summary.get('website_found', getattr(company, 'website', None))
        industry_identified = research_summary.get('industry_identified', getattr(company, 'industry', None))
        
        # Create CompanyRelevance object and add to state
        company_relevance = CompanyRelevance(
            company_name=company.name,
            is_relevant=is_relevant,
            confidence_level=confidence,
            reasoning=reasoning,
            key_factors=key_factors,
            assessment_timestamp=comprehensive_data["research_timestamp"],
            website_analyzed=website_analyzed,
            industry_identified=industry_identified
        )
        
        # Add to state's relevance assessments list
        state.company_relevance_assessments.append(company_relevance)
        
        # Clean summary
        relevance_status = "RELEVANT" if is_relevant else "NOT RELEVANT"
        clean_log(f"Web enrichment completed: {company.name} - {relevance_status}")
        
        # Detailed completion
        detailed_log(f"Web Enrichment completed for {company.name}")
        detailed_log(f"  Status: SUCCESS")
        detailed_log(f"  Relevance: {'✅ RELEVANT' if is_relevant else '❌ NOT RELEVANT'}")
        detailed_log(f"  Confidence: {confidence.upper()}")
        detailed_log(f"  Research Steps: {len(comprehensive_data['research_steps_completed'])}")

        return state

    except Exception as e:
        error_msg = f"Streamlined web enrichment failed for {company.name}: {str(e)}"
        clean_log(f"Web enrichment failed: {company.name}", "error")
        detailed_log(f"Streamlined web enrichment failed for {company.name}: {str(e)}", "error")
        
        # Create fallback CompanyRelevance object for failed analysis
        fallback_relevance = CompanyRelevance(
            company_name=company.name,
            is_relevant=False,
            confidence_level="none",
            reasoning=f"Web enrichment failed: {str(e)}",
            key_factors=["enrichment_error"],
            assessment_timestamp=datetime.now().isoformat(),
            website_analyzed=getattr(company, 'website', None),
            industry_identified=getattr(company, 'industry', None)
        )
        
        # Add fallback relevance to state
        state.company_relevance_assessments.append(fallback_relevance)
        
        # Track in categorized error summary
        state.error_summary.web_enrichment_failures.append({
            "company": company.name,
            "error": str(e)
        })
        
        # Also add to general errors for backward compatibility
        state.errors.append(error_msg)
        return state
