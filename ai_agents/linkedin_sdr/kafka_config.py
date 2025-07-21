import os
from typing import Dict, Any

# EventBridge Consumer Configuration
KAFKA_CONSUMER_SETTINGS = {
    "linkedin_batch_consumer": {
        "topic": "linkedin-batch-processing",
        "group_id": "linkedin-batch-consumer-group",
        "bootstrap_servers": os.getenv("KAFKA_BROKER_LIST", "localhost:9092"),
        "auto_offset_reset": "latest",
        "enable_auto_commit": True,
        "auto_commit_interval_ms": 1000,
        "session_timeout_ms": 30000,
        "heartbeat_interval_ms": 10000,
        "max_poll_records": 1,  # Process one message at a time
        "message_handler": None,  # Will be set in consumer
    }
}

def get_consumer_config(consumer_type: str) -> Dict[str, Any]:
    """
    Get consumer configuration for the specified consumer type
    
    Args:
        consumer_type: Type of consumer (e.g., 'linkedin_batch_consumer')
        
    Returns:
        Consumer configuration dictionary
    """
    if consumer_type not in KAFKA_CONSUMER_SETTINGS:
        raise ValueError(f"Unknown consumer type: {consumer_type}")
    
    return KAFKA_CONSUMER_SETTINGS[consumer_type].copy() 