from typing import List, Optional

from config.loaded_config import loaded_config
from ai_agents.leadgen.services.ai_agents_service import ContactService, CompanyService
from ai_agents.leadgen.schemas.ai_agents import CountCompanyMappings, CompanyMappingList, LushaGetContactEnrichment, LushaContactEnrichment
from ai_agents.leadgen.helper.ai_agents_helper import LushaContactEnrichmentHelper
from config.logging import logger
from global_utils.exceptions import ApiException


class LushaContactHandler:

    def __init__(self):
       self.base_url = loaded_config.base_url
       self.campaign_id = ""
       self.departments = []
       self.contact_service = ContactService()
       self.company_service = CompanyService()
       self.lusha_contact_enrichment_helper = LushaContactEnrichmentHelper()

    async def get_company_mappings(self, page: int = 1, limit: int = 100) -> List[dict]:
        response = await self.company_service.get_company_mapping_list(
            query_params=CompanyMappingList(campaign_id=self.campaign_id, page=page, limit=limit)
        )

        if not response:
            logger.error(f"No company mappings found for campaign_id {self.campaign_id}")
            raise ApiException(f"No company mappings found for campaign_id {self.campaign_id}")

        return response.get("company_map_list", [])

    async def get_contact_ids_for_companies(self, company_mappings: List[dict], page_size: int) -> dict:

        payload = LushaGetContactEnrichment(
            campaign_id=str(self.campaign_id),
            page=0,
            page_size=page_size,
            company_map_list=company_mappings,
            departments=self.departments
        )

        response = await self.lusha_contact_enrichment_helper.lusha_get_contact_enrichment(
            query_params=payload
        )

        contact_pagination = 0
        total_results = 0

        if response.get("contact_ids"):
            total_results = response.get("total_results", 0)
            logger.info(f"Total enrichment results: {total_results}")

            contact_pagination = (total_results + page_size - 1) // page_size
            enrichment_stats = await self.enrich_and_store_contacts(company_contact_mapping=response)

        for page in range(1, contact_pagination + 1):
            payload.page = page
            response = await self.lusha_contact_enrichment_helper.lusha_get_contact_enrichment(
                query_params=payload
            )

            if response.get("contact_ids"):
                enrichment_stats = await self.enrich_and_store_contacts(company_contact_mapping=response)

        return {"enrichment_stats": enrichment_stats, "total_results": total_results}

    async def count_company_mappings(self) -> int:
        response = await self.company_service.count_company_mappings(query_params=CountCompanyMappings(campaign_id=self.campaign_id))

        return response.get("count", 0)

    async def enrich_and_store_contacts(self, company_contact_mapping: dict) -> dict:

        response = await self.lusha_contact_enrichment_helper.lusha_contact_enrichment(
            query_params=LushaContactEnrichment(
                contact_ids=company_contact_mapping.get("contact_ids", []),
                company_source_id_name_mappings=company_contact_mapping.get("company_source_id_name_mappings", {}),
                campaign_id=str(self.campaign_id),
                lusha_request_id=company_contact_mapping.get("lusha_request_id", ""),
            )
        )

        return response.get("data", {})

    async def process_campaign_contacts(self, campaign_id: str, departments: Optional[List[str]] = None) -> dict:

        try:
            self.campaign_id = campaign_id

            logger.info(f"Departments: {departments}")

            if departments:
                self.departments = departments

            logger.info(
                f"🚀 Starting contact enrichment for campaign: {campaign_id}")

            # Phase 1: Get company mappings
            logger.info("📋 Phase 1: Getting company mappings... for initial")
            limit = 50

            company_mappings_count = await self.company_service.count_company_mappings(
                query_params=CountCompanyMappings(campaign_id=self.campaign_id)
            )
            total_company_mappings = company_mappings_count.get("count", 0)

            if total_company_mappings == 0:
                logger.error("No company mappings found")

                return {
                    "status": "success",
                    "message": "No company mappings found"
                }

            total_pages = (total_company_mappings + limit - 1) // limit
            enrichment_count = 0

            for each_page in range(1, total_pages + 1):
                logger.info(f"Fetching company mappings for page {each_page}")
                response = await self.get_company_mappings(page=each_page, limit=limit)
                company_mappings = response

                if not company_mappings:
                    logger.error(
                        f"No company mappings found for page {each_page}")
                    break

                logger.info(
                    f"Fetching contact IDs for companies for page {each_page}")
                enrichment_stats = await self.get_contact_ids_for_companies(company_mappings, page_size=limit)

                if not enrichment_stats:
                    logger.error(
                        f"No company contact mapping found for page {each_page}")
                    continue

                enrichment_count += enrichment_stats.get("total_results", 0)

            logger.info(
                f"contact enrichment completed successfully. Total results: {enrichment_count}")

            return {
                "status": "success",
                "message": "Contact enrichment completed successfully"
            }

        except Exception as e:
            logger.error(f"❌ Error in contact enrichment: {e}")

            return {
                "status": "error",
                "message": f"Contact enrichment failed: {str(e)}"
            }
