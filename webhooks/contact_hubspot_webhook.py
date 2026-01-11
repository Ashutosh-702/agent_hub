"""
Class-based webhook sender for contact data to HubSpot/External webhook
"""
import os
import aiohttp
from typing import Dict, Any, List, Optional
from bson import ObjectId

from config.loaded_config import loaded_config
from database.factory import get_contacts_dao, get_companies_dao, get_campaigns_dao, get_campaign_company_runs_dao, get_campaign_contact_runs_dao
from config.logging import logger
from global_utils.constants import HUBSPOT_BOLTIC_WEBHOOK_URL


class ContactHubspotWebhook:
    """Class to handle webhook sending for contacts"""
    
    def __init__(self, custom_webhook_url: Optional[str] = None, campaign_id: Optional[str] = None, source: Optional[str] = None):
        if custom_webhook_url:
            self.webhook_url = custom_webhook_url
        else:
            self.webhook_url = HUBSPOT_BOLTIC_WEBHOOK_URL
        self.campaign_id = campaign_id
        self.company_id = None
        self.source = source
        self.contacts_dao = get_contacts_dao(loaded_config.connection_manager)
        self.companies_dao = get_companies_dao(loaded_config.connection_manager)
        self.campaigns_dao = get_campaigns_dao(loaded_config.connection_manager)
        self.campaign_company_runs_dao = get_campaign_company_runs_dao(loaded_config.connection_manager)
        self.campaign_contact_runs_dao = get_campaign_contact_runs_dao(loaded_config.connection_manager)
    async def format_phone_number(self, phone: str, country_code: Optional[str] = None) -> str:
        if not phone:
            return ""
        
        phone = phone.replace(" ", "").replace("\t", "").replace("\n", "").strip().lstrip("+")
        
        if phone.startswith("+"):
            return phone
        
        if country_code:
            return f"+{country_code}{phone}"
        
        return f"+{phone}"
    
    async def get_company_details(self, company_id: str) -> Dict[str, Any]:
        if not self.companies_dao:
            return {"name": "", "country": "", "industry": "", "website_url": ""}
        
        try:
            company_doc = await self.companies_dao.get_company(company_id)

            if not company_doc:
                return {"name": "", "country": "", "industry": "", "website_url": ""}
            
            identifiers = company_doc.get("identifiers", {})
            location = company_doc.get("location", {})
            profile = company_doc.get("profile", {})
            
            company_name = identifiers.get("name", "")
            company_website = identifiers.get("website_url", "")
            industry = profile.get("industry", "")
            # Try different possible fields for country
            company_country = (
                location.get("country") or 
                location.get("name") or 
                location.get("countryName") or 
                ""
            )
            
            return {
                "name": company_name,
                "country": company_country,
                "industry": industry,
                "website_url": company_website
            }
        except Exception as e:
            logger.error(f"Error fetching company {company_id}: {e}")
            return {"name": "", "country": "", "industry": "", "website_url": ""}
    
    async def get_interested_product(self) -> str:

        if not self.campaigns_dao:
            return ""
        
        try:
            campaign_doc = await self.campaigns_dao.get_campaign(self.campaign_id)

            if campaign_doc:
                return campaign_doc.get("ownership", {}).get("product_name", "")
        except Exception as e:
            logger.error(f"Error fetching interested product for campaign {self.campaign_id}: {e}")
        
        return ""
    
    def extract_contact_data(self, contact_doc: Dict[str, Any]) -> Dict[str, Any]:
        contact_data_field = contact_doc.get("contact_data", {})
        metadata = contact_doc.get("metadata", {})
        raw_data = metadata.get("raw_data", {})
        person_data = raw_data.get("person", {})
        organization_data = person_data.get("organization", {})
        
        # Extract contact information from contact_data
        first_name = contact_data_field.get("firstname", "")
        last_name = contact_data_field.get("lastname", "")
        job_title = contact_data_field.get("jobtitle", "")
        
        # Fallback to raw_data if not in contact_data
        if not first_name:
            first_name = person_data.get("first_name", "")
        if not last_name:
            last_name = person_data.get("last_name", "") or ""
        if not job_title:
            job_title = person_data.get("title", "")
        
        # Get email (prefer first email if multiple)
        emails = contact_data_field.get("email", [])
        contact_email = ""
        if isinstance(emails, list):
            contact_email = emails[0] if emails else ""
        else:
            contact_email = emails if emails else ""
        
        # Fallback to raw_data email if not in contact_data
        if not contact_email:
            contact_email = person_data.get("email", "")
        
        # Get phone (prefer first phone if multiple)
        phones = contact_data_field.get("phone", [])
        if isinstance(phones, list):
            contact_phone_raw = phones[0] if phones else ""
        else:
            contact_phone_raw = phones if phones else ""
        
        # Get contact country from person data
        contact_country = person_data.get("country", "") or ""
        
        # Extract company details from organization data in raw_data
        company_name = organization_data.get("name", "") or ""
        company_country = organization_data.get("country", "") or ""
        company_industry = organization_data.get("industry", "") or ""
        company_website = organization_data.get("website_url", "") or ""
        
        # Handle industry if it's a list
        if isinstance(company_industry, list):
            company_industry = ", ".join(company_industry) if company_industry else ""
        
        # Get LinkedIn URL from linkedin_data or person_data
        linkedin_data = contact_doc.get("linkedin_data", {})
        linkedin_url = linkedin_data.get("linkedin_url", "") or person_data.get("linkedin_url", "") or ""
        
        return {
            "first_name": first_name,
            "last_name": last_name,
            "email": contact_email,
            "phone": contact_phone_raw,
            "job_title": job_title,
            "country": contact_country,
            "company_name": company_name,
            "company_country": company_country,
            "company_industry": company_industry,
            "company_website": company_website,
            "linkedin_url": linkedin_url,
            "raw_data": raw_data
        }
    
    async def send_webhook(self, webhook_data: Dict[str, Any]) -> bool:
        try:
            payload = {
                "companyName": webhook_data.get("companyName", ""),
                "companyCountry": webhook_data.get("companyCountry", ""),
                "companyWebsite": webhook_data.get("companyWebsite", ""),
                "contactFirstName": webhook_data.get("contactFirstName", ""),
                "contactLastName": webhook_data.get("contactLastName", ""),
                "contactEmail": webhook_data.get("contactEmail", ""),
                "contactPhone": webhook_data.get("contactPhone", ""),
                "linkedin_url": webhook_data.get("linkedin_url", ""),
                "contactCountry": webhook_data.get("contactCountry", ""),
                "companyIndustry": webhook_data.get("companyIndustry", ""),
                "contactJobTitle": webhook_data.get("contactJobTitle", ""),
                "interestedProduct": webhook_data.get("interestedProduct", ""),
                "slack_metadata": webhook_data.get("slack_metadata", {}),
                "meta": webhook_data.get("meta", {}),
            }
            if webhook_data.get("message"):
                payload["message"] = webhook_data.get("message")
            
            # Validate required fields
            if not payload["contactEmail"] and not payload.get("message"):
                logger.warning(f"⚠️ Skipping webhook for contact {payload['contactFirstName']} {payload['contactLastName']} - no email")
                return False

            logger.info(f"🔍 Sending webhook to {self.webhook_url} for contact {payload['contactEmail']}")
            
            # Ensure HTTP session exists
            if not loaded_config.http_session:
                loaded_config.http_session = aiohttp.ClientSession()
            
            response = await loaded_config.http_session.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=15)
            )
            
            if response.status in [200, 201, 202]:
                logger.info(f"✅ Webhook sent successfully for {payload['contactEmail']}")
                return True
            else:
                response_text = await response.text()
                logger.warning(f"⚠️ Webhook failed with status {response.status} for {payload['contactEmail']}: {response_text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error sending webhook: {e}")
            return False
    
    async def send_webhook_for_company(self, company_id: str, slack_metadata: dict = None ) -> Dict[str, Any]:
        if not self.contacts_dao:
            logger.error("ContactsDao not initialized")
            return {
                "status": "error",
                "message": "Database connection not available",
                "total_contacts": 0,
                "webhook_success": 0,
                "webhook_failed": 0
            }
        
        try:
            # Get interested product (still need to fetch from campaign)
            # interested_product = await self.get_interested_product(company_id)
            interested_product = "fynd_create"

            
            logger.info(f"📇 Processing webhooks for company_id: {company_id}")
            
            # Get only contacts where webhook_sent is False or doesn't exist
            contacts = await self.contacts_dao.get_contacts({
                "company_id": ObjectId(company_id),
                "contact_data.email": {"$ne": []}
                # "$or": [
                #     {"webhook_sent": False},
                #     {"webhook_sent": {"$exists": False}}
                # ]
            })
            
            if not contacts:
                logger.info(f"  ⚠️ No contacts found for company {company_id} (all webhooks already sent)")
                # Get company details to send webhook with message
                company_details = await self.get_company_details(company_id)
                company_name = company_details.get("name")

                # Prepare webhook payload with message indicating no contacts
                webhook_data = {
                    "companyName": company_name,
                    "companyCountry": "India",
                    "companyWebsite": "https://www.fynd.com",
                    "companyIndustry": "Transportation",
                    "contactFirstName": "Raju",
                    "contactLastName": "Mishra",
                    "contactEmail": "raju.mishra@fynd.com",
                    "contactPhone": "",
                    "linkedin_url": "https://www.linkedin.com/in/raju-mishra-1234567890",
                    "contactCountry": "India",
                    "contactJobTitle": "Developer",
                    "interestedProduct": interested_product,
                    "slack_metadata": slack_metadata,
                    "meta": {},
                    "message": f"No contacts found for company: {company_name}"
                }
                webhook_sent = await self.send_webhook(webhook_data)
                return {
                    "status": "success",
                    "message": "No contacts found - webhook sent with message",
                    "total_contacts": 0,
                    "webhook_success": 1 if webhook_sent else 0,
                    "webhook_failed": 0 if webhook_sent else 1
                }


            logger.info(f"  ✅ Found {len(contacts)} contacts pending webhook")
            
            webhook_success_count = 0
            webhook_fail_count = 0
            
            # Process each contact and send webhook
            for contact_doc in contacts:
                try:
                    
                    # Extract contact and company data from contact document
                    contact_info = self.extract_contact_data(contact_doc)
                    
                    # Skip if no email (required field)
                    if not contact_info["email"]:
                        logger.warning(f"    ⚠️ Skipping contact {contact_info['first_name']} {contact_info['last_name']} - no email")
                        continue
                    
                    # Skip if no company name (should be in raw_data)
                    if not contact_info["company_name"]:
                        logger.warning(f"    ⚠️ Skipping contact {contact_info['first_name']} {contact_info['last_name']} - no company name in contact data")
                        continue
                    
                    # Format phone number
                    contact_phone = await self.format_phone_number(contact_info["phone"])
                    
                    # Prepare webhook payload using data extracted from contact document
                    webhook_data = {
                        "companyName": contact_info["company_name"],
                        "companyCountry": contact_info["company_country"],
                        "companyWebsite": contact_info["company_website"],
                        "contactFirstName": contact_info["first_name"],
                        "contactLastName": contact_info["last_name"],
                        "contactEmail": contact_info["email"],
                        "contactPhone": contact_phone,
                        "linkedin_url": contact_info["linkedin_url"],
                        "contactCountry": contact_info["country"],
                        "companyIndustry": contact_info["company_industry"],
                        "contactJobTitle": contact_info["job_title"],
                        "interestedProduct": interested_product,
                        "slack_metadata": slack_metadata,
                        "meta": contact_info["raw_data"]
                    }
                    
                    # Send webhook
                    if await self.send_webhook(webhook_data):
                        webhook_success_count += 1
                        
                        # Update webhook_sent flag to True in database
                        try:
                            contact_id = contact_doc.get("_id")
                            await self.contacts_dao.update_contact(
                                str(contact_id),
                                {"$set": {"webhook_sent": True}}
                            )
                            logger.info(f"    ✅ Updated webhook_sent=True for contact {contact_info['email']}")
                            break #break the loop after sending webhook to one contact
                        except Exception as e:
                            logger.warning(f"    ⚠️ Failed to update webhook_sent flag: {e}")
                    else:
                        webhook_fail_count += 1
                    
                except Exception as e:
                    logger.error(f"❌ Error processing contact: {e}")
                    webhook_fail_count += 1
                    continue
            
            logger.info(f"✅ Webhook sending completed for company {company_id}")
            logger.info(f"   Webhooks sent successfully: {webhook_success_count}")
            logger.info(f"   Webhooks failed: {webhook_fail_count}")
            
            return {
                "status": "success",
                "message": "Webhook sending completed",
                "total_contacts": len(contacts),
                "webhook_success": webhook_success_count,
                "webhook_failed": webhook_fail_count
            }
            
        except Exception as e:
            logger.error(f"❌ Error in send_webhook_for_company: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "status": "error",
                "message": f"Error: {str(e)}",
                "total_contacts": 0,
                "webhook_success": 0,
                "webhook_failed": 0
            }
    
    async def send_company_level_webhook(self, company_id: str, slack_metadata: dict=None) -> Dict[str, Any]:
        if not self.contacts_dao:
            logger.error("ContactsDao not initialized")
            return {
                "status": "error",
                "message": "Database connection not available",
                "total_contacts": 0,
                "webhook_success": 0,
                "webhook_failed": 0
            }
        
        try:
            # Get interested product
            interested_product = None

            if self.campaign_id:
                interested_product = await self.get_interested_product()
                #for now, we are using the default product name
                interested_product = "GlamAR"
                
            if not interested_product:
                interested_product = "fynd_create"
            
            logger.info(f"📇 Processing company-level webhook for company_id: {company_id}")
            
            # Get all contacts for the company (including those already sent)
            contacts = []
            pagination_info = None
            if self.campaign_id:
                campaign_contact_runs = await self.campaign_contact_runs_dao.get_campaign_contact_runs({"campaign_id": self.campaign_id, "company_id": ObjectId(company_id), "is_relevant": True})

                if not campaign_contact_runs:
                    logger.info(f"  ⚠️ No campaign contact runs found for company {company_id}")
                    return {
                        "status": "success",
                        "message": "No campaign contact runs found - webhook sent with message",
                        "total_contacts": 0,
                        "webhook_success": 1,
                        "webhook_failed": 0
                    }
                else:
                    contacts_ids = [campaign_contact_run.get("contact_id") for campaign_contact_run in campaign_contact_runs]
                    if len(contacts_ids) > 0:
                        contacts, pagination_info = await self.contacts_dao.get_paginated_contacts({"_id": {"$in": contacts_ids},"contact_data.email": {"$ne": []}}, page=1, limit=5)
            else:
                contacts, pagination_info = await self.contacts_dao.get_paginated_contacts({
                    "company_id": ObjectId(company_id),
                    "contact_data.email": {"$ne": []}
                }, page=1, limit=3)
                
            logger.info(f"  ✅ Found {len(contacts)} contacts for company-level webhook")
            logger.info(f"   Pagination info: {pagination_info}")
            if not contacts or len(contacts) == 0:
                logger.info(f"  ⚠️ No contacts found for company {company_id}")
                # Get company details to send webhook with message
                company_details = await self.get_company_details(company_id)
                company_name = company_details.get("name", "")
                
                # Prepare webhook payload with message indicating no contacts
                webhook_data = {
                    "companyName": company_name,
                    "companyCountry": company_details.get("country", ""),
                    "companyWebsite": company_details.get("website_url", ""),
                    "companyIndustry": company_details.get("industry", ""),
                    "interestedProduct": interested_product,
                    "slack_metadata": slack_metadata,
                    "contact_details": [],
                    "message": f"No contacts found for company: {company_name}"
                }
                
                webhook_sent = await self.send_company_webhook(webhook_data)
                return {
                    "status": "success",
                    "message": "No contacts found - webhook sent with message",
                    "total_contacts": 0,
                    "webhook_success": 1 if webhook_sent else 0,
                    "webhook_failed": 0 if webhook_sent else 1
                }
            
            logger.info(f"  ✅ Found {len(contacts)} contacts for company-level webhook")
            
            # Extract company details from first contact (they should all have same company info)
            first_contact_info = self.extract_contact_data(contacts[0])
            
            # Get company details from database as fallback
            company_details = await self.get_company_details(company_id)
            
            # Build contact_details array
            contact_details = []
            for contact_doc in contacts:
                try:
                    contact_info = self.extract_contact_data(contact_doc)
                    
                    # Skip if no email (required field)
                    if not contact_info["email"]:
                        logger.warning(f"    ⚠️ Skipping contact {contact_info['first_name']} {contact_info['last_name']} - no email")
                        continue
                    
                    # Format phone number
                    contact_phone = await self.format_phone_number(contact_info["phone"])
                    
                    # Build contact detail object
                    contact_detail = {
                        "contactFirstName": contact_info["first_name"],
                        "contactLastName": contact_info["last_name"],
                        "contactEmail": contact_info["email"],
                        "contactPhone": contact_phone,
                        "linkedin_url": contact_info["linkedin_url"],
                        "contactCountry": contact_info["country"],
                        "contactJobTitle": contact_info["job_title"],
                        "meta": contact_info["raw_data"]
                    }
                    
                    contact_details.append(contact_detail)
                    
                except Exception as e:
                    logger.error(f"❌ Error processing contact for company-level webhook: {e}")
                    continue
            
            if not contact_details:
                logger.warning(f"  ⚠️ No valid contacts found after processing")
                # Send webhook with empty contact_details
                webhook_data = {
                    "companyName": company_details.get("name", first_contact_info.get("company_name", "")),
                    "companyCountry": company_details.get("country", first_contact_info.get("company_country", "")),
                    "companyWebsite": first_contact_info.get("company_website", ""),
                    "companyIndustry": company_details.get("industry", first_contact_info.get("company_industry", "")),
                    "interestedProduct": interested_product,
                    "slack_metadata": slack_metadata,
                    "contact_details": [],
                    "message": "No valid contacts found after processing"
                }
                
                webhook_sent = await self.send_company_webhook(webhook_data)
                return {
                    "status": "success",
                    "message": "No valid contacts - webhook sent with message",
                    "total_contacts": len(contacts),
                    "webhook_success": 1 if webhook_sent else 0,
                    "webhook_failed": 0 if webhook_sent else 1
                }
            
            # Handle industry if it's a list
            company_industry = company_details.get("industry", first_contact_info.get("company_industry", ""))
            if isinstance(company_industry, list):
                company_industry = ", ".join(company_industry) if company_industry else ""
            
            # Prepare company-level webhook payload
            webhook_data = {
                "companyName": first_contact_info.get("company_name", ""),
                "companyCountry": first_contact_info.get("company_country", ""),
                "companyWebsite": first_contact_info.get("company_website", ""),
                "companyIndustry": company_industry,
                "interestedProduct": interested_product,
                "slack_metadata": slack_metadata,
                "contact_details": contact_details
            }
            
            # Send company-level webhook
            webhook_sent = await self.send_company_webhook(webhook_data)
            
            if webhook_sent:
                # Update webhook_sent flag at company level
                try:
                    await self.companies_dao.update_company(
                        company_id,
                        {"webhook_sent": True}
                    )
                    logger.info(f"    ✅ Updated webhook_sent=True for company {company_id}")
                except Exception as e:
                    logger.warning(f"    ⚠️ Failed to update webhook_sent flag for company: {e}")
            
            logger.info(f"✅ Company-level webhook sending completed for company {company_id}")
            logger.info(f"   Total contacts: {len(contacts)}")
            logger.info(f"   Contacts in webhook: {len(contact_details)}")
            logger.info(f"   Webhook sent: {webhook_sent}")
            
            return {
                "status": "success",
                "message": "Company-level webhook sending completed",
                "total_contacts": len(contacts),
                "contacts_in_webhook": len(contact_details),
                "webhook_success": 1 if webhook_sent else 0,
                "webhook_failed": 0 if webhook_sent else 1
            }
            
        except Exception as e:
            logger.error(f"❌ Error in send_company_level_webhook: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "status": "error",
                "message": f"Error: {str(e)}",
                "total_contacts": 0,
                "webhook_success": 0,
                "webhook_failed": 0
            }
    
    async def send_company_webhook(self, webhook_data: Dict[str, Any]) -> bool:
        """
        Send webhook with company-level data structure.
        This is a separate method for company-level webhooks (different payload structure).
        
        Args:
            webhook_data: Dictionary containing company data and contact_details array
            
        Returns:
            True if webhook sent successfully, False otherwise
        """
        try:
            payload = {
                "companyName": webhook_data.get("companyName", ""),
                "companyCountry": webhook_data.get("companyCountry", ""),
                "companyWebsite": webhook_data.get("companyWebsite", ""),
                "companyIndustry": webhook_data.get("companyIndustry", ""),
                "interestedProduct": webhook_data.get("interestedProduct", ""),
                "contact_details": webhook_data.get("contact_details", [])
            }
            if self.company_id:
                payload["company_id"] = str(self.company_id)
            if self.campaign_id:
                payload["campaign_id"] = self.campaign_id
            if webhook_data.get("slack_metadata"):
                payload["slack_metadata"] = webhook_data.get("slack_metadata")
            if self.source:
                payload["source"] = self.source
            # Add message if present
            if webhook_data.get("message"):
                payload["message"] = webhook_data.get("message")
            
            # Validate that we have at least company name or contact_details
            if not payload["companyName"] and not payload["contact_details"]:
                logger.warning(f"⚠️ Skipping company-level webhook - no company name or contacts")
                return False
            
            logger.info(f"🔍 Sending company-level webhook to {self.webhook_url}")
            logger.info(f"   Company: {payload['companyName']}")
            logger.info(f"   Contacts: {len(payload['contact_details'])}")
            
            # Ensure HTTP session exists
            if not loaded_config.http_session:
                loaded_config.http_session = aiohttp.ClientSession()
            
            response = await loaded_config.http_session.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=15)
            )
            
            if response.status in [200, 201, 202]:
                logger.info(f"✅ Company-level webhook sent successfully for {payload['companyName']}")
                return True
            else:
                response_text = await response.text()
                logger.warning(f"⚠️ Company-level webhook failed with status {response.status} for {payload['companyName']}: {response_text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error sending company-level webhook: {e}")
            return False


    async def sync_to_hubspot(self, campaign_id: str):
        try:
            campaign = await self.campaigns_dao.get_campaign(campaign_id)
            self.campaign_id = campaign_id
            if not campaign:
                logger.error(f"❌ Campaign not found for campaign_id: {campaign_id}")
                return
            if campaign.get("prospecting_cycle", {}).get("status") in ["draft","prospecting","company_qualification","contact_qualification","hubspot_sync_in_progress","hubspot_sync_completed"]:
                logger.error(f"Campaign is not in contact qualification status for campaign_id: {campaign_id}")
                return

            campaign_company_runs_count = await self.campaign_company_runs_dao.get_campaign_company_runs_count({"campaign_id": campaign_id, "is_relevant": True,"$or": [{"sync_to_hubspot_status": "not_synced"}, {"sync_to_hubspot_status": {"$exists": False}}]})
            if campaign_company_runs_count == 0:
                logger.error(f"❌ No campaign company runs found for campaign_id: {campaign_id}")
                return
            total_pages = (campaign_company_runs_count + 1 - 1) // 1
            for page in range(1, total_pages + 1):
                campaign_company_runs, pagination_info = await self.campaign_company_runs_dao.get_campaign_company_runs_paginated({"campaign_id": campaign_id, "is_relevant": True,"$or": [{"sync_to_hubspot_status": "not_synced"}, {"sync_to_hubspot_status": {"$exists": False}}]}, 1, 1)
                if not campaign_company_runs:
                    logger.error(f"❌ No campaign company runs found for page {page}")
                    continue
                for campaign_company_run in campaign_company_runs:
                    company_id = campaign_company_run.get("company_id")
                    self.company_id = company_id
                    await self.send_company_level_webhook(str(company_id))
                    campaign_company_run_id = campaign_company_run.get("_id")
                    campaign_contact_runs = await self.campaign_contact_runs_dao.get_campaign_contact_runs_count({"campaign_id": self.campaign_id, "company_id": ObjectId(company_id), "is_relevant": True})
                    if campaign_contact_runs > 0:
                        await self.campaign_company_runs_dao.update_campaign_company_run({"_id": campaign_company_run_id}, {"$set": {"sync_to_hubspot_status": "in_progress"}})
            logger.info(f"✅ Synced to HubSpot for campaign_id: {campaign_id}")
            await self.campaigns_dao.update_campaign(campaign_id, {"prospecting_cycle.status": "hubspot_sync_in_progress"})
            return {
                "status": "success",
                "message": "Synced to HubSpot",
                "total_companies": campaign_company_runs_count,
                "companies_synced": campaign_company_runs_count
            }
        except Exception as e:
            logger.error(f"❌ Error syncing to HubSpot: {e}")
            await self.campaigns_dao.update_campaign(campaign_id, {"prospecting_cycle.status": "hubspot_sync_failed"})
            return {
                "status": "error",
                "message": "Error syncing to HubSpot",
                "total_companies": len(campaign_company_runs),
                "companies_synced": len(campaign_company_runs)
            }