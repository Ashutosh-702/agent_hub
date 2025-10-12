#!/usr/bin/env python3


from typing import Dict, Any
from integrations.coresignal.coresignal_api import CoresignalAPIClient
from database.collection_dao.companies import CompaniesDao
from database.collection_dao.campaigns import CampaignsDao
from config.loaded_config import loaded_config
from ai_agents.core_sdr.src.api.company_relevance_check import CompanyRelevanceCheck
from integrations.lusha.lusha_helper import LushaHelper


class IntegrationOrchestrator:
    def __init__(self,config: Dict[str,Any]):
        self.config = config
        self.coresignal_api = CoresignalAPIClient()
        self.lusha_helper = LushaHelper()
        self.companies_dao = CompaniesDao(loaded_config.connection_manager.mongo_client)
        self.campaigns_dao = CampaignsDao(loaded_config.connection_manager.mongo_client)
        self.relevance_check = CompanyRelevanceCheck(self.config)
        self.campaign_id = self.config.get('_id')

    async def process_company_search(self) -> Dict[str, Any]:
        """Core function to process company search"""
        # Initialize variables before try block to avoid UnboundLocalError
        total_company_data = []
        
        try:
            # Check if connection manager is properly initialized
            if not loaded_config.connection_manager or not loaded_config.connection_manager.mongo_client:
                print("❌ Error: Database connection not initialized")
                return {
                    "companies": [],
                    "error": "Database connection not available"
                }
                
            print("Fetching companies from lusha...")
            # inserted_count = await get_companies_from_lusha(config,temp_cached_data) # List of {'id': int, 'name': str}
            inserted_count = await self.lusha_helper.get_companies_from_lusha(self.config)
            print(f"Found {inserted_count} companies from lusha.")
            print("Fetching companies from core_signal...")
            # core_signal_company_data = collect_companies_from_search(config, cached_data) # List of {'id': int, 'name': str}
            total_company_data = inserted_count
            
            print(f"Total new companies added into companies collection: {inserted_count}")
    
            await self.relevance_check.company_relevance_check(self.campaign_id)
            await self.campaigns_dao.update_campaign_status(self.campaign_id,"pending")
            print(f"Updated status of {self.campaign_id} to 'pending'")

        except Exception as e:
            print(f"Error while processing company search for campaign {self.campaign_id}: {str(e)}")
        return {
            "companies": total_company_data
        }