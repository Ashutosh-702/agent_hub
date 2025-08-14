"""
HubSpot Contact Creator Node

Creates HubSpot contacts from LinkedIn prospects data using HubSpot API Client
"""

import json
import time
import traceback
from datetime import datetime
from typing import Dict, Any, List

from hubspot import HubSpot
from hubspot.crm.contacts import PublicObjectSearchRequest, SimplePublicObjectInputForCreate
from hubspot.crm.contacts.exceptions import ApiException

from ai_agents.ai_sdr.sdr.logging_config import clean_log, detailed_log
from ai_agents.ai_sdr.sdr.models import WorkflowState

from bson import ObjectId
from datetime import datetime
from database.collection_dao.contacts import ContactsDao
from database.collection_dao.company_mappings import CompanyMappingsDao
from config.loaded_config import loaded_config


class HubspotContactCreator:

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = HubSpot(access_token=self.config.get("hubspot_api_key"), verify_ssl=False)

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

            detailed_log("🚀 Starting HubSpot contact creation process...")

            results = []
            for prospect in prospects:
                result = self._create_contact(prospect, hubspot_owner_email, retry_count)
                if "status" not in result:
                    result["status"] = "failed"
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

            clean_log(
                f"HubSpot completed: {summary['successful']} created, {summary['failed']} failed, {summary['duplicates_found']} duplicates")
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
            linkedin_url = prospect.get("linkedin_profile") or prospect.get("Person LinkedIn")
            if self._is_duplicate(linkedin_url):
                return {"status": "skipped", "duplicate": True, "linkedin_url": linkedin_url}

            name = prospect.get("name") or prospect.get("Person Name")
            title = prospect.get("title") or prospect.get("Person Title")
            company = prospect.get("company") or prospect.get("Company Name")
            phone = prospect.get("phone_number") or prospect.get("Person Phone")

            name_parts = name.split(" ") if name else []
            firstname = name_parts[0] if name_parts else ""
            lastname = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

            owner_id = self._get_owner_id(owner_email)

            field_sets = [
                ["linkedin_url", "email", "firstname", "lastname", "phone", "jobtitle", "company", "hubspot_owner_id",
                 "source", "product", "ci_lifecycle_stage"],
                ["linkedin_url", "firstname", "lastname", "jobtitle", "company", "hubspot_owner_id", "source",
                 "product", "ci_lifecycle_stage"],
                ["linkedin_url", "firstname", "lastname", "source", "product", "ci_lifecycle_stage"],
                ["linkedin_url", "source", "product", "ci_lifecycle_stage"]
            ]

            base = {
                "email": email,
                "firstname": firstname,
                "lastname": lastname,
                "phone": phone,
                "jobtitle": title,
                "company": company,
                "linkedin_url": linkedin_url,
                "hubspot_owner_id": owner_id,
                "source": "AI-SDR",
                "product": self.config.get("PRODUCT_NAME", ""),
                "ci_lifecycle_stage": "Not Contacted",
            }

            #### Custom Updates Above

            for fields in field_sets:
                properties = {k: v for k, v in base.items() if k in fields and v}
                contact_input = SimplePublicObjectInputForCreate(properties=properties)
                try:
                    created = self.client.crm.contacts.basic_api.create(
                        simple_public_object_input_for_create=contact_input)
                    return {"status": "created", "linkedin_url": linkedin_url, "hubspot_contact_id": created.id}
                except ApiException as e:
                    if e.status == 429:
                        time.sleep(2 ** retry_count)
                        continue
                    return {"status": "failed", "linkedin_url": linkedin_url, "error": str(e),
                            "http_status": getattr(e, 'status', 'unknown')}
        except Exception as e:
            detailed_log(traceback.format_exc(), "error")
            clean_log(f"HubSpot contact creation failed: {str(e)}", "error")
            return self._create_error_response([prospect], str(e))

    def _get_owner_id(self, owner_email: str) -> str:
        """
        Get owner ID by email address
        
        Args:
            owner_email: Email address of the owner
            
        Returns:
            Owner ID if found, email prefix as fallback
        """
        if not owner_email:
            return ""

        try:
            # Get all owners (pagination may be needed for large lists)
            owners = self.client.crm.owners.owners_api.get_page()

            # Search for the owner with matching email
            for owner in owners.results:
                if owner.email == owner_email:
                    return str(owner.id)

            # If not found in first page, check additional pages
            while owners.paging and owners.paging.next:
                after = owners.paging.next.after
                owners = self.client.crm.owners.owners_api.get_page(after=after)

                for owner in owners.results:
                    if owner.email == owner_email:
                        return str(owner.id)

            detailed_log(f"No owner found with email: {owner_email}, using email prefix as fallback", "warning")
            return owner_email.split('@')[0]

        except Exception as e:
            detailed_log(f"Error getting owner: {e}, using email prefix as fallback", "warning")
            return owner_email.split('@')[0]

    def _is_duplicate(self, linkedin_url: str) -> bool:
        if not linkedin_url:
            return False
        try:
            search_payload = {
                "filter_groups": [{
                    "filters": [{"property_name": "linkedin_url", "operator": "EQ", "value": linkedin_url}]
                }],
                "properties": ["linkedin_url"]
            }
            search_request = PublicObjectSearchRequest(**search_payload)
            api_response = self.client.crm.contacts.search_api.do_search(public_object_search_request=search_request)
            return bool(api_response.results)
        except Exception as e:
            detailed_log(f"HubSpot duplicate check failed for {linkedin_url}: {e}", "warning")
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
    
    company_data = state.enriched_data.get(company.name, {})
    linkedin_data = company_data.get("linkedin_prospect_data", {})
    executives_found = linkedin_data.get("executives_found", [])

    if not executives_found:
        clean_log(f"No executives found for {company.name} - skipping", "warning")
        return state

    filtered_prospects = [
        {**exec_profile, "company_name": company.name}
        for exec_profile in executives_found
    ]
    clean_log(f"Key prospects identified: {len(filtered_prospects)} executives/managers for {company.name}")
    detailed_log(f"🎯 Key prospects after filtering: {len(filtered_prospects)}")

    
    contacts_dao = ContactsDao(loaded_config.connection_manager.mongo_client)
    mappings_dao = CompanyMappingsDao(loaded_config.connection_manager.mongo_client)

    campaign_id = config.get("data_source",{}).get("campaign_id","")
    company_id = getattr(state.current_company, "company_id", None)
    
    if not campaign_id or not company_id:
        clean_log("Missing campaign_id or company_id, skipping DB contact storage", "warning")
    else:
        is_relevant = (state.enriched_data.get(company.name, {}).get("web_search_analysis", {}).get("relevance_assessment", {}).get("is_relevant", False))
        inserted_ids = []
        for prospect in filtered_prospects:
            full_name = prospect.get("name", "")
            name_parts = full_name.split(" ", 1) if full_name else ["", ""]
            firstname = name_parts[0]
            lastname = name_parts[1] if len(name_parts) > 1 else ""
            
            contact_doc = {
                "contact_data": {
                    "firstname": firstname,
                    "lastname": lastname,
                    "email": prospect.get("email", ""),
                    "phone": prospect.get("phone_number", ""),
                    "jobtitle": prospect.get("title", ""),
                    "company": prospect.get("company", state.current_company.name)
                },
                "linkedin_data": {
                    "linkedin_url": prospect.get("linkedin_profile", ""),
                    "source": "AI-SDR",
                    "product_name": prospect.get("product","")
                },
                "hubspot_data": {
                    "hubspot_owner_id": config.get("hubspot_owner_email",""),
                    "ci_lifecycle_stage": "Not Contacted"
                },
                "metadata": {
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }

            contact_id = await contacts_dao.create_contact(contact_doc)
            inserted_ids.append(ObjectId(contact_id))
        update_query = {
            "campaign_id": ObjectId(campaign_id),
            "company_output.company_id": ObjectId(company_id)
        }
        update_action = {
                    "$set": {
                        "company_output.$.is_relevant": is_relevant,
                        "metadata.updated_at": datetime.utcnow()
                    },
                    "$push": {
                        "company_output.$.contact_ids": {"$each": inserted_ids}
                    }
                }
        await mappings_dao.update_company_mapping(update_query, update_action)
    # Skip HubSpot creation if disabled
    if not config.get("create_hubspot_contacts", True):
        clean_log(f"HubSpot creation disabled for {company.name}")
        detailed_log("⚠️ HubSpot contact creation is disabled in configuration", "warning")
        return state

    try:
        # Create HubSpot contacts using HubSpot API Client via HubspotContactCreator class
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
