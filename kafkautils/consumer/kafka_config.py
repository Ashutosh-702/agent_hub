"""Kafka consumer configuration for leadgen service."""
import os
from typing import Dict, Any
from kafkautils.constants import LeadgenServices, LEADGEN_BATCH_PROCESSING, KAFKA_SERVICE_CONFIG_MAPPING, LUSHA_COMPANY_COLLECTION, CONTACTS_ENRICHMENT
from kafkautils.handlers import lusha_company_collection_handler, leadgen_batch_processing_handler, contacts_enrichment_handler, leadgen_prospecting_job_processing_handler
from kafkautils.constants import LEADGEN_PROSPECTING_JOB_PROCESSING

# Common Consumer Configuration
COMMON_CONSUMER_CONFIG = {
    "bootstrap_servers": os.getenv("KAFKA_BROKER_LIST", "localhost:9092"),
    "session_timeout_ms": 30000,
    "auto_offset_reset": "earliest",  # Changed to earliest for testing - will read existing messages
    "group_id": "leadgen-batch-consumer-group",
    "enable_auto_commit": False,  # Manual commit for better control
}

# Test Consumer Configuration (Different Group ID)
TEST_CONSUMER_CONFIG = {
    "bootstrap_servers": os.getenv("KAFKA_BROKER_LIST", "localhost:9092"),
    "session_timeout_ms": 30000,
    "auto_offset_reset": "latest",
    "group_id": "test-leadgen-batch-consumer-group",
    "enable_auto_commit": False,
}

# Consumer Settings Dictionary
KAFKA_CONSUMER_SETTINGS = {
    LeadgenServices.leadgen: {  # Service level grouping (like Vector)
        "leadgen_batch_consumer": {
            "service_name": LeadgenServices.leadgen,
            "deserialization_format": "json",
            "consumer_config": COMMON_CONSUMER_CONFIG,
            "custom_commit_offset": "post",
            "async_kafka": True,
            "topics_configurations": {
                # Multiple topics with their respective handlers
                KAFKA_SERVICE_CONFIG_MAPPING[LeadgenServices.leadgen][LEADGEN_BATCH_PROCESSING]["topics"][0]: {
                    "tasks": [leadgen_batch_processing_handler]
                },
                KAFKA_SERVICE_CONFIG_MAPPING[LeadgenServices.leadgen][LEADGEN_PROSPECTING_JOB_PROCESSING]["topics"][0]: {
                    "tasks": [leadgen_prospecting_job_processing_handler]
                },
                KAFKA_SERVICE_CONFIG_MAPPING[LeadgenServices.leadgen][LUSHA_COMPANY_COLLECTION]["topics"][0]: {
                    "tasks": [lusha_company_collection_handler]
                },
                KAFKA_SERVICE_CONFIG_MAPPING[LeadgenServices.leadgen][CONTACTS_ENRICHMENT]["topics"][0]: {
                    "tasks": [contacts_enrichment_handler]
                }
            },
        }
    }
}

def get_consumer_config(consumer_type: str) -> Dict[str, Any]:
    """
    Get consumer configuration for the specified consumer type (Following Vector's Pattern)
    
    Args:
        consumer_type: Type of consumer (e.g., 'leadgen_batch_consumer')
        
    Returns:
        Consumer configuration dictionary
    """
    service_configs = KAFKA_CONSUMER_SETTINGS.get(LeadgenServices.leadgen, {})
    if consumer_type not in service_configs:
        raise ValueError(f"Unknown consumer type: {consumer_type}. Available types: {list(service_configs.keys())}")
    
    return service_configs[consumer_type].copy()

def get_available_consumer_types() -> list:
    """Get list of available consumer types (Following Vector's Pattern)."""
    return list(KAFKA_CONSUMER_SETTINGS.get(LeadgenServices.leadgen, {}).keys()) 