"""
HubSpot Contact Creator Node

Creates HubSpot contacts from LinkedIn prospects data using HubSpot API Client
"""


import json
import time
import traceback
from typing import Dict, Any, List
from datetime import datetime

from hubspot import HubSpot
from hubspot.crm.contacts import SimplePublicObjectInput
from hubspot.crm.contacts.exceptions import ApiException
from hubspot.crm.owners import OwnersApi

from ai_agents.ai_sdr.sdr.models import WorkflowState
from ai_agents.ai_sdr.sdr.prompts import PromptsConfig
from ai_agents.ai_sdr.sdr.logging_config import log_llm_request, log_llm_response, log_llm_error, sdr_logger, clean_log, detailed_log

class HubspotContactCreator:

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        custom_prompts = config.get('custom_prompts', {})
        self.prompts = PromptsConfig(custom_prompts)
        self.client = HubSpot(access_token=self.config.get("hubspot_api_key"))

    async def create_hubspot_contacts(self, prospects: List[Dict[str, Any]], retry_count: int = 0,
                                      previous_context: str = "") -> Dict[str, Any]:
        try:
            clean_log(f"HubSpot Contact Creation: Processing {len(prospects)} prospects")
            detailed_log("")
            detailed_log("═══════════════════════════════════════")
            detailed_log("🏢 HubSpot Contact Creation Starting")
            detailed_log("═══════════════════════════════════════")


            detailed_log("")
            detailed_log(f"📋 Processing {len(prospects)} LinkedIn prospects for HubSpot")
            detailed_log("─" * 40)
            for i, prospect in enumerate(prospects[:5], 1):
                name = prospect.get("name", prospect.get("Person Name", "Unknown"))
                detailed_log(f"  {i:2d}. {name}")
            if len(prospects) > 5:
                detailed_log(f"      ... and {len(prospects) - 5} more prospects")
            detailed_log("")

            hubspot_owner_email = self.config.get("hubspot_owner_email", "no-owner@example.com")
            # instruction = self.prompts.get_prompt("hubspot_creator_instructions", hubspot_owner_email=hubspot_owner_email)

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

            log_llm_request("manual", prompt, f"HubSpot contact creation for {len(prospects)} prospects")
            detailed_log("🚀 Starting HubSpot contact creation process...")

            results = []
            for prospect in prospects:
                result = self._create_contact(prospect, hubspot_owner_email, retry_count)
                results.append(result)

            created_contacts = [r for r in results if r["status"] == "created"]
            failed_contacts = [r for r in results if r["status"] == "failed"]
            duplicates = [r for r in results if r.get("duplicate")]

            summary = {
                "total_processed": len(prospects),
                "successful": len(created_contacts),
                "failed": len(failed_contacts),
                "duplicates_found": len(duplicates),
                "field_retry_summary": "Field fallback retries applied where needed"
            }

            clean_log(f"HubSpot completed: {summary['successful']} created, {summary['failed']} failed, {summary['duplicates_found']} duplicates")
            detailed_log("")
            detailed_log("✅ HubSpot contact creation completed successfully")
            detailed_log("")
            detailed_log("📊 HubSpot Contact Creation Summary:")
            detailed_log("─" * 40)
            detailed_log(f"✅ Successfully Created: {summary['successful']}")
            detailed_log(f"❌ Failed to Create: {summary['failed']}")
            detailed_log(f"🔄 Duplicates Found: {summary['duplicates_found']}")
            detailed_log(f"📋 Total Processed: {summary['total_processed']}")
            detailed_log("")

            return {
                "created_contacts": created_contacts,
                "failed_contacts": failed_contacts,
                "summary": summary,
                "agent_response": json.dumps(results, indent=2),
                "hubspot_owner_id": self._get_owner_id(hubspot_owner_email)
            }
        except Exception as e:
            detailed_log(traceback.format_exc(), "error")
            clean_log(f"HubSpot creation failed: {str(e)}", "error")
            return self._create_error_response(prospects, str(e))

    def _create_contact(self, prospect: Dict[str, Any], owner_email: str, retry_count: int) -> Dict[str, Any]:
        try:
            email = prospect.get("email") or prospect.get("Person Email")
            if not email:
                return {"status": "failed", "reason": "Missing email", "prospect": prospect}

            if self._is_duplicate(email):
                return {"status": "skipped", "duplicate": True, "email": email}

            name = prospect.get("name") or prospect.get("Person Name")
            title = prospect.get("title") or prospect.get("Person Title")
            company = prospect.get("company") or prospect.get("Company Name")
            phone = prospect.get("phone_number") or prospect.get("Person Phone")
            linkedin = prospect.get("linkedin_profile") or prospect.get("Person LinkedIn")

            name_parts = name.split(" ") if name else []
            firstname = name_parts[0] if name_parts else ""
            lastname = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

            owner_id = self._get_owner_id(owner_email)

            field_sets = [
                ["email", "firstname", "lastname", "phone", "jobtitle", "company", "website", "hubspot_owner_id"],
                ["email", "firstname", "lastname", "jobtitle", "company", "hubspot_owner_id"],
                ["email", "firstname", "lastname"],
                ["email"]
            ]

            base = {
                "email": email,
                "firstname": firstname,
                "lastname": lastname,
                "phone": phone,
                "jobtitle": title,
                "company": company,
                "website": linkedin,
                "hubspot_owner_id": owner_id
            }

            for fields in field_sets:
                properties = {k: v for k, v in base.items() if k in fields and v}
                contact_input = SimplePublicObjectInput(properties=properties)
                try:
                    created = self.client.crm.contacts.basic_api.create(simple_public_object_input=contact_input)
                    return {"status": "created", "email": email, "hubspot_contact_id": created.id}
                except ApiException as e:
                    if e.status == 429:
                        time.sleep(2 ** retry_count)
                        continue
            return {"status": "failed", "email": email, "error": str(e), "http_status": getattr(e, 'status', 'unknown')}
        except Exception as e:
            detailed_log(traceback.format_exc(), "error")
            clean_log(f"HubSpot contact creation failed: {str(e)}", "error")
            return self._create_error_response(prospect, str(e))

    def _get_owner_id(self, owner_email: str) -> str:
        try:
            owners_api = OwnersApi(self.client)
            all_owners = owners_api.get_page()
            for owner in all_owners.results:
                if owner.email == owner_email:
                    return owner.id
        except Exception as e:
            detailed_log(f"Hubspot owner lookup failed: {e}", "warning")
        return ""

    def _is_duplicate(self, email: str) -> bool:
        try:
            search_payload = {
                "filterGroups": [{
                    "filters": [{"propertyName": "email", "operator": "EQ", "value": email}]
                }],
                "properties": ["email"]
            }
            api_response = self.client.crm.contacts.search_api.do_search(body=search_payload)
            return bool(api_response.results)
        except Exception as e:
            detailed_log(f"HubSpot duplicate check failed for {email}: {e}", "warning")
            return False

    def _create_error_response(self, prospects: List[Dict[str, Any]], error_message: str) -> Dict[str, Any]:
        return {
            "created_contacts": [],
            "failed_contacts": [{
                "error": error_message,
                "prospects_count": len(prospects),
                "note": "HubSpot API call failed completely",
                "failed_fields": ["all"],
                "retry_attempts": 3
            }],
            "summary": {
                "total_processed": len(prospects),
                "successful": 0,
                "failed": len(prospects),
                "field_retry_summary": "API failure - no retries possible"
            },
            "agent_response": None,
            "error": True
        }


async def hubspot_contact_creator(state: WorkflowState, config: Dict[str, Any] = None) -> WorkflowState:
    """
    Create HubSpot contacts from current company's LinkedIn prospects data

    Args:
        state: Current workflow state containing enriched LinkedIn data
        config: Configuration dictionary

    Returns:
        Updated workflow state with HubSpot contact creation results
    """

    if not state.current_company:
        detailed_log("No current company to process HubSpot contacts for", "warning")
        return state

    company = state.current_company
    
    detailed_log("")
    detailed_log(f"🔗 Starting HubSpot Contact Creation for {company.name}...")
    if config is None: 
        config = {}
    config = config.get("configurable", {})

    # Skip HubSpot creation if disabled
    if not config.get("create_hubspot_contacts", True):
        clean_log(f"HubSpot creation disabled for {company.name}")
        detailed_log("⚠️ HubSpot contact creation is disabled in configuration", "warning")
        return state

    try:
        # Get current company's enriched data
        company_data = state.enriched_data.get(company.name, {})
        linkedin_data = company_data.get('linkedin_prospect_data', {})
        
        # Extract executives found for this company
        executives_found = linkedin_data.get('executives_found', [])
        
        if not executives_found:
            clean_log(f"No executives found for {company.name} - skipping HubSpot", "warning")
            detailed_log(f"⚠️ No executives found for {company.name} - skipping HubSpot contact creation", "warning")
            return state

        # Prepare prospects data for HubSpot
        prospects_data = []
        for exec_profile in executives_found:
            # Add company name to each prospect
            prospect = {
                **exec_profile,
                'company_name': company.name
            }
            prospects_data.append(prospect)

        clean_log(f"Processing {len(prospects_data)} prospects for {company.name}")
        detailed_log(f"📋 LinkedIn executives to process: {len(prospects_data)} for {company.name}")

        # Filter for key decision makers only
        filtered_prospects = prospects_data
        clean_log(f"Key prospects identified: {len(filtered_prospects)} executives/managers for {company.name}")
        detailed_log(f"🎯 Key prospects after filtering: {len(filtered_prospects)}")
        detailed_log("")

        if not filtered_prospects:
            clean_log(f"No key prospects found after filtering for {company.name}", "warning")
            detailed_log(f"⚠️ No key prospects found after filtering for {company.name}", "warning")
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
                    "contact": f"{name} ({company.name})",
                    "error": str(error)
                })

        # Store results in company's enriched data
        state.enriched_data[company.name]["hubspot_results"] = {
            "created_contacts": creation_results.get("created_contacts", []),
            "failed_contacts": creation_results.get("failed_contacts", []),
            "total_processed": len(filtered_prospects),
            "created_count": len(creation_results.get("created_contacts", [])),
            "failed_count": len(creation_results.get("failed_contacts", [])),
            "duplicate_count": creation_results.get("summary", {}).get("duplicates_found", 0),
            "timestamp": datetime.now().isoformat(),
            "owner_email": config.get("hubspot_owner_email", "N/A"),
            "field_retry_summary": creation_results.get("summary", {}).get("field_retry_summary", "")
        }

        # Log summary
        success_count = len(creation_results.get("created_contacts", []))
        failure_count = len(creation_results.get("failed_contacts", []))

        detailed_log(f"✅ HubSpot Contact Creation Summary for {company.name}:")
        detailed_log(f"   📊 Total Processed: {len(filtered_prospects)}")
        detailed_log(f"   ✅ Successfully Created: {success_count}")
        detailed_log(f"   ❌ Failed to Create: {failure_count}")

        if success_count > 0:
            success_rate = (success_count / len(filtered_prospects)) * 100
            detailed_log(f"   📈 Success Rate: {success_rate:.1f}%")

        return state

    except Exception as e:
        error_msg = f"HubSpot contact creation failed for {company.name}: {str(e)}"
        clean_log(f"HubSpot service failed for {company.name}: {str(e)}", "error")
        detailed_log(error_msg, "error")
        
        # Track general HubSpot failure
        state.error_summary.hubspot_failures.append({
            "contact": f"All prospects for {company.name}",
            "error": f"HubSpot service failed: {str(e)}"
        })
        
        # Also add to general errors for backward compatibility
        state.errors.append(error_msg)
        return state


def filter_key_prospects(self,prospects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter prospects to include only executives and key decision makers"""
    try:

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
    except Exception as e:
        detailed_log(traceback.format_exc(), "error")
        clean_log(f"HubSpot filtering key prospects failed: {str(e)}", "error")
        return self._create_error_response(prospects, str(e))
