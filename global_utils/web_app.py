import aiohttp
from structlog.contextvars import bind_contextvars
from config.logging import logger
from database.connection_manager import ConnectionManager
from config.loaded_config import loaded_config
from config.logging import logger


async def run_on_startup():
    bind_contextvars(operation="run_on_startup", component="web_app", event_type="startup")
    logger.info("🚀 connecting to database and eventbridge")
    await initialize_database()
    await eventbridge_producer()
    await http_session()
   
    logger.info("✅ Database and EventBridge connected successfully")
    logger.info("✅ HTTP session initialized")


async def run_on_shutdown():
    await close_database()
    await close_http_session()
    logger.info("✅ Database and session disconnected successfully")

    
async def initialize_database():
    loaded_config.connection_manager = ConnectionManager(mongo_uri=loaded_config.mongo_uri, db_name="linkedin_sdr")
    

async def eventbridge_producer():
     # Initialize EventBridge producer in connection manager
    await loaded_config.connection_manager.setup_eventbridge_producer() 


async def http_session():
    loaded_config.http_session = aiohttp.ClientSession()


async def close_database():
    await loaded_config.connection_manager.close_connections()


async def close_http_session():
    await loaded_config.http_session.close()
    