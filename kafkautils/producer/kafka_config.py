"""Kafka producer configuration for leadgen service."""
import os
from typing import Dict, Any
from kafkautils.constants import LeadgenServices

# Producer Configuration (following EventBridge AIO pattern)
KAFKA_COMMON_PRODUCER_CONFIG = {
    "service_name": LeadgenServices.leadgen,
    'producer_config': {
        'bootstrap_servers': os.getenv("KAFKA_BROKER_LIST", "localhost:9092"),
        'acks': "all",  # Use "all" for maximum safety
        'request_timeout_ms': 60000,
        'enable_idempotence': True,  # Enable for exactly-once semantics
        'max_request_size': 5000000,
        'compression_type': 'lz4'
    },
}

def get_producer_config() -> Dict[str, Any]:
    """Get producer configuration."""
    return KAFKA_COMMON_PRODUCER_CONFIG.copy()
