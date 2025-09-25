

from datetime import datetime
from typing import Dict, Any

import orjson
from openai import OpenAI

from ai_agents.ai_sdr.sdr.models import Company
from ai_agents.ai_sdr.sdr.prompts import PromptsConfig
from config.loaded_config import loaded_config
from database.collection_dao.companies import CompaniesDao
from database.collection_dao.campaign_company_runs import CampaignCompanyRunsDao
from bson import ObjectId


class CompanyRelevanceCheck:
    """
    Streamlined company research with 2 LLM calls:
    1. Web search analysis and data gathering
    2. Browser-based data enrichment
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.openai_client = OpenAI(api_key=loaded_config.openai_api_key)
        custom_prompts = config.get('prompts', {})
        self.prompts = PromptsConfig(custom_prompts)

    async def web_search_analysis(self, company: Company, retry_count: int = 0, previous_context: str = "") -> Dict[str, Any]:

        # Get system prompt from centralized prompts - safely handle None values
        company_website = getattr(
            company, 'website', None) or 'Unknown - MUST FIND'
        company_industry = getattr(
            company, 'industry', None) or 'Unknown - MUST DETERMINE'
        company_location = getattr(
            company, 'location', None) or 'Unknown - MUST FIND'

        # Clean log for main status
        print(f"Web Search Analysis: {company.name}")

        if retry_count > 0:
            print(f"  Retry Attempt: {retry_count + 1}/4")

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
        output_format_prompt = self.prompts.get_prompt(
            "web_enricher_output_format")

        try:
            model = "gpt-4o"
            print(
                model, system_prompt, f"Web search analysis for {company.name} (attempt {retry_count + 1})")
            print(
                model, user_prompt, f"Web search analysis for {company.name} (attempt {retry_count + 1})")
            print(model, output_format_prompt,
                  f"Web search analysis for {company.name} (attempt {retry_count + 1})")

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
                print(
                    f"API Usage: {total_tokens:,} tokens (Input: {input_tokens:,}, Output: {output_tokens:,})")

            # Extract the analysis from the response
            analysis_content = response.output_text
            print(
                model, analysis_content, f"Web search result for {company.name} (attempt {retry_count + 1})", total_tokens)

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
                    print(f"Web analysis completed: {company.name}")
                    print(
                        f"Web Search Analysis completed for {company.name}")
                    print(f"  Status: SUCCESS")
                    print(f"  Retry Count: {retry_count}")
                    print(
                        f"  Data Quality: Valid JSON with required fields")
                    return analysis_data
                else:
                    # Data validation failed, retry if possible
                    if retry_count < 3:
                        print(
                            f"Web search data validation failed for {company.name} (attempt {retry_count + 1}). Retrying...", "warning")
                        context = f"Previous attempt returned incomplete data. Analysis content preview: {str(analysis_data)[:200]}..."
                        return await self.web_search_analysis(company, retry_count + 1, context)
                    else:
                        print(
                            f"Web search validation failed: {company.name}", "error")
                        print(
                            f"Web search data validation failed after {retry_count + 1} attempts for {company.name}", "error")
                        return self._create_fallback_data(company.name, "validation_failed", retry_count + 1, analysis_data)

            except Exception as json_error:
                # JSON parsing failed, retry if possible
                if retry_count < 3:
                    print(
                        f"Web search JSON parse error for {company.name} (attempt {retry_count + 1}): {json_error}. Retrying...", "warning")
                    context = f"Previous attempt failed with JSON parse error. Raw response preview: {analysis_content[:200]}..."
                    return await self.web_search_analysis(company, retry_count + 1, context)
                else:
                    print(
                        model, f"JSON parse error after {retry_count + 1} attempts: {json_error}", f"Web search for {company.name}")
                    return self._create_fallback_data(company.name, "json_parse_error", retry_count + 1, analysis_content, json_error)

        except Exception as e:
            # General error, retry if possible
            if retry_count < 3:
                print(
                    f"Web search analysis error for {company.name} (attempt {retry_count + 1}): {e}. Retrying...", "warning")
                context = f"Previous attempt failed with error: {str(e)}"
                return await self.web_search_analysis(company, retry_count + 1, context)
            else:
                print(
                    "gpt-4o", f"Web search failed after {retry_count + 1} attempts: {e}", f"Web search for {company.name}")
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
                print(
                    f"Missing relevance_assessment for {company_name}", "warning")
                return False

            return True

        except Exception as e:
            print(
                f"Data validation error for {company_name}: {e}", "warning")
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
                fallback_data["raw_response"] = str(
                    raw_data)[:500]  # Truncate for safety
            else:
                fallback_data["partial_data"] = raw_data

        print(
            f"Created fallback data for {company_name} - Error type: {error_type}, Retry count: {retry_count}", "error")

        return fallback_data

    async def company_relevance_check(self, campaign_id: str) -> Any:

        try:
            prompts = self.config.get('prompts', {})
            web_enricher_user_prompt = prompts.get('web', '')
            prospect_enricher_target_executives = prompts.get('persona', '')
            custom_prompts = {
                'web_enricher_user_prompt': web_enricher_user_prompt,
                'prospect_enricher_target_executives': prospect_enricher_target_executives
            }

            self.prompts = PromptsConfig(custom_prompts)

            page = 1
            limit = 50

            companies_dao = CompaniesDao(
                loaded_config.connection_manager.mongo_client)

            campaign_company_runs_dao = CampaignCompanyRunsDao(
                loaded_config.connection_manager.mongo_client)

            company_count = await campaign_company_runs_dao.get_campaign_company_runs_count({"campaign_id": ObjectId(campaign_id)})
            print(f"  Company count: {company_count}")
            count = 0
            total_pages = (company_count + limit - 1) // limit
            print(f"total_pages: {total_pages}")

            for page in range(1, total_pages + 1):

                campaign_company_runs = await campaign_company_runs_dao.get_campaign_company_runs_paginated(
                    {"campaign_id": ObjectId(campaign_id)}, page=page, limit=limit)

                for campaign_company_run in campaign_company_runs[0]:
                    count += 1
                    company_id = campaign_company_run.get("company_id")
                    company = await companies_dao.get_company(ObjectId(company_id))
                    company_name = self.safe_extract_array(
                        company, "identifiers", "name")

                    print(f"  current company count: {count}/{company_count}")
                    print(f"  Company: {company_name}")

                    company_data = Company(
                        company_id=str(company.get("_id", "")),
                        name=self.safe_extract_array(
                            company, "identifiers", "name"),
                        industry=self.safe_extract_array(
                            company, "profile", "industry"),
                        location=self.safe_extract_array(
                            company, "location", "name"),
                        size=self.safe_extract_array(
                            company, "profile", "employee_count"),
                    )

                    web_analysis = await self.web_search_analysis(company_data)

                    # Log results and create relevance assessment
                    relevance = web_analysis.get('relevance_assessment', {})
                    is_relevant = relevance.get('is_relevant', False)
                    confidence = relevance.get('confidence_level', 'unknown')
                    reasoning = relevance.get(
                        'relevance_reason', 'No reasoning provided')
                    key_factors = relevance.get('key_factors', [])

                    campaign_run = campaign_company_run
                    update_data = {
                        "$set": {
                            "is_relevant": is_relevant,
                            "metadata.relevance_reason": reasoning,
                            "metadata.confidence_level": confidence,
                            "metadata.key_factors": key_factors,
                            "metadata.updated_at": datetime.utcnow()
                        }
                    }
                    # Update the document
                    update_result = await campaign_company_runs_dao.update_campaign_company_run(
                        {"_id": campaign_run["_id"]},
                        update_data
                    )

                    if update_result:
                        print(
                            f"✅ Campaign company run updated for company {company_name}")
                    else:
                        print(
                            f"❌ Failed to update campaign company run for company {company_name}")

            print(f"total company relevance update: {count}")

        except Exception as e:
            print(f"error: {e}")
        finally:
            return

    def safe_extract_array(self, data, *keys, default=""):
        """Safely extract from nested dict and handle arrays"""
        try:
            value = data

            for key in keys:
                value = value.get(key, {})

            # Handle array values - take first element or join
            if isinstance(value, list):
                if len(value) > 0:
                    # For arrays, take first element or join with comma
                    return value[0] if len(value) == 1 else ", ".join(str(v) for v in value)
                else:
                    return default

            return str(value) if value else default

        except (AttributeError, TypeError, KeyError):
            return default
