from typing import List, Dict, Any
from datetime import datetime, timezone

from database.collection_dao.companies import CompaniesDao
from database.collection_dao.campaign_company_runs import CampaignCompanyRunsDao
from config.logging import logger


class CompanySaver:
    def __init__(self, companies_dao: CompaniesDao, campaign_company_runs_dao: CampaignCompanyRunsDao):
        self.companies_dao = companies_dao
        self.campaign_company_runs_dao = campaign_company_runs_dao

    async def insert_companies_batch_to_db(
        self,
        company_data_list: List[Dict[str, Any]],
        config: Dict[str, Any],
        source: str,
    ) -> List[str]:  # ✅ Return inserted company IDs instead of count
        """
        Insert companies into database.
        Returns list of inserted company IDs.
        """
        campaign_company_details = {
            'company_ids': [],
            'inserted_ids': []
        }

        if not company_data_list:
            logger.info(f"⚠️ No valid company data list found in {source} batch")
            return campaign_company_details

        # ✅ STEP 1: Extract all source IDs from the batch
        batch_source_ids = []

        for company_data in company_data_list:
            source_id = str(company_data.get("id", ""))

            if source_id:  # Only add non-empty source IDs
                batch_source_ids.append(source_id)

        if not batch_source_ids:
            logger.info(f"⚠️ No valid source IDs found in {source} batch")
            return campaign_company_details

        logger.info(f"🔍 Checking {len(batch_source_ids)} {source} companies against database...")

        # ✅ STEP 2: Query database to find existing source IDs
        existing_companies = await self.companies_dao.get_companies({
            "identifiers.source_id": {"$in": batch_source_ids}
        })

        existing_source_ids = set()


        for company in existing_companies:
            source_id = company.get("identifiers", {}).get("source_id")

            if source_id not in existing_source_ids:
                campaign_company_details['company_ids'].append(company['_id'])

            existing_source_ids.add(company.get("identifiers", {}).get("source_id"))

        logger.info(f"📊 Found {len(existing_source_ids)} existing companies in database")
        companies_to_insert = []

        for company_data in company_data_list:
            source_id = str(company_data.get("id", ""))

            if source_id in existing_source_ids:
                logger.info(f"🔍 {source_id} already exists in database")
                continue

            company_doc = {
                "identifiers": {
                    "source_id": source_id,
                    "name": company_data.get("name", ""),
                },
                "profile": {
                    "industry": config.get("segmentation", {}).get("industry"),
                    "revenue_min": config.get("target", {}).get("revenue_min"),
                    "revenue_max": config.get("target", {}).get("revenue_max"),
                    "employee_count": config.get("target", {}).get("employee_count"),
                },
                "location": {
                    "type": config.get("target", {}).get("location", {}).get("type"),
                    "name": config.get("target", {}).get("location", {}).get("names"),
                },
                "source": source,
                "metadata": {
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                    "api_response": company_data.get("api_response_metadata", {}),
                }
            }

            companies_to_insert.append(company_doc)

        if companies_to_insert:
            inserted_ids = await self.companies_dao.create_companies(companies_to_insert)
            campaign_company_details['company_ids'].extend(inserted_ids)
            campaign_company_details['inserted_ids'].extend(inserted_ids)
            logger.info(f"✅ Inserted {len(inserted_ids)} new {source} companies")

        return campaign_company_details

    async def create_campaign_company_mappings_batch(
        self,
        company_ids: List[str],
        campaign_id: str,
    ) -> int:
        """
        Create campaign-company mappings for a batch of companies.
        Returns number of mappings created.
        """
        if not company_ids:
            logger.info(f"⚠️ No valid company ids found in {campaign_id}")
            return 0

        mappings_created = 0

        campaign_company_runs_data = await self.campaign_company_runs_dao.get_campaign_company_runs({
            "campaign_id": campaign_id,
            "company_id": {"$in": company_ids}
        })

        existing_company_ids = {run["company_id"] for run in campaign_company_runs_data}
        for company_id in company_ids:
            if company_id not in existing_company_ids:
                mapping_doc = {
                    "campaign_id": campaign_id,
                    "company_id": company_id,
                    "company_status": False,
                    "linkedin_contact_status": False,
                    "metadata": {
                        "created_at": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc),
                    },
                }

                await self.campaign_company_runs_dao.create_campaign_company_run(mapping_doc)
                mappings_created += 1

        logger.info(f"✅ Created {mappings_created} campaign-company mappings")
        
        return mappings_created
