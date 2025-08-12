"""Kafka constants and service definitions for leadgen."""

class LeadgenServices:
    """Service name constants."""
    leadgen = "leadgen"

# Topic names
LEADGEN_BATCH_PROCESSING = "leadgen-batch-processing"

# Service configurations mapping
KAFKA_SERVICE_CONFIG_MAPPING = {
    LeadgenServices.leadgen: {
        LEADGEN_BATCH_PROCESSING: {
            "topics": ["leadgen_batch_processing"],  # Use underscores to match EventBridge output
            "description": "Process company search requests"
        }
    }
}

# Kafka configuration constants
KAFKA_SERIALIZATION_FORMAT = "json"
KAFKA_SESSION_TIMEOUT_IN_MS = 30000
KAFKA_OFFSET_RESET_STRATEGY = "latest"
LEADGEN_GROUP_ID = "leadgen-batch-consumer-group" 