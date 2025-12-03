
from datetime import datetime
from typing import Dict, Any, List, Optional

import orjson
from openai import AsyncOpenAI
from ai_agents.ai_sdr.sdr.prompts import PromptsConfig, PEOPLE_SYSTEM_PROMPT, PEOPLE_ASSESSMENT_TEMPLATE
from config.loaded_config import loaded_config
from config.logging import logger


class PeopleRelevanceCheck:
    """
    Streamlined people/contact research with web search analysis
    Assesses whether contacts meet relevance criteria using OpenAI with web search
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.openai_client = AsyncOpenAI(api_key=loaded_config.openai_api_key)
        custom_prompts = config.get('prompts', {})
        self.prompts = PromptsConfig(custom_prompts)

    async def web_search_analysis(self, person_data: Dict[str, Any], retry_count: int = 0, previous_context: str = "") -> Dict[str, Any]:
        # Extract person information - safely handle None values
        person_name = person_data.get('name', '') or (person_data.get('first_name', '') + ' ' + person_data.get('last_name', '')).strip() or 'Unknown - MUST FIND'
        person_title = person_data.get('title', None) or 'Unknown - MUST DETERMINE'
        person_company = person_data.get('source_organization_name') or person_data.get('organization_name', None) or 'Unknown - MUST FIND'
        person_email = person_data.get('email', None) or 'Unknown'
        person_linkedin = person_data.get('linkedin_url', None) or 'Unknown'
        person_seniority = person_data.get('seniority', None) or 'Unknown'
        person_department = person_data.get('departments', None) or 'Unknown'
        apollo_id = person_data.get('id', '') or person_data.get('person_id', '')


        # Clean log for main status
        print(f"Web Search Analysis: {person_name}")

        if retry_count > 0:
            print(f"  Retry Attempt: {retry_count + 1}/4")

        # Get system prompt - check custom prompts first, then use default
        custom_system_prompt = self.config.get('prompts', {}).get('people_enricher_system_prompt')
        system_prompt = custom_system_prompt if custom_system_prompt else PEOPLE_SYSTEM_PROMPT

        apollo_data_formatted = "\n".join([
            f"  - {k}: {v}" for k, v in person_data.items()
            if v and v != "" and k not in ['id', 'person_id', 'source_organization_id']
        ])

        # Get user prompt template - check custom prompts first, then use default
        custom_user_prompt = self.config.get('prompts', {}).get('people_enricher_user_prompt')
        base_user_prompt_template = custom_user_prompt if custom_user_prompt else PEOPLE_ASSESSMENT_TEMPLATE

        # Get relevance criteria using the proper method
        relevance_criteria = self.prompts.get_relevance_criteria()

        # Format the user prompt with variables (similar to system prompt)
        try:
            base_user_prompt = base_user_prompt_template.format(
                person_name=person_name,
                person_title=person_title,
                company_name=person_company,
                apollo_id=apollo_id,
                apollo_data=apollo_data_formatted,
                relevance_criteria=relevance_criteria
            )
        except KeyError as e:
            # If template doesn't have all variables, use as-is
            base_user_prompt = base_user_prompt_template


        # Add retry context if this is a retry attempt
        if retry_count > 0 and previous_context:
            user_prompt = f"""RETRY ATTEMPT {retry_count + 1}/4:

Previous attempt context: {previous_context}

Please try a different search approach or be more thorough in your analysis.

{base_user_prompt}"""
        else:
            user_prompt = base_user_prompt
            

        # Get output format prompt - check custom prompts first, then use default
        custom_output_format = self.config.get('prompts', {}).get('people_enricher_output_format')
        output_format_prompt = custom_output_format if custom_output_format else """CRITICAL: You MUST respond with ONLY valid JSON in this exact format, 
Return ONLY the JSON object—do NOT include any markdown or ``` before/after.:

{
    "relevance_assessment": {
        "is_relevant": true/false,
        "reason": "Detailed explanation of why person is or isn't relevant based on criteria"
    }
}"""

        try:
            model = "gpt-4o"
            print(
                model, system_prompt, f"Web search analysis for {person_name} (attempt {retry_count + 1})")
            print(
                model, user_prompt, f"Web search analysis for {person_name} (attempt {retry_count + 1})")
            print(model, output_format_prompt,
                  f"Web search analysis for {person_name} (attempt {retry_count + 1})")

            response = await self.openai_client.responses.create(
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
                model, analysis_content, f"Web search result for {person_name} (attempt {retry_count + 1})", total_tokens)

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
                if self._validate_analysis_data(analysis_data, person_name):
                    print(f"Web analysis completed: {person_name}")
                    print(
                        f"Web Search Analysis completed for {person_name}")
                    print(f"  Status: SUCCESS")
                    print(f"  Retry Count: {retry_count}")
                    print(
                        f"  Data Quality: Valid JSON with required fields")
                    return analysis_data
                else:
                    # Data validation failed, retry if possible
                    if retry_count < 3:
                        print(
                            f"Web search data validation failed for {person_name} (attempt {retry_count + 1}). Retrying...", "warning")
                        context = f"Previous attempt returned incomplete data. Analysis content preview: {str(analysis_data)[:200]}..."
                        return await self.web_search_analysis(person_data, retry_count + 1, context)
                    else:
                        print(
                            f"Web search validation failed: {person_name}", "error")
                        print(
                            f"Web search data validation failed after {retry_count + 1} attempts for {person_name}", "error")
                        return self._create_fallback_data(person_name, "validation_failed", retry_count + 1, analysis_data)

            except Exception as json_error:
                # JSON parsing failed, retry if possible
                if retry_count < 3:
                    print(
                        f"Web search JSON parse error for {person_name} (attempt {retry_count + 1}): {json_error}. Retrying...", "warning")
                    context = f"Previous attempt failed with JSON parse error. Raw response preview: {analysis_content[:200]}..."
                    return await self.web_search_analysis(person_data, retry_count + 1, context)
                else:
                    print(
                        model, f"JSON parse error after {retry_count + 1} attempts: {json_error}", f"Web search for {person_name}")
                    return self._create_fallback_data(person_name, "json_parse_error", retry_count + 1, analysis_content, json_error)

        except Exception as e:
            # General error, retry if possible
            if retry_count < 3:
                print(
                    f"Web search analysis error for {person_name} (attempt {retry_count + 1}): {e}. Retrying...", "warning")
                context = f"Previous attempt failed with error: {str(e)}"
                return await self.web_search_analysis(person_data, retry_count + 1, context)
            else:
                print(
                    "gpt-4o", f"Web search failed after {retry_count + 1} attempts: {e}", f"Web search for {person_name}")
                return self._create_fallback_data(person_name, "api_error", retry_count + 1, None, e)

    def _validate_analysis_data(self, data: Dict[str, Any], person_name: str) -> bool:
        """Validate that the analysis data contains required fields and meaningful content"""
        try:
            # Check for basic structure
            if not isinstance(data, dict):
                return False

            # Check for relevance assessment with is_relevant and reason
            relevance = data.get('relevance_assessment', {})

            if not isinstance(relevance, dict):
                print(
                    f"Missing relevance_assessment for {person_name}", "warning")
                return False

            if 'is_relevant' not in relevance:
                print(
                    f"Missing is_relevant field for {person_name}", "warning")
                return False

            if 'reason' not in relevance:
                print(
                    f"Missing reason field for {person_name}", "warning")
                return False

            return True

        except Exception as e:
            print(
                f"Data validation error for {person_name}: {e}", "warning")
            return False

    def _create_fallback_data(self, person_name: str, error_type: str, retry_count: int, raw_data: Any = None, error: Exception = None) -> Dict[str, Any]:
        """Create fallback data structure when web search fails"""
        fallback_data = {
            "relevance_assessment": {
                "is_relevant": False,
                "reason": f"Analysis failed after {retry_count} attempts due to {error_type}"
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
            f"Created fallback data for {person_name} - Error type: {error_type}, Retry count: {retry_count}", "error")

        return fallback_data

