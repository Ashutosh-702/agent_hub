"""Constants for LinkedIn SDR Kafka service (Following Vector's Pattern)."""

# LinkedIn SDR Service Events
LINKEDIN_BATCH_PROCESSING = "linkedin_batch_processing"

class LinkedInSDRServices:
    """LinkedIn SDR Service Names"""
    linkedin_sdr = "linkedin_sdr"

# LinkedIn SDR Group ID
LINKEDIN_SDR_GROUP_ID = "linkedin-batch-consumer-group"

# Service Configuration Mapping
KAFKA_SERVICE_CONFIG_MAPPING = {
    LinkedInSDRServices.linkedin_sdr: {
        LINKEDIN_BATCH_PROCESSING: {
            "topics": ["linkedin-batch-processing"],
            "group_id": LINKEDIN_SDR_GROUP_ID,
        }
    }
} 