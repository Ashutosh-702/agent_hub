"""Kafka constants and service definitions for leadgen."""

class LeadgenServices:
    """Service name constants."""
    leadgen = "leadgen"

# Topic names
LEADGEN_BATCH_PROCESSING = "leadgen-batch-processing"
LEADGEN_PROSPECTING_JOB_PROCESSING = "leadgen-prospecting-job-processing"
LUSHA_COMPANY_COLLECTION = "lusha-company-collection"
CONTACTS_ENRICHMENT = "contacts-enrichment"
# Service configurations mapping
KAFKA_SERVICE_CONFIG_MAPPING = {
    LeadgenServices.leadgen: {
        LEADGEN_BATCH_PROCESSING: {
            "topics": ["leadgen_batch_processing"],  # Use underscores to match EventBridge output
            "description": "Process company search requests"
        },
        LEADGEN_PROSPECTING_JOB_PROCESSING: {
            "topics": ["leadgen_prospecting_job_processing"],  # Use underscores to match EventBridge output
            "description": "Process prospecting job requests"
        },
        LUSHA_COMPANY_COLLECTION: {
            "topics": ["lusha_company_collection"],  # Use underscores to match EventBridge output
            "description": "Process Lusha company collection requests"
        },
        CONTACTS_ENRICHMENT: {
            "topics": ["contacts_enrichment"],  # Use underscores to match EventBridge output
            "description": "Process contacts enrichment requests"
        }
    }
}

# Kafka configuration constants
KAFKA_SERIALIZATION_FORMAT = "json"
KAFKA_SESSION_TIMEOUT_IN_MS = 30000
KAFKA_OFFSET_RESET_STRATEGY = "latest"
LEADGEN_GROUP_ID = "leadgen-batch-consumer-group" 