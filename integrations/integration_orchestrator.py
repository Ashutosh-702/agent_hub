#!/usr/bin/env python3


from typing import Dict, Any, Optional
from integrations import coresignal
from integrations.coresignal.coresignal_api_client import CoresignalAPIClient
from database.collection_dao.companies import CompaniesDao
from database.collection_dao.campaigns import CampaignsDao
from database.collection_dao.contacts import ContactsDao
from database.collection_dao.campaign_company_runs import CampaignCompanyRunsDao
from config.loaded_config import loaded_config
from ai_agents.core_sdr.src.api.company_relevance_check import CompanyRelevanceCheck
from integrations.lusha.lusha_helper import LushaHelper
from integrations.coresignal.coresignal_api_client import CoresignalAPIClient
from integrations.lusha.lusha_contact_handler import LushaContactHandler
from integrations.utils import extract_departments_from_config
from integrations.apollo.apollo_helper import ApolloHelper
from integrations.apollo.schema import ApolloResponseSchema
from webhooks.contact_hubspot_webhook import ContactHubspotWebhook
from config.logging import logger


class IntegrationOrchestrator:
    def __init__(self,config: Dict[str,Any]):
        self.config = config
        self.coresignal_api = CoresignalAPIClient()
        self.lusha_helper = LushaHelper()
        self.coresignal_helper = CoresignalAPIClient()
        self.companies_dao = CompaniesDao(loaded_config.connection_manager.mongo_client)
        self.campaigns_dao = CampaignsDao(loaded_config.connection_manager.mongo_client)
        self.CompanyMappingsDao = CampaignCompanyRunsDao(loaded_config.connection_manager.mongo_client)
        self.ContactsDao = ContactsDao(loaded_config.connection_manager.mongo_client)
        self.relevance_check = CompanyRelevanceCheck(self.config)
        self.campaign_id = self.config.get('_id')
        self.lusha_contact_handler = LushaContactHandler()
        self.apollo_helper = ApolloHelper()
        self.webhook_sender = ContactHubspotWebhook(
            custom_webhook_url="https://asia-south1.api.boltic.io/service/webhook/temporal/v1.0/b156f5b3-c90d-449a-b104-2[…]c/workflows/execute/ee89e38a-e39a-42bf-8b26-4bdadb667e1d",
            campaign_id=self.campaign_id,
            source="ai_sdr"
        )

    async def process_prospecting_job(self) -> Dict[str, Any]:
        """Core function to process prospecting job"""
        try:
            await self.campaigns_dao.update_campaign_status(self.campaign_id,"started")
            logger.info("Fetching companies from apollo...")
            inserted_count = await self.apollo_helper.get_companies_from_apollo(self.config)
            logger.info(f"Found {inserted_count} companies from apollo.")
            await self.campaigns_dao.update_campaign_status(self.campaign_id,"company_qualification")
            return {
                "companies_fetched": inserted_count
            }
        except Exception as e:
            logger.error(f"Error while processing prospecting job for campaign {self.campaign_id}: {str(e)}")

    async def process_company_search(self) -> Dict[str, Any]:
        """Core function to process company search"""
        total_company_data = []
        
        try:
            await self.campaigns_dao.update_campaign_status(self.campaign_id,"started")
            logger.info("Fetching companies from lusha...")
            # inserted_count = await self.lusha_helper.get_companies_from_lusha(self.config)
            inserted_count = await self.apollo_helper.get_companies_from_apollo(self.config)
            logger.info(f"Found {inserted_count} companies from apollo.")
            # logger.info("Fetching companies from core_signal...")
            # core_signal_company_data = await self.coresignal_helper.collect_companies_from_search(
            #     self.config, cached_data
            # )
            total_company_data = inserted_count
            logger.info(f"Total new companies added into companies collection: {inserted_count}")
            await self.relevance_check.company_relevance_check(self.campaign_id)
            # departments = extract_departments_from_config(self.config.get("prompts", {}).get("persona", ""))
            # await self.lusha_contact_handler.process_campaign_contacts(
            #     campaign_id=str(self.campaign_id), departments=departments
            # )
            # self.campaign_id = "694274398be5e9ac887ca464"
            await self.process_contacts_enrichment(self.campaign_id)
            await self.campaigns_dao.update_campaign_status(self.campaign_id,"pending")

            logger.info(f"Updated status of {self.campaign_id} to 'pending'")

        except Exception as e:
            logger.error(f"Error while processing company search for campaign {self.campaign_id}: {str(e)}")
            await self.campaigns_dao.update_campaign_status(self.campaign_id,"failed")
        

        finally:
            return {
                "companies_fetched": total_company_data
            }


    async def process_contacts_enrichment(self, campaign_id: str, slack_metadata: Optional[dict] = None):
        try:
            logger.info(f"📋 Campaign ID: {campaign_id}")

            # Initialize database connection if needed        
            # Fetch campaign data from database using campaign_id

            count = await self.CompanyMappingsDao.get_campaign_company_runs_count({"campaign_id": campaign_id, "is_relevant": True})

            if count == 0:
                logger.info(f"No company mappings found for campaign_id: {campaign_id}")
                return

            total_pages = (count + 25 - 1) // 25 if count > 0 else 1
            logger.info(f"total_pages: {total_pages}")
            for page in range(1, total_pages + 1):
                company_mappings, pagination_info = await self.CompanyMappingsDao.get_campaign_company_runs_paginated({"campaign_id": campaign_id, "is_relevant": True}, page, 25)
                if not company_mappings:
                    logger.error(f"No company mappings found for page {page}")
                    continue
                logger.info(f"company_mappings: {company_mappings}")
                logger.info(f"pagination_info: {pagination_info}")
                company_ids = [mapping.get("company_id") for mapping in company_mappings]
                company_data = await self.companies_dao.get_companies({"_id": {"$in": company_ids}})
                if not company_data:
                    logger.error(f"❌ Company not found: {company_ids}")
                    continue
                logger.info(f"company_ids: {company_ids}")
                await self.process_company_mappings(company_ids, slack_metadata)

            return
        except Exception as e:
            logger.error(f"❌ Error processing contacts enrichment: {e}")
            raise

    async def process_company_mappings(self, company_ids: list, slack_metadata: dict):
        try:
            company_data = await self.companies_dao.get_companies({"_id": {"$in": company_ids}})
            if not company_data:
                logger.error(f"❌ Company not found: {company_ids}")
                return

            logger.info(f"company_ids: {company_ids}")

            person_seniorities = [ "vp", "director", "founder", "manager", "head", "partner", "c_suite", "owner"]
            contact_email_status = ["verified", "unverified", "likely to engage"]
            number_of_contacts_per_company = 25
            for company in company_data:
                company_name = company.get("identifiers", {}).get("name", "")
                company_domain = company.get("identifiers", {}).get("source_domain", "")
                organization_id = company.get("identifiers", {}).get("source_id", "")

                company_id = company.get("_id", "")
                logger.info(f"company_data: {company_data}")
                logger.info(f"📊 Company Name: {company_name}")
                logger.info(f"📍 Company ID: {company_id}")

                # if company as  multple unsent contacts, then don't do apollo search
                contacts = await self.ContactsDao.get_contacts({
                    "company_id": company_id,
                    # "webhook_sent": False,
                    "contact_data.email": {"$ne": []} #only get contacts with email. it should not be empty here email is an array field.
                })

                # Create ApolloResponseSchema object
                if len(contacts) == 0:

                    query_params = ApolloResponseSchema(
                        company_name=company_name,
                        company_domain=company_domain,
                        company_id=str(company_id),
                        person_seniorities=person_seniorities,
                        page=1,
                        per_page=number_of_contacts_per_company,
                        enrich_contacts=True,
                        contact_email_status=contact_email_status,
                        organization_id=organization_id
                    )

                    response = await self.apollo_helper.get_company_contacts(query_params)
                #send  webhook to the users with the contacts
                await self.webhook_sender.send_company_level_webhook(str(company_id), slack_metadata)
                logger.info(f"webhook sent to the users with the contacts")

        except Exception as e:
            logger.error(f"❌ Error processing company mappings: {e}")
            raise
            