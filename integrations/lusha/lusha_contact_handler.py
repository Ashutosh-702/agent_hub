from config.loaded_config import loaded_config
from typing import List
import asyncio
import sys
import aiohttp
from aiohttp.client_exceptions import ServerDisconnectedError, ClientError
from typing import Optional
from ai_agents.leadgen.services.ai_agents_service import ContactService,CompanyService
from ai_agents.leadgen.schemas.ai_agents import CountCompanyMappings, CompanyMappingList, LushaGetContactEnrichment, LushaContactEnrichment
from ai_agents.leadgen.helper.ai_agents_helper import LushaContactEnrichmentHelper
from config.logging import logger


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
            raise Exception(
                f"No company mappings found for campaign_id {self.campaign_id}")

        return response.get("company_map_list", [])

    async def get_contact_ids_for_companies(self, company_mappings: List[dict], page_size: int) -> dict:

        payload =LushaGetContactEnrichment(
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
        total_results =0
        # Map response back to company IDs

        if response.get("contact_ids"):
            total_results = response.get("total_results", 0)
            print(f"Total enrichment results: {total_results}")
            
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
            loaded_config.http_session = aiohttp.ClientSession()
            self.campaign_id = campaign_id

            if departments:
                self.departments = departments

            logger.info(f"🚀 Starting contact enrichment for campaign: {campaign_id}")

            # Phase 1: Get company mappings
            logger.info("📋 Phase 1: Getting company mappings... for initial")
            page = 1
            limit = 50

            company_mappings_count = await  self.company_service.count_company_mappings(
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
                    logger.error(f"No company mappings found for page {each_page}")
                    break

                logger.info(f"Fetching contact IDs for companies for page {each_page}")
                enrichment_stats = await self.get_contact_ids_for_companies(company_mappings, page_size=limit)

                if not enrichment_stats:
                    logger.error(f"No company contact mapping found for page {each_page}")
                    continue
                
                enrichment_count += enrichment_stats.get("total_results", 0)

            logger.info(f"contact enrichment completed successfully. Total results: {enrichment_count}")

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

    async def get_linkedin_contact_details(self, linkedin_url: str) -> dict:
        url = f"{self.base_url}/api/v1/get_linkedin_contact_details"
        payload = {
            "linkedin_url": linkedin_url
        }

        response = await self._make_api_call("POST", url, json=payload)
        return response

    async def _make_api_call(self, method: str, url: str, **kwargs) -> dict:
        """Helper method for making API calls"""
        max_retries = 2

        for attempt in range(max_retries):
            try:
                if method == "POST":
                    response = await loaded_config.http_session.post(url, **kwargs)
                    result = await response.json()

                    if response.status == 200 or response.status == 201:
                        return result
                    else:
                        raise Exception(f"API call failed: {response.status} - {await response.text()}")
                elif method == "GET":
                    response = await loaded_config.http_session.get(url, **kwargs)
                    result = await response.json()

                    if response.status == 200 or response.status == 201:
                        return result.get("data", {})
                    else:
                        raise Exception(f"API call failed: {response.status} - {await response.text()}")
                else:
                    raise Exception(f"Invalid method: {method}")
            except ServerDisconnectedError as e:
                logger.error(f"⚠️ Server disconnected on attempt {attempt + 1}: {e}")

                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.info(f"🔄 Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(f"❌ Max retries ({max_retries}) exceeded")
                    raise

            except ClientError as e:
                logger.error(f"❌ Client error on attempt {attempt + 1}: {e}")

                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"🔄 Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise

            except Exception as e:
                logger.error(f"❌ Unexpected error: {e}")
                raise


def main():
    """Main entry point"""
    try:

        app = LushaContactHandler()
        asyncio.run(app.process_campaign_contacts(
            campaign_id="68e8c4dd63aad7b0b2530b72", departments=["Business Development","Administrative"]))
    except KeyboardInterrupt:
        logger.error(f"\n Configuration interrupted. Goodbye!")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
