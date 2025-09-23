from config.loaded_config import loaded_config
from typing import List
import asyncio
import sys
import aiohttp
from aiohttp.client_exceptions import ServerDisconnectedError, ClientError


class LushaContactHandler:

    def __init__(self):
       self.base_url = loaded_config.base_url
       self.campaign_id = ""

    async def get_company_mappings(self, page: int = 1, limit: int = 100) -> List[dict]:
        all_companies = []

        url = f"{self.base_url}/api/v1/get_company_mapping_list"
        params = {
            "campaign_id": self.campaign_id,
            "page": page,
            "limit": limit
        }
        response = await self._make_api_call("GET", url, params=params)
        
        if response.get("company_map_list"):
            all_companies.extend(response["company_map_list"])
        # Check if more pages exist
        pagination = response.get("pagination_info", {})

        result = {
            "company_map_list": all_companies,
            "pagination_info": pagination
        }

        return result

    async def get_contact_ids_for_companies(self, company_mappings: List[dict], page: int, page_size: int) -> dict:

        company_contact_mapping = {}

        url = f"{self.base_url}/api/v1/lusha_get_contact_enrichment"
        payload = {
            "campaign_id": self.campaign_id,
            "page": page,
            "page_size": page_size,
            "company_map_list": company_mappings
        }
        response = await self._make_api_call("POST", url, json=payload)

        # Map response back to company IDs
        if response:
            contact_data = response.get("contact_ids", [])
            company_source_id_name_mappings = response.get(
                "company_source_id_name_mappings", {})
            lusha_request_id = response.get("lusha_request_id", "")
            total_results = response.get("total_results", 0)
            company_contact_mapping = {
                "contact_ids": contact_data,
                "company_source_id_name_mappings": company_source_id_name_mappings,
                "lusha_request_id": lusha_request_id,
                "total_results": total_results
            }
        return company_contact_mapping

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
        return response

    async def process_campaign_contacts(self, campaign_id: str) -> dict:

        try:
            loaded_config.http_session = aiohttp.ClientSession()
            self.campaign_id = campaign_id
            print(f"🚀 Starting contact enrichment for campaign: {campaign_id}")

            # Phase 1: Get company mappings
            print("📋 Phase 1: Getting company mappings... for initial")
            page = 1
            limit = 50

            while True:
                response = await self.get_company_mappings(page=page, limit=limit)
                pagination_info = response.get("pagination_info", {})
                company_mappings = response.get("company_map_list", [])

                if not company_mappings:
                    break

                # Phase 2: Get contact IDs
                contact_page = 0
                contact_page_size = 50
                company_contact_mapping = {}

                while True:
                    company_contact_mapping = await self.get_contact_ids_for_companies(company_mappings, page=contact_page, page_size=contact_page_size)

                    if not company_contact_mapping:
                        break

                    # Phase 3: Enrich and store contacts
                    print("💾 Phase 3: Enriching and storing contacts...")

                    enrichment_stats = await self.enrich_and_store_contacts(company_contact_mapping=company_contact_mapping)
                    total_results = company_contact_mapping.get(
                        "total_results", 0)

                    if total_results == 0:
                        break
                    calculate_total_pages = (
                        total_results + contact_page_size - 1) // contact_page_size

                    if contact_page >= calculate_total_pages:
                        break
                    contact_page += 1

                if not pagination_info.get("has_next", False):
                    break
                page += 1

            print(" contact enrichment completed successfully")

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
                        return result
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
            campaign_id="68d1400db76b00d2f6af7666"))
    except KeyboardInterrupt:
        print(f"\n Configuration interrupted. Goodbye!")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
