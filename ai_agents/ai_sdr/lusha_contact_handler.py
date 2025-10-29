from config.loaded_config import loaded_config
from typing import List
import asyncio
import sys
import aiohttp
from aiohttp.client_exceptions import ServerDisconnectedError, ClientError
from typing import Optional


class LushaContactHandler:

    def __init__(self):
       self.base_url = loaded_config.base_url
       self.campaign_id = ""
       self.departments = []

    async def get_company_mappings(self, page: int = 1, limit: int = 100) -> List[dict]:
        company_map_list = {
            "company_map_list": [],
        }
        url = f"{self.base_url}/api/v1/get_company_mapping_list"
        params = {
            "campaign_id": self.campaign_id,
            "page": page,
            "limit": limit
        }
        response = await self._make_api_call("GET", url, params=params)
        
        if not response:
            return company_map_list

        # Check if more pages exist

        company_map_list["company_map_list"].extend(response)

        return company_map_list

    async def get_contact_ids_for_companies(self, company_mappings: List[dict], page_size: int) -> dict:

        company_contact_mapping = {}

        url = f"{self.base_url}/api/v1/lusha_get_contact_enrichment"
        payload = {
            "campaign_id": self.campaign_id,
            "page": 0,
            "page_size": page_size,
            "company_map_list": company_mappings,
            "departments": self.departments
        }

        response = await self._make_api_call("POST", url, json=payload)
        contact_pagination = 0
        total_results =0
        # Map response back to company IDs

        if response.get("success"):
            response_data = response.get("data",[])
            contact_data = response_data.get("contact_ids", [])
            company_source_id_name_mappings = response_data.get(
                "company_source_id_name_mappings", {})
            lusha_request_id = response_data.get("lusha_request_id", "")
            total_results = response_data.get("total_results", 0)
            print(f"Total enrichment results: {total_results}")
            
            contact_pagination = (total_results + page_size - 1) // page_size
            company_contact_mapping = {
                "contact_ids": contact_data,
                "company_source_id_name_mappings": company_source_id_name_mappings,
                "lusha_request_id": lusha_request_id,
                "total_results": total_results
            }
            enrichment_stats = await self.enrich_and_store_contacts(company_contact_mapping=company_contact_mapping)

        for page in range(1, contact_pagination + 1):
            payload["page"]= page
            response = await self._make_api_call("POST", url, json=payload)

            if response.get("success"):
                response_data = response.get("data",[])
                contact_data = response_data.get("contact_ids", [])
                company_source_id_name_mappings = response_data.get(
                    "company_source_id_name_mappings", {})
                lusha_request_id = response_data.get("lusha_request_id", "")
                company_contact_mapping["contact_ids"] = contact_data
                company_contact_mapping["company_source_id_name_mappings"] = company_source_id_name_mappings
                company_contact_mapping["lusha_request_id"] = lusha_request_id
                company_contact_mapping["total_results"] = total_results
                enrichment_stats = await self.enrich_and_store_contacts(company_contact_mapping=company_contact_mapping)

        return {"enrichment_stats": enrichment_stats, "total_results": total_results}

    async def count_company_mappings(self) -> int:
        url = f"{self.base_url}/api/v1/count_company_mappings"
        payload = {
            "campaign_id": self.campaign_id
        }
        response = await self._make_api_call("GET", url, params=payload)
        return response.get("count", 0)

    async def enrich_and_store_contacts(self, company_contact_mapping: dict) -> dict:

        # Call contact enrichment API
        url = f"{self.base_url}/api/v1/lusha_contact_enrichment"
        payload = {
            "contact_ids": company_contact_mapping.get("contact_ids", []),
            "company_source_id_name_mappings": company_contact_mapping.get("company_source_id_name_mappings", ""),
            "campaign_id": self.campaign_id,
            "lusha_request_id": company_contact_mapping.get("lusha_request_id", ""),
        }

        response = await self._make_api_call("POST", url, json=payload)
        return response.get("data", {})

    async def process_campaign_contacts(self, campaign_id: str, departments: Optional[List[str]] = None) -> dict:

        try:
            loaded_config.http_session = aiohttp.ClientSession()
            self.campaign_id = campaign_id

            if departments:
                self.departments = departments

            print(f"🚀 Starting contact enrichment for campaign: {campaign_id}")

            # Phase 1: Get company mappings
            print("📋 Phase 1: Getting company mappings... for initial")
            page = 1
            limit = 50

            get_company_mappings_response = await self.count_company_mappings()
            total_company_mappings = get_company_mappings_response

            if total_company_mappings == 0:
                print("No company mappings found")
                return {
                    "status": "success",
                    "message": "No company mappings found"
                }

            total_pages = (total_company_mappings + limit - 1) // limit
            enrichment_count = 0

            for each_page in range(1, total_pages + 1):
                print(f"Fetching company mappings for page {each_page}")
                response = await self.get_company_mappings(page=each_page, limit=limit)
                company_mappings = response.get("company_map_list", [])

                if not company_mappings:
                    print(f"No company mappings found for page {each_page}")
                    break

                print(f"Fetching contact IDs for companies for page {each_page}")
                enrichment_stats = await self.get_contact_ids_for_companies(company_mappings, page_size=limit)

                if not enrichment_stats:
                    print(f"No company contact mapping found for page {each_page}")
                    continue
                
                enrichment_count += enrichment_stats.get("total_results", 0)

            print(f"contact enrichment completed successfully. Total results: {enrichment_count}")

            return {
                "status": "success",
                "message": "Contact enrichment completed successfully"
            }

        except Exception as e:
            print(f"❌ Error in contact enrichment: {e}")
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
                print(f"⚠️ Server disconnected on attempt {attempt + 1}: {e}")

                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    print(f"🔄 Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    print(f"❌ Max retries ({max_retries}) exceeded")
                    raise

            except ClientError as e:
                print(f"❌ Client error on attempt {attempt + 1}: {e}")

                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"🔄 Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise

            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                raise


def main():
    """Main entry point"""
    try:

        app = LushaContactHandler()
        asyncio.run(app.process_campaign_contacts(
            campaign_id="68e8c4dd63aad7b0b2530b72", departments=["Business Development","Administrative"]))
    except KeyboardInterrupt:
        print(f"\n Configuration interrupted. Goodbye!")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
