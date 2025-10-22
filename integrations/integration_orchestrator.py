#!/usr/bin/env python3


from typing import Dict, Any
from integrations import coresignal
from integrations.coresignal.coresignal_api_client import CoresignalAPIClient
from database.collection_dao.companies import CompaniesDao
from database.collection_dao.campaigns import CampaignsDao
from config.loaded_config import loaded_config
from ai_agents.core_sdr.src.api.company_relevance_check import CompanyRelevanceCheck
from integrations.lusha.lusha_helper import LushaHelper
from integrations.coresignal.coresignal_api_client import CoresignalAPIClient
from integrations.lusha.lusha_contact_handler import LushaContactHandler
from integrations.utils import extract_departments_from_config


class IntegrationOrchestrator:
    def __init__(self,config: Dict[str,Any]):
        self.config = config
        self.coresignal_api = CoresignalAPIClient()
        self.lusha_helper = LushaHelper()
        self.coresignal_helper = CoresignalAPIClient()
        self.companies_dao = CompaniesDao(loaded_config.connection_manager.mongo_client)
        self.campaigns_dao = CampaignsDao(loaded_config.connection_manager.mongo_client)
        self.relevance_check = CompanyRelevanceCheck(self.config)
        self.campaign_id = self.config.get('_id')
        self.lusha_contact_handler = LushaContactHandler()

    async def process_company_search(self) -> Dict[str, Any]:
        """Core function to process company search"""
        total_company_data = []
        
        try:    
            # print("Fetching companies from lusha...")
            # inserted_count = await self.lusha_helper.get_companies_from_lusha(self.config)
            # print(f"Found {inserted_count} companies from lusha.")
            # print("Fetching companies from core_signal...")
            # # core_signal_company_data = await self.coresignal_helper.collect_companies_from_search(
            # #     self.config, cached_data
            # # )
            # total_company_data = inserted_count
            # print(f"Total new companies added into companies collection: {inserted_count}")
            # await self.relevance_check.company_relevance_check(self.campaign_id)
            departments = extract_departments_from_config(self.config.get("prompts", {}).get("persona", ""))
            await self.lusha_contact_handler.process_campaign_contacts(
                campaign_id=self.campaign_id, departments=departments
            )
            await self.campaigns_dao.update_campaign_status(self.campaign_id,"pending")
            print(f"Updated status of {self.campaign_id} to 'pending'")

        except Exception as e:
            print(f"Error while processing company search for campaign {self.campaign_id}: {str(e)}")

        finally:
            return {
                "companies_fetched": total_company_data
            }
            