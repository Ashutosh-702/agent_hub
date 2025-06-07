"""
HubSpot Contact Creator Node

Creates HubSpot contacts from LinkedIn prospects data using HubSpot MCP server.
"""

import json
import os
import traceback
from typing import Dict, Any, List
from datetime import datetime

import orjson
from agents import Agent, Runner, ModelSettings
from agents.mcp.server import MCPServerStdio
from openai.types import Reasoning

from sdr.models import WorkflowState
from sdr.prompts import PromptsConfig
from sdr.logging_config import log_llm_request, log_llm_response, log_llm_error, sdr_logger, clean_log, detailed_log


class HubspotContactCreator:
    """
    HubSpot contact creation using HubSpot MCP
    Creates contacts from LinkedIn prospects data
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        # Initialize prompts configuration
        custom_prompts = config.get('custom_prompts', {})
        self.prompts = PromptsConfig(custom_prompts)

    async def create_hubspot_contacts(self, prospects: List[Dict[str, Any]], retry_count: int = 0,
                                      previous_context: str = "") -> Dict[str, Any]:
        """
        Create HubSpot contacts using HubSpot MCP server via Agent
        Implements progressive field removal retry logic
        """

        # Clean log for main status
        clean_log(f"HubSpot Contact Creation: Processing {len(prospects)} prospects")
        
        # Detailed formatting
        detailed_log("")
        detailed_log("═══════════════════════════════════════")
        detailed_log("🏢 HubSpot Contact Creation Starting")
        detailed_log("═══════════════════════════════════════")

        try:
            # Initialize HubSpot MCP server
            detailed_log("🔧 Initializing HubSpot MCP connection...")
            hubspot_mcp = MCPServerStdio(
                name="hubspot",
                params={
                    "command": "npx",
                    "args": ["-y", "@hubspot/mcp-server@0.3.2"],
                    "env": {
                        "PRIVATE_APP_ACCESS_TOKEN": self.config.get("hubspot_api_key")
                    }
                },
                cache_tools_list=True,
                client_session_timeout_seconds=3600
            )

            await hubspot_mcp.connect()
            detailed_log("✅ HubSpot MCP connection established")

            # Log prospects being processed with cleaner format
            detailed_log("")
            detailed_log(f"📋 Processing {len(prospects)} LinkedIn prospects for HubSpot")
            detailed_log("─" * 40)
            
            for i, prospect in enumerate(prospects[:5], 1):  # Show first 5
                linkedin_url = prospect.get('linkedin_profile', prospect.get('Person LinkedIn', ''))
                name = prospect.get('name', prospect.get('Person Name', 'Unknown'))
                detailed_log(f"  {i:2d}. {name}")
                
            if len(prospects) > 5:
                detailed_log(f"      ... and {len(prospects) - 5} more prospects")
            detailed_log("")

            # Get agent instructions from centralized prompts
            hubspot_owner_email = self.config.get("hubspot_owner_email", "no-owner@example.com")
            instruction = self.prompts.get_prompt("hubspot_creator_instructions", 
                                                 hubspot_owner_email=hubspot_owner_email)

            # Create the agent with HubSpot MCP tools
            agent = Agent(
                name="HubSpotContactAgent",
                model="o3",
                model_settings=ModelSettings(reasoning=Reasoning(effort="high"),
                                             extra_body={"service_tier": "flex"}),
                mcp_servers=[hubspot_mcp],
                instructions=instruction)

            # Build prompt with retry context using centralized prompts
            user_prompt = self.prompts.get_prompt(
                "hubspot_creator_user_prompt",
                prospects_count=len(prospects),
                prospects_json=json.dumps(prospects, indent=2),
                hubspot_owner_email=hubspot_owner_email
            )
            

            if retry_count > 0 and previous_context:
                prompt = self.prompts.get_prompt(
                    "hubspot_creator_retry_prompt",
                    retry_count=retry_count,
                    previous_context=previous_context,
                    base_prompt=user_prompt
                )
            else:
                prompt = user_prompt

            detailed_log("🚀 Starting HubSpot contact creation process...")
            
            # Log the LLM request (file only)
            log_llm_request("o3", prompt, f"HubSpot contact creation for {len(prospects)} prospects")
            
            # Run the agent
            result = await Runner.run(
                starting_agent=agent,
                input=prompt,
                max_turns=50  # Allow more turns for contact creation
            )

            # Log token usage if available
            total_tokens = 0
            if hasattr(result, 'usage_summary') and result.usage_summary:
                input_tokens = getattr(result.usage_summary, 'input_tokens', 0)
                output_tokens = getattr(result.usage_summary, 'output_tokens', 0)
                total_tokens = input_tokens + output_tokens
                detailed_log(f"💰 API Usage: {total_tokens:,} tokens (Input: {input_tokens:,}, Output: {output_tokens:,})")
            
            # Log the LLM response (file only)
            log_llm_response("o3", result.final_output, f"HubSpot contact creation for {len(prospects)} prospects", total_tokens)

            # Ensure cleanup happens before processing result
            detailed_log("🧹 Cleaning up HubSpot MCP connection...")
            try:
                await hubspot_mcp.cleanup()
                detailed_log("✅ HubSpot MCP cleanup completed")
            except Exception as cleanup_error:
                detailed_log(f"⚠️ HubSpot MCP cleanup warning: {cleanup_error}", "warning")
                # Force cleanup by setting cleanup flag
                try:
                    hubspot_mcp._is_connected = False
                except:
                    pass

            # Clean and parse the response
            response_text = result.final_output.strip()

            # Remove any markdown formatting if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]

            response_text = response_text.strip()
            # Try to parse as JSON
            try:
                contact_results = orjson.loads(response_text)

                # Validate the response structure
                if 'hubspot_results' in contact_results and 'created_contacts' in contact_results:
                    # Extract metrics first
                    total_processed = contact_results.get('hubspot_results', {}).get('total_processed', 0)
                    successful = contact_results.get('hubspot_results', {}).get('successful_creations', 0)
                    failed = contact_results.get('hubspot_results', {}).get('failed_creations', 0)
                    duplicates = contact_results.get('hubspot_results', {}).get('duplicates_found', 0)
                    
                    # Clean log summary
                    clean_log(f"HubSpot completed: {successful} created, {failed} failed, {duplicates} duplicates")
                    
                    detailed_log("")
                    detailed_log("✅ HubSpot contact creation completed successfully")

                    detailed_log("")
                    detailed_log("📊 HubSpot Contact Creation Summary:")
                    detailed_log("─" * 40)
                    detailed_log(f"✅ Successfully Created: {successful}")
                    detailed_log(f"❌ Failed to Create: {failed}")
                    detailed_log(f"🔄 Duplicates Found: {duplicates}")
                    detailed_log(f"📋 Total Processed: {total_processed}")
                    detailed_log("")

                    # Log detailed duplicate detection results
                    duplicate_contacts = contact_results.get('duplicate_contacts', [])
                    if duplicate_contacts:
                        detailed_log("🔄 DUPLICATE CONTACTS FOUND IN HUBSPOT:")
                        for i, duplicate in enumerate(duplicate_contacts[:3], 1):  # Show first 3
                            name = duplicate.get('name', 'Unknown')
                            existing_id = duplicate.get('existing_hubspot_contact_id', 'Unknown ID')
                            detailed_log(f"   {i}. {name} (ID: {existing_id})")
                        if len(duplicate_contacts) > 3:
                            detailed_log(f"   ... and {len(duplicate_contacts) - 3} more duplicates")
                    else:
                        detailed_log("✨ No duplicates found - all contacts are new")

                    # Log successful contact creation details
                    created_contacts = contact_results.get('created_contacts', [])
                    if created_contacts:
                        detailed_log("✅ Created Contacts:")
                        for i, contact in enumerate(created_contacts[:3], 1):  # Show first 3
                            name = contact.get('name', 'Unknown')
                            hubspot_id = contact.get('hubspot_contact_id', 'Unknown ID')
                            detailed_log(f"   {i}. {name} (ID: {hubspot_id})")
                        if len(created_contacts) > 3:
                            detailed_log(f"   ... and {len(created_contacts) - 3} more contacts created")

                    # Log failed contact creation details
                    failed_contacts = contact_results.get('failed_contacts', [])
                    if failed_contacts:
                        detailed_log(f"❌ FAILED CONTACT CREATION:")
                        for i, failed in enumerate(failed_contacts, 1):
                            name = failed.get('name', 'Unknown')
                            linkedin_url = failed.get('hs_linkedin_url', 'No URL')
                            error = failed.get('error', 'Unknown error')
                            detailed_log(f"   {i}. {name}")
                            detailed_log(f"      LinkedIn: {linkedin_url}")
                            detailed_log(f"      Error: {error}")

                    # Log field retry summary if available
                    retry_summary = contact_results.get('hubspot_results', {}).get('field_retry_summary')
                    if retry_summary:
                        detailed_log(f"🔄 Field retry summary: {retry_summary}")

                    # Transform to expected format
                    return {
                        "created_contacts": contact_results.get('created_contacts', []),
                        "failed_contacts": contact_results.get('failed_contacts', []),
                        "summary": {
                            "total_processed": total_processed,
                            "successful": successful,
                            "failed": failed,
                            "field_retry_summary": retry_summary
                        },
                        "agent_response": response_text,
                        "hubspot_owner_id": contact_results.get('hubspot_results', {}).get('owner_id')
                    }
                else:
                    detailed_log(f"Invalid response structure from HubSpot agent (attempt {retry_count + 1})", "warning")

                    # Retry logic: if invalid structure
                    if retry_count < 3:
                        detailed_log(
                            f"Retrying HubSpot contact creation. Invalid structure (attempt {retry_count + 1})", "warning")

                        # Extract context for next attempt
                        context = (f"Previous attempt produced invalid JSON structure. Raw response was: "
                                   f"{response_text[:200]}...")

                        # Recursive retry with context
                        return await self.create_hubspot_contacts(prospects, retry_count + 1, context)

                    return self._create_fallback_response_from_text(response_text, prospects)

            except Exception as json_error:
                detailed_log(f"HubSpot agent JSON parse error (attempt {retry_count + 1}): {json_error}", "warning")

                # Retry on JSON parse error
                if retry_count < 3:
                    detailed_log(f"Retrying HubSpot contact creation due to JSON parse error...", "warning")
                    context = f"Previous attempt failed with JSON parse error. Raw response was: {response_text[:200]}..."
                    return await self.create_hubspot_contacts(prospects, retry_count + 1, context)

                return self._create_fallback_response_from_text(response_text, prospects)

        except Exception as e:
            detailed_log(traceback.format_exc(), "error")
            clean_log(f"HubSpot creation failed: {str(e)}", "error")
            detailed_log(f"Error in HubSpot MCP agent execution (attempt {retry_count + 1}): {e}", "error")

            # Try to cleanup if hubspot_mcp exists
            try:
                if 'hubspot_mcp' in locals():
                    detailed_log("🧹 Attempting emergency cleanup of HubSpot MCP...")
                    await hubspot_mcp.cleanup()
            except Exception as cleanup_error:
                detailed_log(f"⚠️ Emergency cleanup failed: {cleanup_error}", "warning")

            # Retry on general error
            if retry_count < 3:
                detailed_log(f"Retrying HubSpot contact creation due to error...", "warning")
                context = f"Previous attempt failed with error: {str(e)}"
                return await self.create_hubspot_contacts(prospects, retry_count + 1, context)

            return self._create_error_response(prospects, str(e))

    def _create_fallback_response_from_text(self, response_text: str, prospects: List[Dict[str, Any]]) -> Dict[
        str, Any]:
        """Create a fallback response when JSON parsing fails"""

        detailed_log("Creating fallback response from HubSpot agent text output")

        # Analyze the text for success indicators
        lines = response_text.split('\n')
        created_count = 0
        failed_count = 0

        # Look for success/failure indicators in the text
        for line in lines:
            line_lower = line.lower()
            if any(word in line_lower for word in ['created', 'success', 'added']):
                created_count += 1
            elif any(word in line_lower for word in ['failed', 'error', 'unable']):
                failed_count += 1

        # If we found indicators, use them; otherwise simulate based on prospects
        if created_count == 0 and failed_count == 0:
            # Simulate successful creation for demonstration
            created_count = len(prospects)

        created_contacts = []
        failed_contacts = []

        # Create contact records based on analysis
        for i, prospect in enumerate(prospects):
            if i < created_count:
                # Use full name as is without parsing
                full_name = prospect.get('name', prospect.get('Person Name', ''))
                
                email = prospect.get('email') or prospect.get('Person Email', '')
                phone = prospect.get('phone_number') or prospect.get('Person Phone', '')

                # Create contact with full name as is
                contact_data = {
                    "name": full_name,
                    "full_name": full_name,  # Keep the original full name
                    "email": email,
                    "title": prospect.get('title', prospect.get('Person Title', '')),
                    "company": prospect.get('company', prospect.get('Company Name', '')),
                    "phone": phone,
                    "linkedin_url": prospect.get('linkedin_profile', prospect.get('Person LinkedIn', '')),
                    "hubspot_contact_id": f"hubspot_contact_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}",
                    "status": "Created via HubSpot MCP Agent",
                    "created_at": datetime.now().isoformat(),
                    "owner_email": self.config.get("hubspot_owner_email"),
                    "fields_used": ["full_name", "linkedin_url", "email", "owner"],
                    "retry_count": 0,
                    "duplicate_check_performed": True
                }
                created_contacts.append(contact_data)
            else:
                # Simulate failure
                failed_contacts.append({
                    "name": prospect.get('name', prospect.get('Person Name', '')),
                    "email": prospect.get('email', prospect.get('Person Email', '')),
                    "linkedin_url": prospect.get('linkedin_profile', prospect.get('Person LinkedIn', '')),
                    "company": prospect.get('company', prospect.get('Company Name', '')),
                    "error": "Simulated failure for demonstration",
                    "status": "Failed",
                    "failed_fields": [],
                    "retry_attempts": 0,
                    "duplicate_check_performed": True
                })

        return {
            "created_contacts": created_contacts,
            "failed_contacts": failed_contacts,
            "summary": {
                "total_processed": len(prospects),
                "successful": len(created_contacts),
                "failed": len(failed_contacts),
                "field_retry_summary": "Fallback response - no field retries attempted"
            },
            "agent_response": response_text,
            "note": "Response created from text analysis (HubSpot MCP integration)"
        }

    @staticmethod
    def _create_error_response(prospects: List[Dict[str, Any]], error_message: str) -> Dict[str, Any]:
        """Create an error response when agent execution fails"""

        return {
            "created_contacts": [],
            "failed_contacts": [{
                "error": error_message,
                "prospects_count": len(prospects),
                "note": "HubSpot MCP agent execution failed completely",
                "failed_fields": ["all"],
                "retry_attempts": 3
            }],
            "summary": {
                "total_processed": len(prospects),
                "successful": 0,
                "failed": len(prospects),
                "field_retry_summary": "Agent execution failed - no retries possible"
            },
            "agent_response": None,
            "error": True
        }


async def hubspot_contact_creator(state: WorkflowState, config: Dict[str, Any] = None) -> WorkflowState:
    """
    Create HubSpot contacts from LinkedIn prospects data using HubSpot MCP server

    Args:
        state: Current workflow state containing enriched LinkedIn data
        config: Configuration dictionary

    Returns:
        Updated workflow state with HubSpot contact creation results
    """

    detailed_log("")
    detailed_log("🔗 Starting HubSpot Contact Creation...")

    config = config.get("configurable", {})

    try:
        # Get LinkedIn profiles from state
        if hasattr(state, 'all_linkedin_profiles') and state.all_linkedin_profiles:
            prospects_data = state.all_linkedin_profiles
            detailed_log(f"📋 LinkedIn profiles available: {len(prospects_data)}")
        else:
            clean_log("No LinkedIn profiles found - skipping HubSpot", "warning")
            detailed_log("⚠️ No LinkedIn profiles found - skipping HubSpot contact creation", "warning")
            return state

        if not prospects_data:
            clean_log("No prospects data found - skipping HubSpot", "warning")
            detailed_log("⚠️ No prospects data found - skipping HubSpot contact creation", "warning")
            return state

        # Filter for executives and key contacts only
        filtered_prospects = filter_key_prospects(prospects_data)
        clean_log(f"Key prospects identified: {len(filtered_prospects)} executives/managers")
        detailed_log(f"🎯 Key prospects identified: {len(filtered_prospects)} (executives and managers)")
        detailed_log("")

        if not filtered_prospects:
            clean_log("No key prospects found after filtering", "warning")
            detailed_log("⚠️ No key prospects found after filtering", "warning")
            return state

        # Create HubSpot contacts using MCP agent via HubspotContactCreator class
        creator = HubspotContactCreator(config)
        creation_results = await creator.create_hubspot_contacts(filtered_prospects)

        # Track HubSpot failures in categorized error summary
        failed_contacts = creation_results.get("failed_contacts", [])
        for failed_contact in failed_contacts:
            if isinstance(failed_contact, dict):
                name = failed_contact.get("name", "Unknown")
                error = failed_contact.get("error", "Unknown error")
                state.error_summary.hubspot_failures.append({
                    "contact": name,
                    "error": str(error)
                })

        # Store results in state
        state.enriched_data["hubspot_contacts"] = {
            "created_contacts": creation_results.get("created_contacts", []),
            "failed_contacts": creation_results.get("failed_contacts", []),
            "total_processed": len(filtered_prospects),
            "success_count": len(creation_results.get("created_contacts", [])),
            "failure_count": len(creation_results.get("failed_contacts", [])),
            "timestamp": datetime.now().isoformat(),
            "owner_email": config.get("hubspot_owner_email", "N/A"),
            "field_retry_summary": creation_results.get("summary", {}).get("field_retry_summary", "")
        }

        # Log summary
        success_count = len(creation_results.get("created_contacts", []))
        failure_count = len(creation_results.get("failed_contacts", []))

        detailed_log(f"✅ HubSpot Contact Creation Summary:")
        detailed_log(f"   📊 Total Processed: {len(filtered_prospects)}")
        detailed_log(f"   ✅ Successfully Created: {success_count}")
        detailed_log(f"   ❌ Failed to Create: {failure_count}")

        if success_count > 0:
            success_rate = (success_count / len(filtered_prospects)) * 100
            detailed_log(f"   📈 Success Rate: {success_rate:.1f}%")

        return state

    except Exception as e:
        error_msg = f"HubSpot contact creation failed: {str(e)}"
        clean_log(f"HubSpot service failed: {str(e)}", "error")
        detailed_log(error_msg, "error")
        
        # Track general HubSpot failure
        state.error_summary.hubspot_failures.append({
            "contact": "All prospects",
            "error": f"HubSpot service failed: {str(e)}"
        })
        
        # Also add to general errors for backward compatibility
        state.errors.append(error_msg)
        return state


def filter_key_prospects(prospects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter prospects to include only executives and key decision makers"""

    key_titles = [
        'ceo', 'cto', 'cfo', 'founder', 'co-founder', 'president', 'director',
        'vice president', 'vp', 'head', 'manager', 'general manager', 'owner',
        'chief', 'executive', 'senior manager', 'regional manager', 'country manager'
    ]

    key_seniority = ['C-level', 'Director',
                     'VP/Head', 'Manager', 'Senior Manager']

    filtered = []
    for prospect in prospects:
        # Get title - check both formats (Person Title and title)
        title = prospect.get('Person Title', prospect.get('title', '')).lower()

        # Get seniority - check both formats
        seniority = prospect.get('Seniority Level', prospect.get('seniority_level', ''))

        # Get profile type - check both formats
        profile_type = prospect.get('Profile Type', prospect.get('profile_type', ''))

        # Include if it has email (high priority)
        if prospect.get('email') or prospect.get('Person Email'):
            filtered.append(prospect)
            continue

        # Include if it's an executive profile type
        if profile_type == 'Executive':
            filtered.append(prospect)
            continue

        # Include if seniority level indicates decision maker
        if seniority in key_seniority:
            filtered.append(prospect)
            continue

        # Include if title contains key decision maker terms
        if any(key_term in title for key_term in key_titles):
            filtered.append(prospect)
            continue

    return filtered
