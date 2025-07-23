"""Configuration for LinkedIn SDR Kafka consumer (Following Vector's Pattern)."""
import os
from typing import Dict, Any

# Import constants and handlers 
from linkedin_sdr.constants import LinkedInSDRServices, LINKEDIN_BATCH_PROCESSING, KAFKA_SERVICE_CONFIG_MAPPING
from linkedin_sdr.handlers import linkedin_batch_processing_handler

# Global Kafka Configuration Constants 
KAFKA_SERIALIZATION_FORMAT = "json"
KAFKA_SESSION_TIMEOUT_IN_MS = 30000
KAFKA_OFFSET_RESET_STRATEGY = "latest"

# LinkedIn SDR Group ID
LINKEDIN_SDR_GROUP_ID = "linkedin-batch-consumer-group"

# Common Consumer Configuration 
COMMON_CONSUMER_CONFIG = {
    "bootstrap.servers": os.getenv("KAFKA_BROKER_LIST", "localhost:9092"),
    "session.timeout.ms": KAFKA_SESSION_TIMEOUT_IN_MS,
    "default.topic.config": {"auto.offset.reset": KAFKA_OFFSET_RESET_STRATEGY},
    "group.id": LINKEDIN_SDR_GROUP_ID,
}

# Test Consumer Configuration (Different Group ID)
TEST_CONSUMER_CONFIG = {
    "bootstrap.servers": os.getenv("KAFKA_BROKER_LIST", "localhost:9092"),
    "session.timeout.ms": KAFKA_SESSION_TIMEOUT_IN_MS,
    "default.topic.config": {"auto.offset.reset": KAFKA_OFFSET_RESET_STRATEGY},
    "group.id": "test-linkedin-sdr-group-id",
}

# Producer Configuration 
KAFKA_COMMON_PRODUCER_CONFIG = {
    "service_name": LinkedInSDRServices.linkedin_sdr,
    "producer_config": {
        "bootstrap_servers": os.getenv("KAFKA_BROKER_LIST", "localhost:9092"),
        "enable_idempotence": True,
        "acks": "all",
    },
}

# Main Consumer Settings Dictionary 
KAFKA_CONSUMER_SETTINGS = {
    LinkedInSDRServices.linkedin_sdr: {
        "linkedin_batch_consumer": {
            "service_name": LinkedInSDRServices.linkedin_sdr,
            "deserialization_format": KAFKA_SERIALIZATION_FORMAT,
            "consumer_config": COMMON_CONSUMER_CONFIG,
            "topics_configurations": {
                KAFKA_SERVICE_CONFIG_MAPPING[LinkedInSDRServices.linkedin_sdr][LINKEDIN_BATCH_PROCESSING]["topics"][0]: {
                    "tasks": [linkedin_batch_processing_handler]  # Handler function directly here
                }
            },
        },
        "test_linkedin_batch_consumer": {
            "service_name": LinkedInSDRServices.linkedin_sdr,
            "deserialization_format": KAFKA_SERIALIZATION_FORMAT,
            "consumer_config": TEST_CONSUMER_CONFIG,
            "topics_configurations": {
                KAFKA_SERVICE_CONFIG_MAPPING[LinkedInSDRServices.linkedin_sdr][LINKEDIN_BATCH_PROCESSING]["topics"][0]: {
                    "tasks": [linkedin_batch_processing_handler]  # Handler function directly here (Like Vector)
                }
            },
        },
    }
}

def get_consumer_config(consumer_type: str) -> Dict[str, Any]:
    """
    Get consumer configuration for the specified consumer type (Following Vector's Pattern)
    
    Args:
        consumer_type: Type of consumer (e.g., 'linkedin_batch_consumer')
        
    Returns:
        Consumer configuration dictionary
    """
    service_configs = KAFKA_CONSUMER_SETTINGS.get(LinkedInSDRServices.linkedin_sdr, {})
    if consumer_type not in service_configs:
        raise ValueError(f"Unknown consumer type: {consumer_type}. Available types: {list(service_configs.keys())}")
    
    return service_configs[consumer_type].copy()

def get_producer_config() -> Dict[str, Any]:
    """
    Get global producer configuration
    
    Returns:
        Producer configuration dictionary
    """
    return KAFKA_COMMON_PRODUCER_CONFIG.copy() 