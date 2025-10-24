import os
import sys
import asyncio

from config.loaded_config import loaded_config

# Consumer imports
from kafkautils.consumer.consumer import start_eventbridge_consumer
from kafkautils.consumer.kafka_config import get_available_consumer_types
from eventbridge.health import _healthz, _readyz
import urllib3
from urllib3.exceptions import InsecureRequestWarning
import aiohttp
from config.logging import logger
import traceback


urllib3.disable_warnings(InsecureRequestWarning)
async def consumer_main():
    """Async consumer startup (following LinkedIn SDR pattern)"""
    consumer_type = os.getenv("CONSUMER_TYPE", "leadgen_batch_consumer")
    logger.info("🤖 Starting Leadgen Kafka Consumer Server...")
    logger.info(f"   📡 Consumer type: {consumer_type}")
    logger.info("   📨 Listening for multiple topics...")
    logger.info("   🔄 Will process company searches and lusha collections asynchronously")
    logger.info("   🌉 Using EventBridge abstraction")

    try:
        # Validate consumer type
        available_types = get_available_consumer_types()
        logger.info(f"   📂 Available consumer types: {available_types}")

        if consumer_type not in available_types:
            logger.error(f"❌ Unknown consumer type: {consumer_type}")
            logger.error(f"   Available consumer types: {available_types}")
            logger.error("   Set CONSUMER_TYPE environment variable")
            logger.error("   Examples:")

            for consumer in available_types:
                logger.error(f"     CONSUMER_TYPE={consumer}")
                
            sys.exit(1)

        logger.info(f"   ⚙️  Service: leadgen")
        logger.info(f"   📂 Topics: leadgen-batch-processing, lusha-company-collection")

        # Start health check endpoints
        logger.info("   ❤️ Starting health check endpoints...")
        asyncio.create_task(_healthz())
        asyncio.create_task(_readyz())
        # Start EventBridge consumer
        logger.info("   🚀 Starting EventBridge consumer...")
        loaded_config.http_session = aiohttp.ClientSession()
        logger.info(f"✅ HTTP session initialized {loaded_config.http_session}")
        await start_eventbridge_consumer(consumer_type)

    except KeyError as e:
        available_types = get_available_consumer_types()
        logger.error(f"❌ Configuration error: {e}")
        logger.error(f"   Available consumer types: {available_types}")
        logger.error("   Set CONSUMER_TYPE environment variable")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Consumer startup failed: {e}")
        traceback.print_exc()
        sys.exit(1)