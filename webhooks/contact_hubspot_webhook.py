"""
Class-based webhook sender for contact data to HubSpot/External webhook
"""
import os
import aiohttp
from typing import Dict, Any, List, Optional
from bson import ObjectId

from config.loaded_config import loaded_config
from database.collection_dao.contacts import ContactsDao
from database.collection_dao.companies import CompaniesDao
from database.collection_dao.campaigns import CampaignsDao
from database.collection_dao.campaign_company_runs import CampaignCompanyRunsDao
from config.logging import logger
from global_utils.constants import HUBSPOT_BOLTIC_WEBHOOK_URL


class ContactHubspotWebhook:
    """Class to handle webhook sending for contacts"""
    
    def __init__(self):

        self.webhook_url = HUBSPOT_BOLTIC_WEBHOOK_URL
        
        self.contacts_dao = ContactsDao(loaded_config.connection_manager.mongo_client)
        self.companies_dao = CompaniesDao(loaded_config.connection_manager.mongo_client)
        self.campaigns_dao = CampaignsDao(loaded_config.connection_manager.mongo_client)
        self.campaign_company_runs_dao = CampaignCompanyRunsDao(loaded_config.connection_manager.mongo_client)
    
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
            return {"name": "", "country": "", "industry": ""}
        
        try:
            company_doc = await self.companies_dao.get_company(company_id)

            if not company_doc:
                return {"name": "", "country": "", "industry": ""}
            
            identifiers = company_doc.get("identifiers", {})
            location = company_doc.get("location", {})
            profile = company_doc.get("profile", {})
            
            company_name = identifiers.get("name", "")
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
                "industry": industry
            }
        except Exception as e:
            logger.error(f"Error fetching company {company_id}: {e}")
            return {"name": "", "country": "", "industry": ""}
    
    async def get_interested_product(self, company_id: str) -> str:

        if not self.campaign_company_runs_dao or not self.campaigns_dao:
            return ""
        
        try:
            # Get campaign_id from company_id via campaign_company_runs
            campaign_mappings = await self.campaign_company_runs_dao.get_campaign_company_runs({
                "company_id": ObjectId(company_id)
            })
            
            if campaign_mappings:
                # Get campaign_id from first mapping
                campaign_id = campaign_mappings[0].get("campaign_id")
                if campaign_id:
                    campaign_doc = await self.campaigns_dao.get_campaign(str(campaign_id))
                    if campaign_doc:
                        return campaign_doc.get("ownership", {}).get("product_name", "")
        except Exception as e:
            logger.error(f"Error fetching interested product for company {company_id}: {e}")
        
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
                "meta": webhook_data.get("meta", {}),
            }
            
            # Validate required fields
            if not payload["contactEmail"]:
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
                timeout=aiohttp.ClientTimeout(total=10)
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
    
    async def send_webhook_for_company(self, company_id: str) -> Dict[str, Any]:
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
            interested_product = "TMS"

            
            logger.info(f"📇 Processing webhooks for company_id: {company_id}")
            
            # Get only contacts where webhook_sent is False or doesn't exist
            contacts = await self.contacts_dao.get_contacts({
                "company_id": ObjectId(company_id),
                "$or": [
                    {"webhook_sent": False},
                    {"webhook_sent": {"$exists": False}}
                ]
            })
            
            if not contacts:
                logger.info(f"  ⚠️ No contacts found for company {company_id} (all webhooks already sent)")
                return {
                    "status": "success",
                    "message": "No contacts found",
                    "total_contacts": 0,
                    "webhook_success": 0,
                    "webhook_failed": 0
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