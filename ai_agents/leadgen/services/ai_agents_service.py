"""AI Agents Service"""
import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, List
from ai_agents.leadgen.schemas.ai_agents import FormSubmission
from kafkautils.producer.event_helpers import emit_event_helper
from kafkautils.constants import LEADGEN_BATCH_PROCESSING, KAFKA_SERVICE_CONFIG_MAPPING, LeadgenServices
from config.loaded_config import loaded_config
from database.collection_dao.campaigns import CampaignsDao
from global_utils.exceptions import ApiException


class LeadgenFormUploadService:
    def __init__(self):
        self.campaign_dao = CampaignsDao(
            loaded_config.connection_manager.mongo_client)
        self.event_emitter = loaded_config.connection_manager.event_emitter
        self.kafka_config = KAFKA_SERVICE_CONFIG_MAPPING[
            LeadgenServices.leadgen][LEADGEN_BATCH_PROCESSING]

    async def upload_leadgen_form(self, form_submission: FormSubmission) -> Dict[str, str]:

        db_data = self._transform_form_to_db_data(form_submission)

        campaign_id = await self.campaign_dao.create_campaign(db_data)

        if not campaign_id:
            raise ApiException("campaign_id not generated")

        request_id = str(uuid.uuid4())

        if not self.event_emitter:
            raise ApiException("EventBridge Producer not initialized")

        event = {
            "request_id": request_id,
            "action": "process_company_search",
            "campaign_id": str(campaign_id),  # Only send the ID, not all data
            "timestamp": asyncio.get_event_loop().time()
        }

        await emit_event_helper(
            event_emitter=self.event_emitter,
            topics=self.kafka_config["topics"],
            # Use actual topic from mapping
            partition_value=request_id,
            event=event,
            event_meta={"service": "leadgen", "campaign_id": str(campaign_id)}
        )

        print(
            f"📤 Campaign ID {str(campaign_id)} queued for processing: {request_id}")

        return {
            "request_id": request_id,
            "campaign_id": str(campaign_id)
        }

    def _transform_form_to_db_data(self, form_submission: FormSubmission) -> Dict[str, Any]:
        """Transform form submission to database format"""
        return {
            "prompts": {
                "web": form_submission.web_prompt,
                "persona": form_submission.persona_prompt
            },
            "segmentation": {
                "industry": self._parse_list(form_submission.industry, ';'),
                "keywords": form_submission.keywords,
                "categories": form_submission.categories
            },
            "target": {
                "employee_count": self._parse_list(form_submission.employee_count, ','),
                "revenue_min": form_submission.revenue_min,
                "revenue_max": form_submission.revenue_max,
                "currency": form_submission.currency,
                "location": {
                    "type": form_submission.location_type,
                    "names": self._parse_list(form_submission.location, ',')
                }
            },
            "ownership": {
                "hubspot_email": form_submission.hubspot_email,
                "product_name": form_submission.product_name,
                "business_team": form_submission.business_team,
                "user_email": form_submission.user_email
            },
            "lifecycle": {"status": "active"},
            "metadata": {
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        }

    def _parse_list(self, value: str, delimiter: str) -> List[str]:
        """Parse string to list with validation"""
        if not value:
            return []
            
        return sorted([item.strip() for item in value.split(delimiter) if item.strip()])

    async def update_campaign_status(self, campaign_id: str, status: str):
        response = await self.campaign_dao.update_campaign_status(campaign_id, status)

        if not response:
            raise ApiException(f"No campaign found with campaign id {campaign_id} to update status or it's already updated")

        return response
